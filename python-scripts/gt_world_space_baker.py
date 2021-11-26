"""
 GT World Space Baker
 github.com/TrevisanGMW/gt-tools - 2021-11-23
 
 1. This script stores animation according to the provided time line range for the selected controls
 2. Then forces the control back into that position by baking world space coordinates
 
 1.0.1 - 2021-11-26
 Deactivated viewport refresh when extracting/baking keys to speed up process
 Created undo chunk to bake operation
 
 TODO:
    Add sparse key option

"""
try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance
    
try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

from maya import OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import random
import sys


# Script Name
script_name = "GT - World Space Baker"

# Version:
script_version = "1.0.1"

#Python Version
python_version = sys.version_info.major

# Settings
try:
    gt_world_space_baker_settings # Keep settings if they exist
except NameError:
    gt_world_space_baker_settings = { 'stored_elements' : [],
                                      'start_time_range' : 1,
                                      'end_time_range' : 120,
                                    }
# Sotred Animation (Current Instance)
try:
    gt_world_space_baker_anim_storage
except NameError:
    gt_world_space_baker_anim_storage = {}

# Main Form ============================================================================
def build_gui_world_space_baker():
    '''
    Creates main window for world space baker
    '''
    def update_stored_settings():
        '''
        Updates settings dictionary with intfield values
        '''
        gt_world_space_baker_settings['start_time_range'] =  cmds.intField(auto_key_start_int_field, q=True, value=True)
        gt_world_space_baker_settings['end_time_range'] = cmds.intField(auto_key_end_int_field, q=True, value=True)
       

    def object_load_handler():
        ''' 
        Function to handle load button. 
        It updates the UI to reflect the loaded data and stores loaded objects into the settings dictionary.
        
        '''

        # Check If Selection is Valid
        received_valid_element = False
        
        current_selection = cmds.ls(selection=True)
        
        if len(current_selection) == 0:
            cmds.warning("Nothing selected. Please select at least one object.")
        else:
            received_valid_element = True
        
            
        # Update GUI
        if received_valid_element:
            gt_world_space_baker_settings['stored_elements'] = current_selection
            if len(current_selection) == 1:
                load_message = current_selection[0]
            else:
                load_message = str(len(current_selection)) + ' objects'
            cmds.button(selection_status_btn, l=load_message, e=True, bgc=(.6, .8, .6))
            cmds.button(ws_anim_extract_btn, e=True, en=True)
            cmds.rowColumnLayout(range_column, e=True, en=True)
            
        else:
            cmds.button(selection_status_btn, l ="Failed to Load", e=True, bgc=(1, .4, .4))
            cmds.button(ws_anim_extract_btn, e=True, en=False)
            cmds.rowColumnLayout(range_column, e=True, en=False)
  
        
    def get_auto_key_current_frame(target_integer_field='start', is_instance=False):
        '''
        Gets the current frame and auto fills an integer field.

                Parameters:
                    target_integer_field (optional, string) : Gets the current timeline frame and feeds it into the start or end integer field.
                                                              Can only be "start" or "end". Anything else will be understood as "end".
                    is_instance (optional, bool): Allow a bool argument to determine if the settings are supposed to be stored or not
                                                      This is used for secondary instances (multiple windows)

        '''
        current_time = cmds.currentTime(q=True)
        if target_integer_field == 'start':
            cmds.intField(auto_key_start_int_field, e=True, value=current_time)
        else:
            cmds.intField(auto_key_end_int_field, e=True, value=current_time)
            
        update_stored_settings()
        
        
    def validate_operation(operation='extract'):
        ''' Checks elements one last time before running the script '''
        
        update_stored_settings()
        
        if operation == 'extract':
            result = extract_world_space_data()
            if result:
                cmds.button(ws_anim_bake_btn, e=True, en=True)
                   
                plural = 'object'
                if len(gt_world_space_baker_settings.get('stored_elements')) != 1:
                    plural = 'objects'
                message = str(len(gt_world_space_baker_settings.get('stored_elements'))) + ' ' + plural + ' stored. Frames: ' + str(gt_world_space_baker_settings.get('start_time_range')) + '-' + str(gt_world_space_baker_settings.get('end_time_range'))
                cmds.text(stored_status_text, e=True, l=message) 
                
                cmds.rowColumnLayout(status_column, e=True, en=True)
                
                
        elif operation == 'bake':
            bake_world_space_data()
            
        if operation == 'refresh':
            is_data_valid = True
            try:
                for obj in gt_world_space_baker_settings.get('stored_elements'):
                    if not cmds.objExists(obj):
                        is_data_valid = False
                        
                if gt_world_space_baker_anim_storage and is_data_valid:
                    cmds.rowColumnLayout(status_column, e=True, en=True)
                    cmds.button(ws_anim_bake_btn, e=True, en=True)
                   
                    plural = 'object'
                    if len(gt_world_space_baker_settings.get('stored_elements')) != 1:
                        plural = 'objects'
                    message = str(len(gt_world_space_baker_settings.get('stored_elements'))) + ' ' + plural + ' stored. Range: ' + str(gt_world_space_baker_settings.get('start_time_range')) + '-' + str(gt_world_space_baker_settings.get('end_time_range'))
                    cmds.text(stored_status_text, e=True, l=message) 
            except:
                pass
                
                
    window_name = "build_gui_world_space_baker"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_world_space_baker = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\
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
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_world_space_baker())
    cmds.separator(h=5, style='none') # Empty Space
    
    # Body ====================

            
    
    # 1. Selection
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,20)], p=content_main)
    cmds.text('1. Taget(s):')
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 120),(2, 120)], cs=[(1,0)])
    selection_load_btn = cmds.button(l ="Load Selection", c=lambda x:object_load_handler(), w=115)
    selection_status_btn = cmds.button(l ="Not loaded yet", bgc=(.2, .2, .2), w=115, \
                       c=lambda x:select_existing_objects(gt_world_space_baker_settings.get('stored_elements')))
    
    # 2. Range
    range_column = cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,20)], p=content_main, en=False)
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text('2. Animation Range:')
    cmds.separator(h=10, style='none') # Empty Space
    
    anim_range_column = cmds.rowColumnLayout(nc=6, cw=[(1, 40),(2, 40),(3, 30),(4, 30),(5, 40),(6, 30)], cs=[(1, 10), (4, 10)])
    cmds.text('Start:')
    auto_key_start_int_field = cmds.intField(value=gt_world_space_baker_settings.get('start_time_range'), cc=lambda x:update_stored_settings())
    cmds.button(l ="Get", c=lambda x:get_auto_key_current_frame(), h=5) #L
    cmds.text('End:')
    auto_key_end_int_field = cmds.intField(value=gt_world_space_baker_settings.get('end_time_range'), cc=lambda x:update_stored_settings())
    cmds.button(l ="Get", c=lambda x:get_auto_key_current_frame('end'), h=5) #L
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,20)], p=content_main)
    cmds.separator(h=7, style='none') # Empty Space
    ws_anim_extract_btn = cmds.button(l ="Extract World Space", bgc=(.3, .3, .3), c=lambda x:validate_operation(), en=False)    
    cmds.separator(h=7, style='none') # Empty Space     
    

    # 3. Status
    status_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main, en=False)
    cmds.separator(h=7) # Empty Space
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text('3. Stored Data Status:')
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 90),(2, 143),(4, 37)], cs=[(1, 10),(2, 0),(3, 0),(4, 0)])
    cmds.text(l='Stored Keys:  ', align="center", fn="boldLabelFont")
    stored_status_text = cmds.text(l='No Data', align="center", fn="tinyBoldLabelFont")
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,20)], p=content_main)
    cmds.separator(h=6, style='none') # Empty Space

    
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,20)], p=content_main)
                                                                                           
    ws_anim_bake_btn = cmds.button(l ="Bake World Space", bgc=(.3, .3, .3), c=lambda x:validate_operation('bake'), en=False)                                                                                                 
    cmds.separator(h=15, style='none') # Empty Space
    
    # Show and Lock Window
    cmds.showWindow(build_gui_world_space_baker)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/buttonManip.svg')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)
    
    validate_operation('refresh')

    # Main GUI Ends Here =================================================================================
    
            
    

