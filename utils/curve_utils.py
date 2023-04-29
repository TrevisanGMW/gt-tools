def combine_curves_list(curve_list):
    """
    This is a modified version of the GT Utility "Combine Curves"
    It moves the shape objects of all elements in the provided input (curve_list) to a single group (combining them)
    This version was changed to accept a list of objects (instead of selection)

            Parameters:
                    curve_list (list): A string of strings with the name of the curves to be combined.

    """
    errors = ''
    function_name = 'GTU Combine Curves List'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True
        acceptable_types = ['nurbsCurve', 'bezierCurve']
        bezier_in_selection = []

        for crv in curve_list:
            shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(crv)
                if cmds.objectType(shape) not in acceptable_types:
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')

        if valid_selection and len(curve_list) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False

        if len(bezier_in_selection) > 0 and valid_selection:
            message = 'A bezier curve was found in your selection.' \
                      '\nWould you like to convert Bezier to NURBS before combining?'
            user_input = cmds.confirmDialog(title='Bezier curve detected!',
                                            message=message,
                                            button=['Yes', 'No'],
                                            defaultButton='Yes',
                                            cancelButton='No',
                                            dismissString='No',
                                            icon='warning')
            if user_input == 'Yes':
                for bezier in bezier_in_selection:
                    logger.debug(str(bezier))
                    cmds.bezierCurveToNurbs()

        if valid_selection:
            shapes = []
            for crv in curve_list:
                extracted_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
                for ext_shape in extracted_shapes:
                    shapes.append(ext_shape)

            for crv in range(len(curve_list)):
                cmds.makeIdentity(curve_list[crv], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=curve_list[0])
            cmds.select(shapes[0])
            for crv in range(1, (len(shapes))):
                cmds.select(shapes[crv], add=True)

            cmds.select(group, add=True)
            cmds.parent(relative=True, shape=True)
            cmds.delete(curve_list)
            combined_curve = cmds.rename(group, curve_list[0])
            return combined_curve

    except Exception as exception:
        errors += str(exception) + '\n'
        cmds.warning('An error occurred when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)
        
        
def add_snapping_shape(target_object):
    """
    Parents a locator shape to the target object so objects can be snapped to it.
    The parented locator shape has a scale of 0, so it doesn't change the look of the target object.
    Args:
        target_object (string): Name of the object to add the locator shape.
    Returns:
        Name of the added shape
    """
    if not target_object or not cmds.objExists(target_object):
        return
    locator = cmds.spaceLocator(name=target_object + "Point")[0]
    locator_shape = cmds.listRelatives(locator, s=True, f=True) or []
    cmds.setAttr(locator_shape[0] + ".localScaleX", 0)
    cmds.setAttr(locator_shape[0] + ".localScaleY", 0)
    cmds.setAttr(locator_shape[0] + ".localScaleZ", 0)
    cmds.select(locator_shape)
    cmds.select(target_object, add=True)
    cmds.parent(relative=True, shape=True)
    cmds.delete(locator)
    return locator_shape[0]



def add_side_color_setup(obj, left_clr=(0, 0.5, 1), right_clr=(1, 0.5, 0.5)):
    if not obj or not cmds.objExists(obj):
        return

    # Setup Base Connections
    default_clr = (1, 1, 0.65)
    cmds.setAttr(obj + ".overrideEnabled", 1)
    cmds.setAttr(obj + ".overrideRGBColors", 1)
    clr_side_condition = cmds.createNode("condition", name=obj + "_clr_side_condition")
    clr_center_condition = cmds.createNode("condition", name=obj + "_clr_center_condition")
    decompose_matrix = cmds.createNode("decomposeMatrix", name=obj + "_decompose_matrix")
    cmds.connectAttr(obj + ".worldMatrix[0]", decompose_matrix + ".inputMatrix")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_side_condition + ".firstTerm")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_center_condition + ".firstTerm")
    cmds.connectAttr(clr_side_condition + ".outColor", clr_center_condition + ".colorIfFalse")
    cmds.setAttr(clr_side_condition + ".operation", 2)

    # Create Auto Color Attribute
    cmds.addAttr(obj, ln=PROXY_ATTR_COLOR, at='bool', k=True)
    cmds.setAttr(obj + "." + PROXY_ATTR_COLOR, 1)
    clr_auto_blend = cmds.createNode("blendColors", name=obj + "_clr_auto_blend")
    cmds.connectAttr(clr_auto_blend + ".output", obj + ".overrideColorRGB")
    cmds.connectAttr(clr_center_condition + ".outColor", clr_auto_blend + ".color1")
    cmds.connectAttr(obj + "." + PROXY_ATTR_COLOR, clr_auto_blend + ".blender")

    # Setup Color Attributes
    clr_attr = "colorDefault"
    add_attr_double_three(obj, clr_attr, keyable=False)
    cmds.setAttr(obj + "." + clr_attr + "R", default_clr[0])
    cmds.setAttr(obj + "." + clr_attr + "G", default_clr[1])
    cmds.setAttr(obj + "." + clr_attr + "B", default_clr[2])
    cmds.connectAttr(obj + "." + clr_attr + "R", clr_center_condition + ".colorIfTrueR")
    cmds.connectAttr(obj + "." + clr_attr + "G", clr_center_condition + ".colorIfTrueG")
    cmds.connectAttr(obj + "." + clr_attr + "B", clr_center_condition + ".colorIfTrueB")
    cmds.connectAttr(obj + "." + clr_attr, clr_auto_blend + ".color2")  # Blend node input
    r_clr_attr = "colorRight"
    add_attr_double_three(obj, r_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + r_clr_attr + "R", left_clr[0])
    cmds.setAttr(obj + "." + r_clr_attr + "G", left_clr[1])
    cmds.setAttr(obj + "." + r_clr_attr + "B", left_clr[2])
    cmds.connectAttr(obj + "." + r_clr_attr + "R", clr_side_condition + ".colorIfTrueR")
    cmds.connectAttr(obj + "." + r_clr_attr + "G", clr_side_condition + ".colorIfTrueG")
    cmds.connectAttr(obj + "." + r_clr_attr + "B", clr_side_condition + ".colorIfTrueB")
    l_clr_attr = "colorLeft"
    add_attr_double_three(obj, l_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + l_clr_attr + "R", right_clr[0])
    cmds.setAttr(obj + "." + l_clr_attr + "G", right_clr[1])
    cmds.setAttr(obj + "." + l_clr_attr + "B", right_clr[2])
    cmds.connectAttr(obj + "." + l_clr_attr + "R", clr_side_condition + ".colorIfFalseR")
    cmds.connectAttr(obj + "." + l_clr_attr + "G", clr_side_condition + ".colorIfFalseG")
    cmds.connectAttr(obj + "." + l_clr_attr + "B", clr_side_condition + ".colorIfFalseB")
    
    

