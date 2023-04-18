import os
import sys
import logging
import unittest
from collections import namedtuple

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_session_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
#from tools.validation import validation_cleanup

# class MayaSpoof:
#     def spaceLocator(self, *args, **kwargs):
#         logger.warning("spoofing menu")
#         return "nothing"
#
#
# try:
#     import maya.cmds as cmds
#     import maya.standalone
#     import maya.mel as mel
#     import maya.OpenMaya as OpenMaya
# except Exception as e:
#     logger.debug(str(e))
#     logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")
#     cmds = MayaSpoof()


class Test_SessionUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_validate_no_namespace_invalid(self):
        # File to Test - Invalid
        open_invalid_scene()

        # Run Validation
        response = validation_cleanup.validate_no_namespace()

        # Assert Results - Fail
        expected = ValidationResponse(passed=False,
                                      expected=[],
                                      result=['TestNS', 'TestNS2', 'TestNS2:TestNS3'],
                                      message="Namespaces were found in the scene: "
                                              "['TestNS', 'TestNS2', 'TestNS2:TestNS3'].")
        self.assertEqual(response, expected)

    def test_validate_no_namespace_valid(self):
        # File to Test - Valid
        open_valid_scene()

        # Run Validation
        response = validation_cleanup.validate_no_namespace()

        # Assert Results - Fail
        expected = ValidationResponse(passed=True,
                                      expected=[],
                                      result=[],
                                      message="No namespaces detected during validation.")
        self.assertEqual(response, expected)

    def test_validate_existing_elements_found(self):
        # File to Test
        open_valid_scene()
        # All found
        expected_objects = ["pCube1", "cn_root_jnt"]
        response = validation_cleanup.validate_existing_elements(expected_objects)
        expected = ValidationResponse(passed=True,
                                      expected=[],
                                      result=[],
                                      message="All expected elements were found in the scene.")
        self.assertEqual(response, expected)

    def test_validate_existing_elements_missing(self):
        # File to Test - Invalid Cubes
        open_valid_scene()
        # Missing Object
        expected_objects = ["pCube1", "cn_root_jnt", "missing_object"]
        response = validation_cleanup.validate_existing_elements(expected_objects)
        expected = ValidationResponse(passed=False,
                                      expected=[],
                                      result=["missing_object"],
                                      message="Missing expected elements: ['missing_object']")
        self.assertEqual(response, expected)

    def test_patch_delete_namespaces(self):
        # File to Test - Invalid Cubes
        open_invalid_scene()

        # Patch Scene
        result = validation_cleanup.patch_delete_namespaces()
        expected = 3
        self.assertEqual(result, expected)

    def test_get_namespaces(self):
        # File to Test - Invalid Cubes
        open_invalid_scene()

        result = validation_cleanup.get_namespaces(['TestNS:pCube1'])
        expected = ['TestNS']
        self.assertEqual(result, expected)

    def test_namespaces_split(self):
        # File to Test - Invalid Cubes
        open_invalid_scene()

        result = validation_cleanup.namespaces_split('TestNS:pCube1')
        expected = ('TestNS', 'pCube1')
        self.assertEqual(result, expected)

    def test_get_all_namespaces(self):
        # File to Test - Invalid Cubes
        open_invalid_scene()

        result = validation_cleanup.get_all_namespaces()
        expected = ['TestNS', 'TestNS2', 'TestNS2:TestNS3']
        self.assertEqual(result, expected)

    def test_strip_namespace(self):
        # File to Test - Invalid Cubes
        open_invalid_scene()
        # Full object name is "TestNS2:TestNS3:pCube1"
        with validation_cleanup.StripNamespace('TestNS2:TestNS3:') as stripped_nodes:
            result = cmds.ls(stripped_nodes)
            expected = ['pCube1']
            self.assertEqual(result, expected)
