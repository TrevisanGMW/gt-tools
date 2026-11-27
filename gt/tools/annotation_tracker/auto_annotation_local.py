"""Starts the loopback Bionic server and loads its configured vision model."""

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _lms_command():
    """Finds the Bionic/LM Studio CLI in Maya's environment.

    Returns:
        str: Absolute path of the LMS CLI.
    """
    executable = shutil.which("lms")
    if executable:
        return executable
    default = Path.home() / ".lmstudio" / "bin" / ("lms.exe" if os.name == "nt" else "lms")
    if default.is_file():
        return str(default)
    raise ValueError(
        "Bionic's lms CLI was not found. Install the CLI, or start the server and load the model manually."
    )


def _run_lms(arguments, timeout):
    """Runs one non-interactive CLI command without starting a shell.

    Args:
        arguments (list): CLI arguments apart from the executable.
        timeout (float): Maximum time to wait in seconds.

    Returns:
        str: Standard output.
    """
    try:
        result = subprocess.run(
            [_lms_command(), *arguments],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"Bionic timed out during lms {' '.join(arguments[:2])}.") from error
    if result.returncode:
        output = result.stderr.strip() or result.stdout.strip()
        lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output).strip().splitlines()
        message = lines[-1] if lines else f"Exit code {result.returncode}."
        raise ValueError(f"Bionic lms {' '.join(arguments[:2])} failed. {message[:350]}")
    return result.stdout


def get_running_local_endpoint(timeout=5):
    """Finds the HTTP base URL of the local server without starting it.

    Args:
        timeout (float): Maximum seconds to wait for Bionic's CLI.

    Returns:
        str: OpenAI-compatible base URL for the running local server.
    """
    status = json.loads(_run_lms(["server", "status", "--json"], timeout))
    port = status.get("port") if isinstance(status, dict) and status.get("running") else None
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Bionic's local server is stopped. Start it in Bionic or enable auto-start for annotation.")
    return f"http://localhost:{port}/v1"


def _list_models(opener, server, key, timeout):
    """Reads installed and loaded model metadata from Bionic.

    Args:
        opener (OpenerDirector): Loopback opener with redirects disabled.
        server (str): Endpoint scheme and authority.
        key (str): Optional API key.
        timeout (float): Metadata request timeout.

    Returns:
        list or None: Native Bionic model list, or None for a compatible gateway.
    """
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    request = urllib.request.Request(f"{server}/api/v1/models", headers=headers)
    try:
        with opener.open(request, timeout=timeout) as response:
            data = json.loads(response.read(2_000_000))
    except urllib.error.HTTPError as error:
        if error.code in (404, 405):
            return None
        if error.code in (401, 403):
            raise ValueError("Bionic rejected the API credential. Check the Key environment variable.") from error
        return None
    except (UnicodeError, ValueError):
        return None
    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, list):
        return None
    return [item for item in models if isinstance(item, dict)]


def _find_model(models, name):
    """Matches a configured model key, variant, or already-loaded identifier.

    Args:
        models (list): Installed model records from Bionic.
        name (str): Configured API model name.

    Returns:
        tuple: Matching record and whether its requested identifier is loaded.
    """
    for item in models:
        instances = item.get("loaded_instances") or []
        if any(isinstance(instance, dict) and instance.get("id") == name for instance in instances):
            return item, True
    for item in models:
        candidates = (item.get("key"), *(item.get("variants") or []))
        if name in candidates:
            return item, False
    available = [
        item["key"] for item in models
        if item.get("key") and (item.get("capabilities") or {}).get("vision")
    ]
    suffix = f" Installed vision models: {', '.join(available)}." if available else ""
    raise ValueError(f"Bionic does not have '{name}' installed. Run lms ls to find its model key.{suffix}")


def discover_vision_models(endpoint, key, opener, timeout=5):
    """Lists image-capable model IDs and loaded aliases for the local picker.

    Args:
        endpoint (str): Configured loopback inference URL.
        key (str): Optional local server credential.
        opener (OpenerDirector): HTTP opener for this endpoint.
        timeout (float): Maximum seconds to wait for the model inventory.

    Returns:
        list: Model ID, display name, and loaded flag for each choice.
    """
    parsed = urllib.parse.urlsplit(endpoint)
    try:
        models = _list_models(opener, f"{parsed.scheme}://{parsed.netloc}", key, timeout)
    except OSError as error:
        raise ValueError("Could not reach the Bionic server. Check the endpoint or use Detect Server.") from error
    if models is None:
        raise ValueError("This endpoint does not expose the Bionic model inventory. Enter a vision model ID manually.")

    choices = {}
    for item in models:
        if (item.get("capabilities") or {}).get("vision") is not True:
            continue
        key = item.get("key")
        name = item.get("display_name") or key
        aliases = {
            instance["id"] for instance in item.get("loaded_instances") or []
            if isinstance(instance, dict) and isinstance(instance.get("id"), str) and instance["id"]
        }
        for identifier in {key, *(item.get("variants") or []), *aliases}:
            if isinstance(identifier, str) and identifier:
                choices[identifier] = (identifier, name, identifier in aliases)
    return sorted(choices.values(), key=lambda choice: (not choice[2], choice[0].lower()))


