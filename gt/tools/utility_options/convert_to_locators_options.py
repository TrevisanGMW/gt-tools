"""Options window for converting selected transforms to locators."""

import logging

import gt.ui.option_window as ui_option_window
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Bake range labels
BAKE_RANGE_PLAYBACK = "Playback Range"
BAKE_RANGE_CUSTOM = "Custom Range"

# Transform behavior labels
MODE_MATCH_TRANSFORMS = "Match Transforms"
MODE_BAKE_TRANSFORMS = "Bake Transforms"
MODE_CONSTRAINT_TRANSFORMS = "Constraint Transforms"

# Locator color labels
COLOR_NONE = "No Color"
COLOR_AUTO_SIDE = "Auto Side Color"
COLOR_CUSTOM = "Custom Color"


def _add_axis_controls(window, label, key_prefix):
    """Adds a labeled row of enabled-by-default X, Y, and Z checkboxes.

    Args:
        window (OptionWindow): Window that receives the controls.
        label (str): Channel family label shown next to the checkboxes.
        key_prefix (str): Prefix used for stable control lookup keys.

    Returns:
        list: Checkboxes for X, Y, and Z in axis order.
    """
    row_widget = ui_qt.QtWidgets.QWidget(window)
    row_layout = ui_qt.QtWidgets.QHBoxLayout(row_widget)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(12)
    row_layout.addStretch(1)

    checkboxes = []
    for axis_name in "XYZ":
        checkbox = ui_qt.QtWidgets.QCheckBox(axis_name)
        checkbox.setChecked(True)
        checkbox.setToolTip(f"Copy the {label.lower()} {axis_name} channel.")
        row_layout.addWidget(checkbox)
        window.controls[f"{key_prefix}_{axis_name.lower()}"] = checkbox
        checkboxes.append(checkbox)

    row_layout.addStretch(1)
    window._build_field_row(label, row_widget)
    return checkboxes


def _get_playback_range():
    """Returns Maya's current playback range, with a safe UI fallback.

    Returns:
        tuple: Playback start and end frame values.
    """
    try:
        import maya.cmds as cmds

        return (
            int(round(cmds.playbackOptions(query=True, minTime=True))),
            int(round(cmds.playbackOptions(query=True, maxTime=True))),
        )
    except Exception as exception:
        logger.debug(f'Unable to read Maya playback range. Issue: "{exception}".')
        return 1, 24


