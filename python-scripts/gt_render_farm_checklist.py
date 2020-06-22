"""

 Checklist Generator
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-11
 
 When creating a new checklist, change these items:
    checklist_name - variable content
    build_gui_checklist() - name of the function
    build_gui_help_checklist() - name of the function

 To Do:
 

"""
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Checklist Name
checklist_name = "VFS Render Farm Checklist" #""

# Version
script_version = "1.0";


# Status Colors
def_color = 0.3, 0.3, 0.3
pass_color = (0.17, 1.0, 0.17)
warning_color = (1.0, 1.0, 0.17)
error_color = (1.0, 0.17, 0.17)
exception_color = 0.2, 0.2, 0.2

# Full Report .clear

# Checklist Items - Item Number [Name, Expected Value]
checklist_items = { 0 : ["Frame Rate", "film"],
                    1 : ["Scene Units", "cm"],
                    2 : ["Output Resolution", ["1920","1080"] ],
                    3 : ["Total Texture Count", [40, 50] ],
                    4 : ["Network File Paths", ["H:","vfsstorage10"] ],
                    5 : ["Unparented Objects", 0],
                    6 : ["Total Triangle Count", [1800000, 2000000] ],
                    7 : ["Total Poly Object Count", [90, 100] ],
                    8 : ["Shadow Casting Lights", [2, 3] ],
                    9 : ["RS Shadow Casting Lights", [3, 4]],
                   10 : ["Arnold Shadow Casting Lights", [3, 4]],
                   11 : ["Default Object Names", 0],
                   12 : ["Objects Assigned to lambert1", 0],
                   13 : ["Ngons", 0],
                   14 : ["Non-manifold Geometry", 0],
                   15 : ["Empty UV Sets", 0],
                   16 : ["Frozen Transforms", 0],
                   17 : ["Animated Visibility", 0],
                   18 : ["Non Deformer History", 0 ]
                  }
                  

def build_gui_checklist():
    window_name = "build_gui_checklist"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=checklist_name + "  v" + script_version, mnb=False, mxb=False, s=True)

    main_column = cmds.columnLayout()

    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, h=1, w=1)
    
    # UI
    main_cw = 300
    warning_title_cw = 100
    warning_content_cw = 280

    # Title Text
    cmds.separator(h=14, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 240), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=main_column)

    cmds.text(" ", bgc=[0,.5,0])
    cmds.text(checklist_name + " - v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_checklist())
    cmds.separator(h=10, style='none', p=main_column) # Empty Space

    #cmds.separator(h=8)
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.separator(h=8)

    # General Cleanup Info
    cmds.rowColumnLayout(nc=1, cw=[(1, 280)], cs=[(1,10)], p=main_column)
    cmds.separator(h=5, style='none') # Empty Space

    cmds.rowColumnLayout(nc=3, cw=[(1, 170), (2, 35), (3, 90)], cs=[(1, 15), (2, 6), (3, 6)], p=main_column) 
    
    # Header
    cmds.text(l="Operation", align="left")
    cmds.text(l='Status', align="left")
    cmds.text(l='Info', align="center")
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    
    
    # Build Checklist
    def create_checklist_items(items):
        for item in items:
            item_id = checklist_items.get(item)[0].lower().replace(" ","_").replace("-","_")
            cmds.text(l=checklist_items.get(item)[0] + ': ', align="left")
            cmds.button("status_" + item_id , l='', h=14, bgc=def_color)
            cmds.text("output_" + item_id, l='...', align="center")

    create_checklist_items(checklist_items)

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    
    cmds.separator(h=8, style='none') # Empty Space
    
    # End of list
    cmds.separator(h=8)

    # Refresh Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='Generate Report', h=30, c=lambda args: checklist_generate_report())
    cmds.separator(h=10, style='none')
    cmds.button(l='Refresh', h=30, c=lambda args: checklist_refresh())
    cmds.separator(h=8, style='none')

    # Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/checkboxOn.png')
    widget.setWindowIcon(icon)


def checklist_refresh():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)
    
    check_frame_rate()
    check_scene_units()
    check_output_resolution()
    check_total_texture_count()
    check_network_file_paths()
    check_unparented_objects()  
    check_total_triangle_count()
    check_total_poly_object_count()
    check_shadow_casting_light_count()
    check_rs_shadow_casting_light_count()
    check_ai_shadow_casting_light_count()
    check_default_object_names()
    check_objects_assigned_to_lambert1()
    check_ngons()
    check_non_manifold_geometry()
    check_empty_uv_sets()
    check_frozen_transforms()
    check_animated_visibility()
    check_non_deformer_history()
    
    # Clear Selection
    cmds.selectMode( object=True )
    cmds.select(clear=True)
    
    # Reselect Previous Selection
    cmds.select(current_selection)
        
    #load_state() #save_state()
    

def checklist_generate_report():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)
    
    report_strings = []
    report_strings.append(check_frame_rate())
    report_strings.append(check_scene_units())
    report_strings.append(check_output_resolution())
    report_strings.append(check_total_texture_count())
    report_strings.append(check_network_file_paths())
    report_strings.append(check_unparented_objects())
    report_strings.append(check_total_triangle_count())
    report_strings.append(check_total_poly_object_count())
    report_strings.append(check_shadow_casting_light_count())
    report_strings.append(check_rs_shadow_casting_light_count())
    report_strings.append(check_ai_shadow_casting_light_count())
    report_strings.append(check_default_object_names())
    report_strings.append(check_objects_assigned_to_lambert1())
    report_strings.append(check_ngons())
    report_strings.append(check_non_manifold_geometry())
    report_strings.append(check_empty_uv_sets())
    report_strings.append(check_frozen_transforms())
    report_strings.append(check_animated_visibility())
    report_strings.append(check_non_deformer_history())
    
    # Clear Selection
    cmds.selectMode( object=True )
    cmds.select(clear=True)
    
    # Show Report
    export_to_txt(report_strings)
    
    # Reselect Previous Selection
    cmds.select(current_selection)
    
    
    

# Checklist Functions Start Here ================================================================

