import os
import sys
import logging
import unittest

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
from gt.core import material as core_mat

cmds = maya_test_tools.cmds


class TestAttributeCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_common_material_types(self):
        attributes = vars(core_mat.CommonMaterials)
        keys = [attr for attr in attributes if not (attr.startswith("__") and attr.endswith("__"))]
        for mat_key in keys:
            material = getattr(core_mat.CommonMaterials, mat_key)
            if not material:
                raise Exception(f"Missing material: {mat_key}")
            if not isinstance(material, str):
                raise Exception(f'Incorrect material type. Expected str, but got: "{type(material)}".')

    def test_get_all_materials(self):
        result = core_mat.get_all_materials(material_types=core_mat.CommonMaterials.lambert)
        expected = ["lambert1"]
        self.assertEqual(expected, result)

        cube = maya_test_tools.create_poly_cube()
        core_mat.assign_material(obj_list=cube, rgb_color=(1, 0, 0), material_name="M_mocked")

        result = core_mat.get_all_materials(material_types=core_mat.CommonMaterials.lambert)
        expected = ["M_mocked", "lambert1"]
        self.assertEqual(sorted(expected), sorted(result))

    def test_material_exists(self):
        result = core_mat.material_exists(material_name="lambert1")
        expected = True
        self.assertEqual(expected, result)

        result = core_mat.material_exists(material_name="M_mocked")
        expected = False
        self.assertEqual(expected, result)

        cube = maya_test_tools.create_poly_cube()
        core_mat.assign_material(obj_list=cube, rgb_color=(1, 0, 0), material_name="M_mocked")

        result = core_mat.material_exists(material_name="M_mocked")
        expected = True
        self.assertEqual(expected, result)

    def test_get_shading_engine(self):
        result = core_mat.get_shading_engine(material_name="lambert1")
        expected = "initialParticleSE"
        self.assertEqual(expected, result)

        cube = maya_test_tools.create_poly_cube()
        core_mat.assign_material(obj_list=cube, rgb_color=(1, 0, 0), material_name="M_mocked")

        result = core_mat.get_shading_engine(material_name="M_mocked")
        expected = "M_mockedSG"
        self.assertEqual(expected, result)

    def test_assign_material(self):
        cube = maya_test_tools.create_poly_cube()

        result = core_mat.assign_material(obj_list=cube, rgb_color=(1, 0, 0), material_name="M_mocked")
        expected = "M_mocked"
        self.assertEqual(expected, result)

        color_result = cmds.getAttr(f"{result}.color")[0]
        color_expected = (1, 0, 0)
        self.assertEqual(color_expected, color_result)

    def test_assign_material_type(self):
        cube = maya_test_tools.create_poly_cube()

        result = core_mat.assign_material(
            obj_list=cube, rgb_color=(1, 1, 0), material_type=core_mat.CommonMaterials.blinn
        )
        expected = "MAT_blinn"
        self.assertEqual(expected, result)

        color_result = cmds.getAttr(f"{result}.color")[0]
        color_expected = (1, 1, 0)
        self.assertEqual(color_expected, color_result)
