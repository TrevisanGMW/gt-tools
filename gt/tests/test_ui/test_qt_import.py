"""Tests for the shared PySide compatibility imports."""

import importlib.util
import sys
import types
import unittest
from unittest import mock

import gt.ui.qt_import as ui_qt


class TestQtImport(unittest.TestCase):
    """Tests optional Qt imports and active binding version detection."""

    def test_import_optional_qt_module_returns_module(self):
        """Returns the imported module when the optional Qt module exists."""
        expected = mock.MagicMock()
        with mock.patch("gt.ui.qt_import.importlib.import_module", return_value=expected):
            result = ui_qt._import_optional_qt_module(ui_qt.PySide, "QtTest")

        self.assertEqual(expected, result)

    def test_import_optional_qt_module_returns_none_when_unavailable(self):
        """Returns None when the optional Qt module is not bundled with PySide."""
        with mock.patch("gt.ui.qt_import.importlib.import_module", side_effect=ImportError):
            result = ui_qt._import_optional_qt_module(ui_qt.PySide, "QtTest")

        self.assertIsNone(result)

    def test_get_pyside_version_returns_loaded_binding_version(self):
        """Returns the loaded binding's complete version without normalization."""
        for package_name, expected in (
            ("PySide2", "5.15.2.1"),
            ("PySide6", "6.8.3"),
            ("PySide6", "6.8.3rc1"),
        ):
            with self.subTest(package=package_name, version=expected):
                binding = types.ModuleType(package_name)
                binding.__version__ = expected
                with mock.patch.object(ui_qt, "PySide", binding):
                    self.assertEqual(expected, ui_qt.get_pyside_version())

    def test_get_pyside_version_returns_major_version(self):
        """Preserves the major-only string result for both supported bindings."""
        for package_name, version, expected in (
            ("PySide2", "5.15.2.1", "5"),
            ("PySide6", "6.8.3rc1", "6"),
        ):
            with self.subTest(package=package_name):
                binding = types.ModuleType(package_name)
                binding.__version__ = version
                with mock.patch.object(ui_qt, "PySide", binding):
                    self.assertEqual(expected, ui_qt.get_pyside_version(major_only=True))

    def test_get_pyside_version_returns_none_when_version_missing(self):
        """Returns None when the active binding has no version attribute."""
        with mock.patch.object(ui_qt, "PySide", types.ModuleType("PySide6")):
            self.assertIsNone(ui_qt.get_pyside_version())
            self.assertIsNone(ui_qt.get_pyside_version(major_only=True))

    def test_get_pyside_version_returns_none_when_version_empty(self):
        """Returns None when the active binding exposes an empty version."""
        binding = types.ModuleType("PySide6")
        binding.__version__ = ""
        with mock.patch.object(ui_qt, "PySide", binding):
            self.assertIsNone(ui_qt.get_pyside_version())
            self.assertIsNone(ui_qt.get_pyside_version(major_only=True))

    def test_get_pyside_version_does_not_import_other_bindings(self):
        """Reads the active binding without probing other installed bindings."""
        expected = ui_qt.PySide.__version__
        with mock.patch.object(ui_qt.importlib, "import_module") as import_module:
            self.assertEqual(expected, ui_qt.get_pyside_version())
        import_module.assert_not_called()

    def test_import_without_package_metadata_dependencies(self):
        """Imports Qt and reads its version without package metadata helpers."""
        module_spec = importlib.util.spec_from_file_location("qt_import_without_metadata", ui_qt.__file__)
        qt_module = importlib.util.module_from_spec(module_spec)
        unavailable_modules = {"pkg_resources": None, "importlib.metadata": None}
        with mock.patch.dict(sys.modules, unavailable_modules):
            module_spec.loader.exec_module(qt_module)
            self.assertIs(ui_qt.PySide, qt_module.PySide)
            self.assertEqual(ui_qt.PySide.__version__, qt_module.get_pyside_version())
