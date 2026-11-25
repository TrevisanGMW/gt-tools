"""
Multi-File Importer - Imports or references many files into the current scene and lays them out for review.

Where things live:
    __init__.py                         Entry point (launch_tool).
    multi_file_importer_view.py         Widgets only.
    multi_file_importer_controller.py   Wiring, file list actions, import loop, settings files.
    multi_file_importer_model.py        File list, settings, persistence, export/import.
    multi_file_importer_constants.py    Option values and default settings.
    multi_file_importer_formats.py      One small class per file format; calls the format utilities
                                        (gt.core.scene, gt.utils.fbx, gt.utils.usd, gt.utils.bvh, ...).
    multi_file_importer_service.py      One import session in Maya (load, group, place, scripts).
    multi_file_importer_scene.py        Frame rate, unit, up axis, timeline and review overrides.
    multi_file_importer_layout.py       Line and grid placement math.
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


def launch_tool():
    """Launches the Multi-File Importer (entry point used by the menu).

    Returns:
        MultiFileImporterController: Controller of the launched tool.
    """
    return build_gui_multi_file_importer()


def build_gui_multi_file_importer():
    """Builds the Multi-File Importer view, model and controller.

    Returns:
        MultiFileImporterController: Controller of the launched tool.
    """
    from gt.tools.multi_file_importer import multi_file_importer_controller
    from gt.tools.multi_file_importer import multi_file_importer_model
    from gt.tools.multi_file_importer import multi_file_importer_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = multi_file_importer_view.MultiFileImporterView(parent=context.get_parent(), version=__version__)
        model = multi_file_importer_model.MultiFileImporterModel()
        controller = multi_file_importer_controller.MultiFileImporterController(model=model, view=view)
        return controller


if __name__ == "__main__":
    launch_tool()
