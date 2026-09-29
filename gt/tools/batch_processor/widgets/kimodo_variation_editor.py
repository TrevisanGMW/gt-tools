"""Compact editor for Kimodo parameter variation ranges."""

import json
import math
from functools import partial
from gt.ui import qt_import as qt


class KimodoVariationRangeEditor(qt.QtWidgets.QWidget):
    """Edits supported min/max variation ranges without exposing raw JSON."""

    RANGE_SPECS = (
        ("diffusion_steps", "Denoising steps", True, 1, 1000),
        ("heading", "Heading (radians)", False, -6.283, 6.283),
        ("guidance_text", "Text guidance", False, 0, 20),
        ("guidance_constraints", "Pose guidance", False, 0, 20),
        ("duration_seconds", "Total duration (seconds)", False, 0.001, 1000000),
    )

    def __init__(self, ranges, setter, defaults=None, parent=None):
        """Builds a labeled min/max editor for each supported parameter.

        Args:
            ranges (dict or str): Existing ranges in the task's serialized format.
            setter (callable): Receives an updated range dictionary.
            defaults (dict, optional): Default min/max pairs for unchecked rows.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setter = setter
        self.defaults = defaults or {}
        self.inputs = {}
        self.invalid_reason = ""
        self.initializing = True
        self.range_values = self._parse_ranges(ranges)

        layout = qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.hint = qt.QtWidgets.QLabel(
            "Check a parameter to sample between its minimum and maximum for each definition. "
            "Steps are whole numbers; the other ranges are continuous. Duration ranges require retiming."
        )
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        self.error_label = qt.QtWidgets.QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(bool(self.invalid_reason))
        layout.addWidget(self.error_label)

        grid = qt.QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.addWidget(qt.QtWidgets.QLabel("Parameter"), 0, 0)
        grid.addWidget(qt.QtWidgets.QLabel("Minimum"), 0, 1)
        grid.addWidget(qt.QtWidgets.QLabel("Maximum"), 0, 2)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        for row, (key, label, is_integer, minimum, maximum) in enumerate(self.RANGE_SPECS, 1):
            checkbox = qt.QtWidgets.QCheckBox(label)
            checkbox.setChecked(key in self.range_values)
            checkbox.setToolTip(self._tooltip_for_key(key))
            grid.addWidget(checkbox, row, 0)

            start_values = self.range_values.get(key, self.defaults.get(key, [0, 0]))
            use_integer_control = is_integer and all(float(value).is_integer() for value in start_values)
            spin_type = qt.QtWidgets.QSpinBox if use_integer_control else qt.QtWidgets.QDoubleSpinBox
            minimum_spin = spin_type()
            maximum_spin = spin_type()
            spin_minimum = min(minimum, float(start_values[0]))
            spin_maximum = max(maximum, float(start_values[1]))
            if use_integer_control:
                start_values = [int(value) for value in start_values]
                spin_minimum = int(spin_minimum)
                spin_maximum = int(spin_maximum)
            for spin_box in (minimum_spin, maximum_spin):
                spin_box.setRange(spin_minimum, spin_maximum)
                spin_box.setMinimumHeight(30)
                if not use_integer_control:
                    spin_box.setDecimals(3)
                    spin_box.setSingleStep(0.1)
            minimum_spin.setValue(start_values[0])
            maximum_spin.setValue(start_values[1])
            grid.addWidget(minimum_spin, row, 1)
            grid.addWidget(maximum_spin, row, 2)
            self.inputs[key] = (checkbox, minimum_spin, maximum_spin, use_integer_control)

        layout.addLayout(grid)
        actions = qt.QtWidgets.QHBoxLayout()
        self.clear_button = qt.QtWidgets.QPushButton("Clear Ranges")
        self.clear_button.setToolTip("Remove all parameter ranges and reset malformed saved ranges.")
        self.clear_button.clicked.connect(self.clear_ranges)
        actions.addWidget(self.clear_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        for key, (checkbox, minimum_spin, maximum_spin, unused_is_integer) in self.inputs.items():
            checkbox.toggled.connect(partial(self.set_row_enabled, key))
            minimum_spin.valueChanged.connect(self.commit)
            maximum_spin.valueChanged.connect(self.commit)
            self.set_row_enabled(key, checkbox.isChecked())
        self.initializing = False
        if self.invalid_reason:
            self._set_invalid_state()

    def _parse_ranges(self, ranges):
        """Loads supported ranges while retaining invalid input for explicit reset.

        Args:
            ranges (dict or str): Saved range data.

        Returns:
            dict: Valid min/max pairs.
        """
        if isinstance(ranges, str):
            try:
                ranges = json.loads(ranges)
            except ValueError as error:
                self.invalid_reason = f"Saved parameter ranges are not valid JSON: {error}"
                return {}
        if not isinstance(ranges, dict):
            self.invalid_reason = "Saved parameter ranges must be an object. Use Clear Ranges to reset them."
            return {}
        allowed = {spec[0] for spec in self.RANGE_SPECS}
        unsupported = set(ranges) - allowed
        if unsupported:
            names = ", ".join(sorted(str(key) for key in unsupported))
            self.invalid_reason = f"Unsupported saved range(s): {names}. Use Clear Ranges to reset them."
            return {}
        parsed = {}
        for key, bounds in ranges.items():
            try:
                invalid_values = any(type(value) not in (int, float) or not math.isfinite(value)
                                    for value in bounds)
            except (OverflowError, TypeError):
                invalid_values = True
            if (not isinstance(bounds, list) or len(bounds) != 2 or invalid_values or bounds[0] > bounds[1]):
                self.invalid_reason = (
                    f"Saved min/max values for {key} are invalid. Use Clear Ranges to reset them."
                )
                return {}
            parsed[key] = list(bounds)
        return parsed

    def _tooltip_for_key(self, key):
        """Returns one short explanation for a range control.

        Args:
            key (str): Kimodo parameter key.

        Returns:
            str: Control help text.
        """
        descriptions = {
            "diffusion_steps": "Whole-number denoising iterations. Both endpoints are included.",
            "heading": "Initial facing direction in radians.",
            "guidance_text": "Text prompt guidance strength.",
            "guidance_constraints": "Pose constraint guidance strength.",
            "duration_seconds": "Total generated clip duration. Requires Retime Constraints.",
        }
        return descriptions[key]

    def _set_invalid_state(self):
        """Displays the retained-data warning and disables edits until reset."""
        self.error_label.setText(self.invalid_reason)
        self.error_label.setVisible(True)
        for checkbox, minimum_spin, maximum_spin, unused_is_integer in self.inputs.values():
            checkbox.setEnabled(False)
            minimum_spin.setEnabled(False)
            maximum_spin.setEnabled(False)

    def set_row_enabled(self, key, enabled):
        """Enables min/max editors only when their parameter is selected.

        Args:
            key (str): Kimodo parameter key.
            enabled (bool): Whether that range is active.
        """
        checkbox, minimum_spin, maximum_spin, unused_is_integer = self.inputs[key]
        checkbox.setEnabled(not self.invalid_reason)
        minimum_spin.setEnabled(enabled and not self.invalid_reason)
        maximum_spin.setEnabled(enabled and not self.invalid_reason)
        if not self.invalid_reason and not self.initializing:
            self.commit()

    def commit(self, unused_value=None):
        """Serializes the checked rows through the task settings callback.

        Args:
            unused_value (object, optional): Qt signal value.
        """
        if self.invalid_reason or self.initializing:
            return
        ranges = {}
        for key, (checkbox, minimum_spin, maximum_spin, is_integer) in self.inputs.items():
            if not checkbox.isChecked():
                continue
            lower = minimum_spin.value()
            upper = maximum_spin.value()
            ranges[key] = [int(lower), int(upper)] if is_integer else [float(lower), float(upper)]
        self.setter(ranges)

    def clear_ranges(self, unused_checked=False):
        """Clears all ranges, including malformed data retained from a project file.

        Args:
            unused_checked (bool, optional): Qt button signal value.
        """
        self.invalid_reason = ""
        self.error_label.clear()
        self.error_label.setVisible(False)
        for key, (checkbox, minimum_spin, maximum_spin, unused_is_integer) in self.inputs.items():
            checkbox.setEnabled(True)
            checkbox.setChecked(False)
            default_values = self.defaults.get(key, [0, 0])
            minimum_spin.setValue(default_values[0])
            maximum_spin.setValue(default_values[1])
        self.commit()
