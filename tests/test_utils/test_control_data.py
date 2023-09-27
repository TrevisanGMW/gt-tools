import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils.data.controls.control_data import ControlData
from gt.utils.data.controls import cluster_driven
from gt.utils.data.controls import slider


class TestControlData(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    # ------------------------------- Test ControlData Start -------------------------------

    def test_init(self):
        expected_name = "control_name"
        control = ControlData(name=expected_name)
        self.assertEqual(expected_name, control.name)
        self.assertIsNone(control.offset)
        self.assertIsNone(control.setup)
        self.assertEqual([expected_name], control.drivers)
        self.assertEqual([], control.inputs)
        self.assertEqual([], control.outputs)
        self.assertIsNone(control.metadata)

    def test_set_name(self):
        expected_new_name = "new_name"
        control = ControlData(name="control_name")
        control.set_name(name=expected_new_name)
        self.assertEqual(expected_new_name, control.name)

    def test_set_offset(self):
        expected_offset = "offset_transform"
        control = ControlData(name="control_name")
        control.set_offset(offset=expected_offset)
        self.assertEqual(expected_offset, control.offset)

    def test_set_setup(self):
        expected_setup = "setup_transform"
        control = ControlData(name="control_name")
        control.set_setup(setup=expected_setup)
        self.assertEqual(expected_setup, control.setup)

    def test_set_drivers(self):
        expected_driver_1 = "driver_1"
        expected_driver_2 = "driver_2"
        control = ControlData(name="control_name")
        control.set_drivers(drivers=expected_driver_1)
        self.assertEqual([expected_driver_1], control.drivers)
        control.set_drivers(drivers=[expected_driver_1, expected_driver_2])
        self.assertEqual([expected_driver_1, expected_driver_2], control.drivers)

    def test_set_inputs(self):
        expected_inputs = ["input_attr_1", "input_attr_2"]
        control = ControlData(name="control_name")
        control.set_inputs(inputs=expected_inputs)
        self.assertEqual(expected_inputs, control.inputs)

    def test_set_outputs(self):
        expected_outputs = ["output_attr_1", "output_attr_2"]
        control = ControlData(name="control_name")
        control.set_outputs(outputs=expected_outputs)
        self.assertEqual(expected_outputs, control.outputs)

    def test_set_metadata(self):
        expected_metadata = {"key": "value"}
        control = ControlData(name="control_name")
        control.set_metadata(new_metadata=expected_metadata)
        self.assertEqual(expected_metadata, control.metadata)

    def test_add_to_metadata(self):
        control = ControlData(name="control_name")
        control.set_metadata(new_metadata={"key_one": "value_one"})
        control.add_to_metadata(key="key_two", value="value_two")
        expected_metadata = {"key_one": "value_one", "key_two": "value_two"}
        self.assertEqual(expected_metadata, control.metadata)

    def test_get_name(self):
        expected_name = "control_name"
        control = ControlData(name=expected_name)
        self.assertEqual(expected_name, control.get_name())

    def test_get_short_name(self):
        expected_name = "control_name"
        control = ControlData(name=expected_name)
        self.assertEqual(expected_name, control.get_short_name())

    def test_get_offset(self):
        expected_offset = "offset_transform"
        control = ControlData(name="control_name", offset=expected_offset)
        self.assertEqual(expected_offset, control.get_offset())

    def test_get_setup(self):
        expected_setup = "setup_transform"
        control = ControlData(name="control_name", setup=expected_setup)
        self.assertEqual(expected_setup, control.get_setup())

    def test_get_drivers(self):
        expected_drivers = ["driver_1", "driver_2"]
        control = ControlData(name="control_name", drivers=expected_drivers)
        self.assertEqual(expected_drivers, control.get_drivers())

    def test_get_inputs(self):
        expected_inputs = ["input_attr_1", "input_attr_2"]
        control = ControlData(name="control_name", inputs=expected_inputs)
        self.assertEqual(expected_inputs, control.get_inputs())

    def test_get_outputs(self):
        expected_outputs = ["output_attr_1", "output_attr_2"]
        control = ControlData(name="control_name", outputs=expected_outputs)
        self.assertEqual(expected_outputs, control.get_outputs())

    def test_get_metadata(self):
        expected_metadata = {"key": "value"}
        control = ControlData(name="control_name", metadata=expected_metadata)
        self.assertEqual(expected_metadata, control.get_metadata())

    # ------------------------------- Test ControlData End -------------------------------

    def test_create_scalable_two_sides_arrow(self):
        result = cluster_driven.create_scalable_two_sides_arrow("mocked_scalable_arrow")
        expected = "mocked_scalable_arrow"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_slider_squared_one_dimension(self):
        expected = "mocked_slider_one_dimension"
        result = slider.create_slider_squared_one_dimension(name=expected)
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_slider_squared_two_dimensions(self):
        expected = "mocked_create_slider_squared_two_dimensions"
        result = slider.create_slider_squared_two_dimensions(name=expected)
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_sliders_squared_mouth(self):
        result = slider.create_sliders_squared_mouth(name="mocked_mouth")
        expected = "mocked_mouth_gui_grp"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_sliders_squared_eyebrows(self):
        result = slider.create_sliders_squared_eyebrows(name="mocked_eyebrow")
        expected = "mocked_eyebrow_gui_grp"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_sliders_squared_cheek_nose(self):
        result = slider.create_sliders_squared_cheek_nose(name="mocked_nose_cheek")
        expected = "mocked_nose_cheek_gui_grp"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_sliders_squared_eye(self):
        result = slider.create_sliders_squared_eyes(name="mocked_eyes")
        expected = "mocked_eyes_gui_grp"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_create_sliders_squared_facial_side_gui(self):
        result = slider.create_sliders_squared_facial_side_gui(name="mocked_facial")
        expected = "mocked_facial_gui_grp"
        self.assertEqual(expected, result.name)
        self.assertIsInstance(result, ControlData)

    def test_offset_slider_range(self):
        offset_ctrl = slider.create_slider_squared_one_dimension('offset_ctrl')
        expected = 5
        for driver in offset_ctrl.drivers:
            min_trans_y_limit = maya_test_tools.cmds.getAttr(f'{driver}.minTransYLimit')
            max_trans_y_limit = maya_test_tools.cmds.getAttr(f'{driver}.maxTransYLimit')
            self.assertEqual(expected, max_trans_y_limit)
            self.assertEqual(-expected, min_trans_y_limit)
        slider._offset_slider_range(slider_control_data=offset_ctrl, offset_by=5, offset_thickness=1)
        expected = 10
        for driver in offset_ctrl.drivers:
            min_trans_y_limit = maya_test_tools.cmds.getAttr(f'{driver}.minTransYLimit')
            max_trans_y_limit = maya_test_tools.cmds.getAttr(f'{driver}.maxTransYLimit')
            self.assertEqual(expected, max_trans_y_limit)
            self.assertEqual(-expected, min_trans_y_limit)
