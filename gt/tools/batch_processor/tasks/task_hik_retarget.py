"""
Batch Processor HumanIK Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import os
import sys


HIK_BAKE_TARGET_NONE = "None"
HIK_BAKE_TARGET_SKELETON = "Skeleton"
HIK_BAKE_TARGET_CONTROL_RIG = "Control Rig"
HIK_BAKE_TARGET_CUSTOM_CONTROL_RIG = "Custom Control Rig"
HIK_BAKE_TARGETS = [
    HIK_BAKE_TARGET_NONE,
    HIK_BAKE_TARGET_SKELETON,
    HIK_BAKE_TARGET_CONTROL_RIG,
    HIK_BAKE_TARGET_CUSTOM_CONTROL_RIG,
]
DEFAULT_PRE_BAKE_SCRIPT_TEXT = """# Optional HumanIK pre-bake pass.
# Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args: input, output, project, project_dir, task, task_id, etc.
#   environment_variables / env: Project environment variables.
#   project, task, work_item, output_path, source_character, target_character,
#   imported_source_nodes, imported_target_nodes.
import pprint
import sys
import maya.cmds as cmds

sys.stdout.write("HumanIK pre-bake script\\n")
sys.stdout.write("Input: {0}\\n".format(args.get("input") or context.get("source_path")))
sys.stdout.write("Output: {0}\\n".format(args.get("output") or output_path))
sys.stdout.write("Arguments:\\n")
pprint.pprint(arguments)
sys.stdout.write("Environment Variables:\\n")
pprint.pprint(environment_variables)
"""
DEFAULT_POST_SCRIPT_TEXT = """# Optional HumanIK cleanup pass.
# Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args: input, output, project, project_dir, task, task_id, etc.
#   environment_variables / env: Project environment variables.
#   project, task, work_item, output_path, source_character, target_character,
#   imported_source_nodes, imported_target_nodes.
import pprint
import sys
import maya.cmds as cmds

