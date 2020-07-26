"""

 Modeling 1 - Kitchen Checklist
 This script is a modified version of my script "GT Render Checklist" used to check a modeling assignment
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-07-25 - github.com/TrevisanGMW

 For updated versions, check Moodle or my Github.
    
"""
import maya.cmds as cmds
import maya.mel as mel
import copy
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
script_name = "Modeling 1 - Kitchen Checklist" 

# Version
script_version = "1.0";

# Status Colors
def_color = 0.3, 0.3, 0.3
pass_color = (0.17, 1.0, 0.17)
warning_color = (1.0, 1.0, 0.17)
error_color = (1.0, 0.17, 0.17)
exception_color = 0.2, 0.2, 0.2

# Checklist Items - Item Number [Name, Expected Value]
checklist_items = { #0 Removed
                    1 : ["Scene Units", "cm"],
                    2 : ["Output Resolution", ["1280","720"] ], # Modified
                    3 : ["Total Texture Count", [40, 50] ],
                    4 : ["File Paths", ["sourceimages"] ], # Modified
                    #5 Removed 
                    6 : ["Unparented Objects", 0],
                    7 : ["Total Triangle Count", [1800000, 2000000] ],
                    8 : ["Total Poly Object Count", [90, 100] ],
                    #9 Removed
                   10 : ["RS Shadow Casting Lights", [3, 4]],
                   #11 Removed
                   12 : ["Default Object Names", 0],
                   13 : ["Objects Assigned to lambert1", 0],
                   14 : ["Ngons", 0],
                   15 : ["Non-manifold Geometry", 0],
                   #16 Removed
                   17 : ["Frozen Transforms", 0],
                   18 : ["Animated Visibility", 0],
                   19 : ["Non Deformer History", 0 ],
                   20 : ["Textures Color Space", 0 ],
                   #21 Removed
                  }

# Store Default Values for Reseting
settings_default_checklist_values = copy.deepcopy(checklist_items)

# Checklist Settings
checklist_settings = { "is_settings_visible" : False,
                       "checklist_column_height" : 0,
                       "checklist_buttons_height" : 0,
                       "settings_text_fields" : []
                     }


# Build GUI - Main Function ==================================================================================
def build_gui_gt_m1_kitchen_checklist():
    window_name = "build_gui_gt_m1_kitchen_checklist"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + "  v" + script_version, mnb=False, mxb=False, s=True)

    main_column = cmds.columnLayout()

    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, h=1, w=1)
    
    # Title Text
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.separator(h=14, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 240), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=main_column)

    cmds.text(" ", bgc=[0,.5,0])
    cmds.text(script_name, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_gt_m1_kitchen_checklist())
    cmds.separator(h=10, style='none', p=main_column) # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column) # For the separator
    cmds.separator(h=8)
    cmds.separator(h=5, style='none') # Empty Space
    
    # Settings Column  ==========================================================
    settings_column = cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 0)], h=1, p=main_column) 
    
    cmds.rowColumnLayout(nc=3, cw=[(1, 150), (2, 65), (3, 63)], cs=[(1, 19), (2, 6), (3, 6)])
    
    # Header
    cmds.text(l="Operation", align="left")
    cmds.text(l='Warning', align="center")
    cmds.text(l='Expected', align="center")
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')

 
    # Checklist Column  ==========================================================
    checklist_column = cmds.rowColumnLayout(nc=3, cw=[(1, 165), (2, 35), (3, 90)], cs=[(1, 20), (2, 6), (3, 6)], p=main_column) 
    
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

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column) # For the separator
    cmds.separator(h=8, style='none') # Empty Space
    cmds.separator(h=8)
    

    # Checklist Buttons ==========================================================
    checklist_buttons = cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
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

    # Main GUI Ends ==========================================================

    


def checklist_refresh():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)
    
    #Removed
    check_scene_units()
    check_output_resolution()
    check_total_texture_count()
    check_network_file_paths()
    #Removed
    check_unparented_objects()  
    check_total_triangle_count()
    check_total_poly_object_count()
    #Removed
    check_rs_shadow_casting_light_count()
    #Removed
    check_default_object_names()
    check_objects_assigned_to_lambert1()
    check_ngons()
    check_non_manifold_geometry()
    #Removed
    check_frozen_transforms()
    check_animated_visibility()
    check_non_deformer_history()
    check_textures_color_space()
    #Removed
    
    # Clear Selection
    cmds.selectMode( object=True )
    cmds.select(clear=True)
    
    # Reselect Previous Selection
    cmds.select(current_selection)
    

