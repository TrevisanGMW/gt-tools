"""
Batch Processor HumanIK Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.tasks import task_hik_retarget
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import sys


class AttrWidgetRetargetHumanIK(AttrWidgetTask):
    """Attribute widget for the HumanIK retarget task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the HumanIK retarget widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskRetargetHumanIK, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.pre_bake_script_section = None
        self.pre_bake_warning_label = None
        self.bake_checkbox = None
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings(
            scene_io_settings={
                "load_mode_key": "source_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_values": [".ma", ".mb", ".fbx"],
                "include_load_plugins": True,
            }
        )
        self.add_widget_separator_line(label_text="HumanIK Source")
        self.add_text_field(
            "Source Root",
            self.task.settings.get("source_root"),
            partial(self.set_task_setting, key="source_root"),
            placeholder="Optional source root joint, e.g. Reference",
            tooltip="Optional root joint or transform used to capture and restore the source pose.",
        )
        self.add_source_character_controls()
        self.add_text_field(
            "Source Namespace",
            self.task.settings.get("source_namespace"),
            partial(self.set_task_setting, key="source_namespace"),
            placeholder="Optional namespace for imported source animation.",
            tooltip="Namespace used when importing or resolving the source animation skeleton.",
        )
        self.source_definition_widgets = self.add_path_template_field(
            "Source HIK XML",
            self.task.settings.get("source_definition_path"),
            partial(self.set_task_setting, key="source_definition_path"),
            placeholder="{project-dir}/data/source_hik.xml",
            tooltip="HumanIK XML definition used to map the source animation skeleton before retargeting.",
            file_filter="HumanIK XML (*.xml);;All Files (*);;",
            return_widgets=True,
        )
        self.source_tpose_widgets = self.add_path_template_field(
            "Source T-Pose",
            self.task.settings.get("source_tpose_path"),
            partial(self.set_task_setting, key="source_tpose_path"),
            placeholder="{project-dir}/data/source_tpose.pose",
            tooltip="Optional source pose applied before characterization, then the original animation pose is restored.",
            file_filter="Pose Files (*.pose *.json);;JSON Files (*.json);;All Files (*);;",
            return_widgets=True,
        )
        self.refresh_source_character_mode_controls()

        self.add_widget_separator_line(label_text="HumanIK Target")
        self.add_path_template_field(
            "Target Rig",
            self.task.settings.get("target_rig_path"),
            partial(self.set_task_setting, key="target_rig_path"),
            placeholder="Optional target rig file.",
            tooltip=(
                "Optional target rig file imported before retargeting. The target rig is expected to already contain "
                "a valid HumanIK character definition and setup. Leave empty when the target already exists in the scene."
            ),
            file_filter="Maya/FBX Files (*.ma *.mb *.fbx);;All Files (*);;",
        )
        self.add_text_field(
            "Target Character",
            self.task.settings.get("target_character_name"),
            partial(self.set_task_setting, key="target_character_name"),
            placeholder="Leave empty to auto-detect the target HIK character.",
            tooltip=(
                "HumanIK target character expected in the target rig. The target rig should already have this "
                "HumanIK character configured. When empty, the first target namespace HIK character is used."
            ),
        )
        self.add_text_field(
            "Target Namespace",
            self.task.settings.get("target_namespace"),
            partial(self.set_task_setting, key="target_namespace"),
            placeholder="target",
            tooltip="Namespace used when importing or resolving the target rig.",
        )
        self.add_target_properties_controls()
        self.add_combo_box(
            "Bake Target",
            self.task.settings.get("bake_target"),
            task_hik_retarget.HIK_BAKE_TARGETS,
            partial(self.set_task_setting, key="bake_target"),
            tooltip='Bake destination after assigning the HumanIK source. Choose "None" to connect the source without baking.',
        )

        self.add_widget_separator_line(label_text="Bake Preferences")
        self.add_scene_and_bake_options()
        self.add_cleanup_options()
        self.add_action_buttons()
        self.add_pre_bake_script_section()
        self.add_post_script_section()
        self.content_layout.addStretch()

    def add_target_properties_controls(self):
        """Adds the optional target HumanIK properties file controls."""
        tooltip = (
            "Load HumanIK retarget properties onto the target character before assigning the source and baking. "
            "The JSON file can be created with Export Target Properties below."
        )
        self.target_properties_widgets = self.add_path_template_field(
            "Target Properties",
            self.task.settings.get("target_properties_path"),
            partial(self.set_task_setting, key="target_properties_path"),
            placeholder="Optional target HumanIK properties JSON.",
            tooltip=tooltip,
            file_filter="JSON Files (*.json);;All Files (*);;",
            return_widgets=True,
        )
        self.target_properties_checkbox = ui_qt.QtWidgets.QCheckBox("Load")
        self.target_properties_checkbox.setChecked(bool(self.task.settings.get("load_target_properties", False)))
        self.target_properties_checkbox.setToolTip(tooltip)
        self.target_properties_checkbox.stateChanged.connect(
            lambda *args: self.set_load_target_properties(self.target_properties_checkbox.isChecked())
        )
        self.target_properties_widgets.get("layout").insertWidget(1, self.target_properties_checkbox)
        self.refresh_target_properties_controls()

    def set_load_target_properties(self, value):
        """Sets whether target HumanIK properties are loaded.

        Args:
            value (bool): Whether to load the configured properties file.
        """
        self.set_task_setting(bool(value), key="load_target_properties")
        self.refresh_target_properties_controls()

    def refresh_target_properties_controls(self):
        """Refreshes controls governed by the target-properties checkbox."""
        is_enabled = bool(self.task.settings.get("load_target_properties", False))
        for key in ["field", "info_button", "open_button", "browse_button"]:
            widget = self.target_properties_widgets.get(key)
            if widget:
                widget.setEnabled(is_enabled)

    def add_source_character_controls(self):
        """Adds source character name and pre-existing HIK controls."""
        tooltip = (
            "HumanIK source character name. It is created when Pre-existing HIK is off, "
            "or resolved from the source scene when Pre-existing HIK is on."
        )
        layout = self.add_labeled_layout("Source Character", tooltip=tooltip)
        source_character_field = self.create_text_field(
            text=self.task.settings.get("source_character_name"),
            placeholder="source",
            tooltip=tooltip,
        )
        source_character_field.textChanged.connect(partial(self.set_task_setting, key="source_character_name"))
        layout.addWidget(source_character_field)
        layout.setStretchFactor(source_character_field, 1)
        self.source_character_pre_existing_checkbox = ui_qt.QtWidgets.QCheckBox("Pre-existing HIK")
        self.source_character_pre_existing_checkbox.setMinimumHeight(
            self.source_character_pre_existing_checkbox.sizeHint().height() + 2
        )
        self.source_character_pre_existing_checkbox.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Fixed,
            ui_qt.QtLib.SizePolicy.Fixed,
        )
        self.source_character_pre_existing_checkbox.setChecked(
            bool(self.task.settings.get("source_character_pre_existing", False))
        )
        self.source_character_pre_existing_checkbox.setToolTip(
            (
                "Use an existing source HumanIK character from the source scene. "
                "Source HIK XML and Source T-Pose are ignored when enabled."
            )
        )
        self.source_character_pre_existing_checkbox.stateChanged.connect(
            lambda *args: self.set_source_character_pre_existing(
                self.source_character_pre_existing_checkbox.isChecked()
            )
        )
        layout.addWidget(self.source_character_pre_existing_checkbox)

    def set_source_character_pre_existing(self, value):
        """Sets whether the source character already exists in the source scene.

        Args:
            value (bool): Whether to use a pre-existing source HIK character.
        """
        self.set_task_setting(bool(value), key="source_character_pre_existing")
        self.refresh_source_character_mode_controls()

    def refresh_source_character_mode_controls(self):
        """Refreshes controls disabled by pre-existing source HIK mode."""
        is_pre_existing = bool(self.task.settings.get("source_character_pre_existing", False))
        for widget_group in [
            getattr(self, "source_definition_widgets", None),
            getattr(self, "source_tpose_widgets", None),
        ]:
            if not widget_group:
                continue
            for key in ["field", "info_button", "open_button", "browse_button"]:
                widget = widget_group.get(key)
                if widget:
                    widget.setEnabled(not is_pre_existing)

    def add_scene_and_bake_options(self):
        """Adds scene and bake controls."""
        fps_layout = self.add_labeled_layout("Scene FPS", tooltip="Optionally set the Maya scene FPS before retargeting.")
        self.add_checkbox(
            "Set",
            self.task.settings.get("set_framerate"),
            partial(self.set_task_setting, key="set_framerate"),
            layout=fps_layout,
            tooltip="Set Maya FPS before HumanIK retargeting.",
        )
        fps_field = self.create_text_field(
            text=self.task.settings.get("framerate"),
            placeholder="30",
            tooltip="Frames per second used when Set is active.",
        )
        fps_field.setMaximumWidth(80)
        fps_field.textChanged.connect(partial(self.set_task_setting, key="framerate"))
        fps_layout.addWidget(fps_field)
        fps_layout.addStretch()

        bake_layout = ui_qt.QtWidgets.QHBoxLayout()
        bake_layout.setContentsMargins(0, 0, 0, 5)
        self.bake_checkbox = self.add_checkbox(
            "Bake",
            self.task.settings.get("bake_animation"),
            self.set_bake_animation,
            layout=bake_layout,
            tooltip='Bake retargeted animation unless Bake Target is "None".',
        )
        self.add_checkbox(
            "Proxy Bake",
            self.task.settings.get("force_proxy_bake"),
            partial(self.set_task_setting, key="force_proxy_bake"),
            layout=bake_layout,
            tooltip="Force the Python proxy skeleton bake fallback.",
        )
        bake_layout.addStretch()
        self.content_layout.addLayout(bake_layout)

    def set_bake_animation(self, value):
        """Sets the bake state and refreshes bake-dependent controls.

        Args:
            value (bool): Whether HumanIK animation should be baked.
        """
        self.set_task_setting(bool(value), key="bake_animation")
        self.refresh_pre_bake_script_warning()

    def add_cleanup_options(self):
        """Adds source cleanup options."""
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Delete Source", "delete_source_elements", "Delete source animation elements after baking."),
            (
                "Delete Namespace",
                "delete_source_namespace",
                "Merge source and target namespaces back to root before writing output.",
            ),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=layout,
                tooltip=tooltip,
            )
        layout.addStretch()
        self.content_layout.addLayout(layout)

    def add_action_buttons(self):
        """Adds current-scene helper action buttons."""
        tooltip = "Export helper data from the current Maya scene into files used by this HumanIK task."
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        export_pose_button = ui_qt.QtWidgets.QPushButton("Export Pose")
        export_pose_button.setMinimumHeight(35)
        export_pose_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        export_pose_button.setToolTip(
            "Writes a pose file from the configured Source Root. Use it as Source T-Pose for characterization."
        )
        export_pose_button.clicked.connect(self.export_pose_from_current_scene)
        layout.addWidget(export_pose_button)
        export_source_button = ui_qt.QtWidgets.QPushButton("Export Source HIK")
        export_source_button.setMinimumHeight(35)
        export_source_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        export_source_button.setToolTip(
            "Writes the configured Source Character HIK mapping to XML and stores it as Source HIK XML."
        )
        export_source_button.clicked.connect(
            partial(self.export_definition_from_current_scene, character_key="source_character_name")
        )
        layout.addWidget(export_source_button)
        export_target_button = ui_qt.QtWidgets.QPushButton("Export Target HIK")
        export_target_button.setMinimumHeight(35)
        export_target_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        export_target_button.setToolTip(
            "Writes the configured Target Character HIK mapping to XML for reuse or inspection."
        )
        export_target_button.clicked.connect(
            partial(self.export_definition_from_current_scene, character_key="target_character_name")
        )
        layout.addWidget(export_target_button)
        export_properties_button = ui_qt.QtWidgets.QPushButton("Export Target Properties")
        export_properties_button.setMinimumHeight(35)
        export_properties_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        export_properties_button.setToolTip(
            "Writes the configured target character's HumanIK retarget properties to JSON."
        )
        export_properties_button.clicked.connect(self.export_target_properties_from_current_scene)
        layout.addWidget(export_properties_button)
        layout.addStretch()

    def export_target_properties_from_current_scene(self):
        """Exports target HumanIK properties from the current Maya scene."""
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=True,
            caption="Export Target HumanIK Properties",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        character_node = self.task.resolve_hik_character_for_namespace(
            self.task.settings.get("target_character_name"),
            self.task.settings.get("target_namespace"),
        )
        try:
            self.task.export_properties_from_current_scene(character_node=character_node, file_path=file_path)
            message = "Exported HumanIK target properties for '{0}' to: {1}".format(character_node, file_path)
            sys.stdout.write(message + "\n")
            self.emit_status_message(message)
        except Exception as exception:
            message = "Unable to export HumanIK target properties for '{0}'. Issue: {1}".format(
                character_node,
                exception,
            )
            sys.stdout.write(message + "\n")
            self.emit_status_message(message, status="warning")

    def add_post_script_section(self):
        """Adds the collapsed optional post-script section."""
        collapsed = bool(self.task.settings.get("post_script_collapsed", True))
        section = self.add_collapsible_section(
            label_text="Post Script",
            collapsed=collapsed,
            state_setter=partial(self.set_task_setting, key="post_script_collapsed"),
            tooltip="Optional Python cleanup script that runs after retargeting and before writing output.",
        )
        layout = section.get("content_layout")
        post_layout = ui_qt.QtWidgets.QHBoxLayout()
        post_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Run",
            self.task.settings.get("run_post_script"),
            partial(self.set_task_setting, key="run_post_script"),
            layout=post_layout,
            tooltip="Run the configured post-retarget Python script.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("post_script_pass_standard_arguments", True),
            partial(self.set_task_setting, key="post_script_pass_standard_arguments"),
            layout=post_layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("post_script_pass_environment_arguments", True),
            partial(self.set_task_setting, key="post_script_pass_environment_arguments"),
            layout=post_layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        post_layout.addStretch()
        layout.addLayout(post_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get("post_script_text") or task_hik_retarget.DEFAULT_POST_SCRIPT_TEXT,
            placeholder=task_hik_retarget.DEFAULT_POST_SCRIPT_TEXT,
            tooltip=(
                "Inline Python cleanup pass executed after HumanIK retargeting and before output is written. "
                "Use context, arguments/args, environment_variables/env, project, task, work_item, output_path, "
                "source_character, and target_character."
            ),
            text_changed_callback=partial(self.set_task_setting, key="post_script_text"),
            font_size=self.task.settings.get("post_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="post_script_font_size"),
        )
        layout.addWidget(editor)

    def add_pre_bake_script_section(self):
        """Adds the collapsed optional pre-bake script section."""
        collapsed = bool(self.task.settings.get("pre_bake_script_collapsed", True))
        section = self.add_collapsible_section(
            label_text="Pre-Bake Script",
            collapsed=collapsed,
            state_setter=partial(self.set_task_setting, key="pre_bake_script_collapsed"),
            tooltip="Optional Python script that runs immediately before the HumanIK bake operation.",
        )
        self.pre_bake_script_section = section
        layout = section.get("content_layout")
        options_layout = ui_qt.QtWidgets.QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Run",
            self.task.settings.get("run_pre_bake_script"),
            partial(self.set_task_setting, key="run_pre_bake_script"),
            layout=options_layout,
            tooltip="Run the configured script immediately before baking retargeted animation.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pre_bake_script_pass_standard_arguments", True),
            partial(self.set_task_setting, key="pre_bake_script_pass_standard_arguments"),
            layout=options_layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pre_bake_script_pass_environment_arguments", True),
            partial(self.set_task_setting, key="pre_bake_script_pass_environment_arguments"),
            layout=options_layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        self.pre_bake_warning_label = ui_qt.QtWidgets.QLabel("Bake Off: Runs Like Post")
        self.pre_bake_warning_label.setStyleSheet("color: #d6b656;")
        self.pre_bake_warning_label.setToolTip(
            "Bake is disabled, so this script runs after HumanIK source assignment without a following bake."
        )
        options_layout.addStretch()
        options_layout.addWidget(self.pre_bake_warning_label)
        layout.addLayout(options_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=(
                self.task.settings.get("pre_bake_script_text")
                or task_hik_retarget.DEFAULT_PRE_BAKE_SCRIPT_TEXT
            ),
            placeholder=task_hik_retarget.DEFAULT_PRE_BAKE_SCRIPT_TEXT,
            tooltip=(
                "Inline Python pass executed after HumanIK source assignment and immediately before baking. "
                "Use context, arguments/args, environment_variables/env, project, task, work_item, output_path, "
                "source_character, and target_character."
            ),
            text_changed_callback=partial(self.set_task_setting, key="pre_bake_script_text"),
            font_size=self.task.settings.get("pre_bake_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="pre_bake_script_font_size"),
        )
        layout.addWidget(editor)
        self.refresh_pre_bake_script_warning()

    def refresh_pre_bake_script_warning(self):
        """Shows the alternate pre-bake behavior warning while baking is inactive."""
        if not self.pre_bake_warning_label:
            return
        is_bake_enabled = bool(self.task.settings.get("bake_animation", True))
        self.pre_bake_warning_label.setVisible(not is_bake_enabled)

    def export_pose_from_current_scene(self):
        """Exports the configured source root pose from the current Maya scene."""
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=True,
            caption="Export HumanIK Source Pose",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="Pose Files (*.pose);;JSON Files (*.json);;All Files (*);;",
        )
        if not file_path:
            return
        try:
            source_root = self.task.resolve_source_root_for_export()
            self.task.export_pose_from_current_scene(file_path=file_path, source_root=source_root)
            message = "Exported HumanIK source pose from '{0}' to: {1}".format(source_root, file_path)
            sys.stdout.write(message + "\n")
            self.emit_status_message(message)
        except Exception as exception:
            message = "Unable to export HumanIK pose. Check Source Root and current scene. Issue: {0}".format(exception)
            sys.stdout.write(message + "\n")
            self.emit_status_message(message, status="warning")

    def export_definition_from_current_scene(self, character_key):
        """Exports a configured HumanIK definition from the current Maya scene.

        Args:
            character_key (str): Settings key containing the character name.
        """
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=True,
            caption="Export HumanIK Definition",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="HumanIK XML (*.xml);;All Files (*);;",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xml"):
            file_path += ".xml"
        namespace_key = "source_namespace" if character_key == "source_character_name" else "target_namespace"
        character_node = self.task.resolve_hik_character_for_namespace(
            self.task.settings.get(character_key),
            self.task.settings.get(namespace_key),
        )
        try:
            success = self.task.export_definition_from_current_scene(character_node=character_node, file_path=file_path)
            if not success:
                raise RuntimeError("HumanIK definition export failed.")
            message = "Exported HumanIK definition for '{0}' to: {1}".format(character_node, file_path)
            sys.stdout.write(message + "\n")
            self.emit_status_message(message)
        except Exception as exception:
            message = "Unable to export HumanIK definition for '{0}'. Issue: {1}".format(character_node, exception)
            sys.stdout.write(message + "\n")
            self.emit_status_message(message, status="warning")