# Item 0 - Frame Rate
def check_frame_rate():
    item_name = checklist_items.get(0)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(0)[1]
    received_value = cmds.currentUnit( query=True, time=True ) # Frame Rate
    issues_found = 0

    if received_value == expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': '  + received_value.capitalize())) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: patch_frame_rate())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=received_value.capitalize() )
    
    # Patch Function ----------------------
    def patch_frame_rate():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Do you want to change your ' + item_name.lower() + ' from "' + received_value + '" to "' + expected_value.capitalize() + '"?',
                    button=['Yes, change it for me', 'Ignore Issue'],
                    defaultButton='Yes, change it for me',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="question")

        if user_input == 'Yes, change it for me':
            cmds.currentUnit( time=expected_value )
            print("Your " + item_name.lower() + " was changed to " + expected_value)
            check_frame_rate()
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "'  + expected_value.capitalize() + '" and yours is "' + received_value.capitalize() + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "'  + expected_value.capitalize() + '" and yours is "' + received_value.capitalize() + '"'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    

# Item 1 - Scene Units =========================================================================
def check_scene_units():
    item_name = checklist_items.get(1)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(1)[1]
    received_value = cmds.currentUnit( query=True, linear=True )
    issues_found = 0

    if received_value == expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "'  + received_value + '".')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: patch_scene_units())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=received_value.capitalize() )
    
    # Patch Function ----------------------
    def patch_scene_units():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Do you want to change your ' + item_name.lower() + ' from "' + received_value + '" to "' + expected_value.capitalize() + '"?',
                    button=['Yes, change it for me', 'Ignore Issue'],
                    defaultButton='Yes, change it for me',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="question")

        if user_input == 'Yes, change it for me':
            cmds.currentUnit( linear=expected_value )
            print("Your " + item_name.lower() + " was changed to " + expected_value)
            check_scene_units()
        else:
            cmds.button("status_" + item_id, e=True, l= '')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "'  + expected_value.capitalize() + '" and yours is "' + received_value.capitalize() + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "'  + expected_value.capitalize() + '" and yours is "' + received_value.capitalize() + '"'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 2 - Output Resolution =========================================================================
def check_output_resolution():
    item_name = checklist_items[2][0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items[2][1]
    received_value = [str(cmds.getAttr("defaultResolution.width")), str(cmds.getAttr("defaultResolution.height"))]
    issues_found = 0


    if received_value[0] == expected_value[0] and received_value[1] == expected_value[1]:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "' + received_value[0] + 'x' + received_value[1] + '".')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: patch_output_resolution())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=received_value[0] + 'x' + received_value[1] )
    
    # Patch Function ----------------------
    def patch_output_resolution():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Do you want to change your ' + item_name.lower() + ' from "' + ': "' + received_value[0] + 'x' + received_value[1] + '" to "' + expected_value[0] + 'x' + expected_value[1] + '"?',
                    button=['Yes, change it for me', 'Ignore Issue'],
                    defaultButton='Yes, change it for me',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="question")

        if user_input == 'Yes, change it for me':
            cmds.setAttr( "defaultResolution.width", int(expected_value[0]) )
            cmds.setAttr( "defaultResolution.height", int(expected_value[1]) )
            print('Your ' + item_name.lower() + ' was changed to "' + expected_value[0] + 'x' + expected_value[1] + '"')
            check_output_resolution()
        else:
            cmds.button("status_" + item_id, e=True, l= '')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "'  + expected_value[0] + 'x' + expected_value[1] + '" and yours is "' + received_value[0] + 'x' + received_value[1] + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "'  + expected_value[0] + 'x' + expected_value[1] + '" and yours is "' + received_value[0] + 'x' + received_value[1] + '"'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 3 - Total Texture Count =========================================================================
def check_total_texture_count():
    item_name = checklist_items.get(3)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(3)[1] # Solve Warning Value !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    received_value = 0 
    issues_found = 0
    
    # Count File Nodes
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        received_value +=1

    if received_value <= expected_value[1]:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': '  + str(received_value) + ' file nodes')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_total_texture_count())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=received_value )
    
    # Patch Function ----------------------
    def warning_total_texture_count():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Your ' + item_name.lower() + ' should be reduced from "' + str(received_value) + '" to less than "' + str(expected_value[1]) + '".',
                    button=['OK', 'Ignore Issue'],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was less than "'  + str(expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was less than "'  + str(expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    return '\n*** ' + item_name + " ***\n" + string_status
    
