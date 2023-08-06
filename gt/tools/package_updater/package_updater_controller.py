"""
Curve Library Controller

This module contains the CurveLibraryController class responsible for managing interactions between the
CurveLibraryModel and the user interface.
"""
from gt.utils.prefs_utils import PackageCache
import threading
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PackageUpdaterController:
    def __init__(self, model, view):
        """
        Initialize the PackageUpdaterController object.

        Args:
            model: The CurveLibraryModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        # Connections
        self.view.update_button.clicked.connect(self.update_package)
        # Initial Checks:
        self.refresh_updater_data()

    def update_package(self):
        """
        Updates package to the latest version found on GitHub
        """
        cache = PackageCache()
        kwargs = {"cache": cache, "force_update": False}

        def _maya_update_latest_package():
            """ Internal function used to update package using threads in Maya """
            from maya import utils
            utils.executeDeferred(self.model.update_package, **kwargs)

        try:
            thread = threading.Thread(None, target=_maya_update_latest_package)
            thread.start()
        except Exception as e:
            logger.warning(f'Unable to update package. Issue: {e}')
        finally:
            cache.clear_cache()

    def refresh_updater_data(self):
        """
        Checks for updates and refreshes the updater UI to reflect retrieved data
        """
        def _maya_retrieve_update_data():
            """ Internal function used to check for updates using threads in Maya """
            from maya import utils
            utils.executeDeferred(self.model.check_for_updates)

        try:
            thread = threading.Thread(None, target=_maya_retrieve_update_data)
            thread.start()
        except Exception as e:
            logger.warning(f'Unable to refresh updater. Issue: {e}')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
