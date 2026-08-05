import os
import sys
import logging
import unittest
import maya.cmds as cmds
from gt.tests import maya_test_tools
import gt.core.blendshape as core_bs

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


class TestBlendshapeCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_blendshape(self):
        cube = maya_test_tools.create_poly_cube(name="cube")
        cmds.blendShape(cube, n=f"test_blendshape")
        result = core_bs.get_blendshape_node_from_target(cube)
        expected = ["test_blendshape"]
        self.assertEqual(expected, result)

    def test_get_targets(self):
        cube = maya_test_tools.create_poly_cube(name="cube")
        test_bs = cmds.blendShape(cube, n=f"test_blendshape")[0]
        cube_target = maya_test_tools.create_poly_cube(n="cube_target")
        cmds.blendShape(test_bs, e=True, t=(cube, 0, cube_target, 1))
        expected = ["cube_target"]
        result = core_bs.get_targets(test_bs)
        self.assertEqual(expected, result)

    def test_extract_geo(self):
        cube = maya_test_tools.create_poly_cube(name="cube")
        test_bs = cmds.blendShape(cube, n=f"test_blendshape")[0]
        cube_target = maya_test_tools.create_poly_cube(n="cube_target_geo")
        cmds.blendShape(test_bs, e=True, t=(cube, 0, cube_target, 1))
        cmds.delete(cube_target)
        result = core_bs.extract_geo_from_targets(cube)
        expected = ["cube_target_geo"]
        self.assertEqual(expected, result)

    def test_transfer_bs_to_new_mesh(self):
        cube = maya_test_tools.create_poly_cube(name="cube")
        test_bs = cmds.blendShape(cube, n=f"test_blendshape")[0]
        cube_target = maya_test_tools.create_poly_cube(n="cube_target_geo")
        cmds.blendShape(test_bs, e=True, t=(cube, 0, cube_target, 1))
        cmds.delete(cube_target)
        new_cube_mesh = maya_test_tools.create_poly_cube(n="cube_target_new_mesh")
        core_bs.transfer_blendshapes_to_target(cube, new_cube_mesh)
        result_1 = core_bs.get_blendshape_node_from_target(new_cube_mesh)
        expected = ["BS_cube_target_new_mesh"]
        self.assertEqual(expected, result_1)
        result_2 = core_bs.get_targets(result_1[0])
        expected = ["cube_target_geo"]
        self.assertEqual(expected, result_2)