# Item 4 - Network File Paths =========================================================================
def check_network_file_paths():
    item_name = checklist_items.get(4)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(4)[1]
    incorrect_file_nodes = []
    
    # Count Incorrect File Nodes
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        file_path = cmds.getAttr(file + ".fileTextureName")
        
        if file_path != '':
            if file_path.startswith(expected_value[0]) or file_path.startswith(expected_value[1]):
                pass
            else:
                incorrect_file_nodes.append(file)
        else:
            incorrect_file_nodes.append(file)


    if len(incorrect_file_nodes) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('All file nodes currently sourced from the network.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_network_file_paths())
        issues_found = len(incorrect_file_nodes)
        
    cmds.text("output_" + item_id, e=True, l=len(incorrect_file_nodes) )
    
    # Patch Function ----------------------
    def warning_network_file_paths():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message=str(len(incorrect_file_nodes)) + ' of your file node paths aren\'t pointing to the network drive. \nPlease change their path to a network location. \n\n(Too see a list of nodes, generate a full report)',
                    button=['OK', 'Ignore Issue'],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for file_node in incorrect_file_nodes: 
            string_status = string_status + '"' + file_node +  '" isn\'t pointing to the the network drive. Your texture files should be sourced from the network.\n'
    else: 
        string_status = str(issues_found) + ' issues found. All textures were sourced from the network'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    
# Item 5 - Unparented Objects =========================================================================
def check_unparented_objects():
    item_name = checklist_items.get(5)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(5)[1]
    unparented_objects = []

    # Count Unparented Objects
    geo_dag_nodes = cmds.ls(geometry=True)
    for obj in geo_dag_nodes:
        first_parent = cmds.listRelatives(obj, p=True, f=True) # Check if it returned something?
        children_members = cmds.listRelatives(first_parent[0], c=True, type="transform") or []
        parents_members = cmds.listRelatives(first_parent[0], ap=True, type="transform") or []
        if len(children_members) + len(parents_members) == 0:
            if cmds.nodeType(obj) != "mentalrayIblShape":
                unparented_objects.append(obj)

    if len(unparented_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No unparented objects were found.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_unparented_objects())
        issues_found = len(unparented_objects)
        
    cmds.text("output_" + item_id, e=True, l=len(unparented_objects) )
    
    # Patch Function ----------------------
    def warning_unparented_objects():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= str(len(unparented_objects)) + ' unparented object(s) found in this scene. \nIt\'s likely that these objects need to be part of a hierarchy.\n\n(Too see a list of objects, generate a full report)',
                    button=['OK', 'Ignore Issue'],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in unparented_objects: 
            string_status = string_status + '"' + obj +  '" has no parent or child nodes. It should likely be part of a hierarchy.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No unparented objects were found.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 6 - Total Triangle Count =========================================================================
def check_total_triangle_count():
    item_name = checklist_items.get(6)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(6)[1][1]
    inbetween_value = checklist_items.get(6)[1][0]
    unparented_objects = []

    all_poly_count = cmds.ls(type="mesh", flatten=True)
    scene_tri_count = 0;
    smoothedObjCount = 0;
    
    for obj in all_poly_count:
        smooth_level = cmds.getAttr(obj + ".smoothLevel")
        smooth_state = cmds.getAttr(obj + ".displaySmoothMesh")
        total_tri_count = cmds.polyEvaluate(obj, t=True)
        total_edge_count = cmds.polyEvaluate(obj, e=True)
        total_face_count = cmds.polyEvaluate(obj, f=True)

        if smooth_state > 0 and smooth_level != 0:
            one_subdiv_tri_count = (total_edge_count * 4)
            if smooth_level > 1:
                multi_subdiv_tri_count = one_subdiv_tri_count * (4 ** (smooth_level-1))
                scene_tri_count = scene_tri_count + multi_subdiv_tri_count
            else:
                scene_tri_count += one_subdiv_tri_count
        else:
            scene_tri_count += total_tri_count
                
    if scene_tri_count < expected_value and scene_tri_count > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_total_triangle_count())
        issues_found = 0;
        patch_message = 'Your scene has ' + str(scene_tri_count) + ' triangles, which is high. \nConsider optimizing it if possible.'
        cancel_message= "Ignore Warning"
    elif scene_tri_count < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('Your scene has ' + str(scene_tri_count) +  ' triangles. \nGood job keeping the triangle count low!.')) 
        issues_found = 0;
        patch_message = ''
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_total_triangle_count())
        issues_found = 1;
        patch_message = 'Your scene has ' + str(scene_tri_count) + ' triangles. You should try to keep it under ' + str(expected_value) + '.\n\n' + 'In case you see a different number on your "Heads Up Display > Poly Count" option.  It\'s likely that you have “shapeOrig” nodes in your scene. These are intermediate shape node usually created by deformers. If you don\'t have deformations on your scene, you can delete these to reduce triangle count.\n'
        cancel_message= "Ignore Issue"
        
    cmds.text("output_" + item_id, e=True, l=scene_tri_count )
    
    # Patch Function ----------------------
    def warning_total_triangle_count():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', cancel_message],
                    defaultButton='OK',
                    cancelButton=cancel_message,
                    dismissString=cancel_message, 
                    icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(str(issues_found) + ' issues found. Your scene has ' + str(scene_tri_count) +  ' triangles, which is high. \nConsider optimizing it if possible.') )
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if scene_tri_count > inbetween_value and scene_tri_count < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene has ' + str(scene_tri_count) +  ' triangles, which is high. Consider optimizing it if possible.' 
    elif scene_tri_count < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene has ' + str(scene_tri_count) +  ' triangles. Good job keeping the triangle count low!.' 
    else: 
        string_status = str(issues_found) + ' issue found. Your scene has ' + str(scene_tri_count) + ' triangles. You should try to keep it under ' + str(expected_value) + '.'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 7 - Total Poly Object Count =========================================================================
def check_total_poly_object_count():
    item_name = checklist_items.get(7)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(7)[1][1]
    inbetween_value = checklist_items.get(7)[1][0]
    
    all_polymesh = cmds.ls(type= "mesh")

    if len(all_polymesh) < expected_value and len(all_polymesh) > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_total_poly_object_count())
        issues_found = 0;
        patch_message = 'Your scene contains "' + str(len(all_polymesh)) + '" polygon meshes, which is a high number. \nConsider optimizing it if possible.'
        cancel_message= "Ignore Warning"
    elif len(all_polymesh) < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('Your scene contains "' +str(len(all_polymesh)) + '" polygon meshes.')) 
        issues_found = 0;
        patch_message = ''
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_total_poly_object_count())
        issues_found = 1;
        patch_message = str(len(all_polymesh)) + ' polygon meshes in your scene. \nTry to keep this number under ' + str(expected_value) + '.'
        cancel_message= "Ignore Issue"
        
    cmds.text("output_" + item_id, e=True, l=len(all_polymesh) )
    
    # Patch Function ----------------------
    def warning_total_poly_object_count():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', cancel_message],
                    defaultButton='OK',
                    cancelButton=cancel_message,
                    dismissString=cancel_message, 
                    icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(str(issues_found) + ' issues found. Your scene contains ' + str(len(all_polymesh)) +  ' polygon meshes, which is a high number. \nConsider optimizing it if possible.') )
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if len(all_polymesh) < expected_value and len(all_polymesh) > inbetween_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' +  str(len(all_polymesh)) + '" polygon meshes, which is a high number. Consider optimizing it if possible.'
    elif len(all_polymesh) < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(all_polymesh)) + '" polygon meshes.'
    else: 
        string_status = str(issues_found) + ' issue found. Your scene contains "' + str(len(all_polymesh)) + '" polygon meshes. Try to keep this number under "' + str(expected_value) + '".'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    
