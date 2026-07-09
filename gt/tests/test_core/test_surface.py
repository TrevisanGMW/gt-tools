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
from gt.tests import maya_test_tools
from gt.core import surface as core_surface

cmds = maya_test_tools.cmds


class TestSurfaceCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_is_surface_true(self):
        sur = cmds.nurbsPlane(name="mocked_sur", constructionHistory=False)[0]
        sur_shape = cmds.listRelatives(sur, shapes=True)[0]
        result = core_surface.is_surface(surface=sur, consider_shape=True)
        expected = True
        self.assertEqual(expected, result)
        result = core_surface.is_surface(surface=sur_shape, consider_shape=True)
        expected = True
        self.assertEqual(expected, result)
        result = core_surface.is_surface(surface=sur_shape, consider_shape=False)
        expected = True
        self.assertEqual(expected, result)

    def test_is_surface_false(self):
        sur = cmds.nurbsPlane(name="mocked_sur", constructionHistory=False)[0]
        cube = maya_test_tools.create_poly_cube(name="mocked_polygon")
        result = core_surface.is_surface(surface=sur, consider_shape=False)
        expected = False
        self.assertEqual(expected, result)
        result = core_surface.is_surface(surface=cube, consider_shape=True)
        expected = False
        self.assertEqual(expected, result)

    def test_is_surface_periodic_false(self):
        sur = cmds.nurbsPlane(name="mocked_sur", constructionHistory=False)[0]
        sur_shape = cmds.listRelatives(sur, shapes=True)[0]
        result = core_surface.is_surface_periodic(surface_shape=sur_shape)
        expected = False

        self.assertEqual(expected, result)

    def test_is_surface_periodic_true(self):
        sur = cmds.sphere(name="mocked_sur", constructionHistory=False)[0]
        sur_shape = cmds.listRelatives(sur, shapes=True)[0]
        result = core_surface.is_surface_periodic(surface_shape=sur_shape)
        expected = True

        self.assertEqual(expected, result)

    def test_get_surface_function_set(self):
        sur = cmds.nurbsPlane(name="mocked_sur", constructionHistory=False)[0]
        surface_fn = core_surface.get_surface_function_set(surface=sur)
        import maya.OpenMaya as OpenMaya

        self.assertIsInstance(surface_fn, OpenMaya.MFnNurbsSurface)

    def test_create_surface_from_object_list(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        cmds.setAttr(f"{cube_two}.tx", 5)
        obj_list = [cube_one, cube_two]
        result = core_surface.create_surface_from_object_list(obj_list=obj_list)
        expected = "loftedSurface1"
        self.assertEqual(expected, result)
        result = core_surface.create_surface_from_object_list(obj_list=obj_list, surface_name="mocked_name")
        expected = "mocked_name"
        self.assertEqual(expected, result)

    def test_create_surface_from_object_list_degree(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        cmds.setAttr(f"{cube_two}.tx", 5)
        obj_list = [cube_one, cube_two]
        surface = core_surface.create_surface_from_object_list(obj_list=obj_list, degree=3, surface_name="cubic")
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")
        result = cmds.getAttr(f"{surface_shape[0]}.degreeUV")[0]
        expected = (3, 1)
        self.assertEqual(expected, result)
        surface = core_surface.create_surface_from_object_list(obj_list=obj_list, degree=1, surface_name="linear")
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")
        result = cmds.getAttr(f"{surface_shape[0]}.degreeUV")[0]
        expected = (1, 1)
        self.assertEqual(expected, result)

    def test_create_surface_from_object_list_custom_normal(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        cmds.setAttr(f"{cube_two}.tx", 5)
        obj_list = [cube_one, cube_two]
        sur = core_surface.create_surface_from_object_list(obj_list=obj_list)
        expected = "loftedSurface1"
        self.assertEqual(expected, sur)
        sur = core_surface.create_surface_from_object_list(
            obj_list=obj_list, surface_name="mocked_name", custom_normal=(0, 0, 1)
        )
        expected = "mocked_name"
        self.assertEqual(expected, sur)
        expected = [0.0, 2.0, 0.0]
        result = cmds.xform(f"{sur}.cv[0]", query=True, translation=True)
        self.assertEqual(expected, result)
        sur = core_surface.create_surface_from_object_list(
            obj_list=obj_list, surface_name="mocked_name_two", custom_normal=(0, 1, 0)
        )
        expected = [0.0, 0.0, -2.0]
        result = cmds.xform(f"{sur}.cv[0]", query=True, translation=True)
        self.assertEqual(expected, result)

    def test_multiply_surface_spans(self):
        surface = cmds.nurbsPlane(ch=False)[0]
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")
        result = cmds.getAttr(f"{surface_shape[0]}.spansUV")[0]
        expected = (1, 1)
        self.assertEqual(expected, result)
        core_surface.multiply_surface_spans(input_surface=surface, u_multiplier=2, v_multiplier=2)
        result = cmds.getAttr(f"{surface_shape[0]}.spansUV")[0]
        expected = (2, 2)
        self.assertEqual(expected, result)
        core_surface.multiply_surface_spans(input_surface=surface, u_multiplier=2, v_multiplier=2)
        result = cmds.getAttr(f"{surface_shape[0]}.spansUV")[0]
        expected = (4, 4)
        self.assertEqual(expected, result)

    def test_multiply_surface_spans_degrees(self):
        surface = cmds.nurbsPlane(ch=False)[0]
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")
        result = cmds.getAttr(f"{surface_shape[0]}.degreeUV")[0]
        expected = (3, 3)
        self.assertEqual(expected, result)
        core_surface.multiply_surface_spans(
            input_surface=surface, u_multiplier=2, v_multiplier=2, u_degree=3, v_degree=3
        )
        result = cmds.getAttr(f"{surface_shape[0]}.degreeUV")[0]
        expected = (3, 3)
        self.assertEqual(expected, result)
        core_surface.multiply_surface_spans(
            input_surface=surface, u_multiplier=2, v_multiplier=2, u_degree=1, v_degree=1
        )
        result = cmds.getAttr(f"{surface_shape[0]}.degreeUV")[0]
        expected = (1, 1)
        self.assertEqual(expected, result)

    def test_create_follicle(self):
        surface = cmds.nurbsPlane(ch=False)[0]
        follicle_tuple = core_surface.create_follicle(input_surface=surface, uv_position=(0.5, 0.5), name=None)
        _transform = follicle_tuple[0]
        _shape = follicle_tuple[1]
        expected_transform = "|follicle"
        expected_shape = "|follicle|follicleShape"
        self.assertEqual(expected_transform, str(_transform))
        self.assertEqual(expected_shape, str(_shape))
        result_u_pos = cmds.getAttr(f"{_shape}.parameterU")
        result_v_pos = cmds.getAttr(f"{_shape}.parameterV")
        expected_u_pos = 0.5
        expected_v_pos = 0.5
        self.assertEqual(expected_u_pos, result_u_pos)
        self.assertEqual(expected_v_pos, result_v_pos)

    def test_create_follicle_custom_uv_position_and_name(self):
        surface = cmds.nurbsPlane(ch=False)[0]
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")[0]
        follicle_tuple = core_surface.create_follicle(
            input_surface=surface_shape, uv_position=(0.3, 0.7), name="mocked_follicle"
        )
        _transform = follicle_tuple[0]
        _shape = follicle_tuple[1]
        expected_transform = "|mocked_follicle"
        expected_shape = "|mocked_follicle|mocked_follicleShape"
        self.assertEqual(expected_transform, str(_transform))
        self.assertEqual(expected_shape, str(_shape))
        result_u_pos = cmds.getAttr(f"{_shape}.parameterU")
        result_v_pos = cmds.getAttr(f"{_shape}.parameterV")
        expected_u_pos = 0.3
        expected_v_pos = 0.7
        self.assertEqual(expected_u_pos, result_u_pos)
        self.assertEqual(expected_v_pos, result_v_pos)

    def test_get_closest_uv_point(self):
        surface = cmds.nurbsPlane(ch=False, axis=(0, 1, 0))[0]
        surface_shape = cmds.listRelatives(surface, shapes=True, typ="nurbsSurface")[0]
        uv_coordinates = core_surface.get_closest_uv_point(surface=surface, xyz_pos=(0, 0, 0))
        expected = (0.5, 0.5)
        self.assertEqual(expected, uv_coordinates)

        uv_coordinates = core_surface.get_closest_uv_point(surface=surface_shape, xyz_pos=(0, 0, 0))
        expected = (0.5, 0.5)
        self.assertEqual(expected, uv_coordinates)

        uv_coordinates = core_surface.get_closest_uv_point(surface=surface_shape, xyz_pos=(0.1, 0, 0))
        expected = (0.6, 0.5)
        self.assertEqual(expected, uv_coordinates)
