"""Qt view for Connect Attributes."""

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class ConnectAttributesView(metaclass=qt_utils.MayaWindowMeta):
    """Compact interface for building or removing attribute connections."""

    def __init__(self, parent=None, version=None):
        """Initializes the view.

        Args:
            parent (QWidget, optional): Parent Maya window.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        title = "Connect Attributes"
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_connect_attributes))
        self.setStyleSheet(ui_res_lib.Stylesheet.maya_dialog_base + ui_res_lib.Stylesheet.combobox_base)
        self._child_dialogs = []
        self._build_widgets()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds the complete user interface."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 14)
        main_layout.setSpacing(9)

        self.menu_bar = ui_qt.QtWidgets.QMenuBar()
        self.settings_menu = self.menu_bar.addMenu("Settings")
        self.reset_action = self.settings_menu.addAction("Reset Settings")
        self.help_menu = self.menu_bar.addMenu("Help")
        self.help_action = self.help_menu.addAction("How to Use")
        main_layout.addWidget(self.menu_bar)

        self.description_label = ui_qt.QtWidgets.QLabel(
            "Connect one source attribute to one or more attributes on every target. "
            "Selection order is source first, then targets."
        )
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.description_label)

        operation_layout = ui_qt.QtWidgets.QHBoxLayout()
        operation_layout.addWidget(ui_qt.QtWidgets.QLabel("Operation"))
        self.connect_radio = ui_qt.QtWidgets.QRadioButton("Connect")
        self.disconnect_radio = ui_qt.QtWidgets.QRadioButton("Disconnect incoming")
        operation_layout.addWidget(self.connect_radio)
        operation_layout.addWidget(self.disconnect_radio)
        operation_layout.addStretch()
        main_layout.addLayout(operation_layout)

        objects_group = ui_qt.QtWidgets.QGroupBox("Objects")
        objects_layout = ui_qt.QtWidgets.QVBoxLayout(objects_group)
        objects_layout.setContentsMargins(12, 12, 12, 12)
        objects_layout.setSpacing(7)
        self.use_selection_checkbox = ui_qt.QtWidgets.QCheckBox(
            "Use current selection (source first, then targets)"
        )
        self.use_selection_checkbox.setToolTip(
            "Reads the selection when Preview or Run is clicked. Loaded objects are not required."
        )
        objects_layout.addWidget(self.use_selection_checkbox)

        load_layout = ui_qt.QtWidgets.QGridLayout()
        load_layout.setHorizontalSpacing(8)
        load_layout.setVerticalSpacing(6)
        self.load_source_button = ui_qt.QtWidgets.QPushButton("Load Selected Source")
        self.load_targets_button = ui_qt.QtWidgets.QPushButton("Load Selected Targets")
        self.source_status_label = ui_qt.QtWidgets.QPushButton("No source loaded")
        self.target_status_label = ui_qt.QtWidgets.QPushButton("No targets loaded")
        self.source_status_label.setFlat(True)
        self.target_status_label.setFlat(True)
        self.source_status_label.setToolTip("Click the label to select the loaded source.")
        self.target_status_label.setToolTip("Click the label to select the loaded targets.")
        load_layout.addWidget(self.load_source_button, 0, 0)
        load_layout.addWidget(self.source_status_label, 0, 1)
        load_layout.addWidget(self.load_targets_button, 1, 0)
        load_layout.addWidget(self.target_status_label, 1, 1)
        load_layout.setColumnStretch(1, 1)
        objects_layout.addLayout(load_layout)
        main_layout.addWidget(objects_group)

        attributes_group = ui_qt.QtWidgets.QGroupBox("Attributes")
        attributes_layout = ui_qt.QtWidgets.QGridLayout(attributes_group)
        attributes_layout.setContentsMargins(12, 12, 12, 12)
        attributes_layout.setHorizontalSpacing(8)
        attributes_layout.setVerticalSpacing(7)
        self.source_attribute_field = ui_qt.QtWidgets.QLineEdit()
        self.source_attribute_field.setPlaceholderText("e.g. translateX")
        self.source_attribute_field.setToolTip("One output attribute on the source object.")
        self.target_attributes_field = ui_qt.QtWidgets.QLineEdit()
        self.target_attributes_field.setPlaceholderText("e.g. translateX, visibility")
        self.target_attributes_field.setToolTip("One or more target attributes separated by commas.")
        self.list_all_button = ui_qt.QtWidgets.QPushButton("Browse All")
        self.list_keyable_button = ui_qt.QtWidgets.QPushButton("Browse Keyable")
        attributes_layout.addWidget(ui_qt.QtWidgets.QLabel("Source"), 0, 0)
        attributes_layout.addWidget(self.source_attribute_field, 0, 1, 1, 2)
        attributes_layout.addWidget(ui_qt.QtWidgets.QLabel("Targets"), 1, 0)
        attributes_layout.addWidget(self.target_attributes_field, 1, 1, 1, 2)
        attributes_layout.addWidget(self.list_all_button, 2, 1)
        attributes_layout.addWidget(self.list_keyable_button, 2, 2)
        attributes_layout.setColumnStretch(1, 1)
        attributes_layout.setColumnStretch(2, 1)
        main_layout.addWidget(attributes_group)

        options_group = ui_qt.QtWidgets.QGroupBox("Connection Options")
        options_layout = ui_qt.QtWidgets.QGridLayout(options_group)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setHorizontalSpacing(8)
        options_layout.setVerticalSpacing(7)
        self.reverse_checkbox = ui_qt.QtWidgets.QCheckBox("Add Reverse node")
        self.force_checkbox = ui_qt.QtWidgets.QCheckBox("Replace existing incoming connections")
        self.force_checkbox.setToolTip("Allows Maya to replace a connection already driving a target plug.")
        self.utility_checkbox = ui_qt.QtWidgets.QCheckBox("Insert utility node")
        self.utility_combo = ui_qt.QtWidgets.QComboBox()
        self.utility_combo.addItems(["plusMinusAverage", "multiplyDivide", "condition"])
        self.shared_input_checkbox = ui_qt.QtWidgets.QCheckBox("Add one shared secondary input node")
        self.shared_input_checkbox.setToolTip(
            "Creates one utility node and connects its output to the secondary input of every inserted node."
        )
        self.shared_input_combo = ui_qt.QtWidgets.QComboBox()
        self.shared_input_combo.addItems(["condition", "plusMinusAverage", "multiplyDivide"])
        options_layout.addWidget(self.reverse_checkbox, 0, 0, 1, 2)
        options_layout.addWidget(self.force_checkbox, 1, 0, 1, 2)
        options_layout.addWidget(self.utility_checkbox, 2, 0)
        options_layout.addWidget(self.utility_combo, 2, 1)
        options_layout.addWidget(self.shared_input_checkbox, 3, 0)
        options_layout.addWidget(self.shared_input_combo, 3, 1)
        options_layout.setColumnStretch(1, 1)
        main_layout.addWidget(options_group)

        self.status_label = ui_qt.QtWidgets.QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(24)
        main_layout.addWidget(self.status_label)

        action_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.preview_button = ui_qt.QtWidgets.QPushButton("Preview")
        self.run_button = ui_qt.QtWidgets.QPushButton("Connect Attributes")
        self.preview_button.setStyleSheet(
            "QPushButton { padding-left: 10px; padding-right: 10px; }"
        )
        self.run_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        action_button_height = max(
            38,
            self.preview_button.sizeHint().height(),
            self.run_button.sizeHint().height(),
        )
        self.preview_button.setFixedHeight(action_button_height)
        self.run_button.setFixedHeight(action_button_height)
        action_layout.addWidget(self.preview_button)
        action_layout.addWidget(self.run_button, 1)
        main_layout.addLayout(action_layout)

    def set_loaded_nodes(self, source_object, target_objects):
        """Updates the loaded-object summaries.

        Args:
            source_object (str or None): Loaded source node.
            target_objects (list): Loaded target nodes.
        """
        source_text = source_object or "No source loaded"
        targets = target_objects or []
        if not targets:
            target_text = "No targets loaded"
        elif len(targets) == 1:
            target_text = targets[0]
        else:
            target_text = f"{len(targets)} targets loaded"
        self.source_status_label.setText(source_text)
        self.source_status_label.setToolTip(source_text)
        self.target_status_label.setText(target_text)
        self.target_status_label.setToolTip("\n".join(targets) if targets else "No targets loaded")

    def update_enabled_state(self, use_selection, is_connect, use_utility, use_shared_input):
        """Enables controls only when they apply to the current mode.

        Args:
            use_selection (bool): Whether live selection mode is active.
            is_connect (bool): Whether the operation is Connect.
            use_utility (bool): Whether a utility node is enabled.
            use_shared_input (bool): Whether a shared input node is enabled.
        """
        self.load_source_button.setEnabled(not use_selection and is_connect)
        self.load_targets_button.setEnabled(not use_selection)
        self.source_status_label.setEnabled(not use_selection and is_connect)
        self.target_status_label.setEnabled(not use_selection)
        self.source_attribute_field.setEnabled(is_connect)
        self.reverse_checkbox.setEnabled(is_connect)
        self.force_checkbox.setEnabled(is_connect)
        self.utility_checkbox.setEnabled(is_connect)
        self.utility_combo.setEnabled(is_connect and use_utility)
        self.shared_input_checkbox.setEnabled(is_connect and use_utility)
        self.shared_input_combo.setEnabled(is_connect and use_utility and use_shared_input)
        self.run_button.setText("Connect Attributes" if is_connect else "Disconnect Incoming")
        if is_connect:
            self.description_label.setText(
                "Connect one source attribute to one or more attributes on every target. "
                "Selection order is source first, then targets."
            )
        else:
            self.description_label.setText(
                "Remove incoming connections from the listed attributes. "
                "Every selected or loaded object is treated as a target."
            )

    def set_status(self, message, level="info"):
        """Shows concise feedback at the bottom of the window.

        Args:
            message (str): Status text.
            level (str, optional): ``info``, ``success``, ``warning``, or ``error``.
        """
        colors = {
            "info": "#B8B8B8",
            "success": "#8BCB88",
            "warning": "#E2BE72",
            "error": "#E58A8A",
        }
        self.status_label.setStyleSheet(f"color: {colors.get(level, colors['info'])};")
        self.status_label.setText(message)

    def show_attribute_browser(self, node, attributes, keyable=False):
        """Shows attributes in a searchable, copyable dialog.

        Args:
            node (str): Node whose attributes are displayed.
            attributes (list): Attribute names.
            keyable (bool, optional): Whether the list is keyable-only.
        """
        dialog = ui_qt.QtWidgets.QDialog(self)
        dialog.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle(f"{'Keyable ' if keyable else ''}Attributes - {node}")
        dialog.resize(380, 470)
        layout = ui_qt.QtWidgets.QVBoxLayout(dialog)
        search_field = ui_qt.QtWidgets.QLineEdit()
        search_field.setPlaceholderText("Filter attributes...")
        attribute_list = ui_qt.QtWidgets.QListWidget()
        attribute_list.addItems(attributes)
        hint = ui_qt.QtWidgets.QLabel("Double-click an attribute to copy its name.")
        hint.setWordWrap(True)
        layout.addWidget(search_field)
        layout.addWidget(attribute_list)
        layout.addWidget(hint)

        search_field.textChanged.connect(
            lambda text: self._filter_list_widget(attribute_list, text)
        )
        attribute_list.itemDoubleClicked.connect(
            lambda item: ui_qt.QtWidgets.QApplication.clipboard().setText(item.text())
        )
        dialog.destroyed.connect(lambda *args: self._remove_child_dialog(dialog))
        self._child_dialogs.append(dialog)
        dialog.show()

    def show_connection_preview(self, preview_lines, operation, shared_input_type=None):
        """Shows planned connection operations in a searchable dialog.

        Args:
            preview_lines (list): Human-readable planned plug operations.
            operation (str): Active operation, either ``connect`` or ``disconnect``.
            shared_input_type (str, optional): Shared secondary-input node type.
        """
        dialog = ui_qt.QtWidgets.QDialog(self)
        dialog.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle("Connect Attributes Preview")
        dialog.resize(560, 420)
        layout = ui_qt.QtWidgets.QVBoxLayout(dialog)

        operation_label = "connections" if operation == "connect" else "disconnections"
        summary_label = ui_qt.QtWidgets.QLabel(
            f"{len(preview_lines)} planned {operation_label}. No scene changes have been made."
        )
        summary_label.setWordWrap(True)
        search_field = ui_qt.QtWidgets.QLineEdit()
        search_field.setPlaceholderText("Filter planned operations...")
        preview_list = ui_qt.QtWidgets.QListWidget()
        preview_list.addItems(preview_lines)
        layout.addWidget(summary_label)
        if shared_input_type:
            shared_input_label = ui_qt.QtWidgets.QLabel(
                f"Shared secondary input node: {shared_input_type}"
            )
            layout.addWidget(shared_input_label)
        layout.addWidget(search_field)
        layout.addWidget(preview_list)

        search_field.textChanged.connect(
            lambda text: self._filter_list_widget(preview_list, text)
        )
        dialog.destroyed.connect(lambda *args: self._remove_child_dialog(dialog))
        self._child_dialogs.append(dialog)
        dialog.show()

    def _remove_child_dialog(self, dialog):
        """Drops a closed child dialog reference.

        Args:
            dialog (QDialog): Dialog being removed.
        """
        if dialog in self._child_dialogs:
            self._child_dialogs.remove(dialog)

    @staticmethod
    def _filter_list_widget(list_widget, filter_text):
        """Filters a list widget using case-insensitive text.

        Args:
            list_widget (QListWidget): List widget to filter.
            filter_text (str): Filter string.
        """
        normalized_filter = str(filter_text or "").lower()
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            item.setHidden(normalized_filter not in item.text().lower())

    def show_help(self):
        """Shows concise usage guidance."""
        ui_qt.QtWidgets.QMessageBox.information(
            self,
            "Connect Attributes Help",
            "Selection mode reads objects when you click Preview or Run. "
            "Select the source first, then all targets.\n\n"
            "Loaded mode keeps a source and target list for repeated operations in the current scene.\n\n"
            "Disconnect Incoming treats every selected or loaded target as a target, ignores the source, and removes "
            "connections only from the exact attributes listed. Utility and Reverse nodes are available only while "
            "connecting.",
        )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = ConnectAttributesView()
        window.show()
