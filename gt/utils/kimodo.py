"""Scriptable Kimodo bridge, client, and Maya skeleton import utilities.

Importing this module requires only the standard library. Run this file with
the Kimodo environment's Python and ``--serve`` to start the bridge. Kimodo
imports belong exclusively to the server runtime; Maya imports belong to the
scene importer. See ``assets/kimodo/kimodo.md`` in the workspace for examples,
or the Kimodo Generator section of the repository's ``docs/README.md``.
"""

import argparse
import copy
import hashlib
import json
import logging
import math
import os
import platform
import queue
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if not __package__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gt.core.io import read_json_dict as _read_json, write_json


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
PROTOCOL_VERSION = 2
SCHEMA_VERSION = 1
DEFAULT_URL = "http://127.0.0.1:7861"
DEFAULT_MODEL = "kimodo-soma-rp-v1.1"
TERMINAL_STATUSES = ("succeeded", "failed", "cancelled")
ARTIFACT_NAMES = ("motion.json", "motion.npz", "definition.json")
BRIDGE_FEATURES = ("delete_jobs", "shutdown", "runtime_status")


def _write_json(path, data):
    """Atomically publishes JSON using the repository's shared writer.

    Args:
        path (str): Destination inside an owned job directory.
        data (object): JSON-compatible data.
    """
    temporary = f"{path}.{uuid.uuid4().hex}.tmp"
    try:
        json.dumps(data, allow_nan=False)  # Reject NaN before the permissive shared writer.
        if write_json(temporary, data) is None:
            raise OSError(f"Could not write {path}.")
        os.replace(temporary, path)
    finally:
        if os.path.isfile(temporary):
            os.remove(temporary)


def normalize_definition(data):
    """Flattens a Generator setup or validates an existing generation definition.

    Args:
        data (dict): Setup or portable definition.

    Returns:
        dict: Independent validated definition, with enabled constraints only.
    """
    if not isinstance(data, dict):
        raise ValueError("Expected a Kimodo definition or Generator setup object.")
    if "definition" in data:
        definition = copy.deepcopy(data["definition"])
        if "constraints" in data:
            definition["constraints"] = [copy.deepcopy(entry["parameters"])
                                         for entry in data["constraints"] if entry.get("enabled", True)]
    else:
        definition = data
    return KimodoGenerationDefinition.from_dict(definition).as_dict()


def artifact_digest(path):
    """Hashes a file in bounded chunks.

    Args:
        path (str): File to verify.

    Returns:
        str: SHA256 digest.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scene_frames(text):
    """Parses comma-separated frames and inclusive start:end[:step] ranges.

    Args:
        text (str): Scene-frame expression, including fractional frames if needed.

    Returns:
        list: Sorted unique finite frames.
    """
    frames = set()
    for token in str(text or "").split(","):
        if not token.strip():
            continue
        values = [float(value.strip()) for value in token.split(":")]
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Frames must be finite.")
        if len(values) == 1:
            frames.add(values[0])
        elif len(values) in (2, 3):
            start, end = values[:2]
            step = values[2] if len(values) == 3 else 1
            if end < start or step <= 0 or (end - start) / step > 100000:
                raise ValueError("Frame ranges require increasing bounds and a positive, bounded step.")
            frames.update(start + index * step for index in range(int((end - start) / step) + 1))
        else:
            raise ValueError(f"Invalid frame expression: {token}")
        if len(frames) > 100000:
            raise ValueError("Too many requested frames.")
    return sorted(frames)


def map_constraint_frames(frames, start, end, source_fps, model_fps, frame_count=None):
    """Maps source times to zero-based model samples and rejects quantization collisions.

    Args:
        frames (list): Source times.
        start (float): Source range start.
        end (float): Source range end.
        source_fps (float): Source timeline sample rate.
        model_fps (float): Target model sample rate.
        frame_count (int, optional): Retime to this count; otherwise preserve timestamps.

    Returns:
        tuple: Destination indices and total frame count.
    """
    if source_fps <= 0 or model_fps <= 0 or end <= start:
        raise ValueError("Frame rates and range must be positive.")
    count = frame_count or int(math.floor((end - start) * model_fps / source_fps + 0.5)) + 1
    if count < 2:
        raise ValueError("Duration must produce at least two model frames.")
    ratio = (count - 1) / (end - start) if frame_count else model_fps / source_fps
    indices = [int(math.floor((frame - start) * ratio + 0.5)) for frame in frames]
    if any(index < 0 or index >= count for index in indices):
        raise ValueError("Pose falls outside the generated clip.")
    if len(set(indices)) != len(indices):
        raise ValueError("Distinct source poses map to the same model frame; reduce capture density.")
    return indices, count


def distribute_constraint_frames(key_count, frame_count):
    """Spreads ordered constraint keys across the full generated clip.

    Args:
        key_count (int): Number of ordered path transforms.
        frame_count (int): Number of generated clip frames.

    Returns:
        list: Zero-based, evenly distributed destination frames.

    Raises:
        ValueError: If fewer than two keys or insufficient clip frames are provided.
    """
    if type(key_count) is not int or type(frame_count) is not int or key_count < 2 or frame_count < 2:
        raise ValueError("Automatic path timing requires at least two transforms and two generated frames.")
    if key_count > frame_count:
        raise ValueError("There are more path transforms than generated frames; reduce the selected transforms.")
    return [int(math.floor(index * (frame_count - 1) / (key_count - 1) + 0.5)) for index in range(key_count)]


def set_definition_frame_count(definition, count, fps):
    """Scales prompt durations to yield exactly the requested bridge sample count.

    Args:
        definition (dict): Mutable definition.
        count (int): Required total count.
        fps (float): Model rate.
    """
    prompts = definition["prompts"]
    total = sum(prompt["duration_seconds"] for prompt in prompts)
    counts = [int(count * prompt["duration_seconds"] / total) for prompt in prompts]
    counts[-1] += count - sum(counts)
    minimum = definition["parameters"]["transition_frames"] + 1 if len(prompts) > 1 else 2
    if any(value < minimum for value in counts):
        raise ValueError("Prompt segments are too short for the requested duration/transition.")
    for prompt, samples in zip(prompts, counts):
        duration = samples / fps
        # The bridge truncates seconds * fps; guard binary floating-point underflow.
        if int(duration * fps) < samples:
            duration = math.nextafter(duration, math.inf)
        prompt["duration_seconds"] = duration


def _positive_number(value, name, maximum=None):
    """Validates a finite positive numeric value.

    Args:
        value (object): Candidate number.
        name (str): Field used in errors.
        maximum (float, optional): Inclusive upper bound.

    Returns:
        float: Validated value.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    if not math.isfinite(value) or value <= 0 or (maximum and value > maximum):
        raise ValueError(f"Invalid {name}: {value}.")
    return float(value)


class KimodoGenerationDefinition:
    """Stores portable prompts, native constraints, and generation parameters."""

    def __init__(self, prompt, duration_seconds=4.0, model=DEFAULT_MODEL,
                 seed=12345, diffusion_steps=100, postprocess=True, name="Motion",
                 prompts=None, constraints=None, num_samples=1, guidance=None,
                 transition_frames=5, heading=0.0, auto_humanik=True,
                 limit_body_joint_translations=True):
        """Creates and validates a generation definition.

        Args:
            prompt (str): Complete motion description; punctuation is preserved.
            duration_seconds (float): Requested duration, at most 30 seconds.
            model (str): Explicit model key returned by capabilities.
            seed (int or None): Random seed; None selects one on the server.
            diffusion_steps (int): Denoising steps from 1 through 1000.
            postprocess (bool): Whether to apply Kimodo foot cleanup.
            name (str): User-facing label.
            prompts (list, optional): Ordered text/duration segment dictionaries.
            constraints (list, optional): Kimodo constraint dictionaries.
            num_samples (int): Number of alternatives, from 1 through 8.
            guidance (list, optional): Text and constraint guidance weights.
            transition_frames (int): Blending frames between segments.
            heading (float): Initial heading in radians.
            auto_humanik (bool): Add HumanIK when this definition creates a pose skeleton.
                Local Maya authoring option; never sent to the generation server.
            limit_body_joint_translations (bool): Keep non-root joint translations at their rest offsets
                on pose skeletons created from this definition. Local Maya authoring option.
        """
        self.data = {
            "schema_version": SCHEMA_VERSION,
            "id": uuid.uuid4().hex,
            "name": name,
            "model": model,
            "prompts": copy.deepcopy(prompts) if prompts is not None else [
                {"text": prompt, "duration_seconds": duration_seconds}],
            "parameters": {"seed": seed, "num_samples": num_samples,
                           "diffusion_steps": diffusion_steps, "postprocess": postprocess,
                           "guidance": guidance or [2.0, 2.0], "transition_frames": transition_frames,
                           "heading": heading},
            "constraints": copy.deepcopy(constraints or []),
            "maya": {"auto_humanik": auto_humanik,
                     "limit_body_joint_translations": limit_body_joint_translations},
        }
        self.validate()

    def validate(self):
        """Rejects invalid or unsupported generation settings.

        Returns:
            KimodoGenerationDefinition: This validated definition.
        """
        data = self.data
        expected = {"schema_version", "id", "name", "model", "prompts", "parameters", "constraints"}
        if not isinstance(data, dict) or set(data) - {"maya"} != expected:
            raise ValueError("Definition fields do not match schema version 1.")
        options = data.setdefault("maya", {})
        if not isinstance(options, dict):
            raise ValueError("maya options must be a dictionary.")
        options.setdefault("auto_humanik", True)
        options.setdefault("limit_body_joint_translations", True)
        if (set(options) != {"auto_humanik", "limit_body_joint_translations"}
                or any(type(value) is not bool for value in options.values())):
            raise ValueError("maya requires boolean auto_humanik and limit_body_joint_translations options.")
        if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
            raise ValueError("Unsupported definition schema version.")
        for key in ("id", "name", "model"):
            if not isinstance(data[key], str) or not data[key].strip():
                raise ValueError(f"{key} must be a nonempty string.")
        prompts = data["prompts"]
        if not isinstance(prompts, list) or not 1 <= len(prompts) <= 16:
            raise ValueError("Provide between 1 and 16 prompt segments.")
        for segment in prompts:
            if not isinstance(segment, dict) or set(segment) != {"text", "duration_seconds"}:
                raise ValueError("A prompt requires text and duration_seconds.")
            if not isinstance(segment["text"], str) or not segment["text"].strip():
                raise ValueError("Prompt text cannot be empty.")
            if len(segment["text"]) > 10000:
                raise ValueError("Prompt text exceeds 10000 characters.")
            _positive_number(segment["duration_seconds"], "duration_seconds", maximum=30)
        if sum(segment["duration_seconds"] for segment in prompts) > 120:
            raise ValueError("Total duration cannot exceed 120 seconds.")
        validate_constraints(data["constraints"])
        parameters = data["parameters"]
        required_parameters = {"seed", "num_samples", "diffusion_steps", "postprocess"}
        optional_parameters = {"guidance", "transition_frames", "heading"}
        if (not isinstance(parameters, dict) or not required_parameters <= set(parameters)
                or set(parameters) - required_parameters - optional_parameters):
            raise ValueError("Unsupported generation parameter fields.")
        if type(parameters["num_samples"]) is not int or not 1 <= parameters["num_samples"] <= 8:
            raise ValueError("Choose 1 through 8 samples.")
        parameters.setdefault("guidance", [2.0, 2.0])
        parameters.setdefault("transition_frames", 5)
        parameters.setdefault("heading", 0.0)
        _finite_array(parameters["guidance"], (2,), "guidance")
        if any(not 0 <= weight <= 20 for weight in parameters["guidance"]):
            raise ValueError("Guidance must be between 0 and 20.")
        _finite_array(parameters["heading"], (), "heading")
        if type(parameters["transition_frames"]) is not int or not 1 <= parameters["transition_frames"] <= 60:
            raise ValueError("Transition frames must be between 1 and 60.")
        steps = parameters["diffusion_steps"]
        if type(steps) is not int or not 1 <= steps <= 1000:
            raise ValueError("diffusion_steps must be an integer from 1 through 1000.")
        seed = parameters["seed"]
        if seed is not None and (type(seed) is not int or not 0 <= seed < 2 ** 32):
            raise ValueError("seed must be None or an unsigned 32-bit integer.")
        if type(parameters["postprocess"]) is not bool:
            raise ValueError("postprocess must be a boolean.")
        return self

    def as_dict(self):
        """Returns a detached, validated JSON-compatible definition.

        Returns:
            dict: Definition data.
        """
        self.validate()
        return copy.deepcopy(self.data)

    @classmethod
    def from_dict(cls, data):
        """Loads and validates a serialized definition.

        Args:
            data (dict): Serialized definition.

        Returns:
            KimodoGenerationDefinition: Independent definition instance.
        """
        instance = cls.__new__(cls)
        instance.data = copy.deepcopy(data)
        return instance.validate()

    def create_pose_skeleton(self, skeleton_motion, namespace="kimodo_pose", humanik_settings=None):
        """Creates an editable pose source using this definition's local Maya option.

        Args:
            skeleton_motion (dict): One-frame rest motion from client.skeleton().
            namespace (str): Unused Maya namespace.
            humanik_settings (dict, optional): Mapping/stance/name overrides; blank uses Kimodo defaults.

        Returns:
            dict: Created joints, group, and humanik character name (or None).
        """
        self.validate()
        return create_pose_skeleton(
            skeleton_motion, namespace, self.data["maya"]["auto_humanik"], humanik_settings,
            self.data["maya"]["limit_body_joint_translations"])


