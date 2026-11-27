"""Measured cue inspector and pose cue selection for Annotation Setup."""

import copy

from gt.tools.annotation_tracker import auto_annotation_model as model
from gt.tools.annotation_tracker import auto_annotation_rules as rules
from gt.ui.qt_import import QtCore, QtWidgets


CUE_DISPLAY = {
    "speed": ("Speed", "leg lengths/s", "Measured pelvis travel or alternating foot motion for in-place gait."),
    "pelvis_height": ("Pelvis height", "leg lengths", "Height of the pelvis above the estimated support plane."),
    "left_foot_height": ("Left foot height", "leg lengths", "Left toe or ankle height above the support plane."),
    "right_foot_height": ("Right foot height", "leg lengths", "Right toe or ankle height above the support plane."),
    "knee_height": ("Lowest knee height", "leg lengths", "Height of the lower knee above the support plane."),
    "knee_flexion": ("Maximum knee flexion", "degrees", "Largest measured flexion from a straight leg."),
    "thigh_ratio": ("Thigh vertical ratio", "ratio", "Vertical fraction of the most horizontal thigh."),
    "foot_separation": ("Foot separation", "leg lengths", "Ground-plane distance between the two feet."),
    "foot_forward": (
        "Feet ahead of pelvis", "leg lengths", "Average forward offset in the character's facing direction."
    ),
    "torso_pitch": ("Torso pitch", "degrees", "Forward or backward torso tilt relative to vertical."),
    "torso_roll": ("Torso roll", "degrees", "Sideways torso tilt relative to vertical."),
    "left_hand_reach": ("Left hand reach", "leg lengths", "Distance from the torso joint to the left hand."),
    "right_hand_reach": ("Right hand reach", "leg lengths", "Distance from the torso joint to the right hand."),
    "hand_separation": ("Hand separation", "leg lengths", "Distance between the two hands."),
}

RULE_FIELDS = {
    "minimum_range_frames": ("Minimum motion frames", "Shorter motion bouts are treated as stationary."),
    "gap_frames": ("Bridge gaps up to", "Fills short interruptions between motion bouts or at the edges of a clip."),
    "transition_buffer_frames": (
        "Transition buffer", "Maximum frames to label at a travel boundary.\nShort bouts use a smaller buffer."
    ),
    "minimum_travel": (
        "Minimum root travel", "Horizontal excursion required for travel.\nRepeated in-place gait can also qualify."
    ),
    "start_speed_multiplier": (
        "Start speed multiplier", "Motion must clear idle speed multiplied by this value to start.\n"
        "Once active, motion continues down to the idle threshold."
    ),
    "transition_mode": ("Transition labels", "Choose whether Enter and Exit describe arrival or movement."),
    "allow_initial_departure": (
        "Allow an exit before an arrival",
        "In arrival/departure mode, label exits from activities already in progress.",
    ),
    "require_paired_transitions": (
        "Require Enter followed by Exit", "Keeps transitions only when both boundaries can be generated.\n"
        "Activities that continue to the end stay unpaired."
    ),
    "pose_threshold": ("Default match threshold", "Maximum normalized cue distance.\nSmaller values are stricter."),
    "pose_minimum_frames": ("Default pose hold", "Consecutive matching frames required before recognizing a pose."),
    "pose_margin": (
        "Minimum lead over another label", "Minimum distance between the best pose and a competing pose.\n"
        "Increase this to leave more ambiguous poses unlabeled."
    ),
}


def fit_button(button):
    """Widens a button so its text is never cropped by padding or styles.

    Args:
        button (QPushButton): Button to size.
    """
    button.setMinimumWidth(button.fontMetrics().horizontalAdvance(button.text()) + 44)


SPEED_CHIP_STYLES = {
    "Idle": "#5B7C99", "Walk": "#5E9A6B", "Run": "#C48A3A", "Sprint": "#B35A5A",
}


