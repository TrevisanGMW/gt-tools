"""
 Batch Processor
"""

import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (0, 1, 0)
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


if __name__ == "__main__":
    launch_tool()
