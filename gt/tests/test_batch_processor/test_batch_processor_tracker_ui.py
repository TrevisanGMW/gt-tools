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
        tracker_labels = [
            "Auto Hide Completed Filter",
            "Auto-Close When Completed Without Errors",
            "Play Sound When Completed",
            "Show Project Row",
            "Launch in Compact Mode",
            "Launch Minimized",
            "Minimize to System Tray Instead of Taskbar",
        ]
        general_labels = [label for label in labels if label not in tracker_labels]
        self.assertEqual(sorted(general_labels, key=str.casefold), general_labels)
        self.assertEqual(tracker_labels, [label for label in labels if label in tracker_labels])
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

    def test_worker_limit_control_changes_the_live_limit(self):
        """Applies the inline Max Workers value to the running session."""
        controller = self.create_controller()
        self.assertEqual(1, controller.view.worker_limit_spin_box.value())
        self.assertTrue(controller.view.worker_limit_spin_box.isEnabled())

        controller.view.worker_limit_spin_box.setValue(4)
        controller._apply_pending_worker_limit()

        self.assertEqual(4, controller.session.worker_count)
        self.assertIn("worker_count", controller.scheduler.run_settings.manual_keys)

    def test_run_settings_dialog_applies_values(self):
        """Applies retries and timeout from the Adjust Run Settings dialog."""
        controller = self.create_controller()
        controller.show_run_settings_dialog()
        self.addCleanup(controller.run_settings_dialog.close)
        dialog = controller.run_settings_dialog
        dialog.spin_boxes["max_retries"].setValue(2)
        dialog.spin_boxes["timeout_minutes"].setValue(15)

        dialog.apply_button.click()

        self.assertEqual(2, controller.scheduler.max_retries)
        self.assertEqual(15, controller.scheduler.run_settings.timeout_minutes)

    def test_keep_manual_run_settings_preference_is_saved_and_applied(self):
        """Persists the keep-manual preference and forwards it to the scheduler."""
        controller = self.create_controller()
        self.assertFalse(controller.scheduler.run_settings.keep_manual_changes)

        controller.view.keep_manual_run_settings_action.setChecked(True)

        self.assertTrue(controller.scheduler.run_settings.keep_manual_changes)
        later_controller = self.create_controller()
        self.assertTrue(later_controller.view.keep_manual_run_settings_action.isChecked())
        self.assertTrue(later_controller.scheduler.run_settings.keep_manual_changes)

    def test_project_row_is_off_by_default(self):
        """Lists only jobs until the project row preference is enabled."""
        controller = self.create_controller()
        self.assertIsNone(controller.source_model.project_row)
        self.assertFalse(controller.view.show_project_row_action.isChecked())
        self.assertEqual(0, controller.proxy_model.rowCount())

    def test_project_row_stays_pinned_and_summarizes_the_session(self):
        """Pins the row above sorted jobs and aggregates their progress."""
        prefs = core_prefs.Prefs(tracker_constants.PREFS_FILENAME)
        prefs.set_bool(tracker_constants.PREFS_KEY_SHOW_PROJECT_ROW, True)
        prefs.save()
        controller = self.create_controller()
        for number, name in enumerate(("b.ma", "a.ma"), start=1):
            job = tracker_model.TrackerJob(f"job-{number}", number, name, [{"id": f"t{number}", "number": 1, "name": "Task"}])
            controller.session.jobs.append(job)
        controller.session.jobs[0].tasks[0].progress = 100
        controller.session.jobs[0].status = tracker_constants.Status.RUNNING
        controller.refresh()
        proxy = controller.proxy_model
        self.assertTrue(controller.view.show_project_row_action.isChecked())
        self.assertEqual(3, proxy.rowCount())
        for column, order in ((1, ui_qt.QtCore.Qt.AscendingOrder), (1, ui_qt.QtCore.Qt.DescendingOrder),
                              (2, ui_qt.QtCore.Qt.DescendingOrder), (0, ui_qt.QtCore.Qt.AscendingOrder)):
            with self.subTest(column=column, order=order):
                controller.view.tree.sortByColumn(column, order)
                row = proxy.index(0, 0)
                self.assertEqual("Test", proxy.index(0, 1).data())
                self.assertEqual(0, proxy.rowCount(row))
        project = proxy.index(0, 0)
        self.assertEqual(50, project.data(tracker_tree_model.PROGRESS_ROLE))
        self.assertEqual(tracker_constants.Status.RUNNING, project.data(tracker_tree_model.STATUS_ROLE))
        self.assertEqual("0/2", proxy.index(0, 3).data())
        controller.view.search_field.setText("zzz")
        self.assertEqual(1, proxy.rowCount())
        controller.session.finish()
        self.assertEqual(
            tracker_constants.Status.COMPLETED,
            controller.source_model.project_row.status,
        )

    def test_project_row_follows_the_menu_toggle_in_an_open_tracker(self):
        """Adds the row at the top and removes it live."""
        controller = self.create_controller()
        job = tracker_model.TrackerJob("job-1", 1, "a.ma", [])
        controller.session.jobs.append(job)
        controller.refresh()
        proxy = controller.proxy_model
        self.assertEqual(1, proxy.rowCount())
        controller.view.show_project_row_action.setChecked(True)
        self.assertEqual(2, proxy.rowCount())
        self.assertEqual("Test", proxy.index(0, 1).data())
        self.assertIsNotNone(proxy.index(0, 1).data(tracker_tree_model.DECORATION_ROLE))
        self.assertEqual("a.ma", proxy.index(1, 1).data())
        controller.refresh()
        self.assertEqual(2, proxy.rowCount())
        controller.view.show_project_row_action.setChecked(False)
        self.assertEqual(1, proxy.rowCount())
        self.assertEqual("a.ma", proxy.index(0, 1).data())
        self.assertIsNone(controller.source_model.project_row)

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


