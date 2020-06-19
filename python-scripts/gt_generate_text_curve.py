"""
 Text Curve Generator -> Simple script used to quickly create text curves
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-09
 
 1.1 - 2020-06-17
 Changed UI
 Added help menu
 Added icon
 
 To Do:
 Add font/size options
 
 
"""
import maya.cmds as cmds
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
script_name = "GT - Text Curve Generator"

# Version
script_version = "1.1";


# Main Form ============================================================================
def build_gui_generate_text_curve():
    window_name = "build_gui_generate_text_curve"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_generate_text_curve = cmds.window(window_name, title=script_name + "  v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    column_main = cmds.columnLayout() 
    
    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)
    
    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name + " - v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_generate_text_curve())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    cmds.separator(h=15, p=body_column)
    cmds.text('Text:',p=body_column)
    desired_text = cmds.textField(p = body_column, text="hello, world", enterCommand=lambda x:generate_text_curve())
    cmds.separator(h=10, style='none') # Empty Space
    cmds.button(p=body_column, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generate_text_curve())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space
                                                                                                                              
    # Show and Lock Window
    cmds.showWindow(build_gui_generate_text_curve)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/text.png')
    widget.setWindowIcon(icon)
    
    print(' ')

    # Main GUI Ends Here =================================================================================

    # Main Function Starts ----------------------
    def generate_text_curve():
        strings = parse_text_field_commas(cmds.textField(desired_text, q=True, text=True))
        
        for string in strings:
            create_text(string)
            
    # Main Function Ends  ----------------------


# Creates Help GUI
def build_gui_help_generate_text_curve():
    window_name = "build_gui_help_generate_text_curve"
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
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script creates merged curves containing the input', align="left")
    cmds.text(l='text from the text field.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='(All shapes go under one transform)', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='You can create multiple curves by separanting them with', align="left")
    cmds.text(l='commas ",".', align="left")
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
    cmds.separator(h=10, style='none')
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





# Function to Parse textField data 
def parse_text_field_commas(text_field_data):
    if len(text_field_data) <= 0:
        return []
    else:
        return_list = text_field_data.split(",")
        empty_objects = []
        for obj in return_list:
            if '' == obj:
                empty_objects.append(obj)
        for obj in empty_objects:
            return_list.remove(obj)
        return return_list

# Generate texts
def create_text(text):
    cmds.textCurves(ch=0, t=text)
    cmds.ungroup()
    cmds.ungroup()
    curves = cmds.ls(sl=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    shapes = curves[1:]
    cmds.select(shapes, r=True)
    cmds.pickWalk(d='Down')
    cmds.select(curves[0], tgl=True)
    cmds.parent(r=True, s=True)
    cmds.pickWalk(d='up')
    cmds.delete(shapes)
    cmds.xform(cp=True)
    cmds.rename(text.lower() + "_crv")
    return cmds.ls(sl=True)[0]
    
#Run Script
build_gui_generate_text_curve()