def checklist_generate_report():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)
    
    report_strings = []
    #Removed
    report_strings.append(check_scene_units())
    report_strings.append(check_output_resolution())
    report_strings.append(check_total_texture_count())
    report_strings.append(check_network_file_paths())
    #Removed
    report_strings.append(check_unparented_objects())
    report_strings.append(check_total_triangle_count())
    report_strings.append(check_total_poly_object_count())
    #Removed
    report_strings.append(check_rs_shadow_casting_light_count())
    #Removed
    report_strings.append(check_default_object_names())
    report_strings.append(check_objects_assigned_to_lambert1())
    report_strings.append(check_ngons())
    report_strings.append(check_non_manifold_geometry())
    #Removed
    report_strings.append(check_frozen_transforms())
    report_strings.append(check_animated_visibility())
    report_strings.append(check_non_deformer_history())
    report_strings.append(check_textures_color_space())
    #Removed
    
    # Clear Selection
    cmds.selectMode( object=True )
    cmds.select(clear=True)
    
    # Show Report
    export_report_to_txt(report_strings)
    
    # Reselect Previous Selection
    cmds.select(current_selection)
    

    
# Creates Help GUI
def build_gui_help_gt_m1_kitchen_checklist():
    window_name = "build_gui_help_gt_m1_kitchen_checklist"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    # Body ====================
    checklist_spacing = 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script performs a series of checks to detect common', align="left")
    cmds.text(l='issues that are often accidently ignored/unnoticed for', align="left")
    cmds.text(l='the kitchen assignment in Modeling 1 - Term 1.', align="left")
    # Checklist Status =============
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Checklist Status:', align="left", fn="boldLabelFont") 
    cmds.text(l='These are also buttons, you can click on them for extra functions:', align="left", fn="smallPlainLabelFont") 
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 35),(2, 265)], cs=[(1, 10),(2, 10)], p="main_column")
    cmds.button(l='', h=14, bgc=def_color, c=lambda args: print_message('Default color, means that it was not yet tested.', as_heads_up_message=True))
    cmds.text(l='- Default color, not yet tested.', align="left", fn="smallPlainLabelFont") 
    
    cmds.button(l='', h=14, bgc=pass_color, c=lambda args: print_message('Pass color, means that no issues were found.', as_heads_up_message=True))
    cmds.text(l='- Pass color, no issues were found.', align="left", fn="smallPlainLabelFont") 
    
    cmds.button(l='', h=14, bgc=warning_color, c=lambda args: print_message('Warning color, some possible issues were found', as_heads_up_message=True))
    cmds.text(l='- Warning color, some possible issues were found', align="left", fn="smallPlainLabelFont") 
    
    cmds.button(l='', h=14, bgc=error_color, c=lambda args: print_message('Error color, means that some possible issues were found', as_heads_up_message=True))
    cmds.text(l='- Error color, issues were found.', align="left", fn="smallPlainLabelFont") 
    
    cmds.button(l='', h=14, bgc=exception_color, c=lambda args: print_message('Exception color, an issue caused the check to fail. Likely because of a missing plug-in or unexpected value', as_heads_up_message=True))
    cmds.text(l='- Exception color, an issue caused the check to fail.', align="left", fn="smallPlainLabelFont") 
    
    cmds.button(l='?', h=14, bgc=def_color, c=lambda args: print_message('Question mask, click on button for more help. It often gives you extra options regarding the found issues.', as_heads_up_message=True))
    cmds.text(l='- Question mask, click on button for more help.', align="left", fn="smallPlainLabelFont") 
    
    cmds.separator(h=15, style='none') # Empty Space

    # Checklist Items =============
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='Checklist Items and Guidelines:', align="left", fn="boldLabelFont") 
    cmds.separator(h=checklist_spacing, style='none') # Empty Space
   
    # Create Help List: 
    font_size ='smallPlainLabelFont'
    items_for_settings = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11] # Allow user to update expected values
    items_with_warnings = [3, 7, 8, 9, 10, 11] # Allow users to update warning values too
    
    checklist_items_help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="smallPlainLabelFont")
 
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(1)[0] +': returns error if not matching: "' + str(checklist_items.get(1)[1]) + '".\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(2)[0] +': returns error if none of the values match:\n    ' + str(checklist_items.get(2)[1])+ '. For more information check the guidelines for\n    this assignment. It expects your height or width to match\n    the expected value, so force the image to not be too small\n    or too big.\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(3)[0] +': error if more than ' + str(checklist_items.get(3)[1][1]) +  '\n     warning if more than ' + str(checklist_items.get(3)[1][0])+ '.\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(4)[0] +': must contain ' + str(checklist_items.get(4)[1])+ ' in its path.\n     This is to make sure a Maya project is being used.\n\n')
 
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(6)[0] +': returns error if common objects are\n     found outside hierarchies' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(7)[0] +': : error if more than ' + str(checklist_items.get(7)[1][1]) + '\n     warning if more than: ' + str(checklist_items.get(7)[1][0]) + '.' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(8)[0] +': error if more than ' + str(checklist_items.get(8)[1][1])  + '\n     warning if more than ' + str(checklist_items.get(8)[1][0]) + '\n\n')   

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(10)[0] +': error if more than ' + str(checklist_items.get(10)[1][1]) + '\n     warning if more than ' + str(checklist_items.get(10)[1][0]) + '.' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(12)[0] +': error if using default names.' + '\n  warning if containing default names.\n    Examples of default names:\n      "pCube1" = Error\n      "pointLight1" = Error\n      "nurbsPlane1" = Error\n      "my_pCube" = Warning\n\n')  

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(13)[0] +': error if anything is assigned.\n\n') 
        
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(14)[0] +': error if any ngons found.\n     A polygon that is made up of five or more vertices. \n     Anything over a quad (4 sides) is considered an ngon\n\n') 
         
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(15)[0] +': error if is found.\n    A non-manifold geometry is a 3D shape that cannot be\n    unfolded into a 2D surface with all its normals pointing\n    the same direction.\n    For example, objects with faces inside of it.\n\n')
     
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(17)[0] +': error if rotation(XYZ) not frozen.' + '\n     It doesn\'t check objects with incoming connections,\n     for example, animations or rigs.' + '\n\n')
     
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(18)[0] +': error if animated visibility is found' + '\n     warning if hidden object is found.' + '\n\n') 
    
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(19)[0] +': error if any non-deformer history found.' + '\n\n') 
   
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(20)[0] +': error if incorrect color space found.' + '\n     It only checks common nodes for Redshift and Arnold\n     Generally "sRGB" -> float3(color), and "Raw" -> float(value).\n\n')
    
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='\n\n\n\n            Guidelines: (Same as Moodle)\n\n - Part 1 Render Submission:\n\n1. You going to render out two sets of images. One with surfaced only, the other with wireframe over shading.\n\n2. Renders should be (720HD) Renders\n\n3. Use the same Angles for Surfaced and wireframe renders. (best to key your camera in different areas)\n\n4. Render out a Hi Quality image using the render Camera we set up during the beginning of the term\n\n5. Render out 3 more additional angles of your set, focusing on some of the detail and assets you built the term.\n\n6. Composite your reference image and render camera images together, one for modeling, and one for surfacing.\n\n7. Name should be (class#, name, course name, Project, image number.jpeg)  example (3D134_JohnSmith_Modeling_KitchenSet.01.jpg)\n\n8. Repeat this process for the other images.\n\n9. Comp relative reference together with the additional renders.  \n\n10. Use the available asset image templates to organize your images. (Recommended 2K)\n\n')
    
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='\n\n - Part 2 Project Clean up and Archiving:\n\n1. Use the file path editor (windows-general-file path editor) to make sure all your textures are located in you current project.\n\n2.Clean up the most recent scene.  (delete history, freeze transforms, delete empty group nodes)\n\n3.Clean up the Hypershade library (in the Hypershade Edit-Delete unused nodes.)\n\n4.Make sure display layers are used correctly (do they contain the right Pieces of geo in them, and do they make sense.)\n\n5.Archive your scene. (this will make a zip file containing your scene and textures)\n\n\nPlease visit Moodle for more information on your Guidelines. There you\'ll find step by step what to do.')
    
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=1, it='') # Bring Back to the Top

    cmds.separator(h=checklist_spacing, style='none') # Empty Space
   
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='  Issues when using the script?  Please contact me :', align="left")
    

    # Footer =============
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=5, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    

