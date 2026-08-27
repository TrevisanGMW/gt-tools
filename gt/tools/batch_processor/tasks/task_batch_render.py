"""
Batch Processor Maya Batch Render Task

Renders incoming Maya scenes with Maya's command-line renderer ("Render"). The
renderer runs as an isolated process per scene so render layers, renderer
plugins, and licensing behave exactly like a regular Maya batch render.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import gt.ui.resource_library as ui_res_lib
import subprocess
import threading
import shlex
import glob
import sys
import os


PROJECT_MODE_AUTO = "Auto (Scene Workspace)"
PROJECT_MODE_CUSTOM = "Custom Path"
PROJECT_MODES = [PROJECT_MODE_AUTO, PROJECT_MODE_CUSTOM]

DEFAULT_FILE_NAME_PREFIX = "<Scene>"
DEFAULT_IMAGE_FORMAT = "png"
IMAGE_FORMATS = ["png", "jpeg", "tif", "tga", "iff", "exr"]

PREFIX_TOKENS = set(["name", "ext", "task-name", "date"])

RENDERED_IMAGE_EXTENSIONS = set(
    [
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".tga",
        ".iff",
        ".exr",
        ".bmp",
        ".hdr",
        ".psd",
        ".dds",
        ".sgi",
        ".rla",
        ".als",
        ".cin",
        ".eps",
    ]
)

WORKSPACE_FILE_NAME = "workspace.mel"
MAX_WORKSPACE_SEARCH_DEPTH = 6

MARKER_RANGE = "[GT_RENDER_RANGE]"
MARKER_FRAME_START = "[GT_RENDER_FRAME_START]"
MARKER_FRAME_END = "[GT_RENDER_FRAME_END]"
FRAME_UNIT_LABEL = "frames"


class TaskBatchRender(task_base.BatchTask):
    """Task that renders incoming Maya scenes with Maya's command-line renderer."""

    task_type = constants.TaskType.BATCH_RENDER
    default_display_name = "Batch Render"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.batch_task_render
    category = "Outputs"
    category_icon = ui_res_lib.Icon.batch_category_outputs
    is_output_task = True

    def get_default_settings(self):
        """Gets default batch render settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "create_folder_per_file": True,
            "file_name_prefix": DEFAULT_FILE_NAME_PREFIX,
            "set_project": True,
            "project_mode": PROJECT_MODE_AUTO,
            "project_path": "",
            "override_resolution": False,
            "width": 1920,
            "height": 1080,
            "override_frame_range": False,
            "start_frame": 1,
            "end_frame": 24,
            "frame_step": 1,
            "override_camera": False,
            "camera_name": "",
            "override_image_format": False,
            "image_format": DEFAULT_IMAGE_FORMAT,
            "override_frame_padding": False,
            "frame_padding": 4,
            "override_version_label": False,
            "version_label": "",
            "skip_existing_frames": False,
            "render_executable": "",
            "maya_version": "",
            "extra_arguments": "",
            "timeout_minutes": 0,
            "report_frame_progress": True,
            "require_rendered_files": True,
            "write_process_log": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates batch render settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.modifies_in_place():
            result.add_error("Batch render cannot modify source files in place. Use a target path instead.")
        if self.passes_through():
            result.add_error("Batch render always writes images and cannot pass through.")
        prefix = str(self.settings.get("file_name_prefix") or "")
        if prefix:
            prefix_result = task_base.validate_format_tokens(prefix, PREFIX_TOKENS)
            for error in prefix_result.errors:
                result.add_error("Batch render file name prefix: {0}".format(error))
        if self.settings.get("override_resolution"):
            self.validate_positive_int(result, self.settings.get("width"), "width")
            self.validate_positive_int(result, self.settings.get("height"), "height")
        if self.settings.get("override_frame_range"):
            start_frame = self.validate_number(result, self.settings.get("start_frame"), "start frame")
            end_frame = self.validate_number(result, self.settings.get("end_frame"), "end frame")
            self.validate_positive_int(result, self.settings.get("frame_step"), "frame step")
            if start_frame is not None and end_frame is not None and end_frame < start_frame:
                result.add_error("Batch render end frame cannot be lower than the start frame.")
        if self.settings.get("override_camera") and not str(self.settings.get("camera_name") or "").strip():
            result.add_error("Batch render camera override is enabled but no camera name is set.")
        if self.settings.get("override_image_format") and not str(self.settings.get("image_format") or "").strip():
            result.add_error("Batch render image format override is enabled but no format is set.")
        if self.settings.get("override_frame_padding"):
            self.validate_positive_int(result, self.settings.get("frame_padding"), "frame padding")
        if self.settings.get("override_version_label") and not str(self.settings.get("version_label") or "").strip():
            result.add_error("Batch render version label override is enabled but no label is set.")
        self.validate_project_settings(result, project)
        if not self.resolve_render_executable(project=project):
            result.add_warning(
                "Batch render could not find a Maya command-line renderer. "
                "Set an explicit renderer path or Maya version."
            )
        return result

    def validate_project_settings(self, result, project):
        """Validates the optional Maya project override.

        Args:
            result (ValidationResult): Result object to update.
            project (BatchProcessorModel): Project containing this task.
        """
        if not self.settings.get("set_project", True):
            return
        if (self.settings.get("project_mode") or PROJECT_MODE_AUTO) != PROJECT_MODE_CUSTOM:
            return
        project_path = str(self.settings.get("project_path") or "").strip()
        if not project_path:
            result.add_error("Batch render custom Maya project is enabled but no project path is set.")
            return
        resolved_path = project.resolve_template_path(project_path, task=self) if project else project_path
        if resolved_path and not os.path.isdir(resolved_path):
            result.add_warning("Batch render Maya project folder does not exist yet: {0}".format(resolved_path))

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects render output collisions before rendering.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        output_dirs = {}
        create_folder_per_file = self.settings.get("create_folder_per_file", True)
        for work_item in work_items:
            output_dir = self.build_render_output_dir(work_item, step_output_dir)
            key = os.path.normcase(output_dir)
            if key in output_dirs and create_folder_per_file:
                result.add_warning(
                    "Batch render output collision: {0} and {1} both render into {2}".format(
                        output_dirs[key], work_item.current_path, output_dir
                    )
                )
            output_dirs[key] = work_item.current_path
            if list_rendered_files(output_dir) and not self.settings.get("overwrite", False):
                result.add_warning(
                    "Batch render output already contains images and will be skipped: {0}".format(output_dir)
                )
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Renders one work item with Maya's command-line renderer.

        Args:
            work_item (WorkItem): Source work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Work item pointing at the render output folder.
        """
        output_dir = self.build_render_output_dir(work_item, step_output_dir)
        existing_files = list_rendered_files(output_dir)
        if existing_files and not self.settings.get("overwrite", False):
            raise task_base.TaskSkip(
                "Render output already contains {0} image(s) and overwrite is disabled: {1}".format(
                    len(existing_files), output_dir
                ),
                output_path=output_dir,
                work_item=task_base.WorkItem(
                    source_path=work_item.source_path,
                    current_path=output_dir,
                    metadata=dict(work_item.metadata),
                ),
            )
        executable_path = self.resolve_render_executable(project=project)
        if not executable_path:
            raise RuntimeError(
                "Unable to find Maya's command-line renderer. Set an explicit renderer path or Maya version."
            )
        task_utils.ensure_directory(output_dir)
        command = self.build_render_command(
            executable_path=executable_path,
            work_item=work_item,
            output_dir=output_dir,
            project=project,
        )
        log_path = self.build_process_log_path(work_item=work_item, output_dir=output_dir, project=project)
        files_before = set(existing_files)
        monitor = self.build_progress_monitor(work_item=work_item, output_dir=output_dir, context=context)
        return_code, output_text = self.run_render_process(
            command=command,
            log_path=log_path,
            monitor=monitor,
        )
        write_process_log(
            log_path=log_path,
            command=command,
            return_code=return_code,
            input_path=work_item.current_path,
            output_dir=output_dir,
            output_text=output_text,
        )
        task_utils.report_log_artifact(context, log_path)
        if return_code:
            raise RuntimeError(
                "Maya batch render failed with exit code {0} for: {1}{2}".format(
                    return_code,
                    work_item.current_path,
                    " See log: {0}".format(log_path) if log_path else "",
                )
            )
        rendered_files = [path for path in list_rendered_files(output_dir) if path not in files_before]
        if not rendered_files and self.settings.get("require_rendered_files", True):
            raise RuntimeError("Maya batch render did not create any images in: {0}".format(output_dir))
        metadata = task_utils.build_metadata(self, work_item)
        metadata["render_output_dir"] = output_dir
        metadata["rendered_file_count"] = len(rendered_files)
        if rendered_files:
            metadata["first_rendered_file"] = rendered_files[0]
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_dir, metadata=metadata)

    def build_render_output_dir(self, work_item, step_output_dir):
        """Builds the folder that receives the rendered images.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Base output directory for this task.

        Returns:
            str: Render output directory.
        """
        output_dir = task_base.get_output_dir_for_work_item(work_item, step_output_dir)
        if not self.settings.get("create_folder_per_file", True):
            return task_base.normalize_path(output_dir)
        folder_name = task_base.sanitize_filename(get_source_base_name(work_item), "scene")
        return task_base.normalize_path(os.path.join(output_dir, folder_name))

    def build_file_name_prefix(self, work_item):
        """Builds the file name prefix passed to the renderer.

        Batch tokens such as {name} are resolved here, while Maya render tokens
        such as <Scene> are forwarded untouched so Maya can expand them.

        Args:
            work_item (WorkItem): Source work item.

        Returns:
            str: File name prefix, or an empty string to keep the scene prefix.
        """
        prefix = str(self.settings.get("file_name_prefix") or "").strip()
        if not prefix:
            return ""
        source_name = os.path.basename(get_source_path(work_item))
        base_name, extension = os.path.splitext(source_name)
        token_data = {
            "name": base_name,
            "ext": extension.lstrip("."),
            "task-name": task_base.sanitize_filename(self.display_name, "task"),
            "date": task_base.get_today_token(),
        }
        try:
            prefix = prefix.format(**token_data)
        except (KeyError, IndexError, ValueError):
            pass
        return prefix.replace("\\", "/").strip("/")

    def build_render_command(self, executable_path, work_item, output_dir, project):
        """Builds the Maya command-line renderer command.

        The scene renderer is intentionally not forced, so each scene renders
        with the renderer it was authored for.

        Args:
            executable_path (str): Maya command-line renderer path.
            work_item (WorkItem): Work item being rendered.
            output_dir (str): Render output directory.
            project (BatchProcessorModel): Active project.

        Returns:
            list: Command arguments.
        """
        command = [executable_path]
        maya_project_dir = self.resolve_maya_project_dir(work_item=work_item, project=project)
        if maya_project_dir:
            command.extend(["-proj", maya_project_dir])
        command.extend(["-rd", output_dir])
        file_name_prefix = self.build_file_name_prefix(work_item)
        if file_name_prefix:
            command.extend(["-im", file_name_prefix])
        command.extend(self.build_override_arguments())
        command.extend(self.build_callback_arguments())
        command.extend(parse_command_arguments(self.settings.get("extra_arguments")))
        command.append(get_source_path(work_item))
        return command

    def build_callback_arguments(self):
        """Builds the renderer callback arguments used for overrides and progress.

        Maya's command-line renderer only accepts MEL for its callbacks, so the
        version label override and the per-frame progress markers are emitted as
        small MEL statements. Progress markers are the only renderer-agnostic way
        to know which frame the renderer is working on.

        Returns:
            list: Command arguments.
        """
        arguments = []
        pre_render_statements = []
        if self.settings.get("override_version_label"):
            version_label = str(self.settings.get("version_label") or "").strip()
            if version_label:
                pre_render_statements.append(build_version_label_mel(version_label))
        if self.settings.get("report_frame_progress", True):
            pre_render_statements.append(build_frame_range_mel())
        if pre_render_statements:
            arguments.extend(["-preRender", " ".join(pre_render_statements)])
        if self.settings.get("report_frame_progress", True):
            arguments.extend(["-preFrame", build_frame_marker_mel(MARKER_FRAME_START)])
            arguments.extend(["-postFrame", build_frame_marker_mel(MARKER_FRAME_END)])
        return arguments

    def build_progress_monitor(self, work_item, output_dir, context=None):
        """Builds the monitor that turns renderer output into progress reports.

        Args:
            work_item (WorkItem): Work item being rendered.
            output_dir (str): Render output directory.
            context (dict, optional): Runtime context supplying report callbacks.

        Returns:
            RenderProgressMonitor: Monitor used while the renderer runs.
        """
        context = context or {}
        return RenderProgressMonitor(
            output_dir=output_dir,
            scene_name=os.path.basename(get_source_path(work_item)),
            task_type=self.task_type,
            report_message=context.get("report_message"),
            report_progress=context.get("report_progress"),
            is_enabled=bool(self.settings.get("report_frame_progress", True)),
            total_frames=self.get_expected_frame_count(),
        )

    def get_expected_frame_count(self):
        """Gets the frame count implied by the frame range override.

        Returns:
            int: Expected frame count, or 0 when the range comes from the scene.
        """
        if not self.settings.get("override_frame_range"):
            return 0
        return count_frames(
            self.settings.get("start_frame"),
            self.settings.get("end_frame"),
            self.settings.get("frame_step"),
        )

    def build_override_arguments(self):
        """Builds renderer arguments for the enabled render setting overrides.

        Returns:
            list: Command arguments.
        """
        arguments = []
        if self.settings.get("override_resolution"):
            arguments.extend(["-x", str(int(self.settings.get("width") or 1920))])
            arguments.extend(["-y", str(int(self.settings.get("height") or 1080))])
        if self.settings.get("override_frame_range"):
            arguments.extend(["-s", format_frame_value(self.settings.get("start_frame"))])
            arguments.extend(["-e", format_frame_value(self.settings.get("end_frame"))])
            arguments.extend(["-b", format_frame_value(self.settings.get("frame_step") or 1)])
        if self.settings.get("override_camera"):
            camera_name = str(self.settings.get("camera_name") or "").strip()
            if camera_name:
                arguments.extend(["-cam", camera_name])
        if self.settings.get("override_image_format"):
            image_format = str(self.settings.get("image_format") or "").strip()
            if image_format:
                arguments.extend(["-of", image_format])
        if self.settings.get("override_frame_padding"):
            arguments.extend(["-pad", str(int(self.settings.get("frame_padding") or 4))])
        if self.settings.get("skip_existing_frames"):
            arguments.extend(["-skipExistingFrames", "true"])
        return arguments

    def resolve_maya_project_dir(self, work_item, project):
        """Resolves the Maya project folder passed to the renderer.

        Args:
            work_item (WorkItem): Work item being rendered.
            project (BatchProcessorModel): Active project.

        Returns:
            str: Maya project directory, or an empty string when unset.
        """
        if not self.settings.get("set_project", True):
            return ""
        project_mode = self.settings.get("project_mode") or PROJECT_MODE_AUTO
        if project_mode == PROJECT_MODE_CUSTOM:
            project_path = str(self.settings.get("project_path") or "").strip()
            if not project_path:
                return ""
            if project:
                return project.resolve_template_path(project_path, task=self)
            return task_base.normalize_path(project_path)
        return find_scene_workspace_dir(get_source_path(work_item))

    def resolve_render_executable(self, project=None):
        """Resolves the Maya command-line renderer executable.

        Args:
            project (BatchProcessorModel, optional): Active project.

        Returns:
            str: Executable path, or an empty string when none was found.
        """
        value = str(self.settings.get("render_executable") or "").strip()
        if value:
            if project:
                resolved_path = project.resolve_template_path(value, task=self)
            else:
                resolved_path = task_base.normalize_path(value)
            return resolved_path if os.path.isfile(resolved_path) else ""
        return find_render_executable(version=self.settings.get("maya_version"))

    def build_process_log_path(self, work_item, output_dir, project=None):
        """Builds the renderer process log path.

        Args:
            work_item (WorkItem): Work item being rendered.
            output_dir (str): Render output directory.
            project (BatchProcessorModel, optional): Active project.

        Returns:
            str: Log path, or an empty string when logging is disabled.
        """
        if not self.settings.get("write_process_log", True):
            return ""
        log_dir = project.get_logs_dir() if project and hasattr(project, "get_logs_dir") else ""
        target_dir = log_dir or output_dir
        base_name = task_base.sanitize_filename(get_source_base_name(work_item), "scene")
        return task_base.normalize_path(os.path.join(target_dir, "{0}_render.log".format(base_name)))

    def run_render_process(self, command, log_path="", monitor=None):
        """Runs the renderer, streaming its output so progress can be reported.

        Args:
            command (list): Command arguments.
            log_path (str, optional): Log path used for timeout messages.
            monitor (RenderProgressMonitor, optional): Monitor fed with each output line.

        Returns:
            tuple: Return code and captured process output.

        Raises:
            RuntimeError: If the renderer exceeds the configured timeout.
        """
        timeout_minutes = float(self.settings.get("timeout_minutes") or 0)
        timeout_value = timeout_minutes * 60 if timeout_minutes > 0 else None
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
        )
        timeout_state = {"expired": False}

        def stop_expired_process():
            """Kills the renderer once the configured timeout elapses."""
            timeout_state["expired"] = True
            process.kill()

        timeout_timer = None
        if timeout_value:
            timeout_timer = threading.Timer(timeout_value, stop_expired_process)
            timeout_timer.daemon = True
            timeout_timer.start()
        output_lines = []
        try:
            for line in process.stdout:
                output_lines.append(line)
                if monitor:
                    monitor.process_line(line)
        finally:
            if timeout_timer:
                timeout_timer.cancel()
            process.stdout.close()
            process.wait()
        output_text = "".join(output_lines)
        if timeout_state["expired"]:
            write_process_log(
                log_path=log_path,
                command=command,
                return_code="TIMEOUT",
                output_text=output_text,
            )
            raise RuntimeError(
                "Maya batch render timed out after {0} minute(s).{1}".format(
                    timeout_minutes,
                    " See log: {0}".format(log_path) if log_path else "",
                )
            )
        return process.returncode, output_text

    @staticmethod
    def validate_positive_int(result, value, label):
        """Validates a positive integer setting.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Value to validate.
            label (str): Human-readable label.
        """
        try:
            if int(value) < 1:
                raise ValueError
        except (TypeError, ValueError):
            result.add_error("Batch render {0} must be a positive integer.".format(label))

    @staticmethod
    def validate_number(result, value, label):
        """Validates a numeric setting.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Value to validate.
            label (str): Human-readable label.

        Returns:
            float or None: Parsed value, or None when the value is invalid.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            result.add_error("Batch render {0} must be numeric: {1}".format(label, value))
            return None


def get_source_path(work_item):
    """Gets the scene path represented by a work item.

    Args:
        work_item (WorkItem): Work item to inspect.

    Returns:
        str: Scene path, or an empty string.
    """
    return getattr(work_item, "current_path", "") or ""


def get_source_base_name(work_item):
    """Gets the scene file name without its extension.

    Args:
        work_item (WorkItem): Work item to inspect.

    Returns:
        str: File name without extension.
    """
    return os.path.splitext(os.path.basename(get_source_path(work_item)))[0]


def format_frame_value(value):
    """Formats a frame value for the renderer command line.

    Args:
        value (object): Frame value.

    Returns:
        str: Frame value without a redundant decimal part.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "0"
    if number.is_integer():
        return str(int(number))
    return str(number)


