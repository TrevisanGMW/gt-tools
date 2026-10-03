"""Pure state, definitions, constraint entries, and persistent job history."""

import copy
import logging
import os
import subprocess
import tempfile
import uuid
from gt.utils import kimodo
from gt.core.io import read_json_dict, write_json
from gt.tools.kimodo_generator import kimodo_generator_hik as humanik

logger = logging.getLogger(__name__)


def default_download_directory():
    """Resolves the package cache without creating or clearing generated files.

    Returns:
        str: Absolute download directory, with a standard-library fallback outside Maya.
    """
    try:
        from gt.core.prefs import PackageCache

        directory = PackageCache().cache_dir
    except (ImportError, AttributeError, OSError):
        directory = os.path.join(tempfile.gettempdir(), "gt_tools_cache")
    return os.path.join(directory, "kimodo", "downloads")


def query_wsl_distributions():
    """Queries installed WSL distributions without starting a Linux process.

    Returns:
        list[str]: Installed distribution names in Windows' reported order.

    Raises:
        ValueError: When WSL is missing, times out, or reports an error.
    """
    try:
        result = subprocess.run(["wsl.exe", "--list", "--quiet"], capture_output=True,
                                timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"Could not query WSL. Check that WSL is installed and available: {error}") from error

    def decode(payload):
        """Decodes both Windows UTF-16 output and UTF-8 WSL versions.

        Args:
            payload (bytes): Captured subprocess output.

        Returns:
            str: Clean distribution/error text.
        """
        if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
            return payload.decode("utf-16", errors="replace")
        encoding = "utf-16-le" if b"\x00" in payload else "utf-8-sig"
        return payload.decode(encoding, errors="replace").replace("\x00", "")

    if result.returncode:
        detail = decode(result.stderr or result.stdout).strip()
        raise ValueError(f"WSL could not list distributions: {detail}")
    return list(dict.fromkeys(line.strip() for line in decode(result.stdout).splitlines() if line.strip()))


