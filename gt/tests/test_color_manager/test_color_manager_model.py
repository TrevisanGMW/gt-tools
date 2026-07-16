"""Tests for Color Manager color conversion behavior."""

import unittest
from unittest.mock import patch

from gt.tools.color_manager import color_manager_model


class MockMayaCmds:
    """Records Maya attribute edits used by drawing override application."""

    def __init__(self):
        """Initializes recorded attribute values."""
        self.attributes = {}

    @staticmethod
    def getAttr(attribute):
        """Returns a disabled state for queried color systems.

        Args:
            attribute (str): Maya attribute name.

        Returns:
            int: Disabled state.
        """
        return 0

    def setAttr(self, attribute, value):
        """Records an attribute edit.

        Args:
            attribute (str): Maya attribute name.
            value (int or float): Assigned value.
        """
        self.attributes[attribute] = value

    @staticmethod
    def color(*args, **kwargs):
        """Provides the Maya color command used by reset guards.

        Args:
            *args: Positional Maya command arguments.
            **kwargs: Keyword Maya command arguments.
        """


class TestColorManagerModel(unittest.TestCase):
    """Tests the colors derived for the Current Color representation modes."""

    @staticmethod
    def create_model():
        """Creates a model without initializing persistent preferences.

        Returns:
            ColorManagerModel: Model configured with default conversion settings.
        """
        color_model = color_manager_model.ColorManagerModel.__new__(color_manager_model.ColorManagerModel)
        color_model.current_color = [0.3, 0.3, 0.3]
        color_model.current_color_mode = color_manager_model.CURRENT_COLOR_UNCONVERTED
        color_model.auto_adjust_outliner_to_viewport = True
        color_model.auto_adjust_viewport_to_outliner = True
        return color_model

    def test_unconverted_clicked_color_is_converted_for_viewport(self):
        """Tests that an unconverted swatch uses the Outliner-to-Viewport rule."""
        color_model = self.create_model()
        color_model.current_color = [1.0, 0.45, 0.15]
        expected = color_manager_model.convert_color_from_outliner(color_model.current_color)

        result = color_model.get_viewport_color()

        self.assertEqual(expected, result)

    def test_outliner_to_viewport_can_be_disabled(self):
        """Tests that disabling Outliner-to-Viewport preserves the current RGB values."""
        color_model = self.create_model()
        color_model.current_color = [0.25, 0.5, 0.75]
        color_model.auto_adjust_outliner_to_viewport = False

        result = color_model.get_viewport_color()

        self.assertEqual(color_model.current_color, result)

    def test_viewport_to_outliner_uses_derived_viewport_color(self):
        """Tests that both directional rules are respected during Outliner application."""
        color_model = self.create_model()
        color_model.current_color = [1.0, 0.45, 0.15]
        viewport_color = color_manager_model.convert_color_from_outliner(color_model.current_color)
        expected = color_manager_model.convert_color_for_outliner(viewport_color)

        result = color_model.get_outliner_color()

        self.assertEqual(expected, result)

    def test_viewport_to_outliner_can_be_disabled(self):
        """Tests that disabling Viewport-to-Outliner keeps the derived viewport RGB values."""
        color_model = self.create_model()
        color_model.current_color = [0.25, 0.5, 0.75]
        color_model.auto_adjust_viewport_to_outliner = False
        expected = color_model.get_viewport_color()

        result = color_model.get_outliner_color()

        self.assertEqual(expected, result)

    def test_converted_mode_populates_current_color_with_viewport_value(self):
        """Tests the optional converted Current Color representation."""
        color_model = self.create_model()
        color_model.current_color_mode = color_manager_model.CURRENT_COLOR_CONVERTED
        clicked_color = [1.0, 0.45, 0.15]
        expected = color_manager_model.convert_color_from_outliner(clicked_color)

        result = color_model.prepare_clicked_color(clicked_color)

        self.assertEqual(expected, result)

    def test_unconverted_mode_populates_current_color_with_clicked_value(self):
        """Tests that the default Current Color matches the clicked swatch."""
        color_model = self.create_model()
        clicked_color = [1.0, 0.45, 0.15]

        result = color_model.prepare_clicked_color(clicked_color)

        self.assertEqual(clicked_color, result)

    def test_drawing_override_applies_derived_viewport_color(self):
        """Tests that viewport application uses the Outliner-to-Viewport result."""
        color_model = self.create_model()
        color_model.current_color = [1.0, 0.45, 0.15]
        expected = color_model.get_viewport_color()
        maya_cmds = MockMayaCmds()

        with patch.object(color_manager_model, "get_maya_cmds", return_value=maya_cmds):
            color_model._set_drawing_override_color("cube")

        self.assertEqual(expected[0], maya_cmds.attributes["cube.overrideColorR"])
        self.assertEqual(expected[1], maya_cmds.attributes["cube.overrideColorG"])
        self.assertEqual(expected[2], maya_cmds.attributes["cube.overrideColorB"])


if __name__ == "__main__":
    unittest.main()
