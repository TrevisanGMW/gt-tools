"""
 GT Maya to Discord - Send images and videos (playblasts) from Maya to Discord using a Discord Webhook to bridge the two programs.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-28 - github.com/TrevisanGMW
 Tested on Maya 2018, 2019, 2020 - Windows 10
 

 1.1 - 2020-07-04
 Added playblast and desktop options
 It now uses http to handle responses
 Fixed error when capturing viewport on Maya 2019
 Added settings and persistent settings
 
 1.2 - 2020-10-24
 Fixed a few typos in the documentation
 Changed the feedback given by the playblast to use an inViewMessage
 Added a new method of showing the size of the file (it changes the suffix according to the size)
 Updated "capture_desktop_screenshot" to find what monitor is using Maya
 
 1.3 - 2020-11-01
 Updated "discord_post_message" to accept usernames
 Added option to send a messages
 Updated the name of the settings dictionary to avoid conflicts
 Added inview feedback to all buttons
 Made main functions temporarily disable buttons to avoid multiple requests
 Added option to control the visibility of inView messages
 Added option to up timestamp or not
 
 1.4 - 2020-11-03
 Added send OBJ and send FBX functions
 Changed UI
 Buttons were replaced with iconTextButton
 Button icons (base64) are quickly generated before building window
 Removed header image
 
 1.5 - 2020-11-15
 Changed the color of a few UI elements
 Removed a few unnecessary lines
 
 1.6 - 2021-05-16
 Made script compatible with Python 3 (Maya 2022+)
 Removed a few old unecessary lines
 
 Todo:
    Improve embeds for discord image uploader - Add colors, emojis and more
    Add option to deactive threading. (This should affect all send functions)
    Add option to keep screenshots and playblasts in a selected folder
    Add checks to overwrite existing images (UI) when there is a new version
  
""" 

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2 import QtWidgets, QtGui, QtCore
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide import QtWidgets, QtGui, QtCore
    from PySide.QtGui import QIcon, QWidget

try:
    from httplib2 import Http
except ImportError:
    import http.client

import maya.OpenMayaUI as omui
import maya.utils as utils
import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import threading
import urllib
import base64
import socket
import datetime 
import mimetypes 
import random 
import string 
import copy
import time
import sys
import os
from json import dumps
from json import loads


# Script Name
script_name = "GT Maya to Discord"

# Versions:
script_version = "1.6"
maya_version = cmds.about(version=True)

# Python Version
python_version = sys.version_info.major

# Used to define multipart/form-data boundary
_BOUNDARY_CHARS = string.digits + string.ascii_letters

# Settings
gt_mtod_settings = { 'discord_webhook':'',
                     'discord_webhook_name'  : '',
                     'is_first_time_running' : False,
                     'custom_username' : '',
                     'image_format' : 'jpg',
                     'video_format' : 'mov', 
                     'video_scale_pct' : 40, 
                     'video_compression' : 'Animation', 
                     'video_output_type' : 'qt',
                     'is_new_instance' : True,
                     'is_webhook_valid' : False,
                     'feedback_visibility' : True,
                     'timestamp_visibility' : True }

# Default Settings (Deep Copy)
gt_mtod_settings_default = copy.deepcopy(gt_mtod_settings)   