# Item 8 - Shadow Casting Light Count =========================================================================
def check_shadow_casting_light_count():
    item_name = checklist_items.get(8)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(8)[1][1]
    inbetween_value = checklist_items.get(8)[1][0]
    
    all_lights = cmds.ls(lights=True)
    shadow_casting_lights = []
   
    for light in all_lights:
        shadow_state = cmds.getAttr (light + ".useRayTraceShadows")
        if shadow_state == 1:
            shadow_casting_lights.append(light)

    if len(shadow_casting_lights) < expected_value and len(shadow_casting_lights) > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_shadow_casting_light_count())
        issues_found = 0;
        patch_message = 'Your scene contains "' + str(len(shadow_casting_lights)) + '" shadow casting lights, which is a high number. \nConsider optimizing it if possible.'
        cancel_message= "Ignore Warning"
    elif len(shadow_casting_lights) < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('Your scene contains "' +str(len(shadow_casting_lights)) + '" shadow casting lights.')) 
        issues_found = 0;
        patch_message = ''
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_shadow_casting_light_count())
        issues_found = 1;
        patch_message = 'Your scene contains ' + str(len(shadow_casting_lights)) + ' shadow casting lights.\nTry to keep this number under ' + str(expected_value) + '.'
        cancel_message= "Ignore Issue"
        
    cmds.text("output_" + item_id, e=True, l=len(shadow_casting_lights) )
    
    # Patch Function ----------------------
    def warning_shadow_casting_light_count():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', cancel_message],
                    defaultButton='OK',
                    cancelButton=cancel_message,
                    dismissString=cancel_message, 
                    icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(str(issues_found) + ' issues found. Your scene contains ' + str(len(shadow_casting_lights)) +  ' shadow casting lights, which is a high number. \nConsider optimizing it if possible.') )
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if len(shadow_casting_lights) < expected_value and len(shadow_casting_lights) > inbetween_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' +  str(len(shadow_casting_lights)) + '" shadow casting lights, which is a high number. Consider optimizing it if possible.'
    elif len(shadow_casting_lights) < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(shadow_casting_lights)) + '" shadow casting lights.'
    else: 
        string_status = str(issues_found) + ' issue found. Your scene contains "' + str(len(shadow_casting_lights)) + '" shadow casting lights, you should keep this number under "' + str(expected_value) + '".'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    
# Item 9 - Redshift Shadow Casting Light Count =========================================================================
def check_rs_shadow_casting_light_count():
    item_name = checklist_items.get(9)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(9)[1][1]
    inbetween_value = checklist_items.get(9)[1][0]
    
    rs_physical_type = "RedshiftPhysicalLight" # Used to check if Redshift is loaded
    
    node_types = cmds.ls(nodeTypes=True)
    
    if rs_physical_type in node_types: # is RS loaded?
    
        rs_physical = cmds.ls(type=rs_physical_type)
        rs_photometric = cmds.ls(type="RedshiftIESLight")
        rs_portal = cmds.ls(type="RedshiftPortalLight")
        rs_dome = cmds.ls(type="RedshiftDomeLight")
        
        all_rs_lights = []
        all_rs_lights.extend(rs_physical)
        all_rs_lights.extend(rs_photometric)
        all_rs_lights.extend(rs_portal)
        all_rs_lights.extend(rs_dome)
        
        rs_shadow_casting_lights = []
       
        for rs_light in all_rs_lights:
            print(rs_light)
            if rs_light != "<done>":
                if cmds.objectType(rs_light) != "RedshiftPortalLight": # For some odd reason portal lights use an attribute called "shadows" instead of "shadow"
                    rs_shadow_state = cmds.getAttr (rs_light + ".shadow")
                else:
                    rs_shadow_state = cmds.getAttr (rs_light + ".shadows")
                if rs_shadow_state == 1:
                    rs_shadow_casting_lights.append(rs_light)
      
       
        if len(rs_shadow_casting_lights) < expected_value and len(rs_shadow_casting_lights) > inbetween_value:
            cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_rs_shadow_casting_light_count())
            issues_found = 0;
            patch_message = 'Your scene contains "' + str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights, which is a high number. \nConsider optimizing it if possible.'
            cancel_message= "Ignore Warning"
        elif len(rs_shadow_casting_lights) < expected_value:
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('Your scene contains "' +str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights.')) 
            issues_found = 0;
            patch_message = ''
        else: 
            cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_rs_shadow_casting_light_count())
            issues_found = 1;
            patch_message = 'Your scene contains ' + str(len(rs_shadow_casting_lights)) + ' Redshift shadow casting lights.\nTry to keep this number under ' + str(expected_value) + '.'
            cancel_message= "Ignore Issue"
            
        cmds.text("output_" + item_id, e=True, l=len(rs_shadow_casting_lights) )
        
        # Patch Function ----------------------
        def warning_rs_shadow_casting_light_count():
            user_input = cmds.confirmDialog(
                        title=item_name,
                        message= patch_message,
                        button=['OK', cancel_message],
                        defaultButton='OK',
                        cancelButton=cancel_message,
                        dismissString=cancel_message, 
                        icon="warning")

            if user_input == "Ignore Warning":
                cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(str(issues_found) + ' issues found. Your scene contains ' + str(len(rs_shadow_casting_lights)) +  ' Redshift shadow casting lights, which is a high number. \nConsider optimizing it if possible.') )
            else:
                cmds.button("status_" + item_id, e=True, l= '')
        
        # Return string for report ------------
        if len(rs_shadow_casting_lights) < expected_value and len(rs_shadow_casting_lights) > inbetween_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' +  str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights, which is a high number. Consider optimizing it if possible.'
        elif len(rs_shadow_casting_lights) < expected_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights.'
        else: 
            string_status = str(issues_found) + ' issue found. Your scene contains "' + str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights, you should keep this number under "' + str(expected_value) + '".'
        return '\n*** ' + item_name + " ***\n" + string_status
    else:
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('No Redshift light types exist in the scene. Redshift plugin doesn\'t seem to be loaded.', as_warning=True))
        cmds.text("output_" + item_id, e=True, l='No Redshift' )
        return '\n*** ' + item_name + " ***\n" + '0 issues found, but no Redshift light types exist in the scene. Redshift plugin doesn\'t seem to be loaded.'

