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
from tests import maya_test_tools
from gt.utils import mesh_utils


class TestMeshUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        data_dir = maya_test_tools.get_data_dir_path()
        self.triangle_file_path = os.path.join(data_dir, "triangle_mesh.obj")
        self.temp_dir = maya_test_tools.generate_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_get_mesh_path(self):
        from gt.utils.data_utils import DataDirConstants
        result = mesh_utils.get_mesh_file_path("qr_code_package_github")
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
        result = mesh_file.get_name()
        self.assertEqual(expected, result)

    def test_mesh_file_get_name(self):
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=None)
        expected = "triangle_mesh"
        result = mesh_file.get_name()
        self.assertEqual(expected, result)

    def test_mesh_file_is_valid(self):
        mesh_file = mesh_utils.MeshFile(file_path=self.triangle_file_path, metadata=None)
        self.assertTrue(mesh_file.is_valid())
        mesh_file.file_path = "mocked_path"
        self.assertFalse(mesh_file.is_valid())

    def test_mesh_file_fail_init(self):
        logging.disable(logging.WARNING)
        mesh_file = mesh_utils.MeshFile(file_path="mocked_path", metadata=None)
        self.assertFalse(mesh_file.is_valid())
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

    def test_get_curve_preview_image_path(self):
        path = mesh_utils.get_mesh_preview_image_path("qr_code_package_github")
        result = os.path.exists(path)
        self.assertTrue(result)
        result = os.path.basename(path)
        expected = "qr_code_package_github.jpg"
        self.assertEqual(expected, result)

    def test_export_obj_file(self):
        export_path = os.path.join(self.temp_dir, "my_file.obj")
        cube = maya_test_tools.create_poly_cube()
        result = mesh_utils.export_obj_file(export_path=export_path, obj_names=cube)
        return
        self.assertTrue(os.path.exists(result))
        self.assertEqual(export_path, result)
        exported_files = os.listdir(self.temp_dir)
        expected_files = ['my_file.mtl', 'my_file.obj']
        self.assertEqual(expected_files, exported_files)
        maya_test_tools.force_new_scene()
        imported = maya_test_tools.import_file(export_path)
        expected = ['groupId1',
                    'initialShadingGroup1',
                    'materialInfo1',
                    'my_file_initialShadingGroup',
                    '|Mesh',
                    '|Mesh|MeshShape']
        self.assertEqual(expected, imported)

    def test_export_obj_file_options(self):
        export_path = os.path.join(self.temp_dir, "my_file.obj")
        cube = maya_test_tools.create_poly_cube()
        options = "groups=0;materials=0;smoothing=0;normals=0"
        result = mesh_utils.export_obj_file(export_path=export_path, obj_names=cube, options=options)
        self.assertTrue(os.path.exists(result))
        self.assertEqual(export_path, result)
        exported_files = os.listdir(self.temp_dir)
        expected_files = ['my_file.obj']
        self.assertEqual(expected_files, exported_files)
        maya_test_tools.force_new_scene()
        imported = maya_test_tools.import_file(export_path)
        expected = ['|Mesh', '|Mesh|MeshShape']
        self.assertEqual(expected, imported)

    def test_is_face_string_valid_strings(self):
        """
        Test cases for valid input strings.

        Each input string in the 'valid_strings' list is expected to match the pattern.
        """
        valid_strings = [
            "pTorus1.f[132]",
            "someName.f[0]",
            "obj.f[1234556]",
            "abc.f[5678]",
            "NS:something|something_else.f[5678]",
            "a.f[5678]",
            "pCube1.f[12345678901234568]",
        ]
        for input_str in valid_strings:
            with self.subTest(input_str=input_str):
                self.assertTrue(mesh_utils.is_face_string(input_str), f"Expected {input_str} to be valid")

    def test_is_face_string_invalid_strings(self):
        """
        Test cases for invalid input strings.

        Each input string in the 'invalid_strings' list is expected NOT to match the pattern.
        """
        invalid_strings = [
            ".e[0]",
            "someName.vtx[0]",
            "someName.e[0]",
            "someName[0]",
            "someName",
            "anything.e[word]",
            "e[123]",
            "1e[456]",
            "somethingElse",
            "|name",
            "NS:something|something_else.vty[]",
        ]
        for input_str in invalid_strings:
            with self.subTest(input_str=input_str):
                self.assertFalse(mesh_utils.is_face_string(input_str), f"Expected {input_str} to be invalid")

    def test_is_edge_string_valid_strings(self):
        """
        Test cases for valid input strings.

        Each input string in the 'valid_strings' list is expected to match the pattern.
        """
        valid_strings = [
            "pTorus1.e[132]",
            "someName.e[0]",
            "obj.e[1234556]",
            "abc.e[5678]",
            "NS:something|something_else.e[5678]",
            "a.e[5678]",
            "pCube1.e[12345678901234568]",
        ]
        for input_str in valid_strings:
            with self.subTest(input_str=input_str):
                self.assertTrue(mesh_utils.is_edge_string(input_str), f"Expected {input_str} to be valid")

    def test_is_edge_string_invalid_strings(self):
        """
        Test cases for invalid input strings.

        Each input string in the 'invalid_strings' list is expected NOT to match the pattern.
        """
        invalid_strings = [
            ".e[0]",
            "someName.vtx[0]",
            "someName.f[0]",
            "someName[0]",
            "someName",
            "anything.e[word]",
            "e[123]",
            "1e[456]",
            "somethingElse",
            "|name",
            "NS:something|something_else.e[]",
        ]
        for input_str in invalid_strings:
            with self.subTest(input_str=input_str):
                self.assertFalse(mesh_utils.is_edge_string(input_str), f"Expected {input_str} to be invalid")

    def test_is_vertex_string_valid_strings(self):
        """
        Test cases for valid input strings.

        Each input string in the 'valid_strings' list is expected to match the pattern.
        """
        valid_strings = [
            "pTorus1.vtx[132]",
            "someName.vtx[0]",
            "obj.vtx[1234556]",
            "abc.vtx[5678]",
            "NS:something|something_else.vtx[5678]",
            "a.vtx[5678]",
            "pCube1.vtx[12345678901234568]",
        ]
        for input_str in valid_strings:
            with self.subTest(input_str=input_str):
                self.assertTrue(mesh_utils.is_vertex_string(input_str), f"Expected {input_str} to be valid")

    def test_is_vertex_string_invalid_strings(self):
        """
        Test cases for invalid input strings.

        Each input string in the 'invalid_strings' list is expected NOT to match the pattern.
        """
        invalid_strings = [
            ".e[0]",
            "someName.f[0]",
            "someName.e[0]",
            "someName[0]",
            "someName",
            "anything.e[word]",
            "e[123]",
            "1e[456]",
            "somethingElse",
            "|name",
            "NS:something|something_else.vty[]",
        ]
        for input_str in invalid_strings:
            with self.subTest(input_str=input_str):
                self.assertFalse(mesh_utils.is_vertex_string(input_str), f"Expected {input_str} to be invalid")

    def test_extract_components_from_face(self):
        cube = maya_test_tools.create_poly_cube()
        result = mesh_utils.extract_components_from_face(f'{cube}.f[0]')
        expected = ("FaceComponents(vertices=['pCube1.vtx[0]', 'pCube1.vtx[1]', 'pCube1.vtx[2]', "
                    "'pCube1.vtx[3]'], edges=['pCube1.e[0]', 'pCube1.e[1]', 'pCube1.e[4]', 'pCube1.e[5]'])")
        self.assertEqual(expected, str(result))
