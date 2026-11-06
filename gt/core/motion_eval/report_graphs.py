"""
Motion Evaluation Report Graphs - PNG graphs of what each check measured.

Chart descriptions are built with pure Python (``build_check_chart`` and
``build_summary_chart``). Rendering uses Qt's QPainter, imported lazily (the host
application's Qt wrapper when available, otherwise PySide6 or PySide2). Maya
(interactive or standalone) already provides the QGuiApplication that painting
text needs; outside Maya one is created on demand. Blender ships without Qt: check
is_qt_available() first (the runner skips graphs with a warning when it is False) and
install QT_PIP_PACKAGES with pip to enable them.

The report must be produced with ``include_series=True`` for per-check graphs;
without series only the summary image is written.
"""

from .checks_base import STATUS_DISABLED, STATUS_FAILED, STATUS_PASSED, STATUS_WARNING
from .checks_base import STATUS_SKIPPED, CHART_BELOW
import logging
import os
import re

logger = logging.getLogger(__name__)

QT_PIP_PACKAGES = ["PySide6-Essentials"]
CHART_WIDTH = 1280
CHART_HEIGHT = 460
CLIP_FACTOR = 4.0
BATCH_MAX_ROWS = 1200
SERIES_COLORS = ["#8EC5FF", "#FFC66B", "#C39BFF", "#7DE2D1", "#FF9EC7", "#BDBDBD"]
STATUS_COLORS = {
    STATUS_PASSED: "#94FF9D",
    STATUS_WARNING: "#FFD166",
    STATUS_FAILED: "#FF8A8A",
    STATUS_SKIPPED: "#888888",
    STATUS_DISABLED: "#666666",
}
COLORS = {
    "background": "#2B2B2B",
    "plot": "#232323",
    "grid": "#3A3A3A",
    "text": "#DDDDDD",
    "muted": "#9A9A9A",
    "threshold": "#FF6A6A",
    "flagged": "#FF6A6A",
    "ignored": "#777777",
}


