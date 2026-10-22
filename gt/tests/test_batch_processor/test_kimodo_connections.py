"""Pure regression checks for Docker startup waits and task-owned array publication."""

import os
import tempfile
import unittest
from unittest import mock

from gt.utils import kimodo
from gt.tools.batch_processor.tasks import task_kimodo_connection as connections
from gt.tools.batch_processor.tasks.task_kimodo_numpy import publish_numpy


class TestKimodoConnections(unittest.TestCase):
    """Checks readiness, cancellation and file safety without Maya or Docker."""

    def setUp(self):
        """Isolates saved preferences so auto discovery is deterministic."""
        self.saved = {"connection": {"url": kimodo.DEFAULT_URL, "mode": "docker"},
                      "docker": {"directory": "", "executable": ""}}
        patcher = mock.patch.object(connections, "generator_settings", return_value=self.saved)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_deployment(self, directory):
        """Creates credential/configuration fixtures without Docker.

        Args:
            directory (str): Temporary deployment root.

        Returns:
            dict: Existing-bridge settings using automatic credentials.
        """
        import json
        from pathlib import Path

        root = Path(directory)
        (root / "configuration").mkdir()
        (root / "secrets").mkdir()
        (root / "configuration" / ".env").write_text("BRIDGE_PORT=7861\n", encoding="utf8")
        (root / "secrets" / "bridge_token").write_text("fixture-private-token", encoding="utf8")
        (root / "deployment.json").write_text(json.dumps({"schema_version": 1, "tool": "kimodo_generator",
                                                        "project_name": "kimodo-fixture"}), encoding="utf8")
        return {"connection": {"mode": "existing", "url": kimodo.DEFAULT_URL},
                "docker": {"directory": directory, "executable": ""}, "authentication": "auto",
                "token_environment": "KIMODO_BRIDGE_TOKEN"}

    def test_existing_local_bridge_reads_token_and_ignores_unset_legacy_variable(self):
        """Authenticates an existing deployment without starting it or exporting secrets."""
        import json
        from gt.tools.batch_processor.tasks import task_kimodo_generate as generation

        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            with mock.patch.dict(os.environ, {}, clear=True):
                connection = connections.make_connection(settings)
            self.assertEqual("fixture-private-token", connection.token)
            self.assertNotIn(connection.token, json.dumps(settings))
            client = mock.Mock()
            client.health.return_value = {"runtime": {"deployment_id": "kimodo-fixture"}}
            with mock.patch.object(kimodo, "KimodoClient", return_value=client), \
                    mock.patch.object(generation.docker_runtime, "start") as start:
                self.assertIs(client, generation.connect(settings))
            start.assert_not_called()

    def test_saved_generator_deployment_is_used_only_for_matching_local_port(self):
        """Allows URL-only local reuse without reading another endpoint's credentials."""
        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            self.saved["docker"]["directory"] = directory
            settings["docker"]["directory"] = ""
            self.assertEqual("fixture-private-token", connections.make_connection(settings).token)
            settings["connection"]["url"] = "http://127.0.0.1:7862"
            settings["token_environment"] = ""
            self.assertIsNone(connections.make_connection(settings).token)

    def test_saved_wsl_profile_does_not_supply_an_old_docker_credential(self):
        """Keeps URL-only legacy WSL usable when Docker settings remain saved separately."""
        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            self.saved["docker"]["directory"] = directory
            self.saved["connection"]["mode"] = "wsl"
            settings["docker"]["directory"] = ""
            settings["token_environment"] = ""
            self.assertIsNone(connections.make_connection(settings).token)

    def test_explicit_deployment_wrong_port_is_rejected_before_reading_secret(self):
        """Prevents automatically sending a credential to a different local service."""
        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            settings["connection"]["url"] = "http://localhost:7862"
            with mock.patch.object(connections.docker, "bridge_token") as token:
                with self.assertRaisesRegex(ValueError, "BRIDGE_PORT"):
                    connections.make_connection(settings)
            token.assert_not_called()

    def test_remote_auto_never_reads_local_token(self):
        """Requires an explicit remote credential policy instead of forwarding local tokens."""
        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            settings["connection"]["url"] = "http://other-machine:7861"
            settings["token_environment"] = ""
            with mock.patch.object(connections.docker, "bridge_token") as token:
                with self.assertRaisesRegex(ValueError, "Remote bridge"):
                    connections.make_connection(settings)
            token.assert_not_called()

    def test_environment_and_legacy_none_are_explicit(self):
        """Reads an explicitly selected variable and ignores it for the legacy no-auth option."""
        settings = {"connection": {"mode": "existing", "url": "http://other-machine:7861"},
                    "authentication": "environment", "token_environment": "TEST_KIMODO_TOKEN"}
        with mock.patch.dict(os.environ, {"TEST_KIMODO_TOKEN": "remote-token"}):
            self.assertEqual("remote-token", connections.make_connection(settings).token)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "unset in Maya"):
                connections.make_connection(settings)
        settings["authentication"] = "none"
        self.assertIsNone(connections.make_connection(settings).token)
        settings["authentication"] = "environment"
        settings["token_environment"] = "1" * 64
        with self.assertRaises(ValueError) as caught:
            connections.make_connection(settings)
        self.assertNotIn("1" * 64, str(caught.exception))

    def test_identity_mismatch_and_rejected_credentials_are_actionable(self):
        """Checks deployment identity and gives a configuration action for rejected tokens."""
        with tempfile.TemporaryDirectory() as directory:
            settings = self.make_deployment(directory)
            client = mock.Mock()
            client.health.return_value = {"runtime": {"deployment_id": "another-deployment"}}
            with self.assertRaisesRegex(ValueError, "another bridge"):
                connections.check_health(client, settings)
            client.health.side_effect = RuntimeError("Kimodo HTTP 403: unauthorized")
            with self.assertRaisesRegex(RuntimeError, "Automatic credentials"):
                connections.check_health(client, settings)

    def test_encoder_loading_waits_before_submitting(self):
        """Retries only a loading encoder, allowing readiness on the next probe."""
        client = mock.Mock()
        client.test_text_encoder.side_effect = [kimodo.KimodoEncoderUnavailable("loading"), {}]
        with mock.patch.object(connections.time, "sleep") as sleep:
            connections.wait_for_encoder(client, 10)
        self.assertEqual(2, client.test_text_encoder.call_count)
        sleep.assert_called_once_with(1)

    def test_encoder_timeout_and_auth_failures_are_distinct(self):
        """Bounds a download wait while surfacing authentication errors immediately."""
        client = mock.Mock()
        client.test_text_encoder.side_effect = kimodo.KimodoEncoderUnavailable("loading")
        with mock.patch.object(connections.time, "monotonic", side_effect=[0, 2]):
            with self.assertRaisesRegex(TimeoutError, "Startup timeout"):
                connections.wait_for_encoder(client, 1)
        client.test_text_encoder.side_effect = RuntimeError("HTTP 401")
        with self.assertRaisesRegex(RuntimeError, "401"):
            connections.wait_for_encoder(client, 10)

    def test_startup_cancellation_leaves_server_running(self):
        """Cancels before probing or touching any shared server job."""
        client = mock.Mock()
        with self.assertRaisesRegex(RuntimeError, "canceled"):
            connections.wait_for_encoder(client, 10, {"cancel_requested": mock.Mock(return_value=True)})
        client.test_text_encoder.assert_not_called()
        client.cancel.assert_not_called()

    def test_empty_docker_paths_do_not_become_working_directory(self):
        """Keeps unset paths empty and detaches serialized task data."""
        settings = {"connection": {"mode": "docker"}, "docker": {"directory": "", "executable": ""}}
        resolved = connections.resolve_settings(settings)
        self.assertEqual({"directory": "", "executable": ""}, resolved["docker"])
        resolved["docker"]["directory"] = "changed"
        self.assertEqual("", settings["docker"]["directory"])

    def test_numpy_skip_and_overwrite_preserve_existing_outputs(self):
        """Moves only with explicit overwrite and preserves prior arrays otherwise."""
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "motion.npz")
            output = os.path.join(directory, "walk.npz")
            with open(source, "wb") as stream:
                stream.write(b"new native array")
            with open(output, "wb") as stream:
                stream.write(b"previous array")
            publish_numpy(source, output)
            with open(output, "rb") as stream:
                self.assertEqual(b"previous array", stream.read())
            self.assertTrue(os.path.isfile(source))
            publish_numpy(source, output, overwrite=True)
            self.assertFalse(os.path.exists(source))
            with open(output, "rb") as stream:
                self.assertEqual(b"new native array", stream.read())

    def test_empty_numpy_download_cannot_replace_an_output(self):
        """Rejects empty data before touching the destination."""
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "motion.npz")
            output = os.path.join(directory, "walk.npz")
            with open(source, "wb"):
                pass
            with self.assertRaisesRegex(ValueError, "empty"):
                publish_numpy(source, output, overwrite=True)
            self.assertFalse(os.path.exists(output))
