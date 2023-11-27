from copy import deepcopy
import logging
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_resource_path(resource_name, resource_folder, sub_folder=None):
    """
    Get the path to a resource file. This file should exist inside the resources' folder.
    Args:
        resource_name (str): Name of the file. It should contain its extension as it may vary. For example "icon.svg"
        resource_folder (str): Path to the resource folder. Also used to determine the resource type.
        sub_folder (optional, str): In case the icon exists inside a sub-folder, it can be provided as an argument.
                                    For example, if the icon is inside "../resource/icons/my_folder/icon.svg"
                                    One would call "get_icon_path("icon.svg", "my_folder")"
    Returns:
        str: Path to the resource.
    """
    if not sub_folder:
        resource_path = os.path.join(resource_folder, resource_name)
    else:
        resource_path = os.path.join(resource_folder, sub_folder, resource_name)
    return resource_path


def get_icon_path(icon_name, sub_folder=None):
    """
    Get the path to an icon file. This file should exist inside the resources/icons folder.
    Args:
        icon_name (str): Name of the file. It should contain its extension as it may vary. For example "icon.svg"
        sub_folder (optional, str): In case the icon exists inside a sub-folder, it can be provided as an argument.
                                    For example, if the icon is inside "../resource/icons/my_folder/icon.svg"
                                    One would call "get_icon_path("icon.svg", "my_folder")"
    Returns:
        str: Path to the icon.
    """
    icon_path = get_resource_path(icon_name, resource_folder=ResourceDirConstants.DIR_ICONS, sub_folder=sub_folder)
    if not os.path.exists(icon_path) or icon_name == '':
        logger.info(f'Could not find icon: "{icon_path}"')
    return icon_path


def get_font_path(font_name, sub_folder=None):
    """
    Get the path to a font file. This file should exist inside the resources/fonts folder.
    Args:
        font_name (str): Name of the file. It should contain its extension as it may vary. For example "font.ttf"
        sub_folder (optional, str): In case the font exists inside a sub-folder, it can be provided as an argument.
                                    For example, if the icon is inside "../resource/fonts/my_folder/font.ttf"
                                    One would call "get_icon_path("icon.svg", "my_folder")"
    Returns:
        str: QT Formatted Path to the font. @@@ (Double slashes "//" are replaced with single slashes "/")
    """
    font_path = get_resource_path(font_name, resource_folder=ResourceDirConstants.DIR_FONTS, sub_folder=sub_folder)
    if not os.path.exists(font_path) or font_name == '':
        logger.info(f'Could not find font: "{font_path}"')
    return font_path


def process_stylesheet_variables(stylesheet_content, stylesheet_variables=None):
    """
    Replaces any instances of the given stylesheet variables in the given stylesheet
    If not stylesheet is provided, this function acts as passthrough (no changes to the content)
    If stylesheet variables are of an incorrect type, the raw content will be returned.
    Adds a ";" at the end of the variable automatically
    Args:
        stylesheet_content (str): content found in a stylesheet
        stylesheet_variables (dict): A dictionary used to substitute stylesheet values/keys

    Returns:
        str: processed stylesheet content with the variables replaced with dict values
    """
    if stylesheet_variables is None:
        return stylesheet_content
    if not isinstance(stylesheet_variables, dict):
        logger.debug(f'Unable to process stylesheet. '
                     f'Must be a dictionary, but received a: "{str(type(stylesheet_variables))}".')
        return stylesheet_content
    for key, value in stylesheet_variables.items():
        stylesheet_content = stylesheet_content.replace(key, f'{value};')
    return stylesheet_content


def get_stylesheet_content(stylesheet_name, sub_folder=None, file_extension="qss", stylesheet_variables=None):
    """
   Get the path to a stylesheet (qss) file. This file should exist inside the resources/stylesheet folder.
   Args:
       stylesheet_name (str): Name of the file without its extension. Since all files share the same extension "qss"
                              you can provide just the name of the file. If an extension is provided, it is replaced.
       sub_folder (str, optional): In case the icon exists inside a sub-folder, it can be provided as an argument.
                                   For example, if the icon is inside "../resource/icons/my_folder/icon.svg"
                                   One would call "get_icon_path("icon.svg", "my_folder")"
       file_extension (str, optional): File extension used to find the file.
       stylesheet_variables (dict, optional): A dictionary of variables to replace when importing the stylesheet
   Returns:
       str: Stylesheet content
   """
    stylesheet_path = get_resource_path(f"{stylesheet_name}.{file_extension}",
                                        resource_folder=ResourceDirConstants.DIR_STYLESHEETS,
                                        sub_folder=sub_folder)
    if not os.path.exists(stylesheet_path) or stylesheet_name == '':
        logger.info(f'Could not find stylesheet: "{stylesheet_path}"')
        return ""
    else:
        with open(stylesheet_path, "r") as data_file:
            stylesheet_data = data_file.read()
            stylesheet_content = process_stylesheet_variables(stylesheet_content=stylesheet_data,
                                                              stylesheet_variables=stylesheet_variables)
        return stylesheet_content


def rgba_to_hex(r, g, b, a=255, include_alpha=False):
    """
    Convert RGBA (red, green, blue, alpha) values to a HEX color code.

    Args:
        r (int): Red component (0-255).
        g (int): Green component (0-255).
        b (int): Blue component (0-255).
        a (int): Alpha component (0-255).
        include_alpha (bool, optional): If active, it will include two suffix characters to act as alpha.

    Returns:
        str: The HEX color code in the format '#RRGGBBAA'.
    """
    if include_alpha:
        hex_code = "#{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)
    else:
        hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)
    return hex_code.upper()


def rgb_to_hex(r, g, b):
    """
    Convert RGBA (red, green, blue, alpha) values to a HEX color code.

    Args:
        r (int): Red component (0-255).
        g (int): Green component (0-255).
        b (int): Blue component (0-255).

    Returns:
        str: The HEX color code in the format '#RRGGBB'.
    """
    return rgba_to_hex(r, g, b)


