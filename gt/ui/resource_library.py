import logging
import os

# Logging Setup
from copy import deepcopy

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
        resource_path = os.path.join(resource_folder, resource_name)
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


def get_stylesheet_path(stylesheet_name, sub_folder=None, file_extension="qss", stylesheet_variables=None):
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
    # Tools
    maya_to_discord_icon = get_icon_path(r"maya_to_discord.svg")
    fspy_importer = get_icon_path(r"fspy_importer.svg")
    render_calculator = get_icon_path(r"render_calculator.svg")
    startup_booster = get_icon_path(r"startup_booster.svg")
    renamer = get_icon_path(r"renamer.svg")
    outliner_sorter = get_icon_path(r"outliner_sorter.svg")
    selection_manager = get_icon_path(r"selection_manager.svg")
    path_manager = get_icon_path(r"path_manager.svg")
    color_manager = get_icon_path(r"color_manager.svg")
    transfer_transforms = get_icon_path(r"transfer_transforms.svg")
    world_space_baker = get_icon_path(r"world_space_baker.svg")
    attributes_to_python = get_icon_path(r"attributes_to_python.svg")
    render_checklist = get_icon_path(r"render_checklist.svg")
    # Curves
    crv_to_python = get_icon_path(r"crv_to_python.svg")
    crv_text = get_icon_path(r"crv_text.svg")
    crv_state = get_icon_path(r"crv_state.svg")
    crv_combine = get_icon_path(r"crv_combine.svg")
    crv_separate = get_icon_path(r"crv_separate.svg")
    # Modeling
    mod_transfer_uvs = get_icon_path(r"mod_transfer_uvs.svg")
    mod_sphere_types = get_icon_path(r"mod_sphere_types.svg")
    mod_load_udims = get_icon_path(r"mod_load_udims.svg")
    mod_bif_to_mesh = get_icon_path(r"mod_bif_to_mesh.svg")
    mod_copy_material = get_icon_path(r"mod_copy_material.svg")
    mod_paste_material = get_icon_path(r"mod_paste_material.svg")
    # Rigging
    rig_auto_rigger = get_icon_path(r"rig_auto_rigger.svg")
    # Help
    rebuild_menu = get_icon_path(r"rebuild_menu.svg")
    check_for_updates = get_icon_path(r"check_for_updates.svg")
    about = get_icon_path(r"about.svg")
    current_version = get_icon_path(r"current_version.svg")
    # Misc
    abr_create_proxy = get_icon_path(r"abr_create_proxy.svg")
    abr_create_rig = get_icon_path(r"abr_create_rig.svg")
    package_logo = get_icon_path(r"package_logo.png")
    package_icon = get_icon_path(r"package_icon.png")
    cog_icon = get_icon_path(r"cog.svg")
    scrollbar_up = get_icon_path(r"scrollbar_up.svg")
    scrollbar_down = get_icon_path(r"scrollbar_down.svg")
    setup_install = get_icon_path(r"setup_install.svg")
    setup_uninstall = get_icon_path(r"setup_uninstall.svg")
    setup_run_only = get_icon_path(r"setup_run_only.svg")
    setup_close = get_icon_path(r"setup_close.svg")