class SpeedChip(QtWidgets.QFrame):
    """Shows one speed limit as a centered, color-coded box."""

    def __init__(self, title, parent=None):
        """Builds the chip.

        Args:
            title (str): Locomotion state name.
            parent (QWidget, optional): Chip row.
        """
        super().__init__(parent)
        color = SPEED_CHIP_STYLES.get(title, "#777777")
        self.setObjectName("speedChip")
        self.setStyleSheet(
            f"QFrame#speedChip {{ background-color: #3A3A3A; border: 1px solid {color};"
            f" border-left: 5px solid {color}; border-radius: 3px; }}"
            "QFrame#speedChip QLabel { background: transparent; border: none; }"
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)
        self.title = QtWidgets.QLabel(title.upper())
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(f"color: {color}; font-size: 9px; font-weight: bold;")
        self.value = QtWidgets.QLabel("—")
        self.value.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.value.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, text):
        """Displays the limit.

        Args:
            text (str): Formatted value.
        """
        self.value.setText(text)


class SpeedThresholdEditor(QtWidgets.QGroupBox):
    """Edits the idle, walk and run speed limits of a custom profile."""

    edited = QtCore.Signal()

    def __init__(self, parent=None):
        """Builds the threshold spin boxes.

        Args:
            parent (QWidget, optional): Rules page.
        """
        super().__init__("Speed limits (leg lengths/s)", parent)
        layout = QtWidgets.QVBoxLayout(self)
        options = QtWidgets.QHBoxLayout()
        self.learn = QtWidgets.QCheckBox("Learn from idle/walk/run ranges")
        self.learn.setChecked(True)
        self.learn.setToolTip(
            "On: training with ranges whose State is idle, walk, run or sprint can update the limits.\n"
            "Off: only pose cues are learned and the speed limits are never touched.\n"
            "Always off while 'Set manually' is on."
        )
        self.manual = QtWidgets.QCheckBox("Set manually")
        self.manual.setToolTip(
            "Off: limits are learned from labeled idle, walk, run or sprint ranges (or use the defaults).\n"
            "On: type the limits yourself. Adding more speed cues later may replace them."
        )
        options.addWidget(self.learn)
        options.addWidget(self.manual)
        options.addStretch()
        layout.addLayout(options)
        self.idle = QtWidgets.QDoubleSpinBox()
        self.walk = QtWidgets.QDoubleSpinBox()
        self.run = QtWidgets.QDoubleSpinBox()
        for control in (self.idle, self.walk, self.run):
            control.setDecimals(3)
            control.setSingleStep(0.05)
            control.setMinimumWidth(110)
        self.idle.setRange(0.01, 20.0)
        self.walk.setRange(0.02, 40.0)
        self.run.setRange(0.0, 60.0)
        self.run.setSpecialValueText("Off (no sprint)")
        self.idle.setToolTip("Below this speed the character is idle. Trained idle/walk cues update it.")
        self.walk.setToolTip("Walking up to this speed. Trained walk/run cues update it.")
        self.run.setToolTip("Running up to this speed; faster is sprint. Off keeps run as the top state.")
        values = QtWidgets.QHBoxLayout()
        for text, control in (("Idle up to", self.idle), ("Walk up to", self.walk), ("Run up to", self.run)):
            values.addWidget(QtWidgets.QLabel(text))
            values.addWidget(control, 1)
        layout.addLayout(values)
        self.idle.valueChanged.connect(self._keep_order)
        self.walk.valueChanged.connect(self._keep_order)
        self.locked = True
        for control in (self.idle, self.walk, self.run):
            control.valueChanged.connect(lambda *args: self.edited.emit())
        self.manual.toggled.connect(self._update_enabled)
        self._update_enabled()

    def _update_enabled(self, *args):
        """Enables the spin boxes only while manual editing is on."""
        for control in (self.idle, self.walk, self.run):
            control.setEnabled(self.manual.isChecked() and not self.locked)

    def set_locked(self, locked):
        """Locks the editor while the built-in profile is shown.

        Args:
            locked (bool): Whether editing is unavailable.
        """
        self.locked = locked
        self.manual.setEnabled(not locked)
        self.learn.setEnabled(not locked)
        self._update_enabled()

    def learns_speeds(self):
        """Reports whether training may change the speed limits.

        Returns:
            bool: True when learning is on and manual editing is off.
        """
        return self.learn.isChecked() and not self.manual.isChecked()

    def _keep_order(self, *args):
        """Keeps idle < walk < run while editing."""
        if self.walk.value() <= self.idle.value():
            self.walk.setValue(self.idle.value() + 0.05)
        if self.run.value() and self.run.value() <= self.walk.value():
            self.run.setValue(self.walk.value() + 0.05)

    def set_values(self, locomotion):
        """Shows profile thresholds or the built-in defaults.

        Args:
            locomotion (dict): Profile locomotion thresholds, possibly empty.
        """
        controls = (self.idle, self.walk, self.run)
        for control in controls:
            control.blockSignals(True)
        self.idle.setValue(locomotion.get("idle_max_speed", model.DEFAULT_IDLE_SPEED))
        self.walk.setValue(locomotion.get("walk_max_speed", model.DEFAULT_WALK_SPEED))
        self.run.setValue(locomotion.get("run_max_speed", 0.0))
        for control in controls:
            control.blockSignals(False)

    def read_values(self):
        """Gets thresholds that differ from the defaults.

        Returns:
            dict: Locomotion thresholds, or an empty dict when all values are default.
        """
        values = {"idle_max_speed": self.idle.value(), "walk_max_speed": self.walk.value()}
        if self.run.value():
            values["run_max_speed"] = self.run.value()
        defaults = {"idle_max_speed": model.DEFAULT_IDLE_SPEED, "walk_max_speed": model.DEFAULT_WALK_SPEED}
        return {} if values == defaults else values


