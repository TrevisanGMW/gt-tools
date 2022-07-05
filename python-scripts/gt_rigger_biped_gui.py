"""
 GT Biped Rigger GUI
 github.com/TrevisanGMW - 2020-12-08

 2022-06-20
 Added tabs to GUI (Biped/Base, Facial, Corrective, Settings)
 Updated settings management, fixed persistent settings issue

 2022-06-20
 Added Facial and Corrective Tabs to GUI
 Refactored a few function names to avoid conflicts
 Added basic operations and future operations buttons to facial and corrective tabs
 Added "Add Influence Options" to facial and corrective tabs

 2022-06-28
 Added logging for better debugging
 Added settings for corrective rigging
 Fixed reset persistent settings to include facial and corrective settings

 2022-06-30
 Updated (biped) extract pose from generated rig to prioritize "main_ctrl" string attribute

 2022-07-01
 Added "Extract Proxy Pose From Facial Rig" and "Import Pose" (Facial)

 2022-07-04
 Added validation for creating facial or corrective proxy/rig

"""
from shiboken2 import wrapInstance
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QIcon
from maya import OpenMayaUI
from gt_rigger_biped_logic import *
from gt_rigger_data import *
import gt_generate_icons
import gt_rigger_corrective_logic
import gt_rigger_facial_logic
import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import json
import sys
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_biped_gui")
logger.setLevel(20)  # DEBUG 10, INFO 20, WARNING 30, ERROR 40, CRITICAL 50

# Data Objects
data_biped = GTBipedRiggerData()
get_persistent_settings(data_biped)
data_facial = GTBipedRiggerFacialData()
get_persistent_settings(data_facial)
data_corrective = GTBipedRiggerCorrectiveData()
get_persistent_settings(data_corrective)


