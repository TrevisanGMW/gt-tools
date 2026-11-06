"""Import-safe helpers for transferring, testing, and tracing environment variables."""

import copy
import json
import os

import gt.core.environment_references as core_env_refs
from gt.tools.batch_processor import batch_processor_model

REFERENCE_CODE_NAMES = ("env", "environment_variables")
_PROJECT_DIR_DERIVED_KEYS = ("project-parent-dir", "project-grandparent-dir")
_PROJECT_RELATIVE_KEYS = ("input-dir", "task-dir", "output-dir")


def evaluate_variable(name, variables, project=None):
    """Tests a variable with edited definitions and the current project context.

    Earlier rows are resolved in runtime order so successful results are
    available through ``env``. Failed earlier queries are omitted, and later
    queries are not run. Maya is imported only by the runtime query evaluator
    when a query actually runs.

    Args:
        name (str): Name of the variable to evaluate.
        variables (dict): Current editor definitions in table order.
        project (BatchProcessorModel, optional): Project supplying built-in values.

    Returns:
        object: Resolved value from the selected row.

    Raises:
        ValueError: If definitions are invalid, the name is missing, or the selected query fails.
    """
    variables = validate_variables(variables)
    name = batch_processor_model.normalize_environment_key(name)
    if name not in variables:
        raise ValueError(f'Unknown custom environment variable: "{name}".')
    preview_project = copy.copy(project) if project is not None else batch_processor_model.BatchProcessorModel()
    preview_project.custom_environment_variables = {}
    environment = preview_project.get_environment_variables(include_braces=False)
    preview_project.set_custom_environment_variables(variables)
    for variable_name, definition in variables.items():
        try:
            value = preview_project._resolve_custom_environment_variable(
                name=variable_name,
                definition=definition,
                task=None,
                environment_variables=environment,
                raise_errors=True,
                suppress_errors=variable_name != name,
            )
        except Exception as exception:
            if variable_name == name:
                raise ValueError(f"Query {{{variable_name}}} failed: {exception}") from exception
            environment.pop(variable_name, None)
            continue
        if variable_name == name:
            return value
        environment[variable_name] = value


def validate_variables(variables):
    """Validates variable definitions without evaluating query expressions.

    Args:
        variables (dict): Definitions keyed by braced or unbraced names.

    Returns:
        dict: Validated definitions with normalized names in source order.

    Raises:
        ValueError: If any name or definition is invalid or duplicated.
    """
    if not isinstance(variables, dict):
        raise ValueError("Custom variables must be a JSON object.")
    result = {}
    for name, definition in variables.items():
        if not isinstance(name, str):
            raise ValueError("Variable names must be strings.")
        name = name.strip()
        braced_name = name if name.startswith("{") else f"{{{name}}}"
        if not batch_processor_model.is_valid_custom_environment_name(braced_name):
            raise ValueError(f'Invalid variable name: "{name}".')
        if not batch_processor_model.BatchProcessorModel.is_custom_environment_name_available(braced_name):
            raise ValueError(f'"{name}" is reserved by Batch Processor.')
        normalized_name = batch_processor_model.normalize_environment_key(name)
        if normalized_name in result:
            raise ValueError(f'"{name}" is defined more than once.')
        if not isinstance(definition, dict):
            raise ValueError(f'"{name}" must contain a value and a Query flag.')
        value = definition.get("value")
        is_query = definition.get("query")
        if not isinstance(value, str) or not isinstance(is_query, bool):
            raise ValueError(f'"{name}" requires a string value and a boolean Query flag.')
        result[normalized_name] = {"value": value, "query": is_query}
    return result


def serialize_variables(variables):
    """Builds portable JSON text for a file or the system clipboard.

    Args:
        variables (dict): Custom variable definitions.

    Returns:
        str: Readable JSON preserving definition order and literal values.

    Raises:
        ValueError: If any variable is invalid.
    """
    payload = {"version": 1, "custom_environment_variables": validate_variables(variables)}
    return json.dumps(payload, indent=4, ensure_ascii=False)


def deserialize_variables(text):
    """Reads and validates a custom-variable transfer payload.

    Args:
        text (str): JSON file or clipboard contents.

    Returns:
        dict: Validated custom variable definitions.

    Raises:
        ValueError: If the JSON, version, or variable definitions are invalid.
    """
    payload = json.loads(text)
    if not isinstance(payload, dict) or "custom_environment_variables" not in payload:
        raise ValueError("Expected a Batch Processor custom variables JSON object.")
    if type(payload.get("version")) is not int or payload["version"] != 1:
        raise ValueError("Unsupported custom variables file version.")
    return validate_variables(payload["custom_environment_variables"])


def read_variables(file_path):
    """Reads variable definitions from a UTF-8 JSON file.

    Args:
        file_path (str): Source file path.

    Returns:
        dict: Validated variable definitions.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the file contents are invalid.
    """
    with open(file_path, "r", encoding="utf-8-sig") as variables_file:
        return deserialize_variables(variables_file.read())


