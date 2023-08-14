"""
Work in Progress file
"""
import maya.cmds as cmds
from gt.utils.data.controls import CRV_SUFFIX
from gt.utils.curve_utils import combine_curves_list


def create_finger_curl_ctrl(ctrl_name, parent='world', scale_multiplier=1, x_offset=0, z_offset=0):
    """
    Creates a finger curl control. This function was made for a very specific use, so it already orients the control
    accordingly.

    Args:
        ctrl_name (string) : Name of the control (thumb, index, middle, ring, pinky)
        parent (optional, string) : Name of the parent object. If not provided, it will be left in the world.
        scale_multiplier (optional, float) : Number to multiply when scaling it.
        x_offset (optional, float) : Number to multiply the scale offset into X
        z_offset (optional, float) : Number to multiply the scale offset into Z

    Returns:
        curl_ctrl (string) : Name of the generated curl ctrl.
    """
    finger_curl_a = cmds.curve(name=ctrl_name, p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449],
                                                  [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34],
                                                  [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33],
                                                  [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33],
                                                  [0.129, 0.347, -0.368], [0.091, 0.311, -0.402],
                                                  [0.062, 0.269, -0.429], [0.062, 0.269, -0.429],
                                                  [0.062, 0.269, -0.429], [0.062, 0.454, -0.268], [0.062, 0.519, 0.024],
                                                  [0.062, 0.445, 0.232], [0.062, 0.355, 0.343], [0.062, 0.224, 0.445],
                                                  [0.062, 0.0, 0.509], [0.062, -0.224, 0.445], [0.062, -0.355, 0.343],
                                                  [0.062, -0.445, 0.232], [0.062, -0.519, 0.024],
                                                  [0.062, -0.454, -0.268], [0.062, -0.269, -0.429],
                                                  [0.062, -0.269, -0.429], [0.062, -0.269, -0.429],
                                                  [0.091, -0.311, -0.402], [0.129, -0.347, -0.368],
                                                  [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33],
                                                  [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34],
                                                  [0.204, -0.364, -0.34], [0.158, -0.332, -0.383],
                                                  [0.123, -0.292, -0.418], [0.079, -0.237, -0.449],
                                                  [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    finger_curl_b = cmds.curve(name=ctrl_name + '_tempShape_b',
                               p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449],
                                  [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34],
                                  [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33],
                                  [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33],
                                  [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429],
                                  [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268],
                                  [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343],
                                  [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445],
                                  [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024],
                                  [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429],
                                  [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368],
                                  [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33],
                                  [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34],
                                  [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418],
                                  [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    finger_curl_ctrl = combine_curves_list([finger_curl_a, finger_curl_b])
    shapes = cmds.listRelatives(finger_curl_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow_l'))
    cmds.rename(shapes[1], '{0}Shape'.format('arrow_r'))
    cmds.setAttr(finger_curl_ctrl + '.rotateY', -90)
    cmds.setAttr(finger_curl_ctrl + '.scaleX', scale_multiplier * .1)
    cmds.setAttr(finger_curl_ctrl + '.scaleY', scale_multiplier * .1)
    cmds.setAttr(finger_curl_ctrl + '.scaleZ', scale_multiplier * .1)
    cmds.makeIdentity(finger_curl_ctrl, apply=True, scale=True, rotate=True)
    if parent != 'world':
        cmds.parent(finger_curl_ctrl, parent)

    cmds.move(scale_multiplier * z_offset, finger_curl_ctrl, z=True, relative=True, objectSpace=True)
    cmds.move(scale_multiplier * x_offset, finger_curl_ctrl, x=True, relative=True, objectSpace=True)
    return finger_curl_ctrl


def create_slider_control(name, initial_position='middle', lock_unused_channels=True):
    """

    Args:
        name:  Object name (string)
        initial_position:  "middle", "top" or "bottom" (string)
        lock_unused_channels:  locks and hides unused channels (TX, TZ, ROT...)

    Returns:
        ctrl_elements: A list with the control name and control group name
    """
    default_ctrl_line_width = 3

    # Validate Name
    if not name:
        cmds.warning('Control name cannot be empty')
        return

    # Create Elements
    ctrl = cmds.curve(name=name,
                      p=[[-1.0, -1.0, 0.0], [-1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]],
                      d=1)
    ctrl_bg = cmds.curve(name=name + '_bg_' + CRV_SUFFIX,
                         p=[[-1.0, -6.0, 0.0], [-1.0, 6.0, 0.0], [1.0, 6.0, 0.0], [1.0, -6.0, 0.0], [-1.0, -6.0, 0.0]],
                         d=1)
    ctrl_grp = cmds.group(name=ctrl + GRP_SUFFIX.capitalize(), world=True, empty=True)
    cmds.parent(ctrl, ctrl_grp)
    cmds.parent(ctrl_bg, ctrl_grp)

    # Handle Shape
    shape = ''
    for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, '{0}Shape'.format(name))

    # Determine initial position
    if initial_position.lower() == 'top':
        cmds.setAttr(ctrl + '.ty', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 0)
        cmds.setAttr(ctrl + '.minTransYLimit', -10)
    elif initial_position.lower() == 'bottom':
        cmds.setAttr(ctrl + '.ty', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 10)
        cmds.setAttr(ctrl + '.minTransYLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransYLimit', 5)
        cmds.setAttr(ctrl + '.minTransYLimit', -5)

    # Determine Look
    cmds.setAttr(shape + '.lineWidth', default_ctrl_line_width)
    cmds.setAttr(ctrl_bg + '.overrideEnabled', 1)
    cmds.setAttr(ctrl_bg + '.overrideDisplayType', 2)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransYLimitEnable', 1)

    if lock_unused_channels:
        axis = ['x', 'y', 'z']
        attrs = ['t', 'r', 's']
        for ax in axis:
            for attr in attrs:
                if (attr + ax) != 'ty':
                    cmds.setAttr(ctrl + '.' + attr + ax, lock=True, k=False, channelBox=False)
        cmds.setAttr(ctrl + '.v', lock=True, k=False, channelBox=False)

    return [ctrl, ctrl_grp]


def create_2d_slider_control(name, initial_position_y='middle', initial_position_x='middle',
                             lock_unused_channels=True, ignore_range=None):
    """

    Args:
        name:  Object name (string)
        initial_position_y:  "middle", "top" or "bottom" (string)
        initial_position_x:  "middle", "right" or "left" (string)
        lock_unused_channels:  locks and hides unused channels (TX, TZ, ROT...)
        ignore_range: "right", "left", "bottom" or "up". 2D Area to be ignored and removed from the available range

    Returns:
        ctrl_elements: A list with the control name and control group name
    """
    default_ctrl_line_width = 3

    # Validate Name
    if not name:
        cmds.warning('Control name cannot be empty')
        return

    # Create Elements
    ctrl = cmds.curve(name=name,
                      p=[[-1.0, -1.0, 0.0], [-1.0, 1.0, 0], [1.0, 1.0, 0], [1.0, -1.0, 0], [-1.0, -1.0, 0]],
                      d=1)
    ctrl_bg = cmds.curve(name=name + '_bg_' + CRV_SUFFIX,
                         p=[[-6.0, -6.0, 0.0], [-6.0, 6.0, 0.0], [6.0, 6.0, 0.0], [6.0, -6.0, 0.0], [-6.0, -6.0, 0.0]],
                         d=1)
    ctrl_grp = cmds.group(name=ctrl + GRP_SUFFIX.capitalize(), world=True, empty=True)
    cmds.parent(ctrl, ctrl_grp)
    cmds.parent(ctrl_bg, ctrl_grp)

    # Handle Shape
    shape = ''
    for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, '{0}Shape'.format(name))

    # Determine initial Y position
    if initial_position_y.lower() == 'top':
        cmds.setAttr(ctrl + '.ty', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 0)
        cmds.setAttr(ctrl + '.minTransYLimit', -10)
    elif initial_position_y.lower() == 'bottom':
        cmds.setAttr(ctrl + '.ty', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransYLimit', 10)
        cmds.setAttr(ctrl + '.minTransYLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransYLimit', 5)
        cmds.setAttr(ctrl + '.minTransYLimit', -5)

    # Determine initial X position
    if initial_position_x.lower() == 'right':
        cmds.setAttr(ctrl + '.tx', 5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransXLimit', 0)
        cmds.setAttr(ctrl + '.minTransXLimit', -10)
    elif initial_position_x.lower() == 'left':
        cmds.setAttr(ctrl + '.tx', -5)
        cmds.makeIdentity(ctrl, apply=True, translate=True)
        cmds.setAttr(ctrl + '.maxTransXLimit', 10)
        cmds.setAttr(ctrl + '.minTransXLimit', 0)
    else:
        cmds.setAttr(ctrl + '.maxTransXLimit', 5)
        cmds.setAttr(ctrl + '.minTransXLimit', -5)

    # Determine Look
    cmds.setAttr(shape + '.lineWidth', default_ctrl_line_width)
    cmds.setAttr(ctrl_bg + '.overrideEnabled', 1)
    cmds.setAttr(ctrl_bg + '.overrideDisplayType', 2)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransYLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransXLimitEnable', 1)
    cmds.setAttr(ctrl + '.maxTransXLimitEnable', 1)
    cmds.setAttr(ctrl + '.minTransXLimitEnable', 1)

    if lock_unused_channels:
        axis = ['x', 'y', 'z']
        attrs = ['t', 'r', 's']
        for ax in axis:
            for attr in attrs:
                if (attr + ax) != 'ty' and (attr + ax) != 'tx':
                    cmds.setAttr(ctrl + '.' + attr + ax, lock=True, k=False, channelBox=False)
        cmds.setAttr(ctrl + '.v', lock=True, k=False, channelBox=False)

    if ignore_range:
        if ignore_range == 'right':
            cmds.move(-5, ctrl_bg + '.cv[2:3]', moveX=True, relative=True)
            cmds.setAttr(ctrl + '.maxTransXLimit', 0)
        elif ignore_range == 'left':
            cmds.move(5, ctrl_bg + '.cv[0:1]', moveX=True, relative=True)
            cmds.move(5, ctrl_bg + '.cv[4]', moveX=True, relative=True)
            cmds.setAttr(ctrl + '.minTransXLimit', 0)
        elif ignore_range == 'bottom':
            cmds.move(5, ctrl_bg + '.cv[0]', moveY=True, relative=True)
            cmds.move(5, ctrl_bg + '.cv[3:4]', moveY=True, relative=True)
            cmds.setAttr(ctrl + '.minTransYLimit', 0)
        elif ignore_range == 'top':
            cmds.move(-5, ctrl_bg + '.cv[1:2]', moveY=True, relative=True)
            cmds.setAttr(ctrl + '.maxTransYLimit', 0)

    return [ctrl, ctrl_grp]


def create_mouth_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])
    """
    # Containers
    controls = []
    background = []

    # Top Label
    mouth_crv = create_text('MOUTH')
    force_center_pivot(mouth_crv)
    rescale(mouth_crv, 1.75)
    cmds.setAttr(mouth_crv + '.ty', 10.5)
    cmds.setAttr(mouth_crv + '.overrideDisplayType', 2)
    background.append(mouth_crv)

    # 1D Controls
    mid_upper_lip_ctrl = create_slider_control('mid_upperLip_offset_ctrl')
    mid_lower_lip_ctrl = create_slider_control('mid_lowerLip_offset_ctrl')
    left_upper_outer_lip_ctrl = create_slider_control('left_upperOuterLip_offset_ctrl')
    left_lower_outer_lip_ctrl = create_slider_control('left_lowerOuterLip_offset_ctrl')
    left_upper_corner_lip_ctrl = create_slider_control('left_upperCornerLip_offset_ctrl')
    left_lower_corner_lip_ctrl = create_slider_control('left_lowerCornerLip_offset_ctrl')
    right_upper_outer_lip_ctrl = create_slider_control('right_upperOuterLip_offset_ctrl')
    right_lower_outer_lip_ctrl = create_slider_control('right_lowerOuterLip_offset_ctrl')
    right_upper_corner_lip_ctrl = create_slider_control('right_upperCornerLip_offset_ctrl')
    right_lower_corner_lip_ctrl = create_slider_control('right_lowerCornerLip_offset_ctrl')
    main_mouth_offset_ctrl = create_slider_control('mainMouth_offset_ctrl')
    in_out_tongue_ctrl = create_slider_control('inOutTongue_offset_ctrl', initial_position='top')

    # TY
    cmds.setAttr(mid_upper_lip_ctrl[1] + '.ty', 6)
    cmds.setAttr(mid_lower_lip_ctrl[1] + '.ty', -5)
    cmds.setAttr(left_upper_outer_lip_ctrl[1] + '.ty', 5)
    cmds.setAttr(left_lower_outer_lip_ctrl[1] + '.ty', -4)
    cmds.setAttr(left_upper_corner_lip_ctrl[1] + '.ty', 4)
    cmds.setAttr(left_lower_corner_lip_ctrl[1] + '.ty', -3)
    cmds.setAttr(right_upper_outer_lip_ctrl[1] + '.ty', 5)
    cmds.setAttr(right_lower_outer_lip_ctrl[1] + '.ty', -4)
    cmds.setAttr(right_upper_corner_lip_ctrl[1] + '.ty', 4)
    cmds.setAttr(right_lower_corner_lip_ctrl[1] + '.ty', -3)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.tx', 13)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.ty', -13.8)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.ty', -9.5)

    # TX
    cmds.setAttr(left_upper_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_lower_outer_lip_ctrl[1] + '.tx', 2)
    cmds.setAttr(left_upper_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(left_lower_corner_lip_ctrl[1] + '.tx', 4)
    cmds.setAttr(right_upper_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_lower_outer_lip_ctrl[1] + '.tx', -2)
    cmds.setAttr(right_upper_corner_lip_ctrl[1] + '.tx', -4)
    cmds.setAttr(right_lower_corner_lip_ctrl[1] + '.tx', -4)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.tx', -13)

    # Misc
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sx', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sy', 0.8)
    cmds.setAttr(main_mouth_offset_ctrl[1] + '.sz', 0.8)
    cmds.setAttr(in_out_tongue_ctrl[1] + '.rz', 90)

    half_size_ctrls = [left_upper_outer_lip_ctrl, left_lower_outer_lip_ctrl, left_upper_corner_lip_ctrl,
                       left_lower_corner_lip_ctrl, right_upper_outer_lip_ctrl, right_lower_outer_lip_ctrl,
                       right_upper_corner_lip_ctrl, right_lower_corner_lip_ctrl, mid_upper_lip_ctrl, mid_lower_lip_ctrl,
                       in_out_tongue_ctrl]

    for ctrl in half_size_ctrls:
        cmds.setAttr(ctrl[1] + '.sx', 0.5)
        cmds.setAttr(ctrl[1] + '.sy', 0.5)
        cmds.setAttr(ctrl[1] + '.sz', 0.5)

    # 2D Controls
    left_corner_lip_ctrl = create_2d_slider_control('left_cornerLip_offset_ctrl')
    right_corner_lip_ctrl = create_2d_slider_control('right_cornerLip_offset_ctrl')
    jaw_ctrl = create_2d_slider_control('jaw_offset_ctrl')
    tongue_ctrl = create_2d_slider_control('tongue_offset_ctrl')

    # Inverted Right Controls
    cmds.setAttr(right_corner_lip_ctrl[1] + '.ry', 180)

    cmds.setAttr(left_corner_lip_ctrl[1] + '.tx', 12)
    cmds.setAttr(right_corner_lip_ctrl[1] + '.tx', -12)
    cmds.setAttr(jaw_ctrl[1] + '.ty', -15)
    rescale(tongue_ctrl[1], 0.5, freeze=False)
    cmds.setAttr(tongue_ctrl[1] + '.ty', -15)
    cmds.setAttr(tongue_ctrl[1] + '.tx', -13)

    # Determine Grp Order
    controls.append(left_corner_lip_ctrl)
    controls.append(left_upper_outer_lip_ctrl)
    controls.append(left_lower_outer_lip_ctrl)
    controls.append(left_upper_corner_lip_ctrl)
    controls.append(left_lower_corner_lip_ctrl)
    controls.append(right_corner_lip_ctrl)
    controls.append(right_upper_outer_lip_ctrl)
    controls.append(right_lower_outer_lip_ctrl)
    controls.append(right_upper_corner_lip_ctrl)
    controls.append(right_lower_corner_lip_ctrl)
    controls.append(main_mouth_offset_ctrl)
    controls.append(mid_upper_lip_ctrl)
    controls.append(mid_lower_lip_ctrl)
    controls.append(jaw_ctrl)
    controls.append(tongue_ctrl)
    controls.append(in_out_tongue_ctrl)

    # Jaw Label
    jaw_crv = create_text('JAW')
    force_center_pivot(jaw_crv)
    cmds.setAttr(jaw_crv + '.ty', -20.5)
    cmds.setAttr(jaw_crv + '.overrideDisplayType', 2)
    background.append(jaw_crv)

    # Tongue Label
    tongue_crv = create_text('TONGUE')
    force_center_pivot(tongue_crv)
    cmds.setAttr(tongue_crv + '.ty', -20.5)
    cmds.setAttr(tongue_crv + '.tx', -15)
    cmds.setAttr(tongue_crv + '.overrideDisplayType', 2)
    background.append(tongue_crv)

    # Tongue Label
    tongue_crv = create_text('UP/DOWN')
    force_center_pivot(tongue_crv)
    cmds.setAttr(tongue_crv + '.ty', -20.5)
    cmds.setAttr(tongue_crv + '.tx', 10.75)
    cmds.setAttr(tongue_crv + '.overrideDisplayType', 2)
    background.append(tongue_crv)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_mouth_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_mouth_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_mouth_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 9)
    cmds.setAttr(r_crv + '.ty', 9)
    background.append(l_crv)
    background.append(r_crv)

    # Parent Groups
    gui_grp = cmds.group(name='mouth_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='mouth_background_grp', world=True, empty=True)

    # General Background
    mouth_bg_crv = cmds.curve(name='mouth_bg_crv', p=[[-20.0, 13.0, 0.0], [-20.0, -23.0, 0.0], [20.0, -23.0, 0.0],
                                                      [20.0, 13.0, 0.0], [-20.0, 13.0, 0.0]], d=1)

    cmds.setAttr(mouth_bg_crv + '.overrideDisplayType', 1)
    background.append(mouth_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    # Final Color Adjustments
    change_viewport_color(main_mouth_offset_ctrl[0], (1, 0.35, 0.55))
    change_viewport_color(tongue_ctrl[0], (1, 0.35, 0.55))
    change_viewport_color(in_out_tongue_ctrl[0], (1, 0.35, 0.55))

    return gui_grp, controls


def create_eyebrow_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])

    """
    # Containers
    controls = []
    background = []

    # Top Label
    eyebrows_crv = create_text('EYEBROWS')
    force_center_pivot(eyebrows_crv)
    rescale(eyebrows_crv, 1.75)
    cmds.setAttr(eyebrows_crv + '.ty', 7.3)
    cmds.setAttr(eyebrows_crv + '.overrideDisplayType', 2)
    background.append(eyebrows_crv)

    # 1D Controls
    left_mid_brow_ctrl = create_slider_control('left_midBrow_offset_ctrl')
    left_outer_brow_ctrl = create_slider_control('left_outerBrow_offset_ctrl')
    right_mid_brow_ctrl = create_slider_control('right_midBrow_offset_ctrl')
    right_outer_brow_ctrl = create_slider_control('right_outerBrow_offset_ctrl')

    # TY
    cmds.setAttr(left_mid_brow_ctrl[1] + '.tx', 11)
    cmds.setAttr(left_outer_brow_ctrl[1] + '.tx', 15)
    cmds.setAttr(right_mid_brow_ctrl[1] + '.tx', -11)
    cmds.setAttr(right_outer_brow_ctrl[1] + '.tx', -15)

    left_inner_brow_ctrl = create_2d_slider_control('left_innerBrow_offset_ctrl', ignore_range='right')
    right_inner_brow_ctrl = create_2d_slider_control('right_innerBrow_offset_ctrl', ignore_range='right')

    # Invert Right Side
    cmds.setAttr(right_inner_brow_ctrl[1] + '.ry', 180)

    cmds.setAttr(left_inner_brow_ctrl[1] + '.tx', 7)
    cmds.setAttr(right_inner_brow_ctrl[1] + '.tx', -7)

    # Determine Grp Order
    controls.append(left_inner_brow_ctrl)
    controls.append(left_mid_brow_ctrl)
    controls.append(left_outer_brow_ctrl)
    controls.append(right_inner_brow_ctrl)
    controls.append(right_mid_brow_ctrl)
    controls.append(right_outer_brow_ctrl)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_eyebrow_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_eyebrow_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_eyebrow_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 7.3)
    cmds.setAttr(r_crv + '.ty', 7.3)
    cmds.setAttr(l_crv + '.tx', 3)
    cmds.setAttr(r_crv + '.tx', -3)
    background.append(l_crv)
    background.append(r_crv)

    # Parent Groups
    gui_grp = cmds.group(name='eyebrow_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='eyebrow_background_grp', world=True, empty=True)

    # General Background
    eyebrow_bg_crv = cmds.curve(name='eyebrow_bg_crv', p=[[-20.0, 10.0, 0.0], [-20.0, -8.0, 0.0], [20.0, -8.0, 0.0],
                                                          [20.0, 10.0, 0.0], [-20.0, 10.0, 0.0]], d=1)

    cmds.setAttr(eyebrow_bg_crv + '.overrideDisplayType', 1)
    background.append(eyebrow_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    return gui_grp, controls


def create_cheek_nose_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])

    """
    # Containers
    controls = []
    background = []

    # Top Label
    nose_cheek_crv = create_text('NOSE / CHEEK')
    left_nose_crv = create_text('LEFT NOSE')
    right_nose_crv = create_text('RIGHT NOSE')
    left_cheek_in_out_crv = create_text('IN/OUT')
    right_cheek_in_out_crv = create_text('IN/OUT')
    force_center_pivot(nose_cheek_crv)
    rescale(nose_cheek_crv, 1.75)
    cmds.setAttr(nose_cheek_crv + '.ty', 7.3)
    for ctrl in [nose_cheek_crv, left_nose_crv, right_nose_crv, left_cheek_in_out_crv, right_cheek_in_out_crv]:
        cmds.setAttr(ctrl + '.overrideDisplayType', 2)
    background.append(nose_cheek_crv)
    background.append(left_nose_crv)
    background.append(right_nose_crv)
    background.append(left_cheek_in_out_crv)
    background.append(right_cheek_in_out_crv)

    # 1D Controls
    left_cheek_in_out_ctrl = create_slider_control('left_cheek_in_out_offset_ctrl')
    right_cheek_in_out_ctrl = create_slider_control('right_cheek_in_out_offset_ctrl')

    # 2D Controls
    left_cheek_ctrl = create_2d_slider_control('left_cheek_offset_ctrl')
    right_cheek_ctrl = create_2d_slider_control('right_cheek_offset_ctrl')
    left_nose_ctrl = create_2d_slider_control('left_nose_offset_ctrl')
    right_nose_ctrl = create_2d_slider_control('right_nose_offset_ctrl')
    main_nose_ctrl = create_2d_slider_control('main_nose_offset_ctrl')

    # Reposition / Rescale BG
    left_nose_crv_tx = 0.05
    right_nose_crv_tx = -5.3
    nose_crv_ty = -5.56
    nose_crv_scale = .5
    cmds.setAttr(left_nose_crv + '.tx', left_nose_crv_tx)
    cmds.setAttr(right_nose_crv + '.tx', right_nose_crv_tx)
    cmds.setAttr(left_nose_crv + '.ty', nose_crv_ty)
    cmds.setAttr(right_nose_crv + '.ty', nose_crv_ty)
    rescale(left_nose_crv, nose_crv_scale, freeze=False)
    rescale(right_nose_crv, nose_crv_scale, freeze=False)

    left_cheek_in_out_crv_tx = 5.35
    right_cheek_in_out_crv_tx = -8.65
    cheek_in_out_crv_ty = -5.5
    cheek_in_out_crv_scale = .55
    cmds.setAttr(left_cheek_in_out_crv + '.tx', left_cheek_in_out_crv_tx)
    cmds.setAttr(right_cheek_in_out_crv + '.tx', right_cheek_in_out_crv_tx)
    cmds.setAttr(left_cheek_in_out_crv + '.ty', cheek_in_out_crv_ty)
    cmds.setAttr(right_cheek_in_out_crv + '.ty', cheek_in_out_crv_ty)
    rescale(left_cheek_in_out_crv, cheek_in_out_crv_scale, freeze=False)
    rescale(right_cheek_in_out_crv, cheek_in_out_crv_scale, freeze=False)

    # Reposition / Rescale Ctrls
    cheek_tx = 13.5
    cheek_ty = -1
    cheek_scale = .75
    cmds.setAttr(left_cheek_ctrl[1] + '.tx', cheek_tx)
    cmds.setAttr(right_cheek_ctrl[1] + '.tx', -cheek_tx)
    cmds.setAttr(left_cheek_ctrl[1] + '.ty', cheek_ty)
    cmds.setAttr(right_cheek_ctrl[1] + '.ty', cheek_ty)
    rescale(left_cheek_ctrl[1], cheek_scale, freeze=False)
    rescale(right_cheek_ctrl[1], cheek_scale, freeze=False)

    nose_tx = 2.5
    nose_ty = -3
    nose_scale = .25
    cmds.setAttr(left_nose_ctrl[1] + '.tx', nose_tx)
    cmds.setAttr(right_nose_ctrl[1] + '.tx', -nose_tx)
    cmds.setAttr(left_nose_ctrl[1] + '.ty', nose_ty)
    cmds.setAttr(right_nose_ctrl[1] + '.ty', nose_ty)
    rescale(left_nose_ctrl[1], nose_scale, freeze=False)
    rescale(right_nose_ctrl[1], nose_scale, freeze=False)

    cmds.setAttr(main_nose_ctrl[1] + '.ty', 1.7)
    rescale(main_nose_ctrl[1], .3, freeze=False)

    cheek_in_out_tx = 7
    cheek_in_out_ty = -.1
    cheek_in_out_scale = cheek_scale*.8
    cmds.setAttr(left_cheek_in_out_ctrl[1] + '.tx', cheek_in_out_tx)
    cmds.setAttr(right_cheek_in_out_ctrl[1] + '.tx', -cheek_in_out_tx)
    cmds.setAttr(left_cheek_in_out_ctrl[1] + '.ty', cheek_in_out_ty)
    cmds.setAttr(right_cheek_in_out_ctrl[1] + '.ty', cheek_in_out_ty)
    rescale(left_cheek_in_out_ctrl[1], cheek_in_out_scale, freeze=False)
    rescale(right_cheek_in_out_ctrl[1], cheek_in_out_scale, freeze=False)

    # Invert Right Side
    for obj in [right_cheek_ctrl, right_nose_ctrl]:
        cmds.setAttr(obj[1] + '.sx', cmds.getAttr(obj[1] + '.sx')*-1)

    # Determine Grp Order
    controls.append(left_cheek_ctrl)
    controls.append(right_cheek_ctrl)
    controls.append(left_nose_ctrl)
    controls.append(right_nose_ctrl)
    controls.append(main_nose_ctrl)
    controls.append(left_cheek_in_out_ctrl)
    controls.append(right_cheek_in_out_ctrl)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_nose_cheek_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_nose_cheek_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_nose_cheek_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 7.3)
    cmds.setAttr(r_crv + '.ty', 7.3)
    cmds.setAttr(l_crv + '.tx', 3)
    cmds.setAttr(r_crv + '.tx', -3)
    background.append(l_crv)
    background.append(r_crv)

    # Parent Groups
    gui_grp = cmds.group(name='cheek_nose_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='cheek_nose_background_grp', world=True, empty=True)

    # General Background
    eyebrow_bg_crv = cmds.curve(name='cheek_nose_bg_crv', p=[[-20.0, 10.0, 0.0], [-20.0, -8.0, 0.0], [20.0, -8.0, 0.0],
                                                             [20.0, 10.0, 0.0], [-20.0, 10.0, 0.0]], d=1)

    cmds.setAttr(eyebrow_bg_crv + '.overrideDisplayType', 1)
    background.append(eyebrow_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    return gui_grp, controls


def create_eye_controls():
    """
    Dependencies:
        rescale()
        create_slider_control()
        create_2d_slider_control()
        create_text()
        force_center_pivot()
        change_outliner_color()
        change_viewport_color()

    Returns:
        control_tuple: A tuple with the parent group name and a list with all generated controls.
                       E.g. ('eyebrow_gui_grp', ['ctrl_one', 'ctrl_two'])

    """
    # Containers
    controls = []
    background = []

    # Top Label
    eyebrows_crv = create_text('EYES')
    force_center_pivot(eyebrows_crv)
    rescale(eyebrows_crv, 1.75)
    cmds.setAttr(eyebrows_crv + '.ty', 8.6)
    cmds.setAttr(eyebrows_crv + '.overrideDisplayType', 2)
    background.append(eyebrows_crv)

    # 1D Controls
    left_upper_eyelid_ctrl = create_slider_control('left_upperEyelid_offset_ctrl')
    left_lower_eyelid_ctrl = create_slider_control('left_lowerEyelid_offset_ctrl')
    left_blink_eyelid_ctrl = create_slider_control('left_blinkEyelid_ctrl')
    right_upper_eyelid_ctrl = create_slider_control('right_upperEyelid_offset_ctrl')
    right_lower_eyelid_ctrl = create_slider_control('right_lowerEyelid_offset_ctrl')
    right_blink_eyelid_ctrl = create_slider_control('right_blinkEyelid_ctrl')

    offset_slider_range(left_upper_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(left_lower_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(left_blink_eyelid_ctrl, offset_thickness=1)
    #
    offset_slider_range(right_upper_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(right_lower_eyelid_ctrl, offset_thickness=1)
    offset_slider_range(right_blink_eyelid_ctrl, offset_thickness=1)

    # to_scale_down = [left_upper_eyelid_ctrl, left_lower_eyelid_ctrl, left_blink_eyelid_ctrl,
    #                  right_upper_eyelid_ctrl, right_lower_eyelid_ctrl, right_blink_eyelid_ctrl]
    to_scale_down = [left_blink_eyelid_ctrl, right_blink_eyelid_ctrl]
    for ctrl in to_scale_down:
        cmds.setAttr(ctrl[1] + '.sx', 0.5)
        cmds.setAttr(ctrl[1] + '.sy', 0.5)
        cmds.setAttr(ctrl[1] + '.sz', 0.5)

    # TY
    rescale(left_upper_eyelid_ctrl[1], 0.25, freeze=False)
    rescale(left_lower_eyelid_ctrl[1], 0.25, freeze=False)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.tx', 15)
    cmds.setAttr(left_upper_eyelid_ctrl[1] + '.ty', 3)
    cmds.setAttr(left_lower_eyelid_ctrl[1] + '.ty', -4)
    cmds.setAttr(left_blink_eyelid_ctrl[1] + '.tx', 5)

    rescale(right_upper_eyelid_ctrl[1], 0.25, freeze=False)
    rescale(right_lower_eyelid_ctrl[1], 0.25, freeze=False)
    cmds.setAttr(right_upper_eyelid_ctrl[1] + '.tx', -15)
    cmds.setAttr(right_lower_eyelid_ctrl[1] + '.tx', -15)
    cmds.setAttr(right_upper_eyelid_ctrl[1] + '.ty', 3)
    cmds.setAttr(right_lower_eyelid_ctrl[1] + '.ty', -4)
    cmds.setAttr(right_blink_eyelid_ctrl[1] + '.tx', -5)

    # Determine Grp Order
    controls.append(left_upper_eyelid_ctrl)
    controls.append(left_lower_eyelid_ctrl)
    controls.append(left_blink_eyelid_ctrl)
    controls.append(right_upper_eyelid_ctrl)
    controls.append(right_lower_eyelid_ctrl)
    controls.append(right_blink_eyelid_ctrl)

    # L and R Indicators
    l_crv = cmds.curve(p=[[12.357, -0.616, 0], [11.643, -0.616, 0], [11.643, 0.616, 0], [11.807, 0.616, 0],
                          [11.807, -0.47, 0], [12.357, -0.47, 0], [12.357, -0.616, 0], [11.643, -0.616, 0],
                          [11.643, 0.616, 0]], d=1,
                       name='left_indicator_eyes_crv')
    r_crv_a = cmds.curve(p=[[-11.523, -0.616, 0], [-11.63, -0.616, 0], [-11.736, -0.616, 0], [-11.931, -0.371, 0],
                            [-12.126, -0.126, 0], [-12.22, -0.126, 0], [-12.313, -0.126, 0], [-12.313, -0.371, 0],
                            [-12.313, -0.616, 0], [-12.395, -0.616, 0], [-12.477, -0.616, 0], [-12.477, 0, 0],
                            [-12.477, 0.616, 0], [-12.318, 0.616, 0], [-12.159, 0.616, 0], [-12.053, 0.616, 0],
                            [-11.91, 0.592, 0], [-11.846, 0.55, 0], [-11.781, 0.509, 0], [-11.706, 0.378, 0],
                            [-11.706, 0.282, 0], [-11.706, 0.146, 0], [-11.843, -0.036, 0], [-11.962, -0.08, 0],
                            [-11.742, -0.348, 0], [-11.523, -0.616, 0]], d=1,
                         name='right_indicator_a_eyes_crv')
    r_crv_b = cmds.curve(p=[[-11.877, 0.269, 0], [-11.877, 0.323, 0], [-11.915, 0.406, 0], [-11.955, 0.433, 0],
                            [-11.99, 0.456, 0], [-12.082, 0.475, 0], [-12.151, 0.475, 0], [-12.232, 0.475, 0],
                            [-12.313, 0.475, 0], [-12.313, 0.243, 0], [-12.313, 0.01, 0], [-12.241, 0.01, 0],
                            [-12.169, 0.01, 0], [-12.099, 0.01, 0], [-11.986, 0.035, 0], [-11.947, 0.074, 0],
                            [-11.911, 0.109, 0], [-11.877, 0.205, 0], [-11.877, 0.269, 0]], d=1,
                         name='right_indicator_b_eyes_crv')

    r_crv = combine_curves_list([r_crv_a, r_crv_b])
    cmds.setAttr(l_crv + '.overrideDisplayType', 2)
    cmds.setAttr(r_crv + '.overrideDisplayType', 2)
    cmds.setAttr(l_crv + '.ty', 8.6)
    cmds.setAttr(r_crv + '.ty', 8.6)
    cmds.setAttr(l_crv + '.tx', 3)
    cmds.setAttr(r_crv + '.tx', -3)
    background.append(l_crv)
    background.append(r_crv)

    # Main Label
    blink_crv = create_text('BLINK')
    blink_crv = cmds.rename(blink_crv, 'left_eye_' + blink_crv)
    force_center_pivot(blink_crv)
    rescale(blink_crv, .7)
    cmds.setAttr(blink_crv + '.ty', -7.3)
    cmds.setAttr(blink_crv + '.tx', 3.615)
    cmds.setAttr(blink_crv + '.overrideDisplayType', 2)
    right_blink_crv = cmds.duplicate(blink_crv, name=blink_crv.replace('left', 'right'))[0]
    cmds.setAttr(right_blink_crv + '.tx', -6.385)
    background.append(blink_crv)
    background.append(right_blink_crv)

    # Parent Groups
    gui_grp = cmds.group(name='eyes_gui_grp', world=True, empty=True)
    bg_grp = cmds.group(name='eyes_background_grp', world=True, empty=True)

    # General Background
    eyebrow_bg_crv = cmds.curve(name='eyes_bg_crv', p=[[-20.0, 11.0, 0.0], [-20.0, -9.0, 0.0], [20.0, -9.0, 0.0],
                                                       [20.0, 11.0, 0.0], [-20.0, 11.0, 0.0]], d=1)

    cmds.setAttr(eyebrow_bg_crv + '.overrideDisplayType', 1)
    background.append(eyebrow_bg_crv)

    for obj in controls:
        cmds.parent(obj[1], gui_grp)
        if 'left_' in obj[0]:
            change_viewport_color(obj[0], LEFT_CTRL_COLOR)
            change_outliner_color(obj[1], (0.21, 0.59, 1))  # Soft Blue
        elif 'right_' in obj[0]:
            change_viewport_color(obj[0], RIGHT_CTRL_COLOR)
            change_outliner_color(obj[1], RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(obj[0], CENTER_CTRL_COLOR)
            change_outliner_color(obj[1], CENTER_CTRL_COLOR)

    for obj in background:
        cmds.parent(obj, bg_grp)
        cmds.setAttr(obj + '.overrideEnabled', 1)

    # Background Group
    cmds.parent(bg_grp, gui_grp)
    change_outliner_color(bg_grp, (0, 0, 0))

    return gui_grp, controls


def create_facial_side_gui(add_nose_cheeks=False):
    selection = cmds.ls(selection=True)
    parent_grp = cmds.group(empty=True, world=True, name='facial_side_gui_grp')
    eyebrow_ctrls = create_eyebrow_controls()
    eye_ctrls = create_eye_controls()
    mouth_ctrls = create_mouth_controls()
    cmds.move(43, eyebrow_ctrls[0], moveY=True)
    cmds.move(23, eye_ctrls[0], moveY=True)
    cmds.parent(eyebrow_ctrls[0], parent_grp)
    cmds.parent(eye_ctrls[0], parent_grp)
    cmds.parent(mouth_ctrls[0], parent_grp)
    if add_nose_cheeks:
        nose_cheek_ctrls = create_cheek_nose_controls()
        cmds.parent(nose_cheek_ctrls[0], parent_grp)
        cmds.move(22, nose_cheek_ctrls[0], moveY=True)
        cmds.move(42, eye_ctrls[0], moveY=True)
        cmds.move(62, eyebrow_ctrls[0], moveY=True)
    cmds.select(selection)
    return parent_grp