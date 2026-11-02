"""Animated processing indicator drawn with Qt, used by the tracker status slots."""

import gt.ui.qt_import as ui_qt


SPINNER_INTERVAL_MS = 70
SPINNER_STEP_DEGREES = 30
SPINNER_ARC_DEGREES = 110
SPINNER_TRACK_COLOR = "#3f8f5f"
SPINNER_ARC_COLOR = "#5fd08a"


class StatusSpinner(ui_qt.QtCore.QObject):
    """Rotates a green arc inside a label while a batch is processing."""

    def __init__(self, label, size_getter):
        """Initializes the spinner without starting it.

        Args:
            label (QLabel): Label that receives the animated pixmap.
            size_getter (callable): Returns the icon edge length in pixels.
        """
        super().__init__(label)
        self.label = label
        self.size_getter = size_getter
        self.angle = 0
        self.timer = ui_qt.QtCore.QTimer(self)
        self.timer.setInterval(SPINNER_INTERVAL_MS)
        self.timer.timeout.connect(self._advance)

    def is_active(self):
        """Checks whether the animation is running.

        Returns:
            bool: True while the spinner is animating.
        """
        return self.timer.isActive()

    def start(self):
        """Starts the animation; calling it while running is a no-op."""
        if self.timer.isActive():
            return
        self._render()
        self.timer.start()

    def stop(self):
        """Stops the animation."""
        self.timer.stop()

    def _advance(self):
        """Rotates the arc one step, skipping work while the label is hidden."""
        self.angle = (self.angle - SPINNER_STEP_DEGREES) % 360
        if self.label.isVisible():
            self._render()

    def _render(self):
        """Draws the current frame into the label."""
        edge = max(8, int(self.size_getter()))
        ratio = self.label.devicePixelRatioF()
        pixmap = ui_qt.QtGui.QPixmap(int(edge * ratio), int(edge * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(ui_qt.QtCore.Qt.transparent)
        painter = ui_qt.QtGui.QPainter(pixmap)
        painter.setRenderHint(ui_qt.QtGui.QPainter.Antialiasing, True)
        pen_width = max(2.0, edge * 0.14)
        inset = pen_width / 2.0 + 1
        rectangle = ui_qt.QtCore.QRectF(inset, inset, edge - inset * 2, edge - inset * 2)
        track_color = ui_qt.QtGui.QColor(SPINNER_TRACK_COLOR)
        track_color.setAlpha(80)
        track_pen = ui_qt.QtGui.QPen(track_color, pen_width)
        painter.setPen(track_pen)
        painter.drawEllipse(rectangle)
        arc_pen = ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(SPINNER_ARC_COLOR), pen_width)
        arc_pen.setCapStyle(ui_qt.QtCore.Qt.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(rectangle, self.angle * 16, SPINNER_ARC_DEGREES * 16)
        painter.end()
        self.label.setPixmap(pixmap)