def build_version_label_mel(version_label):
    """Builds the pre-render statement that applies a render version label.

    Maya's command-line renderer only accepts MEL for its pre-render callback,
    so this single statement is the only way to override the version label
    without rewriting the incoming source scene.

    Args:
        version_label (str): Version label to apply.

    Returns:
        str: MEL statement passed to the renderer pre-render callback.
    """
    escaped_label = str(version_label).replace("\\", "\\\\").replace('"', '\\"')
    return 'setAttr -type "string" defaultRenderGlobals.renderVersion "{0}";'.format(escaped_label)


def build_frame_range_mel():
    """Builds the pre-render statement that reports the effective frame range.

    Command-line resolution and frame flags are applied to the render globals
    before the pre-render callback runs, so the reported range already includes
    any override set by this task.

    Returns:
        str: MEL statement passed to the renderer pre-render callback.
    """
    return (
        'print("{0} " + `getAttr defaultRenderGlobals.startFrame` + " "'
        ' + `getAttr defaultRenderGlobals.endFrame` + " "'
        ' + `getAttr defaultRenderGlobals.byFrameStep` + " "'
        ' + `getAttr defaultRenderGlobals.animation` + "\\n");'
    ).format(MARKER_RANGE)


def build_frame_marker_mel(marker):
    """Builds a per-frame statement that reports the frame being rendered.

    Args:
        marker (str): Marker printed before the frame number.

    Returns:
        str: MEL statement passed to a renderer frame callback.
    """
    return 'print("{0} " + `currentTime -q` + "\\n");'.format(marker)


