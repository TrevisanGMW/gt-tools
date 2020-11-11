"""
 GT Check for Updates - This script compared your current GT Tools version with the latest release.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-10 - github.com/TrevisanGMW

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

import os
import re
import maya.cmds as cmds
from maya import OpenMayaUI as omui
from httplib2 import Http
from json import dumps
from json import loads

# Script Version (This Script)
script_version = '1.0'
gt_tools_latest_release_api = "https://api.github.com/repos/TrevisanGMW/gt-tools/releases/latest"

# Versions Dictionary
gt_check_for_updates = { 'current_version' : "v0.0.0",
                         'latest_release' : "v0.0.0" } 


def build_gui_gt_check_updates():
    ''' Temp '''
    window_name = "build_gui_gt_check_updates"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= 'GT Check for Updates - v' + script_version, mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 410)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text("GT Check for Updates", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    # Body ====================
    checklist_spacing = 4

    cmds.text(l='\ngithub.com/TrevisanGMW/gt-tools', align="center")
    cmds.separator(h=7, style='none') # Empty Space
    
    
    general_column_width = [(1, 210),(2, 110),(4, 37)]
    
    cmds.rowColumnLayout(nc=3, cw=general_column_width, cs=[(1, 18),(2, 0),(3, 0),(4, 0)], p="main_column")
    cmds.text(l='Status:', align="center", fn="boldLabelFont")
    update_status = cmds.text(l='...', align="center")
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=3, cw=general_column_width, cs=[(1, 18),(2, 0),(3, 0),(4, 0)], p="main_column")
    cmds.text(l='Web Response:', align="center", fn="boldLabelFont")
    web_response_text = cmds.text(l='...', align="center", fn="tinyBoldLabelFont", bgc=(1, 1, 0))
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=3, cw=general_column_width, cs=[(1, 18),(2, 0),(3, 0),(4, 0)], p="main_column")
    cmds.text(l='Installed Version:', align="center", fn="boldLabelFont")
    installed_version_text = cmds.text(l='...', align="center")
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=3, cw=general_column_width, cs=[(1, 18),(2, 0),(3, 0),(4, 0)], p="main_column")
    cmds.text(l='Latest Release:', align="center", fn="boldLabelFont")
    latest_version_text = cmds.text(l='...', align="center")
    cmds.separator(h=7, style='none') # Empty Space

    
    cmds.separator(h=15, style='none') # Empty Space

    # Changelog =============
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p="main_column")
    cmds.text(l='Latest Release Changelog:', align="center", fn="boldLabelFont") 
    cmds.text(l='Use the refresh button to check again:', align="center", fn="smallPlainLabelFont") 
    cmds.separator(h=checklist_spacing, style='none') # Empty Space
   
   
    output_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="obliqueLabelFont")
    
    cmds.separator(h=10, style='none') # Empty Space

    # Refresh Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Refresh', h=30, c=lambda args: reroute_errors('check_for_updates'))
    cmds.separator(h=8, style='none')
    update_btn = cmds.button(l='Update', h=30, en=False, c=lambda args: reroute_errors('open_releases_page'))
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/RS_import_layer.png')
    widget.setWindowIcon(icon)
    
    
    def reroute_errors(operation):
        ''' Temp '''
        try:
            if operation == 'open_releases_page':
                open_releases_page()
            else:
                check_for_updates()
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    
    
    def open_releases_page():
        ''' Temp '''
        cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools', absolute=True) 
        
    def check_for_updates():
        ''' Temp '''
        
        error_detected = False
        
        # Define Current Version
        stored_gt_tools_version_exists = cmds.optionVar(exists=("gt_tools_version"))

        if stored_gt_tools_version_exists:
            gt_check_for_updates['current_version'] = "v" + str(cmds.optionVar(q=("gt_tools_version")))
        else:
            gt_check_for_updates['current_version'] = 'v?.?.?'
        
        # Retrive Latest Version
        try:
            response = get_latest_gttools_release(gt_tools_latest_release_api)
        except:
            error_detected = True
        
        if not error_detected:
            gt_check_for_updates['latest_version'] = response.get('tag_name')
            
            cmds.text(web_response_text, e=True, l='OK', bgc=(0, 1, 0))
            cmds.text(installed_version_text, e=True, l=gt_check_for_updates.get('current_version'))
            cmds.text(latest_version_text, e=True, l=gt_check_for_updates.get('latest_version'))
            
            current_version_int = int(re.sub("[^0-9]", "", gt_check_for_updates.get('current_version')))
            latest_version_int = int(re.sub("[^0-9]", "", gt_check_for_updates.get('latest_version')))
            
            if current_version_int < latest_version_int:
                print('needs update')
                cmds.button(update_btn, e=True, en=True)
                cmds.text(update_status, e=True, l="New Update Available!", fn="tinyBoldLabelFont")#, bgc=(0, 1, 1))
                #cmds.text(update_status
            else:
                cmds.text(update_status, e=True, l="You have the latest version", fn="tinyBoldLabelFont")
            
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=response.get('body'))
    
        
        
    reroute_errors('')


def get_latest_gttools_release(github_api):
    '''
    Requests the name of the webhook and returns a string representing it

            Parameters:
                github_api (str): Github API
                
            Returns:
                name (str): The name of the webhook (or error string, if operation failed)
    '''
    http_obj = Http()
    response, content = http_obj.request(github_api)
    success_codes = [200, 201, 202, 203, 204, 205, 206]
    print (response)
    if response.status in success_codes: 
        response_content_dict = loads(content) 
        return response_content_dict
    else:
        raise Exception('Script failed to retrieve the information about latest version.')


#cmds.optionVar( sv=('gt_tools_version', '0.1.1') )
#cmds.optionVar( sv=('gt_tools_version', '1.5.3') )
#Build GUI
if __name__ == '__main__':
    build_gui_gt_check_updates()


