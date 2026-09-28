"""Offscreen Maya/Qt tests for authoring actions and asynchronous delivery."""

import os
import threading
import time
import unittest
import tempfile
from unittest.mock import patch, Mock


class TestKimodoGeneratorUI(unittest.TestCase):
    """Exercises real Qt widgets in a disposable standalone process."""

    @classmethod
    def setUpClass(cls):
        """Creates QApplication before initializing standalone Maya."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        try:
            from PySide6 import QtWidgets, QtGui
            import maya.standalone
        except ImportError:
            raise unittest.SkipTest("Requires Maya 2025 mayapy with PySide6.")
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        if os.path.isfile("C:/Windows/Fonts/segoeui.ttf"):
            QtGui.QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")
            cls.app.setFont(QtGui.QFont("Segoe UI", 9))
        try:
            maya.standalone.initialize(name="python")
        except RuntimeError:
            raise unittest.SkipTest("Use a fresh mayapy process.")
        cls.standalone = maya.standalone

    @classmethod
    def tearDownClass(cls):
        """Releases the standalone session owned by the tests."""
        cls.standalone.uninitialize()

    def setUp(self):
        """Creates one independent MVC instance."""
        from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
        from gt.tools.kimodo_generator.kimodo_generator_view import KimodoGeneratorView
        from gt.tools.kimodo_generator.kimodo_generator_controller import KimodoGeneratorController

        self.model = KimodoGeneratorModel(preferences=False)
        self.view = KimodoGeneratorView()
        self.controller = KimodoGeneratorController(self.model, self.view)
        self.controller.timer.stop()
        self.app.processEvents()

    def tearDown(self):
        """Closes the view and processes queued Qt cleanup."""
        self.view.close()
        self.app.processEvents()

    def test_prompt_reorder_and_disabled_constraint(self):
        """Preserves text while changing segment order and disabling a pose entry."""
        self.controller.add_prompt()
        self.view.prompts.selectRow(1)
        self.controller.prompt_up()
        self.assertEqual("Describe the next motion.", self.model.definition["prompts"][0]["text"])
        self.model.add_constraint({"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]})
        self.controller.populate_constraints()
        from gt.ui.qt_import import QtCore

        self.view.constraints.item(0, 0).setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.controller.gather()
        self.assertEqual([], self.model.build_definition().as_dict()["constraints"])

    def test_network_delivery_is_on_main_thread(self):
        """Runs worker code off-thread and delivers its callback on the UI thread."""
        received = []

        def operation():
            """Checks the executing thread.

            Returns:
                bool: Whether this is the main thread.
            """
            return threading.current_thread() is threading.main_thread()

        def ready(result):
            """Records result and callback thread affinity.

            Args:
                result (bool): Worker affinity.
            """
            received.append((result, threading.current_thread() is threading.main_thread()))

        self.controller.run_network("test", operation, ready)
        deadline = time.monotonic() + 5
        while not received and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertEqual([(False, True)], received)

    def test_tokens_are_scoped_to_server(self):
        """Never sends the current bearer token to a different history origin."""
        self.view.token.setText("secret")
        self.controller.gather()
        same = self.controller._job_client({"url": self.model.connection["url"]})
        other = self.controller._job_client({"url": "http://another-server:7861"})
        self.assertEqual("secret", same.connection.token)
        self.assertIsNone(other.connection.token)

    def test_connection_fields_and_icon(self):
        """Switches launch controls and resolves the registered vector icon."""
        from gt.ui.qt_import import QtCore

        self.assertEqual(True, self.view.show_console.isChecked())
        self.assertFalse(self.view.show_console.isEnabled())
        self.assertEqual(2, self.view.launch_options.count())
        self.assertTrue(self.view.launch_options.alignment() & QtCore.Qt.AlignmentFlag.AlignCenter)
        self.view.mode.setCurrentIndex(self.view.mode.findData("wsl"))
        self.assertTrue(self.view.distribution.isEnabled())
        self.assertTrue(self.view.buttons["restart_bridge"].isEnabled())
        self.assertTrue(self.view.show_console.isEnabled())
        self.view.mode.setCurrentIndex(self.view.mode.findData("native"))
        self.assertFalse(self.view.distribution.isEnabled())
        self.assertTrue(self.view.python_path.isEnabled())
        self.assertFalse(self.view.windowIcon().isNull())
        self.assertEqual(["Connection", "Generate", "Constraints", "HumanIK", "Summary", "Results"],
                         [self.view.tabs.tabText(index) for index in range(self.view.tabs.count())])
        self.assertNotIn("help", self.view.buttons)

    def test_bridge_console_preference_saves_immediately(self):
        """Persists the local launch presentation without requiring a connection attempt."""
        with patch.object(self.model, "save_preferences") as save:
            self.view.show_console.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.connection["show_console"])

    def test_wsl_distribution_selection_saves_immediately(self):
        """Keeps the last selected distribution even when a later bridge start fails."""
        combo = self.view.distribution
        combo.clear()
        combo.addItems(["Ubuntu", "Ubuntu-26.04"])
        with patch.object(self.model, "save_preferences") as save:
            combo.setCurrentIndex(1)
            save.assert_called_once()
        self.assertEqual("Ubuntu-26.04", self.model.connection["distribution"])

    def test_bridge_control_status_and_management_dispatch(self):
        """Separates non-mutating probes from confirmed stop/restart operations."""
        from gt.ui.qt_import import QtWidgets

        with patch.object(self.controller, "run_network") as dispatch:
            self.controller.test_bridge()
            self.assertEqual("test_bridge", dispatch.call_args.args[0])
            callback = dispatch.call_args.args[2]
            callback({"status": "ready", "features": ["shutdown"], "runtime": {
                "pid": 123, "platform": "Linux", "python_executable": "/env/bin/python",
                "bridge_script": "/cache/gt/utils/kimodo.py", "job_directory": "/cache/jobs",
                "device": "cuda", "text_encoder_url": "http://127.0.0.1:9550",
                "queued_jobs": 0, "active_job_id": None, "unfinished_jobs": 0}})
            self.assertIn("PID: 123", self.view.connection_info.text())
            self.assertIn("Runs in: Linux", self.view.connection_info.text())

        with patch.object(self.controller, "run_network") as dispatch:
            self.controller.test_encoder()
            callback = dispatch.call_args.args[2]
            callback({"url": "http://127.0.0.1:9550", "api_name": "DemoWrapper"})
            self.assertIn("Text encoder is ready", self.view.status.text())

        self.view.mode.setCurrentIndex(self.view.mode.findData("wsl"))
        self.view.python_path.setText("/home/test/kimodo_env/bin/python")
        self.view.distribution.setCurrentText("Ubuntu-Test")
        yes = QtWidgets.QMessageBox.StandardButton.Yes
        with patch.object(QtWidgets.QMessageBox, "question", return_value=yes):
            with patch.object(self.controller, "run_network") as dispatch:
                self.controller.restart_bridge()
                self.assertEqual("restart_bridge", dispatch.call_args.args[0])
            with patch.object(self.controller, "run_network") as dispatch:
                self.controller.stop_bridge()
                self.assertEqual("stop_bridge", dispatch.call_args.args[0])

    def test_missing_steps_are_warnings_without_tracebacks(self):
        """Treats missing job/pose prerequisites as guidance rather than exceptions."""
        from gt.tools.kimodo_generator import kimodo_generator_controller as module

        for key in ("open_folder", "create_skeleton", "preview_pose", "capture_pose", "use_selection"):
            with self.subTest(action=key), patch.object(module.logger, "exception") as traceback:
                with patch.object(module.logger, "warning") as warning:
                    self.controller._action_callback(key)()
                    self.assertEqual("warning", self.view.status.property("feedback_level"))
                    self.assertTrue(self.view.status.text().startswith("Warning:"))
                    warning.assert_called_once()
                    traceback.assert_not_called()

    def test_download_folder_persists_despite_incomplete_prompt(self):
        """Saves folder browsing immediately through real Prefs, independently of prompt validation."""
        from gt.core.prefs import Prefs
        from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
        from gt.ui.qt_import import QtWidgets

        with tempfile.TemporaryDirectory() as directory:
            self.model.prefs = Prefs("kimodo_generator_test", location_dir=directory)
            self.view.seed.setText("unfinished seed")
            chosen = os.path.join(directory, "my downloads")
            with patch.object(QtWidgets.QFileDialog, "getExistingDirectory", return_value=chosen):
                self.controller.browse_output()
            preferences = Prefs("kimodo_generator_test", location_dir=directory)
            with patch("gt.core.prefs.Prefs", return_value=preferences):
                restored = KimodoGeneratorModel()
            self.assertEqual(chosen, restored.output_directory)
            self.assertEqual(chosen, self.view.output.text())
            self.model.prefs = None
            self.view.seed.setText("12345")

    def test_every_control_has_detailed_help(self):
        """Checks action, field, and tab help coverage."""
        from gt.tools.kimodo_generator.kimodo_generator_help import ACTION_TOOLTIPS, CONTROL_TOOLTIPS

        self.assertEqual(set(self.view.buttons), set(ACTION_TOOLTIPS))
        for name in CONTROL_TOOLTIPS:
            self.assertGreater(len(getattr(self.view, name).toolTip()), 65, name)
        for button in self.view.buttons.values():
            self.assertGreater(len(button.toolTip()), 65)

    def test_results_categories_prioritize_normal_workflow(self):
        """Keeps automatic/recovery/history actions grouped and everyday actions visible at the bottom."""
        self.assertFalse(self.view.results_manual.isChecked())
        self.assertTrue(self.view.results_manual_content.isHidden())
        self.assertFalse(self.view.results_history.isChecked())
        self.assertTrue(self.view.results_history_content.isHidden())
        self.assertIs(self.view.results_manual_content,
                      self.view.buttons["download_results"].parentWidget())
        self.assertIs(self.view.results_history_content,
                      self.view.buttons["clear_history"].parentWidget())
        self.assertIs(self.view.results_selected,
                      self.view.buttons["open_folder"].parentWidget())
        self.assertIn("font-weight: bold", self.view.buttons["open_folder"].styleSheet())

    def test_sample_selector_appears_only_for_multiple_results(self):
        """Uses the only motion implicitly while preserving requested alternatives."""
        from gt.ui.qt_import import QtGui, QtWidgets
        from gt.utils import kimodo

        job = self.model.add_job({"job_id": "a" * 32, "status": "succeeded",
                                  "resolved": {"samples": ["motion.json"]}}, kimodo.KimodoConnection())
        self.controller.populate_jobs()
        self.assertTrue(self.view.sample_selector.isHidden())
        self.assertEqual(["motion.json"], [self.view.sample.itemText(0)])
        job["resolved"]["samples"] = ["motion.json", "sample_1.json", "sample_2.json"]
        self.controller.refresh_job_details()
        self.assertFalse(self.view.sample_selector.isHidden())
        self.assertEqual(["motion.json", "sample_1.json", "sample_2.json"],
                         [self.view.sample.itemText(index) for index in range(self.view.sample.count())])
        self.assertEqual(0, self.view.sample_selector.layout().contentsMargins().left())
        font = QtGui.QFont(self.view.font())
        font.setPointSize(15)
        self.view.setFont(font)
        self.view.resize(530, 590)
        self.app.processEvents()
        self.view.refresh_layout_metrics()
        self.app.processEvents()
        page = self.view.tabs.widget(self.view.results_tab_index)
        scroll = page.findChild(QtWidgets.QScrollArea)
        self.assertLessEqual(scroll.horizontalScrollBar().maximum(), 1)

    def test_tables_fit_content_with_a_flexible_final_column(self):
        """Initializes useful column widths for prompts, constraints, and jobs across DPI changes."""
        from gt.ui.qt_import import QtWidgets
        from gt.utils import kimodo

        self.model.add_constraint({"type": "root2d", "frame_indices": [0, 29],
                                   "smooth_root_2d": [[0, 0], [1, 2]]}, "Long constraint name")
        self.controller.populate_constraints()
        self.model.add_job({"job_id": "a" * 32, "status": "succeeded",
                            "stage": "creating Maya files"}, kimodo.KimodoConnection())
        self.controller.populate_jobs()
        for table in (self.view.prompts, self.view.constraints, self.view.jobs):
            header = table.horizontalHeader()
            self.assertEqual(True, bool(table.property("gt_columns_fitted")))
            for column in range(table.columnCount() - 1):
                self.assertEqual(QtWidgets.QHeaderView.ResizeMode.Interactive,
                                 header.sectionResizeMode(column))
                self.assertGreaterEqual(table.columnWidth(column),
                                        table.fontMetrics().horizontalAdvance(
                                            table.horizontalHeaderItem(column).text())
                                        + table.fontMetrics().horizontalAdvance("  "))
            self.assertEqual(QtWidgets.QHeaderView.ResizeMode.Interactive,
                             header.sectionResizeMode(table.columnCount() - 1))
        self.assertIn("QTableWidget::item", self.view.styleSheet())

    def test_table_widths_save_and_restore_without_dpi_refitting(self):
        """Keeps user-sized columns through refresh and preference restoration."""
        table = self.view.jobs
        with patch.object(self.model, "save_preferences") as save:
            table.setColumnWidth(0, 177)
            self.app.processEvents()
            save.assert_called()
        expected = list(self.model.table_widths["jobs"])
        self.assertEqual(177, expected[0])
        self.view.refresh_layout_metrics()
        self.assertEqual(177, table.columnWidth(0))
        table.setColumnWidth(0, 80)
        self.model.table_widths["jobs"] = expected
        self.controller.restore_table_widths()
        self.assertEqual(expected, [table.columnWidth(index) for index in range(table.columnCount())])

    def test_summary_tab_created_time_and_primary_buttons(self):
        """Summarizes settings, timestamps jobs, and uses standard grey primary actions."""
        from gt.utils import kimodo

        self.view.model.addItem("Kimodo SOMA", "kimodo-soma")
        self.model.add_job({"job_id": "a" * 32, "status": "queued", "stage": "queued",
                            "submitted_at": 1_700_000_000}, kimodo.KimodoConnection())
        self.controller.populate_jobs()
        self.controller.update_project_summary()
        expected = self.controller._format_submitted_time(1_700_000_000)
        self.assertEqual(expected, self.view.jobs.item(0, 1).text())
        self.assertIn("Generation", self.view.project_summary.text())
        self.assertIn("Jobs", self.view.project_summary.text())
        for key in ("generate", "summary_generate", "open_folder"):
            self.assertIn("#b0b0b0", self.view.buttons[key].styleSheet())
            self.assertNotIn("#375957", self.view.buttons[key].styleSheet())

    def test_humanik_tab_is_source_only(self):
        """Target controls, actions, and persistent state are no longer part of this tool."""
        from gt.ui import resource_library as resources

        self.assertFalse(hasattr(self.model, "humanik_target"))
        self.assertFalse(any("target" in key for key in self.view.buttons))
        for field in ("hik_target_character", "hik_target_namespace", "hik_target_rig", "hik_target_properties"):
            self.assertFalse(hasattr(self.view, field))
        for key in ("hik_export_pose", "hik_export_source", "hik_apply_pose", "hik_import_source"):
            self.assertIn(key, self.view.buttons)
            self.assertFalse(self.view.buttons[key].icon().isNull())
        self.assertTrue(resources.Icon.rigger_action_export_grayscale.endswith("_grayscale.svg"))
        self.assertTrue(resources.Icon.rigger_action_import_grayscale.endswith("_grayscale.svg"))

    def test_table_context_copy_paste_and_job_clipboard_actions(self):
        """Provides context-appropriate clipboard actions without mixing table schemas."""
        from gt.ui.qt_import import QtCore, QtWidgets
        from gt.utils import kimodo

        context_policy = getattr(QtCore.Qt, "CustomContextMenu", None)
        if context_policy is None:
            context_policy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        for table in (self.view.prompts, self.view.constraints, self.view.jobs):
            self.assertEqual(context_policy, table.contextMenuPolicy())

        self.view.prompts.selectRow(0)
        self.controller.copy_prompt()
        self.controller.paste_prompt()
        self.assertEqual(2, len(self.model.definition["prompts"]))

        self.model.add_constraint(
            {"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]}, "Path")
        self.controller.populate_constraints()
        self.view.constraints.selectRow(0)
        self.controller.copy_constraint()
        self.controller.paste_constraint()
        self.assertEqual(2, len(self.model.constraints))
        self.controller.toggle_constraint()
        self.assertFalse(self.model.constraints[1]["enabled"])
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        self.assertEqual(int(center), self.view.constraints.item(1, 0).textAlignment())

        rotations = [[[0, 0, 0] for unused in range(22)]]
        self.model.add_constraint({"type": "fullbody", "frame_indices": [1],
                                   "local_joints_rot": rotations, "root_positions": [[0, 0, 0]]}, "Pose")
        self.controller.populate_constraints()
        self.view.constraints.selectRow(2)
        self.controller.change_constraint_type("left-hand")
        self.assertEqual("left-hand", self.model.constraints[2]["parameters"]["type"])

        job = self.model.add_job({"job_id": "a" * 32, "status": "queued"}, kimodo.KimodoConnection())
        self.controller.populate_jobs()
        self.view.jobs.selectRow(0)
        self.assertEqual(int(center), self.view.jobs.item(0, 2).textAlignment())
        self.controller.copy_job_id()
        self.assertEqual(job["job_id"], QtWidgets.QApplication.clipboard().text())

    def test_download_status_and_missing_files_refresh(self):
        """Uses local-file state in the table without changing remote success."""
        from gt.utils import kimodo

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "motion.json")
            with open(path, "w") as stream:
                stream.write("{}")
            entry = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
            entry["paths"] = {"motion.json": path, "result.json": path}
            self.controller.populate_jobs()
            self.assertEqual("Downloaded", self.view.jobs.item(0, 2).text())
            os.remove(path)
            self.controller.populate_jobs()
            self.assertEqual("Missing Files", self.view.jobs.item(0, 2).text())
            self.assertEqual("succeeded", entry["status"])

    def test_auto_download_queues_only_eligible_generations(self):
        """Avoids model jobs, active requests and repeat retries after failure."""
        from gt.utils import kimodo

        eligible = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        self.model.add_job({"job_id": "b" * 32, "status": "succeeded", "operation": "download_model"},
                           kimodo.KimodoConnection())
        self.model.add_job({"job_id": "c" * 32, "status": "succeeded", "download_error": "offline"},
                           kimodo.KimodoConnection())
        with patch.object(self.controller, "_download_job") as download:
            self.controller.poll_jobs()
            download.assert_called_once_with(eligible)
        self.assertEqual(True, self.model.auto_download)

    def test_auto_maya_defaults_persistence_and_export_callback(self):
        """Persists opt-out and records automatic scene exports without touching the open scene."""
        from gt.utils import kimodo

        self.assertEqual(True, self.view.auto_maya_file.isChecked())
        self.assertEqual(True, self.view.auto_download.isChecked())
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_maya_file.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.auto_maya_file)
        job = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        job["paths"] = {"motion.json": __file__, "result.json": __file__}
        with patch.object(self.controller, "run_network") as dispatch:
            self.view.auto_maya_file.setChecked(True)
            key, operation, callback = dispatch.call_args.args
            self.assertTrue(key.startswith("maya:"))
            self.assertEqual(True, job["exporting_maya"])
            with self.assertRaisesRegex(ValueError, "export to finish"):
                self.controller._confirm_cleanup([job])
            callback(({"motion.json": __file__}, None))
            self.assertNotIn("exporting_maya", job)
            self.assertEqual({"motion.json": __file__}, job["maya_files"])
            self.controller.poll_jobs()
            dispatch.assert_called_once()

    def test_print_server_location_and_old_bridge_warning(self):
        """Prints the actual remote path and explains when the bridge needs updating."""
        from gt.utils import kimodo

        self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        self.controller.populate_jobs()
        self.view.jobs.selectRow(0)
        with patch.object(self.controller, "run_network") as dispatch:
            self.controller.print_server_location()
            callback = dispatch.call_args.args[2]
            with patch("builtins.print") as output:
                callback({"server_directory": "/home/example/kimodo/jobs/test"})
                self.assertIn("/home/example/kimodo/jobs/test", output.call_args.args[0])
            callback({})
            self.assertEqual("warning", self.view.status.property("feedback_level"))
            self.assertIn("Restart", self.view.status.text())

    def test_failed_exports_require_manual_retry_and_missing_scenes_are_flagged(self):
        """Avoids retry loops and silent regeneration when users remove exported scenes."""
        from gt.utils import kimodo

        job = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        job["paths"] = {"motion.json": __file__, "result.json": __file__}
        with patch.object(self.controller, "run_network") as dispatch:
            self.controller.poll_jobs()
            callback = dispatch.call_args.args[2]
            callback((None, "Simulated export failure"))
            self.assertEqual("Maya Export Failed", self.view.jobs.item(0, 2).text())
            self.controller.poll_jobs()
            dispatch.assert_called_once()
            self.view.jobs.selectRow(0)
            self.controller.create_maya_files()
            callback = dispatch.call_args.args[2]
            self.assertNotIn("maya_export_error", job)
            callback(({"motion.json": "missing.ma"}, None))
            self.assertEqual("Maya Files Missing", self.view.jobs.item(0, 2).text())
            self.controller.poll_jobs()
            self.assertEqual(2, dispatch.call_count)

    def test_cleanup_success_and_failure_keep_correct_history(self):
        """No row disappears until acknowledged cleanup; errors retain retryable state."""
        from gt.utils import kimodo

        job = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        with patch.object(self.controller, "run_network") as dispatch:
            self.controller._request_cleanup([job], server=True, local=False)
            unused, operation, callback = dispatch.call_args.args
            callback({"error": "offline"})
            self.assertIn(job, self.model.jobs)
            self.assertEqual("Cleanup Failed", self.view.jobs.item(0, 2).text())
            self.controller._request_cleanup([job], server=True, local=False)
            unused, operation, callback = dispatch.call_args.args
            callback({"removed": True, "preserved": []})
            self.assertEqual([], self.model.jobs)
            self.assertEqual(0, self.view.jobs.rowCount())

    def test_cleanup_waits_for_active_cancellation(self):
        """Clear All requests cancellation rather than deleting under the running worker."""
        from gt.utils import kimodo

        job = self.model.add_job({"job_id": "a" * 32, "status": "running"}, kimodo.KimodoConnection())
        client = Mock()
        client.status.return_value = {"job_id": job["job_id"], "status": "running"}
        client.cancel.return_value = {"job_id": job["job_id"], "status": "running", "cancel_requested": True}
        with patch.object(self.controller, "_job_client", return_value=client):
            with patch.object(self.controller, "run_network") as dispatch:
                self.controller._request_cleanup([job], server=True, local=False)
                unused, operation, callback = dispatch.call_args.args
                callback(operation())
                client.cancel.assert_called_once_with(job["job_id"])
                client.delete_job.assert_not_called()
                self.assertIn(job, self.model.jobs)
                job["status"] = "cancelled"
                self.controller.poll_jobs()
                unused, operation, callback = dispatch.call_args.args
                callback(operation())
                client.delete_job.assert_called_once_with(job["job_id"])
                self.assertNotIn(job, self.model.jobs)

    def test_pose_humanik_checkbox_defaults_and_persists(self):
        """Checkbox persists immediately without needing a valid generation prompt/seed."""
        self.assertEqual(True, self.view.auto_humanik.isChecked())
        self.view.seed.setText("unfinished")
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_humanik.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.definition["maya"]["auto_humanik"])
        self.controller.load_widgets()
        self.assertEqual(False, self.view.auto_humanik.isChecked())

    def test_humanik_actions_use_current_pose_source_without_selection(self):
        """A freshly created authoring skeleton is usable by source actions without reselecting it."""
        import maya.cmds as cmds

        self.model.pose_group = "authoring:motion"
        self.controller.imported_group = "earlier_result:motion"
        with patch.object(cmds, "ls", return_value=[]):
            self.assertEqual("authoring:motion", self.controller.humanik_source())


    def test_humanik_is_independent_and_preferences_persist(self):
        """Keeps Retargeter unbound and saves HIK settings independently of generation."""
        self.assertNotIn("retarget", self.view.buttons)
        self.assertFalse(hasattr(self.controller, "retarget"))
        self.assertFalse(hasattr(self.controller, "retarget_controller"))
        self.view.seed.setText("unfinished")
        self.view.hik_name.setText("MyCharacter")
        self.view.hik_frame.setText("-5.5")
        self.view.hik_lock.setChecked(False)
        with patch.object(self.model, "save_preferences") as save:
            self.controller.save_humanik_settings()
            save.assert_called_once()
        self.assertEqual("MyCharacter", self.model.humanik["character_name"])
        self.assertEqual(-5.5, self.model.humanik["reference_frame"])
        self.assertEqual(False, self.model.humanik["lock_definition"])
        self.view.seed.setText("12345")

    def test_large_font_and_narrow_window_do_not_crop_controls(self):
        """Exercises enlarged UI text and narrow logical screen layouts."""
        from gt.ui.qt_import import QtGui, QtWidgets

        font = QtGui.QFont(self.view.font())
        font.setPointSize(15)
        self.view.setFont(font)
        self.view.resize(530, 590)
        self.app.processEvents()
        for index in range(self.view.tabs.count()):
            self.view.tabs.setCurrentIndex(index)
            self.app.processEvents()
            self.view.refresh_layout_metrics()
            self.app.processEvents()
            for button in self.view.buttons.values():
                if button.isVisible():
                    self.assertGreaterEqual(button.height(), button.fontMetrics().height() + 6)
            page = self.view.tabs.widget(index)
            scroll = page if isinstance(page, QtWidgets.QScrollArea) else page.findChild(QtWidgets.QScrollArea)
            self.assertIsNotNone(scroll)
            self.assertLessEqual(scroll.horizontalScrollBar().maximum(), 1, f"Tab {index} overflows horizontally")
        self.assertTrue(any(row.direction() == QtWidgets.QBoxLayout.Direction.TopToBottom
                            for row in self.view.responsive_rows))

    def test_screen_change_keeps_window_within_available_size(self):
        """Recomputes bounds for a smaller logical work area on another monitor."""
        from gt.ui.qt_import import QtCore

        screen = Mock()
        screen.availableGeometry.return_value = QtCore.QRect(1920, 0, 960, 540)
        self.view.resize(1200, 900)
        self.view.observe_screen(screen)
        self.app.processEvents()
        self.assertLessEqual(self.view.width(), 960)
        self.assertLessEqual(self.view.height(), 540)
        screen.logicalDotsPerInchChanged.connect.assert_called_once()
        self.view.observe_screen(None)
        screen.logicalDotsPerInchChanged.disconnect.assert_called_once()

    def test_maya_driven_view_deletion_stops_stale_polling(self):
        """Does not access deleted widgets when Maya removes a retained workspace child."""
        from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
        from gt.tools.kimodo_generator.kimodo_generator_view import KimodoGeneratorView
        from gt.tools.kimodo_generator.kimodo_generator_controller import KimodoGeneratorController
        from gt.ui.qt_import import QtCore, shiboken

        view = KimodoGeneratorView()
        controller = KimodoGeneratorController(KimodoGeneratorModel(preferences=False), view)
        self.assertTrue(controller.timer.isActive())
        view.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertFalse(shiboken.isValid(view))
        self.assertEqual(True, controller.closed)
        self.assertEqual({}, controller.pending)
        controller.poll_jobs()
        controller.close()

    def test_deleted_results_table_stops_stale_polling(self):
        """Stops safely if Maya deletes Results children before their parent view."""
        from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
        from gt.tools.kimodo_generator.kimodo_generator_view import KimodoGeneratorView
        from gt.tools.kimodo_generator.kimodo_generator_controller import KimodoGeneratorController
        from gt.ui.qt_import import QtCore, shiboken

        view = KimodoGeneratorView()
        controller = KimodoGeneratorController(KimodoGeneratorModel(preferences=False), view)
        table = view.jobs
        table.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertFalse(shiboken.isValid(table))
        controller.poll_jobs()
        self.assertEqual(True, controller.closed)
        self.assertFalse(controller.timer.isActive())
        view.close()


if __name__ == "__main__":
    unittest.main()
