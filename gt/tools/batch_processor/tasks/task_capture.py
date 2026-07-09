"""
Batch Processor Capture Tasks
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import os


class TaskCaptureThumbnail(task_base.BatchTask):
    """Task that captures viewport thumbnails for incoming Maya files."""

    task_type = constants.TaskType.THUMBNAIL_CAPTURE
    default_display_name = "Capture Thumbnail"
    default_target_path_template = "{project-dir}/{output-dir}/thumbnails"
    icon = "rigger_module_thumbnail_capture"
    category = "Outputs"
    category_icon = "rigger_module_thumbnail_capture"
    is_output_task = True

    def get_default_settings(self):
        """Gets default thumbnail capture settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "image_format": "jpg",
            "width": 1024,
            "height": 1024,
            "camera_name": "",
            "current_frame": True,
            "frame": 1,
            "default_material": False,
            "x_ray": False,
            "wireframe_on_shaded": False,
            "hide_curves": False,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates thumbnail capture settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.modifies_in_place():
            result.add_error("Thumbnail capture cannot modify source files in place. Use a target path.")
        self.validate_positive_int(result, self.settings.get("width"), "width")
        self.validate_positive_int(result, self.settings.get("height"), "height")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Captures a thumbnail for one work item.

        Args:
            work_item (WorkItem): Source work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Thumbnail work item.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            raise task_base.TaskSkip(
                "Thumbnail already exists and overwrite is disabled: {0}".format(output_path),
                output_path=output_path,
                work_item=task_base.WorkItem(
                    source_path=work_item.source_path,
                    current_path=output_path,
                    metadata=dict(work_item.metadata),
                ),
            )
        task_utils.load_source_scene(
            work_item.current_path,
            source_load_mode=self.settings.get("source_load_mode") or "Open",
            load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
        )
        output_dir = os.path.dirname(output_path)
        task_utils.ensure_directory(output_dir)
        rendered_path = capture_thumbnail(
            output_path=output_path,
            image_format=self.settings.get("image_format") or "jpg",
            width=int(self.settings.get("width") or 1024),
            height=int(self.settings.get("height") or 1024),
            frame=None if self.settings.get("current_frame") else int(self.settings.get("frame") or 1),
            panel_options=get_panel_options(self.settings),
        )
        if not rendered_path:
            raise RuntimeError("Unable to capture thumbnail for: {0}".format(work_item.current_path))
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=rendered_path, metadata=metadata)

    def build_output_path(self, work_item, step_output_dir):
        """Builds the thumbnail output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output directory.

        Returns:
            str: Output path.
        """
        image_format = str(self.settings.get("image_format") or "jpg").strip(".")
        return task_utils.build_output_path(work_item, step_output_dir, extension="." + image_format)

    @staticmethod
    def validate_positive_int(result, value, label):
        """Validates a positive integer.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Value to validate.
            label (str): Human-readable label.
        """
        try:
            if int(value) < 1:
                raise ValueError
        except (TypeError, ValueError):
            result.add_error("Thumbnail {0} must be a positive integer.".format(label))


