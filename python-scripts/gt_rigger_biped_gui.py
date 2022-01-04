"""
 GT Biped Rigger GUI
 github.com/TrevisanGMW - 2020-12-08

 1.0 - 2020-12-29
 Initial Release
 
 1.1 - 2021-01-03
 Renamed shapes
 Added joint labelling
 Added icons to buttons
 Added curves (lines) between proxies
 Changed and added a few notes
 Added manip default to all main controls
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
 
 1.3 - 2021-01-19
 Updated help window to better accommodate a high volume of text
 Added new utility to extract proxy pose from generated rig
 Updated export/import functions to be compatible with worldspace
 Added version check to importer for backwards compatibility
 Added auto load for HumanIK plugin in case it's not loaded when attaching rig
 Patched a few small bugs, added colors to a few controls and updated the help text
 Changed forearm joints hierarchy so the rig can be easily exported in to game engines
 Moved the mechanics of the roll joints into the rig setup folder
 Updated the order of the groups inside the rig setup folder
 Addded joint inflation/deflation system
 Switch the order and name of a few custom attributes (none of the keyable ones)
 Switch the order of a few custom attributes (influenceSwitch was moved up)
 Added activation attribute to the main control for the joint inflation/deflation system
 Added counter rotation system to neckMid control so the shape stays in place when automated
 Fixed an issue where the right thumb wouldn't orient corrently
 Added finger abduction/adduction control and updated the name of a few attributes
    
 1.4 - 2021-01-25
 Created auto breathing system
 Added check for geometry group (common name)
 Updated "orient_to_target" function to enforce proxy direction properly
 Added manip default to the foot roll controls
 Fixed an issue where you wouldn't be able to import a JSON file for the beta versions
 Added negative rotation to adduction for more flexibility
 Added auto knuckle compression system (Translation Z Offset)
 Changed the data transfer type of the wrists from parentConstraint to raw to prevent flipping
 Created sin function without expressions
 Created a trigonometry sine function that doesn't use third-party plugins or expressions
 Added debugging option to auto import proxy templates and auto bind geometry
 Added a check for required plugins before running the script
 Changed the data transfer type of the clavicles to allow for offsets (for auto breathing)
 Added notes to the knee proxies (similar to elbows)
 
 1.5 - 2021-01-26
 Changed the names of a few nodes
 Updated the entire forearm and wrist joints system as they would sometimes flip
 Added attribute to head control to determine the visibility of the eye controls
 Updated right forearm connections so it goes into the correct direction
 Fixed undesired offset inherited from a broken node inside the auto breathing system
 Fixed an issue where the shape of some controls would stay opened
 Updated most curves to be created as periodic curves to avoid creation issues
 Fixed the direction of the right side FK/IK switch shapes
 
 1.6 - 2021-01-28
 Fixed an issue where the fingers would still move even when the stretchy system was deactivated
 Fixed another issue where the wrist joints would flip flipping 
 Fixed issue where the spine controls would look locked when moving the cog control
 
 1.7 - 2021-02-05
 Fixed issue where the ik shoulders would sometimes flip during a main control rotation
 Unlocked translate Z for hip proxies
 
 1.7.1 - 2021-02-14
 Fixed issue where "right_forearm_jnt" would rotate to the wrong direction
 
 1.7.2 - 2021-05-10
 Made script compatible with Python 3 (Maya 2022+)
 
 1.7.3 - 2021-08-07
 Fixed an issue where the foot would sometimes be flipped when the angle of the leg is not perfectly straight (
 Enforce footToe ikHandle position)

 1.7.4 - 2021-10-10
 Fixed an issue where the rig would start flickering when following motion capture using a custom rig setup (HumanIK)
 Modified inflation/deflation system to use controls instead of inverseMatrix nodes (less convenient, but more robust)
 Removed extraction of hip rotation from the "Extra Proxy Pose From Generated Rig" to fix an issue where it would sometimes be flipped
 Added debugging warning to GUI for when debugging mode is activated (Replaces script title next to help)
 Changed the "followName" attribute data type for the pole vector controls to float so interpolation is possible
 
 1.7.5 - 2021-10-19
 Added option to generate secondary skeleton used for game engines (no Segment Scale Compensate)
 Added option to create lines between pole vectors and their targets
 
 1.7.6 - 2021-10-20
 Created "settings" button and the GUI updates necessary to display it
 Created the base for persistent settings and implemented "User Real-time Skeleton" option
 Created a custom help window that takes strings as help inputs to display it to the user

 1.7.7 - 2021-10-21
 Changed the behaviour for when creating a real-time skeleton so it overwrites the original skeleton
 
 1.7.8 - 2021-10-24
 Added aim lines to pole vectors and eye controls
 Added some missing documentation
 Fixed a missing connection between follow attributes and their constraints (pole vectors and eyes)
 
 1.7.9 - 2021-10-26
 Fixed an issue where the right IK switcher curve would sometimes not orient itself correctly
 Added parenting options to IK Switchers (chest, clavicle, world)
 
 1.7.10 - 2021-10-28
 Created more debugging options
 Created ribbon setup for the spine (IK Spine)
 Created IK/FK switcher for the new spine setup
 Made proxy limits optional
 Add option to mirror rigged pose. IK Only. (for animators)
 Added option to reset pose
 
 1.7.11 - 2021-10-29
 Changed the name of the seamless FK/IK button to "Custom Rig Interface" as it now carries pose management functions
 Big update to Custom Rig Interface. It can now mirror, reset, import and export poses.
 Created utility to toggle rigging specific attributes
 
 1.7.12 - 2021-11-01
 Minor patches applied to Custom Rig Interface script
 Created finger specific curl controls
 Added option to control visibility of the fingers
 
 1.7.13 - 2021-11-03
 Modified control notes a bit
 Changed the radius of the IK spine joints
 Created IK finger controls
 Included cog_ctrl IK visibility attributes under rigging specific attributes
 Updated order of the custom attributes under the finger controls (no more top separator)
 Fixed an issue where the right hand would receive an unnecessary offset on its abduction system
 
 1.7.14 - 2021-11-04
 Exposed rotation order attribute for a few controls
 
 1.7.15 - 2021-11-05
 Added missing rotation order attribute to feet
 Added a tagged version of the rotation order to the wrist
 Updated custom rig interface GUI
 Replaced a few repeating strings with general variables
 
 1.7.16 - 2021-11-08
 Big update to custom rig interface
 
 1.7.17 - 2021-11-08
 Fixed an issue where IK fingers wouldn't follow the correct preferred angle
 
 1.8.0 - 2021-11-15
 Changed IK Spine to cube control (With 3 hidden adjustment controls. Not visible by default)
 Changed IK Spine to be the default influence
 Secondary chest adjustment control only affects the chest, not the head (so you can keep line of sight)
 Arm pole vector controls now follow arm's plane instead of wrist
 Moved pole vector custom attributes to wrist for ease of access
 Added twist attributes to the pole vector controls for the arms (found under wrists)
 Added 3D visibility type shapes to IK feet and IK wrists
 Changed the source constraint for the feet stretchy system so it accounts for the roll controls
 
 1.8.1 - 2021-11-16
 Brought back the follow wrist option for the elbow pole vector controls
 Fixed an issue where the elbow controls (pole vector) would sometimes receive rotation from the spine (missing aim up dir)
 Slightly changed the shape of the IK spine control for a better starting point
 Moved the pole vector controls little bit further away during creation
 Created pole vector twist and parenting system for legs
 
 1.8.2 - 2021-11-17
 Slightly changed the initial hand and spine box shapes to better conform to the body shape
 Created auto clavicle system. Clavicle rotates based on wrist position (according to influence % under the wrist ctrl)
 Added option to define heel roll as a proxy step (This should allow for a quicker rig profile import/export)
 Gave proxy pose a default extension ".ppose" instead of just ".json" to avoid confusion with other scripts
 
 1.8.3 - 2021-11-18
 Added offset controls to wrists, chest, cog
 
 1.8.4 - 2021-11-19
 Added offset controls to feet
 
 1.8.5 - 2021-11-23
 Fixed an issue where right arm pole vector was receiving undesired offset due to new twisting system
 
 1.8.6 - 2021-11-24
 Created uniform orientation option
 Redefined the scale calculation system to rely on position calculation rather than joint X distance
 Updated stretchy system to accept different joint scale channels
 Removed tagged version of the rotation order enum
 
 1.8.7 - 2021-11-25
 Changed the general scale calculation sligtly
 Fixed issue where spine04_ctrl curve would be rotated incorrectly when using uniform orients 
 
 1.8.8 - 2021-11-29
 Updated the distance calculation method for legs and arms
 Created an option to output world-space IK controls instead of inheriting from the joints
 Changed rotation source for auto clavicle to account for world-space ik controls
 Recreated the IK Spine to support stretchy system and limit positioning while attached to the ribbon setup
 Added world-space IK support to IK spine
 Added refresh suspend function before operations to speedup rig creation
 Added metadata in form of an attribute (type string) attached to the main control (dictionary/json format)
 Added new FK/IK switching references to account for new wrist orientations
 
 1.8.9 - 2021-12-01
 Re-create the uniform orientation option to keep the orientation of the joints intact (use offset instead)
 
 1.8.10 - 2021-12-02
 Replaced "uniform_ctrl_orient" functionality to drive new offset orientation system
 Created new neck head influence system
 Added offset control to neck
 
 1.8.11 - 2021-12-10
 Fixed an issue where spine wouldn't move properly in Maya 2022 (Python 3)
 Split biped rigger file into a more MVC format (controller, model, view)

 1.8.12 - 2021-12-20
 Fixed flipping spine control
 Deactivated auto clavicle when switching to FK

 1.8.13 - 2021-12-21
 Added option to simplify spine
 Added option to eliminate center hip joint
 Renamed auto clavicle joints to "driver" instead of auto
 Renamed "cog" joint to be called "waist" to better describe it
 Renamed "spine04" joint to be called "chest" so it makes sense when simplified
 Fixed some code repetition for the finger abduction system
 Created sum input node for abduction system
 Added rotation to abduction system

 1.8.14 - 2021-12-22
 Fixed an issue where the finger compression system would pop when adjusted


 1.9.0 - 2021-XX-XX
 Dropped Python 2 support

 TODO:
    Transfer scale information from ik spine limit spine to spines
    Add logging for debugging
    Add option to leave all lock translation attributes off
    Allow Knee Pole Vector offset to be controlled by the hip_ctrl instead of the direction_ctrl only
    (inheritance percentage)
    Make scale system and breathing system optional
    Add more roll joints (upper part of the arm, legs, etc)
    Add option to auto create proxy geo
    Create exporter with options to auto generate selection sets based on LOD names.
    
"""
from shiboken2 import wrapInstance
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QIcon
from maya import OpenMayaUI as omui
from gt_rigger_utilities import *
from gt_rigger_biped_logic import *
from gt_rigger_data import *
import maya.cmds as cmds
import maya.mel as mel
import random
import base64
import json
import sys
import os
import re

