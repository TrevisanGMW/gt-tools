# Skips files that do not apply to this validation instead of passing or failing them.
# Skipped files show as skipped in the tracker and are not recorded as passed or failed.

SKIP_KEYWORD = "_wip"

file_name = context.get("file_name", "")
if SKIP_KEYWORD in file_name.lower():
    validation.skip(f"Work-in-progress file, not validated: {file_name}")
else:
    validation.info(f"Validated: {file_name}")