# Main Dialog ============================================================================
def build_gui_auto_biped_rig():
    """  Creates the main GUI for GT Auto Biped Rigger """

    # Unpack Common Variables
    script_name = data_biped.script_name
    script_version = data_biped.script_version

    window_name = 'build_gui_auto_biped_rig'
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Main GUI Start Here =================================================================================
    gui_auto_biped_rig_window = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                            titleBar=True, minimizeButton=False, maximizeButton=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    main_window_title = script_name
    if data_biped.debugging:
        title_bgc_color = (1, .3, .3)
        main_window_title = 'Debugging Mode Activated'

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 280)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 206), (3, 50), (4, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main)
    cmds.text(' ', bgc=title_bgc_color)  # Tiny Empty Space
    cmds.text(main_window_title, bgc=title_bgc_color, fn='boldLabelFont', align='left')
    cmds.button(label='Help', bgc=title_bgc_color, c=lambda x: build_help_gui_auto_biped_rig(script_name))
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)

    form = cmds.formLayout(p=body_column)
    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
    cmds.formLayout(form, edit=True,
                    attachForm=((tabs, 'top', 0), (tabs, 'left', 0), (tabs, 'bottom', 0), (tabs, 'right', 0)))

    # ####################################### BIPED/BASE TAB #######################################
    cw_biped_two_buttons = [(1, 127), (2, 127)]
    cs_biped_two_buttons = [(1, 0), (2, 5)]
    biped_rigger_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 2)], p=tabs)

    # ######## Generate Icon Images ########
    # Icon
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True)

    # Create Proxy Icon
    create_proxy_btn_ico = icons_folder_dir + 'gt_abr_create_proxy.png'

    if os.path.isdir(icons_folder_dir) and os.path.exists(create_proxy_btn_ico) is False:
        gt_generate_icons.generate_image_from_library(create_proxy_btn_ico, 'biped_rigger_proxy_btn')

    # Create Rig Icon
    create_rig_btn_ico = icons_folder_dir + 'gt_abr_create_rig.png'

    if os.path.isdir(icons_folder_dir) and os.path.exists(create_rig_btn_ico) is False:
        gt_generate_icons.generate_image_from_library(create_rig_btn_ico, 'biped_rigger_rig_btn')

    # Step 1
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 1 - Biped Proxy:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_proxy_btn_ico, label='Create Biped Proxy',
                        statusBarMessage='Creates a proxy/guide elements so the user can determine '
                                         'the character\'s shape.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_biped_operation('create_proxy'))

    # Step 2
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 2 - Biped Pose:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Reset Proxy', bgc=(.3, .3, .3), c=lambda x: reset_proxy())
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=biped_rigger_tab)
    cmds.button(label='Mirror Right to Left', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('right_to_left'))
    cmds.button(label='Mirror Left to Right', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('left_to_right'))

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Import Biped Pose', bgc=(.3, .3, .3), c=lambda x: import_biped_proxy_pose())
    cmds.button(label='Export Biped Pose', bgc=(.3, .3, .3), c=lambda x: export_biped_proxy_pose())
    cmds.separator(h=4, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.button(label='Delete Proxy', bgc=(.3, .3, .3), c=lambda x: delete_proxy())

    # Step 3
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 3 - Create Biped Rig:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_rig_btn_ico, label='Create Biped Rig',
                        statusBarMessage='Creates the control rig. It uses the transform data found in the proxy to '
                                         'determine how to create the skeleton, controls and mechanics.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_biped_operation('create_controls'))

    # Step 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 4 - Skin Weights:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=biped_rigger_tab)
    cmds.button(label='Select Skinning Joints', bgc=(.3, .3, .3), c=lambda x: select_skinning_joints_biped())
    cmds.button(label='Bind Skin Options', bgc=(.3, .3, .3), c=lambda x: mel.eval('SmoothBindSkinOptions;'))

    cmds.separator(h=5, style='none')  # Empty Space

    # Utilities
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Utilities:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.button(label='Add Custom Rig Interface to Shelf', bgc=(.3, .3, .3), c=lambda x: add_rig_interface_button())
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=biped_rigger_tab)
    cmds.button(label='Toggle Label Visibility', bgc=(.3, .3, .3), c=lambda x: gtu_uniform_jnt_label_toggle())
    cmds.button(label='Attach to HumanIK', bgc=(.3, .3, .3), c=lambda x: define_biped_humanik('auto_biped'))

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=biped_rigger_tab)
    cmds.button(label='Toggle Rigging Specific Attributes', bgc=(.3, .3, .3), c=lambda x: toggle_rigging_attr())
    cmds.separator(h=6, style='none')  # Empty Space
    cmds.button(label='Extract Proxy Pose From Biped Rig', bgc=(.3, .3, .3), c=lambda x: extract_biped_proxy_pose())

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=10, style='none', p=body_column)  # Empty Space

    # ####################################### FACIAL TAB #######################################
    facial_rigger_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 2)], p=tabs)

    # Step 1 - Facial
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 1 - Facial Proxy:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_proxy_btn_ico, label='Create Facial Proxy',
                        statusBarMessage='Creates a proxy/guide elements so the user can determine '
                                         'the character\'s facial shape.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_facial_operation('create_proxy'))

    # Step 2 - Facial
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 2 - Facial Pose:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Reset Proxy', bgc=(.3, .3, .3), c=lambda x: reset_proxy(proxy_target='facial'))
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=facial_rigger_tab)
    cmds.button(label='Mirror Right to Left', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('right_to_left', 'facial'))
    cmds.button(label='Mirror Left to Right', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('left_to_right', 'facial'))

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Import Facial Pose', bgc=(.3, .3, .3), c=lambda x: import_facial_proxy_pose())
    cmds.button(label='Export Facial Pose', bgc=(.3, .3, .3), c=lambda x: export_facial_proxy_pose())
    cmds.separator(h=4, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=facial_rigger_tab)
    cmds.button(label='Delete Proxy', bgc=(.3, .3, .3), c=lambda x: delete_proxy(proxy_target='facial'))

    # Step 3 - Facial
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=facial_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 3 - Create Facial Rig:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_rig_btn_ico, label='Create Facial Rig',
                        statusBarMessage='Creates the control rig. It uses the transform data found in the proxy to '
                                         'determine how to create the skeleton, controls and mechanics.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_facial_operation('create_controls'))

    # Step 4 - Facial
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=facial_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 4 - Skin Weights:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=facial_rigger_tab)
    cmds.button(label='Select Skinning Joints', bgc=(.3, .3, .3), c=lambda x: select_skinning_joints_facial(), en=0)
    cmds.button(label='Add Influence Options', bgc=(.3, .3, .3), c=lambda x: mel.eval('AddInfluenceOptions;'))

    # Utilities - Facial
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=facial_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Utilities:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=facial_rigger_tab)
    cmds.button(label='Merge Facial Rig with Biped Rig', bgc=(.3, .3, .3),
                c=lambda x: validate_facial_operation('merge'))
    cmds.separator(h=6, style='none')  # Empty Space
    cmds.button(label='Extract Proxy Pose From Facial Rig', bgc=(.3, .3, .3),
                c=lambda x: extract_facial_proxy_pose())

    # ####################################### CORRECTIVE TAB #######################################
    corrective_rigger_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 2)], p=tabs)

    # Step 1 - Corrective
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 1 - Corrective Proxy:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_proxy_btn_ico, label='Create Corrective Proxy',
                        statusBarMessage='Creates a proxy/guide elements so the user can determine '
                                         'the character\'s facial shape.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_corrective_operation('create_proxy'))

    # Step 2 - Corrective
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 2 - Corrective Pose:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Reset Proxy', bgc=(.3, .3, .3), c=lambda x: reset_proxy(proxy_target='corrective'))
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=corrective_rigger_tab)
    cmds.button(label='Mirror Right to Left', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('right_to_left', 'corrective'))
    cmds.button(label='Mirror Left to Right', bgc=(.3, .3, .3), c=lambda x: mirror_proxy('left_to_right', 'corrective'))
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=corrective_rigger_tab)
    cmds.button(label='Delete Proxy', bgc=(.3, .3, .3), c=lambda x: delete_proxy(proxy_target='corrective'))

    # Step 3 - Corrective
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=corrective_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 3 - Create Corrective Rig:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.iconTextButton(style='iconAndTextVertical', image1=create_rig_btn_ico, label='Create Corrective Rig',
                        statusBarMessage='Creates the control rig. It uses the transform data found in the proxy to '
                                         'determine how to create the skeleton, controls and mechanics.',
                        olc=[1, 0, 0], enableBackground=True, bgc=[.4, .4, .4], h=80,
                        command=lambda: validate_corrective_operation('create_controls'))

    # Step 4 - Corrective
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=corrective_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Step 4 - Skin Weights:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=cw_biped_two_buttons, cs=cs_biped_two_buttons, p=corrective_rigger_tab)
    cmds.button(label='Select Skinning Joints', bgc=(.3, .3, .3), c=lambda x: select_skinning_joints_biped(), en=False)
    cmds.button(label='Add Influence Options', bgc=(.3, .3, .3), c=lambda x: mel.eval('AddInfluenceOptions;'))

    # Utilities - Corrective
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=corrective_rigger_tab)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Utilities:', font='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 259)], cs=[(1, 0)], p=corrective_rigger_tab)
    cmds.button(label='Merge Corrective Rig with Biped Rig', bgc=(.3, .3, .3),
                c=lambda x: validate_corrective_operation('merge'))
    cmds.separator(h=6, style='none')  # Empty Space
    cmds.button(label='Extract Proxy Pose From Corrective Rig', bgc=(.3, .3, .3),
                c=lambda x: extract_corrective_proxy_pose())

    # ####################################### SETTINGS TAB #######################################

    settings_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 0)], p=tabs)
    # General Settings
    enabled_bgc_color = (.4, .4, .4)
    disabled_bgc_color = (.3, .3, .3)
    cmds.separator(h=5, style='none', p=settings_tab)  # Empty Space
    cmds.text('  Biped/Base Settings:', font='boldLabelFont', p=settings_tab)
    cmds.separator(h=5, style='none', p=settings_tab)  # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 210), (3, 20)], cs=[(1, 10)], p=settings_tab)

    # Use Real-time skeleton
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Use Real-time Skeleton', value=data_biped.settings.get('using_no_ssc_skeleton'),
                  ebg=True, cc=lambda x: _invert_stored_setting('using_no_ssc_skeleton', data_biped),
                  en=is_option_enabled)

    realtime_custom_help_message = 'Creates another skeleton without the parameter "Segment Scale Compensate" ' \
                                   'being active. This skeleton inherits the transforms from the controls while ' \
                                   'mimicking the behaviour of the "Segment Scale Compensate" option, essentially ' \
                                   'creating a baked version of this Maya depended system.\nAs this baked version ' \
                                   'does not yet fully support non-uniform scaling, it\'s recommended that you only ' \
                                   'use it if you are planning to later send this rig into a game engine or another ' \
                                   '3d application.\n\nThis will allow you to preserve the stretchy settings ' \
                                   'even in programs that do not support it.'
    realtime_custom_help_title = 'Use Real-time Skeleton'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(realtime_custom_help_message,
                                                     realtime_custom_help_title))

    # Limit Proxy Movement
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Limit Proxy Movement', value=data_biped.settings.get('proxy_limits'),
                  ebg=True, cc=lambda x: _invert_stored_setting('proxy_limits', data_biped),
                  en=is_option_enabled)

    proxy_limit_custom_help_message = 'Unlocks transforms for feet and spine proxy elements. ' \
                                      'This allows for more unconventional character shapes, but makes' \
                                      ' the auto rigger less robust. If this is your first time using it, ' \
                                      'you might want to keep the limits active.'
    proxy_limit_custom_help_title = 'Limit Proxy Movement'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(proxy_limit_custom_help_message,
                                                     proxy_limit_custom_help_title))

    # Force Uniform Control Orientation
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Uniform Control Orientation', value=data_biped.settings.get('uniform_ctrl_orient'),
                  ebg=True, cc=lambda x: _invert_stored_setting('uniform_ctrl_orient', data_biped),
                  en=is_option_enabled)

    uniform_orients_custom_help_message = 'Changes the orientation of most controls to be match the world\'s ' \
                                          'orientation. This means that Z will likely face forward, ' \
                                          'X side and Y up/down.'
    uniform_orients_custom_help_title = 'Uniform Control Orientation'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(uniform_orients_custom_help_message,
                                                     uniform_orients_custom_help_title))

    # Force World-Space IK Orientation
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  World-Space IK Orientation', value=data_biped.settings.get('worldspace_ik_orient'),
                  ebg=True, cc=lambda x: _invert_stored_setting('worldspace_ik_orient', data_biped),
                  en=is_option_enabled)

    ws_ik_orients_custom_help_message = 'Changes the orientation of the IK controls to be match the world\'s ' \
                                        'orientation. This means that Z will face forward, X side and Y up/down.' \
                                        '\n\nThe orientation of the joints will be ignored (not inherited)'
    ws_ik_orients_custom_help_title = 'World-Space IK Orientation'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(ws_ik_orients_custom_help_message,
                                                     ws_ik_orients_custom_help_title))

    # Simplify Spine
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Simplify Spine Joints', value=data_biped.settings.get('simplify_spine'),
                  ebg=True, cc=lambda x: _invert_stored_setting('simplify_spine', data_biped),
                  en=is_option_enabled)

    simplify_spine_custom_help_message = 'The number of spine joints used in the base skinned skeleton is reduced.' \
                                         '\nInstead of creating spine 1, 2, 3, and chest, the auto rigger outputs' \
                                         ' only one spine joint and chest.\n\nThe entire system still exists, within' \
                                         ' the rig, this change only affects the base skeleton (skinned)'
    simplify_spine_custom_help_title = 'Simplify Spine Joints'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(simplify_spine_custom_help_message,
                                                     simplify_spine_custom_help_title))

    # # ####################################### FACIAL SETTINGS ##########################################
    # cmds.separator(h=10, style='none', p=settings_tab)  # Empty Space
    # cmds.text('  Facial Settings:', font='boldLabelFont', p=settings_tab)
    # cmds.separator(h=5, style='none', p=settings_tab)  # Empty Space
    # cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 210), (3, 20)], cs=[(1, 10)], p=settings_tab)
    #
    # # Name
    # is_option_enabled = True
    # current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    # cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    # cmds.checkBox(label='  Simplify Spine Joints', value=data_biped.settings.get('simplify_spine'),
    #               ebg=True, cc=lambda x: _invert_stored_setting('simplify_spine'), en=is_option_enabled)
    #
    # simplify_spine_custom_help_message = ''
    # simplify_spine_custom_help_title = 'Simplify Spine Joints'
    # cmds.button(label='?', bgc=current_bgc_color,
    #             c=lambda x: build_custom_help_window(simplify_spine_custom_help_message,
    #                                                  simplify_spine_custom_help_title))

    # ####################################### CORRECTIVE SETTINGS ##########################################
    cmds.separator(h=10, style='none', p=settings_tab)  # Empty Space
    cmds.text('  Corrective Settings:', font='boldLabelFont', p=settings_tab)
    cmds.separator(h=5, style='none', p=settings_tab)  # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 210), (3, 20)], cs=[(1, 10)], p=settings_tab)

    # Setup Wrist Correctives
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Setup Wrist Correctives', value=data_corrective.settings.get('setup_wrists'),
                  ebg=True, cc=lambda x: _invert_stored_setting('setup_wrists', data_corrective),
                  en=is_option_enabled)

    setup_wrists_custom_help_message = 'Creates Wrist Correctives'
    setup_wrists_custom_help_title = 'Setup Wrist Correctives'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(setup_wrists_custom_help_message,
                                                     setup_wrists_custom_help_title))

    # Setup Elbow Correctives
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Setup Elbow Correctives', value=data_corrective.settings.get('setup_elbows'),
                  ebg=True, cc=lambda x: _invert_stored_setting('setup_elbows', data_corrective),
                  en=is_option_enabled)

    setup_wrists_custom_help_message = 'Creates Elbow Correctives'
    setup_wrists_custom_help_title = 'Setup Elbow Correctives'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(setup_wrists_custom_help_message,
                                                     setup_wrists_custom_help_title))

    # Setup Shoulder Correctives
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Setup Shoulder Correctives', value=data_corrective.settings.get('setup_shoulders'),
                  ebg=True, cc=lambda x: _invert_stored_setting('setup_shoulders', data_corrective),
                  en=is_option_enabled)

    setup_wrists_custom_help_message = 'Creates Shoulder Correctives'
    setup_wrists_custom_help_title = 'Setup Shoulder Correctives'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(setup_wrists_custom_help_message,
                                                     setup_wrists_custom_help_title))

    # Setup Hip Correctives
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Setup Hip Correctives', value=data_corrective.settings.get('setup_hips'),
                  ebg=True, cc=lambda x: _invert_stored_setting('setup_hips', data_corrective),
                  en=is_option_enabled)

    setup_wrists_custom_help_message = 'Creates Hip Correctives'
    setup_wrists_custom_help_title = 'Setup Hip Correctives'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(setup_wrists_custom_help_message,
                                                     setup_wrists_custom_help_title))

    # Setup Knee Correctives
    is_option_enabled = True
    current_bgc_color = enabled_bgc_color if is_option_enabled else disabled_bgc_color
    cmds.text(' ', bgc=current_bgc_color, h=20)  # Tiny Empty Space
    cmds.checkBox(label='  Setup Knee Correctives', value=data_corrective.settings.get('setup_knees'),
                  ebg=True, cc=lambda x: _invert_stored_setting('setup_knees', data_corrective),
                  en=is_option_enabled)

    setup_wrists_custom_help_message = 'Creates Knee Correctives'
    setup_wrists_custom_help_title = 'Setup Knee Correctives'
    cmds.button(label='?', bgc=current_bgc_color,
                c=lambda x: build_custom_help_window(setup_wrists_custom_help_message,
                                                     setup_wrists_custom_help_title))
    # #########################################################################################################
    # Reset Persistent Settings
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=settings_tab)
    #
    cmds.separator(h=25)
    # cmds.separator(h=5, style='none')  # Empty Space
    cmds.button(label='Reset Persistent Settings', bgc=current_bgc_color,
                c=lambda x: _reset_persistent_settings_validation([data_biped, data_facial, data_corrective]))

    # Versions:
    cmds.separator(h=180, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=6, cw=[(1, 35), (2, 35), (3, 35), (4, 35), (5, 50), (6, 35)],
                         cs=[(1, 10), (2, 0), (3, 7), (4, 0), (5, 7)], p=settings_tab)
    cmds.text('Biped: ', font='tinyBoldLabelFont', en=False)
    cmds.text('v' + str(data_biped.script_version), font='tinyBoldLabelFont')
    cmds.text('Facial: ', font='tinyBoldLabelFont', en=False)
    cmds.text('v' + str(data_facial.script_version), font='tinyBoldLabelFont')
    cmds.text('Corrective: ', font='tinyBoldLabelFont', en=False)
    cmds.text('v' + str(data_corrective.script_version), font='tinyBoldLabelFont')
    # cmds.separator(h=5, style='none')  # Empty Space
    # cmds.separator(h=5)  # Empty Space

    # ####################################### END TABS #######################################
    cmds.tabLayout(tabs, edit=True, tabLabel=((biped_rigger_tab, 'Biped/Base'),
                                              (facial_rigger_tab, 'Facial'),
                                              (corrective_rigger_tab, ' Corrective'),
                                              (settings_tab, 'Settings ')))

    # Show and Lock Window
    cmds.showWindow(gui_auto_biped_rig_window)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/HIKcreateControlRig.png')
    widget.setWindowIcon(icon)

    # ### GUI Functions ###
    def _invert_stored_setting(key_string, data_object):
        """
        Used for boolean values, it inverts the value, so if True it becomes False and vice-versa
        
        Args:
            key_string (string) : Key name, used to determine what bool value to flip
            data_object: GT Rigger data object used to update the settings
        """
        data_object.settings[key_string] = not data_object.settings.get(key_string)
        set_persistent_settings(data_object)

    def _reset_persistent_settings_validation(data_objects):
        """
        Resets persistent settings for provided data_objects. e.g. GTBipedRiggerData, GTCorrectiveRiggerData...

        Args:
            data_objects (list) : List of data objects to be reset
        """
        for data_obj in data_objects:
            reset_persistent_settings(data_obj)
            get_persistent_settings(data_obj)

        try:

            cmds.evalDeferred('gt_tools.execute_script("gt_rigger_biped_gui", "build_gui_auto_biped_rig")')
        except Exception as exception:
            logger.debug(str(exception))
            try:
                build_gui_auto_biped_rig()
            except Exception as exception:
                logger.debug(str(exception))
                try:
                    cmds.evalDeferred('gt_rigger.biped_gui.build_gui_auto_biped_rig()')
                except Exception as exception:
                    logger.debug(str(exception))

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_help_gui_auto_biped_rig(script_name):
    """ Creates the Help windows """
    window_name = 'build_help_gui_auto_biped_rig'
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + ' Help', mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout('main_column', p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p='main_column')  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p='main_column')  # Title Column
    cmds.text(script_name + ' Help', bgc=(.4, .4, .4), fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p='main_column')  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p='main_column')
    cmds.text(l='Script for quickly generating an advanced biped rig', align='center', fn='boldLabelFont')
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='For more predictable results execute it in a new scene\n containing only the geometry of the '
                'desired character.', align='center')
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=3, cw=[(1, 28)], cs=[(1, 40)], p='main_column')
    cmds.text(l='Click ', hl=True, highlightColor=[1, 1, 1])
    cmds.text(l='<a href="https://github.com/TrevisanGMW/gt-tools/tree/master/docs#-gt-auto-biped-rigger-">Here</a>',
              hl=True, highlightColor=[1, 1, 1])
    cmds.text(l=' for a more complete documentation.', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p='main_column')

    auto_biped_help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="smallPlainLabelFont")

    text = '[X] Step 1: .\n -Create Proxy:\n   This button creates many temporary curves that will later' \
           '\n   be used to generate the rig.\n\n   The initial scale is the average height of a\n   woman. (160cm)' \
           '\n   Presets for other sizes can be found on Github.\n\n   These are not joints. Please don\'t delete or' \
           ' rename them.\n\n[X] Step 2:\n   Pose the proxy (guide) to match your character.\n\n -Reset Proxy:' \
           '\n   Resets the position and rotation of the proxy elements,\n   essentially "recreating" the proxy.' \
           '\n\n -Mirror Side to Side:\n   Copies the transform data from one side to the other,\n   ' \
           'mirroring the pose.\n\n -Import Pose:\n   Imports a JSON file containing the transforms of the proxy\n  ' \
           'elements. This file is generated using the "Export Pose"\n   function.\n\n -Export Pose:\n   ' \
           'Exports a JSON file containing the transforms of the proxy\n   elements.\n\n -Delete Proxy:\n   ' \
           'Simply deletes the proxy in case you no longer need it.\n\n[X] Step 3:\n   ' \
           'This button creates the control rig. It uses the transform data\n   ' \
           'found in the proxy to determine how to create the skeleton\n   and controls. ' \
           'This function will delete the proxy.\n   Make sure you export it first if you plan to reuse it later.' \
           '\n\n[X] Step 4:\n   Now that the rig has been created, it\'s time to attach it to the\n   geometry.' \
           '\n\n -Select Skinning Joints:\n   Select only joints that should be used when skinning the\n   character.' \
           ' This means that it will not include end joints or\n   the toes.\n\n -Bind Skin Options:\n   ' \
           'Opens the options for the function "Bind Skin" so the desired\n   ' \
           'geometry can attached to the skinning joints.\n   Make sure to use the "Bind to" as "Selected Joints"' \
           '\n\n[X] Utilities:\n   These are utilities that you can use after creating your rig.\n   ' \
           'Please visit the full documentation to learn more about it.'
    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=0, it=text)

    cmds.scrollField(auto_biped_help_scroll_field, e=True, ip=1, it='')  # Bring Back to the Top

    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p='main_column')
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p='main_column')
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p='main_column')
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
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

    Args:
        input_text (string): Text used as help, this is displayed in a scroll fields.
        help_title (optional, string)
    """
    window_name = help_title.replace(" ", "_").replace("-", "_").lower().strip() + "_help_window"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=help_title + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(help_title + ' Help', bgc=(.4, .4, .4), fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================       
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')

    cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)
    cmds.scrollField(help_scroll_field, e=True, ip=1, it='')  # Bring Back to the Top

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        """ Closes help windows """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    # Custom Help Dialog Ends Here =================================================================================


def validate_facial_operation(operation):
    """
    Validates the necessary objects before executing desired function (Facial Rig)
    
    Args:
        operation (string): Name of the desired operation. e.g. "create_proxy" or "create_controls"

    """
    if operation == "merge":
        gt_rigger_facial_logic.merge_facial_elements()
        return

    # Check for existing rig or conflicting names
    undesired_elements = ['facial_rig_grp', 'facialAutomation_grp', 'mouthAutomation_grp']
    for obj in undesired_elements:
        if cmds.objExists(obj):
            cmds.warning('"' + obj + '" found in the scene. This means that you either already created a'
                                     ' rig or you have conflicting names on your objects. '
                                     '(Click on "Help" for more details)')
            return

    if operation == "create_proxy":
        # Check if proxy exists in the scene
        proxy_elements = [data_facial.elements_default.get('main_proxy_grp')]
        for proxy in data_facial.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(data_facial.elements_default.get(proxy))
        for obj in proxy_elements:
            if cmds.objExists(obj):
                cmds.warning('"' + obj + '" found in the scene. Proxy creation already in progress. '
                                         'Delete current proxy or generate a rig before creating a new one.')
                return
        gt_rigger_facial_logic.create_facial_proxy(data_facial)
    elif operation == "create_controls":
        gt_rigger_facial_logic.create_facial_controls(data_facial)


def validate_corrective_operation(operation):
    """
    Validates the necessary objects before executing desired function (Corrective Rig)

    Args:
        operation (string): Name of the desired operation. e.g. "create_proxy" or "create_controls"

    """
    if operation == "merge":
        gt_rigger_corrective_logic.merge_corrective_elements()
        return

    # Check for existing rig or conflicting names
    undesired_elements = ['corrective_rig_grp', 'correctiveAutomation_grp']
    for obj in undesired_elements:
        if cmds.objExists(obj):
            cmds.warning('"' + obj + '" found in the scene. This means that you either already created a'
                                     ' rig or you have conflicting names on your objects. '
                                     '(Click on "Help" for more details)')
            return

    if operation == "create_proxy":
        # Check if proxy exists in the scene
        proxy_elements = [data_corrective.elements_default.get('main_proxy_grp')]
        for proxy in data_corrective.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(data_corrective.elements_default.get(proxy))
        for obj in proxy_elements:
            if cmds.objExists(obj):
                cmds.warning('"' + obj + '" found in the scene. Proxy creation already in progress. '
                                         'Delete current proxy or generate a rig before creating a new one.')
                return
        gt_rigger_corrective_logic.create_corrective_proxy(data_corrective)
    elif operation == "create_controls":
        gt_rigger_corrective_logic.create_corrective_setup(data_corrective)


def validate_biped_operation(operation):
    """
    Validates the necessary objects before executing desired function (Biped/Base Rig)

    Args:
        operation (string): Name of the desired operation. e.g. "create_proxy" or "create_controls"

    """

    # Load Required Plugins
    required_plugins = ['quatNodes', 'matrixNodes']
    for plugin in required_plugins:
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            cmds.loadPlugin(plugin, qt=False)

    is_valid = True
    if operation == 'create_proxy':
        # Starts new instance (clean scene)
        if data_biped.debugging and data_biped.debugging_force_new_scene:
            persp_pos = cmds.getAttr('persp.translate')[0]
            persp_rot = cmds.getAttr('persp.rotate')[0]
            cmds.file(new=True, force=True)
            if data_biped.debugging_keep_cam_transforms:
                cmds.viewFit(all=True)
                cmds.setAttr('persp.tx', persp_pos[0])
                cmds.setAttr('persp.ty', persp_pos[1])
                cmds.setAttr('persp.tz', persp_pos[2])
                cmds.setAttr('persp.rx', persp_rot[0])
                cmds.setAttr('persp.ry', persp_rot[1])
                cmds.setAttr('persp.rz', persp_rot[2])

        # Debugging (Auto deletes generated proxy)
        if data_biped.debugging and data_biped.debugging_auto_recreate:
            try:
                cmds.delete(data_biped.elements_default.get('main_proxy_grp'))
            except Exception as e:
                logger.debug(e)
                pass

        # Check if proxy exists in the scene
        proxy_elements = [data_biped.elements_default.get('main_proxy_grp')]
        for proxy in data_biped.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(data_biped.elements_default.get(proxy))
        for obj in proxy_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. Proxy creation already in progress. '
                                         'Delete current proxy or generate a rig before creating a new one.')

        # Check for existing rig or conflicting names
        undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
        for jnt in data_biped.joints_default:
            undesired_elements.append(data_biped.joints_default.get(jnt))
        for obj in undesired_elements:
            if cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" found in the scene. This means that you either already created a'
                                         ' rig or you have conflicting names on your objects. '
                                         '(Click on "Help" for more details)')

        # If valid, create proxy
        if is_valid:
            function_name = 'GT Auto Biped - Create Proxy'
            cmds.undoInfo(openChunk=True, chunkName=function_name)
            cmds.refresh(suspend=True)
            try:
                create_proxy(data_biped)
            except Exception as e:
                cmds.warning(str(e))
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=function_name)
                cmds.refresh(suspend=False)

        # Debugging (Auto imports proxy)
        if data_biped.debugging and data_biped.debugging_import_proxy and os.path.exists(
                data_biped.debugging_import_path):
            import_biped_proxy_pose(debugging=True, debugging_path=data_biped.debugging_import_path)

    elif operation == 'create_controls':
        # Starts new instance (clean scene)
        if data_biped.debugging and data_biped.debugging_force_new_scene:
            persp_pos = cmds.getAttr('persp.translate')[0]
            persp_rot = cmds.getAttr('persp.rotate')[0]
            cmds.file(new=True, force=True)
            if data_biped.debugging_keep_cam_transforms:
                cmds.viewFit(all=True)
                cmds.setAttr('persp.tx', persp_pos[0])
                cmds.setAttr('persp.ty', persp_pos[1])
                cmds.setAttr('persp.tz', persp_pos[2])
                cmds.setAttr('persp.rx', persp_rot[0])
                cmds.setAttr('persp.ry', persp_rot[1])
                cmds.setAttr('persp.rz', persp_rot[2])

        # Debugging (Auto deletes generated rig)
        if data_biped.debugging and data_biped.debugging_auto_recreate:
            try:
                if cmds.objExists('rig_grp'):
                    cmds.delete('rig_grp')
                if cmds.objExists(data_biped.elements.get('main_proxy_grp')):
                    cmds.delete(data_biped.elements.get('main_proxy_grp'))
                create_proxy(data_biped)
                # Debugging (Auto imports proxy)
                if data_biped.debugging_import_proxy and os.path.exists(data_biped.debugging_import_path):
                    import_biped_proxy_pose(debugging=True, debugging_path=data_biped.debugging_import_path)
            except Exception as e:
                logger.debug(e)
                pass

        # Validate Proxy
        if not cmds.objExists(data_biped.elements.get('main_proxy_grp')):
            logger.debug('"' + str(data_biped.elements.get('main_proxy_grp')) + '" not found.')
            is_valid = False
            cmds.warning("Proxy couldn't be found. "
                         "Make sure you first create a proxy (guide objects) before generating a rig.")

        proxy_elements = [data_biped.elements.get('main_proxy_grp')]
        for proxy in data_biped.elements_default:
            if '_crv' in proxy:
                proxy_elements.append(data_biped.elements.get(proxy))
        for obj in proxy_elements:
            if not cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" is missing. '
                             'Create a new proxy and make sure NOT to rename or delete any of its elements.')

        # If valid, create rig
        if is_valid:
            function_name = 'GT Auto Biped - Create Rig'
            if data_biped.debugging:
                create_controls(data_biped)
            else:
                cmds.undoInfo(openChunk=True, chunkName=function_name)
                cmds.refresh(suspend=True)
                try:
                    create_controls(data_biped)
                except Exception as e:
                    raise e
                finally:
                    cmds.undoInfo(closeChunk=True, chunkName=function_name)
                    cmds.refresh(suspend=False)

            # Debugging (Auto binds joints to provided geo)
            if data_biped.debugging and data_biped.debugging_bind_rig and cmds.objExists(data_biped.debugging_bind_geo):
                cmds.select(d=True)
                select_skinning_joints_biped()
                selection = cmds.ls(selection=True)
                if data_biped.debugging_bind_heatmap:
                    cmds.skinCluster(selection, data_biped.debugging_bind_geo, bindMethod=2, heatmapFalloff=0.68,
                                     toSelectedBones=True, smoothWeights=0.5, maximumInfluences=4)
                else:
                    cmds.skinCluster(selection, data_biped.debugging_bind_geo, bindMethod=1, toSelectedBones=True,
                                     smoothWeights=0.5, maximumInfluences=4)
                cmds.select(d=True)


def select_skinning_joints_biped():
    """ Selects joints that should be used during the skinning process """

    # Check for existing rig
    is_valid = True
    desired_elements = []
    for jnt in data_biped.joints_default:
        desired_elements.append(data_biped.joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. '
                                     '(Click on "Help" for more details)')

    if is_valid:
        skinning_joints = []
        for obj in data_biped.joints_default:
            if '_end' + JNT_SUFFIX.capitalize() not in data_biped.joints_default.get(obj) \
                    and '_toe' not in data_biped.joints_default.get(obj) \
                    and 'root_' not in data_biped.joints_default.get(obj) \
                    and 'driver' not in data_biped.joints_default.get(obj):
                parent = cmds.listRelatives(data_biped.joints_default.get(obj), parent=True)[0] or ''
                if parent != 'skeleton_grp':
                    skinning_joints.append(data_biped.joints_default.get(obj))
        cmds.select(skinning_joints)
        if 'left_forearm_jnt' not in skinning_joints or 'right_forearm_jnt' not in skinning_joints:
            for obj in ['left_forearm_jnt', 'right_forearm_jnt']:
                try:
                    cmds.select(obj, add=True)
                except Exception as e:
                    logger.debug(e)
                    pass


def select_skinning_joints_facial():
    """ Selects joints that should be used during the skinning process """

    # Check for existing rig
    is_valid = True
    desired_elements = []
    for jnt in data_biped.joints_default:
        desired_elements.append(data_biped.joints_default.get(jnt))
    for obj in desired_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. '
                                     '(Click on "Help" for more details)')

    if is_valid:
        skinning_joints = []
        for obj in data_biped.joints_default:
            if '_end' + JNT_SUFFIX.capitalize() not in data_biped.joints_default.get(obj) \
                    and '_toe' not in data_biped.joints_default.get(obj) \
                    and 'root_' not in data_biped.joints_default.get(obj) \
                    and 'driver' not in data_biped.joints_default.get(obj):
                parent = cmds.listRelatives(data_biped.joints_default.get(obj), parent=True)[0] or ''
                if parent != 'skeleton_grp':
                    skinning_joints.append(data_biped.joints_default.get(obj))
        cmds.select(skinning_joints)
        if 'left_forearm_jnt' not in skinning_joints or 'right_forearm_jnt' not in skinning_joints:
            for obj in ['left_forearm_jnt', 'right_forearm_jnt']:
                try:
                    cmds.select(obj, add=True)
                except Exception as e:
                    logger.debug(str(e))


def reset_proxy(suppress_warning=False, proxy_target='base'):
    """
    Resets proxy elements to their original position

    Args:
        suppress_warning (bool): Whether it should give inView feedback
        proxy_target (string) : Defaults to "base", determines which proxy to mirror: "base", "facial" or "corrective"

    """

    is_reset = False
    attributes_set_zero = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'followHip']
    attributes_set_one = ['sx', 'sy', 'sz', 'v']
    proxy_elements = []

    data_obj = ''
    if proxy_target == 'base':
        data_obj = data_biped
    elif proxy_target == 'facial':
        data_obj = data_facial
    elif proxy_target == 'corrective':
        data_obj = data_corrective

    for proxy in data_obj.elements_default:
        if '_crv' in proxy or proxy.endswith('_pivot'):
            proxy_elements.append(data_obj.elements_default.get(proxy))
    for obj in proxy_elements:
        if cmds.objExists(obj):
            for attr in attributes_set_zero:
                try:
                    cmds.setAttr(obj + '.' + attr, 0)
                    is_reset = True
                except Exception as exception:
                    logger.debug(str(exception))
            for attr in attributes_set_one:
                try:
                    cmds.setAttr(obj + '.' + attr, 1)
                    is_reset = True
                except Exception as exception:
                    logger.debug(str(exception))

    if is_reset:
        if not suppress_warning:
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(
                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                     'Proxy</span><span style=\"color:#FFFFFF;\"> was reset!</span>',
                pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.warning('No proxy found. Nothing was reset.')


def delete_proxy(suppress_warning=False, proxy_target='base'):
    """
    Deletes current proxy/guide curves

    Args:
        suppress_warning (bool): Whether it should give warnings (feedback)
        proxy_target (string): Which proxy it should affect: "base" (default), "facial", "corrective"

    """

    is_deleted = False
    to_delete_elements = []
    if proxy_target == 'base':
        to_delete_elements = [data_biped.elements.get('main_proxy_grp'), data_biped.elements.get('main_crv')]
    elif proxy_target == 'facial':
        to_delete_elements = [data_facial.elements.get('main_proxy_grp')]
    elif proxy_target == 'corrective':
        to_delete_elements = [data_corrective.elements.get('main_proxy_grp')]

    for obj in to_delete_elements:
        if cmds.objExists(obj) and is_deleted is False:
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


def mirror_proxy(operation, proxy_target='base'):
    """
    Mirrors the proxy curves pose by copying translate, rotate and scale attributes from one side to the other

    Args:
        operation (string) : what direction to mirror. "left_to_right" (+X to -X) or "right_to_left" (-X to +X)
        proxy_target (string) : Defaults to "base", determines which proxy to mirror: "base", "facial" or "corrective"

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
                cmds.setAttr(target + '.' + attr, source_attr * -1)

    # Validate Proxy
    is_valid = True
    # Determine system to be mirrored
    if proxy_target == 'base':
        data_obj = data_biped
    elif proxy_target == 'facial':
        data_obj = data_facial
    elif proxy_target == 'corrective':
        data_obj = data_corrective
    else:
        data_obj = ''
        is_valid = False
        cmds.warning('Proxy target not specified or invalid. Please check the ')

    # Check existence
    proxy_group = data_obj.elements.get('main_proxy_grp')
    if not cmds.objExists(proxy_group):
        is_valid = False
        print('Missing: "' + proxy_group + '". (Renaming or adding name spaces may interfere with it)')
        cmds.warning("Proxy group couldn't be found. "
                     "Make sure you first create a proxy (guide objects) before mirroring it.")

    proxy_elements = [data_obj.elements.get('main_proxy_grp')]
    for proxy in data_obj.elements_default:
        if '_crv' in proxy:
            proxy_elements.append(data_obj.elements.get(proxy))
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
        for obj in data_obj.elements:
            if obj.startswith('left_') and ('_crv' in obj or '_pivot' in obj):
                left_elements.append(data_obj.elements.get(obj))
            elif obj.startswith('right_') and ('_crv' in obj or '_pivot' in obj):
                right_elements.append(data_obj.elements.get(obj))

        for left_obj in left_elements:
            for right_obj in right_elements:
                if left_obj.replace('left', '') == right_obj.replace('right', ''):

                    if operation == 'left_to_right':
                        print(left_obj, right_obj)
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


