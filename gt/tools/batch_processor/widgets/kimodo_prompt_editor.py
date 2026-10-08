"""Ordered prompt-segment editor for the Kimodo Definition task."""

from functools import partial
from gt.ui import qt_import as qt
from gt.ui.qt_utils import TablePlaceholderDelegate


class KimodoPromptEditor(qt.QtWidgets.QWidget):
    """Edits the existing prompt list schema without requiring users to write JSON."""

    def __init__(self, prompts, setter, parent=None):
        """Builds the segment table and its editing actions.

        Args:
            prompts (list): Existing text/duration dictionaries.
            setter (callable): Receives the full edited prompt list.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setter = setter
        layout = qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = qt.QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Seconds", "Motion description"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(qt.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, qt.QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, qt.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, self.fontMetrics().horizontalAdvance("Seconds") + 40)
        self.table.setMinimumHeight(140)
        self.table.setMaximumHeight(240)
        self.table.setToolTip("Double-click a cell to edit.\n"
                              "Each row is one ordered motion segment.\n"
                              "Describe actions in plain language and set a positive duration in seconds.")
        self.placeholder_delegate = TablePlaceholderDelegate(
            "Describe the motion, e.g. A person walks to a chair and sits down.", [1], parent=self.table)
        self.table.setItemDelegateForColumn(1, self.placeholder_delegate)
        layout.addWidget(self.table)
        self.hint = qt.QtWidgets.QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        actions = qt.QtWidgets.QHBoxLayout()
        self.buttons = {}
        for key, text, callback, tooltip in (
                ("add", "Add Segment", self.add_segment,
                 "Append a motion segment and start editing its description."),
                ("remove", "Remove", self.remove_segment,
                 "Remove the selected segment; keep at least one segment."),
                ("up", "Move Up", partial(self.move_segment, -1),
                 "Move the selected segment earlier in the sequence."),
                ("down", "Move Down", partial(self.move_segment, 1),
                 "Move the selected segment later in the sequence.")):
            button = qt.QtWidgets.QPushButton(text)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            actions.addWidget(button)
            self.buttons[key] = button
        actions.addStretch(1)
        layout.addLayout(actions)
        if isinstance(prompts, list):
            for prompt in prompts:
                row = self.table.rowCount()
                self.table.insertRow(row)
                if isinstance(prompt, dict):
                    self.table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem(str(prompt.get("duration_seconds", ""))))
                    self.table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(str(prompt.get("text", ""))))
        self.table.itemChanged.connect(self.commit)
        self.table.itemSelectionChanged.connect(self.update_actions)
        self.table.setCurrentCell(0, 1)
        self.update_actions()

    def commit(self, unused_item=None):
        """Stores edited cells, preserving invalid values for task validation.

        Args:
            unused_item (QTableWidgetItem, optional): Changed cell from the table signal.
        """
        prompts = []
        for row in range(self.table.rowCount()):
            duration_item = self.table.item(row, 0)
            text_item = self.table.item(row, 1)
            duration = duration_item.text().strip() if duration_item else ""
            try:
                duration = float(duration)
            except ValueError:
                pass
            prompts.append({"duration_seconds": duration, "text": text_item.text() if text_item else ""})
        self.setter(prompts)
        self.update_actions()

    def add_segment(self):
        """Appends an empty description without resetting existing rows or duration edits."""
        blocked = self.table.blockSignals(True)
        row = self.table.rowCount()
        try:
            self.table.insertRow(row)
            self.table.setItem(row, 0, qt.QtWidgets.QTableWidgetItem("4"))
            self.table.setItem(row, 1, qt.QtWidgets.QTableWidgetItem(""))
        finally:
            self.table.blockSignals(blocked)
        self.table.setCurrentCell(row, 1)
        self.commit()
        self.table.editItem(self.table.item(row, 1))

    def remove_segment(self):
        """Removes the selected row while retaining at least one prompt."""
        row = self.table.currentRow()
        if row >= 0 and self.table.rowCount() > 1:
            self.table.removeRow(row)
            self.table.setCurrentCell(min(row, self.table.rowCount() - 1), 1)
            self.commit()

    def move_segment(self, direction, unused_checked=False):
        """Swaps the selected segment with its neighbor without rebuilding the editor.

        Args:
            direction (int): Negative one for up, positive one for down.
            unused_checked (bool): Optional button-signal state.
        """
        row = self.table.currentRow()
        destination = row + direction
        if row < 0 or not 0 <= destination < self.table.rowCount():
            return
        blocked = self.table.blockSignals(True)
        try:
            for column in range(2):
                selected = self.table.takeItem(row, column)
                neighbor = self.table.takeItem(destination, column)
                self.table.setItem(row, column, neighbor)
                self.table.setItem(destination, column, selected)
        finally:
            self.table.blockSignals(blocked)
        self.table.setCurrentCell(destination, 1)
        self.commit()

    def update_actions(self):
        """Enables only operations that apply to the selected segment."""
        row = self.table.currentRow()
        count = self.table.rowCount()
        self.buttons["remove"].setEnabled(row >= 0 and count > 1)
        self.buttons["up"].setEnabled(row > 0)
        self.buttons["down"].setEnabled(0 <= row < count - 1)

    def set_timing_mode(self, match_source):
        """Explains whether durations are absolute or scaled to fit the source clip.

        Args:
            match_source (bool): Whether the task preserves source duration.
        """
        self.hint.setText(
            "Double-click to edit. Segment durations are scaled proportionally to fit the source range."
            if match_source else "Double-click to edit. Segment durations set the generated clip length in seconds.")
