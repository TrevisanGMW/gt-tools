"""Non-blocking Qt construction and binding tests for Kimodo task panels."""

import unittest
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

    def test_definition_widget(self):
        """Edits capture and generation values and keeps invalid JSON visible to validation."""
        task = TaskKimodoDefinition()
        project = batch_processor_model.BatchProcessorModel()
        widget = AttrWidgetKimodoDefinition(task=task, project=project)
        try:
            widget.controls[("pose_source",)].setText("kimodo_pose:motion")
            widget.controls[("definition", "parameters", "num_samples")].setValue(3)
            self.assertEqual("kimodo_pose:motion", task.settings["pose_source"])
            self.assertEqual(3, task.settings["definition"]["parameters"]["num_samples"])
            widget.controls[("variation_ranges",)].setPlainText("{")
            self.assertTrue(task.validate(project).errors)
            widget.controls[("variation_ranges",)].setPlainText('{"guidance_text": [1, 3]}')
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
                    if button.text() in ("Pose Capture", "Generation", "HumanIK", "Recovery and Timeouts"):
                        desired = button.text() != "Pose Capture"
                        if button.isChecked() != desired:
                            button.click()
                widget.resize(650, 900)
                self.application.processEvents()
                self.assertLessEqual(widget.width(), 650)
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
