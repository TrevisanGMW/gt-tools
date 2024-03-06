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

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils import uuid_utils
cmds = maya_test_tools.cmds


class TestUUIDUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_generate_uuid_no_conflicting(self):
        uuids = set()
        counter = 0
        for index in range(0, 10000):
            uuids.add(uuid_utils.generate_uuid())
            counter += 1
        self.assertEqual(counter, len(uuids))

    def test_normal_uuid_generation(self):
        result = uuid_utils.generate_uuid()
        expected_length = 36
        expected = isinstance(result, str) and len(result) == expected_length
        self.assertTrue(expected)

    def test_short_uuid_generation(self):
        expected_length = 8
        result = uuid_utils.generate_uuid(short=True)
        expected = isinstance(result, str) and len(result) == expected_length
        self.assertTrue(expected)

    def test_short_uuid_generation_custom_length(self):
        custom_length = 6
        result = uuid_utils.generate_uuid(short=True, short_length=custom_length)
        expected = isinstance(result, str) and len(result) == custom_length
        self.assertTrue(expected)

    def test_short_uuid_invalid_length(self):
        with self.assertRaises(ValueError):
            uuid_utils.generate_uuid(short=True, short_length=-1)

    def test_remove_dashes(self):
        result = uuid_utils.generate_uuid(remove_dashes=True)
        expected_length = 32
        self.assertTrue(isinstance(result, str))
        self.assertTrue(len(result) == expected_length)

    def test_generate_uuid_no_conflicting_short(self):
        uuids = set()
        counter = 0
        for index in range(0, 1000):
            uuids.add(uuid_utils.generate_uuid(short=True, short_length=12))
            counter += 1
        self.assertEqual(counter, len(uuids))

    def test_valid_uuid(self):
        valid_uuid = "123e4567-e89b-12d3-a456-426655440000"
        self.assertTrue(uuid_utils.is_uuid_valid(valid_uuid))

    def test_valid_uuid_no_dashes(self):
        valid_uuid = "123e4567e89b12d3a456426655440000"
        self.assertTrue(uuid_utils.is_uuid_valid(valid_uuid))

    def test_invalid_uuid(self):
        invalid_uuid = "not-a-uuid"
        self.assertFalse(uuid_utils.is_uuid_valid(invalid_uuid))

    def test_invalid_uuid_close(self):
        valid_uuid = "123e4567-e89b-12d3-a456-42665544000"
        self.assertFalse(uuid_utils.is_uuid_valid(valid_uuid))

    def test_valid_short_uuid(self):
        uuid = "abc123"
        result = uuid_utils.is_short_uuid_valid(uuid)
        self.assertTrue(result)

    def test_valid_short_uuid_with_length(self):
        uuid = "abc123"
        length = 6
        result = uuid_utils.is_short_uuid_valid(uuid, length=length)
        self.assertTrue(result)

    def test_invalid_short_uuid_characters(self):
        uuid = "abc@123"
        result = uuid_utils.is_short_uuid_valid(uuid)
        self.assertFalse(result)

    def test_invalid_short_uuid_length(self):
        uuid = "abc123"
        length = 7
        result = uuid_utils.is_short_uuid_valid(uuid, length=length)
        self.assertFalse(result)

    def test_invalid_short_uuid_and_length(self):
        uuid = "abc@123"
        length = 6
        result = uuid_utils.is_short_uuid_valid(uuid, length=length)
        self.assertFalse(result)

    def test_empty_uuid(self):
        uuid = ""
        result = uuid_utils.is_short_uuid_valid(uuid)
        self.assertFalse(result)

    def test_add_proxy_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        attr_name = "mockedAttrName"
        result = uuid_utils.add_uuid_attr(cube, attr_name)
        expected = [f'{cube}.{attr_name}']
        self.assertEqual(expected, result)

    def test_add_proxy_attribute_multiple_objects(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        attr_name = "mockedAttrName"
        result = uuid_utils.add_uuid_attr([cube_one, cube_two], attr_name)
        expected = [f'{cube_one}.{attr_name}', f'{cube_two}.{attr_name}']
        self.assertEqual(expected, result)

    def test_invalid_object_list_input(self):
        obj_list = 123  # Invalid input
        proxy_attrs = uuid_utils.add_uuid_attr(obj_list, 'mockedAttrName')
        expected = []
        self.assertEqual(proxy_attrs, expected)

    def test_invalid_attribute_name(self):
        objects = ['object1', 'object2']
        proxy_attrs = uuid_utils.add_uuid_attr(objects, None)  # Invalid attribute name
        expected = []
        self.assertEqual(proxy_attrs, expected)

    @patch('gt.utils.uuid_utils.add_attr')
    @patch('gt.utils.uuid_utils.set_attr')
    @patch('gt.utils.uuid_utils.generate_uuid')
    def test_initial_uuid_generation(self, mock_generate_uuid, mock_set_attr, mock_add_attr):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        mock_generate_uuid.return_value = 'mocked_uuid'
        mock_add_attr.return_value = [f'{cube_one}.mockedAttrName', f'{cube_two}.mockedAttrName']

        objects = [cube_one, cube_two]
        proxy_attrs = uuid_utils.add_uuid_attr(objects, 'mockedAttrName', set_initial_uuid_value=True)

        expected = [f'{cube_one}.mockedAttrName', f'{cube_two}.mockedAttrName']
        self.assertEqual(proxy_attrs, expected)

        mock_generate_uuid.assert_called()
        mock_set_attr.assert_called()

    def test_find_object_with_uuid(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        maya_test_tools.create_poly_cube()
        attr_name = "mockedAttrName"
        created_uuid_attr = uuid_utils.add_uuid_attr([cube_one, cube_two], attr_name)
        cmds.setAttr(created_uuid_attr[0], "mocked_uuid_value", typ="string")
        cmds.setAttr(created_uuid_attr[1], "mocked_uuid_value_two", typ="string")
        result = uuid_utils.get_object_from_uuid_attr(uuid_string="mocked_uuid_value", attr_name="mockedAttrName")
        expected = "|pCube1"
        self.assertEqual(expected, result)

    def test_get_uuid(self):
        cube = maya_test_tools.create_poly_cube()

        result = uuid_utils.get_uuid(cube)
        expected = cmds.ls(cube, uuid=True)[0]
        self.assertEqual(expected, result)

    def test_get_object_from_uuid(self):
        cube = maya_test_tools.create_poly_cube()

        _uuid = cmds.ls(cube, uuid=True)[0]
        result = uuid_utils.get_object_from_uuid(_uuid)
        expected = cmds.ls(cube, long=True)[0]
        self.assertEqual(expected, result)
