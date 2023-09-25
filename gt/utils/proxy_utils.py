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
from gt.utils.naming_utils import NamingConstants, get_long_name
from gt.utils.uuid_utils import find_object_with_uuid
from gt.utils.control_utils import add_snapping_shape
from gt.utils.transform_utils import Transform
from gt.utils.hierarchy_utils import parent
from dataclasses import dataclass
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


def parent_proxies(proxy_list):
    # Parent Joints
    for proxy in proxy_list:
        built_proxy = find_object_with_uuid(proxy.get_uuid(), ProxyConstants.PROXY_ATTR_UUID)
        parent_proxy = find_object_with_uuid(proxy.get_parent_uuid(), ProxyConstants.PROXY_ATTR_UUID)
        print(f'built_proxy: {built_proxy}')
        print(f'parent_proxy: {parent_proxy}')
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            offset = cmds.listRelatives(built_proxy, parent=True, fullPath=True)
            if offset:
                parent(source_objects=offset, target_parent=parent_proxy)


@dataclass
class ProxyData:
    """
    A proxy data class used as the proxy response for when the proxy is built.
    """
    name: str  # Long name of the generated proxy (full Maya path)
    offset: str  # Name of the proxy offset (parent of the proxy)
    setup: tuple  # Name of the proxy setup items (rig setup items)

    def __repr__(self):
        """
        String conversion returns the name of the proxy
        Returns:
            str: Proxy long name.
        """
        return self.name

    def get_short_name(self):
        """
        Gets the short version of the proxy name (default name is its long name)
        Note, this name might not be unique
        Returns:
            str: Short name of the proxy (short version of self.name) - Last name after "|" characters
        """
        from gt.utils.naming_utils import get_short_name
        return get_short_name(self.name)

    def get_long_name(self):
        """
        Gets the long version of the proxy name.
        Returns:
            str: Long name of the proxy. (a.k.a. Full Path)
        """
        return self.name

    def get_offset(self):
        """
        Gets the long version of the offset proxy group.
        Returns:
            str: Long name of the proxy group. (a.k.a. Full Path)
        """
        return self.offset

    def get_setup(self):
        """
        Gets the setup items tuple from the proxy data. This is a list of objects used to set up the proxy. (rig setup)
        Returns:
            tuple: A tuple with strings (full paths to the rig elements)
        """
        return self.setup


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
        self.locator_scale = 1  # 100% - Initial curve scale
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
            ProxyData: Name of the proxy that was generated/built.
        """
        if not self.is_proxy_valid():
            logger.warning(f'Unable to build proxy. Invalid proxy object.')
            return
        proxy_offset = cmds.group(name=f'{self.name}_{NamingConstants.Suffix.OFFSET}', world=True, empty=True)
        proxy_crv = self.curve.build()
        proxy_crv = cmds.parent(proxy_crv, proxy_offset)[0]
        proxy_offset = get_long_name(proxy_offset)
        proxy_crv = get_long_name(proxy_crv)
        add_snapping_shape(proxy_crv)
        add_separator_attr(target_object=proxy_crv, attr_name=ProxyConstants.SEPARATOR_ATTR)
        uuid_attrs = add_uuid_attribute(obj_list=proxy_crv,
                                        attr_name=ProxyConstants.PROXY_ATTR_UUID,
                                        set_initial_uuid_value=False)
        scale_attr = add_attr(target_list=proxy_crv, attributes=ProxyConstants.PROXY_ATTR_SCALE, default=1) or []
        loc_scale_cluster = None
        if scale_attr and len(scale_attr) == 1:
            scale_attr = scale_attr[0]
            loc_scale_cluster = add_shape_scale_cluster(proxy_crv, scale_driver_attr=scale_attr)
        for attr in uuid_attrs:
            set_attr(attribute_path=attr, value=self.uuid)
        if self.offset_transform:
            self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if self.transform:
            self.transform.apply_transform(target_object=proxy_crv, object_space=True)
        if self.locator_scale and scale_attr:
            cmds.refresh()  # Without refresh, it fails to show the correct scale
            set_attr(scale_attr, self.locator_scale)

        return ProxyData(name=proxy_crv, offset=proxy_offset, setup=(loc_scale_cluster,))

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new proxy name.
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
        self.offset_transform.set_position(x=x, y=y, z=z, xyz=xyz)

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
            logger.warning(f'Unable to set proxy metadata. Expected a dictionary, but got: "{str(type(metadata))}"')
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

    def set_parent_uuid_from_proxy(self, parent_proxy):
        """
        Sets the provided proxy as the parent  of this proxy. Its UUID  is extracted as parent_UUID for this proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            parent_proxy (Proxy): A proxy object. The UUID for the parent will be extracted from it.
                                  Will be the parent of this proxy when being parented.
        """
        error_message = f'Unable to set proxy parent UUID. Invalid proxy input.'
        if not parent_proxy or not isinstance(parent_proxy, Proxy):
            logger.warning(error_message)
            return
        parent_uuid = parent_proxy.get_uuid()
        self.set_parent_uuid(parent_uuid)

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

    def get_uuid(self):
        """
        Gets the uuid value of this proxy.
        Returns:
            str: uuid string
        """
        return self.uuid

    def get_parent_uuid(self):
        """
        Gets the parent uuid value of this proxy.
        Returns:
            str: uuid string for the potential parent of this proxy.
        """
        return self.parent_uuid


class RigComponentBase:
    def __init__(self,
                 name=None,
                 prefix=None,
                 proxies=None,
                 parent_uuid=None,
                 metadata=None):
        # Default Values
        self.name = None
        self.prefix = None
        self.proxies = []
        self.parent_uuid = None  # RigComponent is parented to this object
        self.metadata = None

        if name:
            self.set_name(name)
        if prefix:
            self.set_prefix(prefix)
        if proxies:
            self.set_proxies(proxies)
        if parent_uuid:
            self.set_parent_uuid(parent_uuid)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new component name.
        Args:
            name (str): New name to use on the proxy.
        """
        if not name or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.prefix = name

    def set_prefix(self, prefix):
        """
        Sets a new component prefix.
        Args:
            prefix (str): New name to use on the proxy.
        """
        if not prefix or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def set_proxies(self, proxy_list):
        """
        Sets a new proxy name.
        Args:
            proxy_list (str): New name to use on the proxy.
        """
        if not proxy_list or not isinstance(proxy_list, list):
            logger.warning(f'Unable to set new list of proxies. '
                           f'Expected list of proxies but got "{str(proxy_list)}"')
            return
        self.proxies = proxy_list

    def add_to_proxies(self, proxy):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            proxy (Proxy, List[Proxy]): New proxy element to be added to this component or a list of proxies
        """
        if proxy and isinstance(proxy, Proxy):
            proxy = [proxy]
        if proxy and isinstance(proxy, list):
            for obj in proxy:
                if isinstance(obj, Proxy):
                    self.proxies.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Incompatible type.')
            return
        logger.debug(f'Unable to add provided proxy to component. '
                     f'Must be of the type "Proxy" or a list containing only Proxy elements.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set component metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
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
    def get_name(self):
        """
        Gets the name property of the rig component.
        Returns:
            str or None: Name of the rig component, None if it's not set.
        """
        return self.prefix

    def get_prefix(self):
        """
        Gets the prefix property of the rig component.
        Returns:
            str or None: Prefix of the rig component, None if it's not set.
        """
        return self.prefix

    def get_proxies(self):
        """
        Gets the proxies in this rig component.
        Returns:
            list: A list of proxies found in this rig component.
        """
        return self.proxies

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig component is valid (can be used)
        """
        if not self.proxies:
            logger.warning('Missing proxies. A rig component needs at least one proxy to function.')
            return False
        return True

    def build_proxy(self):
        for proxy in self.proxies:
            proxy.build()


