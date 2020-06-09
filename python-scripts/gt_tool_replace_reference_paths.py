
"""
 GT Replace Reference Paths Script
 @Guilherme Trevisan - TrevisanGMW@gmail.com - github.com/TrevisanGMW - 2020-03-03
 Last update - 2020-03-03

 1.1 - 2020-06-07 
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.

 To do: 
 Show list of current paths directly in the UI
 Add an option for the user to auto search through folders for his reference.

"""
import maya.cmds as cmds
import maya.mel as mel


script_version = "v1.1";

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
    if cmds.window("build_gui_replace_reference_paths", exists =True):
        cmds.deleteUI("build_gui_replace_reference_paths")    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_replace_reference_paths = cmds.window("build_gui_replace_reference_paths", title="gt_ref_paths - " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False, widthHeight=[269, 313])
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)
    
    content_main = cmds.columnLayout(adj = True)

    
    cmds.text(" ")
    row_one = cmds.rowColumnLayout(p=content_main, numberOfRows=1, ) #Empty Space
    cmds.text( "      GT - Replace Reference Paths -  " + script_version + "     ",p=row_one, bgc=[0,.5,0],  fn="boldLabelFont")
    
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_replace_reference_paths())
    cmds.text("    ", bgc=[0,.5,0])
    
    
    cmds.rowColumnLayout(p=content_main)

    cmds.text("  ")
    cmds.text("      This script allows you to search and replace       ")
    cmds.text('      strings in the path of your references.   ')
    cmds.text('        ')
    cmds.text('    It auto adjusts the direction of slashes   ', fn="boldLabelFont")
    cmds.text('        ', height=13)

    cmds.separator(h=15, p=content_main)
    
    cmds.button(l ="Print Current Paths", c=lambda x:print_current_paths("print"))
    
    
    bottom_container = cmds.rowColumnLayout(p=content_main,adj=True)
    cmds.text('Search:',p=bottom_container)
    search_text_field = cmds.textField(p = bottom_container, text=default_search_path, enterCommand=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
    cmds.separator(h=15)
 
    
    bottom_container = cmds.rowColumnLayout(p=content_main,adj=True)
    cmds.text('Replace:',p=bottom_container)
    replace_text_field = cmds.textField(p = bottom_container, text=default_replace_path, enterCommand=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
    cmds.text(' ',p=bottom_container, height=7)
    cmds.button( l ="Attempt to Auto Detect Student Path (VFS)", c=lambda x:auto_detect_path())
    cmds.separator(h=15)
    cmds.button( l ="Replace", bgc=(.6, .8, .6), c=lambda x:search_replace_reference_path\
                                        (cmds.textField(search_text_field, q=True, text=True),\
                                        cmds.textField(replace_text_field, q=True, text=True)))
                                                                        
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

                                                                                                                              
    cmds.showWindow(build_gui_replace_reference_paths)

    # Main GUI Ends Here ================================================================================= 


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


def build_gui_help_replace_reference_paths():
    if cmds.window("build_gui_help_replace_reference_paths", exists =True):
        cmds.deleteUI("build_gui_help_replace_reference_paths")    

    # About Dialog Start Here =================================================================================
    
    # Build About UI
    build_gui_help_replace_reference_paths = cmds.window("build_gui_help_replace_reference_paths", title="GT Replace Ref Path - Help",\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False, widthHeight = [330, 456])
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Help for GT Replace Reference Paths ", bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text(" Version Installed: " + script_version)
    cmds.text("  ")
    cmds.text("      This script allows you to search for a string       ")
    cmds.text('      in the path for your references and replace it  ')
    cmds.text(' ')
    cmds.text('      The "Print Current Paths" button prints a list   ')
    cmds.text('      containing the current path of all your references.    ')
    cmds.text('      Use this to make sure you\'re searching for the    ')
    cmds.text('      correct string.    ')
    cmds.text(' ')
    cmds.text('      Under that, you\'ll find two text fields (boxes),    ')
    cmds.text('      type the string you want to search for on the first      ')
    cmds.text('      one (Search:), and what you want to replace    ')
    cmds.text('      it with in the second (Replace:)    ')
    cmds.text(' ')
    cmds.text('      In case you\'re using this script at VFS you can   ')
    cmds.text('      try to use the "Attempt to Auto Detect Student Path (VFS)"    ')
    cmds.text('      This button will use the path of the scene to try to    ')
    cmds.text('      figure it out what the path of your reference should be    ')
    cmds.text('      (so you don\'t have to find the path manually every time)    ')
    cmds.text(' ')
    cmds.text("      In case something doesn't work or you    ")
    cmds.text('      have a suggestion, send me an email.    ')
    cmds.text(' ')

    email_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    
    cmds.text('             Guilherme Trevisan : ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1], p=email_container)
    website_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text('                      Visit my ')
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1], p=website_container)
    cmds.text(' for updated versions')
    cmds.text(' ', p= content_main)
    cmds.separator(h=15, p=content_main)
    
    cmds.button(l ="Ok", p= content_main, c=lambda x:close_about_window())
                                                                                                                              
    def close_about_window():
        if cmds.window("build_gui_help_replace_reference_paths", exists =True):
            cmds.deleteUI("build_gui_help_replace_reference_paths")  
        
    cmds.showWindow(build_gui_help_replace_reference_paths)
    # About Dialog Ends Here =================================================================================


#Run Script
build_gui_replace_reference_paths()