# Item 10 - Arnold Shadow Casting Light Count =========================================================================
def check_ai_shadow_casting_light_count():
    item_name = checklist_items.get(10)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(10)[1][1]
    inbetween_value = checklist_items.get(10)[1][0]
    
    rs_physical_type = "aiAreaLight" # Used to check if Arnold is loaded
    
    node_types = cmds.ls(nodeTypes=True)

    if rs_physical_type in node_types: # is Arnold loaded?
    
        ai_sky_dome = cmds.ls(type="aiSkyDomeLight")
        ai_mesh = cmds.ls(type="aiMeshLight")
        ai_photometric = cmds.ls(type="aiPhotometricLight")
        ai_area = cmds.ls(type=rs_physical_type)
        #ai_portal = cmds.ls(type="aiLightPortal")
        
        all_ai_lights = []
        all_ai_lights.extend(ai_sky_dome)
        all_ai_lights.extend(ai_mesh)
        all_ai_lights.extend(ai_photometric)
        all_ai_lights.extend(ai_area)
        #all_ai_lights.extend(ai_portal)
        
        ai_shadow_casting_lights = []
       
        for ai_light in all_ai_lights :
            rs_shadow_state = cmds.getAttr (ai_light + ".aiCastShadows")
            if rs_shadow_state == 1:
                ai_shadow_casting_lights.append(ai_light)
      
       
        if len(ai_shadow_casting_lights) < expected_value and len(ai_shadow_casting_lights) > inbetween_value:
            cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_ai_shadow_casting_light_count())
            issues_found = 0;
            patch_message = 'Your scene contains "' + str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights, which is a high number. \nConsider optimizing it if possible.'
            cancel_message= "Ignore Warning"
        elif len(ai_shadow_casting_lights) < expected_value:
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('Your scene contains "' +str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights.')) 
            issues_found = 0;
            patch_message = ''
        else: 
            cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_ai_shadow_casting_light_count())
            issues_found = 1;
            patch_message = 'Your scene contains ' + str(len(ai_shadow_casting_lights)) + ' Arnold shadow casting lights.\nTry to keep this number under ' + str(expected_value) + '.'
            cancel_message= "Ignore Issue"
            
        cmds.text("output_" + item_id, e=True, l=len(ai_shadow_casting_lights) )
        
        # Patch Function ----------------------
        def warning_ai_shadow_casting_light_count():
            user_input = cmds.confirmDialog(
                        title=item_name,
                        message= patch_message,
                        button=['OK', cancel_message],
                        defaultButton='OK',
                        cancelButton=cancel_message,
                        dismissString=cancel_message, 
                        icon="warning")

            if user_input == "Ignore Warning":
                cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(str(issues_found) + ' issues found. Your scene contains ' + str(len(ai_shadow_casting_lights)) +  ' Arnold shadow casting lights, which is a high number. \nConsider optimizing it if possible.') )
            else:
                cmds.button("status_" + item_id, e=True, l= '')
        
        # Return string for report ------------
        if len(ai_shadow_casting_lights) < expected_value and len(ai_shadow_casting_lights) > inbetween_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' +  str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights, which is a high number. Consider optimizing it if possible.'
        elif len(ai_shadow_casting_lights) < expected_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights.'
        else: 
            string_status = str(issues_found) + ' issue found. Your scene contains "' + str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights, you should keep this number under "' + str(expected_value) + '".'
        return '\n*** ' + item_name + " ***\n" + string_status
    else:
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('No Arnold light types exist in the scene. Arnold plugin doesn\'t seem to be loaded.', as_warning=True))
        cmds.text("output_" + item_id, e=True, l='No Arnold' )
        return '\n*** ' + item_name + " ***\n" + '0 issues found, but no Arnold light types exist in the scene. Arnold plugin doesn\'t seem to be loaded.'

# Item 11 - Default Object Names ========================================================================= 
def check_default_object_names():
    item_name = checklist_items.get(11)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(11)[1]
    
    offending_objects = []
    possible_offenders = []

    default_object_names = ["nurbsSphere", "nurbsCube", "nurbsCylinder", "nurbsCone",\
     "nurbsPlane", "nurbsTorus", "nurbsCircle", "nurbsSquare", "pSphere", "pCube", "pCylinder",\
     "pCone", "pPlane", "pTorus", "pPrism", "pPyramid", "pPipe", "pHelix", "pSolid", "rsPhysicalLight",\
     "rsIESLight", "rsPortalLight", "aiAreaLight" ,"rsDomeLight", "aiPhotometricLight", "aiLightPortal", \
     "ambientLight", "directionalLight", "pointLight", "spotLight", "areaLight", "volumeLight"]
     
    all_objects = cmds.ls(lt=True, lf=True, g=True)
    
    
    for obj in all_objects:
        for def_name in default_object_names:
            if obj.startswith(def_name):
                offending_objects.append(obj)
            elif def_name in obj:
                possible_offenders.append(obj)
    
    # Manage Strings
    cancel_message = 'Ignore Issue'
    
    if len(possible_offenders) == 1:
        patch_message_warning = str(len(possible_offenders)) + ' object contains a string extremelly similar to the default names.\n(Ignore this warning if the name describes your object properly)'
    else:
        patch_message_warning = str(len(possible_offenders)) + ' objects contain a string extremelly similar to the default names.\n(Ignore this warning if the name describes your object properly)'
    
    if len(offending_objects) == 1:
        patch_message_error = str(len(offending_objects)) + ' object was not named properly. \nPlease rename your objects descriptively.'
    else:
        patch_message_error = str(len(offending_objects)) + ' objects were not named properly. \nPlease rename your objects descriptively.'
    
    # Manage Buttons
    if len(possible_offenders) != 0 and len(offending_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_default_object_names()) 
        issues_found = 0
    elif len(offending_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No unnamed objects were found, well done!')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_default_object_names())
        issues_found = len(offending_objects)
    
    # Manage Message
    patch_message = ''
            
    if len(possible_offenders) != 0 and len(offending_objects) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_offenders)) + ' ]' )
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
    elif len(possible_offenders) == 0 and len(offending_objects) != 0: 
        cmds.text("output_" + item_id, e=True, l=str(len(offending_objects)))
        patch_message = patch_message_error
    else:
        cmds.text("output_" + item_id, e=True, l=str(len(offending_objects)) + ' + [ ' + str(len(possible_offenders)) + ' ]' )
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        return_message = patch_message_error + '\n' + patch_message_warning
        
    # Patch Function ----------------------
    def warning_default_object_names():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', cancel_message],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: warning_default_object_names()) 
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_offenders) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in offending_objects: 
            string_status = string_status + '"' + obj +  '" was not named properly. Please rename your object descriptively.\n'
        if len(offending_objects) != 0 and len(possible_offenders) == 0:
            string_status = string_status[:-1]
        
        for obj in possible_offenders: 
            string_status = string_status + '"' + obj +  '"  contains a string extremelly similar to the default names.\n'
        if len(possible_offenders) != 0:
            string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No unnamed objects were found, well done!'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 12 - Objects Assigned to lambert1 =========================================================================