class TestTrayBadgeFit(unittest.TestCase):
    """Checks the tray badge text always fits inside its badge."""

    @classmethod
    def setUpClass(cls):
        """Creates an application without entering its event loop."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def test_text_fits_at_every_size_and_value(self):
        from gt.tools.batch_processor.tracker import tracker_window_manager as window_manager

        for size in window_manager.TRAY_ICON_SIZES:
            for progress in (0, 7, 42, 100):
                text = str(progress)
                max_width = size * 0.8 * window_manager.DIGIT_WIDTH_RATIO
                max_height = size * 0.5 * window_manager.DIGIT_HEIGHT_RATIO
                font = window_manager.TrackerWindowManager.fit_badge_font(
                    ui_qt.QtGui.QFont(), text, max_width, max_height
                )
                bounds = ui_qt.QtGui.QFontMetricsF(font).tightBoundingRect(text)
                at_minimum = font.pixelSize() <= window_manager.MIN_BADGE_FONT_PIXELS
                self.assertTrue(at_minimum or (bounds.width() <= max_width and bounds.height() <= max_height))

    def test_pixmaps_ignore_screen_scaling(self):
        from gt.tools.batch_processor.tracker import tracker_window_manager as window_manager

        pixmap = window_manager.TrackerWindowManager._build_badge_pixmap(32, 100, "#5fcf86")
        expected = (32, 32, 1.0)
        self.assertEqual(expected, (pixmap.width(), pixmap.height(), pixmap.devicePixelRatio()))


class TestTrackerFramelessWindow(unittest.TestCase):
    """Checks the custom title bar replaces the native one without losing controls."""

    @classmethod
    def setUpClass(cls):
        """Creates an application without entering its event loop."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def setUp(self):
        """Creates a tracker view."""
        self.view = tracker_view.TrackerView(project_name="Frame Test")
        self.addCleanup(self.view.deleteLater)

    def test_window_is_frameless_with_title_bar_and_grips(self):
        expected = (True, "Batch Processor Tracker - Frame Test", 8)
        result = (
            bool(self.view.windowFlags() & ui_qt.QtCore.Qt.FramelessWindowHint),
            self.view.window_frame.title_bar.title_label.text(),
            len(self.view.window_frame.grips),
        )
        self.assertEqual(expected, result)

    def test_title_follows_window_title_changes(self):
        self.view.setWindowTitle("Renamed")
        self.assertEqual("Renamed", self.view.window_frame.title_bar.title_label.text())

    def test_maximize_button_toggles_state_and_grips(self):
        title_bar = self.view.window_frame.title_bar
        self.view.show()
        title_bar.maximize_button.click()
        self.assertTrue(self.view.isMaximized())
        self.assertEqual("Restore", title_bar.maximize_button.toolTip())
        self.assertFalse(any(grip.isVisible() for grip in self.view.window_frame.grips))
        title_bar.maximize_button.click()
        self.assertFalse(self.view.isMaximized())
        self.assertEqual("Maximize", title_bar.maximize_button.toolTip())
        self.view.hide()

    def test_close_button_runs_the_close_flow(self):
        closes = []
        self.view.close_callback = lambda: closes.append(True) or False
        self.view.window_frame.title_bar.close_button.click()
        self.assertEqual([True], closes)