def parse_rgb_numbers(rgb_string):
    """
    Extracts RGB+A numbers from an RGB+A string.
    All the ranges (RGB+A) are from 0-255.
    Alpha may be included, but it's not necessary.

    Args:
        rgb_string (str): A string containing the RGB color in the format "rgb(R, G, B)" or "rgba(R, G, B, A)"
                          The range goes from "0" to "255". Numbers above 255 are set back to 255.
                          e.g. "300" becomes "255"

    Returns:
        tuple or None: A tuple of three integers representing the RGB values (R, G, B) if the input string
                        matches the correct format. Returns None if no match is found.

    Example:
        rgb_string = "rgb(255, 255, 255)"
        result = extract_rgb_numbers(rgb_string)
        print(result)
        # Output: (255, 255, 255)
    """
    if rgb_string.startswith("rgba"):
        pattern = r'^rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$'
    elif rgb_string.startswith("rgb"):
        pattern = r"rgb\((\d+),\s*(\d+),\s*(\d+)\)"
    else:
        return None
    match = re.match(pattern, rgb_string)
    if match:
        numbers = list(map(int, match.groups()))
        result_tuple = tuple(n if n < 256 else 255 for n in numbers)
        return result_tuple
    else:
        return None


def rgba_string_to_hex(rgb_string):
    """
    Extracts RGB+A numbers from an RGB+A string.
    All the ranges (RGB+A) are from 0-255.
    Alpha may be included, but it's not necessary.

    Args:
        rgb_string (str): A string containing the RGB color in the format "rgb(R, G, B)" or "rgba(R, G, B, A)"
                          The range goes from "0" to "255". Numbers above 255 are set back to 255.
                          e.g. "300" becomes "255"

    Returns:
        str or None: A string with the color converted to Hex. e.g. "rgb(255, 0, 0)" becomes "#FF0000"
    """
    rgba_values = parse_rgb_numbers(rgb_string)
    if not rgba_values:
        return None
    elif len(rgba_values) == 3:
        return rgb_to_hex(rgba_values[0], rgba_values[1], rgba_values[2])
    elif len(rgba_values) == 4:
        return rgba_to_hex(rgba_values[0], rgba_values[1], rgba_values[2], rgba_values[3])
    else:
        return None


class ResourceDirConstants:
    def __init__(self):
        """
        Expected locations - Used to retrieve resources
        """
    DIR_CURRENT = os.path.dirname(__file__)
    DIR_RESOURCES = os.path.join(DIR_CURRENT, "resources")
    DIR_STYLESHEETS = os.path.join(DIR_RESOURCES, 'stylesheets')
    DIR_ICONS = os.path.join(DIR_RESOURCES, 'icons')
    DIR_FONTS = os.path.join(DIR_RESOURCES, 'fonts')


