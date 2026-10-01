"""Pure validation and Maya characterization regression tests."""

import json
import os
import tempfile
import unittest
from unittest import mock

from gt.tools.kimodo_generator import kimodo_generator_hik as humanik
from gt.tools.kimodo_generator import kimodo_generator_hik_tools as hik_tools
from gt.utils import kimodo


def skeleton_fixture():
    """Returns a real SOMA77 skeleton metadata fixture.

    Returns:
        dict: Skeleton topology and neutral joint offsets.
    """
    path = os.path.join(os.path.dirname(__file__), "data", "soma_skeleton.json")
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


class TestHumanIKValidation(unittest.TestCase):
    """Checks mapping and opt-in settings without importing Maya."""

    def test_defaults_and_optional_files(self):
        """Empty overrides do not require files or a Maya installation."""
        self.assertEqual(humanik.default_settings(), humanik.validate_settings({}, check_files=True))
        with self.assertRaises(ValueError):
            humanik.validate_settings({"tpose_path": "missing.pose", "reference_frame": 0})
        with self.assertRaises(ValueError):
            humanik.validate_settings({"reference_frame": float("nan")})
        with self.assertRaises(ValueError):
            humanik.validate_settings({"character_name": "bad:name"})
        with self.assertRaises(ValueError):
            humanik.validate_settings({"definition_path": "missing.xml"}, check_files=True)


    def test_soma_mapping(self):
        """SOMA leg and metacarpal names are not mistaken for native HIK slots."""
        mapping = humanik.soma_mapping(skeleton_fixture())
        self.assertEqual("LeftLeg", mapping["LeftUpLeg"])
        self.assertEqual("LeftShin", mapping["LeftLeg"])
        self.assertEqual("LeftHandIndex1", mapping["LeftInHandIndex"])
        self.assertEqual("LeftHandIndex2", mapping["LeftHandIndex1"])
        self.assertEqual("Chest", mapping["Spine2"])
        self.assertEqual(len(mapping), len(set(mapping.values())))
        skeleton = skeleton_fixture()
        skeleton["id"] = "unknown"
        with self.assertRaises(ValueError):
            humanik.soma_mapping(skeleton)

    def test_custom_mapping_is_scoped(self):
        """XML namespaces are stripped and missing core slots are rejected."""
        skeleton = skeleton_fixture()
        mapping = humanik.soma_mapping(skeleton)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "mapping.xml")
            items = "".join(f'<item key="{slot}" value="foreign:{name}"/>' for slot, name in mapping.items())
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(f"<config_root><match_list>{items}</match_list></config_root>")
            self.assertEqual(mapping, humanik.read_mapping(path, skeleton))
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("<config_root><match_list/></config_root>")
            with self.assertRaises(ValueError):
                humanik.read_mapping(path, skeleton)


