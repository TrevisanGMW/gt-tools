import pymel.core as pm
import maya.cmds as cmds

# GT Menu Script - Creates a menu to call scripts from the GT Tools Package
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-26
# Last update - 2020-02-26 - Initial Release

# Version:
scriptVersion = "v1.0"

main_window = pm.language.melGlobals['gMainWindow']

menuObjName = 'gt_tools'
menuLabel = 'GT Tools'

if pm.menu(menuObjName, label=menuLabel, exists=True, parent=main_window):
    pm.deleteUI(pm.menu(menuObjName,e=True, deleteAllItems=True))
   
# GT Tools Menu
gtToolsMenu = pm.menu(menuObjName,label=menuLabel, parent=main_window, tearOff=True) 

# Tools ============================================================================
pm.menuItem(label='Tools', subMenu=True, parent=gtToolsMenu, tearOff=True)
pm.menuItem(label='Selection Manager', command='import gt_tool_selectionManager\nreload(gt_tool_selectionManager)')
pm.menuItem(label='Generate Python Curve', command='import gt_generate_pythonCurve\nreload(gt_generate_pythonCurve)')
pm.menuItem(label='Replace Reference Paths', command='import gt_tools_replaceReferencePaths\nreload(gt_tools_replaceReferencePaths)')
pm.setParent('..', menu=True) # Brings it back to main menu

# Rigging ============================================================================

pm.menuItem(label='Rigging', subMenu=True, parent=gtToolsMenu, tearOff=True)
pm.menuItem(label='Connect Attributes', command='import gt_connect_Attributes\nreload(gt_connect_Attributes)')
pm.menuItem(label='Generate RigLayer', command='import gt_generate_rigLayer\nreload(gt_generate_rigLayer)')
pm.menuItem(label='Create Auto FK', command='import gt_createCtrl_AutoFK\nreload(gt_createCtrl_AutoFK)')
pm.menuItem(label='Create IK Leg', command='import gt_createCtrl_IK_Biped_Leg\nreload(gt_createCtrl_IK_Biped_Leg)')
pm.setParent('..', menu=True) # Brings it back to main menu

# About ============================================================================
pm.menuItem(divider=True)
pm.menuItem(label='About', command='gt_tools_menu.aboutMenuDialog()')


def aboutMenuDialog():
    if cmds.window("aboutMenuDialog", exists =True):
        cmds.deleteUI("aboutMenuDialog")    

    # About Dialog Start Here =================================================================================
    
    # Build About UI
    aboutMenuDialog = cmds.window("aboutMenuDialog", title="About GT",\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("About - GT Tools", bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text(" Version Installed: " + scriptVersion)
    cmds.text("  ")
    cmds.text("      GT Tools is a script package created with the intention        ")
    cmds.text('      of simplifying or assisting repetitive actions in Maya.  ')
    cmds.text(' ')
    cmds.text('      Most scripts were created according to what was    ')
    cmds.text('      needed to do at the time or for specific projects.    ')
    cmds.text(' ')
    cmds.text('      This package is provided free of charge    ')
    cmds.text('      so there are no guarantees.      ')
    cmds.text('      I suggest you save your project before using it.     ')
    cmds.text(' ')
    cmds.text('      Hopefully these scripts are helpful to you    ')
    cmds.text('      as they were to me :)    ')
    cmds.text(' ')
    cmds.text("      In case something doesn't work or you    ")
    cmds.text('      have a suggestion, send me an email.    ')
    cmds.text(' ')

    emailContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    
    cmds.text('             Guilherme Trevisan : ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1], p=emailContainer)
    websiteContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text('                      Visit my ')
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1], p=websiteContainer)
    cmds.text(' for updated versions')
    cmds.separator(h=15, p=contentMain)
    
    cmds.button(l ="Ok", p= contentMain, c=lambda x:closeAboutWindow())
                                                                                                                              
    def closeAboutWindow():
        if cmds.window("aboutMenuDialog", exists =True):
            cmds.deleteUI("aboutMenuDialog")  
        
    cmds.showWindow(aboutMenuDialog)
    
    # About Dialog Ends Here =================================================================================