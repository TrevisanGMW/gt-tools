"""Tests for the Shape Text to Curve model."""

import unittest

from gt.tools.shape_text_to_curve import shape_text_to_curve_model as model


class TestShapeTextToCurveModel(unittest.TestCase):
    """Tests pure text parsing, font state, and curve dispatch behavior."""

    def test_parse_text_entries_with_multiple_values(self):
        """Tests parsing and trimming multiple comma-separated entries."""
        expected = ["hello", "world"]
        result = model.parse_text_entries(" hello, world ")
        self.assertEqual(expected, result)

    def test_parse_text_entries_with_newline_separator(self):
        """Tests parsing entries separated by new lines and commas."""
        expected = ["hello", "world", "again"]
        result = model.parse_text_entries("hello\nworld,\nagain")
        self.assertEqual(expected, result)

    def test_parse_text_entries_discards_empty_values(self):
        """Tests that empty comma-separated values are discarded."""
        expected = ["hello", "world"]
        result = model.parse_text_entries(",hello,,,world,")
        self.assertEqual(expected, result)

    def test_parse_text_entries_with_invalid_value(self):
        """Tests that a non-string value produces no entries."""
        expected = []
        result = model.parse_text_entries(None)
        self.assertEqual(expected, result)

    def test_set_font_rejects_empty_value(self):
        """Tests that cancelling the font dialog preserves the current font."""
        text_model = model.ShapeTextToCurveModel(font="Arial|Regular")
        result = text_model.set_font("")
        self.assertFalse(result)
        self.assertEqual("Arial|Regular", text_model.font)

    def test_get_font_display_name(self):
        """Tests extraction of the concise font family name."""
        text_model = model.ShapeTextToCurveModel(font="Arial|Regular")
        self.assertEqual("Arial", text_model.get_font_display_name())

    def test_generate_curves_dispatches_every_entry(self):
        """Tests dispatching every parsed entry through the curve factory."""
        calls = []

        def create_curve(text, font):
            """Records a curve request for the test.

            Args:
                text (str): Requested curve text.
                font (str): Requested font.

            Returns:
                str: Synthetic curve name.
            """
            calls.append((text, font))
            return f"{text}_crv"

        text_model = model.ShapeTextToCurveModel(font="Arial", curve_factory=create_curve)
        expected = ["hello_crv", "world_crv"]
        result = text_model.generate_curves("hello, world")
        self.assertEqual(expected, result)
        self.assertEqual([("hello", "Arial"), ("world", "Arial")], calls)

    def test_generate_curves_skips_empty_input(self):
        """Tests that empty input does not invoke the curve factory."""
        calls = []
        text_model = model.ShapeTextToCurveModel(curve_factory=calls.append)
        expected = []
        result = text_model.generate_curves(" , ")
        self.assertEqual(expected, result)
        self.assertEqual([], calls)


if __name__ == "__main__":
    unittest.main()
