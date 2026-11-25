"""Qt tests for the shared environment-variable browser."""

import os
import sys
import unittest

tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.ui.qt_import as ui_qt
from gt.ui.environment_variables_dialog import EnvironmentVariablesDialog


class TestEnvironmentVariablesDialog(unittest.TestCase):
    """Tests the optional reference column and panel."""

    @classmethod
    def setUpClass(cls):
        """Creates the shared Qt application used by widget tests."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication(sys.argv)

    def setUp(self):
        """Creates a dialog with two variables and one reference."""
        self.activated_references = []
        self.references = {
            "output-dir": [
                {
                    "token": "output-dir",
                    "source_kind": "task",
                    "source_id": "task-a",
                    "source_label": "#01 Export",
                    "enabled": False,
                    "defines": "",
                    "field": "parameters.path",
                    "line": 3,
                    "count": 2,
                    "snippet": "{output-dir}/a.fbx",
                    "via": [],
                }
            ]
        }
        self.dialog = EnvironmentVariablesDialog(
            refresh_callback=lambda: {"{output-dir}": "D:/out", "{temp-dir}": "C:/temp"},
            references_callback=lambda: self.references,
            reference_activated_callback=self.activated_references.append,
        )
        self.dialog.refresh()

    def tearDown(self):
        """Closes the dialog and flushes deferred Qt events."""
        self.dialog.close()
        self.dialog.deleteLater()
        self.application.processEvents()

    def get_row(self, token):
        """Gets the table row showing a token.

        Args:
            token (str): Token text.

        Returns:
            int: Row index, or -1 when missing.
        """
        for row in range(self.dialog.variable_table.rowCount()):
            if self.dialog.get_token_for_row(row=row) == token:
                return row
        return -1

    def test_reference_column_is_hidden_until_enabled(self):
        """Keeps the original layout until references are requested."""
        self.assertTrue(self.dialog.variable_table.isColumnHidden(self.dialog.USED_BY_COLUMN))
        self.assertFalse(self.dialog.used_only_checkbox.isEnabled())

        self.dialog.show_references_checkbox.setChecked(True)
        self.assertFalse(self.dialog.variable_table.isColumnHidden(self.dialog.USED_BY_COLUMN))
        used_by_item = self.dialog.variable_table.item(
            self.get_row("{output-dir}"), self.dialog.USED_BY_COLUMN
        )
        self.assertEqual("1 task", used_by_item.text())

    def test_used_only_hides_unreferenced_variables(self):
        """Hides variables with no references when Used only is checked."""
        self.dialog.show_references_checkbox.setChecked(True)
        self.dialog.used_only_checkbox.setChecked(True)

        self.assertTrue(self.dialog.variable_table.isRowHidden(self.get_row("{temp-dir}")))
        self.assertFalse(self.dialog.variable_table.isRowHidden(self.get_row("{output-dir}")))

    def test_reference_panel_lists_selected_variable_and_activates(self):
        """Lists the selected variable's references and forwards double-clicks."""
        self.dialog.show_references_checkbox.setChecked(True)
        self.dialog.variable_table.selectRow(self.get_row("{output-dir}"))

        self.assertEqual(1, self.dialog.reference_table.rowCount())
        expected = "#01 Export (disabled)"
        self.assertEqual(expected, self.dialog.reference_table.item(0, 0).text())
        expected = "parameters.path (line 3, 2 uses)"
        self.assertEqual(expected, self.dialog.reference_table.item(0, 1).text())
        self.dialog.on_reference_double_clicked(0, 0)
        self.assertEqual(self.references["output-dir"], self.activated_references)

    def test_dialog_without_reference_callback_has_no_toggles(self):
        """Keeps tools without reference support unchanged."""
        dialog = EnvironmentVariablesDialog(refresh_callback=lambda: {"{temp-dir}": "C:/temp"})
        dialog.refresh()

        self.assertIsNone(dialog.show_references_checkbox)
        self.assertTrue(dialog.variable_table.isColumnHidden(dialog.USED_BY_COLUMN))
        self.assertEqual(1, dialog.variable_table.rowCount())
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