# ------------------------------------------------ Pure Chart Data ------------------------------------------------
def safe_file_name(text):
    """Converts text into a Windows-safe file name fragment.

    Args:
        text (str): Raw text.

    Returns:
        str: Lowercase name made of letters, digits, dashes, and underscores.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text or "")).strip("_")
    return cleaned.lower() or "untitled"


def get_value_range(series_list, threshold, direction):
    """Computes the vertical range of a chart, clipping extreme spikes.

    Args:
        series_list (list): Series dictionaries with "values".
        threshold (float or None): Threshold drawn on the chart.
        direction (str): CHART_ABOVE or CHART_BELOW.

    Returns:
        tuple: (minimum, maximum, clipped) where clipped is True when spikes go past the range.
    """
    values = [value for series in series_list for value in series["values"] if value is not None]
    if threshold is not None:
        values.append(threshold)
    if not values:
        return 0.0, 1.0, False
    minimum = min(values + [0.0])
    maximum = max(values + [0.0])
    clipped = False
    if threshold is not None and threshold > 0 and direction != CHART_BELOW and maximum > threshold * CLIP_FACTOR:
        maximum = threshold * CLIP_FACTOR
        clipped = True
    if maximum - minimum < 1e-12:
        maximum = minimum + 1.0
    padding = (maximum - minimum) * 0.06
    return minimum - (padding if minimum < 0 else 0.0), maximum + padding, clipped


def build_check_chart(report, entry):
    """Describes the graph for one check entry.

    Args:
        report (dict): Evaluation report.
        entry (dict): Check entry that contains a "chart" payload.

    Returns:
        dict or None: Chart description, or None when the entry has no series.
    """
    chart = entry.get("chart") or {}
    series_list = chart.get("series") or []
    if not series_list:
        return None
    start_frame = int((report.get("frame_range") or [0, 0])[0])
    frame_count = max(len(series["values"]) for series in series_list)
    threshold = chart.get("threshold")
    direction = chart.get("direction")
    minimum, maximum, clipped = get_value_range(series_list, threshold, direction)
    score = entry.get("score")
    score_text = "skipped" if score is None else f"{score}/100"
    subtitle = f"{report.get('scene') or ''}  |  Score {score_text} ({entry.get('status')})  |  " \
               f"{entry.get('flagged_frames', 0)} flagged frame(s), {entry.get('events', 0)} event(s)"
    if clipped:
        subtitle += f"  |  values above {CLIP_FACTOR:g}x the threshold are clipped"
    return {
        "title": entry.get("label") or entry.get("key", ""),
        "subtitle": subtitle.strip(" |"),
        "status": entry.get("status"),
        "unit": chart.get("unit") or "",
        "start_frame": start_frame,
        "frame_count": frame_count,
        "series": [
            {"label": series["label"], "values": series["values"], "color": SERIES_COLORS[index % len(SERIES_COLORS)]}
            for index, series in enumerate(series_list)
        ],
        "threshold": threshold,
        "threshold_label": chart.get("threshold_label") or "",
        "direction": direction,
        "minimum": minimum,
        "maximum": maximum,
        "spans": [list(span) for span in entry.get("spans") or []],
        "ignored": [list(span) for span in report.get("ignored_ranges") or []],
    }


def build_summary_chart(report):
    """Describes the summary graph: score per check and flagged frames over time.

    Args:
        report (dict): Evaluation report.

    Returns:
        dict: Summary description.
    """
    frame_range = report.get("frame_range") or [0, 0]
    rows = []
    for entry in report.get("checks") or []:
        if entry.get("status") == STATUS_DISABLED:
            continue
        rows.append(
            {
                "label": entry.get("label") or entry.get("key", ""),
                "score": entry.get("score"),
                "status": entry.get("status"),
                "spans": [list(span) for span in entry.get("spans") or []],
            }
        )
    return {
        "title": f"{report.get('scene') or 'Animation'} - Score {report.get('score')}/100 ({report.get('status')})",
        "subtitle": f"{report.get('mode_label')} mode  |  Skeleton: {report.get('template') or '-'}  |  "
                    f"Frames {frame_range[0]}-{frame_range[1]} @ {report.get('fps')} fps",
        "status": report.get("status"),
        "start_frame": int(frame_range[0]),
        "end_frame": int(frame_range[1]),
        "rows": rows,
        "ignored": [list(span) for span in report.get("ignored_ranges") or []],
    }


def get_graph_entries(report, only_issues=False):
    """Lists the check entries that get their own graph.

    Args:
        report (dict): Evaluation report.
        only_issues (bool): Keep only checks with a warning or failed status.

    Returns:
        list: Check entries with chart data.
    """
    entries = []
    for entry in report.get("checks") or []:
        if not entry.get("chart"):
            continue
        if only_issues and entry.get("status") not in (STATUS_WARNING, STATUS_FAILED):
            continue
        entries.append(entry)
    return entries


# ------------------------------------------------ Qt Rendering ------------------------------------------------
class QtModules:
    """Holds the QtCore, QtGui, and QtWidgets modules used for painting."""

    def __init__(self, qt_core, qt_gui, qt_widgets):
        """Stores the modules.

        Args:
            qt_core (module): QtCore.
            qt_gui (module): QtGui.
            qt_widgets (module): QtWidgets.
        """
        self.QtCore = qt_core
        self.QtGui = qt_gui
        self.QtWidgets = qt_widgets


def get_qt():
    """Imports Qt lazily: PySide6 (Maya 2025 and newer), otherwise PySide2.

    Returns:
        object: Object exposing QtCore, QtGui, and QtWidgets.

    Raises:
        ImportError: If no Qt binding is available.
    """
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError:
        from PySide2 import QtCore, QtGui, QtWidgets
    return QtModules(QtCore, QtGui, QtWidgets)


def is_qt_available():
    """Checks whether a Qt binding (PySide6 or PySide2) can draw graphs in this Python.

    Maya always has one; Blender and plain Python need it installed with pip
    (see QT_PIP_PACKAGES and SceneHost.build_pip_install_command).

    Returns:
        bool: True when graphs can be written.
    """
    import importlib.util

    for package in ("PySide6", "PySide2"):
        try:
            if importlib.util.find_spec(package) is not None:
                return True
        except (ImportError, ValueError):
            continue
    return False


def ensure_gui_application():
    """Makes sure a Qt GUI application exists so text can be painted.

    Returns:
        object: The Qt application instance.
    """
    ui_qt = get_qt()
    application = ui_qt.QtGui.QGuiApplication.instance()
    if application is None:
        application = ui_qt.QtWidgets.QApplication([])
    return application


class ChartPainter:
    """Paints chart descriptions into QImages."""

    def __init__(self, width=CHART_WIDTH, height=CHART_HEIGHT):
        """Creates an image and a painter.

        Args:
            width (int): Image width in pixels.
            height (int): Image height in pixels.
        """
        ui_qt = get_qt()
        ensure_gui_application()
        self.qt = ui_qt
        self.width = width
        self.height = height
        self.image = ui_qt.QtGui.QImage(width, height, ui_qt.QtGui.QImage.Format.Format_ARGB32)
        self.image.fill(ui_qt.QtGui.QColor(COLORS["background"]))
        self.painter = ui_qt.QtGui.QPainter(self.image)
        self.painter.setRenderHint(ui_qt.QtGui.QPainter.RenderHint.Antialiasing, True)

    def color(self, value, alpha=255):
        """Creates a QColor.

        Args:
            value (str): Hex color.
            alpha (int): Opacity 0-255.

        Returns:
            QColor: Color.
        """
        color = self.qt.QtGui.QColor(value)
        color.setAlpha(alpha)
        return color

    def set_pen(self, color, width=1.0, dashed=False, alpha=255):
        """Sets the painter pen.

        Args:
            color (str): Hex color.
            width (float): Line width.
            dashed (bool): Draw a dashed line.
            alpha (int): Opacity 0-255.
        """
        pen = self.qt.QtGui.QPen(self.color(color, alpha))
        pen.setWidthF(width)
        if dashed:
            pen.setStyle(self.qt.QtCore.Qt.PenStyle.DashLine)
        self.painter.setPen(pen)

    def text(self, x_position, y_position, text, color=None, size=11, bold=False, align_right=False):
        """Draws text with its baseline at the given point.

        Args:
            x_position (float): Left (or right when align_right) position.
            y_position (float): Baseline position.
            text (str): Text.
            color (str, optional): Hex color.
            size (int): Point size.
            bold (bool): Bold font.
            align_right (bool): Treat x_position as the right edge.
        """
        font = self.qt.QtGui.QFont()
        font.setPointSize(size)
        font.setBold(bold)
        self.painter.setFont(font)
        self.set_pen(color or COLORS["text"])
        if align_right:
            x_position -= self.qt.QtGui.QFontMetrics(font).horizontalAdvance(text)
        self.painter.drawText(self.qt.QtCore.QPointF(x_position, y_position), text)

    def fill_rect(self, left, top, width, height, color, alpha=255):
        """Fills a rectangle.

        Args:
            left (float): Left edge.
            top (float): Top edge.
            width (float): Width.
            height (float): Height.
            color (str): Hex color.
            alpha (int): Opacity 0-255.
        """
        self.painter.fillRect(self.qt.QtCore.QRectF(left, top, width, height), self.color(color, alpha))

    def rotated_text(self, x_position, y_position, text, angle, color=None, size=9):
        """Draws text rotated around its baseline start point.

        Args:
            x_position (float): Anchor x.
            y_position (float): Anchor y (baseline).
            text (str): Text.
            angle (float): Rotation in degrees (negative turns counter-clockwise).
            color (str, optional): Hex color.
            size (int): Point size.
        """
        self.painter.save()
        self.painter.translate(x_position, y_position)
        self.painter.rotate(angle)
        self.text(0, 0, text, color=color, size=size)
        self.painter.restore()

    def line(self, start_x, start_y, end_x, end_y):
        """Draws a line with the current pen.

        Args:
            start_x (float): Start x.
            start_y (float): Start y.
            end_x (float): End x.
            end_y (float): End y.
        """
        self.painter.drawLine(self.qt.QtCore.QPointF(start_x, start_y), self.qt.QtCore.QPointF(end_x, end_y))

    def polyline(self, points):
        """Draws connected points with the current pen.

        Args:
            points (list): (x, y) tuples.
        """
        if len(points) == 1:
            self.painter.drawPoint(self.qt.QtCore.QPointF(*points[0]))
            return
        polygon = self.qt.QtGui.QPolygonF([self.qt.QtCore.QPointF(x_value, y_value) for x_value, y_value in points])
        self.painter.drawPolyline(polygon)

    def save(self, file_path):
        """Finishes painting and saves the image.

        Args:
            file_path (str): Output PNG path.

        Returns:
            bool: True when the image was written.
        """
        self.painter.end()
        return bool(self.image.save(file_path, "PNG"))


def format_axis_value(value):
    """Formats an axis tick value compactly.

    Args:
        value (float): Tick value.

    Returns:
        str: Readable value.
    """
    magnitude = abs(value)
    if magnitude >= 1000:
        return f"{value:.0f}"
    if magnitude >= 10:
        return f"{value:.1f}"
    if magnitude >= 0.1 or magnitude == 0:
        return f"{value:.2f}"
    return f"{value:.2g}"


def draw_frame_spans(canvas, spans, plot, frame_to_x, color, alpha):
    """Shades frame spans across the plot height.

    Args:
        canvas (ChartPainter): Painter.
        spans (list): Inclusive [start, end] frame spans.
        plot (tuple): (left, top, width, height) plot rectangle.
        frame_to_x (callable): Converts a frame number to an x position.
        color (str): Hex color.
        alpha (int): Opacity 0-255.
    """
    left, top, width, height = plot
    for start, end in spans:
        span_left = max(left, frame_to_x(start - 0.5))
        span_right = min(left + width, frame_to_x(end + 0.5))
        if span_right > span_left:
            canvas.fill_rect(span_left, top, max(1.0, span_right - span_left), height, color, alpha)


def draw_frame_axis(canvas, plot, start_frame, end_frame, frame_to_x):
    """Draws vertical frame grid lines with labels under the plot.

    Args:
        canvas (ChartPainter): Painter.
        plot (tuple): (left, top, width, height) plot rectangle.
        start_frame (int): First frame.
        end_frame (int): Last frame.
        frame_to_x (callable): Converts a frame number to an x position.
    """
    left, top, width, height = plot
    span = max(1, end_frame - start_frame)
    step = 1
    for candidate in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000):
        step = candidate
        if span / candidate <= 12:
            break
    first_tick = start_frame + (-start_frame % step)
    for frame in range(first_tick, end_frame + 1, step):
        x_position = frame_to_x(frame)
        canvas.set_pen(COLORS["grid"])
        canvas.line(x_position, top, x_position, top + height)
        canvas.text(x_position - 10, top + height + 18, str(frame), COLORS["muted"], size=9)


def render_check_chart(chart, file_path):
    """Renders a check chart to a PNG file.

    Args:
        chart (dict): Description from build_check_chart.
        file_path (str): Output PNG path.

    Returns:
        bool: True when the image was written.
    """
    canvas = ChartPainter()
    plot = (90.0, 92.0, canvas.width - 120.0, canvas.height - 160.0)
    left, top, width, height = plot
    start_frame = chart["start_frame"]
    end_frame = start_frame + max(1, chart["frame_count"] - 1)
    minimum, maximum = chart["minimum"], chart["maximum"]

    def frame_to_x(frame):
        """Converts a frame number to an x position.

        Args:
            frame (float): Frame number.

        Returns:
            float: X position in pixels.
        """
        return left + (frame - start_frame) / float(max(1, end_frame - start_frame)) * width

    def value_to_y(value):
        """Converts a value to a y position, clamped to the plot.

        Args:
            value (float): Series value.

        Returns:
            float: Y position in pixels.
        """
        ratio = (value - minimum) / float(maximum - minimum)
        return top + height - max(0.0, min(1.0, ratio)) * height

    canvas.text(left, 34, chart["title"], size=16, bold=True, color=STATUS_COLORS.get(chart["status"]))
    canvas.text(left, 58, chart["subtitle"], COLORS["muted"], size=10)
    canvas.fill_rect(left, top, width, height, COLORS["plot"])
    draw_frame_spans(canvas, chart["ignored"], plot, frame_to_x, COLORS["ignored"], 70)
    draw_frame_spans(canvas, chart["spans"], plot, frame_to_x, COLORS["flagged"], 70)
    for tick in range(5):
        value = minimum + (maximum - minimum) * tick / 4.0
        y_position = value_to_y(value)
        canvas.set_pen(COLORS["grid"])
        canvas.line(left, y_position, left + width, y_position)
        canvas.text(left - 8, y_position + 4, format_axis_value(value), COLORS["muted"], size=9, align_right=True)
    draw_frame_axis(canvas, plot, start_frame, end_frame, frame_to_x)
    if minimum < 0 < maximum:
        canvas.set_pen(COLORS["muted"], 1.0)
        canvas.line(left, value_to_y(0.0), left + width, value_to_y(0.0))
    for series in chart["series"]:
        canvas.set_pen(series["color"], 1.8)
        segment = []
        for index, value in enumerate(series["values"]):
            if value is None:
                if segment:
                    canvas.polyline(segment)
                segment = []
                continue
            segment.append((frame_to_x(start_frame + index), value_to_y(value)))
        if segment:
            canvas.polyline(segment)
    if chart["threshold"] is not None:
        y_position = value_to_y(chart["threshold"])
        canvas.set_pen(COLORS["threshold"], 1.6, dashed=True)
        canvas.line(left, y_position, left + width, y_position)
        bad_side = "below" if chart["direction"] == CHART_BELOW else "above"
        label = f"{chart['threshold_label']} = {format_axis_value(chart['threshold'])} (flag {bad_side})"
        canvas.text(left + width - 6, y_position - 6, label, COLORS["threshold"], size=9, align_right=True)
    canvas.text(left, top + height + 40, f"Frame  |  Y: {chart['unit']}", COLORS["muted"], size=9)
    legend_x = left + width
    legend_items = [(series["label"], series["color"]) for series in chart["series"]]
    legend_items.append(("flagged frames", COLORS["flagged"]))
    for label, color in reversed(legend_items):
        font_width = len(label) * 7 + 30
        legend_x -= font_width
        canvas.fill_rect(legend_x, top + height + 30, 14, 10, color)
        canvas.text(legend_x + 18, top + height + 40, label, COLORS["text"], size=9)
    return canvas.save(file_path)


def render_summary_chart(summary, file_path):
    """Renders the summary chart to a PNG file.

    Args:
        summary (dict): Description from build_summary_chart.
        file_path (str): Output PNG path.

    Returns:
        bool: True when the image was written.
    """
    row_height = 26
    rows = summary["rows"]
    height = int(130 + max(1, len(rows)) * row_height + 50)
    canvas = ChartPainter(CHART_WIDTH, height)
    label_width = 210.0
    bar_width = 220.0
    timeline_left = 40.0 + label_width + bar_width + 30.0
    timeline_width = canvas.width - timeline_left - 30.0
    top = 100.0
    start_frame, end_frame = summary["start_frame"], max(summary["start_frame"] + 1, summary["end_frame"])

    def frame_to_x(frame):
        """Converts a frame number to an x position on the timeline.

        Args:
            frame (float): Frame number.

        Returns:
            float: X position in pixels.
        """
        return timeline_left + (frame - start_frame) / float(end_frame - start_frame) * timeline_width

    canvas.text(40, 36, summary["title"], size=16, bold=True, color=STATUS_COLORS.get(summary["status"]))
    canvas.text(40, 60, summary["subtitle"], COLORS["muted"], size=10)
    canvas.text(40 + label_width, top - 10, "Score", COLORS["muted"], size=9)
    canvas.text(timeline_left, top - 10, "Flagged frames", COLORS["muted"], size=9)
    timeline_plot = (timeline_left, top, timeline_width, len(rows) * row_height)
    canvas.fill_rect(*timeline_plot, color=COLORS["plot"])
    draw_frame_spans(canvas, summary["ignored"], timeline_plot, frame_to_x, COLORS["ignored"], 70)
    draw_frame_axis(canvas, timeline_plot, start_frame, end_frame, frame_to_x)
    for row_index, row in enumerate(rows):
        row_top = top + row_index * row_height
        color = STATUS_COLORS.get(row["status"], COLORS["text"])
        canvas.text(40, row_top + 18, row["label"], COLORS["text"], size=10)
        canvas.fill_rect(40 + label_width, row_top + 6, bar_width, row_height - 12, COLORS["plot"])
        if row["score"] is not None:
            canvas.fill_rect(40 + label_width, row_top + 6, bar_width * row["score"] / 100.0, row_height - 12, color)
        score_text = "skipped" if row["score"] is None else str(row["score"])
        canvas.text(40 + label_width + bar_width + 6, row_top + 18, score_text, color, size=9)
        for start, end in row["spans"]:
            span_left = frame_to_x(start - 0.5)
            span_right = frame_to_x(end + 0.5)
            canvas.fill_rect(span_left, row_top + 5, max(2.0, span_right - span_left), row_height - 10, color, 220)
    return canvas.save(file_path)


# ------------------------------------------------ Export ------------------------------------------------
def export_report_graphs(report, directory, file_prefix="", only_issues=False):
    """Writes the summary graph and one graph per check into a folder.

    Args:
        report (dict): Evaluation report (with series for per-check graphs).
        directory (str): Output folder. Created when missing.
        file_prefix (str): Prefix for every file name, for example the scene name.
        only_issues (bool): Only graph checks with a warning or failed status.

    Returns:
        list: Written file paths.
    """
    os.makedirs(directory, exist_ok=True)
    prefix = f"{safe_file_name(file_prefix)}_" if file_prefix else ""
    written = []
    summary_path = os.path.join(directory, f"{prefix}00_summary.png")
    if render_summary_chart(build_summary_chart(report), summary_path):
        written.append(summary_path)
    else:
        logger.warning(f"Unable to write {summary_path}")
    for index, entry in enumerate(get_graph_entries(report, only_issues=only_issues), start=1):
        chart = build_check_chart(report, entry)
        if not chart:
            continue
        file_path = os.path.join(directory, f"{prefix}{index:02d}_{safe_file_name(entry.get('key'))}.png")
        if render_check_chart(chart, file_path):
            written.append(file_path)
        else:
            logger.warning(f"Unable to write {file_path}")
    return written


# ------------------------------------------------ Batch ------------------------------------------------
def shorten_text(text, maximum_length):
    """Shortens text with an ellipsis in the middle.

    Args:
        text (str): Text.
        maximum_length (int): Maximum number of characters.

    Returns:
        str: Text no longer than maximum_length.
    """
    text = str(text or "")
    if len(text) <= maximum_length:
        return text
    half = max(1, (maximum_length - 3) // 2)
    return f"{text[:half]}...{text[-half:]}"


def render_batch_chart(chart, file_path):
    """Renders the batch chart (one row per file, one status cell per check) to a PNG file.

    Args:
        chart (dict): Description from batch_summary.build_batch_chart.
        file_path (str): Output PNG path.

    Returns:
        bool: True when the image was written.
    """
    rows = chart["rows"][:BATCH_MAX_ROWS]
    hidden_count = len(chart["rows"]) - len(rows)
    columns = chart["columns"]
    row_height = 22
    cell_width = 30
    label_width = 300.0
    bar_width = 160.0
    left = 40.0
    cells_left = left + label_width + bar_width + 50.0
    header_top = 90.0
    header_height = 150.0
    top = header_top + header_height
    width = int(max(900, cells_left + len(columns) * cell_width + 60))
    height = int(top + max(1, len(rows)) * row_height + (70 if hidden_count else 40))
    canvas = ChartPainter(width, height)
    canvas.text(left, 36, chart["title"], size=16, bold=True)
    canvas.text(left, 60, chart["subtitle"], COLORS["muted"], size=10)
    canvas.text(left, top - 10, "File", COLORS["muted"], size=9)
    canvas.text(left + label_width, top - 10, "Score", COLORS["muted"], size=9)
    for column_index, label in enumerate(columns):
        anchor_x = cells_left + column_index * cell_width + cell_width * 0.6
        canvas.rotated_text(anchor_x, top - 8, label, -60, COLORS["text"], size=9)
    canvas.fill_rect(cells_left, top, len(columns) * cell_width, len(rows) * row_height, COLORS["plot"])
    for row_index, row in enumerate(rows):
        row_top = top + row_index * row_height
        if row_index % 2:
            canvas.fill_rect(left, row_top, cells_left - left + len(columns) * cell_width, row_height,
                             COLORS["grid"], 70)
        color = STATUS_COLORS.get(row["status"], COLORS["text"])
        canvas.text(left, row_top + 15, shorten_text(row["label"], 44), COLORS["text"], size=9)
        canvas.fill_rect(left + label_width, row_top + 5, bar_width, row_height - 10, COLORS["plot"])
        if row["score"] is not None:
            canvas.fill_rect(left + label_width, row_top + 5, bar_width * row["score"] / 100.0, row_height - 10, color)
        score_text = "-" if row["score"] is None else str(row["score"])
        canvas.text(left + label_width + bar_width + 6, row_top + 15, score_text, color, size=9)
        for column_index, status in enumerate(row["cells"]):
            if not status:
                continue
            cell_color = STATUS_COLORS.get(status, COLORS["muted"])
            alpha = 90 if status == STATUS_PASSED else 230
            canvas.fill_rect(cells_left + column_index * cell_width + 2, row_top + 3, cell_width - 4,
                             row_height - 6, cell_color, alpha)
    if hidden_count:
        canvas.text(left, top + len(rows) * row_height + 30,
                    f"{hidden_count} more file(s) with higher scores are not shown; see the batch summary.",
                    COLORS["muted"], size=10)
    return canvas.save(file_path)