# Checklist Functions Start Here ================================================================

   

# Item 1 - Scene Units =========================================================================
def check_scene_units():
    item_name = checklist_items.get(1)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(1)[1]
    received_value = cmds.currentUnit( query=True, linear=True )
    issues_found = 0

    if received_value.lower() == str(expected_value).lower():
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "'  + str(received_value) + '".')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: patch_scene_units())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=str(received_value).capitalize() )
    
    # Patch Function ----------------------
    def patch_scene_units():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Do you want to change your ' + item_name.lower() + ' from "' + str(received_value) + '" to "' + str(expected_value).capitalize() + '"?',
                    button=['Yes, change it for me', 'Ignore Issue'],
                    defaultButton='Yes, change it for me',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="question")

        if user_input == 'Yes, change it for me':
            try:
                cmds.currentUnit( linear=str(expected_value ))
                print("Your " + item_name.lower() + " was changed to " + str(expected_value))
            except:
                cmds.warning('Failed to use custom setting "' + str(expected_value) +  '"  as your new scene unit.')
            check_scene_units()
        else:
            cmds.button("status_" + item_id, e=True, l= '')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "'  + str(expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "'  + str(expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 2 - Output Resolution (MODIFIED) =========================================================================
def check_output_resolution():
    item_name = checklist_items[2][0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items[2][1]
    
    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value, list):
        if len(expected_value) < 2:
            custom_settings_failed = True
            expected_value = settings_default_checklist_values[2][1]
            
    received_value = [cmds.getAttr("defaultResolution.width"), cmds.getAttr("defaultResolution.height")]
    issues_found = 0
    
    is_resolution_valid = False
    
    if str(received_value[0]) == str(expected_value[0]) or str(received_value[1]) == str(expected_value[1]):
        is_resolution_valid=True
    

    if is_resolution_valid:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "' + str(received_value[0]) + 'x' + str(received_value[1]) + '".')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: patch_output_resolution())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=str(received_value[0]) + 'x' + str(received_value[1]) )
    
    # Patch Function ----------------------
    def patch_output_resolution():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message='Either your height or width should match the resolution from the guidelines. \nIt doesn\'t need to be both!\nSo make sure you turn on the option "Maintain the width/height ratio" and make at least one of them match to ensure that your render is not too small, or too big.\nPlease make your width "' + str(expected_value[0]) + '" or your height "' + str(expected_value[1]) + '" and try again.',
                    button=['OK', 'Ignore Issue'],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")  

        if user_input == 'OK':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l= '')
            
    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "'  + str(expected_value[0]) + 'x' + str(expected_value[1]) + '" and yours is "' + str(received_value[0]) + 'x' + str(received_value[1]) + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "'  + str(expected_value[0]) + 'x' + str(expected_value[1]) + '" and yours is "' + str(received_value[0]) + 'x' + str(received_value[1]) + '"'
    if custom_settings_failed:
        string_status = '1 issue found. The custom resolution settings provided couldn\'t be used to check your resolution'
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('The custom value provided couldn\'t be used to check the resolution.', as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 3 - Total Texture Count =========================================================================
def check_total_texture_count():
    item_name = checklist_items.get(3)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(3)[1] 

    received_value = 0 
    issues_found = 0

    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value[0], int) == False or isinstance(expected_value[1], int) == False:
        custom_settings_failed = True


    # Count Textures
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        uv_tiling_mode = cmds.getAttr(file + '.uvTilingMode')
        if uv_tiling_mode != 0:
            use_frame_extension = cmds.getAttr(file + '.useFrameExtension')
            file_path = cmds.getAttr(file + ".fileTextureName")
            udim_file_pattern = maya.app.general.fileTexturePathResolver.getFilePatternString(file_path, use_frame_extension, uv_tiling_mode)
            udim_textures = maya.app.general.fileTexturePathResolver.findAllFilesForPattern(udim_file_pattern, None)
            received_value +=len(udim_textures)
        else:
            received_value +=1
        
    
    # Manager Message
    patch_message = 'Your ' + item_name.lower() + ' should be reduced from "' + str(received_value) + '" to less than "' + str(expected_value[1]) + '".\n (UDIM tiles are counted as individual textures)'
    cancel_button = 'Ignore Issue'
    
    
    if received_value <= expected_value[1] and received_value > expected_value[0]:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_total_texture_count()) 
        patch_message = 'Your ' + item_name.lower() + ' is "' + str(received_value) + '" which is a high number.\nConsider optimizing. (UDIM tiles are counted as individual textures)'
        cancel_button = 'Ignore Warning'
        issues_found = 0
    elif received_value <= expected_value[1]:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "'  + str(received_value) + '". (UDIM tiles are counted as individual textures)')) 

        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_total_texture_count())
        issues_found = 1
        
    cmds.text("output_" + item_id, e=True, l=received_value )
    

    # Patch Function ----------------------
    def warning_total_texture_count():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message=patch_message,
                    button=['OK', cancel_button],
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")

        if user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, l= '', bgc=pass_color)
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was less than "'  + str(expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    else: 
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was less than "'  + str(expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    if custom_settings_failed:
        string_status = '1 issue found. The custom value provided couldn\'t be used to check your total texture count'
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('The custom value provided couldn\'t be used to check your total texture count', as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status
    
# Item 4 - File Paths (MODIFIED) =========================================================================
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
            file_path_no_slashes = file_path.lower()#.replace('/','').replace('\\','')
            for valid_path in expected_value:
                #if not file_path_no_slashes.startswith(valid_path.replace('/','').replace('\\','')):
                if valid_path not in file_path_no_slashes:
                    incorrect_file_nodes.append(file)
        else:
            incorrect_file_nodes.append(file)


    if len(incorrect_file_nodes) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('All file nodes seem to be currently sourced from the sourceimages folder.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_network_file_paths())
        issues_found = len(incorrect_file_nodes)
        
    cmds.text("output_" + item_id, e=True, l=len(incorrect_file_nodes) )
    
    # Patch Function ----------------------
    def warning_network_file_paths():
        user_input = cmds.confirmDialog(
                    title=item_name,
                    message=str(len(incorrect_file_nodes)) + ' of your file node paths aren\'t pointing to a "sourceimages" folder. \nPlease change their path to make sure the files are inside the "sourceimages" folder. \n\n(Too see a list of nodes, generate a full report)',
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
            string_status = string_status + '"' + file_node +  '" isn\'t pointing to the a "sourceimages" folder. Your texture files should be sourced from a proper Maya project.\n'
    else: 
        string_status = str(issues_found) + ' issues found. All textures were sourced from the network'
    return '\n*** ' + item_name + " ***\n" + string_status


    
# Item 6 - Unparented Objects =========================================================================
def check_unparented_objects():
    item_name = checklist_items.get(6)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(6)[1]
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


# Item 7 - Total Triangle Count =========================================================================
def check_total_triangle_count():
    item_name = checklist_items.get(7)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(7)[1][1]
    inbetween_value = checklist_items.get(7)[1][0]
    unparented_objects = []
    
    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value, int) == False or isinstance(inbetween_value, int) == False:
        custom_settings_failed = True

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
        patch_message = 'Your scene has ' + str(scene_tri_count) + ' triangles. You should try to keep it under ' + str(expected_value) + '.\n\n' + 'In case you see a different number on your "Heads Up Display > Poly Count" option.  It\'s likely that you have "shapeOrig" nodes in your scene. These are intermediate shape nodes usually created by deformers. If you don\'t have deformations on your scene, you can delete these to reduce triangle count.\n'
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
    if custom_settings_failed:
        string_status = '1 issue found. The custom value provided couldn\'t be used to check your total triangle count'
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('The custom value provided couldn\'t be used to check your total triangle count', as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status

# Item 8 - Total Poly Object Count =========================================================================
def check_total_poly_object_count():
    item_name = checklist_items.get(8)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(8)[1][1]
    inbetween_value = checklist_items.get(8)[1][0]
    
    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) == False or isinstance(inbetween_value, int) == False:
        custom_settings_failed = True
    
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
    if custom_settings_failed:
        string_status = '1 issue found. The custom value provided couldn\'t be used to check your total poly count'
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('The custom value provided couldn\'t be used to check your total poly count', as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status
    
    

    
# Item 10 - Redshift Shadow Casting Light Count =========================================================================
def check_rs_shadow_casting_light_count():
    item_name = checklist_items.get(10)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(10)[1][1]
    inbetween_value = checklist_items.get(10)[1][0]
    
    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) == False or isinstance(inbetween_value, int) == False:
        custom_settings_failed = True
    
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
        if custom_settings_failed:
            string_status = '1 issue found. The custom value provided couldn\'t be used to check your Redshift shadow casting lights.'
            cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('The custom value provided couldn\'t be used to check your Redshift shadow casting lights.', as_warning=True))
        return '\n*** ' + item_name + " ***\n" + string_status
    else:
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l= '', c=lambda args: print_message('No Redshift light types exist in the scene. Redshift plugin doesn\'t seem to be loaded.', as_warning=True))
        cmds.text("output_" + item_id, e=True, l='No Redshift' )
        return '\n*** ' + item_name + " ***\n" + '0 issues found, but no Redshift light types exist in the scene. Redshift plugin doesn\'t seem to be loaded.'