# Biped Data
biped_data = GTBipedRiggerData()

# Main Dialog ============================================================================
def build_gui_auto_biped_rig():
    """  Creates the main GUI for GT Auto Biped Rigger """

    # Unpack Common Variables
    script_name = biped_data.script_name
    script_version = biped_data.script_version

    # Get Persistent Settings
    # get_persistent_settings(biped_data)

    # print(biped_data.settings)

    window_name = 'build_gui_auto_biped_rig'
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    build_gui_auto_biped_rig = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                           titleBar=True, minimizeButton=False, maximizeButton=False, sizeable=True)
                          
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    main_window_title = script_name
    if biped_data.debugging:
        title_bgc_color = (1, .3, .3)
        main_window_title = 'Debugging Mode Activated'

    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=4, cw=[(1, 10), (2, 150), (3, 50), (4, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main)
    cmds.text(' ', bgc=title_bgc_color)  # Tiny Empty Space
    cmds.text(main_window_title, bgc=title_bgc_color,  fn='boldLabelFont', align='left')
    settings_btn = cmds.button(label='Settings', bgc=title_bgc_color, c=lambda x:update_gui_settings())
    cmds.button(label='Help', bgc=title_bgc_color, c=lambda x:build_help_gui_auto_biped_rig(script_name))
    cmds.separator(h=10, style='none', p=content_main) # Empty Space

    # ######## Generate Images ########
    # Icon
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True) 
    
    # Create Proxy Icon
    create_proxy_btn_ico = icons_folder_dir + 'gt_abr_create_proxy.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(create_proxy_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNi4wLWMwMDIgNzkuMTY0NDg4LCAyMDIwLzA3LzEwLTIyOjA2OjUzICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjIuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTEyLTMwVDIyOjI4OjU0LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wMS0wM1QxMToxNDowOS0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wMS0wM1QxMToxNDowOS0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpjOTRkMjQ0MS03ZDAyLTZk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'
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(create_proxy_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
        
    # Create Rig Icon
    create_rig_btn_ico = icons_folder_dir + 'gt_abr_create_rig.png'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(create_rig_btn_ico) == False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNi4wLWMwMDIgNzkuMTY0NDg4LCAyMDIwLzA3LzEwLTIyOjA2OjUzICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjIuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTEyLTMwVDIyOjM2OjU3LTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMS0wMS0wM1QxMTo1OTowNC0wODowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMS0wMS0wM1QxMTo1OTowNC0wODowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphOTMwMjJjNC0zZTljLWQ5NGYtOGZiMi0xMThkNzc2Y2I4YTYiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDowZGQ3ODU1NS05Nzk0LTk1NDctOGJmOS02NTM5YmFiOTU0ODkiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpmMDJjNmFhZC1lZmRmLWQ5NDktOTYyYy1lOThmMTZiOTljMDgiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmYwMmM2YWFkLWVmZGYtZDk0OS05NjJjLWU5OGYxNmI5OWMwOCIgc3RFdnQ6d2hlbj0iMjAyMC0xMi0zMFQyMjozNjo1Ny0wODowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIyLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphOTMwMjJjNC0zZTljLWQ5NGYtOGZiMi0xMThkNzc2Y2I4YTYiIHN0RXZ0OndoZW49IjIwMjEtMDEtMDNUMTE6NTk6MDQtMDg6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMi4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz4QupX8AAACnElEQVRYhcWXPWsUURSG33XDfkUQVGKimw/TCRYiiCJisBDEVjAIKQQ7FX9AOv0FloKdFmlECyG9IMRKUdFCiYW4S8wmxtVEXVEfi3uGGWdnZndnZ/HAgZnznq977plz7+QA/U8a6kJnVtINSXVJnyXlJb2X9Nr4paT11BkAnfg0sIVPz4FN/qU14HoXvtq4F+V5C3YPyJnsMHAFeGxYA5gaVAICjligTaAcwqrAD8P3DioBAbus5FjQIDYM1A2b7sZfjnRfQdEaLy+pHMKGJK1J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'
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(create_rig_btn_ico, 'wb')
        image_result.write(image_64_decode)
        image_result.close()

    # Settings ================
    settings_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], h=1, p=content_main) 
    
    # General Settings
    settings_bgc_color = (.4, .4, .4)
    cmds.text('General Settings:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 210), (3, 20)], cs=[(1,10)]) 
    
    # Use Real-time skeleton
    cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space   
    cmds.checkBox(label='  Use Real-time Skeleton', value=biped_data.settings.get('using_no_ssc_skeleton'),
                  ebg=True, cc=lambda x:invert_stored_setting('using_no_ssc_skeleton'))
    
    realtime_custom_help_message = 'Creates another skeleton without the parameter "Segment Scale Compensate" ' \
                                   'being active. This skeleton inherits the transforms from the controls while ' \
                                   'mimicking the behaviour of the "Segment Scale Compensate" option, essentially ' \
                                   'creating a baked version of this Maya depended system.\nAs this baked version ' \
                                   'does not yet fully support non-uniform scaling, it\'s recommended that you only ' \
                                   'use it if you are planning to later send this rig into a game engine or another ' \
                                   '3d application.\n\nThis will allow you to preserve the stretchy settings ' \
                                   'even in programs that do not support it.'
    realtime_custom_help_title = 'Use Real-time Skeleton'
    cmds.button(label='?', bgc=settings_bgc_color,
                c=lambda x: build_custom_help_window(realtime_custom_help_message,
                                                     realtime_custom_help_title))

    # Limit Proxy Movement
    cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space   
    cmds.checkBox(label='  Limit Proxy Movement', value=biped_data.settings.get('proxy_limits'),
                  ebg=True, cc=lambda x: invert_stored_setting('proxy_limits'))
    
    proxy_limit_custom_help_message = 'Unlocks transforms for feet and spine proxy elements. ' \
                                      'This allows for more unconventional character shapes, but makes' \
                                      ' the auto rigger less robust. If this is your first time using it, ' \
                                      'you might want to keep the limits active.'
    proxy_limit_custom_help_title = 'Limit Proxy Movement'
    cmds.button(label='?', bgc=settings_bgc_color,
                c=lambda x: build_custom_help_window(proxy_limit_custom_help_message,
                                                     proxy_limit_custom_help_title))
    
    # Force Uniform Control Orientation
    cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space   
    cmds.checkBox(label='  Uniform Control Orientation', value=biped_data.settings.get('uniform_ctrl_orient'),
                  ebg=True, cc=lambda x: invert_stored_setting('uniform_ctrl_orient'))
    
    uniform_orients_custom_help_message = 'Changes the orientation of most controls to be match the world\'s ' \
                                          'orientation. This means that Z will likely face forward, ' \
                                          'X side and Y up/down.'
    uniform_orients_custom_help_title = 'Uniform Control Orientation'
    cmds.button(label='?', bgc=settings_bgc_color,
                c=lambda x: build_custom_help_window(uniform_orients_custom_help_message,
                                                     uniform_orients_custom_help_title))
    
    # Force World-Space IK Orientation
    cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space   
    cmds.checkBox(label='  World-Space IK Orientation', value=biped_data.settings.get('worldspace_ik_orient'),
                  ebg=True, cc=lambda x: invert_stored_setting('worldspace_ik_orient'))
    
    ws_ik_orients_custom_help_message = 'Changes the orientation of the IK controls to be match the world\'s ' \
                                        'orientation. This means that Z will face forward, X side and Y up/down.' \
                                        '\n\nThe orientation of the joints will be ignored (not inherited)'
    ws_ik_orients_custom_help_title = 'World-Space IK Orientation'
    cmds.button(label='?', bgc=settings_bgc_color,
                c=lambda x: build_custom_help_window(ws_ik_orients_custom_help_message,
                                                     ws_ik_orients_custom_help_title))

    # Simplify Spine
    cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space
    cmds.checkBox(label='  Simplify Spine Joints', value=biped_data.settings.get('simplify_spine'),
                  ebg=True, cc=lambda x: invert_stored_setting('simplify_spine'))

    simplify_spine_custom_help_message = 'The number of spine joints used in the base skinned skeleton is reduced.' \
                                         '\nInstead of creating spine 1, 2, 3, and chest, the auto rigger outputs' \
                                         ' only one spine joint and chest.\n\nThe entire system still exists, within' \
                                         ' the rig, this change only affects the base skeleton (skinned)'
    simplify_spine_custom_help_title = 'Simplify Spine Joints'
    cmds.button(label='?', bgc=settings_bgc_color,
                c=lambda x: build_custom_help_window(simplify_spine_custom_help_message,
                                                     simplify_spine_custom_help_title))

    # # Keep Center Hip Joint
    # cmds.text(' ', bgc=settings_bgc_color, h=20) # Tiny Empty Space
    # cmds.checkBox(label='  Keep Center Hip Joint', value=biped_data.settings.get('using_center_hip_jnt'),
    #               ebg=True, cc=lambda x: invert_stored_setting('using_center_hip_jnt'))
    #
    # keep_center_hip_custom_help_message = 'Creates a center hip joint that can be used as a pivot for other joint' \
    #                                       ' hierarchies, such as a tail.'
    # keep_center_hip_spine_custom_help_title = 'Keep Center Hip Joint'
    # cmds.button(label='?', bgc=settings_bgc_color,
    #             c=lambda x: build_custom_help_window(keep_center_hip_custom_help_message,
    #                                                  keep_center_hip_spine_custom_help_title))

    # Reset Persistent Settings
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=settings_column)
    
    cmds.separator(h=25)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button(label='Reset Persistent Settings', bgc=settings_bgc_color,
                c=lambda x: reset_persistent_settings_validation(biped_data), en=False)

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    # Step 1
    cmds.text('Step 1 - Proxy:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.iconTextButton(style='iconAndTextVertical', image1=create_proxy_btn_ico, label='Create Proxy',
                        statusBarMessage='Creates a proxy/guide elements so the user can determine '
                                         'the character\'s shape.',
                        olc=[1,0,0], enableBackground=True, bgc=[.4,.4,.4], h=80,
                        command=lambda: validate_operation('create_proxy', biped_data.debugging))
    
    # Step 2
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 2 - Pose:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.button(label='Reset Proxy', bgc=(.3,.3,.3), c=lambda x:reset_proxy())
    cmds.separator(h=6, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button(label='Mirror Right to Left', bgc=(.3,.3,.3), c=lambda x:mirror_proxy('right_to_left'))
    cmds.button(label='Mirror Left to Right', bgc=(.3,.3,.3), c=lambda x:mirror_proxy('left_to_right'))

    cmds.separator(h=8, style='none') # Empty Space
    cmds.separator(h=8, style='none') # Empty Space
    cmds.button(label='Import Pose', bgc=(.3,.3,.3), c=lambda x:import_proxy_pose())
    cmds.button(label='Export Pose', bgc=(.3,.3,.3), c=lambda x:export_proxy_pose())
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.button(label='Delete Proxy', bgc=(.3,.3,.3), c=lambda x:delete_proxy())

    # Step 3
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 3 - Create Rig:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.iconTextButton(style='iconAndTextVertical', image1=create_rig_btn_ico, label='Create Rig',
                        statusBarMessage='Creates the control rig. It uses the transform data found in the proxy to '
                                         'determine how to create the skeleton, controls and mechanics.',
                        olc=[1,0,0], enableBackground=True, bgc=[.4,.4,.4], h=80,
                        command=lambda: validate_operation('create_controls', biped_data.debugging))
    
    # Step 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Step 4 - Skin Weights:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button(label='Select Skinning Joints', bgc=(.3,.3,.3), c=lambda x:select_skinning_joints())
    cmds.button(label='Bind Skin Options', bgc=(.3,.3,.3), c=lambda x:mel.eval('SmoothBindSkinOptions;'))

    cmds.separator(h=5, style='none') # Empty Space
    
    # Utilities
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Utilities:', font='boldLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.button(label='Add Custom Rig Interface to Shelf', bgc=(.3,.3,.3), c=lambda x:add_rig_interface_button())
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 0), (2, 8)], p=body_column)
    cmds.button(label='Toggle Label Visibility', bgc=(.3,.3,.3), c=lambda x:gtu_uniform_jnt_label_toggle())
    cmds.button(label='Attach to HumanIK', bgc=(.3,.3,.3), c=lambda x:gt_ab_define_humanik('auto_biped'))
    
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1,0)], p=body_column)
    cmds.button(label='Toggle Rigging Specific Attributes', bgc=(.3,.3,.3), c=lambda x:toggle_rigging_attr())
    cmds.separator(h=7, style='none') # Empty Space
    cmds.button(label='Extract Proxy Pose From Generated Rig', bgc=(.3,.3,.3), c=lambda x:extract_proxy_pose())
    
    cmds.separator(h=10, style='none') # Empty Space

    # Show and Lock Window
    cmds.showWindow(build_gui_auto_biped_rig)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/HIKcreateControlRig.png')
    widget.setWindowIcon(icon)

    # ### GUI Functions ###
    def invert_stored_setting(key_string):
        """
        Used for boolean values, it inverts the value, so if True it becomes False and vice-versa
        
                Parameters:
                    key_string (string) : Key name, used to determine what bool value to flip
        """
        biped_data.settings[key_string] = not biped_data.settings.get(key_string)

    def reset_persistent_settings_validation(biped_data):
        """
        Used for boolean values, it inverts the value, so if True it becomes False and vice-versa

                Parameters: TODO
                    biped_data (string) : Key name, used to determine what bool value to flip
        """
        # settings = biped_data.settings_default
        # print("This")
        # print(biped_data.settings_default)
        # biped_data.settings = biped_data.settings_default

        # biped_data = GTBipedRiggerData()
        reset_persistent_settings(biped_data)
        # print(biped_data.settings)
        # del biped_data

    def update_gui_settings():
        """
        Function to show or hide settings. 
        It acomplishes this by switching the height of the body_column and the settings_column.
        """
        if biped_data.settings.get('is_settings_visible') != True:
            biped_data.settings['is_settings_visible'] = True

            cmds.button(settings_btn, e=True, l='Apply', bgc=(.6, .6, .6)) 

            # Hide Checklist Items
            biped_data.settings['body_column_height'] = cmds.rowColumnLayout(body_column, q=True, h=True)
            cmds.rowColumnLayout(body_column, e=True, h=1)
            
            # Show Settings Items
            cmds.rowColumnLayout(settings_column, e=True, h=(biped_data.settings.get('body_column_height')))
        else:
            biped_data.settings['is_settings_visible'] = False
            cmds.rowColumnLayout(body_column, e=True, h=biped_data.settings.get('body_column_height'))
            cmds.rowColumnLayout(settings_column, e=True, h=1)
            cmds.button(settings_btn, e=True, l='Settings', bgc=title_bgc_color)
            # set_persistent_settings(biped_data)
            # get_persistent_settings(biped_data)

    # Main GUI Ends Here =================================================================================
    