def check_objects_assigned_to_lambert1():
    item_name = checklist_items.get(12)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(12)[1]
    
    lambert1_objects = cmds.sets("initialShadingGroup", q=True) or []
    
    if len(lambert1_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No objects were assigned to lambert1.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_objects_assigned_to_lambert1())
        issues_found = len(lambert1_objects)
        
    cmds.text("output_" + item_id, e=True, l=len(lambert1_objects) )
    
    if len(lambert1_objects) == 1:
        patch_message = str(len(lambert1_objects)) + ' object is assigned to lambert1. \nMake sure no objects are assigned to lambert1.\n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(lambert1_objects)) + ' objects are assigned to lambert1. \nMake sure no objects are assigned to lambert1.\n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_objects_assigned_to_lambert1():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Ignore Issue'],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in lambert1_objects: 
            string_status = string_status + '"' + obj +  '"  is assigned to lambert1. It should be assigned to another shader.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No objects are assigned to lambert1.'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 13 - Ngons =========================================================================
def check_ngons():
    item_name = checklist_items.get(13)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(13)[1]
    


    ngon_mel_command = 'string $ngons[] = `polyCleanupArgList 3 { "1","2","1","0","1","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" }`;'
    ngons_list = mel.eval(ngon_mel_command)
    cmds.select(clear=True)
    
    print('') # Clear Any Warnings
 

    if len(ngons_list) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No ngons were found in your scene. Good job!')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_ngons())
        issues_found = len(ngons_list)
        
    cmds.text("output_" + item_id, e=True, l=len(ngons_list) )
    
    if len(ngons_list) == 1:
        patch_message = str(len(ngons_list)) + ' ngon found in your scene. \nMake sure no faces have more than 4 sides.\n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(ngons_list)) + ' ngons found in your scene. \nMake sure no faces have more than 4 sides.\n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_ngons():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Select Ngons', 'Ignore Issue' ],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == 'Select Ngons':
            ngons_list = mel.eval(ngon_mel_command)
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in ngons_list: 
            string_status = string_status + '"' + obj +  '"  is an ngon (face with more than 4 sides).\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No ngons were found in your scene.'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 14 - Non-manifold Geometry =========================================================================
def check_non_manifold_geometry():
    item_name = checklist_items.get(14)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(14)[1]
    
    nonmanifold_geo = []
    nonmanifold_verts = []
    
    all_geo = cmds.ls(type='mesh')
   
    for geo in all_geo:
        obj_non_manifold_verts = cmds.polyInfo(geo, nmv=True) or []
        if len(obj_non_manifold_verts) > 0:
            nonmanifold_geo.append(geo)
            nonmanifold_verts.append(obj_non_manifold_verts)

    if len(nonmanifold_geo) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No objects with non-manifold geometry in your scene. Well Done!')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_non_manifold_geometry())
        issues_found = len(nonmanifold_geo)
        
    cmds.text("output_" + item_id, e=True, l=len(nonmanifold_geo) )
    
    if len(nonmanifold_geo) == 1:
        patch_message = str(len(nonmanifold_geo)) + ' object with non-manifold geometry was found in your scene. \n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(nonmanifold_geo)) + ' objects with non-manifold geometry were found in your scene. \n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_non_manifold_geometry():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Select Non-manifold Vertices', 'Ignore Issue' ],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")
                    
        
        if user_input == 'Select Non-manifold Vertices':
            cmds.select(clear=True)
            for verts in nonmanifold_verts:
                    cmds.select(verts, add=True)
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in nonmanifold_geo: 
            string_status = string_status + '"' + obj +  '"  has non-manifold geometry.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No non-manifold geometry found in your scene.'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 15 - Empty UV Sets =========================================================================
def check_empty_uv_sets():
    item_name = checklist_items.get(15)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(15)[1]
    
    objects_extra_empty_uv_sets = []
    objects_single_empty_uv_sets = []
    
    all_geo = cmds.ls(type='mesh')
    
    for obj in all_geo:
        all_uv_sets = cmds.polyUVSet(obj, q=True, allUVSets=True)
        if len(all_uv_sets) > 1:
            for uv_set in all_uv_sets:
                uv_count = cmds.polyEvaluate(obj, uv=True, uvs=uv_set)
                if uv_count == 0:
                    objects_extra_empty_uv_sets.append(obj)
        else:
            for uv_set in all_uv_sets:
                uv_count = cmds.polyEvaluate(obj, uv=True, uvs=uv_set)
                if uv_count == 0:
                    objects_single_empty_uv_sets.append(obj)

    if len(objects_extra_empty_uv_sets) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No empty UV sets.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_empty_uv_sets())
        issues_found = len(objects_extra_empty_uv_sets)
        
    cmds.text("output_" + item_id, e=True, l=len(objects_extra_empty_uv_sets) )
    
    if len(objects_extra_empty_uv_sets) == 1:
        patch_message = str(len(objects_extra_empty_uv_sets)) + ' object found contaning multiple UV Sets and empty UV Sets. \n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(objects_extra_empty_uv_sets)) + ' objects found contaning multiple UV Sets and empty UV Sets. \n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_empty_uv_sets():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Select Objects with Empty UV Sets', 'Ignore Issue' ],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")
                    
        
        if user_input == 'Select Objects with Empty UV Sets':
            cmds.select(clear=True)
            for obj in objects_extra_empty_uv_sets:
                object_transform = cmds.listRelatives(obj, allParents=True, type='transform') or []
                print(object_transform)
                if len(object_transform) > 0:
                    cmds.select(object_transform, add=True)
                else:
                    cmds.select(obj, add=True)
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_extra_empty_uv_sets: 
            string_status = string_status + '"' + obj +  '" has multiple UV Sets and Empty UV Sets.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No geometry with multiple UV Sets and Empty UV Sets.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 16 - Frozen Transforms =========================================================================
