"""
Animation Clip Tracker Timeline Widget

A pure Qt timeline used to visualize and edit clip ranges.
This module must remain importable outside Maya, so it never imports "maya.cmds".
Scene state is pushed into the widget by the controller and changes are reported back through signals.
"""
import gt.ui.qt_import as ui_qt

from gt.tools.anim_clip_tracker.clip_tracker_constants import (
    MODE_EDIT,
    MODE_NAVIGATE,
    MODE_SELECT,
    get_valid_mode,
)


CLIP_COLORS = [
    (86, 140, 200),
    (200, 140, 86),
    (120, 180, 120),
    (180, 120, 180),
    (200, 190, 100),
    (120, 180, 190),
    (190, 120, 120),
    (150, 150, 200),
]
INVERTED_BORDER_COLOR = (230, 150, 60)
SELECTED_BORDER_COLOR = (255, 200, 50)
HANDLE_TOLERANCE = 5
SIDE_MARGIN = 8
RULER_HEIGHT = 15
TOP_OFFSET = 14
LANE_SPACING = 2
MIN_LANE_HEIGHT = 8
DRAG_THRESHOLD = 8
FRAME_LABEL_COLOR = (165, 165, 165)
NAME_LABEL_COLOR = (235, 235, 235)


def get_clip_color(index):
    """Gets a stable display color for a clip.

    Args:
        index (int): Clip index.

    Returns:
        tuple: RGB values between 0 and 255.
    """
    return CLIP_COLORS[int(index) % len(CLIP_COLORS)]


def get_clip_span(clip):
    """Gets the low and high frames of a clip, supporting inverted ranges.

    Args:
        clip (dict): Clip data containing "start" and "end" keys.

    Returns:
        tuple: Lowest and highest frame of the clip.
    """
    start_frame = int(clip.get("start", 0))
    end_frame = int(clip.get("end", 0))
    return min(start_frame, end_frame), max(start_frame, end_frame)


def is_inverted_clip(clip):
    """Checks whether a clip has its end frame before its start frame.

    Args:
        clip (dict): Clip data.

    Returns:
        bool: True when the clip range is inverted.
    """
    return int(clip.get("end", 0)) < int(clip.get("start", 0))


def get_clip_display_name(clip):
    """Gets the name shown in the middle of a clip block.

    Args:
        clip (dict): Clip data.

    Returns:
        str: Clip name, or a frame-based name when the clip was never named.
    """
    name = str(clip.get("name") or "").strip()
    if name:
        return name
    return "f{0:04d}-f{1:04d}".format(int(clip.get("start", 0)), int(clip.get("end", 0)))


def clamp_frame(frame, min_frame, max_frame):
    """Keeps a frame value inside a frame range.

    Args:
        frame (int): Frame value to clamp.
        min_frame (int): Lowest allowed frame.
        max_frame (int): Highest allowed frame.

    Returns:
        int: Clamped frame value.
    """
    return max(int(min_frame), min(int(max_frame), int(frame)))


def get_clamped_move_delta(delta, start_frame, end_frame, min_frame, max_frame):
    """Limits a move offset so a clip stays inside a frame range.

    The clip length is preserved, so the offset is reduced instead of the clip being cropped.

    Args:
        delta (int): Requested frame offset.
        start_frame (int): Clip start frame before the move.
        end_frame (int): Clip end frame before the move.
        min_frame (int): Lowest allowed frame.
        max_frame (int): Highest allowed frame.

    Returns:
        int: Offset that keeps the clip inside the range.
    """
    clip_low = min(int(start_frame), int(end_frame))
    clip_high = max(int(start_frame), int(end_frame))
    lowest_delta = int(min_frame) - clip_low
    highest_delta = int(max_frame) - clip_high
    if lowest_delta > highest_delta:
        # The clip is longer than the allowed range, so it stays where it is
        return 0
    return max(lowest_delta, min(highest_delta, int(delta)))


def get_snap_frame(proposed_frame, is_low_edge, clips, ignore_index, threshold):
    """Finds the closest frame that makes a clip edge touch another clip without overlapping.

    Args:
        proposed_frame (int): Frame the edge is being moved to.
        is_low_edge (bool): True when the edge is the lowest frame of its clip.
        clips (list): Clip dictionaries.
        ignore_index (int): Index of the clip being edited.
        threshold (int): Maximum snapping distance in frames.

    Returns:
        int or None: Snapped frame, or None when no target is close enough.
    """
    snapped_frame = None
    closest_distance = int(threshold) + 1
    for index, clip in enumerate(clips or []):
        if index == int(ignore_index):
            continue
        clip_low, clip_high = get_clip_span(clip)
        target_frame = clip_high + 1 if is_low_edge else clip_low - 1
        distance = abs(target_frame - int(proposed_frame))
        if distance <= int(threshold) and distance < closest_distance:
            closest_distance = distance
            snapped_frame = target_frame
    return snapped_frame