# Item 12 - Default Object Names ========================================================================= 
def check_default_object_names():
    item_name = checklist_items.get(12)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(12)[1]
    
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
    cancel_message = 'Ignore Issue'
            
    if len(possible_offenders) != 0 and len(offending_objects) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_offenders)) + ' ]' )
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
    elif len(possible_offenders) == 0:
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


# Item 13 - Objects Assigned to lambert1 =========================================================================
def check_objects_assigned_to_lambert1():
    item_name = checklist_items.get(13)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(13)[1]
    
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

# Item 14 - Ngons =========================================================================
def check_ngons():
    item_name = checklist_items.get(14)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(14)[1]
    


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

# Item 15 - Non-manifold Geometry =========================================================================
def check_non_manifold_geometry():
    item_name = checklist_items.get(15)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(15)[1]
    
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


# Item 17 - Frozen Transforms =========================================================================
def check_frozen_transforms():
    item_name = checklist_items.get(17)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(17)[1]
    
    objects_no_frozen_transforms = []
    
    all_transforms = cmds.ls(type='transform')
        
    for transform in all_transforms:
        children = cmds.listRelatives(transform, c=True, pa=True) or []
        for child in children:
            object_type = cmds.objectType(child)
            if object_type == 'mesh' or object_type == 'nurbsCurve':
                if cmds.getAttr(transform + ".rotateX") != 0 or cmds.getAttr(transform + ".rotateY") != 0 or cmds.getAttr(transform + ".rotateZ") != 0:
                    if len(cmds.listConnections(transform + ".rotateX") or []) == 0 and len(cmds.listConnections(transform + ".rotateY") or []) == 0 and len(cmds.listConnections(transform + ".rotateZ") or []) == 0 and len(cmds.listConnections(transform + ".rotate") or []) == 0:
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

