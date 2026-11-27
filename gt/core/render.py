"""Draws skeleton pose sheets from sampled joint positions, without a Maya viewport.

A pose sheet shows many moments of an animation in one image: a row of side-view poses, an optional front-view row,
an optional travel overlay, and an optional top-down map of the path. Left limbs are blue, right limbs are red, and
the spine and head are grey. Every pose is drawn at one shared scale so sizes stay comparable.

The geometry helpers are pure Python and importable outside Maya. Drawing needs Qt and imports it lazily.

Positions are dictionaries of role name to canonical Y-up ``(x, y, z)`` tuples, one dictionary per frame. Supported
roles: pelvis, spine, chest, neck, head, ``left_``/``right_`` upper_leg, knee, foot, toe, arm, forearm and hand.
"""

import bisect
import math
import os

VIEW_SIDE = "side"
VIEW_FRONT = "front"
VIEW_TRAVEL = "travel"
VIEW_TOP = "top"
ALL_VIEWS = (VIEW_SIDE, VIEW_FRONT, VIEW_TRAVEL, VIEW_TOP)
VIEW_TITLES = {
    VIEW_SIDE: "SIDE VIEW - character faces right",
    VIEW_FRONT: "FRONT VIEW",
    VIEW_TRAVEL: "TRAVEL - poses at their real positions, older = fainter",
    VIEW_TOP: "TOP VIEW - path from above, start heading to the right",
}
BONE_CHAINS = (
    ("spine", ("pelvis", "spine", "chest", "neck", "head")),
    ("left", ("pelvis", "left_upper_leg", "left_knee", "left_foot", "left_toe")),
    ("right", ("pelvis", "right_upper_leg", "right_knee", "right_foot", "right_toe")),
    ("left", ("chest", "left_arm", "left_forearm", "left_hand")),
    ("right", ("chest", "right_arm", "right_forearm", "right_hand")),
)
GROUP_COLORS = {"left": (60, 120, 235), "right": (225, 70, 70), "spine": (70, 70, 80)}
BACKGROUND = (246, 246, 246)
GROUND = (150, 150, 150)
TEXT = (40, 40, 40)
ROW_HEIGHT = 320
MINIMUM_CELL_WIDTH = 150
TRAVEL_THRESHOLD = 1.5
TOP_MINIMUM_PATH = 0.75
TOP_MINIMUM_TURN = 30.0

_application = None


# ------------------------------------------------------------------------------------------ pure geometry
def build_bones(roles):
    """Connects the available roles along each limb, skipping roles that are missing.

    Args:
        roles (iterable): Role names present in the positions.

    Returns:
        list: ``(first_role, second_role, group)`` tuples where group is spine, left or right.
    """
    available = set(roles)
    bones = []
    for group, chain in BONE_CHAINS:
        present = [role for role in chain if role in available]
        bones.extend((first, second, group) for first, second in zip(present, present[1:]))
    return bones


def _normalize(x_value, z_value):
    """Normalizes a ground-plane vector.

    Args:
        x_value (float): X component.
        z_value (float): Z component.

    Returns:
        tuple or None: Unit vector, or None when the vector is too short.
    """
    length = math.hypot(x_value, z_value)
    return (x_value / length, z_value / length) if length > 1e-9 else None


def get_heading(sample, previous=None):
    """Finds the direction the character faces on the ground plane.

    The hip line gives the sideways axis and the toes decide which way is forward.

    Args:
        sample (dict): Role positions of one frame.
        previous (tuple, optional): Heading of the previous frame, used when this frame has no hip line.

    Returns:
        tuple: Unit ``(x, z)`` heading. Defaults to +X when nothing is known.
    """
    left = sample.get("left_upper_leg")
    right = sample.get("right_upper_leg")
    heading = None
    if left and right:
        side = _normalize(right[0] - left[0], right[2] - left[2])
        if side:
            heading = (side[1], -side[0])
            toes = [
                (sample[f"{name}_toe"][0] - sample[f"{name}_foot"][0], sample[f"{name}_toe"][2] - sample[f"{name}_foot"][2])
                for name in ("left", "right") if f"{name}_toe" in sample and f"{name}_foot" in sample
            ]
            if toes and sum(offset[0] * heading[0] + offset[1] * heading[1] for offset in toes) < 0:
                heading = (-heading[0], -heading[1])
            elif not toes and previous and heading[0] * previous[0] + heading[1] * previous[1] < 0:
                heading = (-heading[0], -heading[1])
    return heading or previous or (1.0, 0.0)