class Icon:
    def __init__(self):
        """
        A library of icons
        """
    # Root Menu
    root_general = get_icon_path(r"root_general.svg")
    root_curves = get_icon_path(r"root_curves.svg")
    root_modeling = get_icon_path(r"root_modeling.svg")
    root_rigging = get_icon_path(r"root_rigging.svg")
    root_utilities = get_icon_path(r"root_utilities.svg")
    root_miscellaneous = get_icon_path(r"root_miscellaneous.svg")
    root_help = get_icon_path(r"root_help.svg")
    root_dev = get_icon_path(r"root_dev.svg")
    # General
    tool_renamer = get_icon_path(r"tool_renamer.svg")
    tool_outliner_sorter = get_icon_path(r"tool_outliner_sorter.svg")
    tool_selection_manager = get_icon_path(r"tool_selection_manager.svg")
    tool_path_manager = get_icon_path(r"tool_path_manager.svg")
    tool_color_manager = get_icon_path(r"tool_color_manager.svg")
    tool_color_manager_roller = get_icon_path(r"tool_color_manager_roller.svg")
    tool_transfer_transforms = get_icon_path(r"tool_transfer_transforms.svg")
    tool_world_space_baker = get_icon_path(r"tool_world_space_baker.svg")
    tool_attributes_to_python = get_icon_path(r"tool_attributes_to_python.svg")
    tool_render_checklist = get_icon_path(r"tool_render_checklist.svg")
    # Curves
    tool_crv_library = get_icon_path(r"tool_crv_library.svg")
    tool_crv_python = get_icon_path(r"tool_crv_python.svg")
    tool_crv_text = get_icon_path(r"tool_crv_text.svg")
    tool_crv_extract_state = get_icon_path(r"tool_crv_extract_state.svg")
    util_crv_combine = get_icon_path(r"util_crv_combine.svg")
    util_crv_separate = get_icon_path(r"util_crv_separate.svg")
    # Modeling
    tool_transfer_uvs = get_icon_path(r"tool_transfer_uvs.svg")
    tool_mesh_library = get_icon_path(r"tool_sphere_types.svg")
    util_mod_load_udims = get_icon_path(r"util_mod_load_udims.svg")
    util_mod_bif_to_mesh = get_icon_path(r"util_mod_bif_to_mesh.svg")
    util_mod_copy_material = get_icon_path(r"util_mod_copy_material.svg")
    util_mod_paste_material = get_icon_path(r"util_mod_paste_material.svg")
    # Rigging
    tool_auto_rigger_legacy = get_icon_path(r"tool_auto_rigger_legacy.svg")
    tool_auto_rigger = get_icon_path(r"tool_auto_rigger.svg")
    tool_rig_interface = get_icon_path(r"tool_rig_interface.svg")
    tool_retarget_assistant = get_icon_path(r"tool_retarget_assistant.svg")
    tool_game_fbx_exporter = get_icon_path(r"tool_game_fbx_exporter.svg")
    tool_influence_joints = get_icon_path(r"tool_influence_joints.svg")
    tool_add_inbetween = get_icon_path(r"tool_add_inbetween.svg")
    tool_sine_attributes = get_icon_path(r"tool_sine_attributes.svg")
    tool_connect_attributes = get_icon_path(r"tool_connect_attributes.svg")
    tool_create_fk = get_icon_path(r"tool_create_fk.svg")
    tool_testing_keys = get_icon_path(r"tool_testing_keys.svg")
    tool_make_ik_stretchy = get_icon_path(r"tool_make_ik_stretchy.svg")
    tool_mirror_cluster = get_icon_path(r"tool_mirror_cluster.svg")
    tool_morphing_attributes = get_icon_path(r"tool_morphing_attributes.svg")
    tool_morphing_utils = get_icon_path(r"tool_morphing_utils.svg")
    tool_orient_joints = get_icon_path(r"tool_orient_joints.svg")
    # Utils
    util_reload_file = get_icon_path(r"util_reload_file.svg")
    util_open_dir = get_icon_path(r"util_open_dir.svg")
    util_hud_toggle = get_icon_path(r"util_hud_toggle.svg")
    util_sel_non_unique = get_icon_path(r"util_sel_non_unique.svg")
    util_joint_to_label = get_icon_path(r"util_joint_to_label.svg")
    util_lra_toggle = get_icon_path(r"util_lra_toggle.svg")
    util_joint_label_toggle = get_icon_path(r"util_joint_label_toggle.svg")
    util_unhide_trs = get_icon_path(r"util_unhide_trs.svg")
    util_unlock_trs = get_icon_path(r"util_unlock_trs.svg")
    util_convert_joint_mesh = get_icon_path(r"util_convert_joint_mesh.svg")
    util_convert_loc = get_icon_path(r"util_convert_loc.svg")
    util_ref_import = get_icon_path(r"util_ref_import.svg")
    util_ref_remove = get_icon_path(r"util_ref_remove.svg")
    util_pivot_top = get_icon_path(r"util_pivot_top.svg")
    util_pivot_bottom = get_icon_path(r"util_pivot_bottom.svg")
    util_move_origin = get_icon_path(r"util_move_origin.svg")
    util_reset_transforms = get_icon_path(r"util_reset_transforms.svg")
    util_reset_jnt_display = get_icon_path(r"util_reset_jnt_display.svg")
    util_reset_persp = get_icon_path(r"util_reset_persp.svg")
    util_delete_custom_attr = get_icon_path(r"util_delete_custom_attr.svg")
    util_delete_ns = get_icon_path(r"util_delete_ns.svg")
    util_delete_display_layers = get_icon_path(r"util_delete_display_layers.svg")
    util_delete_unused_nodes = get_icon_path(r"util_delete_unused_nodes.svg")
    util_delete_nucleus_nodes = get_icon_path(r"util_delete_nucleus_nodes.svg")
    util_delete_keyframes = get_icon_path(r"util_delete_keyframes.svg")
    util_rivet = get_icon_path(r"util_rivet.svg")
    # Misc
    tool_maya_to_discord = get_icon_path(r"tool_maya_to_discord.svg")
    tool_fspy_importer = get_icon_path(r"tool_fspy_importer.svg")
    tool_render_calculator = get_icon_path(r"tool_render_calculator.svg")
    tool_startup_booster = get_icon_path(r"tool_startup_booster.svg")
    # Help
    tool_package_updater = get_icon_path(r"tool_check_for_updates.svg")
    misc_rebuild_menu = get_icon_path(r"misc_rebuild_menu.svg")
    misc_about = get_icon_path(r"misc_about.svg")
    misc_current_version = get_icon_path(r"misc_current_version.svg")
    # Dev
    tool_resource_library = get_icon_path(r"tool_resource_library.svg")
    dev_brain = get_icon_path(r"dev_brain.svg")
    dev_parameters = get_icon_path(r"dev_parameters.svg")
    dev_git_fork = get_icon_path(r"dev_git_fork.svg")
    dev_git_pull_request = get_icon_path(r"dev_git_pull_request.svg")
    dev_binary = get_icon_path(r"dev_binary.svg")
    dev_scalpel = get_icon_path(r"dev_scalpel.svg")
    dev_wash_bottle = get_icon_path(r"dev_wash_bottle.svg")
    dev_trash = get_icon_path(r"dev_trash.svg")
    dev_tongs = get_icon_path(r"dev_tongs.svg")
    dev_tweezer = get_icon_path(r"dev_tweezer.svg")
    dev_spray = get_icon_path(r"dev_spray.svg")
    dev_filter = get_icon_path(r"dev_filter.svg")
    dev_chainsaw = get_icon_path(r"dev_chainsaw.svg")
    dev_trowel = get_icon_path(r"dev_trowel.svg")
    dev_ruler = get_icon_path(r"dev_ruler.svg")
    dev_pliers = get_icon_path(r"dev_pliers.svg")
    dev_picker = get_icon_path(r"dev_picker.svg")
    dev_lab_flask = get_icon_path(r"dev_lab_flask.svg")
    dev_hammer = get_icon_path(r"dev_hammer.svg")
    dev_screwdriver = get_icon_path(r"dev_screwdriver.svg")
    dev_code = get_icon_path(r"dev_code.svg")
    # Other
    package_logo = get_icon_path(r"package_logo.svg")
    package_icon = get_icon_path(r"package_icon.svg")
    abr_create_proxy = get_icon_path(r"abr_create_proxy.svg")
    abr_create_rig = get_icon_path(r"abr_create_rig.svg")
    misc_cog = get_icon_path(r"misc_cog.svg")
    setup_install = get_icon_path(r"setup_install.svg")
    setup_uninstall = get_icon_path(r"setup_uninstall.svg")
    setup_run_only = get_icon_path(r"setup_run_only.svg")
    setup_close = get_icon_path(r"setup_close.svg")
    curve_library_base_curve = get_icon_path(r"curve_library_base_curve.svg")
    curve_library_user_curve = get_icon_path(r"curve_library_user_curve.svg")
    curve_library_control = get_icon_path(r"curve_library_control.svg")
    mesh_library_base = get_icon_path(r"mesh_library_base.svg")
    mesh_library_user = get_icon_path(r"mesh_library_user.svg")
    mesh_library_param = get_icon_path(r"mesh_library_param.svg")
    library_missing_file = get_icon_path(r"library_missing_file.svg")
    library_parameters = get_icon_path(r"library_parameters.svg")
    library_build = get_icon_path(r"library_build.svg")
    library_edit = get_icon_path(r"library_edit.svg")
    library_snapshot = get_icon_path(r"library_snapshot.svg")
    library_remove = get_icon_path(r"library_remove.svg")
    library_add = get_icon_path(r"library_add.svg")
    library_shelf = get_icon_path(r"library_shelf.svg")
    rigger_proxy = get_icon_path(r"rigger_proxy.svg")
    rigger_project = get_icon_path(r"rigger_project.svg")
    rigger_module_generic = get_icon_path(r"rigger_module_generic.svg")
    rigger_dict = get_icon_path(r"rigger_dict.svg")
    rigger_module_biped_arm = get_icon_path(r"rigger_module_biped_arm.svg")
    rigger_module_biped_fingers = get_icon_path(r"rigger_module_biped_fingers.svg")
    rigger_module_biped_leg = get_icon_path(r"rigger_module_biped_leg.svg")
    rigger_module_root = get_icon_path(r"rigger_module_root.svg")
    rigger_module_spine = get_icon_path(r"rigger_module_spine.svg")
    # User Interface
    ui_add = get_icon_path(r"ui_add.svg")
    ui_arrow_up = get_icon_path(r"ui_arrow_up.svg")
    ui_arrow_down = get_icon_path(r"ui_arrow_down.svg")
    ui_arrow_left = get_icon_path(r"ui_arrow_left.svg")
    ui_arrow_right = get_icon_path(r"ui_arrow_right.svg")
    ui_exclamation = get_icon_path(r"ui_exclamation.svg")
    ui_checkbox_enabled = get_icon_path(r"ui_checkbox_enabled.svg")
    ui_checkbox_disabled = get_icon_path(r"ui_checkbox_disabled.svg")
    ui_toggle_enabled = get_icon_path(r"ui_toggle_enabled.svg")
    ui_toggle_disabled = get_icon_path(r"ui_toggle_disabled.svg")
    ui_edit = get_icon_path(r"ui_edit.svg")
    ui_delete = get_icon_path(r"ui_delete.svg")
    ui_trash = get_icon_path(r"ui_trash.svg")
    # Branch/Hierarchy Lines
    ui_branch_closed = get_icon_path(r"ui_branch_closed.svg")
    ui_branch_end = get_icon_path(r"ui_branch_end.svg")
    ui_branch_line = get_icon_path(r"ui_branch_line.svg")
    ui_branch_more = get_icon_path(r"ui_branch_more.svg")
    ui_branch_open = get_icon_path(r"ui_branch_open.svg")
    ui_branch_root_closed = get_icon_path(r"ui_branch_root_closed.svg")
    ui_branch_root_open = get_icon_path(r"ui_branch_root_open.svg")
    ui_branch_single = get_icon_path(r"ui_branch_single.svg")


