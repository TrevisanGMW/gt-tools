"""
 GT Color Manager - A script for managing the color of many objects at the same time (outliner and other overrides)
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-13
 https://github.com/TrevisanGMW
 
"""
import maya.cmds as cmds
import random
import math
import copy
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
script_name = "GT Color Manager"

# Version
script_version = "1.0";

gt_color_manager_settings = { 'current_color': [.3,.3,.3],
                              'default_mode' : 'Drawing Override',
                              'default_target' : 'Transform',
                              'default_set_outliner' : True,
                              'default_set_viewport' : False}

# Store Default Values for Reseting
gt_color_manager_settings_default_values = copy.deepcopy(gt_color_manager_settings)

def get_persistent_settings_color_manager():
    ''' 
    Checks if persistant settings for GT Color Manager exists and transfer them to the settings variables.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    
    set_outliner_exists = cmds.optionVar(exists=("gt_color_manager_set_outliner"))
    set_viewport_exists = cmds.optionVar(exists=("gt_color_manager_set_viewport"))
    set_current_color_exists = cmds.optionVar(exists=("gt_color_manager_current_color"))
    set_target_exists = cmds.optionVar(exists=("gt_color_manager_target"))
    set_mode_exists = cmds.optionVar(exists=("gt_color_manager_mode"))
    

    if set_outliner_exists:
        gt_color_manager_settings['default_set_outliner'] = int(cmds.optionVar(q=("gt_color_manager_set_outliner")))

    if set_viewport_exists:
        gt_color_manager_settings['default_set_viewport'] = int(cmds.optionVar(q=("gt_color_manager_set_viewport")))


    if set_current_color_exists:
        try:
            color_str_list = cmds.optionVar(q=("gt_color_manager_current_color")).replace('[','').replace(']','').split(',')
            gt_color_manager_settings['current_color'] = [float(color_str_list[0]), float(color_str_list[1]), float(color_str_list[2])]
        except:
            pass
    
    if set_target_exists:
        gt_color_manager_settings['default_target'] = str(cmds.optionVar(q=("gt_color_manager_target")))

    if set_mode_exists:
        gt_color_manager_settings['default_mode'] = str(cmds.optionVar(q=("gt_color_manager_mode")))
    
    

def set_persistent_settings_color_manager(option_var_name, option_var_string):
    ''' 
    Stores persistant settings for GT Color Manager.
    It assumes that persistent settings are using the cmds.optionVar function.
    
        Parameters:
                option_var_name (string): name of the optionVar string. Must start with script name + name of the variable
                option_var_string (string): string to be stored under the option_var_name
                    
    '''
    if option_var_string != '' and option_var_name != '':
        cmds.optionVar( sv=(str(option_var_name), str(option_var_string)))

    

def reset_persistent_settings_color_manager():
    ''' Resets persistant settings for GT Renamer '''

    cmds.optionVar( remove='gt_color_manager_set_outliner' )
    cmds.optionVar( remove='gt_color_manager_set_viewport' )
    cmds.optionVar( remove='gt_color_manager_current_color' )
    cmds.optionVar( remove='gt_color_manager_target' )
    cmds.optionVar( remove='gt_color_manager_mode' )

    for def_value in gt_color_manager_settings_default_values:
        for value in gt_color_manager_settings:
            if def_value == value:
                gt_color_manager_settings[value] = gt_color_manager_settings_default_values[def_value]

    get_persistent_settings_color_manager()
    build_gui_color_manager()
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')




# Main Form ============================================================================
def build_gui_color_manager():
    ''' Builds Main UI '''
    window_name = "build_gui_color_manager"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_color_manager = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
                             
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 330)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 260), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_color_manager())
    cmds.separator(h=3, style='none', p=content_main) # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 320)], cs=[(1,10)], p=content_main)

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)])
        
    cmds.separator(h=20, p=body_column)
        
    mid_container = cmds.rowColumnLayout(p=body_column, h= 25,nc=2, cw=[(1, 160)], cs=[(1,5),(2,15)])
    mode_option = cmds.optionMenu(label='Mode', cc=lambda x:set_persistent_settings_color_manager('gt_color_manager_mode', cmds.optionMenu(mode_option, q=True, value=True)))
    cmds.menuItem( label='Drawing Override' )
    cmds.menuItem( label='Wireframe Color' )
    
    if gt_color_manager_settings.get('default_mode') == 'Drawing Override':
        cmds.optionMenu(mode_option, e=True, select=1) # 1-based selection
    else:
        cmds.optionMenu(mode_option, e=True, select=2) # 1-based selection
    
    target_option = cmds.optionMenu(label='Target', cc=lambda x:set_persistent_settings_color_manager('gt_color_manager_target', cmds.optionMenu(target_option, q=True, value=True)))
    cmds.menuItem( label='Transform' )
    cmds.menuItem( label='Shape' )
    
    if gt_color_manager_settings.get('default_target') == 'Transform':
        cmds.optionMenu(target_option, e=True, select=1) # 1-based selection
    else:
        cmds.optionMenu(target_option, e=True, select=2) # 1-based selection

    # Main Color Picker
    cmds.separator(h=10, style='none', p=body_column) # Empty Space
    color_container = cmds.rowColumnLayout(p=body_column, nc=1, h= 25, cw=[(1,310)], cs=[(1,5)])
    color_slider = cmds.colorSliderGrp(label='Current Color  ', rgb=(gt_color_manager_settings.get("current_color")[0], \
                                                                gt_color_manager_settings.get("current_color")[1],\
                                                                gt_color_manager_settings.get("current_color")[2]),\
                                                                cal=[1,'left'],
                                                                columnWidth=((1,80),(3,130)), cc=lambda x:update_stored_values())
    
    cmds.separator(h=7, style='none', p=body_column) # Empty Space
    
    c_btn_w = 30
    c_btn_s = 1
    cmds.rowColumnLayout(nc=10, cw=[(1,c_btn_w),(2,c_btn_w),(3,c_btn_w),(4,c_btn_w),(5,c_btn_w),(6,c_btn_w),(7,c_btn_w),(8,c_btn_w),(9,c_btn_w),(10,c_btn_w)],\
                         cs=[(1,5),(2,c_btn_s),(3,c_btn_s),(4,c_btn_s),(5,c_btn_s),(6,c_btn_s),(7,c_btn_s),(8,c_btn_s),(9,c_btn_s),(10,c_btn_s)], p=body_column)
    color_buttons_height = 20
    
    # Rainbow
    c_btn_01 = [1,.25,.25] # Red
    c_btn_02 = [1,.45,.15] # Orange
    c_btn_03 = [1,1,.35] # Yellow
    c_btn_04 = [.5,1,.20] # Green
    c_btn_05 = [.3,1,.8] # Cyan
    c_btn_06 = [.2,0.6,1] # Soft Blue
    c_btn_07 = [0,.2,1] # Blue
    c_btn_08 = [1,.45,.70] # Pink
    c_btn_09 = [.75,.35,.90] # Soft Purple
    c_btn_10 = [.45,0.2,0.9] # Purple
    

    cmds.button(l='', bgc=c_btn_01, h=color_buttons_height, c=lambda x:apply_preset(c_btn_01))
    cmds.button(l='', bgc=c_btn_02, h=color_buttons_height, c=lambda x:apply_preset(c_btn_02))
    cmds.button(l='', bgc=c_btn_03, h=color_buttons_height, c=lambda x:apply_preset(c_btn_03))
    cmds.button(l='', bgc=c_btn_04, h=color_buttons_height, c=lambda x:apply_preset(c_btn_04))
    cmds.button(l='', bgc=c_btn_05, h=color_buttons_height, c=lambda x:apply_preset(c_btn_05))
    cmds.button(l='', bgc=c_btn_06, h=color_buttons_height, c=lambda x:apply_preset(c_btn_06))
    cmds.button(l='', bgc=c_btn_07, h=color_buttons_height, c=lambda x:apply_preset(c_btn_07))
    cmds.button(l='', bgc=c_btn_08, h=color_buttons_height, c=lambda x:apply_preset(c_btn_08))
    cmds.button(l='', bgc=c_btn_09, h=color_buttons_height, c=lambda x:apply_preset(c_btn_09))
    cmds.button(l='', bgc=c_btn_10, h=color_buttons_height, c=lambda x:apply_preset(c_btn_10))
    
    cmds.separator(h=7, style='none', p=body_column) # Empty Space
    cmds.separator(h=15, p=body_column)
    bottom_container = cmds.rowColumnLayout(p=body_column,adj=True)
        
    checkbox_column = cmds.rowColumnLayout(p=bottom_container,nc=3, cw=[(1, 80),(2, 100),(3, 100)], cs=[(1,0),(2,60)],nbg=True)
    cmds.text('Set Color For')
    outliner_chk = cmds.checkBox(label='Outliner', p=checkbox_column, nbg=False, value=gt_color_manager_settings.get('default_set_outliner'),\
                                cc=lambda x:set_persistent_settings_color_manager('gt_color_manager_set_outliner',\
                                str(int(cmds.checkBox(outliner_chk, q=True, value=True)))))
    viewport_chk = cmds.checkBox(label='Viewport', p=checkbox_column, value=gt_color_manager_settings.get('default_set_viewport'),\
                                 cc=lambda x:set_persistent_settings_color_manager('gt_color_manager_set_viewport',\
                                 str(int(cmds.checkBox(viewport_chk, q=True, value=True)))))
    
    cmds.separator(h=10, style='none', p=bottom_container) # Empty Space
    cmds.button(l ="Reset", c=lambda x:set_color(reset=True), p=bottom_container) # Empty Space
    cmds.separator(h=5, style='none', p=bottom_container)
    cmds.button(l ="Apply", bgc=(.6, .6, .6), c=lambda x:set_color(), p=bottom_container) 
    cmds.separator(h=10, style='none', p=bottom_container) # Empty Space
                                                                                                                              
    def update_stored_values():
        ''' Updates Current Color '''
        gt_color_manager_settings["current_color"] = cmds.colorSliderGrp(color_slider, q=True, rgb=True)
        set_persistent_settings_color_manager('gt_color_manager_current_color', cmds.colorSliderGrp(color_slider, q=True, rgb=True))


    def apply_preset(rgb_color):
        '''
        Updates current color with the provided input then runs main function.
        
                Parameters:
                    rgb_color (list): a list of three floats describing an RGB Color (e.g. [1,0,0] for Red)
        
        '''
        managed_r = math.pow((rgb_color[0] + 0.055) / 1.055, 2.4)
        managed_g = math.pow((rgb_color[1] + 0.055) / 1.055, 2.4)
        managed_b = math.pow((rgb_color[2] + 0.055) / 1.055, 2.4)
        
        cmds.colorSliderGrp(color_slider, e=True, rgb= (managed_r,managed_g,managed_b))
        update_stored_values()
        set_color()

    def set_color(reset=False):
        '''' 
        Uses the provided settings to manage colors (Main function of this script) 
        
                Parameter:
                    reset (bool): Type of operation. Reset active will restore default colors.
        
        '''
        errors = ''
        try:
            function_name = 'GT Color Manager - Set Color'
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            valid_selection = True
            objects_to_color = []
            colored_total = 0
            
            # Grab Necessary Values
            mode = cmds.optionMenu(mode_option, q=True, value=True)
            target = cmds.optionMenu(target_option, q=True, value=True)
            color = gt_color_manager_settings.get('current_color')
            set_outliner = cmds.checkBox(outliner_chk, q=True, value=True)
            set_viewport = cmds.checkBox(viewport_chk, q=True, value=True)
            
            # Functions
            def set_color_drawing_override(obj_to_set):
                ''' 
                Uses drawing override settings to set the color of an object 

                        Parameters:
                            obj_to_set (str): Name (path) of the object to affect.
                
                '''
                using_wireframe = cmds.getAttr(obj_to_set + '.useObjectColor')
                if using_wireframe != 0:
                    cmds.color( obj_to_set )
                cmds.setAttr(obj_to_set + '.overrideEnabled', 1)
                cmds.setAttr(obj_to_set + '.overrideRGBColors', 1)
                cmds.setAttr(obj_to_set + '.overrideColorR', color[0])
                cmds.setAttr(obj_to_set + '.overrideColorG', color[1])
                cmds.setAttr(obj_to_set + '.overrideColorB', color[2])
                return 1

            def set_color_wireframe_tool(obj_to_set):
                ''' 
                Uses wireframe color to set the color of an object 
                
                        Parameters:
                            obj_to_set (str): Name (path) of the object to affect.
                
                '''
                using_override = cmds.getAttr(obj_to_set + '.overrideEnabled')
                if using_override: 
                    cmds.setAttr(obj_to_set + '.overrideEnabled', 0)
                    cmds.setAttr(obj_to_set + '.overrideColorR', 0)
                    cmds.setAttr(obj_to_set + '.overrideColorG', 0)
                    cmds.setAttr(obj_to_set + '.overrideColorB', 0)
                cmds.color( obj_to_set, rgb=(color[0], color[1], color[2]) )
                return 1

            def set_color_outliner(obj_to_set):
                ''' 
                Sets the outliner color for the selected object 
                
                        Parameters:
                            obj_to_set (str): Name (path) of the object to affect.
                
                '''
                cmds.setAttr(obj_to_set + '.useOutlinerColor', 1)
                cmds.setAttr(obj_to_set + '.outlinerColorR', color[0])
                cmds.setAttr(obj_to_set + '.outlinerColorG', color[1])
                cmds.setAttr(obj_to_set + '.outlinerColorB', color[2])
                return 1
   
            def set_color_reset(obj_to_set, reset_overrides=False, reset_wireframe=False, reset_outliner=False):
                ''' Resets the color of the selected objects
                
                        Parameters:
                            obj_to_set (str): Name (path) of the object to affect.
                            reset_overrides (bool) : Reseting Overrides
                            reset_wireframe (bool) : Reseting Wireframe
                            reset_outliner (bool) : Reseting Outliner
                
                '''
                if reset_overrides:
                    using_override = cmds.getAttr(obj_to_set + '.overrideEnabled')
                    if using_override: 
                        cmds.setAttr(obj_to_set + '.overrideEnabled', 0)
                        cmds.setAttr(obj_to_set + '.overrideColorR', 0)
                        cmds.setAttr(obj_to_set + '.overrideColorG', 0)
                        cmds.setAttr(obj_to_set + '.overrideColorB', 0)
                
                if reset_wireframe:
                    using_wireframe = cmds.getAttr(obj_to_set + '.useObjectColor')
                    if using_wireframe != 0:
                        cmds.color( obj_to_set )
                
                if reset_outliner:
                    try:
                        cmds.setAttr(obj_to_set + '.useOutlinerColor', 0)
                    except:
                        pass
                return 1
          
            selection = cmds.ls(selection=True)
 
            if len(selection) < 1:
                valid_selection = False
                cmds.warning('You need to select at least one object.')
                
            if valid_selection:
            # Determine what to color
                if target == 'Transform':
                    objects_to_color = selection
                else:
                    for sel in selection:
                        shapes = cmds.listRelatives(sel, shapes=True, fullPath=True) or []
                        for shape in shapes:
                            objects_to_color.append(shape)
                
                # Determine total of objects to be colored
                if len(objects_to_color) < 1:
                    valid_selection = False
                    cmds.warning('No shapes were found. Make sure you\'re using the correct "Target" option.')
  
                
            # Set Color
            if valid_selection and reset == False:
                for obj in objects_to_color:
                    if set_viewport:
                        try:
                            if mode == 'Drawing Override':
                                colored_total += set_color_drawing_override(obj)
                            else:
                                colored_total += set_color_wireframe_tool(obj)
                        except Exception as e:
                            errors += str(e) + '\n'
                    if set_outliner:
                        try:
                            if set_viewport:
                                set_color_outliner(obj)
                            else:
                                colored_total += set_color_outliner(obj)
                        except Exception as e:
                            errors += str(e) + '\n'
                            
            if valid_selection and reset == True:
                for obj in selection:
                    if set_viewport:
                        try:
                           colored_total += set_color_reset(obj, reset_overrides=True, reset_wireframe=True)
                        except Exception as e:
                            errors += str(e) + '\n'
                    if set_outliner:
                        try:
                            if set_viewport:
                                set_color_reset(obj, reset_outliner=True)
                            else:
                                colored_total += set_color_reset(obj, reset_outliner=True)
                        except Exception as e:
                            errors += str(e) + '\n'
            
            # Create message 
            message = '<' + str(random.random()) + '><span style=\"color:#FF0000;text-decoration:underline;\">' +  str(colored_total) + ' </span>'
            is_plural = 'objects were'
            if colored_total == 1:
                is_plural = 'object was'
            if reset:
                message += is_plural + '  reset to the default color.'
            else:
                message += is_plural + '  colored.'
            
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
                
        except Exception as e:
            errors += str(e) + '\n'
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)
        if errors != '':
            cmds.warning('An error occured. Open the script editor for more information.')
            print('######## Errors: ########')
            print(errors)
    
    # Show and Lock Window
    cmds.showWindow(build_gui_color_manager)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/render_swColorPerVertex.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_color_manager():
    window_name = "build_gui_help_color_manager"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=title_bgc_color,  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    
    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    
    cmds.text(l='Script for quickly coloring elements in Maya', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Modes:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Drawing Override:\n  Utilize "Object > Object Display > Drawing Overrides" to set color', align="center", font='smallPlainLabelFont')
    cmds.text(l='- Wireframe Color:\n  Utilize "Display > Wireframe Color..." to set color', align="center", font='smallPlainLabelFont')
   
    cmds.separator(h=10, style='none') # Empty Space
   
    cmds.text(l='Target:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Transform:\n  Colorize actual selection. Usually a "transform"', align="center", font='smallPlainLabelFont')
    cmds.text(l='- Wireframe Color:\n  Colorize the shape node inside the transform', align="center", font='smallPlainLabelFont')
    

    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Current Color:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='The color used in the operation', font='smallPlainLabelFont')
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Color Presets:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='A list of common colors. When clicking it sets the color', font='smallPlainLabelFont')
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Set Color For:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Outliner:\n  Control the outliner color', align="center", font='smallPlainLabelFont')
    cmds.text(l='- Wireframe Color:\n  Control the wireframe color seen in the viewport', align="center", font='smallPlainLabelFont')

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
    cmds.button(l='Reset Persistent Settings', h=30, c=lambda args: reset_persistent_settings_color_manager())
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


# Build Main Dialog
if __name__ == '__main__':
    get_persistent_settings_color_manager()
    build_gui_color_manager()  