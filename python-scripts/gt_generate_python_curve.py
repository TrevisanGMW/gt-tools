"""
 Python Curve Generator
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-02
 1.1 - 2020-01-03
 Minor patch.
 
 1.2 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 Added length checker for selection before running.
 
"""

import maya.cmds as cmds
from decimal import *

# Version:
script_version = "v1.2"

# Default Settings
close_curve = True
add_import = False

# Function for the "Run Code" button
def run_output_code(out):
    try:
        exec(out)
    except:
        cmds.warning("Something is wrong with your code!")


# Main Form ============================================================================
def build_gui_py_curve():
    if cmds.window("build_gui_py_curve", exists =True):
        cmds.deleteUI("build_gui_py_curve")    

    # Main GUI Start Here =================================================================================

    build_gui_py_curve = cmds.window("build_gui_py_curve", title="GT Py C - " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable = False, widthHeight = [260, 443])

    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Python Curve Generator - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script generates the Python code       ")
    cmds.text("      necessary to create the selected curve.     ")
    cmds.text("     (Delete its history before running script)     ")
    cmds.text("   ")
    cmds.text('1. Select Desired Curve ')
    cmds.text('2. Click on \"Generate\"  ')
    cmds.text("3. Copy Python Output")
    cmds.text("   ")
    cmds.separator(h=10, p=content_main)
    interactive_container = cmds.rowColumnLayout( numberOfRows=1, h= 25)
    cmds.text("   ")
    settings = cmds.checkBoxGrp(p=interactive_container, columnWidth2=[150, 1], numberOfCheckBoxes=2, \
                                label1 = 'Add import \"maya.cmds\" ', label2 = "Close Curve", v1 = add_import, v2 = close_curve)   
    cmds.button(p=content_main, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generate_python_curve())
    cmds.separator(h=10, p=content_main)
    cmds.text(p=content_main, label='Output Python Curve' )
    output_python = cmds.scrollField(p =content_main, editable=True, wordWrap=True)
    cmds.button(p=content_main, l ="Run Code", c=lambda x:run_output_code(cmds.scrollField(output_python, query=True, text=True)))
    
    def generate_python_curve():
        
        not_curve_error = "Please make sure you selected a Nurbs Curve or a Bezier Curve object before generating it"
        
        if len(cmds.ls(selection=True)) != 0:
            getcontext().prec = 5
            
            shape = cmds.listRelatives(cmds.ls(sl=1)[0],s=1)[0]
            type_checker = str(cmds.objectType(shape))
            

            if "nurbsCurve" in type_checker or "bezierCurve" in type_checker:
                
                cvs = cmds.getAttr(shape+'.cv[*]')
                cvs_list = []
                
                
                for c in cvs:
                    cvs_list.append([float(Decimal("%.3f" % c[0])),float(Decimal("%.3f" % c[1])),float(Decimal("%.3f" % c[2]))])

                if cmds.checkBoxGrp (settings, q=True, value1=True):
                    out = 'import maya.cmds as cmds\n\ncmds.curve(p='
                else:
                    out = 'cmds.curve(p='
                    
                out += '[%s]' % ', '.join(map(str, cvs_list))
                out += ',d='+str(cmds.getAttr(shape+'.degree'))+')'
                
                if cmds.checkBoxGrp (settings, q=True, value2=True):
                    out += '\n\ncmds.closeCurve(ch=False, ps=False, rpo=True)'
                else:
                    pass
                
                print ("#" * 100)
                print out
                print ("#" * 100)
                
                cmds.scrollField(output_python, edit=True, wordWrap=True, text=out ,sl=True)
                cmds.setFocus(output_python)
            else:
                cmds.warning(not_curve_error)
                cmds.scrollField(output_python, edit=True, wordWrap=True, text=not_curve_error ,sl=True)
                cmds.setFocus(output_python)
        else:
            cmds.warning(not_curve_error)

    cmds.showWindow(build_gui_py_curve)
    # Main GUI Ends Here =================================================================================

#Start current "Main"
build_gui_py_curve()