class Color:
    def __init__(self):
        """
        A library of colors
        """
    class RGB:
        def __init__(self):
            """
            A library of colors RGB+A colors.
            Format:
            rgba(Red, Green, Blue, Alpha)
            e.g. "rgba(255, 0, 0, 255)" = Red, full opacity
            Value range 0-255
            """
        # Red -------------------------------------------
        red_maroon = "rgb(128, 0, 0)"
        red_metallic_dark = "rgb(139, 0, 0)"
        red_metallic = 'rgb(175, 45, 45)'
        red_brown = "rgb(165, 42, 42)"
        red_firebrick = "rgb(178, 34, 34)"
        red_crimson = "rgb(220, 20, 60)"
        red = "rgb(255, 0, 0)"
        red_tomato = "rgb(255, 99, 71)"
        red_coral = "rgb(255, 127, 80)"
        red_indian = "rgb(205, 92, 92)"
        red_melon = "rgb(255, 170, 170)"

        # Salmon -----------------------------------------
        salmon_light_coral = "rgb(240, 128, 128)"
        salmon_dark = "rgb(233, 150, 122)"
        salmon = "rgb(250, 128, 114)"
        salmon_light = "rgb(255, 160, 122)"

        # Orange -----------------------------------------
        orange_red = "rgb(255, 69, 0)"
        orange_dark = "rgb(255, 140, 0)"
        orange = "rgb(255, 165, 0)"

        # Yellow -----------------------------------------
        yellow_gold = "rgb(255, 215, 0)"
        yellow_dark_golden_rod = "rgb(184, 134, 11)"
        yellow_golden_rod = "rgb(218, 165, 32)"
        yellow_pale_golden_rod = "rgb(238, 232, 170)"
        yellow_dark_khaki = "rgb(189, 183, 107)"
        yellow_khaki = "rgb(240, 230, 140)"
        yellow_olive = "rgb(128, 128, 0)"
        yellow = "rgb(255, 255, 0)"
        yellow_green = "rgb(154, 205, 50)"

        # Green ------------------------------------------
        green_dark_olive = "rgb(85, 107, 47)"
        green_olive_drab = "rgb(107, 142, 35)"
        green_lawn_green = "rgb(124, 252, 0)"
        green_chartreuse = "rgb(127, 255, 0)"
        green_yellow = "rgb(173, 255, 47)"
        green_dark = "rgb(0, 100, 0)"
        green = "rgb(0, 128, 0)"
        green_forest = "rgb(34, 139, 34)"
        green_lime_pure = "rgb(0, 255, 0)"
        green_lime = "rgb(50, 205, 50)"
        green_light = "rgb(144, 238, 144)"
        green_pale = "rgb(152, 251, 152)"
        green_dark_sea = "rgb(143, 188, 143)"
        green_oxley = 'rgba(96, 152, 129, 255)'
        green_medium_spring = "rgb(0, 250, 154)"
        green_spring = "rgb(0, 255, 127)"
        green_sea = "rgb(46, 139, 87)"
        green_medium_aqua_marine = "rgb(102, 205, 170)"
        green_medium_sea = "rgb(60, 179, 113)"
        green_light_sea = "rgb(32, 178, 170)"
        green_teal = "rgb(0, 128, 128)"
        green_honeydew = "rgb(240, 255, 240)"
        green_pearl_aqua = 'rgb(144,  228,  193)'
        green_wintergreen_dream = 'rgba(88, 140, 119, 255)'

        # Cyan -------------------------------------------
        cyan_dark = "rgb(0, 139, 139)"
        cyan_aqua = "rgb(0, 255, 255)"
        cyan = "rgb(0, 255, 255)"
        cyan_light = "rgb(224, 255, 255)"

        # Turquoise ---------------------------------------
        turquoise_dark = "rgb(0, 206, 209)"
        turquoise = "rgb(64, 224, 208)"
        turquoise_medium = "rgb(72, 209, 204)"
        turquoise_pale = "rgb(175, 238, 238)"

        # Blue --------------------------------------------
        blue_aqua_marine = "rgb(127, 255, 212)"
        blue_powder = "rgb(176, 224, 230)"
        blue_cadet = "rgb(95, 158, 160)"
        blue_steel = "rgb(70, 130, 180)"
        blue_corn_flower = "rgb(100, 149, 237)"
        blue_deep_sky = "rgb(0, 191, 255)"
        blue_dodger = "rgb(30, 144, 255)"
        blue_light = "rgb(173, 216, 230)"
        blue_sky = "rgb(135, 206, 235)"
        blue_light_sky = "rgb(135, 206, 250)"
        blue_midnight = "rgb(25, 25, 112)"
        blue_navy = "rgb(0, 0, 128)"
        blue_dark = "rgb(0, 0, 139)"
        blue_medium = "rgb(0, 0, 205)"
        blue = "rgb(0, 0, 255)"
        blue_royal = "rgb(65, 105, 225)"
        blue_violet = "rgb(138, 43, 226)"
        blue_alice = "rgb(240, 248, 255)"
        blue_azure = "rgb(240, 255, 255)"
        blue_ghosted = 'rgba(0, 0, 255, 75)'
        blue_lavender = 'rgba(189,  217,  255, 255)'
        blue_pastel = 'rgba(82, 133, 166, 255)'
        blue_vivid_cerulean = 'rgba(0, 160, 232, 255)'
        blue_medium_persian = 'rgba(0, 110, 160, 255)'

        # Purple -------------------------------------------
        purple_indigo = "rgb(75, 0, 130)"
        purple_dark_slate_blue = "rgb(72, 61, 139)"
        purple_slate_blue = "rgb(106, 90, 205)"
        purple_medium_slate_blue = "rgb(123, 104, 238)"
        purple_medium = "rgb(147, 112, 219)"
        purple_dark_magenta = "rgb(139, 0, 139)"
        purple_dark_violet = "rgb(148, 0, 211)"
        purple_dark_orchid = "rgb(153, 50, 204)"
        purple_medium_orchid = "rgb(186, 85, 211)"
        purple = "rgb(128, 0, 128)"

        # Magenta -------------------------------------------
        magenta_thistle = "rgb(216, 191, 216)"
        magenta_plum = "rgb(221, 160, 221)"
        magenta_violet = "rgb(238, 130, 238)"
        magenta_fuchsia = "rgb(255, 0, 255)"
        magenta_orchid = "rgb(218, 112, 214)"
        magenta_medium_violet_red = "rgb(199, 21, 133)"
        magenta_pale_violet_red = "rgb(219, 112, 147)"

        # Pink ---------------------------------------------
        pink_deep = "rgb(255, 20, 147)"
        pink_hot = "rgb(255, 105, 180)"
        pink_light = "rgb(255, 182, 193)"
        pink = "rgb(255, 192, 203)"

        # Brown --------------------------------------------
        brown_saddle = "rgb(139, 69, 19)"
        brown_sienna = "rgb(160, 82, 45)"
        brown_chocolate = "rgb(210, 105, 30)"
        brown_peru = "rgb(205, 133, 63)"
        brown_sandy = "rgb(244, 164, 96)"
        brown_burly_wood = "rgb(222, 184, 135)"
        brown_tan = "rgb(210, 180, 140)"

        # White -----------------------------------------
        white = "rgb(255, 255, 255)"
        white_floral = "rgb(255, 250, 240)"
        white_ghost = "rgb(248, 248, 255)"
        white_ivory = "rgb(255, 255, 240)"
        white_snow = "rgb(255, 250, 250)"
        white_smoke = "rgb(245, 245, 245)"
        white_smoke_darker = 'rgba(238,238,238,255)'
        white_smoke_darker_ghosted = 'rgba(238,238,238,75)'
        white_antique = "rgb(250, 235, 215)"
        white_beige = "rgb(245, 245, 220)"
        white_bisque = "rgb(255, 228, 196)"
        white_blanched_almond = "rgb(255, 235, 205)"
        white_wheat = "rgb(245, 222, 179)"
        white_corn_silk = "rgb(255, 248, 220)"
        white_lemon_chiffon = "rgb(255, 250, 205)"
        white_light_golden_rod_yellow = "rgb(250, 250, 210)"
        white_light_yellow = "rgb(255, 255, 224)"
        white_brown_rosy = "rgb(188, 143, 143)"
        white_brown_moccasin = "rgb(255, 228, 181)"
        white_brown_navajo = "rgb(255, 222, 173)"
        white_peach_puff = "rgb(255, 218, 185)"
        white_misty_rose = "rgb(255, 228, 225)"
        white_lavender_blush = "rgb(255, 240, 245)"
        white_lavender = "rgb(230, 230, 250)"
        white_linen = "rgb(250, 240, 230)"
        white_old_lace = "rgb(253, 245, 230)"
        white_papaya_whip = "rgb(255, 239, 213)"
        white_sea_shell = "rgb(255, 245, 238)"
        white_mint_cream = "rgb(245, 255, 250)"

        # Gray -------------------------------------------
        gray_dim = "rgb(105, 105, 105)"
        gray = "rgb(128, 128, 128)"
        gray_dark = "rgb(169, 169, 169)"
        gray_silver = "rgb(192, 192, 192)"
        gray_light = "rgb(211, 211, 211)"
        gray_dark_slate_gray = "rgb(47, 79, 79)"
        gray_nero = 'rgba(20, 20, 20,255)'
        gray_much_darker = 'rgba(29, 29, 29,255)'
        gray_darker_mid = 'rgba(35, 35, 35, 255)'
        gray_darker = 'rgba(43, 43, 43, 255)'
        gray_darker_ghosted = 'rgba(43, 43, 43, 75)'
        gray_mid_dark = 'rgba(68, 68, 68, 255)'
        gray_mid_dark_ghosted = 'rgba(68, 68, 68, 75)'
        gray_mid = 'rgba(73, 73, 73, 255)'
        gray_mid_light = 'rgba(82, 82, 82, 255)'
        gray_mid_lighter = 'rgba(93, 93, 93, 255)'
        gray_mid_much_lighter = 'rgba(112, 112, 112, 255)'
        grey_light = 'rgba(145, 145, 145, 255)'
        gray_lighter = 'rgba(160, 160, 160, 255)'
        gray_dark_silver = 'rgba(180, 180, 180, 255)'
        gray_gainsboro = "rgb(220, 220, 220)"
        gray_slate = "rgb(112, 128, 144)"
        gray_light_slate = "rgb(119, 136, 153)"
        gray_light_steel_blue = "rgb(176, 196, 222)"

        # Misc -----------------------------------------
        black = "rgb(0, 0, 0)"
        transparent = 'rgba(0, 0, 0, 0)'

    class Hex:
        def __init__(self):
            """
            A library of Hex colors
            """
        black = "#000000"
        blue = "#0000FF"
        blue_alice = "#F0F8FF"
        blue_aqua_marine = "#7FFFD4"
        blue_azure = "#F0FFFF"
        blue_cadet = "#5F9EA0"
        blue_corn_flower = "#6495ED"
        blue_dark = "#00008B"
        blue_deep_sky = "#00BFFF"
        blue_dodger = "#1E90FF"
        blue_lavender = "#BDD9FF"
        blue_light = "#ADD8E6"
        blue_light_sky = "#87CEFA"
        blue_medium = "#0000CD"
        blue_medium_persian = "#006EA0"
        blue_midnight = "#191970"
        blue_navy = "#000080"
        blue_pastel = "#5285A6"
        blue_powder = "#B0E0E6"
        blue_royal = "#4169E1"
        blue_sky = "#87CEEB"
        blue_steel = "#4682B4"
        blue_violet = "#8A2BE2"
        blue_vivid_cerulean = "#00A0E8"
        brown_burly_wood = "#DEB887"
        brown_chocolate = "#D2691E"
        brown_peru = "#CD853F"
        brown_saddle = "#8B4513"
        brown_sandy = "#F4A460"
        brown_sienna = "#A0522D"
        brown_tan = "#D2B48C"
        cyan = "#00FFFF"
        cyan_aqua = "#00FFFF"
        cyan_dark = "#008B8B"
        cyan_light = "#E0FFFF"
        gray = "#808080"
        gray_dark = "#A9A9A9"
        gray_dark_silver = "#B4B4B4"
        gray_dark_slate_gray = "#2F4F4F"
        gray_darker = "#2B2B2B"
        gray_darker_mid = "#232323"
        gray_dim = "#696969"
        gray_gainsboro = "#DCDCDC"
        gray_light = "#D3D3D3"
        gray_light_slate = "#778899"
        gray_light_steel_blue = "#B0C4DE"
        gray_lighter = "#A0A0A0"
        gray_mid = "#494949"
        gray_mid_dark = "#444444"
        gray_mid_light = "#525252"
        gray_mid_lighter = "#5D5D5D"
        gray_mid_much_lighter = "#707070"
        gray_much_darker = "#1D1D1D"
        gray_nero = "#141414"
        gray_silver = "#C0C0C0"
        gray_slate = "#708090"
        green = "#008000"
        green_chartreuse = "#7FFF00"
        green_dark = "#006400"
        green_dark_olive = "#556B2F"
        green_dark_sea = "#8FBC8F"
        green_forest = "#228B22"
        green_honeydew = "#F0FFF0"
        green_lawn_green = "#7CFC00"
        green_light = "#90EE90"
        green_light_sea = "#20B2AA"
        green_lime = "#32CD32"
        green_lime_pure = "#00FF00"
        green_medium_aqua_marine = "#66CDAA"
        green_medium_sea = "#3CB371"
        green_medium_spring = "#00FA9A"
        green_olive_drab = "#6B8E23"
        green_oxley = "#609881"
        green_pale = "#98FB98"
        green_pearl_aqua = "#90E4C1"
        green_sea = "#2E8B57"
        green_spring = "#00FF7F"
        green_teal = "#008080"
        green_wintergreen_dream = "#588C77"
        green_yellow = "#ADFF2F"
        grey_light = "#919191"
        magenta_fuchsia = "#FF00FF"
        magenta_medium_violet_red = "#C71585"
        magenta_orchid = "#DA70D6"
        magenta_pale_violet_red = "#DB7093"
        magenta_plum = "#DDA0DD"
        magenta_thistle = "#D8BFD8"
        magenta_violet = "#EE82EE"
        orange = "#FFA500"
        orange_dark = "#FF8C00"
        orange_red = "#FF4500"
        pink = "#FFC0CB"
        pink_deep = "#FF1493"
        pink_hot = "#FF69B4"
        pink_light = "#FFB6C1"
        purple = "#800080"
        purple_dark_magenta = "#8B008B"
        purple_dark_orchid = "#9932CC"
        purple_dark_slate_blue = "#483D8B"
        purple_dark_violet = "#9400D3"
        purple_indigo = "#4B0082"
        purple_medium = "#9370DB"
        purple_medium_orchid = "#BA55D3"
        purple_medium_slate_blue = "#7B68EE"
        purple_slate_blue = "#6A5ACD"
        red = "#FF0000"
        red_brown = "#A52A2A"
        red_coral = "#FF7F50"
        red_crimson = "#DC143C"
        red_firebrick = "#B22222"
        red_indian = "#CD5C5C"
        red_maroon = "#800000"
        red_melon = "#FFAAAA"
        red_metallic = "#AF2D2D"
        red_metallic_dark = "#8B0000"
        red_tomato = "#FF6347"
        salmon = "#FA8072"
        salmon_dark = "#E9967A"
        salmon_light = "#FFA07A"
        salmon_light_coral = "#F08080"
        transparent = "#000000"
        turquoise = "#40E0D0"
        turquoise_dark = "#00CED1"
        turquoise_medium = "#48D1CC"
        turquoise_pale = "#AFEEEE"
        white = "#FFFFFF"
        white_antique = "#FAEBD7"
        white_beige = "#F5F5DC"
        white_bisque = "#FFE4C4"
        white_blanched_almond = "#FFEBCD"
        white_brown_moccasin = "#FFE4B5"
        white_brown_navajo = "#FFDEAD"
        white_brown_rosy = "#BC8F8F"
        white_corn_silk = "#FFF8DC"
        white_floral = "#FFFAF0"
        white_ghost = "#F8F8FF"
        white_ivory = "#FFFFF0"
        white_lavender = "#E6E6FA"
        white_lavender_blush = "#FFF0F5"
        white_lemon_chiffon = "#FFFACD"
        white_light_golden_rod_yellow = "#FAFAD2"
        white_light_yellow = "#FFFFE0"
        white_linen = "#FAF0E6"
        white_mint_cream = "#F5FFFA"
        white_misty_rose = "#FFE4E1"
        white_old_lace = "#FDF5E6"
        white_papaya_whip = "#FFEFD5"
        white_peach_puff = "#FFDAB9"
        white_sea_shell = "#FFF5EE"
        white_smoke = "#F5F5F5"
        white_smoke_darker = "#EEEEEE"
        white_snow = "#FFFAFA"
        white_wheat = "#F5DEB3"
        yellow = "#FFFF00"
        yellow_dark_golden_rod = "#B8860B"
        yellow_dark_khaki = "#BDB76B"
        yellow_gold = "#FFD700"
        yellow_golden_rod = "#DAA520"
        yellow_green = "#9ACD32"
        yellow_khaki = "#F0E68C"
        yellow_olive = "#808000"
        yellow_pale_golden_rod = "#EEE8AA"

    class Gradient:
        def __init__(self):
            """
            A library of colors Gradient colors.
            """
        conical_rainbow = 'qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:0.0 rgba(255, 0, 0, 255), ' \
                          'stop:0.15 rgba(255, 127, 0, 255), stop:0.3 rgba(255, 255, 0, 255), ' \
                          'stop:0.45 rgba(0, 255, 0, 255), stop:0.6 rgba(0, 0, 255, 255), ' \
                          'stop:0.75 rgba(139, 0, 255, 255), stop:1.0 rgba(255, 0, 255, 255));'
        linear_rainbow = 'qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #FF0000, stop: 0.15 #FF7F00, ' \
                         'stop: 0.3 #FFFF00, stop: 0.45 #00FF00, stop: 0.6 #0000FF, stop: 0.75 #8B00FF, ' \
                         'stop: 1 #FF00FF);'


