try:
    import maya.cmds as cmds
except ImportError:
    cmds = None
import copy
import uuid
import random
import json
import os
import glob
import sys
import subprocess
from datetime import datetime
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.resource_library as ui_res_lib
from gt.tools.anim_label_tracker import label_tracker_model

QtWidgets = ui_qt.QtWidgets
QtCore = ui_qt.QtCore
QtGui = ui_qt.QtGui

# --- DEFAULT EXAMPLE FILES ---

EXAMPLE_SCHEMA = """{
  "validation": {
    "full_coverage": true,
    "allow_overlap": false
  },
  "file_level": [
    {
      "type": "enum", "name": "quality", "label": "Quality", 
      "options": ["low", "medium", "high"], 
      "required": true, 
      "description": "Defines the overall animation fidelity and usability.\\n'high' means polished, clean mocap ready for production.\\n'medium' indicates acceptable data that requires some animation cleanup.\\n'low' means blocky, rough motion, significant foot sliding, or missing marker data."
    },
    {
      "type": "row",
      "items": [
        {
          "type": "string", "name": "source", "label": "Source",
          "required": true,
          "placeholder": "e.g. mocap_shoot_01",
          "description": "Identifies the origin of the animation.\\nThis could be a specific mocap shoot (e.g., 'mocap_shoot_01'), a dataset name, a vendor pipeline, or the intended game/cinematic project use-case."
        },
        {
          "type": "enum", "name": "gender", "label": "Gender",
        "options": ["male", "female"],
        "required": false,
          "description": "The apparent gender of the character when it can be determined clearly."
        }
      ]
    },
    {"type": "separator"},
    {
      "type": "row",
      "items": [
        {
          "type": "boolean", "name": "clipped", "label": "Clipped", 
          "required": true, 
          "description": "Set to true if this animation sequence was sliced or extracted from a longer continuous raw take.\\nUsually auto-defined by pipeline tools if clip metadata exists."
        },
        {
          "type": "boolean", "name": "labelled", "label": "Labelled", 
          "required": true, 
          "description": "Set to true once a human animator or an automated script has fully populated, verified, and signed off on the frame-range metadata for this file."
        },
        {
            "type": "boolean", "name": "commercial_use", "label": "Commercial Use",
            "required": true,
            "description": "Set to true when this file is cleared for commercial use."
        }
      ]
    }
  ],
  "frame_range": [
    {
      "type": "row",
      "items": [
        {
          "type": "enum", "name": "state", "label": "State", 
          "options": ["none", "idle", "walk", "jog", "run", "sprint", "turn_in_place", "transition", "mixed"], 
          "required": true, 
          "description": "The core locomotion or foundational action of the character.\\nUse 'none' if the character is completely still without an idle loop, or 'mixed' if the state changes too rapidly within the range to isolate."
        },
        {
          "type": "enum", "name": "style", "label": "Style", 
          "options": ["none", "relaxed", "combat", "tired", "drunk", "confident", "injured", "scared", "aggressive", "cautious", "stealth"], 
          "required": true, 
          "description": "The physical demeanor, personality, or emotional overlay driving the animation.\\nThis defines *how* the character moves rather than *what* they are doing (e.g., an 'aggressive' walk vs a 'tired' walk)."
        },
        {
          "type": "enum", "name": "stance", "label": "Stance", 
          "options": ["none", "stand", "crouch", "kneel", "prone", "sit", "crawl"], 
          "required": true, 
          "description": "The character's primary vertical posture.\\nThis should only change when the root structure or center of mass fundamentally shifts (e.g., dropping from a 'stand' to a 'crouch')."
        }
      ]
    },
    {"type": "separator"},
    {
      "type": "row",
      "items": [
        {
          "type": "enum", "name": "interaction_type", "label": "Interaction Type", 
          "options": ["none", "avoid", "carry_light", "carry_heavy", "navigate", "push_pull", "climb", "gesture"], 
          "required": true, 
          "description": "Categorizes how the character physically reacts to external objects or environments.\\n'avoid' = stepping around/over\\n'navigate' = moving through tight spaces/doors\\n'carry' = holding objects\\n'push_pull' = applying force.\\nSet to 'none' if moving freely in open space."
        },
        {
          "type": "enum", "name": "interaction_scope", "label": "Interaction Scope", 
          "options": ["full_body", "upper_body", "lower_body", "both_arms", "left_arm", "right_arm", "both_legs", "left_leg", "right_leg"], 
          "required": false, 
          "description": "Defines which body parts are actively constrained or driven by the interaction.\\nUse 'full_body' if the interaction shifts the center of mass or alters foot placement. Otherwise, specify isolated limbs."
        }
      ]
    },
    {"type": "separator"},
    {
      "type": "string", "name": "interaction_volumes", "label": "Interaction Volumes", 
      "required": false, 
      "automation": "detect_volumes.py",
      "placeholder": "e.g. box_01, door_02",
      "description": "A comma-separated list of exact scene node names (e.g., 'box_obstacle_01') representing the 3D bounding volumes the character interacts with.\\nMust match scene geometry precisely. Use 'none' if not applicable."
    },
    {
      "type": "string", "name": "interaction_context", "label": "Interaction Context", 
      "required": false, 
      "placeholder": "e.g. torch, phone, sword",
      "description": "Strictly about the prop or target. The real-world name of the item being interacted with when no 3D bounding box exists in the scene (e.g., 'torch', 'heavy_crate', 'low_doorway').\\nThis describes *what* the character interacts with, especially useful when no actual 3D volume exists in the scene.\\nIf the character isn't physically interacting with something, leave empty."
    },
    {"type": "separator"},
    {
      "type": "string", "name": "events", "label": "Events", 
      "required": false, 
      "placeholder": "e.g. {'foot_strike': [18, 32]}",
      "description": "A JSON-formatted dictionary mapping specific animation events to frame numbers (e.g., {'foot_strike': [18, 32], 'blend_start': [12]}).\\nUsed for precise AI training, tagging impacts, or syncing audio."
    },
    {
      "type": "string", "name": "auxiliary_context", "label": "Auxiliary Context", 
      "required": false, 
      "placeholder": "e.g. ground is slippery",
      "description": "Broad context covering narrative, environmental factors, or technical notes that alter the flavor of the animation but don't fit strict enums.\\nE.g., 'slippery ground', 'underwater physics applied', or 'actor's foot slid slightly at frame 102'."
    }
  ]
}"""

EXAMPLE_SCRIPT = '''\"\"\"
Example Automation Script for Range Tool.

This script runs with a globally injected `context` dictionary containing:

context["cmds"]                 # Maya cmds module
context["active_range"]         # The currently selected RangeItem object (or None)
context["timeline_ranges"]      # List of all RangeItem objects in the timeline
context["field_name"]           # Name of the specific field this script was triggered from (if any)
context["set_value"](val)       # Sets the UI value for the triggering field directly

# Advanced API functions:
context["get_last_used_data"]() # Returns the last tracker data stored in Prefs
context["create_range"](name, start, end, color)         # Creates, automatically selects, and returns a new RangeItem
context["get_file_data"](field)                          # Returns the current value of a File Data field
context["update_file_data"](field, val)                  # Updates File Data
context["update_range_data"](field, val)                 # Updates Range Data for the active range
context["refresh_ui"]()                                  # Forces the UI to update to reflect code changes
\"\"\"

# =====================================================================
# 1. Update File Data
# =====================================================================
last_used_data = context["get_last_used_data"]()
print("Last used tracker data from Prefs:")
print(last_used_data)

context["update_file_data"]("quality", "high")
context["update_file_data"]("source", "mocap_shoot_01")
context["update_file_data"]("clipped", True)
context["update_file_data"]("labelled", True)
context["update_file_data"]("commercial_use", True)
context["update_file_data"]("gender", "male")

# =====================================================================
# 2. Automatically generate a full-coverage range
# =====================================================================
start_frame = int(context["cmds"].playbackOptions(q=True, min=True))
end_frame = int(context["cmds"].playbackOptions(q=True, max=True))

context["timeline_ranges"].clear() # Clear existing
new_range = context["create_range"]("Auto_Generated", start_frame, end_frame, (100, 200, 100))

# =====================================================================
# 3. Populate fields dynamically
# =====================================================================
context["update_range_data"]("state", "walk")
context["update_range_data"]("style", "confident")
context["update_range_data"]("stance", "stand")

context["update_range_data"]("interaction_type", "navigate")
context["update_range_data"]("interaction_scope", "full_body")
context["update_range_data"]("interaction_volumes", "doorway_volume_01")
context["update_range_data"]("interaction_context", "heavy_door")

context["update_range_data"]("events", '{"foot_strike": [15, 30, 45]}')
context["update_range_data"]("auxiliary_context", "Floor is slightly uneven.")

print("Generated a full-coverage valid frame range automatically!")
context["refresh_ui"]()
'''

# --- DATA MODEL (Scene Persistence) ---

class DataManager:
    NODE_NAME = "rangeTimelineData"
    ATTR_DATA = "timelineData"
    ATTR_EDITED = "lastEdited"

    @classmethod
    def build_payload(cls, ranges, file_data):
        """Builds JSON-compatible tracker data without touching Maya.

        Args:
            ranges (list): Range items to serialize.
            file_data (dict): File-level metadata to serialize.

        Returns:
            dict: JSON-compatible tracker data.
        """
        range_data = []
        for range_item in ranges:
            range_data.append(
                {
                    "id": range_item.id,
                    "name": range_item.name,
                    "start": range_item.start,
                    "end": range_item.end,
                    "color": range_item.color,
                    "locked": range_item.locked,
                    "custom_data": range_item.custom_data,
                }
            )
        return {"ranges": range_data, "file_data": copy.deepcopy(file_data)}

    @classmethod
    def save_data(cls, ranges, file_data):
        """Serializes range and file metadata to tracker scene data.

        Args:
            ranges (list): Range items to serialize.
            file_data (dict): File-level metadata to serialize.

        Returns:
            dict: JSON-compatible tracker data.
        """
        if not cmds.objExists(cls.NODE_NAME):
            cmds.createNode('network', name=cls.NODE_NAME)
            
        if not cmds.attributeQuery(cls.ATTR_DATA, node=cls.NODE_NAME, exists=True):
            cmds.addAttr(cls.NODE_NAME, ln=cls.ATTR_DATA, dataType="string")
            
        if not cmds.attributeQuery(cls.ATTR_EDITED, node=cls.NODE_NAME, exists=True):
            cmds.addAttr(cls.NODE_NAME, ln=cls.ATTR_EDITED, dataType="string")
            
        payload = cls.build_payload(ranges, file_data)
        json_str = json.dumps(payload)
        cmds.setAttr(f"{cls.NODE_NAME}.{cls.ATTR_DATA}", json_str, type="string")
        
        last_edited = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmds.setAttr(f"{cls.NODE_NAME}.{cls.ATTR_EDITED}", last_edited, type="string")

    @classmethod
    def load_data(cls):
        """Loads serialized tracker data from the current Maya scene.

        Returns:
            tuple: Loaded ranges and file metadata.
        """
        if not cmds.objExists(cls.NODE_NAME): return [], {}
        if not cmds.attributeQuery(cls.ATTR_DATA, node=cls.NODE_NAME, exists=True): return [], {}
            
        data_str = cmds.getAttr(f"{cls.NODE_NAME}.{cls.ATTR_DATA}")
        if not data_str: return [], {}
            
        try:
            payload = json.loads(data_str)
            r_data = payload.get("ranges", [])
            file_data = payload.get("file_data", {})
            
            ranges = []
            for d in r_data:
                c = d.get("color", [128, 128, 128])
                r = RangeItem(d.get("name", ""), d.get("start", 0), d.get("end", 1), tuple(c))
                r.id = d.get("id", str(uuid.uuid4()))
                r.locked = d.get("locked", False)
                r.custom_data = d.get("custom_data", {})
                ranges.append(r)
            return ranges, file_data
        except Exception as e:
            cmds.warning(f"Failed to parse timeline data from scene: {e}")
            return [], {}