# Creates Help GUI
def build_gui_help_world_space_baker():
    ''' Creates Help window for World Space Baker '''
    window_name = "build_gui_help_world_space_baker"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p=window_name)
   
    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=15, style='none', p="main_column") # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 210)], cs=[(1,55)], p="main_column")
    
    cmds.text(l='1. Use "Load Selection" to define targets\n2. Enter animation range (Start & End)\n3. Extract and store transforms\n4. Bake transforms when necessary', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
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
        ''' Closes Help Window '''
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def select_existing_objects(stored_list):
    ''' 
    Selects loaded object in case they exist
    
            Parameters:
                stored_list (list): List of objects to select
    
    '''
    missing_elements = False
    found_elements = []
    print("#" * 32 + " Objects List " + "#" * 32)
    for obj in stored_list:
        if cmds.objExists(obj):
            print(obj)
            found_elements.append(obj)
        else:
            print(obj + " no longer exists!")
            missing_elements = True
    print("#" * 80)
    if missing_elements:
        cmds.inViewMessage(amg='Some elements are <span style=\"color:#FF0000;\">missing!</span>', pos='botLeft', fade=True, alpha=.9)
        cmds.inViewMessage(amg='Open script editor for more information.', pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.inViewMessage(amg='Stored elements have been selected.', pos='botLeft', fade=True, alpha=.9)
    if stored_list != []:
        cmds.select(found_elements)

def extract_world_space_data():
    '''
    Extracts the world space data from the objects that were loaded into selections
    '''
    # Double check target availability
    available_ctrls = []
    for obj in gt_world_space_baker_settings.get('stored_elements'):
        if cmds.objExists(obj):
            available_ctrls.append(obj)

    # Store Current Time
    original_time = cmds.currentTime(q=True)
    
    # Last Validation
    is_valid = True
    if available_ctrls == 0:
        is_valid = False
        cmds.warning('Loaded objects couldn\'t be found. Please review your settings and try again')
    elif gt_world_space_baker_settings.get('start_time_range') >= gt_world_space_baker_settings.get('end_time_range'):
        is_valid = False
        cmds.warning('Starting frame can\'t be higher than ending frame. Review your animation range settings and try again.')
        
    # Extract Keyframes:
    if is_valid:
        try:
            cmds.refresh(suspend=True)
            for obj in available_ctrls:
                attributes = cmds.listAnimatable(obj)
                needs_ws_transforms = True
                frame_translate_values = []
                frame_rotate_values = []
                for attr in attributes:
                    
                    try:
                        # short_attr = attr.split('.')[-1]
                        # frames = cmds.keyframe(obj, q=1, at=short_attr)
                        # values = cmds.keyframe(obj, q=1, at=short_attr, valueChange=True)
                        # in_angle_tangent = cmds.keyTangent(obj, at=short_attr, inAngle=True, query=True)
                        # out_angle_tanget = cmds.keyTangent(obj, at=short_attr, outAngle=True, query=True)
                        # is_locked = cmds.keyTangent(obj, at=short_attr, weightLock=True, query=True)
                        # in_weight = cmds.keyTangent(obj, at=short_attr, inWeight=True, query=True)
                        # out_weight = cmds.keyTangent(obj, at=short_attr, outWeight=True, query=True)
                        # in_tangent_type = cmds.keyTangent(obj, at=short_attr, inTangentType=True, query=True)
                        # out_tangent_type = cmds.keyTangent(obj, at=short_attr, outTangentType=True, query=True)
                        # gt_world_space_baker_anim_storage['{}.{}'.format(obj, short_attr)] = zip(frames, values, in_angle_tangent, out_angle_tanget, is_locked, in_weight, out_weight, in_tangent_type, out_tangent_type)
                        
                        # WS Values # Translate and Rotate for the desired frame range
                        if 'translate' in attr or 'rotate' in attr:  
                            if needs_ws_transforms:
                                cmds.currentTime(gt_world_space_baker_settings.get('start_time_range'))
                                
                                for index in range(gt_world_space_baker_settings.get('end_time_range') - gt_world_space_baker_settings.get('start_time_range')+1):
                                    frame_translate_values.append([cmds.currentTime(q=True), cmds.xform(obj, ws=True, q=True, t=True)])
                                    frame_rotate_values.append([cmds.currentTime(q=True), cmds.xform(obj, ws=True, q=True, ro=True)])
                                    cmds.currentTime(cmds.currentTime(q=True)+1)
                                needs_ws_transforms = False
                                
                            
                            if attr.split('.')[-1].startswith('translate'):
                                gt_world_space_baker_anim_storage['{}.{}'.format(obj, 'translate')] = frame_translate_values
                                
                            if attr.split('.')[-1].startswith('rotate'):
                                gt_world_space_baker_anim_storage['{}.{}'.format(obj, 'rotate')] = frame_rotate_values
                        
                        
                            # if attr.endswith('X'):
                            #     channel_index = 0
                            #     channel_str = 'X'
                            # elif attr.endswith('Y'):
                            #     channel_index = 1
                            #     channel_str = 'Y'
                            # elif attr.endswith('Z'):
                            #     channel_index = 2
                            #     channel_str = 'Z'
                            

                            # if attr.split('.')[-1].startswith('translate'):
                            #     desired_data = []
                            #     for frame_translate in frame_translate_values:
                            #         desired_data.append([frame_translate[0], frame_translate[1][channel_index]])
                            #     gt_world_space_baker_anim_storage['{}.{}'.format(obj, 'translate' + channel_str)] = desired_data
                          

                            # if attr.split('.')[-1].startswith('rotate'):
                            #     desired_data = []
                            #     for frame_translate in frame_translate_values:
                            #         desired_data.append([frame_translate[0], frame_translate[1][channel_index]])
                            #     gt_world_space_baker_anim_storage['{}.{}'.format(obj, 'rotate' + channel_str)] = desired_data
                    except:
                        pass # 0 keyframes
        except:
            pass
        finally:
            cmds.refresh(suspend=False)
            
            
    cmds.currentTime(original_time)
    return True
                
def bake_world_space_data():
    '''
    Bakes extracted data using stored world space dictionary (only translate and rotate)
    '''

    # Store Current Time
    original_time = cmds.currentTime(q=True)
    
    # Last Validation
    is_valid = True
    if len(gt_world_space_baker_anim_storage) == 0:
        is_valid = False
        cmds.warning('Couldn\'t find stored data. Please try extracting it again.')
        
    # Bake Keyframes:
    if is_valid:
        try:
            cmds.refresh(suspend=True)
            cmds.undoInfo(openChunk=True, chunkName='GT World Space Bake')
            for key, dict_value in gt_world_space_baker_anim_storage.iteritems():
                for key_data in dict_value:
                    try:
                        obj, attr = key.split('.')
                        time = key_data[0]
                        value = key_data[1]
                        cmds.currentTime(time)
                        if attr == 'translate':
                            cmds.xform(obj, ws=True, t=value)
                            cmds.setKeyframe(obj, time=time, attribute='tx')
                            cmds.setKeyframe(obj, time=time, attribute='ty')
                            cmds.setKeyframe(obj, time=time, attribute='tz')
                        if attr == 'rotate':
                            cmds.xform(obj, ws=True, ro=value)
                            cmds.setKeyframe(obj, time=time, attribute='rx')
                            cmds.setKeyframe(obj, time=time, attribute='ry')
                            cmds.setKeyframe(obj, time=time, attribute='rz')
                    except:
                        pass
        except:
            pass
        finally:
            cmds.undoInfo(closeChunk=True, chunkName='GT World Space Bake')
            cmds.refresh(suspend=False)
            
                        
    # Reset to Original Time
    cmds.currentTime(original_time)
             

#Build UI
if __name__ == '__main__':
    build_gui_world_space_baker()
