"""
Animation Clip Tracker Controller
"""
from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants
from gt.tools.anim_clip_tracker import clip_tracker_preferences
import gt.ui.qt_import as ui_qt


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


class ClipTrackerController:
    """Connects Clip Tracker model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (ClipTrackerModel): Model instance.
            view (ClipTrackerView): View instance.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.playing_index = None
        self.selected_index = -1
        self._focus_filter = None
        self._is_refreshing = False
        self._timeline_timer = None

    def start(self):
        """Starts the tool."""
        self.view.build_ui()
        self.install_focus_refresh_filter()
        self.refresh(force=True)

    def refresh(self, force=False):
        """Reloads scene data and redraws the clip list.

        Args:
            force (bool, optional): Forces UI redraw even if data didn't change.
        """
        if self._is_refreshing:
            return
        if not self.view.window_exists():
            return
        self._is_refreshing = True
        try:
            import copy
            # Snapshot the current state before reloading
            old_clips = copy.deepcopy(self.model.get_data())

            self.model.load_data()
            if self.model.auto_add_timeline_clip:
                self.model.add_timeline_clip_if_missing()
            if self.model.sync_time_slider_bookmarks:
                self.model.sync_from_time_slider_bookmarks()

            new_clips = self.model.get_data()

            if self.view.window_exists():
                # Only destroy and redraw the UI if the data actually changed or if forced
                if force or old_clips != new_clips:
                    self.view.draw_clips(self.model.get_data(), self.playing_index)
        finally:
            self._is_refreshing = False

    def deferred_refresh(self):
        """Refreshes only when the window still exists."""
        if self.view.window_exists():
            self.refresh()  # Evaluates normally without forcing a redraw

    def rebuild_view(self):
        """Rebuilds the window after deferred UI actions."""
        if self.view.window_exists():
            self.view.build_ui()
            self.install_focus_refresh_filter()
            self.refresh(force=True)

    def add_clip(self, *args):
        """Adds a clip using the current new-clip preferences.

        Args:
            *args: Optional Maya callback arguments.
        """
        self.model.add_clip()
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def add_timeline_clip(self, *args):
        """Adds a clip that matches the current timeline range.

        Args:
            *args: Optional Maya callback arguments.
        """
        self.model.add_timeline_clip()
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def update_clip_val(self, index, key, value):
        """Updates a clip value from UI.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            value (object): New value.
        """
        self.model.update_clip(index, key, value)
        self.view.update_top_info()
        if key in ["start", "end"]:
            if self.model.auto_reorder_clips:
                get_maya_cmds().evalDeferred(self.deferred_draw_clips)
                return
            clips_data = self.model.get_data()
            if index < 0 or index >= len(clips_data):
                return
            clip = clips_data[index]
            self.view.update_duration_field(index, clip.get("start"), clip.get("end"))
            self.view.refresh_duration_fields()

    def modify_frame(self, index, key, action, *args):
        """Modifies a start or end frame.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            action (str): Modification action.
            *args: Optional Maya callback arguments.
        """
        self.modify_frame_from_popup(index, key, action)

    def modify_frame_from_popup(self, index, key, action, field=None, *args):
        """Modifies a frame field from a popup menu without rebuilding the popup parent.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            action (str): Modification action.
            field (str, optional): Maya int field to update.
            *args: Optional Maya callback arguments.
        """
        new_value = self.get_modified_frame_value(index=index, key=key, action=action)
        if new_value is None:
            return
        self.model.update_clip(index, key, new_value)
        if not self.view.window_exists():
            return
        if self.model.auto_reorder_clips:
            get_maya_cmds().evalDeferred(self.deferred_draw_clips)
            return
        clip = self.model.get_data()[index]
        self.view.update_frame_field(index, key, clip.get(key), field=field)
        self.view.refresh_duration_fields()
        self.view.update_top_info()

    def go_to_frame(self, index, key, field=None, *args):
        """Sets the current Maya frame to the value shown in a frame field.

        The displayed value is used even when it was typed without being committed,
        so the clip data is updated to match what the user sees.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            field (str, optional): Maya int field holding the displayed value.
            *args: Optional Maya callback arguments.
        """
        clips_data = self.model.get_data()
        if index < 0 or index >= len(clips_data):
            return
        field_value = self.view.get_frame_field_value(index, key, field=field)
        if field_value is None:
            field_value = int(clips_data[index].get(key, 0))
        if field_value != int(clips_data[index].get(key, 0)):
            self.update_clip_val(index, key, field_value)
        self.model.set_current_frame(field_value)
        self.view.update_top_info()
        self.view.update_timeline()

    def get_modified_frame_value(self, index, key, action):
        """Gets a new frame value for a frame-field action.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            action (str): Modification action.

        Returns:
            int or None: New frame value, or None when the clip is unavailable.
        """
        clips_data = self.model.get_data()
        if index < 0 or index >= len(clips_data):
            return None
        clip = clips_data[index]
        current_value = int(clip.get(key, 0))
        if action == "current":
            return self.model.get_current_frame()
        if action == "increment":
            return current_value + 1
        return current_value - 1

    def delete_clip(self, index, *args):
        """Deletes a clip after confirmation.

        Args:
            index (int): Clip index.
            *args: Optional Maya callback arguments.
        """
        cmds = get_maya_cmds()
        should_delete = True
        if self.model.confirm_delete_clip:
            clip_name = self.model.get_data()[index].get("name") or "Clip {0}".format(index + 1)
            result = cmds.confirmDialog(
                title="Confirm Deletion",
                message='Are you sure you want to delete "{0}"?'.format(clip_name),
                button=["Yes", "Cancel"],
                defaultButton="Yes",
                cancelButton="Cancel",
                dismissString="Cancel",
            )
            should_delete = result == "Yes"
        if should_delete:
            self.model.delete_clip(index)
            if self.playing_index == index:
                self.playing_index = None
            elif self.playing_index is not None and self.playing_index > index:
                self.playing_index -= 1
            if self.selected_index == index:
                self.selected_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
            if self.view.window_exists():
                self.view.draw_clips(self.model.get_data(), self.playing_index)

    def reset_preferences(self, *args):
        """Resets Clip Tracker preferences to defaults."""
        self.model.reset_preferences_to_defaults()
        self.model.save_preferences()
        get_maya_cmds().evalDeferred(self.rebuild_view)

    def set_range(self, index, *args):
        """Sets the timeline to a clip range.

        Args:
            index (int): Clip index.
            *args: Optional Maya callback arguments.
        """
        clip = self.model.get_data()[index]
        self.model.set_playback_range(clip.get("start"), clip.get("end"))

    def toggle_play(self, index, *args):
        """Toggles clip playback.

        Args:
            index (int): Clip index.
            *args: Optional Maya callback arguments.
        """
        cmds = get_maya_cmds()
        clip = self.model.get_data()[index]
        is_playing = cmds.play(query=True, state=True)
        if self.playing_index == index and is_playing:
            self.model.play_clip(clip.get("start"), clip.get("end"), pause_only=True)
            self.playing_index = None
        else:
            self.model.play_clip(clip.get("start"), clip.get("end"), pause_only=False)
            self.playing_index = index
        self.view.update_play_icons(self.playing_index)

    def import_data(self):
        """Imports clip JSON data."""
        cmds = get_maya_cmds()
        file_path = cmds.fileDialog2(
            fileFilter="JSON Files (*.json)",
            dialogStyle=2,
            fileMode=1,
            caption="Import Clip Data",
        )
        if file_path:
            self.model.import_json(file_path[0])
            self.view.draw_clips(self.model.get_data(), self.playing_index)

    def export_data(self):
        """Exports clip JSON data."""
        cmds = get_maya_cmds()
        file_path = cmds.fileDialog2(
            fileFilter="JSON Files (*.json)",
            dialogStyle=2,
            fileMode=0,
            caption="Export Clip Data",
        )
        if file_path:
            self.model.export_json(file_path[0])

    def update_preference(self, key, value):
        """Updates a tool preference.

        Args:
            key (str): Preference key.
            value (object): New value.
        """
        setattr(self.model, key, value)
        self.model.save_preferences()
        if key == "show_timeline":
            # Row highlights only mirror a timeline selection, so they are dropped with the timeline
            if not value:
                self.selected_index = -1
            # The timeline changes the window structure, so the UI is rebuilt
            get_maya_cmds().evalDeferred(self.rebuild_view)
            return
        timeline_only_keys = [
            "timeline_mode",
            "timeline_show_names",
            "timeline_sync_time_edit",
            "timeline_allow_outside_range",
            "timeline_magnet_enabled",
            "timeline_snap_tolerance",
        ]
        if key in timeline_only_keys:
            # These preferences only affect the timeline, so clip rows are left alone
            self.view.update_timeline()
            return
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def connect_preferences_panel(self, preferences_panel):
        """Connects the preferences panel signals.

        Args:
            preferences_panel (ClipPreferencesPanel): Panel to connect.
        """
        preferences_panel.preference_changed.connect(self.update_preference)
        preferences_panel.action_triggered.connect(self.run_preference_action)

    def run_preference_action(self, action):
        """Runs one preference panel action.

        Args:
            action (str): Action name reported by the panel.
        """
        actions = {
            clip_tracker_preferences.ACTION_SYNC_BOOKMARKS: self.sync_bookmarks,
            clip_tracker_preferences.ACTION_REORDER_CLIPS: self.reorder_clips,
            clip_tracker_preferences.ACTION_IMPORT_DATA: self.import_data,
            clip_tracker_preferences.ACTION_EXPORT_DATA: self.export_data,
            clip_tracker_preferences.ACTION_RESET_PREFERENCES: self.reset_preferences,
            clip_tracker_preferences.ACTION_DELETE_SCENE_DATA: self.delete_scene_data,
        }
        action_function = actions.get(action)
        if not action_function:
            self.model.log('Unknown preference action: "{0}"'.format(action))
            return
        action_function()

    def delete_scene_data(self, *args):
        """Deletes the clip data node from the scene after confirmation.

        Args:
            *args: Optional Maya callback arguments.
        """
        cmds = get_maya_cmds()
        result = cmds.confirmDialog(
            title="Delete Scene Data",
            message="Delete the clip data node from this scene?\n"
            "Every clip stored in the current scene will be removed.",
            button=["Delete", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if result != "Delete":
            return
        self.model.delete_scene_data()
        self.playing_index = None
        self.selected_index = -1
        if self.view.window_exists():
            self.view.draw_clips(self.model.get_data(), self.playing_index)

    def set_preferences_collapsed(self, state):
        """Stores preferences collapsed state.

        Args:
            state (bool): Collapsed state.
        """
        self.model.preferences_collapsed = bool(state)
        self.model.save_preferences()

    def sync_bookmarks(self, *args):
        """Synchronizes clips from Maya time slider bookmarks.

        Args:
            *args: Optional Maya callback arguments.
        """
        added_count = self.model.sync_from_time_slider_bookmarks()
        self.model.log("Imported {0} time slider bookmark(s).".format(added_count))
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def reorder_clips(self, *args):
        """Reorders clips by start and end frame.

        Args:
            *args: Optional Maya callback arguments.
        """
        self.model.reorder_clips()
        self.model.save_data()
        # Clip indices change, so the previous timeline selection no longer applies
        self.selected_index = -1
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def connect_timeline(self, timeline_widget):
        """Connects the timeline widget signals and starts its state sync.

        Args:
            timeline_widget (ClipTimelineWidget): Timeline widget to connect.
        """
        timeline_widget.frame_changed.connect(self.set_current_frame)
        timeline_widget.clip_modified.connect(self.update_clip_range)
        timeline_widget.clip_created.connect(self.create_clip_range)
        timeline_widget.clip_selected.connect(self.select_clip)
        timeline_widget.clip_delete_requested.connect(self.delete_clip)
        timeline_widget.clip_range_requested.connect(self.set_range)
        timeline_widget.clip_play_requested.connect(self.toggle_play)
        timeline_widget.add_clip_requested.connect(self.add_clip)
        timeline_widget.add_timeline_clip_requested.connect(self.add_timeline_clip)
        timeline_widget.refresh_requested.connect(self.refresh_from_timeline)
        self.start_timeline_sync()

    def start_timeline_sync(self):
        """Starts the timer that pushes Maya frame state into the timeline widget."""
        self.stop_timeline_sync()
        self._timeline_timer = ui_qt.QtCore.QTimer()
        self._timeline_timer.setInterval(200)
        self._timeline_timer.timeout.connect(self.sync_timeline_state)
        self._timeline_timer.start()

    def stop_timeline_sync(self):
        """Stops the timeline state sync timer."""
        if self._timeline_timer:
            self._timeline_timer.stop()
            self._timeline_timer = None

    def sync_timeline_state(self):
        """Pushes the playback range and current frame into the timeline widget."""
        if not self.view.window_exists() or not self.view.timeline_widget_alive():
            self.stop_timeline_sync()
            return
        range_start, range_end = self.model.get_timeline_range()
        self.view.timeline_widget.set_frame_state(range_start, range_end, self.model.get_current_frame())

    def set_current_frame(self, frame):
        """Sets the current Maya frame.

        Args:
            frame (int): Frame to set.
        """
        self.model.set_current_frame(frame)

    def refresh_from_timeline(self):
        """Refreshes clip data from a timeline context-menu request."""
        self.refresh(force=True)

    def update_clip_range(self, index, start_frame, end_frame):
        """Updates the start and end frames of a clip from the timeline widget.

        Args:
            index (int): Clip index.
            start_frame (int): New start frame.
            end_frame (int): New end frame.
        """
        self.model.update_clip_range(index, start_frame, end_frame)
        if not self.view.window_exists():
            return
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def create_clip_range(self, start_frame, end_frame):
        """Creates a clip from a range drawn in the timeline widget.

        Args:
            start_frame (int): Start frame.
            end_frame (int): End frame.
        """
        self.model.add_clip_range(start_frame=start_frame, end_frame=end_frame)
        self.selected_index = len(self.model.get_data()) - 1
        if not self.view.window_exists():
            return
        self.view.draw_clips(self.model.get_data(), self.playing_index)

    def select_clip(self, index):
        """Highlights the clip selected in the timeline widget.

        The matching clip row is highlighted too, and it is scrolled into view while
        the timeline is in "select" mode so long clip lists remain easy to navigate.

        Args:
            index (int): Clip index, or a negative value to clear the selection.
        """
        self.selected_index = int(index) if self.model.show_timeline else -1
        if not self.view.window_exists():
            return
        is_select_mode = self.model.timeline_mode == clip_constants.MODE_SELECT
        scroll_into_view = self.selected_index >= 0 and is_select_mode
        self.view.highlight_clip_row(self.selected_index, scroll_into_view=scroll_into_view)

    def install_focus_refresh_filter(self):
        """Installs a Qt event filter used for refresh-on-focus."""
        try:
            from maya import OpenMayaUI

            pointer = OpenMayaUI.MQtUtil.findWindow(self.view.WINDOW_NAME)
            if not pointer:
                return
            widget = ui_qt.shiboken.wrapInstance(int(pointer), ui_qt.QtWidgets.QWidget)
            self._focus_filter = ClipTrackerFocusFilter(controller=self)
            widget.installEventFilter(self._focus_filter)
        except Exception as exception:
            self.model.log("Unable to install focus refresh filter: {0}".format(exception))


class ClipTrackerFocusFilter(ui_qt.QtCore.QObject):
    """Qt event filter used to refresh clip data when the window regains focus."""

    def __init__(self, controller):
        """Initializes the focus event filter.

        Args:
            controller (ClipTrackerController): Controller to refresh.
        """
        super().__init__()
        self.controller = controller

    def eventFilter(self, watched, event):
        """Handles focus events.

        Args:
            watched (QObject): Watched object.
            event (QEvent): Qt event.

        Returns:
            bool: False so Qt continues normal processing.
        """
        event_type = event.type()
        if event_type == ui_qt.QtCore.QEvent.WindowActivate:
            if self.controller.model.refresh_on_focus and self.controller.view.window_exists():
                get_maya_cmds().evalDeferred(self.controller.deferred_refresh)
        return False
