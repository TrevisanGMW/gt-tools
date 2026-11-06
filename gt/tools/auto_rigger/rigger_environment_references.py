"""Import-safe helpers that find where Auto Rigger environment variables are used."""

import gt.core.environment_references as core_env_refs

DEFAULT_PROJECT_DIR = "{project-file-dir}"
_MODULE_IDENTITY_KEYS = ("uuid", "parent", "mirror", "module", "active")


def build_reference_sources(project_data, module_labels=None):
    """Builds reference sources from serialized Auto Rigger project data.

    Args:
        project_data (dict): Data returned by ``RigProject.get_project_as_dict``.
        module_labels (dict, optional): Module UUIDs mapped to display labels.

    Returns:
        list: Reference sources for ``gt.core.environment_references.find_references``.
    """
    project_data = dict(project_data or {})
    module_labels = module_labels or {}
    preferences = dict(project_data.get("preferences") or {})
    configured_project_dir = preferences.pop("project_dir", "")
    project_dir_label = "{project-dir} (project directory setting)"
    if not configured_project_dir:
        project_dir_label = "{project-dir} (default project directory)"
    sources = [
        {
            "kind": "variable",
            "id": "project-dir",
            "label": project_dir_label,
            "data": {"project_dir": configured_project_dir or DEFAULT_PROJECT_DIR},
            "defines": "project-dir",
        }
    ]

    project_settings = {
        key: value
        for key, value in project_data.items()
        if key not in ("modules", "preferences", "uuid")
    }
    project_settings["preferences"] = preferences
    sources.append(
        {
            "kind": "project",
            "id": project_data.get("uuid", ""),
            "label": "Project settings",
            "data": project_settings,
        }
    )

    for module_position, module_data in enumerate(project_data.get("modules") or [], start=1):
        module_uuid = module_data.get("uuid", "")
        module_label = (
            module_labels.get(module_uuid)
            or module_data.get("name")
            or module_data.get("module")
            or f"Module {module_position}"
        )
        sources.append(
            {
                "kind": "module",
                "id": module_uuid,
                "label": module_label,
                "enabled": module_data.get("active", True),
                "data": {
                    key: value
                    for key, value in module_data.items()
                    if key not in _MODULE_IDENTITY_KEYS
                },
            }
        )
    return sources


def find_project_references(project_data, module_labels=None):
    """Finds where each environment variable is used in an Auto Rigger project.

    Auto Rigger replaces tokens with exact, case-sensitive matches, so keys are
    only stripped of their braces.

    Args:
        project_data (dict): Data returned by ``RigProject.get_project_as_dict``.
        module_labels (dict, optional): Module UUIDs mapped to display labels.

    Returns:
        dict: Unbraced token keys mapped to reference dictionaries.
    """
    return core_env_refs.find_references(
        build_reference_sources(project_data, module_labels=module_labels)
    )