def create_main_control(name):
    """
    Creates a main control with an arrow pointing to +Z (Direction character should be facing)

        Parameters:
            name (string): Name of the new control

        Returns:
            main_crv (string): Name of the generated control (in case it was different from what was provided)

    """
    main_crv_assembly = []
    main_crv_a = cmds.curve(name=name, p=[[-11.7, 0.0, 45.484], [-16.907, 0.0, 44.279], [-25.594, 0.0, 40.072],
                                          [-35.492, 0.0, 31.953], [-42.968, 0.0, 20.627], [-47.157, 0.0, 7.511],
                                          [-47.209, 0.0, -6.195], [-43.776, 0.0, -19.451], [-36.112, 0.0, -31.134],
                                          [-26.009, 0.0, -39.961], [-13.56, 0.0, -45.63], [0.0, 0.0, -47.66],
                                          [13.56, 0.0, -45.63], [26.009, 0.0, -39.961], [36.112, 0.0, -31.134],
                                          [43.776, 0.0, -19.451], [47.209, 0.0, -6.195], [47.157, 0.0, 7.511],
                                          [42.968, 0.0, 20.627], [35.492, 0.0, 31.953], [25.594, 0.0, 40.072],
                                          [16.907, 0.0, 44.279], [11.7, 0.0, 45.484]], d=3)
    main_crv_assembly.append(main_crv_a)
    main_crv_b = cmds.curve(name=name + 'direction',
                            p=[[-11.7, 0.0, 45.484], [-11.7, 0.0, 59.009], [-23.4, 0.0, 59.009], [0.0, 0.0, 82.409],
                               [23.4, 0.0, 59.009], [11.7, 0.0, 59.009], [11.7, 0.0, 45.484]], d=1)
    main_crv_assembly.append(main_crv_b)
    main_crv = combine_curves_list(main_crv_assembly)

    # Rename Shapes
    shapes = cmds.listRelatives(main_crv, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('main_ctrlCircle'))
    cmds.rename(shapes[1], '{0}Shape'.format('main_ctrlArrow'))

    return main_crv