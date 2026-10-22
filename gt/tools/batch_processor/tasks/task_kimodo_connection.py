"""Import-safe connection settings shared by Kimodo batch runtime and discovery."""

import copy
import os
import re
import time
import urllib.parse

from gt.utils import kimodo
from gt.tools.batch_processor.tasks.task_kimodo_base import resolve_path
from gt.tools.kimodo_generator import kimodo_generator_docker as docker


def resolve_settings(settings, project=None, task=None):
    """Resolves Docker references without storing credentials in a batch project.

    Args:
        settings (dict): Serialized task settings.
        project (BatchProcessorModel, optional): Owning project for path variables.
        task (BatchTask, optional): Task for path variables.

    Returns:
        dict: Detached runtime settings.
    """
    resolved = copy.deepcopy(settings)
    options = resolved.setdefault("docker", {"directory": "", "executable": ""})
    for key in ("directory", "executable"):
        options[key] = resolve_path(options.get(key, ""), project, task)
    source = authentication_source(resolved)
    if source["kind"] == "deployment":
        options["directory"] = source["reference"]
    return resolved


def authentication_source(settings):
    """Resolves credential references without reading or exposing secret values.

    Args:
        settings (dict): Resolved task settings.

    Returns:
        dict: Effective credential kind and its file/directory/environment reference.
    """
    parameters = settings["connection"]
    mode = parameters.get("mode", "existing")
    policy = settings.get("authentication", "auto")
    if policy not in ("auto", "environment", "none"):
        raise ValueError("Choose Automatic, Environment variable, or No authentication under Credentials.")
    if mode == "docker":
        return {"kind": "deployment", "reference": settings.get("docker", {}).get("directory", "")}
    if policy == "none":
        return {"kind": "none", "reference": ""}
    if policy == "auto" and mode == "existing":
        try:
            docker.validate_local_url(parameters["url"])
        except ValueError:
            local = False
        else:
            local = True
        if local:
            directory = settings.get("docker", {}).get("directory", "").strip()
            if not directory:
                saved = generator_settings()
                current_url = urllib.parse.urlsplit(parameters["url"])
                saved_url = urllib.parse.urlsplit(saved["connection"]["url"])
                try:
                    docker.validate_local_url(saved["connection"]["url"])
                except ValueError:
                    pass
                else:
                    if (saved["connection"].get("mode") == "docker"
                            and (current_url.scheme, current_url.port) == (saved_url.scheme, saved_url.port)):
                        directory = saved["docker"].get("directory", "").strip()
            if directory:
                return {"kind": "deployment", "reference": directory}
    name = settings.get("token_environment", "").strip()
    if policy == "environment" or name:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or re.fullmatch(r"[a-fA-F0-9]{32,}", name):
            raise ValueError("Enter an environment variable NAME under Token variable name, not the token value.")
        return {"kind": "environment", "reference": name}
    if policy == "auto":
        try:
            docker.validate_local_url(parameters["url"])
        except ValueError as error:
            raise ValueError("Remote bridge: choose Environment variable credentials and set its token variable. "
                             "Local deployment tokens are never sent to remote URLs automatically.") from error
    return {"kind": "none", "reference": ""}


def validate_deployment_endpoint(directory, url):
    """Restricts automatic local credentials to the deployment's configured loopback port.

    Args:
        directory (str): Prepared local deployment.
        url (str): Requested bridge endpoint.
    """
    docker.validate_local_url(url)
    root = docker.deployment_directory(directory)
    docker.read_deployment(directory)
    port = "7861"
    for line in (root / "configuration" / ".env").read_text(encoding="utf-8").splitlines():
        name, separator, value = line.strip().partition("=")
        if separator and name.strip() == "BRIDGE_PORT":
            port = value.strip().strip("\"'")
    parsed = urllib.parse.urlsplit(url)
    if not port.isdigit() or (parsed.port or (443 if parsed.scheme == "https" else 80)) != int(port):
        raise ValueError("Bridge URL does not match this deployment's BRIDGE_PORT in configuration/.env. "
                         "Choose its published URL or the correct Docker deployment; no token was sent.")


def make_connection(settings):
    """Creates an HTTP client configuration using token references at runtime.

    Args:
        settings (dict): Resolved connection and deployment settings.

    Returns:
        KimodoConnection: Validated transport configuration.
    """
    parameters = dict(settings["connection"])
    source = authentication_source(settings)
    token = None
    if source["kind"] == "environment":
        token = os.environ.get(source["reference"])
        if not token:
            raise ValueError(f"Token variable '{source['reference']}' is unset in Maya / the worker. "
                             "For local Docker choose Automatic credentials and its deployment folder, "
                             "or Use Saved Generator Connection. Remote credentials must exist before Maya starts.")
    elif source["kind"] == "deployment":
        validate_deployment_endpoint(source["reference"], parameters["url"])
        token = docker.bridge_token(source["reference"])
    if parameters.get("mode") == "docker":
        parameters["mode"] = "existing"
    return kimodo.KimodoConnection(token=token, **parameters)


def connection_error(error):
    """Explains rejected credentials without including their values.

    Args:
        error (Exception): Transport or credential error.

    Returns:
        str: Actionable error message.
    """
    if "HTTP 403" in str(error) or "HTTP 401" in str(error):
        return ("Bridge rejected the credentials. For local Docker choose Automatic credentials and "
                "its deployment folder (or Use Saved Generator Connection). For a remote bridge choose "
                "Environment variable and configure its token before starting Maya. "
                "No authentication works only with a bridge configured to allow it.")
    return str(error)


def check_health(client, settings):
    """Authenticates and verifies local deployment identity before any generation request.

    Args:
        client (KimodoClient): Configured client.
        settings (dict): Resolved connection settings.

    Returns:
        dict: Validated server health.
    """
    try:
        health = client.health()
    except RuntimeError as error:
        raise RuntimeError(connection_error(error)) from error
    source = authentication_source(settings)
    if source["kind"] == "deployment":
        docker._verify_identity(source["reference"], health)
    return health


def generator_settings():
    """Reads saved generator connection references for copying or model discovery.

    Returns:
        dict: Connection, Docker paths and an empty token environment reference.
    """
    from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel

    model = KimodoGeneratorModel()
    connection = dict(model.connection)
    connection.pop("auto_connect", None)
    return {"connection": connection,
            "docker": {key: model.docker[key] for key in ("directory", "executable")},
            "authentication": "auto", "token_environment": "", "startup_timeout": 180}


def wait_for_encoder(client, timeout, context=None):
    """Waits for a starting Docker encoder before allowing batch submission.

    Args:
        client (KimodoClient): Authenticated bridge client.
        timeout (float): Maximum encoder startup wait in seconds.
        context (dict, optional): Cancellation and tracker hooks.
    """
    from gt.tools.batch_processor.tasks.task_kimodo_base import report_message

    deadline = time.monotonic() + float(timeout)
    reported = False
    while True:
        predicate = (context or {}).get("cancel_requested")
        if callable(predicate) and predicate():
            raise RuntimeError("Kimodo startup canceled by batch request; containers were left running.")
        try:
            client.test_text_encoder()
            return
        except kimodo.KimodoEncoderUnavailable as error:
            if time.monotonic() >= deadline:
                raise TimeoutError("Docker text encoder is still loading. Check its logs in Kimodo Generator, "
                                   "wait for readiness, or increase Startup timeout before retrying.") from error
            if not reported:
                report_message(context, "Waiting for Docker text encoder to finish downloading or loading.")
                reported = True
            time.sleep(1)
