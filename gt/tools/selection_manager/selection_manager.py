"""
Selection Manager Compatibility Entry Points
"""

from gt.tools.selection_manager import build_gui_help_selection_manager
from gt.tools.selection_manager import build_gui_selection_manager
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

script_name = "Selection Manager"
script_version = "?.?.?"


if __name__ == "__main__":
    build_gui_selection_manager()
