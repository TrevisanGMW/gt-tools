"""Qt regression tests for the Batch Processor user interface."""

import json
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
from gt.tools.batch_processor.widgets import attr_widget_delete_path
from gt.tools.batch_processor.widgets import attr_widget_export_fbx
from gt.tools.batch_processor.widgets import attr_widget_project
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

    def test_delete_path_widget_shows_run_once_before_jobs_option(self):
        """Ensures Delete Path exposes the multi-instance preflight option."""
        delete_task = self.model.add_task(batch_processor_tasks.TaskDeleteProjectFiles())
        task_widget = attr_widget_delete_path.AttrWidgetDeleteProjectFilesTask(
            task=delete_task,
            project=self.model,
        )

        checkbox_labels = [
            label.text()
            for label in task_widget.findChildren(ui_qt.QtWidgets.QLabel)
        ]

        self.assertIn("Run Once Before All Jobs:", checkbox_labels)
        task_widget.deleteLater()

    def test_project_notes_expand_with_the_details_panel(self):
        """Ensures Notes receives the available vertical space in the project panel."""
        project_widget = attr_widget_project.AttrWidgetProject(project=self.model)
        self.view.set_task_widget(project_widget)
        self.view.resize(850, 560)
        self.view.show()
        self.application.processEvents()

        initial_notes_height = project_widget.notes_text_area.height()
        initial_panel_height = project_widget.height()
        self.view.resize(1400, 1400)
        self.application.processEvents()

        notes_height_increase = project_widget.notes_text_area.height() - initial_notes_height
        panel_height_increase = project_widget.height() - initial_panel_height

        self.assertGreater(notes_height_increase, 0)
        self.assertGreater(notes_height_increase, panel_height_increase * 0.75)

    def test_controller_modified_state_detects_nested_extra_data_changes(self):
        """Ensures clean-state comparisons retain an independent data snapshot."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        self.model.extra_data["legacy_settings"] = {"version": 1}

        controller.mark_project_clean()

        self.assertFalse(controller.has_unsaved_changes())
        self.model.extra_data["legacy_settings"]["version"] = 2
        self.assertTrue(controller.has_unsaved_changes())

    def test_clean_project_does_not_open_unsaved_changes_dialog(self):
        """Ensures closing or loading a clean project requires no confirmation."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.mark_project_clean()

        with mock.patch.object(batch_processor_controller.ui_qt.QtWidgets, "QMessageBox") as message_box:
            result = controller.show_unsaved_changes_warning_dialog(
                window=self.view,
                is_close_event=False,
            )

        self.assertFalse(result)
        message_box.assert_not_called()

    def test_view_close_event_displays_unsaved_changes_dialog(self):
        """Ensures a modified standalone view can cancel its native close event."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller.mark_project_clean()
        self.model.project_name = "Modified Batch Project"
        self.view.set_close_event_function(controller.show_unsaved_changes_warning_dialog)

        save_button = object()
        dont_save_button = object()
        cancel_button = object()
        message_box = mock.MagicMock()
        message_box.addButton.side_effect = [save_button, dont_save_button, cancel_button]
        message_box.clickedButton.return_value = cancel_button
        close_event = ui_qt.QtGui.QCloseEvent()

        with mock.patch.object(
            batch_processor_controller.ui_qt.QtWidgets,
            "QMessageBox",
            return_value=message_box,
        ):
            self.view.closeEvent(close_event)

        self.assertFalse(close_event.isAccepted())
        message_box.exec_.assert_called_once_with()
        self.view.close_func = None

    def test_view_close_event_matches_auto_rigger_callback_signature(self):
        """Ensures standalone closes forward the window and native close event."""
        close_callback = mock.MagicMock(return_value=False)
        close_event = ui_qt.QtGui.QCloseEvent()
        self.view.set_close_event_function(close_callback)

        self.view.closeEvent(close_event)

        close_callback.assert_called_once_with(self.view, close_event)
        self.view.close_func = None

    def test_modified_project_uses_parentless_dialog_when_view_is_stale(self):
        """Ensures Maya wrapper changes cannot suppress unsaved-changes warnings."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.mark_project_clean()
        self.model.project_name = "Modified Batch Project"

        save_button = object()
        dont_save_button = object()
        cancel_button = object()
        message_box = mock.MagicMock()
        message_box.addButton.side_effect = [save_button, dont_save_button, cancel_button]
        message_box.clickedButton.return_value = dont_save_button

        with mock.patch.object(
            batch_processor_controller.ui_qt_utils,
            "is_qt_object_valid",
            return_value=False,
        ), mock.patch.object(
            batch_processor_controller.ui_qt.QtWidgets,
            "QMessageBox",
            return_value=message_box,
        ) as message_box_class:
            result = controller.show_unsaved_changes_warning_dialog(
                window=self.view,
                is_close_event=False,
            )

        self.assertFalse(result)
        message_box_class.assert_called_once_with(None)
        message_box.exec_.assert_called_once_with()

    def test_dock_close_event_displays_unsaved_changes_dialog(self):
        """Ensures the Maya dock close hook invokes the unsaved-changes dialog."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller.mark_project_clean()
        self.model.project_name = "Modified Batch Project"
        self.view.set_close_event_function(controller.show_unsaved_changes_warning_dialog)

        save_button = object()
        dont_save_button = object()
        cancel_button = object()
        message_box = mock.MagicMock()
        message_box.addButton.side_effect = [save_button, dont_save_button, cancel_button]
        message_box.clickedButton.return_value = dont_save_button

        with mock.patch.object(
            batch_processor_controller.ui_qt.QtWidgets,
            "QMessageBox",
            return_value=message_box,
        ):
            self.view.dockCloseEventTriggered()

        message_box.exec_.assert_called_once_with()
        self.view.close_func = None

    def test_dock_close_event_matches_auto_rigger_callback_signature(self):
        """Ensures docked closes forward the view using Auto Rigger's keyword form."""
        close_callback = mock.MagicMock(return_value=False)
        self.view.set_close_event_function(close_callback)

        self.view.dockCloseEventTriggered()

        close_callback.assert_called_once_with(window=self.view)
        self.view.close_func = None

    def test_host_close_event_uses_the_view_close_callback(self):
        """Ensures a Maya workspace-control host cannot bypass the close callback."""
        host_window = ui_qt.QtWidgets.QDialog()
        self.view.setParent(host_window)
        close_callback = mock.MagicMock(return_value=True)
        close_event = ui_qt.QtGui.QCloseEvent()
        self.view.set_close_event_function(close_callback)
        self.view.install_host_close_event_filter()

        self.application.sendEvent(host_window, close_event)

        close_callback.assert_called_once_with(self.view, close_event)
        self.assertFalse(close_event.isAccepted())
        self.application.removeEventFilter(self.view)
        self.view._close_event_filter_installed = False
        self.view.close_func = None
        host_window.setParent(None)
        host_window.deleteLater()

    def test_loading_project_stops_when_unsaved_changes_are_cancelled(self):
        """Ensures cancelling the warning preserves the active project."""
        file_descriptor, project_path = tempfile.mkstemp(suffix=".batch")
        os.close(file_descriptor)
        with open(project_path, "w", encoding="utf-8") as project_file:
            json.dump(self.model.to_dict(), project_file)
        self.addCleanup(os.remove, project_path)

        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller._recent_projects = mock.MagicMock()
        controller._recent_projects.normalize_path.return_value = project_path
        controller.show_unsaved_changes_warning_dialog = mock.MagicMock(return_value=True)

        result = controller.load_project_from_path(project_path)

        self.assertFalse(result)
        self.assertIs(self.model, controller.model)
        controller.show_unsaved_changes_warning_dialog.assert_called_once_with(
            window=controller.view,
            is_close_event=False,
        )

    def test_saving_loaded_template_uses_save_as(self):
        """Ensures templates cannot overwrite their source file through Save."""
        template_project = batch_processor_model.BatchProcessorModel()
        template_project.project_file_path = None
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = template_project
        controller.save_project_as = mock.MagicMock(return_value=True)

        result = controller.save_project()

        self.assertTrue(result)
        controller.save_project_as.assert_called_once_with()

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

    def test_fbx_export_frame_controls_follow_auto_frame_range(self):
        """Ensures Auto Frame Range disables the manual FBX frame controls."""
        task = batch_processor_tasks.TaskExportFbx()
        widget = attr_widget_export_fbx.AttrWidgetFbxExportTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        self.assertEqual(0, widget.frame_start_spin.value())
        self.assertEqual(120, widget.frame_end_spin.value())
        self.assertFalse(widget.frame_start_label.isEnabled())
        self.assertFalse(widget.frame_start_spin.isEnabled())
        self.assertFalse(widget.frame_end_label.isEnabled())
        self.assertFalse(widget.frame_end_spin.isEnabled())

        widget.set_auto_frame_range(False)

        self.assertTrue(widget.frame_start_label.isEnabled())
        self.assertTrue(widget.frame_start_spin.isEnabled())
        self.assertTrue(widget.frame_end_label.isEnabled())
        self.assertTrue(widget.frame_end_spin.isEnabled())

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