def get_persistent_settings_maya_to_discord():
    ''' 
    Checks if persistant settings for GT Maya to Discord exists and transfer them to the settings dictionary.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    
    # Check if there is anything stored
    stored_webhook_exists = cmds.optionVar(exists=("gt_maya_to_discord_webhook"))
    stored_webhook_name_exists = cmds.optionVar(exists=("gt_maya_to_discord_webhook_name"))
    stored_custom_username_exists = cmds.optionVar(exists=("gt_maya_to_discord_custom_username"))
    
    stored_image_format_exists = cmds.optionVar(exists=("gt_maya_to_discord_image_format"))
    stored_video_format_exists = cmds.optionVar(exists=("gt_maya_to_discord_video_format"))
    
    stored_video_scale_exists = cmds.optionVar(exists=("gt_maya_to_discord_video_scale"))
    stored_video_compression_exists = cmds.optionVar(exists=("gt_maya_to_discord_video_compression"))
    stored_video_output_type_exists = cmds.optionVar(exists=("gt_maya_to_discord_video_output_type"))
    
    stored_feedback_visibility_exists = cmds.optionVar(exists=("gt_maya_to_discord_feedback_visibility"))
    stored_timestamp_visibility_exists = cmds.optionVar(exists=("gt_maya_to_discord_timestamp_visibility"))
    
    # Discord Settings
    if stored_webhook_exists:  
        gt_mtod_settings['discord_webhook'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook")))
        
        if stored_webhook_name_exists and str(cmds.optionVar(q=("gt_maya_to_discord_webhook_name"))) != '':
            gt_mtod_settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook_name")))
    else:
        gt_mtod_settings['is_first_time_running'] = True
   
    if stored_custom_username_exists:  
        gt_mtod_settings['custom_username'] = str(cmds.optionVar(q=("gt_maya_to_discord_custom_username")))
    else:
        gt_mtod_settings['custom_username'] = ''
        
    # Image Settings
    if stored_image_format_exists:
        gt_mtod_settings['image_format'] = str(cmds.optionVar(q=("gt_maya_to_discord_image_format")))
    

    # Playblast Settings
    if stored_image_format_exists:
        gt_mtod_settings['video_format'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_format")))

    if stored_video_scale_exists:
        gt_mtod_settings['video_scale_pct'] = int(cmds.optionVar(q=("gt_maya_to_discord_video_scale")))

    if stored_video_compression_exists:
        gt_mtod_settings['video_compression'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_compression")))
        
    if stored_video_output_type_exists:
        gt_mtod_settings['video_output_type'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_output_type")))
    
    # Checkboxes
    if stored_feedback_visibility_exists:
        gt_mtod_settings['feedback_visibility'] = bool(cmds.optionVar(q=("gt_maya_to_discord_feedback_visibility")))
  
    if stored_timestamp_visibility_exists:
        gt_mtod_settings['timestamp_visibility'] = bool(cmds.optionVar(q=("gt_maya_to_discord_timestamp_visibility")))



def set_persistent_settings_maya_to_discord(custom_username, webhook, image_format, video_format, video_scale, video_compression, video_output_type):
    ''' 
    Stores persistant settings for GT Maya to Discord.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    
            Parameters:
                    custom_username (str): A string used as custom username
                    webhook (str): A string containing the Discord Webhook URL
                    image_format (str): Extension used for image files
                    video_format (str): Extension used for video files
                    video_scale (int): Scale (percentage) of the playblast
                    video_compression (str): A string used as the compression of the video (e.g. "Animation")
                    video_output_type (str): One of these three strings 'qt', 'avi', or 'movie' as determined by the cmds.playblast function

    '''

    cmds.optionVar( sv=('gt_maya_to_discord_custom_username', custom_username) )
    gt_mtod_settings['custom_username'] = str(cmds.optionVar(q=("gt_maya_to_discord_custom_username")))

    if webhook != '':  
        cmds.optionVar( sv=('gt_maya_to_discord_webhook', webhook) )
        gt_mtod_settings['discord_webhook'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook")))
        
        response = discord_get_webhook_name(webhook)
        cmds.optionVar( sv=('gt_maya_to_discord_webhook_name', response) )
        gt_mtod_settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook_name")))
          
    else:
        cmds.optionVar( sv=('gt_maya_to_discord_webhook', webhook) )
        gt_mtod_settings['discord_webhook'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook")))
        
        cmds.optionVar( sv=('gt_maya_to_discord_webhook_name', 'Missing Webhook') )
        gt_mtod_settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_maya_to_discord_webhook_name")))
        
        cmds.warning('Webhook not provided. Please update your settings if you want your script to work properly.')
        
    if image_format != '':
        cmds.optionVar( sv=('gt_maya_to_discord_image_format', image_format) )
        gt_mtod_settings['image_format'] = str(cmds.optionVar(q=("gt_maya_to_discord_image_format")))
    
    if image_format != '':
        cmds.optionVar( sv=('gt_maya_to_discord_video_format', video_format) )
        gt_mtod_settings['video_format'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_format")))
        
    if video_scale >= 1 and video_scale <= 100:
        cmds.optionVar( sv=('gt_maya_to_discord_video_scale', video_scale) )
        gt_mtod_settings['video_scale_pct'] = int(cmds.optionVar(q=("gt_maya_to_discord_video_scale")))
    else:
        cmds.warning('Video scale needs to be a percentage between 1 and 100.  Provided value was ignored')
        
    if video_compression != '':
        cmds.optionVar( sv=('gt_maya_to_discord_video_compression', video_compression) )
        gt_mtod_settings['video_compression'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_compression")))
        
    if video_output_type != '':
        cmds.optionVar( sv=('gt_maya_to_discord_video_output_type', video_output_type) )
        gt_mtod_settings['video_output_type'] = str(cmds.optionVar(q=("gt_maya_to_discord_video_output_type")))
        
        
def reset_persistent_settings_maya_to_discord():
    ''' Resets persistant settings for GT Maya to Discord '''
    cmds.optionVar( remove='gt_maya_to_discord_webhook' )
    cmds.optionVar( remove='gt_maya_to_discord_webhook_name' )
    cmds.optionVar( remove='gt_maya_to_discord_custom_username' )
    cmds.optionVar( remove='is_first_time_running' )
    cmds.optionVar( remove='gt_maya_to_discord_video_format' )
    cmds.optionVar( remove='gt_maya_to_discord_image_format' )
    cmds.optionVar( remove='gt_maya_to_discord_feedback_visibility' )
    cmds.optionVar( remove='gt_maya_to_discord_timestamp_visibility' )   
    gt_mtod_settings['feedback_visibility'] = gt_mtod_settings_default.get('feedback_visibility')
    gt_mtod_settings['timestamp_visibility'] = gt_mtod_settings_default.get('timestamp_visibility')
    get_persistent_settings_maya_to_discord()
    build_gui_maya_to_discord()
    cmds.warning('Persistent settings for ' + script_name + ' are now removed.')


def build_gui_maya_to_discord():
    ''' Builds the Main GUI for the script '''
    window_name = "build_gui_maya_to_discord"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_maya_to_discord = cmds.window(window_name, title=' ' + script_name + ' - (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=4, cw=[(1, 10), (2, 150), (3, 60),(4, 40)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Settings", bgc=title_bgc_color, c=lambda x:build_gui_settings_maya_to_discord())
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_maya_to_discord())
    cmds.separator(h=5, style='none') # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    # Generate Images
    # Icon
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True) 
    icon_image = icons_folder_dir + 'gt_maya_to_discord_icon.png'
    
    if os.path.isdir(icons_folder_dir) == False:
        icon_image = ':/camera.open.svg'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(icon_image) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTA3LTA1VDE5OjU2OjQwLTA3OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDpkNjdiM2JkNy1iMjk3LWI3NDItOTNkOC0wYTYyZjZhYzUzMmYiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplOTM5YzQ0Yi1lNjdkLWJjNGMtYWMyZS00YmY3ZjcwYzgzODAiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5MzljNDRiLWU2N2QtYmM0Yy1hYzJlLTRiZjdmNzBjODM4MCIgc3RFdnQ6d2hlbj0iMjAyMC0wNy0wNVQxOTo1Njo0MC0wNzowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHN0RXZ0OndoZW49IjIwMjAtMDctMDdUMTU6MjU6MjktMDc6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7Q7fCFAAAIwklEQVR4nO3bf6xlVXUH8M/a5755w/BDfmaYCunAkyq22hFQbClia1sZMBicaIc2bWJqajQpwR9pY6TYKkk1jiBNbZpQq40mVCI60USjERqIP+LQoQRSx6hjfxEjTQpl+DXMu3cv/zjn3nnvdWbefe/O64Uw32TlnZx7ztrfvc7aa+299n6RmZ7PKNMmMG0cM8C0CUwbxwwwbQLTxjEDTJvAtPG8N0Dvpk8v/1AmOUBQGhI5TwZlFgOikuEkXCRskd6LH0f6taGe2iCJbHXp5mARXRvRSlOHDZPhdmzDjRHuq3331r6fzKxvOdXSvh+oWt0l22sxhgHGsdJSjLgn0gul7RmuxiUj4mjCo8LMIM2X4fNj6O46Tmuw06SCGzKJQlnne5m+KHwW3x/aczVY1RDI9s3NUdyhegg7RNv5YBeujvbD/KJiftTKSlkGwuukyHQl7haU4qXJ+zPsCe6JtCVXox/xsU8t/1kWDYGe87P6uPDboy+a9mX1IT23YL7UtveV85JXRniR9PPYhFNwItZrPTDQx348Lvyv9DD+E3uD3ZUHZde/dri8NcIHcdYCY+3CtdJ3VzIExjZAO8B8WPGnS1z5ffiwJIumpqt6XJ68AT+3PIWx8Ai+knxNuCMGng5kY7t02+Ie+ftSvSM5kOMYYMcYBpB+BV/C6Qvu3hb8bud6WyO8P2sXA9Ye9zfhpspnsvWMP8/wgY4rrTddg52xTPfio5888hMRzsS/aV1WUnvFNYXbDwxsi/AprUtPAzV4j/Dxmi6M9DXhtAW/XyjcdyQFRwyCbQxyg67z+FHwlmRTPz0mfN70Ok+b8W7OlHij9qvvwjCTfGTQcCSJz9x2aA/oBU/0XfjIM/65OTiWvqINZK+YJPWsBaIlszfTA7gKjcAzri7zdh7uU/f2HTj0DyU4UL17QScHeL02Oz+rOk8XqJnDuRZMU0rPu5rGzsMFxN6Tg8Mo5OxI25sYzV+ao0t5zdCN3HZWmI3XPMNrpHsO9XDpJYcU3ldCec5XDJNS/Ul0U/ClUobz7yWyIXnLtLkfNYQrozhXYamUob8sFG1EPe2Qyp6jiOrNZcD/kb52HrpQkt+bKtu1QHhrLQyWSGm00W0ohRfjyqmSXQMkLxZ+o0Tr9iNZOv6xdcpc1wyFNywd7r2lUT7C68dZtz8Xkek3l05gyuKU4GTp0unQ+3/By0raUiojWZgVcAWOP6pNTjBlXAtHrFy9KAjO9pjtsX6GErbWCVsN9kT6A1wgXaK6MXlqJXuwbaVNNuETwWuxJdgWfHsyduCyZsBQ4qML6gGR9uAlq9Uc4Qu9tG1Q22JlVmpl5jjnR/Xt+b6TyzIekUnTa8drSXfSpuZSdVZxs3TdajnisWgrSU9AUelkzgSdx33YtvBDZ7Sx5fhqz4bqinGUJDakN59Q3Tksri75/V34wgQ8X1DDBYNgEJQZrEOPl0/i/ZE+oDKoB8vUidl17UUN35kpvnSkNhJN8WBNn89gXXOw1D1qZ4DqQ6vlmSjVlnUDZgaUQaFfqGHLBPHqsX74p360ug5o185Nad13X/JEMuAfjtRGZ7TbngweD57q3D6K9iutI1q5X/j+qqNkePVoLZB9sk+mX12lOnhIeHI4u8jhZsWgrSZHJwb2LqcoqwdHnAbUQVeVXiL4j1WVwZFcOqwC9Oo8wvFl1kUrVzdC06uLb2Tr9ks5jrMR01v4TkZrjNKV5Rfcn6Q+cVavMVfC3hLrKbPOwckTKNyc4dTsvr5gmE5j8fLzl5ZTVMLFpbQTlKb7m52eLj0OPf9FqyUb2D9w3hN9ynEzzDTOnfCs1PooLh+upoazqhgm9NqK9LblFCXbh4kph73t1ilVG1tquBSbV0u2YjbMnTiKAdXmSYt8tdoR805qDhwkzaIaw5s4uFF6BGyOcO3CIubw28wETVDYMRlbknMSZf+A+eqcSYucwSbhLmE2YxSohj9eEeGOFbC7RXr7kOnodnv9ZbxqQq76afPT1fpezpqNvrO6ra+JkOHCQXg40q2l2I0N2VaXrloxyfS3wjXCP5b0iHR+DW/XluUnRnBWSRt7ud8Z0dh0FOvcL8j03himxAliS3IZLith1Sn/MHoVNvaKM0tUZ0TauCaF/qPE+mivCru5wOkZNpay3umKU5Zp5WHtDu1zBfvwk2WeOWG+Or1E3xnSKcs8fDI+jW8cBXJrjd34Gwf3Mw+LwhlFu4e/3EmRWbwx+GCE6591+2K6zBs+EeGPtDWEU8d47dSS/Mh47j2n3Rz9elQR3P6sKB22AfKewkkl/KW0E68e483M8MOCncZMU8kJNe0S3qb6nUhzwl2rZz8Zgn9pwsWlcZl0yaB6qHL2mK9fI/3d0PW/hV8IHh+jURluFR4I/qem11VOjPDHER5YbWdWgL3B9dgYxQVZ7VJ9PcNXh/zGwK/jcxA7PtmeMele3FjDV0u2+/9j4s+CG1M7Tc3iJbX6raheleGXcZ4xAtJhMNAO0Qci3JvcWbmv6abaNf1hcKsx+p0o4b/qwNbkX5umnaOMDFB0lbH2+t3Sx1ZAdL90c+HGLJ4aLoIqIpyQYU46G2dq9xxPwgbMdO/38TT2CY9E+mnyUPJj6dEo3Vb3wfau055cWS57jTrfcFOE9/Rr2/EyPLS50AOyM4AgqrkIfy1dvgJDPIq7It2QfG90grOrDY4z244hEd1Rt4O9fmEJf5HtztX4p8/CruSdM9VuwXwuNsAh019Xg9tbw1btQumLYzZ3CrbVsK4umb6uNGMMnw/dCjvMZ9hu/M7fnbwCFwe702jrbxEOnf8XP/jvTfGmJmySrhO+oXXXQz0r+X3cH0tuToz03+oSb1zcdl+7b3B9MFfSa5P7l1O7krPCP8UtGW5Zx3G1umhQvEx1qfByvBQfkT67iPewILBKIyyoAAm+iWvxV/iBak8Ud9fqwVLdm43HrLC5OPZvc89zHDPAtAlMG8cMMG0C08YxA0ybwLTxvDfAzwB7KURH1CLqQgAAAABJRU5ErkJggg=='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(icon_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
        
    # Send Desktop Icon
    send_desktop_btn_ico = icons_folder_dir + 'gt_mtod_send_desktop.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_desktop_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTAzVDExOjU1OjM4LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wM1QxMjoyNzoxMi0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0xMS0wM1QxMjoyNzoxMi0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpiZTc1ODU2NC04YThkLTQ2NDUtYmU2Yy1lMmY5ZmQwMWU0YjgiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDozYjViOWNhMy1lODgwLTgxNGQtYmFjOS1mNTNmNDExMWQ0MDciIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo5MGM2ZTQ5My0xZDNkLTNiNGQtODI0ZS1kN2JhZDRlNzQ1MzQiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjkwYzZlNDkzLTFkM2QtM2I0ZC04MjRlLWQ3YmFkNGU3NDUzNCIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpiZTc1ODU2NC04YThkLTQ2NDUtYmU2Yy1lMmY5ZmQwMWU0YjgiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6Mjc6MTItMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PHrkDAAAFDklEQVRYhe2XT2gUVxzHP+/N7M5kdetG6+ISY1sRak38Q7L9RwyUhlioh4aI1nry3EKgiKcWUS8tVQjkkAZbpLSRVg/anEzFYGJzsU5AAqUhpUuyQdckWje7+bPZnZnXQ3bDanbWikUv/Z5m5v3e+33e7733e78RSimep/ShoaH9QBOQAZ4FjQ5kgV/r6+t/1oEjruvWAdozcA6A4zhOIpE4EI1G0YG6qakpZ3BwUOq6LmzbRgjh2VkIUbJdKcXjllNKiWEYNDc3+zZs2LAR+FQH1JUrV/xdXV0xKeVV13V9QA7wplhqkyW+u5RZRiklVVVVq2tqat6LRCIvAm/oAJqmKV3Xe/r7+6uEEE1CCD/gPMa5KnqnjD2AVErds237m4GBgW8jkcg1YC0sbQiy2SyVlZWmlPJgJpPJ3rx5UxmGoQkhSs4mH+oVESplr5RCCEF9fX1ofHz85IkTJ+jv7884jgOg9EJoNE3LAvT09PhPnTqVBK4Bq8rMqhRcyWULBALi3Llzb7muG3Qc50MppZ0HWIpAXhLAMAyAHyzLaivjfFnRaPSxNtevXw8qpX6LxWKbWDpt9kNOAdRSXFV+h1f8G+dPIqWUVErJYucPATyicifgP5UXwDPT/wArAMql4adUyYFXACwsLHgaP4XmgYyUKwOuw3K2EoCorKxk27ZtGvBqmQGXR7Isq/DolrEPSCkDuq4X+i4fxeVMaNu2C7Bnzx62b9/eksvl3lFKlYyEEIISbV6XkBJCSJ/PVz07O5sB/CsAbNvmzp07i1NTUx/39vZ2GoaxxjRN23XdkjWCKLFRXNcteRcUNDs7+2BwcLBS1/VU8bWtAyIUColIJKKFw+GvOzo65oBawKR8WL2uY09pmpY+dOhQDDhSmIOwLEtls1nu379/LxwOT2iatoD3JtTyTh7k3yuANBAAVrO0DOWqEiNvuxUgGo1mdOBYX1/fSb/fvzYWi2n5imfFTKSUpNNpx3EcGhsb1/n9fjE5OTlXVVUVjMfjMyMjI2nTNCt8Pp/wgsiHXqbT6eTo6GgIMHXgi66uropMJrNFKeXLd14RgVwup9LptLtv377Vzc3NzRcuXMidP3/e6OjoWDRNc017e/v49PT0YCgUWi+l9HtBSClxXZdUKvU3MKoD9u3bt48BL1BmDY8ePbqupaWlzTCMg8lkcrS7u3vL3bt3OxKJxPDOnTvPdnZ2vhYIBL7fu3fvJ0CQ8kWuyPuaFUXnuFgm0AC8DmwCaoBXgOrh4eGR48ePr4/H46PAQSDe1tZ2ZPfu3V9t3rxZptPpqWAwaAG/AxPAQDQaHfYk8QDYqpT6BdgohJDz8/OZoaGh1KVLl8StW7fWp1Kpn4DPLcv6q1CQNDU1tYbD4Y6Ghoaquro65ff7RS6XyyUSiT9bW1s/AkpC6KU+AqYQYtPAwMD86dOnjUwmY87Nzc1ls9leoBu4YVnWg+IOfX19F4EbV69e/cDn8x0A3jxz5oxp2/ZW4Evg/ScBACAYDAZ27NgxcPjw4YvBYFCEQqFF0zSrgZdYWkdlWVZxVayA+ZmZmbPT09PfhcPh9rGxsVVAtZcPL4DU4uLi2K5du16ura1t1HX97bxD4bplc00BXAWDQaSUvrGxsSxlNrcXwGQ8Hu+cmJj4LJlMviCEkHkAz7+fR7KzkFKilHIuX77sB/7wAhCFur2EVgH7gXdZuk6L5ZXtHh2o8APzI9DvCfA89Q9+dgWL9W/IeAAAAABJRU5ErkJggg=='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_desktop_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_desktop_btn_ico) == False:
        send_desktop_btn_ico = 'fluidGetExamples.png'

    # Send Maya Window Icon
    send_maya_window_btn_ico = icons_folder_dir + 'gt_mtod_send_maya_window.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_maya_window_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTAzVDExOjU1OjM4LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wM1QxMjoyNTozNS0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0xMS0wM1QxMjoyNTozNS0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphMmEzYWE2ZC00ZmE2LTViNDktYjJmYi04Y2VhOWEwMGE0OTQiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDozZjI0OTk0ZS0zM2Y2LWZhNDctODE1OC1lNjhiNzFiM2EyYTEiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo0ZTFhNDdlNi0wNTgyLWMwNDQtOWRhNy0yZDZkMWU5ODJiNWYiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjRlMWE0N2U2LTA1ODItYzA0NC05ZGE3LTJkNmQxZTk4MmI1ZiIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphMmEzYWE2ZC00ZmE2LTViNDktYjJmYi04Y2VhOWEwMGE0OTQiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6MjU6MzUtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7TOzviAAADuUlEQVRYheWXX0ybVRiHn+9ryzA0ICYOOivD6AWRQbr00wsB2xs3qSEgeAGR1OgFmOyCGAw0ImZxlTDvJKYJFxqhmvSKxN1IMGnsBLPU05o4scjMYDSMhUQ7/hRXSnu8KGDchbSugIm/y/Oe8/6enPfkzXsUKSXHKfVY3f8LAPpQKHQFqANKjshTAj9ZrdazAHqgaWFh4e709PR2LBY7UV5erqysrMjS0lIFIBaLSZPJpOTLXVVVHA6HRVGUH6SUZ/UAAwMDD8/Pzwerqqq+n5ubu1VdXX1mdnb2R+BkbW1tidfrvQGczhdETU1NM/AkZG6AVCrF6OjoFavV2qFpWuPY2Nh3MzMzk3V1ddeBTzVNe14IcTNP/gpwBri3D1BWVkZ3d/eXwC3gK+Dxnp6eKNAJvAFcBcx5ApBAEigEUIQQG4lEwqiq6prBYNgAioD43oZd0qI8me9J0TQtKKU8rwf0kUgkFY1GjTqd7oSqqql0Ol2kqmoynU7rAOPumiEfzqqqYrFY9MCzkClBocfj2Q6Hw9eAX8nU6FDl9XrPkSnD/hsoAN4VQnx72OaAAZgC/oC/d8KKIzAHQEqpAA/dD5CrBoGFB4V5EIB2oNLpdC4fB0Ax8DSA3W4/pWma5agBBqWUMb/fT2dnJ8ArhwlgJtOYloEbZBrT25OTkxGXy/V7QUEBQogBIArc3I0P5hNgbXNzcwo4BTw1MjKy3tfXl3S73c+l0+mRVCp1vr+/n1AoZAaeiMfjhq6urkFN07KCyAZgw263Oy9fvnw1Ho9TWVn5qN/vfyuRSLwMfKjT6abq6+svWiyWe4FA4I7NZlPD4XAc+CYbAH02m4QQG4Ctvb39VZ/P97nFYnmvoqKibDdc09TUdDEYDI719va2AZ8JIV7PJi/k+Ah9Pt8XwI7b7T7pcrkiwMfA9WQyeScYDL4GXMrFPGcAoAvYcTgc6eHh4Srgwurq6m8GgyHa1ta28y/y5XzAARS2tLSoQ0NDkzabjbW1tUeAZ0wmk95sNr95mAA6oHlpaeluY2MjExMTL8bj8Zc6OjpKPB7PbYCGhobTmqblNLrtj2RZKLW+vl7d2to6CwigWQhxezf2mNPpHFxeXn4faAE++oc8STJT0V8AW1tbAAdSFBcX/wxUCSF+uT82Pj5+SdO0T4DEQXkURUnueStCCAmQSqXiOp1u56DDeZACFGua9rWU8pweGAgEAh8YjcYiVVUPHUBKyeLi4jbwAoAipURRlHfIzGhH+TuKSCkvKP/73/GfvZZpfU8vP8IAAAAASUVORK5CYII='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_maya_window_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_maya_window_btn_ico) == False:
        send_maya_window_btn_ico = 'hypergraph.png'
        
    # Send Playblast Icon
    send_playblast_btn_ico = icons_folder_dir + 'gt_mtod_send_playblast.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_playblast_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAJ5WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgeG1wOk1vZGlmeURhdGU9IjIwMjAtMTEtMDNUMTY6MTQ6MDUtMDg6MDAiIHhtcDpNZXRhZGF0YURhdGU9IjIwMjAtMTEtMDNUMTY6MTQ6MDUtMDg6MDAiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiBwaG90b3Nob3A6Q29sb3JNb2RlPSIzIiBwaG90b3Nob3A6SUNDUHJvZmlsZT0ic1JHQiBJRUM2MTk2Ni0yLjEiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6Zjk0YTBjMDUtZDZhMy0zOTQzLTgwNWQtOTkzMzZlNjg5OWEyIiB4bXBNTTpEb2N1bWVudElEPSJhZG9iZTpkb2NpZDpwaG90b3Nob3A6ODI3Nzc4MTctNjlhMC1mYzQ2LTgwYzAtMTkxMzJkNjlkZGQ0IiB4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6Nzk5NGJlMmQtMTY5My1jNjRkLWI5Y2ItZjkzYzBiMmE0OGYxIj4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3OTk0YmUyZC0xNjkzLWM2NGQtYjljYi1mOTNjMGIyYTQ4ZjEiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTE6NTU6MzgtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY29udmVydGVkIiBzdEV2dDpwYXJhbWV0ZXJzPSJmcm9tIGltYWdlL3BuZyB0byBhcHBsaWNhdGlvbi92bmQuYWRvYmUucGhvdG9zaG9wIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo1ZTI0ZjJlMC1iNDEwLTgwNGUtYTNhZi1kYWQ5MGVmZGEzMGIiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTM6NTc6MTYtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6YjY1ZWJjZmMtMGMxYS0wMDQ0LTk1NDItYzllNjkwOWRhM2QyIiBzdEV2dDp3aGVuPSIyMDIwLTExLTAzVDE2OjE0OjA1LTA4OjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNvbnZlcnRlZCIgc3RFdnQ6cGFyYW1ldGVycz0iZnJvbSBhcHBsaWNhdGlvbi92bmQuYWRvYmUucGhvdG9zaG9wIHRvIGltYWdlL3BuZyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iZGVyaXZlZCIgc3RFdnQ6cGFyYW1ldGVycz0iY29udmVydGVkIGZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmY5NGEwYzA1LWQ2YTMtMzk0My04MDVkLTk5MzM2ZTY4OTlhMiIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxNjoxNDowNS0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDwvcmRmOlNlcT4gPC94bXBNTTpIaXN0b3J5PiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDpiNjVlYmNmYy0wYzFhLTAwNDQtOTU0Mi1jOWU2OTA5ZGEzZDIiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6Nzk5NGJlMmQtMTY5My1jNjRkLWI5Y2ItZjkzYzBiMmE0OGYxIiBzdFJlZjpvcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6Nzk5NGJlMmQtMTY5My1jNjRkLWI5Y2ItZjkzYzBiMmE0OGYxIi8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQgZW5kPSJyIj8+sI+MuwAABUBJREFUWIXFl39I1Gccx1935+p0wmztxGYIGxEy3KB1U1sSLUrYgnKbGCS5CIz9QEMYWynsFzK2wrYkMrbGMoggWF32w8gDDwvd8n0zHK2MYebI2qyDmLb8dc/+8PsVtfuRbrA3HHf3fT6f5/16nu/3+zyfx2GM4f9UAkAwGHyU2LlAAfAm8Arw1LT2O0Az8APgA4bidbh06VIcxhiCwSBerzdikKQngI+BCvva3bt3B69cufLY7du35wB4PB4WLVpEenr6RN7o6GhtQkLCR16v914siJgAkt4CDgL09vberK2tTW9ra2NoaAigG/gF6LPCn3a73S/k5uY+U1xczJIlSwAIhULv5Ofn749KYIxBUiTzbyWZQCBwKysrywAGaGH8NiTGGFQiUJCdnd1x7NgxI8kcPnw4MCMASSckmZ07d/5iGXcBOTFMoymnsrIyJMnU19f3PBKApO8kmYqKisuW+VezMJ6iqqqq85LM7t27b8QEkLRRktm1a5dt/sG/NbdVV1d3QZLZvHlzICKApARJpqWl5U/LfE+kjiS9KiltNhB+v/+eJJOYmLjJvuac1P41QElJiQe4DmyLYF4NnAFuNTY2fjpTgJSUlByAsrKyQ1hrkA3gBN7r6+vr7+npAXgtSh+vj42NjXV1deHxeD7y+/1/SHrkh9Pr9V598ODBr0VFRTidzj2TAQoAqqurPcDPwNUofTx1586dseLi4qHS0tKucDicCvzY1NTUKmn6yhhRbrd7G8DKlSvfBZw2QAnAxYsXAT6MkT/idDoTgJsdHR2Z+fn5Lx08eHBw3rx5y4D+M2fOlMUD8Hq9foC1a9cCFNgAa0Kh0N/Wb3+MfONwOAwwx/qvvXv3JpeXl9d1d3eTmppae+rUqcuSUuNw9Obk5ACU2ABJly5dmgP0xhtBJLW2tr5bVFSUdeDAgT/S0tKeGxgY+H3r1q2ZMVJ+crvdAGsm3oL+/n4X8NNsACxd3r9/f9r69es/SU5OnrNw4cIOHt4xbd22vpMSojTMSpJcjG/bSHIDO4EtsXImZmD+/Pn/xhtJrwGDwI7m5ua2hoYGgPNRwicWMnsG7mdlZSVNbpiBcRLwDVA8Ojo6WFZW5mxvb18GfAF8HyUtZ3h4eAxw2TPQlJaWBvF3PNc08zcYH3Wx3++/mpub+3h7e/sgsArYEaOfDEnDwH0b4BBAdnZ2RhwAx8jICB6PxyXpFPDD0NBQaMuWLWzfvj2T8eV8HuOlWURJWg3g8/kSgSYbwAdQXl4OsDoGwI0FCxa4GhsbFwBrfT7fb8uXL3+ys7OzD3iZSWVbDH0JEAgEAA7ZAOFwOLwvMzOTxYsXR9wFLb1/7dq1v44fP86KFSuorq5eBHwOpANt8ZwlZQIvnj59uj8cDgP4HtqOGxoaDBBrEckDLjD+4CXHM50G0C3JuFwuA+wFphYkra2tmySZysrKmJXsbCRpjySzbt06u95IeAgA4MiRIwFJpqqq6sJ/aP6BJLNv3z670to40RipKK2vr79hJURbSGZi/pUkc/ToUdv8uykB0crympqaHknm3LlzoZkUHZOMcyR1WQOxq+sTDwVGAwAoLS0NSDKSTHNzc4ekAklRzwSSEq2YFjuvsLDwlmX+baScuEezjIyMtwsLC+s2bpxy2647HI5OJp2KgOeBZ+2YkydP3qypqUkfGBgA2AzUzwrA0hNJSUmf5eXlla9atQqv10tKSsqUgMHBweFgMDhy9uzZxwOBAMPDwzB+pvgUiP5WGWOYwRF9LrABOAr0Mz61kz/9VtsGKzau/gFGuKBUsRuTMAAAAABJRU5ErkJggg=='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_playblast_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_playblast_btn_ico) == False:
        send_playblast_btn_ico = 'createCache.png'
        
    
    # Send OBJ Icon
    send_obj_btn_ico = icons_folder_dir + 'gt_mtod_send_obj.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_obj_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTAzVDExOjU1OjM4LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wM1QxMjo0Njo1MC0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0xMS0wM1QxMjo0Njo1MC0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphODY0N2JkMS0zMjYzLTBjNGYtOGY4OS00NzNhYTc5NDY4MjQiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDo3MDMzNGVkMi02YWQwLWZmNDctYWNkNi0xNzI2YTY1NjYzMjciIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo3ZWJlMzQwNy03NWI4LWYwNGEtOGU3Ni0xMzIwMmM3MGI3NWYiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjdlYmUzNDA3LTc1YjgtZjA0YS04ZTc2LTEzMjAyYzcwYjc1ZiIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphODY0N2JkMS0zMjYzLTBjNGYtOGY4OS00NzNhYTc5NDY4MjQiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6NDY6NTAtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz6cG5g7AAAEzElEQVRYhcWWbWxTVRjHf7fcDjXYAhoN2T5AACMRqMplEj6MhZfFwQiIBKLWrsniJmEbiYnJqMlc7NAPpibEppka5wYZCQtZNqVIFvYCH7qlnAKR2SFLJL5tIYXOzXbMvdzjh93WuYyxFcz+yU37nPv0/n+3z3nOOYqUkvmUChAKhWbK8QDFQNoj8owBEvhlw4YN69QHJNcCjsHBwb+8Xq8JAzgV6bpOb28vRUVFi2w2G8BaRVGuz/TAasDR19fXH4lEljQ0NPwKVAJKqhAHDhxYsX79+ve7u7vj6enpFmDt/QBqAYfD4TizadOm/QUFBTrwuxDiq1TNgXeAss7OzmMej6esvr4eIGqaJvEE4HC73S3hcHi/3W4/qyjKCGB7SPMvOzo6/MXFxR/s2bPHpygKwJKpAN8Ab1dWVrY2NTVtA3ZaLJaYrusmYCxF8yLD/GxJSckuwG232y8b95TJAD7AuW/fvtONjY1bgV1CiO+Bfl3XJRMzNxXzqkAg4C8pKckDPhJClAPjiYTEHPgUOHTnzp0/s7OzDzqdzmqLxZIL7AS2LVy4UHW5XI8Bn8/BPAaUdXR0+EtLS3cZ5h9OTVKklIRCITkwMDAQiUSsGRkZuqqqY1JKRUopVVU1m0wmZWhoCLPZPDobZyklaWlp5q6urm6n07kGcBtvntCbQJ2maf/2tdvttra3t98yyFdgtFtVVdUCTdMWZGVlAfzNLNuwra1NvXnz5hrg9BTz/ygJoKoqwHtCiMYpObtramo8wGohxJOzMTd012q1LgIGZkpKApjNZgDzNDnfeb1egOfmYA5GeQHLrAAMTbfefyGE2AqsniNAQjN2z3QL0VTZgFWapvWkCDCjZgNwMD8//wdg1XwBRFeuXOkA1s0XQFN5efk1oHe+AHrj8fgocPf/AJjNAcO+ZcsWgFfnCyBLCOEH7HN9+AznzeRmNJsSlAGnNE17Y47+48PDw/fbRfvnApARjUaHc3JyTgG3gJPG+NdGXGDE1414BZABLM7JyUlrbm7ebYzfAn4GLgKfzAVgQV1dXTQej0f6+vr66+rqdmuadhL4LRwOqy6X62NN0wqAn0Kh0FN5eXkXPR7PMimlHBwcVG7cuPFEMBh8JhgMPnvu3LmnI5HIZuDl1tbWKDBRJyGEzM3NlcBbQgiM67AQokIIAfAjcBjYDviBY8Z4hRHvNeIzRpweDAbvulyuceAPY8xvMpn8gUBg5Pjx40NMlKY2OQmNM1pCrwPeK1eutBcWFlYIIV6YdO9C4osQomLyj4QQ+yeFitVqHQW+FUIcYmJJvyalvHDkyJFXgEYgP1kCXdcTJVkGjJw/f95bWFiYDSx+UI3uI8VkMimAFXgRuBaLxS5v3LhxO9AphHgNJrXh7du3qaio2AycqK6ufsnn8zVPvJSoTRHA3NPToy9duvRx4GosFgtmZ2dnAm1CiJxEUvIfiMfj2Gy2ZYFAoMHn8119SHOAcGZmprm5uXnv2NjYRcO81djak0qeCS9dusTo6Oi7fr9/x/Lly++VlpbWP4S5BD4DVnd1dfU7nc4lQIsQYvvkJE3TkgDdwPNSSqlMmY2pStf1kZaWluGjR49agAtCiB1TczRNm2hDY8nsNsjHjc9Hcd0DamYC/Qfb3R8nqSPZYgAAAABJRU5ErkJggg=='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_obj_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_obj_btn_ico) == False:
        send_obj_btn_ico = 'cube.png'

    # Send FBX Icon
    send_fbx_btn_ico = icons_folder_dir + 'gt_mtod_send_fbx.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_fbx_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTAzVDExOjU1OjM4LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wM1QxMjo1NjozOS0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0xMS0wM1QxMjo1NjozOS0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDozY2U2OWNjNy1lODkwLTVlNGEtOWI3Mi1kZTFjMzA4ZWU0Y2EiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDo5MDFkZGY4NC1jNzIyLWFiNGQtYTI3Yi1hYjZkNDg3NGEwMzMiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo3NGEyNGY5Yi1lZWZlLWYwNGYtOWI2Zi01NmRhZWIyNDBjNGQiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjc0YTI0ZjliLWVlZmUtZjA0Zi05YjZmLTU2ZGFlYjI0MGM0ZCIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDozY2U2OWNjNy1lODkwLTVlNGEtOWI3Mi1kZTFjMzA4ZWU0Y2EiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6NTY6MzktMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4KTpaaAAAGLElEQVRYhcWWb2hU2RnGf+ece2fGQSdmolXQBoWKEXbV1sT1i23YTaqNXWxlaxdNswEtspCYT6WaioXGQqH4xUooLaTdhUJXSqqiFFM3tiBGkxtiachkhLTWHZKaxMRkopNM5p7TD7kzOxlnoptd6AuXe7nnve/z3HOe948wxvD/NAugt7d3KZ/zQAPg+4IwZwAD/GfXrl2vWy9x/gCom56ejl+8eFHiEV6Oaa0ZHh7mxIkTK3fs2AHwmhDin0sFbAPqRkZGJsfGxorb29sfAecAsVwShw8f3rx9+/YfRSKRZxs2bAgBrxUi8AFQV1dX96c9e/a8c+zYMQ3EHMf57XLBgR8Cp+7evfvz8+fPn7p06RLAhMzj+CFQ19LS8vHAwMA7tbW114QQSWDH5wT/TVdX1/WGhoafHDx4sFUIAVCcS+B3wA/OnTvXeeXKlbeAmlAoNKO1lkBqmeAnPPBrjY2NB4CW2traHm9NZBNoBeoPHTr00eXLl98EDjiO8xdgUmttWFDucsB/fefOneuNjY3fBn7mOM5ZwE07pDXwS+D98fHxp5WVld+vr69vC4VC3wJqgLf8fr/V3NwcAH71GcBngFNdXV3XT548ecAD/2mukzDG0Nvba6ampqbGxsaKNm7cqJVSKa01WmutlFLGGCuRSBAIBJJSSiG8Ayxkxhh8Pp/d398fqa+v3wa0eH+etiPAH8rLyz/N60gkUjQyMjI5MDAwl0gkwgBCCIwx8+3t7fNDQ0MAz7xds3w+n9y3b58qKyuTaT7ZVbWmpsY8ePBgG/BRDvgiyxDQWlNSUvJw9erVo9kOw8PDT4eGhv4BXInH4wPZ38bj8eq+vr53Hz9+vC43sN/v31tUVGQBU0vtVkaEyWQS8ghtbm4uBTzKAQdAKZWybbtQdghvR0KvREBKiVIqXzABzBV4L6SUeikAXpI9GQJ+vx9jzAvi8gSXT3TGdd1ll+UXCFiWheu6dq5DMBi0CxBIKaU+N4GMCIeGhnj48OFkSUnJJ+l3gUDAKi0tXd3W1nYAKMr6zgDPgsHgf7u7u6OxWEyYBUMpJZVSoqys7LMR6Onpoaur667P5/sbgFJK+P1+0dTU9LX9+/e/9+jRozf49DyF1nr+xo0bfz179uy1YDDYZ4yxXNfVfr9fKKXUkSNHvgeoVyagtWZ2drZ7dna2M2tdHD161HVd991YLFYqhMgIyhjDyMhIdSqVuj09Pf3nNNjz588NIC3LmuUVhpgMAdu2AUw8Hs/NBPHkyRPjgWbO3HVdo7X2AeF4PG5Y3KzcaDT6VAix6mUEMiJUSlGIcb7sABBCaAoPKMNSymSBtUwzyhDwymm+ASVvnntlukB8AB5rrdPzX65Nph8ygB6BfH8zk4+ElFIkk8m8bToajSoguHfv3rUdHR1vA//2lgzwCbDyBQJbtmyhqqpqDzCfE+/5hQsXfhGNRn9s27aSUqK1RkrJmjVr7NbW1gpy6v3WrVtXDg4OFicSidTg4GDQsiwFiPHx8VRFRcWX165da3V2dk4A4Uw7vnr1Kps2bboRDoefZAeLxWKjDQ0NN4F/AV8CbEAWFxfLM2fOfHXz5s3btdbKsqxFxFetWvX1e/fuWc3NzRq47+0at2/fru7p6Uk1NTWtAD7M7EAikSCZTPonJiZKsgONjo4KYGU8Ho8AkawlFY/HTX9//1disdiG3GMIh8NFgUDABf7oOM77LMyU940xN5uamt4ALgPvLSrFtm3PS7nwKn03C0rLJyTh8/l0vmYkpcSyLNsYE2Chgu4E7s/MzPRUVFRUAXcdx/ku5HRDb/hESim0XhQ3LwHXdfNN1WmNyGg0SjgcXgH0zczMdFdWVlYAtxzH+WYGN/0wNzeHMUZ6o5gplPvZ5rquKOQ3MTExunv3brujo+M7qVTq75WVlbuBTsdx3sz2y2hg3bp1rFixAsC2bVsJIYRlWWr9+vX6+PHj26LRaDXgx0tVKaUKhUKvFxUVlc7Pz4e9yZn0zOj3+wM7d+5U/f39k/X19d8APnYcp+qFbfSyIAKUGWPMywbOV7VUKuXeunXr2enTp0PATcdxqnN9ysvLF5qKV9EiLJy1692/iCsB/H4pov8DCy25+irlAG4AAAAASUVORK5CYII='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_fbx_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_fbx_btn_ico) == False:
        send_fbx_btn_ico = 'cube.png'
        
    # Send Message Only Icon
    send_message_btn_ico = icons_folder_dir + 'gt_mtod_message.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(send_message_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTAzVDExOjU1OjM4LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wM1QxMzoyMDowOC0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0xMS0wM1QxMzoyMDowOC0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo0YmU0YzBlZi05OWYzLTliNDItYTIwOC0xNTRiZDFhOGQyOTMiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDozMWQyOGU2MC1jZTlhLWMwNDktODY3ZS1hMTE1M2Y1ZDVlNTYiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplN2EzZjY5NC1jNDAxLTllNDYtYjAyZC1hOTA4MmEwODc0MmUiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU3YTNmNjk0LWM0MDEtOWU0Ni1iMDJkLWE5MDgyYTA4NzQyZSIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo0YmU0YzBlZi05OWYzLTliNDItYTIwOC0xNTRiZDFhOGQyOTMiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTM6MjA6MDgtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7oCTqAAAADaElEQVRYhe2XTUhcVxTHf/eNzles2ZXoIlMIpISIDfV10ZrABIKJIi5TqkQFqQwUW5DioogUrasuQiRuQnBhAlmKRsgHQYgjScHrgLGII51NakKN1fapYdCZNzeL9950ZpqRxJngIvnDg/dxzj2/e855990nlFIcpLQDjf4BACgBmJubK2SMHmAAmAPuAdeBZ8Bp4CJwDvgUOAM8cpxqamqA4mQgCbiBL4GflVJP4/H4FBAGuoATgNbW1hbWdf0rx0kIAdgZKFBXW1tbD3u93r5gMEhzc7Pm8/nObm1t7Y6MjLhnZ2dZXV3FMAzNhs1SMQB2FxcXB4FrkUjkWCAQuFJbW3uqr6/PHQ6HXwC/AlPAn8DGuwBASrmLVfdnwAPgVCqVAuiQUk7u5esAHKfwfvjbPjwAbrcbIAUcBfw5tilgORNgHvAWEn1tbe1WfX3991JKAEzTxIZ5CHySaauU2gGqgWUHwAsQi8WIx+P7AhgbG/sG+AcwId3lSWAyGo1+m0gkPABVVVUIITxYk/Zl9UBnZyeGYfwOvNwXBUSAzwBcLhdYZe1qaWkB+AJgenq6xu/3l2BP2gFQgPD7/RiGEZRSfg748gR5Afy2B8RQxrkLQErZlXHvX+Cwc5GVgZ2dHYAy4H6+0be3t58Gg8GvpZR7Qbyxsjrfrlsc+CufQzQaPYq13BZFWQD2u6sBR/I5VFRUAKwVCyCrBB6PB6wu7h0dHf3ldQ4rKysAgWIDCICNjQ2wmm9waGgIMpolR38UEDP1OoAEUNrb20tdXV0PkHQWlDw6CVzJuXcHuJuOYpVTAN9hrbSOPkom//smOQClAA0NDdgOb635+fkLHR0dPzjgNoAJXHbGTwctKQFr0mmAS/39/Tf2E9jR0tLScaANu0E1TXMAmgYGBiaVUi7H1s5AaSbAzYmJCbA2FoUoArRD+pV2AbfHx8cbgcoc291MAKSUNwsM7mgbYH19HezmllLezTXSdZ0sgCLoEHAeqwyEQiFisdjHWFkw8zkJpVShm9J2YJCMFG9ubqbKy8s1AKVUQgjxHGgCnjg2uq6jlCrKprQSqDRNk5mZGbq7u2lsbNSGh4dfLiwsIIQoBQKhUOieruvV//NWSlGE37OfsL6oCWASa7ZlwI/AY/uZAmpzY4sP/4bvPcAr3RsqGl/Oz1oAAAAASUVORK5CYII='
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(send_message_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    if os.path.exists(send_message_btn_ico) == False:
        send_message_btn_ico = 'renamePreset.png'

    cmds.separator(h=5)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 100),(2, 143),(4, 37)], cs=[(1, 18),(2, 0),(3, 0),(4, 0)], p=content_main)
    cmds.text(l='Webhoook Name:', align="center", fn="boldLabelFont")
    webhook_name_text = cmds.text(l='...', align="center", fn="tinyBoldLabelFont")
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=3, cw=[(1, 100),(2, 50),(3, 100),(4, 50)], cs=[(1, 10),(2, 0),(3, 0),(4, 0)], p=content_main)
    
    cmds.text(l='Web Response:', align="center", fn="boldLabelFont")
    status_code_text = cmds.text(l='', align="center")
    status_message_text = cmds.text(l='', align="center")
    
    
    if gt_mtod_settings['is_first_time_running'] == True:
        cmds.text(webhook_name_text, e=True, l='Set Webhook in the Settings', bgc= [1,1,0])
    else:
        if 'Error' in gt_mtod_settings.get('discord_webhook_name') or 'Missing Webhook' in gt_mtod_settings.get('discord_webhook_name'):
            cmds.text(webhook_name_text, e=True, l=gt_mtod_settings.get('discord_webhook_name'), bgc=[.5,0,0])
        else:
            cmds.text(webhook_name_text, e=True, l=gt_mtod_settings.get('discord_webhook_name'), nbg=True)
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main) 
    cmds.separator(h=7, style='none') # Empty Space
    cmds.separator(h=5)
    
    cmds.separator(h=7, style='none') # Empty Space
    attached_message_txtfield = cmds.textField(pht='Attached Message (Optional)', text="")
    cmds.separator(h=10, style='none') # Empty Space
    
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 260),(2, 1),(3, 5)], cs=[(1, 10),(2, 0),(3, 0)], p=content_main)
    send_message_btn = cmds.iconTextButton( style='iconAndTextHorizontal', image1=send_message_btn_ico, label='Send Message Only',\
                                            statusBarMessage='This button will record a playblast and attempt to send it to Discord.',\
                                            olc=[1,0,0] , enableBackground=True, bgc=[.3,.3,.3], h=40, marginWidth=60,\
                                            command=lambda: send_message_only())
    cmds.separator(h=2, style='none') # Empty Space
    
    screenshot_btn_color = [.3,.3,.35]
    cmds.rowColumnLayout(nc=1, cw=[(1, 260),(2, 1),(3, 5)], cs=[(1, 10),(2, 0),(3, 0)], p=content_main) 
    send_desktop_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=send_desktop_btn_ico, label='Send Desktop Screenshot',\
                                            statusBarMessage='This button will take a screenshot of the entire desktop and send it to Discord. (In case of multiple monitors, it will use the one with the main Maya window)',\
                                            olc=[1,0,0] , enableBackground=True, bgc=screenshot_btn_color, h=80,\
                                            command=lambda: send_dekstop_screenshot())
    
    cmds.separator(h=2, style='none') # Empty Space
                         
    cmds.rowColumnLayout(nc=2, cw=[(1, 128),(2, 128),(3, 5)], cs=[(1, 10),(2, 4),(3, 0)], p=content_main)      
    send_maya_window_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=send_maya_window_btn_ico, label='Send Maya Window',\
                                                statusBarMessage='This button will take a screenshot of Maya window without any other elements that might be on top of it, then send it to Discord',\
                                                olc=[1,0,0] , enableBackground=True, bgc=screenshot_btn_color, h=80,\
                                                command=lambda: send_maya_window())
                                            
    send_viewport_btn = cmds.iconTextButton( style='iconAndTextVertical', image1='hypershadeOutlinerPerspLayout.png', label='Send Viewport',\
                                            statusBarMessage='This button will take a screenshot of the currently active viewport then send it to Discord.',\
                                            olc=[1,0,0] , enableBackground=True, bgc=screenshot_btn_color, h=80,\
                                            command=lambda: send_viewport_only())
    
    objects_btn_color = [.25,.3,.35]          
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 260),(2, 1),(3, 5)], cs=[(1, 10),(2, 0),(3, 0)], p=content_main)
    send_playblast_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=send_playblast_btn_ico, label='Send Playblast',\
                                              statusBarMessage='This button will record a playblast and attempt to send it to Discord.',\
                                              olc=[1,0,0] , enableBackground=True, bgc=objects_btn_color, h=80,\
                                              command=lambda: send_animated_playblast())
    
    cmds.separator(h=2, style='none') # Empty Space
                         
    cmds.rowColumnLayout(nc=2, cw=[(1, 128),(2, 128),(3, 5)], cs=[(1, 10),(2, 4),(3, 0)], p=content_main)      
    send_obj_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=send_obj_btn_ico, label='Send OBJ',\
                                        statusBarMessage='This button will export your selection as OBJ and attempt to send it to Discord. (See "Help" for more information)',\
                                        olc=[1,0,0] , enableBackground=True, bgc=objects_btn_color, h=80,\
                                        command=lambda: send_model_obj())
    send_fbx_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=send_fbx_btn_ico, label='Send FBX',\
                                        statusBarMessage='This button will export your selection as FBX and attempt to send it to Discord. (See "Help" for more information)',\
                                        olc=[1,0,0] , enableBackground=True, bgc=objects_btn_color, h=80,\
                                        command=lambda: send_model_fbx())
                    
    cmds.separator(h=10, style='none') # Empty Space
    

    
    # Functions for the buttons -----------
    def get_date_time_message():
        ''' 
        Returns formated string of date and time to be used as a message 
        
                    Returns:
                        date_and_time (str): A formated string containing current date and time.
        
        ''' 
        now = datetime.datetime.now()
        return now.strftime("Date: %m/%d/%Y - Time: %H:%M:%S")
        
    def get_username():
        ''' 
        Returns string to be used as username, it extracts it from the computer's username.
        A custom username may be used, in which case the function returns the custom username followed by the computer's username.
           
                    Returns:
                        username (str): A string composed of custom username (if it exists) and the computer's username
        ''' 
        if gt_mtod_settings.get('custom_username') == '':
            user_name = socket.gethostname()
        else:
            user_name = gt_mtod_settings.get('custom_username') + ' (' + socket.gethostname() + ')'

        return user_name
    
    
    def update_text_status(error=False):
        ''' 
        Updates UI texts to say "Uploading" or "Error" 
        
                Parameters:
                    error (bool): Determines if it will update it to be red and say error or yellow to say Uploading. Default = Uploading (False)
        
        ''' 
        if not error:
            cmds.text(status_message_text, e=True, l='Uploading', bgc=(1, 1, 0))
            cmds.text(status_code_text, e=True, l='...', bgc=(1, 1,0))
        else:
            cmds.text(status_message_text, e=True, l='...', bgc=(.5, 0, 0))
            cmds.text(status_code_text, e=True, l='Error', bgc=(.5, 0, 0))

    def clear_attached_message(response):
        ''' 
        Clears the attached message when a success code is received
        
                Parameters:
                    response (dict): A dictionary response received from a HTTP object after post/get operation.
        
        '''
        if len(response) >= 1:
            status_value = response[0].status
            success_codes = [200, 201, 202, 203, 204, 205, 206]

            if status_value in success_codes: 
                cmds.textField(attached_message_txtfield, e=True, text='')

    
    def parse_sending_response(response):
        '''
        Processes response received when sending an image/video and updates UI text accordingly
        
                Parameters:
                    response (dict): A dictionary response received from a HTTP object after post/get operation.
        
        '''
        if len(response) >= 1:
            status_value = response[0].status
            reason_value = response[0].reason
            success_codes = [200, 201, 202, 203, 204, 205, 206]

            if status_value in success_codes: 
                cmds.text(status_message_text, e=True, l=reason_value, bgc=(0, 0.5, 0))
                cmds.text(status_code_text, e=True, l=status_value, bgc=(0, 0.5,0))
            else: # Error
                cmds.text(status_message_text, e=True, l=reason_value, bgc=(0.5, 0, 0))
                cmds.text(status_code_text, e=True, l=status_value, bgc=(0.5, 0,0))
        else :
            cmds.text(status_message_text, e=True, l='Can\'t read response', bgc=(0.5, 0,0))
            cmds.text(status_code_text, e=True, l='Can\'t read response', bgc=(0.5, 0,0))
            
    def attached_text_message(operation_name, response):
        '''
        Attaches message to the content sent according the response received and the content of the message.
        
                Parameters:
                    operation_name (string): Name of the operation, used to write an output message.
                    response (dict): A dictionary response received from a HTTP object after post/get operation. (This should be the response of the previous operation)
        
        '''
        if len(response) >= 1:
            status_value = response[0].status
            success_codes = [200, 201, 202, 203, 204, 205, 206]
            if status_value in success_codes: 
                try:  
                    upload_message = cmds.textField(attached_message_txtfield, q=True, text=True)
                    if upload_message.strip() != '': 
                        def threaded_upload():
                            try:
                                discord_post_message(get_username(), upload_message, gt_mtod_settings.get('discord_webhook'))
                                utils.executeDeferred(response_inview_feedback, operation_name, response, display_inview=gt_mtod_settings.get('feedback_visibility'))
                                utils.executeDeferred(clear_attached_message, response)
                            except Exception as e:
                                print(e)
                            
                        thread = threading.Thread(None, target = threaded_upload)
                        thread.start()
                    else:
                        response_inview_feedback(operation_name, response, display_inview=gt_mtod_settings.get('feedback_visibility'))
                except:
                    pass
        
                    
    def disable_buttons():
        ''' Disable buttons so user don't accidently send multiple requests at once ''' 
        cmds.iconTextButton(send_message_btn, e=True, enable=False)
        cmds.iconTextButton(send_desktop_btn, e=True, enable=False)
        cmds.iconTextButton(send_maya_window_btn, e=True, enable=False)
        cmds.iconTextButton(send_viewport_btn, e=True, enable=False)
        cmds.iconTextButton(send_playblast_btn, e=True, enable=False)
        cmds.iconTextButton(send_obj_btn, e=True, enable=False)
        cmds.iconTextButton(send_fbx_btn, e=True, enable=False)
    
    def enable_buttons():
        ''' Enable buttons after finishing previously requested function ''' 
        cmds.iconTextButton(send_message_btn, e=True, enable=True)
        cmds.iconTextButton(send_desktop_btn, e=True, enable=True)
        cmds.iconTextButton(send_maya_window_btn, e=True, enable=True)
        cmds.iconTextButton(send_viewport_btn, e=True, enable=True)
        cmds.iconTextButton(send_playblast_btn, e=True, enable=True)
        cmds.iconTextButton(send_obj_btn, e=True, enable=True)
        cmds.iconTextButton(send_fbx_btn, e=True, enable=True)

    # Button Functions ----------
    webhook_error_message = 'Sorry, something went wrong. Please review your webhook and settings.'
    def send_dekstop_screenshot():
        ''' Attempts to send a desktop screenshot using current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            try:
                update_text_status()
                temp_path = generate_temp_file(gt_mtod_settings.get('image_format'))
                temp_desktop_ss_file = capture_desktop_screenshot(temp_path)
                if gt_mtod_settings.get('timestamp_visibility'):
                    upload_message = get_date_time_message()
                else:
                    upload_message = ''
                def threaded_upload():
                    try:
                        utils.executeDeferred(disable_buttons)
                        response = discord_post_attachment(get_username(), upload_message, temp_desktop_ss_file, gt_mtod_settings.get('discord_webhook'))
                        utils.executeDeferred(enable_buttons)
                        utils.executeDeferred(parse_sending_response, response)
                        utils.executeDeferred(attached_text_message, 'desktop screenshot', response)
                    except:
                        update_text_status(error=True)
                        cmds.warning(webhook_error_message)
                    
                
                thread = threading.Thread(None, target = threaded_upload)
                thread.start()

            except:
                update_text_status(error=True)
                cmds.warning(webhook_error_message)
        else:
            cmds.warning(webhook_error_message)
    
    def send_maya_window():
        ''' Attempts to send an image of the maya window using current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            try:  
                update_text_status()
                temp_path = generate_temp_file(gt_mtod_settings.get('image_format'))
                temp_img_file = capture_app_window(temp_path)
                if gt_mtod_settings.get('timestamp_visibility'):
                    upload_message = get_date_time_message()
                else:
                    upload_message = ''                  
                def threaded_upload():
                    try:
                        utils.executeDeferred(disable_buttons)
                        response = discord_post_attachment(get_username(), upload_message, temp_img_file, gt_mtod_settings.get('discord_webhook'))
                        utils.executeDeferred(enable_buttons)
                        utils.executeDeferred(parse_sending_response, response)
                        utils.executeDeferred(attached_text_message, 'Maya window screenshot', response)
                    except:
                        update_text_status(error=True)
                        cmds.warning(webhook_error_message)
                    
                thread = threading.Thread(None, target = threaded_upload)
                thread.start()
            except:
                update_text_status(error=True)
                cmds.warning(webhook_error_message)
        else:
            cmds.warning(webhook_error_message)
        
    def send_viewport_only():
        ''' Attempts to send an image of the active viewport using current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
            
        if gt_mtod_settings.get('is_webhook_valid'):
            try:
                update_text_status()
                temp_path = generate_temp_file(gt_mtod_settings.get('image_format'))
                if maya_version in ['2017','2018','2019']:
                    temp_img_file = capture_viewport_playblast(temp_path)
                else:
                    temp_img_file = capture_viewport(temp_path)
                if gt_mtod_settings.get('timestamp_visibility'):
                    upload_message = get_date_time_message()
                else:
                    upload_message = ''
                def threaded_upload():
                    try:
                        utils.executeDeferred(disable_buttons)
                        response = discord_post_attachment(get_username(), upload_message, temp_img_file, gt_mtod_settings.get('discord_webhook'))
                        utils.executeDeferred(enable_buttons)
                        utils.executeDeferred(parse_sending_response, response)
                        utils.executeDeferred(attached_text_message, 'viewport screenshot', response)
                    except:
                        update_text_status(error=True)
                        cmds.warning(webhook_error_message)
                    
                thread = threading.Thread(None, target = threaded_upload)
                thread.start()
            except:
                update_text_status(error=True)
                cmds.warning(webhook_error_message)
        else:
            cmds.warning(webhook_error_message)
            
    def send_animated_playblast():
        ''' Attempts to record a playblast and upload it using the current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            try:
                update_text_status()
                current_scene_name = cmds.file(q=True, sn=True).split('/')[-1]
                if current_scene_name == '': # If not saved
                    current_scene_name ='never_saved_untitled_scene'
                else:
                    if current_scene_name.endswith('.ma') or current_scene_name.endswith('.mb'):
                        current_scene_name=current_scene_name[:-3]

                temp_path = generate_temp_file( gt_mtod_settings.get('video_format'), file_name=current_scene_name)
                disable_buttons() # This needs to happen before creating the playblast to avoid multiple clicks
                temp_playblast_file = capture_playblast_animation(temp_path, gt_mtod_settings.get('video_scale_pct'), gt_mtod_settings.get('video_compression'), gt_mtod_settings.get('video_output_type') )
                
                if gt_mtod_settings.get('timestamp_visibility'):
                    upload_message = get_date_time_message()
                else:
                    upload_message = ''
                
                def threaded_upload():
                    try:
                        response = discord_post_attachment(get_username(), upload_message, temp_playblast_file, gt_mtod_settings.get('discord_webhook'))
                        utils.executeDeferred(enable_buttons)
                        utils.executeDeferred(parse_sending_response, response)
                        utils.executeDeferred(attached_text_message, 'playblast', response)
                    except:
                        update_text_status(error=True)
                        cmds.warning(webhook_error_message)
                        utils.executeDeferred(enable_buttons)
                    finally:
                        utils.executeDeferred(enable_buttons)
                    
                thread = threading.Thread(None, target = threaded_upload)
                thread.start()
            except:
                update_text_status(error=True)
                cmds.warning(webhook_error_message)
                enable_buttons()

        else:
            cmds.warning(webhook_error_message)


    def send_message_only():
        ''' Attempts to send the message only (no images/videos) using current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            try:  
                upload_message = cmds.textField(attached_message_txtfield, q=True, text=True)
                if upload_message.strip() != '':
                    update_text_status()
                    def threaded_upload():
                        try:
                            utils.executeDeferred(disable_buttons)
                            response = discord_post_message(get_username(), upload_message, gt_mtod_settings.get('discord_webhook'))
                            utils.executeDeferred(enable_buttons)
                            utils.executeDeferred(parse_sending_response, response)
                            utils.executeDeferred(response_inview_feedback, 'message', response, display_inview=gt_mtod_settings.get('feedback_visibility'))
                            utils.executeDeferred(clear_attached_message, response)
                        except:
                            update_text_status(error=True)
                            cmds.warning(webhook_error_message)
                        
                    thread = threading.Thread(None, target = threaded_upload)
                    thread.start()
                else:
                    cmds.warning('Your message is empty, please type something in case you want to send only a message.')
            except:
                update_text_status(error=True)
                cmds.warning(webhook_error_message)
        else:
            cmds.warning(webhook_error_message)

    def send_model_obj():
        ''' Attempts to export selected model as an OBJ file and upload it using the current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            selection = cmds.ls(selection=True)
            if len(selection) > 0:
                try:
                    update_text_status()
       
                    # Determine naming
                    if len(selection) == 1:
                        export_name = selection[-1]
                    else:
                        export_name = str(len(selection)).zfill(2) + '_selected_objects'

                    temp_path = generate_temp_file( 'obj', file_name=export_name)
                    disable_buttons() 
               
                    temp_exported_obj = cmds.file(temp_path, pr=1, typ="OBJexport",es=1, f=True, op="groups=0; ptgroups=0; materials=0; smoothing=0; normals=0")
                    
                    if gt_mtod_settings.get('timestamp_visibility'):
                        upload_message = get_date_time_message()
                    else:
                        upload_message = ''
                    
                    def threaded_upload():
                        try:
                            response = discord_post_attachment(get_username(), upload_message, temp_exported_obj, gt_mtod_settings.get('discord_webhook'))
                            utils.executeDeferred(enable_buttons)
                            utils.executeDeferred(parse_sending_response, response)
                            utils.executeDeferred(attached_text_message, 'OBJ file', response)
                        except:
                            update_text_status(error=True)
                            cmds.warning(webhook_error_message)
                            utils.executeDeferred(enable_buttons)
                        finally:
                            utils.executeDeferred(enable_buttons)
                        
                    thread = threading.Thread(None, target = threaded_upload)
                    thread.start()
                except:
                    update_text_status(error=True)
                    cmds.warning(webhook_error_message)
                    enable_buttons()
            else:
                cmds.warning('Nothing selected. Please, select what you want to send.')
        else:
            cmds.warning(webhook_error_message)

    def send_model_fbx():
        ''' Attempts to export selected model as an FBX file and upload it using the current settings '''
        if gt_mtod_settings.get('is_new_instance'):
            update_discord_webhook_validity(gt_mtod_settings.get('discord_webhook'))
        
        if gt_mtod_settings.get('is_webhook_valid'):
            selection = cmds.ls(selection=True)
            if len(selection) > 0:
                try:
                    update_text_status()
       
                    # Determine naming
                    if len(selection) == 1:
                        export_name = selection[-1]
                    else:
                        export_name = str(len(selection)).zfill(2) + '_selected_objects'

                    temp_path = generate_temp_file( 'fbx', file_name=export_name)
                    disable_buttons() 
               
                    cmds.FBXExport('-file', temp_path, '-s')
                    
                    if gt_mtod_settings.get('timestamp_visibility'):
                        upload_message = get_date_time_message()
                    else:
                        upload_message = ''
                    
                    def threaded_upload():
                        try:
                            response = discord_post_attachment(get_username(), upload_message, temp_path, gt_mtod_settings.get('discord_webhook'))
                            utils.executeDeferred(enable_buttons)
                            utils.executeDeferred(parse_sending_response, response)
                            utils.executeDeferred(attached_text_message, 'FBX file', response)
                        except:
                            update_text_status(error=True)
                            cmds.warning(webhook_error_message)
                            utils.executeDeferred(enable_buttons)
                        finally:
                            utils.executeDeferred(enable_buttons)
                        
                    thread = threading.Thread(None, target = threaded_upload)
                    thread.start()
                except:
                    update_text_status(error=True)
                    cmds.warning(webhook_error_message)
                    enable_buttons()
            else:
                cmds.warning('Nothing selected. Please, select what you want to send.')
        else:
            cmds.warning(webhook_error_message)


    # Show and Lock Window
    cmds.showWindow(build_gui_maya_to_discord)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(icon_image)
    
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================

