"""

 GT Create Testing Keys - Script for creating testing keyframes.
 @Guilherme Trevisan - github.com/TrevisanGMW/gt-tools - 2021-01-28
 
 It creates a sequence of keyframes on the selected objects using the provided offset. 
 Helpful for when testing controls or painting skin weights.
 
 1.0 - 2021-01-28
 Initial Release
 
 1.1 - 2021-01-29
 Changed way that attributes are updated to account for long hierarchies (changed to setAttr instead of move/xform)
 Added a missing undoInfo(openChunk) function that would break the undo queue
 Udated a few incorrect comments
 
 1.2 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 
"""
import maya.cmds as cmds
import sys
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
script_name = "GT - Create Testing Keys"

# Version:
script_version = "1.2"

#Python Version
python_version = sys.version_info.major


# Main Form ============================================================================
def build_gui_create_testing_keys():
    window_name = "build_gui_create_testing_keys"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================

    build_gui_create_testing_keys = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
                          
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 170), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_create_testing_keys())
    cmds.separator(h=10, style='none') # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,10)], p=content_main)
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,20)])
    transform_column_width = [100, 1]
    
    # Offset Values Transforms
    copy_text_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1, adj=True)
    cmds.text("Offset Amount", p=copy_text_container)
    cmds.separator(h=7, style='none', p=body_column) # Empty Space
    
    cmds.rowColumnLayout(nc=4, cw=[(1, 20),(2, 63),(3, 63),(4, 63)], cs=[(1,6),(2,0),(3,2),(4,2)], p=body_column)

    cmds.text(' ')
    cmds.text('X', bgc=[.5,0,0])
    cmds.text('Y', bgc=[0,.5,0])
    cmds.text('Z', bgc=[0,0,.5])

    cmds.rowColumnLayout(nc=4, cw=[(1, 20),(2, 65),(3, 65),(4, 65)], cs=[(1,5),(2,0)], p=body_column)
    cmds.text('T')
    tx_offset_text_field = cmds.textField(text='0.0', ann='tx')
    ty_offset_text_field = cmds.textField(text='0.0', ann='ty')
    tz_offset_text_field = cmds.textField(text='0.0', ann='tz')
    
    cmds.text('R')
    rx_offset_text_field = cmds.textField(text='0.0', ann='rx')
    ry_offset_text_field = cmds.textField(text='0.0', ann='ry')
    rz_offset_text_field = cmds.textField(text='0.0', ann='rz')
    
    cmds.text('S')
    sx_offset_text_field = cmds.textField(text='0.0', ann='sx')
    sy_offset_text_field = cmds.textField(text='0.0', ann='sy')
    sz_offset_text_field = cmds.textField(text='0.0', ann='sz')
    
    cmds.separator(h=10, style='none', p=body_column) # Empty Space 

    cmds.rowColumnLayout(nc=1, cw=[(1, 210)], cs=[(1,10)], p=body_column) 
    cmds.button(l ='Reset All Offset Values', bgc=(.3, .3, .3), c=lambda x:reset_offset_values())  
    cmds.separator(h=10, style='none', p=body_column) # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 200)], cs=[(1,25)], p=body_column) 
    add_inverted_checkbox = cmds.checkBox(l=' Add Inverted Offset Movement', value=True)  
    cmds.separator(h=5, style='none') # Empty Space 
    delete_keys_checkbox = cmds.checkBox(l=' Delete Previously Created Keys', value=True)  
    
    cmds.separator(h=5, style='none', p=body_column) # Empty Space 
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 180)], cs=[(1,25)], p=body_column)
 
    interval_text_field = cmds.floatSliderGrp(cw=[(1,133),(2,45),(3,0)], cal=[(1,'left')], field=True, label='Interval Between Frames:',\
                                         minValue=0, maxValue=1000, fieldMinValue=0, fieldMaxValue=1000, value=5)#, cc=lambda args: update_grade_output())

    cmds.separator(h=7, style='none', p=body_column) # Empty Space 
    cmds.rowColumnLayout(nc=1, cw=[(1, 210)], cs=[(1,10)], p=body_column)  
    cmds.button(l ='Delete All Keyframes in the Scene', bgc=(.3, .3, .3), c=lambda x:gtu_delete_keyframes())
    
    cmds.separator(h=7, style='none') # Empty Space 
    
    cmds.button(l ='Create Testing Keyframes', bgc=(.6, .6, .6), c=lambda x:validate_operation())

    cmds.separator(h=13, style='none', p=content_main) # Empty Space
    
                
    # GUI Build Ends --------------------------------------------
    
    
    def validate_operation():
        '''
        '''
        errors = ''
        try:
            cmds.undoInfo(openChunk=True, chunkName=script_name)
            offset_text_fields = [tx_offset_text_field, ty_offset_text_field, tz_offset_text_field,\
                                rx_offset_text_field, ry_offset_text_field, rz_offset_text_field,\
                                sx_offset_text_field, sy_offset_text_field, sz_offset_text_field]

            initial_time = cmds.currentTime(q=True)
            selection = cmds.ls(selection=True)
            if len(cmds.ls(selection=True)) != 0:
                interval = cmds.floatSliderGrp(interval_text_field, q=True, value=True)
                
                add_inverted = cmds.checkBox(add_inverted_checkbox, q=True, value=True)  
                delete_keys = cmds.checkBox(delete_keys_checkbox, q=True, value=True)  
                
                if delete_keys:
                    for obj in cmds.ls(selection=True):
                        connections = cmds.listConnections(obj, type='animCurveTA') or []
                        connections += cmds.listConnections(obj, type='animCurveTL') or []
                        connections += cmds.listConnections(obj, type='animCurveTT') or []
                        connections += cmds.listConnections(obj, type='animCurveTU') or []
                        for key in connections:
                            try:
                                cmds.delete(key)
                            except:
                                pass
                
                # Apply Offsets 
                for text_field in offset_text_fields:
                    attr = cmds.textField(text_field, q=True, ann=True)
                    value = 0.0
                    try:
                        value = float(cmds.textField(text_field, q=True, text=True))
                    except:
                        pass
                    if value > 0:
                        create_testing_keyframes(value, attr, interval, create_inverted=add_inverted)
                        
            else: 
                cmds.warning('Select at least one object to create testing key frames.')
            cmds.currentTime(initial_time) # Return Time to initial value
        except Exception as e:
            errors += str(e) + '\n'
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=script_name)
        if errors != '':
            cmds.warning('An error occured when creating the keyframes. Open the script editor for more information.')
            print('######## Errors: ########')
            print(errors)
            print('#########################')
        
            
    def create_testing_keyframes(offset, attr, interval, create_inverted=False):
        '''
        Creates a sequence of keyframes on the selected objects so they move for testing
        Used to quickly test joints when rigging
        
                Parameters:
                    offset (float, int): keyframe value, how much it will move up and down (e.g. 1 or 2...)
                    attr (string): name of the attribute "e.g. rotation"
                    interval (int): Interval between keyframes (frequency)
                    create_inverted (bool): Whether or not to increate a key with the inverted offset value
        '''
        initial_time = cmds.currentTime(q=True) 
        selection = cmds.ls(selection=True)
        current_frame = cmds.playbackOptions( animationStartTime=True, q=True ) # Gets the first frame available in the timeline (usually 0 or 1)
        current_max_time = cmds.playbackOptions( maxTime=True, q=True ) # Gets the max time (work area end frame) to see if it needs to expand the timeline
        cmds.currentTime(current_frame) # Resets timeline to first frame 
            
        offset_vec = (0,0,0)
        
        # Desired Channel
        translate = False
        rotate = False
        scale = False
        if 't' in attr:
            translate = True
        elif 'r' in attr:
            rotate = True
        elif 's' in attr:
            scale = True
        
         # Assemble Offset
        if 'x' in attr:
            offset_vec = (offset, offset_vec[1], offset_vec[2])
        elif 'y' in attr:
            offset_vec = (offset_vec[0], offset, offset_vec[2])
        else:
            offset_vec = (offset_vec[0], offset_vec[1], offset)
            

        for obj in selection:
            if cmds.objExists(obj):
                # Create key at neutral pose
                cmds.setKeyframe(obj, at=attr, t=current_frame, itt='linear', ott='linear')
                
                if translate:
                    orig_tx = cmds.getAttr(obj + '.tx')
                    orig_ty = cmds.getAttr(obj + '.ty')
                    orig_tz = cmds.getAttr(obj + '.tz')
                    
                if rotate:
                    orig_rx = cmds.getAttr(obj + '.rx')
                    orig_ry = cmds.getAttr(obj + '.ry')
                    orig_rz = cmds.getAttr(obj + '.rz')

                if scale:
                    orig_sx = cmds.getAttr(obj + '.sx')
                    orig_sy = cmds.getAttr(obj + '.sy')
                    orig_sz = cmds.getAttr(obj + '.sz')
                    
                # Create key at positive pose
                current_frame += interval
                if translate:
                    offset_tx = orig_tx + offset_vec[0]
                    offset_ty = orig_ty + offset_vec[1]
                    offset_tz = orig_tz + offset_vec[2] 
                    if not cmds.getAttr(obj + '.tx', lock=True) and offset_tx != orig_tx:
                        cmds.setAttr(obj + '.tx', offset_tx)
                    if not cmds.getAttr(obj + '.ty', lock=True) and offset_ty != orig_ty:
                        cmds.setAttr(obj + '.ty', offset_ty)
                    if not cmds.getAttr(obj + '.tz', lock=True) and offset_tz != orig_tz:
                        cmds.setAttr(obj + '.tz', offset_tz)

                if rotate:
                    offset_rx = orig_rx + offset_vec[0]
                    offset_ry = orig_ry + offset_vec[1]
                    offset_rz = orig_rz + offset_vec[2]
                    if not cmds.getAttr(obj + '.rx', lock=True) and offset_rx != orig_rx:
                        cmds.setAttr(obj + '.rx', offset_rx)
                    if not cmds.getAttr(obj + '.ry', lock=True) and offset_ry != orig_ry:
                        cmds.setAttr(obj + '.ry', offset_ry)
                    if not cmds.getAttr(obj + '.rz', lock=True) and offset_rz != orig_rz:
                        cmds.setAttr(obj + '.rz', offset_rz)

                if scale:
                    offset_sx = orig_sx + offset_vec[0]
                    offset_sy = orig_sy + offset_vec[1]
                    offset_sz = orig_sz + offset_vec[2]
                    if not cmds.getAttr(obj + '.sx', lock=True) and offset_sx != orig_sx:
                        cmds.setAttr(obj + '.sx', offset_sx)
                    if not cmds.getAttr(obj + '.sy', lock=True) and offset_sy != orig_sy:
                        cmds.setAttr(obj + '.sy', offset_sy)
                    if not cmds.getAttr(obj + '.sz', lock=True) and offset_sz != orig_sz:
                        cmds.setAttr(obj + '.sz', offset_sz)
                cmds.setKeyframe(obj, at=attr, t=current_frame, itt='linear', ott='linear')

                if create_inverted:
                    # Create key at negative pose
                    current_frame += interval
                    if translate:
                        offset_tx = orig_tx + offset_vec[0]*-1
                        offset_ty = orig_ty + offset_vec[1]*-1
                        offset_tz = orig_tz + offset_vec[2]*-1
                        if not cmds.getAttr(obj + '.tx', lock=True) and offset_tx != orig_tx:
                            cmds.setAttr(obj + '.tx', offset_tx)
                        if not cmds.getAttr(obj + '.ty', lock=True) and offset_ty != orig_ty:
                            cmds.setAttr(obj + '.ty', offset_ty)
                        if not cmds.getAttr(obj + '.tz', lock=True) and offset_tz != orig_tz:
                            cmds.setAttr(obj + '.tz', offset_tz)
                            
                    if rotate:
                        offset_rx = orig_rx + offset_vec[0]*-1
                        offset_ry = orig_ry + offset_vec[1]*-1
                        offset_rz = orig_rz + offset_vec[2]*-1
                        if not cmds.getAttr(obj + '.rx', lock=True) and offset_rx != orig_rx:
                            cmds.setAttr(obj + '.rx', offset_rx)
                        if not cmds.getAttr(obj + '.ry', lock=True) and offset_ry != orig_ry:
                            cmds.setAttr(obj + '.ry', offset_ry)
                        if not cmds.getAttr(obj + '.rz', lock=True) and offset_rz != orig_rz:
                            cmds.setAttr(obj + '.rz', offset_rz)
                    if scale:
                        offset_sx = orig_sx + (orig_sx*-1)*2 + (offset_vec[0]*-1)
                        offset_sy = orig_sy + (orig_sy*-1)*2 + (offset_vec[1]*-1)
                        offset_sz = orig_sz + (orig_sz*-1)*2 + (offset_vec[2]*-1)
                        if not cmds.getAttr(obj + '.sx', lock=True) and offset_sx != orig_sx:
                            cmds.setAttr(obj + '.sx', offset_sx)
                        if not cmds.getAttr(obj + '.sy', lock=True) and offset_sy != orig_sy:
                            cmds.setAttr(obj + '.sy', offset_sy)
                        if not cmds.getAttr(obj + '.sz', lock=True) and offset_sz != orig_sz:
                            cmds.setAttr(obj + '.sz', offset_sz)     
                    cmds.setKeyframe(obj, at=attr, t=current_frame, itt='linear', ott='linear')

                    # Create key at neutral pose
                    current_frame += interval
                    if translate:
                        if not cmds.getAttr(obj + '.tx', lock=True):
                            cmds.setAttr(obj + '.tx', orig_tx)
                        if not cmds.getAttr(obj + '.ty', lock=True):
                            cmds.setAttr(obj + '.ty', orig_ty)
                        if not cmds.getAttr(obj + '.tz', lock=True):
                            cmds.setAttr(obj + '.tz', orig_tz)
                    if rotate:

                        if not cmds.getAttr(obj + '.rx', lock=True):
                            cmds.setAttr(obj + '.rx', orig_rx)
                        if not cmds.getAttr(obj + '.ry', lock=True):
                            cmds.setAttr(obj + '.ry', orig_ry)
                        if not cmds.getAttr(obj + '.rz', lock=True):
                            cmds.setAttr(obj + '.rz', orig_rz)
                    if scale:
                        if not cmds.getAttr(obj + '.sx', lock=True):
                            cmds.setAttr(obj + '.sx', orig_sx)
                        if not cmds.getAttr(obj + '.sy', lock=True):
                            cmds.setAttr(obj + '.sy', orig_sy)
                        if not cmds.getAttr(obj + '.sz', lock=True):
                            cmds.setAttr(obj + '.sz', orig_sz)
                    cmds.setKeyframe(obj, at=attr, t=current_frame, itt='linear', ott='linear')
                    
                else:
                    # Create key at neutral pose
                    current_frame += interval
                    if translate:
                        if not cmds.getAttr(obj + '.tx', lock=True):
                            cmds.setAttr(obj + '.tx', orig_tx)
                        if not cmds.getAttr(obj + '.ty', lock=True):
                            cmds.setAttr(obj + '.ty', orig_ty)
                        if not cmds.getAttr(obj + '.tz', lock=True):
                            cmds.setAttr(obj + '.tz', orig_tz)
                    if rotate:

                        if not cmds.getAttr(obj + '.rx', lock=True):
                            cmds.setAttr(obj + '.rx', orig_rx)
                        if not cmds.getAttr(obj + '.ry', lock=True):
                            cmds.setAttr(obj + '.ry', orig_ry)
                        if not cmds.getAttr(obj + '.rz', lock=True):
                            cmds.setAttr(obj + '.rz', orig_rz)
                    if scale:
                        if not cmds.getAttr(obj + '.sx', lock=True):
                            cmds.setAttr(obj + '.sx', orig_sx)
                        if not cmds.getAttr(obj + '.sy', lock=True):
                            cmds.setAttr(obj + '.sy', orig_sy)
                        if not cmds.getAttr(obj + '.sz', lock=True):
                            cmds.setAttr(obj + '.sz', orig_sz)
                    cmds.setKeyframe(obj, at=attr, t=current_frame, itt='linear', ott='linear')
                  
        if current_frame > current_max_time:
            cmds.playbackOptions( maxTime=current_frame ) # Expand max time if necessary

    def reset_offset_values():
        offset_text_fields = [tx_offset_text_field, ty_offset_text_field, tz_offset_text_field,\
                            rx_offset_text_field, ry_offset_text_field, rz_offset_text_field,\
                            sx_offset_text_field, sy_offset_text_field, sz_offset_text_field]
        
        for text_field in offset_text_fields:
            cmds.textField(text_field, e=True, text='0.0')
    
    def gtu_delete_keyframes():
        '''Deletes all keyframes (Doesn't include Set Driven Keys)'''       
        function_name = 'GTU Delete All Keyframes'
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        try:
            keys_ta = cmds.ls(type='animCurveTA')
            keys_tl = cmds.ls(type='animCurveTL')
            keys_tt = cmds.ls(type='animCurveTT')
            keys_tu = cmds.ls(type='animCurveTU')
            deleted_counter = 0
            all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
            for obj in all_keyframes:
                try:
                    cmds.delete(obj)
                    deleted_counter += 1
                except:
                    pass   
            message = '<span style=\"color:#FF0000;text-decoration:underline;\">' +  str(deleted_counter) + ' </span>'
            is_plural = 'keyframe nodes were'
            if deleted_counter == 1:
                is_plural = 'keyframe node was'
            message += is_plural + ' deleted.'
            
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        except Exception as e:
            cmds.warning(str(e))
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)
        

    # Show and Lock Window
    cmds.showWindow(build_gui_create_testing_keys)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/setMaxInfluence.png')
    widget.setWindowIcon(icon)
    
    # Deselect Text Field
    cmds.setFocus(window_name)

    # GUI Functions Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_create_testing_keys():
    window_name = "build_gui_help_create_testing_keys"
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
    cmds.text(l='This script creates a sequence of keys with offset', align="center")
    cmds.text(l='usually used for testing controls or skin weights', align="center")

    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='How to use it:', align="left", fn="boldLabelFont")
    cmds.text(l='1. Select Target Object(s)', align="left")
    cmds.text(l='2. Provide Offset Value(s)', align="left")
    cmds.text(l='3. Create Testing Keyframes', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Offset Amount:', align="left", fn="boldLabelFont")
    cmds.text(l='These are the values that will be added to the object.\nIf set to "0.0" it will be ignored. (No keys will be created)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Reset All Offset Values:', align="left", fn="boldLabelFont")
    cmds.text(l='Resets all offset text fields to "0.0"', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Add Inverted Offset Movement:', align="left", fn="boldLabelFont")
    cmds.text(l='Auto creates another key with the inverted offset value.\nFor example, an offset of "1.0" will also create another\noffset at "-1.0" creating an oscillating movement.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Delete Previously Created Keys:', align="left", fn="boldLabelFont")
    cmds.text(l='Deletes all keys attached to the selected controls before\ncreating new ones. (Doesn\'t include Set Driven Keys)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Create Testing Keyframes:', align="left", fn="boldLabelFont")
    cmds.text(l='Creates keyframes according to the provided settings.', align="left")
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
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

# Build UI
if __name__ == '__main__':
    build_gui_create_testing_keys()