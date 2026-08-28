"""Tests responsive layout behavior for the Animation Clip Tracker view."""
import os
import sys
import tempfile
import unittest
from unittest import mock

from gt.tools.anim_clip_tracker import clip_tracker_preferences
from gt.tools.anim_clip_tracker import clip_tracker_view


class FakeController:
    """Minimal controller used while building isolated clip-row widgets."""

    class Model:
        """Minimal automation state used by the isolated view tests."""

        def __init__(self):
            """Initializes default automation state."""
            self.automation_path = ""
            self.automation_check_states = {}
            self.automation_check_states_path = ""

        def get_automation_check_states(self, automation_path):
            """Gets checked automation states for a matching folder.

            Args:
                automation_path (str): Automation folder path.

            Returns:
                dict: Stored automation check states.
            """
            if automation_path != self.automation_check_states_path:
                return {}
            return dict(self.automation_check_states)

    def __init__(self):
        """Initializes controller methods and automation state."""
        self.model = self.Model()

    def update_clip_val(self, *args):
        """Accepts a clip value update from a test widget.

        Args:
            *args: Ignored clip update data.
        """

    def set_range(self, *args):
        """Accepts a timeline-range request from a test widget.

        Args:
            *args: Ignored range request data.
        """

    def toggle_play(self, *args):
        """Accepts a play-state request from a test widget.

        Args:
            *args: Ignored play request data.
        """

    def delete_clip(self, *args):
        """Accepts a clip-deletion request from a test widget.

        Args:
            *args: Ignored deletion request data.
        """

    def set_automation_check_state(self, *args):
        """Accepts an automation selection update from a test widget.

        Args:
            *args: Ignored automation update data.
        """

    def run_checked_automations(self, *args):
        """Accepts a checked-automation batch request from a test widget.

        Args:
            *args: Ignored automation run request data.
        """

    def run_automation(self, *args):
        """Accepts an individual automation run request from a test widget.

        Args:
            *args: Ignored automation run request data.
        """

    def open_automation_in_editor(self, *args):
        """Accepts an automation edit request from a test widget.

        Args:
            *args: Ignored automation edit request data.
        """


