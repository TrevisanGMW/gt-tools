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
from gt.utils import skin_utils


def import_skinned_test_file():
    """
    Import test plane skinned file from inside the .../data folder/<name>.ma
    """
    maya_test_tools.import_data_file("plane_skinned.ma")


class TestSkinUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_skin_cluster(self):
        import_skinned_test_file()
        result = skin_utils.get_skin_cluster("plane")
        expected = "skinCluster1"
        self.assertEqual(expected, result)

    def test_get_skin_cluster_missing_item(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            skin_utils.get_skin_cluster("mocked_missing_mesh")

    def test_get_skin_cluster_not_skinned(self):
        cube = maya_test_tools.create_poly_cube()
        result = skin_utils.get_skin_cluster(cube)
        expected = None
        self.assertEqual(expected, result)

    def test_get_influences(self):
        import_skinned_test_file()
        result = skin_utils.get_influences("skinCluster1")
        expected = ['root_jnt', 'mid_jnt', 'end_jnt']
        self.assertEqual(expected, result)

    def test_get_influences_missing_cluster(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            skin_utils.get_influences("mocked_missing_cluster")

    def test_get_bound_joints(self):
        import_skinned_test_file()
        result = skin_utils.get_bound_joints("plane")
        expected = ['root_jnt', 'mid_jnt', 'end_jnt']
        self.assertEqual(expected, result)

    def test_get_bound_joints_missing_mesh(self):
        import_skinned_test_file()
        logging.disable(logging.WARNING)
        result = skin_utils.get_bound_joints("mocked_missing_mesh")
        logging.disable(logging.NOTSET)
        expected = []
        self.assertEqual(expected, result)

    def test_get_skin_cluster_from_geometry(self):
        import_skinned_test_file()
        result = skin_utils.get_skin_cluster_from_geometry("skinCluster1")
        expected = ['plane']
        self.assertEqual(expected, result)

    def test_get_skin_cluster_from_geometry_missing_mesh(self):
        import_skinned_test_file()
        with self.assertRaises(ValueError):
            skin_utils.get_skin_cluster_from_geometry("mocked_missing_mesh")

    def test_get_skin_weights(self):
        import_skinned_test_file()
        result = skin_utils.get_skin_weights("skinCluster1")
        expected = {'0': {'root_jnt': 1.0},
                    '1': {'root_jnt': 1.0},
                    '2': {'mid_jnt': 1.0},
                    '3': {'mid_jnt': 1.0},
                    '4': {'end_jnt': 1.0},
                    '5': {'end_jnt': 1.0}}
        self.assertEqual(expected, result)

    def test_set_skin_weights(self):
        import_skinned_test_file()
        skin_data = {'0': {'root_jnt': 1.0},
                     '1': {'root_jnt': 1.0},
                     '2': {'mid_jnt': 1.0},
                     '3': {'mid_jnt': 1.0},
                     '4': {'end_jnt': 1.0},
                     '5': {'end_jnt': 1.0}}
        maya_test_tools.cmds.delete("skinCluster1")
        maya_test_tools.cmds.select(['root_jnt', 'mid_jnt', 'end_jnt', 'plane'])
        skin_cluster = maya_test_tools.cmds.skinCluster(tsb=True)[0]
        self.assertTrue(maya_test_tools.cmds.objExists(skin_cluster))
        skin_utils.set_skin_weights(skin_cluster=skin_cluster, skin_data=skin_data)
        result = skin_utils.get_skin_weights(skin_cluster)
        self.assertEqual(skin_data, result)

    def test_export_skin_weights_to_json(self):
        import_skinned_test_file()
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        temp_file = os.path.join(test_temp_dir, "temp_file.temp")
        skin_data = {'0': {'root_jnt': 1.0},
                     '1': {'root_jnt': 1.0},
                     '2': {'mid_jnt': 1.0},
                     '3': {'mid_jnt': 1.0},
                     '4': {'end_jnt': 1.0},
                     '5': {'end_jnt': 1.0}}
        with open(temp_file, 'w') as file:
            import json
            json.dump(skin_data, file)
        maya_test_tools.cmds.delete("skinCluster1")
        maya_test_tools.cmds.select(['root_jnt', 'mid_jnt', 'end_jnt', 'plane'])
        skin_cluster = maya_test_tools.cmds.skinCluster(tsb=True)[0]
        self.assertTrue(maya_test_tools.cmds.objExists(skin_cluster))
        skin_utils.import_skin_weights_from_json(target_object="plane", import_file_path=temp_file)
        result = skin_utils.get_skin_weights(skin_cluster)
        self.assertEqual(skin_data, result)

    def test_bind_skin(self):
        import_skinned_test_file()
        maya_test_tools.cmds.delete("skinCluster1")
        result = skin_utils.bind_skin(joints=['root_jnt', 'mid_jnt', 'end_jnt'], objects="plane")
        expected = ['skinCluster3']
        self.assertEqual(expected, result)
        result = skin_utils.get_skin_weights('skinCluster3')
        expected = 6
        self.assertEqual(expected, len(result))

    def test_get_python_influences_code(self):
        import_skinned_test_file()
        result = skin_utils.get_python_influences_code(obj_list=['plane', 'plane_two'])
        expected = "# Joint influences found in \"plane\":\n" \
                   "bound_list = ['plane', 'root_jnt', 'mid_jnt', 'end_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)\n" \
                   "\n# Joint influences found in \"plane_two\":\n" \
                   "bound_list = ['plane_two', 'root_two_jnt', 'mid_two_jnt', 'end_two_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)"
        self.assertEqual(expected, result)

    def test_get_python_influences_code_no_bound_mesh(self):
        import_skinned_test_file()
        result = skin_utils.get_python_influences_code(obj_list=['plane', 'plane_two'],
                                                       include_bound_mesh=False)
        expected = "# Joint influences found in \"plane\":\n" \
                   "bound_list = ['root_jnt', 'mid_jnt', 'end_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)\n" \
                   "\n# Joint influences found in \"plane_two\":\n" \
                   "bound_list = ['root_two_jnt', 'mid_two_jnt', 'end_two_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)"
        self.assertEqual(expected, result)

    def test_get_python_influences_code_no_filter(self):
        import_skinned_test_file()
        result = skin_utils.get_python_influences_code(obj_list=['plane', 'plane_two'],
                                                       include_existing_filter=False)
        expected = "# Joint influences found in \"plane\":\n" \
                   "bound_list = ['plane', 'root_jnt', 'mid_jnt', 'end_jnt']" \
                   "\ncmds.select(bound_list)\n" \
                   "\n# Joint influences found in \"plane_two\":\n" \
                   "bound_list = ['plane_two', 'root_two_jnt', 'mid_two_jnt', 'end_two_jnt']" \
                   "\ncmds.select(bound_list)"
        self.assertEqual(expected, result)

    def test_selected_get_python_influences_code(self):
        import_skinned_test_file()
        maya_test_tools.cmds.select(['plane', 'plane_two'])
        result = skin_utils.selected_get_python_influences_code()
        expected = "# Joint influences found in \"plane\":\n" \
                   "bound_list = ['plane', 'root_jnt', 'mid_jnt', 'end_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)\n" \
                   "\n# Joint influences found in \"plane_two\":\n" \
                   "bound_list = ['plane_two', 'root_two_jnt', 'mid_two_jnt', 'end_two_jnt']" \
                   "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]" \
                   "\ncmds.select(bound_list)"
        self.assertEqual(expected, result)

    def test_add_influences_to_set(self):
        import_skinned_test_file()
        result = skin_utils.add_influences_to_set(obj_list=['plane', 'plane_two'])
        expected = ['plane_influenceSet', 'plane_two_influenceSet']
        self.assertEqual(expected, result)

    def test_selected_add_influences_to_set(self):
        import_skinned_test_file()
        maya_test_tools.cmds.select(['plane', 'plane_two'])
        result = skin_utils.selected_add_influences_to_set()
        expected = ['plane_influenceSet', 'plane_two_influenceSet']
        self.assertEqual(expected, result)
