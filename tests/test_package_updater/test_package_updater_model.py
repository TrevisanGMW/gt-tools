from gt.utils.prefs_utils import PackageCache
from unittest.mock import MagicMock, patch
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.package_updater import package_updater_model
from tests import maya_test_tools


class TestCurveLibraryModel(unittest.TestCase):
    @patch('gt.tools.package_updater.package_updater_model.Prefs')
    def setUp(self, mocked_prefs):
        self.mocked_prefs = mocked_prefs.return_value
        self.mocked_prefs.get_raw_preferences.return_value = {"key": "value"}
        self.mocked_prefs.get_string.return_value = "2023-01-01 00:00:00"
        self.mocked_prefs.get_bool.return_value = True
        self.mocked_prefs.get_int.return_value = 15

        self.model = package_updater_model.PackageUpdaterModel()
        self.model.preferences = self.mocked_prefs
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_init(self):
        self.assertIsInstance(self.model.preferences, MagicMock)
        self.assertEqual(self.mocked_prefs, self.model.preferences)
        self.assertEqual(self.model.last_date, "2023-01-01 00:00:00")
        self.assertTrue(self.model.auto_check)
        self.assertEqual(15, self.model.interval_days)
        self.assertEqual("Unknown", self.model.status)
        self.assertEqual("0.0.0", self.model.installed_version)
        self.assertEqual("0.0.0", self.model.latest_github_version)
        self.assertFalse(self.model.needs_update)
        self.assertIsNone(self.model.comparison_result)
        self.assertIsNone(self.model.web_response_code)
        self.assertIsNone(self.model.web_response_reason)
        self.assertIsNone(self.model.response_content)
        self.assertIsNone(self.model.progress_win)
        self.assertFalse(self.model.requested_online_data)

    def test_get_preferences(self):
        preferences = self.model.get_preferences()
        expected = {"key": "value"}
        self.assertEqual(expected, preferences)

    def test_update_preferences(self):
        self.model.update_preferences()
        expected_num_calls = 2  # One init, one manual call
        self.assertEqual(expected_num_calls, self.model.preferences.get_string.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.get_bool.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.get_int.call_count)
        self.model.preferences.get_string.assert_called_with(key=package_updater_model.PREFS_LAST_DATE,
                                                             default='2023-01-01 00:00:00')
        self.model.preferences.get_bool.assert_called_with(key=package_updater_model.PREFS_AUTO_CHECK,
                                                           default=True)
        self.model.preferences.get_int.assert_called_with(key=package_updater_model.PREFS_INTERVAL_DAYS,
                                                          default=15)

    def test_save_preferences(self):
        self.last_date = '2023-01-01 00:00:00'
        self.model.save_preferences()
        expected_num_calls = 1
        self.assertEqual(expected_num_calls, self.model.preferences.set_string.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.set_bool.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.set_int.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.save.call_count)
        self.model.preferences.set_string.assert_called_with(key=package_updater_model.PREFS_LAST_DATE,
                                                             value='2023-01-01 00:00:00')
        self.model.preferences.set_bool.assert_called_with(key=package_updater_model.PREFS_AUTO_CHECK,
                                                           value=True)
        self.model.preferences.set_int.assert_called_with(key=package_updater_model.PREFS_INTERVAL_DAYS,
                                                          value=15)

    def test_get_auto_check(self):
        result = self.model.get_auto_check()
        expected = True
        self.assertEqual(expected, result)

    def test_get_interval_days(self):
        result = self.model.get_interval_days()
        expected = 15
        self.assertEqual(expected, result)

    def test_set_auto_check(self):
        self.model.set_auto_check(False)
        result = self.model.auto_check
        expected = False
        self.assertEqual(expected, result)

    def test_set_interval_days(self):
        self.model.set_interval_days(20)
        result = self.model.interval_days
        expected = 20
        self.assertEqual(expected, result)

    def test_save_last_check_date_as_now(self):
        self.model.save_last_check_date_as_now()
        result = self.model.last_date
        not_expected = '2023-01-01 00:00:00'
        self.assertNotEqual(not_expected, result)
        expected_num_calls = 1
        self.assertEqual(expected_num_calls, self.model.preferences.set_string.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.set_bool.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.set_int.call_count)
        self.assertEqual(expected_num_calls, self.model.preferences.save.call_count)
        self.model.preferences.set_string.assert_called()

    def test_get_version_comparison_result(self):
        result = self.model.get_version_comparison_result()
        expected = None
        self.assertEqual(expected, result)

    def test_get_web_response_code(self):
        result = self.model.get_web_response_code()
        expected = None
        self.assertEqual(expected, result)

    def test_get_web_response_reason(self):
        result = self.model.get_web_response_reason()
        expected = None
        self.assertEqual(expected, result)

    def test_get_installed_version(self):
        result = self.model.get_installed_version()
        expected = "0.0.0"
        self.assertEqual(expected, result)

    def test_get_latest_github_version(self):
        result = self.model.get_latest_github_version()
        expected = "0.0.0"
        self.assertEqual(expected, result)

    def test_is_time_to_update(self):
        result = self.model.is_time_to_update()
        expected = True
        self.assertEqual(expected, result)

    def test_get_status_description(self):
        result = self.model.get_status_description()
        expected = "Unknown"
        self.assertEqual(expected, result)

    def test_refresh_status_description(self):
        self.model.refresh_status_description()
        result = self.model.get_status_description()
        expected = "You're up to date!"
        self.assertEqual(expected, result)

    def test_refresh_status_description_higher(self):
        self.model.latest_github_version = "1.2.3"
        self.model.refresh_status_description()
        result = self.model.get_status_description()
        expected = "New Update Available!"
        self.assertEqual(expected, result)

    def test_refresh_status_description_lower(self):
        self.model.installed_version = "1.2.3"
        self.model.refresh_status_description()
        result = self.model.get_status_description()
        expected = "Unreleased update!"
        self.assertEqual(expected, result)

    def test_has_requested_online_data(self):
        result = self.model.has_requested_online_data()
        expected = False
        self.assertEqual(expected, result)

    def test_is_update_needed(self):
        result = self.model.is_update_needed()
        expected = False
        self.assertEqual(expected, result)

    @patch('gt.utils.version_utils.get_github_releases')
    def test_request_github_data(self, mocked_get_github_releases):
        mocked_response = MagicMock()
        mocked_response.status = 200
        mocked_response.reason = "OK"
        mocked_content = {"body": "Mocked Body"}
        mocked_get_github_releases.return_value = (mocked_response, mocked_content)
        self.model.request_github_data()
        mocked_get_github_releases.assert_called()
        result = self.model.has_requested_online_data()
        expected = True
        self.assertEqual(expected, result)
        result = self.model.get_web_response_code()
        expected = 200
        self.assertEqual(expected, result)
        result = self.model.get_web_response_reason()
        expected = "OK"
        self.assertEqual(expected, result)

    @patch('gt.utils.version_utils.get_latest_github_release_version')
    @patch('gt.utils.version_utils.get_installed_version')
    @patch('gt.utils.version_utils.get_github_releases')
    def test_check_for_updates(self, mocked_get_github_releases,
                               mocked_get_installed_version,
                               mocked_get_latest_github_release_version):
        mocked_get_installed_version.return_value = "1.2.3"
        mocked_get_latest_github_release_version.return_value = "4.5.6"
        mocked_response = MagicMock()
        mocked_response.status = 200
        mocked_response.reason = "OK"
        mocked_content = {"body": "Mocked Body"}
        mocked_get_github_releases.return_value = (mocked_response, mocked_content)
        self.model.check_for_updates()
        mocked_get_github_releases.assert_called()
        mocked_get_installed_version.assert_called()
        mocked_get_latest_github_release_version.assert_called()
        result = self.model.has_requested_online_data()
        expected = True
        self.assertEqual(expected, result)
        result = self.model.get_installed_version()
        expected = "1.2.3"
        self.assertEqual(expected, result)
        result = self.model.get_latest_github_version()
        expected = "4.5.6"
        self.assertEqual(expected, result)

    def test_get_releases_changelog(self):
        self.model.response_content = '[{"tag_name":"v1.2.3","published_at":"date1", "body":"body1"},' \
                                      '{"tag_name":"v1.2.2","published_at":"date2", "body":"body2"}]'
        result = self.model.get_releases_changelog()
        expected = {'v1.2.2 - (date2)\n': 'body2\n', 'v1.2.3 - (date1)\n': 'body1\n'}
        self.assertEqual(expected, result)

    def test_get_releases_changelog_invalid_response(self):
        logging.disable(logging.WARNING)
        result = self.model.get_releases_changelog()
        logging.disable(logging.NOTSET)
        expected = None
        self.assertEqual(expected, result)

    @patch('os.listdir')
    @patch('gt.utils.setup_utils.install_package')
    @patch('gt.utils.feedback_utils.FeedbackMessage')
    @patch('gt.tools.package_updater.package_updater_model.unzip_zip_file')
    @patch('gt.tools.package_updater.package_updater_model.download_file')
    @patch('gt.tools.package_updater.package_updater_model.progress_bar')
    @patch('gt.tools.package_updater.package_updater_model.remove_package_loaded_modules')
    @patch('gt.tools.package_updater.package_updater_model.reload_package_loaded_modules')
    @patch('gt.tools.package_updater.package_updater_model.PackageCache', spec_set=PackageCache)
    def test_update_package(self, mocked_cache, mocked_reload_modules, mocked_remove_modules,
                            mocked_progress_bar, mocked_download_file, mocked_unzip_zip_file, mocked_feedback,
                            mocked_install_package, mocked_os_dir):
        initial_sys_path = sys.path.copy()
        self.model.needs_update = True
        self.model.response_content = '[{"zipball_url":"mocked_url","published_at":"date1", "body":"body1"}]'
        temp_dir = maya_test_tools.generate_test_temp_dir()
        from gt.utils.setup_utils import PACKAGE_MAIN_MODULE
        temp_dir_extract = os.path.join(temp_dir, PACKAGE_MAIN_MODULE, "extracted")
        os.makedirs(temp_dir_extract)
        mocked_os_dir.return_value = [temp_dir_extract]

        class MockedPackageCache:
            @staticmethod
            def get_cache_dir():
                return temp_dir

            def add_path_to_cache_list(self, path_to_add):
                pass

            def clear_cache(self):
                pass

        mocked_cache.return_value = MockedPackageCache()
        self.model.update_package(cache=None, force_update=False)
        mocked_cache.assert_called()
        mocked_os_dir.assert_called()
        mocked_download_file.assert_called()
        mocked_unzip_zip_file.assert_called()
        mocked_remove_modules.assert_called()
        mocked_reload_modules.assert_called()
        self.assertIn(temp_dir_extract, sys.path)
        mocked_install_package.return_value = False
        mocked_install_package.assert_called()
        mocked_feedback.assert_called()
        # Clean up
        sys.path = initial_sys_path
