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
    tool_sphere_types = get_icon_path(r"tool_sphere_types.svg")
    util_mod_load_udims = get_icon_path(r"util_mod_load_udims.svg")
    util_mod_bif_to_mesh = get_icon_path(r"util_mod_bif_to_mesh.svg")
    util_mod_copy_material = get_icon_path(r"util_mod_copy_material.svg")
    util_mod_paste_material = get_icon_path(r"util_mod_paste_material.svg")
    # Rigging
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
    # Utils
    util_reload_file = get_icon_path(r"util_reload_file.svg")
    util_open_dir = get_icon_path(r"util_open_dir.svg")
    util_hud_toggle = get_icon_path(r"util_hud_toggle.svg")
    util_resource_browser = get_icon_path(r"util_resource_browser.svg")
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
    scrollbar_up = get_icon_path(r"scrollbar_up.svg")
    scrollbar_down = get_icon_path(r"scrollbar_down.svg")
    scrollbar_left = get_icon_path(r"scrollbar_left.svg")
    scrollbar_right = get_icon_path(r"scrollbar_right.svg")
    setup_install = get_icon_path(r"setup_install.svg")
    setup_uninstall = get_icon_path(r"setup_uninstall.svg")
    setup_run_only = get_icon_path(r"setup_run_only.svg")
    setup_close = get_icon_path(r"setup_close.svg")
    curve_library_missing_file = get_icon_path(r"curve_library_missing_file.svg")
    curve_library_base_curve = get_icon_path(r"curve_library_base_curve.svg")
    curve_library_user_curve = get_icon_path(r"curve_library_user_curve.svg")
    curve_library_control = get_icon_path(r"curve_library_control.svg")
    curve_library_parameters = get_icon_path(r"curve_library_parameters.svg")
    curve_library_build = get_icon_path(r"curve_library_build.svg")
    curve_library_edit = get_icon_path(r"curve_library_edit.svg")
    curve_library_snapshot = get_icon_path(r"curve_library_snapshot.svg")
    curve_library_remove = get_icon_path(r"curve_library_remove.svg")
    curve_library_add = get_icon_path(r"curve_library_add.svg")
    ui_exclamation = get_icon_path(r"ui_exclamation.svg")


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
        transparent = 'rgba(0,0,0,0)'
        white = 'rgba(255,255,255,255)'
        white_soft = 'rgba(238,238,238,255)'
        white_soft_ghosted = 'rgba(238,238,238,75)'

        grey_darker = 'rgba(29,29,29,255)'
        grey_dark = 'rgba(43,43,43,255)'
        grey_dark_ghosted = 'rgba(43,43,43,75)'
        grey = 'rgba(68,68,68,255)'
        grey_ghosted = 'rgba(68,68,68,75)'
        grey_mid = 'rgba(73,73,73,255)'
        grey_mid_light = 'rgba(82,82,82,255)'
        grey_mid_lighter = 'rgba(93,93,93,255)'
        grey_mid_much_lighter = 'rgba(112,112,112,255)'
        grey_light = 'rgba(145,145,145,255)'
        grey_lighter = 'rgba(160,160,160,255)'
        grey_much_lighter = 'rgba(180,180,180,255)'

        black = 'rgba(0,0,0,255)'

        red = 'rgba(255,0,0,255)'
        red_softer = 'rgba(212,87,87,255)'
        red_dark = 'rgba(175,45,45,255)'

        green = 'rgb(0, 255, 0, 255)'
        green_soft = 'rgb(96, 152, 129, 255)'
        green_light = 'rgb(144, 228, 193, 255)'
        green_dark = 'rgba(88,140,119,255)'

        blue = 'rgba(0,0,255,255)'
        blue_ghosted = 'rgba(0,0,255,75)'
        blue_soft = 'rgba(189, 217, 255,255)'
        blue_soft_dark = 'rgba(82,133,166,255)'
        blue_vivid = 'rgba(0,160,232,255)'
        blue_dark = 'rgba(0,110,160,255)'

    class Hex:
        def __init__(self):
            """
            A library of Hex colors
            """
        black = '#000000'
        white = '#FFFFFF'
        white_soft = '#EEEEEE'
        grey_dark = '#2B2B2B'
        grey = '#444444'
        grey_mid = '#494949'
        grey_lighter = '#A0A0A0'
        red = '#FF0000'
        red_soft = '#FFAAAA'
        red_softer = '#D45757'
        red_dark = '#AF2D2D'
        green = '#20A500'
        green_light = '#90E4C1'
        green_soft = '#609881'
        green_dark = '#588C77'
        blue = '#0033FF'
        blue_dark = '#006EA0'
        blue_vivid = '#00A0E8'
        orange = '#FFBB00'
        lime = '#32FF00'
        yellow = '#FFEE00'
        yellow_dark = '#636110'
        teal = '#00FFFF'
        purple = '#DD22FF'
        pink = '#F700FF'
        magenta = '#C40B5F'
        violet = '#FF22BB'
        cyan_soft = "#48E0DB"

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
        "@maya_background_grey;": Color.RGB.grey,
        "@maya_background_dark;": Color.RGB.grey_dark,
        "@maya_background_darker;": Color.RGB.grey_darker,
        "@maya_background_grey_dark;": Color.RGB.grey_dark,
        "@maya_button;": Color.RGB.grey_mid_lighter,
        "@maya_button_hover;": Color.RGB.grey_mid_much_lighter,
        "@maya_button_clicked;": Color.RGB.grey_darker,
        "@maya_selection;": Color.RGB.blue_soft_dark,
        "@maya_text;": Color.RGB.white_soft,
        "@background_disabled_color;": Color.RGB.grey_mid_light,
        "@disabled_text_color;": Color.RGB.grey_mid_much_lighter,
        "@text_edit_border;": Color.RGB.grey,
        # Formatting
        "@maya_small_button_padding;": "5",
    }
    scrollbar_dark = {
        "@background_mid;": Color.RGB.grey,
        "@background_dark;": Color.RGB.grey_dark,
        "@scroll_area_border;": Color.RGB.grey_mid_much_lighter,
        "@scrollbar_line_background;": Color.RGB.grey_darker,
        "@scrollbar_sub_line;": Color.RGB.grey,
        "@scrollbar_handle;": Color.RGB.grey_mid_much_lighter,
        "@scrollbar_handle_pressed;": Color.RGB.grey_much_lighter,
        "@scrollbar_background;": Color.RGB.grey_dark,
        # Sizes
        "@scrollbar_size;": 15,
        "@sub_control_size;": 15,
        # Icons
        "@image_scrollbar_up;": f"url({Icon.scrollbar_up})".replace("\\", "/"),
        "@image_scrollbar_down;": f"url({Icon.scrollbar_down})".replace("\\", "/"),
        "@image_scrollbar_left;": f"url({Icon.scrollbar_left})".replace("\\", "/"),
        "@image_scrollbar_right;": f"url({Icon.scrollbar_right})".replace("\\", "/"),
    }
    text_edit_mid_grey = {
        "@background_mid;": Color.RGB.grey,
        "@border_color;": Color.RGB.grey_mid_much_lighter,
    }
    progress_bar_dark = {
        # Colors
        "@progress_bar_background;": Color.RGB.grey_mid_much_lighter,
        "@progress_bar_chunk;": Color.RGB.blue_soft,
    }
    list_widget_dark = {
        # Colors
        "@list_background_color;": Color.RGB.grey_darker,
        "@list_text_color;": Color.RGB.grey_much_lighter,
        "@list_selection_bg_color;": Color.RGB.blue_soft_dark,
        "@list_selection_text_color;": Color.RGB.white,
        "@list_hover_bg_color;": Color.RGB.grey,
        "@list_hover_text_color;": Color.RGB.white,
    }
    push_button_bright = {
        # Colors
        "@background_color;": Color.RGB.grey_light,
        "@background_hover_color;": Color.RGB.grey_lighter,
        "@background_pressed_color;": Color.RGB.grey_mid_lighter,
        "@background_disabled_color;": Color.RGB.grey_mid_light,
        "@text_color;": Color.RGB.black,
        "@disabled_text_color;": Color.RGB.grey_mid_much_lighter,

        # Formatting
        "@button_padding;": "15",
    }
    # Metro QToolButton Start ----------------------------------------------------------------
    button_metro_tools_default = {
        # Colors
        "@tool_button_text;": Color.RGB.white,
        "@tool_bg_hover_color;": Color.RGB.grey_mid_much_lighter,
        "@tool_bg_click_color;": Color.RGB.grey_darker,

        # Formatting
        "@tool_button_padding;": "35",
        "@tool_button_font_size;": "16",
        "@tool_button_border_radius;": "5",
    }
    button_metro_tools_blue = deepcopy(button_metro_tools_default)
    button_metro_tools_blue["@tool_bg_hover_color;"] = Color.RGB.blue_vivid
    button_metro_tools_blue["@tool_bg_click_color;"] = Color.RGB.blue_dark
    button_metro_tools_red = deepcopy(button_metro_tools_default)
    button_metro_tools_red["@tool_bg_hover_color;"] = Color.RGB.red_softer
    button_metro_tools_red["@tool_bg_click_color;"] = Color.RGB.red_dark
    button_metro_tools_green = deepcopy(button_metro_tools_default)
    button_metro_tools_green["@tool_bg_hover_color;"] = Color.RGB.green_soft
    button_metro_tools_green["@tool_bg_click_color;"] = Color.RGB.green_dark
    # Metro QToolButton End ------------------------------------------------------------------


