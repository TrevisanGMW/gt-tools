"""
Animation Clip Tracker Model
"""
from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants
from gt.core.prefs import Prefs
import datetime
import json


PREFS_FILENAME = "anim_clip_tracker"
PREFS_KEY_STATE = "state"
CLIP_NODE_NAME = "animClipData"
CLIP_ATTR_NAME = "clipData"
CLIP_ATTR_EDITED = "clipDataLastEdited"
PREFERENCE_KEYS = [
    "preferences_collapsed",
    "validate_min_frames",
    "min_frames",
    "validate_max_frames",
    "max_frames",
    "detect_overlaps",
    "refresh_on_focus",
    "auto_add_timeline_clip",
    "sync_time_slider_bookmarks",
    "auto_reorder_clips",
    "confirm_delete_clip",
    "new_clip_at_current_frame",
    "write_scene_node",
    "show_timeline",
    "timeline_mode",
    "timeline_show_names",
    "timeline_sync_time_edit",
    "timeline_allow_outside_range",
    "timeline_magnet_enabled",
    "timeline_snap_tolerance",
]


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def get_open_maya():
    """Gets Maya API lazily.

    Returns:
        module: maya.api.OpenMaya module.
    """
    import maya.api.OpenMaya as om

    return om


class ClipTrackerModel:
    """Stores clip data in a Maya network node and stores tool preferences."""

    def __init__(self):
        """Initializes the clip tracker model."""
        self.prefs = Prefs(PREFS_FILENAME)
        self.clips = []
        self.last_edited = "Never"
        self.reset_preferences_to_defaults()
        self.load_preferences()
        self.load_data()

    def reset_preferences_to_defaults(self):
        """Resets preferences to default values."""
        self.preferences_collapsed = False
        self.validate_min_frames = False
        self.min_frames = 1
        self.validate_max_frames = False
        self.max_frames = 300
        self.detect_overlaps = True
        self.refresh_on_focus = False
        self.auto_add_timeline_clip = False
        self.sync_time_slider_bookmarks = False
        self.auto_reorder_clips = False
        self.confirm_delete_clip = True
        self.new_clip_at_current_frame = True
        self.write_scene_node = True
        self.show_timeline = False
        self.timeline_mode = clip_constants.DEFAULT_TIMELINE_MODE
        self.timeline_show_names = False
        self.timeline_sync_time_edit = True
        self.timeline_allow_outside_range = False
        self.timeline_magnet_enabled = True
        self.timeline_snap_tolerance = 10

    def load_preferences(self):
        """Loads persistent tool preferences."""
        data = self.prefs.get_raw_preferences().get(PREFS_KEY_STATE) or {}
        if not isinstance(data, dict):
            return
        for key in PREFERENCE_KEYS:
            if key in data:
                setattr(self, key, data.get(key))
        self.timeline_mode = clip_constants.get_valid_mode(self.timeline_mode)

    def save_preferences(self):
        """Saves persistent tool preferences."""
        self.prefs.preferences[PREFS_KEY_STATE] = {
            "preferences_collapsed": bool(self.preferences_collapsed),
            "validate_min_frames": bool(self.validate_min_frames),
            "min_frames": int(self.min_frames),
            "validate_max_frames": bool(self.validate_max_frames),
            "max_frames": int(self.max_frames),
            "detect_overlaps": bool(self.detect_overlaps),
            "refresh_on_focus": bool(self.refresh_on_focus),
            "auto_add_timeline_clip": bool(self.auto_add_timeline_clip),
            "sync_time_slider_bookmarks": bool(self.sync_time_slider_bookmarks),
            "auto_reorder_clips": bool(self.auto_reorder_clips),
            "confirm_delete_clip": bool(self.confirm_delete_clip),
            "new_clip_at_current_frame": bool(self.new_clip_at_current_frame),
            "write_scene_node": bool(self.write_scene_node),
            "show_timeline": bool(self.show_timeline),
            "timeline_mode": clip_constants.get_valid_mode(self.timeline_mode),
            "timeline_show_names": bool(self.timeline_show_names),
            "timeline_sync_time_edit": bool(self.timeline_sync_time_edit),
            "timeline_allow_outside_range": bool(self.timeline_allow_outside_range),
            "timeline_magnet_enabled": bool(self.timeline_magnet_enabled),
            "timeline_snap_tolerance": int(self.timeline_snap_tolerance),
        }
        self.prefs.save()

    def get_preference_values(self):
        """Gets the current value of every tool preference.

        Returns:
            dict: Preference values keyed by preference name.
        """
        return {key: getattr(self, key) for key in PREFERENCE_KEYS}

    def log(self, message):
        """Prints an informational message through Maya.

        Args:
            message (str): Message to print.
        """
        get_open_maya().MGlobal.displayInfo("[Clip Tracker] {0}".format(message))

    def load_data(self):
        """Loads clip data from the Maya scene."""
        cmds = get_maya_cmds()
        if not cmds.objExists(CLIP_NODE_NAME):
            self.clips = []
            self.last_edited = "Never"
            return
        if cmds.attributeQuery(CLIP_ATTR_NAME, node=CLIP_NODE_NAME, exists=True):
            data_string = cmds.getAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_NAME))
            if data_string:
                try:
                    self.clips = normalize_clip_data(json.loads(data_string))
                except ValueError:
                    self.clips = []
                    self.log("Failed to parse clip data from scene.")
            else:
                self.clips = []
        if cmds.attributeQuery(CLIP_ATTR_EDITED, node=CLIP_NODE_NAME, exists=True):
            self.last_edited = cmds.getAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_EDITED)) or "Never"

    def save_data(self):
        """Saves clip data to the Maya scene."""
        if not self.write_scene_node:
            return
        cmds = get_maya_cmds()
        if self.auto_reorder_clips:
            self.reorder_clips()
        if not cmds.objExists(CLIP_NODE_NAME):
            cmds.createNode("network", name=CLIP_NODE_NAME)
        if not cmds.attributeQuery(CLIP_ATTR_NAME, node=CLIP_NODE_NAME, exists=True):
            cmds.addAttr(CLIP_NODE_NAME, ln=CLIP_ATTR_NAME, dataType="string")
        if not cmds.attributeQuery(CLIP_ATTR_EDITED, node=CLIP_NODE_NAME, exists=True):
            cmds.addAttr(CLIP_NODE_NAME, ln=CLIP_ATTR_EDITED, dataType="string")
        cmds.setAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_NAME), json.dumps(self.clips), type="string")
        self.last_edited = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmds.setAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_EDITED), self.last_edited, type="string")

    def delete_scene_data(self):
        """Deletes the clip data node from the current scene.

        Returns:
            bool: True when a data node was deleted.
        """
        cmds = get_maya_cmds()
        self.clips = []
        self.last_edited = "Never"
        if not cmds.objExists(CLIP_NODE_NAME):
            self.log("No clip data node was found in this scene.")
            return False
        cmds.delete(CLIP_NODE_NAME)
        self.log('Deleted clip data node: "{0}"'.format(CLIP_NODE_NAME))
        return True

    def get_data(self):
        """Gets clip data.

        Returns:
            list: Clip dictionaries.
        """
        return self.clips

    def add_clip(self, active=True, name=""):
        """Adds a clip using the current preferences.

        The playback range is used unless new clips are set to start at the current frame.

        Args:
            active (bool, optional): Whether the clip is active.
            name (str, optional): Clip name.

        Returns:
            dict: Created clip data.
        """
        start_frame, end_frame = self.get_new_clip_range()
        return self.add_clip_range(start_frame=start_frame, end_frame=end_frame, active=active, name=name)

    def add_timeline_clip(self, active=True, name=""):
        """Adds a clip that matches the current playback range.

        Args:
            active (bool, optional): Whether the clip is active.
            name (str, optional): Clip name.

        Returns:
            dict: Created clip data.
        """
        start_frame, end_frame = self.get_timeline_range()
        return self.add_clip_range(start_frame=start_frame, end_frame=end_frame, active=active, name=name)

    def add_clip_range(self, start_frame, end_frame, active=True, name=""):
        """Adds a clip using explicit frame values.

        Args:
            start_frame (int): Start frame.
            end_frame (int): End frame.
            active (bool, optional): Whether the clip is active.
            name (str, optional): Clip name.

        Returns:
            dict: Created clip data.
        """
        clip = {"active": bool(active), "name": name, "start": int(start_frame), "end": int(end_frame)}
        self.clips.append(clip)
        self.save_data()
        return clip

    def get_new_clip_range(self):
        """Gets the frame range used by newly created clips.

        Returns:
            tuple: Start and end frames.
        """
        start_frame, end_frame = self.get_timeline_range()
        if not self.new_clip_at_current_frame:
            return start_frame, end_frame
        current_frame = self.get_current_frame()
        return current_frame, max(current_frame, end_frame)

    def add_timeline_clip_if_missing(self):
        """Adds the current timeline range when it is not already represented."""
        start_frame, end_frame = self.get_timeline_range()
        for clip in self.clips:
            if int(clip.get("start")) == start_frame and int(clip.get("end")) == end_frame:
                return
        self.add_timeline_clip(name="Timeline")

    def update_clip(self, index, key, value):
        """Updates one clip value.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            value (object): New value.
        """
        if 0 <= index < len(self.clips):
            if key in ["start", "end"]:
                value = int(value)
            self.clips[index][key] = value
            self.save_data()

    def update_clip_range(self, index, start_frame, end_frame):
        """Updates the start and end frames of a clip in one operation.

        Args:
            index (int): Clip index.
            start_frame (int): New start frame.
            end_frame (int): New end frame.
        """
        if 0 <= index < len(self.clips):
            self.clips[index]["start"] = int(start_frame)
            self.clips[index]["end"] = int(end_frame)
            self.save_data()

    def delete_clip(self, index):
        """Deletes a clip.

        Args:
            index (int): Clip index.
        """
        if 0 <= index < len(self.clips):
            deleted = self.clips.pop(index)
            self.save_data()
            self.log('Deleted clip: "{0}"'.format(deleted.get("name") or "Clip {0}".format(index + 1)))

    def move_clip(self, index, offset):
        """Moves one clip relative to its current list position.

        Args:
            index (int): Source clip index.
            offset (int): Position change, normally -1 or 1.

        Returns:
            bool: True when the clip order was changed.
        """
        index = int(index)
        target_index = index + int(offset)
        if index < 0 or index >= len(self.clips):
            return False
        if target_index < 0 or target_index >= len(self.clips):
            return False
        self.clips[index], self.clips[target_index] = self.clips[target_index], self.clips[index]
        self.save_data()
        return True

    def reorder_clips(self):
        """Sorts clips by start and end frame."""
        self.clips = sorted(self.clips, key=lambda clip: (int(clip.get("start", 0)), int(clip.get("end", 0))))

    def get_timeline_range(self):
        """Gets the current playback range.

        Returns:
            tuple: Start and end frames.
        """
        cmds = get_maya_cmds()
        return int(cmds.playbackOptions(query=True, min=True)), int(cmds.playbackOptions(query=True, max=True))

    def get_current_frame(self):
        """Gets the current Maya frame.

        Returns:
            int: Current frame.
        """
        return int(get_maya_cmds().currentTime(query=True))

    def set_current_frame(self, frame):
        """Sets the current Maya frame.

        Args:
            frame (int): Frame to set.
        """
        get_maya_cmds().currentTime(int(frame), edit=True)

    def set_playback_range(self, start_frame, end_frame):
        """Sets the Maya playback range.

        Args:
            start_frame (int): Start frame.
            end_frame (int): End frame.
        """
        get_maya_cmds().playbackOptions(min=start_frame, max=end_frame)

    def play_clip(self, start_frame, end_frame, pause_only=False):
        """Plays or pauses a clip.

        Args:
            start_frame (int): Start frame.
            end_frame (int): End frame.
            pause_only (bool, optional): Whether only pause should run.
        """
        cmds = get_maya_cmds()
        if pause_only:
            cmds.play(state=False)
            return
        self.set_playback_range(start_frame, end_frame)
        cmds.currentTime(start_frame, edit=True)
        cmds.play(state=True)

    def export_json(self, file_path):
        """Exports clips to JSON.

        Args:
            file_path (str): Output path.
        """
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(self.clips, json_file, indent=4)
        self.log('Exported clips to: "{0}"'.format(file_path))

    def import_json(self, file_path):
        """Imports clips from JSON.

        Args:
            file_path (str): Input path.
        """
        with open(file_path, "r", encoding="utf-8") as json_file:
            self.clips = normalize_clip_data(json.load(json_file))
        self.save_data()
        self.log('Imported clips from: "{0}"'.format(file_path))

    def sync_from_time_slider_bookmarks(self):
        """Attempts to import Maya time slider bookmarks as clips.

        Returns:
            int: Number of imported bookmarks.
        """
        bookmark_data = get_time_slider_bookmarks()
        if not bookmark_data:
            return 0
        existing_ranges = set((int(clip.get("start")), int(clip.get("end"))) for clip in self.clips)
        added_count = 0
        for bookmark in bookmark_data:
            frame_range = (bookmark.get("start"), bookmark.get("end"))
            if frame_range in existing_ranges:
                continue
            self.clips.append(
                {
                    "active": True,
                    "name": bookmark.get("name") or "Bookmark",
                    "start": int(bookmark.get("start")),
                    "end": int(bookmark.get("end")),
                }
            )
            added_count += 1
        if added_count:
            self.save_data()
        return added_count

    def get_clip_issues(self):
        """Gets validation issues for all clips.

        Returns:
            dict: Mapping of clip indices to issue data.
        """
        issues = {}
        for index, clip in enumerate(self.clips):
            duration = get_clip_duration(clip)
            messages = []
            severity = ""
            if self.validate_min_frames and duration < int(self.min_frames):
                messages.append("Duration is below minimum: {0} < {1}".format(duration, int(self.min_frames)))
                severity = "error"
            if self.validate_max_frames and duration > int(self.max_frames):
                messages.append("Duration is above maximum: {0} > {1}".format(duration, int(self.max_frames)))
                severity = "error"
            if int(clip.get("end", 0)) < int(clip.get("start", 0)):
                messages.append("End frame is before start frame.")
                severity = "error"
            if messages:
                issues[index] = {"severity": severity or "warning", "messages": messages}
        if self.detect_overlaps:
            for index, clip in enumerate(self.clips):
                overlaps = get_overlapping_clip_indices(index, clip, self.clips)
                if overlaps:
                    data = issues.setdefault(index, {"severity": "overlap", "messages": []})
                    if data.get("severity") != "error":
                        data["severity"] = "overlap"
                    data["messages"].append(
                        "Overlaps clip(s): {0}".format(", ".join(str(item + 1) for item in overlaps))
                    )
        return issues


