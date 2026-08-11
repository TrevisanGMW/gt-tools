"""
Batch Processor Task Utilities
"""

from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import datetime
import json
import os
import sys


SCRIPTS_DIRECTORY = os.path.join(os.path.dirname(__file__), "scripts")


def load_script(script_name):
    """Loads an editable script from the batch processor scripts folder.

    Args:
        script_name (str): Script file name relative to the scripts folder.

    Returns:
        str: Script source text.

    Raises:
        IOError: If the script file cannot be read.
    """
    script_path = os.path.join(SCRIPTS_DIRECTORY, script_name)
    return load_script_file(script_path)


def load_script_file(script_path):
    """Loads a Python script from a file path.

    Args:
        script_path (str): Absolute or relative path to a Python script.

    Returns:
        str: Script source text.

    Raises:
        IOError: If the script file cannot be read.
    """
    with open(script_path, "r", encoding="utf-8") as script_file:
        return script_file.read()


def get_script_samples_directory(directory_name):
    """Gets a sample script directory inside the batch processor scripts folder.

    Args:
        directory_name (str): Relative task sample directory name.

    Returns:
        str: Absolute sample directory path, or an empty string when invalid.
    """
    directory_name = str(directory_name or "").strip()
    if not directory_name:
        return ""
    scripts_directory = os.path.normcase(os.path.abspath(SCRIPTS_DIRECTORY))
    sample_directory = os.path.normcase(
        os.path.abspath(os.path.join(scripts_directory, directory_name))
    )
    try:
        if os.path.commonpath([scripts_directory, sample_directory]) != scripts_directory:
            return ""
    except ValueError:
        return ""
    return sample_directory


def get_script_samples(directory_name):
    """Gets Python sample scripts from a task-specific sample directory.

    Directories and script files are sorted so the examples menu remains stable.
    Nested folders are supported for task phases that need separate examples.

    Args:
        directory_name (str): Relative task sample directory name.

    Returns:
        list: Dictionaries with normalized ``path`` and ``relative_path`` values.
    """
    sample_directory = get_script_samples_directory(directory_name)
    if not sample_directory or not os.path.isdir(sample_directory):
        return []
    script_samples = []
    for current_directory, directory_names, file_names in os.walk(sample_directory):
        directory_names.sort(key=str.lower)
        for file_name in sorted(file_names, key=str.lower):
            if not file_name.lower().endswith(".py"):
                continue
            script_path = os.path.join(current_directory, file_name)
            relative_path = os.path.relpath(script_path, sample_directory)
            script_samples.append(
                {
                    "path": os.path.normpath(script_path),
                    "relative_path": os.path.normpath(relative_path),
                }
            )
    return script_samples


def ensure_directory(directory_path):
    """Ensures a directory exists.

    Args:
        directory_path (str): Directory path.

    Returns:
        str: Normalized directory path.
    """
    directory_path = task_base.normalize_path(directory_path)
    if directory_path and not os.path.isdir(directory_path):
        os.makedirs(directory_path)
    return directory_path


def build_output_path(work_item, output_dir, extension=None, suffix=""):
    """Builds an output file path using a work item basename.

    Args:
        work_item (WorkItem): Work item used as the source name.
        output_dir (str): Output directory.
        extension (str, optional): Output extension. Uses source extension when omitted.
        suffix (str, optional): Optional suffix appended before the extension.

    Returns:
        str: Normalized output file path.
    """
    source_path = work_item.current_path if work_item else ""
    base_name, source_extension = os.path.splitext(os.path.basename(source_path))
    extension = extension or source_extension
    if extension and not extension.startswith("."):
        extension = "." + extension
    file_name = "{0}{1}{2}".format(task_base.sanitize_filename(base_name, "item"), suffix or "", extension or "")
    return task_base.build_work_item_output_path(work_item=work_item, output_dir=output_dir, file_name=file_name)


def build_metadata(task, work_item):
    """Builds common task metadata.

    Args:
        task (BatchTask): Task that produced the metadata.
        work_item (WorkItem): Source work item.

    Returns:
        dict: Updated metadata dictionary.
    """
    metadata = dict(work_item.metadata if work_item else {})
    metadata["last_task_id"] = task.id
    metadata["last_task_type"] = task.task_type
    metadata["settings_hash"] = task_base.hash_settings(task.settings)
    return metadata


