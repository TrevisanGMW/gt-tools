"""Routes matching scenes using project environment variables, then stops."""

FILTER_KEYWORD = "_filter"
# Use any project/custom environment variables. No machine-specific path is needed.
FILTER_FOLDER = "{project-dir}/{output-dir}/filtered"

if FILTER_KEYWORD in context["file_name"].lower():
    context["control"].save_to_folder(FILTER_FOLDER, reason="Filename matched the filter")
