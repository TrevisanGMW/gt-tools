"""
Renamer Compatibility Layer
"""

from gt.tools.renamer import renamer_model
import copy


script_name = renamer_model.SCRIPT_NAME
script_version = "?.?.?"

_legacy_model = renamer_model.RenamerModel()
gt_renamer_settings = _legacy_model.settings
gt_renamer_settings["error_message"] = renamer_model.ERROR_MESSAGE
gt_renamer_settings["nodes_to_ignore"] = _legacy_model.nodes_to_ignore
gt_renamer_settings["node_types_to_ignore"] = _legacy_model.node_types_to_ignore
gt_renamer_settings_default_values = copy.deepcopy(gt_renamer_settings)


def get_persistent_settings_renamer():
    """Loads persistent Renamer settings into the compatibility settings dictionary."""
    _legacy_model.load_preferences()
    gt_renamer_settings.update(_legacy_model.settings)


def set_persistent_settings_renamer(option_var_name, option_var_string):
    """Stores one legacy Renamer optionVar.

    Args:
        option_var_name (str): OptionVar name.
        option_var_string (str): Value to store.
    """
    for setting_key, mapped_option_var in renamer_model.OPTION_VAR_MAP.items():
        if mapped_option_var == option_var_name:
            _legacy_model.save_setting(setting_key, option_var_string)
            gt_renamer_settings.update(_legacy_model.settings)
            return


def reset_persistent_settings_renamer():
    """Resets persistent Renamer settings."""
    _legacy_model.reset_preferences()
    gt_renamer_settings.update(_legacy_model.settings)


def build_gui_renamer():
    """Builds the Renamer user interface.

    Returns:
        RenamerController: Controller for the launched tool.
    """
    from gt.tools.renamer import renamer_controller
    from gt.tools.renamer import renamer_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = renamer_model.RenamerModel()
        view = renamer_view.RenamerView(parent=context.get_parent(), version=script_version)
        controller = renamer_controller.RenamerController(model=model, view=view)
        return controller


def build_gui_help_renamer():
    """Compatibility wrapper for the removed help window.

    Returns:
        RenamerController: Controller for the launched tool.
    """
    return build_gui_renamer()


def string_replace(string, search, replace):
    """Compatibility wrapper for string replacement.

    Args:
        string (str): String to process.
        search (str): Text to search for.
        replace (str): Replacement text.

    Returns:
        str: Processed string.
    """
    return renamer_model.string_replace(string, search, replace)


def get_short_name(obj):
    """Compatibility wrapper for short-name extraction.

    Args:
        obj (str): Object name.

    Returns:
        str: Short object name.
    """
    return renamer_model.get_short_name(obj)


def rename_uppercase(obj_list):
    """Renames objects to uppercase.

    Args:
        obj_list (list): Object names.
    """
    return _legacy_model.rename_case(obj_list, "upper")


def rename_lowercase(obj_list):
    """Renames objects to lowercase.

    Args:
        obj_list (list): Object names.
    """
    return _legacy_model.rename_case(obj_list, "lower")


def rename_capitalize(obj_list):
    """Capitalizes object names.

    Args:
        obj_list (list): Object names.
    """
    return _legacy_model.rename_case(obj_list, "capitalize")


def remove_first_letter(obj_list):
    """Removes the first letter from object names.

    Args:
        obj_list (list): Object names.
    """
    return _legacy_model.remove_first_letter(obj_list)


def remove_last_letter(obj_list):
    """Removes the last letter from object names.

    Args:
        obj_list (list): Object names.
    """
    return _legacy_model.remove_last_letter(obj_list)


def rename_search_replace(obj_list, search, replace):
    """Renames objects using search and replace.

    Args:
        obj_list (list): Object names.
        search (str): Search text.
        replace (str): Replacement text.
    """
    return _legacy_model.rename_search_replace(obj_list, search, replace)


def rename_and_number(obj_list, new_name, start_number, padding_number, keep_name=False):
    """Renames objects and adds a padded number.

    Args:
        obj_list (list): Object names.
        new_name (str): Base name.
        start_number (int): Starting number.
        padding_number (int): Padding width.
        keep_name (bool, optional): Whether to keep source names as the base.
    """
    return _legacy_model.rename_and_number(obj_list, new_name, start_number, padding_number, keep_name=keep_name)


def rename_add_prefix(obj_list, new_prefix_list):
    """Adds prefixes to objects.

    Args:
        obj_list (list): Object names.
        new_prefix_list (list): Prefix strings.
    """
    return _legacy_model.rename_add_prefix(obj_list, new_prefix_list)


def rename_add_suffix(obj_list, new_suffix_list):
    """Adds suffixes to objects.

    Args:
        obj_list (list): Object names.
        new_suffix_list (list): Suffix strings.
    """
    return _legacy_model.rename_add_suffix(obj_list, new_suffix_list)


def renaming_inview_feedback(number_of_renames):
    """Shows an in-view rename count message.

    Args:
        number_of_renames (int): Rename count.
    """
    return renamer_model.RenamerModel.renaming_inview_feedback(number_of_renames)


def rename_and_letter(obj_list, new_name, is_uppercase=True, keep_name=False):
    """Renames objects and adds an alphabetical suffix.

    Args:
        obj_list (list): Object names.
        new_name (str): Base name.
        is_uppercase (bool, optional): Whether the suffix is uppercase.
        keep_name (bool, optional): Whether to keep source names as the base.
    """
    return _legacy_model.rename_and_letter(obj_list, new_name, is_uppercase=is_uppercase, keep_name=keep_name)


if __name__ == "__main__":
    build_gui_renamer()
