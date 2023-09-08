import unittest
import logging
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
from gt.utils import mesh_utils


class TestMathUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_mesh_path(self):
        from gt.utils.data_utils import DataDirConstants
        result = mesh_utils.get_mesh_path("qr_code_package_github")
        expected = os.path.join(DataDirConstants.DIR_MESHES,
                                f"qr_code_package_github.{mesh_utils.MESH_FILE_EXTENSION}")
        self.assertEqual(expected, result)

    def test_import_obj_file(self):
        data_dir = maya_test_tools.get_data_dir_path()
        file_path = os.path.join(data_dir, "triangle_mesh.obj")
        result = mesh_utils.import_obj_file(file_path)
        expected = ['groupId1', 'lambert2SG', 'lambert2SG1', 'materialInfo1', '|triangle', '|triangle|triangleShape']
        self.assertEqual(expected, result)

    def test_get_vertices(self):
        cube = maya_test_tools.create_poly_cube()
        result = mesh_utils.get_vertices(cube)
        expected = ['pCube1.vtx[0]',
                    'pCube1.vtx[1]',
                    'pCube1.vtx[2]',
                    'pCube1.vtx[3]',
                    'pCube1.vtx[4]',
                    'pCube1.vtx[5]',
                    'pCube1.vtx[6]',
                    'pCube1.vtx[7]']
        self.assertEqual(expected, result)