class TestClipTrackerViewResponsiveLayout(unittest.TestCase):
    """Tests DPI-aware clip-list control dimensions."""

    @classmethod
    def setUpClass(cls):
        """Creates the shared Qt application used by widget tests."""
        application = clip_tracker_view.ui_qt.QtWidgets.QApplication.instance()
        if not application:
            cls.application = clip_tracker_view.ui_qt.QtWidgets.QApplication(sys.argv)
        else:
            cls.application = application

    def setUp(self):
        """Creates an isolated clip tracker view."""
        self.view = clip_tracker_view.ClipTrackerView()
        self.view.controller = FakeController()

    def tearDown(self):
        """Disposes of the clip tracker view without Maya controller callbacks."""
        self.view.controller = None
        self.view.close()
        self.view.deleteLater()

    def test_clip_row_scales_fixed_controls_and_preserves_horizontal_scroll(self):
        """Checks high-DPI clip columns remain readable instead of compressing."""
        with mock.patch.object(self.view, "get_ui_scale_factor", return_value=1.0):
            self.view.update_ui_scale_metrics(force=True)
            clips_tab = self.view.build_clips_tab()
            self.view.draw_clip_row(0, {"active": True, "name": "Walk", "start": 1, "end": 120})

        self.assertEqual(60, self.view.frame_fields[(0, "start")].width())
        with mock.patch.object(self.view, "get_ui_scale_factor", return_value=1.5):
            self.view.update_ui_scale_metrics(force=True)

        clips_tab.resize(320, 180)
        clips_tab.show()
        self.application.processEvents()

        expected_frame_width = 90
        expected_checkbox_width = 30
        expected_row_width = 661
        self.assertEqual(expected_frame_width, self.view.frame_fields[(0, "start")].width())
        self.assertEqual(expected_frame_width, self.view.frame_fields[(0, "end")].width())
        self.assertEqual(expected_frame_width, self.view.duration_fields[0].width())
        self.assertEqual(expected_checkbox_width, self.view.clip_rows[0].findChild(
            clip_tracker_view.ui_qt.QtWidgets.QCheckBox
        ).width())
        self.assertEqual(expected_row_width, self.view.clips_content.minimumWidth())
        self.assertEqual(
            clip_tracker_view.ui_qt.QtCore.Qt.ScrollBarAsNeeded,
            self.view.clips_scroll.horizontalScrollBarPolicy(),
        )
        self.assertGreater(self.view.clips_scroll.horizontalScrollBar().maximum(), 0)

    def test_frame_field_preserves_large_frame_values(self):
        """Checks clip frame fields accept values beyond the previous UI limit."""
        expected_value = 1695613

        frame_field = self.view.create_frame_field(0, "start", expected_value)

        self.assertEqual(expected_value, frame_field.value())
        self.assertEqual(clip_tracker_view.FRAME_FIELD_MINIMUM, frame_field.minimum())
        self.assertEqual(clip_tracker_view.FRAME_FIELD_MAXIMUM, frame_field.maximum())

    def test_timeline_splitter_hides_its_handle_with_the_timeline(self):
        """Checks Show Timeline removes the timeline divider as well."""
        self.view.timeline_widget = clip_tracker_view.clip_tracker_timeline.ClipTimelineWidget(
            parent=self.view
        )
        self.view.build_timeline_container()
        self.view.tabs = clip_tracker_view.ui_qt.QtWidgets.QTabWidget(parent=self.view)
        self.view.timeline_splitter = self.view.build_timeline_splitter()
        self.view.timeline_splitter.setParent(self.view)
        self.view.timeline_splitter.resize(400, 360)
        self.view.timeline_splitter.show()
        self.application.processEvents()
        self.view.timeline_splitter.setSizes([160, 194])
        self.application.processEvents()
        timeline_height = self.view.timeline_splitter.sizes()[0]
        splitter_handle = self.view.get_timeline_splitter_handle()

        self.view.set_timeline_visible(False)

        self.assertEqual(clip_tracker_view.ui_qt.QtCore.Qt.Vertical, self.view.timeline_splitter.orientation())
        self.assertFalse(self.view.timeline_splitter.childrenCollapsible())
        self.assertTrue(self.view.timeline_container.isHidden())
        self.assertTrue(splitter_handle.isHidden())
        self.assertEqual(timeline_height, self.view._timeline_height)

        self.view.set_timeline_visible(True)
        self.application.processEvents()

        self.assertFalse(self.view.timeline_widget.isHidden())
        self.assertFalse(splitter_handle.isHidden())
        self.assertEqual(timeline_height, self.view.timeline_splitter.sizes()[0])

    def test_automations_tab_uses_compact_checkboxes_and_padded_edit_buttons(self):
        """Checks automation controls remain compact at standard DPI."""
        with tempfile.TemporaryDirectory() as temp_directory:
            script_path = os.path.join(temp_directory, "example.py")
            with open(script_path, "w", encoding="utf-8") as script_file:
                script_file.write("pass\n")
            self.view.controller.model.automation_path = temp_directory
            self.view.controller.model.automation_check_states_path = temp_directory
            self.view.build_automations_tab()
            self.view.build_automations_ui()

        checkbox = self.view.automation_checkboxes[script_path]
        edit_button = next(
            button
            for button in self.view.automations_content.findChildren(
                clip_tracker_view.ui_qt.QtWidgets.QPushButton
            )
            if button.text() == "Edit"
        )

        self.assertEqual(
            clip_tracker_view.ui_qt.QtWidgets.QSizePolicy.Fixed,
            checkbox.sizePolicy().horizontalPolicy(),
        )
        self.assertGreaterEqual(edit_button.minimumWidth(), edit_button.sizeHint().width())

    def test_automations_tab_centers_an_empty_folder_message(self):
        """Checks unavailable folders receive a clear centered message."""
        self.view.build_automations_tab()
        self.view.build_automations_ui()

        self.assertEqual(
            "Automations folder not found or path is empty.",
            self.view.automation_empty_label.text(),
        )
        self.assertEqual(
            clip_tracker_view.ui_qt.QtCore.Qt.AlignCenter,
            self.view.automations_layout.alignment(),
        )

    def test_automation_preference_actions_match_text_button_metrics(self):
        """Checks all preference icon buttons match data-management actions."""
        panel = clip_tracker_preferences.ClipPreferencesPanel({})
        buttons = panel.findChildren(clip_tracker_view.ui_qt.QtWidgets.QPushButton)
        icon_button_tooltips = [
            clip_tracker_preferences.TOOLTIP_BTN_CREATE_AUTOMATION,
            clip_tracker_preferences.TOOLTIP_BTN_BROWSE_AUTOMATION,
            clip_tracker_preferences.TOOLTIP_BTN_DELETE_SCENE_DATA,
            clip_tracker_preferences.TOOLTIP_BTN_SELECT_SCENE_DATA,
        ]
        icon_buttons = [
            next(button for button in buttons if button.toolTip() == tooltip)
            for tooltip in icon_button_tooltips
        ]

        for button in icon_buttons:
            self.assertEqual("", button.text())
            self.assertFalse(button.icon().isNull())
            self.assertEqual(28, button.width())
            self.assertEqual(18, button.iconSize().width())

        import_button = next(button for button in buttons if button.text() == "Import JSON")
        import_button.setMinimumHeight(36)
        self.view.preferences_panel = panel
        with mock.patch.object(self.view, "get_ui_scale_factor", return_value=1.5):
            self.view.update_ui_scale_metrics(force=True)

        for button in icon_buttons:
            self.assertEqual(import_button.minimumHeight(), button.width())
            self.assertEqual(import_button.minimumHeight(), button.height())
            self.assertEqual(23, button.iconSize().width())
        self.view.preferences_panel = None
        panel.deleteLater()


if __name__ == "__main__":
    unittest.main()
