"""
Package Updater Model

Classes:
    PackageUpdaterModel: A class for checking for updates
"""
from gt.utils.prefs_utils import Prefs
from gt.utils import version_utils
from datetime import datetime
import threading
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
PREFS_NAME = "package_updater"
PREFS_LAST_DATE = "last_date"  # Format: '2020-01-01 17:08:00'
PREFS_AUTO_CHECK = "auto_check"
PREFS_INTERVAL_DAYS = "interval_days"
PACKAGE_RELEASES_URL = 'https://github.com/TrevisanGMW/gt-tools/releases/latest'


class PackageUpdaterModel:
    def __init__(self):
        """
        Initialize the PackageUpdaterModel object.
        """
        self.preferences = Prefs(PREFS_NAME)
        today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        self.last_date = str(today_date)
        self.auto_check = True
        self.interval_days = 15
        self.update_preferences()
        # Status
        self.status = "Not Installed"
        self.web_response = None
        self.installed_version = "0.0.0"
        self.latest_github_version = "0.0.0"

    def get_preferences(self):
        return self.preferences.get_raw_preferences()

    def update_preferences(self):
        """
        Updates preferences from installation folder. If nothing is found, it keeps previous values.
        """
        self.last_date = self.preferences.get_string(key=PREFS_LAST_DATE, default=self.last_date)
        self.auto_check = self.preferences.get_bool(key=PREFS_AUTO_CHECK, default=self.auto_check)
        self.interval_days = self.preferences.get_int(key=PREFS_INTERVAL_DAYS, default=self.interval_days)

    def set_preferences(self):
        """ Set preferences and save it to disk """
        self.preferences.set_string(key=PREFS_LAST_DATE, value=str(self.last_date))
        self.preferences.set_bool(key=PREFS_AUTO_CHECK, value=self.auto_check)
        self.preferences.set_int(key=PREFS_INTERVAL_DAYS, value=self.interval_days)
        self.preferences.save()

    def check_for_updates(self):
        """ Checks current version against web version and updates stored values with retrieved data """
        # Current Version
        self.installed_version = version_utils.get_installed_version()
        # Latest Version
        response, response_content = version_utils.get_latest_github_release()
        self.latest_github_version = version_utils.get_latest_github_release_version(response_content=response_content)
        # Status
        if not version_utils.is_semantic_version(self.installed_version, metadata_ok=False) or \
                not version_utils.is_semantic_version(self.latest_github_version, metadata_ok=False):
            self.status = "Unknown"
        comparison_result = version_utils.compare_versions(self.installed_version, self.latest_github_version)
        if comparison_result == version_utils.VERSION_BIGGER:
            self.status = "Unreleased update!"
        elif comparison_result == version_utils.VERSION_SMALLER:
            self.status = "New Update Available!"
        else:
            self.status = "You're up to date!"
        # Web Response
        self.web_response = response.status

    def threaded_check_for_updates(self):
        """ Threaded Check for updates """
        thread = threading.Thread(None, target=self.check_for_updates)
        thread.start()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    import maya.standalone
    # maya.standalone.initialize()
    model = PackageUpdaterModel()
    # model.set_preferences()
    # get_installed_version()
    model.threaded_check_for_updates()