def get_snapped_move_delta(delta, start_frame, end_frame, clips, ignore_index, threshold):
    """Adjusts a move offset so the clip snaps to the closest neighboring clip edge.

    Both edges are considered and the closest snapping target wins, so a clip can be
    dropped right after or right before another clip without overlapping it.

    Args:
        delta (int): Requested frame offset.
        start_frame (int): Clip start frame before the move.
        end_frame (int): Clip end frame before the move.
        clips (list): Clip dictionaries.
        ignore_index (int): Index of the clip being moved.
        threshold (int): Maximum snapping distance in frames.

    Returns:
        int: Offset adjusted by the closest snapping target.
    """
    clip_low = min(int(start_frame), int(end_frame)) + int(delta)
    clip_high = max(int(start_frame), int(end_frame)) + int(delta)
    low_target = get_snap_frame(clip_low, True, clips, ignore_index, threshold)
    high_target = get_snap_frame(clip_high, False, clips, ignore_index, threshold)
    low_distance = abs(low_target - clip_low) if low_target is not None else None
    high_distance = abs(high_target - clip_high) if high_target is not None else None
    if low_distance is not None and (high_distance is None or low_distance <= high_distance):
        return int(delta) + (low_target - clip_low)
    if high_distance is not None:
        return int(delta) + (high_target - clip_high)
    return int(delta)


def get_display_bounds(clips, range_start, range_end):
    """Gets the frame bounds the timeline should display.

    The playback range is always included so clips outside of it remain visible.

    Args:
        clips (list): Clip dictionaries.
        range_start (int): Playback range start.
        range_end (int): Playback range end.

    Returns:
        tuple: Lowest and highest frames to display.
    """
    low_frame = min(int(range_start), int(range_end))
    high_frame = max(int(range_start), int(range_end))
    for clip in clips or []:
        clip_low, clip_high = get_clip_span(clip)
        low_frame = min(low_frame, clip_low)
        high_frame = max(high_frame, clip_high)
    if high_frame <= low_frame:
        high_frame = low_frame + 1
    padding = max(1, int((high_frame - low_frame) * 0.02))
    return low_frame - padding, high_frame + padding


def pack_clip_lanes(clips):
    """Assigns clips to stacked lanes so overlapping clips remain readable.

    Args:
        clips (list): Clip dictionaries.

    Returns:
        dict: Mapping of clip indices to zero-based lane indices.
    """
    lane_ends = []
    lanes = {}
    clips = list(clips or [])
    # Lanes are filled in frame order so an unsorted clip list still uses as few lanes as possible
    ordered_indices = sorted(range(len(clips)), key=lambda index: get_clip_span(clips[index]))
    for index in ordered_indices:
        clip_low, clip_high = get_clip_span(clips[index])
        target_lane = None
        for lane_index, lane_end in enumerate(lane_ends):
            if clip_low > lane_end:
                target_lane = lane_index
                break
        if target_lane is None:
            lane_ends.append(clip_high)
            target_lane = len(lane_ends) - 1
        else:
            lane_ends[target_lane] = max(lane_ends[target_lane], clip_high)
        lanes[index] = target_lane
    return lanes


def get_lane_count(lanes):
    """Gets the number of lanes required by a lane mapping.

    Args:
        lanes (dict): Mapping of clip indices to lane indices.

    Returns:
        int: Lane count, at least one.
    """
    if not lanes:
        return 1
    return max(lanes.values()) + 1


def get_event_position(event):
    """Gets the widget-space position of a mouse event across Qt versions.

    Args:
        event (QMouseEvent): Qt mouse event.

    Returns:
        QPoint: Widget-space position.
    """
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


def get_event_global_position(event):
    """Gets the screen-space position of a mouse event across Qt versions.

    Args:
        event (QMouseEvent): Qt mouse event.

    Returns:
        QPoint: Screen-space position.
    """
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


def execute_menu(menu, position):
    """Executes a context menu across Qt versions.

    Args:
        menu (QMenu): Menu to execute.
        position (QPoint): Screen-space position.

    Returns:
        QAction or None: Triggered action.
    """
    if hasattr(menu, "exec_"):
        return menu.exec_(position)
    return menu.exec(position)


