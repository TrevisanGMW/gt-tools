"""Tests Annotation Tracker view formatting helpers."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from gt.tools.anim_annotation_tracker.annotation_tracker_view import AnnotationTrackerView


class TestAnnotationTrackerView(unittest.TestCase):
    """Tests import-safe Annotation Tracker view helpers."""

    def test_validation_report_separates_sections_only(self):
        """Checks validation issues stay grouped without extra issue spacing."""
        errors = [
            "Overlap detected between 'First' and 'Second'",
            "Timeline has 10 uncovered frame(s).",
            "File 'Quality' is required.",
            "Range 'First': 'State' is required.",
            "Range 'First': 'Style' is required.",
        ]
        expected_report = (
            "Validation Issues (5)\n\n"
            "Timeline\n"
            "- Overlap detected between 'First' and 'Second'\n"
            "- Timeline has 10 uncovered frame(s).\n\n"
            "File Data\n"
            "- File 'Quality' is required.\n\n"
            "Range 'First'\n"
            "- Range 'First': 'State' is required.\n"
            "- Range 'First': 'Style' is required."
        )

        actual_report = AnnotationTrackerView._format_validation_report(
            None, errors
        )

        self.assertEqual(expected_report, actual_report)

    def test_show_annotation_data_opens_formatted_output_window(self):
        """Checks current annotation data is displayed in the output window."""
        range_item = SimpleNamespace(
            id="range-id",
            name="Walk",
            start=1,
            end=24,
            color=(100, 150, 200),
            locked=False,
            custom_data={"state": "walk"},
        )
        view = SimpleNamespace(
            timeline=SimpleNamespace(ranges=[range_item]),
            file_data={"source": "mocap"},
            schema={
                "file_level": [{"type": "string", "name": "source"}],
                "frame_range": [{"type": "string", "name": "state"}],
            },
        )
        output_window = MagicMock()
        expected_output = (
            "{\n"
            "    \"file_data\": {\n"
            "        \"source\": \"mocap\"\n"
            "    },\n"
            "    \"range_data\": {\n"
            "        \"range_000\": {\n"
            "            \"name\": \"Walk\",\n"
            "            \"start_frame\": 1,\n"
            "            \"end_frame\": 24,\n"
            "            \"state\": \"walk\"\n"
            "        }\n"
            "    }\n"
            "}"
        )

        with patch(
            "gt.tools.anim_annotation_tracker.annotation_tracker_view."
            "ui_python_output_view.PythonOutputView",
            return_value=output_window,
        ) as mock_output_view:
            AnnotationTrackerView.show_annotation_data(view)

        mock_output_view.assert_called_once_with(parent=view, editable=False)
        output_window.setWindowTitle.assert_called_once_with(
            "Annotation Tracker Annotation Data"
        )
        output_window.set_python_output_text.assert_called_once_with(
            expected_output
        )
        output_window.show.assert_called_once_with()
        self.assertIs(output_window, view._annotation_data_output_window)