# --- TOOL UI & LOGIC ---

class RangeItem:
    def __init__(self, name, start, end, color):
        """Initializes a labeled timeline range.

        Args:
            name (str): User-facing range name.
            start (float): Range start frame.
            end (float): Range end frame.
            color (tuple): RGB color used to display the range.
        """
        self.id = str(uuid.uuid4())
        self.name = name  
        self.start = start
        self.end = end
        self.color = color
        self.locked = False
        self.custom_data = {} 
        
    @property
    def display_name(self):
        """Returns the display label for this range.

        Returns:
            str: Display name, including any required range metadata.
        """
        if self.name and self.name.strip(): return self.name
        return f"f{self.start:04d}-f{self.end:04d}"


def pack_range_lanes(ranges):
    """Assigns overlapping timeline ranges to separate visual lanes.

    Args:
        ranges (list): Range items with ``start`` and ``end`` values.

    Returns:
        dict: Mapping of range indices to zero-based lane indices.
    """
    lane_ends = []
    lanes = {}
    ranges = list(ranges or [])
    ordered_indices = sorted(
        range(len(ranges)),
        key=lambda index: (
            min(ranges[index].start, ranges[index].end),
            max(ranges[index].start, ranges[index].end),
        ),
    )
    for index in ordered_indices:
        range_item = ranges[index]
        start_frame = min(range_item.start, range_item.end)
        end_frame = max(range_item.start, range_item.end)
        target_lane = None
        for lane_index, lane_end in enumerate(lane_ends):
            if start_frame > lane_end:
                target_lane = lane_index
                break
        if target_lane is None:
            lane_ends.append(end_frame)
            target_lane = len(lane_ends) - 1
        else:
            lane_ends[target_lane] = max(lane_ends[target_lane], end_frame)
        lanes[index] = target_lane
    return lanes