def get_headings(positions):
    """Gets a heading per frame, carrying the last known direction through gaps.

    Args:
        positions (list): Role positions per frame.

    Returns:
        list: Unit ``(x, z)`` heading per frame.
    """
    headings = []
    previous = None
    for sample in positions:
        previous = get_heading(sample, previous)
        headings.append(previous)
    return headings


def project_point(point, origin, heading, view):
    """Projects a world point to 2D view coordinates (x to the right, y up).

    Args:
        point (tuple): World ``(x, y, z)``.
        origin (tuple): World position that maps to x=0 (and y=0 for the top view).
        heading (tuple): Unit ground heading that becomes screen-right.
        view (str): ``side``, ``front``, ``travel`` or ``top``.

    Returns:
        tuple: ``(horizontal, vertical)`` in world units.
    """
    delta_x, delta_z = point[0] - origin[0], point[2] - origin[2]
    forward = delta_x * heading[0] + delta_z * heading[1]
    right = delta_x * -heading[1] + delta_z * heading[0]
    if view == VIEW_FRONT:
        return -right, point[1]
    if view == VIEW_TOP:
        return forward, -right
    return forward, point[1]


def estimate_floor(positions):
    """Estimates the ground height from the lowest feet and toes.

    Args:
        positions (list): Role positions per frame.

    Returns:
        float: Estimated floor height.
    """
    heights = sorted(
        sample[role][1] for sample in positions for role in ("left_toe", "right_toe", "left_foot", "right_foot")
        if role in sample
    )
    return heights[int(len(heights) * 0.04)] if heights else 0.0


