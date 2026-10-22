"""Docker progress, Desktop log targeting, and scoped image-removal regressions."""

import json
import os
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest.mock import patch

from gt.tools.kimodo_generator import kimodo_generator_docker as docker
from gt.tools.kimodo_generator import kimodo_generator_docker_inspection as inspection
from gt.tools.kimodo_generator.docker.container_progress import EncoderProgress


class TestDockerWorkflow(unittest.TestCase):
    """Checks deployment safety without requiring an engine or downloading weights."""

    def setUp(self):
        """Creates a dedicated prepared deployment using a fake credential."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = str(Path(temporary.name) / "kimodo")
        names = patch.object(docker, "_docker_project_names", return_value=set())
        names.start()
        self.addCleanup(names.stop)
        with patch.dict(os.environ, {"HF_TOKEN": "test-hf-token"}):
            docker.prepare_deployment(self.directory)

    def test_custom_image_name_is_saved_without_renaming_existing_project(self):
        """Changes the next-build image reference while retaining deployment identity."""
        metadata = docker.read_deployment(self.directory)
        selected = docker.configure_image(self.directory, "studio.motion")
        self.assertEqual("studio.motion:1.12.0", selected)
        self.assertEqual(metadata["project_name"], docker.read_deployment(self.directory)["project_name"])
        self.assertEqual(selected, docker.configure_image(self.directory, "studio.motion"))
        self.assertIn(f"KIMODO_IMAGE={selected}", (Path(self.directory) / "configuration/.env").read_text())
        for invalid in ("", "UpperCase", "a/b", "image:tag", "../input"):
            with self.assertRaises(ValueError):
                docker.configure_image(self.directory, invalid)

    def test_dot_image_name_produces_a_valid_project_name(self):
        """Keeps Docker image repository syntax distinct from Compose project syntax."""
        other = str(Path(self.directory).parent / "other")
        metadata = docker.prepare_deployment(other, image_name="studio.motion")
        self.assertEqual("studio-motion", metadata["project_name"])
        self.assertEqual("studio.motion", metadata["image_repository"])
        self.assertEqual(metadata, docker.read_deployment(other))

    def test_logs_target_uses_exact_container_and_logs_tab(self):
        """Targets the requested service in this deployment, including stopped containers."""
        services = [{"Service": "bridge", "ID": "a" * 64}, {"Service": "text-encoder", "ID": "b" * 64}]
        with patch.object(inspection, "project_services", return_value=services):
            self.assertEqual("docker-desktop://dashboard/open",
                             inspection.logs_target(self.directory))
            self.assertEqual("docker-desktop://dashboard/open",
                             inspection.logs_target(self.directory, "bridge"))
            with self.assertRaises(ValueError):
                inspection.logs_target(self.directory, "other")

    def test_short_compose_ids_resolve_before_desktop_navigation(self):
        """Supports Compose output that truncates IDs to twelve characters."""
        services = [{"Service": "text-encoder", "ID": "a" * 12}]
        with patch.object(inspection, "project_services", return_value=services):
            with patch.object(docker, "_run", return_value="a" * 64):
                self.assertEqual("docker-desktop://dashboard/open",
                                 inspection.logs_target(self.directory))

    def test_bounded_build_tail_ignores_previous_builds(self):
        """Does not show an old success message while resolving new sources."""
        path = Path(self.directory) / "logs/build.log"
        path.write_text("Previous build succeeded\n", encoding="utf-8")
        offset = path.stat().st_size
        self.assertIn("Preparing", inspection.build_progress(self.directory, offset))
        with path.open("a", encoding="utf-8") as stream:
            stream.write("#5 [stage 3/8] installing dependencies\n")
        self.assertIn("installing dependencies", inspection.build_progress(self.directory, offset))

    def test_encoder_progress_uses_measured_bytes_and_flags_stale_reports(self):
        """Differentiates download, load, failed, and stale progress states."""
        path = Path(self.directory) / "logs/encoder-progress.json"
        data = {"stage": "downloading", "downloaded_bytes": 1024, "total_bytes": 4096,
                "updated_at": time.time()}
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(25, inspection.encoder_progress(self.directory)["percent"])
        data["updated_at"] = 0
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("stale", inspection.encoder_progress(self.directory)["detail"])
        data.update(stage="failed", updated_at=time.time())
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("failed", inspection.encoder_progress(self.directory)["stage"])

    def test_image_preview_refuses_running_or_shared_containers(self):
        """Prevents removing an image used by active or unrelated containers."""
        services = [{"ID": "a" * 64, "Name": "bridge", "Service": "bridge", "State": "running"}]
        config = json.dumps({"services": {"bridge": {"image": "kimodo-bridge:1.12.0"}}})
        with patch.object(docker, "check_engine"), patch.object(docker, "_assert_project_owner"):
            with patch.object(docker, "_compose", return_value=config):
                with patch.object(inspection, "project_services", return_value=services):
                    with self.assertRaisesRegex(ValueError, "Stop"):
                        inspection.image_removal_preview(self.directory)
                    services[0]["State"] = "exited"
                    with patch.object(docker, "_run", side_effect=[json.dumps([{"Id": "sha256:test"}]), "other-id"]):
                        with self.assertRaisesRegex(ValueError, "Another container"):
                            inspection.image_removal_preview(self.directory)

    def test_removal_revalidates_id_and_never_prunes_or_removes_volumes(self):
        """Removes only confirmed stopped services and the selected image tag."""
        preview = {"image": "kimodo-bridge:1.12.0", "image_id": "sha256:expected", "containers": []}
        with patch.object(inspection, "image_removal_preview", return_value=preview):
            with patch.object(docker, "_compose") as compose, patch.object(docker, "_run") as run:
                with self.assertRaisesRegex(ValueError, "changed"):
                    inspection.remove_image(self.directory, "sha256:other")
                compose.assert_not_called()
                run.assert_not_called()
                self.assertEqual(preview["image"], inspection.remove_image(self.directory, "sha256:expected"))
                self.assertEqual(["rm", "--force", "bridge", "text-encoder"], compose.call_args.args[1])
                self.assertEqual(["image", "rm", preview["image"]], run.call_args.args[0])
        self.assertTrue((Path(self.directory) / "secrets/hf_token").is_file())

    def test_removal_preview_matches_short_owned_ids_to_full_ancestor_ids(self):
        """Does not mistake its stopped containers for unrelated references."""
        services = [{"ID": "a" * 12, "Name": "bridge", "Service": "bridge", "State": "exited"}]
        config = json.dumps({"services": {"bridge": {"image": "kimodo-bridge:1.12.0"}}})
        with patch.object(docker, "check_engine"), patch.object(docker, "_assert_project_owner"):
            with patch.object(docker, "_compose", return_value=config):
                with patch.object(inspection, "project_services", return_value=services):
                    with patch.object(docker, "_run", side_effect=["a" * 64,
                                      json.dumps([{"Id": "sha256:test"}]), "a" * 64]):
                        preview = inspection.image_removal_preview(self.directory)
        self.assertEqual(["bridge"], preview["containers"])
        self.assertEqual("sha256:test", preview["image_id"])


class FakeProgress:
    """Minimal byte-counter interface for dependency-free progress callback tests."""

    def __init__(self, total=0, unit="B", initial=0, **kwargs):
        """Stores the provided byte-counter settings.

        Args:
            total (int): Known total bytes.
            unit (str): Progress unit.
            initial (int): Resumed byte offset.
            **kwargs: Other upstream settings.
        """
        self.total, self.unit, self.n = total, unit, initial
        self.disable = kwargs.get("disable")

    def update(self, increment=1):
        """Adds a byte delta.

        Args:
            increment (int): New bytes.
        """
        self.n += increment

    def close(self):
        """Closes a fake progress counter."""
        return None


class TestEncoderByteProgress(unittest.TestCase):
    """Validates byte totals independently of file preallocation and terminal output."""

    def test_download_callbacks_accumulate_and_loading_is_distinct(self):
        """Counts separate transfers without ID reuse or assuming cached file sizes."""
        module = types.SimpleNamespace(tqdm=FakeProgress)
        tracker = EncoderProgress()
        tracker.install(module, progress_class=FakeProgress)
        first = module.tqdm(total=8, disable=True)
        self.assertFalse(first.disable)
        first.update(8)
        first.close()
        second = module.tqdm(total=12)
        second.update(4)
        self.assertEqual(12, tracker.snapshot()["downloaded_bytes"])
        self.assertEqual(20, tracker.snapshot()["total_bytes"])
        self.assertEqual("downloading", tracker.snapshot()["stage"])
        second.update(8)
        second.close()
        self.assertEqual("loading", tracker.snapshot()["stage"])
        self.assertEqual(20, tracker.snapshot()["downloaded_bytes"])

    def test_readiness_and_failure_are_written_without_credentials(self):
        """Records API readiness and initialization failure in a shared progress file."""
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "progress.json")
            tracker = EncoderProgress(path=path, probe=lambda: None)
            self.assertEqual("ready", tracker.report()["stage"])
            tracker.close(failed=True)
            self.assertEqual("failed", json.loads(Path(path).read_text())["stage"])