class RigComponentBipedLeg(RigComponentBase):
    def __init__(self,
                 name="Leg",
                 prefix=None,
                 parent_uuid=None,
                 metadata=None):
        super().__init__(name=name, prefix=prefix, parent_uuid=parent_uuid, metadata=metadata)

        # Default Proxies
        hip = Proxy(name="hip")
        hip.set_position(y=84.5)
        hip.set_locator_scale(scale=0.4)
        knee = Proxy(name="knee")
        knee.set_position(y=47.05)
        knee.set_locator_scale(scale=0.5)
        ankle = Proxy(name="ankle")
        ankle.set_position(y=9.6)
        ankle.set_locator_scale(scale=0.4)
        ball = Proxy(name="ball")
        ball.set_position(z=13.1)
        ball.set_locator_scale(scale=0.4)
        toe = Proxy(name="toe")
        toe.set_position(z=23.4)
        toe.set_locator_scale(scale=0.4)
        toe.set_parent_uuid(uuid=ball.get_uuid())
        toe.set_parent_uuid_from_proxy(parent_proxy=ball)
        heel_pivot = Proxy(name="heelPivot")
        heel_pivot.set_locator_scale(scale=0.1)
        self.proxies.extend([hip, knee, ankle, ball, toe, heel_pivot])

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig component is valid (can be used)
        """
        # TODO Other checks here
        return super().is_valid()


class RigProject:
    def __init__(self,
                 name=None,
                 prefix=None,
                 metadata=None):
        # Default Values
        self.name = None
        self.prefix = None
        self.components = []
        self.metadata = None

        if name:
            self.set_name(name=name)
        if prefix:
            self.set_prefix(prefix=prefix)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new project name.
        Args:
            name (str): New name to use on the proxy.
        """
        if not name or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.prefix = name

    def set_prefix(self, prefix):
        """
        Sets a new component prefix.
        Args:
            prefix (str): New name to use on the proxy.
        """
        if not prefix or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def add_to_components(self, component):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            component (RigComponentBase, List[RigComponentBase]): New component element to be added to this project.
        """
        if component and isinstance(component, RigComponentBase):
            component = [component]
        if component and isinstance(component, list):
            for obj in component:
                if isinstance(obj, RigComponentBase):
                    self.components.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Incompatible type.')
            return
        logger.debug(f'Unable to add provided component to rig project. '
                     f'Must be of the type "RigComponentBase" or a list containing only RigComponentBase elements.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set rig project metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
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

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_name(self):
        """
        Gets the name property of the rig project.
        Returns:
            str or None: Name of the rig project, None if it's not set.
        """
        return self.prefix

    def get_prefix(self):
        """
        Gets the prefix property of the rig project.
        Returns:
            str or None: Prefix of the rig project, None if it's not set.
        """
        return self.prefix

    def get_components(self):
        """
        Gets the components of this rig project.
        Returns:
            list: A list of RigComponentBase of the rig component.
        """
        return self.components

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig project is valid (can be used)
        """
        if not self.components:
            logger.warning('Missing components. A rig project needs at least one component to function.')
            return False
        return True

    def build_proxy(self):
        # Build Proxy
        for component in self.components:
            component.build_proxy()

        # Parent Proxy
        for component in self.components:
            parent_proxies(component.get_proxies())


def create_root_curve(name):
    root_curve = get_curve('_rig_root')
    root_curve.set_name(name=name)
    root_crv = root_curve.build()
    root_grp = cmds.group(empty=True, world=True, name="tempGrp")
    cmds.parent(root_crv, root_grp)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    a_leg = RigComponentBipedLeg()
    a_component = RigComponentBase()

    a_hip = Proxy(name="hip")
    a_hip.set_position(y=84.5)
    a_hip.set_locator_scale(scale=0.4)
    a_knee = Proxy(name="knee")
    a_knee.set_position(y=47.05)
    a_knee.set_locator_scale(scale=0.5)
    a_knee.set_parent_uuid_from_proxy(parent_proxy=a_hip)

    a_component.add_to_proxies([a_hip, a_knee])

    a_project = RigProject()
    a_project.add_to_components(a_component)
    # a_project.add_to_components(a_leg)
    # a_project.build_proxy()

    create_root_curve("main")