def define_biped_humanik(character_name):
    """
    Auto creates a character definition for GT Auto Biped. (It overwrites any definition with the same name)

    Args:
        character_name (string): Name of the HIK character

    """
    is_operation_valid = True

    try:
        if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.loadPlugin("mayaHIK", quiet=True)
    except Exception as exception:
        logger.debug(exception)

    # Check for existing rig
    exceptions = [data_biped.joints_default.get('spine01_jnt'),
                  data_biped.joints_default.get('spine02_jnt'),
                  data_biped.joints_default.get('spine03_jnt'),
                  # biped_data.joints_default.get('spine03_jnt'),
                  ]
    desired_elements = []
    for jnt in data_biped.joints_default:
        if not data_biped.joints_default.get(jnt).endswith('endJnt'):
            desired_elements.append(data_biped.joints_default.get(jnt))
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
        except Exception as exception:
            logger.debug(str(exception))
            print('#' * 80)
            if not os.path.exists(maya_location + '/scripts/others/hikGlobalUtils.mel'):
                print('The module "' + maya_location + "/scripts/others/hikGlobalUtils.mel\" couldn't be found.")
            if not os.path.exists(maya_location + '/scripts/others/hikCharacterControlsUI.mel'):
                print(
                    'The module "' + maya_location + "/scripts/others/hikCharacterControlsUI.mel\" couldn't be found.")
            if not os.path.exists(maya_location + '/scripts/others/hikDefinitionOperations.mel'):
                print(
                    'The module "' + maya_location + "/scripts/others/hikDefinitionOperations.mel\" couldn't be found.")
            print('#' * 80)
            cmds.warning("HumanIK modules couldn't be found. You might have to define the character manually. "
                         "Open script editor for more information.")
            is_operation_valid = False

    # Create Character Definition
    if is_operation_valid:
        try:
            joints = data_biped.joints_default  # Unpack

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
                mel.eval(
                    'setCharacterObject("' + joints.get('left_forearm_jnt') + '", "' + character_name + '", 193,0);')
                mel.eval(
                    'setCharacterObject("' + joints.get('right_forearm_jnt') + '", "' + character_name + '", 195,0);')
            except Exception as exception:
                logger.info(str(exception))
                pass

            mel.eval('hikUpdateDefinitionUI;')
            mel.eval('hikToggleLockDefinition();')

            cmds.select(d=True)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(
                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">HumanIK</span>'
                                     '<span style=\"color:#FFFFFF;\"> character and definition created!</span>',
                pos='botLeft', fade=True, alpha=.9)

        except Exception as exception:
            logger.info(str(exception))
            cmds.warning('An error happened when creating the definition. '
                         'You might have to assign your joints manually.')


