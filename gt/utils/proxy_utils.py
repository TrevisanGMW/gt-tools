"""
Proxy Utilities
github.com/TrevisanGMW/gt-tools

TODO:
    Proxy (single joint)
    RigComponent (carry proxies, can be complex)
    RigSkeleton, RigBase (carry components)

"""
from gt.utils.attr_utils import add_separator_attr
from gt.utils.curve_utils import Curve, get_curve
import maya.cmds as cmds
import logging

# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Constants
PACKAGE_GLOBAL_PREFS = "package_prefs"
PACKAGE_PREFS_DIR = "prefs"
PACKAGE_PREFS_EXT = "json"


class ProxyConstants:
    def __init__(self):
        """
        Constant values used by all proxy elements.
        """
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_MAIN_GRP = "proxy_grp"
    PROXY_BASE_CRV = "proxy_dir_crv"
    PROXY_ATTR_UUID = "proxyUUID"
    SEPARATOR_ATTR = "proxyPreferences"  # Locked attribute at the top of the proxy options


class Proxy:
    def __init__(self,
                 name=None,
                 prefix=None,
                 suffix=None,
                 transform=None,
                 parent=None,
                 shape_scale=None,
                 curve=None,
                 metadata=None,):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.transform = transform
        self.curve = get_curve('_proxy_joint')
        self.metadata = None
        self.parent = None

        if curve:
            self.set_curve(curve)
        if metadata:
            self.set_metadata_dict(new_metadata=metadata)

    def is_proxy_valid(self):
        return True

    def build(self):
        if not self.is_proxy_valid():
            return
        proxy_crv = self.curve.build()
        add_separator_attr(target_object=proxy_crv, attr_name=ProxyConstants.SEPARATOR_ATTR)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_curve(self, curve):

        if not curve or not isinstance(curve, Curve):
            logger.debug(f'Unable to set proxy curve. Invalid input. Must be a valid Curve object.')
            return
        if not curve.is_curve_valid():
            logger.debug(f'Unable to set proxy curve. Curve object failed validation.')
            return
        self.curve = curve

    def set_name(self, new_name):
        """
        Sets a new curve name. Useful when ingesting data from dictionary or file with undesired name.
        Args:
            new_name (str): New name to use on the curve.
        """
        if not new_name or not isinstance(new_name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(new_name))}"')
            return
        self.name = new_name

    def set_metadata_dict(self, new_metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            new_metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(new_metadata, dict):
            logger.warning(f'Unable to set curve metadata. Expected a dictionary, but got: "{str(type(new_metadata))}"')
            return
        self.metadata = new_metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_name(self):
        """
        Gets the name property of the proxy.
        Returns:
            str or None: Name of the proxy, None if it's not set.
        """
        return self.name


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    proxy = Proxy()
    proxy.build()
