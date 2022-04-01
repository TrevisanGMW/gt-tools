"""
GT Extract Shape State - Outputs the python code containing the current shape data for the selected curves

v1.0.0 - 2021-10-01
Initial Release

v1.1.0 - 2022-03-16
Added GUI and checks
Added option to print or just return it


"""
import maya.cmds as cmds


def extract_python_curve_shape(curve_transforms, printing=False):
    """
    Extracts the Python code necessary to reshape
    Args:
        curve_transforms (list of strings): Transforms carrying curve shapes inside them (nurbs or bezier)
        printing: Whether to print the extracted python code. If False it will only return the code.

    Returns:
        python_string (string): Python code with the current state of the selected curves (their shape)

    """
    output = ''
    if printing:
        output += ('#' * 80)
    for crv in curve_transforms:
        valid_types = ['nurbsCurve', 'bezierCurve']
        accepted_shapes = []
        curve_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
        # Filter valid shapes:
        for shape in curve_shapes:
            current_shape_type = cmds.objectType(shape)
            if current_shape_type in valid_types:
                accepted_shapes.append(shape)

        # Extract CVs into Python code:
        # print(accepted_shapes)
        for shape in accepted_shapes:
            curve_data = zip(cmds.ls('%s.cv[*]' % shape, flatten=True), cmds.getAttr(shape + '.cv[*]'))
            curve_data_list = list(curve_data)
            # Assemble command:
            if curve_data_list:
                output += '\n# Curve data for "' + str(shape).split('|')[-1] + '":\n'
                output += 'for cv in ' + str(curve_data_list) + ':\n'
                output += '    cmds.xform(cv[0], os=True, t=cv[1])\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection contains nurbs or bezier curves.')
            return None
    else:
        return output


if __name__ == '__main__':
    out = extract_python_curve_shape(cmds.ls(selection=True), False)
    print(out)
