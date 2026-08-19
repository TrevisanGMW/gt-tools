"""Tests Annotation Tracker view formatting helpers."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from gt.tools.anim_annotation_tracker import annotation_tracker_view
from gt.tools.anim_annotation_tracker import annotation_tracker_model
from gt.tools.anim_annotation_tracker.annotation_tracker_view import AnnotationTrackerView


class TestAnnotationTrackerView(unittest.TestCase):
    """Tests import-safe Annotation Tracker view helpers."""

    def test_apply_tool_mode_preference_restores_selected_button(self):
        """Checks a persisted mode selects its radio button and behavior."""
        view = SimpleNamespace(
            rad_nav=MagicMock(),
            rad_sel=MagicMock(),
            rad_edit=MagicMock(),
            rad_raz=MagicMock(),
            on_tool_mode_changed=MagicMock(),
        )

        actual_mode = AnnotationTrackerView._apply_tool_mode_preference(
            view,
            "razor",
        )

        self.assertEqual("razor", actual_mode)
        view.rad_raz.setChecked.assert_called_once_with(True)
        view.on_tool_mode_changed.assert_called_once_with()

    def test_save_preferences_includes_current_tool_mode(self):
        """Checks the selected mode is written through the preference model."""
        line_edit = MagicMock()
        line_edit.text.return_value = ""
        checkbox = MagicMock()
        checkbox.isChecked.return_value = True
        spin_box = MagicMock()
        spin_box.value.return_value = 10
        model = MagicMock()
        view = SimpleNamespace(
            model=model,
            schema_path_fld=line_edit,
            auto_path_fld=line_edit,
            chk_magnet=checkbox,
            spin_magnet=spin_box,
            chk_auto_crop=checkbox,
            spin_crop_tolerance=spin_box,
            chk_auto_stretch=checkbox,
            spin_stretch_tolerance=spin_box,
            chk_show_timeline=checkbox,
            chk_frames=checkbox,
            chk_names=checkbox,
            chk_colors=checkbox,
            chk_sync=checkbox,
            chk_bounds=checkbox,
            chk_razor_colors=checkbox,
            chk_run_all_auto=checkbox,
            chk_val_status=checkbox,
            chk_write_node=checkbox,
            timeline=SimpleNamespace(tool_mode="razor"),
            _get_selected_tool_mode=lambda: "razor",
        )

        AnnotationTrackerView.save_preferences(view)

        saved_preferences = model.update_preferences.call_args.args[0]
        self.assertEqual(
            "razor",
            saved_preferences[
                annotation_tracker_model.TOOL_MODE_PREFERENCE_KEY
            ],
        )

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

    def test_create_example_schema_uses_model_copy_and_writes_stdout(self):
        """Checks the packaged schema is the view's only sample source."""
        requested_path = "C:/schemas/schema.json"
        copied_path = "C:\\schemas\\schema.json"
        stdout = SimpleNamespace(write=MagicMock())
        view = SimpleNamespace(
            schema_path_fld=SimpleNamespace(setText=MagicMock()),
            check_schema_path=MagicMock(return_value=True),
            status_bar=SimpleNamespace(setText=MagicMock()),
        )

        with patch.object(
            annotation_tracker_view.QtWidgets.QFileDialog,
            "getSaveFileName",
            return_value=(requested_path, "JSON Files (*.json)"),
        ), patch.object(
            annotation_tracker_model,
            "copy_sample_schema",
            return_value=copied_path,
        ) as mock_copy, patch.object(
            annotation_tracker_view.sys,
            "stdout",
            stdout,
        ):
            AnnotationTrackerView.create_example_schema(view)

        mock_copy.assert_called_once_with(requested_path)
        view.schema_path_fld.setText.assert_called_once_with(copied_path)
        view.check_schema_path.assert_called_once_with(rebuild=True)
        view.status_bar.setText.assert_called_once_with(
            f"Created and applied schema: {copied_path}"
        )
        stdout.write.assert_called_once_with(
            f"Created example schema at {copied_path}\n"
        )
