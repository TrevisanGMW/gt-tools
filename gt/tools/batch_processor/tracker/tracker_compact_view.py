"""Minimal frameless Qt view for the Batch Processor tracker."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_spinner
from gt.tools.batch_processor.tracker import tracker_tree_model


BASE_WIDTH = 380
BASE_HEIGHT = 66
BASE_MINIMUM_WIDTH = 260
BASE_ICON_SIZE = 18
BASE_BUTTON_SIZE = 24
BASE_GLYPH_SIZE = 13
BASE_BAR_HEIGHT = 22
BASE_GRIP_WIDTH = 8
BASE_CORNER_SIZE = 12
BASE_FONT_PIXELS = 13
REFERENCE_SCREEN_HEIGHT = 1080
REFERENCE_DPI = 96.0
FONT_REFERENCE_HEIGHT = 16.0
MAX_UI_SCALE = 3.0


def compute_ui_scale(widget):
    """Computes a size multiplier from DPI, screen resolution, and font size.

    Remote sessions (for example Parsec) can report a low DPI while exposing a
    high-resolution screen, so the logical screen height is used too. When Qt
    already applies device-pixel scaling, only the font and resolution terms
    matter to avoid scaling twice.

    Args:
        widget (QWidget): Widget used to find the screen and font.

    Returns:
        float: Multiplier of at least 1.0 applied to every base pixel size.
    """
    screen = widget.screen() if hasattr(widget, "screen") else None
    screen = screen or ui_qt.QtWidgets.QApplication.primaryScreen()
    scale_candidates = [1.0, widget.fontMetrics().height() / FONT_REFERENCE_HEIGHT]
    if screen:
        scale_candidates.append(screen.geometry().height() / float(REFERENCE_SCREEN_HEIGHT))
        if screen.devicePixelRatio() <= 1.01:
            scale_candidates.append(screen.logicalDotsPerInchY() / REFERENCE_DPI)
    return min(MAX_UI_SCALE, max(scale_candidates))


def get_global_point(event):
    """Gets the global cursor position across Qt5 and Qt6 mouse events.

    Args:
        event (QMouseEvent): Mouse event.

    Returns:
        QPoint: Global cursor position.
    """
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


class ElidedLabel(ui_qt.QtWidgets.QLabel):
    """Label that elides overflowing text instead of forcing the window wider."""

    def __init__(self, text="", parent=None):
        """Initializes the label.

        Args:
            text (str, optional): Initial text.
            parent (QWidget, optional): Qt parent.
        """
        super().__init__(text, parent)
        self.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        self.setMinimumWidth(40)

    def paintEvent(self, event):
        """Paints the text elided on the right.

        Args:
            event (QPaintEvent): Paint event.
        """
        painter = ui_qt.QtGui.QPainter(self)
        elided_text = self.fontMetrics().elidedText(
            self.text(),
            ui_qt.QtCore.Qt.ElideRight,
            self.width(),
        )
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(self.rect(), ui_qt.QtLib.AlignmentFlag.AlignVCenter, elided_text)


class CompactProgressBar(ui_qt.QtWidgets.QWidget):
    """Status-colored progress bar matching the tracker row style."""

    def __init__(self, parent=None):
        """Initializes the bar.

        Args:
            parent (QWidget, optional): Qt parent.
        """
        super().__init__(parent)
        self.progress = 0
        self.status = tracker_constants.Status.QUEUED
        self.setMinimumWidth(90)
        self.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Expanding,
            ui_qt.QtWidgets.QSizePolicy.Fixed,
        )

    def set_value(self, progress, status):
        """Updates the displayed progress and repaints when it changed.

        Args:
            progress (int): Percentage from 0 to 100.
            status (str): Value from ``tracker_constants.Status``.
        """
        if progress == self.progress and status == self.status:
            return
        self.progress = int(progress)
        self.status = status
        self.update()

    def paintEvent(self, event):
        """Paints the bar.

        Args:
            event (QPaintEvent): Paint event.
        """
        painter = ui_qt.QtGui.QPainter(self)
        tracker_tree_model.paint_progress_bar(painter, self.rect().adjusted(1, 1, -1, -1), self.progress, self.status)


class ResizeGrip(ui_qt.QtWidgets.QWidget):
    """Edge handle that resizes the compact window horizontally."""

    def __init__(self, target_window, is_left_edge):
        """Initializes the grip.

        Args:
            target_window (QWidget): Window resized by this handle.
            is_left_edge (bool): True for the left edge, False for the right edge.
        """
        super().__init__(target_window)
        self.target_window = target_window
        self.is_left_edge = is_left_edge
        self.press_x = 0
        self.press_width = 0
        self.press_left = 0
        self.setCursor(ui_qt.QtCore.Qt.SizeHorCursor)
        self.setToolTip("Drag to resize.")

    def mousePressEvent(self, event):
        """Stores the starting geometry.

        Args:
            event (QMouseEvent): Mouse event.
        """
        self.press_x = get_global_point(event).x()
        self.press_width = self.target_window.width()
        self.press_left = self.target_window.x()
        event.accept()

    def mouseMoveEvent(self, event):
        """Resizes the window while the handle is dragged.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if not event.buttons() & ui_qt.QtCore.Qt.LeftButton:
            return
        delta = get_global_point(event).x() - self.press_x
        minimum_width = self.target_window.minimumWidth()
        if self.is_left_edge:
            new_width = max(minimum_width, self.press_width - delta)
            new_left = self.press_left + (self.press_width - new_width)
            self.target_window.setGeometry(new_left, self.target_window.y(), new_width, self.target_window.height())
        else:
            new_width = max(minimum_width, self.press_width + delta)
            self.target_window.resize(new_width, self.target_window.height())
        event.accept()


