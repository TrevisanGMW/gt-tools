"""Qt/controller regression checks, skipped when Qt bindings are unavailable."""

import unittest
from unittest.mock import Mock

from gt.tools.connect_attributes.connect_attributes_model import ConnectAttributesModel
from gt.tools.connect_attributes.connect_attributes_controller import ConnectAttributesController

try:
    import gt.ui.qt_import as ui_qt
    from gt.tools.connect_attributes.connect_attributes_view import ConnectAttributesView
except ImportError:
    ui_qt = None


@unittest.skipIf(ui_qt is None, "Qt bindings are unavailable; run with mayapy.")
class TestConnectAttributesView(unittest.TestCase):
    """Exercises real widgets and controller bindings without a Maya scene."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application without initializing Maya."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def setUp(self):
        """Builds a real view with injected preferences and scene service."""
        preferences = Mock()
        preferences.get_raw_preferences.return_value = {}
        self.model = ConnectAttributesModel(preferences=preferences)
        self.service = Mock()
        self.service.get_selection.return_value = ["source", "target", "other"]
        self.service.list_attributes.return_value = ["rotateX", "translateX", "visibility"]
        self.view = ConnectAttributesView()
        self.controller = ConnectAttributesController(self.model, self.view, self.service)
        self.application.processEvents()

    def tearDown(self):
        """Closes and deletes widgets before the next test."""
        self.view.close()
        self.view.deleteLater()
        self.application.processEvents()
        ui_qt.QtCore.QCoreApplication.sendPostedEvents(None, ui_qt.QtCore.QEvent.DeferredDelete)

    def test_modes_hide_loading_controls_and_preserve_objects(self):
        """Switches modes without discarding loaded source or target state."""
        self.model.set_source_object("|rig|controls|storedSource")
        self.model.set_target_objects(["|rig|controls|storedTarget"])
        self.view.set_loaded_nodes(self.model.source_object, self.model.target_objects)
        self.assertTrue(self.view.loaded_controls.isHidden())
        self.assertFalse(self.view.source_status_label.isEnabled())
        self.assertFalse(self.view.target_status_label.isEnabled())
        self.view.loaded_objects_radio.click()
        self.assertFalse(self.model.settings["use_selection"])
        self.assertTrue(self.view.load_source_button.isVisible())
        self.assertTrue(self.view.source_status_label.isEnabled())
        self.assertEqual("storedSource", self.view.source_status_label.text())
        self.assertEqual("storedTarget", self.view.target_status_label.text())
        self.assertIn("|rig|controls|storedSource", self.view.source_status_label.toolTip())
        self.assertIn("|rig|controls|storedTarget", self.view.target_status_label.toolTip())
        self.view.current_selection_radio.click()
        self.assertTrue(self.view.loaded_controls.isHidden())
        self.assertEqual("|rig|controls|storedSource", self.model.source_object)
        self.assertEqual(["|rig|controls|storedTarget"], self.model.target_objects)
        self.service.select_nodes.assert_not_called()

    def test_disconnect_hides_source_and_connection_options(self):
        """Only target controls remain relevant while disconnecting."""
        self.view.loaded_objects_radio.click()
        self.view.disconnect_radio.click()
        self.assertEqual("disconnect", self.model.settings["operation"])
        self.assertTrue(self.view.source_attribute_field.isHidden())
        self.assertTrue(self.view.source_browse_button.isHidden())
        self.assertTrue(self.view.load_source_button.isHidden())
        self.assertTrue(self.view.options_group.isHidden())
        self.assertTrue(self.view.target_browse_button.isVisible())
        self.assertTrue(self.view.load_targets_button.isVisible())
        self.view.connect_radio.click()
        self.assertFalse(self.view.source_attribute_field.isHidden())
        self.assertFalse(self.view.options_group.isHidden())

    def test_advanced_state_is_persistent_and_active_options_are_identified(self):
        """Keeps advanced options explicit even when their section is collapsed."""
        self.assertFalse(self.view.force_checkbox.isVisible())
        self.view.advanced_toggle.click()
        self.assertTrue(self.model.settings["advanced_expanded"])
        self.assertFalse(self.view.advanced_content.isHidden())
        self.assertTrue(self.view.force_checkbox.isVisible())
        self.view.force_checkbox.click()
        self.view.advanced_toggle.click()
        self.assertTrue(self.view.advanced_content.isHidden())
        self.assertFalse(self.view.force_checkbox.isVisible())
        self.assertIn("options active", self.view.advanced_toggle.text())
        self.assertFalse(self.model.settings["advanced_expanded"])

    def test_source_browser_assigns_attribute_without_scene_edits(self):
        """Applies an existing source name directly to its field."""
        self.view.source_browse_button.click()
        dialog = self.view._child_dialogs[-1]
        self.assertEqual("source", dialog.node_combo.currentText())
        dialog.attribute_list.setCurrentRow(1)
        dialog.apply_button.click()
        self.assertEqual("translateX", self.view.source_attribute_field.text())
        self.assertEqual("translateX", self.model.settings["source_attribute"])
        self.service.execute.assert_not_called()
        self.service.select_nodes.assert_not_called()

    def test_target_browser_adds_unique_names_and_can_inspect_each_target(self):
        """Appends selected names once and exposes object and keyable filters."""
        self.view.target_attributes_field.setText("translateX, visibility")
        self.view.target_browse_button.click()
        dialog = self.view._child_dialogs[-1]
        self.assertEqual(2, dialog.node_combo.count())
        dialog.node_combo.setCurrentIndex(1)
        dialog.attribute_filter.setCurrentIndex(1)
        self.service.list_attributes.assert_called_with("other", keyable=True)
        for index in (0, 1):
            dialog.attribute_list.item(index).setSelected(True)
        dialog.apply_button.click()
        self.assertEqual("translateX, visibility, rotateX", self.view.target_attributes_field.text())
        self.service.execute.assert_not_called()

    def test_hidden_browser_attributes_are_not_applied(self):
        """Clears a selection hidden by filtering to prevent accidental additions."""
        self.view.target_browse_button.click()
        dialog = self.view._child_dialogs[-1]
        dialog.attribute_list.item(0).setSelected(True)
        dialog.search_field.setText("translate")
        self.assertFalse(dialog.apply_button.isEnabled())

    def test_disconnect_browser_uses_every_selected_object(self):
        """Treats the first selected object as a target in Disconnect mode."""
        self.view.disconnect_radio.click()
        self.view.target_browse_button.click()
        dialog = self.view._child_dialogs[-1]
        self.assertEqual(3, dialog.node_combo.count())
        self.assertEqual("source", dialog.node_combo.currentText())

    def test_preview_filters_and_refreshes_the_current_request(self):
        """Filters inspected rows and refreshes with the current selection."""
        rows = [
            {"source": "source.translate", "target": "target.translate", "via": "",
             "status": "ready", "details": ""},
            {"source": "source.translate", "target": "other.rotate", "via": "",
             "status": "blocked", "details": "Target is locked"},
        ]
        self.service.inspect.return_value = rows
        self.view.preview_button.click()
        dialog = self.view._child_dialogs[-1]
        self.assertEqual(2, dialog.table.rowCount())
        self.assertTrue(dialog.table.isColumnHidden(1))
        dialog.status_filter.setCurrentIndex(1)
        visible = sum(not dialog.table.isRowHidden(index) for index in range(2))
        self.assertEqual(1, visible)
        dialog.search_field.setText("missing")
        self.assertTrue(all(dialog.table.isRowHidden(index) for index in range(2)))
        self.service.get_selection.return_value = ["newSource", "newTarget"]
        dialog.refresh_button.click()
        self.assertEqual("newSource", self.service.inspect.call_args[0][0]["source_object"])
        self.assertEqual(["newTarget"], self.service.inspect.call_args[0][0]["target_objects"])
        self.assertEqual("missing", dialog.search_field.text())
        self.service.execute.assert_not_called()

    def test_invalid_refresh_clears_old_preview(self):
        """Avoids displaying a stale ready snapshot when selection becomes invalid."""
        self.service.inspect.return_value = []
        dialog = self.controller.preview()
        self.service.get_selection.return_value = []
        dialog.refresh_button.click()
        self.assertEqual(0, dialog.table.rowCount())
        self.assertIn("Choose one source", dialog.summary_label.text())

    def test_actions_keep_equal_padding_and_height(self):
        """Preserves action padding and grows both buttons with the window."""
        for button, expected_padding in (
            (self.view.preview_button, (28, 15, 28, 15)),
            (self.view.run_button, (15, 15, 15, 15)),
        ):
            option = ui_qt.QtWidgets.QStyleOptionButton()
            button.initStyleOption(option)
            contents = button.style().subElementRect(
                ui_qt.QtWidgets.QStyle.SE_PushButtonContents, option, button,
            )
            padding = (
                contents.left(), contents.top(), button.width() - contents.right() - 1,
                button.height() - contents.bottom() - 1,
            )
            self.assertEqual(expected_padding, padding)
        self.assertEqual(self.view.preview_button.height(), self.view.run_button.height())
        original_sizes = [self.view.preview_button.size(), self.view.run_button.size()]
        self.view.resize(self.view.width() + 240, self.view.height() + 160)
        self.application.processEvents()
        for button, original_size in zip((self.view.preview_button, self.view.run_button), original_sizes):
            self.assertGreater(button.width(), original_size.width())
            self.assertGreater(button.height(), original_size.height())


if __name__ == "__main__":
    unittest.main()
