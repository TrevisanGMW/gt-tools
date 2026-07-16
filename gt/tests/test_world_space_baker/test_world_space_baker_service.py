"""Unit tests for World Space Baker Maya runtime orchestration."""

import unittest
from unittest import mock

from gt.tools.world_space_baker.world_space_baker_service import WorldSpaceBakerService


class TestWorldSpaceBakerService(unittest.TestCase):
    """Tests extraction and bake calls with a maya.cmds test double."""

    def test_extract_samples_animatable_channels_and_restores_scene_state(self):
        """Samples every inclusive frame and restores time and refresh."""
        cmds = mock.MagicMock()
        cmds.objExists.return_value = True
        cmds.currentTime.side_effect = [42, None, None, None, 42]
        cmds.listAnimatable.return_value = ["|ctrl.translateX", "|ctrl.rotateY"]
        cmds.xform.side_effect = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, 12.0],
        ]
        service = WorldSpaceBakerService(cmds_module=cmds)

        result = service.extract(["|ctrl"], 1, 2)

        expected = {
            "|ctrl": {
                "translate": [[1, [1.0, 2.0, 3.0]], [2, [7.0, 8.0, 9.0]]],
                "rotate": [[1, [4.0, 5.0, 6.0]], [2, [10.0, 11.0, 12.0]]],
            }
        }
        self.assertEqual(expected, result)
        cmds.currentTime.assert_any_call(42)
        self.assertEqual([mock.call(suspend=True), mock.call(suspend=False)], cmds.refresh.call_args_list)

    def test_extract_skips_missing_targets(self):
        """Returns no data when every loaded target is missing."""
        cmds = mock.MagicMock()
        cmds.objExists.return_value = False
        service = WorldSpaceBakerService(cmds_module=cmds)

        result = service.extract(["|missing"], 1, 2)

        self.assertEqual({}, result)
        cmds.refresh.assert_not_called()

    def test_bake_keys_translate_and_rotate_in_one_undo_chunk(self):
        """Applies all stored channels and restores time and refresh."""
        cmds = mock.MagicMock()
        cmds.currentTime.return_value = 15
        cmds.objExists.return_value = True
        service = WorldSpaceBakerService(cmds_module=cmds)
        animation_data = {
            "|ctrl": {
                "translate": [[1, [1.0, 2.0, 3.0]]],
                "rotate": [[1, [4.0, 5.0, 6.0]]],
            }
        }

        result = service.bake(animation_data)

        self.assertEqual({"baked": 1, "missing": 0}, result)
        self.assertEqual(2, cmds.setKeyframe.call_count)
        cmds.undoInfo.assert_has_calls(
            [
                mock.call(openChunk=True, chunkName="World Space Baker"),
                mock.call(closeChunk=True, chunkName="World Space Baker"),
            ]
        )
        cmds.currentTime.assert_any_call(15)
        self.assertEqual([mock.call(suspend=True), mock.call(suspend=False)], cmds.refresh.call_args_list)

    def test_bake_counts_missing_targets_without_keying(self):
        """Skips deleted objects and reports them to the controller."""
        cmds = mock.MagicMock()
        cmds.currentTime.return_value = 15
        cmds.objExists.return_value = False
        service = WorldSpaceBakerService(cmds_module=cmds)

        result = service.bake({"|missing": {"translate": [[1, [0, 0, 0]]]}})

        self.assertEqual({"baked": 0, "missing": 1}, result)
        cmds.xform.assert_not_called()
        cmds.setKeyframe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