# Creates Help GUI
def build_help_gui_auto_biped_rig(script_name):
    """ Creates the Help windows """
    window_name = 'build_help_gui_auto_biped_rig'
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + ' Help', mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout('main_column', p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p='main_column') # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p='main_column') # Title Column
    cmds.text(script_name + ' Help', bgc=(.4, .4, .4),  fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p='main_column') # Empty Space


    # Body ====================   
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p='main_column')
    cmds.text(l='Script for quickly generating an advanced biped rig', align='center', fn='boldLabelFont')
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='For more predictable results execute it in a new scene\n containing only the geometry of the desired character.', align='center')
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=3, cw=[(1, 28)], cs=[(1,40)], p='main_column')
    cmds.text(l='Click ', hl=True, highlightColor=[1,1,1])
    cmds.text(l='<a href="https://github.com/TrevisanGMW/gt-tools/tree/master/docs#-gt-auto-biped-rigger-">Here</a>', hl=True, highlightColor=[1,1,1])
    cmds.text(l=' for a more complete documentation.', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p='main_column')
    
    auto_biped_help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="smallPlainLabelFont")
 
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='[X] Step 1: .\n -Create Proxy:\n   This button will create many temporary curves that will later\n   be used to generate the rig.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n   In case you want to re-scale the proxy, use the root proxy\n   control for that. The initial scale is the average height of a\n   woman. (160cm)\n   Presets for other sizes can be found on Github.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n   These are not joints. Please don\'t delete or rename them.')
  
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n[X] Step 2:\n   Pose the proxy (guide) to match your character.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Reset Proxy:\n   Resets the position and rotation of the proxy elements,\n   essentially "recreating" the proxy.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Mirror Side to Side:\n   Copies the transform data from one side to the other,\n   mirroring the pose.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Import Pose:\n   Imports a JSON file containing the transforms of the proxy\n   elements. This file is generated using the "Export Pose"\n   function.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Export Pose:\n   Exports a JSON file containing the transforms of the proxy\n   elements.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Delete Proxy:\n   Simply deletes the proxy in case you no longer need it.')
    
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n[X] Step 3:\n   This button creates the control rig. It uses the transform data\n   found in the proxy to determine how to create the skeleton\n   and controls. This function will delete the proxy.\n   Make sure you export it first if you plan to reuse it later.')
    
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n[X] Step 4:\n   Now that the rig has been created, it\'s time to attach it to the\n   geometry.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Select Skinning Joints:\n   Select only joints that should be used when skinning the\n   character. This means that it will not include end joints or\n   the toes.')
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n -Bind Skin Options:\n   Opens the options for the function "Bind Skin" so the desired\n   geometry can attached to the skinning joints.\n   Make sure to use the "Bind to" as "Selected Joints"')

    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it='\n\n[X] Utilities:\n   These are utilities that you can use after creating your rig.\n   Please visit the full documentation to learn more about it.')
    
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
    
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p='main_column')
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p='main_column')
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p='main_column')
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        """ Closes help windows """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    # Help Dialog Ends Here =================================================================================


