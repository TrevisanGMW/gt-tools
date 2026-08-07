"""Tests for the Maya-free Render Calculator model."""

import unittest

from gt.tools.render_calculator.render_calculator_controller import (
    RenderCalculatorController,
)
from gt.tools.render_calculator import render_calculator_model


class MemoryPrefs:
    """In-memory preference object matching the model's Prefs interface."""

    def __init__(self):
        """Initializes an empty preference dictionary."""
        self.values = {}

    def get_raw_preferences(self):
        """Returns a copy of the stored preference values.

        Returns:
            dict: Stored preference values.
        """
        return dict(self.values)

    def set_raw_preferences(self, values):
        """Replaces the stored preference values.

        Args:
            values (dict): New preference values.
        """
        self.values = dict(values)

    def save(self):
        """Matches Prefs.save without writing to disk."""


class FakeMayaCommands:
    """Minimal Maya command stub for timeline tests."""

    def playbackOptions(self, **kwargs):
        """Returns a synthetic playback boundary.

        Args:
            **kwargs: Maya playback query flags.

        Returns:
            int: Synthetic start or end frame.
        """
        if kwargs.get("min"):
            return 10
        if kwargs.get("max"):
            return 34
        raise RuntimeError("Unsupported playback query.")


class FakeRenderCalculatorView:
    """Minimal view stub for controller timeline tests."""

    def __init__(self):
        """Initializes values recorded by the controller."""
        self.frame_count = None
        self.status = None
        self.result_text = None

    def set_frame_count(self, frame_count):
        """Records the frame count assigned by the controller.

        Args:
            frame_count (int): Frame count to display.
        """
        self.frame_count = frame_count

    def set_status(self, message, is_error=False):
        """Records controller status feedback.

        Args:
            message (str): Status message.
            is_error (bool): Whether the message is an error.
        """
        self.status = (message, is_error)

    def set_result_text(self, text):
        """Records the refreshed result text.

        Args:
            text (str): Result text.
        """
        self.result_text = text


class TestRenderCalculatorModel(unittest.TestCase):
    """Tests calculator math and summary formatting."""

    def setUp(self):
        """Creates isolated in-memory preferences for each test."""
        self.preferences = MemoryPrefs()

    def test_calculate_render_time_formats_multiple_units(self):
        """Formats a duration using calendar units."""
        expected = " 1 hour\n 2 minutes\n 3 seconds\n"
        result = render_calculator_model.calculate_render_time(
            3723,
            unit="seconds",
        )
        self.assertEqual(expected, result)

    def test_calculate_render_time_divides_work_between_machines(self):
        """Divides total render work by the number of machines."""
        expected = " 30 seconds\n"
        result = render_calculator_model.calculate_render_time(
            60,
            num_frames=2,
            num_machines=4,
            unit="seconds",
        )
        self.assertEqual(expected, result)

    def test_model_summary_includes_per_machine_note(self):
        """Includes distribution details when multiple machines are used."""
        model = render_calculator_model.RenderCalculatorModel(
            time_per_frame=1,
            num_frames=10,
            num_machines=2,
            unit="Minute(s)",
            preferences=self.preferences,
        )
        result = model.get_render_summary()
        self.assertIn("Time per frame 1 minute(s)", result)
        self.assertIn("Frame Count 10 frames(s)", result)
        self.assertIn("Per computer (Number of computers: 2)", result)

    def test_model_normalizes_display_unit(self):
        """Accepts the labels used by the view and stores calculation keys."""
        model = render_calculator_model.RenderCalculatorModel(
            unit="Hour(s)",
            preferences=self.preferences,
        )
        self.assertEqual("hours", model.unit)
        self.assertEqual("Hour(s)", model.get_unit_label())

    def test_model_persists_all_values(self):
        """Restores numeric values and unit from the preference object."""
        model = render_calculator_model.RenderCalculatorModel(
            preferences=self.preferences,
        )
        model.set_time_per_frame(12)
        model.set_num_frames(48)
        model.set_num_machines(3)
        model.set_unit("Hour(s)")

        restored_model = render_calculator_model.RenderCalculatorModel(
            preferences=self.preferences,
        )

        self.assertEqual(12, restored_model.time_per_frame)
        self.assertEqual(48, restored_model.num_frames)
        self.assertEqual(3, restored_model.num_machines)
        self.assertEqual("hours", restored_model.unit)

    def test_reset_numbers_restores_defaults_and_persists(self):
        """Resets all inputs to their defaults and persists the values."""
        model = render_calculator_model.RenderCalculatorModel(
            time_per_frame=12,
            num_frames=48,
            num_machines=3,
            unit="Hour(s)",
            preferences=self.preferences,
        )

        model.reset_numbers()

        self.assertEqual(1, model.time_per_frame)
        self.assertEqual(1, model.num_frames)
        self.assertEqual(1, model.num_machines)
        self.assertEqual("seconds", model.unit)
        self.assertEqual(1, self.preferences.values["num_frames"])
        self.assertEqual("seconds", self.preferences.values["unit"])

    def test_controller_loads_current_timeline_range(self):
        """Loads the inclusive Maya playback range into the model and view."""
        model = render_calculator_model.RenderCalculatorModel(
            num_frames=1,
            preferences=self.preferences,
        )
        view = FakeRenderCalculatorView()
        controller = RenderCalculatorController.__new__(RenderCalculatorController)
        controller.model = model
        controller.view = view
        controller._maya_cmds = FakeMayaCommands()

        controller.get_current_frame_count()

        self.assertEqual(25, model.num_frames)
        self.assertEqual(25, view.frame_count)
        self.assertEqual(("", False), view.status)


if __name__ == "__main__":
    unittest.main()
