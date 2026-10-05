"""Non-blocking Qt checks for paired input editing and JSON workflows."""

import json
import os
import tempfile
import unittest
from unittest import mock
from gt.ui import qt_import as qt
from gt.ui import resource_library as resources
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tasks import task_input_pairs as pairs
from gt.tools.batch_processor.widgets import attr_widget_input_pairs as editor
from gt.tools.batch_processor.widgets.attr_widget_input import AttrWidgetInputTask
from gt.tools.batch_processor.widgets.attr_widget_task import get_task_widget_class


class TestInputPairsUi(unittest.TestCase):
    """Checks table bindings, missing assignments, clipboard, and JSON actions."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application without entering an event loop."""
        cls.application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])

    def setUp(self):
        """Creates an isolated project and source folder."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name

    def create_widget(self, **settings):
        """Creates an editor closed after its test.

        Args:
            **settings: Input Pairs task settings.

        Returns:
            tuple: Task and pair editor.
        """
        settings.setdefault("source_path", self.directory.name)
        task = tasks.TaskInputPairs(settings=settings)
        self.assertIs(editor.AttrWidgetInputPairsTask, get_task_widget_class(task))
        widget = editor.AttrWidgetInputPairsTask(task=task, project=self.project)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return task, widget

    def create_file(self, filename):
        """Creates a disposable input in the project directory.

        Args:
            filename (str): File basename.

        Returns:
            str: Absolute file path.
        """
        path = os.path.join(self.directory.name, filename)
        with open(path, "w", encoding="utf-8") as input_file:
            input_file.write("// test input\n")
        return path

    def test_missing_rows_colors_and_recovery(self):
        """Colors missing assignments red, discards empty missing rows, and restores descriptions."""
        assigned_path = self.create_file("assigned.ma")
        empty_path = self.create_file("empty.ma")
        task, widget = self.create_widget()
        self.assertEqual(2, widget.table.rowCount())
        self.assertFalse(widget.table.item(0, editor.FILE_COLUMN).flags() & qt.QtCore.Qt.ItemIsEditable)
        widget.table.item(0, editor.STRING_COLUMN).setText("Assigned Description")
        row_id = task.settings["folder_pairs"][0]["id"]
        os.remove(assigned_path)
        os.remove(empty_path)
        widget.refresh_files()
        self.assertEqual(1, widget.table.rowCount())
        self.assertEqual(row_id, task.settings["folder_pairs"][0]["id"])
        self.assertEqual(resources.Color.Hex.red.lower(),
                         widget.table.item(0, editor.FILE_COLUMN).foreground().color().name())
        self.assertIn("unavailable", widget.status_label.text())
        self.create_file("assigned.ma")
        widget.refresh_files()
        self.assertEqual("Assigned Description", widget.table.item(0, editor.STRING_COLUMN).text())
        self.assertEqual(qt.QtCore.Qt.NoBrush, widget.table.item(0, editor.FILE_COLUMN).foreground().style())
        self.assertTrue(widget.status_label.text().endswith("1 input(s)"))

    def test_manual_bindings_modes_and_duplicate_ids(self):
        """Keeps manual edits and independent IDs across duplication, activation, and mode switches."""
        task, widget = self.create_widget(input_mode="manual", manual_pairs=[pairs.create_pair("Walk", "Walking")])
        self.assertTrue(widget.folder_page.isHidden())
        widget.table.item(0, editor.FILE_COLUMN).setText("Custom Walk")
        self.assertEqual("Custom Walk", task.settings["manual_pairs"][0]["input_file"])
        widget.table.selectRow(0)
        widget.duplicate_rows()
        self.assertEqual(2, widget.table.rowCount())
        self.assertEqual(2, len({row["id"] for row in task.settings["manual_pairs"]}))
        widget.set_rows_active(active=False)
        self.assertEqual([False, False], [row["enabled"] for row in task.settings["manual_pairs"]])
        widget.set_rows_active(invert=True)
        widget.mode_buttons["folder"].click()
        self.assertEqual(0, widget.table.rowCount())
        widget.mode_buttons["manual"].click()
        self.assertEqual(["Custom Walk", "Custom Walk"], [row["input_file"] for row in widget.get_row_pairs()])
        widget.table.cellWidget(1, editor.DELETE_COLUMN).click()
        self.assertEqual(1, widget.table.rowCount())
        widget.buttons["add"].click()
        self.assertEqual("", task.settings["manual_pairs"][-1]["input_file"])
        widget.remove_empty_rows()
        self.assertEqual(1, widget.table.rowCount())
        widget.table.item(0, editor.FILE_COLUMN).setText("bad/name")
        self.assertIn("Row 1:", widget.status_label.text())

    def test_hide_and_show_folder_rows_preserves_pair_data(self):
        """Keeps source files, descriptions, IDs, and active states when hiding and showing rows."""
        path = self.create_file("untitled.ma")
        task, widget = self.create_widget()
        widget.table.item(0, editor.STRING_COLUMN).setText("Keep this description")
        widget.table.cellWidget(0, editor.ACTIVE_COLUMN).checkbox.setChecked(False)
        original = dict(task.settings["folder_pairs"][0])
        button = widget.table.cellWidget(0, editor.DELETE_COLUMN)
        self.assertEqual("Hide", button.text())
        self.assertEqual("Hide Pair", button.accessibleName())
        button.click()
        widget.refresh_files()
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(["untitled.ma"], task.settings["excluded_files"])
        self.assertEqual(original, task.settings["folder_pairs"][0])
        self.assertEqual(0, widget.table.rowCount())
        self.assertTrue(widget.buttons["show_hidden"].isEnabled())
        widget.buttons["show_hidden"].click()
        self.assertEqual(1, widget.table.rowCount())
        self.assertEqual([], task.settings["excluded_files"])
        self.assertEqual(original, widget.get_row_pairs()[0])
        self.assertFalse(widget.buttons["show_hidden"].isEnabled())

    def test_confirmed_source_path_refreshes_only_existing_directories(self):
        """Loads a confirmed valid folder and leaves the current table intact for invalid paths."""
        self.create_file("previous.ma")
        task, widget = self.create_widget()
        new_directory = os.path.join(self.directory.name, "new_inputs")
        os.makedirs(new_directory)
        with open(os.path.join(new_directory, "new.mb"), "w", encoding="utf-8") as input_file:
            input_file.write("// new input")
        widget.source_path_field.setText("new_inputs")
        self.assertEqual(["previous.ma"], [row["input_file"] for row in widget.get_row_pairs()])
        event = qt.QtGui.QKeyEvent(qt.QtCore.QEvent.KeyPress, qt.QtLib.Key.Key_Return,
                                  qt.QtCore.Qt.NoModifier)
        self.application.sendEvent(widget.source_path_field, event)
        self.assertEqual(["new.mb"], [row["input_file"] for row in widget.get_row_pairs()])
        with mock.patch.object(widget, "refresh_files") as refresh:
            widget.source_path_field.editingFinished.emit()
            refresh.assert_not_called()
        before = widget.get_row_pairs()
        widget.source_path_field.setText("nonexistent_folder")
        widget.source_path_field.editingFinished.emit()
        self.assertEqual(before, widget.get_row_pairs())
        self.assertEqual(before, task.settings["folder_pairs"])

    def test_browsing_to_folder_refreshes_immediately_and_cancel_preserves_rows(self):
        """Loads selected folders without another confirmation and leaves rows intact on cancellation."""
        self.create_file("previous.ma")
        task, widget = self.create_widget()
        new_directory = os.path.join(self.directory.name, "browsed_inputs")
        os.makedirs(new_directory)
        with open(os.path.join(new_directory, "new.mb"), "w", encoding="utf-8") as input_file:
            input_file.write("// browsed input")
        browse_button = widget.folder_path_widgets["browse_button"]
        with mock.patch.object(editor.file_dialog, "file_dialog", return_value=new_directory):
            browse_button.click()
        self.assertEqual(new_directory, task.get_input_dir(self.project))
        self.assertEqual(["new.mb"], [row["input_file"] for row in widget.get_row_pairs()])
        before = widget.get_row_pairs()
        previous_path = widget.source_path_field.text()
        with mock.patch.object(editor.file_dialog, "file_dialog", return_value=None), \
                mock.patch.object(widget, "refresh_files") as refresh:
            browse_button.click()
            refresh.assert_not_called()
        self.assertEqual(previous_path, widget.source_path_field.text())
        self.assertEqual(before, widget.get_row_pairs())

    def test_text_columns_resize_and_keep_widths_after_refresh_and_mode_changes(self):
        """Allows text column resizing in both modes without resetting chosen proportions."""
        self.create_file("input.ma")
        for mode in (pairs.INPUT_MODE_FOLDER, pairs.INPUT_MODE_MANUAL):
            with self.subTest(mode=mode):
                task, widget = self.create_widget(
                    input_mode=mode, manual_pairs=[pairs.create_pair("Walk", "A long motion description")])
                widget.resize(1100, 800)
                widget.show()
                self.application.processEvents()
                header = widget.table.horizontalHeader()
                for column in (editor.FILE_COLUMN, editor.STRING_COLUMN):
                    self.assertEqual(qt.QtLib.QHeaderView.Interactive, header.sectionResizeMode(column))
                self.assertEqual(qt.QtLib.QHeaderView.ResizeToContents,
                                 header.sectionResizeMode(editor.ACTIVE_COLUMN))
                self.assertEqual(qt.QtLib.QHeaderView.ResizeToContents,
                                 header.sectionResizeMode(editor.DELETE_COLUMN))
                initial_widths = [header.sectionSize(column) for column in (editor.FILE_COLUMN, editor.STRING_COLUMN)]
                self.assertLessEqual(abs(initial_widths[0] - initial_widths[1]), 1)
                available_width = sum(initial_widths)
                header.resizeSection(editor.FILE_COLUMN, 150)
                self.application.processEvents()
                self.assertEqual([150, available_width - 150], [header.sectionSize(column)
                                                               for column in (editor.FILE_COLUMN,
                                                                              editor.STRING_COLUMN)])
                string_width = available_width * 3 // 4
                header.resizeSection(editor.STRING_COLUMN, string_width)
                self.application.processEvents()
                chosen_widths = [available_width - string_width, string_width]
                self.assertEqual(chosen_widths, [header.sectionSize(column)
                                                for column in (editor.FILE_COLUMN, editor.STRING_COLUMN)])
                widget.refresh_files(report=False)
                other_mode = pairs.INPUT_MODE_MANUAL if mode == pairs.INPUT_MODE_FOLDER else pairs.INPUT_MODE_FOLDER
                widget.set_input_mode(mode=other_mode)
                widget.set_input_mode(mode=mode)
                widget.hide()
                widget.show()
                self.application.processEvents()
                self.assertEqual(chosen_widths, [header.sectionSize(column)
                                                for column in (editor.FILE_COLUMN, editor.STRING_COLUMN)])

    def test_text_columns_stretch_with_table_and_keep_actions_at_right(self):
        """Fills wider and narrower tables proportionally while keeping row actions at the right edge."""
        self.create_file("input.ma")
        for mode in (pairs.INPUT_MODE_FOLDER, pairs.INPUT_MODE_MANUAL):
            with self.subTest(mode=mode):
                task, widget = self.create_widget(
                    input_mode=mode, manual_pairs=[pairs.create_pair("Walk", "A long motion description")])
                widget.resize(1100, 800)
                widget.show()
                self.application.processEvents()
                header = widget.table.horizontalHeader()
                header.resizeSection(editor.FILE_COLUMN, 150)
                self.application.processEvents()
                previous_widths = [header.sectionSize(column)
                                   for column in (editor.FILE_COLUMN, editor.STRING_COLUMN)]
                chosen_ratio = previous_widths[0] / sum(previous_widths)
                for window_width in (1500, 950, 1250):
                    widget.resize(window_width, 800)
                    self.application.processEvents()
                    text_widths = [header.sectionSize(column)
                                   for column in (editor.FILE_COLUMN, editor.STRING_COLUMN)]
                    available_width = widget.table.viewport().width() - sum(
                        header.sectionSize(column) for column in (editor.ACTIVE_COLUMN, editor.DELETE_COLUMN))
                    self.assertEqual(available_width, sum(text_widths))
                    self.assertAlmostEqual(chosen_ratio, text_widths[0] / available_width, delta=0.002)
                    for previous, current in zip(previous_widths, text_widths):
                        if sum(text_widths) > sum(previous_widths):
                            self.assertGreater(current, previous)
                        else:
                            self.assertLess(current, previous)
                    self.assertEqual(widget.table.viewport().width(),
                                     header.sectionViewportPosition(editor.DELETE_COLUMN)
                                     + header.sectionSize(editor.DELETE_COLUMN))
                    button = widget.table.cellWidget(0, editor.DELETE_COLUMN)
                    self.assertLessEqual(abs(widget.table.viewport().rect().right() - button.geometry().right()), 1)
                    self.assertFalse(widget.table.horizontalScrollBar().isVisible())
                    previous_widths = text_widths

                for row_index in range(40):
                    widget.insert_pair(pairs.create_pair(f"Extra_{row_index}", "Description"))
                self.application.processEvents()
                self.assertTrue(widget.table.verticalScrollBar().isVisible())
                self.assertEqual(widget.table.viewport().width(), header.length())
                widget.refresh_files(report=False)
                self.application.processEvents()
                self.application.processEvents()
                self.assertFalse(widget.table.verticalScrollBar().isVisible())
                self.assertEqual(widget.table.viewport().width(), header.length())
                self.assertAlmostEqual(chosen_ratio, header.sectionSize(editor.FILE_COLUMN)
                                       / widget.get_pair_text_columns_width(), delta=0.002)

    def test_row_buttons_fill_cells_and_center_contents_with_inherited_padding(self):
        """Keeps folder and manual actions centered when cells grow under the tool stylesheet."""
        self.create_file("input.ma")
        for mode in (pairs.INPUT_MODE_FOLDER, pairs.INPUT_MODE_MANUAL):
            with self.subTest(mode=mode):
                task, widget = self.create_widget(input_mode=mode,
                                                 manual_pairs=[pairs.create_pair("Walk", "Walking")])
                widget.setStyleSheet(resources.Stylesheet.btn_push_base)
                widget.show()
                header = widget.table.horizontalHeader()
                header.setSectionResizeMode(editor.DELETE_COLUMN, qt.QtLib.QHeaderView.Interactive)
                for width, row_height in ((64, 40), (96, 72)):
                    header.resizeSection(editor.DELETE_COLUMN, width)
                    widget.table.setRowHeight(0, row_height)
                    self.application.processEvents()
                    button = widget.table.cellWidget(0, editor.DELETE_COLUMN)
                    if mode == pairs.INPUT_MODE_MANUAL:
                        self.assertEqual(qt.QtCore.QSize(20, 20), button.iconSize())
                    cell = widget.table.visualRect(widget.table.model().index(0, editor.DELETE_COLUMN))
                    self.assertEqual(cell.size(), button.size())
                    option = qt.QtWidgets.QStyleOptionButton()
                    option.initFrom(button)
                    contents = button.style().subElementRect(
                        qt.QtWidgets.QStyle.SE_PushButtonContents, option, button)
                    self.assertEqual(button.rect().center(), contents.center())

    def test_folder_footer_counts_refresh_preview_and_hide_actions(self):
        """Shows discovery and missing assignment counts and previews only active available inputs."""
        assigned = self.create_file("assigned.ma")
        unassigned = self.create_file("unassigned.ma")
        self.create_file("inactive.mb")
        self.create_file("ignored.txt")
        task, widget = self.create_widget(folder_pairs=[pairs.create_pair("assigned.ma", "Assigned"),
                                          pairs.create_pair("inactive.mb", "Inactive", enabled=False),
                                          pairs.create_pair("missing.ma", "Retain me")])
        document = qt.QtGui.QTextDocument()
        document.setHtml(widget.input_count_label.text())
        text = document.toPlainText()
        self.assertIn("Found Types: ma, mb, txt | Input Types: ma",
                      [" ".join(line.split()) for line in text.splitlines()])
        for expected in ("Input Files: 2", "Total Files: 4", "File Types: 3", "Found Types: ma, mb, txt",
                         "Input Types: ma", "Assigned Pairs: 3", "Unassigned Pairs: 1", "Inactive Pairs: 1",
                         "Missing Files with Strings: 1", "Unavailable Files: 1", "Hidden Pairs: 0"):
            self.assertIn(expected, text)
        with mock.patch.object(widget, "show_path_list") as preview:
            widget.buttons["resolved"].click()
            self.assertEqual([assigned, unassigned], preview.call_args.kwargs["file_paths"])
        self.create_file("new.ma")
        widget.buttons["refresh"].click()
        self.assertEqual(5, widget.table.rowCount())
        widget.show_context_menu(qt.QtCore.QPoint(5, 5))
        labels = [action.text() for action in widget.context_menu.actions()]
        self.assertIn("Hide Unassigned Pairs", labels)
        self.assertIn("Hide Selected", labels)
        self.assertIn("Show Hidden", labels)
        self.assertNotIn("Delete Selected", labels)
        widget.context_menu.close()

    def test_manual_footer_controls_counts_and_invalid_names(self):
        """Keeps feedback and preview controls available for virtual named scenes."""
        task, widget = self.create_widget(
            input_mode="manual", manual_pairs=[pairs.create_pair("Walk", "Walking"),
            pairs.create_pair("Run", "", enabled=False), pairs.create_pair("", "No name")])
        document = qt.QtGui.QTextDocument()
        document.setHtml(widget.input_count_label.text())
        for expected in ("Input Files: 1", "Total Files: 0", "Found Types: None", "Input Types: ma",
                         "Assigned Pairs: 2", "Unassigned Pairs: 1", "Inactive Pairs: 1", "Unnamed Pairs: 1"):
            self.assertIn(expected, document.toPlainText())
        self.assertFalse(widget.buttons["refresh"].isHidden())
        self.assertFalse(widget.buttons["resolved"].isHidden())
        self.assertTrue(widget.buttons["show_hidden"].isHidden())
        with mock.patch.object(widget, "show_path_list") as preview:
            widget.buttons["resolved"].click()
            paths = preview.call_args.kwargs["file_paths"]
            self.assertEqual(["Walk.ma"], [os.path.basename(path) for path in paths])
            self.assertFalse(os.path.exists(paths[0]))
        widget.table.item(0, editor.FILE_COLUMN).setText("bad/name")
        document.setHtml(widget.input_count_label.text())
        self.assertIn("Invalid Names: 1", document.toPlainText())

    def test_input_files_keeps_all_statistics_with_shared_footer(self):
        """Preserves Input Files feedback and its refresh/preview actions after sharing the footer."""
        path = self.create_file("input.ma")
        self.create_file("ignored.txt")
        task = tasks.TaskInput(settings={"source_path": self.directory.name})
        widget = AttrWidgetInputTask(task=task, project=self.project)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        document = qt.QtGui.QTextDocument()
        document.setHtml(widget.input_count_label.text())
        for expected in ("Input Files: 1", "Total Files: 2", "File Types: 2",
                         "Found Types: ma, txt", "Input Types: ma"):
            self.assertIn(expected, document.toPlainText())
        with mock.patch.object(widget, "show_path_list") as preview:
            widget.input_feedback.preview_button.click()
            self.assertEqual([path], preview.call_args.kwargs["file_paths"])
        self.create_file("new.mb")
        widget.input_feedback.refresh_button.click()
        self.assertIn(".mb: 1", widget.input_count_label.toolTip())

    def test_json_files_and_invalid_import_are_atomic(self):
        """Exports inactive values and imports fresh identities without changing data on invalid JSON."""
        task, widget = self.create_widget(input_mode="manual",
                                         manual_pairs=[pairs.create_pair("Walk", "  caf\u00e9  ", enabled=False)])
        path = os.path.join(self.directory.name, "pairs.json")
        with mock.patch.object(editor.file_dialog, "file_dialog", return_value=path):
            widget.export_pairs()
        with open(path, encoding="utf-8") as pair_file:
            data = json.load(pair_file)
        self.assertEqual("  caf\u00e9  ", data["pairs"][0]["input_string"])
        self.assertFalse(data["pairs"][0]["enabled"])
        with mock.patch.object(editor.file_dialog, "file_dialog", return_value=path):
            widget.import_pairs()
        self.assertEqual(2, widget.table.rowCount())
        self.assertEqual(2, len({row["id"] for row in task.settings["manual_pairs"]}))
        before = json.dumps(task.settings, sort_keys=True)
        with self.assertRaises(ValueError):
            widget.apply_pair_data({"version": 1, "mode": "manual", "pairs": [pairs.create_pair("bad/name")]})
        self.assertEqual(before, json.dumps(task.settings, sort_keys=True))

    def test_folder_import_merges_assignments_and_preserves_missing(self):
        """Imports descriptions by relative filename without duplicating existing rows or losing missing data."""
        self.create_file("untitled.ma")
        task, widget = self.create_widget()
        row_id = task.settings["folder_pairs"][0]["id"]
        widget.apply_pair_data({"version": 1, "mode": "folder", "pairs": [
            pairs.create_pair("untitled.ma", "Untitled Maya File"),
            pairs.create_pair("missing.ma", "Keep Me")]})
        self.assertEqual(2, widget.table.rowCount())
        self.assertEqual(row_id, task.settings["folder_pairs"][0]["id"])
        self.assertEqual(["Untitled Maya File", "Keep Me"],
                         [row["input_string"] for row in widget.get_export_data()["pairs"]])

    def test_clipboard_pairs_and_context_menu(self):
        """Pastes spreadsheet columns, copies JSON, and exposes import/export and selected row actions."""
        task, widget = self.create_widget(input_mode="manual")
        clipboard = mock.MagicMock()
        clipboard.text.return_value = "Walk\tA person walks\nRun\tA person runs"
        with mock.patch.object(qt.QtWidgets.QApplication, "clipboard", return_value=clipboard):
            widget.paste_pairs()
            self.assertEqual(["Walk", "Run"], [row["input_file"] for row in task.settings["manual_pairs"]])
            widget.table.selectRow(1)
            widget.copy_rows()
            copied = json.loads(clipboard.setText.call_args[0][0])
            self.assertEqual(["Run"], [row["input_file"] for row in copied["pairs"]])
        widget.show_context_menu(qt.QtCore.QPoint(5, 5))
        labels = [action.text() for action in widget.context_menu.actions()]
        for label in ("Duplicate Selected", "Import JSON", "Export JSON", "Delete Selected", "Invert Active"):
            self.assertIn(label, labels)
        widget.context_menu.close()
