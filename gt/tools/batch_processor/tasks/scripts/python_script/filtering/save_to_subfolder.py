"""Saves matching scenes into a configurable subfolder, then stops processing."""

FILTER_KEYWORD = "_filter"
FILTER_SUBFOLDER = "filtered"  # Rename this folder to suit the project.

if FILTER_KEYWORD in context["file_name"].lower():
    context["control"].save_to_subfolder(FILTER_SUBFOLDER, reason="Filename matched the filter")
