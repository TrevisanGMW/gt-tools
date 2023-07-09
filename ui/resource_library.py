from PySide2 import QtGui
import logging
import os

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
        stylesheet_content = process_stylesheet_variables(stylesheet_content=open(stylesheet_path).read(),
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
    # Misc
    abr_create_proxy = get_icon_path(r"abr_create_proxy.svg")
    abr_create_rig = get_icon_path(r"abr_create_rig.svg")
    package_logo = get_icon_path(r"package_logo.png")
    package_icon = get_icon_path(r"package_icon.png")
    cog_icon = get_icon_path(r"cog.svg")
    scrollbar_up = get_icon_path(r"scrollbar_up.svg")
    scrollbar_down = get_icon_path(r"scrollbar_down.svg")


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
        green = '#20A500'
        blue = '#0033FF'
        orange = '#FFBB00'
        lime = '#32FF00'
        yellow = '#FFEE00'
        yellow_dark = '#636110'
        teal = '#00FFFF'
        purple = '#DD22FF'
        pink = '#F700FF'
        magenta = '#C40B5F'
        violet = '#ff22BB'

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
        "@maya_background_mid": Color.RGB.grey,
        "@maya_background_dark": Color.RGB.grey_dark,
        "@maya_background_darker": Color.RGB.grey_darker,
        "@maya_background_light": Color.RGB.grey_mid,
        "@maya_button": Color.RGB.grey_light,
        "@maya_button_hover": Color.RGB.grey_lighter,
        "@maya_button_clicked": Color.RGB.grey_darker,
        "@maya_selection": Color.RGB.blue_soft_dark,
        "@maya_text": Color.RGB.white_soft,
        # Formatting
        "@maya_small_button_padding": "5",
    }
    maya_progress_bar = {
        # Colors
        "@maya_background_mid": Color.RGB.grey,
        "@maya_background_dark": Color.RGB.grey_dark,
        "@maya_background_darker": Color.RGB.grey_darker,
        "@maya_background_light": Color.RGB.grey_mid,
        "@maya_button": Color.RGB.grey_light,
        "@maya_button_hover": Color.RGB.grey_lighter,
        "@maya_button_clicked": Color.RGB.grey_darker,
        "@maya_selection": Color.RGB.blue_soft_dark,
        "@maya_text": Color.RGB.white_soft,
        "@progress_bar_background": Color.RGB.grey_lighter,
        "@progress_bar_chunk": Color.RGB.blue_soft,
        "@scrollbar_line_background": Color.RGB.grey_darker,
        "@scrollbar_sub_line": Color.RGB.grey,
        "@scrollbar_handle": Color.RGB.grey_lighter,
        "@scrollbar_handle_pressed": Color.RGB.grey_much_lighter,
        "@scrollbar_background": Color.RGB.grey_dark,
        "@output_text_border": Color.RGB.grey_lighter,
        "@output_text_color": Color.RGB.white_soft,
        "@output_text_color_border": Color.RGB.grey,

        # Formatting
        "@maya_small_button_padding": "5",
        # Icons
        "@image_scrollbar_up": f"url({Icon.scrollbar_up})".replace("\\", "/"),
        "@image_scrollbar_down": f"url({Icon.scrollbar_down})".replace("\\", "/"),
    }


class Stylesheet:
    def __init__(self):
        """
        A library of stylesheets
        """
    maya_basic_dialog = get_stylesheet_path(stylesheet_name="maya_basic_dialog",
                                            stylesheet_variables=StylesheetVariables.maya_basic)
    maya_progress_bar = get_stylesheet_path(stylesheet_name="maya_progress_bar",
                                            stylesheet_variables=StylesheetVariables.maya_progress_bar)


class Font:
    def __init__(self):
        """
        A library of fonts
        Note: Make sure fonts are available on Windows and Mac, otherwise include the font file under resources.
        """
    console = QtGui.QFont("Courier New", 12, QtGui.QFont.Bold)


if __name__ == "__main__":
    from pprint import pprint
    out = None
    pprint(out)
