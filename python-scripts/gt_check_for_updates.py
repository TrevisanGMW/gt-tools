"""
 GT Check for Updates - This script compares your current GT Tools version with the latest release.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-10 - github.com/TrevisanGMW
 
 1.1 - 2020-11-11
 Fixed a few issues with the color of the UI.
 Updated link to show only latest release.
 The "Update" button now is disabled after refreshing.
 
 1.2 - 2020-11-13
 Added code to try to retrieve the three latest releases
 
 1.3 - 2020-11-15
 Changed title background color to grey
 Added dates to changelog
 
 1.4 - 2020-12-04
 Added a text for when the version is higher than expected (Unreleased Version)
 Added an auto check for updates so user's don't forget to update
 Added threading support (so the http request doesn't slow things down)

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
from datetime import datetime
from httplib2 import Http
from json import dumps
from json import loads
import maya.utils as utils
import maya.cmds as cmds
import threading
import os
import re

# Script Version (This Script)
script_version = '1.4'
gt_tools_latest_release_api = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/latest'
gt_tools_tag_release_api = 'https://api.github.com/repos/TrevisanGMW/gt-tools/releases/tags/'

# Versions Dictionary
gt_check_for_updates = { 'current_version' : "v0.0.0",
                         'latest_release' : "v0.0.0",
                         'def_auto_updater_status' : True,
                         'def_auto_updater_interval' : 30 } 


def build_gui_gt_check_for_updates():
    ''' Build a GUI to show current and latest versions '''
    window_name = "build_gui_gt_check_for_updates"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= 'GT Check for Updates - (v' + script_version + ')', mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 410)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text("GT Check for Updates", bgc=title_bgc_color,  fn="boldLabelFont", align="center")
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
    cmds.rowColumnLayout(nc=2, cw=[(1, 280),(2, 115)], cs=[(1,10),(2,5)], p="main_column")
    auto_update_btn = cmds.button(l='Auto Check For Updates: Activated', h=30, c=lambda args: toggle_auto_updater())
    auto_updater_interval_btn = cmds.button(l='Interval: 15 days', h=30, c=lambda args: change_auto_update_interval())
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p="main_column")
    cmds.separator(h=5, style='none')
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
    icon = QIcon(':/SP_FileDialogToParent_Disabled.png')
    widget.setWindowIcon(icon)
    

    def toggle_auto_updater(refresh_only=False):
        ''' 
        Toggle the auto check for updates button while updating an optionVar that controls this behaviour
        
                Parameters:
                    refresh_only (bool): Is it only refreshing or toggling?

        '''
        persistent_auto_updater_exists = cmds.optionVar(exists=('gt_check_for_updates_auto_active'))
        if persistent_auto_updater_exists:
            current_status = bool(cmds.optionVar(q=("gt_check_for_updates_auto_active")))
        else:
            current_status = gt_check_for_updates.get('def_auto_updater_status')
        
        if refresh_only:
            if current_status:
                cmds.button(auto_update_btn, e=True, label='Auto Check For Updates: Activated')
                cmds.button(auto_updater_interval_btn, e=True, en=True)
            else:
                cmds.button(auto_update_btn, e=True, label='Auto Check For Updates: Deactivated')
                cmds.button(auto_updater_interval_btn, e=True, en=False)
                
        
        if not refresh_only:
            if current_status:
                cmds.button(auto_update_btn, e=True, label='Auto Check For Updates: Deactivated')
                cmds.optionVar( iv=('gt_check_for_updates_auto_active', int(False)))
                cmds.button(auto_updater_interval_btn, e=True, en=False)
            else:
                cmds.button(auto_update_btn, e=True, label='Auto Check For Updates: Activated')
                cmds.optionVar( iv=('gt_check_for_updates_auto_active', int(True)))
                cmds.button(auto_updater_interval_btn, e=True, en=True)

    def change_auto_update_interval(refresh_only=False):
        ''' 
        Toggle the auto check for updates button while updating an optionVar that controls this behaviour
        
                Parameters:
                    refresh_only (bool): Is it only refreshing or toggling?

        '''
        check_interval = gt_check_for_updates.get('def_auto_updater_interval')
        persistent_check_interval_exists = cmds.optionVar(exists=('gt_check_for_updates_interval_days'))
        if persistent_check_interval_exists:
            check_interval = int(cmds.optionVar(q=("gt_check_for_updates_interval_days")))
                  
        interval_list = {'half_month' : 15,
                         'one_month' : 30,
                         'three_months' : 91,
                         'six_months': 182,
                         'one_year': 365}
                
        if not refresh_only:
            if check_interval == interval_list.get('half_month'):
                check_interval = interval_list.get('one_month')
                cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(check_interval)))
            elif check_interval == interval_list.get('one_month'):
                check_interval = interval_list.get('three_months')
                cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(check_interval)))
            elif check_interval == interval_list.get('three_months'):
                check_interval = interval_list.get('six_months')
                cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(check_interval)))
            elif check_interval == interval_list.get('six_months'):
                check_interval = interval_list.get('one_year')
                cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(check_interval)))
            elif check_interval == interval_list.get('one_year'):
                check_interval = interval_list.get('half_month') # Restart
                cmds.optionVar( iv=('gt_check_for_updates_interval_days', int(check_interval)))
                
        new_interval = ''
        if check_interval == interval_list.get('half_month') or check_interval == interval_list.get('one_month'):
            new_interval = str(check_interval) + ' days'
        elif check_interval == interval_list.get('three_months'):
            new_interval = '3 months'
        elif check_interval == interval_list.get('six_months'):
            new_interval = '6 months'
        elif check_interval == interval_list.get('one_year'):
            new_interval = '1 year'

        cmds.button(auto_updater_interval_btn, e=True, label='Interval: ' + new_interval)

    
    def reroute_errors(operation):
        ''' Wrap functions around a try and catch to avoid big crashes during runtime '''
        try:
            if operation == 'open_releases_page':
                open_releases_page()
            else:
                check_for_updates()
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    
    
    def open_releases_page():
        ''' Opens a web browser with the latest release '''
        cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/releases/latest', absolute=True) 
      
        
    def check_for_updates():
        ''' 
        Compare versions and update text accordingly 
        It uses "get_github_release" to check for updates
        '''
        
        def execute_operation():
            # Define Current Version
            stored_gt_tools_version_exists = cmds.optionVar(exists=("gt_tools_version"))

            if stored_gt_tools_version_exists:
                gt_check_for_updates['current_version'] = "v" + str(cmds.optionVar(q=("gt_tools_version")))
            else:
                gt_check_for_updates['current_version'] = 'v0.0.0'
            
            # Retrive Latest Version
            response_list = get_github_release(gt_tools_latest_release_api)

            gt_check_for_updates['latest_version'] = response_list[0].get('tag_name') or "v0.0.0"
            
            success_codes = [200, 201, 202, 203, 204, 205, 206]
            web_response_color = (0, 1, 0)
            if response_list[1] not in success_codes:
                web_response_color = (1, .5, .5)
                
            cmds.text(web_response_text, e=True, l=response_list[2], bgc=web_response_color)
            cmds.text(installed_version_text, e=True, l=gt_check_for_updates.get('current_version'))
            cmds.text(latest_version_text, e=True, l=gt_check_for_updates.get('latest_version'))
            
            current_version_int = int(re.sub("[^0-9]", "", str(gt_check_for_updates.get('current_version'))))
            latest_version_int = int(re.sub("[^0-9]", "", str(gt_check_for_updates.get('latest_version'))))
            
            if current_version_int < latest_version_int:
                cmds.button(update_btn, e=True, en=True, bgc=(.6, .6, .6))
                cmds.text(update_status, e=True, l="New Update Available!", fn="tinyBoldLabelFont", bgc=(1, .5, .5))
            elif current_version_int > latest_version_int:
                cmds.text(update_status, e=True, l="Unreleased update!", fn="tinyBoldLabelFont", bgc=(.7, 0 , 1))
                cmds.button(update_btn, e=True, en=False)
            else:
                cmds.text(update_status, e=True, l="You're up to date!", fn="tinyBoldLabelFont", bgc=(0, 1, 0))
                cmds.button(update_btn, e=True, en=False)
            
            published_at = ''
            try:
                published_at = response_list[0].get('published_at').split('T')[0]
            except:
                pass
            
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=(response_list[0].get('tag_name') + (' ' * 80) + '(' + published_at + ')\n'))
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=response_list[0].get('body'))
            
            if latest_version_int != 0:
                try:
                    previous_version = str(latest_version_int - 1)
                    previous_version_tag = 'v'
                    for c in previous_version:
                        previous_version_tag += c + '.'
                    previous_version_tag = previous_version_tag[:-1]
                    
                    before_previous_version = str(latest_version_int - 2)
                    before_previous_version_tag = 'v'
                    for c in before_previous_version:
                        before_previous_version_tag += c + '.'
                    before_previous_version_tag = before_previous_version_tag[:-1]
                    

                    previous_version_response = get_github_release(gt_tools_tag_release_api + previous_version_tag)
                    before_previous_version_response = get_github_release(gt_tools_tag_release_api + before_previous_version_tag)
                    
                    if previous_version_response[1] in success_codes:
                        published_at = ''
                        try:
                            published_at = previous_version_response[0].get('published_at').split('T')[0]
                        except:
                            pass
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n\n' + (previous_version_response[0].get('tag_name') + (' ' * 80) + '(' + published_at + ')\n'))
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it=previous_version_response[0].get('body'))
                    

                    
                    if before_previous_version_response[1] in success_codes:
                        published_at = ''
                        try:
                            published_at = before_previous_version_response[0].get('published_at').split('T')[0]
                        except:
                            pass
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n\n' + (before_previous_version_response[0].get('tag_name') + (' ' * 80) + '(' + published_at + ')\n'))
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it=before_previous_version_response[0].get('body'))

                except:
                    pass
                
            if response_list[1] not in success_codes:
                cmds.text(update_status, e=True, l="Unknown", fn="tinyBoldLabelFont", bgc=(1, .5, .5))
                
            cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
        
        # Threaded Operation
        def threaded_operation():
            try:
                utils.executeDeferred(execute_operation)
            except Exception as e:
                print(e)
                
        thread = threading.Thread(None, target = threaded_operation)
        thread.start()
        
    # Refresh When Opening
    reroute_errors('')
    
    # Refresh Buttons
    toggle_auto_updater(refresh_only=True)
    change_auto_update_interval(refresh_only=True)


def get_github_release(github_api):
    '''
    Requests the name of the webhook and returns a string representing it

            Parameters:
                github_api (str): Github Rest API for latest releases. e.g. "https://api.github.com/repos/**USER**/**REPO**/releases/latest"
                
            Returns:
                response_list (list): A list containing a dictionary (response) the response status and the response reason (e.g. [response, 200, "OK"])
    '''
    try:
        http_obj = Http()
        response, content = http_obj.request(github_api)
        response_content_dict = loads(content) 
        return [response_content_dict, response.status, response.reason]
    except:
        error_content_dict = {'body' : 'Error requesting latest release.',
                              'tag_name' : 'v0.0.0'}
        return [error_content_dict, 0, 'Error']
        

def silent_update_check():
    '''
    Checks if there is a new released version. In case there is one, the "Check for Updates" window will open.
    This function is threaded, so the user won't notice the check happening. 
    It also doesn't request a response unless it's time to check for new updates. (So it doesn't affect performance)
    '''
    # Check if auto updater is active
    is_active = False
    persistent_auto_updater_exists = cmds.optionVar(exists=('gt_check_for_updates_auto_active'))
    if persistent_auto_updater_exists:
        is_active = bool(cmds.optionVar(q=("gt_check_for_updates_auto_active")))
    
    if is_active:
        def compare_current_latest():
            # Get Interval
            check_interval = gt_check_for_updates.get('def_auto_updater_interval')
            persistent_check_interval_exists = cmds.optionVar(exists=('gt_check_for_updates_interval_days'))
            if persistent_check_interval_exists:
                check_interval = int(cmds.optionVar(q=("gt_check_for_updates_interval_days")))
                
            # Get Dates
            today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) 
            persistent_last_date_exists = cmds.optionVar(exists=('gt_check_for_updates_last_date'))
            if persistent_last_date_exists:
                try:
                    date_time_str = str(cmds.optionVar(q=("gt_check_for_updates_last_date")))
                    last_check_date = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S') 
                except:
                    last_check_date = today_date # Failed to extract date
            else: 
                last_check_date = today_date # Failed to extract date

            # Calculate Delta
            delta = today_date - last_check_date
            days_since_last_check = delta.days

            if days_since_last_check > check_interval:
                # Define Current Version
                stored_gt_tools_version_exists = cmds.optionVar(exists=("gt_tools_version"))

                if stored_gt_tools_version_exists:
                    gt_check_for_updates['current_version'] = "v" + str(cmds.optionVar(q=("gt_tools_version")))
                else:
                    gt_check_for_updates['current_version'] = 'v0.0.0'
                    
                # Retrive Latest Version
                response_list = get_github_release(gt_tools_latest_release_api)
                gt_check_for_updates['latest_version'] = response_list[0].get('tag_name') or "v0.0.0"
                
                current_version_int = int(re.sub("[^0-9]", "", str(gt_check_for_updates.get('current_version'))))
                latest_version_int = int(re.sub("[^0-9]", "", str(gt_check_for_updates.get('latest_version'))))
                
                if current_version_int == 0 or latest_version_int == 0:
                    pass
                else:
                    cmds.optionVar( sv=('gt_check_for_updates_last_date', str(today_date))) # Store check date
                    if current_version_int < latest_version_int:
                        #print("New Update Available!")
                        build_gui_gt_check_for_updates()
                
                # Print Output - Debugging
                # print('Check Interval: ' + str(check_interval))
                # print('Check Delta: ' + str(days_since_last_check))
                # print('Current Version: ' + str(current_version_int))
                # print('Latest Version: ' + str(latest_version_int))

        # Threaded Check
        def threaded_version_check():
            try:
                utils.executeDeferred(compare_current_latest)
            except Exception as e:
                print(e)
                
        thread = threading.Thread(None, target = threaded_version_check)
        thread.start()


#Build GUI
if __name__ == '__main__':
    build_gui_gt_check_for_updates()
    #silent_update_check()