"""
Unit tests for the custom variable overrides of the "Settings Override" task.

Covers the pure override helpers, the run settings schedule, the scheduler and
worker hand-off, and the override editor dialog. No worker subprocess is started.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
import gt.ui.qt_import as ui_qt
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler
from gt.tools.batch_processor.tracker import tracker_worker
from gt.tools.batch_processor.widgets import settings_override_variables_dialog as dialog_module

SET = run_settings.CUSTOM_VARIABLE_SET
UNSET = run_settings.CUSTOM_VARIABLE_UNSET


def create_variable_task(rows):
    """Creates a Settings Override task with custom variable overrides enabled.

    Args:
        rows (list): Custom variable rows.

    Returns:
        TaskSettingsOverride: Configured task.
    """
    task = tasks.create_task(task_type=constants.TaskType.SETTINGS_OVERRIDE)
    task.settings["override_custom_variables"] = True
    task.settings["custom_variables"] = rows
    return task


class FakeProcess:
    """Process stand-in that never finishes."""

    pid = 4321

    def poll(self):
        """Reports the process as still running.

        Returns:
            None: Always running.
        """
        return None


class FakeProject:
    """Project stand-in exposing only custom variable access."""

    def __init__(self, definitions):
        """Initializes the fake project.

        Args:
            definitions (dict): Custom variable definitions.
        """
        self.definitions = definitions

    def get_custom_environment_variables(self):
        """Gets a copy of the definitions.

        Returns:
            dict: Definitions.
        """
        return {name: dict(definition) for name, definition in self.definitions.items()}

    def set_custom_environment_variables(self, definitions):
        """Stores definitions.

        Args:
            definitions (dict): Definitions.
        """
        self.definitions = definitions


class TestCustomVariableHelpers(unittest.TestCase):
    def test_normalize_drops_invalid_and_reserved_names_and_last_entry_wins(self):
        rows = [
            {"name": "{my-var}", "value": "first", "query": False, "action": SET},
            {"name": "{input-dir}", "value": "reserved", "query": False, "action": SET},
            {"name": "no braces", "value": "invalid", "query": False, "action": SET},
            {"name": "{my-var}", "value": "second", "query": True, "action": SET},
        ]

        actual = run_settings.normalize_custom_variable_overrides(rows)

        expected = {"my-var": {"action": SET, "value": "second", "query": True}}
        self.assertEqual(expected, actual)

    def test_merge_accumulates_per_name_and_unset_wins_when_later(self):
        first = {"a": {"action": SET, "value": "1", "query": False}, "b": {"action": SET, "value": "x", "query": False}}
        second = {"a": {"action": UNSET}, "c": {"action": SET, "value": "3", "query": False}}

        actual = run_settings.merge_overrides({"custom_variables": first}, {"custom_variables": second})

        expected = {
            "custom_variables": {
                "a": {"action": UNSET},
                "b": {"action": SET, "value": "x", "query": False},
                "c": {"action": SET, "value": "3", "query": False},
            }
        }
        self.assertEqual(expected, actual)

    def test_apply_sets_modifies_and_unsets_without_touching_inputs(self):
        base = {"keep": {"value": "k", "query": False}, "change": {"value": "old", "query": False},
                "drop": {"value": "d", "query": False}}
        overrides = {
            "change": {"action": SET, "value": "new", "query": True},
            "drop": {"action": UNSET},
            "added": {"action": SET, "value": "a", "query": False},
        }

        actual = run_settings.apply_custom_variable_overrides(base, overrides)

        expected = {"keep": {"value": "k", "query": False}, "change": {"value": "new", "query": True},
                    "added": {"value": "a", "query": False}}
        self.assertEqual(expected, actual)
        self.assertEqual({"value": "old", "query": False}, base["change"])
        self.assertEqual(["keep", "change", "added"], list(actual))

    def test_summary_counts_overridden_new_unchanged_and_removed(self):
        base = {"same": {"value": "s", "query": False}, "change": {"value": "old", "query": False},
                "drop": {"value": "d", "query": False}, "untouched": {"value": "u", "query": False}}
        overrides = {
            "same": {"action": SET, "value": "s", "query": False},
            "change": {"action": SET, "value": "new", "query": False},
            "drop": {"action": UNSET},
            "missing": {"action": UNSET},
            "added": {"action": SET, "value": "a", "query": False},
        }

        actual = run_settings.summarize_custom_variable_overrides(base, overrides)

        expected = {"overridden": 1, "new": 1, "removed": 1, "ignored": 1, "unchanged": 2}
        self.assertEqual(expected, actual)
        self.assertEqual(
            "1 overridden, 1 new, 2 unchanged, 1 removed, 1 unset ignored (not defined)",
            run_settings.format_custom_variable_summary(actual),
        )

    def test_task_overrides_include_variables_only_when_enabled_and_valid(self):
        task = create_variable_task([{"name": "{a}", "value": "1", "query": False, "action": SET}])
        empty_task = create_variable_task([{"name": "bad", "value": "1", "query": False, "action": SET}])
        disabled_task = create_variable_task([{"name": "{a}", "value": "1", "query": False, "action": SET}])
        disabled_task.settings["override_custom_variables"] = False

        self.assertEqual({"a": {"action": SET, "value": "1", "query": False}},
                         task.get_overrides()["custom_variables"])
        self.assertEqual({}, empty_task.get_overrides())
        self.assertEqual({}, disabled_task.get_overrides())

    def test_schedule_accumulates_variables_across_segments(self):
        first = create_variable_task([{"name": "{a}", "value": "1", "query": False, "action": SET}])
        second = create_variable_task([{"name": "{b}", "value": "2", "query": False, "action": SET}])
        rename = tasks.create_task(task_type=constants.TaskType.RENAME)
        segments = [[first, rename], [second, tasks.create_task(task_type=constants.TaskType.RENAME)]]

        schedule = run_settings.build_run_settings_schedule(segments)

        self.assertEqual({"a"}, set(schedule["segments"][0]["custom_variables"]))
        self.assertEqual({"b"}, set(schedule["segments"][1]["custom_variables"]))

    def test_state_accumulates_variable_overrides(self):
        state = run_settings.RunSettingsState()
        state.apply({"custom_variables": {"a": {"action": SET, "value": "1", "query": False}}})

        changes, _protected = state.apply({"custom_variables": {"b": {"action": UNSET}}})

        self.assertEqual({"a", "b"}, set(state.custom_variables))
        self.assertEqual(1, len(changes))
        repeated, _protected = state.apply({"custom_variables": {"b": {"action": UNSET}}})
        self.assertEqual([], repeated)

    def test_model_plan_folds_earlier_tasks_into_initial_settings(self):
        model = batch_processor_model.BatchProcessorModel()
        earlier = create_variable_task([{"name": "{a}", "value": "1", "query": False, "action": SET}])
        rename = tasks.create_task(task_type=constants.TaskType.RENAME)
        model.tasks = [tasks.TaskInput(), earlier, rename]

        plan = model.build_run_settings_plan(selected_tasks=[rename])

        self.assertEqual({"a"}, set(plan["initial"]["custom_variables"]))


class TestSchedulerCustomVariables(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="gt_custom_variable_test_")
        self.addCleanup(lambda: os.path.isdir(self.session_dir) and shutil.rmtree(self.session_dir))

    def create_scheduler(self, project, plan=None):
        """Creates a scheduler with one regular job.

        Args:
            project (FakeProject): Project stand-in.
            plan (dict, optional): Run settings plan.

        Returns:
            TrackerScheduler: Scheduler under test.
        """
        jobs = [tracker_model.TrackerJob("job-1", 1, "C:/in/1.ma", [{"id": "t1", "number": 1, "name": "Task"}])]
        session = tracker_model.TrackerSession("Test", "C:/project", 1, jobs, self.session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False, mayapy="C:/maya/mayapy.exe",
                                        project_file="C:/project/snapshot.batch", run_from_task_id="",
                                        run_to_task_id="", final_task_id=[])
        return tracker_scheduler.TrackerScheduler(session=session, options=options, project=project,
                                                  run_settings_plan=plan)

    def test_planned_overrides_change_project_and_hand_workers_a_file(self):
        project = FakeProject({"keep": {"value": "k", "query": False}, "change": {"value": "old", "query": False}})
        overrides = {"change": {"action": SET, "value": "new", "query": False},
                     "added": {"action": SET, "value": "a", "query": False}}
        plan = {"segments": [{"custom_variables": overrides}]}

        scheduler = self.create_scheduler(project, plan)
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()) as popen:
            scheduler._launch_available_jobs()

        expected_definitions = {"keep": {"value": "k", "query": False}, "change": {"value": "new", "query": False},
                                "added": {"value": "a", "query": False}}
        self.assertEqual(expected_definitions, project.definitions)
        command = popen.call_args[0][0]
        file_path = command[command.index("--custom-variables-file") + 1]
        with open(file_path, "r", encoding="utf-8") as file_object:
            self.assertEqual(overrides, json.load(file_object))

    def test_launch_without_overrides_adds_no_flag(self):
        scheduler = self.create_scheduler(FakeProject({}))
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()) as popen:
            scheduler._launch_available_jobs()

        self.assertNotIn("--custom-variables-file", popen.call_args[0][0])

    def test_overrides_always_apply_on_top_of_original_project_definitions(self):
        project = FakeProject({"a": {"value": "base", "query": False}})
        scheduler = self.create_scheduler(project)

        scheduler.update_run_settings({"custom_variables": {"a": {"action": UNSET}}})
        scheduler.update_run_settings({"custom_variables": {"a": {"action": SET, "value": "back", "query": False}}})

        self.assertEqual({"a": {"value": "back", "query": False}}, project.definitions)

    def test_worker_applies_overrides_file_to_loaded_project(self):
        model = batch_processor_model.BatchProcessorModel()
        model.set_custom_environment_variables({"{a}": {"value": "old", "query": False}})
        file_path = os.path.join(self.session_dir, "custom_variables.json")
        with open(file_path, "w", encoding="utf-8") as file_object:
            json.dump({"a": {"action": SET, "value": "new", "query": False},
                       "b": {"action": SET, "value": "added", "query": False}}, file_object)

        applied_count = tracker_worker.apply_custom_variable_overrides_file(model, file_path)

        self.assertEqual(2, applied_count)
        self.assertEqual({"a": {"value": "new", "query": False}, "b": {"value": "added", "query": False}},
                         model.get_custom_environment_variables())


class TestSettingsOverrideVariablesDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Creates a non-blocking Qt application for dialog construction."""
        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])

    def create_dialog(self, override_rows=None):
        """Creates a dialog with two existing variables.

        Args:
            override_rows (list, optional): Saved override rows.

        Returns:
            SettingsOverrideVariablesDialog: Dialog under test.
        """
        dialog = dialog_module.SettingsOverrideVariablesDialog(
            override_rows=override_rows,
            existing_variables={"path": {"value": "C:/a", "query": False}, "mode": {"value": "fast", "query": False}},
        )
        self.addCleanup(dialog.deleteLater)
        return dialog

    def get_states(self, dialog):
        """Reads the State column text of every row.

        Args:
            dialog (SettingsOverrideVariablesDialog): Dialog to read.

        Returns:
            list: State texts in row order.
        """
        return [dialog.variable_table.cellWidget(row, dialog_module.COLUMN_STATE).text()
                for row in range(dialog.variable_table.rowCount())]

    def test_state_flags_new_overriding_same_and_unset_rows(self):
        dialog = self.create_dialog()

        dialog.add_variable_row(name="{brand-new}", value="1")
        dialog.add_variable_row(name="{path}", value="C:/changed")
        dialog.add_variable_row(name="{mode}", value="fast")
        dialog.add_variable_row(name="{missing}", unset=True)
        dialog.add_variable_row(name="{path}", unset=True)

        expected = ["New variable", "Overrides existing", "Same as existing", "Not defined, no effect",
                    "Removes existing"]
        self.assertEqual(expected, self.get_states(dialog))

    def test_add_existing_prefills_value_and_blocks_duplicates(self):
        dialog = self.create_dialog()

        dialog.add_existing_variable(name="path")
        dialog.add_existing_variable(name="path")
        dialog.add_all_existing_variables()

        self.assertEqual(["path", "mode"], dialog._get_table_names())
        self.assertEqual("C:/a", dialog.variable_table.item(0, dialog_module.COLUMN_VALUE).text())

    def test_override_rows_round_trip_with_actions(self):
        saved_rows = [
            {"name": "{path}", "value": "C:/b", "query": False, "action": SET},
            {"name": "{mode}", "value": "", "query": False, "action": UNSET},
        ]
        dialog = self.create_dialog(saved_rows)

        actual = dialog.get_override_rows()

        self.assertEqual(saved_rows, actual)

    def test_invalid_name_blocks_saving_rows(self):
        dialog = self.create_dialog()
        dialog.add_variable_row(name="{input-dir}", value="reserved")

        self.assertIsNone(dialog.get_override_rows())


if __name__ == "__main__":
    unittest.main()
