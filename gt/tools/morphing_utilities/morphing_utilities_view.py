"""Responsive Qt view for Morphing Utilities."""

import gt.ui.qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library as ui_res_lib
from gt.ui.qt_utils import MayaWindowMeta


class ResponsiveButton(ui_qt.QtWidgets.QPushButton):
    """Push button that allows its layout column to shrink with the window."""

    def minimumSizeHint(self):
        """Keeps height constraints while allowing horizontal compression.

        Returns:
            QSize: Minimum height with no artificial text-width constraint.
        """
        size = super().minimumSizeHint()
        size.setWidth(0)
        return size


class MorphingUtilitiesView(metaclass=MayaWindowMeta):
    """Dockable Morphing Utilities interface."""

    def __init__(self, parent=None, version=None):
        """Initializes the dockable window.

        Args:
            parent (QWidget, optional): Maya main window parent.
            version (str, optional): Version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.version = version
        title = "Morphing Utilities"
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_morphing_utils))
        self.setMinimumWidth(340)
        self.resize(410, 720)
        self._build_widgets()
        self._apply_stylesheet()

    def _build_widgets(self):
        """Builds the responsive widget hierarchy."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        main_layout.addWidget(self._build_section_label("General Utilities:"))
        general_layout = ui_qt.QtWidgets.QHBoxLayout()
        general_layout.setSpacing(6)
        self.delete_all_nodes_button = self._create_button(
            "Delete All\nBlend Shape Nodes", "actionButton"
        )
        self.delete_all_targets_button = self._create_button(
            "Delete All\nBlend Shape Targets", "actionButton"
        )
        self.delete_all_nodes_button.setFixedHeight(40)
        self.delete_all_targets_button.setFixedHeight(40)
        general_layout.addWidget(self.delete_all_nodes_button, 1)
        general_layout.addWidget(self.delete_all_targets_button, 1)
        main_layout.addLayout(general_layout)

        main_layout.addWidget(self._build_section_label("Deformed Mesh (Source):"))
        source_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        source_buttons_layout.setSpacing(6)
        self.load_source_button = self._create_button(
            "Load Morphing Object", "actionButton"
        )
        self.source_status_button = self._create_button(
            "Not loaded yet", "statusButton"
        )
        self.source_status_button.setToolTip("Select the loaded source object in Maya.")
        source_buttons_layout.addWidget(self.load_source_button, 1)
        source_buttons_layout.addWidget(self.source_status_button, 1)
        main_layout.addLayout(source_buttons_layout)

        node_label = ui_qt.QtWidgets.QLabel("Blend Shape Nodes:")
        node_label.setObjectName("hintLabel")
        self.blend_node_list = ui_qt.QtWidgets.QListWidget()
        self.blend_node_list.setSelectionMode(ui_qt.QtLib.SelectionMode.SingleSelection)
        self.blend_node_list.setMinimumHeight(70)
        self.blend_node_list.setToolTip(
            "Blend shape nodes found on the loaded morphing object."
        )
        self.blend_node_list.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Expanding,
        )
        self.target_summary_label = ui_qt.QtWidgets.QLabel(
            "No blend shape node selected."
        )
        self.target_summary_label.setObjectName("hintLabel")
        self.target_summary_label.setWordWrap(True)
        main_layout.addWidget(node_label)
        main_layout.addWidget(self.blend_node_list, 1)
        main_layout.addWidget(self.target_summary_label)

        main_layout.addWidget(
            self._build_separator("Search and Replace Target Names:")
        )
        search_layout = ui_qt.QtWidgets.QGridLayout()
        search_layout.setContentsMargins(6, 2, 6, 2)
        search_layout.setHorizontalSpacing(8)
        search_layout.setVerticalSpacing(4)
        search_label = ui_qt.QtWidgets.QLabel("Search:")
        replace_label = ui_qt.QtWidgets.QLabel("Replace:")
        search_label.setAlignment(
            ui_qt.QtLib.AlignmentFlag.AlignRight | ui_qt.QtLib.AlignmentFlag.AlignVCenter
        )
        replace_label.setAlignment(
            ui_qt.QtLib.AlignmentFlag.AlignRight | ui_qt.QtLib.AlignmentFlag.AlignVCenter
        )
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Text Search")
        self.replace_field = ui_qt.QtWidgets.QLineEdit()
        self.replace_field.setPlaceholderText("Text Replace")
        search_layout.addWidget(search_label, 0, 0)
        search_layout.addWidget(self.search_field, 0, 1)
        search_layout.addWidget(replace_label, 1, 0)
        search_layout.addWidget(self.replace_field, 1, 1)
        search_layout.setColumnStretch(1, 1)
        main_layout.addLayout(search_layout)
        self.rename_button = self._create_button(
            "Search Replace Target Names", "primaryButton"
        )
        main_layout.addWidget(self.rename_button)

        mirror_options_layout = ui_qt.QtWidgets.QGridLayout()
        mirror_options_layout.setContentsMargins(6, 2, 6, 2)
        mirror_options_layout.setHorizontalSpacing(8)
        mirror_direction_label = ui_qt.QtWidgets.QLabel("Mirror Direction:")
        mirror_direction_label.setObjectName("hintLabel")
        mirror_options_layout.addWidget(mirror_direction_label, 0, 0)
        self.mirror_direction_combo = ui_qt.QtWidgets.QComboBox()
        self.mirror_direction_combo.addItems(["-", "+"])
        mirror_options_layout.addWidget(self.mirror_direction_combo, 0, 1)
        symmetry_axis_label = ui_qt.QtWidgets.QLabel("Symmetry Axis:")
        symmetry_axis_label.setObjectName("hintLabel")
        mirror_options_layout.addWidget(symmetry_axis_label, 0, 2)
        self.symmetry_axis_combo = ui_qt.QtWidgets.QComboBox()
        self.symmetry_axis_combo.addItems(["x", "y", "z"])
        mirror_options_layout.addWidget(self.symmetry_axis_combo, 0, 3)
        mirror_options_layout.setColumnStretch(1, 1)
        mirror_options_layout.setColumnStretch(3, 1)
        main_layout.addLayout(mirror_options_layout)

        operation_layout = ui_qt.QtWidgets.QGridLayout()
        operation_layout.setContentsMargins(6, 0, 6, 0)
        operation_layout.setHorizontalSpacing(6)
        self.flip_button = self._create_button(
            "Search, Duplicating Flipping", "darkButton"
        )
        self.flip_help_button = self._create_button("?", "darkButton")
        self.flip_help_button.setFixedWidth(28)
        self.mirror_button = self._create_button(
            "Search, Duplicating Mirroring", "darkButton"
        )
        self.mirror_help_button = self._create_button("?", "darkButton")
        self.mirror_help_button.setFixedWidth(28)
        operation_layout.addWidget(self.flip_button, 0, 0)
        operation_layout.addWidget(self.flip_help_button, 0, 1)
        operation_layout.addWidget(self.mirror_button, 1, 0)
        operation_layout.addWidget(self.mirror_help_button, 1, 1)
        operation_layout.setColumnStretch(0, 1)
        main_layout.addLayout(operation_layout)

        main_layout.addWidget(self._build_line())
        values_layout = ui_qt.QtWidgets.QGridLayout()
        values_layout.setContentsMargins(6, 2, 6, 2)
        values_layout.setHorizontalSpacing(8)
        self.set_values_button = self._create_button(
            "Set All Target Values To", "primaryButton"
        )
        self.target_value_spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        self.target_value_spinbox.setRange(-1000000.0, 1000000.0)
        self.target_value_spinbox.setDecimals(3)
        self.target_value_spinbox.setSingleStep(0.1)
        self.target_value_spinbox.setValue(1.0)
        self.target_value_spinbox.setFixedWidth(75)
        self.extract_button = self._create_button(
            "Extract Targets Current Values", "primaryButton"
        )
        values_layout.addWidget(self.set_values_button, 0, 0)
        values_layout.addWidget(self.target_value_spinbox, 0, 1)
        values_layout.addWidget(self.extract_button, 1, 0, 1, 2)
        values_layout.setColumnStretch(0, 1)
        main_layout.addLayout(values_layout)

        self.status_label = ui_qt.QtWidgets.QLabel("Load a source mesh to begin.")
        self.status_label.setObjectName("hintLabel")
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        self._target_widgets = [
            self.rename_button,
            self.flip_button,
            self.mirror_button,
            self.set_values_button,
            self.extract_button,
            self.target_value_spinbox,
            self.mirror_direction_combo,
            self.symmetry_axis_combo,
        ]
        self.blend_node_list.setEnabled(False)
        self.set_target_operations_enabled(False)

    @staticmethod
    def _build_section_label(text):
        """Builds a centered section heading.

        Args:
            text (str): Section text.

        Returns:
            QLabel: Configured section label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("sectionHeader")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        return label

    @staticmethod
    def _build_separator(text):
        """Builds a centered heading with horizontal rules.

        Args:
            text (str): Separator heading.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(7)
        left_line = ui_qt.QtWidgets.QFrame()
        right_line = ui_qt.QtWidgets.QFrame()
        for line in (left_line, right_line):
            line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
            line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("sectionLabel")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    @staticmethod
    def _build_line():
        """Builds a horizontal separator line.

        Returns:
            QFrame: Horizontal sunken line.
        """
        line = ui_qt.QtWidgets.QFrame()
        line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
        line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        return line

    @staticmethod
    def _create_button(text, object_name):
        """Creates a stretchable tool button.

        Args:
            text (str): Button label.
            object_name (str): Style object name.

        Returns:
            QPushButton: Configured button.
        """
        button = ResponsiveButton(text)
        button.setObjectName(object_name)
        button.setMinimumWidth(0)
        button_font = button.font()
        button_font.setPointSize(8)
        button.setFont(button_font)
        button.setFixedHeight(28)
        button.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Fixed,
        )
        return button

    def _apply_stylesheet(self):
        """Applies repository styles and legacy-inspired button colors."""
        stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        stylesheet += ui_res_lib.Stylesheet.spin_box_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        stylesheet += ui_res_lib.Stylesheet.btn_push_base
        stylesheet += """
            QLabel#sectionHeader {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 9px;
            }
            QLabel#sectionLabel, QLabel#hintLabel {
                color: #AAAAAA;
                font-size: 9px;
                font-weight: normal;
            }
            QLabel#hintLabel {
                color: #AAAAAA;
            }
            QPushButton#actionButton {
                background-color: #5C5C5C;
                border: 1px solid #444444;
                color: #DDDDDD;
                padding: 2px 6px;
            }
            QPushButton#actionButton:hover {
                background-color: #696969;
            }
            QPushButton#actionButton:pressed {
                background-color: #4B4B4B;
            }
            QPushButton#darkButton {
                background-color: #4D4D4D;
                border: 1px solid #333333;
                color: #FFFFFF;
                padding: 2px 6px;
            }
            QPushButton#darkButton:hover {
                background-color: #626262;
            }
            QPushButton#darkButton:pressed {
                background-color: #3A3A3A;
            }
            QPushButton#primaryButton {
                background-color: #999999;
                border: 1px solid #444444;
                color: #202020;
                padding: 2px 6px;
            }
            QPushButton#primaryButton:hover {
                background-color: #B0B0B0;
            }
            QPushButton#primaryButton:pressed {
                background-color: #7A7A7A;
            }
            QPushButton#statusButton {
                background-color: #333333;
                border: 1px solid #444444;
                color: #DDDDDD;
                padding: 2px 6px;
            }
            QPushButton#statusButton[state="loaded"] {
                background-color: #99CC99;
                color: #1C1C1C;
            }
            QPushButton#statusButton[state="failed"] {
                background-color: #FF6666;
                color: #1C1C1C;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #292929;
                border: 1px solid #444444;
            }
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
            QComboBox:disabled {
                background-color: #353535;
                color: #707070;
            }
            QListWidget {
                background-color: #292929;
                border: 1px solid #444444;
            }
        """
        self.setStyleSheet(stylesheet)

    def set_target_operations_enabled(self, enabled):
        """Enables or disables controls requiring a selected blend node.

        Args:
            enabled (bool): Whether a valid blend shape node is selected.
        """
        for widget in self._target_widgets:
            widget.setEnabled(bool(enabled))

    def set_source_status(self, text, state="neutral"):
        """Updates the source-object status button.

        Args:
            text (str): Visible status text.
            state (str): One of ``neutral``, ``loaded``, or ``failed``.
        """
        self.source_status_button.setText(text)
        self.source_status_button.setProperty("state", state)
        style = self.source_status_button.style()
        style.unpolish(self.source_status_button)
        style.polish(self.source_status_button)
        self.source_status_button.setToolTip(text)

    def set_blend_nodes(self, blend_nodes, selected_node=None):
        """Replaces the blend shape node list.

        Args:
            blend_nodes (list): Node names to display.
            selected_node (str, optional): Node to select after population.
        """
        self.blend_node_list.blockSignals(True)
        self.blend_node_list.clear()
        self.blend_node_list.addItems(blend_nodes or [])
        self.blend_node_list.setEnabled(bool(blend_nodes))
        if selected_node:
            for index in range(self.blend_node_list.count()):
                item = self.blend_node_list.item(index)
                if item.text() == selected_node:
                    self.blend_node_list.setCurrentItem(item)
                    break
        self.blend_node_list.blockSignals(False)

    def set_target_summary(self, target_count, node_name=None):
        """Updates the target count below the blend shape list.

        Args:
            target_count (int): Number of targets on the selected node.
            node_name (str, optional): Selected node name.
        """
        if not node_name:
            message = "No blend shape node selected."
        else:
            noun = "target" if target_count == 1 else "targets"
            message = f"{node_name}: {target_count} {noun}"
        self.target_summary_label.setText(message)

    def set_status(self, message, level="info"):
        """Updates the bottom status message.

        Args:
            message (str): Message to display.
            level (str): One of ``info``, ``success``, ``warning``, or ``error``.
        """
        colors = {
            "info": "#BBBBBB",
            "success": "#8BCB88",
            "warning": "#E2BE72",
            "error": "#FF7777",
        }
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {colors.get(level, colors['info'])};")

    def confirm_action(self, title, message):
        """Asks for confirmation before a destructive scene operation.

        Args:
            title (str): Dialog title.
            message (str): Confirmation message.

        Returns:
            bool: True when the user confirms.
        """
        answer = ui_qt.QtWidgets.QMessageBox.question(
            self,
            title,
            message,
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return answer == ui_qt.QtLib.StandardButton.Yes

    def show_help(self, topic=None):
        """Shows help for the main tool or a specific mirror operation.

        Args:
            topic (str, optional): ``flip`` or ``mirror`` for focused help.
        """
        if topic == "flip":
            title = "Duplicate Flip"
            message = (
                "Filters targets using Search, duplicates them, and flips the new targets "
                "across the selected symmetry axis. Replace controls the new aliases."
            )
        elif topic == "mirror":
            title = "Duplicate Mirror"
            message = (
                "Filters targets using Search, duplicates them, and mirrors the new targets "
                "across the selected axis and direction. Empty Replace adds a _Mirrored suffix."
            )
        else:
            title = "Morphing Utilities Help"
            message = (
                "Load a deformed mesh, choose one of its blend shape nodes, and use the "
                "operations below to rename, flip, mirror, set, or extract targets.\n\n"
                "All scene-changing actions are grouped into one Maya undo step. Existing "
                "target aliases are never overwritten; generated duplicates receive a suffix "
                "when needed."
            )
        ui_qt.QtWidgets.QMessageBox.information(self, title, message)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext() as context:
        window = MorphingUtilitiesView(parent=context.get_parent(), version="2.0.0")
        window.show()
