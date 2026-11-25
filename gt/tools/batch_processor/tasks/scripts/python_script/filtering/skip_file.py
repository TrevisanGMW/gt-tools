"""Stops matching files without this task's automatic save."""

# Replace this example filename test with any scene or file validation.
FILTER_KEYWORD = "_filter"

if FILTER_KEYWORD in context["file_name"].lower():
    context["control"].skip_file("Filename matched the filter")
