"""Import-safe Docker deployment preparation and project-scoped local lifecycle."""

import json
import logging
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import time
import urllib.parse

from gt.utils import kimodo
from gt.tools.kimodo_generator import kimodo_generator_sources as sources

KIMODO_REVISION = sources.KIMODO_REVISION
VISER_REVISION = sources.VISER_REVISION
DEFAULT_PROJECT_NAME = "kimodo-bridge"
RESOURCE_DIRECTORY = Path(__file__).parent / "docker"
DEPLOYMENT_SCHEMA = 1
logger = logging.getLogger(__name__)


def default_directory():
    """Leaves new deployments unset until the user explicitly chooses a folder.

    Returns:
        str: Empty initial deployment directory.
    """
    return ""


def validate_local_url(url):
    """Keeps deployment credentials scoped to localhost in managed Docker mode.

    Args:
        url (str): Requested bridge origin.
    """
    if urllib.parse.urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Managed Docker requires a localhost URL. Use Existing mode for network servers.")


def deployment_directory(directory):
    """Validates an explicit absolute deployment folder.

    Args:
        directory (str): Requested project directory.

    Returns:
        Path: Absolute directory, without creating it.
    """
    if not directory or not os.path.isabs(os.path.expanduser(str(directory))):
        raise ValueError("Choose an absolute Kimodo Docker deployment folder.")
    result = Path(directory).expanduser().resolve()
    if result == Path(result.anchor):
        raise ValueError("Choose a dedicated Kimodo folder, not a drive or filesystem root.")
    return result


