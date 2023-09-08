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
        data_dir = maya_test_tools.get_data_dir_path()
        self.triangle_file_path = os.path.join(data_dir, "triangle_mesh.obj")

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
        result = mesh_utils.import_obj_file(self.triangle_file_path)
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

    def test_get_vertices_triangle(self):
        mesh_utils.import_obj_file(self.triangle_file_path)
        result = mesh_utils.get_vertices("|triangle")
        expected = ['triangle.vtx[0]', 'triangle.vtx[1]', 'triangle.vtx[2]']
        self.assertEqual(expected, result)

    def test_mesh_file_init(self):
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=None)
        self.assertEqual(self.triangle_file_path, mesh_file.file_path)
        self.assertEqual(None, mesh_file.metadata)
        self.assertEqual(None, mesh_file.get_metadata())

    def test_mesh_file_get_file_name_without_extension(self):
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=None)
        result = mesh_file.get_file_name_without_extension()
        expected = "triangle_mesh"
        self.assertEqual(expected, result)

    def test_mesh_file_is_valid(self):
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=None)
        self.assertTrue(mesh_file.is_file_valid())
        mesh_file.file_path = "mocked_path"
        self.assertFalse(mesh_file.is_file_valid())

    def test_mesh_file_fail_init(self):
        logging.disable(logging.WARNING)
        mesh_file = mesh_utils.MeshFile(file_path="mocked_path", metadata=None)
        self.assertFalse(mesh_file.is_file_valid())
        logging.disable(logging.NOTSET)

    def test_mesh_file_metadata(self):
        mocked_metadata = {"key": "value"}
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=mocked_metadata)
        self.assertEqual(mocked_metadata, mesh_file.metadata)
        self.assertEqual(mocked_metadata, mesh_file.get_metadata())
        mesh_file.add_to_metadata(key="key_two", value="value_true")
        expected = {"key": "value", "key_two": "value_true"}
        self.assertEqual(expected, mesh_file.get_metadata())
        mesh_file.set_metadata_dict(mocked_metadata)
        self.assertEqual(mocked_metadata, mesh_file.get_metadata())