def export_biped_proxy_pose():
    """
    Exports a JSON file containing the translation, rotation and scale data from every proxy curve (to export a pose)
    Added a variable called "gt_rigger_biped_export_method" after v1.3, so the extraction method can be stored.

    """
    # Validate Proxy and Write file
    is_valid = True
    successfully_created_file = False
    pose_file = None
    script_name = data_biped.script_name
    file_extension = data_biped.proxy_storage_variables.get('file_extension')

    proxy_elements = [data_biped.elements.get('main_proxy_grp')]
    for proxy in data_biped.elements_default:
        if '_crv' in proxy:
            proxy_elements.append(data_biped.elements.get(proxy))
    for obj in proxy_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            warning = '"' + obj + '"'
            warning += ' is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.'
            cmds.warning(warning)

    if is_valid:
        file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
        file_filter += script_name + ' - JSON File (*.json)'
        file_name = cmds.fileDialog2(fileFilter=file_filter,
                                     dialogStyle=2, okCaption='Export',
                                     caption='Exporting Proxy Pose for "' + script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:
        export_dict = {data_biped.proxy_storage_variables.get('script_source'): data_biped.script_version,
                       data_biped.proxy_storage_variables.get('export_method'): 'object-space'}
        for obj in data_biped.elements_default:
            if '_crv' in obj:
                translate = cmds.getAttr(data_biped.elements_default.get(obj) + '.translate')[0]
                rotate = cmds.getAttr(data_biped.elements_default.get(obj) + '.rotate')[0]
                scale = cmds.getAttr(data_biped.elements_default.get(obj) + '.scale')[0]
                to_save = [data_biped.elements_default.get(obj), translate, rotate, scale]
                export_dict[obj] = to_save

            if obj.endswith('_pivot'):
                if cmds.objExists(data_biped.elements_default.get(obj)):
                    translate = cmds.getAttr(data_biped.elements_default.get(obj) + '.translate')[0]
                    rotate = cmds.getAttr(data_biped.elements_default.get(obj) + '.rotate')[0]
                    scale = cmds.getAttr(data_biped.elements_default.get(obj) + '.scale')[0]
                    to_save = [data_biped.elements_default.get(obj), translate, rotate, scale]
                    export_dict[obj] = to_save

        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                                    'Proxy Pose</span><span style=\"color:#FFFFFF;\"> '
                                                    'exported.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose exported to the file "' + pose_file + '".')
        except Exception as exception:
            successfully_created_file = False
            logger.info(str(exception))
            logger.info("Successfully Created_ File: " + str(successfully_created_file))
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