def count_frames(start_frame, end_frame, frame_step):
    """Counts the frames produced by a frame range.

    Args:
        start_frame (object): First frame.
        end_frame (object): Last frame.
        frame_step (object): Frame increment.

    Returns:
        int: Frame count, or 0 when the range cannot be parsed.
    """
    try:
        start_value = float(start_frame)
        end_value = float(end_frame)
        step_value = float(frame_step or 1)
    except (TypeError, ValueError):
        return 0
    if step_value <= 0 or end_value < start_value:
        return 0
    return int((end_value - start_value) // step_value) + 1


class RenderProgressMonitor:
    """Turns Maya renderer output into per-frame progress and log messages."""

    def __init__(
        self,
        output_dir,
        scene_name="",
        task_type="",
        report_message=None,
        report_progress=None,
        is_enabled=True,
        total_frames=0,
    ):
        """Initializes a render progress monitor.

        Args:
            output_dir (str): Render output directory watched for new images.
            scene_name (str, optional): Scene file name used in messages.
            task_type (str, optional): Task type used in message prefixes.
            report_message (callable, optional): Callback receiving log messages.
            report_progress (callable, optional): Callback receiving progress units.
            is_enabled (bool, optional): Whether per-frame reporting is active.
            total_frames (int, optional): Known frame count, when already resolved.
        """
        self.output_dir = output_dir
        self.scene_name = scene_name
        self.task_type = task_type or "batch_render"
        self.report_message = report_message
        self.report_progress = report_progress
        self.is_enabled = bool(is_enabled)
        self.total_frames = int(total_frames or 0)
        self.start_frame = None
        self.frame_step = 1.0
        self.completed_frames = 0
        self.known_files = set(list_rendered_files(output_dir))

    def process_line(self, line):
        """Handles one line of renderer output.

        Args:
            line (str): Renderer output line.
        """
        if not self.is_enabled:
            return
        line = str(line or "").strip()
        if MARKER_RANGE in line:
            self.handle_range(line.split(MARKER_RANGE, 1)[1])
        elif MARKER_FRAME_START in line:
            self.handle_frame_start(line.split(MARKER_FRAME_START, 1)[1])
        elif MARKER_FRAME_END in line:
            self.handle_frame_end(line.split(MARKER_FRAME_END, 1)[1])

    def handle_range(self, values_text):
        """Stores the effective frame range reported by the renderer.

        Args:
            values_text (str): Start, end, step, and animation values.
        """
        values = values_text.split()
        if len(values) < 3:
            return
        try:
            self.start_frame = float(values[0])
            end_frame = float(values[1])
            self.frame_step = float(values[2]) or 1.0
        except ValueError:
            self.start_frame = None
            return
        is_animation = True
        if len(values) > 3:
            is_animation = str(values[3]).strip() not in ["0", "0.0", "false"]
        self.total_frames = 1 if not is_animation else count_frames(self.start_frame, end_frame, self.frame_step)
        self.send_progress(0)

    def handle_frame_start(self, value_text):
        """Reports progress for a frame the renderer just started.

        Args:
            value_text (str): Frame number reported by the renderer.
        """
        frame_number = parse_frame_value(value_text)
        if frame_number is None:
            return
        frame_index = self.get_frame_index(frame_number)
        self.send_progress(frame_index)
        self.send_message(
            "Rendering frame {0} ({1}/{2}): {3}".format(
                format_frame_value(frame_number),
                frame_index,
                self.total_frames or frame_index,
                self.scene_name,
            )
        )

    def handle_frame_end(self, value_text):
        """Reports the image written for a frame the renderer just finished.

        Args:
            value_text (str): Frame number reported by the renderer.
        """
        frame_number = parse_frame_value(value_text)
        if frame_number is None:
            return
        self.completed_frames += 1
        frame_index = self.get_frame_index(frame_number)
        new_files = self.collect_new_files()
        rendered_path = new_files[0] if new_files else ""
        if len(new_files) > 1:
            rendered_path = "{0} (+{1} more)".format(rendered_path, len(new_files) - 1)
        self.send_message(
            "Rendered frame {0} ({1}/{2}): {3}".format(
                format_frame_value(frame_number),
                frame_index,
                self.total_frames or frame_index,
                rendered_path or self.output_dir,
            )
        )

    def get_frame_index(self, frame_number):
        """Gets the one-based position of a frame inside the render range.

        Args:
            frame_number (float): Frame number reported by the renderer.

        Returns:
            int: One-based frame index.
        """
        if self.start_frame is None or not self.frame_step:
            return max(1, self.completed_frames or 1)
        return max(1, int(round((frame_number - self.start_frame) / self.frame_step)) + 1)

    def collect_new_files(self):
        """Collects rendered images that appeared since the last check.

        Returns:
            list: Newly written image paths.
        """
        current_files = list_rendered_files(self.output_dir)
        new_files = [path for path in current_files if path not in self.known_files]
        self.known_files.update(current_files)
        return new_files

    def send_progress(self, completed_units):
        """Sends progress units to the runtime callback when one is available.

        Args:
            completed_units (int): Frames started or completed so far.
        """
        if not callable(self.report_progress) or not self.total_frames:
            return
        try:
            self.report_progress(
                completed_units=int(completed_units),
                total_units=int(self.total_frames),
                unit_label=FRAME_UNIT_LABEL,
            )
        except Exception:
            pass

    def send_message(self, message):
        """Sends a log message through the runtime callback or standard output.

        Args:
            message (str): Message to report.
        """
        message = "[INFO] - ({0}) - {1}".format(self.task_type, message)
        if callable(self.report_message):
            try:
                self.report_message(message)
                return
            except Exception:
                pass
        print(message, flush=True)


def parse_frame_value(value_text):
    """Parses a frame number reported by a renderer callback.

    Args:
        value_text (str): Raw frame value.

    Returns:
        float or None: Parsed frame number, or None when unparsable.
    """
    value_text = str(value_text or "").strip()
    if not value_text:
        return None
    try:
        return float(value_text.split()[0])
    except (IndexError, ValueError):
        return None


def parse_command_arguments(arguments):
    """Parses extra renderer arguments from text or a list.

    Args:
        arguments (str or list): Extra arguments.

    Returns:
        list: Parsed argument list.
    """
    if not arguments:
        return []
    if isinstance(arguments, (list, tuple)):
        return [str(item) for item in arguments if str(item).strip()]
    try:
        return shlex.split(str(arguments), posix=False)
    except ValueError:
        return str(arguments).split()


def is_rendered_image(file_name):
    """Checks whether a file name looks like a rendered image.

    Maya frame numbering conventions place the frame number either before or
    after the image extension, so every dotted part of the name is inspected.

    Args:
        file_name (str): File name to inspect.

    Returns:
        bool: True when the name contains a known image extension.
    """
    name_parts = str(file_name or "").lower().split(".")
    for name_part in name_parts[1:]:
        if "." + name_part in RENDERED_IMAGE_EXTENSIONS:
            return True
    return False


def list_rendered_files(output_dir):
    """Lists rendered image files inside an output directory.

    Args:
        output_dir (str): Directory to inspect.

    Returns:
        list: Sorted image file paths.
    """
    output_dir = task_base.normalize_path(output_dir)
    if not output_dir or not os.path.isdir(output_dir):
        return []
    rendered_files = []
    for root_dir, _, file_names in os.walk(output_dir):
        for file_name in file_names:
            if is_rendered_image(file_name):
                rendered_files.append(task_base.normalize_path(os.path.join(root_dir, file_name)))
    return sorted(rendered_files)


def find_scene_workspace_dir(scene_path):
    """Finds the Maya project folder that owns a scene file.

    Args:
        scene_path (str): Scene file path.

    Returns:
        str: Maya project directory, or an empty string when none was found.
    """
    scene_path = task_base.normalize_path(scene_path)
    if not scene_path:
        return ""
    current_dir = os.path.dirname(scene_path)
    for _ in range(MAX_WORKSPACE_SEARCH_DEPTH):
        if not current_dir:
            break
        if os.path.isfile(os.path.join(current_dir, WORKSPACE_FILE_NAME)):
            return task_base.normalize_path(current_dir)
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return ""


def find_render_executable(version=None):
    """Finds Maya's command-line renderer executable.

    Args:
        version (str, optional): Preferred Maya version, such as 2025.

    Returns:
        str: Renderer path, or an empty string when none was found.
    """
    for candidate in get_render_executable_candidates(version=version):
        if os.path.isfile(candidate):
            return task_base.normalize_path(candidate)
    return ""


def get_render_executable_candidates(version=None):
    """Gets likely Maya command-line renderer paths.

    Args:
        version (str, optional): Preferred Maya version, such as 2025.

    Returns:
        list: Candidate renderer paths.
    """
    version = str(version or "").strip()
    executable_name = "Render.exe" if sys.platform == "win32" else "Render"
    candidates = []
    if version:
        candidates.extend(get_versioned_render_candidates(version=version, executable_name=executable_name))
    else:
        current_dir = os.path.dirname(sys.executable)
        if current_dir:
            candidates.append(os.path.join(current_dir, executable_name))
    candidates.extend(get_installed_render_candidates(executable_name=executable_name))
    return list(dict.fromkeys([task_base.normalize_path(path) for path in candidates if path]))


def get_versioned_render_candidates(version, executable_name):
    """Gets renderer paths for a specific Maya version.

    Args:
        version (str): Maya version, such as 2025.
        executable_name (str): Renderer executable file name.

    Returns:
        list: Candidate renderer paths.
    """
    candidates = []
    if sys.platform == "win32":
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMW6432", r"C:\Program Files"),
        ]
        for root in roots:
            if not root:
                continue
            candidates.append(os.path.join(root, "Autodesk", "Maya{0}".format(version), "bin", executable_name))
            candidates.append(os.path.join(root, "Autodesk", "Maya {0}".format(version), "bin", executable_name))
    elif sys.platform == "darwin":
        candidates.append(
            "/Applications/Autodesk/maya{0}/Maya.app/Contents/bin/{1}".format(version, executable_name)
        )
    else:
        candidates.append("/usr/autodesk/maya{0}/bin/{1}".format(version, executable_name))
    return candidates


