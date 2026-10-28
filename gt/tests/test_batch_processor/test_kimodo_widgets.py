"""Non-blocking Qt construction and binding tests for Kimodo task panels."""

import unittest
from unittest import mock
import os
from gt.ui import qt_import as qt
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition
from gt.tools.batch_processor.tasks.task_kimodo_generate import TaskKimodoGenerate
from gt.tools.batch_processor.widgets.attr_widget_kimodo import AttrWidgetKimodoDefinition, AttrWidgetKimodoGenerate


class TestKimodoWidgets(unittest.TestCase):
    """Constructs both panels and verifies nested model edits without scene operations."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application without entering the event loop."""
        cls.application = qt.QtWidgets.QApplication.instance() or qt.QtWidgets.QApplication([])
        font_path = os.path.join(os.environ.get("WINDIR", ""), "Fonts", "segoeui.ttf")
        if os.path.isfile(font_path):
            font_id = qt.QtGui.QFontDatabase.addApplicationFont(font_path)
            families = qt.QtGui.QFontDatabase.applicationFontFamilies(font_id)
            if families:
                cls.application.setFont(qt.QtGui.QFont(families[0], 10))

    def setUp(self):
        """Isolates connection tests from the user's saved generator preferences."""
        from gt.tools.batch_processor.tasks import task_kimodo_connection as connections

        patcher = mock.patch.object(connections, "generator_settings", return_value={
            "connection": {"url": "http://127.0.0.1:7861"}, "docker": {"directory": "", "executable": ""}})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_definition_widget(self):
        """Edits capture and generation values and validates parameter ranges."""
        task = TaskKimodoDefinition()
        project = batch_processor_model.BatchProcessorModel()
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            widget.controls[("pose_source",)].setText("kimodo_pose:motion")
            widget.controls[("definition", "parameters", "num_samples")].setValue(3)
            self.assertEqual("kimodo_pose:motion", task.settings["pose_source"])
            self.assertEqual(3, task.settings["definition"]["parameters"]["num_samples"])
            self.assertIn(("use_pre_generation_scene_for_generation",), widget.controls)
            self.assertIn(("capture_in_world_space",), widget.controls)
            enabled, minimum, maximum, unused_integer = widget.variation_editor.inputs["guidance_text"]
            enabled.setChecked(True)
            minimum.setValue(3)
            self.assertTrue(task.validate(project).errors)
            minimum.setValue(1)
            maximum.setValue(3)
            self.assertEqual([], task.validate(project).errors)
            self.assertFalse(widget.modify_checkbox.isEnabled())
        finally:
            widget.close()
            widget.deleteLater()

    def test_generation_widget(self):
        """Keeps optional HumanIK frames typed and bridge credentials out of settings."""
        task = TaskKimodoGenerate()
        widget = AttrWidgetKimodoGenerate(task=task, project=batch_processor_model.BatchProcessorModel())
        try:
            frame = widget.controls[("humanik", "reference_frame")]
            frame.setText("0")
            self.assertEqual(0, task.settings["humanik"]["reference_frame"])
            frame.setText("")
            self.assertIsNone(task.settings["humanik"]["reference_frame"])
            widget.controls[("connection", "url")].setText("http://localhost:7861")
            self.assertEqual("http://localhost:7861", task.settings["connection"]["url"])
            self.assertNotIn("token", task.settings["connection"])
            self.assertIn("Output", widget.sections)
            self.assertNotIn("Output Naming", widget.sections)
            import_scene = widget.controls[("import_incoming_scene",)]
            self.assertFalse(import_scene.isChecked())
            import_scene.setChecked(True)
            self.assertTrue(task.settings["import_incoming_scene"])
            mode = widget.controls[("result_mode",)]
            mode.setCurrentIndex(mode.findData("artifacts"))
            self.assertFalse(import_scene.isEnabled())
            self.assertTrue(task.settings["import_incoming_scene"])
            mode.setCurrentIndex(mode.findData("maya"))
            self.assertTrue(import_scene.isEnabled())
            restored = TaskKimodoGenerate.from_dict(task.to_dict())
            self.assertTrue(restored.settings["import_incoming_scene"])
        finally:
            widget.close()
            widget.deleteLater()

    def test_docker_controls_and_numpy_dependencies(self):
        """Enables deployment references only for Docker and Maya options only for scenes."""
        task = TaskKimodoGenerate()
        widget = AttrWidgetKimodoGenerate(task=task, project=batch_processor_model.BatchProcessorModel())
        try:
            controls = widget.controls
            mode = controls[("connection", "mode")]
            mode.setCurrentIndex(mode.findData("docker"))
            self.assertTrue(controls[("docker", "directory")].isEnabled())
            self.assertTrue(controls[("docker", "executable")].isEnabled())
            for key in ("python_path", "distribution", "device", "start_encoder", "text_encoder_url"):
                self.assertFalse(controls[("connection", key)].isEnabled())
            self.assertFalse(controls[("token_environment",)].isEnabled())
            result = controls[("result_mode",)]
            result.setCurrentIndex(result.findData("numpy"))
            for key in ("output_extension", "namespace", "import_start_frame", "add_humanik",
                        "import_incoming_scene", "include_definition_attribute"):
                self.assertFalse(controls[(key,)].isEnabled())
            self.assertTrue(controls[("expected_model_fps",)].isEnabled())
            mode.setCurrentIndex(mode.findData("existing"))
            self.assertTrue(controls[("docker", "directory")].isEnabled())
            self.assertFalse(controls[("startup_timeout",)].isEnabled())
            restored = TaskKimodoGenerate.from_dict(task.to_dict())
            self.assertEqual("numpy", restored.settings["result_mode"])
        finally:
            widget.close()
            widget.deleteLater()

    def test_credential_controls_follow_source_and_managed_docker(self):
        """Makes local file credentials and explicit remote variables visibly distinct."""
        task = TaskKimodoGenerate()
        widget = AttrWidgetKimodoGenerate(task=task, project=batch_processor_model.BatchProcessorModel())
        try:
            controls = widget.controls
            credentials = controls[("authentication",)]
            mode = controls[("connection", "mode")]
            self.assertEqual("auto", credentials.currentData())
            self.assertTrue(controls[("docker", "directory")].isEnabled())
            self.assertFalse(controls[("token_environment",)].isEnabled())
            credentials.setCurrentIndex(credentials.findData("environment"))
            self.assertTrue(controls[("token_environment",)].isEnabled())
            self.assertFalse(controls[("docker", "directory")].isEnabled())
            self.assertIn("before launching Maya", widget.authentication_note.text())
            mode.setCurrentIndex(mode.findData("docker"))
            self.assertEqual("auto", credentials.currentData())
            self.assertFalse(credentials.isEnabled())
            self.assertFalse(controls[("token_environment",)].isEnabled())
            self.assertIn("secrets/bridge_token", widget.authentication_note.text())
            mode.setCurrentIndex(mode.findData("existing"))
            self.assertEqual("environment", credentials.currentData())
            credentials.setCurrentIndex(credentials.findData("none"))
            self.assertFalse(controls[("token_environment",)].isEnabled())
            self.assertFalse(controls[("docker", "directory")].isEnabled())
            self.assertIn("legacy", widget.authentication_note.text())
        finally:
            widget.close()
            widget.deleteLater()

    def test_copy_generator_connection_selects_automatic_credentials(self):
        """Copies references instead of requiring a new environment-variable export."""
        from gt.tools.batch_processor.tasks import task_kimodo_connection as connections

        task = TaskKimodoGenerate()
        task.settings.update(authentication="environment", token_environment="STALE_VARIABLE")
        widget = AttrWidgetKimodoGenerate(task=task, project=batch_processor_model.BatchProcessorModel())
        saved = {"connection": {"url": "http://127.0.0.1:7861", "mode": "existing"},
                 "docker": {"directory": "Z:/Docker/example", "executable": ""}}
        try:
            with mock.patch.object(connections, "generator_settings", return_value=saved):
                widget.use_generator_connection()
            self.assertEqual("auto", task.settings["authentication"])
            self.assertEqual("Z:/Docker/example", task.settings["docker"]["directory"])
            self.assertFalse(widget.controls[("token_environment",)].isEnabled())
            self.assertNotIn("token", task.settings["connection"])
        finally:
            widget.close()
            widget.deleteLater()

    def test_get_models_queries_downstream_docker_and_selects_current_metadata(self):
        """Discovers future model IDs and their FPS from the generating task's endpoint."""
        from gt.tools.batch_processor.widgets import kimodo_connection_controls as queries
        from gt.tools.kimodo_generator import kimodo_generator_docker as docker

        project = batch_processor_model.BatchProcessorModel()
        task = TaskKimodoDefinition()
        generate = TaskKimodoGenerate()
        generate.settings["connection"]["mode"] = "docker"
        generate.settings["docker"]["directory"] = "Z:/Docker/prepared"
        project.tasks = [task, generate]
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            with mock.patch.object(docker, "read_deployment", return_value={}), \
                    mock.patch.object(queries.connections, "validate_deployment_endpoint"), \
                    mock.patch.object(docker, "bridge_token", return_value="private-token"), \
                    mock.patch.object(qt.QtCore.QThreadPool.globalInstance(), "start"):
                widget.get_models()
            self.assertFalse(widget.get_models_button.isEnabled())
            worker = widget._query_worker
            self.assertEqual("private-token", worker.connection.token)
            self.assertNotIn("token", generate.settings["connection"])
            client = mock.Mock()
            client.capabilities.return_value = {"models": [{"id": "future-motion-model", "fps": 60}]}
            with mock.patch.object(queries.kimodo, "KimodoClient", return_value=client), \
                    mock.patch.object(docker, "_verify_identity"):
                worker.run()
            self.assertTrue(widget.get_models_button.isEnabled())
            widget.models_menu.actions()[0].trigger()
            self.assertEqual("future-motion-model", task.settings["definition"]["model"])
            self.assertEqual(60, task.settings["model_fps"])
            widget.controls[("template_path",)].setText("template.json")
            self.assertFalse(widget.get_models_button.isEnabled())
        finally:
            widget.close()
            widget.deleteLater()

    def test_read_only_query_failure_restores_button(self):
        """Reports connectivity errors without launching containers or leaving controls locked."""
        from gt.tools.batch_processor.widgets import kimodo_connection_controls as queries

        widget = AttrWidgetKimodoGenerate(task=TaskKimodoGenerate(),
                                         project=batch_processor_model.BatchProcessorModel())
        try:
            with mock.patch.object(qt.QtCore.QThreadPool.globalInstance(), "start"):
                widget.test_connection()
            self.assertFalse(widget.test_connection_button.isEnabled())
            with mock.patch.object(queries.kimodo.KimodoClient, "health", side_effect=ConnectionError("offline")):
                widget._query_worker.run()
            self.assertTrue(widget.test_connection_button.isEnabled())
            self.assertIn("offline", widget.status.text())
        finally:
            widget.close()
            widget.deleteLater()

    def test_motion_text_mode_preserves_table_and_template_dependencies(self):
        """Shows the active text source and retains rows while toggling modes and templates."""
        task = TaskKimodoDefinition(settings={"use_input_string": True})
        project = batch_processor_model.BatchProcessorModel()
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            controls = widget.controls
            mode = controls[("prompt_mode",)]
            text = controls[("prompt_text",)]
            self.assertEqual("table", mode.currentData())
            self.assertFalse(text.isEnabled())
            self.assertTrue(widget.prompt_editor.isEnabled())
            self.assertEqual(1.0, widget.prompt_editor.table_opacity.opacity())
            self.assertNotIn(("use_input_string",), controls)
            original = widget.prompt_editor.table.item(0, 1).text()
            mode.setCurrentIndex(mode.findData("text"))
            self.assertTrue(text.isEnabled())
            self.assertFalse(widget.prompt_editor.isEnabled())
            self.assertEqual(0.4, widget.prompt_editor.table_opacity.opacity())
            self.assertIn("Text", widget.motion_source_status.text())
            self.assertTrue(controls[("definition", "parameters", "transition_frames")].isEnabled())
            text.setText('[[2, "Walk"], [1, "Stop"]]')
            self.assertEqual([], task.validate(project).errors)
            self.assertEqual(original, widget.prompt_editor.table.item(0, 1).text())
            controls[("template_path",)].setText("{project-dir}/setup.json")
            self.assertTrue(text.isEnabled())
            self.assertFalse(controls[("definition", "parameters", "guidance", 0)].isEnabled())
            controls[("template_path",)].clear()
            restored = AttrWidgetKimodoDefinition(task=TaskKimodoDefinition.from_dict(task.to_dict()), project=project)
            try:
                self.assertEqual("text", restored.controls[("prompt_mode",)].currentData())
                self.assertEqual(text.text(), restored.controls[("prompt_text",)].text())
                self.assertFalse(restored.prompt_editor.isEnabled())
            finally:
                restored.close()
                restored.deleteLater()
            mode.setCurrentIndex(mode.findData("table"))
            self.assertTrue(widget.prompt_editor.isEnabled())
            self.assertFalse(text.isEnabled())
            self.assertEqual(1.0, widget.prompt_editor.table_opacity.opacity())
            self.assertEqual(original, widget.prompt_editor.table.item(0, 1).text())
        finally:
            widget.close()
            widget.deleteLater()

    def test_motion_table_actions_have_space_above_sampling(self):
        """Keeps a visible gap beneath the motion-description action buttons in real Qt."""
        widget = AttrWidgetKimodoDefinition(task=TaskKimodoDefinition(),
                                           project=batch_processor_model.BatchProcessorModel())
        try:
            widget.sections["Generation"]["button"].click()
            widget.resize(800, 1100)
            widget.show()
            self.application.processEvents()
            button = widget.prompt_editor.buttons["add"]
            sampling = widget.controls[("definition", "parameters", "num_samples")]
            button_bottom = button.mapTo(widget, qt.QtCore.QPoint(0, button.height())).y()
            sampling_top = sampling.mapTo(widget, qt.QtCore.QPoint(0, 0)).y()
            self.assertGreaterEqual(sampling_top - button_bottom, 12)
        finally:
            widget.close()
            widget.deleteLater()

    def test_samples_limit_and_replacement_table_round_trip(self):
        """Caps samples directly and saves numbered replacement rows through the task serializer."""
        task = TaskKimodoDefinition(settings={"variations": 2})
        project = batch_processor_model.BatchProcessorModel()
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            samples = widget.controls[("definition", "parameters", "num_samples")]
            samples.setValue(100)
            self.assertEqual(8, samples.value())
            self.assertEqual(8, task.settings["definition"]["parameters"]["num_samples"])
            samples.setValue(0)
            self.assertEqual(1, samples.value())
            editor = widget.replacement_editor
            editor.add_button.click()
            editor.table.item(0, 1).setText("walk")
            editor.table.item(0, 2).setText("run")
            editor.add_button.click()
            editor.table.item(1, 1).setText("walking")
            editor.table.item(1, 2).setText("running")
            self.assertEqual([1, 1], [rule["variation"] for rule in task.settings["prompt_replacements"]])
            self.assertEqual([], task.validate(project).errors)
            restored = AttrWidgetKimodoDefinition(task=TaskKimodoDefinition.from_dict(task.to_dict()), project=project)
            try:
                self.assertEqual("walking", restored.replacement_editor.table.item(1, 1).text())
            finally:
                restored.close()
                restored.deleteLater()
            editor.table.item(1, 0).setText("3")
            self.assertTrue(task.validate(project).errors)
            editor.remove_button.click()
            self.assertEqual([], task.validate(project).errors)
            self.assertTrue(widget.controls[("purge_coordination_on_finish",)].isChecked())
        finally:
            widget.close()
            widget.deleteLater()

    def test_inline_checkbox_spacing_and_labels(self):
        """Keeps checkbox rows compact and places a label immediately beside each text field."""
        for widget_type, task, checkbox_key, field_key, label_text, section_name in (
                (AttrWidgetKimodoDefinition, TaskKimodoDefinition(), ("use_marker",),
                 ("marker_attribute",), "Attribute", "Pose Capture"),
                (AttrWidgetKimodoGenerate, TaskKimodoGenerate(), ("connection", "start_encoder"),
                 ("connection", "text_encoder_url"), "URL", "Connection")):
            widget = widget_type(task=task, project=batch_processor_model.BatchProcessorModel())
            try:
                button = widget.sections[section_name]["button"]
                if not button.isChecked():
                    button.click()
                widget.resize(800, 900)
                widget.show()
                self.application.processEvents()
                checkbox = widget.controls[checkbox_key]
                field = widget.controls[field_key]
                label = widget.control_extras[field_key][0]
                self.assertEqual(label_text, label.text())
                self.assertLessEqual(checkbox.width(), checkbox.sizeHint().width() + 2)
                self.assertLess(label.x() - checkbox.geometry().right(), 20)
                self.assertLess(field.x() - label.geometry().right(), 20)
            finally:
                widget.close()
                widget.deleteLater()

    def test_labels_stay_compact_and_fields_explain_their_behavior(self):
        """Checks proportional layout, placeholder coverage, and both SVGs in real Qt."""
        for widget_type, task in ((AttrWidgetKimodoDefinition, TaskKimodoDefinition()),
                                  (AttrWidgetKimodoGenerate, TaskKimodoGenerate())):
            widget = widget_type(task=task, project=batch_processor_model.BatchProcessorModel())
            try:
                widget.resize(800, 900)
                widget.show()
                self.application.processEvents()
                for path, control in widget.controls.items():
                    self.assertGreater(len(control.toolTip()), 30, path)
                    if isinstance(control, (qt.QtWidgets.QLineEdit, qt.QtWidgets.QPlainTextEdit)):
                        self.assertTrue(control.placeholderText(), path)
                label_text = "Range:" if isinstance(task, TaskKimodoDefinition) else "Bridge URL:"
                label = next(label for label in widget.findChildren(qt.QtWidgets.QLabel) if label.text() == label_text)
                initial_width = label.width()
                widget.resize(1050, 900)
                self.application.processEvents()
                self.assertEqual(initial_width, label.width())
                self.assertLess(label.width(), widget.width() / 3)
                icon = qt.QtGui.QIcon(task.icon)
                self.assertFalse(icon.pixmap(64, 64).isNull())
                preview_folder = os.environ.get("GT_KIMODO_UI_PREVIEWS")
                if preview_folder:
                    os.makedirs(preview_folder, exist_ok=True)
                    widget.grab().save(os.path.join(preview_folder, f"{task.task_type}.png"))
                    icon.pixmap(128, 128).save(os.path.join(preview_folder, f"{task.task_type}_icon.png"))
                for button in widget.findChildren(qt.QtWidgets.QPushButton):
                    if button.text() in ("Pose Capture", "Generation", "Variations", "HumanIK",
                                         "Recovery and Timeouts"):
                        desired = button.text() != "Pose Capture"
                        if button.isChecked() != desired:
                            button.click()
                widget.resize(650, 900)
                self.application.processEvents()
                self.application.processEvents()
                self.assertLessEqual(widget.width(), 650)
                if isinstance(task, TaskKimodoDefinition):
                    editor = widget.replacement_editor
                    self.assertLess(editor.table.geometry().bottom(), editor.add_button.geometry().top())
                    self.assertLess(editor.geometry().bottom(), widget.variation_editor.geometry().top())
                if preview_folder:
                    widget.grab().save(os.path.join(preview_folder, f"{task.task_type}_expanded.png"))
            finally:
                widget.close()
                widget.deleteLater()

    def test_definition_dependencies_preserve_values(self):
        """Switches range, marker, and template modes without clearing inactive settings."""
        task = TaskKimodoDefinition()
        widget = AttrWidgetKimodoDefinition(task=task, project=batch_processor_model.BatchProcessorModel())
        try:
            controls = widget.controls
            self.assertFalse(controls[("start_frame",)].isEnabled())
            controls[("range_mode",)].setCurrentIndex(controls[("range_mode",)].findData("custom"))
            controls[("start_frame",)].setValue(296)
            self.assertTrue(controls[("end_frame",)].isEnabled())
            controls[("range_mode",)].setCurrentIndex(0)
            self.assertFalse(controls[("start_frame",)].isEnabled())
            self.assertEqual(296, task.settings["start_frame"])
            self.assertFalse(controls[("marker_attribute",)].isEnabled())
            controls[("use_marker",)].setChecked(True)
            self.assertTrue(controls[("marker_attribute",)].isEnabled())
            controls[("marker_mode",)].setCurrentIndex(controls[("marker_mode",)].findData("keyed"))
            self.assertFalse(controls[("sample_step",)].isEnabled())
            controls[("use_marker",)].setChecked(False)
            self.assertFalse(controls[("marker_value",)].isEnabled())
            self.assertEqual("kimodo_pose:motion.isConstraintPose", task.settings["marker_attribute"])
            controls[("template_path",)].setText("{project-dir}/setup.json")
            self.assertFalse(widget.prompt_editor.isEnabled())
            self.assertFalse(controls[("definition", "parameters", "guidance", 0)].isEnabled())
            controls[("template_path",)].clear()
            self.assertTrue(widget.prompt_editor.isEnabled())
        finally:
            widget.close()
            widget.deleteLater()

    def test_prompt_segments_and_guidance_round_trip(self):
        """Edits, reorders, validates, and reloads prompts in the existing task schema."""
        task = TaskKimodoDefinition()
        project = batch_processor_model.BatchProcessorModel()
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            editor = widget.prompt_editor
            editor.table.item(0, 1).setText("Walk to a chair.")
            self.assertFalse(editor.buttons["remove"].isEnabled())
            editor.buttons["add"].click()
            editor.table.item(1, 1).setText("Sit down and remain seated.")
            editor.table.item(1, 0).setText("3.5")
            self.assertTrue(widget.controls[("definition", "parameters", "transition_frames")].isEnabled())
            editor.buttons["up"].click()
            self.assertEqual("Sit down and remain seated.", task.settings["definition"]["prompts"][0]["text"])
            self.assertEqual(3.5, task.settings["definition"]["prompts"][0]["duration_seconds"])
            editor.buttons["down"].click()
            widget.controls[("definition", "parameters", "guidance", 0)].setValue(2.25)
            widget.controls[("definition", "parameters", "guidance", 1)].setValue(1.75)
            self.assertEqual([2.25, 1.75], task.settings["definition"]["parameters"]["guidance"])
            self.assertEqual([], task.validate(project).errors)
            editor.table.item(1, 0).setText("invalid")
            self.assertTrue(task.validate(project).errors)
            editor.table.item(1, 0).setText("3.5")
            restored = AttrWidgetKimodoDefinition(task=TaskKimodoDefinition.from_dict(task.to_dict()), project=project)
            try:
                self.assertEqual("Sit down and remain seated.", restored.prompt_editor.table.item(1, 1).text())
                self.assertEqual(2.25, restored.controls[("definition", "parameters", "guidance", 0)].value())
            finally:
                restored.close()
                restored.deleteLater()
            editor.buttons["remove"].click()
            self.assertEqual(1, len(task.settings["definition"]["prompts"]))
            self.assertFalse(widget.controls[("definition", "parameters", "transition_frames")].isEnabled())
        finally:
            widget.close()
            widget.deleteLater()

    def test_generate_dependencies_preserve_profiles(self):
        """Toggles Bridge, output, and mutually exclusive pose inputs with browse buttons included."""
        task = TaskKimodoGenerate()
        widget = AttrWidgetKimodoGenerate(task=task, project=batch_processor_model.BatchProcessorModel())
        try:
            controls = widget.controls
            self.assertFalse(controls[("connection", "python_path")].isEnabled())
            mode = controls[("connection", "mode")]
            mode.setCurrentIndex(mode.findData("wsl"))
            self.assertTrue(controls[("connection", "distribution")].isEnabled())
            self.assertTrue(controls[("startup_timeout",)].isEnabled())
            mode.setCurrentIndex(mode.findData("native"))
            self.assertFalse(controls[("connection", "distribution")].isEnabled())
            result = controls[("result_mode",)]
            result.setCurrentIndex(result.findData("artifacts"))
            self.assertFalse(controls[("namespace",)].isEnabled())
            self.assertFalse(controls[("humanik", "reference_frame")].isEnabled())
            self.assertTrue(all(not button.isEnabled()
                                for button in widget.control_extras[("humanik", "definition_path")]))
            self.assertTrue(task.settings["add_humanik"])
            result.setCurrentIndex(result.findData("maya"))
            self.assertTrue(controls[("humanik", "definition_path")].isEnabled())
            controls[("humanik", "reference_frame")].setText("0")
            self.assertFalse(controls[("humanik", "tpose_path")].isEnabled())
            controls[("humanik", "reference_frame")].clear()
            controls[("humanik", "tpose_path")].setText("{project-dir}/pose.json")
            self.assertFalse(controls[("humanik", "reference_frame")].isEnabled())
            controls[("add_humanik",)].setChecked(False)
            self.assertFalse(controls[("humanik", "lock_definition")].isEnabled())
            self.assertEqual("{project-dir}/pose.json", task.settings["humanik"]["tpose_path"])
        finally:
            widget.close()
            widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