def write_variables(file_path, variables):
    """Validates and atomically writes variables to a user-selected destination.

    Args:
        file_path (str): Destination approved by the export file dialog.
        variables (dict): Custom variable definitions.

    Raises:
        OSError: If the file cannot be written.
        ValueError: If a variable is invalid.
    """
    payload = json.loads(serialize_variables(variables))
    batch_processor_model.BatchProcessorModel._atomic_write_json(
        os.path.abspath(file_path), payload, sort_keys=False
    )


def normalize_reference_key(key):
    """Normalizes a referenced token key, mapping legacy aliases to current names.

    Args:
        key (str): Raw token key with or without braces.

    Returns:
        str: Lowercase hyphen-separated key used by the environment-variable table.
    """
    normalized_key = batch_processor_model.normalize_environment_key(key)
    return batch_processor_model._LEGACY_INDEX_ENVIRONMENT_ALIASES.get(
        normalized_key, normalized_key
    )


def _is_project_relative_path(value):
    """Checks whether a configured folder is resolved relative to the project folder.

    Args:
        value (str): Configured folder value.

    Returns:
        bool: True for non-empty relative paths that do not start with a token.
    """
    value = str(value or "").strip()
    return bool(value) and not value.startswith("{") and not os.path.isabs(value)


def build_project_folder_sources(environment_variables):
    """Builds sources for configured project folders and their built-in dependencies.

    Args:
        environment_variables (dict): Serialized project folder settings.

    Returns:
        list: Reference sources defining folder variables.
    """
    sources = []
    for key, value in (environment_variables or {}).items():
        key = batch_processor_model.normalize_environment_key(key)
        if not value:
            continue
        sources.append(
            {
                "kind": "variable",
                "id": key,
                "label": f"{{{key}}} (project folder)",
                "data": {"value": value},
                "defines": key,
            }
        )
        if key in _PROJECT_RELATIVE_KEYS and _is_project_relative_path(value):
            sources.append(
                {
                    "kind": "variable",
                    "id": key,
                    "label": f"{{{key}}} (relative to project folder)",
                    "data": {"value": "{project-dir}"},
                    "defines": key,
                }
            )
    for key in _PROJECT_DIR_DERIVED_KEYS:
        sources.append(
            {
                "kind": "variable",
                "id": key,
                "label": f"{{{key}}} (built-in)",
                "data": {"value": "{project-dir}"},
                "defines": key,
            }
        )
    return sources


def build_reference_sources(project_data):
    """Builds reference sources from serialized Batch Processor project data.

    Args:
        project_data (dict): Data returned by ``BatchProcessorModel.to_dict``.

    Returns:
        list: Reference sources for ``gt.core.environment_references.find_references``.
    """
    project_data = project_data or {}
    sources = build_project_folder_sources(project_data.get("environment_variables"))

    custom_variables = project_data.get("custom_environment_variables") or {}
    for name, definition in custom_variables.items():
        name = batch_processor_model.normalize_environment_key(name)
        definition = definition if isinstance(definition, dict) else {"value": definition}
        query_suffix = " (query)" if definition.get("query") else ""
        sources.append(
            {
                "kind": "variable",
                "id": name,
                "label": f"{{{name}}}{query_suffix}",
                "data": {"value": definition.get("value", "")},
                "defines": name,
            }
        )

    run_settings = dict(project_data.get("run_settings") or {})
    log_path = run_settings.pop("log_path", "")
    if log_path:
        sources.append(
            {
                "kind": "variable",
                "id": "log-dir",
                "label": "{log-dir} (run settings)",
                "data": {"log_path": log_path},
                "defines": "log-dir",
            }
        )
    sources.append(
        {
            "kind": "project",
            "id": "run_settings",
            "label": "Run settings",
            "data": run_settings,
        }
    )
    sources.append(
        {
            "kind": "project",
            "id": "notes",
            "label": "Project notes",
            "data": project_data.get("notes", ""),
        }
    )

    for task_position, task_data in enumerate(project_data.get("tasks") or [], start=1):
        task_name = task_data.get("display_name") or task_data.get("task_type") or "Task"
        scanned_data = {
            key: value
            for key, value in task_data.items()
            if key not in ("id", "task_type", "enabled")
        }
        sources.append(
            {
                "kind": "task",
                "id": task_data.get("id", ""),
                "label": f"#{task_position:02d} {task_name}",
                "enabled": task_data.get("enabled", True),
                "data": scanned_data,
            }
        )
    return sources


def find_project_references(project_data):
    """Finds where each environment variable is used in a Batch Processor project.

    Args:
        project_data (dict): Data returned by ``BatchProcessorModel.to_dict``.

    Returns:
        dict: Unbraced token keys mapped to reference dictionaries.
    """
    return core_env_refs.find_references(
        build_reference_sources(project_data),
        normalize_key=normalize_reference_key,
        code_names=REFERENCE_CODE_NAMES,
    )
