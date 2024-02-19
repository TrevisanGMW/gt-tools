"""
Surface Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.curve_utils import get_curve, get_positions_from_curve, rescale_curve
from gt.utils.iterable_utils import sanitize_maya_list, filter_list_by_type
from gt.utils.attr_utils import hide_lock_default_attrs, set_trs_attr
from gt.utils.color_utils import set_color_viewport, ColorConstants
from gt.utils.transform_utils import match_transform
from gt.utils.math_utils import get_bbox_position
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SURFACE_TYPE = "nurbsSurface"


def is_surface(surface, accept_transform_parent=True):
    """
    Check if the provided object is a NURBS surface or transform parent of a surface.

    Args:
        surface (str): Object to check.
        accept_transform_parent (bool, optional): If True, accepts transform parent as surface
                                                  in case it has a surface shapes as its child.
    Returns:
        bool: True if the object is a NURBS surface or transform parent of a surface, False otherwise.
    """
    if not cmds.objExists(surface):
        return False

    # Check shape
    if cmds.objectType(surface) == 'transform' and accept_transform_parent:
        surface = cmds.listRelatives(surface, shapes=True, noIntermediate=True, path=True)[0]

    return cmds.objectType(surface) == SURFACE_TYPE

def is_surface_periodic(surface_shape):
    """
    Determine if a surface is periodic.
    Args:
        surface_shape (str): The name of the surface shape (or its transform).

    Returns:
        bool: True if the surface is periodic, False otherwise.
    """
    form_u = cmds.getAttr(f"{surface_shape}.formU")
    form_v = cmds.getAttr(f'{surface_shape}.formV')
    if form_u == 2 or form_v == 2:
        return True
    return False


def get_surface_function_set(surface):
    """
    Creates MFnNurbsSurface class object from the provided NURBS surface.

    Args:
        surface (str): Surface to create function class for.

    Returns:
        OpenMaya.MFnNurbsSurface: The MFnNurbsSurface class object.
    """
    if not is_surface(surface):
        raise ValueError(f'Unable to get MFnNurbsSurface from "{surface}". Provided object is not a surface.')

    if cmds.objectType(surface) == 'transform':
        surface = cmds.listRelatives(surface, shapes=True, noIntermediate=True, path=True)[0]

    # Retrieve MFnNurbsSurface
    selection = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getSelectionListByName(surface, selection)
    surface_path = OpenMaya.MDagPath()
    selection.getDagPath(0, surface_path)
    surface_fn = OpenMaya.MFnNurbsSurface()
    surface_fn.setObject(surface_path)
    return surface_fn


def create_surface_from_object_list(obj_list, surface_name=None, degree=3):
    """
    Creates a surface from a list of objects (according to list order)
    The surface is created using curve offsets.
        1. A curve is created using the position of the objects from the list.
        2. Two offset curves are created from the initial curve.
        3. A loft surface is created out of the two offset curves.
    Args:
        obj_list (list): List of objects used to generate the surface (order matters)
        surface_name (str, optional): Name of the generated surface.
        degree (int, optional): The degree of the generated lofted surface. Default is cubic (3)
    Returns:
        str or None: Generated surface (loft) object, otherwise None.
    """
    # Check if there are at least two objects in the list
    if len(obj_list) < 2:
        cmds.warning("At least two objects are required to create a surface.")
        return

    # Get positions of the objects
    positions = [cmds.xform(obj, query=True, translation=True, worldSpace=True) for obj in obj_list]

    # Create a curve with the given positions as control vertices (CVs)
    crv_mid = cmds.curve(d=1, p=positions, n=f'{surface_name}_curveFromList')
    crv_mid = Node(crv_mid)

    # Offset the duplicated curve positively
    offset_distance = 1
    crv_pos = cmds.offsetCurve(crv_mid, name=f'{crv_mid}PositiveOffset',
                               distance=offset_distance, constructionHistory=False)[0]
    crv_neg = cmds.offsetCurve(crv_mid, name=f'{crv_mid}NegativeOffset',
                               distance=-offset_distance, constructionHistory=False)[0]
    crv_pos = Node(crv_pos)
    crv_neg = Node(crv_neg)

    loft_parameters = {}
    if surface_name and isinstance(surface_name, str):
        loft_parameters["name"] = surface_name

    lofted_surface = cmds.loft(crv_pos, crv_neg,
                               range=True,
                               autoReverse=True,
                               degree=degree,
                               uniform=True,
                               constructionHistory=False,
                               **loft_parameters)[0]
    cmds.delete([crv_mid, crv_pos, crv_neg])
    return lofted_surface


def multiply_surface_spans(input_surface, u_multiplier=0, v_multiplier=0, u_degree=None, v_degree=None):
    """
    Multiplies the number of spans in the U and V directions of a NURBS surface.
    This operation deletes the history of the object before running.

    Args:
        input_surface (str, Node): The name of the NURBS surface to be modified. (can be the shape or its transform)
        u_multiplier (int): Multiplier for the number of spans in the U direction. Default is 0.
        v_multiplier (int): Multiplier for the number of spans in the V direction. Default is 0.
        u_degree (int): Degree of the surface in the U direction.
        v_degree (int): Degree of the surface in the V direction.

    Returns:
        str or None: The name of the affected surface, otherwise None.

    Example:
        multiply_surface_spans("myNurbsSurface", u_multiplier=0, v_multiplier=3, u_degree=3, v_degree=3)
    """
    # Check existence
    if not input_surface or not cmds.objExists(input_surface):
        logger.debug(f'Unable to multiply surface division. Missing provided surface.')
        return
    # Check if the provided surface is a transform
    if cmds.objectType(input_surface) == 'transform':
        # If it's a transform, get the associated shape node
        shapes = cmds.listRelatives(input_surface, shapes=True, typ=SURFACE_TYPE)
        if shapes:
            input_surface = shapes[0]
        else:
            logger.debug(f'Unable to multiply surface division. '
                         f'No "nurbsSurface" found in the provided transform.')
            return

    # Get the number of spans in the U and V directions. 0 is ignored.
    num_spans_u = cmds.getAttr(f"{input_surface}.spansU")*u_multiplier
    num_spans_v = cmds.getAttr(f"{input_surface}.spansV")*v_multiplier

    # Prepare parameters and rebuild
    degree_params = {}
    if u_degree and isinstance(u_degree, int):
        degree_params["degreeU"] = u_degree
    if v_degree and isinstance(v_degree, int):
        degree_params["degreeV"] = v_degree
    surface = cmds.rebuildSurface(input_surface, spansU=num_spans_u, spansV=num_spans_v, **degree_params)
    if surface:
        return surface[0]


def create_follicle(input_surface, uv_position=(0.5, 0.5), name=None):
    """
    Creates a follicle and attaches it to a surface.
    Args:
        input_surface (str): A path to a surface transform or shape.
        uv_position (tuple, optional): A UV values to determine where to initially position the follicle.
                                      Default is (0.5, 0.5), which is the center of the surface.
        name (str, optional): Follicle name. If not provided it will be named "follicle"
    Returns:
        tuple: A tuple where the first object is the follicle transform and the second the follicle shape.
    """
    # If it's a transform, get the associated shape node
    if cmds.objectType(input_surface) == 'transform':
        shapes = cmds.listRelatives(input_surface, shapes=True, typ=SURFACE_TYPE)
        if shapes:
            input_surface = shapes[0]
        else:
            logger.debug(f'Unable create follicle. '
                         f'No "nurbsSurface" found in the provided transform.')
            return
    if cmds.objectType(input_surface) != SURFACE_TYPE:
        logger.debug(f'Unable create follicle. '
                     f'The provided input surface is not a {SURFACE_TYPE}.')
        return
    if not name:
        name = "follicle"
    _follicle = Node(cmds.createNode("follicle"))
    _follicle_transform = Node(cmds.listRelatives(_follicle, p=True, fullPath=True)[0])
    _follicle_transform.rename(name)

    # Connect Follicle to Transforms
    cmds.connectAttr(f"{_follicle}.outTranslate", f"{_follicle_transform}.translate")
    cmds.connectAttr(f"{_follicle}.outRotate", f"{_follicle_transform}.rotate")

    # Attach Follicle to Surface
    cmds.connectAttr(f"{input_surface}.worldMatrix[0]", f"{_follicle}.inputWorldMatrix")
    cmds.connectAttr(f"{input_surface}.local", f"{_follicle}.inputSurface")

    cmds.setAttr(f'{_follicle}.parameterU', uv_position[0])
    cmds.setAttr(f'{_follicle}.parameterV', uv_position[1])

    return _follicle_transform, _follicle


def get_closest_uv_point(surface, xyz_pos=(0, 0, 0)):
    """
    Returns UV coordinates of the closest point on surface according to provided XYZ position.

    Args:
        surface (str): Surface to get the closest point.
        xyz_pos (optional, tuple, list): World Position to check against surface. Defaults is origin (0,0,0)
    Returns:
        tuple: The (u, v) coordinates of the closest point on the surface.
    """
    # Get MPoint world position
    point = OpenMaya.MPoint(xyz_pos[0], xyz_pos[1], xyz_pos[2], 1.0)

    # Get Surface Fn
    surf_fn = get_surface_function_set(surface)

    # Get uCoord and vCoord pointer objects
    u_coord = OpenMaya.MScriptUtil()
    u_coord.createFromDouble(0.0)
    u_coord_ptr = u_coord.asDoublePtr()
    v_coord = OpenMaya.MScriptUtil()
    v_coord.createFromDouble(0.0)
    v_coord_ptr = v_coord.asDoublePtr()

    # Get the closest coordinate to edit point position
    # Parameters: toThisPoint, paramU, paramV, ignoreTrimBoundaries, tolerance, space
    surf_fn.closestPoint(point, u_coord_ptr, v_coord_ptr, True, 0.0001, OpenMaya.MSpace.kWorld)
    return OpenMaya.MScriptUtil(u_coord_ptr).asDouble(), OpenMaya.MScriptUtil(v_coord_ptr).asDouble()


class Ribbon:
    def __init__(self,
                 prefix=None,
                 surface_data=None,
                 equidistant=True,
                 num_controls=5,
                 num_joints=20,
                 add_fk=True,
                 ):
        """
        Args:
            prefix (str): The system name to be added as a prefix to the created nodes.
                        If not provided, the name of the surface is used.
            surface_data (str, optional): The name of the surface to be used as a ribbon. (Can be its transform or shape)
                                     If not provided one will be created automatically.
            equidistant (int, optional): Determine if the controls should be equally spaced (True) or not (False).
            num_controls (int, optional): The number of controls to create.
            num_joints (int, optional): The number of joints to create on the ribbon.
            add_fk (int): Flag to add FK controls.
        """
        self.prefix = None
        self.equidistant = True
        self.num_controls = 5
        self.num_joints = 20
        self.add_fk = add_fk
        self.dropoff_rate = 2

        # Surface Data
        self.sur_data = None
        self.sur_data_sanitized = None  # Cached reference for bound objects - Internal Use Only
        self.sur_data_length = None  # When using a list, this is the length of the list. - Internal Use Only
        self.sur_spans_multiplier = 0
        self.sur_data_is_driven = False
        self.sur_data_maintain_offset = True

        # Bind Joint Data
        self.bind_joints_orient_offset = None
        self.bind_joints_parenting = True

        if prefix:
            self.set_prefix(prefix=prefix)
        if surface_data:
            self.set_surface_data(surface_data=surface_data)
        if isinstance(equidistant, bool):
            self.set_equidistant(equidistant=equidistant)
        if num_controls:
            self.set_num_controls(num_controls=num_controls)
        if num_joints:
            self.set_num_joints(num_joints=num_joints)

    def set_prefix(self, prefix):
        """
        Set the prefix attribute of the object.

        Args:
            prefix (str): The prefix to be added to the ribbon objects during the "build" process.
        """
        if not prefix or not isinstance(prefix, str):
            logger.debug('Unable to set prefix. Input must be a non-empty string.')
            return
        self.prefix = prefix

    def set_equidistant(self, equidistant):
        """
        Set the equidistant attribute of the object.

        Args:
            equidistant (bool): Determine if the controls should be equally spaced (True) or not (False).
        """
        if not isinstance(equidistant, bool):
            logger.debug('Unable to set equidistant state. Input must be a bool (True or False)')
            return
        self.equidistant = equidistant

    def set_num_controls(self, num_controls):
        """
        Set the number of controls attribute of the object.

        Args:
            num_controls (int): The number of controls to create.
        """
        if not isinstance(num_controls, int) or num_controls <= 1:
            logger.debug('Unable to set number of controls. Input must be two or more.')
            return
        self.num_controls = num_controls

    def set_num_joints(self, num_joints):
        """
        Set the number of joints attribute of the object.
        Args:
            num_joints (int): The number of joints to be set.
        """
        if not isinstance(num_joints, int) or num_joints <= 0:
            logger.debug('Unable to set number of joints. Input must be a positive integer.')
            return
        self.num_joints = num_joints

    def set_add_fk_state(self, state):
        """
        Determines if the system will create FK controls when building or not.
        Args:
            state (bool) If True, forward kinematics system will be added to the ribbon, otherwise it will be skipped.
        """
        if not isinstance(state, bool):
            logger.debug(f'Unable to set FK creation state. Input must be a boolean.')
            return
        self.add_fk = state

    def set_dropoff_rate(self, rate):
        """
        Sets the rate at which the influence of a transform drops as the distance from that transform increases.
        The valid range is between 0.1 and 10.0. - In this context, it determines the dropoff influence of the controls
        along the ribbon surface.
        Args:
            rate (int, float): Dropoff rate for the ribbon controls. Range 0.1 to 10.0
        """
        if not isinstance(rate, (int, float)):
            logger.debug(f'Unable to set dropoff rate. Invalid data type provided.')
        if 0.1 <= rate <= 10.0:
            self.dropoff_rate = rate
        else:
            logger.debug("Invalid dropoff value. The valid range is between 0.1 and 10.0.")

    def set_surface_data(self, surface_data=None, is_driven=None, maintain_driven_offset=None, span_multiplier=None):
        """
        Set the surface origin to be used as a ribbon of the object.
        Args:
            surface_data (str, list): Data used to create or connect ribbon surface.
                              If a string is provided, it should be the transform or shape of a nurbs surface.
                              If a list of objects or positions is used, a surface will be created using this data.
                              The function "clear_surface_data" can be used to remove previous provided data.
            is_driven (bool, optional): If True, it will use the provided surface_data object list as driven.
                                        This means that the follicles will drive these objects directly.
                                        Commonly used with existing influence joints.
                                        e.g. follicle -> parent constraint > surface_data list item
            maintain_driven_offset (bool, optional): When True, it constrains follicles with maintain offset active.
                                                     This option is only used when "is_driven" is True.
            span_multiplier (int): New span multiplier value. Sets the span multiplier value of the generated surface.
                    That is, the number of divisions in between spans. For example, if a surface is created from
                    point A to point B and the multiplier is set to zero or one, the surface will not change, and be
                    composed only of the starting and ending spans.
                    Now if the multiplier is set to 2, the number of spans will double, essentially adding a span/edge
                    in between the initial spans. This can be seen as a subdivision value for surfaces.
        """
        if surface_data and not isinstance(surface_data, (str, list, tuple)):
            logger.debug(f'Unable to set surface path. Invalid data was provided.')
            return
        self.sur_data = surface_data
        if isinstance(is_driven, bool):
            self.sur_data_is_driven = is_driven
        if isinstance(maintain_driven_offset, bool):
            self.sur_data_maintain_offset = maintain_driven_offset
        if isinstance(span_multiplier, int):
            self.sur_spans_multiplier = span_multiplier

    def clear_surface_data(self):
        """
        Removes/Clears the currently surface data and its attributes.
        This will cause the ribbon to create a new one during the "build" process.
        """
        self.sur_data = None
        _default_ribbon = Ribbon()  # Temporary ribbon used to extract default values
        self.sur_data_is_driven = _default_ribbon.sur_data_is_driven
        self.sur_data_maintain_offset = _default_ribbon.sur_data_maintain_offset
        self.sur_spans_multiplier = _default_ribbon.sur_spans_multiplier

    def set_bind_joint_data(self, orient_offset=None, parenting=None):
        """
        Sets data related to the bind joints. These are only applied when the ribbon is creating the joints.

        Args:
            orient_offset (tuple, optional): An offset tuple with the X, Y, and Z rotation values.
                                             Sets an orientation offset (rotation) for the bind joints.
                                             Helpful for when matching orientation.
                                             e.g. (90, 0, 0) will use "Z" as primary rotation.
            parenting (bool, optional): Determines if the joints should form a hierarchy by parenting them to one
                                        another in the order of creation.
        """
        if isinstance(parenting, bool):
            self.bind_joints_parenting = parenting
        if orient_offset:
            if not isinstance(orient_offset, tuple) or len(orient_offset) < 3:
                logger.debug(f'Unable to set bind joint orient offset. '
                             f'Invalid input. Must be a tuple with X, Y and Z values.')
                return

            if not all(isinstance(num, (int, float)) for num in orient_offset):
                logger.debug(f'Unable to set bind joint orient offset. '
                             f'Input must contain only numbers.')
                return
            self.bind_joints_orient_offset = orient_offset

    def clear_bind_joint_data(self):
        """
        Removes/Clears the bind data by reverting them back to the default values.
        This will cause the ribbon to create a new one during the "build" process.
        """
        _default_ribbon = Ribbon()  # Temporary ribbon used to extract default values
        self.bind_joints_orient_offset = _default_ribbon.bind_joints_orient_offset
        self.bind_joints_parenting = _default_ribbon.bind_joints_parenting

    def _get_or_create_surface(self, prefix):
        """
        Gets or creates the surface used for the ribbon.
        The operation depends on the data stored in the "surface_data" variables.
        If empty, it will create a simple 1x24 surface to match the default size of the grid.
        If a path (string) is provided, it will use it as the surface, essentially using an existing surface.
        If a list of paths (strings) is provided, it will use the position of the objects to create a surface.
        If a list positions (3d tuples or lists) is provided, it will use the data to create a surface.

        This function will also update the "surface_data_length" according to the data found.
        No data = None.
        Path = None.
        List of paths = Length of the existing objects.
        List of positions = Length of the positions list.

        Args:
            prefix (str): Prefix to be added in front of the generated surface.
                          If an existing surface is found, this value is ignored.
        Returns:
            str: The surface name (path)
        """
        self.sur_data_length = None
        if isinstance(self.sur_data, str) and cmds.objExists(self.sur_data):
            return self.sur_data
        if isinstance(self.sur_data, (list, tuple)):
            # Object List
            _filter_obj_list = filter_list_by_type(self.sur_data, data_type=(str, Node))
            if _filter_obj_list:
                _obj_list = sanitize_maya_list(input_list=self.sur_data, sort_list=False,
                                               filter_unique=False, reverse_list=True)
                if not _obj_list or len(_obj_list) < 2:
                    logger.warning(f'Unable to create surface using object list. '
                                   f'At least two valid objects are necessary for this operation.')
                else:
                    self.sur_data_length = len(_obj_list)
                    self.sur_data_sanitized = _obj_list[::-1]  # Reversed
                    _sur = create_surface_from_object_list(obj_list=_obj_list, surface_name=f"{prefix}ribbon_sur")
                    multiply_surface_spans(input_surface=_sur, u_degree=1, v_degree=3,
                                           v_multiplier=self.sur_spans_multiplier)
                    return _sur
            # Position List
            _filter_pos_list = filter_list_by_type(self.sur_data, data_type=(list, tuple), num_items=3)
            if _filter_pos_list:
                obj_list_locator = []
                for pos in self.sur_data:
                    locator_name = cmds.spaceLocator(name=f'{prefix}_temp_surface_assembly_locator')[0]
                    cmds.move(*pos, locator_name)
                    obj_list_locator.append(locator_name)
                obj_list_locator.reverse()
                self.sur_data_length = len(obj_list_locator)
                _sur = create_surface_from_object_list(obj_list=obj_list_locator,
                                                       surface_name=f"{prefix}_ribbon_sur")
                multiply_surface_spans(input_surface=_sur, v_multiplier=self.sur_spans_multiplier, v_degree=3)
                cmds.delete(obj_list_locator)
                return _sur

        surface = cmds.nurbsPlane(axis=(0, 1, 0), width=1, lengthRatio=24, degree=3,
                                  patchesU=1, patchesV=10, constructionHistory=False)[0]
        surface = cmds.rename(surface, f"{prefix}ribbon_sur")
        return surface

    def build(self):
        """
        Build a ribbon rig.
        """
        num_controls = self.num_controls
        num_joints = self.num_joints

        # Determine Prefix
        if not self.prefix:
            prefix = f''
        else:
            prefix = f'{self.prefix}_'

        # Create Surface in case not provided or missing
        input_surface = self._get_or_create_surface(prefix=prefix)
        input_surface = Node(input_surface)

        # Determine Surface Transform and Shape
        surface_shape = None
        if cmds.objectType(input_surface) == "transform":
            surface_shape = cmds.listRelatives(input_surface, shapes=True, fullPath=True)[0]
            surface_shape = Node(surface_shape)
        if cmds.objectType(input_surface) == SURFACE_TYPE:
            surface_shape = Node(input_surface)
            input_surface = cmds.listRelatives(surface_shape, parent=True, fullPath=True)[0]
            input_surface = Node(input_surface)
        cmds.delete(input_surface, constructionHistory=True)

        if not surface_shape:
            logger.warning(f'Unable to create ribbon. Failed to get or create surface.')
            return

        # Determine Direction ----------------------------------------------------------------------------
        u_curve = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)  # (.5 = center)
        v_curve = cmds.duplicateCurve(f'{input_surface}.u[.5]', local=True, ch=0)
        u_length = cmds.arclen(u_curve)
        v_length = cmds.arclen(v_curve)

        if u_length < v_length:
            cmds.reverseSurface(input_surface, direction=3, ch=False, replaceOriginal=True)
            cmds.reverseSurface(input_surface, direction=0, ch=False, replaceOriginal=True)

        u_curve_for_positions = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)[0]

        # U Positions
        is_periodic = is_surface_periodic(surface_shape=str(surface_shape))
        u_position_ctrls = get_positions_from_curve(curve=u_curve_for_positions, count=num_controls,
                                                    periodic=is_periodic, space="uv")
        u_position_joints = get_positions_from_curve(curve=u_curve_for_positions, count=num_joints,
                                                     periodic=is_periodic, space="uv")
        length = cmds.arclen(u_curve_for_positions)
        cmds.delete(u_curve, v_curve, u_curve_for_positions)

        # Determine positions when using list as input
        if self.sur_data_length:
            _num_joints = self.sur_data_length - 1
            _num_joints_multiplied = 0
            if self.sur_spans_multiplier and not self.sur_data_is_driven:
                _num_joints_multiplied = _num_joints*self.sur_spans_multiplier  # Account for new spans
            _num_joints = _num_joints  # -1 to remove end span
            u_pos_value = 1/_num_joints

            last_value = 0
            u_position_joints = []
            for index in range(_num_joints):
                u_position_joints.append(last_value)
                last_value = last_value+u_pos_value
            u_position_joints.append(1)  # End Position: 0=start, 1=end

        # Organization/Groups ----------------------------------------------------------------------------
        grp_suffix = NamingConstants.Suffix.GRP
        parent_group = cmds.group(name=f"{prefix}ribbon_{grp_suffix}", empty=True)
        parent_group = Node(parent_group)
        driver_joints_grp = cmds.group(name=f"{prefix}driver_joints_{grp_suffix}", empty=True)
        driver_joints_grp = Node(driver_joints_grp)
        control_grp = cmds.group(name=f"{prefix}controls_{grp_suffix}", empty=True)
        control_grp = Node(control_grp)
        follicles_grp = cmds.group(name=f"{prefix}follicles_{grp_suffix}", empty=True)
        follicles_grp = Node(follicles_grp)
        bind_grp = cmds.group(name=f"{prefix}bind_{grp_suffix}", empty=True)
        bind_grp = Node(bind_grp)
        setup_grp = cmds.group(name=f"{prefix}setup_{grp_suffix}", empty=True)
        setup_grp = Node(setup_grp)
        ribbon_crv = get_curve("_pin_pos_z")
        ribbon_crv.set_name(f"{prefix}base_{NamingConstants.Suffix.CTRL}")
        ribbon_ctrl = ribbon_crv.build()
        ribbon_ctrl = Node(ribbon_ctrl)
        rescale_curve(curve_transform=str(ribbon_ctrl), scale=length/10)
        ribbon_offset = cmds.group(name=f"{prefix}ctrl_main_offset", empty=True)
        ribbon_offset = Node(ribbon_offset)

        hierarchy_utils.parent(source_objects=ribbon_ctrl, target_parent=ribbon_offset)
        hierarchy_utils.parent(source_objects=control_grp, target_parent=ribbon_ctrl)
        hierarchy_utils.parent(source_objects=[ribbon_offset, bind_grp, setup_grp],
                               target_parent=parent_group)
        hierarchy_utils.parent(source_objects=[input_surface, driver_joints_grp, follicles_grp],
                               target_parent=setup_grp)
        cmds.setAttr(f"{setup_grp}.visibility", 0)

        # Follicles and Bind Joints ----------------------------------------------------------------------
        follicle_nodes = []
        follicle_transforms = []
        bind_joints = []
        bind_joint_radius = (length/60)/(float(num_joints)/40)

        for index in range(len(u_position_joints)):
            _fol_tuple = create_follicle(input_surface=str(surface_shape),
                                         uv_position=(u_position_joints[index], 0.5),
                                         name=f"{prefix}follicle_{(index+1):02d}")

            _follicle_transform = _fol_tuple[0]
            _follicle_shape = _fol_tuple[1]
            follicle_transforms.append(_follicle_transform)
            follicle_nodes.append(_follicle_shape)

            cmds.parent(_follicle_transform, follicles_grp)

            # Driven List (Follicles drive surface_data source object list)
            if self.sur_data_is_driven:
                cmds.parentConstraint(_follicle_transform, self.sur_data_sanitized[index],
                                      maintainOffset=self.sur_data_maintain_offset)
                continue

            # Bind Joint (Creation)
            if prefix:
                joint_name = f"{prefix}{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            else:
                joint_name = f"bind_{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            joint = cmds.createNode("joint", name=joint_name)
            joint = Node(joint)
            bind_joints.append(joint)

            # Constraint Joint
            match_transform(source=_follicle_transform, target_list=joint)
            if self.bind_joints_orient_offset:
                cmds.rotate(*self.bind_joints_orient_offset, joint, relative=True, os=True)
            cmds.parentConstraint(_follicle_transform, joint, maintainOffset=True)
            cmds.setAttr(f"{joint}.radius", bind_joint_radius)

        if follicle_transforms:
            match_transform(source=follicle_transforms[0], target_list=ribbon_offset)
        else:
            bbox_center = get_bbox_position(input_surface)
            set_trs_attr(target_obj=ribbon_offset, value_tuple=bbox_center, translate=True)
        hierarchy_utils.parent(source_objects=bind_joints, target_parent=bind_grp)

        # Ribbon Controls ---------------------------------------------------------------------------------
        ctrl_ref_follicle_nodes = []
        ctrl_ref_follicle_transforms = []

        for index in range(num_controls):
            _follicle_shape = Node(cmds.createNode("follicle"))
            _follicle_transform = cmds.listRelatives(_follicle_shape, parent=True)[0]
            ctrl_ref_follicle_nodes.append(_follicle_shape)
            ctrl_ref_follicle_transforms.append(_follicle_transform)

            cmds.connectAttr(f"{_follicle_shape}.outTranslate", f"{_follicle_transform}.translate")
            cmds.connectAttr(f"{_follicle_shape}.outRotate", f"{_follicle_transform}.rotate")
            cmds.connectAttr(f"{surface_shape}.worldMatrix[0]", f"{_follicle_shape}.inputWorldMatrix")
            cmds.connectAttr(f"{surface_shape}.local", f"{_follicle_shape}.inputSurface")

        divider_for_ctrls = num_controls
        if not is_periodic:
            divider_for_ctrls = num_controls-1
        if self.equidistant:
            for index, _follicle_transform in enumerate(ctrl_ref_follicle_nodes):
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_position_ctrls[index])
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
        else:
            u_pos = 0
            for _follicle_transform in ctrl_ref_follicle_nodes:
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_pos)
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
                u_pos = u_pos + (1.0 / divider_for_ctrls)

        ik_ctrl_scale = (length / 35) / (float(num_controls) / 5)  # TODO TEMP @@@
        ribbon_ctrls = []

        ctrl_offset_grps = []
        ctrl_joints = []
        ctrl_jnt_offset_grps = []
        ctrl_jnt_radius = bind_joint_radius * 1

        for index in range(num_controls):
            crv = get_curve("_cube")
            ctrl = Node(crv.build())
            ctrl.rename(f"{prefix}{NamingConstants.Suffix.CTRL}_{(index+1):02d}")
            scale = ((length/3)/num_controls, 1, 1)

            rescale_curve(curve_transform=ctrl, scale=scale)

            ribbon_ctrls.append(ctrl)

            ctrl_offset_grp = cmds.group(name=f"{ctrl.get_short_name()}_offset", empty=True)
            ctrl_offset_grp = Node(ctrl_offset_grp)
            hierarchy_utils.parent(source_objects=ctrl, target_parent=ctrl_offset_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_offset_grp)
            ctrl_offset_grps.append(ctrl_offset_grp)

            # Ribbon Driver Joint
            joint = cmds.createNode("joint", name=f'{prefix}driver_{(index+1):02d}_{NamingConstants.Suffix.JNT}')
            joint = Node(joint)
            ctrl_joints.append(joint)
            cmds.setAttr(f"{ctrl_joints[index]}.radius", ctrl_jnt_radius)
            ctrl_jnt_ofs_grp = cmds.group(name=f"{joint}_offset", empty=True)
            ctrl_jnt_ofs_grp = Node(ctrl_jnt_ofs_grp)
            hierarchy_utils.parent(source_objects=joint, target_parent=ctrl_jnt_ofs_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_jnt_ofs_grp)
            ctrl_jnt_offset_grps.append(ctrl_jnt_ofs_grp)

        hierarchy_utils.parent(source_objects=ctrl_offset_grps, target_parent=control_grp)
        hierarchy_utils.parent(source_objects=ctrl_jnt_offset_grps, target_parent=driver_joints_grp)

        hide_lock_default_attrs(obj_list=ctrl_offset_grps + ctrl_jnt_offset_grps,
                                translate=True, rotate=True, scale=True, visibility=False)

        cmds.delete(ctrl_ref_follicle_transforms)

        for (control, joint) in zip(ribbon_ctrls, ctrl_joints):
            cmds.parentConstraint(control, joint)
            cmds.scaleConstraint(control, joint)

        # Follicle Scale
        for fol in follicle_transforms:
            cmds.scaleConstraint(ribbon_ctrl, fol)

        # Bind the surface to driver joints
        nurbs_skin_cluster = cmds.skinCluster(ctrl_joints, input_surface,
                                              dropoffRate=self.dropoff_rate,
                                              maximumInfluences=num_controls-1,
                                              nurbsSamples=num_controls*5,
                                              bindMethod=0,  # Closest Distance
                                              name=f"{prefix}skinCluster")[0]
        cmds.skinPercent(nurbs_skin_cluster, input_surface, pruneWeights=0.2)

        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sy")
        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_ctrl}.sx")

        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sy")
        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_offset}.sx")

        # FK Controls ---------------------------------------------------------------------------------------
        fk_ctrls = []
        if self.add_fk and is_periodic:
            logger.warning(f'Unable to add FK controls. Input surface is periodic.')
        elif self.add_fk and not is_periodic:
            fk_offset_groups = []
            crv_obj = get_curve("_circle_pos_x")
            for index in range(1, num_controls):
                _ctrl = Node(crv_obj.build())
                _ctrl.rename(f'{prefix}fk_{index:02d}_ctrl')
                _offset = Node(cmds.group(name=f'{prefix}fk_{index:02d}_offset', empty=True))
                fk_ctrls.append(_ctrl)
                fk_offset_groups.append(_offset)
                cmds.parent(_ctrl, _offset)

            for (offset, ctrl) in zip(fk_offset_groups[1:], fk_ctrls[:-1]):
                cmds.parent(offset, ctrl)

            cmds.parent(fk_offset_groups[0], control_grp)

            # Re-scale FK controls
            fk_ctrl_scale = ik_ctrl_scale*2
            for fk_ctrl in fk_ctrls:
                rescale_curve(curve_transform=fk_ctrl, scale=fk_ctrl_scale)

            ik_offset_grps = [cmds.group(ctrl, name=f"{ctrl.get_short_name()}_offset_grp") for ctrl in ribbon_ctrls]
            [cmds.xform(ik_ctrl_offset_grp, piv=(0, 0, 0), os=True) for ik_ctrl_offset_grp in ik_offset_grps]

            for ik, fk in zip(ribbon_ctrls[:-1], fk_offset_groups):
                cmds.delete(cmds.parentConstraint(ik, fk))

            for fk, ik in zip(fk_ctrls, ik_offset_grps[:-1]):
                cmds.parentConstraint(fk, ik)

            # Constrain Last Ctrl
            cmds.parentConstraint(fk_ctrls[-1], ik_offset_grps[-1], mo=True)

            set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RigControl.TWEAK)
            hide_lock_default_attrs(fk_offset_groups, translate=True, rotate=True, scale=True)

            cmds.select(cl=True)

        # Parenting Binding Joints
        if self.bind_joints_parenting:
            for index in range(len(bind_joints) - 1):
                parent_joint = bind_joints[index]
                child_joint = bind_joints[index + 1]
                if cmds.objExists(parent_joint) and cmds.objExists(child_joint):
                    cmds.parent(child_joint, parent_joint)

        # Colors  ------------------------------------------------------------------------------------------
        set_color_viewport(obj_list=ribbon_ctrl, rgb_color=ColorConstants.RGB.WHITE)
        set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RGB.RED_INDIAN)
        set_color_viewport(obj_list=ribbon_ctrls, rgb_color=ColorConstants.RGB.BLUE_SKY)
        set_color_viewport(obj_list=bind_joints, rgb_color=ColorConstants.RGB.YELLOW)

        # Clean-up  ----------------------------------------------------------------------------------------
        # Delete Empty Bind Group
        bind_grp_children = cmds.listRelatives(bind_grp, children=True)
        if not bind_grp_children:
            cmds.delete(bind_grp)
        # Clear selection
        cmds.select(cl=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Clear Scene
    cmds.file(new=True, force=True)
    # Create Test Joints
    test_joints = [cmds.joint(p=(0, 0, 0)),
                   cmds.joint(p=(-5, 0, 0)),
                   cmds.joint(p=(-10, 2, 0)),
                   cmds.joint(p=(-15, 6, 3)),
                   cmds.joint(p=(-20, 10, 5)),
                   cmds.joint(p=(-25, 15, 10)),
                   cmds.joint(p=(-30, 15, 15))]

    from gt.utils.control_utils import create_fk
    test_fk_ctrls = create_fk(target_list=test_joints, constraint_joint=False)
    # Create Ribbon
    ribbon_factory = Ribbon(equidistant=True,
                            num_controls=5,
                            num_joints=8,
                            add_fk=True)
    ribbon_factory.set_surface_data("mocked_sur")
    ribbon_factory.set_prefix("mocked")
    ribbon_factory.set_surface_data(surface_data=test_joints, is_driven=True)
    # ribbon_factory.set_dropoff_rate(2)
    # ribbon_factory.set_num_controls(9)
    # ribbon_factory.set_surface_span_multiplier(10)
    # ribbon_factory.set_surface_data([(0, 0, 0), (5, 0, 0), (10, 0, 0)])
    # print(ribbon_factory._get_or_create_surface(prefix="test"))
    ribbon_factory.build()
    cmds.viewFit(all=True)