class ClipTimelineWidget(ui_qt.QtWidgets.QWidget):
    """Interactive timeline used to visualize and edit clip ranges."""

    frame_changed = ui_qt.QtCore.Signal(int)
    clip_modified = ui_qt.QtCore.Signal(int, int, int)
    clip_created = ui_qt.QtCore.Signal(int, int)
    clip_selected = ui_qt.QtCore.Signal(int)
    clip_delete_requested = ui_qt.QtCore.Signal(int)
    clip_range_requested = ui_qt.QtCore.Signal(int)
    clip_play_requested = ui_qt.QtCore.Signal(int)
    add_clip_requested = ui_qt.QtCore.Signal()
    add_timeline_clip_requested = ui_qt.QtCore.Signal()
    refresh_requested = ui_qt.QtCore.Signal()

    def __init__(self, parent=None):
        """Initializes the clip timeline widget.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setMinimumHeight(90)
        self.setMouseTracking(True)
        self.clips = []
        self.range_start = 1
        self.range_end = 100
        self.current_frame = 1
        self.selected_index = -1
        self.mode = MODE_EDIT
        self.show_names = False
        self.sync_time_on_edit = True
        self.allow_outside_range = False
        self.magnet_enabled = True
        self.snap_tolerance = 10
        self.interaction_state = None
        self.interaction_index = -1
        self.press_x = 0
        self.press_frame = 0
        self.initial_start = 0
        self.initial_end = 0
        self.preview_frame = 0

    # ------------------------------------------------------------------ state
    def set_mode(self, mode):
        """Sets the interaction mode.

        Args:
            mode (str): One of "navigate", "select" or "edit".
        """
        self.mode = get_valid_mode(mode)
        self.unsetCursor()
        self.update()

    def set_show_names(self, state):
        """Sets whether clip names are drawn inside the clip blocks.

        Args:
            state (bool): True to draw clip names.
        """
        self.show_names = bool(state)
        self.update()

    def set_sync_time_on_edit(self, state):
        """Sets whether the current frame follows the mouse in "edit" mode.

        Args:
            state (bool): True to move the current frame while editing.
        """
        self.sync_time_on_edit = bool(state)

    def set_allow_outside_range(self, state):
        """Sets whether clips can be edited outside the timeline range.

        Args:
            state (bool): True to allow clips outside the timeline range.
        """
        self.allow_outside_range = bool(state)
        self.update()

    def set_magnet_state(self, magnet_enabled, snap_tolerance):
        """Sets the magnet snapping options.

        Args:
            magnet_enabled (bool): True to snap clip edges to nearby clips.
            snap_tolerance (int): Maximum snapping distance in frames.
        """
        self.magnet_enabled = bool(magnet_enabled)
        self.snap_tolerance = max(1, int(snap_tolerance))

    def get_range_bounds(self):
        """Gets the lowest and highest frames clips may use.

        Returns:
            tuple: Lowest and highest allowed frames.
        """
        return min(self.range_start, self.range_end), max(self.range_start, self.range_end)

    def set_clips(self, clips):
        """Sets the clips displayed by the timeline.

        Args:
            clips (list): Clip dictionaries.
        """
        self.clips = [dict(clip) for clip in clips or []]
        if self.selected_index >= len(self.clips):
            self.selected_index = -1
        self.update()

    def set_frame_state(self, range_start, range_end, current_frame):
        """Sets the playback range and current frame.

        Interactions are not interrupted, so dragging values are never overwritten.

        Args:
            range_start (int): Playback range start.
            range_end (int): Playback range end.
            current_frame (int): Current frame.
        """
        if self.interaction_state:
            return
        changed = (
            int(range_start) != self.range_start
            or int(range_end) != self.range_end
            or int(current_frame) != self.current_frame
        )
        self.range_start = int(range_start)
        self.range_end = int(range_end)
        self.current_frame = int(current_frame)
        if changed:
            self.update()

    def set_selected_index(self, index):
        """Sets the highlighted clip.

        Args:
            index (int): Clip index, or a negative value to clear the selection.
        """
        self.selected_index = int(index)
        self.update()

    # ------------------------------------------------------------- coordinates
    def get_display_range(self):
        """Gets the frame bounds currently displayed.

        Returns:
            tuple: Lowest and highest displayed frames.
        """
        return get_display_bounds(self.clips, self.range_start, self.range_end)

    def frame_to_x(self, frame):
        """Converts a frame value into a widget x-coordinate.

        Args:
            frame (float): Frame value.

        Returns:
            int: Widget x-coordinate.
        """
        low_frame, high_frame = self.get_display_range()
        usable_width = max(1, self.width() - (SIDE_MARGIN * 2))
        frame_span = max(1, high_frame - low_frame)
        return int(SIDE_MARGIN + ((float(frame) - low_frame) / frame_span) * usable_width)

    def x_to_frame(self, position_x):
        """Converts a widget x-coordinate into a frame value.

        Args:
            position_x (float): Widget x-coordinate.

        Returns:
            int: Frame value.
        """
        low_frame, high_frame = self.get_display_range()
        usable_width = max(1, self.width() - (SIDE_MARGIN * 2))
        frame_span = max(1, high_frame - low_frame)
        return int(round(low_frame + ((float(position_x) - SIDE_MARGIN) / usable_width) * frame_span))

    def get_lane_geometry(self):
        """Gets the lane mapping and drawing metrics of the clip area.

        Returns:
            tuple: Lane mapping, lane height and top offset.
        """
        lanes = pack_clip_lanes(self.clips)
        lane_count = get_lane_count(lanes)
        available_height = max(MIN_LANE_HEIGHT, self.height() - RULER_HEIGHT - TOP_OFFSET - 4)
        # Clips use the full height while they fit in one lane and shrink once they overlap
        lane_height = int((available_height - (LANE_SPACING * (lane_count - 1))) / lane_count)
        lane_height = max(MIN_LANE_HEIGHT, lane_height)
        return lanes, lane_height, TOP_OFFSET

    def get_clip_rect(self, index, lanes, lane_height, top_offset):
        """Gets the drawing rectangle of a clip.

        Args:
            index (int): Clip index.
            lanes (dict): Lane mapping.
            lane_height (int): Height of one lane.
            top_offset (int): Top offset of the first lane.

        Returns:
            QRect: Clip rectangle.
        """
        clip_low, clip_high = get_clip_span(self.clips[index])
        left_x = self.frame_to_x(clip_low)
        right_x = self.frame_to_x(clip_high + 1)
        lane_index = lanes.get(index, 0)
        top_y = top_offset + (lane_index * (lane_height + LANE_SPACING))
        return ui_qt.QtCore.QRect(left_x, top_y, max(3, right_x - left_x), lane_height)

    def get_handle_positions(self, clip):
        """Gets the x-coordinates of the start and end handles of a clip.

        Inverted clips keep their start handle on the right side of the block.

        Args:
            clip (dict): Clip data.

        Returns:
            tuple: Start handle and end handle x-coordinates.
        """
        start_frame = int(clip.get("start", 0))
        end_frame = int(clip.get("end", 0))
        if is_inverted_clip(clip):
            return self.frame_to_x(start_frame + 1), self.frame_to_x(end_frame)
        return self.frame_to_x(start_frame), self.frame_to_x(end_frame + 1)

    def get_clip_and_zone_at(self, position):
        """Finds the clip and interaction zone under a widget position.

        Args:
            position (QPoint): Widget-space position.

        Returns:
            tuple: Clip index and zone name. Returns ``(-1, None)`` when nothing is hit.
        """
        lanes, lane_height, top_offset = self.get_lane_geometry()
        for index in reversed(range(len(self.clips))):
            clip_rect = self.get_clip_rect(index, lanes, lane_height, top_offset)
            hit_rect = clip_rect.adjusted(-HANDLE_TOLERANCE, 0, HANDLE_TOLERANCE, 0)
            if not hit_rect.contains(position):
                continue
            clip = self.clips[index]
            start_x, end_x = self.get_handle_positions(clip)
            if self.mode == MODE_EDIT:
                if abs(position.x() - start_x) <= HANDLE_TOLERANCE:
                    return index, "start"
                if abs(position.x() - end_x) <= HANDLE_TOLERANCE:
                    return index, "end"
            return index, "center"
        return -1, None

    # ---------------------------------------------------------------- painting
    def paintEvent(self, event):
        """Paints the timeline background, clips, playhead and ruler.

        Args:
            event (QPaintEvent): Qt paint event.
        """
        painter = ui_qt.QtGui.QPainter(self)
        painter.setRenderHint(ui_qt.QtLib.RenderHint.Antialiasing, False)
        widget_rect = self.rect()
        painter.fillRect(widget_rect, ui_qt.QtGui.QColor(38, 38, 38))
        self.draw_playback_band(painter, widget_rect)
        self.draw_ruler(painter, widget_rect)
        self.draw_clips(painter)
        self.draw_creation_preview(painter)
        self.draw_playhead(painter, widget_rect)
        painter.end()

    def draw_creation_preview(self, painter):
        """Draws the range preview shown while creating a clip.

        Args:
            painter (QPainter): Active painter.
        """
        if self.interaction_state != "create":
            return
        _, lane_height, top_offset = self.get_lane_geometry()
        preview_start = self.limit_frame(min(self.press_frame, self.preview_frame))
        preview_end = self.limit_frame(max(self.press_frame, self.preview_frame))
        left_x = self.frame_to_x(preview_start)
        right_x = self.frame_to_x(preview_end + 1)
        preview_rect = ui_qt.QtCore.QRect(left_x, top_offset, max(3, right_x - left_x), lane_height)
        painter.fillRect(preview_rect, ui_qt.QtGui.QColor(220, 220, 220, 70))
        painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(*SELECTED_BORDER_COLOR), 1, ui_qt.QtLib.PenStyle.DashLine))
        painter.drawRect(preview_rect.adjusted(0, 0, -1, -1))

    def draw_playback_band(self, painter, widget_rect):
        """Draws the playback range area.

        Args:
            painter (QPainter): Active painter.
            widget_rect (QRect): Widget rectangle.
        """
        band_color = ui_qt.QtGui.QColor(52, 52, 52)
        if not self.allow_outside_range:
            # The areas outside the timeline range are hidden because clips cannot be moved there
            painter.fillRect(widget_rect, band_color)
            return
        min_frame, max_frame = self.get_range_bounds()
        band_start = self.frame_to_x(min_frame)
        band_end = self.frame_to_x(max_frame + 1)
        band_rect = ui_qt.QtCore.QRect(band_start, 0, max(1, band_end - band_start), widget_rect.height())
        painter.fillRect(band_rect, band_color)
        painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(90, 90, 90), 1, ui_qt.QtLib.PenStyle.DashLine))
        painter.drawLine(band_start, 0, band_start, widget_rect.height())
        painter.drawLine(band_end, 0, band_end, widget_rect.height())

    def draw_ruler(self, painter, widget_rect):
        """Draws the frame ruler.

        Args:
            painter (QPainter): Active painter.
            widget_rect (QRect): Widget rectangle.
        """
        low_frame, high_frame = self.get_display_range()
        frame_span = max(1, high_frame - low_frame)
        step = max(1, int(frame_span / 10))
        painter.setPen(ui_qt.QtGui.QColor(150, 150, 150))
        base_y = widget_rect.height()
        for frame in range(low_frame, high_frame + 1, step):
            tick_x = self.frame_to_x(frame)
            painter.drawLine(tick_x, base_y - 5, tick_x, base_y)
            painter.drawText(tick_x + 2, base_y - 5, str(frame))

    def draw_clips(self, painter):
        """Draws every clip block.

        Args:
            painter (QPainter): Active painter.
        """
        lanes, lane_height, top_offset = self.get_lane_geometry()
        for index, clip in enumerate(self.clips):
            clip_rect = self.get_clip_rect(index, lanes, lane_height, top_offset)
            base_color = ui_qt.QtGui.QColor(*get_clip_color(index))
            is_active = bool(clip.get("active", True))
            fill_color = ui_qt.QtGui.QColor(base_color)
            fill_color.setAlpha(160 if is_active else 60)
            if is_active:
                painter.fillRect(clip_rect, fill_color)
            else:
                painter.fillRect(clip_rect, ui_qt.QtGui.QColor(60, 60, 60, 120))
                painter.fillRect(clip_rect, ui_qt.QtGui.QBrush(fill_color, ui_qt.QtLib.BrushStyle.BDiagPattern))
            if is_inverted_clip(clip):
                inverted_color = ui_qt.QtGui.QColor(*INVERTED_BORDER_COLOR)
                inverted_color.setAlpha(120)
                painter.fillRect(clip_rect, ui_qt.QtGui.QBrush(inverted_color, ui_qt.QtLib.BrushStyle.FDiagPattern))
                border_color = ui_qt.QtGui.QColor(*INVERTED_BORDER_COLOR)
            else:
                border_color = base_color
            if index == self.selected_index:
                painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(*SELECTED_BORDER_COLOR), 2))
            else:
                painter.setPen(ui_qt.QtGui.QPen(border_color, 1))
            painter.drawRect(clip_rect.adjusted(0, 0, -1, -1))
            self.draw_clip_label(painter, clip_rect, clip)

    def draw_clip_label(self, painter, clip_rect, clip):
        """Draws the frame values and the optional name of one clip.

        Args:
            painter (QPainter): Active painter.
            clip_rect (QRect): Clip rectangle.
            clip (dict): Clip data.
        """
        if clip_rect.height() < 14:
            return
        start_label = str(int(clip.get("start", 0)))
        end_label = str(int(clip.get("end", 0)))
        metrics = painter.fontMetrics()
        start_width = metrics.horizontalAdvance(start_label)
        end_width = metrics.horizontalAdvance(end_label)
        text_rect = clip_rect.adjusted(3, 0, -3, -2)
        if clip_rect.width() > start_width + end_width + 8:
            painter.setPen(ui_qt.QtGui.QColor(*FRAME_LABEL_COLOR))
            bottom_left = ui_qt.QtLib.AlignmentFlag.AlignBottom | ui_qt.QtLib.AlignmentFlag.AlignLeft
            bottom_right = ui_qt.QtLib.AlignmentFlag.AlignBottom | ui_qt.QtLib.AlignmentFlag.AlignRight
            painter.drawText(text_rect, bottom_left, start_label)
            painter.drawText(text_rect, bottom_right, end_label)
        if not self.show_names:
            return
        display_name = get_clip_display_name(clip)
        name_width = metrics.horizontalAdvance(display_name)
        if name_width > clip_rect.width() - (start_width + end_width + 16):
            return
        painter.setPen(ui_qt.QtGui.QColor(*NAME_LABEL_COLOR))
        painter.drawText(text_rect, ui_qt.QtLib.AlignmentFlag.AlignCenter, display_name)

    def draw_playhead(self, painter, widget_rect):
        """Draws the current frame marker.

        Args:
            painter (QPainter): Active painter.
            widget_rect (QRect): Widget rectangle.
        """
        playhead_x = self.frame_to_x(self.current_frame)
        painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(235, 60, 60), 2))
        painter.drawLine(playhead_x, 0, playhead_x, widget_rect.height() - RULER_HEIGHT + 4)
        painter.setPen(ui_qt.QtGui.QColor(240, 200, 200))
        painter.drawText(playhead_x + 3, 11, str(self.current_frame))

    # ------------------------------------------------------------ interactions
    def mousePressEvent(self, event):
        """Starts a scrub, selection or edit interaction.

        Args:
            event (QMouseEvent): Qt mouse press event.
        """
        position = get_event_position(event)
        clip_index, zone = self.get_clip_and_zone_at(position)
        if event.button() == ui_qt.QtLib.MouseButton.RightButton:
            self.show_context_menu(event, clip_index)
            return
        if event.button() != ui_qt.QtLib.MouseButton.LeftButton:
            return
        self.press_x = position.x()
        self.press_frame = self.x_to_frame(position.x())
        self.interaction_index = clip_index
        if self.mode == MODE_NAVIGATE:
            self.begin_scrub()
            return
        if self.mode == MODE_SELECT:
            playhead_x = self.frame_to_x(self.current_frame)
            if abs(position.x() - playhead_x) <= DRAG_THRESHOLD:
                self.begin_scrub()
                return
            self.select_clip(clip_index)
            return
        if clip_index < 0:
            self.interaction_state = "scrub_or_create"
            self.select_clip(-1)
            self.set_edit_frame(self.press_frame)
            return
        clip = self.clips[clip_index]
        self.initial_start = int(clip.get("start", 0))
        self.initial_end = int(clip.get("end", 0))
        self.select_clip(clip_index)
        if zone == "start":
            self.interaction_state = "resize_start"
        elif zone == "end":
            self.interaction_state = "resize_end"
        else:
            self.interaction_state = "move"

    def mouseMoveEvent(self, event):
        """Updates cursors and drag interactions.

        Args:
            event (QMouseEvent): Qt mouse move event.
        """
        position = get_event_position(event)
        if not self.interaction_state:
            self.update_hover_state(position)
            return
        hover_frame = self.x_to_frame(position.x())
        if self.interaction_state == "scrub":
            self.set_current_frame_from_interaction(hover_frame)
            return
        if self.interaction_state == "scrub_or_create":
            if abs(position.x() - self.press_x) > DRAG_THRESHOLD:
                self.interaction_state = "create"
            else:
                self.set_edit_frame(hover_frame)
                return
        if self.interaction_state == "create":
            self.preview_frame = hover_frame
            # The current frame keeps following the cursor as a preview of the new range end
            self.set_edit_frame(hover_frame)
            self.update()
            return
        if self.interaction_index < 0 or self.interaction_index >= len(self.clips):
            return
        clip = self.clips[self.interaction_index]
        is_precision = bool(event.modifiers() & ui_qt.QtLib.KeyboardModifier.ControlModifier)
        raw_delta = hover_frame - self.press_frame
        delta = int(raw_delta * 0.2) if is_precision else raw_delta
        min_frame, max_frame = self.get_range_bounds()
        if self.interaction_state == "resize_start":
            clip["start"] = self.limit_frame(self.snap_edge_frame(self.initial_start + delta, clip.get("end")))
        elif self.interaction_state == "resize_end":
            clip["end"] = self.limit_frame(self.snap_edge_frame(self.initial_end + delta, clip.get("start")))
        elif self.interaction_state == "move":
            if self.magnet_enabled:
                delta = get_snapped_move_delta(
                    delta,
                    self.initial_start,
                    self.initial_end,
                    self.clips,
                    self.interaction_index,
                    self.snap_tolerance,
                )
            if not self.allow_outside_range:
                delta = get_clamped_move_delta(
                    delta,
                    self.initial_start,
                    self.initial_end,
                    min_frame,
                    max_frame,
                )
            clip["start"] = self.initial_start + delta
            clip["end"] = self.initial_end + delta
        self.update()

    def mouseReleaseEvent(self, event):
        """Commits the current drag interaction.

        Args:
            event (QMouseEvent): Qt mouse release event.
        """
        position = get_event_position(event)
        state = self.interaction_state
        self.interaction_state = None
        if state == "create":
            release_frame = self.x_to_frame(position.x())
            start_frame = self.limit_frame(min(self.press_frame, release_frame))
            end_frame = self.limit_frame(max(self.press_frame, release_frame))
            self.clip_created.emit(int(start_frame), int(end_frame))
        elif state in ["resize_start", "resize_end", "move"]:
            if 0 <= self.interaction_index < len(self.clips):
                clip = self.clips[self.interaction_index]
                start_frame = int(clip.get("start", 0))
                end_frame = int(clip.get("end", 0))
                # Clicks that did not change any frame should not dirty the scene
                if start_frame != self.initial_start or end_frame != self.initial_end:
                    self.clip_modified.emit(int(self.interaction_index), start_frame, end_frame)
        self.interaction_index = -1
        self.update()

    def update_hover_state(self, position):
        """Updates the mouse cursor and tooltip for a hovered position.

        Args:
            position (QPoint): Widget-space position.
        """
        clip_index, zone = self.get_clip_and_zone_at(position)
        playhead_x = self.frame_to_x(self.current_frame)
        if self.mode == MODE_NAVIGATE:
            self.setCursor(ui_qt.QtLib.CursorShape.SizeHorCursor)
        elif self.mode == MODE_SELECT:
            if abs(position.x() - playhead_x) <= DRAG_THRESHOLD:
                self.setCursor(ui_qt.QtLib.CursorShape.SizeHorCursor)
            elif clip_index >= 0:
                self.setCursor(ui_qt.QtLib.CursorShape.PointingHandCursor)
            else:
                self.setCursor(ui_qt.QtLib.CursorShape.ArrowCursor)
        elif zone in ["start", "end"]:
            self.setCursor(ui_qt.QtLib.CursorShape.SplitHCursor)
        else:
            self.setCursor(ui_qt.QtLib.CursorShape.ArrowCursor)
        self.setToolTip(self.get_clip_tooltip(clip_index))

    def get_clip_tooltip(self, clip_index):
        """Gets the tooltip text of a clip.

        Args:
            clip_index (int): Clip index, or a negative value for empty areas.

        Returns:
            str: Tooltip text.
        """
        if clip_index < 0 or clip_index >= len(self.clips):
            return (
                "Timeline View\n"
                "Navigate: drag to change the current frame.\n"
                "Select: click a clip to highlight it.\n"
                "Edit: drag clip edges to resize, drag a clip to move it,\n"
                "drag an empty area to create a new clip."
            )
        clip = self.clips[clip_index]
        start_frame = int(clip.get("start", 0))
        end_frame = int(clip.get("end", 0))
        clip_low, clip_high = get_clip_span(clip)
        lines = [
            "{0}. {1}".format(clip_index + 1, clip.get("name") or "Unnamed clip"),
            "Start: {0}   End: {1}".format(start_frame, end_frame),
            "Frames: {0}".format(clip_high - clip_low + 1),
        ]
        if is_inverted_clip(clip):
            lines.append("Inverted range: the end frame is before the start frame.")
        if not clip.get("active", True):
            lines.append("Inactive clip.")
        return "\n".join(lines)

    def begin_scrub(self):
        """Starts scrubbing the current frame from the last press position."""
        self.interaction_state = "scrub"
        self.set_current_frame_from_interaction(self.press_frame)

    def snap_edge_frame(self, proposed_frame, opposite_frame):
        """Snaps a resized clip edge to the closest neighboring clip.

        Args:
            proposed_frame (int): Frame the edited edge is being moved to.
            opposite_frame (int): Frame of the edge that is not being edited.

        Returns:
            int: Snapped frame, or the proposed frame when snapping is off or too far.
        """
        if not self.magnet_enabled:
            return int(proposed_frame)
        is_low_edge = int(proposed_frame) <= int(opposite_frame)
        snapped_frame = get_snap_frame(
            proposed_frame,
            is_low_edge,
            self.clips,
            self.interaction_index,
            self.snap_tolerance,
        )
        return int(proposed_frame) if snapped_frame is None else int(snapped_frame)

    def limit_frame(self, frame):
        """Keeps a frame inside the timeline range when required.

        Args:
            frame (int): Frame value being edited.

        Returns:
            int: Frame value allowed by the current preferences.
        """
        if self.allow_outside_range:
            return int(frame)
        min_frame, max_frame = self.get_range_bounds()
        return clamp_frame(frame, min_frame, max_frame)

    def set_edit_frame(self, frame):
        """Updates the current frame from an "edit" mode interaction.

        Nothing happens when moving the current frame while editing is disabled.

        Args:
            frame (int): New current frame.
        """
        if not self.sync_time_on_edit:
            return
        self.set_current_frame_from_interaction(frame)

    def set_current_frame_from_interaction(self, frame):
        """Updates the local playhead and reports the new frame.

        Args:
            frame (int): New current frame.
        """
        self.current_frame = int(frame)
        self.frame_changed.emit(int(frame))
        self.update()

    def select_clip(self, clip_index):
        """Selects a clip and reports the change.

        Args:
            clip_index (int): Clip index, or a negative value to clear the selection.
        """
        self.selected_index = int(clip_index)
        self.clip_selected.emit(int(clip_index))
        self.update()

    def show_context_menu(self, event, clip_index):
        """Shows the timeline context menu.

        Args:
            event (QMouseEvent): Qt mouse press event.
            clip_index (int): Clip index under the cursor, or a negative value.
        """
        menu = ui_qt.QtWidgets.QMenu(self)
        if clip_index >= 0:
            self.select_clip(clip_index)
            clip = self.clips[clip_index]
            action_set_start = menu.addAction("Set Current Frame as Start")
            action_set_end = menu.addAction("Set Current Frame as End")
            action_range = menu.addAction("Set Timeline Range to Clip")
            action_play = menu.addAction("Play/Pause Clip")
            action_swap = menu.addAction("Swap Start and End") if is_inverted_clip(clip) else None
            menu.addSeparator()
            action_delete = menu.addAction("Delete Clip")
            triggered = execute_menu(menu, get_event_global_position(event))
            if triggered is None:
                return
            if triggered == action_range:
                self.clip_range_requested.emit(int(clip_index))
            elif triggered == action_play:
                self.clip_play_requested.emit(int(clip_index))
            elif triggered == action_set_start:
                self.clip_modified.emit(
                    int(clip_index),
                    int(self.current_frame),
                    int(clip.get("end", 0)),
                )
            elif triggered == action_set_end:
                self.clip_modified.emit(
                    int(clip_index),
                    int(clip.get("start", 0)),
                    int(self.current_frame),
                )
            elif action_swap is not None and triggered == action_swap:
                self.clip_modified.emit(
                    int(clip_index),
                    int(clip.get("end", 0)),
                    int(clip.get("start", 0)),
                )
            elif triggered == action_delete:
                self.clip_delete_requested.emit(int(clip_index))
            return
        action_add = menu.addAction("Add New Clip")
        action_add_timeline = menu.addAction("Add Timeline Range as Clip")
        menu.addSeparator()
        action_refresh = menu.addAction("Refresh Clip List")
        triggered = execute_menu(menu, get_event_global_position(event))
        if triggered is None:
            return
        if triggered == action_add:
            self.add_clip_requested.emit()
        elif triggered == action_add_timeline:
            self.add_timeline_clip_requested.emit()
        elif triggered == action_refresh:
            self.refresh_requested.emit()
