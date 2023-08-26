"""
Proxy Utilities
github.com/TrevisanGMW/gt-tools

TODO:
    Proxy (single joint)
    RigComponent (carry proxies, can be complex)
    RigSkeleton, RigBase (carry components)
"""
from gt.utils.uuid_utils import add_uuid_attribute, is_uuid_valid, is_short_uuid_valid, generate_uuid
from gt.utils.curve_utils import Curve, get_curve, add_shape_scale_cluster
from gt.utils.attr_utils import add_separator_attr, set_attr, add_attr
from gt.utils.control_utils import add_snapping_shape
from gt.utils.naming_utils import NamingConstants
from gt.utils.transform_utils import Transform
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
    PROXY_ATTR_SCALE = "locatorScale"
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
        self.name = "proxy"
        self.transform = Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)
        self.offset_transform = Transform()
        self.curve = get_curve('_proxy_joint')
        self.curve.set_name(name=self.name)
        self.locator_scale = 1  # 100%
        self.uuid = generate_uuid(remove_dashes=True)
        self.parent_uuid = None
        self.metadata = None

        if name:
            self.set_name(name)
        if transform:
            self.set_transform(transform)
        if offset_transform:
            self.set_offset_transform(offset_transform)
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
        proxy_offset = cmds.group(name=f'{self.name}_{NamingConstants.Suffix.OFFSET}', world=True, empty=True)
        proxy_crv = self.curve.build()
        cmds.parent(proxy_crv, proxy_offset)
        add_snapping_shape(proxy_crv)
        add_separator_attr(target_object=proxy_crv, attr_name=ProxyConstants.SEPARATOR_ATTR)
        uuid_attrs = add_uuid_attribute(obj_list=proxy_crv,
                                        attr_name=ProxyConstants.PROXY_ATTR_UUID,
                                        set_initial_uuid_value=False)
        scale_attr = add_attr(target_list=proxy_crv, attributes=ProxyConstants.PROXY_ATTR_SCALE, default=1) or []
        if scale_attr and len(scale_attr) == 1:
            scale_attr = scale_attr[0]
            add_shape_scale_cluster(proxy_crv, scale_driver_attr=scale_attr)
        for attr in uuid_attrs:
            set_attr(attribute_path=attr, value=self.uuid)
        if self.offset_transform:
            self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if self.transform:
            self.transform.apply_transform(target_object=proxy_crv, object_space=True)
        if self.locator_scale and scale_attr:
            cmds.refresh()
            set_attr(scale_attr, self.locator_scale)
        return proxy_crv

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

    def set_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.transform = transform

    def set_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_offset_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.offset_transform = transform

    def set_offset_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_offset_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.offset_transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_offset_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.offset_transform.set_scale(x=x, y=y, z=z, xyz=xyz)

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
        error_message = f'Unable to set proxy parent UUID. Invalid UUID input.'
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
    # cmds.polySphere()
    test_parent_uuid = generate_uuid()
    # proxy_parent = Proxy(name="parent", uuid=test_parent_uuid)
    # proxy_parent = proxy_parent.build()
    # cmds.move(0, 20, 0, proxy_parent)
    temp_trans = Transform()
    temp_trans.set_position(0, 10, 0)
    proxy = Proxy()
    proxy.set_transform(temp_trans)
    proxy.set_offset_position(0, 5, 5)
    proxy.set_parent_uuid(test_parent_uuid)
    proxy.set_curve(get_curve("_proxy_joint_handle"))
    proxy.set_locator_scale(5)
    proxy.build()
