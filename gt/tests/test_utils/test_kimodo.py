"""Pure Python and loopback HTTP regression tests for the Kimodo integration."""

import copy
import io
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import uuid
import warnings
from unittest.mock import patch, Mock

from gt.utils import kimodo


def sample_motion():
    """Builds a small SOMA-sized hierarchy with a known quarter-turn motion.

    Returns:
        dict: Portable two-frame test motion.
    """
    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    first = [copy.deepcopy(identity) for index in range(77)]
    second = copy.deepcopy(first)
    second[0] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    return {
        "schema_version": 1,
        "coordinates": {"units": "meters", "up": "y", "forward": "+z",
                        "rotations": "column_local_matrix"},
        "fps": 30.0, "frame_count": 2,
        "skeleton": {"id": "somaskel77", "joint_names": [f"joint_{index}" for index in range(77)],
                     "parents": [-1] + [0] * 76, "offsets": [[0, 0, 0]] + [[1, 0, 0]] * 76},
        "root_positions": [[0, 1, 0], [0, 1, 1]],
        "local_rotations": [first, second],
    }


class FakeBackend:
    """Provides deterministic generation through the real HTTP and job layers."""

    def __init__(self):
        """Initializes execution tracking."""
        self.calls = []

    def capabilities(self):
        """Returns the supported test model.

        Returns:
            dict: Minimal backend capabilities.
        """
        return {"models": [{"id": kimodo.DEFAULT_MODEL}]}

    def generate(self, definition, directory, update):
        """Writes known artifacts or simulates inference failure.

        Args:
            definition (dict): Accepted request.
            directory (str): Server job directory.
            update (callable): Status reporter.

        Returns:
            dict: Resolved seed.
        """
        self.calls.append(definition)
        update(stage="generating")
        if definition["prompts"][0]["text"] == "fail":
            raise RuntimeError("Simulated model failure")
        kimodo._write_json(os.path.join(directory, "motion.json"), sample_motion())
        with open(os.path.join(directory, "motion.npz"), "xb") as stream:
            stream.write(b"test artifact")
        return {"seed": definition["parameters"]["seed"]}

    def download(self, model, update):
        """Simulates downloading a model through the real queue.

        Args:
            model (str): Requested model ID.
            update (callable): Job stage reporter.

        Returns:
            dict: Resolved model ID.
        """
        update(stage="downloading_model")
        return {"model": model}

    def rest_motion(self):
        """Returns a portable rest skeleton fixture.

        Returns:
            dict: Motion metadata.
        """
        return sample_motion()