def build_custom_help_window(input_text, help_title=''):
    """
    Creates a help window to display the provided text

            Parameters:
                input_text (string): Text used as help, this is displayed in a scroll fields.
                help_title (optinal, string)
    """
    window_name = help_title.replace(" ","_").replace("-","_").lower().strip() + "_help_window"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= help_title + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(help_title + ' Help', bgc=(.4, .4, .4),  fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p=main_column) # Empty Space

    # Body ====================       
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    
    help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')
 
    cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)
    cmds.scrollField(help_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        """ Closes help windows """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    # Custom Help Dialog Ends Here =================================================================================


def validate_operation(operation, debugging=False):
    """
    Validates the necessary objects before executing a big function
    
            Parameters:
                operation (string): Name of the desired operation. e.g. "create_proxy" or "create_controls"
                debugging (bool): Debugging mode causes the script to auto delete previous objects (for quick iteration)

    """
    
    # Load Required Plugins
    required_plugins = ['quatNodes','matrixNodes']
    for plugin in required_plugins:
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            cmds.loadPlugin(plugin, qt=False)
    
    is_valid = True
    if operation == 'create_proxy':
        # Starts new instance (clean scene)
        if biped_data.debugging and biped_data.debugging_force_new_scene:
            persp_pos = cmds.getAttr('persp.translate')[0]
            persp_rot = cmds.getAttr('persp.rotate')[0]
            cmds.file(new=True, force=True)
            if biped_data.debugging_keep_cam_transforms:
                cmds.viewFit(all=True)
                cmds.setAttr('persp.tx', persp_pos[0])
                cmds.setAttr('persp.ty', persp_pos[1])
                cmds.setAttr('persp.tz', persp_pos[2])
                cmds.setAttr('persp.rx', persp_rot[0])
                cmds.setAttr('persp.ry', persp_rot[1])
                cmds.setAttr('persp.rz', persp_rot[2])
            
        
        # Debugging (Auto deletes generated proxy)
        if biped_data.debugging and biped_data.debugging_auto_recreate:
            try:
                cmds.delete(biped_data.elements_default.get('main_proxy_grp'))
            except:
                pass


        # Check if proxy exists in the scene
        proxy_elements = [biped_data.elements_default.get('main_proxy_grp')]
        for proxy in biped_data.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(biped_data.elements_default.get(proxy))
        for obj in proxy_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. Proxy creation already in progress. Delete current proxy or generate a rig before creating a new one.')
                
        # Check for existing rig or conflicting names
        undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
        for jnt in biped_data.joints_default:
            undesired_elements.append(biped_data.joints_default.get(jnt))
        for obj in undesired_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. This means that you either already created a rig or you have conflicting names on your objects. (Click on "Help" for more details)')

        # If valid, create proxy
        if is_valid:
            function_name = 'GT Auto Biped - Create Proxy'
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            cmds.refresh(suspend=True)
            try:
                create_proxy(biped_data)
            except Exception as e:
                cmds.warning(str(e))
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=function_name)
                cmds.refresh(suspend=False)

        # Debugging (Auto imports proxy)
        if biped_data.debugging and biped_data.debugging_import_proxy and os.path.exists(biped_data.debugging_import_path):
            import_proxy_pose(debugging=True, debugging_path=biped_data.debugging_import_path)

    elif operation == 'create_controls':
        # Starts new instance (clean scene)
        if biped_data.debugging and biped_data.debugging_force_new_scene:
            persp_pos = cmds.getAttr('persp.translate')[0]
            persp_rot = cmds.getAttr('persp.rotate')[0]
            cmds.file(new=True, force=True)
            if biped_data.debugging_keep_cam_transforms:
                cmds.viewFit(all=True)
                cmds.setAttr('persp.tx', persp_pos[0])
                cmds.setAttr('persp.ty', persp_pos[1])
                cmds.setAttr('persp.tz', persp_pos[2])
                cmds.setAttr('persp.rx', persp_rot[0])
                cmds.setAttr('persp.ry', persp_rot[1])
                cmds.setAttr('persp.rz', persp_rot[2])

        # Debugging (Auto deletes generated rig)
        if biped_data.debugging and biped_data.debugging_auto_recreate:
            try:
                if cmds.objExists('rig_grp'):
                    cmds.delete('rig_grp')
                if cmds.objExists(biped_data.elements.get('main_proxy_grp')):
                    cmds.delete(biped_data.elements.get('main_proxy_grp'))
                create_proxy(biped_data)
                # Debugging (Auto imports proxy)
                if biped_data.debugging_import_proxy and os.path.exists(biped_data.debugging_import_path):
                    import_proxy_pose(debugging=True, debugging_path=biped_data.debugging_import_path)
            except:
                pass

        # Validate Proxy
        if not cmds.objExists(biped_data.elements.get('main_proxy_grp')):
            is_valid = False
            cmds.warning('Proxy couldn\'t be found. Make sure you first create a proxy (guide objects) before generating a rig.')

        proxy_elements = [biped_data.elements.get('main_proxy_grp')]
        for proxy in biped_data.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(biped_data.elements.get(proxy))
        for obj in proxy_elements:
            if not cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.')

        # If valid, create rig
        if is_valid:
            function_name = 'GT Auto Biped - Create Rig'
            if biped_data.debugging:
                create_controls(biped_data)
            else:
                cmds.undoInfo(openChunk=True, chunkName=function_name)
                cmds.refresh(suspend=True)
                try:
                    create_controls(biped_data)
                except Exception as e:
                    raise e
                finally:
                    cmds.undoInfo(closeChunk=True, chunkName=function_name)
                    cmds.refresh(suspend=False)


            # Debugging (Auto binds joints to provided geo)
            if biped_data.debugging and biped_data.debugging_bind_rig and cmds.objExists(biped_data.debugging_bind_geo):
                cmds.select(d=True)
                select_skinning_joints()
                selection = cmds.ls(selection=True)
                if biped_data.debugging_bind_heatmap:
                    cmds.skinCluster(selection, biped_data.debugging_bind_geo, bindMethod=2, heatmapFalloff=0.68, toSelectedBones=True, smoothWeights=0.5, maximumInfluences=4)
                else:
                    cmds.skinCluster(selection, biped_data.debugging_bind_geo, bindMethod=1, toSelectedBones=True, smoothWeights=0.5, maximumInfluences=4)
                cmds.select(d=True)



