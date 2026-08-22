import unittest
import logging
import json
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
import gt.tools.auto_rigger.modules.module_utils as tools_mod_utils
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.modules.module_biped_leg as module_leg
import gt.tools.auto_rigger.control_rig_pose as tools_control_pose
from gt.tests import maya_test_tools
import inspect

cmds = maya_test_tools.cmds


class TestModuleUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.file_path = os.path.join(self.temp_dir, "data.json")
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)

    def tearDown(self):
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_module_utils_inheritance(self):
        classes = []
        for name, obj in inspect.getmembers(tools_mod_utils):
            if inspect.isclass(obj) and obj.__module__ == tools_mod_utils.__name__:
                classes.append(obj)
        for rig_module in classes:
            an_instance = rig_module()
            result = isinstance(an_instance, tools_rig_frm.ModuleGeneric)
            self.assertTrue(result)

    def test_module_new_scene_basic_functionality(self):
        a_new_scene_module = tools_mod_utils.ModuleNewScene()
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_generic_module.add_new_proxy()  # Add a proxy so something is created
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_new_scene_module)
        a_project.add_to_modules(a_generic_module)

        a_cube = maya_test_tools.create_poly_cube(name="a_cube")
        self.assertTrue(cmds.objExists(a_cube))

        # Build functions should cause new scene to trigger
        a_project.build_proxy()
        a_project.build_rig()

        self.assertFalse(cmds.objExists(a_cube), "Unexpected object found, new scene failed to run.")

    def test_module_python_basic_functionality(self):
        a_python_module = tools_mod_utils.ModulePython()
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_generic_module.add_new_proxy()  # Add a proxy so something is created
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_python_module)
        a_project.add_to_modules(a_generic_module)

        a_python_module.set_execution_code('cmds.polyCube(name="a_cube", ch=False)')

        a_project.build_proxy()
        a_project.build_rig()

        self.assertTrue(cmds.objExists("a_cube"), "Expected object missing, python module failed to run.")

    def test_module_import_file_basic_functionality(self):
        an_import_file_module = tools_mod_utils.ModuleImportFile()
        an_import_file_module.set_file_path(file_path=r"{tests-data-dir}\cylinder_project\geo\cylinder.obj")
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_generic_module.add_new_proxy()  # Add a proxy so something is created
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_import_file_module)
        a_project.add_to_modules(a_generic_module)

        a_project.build_proxy()
        a_project.build_rig()

        expected = ["cylinderShape"]
        result = cmds.ls(typ="mesh")
        self.assertEqual(expected, result)

    def test_module_save_scene_basic_functionality(self):
        a_save_scene_module = tools_mod_utils.ModuleSaveScene()
        _scene_path = r"{tests-data-dir}\Rig\cylinder_rig.ma"
        a_save_scene_module.set_file_path(file_path=_scene_path)
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_generic_module.add_new_proxy()  # Add a proxy so something is created
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_generic_module)
        a_project.add_to_modules(a_save_scene_module)

        a_project.build_proxy()
        a_project.build_rig()

        _parsed_path = a_save_scene_module.parse_path(path=_scene_path)
        self.assertTrue(os.path.isfile(_parsed_path))

        if os.path.isfile(_parsed_path):
            os.remove(_parsed_path)

    def test_module_parent_switching_functionality(self):
        leg_module_instance = module_leg.ModuleBipedLeg(prefix="C")
        a_project = tools_rig_frm.RigProject()
        a_project.set_control_rig_pose_mode(tools_control_pose.ControlRigPoseMode.AUTOMATIC)
        a_project.add_to_modules(leg_module_instance)
        a_project.build_proxy()
        a_project.build_rig()
        cmds.setAttr("C_leg_CTRL.influenceSwitch", 1)
        expected = [0.0, 46.9966, 37.5034]
        pos = cmds.xform("C_lowerLeg_IK_CTRL", t=True, ws=True, q=True)
        result = [round(pos[0], 4), round(pos[1], 4), round(pos[2], 4)]
        self.assertEqual(expected, result)
        cmds.setAttr("C_foot_IK_CTRL.ty", 21)
        cmds.setAttr("C_foot_IK_CTRL.ry", 50)
        cmds.setAttr("C_lowerLeg_IK_CTRL.space", 1)
        pos = cmds.xform("C_lowerLeg_IK_CTRL", t=True, ws=True, q=True)
        result = [round(pos[0], 4), round(pos[1], 4), round(pos[2], 4)]
        expected = [30.2328, 67.9966, 23.4056]
        self.assertEqual(expected, result)