class KimodoConnection:
    """Describes an HTTP connection and optional local launch configuration."""

    def __init__(self, url=DEFAULT_URL, mode="existing", python_path=None,
                 distribution=None, token=None, timeout=10.0, device="auto",
                 text_encoder_url="http://127.0.0.1:9550", start_encoder=True,
                 show_console=True):
        """Creates a connection without starting processes or importing runtimes.

        Args:
            url (str): Bridge HTTP(S) URL, not the demo's URL.
            mode (str): Existing server, native Windows, or WSL: existing/native/wsl.
            python_path (str, optional): Absolute Kimodo environment folder or Python path.
            distribution (str, optional): WSL distribution name, required for WSL.
            token (str, optional): Bearer token for a configured bridge.
            timeout (float): Per-request timeout in seconds.
            device (str): Local generation device: auto, cpu, or cuda.
            text_encoder_url (str): Encoder URL used for local startup.
            start_encoder (bool): Start a missing local encoder automatically.
            show_console (bool): Open a visible Windows console for a launched bridge.
        """
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("A valid HTTP(S) bridge URL is required.")
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("Use a bridge origin URL without credentials, query, or path.")
        if mode not in ("existing", "native", "wsl"):
            raise ValueError("mode must be existing, native, or wsl.")
        if device not in ("auto", "cpu", "cuda"):
            raise ValueError("device must be auto, cpu, or cuda.")
        self.url = url.rstrip("/")
        self.mode = mode
        self.python_path = python_path
        self.distribution = distribution
        self.token = token
        self.timeout = _positive_number(timeout, "timeout")
        self.device = device
        self.text_encoder_url = text_encoder_url
        self.start_encoder = start_encoder
        self.show_console = show_console
        self.process = None
        self.log_path = None

    @staticmethod
    def _process_detail(process_result):
        """Extracts readable stdout or stderr from a subprocess result or error.

        Args:
            process_result (object): CompletedProcess, CalledProcessError, or TimeoutExpired.

        Returns:
            str: Decoded diagnostic text, or an empty string.
        """
        payload = getattr(process_result, "stderr", None) or getattr(process_result, "stdout", None)
        if isinstance(payload, bytes):
            return payload.decode("utf-8", errors="replace").strip()
        return str(payload or "").strip()

    def _resolve_wsl_python(self):
        """Resolves a WSL environment folder to its executable without a shell.

        Returns:
            str: Absolute Linux Python executable path.
        """
        if not self.distribution or not self.python_path or not self.python_path.startswith("/"):
            raise ValueError("WSL requires a distribution and absolute Linux Python path or environment folder.")
        path = self.python_path.rstrip("/")
        basename = path.rsplit("/", 1)[-1].lower()
        if basename.startswith("python") or basename.startswith("pypy"):
            return path
        if basename == "bin":
            candidates = [f"{path}/python", f"{path}/python3"]
        else:
            candidates = [f"{path}/bin/python", f"{path}/bin/python3",
                          f"{path}/python", f"{path}/python3"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        last_detail = ""
        for candidate in candidates:
            try:
                result = subprocess.run(
                    ["wsl.exe", "--distribution", self.distribution, "--exec",
                     "test", "-f", candidate, "-a", "-x", candidate],
                    capture_output=True, timeout=15, creationflags=flags)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ValueError(
                    f"Could not inspect the Python environment in WSL distribution "
                    f"{self.distribution}: {error}") from error
            if result.returncode == 0:
                self.python_path = candidate
                return candidate
            last_detail = self._process_detail(result) or last_detail
        detail = f" WSL reported: {last_detail}" if last_detail else ""
        raise ValueError(
            f"No executable Python was found under {path} in WSL distribution "
            f"{self.distribution}. Select the environment folder or its bin/python executable.{detail}")

    def _resolve_native_python(self):
        """Resolves a Windows environment folder to its executable.

        Returns:
            str: Absolute native Python executable path.
        """
        if not self.python_path or not os.path.isabs(self.python_path):
            raise ValueError("Native launch requires an absolute Python path or environment folder.")
        path = os.path.abspath(self.python_path)
        if os.path.isfile(path):
            return path
        if os.path.isdir(path):
            for relative in ("python.exe", "Scripts/python.exe", "bin/python.exe", "bin/python"):
                candidate = os.path.join(path, *relative.split("/"))
                if os.path.isfile(candidate):
                    self.python_path = candidate
                    return candidate
        raise ValueError(
            f"No Python executable was found at {path}. Select the Kimodo environment folder or python.exe.")

    def _python_command(self):
        """Builds a shell-free command for the selected Python environment.

        Returns:
            list[str]: Subprocess argument list.
        """
        if not self.python_path:
            raise ValueError("Set python_path to the Kimodo environment folder or Python executable.")
        if self.mode == "wsl":
            executable = self._resolve_wsl_python()
            return ["wsl.exe", "--distribution", self.distribution, "--exec", executable]
        if self.mode != "native":
            raise ValueError("Local launch mode must be native or wsl.")
        executable = self._resolve_native_python()
        return [executable]

    def validate_local_launch(self):
        """Validates that this connection can safely launch on the configured localhost.

        Returns:
            list[str]: Shell-free Python command for the selected local runtime.
        """
        if self.mode == "existing":
            raise ValueError("Choose Start in WSL or Start on Windows to launch or restart a bridge.")
        parsed = urllib.parse.urlsplit(self.url)
        if parsed.hostname not in ("127.0.0.1", "localhost") or parsed.scheme != "http":
            raise ValueError("Local startup requires an http://127.0.0.1 or localhost URL.")
        return self._python_command()

    def start_local(self, startup_timeout=90.0, log_directory=None):
        """Starts or reconnects to a local bridge, without installing dependencies.

        WSL receives this module and shared core.io over standard input,
        so network drives and WSL mounts need no manual configuration. Model and
        encoder initialization happen on the first job, with visible job stages.

        Args:
            startup_timeout (float): Maximum bridge readiness wait in seconds.
            log_directory (str, optional): Local directory for process logs.

        Returns:
            dict: Ready bridge health response.
        """
        _positive_number(startup_timeout, "startup_timeout")
        client = KimodoClient(self)
        try:
            return client.health()
        except (ConnectionError, OSError):
            pass
        if self.mode == "existing":
            raise ConnectionError(f"No bridge reachable at {self.url}.")
        parsed = urllib.parse.urlsplit(self.url)
        command = self.validate_local_launch()
        environment = os.environ.copy()
        for key in ("PYTHONHOME", "PYTHONPATH"):
            environment.pop(key, None)
        environment.update(PYTHONUNBUFFERED="1", PYTHONUTF8="1")
        hidden_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        script_path = os.path.abspath(__file__)
        if self.mode == "wsl":
            from gt.core import io as core_io

            with open(script_path, encoding="utf-8") as stream:
                bridge_source = stream.read()
            with open(core_io.__file__, encoding="utf-8") as stream:
                io_source = stream.read()
            source = json.dumps({"gt/utils/kimodo.py": bridge_source, "gt/core/io.py": io_source}).encode("utf-8")
            bootstrap = (
                "import hashlib,pathlib,sys,json; source=sys.stdin.buffer.read(); "
                "digest=hashlib.sha256(source).hexdigest(); "
                "folder=pathlib.Path.home()/'.cache'/'gt-tools'/'kimodo'/digest; "
                "files=json.loads(source); "
                "[(folder/path).parent.mkdir(parents=True,exist_ok=True) for path in files]; "
                "[(folder/path).write_text(content,encoding='utf-8') for path,content in files.items()]; "
                "[(folder/path).touch() for path in ('gt/__init__.py','gt/core/__init__.py','gt/utils/__init__.py')]; "
                "print(folder/'gt/utils/kimodo.py')"
            )
            try:
                deployed = subprocess.run(command + ["-c", bootstrap], input=source,
                                          capture_output=True, timeout=60, env=environment,
                                          creationflags=hidden_flags, check=True)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                detail = self._process_detail(error)
                suffix = f" WSL output: {detail}" if detail else ""
                raise RuntimeError(
                    f"Could not deploy the Kimodo bridge using {command[-1]} in WSL distribution "
                    f"{self.distribution}.{suffix}") from error
            script_path = deployed.stdout.decode("utf-8").strip()
            if not script_path.startswith("/") or "\n" in script_path:
                raise RuntimeError("WSL returned an invalid bridge deployment path.")
        arguments = command + ["-u", "-X", "utf8", script_path, "--serve", "--port", str(parsed.port or 80),
                               "--device", self.device, "--text-encoder-url", self.text_encoder_url]
        if not self.start_encoder:
            arguments.append("--no-start-encoder")
        if self.token:
            arguments += ["--token", self.token]
        visible_console = bool(self.show_console and os.name == "nt"
                               and getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        if visible_console:
            self.log_path = None
            self.process = subprocess.Popen(
                arguments, env=environment,
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        else:
            log_directory = log_directory or os.path.join(tempfile.gettempdir(), "gt_kimodo")
            os.makedirs(log_directory, exist_ok=True)
            self.log_path = os.path.join(log_directory, f"bridge_{uuid.uuid4().hex}.log")
            with open(self.log_path, "xb") as stream:
                self.process = subprocess.Popen(
                    arguments, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                    env=environment, creationflags=hidden_flags)
        deadline = time.monotonic() + startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                destination = self.log_path or "the bridge console window"
                raise RuntimeError(f"Bridge exited during startup. See {destination}.")
            try:
                return client.health()
            except (ConnectionError, OSError):
                time.sleep(0.25)
        destination = self.log_path or "the bridge console window"
        raise TimeoutError(f"Bridge readiness timed out. Process may still be starting. See {destination}.")


class KimodoClient:
    """Exposes generation without importing Kimodo, Maya, or third-party clients."""

    def __init__(self, connection=None):
        """Creates a client.

        Args:
            connection (KimodoConnection, optional): Server connection settings.
        """
        self.connection = connection or KimodoConnection()
        # Local traffic should not be redirected through machine proxy settings.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _request(self, path, data=None):
        """Sends an HTTP JSON request and reports actionable failures.

        Args:
            path (str): Relative API path.
            data (dict, optional): JSON body; when present, uses POST.

        Returns:
            dict: Decoded server response.
        """
        body = None if data is None else json.dumps(data, allow_nan=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.connection.token:
            headers["Authorization"] = f"Bearer {self.connection.token}"
        request = urllib.request.Request(self.connection.url + path, data=body, headers=headers)
        try:
            with self.opener.open(request, timeout=self.connection.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                detail = error.read().decode("utf-8", errors="replace")[:2000]
            raise RuntimeError(f"Kimodo HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, OSError) as error:
            raise ConnectionError(f"Cannot reach Kimodo bridge at {self.connection.url}: {error}") from error
        except (ValueError, UnicodeError) as error:
            raise RuntimeError("Server did not return bridge JSON. Check the URL; the demo uses port 7860.") from error

    def health(self):
        """Checks bridge identity and protocol compatibility.

        Returns:
            dict: Service health and readiness.
        """
        result = self._request("/v1/health")
        if result.get("service") != "gt-kimodo" or result.get("protocol_version") != PROTOCOL_VERSION:
            raise RuntimeError("Bridge update required. Restart the Kimodo bridge using the current utility.")
        return result

    def shutdown(self):
        """Gracefully stops an idle bridge while preserving jobs, models, and encoder.

        Returns:
            dict: Shutdown acknowledgement and the stopped bridge runtime details.
        """
        health = self.health()
        if "shutdown" not in health.get("features", []):
            raise ValueError("This older bridge cannot be stopped from Maya. Stop it once manually, then use "
                             "Connect / Start to deploy the current bridge; future restarts can use this button.")
        return self._request("/v1/admin/shutdown", {"confirm": "shutdown"})

    def capabilities(self):
        """Gets supported models and generation limits.

        Returns:
            dict: Backend capability description.
        """
        return self._request("/v1/capabilities")

    def skeleton(self):
        """Gets a SOMA rest-pose motion for authoring constraints.

        Returns:
            dict: Importable one-frame rest skeleton.
        """
        return self._request("/v1/skeleton")

    def download_model(self, model):
        """Queues a Hugging Face model download in the server environment.

        Args:
            model (str): Model ID advertised by capabilities.

        Returns:
            dict: Trackable download job.
        """
        return self._request("/v1/models/download", {"job_id": uuid.uuid4().hex, "model": model})

    def submit(self, definition, job_id=None):
        """Submits one job; reuse job_id to safely retry an uncertain submission.

        Args:
            definition (KimodoGenerationDefinition): Validated generation request.
            job_id (str, optional): Caller-generated UUID hex for idempotent retries.

        Returns:
            dict: Accepted job, including its ID.
        """
        job_id = job_id or uuid.uuid4().hex
        _validate_job_id(job_id)
        payload = definition.as_dict()
        payload.pop("maya", None)  # Authoring options must not change the bridge protocol.
        return self._request("/v1/jobs", {"job_id": job_id, "definition": payload})

    def status(self, job_id):
        """Gets the latest persisted job status.

        Args:
            job_id (str): Submitted job ID.

        Returns:
            dict: Job status, stages, and artifacts when complete.
        """
        _validate_job_id(job_id)
        return self._request(f"/v1/jobs/{job_id}")

    def cancel(self, job_id):
        """Requests cooperative cancellation of an owned generation job.

        Args:
            job_id (str): Submitted job identifier.

        Returns:
            dict: Updated job status.
        """
        _validate_job_id(job_id)
        return self._request(f"/v1/jobs/{job_id}/cancel", {})

    def delete_job(self, job_id):
        """Permanently deletes one terminal server job and all of its server artifacts.

        Running/queued jobs must first be cancelled and reach a terminal state.
        Model weights, the text encoder and other jobs are never removed.

        Args:
            job_id (str): Exact completed/cancelled/failed job identifier.

        Returns:
            dict: Deletion acknowledgement, including whether it was already absent.
        """
        _validate_job_id(job_id)
        if "delete_jobs" not in self.health().get("features", []):
            raise ValueError("This bridge predates job cleanup. Restart the Kimodo bridge with the updated "
                             "gt-tools code, then retry. No new WSL dependencies are needed. History was retained.")
        return self._request(f"/v1/jobs/{job_id}/delete", {"confirm": job_id})

    def wait(self, job_id, timeout=1200.0, poll_interval=1.0):
        """Waits synchronously for a terminal job state.

        This blocks the calling thread. Interactive Maya scripts can submit,
        return control to Maya, and call status/download later instead.

        Args:
            job_id (str): Submitted job ID.
            timeout (float): Total wait limit; expiration does not cancel the job.
            poll_interval (float): Delay between status checks.

        Returns:
            dict: Successful job result.
        """
        _positive_number(timeout, "timeout")
        _positive_number(poll_interval, "poll_interval")
        deadline = time.monotonic() + timeout
        while True:
            result = self.status(job_id)
            if result["status"] == "succeeded":
                return result
            if result["status"] in ("failed", "cancelled"):
                raise RuntimeError(f"Kimodo job {job_id} failed: {result.get('error', 'Unknown error')}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Job {job_id} is still {result['status']}; reconnect with status(job_id).")
            time.sleep(min(poll_interval, remaining))

    def download(self, job_id, directory, reuse_existing=False):
        """Downloads verified artifacts into a new per-job directory.

        Existing files are never overwritten. With reuse enabled, verified files
        are reused and missing files are downloaded. Unverified partials remain
        available for diagnosis; use a different destination after a partial failure.

        Args:
            job_id (str): Completed job ID.
            directory (str): Local parent directory for the new job folder.
            reuse_existing (bool): Reuse verified files and repair missing artifacts.

        Returns:
            dict: Artifact names mapped to absolute local paths.
        """
        result = self.status(job_id)
        if result["status"] != "succeeded":
            raise RuntimeError(f"Job {job_id} is {result['status']}, not ready for download.")
        if not directory or not os.path.isabs(directory):
            raise ValueError("Use an absolute local download directory.")
        destination = os.path.join(directory, job_id)
        if os.path.lexists(destination):
            _validate_job_directory(directory, job_id)
        if reuse_existing and os.path.isdir(destination):
            manifest = os.path.join(destination, "result.json")
            if os.path.isfile(manifest) and _read_json(manifest).get("job_id") != job_id:
                raise ValueError("Existing download manifest belongs to a different job.")
            paths = {}
            for artifact in result["artifacts"]:
                name = artifact["name"]
                if not _is_artifact(name):
                    raise ValueError(f"Unexpected artifact: {name}")
                path = os.path.join(destination, name)
                if not os.path.isfile(path):
                    continue  # Missing artifacts may be downloaded again without replacing existing files.
                if os.path.getsize(path) != artifact["size_bytes"] or artifact_digest(path) != artifact["sha256"]:
                    raise ValueError(f"Existing artifact failed verification: {name}")
                paths[name] = path
            manifest = os.path.join(destination, "result.json")
            if len(paths) == len(result["artifacts"]) and os.path.isfile(manifest):
                paths["result.json"] = manifest
                return paths
        else:
            os.makedirs(destination, exist_ok=False)
        paths = {}
        for artifact in result["artifacts"]:
            name = artifact["name"]
            if not _is_artifact(name) or name in paths:
                raise ValueError(f"Unexpected artifact: {name}")
            request = urllib.request.Request(f"{self.connection.url}/v1/jobs/{job_id}/artifacts/{name}")
            if self.connection.token:
                request.add_header("Authorization", f"Bearer {self.connection.token}")
            path = os.path.join(destination, name)
            if reuse_existing and os.path.isfile(path):
                paths[name] = path  # Already checksum-verified in the preflight pass above.
                continue
            if os.path.lexists(path + ".part"):
                raise ValueError(f"Partial artifact already exists: {path}.part. Choose another download folder.")
            digest = hashlib.sha256()
            size = 0
            with self.opener.open(request, timeout=self.connection.timeout) as response:
                with open(path + ".part", "xb") as stream:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > artifact["size_bytes"]:
                            raise ValueError(f"Artifact exceeded expected size: {name}")
                        digest.update(chunk)
                        stream.write(chunk)
            if size != artifact["size_bytes"] or digest.hexdigest() != artifact["sha256"]:
                raise ValueError(f"Artifact verification failed: {name}")
            os.rename(path + ".part", path)
            paths[name] = path
        if not os.path.isfile(os.path.join(destination, "result.json")):
            _write_json(os.path.join(destination, "result.json"), result)
        paths["result.json"] = os.path.join(destination, "result.json")
        return paths


def _validate_job_id(job_id):
    """Rejects identifiers that could escape a job directory or API path.

    Args:
        job_id (str): Lowercase UUID hex identifier.
    """
    if not isinstance(job_id, str) or not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ValueError("job_id must be a lowercase UUID hex string.")


def _is_artifact(name):
    """Checks an artifact filename without accepting filesystem paths.

    Args:
        name (str): Advertised filename.

    Returns:
        bool: Whether this is a supported artifact name.
    """
    return name in ARTIFACT_NAMES or bool(re.fullmatch(r"sample_[0-7]\.(json|npz)", name))


def validate_constraints(constraints, frame_count=None):
    """Validates native Kimodo constraints and conflicting frame assignments.

    Args:
        constraints (list): Kimodo JSON constraint objects.
        frame_count (int, optional): Actual model clip length for bounds checking.

    Returns:
        list: Original validated constraints.
    """
    if not isinstance(constraints, list) or len(constraints) > 256:
        raise ValueError("Provide a list of at most 256 constraints.")
    occupied = set()
    for constraint in constraints:
        if not isinstance(constraint, dict):
            raise ValueError("Each constraint must be an object.")
        kind = constraint.get("type")
        if kind not in ("fullbody", "root2d", "left-hand", "right-hand", "left-foot", "right-foot", "end-effector"):
            raise ValueError(f"Unsupported constraint type: {kind}")
        frames = constraint.get("frame_indices")
        if not isinstance(frames, list) or not frames or len(frames) > 7200:
            raise ValueError("Constraints require nonempty frame_indices.")
        if any(type(frame) is not int or frame < 0 for frame in frames):
            raise ValueError("Constraint frames must be zero-based integers inside the clip.")
        if frame_count is not None and any(frame >= frame_count for frame in frames):
            largest_frame = max(frames)
            raise ValueError(f"Constraint frame {largest_frame + 1} is outside the generated clip. "
                             f"Use frames 1 through {frame_count}.")
        channels = constraint.get("joint_names", [kind]) if kind == "end-effector" else [kind]
        if not isinstance(channels, list) or not channels or any(not isinstance(name, str) for name in channels):
            raise ValueError("End-effector constraints require joint_names.")
        for frame in frames:
            for channel in channels:
                key = (channel, frame)
                if key in occupied:
                    raise ValueError(f"Duplicate {channel} constraint at clip frame {frame + 1}.")
                occupied.add(key)
        count = len(frames)
        if kind == "root2d":
            _finite_array(constraint.get("smooth_root_2d"), (count, 2), "smooth_root_2d")
            if "global_root_heading" in constraint:
                _finite_array(constraint["global_root_heading"], (count,), "global_root_heading")
        else:
            rotations = constraint.get("local_joints_rot")
            if not isinstance(rotations, list) or not rotations or not isinstance(rotations[0], list):
                raise ValueError("Pose constraints require local_joints_rot.")
            joints = len(rotations[0])
            if joints not in (22, 34, 77):
                raise ValueError("Pose constraints must use a supported output skeleton (22, 34, or 77 joints).")
            _finite_array(rotations, (count, joints, 3), "local_joints_rot")
            _finite_array(constraint.get("root_positions"), (count, 3), "root_positions")
            if "smooth_root_2d" in constraint:
                _finite_array(constraint["smooth_root_2d"], (count, 2), "smooth_root_2d")
    return constraints


def find_pose_group(node=None):
    """Resolves an imported or authoring skeleton from a selected descendant.

    Args:
        node (str, optional): Scene object; defaults to the first selected object.

    Returns:
        str: Full path of the Kimodo placement group.
    """
    import maya.cmds as cmds

    selection = cmds.ls(node, long=True) if node else cmds.ls(selection=True, long=True)
    if not selection:
        raise ValueError("Select a Kimodo skeleton or one of its joints.")
    current = selection[0]
    while current:
        if cmds.attributeQuery("kimodoSkeleton", node=current, exists=True):
            return current
        parents = cmds.listRelatives(current, parent=True, fullPath=True) or []
        current = parents[0] if parents else None
    raise ValueError("Use Create Pose Skeleton, or select a skeleton imported by Kimodo Generator.")


def capture_pose(group=None, frame_index=0, constraint_type="fullbody", bone_offset_tolerance=0.0001):
    """Captures current local joint rotations in the placement group's space.

    Args:
        group (str, optional): Kimodo group or selected descendant.
        frame_index (int): Zero-based destination frame in the generated clip.
        constraint_type (str): Full-body or hand/foot constraint type.
        bone_offset_tolerance (float): Maximum non-root translation deviation in meters.
            HumanIK evaluation may introduce small deviations; accepted offsets are
            normalized to the model skeleton, without editing the Maya joints.

    Returns:
        dict: Native JSON-compatible pose constraint with one key.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as om

    _positive_number(bone_offset_tolerance, "bone_offset_tolerance", maximum=0.01)
    group = find_pose_group(group)
    skeleton = json.loads(cmds.getAttr(f"{group}.kimodoSkeleton"))
    joints = cmds.listRelatives(group, allDescendents=True, type="joint", fullPath=True) or []
    by_name = {joint.rsplit("|", 1)[-1].rsplit(":", 1)[-1]: joint for joint in joints}
    if len(by_name) != len(skeleton["joint_names"]):
        raise ValueError("Skeleton hierarchy has changed; use an unmodified Kimodo hierarchy.")
    scale = om.MDistance(1, om.MDistance.uiUnit()).asMeters()
    rotations = []
    for index, name in enumerate(skeleton["joint_names"]):
        joint = by_name[name]
        if any(abs(value - 1) > 0.00001 for value in cmds.getAttr(f"{joint}.scale")[0]):
            raise ValueError("Capture rotation poses without scaling skeleton joints.")
        local = cmds.getAttr(f"{joint}.matrix")
        transform = om.MTransformationMatrix(om.MMatrix(local))
        axis, angle = transform.rotation(asQuaternion=True).asAxisAngle()
        rotations.append([component * angle for component in (axis.x, axis.y, axis.z)])
        translation = [value * scale for value in cmds.getAttr(f"{joint}.translate")[0]]
        if index == 0:
            root = translation
        else:
            expected_offset = skeleton["offsets"][index]
            offset_delta = [actual - expected for actual, expected in zip(translation, expected_offset)]
            if any(abs(value) > bone_offset_tolerance for value in offset_delta):
                expected_text = ", ".join(f"{value:.6f}" for value in expected_offset)
                actual_text = ", ".join(f"{value:.6f}" for value in translation)
                delta_text = ", ".join(f"{value:+.6f}" for value in offset_delta)
                raise ValueError(
                    f"Bone offset changed beyond {bone_offset_tolerance:g} meters: {joint}. "
                    f"Expected local offset (m): [{expected_text}]; found: [{actual_text}]; "
                    f"delta: [{delta_text}]. Pose joints by rotating them; only the root may be translated.")
    constraint = {"type": constraint_type, "frame_indices": [frame_index],
                  "root_positions": [root], "local_joints_rot": [rotations]}
    validate_constraints([constraint])
    return constraint


def capture_root_path(nodes, frame_indices, group=None):
    """Captures timed locator positions or evenly spaced points on a NURBS curve.

    Args:
        nodes (list): Ordered transforms, or one curve transform.
        frame_indices (list): Zero-based destination frames.
        group (str, optional): Placement group defining generation space.

    Returns:
        dict: Root2D constraint.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as om

    if not nodes or not frame_indices:
        raise ValueError("Select ordered locators or one curve, and provide destination frames.")
    scale = om.MDistance(1, om.MDistance.uiUnit()).asMeters()
    inverse = om.MMatrix(cmds.getAttr(f"{group}.worldInverseMatrix[0]")) if group else om.MMatrix()
    positions = []
    shapes = cmds.listRelatives(nodes[0], shapes=True, fullPath=True) or []
    curve = next((shape for shape in shapes if cmds.nodeType(shape) == "nurbsCurve"), None)
    if len(nodes) == 1 and curve:
        selection = om.MSelectionList()
        selection.add(curve)
        function = om.MFnNurbsCurve(selection.getDagPath(0))
        for index in range(len(frame_indices)):
            distance = function.length() * index / max(1, len(frame_indices) - 1)
            positions.append(function.getPointAtParam(function.findParamFromLength(distance), om.MSpace.kWorld))
    elif len(nodes) == len(frame_indices):
        positions = [om.MPoint(cmds.xform(node, query=True, worldSpace=True, translation=True)) for node in nodes]
    else:
        raise ValueError("Ordered locator paths need one locator per destination frame; a single NURBS curve "
                         "can use any number of samples.")
    points = [point * inverse for point in positions]
    if group or cmds.upAxis(query=True, axis=True) == "y":
        coordinates = [[point.x * scale, point.z * scale] for point in points]
    else:
        coordinates = [[point.x * scale, -point.y * scale] for point in points]
    result = {"type": "root2d", "frame_indices": frame_indices, "smooth_root_2d": coordinates}
    validate_constraints([result])
    return result


def probe_text_encoder(url="http://127.0.0.1:9550", timeout=3.0):
    """Checks the configured Kimodo text encoder without computing embeddings.

    Args:
        url (str): Gradio text-encoder origin URL.
        timeout (float): Network timeout in seconds.

    Returns:
        dict: Ready status, URL, and advertised API name.

    Raises:
        ValueError: If the URL is not a clean HTTP(S) origin.
        ConnectionError: If the service cannot be reached.
        RuntimeError: If the responding service is not Kimodo's encoder.
    """
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username):
        raise ValueError("Use a text-encoder origin URL without credentials, query, or path.")
    _positive_number(timeout, "timeout")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url.rstrip("/") + "/config", timeout=timeout) as response:
            config = json.load(response)
    except (urllib.error.URLError, OSError) as error:
        raise ConnectionError(f"Cannot reach Kimodo text encoder at {url}: {error}") from error
    except (ValueError, UnicodeError) as error:
        raise RuntimeError(f"The service at {url} did not return a valid Gradio configuration.") from error
    if not any(item.get("api_name") == "DemoWrapper" for item in config.get("dependencies", [])):
        raise RuntimeError(f"The service at {url} is not the expected Kimodo text encoder.")
    return {"status": "ready", "url": url.rstrip("/"), "api_name": "DemoWrapper"}


def create_pose_skeleton(skeleton_motion, namespace="kimodo_pose", auto_humanik=True, humanik_settings=None,
                         limit_body_joint_translations=True):
    """Creates an unkeyed authoring skeleton, optionally characterized for Maya HumanIK.

    The character can receive other animation through Maya HumanIK to author pose
    constraints. The rest skeleton is grounded by lifting its root until its lowest
    joint reaches the ground plane. No control rig or retargeting is performed here.

    Args:
        skeleton_motion (dict): One-frame rest motion from client.skeleton().
        namespace (str): Unused Maya namespace.
        auto_humanik (bool): Add a default Kimodo HumanIK definition; enabled by default.
        humanik_settings (dict, optional): Optional local characterization overrides.
        limit_body_joint_translations (bool): Restrict non-root body-joint translations to their rest offsets.

    Returns:
        dict: Imported hierarchy metadata, HumanIK name, and limited joint names.
    """
    if type(auto_humanik) is not bool:
        raise ValueError("auto_humanik must be a boolean.")
    if type(limit_body_joint_translations) is not bool:
        raise ValueError("limit_body_joint_translations must be a boolean.")
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Create pose skeletons on Maya's main thread.")
    validate_motion(skeleton_motion)
    if skeleton_motion["frame_count"] != 1:
        raise ValueError("Use one-frame rest motion to create a pose skeleton, not an animation clip.")
    import maya.cmds as cmds

    result = None
    cmds.undoInfo(openChunk=True, chunkName="Create Kimodo Pose Skeleton")
    try:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "pose.json")
            _write_json(path, skeleton_motion)
            result = import_motion(path, namespace=namespace)
        channels = {f"{joint}.{channel}": cmds.getAttr(f"{joint}.{channel}")
                    for joint in result["joints"] for channel in ("tx", "ty", "tz", "rx", "ry", "rz")}
        curves = set(cmds.listConnections(result["joints"], source=True, destination=False, type="animCurve") or [])
        if curves:
            cmds.delete(list(curves))  # Only curves created on this new hierarchy.
        for plug, value in channels.items():
            cmds.setAttr(plug, value)
        up_index = 1 if cmds.upAxis(query=True, axis=True) == "y" else 2
        lowest = min(cmds.xform(joint, query=True, translation=True, worldSpace=True)[up_index]
                     for joint in result["joints"])
        root_plug = f"{result['joints'][0]}.ty"
        cmds.setAttr(root_plug, cmds.getAttr(root_plug) - lowest)
        result["humanik"] = None
        if auto_humanik:
            result["humanik"] = create_humanik_definition(result["group"], humanik_settings)["character"]
        result["translation_limited_joints"] = (
            apply_body_joint_translation_limits(result["joints"]) if limit_body_joint_translations else [])
        return result
    except Exception:
        if result:
            cmds.delete(result["group"])
            cmds.namespace(removeNamespace=f":{namespace}")
        raise
    finally:
        cmds.undoInfo(closeChunk=True)


def apply_body_joint_translation_limits(joints):
    """Limits every body joint after the root to its existing local rest offset.

    Args:
        joints (list): Ordered skeleton joints, with the root joint first.

    Returns:
        list: Joint names with translation limits applied; excludes the root.
    """
    import maya.cmds as cmds

    if not isinstance(joints, (list, tuple)) or not joints:
        raise ValueError("Provide the ordered Kimodo joints, with its root joint first.")
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Apply joint translation limits on Maya's main thread.")
    limited_joints = []
    for joint in joints[1:]:
        translation = cmds.getAttr(f"{joint}.translate")[0]
        limits = {}
        for axis, value in zip("XYZ", translation):
            limits[f"translation{axis}"] = (value, value)
            limits[f"enableTranslation{axis}"] = (True, True)
        cmds.transformLimits(joint, **limits)
        limited_joints.append(joint)
    return limited_joints


def create_humanik_definition(group, settings=None):
    """Adds a source-only Kimodo characterization without launching a UI.

    Args:
        group (str): Imported Kimodo group or descendant.
        settings (dict, optional): Character name, mapping/stance overrides and locking.

    Returns:
        dict: Character, group, mapped-joint count and lock state.
    """
    from gt.tools.kimodo_generator import kimodo_generator_hik

    return kimodo_generator_hik.create_definition(group, settings)


POSE_PREVIEW_ATTRIBUTE = "gtKimodoPosePreview"
PATH_PREVIEW_ATTRIBUTE = "gtKimodoPathPreview"


def preview_pose(constraint, skeleton_motion, namespace="kimodo_pose", template=True, display_name=None):
    """Creates a tracked one-frame preview from the first key of a pose.

    Args:
        constraint (dict): Captured/imported pose constraint.
        skeleton_motion (dict): Matching rest skeleton from the bridge.
        namespace (str): New preview namespace.
        template (bool): Make the preview unselectable and display it as a template.
        display_name (str, optional): Maya-safe name for the preview's root group.

    Returns:
        dict: Imported preview objects.
    """
    import maya.api.OpenMaya as om
    import maya.cmds as cmds

    if type(template) is not bool:
        raise ValueError("template must be a boolean.")
    if display_name is not None and (not isinstance(display_name, str)
                                     or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", display_name)):
        raise ValueError("display_name must be a Maya-safe name.")
    validate_constraints([constraint])
    if constraint["type"] == "root2d":
        raise ValueError("Select a pose constraint to preview.")
    motion = copy.deepcopy(skeleton_motion)
    motion["frame_count"] = 1
    rotations = []
    for vector in constraint["local_joints_rot"][0]:
        axis = om.MVector(vector)
        angle = axis.length()
        quaternion = om.MQuaternion(angle, axis.normal()) if angle > 1e-10 else om.MQuaternion()
        matrix = quaternion.asMatrix()
        rotations.append([[matrix[column * 4 + row] for column in range(3)] for row in range(3)])
    motion["local_rotations"] = [rotations]
    motion["root_positions"] = [constraint["root_positions"][0]]
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "pose.json")
        _write_json(path, motion)
        result = import_motion(path, namespace=namespace)
    group = result["group"]
    if display_name:
        joint_names = [joint.rsplit("|", 1)[-1] for joint in result["joints"]]
        group = cmds.rename(group, f"{namespace}:{display_name}")
        result["group"] = group
        descendants = cmds.listRelatives(group, allDescendents=True, type="joint", fullPath=True) or []
        by_name = {joint.rsplit("|", 1)[-1]: joint for joint in descendants}
        result["joints"] = [by_name[name] for name in joint_names if name in by_name]
    cmds.addAttr(group, longName=POSE_PREVIEW_ATTRIBUTE, attributeType="bool", hidden=True)
    cmds.setAttr(f"{group}.{POSE_PREVIEW_ATTRIBUTE}", True, lock=True, keyable=False, channelBox=False)
    if template:
        nodes = [group] + (cmds.listRelatives(group, allDescendents=True, fullPath=True) or [])
        for node in nodes:
            if cmds.attributeQuery("overrideEnabled", node=node, exists=True):
                cmds.setAttr(f"{node}.overrideEnabled", True)
                cmds.setAttr(f"{node}.overrideDisplayType", 1)
    return result


def remove_pose_previews():
    """Deletes only pose and root-path previews created by the Kimodo tool.

    Returns:
        int: Number of preview skeleton groups removed.
    """
    import maya.cmds as cmds

    groups = []
    for node in cmds.ls(type="transform", long=True) or []:
        markers = (POSE_PREVIEW_ATTRIBUTE, PATH_PREVIEW_ATTRIBUTE)
        if any(cmds.attributeQuery(marker, node=node, exists=True)
               and cmds.getAttr(f"{node}.{marker}") for marker in markers):
            groups.append(node)
    if not groups:
        return 0
    cmds.undoInfo(openChunk=True, chunkName="Remove Kimodo Pose Previews")
    try:
        cmds.delete(groups)
    finally:
        cmds.undoInfo(closeChunk=True)
    return len(groups)


def tag_path_preview(node):
    """Marks a root-path preview transform so the cleanup action can find it.

    Args:
        node (str): Maya transform returned by ``cmds.curve``.
    """
    import maya.cmds as cmds

    if not cmds.objExists(node) or cmds.nodeType(node) != "transform":
        raise ValueError("A root-path preview must be a valid Maya transform.")
    if not cmds.attributeQuery(PATH_PREVIEW_ATTRIBUTE, node=node, exists=True):
        cmds.addAttr(node, longName=PATH_PREVIEW_ATTRIBUTE, attributeType="bool", hidden=True)
    cmds.setAttr(f"{node}.{PATH_PREVIEW_ATTRIBUTE}", True, lock=True, keyable=False, channelBox=False)


def _finite_array(data, dimensions, label):
    """Validates nested numeric arrays before any Maya mutation.

    Args:
        data (object): Array or numeric leaf.
        dimensions (tuple): Expected array shape.
        label (str): Field name used in errors.
    """
    if not dimensions:
        if isinstance(data, bool) or not isinstance(data, (int, float)) or not math.isfinite(data):
            raise ValueError(f"{label} contains non-finite or non-numeric values.")
        return
    if not isinstance(data, list) or len(data) != dimensions[0]:
        raise ValueError(f"Invalid array shape for {label}; expected {dimensions}.")
    for element in data:
        _finite_array(element, dimensions[1:], label)


def validate_motion(data):
    """Validates the versioned SOMA exchange contract without importing Maya.

    Args:
        data (dict): Decoded motion.json.

    Returns:
        dict: Validated motion data.
    """
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported motion schema.")
    if data.get("coordinates") != {"units": "meters", "up": "y", "forward": "+z",
                                   "rotations": "column_local_matrix"}:
        raise ValueError("Unsupported motion coordinate convention.")
    _positive_number(data.get("fps"), "fps", maximum=240)
    frames = data.get("frame_count")
    if type(frames) is not int or not 1 <= frames <= 7200:
        raise ValueError("Invalid motion frame count.")
    skeleton = data.get("skeleton", {})
    if not isinstance(skeleton, dict):
        raise ValueError("Missing skeleton metadata.")
    names = skeleton.get("joint_names", [])
    parents = skeleton.get("parents", [])
    if not isinstance(names, list) or not 1 <= len(names) <= 256:
        raise ValueError("Expected a supported skeleton with 1 through 256 joints.")
    if not isinstance(names, list) or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) for name in names):
        raise ValueError("Joint names must be unique Maya-safe identifiers.")
    if len(set(names)) != len(names):
        raise ValueError("Joint names must be unique Maya-safe identifiers.")
    if not isinstance(parents, list) or len(parents) != len(names) or parents[0] != -1:
        raise ValueError("Expected one root at joint index zero.")
    for index, parent in enumerate(parents):
        if type(parent) is not int or (index and not 0 <= parent < index):
            raise ValueError("Parents must precede children in a single rooted hierarchy.")
    _finite_array(skeleton.get("offsets"), (len(names), 3), "offsets")
    if skeleton["offsets"][0] != [0, 0, 0]:
        raise ValueError("Root offset must be zero; root_positions supplies its absolute translation.")
    _finite_array(data.get("root_positions"), (frames, 3), "root_positions")
    _finite_array(data.get("local_rotations"), (frames, len(names), 3, 3), "local_rotations")
    for sample in data["local_rotations"]:
        for rotation in sample:
            for row_index in range(3):
                for column_index in range(3):
                    dot = sum(rotation[row_index][axis] * rotation[column_index][axis] for axis in range(3))
                    if abs(dot - int(row_index == column_index)) > 0.005:
                        raise ValueError("Rotation matrices must be orthonormal.")
            determinant = sum(rotation[0][axis] * (
                rotation[1][(axis + 1) % 3] * rotation[2][(axis + 2) % 3]
                - rotation[1][(axis + 2) % 3] * rotation[2][(axis + 1) % 3]) for axis in range(3))
            if abs(determinant - 1) > 0.005:
                raise ValueError("Rotation matrices must have positive unit determinant.")
    return data


def import_motion(path, namespace="kimodo", start_frame=1.0):
    """Imports an animated SOMA skeleton in a new namespace on Maya's main thread.

    Source sample times are preserved as fractional Maya frames. Scene units,
    timeline rate, playback range, current time, and selection are preserved.
    A placement group converts Y-up motion into Z-up scenes when necessary.

    Args:
        path (str): Downloaded motion.json path.
        namespace (str): New namespace; collisions are rejected.
        start_frame (float): Start time in the current Maya timeline units.

    Returns:
        dict: Created group, joints, namespace, sample rate, and time range.
    """
    data = validate_motion(_read_json(path))
    if not isinstance(namespace, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", namespace):
        raise ValueError("namespace must be a simple Maya-safe name.")
    if isinstance(start_frame, bool) or not isinstance(start_frame, (int, float)) or not math.isfinite(start_frame):
        raise ValueError("start_frame must be finite.")
    import maya.cmds as cmds
    import maya.api.OpenMaya as om
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Import animation on Maya's main thread.")
    absolute_namespace = f":{namespace}"
    if cmds.namespace(exists=absolute_namespace):
        raise ValueError(f"Namespace already exists: {namespace}")
    selection = cmds.ls(selection=True, long=True) or []
    previous_namespace = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
    # MDistance avoids assuming that Maya's current linear unit is centimeters.
    scale = om.MDistance(1.0, om.MDistance.kMeters).asUnits(om.MDistance.uiUnit())
    timeline_fps = om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())
    times = [start_frame + index * timeline_fps / data["fps"] for index in range(data["frame_count"])]
    group = None
    joints = []
    cmds.undoInfo(openChunk=True, chunkName="Import Kimodo Motion")
    try:
        cmds.namespace(add=namespace, parent=":")
        cmds.namespace(setNamespace=":")
        group = cmds.createNode("transform", name=f"{absolute_namespace}:motion", skipSelect=True)
        cmds.addAttr(group, longName="kimodoSkeleton", dataType="string")
        cmds.setAttr(f"{group}.kimodoSkeleton", json.dumps(data["skeleton"]), type="string", lock=True)
        if cmds.upAxis(query=True, axis=True) == "z":
            cmds.setAttr(f"{group}.rotateX", 90)
        for index, name in enumerate(data["skeleton"]["joint_names"]):
            parent = data["skeleton"]["parents"][index]
            joint = cmds.createNode("joint", name=f"{absolute_namespace}:{name}",
                                    parent=group if parent == -1 else joints[parent], skipSelect=True)
            cmds.setAttr(f"{joint}.translate", *[value * scale for value in data["skeleton"]["offsets"][index]])
            cmds.setAttr(f"{joint}.jointOrient", 0, 0, 0)
            joints.append(joint)
        for frame_index, sample_time in enumerate(times):
            for joint_index, joint in enumerate(joints):
                rotation = data["local_rotations"][frame_index][joint_index]
                # Kimodo uses column vectors; Maya uses row vectors.
                matrix = om.MMatrix([rotation[0][0], rotation[1][0], rotation[2][0], 0,
                                     rotation[0][1], rotation[1][1], rotation[2][1], 0,
                                     rotation[0][2], rotation[1][2], rotation[2][2], 0,
                                     0, 0, 0, 1])
                euler = om.MTransformationMatrix(matrix).rotation()
                for axis, radians in zip("XYZ", (euler.x, euler.y, euler.z)):
                    angle = om.MAngle(radians).asUnits(om.MAngle.uiUnit())
                    cmds.setKeyframe(joint, attribute=f"rotate{axis}", time=sample_time, value=angle)
            for axis, value in zip("XYZ", data["root_positions"][frame_index]):
                cmds.setKeyframe(joints[0], attribute=f"translate{axis}", time=sample_time, value=value * scale)
        rotation_curves = cmds.listConnections(joints, source=True, destination=False, type="animCurveTA") or []
        if rotation_curves:
            cmds.filterCurve(list(set(rotation_curves)), filter="euler")
        cmds.keyTangent(joints, inTangentType="linear", outTangentType="linear")
    except Exception:
        if group and cmds.objExists(group):
            cmds.delete(group)
        if cmds.namespace(exists=absolute_namespace):
            cmds.namespace(removeNamespace=absolute_namespace)
        raise
    finally:
        cmds.namespace(setNamespace=previous_namespace)
        cmds.select(selection, replace=True) if selection else cmds.select(clear=True)
        cmds.undoInfo(closeChunk=True)
    logger.info("Imported %s: %s joints, %s frames at %s FPS", namespace, len(joints), len(times), data["fps"])
    return {"group": group, "joints": joints, "namespace": namespace,
            "start_frame": times[0], "end_frame": times[-1], "fps": data["fps"]}


class _KimodoBackend:
    """Owns model state exclusively inside the bridge generation worker."""

    def __init__(self, device="auto", text_encoder_url="http://127.0.0.1:9550", start_encoder=True):
        """Stores backend settings without loading a model.

        Args:
            device (str): Inference device selection.
            text_encoder_url (str): Existing or locally managed encoder URL.
            start_encoder (bool): Whether to start a missing local encoder.
        """
        self.device = device
        self.text_encoder_url = text_encoder_url.rstrip("/")
        self.start_encoder = start_encoder
        self.encoder_process = None
        self.model = None
        self.model_name = None

    def capabilities(self):
        """Reads Kimodo's registry without loading model weights.

        Returns:
            dict: Models and supported generation features.
        """
        from kimodo.model.registry import MODEL_INFOS
        from huggingface_hub import try_to_load_from_cache

        models = []
        for info in MODEL_INFOS:
            if info.family != "Kimodo":
                continue
            cached = try_to_load_from_cache(info.repo_id, "config.yaml")
            metadata = {"id": info.short_key, "name": info.display_name, "repo_id": info.repo_id,
                        "skeleton": info.skeleton, "cached": isinstance(cached, str)}
            if isinstance(cached, str):
                with open(cached, encoding="utf-8") as stream:
                    rates = set(re.findall(r"^\s*fps:\s*([\d.]+)\s*$", stream.read(), re.MULTILINE))
                if len(rates) == 1:
                    metadata["fps"] = _positive_number(float(rates.pop()), "model fps")
            models.append(metadata)
        return {"models": models, "skeleton": "somaskel77", "max_prompts": 16, "max_samples": 8,
                "constraints": True, "max_duration_seconds": 120,
                "formats": list(ARTIFACT_NAMES), "device": self.device}

    def download(self, model, update):
        """Downloads a registered checkpoint using Kimodo's existing dependency.

        Args:
            model (str): Registered model ID.
            update (callable): Job stage reporter.

        Returns:
            dict: Download provenance.
        """
        from huggingface_hub import snapshot_download
        from kimodo.model.registry import MODEL_NAMES

        update(stage="downloading_model")
        path = snapshot_download(repo_id=MODEL_NAMES[model])
        return {"model": model, "cache_path": path}

    def rest_motion(self):
        """Builds a SOMA rest skeleton without loading model weights.

        Returns:
            dict: One-frame motion suitable for pose authoring in Maya.
        """
        from kimodo.skeleton import build_skeleton

        skeleton = build_skeleton(77)
        metadata = _skeleton_metadata(skeleton)
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        return {"schema_version": SCHEMA_VERSION, "coordinates": _motion_coordinates(),
                "fps": 30.0, "frame_count": 1, "skeleton": metadata,
                "root_positions": [skeleton.neutral_joints[0].tolist()],
                "local_rotations": [[identity for name in metadata["joint_names"]]]}

    def _encoder_ready(self):
        """Checks the encoder's Gradio configuration without computing embeddings.

        Returns:
            bool: Whether the expected encoder endpoint is advertised.
        """
        try:
            probe_text_encoder(self.text_encoder_url, timeout=2)
            return True
        except (ConnectionError, RuntimeError, ValueError):
            return False

    def _ensure_encoder(self, directory):
        """Starts a missing local text encoder and waits for its API.

        Args:
            directory (str): Job directory receiving startup logs.
        """
        if self._encoder_ready():
            return
        parsed = urllib.parse.urlsplit(self.text_encoder_url)
        if not self.start_encoder or parsed.hostname not in ("127.0.0.1", "localhost"):
            raise RuntimeError(f"Text encoder is unavailable at {self.text_encoder_url}.")
        if self.encoder_process is None or self.encoder_process.poll() is not None:
            environment = os.environ.copy()
            environment.update(GRADIO_SERVER_NAME="127.0.0.1", GRADIO_SERVER_PORT=str(parsed.port or 9550),
                               PYTHONUNBUFFERED="1", PYTHONUTF8="1")
            log_path = os.path.join(directory, "text_encoder.log")
            process_options = {}
            if os.name == "nt":
                process_options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            else:
                # WSL may close the bridge's launch session during restart. A new
                # session lets the encoder remain independently available.
                process_options["start_new_session"] = True
            with open(log_path, "ab") as stream:
                self.encoder_process = subprocess.Popen(
                    [sys.executable, "-u", "-X", "utf8", "-m", "kimodo.scripts.run_text_encoder_server"],
                    stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                    env=environment, **process_options)
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            if self.encoder_process.poll() is not None:
                raise RuntimeError(f"Text encoder exited; inspect {directory}/text_encoder.log.")
            if self._encoder_ready():
                return
            time.sleep(1)
        raise TimeoutError("Text encoder startup exceeded 600 seconds; inspect text_encoder.log.")

    def generate(self, definition, directory, update):
        """Generates one sample and writes portable JSON and native NPZ artifacts.

        Args:
            definition (dict): Validated generation definition.
            directory (str): Exclusive server-side job directory.
            update (callable): Receives stage keyword arguments.

        Returns:
            dict: Resolved model, seed, timing, and runtime provenance.
        """
        import importlib.metadata
        import torch
        from kimodo import load_model
        from kimodo.exports.motion_io import save_kimodo_npz
        from kimodo.model.text_encoder_api import TextEncoderAPI
        from kimodo.tools import seed_everything

        update(stage="connecting_text_encoder")
        self._ensure_encoder(directory)
        if self.model_name != definition["model"]:
            update(stage="loading_model")
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            device = self.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model, self.model_name = load_model(
                definition["model"], device=device, return_resolved_name=True,
                text_encoder=TextEncoderAPI(self.text_encoder_url))
        update(stage="preparing_request")
        parameters = definition["parameters"]
        seed = parameters["seed"] if parameters["seed"] is not None else secrets.randbits(32)
        seed_everything(seed)
        segments = definition["prompts"]
        frame_counts = [int(segment["duration_seconds"] * self.model.fps) for segment in segments]
        frame_count = sum(frame_counts)
        if any(count < 2 for count in frame_counts):
            raise ValueError("Each duration must produce at least two model frames.")
        if len(segments) > 1 and any(count <= parameters["transition_frames"] for count in frame_counts):
            raise ValueError("Every segment must be longer than the transition overlap.")
        validate_constraints(definition["constraints"], frame_count)
        from kimodo.constraints import load_constraints_lst

        for constraint in definition["constraints"]:
            if "local_joints_rot" in constraint and len(constraint["local_joints_rot"][0]) != len(
                    self.model.output_skeleton.bone_order_names):
                raise ValueError("Constraint skeleton does not match the selected model's output skeleton.")
        constraints = load_constraints_lst(definition["constraints"], self.model.skeleton,
                                           device=self.model.device)
        update(stage="generating", seed=seed, fps=float(self.model.fps), frame_count=frame_count)

        def progress(iterable):
            """Reports actual diffusion steps and permits cooperative cancellation.

            Args:
                iterable (iterable): Kimodo denoising indices.

            Yields:
                int: Next diffusion step.
            """
            for index, step in enumerate(iterable):
                update(stage="generating", progress=(index + 1) / parameters["diffusion_steps"])
                yield step

        with torch.inference_mode():
            text_input = [segment["text"] for segment in segments] if len(segments) > 1 else segments[0]["text"]
            output = self.model(text_input,
                                frame_counts if len(segments) > 1 else frame_count,
                                num_denoising_steps=parameters["diffusion_steps"],
                                num_samples=parameters["num_samples"], multi_prompt=len(segments) > 1,
                                constraint_lst=constraints, cfg_type="separated", cfg_weight=parameters["guidance"],
                                num_transition_frames=parameters["transition_frames"],
                                first_heading_angle=parameters["heading"], progress_bar=progress,
                                post_processing=parameters["postprocess"], return_numpy=True)
        update(stage="exporting")
        skeleton = self.model.output_skeleton
        sample_names = []
        for index in range(parameters["num_samples"]):
            sample = {key: value[index] for key, value in output.items()}
            motion = {"schema_version": SCHEMA_VERSION, "coordinates": _motion_coordinates(),
                      "fps": float(self.model.fps), "frame_count": len(sample["root_positions"]),
                      "skeleton": _skeleton_metadata(skeleton),
                      "root_positions": sample["root_positions"].tolist(),
                      "local_rotations": sample["local_rot_mats"].tolist()}
            validate_motion(motion)
            stem = "motion" if index == 0 else f"sample_{index}"
            sample_names.append(f"{stem}.json")
            _write_json(os.path.join(directory, f"{stem}.json"), motion)
            save_kimodo_npz(os.path.join(directory, f"{stem}.npz"), sample)
        return {"model": self.model_name, "seed": seed, "fps": motion["fps"],
                "samples": sample_names,
                "frame_count": motion["frame_count"], "device": str(self.model.device),
                "parameters": dict(parameters, seed=seed, cfg_type="separated"),
                "kimodo_version": importlib.metadata.version("kimodo"),
                "kimodo_source": importlib.metadata.distribution("kimodo").read_text("direct_url.json")}


def _motion_coordinates():
    """Returns the fixed exchange coordinate convention.

    Returns:
        dict: Coordinate metadata.
    """
    return {"units": "meters", "up": "y", "forward": "+z", "rotations": "column_local_matrix"}


def _skeleton_metadata(skeleton):
    """Converts Kimodo skeleton tensors into portable metadata.

    Args:
        skeleton (SkeletonBase): Kimodo runtime skeleton.

    Returns:
        dict: Hierarchy and neutral offsets.
    """
    neutral = skeleton.neutral_joints.detach().cpu().tolist()
    parents = skeleton.joint_parents.detach().cpu().tolist()
    offsets = [[0, 0, 0] if parent == -1 else [value - origin for value, origin in zip(
        neutral[index], neutral[parent])] for index, parent in enumerate(parents)]
    return {"id": skeleton.name, "joint_names": skeleton.bone_order_names, "parents": parents, "offsets": offsets}


class _JobCancelled(Exception):
    """Signals cooperative cancellation at a backend progress boundary."""


def _validate_job_directory(root, job_id):
    """Checks the exact direct-child job directory before filesystem cleanup or reuse.

    Args:
        root (str): Explicit parent directory owned/configured by the caller.
        job_id (str): Validated 32-character identifier, never an arbitrary path.

    Returns:
        str: Absolute child path, free of symlinks/junctions within the job tree.
    """
    _validate_job_id(job_id)
    if not root or not os.path.isabs(root):
        raise ValueError("Job cleanup requires an explicit absolute parent directory.")
    parent = os.path.realpath(root)
    directory = os.path.join(parent, job_id)
    if os.path.dirname(os.path.realpath(directory)) != parent:
        raise ValueError("Job directory resolves outside its configured parent.")
    pending = [directory]
    while pending:
        path = pending.pop()
        if not os.path.lexists(path):
            continue
        attributes = os.lstat(path)
        if (stat.S_ISLNK(attributes.st_mode)
                or getattr(attributes, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)):
            raise ValueError(f"Refusing linked/junction job path: {path}")
        if stat.S_ISDIR(attributes.st_mode):
            with os.scandir(path) as entries:
                pending.extend(entry.path for entry in entries)
    return directory


class _BridgeState:
    """Serializes generation in one worker; never performs Maya scene operations."""

    def __init__(self, directory, backend):
        """Creates an on-disk job store and an idle generation worker.

        Args:
            directory (str): Server-owned job cache root.
            backend (object): Backend exposing capabilities and generate.
        """
        self.directory = os.path.abspath(directory)
        os.makedirs(self.directory, exist_ok=True)
        self.backend = backend
        self.capabilities = backend.capabilities()
        self.lock = threading.RLock()
        self.pending = queue.Queue(maxsize=16)
        self.active_job_id = None
        self.console_job_updates = {}
        self.started_at = time.time()
        self.closed = False
        for name in os.listdir(self.directory):
            if re.fullmatch(r"[0-9a-f]{32}", name):
                path = os.path.join(self.directory, name, "result.json")
                if os.path.isfile(path):
                    result = _read_json(path)
                    if result["status"] not in TERMINAL_STATUSES:
                        result.update(status="failed", stage="interrupted",
                                      error="Bridge restarted before completion.")
                        _write_json(path, result)
        self.worker = threading.Thread(target=self._work, name="KimodoGeneration", daemon=True)
        self.worker.start()

    def runtime(self):
        """Describes the server process and current queue without loading the model.

        Returns:
            dict: Runtime location, process, backend, and activity details.
        """
        with self.lock:
            active_job_id = self.active_job_id
        with self.pending.mutex:
            unfinished_jobs = self.pending.unfinished_tasks
        return {
            "pid": os.getpid(),
            "platform": platform.system(),
            "python_executable": sys.executable,
            "bridge_script": os.path.abspath(__file__),
            "job_directory": self.directory,
            "device": getattr(self.backend, "device", "test"),
            "text_encoder_url": getattr(self.backend, "text_encoder_url", None),
            "started_at": self.started_at,
            "active_job_id": active_job_id,
            "queued_jobs": self.pending.qsize(),
            "unfinished_jobs": unfinished_jobs,
        }

    def close(self):
        """Stops the idle queue worker without terminating its text-encoder child."""
        with self.lock:
            if self.closed:
                return
            self.closed = True
        self.pending.put(None)
        self.worker.join(timeout=10)

    def get(self, job_id):
        """Reads one job under the store lock.

        Args:
            job_id (str): Validated identifier.

        Returns:
            dict: Latest job status.
        """
        _validate_job_id(job_id)
        with self.lock:
            path = os.path.join(self.directory, job_id, "result.json")
            if not os.path.isfile(path):
                raise FileNotFoundError(path)
            result = _read_json(path)
            result["server_directory"] = os.path.dirname(path)
            return result

    def submit(self, job_id, data, operation="generate"):
        """Persists an idempotent request and queues its execution.

        Args:
            job_id (str): Client-supplied identifier.
            data (dict): Definition data.
            operation (str): Generate motion or download_model.

        Returns:
            dict: Accepted or previously submitted job.
        """
        _validate_job_id(job_id)
        definition = KimodoGenerationDefinition.from_dict(data).as_dict() if operation == "generate" else data
        if definition["model"] not in [model["id"] for model in self.capabilities["models"]]:
            raise ValueError("Unsupported model; choose an explicit SOMA model ID from capabilities.")
        directory = os.path.join(self.directory, job_id)
        with self.lock:
            if os.path.isdir(directory):
                if _read_json(os.path.join(directory, "definition.json")) != definition:
                    raise ValueError("job_id already belongs to a different definition.")
                return self.get(job_id)
            if self.pending.full():
                raise ValueError("Generation queue is full; retry later using the same job_id.")
            os.makedirs(directory, exist_ok=False)
            _write_json(os.path.join(directory, "definition.json"), definition)
            result = {"job_id": job_id, "status": "queued", "stage": "queued", "operation": operation,
                      "submitted_at": time.time(), "progress": 0, "artifacts": []}
            _write_json(os.path.join(directory, "result.json"), result)
            self.pending.put_nowait(job_id)
            self._log_job_update(job_id, stage="queued", progress=0, queue_size=self.pending.qsize(),
                                 submitted_at=result["submitted_at"])
            return result

    def delete(self, job_id):
        """Deletes exactly one completed job under the same lock used by the worker.

        Args:
            job_id (str): Explicit job ID; nonterminal jobs are rejected.

        Returns:
            dict: Idempotent deletion acknowledgement.
        """
        with self.lock:
            directory = _validate_job_directory(self.directory, job_id)
            if not os.path.exists(directory):
                return {"job_id": job_id, "deleted": True, "already_absent": True}
            result = self.get(job_id)
            if result.get("job_id") != job_id:
                raise ValueError("Job manifest does not match the requested directory; nothing was removed.")
            if result["status"] not in TERMINAL_STATUSES:
                raise ValueError("Cancel this job and wait for completion before deleting its files.")
            shutil.rmtree(directory)
            return {"job_id": job_id, "deleted": True, "already_absent": False}

    def _update(self, job_id, **values):
        """Atomically updates persisted job state.

        Args:
            job_id (str): Job identifier.
            **values: JSON-compatible status fields.
        """
        with self.lock:
            result = self.get(job_id)
            result.update(values)
            _write_json(os.path.join(self.directory, job_id, "result.json"), result)
        self._log_job_update(job_id, **values)

    def _log_job_update(self, job_id, **values):
        """Prints concise, flushed job feedback independent of logging configuration.

        Args:
            job_id (str): Job identifier.
            **values: Updated job fields, including stage or progress when available.
        """
        stage = values.get("stage")
        visible_stages = {
            "queued", "loading_model", "downloading_model", "generating", "exporting",
            "complete", "failed", "cancelled",
        }
        if stage not in visible_stages:
            return
        progress = values.get("progress")
        percent = max(0, min(100, round(float(progress) * 100))) if progress is not None else None
        if stage == "generating" and percent not in (None, 0, 100):
            percent = int(percent / 10) * 10
        previous_stage, previous_percent = self.console_job_updates.get(job_id, (None, None))
        if stage is None:
            stage = previous_stage
        if stage == previous_stage and (percent is None or percent == previous_percent):
            return
        self.console_job_updates[job_id] = (stage, percent if percent is not None else previous_percent)
        labels = {"queued": "SUBMITTED", "starting": "STARTED", "complete": "COMPLETE"}
        label = labels.get(stage, str(stage or values.get("status") or "working").replace("_", " ").upper())
        progress_text = f"{percent:3d}%" if percent is not None else " ..."
        if stage == "queued":
            progress_text = f"Queue Position {max(1, int(values.get('queue_size', 1)))}"
        elif stage == "loading_model":
            progress_text = "Model initialization may take several minutes"
        elif stage == "failed":
            progress_text = "Error"
        elif stage == "cancelled":
            progress_text = "Stopped"
        elapsed = values.get("elapsed_seconds")
        if elapsed is not None:
            progress_text += f" | Elapsed {float(elapsed):.1f}s"
        timestamp_value = values.get("submitted_at", time.time())
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp_value))
        print(f"[{timestamp}] [Job {job_id[:12]}] {label:<18} | {progress_text}", flush=True)

    def _work(self):
        """Processes queued jobs sequentially, recording failures and artifacts."""
        while True:
            job_id = self.pending.get()
            if job_id is None:
                self.pending.task_done()
                return
            with self.lock:
                self.active_job_id = job_id
            directory = os.path.join(self.directory, job_id)
            started = time.monotonic()
            try:
                self._update(job_id, status="running", stage="starting")

                def update(**values):
                    """Reports a backend stage for the active job.

                    Args:
                        **values: Status fields to persist.
                    """
                    if self.get(job_id).get("cancel_requested"):
                        raise _JobCancelled("Cancelled by the user.")
                    self._update(job_id, **values)

                update(stage="starting")
                definition = _read_json(os.path.join(directory, "definition.json"))
                if self.get(job_id).get("operation") == "download_model":
                    resolved = self.backend.download(definition["model"], update)
                    self.capabilities = self.backend.capabilities()
                else:
                    resolved = self.backend.generate(definition, directory, update)
                update(stage="finalizing")
                artifacts = []
                for name in sorted(name for name in os.listdir(directory) if _is_artifact(name)):
                    with open(os.path.join(directory, name), "rb") as stream:
                        payload = stream.read()
                    artifacts.append({"name": name, "size_bytes": len(payload),
                                      "sha256": hashlib.sha256(payload).hexdigest()})
                self._update(job_id, status="succeeded", stage="complete", progress=1.0, resolved=resolved,
                             artifacts=artifacts, elapsed_seconds=time.monotonic() - started)
            except _JobCancelled as error:
                self._update(job_id, status="cancelled", stage="cancelled", error=str(error),
                             elapsed_seconds=time.monotonic() - started)
            except Exception as error:
                logger.exception("Job %s failed", job_id)
                self._update(job_id, status="failed", stage="failed", error=str(error),
                             elapsed_seconds=time.monotonic() - started)
            finally:
                with self.lock:
                    self.active_job_id = None
                self.console_job_updates.pop(job_id, None)
                self.pending.task_done()


