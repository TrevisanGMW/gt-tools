"""Read-only Docker diagnostics and guarded removal of a selected deployment image."""

import json
import re
import time

from gt.tools.kimodo_generator import kimodo_generator_docker as docker


def _full_container_ids(container_ids, executable=None):
    """Normalizes Compose versions that report shortened container IDs.

    Args:
        container_ids (list): Container IDs returned by Compose.
        executable (str, optional): Docker executable.

    Returns:
        list: Canonical full container IDs.
    """
    if all(re.fullmatch(r"[0-9a-f]{64}", value) for value in container_ids):
        return container_ids
    output = docker._run(["container", "inspect", "--format", "{{.Id}}"] + list(container_ids), executable)
    result = output.splitlines()
    if len(result) != len(container_ids) or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in result):
        raise ValueError("Could not resolve complete Docker container IDs. Refresh the deployment and try again.")
    return result


def project_services(directory, executable=None):
    """Reads container identity/state for only the selected Compose project.

    Args:
        directory (str): Prepared deployment folder.
        executable (str, optional): Docker executable.

    Returns:
        list: Compose service records across supported JSON output formats.
    """
    output = docker._compose(directory, ["ps", "--all", "--format", "json"], executable)
    if not output.strip():
        return []
    try:
        values = json.loads(output)
        return values if isinstance(values, list) else [values]
    except ValueError:
        return [json.loads(line) for line in output.splitlines() if line.strip()]


def logs_target(directory, service="text-encoder", executable=None):
    """Resolves the supported Desktop launcher after verifying the selected service.

    Args:
        directory (str): Prepared deployment folder.
        service (str): Bridge or text-encoder service.
        executable (str, optional): Docker executable.

    Returns:
        str: Docker Desktop dashboard URI. Container routes are internal-only.
    """
    if service not in ("bridge", "text-encoder"):
        raise ValueError("Choose bridge or text-encoder logs.")
    for container in project_services(directory, executable):
        container_id = container.get("ID", "")
        if container.get("Service") == service and re.fullmatch(r"[0-9a-f]{12,64}", container_id):
            container_id = _full_container_ids([container_id], executable)[0]
            return "docker-desktop://dashboard/open"
    raise ValueError(f"No {service} container exists for this deployment. Use Connect / Start first.")


def build_progress(directory, after_offset=0):
    """Reads a bounded log tail for truthful, indeterminate build activity.

    Args:
        directory (str): Deployment directory.
        after_offset (int): Ignore output from older builds before this byte offset.

    Returns:
        str: Most recent nonempty build output line.
    """
    path = docker.deployment_directory(directory) / "logs" / "build.log"
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            size = stream.tell()
            if size <= after_offset:
                return "Preparing sources and resolving revisions..."
            stream.seek(max(after_offset, size - 4096))
            text = stream.read().decode("utf-8", errors="replace")
    except OSError:
        return "Preparing sources and resolving revisions..."
    lines = [line.strip() for line in re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text).replace("\r", "\n").splitlines()
             if line.strip()]
    return lines[-1][:220] if lines else "Preparing sources and resolving revisions..."


def encoder_progress(directory):
    """Reads actual byte callbacks exported by the container, without guessing file sizes.

    Args:
        directory (str): Deployment directory.

    Returns:
        dict: Stage, detail, and optional measured percentage.
    """
    path = docker.deployment_directory(directory) / "logs" / "encoder-progress.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"stage": "unknown", "detail": "Live encoder progress is not available yet. Check Encoder Logs. "
                "Older images need a rebuild and restart to enable reporting."}
    stage = data.get("stage", "unknown")
    if stage not in ("ready", "failed") and time.time() - data.get("updated_at", 0) > 30:
        return {"stage": "unknown", "detail": "Encoder progress is stale. Check the encoder container logs."}
    if stage == "downloading" and data.get("total_bytes", 0) > 0:
        total = max(1, data["total_bytes"])
        completed = min(total, max(0, data.get("downloaded_bytes", 0)))
        return {"stage": stage, "percent": int(completed * 100 / total),
                "detail": f"Downloading encoder: {completed / 1024 ** 3:.2f} / {total / 1024 ** 3:.2f} GiB "
                          "(known downloads)"}
    details = {"loading": "Loading encoder model weights; downloads are complete or cached.",
               "ready": "Text encoder ready.", "failed": "Encoder failed. Open Encoder Logs for the traceback."}
    return {"stage": stage, "detail": details.get(stage, "Initializing text encoder...")}


def image_removal_preview(directory, executable=None):
    """Validates stopped ownership and previews the exact image/container removal scope.

    Args:
        directory (str): Prepared deployment folder.
        executable (str, optional): Docker executable.

    Returns:
        dict: Image reference/ID and stopped container names to present for confirmation.
    """
    docker.check_engine(executable)
    docker._assert_project_owner(directory, executable)
    configuration = json.loads(docker._compose(directory, ["config", "--format", "json"], executable))
    image = configuration["services"]["bridge"]["image"]
    services = project_services(directory, executable)
    owned = [item for item in services if item.get("Service") in ("bridge", "text-encoder")]
    if any(item.get("State") not in ("exited", "created", "dead") for item in owned):
        raise ValueError("Stop the bridge and encoder before removing their image.")
    owned_ids = set(_full_container_ids([item["ID"] for item in owned], executable))
    inspected = json.loads(docker._run(["image", "inspect", image], executable))
    image_id = inspected[0]["Id"]
    references = docker._run(["ps", "--all", "--no-trunc", "--filter", f"ancestor={image_id}",
                              "--format", "{{.ID}}"], executable).splitlines()
    if any(container_id not in owned_ids for container_id in references):
        raise ValueError("Another container uses this image. Its image and containers were left unchanged.")
    return {"image": image, "image_id": image_id,
            "containers": [item.get("Name", item["ID"]) for item in owned]}


def remove_image(directory, expected_image_id, executable=None):
    """Revalidates a confirmed preview and removes only stopped owned containers and their image tag.

    Args:
        directory (str): Prepared deployment folder.
        expected_image_id (str): Image ID approved in the preview.
        executable (str, optional): Docker executable.

    Returns:
        str: Removed image reference.
    """
    preview = image_removal_preview(directory, executable)
    if preview["image_id"] != expected_image_id:
        raise ValueError("The image changed after the removal preview. Review it again before removing.")
    docker._compose(directory, ["rm", "--force", "bridge", "text-encoder"], executable)
    docker._run(["image", "rm", preview["image"]], executable)
    return preview["image"]