def export_facial_proxy_pose():
    """
    Exports a JSON file containing the translation, rotation and scale data from every proxy curve (to export a pose)
    Added a variable called "gt_rigger_facial_export_method" after v1.3, so the extraction method can be stored.
    """
    # Validate Proxy and Write file
    is_valid = True
    successfully_created_file = False
    pose_file = None
    file_extension = data_facial.proxy_storage_variables.get('file_extension')
    script_name = data_facial.script_name

    proxy_elements = [data_facial.elements.get('main_proxy_grp')]
    for proxy in data_facial.elements_default:
        if '_crv' in proxy:
            proxy_elements.append(data_facial.elements.get(proxy))
    for obj in proxy_elements:
        if not cmds.objExists(obj) and is_valid:
            is_valid = False
            warning = '"' + obj + '"'
            warning += ' is missing. Create a new proxy and make sure NOT to rename or delete any of its elements.'
            cmds.warning(warning)

    if is_valid:
        file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
        file_filter += script_name + ' - JSON File (*.json)'
        file_name = cmds.fileDialog2(fileFilter=file_filter,
                                     dialogStyle=2, okCaption='Export',
                                     caption='Exporting Proxy Pose for "' + script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:
        export_dict = {data_facial.proxy_storage_variables.get('script_source'): data_facial.script_version,
                       data_facial.proxy_storage_variables.get('export_method'): 'object-space'}
        for obj in data_facial.elements_default:
            if '_crv' in obj or 'main_root' in obj:
                translate = cmds.getAttr(data_facial.elements_default.get(obj) + '.translate')[0]
                rotate = cmds.getAttr(data_facial.elements_default.get(obj) + '.rotate')[0]
                scale = cmds.getAttr(data_facial.elements_default.get(obj) + '.scale')[0]
                to_save = [data_facial.elements_default.get(obj), translate, rotate, scale]
                export_dict[obj] = to_save
        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                                    'Proxy Pose</span><span style=\"color:#FFFFFF;\"> '
                                                    'exported.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose exported to the file "' + pose_file + '".')
        except Exception as exception:
            successfully_created_file = False
            logger.info(str(exception))
            logger.info("Successfully Created_ File: " + str(successfully_created_file))
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


