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
        from gt.ui.qt_import import QtWidgets

        checkbox = self.view.constraints.cellWidget(0, 0).findChild(QtWidgets.QCheckBox)
        checkbox.setChecked(False)
        self.controller.gather()
        self.assertEqual([], self.model.build_definition().as_dict()["constraints"])

    def test_constraint_use_checkboxes_are_centered_in_cells(self):
        """Centers one Use checkbox per row and reads its state from the widget."""
        from gt.ui.qt_import import QtCore, QtWidgets

        for index in range(2):
            self.model.add_constraint({"type": "root2d", "frame_indices": [index],
                                       "smooth_root_2d": [[index, 0]]}, f"Path {index + 1}")
        self.controller.populate_constraints()
        self.app.processEvents()
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        self.assertTrue(self.view.constraints.horizontalHeaderItem(1).textAlignment() & center)

        for row in range(self.view.constraints.rowCount()):
            cell_item = self.view.constraints.item(row, 0)
            checkbox_cell = self.view.constraints.cellWidget(row, 0)
            checkboxes = checkbox_cell.findChildren(QtWidgets.QCheckBox)
            self.assertEqual(1, len(checkboxes))
            self.assertFalse(cell_item.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            checkbox = checkboxes[0]
            cell_center = checkbox_cell.rect().center()
            checkbox_center = checkbox.mapTo(checkbox_cell, checkbox.rect().center())
            geometry = f"cell={checkbox_cell.geometry()}, check={checkbox.geometry()}"
            self.assertAlmostEqual(cell_center.x(), checkbox_center.x(), delta=1, msg=geometry)
            self.assertAlmostEqual(cell_center.y(), checkbox_center.y(), delta=1, msg=geometry)
            frame_item = self.view.constraints.item(row, 1)
            self.assertTrue(frame_item.textAlignment() & center)
            checkbox.setChecked(False)
            self.assertIsNone(cell_item.data(QtCore.Qt.ItemDataRole.CheckStateRole))
            self.controller.gather_constraints()
            self.assertFalse(self.model.constraints[row]["enabled"])

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
        self.assertEqual(3, self.view.launch_options.count())
        self.assertFalse(self.view.auto_connect.isChecked())
        self.assertTrue(self.view.launch_options.alignment() & QtCore.Qt.AlignmentFlag.AlignCenter)
        self.assertIs(self.view.auto_connect_options, self.view.launch_options)
        self.assertTrue(self.view.auto_connect_options.alignment() & QtCore.Qt.AlignmentFlag.AlignCenter)
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

    def test_randomize_seed_button_writes_unsigned_32bit_value_next_to_seed(self):
        """Places the seed action beside its field and generates a valid Kimodo seed."""
        row = next(layout for layout in self.view.responsive_rows
                   if any(layout.itemAt(index).widget() is self.view.seed for index in range(layout.count())))
        seed_index = next(index for index in range(row.count())
                          if row.itemAt(index).widget() is self.view.seed)
        self.assertIs(row.itemAt(seed_index + 1).widget(), self.view.buttons["randomize_seed"])

        self.view.buttons["randomize_seed"].click()
        seed = int(self.view.seed.text())
        self.assertGreaterEqual(seed, 0)
        self.assertLess(seed, 2 ** 32)

    def test_sample_spinbox_maximum_is_eight(self):
        """Limits the Generate tab to eight samples."""
        self.assertEqual(8, self.view.samples.maximum())

    def test_bridge_console_preference_saves_immediately(self):
        """Persists the local launch presentation without requiring a connection attempt."""
        with patch.object(self.model, "save_preferences") as save:
            self.view.show_console.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.connection["show_console"])

    def test_auto_connect_preference_and_launch_action(self):
        """Persists opt-in auto-connect and runs the normal connect action at launch."""
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_connect.setChecked(True)
            save.assert_called_once()
        self.assertTrue(self.model.connection["auto_connect"])

        with patch.object(self.controller, "connect_bridge") as connect:
            self.controller.auto_connect_on_launch()
            connect.assert_called_once_with()
        self.view.auto_connect.setChecked(False)
        with patch.object(self.controller, "connect_bridge") as connect:
            self.controller.auto_connect_on_launch()
            connect.assert_not_called()

    def test_generation_advanced_settings_are_collapsible_and_compact(self):
        """Uses arrow disclosure for advanced controls and groups Curve samples tightly."""
        self.assertEqual("Advanced Settings", self.view.advanced.toggle_button.text())
        self.assertFalse(self.view.advanced.toggle_button.isChecked())
        self.assertTrue(self.view.advanced_content.isHidden())
        self.assertIs(self.view.advanced_content, self.view.postprocess.parentWidget())
        self.assertIs(self.view.path_curve_samples.parentWidget(), self.view.path_curve_samples_label.parentWidget())
        self.assertEqual(4, self.view.path_curve_samples_label.parentWidget().layout().spacing())

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

        for key in ("create_skeleton", "preview_pose", "capture_pose", "use_selection"):
            with self.subTest(action=key), patch.object(module.logger, "exception") as traceback:
                with patch.object(module.logger, "warning") as warning:
                    self.controller._action_callback(key)()
                    self.assertEqual("warning", self.view.status.property("feedback_level"))
                    self.assertTrue(self.view.status.text().startswith("Warning:"))
                    warning.assert_called_once()
                    traceback.assert_not_called()

    def test_open_results_folder_falls_back_to_download_folder_without_selection(self):
        """Opens the configured output directory and warns when no job is selected."""
        from gt.tools.kimodo_generator import kimodo_generator_controller as module

        with tempfile.TemporaryDirectory() as directory:
            download_folder = os.path.join(directory, "downloads")
            self.model.output_directory = download_folder
            with patch.object(module.ui_qt.QtGui.QDesktopServices, "openUrl", return_value=True) as open_url:
                self.controller.open_folder()
                self.assertTrue(os.path.isdir(download_folder))
                opened_url = open_url.call_args.args[0]
                self.assertEqual(os.path.normcase(download_folder), os.path.normcase(opened_url.toLocalFile()))
        self.assertEqual("warning", self.view.status.property("feedback_level"))
        self.assertIn("No job selected", self.view.status.text())

    def test_pose_frame_menu_uses_maya_time_and_frame_controls_stay_compact(self):
        """Keeps the Clip frame label beside its spinbox and exposes Maya-time lookup by RMB."""
        from gt.ui.qt_import import QtCore, QtWidgets

        self.assertEqual("Clip Frame: ", self.view.pose_frame_label.text())
        self.assertIs(self.view.pose_frame.parentWidget(), self.view.pose_frame_label.parentWidget())
        self.assertEqual(4, self.view.pose_frame_label.parentWidget().layout().spacing())
        self.assertEqual(QtWidgets.QSizePolicy.Policy.Maximum,
                         self.view.pose_frame.sizePolicy().horizontalPolicy())
        self.assertEqual(QtWidgets.QSizePolicy.Policy.Maximum,
                         self.view.pose_frame.parentWidget().sizePolicy().horizontalPolicy())
        self.assertTrue(self.view.template_pose_previews.isChecked())
        self.assertIn("unselectable", self.view.template_pose_previews.text())

        class CapturingMenu(QtWidgets.QMenu):
            """Captures menu contents instead of opening a modal menu."""

            def exec(self, *args, **kwargs):
                """Stores actions for assertions."""
                self.captured_actions = self.actions()

            def exec_(self, *args, **kwargs):
                """Supports the legacy Qt menu spelling."""
                self.captured_actions = self.actions()

        with patch.object(QtWidgets, "QMenu", CapturingMenu):
            self.controller.show_pose_frame_context_menu(QtCore.QPoint(0, 0))
        menu = self.view.pose_frame.findChild(CapturingMenu)
        action = next(item for item in menu.captured_actions
                      if item.text() == "Set Clip Frame to Current Maya Frame")
        self.assertFalse(action.icon().isNull())
        self.assertGreater(len(action.toolTip()), 65)

        with patch("maya.cmds.currentTime", return_value=24.6) as current_time:
            action.trigger()
        current_time.assert_called_once_with(query=True)
        self.assertEqual(25, self.view.pose_frame.value())
        self.assertIn("Maya frame 25", self.view.status.text())

    def test_pose_preview_option_saves_immediately(self):
        """Persists template-preview changes independently of generation input validation."""
        with patch.object(self.model, "save_preferences") as save:
            self.view.template_pose_previews.setChecked(False)
            save.assert_called_once()
        self.assertFalse(self.model.pose_previews_template)

    def test_preview_all_constraints_previews_poses_and_paths(self):
        """Previews every stored row, including disabled rows and root-path curves."""
        pose = {"type": "fullbody", "frame_indices": [4], "root_positions": [[0, 0, 0]],
                "local_joints_rot": [[[0, 0, 0] for unused in range(77)] ]}
        path = {"type": "root2d", "frame_indices": [0, 10], "smooth_root_2d": [[0, 0], [1, 1]]}
        pose_entry = self.model.add_constraint(pose, "Walk pose")
        path_entry = self.model.add_constraint(path, "Walk path")
        path_entry["enabled"] = False
        self.controller.populate_constraints()
        self.model.rest_motion = {"skeleton": "available"}
        with patch.object(self.controller, "_preview_pose_entry") as preview_pose, \
                patch.object(self.controller, "_create_root_path_preview") as preview_path:
            self.controller.preview_all_constraints()

        preview_pose.assert_called_once_with(pose_entry)
        preview_path.assert_called_once_with(path_entry["parameters"], "kimodo_Walk_path_frame_001", select=False)
        self.assertIn("all 2 constraints", self.view.status.text())

    def test_remove_all_constraints_requires_confirmation_and_clears_setup(self):
        """Clears all rows only after confirmation and leaves preview cleanup a separate action."""
        from gt.ui.qt_import import QtWidgets

        self.model.add_constraint({"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]})
        self.controller.populate_constraints()
        no = QtWidgets.QMessageBox.StandardButton.No
        with patch.object(QtWidgets.QMessageBox, "question", return_value=no):
            self.controller.remove_all_constraints()
        self.assertEqual(1, len(self.model.constraints))

        yes = QtWidgets.QMessageBox.StandardButton.Yes
        with patch.object(QtWidgets.QMessageBox, "question", return_value=yes):
            self.controller.remove_all_constraints()
        self.assertEqual([], self.model.constraints)
        self.assertEqual(0, self.view.constraints.rowCount())

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

        self.assertTrue(set(self.view.buttons).issubset(ACTION_TOOLTIPS))
        for name in CONTROL_TOOLTIPS:
            self.assertGreater(len(getattr(self.view, name).toolTip()), 65, name)
        for button in self.view.buttons.values():
            self.assertGreater(len(button.toolTip()), 65)

    def test_constraints_toolbar_only_keeps_actions_outside_the_context_menu(self):
        """Keeps common non-menu actions visible and moves the remaining work to RMB."""
        from gt.tools.kimodo_generator.kimodo_generator_help import ACTION_TOOLTIPS

        removed = ("remove_all_constraints", "duplicate_constraint", "preview_pose", "remove_constraint",
                   "import_constraints", "export_constraints")
        for key in removed:
            self.assertNotIn(key, self.view.buttons)
            self.assertIn(key, ACTION_TOOLTIPS)
        for key in ("preview_all_constraints", "remove_pose_previews", "capture_pose", "capture_path"):
            self.assertIn(key, self.view.buttons)

    def test_results_categories_prioritize_normal_workflow(self):
        """Uses arrow disclosure sections for automation and recovery actions."""
        from gt.ui.qt_import import QtCore, QtWidgets

        self.assertFalse(self.view.results_automation_toggle.isChecked())
        self.assertTrue(self.view.results_automation_content.isHidden())
        self.assertEqual(QtCore.Qt.ArrowType.RightArrow, self.view.results_automation_toggle.arrowType())
        self.assertEqual("Automatic Processing", self.view.results_automation_toggle.text())
        self.assertFalse(self.view.results_manual_toggle.isChecked())
        self.assertTrue(self.view.results_manual_content.isHidden())
        self.assertEqual(QtCore.Qt.ArrowType.RightArrow, self.view.results_manual_toggle.arrowType())
        self.assertEqual("Recovery And Job Management", self.view.results_manual_toggle.text())
        self.assertIs(self.view.results_manual_content,
                      self.view.buttons["download_results"].parentWidget())
        self.assertIs(self.view.results_manual_content,
                      self.view.buttons["clear_history"].parentWidget())
        self.assertIs(self.view.results_manual_content,
                      self.view.buttons["print_server_location"].parentWidget())
        self.assertIs(self.view.results_manual_content,
                      self.view.buttons["delete_server_files"].parentWidget())
        self.assertIs(self.view.results_selected,
                      self.view.buttons["open_folder"].parentWidget())
        self.assertIs(self.view.results_automation_content, self.view.namespace.parentWidget())
        self.assertIs(self.view.results_automation_content, self.view.start_frame.parentWidget())
        results_layout = self.view.results_jobs.parentWidget().layout()
        self.assertLess(results_layout.indexOf(self.view.results_jobs),
                        results_layout.indexOf(self.view.results_automation))
        self.assertLess(results_layout.indexOf(self.view.results_automation),
                        results_layout.indexOf(self.view.results_manual))
        self.assertEqual("Reset to Package Cache", self.view.buttons["use_cache"].text())
        self.assertEqual("Reset to Default Setup", self.view.buttons["load_default_setup"].text())
        self.assertEqual(0, self.view.auto_humanik.geometry().y() - self.view.template_pose_previews.geometry().y())
        self.assertEqual(0, self.view.auto_humanik.geometry().y() -
                         self.view.limit_body_joint_translations.geometry().y())
        title_layout = self.view.heading_label.parentWidget().layout().itemAt(0).layout()
        self.assertEqual(["Load Setup", "Save Setup", "Reset to Default Setup"],
                         [title_layout.itemAt(index).widget().text()
                          for index in range(1, title_layout.count())])
        self.assertTrue(self.view.auto_frame_rate.isEnabled())
        self.assertTrue(self.view.auto_frame_range.isEnabled())
        self.assertFalse(any("Each row is one server request" in widget.text()
                             for widget in self.view.findChildren(QtWidgets.QLabel)))
        self.assertIn("Transforms", self.view.buttons["capture_path"].text())
        self.assertIn("font-weight: bold", self.view.buttons["open_folder"].styleSheet())
        self.view.results_automation_toggle.setChecked(True)
        self.assertFalse(self.view.results_automation_content.isHidden())
        self.assertEqual(QtCore.Qt.ArrowType.DownArrow, self.view.results_automation_toggle.arrowType())

    def test_auto_import_timing_options_follow_the_auto_import_checkbox(self):
        """Enables dependent timing controls only when automatic import is active."""
        self.view.auto_import_maya.setChecked(True)
        self.assertTrue(self.view.auto_import_all_samples.isEnabled())
        self.assertTrue(self.view.auto_clear_scene.isEnabled())
        self.assertTrue(self.view.auto_frame_rate.isEnabled())
        self.assertTrue(self.view.auto_frame_range.isEnabled())
        self.view.auto_import_maya.setChecked(False)
        self.assertFalse(self.view.auto_import_all_samples.isEnabled())
        self.assertFalse(self.view.auto_clear_scene.isEnabled())
        self.assertFalse(self.view.auto_frame_rate.isEnabled())
        self.assertFalse(self.view.auto_frame_range.isEnabled())

    def test_prompt_frames_convert_using_selected_model_fps(self):
        """Accepts whole frame counts and keeps stored/API durations in seconds across model switches."""
        model_id = self.model.definition["model"]
        self.model.capabilities = {"models": [{"id": model_id, "name": "24 FPS", "fps": 24}]}
        self.controller.populate_models()
        self.view.prompt_frames.setChecked(True)
        self.assertEqual("Frames", self.view.prompts.horizontalHeaderItem(0).text())
        self.assertEqual("96", self.view.prompts.item(0, 0).text())

        self.view.prompts.item(0, 0).setText("48")
        self.controller.gather_prompts()
        self.assertAlmostEqual(2.0, self.model.definition["prompts"][0]["duration_seconds"])
        self.view.model.addItem("30 FPS", "test_30_fps")
        self.view.model.setCurrentIndex(self.view.model.findData("test_30_fps"))
        self.assertEqual("60", self.view.prompts.item(0, 0).text())
        self.assertAlmostEqual(2.0, self.model.build_definition().as_dict()["prompts"][0]["duration_seconds"])

        self.view.prompts.item(0, 0).setText("1.5")
        with self.assertRaisesRegex(ValueError, "whole numbers"):
            self.controller.gather_prompts()

    def test_results_constraint_and_prompt_cells_are_centered_and_iconized(self):
        """Centers the requested table values and adds an icon to each supported constraint type."""
        from gt.ui.qt_import import QtCore
        from gt.utils import kimodo

        self.model.add_constraint({"type": "root2d", "frame_indices": [0, 29],
                                   "smooth_root_2d": [[0, 0], [1, 2]]}, "Path")
        self.controller.populate_constraints()
        type_item = self.view.constraints.item(0, 2)
        self.assertFalse(type_item.icon().isNull())
        self.assertEqual("Root Path", type_item.text())
        self.assertTrue(type_item.textAlignment() & QtCore.Qt.AlignmentFlag.AlignCenter)
        self.assertTrue(self.view.prompts.item(0, 0).textAlignment() & QtCore.Qt.AlignmentFlag.AlignCenter)

        self.model.add_job({"job_id": "a" * 32, "status": "succeeded", "submitted_at": 1700000000},
                           kimodo.KimodoConnection())
        self.controller.populate_jobs()
        for column in (0, 1):
            with self.subTest(column=column):
                self.assertTrue(self.view.jobs.item(0, column).textAlignment() & QtCore.Qt.AlignmentFlag.AlignCenter)

    def test_load_default_setup_preserves_connection_and_history(self):
        """Resets generation project state without changing its bridge, credentials, or job history."""
        from gt.ui.qt_import import QtWidgets
        from gt.utils import kimodo

        self.model.connection["url"] = "http://127.0.0.1:9001"
        self.model.token = "session-only-token"
        self.model.definition["prompts"][0]["text"] = "Custom prompt"
        self.model.path_curve_samples = 7
        self.model.pose_previews_template = False
        self.model.add_constraint({"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]})
        self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        with patch.object(QtWidgets.QMessageBox, "question",
                          return_value=QtWidgets.QMessageBox.StandardButton.Yes):
            self.controller.load_default_setup()

        self.assertEqual("http://127.0.0.1:9001", self.model.connection["url"])
        self.assertEqual("session-only-token", self.model.token)
        self.assertEqual("http://127.0.0.1:9001", self.view.url.text())
        self.assertEqual(1, len(self.model.jobs))
        self.assertEqual([], self.model.constraints)
        self.assertEqual(4, self.model.path_curve_samples)
        self.assertTrue(self.model.pose_previews_template)
        self.assertTrue(self.model.auto_import_all_samples)
        self.assertEqual("A person walks forward and comes to a stop.", self.model.definition["prompts"][0]["text"])

    def test_delete_server_files_keeps_job_history_and_local_paths(self):
        """Deletes remote terminal jobs only, retaining local history and downloaded paths."""
        from unittest.mock import Mock
        from gt.ui.qt_import import QtWidgets
        from gt.utils import kimodo

        finished = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        finished["paths"] = {"motion.json": os.path.abspath(__file__)}
        active = self.model.add_job({"job_id": "b" * 32, "status": "running"}, kimodo.KimodoConnection())
        remote_client = Mock()
        remote_client.delete_job.return_value = {"deleted": True}
        with patch.object(QtWidgets.QMessageBox, "question",
                          return_value=QtWidgets.QMessageBox.StandardButton.Yes), \
                patch.object(self.controller, "_job_client", return_value=remote_client), \
                patch.object(self.controller, "run_network") as dispatch:
            self.controller.delete_server_files()
            _, operation, callback = dispatch.call_args.args
            callback(operation())

        remote_client.delete_job.assert_called_once_with("a" * 32)
        self.assertEqual(2, len(self.model.jobs))
        self.assertTrue(finished["server_missing"])
        self.assertEqual({"motion.json": os.path.abspath(__file__)}, finished["paths"])
        self.assertNotIn("server_missing", active)

    def test_root_path_preview_menu_has_a_grayscale_icon_and_creates_curve(self):
        """Adds an enabled root-path-only menu action and previews data as a Maya curve."""
        import maya.cmds as cmds
        import maya.api.OpenMaya as om
        from gt.ui.qt_import import QtCore, QtWidgets

        self.model.add_constraint({"type": "root2d", "frame_indices": [0, 10],
                                   "smooth_root_2d": [[0, 0], [1, 2]]}, "Path")
        self.controller.populate_constraints()
        self.view.constraints.selectRow(0)

        class CapturingMenu(QtWidgets.QMenu):
            """Captures actions without displaying the menu."""

            def exec(self, *args, **kwargs):
                """Stores actions for assertions."""
                self.captured_actions = self.actions()

            def exec_(self, *args, **kwargs):
                """Supports the legacy Qt menu spelling."""
                self.captured_actions = self.actions()

        with patch.object(QtWidgets, "QMenu", CapturingMenu):
            self.controller.show_table_context_menu(
                "constraints", self.view.constraints, QtCore.QPoint(0, 0))
        menu = self.view.constraints.findChild(CapturingMenu)
        action = next(item for item in menu.captured_actions if item.text() == "Preview Root Path")
        self.assertTrue(action.isEnabled())
        self.assertFalse(action.icon().isNull())
        self.assertGreater(len(action.toolTip()), 65)

        units_per_meter = 1.0 / om.MDistance(1, om.MDistance.uiUnit()).asMeters()
        with patch("maya.cmds.select"):
            curve = self.controller.preview_root_path()
        try:
            shapes = cmds.listRelatives(curve, shapes=True, fullPath=True) or []
            self.assertTrue(shapes)
            self.assertEqual("nurbsCurve", cmds.nodeType(shapes[0]))
            position = cmds.pointPosition(f"{curve}.cv[1]", world=True)
            if cmds.upAxis(query=True, axis=True) == "y":
                expected_position = (units_per_meter, 0.0, 2 * units_per_meter)
            else:
                expected_position = (units_per_meter, -2 * units_per_meter, 0.0)
            for actual, expected in zip(position, expected_position):
                self.assertAlmostEqual(expected, actual, places=3)
        finally:
            if cmds.objExists(curve):
                cmds.delete(curve)

    def test_constraint_menu_places_file_actions_before_edit_actions_and_remove_last(self):
        """Puts JSON transfer above row editing and leaves removal at the end."""
        from gt.ui.qt_import import QtCore, QtWidgets

        class CapturingMenu(QtWidgets.QMenu):
            """Captures menu contents instead of opening a modal context menu."""

            def exec(self, *args, **kwargs):
                """Stores the built actions.

                Args:
                    *args: Ignored menu position arguments.
                    **kwargs: Ignored menu options.
                """
                self.captured_actions = self.actions()

            def exec_(self, *args, **kwargs):
                """Stores the built actions for Maya's legacy Qt alias.

                Args:
                    *args: Ignored menu position arguments.
                    **kwargs: Ignored menu options.
                """
                self.captured_actions = self.actions()

        with patch.object(QtWidgets, "QMenu", CapturingMenu):
            self.controller.show_table_context_menu("constraints", self.view.constraints, QtCore.QPoint(0, 0))
        menu = self.view.constraints.findChild(CapturingMenu)
        self.assertIsNotNone(menu)
        labels = [action.text() for action in menu.captured_actions if action.text()]
        self.assertLess(labels.index("Load Constraints JSON"), labels.index("Duplicate Constraint"))
        self.assertLess(labels.index("Save Constraints JSON"), labels.index("Duplicate Constraint"))
        self.assertLess(labels.index("Remove All Constraints"), labels.index("Remove Constraint"))
        self.assertEqual("Remove Constraint", labels[-1])
        for action in menu.captured_actions:
            if action.text() in ("Load Constraints JSON", "Save Constraints JSON", "Remove All Constraints",
                                 "Remove Constraint"):
                self.assertFalse(action.icon().isNull(), action.text())

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
            self.assertEqual(True, bool(table.property("gt_columns_fitted")),
                             f"{table.property('gt_table_name')}: rows={table.rowCount()}, "
                             f"user_widths={table.property('gt_user_widths')}, "
                             f"prefs={self.model.table_widths}")
            for column in range(table.columnCount() - 1):
                self.assertEqual(QtWidgets.QHeaderView.ResizeMode.Interactive,
                                 header.sectionResizeMode(column))
                self.assertGreaterEqual(table.columnWidth(column),
                                        table.fontMetrics().horizontalAdvance(
                                            table.horizontalHeaderItem(column).text())
                                        + table.fontMetrics().horizontalAdvance("  "))
            expected_mode = (QtWidgets.QHeaderView.ResizeMode.Stretch
                             if table.property("gt_table_name") in ("constraints", "jobs")
                             else QtWidgets.QHeaderView.ResizeMode.Interactive)
            self.assertEqual(expected_mode, header.sectionResizeMode(table.columnCount() - 1))
        self.assertIn("QTableWidget::item", self.view.styleSheet())

    def test_table_widths_save_and_restore_without_dpi_refitting(self):
        """Keeps fixed user columns and fits Results/constraint labels to the viewport."""
        from gt.ui.qt_import import QtWidgets

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
        self.assertEqual(expected[:-1], [table.columnWidth(index) for index in range(table.columnCount() - 1)])
        self.assertEqual(QtWidgets.QHeaderView.ResizeMode.Stretch,
                         table.horizontalHeader().sectionResizeMode(table.columnCount() - 1))
        self.model.add_constraint({"type": "root2d", "frame_indices": [0],
                                   "smooth_root_2d": [[0, 0]]}, "A very long constraint name " * 20)
        self.controller.populate_constraints()
        self.controller.fit_constraints_table_width()
        self.app.processEvents()
        self.assertEqual(QtWidgets.QHeaderView.ResizeMode.Stretch,
                         self.view.constraints.horizontalHeader().sectionResizeMode(3))
        self.assertEqual(0, self.view.constraints.horizontalScrollBar().maximum())

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
        """Persists automation choices and imports after the isolated export callback completes."""
        from gt.utils import kimodo

        self.assertEqual(True, self.view.auto_maya_file.isChecked())
        self.assertEqual(True, self.view.auto_download.isChecked())
        self.assertEqual(True, self.view.auto_import_maya.isChecked())
        self.assertEqual(True, self.view.auto_import_all_samples.isChecked())
        self.assertEqual(True, self.view.auto_clear_scene.isChecked())
        self.assertTrue(self.view.auto_clear_scene.isEnabled())
        self.assertTrue(self.view.auto_frame_rate.isChecked())
        self.assertTrue(self.view.auto_frame_range.isChecked())
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_maya_file.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.auto_maya_file)
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_import_all_samples.setChecked(False)
            self.assertFalse(self.model.auto_import_all_samples)
            self.view.auto_import_all_samples.setChecked(True)
            self.assertTrue(self.model.auto_import_all_samples)
            self.assertEqual(2, save.call_count)
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_import_maya.setChecked(False)
            self.assertFalse(self.view.auto_clear_scene.isEnabled())
            self.view.auto_import_maya.setChecked(True)
            self.assertTrue(self.view.auto_clear_scene.isEnabled())
            self.view.auto_clear_scene.setChecked(False)
            self.view.auto_clear_scene.setChecked(True)
            self.assertEqual(4, save.call_count)
        self.assertEqual((True, True), (self.model.auto_import_maya, self.model.auto_clear_scene))
        job = self.model.add_job({"job_id": "a" * 32, "status": "succeeded"}, kimodo.KimodoConnection())
        job["paths"] = {"motion.json": __file__, "result.json": __file__}
        with patch.object(self.controller, "run_network") as dispatch:
            self.view.auto_maya_file.setChecked(True)
            key, operation, callback = dispatch.call_args.args
            self.assertTrue(key.startswith("maya:"))
            self.assertEqual(True, job["exporting_maya"])
            with self.assertRaisesRegex(ValueError, "export to finish"):
                self.controller._confirm_cleanup([job])
            with patch.object(self.controller, "import_generated_maya_file") as import_file:
                callback(({"motion.json": __file__}, None))
                import_file.assert_called_once_with(job, automatic=True)
            self.assertNotIn("exporting_maya", job)
            self.assertEqual({"motion.json": __file__}, job["maya_files"])
            self.controller.poll_jobs()
            dispatch.assert_called_once()

    def test_manual_maya_file_import_does_not_clear_the_open_scene(self):
        """Imports a generated Maya file directly while reserving forced scene clear for automation."""
        from unittest.mock import call

        with tempfile.NamedTemporaryFile(suffix=".ma") as generated_scene:
            job = {"maya_files": {"motion.json": generated_scene.name}}
            self.model.auto_clear_scene = True
            with patch("maya.cmds.file") as maya_file, patch("maya.cmds.viewFit") as view_fit:
                imported = self.controller.import_generated_maya_file(job)
            self.assertEqual(os.path.abspath(generated_scene.name), imported)
            self.assertEqual([call(imported, i=True, type="mayaAscii", ignoreVersion=True,
                                   mergeNamespacesOnClash=False)], maya_file.call_args_list)
            view_fit.assert_not_called()
            self.assertEqual(imported, job["maya_imported"])
            with patch("maya.cmds.file") as maya_file, patch("maya.cmds.viewFit") as view_fit:
                self.controller.import_generated_maya_file(job, automatic=True)
            self.assertEqual([call(new=True, force=True),
                              call(imported, i=True, type="mayaAscii", ignoreVersion=True,
                                   mergeNamespacesOnClash=False)], maya_file.call_args_list)
            view_fit.assert_called_once_with(all=True)

    def test_auto_import_all_samples_uses_one_scene_and_distinct_namespaces(self):
        """Clears at most once and imports every alternative into the shared Maya scene."""
        from unittest.mock import call

        with tempfile.TemporaryDirectory() as directory:
            maya_files = {}
            for sample_name in ("motion.json", "sample_1.json", "sample_2.json"):
                path = os.path.join(directory, sample_name.replace(".json", ".ma"))
                with open(path, "w", encoding="utf-8") as maya_file:
                    maya_file.write("// Generated Maya scene placeholder")
                maya_files[sample_name] = path
            job = {"maya_files": maya_files}
            self.model.auto_clear_scene = True
            self.model.auto_frame_rate = False
            self.model.auto_frame_range = False

            with patch("maya.cmds.file") as maya_file, patch("maya.cmds.viewFit") as view_fit, \
                    patch.object(self.controller, "_namespace",
                                 side_effect=["kimodo_motion", "kimodo_sample_1", "kimodo_sample_2"]), \
                    patch.object(self.controller, "populate_jobs"):
                imported = self.controller.import_generated_maya_file(job, automatic=True)

        self.assertEqual(os.path.abspath(maya_files["motion.json"]), imported)
        self.assertEqual([
            call(new=True, force=True),
            call(os.path.abspath(maya_files["motion.json"]), i=True, type="mayaAscii", ignoreVersion=True,
                 mergeNamespacesOnClash=False, namespace="kimodo_motion"),
            call(os.path.abspath(maya_files["sample_1.json"]), i=True, type="mayaAscii", ignoreVersion=True,
                 mergeNamespacesOnClash=False, namespace="kimodo_sample_1"),
            call(os.path.abspath(maya_files["sample_2.json"]), i=True, type="mayaAscii", ignoreVersion=True,
                 mergeNamespacesOnClash=False, namespace="kimodo_sample_2"),
        ], maya_file.call_args_list)
        view_fit.assert_called_once_with(all=True)
        self.assertEqual(maya_files, job["maya_imported_files"])

    def test_automatic_import_matches_generated_rate_and_frame_range(self):
        """Uses downloaded clip metadata for scene time unit and playback range adjustments."""
        from gt.core import io
        from gt.utils import kimodo

        self.model.auto_clear_scene = False
        with tempfile.TemporaryDirectory() as directory:
            scene_path = os.path.join(directory, "motion.ma")
            motion_path = os.path.join(directory, "motion.json")
            with open(scene_path, "w", encoding="utf-8") as scene_file:
                scene_file.write("// generated scene placeholder")
            with open(motion_path, "w", encoding="utf-8") as motion_file:
                motion_file.write("{}")
            job = {"maya_files": {"motion.json": scene_path},
                   "paths": {"motion.json": motion_path}}

            with patch.object(self.controller, "selected_job", return_value=job), \
                    patch.object(self.controller, "populate_jobs"), \
                    patch.object(io, "read_json_dict", return_value={"fps": 24.0, "frame_count": 48}), \
                    patch.object(kimodo, "validate_motion"), \
                    patch("maya.cmds.file"), patch("maya.cmds.currentUnit") as set_time_unit, \
                    patch("maya.cmds.playbackOptions") as set_playback:
                self.controller.import_generated_maya_file(job, automatic=True)

            set_time_unit.assert_called_once_with(time="24fps", updateAnimation=False)
            set_playback.assert_called_once_with(minTime=1, maxTime=48,
                                                 animationStartTime=1, animationEndTime=48)

    def test_empty_path_frames_spread_selected_transforms_over_generated_clip(self):
        """Uses prompt duration and model FPS to space selected path points across the clip."""
        from gt.utils import kimodo

        selected = ["|path_start", "|path_middle", "|path_end"]
        self.view.path_frames.clear()
        self.view.prompts.item(0, 0).setText("2")
        self.model.capabilities = {"models": [{"id": self.model.definition["model"], "fps": 24}]}
        captured = {"type": "root2d", "frame_indices": [0, 24, 47],
                    "smooth_root_2d": [[0, 0], [1, 0], [2, 0]]}
        with patch("maya.cmds.ls", return_value=selected), \
                patch("maya.cmds.nodeType", return_value="transform"), \
                patch.object(kimodo, "capture_root_path", return_value=captured) as capture:
            self.controller.capture_path()
        capture.assert_called_once_with(selected, [0, 24, 47], None,
                                        heading_mode="none", heading_offset=0.0, sample_times=None)
        self.assertIn("evenly across the generated clip", self.view.status.text())

    def test_empty_path_frames_sample_curve_across_generated_clip(self):
        """Samples a selected NURBS curve at arc-length intervals across the full clip."""
        from gt.utils import kimodo

        selected = ["|path_curve"]
        self.view.path_frames.clear()
        self.view.prompts.item(0, 0).setText("2")
        self.model.capabilities = {"models": [{"id": self.model.definition["model"], "fps": 24}]}
        captured = {"type": "root2d", "frame_indices": [0, 16, 31, 47],
                    "smooth_root_2d": [[0, 0], [1, 0], [2, 0], [3, 0]]}
        with patch("maya.cmds.ls", return_value=selected), \
                patch("maya.cmds.nodeType", side_effect=["transform", "nurbsCurve"]), \
                patch("maya.cmds.listRelatives", return_value=["|path_curve|path_curveShape"]), \
                patch.object(kimodo, "capture_root_path", return_value=captured) as capture:
            self.controller.capture_path()
        capture.assert_called_once_with(selected, [0, 16, 31, 47], None,
                                        heading_mode="none", heading_offset=0.0, sample_times=None)
        self.assertIn("4 curve samples", self.view.status.text())

    def test_curve_sample_count_is_user_configurable_and_disabled_for_explicit_frames(self):
        """Uses the requested automatic curve count only while the frame field is blank."""
        from gt.utils import kimodo

        self.view.path_frames.setText("1, 20")
        self.assertFalse(self.view.path_curve_samples.isEnabled())
        self.view.path_frames.clear()
        self.assertTrue(self.view.path_curve_samples.isEnabled())
        self.view.path_curve_samples.setValue(6)
        self.view.prompts.item(0, 0).setText("2")
        self.model.capabilities = {"models": [{"id": self.model.definition["model"], "fps": 24}]}
        captured = {"type": "root2d", "frame_indices": [0, 9, 19, 28, 38, 47],
                    "smooth_root_2d": [[index, 0] for index in range(6)]}
        with patch("maya.cmds.ls", return_value=["|path_curve"]), \
                patch("maya.cmds.nodeType", side_effect=["transform", "nurbsCurve"]), \
                patch("maya.cmds.listRelatives", return_value=["|path_curve|path_curveShape"]), \
                patch.object(kimodo, "capture_root_path", return_value=captured) as capture:
            self.controller.capture_path()
        capture.assert_called_once_with(["|path_curve"], [0, 9, 19, 28, 38, 47], None,
                                        heading_mode="none", heading_offset=0.0, sample_times=None)
        self.assertIn("6 curve samples", self.view.status.text())

    def test_generation_rejects_constraint_frames_outside_clip_before_submission(self):
        """Reports an out-of-range key locally rather than creating a doomed server job."""
        from gt.utils import kimodo

        self.view.prompts.item(0, 0).setText("1")
        self.model.add_constraint({"type": "root2d", "frame_indices": [89],
                                   "smooth_root_2d": [[0, 0]]}, "Late Path Key")
        self.controller.populate_constraints()
        with patch.object(self.controller, "run_network") as request:
            with self.assertRaisesRegex(ValueError, "Constraint frame 90.*frames 1 through 30"):
                self.controller.generate()
        request.assert_not_called()
        self.assertFalse(self.model.jobs)

    def test_maya_curve_capture_generates_root_path_points(self):
        """Exercises actual NURBS arc-length sampling and clip-bound validation in Maya."""
        import maya.cmds as cmds
        from gt.utils import kimodo

        curve = cmds.curve(point=[(0, 0, 0), (1, 0, 1), (2, 0, -1), (3, 0, 0)], degree=3)
        try:
            result = kimodo.capture_root_path([curve], [0, 15, 29])
            kimodo.validate_constraints([result], frame_count=30)
            self.assertEqual([0, 15, 29], result["frame_indices"])
            self.assertEqual(3, len(result["smooth_root_2d"]))
        finally:
            if cmds.objExists(curve):
                cmds.delete(curve)

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
        """Pose-skeleton options persist immediately without valid generation inputs."""
        self.assertEqual(True, self.view.auto_humanik.isChecked())
        self.assertEqual(True, self.view.limit_body_joint_translations.isChecked())
        self.view.seed.setText("unfinished")
        with patch.object(self.model, "save_preferences") as save:
            self.view.auto_humanik.setChecked(False)
            save.assert_called_once()
        self.assertEqual(False, self.model.definition["maya"]["auto_humanik"])
        self.assertEqual(True, self.model.definition["maya"]["limit_body_joint_translations"])
        with patch.object(self.model, "save_preferences") as save:
            self.view.limit_body_joint_translations.setChecked(False)
            save.assert_called_once()
        self.assertFalse(self.model.definition["maya"]["limit_body_joint_translations"])
        self.controller.load_widgets()
        self.assertEqual(False, self.view.auto_humanik.isChecked())
        self.assertFalse(self.view.limit_body_joint_translations.isChecked())

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
