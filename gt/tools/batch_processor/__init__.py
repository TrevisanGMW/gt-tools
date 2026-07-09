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


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context.
    """
    from gt.tools.batch_processor import batch_processor_controller
    from gt.tools.batch_processor import batch_processor_model
    from gt.tools.batch_processor import batch_processor_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _view = batch_processor_view.BatchProcessorView(parent=context.get_parent(), version=__version__)
        _model = batch_processor_model.BatchProcessorModel()
        _controller = batch_processor_controller.BatchProcessorController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
