from unittest.mock import patch, Mock
import unittest
import logging
import json
import stat
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils import data_utils


class TestDataUtils(unittest.TestCase):
    def setUp(self):
        self.mocked_str = "mocked_data"
        self.mocked_dict = {"mocked_key_a": "mocked_value_a",
                            "mocked_key_b": "mocked_value_b"}
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.file_path = os.path.join(self.temp_dir, "test_file.txt")
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)

    def tearDown(self):
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)
        maya_test_tools.delete_test_temp_dir()

    def create_temp_test_file(self):
        """
        Creates a test file and populates it with the variable "mocked_str"
        Returns:
            str: Path to the test file
        """
        with open(self.file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(self.mocked_str)
        return self.file_path

    def assert_file_content_equal(self, file_path, expected_content):
        """
        Asserts that the content of a file at the specified file path is equal to the expected content.

        Args:
            file_path (str): The path to the file whose content needs to be checked.
            expected_content (str): The expected content that the file should contain.

        Raises:
            AssertionError: If the content of the file does not match the expected content.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            self.assertEqual(content, expected_content)

    def assert_json_file_content_equal(self, file_path, expected_content):
        """
        Asserts that the content of a JSON file at the specified file path is equal to the expected content.

        Args:
            file_path (str): The path to the JSON file whose content needs to be checked.
            expected_content (dict or list): The expected JSON content that the file should contain.
                                            It can be either a dictionary or a list.

        Raises:
            AssertionError: If the content of the JSON file does not match the expected content.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                json_content = json.load(file)
            except json.JSONDecodeError:
                raise AssertionError(f"Invalid JSON file: {file_path}")
        self.assertEqual(json_content, expected_content)

    def test_write_data_return(self):
        data = self.mocked_str
        returned_path = data_utils.write_data(self.file_path, data)
        expected = self.file_path
        self.assertEqual(expected, returned_path)

    def test_write_data_missing_file(self):
        data = self.mocked_str
        logging.disable(logging.WARNING)
        returned_path = data_utils.write_data("mocked_non_existing_path/mocked_file.txt", data)
        logging.disable(logging.NOTSET)
        expected = None
        self.assertEqual(expected, returned_path)

    def test_write_data_content(self):
        data = self.mocked_str
        returned_path = data_utils.write_data(self.file_path, data)
        self.assert_file_content_equal(file_path=returned_path, expected_content=data)

    def test_read_data_content(self):
        data = self.mocked_str
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            data_file.write(data)  # Write Data to Temp File
        result = data_utils.read_data(self.file_path)  # Read Data from Temp File
        self.assertEqual(data, result)

    def test_read_data_content_missing_file(self):
        logging.disable(logging.WARNING)
        result = data_utils.read_data("mocked_non_existing_path/mocked_file.txt")
        logging.disable(logging.NOTSET)
        expected = None
        self.assertEqual(expected, result)

    def test_write_json_return(self):
        data = self.mocked_dict
        returned_path = data_utils.write_json(self.file_path, data)
        expected = self.file_path
        self.assertEqual(expected, returned_path)

    def test_write_json_missing_file(self):
        data = self.mocked_dict
        logging.disable(logging.WARNING)
        returned_path = data_utils.write_json("mocked_non_existing_path/mocked_file.txt", data)
        logging.disable(logging.NOTSET)
        expected = None
        self.assertEqual(expected, returned_path)

    def test_write_json_content(self):
        data = self.mocked_dict
        returned_path = data_utils.write_json(self.file_path, data)
        self.assert_json_file_content_equal(file_path=returned_path, expected_content=data)

    def test_read_json_content(self):
        data = self.mocked_dict
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        with open(self.file_path, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)  # Write JSON Data to Temp File
        result = data_utils.read_json_dict(self.file_path)  # Read JSON Data from Temp File
        self.assertEqual(data, result)

    def test_read_json_content_missing_file(self):
        logging.disable(logging.WARNING)
        result = data_utils.read_json_dict("mocked_non_existing_path/mocked_file.txt")
        logging.disable(logging.NOTSET)
        expected = {}
        self.assertEqual(expected, result)

    def test_set_file_permissions(self):
        test_file = self.create_temp_test_file()
        test_permission_bits = 438
        data_utils.set_file_permissions(test_file, data_utils.PermissionBits.ALL_PERMISSIONS)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode), test_permission_bits)

    def test_set_file_permissions_raises_error(self):
        # Test that FileNotFoundError is raised for non-existent file
        non_existent_file_path = "invalid_path/non_existent_file.txt"
        with self.assertRaises(FileNotFoundError):
            data_utils.set_file_permissions(non_existent_file_path, 0o755)

    def test_set_file_permission_read_only(self):
        test_file = self.create_temp_test_file()
        test_permission_bits = 292
        data_utils.set_file_permission_read_only(test_file)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode), test_permission_bits)

    def test_set_file_permission_modifiable(self):
        test_file = self.create_temp_test_file()
        test_permission_bits = 438
        data_utils.set_file_permission_modifiable(test_file)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode), test_permission_bits)

    def test_data_dir_constants(self):
        path_attributes = vars(data_utils.DataDirConstants)
        path_keys = [attr for attr in path_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for path_key in path_keys:
            path = getattr(data_utils.DataDirConstants, path_key)
            if not path:
                raise Exception(f'Missing constant data dir path: {path_key}')
            if not os.path.exists(path):
                raise Exception(f'Missing constant data dir path: {path_key}')

    def test_unzip_zip_file(self):
        extract_path = os.path.join(self.temp_dir, 'extracted')
        zip_file_path = os.path.join(maya_test_tools.get_data_dir_path(), "zip_file.zip")

        data_utils.unzip_zip_file(zip_file_path, extract_path)

        # Check if the extracted file exists
        self.assertTrue(os.path.exists(extract_path))
        result = os.listdir(extract_path)
        expected = ['script_01.py', 'text_01.txt', 'text_02.txt']
        self.assertEqual(expected, result)

        # Check if the content of the extracted file is correct
        extracted_script = os.path.join(extract_path, 'script_01.py')
        with open(extracted_script, 'rb') as extracted_file:
            content = extracted_file.read()
            expected = b'print("script")'
            self.assertEqual(expected, content)

    def test_unzip_zip_file_return(self):
        extract_path = os.path.join(self.temp_dir, 'extracted')
        zip_file_path = os.path.join(maya_test_tools.get_data_dir_path(), "zip_file.zip")

        result = data_utils.unzip_zip_file(zip_file_path, extract_path)

        # Check if the extracted file exists
        self.assertTrue(os.path.exists(extract_path))
        expected = [os.path.join(extract_path, file) for file in os.listdir(extract_path)]
        self.assertEqual(expected, result)

    def test_progress_callback(self):
        def progress_callback(current_file, total_files):
            self.assertTrue(current_file <= total_files)

        extract_path = os.path.join(self.temp_dir, 'extracted')
        zip_file_path = os.path.join(maya_test_tools.get_data_dir_path(), "zip_file.zip")
        data_utils.unzip_zip_file(zip_file_path, extract_path, progress_callback)

    def test_delete_files(self):
        # Create temporary files
        file1 = os.path.join(self.temp_dir, "test_file1.txt")
        file2 = os.path.join(self.temp_dir, "test_file2.txt")
        with open(file1, "w") as f1, open(file2, "w") as f2:
            f1.write("Test content")
            f2.write("Test content")

        paths_to_delete = [file1, file2]

        result = data_utils.delete_paths(paths_to_delete)

        self.assertTrue(result)
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))

    def test_delete_folders(self):
        # Create temporary folder
        folder = os.path.join(self.temp_dir, "test_folder")
        os.makedirs(folder)
        sub_folder = os.path.join(folder, "sub_folder")
        os.makedirs(sub_folder)

        paths_to_delete = [folder]

        result = data_utils.delete_paths(paths_to_delete)

        self.assertTrue(result)
        self.assertFalse(os.path.exists(folder))

    def test_delete_mixed_paths(self):
        # Create temporary files and folder
        file1 = os.path.join(self.temp_dir, "test_file1.txt")
        folder1 = os.path.join(self.temp_dir, "test_folder1")
        os.makedirs(folder1)
        sub_folder1 = os.path.join(folder1, "sub_folder")
        os.makedirs(sub_folder1)

        with open(file1, "w") as f1:
            f1.write("Test content")

        paths_to_delete = [file1, folder1]

        result = data_utils.delete_paths(paths_to_delete)

        self.assertTrue(result)
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(folder1))

    def test_nonexistent_paths(self):
        paths_to_delete = [
            "nonexistent_file.txt",
            "nonexistent_folder/"
        ]

        result = data_utils.delete_paths(paths_to_delete)
        self.assertTrue(result)

    def test_invalid_input(self):
        path_to_delete = "/path/to/delete/file.txt"
        logging.disable(logging.WARNING)
        result = data_utils.delete_paths(path_to_delete)
        logging.disable(logging.NOTSET)
        self.assertFalse(result)
