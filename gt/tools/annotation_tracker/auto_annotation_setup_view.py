"""Qt views for Annotation Setup preferences and calibration."""

from gt.core.motion_eval import presets
from gt.tools.anim_evaluator.anim_evaluator_widgets import DISABLED_STYLESHEET, PresetEditorWidget
from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.tools.annotation_tracker import auto_annotation_rules as rules
from gt.tools.annotation_tracker import auto_annotation_scene as scene
from gt.tools.annotation_tracker.auto_annotation_calibration_view import (
    CalibrationInspector, CalibrationRuleEditor, SpeedThresholdEditor, fit_button,
)
from gt.tools.annotation_tracker.auto_annotation_vlm_view import VlmSettingsTab
from gt.ui import qt_utils, resource_library
from gt.ui.qt_import import QtCore, QtWidgets


SETUP_STYLESHEET = (
    DISABLED_STYLESHEET
    + "QTableWidget:disabled { background-color: #353535; color: #777777; }"
    + "QLineEdit:disabled, QComboBox:disabled { color: #888888; }"
    + "QPushButton:enabled { background-color: #626262; color: #F1F1F1;"
    + " border: 1px solid #737373; border-radius: 3px; padding: 4px 9px; }"
    + "QPushButton:hover:enabled { background-color: #727272; }"
    + "QGroupBox { background-color: #3a3a3a; border: 1px solid #5c5c5c; border-radius: 4px;"
    + " margin-top: 12px; padding: 10px 6px 6px 6px; }"
    + "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 8px;"
    + " padding: 0 4px; color: #d6d6d6; font-weight: bold; }"
)


class SetupStatus(QtWidgets.QLineEdit):
    """Displays timestamped feedback in the same kind of status line as Batch Processor."""

    def __init__(self):
        """Creates a read-only status line that fills the available footer space."""
        super().__init__()
        self.setReadOnly(True)
        self.setAccessibleName("Annotation Setup status")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        qt_utils.set_status_line_text(self, "")

    def show_message(self, text):
        """Displays the message with the local time and keeps the full text on hover.

        Args:
            text (str): Full status message.
        """
        time = QtCore.QTime.currentTime().toString("HH:mm:ss")
        message = f"[{time}] {text}" if text else ""
        qt_utils.set_status_line_text(self, message)
        self.setCursorPosition(0)
        self.setToolTip(message)