# Creates Help GUI
def build_gui_help_maya_to_discord():
    ''' Builds the Help UI for GT Maya to Discord '''
    window_name = "build_gui_help_maya_to_discord"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space
    
    # Body ====================
    help_font = 'smallPlainLabelFont'
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.text(l=script_name + ' allows you to quickly send', align="center")
    cmds.text(l='images and videos (playblasts) from Maya to Discord', align="center")
    cmds.text(l='using a Discord Webhook to bridge the two programs.', align="center")
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Webhooks:', align="center", fn="boldLabelFont")
    cmds.text(l='A webhook (a.k.a. web callback or HTTP push API) is a way for', align="center", font=help_font)
    cmds.text(l='an app to provide other applications with real-time information.', align="center", font=help_font)
    cmds.text(l='You can use it to send messages to text channels without', align="center", font=help_font)
    cmds.text(l='needing the discord application.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='How to get a Webhook URL:', align="center", fn="boldLabelFont")
    cmds.text(l='If you own a Discord server or you have the correct privileges, ', align="center", font=help_font)
    cmds.text(l='you can go to the settings to create a Webhook URL.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='To create one go to:', align="center", font=help_font)
    cmds.text(l='Discord > Server > Server Settings > Webhooks > Create Webhook', align="center", font=help_font)
    cmds.text(l='Give your webhook a name and select what channel it will operate.', align="center", font=help_font)
    cmds.text(l='Copy the "Webhook URL" and load it in the setttings for this script.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='If you\'re just an user in the server, you\'ll have to ask the', align="center", font=help_font)
    cmds.text(l='administrator of the server to provide you with a Webhook URL.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Send Buttons:', align="center", fn="boldLabelFont")
    cmds.text(l='Send Message Only: Sends only the attached message', align="center", font=help_font)
    cmds.text(l='(Use the textfield above the buttons to type your message)', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Send Desktop Screenshot: Sends a screenshot of your desktop.', align="center", font=help_font)
    cmds.text(l='(This includes other programs and windows that are open)', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Send Maya Window: Sends only the main Maya window.', align="center", font=help_font)
    cmds.text(l='(This ignores other windows, even within Maya)', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Send Viewport: Sends an image of the active viewport', align="center", font=help_font)
    cmds.text(l='(Includes Heads Up Display text, but no UI elements)', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Send Playblast: Sends a playblast video', align="center", font=help_font)
    cmds.text(l='(Use the script settings to determine details about the video)', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Send OBJ/FBX: Sends a model using the chosen format', align="center", font=help_font)
    cmds.text(l='For settings, go to "File > Export Selection... > Options"', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Settings:', align="center", fn="boldLabelFont")
    cmds.text(l='The settings are persistent, which means they will stay the same', align="center", font=help_font)
    cmds.text(l='between Maya sessions.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Custom Username:', align="center", font=help_font)
    cmds.text(l='Nickname used when posting content through the webhook.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Image & Video Format', align="center", font=help_font)
    cmds.text(l='Extension used for the image and video files.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Video Options:', align="center", font=help_font)
    cmds.text(l='Determines the settings used when recording a playblast.', align="center", font=help_font)
    cmds.separator(h=7, style='none') # Empty Space
    cmds.text(l='Feedback and Timestamp Options:', align="center", font=help_font)
    cmds.text(l='Determines feedback visibility and timestamp use.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Limitations:', align="center", fn="boldLabelFont")
    cmds.text(l='Discord has a limit of 8MB for free users and 50MB for paid users', align="center", font=help_font)
    cmds.text(l='for when uploading a file. If you get the error "Payload Too Large"', align="center", font=help_font)
    cmds.text(l='it means your file exceeds the limits. Try changing the settings.', align="center", font=help_font)
    
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='Reset Persistent Settings', h=30, c=lambda args: reset_persistent_settings_maya_to_discord())
    cmds.separator(h=5, style='none')
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




def build_gui_settings_maya_to_discord():
    ''' Builds the Settings UI for GT Maya to Discord '''
    window_name = "build_gui_settings_maya_to_discord"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Settings", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])


    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Settings", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space
    
    
    # Current Settings =================
    current_image_format = gt_mtod_settings.get('image_format')
    current_video_format = gt_mtod_settings.get('video_format')
    current_webhook = ''
    current_custom_username = ''
    if not gt_mtod_settings.get('is_first_time_running'):
        if gt_mtod_settings.get('discord_webhook') != '':
            current_webhook = gt_mtod_settings.get('discord_webhook')
        if gt_mtod_settings.get('custom_username') != '':
            current_custom_username = gt_mtod_settings.get('custom_username')
    current_video_scale = gt_mtod_settings.get('video_scale_pct')
    current_compression = gt_mtod_settings.get('video_compression')
    current_output_type = gt_mtod_settings.get('video_output_type')
    
    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column) 
    
    cmds.text(l='Discord Webhook Url', align="center")
    cmds.separator(h=5, style='none') # Empty Space
    new_webhook_input = cmds.textField(pht='https://discordapp.com/api/webhooks/...', text=current_webhook, font= 'smallPlainLabelFont')
    
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 120),(2, 85),(3, 85)], cs=[(1,10),(2,5),(3,5)], p=main_column)
    
    cmds.text(l='Custom Username ', align="center")
    cmds.text(l='Image Format ', align="center")
    cmds.text(l='Video Format ', align="center")
    new_username_input = cmds.textField(pht='username (not required)', text=current_custom_username, font= 'smallPlainLabelFont')
    new_image_format_input = cmds.textField(pht='jpg', text=current_image_format, font= 'smallPlainLabelFont')
    new_video_format_input = cmds.textField(pht='mov', text=current_video_format, font= 'smallPlainLabelFont')
    

    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 90),(2, 95),(3, 105)], cs=[(1,10),(2,5),(3,5)], p=main_column)
    cmds.text(l='Video Scale % ', align="center", font= 'smallPlainLabelFont')
    cmds.text(l='Video Compression ', align="center", font= 'smallPlainLabelFont')
    cmds.text(l='Video Output Type ', align="center", font= 'smallPlainLabelFont')
    
    video_scale_input = cmds.intSliderGrp( field=True, minValue=1, maxValue=100, fieldMinValue=1, fieldMaxValue=100, value=current_video_scale, cw=([1,35],[2,65]))
    
    compression_input = cmds.optionMenu()
    try:
        for name in get_available_playblast_compressions(current_output_type):
            cmds.menuItem( label=name )
            
        # Find stored menuItem and select it
        for idx,obj in enumerate(cmds.optionMenu(compression_input, q=True, itemListLong=True)):
            if cmds.menuItem( obj , q=True, label=True ) == current_compression:
                cmds.optionMenu(compression_input, e=True, select=idx+1) # 1-based selection
    except:
        cmds.menuItem( label='none' )

    output_type_input = cmds.optionMenu(cc=lambda args: update_available_compressions())   
    cmds.menuItem( label='qt' )
    cmds.menuItem( label='avi' )
    cmds.menuItem( label='movie' )
    
    # Find stored menuItem and select it
    for idx,obj in enumerate(cmds.optionMenu(output_type_input,q=True, itemListLong=True)):
        if cmds.menuItem( obj , q=True, label=True ) == current_output_type:
            cmds.optionMenu(output_type_input, e=True, select=idx+1)
     
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    
    cmds.rowColumnLayout(nc=4, cw=[(1, 15),(2, 140),(3, 15),(4, 100)], cs=[(1,20),(2,5),(3,5)], p=main_column)
    feedback_visibility_chk = cmds.checkBox(label='', value=gt_mtod_settings.get('feedback_visibility'), cc=lambda args: update_checkbox_settings_data())
    cmds.text(l='Display Viewport Feedback', align="left", font= 'smallPlainLabelFont')
    timestamp_visibility_chk = cmds.checkBox(label='', value=gt_mtod_settings.get('timestamp_visibility'), cc=lambda args: update_checkbox_settings_data())
    cmds.text(l='Include Timestamp', align="center", font= 'smallPlainLabelFont')
    cmds.separator(h=10, style='none') # Empty Space
    
    # Bottom Buttons
    cmds.rowColumnLayout(nc=2, cw=[(1, 145),(2, 145)], cs=[(1,10),(2,10)], p=main_column)
    cmds.button(l='Reset Settings', h=30, c=lambda args: reset_settings())
    cmds.button(l='Reset Webhook', c=lambda args: cmds.textField(new_webhook_input, e=True, text=''))
    cmds.separator(h=5, style='none')
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.button(l='Apply', h=30, bgc=(.6, .6, .6), c=lambda args: apply_settings())
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
    icon = QIcon(':/toolSettings.png')
    widget.setWindowIcon(icon)
    
    
    def update_available_compressions():
        ''' Updates items stored in the optionMenu to contain only compatible compressions '''
        try:
            cmds.optionMenu(compression_input, e=True, dai=True)
            for name in get_available_playblast_compressions(cmds.optionMenu(output_type_input, q=True, value=True)):
                cmds.menuItem( label=name, p=compression_input)
        except:
            cmds.menuItem( label='none', p=compression_input )
    
    def reset_settings():
        ''' 
        Resets fields in the settings (do not affect stored variables or persistent setttings)
        It uses a deep copy of the settings dictionary to reset it.
        '''
        
        cmds.textField(new_username_input, e=True, text=gt_mtod_settings_default.get('custom_username'))
        cmds.textField(new_image_format_input, e=True, text=gt_mtod_settings_default.get('image_format'))
        cmds.textField(new_video_format_input, e=True, text=gt_mtod_settings_default.get('video_format') )
        
        for idx,obj in enumerate(cmds.optionMenu(output_type_input,q=True, itemListLong=True)):
            if cmds.menuItem( obj , q=True, label=True ) == gt_mtod_settings_default.get('video_output_type'):
                cmds.optionMenu(output_type_input, e=True, select=idx+1)
        
        update_available_compressions()
    
        found_default = False
        for idx,obj in enumerate(cmds.optionMenu(compression_input, q=True, itemListLong=True)):
            if cmds.menuItem( obj , q=True, label=True ) == gt_mtod_settings_default.get('video_compression'):
                cmds.optionMenu(compression_input, e=True, select=idx+1)
                found_default = True
        
        if not found_default:
            cmds.menuItem( label='none', p=compression_input )
            
        cmds.intSliderGrp(video_scale_input, e=True, value=gt_mtod_settings_default.get('video_scale_pct'))
        
        # Check box Management
        cmds.checkBox(feedback_visibility_chk, e=True, value=gt_mtod_settings_default.get('feedback_visibility'))
        cmds.checkBox(timestamp_visibility_chk, e=True, value=gt_mtod_settings_default.get('timestamp_visibility'))
        update_checkbox_settings_data()
                
        
    def apply_settings():
        ''' Transfer new settings to variables and store them as persistent settings '''
        set_persistent_settings_maya_to_discord(cmds.textField(new_username_input, q=True, text=True), cmds.textField(new_webhook_input, q=True, text=True),\
                                                cmds.textField(new_image_format_input, q=True, text=True), cmds.textField(new_video_format_input, q=True, text=True),\
                                                cmds.intSliderGrp(video_scale_input, q=True, value=True), cmds.optionMenu(compression_input, q=True, value=True),\
                                                cmds.optionMenu(output_type_input, q=True, value=True))
        gt_mtod_settings['is_first_time_running'] = False
        gt_mtod_settings['is_new_instance'] = True
        
        build_gui_maya_to_discord()
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
            
    def update_checkbox_settings_data():
        feedback_visibility = cmds.checkBox(feedback_visibility_chk, q=True, value=True)
        timestamp_visibility = cmds.checkBox(timestamp_visibility_chk, q=True, value=True)

        cmds.optionVar( iv=('gt_maya_to_discord_feedback_visibility', int(feedback_visibility)) )
        gt_mtod_settings['feedback_visibility'] = bool(cmds.optionVar(q=("gt_maya_to_discord_feedback_visibility")))
        
        cmds.optionVar( iv=('gt_maya_to_discord_timestamp_visibility', int(timestamp_visibility)) )
        gt_mtod_settings['timestamp_visibility'] = bool(cmds.optionVar(q=("gt_maya_to_discord_timestamp_visibility")))