class CalibrationRuleEditor(QtWidgets.QWidget):
    """Shows editable profile rules or the locked defaults."""

    def __init__(self, parent=None):
        """Builds the calibration rule controls.

        Args:
            parent (QWidget, optional): Calibration tab.
        """
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.controls = {}
        pose_keys = ("pose_threshold", "pose_minimum_frames", "pose_margin")
        for title, keys in (
            ("Motion and transitions", [key for key in RULE_FIELDS if key not in pose_keys]),
            ("Learned poses", pose_keys),
        ):
            group = QtWidgets.QGroupBox(title)
            form = QtWidgets.QFormLayout(group)
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            for key in keys:
                label, tooltip = RULE_FIELDS[key]
                default, minimum, maximum = rules.RULES[key]
                if type(default) is bool:
                    control = QtWidgets.QCheckBox(label)
                    form.addRow(control)
                elif isinstance(default, str):
                    control = QtWidgets.QComboBox()
                    for value, text in rules.TRANSITION_MODES.items():
                        control.addItem(text, value)
                    form.addRow(label, control)
                else:
                    control = QtWidgets.QSpinBox() if type(default) is int else QtWidgets.QDoubleSpinBox()
                    control.setRange(minimum, maximum)
                    control.setMinimumWidth(150)
                    if type(default) is int:
                        control.setSuffix(" frames")
                    else:
                        control.setDecimals(2)
                        control.setSingleStep(0.05)
                    if key == "minimum_travel":
                        control.setSuffix(" leg lengths")
                    form.addRow(label, control)
                control.setToolTip(tooltip)
                self.controls[key] = control
            layout.addWidget(group)
        layout.addStretch()
        self.set_rules({}, locked=True)

    def set_rules(self, values, locked=False):
        """Displays defaults with any profile-specific values.

        Args:
            values (dict): Calibration profile rule values.
            locked (bool): Locks controls while viewing the built-in profile.
        """
        self.locked = locked
        self.saved_rule_keys = set(values)
        for key, control in self.controls.items():
            value = values.get(key, rules.DEFAULT_RULES[key])
            if isinstance(control, QtWidgets.QCheckBox):
                control.setChecked(value)
            elif isinstance(control, QtWidgets.QComboBox):
                control.setCurrentIndex(control.findData(value))
            else:
                control.setValue(value)
            control.setEnabled(not locked)

    def read_rules(self):
        """Gets explicit rule values and changes from the built-in profile.

        Returns:
            dict: Rule values stored for this profile.
        """
        values = {}
        for key, control in self.controls.items():
            if isinstance(control, QtWidgets.QCheckBox):
                value = control.isChecked()
            elif isinstance(control, QtWidgets.QComboBox):
                value = control.currentData()
            else:
                value = control.value()
            if key in self.saved_rule_keys or value != rules.DEFAULT_RULES[key]:
                values[key] = value
        return values