def estimate_leg_length(positions):
    """Estimates leg length from the first frames.

    Args:
        positions (list): Role positions per frame.

    Returns:
        float: Leg length in scene units, or 1.0 when no leg is available.
    """
    lengths = []
    for sample in positions[:24]:
        for side in ("left", "right"):
            hip, knee, foot = (sample.get(f"{side}_{name}") for name in ("upper_leg", "knee", "foot"))
            if hip and knee and foot:
                lengths.append(math.dist(hip, knee) + math.dist(knee, foot))
    return sorted(lengths)[len(lengths) // 2] if lengths else 1.0


def measure_travel(positions, leg_length):
    """Measures how far the pelvis moves on the ground plane.

    Args:
        positions (list): Role positions per frame.
        leg_length (float): Scale used to normalize distances.

    Returns:
        dict: ``path`` and ``net`` distances in leg lengths, plus the unit ``direction`` of net travel (or None).
    """
    points = [(sample["pelvis"][0], sample["pelvis"][2]) for sample in positions if "pelvis" in sample]
    path = sum(math.dist(first, second) for first, second in zip(points, points[1:]))
    net = math.dist(points[0], points[-1]) if len(points) > 1 else 0.0
    direction = _normalize(points[-1][0] - points[0][0], points[-1][1] - points[0][1]) if len(points) > 1 else None
    return {"path": path / leg_length, "net": net / leg_length, "direction": direction}


def select_pose_indices(positions, count, leg_length):
    """Picks frames spaced evenly by how much the pose changes, so busy moments get more poses.

    A small time-based share keeps long still holds represented. The first and last frames are always included.

    Args:
        positions (list): Role positions per frame.
        count (int): Wanted number of poses.
        leg_length (float): Scale used to normalize pose changes.

    Returns:
        list: Ascending, unique frame indices into positions.
    """
    total = len(positions)
    if total <= max(count, 1):
        return list(range(total))
    roles = sorted(positions[0])

    def vector(sample):
        """Flattens a pose relative to the pelvis, keeping absolute pelvis height.

        Args:
            sample (dict): Role positions of one frame.

        Returns:
            list: Pose coordinates.
        """
        pelvis = sample.get("pelvis", (0.0, 0.0, 0.0))
        values = [pelvis[1]]
        for role in roles:
            point = sample.get(role, pelvis)
            values.extend(point[axis] - pelvis[axis] for axis in range(3))
        return values

    vectors = [vector(sample) for sample in positions]
    changes = [0.0] + [math.dist(first, second) / leg_length for first, second in zip(vectors, vectors[1:])]
    mean_change = sum(changes) / len(changes)
    cumulative = []
    running = 0.0
    for change in changes:
        running += change + 0.25 * mean_change + 1e-6
        cumulative.append(running)
    chosen = {0, total - 1}
    for step in range(1, count - 1):
        target = cumulative[0] + (cumulative[-1] - cumulative[0]) * step / (count - 1)
        chosen.add(min(bisect.bisect_left(cumulative, target), total - 1))
    while len(chosen) < count:
        spare = [index for index in range(total) if index not in chosen]
        chosen.add(max(spare, key=lambda index: min(abs(index - other) for other in chosen)))
    return sorted(chosen)


def describe_span(positions, fps, leg_length, floor):
    """Summarizes a span of frames with simple measured facts.

    Args:
        positions (list): Role positions per frame.
        fps (float): Frames per second.
        leg_length (float): Scale used to normalize distances.
        floor (float): Floor height.

    Returns:
        dict: Duration in seconds, travel in leg lengths, average speed and pelvis height range.
    """
    travel = measure_travel(positions, leg_length)
    seconds = max(len(positions) - 1, 1) / fps
    heights = [(sample["pelvis"][1] - floor) / leg_length for sample in positions if "pelvis" in sample]
    return {
        "duration_seconds": round(seconds, 2),
        "path_leg_lengths": round(travel["path"], 2),
        "net_leg_lengths": round(travel["net"], 2),
        "average_speed_leg_lengths_per_second": round(travel["path"] / seconds, 2),
        "pelvis_height_range": [round(min(heights), 2), round(max(heights), 2)] if heights else [],
    }


# -------------------------------------------------------------------------------------------------- drawing
def ensure_qt_application():
    """Makes sure a Qt application exists so text can be drawn, creating an offscreen one outside a GUI.

    Returns:
        bool: True when drawing with text is possible.
    """
    global _application
    from gt.ui.qt_import import QtGui

    if QtGui.QGuiApplication.instance() is not None:
        return True
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _application = QtGui.QGuiApplication([])
    return True


def _qt_color(rgb, alpha=255):
    """Builds a QColor.

    Args:
        rgb (tuple): Red, green, blue values.
        alpha (int): Opacity from 0 to 255.

    Returns:
        QColor: Color.
    """
    from gt.ui.qt_import import QtGui

    return QtGui.QColor(rgb[0], rgb[1], rgb[2], alpha)


def _draw_figure(painter, sample, bones, mapper, alpha=255, line_width=5.0, head_radius=0.0):
    """Draws one projected skeleton.

    Args:
        painter (QPainter): Active painter.
        sample (dict): Role positions of the pose.
        bones (list): Bones from build_bones.
        mapper (callable): Converts a role position to pixel ``(x, y)``.
        alpha (int): Opacity from 0 to 255.
        line_width (float): Bone thickness in pixels.
        head_radius (float): Head circle radius in pixels, or 0 for none.
    """
    from gt.ui.qt_import import QtCore, QtGui

    order = {"left": 0, "spine": 1, "right": 2}
    for first, second, group in sorted(bones, key=lambda bone: order[bone[2]]):
        if first not in sample or second not in sample:
            continue
        pen = QtGui.QPen(_qt_color(GROUP_COLORS[group], alpha), line_width)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        start, end = mapper(sample[first]), mapper(sample[second])
        painter.drawLine(QtCore.QPointF(*start), QtCore.QPointF(*end))
    if head_radius and "head" in sample:
        painter.setPen(QtGui.QPen(_qt_color(GROUP_COLORS["spine"], alpha), 3))
        painter.setBrush(_qt_color(BACKGROUND, alpha))
        painter.drawEllipse(QtCore.QPointF(*mapper(sample["head"])), head_radius, head_radius)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)