def _eject_other_idle_models(models, selected, endpoint, timeout, quiet=False):
    """Releases other idle language models on the same local Bionic server.

    Args:
        models (list): Model inventory from the requested endpoint.
        selected (dict): Model record to keep, including its loaded aliases.
        endpoint (str): Configured loopback inference URL.
        timeout (float): Maximum seconds for each CLI request.
        quiet (bool): Suppresses console messages when an interactive progress window is visible.

    Returns:
        list: Diagnostics about any attempted unloads.
    """
    others = {
        instance["id"] for item in models if item is not selected and item.get("type") == "llm"
        for instance in item.get("loaded_instances") or []
        if isinstance(instance, dict) and isinstance(instance.get("id"), str)
        and instance["id"] and not instance["id"].startswith("-")
    }
    if not others:
        return []
    try:
        server_port = urllib.parse.urlsplit(get_running_local_endpoint(min(timeout, 5))).port
        configured = urllib.parse.urlsplit(endpoint)
        port = configured.port or (443 if configured.scheme == "https" else 80)
        if port != server_port:
            return ["Kept other models loaded because the configured endpoint is on a different Bionic port."]
        loaded = json.loads(_run_lms(["ps", "--json"], min(timeout, 5)))
        if not isinstance(loaded, list):
            raise ValueError("Bionic did not return loaded model statuses.")
    except (OSError, ValueError) as error:
        return [f"Could not check whether other local models were idle. {error}"]

    idle = {
        entry.get("identifier") for entry in loaded
        if isinstance(entry, dict) and entry.get("status") == "idle" and entry.get("type") == "llm"
        and not entry.get("queued") and not entry.get("deviceIdentifier")
    }
    warnings = []
    for identifier in sorted(others & idle):
        if not quiet:
            print(f"[Auto Annotate] Unloading idle Bionic model '{identifier}'...", flush=True)
        try:
            _run_lms(["unload", identifier], timeout)
        except (OSError, ValueError) as error:
            warnings.append(f"Could not unload '{identifier}'. {error}")
    kept = sorted(others - idle)
    if kept:
        warnings.append(f"Kept these Bionic models loaded because they were not idle local models: {', '.join(kept)}.")
    return warnings


def prepare_local_model(endpoint, name, key, timeout, opener, auto_load=True, eject_others=False, quiet=False):
    """Starts the configured loopback server and loads a local vision model as needed.

    Args:
        endpoint (str): Configured loopback inference URL.
        name (str): Model name used in the inference request.
        key (str): Optional Bionic server credential.
        timeout (float): Inference configuration's timeout in seconds.
        opener (OpenerDirector): Loopback HTTP opener shared with inference.
        auto_load (bool): Starts the local server and explicitly loads the selected model when needed.
        eject_others (bool): Unloads other models whose CLI status is idle.
        quiet (bool): Suppresses console messages when a progress window is visible.

    Returns:
        list: Non-blocking local preparation diagnostics.
    """
    parsed = urllib.parse.urlsplit(endpoint)
    server = f"{parsed.scheme}://{parsed.netloc}"
    probe_timeout = min(timeout, 5)
    try:
        models = _list_models(opener, server, key, probe_timeout)
    except OSError:
        if parsed.scheme != "http" or not auto_load:
            raise ValueError("Could not reach the local VLM endpoint. Check its address and server status.") from None
        port = parsed.port or 80
        address = "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname
        if not quiet:
            print(f"[Auto Annotate] Starting the Bionic server on port {port}...", flush=True)
        try:
            _run_lms(["server", "start", "--port", str(port), "--bind", address], timeout)
        except ValueError as start_error:
            try:
                models = _list_models(opener, server, key, probe_timeout)
            except OSError:
                raise start_error from None
        else:
            try:
                models = _list_models(opener, server, key, probe_timeout)
            except OSError as error:
                raise ValueError("Bionic started, but its local API is still unreachable.") from error
    if models is None:
        if eject_others:
            return ["Kept other local models loaded because this endpoint has no Bionic model inventory."]
        return []
    item, loaded = _find_model(models, name)
    if item.get("type") == "embedding" or (item.get("capabilities") or {}).get("vision") is False:
        raise ValueError(f"'{name}' is not an image-capable Bionic model. Choose a vision model in Annotation Setup.")
    if name.startswith("-"):
        raise ValueError("Choose a valid Bionic model key.")
    warnings = _eject_other_idle_models(models, item, endpoint, timeout, quiet) if eject_others else []
    if loaded or not auto_load:
        return warnings
    if not quiet:
        print(f"[Auto Annotate] Loading local vision model '{name}'...", flush=True)
    try:
        _run_lms(["load", name, "--identifier", name, "--yes"], timeout)
    except ValueError as load_error:
        try:
            refreshed = _list_models(opener, server, key, probe_timeout)
            if refreshed is not None and _find_model(refreshed, name)[1]:
                return warnings
        except (OSError, ValueError):
            pass
        raise load_error from None
    return warnings
