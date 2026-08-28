"""
Material Utility Options

Option window for the Copy/Paste Material utility. It exposes both the copy and paste
actions in a single window and a mode dropdown that determines how the assignment is
transferred:

    Single Material : One material copied from the selection (objects or components) and
                      pasted onto the target selection. Uses Maya's polygon clipboard,
                      wired to "gt.core.misc".
    Matching IDs    : Per-component assignment matched by component id (same topology).
    By Position     : Per-component assignment matched by component position.

The component modes are wired to the material functions in "gt.core.material".
"""

import gt.ui.option_window as ui_option_window
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Combobox option labels
MODE_SINGLE_MATERIAL = "Single Material"
MODE_COMPONENT_INDEX = "Components - Matching IDs"
MODE_COMPONENT_POSITION = "Components - By Position"
SPACE_OBJECT = "Object (Local)"
SPACE_WORLD = "World"

# Status shown while using Maya's polygon clipboard (its content cannot be inspected)
SINGLE_MATERIAL_STATUS = (
    "Single Material mode uses Maya's polygon clipboard. Select objects or components."
)


def _get_space_map():
    """
    Builds the mapping between the space combobox labels and their ComponentSpace values.

    Returns:
        dict: Map of display label to ComponentSpace value.
    """
    from gt.core import material as core_mat

    return {
        SPACE_OBJECT: core_mat.ComponentSpace.object_space,
        SPACE_WORLD: core_mat.ComponentSpace.world,
    }


def _resolve_space(space_combo):
    """
    Resolves the matching space from the space combobox at click time.

    Args:
        space_combo (QComboBox): The space combobox.

    Returns:
        str: A ComponentSpace value (defaults to object/local space).
    """
    space_map = _get_space_map()
    return space_map.get(space_combo.currentText(), space_map[SPACE_OBJECT])


def _resolve_tolerance(tolerance_field):
    """
    Resolves the position tolerance from the tolerance field at click time.

    Args:
        tolerance_field (QLineEdit): The tolerance field.

    Returns:
        float: Parsed tolerance. Falls back to the core default when the text is invalid.
    """
    from gt.core import material as core_mat

    raw_value = tolerance_field.text().strip()
    try:
        tolerance = float(raw_value)
    except (TypeError, ValueError):
        logger.debug(f'Unable to parse the tolerance "{raw_value}". Using the default value.')
        tolerance = core_mat.DEFAULT_POSITION_TOLERANCE
    if tolerance <= 0:
        tolerance = core_mat.DEFAULT_POSITION_TOLERANCE
    tolerance_field.setText(str(tolerance))
    return tolerance


def open_copy_paste_material_options():
    """
    Opens the "Copy/Paste Material" option window.

    Returns:
        OptionWindow: The created option window.
    """
    from gt.core import material as core_mat
    from gt.core import misc as core_misc

    window = ui_option_window.OptionWindow(
        title="Copy/Paste Material",
        object_name="gtCopyPasteMaterialOptions",
        icon=ui_res_lib.Icon.util_mod_copy_material,
        description="Copy materials from the selection (objects or components), "
        "then paste them onto another selection.",
        workspace_restore_factory=(
            "gt.tools.utility_options.material_options.open_copy_paste_material_options"
        ),
    )
    mode_combo = window.add_combobox(
        "Mode",
        [MODE_SINGLE_MATERIAL, MODE_COMPONENT_INDEX, MODE_COMPONENT_POSITION],
        default=MODE_SINGLE_MATERIAL,
        tooltip="Single Material: copies one material from the selection (objects or components)\n"
        "and pastes it onto the target selection (objects or components).\n"
        "Components - Matching IDs: copies the material assignment of every face and pastes it\n"
        "onto targets that share the same topology (same component ids).\n"
        "Components - By Position: same as above, but faces are matched by position, so it also\n"
        "works when the component ids differ.",
    )
    space_combo = window.add_combobox(
        "Match Space",
        [SPACE_OBJECT, SPACE_WORLD],
        default=SPACE_OBJECT,
        tooltip="Space used when matching components by position.\n"
        "Object (Local): ignores the transform, so it also works for duplicates that were moved.\n"
        "World: matches components that overlap in the scene.",
    )
    tolerance_field = window.add_line_edit(
        "Tolerance",
        default=str(core_mat.DEFAULT_POSITION_TOLERANCE),
        placeholder="0.001",
        tooltip="Distance within which a component counts as an exact position match.\n"
        'Components outside it are still assigned while "Assign closest component" is on.',
    )
    fallback_checkbox = window.add_checkbox(
        "Assign closest component when outside tolerance",
        checked=True,
        tooltip="Keeps every target component assigned by using the material of the closest source\n"
        "component, even when it sits outside the tolerance. Turn it off to leave components\n"
        "without a match untouched.",
    )
    status_label = None

    def _update_position_controls():
        """Enables the position matching controls only while a position mode is active."""
        is_position_mode = mode_combo.currentText() == MODE_COMPONENT_POSITION
        window.set_row_enabled(space_combo, is_position_mode)
        window.set_row_enabled(tolerance_field, is_position_mode)
        fallback_checkbox.setEnabled(is_position_mode)

    def _update_status():
        """Refreshes the status label with the current clipboard content."""
        if status_label is None:
            return
        if mode_combo.currentText() == MODE_SINGLE_MATERIAL:
            status_label.setText(SINGLE_MATERIAL_STATUS)
            return
        status_label.setText(core_mat.get_component_material_clipboard_summary())

    def _on_mode_changed():
        """Updates the dependent controls and status whenever the mode changes."""
        _update_position_controls()
        _update_status()

    def _copy_material():
        """Copies the material assignment according to the selected mode."""
        if mode_combo.currentText() == MODE_SINGLE_MATERIAL:
            core_misc.material_copy()
        else:
            core_mat.copy_component_materials()
        _update_status()

    def _paste_material():
        """Pastes the material assignment according to the selected mode."""
        mode = mode_combo.currentText()
        if mode == MODE_SINGLE_MATERIAL:
            core_misc.material_paste()
        elif mode == MODE_COMPONENT_INDEX:
            core_mat.paste_component_materials(match_by=core_mat.MaterialTransferMode.component_index)
        else:
            core_mat.paste_component_materials(
                match_by=core_mat.MaterialTransferMode.component_position,
                space=_resolve_space(space_combo),
                tolerance=_resolve_tolerance(tolerance_field),
                fallback_closest=fallback_checkbox.isChecked(),
            )
        _update_status()

    mode_combo.currentTextChanged.connect(lambda _text: _on_mode_changed())
    _update_position_controls()

    window.add_button(
        "Copy Material",
        command=_copy_material,
        icon=ui_res_lib.Icon.util_mod_copy_material,
        tooltip="Copies material to clipboard.",
    )
    window.add_button(
        "Paste Material",
        command=_paste_material,
        icon=ui_res_lib.Icon.util_mod_paste_material,
        tooltip="Pastes material from clipboard.",
    )
    status_label = window.add_label(SINGLE_MATERIAL_STATUS)
    _update_status()
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_copy_paste_material_options()