def _draw_label(painter, text, x_value, y_value, size=15, bold=True, align_center=True):
    """Draws a text label.

    Args:
        painter (QPainter): Active painter.
        text (str): Label text.
        x_value (float): Anchor x in pixels.
        y_value (float): Baseline y in pixels.
        size (int): Font pixel size.
        bold (bool): Whether to use a bold font.
        align_center (bool): Centers the text on x_value when true, else starts at x_value.
    """
    from gt.ui.qt_import import QtCore, QtGui

    font = QtGui.QFont()
    font.setPixelSize(size)
    font.setBold(bold)
    painter.setFont(font)
    painter.setPen(_qt_color(TEXT))
    width = painter.fontMetrics().horizontalAdvance(text)
    painter.drawText(QtCore.QPointF(x_value - width / 2 if align_center else x_value, y_value), text)


def _frame_text(frame, fps):
    """Formats a frame label with its time.

    Args:
        frame (int): Frame number.
        fps (float): Frames per second.

    Returns:
        str: Label such as ``f57 1.9s``.
    """
    return f"f{frame} {frame / fps:.1f}s"


def _draw_ground(painter, y_value, width):
    """Draws the ground line.

    Args:
        painter (QPainter): Active painter.
        y_value (float): Ground y in pixels.
        width (float): Image width in pixels.
    """
    from gt.ui.qt_import import QtCore, QtGui

    painter.setPen(QtGui.QPen(_qt_color(GROUND), 2))
    painter.drawLine(QtCore.QPointF(8, y_value), QtCore.QPointF(width - 8, y_value))


def _paint_profile_row(painter, view, positions, indices, frames, context, top, width):
    """Paints a row of evenly spaced side or front poses.

    Args:
        painter (QPainter): Active painter.
        view (str): ``side`` or ``front``.
        positions (list): Role positions of the chunk.
        indices (list): Frame indices to draw.
        frames (list): Scene frame numbers of the chunk.
        context (dict): Shared leg_length, floor, fps, bones and headings.
        top (float): Row top in pixels.
        width (float): Image width in pixels.
    """
    leg = context["leg_length"]
    cell = width / len(indices)
    heights = [
        point[1] - context["floor"] for index in indices for point in positions[index].values()
    ]
    tallest = max(max(heights), 1.6 * leg)
    scale = min((ROW_HEIGHT - 70) / tallest, cell / (1.4 * leg))
    ground = top + ROW_HEIGHT - 34
    _draw_ground(painter, ground, width)
    for slot, index in enumerate(indices):
        sample = positions[index]
        center = cell * (slot + 0.5)
        pelvis = sample.get("pelvis", next(iter(sample.values())))
        heading = context["headings"][index]

        def mapper(point):
            """Maps a world point to pixels.

            Args:
                point (tuple): World position.

            Returns:
                tuple: Pixel position.
            """
            horizontal, vertical = project_point(point, pelvis, heading, view)
            return center + horizontal * scale, ground - (vertical - context["floor"]) * scale

        _draw_figure(painter, sample, context["bones"], mapper, head_radius=0.11 * leg * scale)
        _draw_label(painter, _frame_text(frames[index], context["fps"]), center, ground + 22)


