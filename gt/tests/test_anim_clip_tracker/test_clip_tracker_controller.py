"""Tests Animation Clip Tracker selection bookkeeping."""
import os
import tempfile
import unittest
from unittest import mock

from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants
from gt.tools.anim_clip_tracker import clip_tracker_controller
from gt.tools.anim_clip_tracker import clip_tracker_model


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
        self.automation_path = ""
        self.automation_check_states = {}
        self.automation_check_states_path = ""

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

    def add_clip_range(self, start_frame, end_frame, active=True, name=""):
        """Adds a clip using explicit values.

        Args:
            start_frame (int): Clip start frame.
            end_frame (int): Clip end frame.
            active (bool, optional): Whether the clip is active.
            name (str, optional): Clip name.
        """
        self.clips.append(
            {
                "active": bool(active),
                "name": name,
                "start": int(start_frame),
                "end": int(end_frame),
            }
        )

    def update_clip(self, index, key, value):
        """Updates one clip value.

        Args:
            index (int): Clip index.
            key (str): Clip field name.
            value (object): New field value.
        """
        self.clips[index][key] = value

    def get_automation_check_states(self, automation_path):
        """Gets stored automation check states.

        Args:
            automation_path (str): Automation folder path.

        Returns:
            dict: Stored script states.
        """
        if automation_path != self.automation_check_states_path:
            return {}
        return dict(self.automation_check_states)

    def set_automation_check_state(self, automation_path, script_name, is_checked):
        """Stores an automation check state.

        Args:
            automation_path (str): Automation folder path.
            script_name (str): Automation file name.
            is_checked (bool): Whether the automation is selected.
        """
        if automation_path != self.automation_check_states_path:
            self.automation_check_states_path = automation_path
            self.automation_check_states = {}
        self.automation_check_states[script_name] = bool(is_checked)

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

    def set_automation_path(self, automation_path):
        """Provides the controller's automation-path update interface.

        Args:
            automation_path (str): Automation folder path.
        """


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

    def test_automation_helpers_create_and_update_a_clip(self):
        """Checks automation helpers expose clip creation and all setters."""
        controller = build_controller()

        clip_index = controller.create_automation_clip(10, 20, "Initial", True)
        controller.set_automation_clip_start(clip_index, 12)
        controller.set_automation_clip_end(clip_index, 24)
        controller.set_automation_clip_name(clip_index, "Updated")
        controller.set_automation_clip_active(clip_index, False)

        self.assertEqual(
            {"active": False, "name": "Updated", "start": 12, "end": 24},
            controller.model.get_data()[clip_index],
        )

    def test_run_checked_automations_skips_unchecked_scripts(self):
        """Checks batch execution includes only selected automation scripts."""
        controller = build_controller()
        with tempfile.TemporaryDirectory() as temp_directory:
            checked_path = os.path.join(temp_directory, "checked.py")
            unchecked_path = os.path.join(temp_directory, "unchecked.py")
            for script_path in (checked_path, unchecked_path):
                with open(script_path, "w", encoding="utf-8") as script_file:
                    script_file.write("pass\n")
            controller.model.automation_path = temp_directory
            controller.model.automation_check_states_path = temp_directory
            controller.model.automation_check_states = {"unchecked.py": False}

            with mock.patch.object(controller, "run_automation") as run_automation:
                controller.run_checked_automations()

        run_automation.assert_called_once_with(checked_path)

    def test_packaged_automation_creates_and_updates_a_clip(self):
        """Checks the example automation uses the supported context helpers."""
        controller = build_controller()

        with mock.patch.object(
            clip_tracker_controller,
            "get_maya_cmds",
            return_value=object(),
        ):
            result = controller.run_automation(
                clip_tracker_model.get_sample_automation_path()
            )

        self.assertTrue(result)
        self.assertEqual(
            {"active": True, "name": "Automation Updated", "start": 105, "end": 135},
            controller.model.get_data()[0],
        )


if __name__ == "__main__":
    unittest.main()