def import_biped_proxy_pose(debugging=False, debugging_path=''):
    """
    Imports a JSON file containing the translation, rotation and scale data for every proxy curve
    (exported using the "export_proxy_pose" function)
    Uses the imported data to set the translation, rotation and scale position of every proxy curve
    Uses the function "delete_proxy()" to recreate it if necessary
    Uses the function "reset_proxy()" to clean proxy before importing

    It now checks import method to use the proper method when setting attributes.
    Exporting using the export button uses "setAttr", extract functions will use "xform" instead.

    Args:
        debugging (bool): If debugging, the function will attempt to autoload the file provided in the
                          "debugging_path" parameter
        debugging_path (string): Debugging path for the import function

    """

    import_method = 'object-space'
    pose_file = None
    _proxy_storage = data_biped.proxy_storage_variables
    script_source = _proxy_storage.get('script_source')
    export_method = _proxy_storage.get('export_method')
    file_extension = _proxy_storage.get('file_extension')
    script_name = data_biped.script_name

    if not debugging:
        file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
        file_filter += script_name + ' - JSON File (*.json)'
        file_name = cmds.fileDialog2(fileFilter=file_filter,
                                     dialogStyle=2, fileMode=1, okCaption='Import',
                                     caption='Importing Proxy Pose for "' + script_name + '"') or []
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
                    if not data.get(script_source):
                        is_valid_file = False
                        cmds.warning("Imported file doesn't seem to be compatible or is missing data.")
                    else:
                        import_version = float(re.sub("[^0-9]", "", str(data.get(script_source))))
                        logger.debug(str(import_version))

                    if data.get(export_method):
                        import_method = data.get(export_method)
                        logger.debug(str(import_method))

                    is_valid_scene = True
                    # Check for existing rig or conflicting names
                    undesired_elements = ['rig_grp', 'skeleton_grp', 'controls_grp', 'rig_setup_grp']
                    for jnt in data_biped.joints_default:
                        undesired_elements.append(data_biped.joints_default.get(jnt))
                    for obj in undesired_elements:
                        if cmds.objExists(obj) and is_valid_scene:
                            is_valid_scene = False
                            cmds.warning(
                                '"' + obj + '" found in the scene. This means that you either already created a '
                                            'rig or you have conflicting names on your objects. '
                                            '(Click on "Help" for more details)')

                    if is_valid_scene:
                        # Check for Proxy
                        proxy_exists = True

                        proxy_elements = []
                        for proxy in data_biped.elements_default:
                            if '_crv' in proxy:
                                proxy_elements.append(data_biped.elements.get(proxy))
                        for obj in proxy_elements:
                            if not cmds.objExists(obj) and proxy_exists:
                                proxy_exists = False
                                delete_proxy(suppress_warning=True)
                                validate_biped_operation('create_proxy')
                                cmds.warning('Current proxy was missing elements, a new one was created.')

                    if is_valid_file and is_valid_scene:
                        if import_method == 'world-space':
                            reset_proxy(suppress_warning=True)
                            sorted_pairs = []
                            for proxy in data:
                                if proxy != script_source and proxy != export_method:
                                    current_object = data.get(proxy)  # Name, T, R, S
                                    if cmds.objExists(current_object[0]):
                                        long_name = cmds.ls(current_object[0], l=True) or []
                                        number_of_parents = len(long_name[0].split('|'))
                                        sorted_pairs.append((current_object, number_of_parents))

                                    sorted_pairs.sort(key=lambda x: x[1], reverse=True)

                            # Scale (Children First)
                            for obj in sorted_pairs:
                                current_object = obj[0]
                                if cmds.objExists(current_object[0]):
                                    set_unlocked_os_attr(current_object[0], 'sx', current_object[3][0])
                                    set_unlocked_os_attr(current_object[0], 'sy', current_object[3][1])
                                    set_unlocked_os_attr(current_object[0], 'sz', current_object[3][2])

                            # Translate and Rotate (Parents First)
                            for obj in reversed(sorted_pairs):
                                current_object = obj[0]
                                if cmds.objExists(current_object[0]):
                                    set_unlocked_ws_attr(current_object[0], 'translate', current_object[1])
                                    set_unlocked_ws_attr(current_object[0], 'rotate', current_object[2])

                            # Set Transfer Pole Vectors Again
                            for obj in reversed(sorted_pairs):
                                current_object = obj[0]
                                if 'knee' in current_object[0] or 'elbow' in current_object[0]:
                                    if cmds.objExists(current_object[0]):
                                        set_unlocked_ws_attr(current_object[0], 'translate', current_object[1])
                                        set_unlocked_ws_attr(current_object[0], 'rotate', current_object[2])

                        else:  # Object-Space
                            for proxy in data:
                                if proxy != script_source and proxy != export_method:
                                    current_object = data.get(proxy)  # Name, T, R, S
                                    if cmds.objExists(current_object[0]):
                                        set_unlocked_os_attr(current_object[0], 'tx', current_object[1][0])
                                        set_unlocked_os_attr(current_object[0], 'ty', current_object[1][1])
                                        set_unlocked_os_attr(current_object[0], 'tz', current_object[1][2])
                                        set_unlocked_os_attr(current_object[0], 'rx', current_object[2][0])
                                        set_unlocked_os_attr(current_object[0], 'ry', current_object[2][1])
                                        set_unlocked_os_attr(current_object[0], 'rz', current_object[2][2])
                                        set_unlocked_os_attr(current_object[0], 'sx', current_object[3][0])
                                        set_unlocked_os_attr(current_object[0], 'sy', current_object[3][1])
                                        set_unlocked_os_attr(current_object[0], 'sz', current_object[3][2])

                        if not debugging:
                            unique_message = '<' + str(random.random()) + '>'
                            cmds.inViewMessage(
                                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy'
                                                     ' Pose</span><span style=\"color:#FFFFFF;\"> imported!</span>',
                                pos='botLeft', fade=True, alpha=.9)
                            sys.stdout.write('Pose imported from the file "' + pose_file + '".')

                except Exception as exception:
                    logger.info(str(exception))
                    cmds.warning('An error occurred when importing the pose. Make sure you imported the correct JSON '
                                 'file. (Click on "Help" for more info)')
        except Exception as exception:
            file_exists = False
            logger.debug(exception)
            logger.debug('File exists:', str(file_exists))
            cmds.warning("Couldn't read the file. Please make sure the selected file is accessible.")


