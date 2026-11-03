# Checks that every file has a companion file next to it (for example a .json
# metadata file with the same name). Works with "Load Scene" off.
import os

SIDECAR_EXTENSION = ".json"

file_path = context.get("current_path", "")
sidecar_path = os.path.splitext(file_path)[0] + SIDECAR_EXTENSION

if validation.check(os.path.isfile(sidecar_path), f"Missing sidecar file: {sidecar_path}"):
    validation.check(
        os.path.getsize(sidecar_path) > 0,
        f"Sidecar file is empty: {sidecar_path}",
        severity="Warning",
    )