def select_skinning_joints():
    """ Selects joints that should be used during the skinning process """

    # Check for existing rig
    is_valid = True
    desired_elements = []
    for jnt in biped_data.joints_default:
        desired_elements.append(biped_data.joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. (Click on "Help" for more details)')

    if is_valid:
        skinning_joints = []
        for obj in biped_data.joints_default:
            if '_end' + JNT_SUFFIX.capitalize() not in biped_data.joints_default.get(obj)\
                    and '_toe' not in biped_data.joints_default.get(obj)\
                    and 'root_' not in biped_data.joints_default.get(obj) \
                    and 'driver' not in biped_data.joints_default.get(obj):
                parent = cmds.listRelatives(biped_data.joints_default.get(obj), parent=True)[0] or ''
                if parent != 'skeleton_grp':
                    skinning_joints.append(biped_data.joints_default.get(obj))
        cmds.select(skinning_joints)
        if 'left_forearm_jnt' not in skinning_joints or 'right_forearm_jnt' not in skinning_joints:
            for obj in ['left_forearm_jnt', 'right_forearm_jnt']:
                try:
                    cmds.select(obj, add=True)
                except:
                    pass

def reset_proxy(suppress_warning=False):
    """
    Resets proxy elements to their original position

            Parameters:
                suppress_warning (bool): Whether or not it should give inView feedback

    """

    is_reset = False
    attributes_set_zero = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'followHip']
    attributes_set_one = ['sx', 'sy', 'sz', 'v']
    proxy_elements = []
    for proxy in biped_data.elements_default:
        if '_crv' in proxy or proxy.endswith('_pivot'):
            proxy_elements.append(biped_data.elements_default.get(proxy))
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
        if not suppress_warning:
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span><span style=\"color:#FFFFFF;\"> was reset!</span>', pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.warning('No proxy found. Nothing was reset.')

def delete_proxy(suppress_warning=False):
    """
    Deletes current proxy/guide curves

            Parameters:
                suppress_warning (bool): Whether or not it should give warnings (feedback)

    """

    is_deleted = False

    to_delete_elements = [biped_data.elements.get('main_proxy_grp'), biped_data.elements.get('main_crv') ]
    for obj in to_delete_elements:
        if cmds.objExists(obj) and is_deleted == False:
            cmds.delete(obj)
            is_deleted = True

    if not is_deleted:
        if not suppress_warning:
            cmds.warning('Proxy not found. Nothing was deleted.')
    else:
        unique_message = '<' + str(random.random()) + '>'
        unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span>' \
                          '<span style=\"color:#FFFFFF;\"> was deleted!</span>'
        cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)


def mirror_proxy(operation):
    """
    Mirrors a pose on the proxy curves by copying translate, rotate and scale attributes from one side to the other

            Parameters:
                operation (string) : what direction to mirror. "left_to_right" (+X to -X) or "right_to_left" (-X to +X)

    """
    def mirror_attr(source, target):
        """
        Mirrors attributes for proxy elements
        Args:
            source: Source object
            target: Target object

        """
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
    if not cmds.objExists(biped_data.elements.get('main_proxy_grp')):
        is_valid = False
        cmds.warning("Proxy couldn't be found. Make sure you first create a proxy (guide objects) before mirroring it.")

    proxy_elements = [biped_data.elements.get('main_proxy_grp')]
    for proxy in biped_data.elements_default:
        if '_crv' in proxy:
            proxy_elements.append(biped_data.elements.get(proxy))
    for obj in proxy_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            warning = '"' + obj + '"'
            warning += ' is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.'
            cmds.warning(warning)

    # Lists
    left_elements = []
    right_elements = []

    if is_valid:
        for obj in biped_data.elements:
            if obj.startswith('left_') and ('_crv' in obj or '_pivot' in obj):
                left_elements.append(biped_data.elements.get(obj))
            elif obj.startswith('right_') and ( '_crv' in obj or '_pivot' in obj):
                right_elements.append(biped_data.elements.get(obj))

        for left_obj in left_elements:
            for right_obj in right_elements:
                if left_obj.replace('left', '') == right_obj.replace('right', ''):

                    if operation == 'left_to_right':
                        mirror_attr(left_obj, right_obj)

                    elif operation == 'right_to_left':
                        mirror_attr(right_obj, left_obj)

        if operation == 'left_to_right':
            unique_message = '<' + str(random.random()) + '>'
            unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span>' \
                              '<span style=\"color:#FFFFFF;\"> mirrored from left to right. (+X to -X)</span>'
            cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)

        elif operation == 'right_to_left':
            unique_message = '<' + str(random.random()) + '>'
            unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy</span>' \
                              '<span style=\"color:#FFFFFF;\"> mirrored from right to left. (-X to +X)</span>'
            cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)

def export_proxy_pose():
    """
    Exports a JSON file containing the translate, rotate and scale data from every proxy curve (used to export a pose)
    Added a variable called "gt_auto_biped_export_method" after v1.3, so the extraction method can be stored.

    """
    # Validate Proxy and Write file
    is_valid = True
    successfully_created_file = False

    proxy_elements = [biped_data.elements.get('main_proxy_grp')]
    for proxy in biped_data.elements_default:
        if '_crv' in proxy:
            proxy_elements.append(biped_data.elements.get(proxy))
    for obj in proxy_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            warning = '"' + obj + '"'
            warning += ' is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.'
            cmds.warning(warning)


    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=biped_data.script_name + ' - PPOSE File (*.ppose);;'
                                                + biped_data.script_name + ' - JSON File (*.json)',
                                     dialogStyle=2, okCaption= 'Export',
                                     caption= 'Exporting Proxy Pose for "' + biped_data.script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:

        export_dict = {'gt_auto_biped_version': biped_data.script_version,
                       'gt_auto_biped_export_method': 'object-space'}
        for obj in biped_data.elements_default:
            if '_crv' in obj:
                translate = cmds.getAttr(biped_data.elements_default.get(obj) + '.translate')[0]
                rotate = cmds.getAttr(biped_data.elements_default.get(obj) + '.rotate')[0]
                scale = cmds.getAttr(biped_data.elements_default.get(obj) + '.scale')[0]
                to_save = [biped_data.elements_default.get(obj), translate, rotate, scale]
                export_dict[obj] = to_save

            if obj.endswith('_pivot'):
                if cmds.objExists(biped_data.elements_default.get(obj)):
                    translate = cmds.getAttr(biped_data.elements_default.get(obj) + '.translate')[0]
                    rotate = cmds.getAttr(biped_data.elements_default.get(obj) + '.rotate')[0]
                    scale = cmds.getAttr(biped_data.elements_default.get(obj) + '.scale')[0]
                    to_save = [biped_data.elements_default.get(obj), translate, rotate, scale]
                    export_dict[obj] = to_save

        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                                    'Proxy Pose</span><span style=\"color:#FFFFFF;\"> '
                                                    'exported.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose exported to the file "' + pose_file + '".')
        except Exception as e:
            print (e)
            successfully_created_file = False
            cmds.warning('Couldn\'t write to file. Please make sure the exporting directory is accessible.')


