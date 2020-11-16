"""
 GT Replace Reference Paths Script
 @Guilherme Trevisan - TrevisanGMW@gmail.com - github.com/TrevisanGMW - 2020-03-03
 Last update - 2020-03-03

 1.1 - 2020-06-07 
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
 1.2 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI
 
 1.3 - 2020-11-15
 Tweaked the color and text for the title and help menu

 To do: 
 Show list of current paths directly in the UI
 Add an option for the user to auto search through folders for his reference.

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

# Script Name
script_name = "GT - Replace Reference Paths"

# Version:
script_version = "1.3";

# Default Settings: 
default_search_path = "H:\\"
default_replace_path = "\\\\vfsstorage10\\3D\\Students"


#Loads PyMel (if necessary)
try:
    pm.about(version=True)
except:
    if cmds.window("pyMel_load_message", exists =True):
        cmds.deleteUI("pyMel_load_message")    

    pyMel_load_message = cmds.window("pyMel_load_message", title="PyMel",\
                          titleBar=True,minimizeButton=False,maximizeButton=False, sizeable =False, widthHeight=[110, 40])
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("", h=5)
    cmds.text("    Loading PyMel     ", bgc=[.1,.1,.1],  fn="boldLabelFont")
    cmds.text("    Please Wait     ", bgc=[.1,.1,.1],  fn="boldLabelFont")
    cmds.text(" ", h=5)
    cmds.showWindow(pyMel_load_message)

    import pymel.core as pm
                                                                
    if cmds.window("pyMel_load_message", exists =True):
        cmds.deleteUI("pyMel_load_message")  
    

# Store References
refs = pm.listReferences()

# Main Form ============================================================================
def build_gui_replace_reference_paths():
    window_name = "build_gui_replace_reference_paths"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_replace_reference_paths = cmds.window(window_name, title=script_name + ' - (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])
        
    content_main = cmds.columnLayout(adj = True)


    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_replace_reference_paths())
    
    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,10)])

    cmds.separator(h=5, style='none') # Empty Space
    cmds.text("This script allows you to search and replace")
    cmds.text('strings in the path of your references.')
    cmds.separator(h=10, style='none') # Empty Space
 
    cmds.text('It auto adjusts the direction of slashes', fn="boldLabelFont")
    cmds.text('        ', height=13)

    cmds.separator(h=15, p=content_main)
    
    cmds.button(l ="Print Current Paths", c=lambda x:print_current_paths("print"))
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    cmds.text('Search:')
    search_text_field = cmds.textField(text=default_search_path, enterCommand=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
    cmds.separator(h=5, style="none")
 
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    cmds.text('Replace:')
    replace_text_field = cmds.textField(text=default_replace_path, enterCommand=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
    cmds.text(' ', height=7)
    cmds.button( l ="Attempt to Auto Detect Student Path (VFS)", c=lambda x:auto_detect_path())
    cmds.separator(h=5, style='none', p=content_main) # Empty Space
    cmds.separator(h=15, p=content_main)
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button(l ="Replace", bgc=(.6, .6, .6), c=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
    cmds.separator(h=10, style='none', p=content_main) # Empty Space
                                                                        
    def auto_detect_path():
        file_path = cmds.file(q=True, sn=True)
        if file_path != '':
            current_path_as_list = file_path.split("/") # check its length
            if len(current_path_as_list) >= 6:
                guessed_path = current_path_as_list[0] + '/' + current_path_as_list[1] + '/' + current_path_as_list[2] + '/' \
                + current_path_as_list[3] + '/' + current_path_as_list[4] + '/' + current_path_as_list[5] + '/' + current_path_as_list[6]  + '/' 
                cmds.textField(replace_text_field, e=True, text=guessed_path)
            else:
                cmds.warning("The length of the path found doesn't seem to be long enough. Try opening the scene directly from the students folder")
        else:
            cmds.warning("Scene file path seems empty, try opening the scene instead of importing it")

    # Show and Lock Window
    cmds.showWindow(build_gui_replace_reference_paths)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/reference.png')
    widget.setWindowIcon(icon)                                                                                                                          
    

    # Main GUI Ends Here ================================================================================= 

# Creates Help GUI
def build_gui_help_replace_reference_paths():
    window_name = "build_gui_help_replace_reference_paths"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script allows you to search for a string', align="center")
    cmds.text(l='in the path for your references and replace it', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Print Current Paths:', align="left", fn="boldLabelFont")
    cmds.text(l='Prints a list containing the current path of all your', align="left")
    cmds.text(l='references. Use this to make sure you\'re searching for', align="left")
    cmds.text(l='the correct string.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Search and Replace:', align="left", fn="boldLabelFont")
    cmds.text(l='Enter the strings for what you want to search for and', align="left")
    cmds.text(l='what you want to replace it with.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Attempt to Auto Detect Student Path (VFS):', align="left", fn="boldLabelFont")
    cmds.text(l='In case you\'re using this script at VFS you can try to', align="left")
    cmds.text(l='automatically detect the path. This function uses the', align="left")
    cmds.text(l='path of the scene to try determine the new path.', align="left")
    cmds.text(l='For this to work, the scene must be inside your H: drive.', align="left")
    cmds.text(l='', align="left")
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


def print_current_paths(header_mode):
    print("#" * 80)
    if header_mode == "print":
        print("     References Paths:")
    else:
        print("     Updated References Paths:")
    for ref in refs:
        print("%s"%  ref.path) #Old Path
    
    print("#" * 80)
    if header_mode == "print":
        cmds.headsUpMessage( 'Open script editor to see a list of the current paths', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Open script editor to see an updated list of paths', verticalOffset=150 , time=5.0)


def search_replace_reference_path(search,replace):

    invert_slash_search = search.replace("\\","/")
    invert_slash_replace = replace.replace("\\","/")
    
    for ref in refs:
        new_path = ("%s"%  ref.path).replace(invert_slash_search,invert_slash_replace)
        reference_node = ("%s" % ref.refNode)
        cmds.file(new_path, loadReference=reference_node)
        
    print_current_paths("replace")



#Run Script
if __name__ == '__main__':
    build_gui_replace_reference_paths()