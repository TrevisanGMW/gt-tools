"""Qt regression tests for transferring custom variables between projects."""

import json
import os
import tempfile
import unittest
from unittest import mock

import gt.ui.qt_import as ui_qt
from gt.tools.batch_processor import batch_processor_environment_variables as variables_io
from gt.tools.batch_processor.widgets import custom_environment_variables_dialog as variables_ui


class TestCustomEnvironmentVariablesDialog(unittest.TestCase):
    """Exercises file actions and row clipboard actions without running Maya queries."""

    @classmethod
    def setUpClass(cls):
        """Creates a non-blocking Qt application for dialog construction."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def setUp(self):
        """Creates isolated dialogs and a clipboard replacement for each test."""
        self.source = variables_ui.CustomEnvironmentVariablesDialog()
        self.destination = variables_ui.CustomEnvironmentVariablesDialog()
        self.addCleanup(self.source.deleteLater)
        self.addCleanup(self.destination.deleteLater)
        self.clipboard = mock.MagicMock()
        self.clipboard.text.return_value = ""
        clipboard_patch = mock.patch.object(ui_qt.QtWidgets.QApplication, "clipboard", return_value=self.clipboard)
        clipboard_patch.start()
        self.addCleanup(clipboard_patch.stop)

    def test_copy_paste_transfers_complete_row_between_dialogs(self):
        """Copies the requested row even if another row is unfinished."""
        self.source.add_variable_row(name="{first}", value="not selected")
        self.source.add_variable_row(name="{maya-selection}", value="cmds.ls(selection=True)", is_query=True)
        self.source.add_variable_row(name="unfinished", value="still editing")
        self.source.copy_variable(row=1)
        self.clipboard.text.return_value = self.clipboard.setText.call_args[0][0]

        self.destination.paste_variable()

        expected = {"maya-selection": {"value": "cmds.ls(selection=True)", "query": True}}
        self.assertEqual(expected, self.destination.get_custom_environment_variables())
        self.assertEqual(3, self.source.variable_table.rowCount())
        self.assertIn("Click Save", self.destination.status_label.text())

    def test_paste_renames_collisions_without_overwriting(self):
        """Gives each pasted copy a distinct name, including normalized collisions."""
        self.destination.add_variable_row(name="{MY_PATH}", value="original")
        self.clipboard.text.return_value = variables_io.serialize_variables(
            {"my-path": {"value": "new", "query": False}}
        )
        self.destination.paste_variable()
        self.destination.paste_variable()
        expected = {
            "my-path": {"value": "original", "query": False},
            "my-path-copy": {"value": "new", "query": False},
            "my-path-copy-2": {"value": "new", "query": False},
        }
        self.assertEqual(expected, self.destination.get_custom_environment_variables())

    def test_context_menu_copies_clicked_row_and_pastes_into_empty_table(self):
        """Uses the clicked row and exposes Paste when no rows exist."""
        self.source.add_variable_row(name="{first}", value="first")
        self.source.add_variable_row(name="{second}", value="second")
        self.source.variable_table.setCurrentCell(0, 0)
        position = ui_qt.QtCore.QPoint(5, self.source.variable_table.rowViewportPosition(1) + 5)
        with mock.patch.object(self.source.variable_context_menu, "popup"):
            self.source.variable_table.customContextMenuRequested.emit(position)
        self.source.variable_context_menu.actions()[0].trigger()
        self.clipboard.text.return_value = self.clipboard.setText.call_args[0][0]

        with mock.patch.object(self.destination.variable_context_menu, "popup"):
            self.destination.variable_table.customContextMenuRequested.emit(ui_qt.QtCore.QPoint(5, 5))
        actions = self.destination.variable_context_menu.actions()
        self.assertFalse(actions[0].isEnabled())
        self.assertTrue(actions[1].isEnabled())
        self.assertFalse(actions[2].isEnabled())
        self.assertFalse(actions[-1].isEnabled())
        actions[1].trigger()
        self.assertEqual({"second": {"value": "second", "query": False}},
                         self.destination.get_custom_environment_variables())

    def test_context_menu_duplicates_and_deletes_clicked_row(self):
        """Duplicates the clicked row with its Query flag and leaves clipboard data intact."""
        self.source.add_variable_row(name="{first}", value="first")
        self.source.add_variable_row(name="{second}", value="cmds.ls(selection=True)", is_query=True)
        self.source.variable_table.setCurrentCell(0, 0)
        position = ui_qt.QtCore.QPoint(5, self.source.variable_table.rowViewportPosition(1) + 5)
        with mock.patch.object(self.source.variable_context_menu, "popup"):
            self.source.show_variable_context_menu(position)
        actions = {action.text(): action for action in self.source.variable_context_menu.actions()}
        actions["Duplicate Variable"].trigger()
        self.assertEqual({"value": "cmds.ls(selection=True)", "query": True},
                         self.source.get_custom_environment_variables()["second-copy"])
        self.clipboard.setText.assert_not_called()
        actions["Delete Variable"].trigger()
        self.assertEqual(["first", "second-copy"], list(self.source.get_custom_environment_variables()))
        self.assertIn("Deleted variable", self.source.status_label.text())

    def test_trash_button_and_query_button_follow_row_after_deletion(self):
        """Keeps row actions attached to their data after the table indices shift."""
        self.source.add_variable_row(name="{first}", value="first")
        self.source.add_variable_row(name="{second}", value="2 + 2", is_query=True)
        trash_button = self.source.variable_table.cellWidget(0, 4)
        self.assertEqual("", trash_button.text())
        self.assertFalse(trash_button.icon().isNull())
        trash_button.click()
        test_button = self.source.variable_table.cellWidget(0, 3)
        with mock.patch.object(variables_io, "evaluate_variable", return_value=4) as evaluate:
            with mock.patch("builtins.print") as output:
                test_button.click()
        evaluate.assert_called_once_with("second", {"second": {"value": "2 + 2", "query": True}}, project=None)
        output.assert_called_once_with("[Batch Processor] {second} = 4")
        self.assertEqual("{second} = 4", self.source.status_label.text())
        self.source.variable_table.cellWidget(0, 4).click()
        self.assertEqual(0, self.source.variable_table.rowCount())

    def test_query_checkbox_controls_test_button_and_uses_current_values(self):
        """Enables testing only for queries and passes current values with project context."""
        self.source.project = variables_io.batch_processor_model.BatchProcessorModel()
        self.source.add_variable_row(name="{result}", value="old expression")
        checkbox = self.source.variable_table.cellWidget(0, 2).findChild(ui_qt.QtWidgets.QCheckBox)
        test_button = self.source.variable_table.cellWidget(0, 3)
        with mock.patch.object(variables_io, "evaluate_variable", return_value=[]) as evaluate:
            test_button.click()
            evaluate.assert_not_called()
            checkbox.setChecked(True)
            self.assertTrue(test_button.isEnabled())
            self.source.variable_table.item(0, 1).setText("cmds.ls(selection=True)")
            with mock.patch("builtins.print"):
                test_button.click()
            evaluate.assert_called_once_with(
                "result", {"result": {"value": "cmds.ls(selection=True)", "query": True}},
                project=self.source.project,
            )
            checkbox.setChecked(False)
            self.assertFalse(test_button.isEnabled())
        self.assertEqual("{result} = []", self.source.status_label.text())
        self.assertEqual({}, self.source.project.custom_environment_variables)

    def test_query_failure_is_reported_in_status_and_console(self):
        """Reports failed tests without replacing the saved expression."""
        self.source.add_variable_row(name="{result}", value="1 / 0", is_query=True)
        with mock.patch.object(variables_io, "evaluate_variable", side_effect=ValueError("division by zero")):
            with mock.patch("builtins.print") as output:
                self.source.variable_table.cellWidget(0, 3).click()
        self.assertIn("Unable to run {result}: division by zero", self.source.status_label.text())
        output.assert_called_once_with("[Batch Processor] Unable to run {result}: division by zero")
        self.assertEqual("1 / 0", self.source.variable_table.item(0, 1).text())

    def test_query_indicator_is_centered_in_cell_with_inherited_styles(self):
        """Checks indicator geometry with both native and toolkit checkbox styling."""
        self.source.add_variable_row(name="{result}", value="2 + 2", is_query=True)
        container = self.source.variable_table.cellWidget(0, 2)
        checkbox = container.findChild(ui_qt.QtWidgets.QCheckBox)
        for stylesheet in ("", variables_ui.ui_res_lib.Stylesheet.checkbox_base):
            with self.subTest(stylesheet=bool(stylesheet)):
                self.source.setStyleSheet(stylesheet)
                self.source.show()
                self.application.processEvents()
                option = ui_qt.QtWidgets.QStyleOptionButton()
                checkbox.initStyleOption(option)
                indicator = checkbox.style().subElementRect(
                    ui_qt.QtWidgets.QStyle.SE_CheckBoxIndicator, option, checkbox
                )
                indicator_center = checkbox.mapTo(container, indicator.center())
                self.assertLessEqual(abs(indicator_center.x() - container.rect().center().x()), 1)
                self.assertLessEqual(abs(indicator_center.y() - container.rect().center().y()), 1)
                self.assertTrue(container.rect().contains(checkbox.mapTo(container, indicator.topLeft())))
                self.assertTrue(container.rect().contains(checkbox.mapTo(container, indicator.bottomRight())))
        self.source.hide()

    def test_export_import_buttons_round_trip_and_skip_existing(self):
        """Transfers editor values through files while preserving destination values."""
        self.source.add_variable_row(name="{z-path}", value="D:\\café\\{project-dir}")
        self.source.add_variable_row(name="{a-query}", value="env['z-path']", is_query=True)
        self.destination.add_variable_row(name="{Z_PATH}", value="keep this path")
        with tempfile.TemporaryDirectory(prefix="gt_variables_ui_") as directory:
            file_path = os.path.join(directory, "variables.json")
            with mock.patch.object(variables_ui.ui_file_dialog, "file_dialog", return_value=file_path):
                self.source.export_variables_button.click()
                self.destination.import_variables_button.click()
        expected = {
            "z-path": {"value": "keep this path", "query": False},
            "a-query": {"value": "env['z-path']", "query": True},
        }
        self.assertEqual(expected, self.destination.get_custom_environment_variables())
        self.assertEqual(list(expected), list(self.destination.get_custom_environment_variables()))
        self.assertIn("Imported 1 variable(s); skipped 1", self.destination.status_label.text())

    def test_invalid_import_is_all_or_nothing(self):
        """Does not append an earlier valid row when a later definition is invalid."""
        payload = {
            "version": 1,
            "custom_environment_variables": {
                "valid": {"value": "first", "query": False},
                "invalid": {"value": "second", "query": "false"},
            },
        }
        self.destination.add_variable_row(name="{original}", value="keep")
        with tempfile.TemporaryDirectory(prefix="gt_variables_ui_") as directory:
            file_path = os.path.join(directory, "invalid.json")
            with open(file_path, "w", encoding="utf-8") as variables_file:
                json.dump(payload, variables_file)
            with mock.patch.object(variables_ui.ui_file_dialog, "file_dialog", return_value=file_path):
                self.destination.import_variables()
        self.assertEqual({"original": {"value": "keep", "query": False}},
                         self.destination.get_custom_environment_variables())
        self.assertIn("Unable to import", self.destination.status_label.text())

    def test_invalid_clipboard_does_not_change_table(self):
        """Rejects unrelated text, empty payloads, and multi-row clipboard payloads."""
        two_rows = {
            "first": {"value": "one", "query": False},
            "second": {"value": "two", "query": False},
        }
        for content in ("unrelated clipboard", variables_io.serialize_variables({}),
                        variables_io.serialize_variables(two_rows)):
            with self.subTest(content=content):
                self.clipboard.text.return_value = content
                self.destination.paste_variable()
                self.assertEqual(0, self.destination.variable_table.rowCount())
                self.assertIn("Unable to paste", self.destination.status_label.text())

    def test_cancelled_file_actions_leave_rows_unchanged(self):
        """Makes cancelled file selectors harmless."""
        with mock.patch.object(variables_ui.ui_file_dialog, "file_dialog", return_value=""):
            with mock.patch.object(variables_io, "write_variables") as write_variables:
                self.source.export_variables_button.click()
                self.destination.import_variables_button.click()
        write_variables.assert_not_called()
        self.assertEqual(0, self.destination.variable_table.rowCount())

    def test_export_appended_extension_conflict_requires_confirmation(self):
        """Checks the actual JSON destination when the user omits the extension."""
        original = {"original": {"value": "keep", "query": False}}
        with tempfile.TemporaryDirectory(prefix="gt_variables_ui_") as directory:
            selected_path = os.path.join(directory, "variables")
            file_path = f"{selected_path}.json"
            variables_io.write_variables(file_path, original)
            with mock.patch.object(variables_ui.ui_file_dialog, "file_dialog", return_value=selected_path):
                with mock.patch.object(ui_qt.QtWidgets.QMessageBox, "question",
                                       return_value=ui_qt.QtWidgets.QMessageBox.No) as question:
                    self.source.export_variables()
            question.assert_called_once()
            self.assertEqual(original, variables_io.read_variables(file_path))

    def test_export_reports_write_failure(self):
        """Reports a file write failure in the dialog status field."""
        with mock.patch.object(variables_ui.ui_file_dialog, "file_dialog", return_value="variables.json"):
            with mock.patch.object(variables_io, "write_variables", side_effect=OSError("locked")):
                self.source.export_variables()
        self.assertIn("Unable to export variables: locked", self.source.status_label.text())


if __name__ == "__main__":
    unittest.main()