class TaskCapturePlayblast(task_base.BatchTask):
    """Task that captures viewport playblasts for incoming Maya files."""

    task_type = constants.TaskType.PLAYBLAST_CAPTURE
    default_display_name = "Capture Playblast"
    default_target_path_template = "{project-dir}/{output-dir}/playblasts"
    icon = "rigger_module_playblast_capture"
    category = "Outputs"
    category_icon = "rigger_module_playblast_capture"
    is_output_task = True

    def get_default_settings(self):
        """Gets default playblast capture settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "video_format": "qt",
            "width": 1024,
            "height": 1024,
            "camera_name": "",
            "auto_frame_range": True,
            "start_frame": 1,
            "end_frame": 24,
            "show_ornaments": False,
            "default_material": False,
            "x_ray": False,
            "wireframe_on_shaded": False,
            "hide_curves": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates playblast capture settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.modifies_in_place():
            result.add_error("Playblast capture cannot modify source files in place. Use a target path.")
        self.validate_positive_int(result, self.settings.get("width"), "width")
        self.validate_positive_int(result, self.settings.get("height"), "height")
        if self.settings.get("video_format") not in ["qt", "avi", "image", "movie"]:
            result.add_error("Playblast video format must be qt, avi, image, or movie.")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Captures a playblast for one work item.

        Args:
            work_item (WorkItem): Source work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Playblast work item.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            raise task_base.TaskSkip(
                "Playblast already exists and overwrite is disabled: {0}".format(output_path),
                output_path=output_path,
                work_item=task_base.WorkItem(
                    source_path=work_item.source_path,
                    current_path=output_path,
                    metadata=dict(work_item.metadata),
                ),
            )
        task_utils.load_source_scene(
            work_item.current_path,
            source_load_mode=self.settings.get("source_load_mode") or "Open",
            load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
        )
        task_utils.ensure_directory(os.path.dirname(output_path))
        frame_range = self.get_frame_range()
        rendered_path = capture_playblast(
            output_path=output_path,
            video_format=self.settings.get("video_format") or "qt",
            width=int(self.settings.get("width") or 1024),
            height=int(self.settings.get("height") or 1024),
            start_frame=frame_range[0],
            end_frame=frame_range[1],
            show_ornaments=bool(self.settings.get("show_ornaments", False)),
            panel_options=get_panel_options(self.settings),
        )
        if not rendered_path:
            raise RuntimeError("Unable to capture playblast for: {0}".format(work_item.current_path))
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=rendered_path, metadata=metadata)

    def build_output_path(self, work_item, step_output_dir):
        """Builds the playblast output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output directory.

        Returns:
            str: Output path.
        """
        extension_by_format = {"qt": ".mov", "avi": ".avi", "image": ".jpg", "movie": ".mov"}
        extension = extension_by_format.get(self.settings.get("video_format") or "qt", ".mov")
        return task_utils.build_output_path(work_item, step_output_dir, extension=extension)

    def get_frame_range(self):
        """Gets the frame range used for playblast capture.

        Returns:
            tuple: Start and end frame.
        """
        if self.settings.get("auto_frame_range", True):
            import maya.cmds as cmds

            start_frame = int(cmds.playbackOptions(query=True, minTime=True))
            end_frame = int(cmds.playbackOptions(query=True, maxTime=True))
            return start_frame, end_frame
        return int(self.settings.get("start_frame") or 1), int(self.settings.get("end_frame") or 24)

    @staticmethod
    def validate_positive_int(result, value, label):
        """Validates a positive integer.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Value to validate.
            label (str): Human-readable label.
        """
        try:
            if int(value) < 1:
                raise ValueError
        except (TypeError, ValueError):
            result.add_error("Playblast {0} must be a positive integer.".format(label))


def capture_thumbnail(output_path, image_format, width, height, frame=None, panel_options=None):
    """Captures a viewport thumbnail.

    Args:
        output_path (str): Desired output path.
        image_format (str): Image format.
        width (int): Image width.
        height (int): Image height.
        frame (int or None, optional): Frame to capture.
        panel_options (dict, optional): Temporary viewport options.

    Returns:
        str or None: Rendered file path.
    """
    import gt.core.playblast as core_playblast

    output_dir = os.path.dirname(output_path)
    file_name = os.path.splitext(os.path.basename(output_path))[0]
    with TemporaryPanelOptions(panel_options or {}):
        return core_playblast.render_viewport_snapshot(
            file_name=file_name,
            target_dir=output_dir,
            image_format=image_format,
            width=width,
            height=height,
            frame=frame,
        )


def capture_playblast(
    output_path,
    video_format,
    width,
    height,
    start_frame,
    end_frame,
    show_ornaments,
    panel_options=None,
):
    """Captures a viewport playblast.

    Args:
        output_path (str): Desired output path.
        video_format (str): Playblast format.
        width (int): Width in pixels.
        height (int): Height in pixels.
        start_frame (int): Start frame.
        end_frame (int): End frame.
        show_ornaments (bool): Whether to show ornaments.
        panel_options (dict, optional): Temporary viewport options.

    Returns:
        str or None: Rendered file path.
    """
    import gt.core.playblast as core_playblast

    output_dir = os.path.dirname(output_path)
    file_name = os.path.splitext(os.path.basename(output_path))[0]
    with TemporaryPanelOptions(panel_options or {}):
        return core_playblast.render_viewport_playblast(
            file_name=file_name,
            target_dir=output_dir,
            start_frame=start_frame,
            end_frame=end_frame,
            width=width,
            height=height,
            video_format=video_format,
            show_ornaments=show_ornaments,
        )


def get_panel_options(settings):
    """Gets viewport panel options from settings.

    Args:
        settings (dict): Task settings.

    Returns:
        dict: Panel options.
    """
    return {
        "camera_name": settings.get("camera_name") or "",
        "default_material": bool(settings.get("default_material", False)),
        "x_ray": bool(settings.get("x_ray", False)),
        "wireframe_on_shaded": bool(settings.get("wireframe_on_shaded", False)),
        "hide_curves": bool(settings.get("hide_curves", False)),
    }


class TemporaryPanelOptions:
    """Context manager that temporarily applies viewport model panel options."""

    def __init__(self, options):
        """Initializes the panel options context.

        Args:
            options (dict): Options to apply.
        """
        self.options = options or {}
        self.panel = None
        self.previous_values = {}
        self.previous_time = None
        self.previous_camera = None

    def __enter__(self):
        """Applies requested panel options.

        Returns:
            TemporaryPanelOptions: This context manager.
        """
        import maya.cmds as cmds

        self.panel = get_active_model_panel(cmds)
        self.previous_time = cmds.currentTime(query=True)
        if not self.panel:
            return self
        camera_name = self.options.get("camera_name")
        if camera_name:
            camera_name = get_valid_camera_transform(cmds, camera_name)
            self.previous_camera = cmds.modelEditor(self.panel, query=True, camera=True)
            cmds.modelEditor(self.panel, edit=True, camera=camera_name)
        option_map = {
            "default_material": "useDefaultMaterial",
            "x_ray": "xray",
            "wireframe_on_shaded": "wireframeOnShaded",
            "hide_curves": "nurbsCurves",
        }
        for option_key, panel_key in option_map.items():
            if not self.options.get(option_key):
                continue
            current_value = cmds.modelEditor(self.panel, query=True, **{panel_key: True})
            self.previous_values[panel_key] = current_value
            if option_key == "hide_curves":
                cmds.modelEditor(self.panel, edit=True, **{panel_key: False})
            else:
                cmds.modelEditor(self.panel, edit=True, **{panel_key: True})
        try:
            cmds.select(clear=True)
        except Exception:
            pass
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Restores previous panel options.

        Args:
            exception_type (type): Exception type.
            exception_value (Exception): Exception value.
            traceback (traceback): Traceback.
        """
        import maya.cmds as cmds

        if self.previous_time is not None:
            try:
                cmds.currentTime(self.previous_time)
            except Exception:
                pass
        if not self.panel:
            return
        if self.previous_camera:
            try:
                cmds.modelEditor(self.panel, edit=True, camera=self.previous_camera)
            except Exception:
                pass
        for panel_key, previous_value in self.previous_values.items():
            try:
                cmds.modelEditor(self.panel, edit=True, **{panel_key: previous_value})
            except Exception:
                pass