def import_facial_proxy_pose(debugging=False, debugging_path=''):
    """
    Imports a JSON file containing the translation, rotation and scale data for every proxy curve
    (exported using the "export_proxy_pose" function)
    Uses the imported data to set the translation, rotation and scale position of every proxy curve
    Uses the function "delete_proxy()" to recreate it if necessary
    Uses the function "reset_proxy()" to clean proxy before importing

    It now checks import method to use the proper method when setting attributes.
    Exporting using the export button uses "setAttr", extract functions will use "xform" instead.

    Args:
        debugging (bool): If debugging, the function will attempt to autoload the file provided in the
                          "debugging_path" parameter
        debugging_path (string): Debugging path for the import function

    """

    pose_file = None
    _proxy_storage = data_facial.proxy_storage_variables
    script_source = _proxy_storage.get('script_source')
    export_method = _proxy_storage.get('export_method')
    file_extension = _proxy_storage.get('file_extension')
    script_name = data_facial.script_name

    if not debugging:
        file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
        file_filter += script_name + ' - JSON File (*.json)'
        file_name = cmds.fileDialog2(fileFilter=file_filter,
                                     dialogStyle=2, fileMode=1, okCaption='Import',
                                     caption='Importing Proxy Pose for "' + script_name + '"') or []
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

                    if not data.get(script_source):
                        is_valid_file = False
                        cmds.warning("Imported file doesn't seem to be compatible or is missing data.")
                    else:
                        import_version = float(re.sub("[^0-9]", "", str(data.get(script_source))))
                        logger.debug(str(import_version))

                    if data.get(export_method):
                        import_method = data.get(export_method)
                        logger.debug(str(import_method))

                    is_valid_scene = True
                    # Check for existing rig or conflicting names
                    undesired_elements = ['facial_rig_grp']
                    for jnt in data_facial.joints_default:
                        undesired_elements.append(data_facial.joints_default.get(jnt))
                    for obj in undesired_elements:
                        if cmds.objExists(obj) and is_valid_scene:
                            is_valid_scene = False
                            cmds.warning(
                                '"' + obj + '" found in the scene. This means that you either already created a '
                                            'rig or you have conflicting names on your objects. '
                                            '(Click on "Help" for more details)')

                    if is_valid_scene:
                        # Check for Proxy
                        proxy_exists = True

                        proxy_elements = []
                        for proxy in data_facial.elements_default:
                            if '_crv' in proxy or 'main_root' in proxy:
                                proxy_elements.append(data_facial.elements.get(proxy))
                        for obj in proxy_elements:
                            if not cmds.objExists(obj) and proxy_exists:
                                proxy_exists = False
                                delete_proxy(suppress_warning=True, proxy_target='facial')
                                validate_facial_operation('create_proxy')
                                cmds.warning('Current proxy was missing elements, a new one was created.')

                    if is_valid_file and is_valid_scene:
                        for proxy in data:
                            if proxy != script_source and proxy != export_method:
                                current_object = data.get(proxy)  # Name, T, R, S
                                if cmds.objExists(current_object[0]):
                                    set_unlocked_os_attr(current_object[0], 'tx', current_object[1][0])
                                    set_unlocked_os_attr(current_object[0], 'ty', current_object[1][1])
                                    set_unlocked_os_attr(current_object[0], 'tz', current_object[1][2])
                                    set_unlocked_os_attr(current_object[0], 'rx', current_object[2][0])
                                    set_unlocked_os_attr(current_object[0], 'ry', current_object[2][1])
                                    set_unlocked_os_attr(current_object[0], 'rz', current_object[2][2])
                                    set_unlocked_os_attr(current_object[0], 'sx', current_object[3][0])
                                    set_unlocked_os_attr(current_object[0], 'sy', current_object[3][1])
                                    set_unlocked_os_attr(current_object[0], 'sz', current_object[3][2])

                        if not debugging:
                            unique_message = '<' + str(random.random()) + '>'
                            cmds.inViewMessage(
                                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Proxy'
                                                     ' Pose</span><span style=\"color:#FFFFFF;\"> imported!</span>',
                                pos='botLeft', fade=True, alpha=.9)
                            sys.stdout.write('Pose imported from the file "' + pose_file + '".')

                except Exception as exception:
                    logger.info(str(exception))
                    cmds.warning('An error occurred when importing the pose. Make sure you imported the correct JSON '
                                 'file. (Click on "Help" for more info)')
        except Exception as exception:
            file_exists = False
            logger.debug(exception)
            logger.debug('File exists:', str(file_exists))
            cmds.warning("Couldn't read the file. Please make sure the selected file is accessible.")


