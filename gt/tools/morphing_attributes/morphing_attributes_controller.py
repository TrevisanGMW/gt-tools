"""
Morphing Attributes Controller

Connects the Morphing Attributes view and model, handles user actions, syncs
settings, and drives the Maya scene operation.
"""

from gt.tools.morphing_attributes import morphing_attributes_model as model
import gt.ui.qt_import as ui_qt
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HELP_TEXT = (
    "Add Morphing Attributes creates driver attributes on a control object so blend "
    "shape (morphing) targets can be animated without selecting the deformed mesh.\n\n"
    "How to use:\n"
    "1. Select the deformed mesh and click 'Load Morphing Object', then pick a blend "
    "shape node from the list.\n"
    "2. Select the control that should receive the attributes and click "
    "'Load Attribute Holder'.\n"
    "3. Optionally use the desired/undesired filters to include or exclude targets by name.\n"
    "4. Adjust the options and value range, then click 'Create Morphing Attributes'.\n\n"
    "Options:\n"
    "- Ignore Uppercase: Ignore letter casing while filtering.\n"
    "- Add Separator: Add a locked attribute used as a visual divider.\n"
    "- Ignore Connected: Skip targets that already have an incoming connection.\n"
    "- Sort Attributes: Create the attributes in alphabetical order.\n"
    "- Modify Range: Remap the attribute range (e.g. 0-10) to the blend range (e.g. 0-1).\n"
    "- Delete Instead: Remove matching attributes instead of creating them."
)


