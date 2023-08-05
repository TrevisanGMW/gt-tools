"""
Package Updater Model

Classes:
    PackageUpdaterModel: A class for checking for updates
"""
from gt.utils.string_utils import remove_prefix
from gt.utils.prefs_utils import Prefs
from gt.utils import version_utils
from datetime import datetime
from json import loads
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
        self.installed_version = "0.0.0"
        self.latest_github_version = "0.0.0"
        self.needs_update = False
        # Request Data
        self.web_response = None
        self.response_content = None

    def get_preferences(self):
        """
        Returns existing preferences in raw form (dictionary)
        Returns:
            dict: A dictionary with the current preferences.
        """
        return self.preferences.get_raw_preferences()

    def update_preferences(self):
        """
        Updates preferences from installation folder. If nothing is found, it keeps previous values.
        """
        self.last_date = self.preferences.get_string(key=PREFS_LAST_DATE, default=self.last_date)
        self.auto_check = self.preferences.get_bool(key=PREFS_AUTO_CHECK, default=self.auto_check)
        self.interval_days = self.preferences.get_int(key=PREFS_INTERVAL_DAYS, default=self.interval_days)

    def save_preferences(self):
        """ Set preferences and save it to disk """
        self.preferences.set_string(key=PREFS_LAST_DATE, value=str(self.last_date))
        self.preferences.set_bool(key=PREFS_AUTO_CHECK, value=self.auto_check)
        self.preferences.set_int(key=PREFS_INTERVAL_DAYS, value=self.interval_days)
        self.preferences.save()

    def refresh_status(self):
        """ Updates status and  by comparing installed version with the latest GitHub version """
        if not version_utils.is_semantic_version(self.installed_version, metadata_ok=False) or \
                not version_utils.is_semantic_version(self.latest_github_version, metadata_ok=False):
            self.status = "Unknown"
        comparison_result = version_utils.compare_versions(self.installed_version, self.latest_github_version)
        if comparison_result == version_utils.VERSION_BIGGER:
            self.status = "Unreleased update!"
            self.needs_update = False
        elif comparison_result == version_utils.VERSION_SMALLER:
            self.status = "New Update Available!"
            self.needs_update = True
        else:
            self.status = "You're up to date!"
            self.needs_update = False

    def request_github_data(self):
        """ Requests GitHub data and stores it """
        response, response_content = version_utils.get_github_releases()
        self.response_content = response_content
        self.web_response = response.status

    def check_for_updates(self):
        """ Checks current version against web version and updates stored values with retrieved data """
        # Current Version
        self.installed_version = version_utils.get_installed_version()
        # Latest Version
        self.request_github_data()
        response_content = self.response_content
        self.latest_github_version = version_utils.get_latest_github_release_version(response_content=response_content)
        # Status
        self.refresh_status()

    def threaded_check_for_updates(self):
        """ Threaded Check for updates """
        thread = threading.Thread(None, target=self.check_for_updates)
        thread.start()

    def get_releases_changelog(self, num_releases=3):
        """
        Creates a list of strings with the tag name, release date and body for the latest releases.
        Useful for when presenting a list of changes to the user.

        Args:
            num_releases (int, optional): Number of releases to return. If the total is lower than the provided number,
                                          that will be returned instead. For example: If 10 releases are found but this
                                          variable is set to 3, then only the 3 latest releases will be returned.
                                          If num_releases = 3, but only 2 were found, then 2 will be returned.
        Returns:
            list: A list of strings with tag name, release date and body.
        """
        content = None
        changelog_data = []
        if not self.response_content:
            logger.warning("Unable to retrieve changelog. Request content is empty")
            return
        try:
            content = loads(self.response_content)
        except Exception as e:
            logger.warning(f'Unable to interpret content data. Issue: "{str(e)}".')
        if not content:
            logger.warning("Unable to retrieve changelog. Request content is empty")
            return
        if isinstance(content, list) and len(content) >= num_releases:
            content = content[:3]
        for data in content:
            text_line = ''
            text_line += data.get('tag_name', '')
            published_at = data.get('published_at', '').split('T')[0]
            text_line += f' - ({published_at})\n'
            body = data.get('body', '')
            text_line += remove_prefix(body, "\r\n## What's Changed\r\n\r\n")
            text_line += "\n"
            changelog_data.append(text_line)
        return changelog_data


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    import maya.standalone
    maya.standalone.initialize()
    model = PackageUpdaterModel()
    model.check_for_updates()
    changelog = model.get_releases_changelog()
    from pprint import pprint
    print(changelog)
    # print(model.__dict__)