# Item 18 - Animated Visibility =========================================================================
def check_animated_visibility():
    item_name = checklist_items.get(18)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(18)[1]
    
    objects_animated_visibility = []
    objects_hidden = []
    
    all_transforms = cmds.ls(type='transform')
    
    for transform in all_transforms:
        attributes = cmds.listAttr(transform)
        if 'visibility' in attributes:
            if cmds.getAttr(transform + ".visibility") == 0:
                children = cmds.listRelatives(transform, s=True, pa=True) or []
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
    elif len(objects_hidden) == 0:
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
    
    
    

# Item 19 - Non Deformer History =========================================================================
def check_non_deformer_history():
    item_name = checklist_items.get(19)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(19)[1]
    
    objects_non_deformer_history = []
    possible_objects_non_deformer_history = []
    

    objects_to_check = []
    objects_to_check.extend(cmds.ls(typ='nurbsSurface') or [])
    objects_to_check.extend(cmds.ls(typ='mesh') or [])
    objects_to_check.extend(cmds.ls(typ='subdiv') or [])
    objects_to_check.extend(cmds.ls(typ='nurbsCurve') or [])
    
    not_history_nodes = ['tweak', 'expression', 'unitConversion', 'time', 'objectSet', 'reference', 'polyTweak', 'blendShape', 'groupId', \
    'renderLayer', 'renderLayerManager', 'shadingEngine', 'displayLayer', 'skinCluster', 'groupParts', 'mentalraySubdivApprox', 'proximityWrap',\
    'cluster', 'cMuscleSystem', 'timeToUnitConversion', 'deltaMush', 'tension', 'wire', 'wrinkle', 'softMod', 'jiggle', 'diskCache', 'leastSquaresModifier']
    
    possible_not_history_nodes = ['nonLinear','ffd', 'curveWarp', 'wrap', 'shrinkWrap', 'sculpt', 'textureDeformer']
    
    # Find Offenders
    for obj in objects_to_check:
        history = cmds.listHistory(obj, pdo=1) or []
        #Convert to string?
        for node in history:
            if cmds.nodeType(node) not in not_history_nodes and cmds.nodeType(node) not in possible_not_history_nodes:
                if obj not in objects_non_deformer_history:
                    objects_non_deformer_history.append(obj)
            if cmds.nodeType(node) in possible_not_history_nodes:
                if obj not in possible_objects_non_deformer_history:
                    possible_objects_non_deformer_history.append(obj)


    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []
    
    if len(possible_objects_non_deformer_history) == 1:
        patch_message_warning = str(len(possible_objects_non_deformer_history)) + ' object contains deformers often used for modeling.\n'
    else:
        patch_message_warning = str(len(possible_objects_non_deformer_history)) + ' objects contain deformers often used for modeling.\n'
    
    if len(objects_non_deformer_history) == 1:
        patch_message_error = str(len(objects_non_deformer_history)) + ' object contains non-deformer history.\n'
    else:
        patch_message_error = str(len(objects_non_deformer_history)) + ' objects contain non-deformer history.\n'
        
    # Manage Message
    patch_message = ''
            
    if len(possible_objects_non_deformer_history) != 0 and len(objects_non_deformer_history) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_objects_non_deformer_history)) + ' ]' )
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append('Select Objects With Suspicious Deformers')
    elif len(possible_objects_non_deformer_history) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_non_deformer_history)))
        patch_message = patch_message_error
        buttons_to_add.append('Select Objects With Non-deformer History')
    else:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_non_deformer_history)) + ' + [ ' + str(len(possible_objects_non_deformer_history)) + ' ]' )
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append('Select Objects With Suspicious Deformers')
        buttons_to_add.append('Select Objects With Non-deformer History')
    
    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)
    
    # Manage State
    if len(possible_objects_non_deformer_history) != 0 and len(objects_non_deformer_history) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_non_deformer_history()) 
        issues_found = 0
    elif len(objects_non_deformer_history) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No objects with non-deformer history were found.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_non_deformer_history())
        issues_found = len(objects_non_deformer_history)

    # Patch Function ----------------------
    def warning_non_deformer_history():
        user_input = cmds.confirmDialog(
                    title= item_name,
                    message= patch_message,
                    button= assembled_message,
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")
                    
        if user_input == 'Select Objects With Non-deformer History':
            cmds.select(objects_non_deformer_history)
        elif user_input == 'Select Objects With Suspicious Deformers':
            cmds.select(possible_objects_non_deformer_history)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '')
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_objects_non_deformer_history) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_non_deformer_history: 
            string_status = string_status + '"' + obj +  '" contains non-deformer history.\n'
        if len(objects_non_deformer_history) != 0 and len(possible_objects_non_deformer_history) == 0:
            string_status = string_status[:-1]
        
        for obj in possible_objects_non_deformer_history: 
            string_status = string_status + '"' + obj +  '" contains deformers often used for modeling.\n'
        if len(possible_objects_non_deformer_history) != 0:
            string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No objects with non-deformer history!'
    return '\n*** ' + item_name + " ***\n" + string_status
    
    
