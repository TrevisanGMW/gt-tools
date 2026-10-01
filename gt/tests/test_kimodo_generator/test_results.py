"""Filesystem-safe result history/status tests outside Maya."""

import hashlib
import os
import tempfile
import unittest
import uuid
from gt.core.io import write_json
from gt.tools.kimodo_generator import kimodo_generator_results as results
from gt.utils import kimodo


class TestResultCleanup(unittest.TestCase):
    """Checks only files created under an owned TemporaryDirectory."""

    def setUp(self):
        """Creates one tracked download and an unrelated sibling."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.job_id = uuid.uuid4().hex
        self.directory = os.path.join(self.temporary.name, self.job_id)
        os.mkdir(self.directory)
        path = os.path.join(self.directory, "motion.json")
        payload = b"test artifact"
        with open(path, "wb") as stream:
            stream.write(payload)
        artifact = {"name": "motion.json", "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        manifest = os.path.join(self.directory, "result.json")
        write_json(manifest, {"job_id": self.job_id, "artifacts": [artifact]})
        self.job = {"job_id": self.job_id, "status": "succeeded", "artifacts": [artifact],
                    "paths": {"motion.json": path, "result.json": manifest}}

    def test_local_states_do_not_overwrite_server_status(self):
        """Downloaded and missing-file states coexist with a succeeded remote job."""
        self.assertEqual("downloaded", results.display_status(self.job))
        os.remove(self.job["paths"]["motion.json"])
        self.assertEqual("missing files", results.display_status(self.job))
        self.assertEqual("succeeded", self.job["status"])
        self.job["paths"] = {}
        self.assertEqual("ready to download", results.display_status(self.job))

    def test_stage_request_summary_includes_model_and_generation_shape(self):
        """Combines a title-cased stage with useful immutable request details."""
        self.job.update({
            "stage": "preparing_request",
            "definition": {
                "model": "kimodo-soma-rp-v1.1",
                "prompts": [{"text": "Walk", "duration_seconds": 2},
                            {"text": "Stop", "duration_seconds": 1.5}],
                "parameters": {"diffusion_steps": 100},
            },
        })
        expected = "Preparing Request · kimodo-soma-rp-v1.1 · 3.5s / 2 Segments / 100 Steps"
        self.assertEqual(expected, results.display_stage_and_request(self.job))

    def test_cleanup_preserves_added_and_edited_files(self):
        """Deletes verified metadata while retaining modified motion and user-added scene data."""
        extra = os.path.join(self.directory, "my_scene.ma")
        with open(extra, "w") as stream:
            stream.write("user scene")
        with open(self.job["paths"]["motion.json"], "ab") as stream:
            stream.write(b"edited")
        plan = results.delete_local_artifacts(self.job, dry_run=True)
        self.assertTrue(os.path.isfile(self.job["paths"]["result.json"]))
        outcome = results.delete_local_artifacts(self.job)
        self.assertEqual(plan["deleted"], outcome["deleted"])
        self.assertTrue(os.path.isfile(extra))
        self.assertTrue(os.path.isfile(self.job["paths"]["motion.json"]))
        self.assertEqual(2, len(outcome["preserved"]))

    def test_exact_job_cleanup_removes_empty_folder(self):
        """Keeps the selected parent and unrelated sibling intact."""
        sibling = os.path.join(self.temporary.name, "keep.txt")
        with open(sibling, "w") as stream:
            stream.write("keep")
        self.assertEqual(2, len(results.delete_local_artifacts(self.job)["deleted"]))
        self.assertFalse(os.path.exists(self.directory))
        self.assertTrue(os.path.isfile(sibling))
        self.assertEqual([], results.delete_local_artifacts(self.job)["deleted"])

    def test_mismatched_identity_or_unscoped_path_is_rejected(self):
        """A manifest or path mismatch cannot trigger any deletion."""
        write_json(self.job["paths"]["result.json"], {"job_id": uuid.uuid4().hex})
        with self.assertRaises(ValueError):
            results.delete_local_artifacts(self.job)
        self.assertTrue(os.path.isfile(self.job["paths"]["motion.json"]))
        self.job["paths"] = {"motion.json": os.path.join(self.temporary.name, "motion.json")}
        with self.assertRaises(ValueError):
            results.delete_local_artifacts(self.job)

    def test_links_inside_job_are_never_followed(self):
        """Refuses symlinks even if they point back inside the owned temporary tree."""
        link = os.path.join(self.directory, "link")
        try:
            os.symlink(self.temporary.name, link, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is unavailable on this Windows configuration.")
        with self.assertRaises(ValueError):
            kimodo._validate_job_directory(self.temporary.name, self.job_id)
        self.assertTrue(os.path.isfile(self.job["paths"]["motion.json"]))


if __name__ == "__main__":
    unittest.main()