class _BridgeHandler(BaseHTTPRequestHandler):
    """Serves a small versioned JSON API and explicitly named job artifacts."""

    def log_message(self, message, *arguments):
        """Routes HTTP diagnostics to the bridge logger.

        Args:
            message (str): HTTP log format.
            *arguments: Log arguments.
        """
        logger.debug(message, *arguments)

    def _json(self, status, data):
        """Sends one JSON response.

        Args:
            status (int): HTTP status code.
            data (dict): Response body.
        """
        payload = json.dumps(data, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self):
        """Checks bearer authentication and rejects browser-origin requests.

        Returns:
            bool: Whether this request may proceed.
        """
        token = self.server.token
        if self.headers.get("Origin") or (token and not secrets.compare_digest(
                self.headers.get("Authorization", ""), f"Bearer {token}")):
            self._json(403, {"error": "Unauthorized bridge request."})
            return False
        return True

    def do_GET(self):
        """Handles health, capabilities, status, and artifact downloads."""
        if not self._authorized():
            return
        state = self.server.state
        try:
            if self.path == "/v1/health":
                self._json(200, {"service": "gt-kimodo", "protocol_version": PROTOCOL_VERSION,
                                 "status": "ready", "queue_size": state.pending.qsize(),
                                 "features": list(BRIDGE_FEATURES), "runtime": state.runtime()})
            elif self.path == "/v1/capabilities":
                self._json(200, state.capabilities)
            elif self.path == "/v1/skeleton":
                self._json(200, state.backend.rest_motion())
            else:
                match = re.fullmatch(r"/v1/jobs/([0-9a-f]{32})(?:/artifacts/([a-z0-9_.]+))?", self.path)
                if not match:
                    self._json(404, {"error": "Unknown endpoint."})
                    return
                job_id, artifact = match.groups()
                result = state.get(job_id)
                if artifact is None:
                    self._json(200, result)
                elif _is_artifact(artifact) and result["status"] == "succeeded":
                    path = os.path.join(state.directory, job_id, artifact)
                    with open(path, "rb") as stream:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/octet-stream")
                        self.send_header("Content-Length", str(os.path.getsize(path)))
                        self.end_headers()
                        shutil.copyfileobj(stream, self.wfile)
                else:
                    self._json(404, {"error": "Artifact is not available."})
        except FileNotFoundError:
            self._json(404, {"error": "Unknown job."})
        except (BrokenPipeError, ConnectionResetError):
            logger.debug("Client disconnected.")

    def do_POST(self):
        """Validates and submits a JSON generation request."""
        if not self._authorized():
            return
        cancel_match = re.fullmatch(r"/v1/jobs/([0-9a-f]{32})/cancel", self.path)
        delete_match = re.fullmatch(r"/v1/jobs/([0-9a-f]{32})/delete", self.path)
        shutdown_request = self.path == "/v1/admin/shutdown"
        if (self.path not in ("/v1/jobs", "/v1/models/download") and not cancel_match and not delete_match
                and not shutdown_request):
            self._json(404, {"error": "Unknown endpoint."})
            return
        try:
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16 * 1024 * 1024:
                raise ValueError("Request body must be between 1 byte and 16 MB.")
            self.connection.settimeout(10)
            data = json.loads(self.rfile.read(length))
            if shutdown_request:
                if data != {"confirm": "shutdown"}:
                    raise ValueError("Bridge shutdown requires explicit confirmation.")
                runtime = self.server.state.runtime()
                if runtime["active_job_id"] or runtime["unfinished_jobs"]:
                    raise ValueError("The bridge is busy. Cancel or finish all jobs before stopping it.")
                self._json(200, {"stopping": True, "runtime": runtime,
                                 "encoder_action": "unchanged"})
                threading.Thread(target=self.server.shutdown, name="KimodoShutdown", daemon=True).start()
                return
            if delete_match:
                job_id = delete_match.group(1)
                if data != {"confirm": job_id}:
                    raise ValueError("Deletion requires explicit confirmation of this job ID.")
                self._json(200, self.server.state.delete(job_id))
                return
            if cancel_match:
                job_id = cancel_match.group(1)
                if self.server.state.get(job_id)["status"] not in TERMINAL_STATUSES:
                    self.server.state._update(job_id, cancel_requested=True)
                self._json(200, self.server.state.get(job_id))
                return
            if self.path == "/v1/models/download":
                if not isinstance(data, dict) or set(data) != {"job_id", "model"}:
                    raise ValueError("Expected job_id and model.")
                self._json(202, self.server.state.submit(data["job_id"], {"model": data["model"]}, "download_model"))
                return
            if not isinstance(data, dict) or set(data) != {"job_id", "definition"}:
                raise ValueError("Expected job_id and definition.")
            self._json(202, self.server.state.submit(data["job_id"], data["definition"]))
        except (ValueError, TypeError, KeyError, OSError) as error:
            self._json(400, {"error": str(error)})


