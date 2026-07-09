import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import External Sdks
fbx_sdk_directory = os.path.join("R:/DccTools/maya/external/sdks/fbx")
sys.path.append(fbx_sdk_directory)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
import gt.tests.maya_test_tools as maya_test_tools
import gt.utils.fbx as utils_fbx
import gt.core.plugin as core_plugin

cmds = maya_test_tools.cmds


def import_test_rig_file():
    """
    Import test rig file.
    """
    maya_test_tools.import_data_file("cylinder_rig.ma")


def import_test_anim_file():
    """
    Import test anim file.
    """
    maya_test_tools.import_data_file("cylinder_anim.ma")


class TestFbxUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.file_path = os.path.join(self.temp_dir, "test_export_file.fbx")
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)
        core_plugin.load_plugin("fbxmaya")

    @classmethod
    def tearDownClass(cls):
        core_plugin.unload_plugin("fbxmaya")

    def import_exported_file(self):
        cmds.file(self.file_path, i=True)

    def test_skeletal_mesh_export(self):
        import_test_rig_file()
        cmds.select(["test_cylinder", "C_root_JNT"])
        fbx_exp = utils_fbx.FbxExporter()
        with fbx_exp as fbx:
            fbx.set_preferences_skeletal_mesh()
            fbx.export_file(path=self.file_path)

        maya_test_tools.force_new_scene()
        self.import_exported_file()
        result = cmds.ls(dag=True, v=True)
        expected = ["test_cylinder", "test_cylinderShape", "test_cylinderShapeOrig", "C_root_JNT"]
        self.assertEqual(expected, result)

    def test_animation_export(self):
        import_test_anim_file()
        cmds.select("C_root_JNT")
        fbx_exp = utils_fbx.FbxExporter()
        with fbx_exp as fbx:
            fbx.set_preferences_animation()
            fbx.export_file(path=self.file_path)

        maya_test_tools.force_new_scene()
        self.import_exported_file()
        cmds.currentUnit(time="ntsc")
        result = cmds.ls(dag=True, v=True)
        expected = ["C_root_JNT"]
        self.assertEqual(expected, result)
        result = cmds.keyframe("C_root_JNT", q=True, attribute="translateX")
        expected = [1.0, 50.0, 100.0]
        self.assertEqual(expected, result)

    def test_mesh_export(self):
        import_test_rig_file()
        cmds.select("test_cylinder")
        fbx_exp = utils_fbx.FbxExporter()
        with fbx_exp as fbx:
            fbx.set_preferences_mesh()
            fbx.export_file(path=self.file_path)

        maya_test_tools.force_new_scene()
        self.import_exported_file()
        result = cmds.ls(dag=True, v=True)
        expected = ["rig", "geometry", "test_cylinder", "test_cylinderShape"]
        self.assertEqual(expected, result)

    def test_animation_import(self):
        fbx_file_path = os.path.join(maya_test_tools.get_data_dir_path(), "animated_joint.fbx")
        fbx_import = utils_fbx.FbxImporter()
        with fbx_import as fbx:
            fbx.set_preferences_animation()
            fbx.import_file(path=fbx_file_path)
        result = cmds.ls(dag=True, v=True)
        expected = ["joint1"]
        self.assertEqual(expected, result)
        result = cmds.keyframe("joint1", at="tx", q=True)
        expected = [0.0, 10.0, 20.0, 30.0, 40.0]
        self.assertEqual(expected, result)

    def test_animation_with_namespace_import(self):
        fbx_file_path = os.path.join(maya_test_tools.get_data_dir_path(), "animated_joint.fbx")
        fbx_import = utils_fbx.FbxImporter()
        with fbx_import as fbx:
            fbx.set_preferences_animation()
            fbx.import_file(path=fbx_file_path, namespace="test")
        result = cmds.ls(dag=True, v=True)
        expected = ["test:joint1"]
        self.assertEqual(expected, result)
        result = cmds.keyframe("test:joint1", at="tx", q=True)
        expected = [0.0, 10.0, 20.0, 30.0, 40.0]
        self.assertEqual(expected, result)
