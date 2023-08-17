"""
Curve Library Controller

This module contains the CurveLibraryController class responsible for managing interactions between the
CurveLibraryModel and the user interface.
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
        # Clear View
        self.set_view_to_waiting()
        # Connections
        self.view.interval_btn.clicked.connect(self.update_view_interval_button)
        self.view.refresh_btn.clicked.connect(self.refresh_updater_data_threaded_maya)
        self.view.auto_check_btn.clicked.connect(self.cycle_auto_check)
        self.view.update_btn.clicked.connect(self.update_package_threaded_maya)
        # Initial Checks:
        if not model.has_requested_online_data():
            self.refresh_updater_data_threaded_maya()
        else:
            self.refresh_view_values()
        self.view.show()

    def update_view_status_with_color(self, status):
        """
        Updates the status description using the appropriate color.
        Green = Same, Red = Lower, Purple = Unreleased.
        Args:
            status (str): String to be used in the status description
        """
        comparison_result = self.model.get_version_comparison_result()
        text_color_hex = resource_library.Color.Hex.black
        if comparison_result == version_utils.VERSION_BIGGER:
            bg_color = resource_library.Color.Hex.purple
        elif comparison_result == version_utils.VERSION_SMALLER:
            bg_color = resource_library.Color.Hex.red_soft
        elif comparison_result == version_utils.VERSION_EQUAL:
            bg_color = resource_library.Color.Hex.green_soft
        else:
            text_color_hex = resource_library.Color.Hex.white
            bg_color = resource_library.Color.Hex.grey_dark
        self.view.update_status(status=status,
                                text_color_hex=text_color_hex,
                                bg_color_hex=bg_color)

    def update_view_web_response_with_color(self, response_description):
        """
        Updates the web-response description using the appropriate color.
        Args:
            response_description (str): String to be used in the web-response description
        """
        text_color_hex = resource_library.Color.Hex.black
        if response_description == "Requesting...":
            bg_color = resource_library.Color.Hex.yellow
        elif response_description == "None":
            bg_color = resource_library.Color.Hex.red_soft
        else:
            text_color_hex = resource_library.Color.Hex.white
            bg_color = resource_library.Color.Hex.grey
        self.view.update_web_response(response=response_description,
                                      text_color_hex=text_color_hex,
                                      bg_color_hex=bg_color)

    def set_view_to_waiting(self):
        """ Clear view values showing that it's waiting for a refresh """
        self.view.change_update_button_state(state=False)
        self.view.update_installed_version(version=f'v?.?.?')
        self.view.update_latest_release(version=f'v?.?.?')
        self.view.update_status(status="Unknown")
        self.update_view_web_response_with_color(response_description="Requesting...")
        self.view.clear_changelog_box()

    def refresh_view_values(self):
        """ Updates the view with values found in the model """
        auto_check = self.model.get_auto_check()
        self.view.update_auto_check_status_btn(is_active=auto_check)
        interval_days = self.model.get_interval_days()
        self.update_view_interval_button(new_interval=interval_days, cycle=False, verbose=False)
        if self.model.is_update_needed():
            self.view.change_update_button_state(state=True)
        else:
            self.view.change_update_button_state(state=False)
        installed_version = self.model.get_installed_version()
        self.view.update_installed_version(version=f'v{installed_version}')
        latest_github_version = self.model.get_latest_github_version()
        self.view.update_latest_release(version=f'v{latest_github_version}')
        status_description = self.model.get_status_description()
        self.update_view_status_with_color(status=status_description)
        web_response = self.model.get_web_response_reason()
        self.update_view_web_response_with_color(response_description=str(web_response))
        self.update_auto_check()
        self.view.change_update_button_state(state=self.model.is_update_needed())
        self.populate_changelog_box()

    def populate_changelog_box(self):
        """ Populates the changelog box with changelog data """
        self.view.clear_changelog_box()
        if self.model.has_failed_online_request():
            return
        changelog = self.model.get_releases_changelog() or {}
        for tag_name, description in changelog.items():
            self.view.add_text_to_changelog(text=tag_name,
                                            text_color_hex=resource_library.Color.Hex.white)
            self.view.add_text_to_changelog(text=description.replace("\r\n", "\n"),
                                            text_color_hex=resource_library.Color.Hex.grey_lighter)

    def update_view_interval_button(self, new_interval=None, cycle=True, verbose=True):
        """
        Updates the interval button text.
        Args:
            new_interval (int, optional): If provided, this value will be used as the new interval.
                                          Note: It will be converted to string and "days" will be added to the end.
            cycle (bool, optional): If active, it will cycle through a pre-determined list of available periods.
            verbose (bool, optional): If active, it will print the changes so the user knows how it's been updated.
        """
        current_interval = new_interval
        if not new_interval:
            current_interval = self.model.get_interval_days()

        interval_list = {1: "1 day",
                         5: "5 days",
                         15: "15 days",
                         30: "1 month",
                         91: '3 months',
                         182: '6 months',
                         365: '1 year'}

        if cycle and current_interval in interval_list:
            current_interval = get_next_dict_item(interval_list, current_interval, cycle=True)[0]
        elif cycle:
            current_interval = 1

        # Determine Button String
        if current_interval in interval_list:
            time_period = interval_list.get(current_interval)
        else:
            time_period = f'{current_interval} days'
        self.view.update_interval_button(time_period=time_period)
        self.model.set_interval_days(interval_days=current_interval)
        self.model.save_preferences()
        if verbose:
            # Create feedback
            current_date = datetime.now()
            updated_date = current_date + timedelta(days=current_interval)
            formatted_date = updated_date.strftime('%Y-%B-%d')
            sys.stdout.write(f'Interval Set To: {time_period}. - (Next check date: {str(formatted_date)})\n')

    def update_auto_check(self):
        """
        Update the auto check to the value stored in the model
        """
        state = self.model.get_auto_check()
        self.view.update_auto_check_status_btn(is_active=state)
        self.view.change_interval_button_state(state=state)

    def cycle_auto_check(self):
        """
        Update the auto check button by cycling through Activated/Deactivated.
        Also updates to enabled state of the interval button as an interval is only necessary when activated.
        """
        new_state = not self.model.get_auto_check()
        self.view.update_auto_check_status_btn(is_active=new_state)
        self.view.change_interval_button_state(state=new_state)
        self.model.set_auto_check(auto_check=new_state)
        self.model.save_preferences()
        if new_state:
            sys.stdout.write('Auto Check For Updates: Activated\n')
        else:
            sys.stdout.write('Auto Check For Updates: Deactivated\n')

    def update_package(self, cache=None):
        """
        Updates package to the latest version found on GitHub
        """
        self.model.update_package(cache=cache)
        self.refresh_view_values()
        if self.model.progress_win and self.model.progress_win.first_button:
            self.model.progress_win.first_button.clicked.connect(self.view.close_window)

    def update_package_threaded_maya(self):
        """
        Updates package to the latest version found on GitHub - Threaded for Maya
        """
        cache = PackageCache()

        def _maya_update_latest_package():
            """ Internal function used to update package using threads in Maya """
            execute_deferred(self.update_package, cache)

        try:
            thread = threading.Thread(None, target=_maya_update_latest_package)
            thread.start()
            cache.clear_cache()
        except Exception as e:
            logger.warning(f'Unable to update package. Issue: {e}')
        finally:
            cache.clear_cache()

    def refresh_updater_data(self):
        """
        Checks for updates and refreshes the updater UI to reflect retrieved data
        """
        self.model.check_for_updates()
        self.model.save_last_check_date_as_now()
        self.refresh_view_values()

    def refresh_updater_data_threaded_maya(self):
        """
        Threaded version of the function "refresh_updater_data" maya to run in Maya
        Checks for updates and refreshes the updater UI to reflect retrieved data
        """
        def _maya_retrieve_update_data():
            """ Internal function used to check for updates using threads in Maya """
            execute_deferred(self.refresh_updater_data)

        try:
            thread = threading.Thread(None, target=_maya_retrieve_update_data)
            thread.start()
        except Exception as e:
            logger.warning(f'Unable to refresh updater. Issue: {e}')


if __name__ == "__main__":
    print('Run it from "__init__.py".')