class CalibrationInspector(QtWidgets.QWidget):
    """Displays measured example ranges and sets the cues used for pose matching."""

    profile_changed = QtCore.Signal()

    def __init__(self, parent=None, activity_available=True):
        """Builds the cue inspector.

        Args:
            parent (QWidget, optional): Calibration tab.
            activity_available (bool): Whether the active schema supports the activity state.
        """
        super().__init__(parent)
        self.profile = None
        self.locked = False
        self.use_names = True
        self.examples = []
        self.cue_checks = {}
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.speed_summary = QtWidgets.QWidget()
        chips_layout = QtWidgets.QVBoxLayout(self.speed_summary)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(2)
        self.speed_source = QtWidgets.QLabel()
        self.speed_source.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        chips_row = QtWidgets.QHBoxLayout()
        self.speed_chips = {name: SpeedChip(name) for name in SPEED_CHIP_STYLES}
        chips_row.addStretch()
        for chip in self.speed_chips.values():
            chip.setMinimumWidth(92)
            chips_row.addWidget(chip)
        chips_row.addStretch()
        chips_layout.addWidget(self.speed_source)
        chips_layout.addLayout(chips_row)
        standing = model.DEFAULT_STANDING_CUES
        self.speed_source.setToolTip(
            "Baseline and calibrated locomotion both use speed.\n"
            "Labeled idle, walk, run and sprint cues can tune speed thresholds when their bands are distinct.\n"
            f"Default standing also uses pelvis height ≥ {standing['pelvis_height']:g} leg lengths, "
            f"knee flexion ≤ {standing['knee_flexion']:g}°, torso pitch ≤ {standing['torso_pitch']:g}°, "
            f"and torso roll ≤ {standing['torso_roll']:g}° when those cues are available."
        )
        layout.addWidget(self.speed_summary)
        self.example = QtWidgets.QComboBox()
        self.example.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.example.setMinimumContentsLength(25)
        self.example.setToolTip(
            "Select a stored pose or speed cue to see its measurements.\n"
            "Each cue summarizes a frame range using low, median, and high values."
        )
        example_row = QtWidgets.QHBoxLayout()
        example_row.setContentsMargins(0, 0, 0, 0)
        example_row.addWidget(self.example, 1)
        self.rename_label = QtWidgets.QPushButton("Rename Label")
        self.rename_label.setToolTip("Rename the label of the selected cue (merges with an existing label).")
        self.delete_example = QtWidgets.QPushButton("Delete Cue")
        self.delete_example.setToolTip("Remove the selected cue from this custom profile.")
        for button in (self.rename_label, self.delete_example):
            fit_button(button)
            example_row.addWidget(button)
        layout.addLayout(example_row)
        self.rename_label.clicked.connect(self._rename_selected)
        self.delete_example.clicked.connect(self._delete_selected)
        self.example_note = QtWidgets.QLabel()
        self.example_note.setWordWrap(True)
        layout.addWidget(self.example_note)
        self.table = QtWidgets.QTableWidget(len(CUE_DISPLAY), 6)
        self.table.setHorizontalHeaderLabels(["Use for pose", "Cue", "Unit", "Low", "Median", "High"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setMinimumSectionSize(42)
        header.setStretchLastSection(True)
        for column, width in enumerate((100, 180, 92, 65, 65)):
            header.resizeSection(column, width)
        header.setToolTip("Drag a column divider to resize it.")
        self.table.horizontalHeaderItem(0).setToolTip(
            "Checked cues contribute to learned pose matching.\n"
            "Measurements are kept when a cue is unchecked. Speed always drives baseline locomotion."
        )
        self.table.setMinimumHeight(190)
        layout.addWidget(self.table)
        for row, (key, (label, unit, description)) in enumerate(CUE_DISPLAY.items()):
            widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True)
            checkbox.setAccessibleName(f"Use {label} for pose matching")
            checkbox.setToolTip(f"Use {label.lower()} when comparing a pose with stored cues.")
            row_layout.addWidget(checkbox, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.cue_checks[key] = checkbox
            self.table.setCellWidget(row, 0, widget)
            item = QtWidgets.QTableWidgetItem(label)
            item.setToolTip(description)
            self.table.setItem(row, 1, item)
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(unit))
            for column in range(3, 6):
                self.table.setItem(row, column, QtWidgets.QTableWidgetItem())
        self.match_options = QtWidgets.QGroupBox("Selected pose cue")
        form = QtWidgets.QFormLayout(self.match_options)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.threshold = QtWidgets.QDoubleSpinBox()
        self.threshold.setRange(-0.01, 4.0)
        self.threshold.setSingleStep(0.05)
        self.threshold.setSpecialValueText("Profile default")
        self.threshold.setToolTip("Maximum distance allowed from this cue.\nSmaller values are stricter.")
        self.minimum_frames = QtWidgets.QSpinBox()
        self.threshold.setMinimumWidth(150)
        self.minimum_frames.setMinimumWidth(150)
        self.minimum_frames.setRange(0, 10000)
        self.minimum_frames.setSpecialValueText("Profile default")
        self.minimum_frames.setToolTip("Consecutive matching frames needed to recognize this cue.")
        self.suffix = QtWidgets.QLineEdit()
        self.suffix.setMaxLength(100)
        self.suffix.setToolTip(
            "Append this text to the generated range name.\n"
            "Leave it blank to use the profile's label source behavior."
        )
        self.detected_state = QtWidgets.QComboBox()
        self.detected_state.addItem("Keep the motion state", "")
        self.detected_state.addItem("Activity when stationary", "activity")
        self.detected_state.setEnabled(activity_available)
        self.detected_state.setToolTip(
            "Use activity for a matching action that does not involve sustained locomotion."
            if activity_available else "Add activity to the active schema's State options to assign it."
        )
        form.addRow("Match threshold", self.threshold)
        form.addRow("Minimum hold frames", self.minimum_frames)
        form.addRow("Range name suffix", self.suffix)
        form.addRow("Detected state", self.detected_state)
        layout.addWidget(self.match_options)
        self.threshold.valueChanged.connect(self._store_example_options)
        self.minimum_frames.valueChanged.connect(self._store_example_options)
        self.suffix.textChanged.connect(self._store_example_options)
        self.detected_state.currentIndexChanged.connect(self._store_example_options)
        self.example.currentIndexChanged.connect(self._show_example)
        self.set_profile(None)

    def set_profile(self, profile, use_calibration=False, focus_example=None, locked=False, use_names=True):
        """Displays a copy of embedded calibration and its active thresholds.

        Args:
            profile (dict or None): Calibration embedded in the current settings.
            use_calibration (bool): Whether the profile is enabled for future runs.
            focus_example (tuple, optional): Section, label and zero-based example index to show.
            locked (bool): Shows the reference criteria of the built-in profile.
            use_names (bool): Uses a learned label as the default range suffix.
        """
        previous = self.example.currentText()
        self.profile = copy.deepcopy(profile)
        self.locked = locked
        self.use_names = use_names
        data = self.profile or {}
        cues = data.get("pose_cues", model.FEATURE_SCALES)
        for key, checkbox in self.cue_checks.items():
            checkbox.setChecked(key in cues)
            checkbox.setEnabled(not locked)
        self.examples = []
        self.example.blockSignals(True)
        self.example.clear()
        standing = model.DEFAULT_STANDING_CUES
        thresholds = data.get("locomotion", {})
        idle = thresholds.get("idle_max_speed", model.DEFAULT_IDLE_SPEED)
        walk = thresholds.get("walk_max_speed", model.DEFAULT_WALK_SPEED)
        run = thresholds.get("run_max_speed")
        references = {
            "Idle": {"speed": (0, None, idle)},
            "Walk": {"speed": (idle, None, walk)},
            "Run": {"speed": (walk, None, run)},
            "Standing": {
                "pelvis_height": (standing["pelvis_height"], None, None),
                "knee_flexion": (0, None, standing["knee_flexion"]),
                "torso_pitch": (-standing["torso_pitch"], None, standing["torso_pitch"]),
                "torso_roll": (-standing["torso_roll"], None, standing["torso_roll"]),
            },
        }
        if run is not None:
            references["Sprint"] = {"speed": (run, None, None)}
        for name, values in references.items():
            self.examples.append(("reference", name, {"features": values}))
            self.example.addItem(f"Reference: {name}")

        focus_row = None
        for section, label in (("locomotion_examples", "Locomotion"), ("poses", "Pose")):
            for name, examples in sorted(data.get(section, {}).items()):
                for index, example in enumerate(examples):
                    if (section, name, index) == focus_example:
                        focus_row = self.example.count()
                    self.examples.append((section, name, example))
                    frames = example["sample_count"]
                    number = f" ({index + 1})" if index else ""
                    self.example.addItem(f"{label}: {name}{number} · {frames} frames")
        row = focus_row if focus_row is not None else max(0, self.example.findText(previous))
        self.example.setCurrentIndex(row)
        self.example.blockSignals(False)
        self.update_speed_summary(use_calibration)
        self._show_example()

    def update_speed_summary(self, use_calibration):
        """Displays the effective idle and walking speed thresholds.

        Args:
            use_calibration (bool): Whether learned thresholds are enabled.
        """
        thresholds = (self.profile or {}).get("locomotion", {}) if use_calibration else {}
        idle = thresholds.get("idle_max_speed", model.DEFAULT_IDLE_SPEED)
        walk = thresholds.get("walk_max_speed", model.DEFAULT_WALK_SPEED)
        run = thresholds.get("run_max_speed")
        source = "Profile" if thresholds else "Default"
        self.speed_source.setText(f"{source} speed limits · leg lengths per second")
        self.speed_chips["Idle"].set_value(f"≤ {idle:g}")
        self.speed_chips["Walk"].set_value(f"≤ {walk:g}")
        self.speed_chips["Run"].set_value(f"≤ {run:g}" if run is not None else f"> {walk:g}")
        self.speed_chips["Sprint"].set_value(f"> {run:g}" if run is not None else "—")

    def _show_example(self, *args):
        """Shows the selected example's recorded low, median and high for each cue."""
        row = self.example.currentIndex()
        section, name, example = self.examples[row] if 0 <= row < len(self.examples) else ("", "", {})
        features = example.get("features", {})
        pose = section == "poses"
        self.match_options.setVisible(pose)
        editable = section in ("poses", "locomotion_examples") and not self.locked
        self.rename_label.setEnabled(editable and pose)
        self.delete_example.setEnabled(editable)
        note = {
            "reference": (
                "Reference limits used by this profile. Speed limits change only when trained idle/walk/run cues "
                "are distinct, or when set manually under Train."
            ),
            "poses": "Measured pose cue. Checked measurements influence matching for this profile.",
            "locomotion_examples": (
                "Measured speed cue. Speed boundaries update when neighboring training bands are distinct."
            ),
        }
        self.example_note.setText(note.get(section, "Add labeled ranges to see their cues here."))
        for control in (self.threshold, self.minimum_frames, self.suffix, self.detected_state):
            control.blockSignals(True)
        self.threshold.setValue(example.get("threshold", -0.01))
        self.minimum_frames.setValue(example.get("minimum_frames", 0))
        self.suffix.setText(example.get("suffix", ""))
        self.suffix.setPlaceholderText(name if self.use_names else "Optional")
        self.detected_state.setCurrentIndex(self.detected_state.findData(example.get("state", "")))
        for control in (self.threshold, self.minimum_frames, self.suffix, self.detected_state):
            control.blockSignals(False)
        for row, key in enumerate(CUE_DISPLAY):
            values = features.get(key)
            if self.locked:
                self.cue_checks[key].setChecked(key in features)
            for offset, column in enumerate(range(3, 6)):
                item = self.table.item(row, column)
                value = values[offset] if values else None
                item.setText(f"{value:.4g}" if value is not None else "—")
                item.setToolTip("" if value is not None else "No value is defined for this cue.")

    def set_label_source(self, source):
        """Updates the inherited suffix shown for the example.

        Args:
            source (str): Range names or the chosen schema field.
        """
        self.use_names = source == rules.RANGE_NAME_FIELD
        self._show_example()

    def _store_example_options(self, *args):
        """Stores optional rule overrides on the selected measured pose."""
        row = self.example.currentIndex()
        if not 0 <= row < len(self.examples) or self.examples[row][0] != "poses":
            return
        example = self.examples[row][2]
        for key, value, inherited in (
            ("threshold", self.threshold.value(), -0.01),
            ("minimum_frames", self.minimum_frames.value(), 0),
            ("suffix", self.suffix.text().strip(), ""),
            ("state", self.detected_state.currentData(), ""),
        ):
            if value == inherited:
                example.pop(key, None)
            else:
                example[key] = value

    def _selected_example(self):
        """Gets the selected stored example.

        Returns:
            tuple or None: Section, label and index within its label, or None for references.
        """
        row = self.example.currentIndex()
        if not 0 <= row < len(self.examples) or self.examples[row][0] == "reference" or self.profile is None:
            return None
        section, name, example = self.examples[row]
        group = self.profile.get(section, {}).get(name, [])
        index = next((position for position, item in enumerate(group) if item is example), None)
        return None if index is None else (section, name, index)

    def _delete_selected(self):
        """Removes the selected example from the displayed custom profile."""
        selected = self._selected_example()
        if selected is None:
            return
        section, name, index = selected
        group = self.profile[section][name]
        del group[index]
        if not group:
            del self.profile[section][name]
        if section == "locomotion_examples":
            model.refresh_locomotion(self.profile)
        self.set_profile(self.profile, True, locked=self.locked, use_names=self.use_names)
        self.profile_changed.emit()

    def _rename_selected(self):
        """Renames the label of the selected pose example."""
        selected = self._selected_example()
        if selected is None or selected[0] != "poses":
            return
        _, name, index = selected
        new_name, accepted = QtWidgets.QInputDialog.getText(
            self, "Rename Label", "Pose label", QtWidgets.QLineEdit.EchoMode.Normal, name
        )
        new_name = new_name.strip()
        if not accepted or not new_name or new_name == name:
            return
        example = self.profile["poses"][name].pop(index)
        if not self.profile["poses"][name]:
            del self.profile["poses"][name]
        group = self.profile["poses"].setdefault(new_name, [])
        group.append(example)
        self.set_profile(
            self.profile, True, ("poses", new_name, len(group) - 1), locked=self.locked, use_names=self.use_names
        )

    def read_profile(self):
        """Copies the calibration with the current pose cue switches applied.

        Returns:
            dict or None: Calibration to embed in settings.
        """
        cues = [name for name in model.FEATURE_SCALES if self.cue_checks[name].isChecked()]
        profile = copy.deepcopy(self.profile)
        if len(cues) != len(self.cue_checks) or (profile and "pose_cues" in profile):
            profile = profile or model.new_profile()
            profile["pose_cues"] = cues
        return profile