class Color:
    def __init__(self):
        """
        A library of colors
        """
    class Hex:
        def __init__(self):
            """
            A library of Hex colors
            """
        black = '#000000'
        white = '#FFFFFF'
        grey = '#808080'
        grey_dark = '#555555'
        red = '#FF0000'
        red_soft = '#FFAAAA'
        red_softer = '#D45757'
        red_dark = '#AF2D2D'
        green = '#20A500'
        green_light = '#AAFFAA'
        green_soft = '#609881'
        green_dark = '#588C77'
        blue = '#0033FF'
        blue_dark = '#006EA0'
        blue_soft = '#00A0E8'
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

    class RGB:
        def __init__(self):
            """
            A library of colors RGB+A colors.
            Format:
            rgba(Red, Green, Blue, Alpha)
            e.g. "rgba(255, 0, 0, 255)" = Red, full opacity
            Value range 0-255
            """
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
        grey_light = 'rgba(93,93,93,255)'
        grey_lighter = 'rgba(112,112,112,255)'
        grey_much_lighter = 'rgba(180,180,180,255)'

        black = 'rgba(0,0,0,255)'

        red = 'rgb(255, 0, 0, 255)'

        green = 'rgb(0, 255, 0, 255)'
        green_soft = 'rgb(96, 152, 129, 255)'
        green_light = 'rgb(144, 228, 193, 255)'

        blue = 'rgba(0,0,255,255)'
        blue_ghosted = 'rgba(0,0,255,75)'
        blue_soft = 'rgba(189, 217, 255,255)'
        blue_soft_dark = 'rgba(82,133,166,255)'

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
        "@maya_background_mid;": Color.RGB.grey,
        "@maya_background_dark;": Color.RGB.grey_dark,
        "@maya_background_darker;": Color.RGB.grey_darker,
        "@maya_background_light;": Color.RGB.grey_mid,
        "@maya_button;": Color.RGB.grey_light,
        "@maya_button_hover;": Color.RGB.grey_lighter,
        "@maya_button_clicked;": Color.RGB.grey_darker,
        "@maya_selection;": Color.RGB.blue_soft_dark,
        "@maya_text;": Color.RGB.white_soft,
        "@text_edit_border;": Color.RGB.grey,
        # Formatting
        "@maya_small_button_padding;": "5",
    }
    dark_scrollbar = {
        "@background_mid;": Color.RGB.grey,
        "@background_dark;": Color.RGB.grey_dark,
        "@scroll_area_border;": Color.RGB.grey_lighter,
        "@scrollbar_line_background;": Color.RGB.grey_darker,
        "@scrollbar_sub_line;": Color.RGB.grey,
        "@scrollbar_handle;": Color.RGB.grey_lighter,
        "@scrollbar_handle_pressed;": Color.RGB.grey_much_lighter,
        "@scrollbar_background;": Color.RGB.grey_dark,
        # Icons
        "@image_scrollbar_up;": f"url({Icon.scrollbar_up})".replace("\\", "/"),
        "@image_scrollbar_down;": f"url({Icon.scrollbar_down})".replace("\\", "/"),
    }
    dark_progress_bar = {
        # Colors
        "@progress_bar_background;": Color.RGB.grey_lighter,
        "@progress_bar_chunk;": Color.RGB.blue_soft,
    }
    # Metro QToolButton Start ----------------------------------------------------------------
    metro_tools_button_default = {
        # Colors
        "@tool_button_text;": Color.RGB.white,
        "@tool_bg_hover_color;": Color.RGB.grey_lighter,
        "@tool_bg_click_color;": Color.RGB.grey_darker,

        # Formatting
        "@tool_button_padding;": "35",
        "@tool_button_font_size;": "16",
        "@tool_button_border_radius;": "5",
    }
    metro_tools_button_blue = deepcopy(metro_tools_button_default)
    metro_tools_button_blue["@tool_bg_hover_color;"] = Color.Hex.blue_soft
    metro_tools_button_blue["@tool_bg_click_color;"] = Color.Hex.blue_dark
    metro_tools_button_red = deepcopy(metro_tools_button_default)
    metro_tools_button_red["@tool_bg_hover_color;"] = Color.Hex.red_softer
    metro_tools_button_red["@tool_bg_click_color;"] = Color.Hex.red_dark
    metro_tools_button_green = deepcopy(metro_tools_button_default)
    metro_tools_button_green["@tool_bg_hover_color;"] = Color.Hex.green_soft
    metro_tools_button_green["@tool_bg_click_color;"] = Color.Hex.green_dark
    # Metro QToolButton End ------------------------------------------------------------------


class Stylesheet:
    def __init__(self):
        """
        A library of stylesheets
        """
    # Stylesheets Without Variations
    maya_basic_dialog = get_stylesheet_path(stylesheet_name="maya_basic_dialog",
                                            stylesheet_variables=StylesheetVariables.maya_basic)
    dark_progress_bar = get_stylesheet_path(stylesheet_name="dark_progress_bar",
                                            stylesheet_variables=StylesheetVariables.dark_progress_bar)
    dark_scroll_bar = get_stylesheet_path(stylesheet_name="dark_scroll_bar",
                                          stylesheet_variables=StylesheetVariables.dark_scrollbar)
    dark_list_widget = get_stylesheet_path(stylesheet_name="dark_list_widget",
                                           stylesheet_variables=StylesheetVariables.dark_progress_bar)
    # Metro Tool Button
    metro_tool_button = get_stylesheet_path(stylesheet_name="metro_tool_button",
                                            stylesheet_variables=StylesheetVariables.metro_tools_button_default)
    metro_tool_button_red = get_stylesheet_path(stylesheet_name="metro_tool_button",
                                                stylesheet_variables=StylesheetVariables.metro_tools_button_red)
    metro_tool_button_blue = get_stylesheet_path(stylesheet_name="metro_tool_button",
                                                 stylesheet_variables=StylesheetVariables.metro_tools_button_blue)
    metro_tool_button_green = get_stylesheet_path(stylesheet_name="metro_tool_button",
                                                  stylesheet_variables=StylesheetVariables.metro_tools_button_green)


class Font:
    def __init__(self):
        """
        A library of fonts
        Note: Make sure fonts are available on Windows and Mac, otherwise include the font file under resources.
        To use these fonts, wrap them around the function
        """
        self.kb = None
    courier_new = "Courier New"
    roboto = get_font_path("Roboto-Regular.ttf")
    inter = get_font_path("Inter-Regular.ttf")


if __name__ == "__main__":
    from pprint import pprint
    out = None
    out = Stylesheet.dark_progress_bar
    pprint(out)

