"""Publishes verified native Kimodo arrays without importing Maya or NumPy."""

import os


def publish_numpy(source, destination, overwrite=False):
    """Moves one downloaded NPZ into its named output location after validation.

    Args:
        source (str): Verified downloaded array in the task cache.
        destination (str): Reserved output path on the same filesystem.
        overwrite (bool): Whether an existing output may be replaced.
    """
    if os.path.splitext(source)[1].lower() != ".npz":
        raise ValueError(f"Expected a NumPy archive: {source}")
    if not os.path.isfile(source) or not os.path.getsize(source):
        raise ValueError(f"Downloaded NumPy archive is missing or empty: {source}")
    if os.path.exists(destination) and not overwrite:
        if not os.path.isfile(destination) or not os.path.getsize(destination):
            raise ValueError(f"Existing NumPy output is empty or invalid: {destination}")
        return
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    os.replace(source, destination)
