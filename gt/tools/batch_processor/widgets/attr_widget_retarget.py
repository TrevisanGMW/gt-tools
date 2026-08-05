"""
Batch Processor Retarget Task Attribute Widget
"""

from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import os


class AttrWidgetRetargetTask(AttrWidgetTask):
    """Attribute widget for the retarget task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the retarget task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (RetargetTask, optional): Retarget task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Retarget Preferences")
        self.add_retarget_definition_field()
        self.add_path_template_field(
            "Target Rig",
            self.task.settings.get("target_rig_path"),
            partial(self.set_task_setting, key="target_rig_path"),
            placeholder="Optional rig file override.",
            tooltip="Optional target rig file used to override the rig path stored in the retarget definition.",
            file_filter="Maya/FBX Files (*.ma *.mb *.fbx);;All Files (*);;",
        )
        self.add_text_field(
            "Source Namespace",
            self.task.settings.get("source_namespace"),
            partial(self.set_task_setting, key="source_namespace"),
            placeholder="Leave empty when the source has no namespace.",
            tooltip="Namespace used by the source animation hierarchy.",
        )
        self.add_text_field(
            "Target Namespace",
            self.task.settings.get("target_namespace"),
            partial(self.set_task_setting, key="target_namespace"),
            placeholder="Leave empty when the target has no namespace.",
            tooltip="Namespace used by the target rig hierarchy.",
        )
        self.add_combo_box(
            "Output Extension",
            self.task.settings.get("output_extension"),
            [".ma", ".mb", ".fbx"],
            partial(self.set_task_setting, key="output_extension"),
            tooltip="File extension to use when this task writes cooked retarget output.",
        )
        toggle_layout = ui_qt.QtWidgets.QHBoxLayout()
        toggle_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Reference Rig", "reference_rig", "Reference the target rig instead of importing it when supported."),
            ("Delete Source", "delete_source", "Delete source hierarchy after retargeting."),
            ("Delete Static", "delete_static_channels", "Delete static animation channels after baking."),
            ("Shortname Fallback", "shortname_fallback", "Allow source and target matching by short names."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=toggle_layout,
                tooltip=tooltip,
            )
        self.content_layout.addLayout(toggle_layout)

        output_layout = ui_qt.QtWidgets.QHBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Bake Animation", "bake_animation", "Bake the retargeted animation."),
            ("Export Result", "export_result", "Write the retargeted result to this task output folder."),
            ("FBX Key Reducer", "fbx_key_reducer", "Use FBX key reducer when exporting FBX output."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=output_layout,
                tooltip=tooltip,
            )
        output_layout.addStretch()
        self.content_layout.addLayout(output_layout)
        self.content_layout.addStretch()

    def add_retarget_definition_field(self):
        """Adds the retarget definition chooser row."""
        tooltip = "Retargeter definition used by this task."
        layout = self.add_labeled_layout("Definition", tooltip=tooltip)
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setEditable(True)
        combo_box.setMinimumHeight(35)
        combo_box.setMinimumWidth(1)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        combo_box.setToolTip(tooltip)
        available_definitions = self.get_available_retarget_definitions()
        current_definition = self.task.settings.get("definition_path") or ""
        if current_definition:
            combo_box.addItem(current_definition)
        for definition_path in available_definitions:
            if combo_box.findText(definition_path) == -1:
                combo_box.addItem(definition_path)
        combo_box.setCurrentText(current_definition)
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a retarget definition file.")
        layout.addWidget(combo_box)
        layout.addWidget(info_button)
        layout.addWidget(browse_button)
        combo_box.currentTextChanged.connect(partial(self.set_task_setting, key="definition_path"))
        info_button.clicked.connect(partial(self.open_retarget_definition_info_dialog, combo_box=combo_box))
        browse_button.clicked.connect(partial(self.open_retarget_definition_dialog, combo_box=combo_box))

    def open_retarget_definition_info_dialog(self, combo_box):
        """Opens path information for the current retarget definition.

        Args:
            combo_box (QComboBox): Combo box containing the path.
        """
        field = self.create_text_field(text=combo_box.currentText())
        self.open_env_var_feedback_dialog(field=field)

    def open_retarget_definition_dialog(self, combo_box):
        """Opens a file dialog for choosing a retarget definition.

        Args:
            combo_box (QComboBox): Combo box to update.
        """
        field = self.create_text_field(text=combo_box.currentText())
        self.open_path_dialog(
            field=field,
            dir_only=False,
            file_filter="Retarget Definitions (*.rtg *.json);;JSON Files (*.json);;All Files (*);;",
        )
        if field.text():
            combo_box.setCurrentText(field.text())

    @staticmethod
    def get_available_retarget_definitions():
        """Gets available retarget definitions from the retargeter preferences directory.

        Returns:
            list: Sorted definition paths.
        """
        try:
            from gt.tools.retargeter import retargeter_constants

            definition_dir = retargeter_constants.RetargeterConstants.DEFAULT_DEFINITION_FOLDER
        except Exception:
            definition_dir = ""
        if not definition_dir or not os.path.isdir(definition_dir):
            return []
        definition_paths = []
        for file_name in os.listdir(definition_dir):
            if file_name.lower().endswith((".rtg", ".json")):
                definition_paths.append(os.path.join(definition_dir, file_name))
        return sorted(definition_paths)


get_icon_path = attr_widget_base.get_icon_path
