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

    def test_get_time_keyframes_with_empty_object_list(self):
        create_anim_test_scene()
        result = core_anim.get_time_keyframes(obj_list=[])
        expected = []
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

    def test_keyframe_scope_available_scopes(self):
        result = sorted(core_anim.KeyframeScope.get_available_scopes())
        expected = ["both", "double", "time"]
        self.assertEqual(expected, result)

    def test_get_keyframes_both(self):
        create_anim_test_scene()
        result = core_anim.get_keyframes(key_scope=core_anim.KeyframeScope.BOTH)
        expected = [
            "cube_double_rotateY",
            "cube_double_scaleY",
            "cube_double_translateX",
            "cube_mixed_rotateY",
            "cube_mixed_scaleY",
            "cube_mixed_translateZ",
            "cube_time_rotateY",
            "cube_time_scaleY",
            "cube_time_translateZ",
        ]
        self.assertEqual(expected, result)

    def test_get_keyframes_time_scope(self):
        create_anim_test_scene()
        result = core_anim.get_keyframes(key_scope=core_anim.KeyframeScope.TIME)
        expected = sorted(core_anim.get_time_keyframes())
        self.assertEqual(expected, result)

    def test_get_keyframes_double_scope(self):
        create_anim_test_scene()
        result = core_anim.get_keyframes(key_scope=core_anim.KeyframeScope.DOUBLE)
        expected = sorted(core_anim.get_double_keyframes())
        self.assertEqual(expected, result)

    def test_get_keyframes_filtered(self):
        create_anim_test_scene()
        result = core_anim.get_keyframes(obj_list=["cube_time"], key_scope=core_anim.KeyframeScope.TIME)
        expected = ["cube_time_rotateY", "cube_time_scaleY", "cube_time_translateZ"]
        self.assertEqual(expected, result)

    def test_offset_time_keyframes_preserves_key_values(self):
        source = cmds.polyCube(name="offset_source", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=2)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=8)

        result = core_anim.offset_time_keyframes(nodes=[source], offset=3)
        times = cmds.keyframe(source, attribute="translateX", query=True, timeChange=True)
        values = cmds.keyframe(source, attribute="translateX", query=True, valueChange=True)

        self.assertEqual(2, result["key_count"])
        self.assertEqual([4.0, 8.0], times)
        self.assertEqual([2.0, 8.0], values)

    def test_offset_time_keyframes_preserves_selected_keys_for_all_scopes(self):
        scope_data = [
            ("all", 1, 3),
            ("selected", 1, 3),
            ("current", 5, 7),
            ("playback", 5, 7),
        ]
        for scope, selected_time, expected_time in scope_data:
            maya_test_tools.force_new_scene()
            source = cmds.polyCube(name="offset_source", createUVs=4, ch=False)[0]
            cmds.setKeyframe(source, attribute="translateX", time=1, value=2)
            cmds.setKeyframe(source, attribute="translateX", time=5, value=8)
            curve = core_anim.get_time_keyframes([source])[0]
            cmds.currentTime(4)
            cmds.playbackOptions(min=4, max=6)
            cmds.selectKey(clear=True)
            cmds.selectKey(curve, add=True, time=(selected_time, selected_time))

            core_anim.offset_time_keyframes(nodes=[source], offset=2, scope=scope)

            result = cmds.keyframe(curve, query=True, selected=True, timeChange=True)
            self.assertEqual([float(expected_time)], result)

    def test_offset_with_euler_filter_preserves_selected_keys(self):
        source = cmds.polyCube(name="filter_source", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="rotateX", time=1, value=2)
        cmds.setKeyframe(source, attribute="rotateX", time=5, value=200)
        curve = core_anim.get_time_keyframes([source])[0]
        cmds.selectKey(clear=True)
        cmds.selectKey(curve, add=True, time=(1, 1))

        offset_result = core_anim.offset_time_keyframes(nodes=[source], offset=2, scope="selected")
        core_anim.filter_animation_curves(offset_result["curves"])

        result = cmds.keyframe(curve, query=True, selected=True, timeChange=True)
        self.assertEqual([3.0], result)

    def test_animation_constants_group_clip_paste_and_mapping_values(self):
        expected = 1
        result = core_anim.AnimationConstants.Clip.SCHEMA_VERSION
        self.assertEqual(expected, result)

        expected = ["insert", "replace"]
        result = [
            core_anim.AnimationConstants.PasteMode.INSERT,
            core_anim.AnimationConstants.PasteMode.REPLACE,
        ]
        self.assertEqual(expected, result)

        expected = ["selection", "name", "namespace"]
        result = [
            core_anim.AnimationConstants.MappingMode.SELECTION,
            core_anim.AnimationConstants.MappingMode.NAME,
            core_anim.AnimationConstants.MappingMode.NAMESPACE,
        ]
        self.assertEqual(expected, result)

    def test_animation_clip_pastes_to_another_object(self):
        source = cmds.polyCube(name="animation_source", createUVs=4, ch=False)[0]
        target = cmds.polyCube(name="animation_target", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=2)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=8)
        cmds.setKeyframe(target, attribute="translateX", time=1, value=99)

        clip_data = core_anim.extract_animation_clip(nodes=[source])
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=[target],
            paste_time=10,
            mode=core_anim.AnimationConstants.PasteMode.REPLACE,
        )
        times = cmds.keyframe(target, attribute="translateX", query=True, timeChange=True)
        values = cmds.keyframe(target, attribute="translateX", query=True, valueChange=True)

        self.assertEqual(2, result["keys"])
        self.assertEqual([10.0, 14.0], times)
        self.assertEqual([2.0, 8.0], values)

    def test_animation_clip_insert_preserves_future_keys(self):
        source = cmds.polyCube(name="insert_source", createUVs=4, ch=False)[0]
        target = cmds.polyCube(name="insert_target", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=2)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=8)
        cmds.setKeyframe(target, attribute="translateX", time=10, value=50)
        cmds.setKeyframe(target, attribute="translateX", time=20, value=60)

        clip_data = core_anim.extract_animation_clip(nodes=[source])
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=[target],
            paste_time=10,
            mode=core_anim.AnimationConstants.PasteMode.INSERT,
        )
        times = cmds.keyframe(target, attribute="translateX", query=True, timeChange=True)
        values = cmds.keyframe(target, attribute="translateX", query=True, valueChange=True)

        self.assertEqual(2, result["keys"])
        self.assertEqual([10.0, 14.0, 15.0, 25.0], times)
        self.assertEqual([2.0, 8.0, 50.0, 60.0], values)

    def test_animation_clip_maps_matching_namespace_free_names(self):
        cmds.namespace(add="source_rig")
        cmds.namespace(add="target_rig")
        source = cmds.polyCube(name="source_rig:control", createUVs=4, ch=False)[0]
        target = cmds.polyCube(name="target_rig:control", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=3)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=9)

        clip_data = core_anim.extract_animation_clip(nodes=[source])
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=[target],
            paste_time=20,
            mode=core_anim.AnimationConstants.PasteMode.REPLACE,
            mapping_mode=core_anim.AnimationConstants.MappingMode.NAME,
        )
        times = cmds.keyframe(target, attribute="translateX", query=True, timeChange=True)
        values = cmds.keyframe(target, attribute="translateX", query=True, valueChange=True)

        self.assertEqual(2, result["keys"])
        self.assertEqual([20.0, 24.0], times)
        self.assertEqual([3.0, 9.0], values)

    def test_animation_clip_maps_to_target_namespace_without_selection(self):
        cmds.namespace(add="source_rig")
        cmds.namespace(add="target_rig")
        source = cmds.polyCube(name="source_rig:control", createUVs=4, ch=False)[0]
        target = cmds.polyCube(name="target_rig:control", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=3)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=9)

        clip_data = core_anim.extract_animation_clip(nodes=[source])
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=[],
            paste_time=20,
            mode=core_anim.AnimationConstants.PasteMode.REPLACE,
            mapping_mode=core_anim.AnimationConstants.MappingMode.NAMESPACE,
            source_namespace="source_rig",
            target_namespace="target_rig",
        )
        times = cmds.keyframe(target, attribute="translateX", query=True, timeChange=True)
        values = cmds.keyframe(target, attribute="translateX", query=True, valueChange=True)

        self.assertEqual(2, result["keys"])
        self.assertEqual([20.0, 24.0], times)
        self.assertEqual([3.0, 9.0], values)

    def test_animation_clip_extracts_selected_keyframes_only(self):
        source = cmds.polyCube(name="selected_key_source", createUVs=4, ch=False)[0]
        for frame, value in [(1, 2), (5, 8), (10, 14)]:
            cmds.setKeyframe(source, attribute="translateX", time=frame, value=value)
        curve = core_anim.get_time_keyframes([source])[0]
        cmds.selectKey(clear=True)
        cmds.selectKey(curve, add=True, time=(5, 5))
        cmds.selectKey(curve, add=True, time=(10, 10))

        clip_data = core_anim.extract_selected_animation_clip(nodes=[source])
        result = [key_data["time"] for key_data in clip_data["objects"][0]["attributes"][0]["keys"]]

        self.assertEqual([5.0, 10.0], result)

    def test_animation_clip_extracts_keys_before_and_after_current_frame(self):
        source = cmds.polyCube(name="range_key_source", createUVs=4, ch=False)[0]
        for frame, value in [(1, 2), (5, 8), (10, 14)]:
            cmds.setKeyframe(source, attribute="translateX", time=frame, value=value)
        cmds.currentTime(5)

        before_clip = core_anim.extract_animation_clip(nodes=[source], end_frame=cmds.currentTime(query=True))
        after_clip = core_anim.extract_animation_clip(nodes=[source], start_frame=cmds.currentTime(query=True))
        before_result = [key_data["time"] for key_data in before_clip["objects"][0]["attributes"][0]["keys"]]
        after_result = [key_data["time"] for key_data in after_clip["objects"][0]["attributes"][0]["keys"]]

        self.assertEqual([1.0, 5.0], before_result)
        self.assertEqual([5.0, 10.0], after_result)

    def test_animation_clip_details_lists_stored_objects_and_channels(self):
        clip_data = {
            "objects": [
                {
                    "name": "|source:control",
                    "attributes": [
                        {
                            "attribute": "translateX",
                            "keys": [{"time": 1, "value": 4}],
                        }
                    ],
                }
            ]
        }

        result = core_anim.get_animation_clip_details(clip_data)

        self.assertIn("Object 1: |source:control", result)
        self.assertIn("translateX: 1 key(s) at frame(s): 1", result)

    def test_animation_clip_can_paste_to_another_channel(self):
        source = cmds.polyCube(name="channel_source", createUVs=4, ch=False)[0]
        target = cmds.polyCube(name="channel_target", createUVs=4, ch=False)[0]
        cmds.setKeyframe(source, attribute="translateX", time=1, value=12)
        cmds.setKeyframe(source, attribute="translateX", time=5, value=24)

        clip_data = core_anim.extract_animation_clip(nodes=[source])
        result = core_anim.paste_animation_clip(
            clip_data=clip_data,
            targets=[target],
            paste_time=30,
            mode=core_anim.AnimationConstants.PasteMode.REPLACE,
            source_attribute="translateX",
            destination_attribute="rotateY",
        )
        times = cmds.keyframe(target, attribute="rotateY", query=True, timeChange=True)
        values = [round(value, 6) for value in cmds.keyframe(target, attribute="rotateY", query=True, valueChange=True)]

        self.assertEqual(2, result["keys"])
        self.assertEqual([30.0, 34.0], times)
        self.assertEqual([12.0, 24.0], values)

    def test_delete_keyframes_both(self):
        create_anim_test_scene()
        result = core_anim.delete_keyframes(key_scope=core_anim.KeyframeScope.BOTH)
        expected = 9
        self.assertEqual(expected, result)

    def test_delete_keyframes_time_scope(self):
        create_anim_test_scene()
        result = core_anim.delete_keyframes(key_scope=core_anim.KeyframeScope.TIME)
        expected = 5
        self.assertEqual(expected, result)

    def test_delete_keyframes_double_scope(self):
        create_anim_test_scene()
        result = core_anim.delete_keyframes(key_scope=core_anim.KeyframeScope.DOUBLE)
        expected = 4
        self.assertEqual(expected, result)

    def test_delete_keyframes_selected_scope(self):
        create_anim_test_scene()
        result = core_anim.delete_keyframes(obj_list=["cube_time"], key_scope=core_anim.KeyframeScope.TIME)
        expected = 3
        self.assertEqual(expected, result)

    def test_delete_keyframes_in_range(self):
        create_anim_test_scene()
        result = core_anim.delete_keyframes_in_range(start=None, end=5, key_scope=core_anim.KeyframeScope.TIME)
        expected = 5  # All five time curves have a key at/before frame 5
        self.assertEqual(expected, result)
        # cube_time_translateZ had keys at 1 and 10; only the key at 10 should remain
        result = cmds.keyframe("cube_time_translateZ", query=True, keyframeCount=True)
        expected = 1
        self.assertEqual(expected, result)

    def test_delete_keyframes_before_current_frame(self):
        create_anim_test_scene()
        cmds.currentTime(5)
        result = core_anim.delete_keyframes_before_current_frame(key_scope=core_anim.KeyframeScope.TIME)
        expected = 5
        self.assertEqual(expected, result)
        result = cmds.keyframe("cube_time_translateZ", query=True, keyframeCount=True)
        expected = 1  # Key at frame 10 remains
        self.assertEqual(expected, result)

    def test_delete_keyframes_after_current_frame(self):
        create_anim_test_scene()
        cmds.currentTime(5)
        result = core_anim.delete_keyframes_after_current_frame(key_scope=core_anim.KeyframeScope.TIME)
        expected = 5
        self.assertEqual(expected, result)
        result = cmds.keyframe("cube_time_translateZ", query=True, keyframeCount=True)
        expected = 1  # Key at frame 1 remains
        self.assertEqual(expected, result)

    def test_delete_time_keyframes_outside_range(self):
        create_anim_test_scene()
        result = core_anim.delete_time_keyframes_outside_range(start=1, end=10)
        expected = 1
        self.assertEqual(expected, result)
        result = cmds.keyframe("cube_time_scaleY", query=True, keyframeCount=True)
        expected = 1  # The key at the inclusive end frame remains.
        self.assertEqual(expected, result)

    def test_delete_time_keyframes_outside_range_with_large_frame(self):
        create_anim_test_scene()
        cmds.setKeyframe("cube_time.tx", time=100000000, value=1)
        result = core_anim.delete_time_keyframes_outside_range(start=1, end=10)
        expected = 2
        self.assertEqual(expected, result)
        result = cmds.objExists("cube_time_translateX")
        expected = False
        self.assertEqual(expected, result)

    def test_delete_time_keyframes_outside_animation_range(self):
        create_anim_test_scene()
        cmds.playbackOptions(animationStartTime=1, animationEndTime=5)
        result = core_anim.delete_time_keyframes_outside_animation_range()
        expected = 6
        self.assertEqual(expected, result)

    def test_delete_time_keyframes_outside_playback_range(self):
        create_anim_test_scene()
        cmds.playbackOptions(minTime=1, maxTime=5)
        result = core_anim.delete_time_keyframes_outside_playback_range()
        expected = 6
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
