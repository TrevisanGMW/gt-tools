"""Tests for the Color Manager controller."""

import unittest

from gt.tools.color_manager import color_manager_controller


class MockColorModel:
    """Minimal model used to inspect controller color flow."""

    def __init__(self):
        """Initializes mock color state."""
        self.current_color = None
        self.applied_color = None

    @staticmethod
    def prepare_clicked_color(color):
        """Returns the clicked color without conversion.

        Args:
            color (list): Clicked RGB color.

        Returns:
            list: Unchanged RGB color.
        """
        return list(color)

    def set_current_color(self, color):
        """Stores the current color.

        Args:
            color (list): RGB color.
        """
        self.current_color = list(color)

    def apply_color(self, reset=False):
        """Records the color used by apply.

        Args:
            reset (bool, optional): Whether the operation resets colors.
        """
        self.applied_color = None if reset else list(self.current_color)


class MockColorView:
    """Minimal view used to inspect controller color flow."""

    def __init__(self):
        """Initializes mock view state."""
        self.controller = None
        self.current_color = None

    def set_current_color(self, color):
        """Stores the displayed current color.

        Args:
            color (list): RGB color.
        """
        self.current_color = list(color)

    def get_current_color(self):
        """Gets the displayed color.

        Returns:
            list: RGB color.
        """
        return list(self.current_color)


class TestColorManagerController(unittest.TestCase):
    """Tests current-color consistency in controller operations."""

    def test_preset_color_remains_the_clicked_color(self):
        """Tests that preset display state is not altered by outliner conversion."""
        color_model = MockColorModel()
        color_view = MockColorView()
        controller = color_manager_controller.ColorManagerController(color_model, color_view)
        clicked_color = [0.25, 0.5, 0.75]

        controller.apply_preset_color(clicked_color)

        self.assertEqual(clicked_color, color_model.current_color)
        self.assertEqual(clicked_color, color_view.current_color)


if __name__ == "__main__":
    unittest.main()
