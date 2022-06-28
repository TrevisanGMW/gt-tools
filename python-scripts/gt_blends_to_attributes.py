# WIP for script that connects blendshape to a control
import maya.cmds as cmds

selection_source = cmds.ls(selection=True)[0]  # First selected object - Geo with BS
selection_target = cmds.ls(selection=True)[1]  # Second selected object - Curve
history = cmds.listHistory(selection_source)
blendshape_node = cmds.ls(history, type ='blendShape')[0]
blendshape_names = cmds.listAttr(blendshape_node + '.w', m=True)

modify_range = True
attribute_range_min = 0
attribute_range_max = 10
blend_range_min = 0
blend_range_max = 1

ignore_connected = True
add_separator_attribute = True
custom_separator_attr = ''
method = 'includes'

undesired_filter_strings = ['corrective']
desired_blends = []
desired_filter_strings = ['nose']
filtered_blends = []

# Find desired blends
for target in blendshape_names:
    for desired_filter_string in desired_filter_strings:
        if method == 'includes':
            if desired_filter_string in target:
                filtered_blends.append(target)
        elif method == 'startswith':
            if target.startswith(desired_filter_string):
                filtered_blends.append(target)
        elif method == 'endswith':
            if target.endswith(desired_filter_string):
                filtered_blends.append(target)

if len(desired_filter_strings) == 0:  # If filter empty, use everything
    filtered_blends = blendshape_names


if ignore_connected:  # Pre-ignore connected blends
    accessible_blends = []
    for blend in filtered_blends:
        connections = cmds.listConnections(blendshape_node + '.' + blend, destination=False, plugs=True) or []
        if len(connections) == 0:
            accessible_blends.append(blend)
else:
    accessible_blends = filtered_blends

# Remove undesired blends from list
undesired_blends = []
for target in desired_blends:
    for undesired_string in undesired_filter_strings:
        if undesired_string in target:
            undesired_blends.append(target)
for blend in accessible_blends:
    if blend not in undesired_blends:
        desired_blends.append(blend)

# Separator Attribute
if len(desired_blends) != 0 and add_separator_attribute:
    separator_attr = 'blends'
    if custom_separator_attr:
        separator_attr = custom_separator_attr
    cmds.addAttr(selection_target, ln=separator_attr, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(selection_target + '.' + separator_attr, e=True, lock=True)

# Create Blend Drivers
desired_blends.sort()
for target in desired_blends:
    if modify_range:
        cmds.addAttr(selection_target, ln=target, at='double', k=True,
                     maxValue=attribute_range_max, minValue=attribute_range_min)
        remap_node = cmds.createNode('remapValue', name='remap_bs_' + target)
        cmds.setAttr(remap_node + '.inputMax', attribute_range_max)
        cmds.setAttr(remap_node + '.inputMin', attribute_range_min)
        cmds.setAttr(remap_node + '.outputMax', blend_range_max)
        cmds.setAttr(remap_node + '.outputMin', blend_range_min)
        cmds.connectAttr(selection_target + '.' + target, remap_node + '.inputValue')
        cmds.connectAttr(remap_node + '.outValue', blendshape_node + '.' + target, force=True)
    else:
        cmds.addAttr(selection_target, ln=target, at='double', k=True, maxValue=1, minValue=0)
        cmds.connectAttr(selection_target + '.' + target, blendshape_node + '.' + target, force=True)