def check_frozen_transforms():
    item_name = checklist_items.get(16)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(16)[1]
    
    objects_no_frozen_transforms = []
    
    all_transforms = cmds.ls(type='transform')
    
    # if it's a reference, ignore it
    # if it has an input connection, ignore it
    
    for transform in all_transforms:
        children = cmds.listRelatives(transform, c=True, pa=True) or []
        for child in children:
            object_type = cmds.objectType(child)
            #print(object_type)
            if object_type == 'mesh' or object_type == 'nurbsCurve':
                #print(cmds.getAttr(transform + ".rotateX"))
                if cmds.getAttr(transform + ".rotateX") != 0 or cmds.getAttr(transform + ".rotateY") != 0 or cmds.getAttr(transform + ".rotateZ") != 0:
                    objects_no_frozen_transforms.append(transform)
                       
    
    if len(objects_no_frozen_transforms) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No empty UV sets.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '?', c=lambda args: warning_frozen_transforms())
        issues_found = len(objects_no_frozen_transforms)
        
    cmds.text("output_" + item_id, e=True, l=len(objects_no_frozen_transforms) )
    
    if len(objects_no_frozen_transforms) == 1:
        patch_message = str(len(objects_no_frozen_transforms)) + ' object has un-frozen transformations. \n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(objects_no_frozen_transforms)) + ' objects have un-frozen transformations. \n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_frozen_transforms():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Select Objects with un-frozen transformations', 'Ignore Warning' ],
                    defaultButton='OK',
                    cancelButton='Ignore Warning',
                    dismissString='Ignore Warning', 
                    icon="warning")
                    
        if user_input == 'Select Objects with un-frozen transformations':
            cmds.select(objects_no_frozen_transforms)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '')
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_no_frozen_transforms: 
            string_status = string_status + '"' + obj +  '" has un-frozen transformations.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No objects have un-frozen transformations.'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 17 - Animated Visibility =========================================================================
def check_animated_visibility():
    item_name = checklist_items.get(17)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(17)[1]
    
    objects_animated_visibility = []
    objects_hidden = []
    
    all_transforms = cmds.ls(type='transform')
    
    for transform in all_transforms:
        attributes = cmds.listAttr(transform)
        if 'visibility' in attributes:
            if cmds.getAttr(transform + ".visibility") == 0:
                children = cmds.listRelatives(transform, s=True, pa=True)
                if len(children) != 0:
                    if cmds.nodeType(children[0]) != "camera":
                        objects_hidden.append(transform)
        input_nodes = cmds.listConnections(transform + ".visibility", destination=False, source=True) or []
        for node in input_nodes:
            if 'animCurve' in cmds.nodeType(node):
                objects_animated_visibility.append(transform)
            
    
    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []
    
    if len(objects_hidden) == 1:
        patch_message_warning = str(len(objects_hidden)) + ' object is hidden.\n'
    else:
        patch_message_warning = str(len(objects_hidden)) + ' objects are hidden.\n'
    
    if len(objects_animated_visibility) == 1:
        patch_message_error = str(len(objects_animated_visibility)) + ' object with animated visibility.\n'
    else:
        patch_message_error = str(len(objects_animated_visibility)) + ' objects with animated visibility.\n'
        
    # Manage Message
    patch_message = ''
            
    if len(objects_hidden) != 0 and len(objects_animated_visibility) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(objects_hidden)) + ' ]' )
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append('Select Hidden Objects')
    elif len(objects_hidden) == 0 and len(objects_animated_visibility) != 0: 
        cmds.text("output_" + item_id, e=True, l=str(len(objects_animated_visibility)))
        patch_message = patch_message_error
        buttons_to_add.append('Select Objects With Animated Visibility')
    else:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_animated_visibility)) + ' + [ ' + str(len(objects_hidden)) + ' ]' )
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append('Select Hidden Objects')
        buttons_to_add.append('Select Objects With Animated Visibility')
    
    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)
    
    # Manage State
    if len(objects_hidden) != 0 and len(objects_animated_visibility) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_animated_visibility()) 
        issues_found = 0
    elif len(objects_animated_visibility) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No objects with animated visibility or hidden.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_animated_visibility())
        issues_found = len(objects_animated_visibility)
    
        
    # Patch Function ----------------------
    def warning_animated_visibility():
        user_input = cmds.confirmDialog(
                    title= item_name,
                    message= patch_message,
                    button= assembled_message,
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")
                    
        if user_input == 'Select Objects With Animated Visibility':
            cmds.select(objects_animated_visibility)
        elif user_input == 'Select Hidden Objects':
            cmds.select(objects_hidden)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '')
        else:
            cmds.button("status_" + item_id, e=True, l= '')
        
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(objects_hidden) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_animated_visibility: 
            string_status = string_status + '"' + obj +  '" has animated visibility.\n'
        if len(objects_animated_visibility) != 0 and len(objects_hidden) == 0:
            string_status = string_status[:-1]
        
        for obj in objects_hidden: 
            string_status = string_status + '"' + obj +  '" is hidden.\n'
        if len(objects_hidden) != 0:
            string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No unnamed objects were found, well done!'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    
    

