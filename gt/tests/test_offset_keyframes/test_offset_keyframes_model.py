"""Unit tests for the pure Offset Keyframes model."""

import unittest

from gt.tools.offset_keyframes.offset_keyframes_model import (
    OffsetKeyframesModel,
    SCOPE_CURRENT,
    SCOPE_PLAYBACK,
)


class TestOffsetKeyframesModel(unittest.TestCase):
    """Tests Offset Keyframes settings behavior."""

    def test_set_settings_updates_valid_values(self):
        model = OffsetKeyframesModel()

        model.set_settings(
            {
                "offset_amount": 2.5,
                "scope": SCOPE_CURRENT,
                "stagger_step": 3,
                "apply_euler_filter": True,
            }
        )

        expected = {
            "offset_amount": 2.5,
            "scope": SCOPE_CURRENT,
            "stagger_step": 3.0,
            "apply_euler_filter": True,
        }
        self.assertEqual(expected, model.get_settings())

    def test_set_settings_keeps_previous_scope_when_invalid(self):
        model = OffsetKeyframesModel()
        model.scope = SCOPE_PLAYBACK

        model.set_settings({"scope": "unknown"})

        self.assertEqual(SCOPE_PLAYBACK, model.scope)


if __name__ == "__main__":
    unittest.main()
