import logging
import os


# Logging Setup
logging.basicConfig()
logger = logging.getLogger("resource_library")
logger.setLevel(logging.INFO)


def get_icon_path(icon_name, sub_folder=None):
    if not sub_folder:
        icon_path = os.path.join(ResourceDirConstants.DIR_ICONS, icon_name)
    else:
        icon_path = os.path.join(ResourceDirConstants.DIR_ICONS, icon_name)
    if not os.path.exists(icon_path) or icon_name == '':
        logger.info(f'Could not find icon: "{icon_path}"')
    return icon_path


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


if __name__ == "__main__":
    print(get_icon_path("a"))