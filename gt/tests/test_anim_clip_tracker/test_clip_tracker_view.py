"""Tests responsive layout behavior for the Animation Clip Tracker view."""
import sys
import unittest
from unittest import mock

from gt.tools.anim_clip_tracker import clip_tracker_view


class FakeController:
    """Minimal controller used while building isolated clip-row widgets."""

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


if __name__ == "__main__":
    unittest.main()
