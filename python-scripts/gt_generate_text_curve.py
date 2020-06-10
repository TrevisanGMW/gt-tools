"""
 Text Curve Generator -> Simple script used to quickly create text curves
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-09
 
 To Do:
 Add font/size options
 
"""
import maya.cmds as cmds

# Version
script_version = "v1.0";


# Main Form ============================================================================
def build_gui_generate_text_curve():
    if cmds.window("build_gui_generate_text_curve", exists =True):
        cmds.deleteUI("build_gui_generate_text_curve")    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_generate_text_curve = cmds.window("build_gui_generate_text_curve", title=script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable = False, widthHeight=[213, 160])
    column_main = cmds.columnLayout() 
    
    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Text Curve Generator - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("        This script creates a single curve       ")
    cmds.text("   containing the text typed below  ")
    cmds.text("   (All shapes go under one transform)  ")
    cmds.rowColumnLayout(p=content_main,numberOfRows=1, h= 5) #Empty Space
    
    cmds.separator(h=15, p=content_main)
    bottom_container = cmds.rowColumnLayout(p=content_main,adj=True)
    cmds.text('Text:',p=bottom_container)
    desired_text = cmds.textField(p = bottom_container, text="hello, world", enterCommand=lambda x:generate_text_curve())
    cmds.button(p=bottom_container, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generate_text_curve())
                                                                                                                              
        
    cmds.showWindow(build_gui_generate_text_curve)
    
    test = cmds.window(build_gui_generate_text_curve, q=True, widthHeight=True)
    print(test)

    # Main GUI Ends Here =================================================================================

    # Main Function Starts ----------------------
    def generate_text_curve():
        strings = parse_text_field_commas(cmds.textField(desired_text, q=True, text=True))
        
        for string in strings:
            create_text(string)
            
    # Main Function Ends  ----------------------

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