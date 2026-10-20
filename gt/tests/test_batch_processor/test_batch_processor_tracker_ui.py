"""Regression tests for tracker launch preferences and upcoming segments."""

import tempfile
import types
import unittest
from unittest import mock

import gt.core.prefs as core_prefs
import gt.ui.qt_import as ui_qt
from gt.tools.batch_processor.batch_processor_controller import BatchProcessorController
from gt.tools.batch_processor.batch_processor_view import BatchProcessorView
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_controller
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler
from gt.tools.batch_processor.tracker import tracker_tree_model
from gt.tools.batch_processor.tracker import tracker_view


class TestTrackerPreferencesAndSegments(unittest.TestCase):
    """Exercises real Qt filters and segment rows without launching workers."""

    @classmethod
    def setUpClass(cls):
        """Creates an application without entering its event loop."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def setUp(self):
        """Isolates preferences and session files in a temporary directory."""
        directory = tempfile.TemporaryDirectory(prefix="gt_tracker_ui_")
        self.addCleanup(directory.cleanup)
        self.root = directory.name
        patcher = mock.patch.object(core_prefs, "get_prefs_dir", return_value=self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def create_controller(self, segments=None, project=None):
        """Creates a tracker with its timers and window display disabled.

        Args:
            segments (list, optional): Ordered input-segment descriptors.
            project (object, optional): Input discovery provider.

        Returns:
            TrackerController: Controller backed by real Qt widgets.
        """
        session = tracker_model.TrackerSession("Test", self.root, 1, [], self.root)
        scheduler = tracker_scheduler.TrackerScheduler(
            session, types.SimpleNamespace(no_log=True), segments=segments, project=project
        )
        view = tracker_view.TrackerView(project_name="Test")
        self.addCleanup(view.deleteLater)
        with mock.patch.object(tracker_controller.TrackerController, "_create_timers"), \
                mock.patch.object(view, "show"):
            controller = tracker_controller.TrackerController(session, scheduler, view)
        return controller

    def create_segments(self):
        """Creates two segments with distinct input and processing tasks.

        Returns:
            list: Segment descriptors used by the scheduler.
        """
        return [
            {"index": index, "input_tasks": [f"input-{index}"],
             "definitions": [{"id": f"task-{index}", "number": 1, "name": f"Task {index + 1}"}]}
            for index in range(2)
        ]

    def test_first_launch_shows_completed_rows(self):
        """Starts with Hide Completed unchecked when no preference exists."""
        controller = self.create_controller()
        self.assertFalse(controller.view.hide_completed_action.isChecked())
        self.assertFalse(controller.proxy_model.hide_completed)

    def test_editor_preference_controls_future_tracker_windows(self):
        """Persists both states and reloads them when a new tracker starts."""
        editor = BatchProcessorController.__new__(BatchProcessorController)
        editor._tracker_prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        editor.log_status = mock.Mock()
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                editor.toggle_tracker_hide_completed_by_default(enabled)
                controller = self.create_controller()
                self.assertEqual(enabled, controller.view.hide_completed_action.isChecked())
                self.assertEqual(enabled, controller.proxy_model.hide_completed)

    def test_editor_preferences_menu_binds_the_saved_default(self):
        """Starts the menu option unchecked and saves changes from its checkbox."""
        editor = BatchProcessorController.__new__(BatchProcessorController)
        editor.view = BatchProcessorView()
        self.addCleanup(editor.view.deleteLater)
        editor._tracker_prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        editor._convert_abs_paths_to_relative = True
        editor._suppress_custom_environment_query_errors = True
        editor._flag_skipped_tasks = True
        editor._ignore_disabled_tasks_for_task_index = False
        editor._confirm_delete_task = True
        editor._auto_segment_imported_projects = True
        editor.log_status = mock.Mock()
        editor.add_menu_preferences()
        checkboxes = [
            widget for widget in editor.view.menu_items
            if isinstance(widget, ui_qt.QtWidgets.QCheckBox)
        ]
        labels = [checkbox.text() for checkbox in checkboxes]
        self.assertEqual(sorted(labels, key=str.casefold), labels)
        checkbox = next(
            widget for widget in checkboxes if widget.text() == "Auto Hide Completed Filter"
        )
        self.assertFalse(checkbox.isChecked())
        checkbox.setChecked(True)
        self.assertTrue(self.create_controller().view.hide_completed_action.isChecked())
        checkbox.setChecked(False)
        self.assertFalse(self.create_controller().view.hide_completed_action.isChecked())

    def test_completed_rows_follow_the_filter(self):
        """Shows a completed job at first launch and hides it only on request."""
        controller = self.create_controller()
        job = tracker_model.TrackerJob("completed", 1, "source.ma", [])
        job.status = tracker_constants.Status.COMPLETED
        controller.session.jobs.append(job)
        controller.refresh()
        self.assertEqual(1, controller.proxy_model.rowCount())
        controller.view.hide_completed_action.setChecked(True)
        self.assertEqual(0, controller.proxy_model.rowCount())
        controller.view.hide_completed_action.setChecked(False)
        self.assertEqual(1, controller.proxy_model.rowCount())

    def test_tracker_filter_and_reset_preserve_launch_preference(self):
        """Keeps tracker interactions local to the running window."""
        prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        prefs.set_bool(tracker_constants.PREFS_KEY_HIDE_COMPLETED_BY_DEFAULT, True)
        prefs.save()
        controller = self.create_controller()
        controller.view.hide_completed_action.setChecked(False)
        controller.view.hide_completed_action.setChecked(True)
        controller.reset_filters()
        self.assertFalse(controller.proxy_model.hide_completed)
        reloaded = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        self.assertTrue(reloaded.get_bool(tracker_constants.PREFS_KEY_HIDE_COMPLETED_BY_DEFAULT))
        self.assertTrue(self.create_controller().proxy_model.hide_completed)

    def test_open_tracker_does_not_overwrite_a_changed_launch_preference(self):
        """Merges preference writes from the editor and an already open tracker."""
        controller = self.create_controller()
        editor = BatchProcessorController.__new__(BatchProcessorController)
        editor._tracker_prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        editor.log_status = mock.Mock()
        editor.toggle_tracker_hide_completed_by_default(True)
        controller.toggle_skip_warnings(False)
        prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        self.assertTrue(prefs.get_bool(tracker_constants.PREFS_KEY_HIDE_COMPLETED_BY_DEFAULT))
        self.assertFalse(prefs.get_bool(tracker_constants.PREFS_KEY_FLAG_SKIPS_AS_WARNINGS))
        editor.toggle_tracker_hide_completed_by_default(False)
        prefs.load()
        self.assertFalse(prefs.get_bool(tracker_constants.PREFS_KEY_HIDE_COMPLETED_BY_DEFAULT))
        self.assertFalse(prefs.get_bool(tracker_constants.PREFS_KEY_FLAG_SKIPS_AS_WARNINGS))

    def test_pending_segments_show_tasks_without_creating_worker_jobs(self):
        """Lists all segments before processing without changing job totals."""
        controller = self.create_controller(segments=self.create_segments())
        model = controller.source_model
        self.assertEqual(2, model.rowCount())
        self.assertEqual([], controller.session.jobs)
        self.assertEqual([], controller.scheduler.regular_queue)
        self.assertIn("1/2", controller.view.primary_summary_label.text())
        for row in range(2):
            parent = model.index(row, 0)
            self.assertEqual(1, model.rowCount(parent))
            child = model.index(0, 0, parent)
            self.assertEqual(parent, model.parent(child))
            self.assertEqual(tracker_constants.Status.WAITING, parent.data(tracker_tree_model.STATUS_ROLE))
        with mock.patch.object(controller.view.tree, "indexAt", return_value=controller.proxy_model.index(0, 0)), \
                mock.patch.object(ui_qt.QtWidgets, "QMenu") as menu:
            controller.show_tree_context_menu(ui_qt.QtCore.QPoint())
            menu.assert_not_called()

    def test_segment_counter_is_hidden_without_multiple_segments(self):
        """Omits segment information for runs with zero or one segment."""
        for segments in (None, [], self.create_segments()[:1]):
            with self.subTest(segment_count=len(segments or [])):
                controller = self.create_controller(segments=segments)
                for finished in (False, True):
                    controller.session.finished = finished
                    controller.refresh()
                    self.assertFalse(controller.scheduler.segmented)
                    self.assertNotIn("Segments", controller.view.primary_summary_label.text())
                    self.assertNotIn("1/1", controller.view.primary_summary_label.text())
                    self.assertEqual([], controller.scheduler.pending_segments)

    def test_segment_rows_are_replaced_even_when_row_count_stays_equal(self):
        """Rescans later inputs at activation and replaces waiting rows safely."""
        segments = self.create_segments()
        project = mock.Mock()
        project.discover_segment_input_files.side_effect = [["first.ma"], ["generated.ma"]]
        controller = self.create_controller(segments=segments, project=project)
        scheduler = controller.scheduler
        project.discover_segment_input_files.assert_not_called()
        self.assertTrue(scheduler._advance_segments())
        controller.refresh()
        self.assertEqual(2, controller.source_model.rowCount())
        first_job = controller.session.jobs[0]
        self.assertIs(first_job, controller.source_model.index(0, 0).internalPointer())
        self.assertFalse(scheduler._advance_segments())
        self.assertEqual(1, project.discover_segment_input_files.call_count)
        scheduler.regular_queue.clear()
        first_job.status = tracker_constants.Status.COMPLETED
        self.assertTrue(scheduler._advance_segments())
        controller.refresh()
        self.assertEqual(2, controller.source_model.rowCount())
        self.assertEqual("generated.ma", controller.session.jobs[1].source_file)
        self.assertIs(controller.session.jobs[1], controller.source_model.index(1, 0).internalPointer())
        self.assertEqual([], scheduler.pending_segments)
        self.assertIn("2/2", controller.view.primary_summary_label.text())

    def test_abort_marks_upcoming_segments_canceled(self):
        """Keeps unstarted segments visible with an accurate canceled status."""
        controller = self.create_controller(segments=self.create_segments())
        controller.scheduler.abort()
        controller.refresh()
        preview = controller.source_model.index(1, 0).internalPointer()
        self.assertEqual(tracker_constants.Status.CANCELED, preview.status)
        self.assertEqual(tracker_constants.Status.CANCELED, preview.tasks[0].status)

    def test_empty_segments_advance_and_finalization_stays_last(self):
        """Removes empty previews while keeping preflight and finalization ordered."""
        project = mock.Mock()
        project.discover_segment_input_files.return_value = []
        controller = self.create_controller(segments=self.create_segments(), project=project)
        preflight = tracker_model.TrackerJob(
            "preflight", 0, "project.batch", [], is_finalization=True, is_preflight=True
        )
        finalization = tracker_model.TrackerJob("finalization", 10_000_000, "project.batch", [], True)
        controller.session.jobs.extend([preflight, finalization])
        controller.refresh()
        self.assertEqual(4, controller.source_model.rowCount())
        self.assertIs(preflight, controller.source_model.jobs[0])
        self.assertIs(finalization, controller.source_model.jobs[-1])
        controller.scheduler._advance_segments()
        controller.refresh()
        self.assertEqual(3, controller.source_model.rowCount())
        controller.scheduler._advance_segments()
        controller.refresh()
        self.assertEqual([preflight, finalization], controller.source_model.jobs)
        self.assertIn("2/2", controller.view.primary_summary_label.text())


if __name__ == "__main__":
    unittest.main()
