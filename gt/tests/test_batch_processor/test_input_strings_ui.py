"""Non-blocking Qt checks for string input table bindings."""

import os
import tempfile
import unittest
from unittest import mock
from gt.ui import qt_import as qt
from gt.ui import resource_library as resources
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.widgets import attr_widget_input_strings
from gt.tools.batch_processor.widgets.attr_widget_input_strings import AttrWidgetInputStringsTask


class TestInputStringsUi(unittest.TestCase):
    """Checks edits, quick append, row removal, activation, number mode, and line files."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application without entering an event loop."""
        cls.application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])

    def create_widget(self, settings):
        """Creates a widget that is closed after the test.

        Args:
            settings (dict): Task settings.

        Returns:
            tuple: Task and widget.
        """
        task = tasks.TaskInputStrings(settings=settings)
        widget = AttrWidgetInputStringsTask(task=task, project=model.BatchProcessorModel())
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return task, widget

    def get_header_labels(self, widget):
        """Gets the row header labels.

        Args:
            widget (AttrWidgetInputStringsTask): Widget under test.

        Returns:
            list: Row header texts.
        """
        return [widget.table.verticalHeaderItem(row).text() for row in range(widget.table.rowCount())]

    def test_table_actions(self):
        """Preserves exact text, duplicate rows, and parent controls throughout editing."""
        task, widget = self.create_widget({"strings": ["Walk", "Run"]})
        clipboard = mock.MagicMock()
        clipboard.text.return_value = "café\nWalk\nWalk"
        with mock.patch.object(qt.QtWidgets.QApplication, "clipboard", return_value=clipboard):
            widget.table.item(0, attr_widget_input_strings.VALUE_COLUMN).setText("  Walk!  ")
            self.assertEqual("  Walk!  ", task.settings["strings"][0])
            widget.buttons["paste"].click()
            self.assertEqual(["  Walk!  ", "Run", "café", "Walk", "Walk"], task.settings["strings"])
            widget.table.cellWidget(1, attr_widget_input_strings.DELETE_COLUMN).click()
            self.assertEqual(["  Walk!  ", "café", "Walk", "Walk"], task.settings["strings"])
            widget.table.clearSelection()
            widget.table.selectRow(2)
            widget.remove_rows()
            self.assertEqual(["  Walk!  ", "café", "Walk"], task.settings["strings"])
            widget.buttons["add"].click()
            self.assertEqual("", task.settings["strings"][-1])
            self.assertEqual("Running: String Table \u2014 3 input(s)", widget.status_label.text())
            widget.table.clearSelection()
            widget.table.selectRow(0)
            widget.copy_rows()
            clipboard.setText.assert_called_once_with("  Walk!  ")

    def test_active_rows_and_indexes(self):
        """Hides numbers for skipped rows and renumbers the remaining ones."""
        task, widget = self.create_widget({"strings": ["A", "B", "", "C"]})
        self.assertEqual(["1", "2", "", "3"], self.get_header_labels(widget))
        self.assertEqual("Active", widget.table.horizontalHeaderItem(attr_widget_input_strings.ACTIVE_COLUMN).text())
        widget.get_active_checkbox(1).setChecked(False)
        self.assertEqual([True, False, True, True], task.settings["string_enabled"])
        self.assertEqual(["1", "", "", "2"], self.get_header_labels(widget))
        self.assertTrue(widget.status_label.text().endswith(" 2 input(s)"))
        widget.set_rows_active(active=False)
        self.assertEqual([False] * 4, task.settings["string_enabled"])
        widget.invert_active_rows()
        self.assertEqual([True] * 4, task.settings["string_enabled"])
        widget.remove_blank_rows()
        self.assertEqual(["A", "B", "C"], task.settings["strings"])

    def test_delete_button_fills_cell_and_centers_icon_with_inherited_padding(self):
        """Keeps row trash buttons centered and fully clickable when table cells grow."""
        task, widget = self.create_widget({"strings": ["Walk"]})
        widget.setStyleSheet(resources.Stylesheet.btn_push_base)
        widget.show()
        header = widget.table.horizontalHeader()
        column = attr_widget_input_strings.DELETE_COLUMN
        header.setSectionResizeMode(column, qt.QtLib.QHeaderView.Interactive)
        header.resizeSection(column, 80)
        widget.table.setRowHeight(0, 60)
        self.application.processEvents()
        button = widget.table.cellWidget(0, column)
        self.assertEqual(qt.QtCore.QSize(20, 20), button.iconSize())
        cell = widget.table.visualRect(widget.table.model().index(0, column))
        self.assertEqual(cell.size(), button.size())
        option = qt.QtWidgets.QStyleOptionButton()
        option.initFrom(button)
        contents = button.style().subElementRect(qt.QtWidgets.QStyle.SE_PushButtonContents, option, button)
        self.assertEqual(button.rect().center(), contents.center())

    def test_modes_switch_pages_and_status(self):
        """Shows only the active mode page and names the running mode in the status line."""
        task, widget = self.create_widget({"strings": ["A"]})
        numbers = attr_widget_input_strings.task_input_strings.INPUT_MODE_NUMBERS
        input_file = attr_widget_input_strings.task_input_strings.INPUT_MODE_FILE
        self.assertEqual(["table"], [mode for mode, page in widget.mode_pages.items() if not page.isHidden()])
        widget.mode_buttons[numbers].click()
        self.assertEqual(numbers, task.settings["input_mode"])
        self.assertEqual([numbers], [mode for mode, page in widget.mode_pages.items() if not page.isHidden()])
        widget.number_spin_boxes["number_start"].setValue(3)
        widget.number_spin_boxes["number_end"].setValue(7)
        self.assertEqual("Running: Number Range — 5 input(s)", widget.status_label.text())
        self.assertEqual("Values: 3, 4, 5, 6, 7", widget.number_preview_label.text())
        widget.number_filter_combo.setCurrentIndex(widget.number_filter_combo.findData("odd"))
        self.assertEqual("odd", task.settings["number_filter"])
        self.assertEqual("Values: 3, 5, 7", widget.number_preview_label.text())
        self.assertEqual("Numbers to skip, e.g. 4, 8, 10-12", widget.number_skip_field.placeholderText())
        widget.number_skip_field.setText("5")
        self.assertEqual("Running: Number Range — 2 input(s)", widget.status_label.text())
        widget.number_skip_field.setText("5, x")
        self.assertIn("Invalid skip list", widget.status_label.text())
        widget.number_skip_field.setText("")
        widget.number_filter_combo.setCurrentIndex(0)
        widget.mode_buttons[input_file].click()
        self.assertIn("Choose an input file", widget.status_label.text())
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        file_path = os.path.join(directory.name, "lines.txt").replace("\\", "/")
        with open(file_path, "w", encoding="utf-8") as line_file:
            line_file.write("Walk\n\nRun\n")
        widget.file_path_field.setText(file_path)
        self.assertEqual(file_path, task.settings["input_file_path"])
        self.assertEqual("Running: Input File — 2 input(s)", widget.status_label.text())
        self.assertEqual("1. Walk\n2. Run", widget.file_preview.toPlainText())
        self.assertEqual(["A"], task.settings["strings"])

    def test_import_and_export_lines(self):
        """Round-trips rows through a UTF-8 text file."""
        task, widget = self.create_widget({"strings": ["café", "Walk"]})
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        file_path = os.path.join(directory.name, "lines.txt")
        with mock.patch.object(attr_widget_input_strings.ui_file_dialog, "file_dialog", return_value=file_path):
            widget.buttons["export"].click()
            with open(file_path, encoding="utf-8") as line_file:
                self.assertEqual("café\nWalk\n", line_file.read())
            widget.buttons["import"].click()
        self.assertEqual(["café", "Walk", "café", "Walk"], task.settings["strings"])