def extract_facial_proxy_pose():
    """
    Extracts the proxy pose from a generated rig into a JSON file. (Facial)
    Useful when the user forgot to save it and generated the rig already.
    """

    # Validate Proxy and Write file
    successfully_created_file = False
    pose_file = None
    script_name = data_facial.script_name
    file_extension = data_facial.proxy_storage_variables.get('file_extension')
    proxy_attr_name = data_facial.proxy_storage_variables.get('attr_name')

    # Easy method (main_ctrl string)
    main_ctrl = 'head_ctrl'
    if cmds.objExists(main_ctrl):
        proxy_attr = main_ctrl + '.' + proxy_attr_name
        if cmds.objExists(proxy_attr):
            export_dict = cmds.getAttr(proxy_attr)
            try:
                export_dict = json.loads(str(export_dict))
            except Exception as e:
                logger.warning(str(e))
                cmds.warning('Failed to decode JSON data.')
                return
        else:
            cmds.warning('Missing required attribute: "' + proxy_attr + '"')
            return
    else:
        cmds.warning('Missing required control: "' + main_ctrl + '"')
        return

    file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
    file_filter += script_name + ' - JSON File (*.json)'
    file_name = cmds.fileDialog2(
        fileFilter=file_filter,
        dialogStyle=2, okCaption='Export',
        caption='Exporting Proxy Pose for "' + script_name + '"') or []
    if len(file_name) > 0:
        pose_file = file_name[0]
        successfully_created_file = True

    if successfully_created_file:
        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(
                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                     'Proxy Pose</span><span style=\"color:#FFFFFF;\"> extracted.</span>',
                pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose extracted to the file "' + pose_file + '".')
        except Exception as exception:
            logger.info(str(exception))
            # successfully_created_file = False
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


def extract_biped_proxy_pose():
    """
    Extracts the proxy pose from a generated rig into a JSON file. (Biped)
    Useful when the user forgot to save it and generated the rig already.

    Exports using "xform" and world space for more flexibility (scale is ignored)

    """

    def extract_transform_joint_to_proxy(joint_name, ignore_translate=False, ignore_rotate=False, ignore_scale=False,
                                         no_jnt_extraction=None):
        """
        Extracts the world-space for Translate and Rotate and the object-space Scale of the provided joint
        then returns a list with proxy name, translate list, rotate list, and scale list
        [ proxy_name, translate_xyz, rotate_xyz, scale_xyz ]

        Args:
            joint_name (string): Name of the joint used to extract the transform
            ignore_translate (bool): If active, it returns default translate values (0,0,0) instead of extracting it
            ignore_rotate (bool): If active, it returns default rotate values (0,0,0) instead of extracting it
            ignore_scale (bool): If active, it returns default scale values (1,1,1) instead of extracting it
            no_jnt_extraction (bool): In case using another object to match it, you can provide it here

        Returns:
            extracted_pair (list): [proxy_name, translate_xyz, rotate_xyz, scale_xyz]
        """

        proxy_name = joint_name.replace(JNT_SUFFIX, PROXY_SUFFIX).replace('end' + JNT_SUFFIX.capitalize(),
                                                                          'end' + PROXY_SUFFIX.capitalize())

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

        if ignore_scale:
            scale = (1, 1, 1)
        else:
            scale = cmds.getAttr(joint_name + '.scale')[0]

        return [proxy_name, translate, rotate, scale]

    def force_extract_from_joints():
        """
        Extract proxy using current joints (less accurate)
        Returns:
            extracted_export_dict (dict): Proxy dictionary to be written on to a file
        """
        _proxy_storage = data_biped.proxy_storage_variables
        extracted_export_dict = {_proxy_storage.get('script_source'): data_biped.script_version,
                                 _proxy_storage.get('export_method'): 'world-space'}

        no_rot_string_list = ['elbow', 'spine', 'neck', 'head', 'jaw', 'cog', 'eye', 'shoulder', 'ankle', 'knee', 'hip']
        left_offset_rot_string_list = ['left_clavicle', 'left_wrist']
        right_offset_rot_string_list = ['right_clavicle', 'right_wrist']
        no_rot_list = []
        left_offset_rot_list = []
        right_offset_rot_list = []

        for jnt_key in data_biped.joints_default:
            for string in no_rot_string_list:
                if string in jnt_key:
                    no_rot_list.append(jnt_key)
            for string in left_offset_rot_string_list:
                if string in jnt_key:
                    left_offset_rot_list.append(jnt_key)
            for string in right_offset_rot_string_list:
                if string in jnt_key:
                    right_offset_rot_list.append(jnt_key)

        for jnt_key in data_biped.joints_default:
            current_jnt = data_biped.joints_default.get(jnt_key)

            if jnt_key in no_rot_list:
                values_to_store = extract_transform_joint_to_proxy(current_jnt, ignore_rotate=True)
            elif jnt_key in left_offset_rot_list:
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True)
                temp_grp_dir = cmds.group(name='temp_dir' + str(random.random()), world=True, empty=True)
                temp_grp_up = cmds.group(name='temp_up' + str(random.random()), world=True, empty=True)
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp))
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp_dir))
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp_up))
                cmds.move(1, temp_grp_dir, x=True, relative=True, objectSpace=True)
                cmds.move(1, temp_grp_up, z=True, relative=True, objectSpace=True)
                cmds.delete(cmds.aimConstraint(temp_grp_dir, temp_grp, offset=(0, 0, 0), aimVector=(1, 0, 0),
                                               upVector=(0, 1, 0), worldUpType='vector', worldUpVector=(0, 1, 0)))
                cmds.delete(
                    cmds.aimConstraint(temp_grp_up, temp_grp, offset=(0, 0, 0), aimVector=(0, 1, 0), upVector=(0, 1, 0),
                                       worldUpType='vector', worldUpVector=(0, 1, 0), skip=('y', 'z')))
                values_to_store = extract_transform_joint_to_proxy(current_jnt, no_jnt_extraction=temp_grp)
                cmds.delete(temp_grp)
                cmds.delete(temp_grp_dir)
                cmds.delete(temp_grp_up)
            elif jnt_key in right_offset_rot_list:
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True)
                temp_grp_dir = cmds.group(name='temp_dir' + str(random.random()), world=True, empty=True)
                temp_grp_up = cmds.group(name='temp_up' + str(random.random()), world=True, empty=True)
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp))
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp_dir))
                cmds.delete(cmds.parentConstraint(current_jnt, temp_grp_up))
                cmds.move(1, temp_grp_dir, x=True, relative=True, objectSpace=True)
                cmds.move(-1, temp_grp_up, z=True, relative=True, objectSpace=True)
                cmds.delete(cmds.aimConstraint(temp_grp_dir, temp_grp, offset=(0, 0, 0), aimVector=(1, 0, 0),
                                               upVector=(0, 1, 0), worldUpType='vector', worldUpVector=(0, 1, 0)))
                cmds.delete(
                    cmds.aimConstraint(temp_grp_up, temp_grp, offset=(0, 0, 0), aimVector=(0, 1, 0), upVector=(0, 1, 0),
                                       worldUpType='vector', worldUpVector=(0, 1, 0), skip=('y', 'z')))
                values_to_store = extract_transform_joint_to_proxy(current_jnt, no_jnt_extraction=temp_grp)
                cmds.delete(temp_grp)
                cmds.delete(temp_grp_dir)
                cmds.delete(temp_grp_up)
            else:
                values_to_store = extract_transform_joint_to_proxy(current_jnt)

            for proxy_key in data_biped.elements_default:
                if jnt_key.replace('_' + JNT_SUFFIX, '_proxy_crv') == proxy_key:
                    extracted_export_dict[proxy_key] = values_to_store

        # Heel Pivot Extraction
        for pivot in ['left_heel_pivotGrp', 'right_heel_pivotGrp']:
            if cmds.objExists(pivot):
                temp_grp = cmds.group(name='temp_' + str(random.random()), world=True, empty=True)
                cmds.delete(cmds.parentConstraint(pivot, temp_grp))
                pivot_pos = extract_transform_joint_to_proxy(temp_grp, ignore_translate=False, ignore_rotate=True,
                                                             ignore_scale=True)
                cmds.delete(temp_grp)
                extracted_export_dict[pivot.replace('_pivotGrp', '_proxy_pivot')] = (
                    pivot.replace('_pivotGrp', '_pivot_proxy'), pivot_pos[1], pivot_pos[2], pivot_pos[3])

        return extracted_export_dict

    # ############################### extract_biped_proxy_pose main function ############################

    # Validate Proxy and Write file
    is_valid = True
    successfully_created_file = False
    pose_file = None
    needs_joints = True
    export_dict = {}
    file_extension = data_biped.proxy_storage_variables.get('file_extension')
    proxy_attr_name = data_biped.proxy_storage_variables.get('attr_name')
    script_name = data_biped.script_name

    # Easy method (main_ctrl string)
    main_ctrl = 'main_ctrl'
    if cmds.objExists(main_ctrl):
        proxy_attr = main_ctrl + '.' + proxy_attr_name
        if cmds.objExists(proxy_attr):
            export_dict = cmds.getAttr(proxy_attr)
            try:
                export_dict = json.loads(str(export_dict))
                needs_joints = False
            except Exception as e:
                logger.debug(str(e))

    # Check for existing rig
    if needs_joints:
        desired_elements = ['main_ctrl']
        for jnt in data_biped.joints_default:
            desired_elements.append(data_biped.joints_default.get(jnt))
        for obj in desired_elements:
            if not cmds.objExists(obj) and is_valid:
                is_valid = False
                cmds.warning('"' + obj + '" is missing. This means that it was already renamed or deleted. '
                                         '(Click on "Help" for more details)')

    if is_valid:
        file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
        file_filter += script_name + ' - JSON File (*.json)'
        file_name = cmds.fileDialog2(
            fileFilter=file_filter,
            dialogStyle=2, okCaption='Export',
            caption='Exporting Proxy Pose for "' + script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:
        if needs_joints:
            export_dict = force_extract_from_joints()
        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(
                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                     'Proxy Pose</span><span style=\"color:#FFFFFF;\"> extracted.</span>',
                pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose extracted to the file "' + pose_file + '".')
        except Exception as exception:
            logger.info(str(exception))
            # successfully_created_file = False
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


def extract_corrective_proxy_pose():
    """
    Extracts the proxy pose from a generated rig into a JSON file. (Corrective)
    Useful when the user forgot to save it and generated the rig already.
    """

    # Validate Proxy and Write file
    successfully_created_file = False
    pose_file = None
    script_name = data_corrective.script_name
    file_extension = data_corrective.proxy_storage_variables.get('file_extension')
    proxy_attr_name = data_corrective.proxy_storage_variables.get('attr_name')

    # Easy method (main_ctrl string)
    main_ctrl = 'main_ctrl'
    if cmds.objExists(main_ctrl):
        proxy_attr = main_ctrl + '.' + proxy_attr_name
        if cmds.objExists(proxy_attr):
            export_dict = cmds.getAttr(proxy_attr)
            try:
                export_dict = json.loads(str(export_dict))
            except Exception as e:
                logger.warning(str(e))
                cmds.warning('Failed to decode JSON data.')
                return
        else:
            cmds.warning('Missing required attribute: "' + proxy_attr + '"')
            return
    else:
        cmds.warning('Missing required control: "' + main_ctrl + '"')
        return

    file_filter = script_name + ' - ' + file_extension.upper() + ' File (*.' + file_extension + ');;'
    file_filter += script_name + ' - JSON File (*.json)'
    file_name = cmds.fileDialog2(
        fileFilter=file_filter,
        dialogStyle=2, okCaption='Export',
        caption='Exporting Proxy Pose for "' + script_name + '"') or []
    if len(file_name) > 0:
        pose_file = file_name[0]
        successfully_created_file = True

    if successfully_created_file:
        try:
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(
                amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                                     'Proxy Pose</span><span style=\"color:#FFFFFF;\"> extracted.</span>',
                pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose extracted to the file "' + pose_file + '".')
        except Exception as exception:
            logger.info(str(exception))
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


# Build UI
if __name__ == '__main__':
    logger.setLevel(10)
    build_gui_auto_biped_rig()
