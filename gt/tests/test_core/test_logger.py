from unittest.mock import patch, MagicMock
from io import StringIO
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.core import logger as core_logger


class TestLoggerCore(unittest.TestCase):
    def test_custom_severity_levels(self):
        attributes = vars(core_logger.CustomSeverityLevels)
        keys = [attr for attr in attributes if not (attr.startswith("__") and attr.endswith("__"))]
        for key in keys:
            value = getattr(core_logger.CustomSeverityLevels, key)
            if value is None:
                raise Exception(f"Missing value for: {key}")
            if callable(value):  # Ignore Functions
                continue
            if not isinstance(value, int):
                raise Exception(f'Incorrect value type. Expected int, but got: "{type(value)}".')

    def test_custom_severity_levels_all_levels_func(self):
        result = core_logger.CustomSeverityLevels.get_all_levels()
        expected_type = list
        self.assertIsInstance(result, expected_type)

    def test_custom_severity_levels_levels_dict_func(self):
        result = core_logger.CustomSeverityLevels.get_levels_dict()
        expected_type = dict
        self.assertIsInstance(result, expected_type)

    def test_log_formatting(self):
        attributes = vars(core_logger.LogFormatting)
        keys = [attr for attr in attributes if not (attr.startswith("__") and attr.endswith("__"))]
        for key in keys:
            value = getattr(core_logger.LogFormatting, key)
            if value is None:
                raise Exception(f"Missing value for: {key}")
            if callable(value):  # Ignore Functions
                continue
            if not isinstance(value, str):
                raise Exception(f'Incorrect value type. Expected str, but got: "{type(value)}".')

    def test_add_log_level_custom_level_added(self):
        level_name = "SUCCESS"
        level_num = 25

        core_logger.add_log_level(level_name, level_num)

        self.assertEqual(logging.getLevelName(level_num), level_name.upper())

    def test_add_log_level_method_attached_to_logger(self):
        level_name = "SUCCESS"
        level_num = 25

        core_logger.add_log_level(level_name, level_num)

        _logger = logging.getLogger("test_logger")
        self.assertTrue(hasattr(_logger, level_name.lower()))

    @patch("gt.core.logger.CustomSeverityLevels.get_levels_dict")
    def test_add_custom_log_levels_all_levels_added(self, mock_get_levels_dict):
        mock_get_levels_dict.return_value = {"SUCCESS": 25, "NOTICE": 15}

        core_logger.add_custom_log_levels()

        self.assertEqual(logging.getLevelName(25), "SUCCESS")
        self.assertEqual(logging.getLevelName(15), "NOTICE")

    @patch("gt.core.logger.utils_system.get_maya_preferences_dir")
    @patch("os.makedirs")
    def test_get_logs_dir_creates_missing_directory(self, mock_makedirs, mock_get_maya_prefs_dir):
        mock_get_maya_prefs_dir.return_value = "C:/Users/Name/Documents/maya"
        core_logger.PACKAGE_LOGS_DIR = "logs"
        core_logger.core_setup.PACKAGE_NAME = "gt_tools"

        result = core_logger.get_logs_dir()

        expected_path = "C:\\Users\\Name\\Documents\\maya\\gt_tools\\logs"
        self.assertEqual(result, expected_path)
        mock_makedirs.assert_called_with(expected_path)

    @patch("gt.core.logger.get_logs_dir")
    def test_setup_common_logger_creates_file_handler(self, mock_get_logs_dir):
        mock_get_logs_dir.return_value = "C:/Users/Name/Documents/maya/gt_tools/logs"
        _logger = core_logger.setup_common_logger(name="test_logger", log_file_handler=False)

        self.assertIsInstance(_logger, logging.Logger)

    def test_get_logger_name_default_behavior(self):
        module_path = "gt.core.utils"
        core_logger.core_setup.PACKAGE_MAIN_MODULE = "gt"

        result = core_logger.get_logger_name(module_path, remove_package=True)
        expected = "core.utils"
        self.assertEqual(result, expected)

    def test_get_logger_name_with_depth(self):
        module_path = "gt.tools.auto_rigger.rig_utils"
        result = core_logger.get_logger_name(module_path, depth=2)

        expected = "tools.auto_rigger"
        self.assertEqual(result, expected)
