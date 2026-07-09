import logging
import os
import shutil
import sys
import tempfile
import unittest

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
from gt.tools.sample_tool import sample_model


class TestSampleToolModel(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gt_sample_tool_test_")
        self.model = sample_model.SampleToolModel()

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_text_to_file(self):
        file_path = os.path.join(self.temp_dir, "sample.txt")

        result = self.model.save_text_to_file("Hello Sample Tool", file_path)

        expected = True
        self.assertEqual(expected, result)
        with open(file_path, "r", encoding="utf-8") as saved_file:
            result = saved_file.read()
        expected = "Hello Sample Tool"
        self.assertEqual(expected, result)

    def test_save_text_to_file_fails_for_missing_directory(self):
        file_path = os.path.join(self.temp_dir, "missing", "sample.txt")

        result = self.model.save_text_to_file("Hello Sample Tool", file_path)

        expected = False
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
