"""Windows title bar theming for regular (non-frameless) Qt windows."""

import sys

import gt.ui.qt_import as ui_qt


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DEFAULT_CAPTION_COLOR = "#292929"
DEFAULT_TEXT_COLOR = "#e0e0e0"
DEFAULT_BORDER_COLOR = "#4a4a4a"
MAYA_MAIN_WINDOW_NAME = "MayaWindow"


def to_colorref(color_name):
    """Converts a ``#rrggbb`` color to a Windows COLORREF integer.

    Args:
        color_name (str): Color such as ``#292929``.

    Returns:
        int: COLORREF value (0x00BBGGRR).
    """
    color = ui_qt.QtGui.QColor(color_name)
    return (color.blue() << 16) | (color.green() << 8) | color.red()


def apply_dark_title_bar(
    window,
    caption_color=DEFAULT_CAPTION_COLOR,
    text_color=DEFAULT_TEXT_COLOR,
    border_color=DEFAULT_BORDER_COLOR,
):
    """Colors the native title bar to match a dark tool window.

    Uses the Windows 10/11 DWM attributes. Does nothing on other platforms, for
    docked or embedded widgets, or when the calls are unsupported (the caption
    and border colors need Windows 11; older versions still get dark mode).

    Args:
        window (QWidget): Top-level window that is already created.
        caption_color (str, optional): Title bar background.
        text_color (str, optional): Title bar text.
        border_color (str, optional): Window border.

    Returns:
        bool: True when the attributes were applied.
    """
    if sys.platform != "win32":
        return False
    window = window.window()
    if not window.isWindow() or window.objectName() == MAYA_MAIN_WINDOW_NAME:
        # A view docked into Maya's own panels has no title bar of its own to theme.
        return False
    try:
        import ctypes

        handle = ctypes.c_void_p(int(window.winId()))
        dwm = ctypes.windll.dwmapi
        attributes = (
            (DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
            (DWMWA_CAPTION_COLOR, to_colorref(caption_color)),
            (DWMWA_TEXT_COLOR, to_colorref(text_color)),
            (DWMWA_BORDER_COLOR, to_colorref(border_color)),
        )
        for attribute, value in attributes:
            dwm.DwmSetWindowAttribute(
                handle, attribute, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int)
            )
        return True
    except Exception:
        return False


class DarkTitleBarFilter(ui_qt.QtCore.QObject):
    """Re-applies the dark title bar every time the window is shown."""

    def __init__(self, window, **colors):
        """Installs the filter on a window.

        Args:
            window (QWidget): Window to theme.
            **colors: Optional ``caption_color``, ``text_color`` and ``border_color``.
        """
        super().__init__(window)
        self.colors = colors
        self.window = window
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        """Themes the title bar on show.

        Args:
            watched (QObject): Watched window.
            event (QEvent): Event.

        Returns:
            bool: Always False.
        """
        event_type = event.type()
        if event_type in (
            ui_qt.QtCore.QEvent.Show,
            ui_qt.QtCore.QEvent.ParentChange,
            ui_qt.QtCore.QEvent.WindowActivate,
        ):
            apply_dark_title_bar(watched, **self.colors)
            if event_type == ui_qt.QtCore.QEvent.Show:
                # Maya may move the view into its own floating window after it is shown.
                ui_qt.QtCore.QTimer.singleShot(250, self._apply_later)
        return False

    def _apply_later(self):
        """Applies the title bar again once Maya has finished re-parenting the window."""
        try:
            apply_dark_title_bar(self.window, **self.colors)
        except RuntimeError:
            return


def install_dark_title_bar(window, **colors):
    """Keeps a window's native title bar dark for its whole lifetime.

    Args:
        window (QWidget): Window to theme.
        **colors: Optional ``caption_color``, ``text_color`` and ``border_color``.

    Returns:
        DarkTitleBarFilter: The installed filter (parented to the window).
    """
    return DarkTitleBarFilter(window, **colors)
