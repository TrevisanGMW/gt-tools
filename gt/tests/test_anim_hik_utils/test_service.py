"""HumanIK adapter safety and failure regressions using injected dependencies."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from gt.tools.anim_hik_utils.anim_hik_utils_model import DEFAULT_SETTINGS
from gt.tools.anim_hik_utils.anim_hik_utils_service import AnimHikUtilsService


class TestAnimHikUtilsService(unittest.TestCase):
    """Verifies adapter behavior independently of Maya or Qt."""

    def setUp(self):
        """Builds a minimal runtime double with two characters."""
        self.cmds = Mock()
        self.hik = Mock()
        self.hik.get_hik_characters.return_value = ["hero", "source"]
        self.cmds.referenceQuery.return_value = False
        self.cmds.lockNode.return_value = [False]
        self.cmds.listConnections.return_value = []
        self.cmds.ls.return_value = ["selected"]
        self.cmds.objExists.return_value = True
        self.cmds.currentTime.return_value = 12.0
        self.cmds.autoKeyframe.return_value = True
        self.service = AnimHikUtilsService(self.cmds, self.hik)

    def test_scene_state_restored_after_pose_failure(self):
        """A failing pose still closes Undo and restores auto-key, time, and selection."""
        self.hik.flip_hik_pose.side_effect = RuntimeError("failure")
        with self.assertRaisesRegex(RuntimeError, "failure"):
            self.service.pose("hero", "flip", DEFAULT_SETTINGS)
        self.cmds.autoKeyframe.assert_called_with(state=True)
        self.cmds.currentTime.assert_called_with(query=True)
        self.cmds.select.assert_called_with(["selected"], replace=True)
        self.cmds.undoInfo.assert_called_with(closeChunk=True)

    def test_pose_import_respects_file_space(self):
        """The mirror option cannot reinterpret a saved pose's coordinate space."""
        self.service.pose("hero", "import", DEFAULT_SETTINGS, "pose.json")
        self.hik.import_hik_pose.assert_called_once_with("hero", "pose.json", world_space=None)

    def test_stale_character_rejected_before_mutation(self):
        """A deleted character never falls back to a similarly named target."""
        with self.assertRaises(ValueError):
            self.service.pose("deleted", "left", DEFAULT_SETTINGS)
        self.hik.mirror_hik_pose.assert_not_called()
        self.cmds.undoInfo.assert_not_called()

    def test_source_cycles_rejected(self):
        """Direct and transitive source cycles are refused before native commands."""
        self.cmds.listConnections.return_value = ["hero"]
        for source in ("hero", "source"):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, "cycle"):
                self.service.definition_action("hero", "source", source)
        self.hik.set_definition_source.assert_not_called()

    def test_protected_definition_rejected(self):
        """Referenced definitions cannot be renamed through the tool."""
        self.cmds.referenceQuery.return_value = True
        with self.assertRaisesRegex(ValueError, "referenced"):
            self.service.definition_action("hero", "rename", "new_name")
        self.hik.rename_definition.assert_not_called()

    def test_failed_export_preserves_existing_destination(self):
        """Failed exports cannot truncate an existing user file."""
        self.hik.export_hik_pose.return_value = False
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "pose.json")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("existing")
            with self.assertRaises(RuntimeError):
                self.service.export_file("hero", "pose", path, DEFAULT_SETTINGS)
            with open(path, "r", encoding="utf-8") as stream:
                self.assertEqual("existing", stream.read())
            self.assertEqual(["pose.json"], os.listdir(directory))

    def test_cleanup_deletes_only_approved_candidates(self):
        """New empty nodes found after preview are not silently included."""
        with patch.object(self.service, "empty_definitions", return_value=["hero", "new_empty"]):
            self.assertEqual(1, self.service.delete_empty_definitions(["hero"]))
        self.cmds.delete.assert_called_once_with(["hero"])

    def test_cleanup_rechecks_candidates_before_delete(self):
        """A definition connected after preview prevents the cleanup operation."""
        with patch.object(self.service, "empty_definitions", return_value=[]):
            with self.assertRaises(ValueError):
                self.service.delete_empty_definitions(["hero"])
        self.cmds.delete.assert_not_called()

    def test_xml_preview_does_not_mutate_scene(self):
        """Missing bones are reported before unlocking or connecting a definition."""
        self.hik.HIK_CHARACTERIZE_KEYS = ("Hips",)
        self.cmds.ls.return_value = []
        with patch("gt.tools.anim_hik_utils.anim_hik_utils_model.read_definition",
                   return_value=[("Hips", "missing")]):
            self.assertEqual([("Hips", "missing", "Missing")],
                             self.service.preview_definition("hero", "unused.xml", DEFAULT_SETTINGS))
            with self.assertRaises(ValueError):
                self.service.import_definition("hero", "unused.xml", DEFAULT_SETTINGS)
        self.hik.import_definition_from_xml.assert_not_called()


if __name__ == "__main__":
    unittest.main()