# Item 20 - Textures Color Space =========================================================================
def check_textures_color_space():
    item_name = checklist_items.get(20)[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = checklist_items.get(20)[1]
    
    objects_wrong_color_space = []
    possible_objects_wrong_color_space = []
    
    # These types return an error instead of warning
    error_types = ['RedshiftMaterial','RedshiftArchitectural', 'RedshiftDisplacement', 'RedshiftColorCorrection', 'RedshiftBumpMap', 'RedshiftSkin', 'RedshiftSubSurfaceScatter',\
    'aiStandardSurface', 'aiFlat', 'aiCarPaint', 'aiBump2d', '', 'aiToon', 'aiBump3d', 'aiAmbientOcclusion', 'displacementShader']
        
    # If type starts with any of these strings it will be tested
    check_types = ['Redshift', 'ai', 'lambert', 'blinn', 'phong', 'useBackground', 'checker', 'ramp', 'volumeShader', 'displacementShader', 'anisotropic', 'bump2d'] 
    
    # These types and connections are allowed to be float3 even though it's raw
    float3_to_float_exceptions = {'RedshiftBumpMap': 'input',
                                  'RedshiftDisplacement':'texMap'}

    # Count Textures
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        color_space = cmds.getAttr(file + '.colorSpace')
        
        has_suspicious_connection = False
        has_error_node_type = False
        
        intput_node_connections = cmds.listConnections(file, destination=True, source=False, plugs=True) or []
        
        suspicious_connections = []
        possible_suspicious_connections = []
        
        if color_space.lower() == 'Raw'.lower():
            for in_con in intput_node_connections:
                node = in_con.split('.')[0]
                node_in_con = in_con.split('.')[1]
                
                node_type = cmds.objectType(node)
                
                if node_type in error_types:
                    has_error_node_type = True
                
                should_be_checked = False
                for types in check_types:
                    if node_type.startswith(types):
                        should_be_checked = True
                
                if should_be_checked:
                    data_type = cmds.getAttr(in_con, type=True)
                    if data_type == 'float3' and (node_type in float3_to_float_exceptions and node_in_con in float3_to_float_exceptions.values()) == False:
                            has_suspicious_connection = True
                            suspicious_connections.append(in_con)
        
        if color_space.lower() == 'sRGB'.lower():
            for in_con in intput_node_connections:
                node = in_con.split('.')[0]
                node_in_con = in_con.split('.')[1]
                
                node_type = cmds.objectType(node)
                
                if node_type in error_types:
                    has_error_node_type = True
                
                should_be_checked = False
                for types in check_types:
                    if node_type.startswith(types):
                        should_be_checked = True
                
                if should_be_checked:
                    data_type = cmds.getAttr(in_con, type=True)
                    if data_type == 'float':
                            has_suspicious_connection = True
                            suspicious_connections.append(in_con)
                    if node_type in float3_to_float_exceptions and node_in_con in float3_to_float_exceptions.values():
                            has_suspicious_connection = True
                            suspicious_connections.append(in_con)
                  
        if has_suspicious_connection:
            if has_error_node_type:
                objects_wrong_color_space.append([file,suspicious_connections])
            else:
                possible_objects_wrong_color_space.append([file,suspicious_connections])
           
    
    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []
    bottom_message = '\n\n (For a complete list, generate a full report)'
    
    if len(possible_objects_wrong_color_space) == 1:
        patch_message_warning = str(len(possible_objects_wrong_color_space)) + ' file node is using a color space that might not be appropriate for its connection.\n'
    else:
        patch_message_warning = str(len(possible_objects_wrong_color_space)) + ' file nodes are using a color space that might not be appropriate for its connection.\n'
    
    if len(objects_wrong_color_space) == 1:
        patch_message_error = str(len(objects_wrong_color_space)) + ' file node is using a color space that is not appropriate for its connection.\n'
    else:
        patch_message_error = str(len(objects_wrong_color_space)) + ' file nodes are using a color space that is not appropriate for its connection.\n'
        
    
    # Manage Messages
    patch_message = ''
    might_have_issues_message = 'Select File Nodes With Possible Issues'
    has_issues_message = 'Select File Nodes With Issues'
            
    if len(possible_objects_wrong_color_space) != 0 and len(objects_wrong_color_space) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_objects_wrong_color_space)) + ' ]' )
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append(might_have_issues_message)
    elif len(possible_objects_wrong_color_space) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_wrong_color_space)))
        patch_message = patch_message_error
        buttons_to_add.append(has_issues_message)
    else:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_wrong_color_space)) + ' + [ ' + str(len(possible_objects_wrong_color_space)) + ' ]' )
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append(might_have_issues_message)
        buttons_to_add.append(has_issues_message)
    
    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)
    
    # Manage State
    if len(possible_objects_wrong_color_space) != 0 and len(objects_wrong_color_space) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l= '', c=lambda args: warning_non_deformer_history()) 
        issues_found = 0
    elif len(objects_wrong_color_space) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message('No color space issues were found.')) 
        issues_found = 0
    else: 
        cmds.button("status_" + item_id, e=True, bgc=error_color, l= '?', c=lambda args: warning_non_deformer_history())
        issues_found = len(objects_wrong_color_space)

    # Patch Function ----------------------
    def warning_non_deformer_history():
        user_input = cmds.confirmDialog(
                    title= item_name,
                    message= patch_message + bottom_message,
                    button= assembled_message,
                    defaultButton='OK',
                    cancelButton='Ignore Issue',
                    dismissString='Ignore Issue', 
                    icon="warning")
                    
        if user_input == has_issues_message:
            cmds.select(clear=True)
            for obj in objects_wrong_color_space:
                cmds.select(obj[0], add=True)
        elif user_input == might_have_issues_message:
            cmds.select(clear=True)
            for obj in possible_objects_wrong_color_space:
                cmds.select(obj[0], add=True)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '')
        else:
            cmds.button("status_" + item_id, e=True, l= '')
    
    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_objects_wrong_color_space) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_wrong_color_space: 
            string_status = string_status + '"' + obj[0] +  '" is using a color space (' + cmds.getAttr(obj[0] + '.colorSpace') + ') that is not appropriate for its connection.\n' 
            for connection in obj[1]:
                string_status = string_status + '   "' + connection + '" triggered this error.\n'
        if len(objects_wrong_color_space) != 0 and len(possible_objects_wrong_color_space) == 0:
            string_status = string_status[:-1]
        
        for obj in possible_objects_wrong_color_space: 
            string_status = string_status + '"' + obj[0] +  '" might be using a color space (' + cmds.getAttr(obj[0] + '.colorSpace') + ') that is not appropriate for its connection.\n'
            for connection in obj[1]:
                string_status = string_status + '   "' + connection + '" triggered this warning.\n'
        if len(possible_objects_wrong_color_space) != 0:
            string_status = string_status[:-1]
    else: 
        string_status = str(issues_found) + ' issues found. No color space issues were found!'
    return '\n*** ' + item_name + " ***\n" + string_status

 
    
# Checklist Functions End Here ===================================================================


def print_message(message, as_warning=False, as_heads_up_message=False):
    if as_warning:
        cmds.warning(message)
    elif as_heads_up_message:
        cmds.headsUpMessage(message, verticalOffset=150 , time=5.0)
    else:
        print(message)

                    
# Used to Export Full Report:
def export_report_to_txt(list):
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir+'tmp.txt';
    
    f = open(txt_file,'w')
    
    output_string = script_name + " Full Report:\n"
    
    for obj in list:
        output_string = output_string + obj + "\n\n"
    
    f.write(output_string)
    f.close()

    notepadCommand = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepadCommand)



#Build GUI
build_gui_gt_m1_kitchen_checklist()