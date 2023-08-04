"""
Package Updater Model

Classes:
    PackageUpdaterModel: A class for checking for updates
"""
from gt.utils.setup_utils import is_legacy_version_install_present, get_installed_core_module_path
from gt.utils.version_utils import get_package_version, get_legacy_package_version
from gt.utils.feedback_utils import print_when_true
from gt.utils.prefs_utils import Prefs
from datetime import datetime
import logging
import os

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

    def check_for_updates(self, verbose=True):
        # Get Installed Package Version
        package_core_module = get_installed_core_module_path(only_existing=False)
        if not os.path.exists(package_core_module):
            message = f'Package not installed. Missing path: "{package_core_module}"'
            print_when_true(message, do_print=verbose, use_system_write=True)
            return
        installed_version = get_package_version(package_path=package_core_module)
        if not installed_version and is_legacy_version_install_present():
            installed_version = get_legacy_package_version()
        return installed_version


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    import maya.standalone
    maya.standalone.initialize()
    model = PackageUpdaterModel()
    # model.set_preferences()
    model.check_for_updates()