class StylesheetVariables:
    def __init__(self):
        """
        A library of stylesheet variables
        """
    maya_basic = {
        # Colors
        "@maya_background_grey;": Color.RGB.gray_mid_dark,
        "@maya_background_dark;": Color.RGB.gray_darker,
        "@maya_background_darker;": Color.RGB.gray_much_darker,
        "@maya_background_grey_dark;": Color.RGB.gray_darker,
        "@maya_button;": Color.RGB.gray_mid_lighter,
        "@maya_button_hover;": Color.RGB.gray_mid_much_lighter,
        "@maya_button_clicked;": Color.RGB.gray_much_darker,
        "@maya_selection;": Color.RGB.blue_pastel,
        "@maya_text;": Color.RGB.white_smoke_darker,
        "@background_disabled_color;": Color.RGB.gray_mid_light,
        "@disabled_text_color;": Color.RGB.gray_mid_much_lighter,
        "@text_edit_border;": Color.RGB.gray_mid_dark,
        # Formatting
        "@maya_small_button_padding;": "5",
    }
    scroll_bar_base = {
        "@background_mid;": Color.RGB.gray_mid_dark,
        "@background_dark;": Color.RGB.gray_darker,
        "@scroll_area_border;": Color.RGB.gray_mid_much_lighter,
        "@scrollbar_line_background;": Color.RGB.gray_much_darker,
        "@scrollbar_sub_line;": Color.RGB.gray_mid_dark,
        "@scrollbar_handle;": Color.RGB.gray_mid_much_lighter,
        "@scrollbar_handle_pressed;": Color.RGB.gray_dark_silver,
        "@scrollbar_background;": Color.RGB.gray_darker,
        # Sizes
        "@scrollbar_size;": 15,
        "@sub_control_size;": 15,
        # Icons
        "@image_scrollbar_up;": f"url({Icon.ui_arrow_up})".replace("\\", "/"),
        "@image_scrollbar_down;": f"url({Icon.ui_arrow_down})".replace("\\", "/"),
        "@image_scrollbar_left;": f"url({Icon.ui_arrow_left})".replace("\\", "/"),
        "@image_scrollbar_right;": f"url({Icon.ui_arrow_right})".replace("\\", "/"),
    }
    text_edit_base = {
        "@background_mid;": Color.RGB.gray_mid_dark,
        "@border_color;": Color.RGB.gray_mid_much_lighter,
    }
    progress_bar_base = {
        # Colors
        "@progress_bar_background;": Color.RGB.gray_mid_much_lighter,
        "@progress_bar_chunk;": Color.RGB.blue_lavender,
    }
    list_widget_base = {
        # Colors
        "@list_background_color;": Color.RGB.gray_much_darker,
        "@list_text_color;": Color.RGB.gray_dark_silver,
        "@list_selection_bg_color;": Color.RGB.blue_pastel,
        "@list_selection_text_color;": Color.RGB.white,
        "@list_hover_bg_color;": Color.RGB.gray_mid_dark,
        "@list_hover_text_color;": Color.RGB.white,
    }
    btn_push_base = {
        # Colors
        "@background_color;": Color.RGB.gray_mid_lighter,
        "@background_hover_color;": Color.RGB.gray_mid_much_lighter,
        "@background_pressed_color;": Color.RGB.gray_darker_mid,
        "@background_disabled_color;": Color.RGB.gray_mid_light,
        "@text_color;": Color.RGB.white,
        "@disabled_text_color;": Color.RGB.gray_mid_much_lighter,

        # Formatting
        "@button_padding;": "15",
    }
    btn_push_bright = {
        # Colors
        "@background_color;": Color.RGB.grey_light,
        "@background_hover_color;": Color.RGB.gray_lighter,
        "@background_pressed_color;": Color.RGB.gray_mid_lighter,
        "@background_disabled_color;": Color.RGB.gray_mid_light,
        "@text_color;": Color.RGB.black,
        "@disabled_text_color;": Color.RGB.gray_mid_much_lighter,

        # Formatting
        "@button_padding;": "15",
    }
    btn_radio_base = {
        # Colors
        "@text_color;": Color.RGB.white,
        "@indicator_border_color;": Color.RGB.gray_mid_much_lighter,
        "@indicator_hover_color;": Color.RGB.gray_lighter,
        "@indicator_checked_color;": Color.RGB.white,
        "@indicator_checked_border_color;": Color.RGB.gray_gainsboro,

        # Formatting
        "@button_padding;": "5",
    }
    combobox_base = {
        # Colors
        "@text_color;": Color.RGB.gray_dark_silver,
        "@background_color;": Color.RGB.gray_darker,
        "@border_color;": Color.RGB.gray_much_darker,
        "@selection_background;": Color.RGB.blue_pastel,
        "@left_border_bg;": Color.RGB.gray_darker_mid,
        # Icons
        "@image_arrow_down;": f"url({Icon.ui_arrow_down})".replace("\\", "/"),
        "@image_arrow_down_width;": 12,
        "@image_arrow_down_height;": 12,
    }
    checkbox_base = {
        # Colors
        "@text_color;": Color.RGB.gray_dark_silver,
        # Icons
        "@image_checked;": f"url({Icon.ui_checkbox_enabled})".replace("\\", "/"),
        "@image_checked_width;": 32,
        "@image_checked_height;": 32,
        # Icons
        "@image_unchecked;": f"url({Icon.ui_checkbox_disabled})".replace("\\", "/"),
        "@image_unchecked_width;": 32,
        "@image_unchecked_height;": 32,
    }
    tree_widget_base = {
        # Colors
        "@text_color;": Color.RGB.white,
        "@background_color;": Color.RGB.gray_darker,
        "@item_selected_background_color;": Color.RGB.blue_pastel,
        "@item_hover_background_color;": Color.RGB.gray_light_slate,
        "@image_branch_closed;": f"url({Icon.ui_branch_closed})".replace("\\", "/"),
        "@image_branch_opened;": f"url({Icon.ui_branch_open})".replace("\\", "/"),
        "@image_branch_root_open;": f"url({Icon.ui_branch_root_open})".replace("\\", "/"),
        "@image_branch_root_closed;": f"url({Icon.ui_branch_root_closed})".replace("\\", "/"),
        "@image_branch_end;": f"url({Icon.ui_branch_end})".replace("\\", "/"),
        "@image_branch_line;": f"url({Icon.ui_branch_line}) 0;".replace("\\", "/"),
        "@image_branch_more;": f"url({Icon.ui_branch_more}) 0;".replace("\\", "/"),
        "@image_branch_single;": f"url({Icon.ui_branch_single})".replace("\\", "/"),
        "@image_branch_test;": f"url({Icon.ui_add})".replace("\\", "/"),
    }
    table_widget_base = {
        # Colors
        "@text_color;": Color.RGB.white,  # TODO TEMP @@@
        "@background_color;": Color.RGB.gray_darker,
        "@selected_background_color;": Color.RGB.blue_pastel,
        "@hover_background_color;": Color.RGB.gray_light_slate,
    }
    line_edit_base = {
        # Colors
        "@background_color;": Color.RGB.gray_darker,
        "@background_selection_color;": Color.RGB.gray_darker,
        "@focus_border_color;": Color.RGB.blue_corn_flower,
        "@border_color;": Color.RGB.gray_mid_much_lighter,
        "@text_color;": Color.RGB.white_smoke_darker,
        # Formatting
        "@border_radius;": "7",
        "@padding;": "5",
    }
    menu_base = {
        # Colors
        "@text_color;": Color.RGB.white_smoke_darker,
        "@menu_bg_color;": Color.RGB.gray_mid_lighter,
        "@menu_item_selected_bg_color;": Color.RGB.blue_pastel,
        # Formatting
        "@menu_item_padding;": "5 25 5 25;",
    }
    # Metro QToolButton Start ----------------------------------------------------------------
    btn_tool_metro_base = {
        # Colors
        "@tool_button_text;": Color.RGB.white,
        "@tool_bg_hover_color;": Color.RGB.gray_mid_much_lighter,
        "@tool_bg_click_color;": Color.RGB.gray_much_darker,

        # Formatting
        "@tool_button_padding;": "35",
        "@tool_button_font_size;": "16",
        "@tool_button_border_radius;": "5",
    }
    btn_tool_metro_blue = deepcopy(btn_tool_metro_base)
    btn_tool_metro_blue["@tool_bg_hover_color;"] = Color.RGB.blue_vivid_cerulean
    btn_tool_metro_blue["@tool_bg_click_color;"] = Color.RGB.blue_medium_persian
    btn_tool_metro_red = deepcopy(btn_tool_metro_base)
    btn_tool_metro_red["@tool_bg_hover_color;"] = Color.RGB.red_indian
    btn_tool_metro_red["@tool_bg_click_color;"] = Color.RGB.red_metallic
    btn_tool_metro_green = deepcopy(btn_tool_metro_base)
    btn_tool_metro_green["@tool_bg_hover_color;"] = Color.RGB.green_oxley
    btn_tool_metro_green["@tool_bg_click_color;"] = Color.RGB.green_wintergreen_dream
    # Metro QToolButton End ------------------------------------------------------------------