def resolve_environment_python(directory, mode, distribution=""):
    """Finds an interpreter inside a user-selected environment folder.

    Args:
        directory (str): Native Windows directory or a WSL UNC share directory.
        mode (str): Local launch mode, native or wsl.
        distribution (str): Selected WSL distribution name.

    Returns:
        str: Absolute Python executable path for the selected runtime.

    Raises:
        ValueError: When the directory does not contain a suitable interpreter.
    """
    if mode == "wsl":
        normalized = directory.replace("\\", "/").rstrip("/")
        parts = normalized.split("/")
        if len(parts) < 4 or parts[2].lower() not in ("wsl.localhost", "wsl$"):
            raise ValueError("Browse the selected distribution under \\\\wsl.localhost, or enter a Linux Python path.")
        if parts[3].casefold() != distribution.casefold():
            raise ValueError(f"That folder belongs to {parts[3]}. Select that WSL distribution first.")
        candidates = ("bin/python", "bin/python3", "python", "python3")
        linux_directory = "/" + "/".join(parts[4:])
        for relative in candidates:
            candidate = f"{linux_directory.rstrip('/')}/{relative}"
            if os.path.isfile(os.path.join(directory, *relative.split("/"))):
                return candidate
            # Virtual-environment interpreters are often Linux symlinks that
            # Windows cannot dereference through the UNC share.
            try:
                result = subprocess.run(
                    ["wsl.exe", "--distribution", distribution, "--exec",
                     "test", "-f", candidate, "-a", "-x", candidate],
                    capture_output=True, timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ValueError(f"Could not inspect the Python environment inside WSL: {error}") from error
            if result.returncode == 0:
                return candidate
    elif mode == "native":
        for relative in ("Scripts/python.exe", "python.exe", "bin/python.exe"):
            candidate = os.path.join(directory, *relative.split("/"))
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
    else:
        raise ValueError("Choose Start in WSL or Start on Windows before selecting a Python environment.")
    raise ValueError("No Python executable found. Select the Kimodo environment folder or its bin/Scripts folder.")


class KimodoGeneratorModel:
    """Stores editable authoring state independently from Qt and Maya."""

    def __init__(self, preferences=True):
        """Loads tool preferences lazily, with an import-safe memory fallback.

        Args:
            preferences (bool): Whether to attempt using gt.core.prefs.Prefs.
        """
        self.prefs = None
        self.reset()
        if preferences:
            try:
                from gt.core.prefs import Prefs

                self.prefs = Prefs("kimodo_generator")
                saved = self.prefs.get_raw_preferences().get("state", {})
                if saved:
                    self.restore(saved)
            except (ImportError, AttributeError, OSError, ValueError, TypeError, KeyError) as error:
                logger.debug("Kimodo preferences unavailable: %s", error)

    def reset(self):
        """Resets editable settings without deleting any files or server jobs."""
        self.connection = {"url": kimodo.DEFAULT_URL, "mode": "existing", "python_path": "",
                           "distribution": "", "device": "auto", "text_encoder_url": "http://127.0.0.1:9550",
                           "start_encoder": True, "show_console": True, "auto_connect": False}
        self.token = ""
        self.definition = kimodo.KimodoGenerationDefinition("A person walks forward and comes to a stop.").as_dict()
        self.prompt_durations_in_frames = False
        self.constraints = []
        self.path_curve_samples = 4
        self.path_heading_mode = "none"
        self.path_heading_offset = 0.0
        self.jobs = []
        self.auto_download = True
        self.auto_maya_file = True
        self.auto_import_maya = True
        self.auto_import_all_samples = True
        self.auto_clear_scene = True
        self.auto_frame_rate = True
        self.auto_frame_range = True
        self.table_widths = {}
        self.output_directory = default_download_directory()
        self.namespace = "kimodo"
        self.start_frame = 1.0
        self.pose_group = ""
        self.pose_previews_template = True
        self.capabilities = {}
        self.rest_motion = None
        self.humanik = humanik.default_settings()

    def snapshot(self):
        """Builds serializable authoring state, excluding the bearer token.

        Returns:
            dict: Preferences/setup payload.
        """
        return copy.deepcopy({"connection": self.connection, "definition": self.definition,
                              "constraints": self.constraints, "jobs": self.jobs,
                              "path_curve_samples": self.path_curve_samples,
                              "path_heading_mode": self.path_heading_mode,
                              "path_heading_offset": self.path_heading_offset,
                              "output_directory": self.output_directory, "namespace": self.namespace,
                              "start_frame": self.start_frame, "humanik": self.humanik,
                              "auto_download": self.auto_download, "auto_maya_file": self.auto_maya_file,
                              "auto_import_maya": self.auto_import_maya,
                              "auto_import_all_samples": self.auto_import_all_samples,
                              "auto_frame_rate": self.auto_frame_rate,
                              "auto_frame_range": self.auto_frame_range,
                              "prompt_durations_in_frames": self.prompt_durations_in_frames,
                              "auto_clear_scene": self.auto_clear_scene,
                              "table_widths": self.table_widths,
                              "pose_previews_template": self.pose_previews_template})

    def restore(self, data):
        """Validates saved data before replacing the current state.

        Args:
            data (dict): Preferences or saved setup.
        """
        definition = kimodo.KimodoGenerationDefinition.from_dict(data["definition"]).as_dict()
        hik_settings = humanik.validate_settings(data.get("humanik", {}))
        constraints = copy.deepcopy(data.get("constraints", []))
        for entry in constraints:
            kimodo.validate_constraints([entry["parameters"]])
        self.definition = definition
        self.humanik = hik_settings
        self.constraints = constraints
        try:
            path_curve_samples = int(data.get("path_curve_samples", 4))
        except (TypeError, ValueError):
            path_curve_samples = 4
        self.path_curve_samples = min(max(path_curve_samples, 2), 7200)
        try:
            self.path_heading_mode, self.path_heading_offset = kimodo.validate_root_heading_mode(
                data.get("path_heading_mode", "none"), data.get("path_heading_offset", 0.0))
        except ValueError:
            self.path_heading_mode, self.path_heading_offset = "none", 0.0
        self.connection.update(data.get("connection", {}))
        self.connection.pop("token", None)
        self.jobs = copy.deepcopy(data.get("jobs", []))
        for job in self.jobs:
            job.pop("downloading", None)
            job.pop("exporting_maya", None)
        self.auto_download = bool(data.get("auto_download", True))
        self.auto_maya_file = bool(data.get("auto_maya_file", True))
        self.auto_import_maya = bool(data.get("auto_import_maya", True))
        self.auto_import_all_samples = bool(data.get("auto_import_all_samples", True))
        self.auto_frame_rate = bool(data.get("auto_frame_rate", True))
        self.auto_frame_range = bool(data.get("auto_frame_range", True))
        self.prompt_durations_in_frames = bool(data.get("prompt_durations_in_frames", False))
        self.auto_clear_scene = bool(data.get("auto_clear_scene", True))
        self.pose_previews_template = bool(data.get("pose_previews_template", True))
        raw_widths = data.get("table_widths", {})
        self.table_widths = {}
        if isinstance(raw_widths, dict):
            for name, widths in raw_widths.items():
                if (name in ("prompts", "constraints", "jobs") and isinstance(widths, list)
                        and all(isinstance(width, int) and 20 <= width <= 10000 for width in widths)):
                    self.table_widths[name] = list(widths)
        self.output_directory = data.get("output_directory") or self.output_directory
        self.namespace = data.get("namespace", "kimodo")
        self.start_frame = float(data.get("start_frame", 1))

    def save_preferences(self):
        """Persists user settings and history when preferences are available."""
        if self.prefs:
            self.prefs.set_raw_preferences({"state": self.snapshot()})
            self.prefs.save()

    def set_output_directory(self, directory):
        """Validates and immediately persists the download target.

        Args:
            directory (str): Absolute local directory or network-share path.

        Returns:
            str: Normalized directory path.
        """
        directory = os.path.expanduser(directory.strip())
        if not directory or not os.path.isabs(directory):
            raise ValueError("Choose an absolute download folder, or use Package Cache.")
        if os.path.exists(directory) and not os.path.isdir(directory):
            raise ValueError("The download folder points to a file. Choose a directory instead.")
        self.output_directory = os.path.normpath(directory)
        self.save_preferences()
        return self.output_directory

    def build_definition(self):
        """Combines current generation settings with enabled constraints.

        Returns:
            KimodoGenerationDefinition: Detached validated request.
        """
        data = kimodo.normalize_definition({"definition": self.definition, "constraints": self.constraints})
        return kimodo.KimodoGenerationDefinition.from_dict(data)

    def make_connection(self):
        """Creates a connection using the current in-memory bearer token.

        Returns:
            KimodoConnection: Runtime connection settings.
        """
        settings = dict(self.connection)
        settings.pop("auto_connect", None)
        return kimodo.KimodoConnection(token=self.token or None, **settings)

    def add_constraint(self, parameters, name=None):
        """Adds a detached constraint entry with a fresh stable identity.

        Args:
            parameters (dict): Native Kimodo constraint.
            name (str, optional): User-facing label.

        Returns:
            dict: New authoring entry.
        """
        kimodo.validate_constraints([parameters])
        entry = {"id": uuid.uuid4().hex, "name": name or f"{parameters['type']} {len(self.constraints) + 1}",
                 "enabled": True, "parameters": copy.deepcopy(parameters)}
        self.constraints.append(entry)
        return entry

    def import_constraints(self, path):
        """Appends demo JSON constraints without changing the input file.

        Args:
            path (str): Native constraint list or generation definition JSON.
        """
        data = read_json_dict(path)
        constraints = data.get("constraints") if isinstance(data, dict) else data
        kimodo.validate_constraints(constraints)
        for constraint in constraints:
            # Split keys so each pose can be named, timed, previewed, and disabled.
            for index, frame in enumerate(constraint["frame_indices"]):
                item = {key: ([value[index]] if key in (
                    "frame_indices", "root_positions", "local_joints_rot", "smooth_root_2d", "global_root_heading")
                    else value) for key, value in constraint.items()}
                self.add_constraint(item, f"{constraint['type']} at {frame + 1}")

    def export_constraints(self, path):
        """Writes enabled constraints in Kimodo's native format.

        Args:
            path (str): User-selected destination.
        """
        if write_json(path, self.build_definition().as_dict()["constraints"]) is None:
            raise OSError(f"Could not write {path}.")

    def save_setup(self, path):
        """Saves portable authoring data without machine settings or history.

        Args:
            path (str): User-selected JSON destination.
        """
        self.build_definition()
        if write_json(path, {"definition": self.definition, "constraints": self.constraints}) is None:
            raise OSError(f"Could not write {path}.")

    def load_setup(self, path):
        """Loads a tool setup or plain utility generation definition.

        Args:
            path (str): Input JSON file.
        """
        data = read_json_dict(path)
        if "definition" not in data:
            definition = kimodo.KimodoGenerationDefinition.from_dict(data).as_dict()
            constraints = definition.pop("constraints")
            definition["constraints"] = []
            data = {"definition": definition, "constraints": [
                {"id": uuid.uuid4().hex, "name": f"Constraint {index + 1}", "enabled": True, "parameters": value}
                for index, value in enumerate(constraints)]}
        saved = self.snapshot()
        saved.update(data)
        self.restore(saved)

    def add_job(self, response, connection, definition=None):
        """Records a job and its originating server for later reconnection.

        Args:
            response (dict): Submission response.
            connection (KimodoConnection): Originating server.
            definition (dict, optional): Immutable request snapshot.

        Returns:
            dict: Persistent history entry.
        """
        entry = dict(response, url=connection.url, definition=definition, paths={})
        self.jobs.append(entry)
        self.save_preferences()
        return entry
