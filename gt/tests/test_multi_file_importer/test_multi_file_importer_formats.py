import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.tools.multi_file_importer import multi_file_importer_formats as formats


class CustomFormat(formats.FormatBase):
    """Format used to test registration."""

    key = "test_custom_format"
    label = "Custom"
    extensions = (".customfmt",)


class TestMultiFileImporterFormats(unittest.TestCase):
    """Checks the format registry and option handling."""

    def test_registry_resolves_builtin_formats(self):
        expected = {"a.ma": "maya_scene", "b.MB": "maya_scene", "c.fbx": "fbx", "d.usda": "usd", "e.bvh": "bvh",
                    "f.npz": "numpy_points", "g.abc": "alembic", "h.obj": "obj"}
        result = {path: formats.get_format_for_path(path).key for path in expected}
        self.assertEqual(expected, result)
        self.assertIsNone(formats.get_format_for_path("notes.txt"))

    def test_fallback_format_is_last(self):
        self.assertEqual("maya_translator", formats.get_formats()[-1].key)

    def test_register_and_unregister(self):
        self.assertTrue(formats.register_format(CustomFormat(), replace=True))
        self.assertEqual("test_custom_format", formats.get_format_for_path("x.customfmt").key)
        self.assertEqual("maya_translator", formats.get_formats()[-1].key)
        self.assertFalse(formats.register_format(CustomFormat()))
        with self.assertRaises(ValueError):
            formats.register_format(object())
        self.assertTrue(formats.unregister_format("test_custom_format"))
        self.assertIsNone(formats.get_format_for_path("x.customfmt"))

    def test_normalize_settings(self):
        file_format = formats.get_format("bvh")
        expected = {"scale": 0.0001, "start_frame": 1.0, "time_mode": "Real Time", "include_end_sites": False}
        result = file_format.normalize_settings({"scale": -5, "time_mode": "bad", "include_end_sites": 0, "old": 1})
        self.assertEqual(expected, result)

    def test_translator_extensions(self):
        expected = [".ma", ".mb"]
        self.assertEqual(expected, formats.parse_translator_extensions("*.ma;*.MB;*.*"))

    def test_every_format_has_valid_defaults(self):
        for file_format in formats.get_formats():
            defaults = {option.key: option.default for option in file_format.get_options()}
            self.assertEqual(defaults, file_format.normalize_settings({}), file_format.key)
