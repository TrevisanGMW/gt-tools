import os
import sys
import logging
import unittest
from io import StringIO
from unittest.mock import patch

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
from gt.utils import attribute_utils


class TestAttributeUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_user_defined_attributes(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attribute_utils.delete_user_defined_attributes()
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = []
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_user_defined_attributes_no_locked(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attribute_utils.delete_user_defined_attributes(delete_locked=False)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = ['custom_attr_two']
        self.assertEqual(expected, result)
