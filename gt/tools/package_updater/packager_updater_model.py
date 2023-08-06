"""
Package Updater Model

Classes:
    PackageUpdaterModel: A class for checking for updates
"""
from gt.utils.setup_utils import remove_package_loaded_modules
from gt.utils.setup_utils import PACKAGE_MAIN_MODULE
from gt.utils.prefs_utils import Prefs, PackageCache
from gt.utils.request_utils import download_file
from gt.utils.string_utils import remove_prefix
from gt.utils.data_utils import unzip_zip_file
from PySide2.QtWidgets import QApplication
from gt.utils import feedback_utils
from gt.utils import version_utils
from gt.ui import resource_library
from gt.ui import progress_bar
from datetime import datetime
from json import loads
import threading
import logging
import sys
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
        # Misc
        self.progress_win = None

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

    def update_package(self, cache=None, force_update=True):
        """
        Updates the package to the latest release found on GitHub.
        Args:
            cache (PackageCache, optional): If provided, it will be used to generate the cache.
                                            If not, a PackageCache object will be created during installation.
                                            The temporary cache will point to the default cache location:
                                            "maya/gt-tools/cache" and will automatically be purged at the end.
                                            If the operation crashes, It's not guaranteed that it will be purged.
            force_update (bool, optional): If active, it will update even if the update is not necessary.
        """
        if not self.needs_update and not force_update:
            logger.debug("Package does not need to be updated.")
            return

        zip_file_url = None
        try:
            content = loads(self.response_content)
            if isinstance(content, list):
                content = content[0]
            zip_file_url = content.get('zipball_url')
            if not zip_file_url:
                raise Exception('Missing "zipball_url" value.')
        except Exception as e:
            logger.warning(f'Unable to update. Failed to interpret content data. Issue: "{str(e)}".')
            return

        if not QApplication.instance():
            app = QApplication(sys.argv)

        self.progress_win = progress_bar.ProgressBarWindow()
        self.progress_win.show()
        self.progress_win.set_progress_bar_name("Updating Script Package...")

        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        # Number of print functions inside installer (7) + download (1) + extract (1) + clean-up (1)
        self.progress_win.set_progress_bar_max_value(10)
        self.progress_win.increase_progress_bar_value()

        if cache and isinstance(cache, PackageCache):
            _cache = cache
        else:
            _cache = PackageCache()
        cache_dir = _cache.get_cache_dir()
        cache_download = os.path.join(cache_dir, "package_update.zip")
        cache_extract = os.path.join(cache_dir, "update_extract")
        _cache.add_path_to_cache_list(cache_download)
        _cache.add_path_to_cache_list(cache_extract)

        if not os.path.exists(cache_dir):
            message = f'Unable to create cache location. Update operation cancelled. Location: {cache_dir}'
            self.progress_win.add_text_to_output_box(input_string=message, color=resource_library.Color.Hex.red_soft)
            return

        # Download Update --------------------------------------------------
        self.progress_win.add_text_to_output_box("Downloading Update...")
        output_box_content = self.progress_win.get_output_box_plain_text()

        def print_download_progress(progress):
            output_box = output_box_content
            output_box += f"\nDownload progress: {progress:.2f}%"
            self.progress_win.clear_output_box()
            self.progress_win.add_text_to_output_box(output_box, as_new_line=True)

        try:
            download_file(url=zip_file_url, destination=cache_download, chunk_size=65536,
                          callback=print_download_progress)
            self.progress_win.increase_progress_bar_value()
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=resource_library.Color.Hex.red_soft)
            return

        # Extract Update ----------------------------------------------------
        self.progress_win.add_text_to_output_box("Extracting zip file...", as_new_line=True)
        output_box_content = self.progress_win.get_output_box_plain_text()

        def print_extract_progress(current_file, total_files):
            percent_complete = (current_file / total_files) * 100
            output_box = output_box_content
            output_box += f"\nExtract progress: {percent_complete:.2f}% ({current_file}/{total_files})"
            self.progress_win.clear_output_box()
            self.progress_win.add_text_to_output_box(output_box)

        try:
            unzip_zip_file(zip_file_path=cache_download, extract_path=cache_extract, callback=print_extract_progress)
            self.progress_win.increase_progress_bar_value()
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=resource_library.Color.Hex.red_soft)
            return

        # Validate Extraction ----------------------------------------------------
        extracted_content = os.listdir(cache_extract)  # TODO this must be purged to only have one folder
        if not extracted_content:
            message = f'Extraction returned no files.\nExtraction Path: "{cache_extract}".'
            self.progress_win.add_text_to_output_box(input_string=message, color=resource_library.Color.Hex.red_soft)
            return
        extracted_dir_name = extracted_content[0]
        extracted_dir_path = os.path.join(cache_extract, extracted_dir_name)
        extracted_module_path = None
        if os.path.exists(extracted_dir_path) and os.path.isdir(extracted_dir_path):
            extracted_module_path = os.path.join(extracted_dir_path, PACKAGE_MAIN_MODULE)
        if not extracted_module_path:
            message = f'Extracted files are missing core module.\nExtraction Path: "{cache_extract}".'
            self.progress_win.add_text_to_output_box(input_string=message, color=resource_library.Color.Hex.red_soft)
            return

        # Remove existing loaded modules (So it uses the new one) ----------------
        removed_modules = remove_package_loaded_modules()
        if removed_modules:
            self.progress_win.add_text_to_output_box("Initializing downloaded files...", as_new_line=True)

        # Prepend sys path with download location
        sys.path.insert(0, extracted_dir_path)
        sys.path.insert(0, extracted_module_path)

        # Import and run installer -----------------------------------------------
        import gt.utils.setup_utils as setup_utils
        is_installed = False
        try:
            is_installed = setup_utils.install_package(callbacks=[self.progress_win.add_text_to_output_box,
                                                                  self.progress_win.increase_progress_bar_value])
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=resource_library.Color.Hex.red_soft)

        # Update feedback package ------------------------------------------------
        if is_installed:
            self.progress_win.set_progress_bar_done()
            self.progress_win.change_last_line_color(resource_library.Color.Hex.green_soft)
            feedback = feedback_utils.FeedbackMessage(intro="GT-Tools",
                                                      style_intro=f"color:{resource_library.Color.Hex.cyan_soft};"
                                                                  f"text-decoration:underline;",
                                                      conclusion="has been updated and is now active.")
            feedback.print_inview_message(stay_time=4000)
        else:
            self.progress_win.change_last_line_color(resource_library.Color.Hex.red_soft)
        _cache.clear_cache()

        if QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    import maya.standalone
    # maya.standalone.initialize()
    model = PackageUpdaterModel()
    model.check_for_updates()
    model.update_package()
    # print(model.__dict__)