class TestHumanIKMaya(unittest.TestCase):
    """Runs only with mayapy; initializes Maya once for the test class."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone without requiring it for pure validation tests."""
        try:
            import maya.standalone
            import maya.cmds as cmds
        except ImportError:
            raise unittest.SkipTest("Requires Maya Python")
        cls.owns_maya = False
        if not hasattr(cmds, "file"):
            maya.standalone.initialize(name="python")
            cls.owns_maya = True
        cls.cmds = cmds

    @classmethod
    def tearDownClass(cls):
        """Releases standalone when this class initialized it."""
        if cls.owns_maya:
            import maya.standalone
            maya.standalone.uninitialize()

    def setUp(self):
        """Imports an animated SOMA77 fixture with a distinct namespace."""
        self.cmds.file(new=True, force=True)
        skeleton = skeleton_fixture()
        motion = {
            "schema_version": 1, "fps": 30, "frame_count": 2,
            "coordinates": {"units": "meters", "up": "y", "forward": "+z",
                            "rotations": "column_local_matrix"}, "skeleton": skeleton,
            "root_positions": [[0, 1, 0], [0.1, 1.1, 0.2]],
            "local_rotations": [[[[1, 0, 0], [0, 1, 0], [0, 0, 1]] for unused in range(77)]
                                for unused in range(2)]}
        # The current animated pose differs from the neutral characterization stance.
        arm = skeleton["joint_names"].index("LeftArm")
        motion["local_rotations"][1][arm] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        self.rest_motion = dict(motion, frame_count=1, root_positions=[motion["root_positions"][0]],
                                local_rotations=[motion["local_rotations"][0]])
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "motion.json")
            with open(path, "w", encoding="utf-8") as stream:
                json.dump(motion, stream)
            self.result = kimodo.import_motion(path, namespace="hik_source", start_frame=11)

    def snapshot(self):
        """Captures observable animation and temporary scene state.

        Returns:
            dict: Keys, animation connections, time, selection, namespace, and auto-key.
        """
        cmds = self.cmds
        curves = cmds.ls(type="animCurve") or []
        return {
            "curves": {curve: (cmds.keyframe(curve, query=True, timeChange=True),
                               cmds.keyframe(curve, query=True, valueChange=True),
                               cmds.listConnections(curve, source=False, destination=True, plugs=True))
                       for curve in curves},
            "time": cmds.currentTime(query=True), "selection": cmds.ls(selection=True, long=True),
            "transforms": {joint: [round(value, 7) for value in cmds.xform(
                joint, query=True, matrix=True, worldSpace=True)] for joint in self.result["joints"]},
            "namespace": cmds.namespaceInfo(currentNamespace=True), "autokey": cmds.autoKeyframe(query=True)}

    def test_pose_skeleton_auto_definition_is_editable_and_grounded(self):
        """The public definition API creates an unkeyed, characterized pose source."""
        before = self.snapshot()
        definition = kimodo.KimodoGenerationDefinition("Walk")
        pose = definition.create_pose_skeleton(self.rest_motion, namespace="authoring")
        self.assertEqual("kimodo", pose["humanik"])
        self.assertEqual(True, self.cmds.getAttr(f"{pose['humanik']}.InputCharacterizationLock"))
        self.assertFalse(self.cmds.listConnections(pose["joints"], type="animCurve"))
        self.assertEqual(pose["joints"][1:], pose["translation_limited_joints"])
        for axis in "XYZ":
            self.assertEqual([False, False], self.cmds.transformLimits(
                pose["joints"][0], query=True, **{f"enableTranslation{axis}": True}))
            self.assertEqual([True, True], self.cmds.transformLimits(
                pose["joints"][1], query=True, **{f"enableTranslation{axis}": True}))
        offset = self.cmds.getAttr(f"{pose['joints'][1]}.translateX")
        self.cmds.setAttr(f"{pose['joints'][1]}.translateX", offset + 0.5)
        self.assertAlmostEqual(offset, self.cmds.getAttr(f"{pose['joints'][1]}.translateX"))
        lowest = min(self.cmds.xform(joint, query=True, translation=True, worldSpace=True)[1]
                     for joint in pose["joints"])
        self.assertAlmostEqual(0, lowest, places=5)
        self.cmds.setAttr("authoring:LeftArm.rz", -35)
        self.assertEqual([45], kimodo.capture_pose(pose["group"], frame_index=45)["frame_indices"])
        self.assertEqual(before, self.snapshot())

    def test_pose_skeleton_plain_option_and_cleanup_on_failure(self):
        """Disabling HIK makes no character; failed characterization removes only its new import."""
        definition = kimodo.KimodoGenerationDefinition("Walk", auto_humanik=False)
        plain = definition.create_pose_skeleton(self.rest_motion, namespace="plain")
        self.assertIsNone(plain["humanik"])
        self.assertEqual([], self.cmds.ls(type="HIKCharacterNode"))
        with mock.patch.object(kimodo, "create_humanik_definition", side_effect=ValueError("test failure")):
            with self.assertRaises(ValueError):
                kimodo.create_pose_skeleton(self.rest_motion, namespace="failed_pose")
        self.assertFalse(self.cmds.namespace(exists="failed_pose"))
        self.assertTrue(self.cmds.objExists(plain["group"]))
        self.assertTrue(self.cmds.objExists(self.result["group"]))

    def test_python_definition_can_disable_body_translation_limits(self):
        """Exposes the Maya joint-limit option to definition-driven Python workflows."""
        definition = kimodo.KimodoGenerationDefinition(
            "Walk", auto_humanik=False, limit_body_joint_translations=False)
        pose = definition.create_pose_skeleton(self.rest_motion, namespace="unlimited_pose")
        self.assertEqual([], pose["translation_limited_joints"])
        for axis in "XYZ":
            self.assertEqual([False, False], self.cmds.transformLimits(
                pose["joints"][1], query=True, **{f"enableTranslation{axis}": True}))

    def test_pose_previews_are_tracked_templateable_and_safely_removed(self):
        """Marks only preview roots, optionally templates their hierarchy, and removes previews by tag."""
        cmds = self.cmds
        joint_count = len(self.rest_motion["skeleton"]["joint_names"])
        constraint = {
            "type": "fullbody",
            "frame_indices": [0],
            "root_positions": [[0, 0, 0]],
            "local_joints_rot": [[[0, 0, 0] for unused in range(joint_count)]],
        }
        template = kimodo.preview_pose(
            constraint, self.rest_motion, namespace="pose_template_test", display_name="kimodo_walk_frame_005")
        editable = kimodo.preview_pose(constraint, self.rest_motion, namespace="pose_editable_test", template=False)
        marker = kimodo.POSE_PREVIEW_ATTRIBUTE
        self.assertTrue(cmds.getAttr(f"{template['group']}.{marker}"))
        self.assertTrue(cmds.getAttr(f"{editable['group']}.{marker}"))
        self.assertTrue(template["group"].endswith(":kimodo_walk_frame_005"))

        template_nodes = [template["group"]] + (cmds.listRelatives(
            template["group"], allDescendents=True, fullPath=True) or [])
        self.assertTrue(template_nodes)
        for node in template_nodes:
            if cmds.attributeQuery("overrideEnabled", node=node, exists=True):
                self.assertTrue(cmds.getAttr(f"{node}.overrideEnabled"), node)
                self.assertEqual(1, cmds.getAttr(f"{node}.overrideDisplayType"), node)
        self.assertFalse(cmds.getAttr(f"{editable['group']}.overrideEnabled"))

        path_preview = cmds.createNode("transform", name="kimodo_path_preview_test")
        kimodo.tag_path_preview(path_preview)

        self.assertEqual(3, kimodo.remove_pose_previews())
        self.assertFalse(cmds.objExists(template["group"]))
        self.assertFalse(cmds.objExists(editable["group"]))
        self.assertFalse(cmds.objExists(path_preview))
        self.assertTrue(cmds.objExists(self.result["group"]))
        self.assertEqual(0, kimodo.remove_pose_previews())

    def test_pose_skeleton_accepts_humanik_overrides(self):
        """Script callers can pass the same optional settings as the HumanIK tab."""
        pose = kimodo.create_pose_skeleton(self.rest_motion, namespace="overrides", humanik_settings={
            "character_name": "pose_character", "lock_definition": False})
        self.assertEqual("pose_character", pose["humanik"])
        self.assertEqual(False, self.cmds.getAttr("pose_character.InputCharacterizationLock"))

    def test_pose_skeleton_grounding_handles_z_up(self):
        """Uses the placement transform when grounding in a Z-up Maya scene."""
        cmds = self.cmds
        original_axis = cmds.upAxis(query=True, axis=True)
        try:
            cmds.upAxis(axis="z")
            pose = kimodo.create_pose_skeleton(self.rest_motion, namespace="z_pose", auto_humanik=False)
            lowest = min(cmds.xform(joint, query=True, translation=True, worldSpace=True)[2]
                         for joint in pose["joints"])
            self.assertAlmostEqual(0, lowest, places=5)
            self.assertEqual([0], kimodo.capture_pose(pose["group"])["frame_indices"])
        finally:
            cmds.upAxis(axis=original_axis)

    def test_definition_preserves_animation_and_state(self):
        """Built-in rest characterization locks and restores animation and scene state."""
        cmds = self.cmds
        cmds.currentTime(12)
        cmds.select(self.result["joints"][0])
        cmds.namespace(setNamespace="hik_source")
        cmds.autoKeyframe(state=True)
        before = self.snapshot()
        result = humanik.create_definition(self.result["group"])
        self.assertEqual("kimodo", result["character"])
        self.assertEqual(True, result["locked"])
        self.assertEqual(True, bool(cmds.listConnections(result["character"] + ".propertyState")))
        # Native stance offsets must have been captured, not merely the lock attribute set.
        self.assertGreater(cmds.getAttr(result["character"] + ".LeftArmT")[0][0], 1)
        self.assertEqual(before, self.snapshot())
        self.assertEqual("hik_source:LeftShin", cmds.listConnections(result["character"] + ".LeftLeg")[0])
        with self.assertRaises(ValueError):
            humanik.create_definition(self.result["group"])

    def test_failure_restores_animation(self):
        """A native lock failure cannot strand disconnected animation or a partial character."""
        from gt.utils import hik
        before = self.snapshot()
        with mock.patch.object(hik, "set_definition_lock", return_value=False):
            with self.assertRaises(ValueError):
                humanik.create_definition(self.result["group"])
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], self.cmds.ls(type="HIKCharacterNode"))
        self.assertEqual([], self.cmds.ls(type="HIKProperty2State"))

    def test_reference_frame_override(self):
        """A supplied Maya reference frame is evaluated without inserting keys."""
        before = self.snapshot()
        result = humanik.create_definition(self.result["group"], {"reference_frame": 11, "lock_definition": False})
        self.assertEqual(False, result["locked"])
        self.assertEqual(before, self.snapshot())

    def test_custom_xml_and_pose_override(self):
        """Uses supplied files but never connects identically named joints outside the import."""
        from gt.core import pose as core_pose

        cmds = self.cmds
        cmds.currentTime(11)
        pose = core_pose.get_pose_as_dict(self.result["joints"])
        mapping = humanik.soma_mapping(skeleton_fixture())
        cmds.namespace(add="unrelated")
        cmds.select(clear=True)
        unrelated = cmds.joint(name="unrelated:Hips")
        cmds.currentTime(12)
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            pose_path = os.path.join(directory, "reference.pose")
            xml_path = os.path.join(directory, "mapping.xml")
            with open(pose_path, "w", encoding="utf-8") as stream:
                json.dump(pose, stream)
            items = "".join(f'<item key="{slot}" value="unrelated:{name}"/>' for slot, name in mapping.items())
            with open(xml_path, "w", encoding="utf-8") as stream:
                stream.write(f"<config_root><match_list>{items}</match_list></config_root>")
            result = humanik.create_definition(self.result["group"], {
                "tpose_path": pose_path, "definition_path": xml_path, "character_name": "CustomCharacter"})
        self.assertEqual("CustomCharacter", result["character"])
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], cmds.listConnections(unrelated, type="HIKCharacterNode") or [])
        self.assertEqual("hik_source:Hips", cmds.listConnections("CustomCharacter.Hips")[0])

    def test_invalid_override_leaves_scene_unchanged(self):
        """Missing user files are warnings before character or animation mutations."""
        before = self.snapshot()
        with self.assertRaises(ValueError):
            humanik.create_definition(self.result["group"], {"tpose_path": "missing.pose"})
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], self.cmds.ls(type="HIKCharacterNode"))

    def test_default_name_collision_and_custom_name_safety(self):
        """Uses kimodo1 when kimodo is occupied and never overwrites an explicit name."""
        existing = self.cmds.createNode("transform", name="kimodo")
        with self.assertRaises(ValueError):
            humanik.create_definition(self.result["group"], {"character_name": "kimodo"})
        result = humanik.create_definition(self.result["group"])
        self.assertEqual("kimodo1", result["character"])
        self.assertEqual("transform", self.cmds.nodeType(existing))

    def test_default_import_namespace_does_not_break_character_creation(self):
        """Reproduces the reported failure: kimodo namespace forces a numbered HIK node."""
        self.cmds.namespace(rename=("hik_source", "kimodo"))
        group = self.result["group"].replace("hik_source:", "kimodo:")
        result = humanik.create_definition(group)
        self.assertEqual("kimodo1", result["character"])
        self.assertEqual(True, result["locked"])
        self.assertEqual("kimodo:LeftShin", self.cmds.listConnections("kimodo1.LeftLeg")[0])

    def test_shared_hik_helper_returns_actual_maya_name(self):
        """Never returns the requested hint when Maya has automatically renamed it."""
        from gt.utils import hik

        self.cmds.namespace(add="kimodo")
        character = hik.create_definition("kimodo")
        self.assertEqual("kimodo1", character)
        self.assertEqual("HIKCharacterNode", self.cmds.nodeType(character))

    def test_export_pose_and_definitions(self):
        """Exports batch-compatible pose and XML without changing the scene."""
        humanik.create_definition(self.result["group"])
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            pose_path = os.path.join(directory, "source.pose")
            xml_path = os.path.join(directory, "source.xml")
            hik_tools.export_pose(self.result["group"], pose_path)
            hik_tools.export_definition(hik_tools.source_character(self.result["group"]), xml_path)
            self.assertEqual(77, len(humanik.read_pose(pose_path, skeleton_fixture()["joint_names"])))
            self.assertEqual(humanik.soma_mapping(skeleton_fixture()),
                             humanik.read_mapping(xml_path, skeleton_fixture()))
        self.assertEqual(before, self.snapshot())

    def test_apply_pose_testing_is_undoable(self):
        """The deliberate pose test changes this frame without disconnecting animation."""
        cmds = self.cmds
        cmds.undoInfo(state=True)
        cmds.currentTime(12)
        before = self.snapshot()
        count = hik_tools.apply_pose(self.result["group"], humanik.default_settings())
        self.assertEqual(77, count)
        self.assertAlmostEqual(0, cmds.getAttr("hik_source:LeftArm.rz"), places=5)
        self.assertTrue(cmds.connectionInfo("hik_source:LeftArm.rz", sourceFromDestination=True))
        cmds.undo()
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