# Item 18 - Non Deformer History =========================================================================
def check_non_deformer_history():
    item_name = checklist_items.get(18)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(18)[1]
    
    objects_non_deformer_history = []
    objects_single_frozen_transforms = []
    
    all_transforms = cmds.ls(type='transform')
    
    for transform in all_transforms:
        # Check if visibility exists
        transform
        if cmds.getAttr(transform + ".visibility") == 0:
            pass
    
    #  // Check for non deformer history
    # if ((`radioButtonGrp -q -sl historyState`) == 1)
    # {
    #     fprint $fileId "***Non-deformer History Check***\r\n\r\n";
    #     string $histSel[] = `ls -typ nurbsSurface -typ mesh -typ subdiv -typ nurbsCurve`;
    #     int $nonDefHistoryCount = 0;
        
    #     for ($myHistSel in $histSel)
        
    #     {
    #         string $myHistSelList[] = `listHistory -pdo 1 $myHistSel`;
    #         string $myHistSelListString = stringArrayToString( $myHistSelList , ", ");
    #         if (size($myHistSelList) > 0)
    #         {
    #             for ($myHistSelListItem in $myHistSelList)
    #             {
    #                 if ((`nodeType $myHistSelListItem` == "tweak")||(`nodeType $myHistSelListItem` == "expression")||(`nodeType $myHistSelListItem` == "unitConversion")||(`nodeType $myHistSelListItem` == "time")||(`nodeType $myHistSelListItem` == "objectSet")||(`nodeType $myHistSelListItem` == "reference")||(`nodeType $myHistSelListItem` == "polyTweak")||(`nodeType $myHistSelListItem` == "blendShape")||(`nodeType $myHistSelListItem` == "groupId")||(`nodeType $myHistSelListItem` == "renderLayer")||(`nodeType $myHistSelListItem` == "renderLayerManager")||(`nodeType $myHistSelListItem` == "shadingEngine")||(`nodeType $myHistSelListItem` == "displayLayer")||(`nodeType $myHistSelListItem` == "skinCluster")||(`nodeType $myHistSelListItem` == "groupParts")||(`nodeType $myHistSelListItem` == "mentalraySubdivApprox"))
    #                 {
    #                     //print ($myHistSel + " has " + $myHistSelListItem + " in it's history history. You should fix this.\n");
    #                 }
    #                 else
    #                 {
    #                     $nonDefHistoryCount ++;
    #                     fprint $fileId ($myHistSel + " has " + $myHistSelListItem + " in it's history history. You should fix this.\r\n");
    #                     print ($myHistSel + " has " + $myHistSelListItem + " in it's history history. You should fix this.\n");
    #                 }
    #             }
    #         }
    #     }
    #     ;
    #     fprint $fileId "\r\n";
    #     if ($nonDefHistoryCount > 0)
    #     {
    #         if ($nonDefHistoryCount > 1)
    #         {
    #             fprint $fileId ("There are " + $nonDefHistoryCount + " objects in your scene with non-deformer history.\r\n");
    #             print ("There are " + $nonDefHistoryCount + " objects in your scene with non-deformer history.\n");
    #         }
    #         else
    #         {
    #             fprint $fileId ("There is " + $nonDefHistoryCount + " object in your scene with non-deformer history.\r\n");
    #             print ("There is " + $nonDefHistoryCount + " object in your scene with non-deformer history.\n");
    #         }
            
    #     }
    #     else
    #     {
    #         fprint $fileId ("Not objects were found with non-deformer history in your scene. Well Done!.\r\n");
    #         print ("Not objects were found with non-deformer history in your scene. Well Done!.\n");
    #     }
    #     fprint $fileId "\r\n";
    
    for transform in all_transforms:
        children = cmds.listRelatives(transform, c=True, pa=True) or []
        for child in children:
            object_type = cmds.objectType(child)
            #print(object_type)
            if object_type == 'mesh' or object_type == 'nurbsCurve':
                if cmds.getAttr(transform + ".rotateX") != 0 or cmds.getAttr(transform + ".rotateY") != 0 or cmds.getAttr(transform + ".rotateZ") != 0:
                    objects_non_deformer_history.append(transform)
                       
    

    if len(objects_non_deformer_history) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No empty UV sets.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_non_deformer_history())
        issues_found = len(objects_non_deformer_history)
        
    cmds.text("output_" + item_id, e=True, l=len(objects_non_deformer_history) )
    
    if len(objects_non_deformer_history) == 1:
        patch_message = str(len(objects_non_deformer_history)) + ' object has un-frozen transformations. \n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(objects_non_deformer_history)) + ' objects have un-frozen transformations. \n\n(Too see a list of objects, generate a full report)'
    
    # Patch Function ----------------------
    def warning_non_deformer_history():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message= patch_message,
                    button=['OK', 'Select Objects with un-frozen transformations', 'Ignore Warning' ],
                    defaultButton='OK',
                    cancelButton='Ignore Warning',
                    dismissString='Ignore Warning', 
                    icon="warning")
                    
        if user_input == 'Select Objects with un-frozen transformations':
            cmds.select(objects_non_deformer_history)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '')
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_non_deformer_history: 
            string_status = string_status + '"' + obj +  '" has un-frozen transformations.\n'
        string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No objects have un-frozen transformations.'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    

# Checklist Functions End Here ===================================================================


def print_message(message, as_warning=False):
    if as_warning:
        cmds.warning(message)
    else:
        print(message)

def export_to_txt(list):
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp.txt';
    
    f = open(txtFile,'w')
    
    output_string = checklist_name + " Full Report:\n"
    
    for obj in list:
        output_string = output_string + obj + "\n\n"
    
    f.write(output_string)
    f.close()

    notepadCommand = 'exec("notepad ' + txtFile + '");'
    mel.eval(notepadCommand)

# WIP
def save_state():
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp_state.txt';
    
    file_handle = open(txtFile,'w')
    

    selectCommand = "test"

    file_handle.write(selectCommand)
    file_handle.close()

    notepadCommand = 'exec("notepad ' + txtFile + '");'
    mel.eval(notepadCommand)

# WIP
def load_state():
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp_state.txt';
    
    file_handle = open(txtFile,'r')
    
    str1 = file_handle.read()
    file_handle.close()
    print str1


#Build GUI
build_gui_checklist()