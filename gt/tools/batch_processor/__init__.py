"""
 Batch Processor
"""

import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool(project_path=None):
    """Launches the Batch Processor and optionally loads a project.

    Args:
        project_path (str, optional): Batch project to load after constructing the tool.
    """
    from gt.tools.batch_processor import batch_processor_controller
    from gt.tools.batch_processor import batch_processor_model
    from gt.tools.batch_processor import batch_processor_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _view = batch_processor_view.BatchProcessorView(parent=context.get_parent(), version=__version__)
        _model = batch_processor_model.BatchProcessorModel()
        _controller = batch_processor_controller.BatchProcessorController(model=_model, view=_view)
        if project_path:
            _controller.load_project_from_path(project_path)


def launch_project(
    project_path,
    start_minimized=True,
    run_from_task_id=None,
    run_to_task_id=None,
    close_when_finished=False,
    result_dir=None,
):
    """Launches a saved project in its standalone tracker without opening the editor (for scripts and agents).

    The tracker opens minimized to the system tray by default, regardless of user preferences.
    Works with plain Python (no Maya session needed). Use ``.wait()`` on the returned handle to block
    until the run finishes. See ``batch_processor_launch.launch_project``.

    Args:
        project_path (str): Path to the saved ``.batch`` project file.
        start_minimized (bool, optional): Launch the tracker as a tray icon instead of a window.
        run_from_task_id (str, optional): Task id to start from.
        run_to_task_id (str, optional): Task id to stop after.
        close_when_finished (bool, optional): Close the tracker as soon as the run ends.
        result_dir (str, optional): Where result files are published. Defaults to a temp folder.

    Returns:
        ProjectRun: Handle with wait(), get_result(), get_progress(), cancel() and close().
    """
    from gt.tools.batch_processor import batch_processor_launch

    return batch_processor_launch.launch_project(
        project_path,
        start_minimized=start_minimized,
        run_from_task_id=run_from_task_id,
        run_to_task_id=run_to_task_id,
        close_when_finished=close_when_finished,
        result_dir=result_dir,
    )


if __name__ == "__main__":
    launch_tool()