class MorphingAttributesController:
    """Connects the Morphing Attributes model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (MorphingAttributesModel): Tool model.
            view (MorphingAttributesView): Tool view.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.sync_view_from_model()
        self.connect_view()
        self.update_range_enabled()
        self.view.show()

    def connect_view(self):
        """Connects view signals to controller handlers."""
        self.view.help_btn.clicked.connect(lambda *args: self.show_help())
        self.view.load_morphing_btn.clicked.connect(lambda *args: self.load_morphing_object())
        self.view.load_holder_btn.clicked.connect(lambda *args: self.load_attribute_holder())
        self.view.source_status_btn.clicked.connect(lambda *args: self.model.select_object(self.model.morphing_obj))
        self.view.holder_status_btn.clicked.connect(lambda *args: self.model.select_object(self.model.attr_holder))
        self.view.blend_nodes_list.itemSelectionChanged.connect(self.on_blend_node_selected)
        self.view.create_btn.clicked.connect(lambda *args: self.run())

        self.view.desired_filter_field.textChanged.connect(
            lambda text: self.model.set_setting("desired_filter_string", text)
        )
        self.view.undesired_filter_field.textChanged.connect(
            lambda text: self.model.set_setting("undesired_filter_string", text)
        )
        self.view.desired_filter_combo.currentTextChanged.connect(
            lambda text: self.model.set_setting("desired_filter_type", model.method_from_label(text))
        )
        self.view.undesired_filter_combo.currentTextChanged.connect(
            lambda text: self.model.set_setting("undesired_filter_type", model.method_from_label(text))
        )

        self.view.ignore_case_chk.toggled.connect(lambda checked: self.model.set_setting("ignore_case", checked))
        self.view.add_separator_chk.toggled.connect(lambda checked: self.model.set_setting("add_separator", checked))
        self.view.ignore_connected_chk.toggled.connect(
            lambda checked: self.model.set_setting("ignore_connected", checked)
        )
        self.view.sort_chk.toggled.connect(lambda checked: self.model.set_setting("sort_attr", checked))
        self.view.delete_instead_chk.toggled.connect(
            lambda checked: self.model.set_setting("delete_instead", checked)
        )
        self.view.modify_range_chk.toggled.connect(self.on_modify_range_toggled)

        self.view.old_min_spin.valueChanged.connect(lambda value: self.model.set_setting("old_range_min", value))
        self.view.old_max_spin.valueChanged.connect(lambda value: self.model.set_setting("old_range_max", value))
        self.view.new_min_spin.valueChanged.connect(lambda value: self.model.set_setting("new_range_min", value))
        self.view.new_max_spin.valueChanged.connect(lambda value: self.model.set_setting("new_range_max", value))

    def sync_view_from_model(self):
        """Writes the current model settings into the view widgets."""
        settings = self.model.settings
        self.view.desired_filter_field.setText(settings.get("desired_filter_string"))
        self.view.undesired_filter_field.setText(settings.get("undesired_filter_string"))
        self.view.desired_filter_combo.setCurrentText(self._label_from_method(settings.get("desired_filter_type")))
        self.view.undesired_filter_combo.setCurrentText(self._label_from_method(settings.get("undesired_filter_type")))
        self.view.ignore_case_chk.setChecked(bool(settings.get("ignore_case")))
        self.view.add_separator_chk.setChecked(bool(settings.get("add_separator")))
        self.view.ignore_connected_chk.setChecked(bool(settings.get("ignore_connected")))
        self.view.sort_chk.setChecked(bool(settings.get("sort_attr")))
        self.view.modify_range_chk.setChecked(bool(settings.get("modify_range")))
        self.view.delete_instead_chk.setChecked(bool(settings.get("delete_instead")))
        self.view.old_min_spin.setValue(int(settings.get("old_range_min")))
        self.view.old_max_spin.setValue(int(settings.get("old_range_max")))
        self.view.new_min_spin.setValue(int(settings.get("new_range_min")))
        self.view.new_max_spin.setValue(int(settings.get("new_range_max")))

    @staticmethod
    def _label_from_method(method):
        """Gets the user-facing label matching a filter method string.

        Args:
            method (str): Internal method string (e.g. "startswith").

        Returns:
            str: Matching label (e.g. "Starts With"). Defaults to "Includes".
        """
        for label in model.FILTER_METHOD_LABELS:
            if model.method_from_label(label) == method:
                return label
        return model.FILTER_METHOD_LABELS[0]

    def on_modify_range_toggled(self, checked):
        """Handles the Modify Range checkbox toggle.

        Args:
            checked (bool): Whether Modify Range is enabled.
        """
        self.model.set_setting("modify_range", checked)
        self.update_range_enabled()

    def update_range_enabled(self):
        """Enables or disables the range controls based on Modify Range."""
        self.view.range_widget.setEnabled(bool(self.model.settings.get("modify_range")))

    def on_blend_node_selected(self):
        """Stores the selected blend shape node on the model."""
        blend_node = self.view.get_selected_blend_node()
        if blend_node and self.model.object_exists(blend_node):
            self.model.blend_node = blend_node
            sys.stdout.write('"{0}" will be used when creating attributes.\n'.format(blend_node))
        else:
            self.model.blend_node = ""

    def load_morphing_object(self):
        """Loads the selected mesh as the morphing source object."""
        cmds = model.get_maya_cmds()
        selection = self.model.get_selection()
        if not selection:
            cmds.warning("Nothing selected. Please select a mesh and try again.")
            self._reset_source("Failed to Load")
            return
        if len(selection) > 1:
            cmds.warning("You selected more than one source object! Please select only one and try again.")
            self._reset_source("Failed to Load")
            return

        morphing_obj = selection[0]
        blend_nodes = self.model.find_blend_shape_nodes(morphing_obj)
        if not blend_nodes:
            cmds.warning("Unable to find blend shape nodes on the selected object.")
            self._reset_source("Failed to Load")
            return

        self.model.morphing_obj = morphing_obj
        self.view.set_status("source", morphing_obj, "loaded")
        self.view.set_blend_nodes(blend_nodes)

    def load_attribute_holder(self):
        """Loads the selected object as the attribute holder (target)."""
        cmds = model.get_maya_cmds()
        selection = self.model.get_selection()
        if not selection:
            cmds.warning("Nothing selected.")
            self._reset_holder("Failed to Load")
            return
        if len(selection) > 1:
            cmds.warning("You selected more than one object! Please select only one.")
            self._reset_holder("Failed to Load")
            return

        self.model.attr_holder = selection[0]
        self.view.set_status("holder", selection[0], "loaded")

    def _reset_source(self, text):
        """Resets the source object state and status button.

        Args:
            text (str): Status text to display.
        """
        self.model.morphing_obj = ""
        self.model.blend_node = ""
        self.view.set_blend_nodes([])
        self.view.set_status("source", text, "failed")

    def _reset_holder(self, text):
        """Resets the attribute holder state and status button.

        Args:
            text (str): Status text to display.
        """
        self.model.attr_holder = ""
        self.view.set_status("holder", text, "failed")

    def run(self):
        """Runs the create/delete operation. The model reports the result feedback."""
        self.model.run()

    def show_help(self):
        """Shows a help dialog with usage information and a documentation link."""
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle("Add Morphing Attributes - Help")
        try:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Information)
        except AttributeError:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Icon.Information)
        message_box.setText(HELP_TEXT)
        if hasattr(message_box, "exec_"):
            message_box.exec_()
        else:
            message_box.exec()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
