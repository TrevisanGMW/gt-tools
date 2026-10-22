"""Deployment data safety, local ownership, and container connection regressions."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from gt.tools.kimodo_generator import kimodo_generator_docker as docker
from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
from gt.utils import kimodo


class TestKimodoDocker(unittest.TestCase):
    """Exercises pure Docker orchestration without requiring an installed engine."""

    def setUp(self):
        """Creates isolated deployment and Hugging Face credential inputs."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = str(Path(self.temporary.name) / "kimodo")
        self.hf_token = Path(self.temporary.name) / "hf_token"
        self.hf_token.write_text("test-hf-credential", encoding="utf-8")
        self.environment = patch.dict(os.environ, {"HF_TOKEN": "", "HUGGING_FACE_HUB_TOKEN": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        names = patch.object(docker, "_docker_project_names", return_value=set())
        names.start()
        self.addCleanup(names.stop)

    def prepare(self):
        """Prepares a fixture deployment using a fake local credential.

        Returns:
            dict: Deployment identity.
        """
        return docker.prepare_deployment(self.directory, str(self.hf_token))

    def connection(self):
        """Creates an authenticated client configuration for the fixture.

        Returns:
            KimodoConnection: Local deployment connection.
        """
        return kimodo.KimodoConnection(token=docker.bridge_token(self.directory))

    def test_prepare_retains_configuration_credentials_and_outputs(self):
        """Never replaces user configuration, credentials, cached models, or jobs."""
        metadata = self.prepare()
        root = Path(self.directory)
        token = docker.bridge_token(self.directory)
        settings = root / "configuration" / ".env"
        settings.write_text(settings.read_text() + "# user setting\n", encoding="utf-8")
        (root / "jobs" / "retained.txt").write_text("job data", encoding="utf-8")
        (root / "models" / "retained.bin").write_bytes(b"model weights")
        self.hf_token.write_text("replacement", encoding="utf-8")
        self.assertEqual(metadata, self.prepare())
        self.assertEqual(token, docker.bridge_token(self.directory))
        self.assertEqual("test-hf-credential\n", (root / "secrets" / "hf_token").read_text())
        self.assertTrue(settings.read_text().endswith("# user setting\n"))
        self.assertEqual("job data", (root / "jobs" / "retained.txt").read_text())
        self.assertEqual(b"model weights", (root / "models" / "retained.bin").read_bytes())
        self.assertTrue((root / "source" / "kimodo-bridge" / "gt" / "utils" / "kimodo.py").is_file())
        self.assertFalse((root / "source" / "secrets").exists())

    def test_unselected_deployment_is_empty_and_never_defaults_to_a_folder(self):
        """Requires explicit selection even when a previous environment default exists."""
        with patch.dict(os.environ, {"GT_KIMODO_DOCKER_DIRECTORY": self.directory}):
            model = KimodoGeneratorModel(preferences=False)
            self.assertEqual("", docker.default_directory())
            self.assertEqual("", model.docker["directory"])
        with self.assertRaisesRegex(ValueError, "absolute"):
            docker.prepare_deployment(model.docker["directory"])
        self.assertFalse(Path(self.directory).exists())

    def test_refuses_relative_root_and_unrelated_folders(self):
        """Prevents defaulting an empty path to cwd or adopting unrelated data."""
        for directory in ("", "relative", str(Path(self.temporary.name).anchor)):
            with self.assertRaises(ValueError):
                docker.prepare_deployment(directory)
        Path(self.directory).mkdir()
        (Path(self.directory) / "keep.txt").write_text("source", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unrelated"):
            self.prepare()
        self.assertEqual("source", (Path(self.directory) / "keep.txt").read_text())

    def test_model_uses_private_token_without_serializing_credentials(self):
        """Maps managed Docker to the existing transport and keeps secrets on disk."""
        self.prepare()
        model = KimodoGeneratorModel(preferences=False)
        model.connection["mode"] = "docker"
        model.docker["directory"] = self.directory
        connection = model.make_connection()
        self.assertEqual("existing", connection.mode)
        self.assertEqual(docker.bridge_token(self.directory), connection.token)
        serialized = json.dumps(model.snapshot())
        self.assertNotIn(connection.token, serialized)
        self.assertNotIn("test-hf-credential", serialized)
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(model.snapshot())
        self.assertEqual(model.docker, restored.docker)
        self.assertEqual("docker", restored.connection["mode"])
        restored.connection["url"] = "http://other-machine:7861"
        with self.assertRaisesRegex(ValueError, "localhost"):
            restored.make_connection()

    def test_remote_engine_and_network_managed_start_are_rejected(self):
        """Requires local engine mounts while allowing network HTTP clients."""
        with patch.dict(os.environ, {"DOCKER_HOST": "tcp://other-machine:2375"}):
            with self.assertRaisesRegex(ValueError, "local engine"):
                docker.check_engine()
        self.prepare()
        connection = kimodo.KimodoConnection(url="http://other-machine:7861")
        with self.assertRaisesRegex(ValueError, "localhost"):
            docker.start(self.directory, connection)

    def test_busy_or_foreign_bridge_never_stops_containers(self):
        """Checks ownership and authenticated idle shutdown before any Compose stop."""
        metadata = self.prepare()
        client = Mock()
        client.health.return_value = {"runtime": {"deployment_id": "another-project"}}
        with patch.object(docker, "check_engine"), patch.object(docker, "_compose") as compose:
            with patch.object(kimodo, "KimodoClient", return_value=client):
                with self.assertRaisesRegex(ValueError, "another bridge"):
                    docker.stop(self.directory, self.connection())
                client.health.return_value = {"runtime": {"deployment_id": metadata["project_name"]}}
                client.shutdown.side_effect = ValueError("bridge is busy")
                with self.assertRaisesRegex(ValueError, "busy"):
                    docker.stop(self.directory, self.connection())
            compose.assert_not_called()

    def test_port_mismatch_is_reported_before_starting_containers(self):
        """Rejects a mismatched URL instead of starting services and timing out."""
        metadata = self.prepare()
        configuration = {"services": {"bridge": {
            "ports": [{"target": 7861, "published": "9999"}],
            "environment": {"GT_KIMODO_DEPLOYMENT_ID": metadata["project_name"]}}}}
        with patch.object(docker, "check_engine"):
            with patch.object(docker, "_compose", return_value=json.dumps(configuration)) as compose:
                with self.assertRaisesRegex(ValueError, "port does not match"):
                    docker.start(self.directory, self.connection())
        self.assertEqual(1, compose.call_count)
        self.assertEqual(["config", "--format", "json"], compose.call_args.args[1])

    def test_connecting_to_existing_healthy_bridge_does_not_recreate_containers(self):
        """Connects without replacing a server that may still be processing jobs."""
        metadata = self.prepare()
        configuration = {"services": {"bridge": {
            "ports": [{"target": 7861, "published": "7861"}],
            "environment": {"GT_KIMODO_DEPLOYMENT_ID": metadata["project_name"]}}}}
        health = {"runtime": {"deployment_id": metadata["project_name"], "active_job_id": "running-job"}}
        with patch.object(docker, "check_engine"):
            with patch.object(docker, "_compose", return_value=json.dumps(configuration)) as compose:
                with patch.object(kimodo.KimodoClient, "health", return_value=health):
                    self.assertEqual(health, docker.start(self.directory, self.connection()))
        self.assertEqual(1, compose.call_count)
        self.assertEqual(["config", "--format", "json"], compose.call_args.args[1])

    def test_stop_preserves_data_and_only_names_owned_services(self):
        """Issues a project-scoped stop without down, volume deletion, or prune."""
        metadata = self.prepare()
        client = Mock()
        client.health.return_value = {"runtime": {"deployment_id": metadata["project_name"]}}
        client.shutdown.return_value = {"stopping": True}
        with patch.object(docker, "check_engine"), patch.object(docker, "_compose") as compose:
            with patch.object(kimodo, "KimodoClient", return_value=client):
                self.assertEqual({"stopping": True}, docker.stop(self.directory, self.connection()))
        self.assertEqual(["stop", "--timeout", "30", "bridge", "text-encoder"], compose.call_args.args[1])
        self.assertTrue((Path(self.directory) / "secrets" / "hf_token").is_file())

    def test_unreachable_running_bridge_is_not_force_stopped(self):
        """Refuses to interrupt unknown work when HTTP health is unavailable."""
        self.prepare()
        client = Mock()
        client.health.side_effect = ConnectionError("unreachable")
        with patch.object(docker, "check_engine"), patch.object(docker, "_compose", return_value="bridge") as compose:
            with patch.object(kimodo, "KimodoClient", return_value=client):
                with self.assertRaisesRegex(ValueError, "running but unreachable"):
                    docker.stop(self.directory, self.connection())
        self.assertEqual(["ps", "--status", "running", "--services"], compose.call_args.args[1])

    def test_cli_path_also_finds_credential_helpers(self):
        """Prepends the selected CLI directory to the subprocess PATH."""
        executable = str(Path(self.temporary.name) / "bin" / "docker.exe")
        completed = Mock(returncode=0, stdout=b"ready", stderr=b"")
        with patch.object(docker, "find_docker", return_value=executable):
            with patch.object(docker.subprocess, "run", return_value=completed) as run:
                self.assertEqual("ready", docker._run(["version"]))
        self.assertEqual([executable, "version"], run.call_args.args[0])
        self.assertEqual(os.path.dirname(executable), run.call_args.kwargs["env"]["PATH"].split(os.pathsep)[0])

    def test_encoder_status_distinguishes_starting_from_stopped(self):
        """Diagnoses initialization without claiming that an exited encoder is loading."""
        with patch.object(docker, "_compose") as compose:
            compose.return_value = json.dumps({"State": "running", "Health": "starting", "ExitCode": 0})
            result = docker.encoder_status(self.directory)
            self.assertEqual("starting", result["status"])
            self.assertIn("downloading or loading", result["detail"])
            compose.return_value = json.dumps([{"State": "exited", "Health": "", "ExitCode": 1}])
            result = docker.encoder_status(self.directory)
            self.assertEqual("unavailable", result["status"])
            self.assertIn("exit code 1", result["detail"])
            compose.return_value = ""
            self.assertIn("absent", docker.encoder_status(self.directory)["detail"])
            self.assertEqual(["ps", "--all", "--format", "json", "text-encoder"], compose.call_args.args[1])

    def test_friendly_names_only_add_suffixes_for_existing_projects_or_images(self):
        """Claims readable names across Docker resources and adjacent prepared folders."""
        first = self.prepare()
        self.assertEqual("kimodo-bridge", first["project_name"])
        second = docker.prepare_deployment(str(Path(self.temporary.name) / "second"), str(self.hf_token))
        self.assertEqual("kimodo-bridge-2", second["project_name"])
        with patch.object(docker, "_docker_project_names", return_value={"kimodo-bridge-3"}):
            third = docker.prepare_deployment(str(Path(self.temporary.name) / "third"), str(self.hf_token))
        self.assertEqual("kimodo-bridge-4", third["project_name"])
        self.assertEqual(first["project_name"], self.prepare()["project_name"])

    def test_project_conflict_never_manages_another_folder(self):
        """Refuses a same-name project before forwarding the Compose mutation."""
        self.prepare()
        with patch.object(docker, "_run", return_value="container-id|/another/deployment/configuration") as run:
            with self.assertRaisesRegex(ValueError, "another deployment"):
                docker._compose(self.directory, ["stop"])
            self.assertEqual(1, run.call_count)
        owner = str(Path(self.directory) / "configuration")
        with patch.object(docker, "_run", side_effect=[f"container-id|{owner}", "stopped"]):
            self.assertEqual("stopped", docker._compose(self.directory, ["stop"]))

    def test_existing_legacy_project_and_image_names_are_preserved(self):
        """Does not rename an existing deployment or orphan its running containers."""
        metadata = self.prepare()
        root = Path(self.directory)
        legacy = "gt-kimodo-existing123"
        settings = root / "configuration" / ".env"
        original_settings = settings.read_text().replace(metadata["project_name"], legacy)
        settings.write_text(original_settings, encoding="utf-8")
        metadata["project_name"] = legacy
        (root / "deployment.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertEqual(legacy, self.prepare()["project_name"])
        self.assertEqual(original_settings, settings.read_text())

    def test_latest_build_records_exact_commits_and_policy(self):
        """Resolves latest at build time while leaving marker identity unchanged."""
        first = self.prepare()
        revisions = {"kimodo_revision": "a" * 40, "viser_revision": "b" * 40}
        with patch.object(docker, "check_engine"), patch.object(docker, "_clone_source"):
            with patch.object(docker.sources, "latest_revisions", return_value=revisions) as latest:
                with patch.object(docker, "_compose", return_value="built") as compose:
                    docker.build_image(self.directory)
        latest.assert_called_once()
        self.assertEqual(1, compose.call_count)
        result = docker.read_deployment(self.directory)
        self.assertEqual("latest", result["revision_source"])
        self.assertEqual(revisions, result["last_successful_build"])
        self.assertEqual(first["project_name"], result["project_name"])
        self.assertFalse(result["use_stable_revisions"])

    def test_latest_lookup_and_build_failures_use_stable_fallback_once(self):
        """Falls back for unavailable latest sources and incompatible latest builds."""
        self.prepare()
        revisions = {"kimodo_revision": "a" * 40, "viser_revision": "b" * 40}
        with patch.object(docker, "check_engine"), patch.object(docker, "_clone_source"):
            with patch.object(docker.sources, "latest_revisions", side_effect=OSError("offline")):
                with patch.object(docker, "_compose", return_value="built") as compose:
                    docker.build_image(self.directory)
            self.assertEqual(1, compose.call_count)
            self.assertEqual("stable_fallback", docker.read_deployment(self.directory)["revision_source"])
            with patch.object(docker.sources, "latest_revisions", return_value=revisions):
                with patch.object(docker, "_compose", side_effect=[RuntimeError("latest failed"), "built"]) as compose:
                    docker.build_image(self.directory)
            self.assertEqual(2, compose.call_count)
            with patch.object(docker.sources, "latest_revisions", return_value=revisions):
                with patch.object(docker, "_compose", side_effect=RuntimeError("build failed")) as compose:
                    with self.assertRaisesRegex(RuntimeError, "build failed"):
                        docker.build_image(self.directory)
            self.assertEqual(2, compose.call_count)
        result = docker.read_deployment(self.directory)
        self.assertEqual("stable_fallback", result["revision_source"])
        self.assertEqual(docker.sources.stable_revisions(), result["last_successful_build"])

    def test_stable_mode_skips_latest_and_safety_errors_never_retry(self):
        """Uses explicit stable policy and preserves edited sources rather than retrying."""
        self.prepare()
        with patch.object(docker, "check_engine"), patch.object(docker.sources, "latest_revisions") as latest:
            with patch.object(docker, "_clone_source"), patch.object(docker, "_compose", return_value="built"):
                docker.build_image(self.directory, use_stable_revisions=True)
            latest.assert_not_called()
            self.assertEqual("stable", docker.read_deployment(self.directory)["revision_source"])
            with patch.object(docker, "_clone_source", side_effect=docker.sources.SourceCheckoutError("edited")):
                with patch.object(docker, "_compose") as compose:
                    with self.assertRaisesRegex(docker.sources.SourceCheckoutError, "edited"):
                        docker.build_image(self.directory, use_stable_revisions=True)
            compose.assert_not_called()
