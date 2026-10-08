"""Qt regression tests for the Batch Processor user interface."""

import builtins
import copy
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.resource_library as ui_res_lib


test_package_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_package_dir)
package_root_dir = os.path.dirname(tests_dir)
for path_to_append in [package_root_dir, tests_dir]:
    if path_to_append not in sys.path:
        sys.path.append(path_to_append)

from gt.tools.batch_processor import batch_processor_controller
from gt.tools.batch_processor import batch_processor_constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks
from gt.tools.batch_processor import batch_processor_view
from gt.tools.batch_processor.tasks import task_annotation
from gt.tools.batch_processor.tasks import task_batch_render
from gt.tools.batch_processor.tasks import task_clip
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.widgets import attr_widget_annotation
from gt.tools.batch_processor.widgets import attr_widget_batch_render
from gt.tools.batch_processor.widgets import attr_widget_clip
from gt.tools.batch_processor.widgets import attr_widget_delete_path
from gt.tools.batch_processor.widgets import attr_widget_export_fbx
from gt.tools.batch_processor.widgets import attr_widget_maya_import
from gt.tools.batch_processor.widgets import attr_widget_project
from gt.tools.batch_processor.widgets import attr_widget_python_script
from gt.tools.batch_processor.widgets import attr_widget_task
from gt.tools.batch_processor.widgets.custom_environment_variables_dialog import (
    CustomEnvironmentVariablesDialog,
)
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

    @unittest.skipIf(ui_qt.QtTest is None, "PySide QtTest module is unavailable.")
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

    def test_print_selected_task_index_reports_shared_participation(self):
        """Reports both task counters and one inclusion state for the selected task."""
        self.model.tasks = []
        self.model.add_task(batch_processor_tasks.TaskRename())
        self.model.add_task(batch_processor_tasks.TaskRename(settings={"force_segment_separator": True}))
        current_task = self.model.add_task(batch_processor_tasks.TaskRename())
        self.view.refresh_tree(self.model)
        self.view.select_task_by_id(current_task.id)
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller.log_status = mock.MagicMock()

        controller.print_selected_task_index()

        controller.log_status.assert_called_once_with(
            f"{current_task.display_name} Task: Project Index: 3, Task Index: 3, "
            "Index Count: Included, Segment Task Index: 2"
        )
        controller.log_status.reset_mock()
        current_task.settings["include_in_task_index"] = False
        controller.print_selected_task_index()
        controller.log_status.assert_called_once_with(
            f"{current_task.display_name} Task: Project Index: 3, Task Index: 0, "
            "Index Count: Excluded, Segment Task Index: 0"
        )

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

    def test_python_widget_enables_run_once_before_jobs(self):
        """Ensures the Python preflight checkbox persists the selected run mode."""
        python_task = self.model.add_task(batch_processor_tasks.TaskPythonScript())
        task_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=python_task,
            project=self.model,
        )
        checkbox_labels = [
            label.text() for label in task_widget.findChildren(ui_qt.QtWidgets.QLabel)
        ]
        self.assertIn("Run Once Before All Jobs:", checkbox_labels)
        self.assertIn("Run Once After All Jobs:", checkbox_labels)
        before_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if "before worker jobs start" in checkbox.toolTip()
        )

        self.assertFalse(before_checkbox.isChecked())
        before_checkbox.setChecked(True)

        self.assertTrue(python_task.settings["run_once_before_multi_instance"])
        self.assertFalse(python_task.settings["run_once_after_multi_instance"])
        self.assertTrue(python_task.is_aggregate_task)
        task_widget.deleteLater()

    def test_maya_import_segmentation_options_are_collapsed_and_persisted(self):
        """Keeps import timing and missing-folder controls inside the optional segmentation section."""
        import_task = self.model.add_task(batch_processor_tasks.TaskMayaImport())
        task_widget = attr_widget_maya_import.AttrWidgetMayaImportTask(task=import_task, project=self.model)
        self.addCleanup(task_widget.deleteLater)
        self.addCleanup(task_widget.close)
        section = task_widget.segmentation_section
        missing_checkbox = task_widget.allow_missing_input_directory_checkbox
        checkbox_row = section["checkbox_layout"]
        separator_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if "Show a labeled divider above this task" in checkbox.toolTip()
        )
        self.assertGreaterEqual(checkbox_row.indexOf(task_widget.input_directory_validation_widget), 0)
        self.assertGreaterEqual(checkbox_row.indexOf(separator_checkbox), 0)
        before_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if "before worker jobs start" in checkbox.toolTip()
        )
        after_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if "after all worker jobs finish" in checkbox.toolTip()
        )
        self.assertTrue(section["container"].isHidden())
        for checkbox in (missing_checkbox, before_checkbox, after_checkbox):
            self.assertTrue(section["container"].isAncestorOf(checkbox))
            self.assertFalse(checkbox.isChecked())
            self.assertFalse(checkbox.isVisibleTo(task_widget))
        section["button"].click()
        for checkbox in (missing_checkbox, before_checkbox, after_checkbox):
            self.assertTrue(checkbox.isVisibleTo(task_widget))
        before_checkbox.setChecked(True)
        self.assertEqual(True, import_task.settings["run_once_before_multi_instance"])
        self.assertEqual(False, import_task.settings["run_once_after_multi_instance"])
        before_checkbox.setChecked(False)
        after_checkbox.setChecked(True)
        missing_checkbox.setChecked(True)
        restored_task = batch_processor_tasks.create_task_from_dict(import_task.to_dict())
        restored_widget = attr_widget_maya_import.AttrWidgetMayaImportTask(task=restored_task, project=self.model)
        self.addCleanup(restored_widget.deleteLater)
        self.addCleanup(restored_widget.close)
        self.assertEqual(False, restored_task.settings["run_once_before_multi_instance"])
        self.assertEqual(True, restored_task.settings["run_once_after_multi_instance"])
        self.assertTrue(restored_widget.allow_missing_input_directory_checkbox.isChecked())
        self.assertFalse(restored_widget.segmentation_section["container"].isHidden())

    def test_processing_task_regular_index_controls_both_counters(self):
        """Uses one checkbox without adding a Segmentation section to ordinary tasks."""
        export_task = self.model.add_task(batch_processor_tasks.TaskExportFbx())
        refresh_parent = mock.MagicMock()
        task_widget = attr_widget_export_fbx.AttrWidgetFbxExportTask(
            task=export_task, project=self.model, refresh_parent_func=refresh_parent
        )
        self.addCleanup(task_widget.deleteLater)
        self.addCleanup(task_widget.close)
        index_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if checkbox.text() == "Index"
        )
        self.assertIsNone(task_widget.segmentation_section)
        self.assertFalse(any(
            button.text() == "Segmentation"
            for button in task_widget.findChildren(ui_qt.QtWidgets.QPushButton)
        ))
        self.assertIn("{task-idx-padded}", index_checkbox.toolTip())
        self.assertIn("{seg-task-idx-padded}", index_checkbox.toolTip())
        self.assertTrue(index_checkbox.isChecked())
        index_checkbox.setChecked(False)
        self.assertFalse(export_task.includes_segment_task_index())
        self.assertFalse(export_task.includes_task_index())
        self.assertEqual(0, self.model.get_task_environment_index(export_task))
        self.assertEqual(0, self.model.get_segment_task_environment_index(export_task))
        index_checkbox.setChecked(True)
        self.assertTrue(export_task.includes_segment_task_index())
        self.assertTrue(export_task.includes_task_index())
        refresh_parent.assert_not_called()
        self.assertTrue(ui_qt_utils.is_qt_object_valid(index_checkbox))

    def test_input_regular_index_checkbox_persists_shared_state(self):
        """Restores input participation through the regular Index checkbox."""
        widget_class = batch_processor_controller.get_task_widget_class(self.task)
        task_widget = widget_class(task=self.task, project=self.model)
        self.addCleanup(task_widget.deleteLater)
        self.addCleanup(task_widget.close)
        index_checkbox = next(
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if checkbox.text() == "Index"
        )
        self.assertFalse(index_checkbox.isChecked())
        task_widget.segmentation_section["button"].click()
        index_checkbox.setChecked(True)
        self.assertTrue(self.task.includes_task_index())
        self.assertTrue(self.task.includes_segment_task_index())
        restored_task = batch_processor_tasks.create_task_from_dict(self.task.to_dict())
        restored_widget = widget_class(task=restored_task, project=self.model)
        self.addCleanup(restored_widget.deleteLater)
        self.addCleanup(restored_widget.close)
        restored_checkbox = next(
            checkbox for checkbox in restored_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if checkbox.text() == "Index"
        )
        self.assertTrue(restored_checkbox.isChecked())
        self.assertFalse(restored_widget.segmentation_section["container"].isHidden())

    def test_specialized_segmentation_controls_share_one_section(self):
        """Keeps the existing Python segmentation controls without a second index."""
        python_task = self.model.add_task(batch_processor_tasks.TaskPythonScript())
        task_widget = attr_widget_python_script.AttrWidgetPythonScriptTask(
            task=python_task, project=self.model
        )
        self.addCleanup(task_widget.deleteLater)
        self.addCleanup(task_widget.close)
        section_buttons = [
            button for button in task_widget.findChildren(ui_qt.QtWidgets.QPushButton)
            if button.text() == "Segmentation"
        ]
        self.assertEqual(1, len(section_buttons))
        index_checkboxes = [
            checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
            if checkbox.text() == "Index"
        ]
        self.assertEqual(1, len(index_checkboxes))
        self.assertFalse(task_widget.segmentation_section["container"].isAncestorOf(index_checkboxes[0]))
        checkbox_row = task_widget.segmentation_section["checkbox_layout"]
        self.assertIs(checkbox_row, task_widget.segmentation_section["content_layout"].itemAt(0).layout())
        self.assertEqual(-1, checkbox_row.indexOf(index_checkboxes[0]))

    def test_segmentation_is_the_footer_for_all_registered_task_widgets(self):
        """Keeps actual Segmentation sections below task content and skips unnecessary sections."""
        for task_type in batch_processor_tasks.TASK_TYPES:
            with self.subTest(task_type=task_type):
                task = batch_processor_tasks.create_task(task_type)
                widget_class = batch_processor_controller.get_task_widget_class(task)
                task_widget = widget_class(task=task, project=self.model)
                try:
                    outer_layout = task_widget.scroll_content_layout
                    self.assertIs(task_widget.content_layout, outer_layout.itemAt(0).layout())
                    self.assertIs(
                        task_widget.segmentation_layout,
                        outer_layout.itemAt(outer_layout.count() - 1).layout(),
                    )
                    section = task_widget.segmentation_section
                    footer = task_widget.segmentation_layout
                    if section is None:
                        self.assertEqual(0, footer.count())
                        continue
                    self.assertEqual(2, footer.count())
                    self.assertGreaterEqual(footer.itemAt(0).layout().indexOf(section["button"]), 0)
                    self.assertIs(section["container"], footer.itemAt(1).widget())
                    self.assertEqual(-1, task_widget.content_layout.indexOf(section["container"]))
                finally:
                    task_widget.close()
                    task_widget.deleteLater()

    def test_regular_index_is_the_only_index_checkbox_for_all_tasks(self):
        """Keeps one regular Index checkbox outside any Segmentation section."""
        for task_type in batch_processor_tasks.TASK_TYPES:
            with self.subTest(task_type=task_type):
                task = batch_processor_tasks.create_task(task_type)
                widget_class = batch_processor_controller.get_task_widget_class(task)
                task_widget = widget_class(task=task, project=self.model)
                try:
                    section = task_widget.segmentation_section
                    index_checkboxes = [
                        checkbox for checkbox in task_widget.findChildren(ui_qt.QtWidgets.QCheckBox)
                        if checkbox.text() == "Index"
                    ]
                    self.assertEqual(1, len(index_checkboxes))
                    if section is not None:
                        self.assertFalse(section["container"].isAncestorOf(index_checkboxes[0]))
                    self.assertNotIn("include_in_segment_task_index", task.settings)
                finally:
                    task_widget.close()
                    task_widget.deleteLater()

    def test_segmentation_stays_below_controls_added_after_construction(self):
        """Keeps the rendered footer below controls appended by task-specific builders."""
        task_widget = attr_widget_task.AttrWidgetTask(task=self.task, project=self.model)
        self.addCleanup(task_widget.deleteLater)
        self.addCleanup(task_widget.close)
        task_widget.add_segmentation_section(
            main_label="Start New Segment",
            main_key="start_new_input_list",
            main_tooltip="Start a new input segment.",
        )
        late_field = ui_qt.QtWidgets.QLineEdit("Later task controls")
        task_widget.content_layout.addWidget(late_field)
        task_widget.segmentation_section["button"].click()
        task_widget.resize(800, 360)
        task_widget.show()
        self.application.processEvents()
        section_button = task_widget.segmentation_section["button"]
        field_bottom = late_field.mapTo(task_widget, ui_qt.QtCore.QPoint(0, 0)).y() + late_field.height()
        header_top = section_button.mapTo(task_widget, ui_qt.QtCore.QPoint(0, 0)).y()
        self.assertLessEqual(field_bottom, header_top)
        checkbox_row = task_widget.segmentation_section["checkbox_layout"]
        checkbox_widgets = [
            checkbox_row.itemAt(item_index).widget()
            for item_index in range(checkbox_row.count())
            if isinstance(checkbox_row.itemAt(item_index).widget(), ui_qt.QtWidgets.QCheckBox)
        ]
        self.assertGreater(len(checkbox_widgets), 1)
        self.assertEqual(1, len({checkbox.geometry().y() for checkbox in checkbox_widgets}))

    def test_segment_random_color_button_updates_settings_and_defers_refresh(self):
        """Ensures random colors persist and refresh safely after the button callback."""
        for separator_enabled in [False, True]:
            with self.subTest(separator_enabled=separator_enabled):
                self.task.settings["force_segment_separator"] = separator_enabled
                refresh_parent = mock.MagicMock()
                task_widget = attr_widget_task.AttrWidgetTask(
                    task=self.task,
                    project=self.model,
                    refresh_parent_func=refresh_parent,
                )
                task_widget.add_segmentation_section(
                    main_label="Start New Input List",
                    main_key="start_new_input_list",
                    main_tooltip="Start a new input segment.",
                )
                color_combo = task_widget.findChild(ui_qt.QtWidgets.QComboBox)
                randomize_button = next(
                    button for button in task_widget.findChildren(ui_qt.QtWidgets.QPushButton)
                    if button.text() == "Randomize"
                )
                color_layout = next(
                    layout for layout in task_widget.findChildren(ui_qt.QtWidgets.QHBoxLayout)
                    if layout.indexOf(randomize_button) >= 0
                )
                self.assertEqual(separator_enabled, randomize_button.isEnabled())
                self.assertEqual(color_layout.indexOf(color_combo) + 1, color_layout.indexOf(randomize_button))
                random_index = color_combo.findText("orange")
                self.assertGreaterEqual(random_index, 0)

                with mock.patch.object(
                    attr_widget_task.random, "randrange", return_value=random_index
                ) as choose_color:
                    randomize_button.click()

                refresh_parent.assert_not_called()
                if separator_enabled:
                    choose_color.assert_called_once()
                    self.assertEqual("orange", color_combo.currentText())
                    self.assertEqual("orange", self.task.settings["segment_color"])
                    self.assertTrue(ui_qt_utils.is_qt_object_valid(task_widget))
                    self.application.processEvents()
                    refresh_parent.assert_called_once_with()
                else:
                    choose_color.assert_not_called()
                    self.assertEqual("blue_light_sky", self.task.get_segment_color_name())
                task_widget.deleteLater()

    def test_randomize_segment_color_preserves_details_scroll_position(self):
        """Keeps a compressed details panel in place after the color button rebuilds it."""
        self.task.settings["force_segment_separator"] = True
        self.task.settings["segmentation_collapsed"] = False
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller.log_status = mock.MagicMock()
        self.view.controller = controller
        controller.connect_view()
        controller.refresh_widgets()
        self.view.resize(850, 330)
        self.view.show()
        self.application.processEvents()
        task_widget = self.view.get_task_widget()
        randomize_button = next(
            button for button in task_widget.findChildren(ui_qt.QtWidgets.QPushButton)
            if button.text() == "Randomize"
        )
        scroll_bar = self.view.task_attr_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        expected_position = scroll_bar.value()
        self.assertGreater(expected_position, 0)

        randomize_button.click()
        self.application.processEvents()
        self.application.processEvents()

        self.assertIsNot(task_widget, self.view.get_task_widget())
        self.assertEqual(expected_position, scroll_bar.value())

    def test_details_scroll_restore_preserves_both_axes_and_clamps_to_content(self):
        """Restores scrolling after layout and keeps smaller replacement content reachable."""
        self.view.resize(850, 330)
        self.view.show()
        initial_widget = ui_qt.QtWidgets.QWidget()
        initial_widget.setMinimumSize(1400, 1200)
        self.view.set_task_widget(initial_widget)
        self.application.processEvents()
        horizontal_bar = self.view.task_attr_area.horizontalScrollBar()
        vertical_bar = self.view.task_attr_area.verticalScrollBar()
        horizontal_position = horizontal_bar.maximum() // 2
        vertical_position = vertical_bar.maximum() // 2
        self.assertGreater(horizontal_position, 0)
        self.assertGreater(vertical_position, 0)
        horizontal_bar.setValue(horizontal_position)
        vertical_bar.setValue(vertical_position)
        replacement_widget = ui_qt.QtWidgets.QWidget()
        replacement_widget.setMinimumSize(1400, 1200)

        self.view.set_task_widget(replacement_widget, preserve_scroll=True)
        self.application.processEvents()
        self.application.processEvents()

        self.assertEqual(horizontal_position, horizontal_bar.value())
        self.assertEqual(vertical_position, vertical_bar.value())
        smaller_widget = ui_qt.QtWidgets.QWidget()
        smaller_widget.setMinimumSize(700, 500)
        self.view.set_task_widget(smaller_widget, preserve_scroll=True)
        self.application.processEvents()
        self.application.processEvents()
        self.assertEqual(min(horizontal_position, horizontal_bar.maximum()), horizontal_bar.value())
        self.assertEqual(min(vertical_position, vertical_bar.maximum()), vertical_bar.value())

    def test_details_scroll_restore_ignores_a_new_selection(self):
        """Prevents a queued restoration from scrolling another details widget."""
        self.view.resize(850, 330)
        self.view.show()
        initial_widget = ui_qt.QtWidgets.QWidget()
        initial_widget.setMinimumSize(1400, 1200)
        self.view.set_task_widget(initial_widget)
        self.application.processEvents()
        scroll_bar = self.view.task_attr_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        self.assertGreater(scroll_bar.value(), 0)
        replacement_widget = ui_qt.QtWidgets.QWidget()
        replacement_widget.setMinimumSize(1400, 1200)
        self.view.set_task_widget(replacement_widget, preserve_scroll=True)
        new_selection_widget = ui_qt.QtWidgets.QWidget()
        new_selection_widget.setMinimumSize(1400, 1200)

        self.view.set_task_widget(new_selection_widget)
        self.application.processEvents()
        self.application.processEvents()

        self.assertIs(new_selection_widget, self.view.get_task_widget())
        self.assertEqual(0, scroll_bar.value())

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

    def test_project_widget_shows_custom_environment_variable_count(self):
        """Ensures project details expose the count with state-aware styling."""
        project_widget = attr_widget_project.AttrWidgetProject(project=self.model)

        expected = "0 custom variables"
        self.assertEqual(expected, project_widget.custom_environment_variable_count_label.text())
        self.assertEqual(1, project_widget.custom_environment_variable_layout.stretch(0))
        self.assertEqual(2, project_widget.custom_environment_variable_layout.stretch(1))
        expected = ui_res_lib.Color.Hex.gray_dim
        self.assertIn(expected, project_widget.custom_environment_variable_count_label.styleSheet())

        self.model.set_custom_environment_variables(
            {
                "textures-dir": {"value": "D:/studio/textures", "query": False},
                "maya-selection": {"value": "cmds.ls(selection=True)", "query": True},
            }
        )
        project_widget.refresh_custom_environment_variable_count()

        expected = "2 custom variables"
        self.assertEqual(expected, project_widget.custom_environment_variable_count_label.text())
        expected = ui_res_lib.Color.Hex.green_pale
        self.assertIn(expected, project_widget.custom_environment_variable_count_label.styleSheet())
        project_widget.deleteLater()

    def test_custom_environment_variable_dialog_validates_variable_names(self):
        """Ensures the custom-variable editor accepts the documented name syntax."""
        dialog = CustomEnvironmentVariablesDialog(parent=self.view)
        dialog.add_variable_row(name="{textures-dir}", value="D:/studio/textures")

        expected = {"textures-dir": {"value": "D:/studio/textures", "query": False}}
        result = dialog.get_custom_environment_variables()
        self.assertEqual(expected, result)
        dialog.variable_table.item(0, 0).setText("textures-dir")
        result = dialog.get_custom_environment_variables()
        self.assertIsNone(result)
        self.assertIn("must use the pattern", dialog.status_label.text())
        dialog.deleteLater()

    def test_custom_environment_variable_dialog_exposes_examples(self):
        """Ensures the custom-variable dialog adds its local query examples."""
        dialog = CustomEnvironmentVariablesDialog(parent=self.view)
        dialog.refresh_examples_menu()
        action_labels = [action.text() for action in dialog.examples_menu.actions()]

        expected = [
            "Literal String",
            "Maya Selection",
            "Custom Attribute",
            "JSON Attribute",
        ]
        self.assertEqual(expected, action_labels)
        expected = "Examples  ▼"
        self.assertEqual(expected, dialog.examples_button.text())
        expected = "padding: 4px 8px;"
        self.assertEqual(expected, dialog.examples_button.styleSheet())
        self.assertEqual(expected, dialog.add_variable_button.styleSheet())

        for action in dialog.examples_menu.actions():
            action.trigger()

        expected = {
            "custom-path": {"value": "example/custom/path", "query": False},
            "maya-selection": {"value": "cmds.ls(selection=True)", "query": True},
            "custom-attr": {
                "value": "cmds.getAttr('object.attr')",
                "query": True,
            },
            "custom-json-attr": {
                "value": (
                    "', '.join(import_module('json').loads("
                    "cmds.getAttr('object.attr')))"
                ),
                "query": True,
            },
        }
        result = dialog.get_custom_environment_variables()
        self.assertEqual(expected, result)
        dialog.deleteLater()

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

    def test_controller_stores_custom_query_error_suppression_preference(self):
        """Ensures the editing preference updates the active project model."""
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller._prefs = mock.MagicMock()
        controller.log_status = mock.MagicMock()

        controller.toggle_suppress_custom_environment_query_errors(True)

        self.assertTrue(controller._suppress_custom_environment_query_errors)
        self.assertTrue(self.model._suppress_custom_environment_query_errors)
        controller._prefs.set_bool.assert_called_once_with(
            key=batch_processor_constants.Project.PREFS_KEY_SUPPRESS_CUSTOM_ENVIRONMENT_QUERY_ERRORS,
            value=True,
        )
        controller._prefs.save.assert_called_once()

    def test_controller_run_honors_custom_query_error_suppression(self):
        """Ensures execution retains the user's suppression preference."""
        self.model.set_custom_environment_variables(
            {
                "maya-selection": {
                    "value": "cmds.invalid_query()",
                    "query": True,
                }
            }
        )
        self.model.set_suppress_custom_environment_query_errors(True)
        self.model.run_settings["create_log"] = False
        self.model.run_settings["create_task_time_log"] = False
        self.model.run_settings["multi_instance"] = False
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller._suppress_custom_environment_query_errors = True
        controller._flag_skipped_tasks = False
        controller.create_task_time_log_file = mock.MagicMock(return_value=None)
        controller.append_log = mock.MagicMock()
        controller.log_status = mock.MagicMock()
        controller._format_tracker = mock.MagicMock(return_value="Run complete")
        tracker = mock.MagicMock(status="succeeded")
        runner = mock.MagicMock()
        observed_suppression = []

        def run_project(project, **kwargs):
            """Records the model state and evaluates the failing query.

            Args:
                project (BatchProcessorModel): Project passed to the runner.
                **kwargs: Runner options.

            Returns:
                MagicMock: Completed tracker result.
            """
            observed_suppression.append(project._suppress_custom_environment_query_errors)
            project.get_environment_variables(include_braces=True)
            return tracker

        runner.run.side_effect = run_project
        maya_module = types.ModuleType("maya")
        maya_cmds_module = types.ModuleType("maya.cmds")
        maya_module.cmds = maya_cmds_module

        with mock.patch.dict(
            sys.modules,
            {"maya": maya_module, "maya.cmds": maya_cmds_module},
        ), mock.patch.object(
            batch_processor_controller.batch_processor_worker,
            "SingleInstanceBatchRunner",
            return_value=runner,
        ), mock.patch.object(batch_processor_model.logger, "error") as mock_log_error, mock.patch.object(
            builtins, "print"
        ) as mock_print:
            controller._run_project()

        self.assertEqual([True], observed_suppression)
        self.assertTrue(self.model._suppress_custom_environment_query_errors)
        mock_log_error.assert_not_called()
        mock_print.assert_not_called()

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

    def test_event_filter_ignores_events_after_view_is_deleted(self):
        """Ensures a stale dock-view wrapper does not raise during event dispatch."""
        view = self.view
        view.deleteLater()
        self.application.sendPostedEvents(None, ui_qt.QtCore.QEvent.DeferredDelete)

        self.assertFalse(ui_qt_utils.is_qt_object_valid(view))
        event = ui_qt.QtCore.QEvent(ui_qt.QtCore.QEvent.Show)
        result = batch_processor_view.BatchProcessorView.eventFilter(view, object(), event)

        self.assertFalse(result)
        self.view = ui_qt.QtWidgets.QDialog()

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

    def test_annotation_snapshot_summary_displays_file_and_range_counts(self):
        """Ensures Annotation Snapshot displays summary counts from its JSON file."""
        snapshot_directory = tempfile.mkdtemp(prefix="gt_annotation_snapshot_ui_test_")
        self.addCleanup(shutil.rmtree, snapshot_directory)
        snapshot_path = os.path.join(snapshot_directory, "annotation_snapshot.json")
        task_annotation.update_annotation_snapshot(
            snapshot_path=snapshot_path,
            source_root=snapshot_directory,
            annotation_data_by_path={
                "walk.ma": {"file_data": {"shot": "sh010"}, "range_data": [{"name": "walk"}]},
                "run.ma": {"file_data": {}, "range_data": [{"name": "run"}, {"name": "run_end"}]},
            },
        )
        task = batch_processor_tasks.TaskAnnotationSnapshot(settings={"snapshot_path": snapshot_path})
        widget = attr_widget_annotation.AttrWidgetAnnotationSnapshotTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        files_label, _ = widget.summary_cells.get("file_count")
        ranges_label, _ = widget.summary_cells.get("range_count")

        self.assertIn("2", files_label.text())
        self.assertIn("3", ranges_label.text())
        self.assertIn(task_annotation.SNAPSHOT_STATUS_READY, widget.status_label.text())

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

    def test_batch_render_overrides_gate_their_controls(self):
        """Ensures render override checkboxes enable only the widgets they own."""
        task = batch_processor_tasks.TaskBatchRender()
        widget = attr_widget_batch_render.AttrWidgetBatchRenderTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        expected = [False, False]
        self.assertEqual(expected, [item.isEnabled() for item in widget.override_widgets["override_resolution"]])

        widget.override_checkboxes["override_resolution"].setChecked(True)

        expected = [True, True]
        self.assertEqual(expected, [item.isEnabled() for item in widget.override_widgets["override_resolution"]])

        expected = True
        self.assertEqual(expected, task.settings["override_resolution"])

        expected = [False, False, False]
        self.assertEqual(expected, [item.isEnabled() for item in widget.override_widgets["override_frame_range"]])

    def test_batch_render_project_path_requires_custom_project_mode(self):
        """Ensures the Maya project path field follows the project mode and toggle."""
        task = batch_processor_tasks.TaskBatchRender()
        widget = attr_widget_batch_render.AttrWidgetBatchRenderTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        expected = False
        self.assertEqual(expected, widget.project_path_widgets["field"].isEnabled())

        widget.set_project_mode(task_batch_render.PROJECT_MODE_CUSTOM)

        expected = True
        self.assertEqual(expected, widget.project_path_widgets["field"].isEnabled())

        widget.set_project_enabled(False)

        expected = False
        self.assertEqual(expected, widget.project_mode_combo.isEnabled())
        self.assertEqual(expected, widget.project_path_widgets["field"].isEnabled())

    def test_batch_render_prefix_tokens_are_inserted_at_the_cursor(self):
        """Ensures prefix tokens append to the field and update the task setting."""
        task = batch_processor_tasks.TaskBatchRender()
        widget = attr_widget_batch_render.AttrWidgetBatchRenderTask(task=task, project=self.model)
        self.addCleanup(widget.close)

        widget.prefix_field.setText("")
        widget.insert_prefix_token(token="<Scene>")
        widget.insert_prefix_token(token="_{name}")

        expected = "<Scene>_{name}"
        self.assertEqual(expected, widget.prefix_field.text())
        self.assertEqual(expected, task.settings["file_name_prefix"])

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

    def _build_separator_controller(self):
        """Creates a connected controller with two visible task groups.

        Returns:
            BatchProcessorController: Controller with status logging mocked.
        """
        self.task.settings["force_segment_separator"] = True
        self.task.settings["segment_name"] = "Shared Name"
        process_task = self.model.add_task_by_type(batch_processor_constants.TaskType.RENAME)
        process_task.enabled = False
        next_marker = self.model.add_task_by_type(batch_processor_constants.TaskType.RENAME)
        next_marker.settings["force_segment_separator"] = True
        next_marker.settings["segment_name"] = "Shared Name"
        controller = batch_processor_controller.BatchProcessorController.__new__(
            batch_processor_controller.BatchProcessorController
        )
        controller.model = self.model
        controller.view = self.view
        controller.log_status = mock.MagicMock()
        controller._auto_segment_imported_projects = True
        controller.apply_task_index_automation = mock.MagicMock()
        self.view.controller = controller
        controller.connect_view()
        controller.refresh_widgets()
        self.view.task_tree.setCurrentItem(self.view.project_item.child(0))
        controller.mark_project_clean()
        return controller

    def test_segment_toggle_updates_in_place_and_keeps_selection(self):
        """Disables mixed groups and reenables them without deleting the active widget."""
        controller = self._build_separator_controller()
        widget = self.view.get_task_widget()
        selected_item = self.view.task_tree.currentItem()
        initial_icon_image = widget.toggle_tasks_button.icon().pixmap(20, 20).toImage()
        self.assertFalse(widget.toggle_tasks_button.icon().isNull())

        widget.toggle_tasks_button.click()

        self.assertEqual([False, False, True], [task.enabled for task in self.model.tasks])
        self.assertEqual("Enable Tasks", widget.toggle_tasks_button.text())
        self.assertNotEqual(initial_icon_image, widget.toggle_tasks_button.icon().pixmap(20, 20).toImage())
        self.assertIs(widget, self.view.get_task_widget())
        self.assertIs(selected_item, self.view.task_tree.currentItem())
        self.assertTrue(controller.has_unsaved_changes())
        self.assertEqual("Task is disabled.", self.view.project_item.child(1).toolTip(0))

        widget.toggle_tasks_button.click()

        self.assertEqual([True, True, True], [task.enabled for task in self.model.tasks])
        self.assertEqual("Disable Tasks", widget.toggle_tasks_button.text())
        self.assertEqual(initial_icon_image, widget.toggle_tasks_button.icon().pixmap(20, 20).toImage())
        self.assertIs(widget, self.view.get_task_widget())
        self.assertEqual("", self.view.project_item.child(1).toolTip(0))

    def test_segment_buttons_have_equal_sizes_and_are_centered(self):
        """Checks button symmetry after Qt lays out the details panel."""
        self._build_separator_controller()
        self.view.show()
        self.application.processEvents()
        widget = self.view.get_task_widget()
        toggle_button = widget.toggle_tasks_button
        export_button = widget.export_segment_button

        self.assertFalse(export_button.icon().isNull())
        self.assertEqual(toggle_button.iconSize(), export_button.iconSize())
        self.assertEqual(toggle_button.size(), export_button.size())
        self.assertEqual(toggle_button.y(), export_button.y())
        button_row = toggle_button.parentWidget()
        self.assertLessEqual(abs(button_row.geometry().center().x() - widget.rect().center().x()), 1)
        self.assertLessEqual(
            abs((toggle_button.geometry().left() + export_button.geometry().right()) / 2
                - button_row.rect().center().x()),
            1,
        )

    def test_segment_export_button_uses_existing_project_import(self):
        """Round trips the group through Export Segment and Import Project."""
        controller = self._build_separator_controller()
        source_data = copy.deepcopy(self.model.to_dict())
        source_ids = [task.id for task in self.model.tasks]
        with tempfile.TemporaryDirectory() as directory:
            export_path = os.path.join(directory, "segment")
            with mock.patch.object(batch_processor_controller.ui_file_dialog, "file_dialog", return_value=export_path):
                self.view.get_task_widget().export_segment_button.click()
            exported_path = f"{export_path}.batch"
            self.assertTrue(os.path.isfile(exported_path))
            self.assertEqual(source_data, self.model.to_dict())
            self.assertIsNone(self.model.project_file_path)
            self.assertFalse(controller.has_unsaved_changes())

            self.assertTrue(controller.import_tasks_from_path(exported_path))

        self.assertEqual(5, len(self.model.tasks))
        self.assertEqual([True, False], [task.enabled for task in self.model.tasks[-2:]])
        self.assertTrue(self.model.tasks[-2].shows_segment_separator())
        self.assertEqual("Shared Name", self.model.tasks[-2].get_segment_display_name())
        self.assertTrue(all(task.id not in source_ids for task in self.model.tasks[-2:]))

    def test_segment_export_preserves_current_project_file(self):
        """Refuses to replace the active project with a segment export."""
        controller = self._build_separator_controller()
        with tempfile.TemporaryDirectory() as directory:
            project_path = self.model.save_to_file(os.path.join(directory, "project.batch"))
            with open(project_path, "rb") as project_file:
                original_contents = project_file.read()
            with mock.patch.object(
                batch_processor_controller.ui_file_dialog, "file_dialog", return_value=project_path
            ):
                self.assertFalse(controller.export_segment(self.task.id))
            with open(project_path, "rb") as project_file:
                self.assertEqual(original_contents, project_file.read())
            self.assertEqual(project_path, self.model.project_file_path)

    def test_segment_export_handles_cancel_and_write_errors(self):
        """Leaves the source untouched when export is canceled or fails."""
        controller = self._build_separator_controller()
        original_data = self.model.to_dict()
        with mock.patch.object(batch_processor_controller.ui_file_dialog, "file_dialog", return_value=""):
            self.assertFalse(controller.export_segment(self.task.id))
        with tempfile.TemporaryDirectory() as directory:
            export_path = os.path.join(directory, "segment.batch")
            with mock.patch.object(batch_processor_controller.ui_file_dialog, "file_dialog", return_value=export_path):
                with mock.patch.object(
                    batch_processor_model.BatchProcessorModel, "save_to_file", side_effect=OSError("Write failed")
                ):
                    with self.assertLogs(batch_processor_controller.logger, level="ERROR"):
                        self.assertFalse(controller.export_segment(self.task.id))
            self.assertFalse(os.path.exists(export_path))
        self.assertEqual(original_data, self.model.to_dict())

    def test_segment_export_confirms_existing_file_after_adding_extension(self):
        """Checks the actual .batch destination before replacing an existing file."""
        controller = self._build_separator_controller()
        with tempfile.TemporaryDirectory() as directory:
            entered_path = os.path.join(directory, "segment")
            target_path = f"{entered_path}.batch"
            with open(target_path, "w", encoding="utf-8") as target_file:
                target_file.write("existing data")
            with mock.patch.object(
                batch_processor_controller.ui_file_dialog, "file_dialog", return_value=entered_path
            ):
                with mock.patch.object(
                    ui_qt.QtWidgets.QMessageBox, "question", return_value=ui_qt.QtLib.StandardButton.No
                ) as question:
                    self.assertFalse(controller.export_segment(self.task.id))
                    question.assert_called_once()
                with open(target_path, "r", encoding="utf-8") as target_file:
                    self.assertEqual("existing data", target_file.read())
                with mock.patch.object(
                    ui_qt.QtWidgets.QMessageBox, "question", return_value=ui_qt.QtLib.StandardButton.Yes
                ):
                    self.assertTrue(controller.export_segment(self.task.id))
            loaded_model = batch_processor_model.BatchProcessorModel.from_file(target_path)
            self.assertEqual(2, len(loaded_model.tasks))

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