def _paint_travel_row(painter, positions, indices, frames, context, top, width):
    """Paints poses at their real positions along the direction of travel with fading history.

    Args:
        painter (QPainter): Active painter.
        positions (list): Role positions of the chunk.
        indices (list): Frame indices to draw.
        frames (list): Scene frame numbers of the chunk.
        context (dict): Shared leg_length, floor, fps, bones and travel.
        top (float): Row top in pixels.
        width (float): Image width in pixels.
    """
    leg = context["leg_length"]
    direction = context["travel"]["direction"] or (1.0, 0.0)
    origin = positions[indices[0]]["pelvis"]
    spans = [project_point(positions[index]["pelvis"], origin, direction, VIEW_SIDE)[0] for index in indices]
    low, high = min(spans) - leg, max(spans) + leg
    heights = [point[1] - context["floor"] for index in indices for point in positions[index].values()]
    scale = min((ROW_HEIGHT - 70) / max(max(heights), 1.6 * leg), (width - 40) / (high - low))
    ground = top + ROW_HEIGHT - 34
    _draw_ground(painter, ground, width)
    for rank, index in enumerate(indices):
        alpha = int(70 + 185 * rank / max(len(indices) - 1, 1))

        def mapper(point):
            """Maps a world point to pixels.

            Args:
                point (tuple): World position.

            Returns:
                tuple: Pixel position.
            """
            horizontal, vertical = project_point(point, origin, direction, VIEW_SIDE)
            return 20 + (horizontal - low) * scale, ground - (vertical - context["floor"]) * scale

        _draw_figure(painter, positions[index], context["bones"], mapper, alpha=alpha, line_width=4.0)
    for index in (indices[0], indices[-1]):
        pelvis_x = 20 + (project_point(positions[index]["pelvis"], origin, direction, VIEW_SIDE)[0] - low) * scale
        _draw_label(painter, _frame_text(frames[index], context["fps"]), pelvis_x, ground + 22)


def _paint_top_row(painter, positions, indices, frames, context, top, width):
    """Paints the path from above with numbered poses and heading arrows.

    Args:
        painter (QPainter): Active painter.
        positions (list): Role positions of the chunk.
        indices (list): Frame indices to draw.
        frames (list): Scene frame numbers of the chunk.
        context (dict): Shared leg_length, fps, bones and headings.
        top (float): Row top in pixels.
        width (float): Image width in pixels.
    """
    from gt.ui.qt_import import QtCore, QtGui

    leg = context["leg_length"]
    heading = context["headings"][0]
    origin = positions[0].get("pelvis") or next(iter(positions[0].values()))

    def flat(point):
        """Projects a world point onto the top-view plane.

        Args:
            point (tuple): World position.

        Returns:
            tuple: Plane coordinates in world units.
        """
        return project_point(point, origin, heading, VIEW_TOP)

    points = [flat(sample["pelvis"]) for sample in positions if "pelvis" in sample]
    pose_points = [flat(point) for index in indices for point in positions[index].values()]
    everything = points + pose_points
    minimum_x, maximum_x = min(p[0] for p in everything), max(p[0] for p in everything)
    minimum_y, maximum_y = min(p[1] for p in everything), max(p[1] for p in everything)
    span_x, span_y = max(maximum_x - minimum_x, 3 * leg), max(maximum_y - minimum_y, 1.5 * leg)
    inner_height = ROW_HEIGHT - 50
    scale = min((width - 60) / (span_x + leg), inner_height / (span_y + leg))
    center_x, center_y = (minimum_x + maximum_x) / 2, (minimum_y + maximum_y) / 2
    middle_y = top + 14 + inner_height / 2

    def mapper(point):
        """Maps a world point to pixels in the top view.

        Args:
            point (tuple): World position.

        Returns:
            tuple: Pixel position.
        """
        horizontal, vertical = flat(point)
        return width / 2 + (horizontal - center_x) * scale, middle_y - (vertical - center_y) * scale

    pen = QtGui.QPen(_qt_color(GROUND), 3, QtCore.Qt.PenStyle.DashLine)
    painter.setPen(pen)
    polygon = QtGui.QPolygonF([QtCore.QPointF(*mapper(sample["pelvis"])) for sample in positions if "pelvis" in sample])
    painter.drawPolyline(polygon)
    for rank, index in enumerate(indices):
        sample = positions[index]
        _draw_figure(painter, sample, context["bones"], mapper, alpha=200, line_width=3.0)
        pelvis = QtCore.QPointF(*mapper(sample["pelvis"]))
        ahead = context["headings"][index]
        tip = QtCore.QPointF(
            *mapper((
                sample["pelvis"][0] + ahead[0] * 0.7 * leg, sample["pelvis"][1], sample["pelvis"][2] + ahead[1] * 0.7 * leg
            ))
        )
        painter.setPen(QtGui.QPen(_qt_color(TEXT), 2))
        painter.drawLine(pelvis, tip)
        painter.setBrush(_qt_color(TEXT))
        painter.drawEllipse(tip, 4, 4)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        _draw_label(painter, f"{rank + 1}", pelvis.x(), pelvis.y() + 26, size=14)
    _draw_label(painter, "numbers = pose order, dots = facing", 12, top + ROW_HEIGHT - 8, size=12, bold=False, align_center=False)


