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

# Checklist Name
checklist_name = "Checklist Name" #"VFS Render Farm Checklist"

# Version
script_version = "1.0";

# Status Colors
def_color = 0.3, 0.3, 0.3
pass_color = (0.17, 1.0, 0.17)
warning_color = (1.0, 1.0, 0.17)
error_color = (1.0, 0.17, 0.17)

# Full Report .clear
# test = []
# Checklist Items
checklist_items = [
    "Frame Rate", # 1
    "Scene Units",
    "Output Resolution",
    "Total Texture Count",
    "Network File Paths",
    "Unparented Objects",
    "Total Triangle Count",
    "Total Poly Object Count",
    "Shadow Casting Light Count",
    "RS Shadow Casting Light Count",
    "Default Object Names",
    "Objects Assigned to lambert1",
    "Ngons",
    "Non-manifold Geometry",
    "Empty UV Sets",
    "Frozen Transforms",
    "Animated Visibility",
    "Non Deformer History"
    ]



def build_gui_checklist():
    if cmds.window("build_gui_checklist", exists=True):
        cmds.deleteUI("build_gui_checklist", window=True)

    cmds.window("build_gui_checklist", title=checklist_name + "  v" + script_version, mnb=False, mxb=False, s=True)

    cmds.columnLayout("main_column", p="build_gui_checklist")

    cmds.showWindow("build_gui_checklist")
    cmds.window("build_gui_checklist", e=True, h=1) # Change it later
    
    # UI
    main_cw = 300
    warning_title_cw = 100
    warning_content_cw = 280

    # Title Text
   #cmds.rowColumnLayout(nc=1, cs=[(1,10)], columnWidth=[(1, main_cw)], p="main_column")
    cmds.separator(h=14, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 240), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p="main_column")

    cmds.text(" ", bgc=[0,.5,0])
    cmds.text(checklist_name + " - v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_checklist())
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    #cmds.separator(h=8)
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=8)

    # General Cleanup Info
    cmds.rowColumnLayout(nc=1, cw=[(1, 280)], cs=[(1,10)], p="main_column")
    cmds.separator(h=5, style='none') # Empty Space

    cmds.rowColumnLayout(nc=3, cw=[(1, 170), (2, 35), (3, 95)], cs=[(1, 10), (2, 6), (3, 6)], p="main_column") 
    
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
            item_id = item.lower().replace(" ","_").replace("-","_")
            cmds.text(l=item + ': ', align="left")
            cmds.button("status_" + item_id , l='', h=14, bgc=def_color)
            cmds.text("output_" + item_id, l='...', align="center")

    create_checklist_items(checklist_items)
    

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    
    cmds.separator(h=8, style='none') # Empty Space
    
    # End of list
    cmds.separator(h=8)


    # Refresh Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Generate Report', h=30, c=lambda args: refresh_checklist())
    cmds.separator(h=10, style='none')
    cmds.button(l='Refresh', h=30, c=lambda args: refresh_checklist())
    cmds.separator(h=8, style='none')



def refresh_checklist():
    #printReport = ["hello"]
    #exportToTxt(printReport)
    #save_state()
    #load_state()
    check_frame_rate()
    check_scene_units()
    test = check_output_resolution()
    print(test)



# Checklist Functions Start Here ================================================================

# Item 0 - Frame Rate
def check_frame_rate():
    item_name = checklist_items[0]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = "film"
    received_value = cmds.currentUnit( query=True, time=True ) # Frame Rate
    issues_found = 0

    if received_value == expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l= '', c=lambda args: print_message(item_name + ': "'  + received_value.capitalize())) 
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
    
    

# Item 1 - Scene Units
def check_scene_units():
    item_name = checklist_items[1]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = "cm"
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

# Item 2 - Output Resolution
def check_output_resolution():
    item_name = checklist_items[2]
    item_id = item_name.lower().replace(" ","_").replace("-","_")
    expected_value = ["1920","1080"]
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


# Checklist Functions End Here =====+++===========================================================


def print_message(message):
    print(message)


def export_to_txt(list):
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp.txt';
    
    f = open(txtFile,'w')
    

    selectCommand = "# Python command to select it:\n\nimport maya.cmds as cmds\nselectedObjects = ['" + stringForPy + \
    "'] \ncmds.select(selectedObjects)\n\n\n\'\'\'\n// Mel command to select it\nselect -r " + stringForMel + "\n\n\'\'\'\n\n\n# List of Objects:\n# " + stringForList

    f.write(selectCommand)
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