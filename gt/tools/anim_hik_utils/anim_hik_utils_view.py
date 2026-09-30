"""Compact, dockable HumanIK Utilities view using the shared Qt abstraction."""

from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library as ui_res_lib


class AnimHikUtilsView(metaclass=qt_utils.MayaWindowMeta):
    """Constructs widgets independently of Maya scene data and controller state."""

    def __init__(self, parent=None, version=None):
        """Builds the HumanIK window.

        Args:
            parent (QWidget, optional): Maya parent window.
            version (str, optional): Version shown in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.buttons = {}
        self.target_buttons = []
        self.settings_widgets = {}
        self.setWindowTitle("HumanIK Utilities" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_anim_hik_utils))
        self.setStyleSheet("\n".join((
            ui_res_lib.Stylesheet.maya_dialog_base,
            ui_res_lib.Stylesheet.checkbox_base,
            ui_res_lib.Stylesheet.tab_widget_base,
            ui_res_lib.Stylesheet.scroll_bar_base,
            "QWidget { color: #DDDDDD; } QLabel { font-weight: 400; } "
            "QPlainTextEdit { background-color: #2B2B2B; color: #DDDDDD; } "
            "QGroupBox { margin-top: 12px; padding-top: 8px; }",
        )))
        self.setMinimumWidth(440)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        header = ui_qt.QtWidgets.QHBoxLayout()
        title = ui_qt.QtWidgets.QLabel("HumanIK Utilities")
        title.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))
        header.addWidget(title, 1)
        header.addWidget(self.button("reset", "Reset Options", "Restore tool settings.", target=False))
        layout.addLayout(header)
        characters = ui_qt.QtWidgets.QHBoxLayout()
        characters.addWidget(ui_qt.QtWidgets.QLabel("Character:"))
        self.character_combo = ui_qt.QtWidgets.QComboBox()
        self.character_combo.setMinimumContentsLength(12)
        self.character_combo.setSizeAdjustPolicy(
            ui_qt.QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.character_combo.setToolTip("Every action targets this exact HumanIK definition, including its namespace.")
        characters.addWidget(self.character_combo, 1)
        characters.addWidget(self.button("refresh", "Refresh", "Rescan the scene after scene changes.", target=False))
        layout.addLayout(characters)
        self.character_summary = ui_qt.QtWidgets.QLabel("Choose a HumanIK character or create a definition.")
        self.character_summary.setWordWrap(True)
        layout.addWidget(self.character_summary)
        self.tabs = ui_qt.QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.build_pose_tab()
        self.build_definition_tab()
        self.build_retarget_tab()
        self.build_inspect_tab()
        self.status_label = ui_qt.QtWidgets.QLabel("Ready. Refresh after opening or changing a scene.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(36)
        layout.addWidget(self.status_label)
        self.resize(520, 590)
        qt_utils.center_window(self)

    def button(self, key, label, tooltip, target=True):
        """Creates and registers an action button.

        Args:
            key (str): Controller action identifier.
            label (str): Visible button text.
            tooltip (str): User-facing explanation.
            target (bool): Whether the action requires a selected character.

        Returns:
            QPushButton: Registered button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setToolTip(tooltip)
        self.buttons[key] = button
        if target:
            self.target_buttons.append(button)
        return button

    def tab_layout(self, title):
        """Creates a scrollable tab that fits smaller screens.

        Args:
            title (str): Tab label.

        Returns:
            QVBoxLayout: Content layout.
        """
        scroll = ui_qt.QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        contents = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(contents)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        scroll.setWidget(contents)
        self.tabs.addTab(scroll, title)
        return layout

    def note(self, layout, text):
        """Adds wrapping instructional text.

        Args:
            layout (QLayout): Destination layout.
            text (str): Instruction text.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)

    def check_option(self, layout, key, label, tooltip):
        """Creates a persistent checkbox option.

        Args:
            layout (QLayout): Destination layout.
            key (str): Model setting identifier.
            label (str): Visible label.
            tooltip (str): Setting explanation.
        """
        checkbox = ui_qt.QtWidgets.QCheckBox(label)
        checkbox.setToolTip(tooltip)
        self.settings_widgets[key] = checkbox
        layout.addWidget(checkbox)

    def build_pose_tab(self):
        """Builds current-pose mirror, flip, and file actions."""
        layout = self.tab_layout("Pose")
        self.note(layout, "Mirror the current pose of a generated HumanIK control rig. "
                  "Includes mapped fingers, toes, and effectors. No keys are added; key the result when needed.")
        options_row = ui_qt.QtWidgets.QHBoxLayout()
        self.check_option(options_row, "affect_center", "Include center controls",
                          "Also reflect center controls in place. Off preserves the character's center pose.")
        self.check_option(options_row, "world_space", "Use world space",
                          "Mirror and export world matrices. The Reference control defines the mirror plane "
                          "when available. Off uses local space. Pose import always uses the file's saved space.")
        layout.addLayout(options_row)
        mirror_row = ui_qt.QtWidgets.QHBoxLayout()
        mirror_row.addWidget(self.button(
            "mirror_left", "Left to Right", "Copy and mirror the left pose onto the right."
        ))
        mirror_row.addWidget(self.button(
            "mirror_right", "Right to Left", "Copy and mirror the right pose onto the left."
        ))
        layout.addLayout(mirror_row)
        layout.addWidget(self.button("flip", "Flip Pose", "Swap and mirror both sides from the same captured pose."))
        files = ui_qt.QtWidgets.QHBoxLayout()
        files.addWidget(self.button(
            "export_pose", "Export Pose...", "Save a portable pose using stable HIK control IDs."
        ))
        files.addWidget(self.button(
            "import_pose", "Import Pose...", "Apply a saved pose using the file's coordinate space."
        ))
        layout.addLayout(files)
        layout.addWidget(self.button(
            "select_controls", "Select Control Rig Controls", "Select all mapped HIK controls."
        ))
        self.build_animation_controls(layout)
        layout.addStretch()

    def build_animation_controls(self, layout):
        """Adds sampled animation actions alongside the current-frame pose tools.

        Args:
            layout (QVBoxLayout): Pose tab layout.
        """
        group = ui_qt.QtWidgets.QGroupBox("Animation")
        contents = ui_qt.QtWidgets.QVBoxLayout(group)
        self.note(contents, "Mirror or flip baked control-rig animation using the options above. "
                  "Replaces keys within the range with sampled keys; outside keys are kept.")
        range_row = ui_qt.QtWidgets.QHBoxLayout()
        self.animation_range_mode = ui_qt.QtWidgets.QComboBox()
        self.animation_range_mode.addItems(["Playback range", "Custom range"])
        range_row.addWidget(self.animation_range_mode)
        range_row.addWidget(self.button(
            "playback_range", "Use Playback Range", "Fill Start and End from Maya's playback range.", target=False
        ))
        contents.addLayout(range_row)
        values_row = ui_qt.QtWidgets.QHBoxLayout()
        self.animation_start = ui_qt.QtWidgets.QDoubleSpinBox()
        self.animation_end = ui_qt.QtWidgets.QDoubleSpinBox()
        self.animation_step = ui_qt.QtWidgets.QDoubleSpinBox()
        for widget, label, value in (
            (self.animation_start, "Start", 1), (self.animation_end, "End", 120),
            (self.animation_step, "Step", 1),
        ):
            widget.setDecimals(3)
            widget.setRange(0.001 if widget is self.animation_step else -10000000, 10000000)
            widget.setValue(value)
            widget.setMinimumWidth(65)
            values_row.addWidget(ui_qt.QtWidgets.QLabel(label))
            values_row.addWidget(widget, 1)
        self.animation_step.setToolTip(
            "Frames between samples. 1 keys every frame; fractional values sample subframes."
        )
        contents.addLayout(values_row)
        mirrors = ui_qt.QtWidgets.QHBoxLayout()
        mirrors.addWidget(self.button(
            "animation_left", "Left to Right...", "Mirror left-side animation onto the right."
        ))
        mirrors.addWidget(self.button(
            "animation_right", "Right to Left...", "Mirror right-side animation onto the left."
        ))
        contents.addLayout(mirrors)
        contents.addWidget(self.button(
            "animation_flip", "Flip Animation...", "Swap and mirror both sides of the clip."
        ))
        self.animation_range_mode.currentIndexChanged.connect(self.update_animation_range_mode)
        self.update_animation_range_mode()
        layout.addWidget(group)

    def update_animation_range_mode(self, *unused_args):
        """Enables custom range fields only when the user chooses Custom range.

        Args:
            *unused_args: Optional Qt signal arguments.
        """
        custom = self.animation_range_mode.currentIndex() == 1
        self.animation_start.setEnabled(custom)
        self.animation_end.setEnabled(custom)

    def set_animation_range(self, start, end):
        """Displays the current Maya playback range.

        Args:
            start (float): Playback start frame.
            end (float): Playback end frame.
        """
        self.animation_start.setValue(start)
        self.animation_end.setValue(end)

    def build_definition_tab(self):
        """Builds definition management and XML mapping options."""
        layout = self.tab_layout("Definition")
        name_row = ui_qt.QtWidgets.QHBoxLayout()
        self.name_field = ui_qt.QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Character name")
        self.name_field.setToolTip("New character or replacement name. Namespaces are allowed.")
        name_row.addWidget(self.name_field, 1)
        name_row.addWidget(self.button("create", "Create", "Create an empty HumanIK definition.", target=False))
        name_row.addWidget(self.button("rename", "Rename", "Rename the chosen definition."))
        layout.addLayout(name_row)
        locks = ui_qt.QtWidgets.QHBoxLayout()
        locks.addWidget(self.button(
            "lock", "Lock Definition", "Characterize the mapped skeleton in its reference pose."
        ))
        locks.addWidget(self.button(
            "unlock", "Unlock Definition", "Unlock the definition for editing bone assignments."
        ))
        layout.addLayout(locks)
        self.note(layout, "XML mapping uses Maya's HumanIK match-list format. Import updates populated slots "
                  "and leaves the definition unlocked for review. Preview all mappings before applying.")
        path_row = ui_qt.QtWidgets.QHBoxLayout()
        self.xml_path = ui_qt.QtWidgets.QLineEdit()
        self.xml_path.setPlaceholderText("HumanIK definition XML")
        path_row.addWidget(self.xml_path, 1)
        path_row.addWidget(self.button("browse_xml", "Browse...", "Choose a native HumanIK XML file.", target=False))
        layout.addLayout(path_row)
        form = ui_qt.QtWidgets.QFormLayout()
        form.setRowWrapPolicy(ui_qt.QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        for key, label, placeholder, tooltip in (
            ("prefix", "Prefix:", "e.g. hero:", "Add this text to XML bone names. Also used when exporting XML."),
            ("search_namespace", "Find namespace:", "e.g. source:", "Literal text to find after adding the prefix."),
            ("replace_namespace", "Replace with:", "e.g. target:",
             "Replacement text. Empty removes the matched text."),
        ):
            field = ui_qt.QtWidgets.QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setToolTip(tooltip)
            self.settings_widgets[key] = field
            form.addRow(label, field)
        layout.addLayout(form)
        mapping = ui_qt.QtWidgets.QHBoxLayout()
        mapping.addWidget(self.button(
            "detect_namespace", "Use Character Namespace", "Fill Prefix from the mapped skeleton."
        ))
        mapping.addWidget(self.button(
            "preview_xml", "Preview XML", "Check every populated mapping without changing the scene."
        ))
        layout.addLayout(mapping)
        files = ui_qt.QtWidgets.QHBoxLayout()
        files.addWidget(self.button("export_definition", "Export XML...", "Export the current bone mapping."))
        files.addWidget(self.button(
            "import_definition", "Import XML...", "Review and confirm replacing mapped slots."
        ))
        layout.addLayout(files)
        layout.addStretch()

    def build_retarget_tab(self):
        """Builds source assignment, property transfer, and bake controls."""
        layout = self.tab_layout("Retarget / Bake")
        source_row = ui_qt.QtWidgets.QHBoxLayout()
        self.source_combo = ui_qt.QtWidgets.QComboBox()
        self.source_combo.setMinimumContentsLength(10)
        self.source_combo.setSizeAdjustPolicy(
            ui_qt.QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.source_combo.setToolTip("Character whose animation will drive the selected target.")
        source_row.addWidget(self.source_combo, 1)
        source_row.addWidget(self.button(
            "source", "Assign Source", "Assign the chosen source to the target character."
        ))
        layout.addLayout(source_row)
        layout.addWidget(self.button(
            "stance", "Clear Source / Stance", "Disconnect the character input and return to stance."
        ))
        properties = ui_qt.QtWidgets.QGroupBox("Retarget Properties")
        property_layout = ui_qt.QtWidgets.QGridLayout(properties)
        for index, (key, label, tooltip) in enumerate((
            ("copy_properties", "Copy Properties", "Copy properties into this window's session clipboard."),
            ("paste_properties", "Paste Properties", "Apply copied properties to the selected character."),
            ("export_properties", "Export JSON...", "Export properties compatible with the batch HumanIK task."),
            ("import_properties", "Import JSON...",
             "Apply properties from a JSON dictionary; report skipped attributes."),
        )):
            property_layout.addWidget(self.button(key, label, tooltip), index // 2, index % 2)
        layout.addWidget(properties)
        self.note(layout, "Baking uses Maya's current playback range and can replace animation or source connections. "
                  "The confirmation shows the target and range.")
        self.check_option(layout, "force_proxy", "Force Python proxy bake (skeleton only)",
                          "Use the shared proxy bake instead of Maya's native skeleton bake. "
                          "This replaces incoming translate/rotate connections.")
        bake_row = ui_qt.QtWidgets.QHBoxLayout()
        bake_row.addWidget(self.button(
            "bake_skeleton", "Bake to Skeleton...", "Bake the retargeted animation to mapped bones."
        ))
        bake_row.addWidget(self.button(
            "bake_controls", "Bake to Control Rig...", "Use Maya's native HumanIK control-rig bake."
        ))
        layout.addLayout(bake_row)
        layout.addStretch()

    def build_inspect_tab(self):
        """Builds scene reports, targeted selection, and cleanup preview."""
        layout = self.tab_layout("Inspect")
        row = ui_qt.QtWidgets.QHBoxLayout()
        for key, label, tooltip in (
            ("inspect", "Inspect", "Report namespace, source, lock, bones, controls, and property node."),
            ("select_character", "Definition", "Select the definition node."),
            ("select_skeleton", "Skeleton", "Select mapped joints."),
            ("select_property_node", "Properties", "Select the retarget property node."),
        ):
            row.addWidget(self.button(key, label, tooltip))
        layout.addLayout(row)
        self.report = ui_qt.QtWidgets.QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setPlaceholderText("Inspect a character or preview an XML mapping or cleanup.")
        layout.addWidget(self.report, 1)
        layout.addWidget(self.button(
            "cleanup", "Preview Empty Definitions...",
            "Review empty local definitions before deletion. Definitions with skeletons, rigs, "
            "character connections, references, or node locks are excluded.", target=False,
        ))

    def get_settings(self):
        """Reads persistent options from widgets.

        Returns:
            dict: Tool settings represented in the view.
        """
        return {
            key: widget.isChecked() if isinstance(widget, ui_qt.QtWidgets.QCheckBox) else widget.text().strip()
            for key, widget in self.settings_widgets.items()
        }

    def set_settings(self, settings):
        """Updates option widgets without firing persistence callbacks.

        Args:
            settings (dict): Model-owned tool settings.
        """
        for key, widget in self.settings_widgets.items():
            previous = widget.blockSignals(True)
            if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
                widget.setChecked(settings[key])
            else:
                widget.setText(settings[key])
            widget.blockSignals(previous)

    def set_status(self, message):
        """Shows routine results without modal dialogs.

        Args:
            message (str): Result or warning to display.
        """
        self.status_label.setText(message)
        self.status_label.setToolTip(message)

    def show_report(self, text):
        """Displays a selectable report in the Inspect tab.

        Args:
            text (str): Report contents.
        """
        self.report.setPlainText(text)
        self.tabs.setCurrentIndex(3)
