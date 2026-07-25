"""
Batch Processor Auto Rig Build Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetAutoRigBuildTask(AttrWidgetTask):
    """Attribute widget for the Auto Rig build task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Auto Rig build widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskAutoRigBuild, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
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
        self.add_widget_separator_line(label_text="Auto Rig Build Preferences")
        self.add_combo_box(
            "Output Extension",
            self.task.settings.get("output_extension"),
            [".ma", ".mb"],
            partial(self.set_task_setting, key="output_extension"),
            tooltip="Maya scene extension used for the built rig.",
        )
        self.add_checkbox(
            "Optimized Proxy",
            self.task.settings.get("optimized_proxy"),
            partial(self.set_task_setting, key="optimized_proxy"),
            tooltip="Build the proxy in optimized mode before building the final rig.",
        )
        self.add_force_disable_controls()
        self.content_layout.addStretch()

    def add_force_disable_controls(self):
        """Adds controls used to force-disable Auto Rigger module classes."""
        layout = self.add_labeled_layout("Disable Module", tooltip="Add a module class to force-disable before build.")
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setEditable(True)
        combo_box.setMinimumHeight(35)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        for module_name in get_auto_rigger_module_names():
            combo_box.addItem(module_name)
        layout.addWidget(combo_box)
        add_button = ui_qt.QtWidgets.QPushButton("Add")
        add_button.setMinimumHeight(35)
        add_button.clicked.connect(partial(self.add_force_disabled_module, combo_box=combo_box))
        layout.addWidget(add_button)
        self.force_disable_text_area = self.add_text_area(
            "Force Disabled Modules",
            "\n".join(self.task.settings.get("force_disable_modules") or []),
            partial(self.set_task_setting_list_from_text, key="force_disable_modules"),
            placeholder="One Auto Rigger module class per line.",
            tooltip="Modules listed here are disabled before the rig project builds.",
        )

    def add_force_disabled_module(self, combo_box):
        """Adds a selected module name to the force-disabled list.

        Args:
            combo_box (QComboBox): Module selector.
        """
        module_name = combo_box.currentText().strip()
        current_values = self.task.settings.get("force_disable_modules") or []
        if module_name and module_name not in current_values:
            current_values.append(module_name)
            self.task.settings["force_disable_modules"] = current_values
            self.force_disable_text_area.setPlainText("\n".join(current_values))




def get_auto_rigger_module_names():
    """Gets Auto Rigger module names.

    Returns:
        list: Sorted module names.
    """
    try:
        from gt.tools.auto_rigger.rig_modules import RigModules

        return sorted(RigModules.get_module_names())
    except Exception:
        return ["ModuleSaveScene", "ModuleExportSkeletalMesh"]