def import_proxy_pose(debugging=False, debugging_path=''):
    """
    Imports a JSON file containing the translate, rotate and scale data for every proxy curve
    (exported using the "export_proxy_pose" function)
    Uses the imported data to set the translate, rotate and scale position of every proxy curve
    Uses the function "delete_proxy()" to recreate it if necessary
    Uses the function "reset_proxy()" to clean proxy before importing

    It now checks import method to use the proper method when setting attributes.
    Exporting using the export button uses "setAttr", extract functions will use "xform" instead.

            Parameters:
                debugging (bool): If debugging, the function will attempt to auto load the file provided in the
                                  "debugging_path" parameter
                debugging_path (string): Debugging path for the import function

    """
    def set_unlocked_os_attr(target, attr, value):
        """
        Sets an attribute to the provided value in case it's not locked (Uses "cmds.setAttr" function so object space)

                Parameters:
                    target (string): Name of the target object (object that will receive transforms)
                    attr (string): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
                    value (float): Value used to set attribute. e.g. 1.5, 2, 5...

        """
        try:
            if not cmds.getAttr(target + '.' + attr, lock=True):
                cmds.setAttr(target + '.' + attr, value)
        except:
            pass

    def set_unlocked_ws_attr(target, attr, value_tuple):
        """
        Sets an attribute to the provided value in case it's not locked (Uses "cmds.xform" function with world space)

                Parameters:
                    target (string): Name of the target object (object that will receive transforms)
                    attr (string): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
                    value_tuple (tuple): A tuple with three (3) floats used to set attributes. e.g. (1.5, 2, 5)

        """
        try:
            if attr == 'translate':
                cmds.xform(target, ws=True, t=value_tuple)
            if attr == 'rotate':
                cmds.xform(target, ws=True, ro=value_tuple)
            if attr == 'scale':
                cmds.xform(target, ws=True, s=value_tuple)
        except:
            pass

    import_version = 0.0
    import_method = 'object-space'

    if not debugging:
        file_name = cmds.fileDialog2(fileFilter=biped_data.script_name + ' - PPOSE File (*.ppose);;' +
                                                biped_data.script_name + ' - JSON File (*.json)',
                                     dialogStyle=2, fileMode=1, okCaption='Import',
                                     caption= 'Importing Proxy Pose for "' + biped_data.script_name + '"') or []
    else:
        file_name = [debugging_path]

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
                    else:
                        import_version = float(re.sub("[^0-9]", "", str(data.get('gt_auto_biped_version'))))

                    if data.get('gt_auto_biped_export_method'):
                      import_method = data.get('gt_auto_biped_export_method')

                    is_valid_scene = True
                    # Check for existing rig or conflicting names
                    undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
                    for jnt in biped_data.joints_default:
                        undesired_elements.append(biped_data.joints_default.get(jnt))
                    for obj in undesired_elements:
                        if cmds.objExists(obj) and is_valid_scene:
                            is_valid_scene = False
                            cmds.warning('"' + obj + '" found in the scene. This means that you either already created a rig or you have conflicting names on your objects. (Click on "Help" for more details)')

                    if is_valid_scene:
                        # Check for Proxy
                        proxy_exists = True

                        proxy_elements = []
                        for proxy in biped_data.elements_default:
                            if '_crv' in proxy:
                                proxy_elements.append(biped_data.elements.get(proxy))
                        for obj in proxy_elements:
                            if not cmds.objExists(obj) and proxy_exists:
                                proxy_exists = False
                                delete_proxy(True)
                                validate_operation('create_proxy', debugging)
                                cmds.warning('Current proxy was missing elements, a new one was created.')

                    if is_valid_file and is_valid_scene:
                        if import_method == 'world-space':
                            reset_proxy(suppress_warning=True)
                            sorted_pairs = []
                            for proxy in data:
                                if proxy != 'gt_auto_biped_version' and proxy != 'gt_auto_biped_export_method':
                                    curent_object = data.get(proxy) # Name, T, R, S
                                    if cmds.objExists(curent_object[0]):
                                        long_name = cmds.ls(curent_object[0], l=True) or []
                                        number_of_parents = len(long_name[0].split('|'))
                                        sorted_pairs.append((curent_object, number_of_parents))

                                    sorted_pairs.sort(key=lambda x:x[1], reverse=True)

                            # Scale (Children First)
                            for obj in sorted_pairs:
                                curent_object = obj[0]
                                if cmds.objExists(curent_object[0]):
                                    set_unlocked_os_attr(curent_object[0], 'sx', curent_object[3][0])
                                    set_unlocked_os_attr(curent_object[0], 'sy', curent_object[3][1])
                                    set_unlocked_os_attr(curent_object[0], 'sz', curent_object[3][2])

                            # Translate and Rotate (Parents First)
                            for obj in reversed(sorted_pairs):
                                curent_object = obj[0]
                                if cmds.objExists(curent_object[0]):
                                    set_unlocked_ws_attr(curent_object[0], 'translate', curent_object[1])
                                    set_unlocked_ws_attr(curent_object[0], 'rotate', curent_object[2])

                            # Set Transfer Pole Vectors Again
                            for obj in reversed(sorted_pairs):
                                curent_object = obj[0]
                                if 'knee' in curent_object[0] or 'elbow' in curent_object[0]:
                                    if cmds.objExists(curent_object[0]):
                                        set_unlocked_ws_attr(curent_object[0], 'translate', curent_object[1])
                                        set_unlocked_ws_attr(curent_object[0], 'rotate', curent_object[2])

                        else:  # Object-Space
                            for proxy in data:
                                if proxy != 'gt_auto_biped_version' and proxy != 'gt_auto_biped_export_method':
                                    curent_object = data.get(proxy) # Name, T, R, S
                                    if cmds.objExists(curent_object[0]):
                                        set_unlocked_os_attr(curent_object[0], 'tx', curent_object[1][0])
                                        set_unlocked_os_attr(curent_object[0], 'ty', curent_object[1][1])
                                        set_unlocked_os_attr(curent_object[0], 'tz', curent_object[1][2])
                                        set_unlocked_os_attr(curent_object[0], 'rx', curent_object[2][0])
                                        set_unlocked_os_attr(curent_object[0], 'ry', curent_object[2][1])
                                        set_unlocked_os_attr(curent_object[0], 'rz', curent_object[2][2])
                                        set_unlocked_os_attr(curent_object[0], 'sx', curent_object[3][0])
                                        set_unlocked_os_attr(curent_object[0], 'sy', curent_object[3][1])
                                        set_unlocked_os_attr(curent_object[0], 'sz', curent_object[3][2])

                        if not debugging:
                            unique_message = '<' + str(random.random()) + '>'
                            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy Pose</span><span style=\"color:#FFFFFF;\"> imported!</span>', pos='botLeft', fade=True, alpha=.9)
                            sys.stdout.write('Pose imported from the file "' + pose_file + '".')

                except Exception as e:
                    print(e)
                    cmds.warning('An error occured when importing the pose. Make sure you imported the correct JSON file. (Click on "Help" for more info)')
        except:
            file_exists = False
            cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')


