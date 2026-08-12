"""Unit tests for the Batch Processor report task."""

import logging
import os
import shutil
import sys
import tempfile
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tasks import task_report


class TestBatchProcessorReport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gt_batch_processor_report_test_")
        self.task = task_report.TaskSceneReport()

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_report_task_is_registered(self):
        expected = task_report.TaskSceneReport
        result = tasks.get_task_class(constants.TaskType.SCENE_REPORT)
        self.assertEqual(expected, result)

    def test_report_task_default_settings(self):
        expected = {
            "source_mode": task_base.SOURCE_MODE_PATH,
            "include_in_task_index": False,
            "overwrite": True,
            "report_metrics": ["frame_count", "frame_rate", "file_size", "time"],
            "report_detail_mode": task_report.REPORT_DETAIL_TOTAL_ONLY,
            "report_file_name": "{project-name}_report.txt",
            "run_once_after_multi_instance": True,
            "target_path": task_report.REPORT_LOG_TARGET_PATH_TEMPLATE,
        }
        result = {key: self.task.settings.get(key) for key in expected}
        self.assertEqual(expected, result)

    def test_normalize_metric_keys_uses_registry_order(self):
        expected = ["frame_count", "file_size", "scene_units"]
        result = task_report.normalize_metric_keys(["scene_units", "file_size", "unknown_item", "frame_count"])
        self.assertEqual(expected, result)

    def test_normalize_metric_keys_expands_legacy_node_counts(self):
        expected = ["mesh_count", "joint_count", "transform_count"]
        result = task_report.normalize_metric_keys(["node_counts"])
        self.assertEqual(expected, result)

    def test_metrics_require_scene(self):
        self.assertFalse(task_report.metrics_require_scene(["file_size"]))
        self.assertTrue(task_report.metrics_require_scene(["file_size", "frame_count"]))

    def test_get_frame_rate_from_time_unit(self):
        expected = [24.0, 30.0, 23.976, 0.0]
        result = [task_report.get_frame_rate_from_time_unit(value) for value in ["film", "ntsc", "23.976fps", "bad"]]
        self.assertEqual(expected, result)

    def test_aggregate_entries_sums_and_collects_distinct_values(self):
        entries = [
            {"path": "a.ma", "values": {"frame_count": 10, "frame_rate": 24.0}, "errors": []},
            {"path": "b.ma", "values": {"frame_count": 5, "frame_rate": 30.0}, "errors": []},
            {"path": "c.ma", "values": {"frame_count": 5, "frame_rate": 24.0}, "errors": []},
        ]

        totals = task_report.aggregate_entries(entries, ["frame_count", "frame_rate"])

        expected = [("Total Frames", 20), ("Frame Rates", [24.0, 30.0])]
        result = [(total.get("label"), total.get("value")) for total in totals]
        self.assertEqual(expected, result)

    def test_aggregate_entries_ignores_missing_values(self):
        entries = [
            {"path": "a.ma", "values": {"file_size_bytes": 100}, "errors": []},
            {"path": "b.ma", "values": {"file_size_bytes": None}, "errors": []},
        ]

        totals = task_report.aggregate_entries(entries, ["file_size"])

        expected = 100
        self.assertEqual(expected, totals[0].get("value"))

    def test_build_report_lines_total_only_omits_file_list(self):
        self.task.settings["report_metrics"] = ["frame_count"]
        entries = [{"path": "a.ma", "values": {"frame_count": 12}, "errors": []}]

        report_lines = task_report.build_report_lines(self.task.build_report_data(entries))

        self.assertIn("Total Frames: 12", report_lines)
        self.assertNotIn("Files", [line.strip() for line in report_lines if line.strip() == "Files"])

    def test_build_report_lines_list_and_total_includes_file_list(self):
        self.task.settings["report_metrics"] = ["frame_count"]
        self.task.settings["report_detail_mode"] = task_report.REPORT_DETAIL_LIST_AND_TOTAL
        entries = [{"path": "a.ma", "values": {"frame_count": 12}, "errors": []}]

        report_lines = task_report.build_report_lines(self.task.build_report_data(entries))

        self.assertIn("Files", report_lines)
        self.assertIn("1. a.ma", report_lines)
        self.assertIn("    Frames: 12", report_lines)

    def test_build_report_lines_reports_collection_errors(self):
        self.task.settings["report_metrics"] = ["frame_count"]
        self.task.settings["report_detail_mode"] = task_report.REPORT_DETAIL_LIST_AND_TOTAL
        entries = [{"path": "a.ma", "values": {}, "errors": ["Frame Count: broken scene"]}]

        report_lines = task_report.build_report_lines(self.task.build_report_data(entries))

        self.assertIn("    Error: Frame Count: broken scene", report_lines)

    def test_collect_report_entry_reads_file_size_without_maya(self):
        file_path = os.path.join(self.temp_dir, "sample.ma")
        with open(file_path, "w", encoding="utf-8") as sample_file:
            sample_file.write("12345")

        entry = task_report.collect_report_entry(file_path=file_path, metric_keys=["file_size"])

        expected = 5
        self.assertEqual(expected, entry.get("values").get("file_size_bytes"))
        self.assertEqual([], entry.get("errors"))

    def test_build_report_path_resolves_project_name(self):
        project = batch_processor_model.BatchProcessorModel()
        project.project_name = "Shot Cleanup"

        result = task_report.build_report_path(self.task, self.temp_dir, project=project)

        expected = "Shot_Cleanup_report.txt"
        self.assertEqual(expected, os.path.basename(result))

    def test_build_report_path_without_project_uses_fallback_name(self):
        result = task_report.build_report_path(self.task, self.temp_dir)

        expected = "project_report.txt"
        self.assertEqual(expected, os.path.basename(result))

    def test_build_report_path_uses_custom_file_name(self):
        self.task.settings["report_file_name"] = "shot_report"

        result = task_report.build_report_path(self.task, self.temp_dir)

        expected = "shot_report.txt"
        self.assertEqual(expected, os.path.basename(result))

    def test_get_unused_report_path_avoids_existing_files(self):
        report_path = os.path.join(self.temp_dir, "report_report.txt")
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write("previous run")

        result = task_report.get_unused_report_path(report_path)

        expected = "report_report_001.txt"
        self.assertEqual(expected, os.path.basename(result))

    def test_write_report_overwrites_when_overwrite_is_enabled(self):
        self.task.settings["report_metrics"] = ["file_size"]
        entries = [{"path": "a.ma", "values": {"file_size_bytes": 2048}, "errors": []}]

        first_path = self.task.write_report(self.temp_dir, entries, context={"item_index": 1})
        second_path = self.task.write_report(self.temp_dir, entries, context={"item_index": 1})

        self.assertEqual(first_path, second_path)
        with open(second_path, "r", encoding="utf-8") as report_file:
            report_text = report_file.read()
        self.assertIn("Total File Size: 2.00 KB", report_text)

    def test_parts_from_parallel_workers_merge_into_one_report(self):
        self.task.settings["report_metrics"] = ["file_size"]
        self.task.settings["report_detail_mode"] = task_report.REPORT_DETAIL_LIST_AND_TOTAL
        base_report_path = task_report.build_report_path(self.task, self.temp_dir)
        parts_dir = task_report.get_parts_dir(base_report_path)
        run_id = "shared_run"
        for file_name, file_size in [("a.ma", 1024), ("b.ma", 2048)]:
            entry = {"path": file_name, "values": {"file_size_bytes": file_size}, "errors": []}
            task_report.write_report_part(parts_dir, entry, run_id)

        entries = task_report.read_report_parts(parts_dir, run_id)
        report_path = self.task.write_report(self.temp_dir, entries, context={"run_id": run_id})

        expected = ["a.ma", "b.ma"]
        self.assertEqual(expected, [entry.get("path") for entry in entries])
        with open(report_path, "r", encoding="utf-8") as report_file:
            report_text = report_file.read()
        self.assertIn("Files: 2", report_text)
        self.assertIn("Total File Size: 3.00 KB", report_text)

    def test_reprocessing_a_file_replaces_its_part(self):
        parts_dir = os.path.join(self.temp_dir, "report_parts")
        run_id = "shared_run"
        task_report.write_report_part(parts_dir, {"path": "a.ma", "values": {"file_size_bytes": 1}}, run_id)
        task_report.write_report_part(parts_dir, {"path": "a.ma", "values": {"file_size_bytes": 2}}, run_id)

        entries = task_report.read_report_parts(parts_dir, run_id)

        expected = [{"path": "a.ma", "values": {"file_size_bytes": 2}, "errors": []}]
        self.assertEqual(expected, entries)

    def test_parts_from_other_runs_are_ignored_and_purged(self):
        parts_dir = os.path.join(self.temp_dir, "report_parts")
        task_report.write_report_part(parts_dir, {"path": "old.ma", "values": {}}, "previous_run")
        task_report.write_report_part(parts_dir, {"path": "new.ma", "values": {}}, "current_run")

        entries = task_report.read_report_parts(parts_dir, "current_run")
        deleted_count = task_report.purge_stale_parts(parts_dir, "current_run")

        expected = ["new.ma"]
        self.assertEqual(expected, [entry.get("path") for entry in entries])
        self.assertEqual(1, deleted_count)
        self.assertEqual(1, len(task_report.list_part_paths(parts_dir)))

    def test_workers_share_one_numbered_report_when_overwrite_is_disabled(self):
        self.task.settings["overwrite"] = False
        base_report_path = task_report.build_report_path(self.task, self.temp_dir)
        with open(base_report_path, "w", encoding="utf-8") as report_file:
            report_file.write("previous run")

        first_path = task_report.resolve_report_path(base_report_path, run_id="shared_run", overwrite=False)
        with open(first_path, "w", encoding="utf-8") as report_file:
            report_file.write("current run")
        second_path = task_report.resolve_report_path(base_report_path, run_id="shared_run", overwrite=False)

        self.assertEqual(first_path, second_path)
        self.assertNotEqual(base_report_path, first_path)

    def test_next_run_reserves_a_new_report_when_overwrite_is_disabled(self):
        base_report_path = task_report.build_report_path(self.task, self.temp_dir)
        with open(base_report_path, "w", encoding="utf-8") as report_file:
            report_file.write("previous run")

        first_run_path = task_report.resolve_report_path(base_report_path, run_id="run_one", overwrite=False)
        with open(first_run_path, "w", encoding="utf-8") as report_file:
            report_file.write("first run")
        second_run_path = task_report.resolve_report_path(base_report_path, run_id="run_two", overwrite=False)

        self.assertNotEqual(first_run_path, second_run_path)

    def test_report_lock_is_exclusive_until_released(self):
        lock_path = os.path.join(self.temp_dir, "parts", task_report.REPORT_LOCK_NAME)

        first_attempt = task_report.acquire_report_lock(lock_path, timeout_seconds=0)
        second_attempt = task_report.acquire_report_lock(lock_path, timeout_seconds=0)
        task_report.release_report_lock(lock_path)
        third_attempt = task_report.acquire_report_lock(lock_path, timeout_seconds=0)
        task_report.release_report_lock(lock_path)

        self.assertTrue(first_attempt)
        self.assertFalse(second_attempt)
        self.assertTrue(third_attempt)
        self.assertFalse(os.path.exists(lock_path))

    def test_get_run_id_falls_back_to_a_process_value(self):
        expected = task_report.FALLBACK_RUN_ID
        self.assertEqual(expected, task_report.get_run_id({}))
        self.assertEqual("worker_run", task_report.get_run_id({"run_id": "worker_run"}))

    def test_validate_warns_when_no_report_items_are_selected(self):
        self.task.settings["report_metrics"] = []

        result = self.task.validate(project=None)

        expected = 1
        self.assertEqual(expected, len(result.warnings))
        self.assertEqual([], result.errors)


if __name__ == "__main__":
    unittest.main()