def _bridge_banner(host, port, directory):
    """Builds the visible startup message for an interactive bridge console.

    Args:
        host (str): Server listen address.
        port (int): Server listen port.
        directory (str): Persistent server job directory.

    Returns:
        str: Multi-line ASCII bridge identification and runtime details.
    """
    border = "+" + "=" * 62 + "+"
    return "\n".join((
        "",
        border,
        "|" + "KIMODO BRIDGE".center(62) + "|",
        "|" + "Maya animation generation server".center(62) + "|",
        border,
        "  Keep this window open while Maya uses the bridge.",
        f"  Address : http://{host}:{port}",
        f"  Process : {os.getpid()}",
        f"  Jobs    : {directory}",
        border,
        "",
    ))


def _suppress_known_runtime_warnings():
    """Hides known third-party warning and progress noise from the bridge console."""
    warnings.filterwarnings(
        "ignore", message=r"`torch\.jit\.script` is deprecated\..*", category=FutureWarning)
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TQDM_DISABLE", "1")


def serve(host="127.0.0.1", port=7861, directory=None, token=None,
          device="auto", text_encoder_url="http://127.0.0.1:9550", start_encoder=True):
    """Runs the bridge inside a Kimodo Python environment until interrupted.

    Args:
        host (str): Listen address; non-loopback binding requires a token.
        port (int): HTTP listen port, separate from demo and encoder ports.
        directory (str, optional): Persistent server-owned job cache.
        token (str, optional): Bearer token, required for network exposure.
        device (str): Inference device: auto/cpu/cuda.
        text_encoder_url (str): Gradio text encoder origin.
        start_encoder (bool): Whether to launch a missing local encoder.
    """
    if host not in ("127.0.0.1", "localhost") and not token:
        raise ValueError("A bearer token is required when binding beyond localhost.")
    _suppress_known_runtime_warnings()
    directory = directory or os.path.join(os.path.expanduser("~"), ".cache", "gt-tools", "kimodo", "jobs")
    # Bind before touching the job store, preventing duplicate launch on this port.
    server = ThreadingHTTPServer((host, port), _BridgeHandler)
    store_lock = None
    state = None
    try:
        store_lock = _lock_job_store(directory)
        server.token = token
        state = _BridgeState(directory, _KimodoBackend(device, text_encoder_url, start_encoder))
        server.state = state
        print(_bridge_banner(host, port, directory), flush=True)
        logger.info("Kimodo bridge ready at http://%s:%s; jobs: %s", host, port, directory)
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Bridge interrupted. Unfinished jobs will be marked failed on restart.")
    finally:
        server.server_close()
        if state:
            state.close()
        if store_lock:
            store_lock.close()


