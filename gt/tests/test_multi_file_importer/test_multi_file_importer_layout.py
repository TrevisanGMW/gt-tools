import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_layout as layout


class TestMultiFileImporterLayout(unittest.TestCase):
    """Checks line and grid placement math."""

    def test_resolve_column_count(self):
        self.assertEqual(3, layout.resolve_column_count(7))
        self.assertEqual(1, layout.resolve_column_count(1))
        self.assertEqual(5, layout.resolve_column_count(7, requested_columns=5))

    def test_line_offsets(self):
        settings = {"offset_mode": constants.OFFSET_LINE, "line_step_x": 10, "line_step_y": 0, "line_step_z": -5}
        expected = [[0.0, 0.0, 0.0], [10.0, 0.0, -5.0], [20.0, 0.0, -10.0]]
        self.assertEqual(expected, layout.build_layout_offsets(3, settings))

    def test_grid_offsets_floor(self):
        settings = {"offset_mode": constants.OFFSET_GRID, "grid_columns": 2, "grid_spacing_a": 10,
                    "grid_spacing_b": 20, "grid_plane": constants.GRID_PLANE_XZ}
        expected = [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 0.0, 20.0]]
        self.assertEqual(expected, layout.build_layout_offsets(3, settings))

    def test_grid_offsets_wall(self):
        settings = {"offset_mode": constants.OFFSET_GRID, "grid_columns": 1, "grid_spacing_a": 10,
                    "grid_spacing_b": 20, "grid_plane": constants.GRID_PLANE_XY}
        expected = [[0.0, 0.0, 0.0], [0.0, 20.0, 0.0]]
        self.assertEqual(expected, layout.build_layout_offsets(2, settings))

    def test_centered_grid(self):
        settings = {"offset_mode": constants.OFFSET_GRID, "grid_columns": 2, "grid_spacing_a": 10,
                    "grid_spacing_b": 10, "center_layout": True}
        expected = [[-5.0, 0.0, -5.0], [5.0, 0.0, -5.0], [-5.0, 0.0, 5.0], [5.0, 0.0, 5.0]]
        self.assertEqual(expected, layout.build_layout_offsets(4, settings))

    def test_auto_spacing(self):
        settings = {"offset_mode": constants.OFFSET_GRID, "grid_columns": 2, "auto_spacing": True,
                    "auto_spacing_padding": 1.0}
        expected = [[0.0, 0.0, 0.0], [5.0, 0.0, 0.0], [0.0, 0.0, 4.0]]
        self.assertEqual(expected, layout.build_layout_offsets(3, settings, max_size=[4.0, 9.0, 3.0]))

    def test_auto_line_step(self):
        expected = [0.0, 0.0, 6.0]
        self.assertEqual(expected, layout.get_auto_line_step([0, 0, 2], [4.0, 9.0, 5.0], 1.0))

    def test_none_offsets(self):
        expected = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        self.assertEqual(expected, layout.build_layout_offsets(2, {"offset_mode": constants.OFFSET_NONE}))
        self.assertEqual([], layout.build_layout_offsets(0, {"offset_mode": constants.OFFSET_GRID}))

    def test_max_size_ignores_empty_boxes(self):
        empty_box = [1e20, 1e20, 1e20, -1e20, -1e20, -1e20]
        expected = [4.0, 3.0, 2.0]
        result = layout.get_max_size([[0, 0, 0, 1, 3, 1], empty_box, None, [-2, 0, 0, 2, 1, 2]])
        self.assertEqual(expected, result)
        self.assertIsNone(layout.get_max_size([empty_box]))

    def test_coefficients_match_offsets(self):
        settings = {"offset_mode": constants.OFFSET_GRID, "grid_columns": 2, "grid_spacing_a": 10,
                    "grid_spacing_b": 20, "center_layout": True}
        expected = [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5)]
        self.assertEqual(expected, layout.build_layout_coefficients(3, settings))
        vector_a, vector_b = layout.build_layout_vectors(settings)
        self.assertEqual(([10.0, 0.0, 0.0], [0.0, 0.0, 20.0]), (vector_a, vector_b))
        self.assertEqual([-5.0, 0.0, -10.0], layout.combine_offset(expected[0], vector_a, vector_b))

    def test_line_coefficients(self):
        settings = {"offset_mode": constants.OFFSET_LINE, "center_layout": True}
        self.assertEqual([(-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)], layout.build_layout_coefficients(3, settings))

    def test_control_attribute_names(self):
        self.assertEqual("file03", layout.build_control_attribute_name(3))
        self.assertEqual("file12OffsetX", layout.build_control_attribute_name(12, "OffsetX"))
