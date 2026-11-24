"""
File Drop List - A tree widget that accepts files and folders dragged from Explorer/Finder.

It has a darker background and a dashed outline so it reads as a drop area, highlights while
something is dragged over it, and emits signals for common list shortcuts.

Import Line:
    from gt.ui.file_drop_list import FileDropList

Example:
    file_list = FileDropList(placeholder_text="Drop files or folders here")
    file_list.paths_dropped.connect(lambda paths: print(paths))
"""

import gt.ui.qt_import as ui_qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DROP_AREA_STYLESHEET = (
    "QTreeWidget {{ background-color: rgb(38, 38, 38); alternate-background-color: rgb(44, 44, 44); "
    "border: 1px dashed {border_color}; border-radius: 4px; }}"
    "QTreeWidget:disabled {{ color: rgb(110, 110, 110); }}"
    "QHeaderView::section {{ background-color: rgb(50, 50, 50); color: rgb(190, 190, 190); padding: 3px 6px; "
    "border: none; border-right: 1px solid rgb(62, 62, 62); border-bottom: 1px solid rgb(62, 62, 62); }}"
)
IDLE_BORDER_COLOR = "rgb(105, 105, 105)"
ACTIVE_BORDER_COLOR = "rgb(82, 133, 166)"


class FileDropList(ui_qt.QtWidgets.QTreeWidget):
    """Tree widget that emits dropped local paths and draws a hint while empty."""

    paths_dropped = ui_qt.QtCore.Signal(list)
    delete_requested = ui_qt.QtCore.Signal()
    copy_requested = ui_qt.QtCore.Signal()
    paste_requested = ui_qt.QtCore.Signal()
    toggle_requested = ui_qt.QtCore.Signal()
    context_menu_requested = ui_qt.QtCore.Signal(object)

    def __init__(self, parent=None, placeholder_text="Drop files or folders here"):
        """Initializes the drop list.

        Args:
            parent (QWidget, optional): Parent widget.
            placeholder_text (str, optional): Hint drawn while the list is empty.
        """
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self._is_drag_active = False
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setAlternatingRowColors(True)
        self.setDragDropMode(ui_qt.QtWidgets.QAbstractItemView.DragDropMode.DropOnly)
        self._update_drop_style()

    def _update_drop_style(self):
        """Applies the idle or highlighted drop-area style."""
        border_color = ACTIVE_BORDER_COLOR if self._is_drag_active else IDLE_BORDER_COLOR
        self.setStyleSheet(DROP_AREA_STYLESHEET.format(border_color=border_color))

    def _set_drag_active(self, is_active):
        """Updates the drag highlight.

        Args:
            is_active (bool): Whether a drag is over the list.
        """
        if self._is_drag_active == is_active:
            return
        self._is_drag_active = is_active
        self._update_drop_style()
        self.viewport().update()

    @staticmethod
    def get_local_paths(mime_data):
        """Gets local file system paths from drag-and-drop data.

        Args:
            mime_data (QMimeData): Dropped data.

        Returns:
            list: Local paths. Remote URLs are ignored.
        """
        if not mime_data or not mime_data.hasUrls():
            return []
        return [url.toLocalFile() for url in mime_data.urls() if url.isLocalFile() and url.toLocalFile()]

    def dragEnterEvent(self, event):
        """Accepts drags that carry local paths.

        Args:
            event (QDragEnterEvent): Drag event.
        """
        if self.get_local_paths(event.mimeData()):
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        """Keeps accepting drags that carry local paths.

        Args:
            event (QDragMoveEvent): Drag event.
        """
        if self.get_local_paths(event.mimeData()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Clears the drag highlight.

        Args:
            event (QDragLeaveEvent): Drag event.
        """
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """Emits the dropped local paths.

        Args:
            event (QDropEvent): Drop event.
        """
        self._set_drag_active(False)
        paths = self.get_local_paths(event.mimeData())
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.paths_dropped.emit(paths)

    def keyPressEvent(self, event):
        """Emits signals for Delete/Backspace, Ctrl+C, Ctrl+V and Space.

        Args:
            event (QKeyEvent): Key event.
        """
        if event.key() in (ui_qt.QtCore.Qt.Key.Key_Delete, ui_qt.QtCore.Qt.Key.Key_Backspace):
            self.delete_requested.emit()
            return
        if event.matches(ui_qt.QtGui.QKeySequence.StandardKey.Copy):
            self.copy_requested.emit()
            return
        if event.matches(ui_qt.QtGui.QKeySequence.StandardKey.Paste):
            self.paste_requested.emit()
            return
        if event.key() == ui_qt.QtCore.Qt.Key.Key_Space and self.selectedItems():
            self.toggle_requested.emit()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Emits context_menu_requested with the click position in viewport coordinates.

        Handled here (instead of the custom context menu policy) so the menu works when the widget is
        hosted inside Maya's workspace controls.

        Args:
            event (QContextMenuEvent): Context menu event.
        """
        self.context_menu_requested.emit(self.viewport().mapFromGlobal(event.globalPos()))
        event.accept()

    def paintEvent(self, event):
        """Draws the list, plus the placeholder hint while empty.

        Args:
            event (QPaintEvent): Paint event.
        """
        super().paintEvent(event)
        if self.topLevelItemCount():
            return
        painter = ui_qt.QtGui.QPainter(self.viewport())
        try:
            color = ui_qt.QtGui.QColor(150, 170, 185) if self._is_drag_active else ui_qt.QtGui.QColor(130, 130, 130)
            painter.setPen(color)
            painter.drawText(self.viewport().rect(), ui_qt.QtCore.Qt.AlignmentFlag.AlignCenter, self.placeholder_text)
        finally:
            painter.end()
