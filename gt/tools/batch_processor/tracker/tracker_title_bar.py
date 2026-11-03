"""Custom title bar and native-like window behavior for frameless tracker windows."""

import sys

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_spinner


TITLE_BAR_COLOR = "#121212"
BORDER_COLOR = "#4a4a4a"
DRAG_START_DISTANCE = 4
MIN_TITLE_BAR_HEIGHT = 32
MIN_GRIP_SIZE = 5
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
DWMWA_BORDER_COLOR = 34
DWMWA_COLOR_NONE = 0xFFFFFFFE
SEPARATOR_COLOR = "rgba(255, 255, 255, 24)"
STATUS_ICON_SIZE = 20
WM_NCCALCSIZE = 0x0083
GWL_STYLE = -16
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
SWP_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020


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


def get_qt_edge(name):
    """Gets a ``Qt.Edge`` value across PySide2 and PySide6.

    Args:
        name (str): Edge name such as ``LeftEdge``.

    Returns:
        Qt.Edge: Edge value.
    """
    edge_enum = getattr(ui_qt.QtCore.Qt, "Edge", ui_qt.QtCore.Qt)
    return getattr(edge_enum, name)


def apply_native_window_effects(window):
    """Restores the drop shadow and rounded corners that frameless windows lose on Windows.

    Silently does nothing on other platforms or when the DWM calls fail.

    Args:
        window (QWidget): Shown top-level window.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        class Margins(ctypes.Structure):
            """Win32 MARGINS structure."""

            _fields_ = [
                ("left", ctypes.c_int),
                ("right", ctypes.c_int),
                ("top", ctypes.c_int),
                ("bottom", ctypes.c_int),
            ]

        handle = ctypes.c_void_p(int(window.winId()))
        enable_native_snapping(window)
        dwm = ctypes.windll.dwmapi
        dwm.DwmExtendFrameIntoClientArea(handle, ctypes.byref(Margins(1, 1, 1, 1)))
        dwm.DwmSetWindowAttribute(
            handle,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
            ctypes.sizeof(ctypes.c_int),
        )
        # Windows draws its own light outline on inactive windows; our frame draws the border.
        dwm.DwmSetWindowAttribute(
            handle,
            DWMWA_BORDER_COLOR,
            ctypes.byref(ctypes.c_uint(DWMWA_COLOR_NONE)),
            ctypes.sizeof(ctypes.c_uint),
        )
    except Exception:  # pragma: no cover - cosmetic only
        return


def enable_native_snapping(window):
    """Gives a frameless window the resizable-frame style Windows needs for snapping.

    The style enables Win+Arrow shortcuts and dragging to screen edges and
    corners. Handling ``WM_NCCALCSIZE`` (see ``handle_native_event``) keeps the
    frame invisible, so the custom title bar stays in charge of the look.

    Args:
        window (QWidget): Shown top-level window.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        handle = ctypes.c_void_p(int(window.winId()))
        user32.GetWindowLongW.restype = ctypes.c_long
        style = user32.GetWindowLongW(handle, GWL_STYLE)
        wanted_style = style | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
        if wanted_style != style:
            user32.SetWindowLongW(handle, GWL_STYLE, ctypes.c_long(wanted_style))
            user32.SetWindowPos(handle, None, 0, 0, 0, 0, SWP_FLAGS)
    except Exception:  # pragma: no cover - snapping is a convenience
        return


def handle_native_event(event_type, message):
    """Removes the native frame and keeps maximized windows inside the work area.

    Args:
        event_type (bytes): Qt native event type.
        message (object): Qt native message pointer.

    Returns:
        tuple: ``(handled, result)`` to return from ``nativeEvent``.
    """
    if sys.platform != "win32" or bytes(event_type) != b"windows_generic_MSG":
        return False, 0
    try:
        import ctypes
        from ctypes import wintypes

        class NcCalcSizeParams(ctypes.Structure):
            """Win32 NCCALCSIZE_PARAMS structure."""

            _fields_ = [("rgrc", wintypes.RECT * 3), ("lppos", ctypes.c_void_p)]

        class MonitorInfo(ctypes.Structure):
            """Win32 MONITORINFO structure."""

            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        native_message = wintypes.MSG.from_address(int(message))
        if native_message.message != WM_NCCALCSIZE or not native_message.wParam:
            return False, 0
        user32 = ctypes.windll.user32
        if not user32.GetWindowLongW(native_message.hWnd, GWL_STYLE) & WS_THICKFRAME:
            return False, 0
        if user32.IsZoomed(native_message.hWnd):
            params = NcCalcSizeParams.from_address(native_message.lParam)
            monitor = user32.MonitorFromWindow(native_message.hWnd, 2)
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(MonitorInfo)
            if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                params.rgrc[0] = info.rcWork
        return True, 0
    except Exception:  # pragma: no cover - fall back to Qt handling
        return False, 0