def _lock_job_store(directory):
    """Exclusively locks a job store for the lifetime of the bridge process.

    The OS releases this lock after a crash, so stale lock files do not prevent
    restarting. A second bridge must use a different job directory.

    Args:
        directory (str): Server-owned job directory.

    Returns:
        file: Lock handle; keep open while the bridge is running.
    """
    os.makedirs(directory, exist_ok=True)
    stream = open(os.path.join(directory, ".bridge.lock"), "a+b")
    try:
        if os.name == "nt":
            import msvcrt

            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        stream.close()
        raise RuntimeError(f"Another bridge owns job directory {directory}.") from error
    return stream


def _main():
    """Parses the standalone bridge command line and starts its server."""
    # The standalone filename is kimodo.py; do not shadow the installed Kimodo
    # package with this utility when Python adds its directory to sys.path.
    script_directory = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [entry for entry in sys.path if os.path.abspath(entry) != script_directory]
    parser = argparse.ArgumentParser(description="Kimodo bridge")
    parser.add_argument("--serve", action="store_true", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7861)
    parser.add_argument("--directory")
    parser.add_argument("--token")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--text-encoder-url", default="http://127.0.0.1:9550")
    parser.add_argument("--no-start-encoder", action="store_true")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    serve(host=arguments.host, port=arguments.port, directory=arguments.directory,
          token=arguments.token, device=arguments.device, text_encoder_url=arguments.text_encoder_url,
          start_encoder=not arguments.no_start_encoder)


if __name__ == "__main__":
    _main()