def read_deployment(directory):
    """Reads the ownership marker required for Docker mutations.

    Args:
        directory (str): Dedicated deployment folder.

    Returns:
        dict: Validated deployment identity and pinned revisions.
    """
    directory = deployment_directory(directory)
    try:
        data = json.loads((directory / "deployment.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Prepare this Kimodo deployment first; deployment.json is missing or invalid.") from error
    if not isinstance(data, dict):
        raise ValueError("The deployment marker must be a JSON object.")
    project = data.get("project_name", "")
    if not isinstance(project, str):
        raise ValueError("The deployment project name must be a string.")
    known_tool = data.get("tool") == "kimodo_generator" or project.startswith(("gt-kimodo-", "kimodo-bridge"))
    if (data.get("schema_version") != DEPLOYMENT_SCHEMA or not known_tool
            or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", project)):
        raise ValueError("This folder is not a supported GT Kimodo Docker deployment.")
    return data


def find_docker(executable=None):
    """Finds Docker Desktop even when its CLI is absent from the inherited PATH.

    Args:
        executable (str, optional): User-selected Docker executable.

    Returns:
        str: Absolute Docker CLI path.
    """
    if executable:
        candidate = Path(executable).expanduser()
        if candidate.is_absolute() and candidate.is_file():
            return str(candidate)
        raise ValueError("The selected Docker executable does not exist or is not an absolute path.")
    found = shutil.which("docker")
    if found:
        return found
    for root, relative in ((os.environ.get("LOCALAPPDATA"), "Programs/DockerDesktop/resources/bin/docker.exe"),
                           (os.environ.get("ProgramFiles"), "Docker/Docker/resources/bin/docker.exe")):
        if root and (Path(root) / relative).is_file():
            return str(Path(root) / relative)
    raise ValueError("Docker CLI not found. Install/start Docker Desktop or select its docker.exe.")


def _run(arguments, executable=None, timeout=60, log_path=None):
    """Runs a shell-free Docker command with credential helpers on PATH.

    Args:
        arguments (list): Docker command arguments, without secrets.
        executable (str, optional): Explicit CLI path.
        timeout (float): Command timeout in seconds.
        log_path (Path, optional): Persistent output file for long builds.

    Returns:
        str: UTF-8 output, or build log path.
    """
    executable = find_docker(executable)
    environment = os.environ.copy()
    environment["PATH"] = os.path.dirname(executable) + os.pathsep + environment.get("PATH", "")
    environment.update(PYTHONUTF8="1", PYTHONUNBUFFERED="1")
    options = {"env": environment, "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
               "timeout": timeout, "stdin": subprocess.DEVNULL}
    command = [executable] + list(arguments)
    try:
        if log_path:
            with open(log_path, "ab") as stream:
                result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, **options)
            detail = f"See {log_path}"
        else:
            result = subprocess.run(command, capture_output=True, **options)
            detail = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        if result.returncode:
            raise RuntimeError(f"Docker command failed ({result.returncode}). {detail}")
        return str(log_path) if log_path else result.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.TimeoutExpired as error:
        detail = f" Inspect {log_path}." if log_path else ""
        raise TimeoutError(f"Docker command exceeded {timeout:g} seconds.{detail}") from error


def check_engine(executable=None):
    """Requires a local Linux engine before managing host bind mounts.

    Args:
        executable (str, optional): Explicit Docker CLI.

    Returns:
        dict: Engine identity and platform.
    """
    host = os.environ.get("DOCKER_HOST", "")
    if host and not host.startswith(("unix://", "npipe://")):
        raise ValueError("Managed Docker mode requires a local engine. Connect to remote bridges by URL.")
    context = json.loads(_run(["context", "inspect"], executable))
    endpoint = context[0].get("Endpoints", {}).get("docker", {}).get("Host", "")
    if not host and not endpoint.startswith(("unix://", "npipe://")):
        raise ValueError("The active Docker context is remote. Select a local context or use Existing mode.")
    info = json.loads(_run(["info", "--format", "{{json .}}"], executable))
    if info.get("OSType") != "linux":
        raise ValueError("Switch Docker Desktop to Linux containers before starting Kimodo.")
    _run(["compose", "version"], executable)
    return {"name": info.get("Name"), "platform": info.get("OperatingSystem"), "context": context[0]["Name"]}


def _write_new(path, text):
    """Creates a UTF-8 file without replacing existing user configuration.

    Args:
        path (Path): Destination path.
        text (str): Initial file contents.
    """
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except FileExistsError:
        return


def _docker_project_names(executable=None):
    """Collects existing project and image names without creating Docker resources.

    Args:
        executable (str, optional): Docker executable.

    Returns:
        set: Names already in use by containers or image repositories.
    """
    names = set()
    try:
        output = _run(["ps", "--all", "--format", '{{.Label "com.docker.compose.project"}}'],
                      executable, timeout=5)
        names.update(output.splitlines())
        output = _run(["image", "ls", "--format", "{{.Repository}}"], executable, timeout=5)
        names.update(output.splitlines())
    except (OSError, RuntimeError, ValueError) as error:
        logger.debug("Docker name discovery unavailable; checking adjacent deployments: %s", error)
    return names


def validate_image_name(name):
    """Validates a local image repository name without silently rewriting user input.

    Args:
        name (str): Requested image name, without a tag.

    Returns:
        str: Validated name.
    """
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", name):
        raise ValueError("Image names must use lowercase letters, numbers, dots, underscores, or hyphens; omit tags.")
    return name


def choose_project_name(directory, executable=None, base_name=None):
    """Uses a readable name, adding a numeric suffix only for existing names.

    Args:
        directory (Path): New deployment folder.
        executable (str, optional): Docker executable.
        base_name (str, optional): Requested local image/project name.

    Returns:
        str: Available project and default image repository name.
    """
    occupied = _docker_project_names(executable)
    for sibling in directory.parent.iterdir():
        try:
            if sibling != directory and sibling.is_dir():
                marker = sibling / "deployment.json"
                if not marker.is_file():
                    continue
                data = json.loads(marker.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("project_name"), str):
                    occupied.add(data["project_name"])
                    if isinstance(data.get("image_repository"), str):
                        occupied.add(data["image_repository"])
        except (OSError, ValueError):
            continue
    base_name = validate_image_name(base_name or DEFAULT_PROJECT_NAME)
    candidate = base_name
    suffix = 2
    while candidate in occupied or candidate.replace(".", "-") in occupied:
        candidate = f"{base_name}-{suffix}"
        suffix += 1
    return candidate


def prepare_deployment(directory, hf_token_file=None, use_stable_revisions=None, executable=None, image_name=None):
    """Creates an organized deployment while retaining existing credentials and data.

    Args:
        directory (str): Absolute dedicated deployment directory.
        hf_token_file (str, optional): Existing Hugging Face token file to copy once.
        use_stable_revisions (bool, optional): Use pinned sources; new deployments default to latest.
        executable (str, optional): Docker executable for name conflict discovery.
        image_name (str, optional): Preferred local image name; version tag is managed separately.

    Returns:
        dict: Deployment identity and source revisions.
    """
    directory = deployment_directory(directory)
    if (directory / "deployment.json").exists():
        data = read_deployment(str(directory))
    else:
        if directory.exists() and any(entry.name != "source" for entry in directory.iterdir()):
            raise ValueError("Choose an empty dedicated directory; this folder contains unrelated files.")
        directory.parent.mkdir(parents=True, exist_ok=True)
        requested = validate_image_name(image_name or DEFAULT_PROJECT_NAME)
        repository = choose_project_name(directory, executable, requested)
        project = repository.replace(".", "-")
        data = {"schema_version": DEPLOYMENT_SCHEMA, "tool": "kimodo_generator", "project_name": project,
                "image_name": requested, "image_repository": repository,
                "kimodo_revision": KIMODO_REVISION, "viser_revision": VISER_REVISION,
                "use_stable_revisions": False}
        directory.mkdir(parents=True, exist_ok=True)
        _write_new(directory / "deployment.json", json.dumps(data, indent=2) + "\n")
    if use_stable_revisions is not None:
        data["use_stable_revisions"] = bool(use_stable_revisions)
        kimodo._write_json(str(directory / "deployment.json"), data)
    for name in ("configuration", "secrets", "models", "jobs", "logs", "source"):
        (directory / name).mkdir(exist_ok=True)
    # These files are generated resources; .env and secrets remain user-owned.
    for name in ("Dockerfile", "compose.yaml", ".env.example"):
        shutil.copyfile(RESOURCE_DIRECTORY / name, directory / "configuration" / name)
    shutil.copyfile(RESOURCE_DIRECTORY / "README.md", directory / "README.md")
    settings = (RESOURCE_DIRECTORY / ".env.example").read_text(encoding="utf-8")
    settings = re.sub(r"(?m)^COMPOSE_PROJECT_NAME=.*$", f"COMPOSE_PROJECT_NAME={data['project_name']}", settings)
    repository = data.get("image_repository", data["project_name"])
    settings = re.sub(r"(?m)^KIMODO_IMAGE=.*$", f"KIMODO_IMAGE={repository}:1.12.0", settings)
    _write_new(directory / "configuration" / ".env", settings)
    _write_new(directory / "source" / ".dockerignore", "**/.git\n**/__pycache__\n**/*.pyc\nbridge/\ngt-bridge/\n")
    _write_new(directory / "secrets" / "bridge_token", secrets.token_urlsafe(48) + "\n")
    if hf_token_file is None:
        hf_home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
        hf_token_file = os.environ.get("HF_TOKEN_PATH") or str(Path(hf_home) / "token")
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not hf_token and hf_token_file and Path(hf_token_file).is_file():
        hf_token = Path(hf_token_file).read_text(encoding="utf-8").strip()
    token_destination = directory / "secrets" / "hf_token"
    if not token_destination.exists() or not token_destination.stat().st_size:
        if hf_token:
            token_destination.write_text(hf_token.strip() + "\n", encoding="utf-8")
        else:
            _write_new(token_destination, "")
    if os.name != "nt":
        (directory / "secrets").chmod(0o700)
        for name in ("bridge_token", "hf_token"):
            (directory / "secrets" / name).chmod(0o600)
    refresh_bridge(str(directory))
    if image_name is not None:
        configure_image(str(directory), image_name, executable)
        data = read_deployment(str(directory))
    return data


def configure_image(directory, image_name, executable=None):
    """Applies an explicit next-build image choice while preserving the project identity.

    Args:
        directory (str): Prepared deployment folder.
        image_name (str): Requested local repository name.
        executable (str, optional): Docker executable.

    Returns:
        str: Selected image reference.
    """
    requested = validate_image_name(image_name)
    data = read_deployment(directory)
    settings = deployment_directory(directory) / "configuration" / ".env"
    lines = settings.read_text(encoding="utf-8").splitlines()
    current = next((line.split("=", 1)[1].strip().strip("\"'") for line in lines
                    if line.startswith("KIMODO_IMAGE=")), "")
    repository = current.rsplit(":", 1)[0] if ":" in current else current
    if data.get("image_name") == requested and repository == data.get("image_repository"):
        return current
    allocated = repository if repository == requested else choose_project_name(
        deployment_directory(directory), executable, requested)
    image = f"{allocated}:1.12.0"
    replaced = [f"KIMODO_IMAGE={image}" if line.startswith("KIMODO_IMAGE=") else line for line in lines]
    if not any(line.startswith("KIMODO_IMAGE=") for line in lines):
        replaced.append(f"KIMODO_IMAGE={image}")
    temporary = settings.with_suffix(".env.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(replaced) + "\n")
    os.replace(str(temporary), str(settings))
    data.update(image_name=requested, image_repository=allocated)
    kimodo._write_json(str(deployment_directory(directory) / "deployment.json"), data)
    return image


def refresh_bridge(directory):
    """Stages only the import-safe bridge bundle for inclusion in the image.

    Args:
        directory (str): Prepared deployment folder.
    """
    read_deployment(directory)
    source = deployment_directory(directory) / "source"
    package = Path(kimodo.__file__).parents[1]
    for name in ("gt", "gt/core", "gt/utils"):
        target = source / "kimodo-bridge" / name
        target.mkdir(parents=True, exist_ok=True)
        _write_new(target / "__init__.py", "\"\"\"Minimal GT Kimodo bridge runtime.\"\"\"\n")
    for relative in ("utils/kimodo.py", "core/io.py"):
        shutil.copyfile(package / relative, source / "kimodo-bridge" / "gt" / relative)
    shutil.copyfile(RESOURCE_DIRECTORY / "container_runtime.py", source / "container_runtime.py")
    shutil.copyfile(RESOURCE_DIRECTORY / "Dockerfile", source / "Dockerfile")
    shutil.copyfile(RESOURCE_DIRECTORY / "Dockerfile", deployment_directory(directory) / "configuration" / "Dockerfile")
    shutil.copyfile(RESOURCE_DIRECTORY / "container_progress.py", source / "container_progress.py")


def _compose(directory, arguments, executable=None, timeout=60, log_path=None):
    """Runs Compose with an explicit file, project name, and environment file.

    Args:
        directory (str): Prepared deployment directory.
        arguments (list): Compose operation arguments.
        executable (str, optional): Docker executable.
        timeout (float): Command timeout.
        log_path (Path, optional): Long-command output file.

    Returns:
        str: Command output.
    """
    data = read_deployment(directory)
    configuration = deployment_directory(directory) / "configuration"
    if arguments and arguments[0] in ("build", "up", "stop", "rm"):
        _assert_project_owner(directory, executable)
    prefix = ["compose", "--project-name", data["project_name"], "--env-file", str(configuration / ".env"),
              "--file", str(configuration / "compose.yaml")]
    return _run(prefix + list(arguments), executable, timeout, log_path)


def _assert_project_owner(directory, executable=None):
    """Rejects a same-name Docker project owned by a different deployment folder.

    Args:
        directory (str): Prepared deployment folder.
        executable (str, optional): Docker executable.
    """
    project = read_deployment(directory)["project_name"]
    output = _run(["ps", "--all", "--filter", f"label=com.docker.compose.project={project}",
                   "--format", '{{.ID}}|{{.Label "com.docker.compose.project.working_dir"}}'], executable)
    expected = os.path.normcase(str(deployment_directory(directory) / "configuration"))
    for line in output.splitlines():
        container_id, separator, working_directory = line.partition("|")
        owner = os.path.normcase(str(Path(working_directory).resolve())) if separator and working_directory else None
        if owner != expected:
            raise ValueError(f"Docker project {project} belongs to another deployment folder. "
                             "Its containers were left unchanged. Prepare a new dedicated deployment folder.")


def _clone_source(path, repository, revision, previous_revision=None):
    """Fetches a pinned dependency without changing an existing checkout.

    Args:
        path (Path): Owned source checkout directory.
        repository (str): Upstream Git repository URL.
        revision (str): Required commit hash.
        previous_revision (str, optional): Previously recorded commit allowed for a clean update.
    """
    sources.checkout_source(path, repository, revision, previous_revision)


def build_image(directory, executable=None, use_stable_revisions=None, image_name=None):
    """Builds latest sources by default, falling back to stable commits once if needed.

    Args:
        directory (str): Prepared deployment folder.
        executable (str, optional): Docker executable.
        use_stable_revisions (bool, optional): Override the saved revision policy for this build.
        image_name (str, optional): Apply this repository name before building.

    Returns:
        str: Persistent build log path.
    """
    check_engine(executable)
    if image_name is not None:
        configure_image(directory, image_name, executable)
    data = read_deployment(directory)
    if use_stable_revisions is None:
        use_stable_revisions = data.get("use_stable_revisions", False)
    data["use_stable_revisions"] = bool(use_stable_revisions)
    kimodo._write_json(str(deployment_directory(directory) / "deployment.json"), data)
    stable = sources.stable_revisions()
    source = deployment_directory(directory) / "source" / "kimodo"
    log_path = deployment_directory(directory) / "logs" / "build.log"
    selected, revision_source = stable, "stable"
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write("Build requested: resolving source revisions...\n")
        stream.flush()
        if not use_stable_revisions:
            try:
                selected, revision_source = sources.latest_revisions(), "latest"
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                revision_source = "stable_fallback"
                stream.write(f"Latest source lookup failed; using stable fallback. {error}\n")
        stream.flush()
        for attempt in range(2):
            try:
                for key, path, repository in (
                        ("kimodo_revision", source, sources.KIMODO_REPOSITORY),
                        ("viser_revision", source / "kimodo-viser", sources.VISER_REPOSITORY)):
                    _clone_source(path, repository, selected[key], previous_revision=data.get(key))
                    data[key] = selected[key]
                    kimodo._write_json(str(deployment_directory(directory) / "deployment.json"), data)
                refresh_bridge(directory)
                stream.write(f"Building {revision_source}: {json.dumps(selected, sort_keys=True)}\n")
                stream.flush()
                _compose(directory, ["build", "bridge"], executable, timeout=7200, log_path=log_path)
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                if attempt or revision_source != "latest" or selected == stable:
                    raise
                stream.write(f"Latest build failed; retrying stable fallback once. {error}\n")
                stream.flush()
                selected, revision_source = stable, "stable_fallback"
                continue
            data.update(revision_source=revision_source, last_successful_build=dict(selected))
            kimodo._write_json(str(deployment_directory(directory) / "deployment.json"), data)
            return str(log_path)


def bridge_token(directory):
    """Reads the local deployment token for in-memory HTTP connections.

    Args:
        directory (str): Prepared deployment folder.

    Returns:
        str: Bridge access token.
    """
    read_deployment(directory)
    token = (deployment_directory(directory) / "secrets" / "bridge_token").read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("The deployment bridge token is empty. Configure secrets/bridge_token before starting.")
    return token


def _verify_identity(directory, health):
    """Rejects another service at the requested URL before managing containers.

    Args:
        directory (str): Prepared deployment folder.
        health (dict): Authenticated bridge health response.
    """
    expected = read_deployment(directory)["project_name"]
    if health.get("runtime", {}).get("deployment_id") != expected:
        raise ValueError("This URL belongs to another bridge. Choose this deployment's published port.")


def start(directory, connection, executable=None):
    """Starts the selected local project and waits only for the lightweight bridge.

    Args:
        directory (str): Prepared deployment folder.
        connection (KimodoConnection): Local authenticated bridge connection.
        executable (str, optional): Docker executable.

    Returns:
        dict: Bridge health; encoder/model readiness is reported separately.
    """
    validate_local_url(connection.url)
    check_engine(executable)
    configuration = json.loads(_compose(directory, ["config", "--format", "json"], executable))
    bridge = configuration["services"]["bridge"]
    ports = bridge.get("ports", [])
    published = [int(entry["published"]) for entry in ports if int(entry["target"]) == 7861]
    parsed_url = urllib.parse.urlsplit(connection.url)
    if (parsed_url.port or (443 if parsed_url.scheme == "https" else 80)) not in published:
        raise ValueError("The bridge URL port does not match BRIDGE_PORT in configuration/.env.")
    if bridge.get("environment", {}).get("GT_KIMODO_DEPLOYMENT_ID") != read_deployment(directory)["project_name"]:
        raise ValueError("Keep COMPOSE_PROJECT_NAME consistent with deployment.json before starting services.")
    token_path = deployment_directory(directory) / "secrets" / "hf_token"
    if not token_path.is_file() or not token_path.read_text(encoding="utf-8").strip():
        raise ValueError("Add your Hugging Face credential to secrets/hf_token before starting Kimodo.")
    client = kimodo.KimodoClient(connection)
    try:
        health = client.health()
    except ConnectionError:
        health = None
    if health:
        _verify_identity(directory, health)
        return health  # Connecting must not recreate a healthy server after an image was rebuilt.
    _compose(directory, ["up", "--detach", "--no-build", "--pull", "never"], executable, timeout=120)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            health = client.health()
            _verify_identity(directory, health)
            return health
        except ConnectionError:
            time.sleep(0.5)
    raise TimeoutError("Bridge startup exceeded 90 seconds. Use View Docker Logs to inspect this deployment.")


def stop(directory, connection, executable=None):
    """Stops only this idle deployment, preserving all bind-mounted data.

    Args:
        directory (str): Prepared deployment folder.
        connection (KimodoConnection): Local authenticated bridge connection.
        executable (str, optional): Docker executable.

    Returns:
        dict: Bridge shutdown acknowledgement.
    """
    validate_local_url(connection.url)
    check_engine(executable)
    client = kimodo.KimodoClient(connection)
    try:
        health = client.health()
    except ConnectionError:
        services = _compose(directory, ["ps", "--status", "running", "--services"], executable).splitlines()
        if "bridge" in services:
            raise ValueError("The bridge container is running but unreachable. Inspect its logs before stopping it.")
        health = None
    if health:
        _verify_identity(directory, health)
        result = client.shutdown()
    else:
        result = {"stopping": True}
    _compose(directory, ["stop", "--timeout", "30", "bridge", "text-encoder"], executable, timeout=90)
    return result


def export_logs(directory, executable=None):
    """Saves recent stdout/stderr from only this Compose project.

    Args:
        directory (str): Prepared deployment folder.
        executable (str, optional): Docker executable.

    Returns:
        str: Log file path, including import errors and encoder startup output.
    """
    path = deployment_directory(directory) / "logs" / "containers.log"
    output = _compose(directory, ["logs", "--no-color", "--tail", "200"], executable)
    path.write_text(output, encoding="utf-8")
    return str(path)


def encoder_status(directory, executable=None):
    """Describes Docker encoder readiness without starting or changing containers.

    Args:
        directory (str): Prepared deployment directory.
        executable (str, optional): Docker executable.

    Returns:
        dict: Diagnostic status and user-facing detail.
    """
    output = _compose(directory, ["ps", "--all", "--format", "json", "text-encoder"], executable)
    services = json.loads(output) if output.strip() else []
    if isinstance(services, dict):
        services = [services]
    if not services:
        return {"status": "unavailable", "detail": "Encoder container is absent. Use Connect / Start."}
    service = services[0]
    state, health = service.get("State"), service.get("Health")
    if state == "running" and health == "starting":
        return {"status": "starting", "detail": "Encoder is starting: model weights may be downloading or loading. "
                "First startup can take several minutes. Use View Docker Logs for progress, then test again."}
    if state != "running":
        return {"status": "unavailable", "detail": f"Encoder container is {state or 'not running'} "
                f"(exit code {service.get('ExitCode', 'unknown')}). Use View Docker Logs to inspect the cause."}
    return {"status": "unavailable", "detail": "Encoder is running but not accepting requests. "
            "Use View Docker Logs to check startup progress or errors, then test again."}
