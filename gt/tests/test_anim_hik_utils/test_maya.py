"""Maya 2025 runtime and non-blocking Qt checks for HumanIK Utilities."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    import maya.cmds as cmds
    import maya.standalone as standalone
except ImportError:
    cmds = None

from gt.tools.anim_hik_utils.anim_hik_utils_model import AnimHikUtilsModel, DEFAULT_SETTINGS
from gt.tools.anim_hik_utils.anim_hik_utils_service import AnimHikUtilsService


@unittest.skipIf(cmds is None, "Requires Maya or mayapy")
class TestAnimHikUtilsMaya(unittest.TestCase):
    """Exercises real HumanIK nodes and the Qt interface in an isolated scene."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when Maya commands are not yet available."""
        from gt.ui import qt_import as ui_qt

        cls.application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])
        cls.owns_standalone = False
        try:
            cmds.about(version=True)
        except (AttributeError, RuntimeError):
            standalone.initialize(name="python")
            cls.owns_standalone = True
        cmds.loadPlugin("mayaHIK", quiet=True)
        cls.service = AnimHikUtilsService()

    @classmethod
    def tearDownClass(cls):
        """Clears temporary nodes and releases the owned standalone runtime."""
        cmds.file(new=True, force=True)
        if cls.owns_standalone:
            standalone.uninitialize()

    def setUp(self):
        """Creates two characters and a small generated-control graph."""
        cmds.file(new=True, force=True)
        self.character = cmds.createNode("HIKCharacterNode", name="hero")
        self.empty = cmds.createNode("HIKCharacterNode", name="empty")
        self.rig = cmds.createNode("HIKControlSetNode", name="hero_ControlRig")
        cmds.connectAttr(f"{self.character}.OutputCharacterDefinition", f"{self.rig}.InputCharacterDefinition")
        self.controls = {}
        for slot in ("Reference", "LeftArm", "RightArm"):
            node = cmds.createNode("transform", name=f"hero_Ctrl_{slot}")
            cmds.addAttr(node, longName="ControlSet", attributeType="message")
            cmds.connectAttr(f"{node}.ControlSet", f"{self.rig}.{slot}")
            self.controls[slot] = node

    def test_character_inspection_and_control_selection(self):
        """Inspection reads real native nodes and selects only the chosen rig."""
        details = self.service.inspect_character(self.character)
        self.assertEqual(self.rig, details["control_rig"])
        self.assertEqual(3, len(details["controls"]))
        self.assertEqual(3, self.service.select_nodes(self.character, "controls"))

    def test_source_graph_and_cycle_detection(self):
        """Retargeter source and destination connections are resolved without MEL."""
        retargeter = cmds.createNode("HIKRetargeterNode")
        cmds.connectAttr(f"{self.empty}.OutputCharacterDefinition", f"{retargeter}.InputCharacterDefinitionSrc")
        cmds.connectAttr(f"{self.character}.OutputCharacterDefinition", f"{retargeter}.InputCharacterDefinitionDst")
        self.assertEqual([self.empty], self.service.character_sources(self.character))
        self.assertEqual([], self.service.character_sources(self.empty))
        self.assertNotIn(self.empty, self.service.empty_definitions())
        with self.assertRaisesRegex(ValueError, "cycle"):
            self.service.definition_action(self.empty, "source", self.character)

    def test_create_and_rename_definition(self):
        """Native HumanIK wrappers return the actual created and renamed nodes."""
        created = self.service.definition_action("", "create", "Created")
        self.assertEqual("Created", created)
        renamed = self.service.definition_action(created, "rename", "Renamed")
        self.assertEqual("Renamed", renamed)
        self.assertTrue(cmds.objExists(renamed))

    def test_mirror_restores_scene_state_and_is_undoable(self):
        """The adapter mirrors a control pose in one undoable edit."""
        left, right = self.controls["LeftArm"], self.controls["RightArm"]
        cmds.setAttr(f"{left}.translateX", 3)
        cmds.select(left)
        cmds.currentTime(12)
        cmds.autoKeyframe(state=True)
        self.service.pose(self.character, "left", DEFAULT_SETTINGS)
        self.assertAlmostEqual(-3, cmds.getAttr(f"{right}.translateX"))
        self.assertEqual([left], cmds.ls(selection=True))
        self.assertEqual(12, cmds.currentTime(query=True))
        self.assertTrue(cmds.autoKeyframe(query=True, state=True))
        cmds.undo()
        self.assertAlmostEqual(0, cmds.getAttr(f"{right}.translateX"))

    def test_pose_export_and_import_round_trip(self):
        """Portable pose files restore values through the actual shared helpers."""
        left = self.controls["LeftArm"]
        cmds.setAttr(f"{left}.translateY", 4)
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "pose.json")
            self.service.export_file(self.character, "pose", path, DEFAULT_SETTINGS)
            cmds.setAttr(f"{left}.translateY", 0)
            self.service.pose(self.character, "import", DEFAULT_SETTINGS, path)
        self.assertAlmostEqual(4, cmds.getAttr(f"{left}.translateY"))

    def animate_sides(self):
        """Creates different sparse curves, including keys outside the edit range.

        Returns:
            tuple: Left and right translate plugs.
        """
        left = f"{self.controls['LeftArm']}.translateX"
        right = f"{self.controls['RightArm']}.translateX"
        for frame, left_value, right_value in ((0, 1, -20), (1, 2, -10), (3, 8, -30), (4, 9, -40)):
            cmds.setKeyframe(left, time=frame, value=left_value, inTangentType="linear", outTangentType="linear")
            cmds.setKeyframe(right, time=frame, value=right_value, inTangentType="linear", outTangentType="linear")
        return left, right

    def test_animation_mirror_preserves_source_outside_keys_state_and_undo(self):
        """Mirroring samples the source and replaces only target keys in the range."""
        left, right = self.animate_sides()
        original = cmds.keyframe(right, query=True, valueChange=True)
        source = cmds.keyframe(left, query=True, valueChange=True)
        cmds.currentTime(12)
        cmds.autoKeyframe(state=True)
        cmds.select(self.controls["LeftArm"])
        result = self.service.animation(self.character, "left", DEFAULT_SETTINGS, 1, 3, 0.5)
        self.assertEqual(5, result["sample_count"])
        self.assertEqual(source, cmds.keyframe(left, query=True, valueChange=True))
        self.assertEqual([0, 1, 1.5, 2, 2.5, 3, 4], cmds.keyframe(right, query=True, timeChange=True))
        for expected, actual in zip(
            [-20, -2, -3.5, -5, -6.5, -8, -40], cmds.keyframe(right, query=True, valueChange=True)
        ):
            self.assertAlmostEqual(expected, actual)
        self.assertEqual(12, cmds.currentTime(query=True))
        self.assertTrue(cmds.autoKeyframe(query=True, state=True))
        self.assertEqual([self.controls["LeftArm"]], cmds.ls(selection=True))
        cmds.undo()
        self.assertEqual(original, cmds.keyframe(right, query=True, valueChange=True))

    def test_animation_flip_captures_both_sides_before_any_writes(self):
        """Sparse target interpolation cannot corrupt the source while flipping."""
        left, right = self.animate_sides()
        result = self.service.animation(self.character, "flip", DEFAULT_SETTINGS, 1, 3)
        self.assertEqual(2, len(result["controls"]))
        self.assertEqual([10, 20, 30], cmds.keyframe(left, query=True, time=(1, 3), valueChange=True))
        self.assertEqual([-2, -5, -8], cmds.keyframe(right, query=True, time=(1, 3), valueChange=True))

    def test_animation_failure_rolls_back_partial_keys(self):
        """A mid-bake failure restores all animation instead of leaving a partial clip."""
        from gt.utils import hik

        unused_left, right = self.animate_sides()
        original = cmds.keyframe(right, query=True, valueChange=True)
        original_apply = hik._apply_hik_pose_data
        applied_samples = []

        def fail_second_sample(*args, **kwargs):
            """Applies one sample, then simulates a Maya failure.

            Args:
                *args: Pose application arguments.
                **kwargs: Pose application options.

            Returns:
                list: Applied controls on the first sample.
            """
            if applied_samples:
                raise RuntimeError("sample failure")
            applied_samples.append(True)
            return original_apply(*args, **kwargs)

        with patch.object(hik, "_apply_hik_pose_data", side_effect=fail_second_sample):
            with self.assertRaisesRegex(RuntimeError, "sample failure"):
                self.service.animation(self.character, "flip", DEFAULT_SETTINGS, 1, 3)
        self.assertEqual(original, cmds.keyframe(right, query=True, valueChange=True))
        self.assertEqual([0, 1, 3, 4], cmds.keyframe(right, query=True, timeChange=True))

    def test_animation_rejects_driven_target_before_edits(self):
        """Constraints and layers cannot be silently replaced by animation curves."""
        self.animate_sides()
        driver = cmds.createNode("transform", name="driver")
        cmds.connectAttr(f"{driver}.translateY", f"{self.controls['RightArm']}.translateY")
        with self.assertRaisesRegex(ValueError, "driver"):
            self.service.animation(self.character, "left", DEFAULT_SETTINGS, 1, 3)
        self.assertEqual([0, 1, 3, 4], cmds.keyframe(
            f"{self.controls['RightArm']}.translateX", query=True, timeChange=True
        ))

    def test_animation_preserves_locked_and_nonkeyable_channels(self):
        """Channels excluded from animation must not receive unkeyed pose changes."""
        self.animate_sides()
        left, right = self.controls["LeftArm"], self.controls["RightArm"]
        cmds.setAttr(f"{left}.scaleX", 2)
        cmds.setAttr(f"{right}.scaleX", keyable=False)
        cmds.setAttr(f"{right}.rotateZ", lock=True)
        result = self.service.animation(self.character, "left", DEFAULT_SETTINGS, 1, 3)
        self.assertIn(f"|{right}.sx", result["skipped_channels"])
        self.assertEqual(1, cmds.getAttr(f"{right}.scaleX"))
        self.assertEqual(0, cmds.keyframe(f"{right}.scaleX", query=True, keyframeCount=True))
        self.assertEqual(0, cmds.getAttr(f"{right}.rotateZ"))

    def test_animation_rotation_stays_continuous_across_half_turn(self):
        """Euler solutions remain close across a mirrored 180-degree crossing."""
        left, right = self.controls["LeftArm"], self.controls["RightArm"]
        cmds.setKeyframe(left, attribute="rotateY", time=1, value=170,
                         inTangentType="linear", outTangentType="linear")
        cmds.setKeyframe(left, attribute="rotateY", time=3, value=210,
                         inTangentType="linear", outTangentType="linear")
        self.service.animation(self.character, "left", DEFAULT_SETTINGS, 1, 3)
        values = cmds.keyframe(right, attribute="rotateY", query=True, valueChange=True)
        self.assertAlmostEqual(-20, values[1] - values[0])
        self.assertAlmostEqual(-20, values[2] - values[1])

    def test_animation_world_space_and_center(self):
        """World-space samples follow an animated character reference plane."""
        reference = self.controls["Reference"]
        for control in (self.controls["LeftArm"], self.controls["RightArm"]):
            cmds.parent(control, reference)
        self.animate_sides()
        cmds.setKeyframe(reference, attribute="translateX", time=1, value=10)
        cmds.setKeyframe(reference, attribute="translateX", time=3, value=20)
        settings = dict(DEFAULT_SETTINGS, world_space=True)
        self.service.animation(self.character, "left", settings, 1, 3)
        for frame, expected in ((1, 8), (3, 12)):
            cmds.currentTime(frame)
            self.assertAlmostEqual(expected, cmds.xform(
                self.controls["RightArm"], query=True, translation=True, worldSpace=True
            )[0])
        settings = dict(DEFAULT_SETTINGS, affect_center=True)
        self.service.animation(self.character, "flip", settings, 1, 3)
        self.assertEqual([-10, -20], cmds.keyframe(
            reference, attribute="translateX", query=True, time=(1, 3), valueChange=True
        )[::2])

    def test_sampling_range_validation_and_capture_failure(self):
        """General sampling handles subframes, endpoints, invalid input, and failures."""
        from gt.core import anim

        self.assertEqual([1, 1.75, 2.5, 3], anim.get_frame_sample_times(1, 3, 0.75))
        self.assertEqual([2], anim.get_frame_sample_times(2, 2))
        for values in ((3, 1, 1), (1, 3, 0), (1, 3, -1), (1, float("inf"), 1), (1, 1e9, 0.01)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                anim.get_frame_sample_times(*values)
        cmds.currentTime(12)
        with self.assertRaises(RuntimeError):
            anim.sample_animation_range(Mock(side_effect=RuntimeError("capture failure")), 1, 3)
        self.assertEqual(12, cmds.currentTime(query=True))

    def test_empty_cleanup_preserves_control_rigs_and_locked_nodes(self):
        """Only the unprotected empty definition is deleted and Undo restores it."""
        protected = cmds.createNode("HIKCharacterNode", name="protected")
        cmds.lockNode(protected, lock=True)
        self.assertEqual([self.empty], self.service.empty_definitions())
        self.service.delete_empty_definitions([self.empty])
        self.assertTrue(cmds.objExists(self.character))
        self.assertTrue(cmds.objExists(protected))
        self.assertFalse(cmds.objExists(self.empty))
        cmds.undo()
        self.assertTrue(cmds.objExists(self.empty))

    def test_xml_import_and_export_round_trip(self):
        """Native XML mappings can be previewed and connected to real joints."""
        cmds.select(clear=True)
        joint = cmds.joint(name="pelvis")
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "definition.xml")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write('<config_root><match_list><item key="Hips" value="pelvis"/>'
                             '</match_list></config_root>')
            self.assertEqual([("Hips", joint, "Ready")],
                             self.service.preview_definition(self.empty, path, DEFAULT_SETTINGS))
            self.assertEqual(1, self.service.import_definition(self.empty, path, DEFAULT_SETTINGS))
            exported = os.path.join(directory, "export.xml")
            self.service.export_file(self.empty, "definition", exported, DEFAULT_SETTINGS)
            self.assertTrue(os.path.isfile(exported))
        self.assertEqual([joint], cmds.listConnections(f"{self.empty}.Hips", source=True, destination=False))

    def test_properties_export_import(self):
        """Property JSON is usable with real HIK property-state nodes."""
        self.service.runtime()[1].get_hik_property_node(self.character, create_if_missing=True)
        values = self.service.properties(self.character)
        self.assertTrue(values)
        applied = self.service.apply_properties(self.empty, values)
        self.assertEqual(set(values), set(applied))

    def test_qt_controller_actions_cancel_and_error_feedback(self):
        """Builds all tabs and verifies cancellation and errors without modal blocking."""
        from gt.ui import qt_import as ui_qt
        from gt.ui import resource_library
        from gt.tools.anim_hik_utils.anim_hik_utils_view import AnimHikUtilsView
        from gt.tools.anim_hik_utils.anim_hik_utils_controller import AnimHikUtilsController

        app = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication([])
        view = AnimHikUtilsView(version="test")
        model = AnimHikUtilsModel(prefs=False)
        controller = AnimHikUtilsController(model, view, self.service)
        try:
            app.processEvents()
            self.assertEqual(4, view.tabs.count())
            self.assertEqual(ui_qt.QtLib.AlignmentFlag.AlignCenter, view.status_label.alignment())
            self.assertEqual(view.settings_widgets["affect_center"].geometry().y(),
                             view.settings_widgets["world_space"].geometry().y())
            self.assertEqual(set(view.buttons), set(controller.actions))
            self.assertFalse(view.buttons["flip"].isEnabled())
            view.character_combo.setCurrentIndex(view.character_combo.findData(self.character))
            self.assertTrue(view.buttons["flip"].isEnabled())
            with patch.object(controller, "confirm", return_value=False):
                with patch.object(self.service, "animation") as animation:
                    controller.execute("animation_flip")
                    animation.assert_not_called()
            self.assertFalse(ui_qt.QtGui.QIcon(resource_library.Icon.tool_anim_hik_utils).isNull())
            with patch.object(controller, "confirm", return_value=False):
                controller.execute("cleanup")
            self.assertTrue(cmds.objExists(self.empty))
            with patch.object(controller, "file_dialog", return_value=""):
                with patch.object(self.service, "export_file") as export:
                    controller.execute("export_pose")
                    export.assert_not_called()
            with patch.object(self.service, "pose", side_effect=ValueError("No controls changed")):
                with self.assertLogs("gt.tools.anim_hik_utils.anim_hik_utils_controller", level="ERROR"):
                    controller.execute("flip")
            self.assertIn("No controls changed", view.status_label.text())
            # A name removed by a scene change must not silently select another character.
            cmds.delete(self.character)
            controller.execute("refresh")
            self.assertEqual("", model.character)
            self.assertFalse(view.buttons["flip"].isEnabled())
        finally:
            view.close()
            view.deleteLater()
            app.processEvents()


if __name__ == "__main__":
    unittest.main()
