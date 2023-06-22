import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("resource_library")
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


def get_stylesheet_path(stylesheet_name, sub_folder=None, file_extension="qss"):
    """
   Get the path to a stylesheet (qss) file. This file should exist inside the resources/stylesheet folder.
   Args:
       stylesheet_name (str): Name of the file without its extension. Since all files share the same extension "qss"
                              you can provide just the name of the file. If an extension is provided, it is replaced.
       sub_folder (optional, str): In case the icon exists inside a sub-folder, it can be provided as an argument.
                                   For example, if the icon is inside "../resource/icons/my_folder/icon.svg"
                                   One would call "get_icon_path("icon.svg", "my_folder")"
       file_extension (optional, str): File extension used to find the file.
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
        stylesheet_content = open(stylesheet_path).read()
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
    package_logo = get_icon_path(r"package_logo.png")
    cog_icon = get_icon_path(r"cog.svg")
    # Root Menu
    root_general = get_icon_path(r"root_general.svg")
    root_curves = get_icon_path(r"root_curves.svg")
    root_modeling = get_icon_path(r"root_modeling.svg")
    root_rigging = get_icon_path(r"root_rigging.svg")
    # Tools
    maya_to_discord_icon = get_icon_path(r"maya_to_discord.svg")
    fspy_importer = get_icon_path(r"fspy_importer.png")
    # Misc
    abr_create_proxy = get_icon_path(r"abr_create_proxy.svg")
    abr_create_rig = get_icon_path(r"abr_create_rig.svg")


class Stylesheet:
    def __init__(self):
        """
        A library of stylesheets
        """
    maya_bordered_widget = get_stylesheet_path(r"maya_bordered_widget")
    dark_style_stylesheet = get_stylesheet_path(r"darkstyle")


if __name__ == "__main__":
    from pprint import pprint
    out = None
    pprint(out)