class AnnotationSetupDialog(QtWidgets.QDialog):
    """Displays Auto Annotate settings and calibration cues."""

    ranges_clicked = QtCore.Signal()

    def __init__(self, settings, schema, parent=None):
        """Creates the settings and calibration pages.

        Args:
            settings (dict): Current Auto Annotate settings.
            schema (dict): Active Annotation Tracker schema.
            parent (QWidget, optional): Tracker window.
        """
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Annotation Setup")
        self.resize(720, 680)
        self.setStyleSheet(SETUP_STYLESHEET)
        self.options = dict(settings)
        self.schema = schema
        self.range_fields = model.get_schema_fields(schema, "frame_range")
        self.file_fields = model.get_schema_fields(schema, "file_level")
        self.custom_calibration = None
        self.showing_custom = False

        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self._scrollable(self._build_settings()), "Settings")
        self.tabs.addTab(self._build_calibration(), "Calibration")
        self.vlm = VlmSettingsTab(self.options)
        self.tabs.addTab(self._scrollable(self.vlm), "VLM")
        self.tabs.addTab(self._build_metadata(), "Metadata")
        self.tabs.addTab(self._scrollable(self._build_quality()), "Quality")
        layout.addWidget(self.tabs)
        footer = QtWidgets.QHBoxLayout()
        status_container = QtWidgets.QWidget()
        status_container.setStyleSheet(resource_library.Stylesheet.line_edit_base)
        status_layout = QtWidgets.QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.status = SetupStatus()
        status_layout.addWidget(self.status)
        footer.addWidget(status_container, 1)
        self.auto_save = QtWidgets.QCheckBox("Auto-save changes")
        self.auto_save.setChecked(self.options["auto_save"])
        self.auto_save.setToolTip(
            "Saves every change a moment after you make it, so Auto Annotate uses it without closing Setup.\n"
            "Changes cannot be discarded while this is on."
        )
        footer.addWidget(self.auto_save)
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setToolTip(
            "Saves preferences for future interactive and unattended runs."
        )
        self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setToolTip(
            "Closes Setup and discards pending preference edits.\n"
            "Exports and confirmed resets take effect immediately."
        )
        self.buttons.rejected.connect(self.reject)
        footer.addWidget(self.buttons)
        layout.addLayout(footer)
        self.calibration.profile_changed.connect(self._sync_speed_editor)
        self.speed_editor.edited.connect(self._show_edited_speeds)
        self.auto_save.toggled.connect(self._update_auto_save_ui)
        self._update_auto_save_ui()
        self.profile_selector.currentIndexChanged.connect(self._switch_calibration_profile)
        self.skeleton_mode.currentIndexChanged.connect(self._update_controls)
        self.file_style_source.currentIndexChanged.connect(self._update_controls)
        self.source_mode.currentIndexChanged.connect(self._update_controls)
        self.source_fallback.currentIndexChanged.connect(self._update_controls)
        self.source_pattern.textChanged.connect(self._hide_stale_source_example)
        self.show_full_paths.toggled.connect(self._refresh_joint_paths)
        self.joints.itemChanged.connect(self._joint_edited)
        self.pose_field.currentIndexChanged.connect(self._update_training_labels)
        self.profile_name.textChanged.connect(lambda *args: self.profile_status.setText(self._profile_status_text()))
        self._update_controls()
        self._update_training_labels()
        self.set_calibration(settings["calibration"])

    def _sync_speed_editor(self):
        """Shows the speed limits that remain after a speed cue was deleted."""
        self.speed_editor.set_values((self.calibration.profile or {}).get("locomotion", {}))

    def _show_edited_speeds(self):
        """Updates the Motion Cues references after the limits are typed."""
        if not self.showing_custom or self.calibration.profile is None:
            return
        profile = self.calibration.profile
        speeds = self.speed_editor.read_values()
        if speeds:
            profile["locomotion"] = speeds
        else:
            profile.pop("locomotion", None)
        self.calibration.set_profile(
            profile, True, locked=False, use_names=self.pose_field.currentData() == rules.RANGE_NAME_FIELD
        )

    def eventFilter(self, watched, event):
        """Asks for a range refresh after the user clicks the Train range list.

        Args:
            watched (QObject): Object that received the event.
            event (QEvent): Incoming event.

        Returns:
            bool: Always False so the click is handled normally.
        """
        if watched is self.ranges.viewport() and event.type() == QtCore.QEvent.Type.MouseButtonPress:
            QtCore.QTimer.singleShot(0, self.ranges_clicked.emit)
        return False

    def _update_auto_save_ui(self, *args):
        """Relabels the footer buttons because changes are saved as they are made."""
        enabled = self.auto_save.isChecked()
        save_button = self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Save)
        save_button.setText("Close" if enabled else "Save")
        self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setVisible(not enabled)

    @staticmethod
    def _scrollable(page):
        """Wraps a settings page to keep controls accessible at small window sizes.

        Args:
            page (QWidget): Settings page.

        Returns:
            QScrollArea: Resizable, frameless page container.
        """
        scroll = QtWidgets.QScrollArea()
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def _combo(choices, current):
        """Creates a choice widget from display names and stored values.

        Args:
            choices (tuple): Display and data pairs.
            current (str): Data value to select.

        Returns:
            QComboBox: Populated choice widget.
        """
        combo = QtWidgets.QComboBox()
        for name, value in choices:
            combo.addItem(name, value)
        combo.setCurrentIndex(max(0, combo.findData(current)))
        return combo

    @staticmethod
    def _with_button(field, button):
        """Places a field and an associated control in one compact row.

        Args:
            field (QWidget): Main control.
            button (QWidget): Associated action or status display.

        Returns:
            QWidget: Row containing both controls.
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field, 1)
        layout.addWidget(button)
        return widget

    def _build_settings(self):
        """Builds the profile and skeleton preferences page.

        Returns:
            QWidget: Settings page.
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)

        profile_group = QtWidgets.QGroupBox("Settings Profile")
        profile_form = QtWidgets.QFormLayout(profile_group)
        self.import_settings = QtWidgets.QPushButton("Import Settings")
        self.export_settings = QtWidgets.QPushButton("Export Settings")
        self.reset_all = QtWidgets.QPushButton("Reset Settings")
        self.reset_all.setToolTip(
            "Restores Auto Annotate defaults after confirmation.\nChoose whether to retain embedded calibration."
        )
        self.import_settings.setToolTip(
            "Load a settings JSON into this window, including calibration.\n"
            "Click Save to use those preferences in the Tracker."
        )
        self.export_settings.setToolTip(
            "Export the settings, embedded calibration, and schema as one file for automated runs."
        )
        profile_actions = QtWidgets.QHBoxLayout()
        profile_actions.addWidget(self.import_settings)
        profile_actions.addWidget(self.export_settings)
        profile_actions.addWidget(self.reset_all)
        profile_actions.addStretch()
        self.profile_status = QtWidgets.QLabel()
        self.profile_status.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.profile_status.setToolTip("The active profile is selected on the Calibration tab.")
        profile_actions.addWidget(self.profile_status)
        profile_form.addRow(profile_actions)
        layout.addWidget(profile_group)

        output_group = QtWidgets.QGroupBox("Annotation Output")
        output_form = QtWidgets.QFormLayout(output_group)
        self.fill_mode = self._combo(
            (("Only fill gaps (keep existing ranges)", "gaps"), ("Overwrite existing ranges", "overwrite")),
            self.options["fill_mode"],
        )
        self.fill_mode.setToolTip(
            "Only fill gaps: new ranges are added only where frames have no range. Nothing is replaced.\n"
            "Overwrite: unlocked ranges inside the analyzed frames are replaced. Locked ranges are kept.\n"
            "Overwriting can be undone with Maya's undo."
        )
        output_form.addRow("Existing annotations", self.fill_mode)
        layout.addWidget(output_group)

        skeleton_group = QtWidgets.QGroupBox("Skeleton")
        skeleton_form = QtWidgets.QFormLayout(skeleton_group)
        self.skeleton_mode = self._combo(
            (("Auto-detect", "auto"), ("Manual mapping", "manual")), self.options["skeleton_mode"]
        )
        self.skeleton_mode.setToolTip(
            "Auto-detect resolves familiar humanoid names inside one joint hierarchy.\n"
            "Manual mapping uses the joint assignments in the table."
        )
        self.skeleton_root = QtWidgets.QLineEdit(self.options["skeleton_root"])
        self.skeleton_root.setPlaceholderText("Optional. Constrain detection to one character.")
        self.skeleton_root.setToolTip(
            "Limit skeleton resolution to descendants of this joint or transform.\n"
            "Use a full Maya DAG path when scenes contain duplicate short names."
        )
        self.pick_root = QtWidgets.QPushButton("Use Selection")
        self.pick_root.setToolTip("Use the single selected Maya transform or joint as the skeleton root.")
        self.detect_skeleton = QtWidgets.QPushButton("Detect Current Skeleton")
        self.detect_skeleton.setToolTip(
            "Detects the joint roles in the current scene and shows the results in the table.\n"
            "In manual mode, you can edit these assignments before saving."
        )
        self.pick_joint = QtWidgets.QPushButton("Assign Selected Joint")
        self.pick_joint.setToolTip("Assign the single selected Maya joint to the highlighted manual role.")
        self.show_full_paths = QtWidgets.QCheckBox("Show full paths")
        self.show_full_paths.setToolTip(
            "Toggles the full DAG path in the joint table.\nThe underlying joint mapping stays the same."
        )
        self.show_full_paths.setChecked(self.options["show_full_joint_paths"])
        self.short_name_fallback = QtWidgets.QCheckBox("Short-name fallback")
        self.short_name_fallback.setChecked(self.options["short_name_fallback"])
        self.short_name_fallback.setToolTip(
            "If a saved DAG path no longer exists, try its short name.\n"
            "The match must be unique within the appropriate skeleton hierarchy."
        )
        self.clear_mapping = QtWidgets.QPushButton("Clear Saved Mapping")
        self.clear_mapping.setToolTip(
            "Clears the saved root and manual joint assignments after confirmation.\n"
            "Auto-detection is enabled again and calibration files are kept."
        )
        self.joints = QtWidgets.QTableWidget(len(scene.ROLE_NAMES), 2)
        self.joints.setHorizontalHeaderLabels(["Role", "Joint"])
        self.joints.horizontalHeader().setStretchLastSection(True)
        self.joints.verticalHeader().hide()
        self.joints.setMinimumHeight(132)
        self.joints.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.joints.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.joints.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.joints.customContextMenuRequested.connect(self._show_joint_menu)
        self.joints.setToolTip(
            "Manual mapping requires a pelvis and both feet.\n"
            "Extra joints improve pose measurements and support Biped quality checks."
        )
        self.set_joint_map(self.options["joint_map"])
        skeleton_form.addRow("Mode", self._with_button(self.skeleton_mode, self.detect_skeleton))
        skeleton_form.addRow("Skeleton root", self._with_button(self.skeleton_root, self.pick_root))
        skeleton_form.addRow(self.joints)
        joint_actions = QtWidgets.QHBoxLayout()
        joint_actions.addWidget(self.show_full_paths)
        joint_actions.addWidget(self.short_name_fallback)
        joint_actions.addStretch()
        for button in (self.pick_joint, self.clear_mapping):
            fit_button(button)
            joint_actions.addWidget(button)
        skeleton_form.addRow(joint_actions)
        self._build_joint_menu()
        layout.addWidget(skeleton_group, 1)

        return page

    def _build_joint_menu(self):
        """Creates the skeleton table's right-click menu and keeps a reference to it."""
        self.joint_menu = QtWidgets.QMenu(self.joints)
        self.assign_action = self.joint_menu.addAction("Assign Selected Joint")
        self.joint_menu.addSeparator()
        self.clear_action = self.joint_menu.addAction("Clear Selected")
        self.joint_menu.addSeparator()
        self.copy_action = self.joint_menu.addAction("Copy")
        self.paste_action = self.joint_menu.addAction("Paste")
        self.assign_action.triggered.connect(self.pick_joint.click)
        self.clear_action.triggered.connect(self.clear_selected_joints)
        self.copy_action.triggered.connect(self.copy_selected_joints)
        self.paste_action.triggered.connect(self.paste_joints)

    def _show_joint_menu(self, position):
        """Shows the joint menu for the row under the cursor.

        Args:
            position (QPoint): Cursor position inside the table viewport.
        """
        item = self.joints.itemAt(position)
        if item is not None and not self.joints.item(item.row(), 0).isSelected():
            self.joints.selectRow(item.row())
        manual = self.skeleton_mode.currentData() == "manual"
        has_selection = bool(self.joints.selectionModel().selectedRows())
        self.assign_action.setEnabled(manual and has_selection)
        self.clear_action.setEnabled(manual and has_selection)
        self.copy_action.setEnabled(has_selection)
        self.paste_action.setEnabled(manual and has_selection)
        self.joint_menu.exec(self.joints.viewport().mapToGlobal(position))

    def _selected_joint_rows(self):
        """Gets the highlighted skeleton rows in table order.

        Returns:
            list: Row numbers.
        """
        return sorted(index.row() for index in self.joints.selectionModel().selectedRows())

    def clear_selected_joints(self):
        """Clears the joint assigned to each highlighted role."""
        rows = self._selected_joint_rows()
        for row in rows:
            self.set_joint(row, "")
        self.status.show_message(f"Cleared {len(rows)} joint assignment(s).")

    def copy_selected_joints(self):
        """Copies the highlighted joint paths, one per line."""
        paths = [self.joints.item(row, 1).data(QtCore.Qt.ItemDataRole.UserRole) for row in self._selected_joint_rows()]
        QtWidgets.QApplication.clipboard().setText("\n".join(paths))
        self.status.show_message(f"Copied {len(paths)} joint path(s).")

    def paste_joints(self):
        """Pastes clipboard lines into the highlighted roles in order.

        One line fills every highlighted role. Several lines fill roles from the first highlighted row down.
        """
        lines = [line.strip() for line in QtWidgets.QApplication.clipboard().text().splitlines() if line.strip()]
        rows = self._selected_joint_rows()
        if not lines or not rows:
            self.status.show_message("The clipboard has no joint names to paste.")
            return
        if len(lines) == 1:
            targets = [(row, lines[0]) for row in rows]
        else:
            targets = list(zip(range(rows[0], len(scene.ROLE_NAMES)), lines))
        for row, path in targets:
            self.set_joint(row, path)
        self.status.show_message(f"Pasted {len(targets)} joint assignment(s).")

    def _build_calibration(self):
        """Builds the calibration profile, training and inspection pages.

        Returns:
            QWidget: Calibration page.
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        profile_form = QtWidgets.QFormLayout()
        self.profile_selector = self._combo(
            (("Built-in Default (locked)", False), ("Custom Profile", True)), self.options["use_profile"],
        )
        self.profile_selector.setToolTip(
            "The built-in calibration profile is read-only.\n"
            "Choose Custom Profile to edit rules and use your own training cues."
        )
        profile_row = QtWidgets.QWidget()
        profile_actions = QtWidgets.QHBoxLayout(profile_row)
        profile_actions.setContentsMargins(0, 0, 0, 0)
        profile_actions.addWidget(self.profile_selector, 1)
        self.import_calibration = QtWidgets.QPushButton("Import")
        self.export_calibration = QtWidgets.QPushButton("Export")
        self.duplicate_calibration = QtWidgets.QPushButton("Duplicate")
        self.clear_calibration = QtWidgets.QPushButton("Clear")
        for button in (
            self.import_calibration, self.export_calibration, self.duplicate_calibration, self.clear_calibration,
        ):
            button.setAccessibleName(f"{button.text()} calibration profile")
            profile_actions.addWidget(button)
        self.import_calibration.setToolTip("Copy cues, detection rules and cue choices into this setup.")
        self.export_calibration.setToolTip("Export the selected calibration profile as a separate JSON file.")
        self.duplicate_calibration.setToolTip(
            "Copy the locked defaults into an editable custom calibration profile."
        )
        self.clear_calibration.setToolTip("Discard the custom calibration profile while keeping the other settings.")
        profile_form.addRow("Calibration profile", profile_row)
        self.profile_name = QtWidgets.QLineEdit()
        self.profile_name.setMaxLength(model.PROFILE_NAME_LENGTH)
        self.profile_name.setPlaceholderText(model.DEFAULT_PROFILE_NAME)
        self.profile_name.setToolTip(
            "Describe what this custom calibration is for, e.g. 'Vending machine idles'.\n"
            "The name is saved with the profile and printed when Auto Annotate runs."
        )
        profile_form.addRow("Profile name", self.profile_name)
        layout.addLayout(profile_form)
        self.calibration_tabs = QtWidgets.QTabWidget()
        self.detection_rules = CalibrationRuleEditor()
        self.calibration_tabs.addTab(self._scrollable(self.detection_rules), "Rules")
        self.training_page = self._build_training()
        self.calibration_tabs.addTab(self.training_page, "Train")
        activity_available = model.supports_value(self.range_fields.get("state"), "activity")
        self.calibration = CalibrationInspector(activity_available=activity_available)
        self.examples_page = self._scrollable(self.calibration)
        self.calibration_tabs.addTab(self.examples_page, "Motion Cues")
        layout.addWidget(self.calibration_tabs, 1)
        self.calibration_page = page
        return page

    def _build_training(self):
        """Builds training controls for adding cues from the current scene.

        Returns:
            QWidget: Training page with label source and selectable ranges.
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        form = QtWidgets.QFormLayout()
        self.pose_field = self._combo(
            (("Range names", rules.RANGE_NAME_FIELD),) + tuple(
                (f"{field.get('label', name)} field", name) for name, field in self.range_fields.items()
                if field.get("type") in ("enum", "string") and name != "state"
            ), self.options["pose_field"],
        )
        self.select_label_source(self.options["pose_field"])
        self.pose_field.setToolTip(
            "Where each training range gets its pose label.\n"
            "This does not limit training to one pose: every labeled range you add becomes a cue.\n"
            "Range names uses the range name (e.g. vending_machine) and appends it to detected range names.\n"
            "A schema field uses that field's populated values and writes them back when detected."
        )
        form.addRow("Pose label comes from", self.pose_field)
        layout.addLayout(form)
        self.ranges = QtWidgets.QListWidget()
        self.ranges.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.ranges.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ranges.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.ranges.setToolTip(
            "Select ranges from the current scene.\nUse Ctrl or Shift to select more than one."
        )
        self.ranges.setMinimumHeight(125)
        self.ranges.viewport().installEventFilter(self)
        self.ranges.itemSelectionChanged.connect(self._update_add_selected)
        layout.addWidget(self.ranges, 1)
        self.training_summary = QtWidgets.QLabel()
        self.training_summary.setWordWrap(True)
        layout.addWidget(self.training_summary)
        self.speed_editor = SpeedThresholdEditor()
        layout.addWidget(self.speed_editor)
        self.calibrate_all = QtWidgets.QPushButton("Learn from All Ranges")
        self.calibrate = QtWidgets.QPushButton("Learn from Selected")
        self.calibrate_playback = QtWidgets.QPushButton("Learn from Playback")
        self.refresh_ranges = QtWidgets.QPushButton("Refresh Ranges")
        self.calibrate_all.setToolTip(
            "Measures every labeled Tracker range in one pass through playback.\n"
            "New cues are added to the custom profile."
        )
        self.calibrate.setToolTip(
            "Measures selected ranges and adds their cues to the current setup.\n"
            "Click Save to use the cues in the Tracker, or Export Settings to use them in a dataset run."
        )
        self.refresh_ranges.setToolTip("Reload the calibration range list after changing scenes or Tracker ranges.")
        self.calibrate_playback.setToolTip(
            "Assign one label to the full playback range.\nUse this when the clip is already an isolated pose cue."
        )
        action_row = QtWidgets.QHBoxLayout()
        for button in (self.calibrate_all, self.calibrate, self.calibrate_playback, self.refresh_ranges):
            fit_button(button)
            action_row.addWidget(button)
        action_row.addStretch()
        layout.addLayout(action_row)
        return page

    def select_label_source(self, name):
        """Preserves an imported pose field even if the active schema lacks it.

        Args:
            name (str): Stored pose field key.
        """
        index = self.pose_field.findData(name)
        if index < 0:
            self.pose_field.addItem(f"{name} (outside active schema)", name)
            index = self.pose_field.count() - 1
        self.pose_field.setCurrentIndex(index)

    def set_calibration(self, profile, activate=None, focus_example=None):
        """Displays new embedded calibration and its current use status.

        Args:
            profile (dict or None): Embedded calibration.
            activate (bool, optional): Selects the custom profile when true or the built-in profile when false.
            focus_example (tuple, optional): Section, label and example index to select.
        """
        self.custom_calibration = profile
        if activate is not None:
            self.profile_selector.blockSignals(True)
            self.profile_selector.setCurrentIndex(self.profile_selector.findData(activate))
            self.profile_selector.blockSignals(False)
        self._show_calibration_profile(focus_example)

    def _switch_calibration_profile(self, *args):
        """Keeps custom edits while switching between the profiles."""
        if self.showing_custom:
            self.custom_calibration = self.read_calibration()
        self._show_calibration_profile()

    def _show_calibration_profile(self, focus_example=None):
        """Loads the selected profile into the rule and cue views.

        Args:
            focus_example (tuple, optional): Section, label and example index to select.
        """
        self.showing_custom = bool(self.profile_selector.currentData())
        if self.showing_custom and self.custom_calibration is None:
            self.custom_calibration = dict(model.new_profile(), rules={})
        profile = self.custom_calibration if self.showing_custom else None
        self.detection_rules.set_rules((profile or {}).get("rules", {}), locked=not self.showing_custom)
        self.speed_editor.set_values((profile or {}).get("locomotion", {}))
        self.speed_editor.set_locked(not self.showing_custom)
        self.profile_name.setEnabled(self.showing_custom)
        self.profile_name.setText((profile or {}).get("name", "") if self.showing_custom else "")
        self.calibration.set_profile(
            profile, self.showing_custom, focus_example, locked=not self.showing_custom,
            use_names=self.pose_field.currentData() == rules.RANGE_NAME_FIELD,
        )
        exists = self.custom_calibration is not None
        self.duplicate_calibration.setEnabled(not self.showing_custom)
        self.clear_calibration.setEnabled(self.showing_custom and exists)
        self.profile_status.setText(self._profile_status_text())

    def _profile_status_text(self):
        """Describes the active calibration profile for the Settings page.

        Returns:
            str: Profile kind and custom name.
        """
        if not self.showing_custom:
            return "Calibration: Built-in profile"
        name = self.profile_name.text().strip() or model.DEFAULT_PROFILE_NAME
        return f"Calibration: Custom profile \u201c{name}\u201d"

    def read_calibration(self):
        """Gets the editable profile while preserving its data when viewing defaults.

        Returns:
            dict or None: Custom calibration saved with Setup.
        """
        if not self.showing_custom:
            return self.custom_calibration
        profile = self.calibration.read_profile() or model.new_profile()
        profile["label_source"] = self.pose_field.currentData()
        name = self.profile_name.text().strip()
        if name:
            profile["name"] = name
        else:
            profile.pop("name", None)
        speeds = self.speed_editor.read_values()
        if speeds:
            profile["locomotion"] = speeds
        else:
            profile.pop("locomotion", None)
        values = self.detection_rules.read_rules()
        if values or not model.has_calibration(profile):
            profile["rules"] = values
        else:
            profile.pop("rules", None)
        return profile

    def show_training_result(self, profile, focus_example):
        """Shows newly measured cues in the custom profile.

        Args:
            profile (dict): Updated calibration profile.
            focus_example (tuple or None): Section, label and example index to show.
        """
        self.set_calibration(profile, activate=True, focus_example=focus_example)
        self.calibration_tabs.setCurrentWidget(self.examples_page)

    def _build_metadata(self):
        """Builds the controls for automatic file-level fields.

        Returns:
            QWidget: Metadata settings page.
        """
        page = QtWidgets.QWidget()
        page_layout = QtWidgets.QVBoxLayout(page)

        def make_group(title):
            """Adds a titled box with a form to the page.

            Args:
                title (str): Box title.

            Returns:
                QFormLayout: Layout for the box rows.
            """
            box = QtWidgets.QGroupBox(title)
            box_form = QtWidgets.QFormLayout(box)
            box_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            box.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
            page_layout.addWidget(box)
            return box_form

        form = make_group("Commercial use and style")
        source_form = make_group("Source")
        flags_form = make_group("Clip Tracker and annotated flag")
        commercial_value = {None: "keep", True: "true", False: "false"}.get(self.options["commercial_use"], "keep")
        self.commercial_use = self._combo(
            (("Leave as is", "keep"), ("Set to Yes when empty", "true"), ("Set to No when empty", "false")),
            commercial_value,
        )
        self.commercial_use.setToolTip(
            "Fills Commercial Use only when the field is empty.\n"
            "Choose Yes only for material cleared for commercial use."
        )
        self.file_style_source = self._combo(
            (("Leave as is", "keep"), ("Use VLM suggestions", "vlm"), ("Set a value when empty", "fixed")),
            self.options["file_style_source"],
        )
        self.file_style_source.setToolTip(
            "Choose whether a VLM suggestion or a fixed value can fill File Style.\n"
            "VLM suggestions require an enabled mode on the VLM tab."
        )
        self.file_style = QtWidgets.QComboBox()
        style = self.file_fields.get("style", {})
        self.file_style.setEditable(style.get("type") == "string")
        self.file_style.addItem("")
        self.file_style.addItems([option for option in style.get("options", []) if option.lower() != "none"])
        self.file_style.setToolTip("Choose a label accepted by the active schema for an empty File Style field.")
        self._set_style_value(self.options["file_style"])
        self.source_mode = self._combo(
            (
                ("Leave as is", "keep"), ("Set a fixed text when empty", "fixed"),
                ("Find in the scene's folder path", "path"),
            ),
            self.options["file_source_mode"],
        )
        self.source_mode.setToolTip("Fills Source only when it is empty. Existing values are kept.")
        self.source_value = QtWidgets.QLineEdit(self.options["file_source"])
        self.source_value.setMaxLength(200)
        self.source_value.setPlaceholderText("Text to use as the Source")
        self.source_pattern = QtWidgets.QLineEdit(self.options["file_source_pattern"])
        self.source_pattern.setMaxLength(300)
        self.source_example = QtWidgets.QLabel()
        self.source_example.setWordWrap(True)
        self.source_example.setVisible(False)
        self.source_example.setStyleSheet("color: #E4C98A;")
        self.source_presets = QtWidgets.QPushButton("Examples")
        self.source_presets.setMinimumWidth(self.source_presets.fontMetrics().horizontalAdvance("Examples") + 56)
        self.source_presets.setToolTip("Fill the pattern with a ready-made example.")
        self.source_preset_menu = QtWidgets.QMenu(self.source_presets)
        for preset_label, preset_pattern, preset_sample in model.SOURCE_PATTERN_PRESETS:
            action = self.source_preset_menu.addAction(preset_label)
            action.setToolTip(preset_pattern)
            action.triggered.connect(
                lambda checked=False, pattern=preset_pattern, sample=preset_sample, name=preset_label:
                self._apply_source_preset(name, pattern, sample)
            )
        self.source_presets.setMenu(self.source_preset_menu)
        self.preset_pattern = None
        pattern_row = QtWidgets.QWidget()
        pattern_layout = QtWidgets.QHBoxLayout(pattern_row)
        pattern_layout.setContentsMargins(0, 0, 0, 0)
        pattern_layout.addWidget(self.source_pattern, 1)
        pattern_layout.addWidget(self.source_presets)
        self.source_fallback = self._combo(
            (
                ("Leave empty and warn", "none"), ("Use the Source text", "text"),
                ("Use the nearest folder name", "folder"),
            ),
            self.options["file_source_fallback"],
        )
        self.source_fallback.setToolTip("What to do when no folder matches the pattern.")
        self.source_pattern.setPlaceholderText("Regular expression. Blank uses the whole folder name.")
        self.source_pattern.setToolTip(
            "Searched anywhere inside each folder name, so a longer folder name can still give its matching part.\n"
            "If the pattern has a group, the first group is used, otherwise the whole match.\n"
            "Example: ^([A-Za-z]+_\\d{3}) takes the leading part of 'Name_001_r21_testing'."
        )
        self.source_depth = QtWidgets.QSpinBox()
        self.source_depth.setRange(0, 40)
        self.source_depth.setSpecialValueText("All folders")
        self.source_depth.setSuffix(" up")
        self.source_depth.setMinimumWidth(110)
        self.source_depth.setValue(self.options["file_source_depth"])
        self.source_depth.setToolTip("How many folders above the scene file to search. 1 is the file's own folder.")
        self.source_order = self._combo(
            (("Nearest folder first", "nearest"), ("Highest folder first", "outermost")),
            self.options["file_source_order"],
        )
        self.source_order.setToolTip("Which folder wins when several match.")
        search_row = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_row)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(self.source_depth)
        search_layout.addWidget(self.source_order, 1)
        self.source_test_path = QtWidgets.QLineEdit()
        self.source_test_path.setPlaceholderText("Paste a path to test, or leave blank for the current scene")
        self.test_source = QtWidgets.QPushButton("Test")
        self.test_source.setMinimumWidth(self.test_source.fontMetrics().horizontalAdvance("Test") + 44)
        self.test_source.setToolTip("Shows the Source these settings would find, without changing anything.")
        test_row = QtWidgets.QWidget()
        test_layout = QtWidgets.QHBoxLayout(test_row)
        test_layout.setContentsMargins(0, 0, 0, 0)
        test_layout.addWidget(self.source_test_path, 1)
        test_layout.addWidget(self.test_source)
        self.set_clipped = QtWidgets.QCheckBox("Check Clip Tracker for valid clips")
        self.set_clipped.setChecked(self.options["auto_set_clipped"])
        self.set_clipped.setToolTip(
            "Marks Clipped when a valid Clip Tracker range is present.\nExisting positive values are preserved."
        )
        self.set_annotated = QtWidgets.QCheckBox("Set from schema validation and full timeline coverage")
        self.set_annotated.setChecked(self.options["auto_set_annotated"])
        self.set_annotated.setToolTip(
            "Sets Annotated when the schema validates and ranges cover playback.\n"
            "Clears the flag when required fields or frames are missing."
        )
        for name, label, control in (
            ("commercial_use", "Commercial Use", self.commercial_use), ("style", "File Style", self.file_style_source),
            ("clipped", "Clipped", self.set_clipped), ("annotated", "Annotated", self.set_annotated),
        ):
            (flags_form if name in ("clipped", "annotated") else form).addRow(label, control)
            if name not in self.file_fields:
                control.setEnabled(False)
                control.setToolTip("This field is unavailable in the active schema.")
        form.insertRow(2, "Style value", self.file_style)
        for label, control in (
            ("Source", self.source_mode), ("Source text", self.source_value), ("Folder pattern", pattern_row),
            ("", self.source_example), ("Folder search", search_row), ("If nothing matches", self.source_fallback),
            ("Test", test_row),
        ):
            source_form.addRow(label, control)
            if "source" not in self.file_fields:
                control.setEnabled(False)
                control.setToolTip("This field is unavailable in the active schema.")
        page_layout.addStretch()
        return page

    def _build_quality(self):
        """Builds the shared Motion Evaluator preset editor.

        Returns:
            QWidget: Quality settings page.
        """
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        self.set_quality = QtWidgets.QCheckBox("Set empty Quality from Motion Evaluator")
        self.set_quality.setChecked(self.options["auto_set_quality"])
        self.set_quality.setToolTip(
            "Scores the detected or mapped character over the full playback range.\n"
            "An existing manual Quality score is preserved."
        )
        self.quality_editor = PresetEditorWidget(parent=page, preset=self.options["quality_preset"])
        for button in self.quality_editor.findChildren(QtWidgets.QPushButton):
            button.setText(button.text().rstrip(".…"))
        self.quality_editor.setEnabled(self.set_quality.isChecked())
        self.set_quality.toggled.connect(self.quality_editor.setEnabled)
        layout.addWidget(self.set_quality)
        layout.addWidget(self.quality_editor, 1)
        return page

    def _set_style_value(self, value):
        """Selects a fixed style using the field type from the active schema.

        Args:
            value (str): Saved style value.
        """
        value = "" if value.strip().lower() == "none" else value
        if self.file_style.isEditable():
            self.file_style.setEditText(value)
        else:
            index = self.file_style.findText(value)
            if index < 0 and value:
                self.file_style.addItem(value)
                index = self.file_style.count() - 1
            self.file_style.setCurrentIndex(max(0, index))

    def _apply_source_preset(self, name, pattern, sample):
        """Puts an example pattern in the field and shows what it does to a sample name.

        Args:
            name (str): Preset description.
            pattern (str): Regular expression.
            sample (str): Example folder name.
        """
        self.source_pattern.setText(pattern)
        self.preset_pattern = pattern
        result = model.preview_source_preset(pattern, sample)
        self.source_example.setText(f"{name}\nExample: {sample}  \u2192  {result}")
        self.source_example.setVisible(True)

    def _hide_stale_source_example(self, text):
        """Hides the example note once the pattern is edited away from the chosen preset.

        Args:
            text (str): Current pattern text.
        """
        if self.preset_pattern is not None and text != self.preset_pattern:
            self.source_example.setVisible(False)
            self.preset_pattern = None

    def _update_controls(self, *args):
        """Reflects the skeleton and metadata settings in their controls."""
        manual = self.skeleton_mode.currentData() == "manual"
        trigger = (
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
            | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed
            if manual else QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.joints.setEditTriggers(trigger)
        self.pick_joint.setEnabled(manual)
        fixed_style = self.file_style_source.currentData() == "fixed"
        self.file_style.setEnabled(self.file_style_source.isEnabled() and fixed_style)
        if "source" in self.file_fields:
            mode = self.source_mode.currentData()
            fallback_text = mode == "path" and self.source_fallback.currentData() == "text"
            self.source_value.setEnabled(mode == "fixed" or fallback_text)
            for control in (
                self.source_pattern, self.source_presets, self.source_depth, self.source_order,
                self.source_fallback, self.source_test_path, self.test_source,
            ):
                control.setEnabled(mode == "path")

    def _update_training_labels(self, *args):
        """Shows what each range would teach with the selected label source."""
        source = self.pose_field.currentData()
        field = self.range_fields.get(source)
        count = 0
        for row in range(self.ranges.count()):
            widget = self.ranges.item(row)
            item = widget.data(QtCore.Qt.ItemDataRole.UserRole)
            pose, speed = model.get_training_labels(item, source, field)
            labels = []
            if pose:
                prefix = "Activity" if model.is_activity_example(item) else "Pose"
                labels.append(f"{prefix}: {pose}")
            if speed:
                labels.append(f"Speed: {speed}")
            count += bool(labels)
            description = " · ".join(labels) or "No training label"
            text = f"{item['start']}–{item['end']}   {item['name']} · {description}"
            widget.setText(text)
            widget.setToolTip(text)
        self.calibration.set_label_source(source)
        self.calibrate_all.setEnabled(bool(count))
        self._update_add_selected()
        self.training_summary.setText(
            f"{count} of {self.ranges.count()} ranges have labels usable for training."
            if self.ranges.count() else "Create Tracker ranges or add the full playback as one cue."
        )

    def _update_add_selected(self):
        """Enables training when a selected range has a usable label."""
        source = self.pose_field.currentData()
        field = self.range_fields.get(source)
        self.calibrate.setEnabled(any(
            any(model.get_training_labels(item.data(QtCore.Qt.ItemDataRole.UserRole), source, field))
            for item in self.ranges.selectedItems()
        ))

    def set_joint_map(self, mapping):
        """Displays resolved or manually saved joint assignments.

        Args:
            mapping (dict): Joint paths keyed by role.
        """
        for index, role in enumerate(scene.ROLE_NAMES):
            label = QtWidgets.QTableWidgetItem(role.replace("_", " ").capitalize())
            label.setFlags(label.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.joints.setItem(index, 0, label)
            self.set_joint(index, mapping.get(role, ""))
        self.joints.resizeColumnToContents(0)

    def set_joint(self, row, path):
        """Stores the full path and displays it using the current path mode.

        Args:
            row (int): Role row to update.
            path (str): Full DAG path or manually entered name.
        """
        text = path if self.show_full_paths.isChecked() else path.rsplit("|", 1)[-1]
        blocked = self.joints.blockSignals(True)
        try:
            item = self.joints.item(row, 1)
            if item is None:
                item = QtWidgets.QTableWidgetItem()
                self.joints.setItem(row, 1, item)
            item.setText(text)
            item.setToolTip(path)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
        finally:
            self.joints.blockSignals(blocked)

    def _joint_edited(self, item):
        """Keeps a manually edited joint label and its stored path in sync.

        Args:
            item (QTableWidgetItem): Edited table cell.
        """
        if item.column() == 1:
            self.set_joint(item.row(), item.text().strip())

    def get_joint_map(self):
        """Reads joint paths from the table independently of the display mode.

        Returns:
            dict: Nonempty full joint names by role.
        """
        paths = [
            self.joints.item(row, 1).data(QtCore.Qt.ItemDataRole.UserRole) for row in range(len(scene.ROLE_NAMES))
        ]
        return {role: path for role, path in zip(scene.ROLE_NAMES, paths) if path}

    def _refresh_joint_paths(self, *args):
        """Refreshes only the displayed names after changing path mode."""
        self.set_joint_map(self.get_joint_map())

    def set_ranges(self, ranges, selected_ids=()):
        """Lists usable ranges and highlights the active Tracker selection.

        Args:
            ranges (list): Existing Tracker range dictionaries.
            selected_ids (tuple or set): IDs to keep selected.
        """
        was_blocked = self.ranges.blockSignals(True)
        self.ranges.clear()
        for item in ranges:
            widget = QtWidgets.QListWidgetItem(f"{item['start']}–{item['end']}   {item['name']}")
            widget.setData(QtCore.Qt.ItemDataRole.UserRole, item)
            self.ranges.addItem(widget)
            if item["id"] in selected_ids:
                widget.setSelected(True)
        self.ranges.blockSignals(was_blocked)
        self._update_training_labels()

    def read_settings(self):
        """Collects current configuration without persisting it.

        Returns:
            dict: Current Auto Annotate settings.
        """
        return {
            **self.options,
            **self.vlm.read_settings(),
            "use_profile": self.showing_custom,
            "calibration": self.read_calibration(),
            "skeleton_mode": self.skeleton_mode.currentData(),
            "skeleton_root": self.skeleton_root.text().strip(),
            "joint_map": self.get_joint_map(),
            "show_full_joint_paths": self.show_full_paths.isChecked(),
            "short_name_fallback": self.short_name_fallback.isChecked(),
            "pose_field": self.pose_field.currentData() or self.options["pose_field"],
            "fill_mode": self.fill_mode.currentData(),
            "auto_save": self.auto_save.isChecked(),
            "commercial_use": {"keep": None, "true": True, "false": False}[self.commercial_use.currentData()],
            "file_source_mode": self.source_mode.currentData(),
            "file_source": self.source_value.text().strip(),
            "file_source_pattern": self.source_pattern.text().strip(),
            "file_source_depth": self.source_depth.value(),
            "file_source_order": self.source_order.currentData(),
            "file_source_fallback": self.source_fallback.currentData(),
            "file_style_source": self.file_style_source.currentData(),
            "file_style": self.file_style.currentText().strip(),
            "auto_set_quality": self.set_quality.isChecked(),
            "quality_preset": self.quality_editor.preset,
            "auto_set_clipped": self.set_clipped.isChecked(),
            "auto_set_annotated": self.set_annotated.isChecked(),
        }

    def apply_settings(self, settings):
        """Refreshes all inputs from a fresh settings dictionary.

        Args:
            settings (dict): Defaults or reloaded Auto Annotate preferences.
        """
        self.options = dict(settings)
        self.vlm.apply_settings(settings)
        for control, key in (
            (self.skeleton_mode, "skeleton_mode"), (self.file_style_source, "file_style_source"),
            (self.fill_mode, "fill_mode"), (self.source_mode, "file_source_mode"),
            (self.source_order, "file_source_order"), (self.source_fallback, "file_source_fallback"),
        ):
            control.setCurrentIndex(max(0, control.findData(settings[key])))
        self.select_label_source(settings["pose_field"])
        self.skeleton_root.setText(settings["skeleton_root"])
        for control, key in (
            (self.auto_save, "auto_save"), (self.show_full_paths, "show_full_joint_paths"),
            (self.short_name_fallback, "short_name_fallback"),
            (self.set_quality, "auto_set_quality"), (self.set_clipped, "auto_set_clipped"),
            (self.set_annotated, "auto_set_annotated"),
        ):
            control.setChecked(settings[key])
        commercial_value = {None: "keep", True: "true", False: "false"}[settings["commercial_use"]]
        self.commercial_use.setCurrentIndex(self.commercial_use.findData(commercial_value))
        self._set_style_value(settings["file_style"])
        self.source_value.setText(settings["file_source"])
        self.source_pattern.setText(settings["file_source_pattern"])
        self.source_depth.setValue(settings["file_source_depth"])
        self.set_joint_map(settings["joint_map"])
        self.quality_editor.set_preset(settings["quality_preset"] or presets.DEFAULT_PRESET)
        self._update_controls()
        self._update_training_labels()
        self.set_calibration(settings["calibration"], activate=settings["use_profile"])