class TestKimodoDefinition(unittest.TestCase):
    """Tests portable settings and import isolation."""

    def test_round_trip_is_detached(self):
        """Preserves punctuation and settings without sharing mutable data."""
        definition = kimodo.KimodoGenerationDefinition("Walk. Stop!", seed=None)
        data = definition.as_dict()
        loaded = kimodo.KimodoGenerationDefinition.from_dict(data)
        self.assertEqual(data, loaded.as_dict())
        data["prompts"][0]["text"] = "Changed"
        self.assertEqual("Walk. Stop!", loaded.as_dict()["prompts"][0]["text"])

    def test_local_humanik_option_round_trip_and_old_definitions(self):
        """Defaults authoring to HumanIK while keeping old definition files readable."""
        definition = kimodo.KimodoGenerationDefinition("Walk", auto_humanik=False)
        self.assertEqual(False, kimodo.KimodoGenerationDefinition.from_dict(
            definition.as_dict()).data["maya"]["auto_humanik"])
        old = definition.as_dict()
        old.pop("maya")
        self.assertEqual(True, kimodo.KimodoGenerationDefinition.from_dict(old).data["maya"]["auto_humanik"])
        with self.assertRaises(ValueError):
            kimodo.KimodoGenerationDefinition("Walk", auto_humanik="yes")

    def test_local_options_do_not_change_bridge_payload(self):
        """Supports already-running bridges without requiring a WSL update/restart."""
        definition = kimodo.KimodoGenerationDefinition("Walk", auto_humanik=False)
        client = kimodo.KimodoClient()
        with patch.object(client, "_request", return_value={}) as request:
            client.submit(definition)
        self.assertNotIn("maya", request.call_args[0][1]["definition"])
        self.assertEqual(False, definition.data["maya"]["auto_humanik"])

    def test_invalid_settings(self):
        """Rejects non-finite numbers, booleans masquerading as integers, and empty text."""
        for settings in ({"prompt": ""}, {"duration_seconds": float("nan")},
                         {"duration_seconds": 0}, {"seed": True}, {"diffusion_steps": 0},
                         {"postprocess": 1}, {"duration_seconds": 31}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                arguments = dict(prompt="Walk")
                arguments.update(settings)
                kimodo.KimodoGenerationDefinition(**arguments)

    def test_unsupported_features_are_not_silently_ignored(self):
        """Rejects settings outside the first milestone."""
        for field, value in (("constraints", [{"type": "root2d"}]),
                             ("prompts", []), ("schema_version", 2), ("extra", 1)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                data = kimodo.KimodoGenerationDefinition("Walk").as_dict()
                data[field] = value
                kimodo.KimodoGenerationDefinition.from_dict(data)

    def test_module_import_does_not_load_runtimes(self):
        """Imports the client without Maya, Kimodo, NumPy, or Torch."""
        code = ("import sys; import gt.utils.kimodo; "
                "assert not any(name in sys.modules for name in ('maya', 'torch', 'kimodo', 'numpy'))")
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)

    def test_motion_validation(self):
        """Validates shapes, names, finite values, hierarchy, and rotations."""
        self.assertEqual(2, kimodo.validate_motion(sample_motion())["frame_count"])
        for change in ("hierarchy", "names", "nan", "shape", "reflection"):
            data = sample_motion()
            if change == "hierarchy":
                data["skeleton"]["parents"][1] = 1
            elif change == "names":
                data["skeleton"]["joint_names"][1] = "root|unsafe"
            elif change == "nan":
                data["root_positions"][0][0] = float("nan")
            elif change == "shape":
                data["local_rotations"].pop()
            else:
                data["local_rotations"][0][0][0][0] = -1
            with self.subTest(change=change), self.assertRaises(ValueError):
                kimodo.validate_motion(data)

    def test_launch_modes_use_argument_lists(self):
        """Preserves spaces in native paths and uses the selected WSL distribution."""
        native = kimodo.KimodoConnection(mode="native", python_path=sys.executable)
        self.assertEqual([sys.executable], native._python_command())
        wsl = kimodo.KimodoConnection(mode="wsl", distribution="Ubuntu Test",
                                      python_path="/home/test user/env/bin/python")
        self.assertEqual(["wsl.exe", "--distribution", "Ubuntu Test", "--exec",
                          "/home/test user/env/bin/python"], wsl._python_command())
        self.assertEqual(wsl._python_command(), wsl.validate_local_launch())
        with self.assertRaises(ValueError):
            kimodo.KimodoConnection(mode="wsl", python_path="~/env/bin/python")._python_command()
        with self.assertRaisesRegex(ValueError, "localhost"):
            kimodo.KimodoConnection(url="https://remote.example:7861", mode="wsl",
                                    distribution="Ubuntu Test",
                                    python_path="/home/test/env/bin/python").validate_local_launch()

    def test_launch_resolves_environment_folders(self):
        """Accepts environment roots instead of trying to execute their directories."""
        with tempfile.TemporaryDirectory() as directory:
            scripts = os.path.join(directory, "Scripts")
            os.makedirs(scripts)
            executable = os.path.join(scripts, "python.exe")
            with open(executable, "wb") as stream:
                stream.write(b"")
            native = kimodo.KimodoConnection(mode="native", python_path=directory)
            self.assertEqual([executable], native._python_command())
            self.assertEqual(executable, native.python_path)
        checked = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        wsl = kimodo.KimodoConnection(
            mode="wsl", distribution="Ubuntu-26.04", python_path="/home/user/kimodo_env")
        with patch.object(kimodo.subprocess, "run", return_value=checked) as run:
            command = wsl._python_command()
        expected = "/home/user/kimodo_env/bin/python"
        self.assertEqual(["wsl.exe", "--distribution", "Ubuntu-26.04", "--exec", expected], command)
        self.assertEqual(expected, wsl.python_path)
        self.assertEqual(["wsl.exe", "--distribution", "Ubuntu-26.04", "--exec",
                          "test", "-f", expected, "-a", "-x", expected], run.call_args.args[0])

    def test_wsl_deployment_failure_reports_resolved_python_and_output(self):
        """Replaces raw CalledProcessError tracebacks with actionable WSL diagnostics."""
        checked = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        failure = subprocess.CalledProcessError(
            1, ["wsl.exe"], stderr=b"the selected interpreter could not run the deployment")
        connection = kimodo.KimodoConnection(
            mode="wsl", distribution="Ubuntu-26.04", python_path="/home/user/kimodo_env")
        with patch.object(kimodo.KimodoClient, "health", side_effect=ConnectionError):
            with patch.object(kimodo.subprocess, "run", side_effect=[checked, failure]):
                with self.assertRaisesRegex(RuntimeError, "/home/user/kimodo_env/bin/python") as caught:
                    connection.start_local()
        self.assertIn("the selected interpreter could not run", str(caught.exception))

    def test_local_launch_console_is_visible_by_default_and_can_be_hidden(self):
        """Uses a new console by default and redirected logs only after explicit opt-out."""
        process = Mock()
        process.poll.return_value = None
        ready = {"status": "ready"}
        with patch.object(kimodo.os, "name", "nt"):
            with patch.object(kimodo.subprocess, "CREATE_NEW_CONSOLE", 16, create=True):
                connection = kimodo.KimodoConnection(
                    mode="native", python_path=sys.executable, show_console=True)
                with patch.object(kimodo.KimodoClient, "health",
                                  side_effect=[ConnectionError, ready]):
                    with patch.object(kimodo.subprocess, "Popen", return_value=process) as launch:
                        self.assertEqual(ready, connection.start_local(startup_timeout=1))
                self.assertEqual(16, launch.call_args.kwargs["creationflags"])
                self.assertNotIn("stdin", launch.call_args.kwargs)
                self.assertNotIn("stdout", launch.call_args.kwargs)
                self.assertIsNone(connection.log_path)
        with tempfile.TemporaryDirectory() as directory:
            connection = kimodo.KimodoConnection(
                mode="native", python_path=sys.executable, show_console=False)
            with patch.object(kimodo.KimodoClient, "health", side_effect=[ConnectionError, ready]):
                with patch.object(kimodo.subprocess, "Popen", return_value=process) as launch:
                    self.assertEqual(ready, connection.start_local(
                        startup_timeout=1, log_directory=directory))
            self.assertIn("stdout", launch.call_args.kwargs)
            self.assertTrue(os.path.isfile(connection.log_path))

    def test_bridge_banner_identifies_server_and_runtime(self):
        """Makes a visible console unmistakably identify its purpose and endpoint."""
        banner = kimodo._bridge_banner("127.0.0.1", 7861, "/tmp/kimodo/jobs")
        self.assertIn("KIMODO BRIDGE", banner)
        self.assertIn("Maya animation generation server", banner)
        self.assertIn("http://127.0.0.1:7861", banner)
        self.assertIn("/tmp/kimodo/jobs", banner)
        self.assertIn(str(os.getpid()), banner)

    def test_known_torch_deprecation_is_hidden_without_hiding_other_warnings(self):
        """Filters only the noisy torch.jit.script deprecation from bridge startup."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            kimodo._suppress_known_runtime_warnings()
            warnings.warn("`torch.jit.script` is deprecated. Please switch APIs.", FutureWarning)
            warnings.warn("A different runtime warning", FutureWarning)
        self.assertEqual(1, len(caught))
        self.assertIn("different runtime", str(caught[0].message))
        self.assertEqual("1", os.environ["HF_HUB_DISABLE_PROGRESS_BARS"])
        self.assertEqual("1", os.environ["TQDM_DISABLE"])

    def test_text_encoder_probe_validates_expected_api(self):
        """Distinguishes a ready Kimodo encoder from an arbitrary web service."""
        opener = Mock()
        opener.open.return_value = io.BytesIO(
            b'{"dependencies": [{"api_name": "DemoWrapper"}]}')
        with patch.object(kimodo.urllib.request, "build_opener", return_value=opener):
            result = kimodo.probe_text_encoder("http://127.0.0.1:9550")
        self.assertEqual("ready", result["status"])
        self.assertEqual("DemoWrapper", result["api_name"])
        opener.open.return_value = io.BytesIO(b'{"dependencies": []}')
        with patch.object(kimodo.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(RuntimeError, "not the expected"):
                kimodo.probe_text_encoder("http://127.0.0.1:9550")

    def test_wsl_encoder_launch_uses_an_independent_session(self):
        """Keeps a bridge-owned Linux/WSL encoder alive across managed bridge restarts."""
        backend = object.__new__(kimodo._KimodoBackend)
        backend.text_encoder_url = "http://127.0.0.1:9550"
        backend.start_encoder = True
        backend.encoder_process = None
        backend._encoder_ready = Mock(side_effect=(False, True))
        process = Mock()
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(kimodo.os, "name", "posix"):
                with patch.object(kimodo.subprocess, "Popen", return_value=process) as launch:
                    backend._ensure_encoder(directory)
        self.assertEqual(True, launch.call_args.kwargs["start_new_session"])
        self.assertNotIn("creationflags", launch.call_args.kwargs)


class TestKimodoRootHeading(unittest.TestCase):
    """Verifies Maya-free root heading math and the native [cos, sin] constraint shape."""

    def test_heading_from_direction_matches_kimodo_convention(self):
        """Uses 0 for +Z and positive quarter turns toward +X."""
        self.assertAlmostEqual(0.0, kimodo.heading_from_direction(0, 1))
        self.assertAlmostEqual(kimodo.math.pi / 2, kimodo.heading_from_direction(1, 0))
        self.assertAlmostEqual(-kimodo.math.pi / 2, kimodo.heading_from_direction(-1, 0))

    def test_travel_headings_hold_through_stops(self):
        """Keeps the last travel direction while the root is stationary, and backfills a still start."""
        coordinates = [[0, 0], [0, 0], [0, 1], [0, 2], [0, 2], [0, 2], [1, 2], [2, 2]]
        headings = kimodo.travel_headings(coordinates)
        self.assertEqual(len(coordinates), len(headings))
        self.assertAlmostEqual(0.0, headings[0])
        self.assertAlmostEqual(0.0, headings[4])
        self.assertAlmostEqual(kimodo.math.pi / 2, headings[-1])
        self.assertEqual([0.0, 0.0], kimodo.travel_headings([[1, 1], [1, 1]]))

    def test_travel_headings_prefer_explicit_tangents(self):
        """Uses supplied tangents instead of finite differences."""
        headings = kimodo.travel_headings([[0, 0], [0, 1]], tangents=[[1, 0], [1, 0]])
        self.assertAlmostEqual(kimodo.math.pi / 2, headings[0])

    def test_heading_vectors_apply_offset(self):
        """Encodes cos/sin pairs and adds offsets in degrees."""
        self.assertEqual([[1.0, 0.0]], kimodo.heading_vectors([0.0]))
        self.assertEqual([[-1.0, 0.0]], kimodo.heading_vectors([0.0], 180))
        self.assertEqual([[0.0, 1.0]], kimodo.heading_vectors([0.0], 90))

    def test_validate_root_heading_mode(self):
        """Accepts known modes and rejects unknown modes or invalid offsets."""
        self.assertEqual(("path", 180.0), kimodo.validate_root_heading_mode("path", 180))
        for mode, offset in (("tangent", 0), ("node", "90"), ("node", float("nan")), ("node", True)):
            with self.assertRaises(ValueError):
                kimodo.validate_root_heading_mode(mode, offset)

    def test_root2d_heading_uses_cos_sin_pairs(self):
        """Matches Kimodo's (frames, 2) global_root_heading layout."""
        constraint = {"type": "root2d", "frame_indices": [0, 1], "smooth_root_2d": [[0, 0], [0, 1]],
                      "global_root_heading": [[1, 0], [1, 0]]}
        self.assertEqual([constraint], kimodo.validate_constraints([constraint]))
        constraint["global_root_heading"] = [0.0, 0.0]
        with self.assertRaises(ValueError):
            kimodo.validate_constraints([constraint])


class TestKimodoHttp(unittest.TestCase):
    """Exercises real HTTP with a deterministic backend and isolated job storage."""

    def setUp(self):
        """Starts a loopback bridge on an ephemeral port."""
        self.temporary = tempfile.TemporaryDirectory()
        self.backend = FakeBackend()
        self.state = kimodo._BridgeState(os.path.join(self.temporary.name, "server"), self.backend)
        self.server = kimodo.ThreadingHTTPServer(("127.0.0.1", 0), kimodo._BridgeHandler)
        self.server.state = self.state
        self.server.token = "test-token"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = kimodo.KimodoConnection(
            url=f"http://127.0.0.1:{self.server.server_port}", token="test-token")
        self.client = kimodo.KimodoClient(self.connection)

    def tearDown(self):
        """Stops only owned test resources."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.state.close()
        self.temporary.cleanup()

    def test_generation_download_and_no_overwrite(self):
        """Submits, polls, verifies checksums, and prevents overwriting local results."""
        self.assertEqual("gt-kimodo", self.client.health()["service"])
        job = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))
        result = self.client.wait(job["job_id"], timeout=5, poll_interval=0.01)
        self.assertEqual("succeeded", result["status"])
        self.assertEqual(("complete", 1.0), (result["stage"], result["progress"]))
        self.assertEqual(os.path.join(self.temporary.name, "server", job["job_id"]), result["server_directory"])
        paths = self.client.download(job["job_id"], self.temporary.name)
        self.assertEqual(2, kimodo.validate_motion(kimodo._read_json(paths["motion.json"]))["frame_count"])
        self.assertEqual(12345, kimodo._read_json(paths["result.json"])["resolved"]["seed"])
        with self.assertRaises(FileExistsError):
            self.client.download(job["job_id"], self.temporary.name)
        self.assertEqual(paths, self.client.download(job["job_id"], self.temporary.name, reuse_existing=True))

    def test_console_feedback_is_flushed_and_coarsely_throttled(self):
        """Always shows acceptance and terminal state without flooding every diffusion step."""
        job_id = "a" * 32
        self.state.console_job_updates.pop(job_id, None)
        with patch("builtins.print") as output:
            self.state._log_job_update(job_id, stage="queued", progress=0, queue_size=2)
            self.state._log_job_update(job_id, stage="connecting_text_encoder")
            self.state._log_job_update(job_id, stage="generating", progress=0.11)
            self.state._log_job_update(job_id, stage="generating", progress=0.19)
            self.state._log_job_update(job_id, stage="complete", progress=1.0)
        messages = [call.args[0] for call in output.call_args_list]
        self.assertEqual(3, len(messages))
        self.assertIn("SUBMITTED", messages[0])
        self.assertIn("Queue Position 2", messages[0])
        self.assertRegex(messages[0], r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")
        self.assertIn("10%", messages[1])
        self.assertIn("COMPLETE", messages[2])
        self.assertFalse(any("TEXT ENCODER" in message for message in messages))
        self.assertTrue(all(call.kwargs.get("flush") for call in output.call_args_list))

    def test_health_reports_runtime_and_shutdown_refuses_busy_work(self):
        """Makes process ownership visible and stops only when no generation can be interrupted."""
        health = self.client.health()
        self.assertEqual(["delete_jobs", "shutdown", "runtime_status", "root_heading_vectors"], health["features"])
        self.assertEqual(os.getpid(), health["runtime"]["pid"])
        self.assertEqual(self.state.directory, health["runtime"]["job_directory"])
        self.assertIsNone(health["runtime"]["active_job_id"])
        self.assertEqual(0, health["runtime"]["unfinished_jobs"])
        with self.state.lock:
            self.state.active_job_id = "a" * 32
        try:
            with self.assertRaisesRegex(RuntimeError, "bridge is busy"):
                self.client.shutdown()
        finally:
            with self.state.lock:
                self.state.active_job_id = None
        result = self.client.shutdown()
        self.assertEqual(True, result["stopping"])
        self.assertEqual("unchanged", result["encoder_action"])
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def test_heading_submission_requires_current_bridge(self):
        """Explains a bridge restart instead of letting an old validator reject heading pairs."""
        constraint = {"type": "root2d", "frame_indices": [0, 1], "smooth_root_2d": [[0, 0], [0, 1]],
                      "global_root_heading": [[1, 0], [1, 0]]}
        definition = kimodo.KimodoGenerationDefinition("Walk", constraints=[constraint])
        old_health = dict(self.client.health(), features=["delete_jobs", "shutdown", "runtime_status"])
        with patch.object(self.client, "health", return_value=old_health):
            with self.assertRaisesRegex(ValueError, "Restart the bridge"):
                self.client.submit(definition)
        job = self.client.submit(definition)
        self.client.wait(job["job_id"], timeout=5, poll_interval=0.01)

    def test_duplicate_submission_is_idempotent(self):
        """A retry never generates twice, and a conflicting payload is rejected."""
        definition = kimodo.KimodoGenerationDefinition("Walk")
        job_id = uuid.uuid4().hex
        self.client.submit(definition, job_id=job_id)
        self.client.wait(job_id, timeout=5, poll_interval=0.01)
        self.client.submit(definition, job_id=job_id)
        self.assertEqual(1, len(self.backend.calls))
        with self.assertRaisesRegex(RuntimeError, "different definition"):
            self.client.submit(kimodo.KimodoGenerationDefinition("Run"), job_id=job_id)

    def test_failed_job_does_not_stop_worker(self):
        """Returns the backend error and processes a subsequent request."""
        job = self.client.submit(kimodo.KimodoGenerationDefinition("fail"))
        with self.assertRaisesRegex(RuntimeError, "Simulated model failure"):
            self.client.wait(job["job_id"], timeout=5, poll_interval=0.01)
        next_job = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))
        self.assertEqual("succeeded", self.client.wait(next_job["job_id"], timeout=5)["status"])

    def test_authentication_and_path_traversal(self):
        """Rejects bad tokens, browser requests, and arbitrary file paths."""
        self.connection.token = "incorrect"
        with self.assertRaisesRegex(RuntimeError, "403"):
            self.client.health()
        self.connection.token = "test-token"
        request = urllib.request.Request(self.connection.url + "/v1/health", headers={
            "Authorization": "Bearer test-token", "Origin": "http://untrusted.example"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.client.opener.open(request)
        caught.exception.close()
        with self.assertRaises(ValueError):
            self.client.status("../../definition.json")
        with self.assertRaisesRegex(RuntimeError, "404"):
            self.client._request(f"/v1/jobs/{uuid.uuid4().hex}/artifacts/../../file")

    def test_corrupt_artifact_is_not_published(self):
        """Leaves a failed verification as a partial file, never a valid motion.json."""
        job_id = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))["job_id"]
        self.client.wait(job_id, timeout=5, poll_interval=0.01)
        path = os.path.join(self.state.directory, job_id, "motion.json")
        with open(path, "ab") as stream:
            stream.write(b"corruption")
        with self.assertRaises(ValueError):
            self.client.download(job_id, self.temporary.name)
        self.assertFalse(os.path.exists(os.path.join(self.temporary.name, job_id, "motion.json")))

    def test_start_reuses_existing_bridge(self):
        """Connecting to an existing service never launches a subprocess."""
        with patch.object(kimodo.subprocess, "Popen") as launch:
            self.assertEqual("ready", self.connection.start_local()["status"])
        launch.assert_not_called()

    def test_unknown_fields_and_models_are_rejected(self):
        """Rejects malformed requests before execution."""
        with self.assertRaisesRegex(RuntimeError, "400"):
            self.client._request("/v1/jobs", {"definition": {}})
        with self.assertRaisesRegex(RuntimeError, "Unsupported model"):
            self.client.submit(kimodo.KimodoGenerationDefinition("Walk", model="nonexistent"))
        self.assertEqual([], self.backend.calls)

    def test_job_store_lock_is_exclusive_and_recoverable(self):
        """Prevents two bridges from marking each other's jobs interrupted."""
        directory = os.path.join(self.temporary.name, "locked_store")
        with kimodo._lock_job_store(directory):
            with self.assertRaises(RuntimeError):
                kimodo._lock_job_store(directory)
        with kimodo._lock_job_store(directory):
            self.assertTrue(os.path.isfile(os.path.join(directory, ".bridge.lock")))

    def test_wait_timeout_does_not_cancel_job(self):
        """Keeps an outstanding job retrievable after a client-side timeout."""
        job_id = uuid.uuid4().hex
        with patch.object(self.client, "status", return_value={"job_id": job_id, "status": "running"}):
            with self.assertRaisesRegex(TimeoutError, job_id):
                self.client.wait(job_id, timeout=0.01, poll_interval=0.01)

    def test_server_cleanup_removes_only_exact_terminal_job(self):
        """Deletes the selected cache entry, retains siblings, and permits idempotent retries."""
        first = self.client.submit(kimodo.KimodoGenerationDefinition("First"))["job_id"]
        second = self.client.submit(kimodo.KimodoGenerationDefinition("Second"))["job_id"]
        self.client.wait(first, timeout=5, poll_interval=0.01)
        self.client.wait(second, timeout=5, poll_interval=0.01)
        self.assertEqual(True, self.client.delete_job(first)["deleted"])
        self.assertFalse(os.path.exists(os.path.join(self.state.directory, first)))
        self.assertEqual("succeeded", self.client.status(second)["status"])
        self.assertEqual(True, self.client.delete_job(first)["already_absent"])
        with self.assertRaises(ValueError):
            self.client.delete_job("../outside")

    def test_server_cleanup_requires_confirmation_and_authentication(self):
        """Destructive API calls need the exact ID and the same bearer authorization."""
        job_id = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))["job_id"]
        self.client.wait(job_id, timeout=5, poll_interval=0.01)
        with self.assertRaisesRegex(RuntimeError, "confirmation"):
            self.client._request(f"/v1/jobs/{job_id}/delete", {})
        self.connection.token = "wrong"
        with self.assertRaisesRegex(RuntimeError, "403"):
            self.client.delete_job(job_id)
        self.assertTrue(os.path.isdir(os.path.join(self.state.directory, job_id)))

    def test_cleanup_rejects_active_job_until_cancellation_finishes(self):
        """No directory is removed under the generation worker, even after cancellation is requested."""
        entered, release = threading.Event(), threading.Event()

        def blocked(definition, directory, update):
            """Waits until the test lets this worker reach a cancellation checkpoint.

            Args:
                definition (dict): Unused generation request.
                directory (str): Owned test output directory.
                update (callable): Checks cooperative cancellation.

            Returns:
                dict: Empty test provenance.
            """
            entered.set()
            release.wait(timeout=5)
            update(stage="test checkpoint")
            return {}

        with patch.object(self.backend, "generate", side_effect=blocked):
            job_id = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))["job_id"]
            self.assertTrue(entered.wait(timeout=5))
            try:
                with self.assertRaisesRegex(RuntimeError, "Cancel this job"):
                    self.client.delete_job(job_id)
                self.client.cancel(job_id)
                with self.assertRaisesRegex(RuntimeError, "Cancel this job"):
                    self.client.delete_job(job_id)
            finally:
                release.set()
            with self.assertRaises(RuntimeError):
                self.client.wait(job_id, timeout=5, poll_interval=0.01)
            self.assertEqual(True, self.client.delete_job(job_id)["deleted"])

    def test_missing_download_can_be_repaired_without_overwrite(self):
        """Reuses verified files and restores only absent files in the original folder."""
        job_id = self.client.submit(kimodo.KimodoGenerationDefinition("Walk"))["job_id"]
        self.client.wait(job_id, timeout=5, poll_interval=0.01)
        paths = self.client.download(job_id, self.temporary.name)
        timestamp = os.stat(paths["definition.json"]).st_mtime_ns
        os.remove(paths["motion.json"])
        repaired = self.client.download(job_id, self.temporary.name, reuse_existing=True)
        self.assertEqual(paths, repaired)
        self.assertEqual(timestamp, os.stat(paths["definition.json"]).st_mtime_ns)
        self.assertTrue(os.path.isfile(paths["motion.json"]))

    def test_old_bridge_cleanup_fails_without_forgetting_data(self):
        """Does not mistake an old server's unknown endpoint for successful deletion."""
        with patch.object(self.client, "health", return_value={"protocol_version": 2}):
            with self.assertRaisesRegex(ValueError, "Restart"):
                self.client.delete_job(uuid.uuid4().hex)

    def test_old_bridge_shutdown_explains_one_time_manual_stop(self):
        """Never treats an unsupported admin endpoint as a completed stop."""
        with patch.object(self.client, "health", return_value={"protocol_version": 2}):
            with self.assertRaisesRegex(ValueError, "manually"):
                self.client.shutdown()

    def test_restart_marks_incomplete_jobs_failed(self):
        """Preserves successful results while surfacing interrupted generation."""
        directory = os.path.join(self.temporary.name, "restart_store")
        job_id = uuid.uuid4().hex
        os.makedirs(os.path.join(directory, job_id))
        kimodo._write_json(os.path.join(directory, job_id, "result.json"),
                           {"job_id": job_id, "status": "running"})
        recovered = kimodo._BridgeState(directory, self.backend)
        try:
            self.assertEqual("failed", recovered.get(job_id)["status"])
            self.assertEqual("interrupted", recovered.get(job_id)["stage"])
        finally:
            recovered.pending.put(None)
            recovered.worker.join(timeout=5)

    def test_download_job_and_skeleton_endpoint(self):
        """Tracks downloads independently from generation and discovers skeleton data."""
        job = self.client.download_model(kimodo.DEFAULT_MODEL)
        result = self.client.wait(job["job_id"], timeout=5, poll_interval=0.01)
        self.assertEqual("download_model", result["operation"])
        self.assertEqual(kimodo.DEFAULT_MODEL, result["resolved"]["model"])
        self.assertEqual("somaskel77", self.client.skeleton()["skeleton"]["id"])

    def test_queued_cancellation_does_not_run_backend(self):
        """Honors cancellation before entering the generation implementation."""
        entered = threading.Event()
        release = threading.Event()
        original = self.backend.generate

        def blocked(definition, directory, update):
            """Holds the first job so another can be cancelled while queued.

            Args:
                definition (dict): Request data.
                directory (str): Job cache directory.
                update (callable): Status reporter.

            Returns:
                dict: Resolved test parameters.
            """
            entered.set()
            release.wait(timeout=5)
            return original(definition, directory, update)

        with patch.object(self.backend, "generate", side_effect=blocked):
            first = self.client.submit(kimodo.KimodoGenerationDefinition("First"))
            self.assertTrue(entered.wait(timeout=5))
            second = self.client.submit(kimodo.KimodoGenerationDefinition("Second"))
            self.client.cancel(second["job_id"])
            release.set()
            self.client.wait(first["job_id"], timeout=5, poll_interval=0.01)
            with self.assertRaisesRegex(RuntimeError, "Cancelled"):
                self.client.wait(second["job_id"], timeout=5, poll_interval=0.01)
        self.assertEqual(1, len(self.backend.calls))


if __name__ == "__main__":
    unittest.main()
