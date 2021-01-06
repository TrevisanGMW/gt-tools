"""

 GT Auto Biped Rigger
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-12-08 - github.com/TrevisanGMW

 1.0 - 2020-12-29
 Initial Release
 
 1.1 - 2021-01-03
 Renamed shapes
 Added joint labelling
 Added icons to buttons
 Added curves (lines) between proxies
 Changed and added a few notes
 Added manip default to all controls
 Locked default channels for the main rig group
 Made rig setup elements visible after creation
 Updated stretchy system to avoid cycles or errors
 Updated stretchy system to account for any curvature
 Fixed possible scale cycle happening during control creation
 
 1.2 - 2021-01-04
 Changed stretchy system so it doesn't use floatConstant nodes
 Updated the import proxy function so it doesn't give an error when importing a different scale
 Added utility to automatically create and define a humanik character from the rig
 Added utility to toggle the visibility of all joint labels
 Created utility to add a seamless FK/IK switch script to the current shelf
 "followHip" (ankle proxies) attribute is not longer activated by default
 Fixed an issue where left arm ik would be generated with an offset in extreme angles
 
 To do:
    Add more roll joints
    Add utilities
        Convert rig to proxy
    Add option to auto create proxy geo
    Add option to colorize (or not) proxy and rig elements
    Add option to not include forearm/eyes in the skinning joints
    Create button to add a shelf button for an animation picker
    
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
from decimal import *
import maya.cmds as cmds
import maya.mel as mel
import random
import base64
import copy
import math
import json
import sys
import os


# Script Name
script_name = "GT Auto Biped Rigger"

# Version:
script_version = "1.2"

# General Vars
grp_suffix = 'grp'
jnt_suffix = 'jnt'
proxy_suffix = 'proxy'
ctrl_suffix = 'ctrl'
automation_suffix = 'automation'
multiply_suffix = 'multiply'
first_shape_suffix = '1st'
second_shape_suffix = '2nd'

# Loaded Elements Dictionary
gt_ab_settings = { # General Settings
                   'main_proxy_grp' : 'auto_biped_proxy' + '_' + grp_suffix,
                   # Center Elements
                   'main_crv' : 'root' + '_' + proxy_suffix,
                   'cog_proxy_crv' : 'cog' + '_' + proxy_suffix,
                   'spine01_proxy_crv' : 'spine01' + '_' + proxy_suffix,
                   'spine02_proxy_crv' : 'spine02' + '_' + proxy_suffix,
                   'spine03_proxy_crv' : 'spine03' + '_' + proxy_suffix,
                   'spine04_proxy_crv' : 'spine04' + '_' + proxy_suffix,
                   'neck_base_proxy_crv' : 'neckBase' + '_' + proxy_suffix,
                   'neck_mid_proxy_crv' : 'neckMid' + '_' + proxy_suffix,
                   'head_proxy_crv' : 'head' + '_' + proxy_suffix,
                   'head_end_proxy_crv' : 'head' + '_end' + proxy_suffix.capitalize(),
                   'jaw_proxy_crv' : 'jaw' + '_' + proxy_suffix,
                   'jaw_end_proxy_crv' : 'jaw' + '_end' + proxy_suffix.capitalize(),
                   'hip_proxy_crv' : 'hip' + '_' + proxy_suffix,
                   # Left Side Elements (No need for prefix, these are automatically added)
                   # Right Side Elements are auto populated, script copies from Left to Right
                   'left_eye_proxy_crv' : 'eye' + '_' + proxy_suffix,
                   'left_clavicle_proxy_crv' : 'clavicle' + '_' + proxy_suffix,
                   'left_shoulder_proxy_crv' : 'shoulder' + '_' + proxy_suffix,
                   'left_elbow_proxy_crv' : 'elbow' + '_' + proxy_suffix,
                   'left_wrist_proxy_crv' : 'wrist' + '_' + proxy_suffix,
                   'left_thumb01_proxy_crv' : 'thumb01' + '_' + proxy_suffix,
                   'left_thumb02_proxy_crv' : 'thumb02' + '_' + proxy_suffix,
                   'left_thumb03_proxy_crv' : 'thumb03' + '_' + proxy_suffix,
                   'left_thumb04_proxy_crv' : 'thumb04' + '_end' + proxy_suffix.capitalize(),
                   'left_index01_proxy_crv' : 'index01' + '_' + proxy_suffix,
                   'left_index02_proxy_crv' : 'index02' + '_' + proxy_suffix,
                   'left_index03_proxy_crv' : 'index03' + '_' + proxy_suffix,
                   'left_index04_proxy_crv' : 'index04' + '_end' + proxy_suffix.capitalize(),
                   'left_middle01_proxy_crv' : 'middle01' + '_' + proxy_suffix,
                   'left_middle02_proxy_crv' : 'middle02' + '_' + proxy_suffix,
                   'left_middle03_proxy_crv' : 'middle03' + '_' + proxy_suffix,
                   'left_middle04_proxy_crv' : 'middle04' + '_end' + proxy_suffix.capitalize(),
                   'left_ring01_proxy_crv' : 'ring01' + '_' + proxy_suffix,
                   'left_ring02_proxy_crv' : 'ring02' + '_' + proxy_suffix,
                   'left_ring03_proxy_crv' : 'ring03' + '_' + proxy_suffix,
                   'left_ring04_proxy_crv' : 'ring04' + '_end' + proxy_suffix.capitalize(),
                   'left_pinky01_proxy_crv' : 'pinky01' + '_' + proxy_suffix,
                   'left_pinky02_proxy_crv' : 'pinky02' + '_' + proxy_suffix,
                   'left_pinky03_proxy_crv' : 'pinky03' + '_' + proxy_suffix,
                   'left_pinky04_proxy_crv' : 'pinky04' + '_end' + proxy_suffix.capitalize(),
                   'left_hip_proxy_crv' : 'hip' + '_' + proxy_suffix,
                   'left_knee_proxy_crv' : 'knee' + '_' + proxy_suffix,
                   'left_ankle_proxy_crv' : 'ankle' + '_' + proxy_suffix,
                   'left_ball_proxy_crv' : 'ball' + '_' + proxy_suffix,
                   'left_toe_proxy_crv' : 'toe' + '_' + proxy_suffix,
                   'left_elbow_pv_dir' : 'elbow_proxy_poleVecDir', 
                   'left_elbow_dir_loc' : 'elbow_proxy_dirParent', 
                   'left_elbow_aim_loc' : 'elbow_proxy_dirAim',
                   'left_elbow_upvec_loc' : 'elbow_proxy_dirParentUp',
                   'left_elbow_divide_node' : 'elbowUp_divide',
                   'left_knee_pv_dir' : 'knee_proxy_poleVecDir',
                   'left_knee_dir_loc' : 'knee_proxy_dirParent',
                   'left_knee_aim_loc' : 'knee_proxy_dirAim',
                   'left_knee_upvec_loc' : 'knee_proxy_dirParentUp',
                   'left_knee_divide_node' : 'knee_divide',
                   'left_ball_pivot_grp' : 'ball_proxy_pivot' + grp_suffix.capitalize(),
                   'left_ankle_ik_reference' : 'ankleSwitch_loc',
                   'left_knee_ik_reference' : 'kneeSwitch_loc',
                   'left_elbow_ik_reference' : 'elbowSwitch_loc',
                 }

# Auto Populate Control Names (Copy from Left to Right) + Add prefixes
gt_ab_settings_list = list(gt_ab_settings)
for item in gt_ab_settings_list:
    if item.startswith('left_'):
        gt_ab_settings[item] = 'left_' + gt_ab_settings.get(item) # Add "left_" prefix
        gt_ab_settings[item.replace('left_', 'right_')] = gt_ab_settings.get(item).replace('left_', 'right_') # Add right copy

# Store Default Values
gt_ab_settings_default = copy.deepcopy(gt_ab_settings)

# Create Joints List
gt_ab_joints_default = {}
for obj in gt_ab_settings:
    if obj.endswith('_crv'):
        name = gt_ab_settings.get(obj).replace(proxy_suffix, jnt_suffix).replace('end' + proxy_suffix.capitalize(), 'end' + jnt_suffix.capitalize())
        gt_ab_joints_default[obj.replace('_crv','_' + jnt_suffix).replace('_proxy', '')] = name
gt_ab_joints_default['left_forearm_jnt'] = 'left_forearm_jnt'
gt_ab_joints_default['right_forearm_jnt'] = 'right_forearm_jnt'


# Main Dialog ============================================================================
def build_gui_auto_biped_rig():
    '''  Creates the main GUI for GT Auto Biped Rigger '''
    window_name = "build_gui_auto_biped_rig"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================

    build_gui_auto_biped_rig = cmds.window(window_name, title=script_name + "  (v" + script_version + ')',\
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
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_help_gui_auto_biped_rig())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space

    ######## Generate Images ########
    # Icon
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True) 
    
    # Create Proxy Icon
    create_proxy_btn_ico = icons_folder_dir + 'gt_abr_create_proxy.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(create_proxy_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNi4wLWMwMDIgNzkuMTY0NDg4LCAyMDIwLzA3LzEwLTIyOjA2OjUzICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjIuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTEyLTMwVDIyOjI4OjU0LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wMS0wM1QxMToxNDowOS0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wMS0wM1QxMToxNDowOS0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpjOTRkMjQ0MS03ZDAyLTZkNGUtOWE0OS1kNTBkMTQ1MTIyNWYiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDoxYmRjOTk2My1mNDQ2LTIwNDMtYTQzOS1kMjIzNDAyMGQxNjUiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo0Njk2OTYwMy1lMTc2LTQ0NDAtODAzMi1mMjk5NmY4YmQ4YTAiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjQ2OTY5NjAzLWUxNzYtNDQ0MC04MDMyLWYyOTk2ZjhiZDhhMCIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjoyODo1NC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpjOTRkMjQ0MS03ZDAyLTZkNGUtOWE0OS1kNTBkMTQ1MTIyNWYiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6MTQ6MDktMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz66Y+ZhAAACHElEQVRYhcWXsUtWURjGfwZBOZjQUNicBRKCg9QkWq7fVJNrIDgoGGLiHDmKi8bX0tBUf0MgDbm5CkKDUC0ltGQg9Gu4762bXa/3ds9HLxzO/c77Pt/znPOec+97UEnUzqub/mnv1U4Vrk8lgV0E9oFrwGvgHXAJeAgMASvAWiky0ex3YsYjJb6t8I2XYVOQjwbBbEXMN3WvzHcuwfJ3ou9WxLwEbpQ5Ugi4EP2Pipgv0QvsAFO/PAlSMBkpmK6IuaWuqi/Uo4hfTrUHUN+qn9WhmvH5cb2bSkA3/nCiAeaTepiCfD3IFxrilkxIvvgP2Jm2AtqQo75qI6Au+aTaXzI+HPhuL8nnI+7Y7IM0qF5R52L8QJsfw7rkixH3TN31b9tWB5oKaEq+URi7p66oj9SxYvxJ8FgErQQoH99oSL5ed2L5w0Asy0nbjWXsCXlRwEGA58w2yqDZxjmO8flekOcC8tfocElAv9lR6gl5LkCzl0JjcFvyooCZ/0FeFLDUELiQgjwXcGj2aawLmgjybltyzWrCB8BVYLNmCbYfJdbNJnXbqRZKlmNWR2Zl06pZGXWa8umIP+uE1EpB3qb8Xd+rrp0BVn2SIgW5vQFuA33x+3LFwuW476lScLLtmV0mTvPPxgqMpkxBsY0HwVaJbyR8O23Jtfpy+hh4CnwEngNfgTvAfeADcB046lUK8tYxu2IXbdPsKt569io/ATmPTUo5+FpvAAAAAElFTkSuQmCC+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjJlYTcwZDZhLWJiYmUtNGM0ZS1iODVhLWFmYmFkOGFmYjkxMyIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjozMzo0MC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowN2ZhMTRjYi01NjVhLTc0NGQtYjljYi04Y2QzYzJlNGJlZmQiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6MTI6NDUtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz5Vep1AAAAC8ElEQVRYhbWWS0gWURTH/6lYiCAVGQQSpdUiiIgSsU0URi+MqAiixIXYw4xWWRSGKRGBFQS9NLKIIKSUFiFKixZCoBStjKIntShCSBeFPX4t5ozf+H0z33cn9MBlZs75n3P+98659x4BAtYAn0jII6DAbK7jFBPlmIufgHJzeAfUA432/R7IdkzeZj53gTqg074vuhAYAT4kGYosQKtD8mWGPZqkbzb94kwEAHaFGAeBYQcCZyxGmA3geDr/LHmyUKkyU9K3EH2y+JisJH2BPb+m9QaeGNOSALMa0612WIFZhn0csoIA+Zl+QR7w0cDP8YrRl3oHAgJ2Gv418CzgvzmTr/+SA5wFhoABYCtwxII0OZK4b/ghvF2w1MUvE+B0DBIA1x3Jjo+cDAXWKAl7TrOnX3BbJJVK+iWpUNKYpFqHok0pQpfRZDOsA3YTLdVxVyAOeF8gUTdQCuQC04EVwDWzXZ0qApWW4GAazP7ASk0qgWwL3OOA7TOs0z0Sd/YlDtgSw1aGTGI7UIV318QicN6CuuIBGgLfFaRKM2Tehv8rfyVVSOqUlCupV9ILSdWSvkuqk3RS0vBU/IIiUuVtCO5hnCUV8Bm3IuyxpMXADnvvCsFtiEug34LVpMH42/BQQNcL/AnBdrgSyCdxtfbas5vEQZQLlAE3zHY5yd/vmLqA2Yb3D7VzQeAcYBuwPqBbRULKTHeYaBmMmERVCLaDwDZsSDJ+IXETvgIKkwJm4RVmi421eCckwJIIEvPwOuUWvEZ4/Bzw/9sVcy4DXprudkSwqPEDeBPHR5aoL8T4E69JiUNgucUbwGtM7gALXAhsCjH2A6MxCfit2SgTW7PyKB+fQHuIcQR4GiP5fIt1M6DLwesxx+w9lMAlc9xjyjxbOoCVMQi0mk+yfpHpN0YREHCPVKmNkVzArQgCM0y/Nx0BAeuAC3jbrzhmcuFtxbBE7aafm4nAZIwHlqwN7zj274UTUT6TTSBYCwC/gQPp8P8AGt+2v3RmfFgAAAAASUVORK5CYII=+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjkwYzZlNDkzLTFkM2QtM2I0ZC04MjRlLWQ3YmFkNGU3NDUzNCIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpiZTc1ODU2NC04YThkLTQ2NDUtYmU2Yy1lMmY5ZmQwMWU0YjgiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6Mjc6MTItMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PHrkDAAAFDklEQVRYhe2XT2gUVxzHP+/N7M5kdetG6+ISY1sRak38Q7L9RwyUhlioh4aI1nry3EKgiKcWUS8tVQjkkAZbpLSRVg/anEzFYGJzsU5AAqUhpUuyQdckWje7+bPZnZnXQ3bDanbWikUv/Z5m5v3e+33e7733e78RSimep/ShoaH9QBOQAZ4FjQ5kgV/r6+t/1oEjruvWAdozcA6A4zhOIpE4EI1G0YG6qakpZ3BwUOq6LmzbRgjh2VkIUbJdKcXjllNKiWEYNDc3+zZs2LAR+FQH1JUrV/xdXV0xKeVV13V9QA7wplhqkyW+u5RZRiklVVVVq2tqat6LRCIvAm/oAJqmKV3Xe/r7+6uEEE1CCD/gPMa5KnqnjD2AVErds237m4GBgW8jkcg1YC0sbQiy2SyVlZWmlPJgJpPJ3rx5UxmGoQkhSs4mH+oVESplr5RCCEF9fX1ofHz85IkTJ+jv7884jgOg9EJoNE3LAvT09PhPnTqVBK4Bq8rMqhRcyWULBALi3Llzb7muG3Qc50MppZ0HWIpAXhLAMAyAHyzLaivjfFnRaPSxNtevXw8qpX6LxWKbWDpt9kNOAdRSXFV+h1f8G+dPIqWUVErJYucPATyicifgP5UXwDPT/wArAMql4adUyYFXACwsLHgaP4XmgYyUKwOuw3K2EoCorKxk27ZtGvBqmQGXR7Isq/DolrEPSCkDuq4X+i4fxeVMaNu2C7Bnzx62b9/eksvl3lFKlYyEEIISbV6XkBJCSJ/PVz07O5sB/CsAbNvmzp07i1NTUx/39vZ2GoaxxjRN23XdkjWCKLFRXNcteRcUNDs7+2BwcLBS1/VU8bWtAyIUColIJKKFw+GvOzo65oBawKR8WL2uY09pmpY+dOhQDDhSmIOwLEtls1nu379/LxwOT2iatoD3JtTyTh7k3yuANBAAVrO0DOWqEiNvuxUgGo1mdOBYX1/fSb/fvzYWi2n5imfFTKSUpNNpx3EcGhsb1/n9fjE5OTlXVVUVjMfjMyMjI2nTNCt8Pp/wgsiHXqbT6eTo6GgIMHXgi66uropMJrNFKeXLd14RgVwup9LptLtv377Vzc3NzRcuXMidP3/e6OjoWDRNc017e/v49PT0YCgUWi+l9HtBSClxXZdUKvU3MKoD9u3bt48BL1BmDY8ePbqupaWlzTCMg8lkcrS7u3vL3bt3OxKJxPDOnTvPdnZ2vhYIBL7fu3fvJ0CQ8kWuyPuaFUXnuFgm0AC8DmwCaoBXgOrh4eGR48ePr4/H46PAQSDe1tZ2ZPfu3V9t3rxZptPpqWAwaAG/AxPAQDQaHfYk8QDYqpT6BdgohJDz8/OZoaGh1KVLl8StW7fWp1Kpn4DPLcv6q1CQNDU1tYbD4Y6Ghoaquro65ff7RS6XyyUSiT9bW1s/AkpC6KU+AqYQYtPAwMD86dOnjUwmY87Nzc1ls9leoBu4YVnWg+IOfX19F4EbV69e/cDn8x0A3jxz5oxp2/ZW4Evg/ScBACAYDAZ27NgxcPjw4YvBYFCEQqFF0zSrgZdYWkdlWVZxVayA+ZmZmbPT09PfhcPh9rGxsVVAtZcPL4DU4uLi2K5du16ura1t1HX97bxD4bplc00BXAWDQaSUvrGxsSxlNrcXwGQ8Hu+cmJj4LJlMviCEkHkAz7+fR7KzkFKilHIuX77sB/7wAhCFur2EVgH7gXdZuk6L5ZXtHh2o8APzI9DvCfA89Q9+dgWL9W/IeAAAAABJRU5ErkJggg=='
        image_64_decode = base64.decodestring(image_enconded)
        image_result = open(create_proxy_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
        
    # Create Rig Icon
    create_rig_btn_ico = icons_folder_dir + 'gt_abr_create_rig.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(create_rig_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNi4wLWMwMDIgNzkuMTY0NDg4LCAyMDIwLzA3LzEwLTIyOjA2OjUzICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjIuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTEyLTMwVDIyOjM2OjU3LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wMS0wM1QxMTo1OTowNC0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wMS0wM1QxMTo1OTowNC0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphOTMwMjJjNC0zZTljLWQ5NGYtOGZiMi0xMThkNzc2Y2I4YTYiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDowZGQ3ODU1NS05Nzk0LTk1NDctOGJmOS02NTM5YmFiOTU0ODkiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpmMDJjNmFhZC1lZmRmLWQ5NDktOTYyYy1lOThmMTZiOTljMDgiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmYwMmM2YWFkLWVmZGYtZDk0OS05NjJjLWU5OGYxNmI5OWMwOCIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjozNjo1Ny0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphOTMwMjJjNC0zZTljLWQ5NGYtOGZiMi0xMThkNzc2Y2I4YTYiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6NTk6MDQtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4QupX8AAACnElEQVRYhcWXPWsUURSG33XDfkUQVGKimw/TCRYiiCJisBDEVjAIKQQ7FX9AOv0FloKdFmlECyG9IMRKUdFCiYW4S8wmxtVEXVEfi3uGGWdnZndnZ/HAgZnznq977plz7+QA/U8a6kJnVtINSXVJnyXlJb2X9Nr4paT11BkAnfg0sIVPz4FN/qU14HoXvtq4F+V5C3YPyJnsMHAFeGxYA5gaVAICjligTaAcwqrAD8P3DioBAbus5FjQIDYM1A2b7sZfjnRfQdEaLy+pHMKGJK1J2iGpKqmW5GhbmuiSWpJGJZUkPQlhvySNWRIfJI0nekrTuQE+a+U+E4GVgA3gJzCS9RYE6ZukF5KORWBFSQ25uXEwyjjtFni0U64H3sbgLbmeaMQ56KcCZUlv5JrslKTvMTo1SU1JJ+X6oylXNUnpK1CQG81VScsxwWXyaUkjcttQl7Ql18COUjRe2ebAb+CaNeH9AF4ALkTYXAUu46YlwGSaQeR1NsAek52z9wVgAqjZ+6sEH5+AJnC8l+BFM4T2CTiDT3+A8/a8mOAP4F0vZV83o/EYnVWg5ZUWuGP6Ubo3DZvvJnjFnBNwHq6Ml1ywMk9xQyisf9t0L9JFDxSBL2awLya5jZjkjpp8KSC7a7I5T5YUfDuwYgZTEXgZv6PjtuWE4Q+AW/Z8KagTF3wI/9YzGlOZr4aPdajiIXyaDeNRBsPAx4SVl/DvA5MdgoeTbpOHBQWSu71EdMOl5vCeeiuLCh6cA3F7njqBCrBsziciFCsdKtN3AovmPN8heCZlD7J3Gno/FrsjTr0VuXO/KnfFypYC2SzZKg/gfw3eHNif9crDW+DxMws4hzutIHoODCwBAY8s8Cq9feeZJTADPCQ0MgfFWdyK+6K//IPqj1Ija+YAAAAASUVORK5CYII=+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjBjOGI1MmEwLTllNzUtZTc0Zi1iM2JhLWQ1YTEzZGM0ZDNiMCIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjo0MToyOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDoxODUxOTlkMC0yZDliLTU4NDAtOTQwZi04OTkwMTFjMGFhYjEiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6NTM6NDItMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7Y+HHIAAADpUlEQVRYha2XXYjVRRjGn7OtH5lEJFp5YbFpH5Z9XIReSJloG2lIGZgGpSIu0Z2lBVFkxgp6IaQXQYiWZCSWRCpEK4uVnyGslh+ha2asoBeirlla+utinunMGc6y56z/gWH+7/O+M+9zZt555z0CVGAfA3xNaE8meDdwAZgNDEjnFOlcwGXgEvAH8BfQBHxqQns9jkvnlAAV2A5K+k3SVEnpwuM87pbUkOoaC3B6j6TBkvZLOi1pivGR1l2QtEfSl8ZvkTRM0ihJm693y0vA31S2BT3YPgCcyWxnXi+BVi/UDCwBWow/CBxOHC003gQsBR4CfqaAoPvADloTbAjwL/An8DbwuW3eTGxeMnagiMh/1ottt/yx5dTmiwR7JiVU1PU7Dlz19x7/+lQ/OyHwsr8biyAwHFjrBRcbm2P5OcuDgHPAKctDgS7gIjC3Vkf3Ao8C92f4J3b2RIZvNH6RchuZ2RyF2pw/T2Wbn+iaja0lZL59ie4V4CtgBXC7sbdsf9BjWzWHd2TyBhtP9C/am+l/BE7aGcCBHn7IAuvXAVuAn4Cm3GiJjdYk2FngkL/jQxN171peZbk10b8B/ArstDw3myuSICwBy2ywyeNJ4IS/Y3Z7wXIXsD+x/4eQYI4BPwBjrYs2mxMsBmcFgUYrT1AOurOE69WcsZ4AdABXKD+533n+t5TbLuvuS7BTwPhqBATMsNGcfJt66ROyXZoIrKQyll4D3gEG5vPzxTZ5sZsS7EZCLv+McNeHJrqS7TvqJN0jgX2EF6uf5dGE8yUZASYlBI4R4qXPBFoIZxif1WmU46IbOA/caexWyoE1xNhjlq8BOwg5vqLs6o0AhPu9gZA8ojKm1BFVJkK4NVGeCawnBBmE2rAuAlOrKD+yrtrEK0B7FfwuzxlbK4EGl0nfSDos6b2k1Nrm8ZGsBLtZUj9JbQm2SFKHQj0oSedrLuiAp4APgV/MPj2G342N97k+THjZLhFuh4DJtjkOrCYkmoZ6jiDt7YRqJgbRbUAnla2bUN/FW3AOOFKrw7znVfE1STdI/x/NaUl3S5ouaYykTknr0g30kZypecurHEHs8WF53HL/XtgPzgJvdT1bnx9Bfy/Saflpy1eBebh8cp9FyA1YJ8LzCqFC6hOBEvBqQgLCw9Lm7/dtF5/UHZQLzWi/mHIGrZtA7C2EjPZ6gnUR0q2ArXYWdS9aXl6v454IVOvr7WS+x+/76qyvBCYTymwI/35nFEngP95bhWYX1iytAAAAAElFTkSuQmCC+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjQ2OTY5NjAzLWUxNzYtNDQ0MC04MDMyLWYyOTk2ZjhiZDhhMCIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjoyODo1NC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpjOTRkMjQ0MS03ZDAyLTZkNGUtOWE0OS1kNTBkMTQ1MTIyNWYiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6MTQ6MDktMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz66Y+ZhAAACHElEQVRYhcWXsUtWURjGfwZBOZjQUNicBRKCg9QkWq7fVJNrIDgoGGLiHDmKi8bX0tBUf0MgDbm5CkKDUC0ltGQg9Gu4762bXa/3ds9HLxzO/c77Pt/znPOec+97UEnUzqub/mnv1U4Vrk8lgV0E9oFrwGvgHXAJeAgMASvAWiky0ex3YsYjJb6t8I2XYVOQjwbBbEXMN3WvzHcuwfJ3ou9WxLwEbpQ5Ugi4EP2Pipgv0QvsAFO/PAlSMBkpmK6IuaWuqi/Uo4hfTrUHUN+qn9WhmvH5cb2bSkA3/nCiAeaTepiCfD3IFxrilkxIvvgP2Jm2AtqQo75qI6Au+aTaXzI+HPhuL8nnI+7Y7IM0qF5R52L8QJsfw7rkixH3TN31b9tWB5oKaEq+URi7p66oj9SxYvxJ8FgErQQoH99oSL5ed2L5w0Asy0nbjWXsCXlRwEGA58w2yqDZxjmO8flekOcC8tfocElAv9lR6gl5LkCzl0JjcFvyooCZ/0FeFLDUELiQgjwXcGj2aawLmgjybltyzWrCB8BVYLNmCbYfJdbNJnXbqRZKlmNWR2Zl06pZGXWa8umIP+uE1EpB3qb8Xd+rrp0BVn2SIgW5vQFuA33x+3LFwuW476lScLLtmV0mTvPPxgqMpkxBsY0HwVaJbyR8O23Jtfpy+hh4CnwEngNfgTvAfeADcB046lUK8tYxu2IXbdPsKt569io/ATmPTUo5+FpvAAAAAElFTkSuQmCC+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjJlYTcwZDZhLWJiYmUtNGM0ZS1iODVhLWFmYmFkOGFmYjkxMyIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjozMzo0MC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowN2ZhMTRjYi01NjVhLTc0NGQtYjljYi04Y2QzYzJlNGJlZmQiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6MTI6NDUtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz5Vep1AAAAC8ElEQVRYhbWWS0gWURTH/6lYiCAVGQQSpdUiiIgSsU0URi+MqAiixIXYw4xWWRSGKRGBFQS9NLKIIKSUFiFKixZCoBStjKIntShCSBeFPX4t5ozf+H0z33cn9MBlZs75n3P+98659x4BAtYAn0jII6DAbK7jFBPlmIufgHJzeAfUA432/R7IdkzeZj53gTqg074vuhAYAT4kGYosQKtD8mWGPZqkbzb94kwEAHaFGAeBYQcCZyxGmA3geDr/LHmyUKkyU9K3EH2y+JisJH2BPb+m9QaeGNOSALMa0612WIFZhn0csoIA+Zl+QR7w0cDP8YrRl3oHAgJ2Gv418CzgvzmTr/+SA5wFhoABYCtwxII0OZK4b/ghvF2w1MUvE+B0DBIA1x3Jjo+cDAXWKAl7TrOnX3BbJJVK+iWpUNKYpFqHok0pQpfRZDOsA3YTLdVxVyAOeF8gUTdQCuQC04EVwDWzXZ0qApWW4GAazP7ASk0qgWwL3OOA7TOs0z0Sd/YlDtgSw1aGTGI7UIV318QicN6CuuIBGgLfFaRKM2Tehv8rfyVVSOqUlCupV9ILSdWSvkuqk3RS0vBU/IIiUuVtCO5hnCUV8Bm3IuyxpMXADnvvCsFtiEug34LVpMH42/BQQNcL/AnBdrgSyCdxtfbas5vEQZQLlAE3zHY5yd/vmLqA2Yb3D7VzQeAcYBuwPqBbRULKTHeYaBmMmERVCLaDwDZsSDJ+IXETvgIKkwJm4RVmi421eCckwJIIEvPwOuUWvEZ4/Bzw/9sVcy4DXprudkSwqPEDeBPHR5aoL8T4E69JiUNgucUbwGtM7gALXAhsCjH2A6MxCfit2SgTW7PyKB+fQHuIcQR4GiP5fIt1M6DLwesxx+w9lMAlc9xjyjxbOoCVMQi0mk+yfpHpN0YREHCPVKmNkVzArQgCM0y/Nx0BAeuAC3jbrzhmcuFtxbBE7aafm4nAZIwHlqwN7zj274UTUT6TTSBYCwC/gQPp8P8AGt+2v3RmfFgAAAAASUVORK5CYII=+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjkwYzZlNDkzLTFkM2QtM2I0ZC04MjRlLWQ3YmFkNGU3NDUzNCIgc3RFdnQ6d2hlbj0iMjAyMC0xMS0wM1QxMTo1NTozOC0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDpiZTc1ODU2NC04YThkLTQ2NDUtYmU2Yy1lMmY5ZmQwMWU0YjgiIHN0RXZ0OndoZW49IjIwMjAtMTEtMDNUMTI6Mjc6MTItMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7PHrkDAAAFDklEQVRYhe2XT2gUVxzHP+/N7M5kdetG6+ISY1sRak38Q7L9RwyUhlioh4aI1nry3EKgiKcWUS8tVQjkkAZbpLSRVg/anEzFYGJzsU5AAqUhpUuyQdckWje7+bPZnZnXQ3bDanbWikUv/Z5m5v3e+33e7733e78RSimep/ShoaH9QBOQAZ4FjQ5kgV/r6+t/1oEjruvWAdozcA6A4zhOIpE4EI1G0YG6qakpZ3BwUOq6LmzbRgjh2VkIUbJdKcXjllNKiWEYNDc3+zZs2LAR+FQH1JUrV/xdXV0xKeVV13V9QA7wplhqkyW+u5RZRiklVVVVq2tqat6LRCIvAm/oAJqmKV3Xe/r7+6uEEE1CCD/gPMa5KnqnjD2AVErds237m4GBgW8jkcg1YC0sbQiy2SyVlZWmlPJgJpPJ3rx5UxmGoQkhSs4mH+oVESplr5RCCEF9fX1ofHz85IkTJ+jv7884jgOg9EJoNE3LAvT09PhPnTqVBK4Bq8rMqhRcyWULBALi3Llzb7muG3Qc50MppZ0HWIpAXhLAMAyAHyzLaivjfFnRaPSxNtevXw8qpX6LxWKbWDpt9kNOAdRSXFV+h1f8G+dPIqWUVErJYucPATyicifgP5UXwDPT/wArAMql4adUyYFXACwsLHgaP4XmgYyUKwOuw3K2EoCorKxk27ZtGvBqmQGXR7Isq/DolrEPSCkDuq4X+i4fxeVMaNu2C7Bnzx62b9/eksvl3lFKlYyEEIISbV6XkBJCSJ/PVz07O5sB/CsAbNvmzp07i1NTUx/39vZ2GoaxxjRN23XdkjWCKLFRXNcteRcUNDs7+2BwcLBS1/VU8bWtAyIUColIJKKFw+GvOzo65oBawKR8WL2uY09pmpY+dOhQDDhSmIOwLEtls1nu379/LxwOT2iatoD3JtTyTh7k3yuANBAAVrO0DOWqEiNvuxUgGo1mdOBYX1/fSb/fvzYWi2n5imfFTKSUpNNpx3EcGhsb1/n9fjE5OTlXVVUVjMfjMyMjI2nTNCt8Pp/wgsiHXqbT6eTo6GgIMHXgi66uropMJrNFKeXLd14RgVwup9LptLtv377Vzc3NzRcuXMidP3/e6OjoWDRNc017e/v49PT0YCgUWi+l9HtBSClxXZdUKvU3MKoD9u3bt48BL1BmDY8ePbqupaWlzTCMg8lkcrS7u3vL3bt3OxKJxPDOnTvPdnZ2vhYIBL7fu3fvJ0CQ8kWuyPuaFUXnuFgm0AC8DmwCaoBXgOrh4eGR48ePr4/H46PAQSDe1tZ2ZPfu3V9t3rxZptPpqWAwaAG/AxPAQDQaHfYk8QDYqpT6BdgohJDz8/OZoaGh1KVLl8StW7fWp1Kpn4DPLcv6q1CQNDU1tYbD4Y6Ghoaquro65ff7RS6XyyUSiT9bW1s/AkpC6KU+AqYQYtPAwMD86dOnjUwmY87Nzc1ls9leoBu4YVnWg+IOfX19F4EbV69e/cDn8x0A3jxz5oxp2/ZW4Evg/ScBACAYDAZ27NgxcPjw4YvBYFCEQqFF0zSrgZdYWkdlWVZxVayA+ZmZmbPT09PfhcPh9rGxsVVAtZcPL4DU4uLi2K5du16ura1t1HX97bxD4bplc00BXAWDQaSUvrGxsSxlNrcXwGQ8Hu+cmJj4LJlMviCEkHkAz7+fR7KzkFKilHIuX77sB/7wAhCFur2EVgH7gXdZuk6L5ZXtHh2o8APzI9DvCfA89Q9+dgWL9W/IeAAAAABJRU5ErkJggg=='
        image_64_decode = base64.decodestring(image_enconded)
        image_result = open(create_rig_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()


    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    # Step 1
    cmds.text('Step 1 - Proxy:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    # cmds.button( l ="Create Proxy", bgc=(.6,.6,.6), c=lambda x:validate_operation('create_proxy'))
    
    cmds.iconTextButton( style='iconAndTextVertical', image1=create_proxy_btn_ico, label='Create Proxy',\
                         statusBarMessage='Creates a proxy/guide elements so the user can determine the character\'s shape.',\
                         olc=[1,0,0] , enableBackground=True, bgc=[.4,.4,.4], h=80,\
                         command=lambda: validate_operation('create_proxy'))
    
    # Step 2
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 2 - Pose:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button( l ="Reset Proxy", bgc=(.3,.3,.3), c=lambda x:reset_proxy())
    cmds.separator(h=6, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button( l ="Mirror Right to Left", bgc=(.3,.3,.3), c=lambda x:mirror_proxy('right_to_left'))
    cmds.button( l ="Mirror Left to Right", bgc=(.3,.3,.3), c=lambda x:mirror_proxy('left_to_right'))
    
   
    cmds.separator(h=8, style='none') # Empty Space
    cmds.separator(h=8, style='none') # Empty Space
    cmds.button( l ="Import Pose", bgc=(.3,.3,.3), c=lambda x:import_proxy_pose())
    cmds.button( l ="Export Pose", bgc=(.3,.3,.3), c=lambda x:export_proxy_pose())
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.button( l ="Delete Proxy", bgc=(.3,.3,.3), c=lambda x:delete_proxy())

    
    # Step 3
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 3 - Create Rig:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    #cmds.button( l ="Create Rig", bgc=(.6,.6,.6), c=lambda x:validate_operation('create_controls'))
    
    cmds.iconTextButton( style='iconAndTextVertical', image1=create_rig_btn_ico, label='Create Rig',\
                         statusBarMessage='Creates the control rig. It uses the transform data found in the proxy to determine how to create the skeleton, controls and mechanics.',\
                         olc=[1,0,0] , enableBackground=True, bgc=[.4,.4,.4], h=80,\
                         command=lambda: validate_operation('create_controls'))
    
    # Step 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 4 - Skin Weights:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button( l ="Select Skinning Joints", bgc=(.3,.3,.3), c=lambda x:select_skinning_joints())
    cmds.button( l ="Bind Skin Options", bgc=(.3,.3,.3), c=lambda x:mel.eval("SmoothBindSkinOptions;"))

    cmds.separator(h=5, style='none') # Empty Space
    
    # Utilities
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Utilities:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.button( l ="Add Seamless FK/IK Switch to Shelf", bgc=(.3,.3,.3), c=lambda x:add_seamless_fkik_button())
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button( l ="Toggle Label Visibility", bgc=(.3,.3,.3), c=lambda x:gtu_uniform_jnt_label_toggle())
    cmds.button( l ="Attach to HumanIK", bgc=(.3,.3,.3), c=lambda x:gt_ab_define_humanik('auto_biped'))

    cmds.separator(h=10, style='none') # Empty Space

    # Show and Lock Window
    cmds.showWindow(build_gui_auto_biped_rig)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/HIKcreateControlRig.png')
    widget.setWindowIcon(icon)
    
    
    # Main GUI Ends Here =================================================================================
    

# Creates Help GUI
def build_help_gui_auto_biped_rig():
    ''' Creates the Help windows '''
    window_name = "build_help_gui_auto_biped_rig"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=(.4, .4, .4),  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    help_spacing = 7

    # Body ====================   
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='Script for quickly generating an advanced biped rig', align="center", fn="boldLabelFont")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='For more predictable results execute it in a new scene\n containing only the geometry of the desired character.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Step 1:', align="center", fn="boldLabelFont")
    cmds.text(l='Create Proxy: This button will create many temporary\ncurves that will later be used to generate the rig.', align="center")
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='In case you want to re-scale the proxy,\n use the root proxy control for that.\n The initial scale is the average height of a woman.\n(160cm)', align="center")
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='To position the eye joints: Center the pivot point\n of the eye geometry then display its LRA\n so you can snap the proxy to its center.', align="center")
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='These are not joints.\nPlease don\'t delete or rename them.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Step 2:', align="center", fn="boldLabelFont")
    cmds.text(l='Pose the proxy (guide) to match your character.', align="center")
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Reset Proxy:\n Resets the position and rotation of the proxy\n elements, essentially "recreating" the proxy.', align="center")

    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Mirror Side to Side:\n Copies the transform data from one\n side to the other, mirroring the pose.', align="center")
 
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Import Pose:\n Imports a JSON file containing the transforms\n of the proxy elements. This file is generated\n using the "Export Pose" function.', align="center")
 
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Export Pose:\n Exports a JSON file containing the\n transforms of the proxy elements.', align="center")

    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Delete Proxy:\n Simply deletes the proxy in case\nyou no longer need it.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Step 3:', align="center", fn="boldLabelFont")
    cmds.text(l='This button creates the control rig. \nIt uses the transform data found in the proxy to\n determine how to create the skeleton and controls.\nThis function will delete the proxy.\nMake sure you export it first if you plan to reuse it later.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Step 4:', align="center", fn="boldLabelFont")
    cmds.text(l='Now that the rig has been created,\n all that is left is to attach it to the geometry.', align="center")
    
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Select Skinning Joints:\n Select only joints that should\n be used when skinning the character.\n This means that it will not include end joints or the toes.', align="center")
    cmds.separator(h=help_spacing, style='none') # Empty Space
    cmds.text(l='- Bind Skin Options:\n Opens the options for the function "Bind Skin"\n so the desired geometry can attached to the\n skinning joints.\nMake sure to use the "Bind to" as "Selected Joints"', align="center")
    
    
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
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        ''' Closes help windows '''
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    # Help Dialog Ends Here =================================================================================




def gtu_combine_curves_list(curve_list):
    ''' 
    This is a modified version of the GT Utility "Combine Curves"
    It moves the shape objects of all elements in the provided input (curve_list) to a single group (combining them)
    This version was changed to accept a list of objects (instead of selection)
    
            Parameters:
                    curve_list (list): A string of strings with the name of the curves to be combined.
    
    '''
    errors = ''
    try:
        function_name = 'GTU Combine Curves List'
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True
        acceptable_types = ['nurbsCurve','bezierCurve']
        bezier_in_selection = []
    
        for obj in curve_list:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(obj)
                if cmds.objectType(shape) not in acceptable_types:
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')
            
        if valid_selection and len(curve_list) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False
             
        if len(bezier_in_selection) > 0 and valid_selection:
            user_input = cmds.confirmDialog( title='Bezier curve detected!',\
                                message='A bezier curve was found in your selection.\nWould you like to convert Bezier to NURBS before combining?',\
                                button=['Yes','No'],\
                                defaultButton='Yes',\
                                cancelButton='No',\
                                dismissString='No',\
                                icon="warning" )
            if user_input == 'Yes':
                    for obj in bezier_in_selection:
                            cmds.bezierCurveToNurbs()
   
        if valid_selection:
            shapes = []
            for obj in curve_list:
                extracted_shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for ext_shape in extracted_shapes:
                    shapes.append(ext_shape)

            for obj in range(len(curve_list)):
                cmds.makeIdentity(curve_list[obj], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=curve_list[0])
            cmds.select(shapes[0])
            for obj in range(1, (len(shapes))):
                cmds.select(shapes[obj], add=True)
                
            cmds.select(group, add=True) 
            cmds.parent(relative=True, shape=True)
            cmds.delete(curve_list)   
            combined_curve = cmds.rename(group, curve_list[0])
            return combined_curve
         
    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occured when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def change_outliner_color(obj, rgb_color=(1,1,1)):
    ''' 
    Sets the outliner color for the selected object 
    
            Parameters:
                obj_to_set (str): Name (path) of the object to change.
    
    '''
    if cmds.objExists(obj) and cmds.getAttr(obj + '.useOutlinerColor', lock=True) is False:
        cmds.setAttr(obj + '.useOutlinerColor', 1)
        cmds.setAttr(obj + '.outlinerColorR', rgb_color[0])
        cmds.setAttr(obj + '.outlinerColorG', rgb_color[1])
        cmds.setAttr(obj + '.outlinerColorB', rgb_color[2])


def change_viewport_color(obj, rgb_color=(1,1,1)):
    '''
    Changes the color of an object by changing the drawing override settings
            
            Parameters:
                    obj (string): Name of the object to change color
                    rgb_color (tuple): RGB color 
                        
    '''
    if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
        cmds.setAttr(obj + ".overrideEnabled", 1)
        cmds.setAttr(obj + ".overrideRGBColors", 1) 
        cmds.setAttr(obj + ".overrideColorRGB", rgb_color[0], rgb_color[1], rgb_color[2]) 

def add_node_note(obj, note_string):
    ''' Addes a note to the provided node (It can be seen at the bottom of the attribute editor)
    
            Parameters:
                obj (string): Name of the object.
                note_string (string): A string to be used as the note.
    
    '''
    if not cmds.attributeQuery("notes", n = obj, ex = True):
        cmds.addAttr(obj, ln = "notes", sn="nts", dt="string")
        cmds.setAttr("%s.notes"%obj, note_string, type="string")
    else:
        cmds.warning("%s already has a notes attribute"%obj)


def make_stretchy_ik(ik_handle, stretchy_name='temp', attribute_holder=None):
    '''
    Creates two measure tools and use them to determine when the joints should be scaled up causing a stretchy effect.
    
            Parameters:
                ik_handle (string) : Name of the IK Handle (joints will be extracted from it)
                stretchy_name (string): Name to be used when creating system (optional, if not provided it will be "temp")
                attribute_holder (string): The name of an object. If it exists, custom attributes will be added to it. 
                                           These attributes allow the user to control whether or not the system is active, as well as its operation.
                                           For a more complete stretchy system you have to provide a valid object in this parameter as without it volume preservation is skipped
    
            Returns:
                list (list): A list with the end locator one (to be attached to the IK control) the stretchy_grp (system elements) and the end_ik_jnt (joint under the ikHandle)
    '''
    
    
    def caculate_distance(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
        ''' 
        Calculates the magnitude (in this case distance) between two objects
        
                Parameters:
                    pos_a_x (float): Position X for object A
                    pos_a_y (float): Position Y for object A
                    pos_a_z (float): Position Z for object A
                    pos_b_x (float): Position X for object B
                    pos_b_y (float): Position Y for object B
                    pos_b_z (float): Position Z for object B
                   
                Returns:
                    magnitude (float): Distance between two objects
        
        '''
        dx = pos_a_x - pos_b_x
        dy = pos_a_y - pos_b_y
        dz = pos_a_z - pos_b_z
        return math.sqrt( dx*dx + dy*dy + dz*dz )
    
    def int_to_en(num):
        '''
        Given an int32 number, returns an English word for it.
        
                Parameters:
                    num (int) and integer to be converted to English words.
                    
                Returns:
                    number (string): The input number as words
        
        
        '''
        d = { 0 : 'zero', 1 : 'one', 2 : 'two', 3 : 'three', 4 : 'four', 5 : 'five',
              6 : 'six', 7 : 'seven', 8 : 'eight', 9 : 'nine', 10 : 'ten',
              11 : 'eleven', 12 : 'twelve', 13 : 'thirteen', 14 : 'fourteen',
              15 : 'fifteen', 16 : 'sixteen', 17 : 'seventeen', 18 : 'eighteen',
              19 : 'nineteen', 20 : 'twenty',
              30 : 'thirty', 40 : 'forty', 50 : 'fifty', 60 : 'sixty',
              70 : 'seventy', 80 : 'eighty', 90 : 'ninety' }
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert(0 <= num)

        if (num < 20):
            return d[num]

        if (num < 100):
            if num % 10 == 0: return d[num]
            else: return d[num // 10 * 10] + '-' + d[num % 10]

        if (num < k):
            if num % 100 == 0: return d[num // 100] + ' hundred'
            else: return d[num // 100] + ' hundred and ' + int_to_en(num % 100)

        if (num < m):
            if num % k == 0: return int_to_en(num // k) + ' thousand'
            else: return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

        if (num < b):
            if (num % m) == 0: return int_to_en(num // m) + ' million'
            else: return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

        if (num < t):
            if (num % b) == 0: return int_to_en(num // b) + ' billion'
            else: return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

        if (num % t == 0): return int_to_en(num // t) + ' trillion'
        else: return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)

        raise AssertionError('num is too large: %s' % str(num))
    
    ########## Start of Make Stretchy Function ##########
    
    ik_handle_joints = cmds.ikHandle(ik_handle, q=True, jointList=True)
    children_last_jnt = cmds.listRelatives(ik_handle_joints[-1], children=True, type='joint') or []
    
    # Find end joint
    end_ik_jnt = ''
    if len(children_last_jnt) == 1:
        end_ik_jnt = children_last_jnt[0]
    elif len(children_last_jnt) > 1: # Find Joint Closest to ikHandle
        jnt_magnitude_pairs = []
        for jnt in children_last_jnt:
            ik_handle_ws_pos = cmds.xform(ik_handle, q=True, t=True, ws=True)
            jnt_ws_pos = cmds.xform(jnt, q=True, t=True, ws=True)
            mag = caculate_distance(ik_handle_ws_pos[0], ik_handle_ws_pos[1], ik_handle_ws_pos[2], jnt_ws_pos[0], jnt_ws_pos[1], jnt_ws_pos[2])
            jnt_magnitude_pairs.append([jnt, mag])
        # Find Lowest Distance
        curent_jnt = jnt_magnitude_pairs[1:][0]
        curent_closest = jnt_magnitude_pairs[1:][1]
        for pair in jnt_magnitude_pairs:
            if pair[1] < curent_closest:
                curent_closest = pair[1]
                curent_jnt = pair[0]
        end_ik_jnt = curent_jnt
    

    distance_one = cmds.distanceDimension(sp=(1,random.random()*10,1), ep=(2,random.random()*10,2) )
    distance_one_transform = cmds.listRelatives(distance_one, parent=True, f=True) or [][0]
    distance_one_locators = cmds.listConnections(distance_one)
    cmds.delete(cmds.pointConstraint(ik_handle_joints[0], distance_one_locators[0]))
    cmds.delete(cmds.pointConstraint(ik_handle, distance_one_locators[1]))

    # Rename Distance One Nodes
    distance_node_one = cmds.rename(distance_one_transform, stretchy_name + "_stretchyTerm_strechyDistance")
    start_loc_one = cmds.rename(distance_one_locators[0], stretchy_name + "_stretchyTerm_start")
    end_loc_one = cmds.rename(distance_one_locators[1], stretchy_name + "_stretchyTerm_end")

    
    distance_nodes = {} # [distance_node_transform, start_loc, end_loc, ik_handle_joint]
    index = 0
    for index in range(len(ik_handle_joints)):
        distance_node = cmds.distanceDimension(sp=(1,random.random()*10,1), ep=(2,random.random()*10,2) )
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, f=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        
        distance_node = cmds.rename(distance_node, stretchy_name + '_defaultTerm' + int_to_en(index+1).capitalize() + '_strechyDistanceShape' )
        distance_node_transform = cmds.rename(distance_node_transform, stretchy_name + '_defaultTerm' + int_to_en(index+1).capitalize() + '_strechyDistance' )
        start_loc = cmds.rename(distance_node_locators[0], stretchy_name + '_defaultTerm' + int_to_en(index+1).capitalize() + '_start')
        end_loc = cmds.rename(distance_node_locators[1], stretchy_name + '_defaultTerm' + int_to_en(index+1).capitalize() + '_end')

        cmds.delete(cmds.pointConstraint(ik_handle_joints[index], start_loc))
        if index < (len(ik_handle_joints)-1):
            cmds.delete(cmds.pointConstraint(ik_handle_joints[index+1], end_loc))
        else:
            cmds.delete(cmds.pointConstraint(end_ik_jnt, end_loc))

        
        distance_nodes[distance_node] = [distance_node_transform, start_loc, end_loc, ik_handle_joints[index]]
        
        index += 1
 
    # Organize Basic Hierarchy
    stretchy_grp = cmds.group(name=stretchy_name + "_stretchy_grp", empty=True, world=True)
    cmds.parent( distance_node_one, stretchy_grp )
    cmds.parent( start_loc_one, stretchy_grp )
    cmds.parent( end_loc_one, stretchy_grp )
 
    
    # Connect, Colorize and Organize Hierarchy
    default_distance_sum_node = cmds.createNode('plusMinusAverage', name=stretchy_name + "_defaultTermSum_plus")
    index = 0
    for node in distance_nodes:
        cmds.connectAttr('%s.distance' % node, '%s.input1D' % default_distance_sum_node + '[' + str(index) + ']')
        for obj in distance_nodes.get(node):
            if cmds.objectType(obj) != 'joint':
                change_outliner_color(obj, (1,.5,.5))
                cmds.parent(obj, stretchy_grp)
        index += 1
    
    # Outliner Color
    for obj in [distance_node_one,start_loc_one,end_loc_one]:
        change_outliner_color(obj,(.5,1,.2))
        

    # Connect Nodes
    nonzero_stretch_condition_node = cmds.createNode('condition', name=stretchy_name + "_strechyNonZero_condition")
    nonzero_multiply_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_onePctDistCondition_multiply")
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % nonzero_multiply_node)
    cmds.setAttr( nonzero_multiply_node + ".input2X", 0.01)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.colorIfTrueR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.secondTerm' % nonzero_stretch_condition_node)
    cmds.setAttr( nonzero_stretch_condition_node + ".operation", 5)
    
    
    stretch_normalization_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.firstTerm' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.colorIfFalseR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node, '%s.input1X' % stretch_normalization_node)
    
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input2X' % stretch_normalization_node)

    cmds.setAttr( stretch_normalization_node + ".operation", 2)

    stretch_condition_node = cmds.createNode('condition', name=stretchy_name + "_strechyAutomation_condition")
    cmds.setAttr( stretch_condition_node + ".operation", 3)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node, '%s.firstTerm' % stretch_condition_node) # Distance One
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.secondTerm' % stretch_condition_node)
    cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.colorIfTrueR' % stretch_condition_node)

    # Constraints
    cmds.pointConstraint (ik_handle_joints[0], start_loc_one)
    for node in distance_nodes:
        if distance_nodes.get(node)[3] == ik_handle_joints[0:][0]:
            start_loc_condition = cmds.pointConstraint (ik_handle_joints[0], distance_nodes.get(node)[1])
    
    # Attribute Holder Setup
    if attribute_holder:
        if cmds.objExists(attribute_holder):
            cmds.pointConstraint(attribute_holder, end_loc_one)
            cmds.addAttr(attribute_holder , ln='stretch', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + ".stretch", 1)
            cmds.addAttr(attribute_holder , ln='squash', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder , ln='stretchFromSource', at='bool', k=True)
            cmds.addAttr(attribute_holder , ln='saveVolume', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder , ln='baseVolumeMultiplier', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + ".baseVolumeMultiplier", .5)
            cmds.addAttr(attribute_holder , ln='minimumVolume', at='double', k=True, minValue=0.01, maxValue=1)
            cmds.addAttr(attribute_holder , ln='maximumVolume', at='double', k=True, minValue=0)
            cmds.setAttr(attribute_holder + ".minimumVolume", .4)
            cmds.setAttr(attribute_holder + ".maximumVolume", 2)
            cmds.setAttr(attribute_holder + ".stretchFromSource", 1)

            # Stretch From Body
            from_body_reverse_node = cmds.createNode('reverse', name=stretchy_name + '_stretchFromSource_reverse')
            cmds.connectAttr('%s.stretchFromSource' % attribute_holder, '%s.inputX' % from_body_reverse_node)
            cmds.connectAttr('%s.outputX' % from_body_reverse_node, '%s.w0' % start_loc_condition[0])

            # Squash
            squash_condition_node = cmds.createNode('condition', name=stretchy_name + "_squashAutomation_condition")
            cmds.setAttr(squash_condition_node + ".secondTerm", 1)
            cmds.setAttr(squash_condition_node + ".colorIfTrueR", 1)
            cmds.setAttr(squash_condition_node + ".colorIfFalseR", 3)
            cmds.connectAttr('%s.squash' % attribute_holder, '%s.firstTerm' % squash_condition_node)
            cmds.connectAttr('%s.outColorR' % squash_condition_node, '%s.operation' % stretch_condition_node)
            
            # Stretch
            activation_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_strechyActivation_blend")
            cmds.setAttr(activation_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.input[1]' % activation_blend_node)
            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.attributesBlender' % activation_blend_node)
            
            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.output' % activation_blend_node, '%s.scaleX' % jnt)
            
            # Save Volume
            save_volume_condition_node = cmds.createNode('condition', name=stretchy_name + "_saveVolume_condition")
            volume_normalization_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_volumeNormalization_divide")
            volume_value_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_volumeValue_divide")
            xy_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_volumeXY_divide")
            volume_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_volumeActivation_blend")
            volume_clamp_node = cmds.createNode('clamp', name=stretchy_name + "_volumeLimits_clamp")
            volume_base_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_volumeBase_blend")
            
            cmds.setAttr(save_volume_condition_node + ".secondTerm", 1)
            cmds.setAttr(volume_normalization_divide_node + ".operation", 2) # Divide
            cmds.setAttr(volume_value_divide_node + ".operation", 2) # Divide
            cmds.setAttr(xy_divide_node + ".operation", 2) # Divide

            cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node, '%s.input2X' % volume_normalization_divide_node) # Distance One
            cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % volume_normalization_divide_node)
            
            cmds.connectAttr('%s.outputX' % volume_normalization_divide_node, '%s.input2X' % volume_value_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % volume_value_divide_node)
            
            cmds.connectAttr('%s.outputX' % volume_value_divide_node, '%s.input2X' % xy_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % xy_divide_node)
            
            cmds.setAttr(volume_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outputX' % xy_divide_node, '%s.input[1]' % volume_blend_node)
          
            cmds.connectAttr('%s.saveVolume' % attribute_holder, '%s.attributesBlender' % volume_blend_node)
        
            cmds.connectAttr('%s.output' % volume_blend_node, '%s.inputR' % volume_clamp_node)
            cmds.connectAttr('%s.outputR' % volume_clamp_node, '%s.colorIfTrueR' % save_volume_condition_node)
            
            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.firstTerm' % save_volume_condition_node)
            cmds.connectAttr('%s.minimumVolume' % attribute_holder, '%s.minR' % volume_clamp_node)
            cmds.connectAttr('%s.maximumVolume' % attribute_holder, '%s.maxR' % volume_clamp_node)
        
            # Base Multiplier
            cmds.setAttr(volume_base_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.input[1]' % volume_base_blend_node)
            cmds.connectAttr('%s.baseVolumeMultiplier' % attribute_holder, '%s.attributesBlender' % volume_base_blend_node)
        
            # Connect to Joints
            cmds.connectAttr('%s.output' % volume_base_blend_node, '%s.scaleY' % ik_handle_joints[0])
            cmds.connectAttr('%s.output' % volume_base_blend_node, '%s.scaleZ' % ik_handle_joints[0])
        
            for jnt in ik_handle_joints[1:]:
                cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.scaleY' % jnt)
                cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.scaleZ' % jnt)
            
        else:
            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % jnt)
    else:
        for jnt in ik_handle_joints:
                cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % jnt)


    return [end_loc_one, stretchy_grp, end_ik_jnt]


def create_visualization_line(object_a, object_b):
    ''' 
    Creates a curve attached to two objects so you can easily visualize hierarchies 
    
                Parameters:
                    object_a (string): Name of the object driving the start of the curve
                    object_b (string): Name of the object driving end of the curve (usually a child of object_a)
                    
                Returns:
                    list (list): A list with the generated curve, cluster_a, and cluster_b
    
    '''
    crv = cmds.curve(p=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],d=1)
    cluster_a = cmds.cluster( crv + '.cv[0]' )
    cluster_b = cmds.cluster( crv + '.cv[1]' )

    if cmds.objExists(object_a):
        cmds.pointConstraint(object_a, cluster_a[1])
        
    if cmds.objExists(object_a):
        cmds.pointConstraint(object_b, cluster_b[1])
        
    crv = cmds.rename(crv, object_a + '_to_' + object_b)
    cluster_a = cmds.rename(cluster_a[1], object_a + '_cluster')
    cluster_b = cmds.rename(cluster_b[1], object_b + '_cluster')
    cmds.setAttr(cluster_a + '.v', 0)
    cmds.setAttr(cluster_b + '.v', 0)

    return [crv, cluster_a, cluster_b]



def create_joint_curve(name, scale, initial_position=(0,0,0)): 
    ''' 
    Creates a curve that looks like a joint to be used as a proxy 
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve
                initial_position (tuple): A tuple of three floats. Used to determine initial position of the curve.

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    
    '''
    curve_crv = cmds.curve(name=name, p=[[0.0, 2.428, 0.0], [0.0, 2.246, 0.93], [0.0, 1.72, 1.72], [0.0, 0.93, 2.246], [0.0, 0.0, 2.428], [0.0, -0.93, 2.246], [0.0, -1.72, 1.72], [0.0, -2.246, 0.93], [0.0, -2.428, 0.0], [0.0, -2.246, -0.93], [0.0, -1.72, -1.72], [0.0, -0.93, -2.246], [0.0, 0.0, -2.428], [0.0, 0.93, -2.246], [0.0, 1.72, -1.72], [0.0, 2.246, -0.93], [0.0, 2.428, 0.0], [0.93, 2.246, 0.0], [1.72, 1.72, 0.0], [2.246, 0.93, 0.0], [2.428, 0.0, 0.0], [2.246, -0.93, 0.0], [1.72, -1.72, 0.0], [0.93, -2.246, 0.0], [0.0, -2.428, 0.0], [-0.93, -2.246, 0.0], [-1.72, -1.72, 0.0], [-2.246, -0.93, 0.0], [-2.428, 0.0, 0.0], [-2.246, 0.93, 0.0], [-1.72, 1.72, 0.0], [-0.93, 2.246, 0.0], [0.0, 2.428, 0.0], [0.0, 2.246, -0.93], [0.0, 1.72, -1.72], [0.0, 0.93, -2.246], [0.0, 0.0, -2.428], [-0.93, 0.0, -2.246], [-1.72, 0.0, -1.72], [-2.246, 0.0, -0.93], [-2.428, 0.0, 0.0], [-2.246, 0.0, 0.93], [-1.72, 0.0, 1.72], [-0.93, 0.0, 2.246], [0.0, 0.0, 2.428], [0.93, 0.0, 2.246], [1.72, 0.0, 1.72], [2.246, 0.0, 0.93], [2.428, 0.0, 0.0], [2.246, 0.0, -0.93], [1.72, 0.0, -1.72], [0.93, 0.0, -2.246], [0.0, 0.0, -2.428]],d=1)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.move(initial_position[0], initial_position[1],initial_position[2], curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)
    # Rename Shapes
    for shape in cmds.listRelatives(curve_crv, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(name))
    return curve_crv
    
def create_loc_joint_curve(name, scale, initial_position=(0,0,0)): 
    ''' 
    Creates a curve that looks like a joint and a locator to be used as a proxy 
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve
                initial_position (tuple): A tuple of three floats. Used to determine initial position of the curve.

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    '''
    curve_assembly = []
    joint_crv = cmds.curve(name=name, p=[[0.0, 2.428, 0.0], [0.0, 2.246, 0.93], [0.0, 1.72, 1.72], [0.0, 0.93, 2.246], [0.0, 0.0, 2.428], [0.0, -0.93, 2.246], [0.0, -1.72, 1.72], [0.0, -2.246, 0.93], [0.0, -2.428, 0.0], [0.0, -2.246, -0.93], [0.0, -1.72, -1.72], [0.0, -0.93, -2.246], [0.0, 0.0, -2.428], [0.0, 0.93, -2.246], [0.0, 1.72, -1.72], [0.0, 2.246, -0.93], [0.0, 2.428, 0.0], [0.93, 2.246, 0.0], [1.72, 1.72, 0.0], [2.246, 0.93, 0.0], [2.428, 0.0, 0.0], [2.246, -0.93, 0.0], [1.72, -1.72, 0.0], [0.93, -2.246, 0.0], [0.0, -2.428, 0.0], [-0.93, -2.246, 0.0], [-1.72, -1.72, 0.0], [-2.246, -0.93, 0.0], [-2.428, 0.0, 0.0], [-2.246, 0.93, 0.0], [-1.72, 1.72, 0.0], [-0.93, 2.246, 0.0], [0.0, 2.428, 0.0], [0.0, 2.246, -0.93], [0.0, 1.72, -1.72], [0.0, 0.93, -2.246], [0.0, 0.0, -2.428], [-0.93, 0.0, -2.246], [-1.72, 0.0, -1.72], [-2.246, 0.0, -0.93], [-2.428, 0.0, 0.0], [-2.246, 0.0, 0.93], [-1.72, 0.0, 1.72], [-0.93, 0.0, 2.246], [0.0, 0.0, 2.428], [0.93, 0.0, 2.246], [1.72, 0.0, 1.72], [2.246, 0.0, 0.93], [2.428, 0.0, 0.0], [2.246, 0.0, -0.93], [1.72, 0.0, -1.72], [0.93, 0.0, -2.246], [0.0, 0.0, -2.428]],d=1)
    curve_assembly.append(joint_crv)
    loc_crv = cmds.curve(name=name + '_loc', p=[[0.0, 0.0, 0.158], [0.0, 0.0, -0.158], [0.0, 0.0, 0.0], [0.158, 0.0, 0.0], [-0.158, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.158, 0.0], [0.0, -0.158, 0.0]],d=1)
    curve_assembly.append(loc_crv)
    curve_crv = gtu_combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.move(initial_position[0], initial_position[1],initial_position[2], curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)
    
    # Rename Shapes
    shapes =  cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], "{0}Shape".format(curve_crv + 'Loc'))
    
    return curve_crv
    
def create_aim_joint_curve(name, scale):
    ''' 
    Creates a curve that looks like a joint with an arrow to be used as a proxy 
    It needs the function "gtu_combine_curves_list()" and "create_joint_curve" to properly work.
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    '''
    curve_assembly = []
    curve_crv_a = create_joint_curve(name, 1)
    curve_assembly.append(curve_crv_a)
    curve_crv_b = cmds.curve(name= 'arrow_temp_crv', p=[[-2.428, 0.0, 0.0], [2.428, 0.0, 0.0], [2.428, 0.0, -11.7], [4.85, 0.0, -11.7], [0.0, 0.0, -19.387], [-4.85, 0.0, -11.7], [-2.428, 0.0, -11.7], [-2.428, 0.0, 0.0]],d=1)
    curve_assembly.append(curve_crv_b)
    curve_crv = gtu_combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)
    
    # Rename Shapes
    shapes =  cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], "{0}Shape".format(curve_crv + 'Arrow'))
    
    return curve_crv

def create_directional_joint_curve(name, scale):
    ''' 
    Creates a curve that looks like a joint with an up direction to be used as a proxy 
    It needs the function "gtu_combine_curves_list()" and "create_joint_curve" to properly work.
    
            Parameters:
                name (string): Name of the generated curve
                scale (float): The desired initial scale of the curve

            Returns:
                curve_crv (string): Name of the generated curve (in case it was changed during creation)
    '''
    curve_assembly = []
    curve_crv_a = create_joint_curve(name, 1)
    curve_assembly.append(curve_crv_a)
    curve_crv_b = cmds.curve(name='arrow_tip_temp_crv', p=[[-0.468, 5.517, 0.807], [0.0, 7.383, 0.0], [0.468, 5.517, 0.807], [-0.468, 5.517, 0.807], [-0.936, 5.517, 0.0], [0.0, 7.383, 0.0], [-0.936, 5.517, 0.0], [-0.468, 5.517, -0.807], [0.0, 7.383, 0.0], [0.468, 5.517, -0.807], [-0.468, 5.517, -0.807], [0.468, 5.517, -0.807], [0.0, 7.383, 0.0], [0.936, 5.517, 0.0], [0.468, 5.517, -0.807], [0.936, 5.517, 0.0], [0.468, 5.517, 0.807]],d=1)
    curve_assembly.append(curve_crv_b)
    curve_crv_c = cmds.curve(name='arrow_base_temp_crv',p=[[-0.468, 5.517, 0.807], [0.0, 5.517, 0.0], [0.468, 5.517, 0.807], [-0.468, 5.517, 0.807], [-0.936, 5.517, 0.0], [0.0, 5.517, 0.0], [-0.936, 5.517, 0.0], [-0.468, 5.517, -0.807], [0.0, 5.517, 0.0], [0.468, 5.517, -0.807], [-0.468, 5.517, -0.807], [0.468, 5.517, -0.807], [0.0, 5.517, 0.0], [0.936, 5.517, 0.0], [0.468, 5.517, -0.807], [0.936, 5.517, 0.0], [0.468, 5.517, 0.807]],d=1)
    curve_assembly.append(curve_crv_c)
    curve_crv_d = cmds.curve(name='arrow_line_temp_crv', p=[[0.0, 5.517, 0.0], [0.0, 2.428, 0.0]],d=1)
    curve_assembly.append(curve_crv_d)
    curve_crv = gtu_combine_curves_list(curve_assembly)
    cmds.scale(scale, scale, scale, curve_crv)
    cmds.makeIdentity(curve_crv, apply=True, translate=True, scale=True)
    
    # Rename Shapes
    shapes =  cmds.listRelatives(curve_crv, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(curve_crv + 'Joint'))
    cmds.rename(shapes[1], "{0}Shape".format(curve_crv + 'ArrowTip'))
    cmds.rename(shapes[2], "{0}Shape".format(curve_crv + 'ArrowBase'))
    cmds.rename(shapes[3], "{0}Shape".format(curve_crv + 'ArrowLine'))
    
    return curve_crv

def create_main_control(name): 
    '''
    Creates a main control with an arrow pointing to +Z (Direction character should be facing)
    
        Parameters:
            name (string): Name of the new control
            
        Returns:
            main_crv (string): Name of the generated control (in case it was different than what was provided)
    
    '''
    main_crv_assembly = []
    main_crv_a = cmds.curve(name=name, p=[[-11.7, 0.0, 45.484], [-16.907, 0.0, 44.279], [-25.594, 0.0, 40.072], [-35.492, 0.0, 31.953], [-42.968, 0.0, 20.627], [-47.157, 0.0, 7.511], [-47.209, 0.0, -6.195], [-43.776, 0.0, -19.451], [-36.112, 0.0, -31.134], [-26.009, 0.0, -39.961], [-13.56, 0.0, -45.63], [0.0, 0.0, -47.66], [13.56, 0.0, -45.63], [26.009, 0.0, -39.961], [36.112, 0.0, -31.134], [43.776, 0.0, -19.451], [47.209, 0.0, -6.195], [47.157, 0.0, 7.511], [42.968, 0.0, 20.627], [35.492, 0.0, 31.953], [25.594, 0.0, 40.072], [16.907, 0.0, 44.279], [11.7, 0.0, 45.484]],d=3)
    main_crv_assembly.append(main_crv_a)
    main_crv_b = cmds.curve(name=name + 'direction', p=[[-11.7, 0.0, 45.484], [-11.7, 0.0, 59.009], [-23.4, 0.0, 59.009], [0.0, 0.0, 82.409], [23.4, 0.0, 59.009], [11.7, 0.0, 59.009], [11.7, 0.0, 45.484]],d=1)
    main_crv_assembly.append(main_crv_b)
    main_crv = gtu_combine_curves_list(main_crv_assembly)
    
    # Rename Shapes
    shapes =  cmds.listRelatives(main_crv, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('main_ctrlCircle'))
    cmds.rename(shapes[1], "{0}Shape".format('main_ctrlArrow'))
    
    return main_crv


def validate_operation(operation, debugging=False):
    ''' 
    Validates the necessary objects before executing a big function
    
            Parameters:
                operation (string): Name of the desired operation. e.g. "create_proxy" or "create_controls"
                debugging (bool): Debugging mode causes the script to auto delete previous objects (for quick iteration)

    '''
    is_valid = True
    if operation == 'create_proxy':
        # Debugging (Auto deletes generated proxy)
        if debugging:
            try:
                cmds.delete(gt_ab_settings_default.get('main_proxy_grp'))
            except:
                pass

        # Check if proxy exists in the scene
        proxy_elements = [gt_ab_settings_default.get('main_proxy_grp')]
        for proxy in gt_ab_settings_default:
            if '_crv' in proxy:
                proxy_elements.append(gt_ab_settings_default.get(proxy))
        for obj in proxy_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. Proxy creation already in progress. Delete current proxy or generate a rig before creating a new one.')
                
        # Check for existing rig or conflicting names
        undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
        for jnt in gt_ab_joints_default:
            undesired_elements.append(gt_ab_joints_default.get(jnt))
        for obj in undesired_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. This means that you either already created a rig or you have conflicting names on your objects. (Click on "Help" for more details)')
        
        # If valid, create proxy
        if is_valid:
            function_name = 'GT Auto Biped - Create Proxy'
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            try:
                create_proxy()
            except Exception as e:
                cmds.warning(str(e))
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=function_name)
                
    elif operation == 'create_controls':
        # Debugging (Auto deletes generated rig)
        if debugging:
            try:
                cmds.delete('rig_grp')
            except:
                pass
                    
        # Validate Proxy
        if not cmds.objExists(gt_ab_settings.get('main_proxy_grp')):
            is_valid = False
            cmds.warning('Proxy couldn\'t be found. Make sure you first create a proxy (guide objects) before generating a rig.')
        
        proxy_elements = [gt_ab_settings.get('main_proxy_grp')]
        for proxy in gt_ab_settings_default:
            if '_crv' in proxy:
                proxy_elements.append(gt_ab_settings.get(proxy))
        for obj in proxy_elements:
            if not cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.')
 
        # If valid, create rig
        if is_valid:
            function_name = 'GT Auto Biped - Create Rig'
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            try:
                create_controls()
            except Exception as e:
                cmds.warning(str(e))
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=function_name)


def create_proxy(colorize_proxy=True):
    ''' 
    Creates a proxy (guide) skeleton used to later generate entire rig 
    
            Parameters:
                colorize_proxy (bool): Whether or not proxy elements will be colorized (outliner and viewport color)
    
    '''
    proxy_finger_scale = 0.3
    proxy_end_joint_scale = 0.2
 
    if cmds.objExists('auto_biped_main'):
        is_valid = False
        cmds.warning('Proxy creation already in progress, please finish it first.')

    # Main
    main_crv = create_main_control(gt_ab_settings_default.get('main_crv'))
    main_grp = cmds.group(empty=True, world=True, name=gt_ab_settings_default.get('main_proxy_grp'))
    cmds.parent(main_crv, main_grp)

    # Root
    cog_proxy_crv = create_joint_curve(gt_ab_settings_default.get('cog_proxy_crv'), 1)
    root_proxy_grp = cmds.group(empty=True, world=True, name=cog_proxy_crv + grp_suffix.capitalize())
    cmds.parent(cog_proxy_crv, root_proxy_grp)
    cmds.move(0, 89.2, 0, root_proxy_grp)

    # Spine 1
    spine01_proxy_crv = create_joint_curve(gt_ab_settings_default.get('spine01_proxy_crv'), 0.5)
    spine01_proxy_grp = cmds.group(empty=True, world=True, name=spine01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(spine01_proxy_crv, spine01_proxy_grp)
    cmds.move(0, 98.5, 0, spine01_proxy_grp)

    # Spine 2
    spine02_proxy_crv = create_joint_curve(gt_ab_settings_default.get('spine02_proxy_crv'), 0.5)
    spine02_proxy_grp = cmds.group(empty=True, world=True, name=spine02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(spine02_proxy_crv, spine02_proxy_grp)
    cmds.move(0, 108.2, 0, spine02_proxy_grp)

    # Spine 3
    spine03_proxy_crv = create_joint_curve(gt_ab_settings_default.get('spine03_proxy_crv'), 0.5)
    spine03_proxy_grp = cmds.group(empty=True, world=True, name=spine03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(spine03_proxy_crv, spine03_proxy_grp)
    cmds.move(0, 117.8, 0, spine03_proxy_grp)

    # Spine 4
    spine04_proxy_crv = create_joint_curve(gt_ab_settings_default.get('spine04_proxy_crv'), 1)
    spine04_proxy_grp = cmds.group(empty=True, world=True, name=spine04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(spine04_proxy_crv, spine04_proxy_grp)
    cmds.move(0, 127.5, 0, spine04_proxy_grp)

    # Neck Base
    neck_base_proxy_crv = create_joint_curve(gt_ab_settings_default.get('neck_base_proxy_crv'), .5)
    neck_base_proxy_grp = cmds.group(empty=True, world=True, name=neck_base_proxy_crv + grp_suffix.capitalize())
    cmds.parent(neck_base_proxy_crv, neck_base_proxy_grp)
    cmds.move(0, 137.1, 0, neck_base_proxy_grp)
    
    # Neck Mid
    neck_mid_proxy_crv = create_joint_curve(gt_ab_settings_default.get('neck_mid_proxy_crv'), .2)
    neck_mid_proxy_grp = cmds.group(empty=True, world=True, name=neck_mid_proxy_crv + grp_suffix.capitalize())
    cmds.parent(neck_mid_proxy_crv, neck_mid_proxy_grp)
    cmds.move(0, 139.8, 0, neck_mid_proxy_grp)

    # Head
    head_proxy_crv = create_joint_curve(gt_ab_settings_default.get('head_proxy_crv'), .5)
    head_proxy_grp = cmds.group(empty=True, world=True, name=head_proxy_crv + grp_suffix.capitalize())
    cmds.parent(head_proxy_crv, head_proxy_grp)
    cmds.move(0, 142.4, 0, head_proxy_grp)

    # Head End
    head_end_proxy_crv = create_joint_curve(gt_ab_settings_default.get('head_end_proxy_crv'), .2) 
    head_end_proxy_grp = cmds.group(empty=True, world=True, name=head_end_proxy_crv + grp_suffix.capitalize())
    cmds.parent(head_end_proxy_crv, head_end_proxy_grp)
    cmds.move(0, 160, 0, head_end_proxy_grp)

    # Jaw
    jaw_proxy_crv = create_joint_curve(gt_ab_settings_default.get('jaw_proxy_crv'), .5)
    jaw_proxy_grp = cmds.group(empty=True, world=True, name=jaw_proxy_crv + grp_suffix.capitalize())
    cmds.parent(jaw_proxy_crv, jaw_proxy_grp)
    cmds.move(0, 147.4, 2.35, jaw_proxy_grp)

    # Jaw End
    jaw_end_proxy_crv = create_joint_curve(gt_ab_settings_default.get('jaw_end_proxy_crv'), .2)
    jaw_end_proxy_grp = cmds.group(empty=True, world=True, name=jaw_end_proxy_crv + grp_suffix.capitalize())
    cmds.parent(jaw_end_proxy_crv, jaw_end_proxy_grp)
    cmds.move(0, 142.7, 10.8, jaw_end_proxy_grp)

    # Right Eye
    right_eye_proxy_crv = create_loc_joint_curve(gt_ab_settings_default.get('right_eye_proxy_crv'), .6)
    right_eye_proxy_grp = cmds.group(empty=True, world=True, name=right_eye_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_eye_proxy_crv, right_eye_proxy_grp)
    cmds.move(-3.5, 151.2, 8.7, right_eye_proxy_grp)

    # Left Eye
    left_eye_proxy_crv = create_loc_joint_curve(gt_ab_settings_default.get('left_eye_proxy_crv'), .6)
    left_eye_proxy_grp = cmds.group(empty=True, world=True, name=left_eye_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_eye_proxy_crv, left_eye_proxy_grp)
    cmds.move(3.5, 151.2, 8.7, left_eye_proxy_grp)


    ################# Left Arm #################
    # Left Clavicle
    left_clavicle_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_clavicle_proxy_crv'), .5)
    left_clavicle_proxy_grp = cmds.group(empty=True, world=True, name=left_clavicle_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_clavicle_proxy_crv, left_clavicle_proxy_grp)
    cmds.move(7.3, 130.4, 0, left_clavicle_proxy_grp)

    # Left Shoulder
    left_shoulder_proxy_crv = create_joint_curve(gt_ab_settings_default.get('left_shoulder_proxy_crv'), .5)
    left_shoulder_proxy_grp = cmds.group(empty=True, world=True, name=left_shoulder_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_shoulder_proxy_crv, left_shoulder_proxy_grp)
    cmds.move(17.2, 130.4, 0, left_shoulder_proxy_grp)

    # Left Elbow
    left_elbow_proxy_crv = create_aim_joint_curve(gt_ab_settings_default.get('left_elbow_proxy_crv'), .5)
    left_elbow_proxy_grp = cmds.group(empty=True, world=True, name=left_elbow_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_elbow_proxy_crv, left_elbow_proxy_grp)
    cmds.move(37.7, 130.4, 0, left_elbow_proxy_grp)

    # Left Wrist
    left_wrist_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_wrist_proxy_crv'), .6)
    left_wrist_proxy_grp = cmds.group(empty=True, world=True, name=left_wrist_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_wrist_proxy_crv, left_wrist_proxy_grp)
    cmds.move(58.2, 130.4, 0, left_wrist_proxy_grp)


    # Left Thumb
    left_thumb01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_thumb01_proxy_crv'), proxy_finger_scale)
    left_thumb01_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_thumb01_proxy_crv, left_thumb01_proxy_grp)
    cmds.move(60.8, 130.4, 2.9, left_thumb01_proxy_grp)

    left_thumb02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_thumb02_proxy_crv'), proxy_finger_scale)
    left_thumb02_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_thumb02_proxy_crv, left_thumb02_proxy_grp)
    cmds.move(60.8, 130.4, 7.3, left_thumb02_proxy_grp)

    left_thumb03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_thumb03_proxy_crv'), proxy_finger_scale)
    left_thumb03_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_thumb03_proxy_crv, left_thumb03_proxy_grp)
    cmds.move(60.8, 130.4, 11.7, left_thumb03_proxy_grp)

    left_thumb04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_thumb04_proxy_crv'), proxy_end_joint_scale)
    left_thumb04_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_thumb04_proxy_crv, left_thumb04_proxy_grp)
    cmds.move(60.8, 130.4, 16.3, left_thumb04_proxy_grp)

    # Left Index
    left_index01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_index01_proxy_crv'), proxy_finger_scale)
    left_index01_proxy_grp = cmds.group(empty=True, world=True, name=left_index01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_index01_proxy_crv, left_index01_proxy_grp)
    cmds.move(66.9, 130.4, 3.5, left_index01_proxy_grp)

    left_index02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_index02_proxy_crv'), proxy_finger_scale)
    left_index02_proxy_grp = cmds.group(empty=True, world=True, name=left_index02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_index02_proxy_crv, left_index02_proxy_grp)
    cmds.move(70.1, 130.4, 3.5, left_index02_proxy_grp)

    left_index03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_index03_proxy_crv'), proxy_finger_scale)
    left_index03_proxy_grp = cmds.group(empty=True, world=True, name=left_index03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_index03_proxy_crv, left_index03_proxy_grp)
    cmds.move(74.2, 130.4, 3.5, left_index03_proxy_grp)

    left_index04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_index04_proxy_crv'), proxy_end_joint_scale)
    left_index04_proxy_grp = cmds.group(empty=True, world=True, name=left_index04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_index04_proxy_crv, left_index04_proxy_grp)
    cmds.move(77.5, 130.4, 3.5, left_index04_proxy_grp)


    # Left Middle
    left_middle01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_middle01_proxy_crv'), proxy_finger_scale)
    left_middle01_proxy_grp = cmds.group(empty=True, world=True, name=left_middle01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_middle01_proxy_crv, left_middle01_proxy_grp)
    cmds.move(66.9, 130.4, 1.1, left_middle01_proxy_grp)

    left_middle02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_middle02_proxy_crv'), proxy_finger_scale)
    left_middle02_proxy_grp = cmds.group(empty=True, world=True, name=left_middle02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_middle02_proxy_crv, left_middle02_proxy_grp)
    cmds.move(70.7, 130.4, 1.1, left_middle02_proxy_grp)

    left_middle03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_middle03_proxy_crv'), proxy_finger_scale)
    left_middle03_proxy_grp = cmds.group(empty=True, world=True, name=left_middle03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_middle03_proxy_crv, left_middle03_proxy_grp)
    cmds.move(74.4, 130.4, 1.1, left_middle03_proxy_grp)

    left_middle04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_middle04_proxy_crv'), proxy_end_joint_scale)
    left_middle04_proxy_grp = cmds.group(empty=True, world=True, name=left_middle04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_middle04_proxy_crv, left_middle04_proxy_grp)
    cmds.move(78.0, 130.4, 1.1, left_middle04_proxy_grp)
        
        
    # Left Ring
    left_ring01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_ring01_proxy_crv'), proxy_finger_scale)
    left_ring01_proxy_grp = cmds.group(empty=True, world=True, name=left_ring01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ring01_proxy_crv, left_ring01_proxy_grp)
    cmds.move(66.9, 130.4, -1.1, left_ring01_proxy_grp)

    left_ring02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_ring02_proxy_crv'), proxy_finger_scale)
    left_ring02_proxy_grp = cmds.group(empty=True, world=True, name=left_ring02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ring02_proxy_crv, left_ring02_proxy_grp)
    cmds.move(70.4, 130.4, -1.1, left_ring02_proxy_grp)

    left_ring03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_ring03_proxy_crv'), proxy_finger_scale)
    left_ring03_proxy_grp = cmds.group(empty=True, world=True, name=left_ring03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ring03_proxy_crv, left_ring03_proxy_grp)
    cmds.move(74, 130.4, -1.1, left_ring03_proxy_grp)

    left_ring04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_ring04_proxy_crv'), proxy_end_joint_scale)
    left_ring04_proxy_grp = cmds.group(empty=True, world=True, name=left_ring04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ring04_proxy_crv, left_ring04_proxy_grp)
    cmds.move(77.5, 130.4, -1.1, left_ring04_proxy_grp)


    # Left Pinky
    left_pinky01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_pinky01_proxy_crv'), proxy_finger_scale)
    left_pinky01_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_pinky01_proxy_crv, left_pinky01_proxy_grp)
    cmds.move(66.3, 130.4, -3.2, left_pinky01_proxy_grp)

    left_pinky02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_pinky02_proxy_crv'), proxy_finger_scale)
    left_pinky02_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_pinky02_proxy_crv, left_pinky02_proxy_grp)
    cmds.move(69.6, 130.4, -3.2, left_pinky02_proxy_grp)

    left_pinky03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_pinky03_proxy_crv'), proxy_finger_scale)
    left_pinky03_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_pinky03_proxy_crv, left_pinky03_proxy_grp)
    cmds.move(72.8, 130.4, -3.2, left_pinky03_proxy_grp)

    left_pinky04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('left_pinky04_proxy_crv'), proxy_end_joint_scale)
    left_pinky04_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_pinky04_proxy_crv, left_pinky04_proxy_grp)
    cmds.move(76.3, 130.4, -3.2, left_pinky04_proxy_grp)
        

    ################# Right Arm #################
    # Right Clavicle
    right_clavicle_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_clavicle_proxy_crv'), .5)
    right_clavicle_proxy_grp = cmds.group(empty=True, world=True, name=right_clavicle_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_clavicle_proxy_crv, right_clavicle_proxy_grp)
    cmds.move(-7.3, 130.4, 0, right_clavicle_proxy_grp)

    # Right Shoulder
    right_shoulder_proxy_crv = create_joint_curve(gt_ab_settings_default.get('right_shoulder_proxy_crv'), .5)
    right_shoulder_proxy_grp = cmds.group(empty=True, world=True, name=right_shoulder_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_shoulder_proxy_crv, right_shoulder_proxy_grp)
    cmds.move(-17.2, 130.4, 0, right_shoulder_proxy_grp)

    # Right Elbow
    right_elbow_proxy_crv = create_aim_joint_curve(gt_ab_settings_default.get('right_elbow_proxy_crv'), .5)
    right_elbow_proxy_grp = cmds.group(empty=True, world=True, name=right_elbow_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_elbow_proxy_crv, right_elbow_proxy_grp)
    cmds.move(-37.7, 130.4, 0, right_elbow_proxy_grp)


    # Right Wrist
    right_wrist_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_wrist_proxy_crv'), .6)
    right_wrist_proxy_grp = cmds.group(empty=True, world=True, name=right_wrist_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_wrist_proxy_crv, right_wrist_proxy_grp)
    cmds.move(-58.2, 130.4, 0, right_wrist_proxy_grp)


    # Right Thumb
    right_thumb01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_thumb01_proxy_crv'), proxy_finger_scale)
    right_thumb01_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_thumb01_proxy_crv, right_thumb01_proxy_grp)
    cmds.move(-60.8, 130.4, 2.9, right_thumb01_proxy_grp)

    right_thumb02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_thumb02_proxy_crv'), proxy_finger_scale)
    right_thumb02_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_thumb02_proxy_crv, right_thumb02_proxy_grp)
    cmds.move(-60.8, 130.4, 7.3, right_thumb02_proxy_grp)

    right_thumb03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_thumb03_proxy_crv'), proxy_finger_scale)
    right_thumb03_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_thumb03_proxy_crv, right_thumb03_proxy_grp)
    cmds.move(-60.8, 130.4, 11.7, right_thumb03_proxy_grp)

    right_thumb04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_thumb04_proxy_crv'), proxy_end_joint_scale)
    right_thumb04_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_thumb04_proxy_crv, right_thumb04_proxy_grp)
    cmds.move(-60.8, 130.4, 16.3, right_thumb04_proxy_grp)

    # Right Index
    right_index01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_index01_proxy_crv'), proxy_finger_scale)
    right_index01_proxy_grp = cmds.group(empty=True, world=True, name=right_index01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_index01_proxy_crv, right_index01_proxy_grp)
    cmds.move(-66.9, 130.4, 3.5, right_index01_proxy_grp)

    right_index02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_index02_proxy_crv'), proxy_finger_scale)
    right_index02_proxy_grp = cmds.group(empty=True, world=True, name=right_index02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_index02_proxy_crv, right_index02_proxy_grp)
    cmds.move(-70.1, 130.4, 3.5, right_index02_proxy_grp)

    right_index03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_index03_proxy_crv'), proxy_finger_scale)
    right_index03_proxy_grp = cmds.group(empty=True, world=True, name=right_index03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_index03_proxy_crv, right_index03_proxy_grp)
    cmds.move(-74.2, 130.4, 3.5, right_index03_proxy_grp)

    right_index04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_index04_proxy_crv'), proxy_end_joint_scale)
    right_index04_proxy_grp = cmds.group(empty=True, world=True, name=right_index04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_index04_proxy_crv, right_index04_proxy_grp)
    cmds.move(-77.5, 130.4, 3.5, right_index04_proxy_grp)


    # Right Middle
    right_middle01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_middle01_proxy_crv'), proxy_finger_scale)
    right_middle01_proxy_grp = cmds.group(empty=True, world=True, name=right_middle01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_middle01_proxy_crv, right_middle01_proxy_grp)
    cmds.move(-66.9, 130.4, 1.1, right_middle01_proxy_grp)

    right_middle02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_middle02_proxy_crv'), proxy_finger_scale)
    right_middle02_proxy_grp = cmds.group(empty=True, world=True, name=right_middle02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_middle02_proxy_crv, right_middle02_proxy_grp)
    cmds.move(-70.7, 130.4, 1.1, right_middle02_proxy_grp)

    right_middle03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_middle03_proxy_crv'), proxy_finger_scale)
    right_middle03_proxy_grp = cmds.group(empty=True, world=True, name=right_middle03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_middle03_proxy_crv, right_middle03_proxy_grp)
    cmds.move(-74.4, 130.4, 1.1, right_middle03_proxy_grp)

    right_middle04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_middle04_proxy_crv'), proxy_end_joint_scale)
    right_middle04_proxy_grp = cmds.group(empty=True, world=True, name=right_middle04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_middle04_proxy_crv, right_middle04_proxy_grp)
    cmds.move(-78, 130.4, 1.1, right_middle04_proxy_grp)
        
        
    # Right Ring
    right_ring01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_ring01_proxy_crv'), proxy_finger_scale)
    right_ring01_proxy_grp = cmds.group(empty=True, world=True, name=right_ring01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ring01_proxy_crv, right_ring01_proxy_grp)
    cmds.move(-66.9, 130.4, -1.1, right_ring01_proxy_grp)

    right_ring02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_ring02_proxy_crv'), proxy_finger_scale)
    right_ring02_proxy_grp = cmds.group(empty=True, world=True, name=right_ring02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ring02_proxy_crv, right_ring02_proxy_grp)
    cmds.move(-70.4, 130.4, -1.1, right_ring02_proxy_grp)

    right_ring03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_ring03_proxy_crv'), proxy_finger_scale)
    right_ring03_proxy_grp = cmds.group(empty=True, world=True, name=right_ring03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ring03_proxy_crv, right_ring03_proxy_grp)
    cmds.move(-74, 130.4, -1.1, right_ring03_proxy_grp)

    right_ring04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_ring04_proxy_crv'), proxy_end_joint_scale)
    right_ring04_proxy_grp = cmds.group(empty=True, world=True, name=right_ring04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ring04_proxy_crv, right_ring04_proxy_grp)
    cmds.move(-77.5, 130.4, -1.1, right_ring04_proxy_grp)


    # Right Pinky
    right_pinky01_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_pinky01_proxy_crv'), proxy_finger_scale)
    right_pinky01_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky01_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_pinky01_proxy_crv, right_pinky01_proxy_grp)
    cmds.move(-66.3, 130.4, -3.2, right_pinky01_proxy_grp)

    right_pinky02_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_pinky02_proxy_crv'), proxy_finger_scale)
    right_pinky02_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky02_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_pinky02_proxy_crv, right_pinky02_proxy_grp)
    cmds.move(-69.6, 130.4, -3.2, right_pinky02_proxy_grp)

    right_pinky03_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_pinky03_proxy_crv'), proxy_finger_scale)
    right_pinky03_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky03_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_pinky03_proxy_crv, right_pinky03_proxy_grp)
    cmds.move(-72.8, 130.4, -3.2, right_pinky03_proxy_grp)

    right_pinky04_proxy_crv = create_directional_joint_curve(gt_ab_settings_default.get('right_pinky04_proxy_crv'), proxy_end_joint_scale)
    right_pinky04_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky04_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_pinky04_proxy_crv, right_pinky04_proxy_grp)
    cmds.move(-76.3, 130.4, -3.2, right_pinky04_proxy_grp)


    # Hip
    hip_proxy_crv = create_joint_curve(gt_ab_settings_default.get('hip_proxy_crv'), .4)
    hip_proxy_grp = cmds.group(empty=True, world=True, name=hip_proxy_crv + grp_suffix.capitalize())
    cmds.parent(hip_proxy_crv, hip_proxy_grp)
    cmds.move(0, 84.5, 0, hip_proxy_grp)
        
    ################# Left Leg #################
    # Left Hip
    left_hip_proxy_crv = create_joint_curve(gt_ab_settings_default.get('left_hip_proxy_crv'), .4)
    left_hip_proxy_grp = cmds.group(empty=True, world=True, name=left_hip_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_hip_proxy_crv, left_hip_proxy_grp)
    cmds.move(10.2, 84.5, 0, left_hip_proxy_grp)

    # Left Knee
    left_knee_proxy_crv = create_aim_joint_curve(gt_ab_settings_default.get('left_knee_proxy_crv'), .5)
    cmds.rotate(0, 180, 90, left_knee_proxy_crv)
    cmds.makeIdentity(left_knee_proxy_crv, apply=True, translate=True, scale=True, rotate=True)
    left_knee_proxy_grp = cmds.group(empty=True, world=True, name=left_knee_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_knee_proxy_crv, left_knee_proxy_grp)
    cmds.move(10.2, 46.8, 0, left_knee_proxy_grp)

    # Left Ankle
    left_ankle_proxy_crv = create_joint_curve(gt_ab_settings_default.get('left_ankle_proxy_crv'), .4)
    left_ankle_proxy_grp = cmds.group(empty=True, world=True, name=left_ankle_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ankle_proxy_crv, left_ankle_proxy_grp)
    cmds.move(10.2, 9.6, 0, left_ankle_proxy_grp)

    # Left Ball
    left_ball_proxy_crv = create_joint_curve(gt_ab_settings_default.get('left_ball_proxy_crv'), .4)
    left_ball_proxy_grp = cmds.group(empty=True, world=True, name=left_ball_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_ball_proxy_crv, left_ball_proxy_grp)
    cmds.move(10.2, 0, 13.1, left_ball_proxy_grp)

    # Left Toe
    left_toe_proxy_crv = create_joint_curve(gt_ab_settings_default.get('left_toe_proxy_crv'), .35)
    left_toe_proxy_grp = cmds.group(empty=True, world=True, name=left_toe_proxy_crv + grp_suffix.capitalize())
    cmds.parent(left_toe_proxy_crv, left_toe_proxy_grp)
    cmds.move(10.2, 0, 23.4, left_toe_proxy_grp)


    ################# Right Leg #################
    # Right Hip
    right_hip_proxy_crv = create_joint_curve(gt_ab_settings_default.get('right_hip_proxy_crv'), .4)
    right_hip_proxy_grp = cmds.group(empty=True, world=True, name=right_hip_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_hip_proxy_crv, right_hip_proxy_grp)
    cmds.move(-10.2, 84.5, 0, right_hip_proxy_grp)

    # Right Knee
    right_knee_proxy_crv = create_aim_joint_curve(gt_ab_settings_default.get('right_knee_proxy_crv'), .5)
    cmds.rotate(0, 180, 90, right_knee_proxy_crv)
    cmds.makeIdentity(right_knee_proxy_crv, apply=True, translate=True, scale=True, rotate=True)
    right_knee_proxy_grp = cmds.group(empty=True, world=True, name=right_knee_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_knee_proxy_crv, right_knee_proxy_grp)
    cmds.move(-1.75, 8, 0, right_knee_proxy_grp)

    # Right Ankle
    right_ankle_proxy_crv = create_joint_curve(gt_ab_settings_default.get('right_ankle_proxy_crv'), .4)
    right_ankle_proxy_grp = cmds.group(empty=True, world=True, name=right_ankle_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ankle_proxy_crv, right_ankle_proxy_grp)
    cmds.move(-10.2, 9.6, 0, right_ankle_proxy_grp)

    # Right Ball
    right_ball_proxy_crv = create_joint_curve(gt_ab_settings_default.get('right_ball_proxy_crv'), .4)
    right_ball_proxy_grp = cmds.group(empty=True, world=True, name=right_ball_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_ball_proxy_crv, right_ball_proxy_grp)
    cmds.move(-10.2, 0, 13.1, right_ball_proxy_grp)

    # Right Toe
    right_toe_proxy_crv = create_joint_curve(gt_ab_settings_default.get('right_toe_proxy_crv'), .35)
    right_toe_proxy_grp = cmds.group(empty=True, world=True, name=right_toe_proxy_crv + grp_suffix.capitalize())
    cmds.parent(right_toe_proxy_crv, right_toe_proxy_grp)
    cmds.move(-10.2, 0, 23.4, right_toe_proxy_grp)

        
    # Assemble Hierarchy
    cmds.parent(root_proxy_grp, main_crv)
    
    cmds.parent(spine01_proxy_grp, main_crv)
    cmds.parent(spine02_proxy_grp, main_crv)
    cmds.parent(spine03_proxy_grp, main_crv)
    cmds.parent(spine04_proxy_grp, main_crv)
    
    cmds.parent(left_shoulder_proxy_grp, left_clavicle_proxy_crv)
    cmds.parent(right_shoulder_proxy_grp, right_clavicle_proxy_crv)
    
    cmds.parent(hip_proxy_grp, cog_proxy_crv)
    cmds.parent(left_hip_proxy_grp, hip_proxy_grp)
    cmds.parent(right_hip_proxy_grp, hip_proxy_grp)
    
    # Neck and Head
    cmds.parent(neck_base_proxy_grp, spine04_proxy_crv)
    cmds.parent(neck_mid_proxy_grp, neck_base_proxy_crv)
    cmds.parent(head_proxy_grp, neck_base_proxy_crv)
    cmds.parent(jaw_proxy_grp, head_proxy_crv)
    cmds.parent(jaw_end_proxy_grp, jaw_proxy_crv)
    cmds.parent(head_end_proxy_grp, head_proxy_crv)
    cmds.parent(left_eye_proxy_grp, head_proxy_crv)
    cmds.parent(right_eye_proxy_grp, head_proxy_crv)
    
    # Arms
    cmds.parent(left_clavicle_proxy_grp, spine04_proxy_crv)
    cmds.parent(right_clavicle_proxy_grp, spine04_proxy_crv)
    
    cmds.parent(left_elbow_proxy_grp, main_crv)
    cmds.parent(left_wrist_proxy_grp, main_crv)

    cmds.parent(right_elbow_proxy_grp, main_crv)
    cmds.parent(right_wrist_proxy_grp, main_crv)
    
    # Legs
    cmds.parent(left_hip_proxy_grp, main_crv)
    cmds.parent(left_knee_proxy_grp, main_crv)
    cmds.parent(left_ankle_proxy_grp, main_crv)
    
    cmds.parent(right_hip_proxy_grp, main_crv)
    cmds.parent(right_knee_proxy_grp, main_crv)
    cmds.parent(right_ankle_proxy_grp, main_crv)
    
    # Fingers
    cmds.parent(left_thumb01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_thumb02_proxy_grp, left_thumb01_proxy_crv)
    cmds.parent(left_thumb03_proxy_grp, left_thumb02_proxy_crv)
    cmds.parent(left_thumb04_proxy_grp, left_thumb03_proxy_crv)
    
    cmds.parent(left_index01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_index02_proxy_grp, left_index01_proxy_crv)
    cmds.parent(left_index03_proxy_grp, left_index02_proxy_crv)
    cmds.parent(left_index04_proxy_grp, left_index03_proxy_crv)
    
    cmds.parent(left_middle01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_middle02_proxy_grp, left_middle01_proxy_crv)
    cmds.parent(left_middle03_proxy_grp, left_middle02_proxy_crv)
    cmds.parent(left_middle04_proxy_grp, left_middle03_proxy_crv)
    
    cmds.parent(left_ring01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_ring02_proxy_grp, left_ring01_proxy_crv)
    cmds.parent(left_ring03_proxy_grp, left_ring02_proxy_crv)
    cmds.parent(left_ring04_proxy_grp, left_ring03_proxy_crv)
    
    cmds.parent(left_pinky01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_pinky02_proxy_grp, left_pinky01_proxy_crv)
    cmds.parent(left_pinky03_proxy_grp, left_pinky02_proxy_crv)
    cmds.parent(left_pinky04_proxy_grp, left_pinky03_proxy_crv)
    
    cmds.parent(right_thumb01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_thumb02_proxy_grp, right_thumb01_proxy_crv)
    cmds.parent(right_thumb03_proxy_grp, right_thumb02_proxy_crv)
    cmds.parent(right_thumb04_proxy_grp, right_thumb03_proxy_crv)
    
    cmds.parent(right_index01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_index02_proxy_grp, right_index01_proxy_crv)
    cmds.parent(right_index03_proxy_grp, right_index02_proxy_crv)
    cmds.parent(right_index04_proxy_grp, right_index03_proxy_crv)
    
    cmds.parent(right_middle01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_middle02_proxy_grp, right_middle01_proxy_crv)
    cmds.parent(right_middle03_proxy_grp, right_middle02_proxy_crv)
    cmds.parent(right_middle04_proxy_grp, right_middle03_proxy_crv)
    
    cmds.parent(right_ring01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_ring02_proxy_grp, right_ring01_proxy_crv)
    cmds.parent(right_ring03_proxy_grp, right_ring02_proxy_crv)
    cmds.parent(right_ring04_proxy_grp, right_ring03_proxy_crv)
    
    cmds.parent(right_pinky01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_pinky02_proxy_grp, right_pinky01_proxy_crv)
    cmds.parent(right_pinky03_proxy_grp, right_pinky02_proxy_crv)
    cmds.parent(right_pinky04_proxy_grp, right_pinky03_proxy_crv)
    
    
    # Constrain Spine Joints
    pc_s1 = cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine01_proxy_grp, offset=(0, 0, 0), skip='x')
    cmds.setAttr(pc_s1[0] + '.' + cog_proxy_crv + 'W0', 3)
    
    cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine02_proxy_grp, offset=(0, 0, 0), skip='x')

    pc_s3 = cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine03_proxy_grp, offset=(0, 0, 0), skip='x')
    cmds.setAttr(pc_s3[0] + '.' + spine04_proxy_crv + 'W1', 3)
    
    # Constraint Neck Mid
    cmds.pointConstraint([neck_base_proxy_crv, head_proxy_crv], neck_mid_proxy_grp, offset=(0, 0, 0), skip='x')
    
    # Constrain Left Elbow Between Shoulder and Wrist
    cmds.pointConstraint([left_shoulder_proxy_crv, left_wrist_proxy_crv], left_elbow_proxy_grp)
    cmds.pointConstraint([right_shoulder_proxy_crv, right_wrist_proxy_crv], right_elbow_proxy_grp)
        
    # Constraint Left Knee Between Hip and Ankle
    cmds.pointConstraint([left_hip_proxy_crv, left_ankle_proxy_crv], left_knee_proxy_grp)
    cmds.pointConstraint([right_hip_proxy_crv, right_ankle_proxy_crv], right_knee_proxy_grp)
    
    cmds.parent(left_toe_proxy_grp, left_ball_proxy_crv)
    cmds.parent(left_ball_proxy_grp, left_ankle_proxy_crv)
    cmds.parent(right_toe_proxy_grp, right_ball_proxy_crv)
    cmds.parent(right_ball_proxy_grp, right_ankle_proxy_crv)
    
    # Left Elbow Constraints
    # Left Elbow Pole Vector Dir
    left_elbow_pv_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_elbow_pv_dir') )
    cmds.delete(cmds.pointConstraint(gt_ab_settings_default.get('left_elbow_proxy_crv'), left_elbow_pv_loc[0]))
    cmds.parent(left_elbow_pv_loc[0], gt_ab_settings_default.get('left_elbow_proxy_crv'))
    cmds.move(0,0,-9.6, left_elbow_pv_loc[0], relative=True)
    
    left_elbow_dir_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_elbow_dir_loc') )
    left_elbow_aim_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_elbow_aim_loc') )
    left_elbow_upvec_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_elbow_upvec_loc') )
    left_elbow_upvec_loc_grp = cmds.group(empty=True, world=True, name=left_elbow_upvec_loc[0] + grp_suffix.capitalize())
    
    cmds.parent(left_elbow_aim_loc, left_elbow_dir_loc)
    cmds.parent(left_elbow_dir_loc, main_crv)
    cmds.parent(left_elbow_upvec_loc, left_elbow_upvec_loc_grp)
    cmds.parent(left_elbow_upvec_loc_grp, main_crv)
    
    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_dir_loc)
    cmds.pointConstraint([left_wrist_proxy_crv, left_shoulder_proxy_crv], left_elbow_aim_loc)
    cmds.aimConstraint(left_wrist_proxy_crv, left_elbow_dir_loc)
    
    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_upvec_loc_grp, skip=['x','z'])
    
    left_elbow_divide_node = cmds.createNode('multiplyDivide', name=gt_ab_settings_default.get('left_elbow_divide_node'))
    
    cmds.setAttr(left_elbow_divide_node + '.operation', 2) # Make Divide
    cmds.setAttr(left_elbow_divide_node + '.input2X', -2)
    cmds.connectAttr(left_wrist_proxy_crv + '.ty', left_elbow_divide_node + '.input1X')
    cmds.connectAttr(left_elbow_divide_node + '.outputX', left_elbow_upvec_loc[0] + '.ty', force=True)
    
    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_dir_loc)
    cmds.pointConstraint([left_shoulder_proxy_crv, left_wrist_proxy_crv], left_elbow_aim_loc[0])
    
    cmds.connectAttr(left_elbow_dir_loc[0] + '.rotate', left_elbow_proxy_grp + '.rotate')

    cmds.aimConstraint(left_wrist_proxy_crv, left_elbow_dir_loc[0], aimVector=(1,0,0), upVector=(-1,0,0), worldUpType='object', worldUpObject=left_elbow_upvec_loc[0])
    cmds.aimConstraint(left_elbow_aim_loc[0], left_elbow_proxy_crv, aimVector=(0,0,1), upVector=(0,1,0), worldUpType='none', skip=['y', 'z']) # Possible Issue

    # Right Elbow Constraints
    # Right Elbow Pole Vector Dir
    right_elbow_pv_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_elbow_pv_dir') )
    cmds.delete(cmds.pointConstraint(gt_ab_settings_default.get('right_elbow_proxy_crv'), right_elbow_pv_loc[0]))
    cmds.parent(right_elbow_pv_loc[0], gt_ab_settings_default.get('right_elbow_proxy_crv'))
    cmds.move(0,0,-9.6, right_elbow_pv_loc[0], relative=True)
    
    right_elbow_dir_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_elbow_dir_loc') )
    right_elbow_aim_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_elbow_aim_loc') )
    right_elbow_upvec_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_elbow_upvec_loc') )
    right_elbow_upvec_loc_grp = cmds.group(empty=True, world=True, name=right_elbow_upvec_loc[0] + grp_suffix.capitalize())
    
    cmds.parent(right_elbow_aim_loc, right_elbow_dir_loc)
    cmds.parent(right_elbow_dir_loc, main_crv)
    cmds.parent(right_elbow_upvec_loc, right_elbow_upvec_loc_grp)
    cmds.parent(right_elbow_upvec_loc_grp, main_crv)
    
    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_dir_loc)
    cmds.pointConstraint([right_wrist_proxy_crv, right_shoulder_proxy_crv], right_elbow_aim_loc)
    cmds.aimConstraint(right_wrist_proxy_crv, right_elbow_dir_loc)
    
    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_upvec_loc_grp, skip=['x','z'])
    
    right_elbow_divide_node = cmds.createNode('multiplyDivide', name=gt_ab_settings_default.get('right_elbow_divide_node'))
    
    cmds.setAttr(right_elbow_divide_node + '.operation', 2) # Make Divide
    cmds.setAttr(right_elbow_divide_node + '.input2X', -2)
    cmds.connectAttr(right_wrist_proxy_crv + '.ty', right_elbow_divide_node + '.input1X')
    cmds.connectAttr(right_elbow_divide_node + '.outputX', right_elbow_upvec_loc[0] + '.ty', force=True)
    
    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_dir_loc)
    cmds.pointConstraint([right_shoulder_proxy_crv, right_wrist_proxy_crv], right_elbow_aim_loc[0])
    
    cmds.connectAttr(right_elbow_dir_loc[0] + '.rotate', right_elbow_proxy_grp + '.rotate')

    cmds.aimConstraint(right_wrist_proxy_crv, right_elbow_dir_loc[0], aimVector=(-1,0,0), upVector=(1,0,0), worldUpType='object', worldUpObject=right_elbow_upvec_loc[0])
    cmds.aimConstraint(right_elbow_aim_loc[0], right_elbow_proxy_crv, aimVector=(0,0,1), upVector=(0,1,0), worldUpType='none', skip=['y', 'z']) # Possible Issue


    # Left Knee Setup
    left_knee_pv_dir = cmds.spaceLocator( name=gt_ab_settings_default.get('left_knee_pv_dir') )
    temp = cmds.pointConstraint(left_knee_proxy_crv, left_knee_pv_dir)
    cmds.delete(temp)
    cmds.move(0, 0, 12.9, left_knee_pv_dir, relative=True)
    cmds.parent(left_knee_pv_dir[0], left_knee_proxy_crv)
    

    # Right Knee Setup
    right_knee_pv_dir = cmds.spaceLocator( name=gt_ab_settings_default.get('right_knee_pv_dir') )
    temp = cmds.pointConstraint(right_knee_proxy_crv, right_knee_pv_dir)
    cmds.delete(temp)
    cmds.move(0, 0, 12.9, right_knee_pv_dir, relative=True)
    cmds.parent(right_knee_pv_dir[0], right_knee_proxy_crv)
    

    # Left Knee Constraints
    left_knee_dir_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_knee_dir_loc') )
    left_knee_aim_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_knee_aim_loc') )
    left_knee_upvec_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_knee_upvec_loc') )
    left_knee_upvec_loc_grp = cmds.group(empty=True, world=True, name=left_knee_upvec_loc[0] + grp_suffix.capitalize())
    cmds.parent(left_knee_upvec_loc, left_knee_upvec_loc_grp)
    cmds.parent(left_knee_upvec_loc_grp, main_crv)
    cmds.parent(left_knee_dir_loc[0], main_crv)
    cmds.parent(left_knee_aim_loc[0], left_knee_dir_loc[0])
    
    left_knee_divide_node = cmds.createNode('multiplyDivide', name=gt_ab_settings_default.get('left_knee_divide_node'))
    cmds.setAttr(left_knee_divide_node + '.operation', 2) # Make Divide
    cmds.setAttr(left_knee_divide_node + '.input2X', -2)
    cmds.connectAttr(left_ankle_proxy_crv + '.tx', left_knee_divide_node + '.input1X')
    cmds.connectAttr(left_knee_divide_node + '.outputX', left_knee_upvec_loc[0] + '.tx', force=True)

    cmds.move(0, 11.7, 0, left_knee_upvec_loc[0])
    cmds.pointConstraint(left_hip_proxy_crv, left_knee_upvec_loc_grp)
    cmds.pointConstraint(left_hip_proxy_crv, left_knee_dir_loc[0])
    cmds.pointConstraint([left_hip_proxy_crv, left_ankle_proxy_crv], left_knee_aim_loc[0])
    
    
    cmds.connectAttr(left_knee_dir_loc[0] + '.rotate', left_knee_proxy_grp + '.rotate', force=True)

    cmds.aimConstraint(left_ankle_proxy_crv, left_knee_dir_loc[0], aimVector=(0,-1,0), upVector=(0,-1,0), worldUpType='object', worldUpObject=left_knee_upvec_loc[0])
    cmds.aimConstraint(left_knee_aim_loc[0], left_knee_proxy_crv, aimVector=(0,0,-1), upVector=(0,1,0), worldUpType='none', skip=['x', 'z']) # Possible Issue


    # Right Knee Constraints
    right_knee_dir_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_knee_dir_loc') )
    right_knee_aim_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_knee_aim_loc') )
    right_knee_upvec_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_knee_upvec_loc') )
    right_knee_upvec_loc_grp = cmds.group(empty=True, world=True, name=right_knee_upvec_loc[0] + grp_suffix.capitalize())
    cmds.parent(right_knee_upvec_loc, right_knee_upvec_loc_grp)
    cmds.parent(right_knee_upvec_loc_grp, main_crv)
    cmds.parent(right_knee_dir_loc[0], main_crv)
    cmds.parent(right_knee_aim_loc[0], right_knee_dir_loc[0])
    
    right_knee_divide_node = cmds.createNode('multiplyDivide', name=gt_ab_settings_default.get('right_knee_divide_node'))
    cmds.setAttr(right_knee_divide_node + '.operation', 2) # Make Divide
    cmds.setAttr(right_knee_divide_node + '.input2X', -2)
    cmds.connectAttr(right_ankle_proxy_crv + '.tx', right_knee_divide_node + '.input1X')
    cmds.connectAttr(right_knee_divide_node + '.outputX', right_knee_upvec_loc[0] + '.tx', force=True)

    cmds.move(0, 11.7, 0, right_knee_upvec_loc[0])
    cmds.pointConstraint(right_hip_proxy_crv, right_knee_upvec_loc_grp)
    cmds.pointConstraint(right_hip_proxy_crv, right_knee_dir_loc[0])
    cmds.pointConstraint([right_hip_proxy_crv, right_ankle_proxy_crv], right_knee_aim_loc[0])
    
    
    cmds.connectAttr(right_knee_dir_loc[0] + '.rotate', right_knee_proxy_grp + '.rotate', force=True)

    cmds.aimConstraint(right_ankle_proxy_crv, right_knee_dir_loc[0], aimVector=(0,-1,0), upVector=(0,-1,0), worldUpType='object', worldUpObject=right_knee_upvec_loc[0])
    cmds.aimConstraint(right_knee_aim_loc[0], right_knee_proxy_crv, aimVector=(0,0,-1), upVector=(0,1,0), worldUpType='none', skip=['x', 'z']) # Possible Issue


    # Left Rolls
    left_ball_pivot_grp = cmds.group(empty=True, world=True, name=gt_ab_settings_default.get('left_ball_pivot_grp'))
    cmds.parent(left_ball_pivot_grp, main_crv)
    ankle_pos = cmds.xform(left_ankle_proxy_crv, q=True, ws=True, rp=True)
    cmds.move(ankle_pos[0], left_ball_pivot_grp, moveX=True)
    
    cmds.pointConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, maintainOffset=True, skip=['y'])
    cmds.orientConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, maintainOffset=True, skip=['x', 'z'])
    cmds.scaleConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, skip=['y'])
    cmds.parent(left_ball_proxy_grp, left_ball_pivot_grp)
    
    # Right Rolls
    right_ball_pivot_grp = cmds.group(empty=True, world=True, name=gt_ab_settings_default.get('right_ball_pivot_grp'))
    cmds.parent(right_ball_pivot_grp, main_crv)
    ankle_pos = cmds.xform(right_ankle_proxy_crv, q=True, ws=True, rp=True)
    cmds.move(ankle_pos[0], right_ball_pivot_grp, moveX=True)
    
    cmds.pointConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, maintainOffset=True, skip=['y'])
    cmds.orientConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, maintainOffset=True, skip=['x', 'z'])
    cmds.scaleConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, skip=['y'])
    cmds.parent(right_ball_proxy_grp, right_ball_pivot_grp)


    # Limits and Locks
    cmds.transformLimits(left_elbow_proxy_crv, tz=(-1, -0.01), etz=(0, 1))
    cmds.transformLimits(right_elbow_proxy_crv, tz=(-1, -0.01), etz=(0, 1))
    
    cmds.transformLimits(left_knee_proxy_crv, tz=(0, 1), etz=(1, 0))
    cmds.transformLimits(right_knee_proxy_crv, tz=(0, 1), etz=(1, 0))
    
    # Left Ankle
    cmds.setAttr(left_ankle_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_ankle_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.transformLimits(left_ankle_proxy_crv, ry=(-80, 80), ery=(1, 1))
    
    # Right Ankle
    cmds.setAttr(right_ankle_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(right_ankle_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.transformLimits(right_ankle_proxy_crv, ry=(-80, 80), ery=(1, 1))
        
    # Main Control
    cmds.setAttr(main_crv + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(main_crv + '.rotate', l=True, k=False, channelBox=False)
    
    # Other Center Joints
    cmds.setAttr(cog_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    
    cmds.setAttr(spine01_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    cmds.setAttr(spine04_proxy_crv + '.tx', l=True, k=False, channelBox=False)

    cmds.setAttr(neck_base_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(neck_mid_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    
    cmds.setAttr(head_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(head_end_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    
    cmds.setAttr(jaw_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.tx', l=True, k=False, channelBox=False)

    cmds.setAttr(head_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine04_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(spine04_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(neck_base_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(head_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(head_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(cog_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(neck_base_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(head_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    
    cmds.setAttr(hip_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)
        
    # Proxy Groups
    cmds.setAttr(spine01_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.v', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.v', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.v', l=True, k=False, channelBox=False)
     
    # Arms
    cmds.setAttr(left_shoulder_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(right_shoulder_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_shoulder_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(right_shoulder_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    cmds.setAttr(left_elbow_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(right_elbow_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_elbow_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(right_elbow_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    # Legs
    cmds.setAttr(right_hip_proxy_crv + '.tz', l=True, k=False, channelBox=False)
    cmds.setAttr(left_hip_proxy_crv + '.tz', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_hip_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_hip_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(left_hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_knee_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_knee_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_knee_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(left_knee_proxy_crv + '.scale', l=True, k=False, channelBox=False)
            
    # Feet
    cmds.setAttr(left_ball_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    cmds.setAttr(right_ball_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_ball_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(right_ball_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_toe_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(right_toe_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    
    cmds.setAttr(left_ball_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_ball_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    
    cmds.setAttr(left_toe_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_toe_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(left_toe_proxy_crv + '.ty', l=True, k=False, channelBox=False)
    
    cmds.setAttr(right_toe_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        
    # Set Loc Visibility
    cmds.setAttr(left_knee_upvec_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_aim_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_dir_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_pv_dir[0] + '.v', 0)
    
    cmds.setAttr(left_elbow_pv_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_aim_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_dir_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_upvec_loc[0] + '.v', 0)
    
    cmds.setAttr(right_knee_upvec_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_aim_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_dir_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_pv_dir[0] + '.v', 0)
    
    cmds.setAttr(right_elbow_pv_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_aim_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_dir_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_upvec_loc[0] + '.v', 0)
    
    # Hide in the Outliner
    cmds.setAttr(left_knee_upvec_loc_grp + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_pv_dir[0] + '.hiddenInOutliner', 1)
    
    cmds.setAttr(left_elbow_pv_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_upvec_loc_grp + '.hiddenInOutliner', 1)
    
    cmds.setAttr(right_knee_upvec_loc_grp + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_pv_dir[0] + '.hiddenInOutliner', 1)
    
    cmds.setAttr(right_elbow_pv_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_upvec_loc_grp + '.hiddenInOutliner', 1)
    
    # Ankle can follow Hip
    cmds.addAttr(left_ankle_proxy_crv, ln="proxyControl", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_ankle_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(left_ankle_proxy_crv, ln="followHip", at="bool", keyable=True)
    cmds.setAttr(left_ankle_proxy_crv + '.followHip', 0)
    constraint = cmds.pointConstraint(left_hip_proxy_crv, left_ankle_proxy_grp, maintainOffset=True)
    cmds.connectAttr(left_ankle_proxy_crv + '.followHip', constraint[0] + '.w0')

    cmds.addAttr(right_ankle_proxy_crv, ln="proxyControl", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_ankle_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(right_ankle_proxy_crv, ln="followHip", at="bool", keyable=True)
    cmds.setAttr(right_ankle_proxy_crv + '.followHip', 0)
    constraint = cmds.pointConstraint(right_hip_proxy_crv, right_ankle_proxy_grp, maintainOffset=True)
    cmds.connectAttr(right_ankle_proxy_crv + '.followHip', constraint[0] + '.w0')
    
    # Store new names into settings in case they were modified
    gt_ab_settings['main_crv'] = main_crv
    gt_ab_settings['cog_proxy_crv'] = cog_proxy_crv
    gt_ab_settings['spine01_proxy_crv'] = spine01_proxy_crv
    gt_ab_settings['spine02_proxy_crv'] = spine02_proxy_crv
    gt_ab_settings['spine03_proxy_crv'] = spine03_proxy_crv
    gt_ab_settings['spine04_proxy_crv'] = spine04_proxy_crv
    gt_ab_settings['neck_base_proxy_crv'] = neck_base_proxy_crv
    gt_ab_settings['neck_mid_proxy_crv'] = neck_mid_proxy_crv
    gt_ab_settings['head_proxy_crv'] = head_proxy_crv
    gt_ab_settings['head_end_proxy_crv'] = head_end_proxy_crv
    gt_ab_settings['jaw_proxy_crv'] = jaw_proxy_crv
    gt_ab_settings['jaw_end_proxy_crv'] = jaw_end_proxy_crv
    gt_ab_settings['hip_proxy_crv'] = hip_proxy_crv
    # Left Side Elements
    gt_ab_settings['left_eye_proxy_crv'] = left_eye_proxy_crv
    gt_ab_settings['left_clavicle_proxy_crv'] = left_clavicle_proxy_crv
    gt_ab_settings['left_shoulder_proxy_crv'] = left_shoulder_proxy_crv
    gt_ab_settings['left_elbow_proxy_crv'] = left_elbow_proxy_crv
    gt_ab_settings['left_wrist_proxy_crv'] = left_wrist_proxy_crv
    gt_ab_settings['left_thumb01_proxy_crv'] = left_thumb01_proxy_crv
    gt_ab_settings['left_thumb02_proxy_crv'] = left_thumb02_proxy_crv
    gt_ab_settings['left_thumb03_proxy_crv'] = left_thumb03_proxy_crv
    gt_ab_settings['left_thumb04_proxy_crv'] = left_thumb04_proxy_crv
    gt_ab_settings['left_index01_proxy_crv'] = left_index01_proxy_crv
    gt_ab_settings['left_index02_proxy_crv'] = left_index02_proxy_crv
    gt_ab_settings['left_index03_proxy_crv'] = left_index03_proxy_crv
    gt_ab_settings['left_index04_proxy_crv'] = left_index04_proxy_crv
    gt_ab_settings['left_middle01_proxy_crv'] = left_middle01_proxy_crv
    gt_ab_settings['left_middle02_proxy_crv'] = left_middle02_proxy_crv
    gt_ab_settings['left_middle03_proxy_crv'] = left_middle03_proxy_crv
    gt_ab_settings['left_middle04_proxy_crv'] = left_middle04_proxy_crv
    gt_ab_settings['left_ring01_proxy_crv'] = left_ring01_proxy_crv
    gt_ab_settings['left_ring02_proxy_crv'] = left_ring02_proxy_crv
    gt_ab_settings['left_ring03_proxy_crv'] = left_ring03_proxy_crv
    gt_ab_settings['left_ring04_proxy_crv'] = left_ring04_proxy_crv
    gt_ab_settings['left_pinky01_proxy_crv'] = left_pinky01_proxy_crv
    gt_ab_settings['left_pinky02_proxy_crv'] = left_pinky02_proxy_crv
    gt_ab_settings['left_pinky03_proxy_crv'] = left_pinky03_proxy_crv
    gt_ab_settings['left_pinky04_proxy_crv'] = left_pinky04_proxy_crv
    gt_ab_settings['left_hip_proxy_crv'] = left_hip_proxy_crv
    gt_ab_settings['left_knee_proxy_crv'] = left_knee_proxy_crv
    gt_ab_settings['left_ankle_proxy_crv'] = left_ankle_proxy_crv
    gt_ab_settings['left_ball_proxy_crv'] = left_ball_proxy_crv
    gt_ab_settings['left_toe_proxy_crv'] = left_toe_proxy_crv
    gt_ab_settings['left_elbow_pv_loc'] = left_elbow_pv_loc[0] 
    gt_ab_settings['left_elbow_dir_loc'] = left_elbow_dir_loc[0] 
    gt_ab_settings['left_elbow_aim_loc'] = left_elbow_aim_loc[0]
    gt_ab_settings['left_elbow_upvec_loc'] = left_elbow_upvec_loc[0]
    gt_ab_settings['left_elbow_divide_node'] = left_elbow_divide_node
    gt_ab_settings['left_knee_pv_dir'] = left_knee_pv_dir[0]
    gt_ab_settings['left_knee_dir_loc'] = left_knee_dir_loc[0]
    gt_ab_settings['left_knee_aim_loc'] = left_knee_aim_loc[0]
    gt_ab_settings['left_knee_upvec_loc'] = left_knee_upvec_loc[0]
    gt_ab_settings['left_knee_divide_node'] = left_knee_divide_node
    gt_ab_settings['left_ball_pivot_grp'] = left_ball_pivot_grp
    # Right Side Elements
    gt_ab_settings['right_eye_proxy_crv'] = right_eye_proxy_crv
    gt_ab_settings['right_clavicle_proxy_crv'] = right_clavicle_proxy_crv
    gt_ab_settings['right_shoulder_proxy_crv'] = right_shoulder_proxy_crv
    gt_ab_settings['right_elbow_proxy_crv'] = right_elbow_proxy_crv
    gt_ab_settings['right_wrist_proxy_crv'] = right_wrist_proxy_crv
    gt_ab_settings['right_thumb01_proxy_crv'] = right_thumb01_proxy_crv
    gt_ab_settings['right_thumb02_proxy_crv'] = right_thumb02_proxy_crv
    gt_ab_settings['right_thumb03_proxy_crv'] = right_thumb03_proxy_crv
    gt_ab_settings['right_thumb04_proxy_crv'] = right_thumb04_proxy_crv
    gt_ab_settings['right_index01_proxy_crv'] = right_index01_proxy_crv
    gt_ab_settings['right_index02_proxy_crv'] = right_index02_proxy_crv
    gt_ab_settings['right_index03_proxy_crv'] = right_index03_proxy_crv
    gt_ab_settings['right_index04_proxy_crv'] = right_index04_proxy_crv
    gt_ab_settings['right_middle01_proxy_crv'] = right_middle01_proxy_crv
    gt_ab_settings['right_middle02_proxy_crv'] = right_middle02_proxy_crv
    gt_ab_settings['right_middle03_proxy_crv'] = right_middle03_proxy_crv
    gt_ab_settings['right_middle04_proxy_crv'] = right_middle04_proxy_crv
    gt_ab_settings['right_ring01_proxy_crv'] = right_ring01_proxy_crv
    gt_ab_settings['right_ring02_proxy_crv'] = right_ring02_proxy_crv
    gt_ab_settings['right_ring03_proxy_crv'] = right_ring03_proxy_crv
    gt_ab_settings['right_ring04_proxy_crv'] = right_ring04_proxy_crv
    gt_ab_settings['right_pinky01_proxy_crv'] = right_pinky01_proxy_crv
    gt_ab_settings['right_pinky02_proxy_crv'] = right_pinky02_proxy_crv
    gt_ab_settings['right_pinky03_proxy_crv'] = right_pinky03_proxy_crv
    gt_ab_settings['right_pinky04_proxy_crv'] = right_pinky04_proxy_crv
    gt_ab_settings['right_hip_proxy_crv'] = right_hip_proxy_crv
    gt_ab_settings['right_knee_proxy_crv'] = right_knee_proxy_crv
    gt_ab_settings['right_ankle_proxy_crv'] = right_ankle_proxy_crv
    gt_ab_settings['right_ball_proxy_crv'] = right_ball_proxy_crv
    gt_ab_settings['right_toe_proxy_crv'] = right_toe_proxy_crv
    gt_ab_settings['right_elbow_pv_loc'] = right_elbow_pv_loc[0] 
    gt_ab_settings['right_elbow_dir_loc'] = right_elbow_dir_loc[0] 
    gt_ab_settings['right_elbow_aim_loc'] = right_elbow_aim_loc[0]
    gt_ab_settings['right_elbow_upvec_loc'] = right_elbow_upvec_loc[0]
    gt_ab_settings['right_elbow_divide_node'] = right_elbow_divide_node
    gt_ab_settings['right_knee_pv_dir'] = right_knee_pv_dir[0]
    gt_ab_settings['right_knee_dir_loc'] = right_knee_dir_loc[0]
    gt_ab_settings['right_knee_aim_loc'] = right_knee_aim_loc[0]
    gt_ab_settings['right_knee_upvec_loc'] = right_knee_upvec_loc[0]
    gt_ab_settings['right_knee_divide_node'] = right_knee_divide_node
    gt_ab_settings['right_ball_pivot_grp'] = right_ball_pivot_grp
    
    
    
    # Visibility Adjustments
    for obj in gt_ab_settings:
        if obj.endswith('_crv'):
            proxy_crv = gt_ab_settings.get(obj)
            is_end_jnt = False
            color = (0,0,0)
            if '_endProxy' in proxy_crv:
                add_node_note(proxy_crv, 'This is an end proxy. This element will be used to determine the orientation of its parent. For example:\n"jaw_endProxy" determines the orientation of the "jaw_proxy".\n\nEven though a joint will be generated it mostly likely shouldn\'t be an influence when skinning.')
                color = (.5,.5,0)
                is_end_jnt=True
            elif gt_ab_settings.get('neck_mid_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv, 'This is the neckMid proxy. This element will be automated to receive part of its transforms from the neckBase and the other part from the head.')
                color = (.3,.3,0)
            elif gt_ab_settings.get('left_toe_proxy_crv') in proxy_crv or gt_ab_settings.get('right_toe_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv, 'This is a toe proxy. This element will be used to automate toe poses. Much like an end proxy, it will generate a joint that most likely shoudln\'t be used as an influence when skinning.\n\nThis joint should be placed at the end of the longest toe.')
                color = (.3,.3,0)
                is_end_jnt=True
            elif proxy_crv.startswith('right_'):
                color = (1,.4,.4)
            elif proxy_crv.startswith('left_'):
                color = (.2,.6,1)
            elif gt_ab_settings.get('spine01_proxy_crv') in proxy_crv or gt_ab_settings.get('spine02_proxy_crv') in proxy_crv or gt_ab_settings.get('spine03_proxy_crv') in proxy_crv:
                color = (.3,.3,0)
            else:
                color = (1,1,.65)
            
            # Notes Only
            if gt_ab_settings.get('left_eye_proxy_crv') in proxy_crv or gt_ab_settings.get('right_eye_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv, 'This is an eye proxy.\nThis element should be snapped to the center of the eye geometry.\nYou can see the center of the eye by selecting the eye geometry then going to "Display > Transform Display > Local Rotation Axes".\nYou can then use this axis to snap the joint to its center. (Using "Ctrl + V")\n\nPS: If for some reason the pivot point is not in the center of the eye, you can reset it first: "Modify > Center Pivot".')
            if gt_ab_settings.get('left_elbow_proxy_crv') in proxy_crv or gt_ab_settings.get('right_elbow_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv, 'This is an elbow proxy.\nThe movement of this element is intentionaly limited to attempt to keep the joints in one single plane. For better results keep the arm joints in "T" or "A" pose.')
                
            if colorize_proxy:
                change_viewport_color(proxy_crv, color)
            if colorize_proxy and is_end_jnt:
                change_outliner_color(proxy_crv, (.8,.8,0))
    
    # Create Lines
    line_list = []
    line_list.append(create_visualization_line(gt_ab_settings.get('cog_proxy_crv'), gt_ab_settings.get('hip_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('cog_proxy_crv'), gt_ab_settings.get('spine01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine01_proxy_crv'), gt_ab_settings.get('spine02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine02_proxy_crv'), gt_ab_settings.get('spine03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine03_proxy_crv'), gt_ab_settings.get('spine04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine04_proxy_crv'), gt_ab_settings.get('neck_base_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('neck_base_proxy_crv'), gt_ab_settings.get('neck_mid_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('neck_mid_proxy_crv'), gt_ab_settings.get('head_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('head_proxy_crv'), gt_ab_settings.get('head_end_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('head_proxy_crv'), gt_ab_settings.get('jaw_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('jaw_proxy_crv'), gt_ab_settings.get('jaw_end_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('head_proxy_crv'), gt_ab_settings.get('left_eye_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('head_proxy_crv'), gt_ab_settings.get('right_eye_proxy_crv')))
    # Left Side
    line_list.append(create_visualization_line(gt_ab_settings.get('hip_proxy_crv'), gt_ab_settings.get('left_hip_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_hip_proxy_crv'), gt_ab_settings.get('left_knee_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_knee_proxy_crv'), gt_ab_settings.get('left_ankle_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_ankle_proxy_crv'), gt_ab_settings.get('left_ball_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_ball_proxy_crv'), gt_ab_settings.get('left_toe_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine04_proxy_crv'), gt_ab_settings.get('left_clavicle_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_clavicle_proxy_crv'), gt_ab_settings.get('left_shoulder_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_shoulder_proxy_crv'), gt_ab_settings.get('left_elbow_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_elbow_proxy_crv'), gt_ab_settings.get('left_wrist_proxy_crv')))
    # Left Fingers
    line_list.append(create_visualization_line(gt_ab_settings.get('left_wrist_proxy_crv'), gt_ab_settings.get('left_thumb01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_thumb01_proxy_crv'), gt_ab_settings.get('left_thumb02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_thumb02_proxy_crv'), gt_ab_settings.get('left_thumb03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_thumb03_proxy_crv'), gt_ab_settings.get('left_thumb04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_wrist_proxy_crv'), gt_ab_settings.get('left_index01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_index01_proxy_crv'), gt_ab_settings.get('left_index02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_index02_proxy_crv'), gt_ab_settings.get('left_index03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_index03_proxy_crv'), gt_ab_settings.get('left_index04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_wrist_proxy_crv'), gt_ab_settings.get('left_middle01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_middle01_proxy_crv'), gt_ab_settings.get('left_middle02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_middle02_proxy_crv'), gt_ab_settings.get('left_middle03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_middle03_proxy_crv'), gt_ab_settings.get('left_middle04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_wrist_proxy_crv'), gt_ab_settings.get('left_ring01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_ring01_proxy_crv'), gt_ab_settings.get('left_ring02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_ring02_proxy_crv'), gt_ab_settings.get('left_ring03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_ring03_proxy_crv'), gt_ab_settings.get('left_ring04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_wrist_proxy_crv'), gt_ab_settings.get('left_pinky01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_pinky01_proxy_crv'), gt_ab_settings.get('left_pinky02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_pinky02_proxy_crv'), gt_ab_settings.get('left_pinky03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('left_pinky03_proxy_crv'), gt_ab_settings.get('left_pinky04_proxy_crv')))
    # Right Side
    line_list.append(create_visualization_line(gt_ab_settings.get('hip_proxy_crv'), gt_ab_settings.get('right_hip_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_hip_proxy_crv'), gt_ab_settings.get('right_knee_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_knee_proxy_crv'), gt_ab_settings.get('right_ankle_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_ankle_proxy_crv'), gt_ab_settings.get('right_ball_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_ball_proxy_crv'), gt_ab_settings.get('right_toe_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('spine04_proxy_crv'), gt_ab_settings.get('right_clavicle_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_clavicle_proxy_crv'), gt_ab_settings.get('right_shoulder_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_shoulder_proxy_crv'), gt_ab_settings.get('right_elbow_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_elbow_proxy_crv'), gt_ab_settings.get('right_wrist_proxy_crv')))
    # Right Fingers
    line_list.append(create_visualization_line(gt_ab_settings.get('right_wrist_proxy_crv'), gt_ab_settings.get('right_thumb01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_thumb01_proxy_crv'), gt_ab_settings.get('right_thumb02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_thumb02_proxy_crv'), gt_ab_settings.get('right_thumb03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_thumb03_proxy_crv'), gt_ab_settings.get('right_thumb04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_wrist_proxy_crv'), gt_ab_settings.get('right_index01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_index01_proxy_crv'), gt_ab_settings.get('right_index02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_index02_proxy_crv'), gt_ab_settings.get('right_index03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_index03_proxy_crv'), gt_ab_settings.get('right_index04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_wrist_proxy_crv'), gt_ab_settings.get('right_middle01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_middle01_proxy_crv'), gt_ab_settings.get('right_middle02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_middle02_proxy_crv'), gt_ab_settings.get('right_middle03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_middle03_proxy_crv'), gt_ab_settings.get('right_middle04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_wrist_proxy_crv'), gt_ab_settings.get('right_ring01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_ring01_proxy_crv'), gt_ab_settings.get('right_ring02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_ring02_proxy_crv'), gt_ab_settings.get('right_ring03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_ring03_proxy_crv'), gt_ab_settings.get('right_ring04_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_wrist_proxy_crv'), gt_ab_settings.get('right_pinky01_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_pinky01_proxy_crv'), gt_ab_settings.get('right_pinky02_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_pinky02_proxy_crv'), gt_ab_settings.get('right_pinky03_proxy_crv')))
    line_list.append(create_visualization_line(gt_ab_settings.get('right_pinky03_proxy_crv'), gt_ab_settings.get('right_pinky04_proxy_crv')))
    
    lines_grp = cmds.group(name='visualization_lines', empty=True, world=True)
    cmds.setAttr(lines_grp + '.overrideEnabled', 1)
    cmds.setAttr(lines_grp + '.overrideDisplayType', 1)
    for line_objs in line_list:
        for obj in line_objs:
            cmds.parent(obj, lines_grp)
   
    cmds.parent(lines_grp, gt_ab_settings.get('main_proxy_grp'))
    
    cmds.addAttr(gt_ab_settings.get('main_crv'), ln="proxyOptions", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(gt_ab_settings.get('main_crv') + '.proxyOptions', lock=True)
    cmds.addAttr(gt_ab_settings.get('main_crv'), ln="linesVisibility", at="bool", keyable=True)
    cmds.setAttr(gt_ab_settings.get('main_crv') + '.linesVisibility', 1)
    cmds.connectAttr(gt_ab_settings.get('main_crv') + '.linesVisibility', lines_grp + '.v', f=True)
    
    # Main Proxy Control Scale
    cmds.connectAttr(gt_ab_settings.get('main_crv') + '.sy', gt_ab_settings.get('main_crv') + '.sx', f=True)
    cmds.connectAttr(gt_ab_settings.get('main_crv') + '.sy', gt_ab_settings.get('main_crv') + '.sz', f=True)
    cmds.setAttr(gt_ab_settings.get('main_crv') + '.sx', k=False)
    cmds.setAttr(gt_ab_settings.get('main_crv') + '.sz', k=False)
    
    
    # Clean Selection and Print Feedback
    cmds.select(d=True)
    unique_message = '<' + str(random.random()) + '>'
    cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> was created!</span>', pos='botLeft', fade=True, alpha=.9)



def create_controls():
    ''' Creates rig using the previously created proxy/guide '''
    
    left_ctrl_color = (0, .3, 1)
    right_ctrl_color = (1, 0, 0)
    automation_ctrl_color = (.6,.2,1)
    
    def rename_proxy(old_name):
        ''' 
        Replaces a few parts of the old names for the creation of joints
        Replaces "proxy" with "jnt"
        Replaces "endProxy" with "endJnt"
        
                Parameters:
                    old_name (string): Name of the proxy element
                    
                Returns:
                    new_name (string): Name of the joint to be created out of the element
        
        '''
        return old_name.replace(proxy_suffix, jnt_suffix).replace('end' + proxy_suffix.capitalize(), 'end' + jnt_suffix.capitalize())
    
    
    def orient_to_target(obj, target, orient_offset=(0,0,0), proxy_obj=None, aim_vec=(1,0,0), up_vec=(0,-1,0)):
        ''' 
        Orients an object based on a target object 
        
                Parameters:
                    obj (string): Name of the object to orient (usually a joint)
                    target (string): Name of the target object (usually the element that will be the child of "obj")
                    orient_offset (tuple): A tuple containing three 32b floats, used as a rotate offset to change the result orientation
                    proxy_obj (string): The name of the proxy element (used as extra rotation input)
                    aim_vec (tuple): A tuple of floats used for the aim vector of the aim constraint - default value: (1,0,0)
                    up_vec (tuple):  A tuple of floats used for the up vector of the aim constraint - default value: (0,-1,0)
        '''
        if proxy_obj:
            constraint = cmds.orientConstraint(proxy_obj, obj, offset=(0,0,0))
            cmds.delete(constraint)
            cmds.makeIdentity(obj, apply=True, rotate=True)
        cmds.setAttr(obj + '.rotateX', orient_offset[0])
        cmds.setAttr(obj + '.rotateY', orient_offset[1])
        cmds.setAttr(obj + '.rotateZ', orient_offset[2])
        cmds.makeIdentity(obj, apply=True, rotate=True)
        constraint = cmds.aimConstraint(target, obj, offset=(0,0,0), aimVector=aim_vec, upVector=up_vec, worldUpType="vector", worldUpVector=(0,1,0), skip='x')
        cmds.delete(constraint)
        cmds.makeIdentity(obj, apply=True, rotate=True)
    
    def create_simple_fk_control(jnt_name, scale_offset, create_offset_grp=True):
        ''' 
        Creates a simple fk control. Used to quickly interate through the creation of the finger controls
        
                Parameters:
                    jnt_name (string): Name of the joint that will be controlled
                    scale_offset (float): The scale offset applied to the control before freezing it
                    create_offset_grp (bool): Whether or not an offset group will be created
                Returns:
                    control_name_and_group (tuple): The name of the generated control and the name of its ctrl group
        
        '''
        fk_ctrl = cmds.curve(name=jnt_name.replace(jnt_suffix, '') + ctrl_suffix, p=[[0.0, 0.0, 0.0], [0.0, 0.897, 0.0], [0.033, 0.901, 0.0], [0.064, 0.914, 0.0], [0.091, 0.935, 0.0], [0.111, 0.961, 0.0], [0.124, 0.992, 0.0], [0.128, 1.025, 0.0], [0.0, 1.025, 0.0], [0.0, 0.897, 0.0], [-0.033, 0.901, 0.0], [-0.064, 0.914, 0.0], [-0.091, 0.935, 0.0], [-0.111, 0.961, 0.0], [-0.124, 0.992, 0.0], [-0.128, 1.025, 0.0], [-0.124, 1.058, 0.0], [-0.111, 1.089, 0.0], [-0.091, 1.116, 0.0], [-0.064, 1.136, 0.0], [-0.033, 1.149, 0.0], [0.0, 1.153, 0.0], [0.033, 1.149, 0.0], [0.064, 1.136, 0.0], [0.091, 1.116, 0.0], [0.111, 1.089, 0.0], [0.124, 1.058, 0.0], [0.128, 1.025, 0.0], [-0.128, 1.025, 0.0], [0.0, 1.025, 0.0], [0.0, 1.153, 0.0]],d=1)
        fk_ctrl_grp = cmds.group(name=fk_ctrl + grp_suffix.capitalize(), empty=True, world=True)
        
        if create_offset_grp:
            fk_ctrl_offset_grp = cmds.group(name=fk_ctrl + 'Offset' + grp_suffix.capitalize(), empty=True, world=True)
            cmds.parent(fk_ctrl, fk_ctrl_offset_grp)
            cmds.parent(fk_ctrl_offset_grp, fk_ctrl_grp)
        else:
            cmds.parent(fk_ctrl, fk_ctrl_grp)

        cmds.setAttr(fk_ctrl + '.scaleX', scale_offset)
        cmds.setAttr(fk_ctrl + '.scaleY', scale_offset)
        cmds.setAttr(fk_ctrl + '.scaleZ', scale_offset)
        cmds.makeIdentity(fk_ctrl, apply=True, scale=True)
        
        cmds.delete(cmds.parentConstraint(jnt_name, fk_ctrl_grp))
        if 'left_' in jnt_name:
            change_viewport_color(fk_ctrl, left_ctrl_color)
        elif 'right_' in jnt_name:
            change_viewport_color(fk_ctrl, right_ctrl_color)
            
        for shape in cmds.listRelatives(fk_ctrl, s=True, f=True) or []:
            shape = cmds.rename(shape, "{0}Shape".format(fk_ctrl))
        
        return fk_ctrl, fk_ctrl_grp, fk_ctrl_offset_grp
    
    def remove_numbers(string):
        '''
        Removes all numbers (digits) from the provided string
        
                Parameters:
                    string (string): input string (numbers will be removed from it)
                    
                Returns:
                    string (string): output string without numbers (digits)
        
        
        '''
        return (''.join([i for i in string if not i.isdigit()]))
    
    def lock_hide_default_attr(obj, translate=True, rotate=True, scale=True, visibility=True):
        '''
        Lock and Hide default attributes
        
                Parameters:
                    obj (string): Name of the object to be locked
                    translate (bool): Whether or not to lock and hide translate
                    rotate (bool): Whether or not to lock and hide rotate
                    scale (bool): Whether or not to lock and hide scale
                    visibility (bool): Whether or not to lock and hide visibility
        
        '''
        if translate:
            cmds.setAttr(obj + '.tx', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.ty', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.tz', lock=True, k=False, channelBox=False)
        
        if rotate:
            cmds.setAttr(obj + '.rx', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.ry', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.rz', lock=True, k=False, channelBox=False)
        
        if scale:
            cmds.setAttr(obj + '.sx', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.sy', lock=True, k=False, channelBox=False)
            cmds.setAttr(obj + '.sz', lock=True, k=False, channelBox=False)
        
        if visibility:
            cmds.setAttr(obj + '.v', lock=True, k=False, channelBox=False)


    # Store selection and symmetry states
    cmds.select(d=True) # Clear Selection
    cmds.symmetricModelling(e=True, symmetry=False) # Turn off symmetry

    # Create Joints
    gt_ab_joints = {}
    for obj in gt_ab_settings:
        if obj.endswith('_crv'):
            cmds.select(d=True)
            joint = cmds.joint(name=rename_proxy(gt_ab_settings.get(obj)), radius=1)
            constraint = cmds.pointConstraint(gt_ab_settings.get(obj), joint)
            cmds.delete(constraint)
            gt_ab_joints[obj.replace('_crv','_' + jnt_suffix).replace('_proxy', '')] = joint
   
   
    # General Orients
    orient_to_target(gt_ab_joints.get('spine01_jnt'), gt_ab_joints.get('spine02_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('spine02_jnt'), gt_ab_joints.get('spine03_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('spine03_jnt'), gt_ab_joints.get('spine04_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('spine04_jnt'), gt_ab_joints.get('neck_base_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('neck_base_jnt'), gt_ab_joints.get('neck_mid_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('neck_mid_jnt'), gt_ab_joints.get('head_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('head_jnt'), gt_ab_joints.get('head_end_jnt'), (90, 0, 90))
    orient_to_target(gt_ab_joints.get('jaw_jnt'), gt_ab_joints.get('jaw_end_jnt'), (90, 0, 90))
    
    # Left Finger Orients
    orient_to_target(gt_ab_joints.get('left_thumb01_jnt'), gt_ab_joints.get('left_thumb02_jnt'), (-90, 0, 90), gt_ab_settings.get('left_thumb01_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_thumb02_jnt'), gt_ab_joints.get('left_thumb03_jnt'), (-90, 0, 90), gt_ab_settings.get('left_thumb02_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_thumb03_jnt'), gt_ab_joints.get('left_thumb04_jnt'), (-90, 0, 90), gt_ab_settings.get('left_thumb03_proxy_crv'), up_vec=(0,1,0))
    
    orient_to_target(gt_ab_joints.get('left_index01_jnt'), gt_ab_joints.get('left_index02_jnt'), (0, 0, 90), gt_ab_settings.get('left_index01_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_index02_jnt'), gt_ab_joints.get('left_index03_jnt'), (0, 0, 90), gt_ab_settings.get('left_index02_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_index03_jnt'), gt_ab_joints.get('left_index04_jnt'), (0, 0, 90), gt_ab_settings.get('left_index03_proxy_crv'), up_vec=(0,1,0))
    
    orient_to_target(gt_ab_joints.get('left_middle01_jnt'), gt_ab_joints.get('left_middle02_jnt'), (0, 0, 90), gt_ab_settings.get('left_middle01_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_middle02_jnt'), gt_ab_joints.get('left_middle03_jnt'), (0, 0, 90), gt_ab_settings.get('left_middle02_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_middle03_jnt'), gt_ab_joints.get('left_middle04_jnt'), (0, 0, 90), gt_ab_settings.get('left_middle03_proxy_crv'), up_vec=(0,1,0))
    
    orient_to_target(gt_ab_joints.get('left_ring01_jnt'), gt_ab_joints.get('left_ring02_jnt'), (0, 0, 90), gt_ab_settings.get('left_ring01_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_ring02_jnt'), gt_ab_joints.get('left_ring03_jnt'), (0, 0, 90), gt_ab_settings.get('left_ring02_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_ring03_jnt'), gt_ab_joints.get('left_ring04_jnt'), (0, 0, 90), gt_ab_settings.get('left_ring03_proxy_crv'), up_vec=(0,1,0))
    
    orient_to_target(gt_ab_joints.get('left_pinky01_jnt'), gt_ab_joints.get('left_pinky02_jnt'), (0, 0, 90), gt_ab_settings.get('left_pinky01_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_pinky02_jnt'), gt_ab_joints.get('left_pinky03_jnt'), (0, 0, 90), gt_ab_settings.get('left_pinky02_proxy_crv'), up_vec=(0,1,0))
    orient_to_target(gt_ab_joints.get('left_pinky03_jnt'), gt_ab_joints.get('left_pinky04_jnt'), (0, 0, 90), gt_ab_settings.get('left_pinky03_proxy_crv'), up_vec=(0,1,0))
    
    # Right Finger Orients
    orient_to_target(gt_ab_joints.get('right_thumb01_jnt'), gt_ab_joints.get('right_thumb02_jnt'), (0, 180, 0), gt_ab_settings.get('right_thumb01_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_thumb02_jnt'), gt_ab_joints.get('right_thumb03_jnt'), (0, 180, 0), gt_ab_settings.get('right_thumb02_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_thumb03_jnt'), gt_ab_joints.get('right_thumb04_jnt'), (0, 180, 0), gt_ab_settings.get('right_thumb03_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    
    orient_to_target(gt_ab_joints.get('right_index01_jnt'), gt_ab_joints.get('right_index02_jnt'), (0, 180, 0), gt_ab_settings.get('right_index01_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_index02_jnt'), gt_ab_joints.get('right_index03_jnt'), (0, 180, 0), gt_ab_settings.get('right_index02_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_index03_jnt'), gt_ab_joints.get('right_index04_jnt'), (0, 180, 0), gt_ab_settings.get('right_index03_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    
    orient_to_target(gt_ab_joints.get('right_middle01_jnt'), gt_ab_joints.get('right_middle02_jnt'), (0, 180, 0), gt_ab_settings.get('right_middle01_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_middle02_jnt'), gt_ab_joints.get('right_middle03_jnt'), (0, 180, 0), gt_ab_settings.get('right_middle02_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_middle03_jnt'), gt_ab_joints.get('right_middle04_jnt'), (0, 180, 0), gt_ab_settings.get('right_middle03_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    
    orient_to_target(gt_ab_joints.get('right_ring01_jnt'), gt_ab_joints.get('right_ring02_jnt'), (0, 180, 0), gt_ab_settings.get('right_ring01_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_ring02_jnt'), gt_ab_joints.get('right_ring03_jnt'), (0, 180, 0), gt_ab_settings.get('right_ring02_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_ring03_jnt'), gt_ab_joints.get('right_ring04_jnt'), (0, 180, 0), gt_ab_settings.get('right_ring03_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    
    orient_to_target(gt_ab_joints.get('right_pinky01_jnt'), gt_ab_joints.get('right_pinky02_jnt'), (0, 180, 0), gt_ab_settings.get('right_pinky01_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_pinky02_jnt'), gt_ab_joints.get('right_pinky03_jnt'), (0, 180, 0), gt_ab_settings.get('right_pinky02_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))
    orient_to_target(gt_ab_joints.get('right_pinky03_jnt'), gt_ab_joints.get('right_pinky04_jnt'), (0, 180, 0), gt_ab_settings.get('right_pinky03_proxy_crv'), up_vec=(0,1,0), aim_vec=(1,0,0))

    
    # Center Parenting
    cmds.parent(gt_ab_joints.get('spine01_jnt'), gt_ab_joints.get('cog_jnt'))
    cmds.parent(gt_ab_joints.get('spine02_jnt'), gt_ab_joints.get('spine01_jnt'))
    cmds.parent(gt_ab_joints.get('spine03_jnt'), gt_ab_joints.get('spine02_jnt'))
    cmds.parent(gt_ab_joints.get('spine04_jnt'), gt_ab_joints.get('spine03_jnt'))
    cmds.parent(gt_ab_joints.get('neck_base_jnt'), gt_ab_joints.get('spine04_jnt'))
    cmds.parent(gt_ab_joints.get('neck_mid_jnt'), gt_ab_joints.get('neck_base_jnt'))
    cmds.parent(gt_ab_joints.get('head_jnt'), gt_ab_joints.get('neck_mid_jnt'))
    cmds.parent(gt_ab_joints.get('head_end_jnt'), gt_ab_joints.get('head_jnt'))
    cmds.parent(gt_ab_joints.get('jaw_end_jnt'), gt_ab_joints.get('jaw_jnt'))
    
    
    # Left Fingers Parenting
    cmds.parent(gt_ab_joints.get('left_thumb01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_thumb02_jnt'), gt_ab_joints.get('left_thumb01_jnt'))
    cmds.parent(gt_ab_joints.get('left_thumb03_jnt'), gt_ab_joints.get('left_thumb02_jnt'))
    cmds.parent(gt_ab_joints.get('left_thumb04_jnt'), gt_ab_joints.get('left_thumb03_jnt'))
    
    cmds.parent(gt_ab_joints.get('left_index01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_index02_jnt'), gt_ab_joints.get('left_index01_jnt'))
    cmds.parent(gt_ab_joints.get('left_index03_jnt'), gt_ab_joints.get('left_index02_jnt'))
    cmds.parent(gt_ab_joints.get('left_index04_jnt'), gt_ab_joints.get('left_index03_jnt'))
    
    cmds.parent(gt_ab_joints.get('left_middle01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_middle02_jnt'), gt_ab_joints.get('left_middle01_jnt'))
    cmds.parent(gt_ab_joints.get('left_middle03_jnt'), gt_ab_joints.get('left_middle02_jnt'))
    cmds.parent(gt_ab_joints.get('left_middle04_jnt'), gt_ab_joints.get('left_middle03_jnt'))
    
    cmds.parent(gt_ab_joints.get('left_ring01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_ring02_jnt'), gt_ab_joints.get('left_ring01_jnt'))
    cmds.parent(gt_ab_joints.get('left_ring03_jnt'), gt_ab_joints.get('left_ring02_jnt'))
    cmds.parent(gt_ab_joints.get('left_ring04_jnt'), gt_ab_joints.get('left_ring03_jnt'))
    
    cmds.parent(gt_ab_joints.get('left_pinky01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_pinky02_jnt'), gt_ab_joints.get('left_pinky01_jnt'))
    cmds.parent(gt_ab_joints.get('left_pinky03_jnt'), gt_ab_joints.get('left_pinky02_jnt'))
    cmds.parent(gt_ab_joints.get('left_pinky04_jnt'), gt_ab_joints.get('left_pinky03_jnt'))
    
    
    # Right Fingers Parenting
    cmds.parent(gt_ab_joints.get('right_thumb01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_thumb02_jnt'), gt_ab_joints.get('right_thumb01_jnt'))
    cmds.parent(gt_ab_joints.get('right_thumb03_jnt'), gt_ab_joints.get('right_thumb02_jnt'))
    cmds.parent(gt_ab_joints.get('right_thumb04_jnt'), gt_ab_joints.get('right_thumb03_jnt'))
    
    cmds.parent(gt_ab_joints.get('right_index01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_index02_jnt'), gt_ab_joints.get('right_index01_jnt'))
    cmds.parent(gt_ab_joints.get('right_index03_jnt'), gt_ab_joints.get('right_index02_jnt'))
    cmds.parent(gt_ab_joints.get('right_index04_jnt'), gt_ab_joints.get('right_index03_jnt'))
    
    cmds.parent(gt_ab_joints.get('right_middle01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_middle02_jnt'), gt_ab_joints.get('right_middle01_jnt'))
    cmds.parent(gt_ab_joints.get('right_middle03_jnt'), gt_ab_joints.get('right_middle02_jnt'))
    cmds.parent(gt_ab_joints.get('right_middle04_jnt'), gt_ab_joints.get('right_middle03_jnt'))
    
    cmds.parent(gt_ab_joints.get('right_ring01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_ring02_jnt'), gt_ab_joints.get('right_ring01_jnt'))
    cmds.parent(gt_ab_joints.get('right_ring03_jnt'), gt_ab_joints.get('right_ring02_jnt'))
    cmds.parent(gt_ab_joints.get('right_ring04_jnt'), gt_ab_joints.get('right_ring03_jnt'))
    
    cmds.parent(gt_ab_joints.get('right_pinky01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_pinky02_jnt'), gt_ab_joints.get('right_pinky01_jnt'))
    cmds.parent(gt_ab_joints.get('right_pinky03_jnt'), gt_ab_joints.get('right_pinky02_jnt'))
    cmds.parent(gt_ab_joints.get('right_pinky04_jnt'), gt_ab_joints.get('right_pinky03_jnt'))
    
    # Extract General Scale Offset
    general_scale_offset = 0.0
    general_scale_offset -= cmds.xform(gt_ab_joints.get('hip_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('spine01_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('spine02_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('spine03_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('spine04_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('neck_base_jnt'),q=True, t=True)[0]
    general_scale_offset += cmds.xform(gt_ab_joints.get('neck_mid_jnt'),q=True, t=True)[0]
    general_scale_offset = (general_scale_offset/7)*3

    # Adjust Joint Visibility
    joint_scale_offset = general_scale_offset*.06
    for jnt in gt_ab_joints:
        joint = gt_ab_joints.get(jnt)
        # End Joints
        if 'endJnt' in joint or gt_ab_joints.get('right_toe_jnt') in joint or gt_ab_joints.get('left_toe_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6*joint_scale_offset)
            add_node_note(joint, 'This is an end joint. This means that this joint shouldn\'t be an influence when skinning.')
            change_outliner_color(joint, (1,0,0))
            change_viewport_color(joint, (1,0,0))
        # Eye Joints
        elif gt_ab_joints.get('left_eye_jnt') in joint or gt_ab_joints.get('right_eye_jnt') in joint:
            cmds.setAttr(joint + '.radius', 3*joint_scale_offset)
            change_viewport_color(joint, (0,1,0))
        # Finger Joints
        elif 'thumb' in joint or 'index' in joint or 'middle' in joint or 'ring' in joint or 'pinky' in joint:
            cmds.setAttr(joint + '.radius', 1*joint_scale_offset)
            change_viewport_color(joint, (.3,.3,0))
        # Side Joints
        elif 'left_' in joint or 'right_' in joint:
            cmds.setAttr(joint + '.radius', 2*joint_scale_offset)
            change_viewport_color(joint, (.3,.3,0))
        # Center Joints
        else:
            cmds.setAttr(joint + '.radius', 1.5*joint_scale_offset)
            change_viewport_color(joint, (1,1,0))
        
        # Skeleton (Main) Joint
        if gt_ab_joints.get('main_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6*joint_scale_offset)
            change_viewport_color(joint, (.4,.4,.4))
        elif gt_ab_joints.get('head_jnt') in joint:
            cmds.setAttr(joint + '.radius', 3.5*joint_scale_offset)
        elif gt_ab_joints.get('neck_base_jnt') in joint or gt_ab_joints.get('jaw_jnt') in joint:
            cmds.setAttr(joint + '.radius', 1.2*joint_scale_offset)
        elif gt_ab_joints.get('neck_mid_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6*joint_scale_offset)
            change_viewport_color(joint, (.3,.3,0))
        
    # Set Orientation For Arms
    orient_to_target(gt_ab_joints.get('left_clavicle_jnt'), gt_ab_joints.get('left_shoulder_jnt'), (-90,0,0), gt_ab_settings.get('left_clavicle_proxy_crv'))
    orient_to_target(gt_ab_joints.get('left_shoulder_jnt'), gt_ab_joints.get('left_elbow_jnt'), (-90,0,0))
    orient_to_target(gt_ab_joints.get('left_elbow_jnt'), gt_ab_joints.get('left_wrist_jnt'), (-90,0,0), gt_ab_settings.get('left_elbow_proxy_crv'))
    
    orient_to_target(gt_ab_joints.get('right_clavicle_jnt'), gt_ab_joints.get('right_shoulder_jnt'), (90,0,0), gt_ab_settings.get('right_clavicle_proxy_crv'), (-1,0,0))
    orient_to_target(gt_ab_joints.get('right_shoulder_jnt'), gt_ab_joints.get('right_elbow_jnt'), (90,0,0), aim_vec=(-1,0,0))
    orient_to_target(gt_ab_joints.get('right_elbow_jnt'), gt_ab_joints.get('right_wrist_jnt'), (90,0,0), gt_ab_settings.get('right_elbow_proxy_crv'), aim_vec=(-1,0,0))
 
    # Left Arm Parenting
    cmds.parent(gt_ab_joints.get('left_clavicle_jnt'), gt_ab_joints.get('spine04_jnt'))
    cmds.parent(gt_ab_joints.get('left_shoulder_jnt'), gt_ab_joints.get('left_clavicle_jnt'))
    cmds.parent(gt_ab_joints.get('left_elbow_jnt'), gt_ab_joints.get('left_shoulder_jnt'))
    cmds.parent(gt_ab_joints.get('left_wrist_jnt'), gt_ab_joints.get('left_elbow_jnt'))
    
    # Right Arm Parenting
    cmds.parent(gt_ab_joints.get('right_clavicle_jnt'), gt_ab_joints.get('spine04_jnt'))
    cmds.parent(gt_ab_joints.get('right_shoulder_jnt'), gt_ab_joints.get('right_clavicle_jnt'))
    cmds.parent(gt_ab_joints.get('right_elbow_jnt'), gt_ab_joints.get('right_shoulder_jnt'))
    cmds.parent(gt_ab_joints.get('right_wrist_jnt'), gt_ab_joints.get('right_elbow_jnt'))
             
    # Left Hand Hierarchy and Orients
    # Left Remove Fingers
    cmds.parent(gt_ab_joints.get('left_wrist_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('left_thumb01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('left_index01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('left_middle01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('left_ring01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('left_pinky01_jnt'), world=True)
    
    # Left Wrist Orient
    temp_transform = cmds.group(empty=True, world=True, name=gt_ab_settings.get('left_wrist_proxy_crv') + '_orient_target')
    constraint = cmds.parentConstraint(gt_ab_settings.get('left_wrist_proxy_crv'), temp_transform)
    cmds.delete(constraint)
    cmds.parent(temp_transform, gt_ab_settings.get('left_wrist_proxy_crv'))
    cmds.setAttr(temp_transform + '.tx', 1)
    orient_to_target(gt_ab_joints.get('left_wrist_jnt'), temp_transform, (-90,0,0), gt_ab_settings.get('left_wrist_proxy_crv'))
    cmds.delete(temp_transform)

    # Left Add Fingers
    cmds.parent(gt_ab_joints.get('left_wrist_jnt'), gt_ab_joints.get('left_elbow_jnt'))
    cmds.parent(gt_ab_joints.get('left_thumb01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_index01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_middle01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_ring01_jnt'), gt_ab_joints.get('left_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('left_pinky01_jnt'), gt_ab_joints.get('left_wrist_jnt'))

    # Right Hand Hierarchy and Orients
    # Right Remove Fingers
    cmds.parent(gt_ab_joints.get('right_wrist_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('right_thumb01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('right_index01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('right_middle01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('right_ring01_jnt'), world=True)
    cmds.parent(gt_ab_joints.get('right_pinky01_jnt'), world=True)
    
    # Right Wrist Orient
    temp_transform = cmds.group(empty=True, world=True, name=gt_ab_settings.get('right_wrist_proxy_crv') + '_orient_target')
    constraint = cmds.parentConstraint(gt_ab_settings.get('right_wrist_proxy_crv'), temp_transform)
    cmds.delete(constraint)
    cmds.parent(temp_transform, gt_ab_settings.get('right_wrist_proxy_crv'))
    cmds.setAttr(temp_transform + '.tx', -1)
    orient_to_target(gt_ab_joints.get('right_wrist_jnt'), temp_transform, (90,0,0), gt_ab_settings.get('right_wrist_proxy_crv'), (-1,0,0))
    cmds.delete(temp_transform)

    # Right Add Fingers
    cmds.parent(gt_ab_joints.get('right_wrist_jnt'), gt_ab_joints.get('right_elbow_jnt'))
    cmds.parent(gt_ab_joints.get('right_thumb01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_index01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_middle01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_ring01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    cmds.parent(gt_ab_joints.get('right_pinky01_jnt'), gt_ab_joints.get('right_wrist_jnt'))
    
    # The rest of the parenting and orients
    cmds.parent(gt_ab_joints.get('left_eye_jnt'), gt_ab_joints.get('head_jnt'))
    cmds.parent(gt_ab_joints.get('right_eye_jnt'), gt_ab_joints.get('head_jnt'))
    cmds.parent(gt_ab_joints.get('jaw_jnt'), gt_ab_joints.get('head_jnt'))
    
    cmds.parent(gt_ab_joints.get('spine01_jnt'), world=True)
    
    # Root Orients
    cog_orients = cmds.xform(gt_ab_settings.get('cog_proxy_crv'), q=True, ro=True)
    cmds.joint(gt_ab_joints.get('cog_jnt'), e=True, oj='none', zso=True) # ch
    cmds.setAttr(gt_ab_joints.get('cog_jnt') + '.jointOrientX', 90)
    cmds.setAttr(gt_ab_joints.get('cog_jnt') + '.jointOrientY', 0)
    cmds.setAttr(gt_ab_joints.get('cog_jnt') + '.jointOrientZ', 90)
    cmds.setAttr(gt_ab_joints.get('cog_jnt') + '.rz', cog_orients[0])
    cmds.makeIdentity(gt_ab_joints.get('cog_jnt'), apply=True, rotate=True)
    
    # Hip Orients
    hip_orients = cmds.xform(gt_ab_settings.get('hip_proxy_crv'), q=True, ro=True)
    cmds.joint(gt_ab_joints.get('hip_jnt'), e=True, oj='none', zso=True)
    cmds.setAttr(gt_ab_joints.get('hip_jnt') + '.jointOrientX', 90)
    cmds.setAttr(gt_ab_joints.get('hip_jnt') + '.jointOrientY', 0)
    cmds.setAttr(gt_ab_joints.get('hip_jnt') + '.jointOrientZ', 90)
    cmds.setAttr(gt_ab_joints.get('hip_jnt') + '.rz', hip_orients[0])
    cmds.makeIdentity(gt_ab_joints.get('hip_jnt'), apply=True, rotate=True)
    
    
    orient_to_target(gt_ab_joints.get('left_hip_jnt'), gt_ab_joints.get('left_knee_jnt'), (90,0,-90), gt_ab_settings.get('left_knee_proxy_crv'))
    orient_to_target(gt_ab_joints.get('left_knee_jnt'), gt_ab_joints.get('left_ankle_jnt'), (90,0,-90), gt_ab_settings.get('left_knee_proxy_crv'))
    
    orient_to_target(gt_ab_joints.get('right_hip_jnt'), gt_ab_joints.get('right_knee_jnt'), (90,0,-90), gt_ab_settings.get('right_knee_proxy_crv'), (-1,0,0))
    orient_to_target(gt_ab_joints.get('right_knee_jnt'), gt_ab_joints.get('right_ankle_jnt'), (90,0,-90), gt_ab_settings.get('right_knee_proxy_crv'), (-1,0,0))
    
    # Feet Orients
    # Left Foot
    orient_to_target(gt_ab_joints.get('left_ankle_jnt'), gt_ab_joints.get('left_ball_jnt'), (90,0,-90), gt_ab_settings.get('left_ankle_proxy_crv'))#, (-1,0,0))
    orient_to_target(gt_ab_joints.get('left_ball_jnt'), gt_ab_joints.get('left_toe_jnt'), (90,0,-90), gt_ab_settings.get('left_ball_proxy_crv'))#, (-1,0,0))
    # Right Foot
    orient_to_target(gt_ab_joints.get('right_ankle_jnt'), gt_ab_joints.get('right_ball_jnt'), (90,0,-90), gt_ab_settings.get('right_ankle_proxy_crv'), (-1,0,0))
    orient_to_target(gt_ab_joints.get('right_ball_jnt'), gt_ab_joints.get('right_toe_jnt'), (90,0,-90), gt_ab_settings.get('right_ball_proxy_crv'), (-1,0,0))


    # Right Leg Parenting
    cmds.parent(gt_ab_joints.get('right_knee_jnt'), gt_ab_joints.get('right_hip_jnt'))
    cmds.parent(gt_ab_joints.get('right_ankle_jnt'), gt_ab_joints.get('right_knee_jnt'))
    cmds.parent(gt_ab_joints.get('right_ball_jnt'), gt_ab_joints.get('right_ankle_jnt'))
    cmds.parent(gt_ab_joints.get('right_toe_jnt'), gt_ab_joints.get('right_ball_jnt'))
    
    # Left Leg Parenting
    cmds.parent(gt_ab_joints.get('left_knee_jnt'), gt_ab_joints.get('left_hip_jnt'))
    cmds.parent(gt_ab_joints.get('left_ankle_jnt'), gt_ab_joints.get('left_knee_jnt'))
    cmds.parent(gt_ab_joints.get('left_ball_jnt'), gt_ab_joints.get('left_ankle_jnt'))
    cmds.parent(gt_ab_joints.get('left_toe_jnt'), gt_ab_joints.get('left_ball_jnt'))

    # Reparenting
    cmds.parent(gt_ab_joints.get('hip_jnt'), gt_ab_joints.get('cog_jnt')) 
    cmds.parent(gt_ab_joints.get('left_hip_jnt'), gt_ab_joints.get('hip_jnt'))
    cmds.parent(gt_ab_joints.get('right_hip_jnt'), gt_ab_joints.get('hip_jnt'))
    cmds.parent(gt_ab_joints.get('spine01_jnt'), gt_ab_joints.get('cog_jnt'))
    cmds.parent(gt_ab_joints.get('cog_jnt'), gt_ab_joints.get('main_jnt'))
    
    # Oriented to their parent (end joints)
    for jnt in gt_ab_joints:
        joint = gt_ab_joints.get(jnt)
        if 'endJnt' in joint or gt_ab_joints.get('right_toe_jnt') in joint or gt_ab_joints.get('left_toe_jnt') in joint:
            cmds.setAttr(joint + '.jointOrientX', 0)
            cmds.setAttr(joint + '.jointOrientY', 0)
            cmds.setAttr(joint + '.jointOrientZ', 0)
    

    # Left Forearm Joint
    cmds.select(d=True)
    left_forearm_jnt = cmds.joint(name='left_forearm_' + jnt_suffix, radius=cmds.getAttr(gt_ab_joints.get('left_wrist_jnt') + '.radius')*.8)
    gt_ab_joints['left_forearm_' + jnt_suffix] = left_forearm_jnt
    cmds.delete(cmds.pointConstraint([gt_ab_joints.get('left_wrist_jnt'), gt_ab_joints.get('left_elbow_jnt')], gt_ab_joints.get('left_forearm_jnt')))
    orient_to_target(gt_ab_joints.get('left_forearm_jnt'), gt_ab_joints.get('left_wrist_jnt'), (-90,0,0))
    cmds.parent(gt_ab_joints.get('left_forearm_jnt'), gt_ab_joints.get('left_elbow_jnt'))
    change_viewport_color(gt_ab_joints.get('left_forearm_jnt'), (1,1,0))
    
    # Right Forearm Joint
    cmds.select(d=True)
    right_forearm_jnt = cmds.joint(name='right_forearm_' + jnt_suffix, radius=cmds.getAttr(gt_ab_joints.get('right_wrist_jnt') + '.radius')*.8)
    gt_ab_joints['right_forearm_' + jnt_suffix] = right_forearm_jnt
    cmds.delete(cmds.pointConstraint([gt_ab_joints.get('right_wrist_jnt'), gt_ab_joints.get('right_elbow_jnt')], gt_ab_joints.get('right_forearm_jnt')))
    orient_to_target(gt_ab_joints.get('right_forearm_jnt'), gt_ab_joints.get('right_wrist_jnt'), (90,0,0), aim_vec=(-1,0,0))
    cmds.parent(gt_ab_joints.get('right_forearm_jnt'), gt_ab_joints.get('right_elbow_jnt'))
    change_viewport_color(gt_ab_joints.get('right_forearm_jnt'), (1,1,0))

    # # Left Eye Orient
    # temp_transform = cmds.group(empty=True, world=True, name=gt_ab_settings.get('left_eye_proxy_crv') + '_orient_target')
    # cmds.delete(cmds.parentConstraint(gt_ab_settings.get('left_eye_proxy_crv'), temp_transform))
    # cmds.parent(temp_transform, gt_ab_settings.get('left_eye_proxy_crv'))
    # cmds.setAttr(temp_transform + '.tz', 1)
    # orient_to_target(gt_ab_joints.get('left_eye_jnt'), temp_transform, (0,0,0), gt_ab_settings.get('left_eye_proxy_crv'))#, (-1,0,0))
    # cmds.delete(temp_transform)

    # # Right Eye Orient
    # temp_transform = cmds.group(empty=True, world=True, name=gt_ab_settings.get('right_eye_proxy_crv') + '_orient_target')
    # cmds.delete(cmds.parentConstraint(gt_ab_settings.get('right_eye_proxy_crv'), temp_transform))
    # cmds.parent(temp_transform, gt_ab_settings.get('right_eye_proxy_crv'))
    # cmds.setAttr(temp_transform + '.tz', 1)
    # orient_to_target(gt_ab_joints.get('right_eye_jnt'), temp_transform, (0,0,0), gt_ab_settings.get('right_eye_proxy_crv'))#, (-1,0,0))
    # cmds.delete(temp_transform)


    # Set Preferred Angles
    cmds.setAttr(gt_ab_joints.get('left_hip_jnt') + '.preferredAngleZ', 90)
    cmds.setAttr(gt_ab_joints.get('right_hip_jnt') + '.preferredAngleZ', 90)
    cmds.setAttr(gt_ab_joints.get('left_knee_jnt') + '.preferredAngleZ', -90)
    cmds.setAttr(gt_ab_joints.get('right_knee_jnt') + '.preferredAngleZ', -90)
    
    # Create Skeleton Group
    skeleton_grp = cmds.group(name=('skeleton_' + grp_suffix), empty=True, world=True)
    change_outliner_color(skeleton_grp, (.75,.45,.95))  # Purple (Like a joint)
    cmds.parent(gt_ab_joints.get('main_jnt'), skeleton_grp)
    
    # Start Duplicating For IK/FK Switch
    ikfk_jnt_color = (1,.5,1)
    ik_jnt_scale = cmds.getAttr(gt_ab_joints.get('main_jnt') + '.radius')*1.5
    ik_jnt_color = (.5,.5 ,1)
    fk_jnt_scale = ik_jnt_scale/2
    fk_jnt_color = (1,.5,.5)
    
    # Left Arms FK/IK
    left_clavicle_switch_jnt = cmds.duplicate(gt_ab_joints.get('left_clavicle_jnt'), name=gt_ab_joints.get('left_clavicle_jnt').replace(jnt_suffix, 'switch_' + jnt_suffix), parentOnly=True)[0]
    cmds.setAttr(left_clavicle_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(left_clavicle_switch_jnt, ikfk_jnt_color)
    cmds.parent(left_clavicle_switch_jnt, skeleton_grp)
    cmds.parentConstraint(gt_ab_joints.get('left_clavicle_jnt'), left_clavicle_switch_jnt)
    
    # Left Arm IK
    left_shoulder_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_shoulder_jnt'), name=gt_ab_joints.get('left_shoulder_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_elbow_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_elbow_jnt'), name=gt_ab_joints.get('left_elbow_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_wrist_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_wrist_jnt'), name=gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(left_shoulder_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_elbow_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_wrist_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(left_shoulder_ik_jnt, ik_jnt_color)
    change_viewport_color(left_elbow_ik_jnt, ik_jnt_color)
    change_viewport_color(left_wrist_ik_jnt, ik_jnt_color)
    change_outliner_color(left_shoulder_ik_jnt, ik_jnt_color)
    change_outliner_color(left_elbow_ik_jnt, ik_jnt_color)
    change_outliner_color(left_wrist_ik_jnt, ik_jnt_color)
    
    cmds.parent(left_elbow_ik_jnt, left_shoulder_ik_jnt)
    cmds.parent(left_wrist_ik_jnt, left_elbow_ik_jnt)
    
    # Left Arm FK
    left_shoulder_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_shoulder_jnt'), name=gt_ab_joints.get('left_shoulder_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_elbow_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_elbow_jnt'), name=gt_ab_joints.get('left_elbow_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_wrist_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_wrist_jnt'), name=gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(left_shoulder_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_elbow_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_wrist_fk_jnt + '.radius', fk_jnt_scale)
    
    change_viewport_color(left_shoulder_fk_jnt, fk_jnt_color)
    change_viewport_color(left_elbow_fk_jnt, fk_jnt_color)
    change_viewport_color(left_wrist_fk_jnt, fk_jnt_color)
    change_outliner_color(left_shoulder_fk_jnt, fk_jnt_color)
    change_outliner_color(left_elbow_fk_jnt, fk_jnt_color)
    change_outliner_color(left_wrist_fk_jnt, fk_jnt_color)
    
    cmds.parent(left_shoulder_fk_jnt, left_clavicle_switch_jnt)
    cmds.parent(left_elbow_fk_jnt, left_shoulder_fk_jnt)
    cmds.parent(left_wrist_fk_jnt, left_elbow_fk_jnt)

    # right Arms FK/IK
    right_clavicle_switch_jnt = cmds.duplicate(gt_ab_joints.get('right_clavicle_jnt'), name=gt_ab_joints.get('right_clavicle_jnt').replace(jnt_suffix, 'switch_' + jnt_suffix), parentOnly=True)[0]
    cmds.setAttr(right_clavicle_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(right_clavicle_switch_jnt, ikfk_jnt_color)
    cmds.parent(right_clavicle_switch_jnt, skeleton_grp)
    cmds.parentConstraint(gt_ab_joints.get('right_clavicle_jnt'), right_clavicle_switch_jnt)
    
    # Right Arm IK
    right_shoulder_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_shoulder_jnt'), name=gt_ab_joints.get('right_shoulder_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_elbow_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_elbow_jnt'), name=gt_ab_joints.get('right_elbow_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_wrist_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_wrist_jnt'), name=gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(right_shoulder_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_elbow_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_wrist_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(right_shoulder_ik_jnt, ik_jnt_color)
    change_viewport_color(right_elbow_ik_jnt, ik_jnt_color)
    change_viewport_color(right_wrist_ik_jnt, ik_jnt_color)
    change_outliner_color(right_shoulder_ik_jnt, ik_jnt_color)
    change_outliner_color(right_elbow_ik_jnt, ik_jnt_color)
    change_outliner_color(right_wrist_ik_jnt, ik_jnt_color)
    
    cmds.parent(right_elbow_ik_jnt, right_shoulder_ik_jnt)
    cmds.parent(right_wrist_ik_jnt, right_elbow_ik_jnt)
    
    # Right Arm FK
    right_shoulder_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_shoulder_jnt'), name=gt_ab_joints.get('right_shoulder_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_elbow_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_elbow_jnt'), name=gt_ab_joints.get('right_elbow_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_wrist_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_wrist_jnt'), name=gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(right_shoulder_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_elbow_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_wrist_fk_jnt + '.radius', fk_jnt_scale)
    
    change_viewport_color(right_shoulder_fk_jnt, fk_jnt_color)
    change_viewport_color(right_elbow_fk_jnt, fk_jnt_color)
    change_viewport_color(right_wrist_fk_jnt, fk_jnt_color)
    change_outliner_color(right_shoulder_fk_jnt, fk_jnt_color)
    change_outliner_color(right_elbow_fk_jnt, fk_jnt_color)
    change_outliner_color(right_wrist_fk_jnt, fk_jnt_color)
    
    cmds.parent(right_shoulder_fk_jnt, right_clavicle_switch_jnt)
    cmds.parent(right_elbow_fk_jnt, right_shoulder_fk_jnt)
    cmds.parent(right_wrist_fk_jnt, right_elbow_fk_jnt)

    # Legs FK/IK Switch
    hip_switch_jnt = cmds.duplicate(gt_ab_joints.get('hip_jnt'), name=gt_ab_joints.get('hip_jnt').replace(jnt_suffix, 'switch_' + jnt_suffix), parentOnly=True)[0]
    cmds.setAttr(hip_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(hip_switch_jnt, ikfk_jnt_color)
    cmds.parent(hip_switch_jnt, skeleton_grp)
    cmds.parentConstraint(gt_ab_joints.get('hip_jnt'), hip_switch_jnt)

    # Left Leg IK
    left_hip_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_hip_jnt'), name=gt_ab_joints.get('left_hip_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_knee_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_knee_jnt'), name=gt_ab_joints.get('left_knee_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_ankle_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_ankle_jnt'), name=gt_ab_joints.get('left_ankle_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_ball_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_ball_jnt'), name=gt_ab_joints.get('left_ball_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    left_toe_ik_jnt = cmds.duplicate(gt_ab_joints.get('left_toe_jnt'), name=gt_ab_joints.get('left_toe_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(left_hip_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_knee_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_ankle_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_ball_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_toe_ik_jnt + '.radius', ik_jnt_scale)
  
    change_viewport_color(left_hip_ik_jnt, ik_jnt_color)
    change_viewport_color(left_knee_ik_jnt, ik_jnt_color)
    change_viewport_color(left_ankle_ik_jnt, ik_jnt_color)
    change_viewport_color(left_ball_ik_jnt, ik_jnt_color)
    change_viewport_color(left_toe_ik_jnt, ik_jnt_color)
    
    change_outliner_color(left_hip_ik_jnt, ik_jnt_color)
    change_outliner_color(left_knee_ik_jnt, ik_jnt_color)
    change_outliner_color(left_ankle_ik_jnt, ik_jnt_color)
    change_outliner_color(left_ball_ik_jnt, ik_jnt_color)
    change_outliner_color(left_toe_ik_jnt, ik_jnt_color)
  
    cmds.parent(left_hip_ik_jnt, hip_switch_jnt)
    cmds.parent(left_knee_ik_jnt, left_hip_ik_jnt)
    cmds.parent(left_ankle_ik_jnt, left_knee_ik_jnt)
    cmds.parent(left_ball_ik_jnt, left_ankle_ik_jnt)
    cmds.parent(left_toe_ik_jnt, left_ball_ik_jnt)

    # Left Leg FK
    left_hip_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_hip_jnt'), name=gt_ab_joints.get('left_hip_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_knee_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_knee_jnt'), name=gt_ab_joints.get('left_knee_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_ankle_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_ankle_jnt'), name=gt_ab_joints.get('left_ankle_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_ball_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_ball_jnt'), name=gt_ab_joints.get('left_ball_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    left_toe_fk_jnt = cmds.duplicate(gt_ab_joints.get('left_toe_jnt'), name=gt_ab_joints.get('left_toe_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(left_hip_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_knee_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_ankle_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_ball_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_toe_fk_jnt + '.radius', fk_jnt_scale)
  
    change_viewport_color(left_hip_fk_jnt, fk_jnt_color)
    change_viewport_color(left_knee_fk_jnt, fk_jnt_color)
    change_viewport_color(left_ankle_fk_jnt, fk_jnt_color)
    change_viewport_color(left_ball_fk_jnt, fk_jnt_color)
    change_viewport_color(left_toe_fk_jnt, fk_jnt_color)
    
    change_outliner_color(left_hip_fk_jnt, fk_jnt_color)
    change_outliner_color(left_knee_fk_jnt, fk_jnt_color)
    change_outliner_color(left_ankle_fk_jnt, fk_jnt_color)
    change_outliner_color(left_ball_fk_jnt, fk_jnt_color)
    change_outliner_color(left_toe_fk_jnt, fk_jnt_color)
  
    cmds.parent(left_hip_fk_jnt, hip_switch_jnt)
    cmds.parent(left_knee_fk_jnt, left_hip_fk_jnt)
    cmds.parent(left_ankle_fk_jnt, left_knee_fk_jnt)
    cmds.parent(left_ball_fk_jnt, left_ankle_fk_jnt)
    cmds.parent(left_toe_fk_jnt, left_ball_fk_jnt)

    # Right Leg IK
    right_hip_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_hip_jnt'), name=gt_ab_joints.get('right_hip_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_knee_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_knee_jnt'), name=gt_ab_joints.get('right_knee_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_ankle_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_ankle_jnt'), name=gt_ab_joints.get('right_ankle_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_ball_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_ball_jnt'), name=gt_ab_joints.get('right_ball_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    right_toe_ik_jnt = cmds.duplicate(gt_ab_joints.get('right_toe_jnt'), name=gt_ab_joints.get('right_toe_jnt').replace(jnt_suffix, 'ik_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(right_hip_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_knee_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_ankle_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_ball_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_toe_ik_jnt + '.radius', ik_jnt_scale)
  
    change_viewport_color(right_hip_ik_jnt, ik_jnt_color)
    change_viewport_color(right_knee_ik_jnt, ik_jnt_color)
    change_viewport_color(right_ankle_ik_jnt, ik_jnt_color)
    change_viewport_color(right_ball_ik_jnt, ik_jnt_color)
    change_viewport_color(right_toe_ik_jnt, ik_jnt_color)
    
    change_outliner_color(right_hip_ik_jnt, ik_jnt_color)
    change_outliner_color(right_knee_ik_jnt, ik_jnt_color)
    change_outliner_color(right_ankle_ik_jnt, ik_jnt_color)
    change_outliner_color(right_ball_ik_jnt, ik_jnt_color)
    change_outliner_color(right_toe_ik_jnt, ik_jnt_color)
  
    cmds.parent(right_hip_ik_jnt, hip_switch_jnt)
    cmds.parent(right_knee_ik_jnt, right_hip_ik_jnt)
    cmds.parent(right_ankle_ik_jnt, right_knee_ik_jnt)
    cmds.parent(right_ball_ik_jnt, right_ankle_ik_jnt)
    cmds.parent(right_toe_ik_jnt, right_ball_ik_jnt)

    # Right Leg FK
    right_hip_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_hip_jnt'), name=gt_ab_joints.get('right_hip_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_knee_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_knee_jnt'), name=gt_ab_joints.get('right_knee_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_ankle_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_ankle_jnt'), name=gt_ab_joints.get('right_ankle_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_ball_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_ball_jnt'), name=gt_ab_joints.get('right_ball_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    right_toe_fk_jnt = cmds.duplicate(gt_ab_joints.get('right_toe_jnt'), name=gt_ab_joints.get('right_toe_jnt').replace(jnt_suffix, 'fk_' + jnt_suffix), parentOnly=True)[0]
    
    cmds.setAttr(right_hip_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_knee_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_ankle_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_ball_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_toe_fk_jnt + '.radius', fk_jnt_scale)
  
    change_viewport_color(right_hip_fk_jnt, fk_jnt_color)
    change_viewport_color(right_knee_fk_jnt, fk_jnt_color)
    change_viewport_color(right_ankle_fk_jnt, fk_jnt_color)
    change_viewport_color(right_ball_fk_jnt, fk_jnt_color)
    change_viewport_color(right_toe_fk_jnt, fk_jnt_color)
    
    change_outliner_color(right_hip_fk_jnt, fk_jnt_color)
    change_outliner_color(right_knee_fk_jnt, fk_jnt_color)
    change_outliner_color(right_ankle_fk_jnt, fk_jnt_color)
    change_outliner_color(right_ball_fk_jnt, fk_jnt_color)
    change_outliner_color(right_toe_fk_jnt, fk_jnt_color)
  
    cmds.parent(right_hip_fk_jnt, hip_switch_jnt)
    cmds.parent(right_knee_fk_jnt, right_hip_fk_jnt)
    cmds.parent(right_ankle_fk_jnt, right_knee_fk_jnt)
    cmds.parent(right_ball_fk_jnt, right_ankle_fk_jnt)
    cmds.parent(right_toe_fk_jnt, right_ball_fk_jnt)

    # Start Creating Controls
    controls_grp = cmds.group(name='controls_' + grp_suffix, empty=True, world=True)
    change_outliner_color(controls_grp, (1,0.47,0.18))    
    
    # Main Ctrl
    main_ctrl = create_main_control(name='main_' + ctrl_suffix)
    main_ctrl_scale = cmds.xform(gt_ab_settings.get('main_crv'), q=True, ws=True, scale=True)
    cmds.scale( main_ctrl_scale[1], main_ctrl_scale[1], main_ctrl_scale[1], main_ctrl )

    cmds.makeIdentity(main_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(main_ctrl, s=True, f=True) or []:
        try:
            cmds.setAttr(shape + '.lineWidth', 3)
        except:
            pass
            
    change_viewport_color(main_ctrl, (1,0.171,0.448))
    main_ctrl_grp = cmds.group(name=main_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(main_ctrl, main_ctrl_grp)
    cmds.parent(main_ctrl_grp, controls_grp)
    
    # Direction Control
    direction_ctrl = cmds.circle(name='direction_' + ctrl_suffix, nr=(0,1,0), ch=False, radius=44.5)[0]
    for shape in cmds.listRelatives(direction_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(direction_ctrl))
    change_viewport_color(direction_ctrl, (1,1,0))
    cmds.delete(cmds.scaleConstraint(gt_ab_settings.get('main_crv'), direction_ctrl))
    cmds.makeIdentity(direction_ctrl, apply=True, scale=True)
    direction_ctrl_grp = cmds.group(name=direction_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(direction_ctrl, direction_ctrl_grp)
    cmds.parent(direction_ctrl_grp, main_ctrl)
    cmds.rebuildCurve(direction_ctrl, ch=False,rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=20, d=3, tol=0.01)
    
    # COG Control
    cog_ctrl = cmds.circle(name=gt_ab_joints.get('cog_jnt').replace(jnt_suffix, '') + ctrl_suffix, nr=(1,0,0), ch=False, radius=general_scale_offset)[0]
    for shape in cmds.listRelatives(cog_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(cog_ctrl))
    change_viewport_color(cog_ctrl, (1,1,0))
    cmds.makeIdentity(cog_ctrl, apply=True, scale=True)
    cog_ctrl_grp = cmds.group(name=cog_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(cog_ctrl, cog_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('cog_jnt'), cog_ctrl_grp))
    cmds.parent(cog_ctrl_grp, direction_ctrl)
    
    # Hip Control
    hip_ctrl = cmds.curve(name=gt_ab_joints.get('hip_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.159, 0.671, -0.185], [-0.185, 0.674, -0.001], [-0.159, 0.65, 0.185], [-0.05, 0.592, 0.366], [0.037, 0.515, 0.493], [0.12, 0.406, 0.632], [-0.062, -0.0, 0.818], [0.12, -0.406, 0.632], [0.037, -0.515, 0.493], [-0.05, -0.592, 0.366], [-0.159, -0.65, 0.185], [-0.183, -0.671, -0.001], [-0.159, -0.65, -0.185], [-0.05, -0.592, -0.366], [0.037, -0.515, -0.493], [0.12, -0.406, -0.632], [-0.062, 0.0, -0.818], [0.12, 0.406, -0.632], [0.037, 0.515, -0.493], [-0.05, 0.606, -0.366]],d=3)
    cmds.setAttr(hip_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(hip_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(hip_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(hip_ctrl, apply=True, scale=True)
    cmds.closeCurve(hip_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(hip_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(hip_ctrl))
    change_viewport_color(hip_ctrl, (.8,.8,0))
    hip_ctrl_grp = cmds.group(name=hip_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(hip_ctrl, hip_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('hip_jnt'), hip_ctrl_grp))
    cmds.parent(hip_ctrl_grp, cog_ctrl)
    
    
    # Spine01 Control
    spine01_ctrl = cmds.curve(name=gt_ab_joints.get('spine01_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299], [-0.061, -0.895, -0.126], [-0.061, -0.912, -0.002], [-0.061, -0.894, 0.13], [-0.121, -0.836, 0.299], [0.0, -0.836, 0.299], [0.121, -0.836, 0.299], [0.061, -0.894, 0.13], [0.061, -0.912, -0.002], [0.061, -0.895, -0.126]],d=3)
    cmds.setAttr(spine01_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine01_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine01_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine01_ctrl, apply=True, scale=True)
    cmds.closeCurve(spine01_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(spine01_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(spine01_ctrl))
    change_viewport_color(spine01_ctrl, automation_ctrl_color)
    spine01_ctrl_grp = cmds.group(name=spine01_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(spine01_ctrl, spine01_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('spine01_jnt'), spine01_ctrl_grp))
    cmds.parent(spine01_ctrl_grp, cog_ctrl)
    
    # Spine02 Control
    spine02_ctrl = cmds.curve(name=gt_ab_joints.get('spine02_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.114, -0.849, -0.261], [0.0, -0.849, -0.261], [-0.114, -0.849, -0.261], [-0.053, -0.9, -0.105], [-0.061, -0.909, -0.001], [-0.053, -0.899, 0.109], [-0.114, -0.849, 0.261], [0.0, -0.849, 0.261], [0.114, -0.849, 0.261], [0.053, -0.899, 0.109], [0.061, -0.909, -0.001], [0.053, -0.9, -0.105]],d=3)
    cmds.setAttr(spine02_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine02_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine02_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine02_ctrl, apply=True, scale=True)
    cmds.closeCurve(spine02_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(spine02_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(spine02_ctrl))
    change_viewport_color(spine02_ctrl, (.8,.8,0))
    spine02_ctrl_grp = cmds.group(name=spine02_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(spine02_ctrl, spine02_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('spine02_jnt'), spine02_ctrl_grp))
    cmds.parent(spine02_ctrl_grp, spine01_ctrl)
    
    # Spine03 Control
    spine03_ctrl = cmds.curve(name=gt_ab_joints.get('spine03_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.089, -0.869, -0.2], [-0.0, -0.869, -0.2], [-0.089, -0.869, -0.2], [-0.058, -0.901, -0.092], [-0.053, -0.908, -0.001], [-0.058, -0.901, 0.094], [-0.089, -0.869, 0.2], [-0.0, -0.869, 0.2], [0.089, -0.869, 0.2], [0.058, -0.901, 0.094], [0.053, -0.908, -0.001], [0.058, -0.901, -0.092]],d=3)
    cmds.setAttr(spine03_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine03_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine03_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine03_ctrl, apply=True, scale=True)
    cmds.closeCurve(spine03_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(spine03_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(spine03_ctrl))
    change_viewport_color(spine03_ctrl, automation_ctrl_color)
    spine03_ctrl_grp = cmds.group(name=spine03_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(spine03_ctrl, spine03_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('spine03_jnt'), spine03_ctrl_grp))
    cmds.parent(spine03_ctrl_grp, spine02_ctrl)
    
    # Spine04 Control
    spine04_ctrl = cmds.curve(name=gt_ab_joints.get('spine04_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.103, -0.881, -0.16], [0.0, -0.881, -0.16], [-0.103, -0.881, -0.16], [-0.023, -0.918, 0.0], [-0.103, -0.881, 0.16], [0.0, -0.881, 0.16], [0.103, -0.881, 0.16], [0.023, -0.918, 0.0]],d=3)
    cmds.setAttr(spine04_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine04_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine04_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine04_ctrl, apply=True, scale=True)
    cmds.closeCurve(spine04_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(spine04_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(spine04_ctrl))
    change_viewport_color(spine04_ctrl, (.8,.8,0))
    spine04_ctrl_grp = cmds.group(name=spine04_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(spine04_ctrl, spine04_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('spine04_jnt'), spine04_ctrl_grp))
    cmds.parent(spine04_ctrl_grp, spine03_ctrl)
    
    # Neck Base Control
    neck_base_ctrl = cmds.curve(name=gt_ab_joints.get('neck_base_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.064, -0.894, -0.111], [-0.0, -0.894, -0.111], [-0.064, -0.894, -0.111], [-0.05, -0.904, -0.052], [-0.032, -0.907, 0.0], [-0.05, -0.904, 0.052], [-0.064, -0.894, 0.111], [0.0, -0.894, 0.111], [0.064, -0.894, 0.111], [0.05, -0.904, 0.052], [0.032, -0.907, 0.0], [0.05, -0.904, -0.052]],d=3)
    cmds.setAttr(neck_base_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(neck_base_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(neck_base_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(neck_base_ctrl, apply=True, scale=True)
    cmds.closeCurve(neck_base_ctrl, ch=False, ps=False, rpo=True)
    for shape in cmds.listRelatives(neck_base_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(neck_base_ctrl))
    change_viewport_color(neck_base_ctrl, (.8,.8,0))
    neck_base_ctrl_grp = cmds.group(name=neck_base_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(neck_base_ctrl, neck_base_ctrl_grp)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('neck_base_jnt'), neck_base_ctrl_grp))
    cmds.parent(neck_base_ctrl_grp, spine04_ctrl)
        
    # Neck Mid Control
    neck_mid_ctrl = cmds.curve(name=gt_ab_joints.get('neck_mid_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.039, -0.899, -0.084], [0.0, -0.899, -0.084], [-0.039, -0.899, -0.084], [-0.024, -0.905, -0.039], [-0.017, -0.907, 0.0], [-0.024, -0.905, 0.039], [-0.039, -0.899, 0.084], [0.0, -0.899, 0.084], [0.039, -0.899, 0.084], [0.024, -0.905, 0.039], [0.017, -0.907, 0.0], [0.024, -0.905, -0.039]],d=3)
    cmds.setAttr(neck_mid_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(neck_mid_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(neck_mid_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(neck_mid_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(neck_mid_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(neck_mid_ctrl))
    change_viewport_color(neck_mid_ctrl, automation_ctrl_color)
    neck_mid_ctrl_grp = cmds.group(name=neck_mid_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(neck_mid_ctrl, neck_mid_ctrl_grp)
    cmds.parent(neck_mid_ctrl_grp, neck_base_ctrl)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('neck_mid_jnt'), neck_mid_ctrl_grp))
    desired_pivot = cmds.xform(neck_mid_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('neck_base_jnt'), neck_mid_ctrl))
    cmds.xform(neck_mid_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(neck_mid_ctrl, apply=True, scale=True, rotate=True, translate=True)
    cmds.closeCurve(neck_mid_ctrl, ch=False, ps=False, rpo=True)
    
    # Head Control
    head_ctrl = cmds.curve(name=gt_ab_joints.get('head_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.141, 0.529, -0.529], [0.141, 0.0, -0.748], [0.141, -0.529, -0.529], [0.141, -0.748, -0.0], [0.141, -0.529, 0.529], [0.141, -0.0, 0.748], [0.141, 0.529, 0.529], [0.141, 0.748, 0.0]],d=3)
    cmds.setAttr(head_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(head_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(head_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(head_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(head_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(head_ctrl))
    change_viewport_color(head_ctrl, (.8,.8,0))
    head_ctrl_grp = cmds.group(name=head_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(head_ctrl, head_ctrl_grp)
    cmds.parent(head_ctrl_grp, neck_mid_ctrl)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('head_jnt'), head_ctrl_grp))
    desired_pivot = cmds.xform(head_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('head_end_jnt'), head_ctrl))
    cmds.xform(head_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(head_ctrl, apply=True, scale=True, rotate=True, translate=True)
    cmds.closeCurve(head_ctrl, ch=False, ps=False, rpo=True)
    
    # Jaw Control
    jaw_ctrl = cmds.curve(name=gt_ab_joints.get('jaw_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.013, 0.088, -0.088], [0.013, 0.016, -0.125], [0.013, 0.042, -0.088], [0.013, 0.078, -0.0], [0.013, 0.042, 0.088], [0.013, 0.016, 0.125], [0.013, 0.088, 0.088], [0.013, 0.125, 0.0]],d=3)
    cmds.setAttr(jaw_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(jaw_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(jaw_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(jaw_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(jaw_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(jaw_ctrl))
    change_viewport_color(jaw_ctrl, (.8,.8,0))
    jaw_ctrl_grp = cmds.group(name=jaw_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(jaw_ctrl, jaw_ctrl_grp)
    cmds.parent(jaw_ctrl_grp, head_ctrl)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('jaw_jnt'), jaw_ctrl_grp))
    desired_pivot = cmds.xform(jaw_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('jaw_end_jnt'), jaw_ctrl))
    cmds.xform(jaw_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(jaw_ctrl, apply=True, scale=True, rotate=True, translate=True)
    cmds.closeCurve(jaw_ctrl, ch=False, ps=False, rpo=True)

    # Eye Controls
    left_eye_ctrl = cmds.curve(name=gt_ab_joints.get('left_eye_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.098, -0.098, -0.0], [0.139, -0.0, -0.0], [0.098, 0.098, 0.0], [0.0, 0.139, 0.0], [-0.098, 0.098, 0.0], [-0.139, 0.0, 0.0], [-0.098, -0.098, -0.0], [-0.0, -0.139, -0.0]],d=3)
    right_eye_ctrl = cmds.curve(name=gt_ab_joints.get('right_eye_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.098, -0.098, -0.0], [0.139, -0.0, -0.0], [0.098, 0.098, 0.0], [0.0, 0.139, 0.0], [-0.098, 0.098, 0.0], [-0.139, 0.0, 0.0], [-0.098, -0.098, -0.0], [-0.0, -0.139, -0.0]],d=3)
    main_eye_ctrl = cmds.curve(name=gt_ab_joints.get('right_eye_jnt').replace(jnt_suffix, '').replace('right','main') + ctrl_suffix, p=[[0.315, -0.242, -0.0], [0.446, -0.0, -0.0], [0.315, 0.242, 0.0], [0.0, 0.105, 0.0], [-0.315, 0.242, 0.0], [-0.446, 0.0, 0.0], [-0.315, -0.242, -0.0], [-0.0, -0.105, -0.0]],d=3)
    temp_transform = cmds.group(name='temporary_eye_finder_transform', empty=True, world=True)
    
    # Rename Shapes
    for shape in cmds.listRelatives(left_eye_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_eye_ctrl))
    for shape in cmds.listRelatives(right_eye_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_eye_ctrl))
    for shape in cmds.listRelatives(main_eye_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(main_eye_ctrl))
    
    # Create Control Groups
    left_eye_ctrl_grp = cmds.group(name=left_eye_ctrl + '_' + grp_suffix, empty=True, world=True)
    right_eye_ctrl_grp = cmds.group(name=right_eye_ctrl + '_' + grp_suffix, empty=True, world=True)
    main_eye_ctrl_grp = cmds.group(name=main_eye_ctrl + '_' + grp_suffix, empty=True, world=True)
    
    # Assemble Hierarchy
    cmds.parent(left_eye_ctrl, left_eye_ctrl_grp)
    cmds.parent(right_eye_ctrl, right_eye_ctrl_grp)
    cmds.parent(main_eye_ctrl, main_eye_ctrl_grp)
    cmds.parent(left_eye_ctrl_grp, main_eye_ctrl)
    cmds.parent(right_eye_ctrl_grp, main_eye_ctrl)
    
    # Position Elements
    cmds.move(.2,0,0, left_eye_ctrl_grp)
    cmds.move(-.2,0,0, right_eye_ctrl_grp)
    
    # Find Position
    cmds.delete(cmds.pointConstraint([gt_ab_joints.get('left_eye_jnt'),gt_ab_joints.get('right_eye_jnt')], temp_transform))
    cmds.move(0,0,general_scale_offset * 2, temp_transform, relative=True)
    desired_position = cmds.xform(temp_transform, q=True, t=True)
    cmds.delete(temp_transform)
    cmds.move(desired_position[0], desired_position[1], desired_position[2], main_eye_ctrl_grp)
    
    # Find Scale
    left_eye_position = abs(cmds.xform(gt_ab_joints.get('left_eye_jnt'), q=True, ws=True, t=True)[0])
    right_eye_position = abs(cmds.xform(gt_ab_joints.get('right_eye_jnt'), q=True, ws=True, t=True)[0])
    
    main_eye_scale = (right_eye_position + left_eye_position)*3
    
    cmds.setAttr(main_eye_ctrl_grp + '.scaleX', main_eye_scale)
    cmds.setAttr(main_eye_ctrl_grp + '.scaleY', main_eye_scale)
    cmds.setAttr(main_eye_ctrl_grp + '.scaleZ', main_eye_scale)
    cmds.makeIdentity(main_eye_ctrl_grp, apply=True, scale=True)
    
    # Finish Eye Control Look
    cmds.closeCurve(left_eye_ctrl, ch=False, ps=False, rpo=True)
    cmds.closeCurve(right_eye_ctrl, ch=False, ps=False, rpo=True)
    cmds.closeCurve(main_eye_ctrl, ch=False, ps=False, rpo=True)
    
    change_viewport_color(left_eye_ctrl, left_ctrl_color)
    change_viewport_color(right_eye_ctrl, right_ctrl_color)
    change_viewport_color(main_eye_ctrl_grp, (1,1,0))
    
    cmds.parent(main_eye_ctrl_grp, head_ctrl)
    
    
    ################# Left Leg FK #################
    # Calculate Scale Offset
    left_leg_scale_offset = 0
    left_leg_scale_offset += cmds.xform(gt_ab_joints.get('left_ankle_jnt'), q=True, t=True)[0]
    left_leg_scale_offset += cmds.xform(gt_ab_joints.get('left_knee_jnt'), q=True, t=True)[0]
    left_leg_scale_offset = left_leg_scale_offset
    
    # Left Hip FK
    left_hip_ctrl = cmds.curve(name=gt_ab_joints.get('left_hip_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_hip_ctrl_grp = cmds.group(name=left_hip_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_hip_ctrl, left_hip_ctrl_grp)
    
    for shape in cmds.listRelatives(left_hip_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_hip_ctrl))

    cmds.setAttr(left_hip_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_hip_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_hip_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_hip_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_hip_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_hip_jnt'), left_hip_ctrl_grp))
    change_viewport_color(left_hip_ctrl, left_ctrl_color)
    cmds.parent(left_hip_ctrl_grp, hip_ctrl)
    
    # Adjust Size
    left_leg_scale_offset = left_leg_scale_offset*.8
    
    # Left Knee FK
    left_knee_ctrl = cmds.curve(name=gt_ab_joints.get('left_knee_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_knee_ctrl_grp = cmds.group(name=left_knee_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_knee_ctrl, left_knee_ctrl_grp)
    
    for shape in cmds.listRelatives(left_knee_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_knee_ctrl))
    
    cmds.setAttr(left_knee_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_knee_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_knee_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_knee_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_knee_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_knee_jnt'), left_knee_ctrl_grp))
    change_viewport_color(left_knee_ctrl, left_ctrl_color)
    cmds.parent(left_knee_ctrl_grp, left_hip_ctrl)
    
    # Left Ankle FK
    left_ankle_ctrl = cmds.curve(name=gt_ab_joints.get('left_ankle_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_ankle_ctrl_grp = cmds.group(name=left_ankle_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_ankle_ctrl, left_ankle_ctrl_grp)
    
    for shape in cmds.listRelatives(left_ankle_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_ankle_ctrl))
    
    cmds.setAttr(left_ankle_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_ankle_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_ankle_ctrl + '.scaleZ', left_leg_scale_offset)

    cmds.makeIdentity(left_ankle_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_ankle_jnt'), left_ankle_ctrl_grp))
    change_viewport_color(left_ankle_ctrl, left_ctrl_color)
    
    temp_transform = cmds.group(name=left_ankle_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_toe_jnt'), temp_transform))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_ankle_jnt'), temp_transform, skip=['x','z']))
    cmds.delete(cmds.aimConstraint(temp_transform, left_ankle_ctrl, offset=(0,0,0), aimVector=(0,1,0), upVector=(1,0,0), worldUpType="vector", worldUpVector=(0,-1,0)))
    cmds.delete(temp_transform)
    cmds.makeIdentity(left_ankle_ctrl, apply=True, rotate=True)
    cmds.closeCurve(left_ankle_ctrl, ch=False, ps=False, rpo=True)
    cmds.parent(left_ankle_ctrl_grp, left_knee_ctrl)
    
    # Left Ball FK
    left_ball_ctrl = cmds.curve(name=gt_ab_joints.get('left_ball_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_ball_ctrl_grp = cmds.group(name=left_ball_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_ball_ctrl, left_ball_ctrl_grp)
    
    for shape in cmds.listRelatives(left_ball_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_ball_ctrl))
    
    cmds.setAttr(left_ball_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_ball_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_ball_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_ball_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_ball_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_ball_jnt'), left_ball_ctrl_grp))
    change_viewport_color(left_ball_ctrl, left_ctrl_color)
    cmds.parent(left_ball_ctrl_grp, left_ankle_ctrl)
    
    ################# Left Leg IK Control #################
    left_knee_scale_offset = 0
    left_knee_scale_offset += cmds.xform(gt_ab_joints.get('left_ankle_jnt'), q=True, t=True)[0]
    left_knee_scale_offset += cmds.xform(gt_ab_joints.get('left_knee_jnt'), q=True, t=True)[0]
    left_knee_scale_offset = left_knee_scale_offset/2
    
    # Left Knee Pole Vector Ctrl
    left_knee_ik_ctrl = cmds.curve(name=gt_ab_joints.get('left_knee_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125], [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]],d=1)
    left_knee_ik_ctrl_grp = cmds.group(name=left_knee_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_knee_ik_ctrl, left_knee_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(left_knee_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_knee_ik_ctrl))
    
    # Left Knee Find Position
    temp_transform = cmds.group(name=left_knee_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('left_knee_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(gt_ab_settings.get('left_knee_pv_dir'), temp_transform, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,-1,0), worldUpType="vector", worldUpVector=(0,1,0)))
    cmds.move(left_knee_scale_offset ,0 , 0, temp_transform, os=True, relative=True)    
    cmds.delete(cmds.pointConstraint(temp_transform, left_knee_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Left Knee Pole Vec Visibility and Parenting
    cmds.setAttr(left_knee_ik_ctrl + '.scaleX', left_knee_scale_offset)
    cmds.setAttr(left_knee_ik_ctrl + '.scaleY', left_knee_scale_offset)
    cmds.setAttr(left_knee_ik_ctrl + '.scaleZ', left_knee_scale_offset)
    cmds.makeIdentity(left_knee_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_knee_ik_ctrl, left_ctrl_color)
    cmds.parent(left_knee_ik_ctrl_grp, direction_ctrl)
    
    ################# Left Foot IK Control #################
    left_foot_ik_ctrl = cmds.curve(name='left_foot_ik_' + ctrl_suffix, p=[[-0.183, 0.0, -0.323], [-0.197, 0.0, -0.428], [-0.184, 0.0, -0.521], [-0.15, 0.0, -0.575], [-0.114, 0.0, -0.611], [-0.076, 0.0, -0.631], [-0.036, 0.0, -0.641], [0.006, 0.0, -0.635], [0.047, 0.0, -0.62], [0.087, 0.0, -0.587], [0.127, 0.0, -0.538], [0.149, 0.0, -0.447], [0.146, 0.0, -0.34], [0.153, 0.0, -0.235], [0.173, 0.0, -0.136], [0.202, 0.0, -0.05], [0.23, 0.0, 0.039], [0.259, 0.0, 0.154], [0.27, 0.0, 0.234], [0.267, 0.0, 0.338], [0.247, 0.0, 0.426], [0.22, 0.0, 0.496], [0.187, 0.0, 0.553], [0.153, 0.0, 0.597], [0.116, 0.0, 0.628], [0.076, 0.0, 0.65], [0.036, 0.0, 0.66], [-0.006, 0.0, 0.656], [-0.045, 0.0, 0.638], [-0.087, 0.0, 0.611], [-0.127, 0.0, 0.571], [-0.164, 0.0, 0.517], [-0.199, 0.0, 0.451], [-0.228, 0.0, 0.366], [-0.242, 0.0, 0.263], [-0.239, 0.0, 0.181], [-0.224, 0.0, 0.063], [-0.206, 0.0, -0.028], [-0.187, 0.0, -0.117], [-0.177, 0.0, -0.216], [-0.183, 0.0, -0.323]],d=1)
    left_foot_ik_ctrl_grp = cmds.group(name=left_foot_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_foot_ik_ctrl, left_foot_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(left_foot_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_foot_ik_ctrl))
    
    # Left Foot Scale
    left_foot_scale_offset = 0
    left_foot_scale_offset += cmds.xform(gt_ab_joints.get('left_ball_jnt'), q=True, t=True)[0]
    left_foot_scale_offset += cmds.xform(gt_ab_joints.get('left_toe_jnt'), q=True, t=True)[0]
    cmds.setAttr(left_foot_ik_ctrl + '.scaleX', left_foot_scale_offset)
    cmds.setAttr(left_foot_ik_ctrl + '.scaleY', left_foot_scale_offset)
    cmds.setAttr(left_foot_ik_ctrl + '.scaleZ', left_foot_scale_offset)
    cmds.makeIdentity(left_foot_ik_ctrl, apply=True, scale=True)
    
    # Left Foot Position
    cmds.delete(cmds.pointConstraint([gt_ab_joints.get('left_ankle_jnt'), gt_ab_joints.get('left_toe_jnt')], left_foot_ik_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(left_foot_ik_ctrl_grp + '.ry', desired_rotation[1])
    
    # Left Foot Pivot Adjustment
    cmds.xform(left_foot_ik_ctrl_grp, piv=desired_translation, ws=True)
    cmds.xform(left_foot_ik_ctrl, piv=desired_translation, ws=True)
    
    # Left Foot General Adjustments
    change_viewport_color(left_foot_ik_ctrl, left_ctrl_color)
    cmds.parent(left_foot_ik_ctrl_grp, direction_ctrl)
    
    ################# Right Leg FK #################
    # Calculate Scale Offset
    right_leg_scale_offset = 0
    right_leg_scale_offset += cmds.xform(gt_ab_joints.get('right_ankle_jnt'), q=True, t=True)[0]
    right_leg_scale_offset += cmds.xform(gt_ab_joints.get('right_knee_jnt'), q=True, t=True)[0]
    right_leg_scale_offset = right_leg_scale_offset
    
    # Right Hip FK
    right_hip_ctrl = cmds.curve(name=gt_ab_joints.get('right_hip_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_hip_ctrl_grp = cmds.group(name=right_hip_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_hip_ctrl, right_hip_ctrl_grp)
    
    for shape in cmds.listRelatives(right_hip_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_hip_ctrl))

    cmds.setAttr(right_hip_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_hip_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_hip_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_hip_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_hip_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_hip_jnt'), right_hip_ctrl_grp))
    change_viewport_color(right_hip_ctrl, right_ctrl_color)
    cmds.parent(right_hip_ctrl_grp, hip_ctrl)
    
    # Adjust Size
    right_leg_scale_offset = right_leg_scale_offset*.8
    
    # Right Knee FK
    right_knee_ctrl = cmds.curve(name=gt_ab_joints.get('right_knee_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_knee_ctrl_grp = cmds.group(name=right_knee_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_knee_ctrl, right_knee_ctrl_grp)
    
    for shape in cmds.listRelatives(right_knee_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_knee_ctrl))
    
    cmds.setAttr(right_knee_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_knee_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_knee_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_knee_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_knee_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_knee_jnt'), right_knee_ctrl_grp))
    change_viewport_color(right_knee_ctrl, right_ctrl_color)
    cmds.parent(right_knee_ctrl_grp, right_hip_ctrl)
    
    # Right Ankle FK
    right_ankle_ctrl = cmds.curve(name=gt_ab_joints.get('right_ankle_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_ankle_ctrl_grp = cmds.group(name=right_ankle_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_ankle_ctrl, right_ankle_ctrl_grp)
    
    for shape in cmds.listRelatives(right_ankle_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_ankle_ctrl))
    
    cmds.setAttr(right_ankle_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_ankle_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_ankle_ctrl + '.scaleZ', right_leg_scale_offset)

    cmds.makeIdentity(right_ankle_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_ankle_jnt'), right_ankle_ctrl_grp))
    change_viewport_color(right_ankle_ctrl, right_ctrl_color)
    
    temp_transform = cmds.group(name=right_ankle_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_toe_jnt'), temp_transform))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_ankle_jnt'), temp_transform, skip=['x','z']))
    cmds.delete(cmds.aimConstraint(temp_transform, right_ankle_ctrl, offset=(0,0,0), aimVector=(0,1,0), upVector=(1,0,0), worldUpType="vector", worldUpVector=(0,-1,0)))
    cmds.delete(temp_transform)
    cmds.makeIdentity(right_ankle_ctrl, apply=True, rotate=True)
    cmds.closeCurve(right_ankle_ctrl, ch=False, ps=False, rpo=True)
    cmds.parent(right_ankle_ctrl_grp, right_knee_ctrl)
    
    # Right Ball FK
    right_ball_ctrl = cmds.curve(name=gt_ab_joints.get('right_ball_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_ball_ctrl_grp = cmds.group(name=right_ball_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_ball_ctrl, right_ball_ctrl_grp)
    
    for shape in cmds.listRelatives(right_ball_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_ball_ctrl))
    
    cmds.setAttr(right_ball_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_ball_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_ball_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_ball_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_ball_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_ball_jnt'), right_ball_ctrl_grp))
    change_viewport_color(right_ball_ctrl, right_ctrl_color)
    cmds.parent(right_ball_ctrl_grp, right_ankle_ctrl)
    
    ################# Right Leg IK Control #################
    right_knee_scale_offset = 0
    right_knee_scale_offset += cmds.xform(gt_ab_joints.get('right_ankle_jnt'), q=True, t=True)[0]
    right_knee_scale_offset += cmds.xform(gt_ab_joints.get('right_knee_jnt'), q=True, t=True)[0]
    right_knee_scale_offset = right_knee_scale_offset/2
    
    # Right Knee Pole Vector Ctrl
    right_knee_ik_ctrl = cmds.curve(name=gt_ab_joints.get('right_knee_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125], [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]],d=1)
    right_knee_ik_ctrl_grp = cmds.group(name=right_knee_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_knee_ik_ctrl, right_knee_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(right_knee_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_knee_ik_ctrl))
    
    # Right Knee Find Position
    temp_transform = cmds.group(name=right_knee_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('right_knee_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(gt_ab_settings.get('right_knee_pv_dir'), temp_transform, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,-1,0), worldUpType="vector", worldUpVector=(0,1,0)))
    cmds.move(right_knee_scale_offset*-1 ,0 , 0, temp_transform, os=True, relative=True)    
    cmds.delete(cmds.pointConstraint(temp_transform, right_knee_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Right Knee Pole Vec Visibility and Parenting
    cmds.setAttr(right_knee_ik_ctrl + '.scaleX', right_knee_scale_offset)
    cmds.setAttr(right_knee_ik_ctrl + '.scaleY', right_knee_scale_offset)
    cmds.setAttr(right_knee_ik_ctrl + '.scaleZ', right_knee_scale_offset)
    cmds.makeIdentity(right_knee_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_knee_ik_ctrl, right_ctrl_color)
    cmds.parent(right_knee_ik_ctrl_grp, direction_ctrl)
    
    ################# Right Foot IK Control #################
    right_foot_ik_ctrl = cmds.curve(name='right_foot_ik_' + ctrl_suffix, p=[[-0.183, 0.0, -0.323], [-0.197, 0.0, -0.428], [-0.184, 0.0, -0.521], [-0.15, 0.0, -0.575], [-0.114, 0.0, -0.611], [-0.076, 0.0, -0.631], [-0.036, 0.0, -0.641], [0.006, 0.0, -0.635], [0.047, 0.0, -0.62], [0.087, 0.0, -0.587], [0.127, 0.0, -0.538], [0.149, 0.0, -0.447], [0.146, 0.0, -0.34], [0.153, 0.0, -0.235], [0.173, 0.0, -0.136], [0.202, 0.0, -0.05], [0.23, 0.0, 0.039], [0.259, 0.0, 0.154], [0.27, 0.0, 0.234], [0.267, 0.0, 0.338], [0.247, 0.0, 0.426], [0.22, 0.0, 0.496], [0.187, 0.0, 0.553], [0.153, 0.0, 0.597], [0.116, 0.0, 0.628], [0.076, 0.0, 0.65], [0.036, 0.0, 0.66], [-0.006, 0.0, 0.656], [-0.045, 0.0, 0.638], [-0.087, 0.0, 0.611], [-0.127, 0.0, 0.571], [-0.164, 0.0, 0.517], [-0.199, 0.0, 0.451], [-0.228, 0.0, 0.366], [-0.242, 0.0, 0.263], [-0.239, 0.0, 0.181], [-0.224, 0.0, 0.063], [-0.206, 0.0, -0.028], [-0.187, 0.0, -0.117], [-0.177, 0.0, -0.216], [-0.183, 0.0, -0.323]],d=1)
    right_foot_ik_ctrl_grp = cmds.group(name=right_foot_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_foot_ik_ctrl, right_foot_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(right_foot_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_foot_ik_ctrl))
    
    # Right Foot Scale
    right_foot_scale_offset = 0
    right_foot_scale_offset += cmds.xform(gt_ab_joints.get('right_ball_jnt'), q=True, t=True)[0]
    right_foot_scale_offset += cmds.xform(gt_ab_joints.get('right_toe_jnt'), q=True, t=True)[0]
    cmds.setAttr(right_foot_ik_ctrl + '.scaleX', right_foot_scale_offset)
    cmds.setAttr(right_foot_ik_ctrl + '.scaleY', right_foot_scale_offset)
    cmds.setAttr(right_foot_ik_ctrl + '.scaleZ', right_foot_scale_offset*-1)
    cmds.makeIdentity(right_foot_ik_ctrl, apply=True, scale=True)
    
    # Right Foot Position
    cmds.delete(cmds.pointConstraint([gt_ab_joints.get('right_ankle_jnt'), gt_ab_joints.get('right_toe_jnt')], right_foot_ik_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(right_foot_ik_ctrl_grp + '.ry', desired_rotation[1])
    
    # Right Foot Pivot Adjustment
    cmds.xform(right_foot_ik_ctrl_grp, piv=desired_translation, ws=True)
    cmds.xform(right_foot_ik_ctrl, piv=desired_translation, ws=True)
    
    # Right Foot General Adjustments
    change_viewport_color(right_foot_ik_ctrl, right_ctrl_color)
    cmds.parent(right_foot_ik_ctrl_grp, direction_ctrl)


    ################# Left Arm #################
    # Left Clavicle FK
    left_clavicle_ctrl = cmds.curve(name=gt_ab_joints.get('left_clavicle_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.0, 0.0, 0.0], [0.897, 1.554, 0.0], [0.959, 1.528, 0.0], [1.025, 1.52, 0.0], [1.091, 1.528, 0.0], [1.153, 1.554, 0.0], [1.206, 1.595, 0.0], [1.247, 1.647, 0.0], [1.025, 1.776, 0.0], [0.897, 1.554, 0.0], [0.844, 1.595, 0.0], [0.803, 1.648, 0.0], [0.778, 1.709, 0.0], [0.769, 1.776, 0.0], [0.778, 1.842, 0.0], [0.803, 1.904, 0.0], [0.844, 1.957, 0.0], [0.897, 1.997, 0.0], [0.959, 2.023, 0.0], [1.025, 2.032, 0.0], [1.091, 2.023, 0.0], [1.153, 1.998, 0.0], [1.206, 1.957, 0.0], [1.247, 1.904, 0.0], [1.273, 1.842, 0.0], [1.281, 1.776, 0.0], [1.272, 1.709, 0.0], [1.247, 1.647, 0.0], [0.803, 1.904, 0.0], [1.025, 1.776, 0.0], [1.153, 1.998, 0.0]],d=1)
    left_clavicle_ctrl_grp = cmds.group(name=left_clavicle_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    
    for shape in cmds.listRelatives(left_clavicle_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_clavicle_ctrl))
    
    # Left Clavicle Scale
    cmds.setAttr(left_clavicle_ctrl + '.scaleX', general_scale_offset*.25)
    cmds.setAttr(left_clavicle_ctrl + '.scaleY', general_scale_offset*.25)
    cmds.setAttr(left_clavicle_ctrl + '.scaleZ', general_scale_offset*.25)
    cmds.makeIdentity(left_clavicle_ctrl, apply=True, scale=True)
    
    # Left Clavicle Position
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_clavicle_jnt'), left_clavicle_ctrl_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_clavicle_jnt'), left_clavicle_ctrl))
    cmds.parent(left_clavicle_ctrl, left_clavicle_ctrl_grp)
    cmds.makeIdentity(left_clavicle_ctrl, apply=True, rotate=True)
    
    # Left Clavicle General Adjustments
    change_viewport_color(left_clavicle_ctrl, left_ctrl_color)
    cmds.parent(left_clavicle_ctrl_grp, spine04_ctrl)

    # Left Shoulder FK
    left_shoulder_ctrl = cmds.curve(name=gt_ab_joints.get('left_shoulder_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_shoulder_ctrl_grp = cmds.group(name=left_shoulder_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_shoulder_ctrl, left_shoulder_ctrl_grp)
    
    for shape in cmds.listRelatives(left_shoulder_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_shoulder_ctrl))
    
    left_shoulder_scale_offset = cmds.xform(gt_ab_joints.get('left_shoulder_jnt'), q=True, t=True)[0]*6.5
    
    cmds.setAttr(left_shoulder_ctrl + '.scaleX', left_shoulder_scale_offset)
    cmds.setAttr(left_shoulder_ctrl + '.scaleY', left_shoulder_scale_offset)
    cmds.setAttr(left_shoulder_ctrl + '.scaleZ', left_shoulder_scale_offset)
    cmds.makeIdentity(left_shoulder_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_shoulder_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_shoulder_jnt'), left_shoulder_ctrl_grp))
    change_viewport_color(left_shoulder_ctrl, left_ctrl_color)
    cmds.parent(left_shoulder_ctrl_grp, left_clavicle_ctrl)
    
    # Left Elbow FK
    left_elbow_ctrl = cmds.curve(name=gt_ab_joints.get('left_elbow_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_elbow_ctrl_grp = cmds.group(name=left_elbow_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_elbow_ctrl, left_elbow_ctrl_grp)
    
    for shape in cmds.listRelatives(left_elbow_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_elbow_ctrl))
    
    left_arm_scale_offset = cmds.xform(gt_ab_joints.get('left_elbow_jnt'), q=True, t=True)[0]
    left_arm_scale_offset += cmds.xform(gt_ab_joints.get('left_wrist_jnt'), q=True, t=True)[0]
    left_arm_scale_offset = left_arm_scale_offset*1.35
    
    cmds.setAttr(left_elbow_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_elbow_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_elbow_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_elbow_jnt'), left_elbow_ctrl_grp))
    change_viewport_color(left_elbow_ctrl, left_ctrl_color)
    cmds.parent(left_elbow_ctrl_grp, left_shoulder_ctrl)
    
    # Left Wrist FK
    left_wrist_ctrl = cmds.curve(name=gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    left_wrist_ctrl_grp = cmds.group(name=left_wrist_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_wrist_ctrl, left_wrist_ctrl_grp)
    
    for shape in cmds.listRelatives(left_wrist_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_wrist_ctrl))
    
    left_arm_scale_offset = left_arm_scale_offset*.9
    
    cmds.setAttr(left_wrist_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_wrist_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_wrist_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_wrist_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_wrist_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_wrist_jnt'), left_wrist_ctrl_grp))
    change_viewport_color(left_wrist_ctrl, left_ctrl_color)
    cmds.parent(left_wrist_ctrl_grp, left_elbow_ctrl)
    
    ################# Left Fingers FK #################
    # Left Fingers Parent
    left_hand_grp = cmds.group(name='left_hand_' + grp_suffix, empty=True, world=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_wrist_jnt'), left_hand_grp))
    cmds.parent(left_hand_grp, direction_ctrl)
    
    # Left Index Finger
    index_scale_offset = cmds.xform(gt_ab_joints.get('left_index02_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(gt_ab_joints.get('left_index03_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(gt_ab_joints.get('left_index04_jnt'), q=True, t=True)[0]
    index_scale_offset = index_scale_offset/3
    
    left_index01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_index01_jnt'),index_scale_offset)
    left_index02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_index02_jnt'),index_scale_offset)
    left_index03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_index03_jnt'),index_scale_offset)

    cmds.parent(left_index01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_index02_ctrl_list[1], left_index01_ctrl_list[0])
    cmds.parent(left_index03_ctrl_list[1], left_index02_ctrl_list[0])
    
    # Left Middle Finger
    middle_scale_offset = cmds.xform(gt_ab_joints.get('left_middle02_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(gt_ab_joints.get('left_middle03_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(gt_ab_joints.get('left_middle04_jnt'), q=True, t=True)[0]
    middle_scale_offset = middle_scale_offset/3
    
    left_middle01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_middle01_jnt'),middle_scale_offset)
    left_middle02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_middle02_jnt'),middle_scale_offset)
    left_middle03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_middle03_jnt'),middle_scale_offset)

    cmds.parent(left_middle01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_middle02_ctrl_list[1], left_middle01_ctrl_list[0])
    cmds.parent(left_middle03_ctrl_list[1], left_middle02_ctrl_list[0])
    
    # Left Ring Finger
    ring_scale_offset = cmds.xform(gt_ab_joints.get('left_ring02_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(gt_ab_joints.get('left_ring03_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(gt_ab_joints.get('left_ring04_jnt'), q=True, t=True)[0]
    ring_scale_offset = ring_scale_offset/3
    
    left_ring01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_ring01_jnt'),ring_scale_offset)
    left_ring02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_ring02_jnt'),ring_scale_offset)
    left_ring03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_ring03_jnt'),ring_scale_offset)

    cmds.parent(left_ring01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_ring02_ctrl_list[1], left_ring01_ctrl_list[0])
    cmds.parent(left_ring03_ctrl_list[1], left_ring02_ctrl_list[0])
    
    # Left Pinky Finger
    pinky_scale_offset = cmds.xform(gt_ab_joints.get('left_pinky02_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(gt_ab_joints.get('left_pinky03_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(gt_ab_joints.get('left_pinky04_jnt'), q=True, t=True)[0]
    pinky_scale_offset = pinky_scale_offset/3
    
    left_pinky01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_pinky01_jnt'),pinky_scale_offset)
    left_pinky02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_pinky02_jnt'),pinky_scale_offset)
    left_pinky03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_pinky03_jnt'),pinky_scale_offset)

    cmds.parent(left_pinky01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_pinky02_ctrl_list[1], left_pinky01_ctrl_list[0])
    cmds.parent(left_pinky03_ctrl_list[1], left_pinky02_ctrl_list[0])
    
    # Left Thumb Finger
    thumb_scale_offset = cmds.xform(gt_ab_joints.get('left_thumb02_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(gt_ab_joints.get('left_thumb03_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(gt_ab_joints.get('left_thumb04_jnt'), q=True, t=True)[0]
    thumb_scale_offset = thumb_scale_offset/3
    
    left_thumb01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_thumb01_jnt'),thumb_scale_offset)
    left_thumb02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_thumb02_jnt'),thumb_scale_offset)
    left_thumb03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('left_thumb03_jnt'),thumb_scale_offset)

    cmds.parent(left_thumb01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_thumb02_ctrl_list[1], left_thumb01_ctrl_list[0])
    cmds.parent(left_thumb03_ctrl_list[1], left_thumb02_ctrl_list[0])
    
    # Left Wrist IK
    left_wrist_ik_ctrl_a = cmds.curve(name=gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[0.267, -1.0, 0.0], [0.158, -1.0, 0.0], [0.158, -0.906, 0.0], [0.158, -0.524, 0.0], [0.158, 0.0, 0.0], [0.158, 0.523, -0.0], [0.158, 0.906, -0.0], [0.158, 1.0, -0.0], [0.267, 1.0, -0.0], [1.665, 1.0, -0.0], [2.409, 0.0, 0.0], [1.665, -1.0, 0.0]],d=3)
    left_wrist_ik_ctrl_b = cmds.curve(name=left_wrist_ik_ctrl_a + 'b', p=[[0.0, 0.0, 0.0], [0.157, 0.0, 0.0], [0.157, 0.743, 0.0], [0.19, 0.747, 0.0], [0.221, 0.76, 0.0], [0.248, 0.781, 0.0], [0.268, 0.807, 0.0], [0.281, 0.838, 0.0], [0.285, 0.871, 0.0], [0.157, 0.871, 0.0], [0.157, 0.743, 0.0], [0.124, 0.747, 0.0], [0.093, 0.76, 0.0], [0.066, 0.781, 0.0], [0.046, 0.807, 0.0], [0.033, 0.838, 0.0], [0.029, 0.871, 0.0], [0.033, 0.904, 0.0], [0.046, 0.935, 0.0], [0.066, 0.962, 0.0], [0.093, 0.982, 0.0], [0.124, 0.995, 0.0], [0.157, 0.999, 0.0], [0.19, 0.995, 0.0], [0.221, 0.982, 0.0], [0.248, 0.962, 0.0], [0.268, 0.935, 0.0], [0.281, 0.904, 0.0], [0.285, 0.871, 0.0], [0.029, 0.871, 0.0], [0.157, 0.871, 0.0], [0.157, 0.999, 0.0]],d=1)
    left_wrist_ik_ctrl = gtu_combine_curves_list([left_wrist_ik_ctrl_a, left_wrist_ik_ctrl_b])
    
    shapes = cmds.listRelatives(left_wrist_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, 'semiCircle')))
    cmds.rename(shapes[1], "{0}Shape".format(gt_ab_joints.get('left_wrist_jnt').replace(jnt_suffix, 'pin')))
    
    left_wrist_ik_ctrl_grp = cmds.group(name=left_wrist_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_wrist_ik_ctrl, left_wrist_ik_ctrl_grp)
    
    left_wrist_scale_offset = cmds.xform(gt_ab_joints.get('left_middle01_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(gt_ab_joints.get('left_middle02_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(gt_ab_joints.get('left_middle03_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(gt_ab_joints.get('left_middle04_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset = left_wrist_scale_offset/2
    
    cmds.setAttr(left_wrist_ik_ctrl + '.scaleX', left_wrist_scale_offset)
    cmds.setAttr(left_wrist_ik_ctrl + '.scaleY', left_wrist_scale_offset)
    cmds.setAttr(left_wrist_ik_ctrl + '.scaleZ', left_wrist_scale_offset)
    cmds.makeIdentity(left_wrist_ik_ctrl, apply=True, scale=True)
    cmds.closeCurve(left_wrist_ik_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_wrist_jnt'), left_wrist_ik_ctrl_grp))
    change_viewport_color(left_wrist_ik_ctrl, left_ctrl_color)
    cmds.parent(left_wrist_ik_ctrl_grp, direction_ctrl)
    
    # Left Elbow IK Pole Vector Ctrl
    left_elbow_ik_ctrl = cmds.curve(name=gt_ab_joints.get('left_elbow_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125], [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]],d=1)
    left_elbow_ik_ctrl_grp = cmds.group(name=left_elbow_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_elbow_ik_ctrl, left_elbow_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(left_elbow_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_elbow_ik_ctrl))
    
    # Left Knee Find Position
    left_arm_scale_offset = left_arm_scale_offset*.5
    temp_transform = cmds.group(name=left_elbow_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('left_elbow_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(gt_ab_settings.get('left_elbow_pv_dir'), temp_transform, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,-1,0), worldUpType="vector", worldUpVector=(0,1,0)))
    cmds.move(left_arm_scale_offset ,0 , 0, temp_transform, os=True, relative=True)    
    cmds.delete(cmds.pointConstraint(temp_transform, left_elbow_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Left Knee Pole Vec Visibility and Parenting
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_elbow_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_elbow_ik_ctrl, left_ctrl_color)
    cmds.parent(left_elbow_ik_ctrl_grp, direction_ctrl)
    
    ################# Right Arm #################
    # Right Clavicle FK
    right_clavicle_ctrl = cmds.curve(name=gt_ab_joints.get('right_clavicle_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[0.0, 0.0, 0.0], [0.897, 1.554, 0.0], [0.959, 1.528, 0.0], [1.025, 1.52, 0.0], [1.091, 1.528, 0.0], [1.153, 1.554, 0.0], [1.206, 1.595, 0.0], [1.247, 1.647, 0.0], [1.025, 1.776, 0.0], [0.897, 1.554, 0.0], [0.844, 1.595, 0.0], [0.803, 1.648, 0.0], [0.778, 1.709, 0.0], [0.769, 1.776, 0.0], [0.778, 1.842, 0.0], [0.803, 1.904, 0.0], [0.844, 1.957, 0.0], [0.897, 1.997, 0.0], [0.959, 2.023, 0.0], [1.025, 2.032, 0.0], [1.091, 2.023, 0.0], [1.153, 1.998, 0.0], [1.206, 1.957, 0.0], [1.247, 1.904, 0.0], [1.273, 1.842, 0.0], [1.281, 1.776, 0.0], [1.272, 1.709, 0.0], [1.247, 1.647, 0.0], [0.803, 1.904, 0.0], [1.025, 1.776, 0.0], [1.153, 1.998, 0.0]],d=1)
    right_clavicle_ctrl_grp = cmds.group(name=right_clavicle_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    
    for shape in cmds.listRelatives(right_clavicle_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_clavicle_ctrl))
    
    # Right Clavicle Scale
    cmds.setAttr(right_clavicle_ctrl + '.scaleX', (general_scale_offset*.25)*-1)
    cmds.setAttr(right_clavicle_ctrl + '.scaleY', general_scale_offset*.25)
    cmds.setAttr(right_clavicle_ctrl + '.scaleZ', general_scale_offset*.25)
    cmds.makeIdentity(right_clavicle_ctrl, apply=True, scale=True)
    
    # Right Clavicle Position
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_clavicle_jnt'), right_clavicle_ctrl_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_clavicle_jnt'), right_clavicle_ctrl))
    cmds.parent(right_clavicle_ctrl, right_clavicle_ctrl_grp)
    cmds.makeIdentity(right_clavicle_ctrl, apply=True, rotate=True)
    
    # Right Clavicle General Adjustments
    change_viewport_color(right_clavicle_ctrl, right_ctrl_color)
    cmds.parent(right_clavicle_ctrl_grp, spine04_ctrl)

    # Right Shoulder FK
    right_shoulder_ctrl = cmds.curve(name=gt_ab_joints.get('right_shoulder_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_shoulder_ctrl_grp = cmds.group(name=right_shoulder_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_shoulder_ctrl, right_shoulder_ctrl_grp)
    
    for shape in cmds.listRelatives(right_shoulder_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_shoulder_ctrl))
    
    right_shoulder_scale_offset = cmds.xform(gt_ab_joints.get('right_shoulder_jnt'), q=True, t=True)[0]*6.5
    
    cmds.setAttr(right_shoulder_ctrl + '.scaleX', right_shoulder_scale_offset)
    cmds.setAttr(right_shoulder_ctrl + '.scaleY', right_shoulder_scale_offset)
    cmds.setAttr(right_shoulder_ctrl + '.scaleZ', right_shoulder_scale_offset)
    cmds.makeIdentity(right_shoulder_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_shoulder_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_shoulder_jnt'), right_shoulder_ctrl_grp))
    change_viewport_color(right_shoulder_ctrl, right_ctrl_color)
    cmds.parent(right_shoulder_ctrl_grp, right_clavicle_ctrl)
    
    # Right Elbow FK
    right_elbow_ctrl = cmds.curve(name=gt_ab_joints.get('right_elbow_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_elbow_ctrl_grp = cmds.group(name=right_elbow_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_elbow_ctrl, right_elbow_ctrl_grp)
    
    for shape in cmds.listRelatives(right_elbow_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_elbow_ctrl))
    
    right_arm_scale_offset = cmds.xform(gt_ab_joints.get('right_elbow_jnt'), q=True, t=True)[0]
    right_arm_scale_offset += cmds.xform(gt_ab_joints.get('right_wrist_jnt'), q=True, t=True)[0]
    right_arm_scale_offset = right_arm_scale_offset*1.35
    
    cmds.setAttr(right_elbow_ctrl + '.scaleX', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_elbow_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_elbow_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_elbow_jnt'), right_elbow_ctrl_grp))
    change_viewport_color(right_elbow_ctrl, right_ctrl_color)
    cmds.parent(right_elbow_ctrl_grp, right_shoulder_ctrl)
    
    # Right Wrist FK
    right_wrist_ctrl = cmds.curve(name=gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, '') + ctrl_suffix, p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0]],d=3)
    right_wrist_ctrl_grp = cmds.group(name=right_wrist_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_wrist_ctrl, right_wrist_ctrl_grp)
    
    for shape in cmds.listRelatives(right_wrist_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_wrist_ctrl))
    
    right_arm_scale_offset = right_arm_scale_offset*.9
    
    cmds.setAttr(right_wrist_ctrl + '.scaleX', right_arm_scale_offset)
    cmds.setAttr(right_wrist_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_wrist_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_wrist_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_wrist_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_wrist_jnt'), right_wrist_ctrl_grp))
    change_viewport_color(right_wrist_ctrl, right_ctrl_color)
    cmds.parent(right_wrist_ctrl_grp, right_elbow_ctrl)
    
    ################# Right Fingers FK #################
    # Right Fingers Parent
    right_hand_grp = cmds.group(name='right_hand_' + grp_suffix, empty=True, world=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_wrist_jnt'), right_hand_grp))
    cmds.parent(right_hand_grp, direction_ctrl)
    
    # Right Index Finger
    index_scale_offset = cmds.xform(gt_ab_joints.get('right_index02_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(gt_ab_joints.get('right_index03_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(gt_ab_joints.get('right_index04_jnt'), q=True, t=True)[0]
    index_scale_offset = index_scale_offset/3
    
    right_index01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_index01_jnt'),index_scale_offset)
    right_index02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_index02_jnt'),index_scale_offset)
    right_index03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_index03_jnt'),index_scale_offset)

    cmds.parent(right_index01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_index02_ctrl_list[1], right_index01_ctrl_list[0])
    cmds.parent(right_index03_ctrl_list[1], right_index02_ctrl_list[0])
    
    # Right Middle Finger
    middle_scale_offset = cmds.xform(gt_ab_joints.get('right_middle02_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(gt_ab_joints.get('right_middle03_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(gt_ab_joints.get('right_middle04_jnt'), q=True, t=True)[0]
    middle_scale_offset = middle_scale_offset/3
    
    right_middle01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_middle01_jnt'),middle_scale_offset)
    right_middle02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_middle02_jnt'),middle_scale_offset)
    right_middle03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_middle03_jnt'),middle_scale_offset)

    cmds.parent(right_middle01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_middle02_ctrl_list[1], right_middle01_ctrl_list[0])
    cmds.parent(right_middle03_ctrl_list[1], right_middle02_ctrl_list[0])
    
    # Right Ring Finger
    ring_scale_offset = cmds.xform(gt_ab_joints.get('right_ring02_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(gt_ab_joints.get('right_ring03_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(gt_ab_joints.get('right_ring04_jnt'), q=True, t=True)[0]
    ring_scale_offset = ring_scale_offset/3
    
    right_ring01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_ring01_jnt'),ring_scale_offset)
    right_ring02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_ring02_jnt'),ring_scale_offset)
    right_ring03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_ring03_jnt'),ring_scale_offset)

    cmds.parent(right_ring01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_ring02_ctrl_list[1], right_ring01_ctrl_list[0])
    cmds.parent(right_ring03_ctrl_list[1], right_ring02_ctrl_list[0])
    
    # Right Pinky Finger
    pinky_scale_offset = cmds.xform(gt_ab_joints.get('right_pinky02_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(gt_ab_joints.get('right_pinky03_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(gt_ab_joints.get('right_pinky04_jnt'), q=True, t=True)[0]
    pinky_scale_offset = pinky_scale_offset/3
    
    right_pinky01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_pinky01_jnt'),pinky_scale_offset)
    right_pinky02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_pinky02_jnt'),pinky_scale_offset)
    right_pinky03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_pinky03_jnt'),pinky_scale_offset)

    cmds.parent(right_pinky01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_pinky02_ctrl_list[1], right_pinky01_ctrl_list[0])
    cmds.parent(right_pinky03_ctrl_list[1], right_pinky02_ctrl_list[0])
    
    # Right Thumb Finger
    thumb_scale_offset = cmds.xform(gt_ab_joints.get('right_thumb02_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(gt_ab_joints.get('right_thumb03_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(gt_ab_joints.get('right_thumb04_jnt'), q=True, t=True)[0]
    thumb_scale_offset = thumb_scale_offset/3
    
    right_thumb01_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_thumb01_jnt'),thumb_scale_offset)
    right_thumb02_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_thumb02_jnt'),thumb_scale_offset)
    right_thumb03_ctrl_list = create_simple_fk_control(gt_ab_joints.get('right_thumb03_jnt'),thumb_scale_offset)

    cmds.parent(right_thumb01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_thumb02_ctrl_list[1], right_thumb01_ctrl_list[0])
    cmds.parent(right_thumb03_ctrl_list[1], right_thumb02_ctrl_list[0])
    
    # Right Wrist IK
    right_wrist_ik_ctrl_a = cmds.curve(name=gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[0.267, -1.0, 0.0], [0.158, -1.0, 0.0], [0.158, -0.906, 0.0], [0.158, -0.524, 0.0], [0.158, 0.0, 0.0], [0.158, 0.523, -0.0], [0.158, 0.906, -0.0], [0.158, 1.0, -0.0], [0.267, 1.0, -0.0], [1.665, 1.0, -0.0], [2.409, 0.0, 0.0], [1.665, -1.0, 0.0]],d=3)
    right_wrist_ik_ctrl_b = cmds.curve(name=right_wrist_ik_ctrl_a + 'b', p=[[0.0, 0.0, 0.0], [0.157, 0.0, 0.0], [0.157, 0.743, 0.0], [0.19, 0.747, 0.0], [0.221, 0.76, 0.0], [0.248, 0.781, 0.0], [0.268, 0.807, 0.0], [0.281, 0.838, 0.0], [0.285, 0.871, 0.0], [0.157, 0.871, 0.0], [0.157, 0.743, 0.0], [0.124, 0.747, 0.0], [0.093, 0.76, 0.0], [0.066, 0.781, 0.0], [0.046, 0.807, 0.0], [0.033, 0.838, 0.0], [0.029, 0.871, 0.0], [0.033, 0.904, 0.0], [0.046, 0.935, 0.0], [0.066, 0.962, 0.0], [0.093, 0.982, 0.0], [0.124, 0.995, 0.0], [0.157, 0.999, 0.0], [0.19, 0.995, 0.0], [0.221, 0.982, 0.0], [0.248, 0.962, 0.0], [0.268, 0.935, 0.0], [0.281, 0.904, 0.0], [0.285, 0.871, 0.0], [0.029, 0.871, 0.0], [0.157, 0.871, 0.0], [0.157, 0.999, 0.0]],d=1)
    right_wrist_ik_ctrl = gtu_combine_curves_list([right_wrist_ik_ctrl_a, right_wrist_ik_ctrl_b])
    
    shapes = cmds.listRelatives(right_wrist_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, 'semiCircle')))
    cmds.rename(shapes[1], "{0}Shape".format(gt_ab_joints.get('right_wrist_jnt').replace(jnt_suffix, 'pin')))
    
    right_wrist_ik_ctrl_grp = cmds.group(name=right_wrist_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_wrist_ik_ctrl, right_wrist_ik_ctrl_grp)
    
    right_wrist_scale_offset = abs(cmds.xform(gt_ab_joints.get('right_middle01_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(gt_ab_joints.get('right_middle02_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(gt_ab_joints.get('right_middle03_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(gt_ab_joints.get('right_middle04_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset = right_wrist_scale_offset/2
    
    cmds.setAttr(right_wrist_ik_ctrl + '.scaleX', right_wrist_scale_offset*-1)
    cmds.setAttr(right_wrist_ik_ctrl + '.scaleY', right_wrist_scale_offset*-1)
    cmds.setAttr(right_wrist_ik_ctrl + '.scaleZ', right_wrist_scale_offset*-1)
    cmds.makeIdentity(right_wrist_ik_ctrl, apply=True, scale=True)
    cmds.closeCurve(right_wrist_ik_ctrl, ch=False, ps=False, rpo=True)
    
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_wrist_jnt'), right_wrist_ik_ctrl_grp))
    change_viewport_color(right_wrist_ik_ctrl, right_ctrl_color)
    cmds.parent(right_wrist_ik_ctrl_grp, direction_ctrl)
    
    # Right Elbow IK Pole Vector Ctrl
    right_elbow_ik_ctrl = cmds.curve(name=gt_ab_joints.get('right_elbow_jnt').replace(jnt_suffix, 'ik_') + ctrl_suffix, p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125], [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]],d=1)
    right_elbow_ik_ctrl_grp = cmds.group(name=right_elbow_ik_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_elbow_ik_ctrl, right_elbow_ik_ctrl_grp)
    
    for shape in cmds.listRelatives(right_elbow_ik_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_elbow_ik_ctrl))
    
    # Right Elbow Find Position
    right_arm_scale_offset = abs(right_arm_scale_offset)*.5
    temp_transform = cmds.group(name=right_elbow_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('right_elbow_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(gt_ab_settings.get('right_elbow_pv_dir'), temp_transform, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,1,0), worldUpType="vector", worldUpVector=(0,1,0)))
    cmds.move(right_arm_scale_offset ,0 , 0, temp_transform, os=True, relative=True)    
    cmds.delete(cmds.pointConstraint(temp_transform, right_elbow_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Right Elbow Pole Vec Visibility and Parenting
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleX', right_arm_scale_offset*1)
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_elbow_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_elbow_ik_ctrl, right_ctrl_color)
    cmds.parent(right_elbow_ik_ctrl_grp, direction_ctrl)
    
    
    # IK/FK Switches
    # Left Arm
    left_arm_switch = cmds.curve(name='left_arm_switch_' + ctrl_suffix, p=[[0.273, 0.0, -1.87], [0.273, -0.465, -2.568], [0.273, -0.233, -2.568], [0.273, -0.233, -3.295], [0.273, 0.233, -3.295], [0.273, 0.233, -2.568], [0.273, 0.465, -2.568], [0.273, 0.0, -1.87], [0.273, 0.0, -1.87], [0.738, 0.0, -2.568], [0.506, 0.0, -2.568], [0.506, 0.0, -3.295], [0.04, 0.0, -3.295], [0.04, 0.0, -2.568], [-0.192, 0.0, -2.568], [0.273, 0.0, -1.87]],d=1)
    left_arm_switch_a = cmds.curve(name='left_arm_fk_a_' + ctrl_suffix, p=[[0.092, 0.0, -3.811], [0.092, 0.0, -3.591], [0.226, 0.0, -3.591], [0.226, 0.0, -3.802], [0.282, 0.0, -3.802], [0.282, 0.0, -3.591], [0.51, 0.0, -3.591], [0.51, 0.0, -3.528], [0.036, 0.0, -3.528], [0.036, 0.0, -3.811]],d=1)
    left_arm_switch_b = cmds.curve(name='left_arm_fk_b_' + ctrl_suffix, p=[[0.51, 0.0, -4.212], [0.51, 0.0, -4.131], [0.289, 0.0, -3.958], [0.321, 0.0, -3.93], [0.51, 0.0, -3.93], [0.51, 0.0, -3.867], [0.036, 0.0, -3.867], [0.036, 0.0, -3.93], [0.254, 0.0, -3.93], [0.036, 0.0, -4.124], [0.036, 0.0, -4.201], [0.248, 0.0, -4.005]],d=1)
    left_arm_switch_c = cmds.curve(name='left_arm_ik_c_' + ctrl_suffix, p=[[0.51, 0.0, -3.751], [0.51, 0.0, -3.567], [0.461, 0.0, -3.567], [0.461, 0.0, -3.627], [0.085, 0.0, -3.627], [0.085, 0.0, -3.567], [0.036, 0.0, -3.567], [0.036, 0.0, -3.751], [0.085, 0.0, -3.751], [0.085, 0.0, -3.69], [0.461, 0.0, -3.69], [0.461, 0.0, -3.751]],d=1)
    left_arm_switch_d = cmds.curve(name='left_arm_ik_d_' + ctrl_suffix, p=[[0.51, 0.0, -4.173], [0.51, 0.0, -4.091], [0.289, 0.0, -3.919], [0.321, 0.0, -3.891], [0.51, 0.0, -3.891], [0.51, 0.0, -3.828], [0.036, 0.0, -3.828], [0.036, 0.0, -3.891], [0.254, 0.0, -3.891], [0.036, 0.0, -4.085], [0.036, 0.0, -4.162], [0.248, 0.0, -3.966]],d=1)
    
    for crv in [left_arm_switch, left_arm_switch_a, left_arm_switch_b, left_arm_switch_c, left_arm_switch_d]:
        cmds.setAttr(crv + '.scaleX', left_arm_scale_offset/4)
        cmds.setAttr(crv + '.scaleY', left_arm_scale_offset/4)
        cmds.setAttr(crv + '.scaleZ', left_arm_scale_offset/4)
        cmds.makeIdentity(crv, apply=True, scale=True)
        cmds.closeCurve(crv, ch=False, ps=False, rpo=True)
    
    left_arm_switch = gtu_combine_curves_list([left_arm_switch, left_arm_switch_a, left_arm_switch_b, left_arm_switch_c, left_arm_switch_d])
    
    shapes = cmds.listRelatives(left_arm_switch, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('arrow'))
    cmds.rename(shapes[1], "{0}Shape".format('fk_f'))
    cmds.rename(shapes[2], "{0}Shape".format('fk_k'))
    cmds.rename(shapes[3], "{0}Shape".format('ik_i'))
    cmds.rename(shapes[4], "{0}Shape".format('ik_k'))
    
    left_arm_switch_grp = cmds.group(name=left_arm_switch + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_arm_switch, left_arm_switch_grp)
    
    change_viewport_color(left_arm_switch, left_ctrl_color)
    cmds.delete(cmds.parentConstraint(gt_ab_settings.get('left_wrist_proxy_crv'), left_arm_switch_grp))
    cmds.parent(left_arm_switch_grp, main_ctrl)
    
    # Right Arm
    right_arm_switch = cmds.curve(name='right_arm_switch_' + ctrl_suffix, p=[[0.273, 0.0, -1.87], [0.273, -0.465, -2.568], [0.273, -0.233, -2.568], [0.273, -0.233, -3.295], [0.273, 0.233, -3.295], [0.273, 0.233, -2.568], [0.273, 0.465, -2.568], [0.273, 0.0, -1.87], [0.273, 0.0, -1.87], [0.738, 0.0, -2.568], [0.506, 0.0, -2.568], [0.506, 0.0, -3.295], [0.04, 0.0, -3.295], [0.04, 0.0, -2.568], [-0.192, 0.0, -2.568], [0.273, 0.0, -1.87]],d=1)
    right_arm_switch_a = cmds.curve(name='right_arm_fk_a_' + ctrl_suffix, p=[[0.092, 0.0, -3.811], [0.092, 0.0, -3.591], [0.226, 0.0, -3.591], [0.226, 0.0, -3.802], [0.282, 0.0, -3.802], [0.282, 0.0, -3.591], [0.51, 0.0, -3.591], [0.51, 0.0, -3.528], [0.036, 0.0, -3.528], [0.036, 0.0, -3.811]],d=1)
    right_arm_switch_b = cmds.curve(name='right_arm_fk_b_' + ctrl_suffix, p=[[0.51, 0.0, -4.212], [0.51, 0.0, -4.131], [0.289, 0.0, -3.958], [0.321, 0.0, -3.93], [0.51, 0.0, -3.93], [0.51, 0.0, -3.867], [0.036, 0.0, -3.867], [0.036, 0.0, -3.93], [0.254, 0.0, -3.93], [0.036, 0.0, -4.124], [0.036, 0.0, -4.201], [0.248, 0.0, -4.005]],d=1)
    right_arm_switch_c = cmds.curve(name='right_arm_ik_c_' + ctrl_suffix, p=[[0.51, 0.0, -3.751], [0.51, 0.0, -3.567], [0.461, 0.0, -3.567], [0.461, 0.0, -3.627], [0.085, 0.0, -3.627], [0.085, 0.0, -3.567], [0.036, 0.0, -3.567], [0.036, 0.0, -3.751], [0.085, 0.0, -3.751], [0.085, 0.0, -3.69], [0.461, 0.0, -3.69], [0.461, 0.0, -3.751]],d=1)
    right_arm_switch_d = cmds.curve(name='right_arm_ik_d_' + ctrl_suffix, p=[[0.51, 0.0, -4.173], [0.51, 0.0, -4.091], [0.289, 0.0, -3.919], [0.321, 0.0, -3.891], [0.51, 0.0, -3.891], [0.51, 0.0, -3.828], [0.036, 0.0, -3.828], [0.036, 0.0, -3.891], [0.254, 0.0, -3.891], [0.036, 0.0, -4.085], [0.036, 0.0, -4.162], [0.248, 0.0, -3.966]],d=1)
    
    for crv in [right_arm_switch, right_arm_switch_a, right_arm_switch_b, right_arm_switch_c, right_arm_switch_d]:
        cmds.setAttr(crv + '.scaleX', -right_arm_scale_offset/4)
        cmds.setAttr(crv + '.scaleY', right_arm_scale_offset/4)
        cmds.setAttr(crv + '.scaleZ', right_arm_scale_offset/4)
        cmds.makeIdentity(crv, apply=True, scale=True)
        cmds.closeCurve(crv, ch=False, ps=False, rpo=True)
    
    right_arm_switch = gtu_combine_curves_list([right_arm_switch, right_arm_switch_a, right_arm_switch_b, right_arm_switch_c, right_arm_switch_d])
    
    shapes = cmds.listRelatives(right_arm_switch, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('arrow'))
    cmds.rename(shapes[1], "{0}Shape".format('fk_f'))
    cmds.rename(shapes[2], "{0}Shape".format('fk_k'))
    cmds.rename(shapes[3], "{0}Shape".format('ik_i'))
    cmds.rename(shapes[4], "{0}Shape".format('ik_k'))
    
    right_arm_switch_grp = cmds.group(name=right_arm_switch + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_arm_switch, right_arm_switch_grp)
    
    change_viewport_color(right_arm_switch, right_ctrl_color)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('right_wrist_proxy_crv'), right_arm_switch_grp))
    cmds.parent(right_arm_switch_grp, main_ctrl)
    
    
    # Left Leg
    left_leg_switch = cmds.curve(name='left_leg_switch_' + ctrl_suffix, p=[[-0.0, 0.0, -1.87], [-0.0, -0.465, -2.568], [-0.0, -0.233, -2.568], [-0.0, -0.233, -3.295], [-0.0, 0.233, -3.295], [-0.0, 0.233, -2.568], [-0.0, 0.465, -2.568], [-0.0, 0.0, -1.87], [-0.0, 0.0, -1.87], [0.465, 0.0, -2.568], [0.233, 0.0, -2.568], [0.233, 0.0, -3.295], [-0.233, 0.0, -3.295], [-0.233, 0.0, -2.568], [-0.465, 0.0, -2.568], [-0.0, 0.0, -1.87]],d=1)
    left_leg_switch_a = cmds.curve(name='left_leg_fk_a_' + ctrl_suffix, p=[[-0.181, 0.0, -3.811], [-0.181, 0.0, -3.591], [-0.047, 0.0, -3.591], [-0.047, 0.0, -3.802], [0.009, 0.0, -3.802], [0.009, 0.0, -3.591], [0.237, 0.0, -3.591], [0.237, 0.0, -3.528], [-0.237, 0.0, -3.528], [-0.237, 0.0, -3.811]],d=1)
    left_leg_switch_b = cmds.curve(name='left_leg_fk_b_' + ctrl_suffix, p=[[0.237, 0.0, -4.212], [0.237, 0.0, -4.131], [0.016, 0.0, -3.958], [0.048, 0.0, -3.93], [0.237, 0.0, -3.93], [0.237, 0.0, -3.867], [-0.237, 0.0, -3.867], [-0.237, 0.0, -3.93], [-0.019, 0.0, -3.93], [-0.237, 0.0, -4.124], [-0.237, 0.0, -4.201], [-0.025, 0.0, -4.005]],d=1)
    left_leg_switch_c = cmds.curve(name='left_leg_ik_c_' + ctrl_suffix, p=[[0.237, 0.0, -3.751], [0.237, 0.0, -3.567], [0.188, 0.0, -3.567], [0.188, 0.0, -3.627], [-0.188, 0.0, -3.627], [-0.188, 0.0, -3.567], [-0.237, 0.0, -3.567], [-0.237, 0.0, -3.751], [-0.188, 0.0, -3.751], [-0.188, 0.0, -3.69], [0.188, 0.0, -3.69], [0.188, 0.0, -3.751]],d=1)
    left_leg_switch_d = cmds.curve(name='left_leg_ik_d_' + ctrl_suffix, p=[[0.237, 0.0, -4.173], [0.237, 0.0, -4.091], [0.016, 0.0, -3.919], [0.048, 0.0, -3.891], [0.237, 0.0, -3.891], [0.237, 0.0, -3.828], [-0.237, 0.0, -3.828], [-0.237, 0.0, -3.891], [-0.019, 0.0, -3.891], [-0.237, 0.0, -4.085], [-0.237, 0.0, -4.162], [-0.025, 0.0, -3.966]],d=1)
    
    for crv in [left_leg_switch, left_leg_switch_a, left_leg_switch_b, left_leg_switch_c, left_leg_switch_d]:
        cmds.setAttr(crv + '.scaleX', left_foot_scale_offset/6.5)
        cmds.setAttr(crv + '.scaleY', left_foot_scale_offset/6.5)
        cmds.setAttr(crv + '.scaleZ', left_foot_scale_offset/6.5)
        cmds.makeIdentity(crv, apply=True, scale=True)
        cmds.closeCurve(crv, ch=False, ps=False, rpo=True)
    
    left_leg_switch = gtu_combine_curves_list([left_leg_switch, left_leg_switch_a, left_leg_switch_b, left_leg_switch_c, left_leg_switch_d])
    
    shapes = cmds.listRelatives(left_leg_switch, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('arrow'))
    cmds.rename(shapes[1], "{0}Shape".format('fk_f'))
    cmds.rename(shapes[2], "{0}Shape".format('fk_k'))
    cmds.rename(shapes[3], "{0}Shape".format('ik_i'))
    cmds.rename(shapes[4], "{0}Shape".format('ik_k'))
    
    left_leg_switch_grp = cmds.group(name=left_leg_switch + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_leg_switch, left_leg_switch_grp)

    change_viewport_color(left_leg_switch, left_ctrl_color)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('left_ankle_proxy_crv'), left_leg_switch_grp))
    
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_leg_switch_grp + '.ry', desired_rotation[1])
    
    cmds.parent(left_leg_switch_grp, main_ctrl)
    
    # Right Leg
    right_leg_switch = cmds.curve(name='right_leg_switch_' + ctrl_suffix, p=[[-0.0, 0.0, -1.87], [-0.0, -0.465, -2.568], [-0.0, -0.233, -2.568], [-0.0, -0.233, -3.295], [-0.0, 0.233, -3.295], [-0.0, 0.233, -2.568], [-0.0, 0.465, -2.568], [-0.0, 0.0, -1.87], [-0.0, 0.0, -1.87], [0.465, 0.0, -2.568], [0.233, 0.0, -2.568], [0.233, 0.0, -3.295], [-0.233, 0.0, -3.295], [-0.233, 0.0, -2.568], [-0.465, 0.0, -2.568], [-0.0, 0.0, -1.87]],d=1)
    right_leg_switch_a = cmds.curve(name='right_leg_fk_a_' + ctrl_suffix, p=[[-0.181, 0.0, -3.811], [-0.181, 0.0, -3.591], [-0.047, 0.0, -3.591], [-0.047, 0.0, -3.802], [0.009, 0.0, -3.802], [0.009, 0.0, -3.591], [0.237, 0.0, -3.591], [0.237, 0.0, -3.528], [-0.237, 0.0, -3.528], [-0.237, 0.0, -3.811]],d=1)
    right_leg_switch_b = cmds.curve(name='right_leg_fk_b_' + ctrl_suffix, p=[[0.237, 0.0, -4.212], [0.237, 0.0, -4.131], [0.016, 0.0, -3.958], [0.048, 0.0, -3.93], [0.237, 0.0, -3.93], [0.237, 0.0, -3.867], [-0.237, 0.0, -3.867], [-0.237, 0.0, -3.93], [-0.019, 0.0, -3.93], [-0.237, 0.0, -4.124], [-0.237, 0.0, -4.201], [-0.025, 0.0, -4.005]],d=1)
    right_leg_switch_c = cmds.curve(name='right_leg_ik_c_' + ctrl_suffix, p=[[0.237, 0.0, -3.751], [0.237, 0.0, -3.567], [0.188, 0.0, -3.567], [0.188, 0.0, -3.627], [-0.188, 0.0, -3.627], [-0.188, 0.0, -3.567], [-0.237, 0.0, -3.567], [-0.237, 0.0, -3.751], [-0.188, 0.0, -3.751], [-0.188, 0.0, -3.69], [0.188, 0.0, -3.69], [0.188, 0.0, -3.751]],d=1)
    right_leg_switch_d = cmds.curve(name='right_leg_ik_d_' + ctrl_suffix, p=[[0.237, 0.0, -4.173], [0.237, 0.0, -4.091], [0.016, 0.0, -3.919], [0.048, 0.0, -3.891], [0.237, 0.0, -3.891], [0.237, 0.0, -3.828], [-0.237, 0.0, -3.828], [-0.237, 0.0, -3.891], [-0.019, 0.0, -3.891], [-0.237, 0.0, -4.085], [-0.237, 0.0, -4.162], [-0.025, 0.0, -3.966]],d=1)
    
    for crv in [right_leg_switch, right_leg_switch_a, right_leg_switch_b, right_leg_switch_c, right_leg_switch_d]:
        cmds.setAttr(crv + '.scaleX', right_foot_scale_offset/6.5)
        cmds.setAttr(crv + '.scaleY', right_foot_scale_offset/6.5)
        cmds.setAttr(crv + '.scaleZ', -right_foot_scale_offset/6.5)
        cmds.makeIdentity(crv, apply=True, scale=True)
        cmds.closeCurve(crv, ch=False, ps=False, rpo=True)
    
    right_leg_switch = gtu_combine_curves_list([right_leg_switch, right_leg_switch_a, right_leg_switch_b, right_leg_switch_c, right_leg_switch_d])
    
    shapes = cmds.listRelatives(right_leg_switch, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('arrow'))
    cmds.rename(shapes[1], "{0}Shape".format('fk_f'))
    cmds.rename(shapes[2], "{0}Shape".format('fk_k'))
    cmds.rename(shapes[3], "{0}Shape".format('ik_i'))
    cmds.rename(shapes[4], "{0}Shape".format('ik_k'))
    
    right_leg_switch_grp = cmds.group(name=right_leg_switch + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_leg_switch, right_leg_switch_grp)
    
    
    
    change_viewport_color(right_leg_switch, right_ctrl_color)
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('right_ankle_proxy_crv'), right_leg_switch_grp))
    cmds.parent(right_leg_switch_grp, main_ctrl)
    
    
    # Left Foot Automation Controls
    # Left Toe Roll
    left_toe_roll_ctrl_a = cmds.curve(name='left_toeRoll_' + ctrl_suffix, p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335], [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2], [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256], [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332], [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018], [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312], [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]],d=3)
    left_toe_roll_ctrl_b = cmds.curve(p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312], [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173], [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332], [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3], [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354], [-0.0, 0.095, 0.38]],d=3)
    left_toe_roll_ctrl = gtu_combine_curves_list([left_toe_roll_ctrl_a, left_toe_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(left_toe_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(left_toe_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(left_toe_roll_ctrl + second_shape_suffix))
    
    left_toe_roll_ctrl_grp = cmds.group(name=left_toe_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_toe_roll_ctrl, left_toe_roll_ctrl_grp)
    
    # Left Toe Roll Scale
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleX', left_foot_scale_offset/5)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleY', left_foot_scale_offset/5)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset/5)
    cmds.makeIdentity(left_toe_roll_ctrl_grp, apply=True, scale=True)
    
    # Left Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_toe_jnt'), left_toe_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset/4,left_toe_roll_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(left_toe_roll_ctrl, left_ctrl_color)
    cmds.parent(left_toe_roll_ctrl_grp, left_foot_ik_ctrl)
    
    
    # Left Toe Up/Down
    left_toe_up_down_ctrl = cmds.curve(name='left_toe_upDown_' + ctrl_suffix, p=[[0.0, 0.351, 0.0], [0.0, 0.21, -0.14], [0.0, 0.21, -0.037], [-0.0, -0.21, -0.037], [-0.0, -0.21, -0.14], [-0.0, -0.351, 0.0], [-0.0, -0.21, 0.14], [-0.0, -0.21, 0.037], [0.0, 0.21, 0.037], [0.0, 0.21, 0.14], [0.0, 0.351, 0.0]],d=1)
    
    for shape in cmds.listRelatives(left_toe_up_down_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(left_toe_up_down_ctrl))
    
    left_toe_up_down_ctrl_grp = cmds.group(name=left_toe_up_down_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_toe_up_down_ctrl, left_toe_up_down_ctrl_grp)
    
    # Left Toe Roll Scale
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleX', left_foot_scale_offset/5)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleY', left_foot_scale_offset/5)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleZ', left_foot_scale_offset/5)
    cmds.makeIdentity(left_toe_up_down_ctrl_grp, apply=True, scale=True)
    
    # Left Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_toe_jnt'), left_toe_up_down_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset/2.6,left_toe_up_down_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(left_toe_up_down_ctrl, left_ctrl_color)
    cmds.parent(left_toe_up_down_ctrl_grp, left_foot_ik_ctrl)
    
    # Left Ball Roll
    left_ball_roll_ctrl_a = cmds.curve(name='left_ballRoll_' + ctrl_suffix, p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335], [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2], [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256], [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332], [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018], [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312], [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]],d=3)
    left_ball_roll_ctrl_b = cmds.curve(p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312], [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173], [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332], [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3], [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354], [-0.0, 0.095, 0.38]],d=3)
    left_ball_roll_ctrl = gtu_combine_curves_list([left_ball_roll_ctrl_a, left_ball_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(left_ball_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(left_ball_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(left_ball_roll_ctrl + second_shape_suffix))
    
    left_ball_roll_ctrl_grp = cmds.group(name=left_ball_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_ball_roll_ctrl, left_ball_roll_ctrl_grp)
    
    # Left Ball Roll Scale
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleX', left_foot_scale_offset/6)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleY', left_foot_scale_offset/6)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset/6)
    cmds.makeIdentity(left_ball_roll_ctrl_grp, apply=True, scale=True)
    
    # Left Ball Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_ball_jnt'), left_ball_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset/3,left_ball_roll_ctrl_grp, x=True, relative=True, objectSpace=True)
    
    change_viewport_color(left_ball_roll_ctrl, left_ctrl_color)
    cmds.parent(left_ball_roll_ctrl_grp, left_foot_ik_ctrl)
    
    # Left Heel Roll
    left_heel_roll_ctrl_a = cmds.curve(name='left_heelRoll_' + ctrl_suffix, p=[[0.0, 0.095, -0.38], [0.035, 0.145, -0.354], [0.059, 0.177, -0.335], [0.092, 0.218, -0.312], [0.118, 0.248, -0.286], [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.096, 0.259, -0.275], [0.068, 0.232, -0.3], [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.339, -0.2], [0.046, 0.387, 0.018], [0.046, 0.332, 0.173], [0.046, 0.265, 0.256], [0.046, 0.167, 0.332], [0.046, -0.0, 0.38], [0.046, -0.167, 0.332], [0.046, -0.265, 0.256], [0.046, -0.332, 0.173], [0.046, -0.387, 0.018], [0.046, -0.339, -0.2], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32], [0.068, -0.232, -0.3], [0.096, -0.259, -0.275], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254], [0.118, -0.248, -0.286], [0.092, -0.218, -0.312], [0.059, -0.177, -0.335], [0.035, -0.145, -0.354], [0.0, -0.095, -0.38]],d=3)
    left_heel_roll_ctrl_b = cmds.curve(p=[[0.0, 0.095, -0.38], [-0.035, 0.145, -0.354], [-0.059, 0.177, -0.335], [-0.092, 0.218, -0.312], [-0.118, 0.248, -0.286], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.096, 0.259, -0.275], [-0.068, 0.232, -0.3], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32], [-0.046, 0.339, -0.2], [-0.046, 0.387, 0.018], [-0.046, 0.332, 0.173], [-0.046, 0.265, 0.256], [-0.046, 0.167, 0.332], [-0.046, -0.0, 0.38], [-0.046, -0.167, 0.332], [-0.046, -0.265, 0.256], [-0.046, -0.332, 0.173], [-0.046, -0.387, 0.018], [-0.046, -0.339, -0.2], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.068, -0.232, -0.3], [-0.096, -0.259, -0.275], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.118, -0.248, -0.286], [-0.092, -0.218, -0.312], [-0.059, -0.177, -0.335], [-0.035, -0.145, -0.354], [0.0, -0.095, -0.38]],d=3)
    left_heel_roll_ctrl = gtu_combine_curves_list([left_heel_roll_ctrl_a, left_heel_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(left_heel_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(left_heel_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(left_heel_roll_ctrl + second_shape_suffix))
    
    left_heel_roll_ctrl_grp = cmds.group(name=left_heel_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(left_heel_roll_ctrl, left_heel_roll_ctrl_grp)
    
    # Left Heel Roll Scale
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleX', left_foot_scale_offset/6)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleY', left_foot_scale_offset/6)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset/6)
    cmds.makeIdentity(left_heel_roll_ctrl_grp, apply=True, scale=True)
    
    # Left Heel Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_ankle_jnt'), left_heel_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset/3.5*-1,left_heel_roll_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(left_heel_roll_ctrl, left_ctrl_color)
    cmds.parent(left_heel_roll_ctrl_grp, left_foot_ik_ctrl)


    # Right Foot Automation Controls
    # Right Toe Roll
    right_toe_roll_ctrl_a = cmds.curve(name='right_toeRoll_' + ctrl_suffix, p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335], [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2], [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256], [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332], [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018], [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312], [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]],d=3)
    right_toe_roll_ctrl_b = cmds.curve(p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312], [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173], [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332], [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3], [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354], [-0.0, 0.095, 0.38]],d=3)
    right_toe_roll_ctrl = gtu_combine_curves_list([right_toe_roll_ctrl_a, right_toe_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(right_toe_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(right_toe_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(right_toe_roll_ctrl + second_shape_suffix))
    
    # Match Right Side Look
    cmds.setAttr(right_toe_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_toe_roll_ctrl, apply=True, rotate=True)
    
    right_toe_roll_ctrl_grp = cmds.group(name=right_toe_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_toe_roll_ctrl, right_toe_roll_ctrl_grp)
    
    # Right Toe Roll Scale
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleX', right_foot_scale_offset/5)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleY', right_foot_scale_offset/5)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset/5)
    cmds.makeIdentity(right_toe_roll_ctrl_grp, apply=True, scale=True)
    
    # Right Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_toe_jnt'), right_toe_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset/4,right_toe_roll_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(right_toe_roll_ctrl, right_ctrl_color)
    cmds.parent(right_toe_roll_ctrl_grp, right_foot_ik_ctrl)
    
    
    # Right Toe Up/Down
    right_toe_up_down_ctrl = cmds.curve(name='right_toe_upDown_' + ctrl_suffix, p=[[0.0, 0.351, 0.0], [0.0, 0.21, -0.14], [0.0, 0.21, -0.037], [-0.0, -0.21, -0.037], [-0.0, -0.21, -0.14], [-0.0, -0.351, 0.0], [-0.0, -0.21, 0.14], [-0.0, -0.21, 0.037], [0.0, 0.21, 0.037], [0.0, 0.21, 0.14], [0.0, 0.351, 0.0]],d=1)
    
    for shape in cmds.listRelatives(right_toe_up_down_ctrl, s=True, f=True) or []:
        shape = cmds.rename(shape, "{0}Shape".format(right_toe_up_down_ctrl))
    
    right_toe_up_down_ctrl_grp = cmds.group(name=right_toe_up_down_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_toe_up_down_ctrl, right_toe_up_down_ctrl_grp)
    
    # Right Toe Roll Scale
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleX', right_foot_scale_offset/5)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleY', right_foot_scale_offset/5)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleZ', right_foot_scale_offset/5)
    cmds.makeIdentity(right_toe_up_down_ctrl_grp, apply=True, scale=True)
    
    # Right Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_toe_jnt'), right_toe_up_down_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset/2.6,right_toe_up_down_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(right_toe_up_down_ctrl, right_ctrl_color)
    cmds.parent(right_toe_up_down_ctrl_grp, right_foot_ik_ctrl)
    
    # Right Ball Roll
    right_ball_roll_ctrl_a = cmds.curve(name='right_ballRoll_' + ctrl_suffix, p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335], [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2], [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256], [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332], [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018], [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312], [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]],d=3)
    right_ball_roll_ctrl_b = cmds.curve(p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312], [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173], [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332], [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3], [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354], [-0.0, 0.095, 0.38]],d=3)
    right_ball_roll_ctrl = gtu_combine_curves_list([right_ball_roll_ctrl_a, right_ball_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(right_ball_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(right_ball_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(right_ball_roll_ctrl + second_shape_suffix))
    
    # Match Right Side Look
    cmds.setAttr(right_ball_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_ball_roll_ctrl, apply=True, rotate=True)
    
    right_ball_roll_ctrl_grp = cmds.group(name=right_ball_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_ball_roll_ctrl, right_ball_roll_ctrl_grp)
    
    # Right Ball Roll Scale
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleX', right_foot_scale_offset/6)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleY', right_foot_scale_offset/6)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset/6)
    cmds.makeIdentity(right_ball_roll_ctrl_grp, apply=True, scale=True)
    
    # Right Ball Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_ball_jnt'), right_ball_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(right_foot_scale_offset/3,right_ball_roll_ctrl_grp, x=True, relative=True, objectSpace=True)
    
    change_viewport_color(right_ball_roll_ctrl, right_ctrl_color)
    cmds.parent(right_ball_roll_ctrl_grp, right_foot_ik_ctrl)
    
    # Right Heel Roll
    right_heel_roll_ctrl_a = cmds.curve(name='right_heelRoll_' + ctrl_suffix, p=[[0.0, 0.095, -0.38], [0.035, 0.145, -0.354], [0.059, 0.177, -0.335], [0.092, 0.218, -0.312], [0.118, 0.248, -0.286], [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.096, 0.259, -0.275], [0.068, 0.232, -0.3], [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.339, -0.2], [0.046, 0.387, 0.018], [0.046, 0.332, 0.173], [0.046, 0.265, 0.256], [0.046, 0.167, 0.332], [0.046, -0.0, 0.38], [0.046, -0.167, 0.332], [0.046, -0.265, 0.256], [0.046, -0.332, 0.173], [0.046, -0.387, 0.018], [0.046, -0.339, -0.2], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32], [0.068, -0.232, -0.3], [0.096, -0.259, -0.275], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254], [0.118, -0.248, -0.286], [0.092, -0.218, -0.312], [0.059, -0.177, -0.335], [0.035, -0.145, -0.354], [0.0, -0.095, -0.38]],d=3)
    right_heel_roll_ctrl_b = cmds.curve(p=[[0.0, 0.095, -0.38], [-0.035, 0.145, -0.354], [-0.059, 0.177, -0.335], [-0.092, 0.218, -0.312], [-0.118, 0.248, -0.286], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.096, 0.259, -0.275], [-0.068, 0.232, -0.3], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32], [-0.046, 0.339, -0.2], [-0.046, 0.387, 0.018], [-0.046, 0.332, 0.173], [-0.046, 0.265, 0.256], [-0.046, 0.167, 0.332], [-0.046, -0.0, 0.38], [-0.046, -0.167, 0.332], [-0.046, -0.265, 0.256], [-0.046, -0.332, 0.173], [-0.046, -0.387, 0.018], [-0.046, -0.339, -0.2], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.068, -0.232, -0.3], [-0.096, -0.259, -0.275], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.118, -0.248, -0.286], [-0.092, -0.218, -0.312], [-0.059, -0.177, -0.335], [-0.035, -0.145, -0.354], [0.0, -0.095, -0.38]],d=3)
    right_heel_roll_ctrl = gtu_combine_curves_list([right_heel_roll_ctrl_a, right_heel_roll_ctrl_b])
    
    shapes =  cmds.listRelatives(right_heel_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format(right_heel_roll_ctrl + first_shape_suffix))
    cmds.rename(shapes[1], "{0}Shape".format(right_heel_roll_ctrl + second_shape_suffix))
    
    # Match Right Side Look
    cmds.setAttr(right_heel_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_heel_roll_ctrl, apply=True, rotate=True)
    
    right_heel_roll_ctrl_grp = cmds.group(name=right_heel_roll_ctrl + '_' + grp_suffix, empty=True, world=True)
    cmds.parent(right_heel_roll_ctrl, right_heel_roll_ctrl_grp)
    
    # Right Heel Roll Scale
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleX', right_foot_scale_offset/6)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleY', right_foot_scale_offset/6)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset/6)
    cmds.makeIdentity(right_heel_roll_ctrl_grp, apply=True, scale=True)
    
    # Right Heel Position and Visibility
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_ankle_jnt'), right_heel_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset/3.5*-1,right_heel_roll_ctrl_grp, z=True, relative=True, objectSpace=True)
    
    change_viewport_color(right_heel_roll_ctrl, right_ctrl_color)
    cmds.parent(right_heel_roll_ctrl_grp, right_foot_ik_ctrl)


    # Left Finger Automation Controls
    # Left Fingers
    left_fingers_ctrl_a = cmds.curve(name='left_fingers_' + ctrl_suffix, p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449], [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.129, 0.347, -0.368], [0.091, 0.311, -0.402], [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.454, -0.268], [0.062, 0.519, 0.024], [0.062, 0.445, 0.232], [0.062, 0.355, 0.343], [0.062, 0.224, 0.445], [0.062, 0.0, 0.509], [0.062, -0.224, 0.445], [0.062, -0.355, 0.343], [0.062, -0.445, 0.232], [0.062, -0.519, 0.024], [0.062, -0.454, -0.268], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429], [0.091, -0.311, -0.402], [0.129, -0.347, -0.368], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34], [0.158, -0.332, -0.383], [0.123, -0.292, -0.418], [0.079, -0.237, -0.449], [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]],d=3)
    left_fingers_ctrl_b = cmds.curve(name=left_wrist_ik_ctrl_a + 'b', p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449], [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268], [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343], [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445], [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024], [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418], [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]],d=3)
    left_fingers_ctrl_c = cmds.curve(name=left_wrist_ik_ctrl_a + 'c', p=[[0.048, -0.0, 0.126], [0.073, 0.013, 0.139], [0.089, 0.023, 0.149], [0.109, 0.035, 0.16], [0.124, 0.046, 0.173], [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.13, 0.037, 0.179], [0.116, 0.026, 0.166], [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.17, 0.018, 0.216], [0.194, 0.018, 0.325], [0.166, 0.018, 0.403], [0.133, 0.018, 0.444], [0.084, 0.018, 0.482], [0.0, 0.018, 0.506], [-0.084, 0.018, 0.482], [-0.133, 0.018, 0.444], [-0.166, 0.018, 0.403], [-0.194, 0.018, 0.325], [-0.17, 0.018, 0.216], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156], [-0.116, 0.026, 0.166], [-0.13, 0.037, 0.179], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189], [-0.124, 0.046, 0.173], [-0.109, 0.035, 0.16], [-0.089, 0.023, 0.149], [-0.073, 0.013, 0.139], [-0.048, 0.0, 0.126]],d=3)
    left_fingers_ctrl_d = cmds.curve(name=left_wrist_ik_ctrl_a + 'd', p=[[0.048, -0.0, 0.126], [0.073, -0.013, 0.139], [0.089, -0.023, 0.149], [0.109, -0.035, 0.16], [0.124, -0.046, 0.173], [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.13, -0.037, 0.179], [0.116, -0.026, 0.166], [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.17, -0.018, 0.216], [0.194, -0.018, 0.325], [0.166, -0.018, 0.403], [0.133, -0.018, 0.444], [0.084, -0.018, 0.482], [-0.0, -0.018, 0.506], [-0.084, -0.018, 0.482], [-0.133, -0.018, 0.444], [-0.166, -0.018, 0.403], [-0.194, -0.018, 0.325], [-0.17, -0.018, 0.216], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156], [-0.116, -0.026, 0.166], [-0.13, -0.037, 0.179], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189], [-0.124, -0.046, 0.173], [-0.109, -0.035, 0.16], [-0.089, -0.023, 0.149], [-0.073, -0.013, 0.139], [-0.048, 0.0, 0.126]],d=3)
    left_fingers_ctrl = gtu_combine_curves_list([left_fingers_ctrl_a, left_fingers_ctrl_b, left_fingers_ctrl_c, left_fingers_ctrl_d])
    
    shapes =  cmds.listRelatives(left_fingers_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('big_arrow_l'))
    cmds.rename(shapes[1], "{0}Shape".format('big_arrow_r'))
    cmds.rename(shapes[2], "{0}Shape".format('small_arrow_u'))
    cmds.rename(shapes[3], "{0}Shape".format('small_arrow_d'))
    

    left_fingers_ctrl_grp = cmds.group(name=left_fingers_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_fingers_ctrl, left_fingers_ctrl_grp)
    
    cmds.setAttr(left_fingers_ctrl + '.rotateY', -90)
    cmds.setAttr(left_fingers_ctrl + '.scaleX', left_wrist_scale_offset*.3)
    cmds.setAttr(left_fingers_ctrl + '.scaleY', left_wrist_scale_offset*.3)
    cmds.setAttr(left_fingers_ctrl + '.scaleZ', left_wrist_scale_offset*.3)
    cmds.makeIdentity(left_fingers_ctrl, apply=True, scale=True, rotate=True)
  
    # Position
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_wrist_jnt'), left_fingers_ctrl_grp))
    cmds.rotate(90, left_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    cmds.move(left_wrist_scale_offset*2.3, left_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    
    # Hierarchy
    change_viewport_color(left_fingers_ctrl, left_ctrl_color)
    cmds.parent(left_fingers_ctrl_grp, left_hand_grp)

    # Right Finger Automation Controls
    # Right Fingers
    right_fingers_ctrl_a = cmds.curve(name='right_fingers_' + ctrl_suffix, p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449], [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.129, 0.347, -0.368], [0.091, 0.311, -0.402], [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.454, -0.268], [0.062, 0.519, 0.024], [0.062, 0.445, 0.232], [0.062, 0.355, 0.343], [0.062, 0.224, 0.445], [0.062, 0.0, 0.509], [0.062, -0.224, 0.445], [0.062, -0.355, 0.343], [0.062, -0.445, 0.232], [0.062, -0.519, 0.024], [0.062, -0.454, -0.268], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429], [0.091, -0.311, -0.402], [0.129, -0.347, -0.368], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34], [0.158, -0.332, -0.383], [0.123, -0.292, -0.418], [0.079, -0.237, -0.449], [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]],d=3)
    right_fingers_ctrl_b = cmds.curve(name=right_wrist_ik_ctrl_a + 'b', p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449], [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268], [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343], [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445], [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024], [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418], [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]],d=3)
    right_fingers_ctrl_c = cmds.curve(name=right_wrist_ik_ctrl_a + 'c', p=[[0.048, -0.0, 0.126], [0.073, 0.013, 0.139], [0.089, 0.023, 0.149], [0.109, 0.035, 0.16], [0.124, 0.046, 0.173], [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.13, 0.037, 0.179], [0.116, 0.026, 0.166], [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.17, 0.018, 0.216], [0.194, 0.018, 0.325], [0.166, 0.018, 0.403], [0.133, 0.018, 0.444], [0.084, 0.018, 0.482], [0.0, 0.018, 0.506], [-0.084, 0.018, 0.482], [-0.133, 0.018, 0.444], [-0.166, 0.018, 0.403], [-0.194, 0.018, 0.325], [-0.17, 0.018, 0.216], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156], [-0.116, 0.026, 0.166], [-0.13, 0.037, 0.179], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189], [-0.124, 0.046, 0.173], [-0.109, 0.035, 0.16], [-0.089, 0.023, 0.149], [-0.073, 0.013, 0.139], [-0.048, 0.0, 0.126]],d=3)
    right_fingers_ctrl_d = cmds.curve(name=right_wrist_ik_ctrl_a + 'd', p=[[0.048, -0.0, 0.126], [0.073, -0.013, 0.139], [0.089, -0.023, 0.149], [0.109, -0.035, 0.16], [0.124, -0.046, 0.173], [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.13, -0.037, 0.179], [0.116, -0.026, 0.166], [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.17, -0.018, 0.216], [0.194, -0.018, 0.325], [0.166, -0.018, 0.403], [0.133, -0.018, 0.444], [0.084, -0.018, 0.482], [-0.0, -0.018, 0.506], [-0.084, -0.018, 0.482], [-0.133, -0.018, 0.444], [-0.166, -0.018, 0.403], [-0.194, -0.018, 0.325], [-0.17, -0.018, 0.216], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156], [-0.116, -0.026, 0.166], [-0.13, -0.037, 0.179], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189], [-0.124, -0.046, 0.173], [-0.109, -0.035, 0.16], [-0.089, -0.023, 0.149], [-0.073, -0.013, 0.139], [-0.048, 0.0, 0.126]],d=3)
    right_fingers_ctrl = gtu_combine_curves_list([right_fingers_ctrl_a, right_fingers_ctrl_b, right_fingers_ctrl_c, right_fingers_ctrl_d])
    
    shapes =  cmds.listRelatives(right_fingers_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], "{0}Shape".format('big_arrow_l'))
    cmds.rename(shapes[1], "{0}Shape".format('big_arrow_r'))
    cmds.rename(shapes[2], "{0}Shape".format('small_arrow_u'))
    cmds.rename(shapes[3], "{0}Shape".format('small_arrow_d'))

    right_fingers_ctrl_grp = cmds.group(name=right_fingers_ctrl + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_fingers_ctrl, right_fingers_ctrl_grp)
    
    cmds.setAttr(right_fingers_ctrl + '.rotateY', 90)
    cmds.setAttr(right_fingers_ctrl + '.scaleX', right_wrist_scale_offset*.3)
    cmds.setAttr(right_fingers_ctrl + '.scaleY', right_wrist_scale_offset*.3)
    cmds.setAttr(right_fingers_ctrl + '.scaleZ', right_wrist_scale_offset*.3)
    cmds.makeIdentity(right_fingers_ctrl, apply=True, scale=True, rotate=True)
  
    # Position
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_wrist_jnt'), right_fingers_ctrl_grp))
    cmds.rotate(90, right_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    cmds.move(-right_wrist_scale_offset*2.3, right_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    
    # Hierarchy
    change_viewport_color(right_fingers_ctrl, right_ctrl_color)
    cmds.parent(right_fingers_ctrl_grp, right_hand_grp)

    ################# ======= Rig Mechanics ======= #################
    
    # Main Scale
    cmds.connectAttr(main_ctrl + '.sy', main_ctrl + '.sx', f=True)
    cmds.connectAttr(main_ctrl + '.sy', main_ctrl + '.sz', f=True)
    
    ################# Center FK #################
    cmds.parentConstraint(main_ctrl, gt_ab_joints.get('main_jnt'))
    cmds.parentConstraint(cog_ctrl, gt_ab_joints.get('cog_jnt'))
    lock_hide_default_attr(cog_ctrl, translate=False, rotate=False)
    
    # Spine 01
    cmds.parentConstraint(spine01_ctrl, gt_ab_joints.get('spine01_jnt')) # Automated
    offset_group = cmds.group(name=spine01_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(spine01_ctrl_grp, offset_group))
    cmds.parent(offset_group, spine01_ctrl_grp)
    cmds.parent(spine01_ctrl, offset_group)
    
    spine01_condition_node = cmds.createNode('condition', name=spine01_ctrl.replace(ctrl_suffix, '') + automation_suffix)
    cmds.connectAttr(spine02_ctrl + '.rotate', spine01_condition_node + '.colorIfTrue', f=True)
    cmds.connectAttr(spine01_condition_node + '.outColor', offset_group + '.rotate', f=True)
    cmds.setAttr(spine01_condition_node + '.secondTerm', 1)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseB', 0)
    
    
    cmds.addAttr(spine02_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(spine02_ctrl + '.controlBehavior', lock=True)
    
    cmds.addAttr(spine02_ctrl, ln="spine01AutoRotate", at='bool', k=True, niceName='Auto Rotate Spine 01')
    cmds.setAttr(spine02_ctrl + '.spine01AutoRotate', 1)
    cmds.connectAttr(spine02_ctrl + '.spine01AutoRotate', spine01_condition_node + '.firstTerm', f=True)
    
    cmds.addAttr(spine02_ctrl, ln="spine01Visibility", at='bool', k=True, niceName='Visibility Spine 01')
    
    for shape in cmds.listRelatives(spine01_ctrl, s=True, f=True) or []:
        cmds.connectAttr(spine02_ctrl + '.spine01Visibility', shape + '.visibility', f=True)
    
    lock_hide_default_attr(spine01_ctrl, translate=False, rotate=False)
    
    # Spine 02
    cmds.parentConstraint(spine02_ctrl, gt_ab_joints.get('spine02_jnt')) 
    lock_hide_default_attr(spine02_ctrl, translate=False, rotate=False)
    
    # Spine 03
    cmds.parentConstraint(spine03_ctrl, gt_ab_joints.get('spine03_jnt')) # Automated
    offset_group = cmds.group(name=spine03_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(spine03_ctrl_grp, offset_group))
    cmds.parent(offset_group, spine03_ctrl_grp)
    cmds.parent(spine03_ctrl, offset_group)
    
    spine03_condition_node = cmds.createNode('condition', name=spine03_ctrl.replace(ctrl_suffix, '') + automation_suffix)
    cmds.connectAttr(spine04_ctrl + '.rotate', spine03_condition_node + '.colorIfTrue', f=True)
    cmds.connectAttr(spine03_condition_node + '.outColor', offset_group + '.rotate', f=True)
    cmds.setAttr(spine03_condition_node + '.secondTerm', 1)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseB', 0)
    
    cmds.addAttr(spine04_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(spine04_ctrl + '.controlBehavior', lock=True)
    
    cmds.addAttr(spine04_ctrl, ln="spine03AutoRotate", at='bool', k=True, niceName='Auto Rotate Spine 03')
    cmds.setAttr(spine04_ctrl + '.spine03AutoRotate', 1)
    cmds.connectAttr(spine04_ctrl + '.spine03AutoRotate', spine03_condition_node + '.firstTerm', f=True)
    
    cmds.addAttr(spine04_ctrl, ln="spine03Visibility", at='bool', k=True, niceName='Visibility Spine 03')
    
    for shape in cmds.listRelatives(spine03_ctrl, s=True, f=True) or []:
        cmds.connectAttr(spine04_ctrl + '.spine03Visibility', shape + '.visibility', f=True)
        
    lock_hide_default_attr(spine03_ctrl, translate=False, rotate=False)
    
    # Spine 04
    cmds.parentConstraint(spine04_ctrl, gt_ab_joints.get('spine04_jnt')) 
    lock_hide_default_attr(spine04_ctrl, translate=False, rotate=False)
    
    # Neck Base
    cmds.parentConstraint(neck_base_ctrl, gt_ab_joints.get('neck_base_jnt')) 
    lock_hide_default_attr(neck_base_ctrl, translate=False, rotate=False)

    # Neck Mid
    cmds.parentConstraint(neck_mid_ctrl, gt_ab_joints.get('neck_mid_jnt')) # Automated
    offset_group = cmds.group(name=neck_mid_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(neck_mid_ctrl_grp, offset_group))
    cmds.parent(offset_group, neck_mid_ctrl_grp)
    cmds.parent(neck_mid_ctrl, offset_group)
    
    neck_mid_condition_node = cmds.createNode('condition', name=neck_mid_ctrl.replace(ctrl_suffix, '') + automation_suffix)
    cmds.connectAttr(neck_base_ctrl + '.rotate', neck_mid_condition_node + '.colorIfTrue', f=True)
    cmds.connectAttr(neck_mid_condition_node + '.outColor', offset_group + '.rotate', f=True)
    cmds.setAttr(neck_mid_condition_node + '.secondTerm', 1)
    cmds.setAttr(neck_mid_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(neck_mid_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(neck_mid_condition_node + '.colorIfFalseB', 0)
    
    cmds.addAttr(neck_base_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(neck_base_ctrl + '.controlBehavior', lock=True)
    
    cmds.addAttr(neck_base_ctrl, ln="neckMidAutoRotate", at='bool', k=True, niceName='Auto Rotate Neck Mid')
    cmds.setAttr(neck_base_ctrl + '.neckMidAutoRotate', 1)
    cmds.connectAttr(neck_base_ctrl + '.neckMidAutoRotate', neck_mid_condition_node + '.firstTerm', f=True)
    
    cmds.addAttr(neck_base_ctrl, ln="neckMidVisibility", at='bool', k=True, niceName='Visibility Neck Mid')
    
    for shape in cmds.listRelatives(neck_mid_ctrl, s=True, f=True) or []:
        cmds.connectAttr(neck_base_ctrl + '.neckMidVisibility', shape + '.visibility', f=True)
    
    lock_hide_default_attr(neck_mid_ctrl, translate=False, rotate=False)
    
    # Head Ctrl
    cmds.parentConstraint(head_ctrl, gt_ab_joints.get('head_jnt'))
    lock_hide_default_attr(head_ctrl, translate=False, rotate=False)
    
    # Jaw Ctrl
    cmds.parentConstraint(jaw_ctrl, gt_ab_joints.get('jaw_jnt')) 
    lock_hide_default_attr(jaw_ctrl, translate=False, rotate=False)
    
    # Hip Ctrl
    cmds.parentConstraint(hip_ctrl, gt_ab_joints.get('hip_jnt')) 
    lock_hide_default_attr(hip_ctrl, translate=False, rotate=False)
    
    ################# Left FK Controls #################
    # Left Leg
    cmds.parentConstraint(left_hip_ctrl, left_hip_fk_jnt)
    cmds.parentConstraint(left_knee_ctrl, left_knee_fk_jnt)
    cmds.parentConstraint(left_ankle_ctrl, left_ankle_fk_jnt)
    cmds.parentConstraint(left_ball_ctrl, left_ball_fk_jnt)
    lock_hide_default_attr(left_hip_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_knee_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_ankle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_ball_ctrl, translate=False, rotate=False)
    
    # Left Arm
    cmds.parentConstraint(left_clavicle_ctrl, left_clavicle_switch_jnt)
    cmds.parentConstraint(left_shoulder_ctrl, left_shoulder_fk_jnt)
    cmds.parentConstraint(left_elbow_ctrl, left_elbow_fk_jnt)
    cmds.parentConstraint(left_wrist_ctrl, left_wrist_fk_jnt)
    lock_hide_default_attr(left_clavicle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_shoulder_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_elbow_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_wrist_ctrl, translate=False, rotate=False)
    
    # Left Fingers
    cmds.parentConstraint(left_thumb01_ctrl_list[0], gt_ab_joints.get('left_thumb01_jnt'))
    cmds.parentConstraint(left_thumb02_ctrl_list[0], gt_ab_joints.get('left_thumb02_jnt'))
    cmds.parentConstraint(left_thumb03_ctrl_list[0], gt_ab_joints.get('left_thumb03_jnt'))
    lock_hide_default_attr(left_thumb01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_thumb02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_thumb03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(left_index01_ctrl_list[0], gt_ab_joints.get('left_index01_jnt'))
    cmds.parentConstraint(left_index02_ctrl_list[0], gt_ab_joints.get('left_index02_jnt'))
    cmds.parentConstraint(left_index03_ctrl_list[0], gt_ab_joints.get('left_index03_jnt'))
    lock_hide_default_attr(left_index01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_index02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_index03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(left_middle01_ctrl_list[0], gt_ab_joints.get('left_middle01_jnt'))
    cmds.parentConstraint(left_middle02_ctrl_list[0], gt_ab_joints.get('left_middle02_jnt'))
    cmds.parentConstraint(left_middle03_ctrl_list[0], gt_ab_joints.get('left_middle03_jnt'))
    lock_hide_default_attr(left_middle01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_middle02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_middle03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(left_ring01_ctrl_list[0], gt_ab_joints.get('left_ring01_jnt'))
    cmds.parentConstraint(left_ring02_ctrl_list[0], gt_ab_joints.get('left_ring02_jnt'))
    cmds.parentConstraint(left_ring03_ctrl_list[0], gt_ab_joints.get('left_ring03_jnt'))
    lock_hide_default_attr(left_ring01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_ring02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_ring03_ctrl_list[0], translate=False, rotate=False)
   
    cmds.parentConstraint(left_pinky01_ctrl_list[0], gt_ab_joints.get('left_pinky01_jnt'))
    cmds.parentConstraint(left_pinky02_ctrl_list[0], gt_ab_joints.get('left_pinky02_jnt'))
    cmds.parentConstraint(left_pinky03_ctrl_list[0], gt_ab_joints.get('left_pinky03_jnt'))
    lock_hide_default_attr(left_pinky01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_pinky02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(left_pinky03_ctrl_list[0], translate=False, rotate=False)
    
    left_fingers_list = [(left_thumb01_ctrl_list, left_thumb02_ctrl_list, left_thumb03_ctrl_list),\
                         (left_index01_ctrl_list, left_index02_ctrl_list, left_index03_ctrl_list),\
                         (left_middle01_ctrl_list, left_middle02_ctrl_list, left_middle03_ctrl_list),\
                         (left_ring01_ctrl_list, left_ring02_ctrl_list, left_ring03_ctrl_list),\
                         (left_pinky01_ctrl_list, left_pinky02_ctrl_list, left_pinky03_ctrl_list)]
        
    # Add Custom Attributes
    cmds.addAttr(left_fingers_ctrl , ln='automationSystem', at='enum', k=True, en="Fingers:")
    cmds.addAttr(left_fingers_ctrl , ln='activateSystem', at='bool', k=True)
    cmds.setAttr(left_fingers_ctrl + '.activateSystem', 1)
    lock_hide_default_attr(left_fingers_ctrl, rotate=False)
    cmds.setAttr(left_fingers_ctrl + '.automationSystem', lock=True)
    add_node_note(left_fingers_ctrl, 'Finger automation system. Rotating this control will cause fingers to rotate in the same direction. Convenient for when quickly creating a fist pose.\nAttributes:\n-Activate System: Whether or not the system is active.\n\n-Fist Pose Limit: What rotation should be considered a "fist" pose for the fingers.\n\n-Rot Multiplier: How much of the rotation will be transfered to the selected finger. (Used to create a less robotic movement between the fingers)')
    
    # Left Auto Offset
    for obj in left_fingers_list:
        finger_name = remove_numbers(obj[0][0].replace(ctrl_suffix, ''))
        
        # Create Nodes
        active_condition_node = cmds.createNode('condition', name=finger_name + automation_suffix)
        limit_condition_node = cmds.createNode('condition', name=finger_name + 'limit')
        multiply_node = cmds.createNode('multiplyDivide', name=finger_name + multiply_suffix)
        
        attribute_fist_pose_long = finger_name.replace('left_','').replace('right_','').replace('_','') + 'FistPoseLimit'
        attribute_fist_pose_nice = 'Fist Pose Limit ' + finger_name.replace('left_','').replace('right_','').replace('_','').capitalize()
        cmds.addAttr(left_fingers_ctrl , ln=attribute_fist_pose_long, at='double', k=True, niceName=attribute_fist_pose_nice)
        cmds.setAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, -90)
        
        attribute_long_name = finger_name.replace('left_','').replace('right_','').replace('_','') + 'Multiplier'
        attribute_nice_name = 'Rot Multiplier ' + finger_name.replace('left_','').replace('right_','').replace('_','').capitalize()
        cmds.addAttr(left_fingers_ctrl , ln=attribute_long_name, at='double', k=True, niceName=attribute_nice_name) 
        
        # Set Default Values
        cmds.setAttr(active_condition_node + '.secondTerm', 1)
        cmds.setAttr(active_condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseB', 0)
        cmds.setAttr(limit_condition_node + '.operation', 3)
        
        # Offset
        if 'thumb' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .7)
        elif 'index' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .8)
        elif 'middle' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .9)
        else:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, 1)
        
        # Connect Nodes
        cmds.connectAttr(left_fingers_ctrl + '.activateSystem', active_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.rotate', multiply_node + '.input1', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2X', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Y', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Z', f=True)
        cmds.connectAttr(active_condition_node + '.outColorB', limit_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(multiply_node + '.output', active_condition_node + '.colorIfTrue', f=True)
        cmds.connectAttr(active_condition_node + '.outColor', limit_condition_node + '.colorIfTrue', f=True)
   
        # Set Limits
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.secondTerm', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseR', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseG', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseB', f=True)

        for finger in obj:
            cmds.connectAttr(active_condition_node + '.outColorR', finger[2] + '.rotateX', f=True)
            cmds.connectAttr(active_condition_node + '.outColorG', finger[2] + '.rotateY', f=True)
            cmds.connectAttr(limit_condition_node + '.outColorB', finger[2] + '.rotateZ', f=True)
            
    ################# Right FK Controls #################
    # Right Leg
    cmds.parentConstraint(right_hip_ctrl, right_hip_fk_jnt)
    cmds.parentConstraint(right_knee_ctrl, right_knee_fk_jnt)
    cmds.parentConstraint(right_ankle_ctrl, right_ankle_fk_jnt)
    cmds.parentConstraint(right_ball_ctrl, right_ball_fk_jnt)
    lock_hide_default_attr(right_hip_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_knee_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_ankle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_ball_ctrl, translate=False, rotate=False)
    
    # Right Arm
    cmds.parentConstraint(right_clavicle_ctrl, right_clavicle_switch_jnt)
    cmds.parentConstraint(right_shoulder_ctrl, right_shoulder_fk_jnt)
    cmds.parentConstraint(right_elbow_ctrl, right_elbow_fk_jnt)
    cmds.parentConstraint(right_wrist_ctrl, right_wrist_fk_jnt)
    lock_hide_default_attr(right_clavicle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_shoulder_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_elbow_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_wrist_ctrl, translate=False, rotate=False)
    
    # Right Fingers
    cmds.parentConstraint(right_thumb01_ctrl_list[0], gt_ab_joints.get('right_thumb01_jnt'))
    cmds.parentConstraint(right_thumb02_ctrl_list[0], gt_ab_joints.get('right_thumb02_jnt'))
    cmds.parentConstraint(right_thumb03_ctrl_list[0], gt_ab_joints.get('right_thumb03_jnt'))
    lock_hide_default_attr(right_thumb01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_thumb02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_thumb03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(right_index01_ctrl_list[0], gt_ab_joints.get('right_index01_jnt'))
    cmds.parentConstraint(right_index02_ctrl_list[0], gt_ab_joints.get('right_index02_jnt'))
    cmds.parentConstraint(right_index03_ctrl_list[0], gt_ab_joints.get('right_index03_jnt'))
    lock_hide_default_attr(right_index01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_index02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_index03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(right_middle01_ctrl_list[0], gt_ab_joints.get('right_middle01_jnt'))
    cmds.parentConstraint(right_middle02_ctrl_list[0], gt_ab_joints.get('right_middle02_jnt'))
    cmds.parentConstraint(right_middle03_ctrl_list[0], gt_ab_joints.get('right_middle03_jnt'))
    lock_hide_default_attr(right_middle01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_middle02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_middle03_ctrl_list[0], translate=False, rotate=False)
    
    cmds.parentConstraint(right_ring01_ctrl_list[0], gt_ab_joints.get('right_ring01_jnt'))
    cmds.parentConstraint(right_ring02_ctrl_list[0], gt_ab_joints.get('right_ring02_jnt'))
    cmds.parentConstraint(right_ring03_ctrl_list[0], gt_ab_joints.get('right_ring03_jnt'))
    lock_hide_default_attr(right_ring01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_ring02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_ring03_ctrl_list[0], translate=False, rotate=False)
   
    cmds.parentConstraint(right_pinky01_ctrl_list[0], gt_ab_joints.get('right_pinky01_jnt'))
    cmds.parentConstraint(right_pinky02_ctrl_list[0], gt_ab_joints.get('right_pinky02_jnt'))
    cmds.parentConstraint(right_pinky03_ctrl_list[0], gt_ab_joints.get('right_pinky03_jnt'))
    lock_hide_default_attr(right_pinky01_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_pinky02_ctrl_list[0], translate=False, rotate=False)
    lock_hide_default_attr(right_pinky03_ctrl_list[0], translate=False, rotate=False)
    
    right_fingers_list = [(right_thumb01_ctrl_list, right_thumb02_ctrl_list, right_thumb03_ctrl_list),\
                         (right_index01_ctrl_list, right_index02_ctrl_list, right_index03_ctrl_list),\
                         (right_middle01_ctrl_list, right_middle02_ctrl_list, right_middle03_ctrl_list),\
                         (right_ring01_ctrl_list, right_ring02_ctrl_list, right_ring03_ctrl_list),\
                         (right_pinky01_ctrl_list, right_pinky02_ctrl_list, right_pinky03_ctrl_list)]
        
    # Add Custom Attributes
    cmds.addAttr(right_fingers_ctrl , ln='automationSystem', at='enum', k=True, en="Fingers:")
    cmds.addAttr(right_fingers_ctrl , ln='activateSystem', at='bool', k=True)
    cmds.setAttr(right_fingers_ctrl + '.activateSystem', 1)
    lock_hide_default_attr(right_fingers_ctrl, rotate=False)
    cmds.setAttr(right_fingers_ctrl + '.automationSystem', lock=True)
    add_node_note(right_fingers_ctrl, 'Finger automation system. Rotating this control will cause fingers to rotate in the same direction. Convenient for when quickly creating a fist pose.\nAttributes:\n-Activate System: Whether or not the system is active.\n\n-Fist Pose Limit: What rotation should be considered a "fist" pose for the fingers.\n\n-Rot Multiplier: How much of the rotation will be transfered to the selected finger. (Used to create a less robotic movement between the fingers)')
    
    # Right Auto Offset
    for obj in right_fingers_list:
        finger_name = remove_numbers(obj[0][0].replace(ctrl_suffix, ''))
        
        # Create Nodes
        active_condition_node = cmds.createNode('condition', name=finger_name + automation_suffix)
        limit_condition_node = cmds.createNode('condition', name=finger_name + 'limit')
        multiply_node = cmds.createNode('multiplyDivide', name=finger_name + multiply_suffix)
        
        attribute_fist_pose_long = finger_name.replace('right_','').replace('right_','').replace('_','') + 'FistPoseLimit'
        attribute_fist_pose_nice = 'Fist Pose Limit ' + finger_name.replace('right_','').replace('right_','').replace('_','').capitalize()
        cmds.addAttr(right_fingers_ctrl , ln=attribute_fist_pose_long, at='double', k=True, niceName=attribute_fist_pose_nice)
        cmds.setAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, -90)
        
        attribute_long_name = finger_name.replace('right_','').replace('right_','').replace('_','') + 'Multiplier'
        attribute_nice_name = 'Rot Multiplier ' + finger_name.replace('right_','').replace('right_','').replace('_','').capitalize()
        cmds.addAttr(right_fingers_ctrl , ln=attribute_long_name, at='double', k=True, niceName=attribute_nice_name) 
        
        # Set Default Values
        cmds.setAttr(active_condition_node + '.secondTerm', 1)
        cmds.setAttr(active_condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseB', 0)
        cmds.setAttr(limit_condition_node + '.operation', 3)
        
        # Offset
        if 'thumb' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .7)
        elif 'index' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .8)
        elif 'middle' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .9)
        else:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, 1)
        
        # Connect Nodes
        cmds.connectAttr(right_fingers_ctrl + '.activateSystem', active_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.rotate', multiply_node + '.input1', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2X', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Y', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Z', f=True)
        cmds.connectAttr(active_condition_node + '.outColorB', limit_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(multiply_node + '.output', active_condition_node + '.colorIfTrue', f=True)
        cmds.connectAttr(active_condition_node + '.outColor', limit_condition_node + '.colorIfTrue', f=True)
   
        # Set Limits
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.secondTerm', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseR', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseG', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseB', f=True)

        for finger in obj:
            cmds.connectAttr(active_condition_node + '.outColorR', finger[2] + '.rotateX', f=True)
            cmds.connectAttr(active_condition_node + '.outColorG', finger[2] + '.rotateY', f=True)
            cmds.connectAttr(limit_condition_node + '.outColorB', finger[2] + '.rotateZ', f=True)

    ################# IK Controls #################
    rig_setup_grp = cmds.group(name='rig_setup_' + grp_suffix, empty=True, world=True)
    ik_solvers_grp = cmds.group(name='ikSolvers_' + grp_suffix, empty=True, world=True)
    change_outliner_color(rig_setup_grp, (1,.26,.26))
    change_outliner_color(ik_solvers_grp, (1,1,.35))
    cmds.parent(ik_solvers_grp, rig_setup_grp)
    
    
    ################# Left Leg IK Controls #################
    left_leg_rp_ik_handle = cmds.ikHandle( n='left_footAnkle_RP_ikHandle', sj=left_hip_ik_jnt, ee=left_ankle_ik_jnt, sol='ikRPsolver')
    left_leg_ball_ik_handle = cmds.ikHandle( n='left_footBall_SC_ikHandle', sj=left_ankle_ik_jnt, ee=left_ball_ik_jnt, sol='ikSCsolver')
    left_leg_toe_ik_handle = cmds.ikHandle( n='left_footToe_SC_ikHandle', sj=left_ball_ik_jnt, ee=left_toe_ik_jnt, sol='ikSCsolver')
    cmds.poleVectorConstraint(left_knee_ik_ctrl, left_leg_rp_ik_handle[0])
    
    # Left Foot Automation Setup
    left_foot_pivot_grp = cmds.group(name='left_foot_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    left_heel_pivot_grp = cmds.group(name='left_heel_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    left_ball_pivot_grp = cmds.group(name='left_ball_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    left_toe_pivot_grp = cmds.group(name='left_toe_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    left_toe_pos_pivot_grp = cmds.group(name='left_toeUpDown_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(left_toe_pos_pivot_grp, left_toe_pivot_grp)

    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_ankle_jnt'), left_foot_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('left_ball_pivot_grp'), left_heel_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_ball_jnt'), left_ball_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('left_toe_jnt'), left_toe_pivot_grp))
    
    desired_rotation = cmds.xform(gt_ab_settings.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_foot_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_heel_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_ball_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_toe_pivot_grp + '.ry', desired_rotation[1])
    
    cmds.parent(left_foot_pivot_grp, rig_setup_grp)
    cmds.parent(left_heel_pivot_grp, left_foot_pivot_grp)
    cmds.parent(left_toe_pivot_grp, left_heel_pivot_grp)
    cmds.parent(left_ball_pivot_grp, left_toe_pivot_grp)
    
    cmds.parent(left_leg_toe_ik_handle[0], left_toe_pos_pivot_grp)
    cmds.parent(left_leg_ball_ik_handle[0], left_ball_pivot_grp)
    cmds.parent(left_leg_rp_ik_handle[0], left_ball_pivot_grp)
    cmds.parentConstraint(left_foot_ik_ctrl, left_foot_pivot_grp, mo=True)
    
    cmds.connectAttr(left_ball_roll_ctrl + '.rotate', left_ball_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_toe_roll_ctrl + '.rotate', left_toe_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_heel_roll_ctrl + '.rotate', left_heel_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.translate', left_toe_pos_pivot_grp + '.translate', f=True)
    
    # Left Leg Switch
    lock_hide_default_attr(left_leg_switch)
    cmds.addAttr(left_leg_switch, ln="switchAttributes", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(left_leg_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(left_leg_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(left_leg_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(left_leg_switch, ln="footAutomation", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(left_leg_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(left_leg_switch + '.ctrlVisibility', 1)
    cmds.setAttr(left_leg_switch + '.footAutomation', lock=True)
    cmds.setAttr(left_leg_switch + '.switchAttributes', lock=True)
    cmds.setAttr(left_leg_switch + '.autoVisibility', 1)
    cmds.setAttr(left_leg_switch + '.systemVisibility', 1)
    cmds.setAttr(left_leg_switch + '.influenceSwitch', 1)
    
    left_switch_condition_node = cmds.createNode('condition', name='left_leg_switchVisibility_' + automation_suffix)
    left_visibility_condition_node = cmds.createNode('condition', name='left_leg_autoVisibility_' + automation_suffix)
    
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_visibility_condition_node + '.operation', 3)
    cmds.setAttr(left_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseB', 0)
    
    cmds.connectAttr(left_leg_switch + '.systemVisibility', left_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(left_leg_switch + '.autoVisibility', left_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_switch_condition_node + '.secondTerm', 1)
    
    cmds.connectAttr(left_visibility_condition_node + '.outColor', left_switch_condition_node + '.colorIfTrue', f=True)
    
    # IK Reverse
    left_v_reverse_node = cmds.createNode('reverse', name='left_leg_autoVisibility_reverse')
    cmds.connectAttr(left_switch_condition_node + '.outColorR', left_v_reverse_node + '.inputX', f=True)
    
    # IK Visibility
    visibility_ik = [left_foot_ik_ctrl_grp, left_knee_ik_ctrl_grp]
    
    for obj in visibility_ik:
        cmds.connectAttr(left_switch_condition_node + '.outColorR', obj + '.v', f=True)
    
    for shape in cmds.listRelatives(left_leg_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(left_switch_condition_node + '.outColorR', shape + '.v', f=True)
    
    # Fk Visibility
    visibility_fk = [left_hip_ctrl_grp, left_knee_ctrl_grp, left_ankle_ctrl_grp, left_ball_ctrl_grp]
    
    for obj in visibility_fk:
        cmds.connectAttr(left_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_leg_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(left_v_reverse_node + '.outputX', shape + '.v', f=True)
            
    # FK IK Constraints
    left_hip_constraint = cmds.parentConstraint([left_hip_fk_jnt, left_hip_ik_jnt], gt_ab_joints.get('left_hip_jnt'))
    left_knee_constraint = cmds.parentConstraint([left_knee_fk_jnt, left_knee_ik_jnt], gt_ab_joints.get('left_knee_jnt'))
    left_ankle_constraint = cmds.parentConstraint([left_ankle_fk_jnt, left_ankle_ik_jnt], gt_ab_joints.get('left_ankle_jnt'))
    left_ball_constraint = cmds.parentConstraint([left_ball_fk_jnt, left_ball_ik_jnt], gt_ab_joints.get('left_ball_jnt'))
    left_switch_constraint = cmds.parentConstraint([left_foot_ik_ctrl, left_ankle_ctrl], left_leg_switch_grp, mo=True)

    left_switch_reverse_node = cmds.createNode('reverse', name='left_leg_switch_reverse')
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_switch_reverse_node + '.inputX', f=True)
    
    #FK
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_hip_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_knee_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_ankle_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_ball_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_constraint[0] + '.w1', f=True)
    
    #IK
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_hip_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_knee_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ankle_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ball_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_switch_constraint[0] + '.w0', f=True)
    
    # Foot Automation Visibility
    cmds.connectAttr(left_leg_switch + '.ctrlVisibility', left_heel_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.ctrlVisibility', left_ball_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.ctrlVisibility', left_toe_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.ctrlVisibility', left_toe_up_down_ctrl_grp + '.v', f=True)
    
    # IK Knee Automation
    left_knee_ctrl_constraint = cmds.parentConstraint(left_foot_ik_ctrl, left_knee_ik_ctrl_grp, mo=True)
    cmds.addAttr(left_knee_ik_ctrl, ln="kneeAutomation", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_knee_ik_ctrl + '.kneeAutomation', lock=True)
    cmds.addAttr(left_knee_ik_ctrl , ln='followFoot', at='bool', k=True)
    cmds.connectAttr(left_knee_ik_ctrl + '.followFoot', left_knee_ctrl_constraint[0] + '.w0', f=True)
    
    # General Adjustment
    lock_hide_default_attr(left_foot_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_heel_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_ball_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_toe_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_toe_up_down_ctrl, translate=False)
    lock_hide_default_attr(left_knee_ik_ctrl, translate=False)
    
    # Left Leg Stretchy System
    
    cmds.addAttr(left_leg_switch, ln="squashStretch", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_leg_switch + '.squashStretch', lock=True)
    left_leg_stretchy_elements = make_stretchy_ik(left_leg_rp_ik_handle[0], 'left_leg', left_leg_switch)
    
    # Transfer Data to Base Skeleton
    left_hip_scale_blend = cmds.createNode('blendColors', name='left_hip_switchScale_blend')
    left_knee_scale_blend = cmds.createNode('blendColors', name='left_knee_switchScale_blend')

    cmds.connectAttr(left_hip_ik_jnt + '.scale', left_hip_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_hip_fk_jnt + '.scale', left_hip_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_hip_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_hip_scale_blend + '.output', gt_ab_joints.get('left_hip_jnt') + '.scale', f=True)
    
    cmds.connectAttr(left_knee_ik_jnt + '.scale', left_knee_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_knee_fk_jnt + '.scale', left_knee_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_knee_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_knee_scale_blend + '.output', gt_ab_joints.get('left_knee_jnt') + '.scale', f=True)
 
    
    # Left Foot Control Limits
    # Heel, Ball and Toe
    for ctrl in [left_heel_roll_ctrl, left_ball_roll_ctrl, left_toe_roll_ctrl]:
        cmds.addAttr(ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
        cmds.setAttr(ctrl + '.controlBehavior', lock=True)
        cmds.addAttr(ctrl, ln='lockYZ', at='bool', k=True)
        cmds.setAttr(ctrl + '.lockYZ', 1)

        cmds.setAttr(ctrl + '.minRotYLimit', 0)
        cmds.setAttr(ctrl + '.maxRotYLimit', 0)
        cmds.setAttr(ctrl + '.minRotZLimit', 0)
        cmds.setAttr(ctrl + '.maxRotZLimit', 0)
        
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotZLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotZLimitEnable', f=True)
        
    # Left Toe Up and Down
    cmds.addAttr(left_toe_up_down_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_toe_up_down_ctrl + '.controlBehavior', lock=True)
    cmds.addAttr(left_toe_up_down_ctrl, ln='lockXZ', at='bool', k=True)
    cmds.setAttr(left_toe_up_down_ctrl + '.lockXZ', 1)

    cmds.setAttr(left_toe_up_down_ctrl + '.minTransXLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.maxTransXLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.minTransZLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.maxTransZLimit', 0)
    
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.minTransXLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.maxTransXLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.minTransZLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.maxTransZLimitEnable', f=True)
    
    
    ################# Right Leg IK Controls #################
    right_leg_rp_ik_handle = cmds.ikHandle( n='right_footAnkle_RP_ikHandle', sj=right_hip_ik_jnt, ee=right_ankle_ik_jnt, sol='ikRPsolver')
    right_leg_ball_ik_handle = cmds.ikHandle( n='right_footBall_SC_ikHandle', sj=right_ankle_ik_jnt, ee=right_ball_ik_jnt, sol='ikSCsolver')
    right_leg_toe_ik_handle = cmds.ikHandle( n='right_footToe_SC_ikHandle', sj=right_ball_ik_jnt, ee=right_toe_ik_jnt, sol='ikSCsolver')
    cmds.poleVectorConstraint(right_knee_ik_ctrl, right_leg_rp_ik_handle[0])
    
    # Right Foot Automation Setup
    right_foot_pivot_grp = cmds.group(name='right_foot_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    right_heel_pivot_grp = cmds.group(name='right_heel_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    right_ball_pivot_grp = cmds.group(name='right_ball_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    right_toe_pivot_grp = cmds.group(name='right_toe_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    right_toe_pos_pivot_grp = cmds.group(name='right_toeUpDown_pivot' + grp_suffix.capitalize(), empty=True, world=True)
    cmds.parent(right_toe_pos_pivot_grp, right_toe_pivot_grp)

    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_ankle_jnt'), right_foot_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_settings.get('right_ball_pivot_grp'), right_heel_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_ball_jnt'), right_ball_pivot_grp))
    cmds.delete(cmds.pointConstraint(gt_ab_joints.get('right_toe_jnt'), right_toe_pivot_grp))
    
    desired_rotation = cmds.xform(gt_ab_settings.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_foot_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_heel_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_ball_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_toe_pivot_grp + '.ry', desired_rotation[1])
    
    cmds.parent(right_foot_pivot_grp, rig_setup_grp)
    cmds.parent(right_heel_pivot_grp, right_foot_pivot_grp)
    cmds.parent(right_toe_pivot_grp, right_heel_pivot_grp)
    cmds.parent(right_ball_pivot_grp, right_toe_pivot_grp)
    
    cmds.parent(right_leg_toe_ik_handle[0], right_toe_pos_pivot_grp)
    cmds.parent(right_leg_ball_ik_handle[0], right_ball_pivot_grp)
    cmds.parent(right_leg_rp_ik_handle[0], right_ball_pivot_grp)
    cmds.parentConstraint(right_foot_ik_ctrl, right_foot_pivot_grp, mo=True)
    
    cmds.connectAttr(right_ball_roll_ctrl + '.rotate', right_ball_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_toe_roll_ctrl + '.rotate', right_toe_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_heel_roll_ctrl + '.rotate', right_heel_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.translate', right_toe_pos_pivot_grp + '.translate', f=True)
    
    # Right Leg Switch
    lock_hide_default_attr(right_leg_switch)
    cmds.addAttr(right_leg_switch, ln="switchAttributes", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(right_leg_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(right_leg_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(right_leg_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(right_leg_switch, ln="footAutomation", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(right_leg_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(right_leg_switch + '.ctrlVisibility', 1)
    cmds.setAttr(right_leg_switch + '.footAutomation', lock=True)
    cmds.setAttr(right_leg_switch + '.switchAttributes', lock=True)
    cmds.setAttr(right_leg_switch + '.autoVisibility', 1)
    cmds.setAttr(right_leg_switch + '.systemVisibility', 1)
    cmds.setAttr(right_leg_switch + '.influenceSwitch', 1)
    
    right_switch_condition_node = cmds.createNode('condition', name='right_leg_switchVisibility_' + automation_suffix)
    right_visibility_condition_node = cmds.createNode('condition', name='right_leg_autoVisibility_' + automation_suffix)
    
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_visibility_condition_node + '.operation', 3)
    cmds.setAttr(right_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseB', 0)
    
    cmds.connectAttr(right_leg_switch + '.systemVisibility', right_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(right_leg_switch + '.autoVisibility', right_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_switch_condition_node + '.secondTerm', 1)
    
    cmds.connectAttr(right_visibility_condition_node + '.outColor', right_switch_condition_node + '.colorIfTrue', f=True)
    
    # IK Reverse
    right_v_reverse_node = cmds.createNode('reverse', name='right_leg_autoVisibility_reverse')
    cmds.connectAttr(right_switch_condition_node + '.outColorR', right_v_reverse_node + '.inputX', f=True)
    
    # IK Visibility
    visibility_ik = [right_foot_ik_ctrl_grp, right_knee_ik_ctrl_grp]
    
    for obj in visibility_ik:
        cmds.connectAttr(right_switch_condition_node + '.outColorR', obj + '.v', f=True)
    
    for shape in cmds.listRelatives(right_leg_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(right_switch_condition_node + '.outColorR', shape + '.v', f=True)
    
    # Fk Visibility
    visibility_fk = [right_hip_ctrl_grp, right_knee_ctrl_grp, right_ankle_ctrl_grp, right_ball_ctrl_grp]
    
    for obj in visibility_fk:
        cmds.connectAttr(right_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_leg_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(right_v_reverse_node + '.outputX', shape + '.v', f=True)
            
    # FK IK Constraints
    right_hip_constraint = cmds.parentConstraint([right_hip_fk_jnt, right_hip_ik_jnt], gt_ab_joints.get('right_hip_jnt'))
    right_knee_constraint = cmds.parentConstraint([right_knee_fk_jnt, right_knee_ik_jnt], gt_ab_joints.get('right_knee_jnt'))
    right_ankle_constraint = cmds.parentConstraint([right_ankle_fk_jnt, right_ankle_ik_jnt], gt_ab_joints.get('right_ankle_jnt'))
    right_ball_constraint = cmds.parentConstraint([right_ball_fk_jnt, right_ball_ik_jnt], gt_ab_joints.get('right_ball_jnt'))
    right_switch_constraint = cmds.parentConstraint([right_foot_ik_ctrl, right_ankle_ctrl], right_leg_switch_grp, mo=True)

    right_switch_reverse_node = cmds.createNode('reverse', name='right_leg_switch_reverse')
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_switch_reverse_node + '.inputX', f=True)
    
    #FK
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_hip_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_knee_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_ankle_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_ball_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_constraint[0] + '.w1', f=True)
    
    #IK
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_hip_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_knee_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ankle_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ball_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_switch_constraint[0] + '.w0', f=True)
    
    # Foot Automation Visibility
    cmds.connectAttr(right_leg_switch + '.ctrlVisibility', right_heel_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.ctrlVisibility', right_ball_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.ctrlVisibility', right_toe_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.ctrlVisibility', right_toe_up_down_ctrl_grp + '.v', f=True)
    
    # IK Knee Automation
    right_knee_ctrl_constraint = cmds.parentConstraint(right_foot_ik_ctrl, right_knee_ik_ctrl_grp, mo=True)
    cmds.addAttr(right_knee_ik_ctrl, ln="kneeAutomation", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_knee_ik_ctrl + '.kneeAutomation', lock=True)
    cmds.addAttr(right_knee_ik_ctrl , ln='followFoot', at='bool', k=True)
    cmds.connectAttr(right_knee_ik_ctrl + '.followFoot', right_knee_ctrl_constraint[0] + '.w0', f=True)
    
    # General Adjustment
    lock_hide_default_attr(right_foot_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_heel_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_ball_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_toe_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_toe_up_down_ctrl, translate=False)
    lock_hide_default_attr(right_knee_ik_ctrl, translate=False)
    
    # Right Leg Stretchy System
    
    cmds.addAttr(right_leg_switch, ln="squashStretch", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_leg_switch + '.squashStretch', lock=True)
    right_leg_stretchy_elements = make_stretchy_ik(right_leg_rp_ik_handle[0], 'right_leg', right_leg_switch)
    
    # Transfer Data to Base Skeleton
    right_hip_scale_blend = cmds.createNode('blendColors', name='right_hip_switchScale_blend')
    right_knee_scale_blend = cmds.createNode('blendColors', name='right_knee_switchScale_blend')

    cmds.connectAttr(right_hip_ik_jnt + '.scale', right_hip_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_hip_fk_jnt + '.scale', right_hip_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_hip_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_hip_scale_blend + '.output', gt_ab_joints.get('right_hip_jnt') + '.scale', f=True)
    
    cmds.connectAttr(right_knee_ik_jnt + '.scale', right_knee_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_knee_fk_jnt + '.scale', right_knee_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_knee_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_knee_scale_blend + '.output', gt_ab_joints.get('right_knee_jnt') + '.scale', f=True)
    
    # Right Foot Control Limits
    # Heel, Ball and Toe
    for ctrl in [right_heel_roll_ctrl, right_ball_roll_ctrl, right_toe_roll_ctrl]:
        cmds.addAttr(ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
        cmds.setAttr(ctrl + '.controlBehavior', lock=True)
        cmds.addAttr(ctrl, ln='lockYZ', at='bool', k=True)
        cmds.setAttr(ctrl + '.lockYZ', 1)

        cmds.setAttr(ctrl + '.minRotYLimit', 0)
        cmds.setAttr(ctrl + '.maxRotYLimit', 0)
        cmds.setAttr(ctrl + '.minRotZLimit', 0)
        cmds.setAttr(ctrl + '.maxRotZLimit', 0)
        
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotZLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotZLimitEnable', f=True)
        
    # Right Toe Up and Down
    cmds.addAttr(right_toe_up_down_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_toe_up_down_ctrl + '.controlBehavior', lock=True)
    cmds.addAttr(right_toe_up_down_ctrl, ln='lockXZ', at='bool', k=True)
    cmds.setAttr(right_toe_up_down_ctrl + '.lockXZ', 1)

    cmds.setAttr(right_toe_up_down_ctrl + '.minTransXLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.maxTransXLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.minTransZLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.maxTransZLimit', 0)
    
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.minTransXLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.maxTransXLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.minTransZLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.maxTransZLimitEnable', f=True)

    
    ################# Organize Stretchy System Elements #################
    stretchy_system_grp = cmds.group(name='stretchySystem_' + grp_suffix, empty=True, world=True)
    foot_automation_grp = cmds.group(name='footAutomation_' + grp_suffix, empty=True, world=True)
    change_outliner_color(stretchy_system_grp, (.5, 1, .85))
    change_outliner_color(foot_automation_grp, (1, .65, .45))
    cmds.parent(left_leg_stretchy_elements[1], stretchy_system_grp)
    cmds.parent(right_leg_stretchy_elements[1], stretchy_system_grp)
    cmds.parent(stretchy_system_grp, rig_setup_grp)
    cmds.parent(foot_automation_grp, rig_setup_grp)
    cmds.parent(left_foot_pivot_grp, foot_automation_grp)
    cmds.parent(right_foot_pivot_grp, foot_automation_grp)
    #cmds.setAttr(foot_automation_grp + '.v', 0)
    #cmds.setAttr(stretchy_system_grp + '.v', 0)
    #cmds.setAttr(ik_solvers_grp + '.v', 0)
    lock_hide_default_attr(foot_automation_grp, visibility=False)
    lock_hide_default_attr(stretchy_system_grp, visibility=False)
    lock_hide_default_attr(ik_solvers_grp, visibility=False)
 
    
    ################# Left Arm Controls #################   
    # Left Arm Handles
    left_arm_rp_ik_handle = cmds.ikHandle( n='left_armWrist_RP_ikHandle', sj=left_shoulder_ik_jnt, ee=left_wrist_ik_jnt, sol='ikRPsolver')
    cmds.poleVectorConstraint(left_elbow_ik_ctrl, left_arm_rp_ik_handle[0])
    cmds.parent(left_arm_rp_ik_handle[0], ik_solvers_grp)
    cmds.pointConstraint(left_wrist_ik_ctrl, left_arm_rp_ik_handle[0])
    cmds.orientConstraint(left_wrist_ik_ctrl, left_wrist_ik_jnt)
    
    
    # Left Arm Switch
    lock_hide_default_attr(left_arm_switch)
    cmds.addAttr(left_arm_switch, ln="switchAttributes", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(left_arm_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(left_arm_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(left_arm_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(left_arm_switch, ln="fingerAutomation", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(left_arm_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(left_arm_switch + '.ctrlVisibility', 1)
    cmds.setAttr(left_arm_switch + '.fingerAutomation', lock=True)
    cmds.setAttr(left_arm_switch + '.switchAttributes', lock=True)
    cmds.setAttr(left_arm_switch + '.autoVisibility', 1)
    cmds.setAttr(left_arm_switch + '.systemVisibility', 1)
    cmds.setAttr(left_arm_switch + '.influenceSwitch', 1)
    
    left_switch_condition_node = cmds.createNode('condition', name='left_arm_switchVisibility_' + automation_suffix)
    left_visibility_condition_node = cmds.createNode('condition', name='left_arm_autoVisibility_' + automation_suffix)
    
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_visibility_condition_node + '.operation', 3)
    cmds.setAttr(left_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseB', 0)
    
    cmds.connectAttr(left_arm_switch + '.systemVisibility', left_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(left_arm_switch + '.autoVisibility', left_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_switch_condition_node + '.secondTerm', 1)
    
    cmds.connectAttr(left_visibility_condition_node + '.outColor', left_switch_condition_node + '.colorIfTrue', f=True)
    
    # IK Reverse
    left_v_reverse_node = cmds.createNode('reverse', name='left_arm_autoVisibility_reverse')
    cmds.connectAttr(left_switch_condition_node + '.outColorR', left_v_reverse_node + '.inputX', f=True)
    
    # IK Visibility
    visibility_ik = [left_wrist_ik_ctrl_grp, left_elbow_ik_ctrl_grp]
    
    for obj in visibility_ik:
        cmds.connectAttr(left_switch_condition_node + '.outColorR', obj + '.v', f=True)
    
    for shape in cmds.listRelatives(left_arm_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(left_switch_condition_node + '.outColorR', shape + '.v', f=True)
    
    # Fk Visibility
    visibility_fk = [left_shoulder_ctrl_grp, left_elbow_ctrl_grp, left_wrist_ctrl_grp]
    
    for obj in visibility_fk:
        cmds.connectAttr(left_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_arm_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(left_v_reverse_node + '.outputX', shape + '.v', f=True)
            
    # FK IK Constraints
    left_clavicle_constraint = cmds.parentConstraint(left_clavicle_ctrl, gt_ab_joints.get('left_clavicle_jnt'))
    left_shoulder_constraint = cmds.parentConstraint([left_shoulder_fk_jnt, left_shoulder_ik_jnt], gt_ab_joints.get('left_shoulder_jnt'))
    left_elbow_constraint = cmds.parentConstraint([left_elbow_fk_jnt, left_elbow_ik_jnt], gt_ab_joints.get('left_elbow_jnt'))
    left_wrist_constraint = cmds.parentConstraint([left_wrist_fk_jnt, left_wrist_ik_jnt], gt_ab_joints.get('left_wrist_jnt'))
    left_switch_constraint = cmds.parentConstraint([left_wrist_ik_ctrl, left_wrist_ctrl], left_arm_switch_grp, mo=True)
    left_hand_constraint = cmds.parentConstraint([left_wrist_ik_ctrl, left_wrist_ctrl], left_hand_grp, mo=True)
    

    left_switch_reverse_node = cmds.createNode('reverse', name='left_arm_switch_reverse')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_reverse_node + '.inputX', f=True)
    
    #FK
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_shoulder_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_elbow_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_wrist_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_hand_constraint[0] + '.w1', f=True)
    
    #IK
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_shoulder_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_elbow_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_wrist_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_hand_constraint[0] + '.w0', f=True)
    
    
    # Foot Automation Visibility
    cmds.connectAttr(left_arm_switch + '.ctrlVisibility', left_fingers_ctrl_grp + '.v', f=True)

    
    # IK Knee Automation
    left_wrist_ctrl_constraint = cmds.parentConstraint(left_wrist_ik_ctrl, left_elbow_ik_ctrl_grp, mo=True)
    cmds.addAttr(left_elbow_ik_ctrl, ln="elbowAutomation", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_elbow_ik_ctrl + '.elbowAutomation', lock=True)
    cmds.addAttr(left_elbow_ik_ctrl , ln='followWrist', at='bool', k=True)
    cmds.connectAttr(left_elbow_ik_ctrl + '.followWrist', left_wrist_ctrl_constraint[0] + '.w0', f=True)
    
    # General Adjustment
    lock_hide_default_attr(left_wrist_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_elbow_ik_ctrl, translate=False)
    

    # Left Leg Stretchy System
    cmds.addAttr(left_arm_switch, ln="squashStretch", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_arm_switch + '.squashStretch', lock=True)
    left_arm_stretchy_elements = make_stretchy_ik(left_arm_rp_ik_handle[0], 'left_arm', left_arm_switch)
    cmds.parent(left_arm_stretchy_elements[1], stretchy_system_grp)


    # Transfer Data to Base Skeleton
    left_shoulder_scale_blend = cmds.createNode('blendColors', name='left_shoulder_switchScale_blend')
    left_elbow_scale_blend = cmds.createNode('blendColors', name='left_elbow_switchScale_blend')

    cmds.connectAttr(left_shoulder_ik_jnt + '.scale', left_shoulder_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_shoulder_fk_jnt + '.scale', left_shoulder_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_shoulder_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_shoulder_scale_blend + '.output', gt_ab_joints.get('left_shoulder_jnt') + '.scale', f=True)
    
    cmds.connectAttr(left_elbow_ik_jnt + '.scale', left_elbow_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_elbow_fk_jnt + '.scale', left_elbow_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_elbow_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_elbow_scale_blend + '.output', gt_ab_joints.get('left_elbow_jnt') + '.scale', f=True)
    
    
    # Left Hand Ctrl Visibility Type
    cmds.addAttr(left_arm_switch, ln="handControl", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_arm_switch + '.handControl', lock=True)
    cmds.addAttr(left_arm_switch, ln="visibilityType", at="enum", en="Semi-Circle:Pin:", keyable=True)

    left_v_type_condition_node = cmds.createNode('condition', name='left_arm_visibilityType_condition')
    left_v_type_reverse_node = cmds.createNode('reverse', name='left_arm_visibilityType_reverse')
    cmds.connectAttr(left_arm_switch + '.visibilityType', left_v_type_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(left_v_type_condition_node + '.outColorR', left_v_type_reverse_node + '.inputX', f=True)
    

    for shape in cmds.listRelatives(left_wrist_ik_ctrl, s=True, f=True) or []:
        if 'semiCircle' in shape:
            cmds.connectAttr(left_v_type_reverse_node + '.outputX', shape + '.v', f=True)
        elif 'pin' in shape:
            cmds.connectAttr(left_v_type_condition_node + '.outColorR', shape + '.v', f=True)
    
    
    # Left Fingers Limits
    cmds.addAttr(left_fingers_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(left_fingers_ctrl + '.controlBehavior', lock=True)
    cmds.addAttr(left_fingers_ctrl, ln='lockXY', at='bool', k=True)
    cmds.setAttr(left_fingers_ctrl + '.lockXY', 1)
    
    cmds.setAttr(left_fingers_ctrl + '.minRotXLimit', 0)
    cmds.setAttr(left_fingers_ctrl + '.maxRotXLimit', 0)
    cmds.setAttr(left_fingers_ctrl + '.minRotYLimit', 0)
    cmds.setAttr(left_fingers_ctrl + '.maxRotYLimit', 0)
        
    cmds.connectAttr(left_fingers_ctrl + '.lockXY', left_fingers_ctrl + '.minRotXLimitEnable', f=True)
    cmds.connectAttr(left_fingers_ctrl + '.lockXY', left_fingers_ctrl + '.maxRotXLimitEnable', f=True)
    cmds.connectAttr(left_fingers_ctrl + '.lockXY', left_fingers_ctrl + '.minRotYLimitEnable', f=True)
    cmds.connectAttr(left_fingers_ctrl + '.lockXY', left_fingers_ctrl + '.maxRotYLimitEnable', f=True)
    
    
    # Left Forearm Rotation
    left_forearm_grp = cmds.group(name=left_forearm_jnt + grp_suffix.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_elbow_jnt'), left_forearm_grp))
    cmds.parent(left_forearm_jnt, left_forearm_grp)
    cmds.parent(left_forearm_grp, skeleton_grp)
    cmds.pointConstraint([gt_ab_joints.get('left_elbow_jnt'), gt_ab_joints.get('left_wrist_jnt')], left_forearm_grp)
    cmds.orientConstraint(gt_ab_joints.get('left_elbow_jnt'), left_forearm_grp)
    cmds.setAttr(left_forearm_jnt + '.tx', 0)
    cmds.setAttr(left_forearm_jnt + '.ty', 0)
    cmds.setAttr(left_forearm_jnt + '.tz', 0)
    
    cmds.addAttr(left_arm_switch, ln='forearmRotation', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(left_arm_switch + '.forearmRotation', 1)
    
    left_forearm_multiply_node = cmds.createNode('multiplyDivide', name="left_arm_foreArmRotation_" + multiply_suffix)
    
    cmds.connectAttr(left_arm_switch + '.forearmRotation', left_forearm_multiply_node + '.input2X', f=True)
    cmds.connectAttr(gt_ab_joints.get('left_wrist_jnt') + '.rotateX', left_forearm_multiply_node + '.input1X', f=True)
    cmds.connectAttr(left_forearm_multiply_node + '.outputX', left_forearm_jnt + '.rotateX', f=True)
    
    # Left IK Follow Clavicle
    left_clavicle_wrist_constraint = cmds.parentConstraint(left_clavicle_ctrl, left_wrist_ik_ctrl_grp, mo=True)
    cmds.addAttr(left_arm_switch, ln='followClavicle', at='bool', k=True)
    cmds.setAttr(left_arm_switch + '.followClavicle', 1)
    cmds.connectAttr(left_arm_switch + '.followClavicle', left_clavicle_wrist_constraint[0] + '.w0', f=True)
    
    
    ################# Right Arm Controls #################   
    # Right Arm Handles
    right_arm_rp_ik_handle = cmds.ikHandle( n='right_armWrist_RP_ikHandle', sj=right_shoulder_ik_jnt, ee=right_wrist_ik_jnt, sol='ikRPsolver')
    cmds.poleVectorConstraint(right_elbow_ik_ctrl, right_arm_rp_ik_handle[0])
    cmds.parent(right_arm_rp_ik_handle[0], ik_solvers_grp)
    cmds.pointConstraint(right_wrist_ik_ctrl, right_arm_rp_ik_handle[0])
    cmds.orientConstraint(right_wrist_ik_ctrl, right_wrist_ik_jnt)
    
    
    # Right Arm Switch
    lock_hide_default_attr(right_arm_switch)
    cmds.addAttr(right_arm_switch, ln="switchAttributes", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(right_arm_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(right_arm_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(right_arm_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(right_arm_switch, ln="fingerAutomation", at="enum", en="-------------:", keyable=True)
    cmds.addAttr(right_arm_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(right_arm_switch + '.ctrlVisibility', 1)
    cmds.setAttr(right_arm_switch + '.fingerAutomation', lock=True)
    cmds.setAttr(right_arm_switch + '.switchAttributes', lock=True)
    cmds.setAttr(right_arm_switch + '.autoVisibility', 1)
    cmds.setAttr(right_arm_switch + '.systemVisibility', 1)
    cmds.setAttr(right_arm_switch + '.influenceSwitch', 1)
    
    right_switch_condition_node = cmds.createNode('condition', name='right_arm_switchVisibility_' + automation_suffix)
    right_visibility_condition_node = cmds.createNode('condition', name='right_arm_autoVisibility_' + automation_suffix)
    
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_visibility_condition_node + '.operation', 3)
    cmds.setAttr(right_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseB', 0)
    
    cmds.connectAttr(right_arm_switch + '.systemVisibility', right_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(right_arm_switch + '.autoVisibility', right_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_switch_condition_node + '.secondTerm', 1)
    
    cmds.connectAttr(right_visibility_condition_node + '.outColor', right_switch_condition_node + '.colorIfTrue', f=True)
    
    # IK Reverse
    right_v_reverse_node = cmds.createNode('reverse', name='right_arm_autoVisibility_reverse')
    cmds.connectAttr(right_switch_condition_node + '.outColorR', right_v_reverse_node + '.inputX', f=True)
    
    # IK Visibility
    visibility_ik = [right_wrist_ik_ctrl_grp, right_elbow_ik_ctrl_grp]
    
    for obj in visibility_ik:
        cmds.connectAttr(right_switch_condition_node + '.outColorR', obj + '.v', f=True)
    
    for shape in cmds.listRelatives(right_arm_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(right_switch_condition_node + '.outColorR', shape + '.v', f=True)
    
    # Fk Visibility
    visibility_fk = [right_shoulder_ctrl_grp, right_elbow_ctrl_grp, right_wrist_ctrl_grp]
    
    for obj in visibility_fk:
        cmds.connectAttr(right_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_arm_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(right_v_reverse_node + '.outputX', shape + '.v', f=True)
            
    # FK IK Constraints
    right_clavicle_constraint = cmds.parentConstraint(right_clavicle_ctrl, gt_ab_joints.get('right_clavicle_jnt'))
    right_shoulder_constraint = cmds.parentConstraint([right_shoulder_fk_jnt, right_shoulder_ik_jnt], gt_ab_joints.get('right_shoulder_jnt'))
    right_elbow_constraint = cmds.parentConstraint([right_elbow_fk_jnt, right_elbow_ik_jnt], gt_ab_joints.get('right_elbow_jnt'))
    right_wrist_constraint = cmds.parentConstraint([right_wrist_fk_jnt, right_wrist_ik_jnt], gt_ab_joints.get('right_wrist_jnt'))
    right_switch_constraint = cmds.parentConstraint([right_wrist_ik_ctrl, right_wrist_ctrl], right_arm_switch_grp, mo=True)
    right_hand_constraint = cmds.parentConstraint([right_wrist_ik_ctrl, right_wrist_ctrl], right_hand_grp, mo=True)
    

    right_switch_reverse_node = cmds.createNode('reverse', name='right_arm_switch_reverse')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_reverse_node + '.inputX', f=True)
    
    #FK
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_shoulder_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_elbow_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_wrist_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_hand_constraint[0] + '.w1', f=True)
    
    #IK
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_shoulder_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_elbow_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_wrist_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_hand_constraint[0] + '.w0', f=True)
    
    
    # Foot Automation Visibility
    cmds.connectAttr(right_arm_switch + '.ctrlVisibility', right_fingers_ctrl_grp + '.v', f=True)

    
    # IK Knee Automation
    right_wrist_ctrl_constraint = cmds.parentConstraint(right_wrist_ik_ctrl, right_elbow_ik_ctrl_grp, mo=True)
    cmds.addAttr(right_elbow_ik_ctrl, ln="elbowAutomation", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_elbow_ik_ctrl + '.elbowAutomation', lock=True)
    cmds.addAttr(right_elbow_ik_ctrl , ln='followWrist', at='bool', k=True)
    cmds.connectAttr(right_elbow_ik_ctrl + '.followWrist', right_wrist_ctrl_constraint[0] + '.w0', f=True)
    
    # General Adjustment
    lock_hide_default_attr(right_wrist_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_elbow_ik_ctrl, translate=False)
    

    # Right Leg Stretchy System
    cmds.addAttr(right_arm_switch, ln="squashStretch", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_arm_switch + '.squashStretch', lock=True)
    right_arm_stretchy_elements = make_stretchy_ik(right_arm_rp_ik_handle[0], 'right_arm', right_arm_switch)
    cmds.parent(right_arm_stretchy_elements[1], stretchy_system_grp)


    # Transfer Data to Base Skeleton
    right_shoulder_scale_blend = cmds.createNode('blendColors', name='right_shoulder_switchScale_blend')
    right_elbow_scale_blend = cmds.createNode('blendColors', name='right_elbow_switchScale_blend')

    cmds.connectAttr(right_shoulder_ik_jnt + '.scale', right_shoulder_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_shoulder_fk_jnt + '.scale', right_shoulder_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_shoulder_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_shoulder_scale_blend + '.output', gt_ab_joints.get('right_shoulder_jnt') + '.scale', f=True)
    
    cmds.connectAttr(right_elbow_ik_jnt + '.scale', right_elbow_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_elbow_fk_jnt + '.scale', right_elbow_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_elbow_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_elbow_scale_blend + '.output', gt_ab_joints.get('right_elbow_jnt') + '.scale', f=True)
    
    
    # Right Hand Ctrl Visibility Type
    cmds.addAttr(right_arm_switch, ln="handControl", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_arm_switch + '.handControl', lock=True)
    cmds.addAttr(right_arm_switch, ln="visibilityType", at="enum", en="Semi-Circle:Pin:", keyable=True)

    right_v_type_condition_node = cmds.createNode('condition', name='right_arm_visibilityType_condition')
    right_v_type_reverse_node = cmds.createNode('reverse', name='right_arm_visibilityType_reverse')
    cmds.connectAttr(right_arm_switch + '.visibilityType', right_v_type_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(right_v_type_condition_node + '.outColorR', right_v_type_reverse_node + '.inputX', f=True)
    

    for shape in cmds.listRelatives(right_wrist_ik_ctrl, s=True, f=True) or []:
        if 'semiCircle' in shape:
            cmds.connectAttr(right_v_type_reverse_node + '.outputX', shape + '.v', f=True)
        elif 'pin' in shape:
            cmds.connectAttr(right_v_type_condition_node + '.outColorR', shape + '.v', f=True)
    
    
    # Right Fingers Limits
    cmds.addAttr(right_fingers_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(right_fingers_ctrl + '.controlBehavior', lock=True)
    cmds.addAttr(right_fingers_ctrl, ln='lockXY', at='bool', k=True)
    cmds.setAttr(right_fingers_ctrl + '.lockXY', 1)
    
    cmds.setAttr(right_fingers_ctrl + '.minRotXLimit', 0)
    cmds.setAttr(right_fingers_ctrl + '.maxRotXLimit', 0)
    cmds.setAttr(right_fingers_ctrl + '.minRotYLimit', 0)
    cmds.setAttr(right_fingers_ctrl + '.maxRotYLimit', 0)
        
    cmds.connectAttr(right_fingers_ctrl + '.lockXY', right_fingers_ctrl + '.minRotXLimitEnable', f=True)
    cmds.connectAttr(right_fingers_ctrl + '.lockXY', right_fingers_ctrl + '.maxRotXLimitEnable', f=True)
    cmds.connectAttr(right_fingers_ctrl + '.lockXY', right_fingers_ctrl + '.minRotYLimitEnable', f=True)
    cmds.connectAttr(right_fingers_ctrl + '.lockXY', right_fingers_ctrl + '.maxRotYLimitEnable', f=True)
    
    
    # Right Forearm Rotation
    right_forearm_grp = cmds.group(name=right_forearm_jnt + grp_suffix.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_elbow_jnt'), right_forearm_grp))
    cmds.parent(right_forearm_jnt, right_forearm_grp)
    cmds.parent(right_forearm_grp, skeleton_grp)
    cmds.pointConstraint([gt_ab_joints.get('right_elbow_jnt'), gt_ab_joints.get('right_wrist_jnt')], right_forearm_grp)
    cmds.orientConstraint(gt_ab_joints.get('right_elbow_jnt'), right_forearm_grp)
    cmds.setAttr(right_forearm_jnt + '.tx', 0)
    cmds.setAttr(right_forearm_jnt + '.ty', 0)
    cmds.setAttr(right_forearm_jnt + '.tz', 0)
    
    cmds.addAttr(right_arm_switch, ln='forearmRotation', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(right_arm_switch + '.forearmRotation', 1)
    
    right_forearm_multiply_node = cmds.createNode('multiplyDivide', name="right_arm_foreArmRotation_" + multiply_suffix)
    
    cmds.connectAttr(right_arm_switch + '.forearmRotation', right_forearm_multiply_node + '.input2X', f=True)
    cmds.connectAttr(gt_ab_joints.get('right_wrist_jnt') + '.rotateX', right_forearm_multiply_node + '.input1X', f=True)
    cmds.connectAttr(right_forearm_multiply_node + '.outputX', right_forearm_jnt + '.rotateX', f=True)
    
    # Right IK Follow Clavicle
    right_clavicle_wrist_constraint = cmds.parentConstraint(right_clavicle_ctrl, right_wrist_ik_ctrl_grp, mo=True)
    cmds.addAttr(right_arm_switch, ln='followClavicle', at='bool', k=True)
    cmds.setAttr(right_arm_switch + '.followClavicle', 1)
    cmds.connectAttr(right_arm_switch + '.followClavicle', right_clavicle_wrist_constraint[0] + '.w0', f=True)


    ################# Lock Parameters for FK Controls #################

    for obj in [left_knee_ctrl, left_elbow_ctrl, right_knee_ctrl, right_elbow_ctrl]:
        cmds.addAttr(obj, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
        cmds.setAttr(obj + '.controlBehavior', lock=True)
        cmds.addAttr(obj, ln='lockTranslate', at='bool', k=True)
        cmds.setAttr(obj + '.lockTranslate', 1)
        cmds.addAttr(obj, ln='lockXY', at='bool', k=True)
        cmds.setAttr(obj + '.lockXY', 1)
        
        cmds.setAttr(obj + '.minRotXLimit', 0)
        cmds.setAttr(obj + '.maxRotXLimit', 0)
        cmds.setAttr(obj + '.minRotYLimit', 0)
        cmds.setAttr(obj + '.maxRotYLimit', 0)
        cmds.setAttr(obj + '.minTransXLimit', 0)
        cmds.setAttr(obj + '.maxTransXLimit', 0)
        cmds.setAttr(obj + '.minTransYLimit', 0)
        cmds.setAttr(obj + '.maxTransYLimit', 0)
        cmds.setAttr(obj + '.minTransZLimit', 0)
        cmds.setAttr(obj + '.maxTransZLimit', 0)
            
        cmds.connectAttr(obj + '.lockXY', obj + '.minRotXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockXY', obj + '.maxRotXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockXY', obj + '.minRotYLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockXY', obj + '.maxRotYLimitEnable', f=True)
        
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransYLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransYLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransZLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransZLimitEnable', f=True)
        
    for obj in [left_hip_ctrl, left_ankle_ctrl, left_ball_ctrl, left_clavicle_ctrl, left_shoulder_ctrl, left_wrist_ctrl,\
                right_hip_ctrl, right_ankle_ctrl, right_ball_ctrl, right_clavicle_ctrl, right_shoulder_ctrl, right_wrist_ctrl,\
                spine01_ctrl, spine02_ctrl, spine03_ctrl, spine04_ctrl, neck_base_ctrl, neck_mid_ctrl, hip_ctrl, jaw_ctrl, head_ctrl]:
        
        if not obj.startswith('spine02') and not obj.startswith('spine04') and not obj.startswith('neckBase'):
            cmds.addAttr(obj, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
            cmds.setAttr(obj + '.controlBehavior', lock=True)
        cmds.addAttr(obj, ln='lockTranslate', at='bool', k=True)
        cmds.setAttr(obj + '.lockTranslate', 1)
      
        cmds.setAttr(obj + '.minTransXLimit', 0)
        cmds.setAttr(obj + '.maxTransXLimit', 0)
        cmds.setAttr(obj + '.minTransYLimit', 0)
        cmds.setAttr(obj + '.maxTransYLimit', 0)
        cmds.setAttr(obj + '.minTransZLimit', 0)
        cmds.setAttr(obj + '.maxTransZLimit', 0)
            
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransXLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransYLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransYLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.minTransZLimitEnable', f=True)
        cmds.connectAttr(obj + '.lockTranslate', obj + '.maxTransZLimitEnable', f=True)
        
    # Eyes
    lock_hide_default_attr(main_eye_ctrl, translate=False)
    lock_hide_default_attr(left_eye_ctrl, translate=False)
    lock_hide_default_attr(right_eye_ctrl, translate=False)
    cmds.parent(main_eye_ctrl_grp, direction_ctrl)
    main_eye_constraint = cmds.parentConstraint([head_ctrl, direction_ctrl], main_eye_ctrl_grp, mo=True)
    cmds.addAttr(main_eye_ctrl, ln="controlBehavior", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(main_eye_ctrl + '.controlBehavior', lock=True)
    cmds.addAttr(main_eye_ctrl, ln='followHead', at='double', k=True, minValue=0, maxValue=1)
    cmds.setAttr(main_eye_ctrl + '.followHead', 1)
    
    eye_follow_head_reverse_node = cmds.createNode('reverse', name='eyes_followHead_reverse')
    cmds.connectAttr(main_eye_ctrl + '.followHead', main_eye_constraint[0] + '.w0', f=True)
    cmds.connectAttr(main_eye_ctrl + '.followHead', eye_follow_head_reverse_node + '.inputX', f=True)
    cmds.connectAttr(eye_follow_head_reverse_node + '.outputX', main_eye_constraint[0] + '.w1', f=True)
    
    # Left Eye
    left_eye_up_vec = cmds.spaceLocator( name='left_eye_upVec' )[0]
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('left_eye_jnt'), left_eye_up_vec))
    cmds.move(general_scale_offset, left_eye_up_vec, y=True, relative=True, objectSpace=True)
    cmds.setAttr(left_eye_up_vec + '.lsx', general_scale_offset*.1)
    cmds.setAttr(left_eye_up_vec + '.lsy', general_scale_offset*.1)
    cmds.setAttr(left_eye_up_vec + '.lsz', general_scale_offset*.1)
    cmds.setAttr(left_eye_up_vec + '.v', 0)
    cmds.parent(left_eye_up_vec, head_ctrl)
    change_viewport_color(left_eye_up_vec, (1, 0, 0))
    
    cmds.aimConstraint(left_eye_ctrl, gt_ab_joints.get('left_eye_jnt'), mo=True, upVector=(0, 1, 0), worldUpType="object", worldUpObject=left_eye_up_vec)
 
    # Right Eye
    right_eye_up_vec = cmds.spaceLocator( name='right_eye_upVec' )[0]
    cmds.delete(cmds.parentConstraint(gt_ab_joints.get('right_eye_jnt'), right_eye_up_vec))
    cmds.move(general_scale_offset, right_eye_up_vec, y=True, relative=True, objectSpace=True)
    cmds.setAttr(right_eye_up_vec + '.lsx', general_scale_offset*.1)
    cmds.setAttr(right_eye_up_vec + '.lsy', general_scale_offset*.1)
    cmds.setAttr(right_eye_up_vec + '.lsz', general_scale_offset*.1)
    cmds.setAttr(right_eye_up_vec + '.v', 0)
    cmds.parent(right_eye_up_vec, head_ctrl)
    change_viewport_color(right_eye_up_vec, (1, 0, 0))
    
    cmds.aimConstraint(right_eye_ctrl, gt_ab_joints.get('right_eye_jnt'), mo=True, upVector=(0, 1, 0), worldUpType="object", worldUpObject=right_eye_up_vec)
 
    # Scale Constraints
    cmds.scaleConstraint(main_ctrl, skeleton_grp)
    cmds.scaleConstraint(main_ctrl, rig_setup_grp)
    
    # Other Groups
    geometry_grp = cmds.group(name='geometry_grp', empty=True, world=True)
    change_outliner_color(geometry_grp, (.3,1,.8))
    rig_grp = cmds.group(name='rig_grp', empty=True, world=True)
    change_outliner_color(rig_grp, (1,.45,.7))
    
    # Lock Groups
    lock_hide_default_attr(controls_grp, visibility=False)
    lock_hide_default_attr(skeleton_grp, visibility=False)
    lock_hide_default_attr(direction_ctrl, translate=False, rotate=False, visibility=False)
    lock_hide_default_attr(rig_setup_grp, visibility=False)
    lock_hide_default_attr(geometry_grp, visibility=False)
    lock_hide_default_attr(rig_grp, visibility=False)
 
    # Hierarchy Adjustments and Color
    cmds.setAttr(rig_setup_grp + '.v', 0)
    cmds.setAttr(left_clavicle_switch_jnt + '.v', 0)
    cmds.setAttr(right_clavicle_switch_jnt + '.v', 0)
    cmds.setAttr(hip_switch_jnt + '.v', 0)

    cmds.parent(geometry_grp, rig_grp)
    cmds.parent(skeleton_grp, rig_grp)
    cmds.parent(controls_grp, rig_grp)
    cmds.parent(rig_setup_grp, rig_grp)
    
    cmds.setAttr(main_ctrl + '.sx', k=False)
    cmds.setAttr(main_ctrl + '.sz', k=False)
    cmds.addAttr(main_ctrl, ln="rigOptions", at="enum", en="-------------:", keyable=True)
    cmds.setAttr(main_ctrl + '.rigOptions', lock=True)
    cmds.addAttr(main_ctrl, ln="geometryDisplayMode", at="enum", en="Normal:Template:Reference:", keyable=True)
    cmds.addAttr(main_ctrl, ln="controlsVisibility", at="bool", keyable=True)
    cmds.setAttr(main_ctrl + '.controlsVisibility', 1)
    cmds.setAttr(geometry_grp + '.overrideEnabled', 1)
    cmds.connectAttr(main_ctrl + '.geometryDisplayMode', geometry_grp + '.overrideDisplayType', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', direction_ctrl_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', left_arm_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', right_arm_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', left_leg_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', right_leg_switch_grp + '.v', f=True)
    
    # Moved the parenting of these systems after IK creation to solve pose issues
    cmds.parent(right_shoulder_ik_jnt, right_clavicle_switch_jnt)
    cmds.parent(left_shoulder_ik_jnt, left_clavicle_switch_jnt)
    
    # Delete Proxy
    cmds.delete(gt_ab_settings.get('main_proxy_grp'))
    
    # Add Notes
    note = 'This rig was created using ' + str(script_name) + '. (v' + str(script_version) + ')\n\nIssues, questions or suggestions? Go to:\ngithub.com/TrevisanGMW/gt-tools'
    add_node_note(main_ctrl, note)
    add_node_note(main_ctrl_grp, note)
    add_node_note(controls_grp, note)
    add_node_note(rig_grp, note)
    
    ################# Control Manip Default #################
    cmds.setAttr(main_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(direction_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(cog_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(hip_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(spine01_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(spine02_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(spine03_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(spine04_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(neck_base_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(neck_mid_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(head_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(jaw_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(main_eye_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(left_eye_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(right_eye_ctrl + '.showManipDefault', 1) # Translate
    
    ### Left Controls
    cmds.setAttr(left_hip_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_knee_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_ankle_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_ball_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_foot_ik_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(left_knee_ik_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(left_clavicle_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_shoulder_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_elbow_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_wrist_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(left_wrist_ik_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(left_elbow_ik_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(left_fingers_ctrl + '.showManipDefault', 2) # Rotate
    for finger in left_fingers_list:
        for ctrl_tuple in finger:
            for ctrl in ctrl_tuple:
                cmds.setAttr(ctrl + '.showManipDefault', 2) # Rotate
                
    ### Right Controls
    cmds.setAttr(right_hip_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_knee_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_ankle_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_ball_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_foot_ik_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(right_knee_ik_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(right_clavicle_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_shoulder_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_elbow_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_wrist_ctrl + '.showManipDefault', 2) # Rotate
    cmds.setAttr(right_wrist_ik_ctrl + '.showManipDefault', 6) # Smart
    cmds.setAttr(right_elbow_ik_ctrl + '.showManipDefault', 1) # Translate
    cmds.setAttr(right_fingers_ctrl + '.showManipDefault', 2) # Rotate
    for ctrl in right_fingers_list:
        for ctrl_tuple in finger:
            for ctrl in ctrl_tuple:
                cmds.setAttr(ctrl + '.showManipDefault', 2) # Rotate


    # Create Seamless FK/IK Switch References
    left_ankle_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_ankle_ik_reference') )[0]
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_ankle_ref_loc))
    cmds.parent(left_ankle_ref_loc, left_ankle_fk_jnt)
    cmds.setAttr(left_ankle_ref_loc + '.v', 0)
    
    left_knee_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_knee_ik_reference') )[0]
    cmds.delete(cmds.pointConstraint(left_knee_ik_ctrl, left_knee_ref_loc))
    cmds.parent(left_knee_ref_loc, left_knee_fk_jnt)
    cmds.setAttr(left_knee_ref_loc + '.v', 0)
    
    left_elbow_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('left_elbow_ik_reference') )[0]
    cmds.delete(cmds.pointConstraint(left_elbow_ik_ctrl, left_elbow_ref_loc))
    cmds.parent(left_elbow_ref_loc, left_elbow_fk_jnt)
    cmds.setAttr(left_elbow_ref_loc + '.v', 0)
  
    right_ankle_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_ankle_ik_reference') )[0]
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_ankle_ref_loc))
    cmds.parent(right_ankle_ref_loc, right_ankle_fk_jnt)
    cmds.setAttr(right_ankle_ref_loc + '.v', 0)
    
    right_knee_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_knee_ik_reference') )[0]
    cmds.delete(cmds.pointConstraint(right_knee_ik_ctrl, right_knee_ref_loc))
    cmds.parent(right_knee_ref_loc, right_knee_fk_jnt)
    cmds.setAttr(right_knee_ref_loc + '.v', 0)
    
    right_elbow_ref_loc = cmds.spaceLocator( name=gt_ab_settings_default.get('right_elbow_ik_reference') )[0]
    cmds.delete(cmds.pointConstraint(right_elbow_ik_ctrl, right_elbow_ref_loc))
    cmds.parent(right_elbow_ref_loc, right_elbow_fk_jnt)
    cmds.setAttr(right_elbow_ref_loc + '.v', 0)

    ################# Joint Labelling #################
    # cmds.addAttr(skeleton_grp, ln="skeletonOptions", at="enum", en="-------------:", keyable=True)
    # cmds.setAttr(skeleton_grp + '.skeletonOptions', lock=True)
    # cmds.addAttr(skeleton_grp, ln="labelVisibility", at="bool", keyable=True)
    # cmds.setAttr(skeleton_grp + '.labelVisibility', 1)
    #for jnt in gt_ab_joints:
        #cmds.connectAttr(skeleton_grp + '.labelVisibility', gt_ab_joints.get(jnt) + '.drawLabel', f=True)
        ##cmds.setAttr(gt_ab_joints.get(jnt) + '.drawLabel', 1)

    # Joint Side
    for obj in gt_ab_joints:
        if 'left_' in obj:
            cmds.setAttr(gt_ab_joints.get(obj) + '.side', 1) # 1 Left
        elif 'right_' in obj:
            cmds.setAttr(gt_ab_joints.get(obj) + '.side', 2) # 2 Right
        else:
            cmds.setAttr(gt_ab_joints.get(obj) + '.side', 0) # 0 Center
    
    
    # Joint Label
    cmds.setAttr(gt_ab_joints.get('main_jnt') + '.type', 18) # Other
    cmds.setAttr(gt_ab_joints.get('main_jnt') + '.otherType', 'Origin', type='string') # Other
    cmds.setAttr(gt_ab_joints.get('cog_jnt') + '.type', 1) # Root
    cmds.setAttr(gt_ab_joints.get('spine01_jnt') + '.type', 6) # Spine
    cmds.setAttr(gt_ab_joints.get('spine02_jnt') + '.type', 6) # Spine
    cmds.setAttr(gt_ab_joints.get('spine03_jnt') + '.type', 6) # Spine
    cmds.setAttr(gt_ab_joints.get('spine04_jnt') + '.type', 6) # Spine
    cmds.setAttr(gt_ab_joints.get('neck_base_jnt') + '.type', 7) # Neck
    cmds.setAttr(gt_ab_joints.get('neck_mid_jnt') + '.type', 7) # Neck
    cmds.setAttr(gt_ab_joints.get('head_jnt') + '.type', 8) # Head
    cmds.setAttr(gt_ab_joints.get('jaw_jnt') + '.type', 18) # Other
    cmds.setAttr(gt_ab_joints.get('jaw_jnt') + '.otherType', 'Jaw', type='string') # Other
    cmds.setAttr(gt_ab_joints.get('left_eye_jnt') + '.type', 18) # Other
    cmds.setAttr(gt_ab_joints.get('right_eye_jnt') + '.type', 18) # Other
    cmds.setAttr(gt_ab_joints.get('left_eye_jnt') + '.otherType', 'Eye', type='string') # Other
    cmds.setAttr(gt_ab_joints.get('right_eye_jnt') + '.otherType', 'Eye', type='string') # Other
    cmds.setAttr(gt_ab_joints.get('hip_jnt') + '.type', 2) # Hip
    cmds.setAttr(gt_ab_joints.get('left_hip_jnt') + '.type', 2) # Hip
    cmds.setAttr(gt_ab_joints.get('right_hip_jnt') + '.type', 2) # Hip
    cmds.setAttr(gt_ab_joints.get('left_knee_jnt') + '.type', 3) # Knee
    cmds.setAttr(gt_ab_joints.get('right_knee_jnt') + '.type', 3) # Knee
    cmds.setAttr(gt_ab_joints.get('left_ankle_jnt') + '.type', 4) # Foot
    cmds.setAttr(gt_ab_joints.get('right_ankle_jnt') + '.type', 4) # Foot
    cmds.setAttr(gt_ab_joints.get('left_ball_jnt') + '.type', 5) # Toe
    cmds.setAttr(gt_ab_joints.get('right_ball_jnt') + '.type', 5) # Toe
    cmds.setAttr(gt_ab_joints.get('left_clavicle_jnt') + '.type', 9) # Collar
    cmds.setAttr(gt_ab_joints.get('right_clavicle_jnt') + '.type', 9) # Collar
    cmds.setAttr(gt_ab_joints.get('left_shoulder_jnt') + '.type', 10) # Shoulder
    cmds.setAttr(gt_ab_joints.get('right_shoulder_jnt') + '.type', 10) # Shoulder
    cmds.setAttr(gt_ab_joints.get('left_elbow_jnt') + '.type', 11) # Elbow
    cmds.setAttr(gt_ab_joints.get('right_elbow_jnt') + '.type', 11) # Elbow
    cmds.setAttr(gt_ab_joints.get('left_wrist_jnt') + '.type', 12) # Elbow
    cmds.setAttr(gt_ab_joints.get('right_wrist_jnt') + '.type', 12) # Elbow
    cmds.setAttr(left_forearm_jnt + '.type', 18) # Other
    cmds.setAttr(right_forearm_jnt + '.type', 18) # Other
    cmds.setAttr(left_forearm_jnt + '.otherType', 'Forearm', type='string') # Other
    cmds.setAttr(right_forearm_jnt + '.otherType', 'Forearm', type='string') # Other
    # Left Fingers
    cmds.setAttr(gt_ab_joints.get('left_thumb01_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('left_thumb02_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('left_thumb03_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('left_index01_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('left_index02_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('left_index03_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('left_middle01_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('left_middle02_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('left_middle03_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('left_ring01_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('left_ring02_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('left_ring03_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('left_pinky01_jnt') + '.type', 22) # Pinky Finger
    cmds.setAttr(gt_ab_joints.get('left_pinky02_jnt') + '.type', 22) # Pinky Finger
    cmds.setAttr(gt_ab_joints.get('left_pinky03_jnt') + '.type', 22) # Pinky Finger
    # Right Fingers
    cmds.setAttr(gt_ab_joints.get('right_thumb01_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('right_thumb02_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('right_thumb03_jnt') + '.type', 14) # Thumb
    cmds.setAttr(gt_ab_joints.get('right_index01_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('right_index02_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('right_index03_jnt') + '.type', 19) # Index Finger
    cmds.setAttr(gt_ab_joints.get('right_middle01_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('right_middle02_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('right_middle03_jnt') + '.type', 20) # Middle Finger
    cmds.setAttr(gt_ab_joints.get('right_ring01_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('right_ring02_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('right_ring03_jnt') + '.type', 21) # Ring Finger
    cmds.setAttr(gt_ab_joints.get('right_pinky01_jnt') + '.type', 22) # Pinky Finger
    cmds.setAttr(gt_ab_joints.get('right_pinky02_jnt') + '.type', 22) # Pinky Finger
    cmds.setAttr(gt_ab_joints.get('right_pinky03_jnt') + '.type', 22) # Pinky Finger
    
    ################# Store Created Joints #################
    gt_ab_joints_default['left_forearm_jnt'] = left_forearm_jnt
    gt_ab_joints_default['right_forearm_jnt'] = right_forearm_jnt

    for obj in gt_ab_joints:
        gt_ab_joints_default[obj] = gt_ab_joints.get(obj)
    

    ################# Clean Selection & Print Feedback #################
    cmds.select(d=True)
    unique_message = '<' + str(random.random()) + '>'
    cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Control Rig</span><span style=\"color:#FFFFFF;\"> has been generated. Enjoy!</span>', pos='botLeft', fade=True, alpha=.9)
    


def select_skinning_joints():
    ''' Selects joints that should be used during the skinning process '''
    
    # Check for existing rig
    is_valid = True
    desired_elements = []
    for jnt in gt_ab_joints_default:
        desired_elements.append(gt_ab_joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. (Click on "Help" for more details)')
    
    if is_valid:
        skinning_joints = []
        for obj in gt_ab_joints_default:
            if '_end' + jnt_suffix.capitalize() not in gt_ab_joints_default.get(obj) and '_toe' not in gt_ab_joints_default.get(obj) and 'root_' not in gt_ab_joints_default.get(obj):
                skinning_joints.append(gt_ab_joints_default.get(obj))
        cmds.select(skinning_joints)
        if 'left_forearm_jnt' not in skinning_joints or 'right_forearm_jnt' not in skinning_joints:
            for obj in ['left_forearm_jnt', 'right_forearm_jnt']:
                try:
                    cmds.select(obj, add=True)
                except:
                    pass
                
def reset_proxy():
    ''' Resets proxy elements to their original position '''
    
    is_reset = False
    attributes_set_zero = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'followHip']
    attributes_set_one = ['sx', 'sy', 'sz', 'v']
    proxy_elements = []
    for proxy in gt_ab_settings_default:
        if '_crv' in proxy:
            proxy_elements.append(gt_ab_settings_default.get(proxy))
    for obj in proxy_elements:
        if cmds.objExists(obj):
            for attr in attributes_set_zero:
                try:
                    cmds.setAttr(obj + '.' + attr, 0)
                    is_reset = True
                except:
                    pass
            for attr in attributes_set_one:
                try:
                    cmds.setAttr(obj + '.' + attr, 1)
                    is_reset = True
                except:
                    pass
    
    if is_reset:
        unique_message = '<' + str(random.random()) + '>'
        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> was reset!</span>', pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.warning('No proxy found. Nothing was reset.')
        
def delete_proxy(suppress_warning=False):
    ''' 
    Deletes current proxy/guide curves 
    
            Parameters:
                suppress_warning (bool): Whether or not it should give warnings (feedback)
    
    '''
    
    is_deleted = False
    
    to_delete_elements = [gt_ab_settings.get('main_proxy_grp'), gt_ab_settings.get('main_crv') ]
    for obj in to_delete_elements:
        if cmds.objExists(obj) and is_deleted == False:
            cmds.delete(obj)
            is_deleted = True
            
    if not is_deleted:
        if not suppress_warning:
            cmds.warning('Proxy not found. Nothing was deleted.')
    else:
        unique_message = '<' + str(random.random()) + '>'
        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> was deleted!</span>', pos='botLeft', fade=True, alpha=.9)


def mirror_proxy(operation):
    ''' 
    Mirrors a pose on the proxy curves by copying translate, rotate and scale attributes from one side to the other
    
            Parameters:
                operation (string) : what direction to mirror. "left_to_right" (+X to -X) or "right_to_left" (-X to +X)
    
    '''
    
    def mirror_attr(source, target):
        ''' abc '''
        # Attr
        for attr in ['ty', 'tz', 'rx', 'sx', 'sy', 'sz']:
            source_attr = cmds.getAttr(source + '.' + attr)
            if not cmds.getAttr(target + '.' + attr, lock=True):
                cmds.setAttr(target + '.' + attr, source_attr)
        # Inverted Attr
        for attr in ['tx', 'ry', 'rz']:
            source_attr = cmds.getAttr(source + '.' + attr)
            if not cmds.getAttr(target + '.' + attr, lock=True):
                cmds.setAttr(target + '.' + attr, source_attr*-1)
    
    # Validate Proxy
    is_valid = True
    if not cmds.objExists(gt_ab_settings.get('main_proxy_grp')):
        is_valid = False
        cmds.warning('Proxy couldn\'t be found. Make sure you first create a proxy (guide objects) before mirroring it.')
    
    proxy_elements = [gt_ab_settings.get('main_proxy_grp')]
    for proxy in gt_ab_settings_default:
        if '_crv' in proxy:
            proxy_elements.append(gt_ab_settings.get(proxy))
    for obj in proxy_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.')
    
    # Lists
    left_elements = []
    right_elements = []
    
    if is_valid:
        for obj in gt_ab_settings:
            if obj.startswith('left_') and '_crv' in obj:
                left_elements.append(gt_ab_settings.get(obj))
            elif obj.startswith('right_') and '_crv' in obj:
                right_elements.append(gt_ab_settings.get(obj))
        
        for left_obj in left_elements:
            for right_obj in right_elements:
                if left_obj.replace('left','') == right_obj.replace('right', ''):
                    
                    if operation == 'left_to_right':
                        mirror_attr(left_obj, right_obj)
                     
                    elif operation == 'right_to_left':
                        mirror_attr(right_obj, left_obj)
                     
        if operation == 'left_to_right':
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> mirrored from left to right. (+X to -X)</span>', pos='botLeft', fade=True, alpha=.9)

        elif operation == 'right_to_left':
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> mirrored from right to left. (-X to +X)</span>', pos='botLeft', fade=True, alpha=.9)

def export_proxy_pose():
    ''' Exports a JSON file containing the translate, rotate and scale data from every proxy curve (used to export a pose) ''' 
    
    file_name = cmds.fileDialog2(fileFilter=script_name + " - JSON File (*.json)", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Proxy Pose for "' + script_name + '"') or []
    
    successfully_created_file = False
    if len(file_name) > 0:
        pose_file = file_name[0]
        successfully_created_file = True

    if successfully_created_file:
        
        export_dict = {'gt_auto_biped_version' : script_version}
        
        # Validate Proxy
        is_valid = True

        proxy_elements = [gt_ab_settings.get('main_proxy_grp')]
        for proxy in gt_ab_settings_default:
            if '_crv' in proxy:
                proxy_elements.append(gt_ab_settings.get(proxy))
        for obj in proxy_elements:
            if not cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.')

        if is_valid:
            for obj in gt_ab_settings_default:
                if '_crv' in obj:
                    translate = cmds.getAttr(gt_ab_settings_default.get(obj) + '.translate')
                    rotate = cmds.getAttr(gt_ab_settings_default.get(obj) + '.rotate')
                    scale = cmds.getAttr(gt_ab_settings_default.get(obj) + '.scale')
                    to_save = [gt_ab_settings_default.get(obj), translate[0], rotate[0], scale[0]]
                    export_dict[obj] = to_save
        
            try: 
                with open(pose_file, 'w') as outfile:
                    json.dump(export_dict, outfile, indent=4)

                unique_message = '<' + str(random.random()) + '>'
                cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy Pose</span><span style=\"color:#FFFFFF;\"> exported.</span>', pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write('Pose exported to the file "' + pose_file + '".')
            except Exception as e:
                print (e)
                successfully_created_file = False
                cmds.warning('Couldn\'t write to file. Please make sure the saving location is accessible.')


def import_proxy_pose():
    ''' 
    Imports a JSON file containing the translate, rotate and scale data for every proxy curve (exported using the "export_proxy_pose" function)
    Uses the imported data to set the translate, rotate and scale position of every proxy curve
    Uses the function "delete_proxy()" to recreate it if necessary
    
    ''' 
    def set_unlocked_attr(target, attr, value):
        ''' 
        Sets an attribute to the provided value in case it's not locked
        
                Parameters:
                    target (string): Name of the target object (object that will receive transforms)
                    attr (string): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
                    value (float): Value used to set attribute. e.g. 1.5, 2, 5...
        
        '''
        if not cmds.getAttr(target + '.' + attr, lock=True):
            cmds.setAttr(target + '.' + attr, value)
                                
    file_name = cmds.fileDialog2(fileFilter=script_name + " - JSON File (*.json)", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for "' + script_name + '"') or []
    
    if len(file_name) > 0:
        pose_file = file_name[0]
        file_exists = True
    else:
        file_exists = False
    
    if file_exists:
        try: 
            with open(pose_file) as json_file:
                data = json.load(json_file)
                try:
                    is_valid_file = True
                    if not data.get('gt_auto_biped_version'):
                        is_valid_file = False
                        cmds.warning('Imported file doesn\'t seem to be compatible or is missing data.')
                    
                    is_valid_scene = True
                    # Check for existing rig or conflicting names
                    undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
                    for jnt in gt_ab_joints_default:
                        undesired_elements.append(gt_ab_joints_default.get(jnt))
                    for obj in undesired_elements:
                        if cmds.objExists(obj) and is_valid_scene:
                            is_valid_scene = False
                            cmds.warning('"' + obj + '" found in the scene. This means that you either already created a rig or you have conflicting names on your objects. (Click on "Help" for more details)')
                    
                    if is_valid_scene:
                        # Check for Proxy
                        proxy_exists = True

                        proxy_elements = []
                        for proxy in gt_ab_settings_default:
                            if '_crv' in proxy:
                                proxy_elements.append(gt_ab_settings.get(proxy))
                        for obj in proxy_elements:
                            if not cmds.objExists(obj) and proxy_exists:
                                proxy_exists = False
                                delete_proxy(True)
                                validate_operation('create_proxy')
                                cmds.warning('Current proxy was missing elements, a new one was created.')
                    
                    
                    if is_valid_file and is_valid_scene:
                        for proxy in data:
                            if proxy != 'gt_auto_biped_version':
                                curent_object = data.get(proxy) # Name, T, R, S
                                if cmds.objExists(curent_object[0]):
                                    set_unlocked_attr(curent_object[0], 'tx', curent_object[1][0])
                                    set_unlocked_attr(curent_object[0], 'ty', curent_object[1][1])
                                    set_unlocked_attr(curent_object[0], 'tz', curent_object[1][2])
                                    set_unlocked_attr(curent_object[0], 'rx', curent_object[2][0])
                                    set_unlocked_attr(curent_object[0], 'ry', curent_object[2][1])
                                    set_unlocked_attr(curent_object[0], 'rz', curent_object[2][2])
                                    try:
                                        set_unlocked_attr(curent_object[0], 'sx', curent_object[3][0])
                                    except:
                                        pass
                                    try:
                                        set_unlocked_attr(curent_object[0], 'sy', curent_object[3][1])
                                    except:
                                        pass
                                    try:
                                        set_unlocked_attr(curent_object[0], 'sz', curent_object[3][2])
                                    except:
                                        pass
                        unique_message = '<' + str(random.random()) + '>'
                        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy Pose</span><span style=\"color:#FFFFFF;\"> imported!</span>', pos='botLeft', fade=True, alpha=.9)
                        sys.stdout.write('Pose imported from the file "' + pose_file + '".')

                except Exception as e:
                    cmds.warning('An error occured when importing the pose. Make sure you imported the correct JSON file. (Click on "Help" for more info)')
        except:
            file_exists = False
            cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')
    

def gt_ab_define_humanik(character_name):
    '''
    Auto creates a character definition for GT Auto Biped. (It overwrites any definition with the same name)
    
            Parameters:
                character_name (string): Name of the HIK character
    
    '''
    is_operation_valid = True

    # Check for existing rig
    desired_elements = []
    for jnt in gt_ab_joints_default:
        desired_elements.append(gt_ab_joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_operation_valid:
            is_operation_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. (Click on "Help" for more details)')
    
    # Source HIK Modules
    if is_operation_valid:
        try:
            # Source HIK scripts
            MAYA_LOCATION = os.environ['MAYA_LOCATION']
            mel.eval('source "'+ MAYA_LOCATION + '/scripts/others/hikGlobalUtils.mel"')
            mel.eval('source "'+ MAYA_LOCATION + '/scripts/others/hikCharacterControlsUI.mel"')
            mel.eval('source "'+ MAYA_LOCATION + '/scripts/others/hikDefinitionOperations.mel"')
        except:
            print('#' * 80)
            if not os.path.exists(MAYA_LOCATION + '/scripts/others/hikGlobalUtils.mel'):
                print('The module "' + MAYA_LOCATION + '/scripts/others/hikGlobalUtils.mel" couldn\'t be found.')
            if not os.path.exists(MAYA_LOCATION + '/scripts/others/hikCharacterControlsUI.mel'):
                print('The module "' + MAYA_LOCATION + '/scripts/others/hikCharacterControlsUI.mel" couldn\'t be found.')
            if not os.path.exists(MAYA_LOCATION + '/scripts/others/hikDefinitionOperations.mel'):
                print('The module "' + MAYA_LOCATION + '/scripts/others/hikDefinitionOperations.mel" couldn\'t be found.')
            print('#' * 80)
            cmds.warning('HumanIK modules couldn\'t be found. You might have to define the character manually. Open script editor for more information.')
            is_operation_valid = False

    # Create Character Definition
    if is_operation_valid:
        try:
            mel.eval('catchQuiet(deleteCharacter("' + character_name + '"))')
            mel.eval('hikCreateCharacter("' + character_name + '")')

            # Add joints to Definition.
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('main_jnt') + '", "' + character_name + '", 0,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('hip_jnt') + '", "' + character_name + '", 1,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_hip_jnt') + '", "' + character_name + '", 2,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_knee_jnt') + '", "' + character_name + '", 3,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_ankle_jnt') + '", "' + character_name + '", 4,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_hip_jnt') + '", "' + character_name + '", 5,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_knee_jnt') + '", "' + character_name + '", 6,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_ankle_jnt') + '", "' + character_name + '", 7,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('cog_jnt') + '", "' + character_name + '", 8,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_shoulder_jnt') + '", "' + character_name + '", 9,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_elbow_jnt') + '", "' + character_name + '", 10,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_wrist_jnt') + '", "' + character_name + '", 11,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_shoulder_jnt') + '", "' + character_name + '", 12,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_elbow_jnt') + '", "' + character_name + '", 13,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_wrist_jnt') + '", "' + character_name + '", 14,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('head_jnt') + '", "' + character_name + '", 15,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_ball_jnt') + '", "' + character_name + '", 16,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_ball_jnt') + '", "' + character_name + '", 17,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_clavicle_jnt') + '", "' + character_name + '", 18,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_clavicle_jnt') + '", "' + character_name + '", 19,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('neck_base_jnt') + '", "' + character_name + '", 20,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('neck_mid_jnt') + '", "' + character_name + '", 32,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('spine01_jnt') + '", "' + character_name + '", 23,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('spine02_jnt') + '", "' + character_name + '", 24,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('spine03_jnt') + '", "' + character_name + '", 25,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('spine04_jnt') + '", "' + character_name + '", 26,0);')
            
            # Fingers
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_thumb01_jnt') + '", "' + character_name + '", 50,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_thumb02_jnt') + '", "' + character_name + '", 51,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_thumb03_jnt') + '", "' + character_name + '", 52,0);')
        
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_index01_jnt') + '", "' + character_name + '", 54,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_index02_jnt') + '", "' + character_name + '", 55,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_index03_jnt') + '", "' + character_name + '", 56,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_middle01_jnt') + '", "' + character_name + '", 58,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_middle02_jnt') + '", "' + character_name + '", 59,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_middle03_jnt') + '", "' + character_name + '", 60,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_ring01_jnt') + '", "' + character_name + '", 62,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_ring02_jnt') + '", "' + character_name + '", 63,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_ring03_jnt') + '", "' + character_name + '", 64,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_pinky01_jnt') + '", "' + character_name + '", 66,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_pinky02_jnt') + '", "' + character_name + '", 67,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_pinky03_jnt') + '", "' + character_name + '", 68,0);')

            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_thumb01_jnt') + '", "' + character_name + '", 74,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_thumb02_jnt') + '", "' + character_name + '", 75,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_thumb03_jnt') + '", "' + character_name + '", 76,0);')
        
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_index01_jnt') + '", "' + character_name + '", 78,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_index02_jnt') + '", "' + character_name + '", 79,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_index03_jnt') + '", "' + character_name + '", 80,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_middle01_jnt') + '", "' + character_name + '", 82,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_middle02_jnt') + '", "' + character_name + '", 83,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_middle03_jnt') + '", "' + character_name + '", 84,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_ring01_jnt') + '", "' + character_name + '", 86,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_ring02_jnt') + '", "' + character_name + '", 87,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_ring03_jnt') + '", "' + character_name + '", 88,0);')
            
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_pinky01_jnt') + '", "' + character_name + '", 90,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_pinky02_jnt') + '", "' + character_name + '", 91,0);')
            mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_pinky03_jnt') + '", "' + character_name + '", 92,0);')
            
            try:
                mel.eval('setCharacterObject("' + gt_ab_joints_default.get('left_forearm_jnt') + '", "' + character_name + '", 193,0);')
                mel.eval('setCharacterObject("' + gt_ab_joints_default.get('right_forearm_jnt') + '", "' + character_name + '", 195,0);')
            except:
               pass

            mel.eval('hikUpdateDefinitionUI;')
            mel.eval('hikToggleLockDefinition();')
            
            cmds.select(d=True)
            
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">HumanIK</span><span style=\"color:#FFFFFF;\"> character and definition created!</span>', pos='botLeft', fade=True, alpha=.9)

        except:
            cmds.warning('An error happened when creating the definition. You might have to assign your joints manually.')

def gtu_uniform_jnt_label_toggle():
    ''' 
    Makes the visibility of the Joint Labels uniform according to the current state of the majority of them.  
    '''

    function_name = 'GTU Uniform Joint Label Toggle'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        errors = ''
        joints = cmds.ls(type='joint', long=True)
        
        inactive_label = []
        active_label = []
        
        for obj in joints:
            try:
                current_label_state = cmds.getAttr(obj + '.drawLabel')
                if current_label_state:
                    active_label.append(obj)
                else:
                    inactive_label.append(obj)
            except Exception as e:
                errors += str(e) + '\n'
           
        if len(active_label) == 0:
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(inactive_label) == 0:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(active_label) > len(inactive_label):
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        else:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        

        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('The script couldn\'t read or write some "drawLabel" states. Open script editor for more info.')
    except:
        pass
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def create_shelf_button(command, 
                        label='',
                        name=None, 
                        tooltip='',
                        image=None, # Default Python Icon
                        label_color=(1, 0, 0), # Default Red
                        label_bgc_color=(0, 0, 0, 1), # Default Black
                        bgc_color=None
                        ):
    '''
    Add a shelf button to the current shelf (according to the provided parameters)
    
            Parameters:
                command (str): A string containing the code or command you want the button to run when clicking on it. E.g. "print("Hello World")"
                label (str): The label of the button. This is the text you see below it.
                name (str): The name of the button as seen inside the shelf editor.
                tooltip (str): The help message you get when hovering the button.
                image (str): The image used for the button (defaults to Python icon if none)
                label_color (tuple): A tuple containing three floats, these are RGB 0 to 1 values to determine the color of the label.
                label_bgc_color (tuple): A tuple containing four floats, these are RGBA 0 to 1 values to determine the background of the label.
                bgc_color (tuple):  A tuple containing three floats, these are RGB 0 to 1 values to determine the background of the icon
    
    '''
    maya_version = cmds.about(v=True)
    
    shelf_top_level = mel.eval('$temp=$gShelfTopLevel')
    if not cmds.tabLayout(shelf_top_level, exists=True):
        cmds.warning('Shelf is not visible')
        return

    if not image:
        image = 'pythonFamily.png'

    shelf_tab = cmds.shelfTabLayout(shelf_top_level, query=True, selectTab=True)
    shelf_tab = shelf_top_level + '|' + shelf_tab

    # Populate extra arguments according to the current Maya version
    kwargs = {}
    if maya_version >= 2009:
        kwargs['commandRepeatable'] = True
    if maya_version >= 2011:
        kwargs['overlayLabelColor'] = label_color
        kwargs['overlayLabelBackColor'] = label_bgc_color
        if bgc_color:
            kwargs['enableBackground'] = bool(bgc_color)
            kwargs['backgroundColor'] = bgc_color

    return cmds.shelfButton(parent=shelf_tab, label=label, command=command,
                          imageOverlayLabel=label, image=image, annotation=tooltip,
                          width=32, height=32, align='center', **kwargs) 


def add_seamless_fkik_button():
    ''' 
    Create a button for a seamless FK/IK swticher
    
    '''
    create_shelf_button("\"\"\"\n Seamless IK/FK Switch for GT Auto Biped Rigger.\n @Guilherme Trevisan - TrevisanGMW@gmail.com - 2021-01-05\n github.com/TrevisanGMW/gt-tools\n\n 1.0 - 2021-01-05\n Initial Release\n\n\"\"\"\ntry:\n    from shiboken2 import wrapInstance\nexcept ImportError:\n    from shiboken import wrapInstance\n    \ntry:\n    from PySide2.QtGui import QIcon\n    from PySide2.QtWidgets import QWidget\nexcept ImportError:\n    from PySide.QtGui import QIcon, QWidget\n\nfrom maya import OpenMayaUI as omui\nimport maya.cmds as cmds\n\n\n\n# Script Name\nscript_name = \"GT - Seamless FK/IK Switcher\"\n\n# Version:\nscript_version = \"1.0\";\n\n# Settings\nleft_arm_seamless_dict = { 'switch_ctrl' : 'left_arm_switch_ctrl', # Switch Ctrl\n                           'end_ik_ctrl' : 'left_wrist_ik_ctrl', # IK Elements\n                           'pvec_ik_ctrl' : 'left_elbow_ik_ctrl',\n                           'base_ik_jnt' :  'left_shoulder_ik_jnt',\n                           'mid_ik_jnt' : 'left_elbow_ik_jnt',\n                           'end_ik_jnt' : 'left_wrist_ik_jnt',\n                           'base_fk_ctrl' : 'left_shoulder_ctrl', # FK Elements\n                           'mid_fk_ctrl' : 'left_elbow_ctrl',\n                           'end_fk_ctrl' : 'left_wrist_ctrl' ,\n                           'base_fk_jnt' :  'left_shoulder_fk_jnt',\n                           'mid_fk_jnt' : 'left_elbow_fk_jnt',\n                           'end_fk_jnt' : 'left_wrist_fk_jnt',\n                           'mid_ik_reference' : 'left_elbowSwitch_loc',\n                           'end_ik_reference' : ''\n                         }\n\nright_arm_seamless_dict = { 'switch_ctrl' : 'right_arm_switch_ctrl', # Switch Ctrl\n                            'end_ik_ctrl' : 'right_wrist_ik_ctrl', # IK Elements\n                            'pvec_ik_ctrl' : 'right_elbow_ik_ctrl',\n                            'base_ik_jnt' :  'right_shoulder_ik_jnt',\n                            'mid_ik_jnt' : 'right_elbow_ik_jnt',\n                            'end_ik_jnt' : 'right_wrist_ik_jnt',\n                            'base_fk_ctrl' : 'right_shoulder_ctrl', # FK Elements\n                            'mid_fk_ctrl' : 'right_elbow_ctrl',\n                            'end_fk_ctrl' : 'right_wrist_ctrl' ,\n                            'base_fk_jnt' :  'right_shoulder_fk_jnt',\n                            'mid_fk_jnt' : 'right_elbow_fk_jnt',\n                            'end_fk_jnt' : 'right_wrist_fk_jnt',\n                            'mid_ik_reference' : 'right_elbowSwitch_loc',\n                            'end_ik_reference' : ''\n                           }\n                            \nleft_leg_seamless_dict = { 'switch_ctrl' : 'left_leg_switch_ctrl', # Switch Ctrl\n                           'end_ik_ctrl' : 'left_foot_ik_ctrl', # IK Elements\n                           'pvec_ik_ctrl' : 'left_knee_ik_ctrl',\n                           'base_ik_jnt' :  'left_hip_ik_jnt',\n                           'mid_ik_jnt' : 'left_knee_ik_jnt',\n                           'end_ik_jnt' : 'left_ankle_ik_jnt',\n                           'base_fk_ctrl' : 'left_hip_ctrl', # FK Elements\n                           'mid_fk_ctrl' : 'left_knee_ctrl',\n                           'end_fk_ctrl' : 'left_ankle_ctrl' ,\n                           'base_fk_jnt' :  'left_hip_fk_jnt',\n                           'mid_fk_jnt' : 'left_knee_fk_jnt',\n                           'end_fk_jnt' : 'left_ankle_fk_jnt',\n                           'mid_ik_reference' : 'left_kneeSwitch_loc',\n                           'end_ik_reference' : 'left_ankleSwitch_loc'\n                          }\n                           \nright_leg_seamless_dict = { 'switch_ctrl' : 'right_leg_switch_ctrl', # Switch Ctrl\n                            'end_ik_ctrl' : 'right_foot_ik_ctrl', # IK Elements\n                            'pvec_ik_ctrl' : 'right_knee_ik_ctrl',\n                            'base_ik_jnt' :  'right_hip_ik_jnt',\n                            'mid_ik_jnt' : 'right_knee_ik_jnt',\n                            'end_ik_jnt' : 'right_ankle_ik_jnt',\n                            'base_fk_ctrl' : 'right_hip_ctrl', # FK Elements\n                            'mid_fk_ctrl' : 'right_knee_ctrl',\n                            'end_fk_ctrl' : 'right_ankle_ctrl' ,\n                            'base_fk_jnt' :  'right_hip_fk_jnt',\n                            'mid_fk_jnt' : 'right_knee_fk_jnt',\n                            'end_fk_jnt' : 'right_ankle_fk_jnt',\n                            'mid_ik_reference' : 'right_kneeSwitch_loc',\n                            'end_ik_reference' : 'right_ankleSwitch_loc'\n                          }\n\n# Main Form ============================================================================\ndef build_gui_seamless_ab_fk_ik():\n    window_name = \"build_gui_seamless_ab_fk_ik\"\n    if cmds.window(window_name, exists =True):\n        cmds.deleteUI(window_name)    \n\n    # Main GUI Start Here =================================================================================\n    \n    # Build UI\n    build_gui_seamless_ab_fk_ik = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\\\n                          titleBar=True, mnb=False, mxb=False, sizeable =True)\n\n    cmds.window(window_name, e=True, s=True, wh=[1,1])\n\n    content_main = cmds.columnLayout(adj = True)\n\n    # Title Text\n    title_bgc_color = (.4, .4, .4)\n    cmds.separator(h=10, style='none') # Empty Space\n    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment\n    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column\n    cmds.text(\" \", bgc=title_bgc_color) # Tiny Empty Green Space\n    cmds.text(script_name, bgc=title_bgc_color,  fn=\"boldLabelFont\", align=\"left\")\n    cmds.button( l =\"Help\", bgc=title_bgc_color, c=lambda x:open_gt_tools_documentation())\n    cmds.separator(h=5, style='none') # Empty Space\n    \n    # Body ====================\n    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)\n    \n    \n    cmds.text('Namespace:')\n    namespace_txt = cmds.textField(text='', pht='Namespace:: (Optional)')\n    \n \n    \n    cmds.separator(h=10, style='none') # Empty Space\n    \n    btn_margin = 5\n    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)\n    cmds.text('Right Arm:') #R\n    cmds.text('Left Arm:') #L\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.button(l =\"Toggle\", c=lambda x:gt_ab_seamless_fk_ik_toggle(right_arm_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"Toggle\", c=lambda x:gt_ab_seamless_fk_ik_toggle(left_arm_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    cmds.button(l =\"FK to IK\", c=lambda x:gt_ab_seamless_fk_ik_switch(right_arm_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"FK to IK\", c=lambda x:gt_ab_seamless_fk_ik_switch(left_arm_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    cmds.button(l =\"IK to FK\", c=lambda x:gt_ab_seamless_fk_ik_switch(right_arm_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"IK to FK\", c=lambda x:gt_ab_seamless_fk_ik_switch(left_arm_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    \n    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)\n    cmds.text('Right Leg:') #R\n    cmds.text('Left Leg:') #L\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.separator(h=btn_margin, style='none') # Empty Space\n    cmds.button(l =\"Toggle\", c=lambda x:gt_ab_seamless_fk_ik_toggle(right_leg_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"Toggle\", c=lambda x:gt_ab_seamless_fk_ik_toggle(left_leg_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    cmds.button(l =\"FK to IK\", c=lambda x:gt_ab_seamless_fk_ik_switch(right_leg_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"FK to IK\", c=lambda x:gt_ab_seamless_fk_ik_switch(left_leg_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    cmds.button(l =\"IK to FK\", c=lambda x:gt_ab_seamless_fk_ik_switch(right_leg_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #R\n    cmds.button(l =\"IK to FK\", c=lambda x:gt_ab_seamless_fk_ik_switch(left_leg_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)), w=130) #L\n    \n    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)\n\n                                                                                               \n    cmds.separator(h=10, style='none') # Empty Space\n    \n    # Show and Lock Window\n    cmds.showWindow(build_gui_seamless_ab_fk_ik)\n    cmds.window(window_name, e=True, s=False)\n    \n    # Set Window Icon\n    qw = omui.MQtUtil.findWindow(window_name)\n    widget = wrapInstance(long(qw), QWidget)\n    icon = QIcon(':/ikSCsolver.svg')\n    widget.setWindowIcon(icon)\n\n    # Remove the focus from the textfield and give it to the window\n    cmds.setFocus(window_name)\n\n    # Main GUI Ends Here =================================================================================\n    \n    \n    def object_load_handler(operation):\n        ''' \n        Function to handle load buttons. It updates the UI to reflect the loaded data.\n        \n                Parameters:\n                    operation (str): String to determine function (Currently either \"ik_handle\" or \"attr_holder\")\n        \n        '''\n\n        # Check If Selection is Valid\n        received_valid_element = False\n        \n        # ikHandle\n        if operation == 'ik_handle':\n            current_selection = cmds.ls(selection=True, type='ikHandle')\n            \n            if len(current_selection) == 0:\n                cmds.warning(\"Nothing selected. Please select an ikHandle and try again.\")\n            elif len(current_selection) > 1:\n                cmds.warning(\"You selected more than one ikHandle! Please select only one\")\n            elif cmds.objectType(current_selection[0]) == \"ikHandle\":\n                gt_make_ik_stretchy_settings['ik_handle'] = current_selection[0]\n                received_valid_element = True\n            else:\n                cmds.warning(\"Something went wrong, make sure you selected just one ikHandle and try again.\")\n            \n            # ikHandle Update GUI\n            if received_valid_element:\n                cmds.button(ik_handle_status, l=gt_make_ik_stretchy_settings.get('ik_handle'), e=True, bgc=(.6, .8, .6), w=130)\n            else:\n                cmds.button(ik_handle_status, l =\"Failed to Load\", e=True, bgc=(1, .4, .4), w=130)\n           \n        # Attr Holder\n        if operation == 'attr_holder':\n            current_selection = cmds.ls(selection=True)\n            if len(current_selection) == 0:\n                cmds.warning(\"Nothing selected. Assuming you don\\'t want an attribute holder. To select an attribute holder, select only one object (usually a control curve) and try again.\")\n                gt_make_ik_stretchy_settings['attr_holder'] = ''\n            elif len(current_selection) > 1:\n                cmds.warning(\"You selected more than one object! Please select only one\")\n            elif cmds.objExists(current_selection[0]):\n                gt_make_ik_stretchy_settings['attr_holder'] = current_selection[0]\n                received_valid_element = True\n            else:\n                cmds.warning(\"Something went wrong, make sure you selected just one object and try again.\")\n                \n            # Attr Holder Update GUI\n            if received_valid_element:\n                cmds.button(attr_holder_status, l=gt_make_ik_stretchy_settings.get('attr_holder'), e=True, bgc=(.6, .8, .6), w=130)\n            else:\n                cmds.button(attr_holder_status, l =\"Not provided\", e=True, bgc=(.2, .2, .2), w=130)\n        \n    def validate_operation():\n        ''' Checks elements one last time before running the script '''\n        \n        is_valid = False\n        stretchy_name = None\n        attr_holder = None\n        \n        stretchy_prefix = cmds.textField(stretchy_system_prefix, q=True, text=True).replace(' ','')\n        \n        # Name\n        if stretchy_prefix != '':\n            stretchy_name = stretchy_prefix\n\n        # ikHandle\n        if gt_make_ik_stretchy_settings.get('ik_handle') == '':\n            cmds.warning('Please load an ikHandle first before running the script.')\n            is_valid = False\n        else:\n            if cmds.objExists(gt_make_ik_stretchy_settings.get('ik_handle')):\n                is_valid = True\n            else:\n                cmds.warning('\"' + str(gt_make_ik_stretchy_settings.get('ik_handle')) + '\" couldn\\'t be located. Make sure you didn\\'t rename or deleted the object after loading it')\n            \n        # Attribute Holder\n        if is_valid:\n            if gt_make_ik_stretchy_settings.get('attr_holder') != '':\n                if cmds.objExists(gt_make_ik_stretchy_settings.get('attr_holder')):\n                    attr_holder = gt_make_ik_stretchy_settings.get('attr_holder')\n                else:\n                    cmds.warning('\"' + str(gt_make_ik_stretchy_settings.get('attr_holder')) + '\" couldn\\'t be located. Make sure you didn\\'t rename or deleted the object after loading it. A simpler version of the stretchy system was created.')\n            else:\n                sys.stdout.write('An attribute holder was not provided. A simpler version of the stretchy system was created.')\n            \n        # Run Script\n        if is_valid:\n            if stretchy_name:\n                make_stretchy_ik(gt_make_ik_stretchy_settings.get('ik_handle'), stretchy_name=stretchy_name, attribute_holder=attr_holder)\n            else:\n                make_stretchy_ik(gt_make_ik_stretchy_settings.get('ik_handle'), stretchy_name='temp', attribute_holder=attr_holder)\n\n\ndef gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=''):\n    '''\n    Transfer the position of the FK to IK or IK to FK systems in a seamless way, so the animator can easily switch between one and the other\n    \n            Parameters:\n                ik_fk_ns_dict (dict): A dicitionary containg the elements that are part of the system you want to switch\n                direction (string): Either \"fk_to_ik\" or \"ik_to_fk\". It determines what is the source and what is the target.\n                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.\n    '''\n    ik_fk_ns_dict = {}\n    for obj in ik_fk_dict:\n        ik_fk_ns_dict[obj] = namespace + ik_fk_dict.get(obj)\n    \n    \n    fk_pairs = [[ik_fk_ns_dict.get('base_ik_jnt'), ik_fk_ns_dict.get('base_fk_ctrl')],\n                [ik_fk_ns_dict.get('mid_ik_jnt'), ik_fk_ns_dict.get('mid_fk_ctrl')],\n                [ik_fk_ns_dict.get('end_ik_jnt'), ik_fk_ns_dict.get('end_fk_ctrl')]]            \n                \n    if direction == 'fk_to_ik':\n\n        if ik_fk_dict.get('end_ik_reference') != '':\n            cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_ik_reference'), pos=1, rot=1)\n        else:\n            cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_fk_jnt'), pos=1, rot=1)\n        \n        cmds.matchTransform(ik_fk_ns_dict.get('pvec_ik_ctrl'), ik_fk_ns_dict.get('mid_ik_reference'), pos=1, rot=1)\n        cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 1)\n    if direction == 'ik_to_fk':\n        for pair in fk_pairs:\n            cmds.matchTransform(pair[1], pair[0], pos=1, rot=1)\n        cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 0)\n   \ndef open_gt_tools_documentation():\n    ''' Opens a web browser with the latest release '''\n    cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/tree/master/docs#-gt-auto-biped-rigger-', absolute=True) \n    \ndef gt_ab_seamless_fk_ik_toggle(ik_fk_dict, namespace=''):\n    ''' Calls gt_ab_seamless_fk_ik_switch, but toggles between fk and ik '''\n    current_system = cmds.getAttr(namespace + ik_fk_dict.get('switch_ctrl') + '.influenceSwitch')\n    if current_system < 0.5:\n        gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=namespace)\n    else:\n        gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='ik_to_fk', namespace=namespace)\n\n\n#Build UI\nif __name__ == '__main__':\n    build_gui_seamless_ab_fk_ik()",
               label='FKIK', tooltip='This button opens the FKIK Switcher for GT Auto Biped Rigger.', image='openScript.png')
    cmds.inViewMessage(amg='<span style=\"color:#FFFF00;\">FK/IK Switcher</span> button was added to your current shelf.', pos='botLeft', fade=True, alpha=.9)
        
        
# Build UI
if __name__ == '__main__':
    build_gui_auto_biped_rig()