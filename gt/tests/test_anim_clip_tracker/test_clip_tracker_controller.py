"""Tests Animation Clip Tracker selection bookkeeping."""
import unittest

from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants
from gt.tools.anim_clip_tracker import clip_tracker_controller


class FakeModel:
    """Minimal stand-in for the clip tracker model."""

    def __init__(self, clips=None, timeline_mode=clip_constants.MODE_SELECT):
        """Initializes the fake model.

        Args:
            clips (list, optional): Clip dictionaries.
            timeline_mode (str, optional): Timeline interaction mode.
        """
        self.clips = list(clips or [])
        self.timeline_mode = timeline_mode
        self.confirm_delete_clip = False
        self.auto_reorder_clips = False
        self.saved = False

    def get_data(self):
        """Gets clip data.

        Returns:
            list: Clip dictionaries.
        """
        return self.clips

    def get_clip_issues(self):
        """Gets validation issues.

        Returns:
            dict: Empty issue mapping.
        """
        return {}

    def delete_clip(self, index):
        """Removes a clip.

        Args:
            index (int): Clip index.
        """
        self.clips.pop(index)

    def reorder_clips(self):
        """Sorts clips by start frame."""
        self.clips = sorted(self.clips, key=lambda clip: clip.get("start", 0))

    def save_data(self):
        """Records that data was saved."""
        self.saved = True

    def log(self, message):
        """Ignores log messages.

        Args:
            message (str): Message to log.
        """


class FakeView:
    """Minimal stand-in for the clip tracker view."""

    def __init__(self):
        """Initializes the fake view."""
        self.controller = None
        self.highlight_calls = []
        self.draw_calls = []

    def window_exists(self):
        """Reports the window as available.

        Returns:
            bool: Always True.
        """
        return True

    def draw_clips(self, clips_data, playing_index=None):
        """Records a clip list redraw.

        Args:
            clips_data (list): Clip dictionaries.
            playing_index (int, optional): Currently playing clip index.
        """
        self.draw_calls.append((list(clips_data), playing_index))

    def highlight_clip_row(self, selected_index, scroll_into_view=False):
        """Records a row highlight request.

        Args:
            selected_index (int): Clip index.
            scroll_into_view (bool, optional): Whether the row should be revealed.
        """
        self.highlight_calls.append((selected_index, scroll_into_view))


def build_controller(clips=None, timeline_mode=clip_constants.MODE_SELECT):
    """Builds a controller wired to fake collaborators.

    Args:
        clips (list, optional): Clip dictionaries.
        timeline_mode (str, optional): Timeline interaction mode.

    Returns:
        ClipTrackerController: Controller using the fake model and view.
    """
    model = FakeModel(clips=clips, timeline_mode=timeline_mode)
    view = FakeView()
    return clip_tracker_controller.ClipTrackerController(model=model, view=view)


class TestClipTrackerControllerSelection(unittest.TestCase):
    """Tests how timeline selection is mirrored in the clip list."""

    def test_select_clip_highlights_row_and_scrolls_in_select_mode(self):
        """Checks selecting a clip reveals its row while in select mode."""
        controller = build_controller(clips=[{"start": 1, "end": 5}, {"start": 6, "end": 9}])

        controller.select_clip(1)

        self.assertEqual(1, controller.selected_index)
        self.assertEqual([(1, True)], controller.view.highlight_calls)

    def test_select_clip_does_not_scroll_in_edit_mode(self):
        """Checks editing a clip highlights the row without moving the list."""
        controller = build_controller(
            clips=[{"start": 1, "end": 5}],
            timeline_mode=clip_constants.MODE_EDIT,
        )

        controller.select_clip(0)

        self.assertEqual([(0, False)], controller.view.highlight_calls)

    def test_select_clip_clears_highlight(self):
        """Checks clicking an empty timeline area clears the highlight."""
        controller = build_controller(clips=[{"start": 1, "end": 5}])

        controller.select_clip(-1)

        self.assertEqual(-1, controller.selected_index)
        self.assertEqual([(-1, True)], controller.view.highlight_calls)

    def test_delete_clip_shifts_selection(self):
        """Checks the highlight follows a clip after earlier clips are removed."""
        controller = build_controller(clips=[{"start": 1, "end": 5}, {"start": 6, "end": 9}])
        controller.selected_index = 1

        controller.delete_clip(0)

        self.assertEqual(0, controller.selected_index)

    def test_delete_clip_clears_selection_of_deleted_clip(self):
        """Checks deleting the selected clip clears the highlight."""
        controller = build_controller(clips=[{"start": 1, "end": 5}, {"start": 6, "end": 9}])
        controller.selected_index = 1

        controller.delete_clip(1)

        self.assertEqual(-1, controller.selected_index)

    def test_reorder_clips_clears_selection(self):
        """Checks reordering clears the highlight because indices change."""
        controller = build_controller(clips=[{"start": 6, "end": 9}, {"start": 1, "end": 5}])
        controller.selected_index = 0

        controller.reorder_clips()

        self.assertEqual(-1, controller.selected_index)


if __name__ == "__main__":
    unittest.main()
