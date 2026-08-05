"""
Outliner Sorter Compatibility Entry Points
"""

from gt.tools.outliner_sorter import build_gui_outliner_sorter
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

script_name = "Outliner Sorter"
script_version = "?.?.?"


if __name__ == "__main__":
    build_gui_outliner_sorter()
