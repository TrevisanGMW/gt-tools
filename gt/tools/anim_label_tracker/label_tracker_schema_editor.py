"""Schema editor dialog for Animation Label Tracker."""

import copy
import json

import gt.ui.qt_import as ui_qt


QtWidgets = ui_qt.QtWidgets


class SchemaEditorDialog(QtWidgets.QDialog):
    """Edits Animation Label Tracker schemas with form and JSON views."""

    def __init__(self, schema, parent=None):
        """Initializes the schema editor.

        Args:
            schema (dict): Schema data to edit.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.schema = copy.deepcopy(schema or {})
        self._entries = []
        self._current_item = None
        self._json_dirty = False
        self._updating_json = False
        self.setWindowTitle("Edit Animation Label Tracker Schema")
        self.resize(860, 620)
        self._build_ui()
        self._refresh_entries()
        self._update_json_text()

    def _build_ui(self):
        """Builds the schema editor widgets."""
        main_layout = QtWidgets.QVBoxLayout(self)

        validation_group = QtWidgets.QGroupBox("Validation")
        validation_layout = QtWidgets.QHBoxLayout(validation_group)
        self.full_coverage_checkbox = QtWidgets.QCheckBox("Require full coverage")
        self.allow_overlap_checkbox = QtWidgets.QCheckBox("Allow overlap")
        validation_layout.addWidget(self.full_coverage_checkbox)
        validation_layout.addWidget(self.allow_overlap_checkbox)
        validation_layout.addStretch()
        main_layout.addWidget(validation_group)

        editor_layout = QtWidgets.QHBoxLayout()

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        section_layout = QtWidgets.QHBoxLayout()
        section_layout.addWidget(QtWidgets.QLabel("Section:"))
        self.section_combo = QtWidgets.QComboBox()
        self.section_combo.addItem("File Data", "file_level")
        self.section_combo.addItem("Range Data", "frame_range")
        self.section_combo.currentIndexChanged.connect(self._refresh_entries)
        section_layout.addWidget(self.section_combo)
        left_layout.addLayout(section_layout)

        self.item_list = QtWidgets.QListWidget()
        self.item_list.currentRowChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.item_list)

        item_buttons_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add")
        self.remove_button = QtWidgets.QPushButton("Remove")
        self.up_button = QtWidgets.QPushButton("Up")
        self.down_button = QtWidgets.QPushButton("Down")
        self.add_button.clicked.connect(self._add_item)
        self.remove_button.clicked.connect(self._remove_item)
        self.up_button.clicked.connect(lambda: self._move_item(-1))
        self.down_button.clicked.connect(lambda: self._move_item(1))
        item_buttons_layout.addWidget(self.add_button)
        item_buttons_layout.addWidget(self.remove_button)
        item_buttons_layout.addWidget(self.up_button)
        item_buttons_layout.addWidget(self.down_button)
        left_layout.addLayout(item_buttons_layout)
        editor_layout.addWidget(left_widget, 1)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        form_layout = QtWidgets.QFormLayout()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["enum", "string", "boolean", "separator", "row"])
        self.name_edit = QtWidgets.QLineEdit()
        self.label_edit = QtWidgets.QLineEdit()
        self.options_edit = QtWidgets.QLineEdit()
        self.required_checkbox = QtWidgets.QCheckBox()
        self.automation_edit = QtWidgets.QLineEdit()
        self.placeholder_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QPlainTextEdit()
        self.description_edit.setMinimumHeight(100)
        form_layout.addRow("Type:", self.type_combo)
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Label:", self.label_edit)
        form_layout.addRow("Options (comma separated):", self.options_edit)
        form_layout.addRow("Required:", self.required_checkbox)
        form_layout.addRow("Automation:", self.automation_edit)
        form_layout.addRow("Placeholder:", self.placeholder_edit)
        form_layout.addRow("Description:", self.description_edit)
        right_layout.addLayout(form_layout)

        advanced_label = QtWidgets.QLabel(
            "Advanced JSON is available for row items and custom parameters."
        )
        right_layout.addWidget(advanced_label)
        self.json_edit = QtWidgets.QPlainTextEdit()
        self.json_edit.setTabChangesFocus(False)
        self.json_edit.textChanged.connect(self._mark_json_dirty)
        right_layout.addWidget(self.json_edit, 1)
        editor_layout.addWidget(right_widget, 2)
        main_layout.addLayout(editor_layout, 1)

        dialog_buttons_layout = QtWidgets.QHBoxLayout()
        dialog_buttons_layout.addStretch()
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.write_button = QtWidgets.QPushButton("Write")
        self.cancel_button.clicked.connect(self.reject)
        self.write_button.clicked.connect(self._write_schema)
        dialog_buttons_layout.addWidget(self.cancel_button)
        dialog_buttons_layout.addWidget(self.write_button)
        main_layout.addLayout(dialog_buttons_layout)

        self.full_coverage_checkbox.stateChanged.connect(self._save_validation)
        self.allow_overlap_checkbox.stateChanged.connect(self._save_validation)
        for widget in (
            self.type_combo,
            self.name_edit,
            self.label_edit,
            self.options_edit,
            self.required_checkbox,
            self.automation_edit,
            self.placeholder_edit,
            self.description_edit,
        ):
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self._save_current_item)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.stateChanged.connect(self._save_current_item)
            else:
                widget.textChanged.connect(self._save_current_item)

    def _get_section_name(self):
        """Gets the currently selected schema section.

        Returns:
            str: Schema section key.
        """
        return self.section_combo.currentData()

    def _iter_items(self, items):
        """Yields editable objects from nested schema items.

        Args:
            items (list): Schema item list.

        Yields:
            dict: Schema item.
        """
        for item in items or []:
            yield item
            if item.get("type") == "row":
                for child_item in self._iter_items(item.get("items", [])):
                    yield child_item

    def _refresh_entries(self):
        """Refreshes the visible item list for the active section."""
        if not hasattr(self, "item_list"):
            return
        self._save_current_item()
        section_name = self._get_section_name()
        self._entries = list(self._iter_items(self.schema.get(section_name, [])))
        self.item_list.blockSignals(True)
        self.item_list.clear()
        for item in self._entries:
            item_type = item.get("type", "unknown")
            display_name = item.get("label") or item.get("name") or item_type
            self.item_list.addItem(f"{display_name} [{item_type}]")
        self.item_list.blockSignals(False)
        if self._entries:
            self.item_list.setCurrentRow(0)
        else:
            self._current_item = None
            self._clear_item_form()
        self._load_validation()

    def _on_item_selected(self, row):
        """Loads a selected schema item into the form.

        Args:
            row (int): Selected list row.
        """
        self._save_current_item()
        if row < 0 or row >= len(self._entries):
            self._current_item = None
            self._clear_item_form()
            return
        self._current_item = self._entries[row]
        self._load_item_form(self._current_item)

    def _load_item_form(self, item):
        """Loads one schema item into the detail controls.

        Args:
            item (dict): Item to display.
        """
        controls = (
            self.type_combo,
            self.name_edit,
            self.label_edit,
            self.options_edit,
            self.required_checkbox,
            self.automation_edit,
            self.placeholder_edit,
            self.description_edit,
        )
        for control in controls:
            control.blockSignals(True)
        self.type_combo.setCurrentText(item.get("type", "string"))
        self.name_edit.setText(str(item.get("name", "")))
        self.label_edit.setText(str(item.get("label", "")))
        self.options_edit.setText(", ".join(item.get("options", [])))
        self.required_checkbox.setChecked(bool(item.get("required", False)))
        self.automation_edit.setText(str(item.get("automation", "")))
        self.placeholder_edit.setText(str(item.get("placeholder", "")))
        self.description_edit.setPlainText(str(item.get("description", "")))
        for control in controls:
            control.blockSignals(False)
        self._set_item_controls_enabled(item.get("type") not in ("row", "separator"))
        self._update_json_text()

    def _clear_item_form(self):
        """Clears the item detail controls."""
        self._load_item_form({"type": "string"})

    def _set_item_controls_enabled(self, enabled):
        """Enables or disables form controls for structural items.

        Args:
            enabled (bool): Whether editable field controls should be enabled.
        """
        for control in (
            self.name_edit,
            self.label_edit,
            self.options_edit,
            self.required_checkbox,
            self.automation_edit,
            self.placeholder_edit,
            self.description_edit,
        ):
            control.setEnabled(enabled)

    def _save_current_item(self, *args):
        """Writes form values to the currently selected schema item."""
        if not self._current_item:
            return
        item = self._current_item
        item_type = self.type_combo.currentText()
        item["type"] = item_type
        if item_type in ("row", "separator"):
            self._update_json_text()
            return
        item["name"] = self.name_edit.text().strip()
        item["label"] = self.label_edit.text().strip()
        item["options"] = [
            option.strip()
            for option in self.options_edit.text().split(",")
            if option.strip()
        ]
        item["required"] = self.required_checkbox.isChecked()
        item["automation"] = self.automation_edit.text().strip()
        item["placeholder"] = self.placeholder_edit.text().strip()
        item["description"] = self.description_edit.toPlainText()
        self._update_json_text()

    def _save_validation(self, *args):
        """Stores validation checkbox values."""
        self.schema.setdefault("validation", {})["full_coverage"] = (
            self.full_coverage_checkbox.isChecked()
        )
        self.schema.setdefault("validation", {})["allow_overlap"] = (
            self.allow_overlap_checkbox.isChecked()
        )
        self._update_json_text()

    def _load_validation(self):
        """Loads validation values into the checkboxes."""
        validation = self.schema.get("validation", {})
        self.full_coverage_checkbox.blockSignals(True)
        self.allow_overlap_checkbox.blockSignals(True)
        self.full_coverage_checkbox.setChecked(bool(validation.get("full_coverage", False)))
        self.allow_overlap_checkbox.setChecked(bool(validation.get("allow_overlap", True)))
        self.full_coverage_checkbox.blockSignals(False)
        self.allow_overlap_checkbox.blockSignals(False)

    def _find_parent_list(self, items, target_item):
        """Finds the list containing a nested item.

        Args:
            items (list): Items to search.
            target_item (dict): Item to find.

        Returns:
            list or None: Containing list.
        """
        for item in items:
            if item is target_item:
                return items
            if item.get("type") == "row":
                parent_list = self._find_parent_list(item.get("items", []), target_item)
                if parent_list is not None:
                    return parent_list
        return None

    def _add_item(self):
        """Adds a new editable string field to the current section."""
        self._save_current_item()
        section_name = self._get_section_name()
        self.schema.setdefault(section_name, []).append(
            {
                "type": "string",
                "name": "new_field",
                "label": "New Field",
                "required": False,
                "description": "",
            }
        )
        self._refresh_entries()
        self.item_list.setCurrentRow(len(self._entries) - 1)

    def _remove_item(self):
        """Removes the selected schema item."""
        if not self._current_item:
            return
        section_name = self._get_section_name()
        parent_list = self._find_parent_list(
            self.schema.get(section_name, []), self._current_item
        )
        if parent_list is not None:
            parent_list.remove(self._current_item)
        self._current_item = None
        self._refresh_entries()

    def _move_item(self, offset):
        """Moves the selected item within its parent list.

        Args:
            offset (int): Relative list offset, usually -1 or 1.
        """
        if not self._current_item:
            return
        section_name = self._get_section_name()
        parent_list = self._find_parent_list(
            self.schema.get(section_name, []), self._current_item
        )
        if parent_list is None:
            return
        current_index = parent_list.index(self._current_item)
        new_index = current_index + offset
        if new_index < 0 or new_index >= len(parent_list):
            return
        parent_list[current_index], parent_list[new_index] = (
            parent_list[new_index],
            parent_list[current_index],
        )
        self._refresh_entries()
        self.item_list.setCurrentRow(self._entries.index(self._current_item))

    def _mark_json_dirty(self):
        """Marks the advanced JSON editor as user-modified."""
        if not self._updating_json:
            self._json_dirty = True

    def _update_json_text(self):
        """Updates the advanced JSON editor from the current schema."""
        if not hasattr(self, "json_edit"):
            return
        self._updating_json = True
        self.json_edit.setPlainText(json.dumps(self.schema, indent=2, ensure_ascii=False))
        self._updating_json = False
        self._json_dirty = False

    def _apply_json(self):
        """Applies advanced JSON changes to the schema.

        Returns:
            bool: True when the JSON was valid and applied.
        """
        if not self._json_dirty:
            return True
        try:
            schema = json.loads(self.json_edit.toPlainText())
        except (TypeError, ValueError) as error:
            QtWidgets.QMessageBox.warning(self, "Invalid Schema", str(error))
            return False
        if not isinstance(schema, dict):
            QtWidgets.QMessageBox.warning(self, "Invalid Schema", "Schema root must be an object.")
            return False
        self.schema = schema
        self._json_dirty = False
        self._refresh_entries()
        return True

    def _write_schema(self):
        """Validates edits and closes the dialog with accepted data."""
        if self._json_dirty:
            if not self._apply_json():
                return
        else:
            self._save_current_item()
        self.accept()

    def get_schema(self):
        """Gets the edited schema.

        Returns:
            dict: Edited schema data.
        """
        return copy.deepcopy(self.schema)