def get_installed_render_candidates(executable_name):
    """Gets renderer paths from default Maya install locations, newest first.

    Args:
        executable_name (str): Renderer executable file name.

    Returns:
        list: Candidate renderer paths.
    """
    patterns = []
    if sys.platform == "win32":
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMW6432", r"C:\Program Files"),
        ]
        for root in roots:
            if root:
                patterns.append(os.path.join(root, "Autodesk", "Maya*", "bin", executable_name))
    elif sys.platform == "darwin":
        patterns.append("/Applications/Autodesk/maya*/Maya.app/Contents/bin/{0}".format(executable_name))
    else:
        patterns.append("/usr/autodesk/maya*/bin/{0}".format(executable_name))
    candidates = []
    for pattern in patterns:
        candidates.extend(glob.glob(pattern))
    return sorted(candidates, reverse=True)


def write_process_log(
    log_path,
    command,
    return_code=None,
    input_path="",
    output_dir="",
    output_text="",
):
    """Writes captured renderer output to a log file.

    Args:
        log_path (str): Log file path.
        command (list): Executed command.
        return_code (int or str, optional): Process return code.
        input_path (str, optional): Rendered scene path.
        output_dir (str, optional): Render output directory.
        output_text (str, optional): Captured process output.
    """
    if not log_path:
        return
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    with open(log_path, "a", encoding="utf-8", errors="replace") as log_file:
        log_file.write("Command:\n{0}\n\n".format(" ".join([str(item) for item in command or []])))
        log_file.write("Return Code: {0}\n\n".format(return_code))
        log_file.write("Input Path: {0}\n".format(input_path or ""))
        log_file.write("Output Directory: {0}\n\n".format(output_dir or ""))
        log_file.write("OUTPUT:\n{0}\n\n".format(output_text or ""))