def write_json_log(output_path, data):
    """Writes a JSON log file.

    Args:
        output_path (str): Destination JSON path.
        data (dict): Serializable log data.

    Returns:
        str: Written log path.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directory(output_dir)
    with open(output_path, "w", encoding="utf-8") as log_file:
        json.dump(data, log_file, indent=4, sort_keys=True)
    return output_path


def report_log_artifact(context, log_path):
    """Reports a generated log path to an optional runtime tracker callback.

    Args:
        context (dict): Task execution context.
        log_path (str): Generated log path.

    Returns:
        str: Unmodified log path.
    """
    callback = (context or {}).get("report_log")
    if log_path and callable(callback):
        callback(log_path)
    return log_path


def get_timestamp():
    """Gets an ISO timestamp string.

    Returns:
        str: Timestamp.
    """
    return datetime.datetime.utcnow().isoformat()


def load_source_scene(source_path, source_load_mode="Open", load_relevant_plugins=True):
    """Loads a source file into Maya.

    Args:
        source_path (str): Source file path.
        source_load_mode (str, optional): Either Open or Import.
        load_relevant_plugins (bool, optional): Whether known file plugins should load.
    """
    extension = os.path.splitext(source_path)[1].lower()
    source_load_mode = str(source_load_mode or "Open").lower()
    if source_load_mode == "open" and extension in [".ma", ".mb", ".fbx"]:
        batch_processor_maya.open_scene(source_path, load_relevant_plugins=load_relevant_plugins)
        return
    batch_processor_maya.new_scene()
    if os.path.isfile(source_path):
        batch_processor_maya.import_file(source_path, load_relevant_plugins=load_relevant_plugins)


def build_python_script_runtime_context(
    project,
    task,
    work_item,
    output_path,
    context=None,
    extra_values=None,
    pass_standard_arguments=True,
    pass_environment_arguments=True,
):
    """Builds a standard Python script runtime context for task-owned scripts.

    Args:
        project (BatchProcessorModel): Active project model.
        task (BatchTask): Task running the script.
        work_item (WorkItem): Work item being processed.
        output_path (str): Expected output path.
        context (dict, optional): Existing runner context.
        extra_values (dict, optional): Additional globals to expose.
        pass_standard_arguments (bool, optional): Whether to expose task arguments.
        pass_environment_arguments (bool, optional): Whether to expose project environment variables.

    Returns:
        dict: Runtime context with standard script dictionaries and aliases.
    """
    runtime_context = dict(context or {})
    current_path = getattr(work_item, "current_path", "") or ""
    source_path = getattr(work_item, "source_path", current_path) or current_path
    source_relative_path = task_base.get_work_item_relative_path(work_item)
    source_relative_dir = task_base.get_work_item_relative_dir(work_item)
    project_path = getattr(project, "project_file_path", "") or ""
    project_dir = project.get_project_dir() if project else ""
    task_name = getattr(task, "display_name", "") or ""
    task_id = getattr(task, "id", "") or ""
    task_type = getattr(task, "task_type", "") or ""
    arguments = {}
    if pass_standard_arguments:
        arguments = {
            "input": current_path,
            "output": output_path,
            "project": project_path,
            "project_path": project_path,
            "project_dir": project_dir,
            "task": task_name,
            "task_id": task_id,
            "current_path": current_path,
            "source_path": source_path,
            "output_path": output_path,
            "task_name": task_name,
            "task_type": task_type,
            "file_name": os.path.basename(current_path),
        }
    environment_variables = {}
    if project and task and pass_environment_arguments:
        task_index = None
        if hasattr(project, "get_task_environment_index"):
            task_index = project.get_task_environment_index(task)
        environment_variables = project.get_environment_variables(
            task=task,
            task_index=task_index,
            include_braces=False,
        )
    runtime_context.update(
        {
            "current_path": current_path,
            "source_path": current_path,
            "original_source_path": source_path,
            "output_path": output_path,
            "rel_path": source_relative_dir or ".",
            "json_lookup_key": source_relative_path or os.path.basename(current_path),
            "source_relative_path": source_relative_path,
            "source_relative_dir": source_relative_dir,
            "project_path": project_path,
            "project_dir": project_dir,
            "task_id": task_id,
            "task_name": task_name,
            "task_type": task_type,
            "file_name": os.path.basename(current_path),
            "arguments": arguments,
            "args": arguments,
            "environment_variables": environment_variables,
            "env": environment_variables,
        }
    )
    runtime_context.update(extra_values or {})
    return runtime_context


def run_inline_python_script(script_text, context, script_name="<batch_post_script>"):
    """Runs inline Python code with a runtime context.

    Args:
        script_text (str): Python code to execute.
        context (dict): Runtime values exposed to the script.
        script_name (str, optional): Compile name used in tracebacks.
    """
    if context is None:
        context = {}
    arguments = context.get("arguments") or context.get("args") or {}
    environment_variables = context.get("environment_variables") or context.get("env") or {}
    namespace = dict(context)
    namespace.setdefault("context", context)
    namespace.setdefault("batch_context", context)
    namespace.setdefault("arguments", arguments)
    namespace.setdefault("args", arguments)
    namespace.setdefault("environment_variables", environment_variables)
    namespace.setdefault("env", environment_variables)
    namespace.setdefault("sys", sys)
    exec(compile(str(script_text or ""), str(script_name or "<batch_post_script>"), "exec"), namespace, namespace)
