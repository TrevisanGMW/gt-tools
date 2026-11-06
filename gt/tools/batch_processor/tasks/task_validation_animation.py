"""
Batch Processor Validate Animation Task

Scores every incoming animation file (Maya scene, FBX, or USD) with the motion
evaluation checks (core.motion_eval), optionally stores the score as a Maya attribute, writes
outputs (batch or per-file summaries, JSON reports, and graphs) into the task
folder, runs an optional post-script (for example to copy the score elsewhere),
and logs the report.

Batch-wide outputs are rebuilt after every file from small per-file parts, so
parallel workers each add their file without overwriting the others.

The Skeleton setting decides what is checked: "None" runs the General checks on
any animated nodes, while a skeleton (built-in or Custom Skeleton file) adds the
Biped checks on the mapped joints.

USD files are imported the same way as motion_eval.runner: the scene frame rate
comes from the file, and Z-up files are rotated into Maya's Y up when Align USD
Up Axis is on. Only supported animation files are picked up from the source
folder (other files, such as reports, are ignored).
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_run_state as run_state
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_validation
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks import task_report
from gt.core.motion_eval import outputs
from gt.core.motion_eval import checks_base
from gt.core.motion_eval import presets
from gt.core.motion_eval import sampling
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import templates
from gt.core.motion_eval import usd_scene
import gt.ui.resource_library as ui_res_lib
import fnmatch
import os
import sys

SKELETON_NONE = "none"
SKELETON_CUSTOM = "custom"
SKELETON_SOURCE_VALUES = [SKELETON_NONE] + templates.get_builtin_template_keys() + [SKELETON_CUSTOM]
LEGACY_TEMPLATE_SOURCE_FILE = "file"
PRESET_SOURCE_INLINE = "inline"
PRESET_SOURCE_FILE = "file"
PRESET_SOURCE_VALUES = [PRESET_SOURCE_INLINE, PRESET_SOURCE_FILE]
DEFAULT_CUSTOM_SKELETON_PATH = "{project-dir}/data/custom_skeleton.json"
DEFAULT_PRESET_PATH = "{project-dir}/data/evaluation_preset.json"
DEFAULT_OUTPUT_PATH = "{project-dir}/{task-dir}/{task-sanitized-name}"
LEGACY_GRAPHS_PATH = "{log-dir}/animation_graphs"
PARTS_DIRECTORY_PREFIX = "_validate_animation_parts"
BATCH_SUMMARY_FILE_NAME = outputs.BATCH_SUMMARY_FILE_NAME
BATCH_REPORT_FILE_NAME = outputs.BATCH_REPORT_FILE_NAME
BATCH_GRAPH_FILE_NAME = outputs.BATCH_GRAPH_FILE_NAME
BATCH_GENERAL_SCOPES = [scope for scope in sampling.GENERAL_SCOPES if scope != sampling.SCOPE_SELECTION]
POST_SCRIPT_SAMPLES_DIRECTORY = "validate_animation"
POST_SCRIPT_NAME = "<validate_animation_post_script>"
SCENE_EXTENSIONS = (".ma", ".mb", ".fbx") + usd_scene.USD_EXTENSIONS


class TaskValidationAnimation(task_base.BatchTask):
    """Task that scores the animation of each incoming scene."""

    task_type = constants.TaskType.ANIMATION_VALIDATE
    default_display_name = "Validate Animation"
    default_target_path_template = task_validation.VALIDATION_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.batch_task_validate_animation
    category = "Validation"
    category_icon = ui_res_lib.Icon.batch_category_validation
    is_indexless_task = True
    supports_run_once_after_jobs = True
    supports_run_once_before_jobs = True
    post_script_samples_directory = POST_SCRIPT_SAMPLES_DIRECTORY

    def get_default_settings(self):
        """Gets default Validate Animation settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "load_scene": True,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "align_up_axis": True,
            "filter_enabled": False,
            "filter_include_patterns": "",
            "filter_exclude_patterns": "",
            "filter_collapsed": True,
            "skeleton_source": SKELETON_NONE,
            "custom_skeleton_path": DEFAULT_CUSTOM_SKELETON_PATH,
            "preset_source": PRESET_SOURCE_INLINE,
            "preset": presets.create_preset(mode=checks_base.MODE_GENERAL),
            "preset_path": DEFAULT_PRESET_PATH,
            "range_mode": sampling.RANGE_PLAYBACK,
            "custom_start": 1,
            "custom_end": 100,
            "general_scope": sampling.SCOPE_ALL_JOINTS,
            "node_list": "",
            "log_mode": task_validation.VALIDATION_LOG_ALL,
            "fail_on_failed": True,
            "report_warnings": True,
            "fail_on_error": True,
            "write_score": True,
            "score_target_mode": scene_io.TARGET_DEDICATED_NODE,
            "score_node_name": scene_io.DEFAULT_NODE_NAME,
            "score_attribute": scene_io.DEFAULT_SCORE_ATTRIBUTE,
            "report_attribute": scene_io.DEFAULT_REPORT_ATTRIBUTE,
            "write_report_attribute": True,
            "score_write_policy": scene_io.WRITE_POLICY_OVERWRITE,
            "output_path": DEFAULT_OUTPUT_PATH,
            "summary_batch": True,
            "summary_per_file": False,
            "report_batch": False,
            "report_per_file": False,
            "graphs_batch": False,
            "graphs_per_file": False,
            "graphs_only_on_failure": True,
            "file_folders": True,
            "delete_parts": True,
            "save_scene": False,
            "allow_source_overwrite": False,
            "run_post_script": False,
            "post_script_text": "",
            "post_script_collapsed": True,
            "post_script_font_size": 14,
            "post_script_pass_standard_arguments": True,
            "post_script_pass_environment_arguments": True,
            "preferences_collapsed": False,
            "checks_collapsed": True,
            "score_collapsed": True,
            "output_collapsed": True,
            "actions_collapsed": True,
            "overwrite": True,
            "run_once_before_multi_instance": False,
            "run_once_after_multi_instance": False,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def _normalize_common_settings(self, incoming_settings=None):
        """Normalizes common settings and migrates the older template settings.

        Older projects stored "template_source" (built-in key or "file") and "template_path", and chose
        General or Biped through the preset mode. The skeleton choice now decides the mode, so an
        inline General preset maps to the "None" skeleton.

        Args:
            incoming_settings (dict, optional): Raw settings supplied to the constructor.
        """
        super()._normalize_common_settings(incoming_settings=incoming_settings)
        incoming_settings = incoming_settings or {}
        if "skeleton_source" not in incoming_settings and "template_source" in incoming_settings:
            legacy_source = incoming_settings.get("template_source")
            legacy_mode = presets.resolve_preset(incoming_settings.get("preset") or presets.DEFAULT_PRESET)["mode"]
            if incoming_settings.get("preset_source") != PRESET_SOURCE_FILE and legacy_mode != checks_base.MODE_BIPED:
                self.settings["skeleton_source"] = SKELETON_NONE
            elif legacy_source == LEGACY_TEMPLATE_SOURCE_FILE:
                self.settings["skeleton_source"] = SKELETON_CUSTOM
            elif legacy_source in templates.BUILTIN_TEMPLATES:
                self.settings["skeleton_source"] = legacy_source
        if "custom_skeleton_path" not in incoming_settings and incoming_settings.get("template_path"):
            self.settings["custom_skeleton_path"] = incoming_settings.get("template_path")
        if self.settings.get("skeleton_source") not in SKELETON_SOURCE_VALUES:
            self.settings["skeleton_source"] = SKELETON_NONE
        if self.settings.get("general_scope") == sampling.SCOPE_TEMPLATE_JOINTS:
            self.settings["general_scope"] = sampling.SCOPE_ALL_JOINTS
        self.settings.pop("template_source", None)
        self.settings.pop("template_path", None)
        self.migrate_graph_settings(incoming_settings)

    def migrate_graph_settings(self, incoming_settings):
        """Maps the older Graphs section (export_graphs, graphs_path) to the Output settings.

        Args:
            incoming_settings (dict): Raw settings supplied to the constructor.
        """
        if "graphs_per_file" not in incoming_settings and incoming_settings.get("export_graphs"):
            self.settings["graphs_per_file"] = True
            legacy_path = str(incoming_settings.get("graphs_path") or "").strip()
            if "output_path" not in incoming_settings and legacy_path and legacy_path != LEGACY_GRAPHS_PATH:
                self.settings["output_path"] = legacy_path
        if "output_collapsed" not in incoming_settings and "graphs_collapsed" in incoming_settings:
            self.settings["output_collapsed"] = bool(incoming_settings.get("graphs_collapsed"))
        for legacy_key in ("export_graphs", "graphs_path", "graphs_collapsed"):
            self.settings.pop(legacy_key, None)

    # ------------------------------------------------ Source Files ------------------------------------------------
    def discover_source_files(self, project, task_index=None):
        """Discovers the animation files in the source path, ignoring other files (reports, logs, ...).

        Args:
            project (BatchProcessorModel): Active project model.
            task_index (int, optional): One-based task index.

        Returns:
            list: Sorted normalized animation file paths.
        """
        source_files = super().discover_source_files(project, task_index=task_index)
        return [path for path in source_files if is_supported_file(path) and self.passes_name_filters(path)]

    def passes_name_filters(self, file_path):
        """Checks a file against the optional Include/Exclude name filters.

        Args:
            file_path (str): File path.

        Returns:
            bool: True when filters are off, or the file matches Include and not Exclude.
        """
        if not self.settings.get("filter_enabled", False):
            return True
        return matches_name_filters(
            file_path,
            parse_name_patterns(self.settings.get("filter_include_patterns")),
            parse_name_patterns(self.settings.get("filter_exclude_patterns")),
        )

    def load_scene(self, file_path):
        """Loads an animation file into a new scene.

        USD files are imported with motion_eval (frame rate from the file, up axis alignment); Maya
        scenes and FBX files use the Scene Load settings.

        Args:
            file_path (str): Animation file path.
        """
        if usd_scene.is_usd_file(file_path):
            if self.settings.get("load_relevant_plugins", True):
                batch_processor_maya.load_relevant_file_plugin(file_path)
            usd_scene.load_usd_scene(file_path, align_up_axis=bool(self.settings.get("align_up_axis", True)))
            return
        task_utils.load_source_scene(
            file_path,
            source_load_mode=self.settings.get("source_load_mode") or "Open",
            load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
        )

    # ------------------------------------------- Skeleton / Preset -------------------------------------------
    def get_mode(self):
        """Gets the evaluation mode implied by the skeleton choice.

        Returns:
            str: MODE_GENERAL without a skeleton, MODE_BIPED with one.
        """
        if self.settings.get("skeleton_source", SKELETON_NONE) == SKELETON_NONE:
            return checks_base.MODE_GENERAL
        return checks_base.MODE_BIPED

    def resolve_setting_path(self, project, key):
        """Resolves a path template stored in the settings.

        Args:
            project (BatchProcessorModel): Project used to resolve templates.
            key (str): Setting key.

        Returns:
            str: Resolved path, or an empty string when unset.
        """
        path = str(self.settings.get(key) or "").strip()
        if not path:
            return ""
        if project:
            return project.resolve_template_path(path, task=self)
        return task_base.normalize_path(path)

    def load_skeleton_template(self, project):
        """Loads the configured skeleton.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict or None: Skeleton template, or None when the skeleton is "None".

        Raises:
            IOError, ValueError: If a Custom Skeleton file cannot be loaded.
        """
        source = self.settings.get("skeleton_source") or SKELETON_NONE
        if source == SKELETON_NONE:
            return None
        if source == SKELETON_CUSTOM:
            path = self.resolve_setting_path(project, "custom_skeleton_path")
            if not path:
                raise ValueError("Custom Skeleton file path is empty.")
            return templates.load_template(path)
        if source not in templates.BUILTIN_TEMPLATES:
            source = templates.DEFAULT_TEMPLATE_KEY
        return templates.get_builtin_template(source)

    def load_preset(self, project):
        """Loads the configured evaluation preset, with the mode set by the skeleton choice.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Compact preset.

        Raises:
            IOError, ValueError: If a preset file cannot be loaded.
        """
        if self.settings.get("preset_source") == PRESET_SOURCE_FILE:
            preset = presets.load_preset(self.resolve_setting_path(project, "preset_path"))
        else:
            preset = presets.compact_preset(self.settings.get("preset") or presets.DEFAULT_PRESET)
        resolved = presets.resolve_preset(preset)
        resolved["mode"] = self.get_mode()
        return presets.compact_preset(resolved)

    def validate(self, project):
        """Validates task settings before running.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        try:
            preset = self.load_preset(project)
        except (IOError, OSError, ValueError) as exception:
            result.add_error(f"Validate Animation preset could not be loaded: {exception}")
            return result
        for error in presets.validate_preset(preset):
            result.add_error(f"Validate Animation preset: {error}")
        if self.get_mode() == checks_base.MODE_BIPED:
            try:
                template = self.load_skeleton_template(project)
            except (IOError, OSError, ValueError) as exception:
                result.add_error(f"Validate Animation skeleton could not be loaded: {exception}")
                return result
            for error in templates.validate_template(template, require_biped=True):
                result.add_error(f"Validate Animation skeleton: {error}")
        if self.has_outputs() and not str(self.settings.get("output_path") or "").strip():
            result.add_error("Validate Animation writes outputs but the output folder is empty.")
        if self.settings.get("range_mode") == sampling.RANGE_CUSTOM:
            if int(self.settings.get("custom_end", 0)) <= int(self.settings.get("custom_start", 0)):
                result.add_error("Validate Animation custom frame range needs an end frame after the start frame.")
        if self.settings.get("write_score"):
            if not str(self.settings.get("score_attribute") or "").strip():
                result.add_error("Validate Animation score attribute name cannot be empty.")
            if not self.settings.get("save_scene") and not self.settings.get("run_post_script"):
                result.add_warning(
                    "Validate Animation writes the score attribute but does not save the scene. "
                    "Enable Save Scene (or save from the post-script) to keep it."
                )
        if self.settings.get("run_post_script"):
            script_text = str(self.settings.get("post_script_text") or "")
            if not script_text.strip():
                result.add_error("Validate Animation post-script is enabled but empty.")
            else:
                try:
                    compile(script_text, POST_SCRIPT_NAME, "exec")
                except SyntaxError as exception:
                    result.add_error(
                        f"Validate Animation post-script syntax error on line {exception.lineno}: {exception.msg}"
                    )
        return result

    # ------------------------------------------------ Evaluation ------------------------------------------------
    def get_node_names(self):
        """Gets the Node List entries.

        Returns:
            list: Node names or wildcards.
        """
        return [name.strip() for name in str(self.settings.get("node_list") or "").split(",") if name.strip()]

    def evaluate_current_scene(self, project, include_series=None):
        """Evaluates the scene currently open in Maya (same steps as motion_eval.runner).

        Args:
            project (BatchProcessorModel): Active project.
            include_series (bool, optional): Keep graph series in the report. Defaults to Graphs Per File.

        Returns:
            dict: Evaluation report.

        Raises:
            ValueError, IOError: If settings or scene cannot be evaluated.
        """
        from gt.core.motion_eval import runner

        if include_series is None:
            include_series = outputs.needs_series(self.get_output_options())
        return runner.evaluate_open_scene(
            self.load_preset(project),
            template=self.load_skeleton_template(project),
            range_mode=self.settings.get("range_mode") or sampling.RANGE_PLAYBACK,
            custom_start=self.settings.get("custom_start"),
            custom_end=self.settings.get("custom_end"),
            general_scope=self.settings.get("general_scope") or sampling.SCOPE_ALL_JOINTS,
            node_names=self.get_node_names(),
            include_series=include_series,
        )

    # ------------------------------------------------ Outputs ------------------------------------------------
    def get_output_options(self):
        """Gets the output options in the motion_eval.outputs format.

        Returns:
            dict: Output options.
        """
        return outputs.resolve_output_options(
            dict((key, self.settings.get(key, default)) for key, default in outputs.DEFAULT_OUTPUT_OPTIONS.items())
        )

    def has_outputs(self):
        """Checks whether any summary, report, or graph output is enabled.

        Returns:
            bool: True when at least one output is on.
        """
        return outputs.has_outputs(self.get_output_options())

    def write_file_outputs(self, project, work_item, report):
        """Writes the per-file summary, JSON report, and graphs that are enabled.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being evaluated.
            report (dict): Evaluation report (with graph series when per-file graphs are on).

        Returns:
            list: Written file paths.
        """
        output_root = self.resolve_setting_path(project, "output_path")
        written = outputs.write_file_outputs(
            report,
            work_item.current_path,
            output_root,
            self.get_output_options(),
            relative_dir=task_base.get_work_item_relative_dir(work_item),
        )
        return [task_base.normalize_path(path) for path in written]

    def get_parts_dir(self, step_output_dir):
        """Gets the temporary parts folder, kept in the task's log folder.

        Args:
            step_output_dir (str): Log output directory of this task.

        Returns:
            str: Parts folder.
        """
        task_key = task_base.sanitize_filename(str(self.id or "task"))
        return task_base.normalize_path(os.path.join(step_output_dir, f"{PARTS_DIRECTORY_PREFIX}_{task_key}"))

    def write_batch_outputs(self, project, work_item, report, context=None, step_output_dir=""):
        """Adds this file to the batch outputs and rebuilds the enabled ones.

        Every file writes a small part (one JSON per file) into a temporary folder in the task's log
        folder; the batch summary, report, and graph are then rebuilt from every part of the current
        run, under a lock so parallel workers do not overwrite each other. The parts are deleted when
        the run ends unless Delete Temp Parts is off.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being evaluated.
            report (dict): Evaluation report.
            context (dict, optional): Runner context (run id, last item flags).
            step_output_dir (str, optional): Log output directory. Defaults to the output folder.

        Returns:
            list: Written batch file paths.
        """
        options = self.get_output_options()
        if not outputs.has_batch_outputs(options):
            return []
        from gt.core.motion_eval import batch_summary

        context = context or {}
        output_root = self.resolve_setting_path(project, "output_path")
        parts_dir = self.get_parts_dir(step_output_dir or output_root)
        run_id = task_report.get_run_id(context)
        self.purge_stale_parts_once(parts_dir, run_id)
        entry = batch_summary.build_batch_entry(report, work_item.current_path)
        task_report.write_report_part(parts_dir, {"path": work_item.current_path, "entry": entry}, run_id)
        cleanup = bool(context.get("cleanup_report_parts") and context.get("is_last_item"))
        with task_report.report_lock(parts_dir):
            entries = read_batch_entries(parts_dir, run_id)
            written = outputs.write_batch_outputs(
                entries, output_root, options, settings=report.get("settings"),
                title=self.display_name or self.default_display_name,
            )
            if cleanup and self.settings.get("delete_parts", True):
                task_report.cleanup_report_parts(parts_dir, run_id)
        if cleanup and self.settings.get("delete_parts", True):
            task_report.remove_parts_directory_if_empty(parts_dir)
        return [task_base.normalize_path(path) for path in written]

    def cleanup_run_files(self, project, run_id):
        """Deletes this run's temporary parts after every worker finished (called by the tracker).

        Args:
            project (BatchProcessorModel): Active project.
            run_id (str): Identifier of the finished run.

        Returns:
            int: Number of deleted files.
        """
        if not self.settings.get("delete_parts", True) or not outputs.has_batch_outputs(self.get_output_options()):
            return 0
        task_index = project.get_task_environment_index(self)
        step_output_dir = self.resolve_task_path(project, task_index=task_index)
        parts_dir = self.get_parts_dir(step_output_dir)
        if not os.path.isdir(parts_dir):
            return 0
        with task_report.report_lock(parts_dir, timeout_seconds=0) as acquired:
            if not acquired:
                return 0
            deleted_count = task_report.cleanup_report_parts(parts_dir, run_id)
        task_report.remove_parts_directory_if_empty(parts_dir)
        return deleted_count

    def purge_stale_parts_once(self, parts_dir, run_id):
        """Removes parts left by earlier runs, once per process.

        Args:
            parts_dir (str): Parts folder.
            run_id (str): Identifier of the current run.
        """
        purged = getattr(self, "_purged_output_parts", None)
        if purged is None:
            purged = set()
            setattr(self, "_purged_output_parts", purged)
        if parts_dir in purged:
            return
        purged.add(parts_dir)
        task_report.purge_stale_parts(parts_dir, run_id)

    def write_outputs(self, project, work_item, report, context=None, step_output_dir=""):
        """Writes every enabled output, reporting problems without failing the item.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being evaluated.
            report (dict): Evaluation report.
            context (dict, optional): Runner context.
            step_output_dir (str, optional): Log output directory (holds the temporary parts).

        Returns:
            list: Written file paths.
        """
        if not self.has_outputs():
            return []
        output_root = self.resolve_setting_path(project, "output_path")
        if not output_root or not os.path.isabs(output_root):
            sys.stdout.write(
                "  Outputs skipped: the output folder does not resolve to an absolute path "
                f"({output_root or 'empty'}). Save the project or use an absolute folder.\n"
            )
            return []
        written = []
        for label, writer in (
            ("per-file outputs", lambda: self.write_file_outputs(project, work_item, report)),
            ("batch outputs", lambda: self.write_batch_outputs(project, work_item, report, context, step_output_dir)),
        ):
            try:
                written.extend(path for path in writer() if path)
            except Exception as exception:
                sys.stdout.write(f"  Unable to write {label}: {exception}\n")
        if written:
            sys.stdout.write(f"  Outputs: {len(written)} file(s) in {output_root}\n")
        return written

    def write_score_if_needed(self, report):
        """Writes the score attribute when enabled.

        Args:
            report (dict): Evaluation report.

        Returns:
            dict: Write outcome from scene_io.write_score, or a "disabled" outcome.
        """
        if not self.settings.get("write_score"):
            return {"written": False, "node": "", "attribute": "", "previous": None, "message": "Score writing is off."}
        return scene_io.write_score(
            report,
            target_mode=self.settings.get("score_target_mode") or scene_io.TARGET_DEDICATED_NODE,
            node_name=str(self.settings.get("score_node_name") or "").strip(),
            score_attribute=str(self.settings.get("score_attribute") or "").strip(),
            report_attribute=str(self.settings.get("report_attribute") or "").strip(),
            write_policy=self.settings.get("score_write_policy") or scene_io.WRITE_POLICY_OVERWRITE,
            write_report=bool(self.settings.get("write_report_attribute", True)),
        )

    def run_post_script_if_needed(self, project, work_item, step_output_dir, report, write_outcome, context=None):
        """Runs the optional post-script with the evaluation in its context.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being evaluated.
            step_output_dir (str): Log output directory.
            report (dict): Evaluation report.
            write_outcome (dict): Score attribute write outcome.
            context (dict, optional): Runner context.

        Returns:
            bool: True when a script ran.
        """
        if not self.settings.get("run_post_script"):
            return False
        script_text = str(self.settings.get("post_script_text") or "")
        if not script_text.strip():
            return False
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=work_item,
            output_path=step_output_dir,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": work_item,
                "output_path": step_output_dir,
                "log_dir": step_output_dir,
                "evaluation": report,
                "score": report.get("score"),
                "status": report.get("status"),
                "score_write": write_outcome,
            },
            pass_standard_arguments=self.settings.get("post_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("post_script_pass_environment_arguments", True),
        )
        task_utils.run_inline_python_script(
            script_text=script_text, context=runtime_context, script_name=POST_SCRIPT_NAME
        )
        return True

    def save_scene_if_needed(self, work_item, scene_changed):
        """Saves the evaluated scene in place when enabled and safe.

        The original input file is protected unless Allow Source Overwrite is on.

        Args:
            work_item (WorkItem): Work item being evaluated.
            scene_changed (bool): Whether the score or post-script changed the scene.

        Returns:
            str: Saved path, or an empty string when nothing was saved.

        Raises:
            RuntimeError: If saving would overwrite the original input without permission.
        """
        if not self.settings.get("save_scene") or not scene_changed:
            return ""
        self.check_save_allowed(work_item)
        current_path = work_item.current_path
        batch_processor_maya.save_scene(current_path, file_type=batch_processor_maya.get_maya_file_type(current_path))
        return current_path

    def check_save_allowed(self, work_item):
        """Checks that saving in place is possible and does not overwrite the original input.

        Args:
            work_item (WorkItem): Work item being evaluated.

        Raises:
            RuntimeError: If the file is not a Maya scene or is the protected original input.
        """
        if not self.settings.get("save_scene"):
            return
        current_path = work_item.current_path
        extension = os.path.splitext(current_path)[1].lower()
        if extension not in (".ma", ".mb"):
            raise RuntimeError(f"Validate Animation can only save Maya scenes in place: {current_path}")
        is_source = os.path.normcase(os.path.abspath(current_path)) == os.path.normcase(
            os.path.abspath(work_item.source_path or "")
        )
        if is_source and not self.settings.get("allow_source_overwrite"):
            raise RuntimeError(
                "Validate Animation will not overwrite the original input file. Save a copy first "
                f"(Save Maya File task) or enable Allow Source Overwrite: {current_path}"
            )

    def execute(self, work_item, project, step_output_dir, context=None):
        """Evaluates one incoming scene.

        Args:
            work_item (WorkItem): Work item to evaluate.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Log output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Original work item.

        Raises:
            TaskSkip: The scene could not be evaluated and Fail On Error is off.
            RuntimeError: Evaluation failed and the task is set to fail.
        """
        from gt.core.motion_eval import evaluation

        context = context or {}
        item_label = os.path.basename(work_item.current_path)
        if self.settings.get("load_scene", True) and not is_supported_file(work_item.current_path):
            message = (f"Validate Animation skipped {item_label}: not an animation file "
                       f"({', '.join(SCENE_EXTENSIONS)}).")
            sys.stdout.write(message + "\n")
            raise task_base.TaskSkip(message)
        if not self.passes_name_filters(work_item.current_path):
            message = f"Validate Animation skipped {item_label}: excluded by the name filters."
            sys.stdout.write(message + "\n")
            raise task_base.TaskSkip(message)
        self.check_save_allowed(work_item)
        if self.settings.get("load_scene", True):
            self.load_scene(work_item.current_path)
        try:
            report = self.evaluate_current_scene(project)
        except (ValueError, IOError, OSError) as exception:
            message = f"Validate Animation could not evaluate {item_label}: {exception}"
            sys.stdout.write(message + "\n")
            sys.stdout.flush()
            run_state.record_validation(project, False)
            if self.settings.get("fail_on_error", True):
                raise RuntimeError(message)
            raise task_base.TaskSkip(message)
        self.print_report_summary(item_label, report)
        output_paths = self.write_outputs(project, work_item, report, context, step_output_dir)
        write_outcome = self.write_score_if_needed(report)
        if write_outcome.get("message"):
            sys.stdout.write(f"  {write_outcome['message']}\n")
        script_ran = self.run_post_script_if_needed(project, work_item, step_output_dir, report, write_outcome, context)
        saved_path = self.save_scene_if_needed(work_item, bool(write_outcome.get("written")) or script_ran)
        if saved_path:
            sys.stdout.write(f"  Saved scene: {saved_path}\n")
        sys.stdout.flush()
        status = report.get("status")
        has_issues = status != checks_base.STATUS_PASSED
        run_state.record_validation(project, status != checks_base.STATUS_FAILED)
        task_validation.write_task_validation_log(
            task=self,
            step_output_dir=step_output_dir,
            entry={
                "source": work_item.current_path,
                "score": report.get("score"),
                "status": status,
                "has_issues": has_issues,
                "score_write": write_outcome,
                "saved_path": saved_path,
                "outputs": output_paths,
                "report": evaluation.strip_series(report),
            },
            has_issues=has_issues,
            context=context,
        )
        if status == checks_base.STATUS_WARNING and self.settings.get("report_warnings", True):
            report_warning = context.get("report_warning")
            if callable(report_warning):
                report_warning(f"{item_label}: animation score {report.get('score')} (warning)")
        if status == checks_base.STATUS_FAILED and self.settings.get("fail_on_failed", True):
            raise RuntimeError(
                f"Animation validation failed with score {report.get('score')}: {work_item.current_path}"
            )
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=work_item.current_path,
            metadata=task_utils.build_metadata(self, work_item),
        )

    @staticmethod
    def print_report_summary(item_label, report):
        """Prints a concise evaluation summary.

        Args:
            item_label (str): File name or label.
            report (dict): Evaluation report.
        """
        from gt.core.motion_eval import evaluation

        sys.stdout.write(f"Validate Animation [{report.get('status')}] {item_label}\n")
        for line in evaluation.summarize_report(report):
            sys.stdout.write(f"  {line}\n")
        sys.stdout.flush()

    def run_on_current_scene(self, project):
        """Evaluates the scene open in Maya. Nothing is loaded, written, saved, output, or logged.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Evaluation report (without graph series).
        """
        return self.evaluate_current_scene(project, include_series=False)


def is_supported_file(file_path):
    """Checks whether a file is an animation file the task can load.

    Args:
        file_path (str): File path.

    Returns:
        bool: True for Maya scenes, FBX, and USD files.
    """
    return os.path.splitext(str(file_path or ""))[1].lower() in SCENE_EXTENSIONS


def parse_name_patterns(value):
    """Parses comma, semicolon, or newline separated name patterns.

    Args:
        value (str or list): Raw pattern text or list.

    Returns:
        list: Clean, lowercase patterns. Text without wildcards becomes a "contains" pattern.
    """
    if isinstance(value, (list, tuple)):
        raw_items = value
    else:
        raw_items = str(value or "").replace(";", "\n").replace(",", "\n").splitlines()
    patterns = []
    for item in raw_items:
        pattern = str(item).strip().replace("\\", "/").lower()
        if not pattern:
            continue
        if not any(character in pattern for character in "*?["):
            pattern = f"*{pattern}*"
        patterns.append(pattern)
    return patterns


def matches_name_filters(file_path, include_patterns, exclude_patterns):
    """Checks a file name (or path) against include and exclude patterns.

    Args:
        file_path (str): File path.
        include_patterns (list): Lowercase patterns from parse_name_patterns. Empty keeps every file.
        exclude_patterns (list): Lowercase patterns from parse_name_patterns.

    Returns:
        bool: True when the file matches an include pattern (or there are none) and no exclude pattern.
    """
    normalized_path = str(file_path or "").replace("\\", "/").lower()
    candidates = [os.path.basename(normalized_path), normalized_path]

    def matches_any(patterns):
        """Checks whether any pattern matches the file name or path.

        Args:
            patterns (list): Patterns to test.

        Returns:
            bool: True when one pattern matches.
        """
        return any(fnmatch.fnmatchcase(candidate, pattern) for pattern in patterns for candidate in candidates)

    if include_patterns and not matches_any(include_patterns):
        return False
    return not matches_any(exclude_patterns)


def read_batch_entries(parts_dir, run_id):
    """Reads the batch entries written by the current run.

    Args:
        parts_dir (str): Parts folder.
        run_id (str): Identifier of the current run.

    Returns:
        list: Batch entries.
    """
    entries = []
    for part_path in task_report.list_part_paths(parts_dir):
        part_data = task_report.read_json_file(part_path)
        if part_data and part_data.get("run_id") == run_id and part_data.get("entry"):
            entries.append(part_data["entry"])
    return entries
