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
from gt.core import anim as core_anim

cmds = maya_test_tools.cmds


def create_anim_test_scene():
    """
    Creates a test scene for the anim module
    """
    # Create Cubes
    cube_double = "cube_double"
    cube_double = cmds.polyCube(name=cube_double, createUVs=4, ch=False)[0]
    cmds.move(0, 0.5, 0, cube_double)
    cmds.xform(cube_double, pivots=(0, -0.5, 0))
    cmds.setAttr(f"{cube_double}.tx", -1)
    cmds.setAttr(f"{cube_double}.ty", 0.5)

    cube_time = "cube_time"
    cube_time = cmds.polyCube(name=cube_time, createUVs=4, ch=False)[0]
    cmds.move(0, 0.5, 0, cube_time)
    cmds.xform(cube_time, pivots=(0, -0.5, 0))
    cmds.setAttr(f"{cube_time}.tz", -1)
    cmds.setAttr(f"{cube_time}.ty", 0.5)

    cube_no_keys = "cube_no_keys"
    cube_no_keys = cmds.polyCube(name=cube_no_keys, createUVs=4, ch=False)[0]
    cmds.move(0, 0.5, 0, cube_no_keys)
    cmds.xform(cube_no_keys, pivots=(0, -0.5, 0))
    cmds.setAttr(f"{cube_no_keys}.tx", 1)
    cmds.setAttr(f"{cube_no_keys}.ty", 0.5)

    cube_mixed = "cube_mixed"
    cube_mixed = cmds.polyCube(name=cube_mixed, createUVs=4, ch=False)[0]
    cmds.move(0, 0.5, 0, cube_mixed)
    cmds.xform(cube_mixed, pivots=(0, -0.5, 0))
    cmds.setAttr(f"{cube_mixed}.tz", 1)
    cmds.setAttr(f"{cube_mixed}.ty", 0.5)

    # Add Time Keys
    cmds.setKeyframe(cube_time, attribute="tz", time=1, value=-1)
    cmds.setKeyframe(cube_time, attribute="tz", time=10, value=-10)
    cmds.setKeyframe(cube_time, attribute="ry", time=1, value=0)
    cmds.setKeyframe(cube_time, attribute="ry", time=10, value=90)
    cmds.setKeyframe(cube_time, attribute="sy", time=0, value=1)
    cmds.setKeyframe(cube_time, attribute="sy", time=10, value=2)
    cmds.delete(f"{cube_time}Shape_sofy")

    cmds.setKeyframe(cube_mixed, attribute="tz", time=1, value=1)
    cmds.setKeyframe(cube_mixed, attribute="tz", time=10, value=10)
    cmds.setKeyframe(cube_mixed, attribute="ry", time=1, value=0)
    cmds.setKeyframe(cube_mixed, attribute="ry", time=10, value=90)

    # Add Double Keys
    linear_params = {"inTangentType": "Linear", "outTangentType": "Linear"}

    # Translate Pure
    cmds.setDrivenKeyframe(
        f"{cube_double}.tx", currentDriver=f"{cube_time}.tz", driverValue=-10, value=-10, **linear_params
    )
    cmds.setDrivenKeyframe(
        f"{cube_double}.tx", currentDriver=f"{cube_time}.tz", driverValue=-1, value=-1, **linear_params
    )
    cmds.setDrivenKeyframe(
        f"{cube_double}.tx", currentDriver=f"{cube_time}.tz", driverValue=0, value=-2, **linear_params
    )

    # Rotate Pure
    cmds.setDrivenKeyframe(
        f"{cube_double}.ry", currentDriver=f"{cube_time}.ry", driverValue=0, value=0, **linear_params
    )
    cmds.setDrivenKeyframe(
        f"{cube_double}.ry", currentDriver=f"{cube_time}.ry", driverValue=90, value=-90, **linear_params
    )

    # Scale Pure
    cmds.setDrivenKeyframe(
        f"{cube_double}.sy", currentDriver=f"{cube_time}.sy", driverValue=1, value=1, **linear_params
    )
    cmds.setDrivenKeyframe(
        f"{cube_double}.sy", currentDriver=f"{cube_time}.sy", driverValue=2, value=2, **linear_params
    )

    # Scale Mixed
    cmds.setDrivenKeyframe(
        f"{cube_mixed}.sy", currentDriver=f"{cube_time}.ry", driverValue=0, value=1
    )  # No extra params = Auto
    cmds.setDrivenKeyframe(
        f"{cube_mixed}.sy", currentDriver=f"{cube_time}.ry", driverValue=90, value=0.5
    )  # No extra params = Auto


class TestAnimCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.temp_dir = maya_test_tools.generate_test_temp_dir()

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_time_keyframes(self):
        create_anim_test_scene()
        result = core_anim.get_time_keyframes()
        expected = [
            "cube_mixed_rotateY",
            "cube_time_rotateY",
            "cube_mixed_translateZ",
            "cube_time_translateZ",
            "cube_time_scaleY",
        ]
        self.assertEqual(expected, result)

    def test_get_time_keyframes_filtered(self):
        create_anim_test_scene()
        result = core_anim.get_time_keyframes(obj_list=["cube_time"])
        expected = ["cube_time_rotateY", "cube_time_scaleY", "cube_time_translateZ"]
        self.assertEqual(expected, result)

    def test_get_double_keyframes(self):
        create_anim_test_scene()
        result = core_anim.get_double_keyframes()
        expected = ["cube_double_rotateY", "cube_double_scaleY", "cube_double_translateX", "cube_mixed_scaleY"]
        self.assertEqual(expected, result)

    def test_get_double_keyframes_filtered(self):
        create_anim_test_scene()
        result = core_anim.get_double_keyframes(obj_list=["cube_double"])
        expected = ["cube_double_rotateY", "cube_double_scaleY", "cube_double_translateX"]
        self.assertEqual(expected, result)

    def test_delete_time_keyframes(self):
        create_anim_test_scene()
        result = core_anim.delete_time_keyframes()
        expected = 5
        self.assertEqual(expected, result)

    def test_delete_double_keyframes(self):
        create_anim_test_scene()
        result = core_anim.delete_double_keyframes()
        expected = 4
        self.assertEqual(expected, result)

    def test_DoubleKeyframe(self):
        create_anim_test_scene()
        double_keyframe = core_anim.DoubleKeyframe("cube_double_scaleY")
        result = double_keyframe.get_data_as_dict()
        expected = {
            "driven_attr": "cube_double.scaleY",
            "driver_attr": "cube_time.scaleY",
            "keyframe_data": [
                {
                    "in_angle_tangent": 0.0,
                    "in_tangent_type": "linear",
                    "in_weight": 1.0,
                    "interpolation": False,
                    "out_angle_tangent": 2.3859440303888126,
                    "out_tangent_type": "linear",
                    "out_weight": 1.0,
                    "time": 1.0,
                    "value": 1.0,
                },
                {
                    "in_angle_tangent": 2.3859440303888126,
                    "in_tangent_type": "linear",
                    "in_weight": 1.0,
                    "interpolation": False,
                    "out_angle_tangent": 0.0,
                    "out_tangent_type": "linear",
                    "out_weight": 1.0,
                    "time": 2.0,
                    "value": 2.0,
                },
            ],
            "node": "cube_double_scaleY",
        }
        self.assertEqual(expected, result)

    def test_find_set_driven_key(self):
        create_anim_test_scene()
        result = core_anim.find_set_driven_key(driven_attr_path="cube_double.tx", driver_attr_path="cube_time.tz")
        expected = "cube_double_translateX"
        self.assertEqual(expected, result)

    def test_export_double_keys_to_directory(self):
        create_anim_test_scene()
        result = core_anim.export_double_keys_to_directory(source_objs=["cube_double"], target_dir=self.temp_dir)
        expected = 3
        self.assertEqual(expected, result)
        result = [f for f in os.listdir(self.temp_dir) if os.path.isfile(os.path.join(self.temp_dir, f))]
        expected = ["cube_double_rotateY.json", "cube_double_scaleY.json", "cube_double_translateX.json"]
        self.assertEqual(expected, result)

    def test_import_double_keys_from_directory(self):
        create_anim_test_scene()
        core_anim.export_double_keys_to_directory(source_objs=["cube_double"], target_dir=self.temp_dir)
        core_anim.delete_double_keyframes()
        result = core_anim.import_double_keys_from_directory(source_dir=self.temp_dir)
        expected = 3
        self.assertEqual(expected, result)
        result = core_anim.get_double_keyframes(obj_list=["cube_double"])
        expected = ["cube_double_rotateY", "cube_double_scaleY", "cube_double_translateX"]
        self.assertEqual(expected, result)
