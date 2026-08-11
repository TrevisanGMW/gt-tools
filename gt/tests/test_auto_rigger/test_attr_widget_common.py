"""Tests Auto Rigger fallback attribute widget imports."""

import unittest

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import AttrWidgetCommon
import gt.tools.auto_rigger.attr_widgets.attr_widgets as attr_widgets


class TestAttrWidgetCommonImports(unittest.TestCase):
    """Tests fallback widget resolution."""

    def test_common_widget_comes_from_base_module(self):
        """Ensures the fallback widget is sourced from the base module."""
        result = attr_widgets.AttrWidgetCommon

        expected = AttrWidgetCommon
        self.assertIs(expected, result)
        self.assertEqual(
            "gt.tools.auto_rigger.attr_widgets.attr_widget_base",
            result.__module__,
        )


if __name__ == "__main__":
    unittest.main()