class CustomTimelineWidget(QtWidgets.QWidget):
    rangeSelected = QtCore.Signal(object) 
    timeChanged = QtCore.Signal(int)
    rangesChanged = QtCore.Signal() 

    def __init__(self, parent=None):
        """Initializes the interactive range timeline widget.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super(CustomTimelineWidget, self).__init__(parent)
        self.setMinimumHeight(100)
        self.setMouseTracking(True) 
        
        self.start_frame = int(cmds.playbackOptions(q=True, min=True))
        self.end_frame = int(cmds.playbackOptions(q=True, max=True))
        self.current_frame = int(cmds.currentTime(q=True))
        self.ranges = []
        
        self.pref_show_frames = True
        self.pref_show_names = False
        self.pref_random_colors = True
        self.pref_sync_time = True
        self.pref_limit_bounds = True
        self.pref_razor_random_colors = True 
        
        self.tool_mode = 'edit'
        self.magnet_enabled = True
        self.snap_threshold = 10
        self.auto_crop_enabled = False
        self.crop_tolerance = 10
        self.auto_stretch_enabled = False
        self.stretch_tolerance = 10
        
        self.interaction_state = None 
        self.active_range = None
        self.click_start_pos = 0
        self.click_start_frame = 0
        self.initial_range_start = 0 
        self.drag_accum = 0.0 

    def get_lane_geometry(self):
        """Gets visual lane positions for the current timeline ranges.

        Returns:
            tuple: Range-index lane mapping, lane height, and top offset.
        """
        lanes = pack_range_lanes(self.ranges)
        lane_count = max(lanes.values()) + 1 if lanes else 1
        top_offset = 20
        bottom_margin = 20
        lane_spacing = 3
        available_height = self.height() - top_offset - bottom_margin
        lane_height = int((available_height - (lane_spacing * (lane_count - 1))) / lane_count)
        return lanes, max(8, lane_height), top_offset

    def get_range_rect(self, range_item, index, lanes, lane_height, top_offset):
        """Builds the visual rectangle for one timeline range.

        Args:
            range_item (RangeItem): Timeline range being drawn.
            index (int): Range index in the timeline collection.
            lanes (dict): Range-index lane mapping.
            lane_height (int): Height of each visual lane.
            top_offset (int): Vertical offset of the first lane.

        Returns:
            QRect: Visual rectangle for the range.
        """
        x_start = self.frame_to_x(range_item.start)
        x_end = self.frame_to_x(range_item.end)
        width = max(x_end - x_start, 5)
        lane_spacing = 3
        lane_index = lanes.get(index, 0)
        y_position = top_offset + (lane_index * (lane_height + lane_spacing))
        if range_item.locked:
            y_position += 5
            lane_height = max(3, lane_height - 10)
        return QtCore.QRect(x_start, y_position, width, lane_height)

    def frame_to_x(self, frame):
        """Converts a Maya frame value to a timeline x-coordinate.

        Args:
            frame (float): Frame value to convert.

        Returns:
            float: Corresponding widget x-coordinate.
        """
        width = self.width()
        frame_range = self.end_frame - self.start_frame
        if frame_range <= 0: return 0
        return int(((frame - self.start_frame) / frame_range) * width)

    def x_to_frame(self, x):
        """Converts a timeline x-coordinate to a Maya frame value.

        Args:
            x (float): Widget x-coordinate to convert.

        Returns:
            float: Corresponding frame value.
        """
        width = self.width()
        frame_range = self.end_frame - self.start_frame
        frame = self.start_frame + (float(x) / width) * frame_range
        return round(frame)

    def get_range_and_zone_at_x(self, x, y=None):
        """Finds the range and edge zone under a widget coordinate.

        Args:
            x (float): Widget x-coordinate to inspect.
            y (float, optional): Widget y-coordinate to inspect.

        Returns:
            tuple: Range item and interaction zone, or ``(None, None)``.
        """
        frame = self.x_to_frame(x)
        tolerance_px = 6
        lanes, lane_height, top_offset = self.get_lane_geometry()
        for index in reversed(range(len(self.ranges))):
            range_item = self.ranges[index]
            range_rect = self.get_range_rect(range_item, index, lanes, lane_height, top_offset)
            x_start = range_rect.left()
            x_end = range_rect.right()
            if y is not None and not range_rect.adjusted(-tolerance_px, 0, tolerance_px, 0).contains(x, y):
                continue
            if x_start - tolerance_px <= x <= x_end + tolerance_px:
                if range_item.locked or self.tool_mode != 'edit':
                    if range_item.start <= frame <= range_item.end: return range_item, 'center'
                else:
                    if abs(x - x_start) <= tolerance_px: return range_item, 'left'
                    elif abs(x - x_end) <= tolerance_px: return range_item, 'right'
                    elif range_item.start <= frame <= range_item.end: return range_item, 'center'
        return None, None

    def get_snap_frame(self, proposed_frame, edge_type, ignore_range=None):
        """Resolves a proposed frame against nearby snapping targets.

        Args:
            proposed_frame (float): Frame value being positioned.
            edge_type (str): Edge being moved, such as ``start`` or ``end``.
            ignore_range (RangeItem, optional): Range excluded from snapping.

        Returns:
            float: Snapped or unchanged frame value.
        """
        if not self.magnet_enabled: return None
        closest_dist = self.snap_threshold + 1
        snapped_frame = None
        for r in self.ranges:
            if r is ignore_range: continue
            if edge_type == 'start':
                target = r.end + 1
                dist = abs(target - proposed_frame)
                if dist <= self.snap_threshold and dist < closest_dist:
                    closest_dist = dist; snapped_frame = target
            elif edge_type == 'end':
                target = r.start - 1
                dist = abs(target - proposed_frame)
                if dist <= self.snap_threshold and dist < closest_dist:
                    closest_dist = dist; snapped_frame = target
        return snapped_frame

    def adjust_adjacent_ranges(self):
        """Adjusts adjacent ranges using the current snapping preferences.

        Returns:
            list: Ranges changed by the adjustment.
        """
        return label_tracker_model.adjust_adjacent_ranges(
            self.active_range,
            self.ranges,
            auto_crop=self.auto_crop_enabled,
            crop_tolerance=self.crop_tolerance,
            auto_stretch=self.auto_stretch_enabled,
            stretch_tolerance=self.stretch_tolerance,
        )

    def paintEvent(self, event):
        """Paints timeline ranges, labels, and interaction markers.

        Args:
            event (QPaintEvent): Qt paint event supplied by the widget system.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        painter.fillRect(rect, QtGui.QColor(40, 40, 40))
        painter.setPen(QtGui.QColor(150, 150, 150))
        frame_range = int(self.end_frame - self.start_frame)
        step = max(1, frame_range // 20) 
        for f in range(int(self.start_frame), int(self.end_frame) + 1, step):
            x = self.frame_to_x(f)
            painter.drawLine(x, rect.height() - 15, x, rect.height())
            painter.drawText(x + 2, rect.height() - 2, str(f))

        lanes, lane_height, top_offset = self.get_lane_geometry()
        for index, range_item in enumerate(self.ranges):
            range_rect = self.get_range_rect(range_item, index, lanes, lane_height, top_offset)
            
            color = QtGui.QColor(*range_item.color)
            color.setAlpha(150)
            if range_item.locked:
                brush = QtGui.QBrush(color, QtCore.Qt.BrushStyle.BDiagPattern)
                painter.fillRect(range_rect, QtGui.QColor(60, 60, 60, 150))
                painter.fillRect(range_rect, brush)
            else:
                painter.fillRect(range_rect, color)
            
            if range_item == self.active_range: painter.setPen(QtGui.QPen(QtGui.QColor(255, 200, 50), 3))
            else: painter.setPen(QtGui.QPen(QtGui.QColor(*range_item.color), 2))
            painter.drawRect(range_rect)
            
            if self.pref_show_names:
                painter.setPen(QtGui.QColor(255, 255, 255))
                painter.drawText(range_rect, QtCore.Qt.AlignmentFlag.AlignCenter, range_item.display_name)
            if self.pref_show_frames:
                bold_font = painter.font()
                bold_font.setPointSize(bold_font.pointSize() + 1); bold_font.setBold(True)
                painter.setFont(bold_font)
                painter.setPen(QtGui.QColor(220, 220, 220, 220))
                text_rect = range_rect.adjusted(3, 0, -3, -2)
                left_alignment = (
                    QtCore.Qt.AlignmentFlag.AlignBottom
                    | QtCore.Qt.AlignmentFlag.AlignLeft
                )
                right_alignment = (
                    QtCore.Qt.AlignmentFlag.AlignBottom
                    | QtCore.Qt.AlignmentFlag.AlignRight
                )
                painter.drawText(text_rect, left_alignment, str(range_item.start))
                painter.drawText(text_rect, right_alignment, str(range_item.end))

        cx = self.frame_to_x(self.current_frame)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 50, 50), 2))
        painter.drawLine(cx, 0, cx, rect.height())

    def mousePressEvent(self, event):
        """Begins range selection or edge manipulation from a mouse press.

        Args:
            event (QMouseEvent): Qt mouse press event.
        """
        event_position = event.position()
        event_x = int(event_position.x())
        clicked_range, zone = self.get_range_and_zone_at_x(event_x, int(event_position.y()))
        playhead_x = self.frame_to_x(self.current_frame)

        if event.button() == QtCore.Qt.MouseButton.RightButton:
            if clicked_range:
                self.active_range = clicked_range
                self.rangeSelected.emit(self.active_range)
                
            menu = QtWidgets.QMenu(self)
            action_lock = menu.addAction(
                QtGui.QIcon(ui_res_lib.Icon.ui_read_only),
                "Unlock" if clicked_range.locked else "Lock",
            )
            action_del = menu.addAction(
                QtGui.QIcon(ui_res_lib.Icon.ui_delete),
                "Delete",
            )
                
            action = menu.exec(event.globalPosition().toPoint())
            if action == action_lock:
                    clicked_range.locked = not clicked_range.locked
                    self.rangeSelected.emit(self.active_range)
                    self.rangesChanged.emit() # Save trigger
                    self.update()
            elif action == action_del:
                    self.ranges.remove(clicked_range)
                    self.active_range = None
                    self.rangeSelected.emit(None)
                    self.rangesChanged.emit() # Save trigger
                    self.update()
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.click_start_pos = event_x
            self.click_start_frame = self.x_to_frame(event_x)
            
            if self.tool_mode in ['select', 'navigate'] and abs(event_x - playhead_x) <= 8:
                self.interaction_state = 'scrubbing'
                self.current_frame = self.click_start_frame
                cmds.currentTime(self.current_frame)
                self.timeChanged.emit(self.current_frame); self.update()
                return

            if self.tool_mode == 'navigate':
                self.interaction_state = 'scrubbing'
                self.current_frame = self.click_start_frame
                cmds.currentTime(self.current_frame)
                self.timeChanged.emit(self.current_frame)
            elif self.tool_mode == 'select':
                self.active_range = clicked_range
                self.rangeSelected.emit(self.active_range)
            elif self.tool_mode == 'razor':
                if clicked_range and clicked_range.start <= self.click_start_frame < clicked_range.end:
                    n1 = clicked_range.name + "_01" if clicked_range.name else ""
                    n2 = clicked_range.name + "_02" if clicked_range.name else ""
                    c1, c2 = clicked_range.color, clicked_range.color
                    if self.pref_razor_random_colors:
                        c1 = (random.randint(60, 220), random.randint(60, 220), random.randint(60, 220))
                        c2 = (random.randint(60, 220), random.randint(60, 220), random.randint(60, 220))
                    r1 = RangeItem(n1, clicked_range.start, self.click_start_frame, c1)
                    r2 = RangeItem(n2, self.click_start_frame + 1, clicked_range.end, c2)
                    import copy
                    r1.custom_data = copy.deepcopy(clicked_range.custom_data)
                    r2.custom_data = copy.deepcopy(clicked_range.custom_data)
                    idx = self.ranges.index(clicked_range)
                    self.ranges.pop(idx); self.ranges.insert(idx, r1); self.ranges.insert(idx+1, r2)
                    self.active_range = r2
                    self.rangeSelected.emit(self.active_range)
                    self.rangesChanged.emit() 
                else:
                    self.current_frame = self.click_start_frame
                    cmds.currentTime(self.current_frame)
                    self.timeChanged.emit(self.current_frame)
            elif self.tool_mode == 'edit':
                if clicked_range:
                    self.active_range = clicked_range
                    self.rangeSelected.emit(self.active_range)
                    self.drag_accum = 0.0
                    if clicked_range.locked: self.interaction_state = None 
                    else:
                        if zone == 'left': self.interaction_state = 'resizing_left'
                        elif zone == 'right': self.interaction_state = 'resizing_right'
                        else: 
                            self.interaction_state = 'moving'
                            self.initial_range_start = clicked_range.start
                else:
                    self.active_range = None
                    self.rangeSelected.emit(None)
                    self.interaction_state = 'scrubbing_edit'
                    self.current_frame = self.click_start_frame
                    cmds.currentTime(self.current_frame)
                    self.timeChanged.emit(self.current_frame)
            self.update()

    def mouseMoveEvent(self, event):
        """Updates the active range while the mouse is being dragged.

        Args:
            event (QMouseEvent): Qt mouse move event.
        """
        current_x = int(event.position().x())
        current_hover_frame = self.x_to_frame(current_x)
        playhead_x = self.frame_to_x(self.current_frame)
        
        if not self.interaction_state:
            if self.tool_mode == 'select' and abs(current_x - playhead_x) <= 8:
                self.setCursor(QtCore.Qt.CursorShape.SizeWECursor)
            elif self.tool_mode == 'edit':
                _, zone = self.get_range_and_zone_at_x(current_x, int(event.position().y()))
                if zone in ('left', 'right'): self.setCursor(QtCore.Qt.CursorShape.SplitHCursor)
                else: self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            elif self.tool_mode == 'razor': self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
            else: self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            return

        is_precision = event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        min_bounds = self.start_frame if self.pref_limit_bounds else -100000
        max_bounds = self.end_frame if self.pref_limit_bounds else 100000

        if self.interaction_state == 'scrubbing':
            self.current_frame = current_hover_frame
            cmds.currentTime(self.current_frame); self.timeChanged.emit(self.current_frame)
            
        elif self.interaction_state == 'scrubbing_edit':
            if abs(current_x - self.click_start_pos) > 10: 
                self.interaction_state = 'creating'
                col = (random.randint(60, 220), random.randint(60, 220), random.randint(60, 220)) if self.pref_random_colors else (128, 128, 128)
                self.active_range = RangeItem("", self.click_start_frame, current_hover_frame, col)
                self.ranges.append(self.active_range)
                self.rangeSelected.emit(self.active_range)
            else:
                self.current_frame = current_hover_frame
                cmds.currentTime(self.current_frame); self.timeChanged.emit(self.current_frame)
                
        elif self.interaction_state == 'creating':
            s = max(min_bounds, min(self.click_start_frame, current_hover_frame)) if self.pref_limit_bounds else min(self.click_start_frame, current_hover_frame)
            e = min(max_bounds, max(self.click_start_frame, current_hover_frame)) if self.pref_limit_bounds else max(self.click_start_frame, current_hover_frame)
            self.active_range.start, self.active_range.end = s, e
            self.rangeSelected.emit(self.active_range)
            if self.pref_sync_time:
                self.current_frame = current_hover_frame
                cmds.currentTime(self.current_frame); self.timeChanged.emit(self.current_frame)
                
        elif self.interaction_state == 'resizing_left':
            p = min(current_hover_frame, self.active_range.end - 1)
            if self.pref_limit_bounds: p = max(min_bounds, p)
            snap = self.get_snap_frame(p, 'start', self.active_range)
            self.active_range.start = snap if snap is not None else p
            self.rangeSelected.emit(self.active_range) 
            
        elif self.interaction_state == 'resizing_right':
            p = max(current_hover_frame, self.active_range.start + 1)
            if self.pref_limit_bounds: p = min(max_bounds, p)
            snap = self.get_snap_frame(p, 'end', self.active_range)
            self.active_range.end = snap if snap is not None else p
            self.rangeSelected.emit(self.active_range) 
            
        elif self.interaction_state == 'moving':
            raw_delta = current_hover_frame - self.click_start_frame
            delta = int(raw_delta * 0.2) if is_precision else raw_delta

            length = self.active_range.end - self.active_range.start
            prop_s = max(min_bounds, min(max_bounds - length, self.initial_range_start + delta))
            
            if self.magnet_enabled:
                snap_s = self.get_snap_frame(prop_s, 'start', self.active_range)
                snap_e = self.get_snap_frame(prop_s + length, 'end', self.active_range)
                
                ds = abs(snap_s - prop_s) if snap_s is not None else 9999
                de = abs(snap_e - (prop_s + length)) if snap_e is not None else 9999
                
                if snap_s is not None and (ds <= de):
                    prop_s = snap_s
                elif snap_e is not None:
                    prop_s = snap_e - length

            if self.active_range.start != prop_s:
                self.active_range.start = prop_s
                self.active_range.end = prop_s + length
                self.rangeSelected.emit(self.active_range) 
        self.update()

    def mouseReleaseEvent(self, event):
        """Finishes the current range drag interaction.

        Args:
            event (QMouseEvent): Qt mouse release event.
        """
        if self.interaction_state in ['creating', 'moving', 'resizing_left', 'resizing_right']:
            self.adjust_adjacent_ranges()
            self.rangesChanged.emit()
        self.interaction_state = None
        self.update()

class RangeToolWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """Initializes the animation label tracker window.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super(RangeToolWindow, self).__init__(parent)
        self.setWindowTitle("Animation Label Tracker")
        self.resize(900, 450)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.sj_id = None
        if not getattr(self, "model", None):
            self.model = label_tracker_model.AnimationLabelTrackerModel()
        self._suspend_last_used_data = False
        self._is_loading_data = False
        
        self.schema = {}
        self.file_data = {}
        self.scene_file_data_cache = {}
        self._is_building_ui = False
        
        self.ui_widgets_file = {}
        self.ui_widgets_range = {}
        
        # Load from scene initially
        loaded_ranges, loaded_file_data = DataManager.load_data()
        self.scene_file_data_cache = loaded_file_data
        
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # --- TOP BAR ---
        top_layout = QtWidgets.QHBoxLayout()
        ro_style = "QLineEdit { background-color: #3b3b3b; color: #999999; border: 1px solid #2b2b2b; }"
        
        top_layout.addWidget(QtWidgets.QLabel("Start:"))
        self.start_fld = QtWidgets.QLineEdit()
        self.start_fld.setReadOnly(True); self.start_fld.setStyleSheet(ro_style); self.start_fld.setMaximumWidth(60)
        top_layout.addWidget(self.start_fld)
        top_layout.addStretch()
        
        top_layout.addWidget(QtWidgets.QLabel("Current:"))
        self.current_fld = QtWidgets.QSpinBox()
        self.current_fld.setRange(-10000, 10000)
        self.current_fld.valueChanged.connect(self.on_current_field_changed)
        top_layout.addWidget(self.current_fld)
        top_layout.addStretch()
        
        top_layout.addWidget(QtWidgets.QLabel("End:"))
        self.end_fld = QtWidgets.QLineEdit()
        self.end_fld.setReadOnly(True); self.end_fld.setStyleSheet(ro_style); self.end_fld.setMaximumWidth(60)
        top_layout.addWidget(self.end_fld)
        main_layout.addLayout(top_layout)
        
        # --- TIMELINE ---
        self.timeline = CustomTimelineWidget()
        self.timeline.ranges = loaded_ranges # Inject scene data
        self.timeline.timeChanged.connect(self.sync_current_field)
        self.timeline.rangeSelected.connect(self.populate_edit_area)
        self.timeline.rangesChanged.connect(self.on_ranges_changed) # Hooks into save loop
        main_layout.addWidget(self.timeline)
        
        # --- TABS ---
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 1. Tools Tab 
        self.tab_tools = QtWidgets.QScrollArea()
        self.tab_tools.setWidgetResizable(True)
        self.tab_tools.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.tools_widget = QtWidgets.QWidget()
        self.tools_layout = QtWidgets.QVBoxLayout(self.tools_widget)
        
        mode_grp_box = QtWidgets.QGroupBox("Mode")
        mode_layout = QtWidgets.QHBoxLayout(mode_grp_box)
        self.tool_grp = QtWidgets.QButtonGroup(self)
        self.rad_nav = QtWidgets.QRadioButton("Navigate")
        self.rad_sel = QtWidgets.QRadioButton("Select")
        self.rad_edit = QtWidgets.QRadioButton("Edit")
        self.rad_edit.setChecked(True)
        self.rad_raz = QtWidgets.QRadioButton("Razor")
        for i, rb in enumerate([self.rad_nav, self.rad_sel, self.rad_edit, self.rad_raz], 1):
            self.tool_grp.addButton(rb, i)
            mode_layout.addWidget(rb)
        self.tool_grp.buttonClicked.connect(self.on_tool_mode_changed)
        self.tools_layout.addWidget(mode_grp_box)
        
        snap_grp_box = QtWidgets.QGroupBox("Snapping")
        snap_layout = QtWidgets.QVBoxLayout(snap_grp_box)
        snap_layout.setSpacing(6)
        magnet_layout = QtWidgets.QHBoxLayout()
        magnet_layout.setSpacing(10)
        self.chk_magnet = QtWidgets.QCheckBox("Enable Magnet")
        self.chk_magnet.setChecked(self.timeline.magnet_enabled)
        self.chk_magnet.stateChanged.connect(self.on_tool_mode_changed)
        self.chk_magnet.setToolTip(
            "Snaps range edges to nearby range edges.\n"
            "Tolerance controls the maximum snapping distance."
        )
        magnet_layout.addWidget(self.chk_magnet)
        magnet_layout.addStretch()
        magnet_layout.addWidget(QtWidgets.QLabel("Tolerance:"))
        self.spin_magnet = QtWidgets.QSpinBox(); self.spin_magnet.setRange(1, 100); self.spin_magnet.setValue(self.timeline.snap_threshold)
        self.spin_magnet.valueChanged.connect(self.on_magnet_tolerance_changed)
        self.spin_magnet.setMinimumWidth(55)
        magnet_layout.addWidget(self.spin_magnet)
        snap_layout.addLayout(magnet_layout)

        crop_layout = QtWidgets.QHBoxLayout()
        crop_layout.setSpacing(10)
        self.chk_auto_crop = QtWidgets.QCheckBox("Auto Crop")
        self.chk_auto_crop.setChecked(self.timeline.auto_crop_enabled)
        self.chk_auto_crop.setToolTip(
            "Shortens adjacent ranges to prevent overlaps.\n"
            "Tolerance limits the overlap corrected automatically."
        )
        self.chk_auto_crop.stateChanged.connect(self.on_auto_snapping_changed)
        crop_layout.addWidget(self.chk_auto_crop)
        crop_layout.addStretch()
        crop_layout.addWidget(QtWidgets.QLabel("Tolerance:"))
        self.spin_crop_tolerance = QtWidgets.QSpinBox()
        self.spin_crop_tolerance.setRange(1, 100)
        self.spin_crop_tolerance.setValue(self.timeline.crop_tolerance)
        self.spin_crop_tolerance.setMinimumWidth(55)
        self.spin_crop_tolerance.valueChanged.connect(self.on_auto_snapping_changed)
        crop_layout.addWidget(self.spin_crop_tolerance)
        snap_layout.addLayout(crop_layout)

        stretch_layout = QtWidgets.QHBoxLayout()
        stretch_layout.setSpacing(10)
        self.chk_auto_stretch = QtWidgets.QCheckBox("Auto Stretch")
        self.chk_auto_stretch.setChecked(self.timeline.auto_stretch_enabled)
        self.chk_auto_stretch.setToolTip(
            "Extends adjacent ranges to close gaps.\n"
            "Tolerance limits the gap corrected automatically."
        )
        self.chk_auto_stretch.stateChanged.connect(self.on_auto_snapping_changed)
        stretch_layout.addWidget(self.chk_auto_stretch)
        stretch_layout.addStretch()
        stretch_layout.addWidget(QtWidgets.QLabel("Tolerance:"))
        self.spin_stretch_tolerance = QtWidgets.QSpinBox()
        self.spin_stretch_tolerance.setRange(1, 100)
        self.spin_stretch_tolerance.setValue(self.timeline.stretch_tolerance)
        self.spin_stretch_tolerance.setMinimumWidth(55)
        self.spin_stretch_tolerance.valueChanged.connect(self.on_auto_snapping_changed)
        stretch_layout.addWidget(self.spin_stretch_tolerance)
        snap_layout.addLayout(stretch_layout)
        self.tools_layout.addWidget(snap_grp_box)
        
        self.tools_layout.addStretch()
        self.tab_tools.setWidget(self.tools_widget)
        self.tabs.addTab(self.tab_tools, "Tools")
        
        # 2. File Data Tab
        self.tab_file = QtWidgets.QScrollArea()
        self.tab_file.setWidgetResizable(True)
        self.tab_file.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.file_scroll_widget = QtWidgets.QWidget()
        self.file_scroll_layout = QtWidgets.QVBoxLayout(self.file_scroll_widget)
        
        self.file_group = QtWidgets.QGroupBox("Schema Data")
        self.file_layout = QtWidgets.QVBoxLayout(self.file_group)
        self.file_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        self.file_scroll_layout.addWidget(self.file_group)
        self.file_scroll_layout.addStretch()
        self.tab_file.setWidget(self.file_scroll_widget)
        self.tabs.addTab(self.tab_file, "File Data")
        
        # 3. Range Data Tab
        self.tab_data = QtWidgets.QScrollArea()
        self.tab_data.setWidgetResizable(True)
        self.tab_data.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.data_widget = QtWidgets.QWidget()
        self.data_layout = QtWidgets.QVBoxLayout(self.data_widget)
        
        base_group = QtWidgets.QGroupBox("Base Data")
        base_layout = QtWidgets.QVBoxLayout(base_group)
        
        # SINGLE ROW for Base Data
        base_row = QtWidgets.QHBoxLayout()
        base_row.addWidget(QtWidgets.QLabel("Name:"))
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Action A (Leave empty for auto)")
        self.name_edit.textChanged.connect(self.on_base_range_data_changed)
        base_row.addWidget(self.name_edit)
        
        base_row.addWidget(QtWidgets.QLabel("Start:"))
        self.start_edit = QtWidgets.QSpinBox(); self.start_edit.setRange(-10000, 10000)
        self.start_edit.valueChanged.connect(self.on_base_range_data_changed)
        base_row.addWidget(self.start_edit)
        
        base_row.addWidget(QtWidgets.QLabel("End:"))
        self.end_edit = QtWidgets.QSpinBox(); self.end_edit.setRange(-10000, 10000)
        self.end_edit.valueChanged.connect(self.on_base_range_data_changed)
        base_row.addWidget(self.end_edit)
        
        self.color_btn = QtWidgets.QPushButton("Color")
        self.color_btn.clicked.connect(self.pick_color)
        base_row.addWidget(self.color_btn)
        
        self.lock_btn = QtWidgets.QPushButton("Lock"); self.lock_btn.setCheckable(True); self.lock_btn.clicked.connect(self.toggle_lock_active_range)
        base_row.addWidget(self.lock_btn)
        
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_active_range)
        base_row.addWidget(self.delete_btn)
        
        base_layout.addLayout(base_row)
        self.data_layout.addWidget(base_group)
        
        self.dynamic_range_container = QtWidgets.QGroupBox("Schema Data")
        self.dynamic_range_layout = QtWidgets.QVBoxLayout(self.dynamic_range_container)
        self.dynamic_range_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.data_layout.addWidget(self.dynamic_range_container)
        
        self.data_layout.addStretch()
        self.tab_data.setWidget(self.data_widget)
        self.tab_data.setEnabled(False)
        self.tabs.addTab(self.tab_data, "Range Data")
        
        # 4. Automations Tab
        self.tab_auto = QtWidgets.QScrollArea()
        self.tab_auto.setWidgetResizable(True)
        self.tab_auto.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.auto_scroll_widget = QtWidgets.QWidget()
        self.auto_btn_layout = QtWidgets.QVBoxLayout(self.auto_scroll_widget)
        self.auto_btn_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.tab_auto.setWidget(self.auto_scroll_widget)
        self.tabs.addTab(self.tab_auto, "Automations")
        
        # 5. Preferences Tab
        self.tab_prefs = QtWidgets.QScrollArea()
        self.tab_prefs.setWidgetResizable(True)
        self.tab_prefs.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.prefs_widget = QtWidgets.QWidget()
        self.pref_layout = QtWidgets.QVBoxLayout(self.prefs_widget)
        
        path_group = QtWidgets.QGroupBox("Paths")
        path_layout = QtWidgets.QVBoxLayout(path_group)
        schema_row = QtWidgets.QHBoxLayout()
        schema_row.addWidget(QtWidgets.QLabel("Schema File:"))
        self.schema_path_fld = QtWidgets.QLineEdit()
        self.schema_path_fld.setText(
            os.path.join(os.path.dirname(__file__), "samples", "schema.json")
        )
        self.schema_path_fld.textChanged.connect(lambda: self.check_schema_path(rebuild=True))
        schema_row.addWidget(self.schema_path_fld)
        
        self.btn_add_schema = QtWidgets.QPushButton("Create")
        self.btn_add_schema.clicked.connect(self.create_example_schema)
        schema_row.addWidget(self.btn_add_schema)
        self.btn_load_schema = QtWidgets.QPushButton("Browse")
        self.btn_load_schema.clicked.connect(self.browse_schema)
        schema_row.addWidget(self.btn_load_schema)
        path_layout.addLayout(schema_row)
        
        auto_row = QtWidgets.QHBoxLayout()
        auto_row.addWidget(QtWidgets.QLabel("Automations:"))
        self.auto_path_fld = QtWidgets.QLineEdit()
        self.auto_path_fld.setText(
            os.path.join(os.path.dirname(__file__), "samples")
        )
        self.auto_path_fld.textChanged.connect(self.build_automations_ui)
        auto_row.addWidget(self.auto_path_fld)
        
        self.btn_add_auto = QtWidgets.QPushButton("Create")
        self.btn_add_auto.clicked.connect(self.create_example_automation)
        auto_row.addWidget(self.btn_add_auto)
        self.btn_load_auto = QtWidgets.QPushButton("Browse")
        self.btn_load_auto.clicked.connect(self.browse_automations_folder)
        auto_row.addWidget(self.btn_load_auto)
        path_layout.addLayout(auto_row)
        self.pref_layout.addWidget(path_group)
        
        display_group = QtWidgets.QGroupBox("Timeline Display")
        display_layout = QtWidgets.QVBoxLayout(display_group)
        self.chk_frames = QtWidgets.QCheckBox("Show Corner Frames")
        self.chk_frames.setChecked(self.timeline.pref_show_frames)
        self.chk_frames.setToolTip("Displays the start and end frame numbers\nin the bottom corners of each range.")
        self.chk_names = QtWidgets.QCheckBox("Show Range Names")
        self.chk_names.setChecked(self.timeline.pref_show_names)
        self.chk_names.setToolTip("Displays the custom name of the range\nin the center of the block.")
        display_layout.addWidget(self.chk_frames)
        display_layout.addWidget(self.chk_names)
        self.pref_layout.addWidget(display_group)
        
        colors_group = QtWidgets.QGroupBox("Colors")
        colors_layout = QtWidgets.QVBoxLayout(colors_group)
        self.chk_colors = QtWidgets.QCheckBox("Randomize Colors")
        self.chk_colors.setChecked(self.timeline.pref_random_colors)
        self.chk_colors.setToolTip("Assigns a random color when drawing\na new frame range.")
        self.chk_razor_colors = QtWidgets.QCheckBox("Randomize Razor Slices")
        self.chk_razor_colors.setChecked(self.timeline.pref_razor_random_colors)
        self.chk_razor_colors.setToolTip("Assigns new random colors to the two halves\nwhen using the Razor tool to slice a range.")
        colors_layout.addWidget(self.chk_colors)
        colors_layout.addWidget(self.chk_razor_colors)
        self.pref_layout.addWidget(colors_group)
        
        behaviors_group = QtWidgets.QGroupBox("Behaviors")
        behaviors_layout = QtWidgets.QVBoxLayout(behaviors_group)
        self.chk_sync = QtWidgets.QCheckBox("Sync Maya Time")
        self.chk_sync.setChecked(self.timeline.pref_sync_time)
        self.chk_sync.setToolTip("Synchronizes the tool's playhead and timeline\nwith Maya's active current time.")
        self.chk_bounds = QtWidgets.QCheckBox("Limit Timeline Bounds")
        self.chk_bounds.setChecked(self.timeline.pref_limit_bounds)
        self.chk_bounds.setToolTip("Prevents ranges from being moved or resized\nbeyond the start and end of the timeline.")
        self.chk_run_all_auto = QtWidgets.QCheckBox("Show 'Run All' Automations Button")
        self.chk_run_all_auto.setChecked(True)
        self.chk_val_status = QtWidgets.QCheckBox("Show Validation Status")
        self.chk_val_status.setChecked(True)
        self.chk_val_status.setToolTip("Displays the real-time validation status bar\nat the bottom of the tool.")
        behaviors_layout.addWidget(self.chk_sync)
        behaviors_layout.addWidget(self.chk_bounds)
        behaviors_layout.addWidget(self.chk_run_all_auto)
        behaviors_layout.addWidget(self.chk_val_status)
        self.pref_layout.addWidget(behaviors_group)
        
        for cb in [self.chk_frames, self.chk_names, self.chk_colors, self.chk_sync, self.chk_bounds, self.chk_razor_colors, self.chk_val_status]:
            cb.stateChanged.connect(self.on_pref_changed)
        self.chk_run_all_auto.stateChanged.connect(lambda: self.build_automations_ui())
        
        data_mng_group = QtWidgets.QGroupBox("Data Management")
        data_mng_layout = QtWidgets.QHBoxLayout(data_mng_group)
        self.chk_write_node = QtWidgets.QCheckBox("Write Data to Scene Node (rangeTimelineData)")
        self.chk_write_node.setChecked(True)
        self.chk_write_node.stateChanged.connect(self.on_write_node_changed)
        data_mng_layout.addWidget(self.chk_write_node)
        data_mng_layout.addStretch()
        
        btn_del_node = QtWidgets.QPushButton("Delete Node")
        btn_del_node.setStyleSheet("background-color: #c94c4c; color: white;")
        btn_del_node.clicked.connect(self.delete_scene_node)
        data_mng_layout.addWidget(btn_del_node)
        self.btn_select_node = QtWidgets.QPushButton()
        self.btn_select_node.setToolTip("Select scene data node")
        self.btn_select_node.clicked.connect(self.select_scene_node)
        data_mng_layout.addWidget(self.btn_select_node)

        btn_import = QtWidgets.QPushButton("Import JSON")
        btn_import.clicked.connect(self.import_data)
        data_mng_layout.addWidget(btn_import)
        
        btn_export = QtWidgets.QPushButton("Export JSON")
        btn_export.clicked.connect(self.export_data)
        data_mng_layout.addWidget(btn_export)
        
        self.pref_layout.addWidget(data_mng_group)
            
        self.pref_layout.addStretch()
        self.tab_prefs.setWidget(self.prefs_widget)
        self.tabs.addTab(self.tab_prefs, "Preferences")
        
        # --- STATUS BAR ---
        self.status_bar = QtWidgets.QLabel("Ready")
        self.status_bar.setWordWrap(True)
        self.status_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter) 
        self.status_bar.setStyleSheet("padding: 4px; background-color: #2b2b2b; color: #999999; border-top: 1px solid #111;")
        main_layout.addWidget(self.status_bar)

        # --- INITIALIZATION SEQUENCE ---
        self.setup_scriptjob()
        self.check_schema_path(rebuild=False)
        self.handle_data_load(loaded_ranges, loaded_file_data)
        self.build_automations_ui()
        self.refresh_from_maya()

    # --- SAVE / EXPORT / IMPORT LOGIC ---
    def select_scene_node(self):
        """Selects the tracker data node in the current Maya scene."""
        node_name = DataManager.NODE_NAME
        if not cmds.objExists(node_name):
            QtWidgets.QMessageBox.warning(
                self,
                "Select Node",
                f"Node '{node_name}' not found in scene.",
            )
            return
        cmds.select(node_name, replace=True)
        self.status_bar.setText(f"Selected scene data node: {node_name}")

    def delete_scene_node(self):
        """Deletes the tracker data node from the current Maya scene."""
        node_name = DataManager.NODE_NAME
        if not cmds.objExists(node_name):
            QtWidgets.QMessageBox.warning(self, "Delete Node", f"Node '{node_name}' not found in the scene.")
            return
            
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle("Confirm Deletion")
        msgBox.setText(f"Are you sure you want to delete the '{node_name}' node?\nAll saved timeline data in this scene will be lost.")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        
        if msgBox.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            cmds.delete(node_name)
            self.chk_write_node.setChecked(False) # Turn off writing so it doesn't instantly recreate
            QtWidgets.QMessageBox.information(self, "Node Deleted", f"Successfully deleted '{node_name}'.\n\n'Write Data to Scene Node' has been disabled in Preferences to prevent accidental recreation.")

    def save_to_scene(self):
        """Persists the current tracker ranges and metadata to the scene."""
        if getattr(self, '_is_building_ui', False): return
        payload = DataManager.build_payload(self.timeline.ranges, self.file_data)
        if not self._suspend_last_used_data and not self._is_loading_data:
            self.model.set_last_used_data(payload)
        if not self.chk_write_node.isChecked(): return
        DataManager.save_data(self.timeline.ranges, self.file_data)
        
    def on_write_node_changed(self, state):
        """Updates whether tracker changes are written to the scene.

        Args:
            state (int): Qt checkbox state.
        """
        if self.chk_write_node.isChecked():
            self.save_to_scene()

    def on_ranges_changed(self):
        """Refreshes tracker state after the timeline ranges change."""
        self.highlight_validation()
        self.save_to_scene()

    def export_data(self):
        """Exports tracker data to a user-selected JSON file."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export JSON", "timeline_data.json", "JSON Files (*.json)")
        if path:
            payload = DataManager.build_payload(self.timeline.ranges, self.file_data)
            try:
                with open(path, 'w') as f: json.dump(payload, f, indent=2)
                cmds.warning(f"Data exported successfully to {path}")
            except Exception as e:
                cmds.warning(f"Export failed: {e}")
                
    def import_data(self):
        """Imports tracker ranges and metadata from a JSON file."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import JSON", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r') as f: payload = json.load(f)
                ranges = []
                for d in payload.get("ranges", []):
                    c = d.get("color", [128, 128, 128])
                    r = RangeItem(d.get("name", ""), d.get("start", 0), d.get("end", 1), tuple(c))
                    r.id = d.get("id", str(uuid.uuid4()))
                    r.locked = d.get("locked", False)
                    r.custom_data = d.get("custom_data", {})
                    ranges.append(r)
                file_data = payload.get("file_data", {})
                self.handle_data_load(ranges, file_data)
            except Exception as e:
                cmds.warning(f"Import failed: {e}")

    # --- DATA SCHEMA CHECKER ---
    def handle_data_load(self, loaded_ranges, loaded_file_data):
        """Applies loaded data after validating its schema.

        Args:
            loaded_ranges (list): Ranges read from the input data.
            loaded_file_data (dict): File metadata read from the input data.
        """
        previous_loading = self._is_loading_data
        self._is_loading_data = True
        while True:
            if not self.check_schema_mismatch(loaded_ranges, loaded_file_data):
                break
                
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle("Schema Mismatch")
            msgBox.setText("The imported/scene data does not match the currently loaded schema.\n\nFields might be missing or lost if you proceed.")
            btn_browse = msgBox.addButton("Pick Another Schema", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            btn_ignore = msgBox.addButton("Ignore (Risk Data Loss)", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            btn_disable = msgBox.addButton("Disable Scene Writing", QtWidgets.QMessageBox.ButtonRole.ActionRole)
            
            msgBox.exec()
            
            if msgBox.clickedButton() == btn_browse:
                path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load JSON Schema", "", "JSON Files (*.json)")
                if path:
                    self.schema_path_fld.setText(path)
                    self.check_schema_path(rebuild=False) 
                continue 
                
            elif msgBox.clickedButton() == btn_disable:
                self.chk_write_node.setChecked(False)
                break
            else: 
                break
                
        self.timeline.ranges = loaded_ranges
        self.scene_file_data_cache = loaded_file_data
        self.rebuild_schema_ui()
        self.timeline.rangesChanged.emit()
        self._is_loading_data = previous_loading
        
    def check_schema_mismatch(self, loaded_ranges, loaded_file_data):
        """Checks imported data against the active schema definition.

        Args:
            loaded_ranges (list): Imported range data.
            loaded_file_data (dict): Imported file metadata.

        Returns:
            list: Schema fields that do not match the active definition.
        """
        if not loaded_file_data and not loaded_ranges:
            return False 
            
        schema_file_keys = {item['name'] for item in self._flatten_schema(self.schema.get("file_level", []))}
        schema_range_keys = {item['name'] for item in self._flatten_schema(self.schema.get("frame_range", []))}
        
        if loaded_file_data:
            if set(loaded_file_data.keys()) != schema_file_keys:
                return True
                
        for r in loaded_ranges:
            if set(r.custom_data.keys()) != schema_range_keys:
                return True
                
        return False

    # --- ADD BUTTONS LOGIC ---
    def create_example_schema(self):
        """Creates an example schema file for the tracker tool."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Example Schema", "schema.json", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'w') as f: f.write(EXAMPLE_SCHEMA)
                self.schema_path_fld.setText(path)
                cmds.warning(f"Created example schema at {path}")
            except Exception as e:
                cmds.warning(f"Failed to save schema: {e}")
                
    def create_example_automation(self):
        """Creates an example automation script in the configured folder."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Example Automation Script", "automation.py", "Python Files (*.py)")
        if path:
            try:
                with open(path, 'w') as f: f.write(EXAMPLE_SCRIPT)
                folder = os.path.dirname(path)
                self.auto_path_fld.setText(folder)
                self.build_automations_ui()
                cmds.warning(f"Created example automation at {path}")
            except Exception as e:
                cmds.warning(f"Failed to save script: {e}")

    # --- DYNAMIC SCHEMA & UI LOGIC ---
    def check_schema_path(self, rebuild=True):
        """Validates the configured schema path and optionally rebuilds the UI.

        Args:
            rebuild (bool): Whether to rebuild schema controls after validation.
        """
        path = self.schema_path_fld.text().strip(' "\'')
        if not path or not os.path.exists(path):
            self.schema = {}
            if rebuild: self.rebuild_schema_ui()
        else:
            try:
                with open(path, 'r') as f: self.schema = json.load(f)
                if rebuild: self.rebuild_schema_ui()
                print("Schema loaded successfully.") 
            except Exception as e:
                print(f"Failed to load schema: {e}")
                self.schema = {}
                if rebuild: self.rebuild_schema_ui()

    def browse_schema(self):
        """Opens a file dialog for selecting a tracker schema."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load JSON Schema", "", "JSON Files (*.json)")
        if path: self.schema_path_fld.setText(path)
        
    def browse_automations_folder(self):
        """Opens a file dialog for selecting the automations folder."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Automations Folder")
        if folder: self.auto_path_fld.setText(folder)

    def rebuild_schema_ui(self):
        """Rebuilds dynamic tracker controls from the active schema."""
        self._is_building_ui = True
        self.file_data = {}
        self.clear_layout(self.file_layout)
        self.ui_widgets_file.clear()
        
        if not self.schema:
            self.file_layout.addWidget(QtWidgets.QLabel("No schema loaded or path is empty."))
        else:
            self.build_dynamic_ui(self.schema.get("file_level", []), self.file_layout, self.ui_widgets_file, self.on_file_data_changed)
        
        self.clear_layout(self.dynamic_range_layout)
        self.ui_widgets_range.clear()
        
        if not self.schema:
            self.dynamic_range_layout.addWidget(QtWidgets.QLabel("No schema loaded or path is empty."))
        else:
            self.build_dynamic_ui(self.schema.get("frame_range", []), self.dynamic_range_layout, self.ui_widgets_range, self.on_dynamic_range_data_changed)
        
        default_values = {
            item.get("name"): item.get("default")
            for item in self._flatten_schema(self.schema.get("file_level", []))
            if item.get("name") and "default" in item
        }
        for name, widget in self.ui_widgets_file.items():
            widget.blockSignals(True)
            val = self.scene_file_data_cache.get(name)
            if val in (None, ""):
                val = default_values.get(name, val)
            if val is not None:
                if isinstance(widget, QtWidgets.QComboBox): widget.setCurrentText(str(val))
                elif isinstance(widget, QtWidgets.QLineEdit): widget.setText(str(val))
                elif isinstance(widget, QtWidgets.QCheckBox): widget.setChecked(bool(val))
            widget.blockSignals(False)

        self._is_building_ui = False
        previous_suspend = self._suspend_last_used_data
        self._suspend_last_used_data = True
        try:
            self.on_file_data_changed()
        finally:
            self._suspend_last_used_data = previous_suspend
        
        self.populate_edit_area(self.timeline.active_range)
        self.highlight_validation()

    def clear_layout(self, layout):
        """Removes and deletes all widgets from a Qt layout.

        Args:
            layout (QLayout): Layout whose child items should be removed.
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clear_layout(item.layout())
                    item.layout().deleteLater()

    def build_dynamic_ui(self, schema_items, parent_layout, widget_registry, callback):
        """Builds schema-driven controls and registers their widgets.

        Args:
            schema_items (list): Schema field definitions to display.
            parent_layout (QLayout): Layout receiving the generated controls.
            widget_registry (dict): Mapping populated with generated widgets.
            callback (callable): Change callback connected to generated widgets.
        """
        for item in schema_items:
            itype = item.get("type")
            if itype == "separator":
                line = QtWidgets.QFrame(); line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                parent_layout.addWidget(line)
            elif itype == "row":
                row_layout = QtWidgets.QHBoxLayout()
                self.build_dynamic_ui(item.get("items", []), row_layout, widget_registry, callback)
                parent_layout.addLayout(row_layout)
            else:
                field_layout = QtWidgets.QHBoxLayout() 
                v_layout = QtWidgets.QVBoxLayout() 
                
                req = item.get("required", False)
                lbl_text = item.get("label", item.get("name", ""))
                if req: lbl_text += " *"
                lbl = QtWidgets.QLabel(lbl_text)
                
                desc = item.get("description", "")
                if desc: lbl.setToolTip(desc.replace(". ", ".\n"))
                v_layout.addWidget(lbl)
                
                name = item.get("name")
                widget = None
                
                if itype == "enum":
                    widget = QtWidgets.QComboBox()
                    widget.addItem("---")
                    widget.addItems(item.get("options", []))
                    default_value = item.get("default")
                    if default_value is not None:
                        widget.setCurrentText(str(default_value))
                    widget.currentIndexChanged.connect(callback)
                elif itype == "string":
                    widget = QtWidgets.QLineEdit()
                    custom_placeholder = item.get("placeholder", "")
                    if custom_placeholder:
                        p_text = f"({'Required' if req else 'Optional'}) {custom_placeholder}"
                    else:
                        p_text = f"({'Required' if req else 'Optional'}) {desc}"
                    widget.setPlaceholderText(p_text)
                    widget.textChanged.connect(callback)
                elif itype == "boolean":
                    widget = QtWidgets.QCheckBox()
                    widget.stateChanged.connect(callback)
                    
                if widget:
                    widget_registry[name] = widget
                    v_layout.addWidget(widget)
                    field_layout.addLayout(v_layout)
                    
                    auto_script = item.get("automation")
                    if auto_script:
                        btn = QtWidgets.QPushButton("Auto")
                        btn.setToolTip(f"Runs:\n{auto_script}")
                        btn.clicked.connect(lambda checked=False, s=auto_script, f=name, w=widget: self.execute_automation(s, f, w))
                        field_layout.addWidget(btn, alignment=QtCore.Qt.AlignmentFlag.AlignBottom)
                        
                parent_layout.addLayout(field_layout)

    # --- AUTOMATIONS LOGIC ---
    def build_automations_ui(self):
        """Builds the automation controls for the current schema."""
        self.clear_layout(self.auto_btn_layout)
        folder = self.auto_path_fld.text().strip(' "\'')
        
        if not folder or not os.path.exists(folder):
            self.auto_btn_layout.addWidget(QtWidgets.QLabel("Automations folder not found or path is empty."))
            return
            
        py_files = glob.glob(os.path.join(folder, "*.py"))
        info_lbl = QtWidgets.QLabel(f"<b>Found {len(py_files)} automation scripts</b><br><span style='color:gray'>{folder}</span><br>")
        info_lbl.setWordWrap(True)
        self.auto_btn_layout.addWidget(info_lbl)
        
        if not py_files: return
        
        if self.chk_run_all_auto.isChecked():
            btn_run_all = QtWidgets.QPushButton("Run All")
            btn_run_all.setStyleSheet("background-color: #b0b0b0; color: black; font-weight: bold; padding: 4px;")
            btn_run_all.clicked.connect(self.run_all_automations)
            self.auto_btn_layout.addWidget(btn_run_all)
            
            line = QtWidgets.QFrame(); line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            self.auto_btn_layout.addWidget(line)
            
        for i, fpath in enumerate(py_files, 1):
            row = QtWidgets.QHBoxLayout()
            fname = os.path.basename(fpath)
            
            num_lbl = QtWidgets.QLabel(f"{i}.")
            num_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            num_lbl.setFixedWidth(24)
            row.addWidget(num_lbl)
            
            btn = QtWidgets.QPushButton(fname)
            btn.clicked.connect(lambda checked=False, p=fpath: self.execute_automation_by_path(p))
            row.addWidget(btn)
            
            edit_btn = QtWidgets.QPushButton("Edit")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda checked=False, p=fpath: self.open_file_in_editor(p))
            row.addWidget(edit_btn)
            
            self.auto_btn_layout.addLayout(row)

    def run_all_automations(self):
        """Runs every automation configured for the current tracker."""
        folder = self.auto_path_fld.text().strip(' "\'')
        py_files = glob.glob(os.path.join(folder, "*.py"))
        for fpath in py_files:
            self.execute_automation_by_path(fpath)

    def open_file_in_editor(self, filepath):
        """Opens an automation file in the configured system editor.

        Args:
            filepath (str): Path to the file to open.
        """
        try:
            if sys.platform.startswith('win'): os.startfile(filepath)
            elif sys.platform.startswith('darwin'): subprocess.call(('open', filepath))
            else: subprocess.call(('xdg-open', filepath))
        except Exception as e:
            cmds.warning(f"Could not open file: {e}")

    def execute_automation_by_path(self, script_path):
        """Executes an automation script using its explicit path.

        Args:
            script_path (str): Path to the automation script.
        """
        self._run_script(script_path, self._get_automation_context())

    def execute_automation(self, script_name, field_name, widget):
        """Executes a named automation and exposes its target field widget.

        Args:
            script_name (str): Automation script file name.
            field_name (str): Schema field associated with the automation.
            widget (QWidget): Widget that initiated the automation.
        """
        folder = self.auto_path_fld.text().strip(' "\'')
        script_path = os.path.join(folder, script_name)
        if not os.path.exists(script_path):
            cmds.warning(f"Automation script not found: {script_path}")
            return
            
        ctx = self._get_automation_context()
        
        def set_value(val):
            """Updates the field value through the automation context.

            Args:
                val (object): Value supplied by the automation script.
            """
            if widget in self.ui_widgets_range.values():
                ctx["update_range_data"](field_name, val)
            else:
                ctx["update_file_data"](field_name, val)
                
        ctx["set_value"] = set_value
        ctx["field_name"] = field_name
        
        self._run_script(script_path, ctx)
        
    def _get_automation_context(self):
        """Builds the helper context exposed to automation scripts.

        Returns:
            dict: Automation helper functions and current tracker values.
        """
        def update_range_data(field_name, val):
            """Updates a custom field on the active range.

            Args:
                field_name (str): Name of the range field to update.
                val (object): New field value.
            """
            if not self.timeline.active_range:
                cmds.warning("No range selected. Please select a range first.")
                return
            self.timeline.active_range.custom_data[field_name] = str(val)
            w = self.ui_widgets_range.get(field_name)
            if w:
                w.blockSignals(True)
                if isinstance(w, QtWidgets.QLineEdit): w.setText(str(val))
                elif isinstance(w, QtWidgets.QComboBox): w.setCurrentText(str(val))
                elif isinstance(w, QtWidgets.QCheckBox): w.setChecked(bool(val))
                w.blockSignals(False)
            self.highlight_validation()
            self.save_to_scene()

        def update_file_data(field_name, val):
            """Updates a file-level tracker field and its widget.

            Args:
                field_name (str): Name of the file field to update.
                val (object): New field value.
            """
            self.file_data[field_name] = str(val)
            w = self.ui_widgets_file.get(field_name)
            if w:
                w.blockSignals(True)
                if isinstance(w, QtWidgets.QLineEdit): w.setText(str(val))
                elif isinstance(w, QtWidgets.QComboBox): w.setCurrentText(str(val))
                elif isinstance(w, QtWidgets.QCheckBox): w.setChecked(bool(val))
                w.blockSignals(False)
            self.highlight_validation()
            self.save_to_scene()

        def get_file_data(field_name):
            """Reads a file-level tracker field.

            Args:
                field_name (str): Name of the field to read.

            Returns:
                object: Stored field value, or the default fallback.
            """
            return self.file_data.get(field_name, "")
            
        def create_range(name, start, end, color=None):
            """Creates and activates a new timeline range.

            Args:
                name (str): Name for the new range.
                start (float): Start frame.
                end (float): End frame.
                color (tuple, optional): RGB display color.
            """
            c = color if color else (100, 100, 100)
            nr = RangeItem(name, start, end, c)
            self.timeline.ranges.append(nr)
            self.timeline.active_range = nr 
            self.timeline.rangesChanged.emit()
            return nr

        def get_last_used_data():
            """Gets a copy of the last tracker data stored in tool preferences.

            Returns:
                dict: Previously saved range and file metadata.
            """
            return self.model.get_last_used_data()

        def refresh_ui():
            """Refreshes the timeline and dynamic editor controls."""
            self.timeline.update()
            if self.timeline.active_range:
                self.populate_edit_area(self.timeline.active_range)
            self.highlight_validation()

        return {
            "cmds": cmds,
            "active_range": self.timeline.active_range,
            "timeline_ranges": self.timeline.ranges,
            "update_range_data": update_range_data,
            "update_file_data": update_file_data,
            "get_file_data": get_file_data,
            "get_last_used_data": get_last_used_data,
            "create_range": create_range,
            "refresh_ui": refresh_ui
        }

    def _run_script(self, script_path, ctx):
        """Reads and executes an automation script in its supplied context.

        Args:
            script_path (str): Path to the automation script.
            ctx (dict): Globals and helper values exposed to the script.
        """
        try:
            with open(script_path, 'r') as f: code = f.read()
            globals_dict = {"context": ctx}
            exec(code, globals_dict)
        except Exception as e:
            cmds.warning(f"Error executing {os.path.basename(script_path)}: {e}")

    # --- VALIDATION LOGIC ---
    def on_file_data_changed(self, *args):
        """Stores values changed in file-level schema widgets."""
        for name, widget in self.ui_widgets_file.items():
            if isinstance(widget, QtWidgets.QComboBox):
                val = widget.currentText()
                self.file_data[name] = "" if val == "---" else val
            elif isinstance(widget, QtWidgets.QLineEdit): self.file_data[name] = widget.text()
            elif isinstance(widget, QtWidgets.QCheckBox): self.file_data[name] = widget.isChecked()
        self.highlight_validation()
        self.save_to_scene()

    def on_dynamic_range_data_changed(self, *args):
        """Stores values changed in active-range schema widgets."""
        if not self.timeline.active_range: return
        data = self.timeline.active_range.custom_data
        for name, widget in self.ui_widgets_range.items():
            if isinstance(widget, QtWidgets.QComboBox):
                val = widget.currentText()
                data[name] = "" if val == "---" else val
            elif isinstance(widget, QtWidgets.QLineEdit): data[name] = widget.text()
            elif isinstance(widget, QtWidgets.QCheckBox): data[name] = widget.isChecked()
        self.highlight_validation()
        self.save_to_scene()

    def highlight_validation(self):
        """Highlights schema controls whose values fail validation."""
        if not self.chk_val_status.isChecked():
            self.status_bar.setVisible(False)
            return
        
        self.status_bar.setVisible(True)
        if not self.schema:
            self.status_bar.setText("No schema loaded.")
            self.status_bar.setStyleSheet("padding: 4px; background-color: #2b2b2b; color: #999999;")
            return
            
        invalid_style = "border: 1px solid #ff4444;"
        errors = []
        val_rules = self.schema.get("validation", {})
        
        # 1. Overlap Check
        if not val_rules.get("allow_overlap", True):
            sorted_r = sorted(self.timeline.ranges, key=lambda x: x.start)
            for i in range(len(sorted_r) - 1):
                if sorted_r[i].end > sorted_r[i+1].start:
                    errors.append(f"Overlap detected between '{sorted_r[i].display_name}' and '{sorted_r[i+1].display_name}'")

        # 2. Coverage Check
        if val_rules.get("full_coverage", False):
            covered = set()
            for r in self.timeline.ranges: 
                covered.update(range(r.start, r.end + 1))
            
            expected = set(range(self.timeline.start_frame, self.timeline.end_frame + 1))
            missing = expected - covered
            if missing: 
                errors.append(f"Timeline is not fully covered (Missing {len(missing)} frames)")
        
        # 3. File Level Check
        for item in self._flatten_schema(self.schema.get("file_level", [])):
            w = self.ui_widgets_file.get(item["name"])
            val = self.file_data.get(item["name"])
            if item.get("required"):
                if val is None or val == "": 
                    if w: w.setStyleSheet(invalid_style)
                    errors.append(f"File Data: Missing '{item.get('label')}'")
                else: 
                    if w: w.setStyleSheet("")
                    
        # 4. Range Level Check
        req_range = [i for i in self._flatten_schema(self.schema.get("frame_range", [])) if i.get("required")]
        active_r = self.timeline.active_range
        
        for r in self.timeline.ranges:
            for item in req_range:
                val = r.custom_data.get(item["name"])
                if val is None or val == "":
                    errors.append(f"Range '{r.display_name}': Missing '{item.get('label')}'")
                    
        for item in req_range:
            w = self.ui_widgets_range.get(item["name"])
            if w:
                if active_r:
                    val = active_r.custom_data.get(item["name"])
                    if val is None or val == "": w.setStyleSheet(invalid_style)
                    else: w.setStyleSheet("")
                else: w.setStyleSheet("") 

        if errors:
            err_text = f"Validation Error: {errors[0]}"
            if len(errors) > 1: err_text += f" (+{len(errors)-1} more)"
            self.status_bar.setText(err_text)
            self.status_bar.setStyleSheet("padding: 4px; background-color: #2b2b2b; color: #ff6666; font-weight: bold; border-top: 1px solid #111;")
        else:
            self.status_bar.setText("Validation Passed!")
            self.status_bar.setStyleSheet("padding: 4px; background-color: #2b2b2b; color: #66ff66; border-top: 1px solid #111;")

    def _flatten_schema(self, schema_items):
        """Flattens nested schema fields into a linear field collection.

        Args:
            schema_items (list): Nested schema field definitions.

        Returns:
            list: Flattened schema fields.
        """
        res = []
        for item in schema_items:
            if item.get("type") == "row": res.extend(self._flatten_schema(item.get("items", [])))
            elif item.get("type") not in ("separator", "row"): res.append(item)
        return res

    # --- STANDARD APP LOGIC ---
    def setup_scriptjob(self):
        """Creates the Maya time-change job used to refresh the tracker."""
        self.teardown_scriptjob()
        self.sj_id = cmds.scriptJob(e=["timeChanged", self.on_maya_time_changed], protected=True)

    def teardown_scriptjob(self):
        """Removes the Maya time-change job when the window is closed."""
        script_job_id = getattr(self, "sj_id", None)
        if script_job_id:
            try:
                if cmds.scriptJob(exists=script_job_id):
                    cmds.scriptJob(kill=script_job_id, force=True)
            except RuntimeError:
                pass
        self.sj_id = None

    def runtime_widgets_alive(self):
        """Checks whether the controls used by Maya callbacks still exist.

        Returns:
            bool: True when the tracker controls can receive updates.
        """
        widgets = [
            self,
            getattr(self, "start_fld", None),
            getattr(self, "current_fld", None),
            getattr(self, "end_fld", None),
            getattr(self, "timeline", None),
        ]
        return all(ui_qt_utils.is_qt_object_valid(widget) for widget in widgets)

    def closeEvent(self, event):
        """Cleans up tracker resources before closing the window.

        Args:
            event (QCloseEvent): Qt close event.
        """
        self.teardown_scriptjob()
        super(RangeToolWindow, self).closeEvent(event)
    def changeEvent(self, event):
        """Handles Qt window state changes that require UI refreshes.

        Args:
            event (QEvent): Qt change event.
        """
        if event.type() == QtCore.QEvent.Type.ActivationChange and self.isActiveWindow():
            self.refresh_from_maya()
        super(RangeToolWindow, self).changeEvent(event)

    def on_maya_time_changed(self):
        """Updates the timeline position after Maya's current time changes."""
        if not self.runtime_widgets_alive():
            self.teardown_scriptjob()
            return
        try:
            if self.timeline.pref_sync_time and not self.timeline.interaction_state:
                current = int(cmds.currentTime(q=True))
                self.sync_current_field(current)
                self.timeline.current_frame = current
                self.timeline.update()
        except RuntimeError:
            self.teardown_scriptjob()

    def refresh_from_maya(self):
        """Refreshes tracker display values from the current Maya scene."""
        if not self.runtime_widgets_alive():
            return
        s = int(cmds.playbackOptions(q=True, min=True))
        e = int(cmds.playbackOptions(q=True, max=True))
        c = int(cmds.currentTime(q=True))
        self.start_fld.setText(str(s))
        self.end_fld.setText(str(e))
        self.sync_current_field(c)
        self.timeline.start_frame, self.timeline.end_frame, self.timeline.current_frame = s, e, c
        self.timeline.update()
        self.highlight_validation()

    def sync_current_field(self, frame):
        """Synchronizes the current-frame field with a timeline frame.

        Args:
            frame (float): Current timeline frame.
        """
        current_field = getattr(self, "current_fld", None)
        if not ui_qt_utils.is_qt_object_valid(current_field):
            self.teardown_scriptjob()
            return
        try:
            current_field.blockSignals(True)
            current_field.setValue(int(frame))
            current_field.blockSignals(False)
        except RuntimeError:
            self.teardown_scriptjob()

    def on_current_field_changed(self, val):
        """Moves Maya's current time when the current field changes.

        Args:
            val (object): New current-frame field value.
        """
        if not self.runtime_widgets_alive():
            return
        cmds.currentTime(val)
        self.timeline.current_frame = val
        self.timeline.update()

    def on_tool_mode_changed(self, _=None):
        """Updates timeline behavior after the tool mode changes.

        Args:
            _ (object): Unused Qt signal value.
        """
        if self.rad_nav.isChecked(): 
            self.timeline.tool_mode = 'navigate'
            if self.timeline.active_range:
                self.timeline.active_range = None
                self.populate_edit_area(None)
        elif self.rad_sel.isChecked(): self.timeline.tool_mode = 'select'
        elif self.rad_edit.isChecked(): self.timeline.tool_mode = 'edit'
        elif self.rad_raz.isChecked(): self.timeline.tool_mode = 'razor'
        self.timeline.magnet_enabled = self.chk_magnet.isChecked(); self.timeline.update()
        
    def on_magnet_tolerance_changed(self, val):
        """Updates the range snapping tolerance from the preferences UI.

        Args:
            val (object): New tolerance value.
        """
        self.timeline.snap_threshold = val

    def on_auto_snapping_changed(self, *args):
        """Updates automatic adjacent-range snapping preferences."""
        self.timeline.auto_crop_enabled = self.chk_auto_crop.isChecked()
        self.timeline.crop_tolerance = self.spin_crop_tolerance.value()
        self.timeline.auto_stretch_enabled = self.chk_auto_stretch.isChecked()
        self.timeline.stretch_tolerance = self.spin_stretch_tolerance.value()
        self.timeline.adjust_adjacent_ranges()
        self.timeline.update()

    def on_pref_changed(self, state):
        """Stores a changed tracker preference.

        Args:
            state (int): Qt checkbox state.
        """
        self.timeline.pref_show_frames = self.chk_frames.isChecked()
        self.timeline.pref_show_names = self.chk_names.isChecked()
        self.timeline.pref_random_colors = self.chk_colors.isChecked()
        self.timeline.pref_sync_time = self.chk_sync.isChecked()
        self.timeline.pref_limit_bounds = self.chk_bounds.isChecked()
        self.timeline.pref_razor_random_colors = getattr(self, 'chk_razor_colors', QtWidgets.QCheckBox()).isChecked()
        
        self.status_bar.setVisible(self.chk_val_status.isChecked())
        self.highlight_validation()
        self.timeline.update()

    def populate_edit_area(self, r):
        """Populates the edit area with data from a selected range.

        Args:
            r (RangeItem): Range whose data should be displayed.
        """
        if not r:
            self.tab_data.setEnabled(False)
            self.name_edit.setText("")
            for w in self.ui_widgets_range.values():
                w.blockSignals(True)
                if isinstance(w, QtWidgets.QComboBox): w.setCurrentIndex(0)
                elif isinstance(w, QtWidgets.QLineEdit): w.setText("")
                elif isinstance(w, QtWidgets.QCheckBox): w.setChecked(False)
                w.blockSignals(False)
            self.highlight_validation()
            return
            
        self.tab_data.setEnabled(True)
        self.name_edit.blockSignals(True); self.start_edit.blockSignals(True)
        self.end_edit.blockSignals(True); self.lock_btn.blockSignals(True)
        
        self.name_edit.setText(r.name)
        self.start_edit.setValue(r.start); self.end_edit.setValue(r.end)
        self.lock_btn.setChecked(r.locked); self.lock_btn.setText("Unlock" if r.locked else "Lock")
        self.start_edit.setEnabled(not r.locked); self.end_edit.setEnabled(not r.locked)
        self.color_btn.setStyleSheet(f"background-color: #{r.color[0]:02x}{r.color[1]:02x}{r.color[2]:02x}; color: black;")
        
        for name, widget in self.ui_widgets_range.items():
            widget.blockSignals(True)
            val = r.custom_data.get(name)
            if isinstance(widget, QtWidgets.QComboBox):
                if val: widget.setCurrentText(val)
                else: widget.setCurrentIndex(0)
            elif isinstance(widget, QtWidgets.QLineEdit): widget.setText(val if val else "")
            elif isinstance(widget, QtWidgets.QCheckBox): widget.setChecked(bool(val))
            widget.blockSignals(False)
        
        self.name_edit.blockSignals(False); self.start_edit.blockSignals(False)
        self.end_edit.blockSignals(False); self.lock_btn.blockSignals(False)
        self.highlight_validation()

    def on_base_range_data_changed(self, *args):
        """Applies edits made to the selected range's base fields."""
        if not self.timeline.active_range: return
        r = self.timeline.active_range; r.name = self.name_edit.text()
        
        ns, ne = self.start_edit.value(), self.end_edit.value()
        if self.timeline.pref_limit_bounds:
            mb, me = self.timeline.start_frame, self.timeline.end_frame
            ns = max(mb, min(me - 1, ns)); ne = max(ns + 1, min(me, ne))
            if ns != self.start_edit.value() or ne != self.end_edit.value():
                self.start_edit.blockSignals(True); self.start_edit.setValue(ns); self.start_edit.blockSignals(False)
                self.end_edit.blockSignals(True); self.end_edit.setValue(ne); self.end_edit.blockSignals(False)
        elif ns > ne:
            ns = ne; self.start_edit.blockSignals(True); self.start_edit.setValue(ns); self.start_edit.blockSignals(False)
            
        r.start, r.end = ns, ne
        self.timeline.adjust_adjacent_ranges()
        self.timeline.update()
        self.timeline.rangesChanged.emit() 
        
    def toggle_lock_active_range(self):
        """Toggles the lock state of the selected timeline range."""
        if not self.timeline.active_range: return
        self.timeline.active_range.locked = self.lock_btn.isChecked()
        self.populate_edit_area(self.timeline.active_range); self.timeline.update()
        self.save_to_scene()

    def pick_color(self):
        """Opens a color picker and applies the selected range color."""
        if not self.timeline.active_range: return
        col = QtWidgets.QColorDialog.getColor(QtGui.QColor(*self.timeline.active_range.color), self, "Pick Range Color")
        if col.isValid():
            r, g, b, _ = col.getRgb()
            self.timeline.active_range.color = (r, g, b)
            self.populate_edit_area(self.timeline.active_range); self.timeline.update()
            self.save_to_scene()

    def delete_active_range(self):
        """Deletes the currently active timeline range."""
        if self.timeline.active_range in self.timeline.ranges:
            self.timeline.ranges.remove(self.timeline.active_range)
            self.timeline.active_range = None
            self.populate_edit_area(None); self.timeline.update()
            self.timeline.rangesChanged.emit() 

try:
    range_window.close(); range_window.deleteLater()
except:
    pass

range_window = None


def launch_tool():
    """Launches Animation Label Tracker through its MVC entry point.

    Returns:
        object: Animation Label Tracker controller.
    """
    from gt.tools.anim_label_tracker import launch_tool as package_launch_tool

    return package_launch_tool()


if __name__ == "__main__":
    launch_tool()
