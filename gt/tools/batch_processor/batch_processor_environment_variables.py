"""Import-safe helpers for transferring and testing custom environment variables."""

import copy
import json
import os

from gt.tools.batch_processor import batch_processor_model


def evaluate_variable(name, variables, project=None):
    """Tests a variable with edited definitions and the current project context.

    Earlier rows are resolved in runtime order so their results are available
    through ``env``. Later queries are not run. Maya is imported only by the
    model's query evaluator when a query actually runs.

    Args:
        name (str): Name of the variable to evaluate.
        variables (dict): Current editor definitions in table order.
        project (BatchProcessorModel, optional): Project supplying built-in values.

    Returns:
        object: Resolved value from the selected row.

    Raises:
        ValueError: If definitions are invalid, the name is missing, or a query fails.
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
            )
        except Exception as exception:
            raise ValueError(f"Query {{{variable_name}}} failed: {exception}") from exception
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
