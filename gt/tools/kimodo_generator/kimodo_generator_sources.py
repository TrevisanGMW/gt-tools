"""Pinned fallback commits and guarded updates of generated upstream checkouts."""

import re
import subprocess

KIMODO_REVISION = "e1c219c99b4b94ba48be1fb6a1cbc64ecee4c954"
VISER_REVISION = "7c82ad8f8640bad9dff8ded5c5eee908eeb08f11"
KIMODO_REPOSITORY = "https://github.com/nv-tlabs/kimodo.git"
VISER_REPOSITORY = "https://github.com/nv-tlabs/kimodo-viser.git"


class SourceCheckoutError(ValueError):
    """Refuses changes to a checkout whose ownership or clean state cannot be verified."""


def run_git(arguments, timeout=180):
    """Runs Git without a shell or visible console window.

    Args:
        arguments (list): Git arguments, excluding the executable.
        timeout (float): Command timeout in seconds.

    Returns:
        str: UTF-8 command output.
    """
    result = subprocess.run(["git"] + list(arguments), capture_output=True, timeout=timeout, check=True,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return result.stdout.decode("utf-8", errors="replace").strip()


def stable_revisions():
    """Returns the known fallback source commits.

    Returns:
        dict: Kimodo and Viser commit hashes.
    """
    return {"kimodo_revision": KIMODO_REVISION, "viser_revision": VISER_REVISION}


def latest_revisions():
    """Resolves both upstream default branches to concrete commits before building.

    Returns:
        dict: Resolved Kimodo and Viser commit hashes.
    """
    revisions = {}
    for key, repository in (("kimodo_revision", KIMODO_REPOSITORY), ("viser_revision", VISER_REPOSITORY)):
        output = run_git(["ls-remote", repository, "HEAD"], timeout=20)
        commit = output.split()[0] if output else ""
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError(f"Could not resolve the latest source commit for {repository}.")
        revisions[key] = commit
    return revisions


def checkout_source(path, repository, revision, previous_revision=None):
    """Updates only a clean, known generated checkout without resetting user edits.

    Args:
        path (Path): Owned source checkout directory.
        repository (str): Expected upstream Git URL.
        revision (str): Required commit hash.
        previous_revision (str, optional): Commit recorded for the existing checkout.
    """
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SourceCheckoutError("Source revisions must be full Git commit hashes.")
    if not path.exists():
        run_git(["clone", repository, str(path)])
        run_git(["-C", str(path), "checkout", "--detach", revision])
        return
    origin = run_git(["-C", str(path), "remote", "get-url", "origin"])
    current = run_git(["-C", str(path), "rev-parse", "HEAD"])
    changes = run_git(["-C", str(path), "diff", "--name-only", "HEAD"])
    if origin != repository or current not in (revision, previous_revision) or changes:
        raise SourceCheckoutError(f"Source checkout {path} has edits, a different origin, or an unrecorded commit. "
                                  "It was left unchanged; review it before building.")
    if current != revision:
        run_git(["-C", str(path), "fetch", "origin", revision])
        # No force/reset/clean: Git also refuses untracked files that would be overwritten.
        run_git(["-C", str(path), "checkout", "--detach", revision])
