"""Nonblocking Qt checks for nested project settings and completion policies."""

import os
import sys
import tempfile
import types
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor.batch_processor_model import BatchProcessorModel
from gt.tools.batch_processor.batch_processor_tasks import TaskRunBatchProject

try:
    import gt.ui.qt_import as ui_qt
    from gt.tools.batch_processor.widgets.attr_widget_run_batch_project import AttrWidgetRunBatchProject
    from gt.tools.batch_processor.widgets.attr_widget_task import get_task_widget_class
    from gt.tools.batch_processor.tracker.tracker_controller import TrackerController
except ImportError:
    ui_qt = None


@unittest.skipIf(ui_qt is None, "Requires supported Qt bindings")
class TestBatchProjectsUi(unittest.TestCase):
    """Exercises settings binding and result-driven tracker closure."""

    @classmethod
    def setUpClass(cls):
        """Creates one application without entering its event loop."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def test_widget_registration_construction_and_binding(self):
        """Constructs the widget and binds queue eligibility and child-only overrides."""
        project = BatchProcessorModel()
        task = project.add_task(TaskRunBatchProject())
        original_workers = project.run_settings["worker_count"]
        self.assertEqual(AttrWidgetRunBatchProject, get_task_widget_class(task))
        widget = AttrWidgetRunBatchProject(task=task, project=project)
        try:
            self.assertFalse(widget.dependency_combo.isEnabled())
            for mode in ("Ordered Chain", "Groups"):
                widget.queue_combo.setCurrentText(mode)
                self.assertTrue(widget.dependency_combo.isEnabled())
            widget.queue_combo.setCurrentText("Independent")
            self.assertFalse(widget.dependency_combo.isEnabled())
            checkbox, spin = widget.override_controls["worker_count"]
            self.assertFalse(spin.isEnabled())
            checkbox.setChecked(True)
            spin.setValue(3)
            self.assertEqual(3, task.settings["worker_count"])
            self.assertEqual(original_workers, project.run_settings["worker_count"])
            self.assertNotIn("disabled_task_types", task.settings)
            self.assertNotIn("project_timeout_minutes", task.settings)
            self.assertNotIn("project_retries", task.settings)
            self.application.processEvents()
        finally:
            widget.close()
            widget.deleteLater()

    def test_close_policy_uses_saved_result(self):
        """Closes successful children and retains failed tracker windows."""
        with tempfile.TemporaryDirectory(prefix="gt_child_ui_") as root:
            result_file = os.path.join(root, "result.json")
            for outcome, policy, expected in (("succeeded", "Close On Success", True),
                                               ("failed", "Close On Success", False),
                                               ("failed", "Close When Finished", True),
                                               ("succeeded", "Keep Open", False)):
                with self.subTest(outcome=outcome, policy=policy):
                    projects.write_json(result_file, {"outcome": outcome})
                    controller = types.SimpleNamespace(
                        scheduler_timer=mock.Mock(), view=mock.Mock(), refresh=mock.Mock(),
                        log_timer=mock.Mock(), close_after_abort=False,
                        scheduler=types.SimpleNamespace(options=types.SimpleNamespace(
                            result_file=result_file, window_policy=policy)))
                    TrackerController.on_finished(controller)
                    self.assertEqual(expected, controller.view.close.called)


if __name__ == "__main__":
    unittest.main()
