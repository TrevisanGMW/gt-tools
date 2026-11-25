"""Qt view for Connect Attributes."""

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
from gt.tools.connect_attributes.connect_attributes_dialogs import (
    AttributeBrowserDialog,
    ConnectionPreviewDialog,
)


class ConnectAttributesView(metaclass=qt_utils.MayaWindowMeta):
    """Compact interface for building or removing attribute connections."""

    def __init__(self, parent=None, version=None):
        """Initializes the view with minimal external state.

        Args:
            parent (QWidget, optional): Parent Maya window.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        title = "Connect Attributes"
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_connect_attributes))
        self.setStyleSheet(
            ui_res_lib.Stylesheet.maya_dialog_base + ui_res_lib.Stylesheet.combobox_base
            + "QPushButton { padding: 7px 12px; }"
        )
        self._child_dialogs = []
        self._build_widgets()
        self.set_loaded_nodes(None, [])
        self.update_enabled_state(True, True, False, False)
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds the main layout and common actions."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 14)
        main_layout.setSpacing(12)
        self.menu_bar = ui_qt.QtWidgets.QMenuBar()
        self.settings_menu = self.menu_bar.addMenu("Settings")
        self.reset_action = self.settings_menu.addAction("Reset Settings")
        self.help_menu = self.menu_bar.addMenu("Help")
        self.help_action = self.help_menu.addAction("How to Use")
        main_layout.addWidget(self.menu_bar)
        operation_layout = ui_qt.QtWidgets.QHBoxLayout()
        operation_layout.setSpacing(0)
        operation_layout.addWidget(ui_qt.QtWidgets.QLabel("Operation"))
        operation_layout.addStretch(1)
        self.connect_radio = ui_qt.QtWidgets.QRadioButton("Connect")
        self.disconnect_radio = ui_qt.QtWidgets.QRadioButton("Disconnect incoming")
        self.operation_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.operation_group.addButton(self.connect_radio)
        self.operation_group.addButton(self.disconnect_radio)
        self.connect_radio.setChecked(True)
        operation_layout.addWidget(self.connect_radio)
        operation_layout.addStretch(1)
        operation_layout.addWidget(self.disconnect_radio)
        main_layout.addLayout(operation_layout)
        main_layout.addWidget(self._build_objects())
        main_layout.addWidget(self._build_attributes())
        main_layout.addWidget(self._build_options())
        self.status_label = ui_qt.QtWidgets.QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(32)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.set_status("Ready")
        main_layout.addWidget(self.status_label)
        action_layout = ui_qt.QtWidgets.QHBoxLayout()
        action_layout.setSpacing(10)
        self.preview_button = ui_qt.QtWidgets.QPushButton("Preview")
        self.run_button = ui_qt.QtWidgets.QPushButton("Connect Attributes")
        self.preview_button.setStyleSheet("QPushButton { padding: 15px 28px; }")
        self.run_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        action_button_height = max(
            38, self.preview_button.sizeHint().height(), self.run_button.sizeHint().height(),
        )
        for button in (self.preview_button, self.run_button):
            button.setMinimumHeight(action_button_height)
            button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        action_layout.addWidget(self.preview_button, 1)
        action_layout.addWidget(self.run_button, 2)
        main_layout.addLayout(action_layout, 1)

    def _build_objects(self):
        """Builds object modes and the conditionally visible loading controls.

        Returns:
            QGroupBox: Objects section.
        """
        group = ui_qt.QtWidgets.QGroupBox("Objects")
        layout = ui_qt.QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        modes = ui_qt.QtWidgets.QHBoxLayout()
        self.current_selection_radio = ui_qt.QtWidgets.QRadioButton("Current Selection")
        self.loaded_objects_radio = ui_qt.QtWidgets.QRadioButton("Loaded Objects")
        self.object_mode_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.object_mode_group.addButton(self.current_selection_radio)
        self.object_mode_group.addButton(self.loaded_objects_radio)
        self.current_selection_radio.setChecked(True)
        self.use_selection_checkbox = self.current_selection_radio
        self.current_selection_radio.setToolTip("Reads selection when Preview, Refresh or Run is clicked.")
        modes.addWidget(self.current_selection_radio, 1)
        modes.addWidget(self.loaded_objects_radio, 1)
        layout.addLayout(modes)
        self.selection_hint = ui_qt.QtWidgets.QLabel()
        self.selection_hint.setWordWrap(True)
        self.selection_hint.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.selection_hint.setStyleSheet("font-weight: normal; color: #B8B8B8;")
        layout.addWidget(self.selection_hint)
        self.loaded_controls = ui_qt.QtWidgets.QWidget()
        load_layout = ui_qt.QtWidgets.QGridLayout(self.loaded_controls)
        load_layout.setContentsMargins(0, 0, 0, 0)
        load_layout.setHorizontalSpacing(8)
        load_layout.setVerticalSpacing(8)
        self.load_source_button = ui_qt.QtWidgets.QPushButton("Load Selected Source")
        self.load_targets_button = ui_qt.QtWidgets.QPushButton("Load Selected Targets")
        self.source_status_label = ui_qt.QtWidgets.QPushButton("No source loaded")
        self.target_status_label = ui_qt.QtWidgets.QPushButton("No targets loaded")
        for button in (self.source_status_label, self.target_status_label):
            button.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Ignored, ui_qt.QtWidgets.QSizePolicy.Preferred)
            button.setMinimumWidth(0)
        load_layout.addWidget(self.load_source_button, 0, 0)
        load_layout.addWidget(self.source_status_label, 0, 1)
        load_layout.addWidget(self.load_targets_button, 1, 0)
        load_layout.addWidget(self.target_status_label, 1, 1)
        load_layout.setColumnStretch(1, 1)
        layout.addWidget(self.loaded_controls)
        return group

    def _build_attributes(self):
        """Builds attribute fields with contextual pickers.

        Returns:
            QGroupBox: Attributes section.
        """
        group = ui_qt.QtWidgets.QGroupBox("Attributes")
        layout = ui_qt.QtWidgets.QGridLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)
        self.source_attribute_label = ui_qt.QtWidgets.QLabel("Source")
        self.source_attribute_field = ui_qt.QtWidgets.QLineEdit()
        self.source_attribute_field.setPlaceholderText("e.g. translateX")
        self.source_attribute_field.setToolTip("One output attribute on the source object.")
        self.target_attributes_field = ui_qt.QtWidgets.QLineEdit()
        self.target_attributes_field.setPlaceholderText("e.g. translateX, visibility")
        self.target_attributes_field.setToolTip(
            "Existing attribute names applied to every target, separated by commas."
        )
        self.source_browse_button = ui_qt.QtWidgets.QPushButton("Browse...")
        self.target_browse_button = ui_qt.QtWidgets.QPushButton("Browse...")
        self.source_browse_button.setToolTip("Choose an existing source attribute name.")
        self.target_browse_button.setToolTip("Add existing target attribute names to the field.")
        layout.addWidget(self.source_attribute_label, 0, 0)
        layout.addWidget(self.source_attribute_field, 0, 1)
        layout.addWidget(self.source_browse_button, 0, 2)
        layout.addWidget(ui_qt.QtWidgets.QLabel("Targets"), 1, 0)
        layout.addWidget(self.target_attributes_field, 1, 1)
        layout.addWidget(self.target_browse_button, 1, 2)
        layout.setColumnStretch(1, 1)
        return group

    def _build_options(self):
        """Builds common options and a collapsible advanced area.

        Returns:
            QWidget: Collapsible advanced options section.
        """
        self.options_group = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(self.options_group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.force_checkbox = ui_qt.QtWidgets.QCheckBox("Replace existing incoming connections")
        self.force_checkbox.setToolTip("Allows Maya to replace existing inputs. Preview identifies affected plugs.")
        self.advanced_toggle = ui_qt.QtWidgets.QPushButton("Show Advanced")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setToolTip("Show replacement, math/logic and shared-input settings.")
        layout.addWidget(self.advanced_toggle)
        self.advanced_content = ui_qt.QtWidgets.QWidget()
        advanced_layout = ui_qt.QtWidgets.QGridLayout(self.advanced_content)
        advanced_layout.setContentsMargins(12, 4, 12, 4)
        advanced_layout.setHorizontalSpacing(10)
        advanced_layout.setVerticalSpacing(9)
        self.reverse_checkbox = ui_qt.QtWidgets.QCheckBox("Invert value (1 - input)")
        self.reverse_checkbox.setToolTip("Insert a Maya Reverse node: for example, 0.2 becomes 0.8.")
        self.utility_checkbox = ui_qt.QtWidgets.QCheckBox("Insert math/logic node")
        self.utility_checkbox.setToolTip("Create one utility node for each target attribute connection.")
        self.utility_combo = ui_qt.QtWidgets.QComboBox()
        self.utility_combo.addItems(["plusMinusAverage", "multiplyDivide", "condition"])
        self.utility_combo.setToolTip("Maya node type inserted between the source and each target.")
        self.shared_input_checkbox = ui_qt.QtWidgets.QCheckBox("Share a secondary input")
        self.shared_input_checkbox.setToolTip(
            "Create one shared node and connect its output to the secondary input of every utility node."
        )
        self.shared_input_combo = ui_qt.QtWidgets.QComboBox()
        self.shared_input_combo.addItems(["condition", "multiplyDivide", "plusMinusAverage"])
        advanced_layout.addWidget(self.force_checkbox, 0, 0, 1, 2)
        advanced_layout.addWidget(self.reverse_checkbox, 1, 0, 1, 2)
        advanced_layout.addWidget(self.utility_checkbox, 2, 0)
        advanced_layout.addWidget(self.utility_combo, 2, 1)
        advanced_layout.addWidget(self.shared_input_checkbox, 3, 0)
        advanced_layout.addWidget(self.shared_input_combo, 3, 1)
        advanced_layout.setColumnStretch(1, 1)
        layout.addWidget(self.advanced_content)
        self.advanced_toggle.toggled.connect(self._update_advanced)
        self._update_advanced(False)
        return self.options_group

    def _update_advanced(self, expanded):
        """Updates the advanced section without rebuilding its controls.

        Args:
            expanded (bool): Whether the advanced controls are visible.
        """
        self.advanced_content.setVisible(expanded)
        active = (
            self.force_checkbox.isChecked() or self.reverse_checkbox.isChecked()
            or self.utility_checkbox.isChecked()
        )
        suffix = " (options active)" if active and not expanded else ""
        self.advanced_toggle.setText(f"{'Hide' if expanded else 'Show'} Advanced{suffix}")

    def set_loaded_nodes(self, source_object, target_objects):
        """Updates clickable loaded-object summaries.

        Args:
            source_object (str or None): Loaded source node.
            target_objects (list): Loaded target nodes.
        """
        source_text = source_object.rsplit("|", 1)[-1] if source_object else "No source loaded"
        targets = target_objects or []
        target_text = targets[0].rsplit("|", 1)[-1] if len(targets) == 1 else f"{len(targets)} targets loaded"
        if not targets:
            target_text = "No targets loaded"
        self.source_status_label.setText(source_text)
        self.source_status_label.setToolTip(f"Click to select: {source_object}" if source_object else source_text)
        self.target_status_label.setText(target_text)
        self.target_status_label.setToolTip("\n".join(targets) or "No targets loaded")
        self._style_loaded_button(self.source_status_label, bool(source_object))
        self._style_loaded_button(self.target_status_label, bool(targets))

    @staticmethod
    def _style_loaded_button(button, has_objects):
        """Styles defined slots green and empty or inactive slots gray.

        Args:
            button (QPushButton): Loaded-object summary button.
            has_objects (bool): Whether objects have been defined for this slot.
        """
        background = "#406449" if has_objects else "#333333"
        hover = "#4A7354" if has_objects else "#3D3D3D"
        button.setStyleSheet(
            f"QPushButton {{ background-color: {background}; color: #EEEEEE; padding: 7px 12px; }}"
            f"QPushButton:hover:enabled {{ background-color: {hover}; }}"
            "QPushButton:disabled { background-color: #4B4B4B; color: #929292; }"
        )

    def update_enabled_state(self, use_selection, is_connect, use_utility, use_shared_input):
        """Updates visibility and enabled controls for the current operation.

        Args:
            use_selection (bool): Whether selection is read at action time.
            is_connect (bool): Whether the operation is Connect.
            use_utility (bool): Whether a utility node is enabled.
            use_shared_input (bool): Whether a shared secondary input is enabled.
        """
        self.loaded_controls.setVisible(not use_selection)
        self.load_source_button.setEnabled(not use_selection and is_connect)
        self.source_status_label.setEnabled(not use_selection and is_connect)
        self.load_targets_button.setEnabled(not use_selection)
        self.target_status_label.setEnabled(not use_selection)
        self.selection_hint.setVisible(use_selection)
        self.selection_hint.setText(
            "Select the source first, then the targets." if is_connect
            else "Select the objects whose incoming connections should be removed."
        )
        for widget in (self.load_source_button, self.source_status_label):
            widget.setVisible(is_connect)
        for widget in (
            self.source_attribute_label, self.source_attribute_field, self.source_browse_button,
        ):
            widget.setVisible(is_connect)
        self.options_group.setVisible(is_connect)
        self.utility_combo.setEnabled(use_utility)
        self.shared_input_checkbox.setEnabled(use_utility)
        self.shared_input_combo.setEnabled(use_utility and use_shared_input)
        self._update_advanced(self.advanced_toggle.isChecked())
        self.run_button.setText("Connect Attributes" if is_connect else "Disconnect Incoming")

    def set_status(self, message, level="info"):
        """Shows concise feedback at the bottom of the window.

        Args:
            message (str): Status text.
            level (str, optional): Info, success, warning or error severity.
        """
        colors = {"info": "#B8B8B8", "success": "#8BCB88", "warning": "#E2BE72", "error": "#E58A8A"}
        self.status_label.setStyleSheet(
            "QLabel { background-color: #2D2D2D; border: 1px solid #484848; "
            "border-radius: 6px; padding: 6px 10px; "
            f"color: {colors.get(level, colors['info'])}; }}"
        )
        self.status_label.setText(message)

    def show_attribute_browser(self, node, attributes, keyable=False, role="copy", nodes=None):
        """Shows existing attribute names in a contextual browser.

        Args:
            node (str): Initially inspected node.
            attributes (list): Initially available attribute names.
            keyable (bool, optional): Whether the initial list is keyable-only.
            role (str, optional): Source, target or legacy copy-only behavior.
            nodes (list, optional): Objects available in the object selector.

        Returns:
            AttributeBrowserDialog: Browser for controller signal bindings.
        """
        dialog = AttributeBrowserDialog(nodes or [node], role=role, keyable=keyable, parent=self)
        dialog.node_combo.setCurrentText(node)
        dialog.set_attributes(attributes)
        self._track_dialog(dialog)
        return dialog

    def show_operation_preview(self, rows, request):
        """Shows inspected operations in a read-only table.

        Args:
            rows (list): Structured operation rows.
            request (dict): Normalized request used for the snapshot.

        Returns:
            ConnectionPreviewDialog: Preview for refresh bindings.
        """
        dialog = ConnectionPreviewDialog(parent=self)
        dialog.set_preview(rows, request)
        self._track_dialog(dialog)
        return dialog

    def show_connection_preview(self, preview_lines, operation, shared_input_type=None):
        """Preserves the previous text-preview entry point using the table dialog.

        Args:
            preview_lines (list): Legacy human-readable preview strings.
            operation (str): Connect or disconnect operation.
            shared_input_type (str, optional): Shared secondary-input node type.

        Returns:
            ConnectionPreviewDialog: Read-only preview dialog.
        """
        rows = [
            {"source": "", "target": "", "via": "", "status": "warning", "details": line}
            for line in preview_lines
        ]
        request = {"operation": operation, "shared_input_node_type": shared_input_type}
        return self.show_operation_preview(rows, request)

    def _track_dialog(self, dialog):
        """Retains a non-modal dialog until Qt destroys it.

        Args:
            dialog (QDialog): Child dialog to retain and show.
        """
        self._child_dialogs.append(dialog)
        dialog.destroyed.connect(lambda *args: self._remove_child_dialog(dialog))
        dialog.show()

    def _remove_child_dialog(self, dialog):
        """Drops a closed child dialog reference.

        Args:
            dialog (QDialog): Dialog being removed.
        """
        if dialog in self._child_dialogs:
            self._child_dialogs.remove(dialog)

    def show_help(self):
        """Shows concise usage guidance."""
        ui_qt.QtWidgets.QMessageBox.information(
            self, "Connect Attributes Help",
            "Current Selection reads objects when Preview, Refresh or Run is clicked. "
            "Select the source first, then targets.\n\n"
            "Loaded Objects keeps a source and target list for repeated operations. "
            "Switching modes preserves loaded objects.\n\n"
            "Browse chooses existing attribute names for the fields. Target names apply to every target. "
            "Preview reports missing, locked and conflicting attributes without changing the scene.\n\n"
            "Run rechecks the scene and runs available operations, reporting blocked items.\n\n"
            "Disconnect Incoming treats every selected or loaded target as a target. "
            "Advanced options insert math/logic nodes; Invert computes 1 minus the input.",
        )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = ConnectAttributesView()
        window.show()
