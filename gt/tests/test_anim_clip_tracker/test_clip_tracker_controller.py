"""Tests Animation Clip Tracker selection bookkeeping."""
import unittest

from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants
from gt.tools.anim_clip_tracker import clip_tracker_controller


class FakeModel:
    """Minimal stand-in for the clip tracker model."""

    def __init__(self, clips=None, timeline_mode=clip_constants.MODE_SELECT, show_timeline=True):
        """Initializes the fake model.

        Args:
            clips (list, optional): Clip dictionaries.
            timeline_mode (str, optional): Timeline interaction mode.
            show_timeline (bool, optional): Whether the timeline view is visible.
        """
        self.clips = list(clips or [])
        self.timeline_mode = timeline_mode
        self.show_timeline = show_timeline
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

    def move_clip(self, index, offset):
        """Swaps a clip with its requested neighboring position.

        Args:
            index (int): Source clip index.
            offset (int): Relative move amount.

        Returns:
            bool: True when the move is valid.
        """
        target_index = index + offset
        if target_index < 0 or target_index >= len(self.clips):
            return False
        self.clips[index], self.clips[target_index] = self.clips[target_index], self.clips[index]
        return True

    def save_data(self):
        """Records that data was saved."""
        self.saved = True

    def save_preferences(self):
        """Records that preferences were saved."""
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
        self.timeline_visibility_calls = []

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

    def set_timeline_visible(self, is_visible):
        """Records a timeline visibility update.

        Args:
            is_visible (bool): Requested timeline visibility.
        """
        self.timeline_visibility_calls.append(bool(is_visible))

    def update_timeline(self):
        """Provides the controller's timeline update interface."""


def build_controller(clips=None, timeline_mode=clip_constants.MODE_SELECT, show_timeline=True):
    """Builds a controller wired to fake collaborators.

    Args:
        clips (list, optional): Clip dictionaries.
        timeline_mode (str, optional): Timeline interaction mode.
        show_timeline (bool, optional): Whether the timeline view is visible.

    Returns:
        ClipTrackerController: Controller using the fake model and view.
    """
    model = FakeModel(clips=clips, timeline_mode=timeline_mode, show_timeline=show_timeline)
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
        self.assertEqual([(-1, False)], controller.view.highlight_calls)

    def test_select_clip_is_ignored_without_the_timeline_view(self):
        """Checks no row is highlighted while the timeline view is hidden."""
        controller = build_controller(clips=[{"start": 1, "end": 5}], show_timeline=False)

        controller.select_clip(0)

        self.assertEqual(-1, controller.selected_index)
        self.assertEqual([(-1, False)], controller.view.highlight_calls)

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

    def test_show_timeline_changes_visibility_without_a_rebuild(self):
        """Checks timeline visibility updates without rebuilding the docked view."""
        controller = build_controller(show_timeline=False)
        controller.update_preference("show_timeline", True)
        controller.update_preference("show_timeline", False)

        self.assertEqual([True, False], controller.view.timeline_visibility_calls)
        self.assertEqual(False, controller.model.show_timeline)

    def test_move_clip_updates_selection_and_playback_indices(self):
        """Checks moving a clip preserves the matching selected and playing rows."""
        controller = build_controller(clips=[{"start": 1}, {"start": 10}])
        controller.selected_index = 0
        controller.playing_index = 0

        controller.move_clip(0, 1)

        self.assertEqual(1, controller.selected_index)
        self.assertEqual(1, controller.playing_index)
        self.assertEqual(10, controller.model.clips[0]["start"])


if __name__ == "__main__":
    unittest.main()
