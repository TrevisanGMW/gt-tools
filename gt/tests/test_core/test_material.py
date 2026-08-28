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
        cube_one = maya_test_tools.create_poly_cube()
        default_lambert = "lambert1"
        core_mat.assign_material(obj_list=cube_one, rgb_color=(1, 0, 0), material_name=default_lambert, is_unique=True)
        result = core_mat.get_shading_engine(material_name=default_lambert)
        expected = f"{default_lambert}SG"
        self.assertEqual(expected, result)

        cube_two = maya_test_tools.create_poly_cube()
        mocked_material = "M_mocked"
        core_mat.assign_material(obj_list=cube_two, rgb_color=(1, 0, 0), material_name=mocked_material)

        result = core_mat.get_shading_engine(material_name=mocked_material)
        expected = f"{mocked_material}SG"
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
        expected = "M_blinn"
        self.assertEqual(expected, result)

        color_result = cmds.getAttr(f"{result}.color")[0]
        color_expected = (1, 1, 0)
        self.assertEqual(color_expected, color_result)

    # ------------------------------------ Component Material Transfer ------------------------------------
    @staticmethod
    def create_two_material_cube(name="source_cube"):
        """
        Creates a poly cube with "M_red" assigned to the first three faces and "M_blue" to the last three.

        Args:
            name (str, optional): Name of the created cube.

        Returns:
            str: Name of the created cube transform.
        """
        cube = maya_test_tools.create_poly_cube(name=name, constructionHistory=False)
        core_mat.assign_material(obj_list=[f"{cube}.f[0:2]"], rgb_color=(1, 0, 0), material_name="M_red")
        core_mat.assign_material(obj_list=[f"{cube}.f[3:5]"], rgb_color=(0, 0, 1), material_name="M_blue")
        return cube

    @staticmethod
    def get_face_materials(mesh):
        """
        Retrieves the material assigned to each face of a mesh.

        Args:
            mesh (str): Mesh transform, shape or component string.

        Returns:
            list: Material name per face (None when a face has no material).
        """
        shading_engines, face_slots = core_mat.get_face_shading_engines(mesh)
        materials = []
        for slot in face_slots:
            if slot < 0:
                materials.append(None)
                continue
            materials.append(core_mat.get_material_from_shading_engine(shading_engines[slot]))
        return materials

    def test_get_index_ranges(self):
        result = core_mat._get_index_ranges([12, 0, 1, 2, 8, 7])
        expected = [(0, 2), (7, 8), (12, 12)]
        self.assertEqual(expected, result)

    def test_compress_face_indices(self):
        result = core_mat._compress_face_indices("mocked_shape", [0, 1, 2, 7])
        expected = ["mocked_shape.f[0:2]", "mocked_shape.f[7]"]
        self.assertEqual(expected, result)

    def test_build_position_hash(self):
        positions = [(0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (10.0, 0.0, 0.0)]
        result = core_mat._build_position_hash(positions, cell_size=1.0)
        expected = {(0, 0, 0): [0, 1], (10, 0, 0): [2]}
        self.assertEqual(expected, result)

    def test_find_closest_position_index(self):
        positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
        position_hash = core_mat._build_position_hash(positions, cell_size=1.0)

        result = core_mat._find_closest_position_index(
            position=(1.0001, 0.0, 0.0),
            positions=positions,
            position_hash=position_hash,
            cell_size=1.0,
            tolerance=1.0,
        )
        expected = 1
        self.assertEqual(expected, result)

    def test_find_closest_position_index_out_of_tolerance(self):
        positions = [(0.0, 0.0, 0.0)]
        position_hash = core_mat._build_position_hash(positions, cell_size=0.001)

        result = core_mat._find_closest_position_index(
            position=(5.0, 0.0, 0.0),
            positions=positions,
            position_hash=position_hash,
            cell_size=0.001,
            tolerance=0.001,
        )
        expected = None
        self.assertEqual(expected, result)

    def test_find_closest_position_index_without_tolerance(self):
        positions = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
        position_hash = core_mat._build_position_hash(positions, cell_size=1.0)
        cell_bounds = core_mat._get_hash_cell_bounds(position_hash)

        result = core_mat._find_closest_position_index(
            position=(7.0, 0.0, 0.0),
            positions=positions,
            position_hash=position_hash,
            cell_size=1.0,
            tolerance=None,
            cell_bounds=cell_bounds,
        )
        expected = 1
        self.assertEqual(expected, result)

    def test_get_hash_cell_bounds(self):
        positions = [(0.0, 0.0, 0.0), (2.5, -1.5, 0.0)]
        position_hash = core_mat._build_position_hash(positions, cell_size=1.0)

        result = core_mat._get_hash_cell_bounds(position_hash)
        expected = ((0, -2, 0), (2, 0, 0))
        self.assertEqual(expected, result)

        result = core_mat._get_hash_cell_bounds({})
        expected = None
        self.assertEqual(expected, result)

    def test_get_cell_shell_keys(self):
        result = core_mat._get_cell_shell_keys((0, 0, 0), radius=0)
        expected = [(0, 0, 0)]
        self.assertEqual(expected, result)

        result = core_mat._get_cell_shell_keys((0, 0, 0), radius=1)
        expected = 26  # A 3x3x3 box without its center
        self.assertEqual(expected, len(result))
        self.assertNotIn((0, 0, 0), result)

    def test_get_cell_shell_keys_bounded(self):
        # The shell is clipped to the populated area, so far away cells are not visited
        result = core_mat._get_cell_shell_keys((10, 0, 0), radius=9, cell_bounds=((0, 0, 0), (1, 0, 0)))
        expected = [(1, 0, 0)]
        self.assertEqual(expected, result)

    def test_get_search_radius_range(self):
        # Base cell inside the populated area
        result = core_mat._get_search_radius_range((0, 0, 0), cell_bounds=((-3, 0, 0), (1, 0, 0)))
        expected = (0, 3)
        self.assertEqual(expected, result)

        # Base cell far away from the populated area, so the empty shells are skipped
        result = core_mat._get_search_radius_range((100, 0, 0), cell_bounds=((0, 0, 0), (2, 0, 0)))
        expected = (98, 100)
        self.assertEqual(expected, result)

        result = core_mat._get_search_radius_range((0, 0, 0), cell_bounds=None)
        expected = (0, 1)
        self.assertEqual(expected, result)

    def test_estimate_cell_size(self):
        result = core_mat._estimate_cell_size([], minimum_cell_size=0.05)
        expected = 0.05
        self.assertEqual(expected, result)

        # Every position sits in the same spot, so the minimum size is used
        result = core_mat._estimate_cell_size([(1.0, 1.0, 1.0)] * 8, minimum_cell_size=0.01)
        expected = 0.01
        self.assertEqual(expected, result)

        # Ten positions spread over nine units. Two divisions per axis means 4.5 units per cell
        positions = [(value, 0.0, 0.0) for value in range(0, 10)]
        result = core_mat._estimate_cell_size(positions, minimum_cell_size=0.001)
        expected = 4.5
        self.assertAlmostEqual(expected, result, places=5)

    def test_get_mesh_shape(self):
        cube = maya_test_tools.create_poly_cube(name="mocked_cube", constructionHistory=False)
        expected = cmds.listRelatives(cube, shapes=True, fullPath=True)[0]

        self.assertEqual(expected, core_mat.get_mesh_shape(cube))
        self.assertEqual(expected, core_mat.get_mesh_shape(f"{cube}.f[0]"))
        self.assertEqual(expected, core_mat.get_mesh_shape(expected))
        self.assertEqual(None, core_mat.get_mesh_shape("mocked_missing_object"))

    def test_get_selected_face_indices(self):
        cube = maya_test_tools.create_poly_cube(name="mocked_cube", constructionHistory=False)
        shape = cmds.listRelatives(cube, shapes=True, fullPath=True)[0]

        result = core_mat.get_selected_face_indices([f"{cube}.f[0:2]", f"{cube}.f[5]"])
        expected = {shape: [0, 1, 2, 5]}
        self.assertEqual(expected, result)

        result = core_mat.get_selected_face_indices([cube])
        expected = {}
        self.assertEqual(expected, result)

    def test_get_face_shading_engines(self):
        cube = self.create_two_material_cube()

        shading_engines, face_slots = core_mat.get_face_shading_engines(cube)
        expected_engines = ["M_blueSG", "M_redSG"]
        self.assertEqual(expected_engines, sorted(shading_engines))

        expected_materials = ["M_red", "M_red", "M_red", "M_blue", "M_blue", "M_blue"]
        self.assertEqual(expected_materials, self.get_face_materials(cube))
        self.assertEqual(6, len(face_slots))

    def test_get_face_centers(self):
        cube = maya_test_tools.create_poly_cube(name="mocked_cube", constructionHistory=False)
        cmds.setAttr(f"{cube}.translateX", 10)

        object_centers = core_mat.get_face_centers(cube, space=core_mat.ComponentSpace.object_space)
        expected_quantity = 6
        self.assertEqual(expected_quantity, len(object_centers))
        self.assertAlmostEqual(0.0, object_centers[0][0], places=5)
        self.assertAlmostEqual(0.5, object_centers[0][2], places=5)

        world_centers = core_mat.get_face_centers(cube, space=core_mat.ComponentSpace.world)
        self.assertAlmostEqual(10.0, world_centers[0][0], places=5)

    def test_copy_component_materials(self):
        cube = self.create_two_material_cube()

        result = core_mat.copy_component_materials(source=cube, verbose=False)
        expected_faces = [0, 1, 2, 3, 4, 5]
        self.assertEqual(expected_faces, result.get("faces"))
        expected_materials = ["M_blue", "M_red"]
        self.assertEqual(expected_materials, sorted(item for item in result.get("materials") if item))
        self.assertEqual(6, len(result.get("face_centers_object")))
        self.assertEqual(6, len(result.get("face_centers_world")))
        self.assertEqual(result, core_mat.get_component_material_clipboard())

        core_mat.clear_component_material_clipboard()
        expected = {}
        self.assertEqual(expected, core_mat.get_component_material_clipboard())

    def test_copy_component_materials_face_indices(self):
        cube = self.create_two_material_cube()

        result = core_mat.copy_component_materials(source=cube, face_indices=[0, 4], verbose=False)
        expected_faces = [0, 4]
        self.assertEqual(expected_faces, result.get("faces"))

    def test_get_component_material_clipboard_summary(self):
        result = core_mat.get_component_material_clipboard_summary({})
        expected = "Clipboard is empty."
        self.assertEqual(expected, result)

        cube = self.create_two_material_cube()
        clipboard_data = core_mat.copy_component_materials(source=cube, verbose=False)
        result = core_mat.get_component_material_clipboard_summary(clipboard_data)
        expected = "source_cubeShape - 6 faces, 2 materials (M_blue, M_red)"
        self.assertEqual(expected, result)

    def test_paste_component_materials_by_index(self):
        source = self.create_two_material_cube()
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[target], match_by=core_mat.MaterialTransferMode.component_index, verbose=False
        )
        expected_assigned = 6
        self.assertEqual(expected_assigned, result.get("assigned"))
        expected_unmatched = 0
        self.assertEqual(expected_unmatched, result.get("unmatched"))

        expected_materials = ["M_red", "M_red", "M_red", "M_blue", "M_blue", "M_blue"]
        self.assertEqual(expected_materials, self.get_face_materials(target))

    def test_paste_component_materials_by_index_selected_faces(self):
        source = self.create_two_material_cube()
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[f"{target}.f[3:5]"],
            match_by=core_mat.MaterialTransferMode.component_index,
            verbose=False,
        )
        expected_assigned = 3
        self.assertEqual(expected_assigned, result.get("assigned"))

        default_material = core_mat.get_material_from_shading_engine("initialShadingGroup")
        expected_materials = [default_material] * 3 + ["M_blue", "M_blue", "M_blue"]
        self.assertEqual(expected_materials, self.get_face_materials(target))

    def test_paste_component_materials_by_position(self):
        source = self.create_two_material_cube()
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[target],
            match_by=core_mat.MaterialTransferMode.component_position,
            space=core_mat.ComponentSpace.object_space,
            verbose=False,
        )
        expected_assigned = 6
        self.assertEqual(expected_assigned, result.get("assigned"))

        expected_materials = ["M_red", "M_red", "M_red", "M_blue", "M_blue", "M_blue"]
        self.assertEqual(expected_materials, self.get_face_materials(target))

    def test_paste_component_materials_by_position_strict_tolerance(self):
        source = self.create_two_material_cube()
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)
        cmds.setAttr(f"{target}.translateX", 50)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[target],
            match_by=core_mat.MaterialTransferMode.component_position,
            space=core_mat.ComponentSpace.world,
            fallback_closest=False,
            verbose=False,
        )
        expected_assigned = 0
        self.assertEqual(expected_assigned, result.get("assigned"))
        expected_unmatched = 6
        self.assertEqual(expected_unmatched, result.get("unmatched"))

    def test_paste_component_materials_by_position_fallback_closest(self):
        source = self.create_two_material_cube()
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)
        cmds.setAttr(f"{target}.translateX", 50)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[target],
            match_by=core_mat.MaterialTransferMode.component_position,
            space=core_mat.ComponentSpace.world,
            verbose=False,
        )
        expected_assigned = 6
        self.assertEqual(expected_assigned, result.get("assigned"))
        expected_unmatched = 0
        self.assertEqual(expected_unmatched, result.get("unmatched"))
        expected_approximate = 6
        self.assertEqual(expected_approximate, result.get("approximate"))

        # Every face must end up with a material, none can be left without a shading engine
        self.assertNotIn(None, self.get_face_materials(target))

    def test_paste_component_materials_by_position_different_topology(self):
        source = maya_test_tools.create_poly_sphere(
            name="source_sphere", subdivisionsX=12, subdivisionsY=12, constructionHistory=False
        )
        source_face_count = cmds.polyEvaluate(source, face=True)
        half = source_face_count // 2
        core_mat.assign_material(
            obj_list=[f"{source}.f[0:{half - 1}]"], rgb_color=(1, 0, 0), material_name="M_red"
        )
        core_mat.assign_material(
            obj_list=[f"{source}.f[{half}:{source_face_count - 1}]"], rgb_color=(0, 0, 1), material_name="M_blue"
        )
        target = maya_test_tools.create_poly_sphere(
            name="target_sphere", subdivisionsX=16, subdivisionsY=16, constructionHistory=False
        )
        target_face_count = cmds.polyEvaluate(target, face=True)

        core_mat.copy_component_materials(source=source, verbose=False)
        result = core_mat.paste_component_materials(
            targets=[target],
            match_by=core_mat.MaterialTransferMode.component_position,
            space=core_mat.ComponentSpace.object_space,
            verbose=False,
        )
        expected_assigned = target_face_count
        self.assertEqual(expected_assigned, result.get("assigned"))
        expected_unmatched = 0
        self.assertEqual(expected_unmatched, result.get("unmatched"))

        target_materials = self.get_face_materials(target)
        self.assertNotIn(None, target_materials)
        expected_materials = ["M_blue", "M_red"]
        self.assertEqual(expected_materials, sorted(set(target_materials)))

    def test_paste_component_materials_empty_clipboard(self):
        target = maya_test_tools.create_poly_cube(name="target_cube", constructionHistory=False)
        core_mat.clear_component_material_clipboard()

        result = core_mat.paste_component_materials(targets=[target], verbose=False)
        expected = {"assigned": 0, "approximate": 0, "unmatched": 0, "targets": [], "skipped": []}
        self.assertEqual(expected, result)

    def test_assign_faces_to_shading_engine(self):
        cube = maya_test_tools.create_poly_cube(name="mocked_cube", constructionHistory=False)
        core_mat.assign_material(obj_list=[cube], rgb_color=(1, 0, 0), material_name="M_red")

        result = core_mat.assign_faces_to_shading_engine(
            shape=cube, face_indices=[0, 1], shading_engine="initialShadingGroup"
        )
        expected = 2
        self.assertEqual(expected, result)

        default_material = core_mat.get_material_from_shading_engine("initialShadingGroup")
        expected_materials = [default_material] * 2 + ["M_red"] * 4
        self.assertEqual(expected_materials, self.get_face_materials(cube))