def render_pose_sheet(positions, frames, views, fps, pose_count=6, leg_length=None, floor=None):
    """Renders one image that shows a span of animation as several skeleton poses.

    Args:
        positions (list): Role positions per frame of the span.
        frames (list): Scene frame number of each entry in positions.
        views (iterable): Views to include, from ALL_VIEWS. Travel appears only when the character moves.
        fps (float): Frames per second, used for time labels.
        pose_count (int): Poses per row.
        leg_length (float, optional): Scale override. Estimated from the positions when omitted.
        floor (float, optional): Floor height override. Estimated from the positions when omitted.

    Returns:
        QImage: Rendered sheet.
    """
    from gt.ui.qt_import import QtGui

    ensure_qt_application()
    leg = leg_length or estimate_leg_length(positions)
    ground_height = estimate_floor(positions) if floor is None else floor
    indices = select_pose_indices(positions, max(pose_count, 2), leg)
    travel = measure_travel(positions, leg)
    context = {
        "leg_length": leg, "floor": ground_height, "fps": fps, "travel": travel,
        "bones": build_bones({role for sample in positions for role in sample}),
        "headings": get_headings(positions),
    }
    rows = [view for view in ALL_VIEWS if view in set(views)]
    if VIEW_TRAVEL in rows and travel["net"] < TRAVEL_THRESHOLD:
        rows.remove(VIEW_TRAVEL)
    first_heading = context["headings"][0]
    turn = max(
        math.degrees(math.acos(max(-1.0, min(1.0, first_heading[0] * heading[0] + first_heading[1] * heading[1]))))
        for heading in context["headings"]
    )
    if len(rows) > 1 and VIEW_TOP in rows and travel["path"] < TOP_MINIMUM_PATH and turn < TOP_MINIMUM_TURN:
        rows.remove(VIEW_TOP)  # A character that stays put and faces one way gives a top view nothing to show.
    rows = rows or [VIEW_SIDE]
    width = max(1024, MINIMUM_CELL_WIDTH * len(indices))
    image = QtGui.QImage(width, ROW_HEIGHT * len(rows), QtGui.QImage.Format.Format_RGB32)
    image.fill(_qt_color(BACKGROUND))
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    try:
        for row, view in enumerate(rows):
            top = row * ROW_HEIGHT
            _draw_label(painter, VIEW_TITLES[view], 12, top + 20, size=14, align_center=False)
            if view in (VIEW_SIDE, VIEW_FRONT):
                _paint_profile_row(painter, view, positions, indices, frames, context, top, width)
            elif view == VIEW_TRAVEL:
                _paint_travel_row(painter, positions, indices, frames, context, top, width)
            else:
                _paint_top_row(painter, positions, indices, frames, context, top, width)
    finally:
        painter.end()
    return image


def save_image(image, path):
    """Saves a rendered sheet as PNG.

    Args:
        image (QImage): Image from render_pose_sheet.
        path (str or Path): Destination file.

    Returns:
        str: Saved path.
    """
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    if not image.save(str(path), "PNG"):
        raise OSError(f"Could not save the pose sheet to {path}.")
    return str(path)
