"""Import-safe, cumulative run results exposed to batch scripts.

State belongs to one run, is never saved in a .batch file, and is transferred
between worker processes by the tracker. Failed and incomplete work remain
recorded even when later work or a retry succeeds.
"""

import json


WORKER_STATE_VARIABLE = "GT_BATCH_RUN_STATE"
ENVIRONMENT_KEYS = (
    "batch-status-known", "batch-run-scope", "batch-run-id",
    "batch-tasks-failed", "batch-tasks-incomplete", "batch-validation-failed",
    "batch-validation-passed", "batch-previous-tasks-succeeded", "batch-is-final-task",
    "batch-task-run-once",
)


def new_state(run_id="", scope="worker"):
    """Creates fresh results for one run.

    Args:
        run_id (str, optional): Identity of the active run.
        scope (str, optional): project for a barrier, worker for individual jobs.

    Returns:
        dict: Serializable runtime results.
    """
    return {
        "known": True, "run_id": run_id, "scope": scope,
        "tasks_failed": False, "tasks_incomplete": False,
        "validation_failed": False, "validation_checked": False,
        "completed_task_ids": [],
    }


def merge_states(states, run_id="", scope="worker"):
    """Combines results while retaining every failure and unknown outcome.

    Args:
        states (list): Runtime result dictionaries; None means unknown.
        run_id (str, optional): Identity of the containing run.
        scope (str, optional): Scope of the combined results.

    Returns:
        dict: Combined results with cumulative failure flags.
    """
    merged = new_state(run_id, scope)
    for state in states:
        if not isinstance(state, dict) or state.get("known") is not True:
            merged["known"] = False
            continue
        for key in ("tasks_failed", "tasks_incomplete", "validation_failed", "validation_checked"):
            merged[key] = merged[key] or state.get(key) is True
        merged["completed_task_ids"] = sorted(set(merged["completed_task_ids"]) |
                                               set(state.get("completed_task_ids") or []))
    return merged


def decode_state(value):
    """Reads worker results, rejecting invalid or incomplete payloads.

    Args:
        value (str): JSON received from the tracker.

    Returns:
        dict or None: Validated results, or None for an unknown outcome.
    """
    try:
        state = json.loads(value)
        boolean_keys = ("known", "tasks_failed", "tasks_incomplete",
                        "validation_failed", "validation_checked")
        if not isinstance(state, dict) or any(type(state.get(key)) is not bool for key in boolean_keys):
            return None
        completed = state.get("completed_task_ids")
        if not isinstance(completed, list) or any(not isinstance(value, str) for value in completed):
            return None
        if state.get("scope") not in ("project", "worker") or not isinstance(state.get("run_id"), str):
            return None
        return state
    except (ValueError, TypeError):
        return None


def initialize(project, run_id, scope="project", seed=None):
    """Initializes runtime state without changing project serialization.

    Args:
        project (BatchProcessorModel): Owning project.
        run_id (str): Identity of the active run.
        scope (str, optional): Extent of the verified results.
        seed (dict, optional): Cumulative results from preceding worker jobs.

    Returns:
        dict: Mutable state attached to the project.
    """
    state = merge_states([seed], run_id, scope) if seed is not None else new_state(run_id, scope)
    project._batch_run_state = state
    return state


def record_task(project, task, status):
    """Records completion and preserves failures or skips for the whole run.

    Args:
        project (BatchProcessorModel): Owning project.
        task (BatchTask or None): Task that just finished.
        status (str): succeeded, failed, skipped, or incomplete.
    """
    state = getattr(project, "_batch_run_state", None)
    if state is None:
        return
    if status == "succeeded" and task:
        if task.id not in state["completed_task_ids"]:
            state["completed_task_ids"].append(task.id)
        return
    state["tasks_incomplete"] = True
    if status == "failed":
        state["tasks_failed"] = True
        if task and getattr(task, "category", "") == "Validation":
            state["validation_failed"] = True


def record_validation(project, passed):
    """Records validation independently of the task's failure policy.

    Args:
        project (BatchProcessorModel): Owning project.
        passed (bool): Whether the actual checks completed without issues.
    """
    state = getattr(project, "_batch_run_state", None)
    if state is not None:
        state["validation_checked"] = True
        state["validation_failed"] = state["validation_failed"] or not passed


def get_environment_variables(project, task=None):
    """Builds fail-closed result variables for the current task.

    Args:
        project (BatchProcessorModel): Active project.
        task (BatchTask, optional): Task requesting the results.

    Returns:
        dict: String values; boolean flags use 1 and 0. The previous-tasks flag
            excludes the running task and includes all enabled processing tasks
            before it, including tasks outside a shortened run.
    """
    state = getattr(project, "_batch_run_state", None) or {"known": False}
    enabled = project.get_enabled_tasks()
    previous = []
    for candidate in enabled:
        if candidate is task:
            break
        if not candidate.is_input_task:
            previous.append(candidate.id)
    known = state.get("known") is True
    previous_succeeded = (
        known and task in enabled and not state.get("tasks_failed")
        and not state.get("tasks_incomplete")
        and set(previous).issubset(state.get("completed_task_ids") or [])
    )
    values = {
        "batch-status-known": known,
        "batch-tasks-failed": state.get("tasks_failed", False),
        "batch-tasks-incomplete": state.get("tasks_incomplete", False),
        "batch-validation-failed": state.get("validation_failed", False),
        "batch-validation-passed": known and state.get("validation_checked", False)
        and not state.get("validation_failed", False),
        "batch-previous-tasks-succeeded": previous_succeeded,
        "batch-is-final-task": bool(task and enabled and task is enabled[-1]),
        "batch-task-run-once": bool(task and getattr(task, "is_aggregate_task", False)),
    }
    result = {key: "1" if value else "0" for key, value in values.items()}
    result.update({"batch-run-scope": state.get("scope", "unknown"),
                   "batch-run-id": state.get("run_id", "")})
    return result
