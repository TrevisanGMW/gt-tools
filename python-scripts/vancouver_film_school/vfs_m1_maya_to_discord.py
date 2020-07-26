"""
 This is a modified version of my script "GT Maya to Discord" for Modeling 1 students to quickly share their work on Discord.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-07-26 - github.com/TrevisanGMW
 Tested on Maya 2018, 2019, 2020 - Windows 10
   
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
import os
from json import dumps
from json import loads
from httplib2 import Http


# Forced Webhook
hard_coded_webhook = 'https://discordapp.com/api/webhooks/734789179044790322/fvOuKv1FE2kFTU1ia7otyJUhhZKSvHgMkAuoULZ3RsPXwqImCWkIK9JYL0CLsP_B_Vm8'
hard_coded_webhook_name = '3D147 - Q&A'

# Script Name
script_name = "Mod 1 -  Maya to Discord"

# Versions:
script_version = "1.0"
maya_version = cmds.about(version=True)

# Used to define multipart/form-data boundary
_BOUNDARY_CHARS = string.digits + string.ascii_letters


# Settings
settings = { 'discord_webhook': hard_coded_webhook,
             'discord_webhook_name'  : '',
             'is_first_time_running' : False,
             'custom_username' : '',
             'image_format' : 'jpg',
             'video_format' : 'mov', 
             'video_scale_pct' : 40, 
             'video_compression' : 'Animation', 
             'video_output_type' : 'qt',
             'is_new_instance' : True,
             'is_webhook_valid' : False }

# Default Settings (Deep Copy)
settings_default = copy.deepcopy(settings)   


def get_persistent_settings_maya_to_discord():
    ''' 
    Checks if persistant settings for GT Maya to Discord exists and transfer them to the settings dictionary.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    
    # Check if there is anything stored
    stored_webhook_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_webhook"))
    stored_webhook_name_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_webhook_name"))
    stored_custom_username_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_custom_username"))
    
    stored_image_format_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_image_format"))
    stored_video_format_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_video_format"))
    
    stored_video_scale_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_video_scale"))
    stored_video_compression_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_video_compression"))
    stored_video_output_type_exists = cmds.optionVar(exists=("gt_m1_maya_to_discord_video_output_type"))
    
    # Discord Settings
    if stored_webhook_exists:  
        settings['discord_webhook'] = hard_coded_webhook # MODIFIED
        
        if stored_webhook_name_exists and str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook_name"))) != '':
            settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook_name")))
    else:
        settings['is_first_time_running'] = True
   
    if stored_custom_username_exists:  
        settings['custom_username'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_custom_username")))
    else:
        settings['custom_username'] = ''
        
    # Image Settings
    if stored_image_format_exists:
        settings['image_format'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_image_format")))
    

    # Playblast Settings
    if stored_image_format_exists:
        settings['video_format'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_format")))

    if stored_video_scale_exists:
        settings['video_scale_pct'] = int(cmds.optionVar(q=("gt_m1_maya_to_discord_video_scale")))

    if stored_video_compression_exists:
        settings['video_compression'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_compression")))
        
    if stored_video_output_type_exists:
        settings['video_output_type'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_output_type")))



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

    cmds.optionVar( sv=('gt_m1_maya_to_discord_custom_username', custom_username) )
    settings['custom_username'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_custom_username")))

    if webhook != '':  
        cmds.optionVar( sv=('gt_m1_maya_to_discord_webhook', webhook) )
        settings['discord_webhook'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook")))
        
        response = discord_get_webhook_name(webhook)
        cmds.optionVar( sv=('gt_m1_maya_to_discord_webhook_name', response) )
        settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook_name")))
          
    else:
        cmds.optionVar( sv=('gt_m1_maya_to_discord_webhook', webhook) )
        settings['discord_webhook'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook")))
        
        cmds.optionVar( sv=('gt_m1_maya_to_discord_webhook_name', 'Missing Webhook') )
        settings['discord_webhook_name'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_webhook_name")))
        
        cmds.warning('Webhook not provided. Please update your settings if you want your script to work properly.')
        
    if image_format != '':
        cmds.optionVar( sv=('gt_m1_maya_to_discord_image_format', image_format) )
        settings['image_format'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_image_format")))
    
    if image_format != '':
        cmds.optionVar( sv=('gt_m1_maya_to_discord_video_format', video_format) )
        settings['video_format'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_format")))
        
    if video_scale >= 1 and video_scale <= 100:
        cmds.optionVar( sv=('gt_m1_maya_to_discord_video_scale', video_scale) )
        settings['video_scale_pct'] = int(cmds.optionVar(q=("gt_m1_maya_to_discord_video_scale")))
    else:
        cmds.warning('Video scale needs to be a percentage between 1 and 100.  Provided value was ignored')
        
    if video_compression != '':
        cmds.optionVar( sv=('gt_m1_maya_to_discord_video_compression', video_compression) )
        settings['video_compression'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_compression")))
        
    if video_output_type != '':
        cmds.optionVar( sv=('gt_m1_maya_to_discord_video_output_type', video_output_type) )
        settings['video_output_type'] = str(cmds.optionVar(q=("gt_m1_maya_to_discord_video_output_type")))
        
        
def reset_persistent_settings_maya_to_discord():
    ''' Resets persistant settings for GT Maya to Discord '''
    cmds.optionVar( remove='gt_m1_maya_to_discord_webhook' )
    cmds.optionVar( remove='gt_m1_maya_to_discord_webhook_name' )
    cmds.optionVar( remove='gt_m1_maya_to_discord_custom_username' )
    cmds.optionVar( remove='is_first_time_running' )
    cmds.optionVar( remove='gt_m1_maya_to_discord_video_format' )
    cmds.optionVar( remove='gt_m1_maya_to_discord_image_format' )
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
    build_gui_maya_to_discord = cmds.window(window_name, title=' ' + script_name + " - v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=4, cw=[(1, 10), (2, 150), (3, 60),(4, 40)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Settings", bgc=(0, .5, 0), c=lambda x:build_gui_m1_settings_maya_to_discord())
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_m1_help_maya_to_discord())
    cmds.separator(h=5, style='none') # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    

    header_image_dir = cmds.internalVar(userBitmapsDir=True) 
    header_image = header_image_dir + 'gt_m1_maya_to_discord_header.png'
    
    if os.path.isdir(header_image_dir) and os.path.exists(header_image) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAAQQAAABkCAYAAABgi07kAAAACXBIWXMAAAsTAAALEwEAmpwYAAAJTmlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiIHhtbG5zOnN0UmVmPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VSZWYjIiB4bWxuczpwaG90b3Nob3A9Imh0dHA6Ly9ucy5hZG9iZS5jb20vcGhvdG9zaG9wLzEuMC8iIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiB4bXA6Q3JlYXRlRGF0ZT0iMjAyMC0wNy0wN1QxNTo1NzoyNS0wNzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0wNy0wN1QxNTo1ODoyNi0wNzowMCIgeG1wOk1vZGlmeURhdGU9IjIwMjAtMDctMDdUMTU6NTg6MjYtMDc6MDAiIGRjOmZvcm1hdD0iaW1hZ2UvcG5nIiB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOmNkNjc1YmFlLWQ3MmYtNjM0My04MzZlLTMzMzRjZjI2ZTAzNyIgeG1wTU06RG9jdW1lbnRJRD0iYWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOmIyNTQ5MDE0LWYxYWItNzQ0Yi05NmMxLTI1ZTJmY2E1ZGUzOCIgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOmIxMTNhOWJmLTA3OTAtNGU0ZS1hM2U5LTlhOWQxMTQ4M2U3ZCIgcGhvdG9zaG9wOkNvbG9yTW9kZT0iMyIgcGhvdG9zaG9wOklDQ1Byb2ZpbGU9InNSR0IgSUVDNjE5NjYtMi4xIj4gPHhtcE1NOkhpc3Rvcnk+IDxyZGY6U2VxPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iY3JlYXRlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpiMTEzYTliZi0wNzkwLTRlNGUtYTNlOS05YTlkMTE0ODNlN2QiIHN0RXZ0OndoZW49IjIwMjAtMDctMDdUMTU6NTc6MjUtMDc6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6M2Q3OTM5NDktNjE1My0yMzQwLTk3YjktMjhiYjQ3MmJkMzcwIiBzdEV2dDp3aGVuPSIyMDIwLTA3LTA3VDE1OjU4OjI2LTA3OjAwIiBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249ImNvbnZlcnRlZCIgc3RFdnQ6cGFyYW1ldGVycz0iZnJvbSBhcHBsaWNhdGlvbi92bmQuYWRvYmUucGhvdG9zaG9wIHRvIGltYWdlL3BuZyIvPiA8cmRmOmxpIHN0RXZ0OmFjdGlvbj0iZGVyaXZlZCIgc3RFdnQ6cGFyYW1ldGVycz0iY29udmVydGVkIGZyb20gYXBwbGljYXRpb24vdm5kLmFkb2JlLnBob3Rvc2hvcCB0byBpbWFnZS9wbmciLz4gPHJkZjpsaSBzdEV2dDphY3Rpb249InNhdmVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmNkNjc1YmFlLWQ3MmYtNjM0My04MzZlLTMzMzRjZjI2ZTAzNyIgc3RFdnQ6d2hlbj0iMjAyMC0wNy0wN1QxNTo1ODoyNi0wNzowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIiBzdEV2dDpjaGFuZ2VkPSIvIi8+IDwvcmRmOlNlcT4gPC94bXBNTTpIaXN0b3J5PiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDozZDc5Mzk0OS02MTUzLTIzNDAtOTdiOS0yOGJiNDcyYmQzNzAiIHN0UmVmOmRvY3VtZW50SUQ9InhtcC5kaWQ6YjExM2E5YmYtMDc5MC00ZTRlLWEzZTktOWE5ZDExNDgzZTdkIiBzdFJlZjpvcmlnaW5hbERvY3VtZW50SUQ9InhtcC5kaWQ6YjExM2E5YmYtMDc5MC00ZTRlLWEzZTktOWE5ZDExNDgzZTdkIi8+IDxwaG90b3Nob3A6RG9jdW1lbnRBbmNlc3RvcnM+IDxyZGY6QmFnPiA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo3MWM4MWE0Zi0xMDFlLTRjNGQtYWM2Zi03N2JiMjY2MmNlNDM8L3JkZjpsaT4gPC9yZGY6QmFnPiA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz5zwoMaAAA1UklEQVR4nO29d5xkV33m/T3nhsqde0JPnpE0kkYZSUhCIIEELEiEBWPCggEbMP5gMDYvYGOvbYxZ27DeJb3va/ziNWYJAgOGJYsoQIGghKSZkSZPd0/nru7qivfec877x7m3umYkjWakqe4eqR59rqa66oZzq/s89xefI4wxdNBBBx0AyOUeQAcddLBy0CGEDjrooIkOIXTQQQdNdAihgw46aKJDCB100EETHULooIMOmugQQgcddNBEhxA66KCDJjqE0EEHHTTRIYQOOuigiQ4hdNBBB0247b7ARKUyaowptPs6pwkW1hYK65Z7EE8GfOhT2gGuBM4E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'
        image_64_decode = base64.decodestring(image_enconded)
        image_result = open(header_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()

    icon_image_dir = cmds.internalVar(userBitmapsDir=True) 
    icon_image = icon_image_dir + 'gt_m1_maya_to_discord_icon.png'
    
    if os.path.isdir(icon_image_dir) == False:
        icon_image = ':/camera.open.svg'
    
    if os.path.isdir(icon_image_dir) and os.path.exists(icon_image) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTA3LTA1VDE5OjU2OjQwLTA3OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDpkNjdiM2JkNy1iMjk3LWI3NDItOTNkOC0wYTYyZjZhYzUzMmYiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplOTM5YzQ0Yi1lNjdkLWJjNGMtYWMyZS00YmY3ZjcwYzgzODAiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5MzljNDRiLWU2N2QtYmM0Yy1hYzJlLTRiZjdmNzBjODM4MCIgc3RFdnQ6d2hlbj0iMjAyMC0wNy0wNVQxOTo1Njo0MC0wNzowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHN0RXZ0OndoZW49IjIwMjAtMDctMDdUMTU6MjU6MjktMDc6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7Q7fCFAAAIwklEQVR4nO3bf6xlVXUH8M/a5755w/BDfmaYCunAkyq22hFQbClia1sZMBicaIc2bWJqajQpwR9pY6TYKkk1jiBNbZpQq40mVCI60USjERqIP+LQoQRSx6hjfxEjTQpl+DXMu3cv/zjn3nnvdWbefe/O64Uw32TlnZx7ztrfvc7aa+299n6RmZ7PKNMmMG0cM8C0CUwbxwwwbQLTxjEDTJvAtPG8N0Dvpk8v/1AmOUBQGhI5TwZlFgOikuEkXCRskd6LH0f6taGe2iCJbHXp5mAR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'
        image_64_decode = base64.decodestring(image_enconded)
        image_result = open(icon_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
    
    cmds.image(image = header_image)
    
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
    
    
    if settings['is_first_time_running'] == True:
        cmds.text(webhook_name_text, e=True, l=hard_coded_webhook_name)#, bgc= [1,1,0]) # MODIFIED
    else:
        if 'Error' in settings.get('discord_webhook_name') or 'Missing Webhook' in settings.get('discord_webhook_name'):
            cmds.text(webhook_name_text, e=True, l=settings.get('discord_webhook_name'), bgc=[.5,0,0])
        else:
            cmds.text(webhook_name_text, e=True, l=settings.get('discord_webhook_name'), nbg=True)
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main) 
    cmds.separator(h=7, style='none') # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.button(l ="Send Entire Desktop", bgc=(.6, .8, .6), c=lambda x:send_dekstop_screenshot())  
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button(l ="Send Maya Window", bgc=(.6, .8, .6), c=lambda x:send_maya_window())   
    cmds.separator(h=5, style='none') # Empty Space   
    cmds.button(l ="Send Viewport", bgc=(.6, .8, .6), c=lambda x:send_viewport_only())                                                                                             
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button(l ="Send Playblast", bgc=(.6, .8, .6), c=lambda x:send_animated_playblast())                                                                                                                                                                                      
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
        if settings.get('custom_username') == '':
            user_name = socket.gethostname()
        else:
            user_name = settings.get('custom_username') + ' (' + socket.gethostname() + ')'

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

    # Button Functions ----------
    webhook_error_message = 'Sorry, something went wrong. Please review your webhook and settings.'
    def send_dekstop_screenshot():
        ''' Attempts to send a desktop screenshot using current settings '''
        if settings.get('is_new_instance'):
            update_discord_webhook_validity(settings.get('discord_webhook'))
        
        if settings.get('is_webhook_valid'):
            try:
                update_text_status()
                temp_path = generate_temp_file(settings.get('image_format'))
                temp_desktop_ss_file = capture_desktop_screenshot(temp_path)
                upload_message = get_date_time_message()
                def threaded_upload():
                    try:
                        response = discord_post_attachment(get_username(), upload_message, temp_desktop_ss_file, settings.get('discord_webhook'))
                        utils.executeDeferred(parse_sending_response, response)
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
        if settings.get('is_new_instance'):
            update_discord_webhook_validity(settings.get('discord_webhook'))
        
        if settings.get('is_webhook_valid'):
            try:  
                update_text_status()
                temp_path = generate_temp_file(settings.get('image_format'))
                temp_img_file = capture_app_window(temp_path)
                upload_message = get_date_time_message()                   
                def threaded_upload():
                    try:
                        response = discord_post_attachment(get_username(), upload_message, temp_img_file, settings.get('discord_webhook'))
                        utils.executeDeferred(parse_sending_response, response)
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
        if settings.get('is_new_instance'):
            update_discord_webhook_validity(settings.get('discord_webhook'))
            
        if settings.get('is_webhook_valid'):
            try:
                update_text_status()
                temp_path = generate_temp_file(settings.get('image_format'))
                if maya_version in ['2017','2018','2019']:
                    temp_img_file = capture_viewport_playblast(temp_path)
                else:
                    temp_img_file = capture_viewport(temp_path)
                upload_message = get_date_time_message()
                
                def threaded_upload():
                    try:
                        response = discord_post_attachment(get_username(), upload_message, temp_img_file, settings.get('discord_webhook'))
                        utils.executeDeferred(parse_sending_response, response)
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
        if settings.get('is_new_instance'):
            update_discord_webhook_validity(settings.get('discord_webhook'))
        
        if settings.get('is_webhook_valid'):
            try:
                update_text_status()
                current_scene_name = cmds.file(q=True, sn=True).split('/')[-1]
                if current_scene_name == '': # If not saved
                    current_scene_name ='never_saved_untitled_scene'
                else:
                    if current_scene_name.endswith('.ma') or current_scene_name.endswith('.mb'):
                        current_scene_name=current_scene_name[:-3]

                temp_path = generate_temp_file( settings.get('video_format'), file_name=current_scene_name)
                temp_playblast_file = capture_playblast_animation(temp_path, settings.get('video_scale_pct'), settings.get('video_compression'), settings.get('video_output_type') )
                upload_message = get_date_time_message()
                
                def threaded_upload():
                    try:
                        response = discord_post_attachment(get_username(), upload_message, temp_playblast_file, settings.get('discord_webhook'))
                        utils.executeDeferred(parse_sending_response, response)
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


    # Show and Lock Window
    cmds.showWindow(build_gui_maya_to_discord)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(icon_image)
    
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================

# Creates Help GUI
def build_gui_m1_help_maya_to_discord():
    ''' Builds the Help UI for GT Maya to Discord '''
    window_name = "build_gui_m1_help_maya_to_discord"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Help", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
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
    cmds.text(l='Send Entire Desktop: Sends a screenshot of your desktop.', align="center", font=help_font)
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
    cmds.separator(h=10, style='none') # Empty Space
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
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)




def build_gui_m1_settings_maya_to_discord():
    ''' Builds the Settings UI for GT Maya to Discord '''
    window_name = "build_gui_m1_settings_maya_to_discord"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Settings", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])


    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Settings", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space
    
    
    # Current Settings =================
    
    current_image_format = settings.get('image_format')
    current_video_format = settings.get('video_format')
    current_webhook = ''
    current_custom_username = ''
    if not settings.get('is_first_time_running'):
        if settings.get('discord_webhook') != '':
            current_webhook = settings.get('discord_webhook')
        if settings.get('custom_username') != '':
            current_custom_username = settings.get('custom_username')
    current_video_scale = settings.get('video_scale_pct')
    current_compression = settings.get('video_compression')
    current_output_type = settings.get('video_output_type')
    
    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column) 
    
    cmds.text(l='Discord Webhook URL', align="center")
    cmds.separator(h=5, style='none') # Empty Space
    new_webhook_input = cmds.textField(pht=hard_coded_webhook, en=False, text=hard_coded_webhook, font= 'smallPlainLabelFont')
    
    
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
     
    
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    
    # Bottom Buttons
    cmds.rowColumnLayout(nc=2, cw=[(1, 145),(2, 145)], cs=[(1,10),(2,10)], p=main_column)
    cmds.button(l='Reset Settings', h=30, c=lambda args: reset_settings())
    cmds.button(l='Reset Webhook', en=False, c=lambda args: cmds.textField(new_webhook_input, e=True, text=''))
    cmds.separator(h=5, style='none')
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.button(l='Apply', h=30, bgc=(.6, .8, .6), c=lambda args: apply_settings())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
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
        
        cmds.textField(new_username_input, e=True, text=settings_default.get('custom_username'))
        cmds.textField(new_image_format_input, e=True, text=settings_default.get('image_format'))
        cmds.textField(new_video_format_input, e=True, text=settings_default.get('video_format') )
        
        for idx,obj in enumerate(cmds.optionMenu(output_type_input,q=True, itemListLong=True)):
            if cmds.menuItem( obj , q=True, label=True ) == settings_default.get('video_output_type'):
                cmds.optionMenu(output_type_input, e=True, select=idx+1)
        
        update_available_compressions()
    
        found_default = False
        for idx,obj in enumerate(cmds.optionMenu(compression_input, q=True, itemListLong=True)):
            if cmds.menuItem( obj , q=True, label=True ) == settings_default.get('video_compression'):
                cmds.optionMenu(compression_input, e=True, select=idx+1)
                found_default = True
        
        if not found_default:
            cmds.menuItem( label='none', p=compression_input )
            
        cmds.intSliderGrp(video_scale_input, e=True, value=settings_default.get('video_scale_pct'))
                
        
    def apply_settings():
        ''' Transfer new settings to variables and store them as persistent settings '''
        set_persistent_settings_maya_to_discord(cmds.textField(new_username_input, q=True, text=True), cmds.textField(new_webhook_input, q=True, text=True),\
                                                cmds.textField(new_image_format_input, q=True, text=True), cmds.textField(new_video_format_input, q=True, text=True),\
                                                cmds.intSliderGrp(video_scale_input, q=True, value=True), cmds.optionMenu(compression_input, q=True, value=True),\
                                                cmds.optionMenu(output_type_input, q=True, value=True))
        settings['is_first_time_running'] = False
        settings['is_new_instance'] = True
        
        build_gui_maya_to_discord()
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)



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
                
            Retruns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    app = QtWidgets.QApplication.instance()
    win_id = app.desktop().winId()
    long_win_id = long(win_id)
    frame = QtGui.QPixmap.grabWindow(long_win_id)
    frame.save(image_file)
    return image_file


def capture_app_window(image_file):
    ''' 
    Takes a snapshot of the entire Qt App (Maya) and writes it to an image
    
            Parameters:
                image_file (str): File path for where to store generated image
                
            Retruns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    win = omui.MQtUtil_mainWindow()
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
                
            Retruns:
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
                
            Retruns:
                image_file (str): Returns the same path after storing data in it
    
    '''
    current_image_format = cmds.getAttr ("defaultRenderGlobals.imageFormat")
    cmds.setAttr ("defaultRenderGlobals.imageFormat", 8)
    cmds.playblast (st=True, et=True, v=0, fmt="image", qlt=100, p=100, w=1920, h=1080, fp=0, cf=image_file)
    cmds.setAttr ("defaultRenderGlobals.imageFormat", current_image_format)
    return image_file
    


def discord_post_message(message, webhook_url):
    '''
    Sends a string message to Discord using a webhook
    
            Parameters:
                message (str): A string to be used as a message
                webhook_url (str): A Discord Webhook to make the request
                
            Retruns:
                response (dict): Returns the response generated by the http object
                
    '''
    bot_message = {
        'content' : message }

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
    body = '\r\n'.join(lines)

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
                
            Retruns:
                response (dict): Returns the response generated by the http object
                
    '''
    
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
    It also prints the size of the file to the active viewport as a heads up message (cmds.headsUpMessage).
            
            Parameters:
                video_file (str): A path for the file that will be generated (playblast file)
                scale_pct (int): Int to determine the scale of the playblast image (percentage)
                compression (str): Compression used for the playblast
                video_format (str): One of the three formats used by cmds.playblast to record a playblast
                
            Retruns:
                playblast (str): Returns the path for the generated video file
    '''
         
    playblast = cmds.playblast( p=scale_pct, f=video_file, compression=compression, format=video_format ,forceOverwrite=True, v=False)
    file_size = os.path.getsize(playblast)
    active_viewport_height = omui.M3dView.active3dView().portHeight()
    cmds.headsUpMessage( 'Playblast File Size: ' + str(round(file_size / (1024 * 1024), 3)) + ' Megabytes. (More information in the script editor)', verticalOffset=active_viewport_height*-0.45 , time=5.0)
    print('#' * 80)
    print('Recorded Playblast:')
    print('Video Scale: ' + str(scale_pct) + '%')
    print('Compression: ' + compression)
    print('OutputType: ' + video_format)
    print('File path: ' + playblast)
    print('File size in bytes: ' + str(file_size))
    print('File size in megabytes: ' + str(round(file_size / (1024 * 1024), 3)))
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
    try: 
        http_obj = Http()
        response, content = http_obj.request(webhook_url)

        success_codes = [200, 201, 202, 203, 204, 205, 206]
        if response.status in success_codes: 
            #response_content_dict = eval(content)
            response_content_dict = loads(content)
            response_content_dict.get('name')
            settings['is_new_instance'] = False
            settings['is_webhook_valid'] = True 
        else:
            settings['is_new_instance'] = False
            settings['is_webhook_valid'] = False 
    except:
        settings['is_new_instance'] = False
        settings['is_webhook_valid'] = False 
        

def discord_get_webhook_name(webhook_url):
    '''
    Requests the name of the webhook and returns a string representing it
    
            Parameters:
                webhook_url (str): Discord Webhook URL
                
            Returns:
                name (str): The name of the webhook (or error string, if operation failed)
    '''
    try: 
        http_obj = Http()
        response, content = http_obj.request(webhook_url)
        success_codes = [200, 201, 202, 203, 204, 205, 206]
        if response.status in success_codes: 
            response_content_dict = loads(content) 
            return response_content_dict.get('name')
        else:
            return 'Error reading webhook response'
    except:
        cmds.warning('Error connecting to provided webhook. Make sure you\'re pasting the correct URL')
        return 'Error connecting to webhook'


#Get Settings & Build GUI
get_persistent_settings_maya_to_discord()
build_gui_maya_to_discord()