def open_convert_to_locators_options():
    """Opens the "Convert to Locators" option window.

    Returns:
        OptionWindow: The created option window.
    """
    window = ui_option_window.OptionWindow(
        title="Convert to Locators",
        object_name="gtConvertToLocatorsOptions",
        icon=ui_res_lib.Icon.util_convert_loc,
        description="Create locators for the selected objects and keep the source objects intact.",
        workspace_restore_factory=(
            "gt.tools.utility_options.convert_to_locators_options.open_convert_to_locators_options"
        ),
    )

    translate_controls = _add_axis_controls(window, "Translate", "translate")
    rotate_controls = _add_axis_controls(window, "Rotate", "rotate")
    scale_controls = _add_axis_controls(window, "Scale", "scale")
    window.add_separator()

    transform_mode_combo = window.add_combobox(
        "Transform Mode",
        [MODE_MATCH_TRANSFORMS, MODE_BAKE_TRANSFORMS, MODE_CONSTRAINT_TRANSFORMS],
        default=MODE_MATCH_TRANSFORMS,
        tooltip="Match the current pose, bake animation across a range, or keep live constraints.",
        key="transform_mode",
    )
    bake_range_combo = window.add_combobox(
        "Bake Range",
        [BAKE_RANGE_PLAYBACK, BAKE_RANGE_CUSTOM],
        default=BAKE_RANGE_PLAYBACK,
        tooltip="Use Maya's playback range or enter a custom inclusive start and end frame.",
        key="bake_range",
    )
    playback_start, playback_end = _get_playback_range()
    start_frame = window.add_spinbox(
        "Start Frame",
        default=playback_start,
        minimum=-100000,
        maximum=100000,
        key="start_frame",
    )
    end_frame = window.add_spinbox(
        "End Frame",
        default=playback_end,
        minimum=-100000,
        maximum=100000,
        key="end_frame",
    )

    def _copy_timeline_range():
        """Copies Maya's current playback range into the custom frame fields."""
        timeline_start, timeline_end = _get_playback_range()
        start_frame.setValue(timeline_start)
        end_frame.setValue(timeline_end)

    get_range_button = window.add_button_row(
        [
            {
                "label": "Get Timeline Range",
                "command": _copy_timeline_range,
                "tooltip": "Copy Maya's current playback start and end into the custom range.",
            }
        ]
    )[0]
    window.add_separator()

    shape_scale = window.add_double_spinbox(
        "Locator Shape Scale",
        default=1.0,
        minimum=0.01,
        maximum=1000.0,
        step=0.1,
        decimals=2,
        tooltip="Changes the locator shape size without scaling its transform.",
        key="locator_shape_scale",
    )
    color_combo = window.add_combobox(
        "Color",
        [COLOR_NONE, COLOR_AUTO_SIDE, COLOR_CUSTOM],
        default=COLOR_NONE,
        tooltip="Choose no override, the auto rigger's X-side color setup, or one custom color.",
        key="color_mode",
    )

    custom_color = (1.0, 0.4, 0.4)
    color_button = ui_qt.QtWidgets.QPushButton("Choose Color")
    color_button.setMinimumHeight(window.CONTROL_HEIGHT)
    color_button.setToolTip("Select the viewport override color used for each locator.")
    window._build_field_row("Custom Color", color_button)
    window.controls["custom_color"] = color_button

    def _update_enabled_controls():
        """Enables range and color controls only when their modes require them."""
        is_bake_mode = transform_mode_combo.currentText() == MODE_BAKE_TRANSFORMS
        is_custom_range = bake_range_combo.currentText() == BAKE_RANGE_CUSTOM
        window.set_row_enabled(bake_range_combo, is_bake_mode)
        window.set_row_enabled(start_frame, is_bake_mode and is_custom_range)
        window.set_row_enabled(end_frame, is_bake_mode and is_custom_range)
        get_range_button.setEnabled(is_bake_mode and is_custom_range)
        window.set_row_enabled(color_combo, True)
        window.set_row_enabled(
            window.controls["custom_color"],
            color_combo.currentText() == COLOR_CUSTOM,
        )

    def _choose_custom_color():
        """Opens a color dialog and stores the selected RGB value."""
        nonlocal custom_color
        initial_color = ui_qt.QtGui.QColor.fromRgbF(*custom_color)
        chosen_color = ui_qt.QtWidgets.QColorDialog.getColor(
            initial_color,
            window,
            "Choose Locator Color",
        )
        if not chosen_color.isValid():
            return
        custom_color = (chosen_color.redF(), chosen_color.greenF(), chosen_color.blueF())
        color_button.setStyleSheet(
            "QPushButton {"
            f"background-color: rgb({chosen_color.red()}, {chosen_color.green()}, {chosen_color.blue()});"
            "color: #202020; border: 1px solid #444444; padding: 2px 6px; }"
        )

    def _convert_to_locators():
        """Runs the conversion using the values currently shown in the window."""
        from gt.core import transform as core_transform

        selected_transform_mode = transform_mode_combo.currentText()
        bake_range = None
        if selected_transform_mode == MODE_BAKE_TRANSFORMS:
            if bake_range_combo.currentText() == BAKE_RANGE_CUSTOM:
                bake_start = start_frame.value()
                bake_end = end_frame.value()
            else:
                bake_start, bake_end = _get_playback_range()
            if bake_start > bake_end:
                import maya.cmds as cmds

                cmds.warning("Bake start frame must be less than or equal to the end frame.")
                return
            bake_range = (bake_start, bake_end)

        selected_color_mode = color_combo.currentText()
        core_transform.convert_transforms_to_locators(
            translate_axes=tuple(control.isChecked() for control in translate_controls),
            rotate_axes=tuple(control.isChecked() for control in rotate_controls),
            scale_axes=tuple(control.isChecked() for control in scale_controls),
            bake_range=bake_range,
            constraint_transforms=selected_transform_mode == MODE_CONSTRAINT_TRANSFORMS,
            locator_scale=shape_scale.value(),
            auto_side_color=selected_color_mode == COLOR_AUTO_SIDE,
            locator_color=custom_color if selected_color_mode == COLOR_CUSTOM else None,
        )

    transform_mode_combo.currentTextChanged.connect(lambda _text: _update_enabled_controls())
    bake_range_combo.currentTextChanged.connect(lambda _text: _update_enabled_controls())
    color_combo.currentTextChanged.connect(lambda _text: _update_enabled_controls())
    color_button.clicked.connect(_choose_custom_color)
    _update_enabled_controls()

    window.add_separator()
    window.add_button(
        "Convert to Locators",
        command=_convert_to_locators,
        variant="primary",
        icon=ui_res_lib.Icon.util_convert_loc,
        tooltip="Create locators from the current selection using these options.",
    )
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_convert_to_locators_options()