def normalize_clip_data(data):
    """Normalizes clip data.

    Args:
        data (list): Raw clip data.

    Returns:
        list: Normalized clip data.
    """
    clips = []
    for clip in data if isinstance(data, list) else []:
        if not isinstance(clip, dict):
            continue
        start_frame = int(float(clip.get("start", 0)))
        end_frame = int(float(clip.get("end", start_frame)))
        clips.append(
            {
                "active": bool(clip.get("active", True)),
                "name": str(clip.get("name") or ""),
                "start": start_frame,
                "end": end_frame,
            }
        )
    return clips


def get_clip_duration(clip):
    """Gets a clip duration.

    Args:
        clip (dict): Clip data.

    Returns:
        int: Clip duration in frames.
    """
    return int(clip.get("end", 0)) - int(clip.get("start", 0)) + 1


def get_overlapping_clip_indices(index, clip, clips):
    """Gets indices of clips overlapping a clip.

    Args:
        index (int): Clip index.
        clip (dict): Clip data.
        clips (list): All clips.

    Returns:
        list: Overlapping clip indices.
    """
    overlaps = []
    start_frame = int(clip.get("start", 0))
    end_frame = int(clip.get("end", 0))
    for other_index, other_clip in enumerate(clips):
        if other_index == index:
            continue
        other_start = int(other_clip.get("start", 0))
        other_end = int(other_clip.get("end", 0))
        if start_frame <= other_end and other_start <= end_frame:
            overlaps.append(other_index)
    return overlaps


def get_time_slider_bookmarks():
    """Gets Maya time slider bookmark data when available.

    Returns:
        list: Bookmark dictionaries.
    """
    cmds = get_maya_cmds()
    bookmarks = []
    for node in cmds.ls(type="timeSliderBookmark") or []:
        start_frame = get_first_existing_attr(node, ["start", "startTime", "timeRangeStart"])
        end_frame = get_first_existing_attr(node, ["stop", "end", "stopTime", "timeRangeStop"])
        if start_frame is None or end_frame is None:
            continue
        name = get_first_existing_attr(node, ["name", "bookmarkName"]) or node
        bookmarks.append({"name": name, "start": int(start_frame), "end": int(end_frame)})
    return bookmarks


def get_first_existing_attr(node, attr_names):
    """Gets the first existing attribute value from a node.

    Args:
        node (str): Maya node.
        attr_names (list): Attribute names to try.

    Returns:
        object: Attribute value, or None.
    """
    cmds = get_maya_cmds()
    for attr_name in attr_names:
        if cmds.attributeQuery(attr_name, node=node, exists=True):
            return cmds.getAttr("{0}.{1}".format(node, attr_name))
    return None
