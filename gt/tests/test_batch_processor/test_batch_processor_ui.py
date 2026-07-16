"""Qt regression tests for the Batch Processor user interface."""

import os
import sys
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
from gt.tools.batch_processor import batch_processor_view
from gt.tools.batch_processor.widgets import attr_widget_task


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


if __name__ == "__main__":
    unittest.main()
