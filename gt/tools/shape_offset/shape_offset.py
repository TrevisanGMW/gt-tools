"""
GT Offset Shape - Offsets the CVs of a curve shape
github.com/TrevisanGMW/gt-tools - 2022-03-16
"""
import maya.cmds as cmds


def offset_curve_shape(curve_transforms, offset_pos=None):
    """
    Offsets curves according to the provided parameters (currently only supporting position)
    Args:
        curve_transforms (list): A list of curves to receive the offsets
        offset_pos (optional, list): A tuple or list containing the position offset values
                                     (float_x, float_y, float_z)
        # offset_rot (optional, list): A tuple or list containing the rotation offset values
                                      (float_x, float_y, float_z)
        # offset_scale (optional, list): A tuple or list containing the rotation offset values
                                        (float_x, float_y, float_z)
    """
    valid_types = ['nurbsCurve', 'bezierCurve']
    accepted_shapes = []
    for crv in curve_transforms:
        curve_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
        # Filter valid shapes:
        for shape in curve_shapes:
            current_shape_type = cmds.objectType(shape)
            if current_shape_type in valid_types:
                accepted_shapes.append(shape)
    # Position
    if offset_pos:
        # Extract CVs into Python code:
        for shape in accepted_shapes:
            curve_data = zip(cmds.ls('%s.cv[*]' % shape, flatten=True), cmds.getAttr(shape + '.cv[*]'))
            curve_data_list = list(curve_data)
            # Offset CVs:
            if curve_data_list:
                for cv in curve_data_list:
                    cv_index = cv[0]
                    cv_pos = cv[1]
                    cv_pos_offset = [cv_pos[0] + offset_pos[0],
                                     cv_pos[1] + offset_pos[1],
                                     cv_pos[2] + offset_pos[2]]
                    cmds.xform(cv_index, os=True, t=cv_pos_offset)

    # Rotation or Scale
    # if offset_rot or offset_scale:
    #     for crv in curve_transforms:
    #         duplicated_crv = cmds.duplicate(crv, name='temp_' + str(random.random()),
    #                                         renameChildren=True)[0]
    #         print(duplicated_crv)
    #         print('yes')

    # if offset_scale:


if __name__ == '__main__':
    offset_curve_shape(['chest_ribbon_ctrl'])