def gt_ab_define_humanik(character_name):
    """
    Auto creates a character definition for GT Auto Biped. (It overwrites any definition with the same name)

            Parameters:
                character_name (string): Name of the HIK character

    """
    is_operation_valid = True

    try:
        if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.loadPlugin("mayaHIK", quiet=True)
    except:
        pass

    # Check for existing rig
    exceptions = [biped_data.joints_default.get('spine01_jnt'),
                  biped_data.joints_default.get('spine02_jnt'),
                  biped_data.joints_default.get('spine03_jnt')]
    desired_elements = []
    for jnt in biped_data.joints_default:
        desired_elements.append(biped_data.joints_default.get(jnt))
    for obj in exceptions:
        desired_elements.remove(obj)
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_operation_valid:
            is_operation_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. '
                                     '(Click on "Help" for more details)')

    # Source HIK Modules
    if is_operation_valid:
        maya_location = os.environ['MAYA_LOCATION']
        try:
            # Source HIK scripts
            mel.eval('source "' + maya_location + '/scripts/others/hikGlobalUtils.mel"')
            mel.eval('source "' + maya_location + '/scripts/others/hikCharacterControlsUI.mel"')
            mel.eval('source "' + maya_location + '/scripts/others/hikDefinitionOperations.mel"')
        except:
            print('#' * 80)
            if not os.path.exists(maya_location + '/scripts/others/hikGlobalUtils.mel'):
                print('The module "' + maya_location + '/scripts/others/hikGlobalUtils.mel" couldn\'t be found.')
            if not os.path.exists(maya_location + '/scripts/others/hikCharacterControlsUI.mel'):
                print('The module "' + maya_location + '/scripts/others/hikCharacterControlsUI.mel" couldn\'t be found.')
            if not os.path.exists(maya_location + '/scripts/others/hikDefinitionOperations.mel'):
                print('The module "' + maya_location + '/scripts/others/hikDefinitionOperations.mel" couldn\'t be found.')
            print('#' * 80)
            cmds.warning('HumanIK modules couldn\'t be found. You might have to define the character manually. Open script editor for more information.')
            is_operation_valid = False

    # Create Character Definition
    if is_operation_valid:
        try:
            joints = biped_data.joints_default  # Unpack

            mel.eval('catchQuiet(deleteCharacter("' + character_name + '"))')
            mel.eval('hikCreateCharacter("' + character_name + '")')

            # Add joints to Definition.
            mel.eval('setCharacterObject("' + joints.get('main_jnt') + '", "' + character_name + '", 0,0);')
            mel.eval('setCharacterObject("' + joints.get('hip_jnt') + '", "' + character_name + '", 1,0);')
            mel.eval('setCharacterObject("' + joints.get('left_hip_jnt') + '", "' + character_name + '", 2,0);')
            mel.eval('setCharacterObject("' + joints.get('left_knee_jnt') + '", "' + character_name + '", 3,0);')
            mel.eval('setCharacterObject("' + joints.get('left_ankle_jnt') + '", "' + character_name + '", 4,0);')
            mel.eval('setCharacterObject("' + joints.get('right_hip_jnt') + '", "' + character_name + '", 5,0);')
            mel.eval('setCharacterObject("' + joints.get('right_knee_jnt') + '", "' + character_name + '", 6,0);')
            mel.eval('setCharacterObject("' + joints.get('right_ankle_jnt') + '", "' + character_name + '", 7,0);')
            mel.eval('setCharacterObject("' + joints.get('cog_jnt') + '", "' + character_name + '", 8,0);')
            mel.eval('setCharacterObject("' + joints.get('left_shoulder_jnt') + '", "' + character_name + '", 9,0);')
            mel.eval('setCharacterObject("' + joints.get('left_elbow_jnt') + '", "' + character_name + '", 10,0);')
            mel.eval('setCharacterObject("' + joints.get('left_wrist_jnt') + '", "' + character_name + '", 11,0);')
            mel.eval('setCharacterObject("' + joints.get('right_shoulder_jnt') + '", "' + character_name + '", 12,0);')
            mel.eval('setCharacterObject("' + joints.get('right_elbow_jnt') + '", "' + character_name + '", 13,0);')
            mel.eval('setCharacterObject("' + joints.get('right_wrist_jnt') + '", "' + character_name + '", 14,0);')
            mel.eval('setCharacterObject("' + joints.get('head_jnt') + '", "' + character_name + '", 15,0);')
            mel.eval('setCharacterObject("' + joints.get('left_ball_jnt') + '", "' + character_name + '", 16,0);')
            mel.eval('setCharacterObject("' + joints.get('right_ball_jnt') + '", "' + character_name + '", 17,0);')
            mel.eval('setCharacterObject("' + joints.get('left_clavicle_jnt') + '", "' + character_name + '", 18,0);')
            mel.eval('setCharacterObject("' + joints.get('right_clavicle_jnt') + '", "' + character_name + '", 19,0);')
            mel.eval('setCharacterObject("' + joints.get('neck_base_jnt') + '", "' + character_name + '", 20,0);')
            mel.eval('setCharacterObject("' + joints.get('neck_mid_jnt') + '", "' + character_name + '", 32,0);')

            # Simplified Spine:
            mel.eval('setCharacterObject("' + joints.get('spine01_jnt') + '", "' + character_name + '", 23,0);')
            if cmds.objExists(joints.get('spine02_jnt')):
                mel.eval('setCharacterObject("' + joints.get('spine02_jnt') + '", "' + character_name + '", 24,0);')
            else:
                joint_name = re.sub(r'[0-9]+', '', joints.get('spine02_jnt'))
                mel.eval('setCharacterObject("' + joint_name + '", "' + character_name + '", 24,0);')
            mel.eval('setCharacterObject("' + joints.get('spine03_jnt') + '", "' + character_name + '", 25,0);')
            mel.eval('setCharacterObject("' + joints.get('spine04_jnt') + '", "' + character_name + '", 26,0);')

            # Fingers
            mel.eval('setCharacterObject("' + joints.get('left_thumb01_jnt') + '", "' + character_name + '", 50,0);')
            mel.eval('setCharacterObject("' + joints.get('left_thumb02_jnt') + '", "' + character_name + '", 51,0);')
            mel.eval('setCharacterObject("' + joints.get('left_thumb03_jnt') + '", "' + character_name + '", 52,0);')

            mel.eval('setCharacterObject("' + joints.get('left_index01_jnt') + '", "' + character_name + '", 54,0);')
            mel.eval('setCharacterObject("' + joints.get('left_index02_jnt') + '", "' + character_name + '", 55,0);')
            mel.eval('setCharacterObject("' + joints.get('left_index03_jnt') + '", "' + character_name + '", 56,0);')

            mel.eval('setCharacterObject("' + joints.get('left_middle01_jnt') + '", "' + character_name + '", 58,0);')
            mel.eval('setCharacterObject("' + joints.get('left_middle02_jnt') + '", "' + character_name + '", 59,0);')
            mel.eval('setCharacterObject("' + joints.get('left_middle03_jnt') + '", "' + character_name + '", 60,0);')

            mel.eval('setCharacterObject("' + joints.get('left_ring01_jnt') + '", "' + character_name + '", 62,0);')
            mel.eval('setCharacterObject("' + joints.get('left_ring02_jnt') + '", "' + character_name + '", 63,0);')
            mel.eval('setCharacterObject("' + joints.get('left_ring03_jnt') + '", "' + character_name + '", 64,0);')

            mel.eval('setCharacterObject("' + joints.get('left_pinky01_jnt') + '", "' + character_name + '", 66,0);')
            mel.eval('setCharacterObject("' + joints.get('left_pinky02_jnt') + '", "' + character_name + '", 67,0);')
            mel.eval('setCharacterObject("' + joints.get('left_pinky03_jnt') + '", "' + character_name + '", 68,0);')

            mel.eval('setCharacterObject("' + joints.get('right_thumb01_jnt') + '", "' + character_name + '", 74,0);')
            mel.eval('setCharacterObject("' + joints.get('right_thumb02_jnt') + '", "' + character_name + '", 75,0);')
            mel.eval('setCharacterObject("' + joints.get('right_thumb03_jnt') + '", "' + character_name + '", 76,0);')

            mel.eval('setCharacterObject("' + joints.get('right_index01_jnt') + '", "' + character_name + '", 78,0);')
            mel.eval('setCharacterObject("' + joints.get('right_index02_jnt') + '", "' + character_name + '", 79,0);')
            mel.eval('setCharacterObject("' + joints.get('right_index03_jnt') + '", "' + character_name + '", 80,0);')

            mel.eval('setCharacterObject("' + joints.get('right_middle01_jnt') + '", "' + character_name + '", 82,0);')
            mel.eval('setCharacterObject("' + joints.get('right_middle02_jnt') + '", "' + character_name + '", 83,0);')
            mel.eval('setCharacterObject("' + joints.get('right_middle03_jnt') + '", "' + character_name + '", 84,0);')

            mel.eval('setCharacterObject("' + joints.get('right_ring01_jnt') + '", "' + character_name + '", 86,0);')
            mel.eval('setCharacterObject("' + joints.get('right_ring02_jnt') + '", "' + character_name + '", 87,0);')
            mel.eval('setCharacterObject("' + joints.get('right_ring03_jnt') + '", "' + character_name + '", 88,0);')

            mel.eval('setCharacterObject("' + joints.get('right_pinky01_jnt') + '", "' + character_name + '", 90,0);')
            mel.eval('setCharacterObject("' + joints.get('right_pinky02_jnt') + '", "' + character_name + '", 91,0);')
            mel.eval('setCharacterObject("' + joints.get('right_pinky03_jnt') + '", "' + character_name + '", 92,0);')

            try:
                mel.eval('setCharacterObject("' + joints.get('left_forearm_jnt') + '", "' + character_name + '", 193,0);')
                mel.eval('setCharacterObject("' + joints.get('right_forearm_jnt') + '", "' + character_name + '", 195,0);')
            except:
               pass

            mel.eval('hikUpdateDefinitionUI;')
            mel.eval('hikToggleLockDefinition();')

            cmds.select(d=True)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">HumanIK</span><span style=\"color:#FFFFFF;\"> character and definition created!</span>', pos='botLeft', fade=True, alpha=.9)

        except:
            cmds.warning('An error happened when creating the definition. You might have to assign your joints manually.')



