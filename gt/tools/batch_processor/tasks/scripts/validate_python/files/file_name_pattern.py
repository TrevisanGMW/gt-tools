# Validates file names without opening them.
# Turn "Load Scene" off for this example so files are not loaded into Maya.
# Edit NAME_PATTERN (a regular expression) and ALLOWED_EXTENSIONS for your project.
import os
import re

NAME_PATTERN = r"^[a-z0-9]+(_[a-z0-9]+)*$"
ALLOWED_EXTENSIONS = [".ma", ".mb", ".fbx"]

file_path = context.get("current_path", "")
base_name, extension = os.path.splitext(os.path.basename(file_path))

validation.check(
    extension.lower() in ALLOWED_EXTENSIONS,
    f"Unexpected extension '{extension}', allowed: {', '.join(ALLOWED_EXTENSIONS)}",
)
validation.check(
    re.match(NAME_PATTERN, base_name),
    f"File name does not match the naming convention: {base_name}",
    pattern=NAME_PATTERN,
)