class Stylesheet:
    def __init__(self):
        """
        A library of stylesheets
        """
    # Stylesheets Without Variations
    maya_dialog_base = get_stylesheet_content(stylesheet_name="maya_dialog_base",
                                              stylesheet_variables=StylesheetVariables.maya_basic)
    progress_bar_base = get_stylesheet_content(stylesheet_name="progress_bar_base",
                                               stylesheet_variables=StylesheetVariables.progress_bar_base)
    scroll_bar_base = get_stylesheet_content(stylesheet_name="scroll_bar_base",
                                             stylesheet_variables=StylesheetVariables.scroll_bar_base)
    list_widget_base = get_stylesheet_content(stylesheet_name="list_widget_base",
                                              stylesheet_variables=StylesheetVariables.list_widget_base)
    text_edit_base = get_stylesheet_content(stylesheet_name="text_edit_base",
                                            stylesheet_variables=StylesheetVariables.text_edit_base)
    combobox_base = get_stylesheet_content(stylesheet_name="combobox_base",
                                           stylesheet_variables=StylesheetVariables.combobox_base)
    checkbox_base = get_stylesheet_content(stylesheet_name="checkbox_base",
                                           stylesheet_variables=StylesheetVariables.checkbox_base)
    tree_widget_base = get_stylesheet_content(stylesheet_name="tree_widget_base",
                                              stylesheet_variables=StylesheetVariables.tree_widget_base)
    table_widget_base = get_stylesheet_content(stylesheet_name="table_widget_base",
                                               stylesheet_variables=StylesheetVariables.table_widget_base)
    line_edit_base = get_stylesheet_content(stylesheet_name="line_edit_base",
                                            stylesheet_variables=StylesheetVariables.line_edit_base)
    menu_base = get_stylesheet_content(stylesheet_name="menu_base",
                                       stylesheet_variables=StylesheetVariables.menu_base)

    # --------------------------------------------- Buttons ---------------------------------------------
    btn_push_base = get_stylesheet_content(stylesheet_name="btn_push_base",
                                           stylesheet_variables=StylesheetVariables.btn_push_base)
    btn_push_bright = get_stylesheet_content(stylesheet_name="btn_push_base",
                                             stylesheet_variables=StylesheetVariables.btn_push_bright)
    btn_radio_base = get_stylesheet_content(stylesheet_name="btn_radio_base",
                                            stylesheet_variables=StylesheetVariables.btn_radio_base)
    # Metro Tool Button
    btn_tool_metro_base = get_stylesheet_content(stylesheet_name="btn_tool_metro_base",
                                                 stylesheet_variables=StylesheetVariables.btn_tool_metro_base)
    btn_tool_metro_red = get_stylesheet_content(stylesheet_name="btn_tool_metro_base",
                                                stylesheet_variables=StylesheetVariables.btn_tool_metro_red)
    btn_tool_metro_blue = get_stylesheet_content(stylesheet_name="btn_tool_metro_base",
                                                 stylesheet_variables=StylesheetVariables.btn_tool_metro_blue)
    btn_tool_metro_green = get_stylesheet_content(stylesheet_name="btn_tool_metro_base",
                                                  stylesheet_variables=StylesheetVariables.btn_tool_metro_green)


class Font:
    def __init__(self):
        """
        A library of fonts
        Note: Make sure fonts are available on Windows and Mac, otherwise include the font file under resources.
        To use these fonts, wrap them around the function
        """
        self.kb = None
    roboto = get_font_path("Roboto-Regular.ttf")
    inter = get_font_path("Inter-Regular.ttf")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Convert RGB to HEX
    all_attributes = dir(Color.RGB)
    user_attributes = [attr for attr in all_attributes if not (attr.startswith('__') and attr.endswith('__'))]
    for rgb_color in user_attributes:
        attribute_content = getattr(Color.RGB, rgb_color)
        if "_ghosted" not in rgb_color:
            hex_converted = rgba_string_to_hex(attribute_content)
            print(f'{rgb_color} = "{hex_converted}"')
