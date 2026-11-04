"""Tests for handing a Batch Processor session over to another process."""

import os
import shutil
import tempfile
import unittest

from gt.tools.batch_processor import batch_processor_handoff


class TestBatchProcessorHandoff(unittest.TestCase):
    """Checks recovery and ready files survive the trip between processes."""

    def setUp(self):
        """Creates a hand-off folder."""
        self.directory = batch_processor_handoff.create_handoff_directory()
        self.addCleanup(shutil.rmtree, self.directory, True)

    def test_recovery_payload_round_trips(self):
        payload = batch_processor_handoff.build_recovery_payload(
            project_data={"tasks": [{"id": "a"}], "name": "Demo"},
            source_project_file=r"C:\Projects\Demo.batch",
            saved_state={"tasks": [], "name": "Demo"},
        )
        recovery_path = os.path.join(self.directory, batch_processor_handoff.RECOVERY_FILE_NAME)
        batch_processor_handoff.write_json_file(recovery_path, payload)
        self.assertEqual(payload, batch_processor_handoff.read_json_file(recovery_path))

    def test_untitled_project_has_an_empty_source_path(self):
        payload = batch_processor_handoff.build_recovery_payload({"tasks": []}, None, None)
        expected = ("", None)
        self.assertEqual(expected, (payload["source_project_file"], payload["saved_state"]))

    def test_missing_or_broken_files_read_as_empty(self):
        broken_path = os.path.join(self.directory, "broken.json")
        with open(broken_path, "w", encoding="utf-8") as broken_file:
            broken_file.write("{not json")
        self.assertEqual(
            ({}, {}),
            (
                batch_processor_handoff.read_json_file(os.path.join(self.directory, "missing.json")),
                batch_processor_handoff.read_json_file(broken_path),
            ),
        )

    def test_ready_file_reports_success_and_failure(self):
        ready_path = os.path.join(self.directory, batch_processor_handoff.READY_FILE_NAME)
        batch_processor_handoff.write_ready_file(ready_path)
        self.assertEqual("ready", batch_processor_handoff.read_json_file(ready_path)["status"])
        batch_processor_handoff.write_ready_file(ready_path, status="failed", error="boom")
        self.assertEqual(
            ("failed", "boom"),
            tuple(batch_processor_handoff.read_json_file(ready_path)[key] for key in ("status", "error")),
        )

    def test_empty_ready_path_is_ignored(self):
        batch_processor_handoff.write_ready_file("")
