"""Switches the tracker between full and compact windows and manages the tray icon."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_constants


TRAY_ICON_SIZES = (16, 20, 24, 28, 32, 40, 48, 64, 96, 128)
TILE_BORDER_RATIO = 0.07
TILE_RADIUS_RATIO = 0.24
BAR_HEIGHT_RATIO = 0.17
DIGIT_WIDTH_RATIO = 0.96
DIGIT_HEIGHT_RATIO = 0.92
MIN_BADGE_FONT_PIXELS = 5


class TrackerWindowManager:
    """Owns which tracker window is shown and the optional system tray icon."""

    def __init__(self, view, compact_view, abort_callback=None, allow_tray=True):
        """Initializes the manager without showing anything.

        Args:
            view (TrackerView): Full tracker window.
            compact_view (TrackerCompactView): Compact tracker window.
            abort_callback (callable, optional): Called by the tray "Abort All" action.
            allow_tray (bool, optional): False disables tray support entirely,
                for example in a preview window hosted by another application.
        """
        self.view = view
        self.compact_view = compact_view
        self.abort_callback = abort_callback
        self.allow_tray = allow_tray
        self.compact_active = False
        self.tray_enabled = False
        self.tray_icon = None
        self.tray_menu = None
        self.toggle_visibility_action = None
        self.switch_mode_action = None
        self.abort_action = None
        self.badge_key = None
        self.taskbar_anchor = None
        self.last_compact_position = None
        self.view.minimize_to_tray_callback = None

    @staticmethod
    def is_tray_available():
        """Checks whether the OS offers a system tray.

        Returns:
            bool: True when a tray icon can be shown.
        """
        return ui_qt.QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()

    def get_active_window(self):
        """Gets the window matching the current mode.

        Returns:
            QWidget: Compact window when compact is active, otherwise the full window.
        """
        return self.compact_view if self.compact_active else self.view

    def show_initial(self, compact, minimized=False):
        """Shows the first window, or leaves it minimized.

        A minimized launch stays hidden behind the tray icon when a tray exists,
        otherwise it opens minimized on the taskbar.

        Args:
            compact (bool): True to start with the compact window.
            minimized (bool, optional): True to start minimized.
        """
        self.compact_active = bool(compact)
        window = self.get_active_window()
        if not minimized:
            window.show()
        elif not self.tray_enabled:
            window.showMinimized()

    def set_compact(self, compact):
        """Swaps between the compact and full windows.

        Going compact restores the last compact position (or the full window's
        position the first time). Going full centers the window on the screen
        the compact window was on, like a fresh launch.

        Args:
            compact (bool): True for the compact window, False for the full window.
        """
        compact = bool(compact)
        if compact == self.compact_active:
            return
        previous_window = self.get_active_window()
        was_visible = previous_window.isVisible()
        screen = self._get_window_screen(previous_window)
        if not compact:
            self.last_compact_position = previous_window.pos()
        position = self.last_compact_position if compact and self.last_compact_position else previous_window.pos()
        self.compact_active = compact
        previous_window.hide()
        next_window = self.get_active_window()
        if compact:
            next_window.move(position)
        else:
            self._center_on_screen(next_window, screen)
        if was_visible:
            self.show_window(next_window)
        self._refresh_tray_actions()

    @staticmethod
    def _get_window_screen(window):
        """Gets the screen currently holding a window.

        Args:
            window (QWidget): Tracker window.

        Returns:
            QScreen: Screen under the window center, or the primary screen.
        """
        application = ui_qt.QtWidgets.QApplication
        screen = application.screenAt(window.frameGeometry().center())
        return screen or application.primaryScreen()

    @staticmethod
    def _center_on_screen(window, screen):
        """Centers a window inside a screen's available area.

        Args:
            window (QWidget): Window to place.
            screen (QScreen): Target screen.
        """
        available = screen.availableGeometry()
        width = min(window.width(), available.width())
        height = min(window.height(), available.height())
        window.resize(width, height)
        window.move(
            available.left() + (available.width() - width) // 2,
            available.top() + (available.height() - height) // 2,
        )

    @staticmethod
    def show_window(window):
        """Shows, un-minimizes, and focuses a window.

        Args:
            window (QWidget): Window to bring forward.
        """
        window.setWindowState(window.windowState() & ~ui_qt.QtCore.Qt.WindowMinimized)
        window.show()
        window.raise_()
        window.activateWindow()

    def set_tray_enabled(self, enabled):
        """Shows the tray icon and keeps tracker windows off the taskbar, or reverts.

        Windows stay regular windows (with minimize, maximize and close buttons).
        Giving them a hidden owner window removes their taskbar button. Falls
        back to regular taskbar windows when no system tray exists.

        Args:
            enabled (bool): Requested tray mode.
        """
        enabled = bool(enabled) and self.allow_tray and self.is_tray_available()
        if enabled == self.tray_enabled:
            return
        self.tray_enabled = enabled
        if enabled:
            self._create_tray_icon()
            self.tray_icon.show()
        elif self.tray_icon:
            self.tray_icon.hide()
        for window in (self.view, self.compact_view):
            self._apply_taskbar_owner(window, enabled)
        self.view.minimize_to_tray_callback = self.minimize_active if enabled else None

    def _apply_taskbar_owner(self, window, hidden_from_taskbar):
        """Parents a window to a never-shown owner, or detaches it again.

        Args:
            window (QWidget): Tracker window.
            hidden_from_taskbar (bool): True to keep the window off the taskbar.
        """
        was_visible = window.isVisible()
        position = window.pos()
        if hidden_from_taskbar and self.taskbar_anchor is None:
            self.taskbar_anchor = ui_qt.QtWidgets.QWidget()
            self.taskbar_anchor.setWindowFlag(ui_qt.QtCore.Qt.Tool, True)
            self.taskbar_anchor.winId()
        window.setParent(self.taskbar_anchor if hidden_from_taskbar else None, window.windowFlags())
        window.move(position)
        if was_visible:
            window.show()

    def _create_tray_icon(self):
        """Creates the tray icon and its menu once."""
        if self.tray_icon:
            return
        self.tray_icon = ui_qt.QtWidgets.QSystemTrayIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.batch_tracker), self.view
        )
        self.tray_icon.setToolTip(self.view.windowTitle())
        self.tray_menu = ui_qt.QtWidgets.QMenu()
        self.toggle_visibility_action = self.tray_menu.addAction("Show / Hide Tracker")
        self.toggle_visibility_action.triggered.connect(self.toggle_visibility)
        self.switch_mode_action = self.tray_menu.addAction("Switch to Compact Tracker")
        self.switch_mode_action.triggered.connect(self._toggle_compact)
        self.tray_menu.addSeparator()
        self.abort_action = self.tray_menu.addAction("Abort All")
        self.abort_action.triggered.connect(self._request_abort)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self._refresh_tray_actions()

    def _refresh_tray_actions(self):
        """Keeps the tray mode action text in sync with the active window."""
        if self.switch_mode_action:
            self.switch_mode_action.setText(
                "Switch to Full Tracker" if self.compact_active else "Switch to Compact Tracker"
            )

    def _toggle_compact(self):
        """Switches between compact and full windows from the tray menu."""
        self.set_compact(not self.compact_active)
        self.show_window(self.get_active_window())

    def _request_abort(self):
        """Forwards the tray abort action to the controller."""
        if callable(self.abort_callback):
            self.abort_callback()

    def _on_tray_activated(self, reason):
        """Toggles the tracker when the tray icon is double-clicked; single clicks are ignored.

        Args:
            reason (QSystemTrayIcon.ActivationReason): Activation type.
        """
        reasons = ui_qt.QtWidgets.QSystemTrayIcon
        double_click = getattr(reasons, "DoubleClick", None) or reasons.ActivationReason.DoubleClick
        if reason == double_click:
            self.toggle_visibility()

    def toggle_visibility(self):
        """Hides the active window if visible, otherwise brings it forward."""
        window = self.get_active_window()
        if window.isVisible() and not window.isMinimized():
            window.hide()
            return
        self.show_window(window)

    def minimize_active(self, window=None):
        """Minimizes a window to the tray, or to the taskbar when the tray is off.

        Minimizing never closes anything; the window stays alive and can be
        restored from the tray icon or the taskbar.

        Args:
            window (QWidget, optional): Window to minimize. Defaults to the active one.
        """
        window = window or self.get_active_window()
        if self.tray_enabled:
            window.setWindowState(window.windowState() & ~ui_qt.QtCore.Qt.WindowMinimized)
            window.hide()
        else:
            window.showMinimized()

    def set_progress_badge(self, progress, health_state):
        """Redraws the tray icon as a progress tile showing the percentage.

        Args:
            progress (int): Percentage from 0 to 100.
            health_state (str): Value from ``tracker_constants.HealthState``.
        """
        if not self.tray_icon:
            return
        badge_key = (int(progress), health_state)
        if badge_key == self.badge_key:
            return
        self.badge_key = badge_key
        accent = tracker_constants.TRAY_BADGE_COLORS.get(health_state, tracker_constants.TRAY_BADGE_DEFAULT_COLOR)
        self.tray_icon.setIcon(self._build_badge_icon(int(progress), accent))

    @staticmethod
    def _build_badge_icon(progress, accent_color):
        """Builds the tray icon at several sizes so every tray slot gets a crisp one.

        Args:
            progress (int): Percentage from 0 to 100.
            accent_color (str): Status color for the border and progress bar.

        Returns:
            QIcon: Tray icon.
        """
        icon = ui_qt.QtGui.QIcon()
        for size in TRAY_ICON_SIZES:
            icon.addPixmap(TrackerWindowManager._build_badge_pixmap(size, progress, accent_color))
        return icon

    @staticmethod
    def _build_badge_pixmap(size, progress, accent_color):
        """Draws one tray icon size: dark tile, big digits, and a progress bar underneath.

        The pixmap is created at exactly ``size`` device pixels with a device
        pixel ratio of 1, so it does not depend on the screen scaling.

        Args:
            size (int): Edge length in pixels.
            progress (int): Percentage from 0 to 100.
            accent_color (str): Status color for the border and progress bar.

        Returns:
            QPixmap: Icon pixmap.
        """
        pixmap = ui_qt.QtGui.QPixmap(size, size)
        pixmap.setDevicePixelRatio(1.0)
        pixmap.fill(ui_qt.QtCore.Qt.transparent)
        painter = ui_qt.QtGui.QPainter(pixmap)
        painter.setRenderHint(ui_qt.QtGui.QPainter.Antialiasing, True)
        border_width = max(1.0, size * TILE_BORDER_RATIO)
        half_border = border_width / 2.0
        tile = ui_qt.QtCore.QRectF(half_border, half_border, size - border_width, size - border_width)
        radius = size * TILE_RADIUS_RATIO
        painter.setPen(ui_qt.QtGui.QPen(ui_qt.QtGui.QColor(accent_color), border_width))
        painter.setBrush(ui_qt.QtGui.QColor(tracker_constants.TRAY_TILE_COLOR))
        painter.drawRoundedRect(tile, radius, radius)
        inset = border_width + size * 0.07
        bar_height = max(2.0, size * BAR_HEIGHT_RATIO)
        bar_track = ui_qt.QtCore.QRectF(inset, size - inset - bar_height, size - inset * 2, bar_height)
        painter.setPen(ui_qt.QtCore.Qt.NoPen)
        painter.setBrush(ui_qt.QtGui.QColor(tracker_constants.TRAY_TRACK_COLOR))
        painter.drawRoundedRect(bar_track, bar_height / 2.0, bar_height / 2.0)
        fill_width = bar_track.width() * max(0, min(100, progress)) / 100.0
        if fill_width > 0:
            painter.setBrush(ui_qt.QtGui.QColor(accent_color))
            painter.drawRoundedRect(
                ui_qt.QtCore.QRectF(bar_track.left(), bar_track.top(), max(fill_width, bar_height), bar_height),
                bar_height / 2.0,
                bar_height / 2.0,
            )
        text_area = ui_qt.QtCore.QRectF(inset, inset, size - inset * 2, bar_track.top() - inset * 1.4)
        text = str(int(progress))
        font = TrackerWindowManager.fit_badge_font(
            painter.font(), text, text_area.width() * DIGIT_WIDTH_RATIO, text_area.height() * DIGIT_HEIGHT_RATIO
        )
        painter.setFont(font)
        painter.setPen(ui_qt.QtGui.QColor(tracker_constants.TRAY_TEXT_COLOR))
        painter.drawText(text_area, ui_qt.QtLib.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap

    @staticmethod
    def fit_badge_font(base_font, text, max_width, max_height):
        """Finds the largest bold pixel font whose measured text fits a box.

        Args:
            base_font (QFont): Font to copy.
            text (str): Text to measure.
            max_width (float): Available width in pixels.
            max_height (float): Available height in pixels.

        Returns:
            QFont: Bold font that fits, never smaller than the minimum readable size.
        """
        font = ui_qt.QtGui.QFont(base_font)
        font.setBold(True)
        pixel_size = max(MIN_BADGE_FONT_PIXELS, int(max_height * 1.4))
        while True:
            font.setPixelSize(pixel_size)
            bounds = ui_qt.QtGui.QFontMetricsF(font).tightBoundingRect(text)
            if (bounds.width() <= max_width and bounds.height() <= max_height) or pixel_size <= MIN_BADGE_FONT_PIXELS:
                return font
            pixel_size -= 1

    def set_tooltip(self, text):
        """Updates the tray hover text.

        Args:
            text (str): Short status summary.
        """
        if self.tray_icon:
            self.tray_icon.setToolTip(text)

    def notify(self, title, message):
        """Shows a tray notification when every tracker window is hidden.

        Args:
            title (str): Notification title.
            message (str): Notification body.
        """
        if self.tray_icon and self.tray_enabled and not self.get_active_window().isVisible():
            self.tray_icon.showMessage(title, message)

    def shutdown(self):
        """Hides the compact window and removes the tray icon."""
        self.compact_view.hide()
        if self.tray_icon:
            self.tray_icon.hide()