def get_active_model_panel(cmds):
    """Gets the active or first visible model panel.

    Args:
        cmds (module): Maya commands module.

    Returns:
        str or None: Model panel name.
    """
    try:
        panel = cmds.getPanel(withFocus=True)
        if cmds.getPanel(typeOf=panel) == "modelPanel":
            return panel
    except Exception:
        pass
    for panel in cmds.getPanel(type="modelPanel") or []:
        try:
            if cmds.modelEditor(panel, query=True, visible=True):
                return panel
        except Exception:
            pass
    return None


def get_valid_camera_transform(cmds, camera_name):
    """Gets a camera transform from a camera transform or shape name.

    Args:
        cmds (module): Maya commands module.
        camera_name (str): Camera transform or shape name.

    Returns:
        str: Camera transform name.

    Raises:
        RuntimeError: If the camera does not exist or is not a camera.
    """
    camera_name = str(camera_name or "").strip()
    if not camera_name:
        return ""
    if not cmds.objExists(camera_name):
        raise RuntimeError("Capture camera does not exist: {0}".format(camera_name))
    if cmds.objectType(camera_name) == "camera":
        parents = cmds.listRelatives(camera_name, parent=True, fullPath=False) or []
        if parents:
            return parents[0]
    shapes = cmds.listRelatives(camera_name, shapes=True, fullPath=False) or []
    for shape in shapes:
        if cmds.objectType(shape) == "camera":
            return camera_name
    raise RuntimeError("Capture camera is not a camera transform or shape: {0}".format(camera_name))


ThumbnailCaptureTask = TaskCaptureThumbnail
PlayblastCaptureTask = TaskCapturePlayblast
