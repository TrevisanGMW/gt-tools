"""Qt regression tests for the Batch Processor user interface."""

import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as ui_qt_utils


test_package_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_package_dir)
package_root_dir = os.path.dirname(tests_dir)
for path_to_append in [package_root_dir, tests_dir]:
    if path_to_append not in sys.path:
        sys.path.append(path_to_append)

from gt.tools.batch_processor import batch_processor_controller
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks
from gt.tools.batch_processor import batch_processor_view
from gt.tools.batch_processor.tasks import task_clip
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.widgets import attr_widget_clip
from gt.tools.batch_processor.widgets import attr_widget_python_script
from gt.tools.batch_processor.widgets import attr_widget_task
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget


class TestBatchProcessorUi(unittest.TestCase):
    """Tests Batch Processor widget refresh and object-lifetime behavior."""

    @classmethod
    def setUpClass(cls):
        """Creates the shared Qt application used by widget tests."""
        application = ui_qt.QtWidgets.QApplication.instance()
        if not application:
            cls.application = ui_qt.QtWidgets.QApplication(sys.argv)
        else:
            cls.application = application

    def setUp(self):
        """Creates a model and view for each UI test."""
        self.model = batch_processor_model.BatchProcessorModel()
        self.task = self.model.tasks[0]
        self.view = batch_processor_view.BatchProcessorView()
        self.view.refresh_tree(self.model)
        self.view.select_task_by_id(self.task.id)

    def tearDown(self):
        """Closes test widgets and flushes deferred Qt events."""
        self.view.close()
        self.application.processEvents()

    def test_task_rename_does_not_replace_widget_during_focus_change(self):
        """Ensures task-name focus loss updates the tree without deleting its widget."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        self.view.controller = controller
        refresh_parent = mock.MagicMock()
        task_widget = attr_widget_task.AttrWidgetTask(
            task=self.task,
            project=self.model,
            refresh_parent_func=refresh_parent,
            controller=controller,
        )
        next_field = ui_qt.QtWidgets.QLineEdit()
        task_widget.content_layout.addWidget(next_field)
        self.view.set_task_widget(task_widget)
        self.view.show()
        self.application.processEvents()

        task_widget.task_name_field.setFocus()
        task_widget.task_name_field.selectAll()
        ui_qt.QtTest.QTest.keyClicks(task_widget.task_name_field, "Renamed Task")
        next_field.setFocus()
        self.application.processEvents()

        expected = "Renamed Task"
        self.assertEqual(expected, self.task.display_name)
        self.assertEqual(expected, self.view.project_item.child(0).text(0))
        self.assertIs(task_widget, self.view.get_task_widget())
        self.assertTrue(ui_qt_utils.is_qt_object_valid(task_widget))
        self.assertTrue(ui_qt_utils.is_qt_object_valid(task_widget.task_name_field))
        refresh_parent.assert_not_called()

    def test_refresh_tree_blocks_intermediate_selection_signals(self):
        """Ensures a tree rebuild does not emit transient selection changes."""
        selection_changed = mock.MagicMock()
        self.view.task_tree.itemSelectionChanged.connect(selection_changed)

        self.view.refresh_tree(self.model)

        selection_changed.assert_not_called()
        expected = self.task.id
        self.assertEqual(expected, self.view.get_selected_task_id())

    def test_clip_snapshot_summary_displays_file_and_clip_counts(self):
        """Ensures Clip Snapshot displays summary counts from its JSON file."""
        snapshot_directory = tempfile.mkdtemp(prefix="gt_clip_snapshot_ui_test_")
        self.addCleanup(shutil.rmtree, snapshot_directory)
        snapshot_path = os.path.join(snapshot_directory, "clip_snapshot.json")
        task_clip.update_clip_snapshot(
            snapshot_path=snapshot_path,
            source_root=snapshot_directory,
            clip_data_by_path={
                "walk.ma": [{"name": "walk"}],
                "run.ma": [{"name": "run"}, {"name": "run_end"}],
            },
        )
        task = batch_processor_tasks.TaskClipSnapshot(settings={"snapshot_path": snapshot_path})
        widget = attr_widget_clip.AttrWidgetClipSnapshotTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        files_label, _ = widget.summary_cells.get("file_count")
        clips_label, _ = widget.summary_cells.get("clip_count")

        self.assertIn("2", files_label.text())
        self.assertIn("3", clips_label.text())
        self.assertIn(task_clip.SNAPSHOT_STATUS_READY, widget.status_label.text())

    def test_update_task_tree_item_updates_label_and_enabled_state(self):
        """Ensures an existing tree row reflects task changes in place."""
        self.task.display_name = "Updated Task"
        self.task.enabled = False

        result = self.view.update_task_tree_item(self.task)

        self.assertTrue(result)
        tree_item = self.view.project_item.child(0)
        expected = "Updated Task"
        self.assertEqual(expected, tree_item.text(0))
        expected = "Task is disabled."
        self.assertEqual(expected, tree_item.toolTip(0))

        self.task.enabled = True
        result = self.view.update_task_tree_item(self.task)

        self.assertTrue(result)
        expected = ""
        self.assertEqual(expected, tree_item.toolTip(0))

    def test_refresh_tree_shows_separator_for_disabled_task(self):
        """Ensures task-list separators remain visible when their task is disabled."""
        self.task.enabled = False
        self.task.settings["force_segment_separator"] = True

        self.view.refresh_tree(self.model)

        separator_item = self.view.project_item.child(0)
        expected = "segment_separator"
        self.assertEqual(expected, separator_item.data(0, self.view.DATA_ROLE))
        task_item = self.view.project_item.child(1)
        expected = self.task.id
        self.assertEqual(expected, task_item.data(0, self.view.DATA_ROLE))

    def test_parent_refresh_is_deferred_until_next_event_loop_cycle(self):
        """Ensures full parent rebuilds do not run inside an emitting callback."""
        refresh_parent = mock.MagicMock()
        task_widget = attr_widget_task.AttrWidgetTask(
            task=self.task,
            project=self.model,
            refresh_parent_func=refresh_parent,
        )

        task_widget.call_parent_refresh()

        refresh_parent.assert_not_called()
        self.application.processEvents()
        refresh_parent.assert_called_once_with()
        task_widget.close()

    def test_python_script_paths_persist_when_the_widget_is_rebuilt(self):
        """Ensures dynamic Python path fields write to task settings."""
        external_task = self.model.add_task(
            batch_processor_tasks.TaskPythonScript(settings={"script_mode": "External File"})
        )
        external_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=external_task,
            project=self.model,
        )
        external_path = "C:/custom/external.py"
        external_widget.external_script_widgets[0]["field"].setText(external_path)
        self.application.processEvents()

        external_return_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=external_task,
            project=self.model,
        )
        self.assertEqual(external_path, external_return_widget.external_script_widgets[0]["field"].text())

        batch_task = self.model.add_task(
            batch_processor_tasks.TaskPythonScript(settings={"script_mode": "Batch Directory"})
        )
        batch_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=batch_task,
            project=self.model,
        )
        batch_path = "C:/custom/scripts"
        batch_widget.batch_directory_widgets[0]["field"].setText(batch_path)
        batch_widget.batch_directory_widgets[0]["include_field"].setText("publish_*.py")
        batch_widget.batch_directory_widgets[0]["exclude_field"].setText("wip_*.py")
        self.application.processEvents()

        batch_return_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=batch_task,
            project=self.model,
        )
        batch_entry = batch_return_widget.batch_directory_widgets[0]
        self.assertEqual(batch_path, batch_entry["field"].text())
        self.assertEqual("publish_*.py", batch_entry["include_field"].text())
        self.assertEqual("wip_*.py", batch_entry["exclude_field"].text())

    def test_inline_python_editor_loads_example_script_when_empty(self):
        """Ensures selecting an example fills an empty inline editor."""
        sample = task_utils.get_script_samples("python_script")[0]
        expected = task_utils.load_script_file(sample["path"])
        editor = InlinePythonEditorWidget(
            sample_scripts_directory="python_script",
        )
        editor.sample_scripts_button.refresh_sample_menu()
        action_labels = [action.text() for action in editor.sample_scripts_button.sample_menu.actions()]

        self.assertIn("Print Batch Context", action_labels)
        self.assertIs(
            editor.python_edit,
            editor.python_editor_widget.get_text_edit(),
        )
        self.assertIs(
            editor.python_edit,
            editor.python_editor_widget.number_bar.text_edit,
        )

        editor.sample_scripts_button.load_sample_script(
            script_path=sample["path"],
            relative_path=sample["relative_path"],
        )

        result = editor.get_text()
        self.assertEqual(expected, result)
        editor.close()

    def test_python_task_inline_editor_exposes_example_menu(self):
        """Ensures the unified Python task uses the shared example menu button."""
        task = self.model.add_task(batch_processor_tasks.TaskPythonScript())
        widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=task,
            project=self.model,
        )
        widget.sample_scripts_button.refresh_sample_menu()
        action_labels = [action.text() for action in widget.sample_scripts_button.sample_menu.actions()]

        expected = "Examples  ▼"
        result = widget.sample_scripts_button.text()
        self.assertEqual(expected, result)
        self.assertTrue(widget.sample_scripts_button.icon().isNull())
        self.assertEqual("padding: 6px;", widget.sample_scripts_button.styleSheet())
        self.assertIn("Print Batch Context", action_labels)
        self.assertIs(
            widget.python_edit,
            widget.python_editor_widget.number_bar.text_edit,
        )
        widget.close()

    def test_inline_python_editor_keeps_line_number_gutter_width_while_scrolling(self):
        """Ensures long scripts cannot resize the line number gutter while scrolling."""
        editor = InlinePythonEditorWidget()
        script_text = "\n".join(["print('line')"] * 150)
        editor.set_text(script_text)
        editor.resize(500, 220)
        editor.show()
        self.application.processEvents()
        number_bar = editor.python_editor_widget.number_bar
        number_bar.update()
        expected_width = number_bar.width()
        scroll_bar = editor.python_edit.verticalScrollBar()

        for scroll_value in [0, scroll_bar.maximum() // 2, scroll_bar.maximum()]:
            scroll_bar.setValue(scroll_value)
            self.application.processEvents()
            number_bar.update()
            result_width = number_bar.width()
            self.assertEqual(expected_width, result_width)

        editor.close()

    def test_python_task_editor_font_size_updates_script_text(self):
        """Ensures the font size control updates Python code, not only line numbers."""
        task = self.model.add_task(batch_processor_tasks.TaskPythonScript())
        widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=task,
            project=self.model,
        )
        widget.python_edit.setPlainText("print('font size')")
        document = widget.python_edit.document()
        before_height = document.documentLayout().blockBoundingRect(document.firstBlock()).height()

        widget.set_editor_font_size(20)
        self.application.processEvents()

        after_height = document.documentLayout().blockBoundingRect(document.firstBlock()).height()
        self.assertGreater(after_height, before_height)
        widget.close()

    def test_inline_python_editor_keeps_existing_code_when_replacement_is_cancelled(self):
        """Ensures an example cannot silently replace a user's inline script."""
        expected = "custom_script = True"
        editor = InlinePythonEditorWidget(
            text=expected,
            sample_scripts_directory="python_script",
        )
        sample = task_utils.get_script_samples("python_script")[0]

        with mock.patch.object(
            editor.sample_scripts_button,
            "confirm_script_replacement",
            return_value=False,
        ):
            editor.sample_scripts_button.load_sample_script(
                script_path=sample["path"],
                relative_path=sample["relative_path"],
            )

        result = editor.get_text()
        self.assertEqual(expected, result)
        editor.close()


if __name__ == "__main__":
    unittest.main()