def parse_discord_api(discord_webhook_full_path):
        ''' Parses and returns two strings to be used with HTTPSConnection instead of Http()
        
                Parameters:
                    discord_webhook_full_path (str): Discord Webhook (Full Path)
                    
                Returns:
                    discord_api_host (str): Only the host used for discord's api
                    discord_api_repo (str): The rest of the path used to describe the webhook
        '''
        path_elements = discord_webhook_full_path.replace('https://','').replace('http://','').split('/')
        host = ''
        repo = ''
        if len(path_elements) == 1:
            raise Exception('Failed to parse Discord Webhook path.')
        else:
            host = path_elements[0]
            for path_part in path_elements:
                if path_part != host:
                    repo += '/' + path_part
            return host, repo 

def generate_temp_file(file_format, file_name='tmp'):
    ''' 
    Generates a temporary file in the temp folder (Usually "C:/Users/USERNAME/AppData/Local/Temp/tmp.ext")
    
            Parameters:
                file_format (str) : Extension of the temp file
                file_name (str): File name (Optional)
    
            Returns:
                file ('unicode'): Path to generated file
    
    '''
    temp_dir = cmds.internalVar(userTmpDir=True)
    tmp_file = temp_dir + file_name + '.' + file_format
    return tmp_file
      

def capture_desktop_screenshot(image_file):
    ''' 
    Takes a snapshot of the entire Desktop and writes it to an image
    
            Parameters:
                image_file (str): File path for where to store generated image
                
            Returns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    app = QtWidgets.QApplication.instance()
    win = omui.MQtUtil_mainWindow()
    if python_version == 3:
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    else:
        ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    screen_number = app.desktop().screenNumber(ptr)
    screen_geometry = app.desktop().screenGeometry(screen_number)
    frame = app.primaryScreen().grabWindow(0, screen_geometry.x(), screen_geometry.y(), screen_geometry.width(), screen_geometry.height())
    frame.save(image_file)
    return image_file


def capture_app_window(image_file):
    ''' 
    Takes a snapshot of the entire Qt App (Maya) and writes it to an image
    
            Parameters:
                image_file (str): File path for where to store generated image
                
            Returns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    win = omui.MQtUtil_mainWindow()
    if python_version == 3:
        ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
        main_window_id = ptr.winId()
        long_win_id = int(main_window_id)
    else:
        ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
        main_window_id = ptr.winId()
        long_win_id = long(main_window_id)
    frame = QtGui.QPixmap.grabWindow(long_win_id)
    frame.save(image_file)
    return image_file