def get_native_client_margins(window):
    """Measures how far Qt's window rectangle extends past the real client area.

    A maximized window with a resizable frame overhangs the screen, and Qt keeps
    laying out against the larger window rectangle, which would crop the right
    and bottom edges of the content.

    Args:
        window (QWidget): Shown top-level window.

    Returns:
        tuple: ``(left, top, right, bottom)`` margins in pixels, all zero when
            unavailable.
    """
    if sys.platform != "win32":
        return 0, 0, 0, 0
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        handle = ctypes.c_void_p(int(window.winId()))
        window_rect = wintypes.RECT()
        client_rect = wintypes.RECT()
        client_origin = wintypes.POINT(0, 0)
        user32.GetWindowRect(handle, ctypes.byref(window_rect))
        user32.GetClientRect(handle, ctypes.byref(client_rect))
        user32.ClientToScreen(handle, ctypes.byref(client_origin))
        left = max(0, client_origin.x - window_rect.left)
        top = max(0, client_origin.y - window_rect.top)
        right = max(0, window_rect.right - (client_origin.x + client_rect.right))
        bottom = max(0, window_rect.bottom - (client_origin.y + client_rect.bottom))
        return left, top, right, bottom
    except Exception:  # pragma: no cover - cosmetic only
        return 0, 0, 0, 0