class Stylesheet:
    def __init__(self):
        """
        A library of stylesheets
        """
    # Stylesheets Without Variations
    maya_basic_dialog = get_stylesheet_content(stylesheet_name="maya_basic_dialog",
                                               stylesheet_variables=StylesheetVariables.maya_basic)
    progress_bar_dark = get_stylesheet_content(stylesheet_name="progress_bar_dark",
                                               stylesheet_variables=StylesheetVariables.progress_bar_dark)
    scroll_bar_dark = get_stylesheet_content(stylesheet_name="scroll_bar_dark",
                                             stylesheet_variables=StylesheetVariables.scrollbar_dark)
    list_widget_dark = get_stylesheet_content(stylesheet_name="list_widget_dark",
                                              stylesheet_variables=StylesheetVariables.list_widget_dark)
    text_edit_mid_grey = get_stylesheet_content(stylesheet_name="text_edit_mid_grey",
                                                stylesheet_variables=StylesheetVariables.text_edit_mid_grey)
    # --------------------------------------------- Buttons ---------------------------------------------
    push_button_bright = get_stylesheet_content(stylesheet_name="push_button_bright",
                                                stylesheet_variables=StylesheetVariables.push_button_bright)
    # Metro Tool Button
    button_metro_tool = get_stylesheet_content(stylesheet_name="button_metro_tool",
                                               stylesheet_variables=StylesheetVariables.button_metro_tools_default)
    button_metro_tool_red = get_stylesheet_content(stylesheet_name="button_metro_tool",
                                                   stylesheet_variables=StylesheetVariables.button_metro_tools_red)
    button_metro_tool_blue = get_stylesheet_content(stylesheet_name="button_metro_tool",
                                                    stylesheet_variables=StylesheetVariables.button_metro_tools_blue)
    button_metro_tool_green = get_stylesheet_content(stylesheet_name="button_metro_tool",
                                                     stylesheet_variables=StylesheetVariables.button_metro_tools_green)


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
    from pprint import pprint
    out = None
    out = Icon.package_icon
    pprint(out)

