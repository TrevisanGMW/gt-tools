import maya.cmds as cmds
from decimal import *

# Python Curve Generator
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2019-01-02
# Last update - 2019-01-02

# Version:
scriptVersion = "v1.0"

# Default Settings
closeCurve = True
addImport = False

# Function for the "Run Code" button
def runOutput(out):
    try:
        exec(out)
    except:
        cmds.warning("Something is wrong with your code!")


# Main Form ============================================================================
def mainDialog():
    if cmds.window("mainDialog", exists =True):
        cmds.deleteUI("mainDialog")    

    # mainDialog Start Here =================================================================================

    crMainDialog = cmds.window("mainDialog", title="Py C Gen - " + scriptVersion, widthHeight=(480,250),\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Python Curve Generator - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script generates the Python code       ")
    cmds.text("      necessary to create the selected curve.     ")
    cmds.text("     (Delete its history before running script)     ")
    cmds.text("   ")
    cmds.text('1. Select Desired Curve ')
    cmds.text('2. Click on \"Generate\"  ')
    cmds.text("3. Copy Python Output")
    cmds.text("   ")
    cmds.separator(h=10, p=contentMain)
    interactiveContainer = cmds.rowColumnLayout( numberOfRows=1, h= 25)
    cmds.text("   ")
    settings = cmds.checkBoxGrp(p=interactiveContainer, columnWidth2=[150, 1], numberOfCheckBoxes=2, \
                                label1 = 'Add import \"maya.cmds\" ', label2 = "Close Curve", v1 = addImport, v2 = closeCurve)   
    cmds.button(p=contentMain, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generatePythonCurve())
    cmds.separator(h=10, p=contentMain)
    cmds.text(p=contentMain, label='Output Python Curve' )
    outputPython = cmds.scrollField(p =contentMain, editable=True, wordWrap=True)
    swOrganizationContainer = cmds.columnLayout(p=contentMain)
    cmds.button(p=contentMain, l ="Run Code", c=lambda x:runOutput(cmds.scrollField(outputPython, query=True, text=True)))
    
    def generatePythonCurve():

        getcontext().prec = 5

        shape = cmds.listRelatives(cmds.ls(sl=1)[0],s=1)[0]
        cvs = cmds.getAttr(shape+'.cv[*]')
        cvsList = []
        for c in cvs:
            cvsList.append([float(Decimal("%.3f" % c[0])),float(Decimal("%.3f" % c[1])),float(Decimal("%.3f" % c[2]))])

        if cmds.checkBoxGrp (settings, q=True, value1=True):
            out = 'import maya.cmds as cmds\n\ncmds.curve(p='
        else:
            out = 'cmds.curve(p='
            
        out += '[%s]' % ', '.join(map(str, cvsList))
        out += ',d='+str(cmds.getAttr(shape+'.degree'))+')'
        
        if cmds.checkBoxGrp (settings, q=True, value2=True):
            out += '\n\ncmds.closeCurve(ch=False, ps=False, rpo=True)'
        else:
            pass
        
        print ("#" * 100)
        print out
        print ("#" * 100)
        
        cmds.scrollField(outputPython, edit=True, wordWrap=True, text=out ,sl=True)
        cmds.setFocus(outputPython)

    cmds.showWindow(crMainDialog)
    # mainDialog Ends Here =================================================================================

#Start current "Main"
mainDialog()