class ResizeGrip(ui_qt.QtWidgets.QWidget):
    """Invisible edge or corner handle that starts a native window resize."""

    def __init__(self, window, edge_names, cursor_shape):
        """Initializes the grip.

        Args:
            window (QWidget): Window resized by this grip.
            edge_names (tuple): ``Qt.Edge`` names resized together, such as ``("LeftEdge",)``.
            cursor_shape (Qt.CursorShape): Cursor shown while hovering.
        """
        super().__init__(window)
        self.target_window = window
        self.edge_names = edge_names
        self.setCursor(cursor_shape)

    def mousePressEvent(self, event):
        """Hands the resize to the operating system.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if event.button() != ui_qt.QtCore.Qt.LeftButton:
            return
        handle = self.target_window.windowHandle()
        if not handle:
            return
        edges = get_qt_edge(self.edge_names[0])
        for edge_name in self.edge_names[1:]:
            edges = edges | get_qt_edge(edge_name)
        handle.startSystemResize(edges)


class TitleBar(ui_qt.QtWidgets.QWidget):
    """Draggable title row with icon, title, and minimize, maximize, and close buttons."""

    def __init__(self, window):
        """Initializes the title bar.

        Args:
            window (QWidget): Window controlled by this bar.
        """
        super().__init__()
        self.target_window = window
        self.press_point = None
        self.setObjectName("trackerTitleBar")
        self._create_widgets()
        self._create_layout()
        self.apply_metrics()
        self.update_maximize_button()
        window.windowTitleChanged.connect(self.title_label.setText)
        window.windowIconChanged.connect(self._update_icon)
        self._update_icon()

    def _create_widgets(self):
        """Creates the bar widgets."""
        self.icon_label = ui_qt.QtWidgets.QLabel()
        self.title_label = ui_qt.QtWidgets.QLabel(self.target_window.windowTitle())
        for label in (self.icon_label, self.title_label):
            label.setAttribute(ui_qt.QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.status_icon_label = ui_qt.QtWidgets.QLabel()
        self.status_icon_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_icon_label.setToolTip("Starting — preparing the worker queue.")
        self.status_icon_label.setAccessibleName("Tracker status: Starting")
        self.status_spinner = tracker_spinner.StatusSpinner(self.status_icon_label, lambda: STATUS_ICON_SIZE)
        self.compact_button = self._create_button(
            ui_res_lib.Icon.ui_tracker_compact, "Switch to the compact tracker"
        )
        self.minimize_button = self._create_button(ui_res_lib.Icon.ui_window_minimize, "Minimize")
        self.maximize_button = self._create_button(ui_res_lib.Icon.ui_window_maximize, "Maximize")
        self.close_button = self._create_button(ui_res_lib.Icon.ui_window_close, "Close")
        self.close_button.setObjectName("trackerCloseButton")
        self.minimize_button.clicked.connect(self.target_window.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximized)
        self.close_button.clicked.connect(self.target_window.close)

    @staticmethod
    def _create_button(icon_path, tooltip):
        """Creates one title-bar button.

        Args:
            icon_path (str): Icon resource path.
            tooltip (str): Hover text.

        Returns:
            QToolButton: Configured button.
        """
        button = ui_qt.QtWidgets.QToolButton()
        button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        button.setToolTip(tooltip)
        button.setFocusPolicy(ui_qt.QtCore.Qt.NoFocus)
        return button

    def _create_layout(self):
        """Creates the single-row layout."""
        self.row_layout = ui_qt.QtWidgets.QHBoxLayout(self)
        self.row_layout.addWidget(self.icon_label)
        self.row_layout.addWidget(self.title_label, 1)
        self.row_layout.addWidget(self.status_icon_label)
        self.row_layout.addWidget(self.compact_button)
        self.row_layout.addWidget(self.minimize_button)
        self.row_layout.addWidget(self.maximize_button)
        self.row_layout.addWidget(self.close_button)

    def apply_metrics(self):
        """Sizes the bar from the application font so it follows the user's text scaling."""
        font_height = ui_qt.QtGui.QFontMetrics(ui_qt.QtWidgets.QApplication.font()).height()
        bar_height = max(MIN_TITLE_BAR_HEIGHT, int(font_height * 2.2))
        button_size = bar_height - 8
        icon_size = int(bar_height * 0.5)
        self.setFixedHeight(bar_height)
        self.row_layout.setContentsMargins(10, 0, 6, 0)
        self.row_layout.setSpacing(6)
        self.icon_size = icon_size
        self.status_icon_label.setFixedSize(STATUS_ICON_SIZE + 4, STATUS_ICON_SIZE + 4)
        for button in (self.compact_button, self.minimize_button, self.maximize_button, self.close_button):
            button.setFixedSize(int(button_size * 1.25), button_size)
            button.setIconSize(ui_qt.QtCore.QSize(int(icon_size * 0.8), int(icon_size * 0.8)))
        self.setStyleSheet(
            f"QWidget#trackerTitleBar {{ background-color: {TITLE_BAR_COLOR}; }}"
            "QLabel { background: transparent; color: #e0e0e0; font-weight: 600; }"
            "QToolButton { background-color: transparent; border: none; border-radius: 4px; }"
            "QToolButton:hover { background-color: #465158; }"
            "QToolButton:pressed { background-color: #55788a; }"
            "QToolButton#trackerCloseButton:hover { background-color: #a04848; }"
        )

    def set_status_icon(self, icon_path, tooltip, accessible_name):
        """Shows a static status icon and stops the processing animation.

        Args:
            icon_path (str): Status icon resource path.
            tooltip (str): Detailed hover text.
            accessible_name (str): Screen-reader description.
        """
        self.status_spinner.stop()
        pixmap = ui_qt.QtGui.QPixmap(icon_path).scaled(
            STATUS_ICON_SIZE,
            STATUS_ICON_SIZE,
            ui_qt.QtCore.Qt.KeepAspectRatio,
            ui_qt.QtLib.TransformationMode.SmoothTransformation,
        )
        self.status_icon_label.setPixmap(pixmap)
        self.status_icon_label.setToolTip(tooltip)
        self.status_icon_label.setAccessibleName(accessible_name)

    def set_status_spinning(self, tooltip, accessible_name):
        """Shows the animated processing indicator.

        Args:
            tooltip (str): Detailed hover text.
            accessible_name (str): Screen-reader description.
        """
        self.status_icon_label.setToolTip(tooltip)
        self.status_icon_label.setAccessibleName(accessible_name)
        self.status_spinner.start()

    def _update_icon(self, *args):
        """Refreshes the window icon shown at the left of the bar.

        Args:
            *args: Optional Qt signal values.
        """
        self.icon_label.setPixmap(self.target_window.windowIcon().pixmap(self.icon_size, self.icon_size))

    def update_maximize_button(self):
        """Switches the maximize button between maximize and restore."""
        maximized = self.target_window.isMaximized()
        icon_path = ui_res_lib.Icon.ui_window_restore if maximized else ui_res_lib.Icon.ui_window_maximize
        self.maximize_button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        self.maximize_button.setToolTip("Restore" if maximized else "Maximize")

    def toggle_maximized(self):
        """Maximizes the window, or restores it when already maximized."""
        if self.target_window.isMaximized():
            self.target_window.showNormal()
        else:
            self.target_window.showMaximized()

    def mousePressEvent(self, event):
        """Remembers where a drag may start.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if event.button() == ui_qt.QtCore.Qt.LeftButton:
            self.press_point = get_global_point(event)

    def mouseMoveEvent(self, event):
        """Starts a native window move once the cursor has dragged far enough.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if self.press_point is None or not event.buttons() & ui_qt.QtCore.Qt.LeftButton:
            return
        point = get_global_point(event)
        if (point - self.press_point).manhattanLength() < DRAG_START_DISTANCE:
            return
        self.press_point = None
        self._start_move(point)

    def mouseReleaseEvent(self, event):
        """Cancels a pending drag.

        Args:
            event (QMouseEvent): Mouse event.
        """
        self.press_point = None

    def mouseDoubleClickEvent(self, event):
        """Toggles maximize, like a native title bar.

        Args:
            event (QMouseEvent): Mouse event.
        """
        if event.button() == ui_qt.QtCore.Qt.LeftButton:
            self.press_point = None
            self.toggle_maximized()

    def contextMenuEvent(self, event):
        """Shows the system-style menu on right-click.

        Args:
            event (QContextMenuEvent): Context menu event.
        """
        window = self.target_window
        menu = ui_qt.QtWidgets.QMenu(self)
        restore_action = menu.addAction("Restore")
        restore_action.setEnabled(window.isMaximized() or window.isMinimized())
        minimize_action = menu.addAction("Minimize")
        maximize_action = menu.addAction("Maximize")
        maximize_action.setEnabled(not window.isMaximized())
        menu.addSeparator()
        close_action = menu.addAction("Close")
        restore_action.triggered.connect(window.showNormal)
        minimize_action.triggered.connect(window.showMinimized)
        maximize_action.triggered.connect(window.showMaximized)
        close_action.triggered.connect(window.close)
        menu.exec_(event.globalPos())

    def _start_move(self, point):
        """Starts the operating-system move so snapping and multi-monitor drags work.

        A maximized window is restored first and repositioned under the cursor.

        Args:
            point (QPoint): Global cursor position.
        """
        window = self.target_window
        if window.isMaximized():
            width_ratio = (point.x() - window.x()) / max(1, window.width())
            window.showNormal()
            window.move(point.x() - int(window.width() * width_ratio), point.y() - self.height() // 2)
        handle = window.windowHandle()
        if handle:
            handle.startSystemMove()


class FramelessWindowFrame(ui_qt.QtCore.QObject):
    """Turns a main window into a frameless window with a custom title bar.

    Adds a title bar above the central content, edge and corner resize grips,
    a border, and Windows shadow and rounded corners, and keeps them in sync
    with maximize, restore, and minimize.
    """

    GRIP_DEFINITIONS = (
        (("LeftEdge",), "SizeHorCursor"),
        (("RightEdge",), "SizeHorCursor"),
        (("TopEdge",), "SizeVerCursor"),
        (("BottomEdge",), "SizeVerCursor"),
        (("LeftEdge", "TopEdge"), "SizeFDiagCursor"),
        (("RightEdge", "BottomEdge"), "SizeFDiagCursor"),
        (("RightEdge", "TopEdge"), "SizeBDiagCursor"),
        (("LeftEdge", "BottomEdge"), "SizeBDiagCursor"),
    )

    def __init__(self, window):
        """Applies frameless flags and creates the title bar and grips.

        Args:
            window (QMainWindow): Window to restyle. Must not be shown yet.
        """
        super().__init__(window)
        self.window = window
        window.setWindowFlags(
            ui_qt.QtCore.Qt.Window
            | ui_qt.QtCore.Qt.FramelessWindowHint
            | ui_qt.QtCore.Qt.WindowMinMaxButtonsHint
            | ui_qt.QtCore.Qt.WindowSystemMenuHint
        )
        self.title_bar = TitleBar(window)
        self.frame = None
        self.grips = []
        window.installEventFilter(self)

    def wrap(self, content_widget):
        """Builds the framed container holding the title bar and the content.

        Args:
            content_widget (QWidget): Existing central content.

        Returns:
            QWidget: Container to use as the window's central widget.
        """
        self.frame = ui_qt.QtWidgets.QFrame()
        self.frame.setObjectName("trackerWindowFrame")
        frame_layout = ui_qt.QtWidgets.QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        frame_layout.addWidget(self.title_bar)
        separator = ui_qt.QtWidgets.QFrame()
        separator.setObjectName("trackerTitleSeparator")
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"QFrame#trackerTitleSeparator {{ background-color: {SEPARATOR_COLOR}; border: none; }}")
        frame_layout.addWidget(separator)
        frame_layout.addWidget(content_widget, 1)
        self._update_frame_style()
        for edge_names, cursor_name in self.GRIP_DEFINITIONS:
            cursor_enum = getattr(ui_qt.QtCore.Qt, "CursorShape", ui_qt.QtCore.Qt)
            grip = ResizeGrip(self.window, edge_names, getattr(cursor_enum, cursor_name))
            self.grips.append(grip)
        return self.frame

    def eventFilter(self, watched, event):
        """Keeps grips, border, and buttons in sync with window events.

        Args:
            watched (QObject): Watched object.
            event (QEvent): Event.

        Returns:
            bool: Always False so the event continues normally.
        """
        if watched is self.window:
            event_type = event.type()
            if event_type == ui_qt.QtCore.QEvent.Resize:
                self._position_grips()
                if self.window.isMaximized():
                    self._schedule_margin_update()
            elif event_type == ui_qt.QtCore.QEvent.WindowStateChange:
                self._on_state_changed()
            elif event_type == ui_qt.QtCore.QEvent.Show:
                apply_native_window_effects(self.window)
                self._position_grips()
                self._schedule_margin_update()
        return False

    def _on_state_changed(self):
        """Updates the maximize button, border, and grips after a state change."""
        self.title_bar.update_maximize_button()
        self._update_frame_style()
        self._position_grips()
        self._schedule_margin_update()

    def _schedule_margin_update(self):
        """Re-measures the client area once Windows has finished resizing."""
        ui_qt.QtCore.QTimer.singleShot(0, self._update_client_margins)
        ui_qt.QtCore.QTimer.singleShot(120, self._update_client_margins)

    def _update_client_margins(self):
        """Keeps content inside the real client area while maximized."""
        if not self.window.isVisible():
            return
        margins = get_native_client_margins(self.window) if self.window.isMaximized() else (0, 0, 0, 0)
        current = self.window.contentsMargins()
        if (current.left(), current.top(), current.right(), current.bottom()) != margins:
            self.window.setContentsMargins(*margins)

    def _update_frame_style(self):
        """Draws the 1 px border, except when maximized."""
        if not self.frame:
            return
        border = "none" if self.window.isMaximized() else f"1px solid {BORDER_COLOR}"
        self.frame.setStyleSheet(f"QFrame#trackerWindowFrame {{ border: {border}; }}")

    def _position_grips(self):
        """Places the resize grips on the window edges, hiding them when maximized."""
        if not self.grips:
            return
        resizable = not self.window.isMaximized() and not self.window.isFullScreen()
        font_height = ui_qt.QtGui.QFontMetrics(ui_qt.QtWidgets.QApplication.font()).height()
        size = max(MIN_GRIP_SIZE, font_height // 3)
        corner = size * 2
        width = self.window.width()
        height = self.window.height()
        geometries = (
            (0, corner, size, height - corner * 2),
            (width - size, corner, size, height - corner * 2),
            (corner, 0, width - corner * 2, size),
            (corner, height - size, width - corner * 2, size),
            (0, 0, corner, corner),
            (width - corner, height - corner, corner, corner),
            (width - corner, 0, corner, corner),
            (0, height - corner, corner, corner),
        )
        for grip, geometry in zip(self.grips, geometries):
            grip.setVisible(resizable)
            grip.setGeometry(*[max(0, value) for value in geometry])
            grip.raise_()