def capture_viewport(image_file):
    ''' 
    Takes a snapshot of the active viewport and writes it to an image
    
            Parameters:
                image_file (str): File path for where to store generated image
                
            Returns:
                image_file (str): Returns the same path after storing data in it
    
    '''

    view = omui.M3dView.active3dView()
    image = om.MImage()
    view.readColorBuffer(image, True)
    image.writeToFile(image_file)
    return image_file


def capture_viewport_playblast(image_file): 
    ''' 
    Takes a snapshot of the active viewport and writes it to an image
    
            Parameters:
                image_file (str): File path for where to store generated image
                
            Returns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    current_image_format = cmds.getAttr ("defaultRenderGlobals.imageFormat")
    cmds.setAttr ("defaultRenderGlobals.imageFormat", 8)
    cmds.playblast (st=True, et=True, v=0, fmt="image", qlt=100, p=100, w=1920, h=1080, fp=0, cf=image_file)
    cmds.setAttr ("defaultRenderGlobals.imageFormat", current_image_format)
    return image_file
    

def discord_post_message(username, message, webhook_url):
    '''
    Sends a string message to Discord using a webhook
    
            Parameters:
                username (str): A string to be used as the username (Replaces bot name)
                message (str): A string to be used as a message
                webhook_url (str): A Discord Webhook to make the request
                
            Returns:
                response (dict): Returns the response generated by the http object
                
    ''' 
    if python_version == 3:
        bot_message = {
                'username': username,
                'content': message
                } 

        host, path = parse_discord_api(webhook_url)
        connection = http.client.HTTPSConnection(host)
        connection.request('POST', path, headers={'Content-Type': 'application/json; charset=UTF-8', 'User-Agent' : 'gt_maya_to_discord/' + str(script_version)} , body=dumps(bot_message))
        response = connection.getresponse()
        return tuple([response])
    else:
        bot_message = {
        'username': username,
        'content': message
        } 

        message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

        http_obj = Http()

        response = http_obj.request(
            uri=webhook_url,
            method='POST',
            headers=message_headers,
            body=dumps(bot_message),
        )
        return response
        

def encode_multipart(fields, files, boundary=None):
    '''
    Encode dict of form fields and dict of files as multipart/form-data.
    Return tuple of (body_string, headers_dict). Each value in files is a dict
    with required keys 'filename' and 'content', and optional 'mimetype' (if
    not specified, tries to guess mime type or uses 'application/octet-stream').

    >>> body, headers = encode_multipart({'FIELD': 'VALUE'},
    ...                                  {'FILE': {'filename': 'F.TXT', 'content': 'CONTENT'}},
    ...                                  boundary='BOUNDARY')
    >>> print('\n'.join(repr(l) for l in body.split('\r\n')))
    '--BOUNDARY'
    'Content-Disposition: form-data; name="FIELD"'
    ''
    'VALUE'
    '--BOUNDARY'
    'Content-Disposition: form-data; name="FILE"; filename="F.TXT"'
    'Content-Type: text/plain'
    ''
    'CONTENT'
    '--BOUNDARY--'
    ''
    '''
    def escape_quote(s):
        return s.replace('"', '\\"')

    if boundary is None:
        boundary = ''.join(random.choice(_BOUNDARY_CHARS) for i in range(30))
    lines = []

    for name, value in fields.items():
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)),
            '',
            str(value),
        ))

    for name, value in files.items():
        filename = value['filename']
        if 'mimetype' in value:
            mimetype = value['mimetype']
        else:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(
                    escape_quote(name), escape_quote(filename)),
            'Content-Type: {0}'.format(mimetype),
            '',
            value['content'],
        ))

    lines.extend((
        '--{0}--'.format(boundary),
        '',
    ))
    
    
    clean_lines = [] # Only Bytes
    for line in lines:
        if type(line) == bytes:
            clean_lines.append(line)
        else:
            clean_lines.append(bytes(line, 'utf-8'))

    body = b'\r\n'.join(clean_lines)


    headers = {
        'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
        'Content-Length': str(len(body)),
    }

    return (body, headers)
    

def discord_post_attachment(username, message, file_path, webhook_url):
    '''
    Sends a message and an attachment to Discord using a webhook
  
            Parameters:
                username (str): A string to be used as the username (replaces bot name)
                message (str): A string to be used as a message
                file_path (str): A path for a file that will be uploaded
                webhook_url (str): A Discord Webhook to make the request
                
            Returns:
                response (dict): Returns the response generated by the http object
                
    '''
    if python_version == 3:
        fields = { 'content' : message, 'username' : username}
        file_name = file_path.split('/')[-1]
        files = {'file1': {'filename': file_name, 'content': open(file_path, "rb").read()}}
        data, headers = encode_multipart(fields, files)

        host, path = parse_discord_api(webhook_url)
        connection = http.client.HTTPSConnection(host)
        connection.request('POST', path, headers=headers , body=data)
        response = connection.getresponse()
        return tuple([response])
    else:
        fields = { 'content' : message, 'username' : username}
        file_name = file_path.split('/')[-1]
        files = {'file1': {'filename': file_name, 'content': open(file_path, "rb").read()}}
        data, headers = encode_multipart(fields, files)
        
        http_obj = Http()

        response = http_obj.request(
            uri=webhook_url,
            method='POST',
            headers=headers,
            body=data
        )

    return response
    
def capture_playblast_animation(video_file, scale_pct, compression, video_format): 
    ''' 
    Records a playblast and returns its path.
    It also prints the size of the file to the active viewport as a heads up message (cmds.inViewMessage)
            
            Parameters:
                video_file (str): A path for the file that will be generated (playblast file)
                scale_pct (int): Int to determine the scale of the playblast image (percentage)
                compression (str): Compression used for the playblast
                video_format (str): One of the three formats used by cmds.playblast to record a playblast
                
            Returns:
                playblast (str): Returns the path for the generated video file
    '''
         
    playblast = cmds.playblast( p=scale_pct, f=video_file, compression=compression, format=video_format ,forceOverwrite=True, v=False)
    file_size = os.path.getsize(playblast)
    active_viewport_height = omui.M3dView.active3dView().portHeight()
    #cmds.headsUpMessage( 'Playblast File Size: ' + str(round(file_size / (1024 * 1024), 3)) + ' Megabytes. (More information in the script editor)', verticalOffset=active_viewport_height*-0.45 , time=5.0)
    message = '<span style=\"color:#FFFFFF;\">Playblast File Size:</span> <span style=\"color:#FF0000;text-decoration:underline;\">' + get_readable_size(file_size, precision=2) + '</span>'
    if gt_mtod_settings.get('feedback_visibility'):
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        cmds.inViewMessage(amg='<span style=\"color:#FFFFFF;\">Open the the script editor for more information', pos='botLeft', fade=True, alpha=.9)
    print('#' * 80)
    print('Recorded Playblast:')
    print('Video Scale: ' + str(scale_pct) + '%')
    print('Compression: ' + compression)
    print('OutputType: ' + video_format)
    print('File path: ' + playblast)
    print('File size in bytes: ' + str(file_size))
    print('File size: ' + get_readable_size(file_size, precision=2))
    print('#' * 80)
    return playblast


def get_available_playblast_compressions(format):
        return mel.eval('playblast -format "{0}" -q -compression;'.format(format))

def update_discord_webhook_validity(webhook_url):
    '''
    Updates Validity of a webhook for when running the script again a second time.
    This function updates the "settings" dictionary directly.
    
            Parameters:
                webhook_url (str): Discord Webhook URL
    
    '''
    success_codes = [200, 201, 202, 203, 204, 205, 206]
    if python_version == 3:
        try: 
            host, path = parse_discord_api(webhook_url)
            connection = http.client.HTTPSConnection(host)
            connection.request('GET', path, headers={'Content-Type': 'application/json; charset=UTF-8', 'User-Agent' : 'gt_maya_to_discord/' + str(script_version)})
            response = connection.getresponse()
            response_content_dict = loads(response.read())
            if response.status in success_codes: 
                response_content_dict.get('name')
                gt_mtod_settings['is_new_instance'] = False
                gt_mtod_settings['is_webhook_valid'] = True
            else:
                gt_mtod_settings['is_new_instance'] = False
                gt_mtod_settings['is_webhook_valid'] = False 
        except:
            gt_mtod_settings['is_new_instance'] = False
            gt_mtod_settings['is_webhook_valid'] = False 
    else:
        try: 
            http_obj = Http()
            response, content = http_obj.request(webhook_url)

            if response.status in success_codes: 
                response_content_dict = loads(content)
                response_content_dict.get('name')
                gt_mtod_settings['is_new_instance'] = False
                gt_mtod_settings['is_webhook_valid'] = True 
            else:
                gt_mtod_settings['is_new_instance'] = False
                gt_mtod_settings['is_webhook_valid'] = False 
        except:
            gt_mtod_settings['is_new_instance'] = False
            gt_mtod_settings['is_webhook_valid'] = False 
        

def discord_get_webhook_name(webhook_url):
    '''
    Requests the name of the webhook and returns a string representing it
    
            Parameters:
                webhook_url (str): Discord Webhook URL
                
            Returns:
                name (str): The name of the webhook (or error string, if operation failed)
    '''
    success_codes = [200, 201, 202, 203, 204, 205, 206]
    if python_version == 3:
        try: 
            host, path = parse_discord_api(webhook_url)
            connection = http.client.HTTPSConnection(host)
            connection.request('GET', path, headers={'Content-Type': 'application/json; charset=UTF-8', 'User-Agent' : 'gt_maya_to_discord/' + str(script_version)})
            response = connection.getresponse()
            response_content_dict = loads(response.read())
            if response.status in success_codes: 
                return response_content_dict.get('name')
            else:
                return 'Error reading webhook response'
        except:
            cmds.warning('Error connecting to provided webhook. Make sure you\'re pasting the correct URL')
            return 'Error connecting to webhook'
    else:
        try: 
            http_obj = Http()
            response, content = http_obj.request(webhook_url)
            if response.status in success_codes: 
                response_content_dict = loads(content) 
                return response_content_dict.get('name')
            else:
                return 'Error reading webhook response'
        except:
            cmds.warning('Error connecting to provided webhook. Make sure you\'re pasting the correct URL')
            return 'Error connecting to webhook'

def get_readable_size(size, precision=2):
    ''' 
    Returns a human redable version of the size of a file 
    
            Parameters:
                size (float or int) : size of the file in bytes
                precision (int) : precision of the returned result
                    
            Returns:
                formated_string (string) : Size + Suffix
                
    '''
    suffixes=['B','KB','MB','GB','TB']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        size = size/1024.0
    return "%.*f%s"%(precision, size, suffixes[suffix_index])
    
    
def response_inview_feedback(operation_name, response, write_output=True, display_inview=True):
    '''
    Prints an inViewMessage to give feedback to the user about what is being executed.
    Uses the module "random" to force identical messages to appear at the same time.

            Parameters:
                    operation_name (string): name of the operation being display (e.g. playblast)
                    response (dict): A dictionary response received from a HTTP object after post/get operation.
                    write_output (bool): Determines if the functions will write an extra output text (Like a "Result: pCube1" text output)
                    display_inview (bool): Determines if generated message will be displayed as an inView message or not (visibility)
    '''

    message = '<' + str(random.random()) + '>'
            
    if len(response) >= 1:
        status_value = response[0].status
        reason_value = response[0].reason
        success_codes = [200, 201, 202, 203, 204, 205, 206]

        if status_value in success_codes: 
            message += 'The ' + str(operation_name) + ' was <span style=\"color:#00FF00;text-decoration:underline;\">sent successfully</span>.'
            if write_output:
                sys.stdout.write('The ' + str(operation_name) + ' was sent successfully.  Web response: ' + str(reason_value) + ' (' + str(status_value) + ')')
        else: # Error
            message += 'The ' + str(operation_name) + ' was <span style=\"color:#FF0000;text-decoration:underline;\">not sent.'
            if write_output:
                sys.stdout.write('The ' + str(operation_name) + ' was sent.  Web response: ' + str(reason_value) + ' (' + str(status_value) + ')')
    else :
        message += 'The ' + str(operation_name) + ' was <span style=\"color:#FF0000;text-decoration:underline;\">not sent.'
        if write_output:
            sys.stdout.write('The ' + str(operation_name) + ' was not sent.  Error: Web responsed can\'t be read.')
     
    if display_inview:
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


#Get Settings & Build GUI
get_persistent_settings_maya_to_discord()
if __name__ == '__main__':
    build_gui_maya_to_discord()