"""Scoped runtime text values shared by batch runners and scene-loading helpers."""

import os
from contextlib import contextmanager
from contextvars import ContextVar


_VIRTUAL_SCENE = ContextVar("batch_virtual_scene", default="")


def is_string_scene(work_item):
    """Checks whether the current item still represents its initial empty scene.

    Args:
        work_item (WorkItem): Item to inspect.

    Returns:
        bool: Whether no real output has replaced the virtual scene identity.
    """
    return bool(work_item and work_item.metadata.get("input_string_path") == work_item.current_path)


def is_active_virtual_path(path):
    """Checks whether a scene loader was given the active virtual identity.

    Args:
        path (str): Requested scene path.

    Returns:
        bool: Whether the empty scene has already been prepared by the runner.
    """
    return bool(path and _VIRTUAL_SCENE.get() == os.path.normpath(os.path.abspath(path)))


@contextmanager
def work_item_context(project, work_item):
    """Exposes one row during execution and restores state even after failure.

    Args:
        project (BatchProcessorModel): Owning project.
        work_item (WorkItem): Current item, including inherited text metadata.

    Yields:
        None: The task may execute inside this scope.
    """
    metadata = work_item.metadata if work_item else {}
    previous_runtime = getattr(project, "_input_string_environment", {})
    virtual_scene = is_string_scene(work_item)
    token = _VIRTUAL_SCENE.set(work_item.current_path if virtual_scene else "")
    try:
        value = metadata.get("input_string", "")
        project._input_string_environment = {
            "input-file": metadata.get("input_file", os.path.splitext(os.path.basename(work_item.source_path))[0]
                                       if work_item else ""),
            "input-string": value, "input-string-index": metadata.get("input_string_index", ""),
        }
        if virtual_scene:
            from gt.tools.batch_processor import batch_processor_maya

            batch_processor_maya.new_scene()
        yield
    finally:
        _VIRTUAL_SCENE.reset(token)
        project._input_string_environment = previous_runtime


def execute_work_item(task, work_item, project, step_output_dir, context=None):
    """Executes a task with per-row variables and an isolated initial scene.

    Args:
        task (BatchTask): Task to execute.
        work_item (WorkItem): Current item.
        project (BatchProcessorModel): Owning project.
        step_output_dir (str): Default task output directory.
        context (dict, optional): Tracker callbacks and indices.

    Returns:
        WorkItem or list: Task output items.
    """
    if is_string_scene(work_item) and task.modifies_in_place():
        raise ValueError("String inputs have no source file to modify. Choose a separate output path.")
    with work_item_context(project, work_item):
        if "input_string" in work_item.metadata and task.writes_to_target_path():
            step_output_dir = task.resolve_task_path(project, task_index=project.get_task_environment_index(task))
            os.makedirs(step_output_dir, exist_ok=True)
        return task.execute(work_item, project, step_output_dir, context=context)
