"""Resizable table separator with a task-specific saved table height."""

from gt.ui import qt_import as qt


class TableHeightHandle(qt.QtWidgets.QFrame):
    """Draggable horizontal separator that stores its height on the owning task."""

    def __init__(self, table, task, state_key, parent=None):
        """Initializes a separator and restores its owning task's saved height.

        Args:
            table (QWidget): Table resized by this handle.
            task (BatchTask): Task that owns the saved UI state.
            state_key (str): Key storing the table height in the task's UI state.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.table = table
        self.task = task
        self.state_key = state_key
        self._minimum_height = table.minimumHeight()
        self._drag_start_y = None
        self._drag_start_height = None
        self.setFrameShape(qt.QtLib.FrameStyle.HLine)
        self.setFrameShadow(qt.QtLib.FrameStyle.Sunken)
        self.setFixedHeight(10)
        self.setCursor(qt.QtLib.CursorShape.SizeVerCursor)
        self.setAccessibleName("Resize table height")
        self.setToolTip("Drag to adjust this task's table height. The height is saved with the task.")
        self.restore_height()

    def get_task_ui_state(self, create=False):
        """Gets the UI state dictionary stored with the owning task.

        Args:
            create (bool, optional): Whether to create missing UI state data.

        Returns:
            dict: Mutable task-specific UI state.
        """
        task_ui_state = self.task.extra_data.get("ui_state")
        if not isinstance(task_ui_state, dict):
            if not create:
                return {}
            task_ui_state = {}
            self.task.extra_data["ui_state"] = task_ui_state
        return task_ui_state

    def restore_height(self):
        """Applies this task's previously saved table height when available."""
        saved_height = self.get_task_ui_state().get(self.state_key)
        try:
            saved_height = int(saved_height)
        except (TypeError, ValueError):
            return
        if saved_height >= self._minimum_height:
            self.table.setFixedHeight(saved_height)

    def save_height(self):
        """Stores the table's current height with its owning task."""
        self.get_task_ui_state(create=True)[self.state_key] = self.table.height()

    def get_global_y(self, event):
        """Gets the event's global vertical position across supported Qt versions.

        Args:
            event (QMouseEvent): Mouse event being processed.

        Returns:
            int: Global vertical mouse coordinate.
        """
        global_position = getattr(event, "globalPosition", None)
        if global_position:
            return global_position().toPoint().y()
        return event.globalPos().y()

    def mousePressEvent(self, event):
        """Starts a table resize when the left mouse button is pressed.

        Args:
            event (QMouseEvent): Mouse press event.
        """
        if event.button() == qt.QtLib.MouseButton.LeftButton:
            self._drag_start_y = self.get_global_y(event)
            self._drag_start_height = self.table.height()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Resizes the table by the distance dragged from the separator.

        Args:
            event (QMouseEvent): Mouse move event.
        """
        if self._drag_start_y is not None:
            height_delta = self.get_global_y(event) - self._drag_start_y
            table_height = max(self._minimum_height, self._drag_start_height + height_delta)
            self.table.setFixedHeight(table_height)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Saves the table's height when a resize drag ends.

        Args:
            event (QMouseEvent): Mouse release event.
        """
        if event.button() == qt.QtLib.MouseButton.LeftButton and self._drag_start_y is not None:
            self._drag_start_y = None
            self._drag_start_height = None
            self.save_height()
            event.accept()
            return
        super().mouseReleaseEvent(event)
