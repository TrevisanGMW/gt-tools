"""Tests for the Auto Rigger Python module attribute widget."""

import logging
import sys
import unittest

import gt.ui.qt_import as ui_qt
import gt.tools.auto_rigger.attr_widgets.attr_widget_base as attr_widget_base
import gt.tools.auto_rigger.attr_widgets.attr_widgets as attr_widgets
from gt.tools.auto_rigger.attr_widgets.attr_widget_python import AttrWidgetModulePython
from gt.tools.auto_rigger.modules.module_utils import ModulePython
from gt.tools.auto_rigger.rigger_controller import get_module_attr_widgets
from gt.tools.auto_rigger.rig_framework import RigProject


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestAttrWidgetModulePython(unittest.TestCase):
    """Tests the Auto Rigger Python module attribute widget."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application when one does not already exist."""
        application = ui_qt.QtWidgets.QApplication.instance()
        if not application:
            cls.application = ui_qt.QtWidgets.QApplication(sys.argv)
        else:
            cls.application = application

    def setUp(self):
        """Creates an Auto Rigger project and Python module widget."""
        self.module = ModulePython()
        self.project = RigProject()
        self.project.add_to_modules(self.module)
        self.widget = AttrWidgetModulePython(module=self.module, project=self.project)

    def tearDown(self):
        """Closes the Python module widget after each test."""
        self.widget.close()

    def test_python_editor_includes_line_number_gutter(self):
        """Ensures the Python editor is registered with the shared number bar."""
        result = self.widget.python_editor_widget.number_bar.text_edit

        expected = self.widget.python_edit
        self.assertIs(expected, result)

    def test_python_widget_uses_its_own_module(self):
        """Ensures the controller resolves the Python widget implementation."""
        result = attr_widgets.AttrWidgetModulePython
        expected = AttrWidgetModulePython
        self.assertIs(expected, result)
        self.assertEqual(
            "gt.tools.auto_rigger.attr_widgets.attr_widget_python",
            result.__module__,
        )
        self.assertFalse(hasattr(attr_widget_base, "AttrWidgetModulePython"))
        self.assertIs(expected, get_module_attr_widgets(self.module))

    def test_python_editor_includes_placeholder(self):
        """Ensures an empty Python editor explains its intended use."""
        result = self.widget.python_edit.placeholderText()
        expected = "Write Python code to run when this module executes."
        self.assertEqual(expected, result)

    def test_font_size_slider_resizes_python_code(self):
        """Ensures the font size slider updates the visible Python code size."""
        self.widget.python_edit.setPlainText("print('font size')")
        document = self.widget.python_edit.document()
        expected = document.documentLayout().blockBoundingRect(document.firstBlock()).height()

        self.widget.font_size_slider.setValue(20)
        self.application.processEvents()

        result = document.documentLayout().blockBoundingRect(document.firstBlock()).height()
        self.assertGreater(result, expected)
        self.assertEqual(20, self.module.font_size)


if __name__ == "__main__":
    unittest.main()
