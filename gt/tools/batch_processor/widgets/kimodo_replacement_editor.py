"""Numbered prompt search/replace rules for Kimodo definition variations."""

from gt.ui import qt_import as qt
from gt.ui.qt_utils import TablePlaceholderDelegate


class KimodoReplacementEditor(qt.QtWidgets.QWidget):
    """Edits literal replacement rules grouped by their variation number."""

    def __init__(self, rules, setter, parent=None):
        """Builds the rule table and editing actions.

        Args:
            rules (list): Serialized variation, search, and replace dictionaries.
            setter (callable): Receives the complete edited rule list.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setSizePolicy(qt.QtLib.SizePolicy.Preferred, qt.QtLib.SizePolicy.Minimum)
        self.setter = setter
        layout = qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(qt.QtWidgets.QLabel("Prompt Search / Replace"))
        hint = qt.QtWidgets.QLabel(
            "Same variation number = rules applied together.\n"
            "Applied to every prompt, after Prompt choices.\n"
            "Case-sensitive; longer matches win.\n"
            "Set Definitions per file to include each variation.")
        hint.setToolTip("Example: variation 1: walk → run, walking → running;\n"
                        "variation 2: walk → jog.\n"
                        "Rules apply once; replacement text is not matched again.\n"
                        "Variations with no rules keep their prompt text.")
        layout.addWidget(hint)
        self.table = qt.QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Variation", "Search", "Replace"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(qt.QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, qt.QtWidgets.QHeaderView.ResizeMode.Interactive)
        for column in (1, 2):
            header.setSectionResizeMode(column, qt.QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, self.fontMetrics().horizontalAdvance("Variation") + 32)
        self.table.setMinimumHeight(145)
        self.table.setMaximumHeight(245)
        self.table.setToolTip("Double-click to edit.\n"
                              "Variation starts at 1.\n"
                              "Search is literal text, not a regular expression.\n"
                              "Leave Replace blank to remove matching text.")
        self.delegates = []
        for column, placeholder in ((1, "e.g. walking"), (2, "e.g. running (blank removes)")):
            delegate = TablePlaceholderDelegate(placeholder, [column], parent=self.table)
            self.table.setItemDelegateForColumn(column, delegate)
            self.delegates.append(delegate)
        layout.addWidget(self.table)
        actions = qt.QtWidgets.QHBoxLayout()
        self.add_button = qt.QtWidgets.QPushButton("Add Rule")
        self.add_button.setToolTip("Add another rule for the selected variation, or variation 1 when empty.")
        self.add_button.clicked.connect(self.add_rule)
        self.remove_button = qt.QtWidgets.QPushButton("Remove Rule")
        self.remove_button.setToolTip("Remove the selected search/replace rule.")
        self.remove_button.clicked.connect(self.remove_rule)
        actions.addWidget(self.add_button)
        actions.addWidget(self.remove_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        for rule in rules if isinstance(rules, list) else []:
            self.append_row(rule)
        self.table.itemChanged.connect(self.commit)
        self.table.itemSelectionChanged.connect(self.update_actions)
        self.update_actions()

    def append_row(self, rule):
        """Appends a rule without emitting partially populated edits.

        Args:
            rule (dict): Rule values to display.
        """
        blocked = self.table.blockSignals(True)
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, key in enumerate(("variation", "search", "replace")):
                value = rule.get(key, "") if isinstance(rule, dict) else ""
                self.table.setItem(row, column, qt.QtWidgets.QTableWidgetItem(str(value)))
        finally:
            self.table.blockSignals(blocked)

    def add_rule(self):
        """Adds a rule using the selected variation number."""
        selected = self.table.item(self.table.currentRow(), 0)
        self.append_row({"variation": selected.text() if selected else 1, "search": "", "replace": ""})
        self.table.setCurrentCell(self.table.rowCount() - 1, 1)
        self.commit()
        self.table.editItem(self.table.currentItem())

    def remove_rule(self):
        """Removes the selected rule and allows an empty rule list."""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.commit()

    def commit(self, unused_item=None):
        """Persists table edits, retaining invalid values for task validation.

        Args:
            unused_item (QTableWidgetItem, optional): Cell emitting the change.
        """
        rules = []
        for row in range(self.table.rowCount()):
            rule = {key: self.table.item(row, column).text()
                    for column, key in enumerate(("variation", "search", "replace"))}
            try:
                rule["variation"] = int(rule["variation"])
            except ValueError:
                pass
            rules.append(rule)
        self.setter(rules)
        self.update_actions()

    def update_actions(self):
        """Enables removal when a rule is selected."""
        self.remove_button.setEnabled(self.table.currentRow() >= 0)
