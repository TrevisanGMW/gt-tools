"""Tests for the shared PySide compatibility imports."""

import unittest
from unittest import mock

import gt.ui.qt_import as ui_qt


class TestQtImport(unittest.TestCase):
    """Tests optional Qt module imports."""

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