class TrackerCompactView(ui_qt.QtWidgets.QWidget):
    """Frameless window with a custom title row and a full-width progress bar."""

    def __init__(self, project_name, parent=None):
        """Initializes the compact tracker window.

        Args:
            project_name (str): Project display name.
            parent (QWidget, optional): Qt parent.
        """
        super().__init__(parent)
        self.close_callback = None
        self.drag_offset = None
        self.ui_scale = 0.0
        self.setWindowTitle(f"Batch Processor Tracker - {project_name}")
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.batch_tracker))
        self.setWindowFlag(ui_qt.QtCore.Qt.FramelessWindowHint, True)
        self.setAttribute(ui_qt.QtCore.Qt.WA_TranslucentBackground, True)
        self._create_widgets(project_name)
        self._create_layout()
        self.apply_scale()
        self.resize(self.scale_px(BASE_WIDTH), self.scale_px(BASE_HEIGHT))

    def scale_px(self, value):
        """Scales a base pixel size by the current UI scale.

        Args:
            value (int): Base size in pixels.

        Returns:
            int: Scaled size in pixels.
        """
        return int(round(value * self.ui_scale))

    def _create_widgets(self, project_name):
        """Creates the compact widgets.

        Args:
            project_name (str): Project display name.
        """
        self.frame = ui_qt.QtWidgets.QFrame(self)
        self.frame.setObjectName("compactFrame")
        self.project_icon_label = ui_qt.QtWidgets.QLabel()
        self.name_label = ElidedLabel(project_name)
        self.name_label.setToolTip(project_name)
        self.status_icon_label = ui_qt.QtWidgets.QLabel()
        self.status_icon_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_spinner = tracker_spinner.StatusSpinner(
            self.status_icon_label, lambda: self.scale_px(BASE_ICON_SIZE)
        )
        self.minimize_button = self._create_title_button(ui_res_lib.Icon.ui_window_minimize, "Minimize.")
        self.expand_button = self._create_title_button(ui_res_lib.Icon.ui_maximize, "Expand to the full tracker.")
        self.close_button = self._create_title_button(ui_res_lib.Icon.ui_window_close, "Close the tracker.")
        self.close_button.setObjectName("closeButton")
        self.progress_bar = CompactProgressBar()
        self.left_grip = ResizeGrip(self, is_left_edge=True)
        self.right_grip = ResizeGrip(self, is_left_edge=False)
        self.corner_grip = ResizeGrip(self, is_left_edge=False)
        self.status_pixmap_path = ""

    @staticmethod
    def _create_title_button(icon_path, tooltip):
        """Creates one small title-row button.

        Args:
            icon_path (str): Icon resource path.
            tooltip (str): Hover text.

        Returns:
            QToolButton: Configured button.
        """
        button = ui_qt.QtWidgets.QToolButton()
        button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        button.setToolTip(tooltip)
        return button

    def _create_layout(self):
        """Creates the title row above a full-width progress bar."""
        outer_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.frame)
        self.content_layout = ui_qt.QtWidgets.QVBoxLayout(self.frame)
        self.title_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.title_layout.addWidget(self.project_icon_label)
        self.title_layout.addWidget(self.name_label, 1)
        self.title_layout.addWidget(self.status_icon_label)
        self.title_layout.addSpacing(2)
        self.title_layout.addWidget(self.minimize_button)
        self.title_layout.addWidget(self.expand_button)
        self.title_layout.addWidget(self.close_button)
        self.content_layout.addLayout(self.title_layout)
        self.content_layout.addWidget(self.progress_bar)

    def apply_scale(self):
        """Recomputes the UI scale and resizes every scaled element."""
        new_scale = compute_ui_scale(self)
        if abs(new_scale - self.ui_scale) < 0.01:
            return
        previous_scale = self.ui_scale
        self.ui_scale = new_scale
        icon_size = self.scale_px(BASE_ICON_SIZE)
        button_size = self.scale_px(BASE_BUTTON_SIZE)
        glyph_size = self.scale_px(BASE_GLYPH_SIZE)
        for label in (self.project_icon_label, self.status_icon_label):
            label.setFixedSize(icon_size, icon_size)
        self.project_icon_label.setPixmap(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.batch_tracker_project).pixmap(icon_size, icon_size)
        )
        for button in (self.minimize_button, self.expand_button, self.close_button):
            button.setFixedSize(button_size, button_size)
            button.setIconSize(ui_qt.QtCore.QSize(glyph_size, glyph_size))
        self.progress_bar.setFixedHeight(self.scale_px(BASE_BAR_HEIGHT))
        self.content_layout.setContentsMargins(
            self.scale_px(10), self.scale_px(6), self.scale_px(10), self.scale_px(8)
        )
        self.content_layout.setSpacing(self.scale_px(5))
        self.title_layout.setSpacing(self.scale_px(6))
        self.setFixedHeight(self.scale_px(BASE_HEIGHT))
        self.setMinimumWidth(self.scale_px(BASE_MINIMUM_WIDTH))
        self._apply_stylesheet()
        if self.status_pixmap_path and not self.status_spinner.is_active():
            self.set_status_icon(self.status_pixmap_path, self.status_icon_label.toolTip(),
                                 self.status_icon_label.accessibleName())
        if previous_scale:
            self.resize(int(self.width() * new_scale / previous_scale), self.height())

    def _apply_stylesheet(self):
        """Applies styling consistent with the full tracker, scaled to the screen."""
        radius = self.scale_px(7)
        self.setStyleSheet(
            f"QFrame#compactFrame {{ background-color: #292929; border: 1px solid #4a4a4a;"
            f" border-radius: {radius}px; }}"
            f"QLabel {{ background: transparent; color: #e0e0e0; font-weight: 600;"
            f" font-size: {self.scale_px(BASE_FONT_PIXELS)}px; }}"
            f"QToolButton {{ background-color: transparent; border: none; border-radius: {self.scale_px(4)}px; }}"
            "QToolButton:hover { background-color: #465158; }"
            "QToolButton:pressed { background-color: #55788a; }"
            "QToolButton#closeButton:hover { background-color: #a04848; }"
            "QToolTip { background-color: #444444; color: #dddddd; border: 1px solid #5a5a5a; }"
        )

    def showEvent(self, event):
        """Re-checks the scale when shown, since the window may be on another screen.

        Args:
            event (QShowEvent): Show event.
        """
        super().showEvent(event)
        self.apply_scale()

    def resizeEvent(self, event):
        """Keeps the resize handles on the left and right edges.

        Args:
            event (QResizeEvent): Resize event.
        """
        super().resizeEvent(event)
        grip_width = self.scale_px(BASE_GRIP_WIDTH)
        grip_top = self.scale_px(8)
        grip_height = max(1, self.height() - grip_top * 2)
        self.left_grip.setGeometry(0, grip_top, grip_width, grip_height)
        self.right_grip.setGeometry(self.width() - grip_width, grip_top, grip_width, grip_height)
        corner_size = self.scale_px(BASE_CORNER_SIZE)
        self.corner_grip.setGeometry(
            self.width() - corner_size, self.height() - corner_size, corner_size, corner_size
        )
        self.left_grip.raise_()
        self.right_grip.raise_()
        self.corner_grip.raise_()

    def mousePressEvent(self, event):
        """Starts dragging the window from any non-button area.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if event.button() == ui_qt.QtCore.Qt.LeftButton:
            self.drag_offset = get_global_point(event) - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Moves the window while dragging.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if self.drag_offset is not None and event.buttons() & ui_qt.QtCore.Qt.LeftButton:
            self.move(get_global_point(event) - self.drag_offset)

    def mouseReleaseEvent(self, event):
        """Ends dragging.

        Args:
            event (QMouseEvent): Mouse event.
        """
        self.drag_offset = None

    def mouseDoubleClickEvent(self, event):
        """Expands to the full tracker on double-click.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if event.button() == ui_qt.QtCore.Qt.LeftButton:
            self.expand_button.click()

    def set_project_name(self, project_name):
        """Updates the displayed project name.

        Args:
            project_name (str): Project display name.
        """
        self.name_label.setText(project_name)
        self.name_label.setToolTip(project_name)

    def set_progress(self, progress, status):
        """Updates the progress bar.

        Args:
            progress (int): Percentage from 0 to 100.
            status (str): Value from ``tracker_constants.Status``.
        """
        self.progress_bar.set_value(progress, status)

    def set_status_icon(self, icon_path, tooltip, accessible_name):
        """Updates the overall status indicator.

        Args:
            icon_path (str): Status icon resource path.
            tooltip (str): Detailed hover text.
            accessible_name (str): Screen-reader description.
        """
        self.status_pixmap_path = icon_path
        self.status_spinner.stop()
        icon_size = self.scale_px(BASE_ICON_SIZE)
        pixmap = ui_qt.QtGui.QPixmap(icon_path).scaled(
            icon_size,
            icon_size,
            ui_qt.QtCore.Qt.KeepAspectRatio,
            ui_qt.QtLib.TransformationMode.SmoothTransformation,
        )
        self.status_icon_label.setPixmap(pixmap)
        self.status_icon_label.setToolTip(tooltip)
        self.status_icon_label.setAccessibleName(accessible_name)

    def set_status_spinning(self, tooltip, accessible_name):
        """Shows the animated processing indicator instead of a static status icon.

        Args:
            tooltip (str): Detailed hover text.
            accessible_name (str): Screen-reader description.
        """
        self.status_icon_label.setToolTip(tooltip)
        self.status_icon_label.setAccessibleName(accessible_name)
        self.status_spinner.start()

    def closeEvent(self, event):
        """Delegates close requests to the controller, which owns the close flow.

        Args:
            event (QCloseEvent): Window close event.
        """
        if callable(self.close_callback):
            self.close_callback()
        event.ignore()