sys.stdout.write("HumanIK post script\\n")
sys.stdout.write("Input: {0}\\n".format(args.get("input") or context.get("source_path")))
sys.stdout.write("Output: {0}\\n".format(args.get("output") or output_path))
sys.stdout.write("Arguments:\\n")
pprint.pprint(arguments)
sys.stdout.write("Environment Variables:\\n")
pprint.pprint(environment_variables)
"""


class TaskRetargetHumanIK(task_base.BatchTask):
    """Task that retargets animation using Maya HumanIK."""

    task_type = constants.TaskType.HIK_RETARGET
    default_display_name = "HumanIK"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_hik_retarget"
    icon = "tool_retargeter"
    category = "Animation"
    category_icon = "root_animation"

    def get_default_settings(self):
        """Gets default HumanIK retarget settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "source_namespace": "source",
            "target_namespace": "target",
            "source_root": "",
            "source_character_name": "source",
            "source_character_pre_existing": False,
            "source_character_auto_detect": False,
            "source_definition_path": "{project-dir}/data/source_hik.xml",
            "source_tpose_path": "{project-dir}/data/source_tpose.pose",
            "target_rig_path": "",
            "target_character_name": "",
            "load_target_properties": False,
            "target_properties_path": "",
            "set_framerate": True,
            "framerate": 30,
            "bake_animation": True,
            "bake_target": HIK_BAKE_TARGET_SKELETON,
            "force_proxy_bake": False,
            "run_pre_bake_script": False,
            "pre_bake_script_text": DEFAULT_PRE_BAKE_SCRIPT_TEXT,
            "pre_bake_script_collapsed": True,
            "pre_bake_script_font_size": 14,
            "pre_bake_script_pass_standard_arguments": True,
            "pre_bake_script_pass_environment_arguments": True,
            "delete_source_elements": True,
            "delete_source_namespace": True,
            "run_post_script": False,
            "post_script_text": DEFAULT_POST_SCRIPT_TEXT,
            "post_script_collapsed": True,
            "post_script_font_size": 14,
            "post_script_pass_standard_arguments": True,
            "post_script_pass_environment_arguments": True,
            "output_extension": ".ma",
            "overwrite": False,
        }

    def validate(self, project):
        """Validates HumanIK retarget settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.get_output_extension() not in [".ma", ".mb", ".fbx"]:
            result.add_error("HumanIK retarget output extension must be .ma, .mb, or .fbx.")
        if self.settings.get("set_framerate"):
            try:
                if int(float(self.settings.get("framerate"))) < 1:
                    result.add_error("HumanIK retarget framerate must be greater than zero.")
            except (TypeError, ValueError):
                result.add_error("HumanIK retarget framerate must be numeric.")
        if self.settings.get("bake_target") not in HIK_BAKE_TARGETS:
            result.add_error("HumanIK retarget bake target is invalid.")
        pre_bake_script_text = self.settings.get("pre_bake_script_text")
        if pre_bake_script_text is None:
            pre_bake_script_text = DEFAULT_PRE_BAKE_SCRIPT_TEXT
        if self.settings.get("run_pre_bake_script") and not pre_bake_script_text:
            result.add_error("HumanIK pre-bake script is enabled but no inline script is set.")
        source_path_checks = []
        if not self.uses_pre_existing_source_character():
            source_path_checks = [
                ("source_definition_path", "Source HIK definition"),
                ("source_tpose_path", "Source T-pose"),
            ]
        for key, label in source_path_checks + [("target_rig_path", "Target rig")]:
            path = self.get_resolved_path(project, key)
            if path and not os.path.isfile(path):
                result.add_error("{0} does not exist: {1}".format(label, path))
        if self.settings.get("load_target_properties"):
            properties_path = self.get_resolved_path(project, "target_properties_path")
            if not properties_path:
                result.add_error("HumanIK target properties are enabled but no properties file is configured.")
            elif not os.path.isfile(properties_path):
                result.add_error("Target HumanIK properties do not exist: {0}".format(properties_path))
        post_script_text = self.settings.get("post_script_text")
        if post_script_text is None:
            post_script_text = DEFAULT_POST_SCRIPT_TEXT
        if self.settings.get("run_post_script") and not post_script_text:
            result.add_error("HumanIK post script is enabled but no inline script is set.")
        if (
            self.uses_pre_existing_source_character()
            and not self.uses_auto_detected_source_character()
            and not self.settings.get("source_character_name")
        ):
            result.add_error("Pre-existing HumanIK source character mode requires a Source Character name.")
        if not self.uses_pre_existing_source_character() and not self.settings.get("source_definition_path"):
            result.add_warning("HumanIK retarget has no source HIK XML definition path configured.")
        if not self.settings.get("target_character_name") and not self.settings.get("target_rig_path"):
            result.add_warning("HumanIK retarget has no explicit target character or target rig path configured.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before retargeting.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        output_paths = {}
        for work_item in work_items:
            output_path = self.build_output_path(work_item, step_output_dir)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "HumanIK retarget collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning("HumanIK retarget output already exists and will be skipped: {0}".format(output_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs HumanIK retargeting for one work item.

        Args:
            work_item (WorkItem): Source animation work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Retargeted output work item.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            skipped_item = task_base.WorkItem(
                source_path=work_item.source_path,
                current_path=output_path,
                metadata=dict(work_item.metadata),
            )
            raise task_base.TaskSkip(
                "Output already exists and overwrite is disabled: {0}".format(output_path),
                output_path=output_path,
                work_item=skipped_item,
            )
        self._runtime_source_namespace = ""
        self._runtime_target_namespace = ""
        self._runtime_source_character = ""
        imported_source_nodes = self.load_source(work_item.current_path)
        batch_processor_maya.apply_scene_options(self.settings)
        if self.settings.get("set_framerate"):
            self.round_playback_range_to_whole_frames()
        source_playback_range = self.capture_playback_range()
        imported_target_nodes = self.import_target_rig(project)
        self.restore_playback_range(source_playback_range)
        for hik_node in self.get_hik_characters():
            self.evaluate_hik_character(hik_node)
        source_character = self.setup_source_character(project)
        target_character = self.get_target_character()
        if not source_character:
            raise RuntimeError("Unable to create or find a HumanIK source character.")
        if not target_character:
            raise RuntimeError("Unable to find a HumanIK target character.")
        self.load_target_hik_properties(project, target_character)

        def run_pre_bake_script():
            """Runs the configured pre-bake script with the active task context."""
            self.run_pre_bake_script_if_needed(
                project=project,
                work_item=work_item,
                output_path=output_path,
                source_character=source_character,
                target_character=target_character,
                imported_source_nodes=imported_source_nodes,
                imported_target_nodes=imported_target_nodes,
                context=context,
            )

        self.retarget_and_bake(
            source_character=source_character,
            target_character=target_character,
            pre_bake_callback=run_pre_bake_script,
        )
        self.run_post_script_if_needed(
            project=project,
            work_item=work_item,
            output_path=output_path,
            source_character=source_character,
            target_character=target_character,
            imported_source_nodes=imported_source_nodes,
            imported_target_nodes=imported_target_nodes,
            context=context,
        )
        self.cleanup_source(project, imported_source_nodes, source_character)
        self.write_output(output_path)
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def load_source(self, source_path):
        """Loads the source animation file.

        Args:
            source_path (str): Source file path.

        Returns:
            list: Imported source nodes when using import mode.
        """
        load_relevant_plugins = self.settings.get("load_relevant_plugins", True)
        source_load_mode = self.settings.get("source_load_mode") or "Import"
        source_load_mode = str(source_load_mode).lower()
        extension = os.path.splitext(source_path)[1].lower()
        if source_load_mode == "open" and extension == ".fbx":
            self.open_fbx_source_scene(source_path)
            imported_nodes = self.apply_source_namespace_to_opened_scene(self.get_source_scene_nodes())
            self._runtime_source_namespace = self.detect_runtime_namespace(
                imported_nodes=imported_nodes,
                requested_namespace=self.settings.get("source_namespace") or "",
                root_name=self.settings.get("source_root") or "",
            )
            return imported_nodes
        if source_load_mode == "open" and extension in [".ma", ".mb"]:
            batch_processor_maya.open_scene(source_path, load_relevant_plugins=load_relevant_plugins)
            imported_nodes = self.apply_source_namespace_to_opened_scene(self.get_source_scene_nodes())
            self._runtime_source_namespace = self.detect_runtime_namespace(
                imported_nodes=imported_nodes,
                requested_namespace=self.settings.get("source_namespace") or "",
                root_name=self.settings.get("source_root") or "",
            )
            return imported_nodes
        batch_processor_maya.new_scene()
        if extension == ".fbx":
            imported_nodes = self.import_fbx_source_animation(
                source_path,
                namespace=self.settings.get("source_namespace") or None,
            )
        else:
            imported_nodes = self.import_file_with_namespace(
                source_path,
                namespace=self.settings.get("source_namespace") or None,
                load_relevant_plugins=load_relevant_plugins,
            )
        self._runtime_source_namespace = self.detect_runtime_namespace(
            imported_nodes=imported_nodes,
            requested_namespace=self.settings.get("source_namespace") or "",
            root_name=self.settings.get("source_root") or "",
        )
        requested_namespace = self.clean_namespace(self.settings.get("source_namespace") or "")
        if requested_namespace and not self._runtime_source_namespace:
            sys.stdout.write(
                "[WARNING] - (HumanIK) - Source namespace '{0}' was requested, but imported source nodes were "
                "not namespaced. Characterization will use unnamespaced source nodes.\n".format(requested_namespace)
            )
        return imported_nodes

    def import_target_rig(self, project):
        """Imports the optional target rig file.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Imported target nodes.
        """
        target_rig_path = self.get_resolved_path(project, "target_rig_path")
        if not target_rig_path:
            return []
        imported_nodes = self.import_file_with_namespace(
            target_rig_path,
            namespace=self.settings.get("target_namespace") or None,
            load_relevant_plugins=True,
        )
        self._runtime_target_namespace = self.detect_runtime_namespace(
            imported_nodes=imported_nodes,
            requested_namespace=self.settings.get("target_namespace") or "",
            root_name="",
        )
        return imported_nodes

    def setup_source_character(self, project):
        """Creates or updates the HumanIK source definition.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Source HIK character node.
        """
        requested_character = self.settings.get("source_character_name") or "source"
        source_namespace = self.get_runtime_source_namespace()
        if self.uses_pre_existing_source_character():
            source_character = self.get_pre_existing_source_character(requested_character)
            self._runtime_source_character = source_character
            if not source_character:
                raise RuntimeError(
                    "Pre-existing HumanIK source character '{0}' does not exist. "
                    "Available HIK characters: {1}".format(
                        requested_character,
                        ", ".join(self.get_hik_characters()) or "None",
                    )
                )
            self.evaluate_hik_character(source_character)
            return source_character

        import gt.core.io as core_io
        import gt.core.pose as core_pose
        import gt.utils.hik as utils_hik

        requested_character = self.get_namespaced_name(requested_character, source_namespace)
        source_character = self.get_or_create_hik_character(requested_character)
        self._runtime_source_character = source_character
        if not source_character:
            return ""
        utils_hik.set_definition_lock(source_character, False)
        current_pose = None
        joints = self.get_source_joints()
        if joints:
            current_pose = core_pose.get_pose_as_dict(joints)
        tpose_path = self.get_resolved_path(project, "source_tpose_path")
        if tpose_path:
            tpose_dict = core_io.read_json_dict(tpose_path)
            if tpose_dict:
                applied_tpose_joints = core_pose.set_pose_from_dict(tpose_dict, namespace=source_namespace)
                if not applied_tpose_joints:
                    raise RuntimeError(
                        "Source T-pose did not match any joints using namespace '{0}': {1}".format(
                            source_namespace or "<root>",
                            tpose_path,
                        )
                    )
                self.force_joint_evaluation(joints)
        definition_path = self.get_resolved_path(project, "source_definition_path")
        if definition_path:
            source_namespace = self.get_runtime_source_namespace()
            prefix = "{0}:".format(source_namespace.strip(":")) if source_namespace else ""
            utils_hik.import_definition_from_xml(source_character, definition_path, prefix=prefix)
        utils_hik.set_definition_lock(source_character, True)
        self.evaluate_hik_character(source_character)
        if current_pose:
            core_pose.set_pose_from_dict(current_pose, namespace=source_namespace)
            self.force_joint_evaluation(joints)
        self.evaluate_hik_character(source_character)
        return source_character

    def uses_pre_existing_source_character(self):
        """Gets whether the source scene already contains the HumanIK source character.

        Returns:
            bool: True when source XML and T-pose setup should be skipped.
        """
        return bool(self.settings.get("source_character_pre_existing", False))

    def uses_auto_detected_source_character(self):
        """Gets whether the source character should be auto-detected from the scene.

        Returns:
            bool: True when pre-existing mode should auto-detect the source character.
        """
        return self.uses_pre_existing_source_character() and bool(
            self.settings.get("source_character_auto_detect", False)
        )

    def get_auto_detected_source_character(self):
        """Gets the first HumanIK character in the scene that is not the target character.

        Returns:
            str: Auto-detected source HIK character node, or empty string.
        """
        target_character = self.get_target_character()
        for hik_node in self.get_hik_characters():
            if hik_node and hik_node != target_character:
                return hik_node
        return ""

    def get_pre_existing_source_character(self, requested_character):
        """Gets an existing source HumanIK character without creating one.

        Args:
            requested_character (str): Requested source character name.

        Returns:
            str: Existing source HIK character node, or empty string.
        """
        if self.uses_auto_detected_source_character():
            auto_detected_character = self.get_auto_detected_source_character()
            if auto_detected_character:
                return auto_detected_character
        source_namespace = self.get_runtime_source_namespace()
        source_character = self.resolve_hik_character_for_namespace(requested_character, source_namespace)
        if source_character and self.is_hik_character(source_character):
            return source_character
        resolved_character = self.resolve_hik_character(requested_character)
        if resolved_character and self.is_hik_character(resolved_character):
            return resolved_character
        return ""

    def retarget_and_bake(self, source_character, target_character, pre_bake_callback=None):
        """Assigns the source character to the target and optionally bakes.

        Args:
            source_character (str): Source HIK character.
            target_character (str): Target HIK character.
            pre_bake_callback (callable, optional): Function run after source assignment and before optional baking.
        """
        import gt.utils.hik as utils_hik

        self.evaluate_hik_character(source_character)
        self.evaluate_hik_character(target_character)
        if not utils_hik.set_definition_source(target_character, source_character):
            self.evaluate_hik_character(source_character)
            self.evaluate_hik_character(target_character)
            if not utils_hik.set_definition_source(target_character, source_character):
                raise RuntimeError(
                    "Unable to assign HumanIK source character '{0}' to target character '{1}'. "
                    "Available HIK characters: {2}".format(
                        source_character,
                        target_character,
                        ", ".join(self.get_hik_characters()) or "None",
                    )
                )
        if callable(pre_bake_callback):
            pre_bake_callback()
        if not self.settings.get("bake_animation", True):
            return
        bake_target = self.settings.get("bake_target") or HIK_BAKE_TARGET_SKELETON
        if bake_target == HIK_BAKE_TARGET_NONE:
            return
        if bake_target == HIK_BAKE_TARGET_SKELETON:
            success = utils_hik.bake_to_skeleton(
                target_character,
                force_proxy=bool(self.settings.get("force_proxy_bake", False)),
            )
        else:
            success = utils_hik.bake_to_control_rig(target_character)
        if not success:
            raise RuntimeError("HumanIK bake failed for target: {0}".format(target_character))

    def load_target_hik_properties(self, project, target_character):
        """Loads optional HumanIK properties onto the resolved target character.

        Args:
            project (BatchProcessorModel): Active project.
            target_character (str): Resolved target HumanIK character node.

        Returns:
            dict: Properties successfully applied.
        """
        if not self.settings.get("load_target_properties", False):
            return {}
        import gt.core.io as core_io
        import gt.utils.hik as utils_hik

        properties_path = self.get_resolved_path(project, "target_properties_path")
        properties = core_io.read_json_dict(properties_path)
        if not isinstance(properties, dict) or not properties:
            raise RuntimeError("Target HumanIK properties file is empty or invalid: {0}".format(properties_path))
        applied_properties = utils_hik.set_hik_properties(target_character, properties)
        if not applied_properties:
            raise RuntimeError(
                "No HumanIK properties could be applied to target character '{0}' from: {1}".format(
                    target_character,
                    properties_path,
                )
            )
        sys.stdout.write(
            "[HumanIK] Applied {0} target properties from: {1}\n".format(
                len(applied_properties),
                properties_path,
            )
        )
        self.evaluate_hik_character(target_character)
        return applied_properties

    def run_pre_bake_script_if_needed(
        self,
        project,
        work_item,
        output_path,
        source_character,
        target_character,
        imported_source_nodes,
        imported_target_nodes,
        context=None,
    ):
        """Runs the optional script after source assignment and before optional baking.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Source work item.
            output_path (str): Output path.
            source_character (str): Source HIK character.
            target_character (str): Target HIK character.
            imported_source_nodes (list): Imported source nodes.
            imported_target_nodes (list): Imported target nodes.
            context (dict, optional): Runner context.
        """
        if not self.settings.get("run_pre_bake_script"):
            return
        script_text = self.settings.get("pre_bake_script_text")
        if script_text is None:
            script_text = DEFAULT_PRE_BAKE_SCRIPT_TEXT
        if not script_text.strip():
            return
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=work_item,
            output_path=output_path,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": work_item,
                "output_path": output_path,
                "source_character": source_character,
                "target_character": target_character,
                "imported_source_nodes": list(imported_source_nodes or []),
                "imported_target_nodes": list(imported_target_nodes or []),
            },
            pass_standard_arguments=self.settings.get("pre_bake_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("pre_bake_script_pass_environment_arguments", True),
        )
        run_inline_python_script(
            script_text=script_text,
            context=runtime_context,
            script_name="<humanik_pre_bake_script>",
        )

    def run_post_script_if_needed(
        self,
        project,
        work_item,
        output_path,
        source_character,
        target_character,
        imported_source_nodes,
        imported_target_nodes,
        context=None,
    ):
        """Runs the optional post-retarget Python cleanup script.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Source work item.
            output_path (str): Output path.
            source_character (str): Source HIK character.
            target_character (str): Target HIK character.
            imported_source_nodes (list): Imported source nodes.
            imported_target_nodes (list): Imported target nodes.
            context (dict, optional): Runner context.
        """
        if not self.settings.get("run_post_script"):
            return
        script_text = self.settings.get("post_script_text")
        if script_text is None:
            script_text = DEFAULT_POST_SCRIPT_TEXT
        if not script_text.strip():
            return
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=work_item,
            output_path=output_path,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": work_item,
                "output_path": output_path,
                "source_character": source_character,
                "target_character": target_character,
                "imported_source_nodes": list(imported_source_nodes or []),
                "imported_target_nodes": list(imported_target_nodes or []),
            },
            pass_standard_arguments=self.settings.get("post_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("post_script_pass_environment_arguments", True),
        )
        run_inline_python_script(
            script_text=script_text,
            context=runtime_context,
            script_name="<humanik_post_script>",
        )

    def cleanup_source(self, project, imported_source_nodes, source_character):
        """Deletes source elements and merges namespaces when requested.

        Args:
            project (BatchProcessorModel): Active project.
            imported_source_nodes (list): Imported source nodes.
            source_character (str): Source HIK character.
        """
        if self.settings.get("delete_source_elements", True):
            delete_targets = []
            source_root = self.get_source_root()
            if source_root:
                delete_targets.append(source_root)
            delete_targets.extend(imported_source_nodes or [])
            delete_targets.append(source_character)
            self.delete_source_nodes(delete_targets)
        try:
            import gt.utils.hik as utils_hik

            utils_hik.delete_unused_definitions()
        except Exception:
            pass
        if self.settings.get("delete_source_namespace", True):
            for namespace in [self.get_runtime_source_namespace(), self.get_runtime_target_namespace()]:
                if namespace:
                    self.delete_namespace(namespace)

    @staticmethod
    def resolve_delete_paths(requested_nodes):
        """Resolves requested nodes to unique deletable paths.

        Non-unique short names are expanded to their full DAG paths so each
        matching object can be deleted individually. Names that match a single
        object (including non-DAG nodes such as HIK character nodes) are kept as
        returned by Maya. Duplicate paths are removed while preserving a
        deepest-first order so children are addressed before their parents.

        Args:
            requested_nodes (list): Requested node names, possibly non-unique.

        Returns:
            list: Unique full paths to delete, ordered deepest-first.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        resolved_paths = []
        for node in requested_nodes or []:
            if not node:
                continue
            try:
                matches = cmds.ls(node, long=True) or []
            except Exception:
                matches = []
            for match in matches:
                if match and match not in resolved_paths:
                    resolved_paths.append(match)
        return sorted(resolved_paths, key=lambda item: str(item).count("|"), reverse=True)

    def delete_source_nodes(self, requested_nodes):
        """Deletes source nodes one at a time, logging failures instead of erroring.

        Each requested name is resolved to its full path(s) so non-unique or
        dirty scene names do not abort the whole deletion. Nodes already removed
        by an earlier parent deletion are skipped silently.

        Args:
            requested_nodes (list): Requested node names to delete.

        Returns:
            dict: Counts keyed by "deleted", "skipped", and "failed".
        """
        cmds = batch_processor_maya.get_maya_cmds()
        counts = {"deleted": 0, "skipped": 0, "failed": 0}
        for path in self.resolve_delete_paths(requested_nodes):
            try:
                if not cmds.objExists(path):
                    counts["skipped"] += 1
                    continue
                cmds.delete(path)
                counts["deleted"] += 1
            except Exception as exception:
                counts["failed"] += 1
                sys.stdout.write(
                    "[WARNING] - (HumanIK) - Unable to delete source element '{0}': {1}\n".format(path, exception)
                )
                sys.stdout.flush()
        if counts["failed"]:
            sys.stdout.write(
                "[HumanIK] Source cleanup deleted {0}, skipped {1}, failed {2}.\n".format(
                    counts["deleted"], counts["skipped"], counts["failed"]
                )
            )
            sys.stdout.flush()
        return counts

    def write_output(self, output_path):
        """Writes the retargeted scene.

        Args:
            output_path (str): Destination path.
        """
        output_extension = self.get_output_extension()
        if output_extension in [".ma", ".mb"]:
            batch_processor_maya.save_scene(output_path, batch_processor_maya.get_maya_file_type(output_path))
            return
        import gt.utils.fbx as utils_fbx

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with utils_fbx.FbxExporter(selection=False, key_reducer=False) as fbx:
            fbx.set_preferences_animation()
            fbx.export_file(path=output_path)

    def build_output_path(self, work_item, step_output_dir):
        """Builds the retarget output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output folder.

        Returns:
            str: Output path.
        """
        return task_utils.build_output_path(work_item, step_output_dir, extension=self.get_output_extension())

    def get_output_extension(self):
        """Gets the normalized output extension.

        Returns:
            str: Output extension.
        """
        extension = str(self.settings.get("output_extension") or ".ma").lower()
        if not extension.startswith("."):
            extension = "." + extension
        return extension

    def get_resolved_path(self, project, key):
        """Gets a resolved task path setting.

        Args:
            project (BatchProcessorModel): Active project.
            key (str): Settings key.

        Returns:
            str: Resolved path.
        """
        value = self.settings.get(key) or ""
        return project.resolve_template_path(value, task=self) if value else ""

    def get_source_root(self):
        """Gets the source root with namespace applied when needed.

        Returns:
            str: Source root node.
        """
        return self.resolve_existing_node(
            self.settings.get("source_root") or "",
            self.get_runtime_source_namespace(),
        )

    def get_source_joints(self):
        """Gets source joints from the configured root.

        Returns:
            list: Source joint nodes.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        source_root = self.get_source_root()
        if not source_root or not cmds.objExists(source_root):
            return []
        current_selection = cmds.ls(selection=True) or []
        try:
            cmds.select(source_root, hierarchy=True)
            return cmds.ls(selection=True, type="joint") or []
        finally:
            if current_selection:
                cmds.select(current_selection)
            else:
                cmds.select(clear=True)

    def get_target_character(self):
        """Gets the target HumanIK character node.

        Returns:
            str: Target HIK character node.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        explicit_name = self.settings.get("target_character_name") or ""
        target_namespace = self.get_runtime_target_namespace()
        if explicit_name:
            candidate = self.get_namespaced_name(explicit_name, target_namespace)
            if cmds.objExists(candidate):
                return candidate
            if cmds.objExists(explicit_name):
                return explicit_name
        if target_namespace:
            namespaced_nodes = cmds.ls("{0}:*".format(target_namespace.strip(":")), type="HIKCharacterNode") or []
            if namespaced_nodes:
                return namespaced_nodes[0]
        source_name = getattr(self, "_runtime_source_character", "") or self.resolve_hik_character(
            self.settings.get("source_character_name") or ""
        )
        for hik_node in cmds.ls(type="HIKCharacterNode") or []:
            if hik_node != source_name:
                return hik_node
        return ""

    def get_or_create_hik_character(self, requested_name):
        """Gets or creates a HIK character using Maya's actual resulting node name.

        Args:
            requested_name (str): Preferred HIK character name.

        Returns:
            str: Existing or newly created HIK character node.
        """
        import gt.utils.hik as utils_hik

        requested_name = str(requested_name or "source")
        existing_character = self.resolve_hik_character(requested_name)
        if existing_character:
            return existing_character
        before_characters = set(self.get_hik_characters())
        created_character = utils_hik.create_definition(requested_name)
        self.evaluate_hik_character(created_character)
        if self.is_hik_character(created_character):
            return created_character
        after_characters = set(self.get_hik_characters())
        new_characters = list(after_characters.difference(before_characters))
        if new_characters:
            requested_short_name = requested_name.rpartition(":")[-1]
            new_characters.sort(key=lambda node: (not self.hik_name_matches(node, requested_short_name), node))
            new_character = new_characters[0]
            if ":" in requested_name and new_character != requested_name:
                renamed_character = utils_hik.rename_definition(new_character, requested_name)
                if self.is_hik_character(renamed_character):
                    return renamed_character
            return new_character
        resolved_character = self.resolve_hik_character(requested_name)
        if resolved_character:
            return resolved_character
        return created_character

    def resolve_hik_character(self, requested_name):
        """Resolves a HIK character from a requested name.

        Args:
            requested_name (str): Requested HIK character name.

        Returns:
            str: Existing HIK character node, or empty string.
        """
        requested_name = str(requested_name or "")
        if self.is_hik_character(requested_name):
            return requested_name
        exact_matches = []
        fuzzy_matches = []
        for hik_node in self.get_hik_characters():
            short_name = hik_node.rpartition(":")[-1]
            if short_name == requested_name:
                exact_matches.append(hik_node)
            elif self.hik_name_matches(hik_node, requested_name):
                fuzzy_matches.append(hik_node)
        if exact_matches:
            return sorted(exact_matches)[0]
        if fuzzy_matches:
            return sorted(fuzzy_matches)[0]
        return ""

    def resolve_hik_character_for_namespace(self, character_name, namespace=""):
        """Resolves a HIK character while allowing skeleton namespace fallback.

        Maya may keep HumanIK character nodes unnamespaced even when the
        skeleton objects are namespaced. This resolver tries the explicit
        namespaced node first, then falls back to the raw and short character
        names.

        Args:
            character_name (str): Requested HumanIK character name.
            namespace (str, optional): Skeleton namespace from task settings.

        Returns:
            str: Existing HIK character node, or the best requested candidate.
        """
        candidates = self.get_hik_character_namespace_candidates(character_name, namespace)
        for candidate in candidates:
            if self.is_hik_character(candidate):
                return candidate
        for candidate in candidates:
            resolved_character = self.resolve_hik_character(candidate)
            if resolved_character and self.is_hik_character(resolved_character):
                return resolved_character
        return candidates[0] if candidates else ""

    @staticmethod
    def get_hik_character_namespace_candidates(character_name, namespace=""):
        """Gets HIK character name candidates for a skeleton namespace.

        Args:
            character_name (str): Requested HumanIK character name.
            namespace (str, optional): Skeleton namespace.

        Returns:
            list: Candidate HIK character names in preferred order.
        """
        character_name = str(character_name or "")
        namespace = TaskRetargetHumanIK.clean_namespace(namespace)
        candidates = []

        def add_candidate(candidate):
            """Adds a candidate when it is meaningful and unique.

            Args:
                candidate (str): Candidate name.
            """
            candidate = str(candidate or "")
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        if namespace:
            add_candidate(TaskRetargetHumanIK.get_namespaced_name(character_name, namespace))
        add_candidate(character_name)
        if ":" in character_name:
            add_candidate(character_name.rpartition(":")[-1])
        return candidates

    def import_file_with_namespace(self, file_path, namespace=None, load_relevant_plugins=True):
        """Imports a Maya file using an explicit namespace context.

        Args:
            file_path (str): File path to import.
            namespace (str, optional): Requested namespace.
            load_relevant_plugins (bool, optional): Whether relevant importer plugins should load.

        Returns:
            list: Imported node names returned by Maya.
        """
        namespace = self.clean_namespace(namespace)
        if not namespace:
            return batch_processor_maya.import_file(
                file_path=file_path,
                namespace=None,
                load_relevant_plugins=load_relevant_plugins,
            )
        cmds = batch_processor_maya.get_maya_cmds()
        if load_relevant_plugins:
            batch_processor_maya.load_relevant_file_plugin(file_path)
        imported_nodes = cmds.file(
            file_path,
            i=True,
            ignoreVersion=True,
            returnNewNodes=True,
            namespace=namespace,
            mergeNamespacesOnClash=False,
            importTimeRange="override",
        ) or []
        return self.force_imported_nodes_namespace(imported_nodes, namespace)

    def open_fbx_source_scene(self, file_path):
        """Opens an FBX source as the active scene using animation-aware FBX settings.

        Args:
            file_path (str): FBX file path.

        Returns:
            str: Opened file path.
        """
        return batch_processor_maya.open_fbx_scene(file_path, load_relevant_plugins=True)

    def import_fbx_source_animation(self, file_path, namespace=None):
        """Imports a FBX animation source using animation-aware FBX preferences.

        Args:
            file_path (str): FBX file path.
            namespace (str, optional): Requested source namespace.

        Returns:
            list: Imported node names returned by Maya.
        """
        import gt.utils.fbx as utils_fbx

        namespace = self.clean_namespace(namespace)
        batch_processor_maya.load_relevant_file_plugin(file_path)
        with utils_fbx.FbxImporter() as fbx_importer:
            fbx_importer.set_preferences_animation()
            imported_nodes = fbx_importer.import_file(path=file_path, namespace=namespace or None) or []
        if namespace:
            imported_nodes = self.force_imported_nodes_namespace(imported_nodes, namespace)
        return imported_nodes

    def force_imported_nodes_namespace(self, imported_nodes, namespace):
        """Forces imported nodes into the requested namespace.

        Args:
            imported_nodes (list): Imported node names.
            namespace (str): Namespace to apply.

        Returns:
            list: Renamed or resolved imported node names.
        """
        namespace = self.clean_namespace(namespace)
        if not namespace:
            return imported_nodes or []
        cmds = batch_processor_maya.get_maya_cmds()
        if not cmds.namespace(exists=namespace):
            cmds.namespace(add=namespace)
            cmds.namespace(set=":")
        renamed_nodes = []
        existing_nodes = []
        for node in imported_nodes or []:
            if not node or not cmds.objExists(node):
                continue
            existing = cmds.ls(node, long=True) or [node]
            existing_nodes.append(existing[0])
        existing_nodes = sorted(set(existing_nodes), key=lambda item: str(item).count("|"), reverse=True)
        for node in existing_nodes:
            if not cmds.objExists(node):
                continue
            short_name = str(node).split("|")[-1]
            short_namespace = short_name.rpartition(":")[0] if ":" in short_name else ""
            short_name_no_namespace = short_name.rpartition(":")[-1]
            if short_namespace == namespace:
                renamed_nodes.append(node)
                continue
            try:
                renamed_nodes.append(cmds.rename(node, "{0}:{1}".format(namespace, short_name_no_namespace)))
            except Exception:
                renamed_nodes.append(node)
        return renamed_nodes or list(imported_nodes or [])

    def apply_source_namespace_to_opened_scene(self, source_nodes):
        """Applies the requested source namespace to nodes from an opened source scene.

        Args:
            source_nodes (list): Source scene nodes collected after opening the file.

        Returns:
            list: Source nodes after namespace application.
        """
        requested_namespace = self.clean_namespace(self.settings.get("source_namespace") or "")
        if not requested_namespace:
            return source_nodes or []
        if self.namespace_contains_nodes(requested_namespace):
            return source_nodes or []
        namespaced_nodes = self.force_imported_nodes_namespace(source_nodes, requested_namespace)
        if not self.namespace_contains_nodes(requested_namespace):
            sys.stdout.write(
                "[WARNING] - (HumanIK) - Unable to apply source namespace '{0}' to opened source scene.\n".format(
                    requested_namespace
                )
            )
        return namespaced_nodes

    @staticmethod
    def get_source_scene_nodes():
        """Gets user DAG nodes from the currently opened source scene.

        Returns:
            list: Source scene nodes, excluding default Maya cameras.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        default_camera_nodes = {
            "persp",
            "top",
            "front",
            "side",
            "perspShape",
            "topShape",
            "frontShape",
            "sideShape",
        }
        source_nodes = []
        for node in cmds.ls(dag=True, long=True) or []:
            short_name = str(node).split("|")[-1].rpartition(":")[-1]
            if short_name in default_camera_nodes:
                continue
            source_nodes.append(node)
        source_nodes.extend(cmds.ls(type="HIKCharacterNode") or [])
        return sorted(set(source_nodes), key=lambda item: str(item).count("|"), reverse=True)

    @staticmethod
    def capture_playback_range():
        """Captures the current scene playback and animation range.

        Returns:
            dict: Playback range values.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        return {
            "min": cmds.playbackOptions(query=True, min=True),
            "max": cmds.playbackOptions(query=True, max=True),
            "ast": cmds.playbackOptions(query=True, ast=True),
            "aet": cmds.playbackOptions(query=True, aet=True),
        }

    @staticmethod
    def restore_playback_range(playback_range):
        """Restores a captured playback and animation range.

        Args:
            playback_range (dict): Playback range values from capture_playback_range.
        """
        if not playback_range:
            return
        cmds = batch_processor_maya.get_maya_cmds()
        cmds.playbackOptions(
            edit=True,
            min=playback_range.get("min"),
            max=playback_range.get("max"),
            ast=playback_range.get("ast"),
            aet=playback_range.get("aet"),
        )

    @staticmethod
    def round_playback_range_to_whole_frames():
        """Rounds the current playback range and current frame to whole frames.

        Returns:
            dict: Rounded playback range values.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        min_frame = round(cmds.playbackOptions(query=True, minTime=True))
        max_frame = round(cmds.playbackOptions(query=True, maxTime=True))
        animation_start = round(cmds.playbackOptions(query=True, animationStartTime=True))
        animation_end = round(cmds.playbackOptions(query=True, animationEndTime=True))
        current_frame = round(cmds.currentTime(query=True))
        cmds.playbackOptions(
            edit=True,
            minTime=min_frame,
            maxTime=max_frame,
            animationStartTime=animation_start,
            animationEndTime=animation_end,
        )
        cmds.currentTime(current_frame, edit=True)
        return {
            "min": min_frame,
            "max": max_frame,
            "ast": animation_start,
            "aet": animation_end,
        }

    def detect_runtime_namespace(self, imported_nodes, requested_namespace="", root_name=""):
        """Detects the namespace that actually contains imported nodes.

        Args:
            imported_nodes (list): Nodes returned by Maya import.
            requested_namespace (str, optional): Namespace requested by settings.
            root_name (str, optional): Important root node name to test.

        Returns:
            str: Effective namespace, or empty string when nodes are unnamespaced.
        """
        requested_namespace = self.clean_namespace(requested_namespace)
        if requested_namespace and self.namespace_contains_nodes(requested_namespace):
            return requested_namespace
        if requested_namespace and root_name:
            candidate = self.get_namespaced_name(root_name, requested_namespace)
            if self.object_exists(candidate):
                return requested_namespace
        for node in imported_nodes or []:
            short_name = str(node or "").split("|")[-1]
            if ":" in short_name:
                return short_name.rpartition(":")[0]
        return ""

    def get_runtime_source_namespace(self):
        """Gets the namespace that actually contains the source skeleton.

        Returns:
            str: Effective source namespace.
        """
        namespace = getattr(self, "_runtime_source_namespace", "")
        if namespace:
            return namespace
        return self.detect_runtime_namespace(
            imported_nodes=[],
            requested_namespace=self.settings.get("source_namespace") or "",
            root_name=self.settings.get("source_root") or "",
        )

    def get_runtime_target_namespace(self):
        """Gets the namespace that actually contains the target rig.

        Returns:
            str: Effective target namespace.
        """
        namespace = getattr(self, "_runtime_target_namespace", "")
        if namespace:
            return namespace
        return self.detect_runtime_namespace(
            imported_nodes=[],
            requested_namespace=self.settings.get("target_namespace") or "",
            root_name="",
        )

    def resolve_existing_node(self, name, namespace=""):
        """Resolves a node with namespace fallback.

        Args:
            name (str): Node name to resolve.
            namespace (str, optional): Preferred namespace.

        Returns:
            str: Existing node name when found, otherwise the best candidate.
        """
        name = str(name or "")
        namespace = self.clean_namespace(namespace)
        if not name:
            return ""
        if namespace:
            candidate = self.get_namespaced_name(name, namespace)
            if self.object_exists(candidate):
                return candidate
        if self.object_exists(name):
            return name
        if ":" in name:
            short_name = name.rpartition(":")[-1]
            if self.object_exists(short_name):
                return short_name
        return self.get_namespaced_name(name, namespace) if namespace else name

    def resolve_source_root_for_export(self):
        """Resolves the configured source root for a current-scene export.

        The configured namespace is preferred when that node exists. Scenes
        prepared without namespaces remain usable through the unnamespaced
        fallback in :meth:`resolve_existing_node`.

        Returns:
            str: Existing source root, or the preferred candidate when missing.
        """
        return self.resolve_existing_node(
            name=self.settings.get("source_root"),
            namespace=self.settings.get("source_namespace"),
        )

    @staticmethod
    def force_joint_evaluation(joints):
        """Forces Maya to evaluate the provided joints.

        Args:
            joints (list): Joint nodes.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        for joint in joints or []:
            if cmds.objExists(joint):
                try:
                    cmds.getAttr("{0}.worldMatrix[0]".format(joint))
                except Exception:
                    pass
        try:
            cmds.refresh(force=True)
        except Exception:
            pass

    @staticmethod
    def get_namespaced_name(name, namespace):
        """Applies a namespace to a node name if needed.

        Args:
            name (str): Node name.
            namespace (str): Namespace.

        Returns:
            str: Namespaced node name.
        """
        name = str(name or "")
        namespace = str(namespace or "").strip(":")
        if not name or not namespace or ":" in name:
            return name
        return "{0}:{1}".format(namespace, name)

    @staticmethod
    def object_exists(node):
        """Checks whether a Maya object exists.

        Args:
            node (str): Node name.

        Returns:
            bool: True if the object exists.
        """
        if not node:
            return False
        cmds = batch_processor_maya.get_maya_cmds()
        return bool(cmds.objExists(node))

    @staticmethod
    def is_hik_character(node):
        """Checks whether a node is an existing HIK character.

        Args:
            node (str): Node name.

        Returns:
            bool: True if the node is a HIKCharacterNode.
        """
        if not node:
            return False
        cmds = batch_processor_maya.get_maya_cmds()
        try:
            return bool(cmds.objExists(node) and cmds.nodeType(node) == "HIKCharacterNode")
        except Exception:
            return False

    @staticmethod
    def hik_name_matches(node, requested_name):
        """Checks whether a HIK node matches a requested base name.

        Args:
            node (str): Existing HIK node.
            requested_name (str): Requested name.

        Returns:
            bool: True when the node is an exact or Maya-uniquified match.
        """
        short_name = str(node or "").rpartition(":")[-1]
        requested_name = str(requested_name or "")
        if not short_name or not requested_name:
            return False
        if short_name == requested_name:
            return True
        suffix = short_name[len(requested_name):]
        return bool(short_name.startswith(requested_name) and suffix.isdigit())

    @staticmethod
    def clean_namespace(namespace):
        """Normalizes a namespace setting.

        Args:
            namespace (str): Namespace value.

        Returns:
            str: Namespace without leading or trailing colons.
        """
        return str(namespace or "").strip(":")

    @staticmethod
    def namespace_contains_nodes(namespace):
        """Checks whether a Maya namespace contains nodes.

        Args:
            namespace (str): Namespace to inspect.

        Returns:
            bool: True if the namespace exists and contains nodes.
        """
        namespace = TaskRetargetHumanIK.clean_namespace(namespace)
        if not namespace:
            return False
        cmds = batch_processor_maya.get_maya_cmds()
        try:
            if not cmds.namespace(exists=namespace):
                return False
            nodes = cmds.namespaceInfo(namespace, listOnlyDependencyNodes=True, recurse=True) or []
            return bool(nodes)
        except Exception:
            return False

    @staticmethod
    def delete_namespace(namespace):
        """Deletes a namespace when it exists.

        Args:
            namespace (str): Namespace to remove.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        namespace = str(namespace or "").strip(":")
        if not namespace or not cmds.namespace(exists=namespace):
            return
        child_namespaces = []
        try:
            child_namespaces = cmds.namespaceInfo(namespace, listOnlyNamespaces=True, recurse=True) or []
        except Exception:
            child_namespaces = []
        for child_namespace in sorted(child_namespaces, key=lambda item: str(item).count(":"), reverse=True):
            child_namespace = str(child_namespace or "").strip(":")
            if child_namespace and cmds.namespace(exists=child_namespace):
                try:
                    cmds.namespace(removeNamespace=child_namespace, mergeNamespaceWithRoot=True)
                except Exception:
                    pass
        try:
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
        except Exception:
            pass

    @staticmethod
    def get_hik_characters():
        """Gets available HumanIK character nodes.

        Returns:
            list: HIK character node names.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        return cmds.ls(type="HIKCharacterNode") or []

    @staticmethod
    def evaluate_hik_character(character_node):
        """Forces HumanIK to evaluate a character node and update internal lists.

        Args:
            character_node (str): HIK character node.
        """
        cmds = batch_processor_maya.get_maya_cmds()
        if not character_node or not cmds.objExists(character_node):
            return
        try:
            cmds.exactWorldBoundingBox(character_node)
        except Exception:
            pass
        try:
            import maya.mel as mel

            mel.eval("hikUpdateCharacterList();")
            mel.eval("hikUpdateSourceList();")
            mel.eval("hikUpdateContextualUI();")
            mel.eval("hikUpdateSkeletonUI();")
        except Exception:
            pass
        try:
            cmds.refresh(force=True)
        except Exception:
            pass

    @staticmethod
    def export_pose_from_current_scene(file_path, source_root):
        """Exports a pose from the current Maya scene.

        Args:
            file_path (str): Output pose path.
            source_root (str): Root joint or transform.

        Returns:
            str: Written file path.
        """
        import gt.core.io as core_io
        import gt.core.pose as core_pose

        cmds = batch_processor_maya.get_maya_cmds()
        if not source_root or not cmds.objExists(source_root):
            raise RuntimeError("Source root does not exist: {0}".format(source_root))
        current_selection = cmds.ls(selection=True) or []
        try:
            cmds.select(source_root, hierarchy=True)
            joints = cmds.ls(selection=True, type="joint") or []
            pose_data = core_pose.get_pose_as_dict(joints)
            core_io.write_json(path=file_path, data=pose_data)
            return file_path
        finally:
            if current_selection:
                cmds.select(current_selection)
            else:
                cmds.select(clear=True)

    @staticmethod
    def export_definition_from_current_scene(character_node, file_path, prefix=""):
        """Exports a HumanIK XML definition from the current Maya scene.

        Args:
            character_node (str): HIK character node.
            file_path (str): Output XML file.
            prefix (str, optional): Optional output prefix.

        Returns:
            bool: True if export succeeded.
        """
        import gt.utils.hik as utils_hik

        return utils_hik.export_definition_to_xml(character_node, file_path, prefix=prefix)

    @staticmethod
    def export_properties_from_current_scene(character_node, file_path):
        """Exports HumanIK properties from the current Maya scene.

        Args:
            character_node (str): HIK character node.
            file_path (str): Output JSON file.

        Returns:
            str: Written JSON file path.
        """
        import gt.core.io as core_io
        import gt.utils.hik as utils_hik

        properties = utils_hik.get_hik_properties(character_node)
        if not properties:
            raise RuntimeError("No HumanIK properties found for target: {0}".format(character_node))
        core_io.write_json(path=file_path, data=properties)
        return file_path

    def apply_source_tpose_in_scene(self, project):
        """Applies the configured source T-pose to the current scene for testing.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Joints affected by the applied pose.
        """
        import gt.core.io as core_io
        import gt.core.pose as core_pose

        tpose_path = self.get_resolved_path(project, "source_tpose_path")
        if not tpose_path:
            raise RuntimeError("No Source T-Pose path is configured.")
        if not os.path.isfile(tpose_path):
            raise RuntimeError("Source T-Pose file does not exist: {0}".format(tpose_path))
        tpose_dict = core_io.read_json_dict(tpose_path)
        if not tpose_dict:
            raise RuntimeError("Source T-Pose file is empty or invalid: {0}".format(tpose_path))
        source_namespace = self.get_runtime_source_namespace()
        applied_joints = core_pose.set_pose_from_dict(tpose_dict, namespace=source_namespace)
        if not applied_joints:
            raise RuntimeError(
                "Source T-Pose did not match any joints using namespace '{0}': {1}".format(
                    source_namespace or "<root>",
                    tpose_path,
                )
            )
        return applied_joints

    def import_source_definition_in_scene(self, project):
        """Imports the configured source HIK definition into the current scene for testing.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Source HIK character node the definition was imported onto.
        """
        import gt.utils.hik as utils_hik

        definition_path = self.get_resolved_path(project, "source_definition_path")
        if not definition_path:
            raise RuntimeError("No Source HIK XML path is configured.")
        if not os.path.isfile(definition_path):
            raise RuntimeError("Source HIK XML file does not exist: {0}".format(definition_path))
        source_namespace = self.get_runtime_source_namespace()
        requested_character = self.get_namespaced_name(
            self.settings.get("source_character_name") or "source",
            source_namespace,
        )
        source_character = self.get_or_create_hik_character(requested_character)
        if not source_character:
            raise RuntimeError("Unable to create or find a HumanIK source character for the definition import.")
        utils_hik.set_definition_lock(source_character, False)
        prefix = "{0}:".format(source_namespace.strip(":")) if source_namespace else ""
        utils_hik.import_definition_from_xml(source_character, definition_path, prefix=prefix)
        utils_hik.set_definition_lock(source_character, True)
        self.evaluate_hik_character(source_character)
        return source_character

    def import_target_rig_in_scene(self, project):
        """Imports the configured target rig into the current scene for testing.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Imported target nodes.
        """
        target_rig_path = self.get_resolved_path(project, "target_rig_path")
        if not target_rig_path:
            raise RuntimeError("No Target Rig path is configured.")
        if not os.path.isfile(target_rig_path):
            raise RuntimeError("Target Rig file does not exist: {0}".format(target_rig_path))
        return self.import_target_rig(project)

    def import_target_properties_in_scene(self, project):
        """Applies the configured target HIK properties in the current scene for testing.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Properties applied to the target character.
        """
        import gt.core.io as core_io
        import gt.utils.hik as utils_hik

        properties_path = self.get_resolved_path(project, "target_properties_path")
        if not properties_path:
            raise RuntimeError("No Target Properties path is configured.")
        if not os.path.isfile(properties_path):
            raise RuntimeError("Target Properties file does not exist: {0}".format(properties_path))
        target_character = self.get_target_character()
        if not target_character:
            raise RuntimeError("Unable to resolve a HumanIK target character in the current scene.")
        properties = core_io.read_json_dict(properties_path)
        if not isinstance(properties, dict) or not properties:
            raise RuntimeError("Target HumanIK properties file is empty or invalid: {0}".format(properties_path))
        applied_properties = utils_hik.set_hik_properties(target_character, properties)
        if not applied_properties:
            raise RuntimeError(
                "No HumanIK properties could be applied to target character '{0}' from: {1}".format(
                    target_character,
                    properties_path,
                )
            )
        self.evaluate_hik_character(target_character)
        return applied_properties


def run_inline_python_script(script_text, context, script_name="<humanik_post_script>"):
    """Runs inline Python post-retarget code.

    Args:
        script_text (str): Python script text.
        context (dict): Runtime context.
        script_name (str, optional): Name reported for compiled script errors.
    """
    task_utils.run_inline_python_script(
        script_text=script_text,
        context=context,
        script_name=script_name,
    )


HumanIKRetargetTask = TaskRetargetHumanIK
HikRetargetTask = TaskRetargetHumanIK
RetargetHumanIKTask = TaskRetargetHumanIK
