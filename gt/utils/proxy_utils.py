"""
Proxy Utilities
github.com/TrevisanGMW/gt-tools

TODO:
    Proxy (single joint)
    RigComponent (carry proxies, can be complex)
    RigSkeleton, RigBase (carry components)
"""
from gt.utils.uuid_utils import add_uuid_attribute, is_uuid_valid, is_short_uuid_valid, generate_uuid
from gt.utils.attr_utils import add_separator_attr, set_attr
from gt.utils.control_utils import add_snapping_shape
from gt.utils.uuid_utils import find_object_with_uuid
from gt.utils.curve_utils import Curve, get_curve
from gt.utils.naming_utils import NamingConstants
from gt.utils.transform_utils import Transform, Vector3
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProxyConstants:
    def __init__(self):
        """
        Constant values used by all proxy elements.
        """
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_ATTR_UUID = "proxyUUID"
    PROXY_MAIN_CRV = "proxy_main_crv"  # Main control that holds many proxies
    SEPARATOR_ATTR = "proxyPreferences"  # Locked attribute at the top of the proxy options


class Proxy:
    def __init__(self,
                 name=None,
                 transform=None,
                 offset_transform=None,
                 curve=None,
                 uuid=None,
                 parent_uuid=None,
                 locator_scale=None,
                 metadata=None):
        # Default Values
        self.name = "proxy_crv"
        self.transform = transform
        self.offset_transform = transform
        self.curve = get_curve('_proxy_joint')
        self.locator_scale = 1  # 100%
        self.uuid = generate_uuid(remove_dashes=True)
        self.parent_uuid = None
        self.metadata = None

        if name:
            self.set_name(name)
        if transform:
            pass  # TODO @@@
        if curve:
            self.set_curve(curve)
        if uuid:
            self.set_uuid(uuid)
        if parent_uuid:
            self.set_parent_uuid(parent_uuid)
        if locator_scale:
            self.set_locator_scale(locator_scale)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    def is_proxy_valid(self):
        """
        Checks if the current proxy element is valid
        """
        if not self.name:
            logger.warning('Invalid proxy object. Missing name.')
            return False
        if not self.curve:
            logger.warning('Invalid proxy object. Missing curve.')
            return False
        return True

    def build(self):
        """
        Builds a proxy object.
        Returns:
            str: Name of the proxy that was generated/built.
        """
        if not self.is_proxy_valid():
            logger.warning(f'Unable to build proxy. Invalid proxy object.')
            return
        proxy_grp = cmds.group(name=f'{self.name}_{NamingConstants.Suffix.GRP}', world=True, empty=True)
        proxy_crv = self.curve.build()
        cmds.parent(proxy_crv, proxy_grp)
        add_snapping_shape(proxy_crv)
        add_separator_attr(target_object=proxy_crv, attr_name=ProxyConstants.SEPARATOR_ATTR)
        uuid_attrs = add_uuid_attribute(obj_list=proxy_crv,
                                        attr_name=ProxyConstants.PROXY_ATTR_UUID,
                                        set_initial_uuid_value=False)
        for attr in uuid_attrs:
            set_attr(attribute_path=attr, value=self.uuid)
        if self.transform:
            self.apply_transform(target_object=proxy_grp)
        return proxy_crv

    def apply_transform(self, target_object):
        """
        Uses the provided Transform data to set the TRS data of the curve object.
        Args:
            target_object (str): Name of the curve to set with stored Transform data
        """
        if not target_object:
            logger.warning(f'Unable to apply curve transform. Missing target object "{target_object}".')
            return
        if not self.transform:
            logger.warning(f'Unable to apply curve transform. Missing transform data.')
            return
        if not isinstance(self.transform, Transform):
            logger.warning(f'Unable to apply curve transform. '
                           f'Expected "Transform", but got "{str(type(self.transform))}".')
            return
        self.transform.apply_transform(target_object=target_object)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new proxy name. Useful when ingesting data from dictionary or file with undesired name.
        Args:
            name (str): New name to use on the proxy.
        """
        if not name or not isinstance(name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(name))}"')
            return
        self.curve.set_name(name)
        self.name = name

    def set_curve(self, curve, inherit_curve_name=False):
        """
        Sets the curve used to build the proxy element
        Args:
            curve (Curve) A Curve object to be used for building the proxy element (its shape)
            inherit_curve_name (bool, optional): If active, this function try to extract the name of the curve and
                                                 change the name of the proxy to match it. Does nothing if name is None.
        """
        if not curve or not isinstance(curve, Curve):
            logger.debug(f'Unable to set proxy curve. Invalid input. Must be a valid Curve object.')
            return
        if not curve.is_curve_valid():
            logger.debug(f'Unable to set proxy curve. Curve object failed validation.')
            return
        if inherit_curve_name:
            self.set_name(curve.get_name())
        else:
            curve.set_name(name=self.name)
        self.curve = curve

    def set_locator_scale(self, scale):
        if not isinstance(scale, (float, int)):
            logger.debug(f'Unable to set locator scale. Invalid input.')
        self.locator_scale = scale

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set curve metadata. Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

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

    def set_uuid(self, uuid):
        """
        Sets a new UUID for the proxy.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this proxy
        """
        error_message = f'Unable to set proxy UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.uuid = uuid
        else:
            logger.warning(error_message)

    def set_parent_uuid(self, uuid):
        """
        Sets a new parent UUID for the proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            uuid (str): A new UUID for the parent of this proxy
        """
        error_message = f'Unable to set proxy UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

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
    cmds.polySphere()
    test_parent_uuid = generate_uuid()
    proxy_parent = Proxy(name="parent", uuid=test_parent_uuid)
    proxy_parent = proxy_parent.build()
    cmds.move(0, 20, 0, proxy_parent)
    proxy = Proxy()
    proxy.set_parent_uuid(test_parent_uuid)
    proxy.build()

