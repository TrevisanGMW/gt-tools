"""
Package Updater Controller
"""
from gt.utils.iterable_utils import get_next_dict_item
from gt.utils.system_utils import execute_deferred
from gt.utils.prefs_utils import PackageCache
from datetime import datetime, timedelta
from gt.ui import resource_library
from gt.utils import version_utils
import threading
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AttributesToPythonController:
    def __init__(self, model, view):
        """
        Initialize the AttributesToPythonController object.

        Args:
            model: The AttributesToPythonModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # # Connections
        # self.view.interval_btn.clicked.connect(self.update_view_interval_button)
        # self.view.refresh_btn.clicked.connect(self.refresh_updater_data_threaded_maya)
        # self.view.auto_check_btn.clicked.connect(self.cycle_auto_check)
        # self.view.update_btn.clicked.connect(self.update_package_threaded_maya)

        self.view.show()


if __name__ == "__main__":
    print('Run it from "__init__.py".')