def extract_proxy_pose():
    """
    Extracts the proxy pose from a generated rig into a JSON file. Useful when the user forgot to save it and generated the rig already.

    Exports using "xform" and world space for more flexibility (with the exception of scale)

    """

    def extract_transform_joint_to_proxy(joint_name, ignore_translate=False, ignore_rotate=False, ignore_scale=False, no_jnt_extraction=None):
        """
        Extracts the world-space for Translate and Rotate and the object-space Scale of the provided joint
        then returns a list with proxy name, translate list, rotate list, and scale list
        [ proxy_name, translate_xyz, rotate_xyz, scale_xyz ]

                Parameters:
                    joint_name (string): Name of the joint used to extract the transform
                    ignore_translate (bool): If active, it returns default translate values (0,0,0) instead of extracting it
                    ignore_rotate (bool): If active, it returns default rotate values (0,0,0) instead of extracting it
                    ignore_scale (bool): If active, it returns default scale values (1,1,1) instead of extracting it
                    no_jnt_extraction (bool): In case using another object to match it, you can provide it here

                Returns:
                    extracted_pair (list): [proxy_name, translate_xyz, rotate_xyz, scale_xyz]
        """

        proxy_name = joint_name.replace(JNT_SUFFIX, PROXY_SUFFIX).replace('end' + JNT_SUFFIX.capitalize(), 'end' + PROXY_SUFFIX.capitalize())

        if no_jnt_extraction:
            joint_name = no_jnt_extraction

        if ignore_translate:
            translate = (0, 0, 0)
        else:
            translate = cmds.xform(joint_name, q=True, t=True, ws=True)

        if ignore_rotate:
            rotate = (0, 0, 0)
        else:
            rotate = cmds.xform(joint_name, q=True, ro=True, ws=True)

        if ignore_translate:
            scale = (1, 1, 1)
        else:
            scale = cmds.getAttr(joint_name + '.scale')[0]

        return [proxy_name, translate, rotate, scale]


    # Validate Proxy and Write file
    is_valid = True
    successfully_created_file = False

    # Check for existing rig
    desired_elements = []
    for jnt in biped_data.joints_default:
        desired_elements.append(biped_data.joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. (Click on "Help" for more details)')


    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=biped_data.script_name + ' - PPOSE File (*.ppose);;' + biped_data.script_name + ' - JSON File (*.json)', dialogStyle=2, okCaption= 'Export', caption= 'Exporting Proxy Pose for "' + biped_data.script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:

        export_dict = {'gt_auto_biped_version' : biped_data.script_version, 'gt_auto_biped_export_method' : 'world-space'}

        no_rot_string_list = ['elbow', 'spine', 'neck', 'head', 'jaw', 'cog', 'eye', 'shoulder', 'ankle', 'knee', 'hip']
        left_offset_rot_string_list = ['left_clavicle', 'left_wrist']
        right_offset_rot_string_list = ['right_clavicle', 'right_wrist']
        no_rot_list = []
        left_offset_rot_list = []
        right_offset_rot_list = []

        for jnt_key in biped_data.joints_default:
            for string in no_rot_string_list:
                if string in jnt_key:
                    no_rot_list.append(jnt_key)
            for string in left_offset_rot_string_list:
                if string in jnt_key:
                    left_offset_rot_list.append(jnt_key)
            for string in right_offset_rot_string_list:
                if string in jnt_key:
                    right_offset_rot_list.append(jnt_key)

        for jnt_key in biped_data.joints_default:
            jnt = biped_data.joints_default.get(jnt_key)


            if jnt_key in no_rot_list:
                values_to_store = extract_transform_joint_to_proxy(jnt, ignore_rotate=True)
            elif jnt_key in left_offset_rot_list:
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True )
                temp_grp_dir = cmds.group(name='temp_dir' + str(random.random()), world=True, empty=True )
                temp_grp_up = cmds.group(name='temp_up' + str(random.random()), world=True, empty=True )
                cmds.delete(cmds.parentConstraint(jnt, temp_grp))
                cmds.delete(cmds.parentConstraint(jnt, temp_grp_dir))
                cmds.delete(cmds.parentConstraint(jnt, temp_grp_up))
                cmds.move(1, temp_grp_dir, x=True, relative=True, objectSpace=True)
                cmds.move(1, temp_grp_up, z=True, relative=True, objectSpace=True)
                cmds.delete(cmds.aimConstraint(temp_grp_dir, temp_grp, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,1,0), worldUpType='vector', worldUpVector=(0,1,0)))
                cmds.delete(cmds.aimConstraint(temp_grp_up, temp_grp, offset=(0,0,0), aimVector=(0,1,0), upVector=(0,1,0), worldUpType='vector', worldUpVector=(0,1,0), skip=('y','z')))
                values_to_store = extract_transform_joint_to_proxy(jnt, no_jnt_extraction=temp_grp)
                cmds.delete(temp_grp)
                cmds.delete(temp_grp_dir)
                cmds.delete(temp_grp_up)
            elif jnt_key in right_offset_rot_list:
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True )
                temp_grp_dir = cmds.group(name='temp_dir' + str(random.random()), world=True, empty=True )
                temp_grp_up = cmds.group(name='temp_up' + str(random.random()), world=True, empty=True )
                cmds.delete(cmds.parentConstraint(jnt, temp_grp))
                cmds.delete(cmds.parentConstraint(jnt, temp_grp_dir))
                cmds.delete(cmds.parentConstraint(jnt, temp_grp_up))
                cmds.move(1, temp_grp_dir, x=True, relative=True, objectSpace=True)
                cmds.move(-1, temp_grp_up, z=True, relative=True, objectSpace=True)
                cmds.delete(cmds.aimConstraint(temp_grp_dir, temp_grp, offset=(0,0,0), aimVector=(1,0,0), upVector=(0,1,0), worldUpType='vector', worldUpVector=(0,1,0)))
                cmds.delete(cmds.aimConstraint(temp_grp_up, temp_grp, offset=(0,0,0), aimVector=(0,1,0), upVector=(0,1,0), worldUpType='vector', worldUpVector=(0,1,0), skip=('y','z')))
                values_to_store = extract_transform_joint_to_proxy(jnt, no_jnt_extraction=temp_grp)
                cmds.delete(temp_grp)
                cmds.delete(temp_grp_dir)
                cmds.delete(temp_grp_up)
            else:
                values_to_store = extract_transform_joint_to_proxy(jnt)
            
            for proxy_key in biped_data.elements_default:
                if jnt_key.replace('_' + JNT_SUFFIX, '_proxy_crv') == proxy_key:
                    export_dict[proxy_key] = values_to_store
        
        # Heel Pivot Extraction 
        for pivot in ['left_heel_pivotGrp', 'right_heel_pivotGrp']:
            if cmds.objExists(pivot):
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True)
                cmds.delete(cmds.parentConstraint(pivot, temp_grp))
                pivot_pos = extract_transform_joint_to_proxy(temp_grp, ignore_translate=False, ignore_rotate=True, ignore_scale=True)
                cmds.delete(temp_grp)
                export_dict[pivot.replace('_pivotGrp', '_proxy_pivot')] = (pivot.replace('_pivotGrp', '_pivot_proxy'), pivot_pos[1], pivot_pos[2], pivot_pos[3])
 
        try: 
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy Pose</span><span style=\"color:#FFFFFF;\"> extracted.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose extracted to the file "' + pose_file + '".')
        except Exception as e:
            print (e)
            successfully_created_file = False
            cmds.warning('Couldn\'t write to file. Please make sure the exporting directory is accessible.')


# Build UI
if __name__ == '__main__':
    build_gui_auto_biped_rig()

    # try:
    #     del biped_data
    # except:
    # #     pass
    # biped_data = GTBipedRiggerData()
    # # biped_data.settings = biped_data.settings_default
    #
    #
    # # print('#####')
    # biped_data.settings['body_column_height'] = 123
    # # print(biped_data.settings)
    # reset_persistent_settings(biped_data)
    # # print(biped_data.settings_default)
