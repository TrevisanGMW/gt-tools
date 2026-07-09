from unittest.mock import patch
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
from gt.core import skin as core_skin

cmds = maya_test_tools.cmds


def import_skinned_test_file():
    """
    Import test plane skinned file from inside the .../data folder/<name>.ma
    """
    maya_test_tools.import_data_file("plane_skinned.ma")


def create_surface_test_scene():
    """
    Create a test NURBS surface bound to joints with a skin cluster.
    Returns the created surface, joints, and skinCluster.
    """
    # Create joints
    joint_one = cmds.joint(position=(0, 2.5, 0), name="joint_one")
    cmds.select(clear=True)
    joint_two = cmds.joint(position=(0, 0, 0), name="joint_two")
    cmds.select(clear=True)
    joint_three = cmds.joint(position=(0, -2.5, 0), name="joint_three")
    cmds.select(clear=True)
    joint_four = cmds.joint(position=(0, 0, -2.5), name="joint_four")

    # Create NURBS surface
    surface = cmds.nurbsPlane(
        pivot=[0, 0, 0],
        axis=[1, 0, 0],
        width=5,
        lengthRatio=1,
        degree=1,
        patchesU=1,
        patchesV=2,
        constructionHistory=False,
        name="surface_instance",
    )[0]

    # Bind surface to joints
    skin_cluster = cmds.skinCluster(joint_one, joint_two, joint_three, joint_four, surface, toSelectedBones=True)[0]

    skin_map = {
        f"{surface}.cv[0][2]": [(joint_one, 1.0), (joint_two, 0.0), (joint_three, 0.0)],  # Top Left
        f"{surface}.cv[1][2]": [(joint_one, 1.0), (joint_two, 0.0), (joint_three, 0.0)],  # Top Right
        f"{surface}.cv[0][1]": [(joint_one, 0.0), (joint_two, 1.0), (joint_three, 0.0)],  # Mid Left
        f"{surface}.cv[1][1]": [(joint_one, 0.0), (joint_two, 1.0), (joint_three, 0.0)],  # Mid Right
        f"{surface}.cv[0][0]": [(joint_one, 0.0), (joint_two, 0.0), (joint_three, 1.0)],  # Bottom Right
        f"{surface}.cv[1][0]": [(joint_one, 0.0), (joint_two, 0.0), (joint_three, 1.0)],
    }  # Bottom Left

    for cv, weight in skin_map.items():
        cmds.skinPercent(skin_cluster, cv, transformValue=weight)

    return surface, [joint_one, joint_two, joint_three], skin_cluster


class TestSkinCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        """
        Clean up the test scene after each test.
        """
        cmds.file(new=True, force=True)

    def assertDictAlmostEqual(self, dict1, dict2, delta=1e-6):
        """
        Custom assertion method to compare two dictionaries with float values.
        """
        self.assertEqual(set(dict1.keys()), set(dict2.keys()), "Dictionaries keys differ.")
        for key in dict1:
            self.assertAlmostEqual(dict1[key], dict2[key], delta=delta)

    def test_get_skin_cluster(self):
        import_skinned_test_file()
        result = core_skin.get_skin_cluster("plane")
        expected = "skinCluster1"
        self.assertEqual(expected, result)

    def test_get_skin_cluster_missing_item(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            core_skin.get_skin_cluster("mocked_missing_mesh")

    def test_get_influences(self):
        import_skinned_test_file()
        result = core_skin.get_influences("skinCluster1")
        expected = ["|root_jnt", "|root_jnt|mid_jnt", "|root_jnt|mid_jnt|end_jnt"]
        self.assertEqual(expected, result)

    def test_get_influences_missing_cluster(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            core_skin.get_influences("mocked_missing_cluster")

    def test_get_bound_joints(self):
        import_skinned_test_file()
        result = core_skin.get_bound_joints("plane")
        expected = ["|root_jnt", "|root_jnt|mid_jnt", "|root_jnt|mid_jnt|end_jnt"]
        self.assertEqual(expected, result)

    def test_get_bound_joints_missing_mesh(self):
        import_skinned_test_file()
        logging.disable(logging.WARNING)
        result = core_skin.get_bound_joints("mocked_missing_mesh")
        logging.disable(logging.NOTSET)
        expected = []
        self.assertEqual(expected, result)

    def test_get_geos_from_skin_cluster_missing_mesh(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            core_skin.get_geos_from_skin_cluster("mocked_missing_mesh")

    def test_get_skin_weights(self):
        import_skinned_test_file()
        result = core_skin.get_skin_weights("plane")
        expected = {
            0: {"root_jnt": 1.0},
            1: {"root_jnt": 1.0},
            2: {"mid_jnt": 1.0},
            3: {"mid_jnt": 1.0},
            4: {"end_jnt": 1.0},
            5: {"end_jnt": 1.0},
        }
        self.assertEqual(expected, result)

    def test_set_skin_weights(self):
        import_skinned_test_file()
        skin_data = {
            0: {"root_jnt": 1.0},
            1: {"root_jnt": 1.0},
            2: {"mid_jnt": 1.0},
            3: {"mid_jnt": 1.0},
            4: {"end_jnt": 1.0},
            5: {"end_jnt": 1.0},
        }
        cmds.delete("skinCluster1")
        cmds.select(["root_jnt", "mid_jnt", "end_jnt", "plane"])
        skin_cluster = cmds.skinCluster(tsb=True)[0]
        self.assertTrue(cmds.objExists(skin_cluster))
        core_skin.set_skin_weights("plane", skin_data=skin_data)
        result = core_skin.get_skin_weights("plane")
        self.assertEqual(skin_data, result)

    def test_export_skin_weights_to_json(self):
        import_skinned_test_file()
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        temp_file = os.path.join(test_temp_dir, "temp_file.temp")
        skin_data = {
            0: {"root_jnt": 1.0},
            1: {"root_jnt": 1.0},
            2: {"mid_jnt": 1.0},
            3: {"mid_jnt": 1.0},
            4: {"end_jnt": 1.0},
            5: {"end_jnt": 1.0},
        }
        with open(temp_file, "w") as file:
            import json

            json.dump(skin_data, file)
        cmds.delete("skinCluster1")
        cmds.select(["root_jnt", "mid_jnt", "end_jnt", "plane"])
        skin_cluster = cmds.skinCluster(tsb=True)[0]
        self.assertTrue(cmds.objExists(skin_cluster))
        core_skin.import_skin_weights_from_json(target_object="plane", import_file_path=temp_file)
        result = core_skin.get_skin_weights("plane")
        self.assertEqual(skin_data, result)

    @patch("gt.core.feedback.log_when_true")
    def test_is_valid_for_binding_valid_object(self, mock_log_when_true):
        maya_test_tools.create_poly_cube(name="valid_object")
        result = core_skin.is_valid_for_binding("valid_object")
        self.assertTrue(result)
        mock_log_when_true.assert_not_called()

    @patch("gt.core.feedback.log_when_true")
    def test_is_valid_for_binding_missing_object(self, mock_log_when_true):
        result = core_skin.is_valid_for_binding("missing_object")
        self.assertFalse(result)
        mock_log_when_true.assert_called_once()

    @patch("gt.core.feedback.log_when_true")
    def test_is_valid_for_binding_no_shapes(self, mock_log_when_true):
        cmds.group(name="object_no_shapes", empty=True, world=True)
        result = core_skin.is_valid_for_binding("object_no_shapes")
        self.assertFalse(result)
        mock_log_when_true.assert_called_once()

    @patch("gt.core.feedback.log_when_true")
    def test_is_valid_for_binding_invalid_shape_type(self, mock_log_when_true):
        cmds.spaceLocator(name="object_invalid_shape_type")
        result = core_skin.is_valid_for_binding("object_invalid_shape_type")
        self.assertFalse(result)
        mock_log_when_true.assert_called_once()

    @patch("gt.core.feedback.log_when_true")
    def test_is_valid_for_binding_invisible_shape(self, mock_log_when_true):
        cube = maya_test_tools.create_poly_cube(name="object_invisible_shape")
        shapes = cmds.listRelatives(cube, shapes=True, children=False, fullPath=True) or []
        for shape in shapes:
            cmds.setAttr(f"{shape}.v", 0)
        result = core_skin.is_valid_for_binding("object_invisible_shape")
        self.assertFalse(result)
        mock_log_when_true.assert_called_once()

    def test_bind_skin(self):
        import_skinned_test_file()
        cmds.delete("skinCluster1")
        result = core_skin.bind_skin(joints=["root_jnt", "mid_jnt", "end_jnt"], objects="plane")
        expected = ["skinCluster3"]
        self.assertEqual(expected, result)
        result = core_skin.get_skin_weights("plane")
        expected = 6
        self.assertEqual(expected, len(result))

    def test_get_python_influences_code(self):
        import_skinned_test_file()
        result = core_skin.get_python_influences_code(obj_list=["plane", "plane_two"])
        expected = (
            '# Joint influences found in "plane":\n'
            "bound_list = ['plane', '|root_jnt', '|root_jnt|mid_jnt', '|root_jnt|mid_jnt|end_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)\n"
            '\n# Joint influences found in "plane_two":\n'
            "bound_list = ['plane_two', '|root_two_jnt', '|root_two_jnt|mid_two_jnt', '|root_two_jnt|mid_two_jnt|end_two_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)"
        )
        self.assertEqual(expected, result)

    def test_get_python_influences_code_no_bound_mesh(self):
        import_skinned_test_file()
        result = core_skin.get_python_influences_code(obj_list=["plane", "plane_two"], include_bound_mesh=False)
        expected = (
            '# Joint influences found in "plane":\n'
            "bound_list = ['|root_jnt', '|root_jnt|mid_jnt', '|root_jnt|mid_jnt|end_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)\n"
            '\n# Joint influences found in "plane_two":\n'
            "bound_list = ['|root_two_jnt', '|root_two_jnt|mid_two_jnt', '|root_two_jnt|mid_two_jnt|end_two_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)"
        )
        self.assertEqual(expected, result)

    def test_get_python_influences_code_no_filter(self):
        import_skinned_test_file()
        result = core_skin.get_python_influences_code(obj_list=["plane", "plane_two"], include_existing_filter=False)
        expected = (
            '# Joint influences found in "plane":\n'
            "bound_list = ['plane', '|root_jnt', '|root_jnt|mid_jnt', '|root_jnt|mid_jnt|end_jnt']"
            "\ncmds.select(bound_list)\n"
            '\n# Joint influences found in "plane_two":\n'
            "bound_list = ['plane_two', '|root_two_jnt', '|root_two_jnt|mid_two_jnt', '|root_two_jnt|mid_two_jnt|end_two_jnt']"
            "\ncmds.select(bound_list)"
        )
        self.assertEqual(expected, result)

    def test_selected_get_python_influences_code(self):
        import_skinned_test_file()
        cmds.select(["plane", "plane_two"])
        result = core_skin.selected_get_python_influences_code()
        expected = (
            '# Joint influences found in "plane":\n'
            "bound_list = ['plane', '|root_jnt', '|root_jnt|mid_jnt', '|root_jnt|mid_jnt|end_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)\n"
            '\n# Joint influences found in "plane_two":\n'
            "bound_list = ['plane_two', '|root_two_jnt', '|root_two_jnt|mid_two_jnt', '|root_two_jnt|mid_two_jnt|end_two_jnt']"
            "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"
            "\ncmds.select(bound_list)"
        )
        self.assertEqual(expected, result)

    def test_add_influences_to_set(self):
        import_skinned_test_file()
        result = core_skin.add_influences_to_set(obj_list=["plane", "plane_two"])
        expected = ["plane_influenceSet", "plane_two_influenceSet"]
        self.assertEqual(expected, result)

    def test_selected_add_influences_to_set(self):
        import_skinned_test_file()
        cmds.select(["plane", "plane_two"])
        result = core_skin.selected_add_influences_to_set()
        expected = ["plane_influenceSet", "plane_two_influenceSet"]
        self.assertEqual(expected, result)

    def test_get_skin_weights_from_surface_valid(self):
        """
        Test retrieving skin weights from a valid NURBS surface.
        """
        surface, joints, skin_cluster = create_surface_test_scene()

        expected_weights = {
            (0, 0): {"joint_three": 1.0},
            (0, 1): {"joint_two": 1.0},
            (0, 2): {"joint_one": 1.0},
            (0, 3): {"joint_one": 1.0},
            (1, 0): {"joint_three": 1.0},
            (1, 1): {"joint_two": 1.0},
            (1, 2): {"joint_one": 1.0},
            (1, 3): {"joint_one": 1.0},
            (2, 0): {"joint_three": 1.0},
            (2, 1): {"joint_two": 1.0},
            (2, 2): {"joint_one": 1.0},
            (2, 3): {"joint_one": 1.0},
        }
        result_weights = core_skin.get_skin_weights_from_surface(surface, remove_unused_inf=True)

        for cv, expected_data in expected_weights.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

    def test_get_skin_weights_from_surface_all_influences(self):
        """
        Test retrieving skin weights from a valid NURBS surface, but keeping all influences (even zeros)
        """
        surface, joints, skin_cluster = create_surface_test_scene()

        expected_weights = {
            (0, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (0, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (0, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (0, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (1, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (1, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (2, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (2, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
        }
        result_weights = core_skin.get_skin_weights_from_surface(surface, remove_unused_inf=False)
        for cv, expected_data in expected_weights.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

    def test_get_skin_weights_from_surface_invalid_surface(self):
        """
        Test retrieving skin weights from an invalid surface (raises ValueError).
        """
        with self.assertRaises(ValueError):
            core_skin.get_skin_weights_from_surface("nonExistentSurface")

    def test_set_skin_weights_on_surface(self):
        """
        Test applying skin weights to a NURBS surface.
        """
        surface, joints, skin_cluster = create_surface_test_scene()

        expected_weights = {
            (0, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (0, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (0, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (0, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (1, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (1, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (2, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (2, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
        }

        result_weights = core_skin.get_skin_weights_from_surface(surface, remove_unused_inf=False)
        for cv, expected_data in expected_weights.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

        new_weights = {
            (0, 2): {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Top Left
            (1, 2): {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Top Right
            (0, 1): {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Mid Left
            (1, 1): {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Mid Right
            (0, 0): {"joint_one": 0.0, "joint_two": 1.0, "joint_three": 0.0},  # Bottom Right
            (1, 0): {"joint_one": 0.0, "joint_two": 1.0, "joint_three": 0.0},  # Bottom Left
        }

        core_skin.set_skin_weights_on_surface(surface, new_weights)
        # Verify the applied weights
        result_weights = core_skin.get_skin_weights_from_surface(surface, remove_unused_inf=True)

        expected = {
            (0, 0): {"joint_two": 1.0},
            (0, 1): {"joint_one": 1.0},
            (0, 2): {"joint_one": 1.0},
            (0, 3): {"joint_one": 1.0},
            (1, 0): {"joint_two": 1.0},
            (1, 1): {"joint_one": 1.0},
            (1, 2): {"joint_one": 1.0},
            (1, 3): {"joint_one": 1.0},
            (2, 0): {"joint_two": 1.0},
            (2, 1): {"joint_one": 1.0},
            (2, 2): {"joint_one": 1.0},
            (2, 3): {"joint_one": 1.0},
        }

        for cv, expected_data in expected.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

    def test_get_skin_weights_from_surface_all_influences_encoded(self):
        """
        Test retrieving skin weights from a valid NURBS surface, but keeping all influences (even zeros)
        """
        surface, joints, skin_cluster = create_surface_test_scene()

        expected_weights = {
            "(0, 0)": {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            "(0, 1)": {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            "(0, 2)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            "(0, 3)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            "(1, 0)": {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            "(1, 1)": {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            "(1, 2)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            "(1, 3)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            "(2, 0)": {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            "(2, 1)": {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            "(2, 2)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            "(2, 3)": {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
        }
        result_weights = core_skin.get_skin_weights_from_surface(
            surface, remove_unused_inf=False, encode_key_as_str=True
        )
        for cv, expected_data in expected_weights.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

    def test_set_skin_weights_on_surface_encoded(self):
        """
        Test applying skin weights to a NURBS surface.
        """
        surface, joints, skin_cluster = create_surface_test_scene()

        expected_weights = {
            (0, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (0, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (0, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (0, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (1, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (1, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (1, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 0): {"joint_three": 1.0, "joint_four": 0.0, "joint_two": 0.0, "joint_one": 0.0},
            (2, 1): {"joint_two": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_one": 0.0},
            (2, 2): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
            (2, 3): {"joint_one": 1.0, "joint_four": 0.0, "joint_three": 0.0, "joint_two": 0.0},
        }

        result_weights = core_skin.get_skin_weights_from_surface(surface, remove_unused_inf=False)
        for cv, expected_data in expected_weights.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)

        new_weights = {
            "(0, 2)": {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Top Left
            "(1, 2)": {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Top Right
            "(0, 1)": {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Mid Left
            "(1, 1)": {"joint_one": 1.0, "joint_two": 0.0, "joint_three": 0.0},  # Mid Right
            "(0, 0)": {"joint_one": 0.0, "joint_two": 1.0, "joint_three": 0.0},  # Bottom Right
            "(1, 0)": {"joint_one": 0.0, "joint_two": 1.0, "joint_three": 0.0},  # Bottom Left
        }

        core_skin.set_skin_weights_on_surface(surface, new_weights, decode_str_keys=True)
        # Verify the applied weights
        result_weights = core_skin.get_skin_weights_from_surface(
            surface, remove_unused_inf=True, encode_key_as_str=True
        )

        expected = {
            "(0, 0)": {"joint_two": 1.0},
            "(0, 1)": {"joint_one": 1.0},
            "(0, 2)": {"joint_one": 1.0},
            "(0, 3)": {"joint_one": 1.0},
            "(1, 0)": {"joint_two": 1.0},
            "(1, 1)": {"joint_one": 1.0},
            "(1, 2)": {"joint_one": 1.0},
            "(1, 3)": {"joint_one": 1.0},
            "(2, 0)": {"joint_two": 1.0},
            "(2, 1)": {"joint_one": 1.0},
            "(2, 2)": {"joint_one": 1.0},
            "(2, 3)": {"joint_one": 1.0},
        }

        for cv, expected_data in expected.items():
            self.assertDictAlmostEqual(result_weights[cv], expected_data)
