"""
 GT Render Checklist - Check your Maya scene before submitting to a render farm or simply batch rendering.
 github.com/TrevisanGMW/gt-tools -  2020-06-11
 Tested on Maya 2019, 2020 - Windows 10
 
 When creating a new checklist, change these items:
    script_name - variable content
    build_gui_gt_render_checklist() - name of the function
    build_gui_help_gt_render_checklist() - name of the function
    
 1.1 - 2020-07-25
    User no longer needs to remove slashes from custom path. Script manages it.
    Settings are now persistent. (You can reset them in the help menu)
    New function added: "Other Network Paths" checks for paths for the following nodes
        Audio Nodes, Mash Audio Nodes, nCache Nodes,Maya Fluid Cache Nodes,
        Arnold Volumes/Standins/Lights, Redshift Proxy/Volume/Normal/Lights,
        Alembic/BIF/GPU Cache,Golaem Common and Cache Nodes

 1.2 - 2020-11-15
    Changed a few UI elements and colors

 1.3 - 2020-12-05
    Fixed issue where checklist wouldn't update without bifrost loaded
    Added support for non-unique objects to non-manifold checks
    Fixed typos in the help text
    Fixed issue where spaces would cause resolution check to fail
    
 1.4 - 2021-05-12
    Made script compatible with Python 3 (Maya 2022+)
    
 1.4.1 - 2021-08-27
    Added PATCH field to the version 11.11.(11)
    Changed default expected network path and file paths
    
 1.4.2 - 2021-09-03
    Added import line for fileTexturePathResolver

 1.4.3 - 2022-07-18
    Some PEP8 Cleanup

 1.4.4 - 2022-07-21
    A bit more PEP8 Cleanup
    Fixed settings issue where the UI would get bigger

 Todo:
    Add checks for xgen
    Create a better error handling option for the total texture count function
    
"""
import maya.cmds as cmds
import maya.mel as mel
import logging
import copy
from maya import OpenMayaUI as OpenMayaUI

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_render_checklist")
logger.setLevel(logging.INFO)

# Checklist Name
script_name = "GT Render Checklist"

# Versions
script_version = "1.4.4"
maya_version = cmds.about(version=True)

# Status Colors
def_color = 0.3, 0.3, 0.3
pass_color = (0.17, 1.0, 0.17)
warning_color = (1.0, 1.0, 0.17)
error_color = (1.0, 0.17, 0.17)
exception_color = 0.2, 0.2, 0.2

# Checklist Items - Item Number [Name, Expected Value]
checklist_items = {0: ["Frame Rate", "film"],
                   1: ["Scene Units", "cm"],
                   2: ["Output Resolution", ["1920", "1080"]],
                   3: ["Total Texture Count", [40, 50]],
                   4: ["Network File Paths", ["C:\\"]],  # Uses startswith and ignores slashes
                   5: ["Network Reference Paths", ["C:\\"]],  # Uses startswith and ignores slashes
                   6: ["Unparented Objects", 0],
                   7: ["Total Triangle Count", [1800000, 2000000]],
                   8: ["Total Poly Object Count", [90, 100]],
                   9: ["Shadow Casting Lights", [2, 3]],
                   10: ["RS Shadow Casting Lights", [3, 4]],
                   11: ["Ai Shadow Casting Lights", [3, 4]],
                   12: ["Default Object Names", 0],
                   13: ["Objects Assigned to lambert1", 0],
                   14: ["Ngons", 0],
                   15: ["Non-manifold Geometry", 0],
                   16: ["Empty UV Sets", 0],
                   17: ["Frozen Transforms", 0],
                   18: ["Animated Visibility", 0],
                   19: ["Non Deformer History", 0],
                   20: ["Textures Color Space", 0],
                   21: ["Other Network Paths", ["C:\\"]]
                   }

# Store Default Values for Resetting
settings_default_checklist_values = copy.deepcopy(checklist_items)

# Checklist Settings
checklist_settings = {"is_settings_visible": False,
                      "checklist_column_height": 0,
                      "checklist_buttons_height": 0,
                      "settings_text_fields": []
                      }


def get_persistent_settings_render_checklist():
    """
    Checks if persistent settings for GT Render Checklist exists and transfer them to the settings dictionary.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    """
    # Check if there is anything stored
    stored_setup_exists = cmds.optionVar(exists="gt_render_checklist_setup")

    if stored_setup_exists:
        stored_checklist_items = {}
        try:
            stored_checklist_items = eval(str(cmds.optionVar(q="gt_render_checklist_setup")))
            for stored_item in stored_checklist_items:
                for item in checklist_items:
                    if stored_item == item:
                        checklist_items[item][1] = stored_checklist_items.get(stored_item)[1]
        except Exception as e:
            logger.debug(str(e))
            print("Couldn't load persistent settings, try resetting it in the help menu.")


def set_persistent_settings_render_checklist():
    """
    Stores persistent settings for GT Render Checklist.
    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)
    It assumes that persistent settings were stored using the cmds.optionVar function.
    """
    cmds.optionVar(sv=('gt_render_checklist_setup', str(checklist_items)))


def reset_persistent_settings_render_checklist():
    """ Resets persistent settings for GT Render Checklist """
    cmds.optionVar(remove='gt_render_checklist_setup')
    get_persistent_settings_render_checklist()
    build_gui_gt_render_checklist()
    build_gui_help_gt_render_checklist()
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')


# Build GUI - Main Function ==================================================================================
def build_gui_gt_render_checklist():
    window_name = "build_gui_gt_render_checklist"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + '  (v' + script_version + ')', mnb=False, mxb=False, s=True)

    main_column = cmds.columnLayout()

    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, h=1, w=1)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.separator(h=14, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=4, cw=[(1, 10), (2, 190), (3, 60), (4, 40)], cs=[(1, 10), (2, 0), (3, 0)], p=main_column)

    cmds.text(" ", bgc=title_bgc_color)
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    settings_btn = cmds.button(l="Settings", bgc=title_bgc_color, c=lambda x: update_gui_settings())
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_gt_render_checklist())
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # For the separator
    cmds.separator(h=8)
    cmds.separator(h=5, style='none')  # Empty Space

    # Settings Column  ==========================================================
    settings_column = cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 0)], h=1, p=main_column)

    cmds.rowColumnLayout(nc=3, cw=[(1, 150), (2, 65), (3, 63)], cs=[(1, 19), (2, 6), (3, 6)])

    # Header
    cmds.text(l="Operation", align="left")
    cmds.text(l='Warning', align="center")
    cmds.text(l='Expected', align="center")
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')

    # Settings : 
    font_size = 'smallPlainLabelFont'
    items_for_settings = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 21]  # Allow user to update expected values
    items_with_warnings = [3, 7, 8, 9, 10, 11]  # Allow users to update warning values too

    def create_settings_items(items, items_for_settings, items_with_warnings):
        for item in items:
            # item_id = checklist_items.get(item)[0].lower().replace(" ", "_").replace("-", "_")
            cmds.text(l=checklist_items.get(item)[0] + ': ', align="left")

            # Items with warnings
            if item in items_with_warnings:
                cmds.textField('settings_warning_' + str(item), tx=checklist_items.get(item)[1][0], h=14,
                               font=font_size)
                checklist_settings.get('settings_text_fields').append('settings_warning_' + str(item))
            else:
                cmds.textField(en=False, h=14)

            # Items for settings only
            if item in items_for_settings:
                if item not in items_with_warnings:
                    if isinstance(checklist_items.get(item)[1], list):
                        combined_values = ''
                        for array_item in checklist_items.get(item)[1]:
                            combined_values = str(combined_values) + str(array_item) + ', '
                        if len(checklist_items.get(item)[1]) > 0:
                            combined_values = combined_values[:-2]
                        cmds.textField('settings_list_error_' + str(item), tx=combined_values, h=14, font=font_size)
                        checklist_settings.get('settings_text_fields').append('settings_list_error_' + str(item))
                    else:
                        cmds.textField('settings_1d_error_' + str(item), tx=checklist_items.get(item)[1], h=14,
                                       font=font_size)
                        checklist_settings.get('settings_text_fields').append('settings_1d_error_' + str(item))
                else:
                    cmds.textField('settings_2d_error_' + str(item), tx=checklist_items.get(item)[1][1], h=14,
                                   font=font_size)
                    checklist_settings.get('settings_text_fields').append('settings_2d_error_' + str(item))
            else:
                cmds.textField(en=False, h=14, font=font_size)

    create_settings_items(checklist_items, items_for_settings, items_with_warnings)

    # Checklist Column  ==========================================================
    checklist_column = cmds.rowColumnLayout(nc=3, cw=[(1, 165), (2, 35), (3, 90)], cs=[(1, 20), (2, 6), (3, 6)],
                                            p=main_column)

    # Header
    cmds.text(l="Operation", align="left")
    cmds.text(l='Status', align="left")
    cmds.text(l='Info', align="center")
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')

    # Build Checklist 
    def create_checklist_items(items):
        for item in items:
            item_id = checklist_items.get(item)[0].lower().replace(" ", "_").replace("-", "_")
            cmds.text(l=checklist_items.get(item)[0] + ': ', align="left")
            cmds.button("status_" + item_id, l='', h=14, bgc=def_color)
            cmds.text("output_" + item_id, l='...', align="center")

    create_checklist_items(checklist_items)

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # For the separator
    cmds.separator(h=8, style='none')  # Empty Space
    cmds.separator(h=8)

    # Checklist Buttons ==========================================================
    checklist_buttons = cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='Generate Report', h=30, c=lambda args: checklist_generate_report())
    cmds.separator(h=10, style='none')
    cmds.button(l='Refresh', h=30, c=lambda args: checklist_refresh())
    cmds.separator(h=8, style='none')

    settings_buttons = cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column, h=1)
    cmds.separator(h=9, style='none')
    save_load_row = cmds.rowColumnLayout(nc=2, cw=[(1, 145), (2, 145), ], cs=[(1, 0), (2, 10)], p=settings_buttons,
                                         h=30)
    cmds.button(l='Import Settings', h=30, c=lambda args: settings_import_state(), p=save_load_row)
    cmds.button(l='Export Settings', h=30, c=lambda args: settings_export_state(), p=save_load_row)
    cmds.separator(h=10, style='none', p=settings_buttons)
    cmds.button(l='Reset to Default Values', h=30, c=lambda args: settings_apply_changes(reset_default=True),
                p=settings_buttons)
    cmds.separator(h=8, style='none', p=settings_buttons)

    def update_gui_settings():
        if not checklist_settings.get('is_settings_visible'):
            checklist_settings["is_settings_visible"] = True

            cmds.button(settings_btn, e=True, l='Apply', bgc=(.6, .6, .6))

            # Hide Checklist Items
            checklist_settings["checklist_column_height"] = cmds.rowColumnLayout(checklist_column, q=True, h=True)
            cmds.rowColumnLayout(checklist_column, e=True, h=1)

            # Show Settings Items
            cmds.rowColumnLayout(settings_column, e=True, h=(checklist_settings.get('checklist_column_height')))

            # Hide Checklist Buttons
            checklist_settings["checklist_buttons_height"] = cmds.rowColumnLayout(checklist_buttons, q=True, h=True)
            cmds.rowColumnLayout(checklist_buttons, e=True, h=1)

            # Show Settings Buttons
            cmds.rowColumnLayout(settings_buttons, e=True, h=checklist_settings.get('checklist_buttons_height'))
        else:
            checklist_settings["is_settings_visible"] = False
            cmds.rowColumnLayout(checklist_column, e=True, h=checklist_settings.get('checklist_column_height'))
            cmds.rowColumnLayout(checklist_buttons, e=True, h=checklist_settings.get('checklist_buttons_height'))
            cmds.rowColumnLayout(settings_column, e=True, h=1)
            cmds.rowColumnLayout(settings_buttons, e=True, h=1)
            cmds.button(settings_btn, e=True, l='Settings', bgc=title_bgc_color)
            settings_apply_changes()
            set_persistent_settings_render_checklist()

            # Lock Window

    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/checkboxOn.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends ==========================================================


def checklist_refresh():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)

    check_frame_rate()
    check_scene_units()
    check_output_resolution()
    check_total_texture_count()
    check_network_file_paths()
    check_network_reference_paths()
    check_unparented_objects()
    check_total_triangle_count()
    check_total_poly_object_count()
    check_shadow_casting_light_count()
    check_rs_shadow_casting_light_count()
    check_ai_shadow_casting_light_count()
    check_default_object_names()
    check_objects_assigned_to_lambert1()
    check_ngons()
    check_non_manifold_geometry()
    check_empty_uv_sets()
    check_frozen_transforms()
    check_animated_visibility()
    check_non_deformer_history()
    check_textures_color_space()
    check_other_network_paths()

    # Clear Selection
    cmds.selectMode(object=True)
    cmds.select(clear=True)

    # Reselect Previous Selection
    cmds.select(current_selection)


def checklist_generate_report():
    # Save Current Selection For Later
    current_selection = cmds.ls(selection=True)

    report_strings = [check_frame_rate(),
                      check_scene_units(),
                      check_output_resolution(),
                      check_total_texture_count(),
                      check_network_file_paths(),
                      check_network_reference_paths(),
                      check_unparented_objects(),
                      check_total_triangle_count(),
                      check_total_poly_object_count(),
                      check_shadow_casting_light_count(),
                      check_rs_shadow_casting_light_count(),
                      check_ai_shadow_casting_light_count(),
                      check_default_object_names(),
                      check_objects_assigned_to_lambert1(),
                      check_ngons(),
                      check_non_manifold_geometry(),
                      check_empty_uv_sets(),
                      check_frozen_transforms(),
                      check_animated_visibility(),
                      check_non_deformer_history(),
                      check_textures_color_space(),
                      check_other_network_paths(),
                      ]

    # Clear Selection
    cmds.selectMode(object=True)
    cmds.select(clear=True)

    # Show Report
    export_report_to_txt(report_strings)

    # Reselect Previous Selection
    cmds.select(current_selection)


# Creates Help GUI
def build_gui_help_gt_render_checklist():
    window_name = "build_gui_help_gt_render_checklist"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    checklist_spacing = 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='This script performs a series of checks to detect common', align="left")
    cmds.text(l='issues that are often accidentally ignored/unnoticed.', align="left")

    # Checklist Status =============
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Checklist Status:', align="left", fn="boldLabelFont")
    cmds.text(l='These are also buttons, you can click on them for extra functions:', align="left",
              fn="smallPlainLabelFont")
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 35), (2, 265)], cs=[(1, 10), (2, 10)], p="main_column")
    cmds.button(l='', h=14, bgc=def_color,
                c=lambda args: print_message('Default color, means that it was not yet tested.',
                                             as_heads_up_message=True))
    cmds.text(l='- Default color, not yet tested.', align="left", fn="smallPlainLabelFont")

    cmds.button(l='', h=14, bgc=pass_color,
                c=lambda args: print_message('Pass color, means that no issues were found.', as_heads_up_message=True))
    cmds.text(l='- Pass color, no issues were found.', align="left", fn="smallPlainLabelFont")

    cmds.button(l='', h=14, bgc=warning_color,
                c=lambda args: print_message('Warning color, some possible issues were found',
                                             as_heads_up_message=True))
    cmds.text(l='- Warning color, some possible issues were found.', align="left", fn="smallPlainLabelFont")

    cmds.button(l='', h=14, bgc=error_color,
                c=lambda args: print_message('Error color, means that some possible issues were found',
                                             as_heads_up_message=True))
    cmds.text(l='- Error color, issues were found.', align="left", fn="smallPlainLabelFont")

    cmds.button(l='', h=14, bgc=exception_color, c=lambda args: print_message(
        'Exception color, an issue caused the check to fail. Likely because of a missing plug-in or unexpected value',
        as_heads_up_message=True))
    cmds.text(l='- Exception color, an issue caused the check to fail.', align="left", fn="smallPlainLabelFont")

    cmds.button(l='?', h=14, bgc=def_color, c=lambda args: print_message(
        'Question mask, click on button for more help. It often gives you extra options regarding the found issues.',
        as_heads_up_message=True))
    cmds.text(l='- Question mark, click on button for more help.', align="left", fn="smallPlainLabelFont")

    cmds.separator(h=15, style='none')  # Empty Space

    # Checklist Items =============
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='Checklist Items:', align="left", fn="boldLabelFont")
    cmds.text(l='This list uses the current settings to show what it expects to find:', align="left",
              fn="smallPlainLabelFont")
    cmds.separator(h=checklist_spacing, style='none')  # Empty Space

    # Create Help List: 
    font_size = 'smallPlainLabelFont'
    items_for_settings = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11]  # Allow user to update expected values
    items_with_warnings = [3, 7, 8, 9, 10, 11]  # Allow users to update warning values too

    checklist_items_help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="smallPlainLabelFont")

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(0)[0] + ': returns error if not matching: "' + str(
                         checklist_items.get(0)[
                             1]) + '".\n     Examples of custom values:\n     "film" (24fps),\n     "23.976fps",\n     "ntsc" (30fps),\n     "ntscf" (60fps),\n     "29.97fps"' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(1)[0] + ': returns error if not matching: "' + str(
                         checklist_items.get(1)[
                             1]) + '".\n     Examples of custom values:\n     "mm" (milimeter),\n     "cm" (centimeter),\n     "m" (meter)' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(2)[0] + ': returns error if not: ' + str(checklist_items.get(2)[
                                                                                                  1]) + '.\n     Please use a comma "," for entering a custom value.\n     Examples of custom values:\n     "1280, 720" (720p),\n     "1920, 1080" (1080p),\n     "2560, 1440" (1440p),\n     "3840, 2160" (4K),\n     "7680, 4320" (8K)\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(3)[0] + ': error if more than ' + str(
                         checklist_items.get(3)[1][1]) + '\n     warning if more than ' + str(
                         checklist_items.get(3)[1][0]) + '.\n    (UDIM tiles are counted as individual textures)\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(4)[0] + ': must start with ' + str(checklist_items.get(4)[
                                                                                            1]) + '\n   This function completely ignore slashes.\n   You may use a list as custom value.\n   Use a comma "," to separate multiple paths\n\n')

    message = '[X] ' + checklist_items.get(5)[0] + ': must start with ' + str(checklist_items.get(5)[1]) + \
              '\n   This function completely ignore slashes.\n   You may use a list as custom value.\n   ' \
              'Use a comma "," to separate multiple paths\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it='[X] ' + checklist_items.get(6)[
        0] + ': returns error if common objects are\n     found outside hierarchies' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(7)[0] + ': : error if more than ' + str(
                         checklist_items.get(7)[1][1]) + '\n     warning if more than: ' + str(
                         checklist_items.get(7)[1][0]) + '.' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(8)[0] + ': error if more than ' + str(
                         checklist_items.get(8)[1][1]) + '\n     warning if more than ' + str(
                         checklist_items.get(8)[1][0]) + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(9)[0] + ': error if more than ' + str(
                         checklist_items.get(9)[1][1]) + '\n     warning if more than ' + str(
                         checklist_items.get(9)[1][0]) + '.' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(10)[0] + ': error if more than ' + str(
                         checklist_items.get(10)[1][1]) + '\n     warning if more than ' + str(
                         checklist_items.get(10)[1][0]) + '.' + '\n\n')

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0,
                     it='[X] ' + checklist_items.get(11)[0] + ': error if more than ' + str(
                         checklist_items.get(11)[1][1]) + '\n     warning if more than ' + str(
                         checklist_items.get(11)[1][0]) + '.' + '\n\n')

    message = '[X] ' + checklist_items.get(12)[0] + ': error if using default names.' + \
              '\n  warning if containing default names.\n    Examples of default names:\n      ' \
              '"pCube1" = Error\n      "pointLight1" = Error\n      "nurbsPlane1" = Error\n      ' \
              '"my_pCube" = Warning\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(13)[0] + ': error if anything is assigned.\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(14)[0] + ': error if any ngons found.\n     ' \
                                                    'A polygon that is made up of five or more vertices. \n     ' \
                                                    'Anything over a quad (4 sides) is considered an ngon\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(15)[0] + ': error if is found.\n    A non-manifold geometry is a ' \
                                                    '3D shape that cannot be\n    unfolded into a 2D surface ' \
                                                    'with all its normals pointing\n    the same direction.\n   ' \
                                                    ' For example, objects with faces inside of it.\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(16)[0] + ': error if multiples UV Sets and Empty UV Sets.\n     ' \
                                                    'It ignores objects without UVs if they have only one UV Set.\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(17)[0] + ': error if rotation(XYZ) not frozen.' + \
              "\n     It doesn't check objects with incoming connections,\n     " \
              "for example, animations or rigs." + '\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(18)[0] + ': error if animated visibility is found' + \
              '\n     warning if hidden object is found.' + '\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(19)[0] + ': error if any non-deformer history found.' + '\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(20)[0] + ': error if incorrect color space found.' + \
              '\n     It only checks commonly used nodes for Redshift and Arnold\n     ' \
              'Generally "sRGB" -> float3(color), and "Raw" -> float(value).\n\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    message = '[X] ' + checklist_items.get(21)[0] + ': must start with ' + str(checklist_items.get(21)[1]) + \
              '\n   This function completely ignore slashes.\n   You may use a list as custom value.\n   ' \
              'Use a comma "," to separate multiple paths\n   This function checks:\n     Audio Nodes, \n     ' \
              'Mash Audio Nodes,\n     nCache Nodes,\n     Maya Fluid Cache Nodes,\n     ' \
              'Arnold Volumes/Standins/Lights,\n     Redshift Proxy/Volume/Normal/Lights,\n     ' \
              'Alembic/BIF/GPU Cache,\n     Golaem Common and Cache Nodes' + '\n'
    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=0, it=message)

    cmds.scrollField(checklist_items_help_scroll_field, e=True, ip=1, it='')  # Bring Back to the Top

    cmds.separator(h=checklist_spacing, style='none')  # Empty Space

    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text(l='  Issues when using the script?  Please contact me :', align="left")

    # Footer =============
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Reset Persistent Settings', h=30, c=lambda args: reset_persistent_settings_render_checklist())
    cmds.separator(h=5, style='none')
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
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


# Checklist Functions Start Here ================================================================

# Item 0 - Frame Rate
def check_frame_rate():
    item_name = checklist_items.get(0)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(0)[1]
    received_value = cmds.currentUnit(query=True, time=True)  # Frame Rate

    if received_value == expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message(item_name + ': ' + str(received_value).capitalize()))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: patch_frame_rate())
        issues_found = 1

    cmds.text("output_" + item_id, e=True, l=str(received_value).capitalize())

    # Patch Function ----------------------
    def patch_frame_rate():
        user_input = cmds.confirmDialog(
            title=item_name,
            message='Do you want to change your ' + item_name.lower() + ' from "' + str(
                received_value) + '" to "' + str(expected_value).capitalize() + '"?',
            button=['Yes, change it for me', 'Ignore Issue'],
            defaultButton='Yes, change it for me',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="question")

        if user_input == 'Yes, change it for me':
            try:
                cmds.currentUnit(time=expected_value)
                print("Your " + item_name.lower() + " was changed to " + expected_value)
            except Exception as e:
                logger.debug(str(e))
                cmds.warning('Failed to use custom setting "' + str(expected_value) + '"  as your new frame rate.')
            check_frame_rate()
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "' + str(
            expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    else:
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "' + str(
            expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 1 - Scene Units =========================================================================
def check_scene_units():
    item_name = checklist_items.get(1)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(1)[1]
    received_value = cmds.currentUnit(query=True, linear=True)

    if received_value.lower() == str(expected_value).lower():
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message(item_name + ': "' + str(received_value) + '".'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: patch_scene_units())
        issues_found = 1

    cmds.text("output_" + item_id, e=True, l=str(received_value).capitalize())

    # Patch Function ----------------------
    def patch_scene_units():
        user_input = cmds.confirmDialog(
            title=item_name,
            message='Do you want to change your ' + item_name.lower() + ' from "' + str(
                received_value) + '" to "' + str(expected_value).capitalize() + '"?',
            button=['Yes, change it for me', 'Ignore Issue'],
            defaultButton='Yes, change it for me',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="question")

        if user_input == 'Yes, change it for me':
            try:
                cmds.currentUnit(linear=str(expected_value))
                print("Your " + item_name.lower() + " was changed to " + str(expected_value))
            except Exception as e:
                logger.debug(str(e))
                cmds.warning('Failed to use custom setting "' + str(expected_value) + '"  as your new scene unit.')
            check_scene_units()
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "' + str(
            expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    else:
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "' + str(
            expected_value).capitalize() + '" and yours is "' + str(received_value).capitalize() + '"'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 2 - Output Resolution =========================================================================
def check_output_resolution():
    item_name = checklist_items[2][0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items[2][1]

    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value, list):
        if len(expected_value) < 2:
            custom_settings_failed = True
            expected_value = settings_default_checklist_values[2][1]

    received_value = [cmds.getAttr("defaultResolution.width"), cmds.getAttr("defaultResolution.height")]
    # issues_found = 0

    if str(received_value[0]).replace(' ', '') == str(expected_value[0]).replace(' ', '') and str(
            received_value[1]).replace(' ', '') == str(expected_value[1].replace(' ', '')):
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
            item_name + ': "' + str(received_value[0]) + 'x' + str(received_value[1]) + '".'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: patch_output_resolution())
        issues_found = 1

    cmds.text("output_" + item_id, e=True, l=str(received_value[0]) + 'x' + str(received_value[1]))

    # Patch Function ----------------------
    def patch_output_resolution():
        user_input = cmds.confirmDialog(
            title=item_name,
            message='Do you want to change your ' + item_name.lower() + ' from : "' + str(
                received_value[0]) + 'x' + str(received_value[1]) + '" to "' + str(expected_value[0]) + 'x' + str(
                expected_value[1]) + '"?',
            button=['Yes, change it for me', 'Ignore Issue'],
            defaultButton='Yes, change it for me',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="question")

        if user_input == 'Yes, change it for me':
            try:
                cmds.setAttr("defaultResolution.width", int(expected_value[0]))
                cmds.setAttr("defaultResolution.height", int(expected_value[1]))
                print('Your ' + item_name.lower() + ' was changed to "' + str(expected_value[0]) + 'x' + str(
                    expected_value[1]) + '"')
            except Exception as e:
                logger.debug(str(e))
                cmds.warning('Failed to use custom setting "' + str(expected_value[0]) + 'x' + str(
                    expected_value[1]) + '" as your new resolution.')
            check_output_resolution()
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(issues_found) + " issue found. The expected " + item_name.lower() + ' was "' + \
                        str(expected_value[0]) + 'x' + str(expected_value[1]) + '" and yours is "' + \
                        str(received_value[0]) + 'x' + str(received_value[1]) + '"'
    else:
        string_status = str(issues_found) + " issues found. The expected " + item_name.lower() + ' was "' + \
                        str(expected_value[0]) + 'x' + str(expected_value[1]) + '" and yours is "' + \
                        str(received_value[0]) + 'x' + str(received_value[1]) + '"'
    if custom_settings_failed:
        string_status = "1 issue found. " \
                        "The custom resolution settings provided couldn't be used to check your resolution"
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='',
                    c=lambda args: print_message("The custom value provided couldn't be used to check the resolution.",
                                                 as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 3 - Total Texture Count =========================================================================
def check_total_texture_count():
    item_name = checklist_items.get(3)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(3)[1]

    received_value = 0
    # issues_found = 0

    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value[0], int) is False or isinstance(expected_value[1], int) is False:
        custom_settings_failed = True

    # Count Textures
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        uv_tiling_mode = cmds.getAttr(file + '.uvTilingMode')
        if uv_tiling_mode != 0:
            use_frame_extension = cmds.getAttr(file + '.useFrameExtension')
            file_path = cmds.getAttr(file + ".fileTextureName")

            try:
                import maya.app.general.fileTexturePathResolver
                udim_file_pattern = maya.app.general.fileTexturePathResolver.getFilePatternString(file_path,
                                                                                                  use_frame_extension,
                                                                                                  uv_tiling_mode)
                udim_textures = maya.app.general.fileTexturePathResolver.findAllFilesForPattern(udim_file_pattern, None)
            except Exception as e:
                logger.debug(str(e))
                udim_textures = 0
            received_value += len(udim_textures)
        else:
            received_value += 1

    # Manager Message
    patch_message = 'Your ' + item_name.lower() + ' should be reduced from "' + str(
        received_value) + '" to less than "' + str(
        expected_value[1]) + '".\n (UDIM tiles are counted as individual textures)'
    cancel_button = 'Ignore Issue'

    if received_value <= expected_value[1] and received_value > expected_value[0]:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_total_texture_count())
        patch_message = 'Your ' + item_name.lower() + ' is "' + str(received_value) + '" which is a high number.' \
                                                                                      '\nConsider optimizing. (UDIM ' \
                                                                                      'tiles are counted as ' \
                                                                                      'unique textures)'
        cancel_button = 'Ignore Warning'
        issues_found = 0
    elif received_value <= expected_value[1]:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
            item_name + ': "' + str(received_value) + '". (UDIM tiles are counted as individual textures)'))

        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_total_texture_count())
        issues_found = 1

    cmds.text("output_" + item_id, e=True, l=received_value)

    # Patch Function ----------------------
    def warning_total_texture_count():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', cancel_button],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, l='', bgc=pass_color)
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if issues_found > 0:
        string_status = str(
            issues_found) + " issue found. The expected " + item_name.lower() + ' was less than "' + str(
            expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    else:
        string_status = str(
            issues_found) + " issues found. The expected " + item_name.lower() + ' was less than "' + str(
            expected_value[1]) + '" and yours is "' + str(received_value) + '"'
    if custom_settings_failed:
        string_status = "1 issue found. The custom value provided couldn't be used to check your total texture count"
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "The custom value provided couldn't be used to check your total texture count", as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 4 - Network File Paths =========================================================================
def check_network_file_paths():
    item_name = checklist_items.get(4)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(4)[1]
    incorrect_file_nodes = []

    # Count Incorrect File Nodes
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        file_path = cmds.getAttr(file + ".fileTextureName")
        if file_path != '':
            file_path_no_slashes = file_path.replace('/', '').replace('\\', '')
            for valid_path in expected_value:
                if not file_path_no_slashes.startswith(valid_path.replace('/', '').replace('\\', '')):
                    incorrect_file_nodes.append(file)
        else:
            incorrect_file_nodes.append(file)

    if len(incorrect_file_nodes) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('All file nodes currently sourced from the network.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_network_file_paths())
        issues_found = len(incorrect_file_nodes)

    cmds.text("output_" + item_id, e=True, l=len(incorrect_file_nodes))

    # Patch Function ----------------------
    def warning_network_file_paths():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=str(len(incorrect_file_nodes)) + ' of your file node paths aren\'t pointing to the network drive. '
                                                     '\nPlease change their path to a network location. '
                                                     '\n\n(Too see a list of nodes, generate a full report)',
            button=['OK', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for file_node in incorrect_file_nodes:
            string_status = string_status + '"' + file_node + "\" isn't pointing to the the network drive. " \
                                                              "Your texture files should be sourced from the " \
                                                              "network.\n\""
    else:
        string_status = str(issues_found) + ' issues found. All textures were sourced from the network'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 5 - Network Reference Paths =========================================================================
def check_network_reference_paths():
    item_name = checklist_items.get(5)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(5)[1]
    incorrect_reference_nodes = []

    # Count Incorrect Reference Nodes
    reference_list = cmds.ls(rf=True)
    try:
        for ref in reference_list:
            ref_path = cmds.referenceQuery(ref, filename=True)
            if ref_path != '':
                ref_path_no_slashes = ref_path.replace('/', '').replace('\\', '')
                for valid_path in expected_value:
                    if not ref_path_no_slashes.startswith(valid_path.replace('/', '').replace('\\', '')):
                        incorrect_reference_nodes.append(ref)
            else:
                incorrect_reference_nodes.append(ref)
    except Exception as e:
        logger.debug(str(e))
        print('One of your references is not associated with a reference file!')

    if len(incorrect_reference_nodes) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('All file nodes currently sourced from the network.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                    c=lambda args: warning_network_reference_paths())
        issues_found = len(incorrect_reference_nodes)

    cmds.text("output_" + item_id, e=True, l=len(incorrect_reference_nodes))

    # Patch Function ----------------------
    def warning_network_reference_paths():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=str(
                len(incorrect_reference_nodes)) + "\" of your reference paths aren't pointing to the network drive. "
                                                  "\nPlease change their path to a network location."
                                                  "\n\n(Too see a list of nodes, generate a full report)",
            button=['OK', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for file_node in incorrect_reference_nodes:
            string_status = string_status + '"' + file_node + "\" isn't pointing to the the network drive. " \
                                                              "Your references should be sourced from the network.\n"
    else:
        string_status = str(issues_found) + ' issues found. All references were sourced from the network'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 6 - Unparented Objects =========================================================================
def check_unparented_objects():
    item_name = checklist_items.get(6)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(6)[1]
    unparented_objects = []

    # Count Unparented Objects
    geo_dag_nodes = cmds.ls(geometry=True)
    for obj in geo_dag_nodes:
        first_parent = cmds.listRelatives(obj, p=True, f=True)  # Check if it returned something?
        children_members = cmds.listRelatives(first_parent[0], c=True, type="transform") or []
        parents_members = cmds.listRelatives(first_parent[0], ap=True, type="transform") or []
        if len(children_members) + len(parents_members) == 0:
            if cmds.nodeType(obj) != "mentalrayIblShape":
                unparented_objects.append(obj)

    if len(unparented_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No unparented objects were found.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_unparented_objects())
        issues_found = len(unparented_objects)

    cmds.text("output_" + item_id, e=True, l=len(unparented_objects))

    # Patch Function ----------------------
    def warning_unparented_objects():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=str(
                len(unparented_objects)) + ' unparented object(s) found in this scene.'
                                           '\nIt\'s likely that these objects need to be part of a hierarchy.'
                                           '\n\n(Too see a list of objects, generate a full report)',
            button=['OK', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in unparented_objects:
            string_status = string_status + '"' + obj + '" has no parent or child nodes. ' \
                                                        'It should likely be part of a hierarchy.\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No unparented objects were found.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 7 - Total Triangle Count =========================================================================
def check_total_triangle_count():
    item_name = checklist_items.get(7)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(7)[1][1]
    inbetween_value = checklist_items.get(7)[1][0]
    # unparented_objects = []

    # Check Custom Value
    custom_settings_failed = False
    if isinstance(expected_value, int) is False or isinstance(inbetween_value, int) is False:
        custom_settings_failed = True

    all_poly_count = cmds.ls(type="mesh", flatten=True)
    scene_tri_count = 0
    # smoothed_obj_count = 0

    for obj in all_poly_count:
        smooth_level = cmds.getAttr(obj + ".smoothLevel")
        smooth_state = cmds.getAttr(obj + ".displaySmoothMesh")
        total_tri_count = cmds.polyEvaluate(obj, t=True)
        total_edge_count = cmds.polyEvaluate(obj, e=True)
        # total_face_count = cmds.polyEvaluate(obj, f=True)

        if smooth_state > 0 and smooth_level != 0:
            one_subdiv_tri_count = (total_edge_count * 4)
            if smooth_level > 1:
                multi_subdiv_tri_count = one_subdiv_tri_count * (4 ** (smooth_level - 1))
                scene_tri_count = scene_tri_count + multi_subdiv_tri_count
            else:
                scene_tri_count += one_subdiv_tri_count
        else:
            scene_tri_count += total_tri_count

    if scene_tri_count < expected_value and scene_tri_count > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_total_triangle_count())
        issues_found = 0
        patch_message = 'Your scene has ' + str(
            scene_tri_count) + ' triangles, which is high. \nConsider optimizing it if possible.'
        cancel_message = "Ignore Warning"
    elif scene_tri_count < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
            'Your scene has ' + str(scene_tri_count) + ' triangles. \nGood job keeping the triangle count low!.'))
        issues_found = 0
        patch_message = ''
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_total_triangle_count())
        issues_found = 1
        patch_message = 'Your scene has ' + str(scene_tri_count) + ' triangles. You should try to keep it under ' + \
                        str(expected_value) + '.\n\n' + \
                        'In case you see a different number on your "Heads Up Display > Poly Count" option.  ' \
                        'It\'s likely that you have "shapeOrig" nodes in your scene. These are intermediate shape ' \
                        'nodes usually created by deformers. If you don\'t have deformations on your scene, you can ' \
                        'delete these to reduce triangle count.\n'
        cancel_message = "Ignore Issue"

    cmds.text("output_" + item_id, e=True, l=scene_tri_count)

    # Patch Function ----------------------
    def warning_total_triangle_count():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', cancel_message],
            defaultButton='OK',
            cancelButton=cancel_message,
            dismissString=cancel_message,
            icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                str(issues_found) + ' issues found. Your scene has ' + str(
                    scene_tri_count) + ' triangles, which is high. \nConsider optimizing it if possible.'))
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if scene_tri_count > inbetween_value and scene_tri_count < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene has ' + str(
            scene_tri_count) + ' triangles, which is high. Consider optimizing it if possible.'
    elif scene_tri_count < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene has ' + str(
            scene_tri_count) + ' triangles. Good job keeping the triangle count low!.'
    else:
        string_status = str(issues_found) + ' issue found. Your scene has ' + str(
            scene_tri_count) + ' triangles. You should try to keep it under ' + str(expected_value) + '.'
    if custom_settings_failed:
        string_status = "1 issue found. The custom value provided couldn't be used to check your total triangle count"
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "The custom value provided couldn't be used to check your total triangle count", as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 8 - Total Poly Object Count =========================================================================
def check_total_poly_object_count():
    item_name = checklist_items.get(8)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(8)[1][1]
    inbetween_value = checklist_items.get(8)[1][0]

    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) is False or isinstance(inbetween_value, int) is False:
        custom_settings_failed = True

    all_polymesh = cmds.ls(type="mesh")

    if len(all_polymesh) < expected_value and len(all_polymesh) > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='',
                    c=lambda args: warning_total_poly_object_count())
        issues_found = 0
        patch_message = 'Your scene contains "' + str(
            len(all_polymesh)) + '" polygon meshes, which is a high number. \nConsider optimizing it if possible.'
        cancel_message = "Ignore Warning"
    elif len(all_polymesh) < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
            'Your scene contains "' + str(len(all_polymesh)) + '" polygon meshes.'))
        issues_found = 0
        patch_message = ''
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                    c=lambda args: warning_total_poly_object_count())
        issues_found = 1
        patch_message = str(
            len(all_polymesh)) + ' polygon meshes in your scene. \nTry to keep this number under ' + str(
            expected_value) + '.'
        cancel_message = "Ignore Issue"

    cmds.text("output_" + item_id, e=True, l=len(all_polymesh))

    # Patch Function ----------------------
    def warning_total_poly_object_count():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', cancel_message],
            defaultButton='OK',
            cancelButton=cancel_message,
            dismissString=cancel_message,
            icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                str(issues_found) + ' issues found. Your scene contains ' + str(len(all_polymesh)) +
                ' polygon meshes, which is a high number. \nConsider optimizing it if possible.'))
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if len(all_polymesh) < expected_value and len(all_polymesh) > inbetween_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
            len(all_polymesh)) + '" polygon meshes, which is a high number. Consider optimizing it if possible.'
    elif len(all_polymesh) < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
            len(all_polymesh)) + '" polygon meshes.'
    else:
        string_status = str(issues_found) + ' issue found. Your scene contains "' + str(
            len(all_polymesh)) + '" polygon meshes. Try to keep this number under "' + str(expected_value) + '".'
    if custom_settings_failed:
        string_status = "1 issue found. The custom value provided couldn't be used to check your total poly count"
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "The custom value provided couldn't be used to check your total poly count", as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 9 - Shadow Casting Light Count =========================================================================
def check_shadow_casting_light_count():
    item_name = checklist_items.get(9)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(9)[1][1]
    inbetween_value = checklist_items.get(9)[1][0]

    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) is False or isinstance(inbetween_value, int) is False:
        custom_settings_failed = True

    all_lights = cmds.ls(lights=True)
    shadow_casting_lights = []

    for light in all_lights:
        shadow_state = cmds.getAttr(light + ".useRayTraceShadows")
        if shadow_state == 1:
            shadow_casting_lights.append(light)

    if len(shadow_casting_lights) < expected_value and len(shadow_casting_lights) > inbetween_value:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='',
                    c=lambda args: warning_shadow_casting_light_count())
        issues_found = 0
        patch_message = 'Your scene contains "' + str(len(shadow_casting_lights)) + \
                        '" shadow casting lights, which is a high number. \nConsider optimizing it if possible.'
        cancel_message = "Ignore Warning"
    elif len(shadow_casting_lights) < expected_value:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
            'Your scene contains "' + str(len(shadow_casting_lights)) + '" shadow casting lights.'))
        issues_found = 0
        patch_message = ''
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                    c=lambda args: warning_shadow_casting_light_count())
        issues_found = 1
        patch_message = 'Your scene contains ' + str(
            len(shadow_casting_lights)) + ' shadow casting lights.\nTry to keep this number under ' + str(
            expected_value) + '.'
        cancel_message = "Ignore Issue"

    cmds.text("output_" + item_id, e=True, l=len(shadow_casting_lights))

    # Patch Function ----------------------
    def warning_shadow_casting_light_count():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', cancel_message],
            defaultButton='OK',
            cancelButton=cancel_message,
            dismissString=cancel_message,
            icon="warning")

        if user_input == "Ignore Warning":
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                str(issues_found) + ' issues found. Your scene contains ' + str(len(shadow_casting_lights)) +
                ' shadow casting lights, which is a high number. \nConsider optimizing it if possible.'))
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    if len(shadow_casting_lights) < expected_value and len(shadow_casting_lights) > inbetween_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(shadow_casting_lights)) + \
                        '" shadow casting lights, which is a high number. Consider optimizing it if possible.'
    elif len(shadow_casting_lights) < expected_value:
        string_status = str(issues_found) + ' issues found. Your scene contains "' + str(len(shadow_casting_lights)) +\
                        '" shadow casting lights.'
    else:
        string_status = str(issues_found) + ' issue found. Your scene contains "' + str(len(shadow_casting_lights)) + \
                        '" shadow casting lights, you should keep this number under "' + str(expected_value) + '".'
    if custom_settings_failed:
        string_status = "1 issue found. " \
                        "The custom value provided couldn't be used to check your shadow casting lights."
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "The custom value provided couldn't be used to check your shadow casting lights.", as_warning=True))
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 10 - Redshift Shadow Casting Light Count =====================================================================
def check_rs_shadow_casting_light_count():
    item_name = checklist_items.get(10)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(10)[1][1]
    inbetween_value = checklist_items.get(10)[1][0]

    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) is False or isinstance(inbetween_value, int) is False:
        custom_settings_failed = True

    rs_physical_type = "RedshiftPhysicalLight"  # Used to check if Redshift is loaded

    node_types = cmds.ls(nodeTypes=True)

    if rs_physical_type in node_types:  # is RS loaded?

        rs_physical = cmds.ls(type=rs_physical_type)
        rs_photometric = cmds.ls(type="RedshiftIESLight")
        rs_portal = cmds.ls(type="RedshiftPortalLight")
        rs_dome = cmds.ls(type="RedshiftDomeLight")

        all_rs_lights = []
        all_rs_lights.extend(rs_physical)
        all_rs_lights.extend(rs_photometric)
        all_rs_lights.extend(rs_portal)
        all_rs_lights.extend(rs_dome)

        rs_shadow_casting_lights = []

        for rs_light in all_rs_lights:
            if rs_light != "<done>":
                # For some odd reason portal lights use an attribute called "shadows" instead of "shadow"
                if cmds.objectType(rs_light) != "RedshiftPortalLight":
                    rs_shadow_state = cmds.getAttr(rs_light + ".shadow")
                else:
                    rs_shadow_state = cmds.getAttr(rs_light + ".shadows")
                if rs_shadow_state == 1:
                    rs_shadow_casting_lights.append(rs_light)

        if len(rs_shadow_casting_lights) < expected_value and len(rs_shadow_casting_lights) > inbetween_value:
            cmds.button("status_" + item_id, e=True, bgc=warning_color, l='',
                        c=lambda args: warning_rs_shadow_casting_light_count())
            issues_found = 0
            patch_message = 'Your scene contains "' + str(len(rs_shadow_casting_lights)) + \
                            '" Redshift shadow casting lights, which is a high number. ' \
                            '\nConsider optimizing it if possible.'
            cancel_message = "Ignore Warning"
        elif len(rs_shadow_casting_lights) < expected_value:
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                'Your scene contains "' + str(len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights.'))
            issues_found = 0
            patch_message = ''
        else:
            cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                        c=lambda args: warning_rs_shadow_casting_light_count())
            issues_found = 1
            patch_message = 'Your scene contains ' + str(len(rs_shadow_casting_lights)) + \
                            ' Redshift shadow casting lights.\nTry to keep this number under ' + \
                            str(expected_value) + '.'
            cancel_message = "Ignore Issue"

        cmds.text("output_" + item_id, e=True, l=len(rs_shadow_casting_lights))

        # Patch Function ----------------------
        def warning_rs_shadow_casting_light_count():
            user_input = cmds.confirmDialog(
                title=item_name,
                message=patch_message,
                button=['OK', cancel_message],
                defaultButton='OK',
                cancelButton=cancel_message,
                dismissString=cancel_message,
                icon="warning")

            if user_input == "Ignore Warning":
                cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                    str(issues_found) + ' issues found. Your scene contains ' + str(
                        len(rs_shadow_casting_lights)) + ' Redshift shadow casting lights, which is a high number. '
                                                         '\nConsider optimizing it if possible.'))
            else:
                cmds.button("status_" + item_id, e=True, l='')

        # Return string for report ------------
        if len(rs_shadow_casting_lights) < expected_value and len(rs_shadow_casting_lights) > inbetween_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
                len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights, which is a high number. ' \
                                                 'Consider optimizing it if possible.'
        elif len(rs_shadow_casting_lights) < expected_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
                len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights.'
        else:
            string_status = str(issues_found) + ' issue found. Your scene contains "' + str(
                len(rs_shadow_casting_lights)) + '" Redshift shadow casting lights, you should ' \
                                                 'keep this number under "' + str(expected_value) + '".'
        if custom_settings_failed:
            string_status = "1 issue found. The custom value provided couldn't " \
                            "be used to check your Redshift shadow casting lights."
            cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
                "The custom value provided couldn't be used to check your Redshift shadow casting lights.",
                as_warning=True))
        return '\n*** ' + item_name + " ***\n" + string_status
    else:
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "No Redshift light types exist in the scene. Redshift plugin doesn't seem to be loaded.", as_warning=True))
        cmds.text("output_" + item_id, e=True, l='No Redshift')
        return '\n*** ' + item_name + " ***\n" + "0 issues found, but no Redshift light types exist in the scene. " \
                                                 "Redshift plugin doesn't seem to be loaded."


# Item 11 - Arnold Shadow Casting Light Count =========================================================================
def check_ai_shadow_casting_light_count():
    item_name = checklist_items.get(11)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(11)[1][1]
    inbetween_value = checklist_items.get(11)[1][0]

    # Check Custom Values
    custom_settings_failed = False
    if isinstance(expected_value, int) is False or isinstance(inbetween_value, int) is False:
        custom_settings_failed = True

    ai_physical_type = "aiAreaLight"  # Used to check if Arnold is loaded

    node_types = cmds.ls(nodeTypes=True)

    if ai_physical_type in node_types:  # is Arnold loaded?

        ai_sky_dome = cmds.ls(type="aiSkyDomeLight")
        ai_mesh = cmds.ls(type="aiMeshLight")
        ai_photometric = cmds.ls(type="aiPhotometricLight")
        ai_area = cmds.ls(type=ai_physical_type)
        # ai_portal = cmds.ls(type="aiLightPortal")

        all_ai_lights = []
        all_ai_lights.extend(ai_sky_dome)
        all_ai_lights.extend(ai_mesh)
        all_ai_lights.extend(ai_photometric)
        all_ai_lights.extend(ai_area)
        # all_ai_lights.extend(ai_portal)

        ai_shadow_casting_lights = []

        for ai_light in all_ai_lights:
            rs_shadow_state = cmds.getAttr(ai_light + ".aiCastShadows")
            if rs_shadow_state == 1:
                ai_shadow_casting_lights.append(ai_light)

        if len(ai_shadow_casting_lights) < expected_value and len(ai_shadow_casting_lights) > inbetween_value:
            cmds.button("status_" + item_id, e=True, bgc=warning_color, l='',
                        c=lambda args: warning_ai_shadow_casting_light_count())
            issues_found = 0
            patch_message = 'Your scene contains "' + str(len(ai_shadow_casting_lights)) + \
                            '" Arnold shadow casting lights, which is a high number. \n' \
                            'Consider optimizing it if possible.'
            cancel_message = "Ignore Warning"
        elif len(ai_shadow_casting_lights) < expected_value:
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                'Your scene contains "' + str(len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights.'))
            issues_found = 0
            patch_message = ''
        else:
            cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                        c=lambda args: warning_ai_shadow_casting_light_count())
            issues_found = 1
            patch_message = 'Your scene contains ' + str(
                len(ai_shadow_casting_lights)) + ' Arnold shadow casting lights.\nTry to keep this number under ' + str(
                expected_value) + '.'
            cancel_message = "Ignore Issue"

        cmds.text("output_" + item_id, e=True, l=len(ai_shadow_casting_lights))

        # Patch Function ----------------------
        def warning_ai_shadow_casting_light_count():
            user_input = cmds.confirmDialog(
                title=item_name,
                message=patch_message,
                button=['OK', cancel_message],
                defaultButton='OK',
                cancelButton=cancel_message,
                dismissString=cancel_message,
                icon="warning")

            if user_input == "Ignore Warning":
                cmds.button("status_" + item_id, e=True, bgc=pass_color, l='', c=lambda args: print_message(
                    str(issues_found) + ' issues found. Your scene contains ' + str(
                        len(ai_shadow_casting_lights)) + ' Arnold shadow casting lights, which is a high number. '
                                                         '\nConsider optimizing it if possible.'))
            else:
                cmds.button("status_" + item_id, e=True, l='')

        # Return string for report ------------
        if len(ai_shadow_casting_lights) < expected_value and len(ai_shadow_casting_lights) > inbetween_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
                len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights, which is a high number. ' \
                                                 'Consider optimizing it if possible.'
        elif len(ai_shadow_casting_lights) < expected_value:
            string_status = str(issues_found) + ' issues found. Your scene contains "' + str(
                len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights.'
        else:
            string_status = str(issues_found) + ' issue found. Your scene contains "' + str(
                len(ai_shadow_casting_lights)) + '" Arnold shadow casting lights, you ' \
                                                 'should keep this number under "' + str(expected_value) + '".'
        if custom_settings_failed:
            string_status = "1 issue found. The custom value provided couldn't " \
                            "be used to check your Arnold shadow casting lights."
            cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
                "The custom value provided couldn't be used to check your Arnold shadow casting lights.",
                as_warning=True))
        return '\n*** ' + item_name + " ***\n" + string_status
    else:
        cmds.button("status_" + item_id, e=True, bgc=exception_color, l='', c=lambda args: print_message(
            "No Arnold light types exist in the scene. Arnold plugin doesn't seem to be loaded.", as_warning=True))
        cmds.text("output_" + item_id, e=True, l='No Arnold')
        return '\n*** ' + item_name + " ***\n" + "0 issues found, but no Arnold light types exist in the scene. " \
                                                 "Arnold plugin doesn't seem to be loaded."


# Item 12 - Default Object Names =========================================================================
def check_default_object_names():
    item_name = checklist_items.get(12)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(12)[1]

    offending_objects = []
    possible_offenders = []

    default_object_names = ["nurbsSphere", "nurbsCube", "nurbsCylinder", "nurbsCone",
                            "nurbsPlane", "nurbsTorus", "nurbsCircle", "nurbsSquare", "pSphere", "pCube", "pCylinder",
                            "pCone", "pPlane", "pTorus", "pPrism", "pPyramid", "pPipe", "pHelix", "pSolid",
                            "rsPhysicalLight",
                            "rsIESLight", "rsPortalLight", "aiAreaLight", "rsDomeLight", "aiPhotometricLight",
                            "aiLightPortal",
                            "ambientLight", "directionalLight", "pointLight", "spotLight", "areaLight", "volumeLight"]

    all_objects = cmds.ls(lt=True, lf=True, g=True)

    for obj in all_objects:
        for def_name in default_object_names:
            if obj.startswith(def_name):
                offending_objects.append(obj)
            elif def_name in obj:
                possible_offenders.append(obj)

    # Manage Strings
    if len(possible_offenders) == 1:
        patch_message_warning = str(
            len(possible_offenders)) + ' object contains a string extremely similar to the default names.' \
                                       '\n(Ignore this warning if the name describes your object properly)'
    else:
        patch_message_warning = str(
            len(possible_offenders)) + ' objects contain a string extremely similar to the default names.' \
                                       '\n(Ignore this warning if the name describes your object properly)'

    if len(offending_objects) == 1:
        patch_message_error = str(
            len(offending_objects)) + ' object was not named properly. \nPlease rename your objects descriptively.'
    else:
        patch_message_error = str(
            len(offending_objects)) + ' objects were not named properly. \nPlease rename your objects descriptively.'

    # Manage Buttons
    if len(possible_offenders) != 0 and len(offending_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_default_object_names())
        issues_found = 0
    elif len(offending_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No unnamed objects were found, well done!'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_default_object_names())
        issues_found = len(offending_objects)

    # Manage Message
    patch_message = ''
    cancel_message = 'Ignore Issue'

    if len(possible_offenders) != 0 and len(offending_objects) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_offenders)) + ' ]')
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
    elif len(possible_offenders) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(offending_objects)))
        patch_message = patch_message_error
    else:
        cmds.text("output_" + item_id, e=True,
                  l=str(len(offending_objects)) + ' + [ ' + str(len(possible_offenders)) + ' ]')
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        # return_message = patch_message_error + '\n' + patch_message_warning

    # Patch Function ----------------------
    def warning_default_object_names():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', cancel_message],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                        c=lambda args: warning_default_object_names())
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_offenders) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in offending_objects:
            string_status = string_status + '"' + obj + '" was not named properly. Please rename ' \
                                                        'your object descriptively.\n'
        if len(offending_objects) != 0 and len(possible_offenders) == 0:
            string_status = string_status[:-1]

        for obj in possible_offenders:
            string_status = string_status + '"' + obj + '"  contains a string extremely similar to the default names.\n'
        if len(possible_offenders) != 0:
            string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No unnamed objects were found, well done!'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 13 - Objects Assigned to lambert1 =========================================================================
def check_objects_assigned_to_lambert1():
    item_name = checklist_items.get(13)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(13)[1]

    lambert1_objects = cmds.sets("initialShadingGroup", q=True) or []

    if len(lambert1_objects) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No objects were assigned to lambert1.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?',
                    c=lambda args: warning_objects_assigned_to_lambert1())
        issues_found = len(lambert1_objects)

    cmds.text("output_" + item_id, e=True, l=len(lambert1_objects))

    if len(lambert1_objects) == 1:
        patch_message = str(len(lambert1_objects)) + ' object is assigned to lambert1. \nMake sure no objects are ' \
                                                     'assigned to lambert1.\n\n(Too see a list of ' \
                                                     'objects, generate a full report)'
    else:
        patch_message = str(len(lambert1_objects)) + ' objects are assigned to lambert1. \nMake sure no objects are ' \
                                                     'assigned to lambert1.\n\n(Too see a list of objects, ' \
                                                     'generate a full report)'

    # Patch Function ----------------------
    def warning_objects_assigned_to_lambert1():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == '':
            pass
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in lambert1_objects:
            string_status = string_status + '"' + obj + '"  is assigned to lambert1. ' \
                                                        'It should be assigned to another shader.\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No objects are assigned to lambert1.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 14 - Ngons =========================================================================
def check_ngons():
    item_name = checklist_items.get(14)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(14)[1]

    ngon_mel_command = 'string $ngons[] = `polyCleanupArgList 3 { "1","2","1","0","1","0","0","0","0",' \
                       '"1e-005","0","1e-005","0","1e-005","0","-1","0" }`;'
    ngons_list = mel.eval(ngon_mel_command)
    cmds.select(clear=True)

    print('')  # Clear Any Warnings

    if len(ngons_list) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No ngons were found in your scene. Good job!'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_ngons())
        issues_found = len(ngons_list)

    cmds.text("output_" + item_id, e=True, l=len(ngons_list))

    if len(ngons_list) == 1:
        patch_message = str(len(ngons_list)) + ' ngon found in your scene. \nMake sure no faces have more than 4 ' \
                                               'sides.\n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(ngons_list)) + ' ngons found in your scene. \nMake sure no faces have more than 4 ' \
                                               'sides.\n\n(Too see a list of objects, generate a full report)'

    # Patch Function ----------------------
    def warning_ngons():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', 'Select Ngons', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Ngons':
            out_ngons_list = mel.eval(ngon_mel_command)
            logger.debug(str(out_ngons_list))
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in ngons_list:
            string_status = string_status + '"' + obj + '"  is an ngon (face with more than 4 sides).\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No ngons were found in your scene.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 15 - Non-manifold Geometry =========================================================================
def check_non_manifold_geometry():
    item_name = checklist_items.get(15)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(15)[1]

    nonmanifold_geo = []
    nonmanifold_verts = []

    all_geo = cmds.ls(type='mesh', long=True)

    for geo in all_geo:
        obj_non_manifold_verts = cmds.polyInfo(geo, nmv=True) or []
        if len(obj_non_manifold_verts) > 0:
            nonmanifold_geo.append(geo)
            nonmanifold_verts.append(obj_non_manifold_verts)

    if len(nonmanifold_geo) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No objects with non-manifold geometry in your scene. Well Done!'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_non_manifold_geometry())
        issues_found = len(nonmanifold_geo)

    cmds.text("output_" + item_id, e=True, l=len(nonmanifold_geo))

    if len(nonmanifold_geo) == 1:
        patch_message = str(len(nonmanifold_geo)) + ' object with non-manifold geometry was found in your scene. ' \
                                                    '\n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(nonmanifold_geo)) + ' objects with non-manifold geometry were found in your scene. ' \
                                                    '\n\n(Too see a list of objects, generate a full report)'

    # Patch Function ----------------------
    def warning_non_manifold_geometry():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', 'Select Non-manifold Vertices', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Non-manifold Vertices':
            cmds.select(clear=True)
            for verts in nonmanifold_verts:
                cmds.select(verts, add=True)
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in nonmanifold_geo:
            string_status = string_status + '"' + get_short_name(obj) + '"  has non-manifold geometry.\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No non-manifold geometry found in your scene.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 16 - Empty UV Sets =========================================================================
def check_empty_uv_sets():
    item_name = checklist_items.get(16)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(16)[1]

    objects_extra_empty_uv_sets = []
    objects_single_empty_uv_sets = []

    all_geo = cmds.ls(type='mesh')

    for obj in all_geo:
        all_uv_sets = cmds.polyUVSet(obj, q=True, allUVSets=True) or []
        if len(all_uv_sets) > 1:
            for uv_set in all_uv_sets:
                uv_count = cmds.polyEvaluate(obj, uv=True, uvs=uv_set)
                if uv_count == 0:
                    objects_extra_empty_uv_sets.append(obj)
        else:
            for uv_set in all_uv_sets:
                uv_count = cmds.polyEvaluate(obj, uv=True, uvs=uv_set)
                if uv_count == 0:
                    objects_single_empty_uv_sets.append(obj)

    if len(objects_extra_empty_uv_sets) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No empty UV sets.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_empty_uv_sets())
        issues_found = len(objects_extra_empty_uv_sets)

    cmds.text("output_" + item_id, e=True, l=len(objects_extra_empty_uv_sets))

    if len(objects_extra_empty_uv_sets) == 1:
        patch_message = str(
            len(objects_extra_empty_uv_sets)) + ' object found containing multiple UV Sets and empty UV Sets. ' \
                                                '\n\n(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(
            len(objects_extra_empty_uv_sets)) + ' objects found containing multiple UV Sets and empty UV Sets. ' \
                                                '\n\n(Too see a list of objects, generate a full report)'

    # Patch Function ----------------------
    def warning_empty_uv_sets():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', 'Select Objects with Empty UV Sets', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Objects with Empty UV Sets':
            cmds.select(clear=True)
            for uv_obj in objects_extra_empty_uv_sets:
                object_transform = cmds.listRelatives(uv_obj, allParents=True, type='transform') or []
                if len(object_transform) > 0:
                    cmds.select(object_transform, add=True)
                else:
                    cmds.select(uv_obj, add=True)
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_extra_empty_uv_sets:
            string_status = string_status + '"' + obj + '" has multiple UV Sets and Empty UV Sets.\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No geometry with multiple UV Sets and Empty UV Sets.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 17 - Frozen Transforms =========================================================================
def check_frozen_transforms():
    item_name = checklist_items.get(17)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(17)[1]

    objects_no_frozen_transforms = []

    all_transforms = cmds.ls(type='transform')

    for transform in all_transforms:
        children = cmds.listRelatives(transform, c=True, pa=True) or []
        for child in children:
            object_type = cmds.objectType(child)
            if object_type == 'mesh' or object_type == 'nurbsCurve':
                if cmds.getAttr(transform + ".rotateX") != 0 or cmds.getAttr(
                        transform + ".rotateY") != 0 or cmds.getAttr(transform + ".rotateZ") != 0:
                    if len(cmds.listConnections(transform + ".rotateX") or []) == 0 and len(
                            cmds.listConnections(transform + ".rotateY") or []) == 0 and len(
                            cmds.listConnections(transform + ".rotateZ") or []) == 0 and len(
                            cmds.listConnections(transform + ".rotate") or []) == 0:
                        objects_no_frozen_transforms.append(transform)

    if len(objects_no_frozen_transforms) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No empty UV sets.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='?', c=lambda args: warning_frozen_transforms())
        issues_found = len(objects_no_frozen_transforms)

    cmds.text("output_" + item_id, e=True, l=len(objects_no_frozen_transforms))

    if len(objects_no_frozen_transforms) == 1:
        patch_message = str(len(objects_no_frozen_transforms)) + ' object has un-frozen transformations. \n\n' \
                                                                 '(Too see a list of objects, generate a full report)'
    else:
        patch_message = str(len(objects_no_frozen_transforms)) + ' objects have un-frozen transformations. \n\n' \
                                                                 '(Too see a list of objects, generate a full report)'

    # Patch Function ----------------------
    def warning_frozen_transforms():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=['OK', 'Select Objects with un-frozen transformations', 'Ignore Warning'],
            defaultButton='OK',
            cancelButton='Ignore Warning',
            dismissString='Ignore Warning',
            icon="warning")

        if user_input == 'Select Objects with un-frozen transformations':
            cmds.select(objects_no_frozen_transforms)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='')
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_no_frozen_transforms:
            string_status = string_status + '"' + obj + '" has un-frozen transformations.\n'
        string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No objects have un-frozen transformations.'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 18 - Animated Visibility =========================================================================
def check_animated_visibility():
    item_name = checklist_items.get(18)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(18)[1]

    objects_animated_visibility = []
    objects_hidden = []

    all_transforms = cmds.ls(type='transform')

    for transform in all_transforms:
        attributes = cmds.listAttr(transform)
        if 'visibility' in attributes:
            if cmds.getAttr(transform + ".visibility") == 0:
                children = cmds.listRelatives(transform, s=True, pa=True) or []
                if len(children) != 0:
                    if cmds.nodeType(children[0]) != "camera":
                        objects_hidden.append(transform)
        input_nodes = cmds.listConnections(transform + ".visibility", destination=False, source=True) or []
        for node in input_nodes:
            if 'animCurve' in cmds.nodeType(node):
                objects_animated_visibility.append(transform)

    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []

    if len(objects_hidden) == 1:
        patch_message_warning = str(len(objects_hidden)) + ' object is hidden.\n'
    else:
        patch_message_warning = str(len(objects_hidden)) + ' objects are hidden.\n'

    if len(objects_animated_visibility) == 1:
        patch_message_error = str(len(objects_animated_visibility)) + ' object with animated visibility.\n'
    else:
        patch_message_error = str(len(objects_animated_visibility)) + ' objects with animated visibility.\n'

    # Manage Message
    patch_message = ''

    if len(objects_hidden) != 0 and len(objects_animated_visibility) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(objects_hidden)) + ' ]')
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append('Select Hidden Objects')
    elif len(objects_hidden) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_animated_visibility)))
        patch_message = patch_message_error
        buttons_to_add.append('Select Objects With Animated Visibility')
    else:
        cmds.text("output_" + item_id, e=True,
                  l=str(len(objects_animated_visibility)) + ' + [ ' + str(len(objects_hidden)) + ' ]')
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        # return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append('Select Hidden Objects')
        buttons_to_add.append('Select Objects With Animated Visibility')

    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)

    # Manage State
    if len(objects_hidden) != 0 and len(objects_animated_visibility) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_animated_visibility())
        issues_found = 0
    elif len(objects_animated_visibility) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No objects with animated visibility or hidden.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_animated_visibility())
        issues_found = len(objects_animated_visibility)

    # Patch Function ----------------------
    def warning_animated_visibility():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=assembled_message,
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Objects With Animated Visibility':
            cmds.select(objects_animated_visibility)
        elif user_input == 'Select Hidden Objects':
            cmds.select(objects_hidden)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='')
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(objects_hidden) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_animated_visibility:
            string_status = string_status + '"' + obj + '" has animated visibility.\n'
        if len(objects_animated_visibility) != 0 and len(objects_hidden) == 0:
            string_status = string_status[:-1]

        for obj in objects_hidden:
            string_status = string_status + '"' + obj + '" is hidden.\n'
        if len(objects_hidden) != 0:
            string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No unnamed objects were found, well done!'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 19 - Non Deformer History =========================================================================
def check_non_deformer_history():
    item_name = checklist_items.get(19)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(19)[1]

    objects_non_deformer_history = []
    possible_objects_non_deformer_history = []

    objects_to_check = []
    objects_to_check.extend(cmds.ls(typ='nurbsSurface') or [])
    objects_to_check.extend(cmds.ls(typ='mesh') or [])
    objects_to_check.extend(cmds.ls(typ='subdiv') or [])
    objects_to_check.extend(cmds.ls(typ='nurbsCurve') or [])

    not_history_nodes = ['tweak', 'expression', 'unitConversion', 'time', 'objectSet', 'reference', 'polyTweak',
                         'blendShape', 'groupId',
                         'renderLayer', 'renderLayerManager', 'shadingEngine', 'displayLayer', 'skinCluster',
                         'groupParts', 'mentalraySubdivApprox', 'proximityWrap',
                         'cluster', 'cMuscleSystem', 'timeToUnitConversion', 'deltaMush', 'tension', 'wire', 'wrinkle',
                         'softMod', 'jiggle', 'diskCache', 'leastSquaresModifier']

    possible_not_history_nodes = ['nonLinear', 'ffd', 'curveWarp', 'wrap', 'shrinkWrap', 'sculpt', 'textureDeformer']

    # Find Offenders
    for obj in objects_to_check:
        history = cmds.listHistory(obj, pdo=1) or []
        # Convert to string?
        for node in history:
            if cmds.nodeType(node) not in not_history_nodes and cmds.nodeType(node) not in possible_not_history_nodes:
                if obj not in objects_non_deformer_history:
                    objects_non_deformer_history.append(obj)
            if cmds.nodeType(node) in possible_not_history_nodes:
                if obj not in possible_objects_non_deformer_history:
                    possible_objects_non_deformer_history.append(obj)

    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []

    if len(possible_objects_non_deformer_history) == 1:
        patch_message_warning = str(
            len(possible_objects_non_deformer_history)) + ' object contains deformers often used for modeling.\n'
    else:
        patch_message_warning = str(
            len(possible_objects_non_deformer_history)) + ' objects contain deformers often used for modeling.\n'

    if len(objects_non_deformer_history) == 1:
        patch_message_error = str(len(objects_non_deformer_history)) + ' object contains non-deformer history.\n'
    else:
        patch_message_error = str(len(objects_non_deformer_history)) + ' objects contain non-deformer history.\n'

    # Manage Message
    patch_message = ''

    if len(possible_objects_non_deformer_history) != 0 and len(objects_non_deformer_history) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_objects_non_deformer_history)) + ' ]')
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append('Select Objects With Suspicious Deformers')
    elif len(possible_objects_non_deformer_history) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_non_deformer_history)))
        patch_message = patch_message_error
        buttons_to_add.append('Select Objects With Non-deformer History')
    else:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_non_deformer_history)) + ' + [ ' + str(
            len(possible_objects_non_deformer_history)) + ' ]')
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        # return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append('Select Objects With Suspicious Deformers')
        buttons_to_add.append('Select Objects With Non-deformer History')

    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)

    # Manage State
    if len(possible_objects_non_deformer_history) != 0 and len(objects_non_deformer_history) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_non_deformer_history())
        issues_found = 0
    elif len(objects_non_deformer_history) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No objects with non-deformer history were found.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_non_deformer_history())
        issues_found = len(objects_non_deformer_history)

    # Patch Function ----------------------
    def warning_non_deformer_history():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message,
            button=assembled_message,
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Objects With Non-deformer History':
            cmds.select(objects_non_deformer_history)
        elif user_input == 'Select Objects With Suspicious Deformers':
            cmds.select(possible_objects_non_deformer_history)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='')
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_objects_non_deformer_history) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_non_deformer_history:
            string_status = string_status + '"' + obj + '" contains non-deformer history.\n'
        if len(objects_non_deformer_history) != 0 and len(possible_objects_non_deformer_history) == 0:
            string_status = string_status[:-1]

        for obj in possible_objects_non_deformer_history:
            string_status = string_status + '"' + obj + '" contains deformers often used for modeling.\n'
        if len(possible_objects_non_deformer_history) != 0:
            string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No objects with non-deformer history!'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 20 - Textures Color Space =========================================================================
def check_textures_color_space():
    item_name = checklist_items.get(20)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    # expected_value = checklist_items.get(20)[1]

    objects_wrong_color_space = []
    possible_objects_wrong_color_space = []

    # These types return an error instead of warning
    error_types = ['RedshiftMaterial', 'RedshiftArchitectural', 'RedshiftDisplacement', 'RedshiftColorCorrection',
                   'RedshiftBumpMap', 'RedshiftSkin', 'RedshiftSubSurfaceScatter',
                   'aiStandardSurface', 'aiFlat', 'aiCarPaint', 'aiBump2d', '', 'aiToon', 'aiBump3d',
                   'aiAmbientOcclusion', 'displacementShader']

    # If type starts with any of these strings it will be tested
    check_types = ['Redshift', 'ai', 'lambert', 'blinn', 'phong', 'useBackground', 'checker', 'ramp', 'volumeShader',
                   'displacementShader', 'anisotropic', 'bump2d']

    # These types and connections are allowed to be float3 even though it's raw
    float3_to_float_exceptions = {'RedshiftBumpMap': 'input',
                                  'RedshiftDisplacement': 'texMap'}

    # Count Textures
    all_file_nodes = cmds.ls(type="file")
    for file in all_file_nodes:
        color_space = cmds.getAttr(file + '.colorSpace')

        has_suspicious_connection = False
        has_error_node_type = False

        input_node_connections = cmds.listConnections(file, destination=True, source=False, plugs=True) or []

        suspicious_connections = []

        if color_space.lower() == 'Raw'.lower():
            for in_con in input_node_connections:
                node = in_con.split('.')[0]
                node_in_con = in_con.split('.')[1]

                node_type = cmds.objectType(node)

                if node_type in error_types:
                    has_error_node_type = True

                should_be_checked = False
                for types in check_types:
                    if node_type.startswith(types):
                        should_be_checked = True

                if should_be_checked:
                    data_type = cmds.getAttr(in_con, type=True)
                    if data_type == 'float3' and (node_type in float3_to_float_exceptions and
                                                  node_in_con in float3_to_float_exceptions.values()) is False:
                        has_suspicious_connection = True
                        suspicious_connections.append(in_con)

        if color_space.lower() == 'sRGB'.lower():
            for in_con in input_node_connections:
                node = in_con.split('.')[0]
                node_in_con = in_con.split('.')[1]

                node_type = cmds.objectType(node)

                if node_type in error_types:
                    has_error_node_type = True

                should_be_checked = False
                for types in check_types:
                    if node_type.startswith(types):
                        should_be_checked = True

                if should_be_checked:
                    data_type = cmds.getAttr(in_con, type=True)
                    if data_type == 'float':
                        has_suspicious_connection = True
                        suspicious_connections.append(in_con)
                    if node_type in float3_to_float_exceptions and node_in_con in float3_to_float_exceptions.values():
                        has_suspicious_connection = True
                        suspicious_connections.append(in_con)

        if has_suspicious_connection:
            if has_error_node_type:
                objects_wrong_color_space.append([file, suspicious_connections])
            else:
                possible_objects_wrong_color_space.append([file, suspicious_connections])

    # Manage Strings
    cancel_message = 'Ignore Issue'
    buttons_to_add = []
    bottom_message = '\n\n (For a complete list, generate a full report)'

    if len(possible_objects_wrong_color_space) == 1:
        patch_message_warning = str(len(possible_objects_wrong_color_space)) + ' file node is using a color space ' \
                                                                               'that might not be appropriate for ' \
                                                                               'its connection.\n'
    else:
        patch_message_warning = str(len(possible_objects_wrong_color_space)) + ' file nodes are using a color space ' \
                                                                               'that might not be appropriate for ' \
                                                                               'its connection.\n'

    if len(objects_wrong_color_space) == 1:
        patch_message_error = str(len(objects_wrong_color_space)) + ' file node is using a color space that is not ' \
                                                                    'appropriate for its connection.\n'
    else:
        patch_message_error = str(len(objects_wrong_color_space)) + ' file nodes are using a color space that is ' \
                                                                    'not appropriate for its connection.\n'

    # Manage Messages
    patch_message = ''
    might_have_issues_message = 'Select File Nodes With Possible Issues'
    has_issues_message = 'Select File Nodes With Issues'

    if len(possible_objects_wrong_color_space) != 0 and len(objects_wrong_color_space) == 0:
        cmds.text("output_" + item_id, e=True, l='[ ' + str(len(possible_objects_wrong_color_space)) + ' ]')
        patch_message = patch_message_warning
        cancel_message = 'Ignore Warning'
        buttons_to_add.append(might_have_issues_message)
    elif len(possible_objects_wrong_color_space) == 0:
        cmds.text("output_" + item_id, e=True, l=str(len(objects_wrong_color_space)))
        patch_message = patch_message_error
        buttons_to_add.append(has_issues_message)
    else:
        cmds.text("output_" + item_id, e=True,
                  l=str(len(objects_wrong_color_space)) + ' + [ ' + str(len(possible_objects_wrong_color_space)) + ' ]')
        patch_message = patch_message_error + '\n\n' + patch_message_warning
        # return_message = patch_message_error + '\n' + patch_message_warning
        buttons_to_add.append(might_have_issues_message)
        buttons_to_add.append(has_issues_message)

    assembled_message = ['OK']
    assembled_message.extend(buttons_to_add)
    assembled_message.append(cancel_message)

    # Manage State
    if len(possible_objects_wrong_color_space) != 0 and len(objects_wrong_color_space) == 0:
        cmds.button("status_" + item_id, e=True, bgc=warning_color, l='', c=lambda args: warning_non_deformer_history())
        issues_found = 0
    elif len(objects_wrong_color_space) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('No color space issues were found.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_non_deformer_history())
        issues_found = len(objects_wrong_color_space)

    # Patch Function ----------------------
    def warning_non_deformer_history():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=patch_message + bottom_message,
            button=assembled_message,
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == has_issues_message:
            cmds.select(clear=True)
            for w_obj in objects_wrong_color_space:
                cmds.select(w_obj[0], add=True)
        elif user_input == might_have_issues_message:
            cmds.select(clear=True)
            for p_obj in possible_objects_wrong_color_space:
                cmds.select(p_obj[0], add=True)
        elif user_input == 'Ignore Warning':
            cmds.button("status_" + item_id, e=True, bgc=pass_color, l='')
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0 or len(possible_objects_wrong_color_space) > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for obj in objects_wrong_color_space:
            string_status = string_status + '"' + obj[0] + '" is using a color space (' + cmds.getAttr(
                obj[0] + '.colorSpace') + ') that is not appropriate for its connection.\n'
            for connection in obj[1]:
                string_status = string_status + '   "' + connection + '" triggered this error.\n'
        if len(objects_wrong_color_space) != 0 and len(possible_objects_wrong_color_space) == 0:
            string_status = string_status[:-1]

        for obj in possible_objects_wrong_color_space:
            string_status = string_status + '"' + obj[0] + '" might be using a color space (' + cmds.getAttr(
                obj[0] + '.colorSpace') + ') that is not appropriate for its connection.\n'
            for connection in obj[1]:
                string_status = string_status + '   "' + connection + '" triggered this warning.\n'
        if len(possible_objects_wrong_color_space) != 0:
            string_status = string_status[:-1]
    else:
        string_status = str(issues_found) + ' issues found. No color space issues were found!'
    return '\n*** ' + item_name + " ***\n" + string_status


# Item 21 - Network Paths (Miscellaneous) - Other Network Paths ====================================================
def check_other_network_paths():
    item_name = checklist_items.get(21)[0]
    item_id = item_name.lower().replace(" ", "_").replace("-", "_")
    expected_value = checklist_items.get(21)[1]
    incorrect_path_nodes = []

    def check_paths(node_type, path_attribute_name, accepts_empty=False, checks_multiple_paths=False,
                    multiple_paths_spliter=';'):
        try:
            all_provided_type_nodes = cmds.ls(type=node_type) or []
            for node in all_provided_type_nodes:
                file_path = cmds.getAttr(node + "." + path_attribute_name) or ''

                if checks_multiple_paths:
                    file_path = file_path.split[multiple_paths_spliter]
                    for one_path in file_path:
                        if one_path != '':
                            file_path_no_slashes = one_path.replace('/', '').replace('\\', '')
                            for valid_path in expected_value:
                                if not file_path_no_slashes.startswith(valid_path.replace('/', '').replace('\\', '')):
                                    incorrect_path_nodes.append([node, node_type])
                        else:
                            if not accepts_empty:
                                incorrect_path_nodes.append([node, node_type])
                else:
                    if file_path != '':
                        file_path_no_slashes = file_path.replace('/', '').replace('\\', '')
                        for valid_path in expected_value:
                            if not file_path_no_slashes.startswith(valid_path.replace('/', '').replace('\\', '')):
                                incorrect_path_nodes.append([node, node_type])
                    else:
                        if not accepts_empty:
                            incorrect_path_nodes.append([node, node_type])
        except Exception as e:
            logger.debug(str(e))
            print('Something went wrong when checking the attribute "' + path_attribute_name +
                  '" in the nodes of type "' + str(node_type) + '".')

    node_types = cmds.ls(nodeTypes=True)

    # Count Nodes Incorrect  with Incorrect Paths

    # General Checks
    check_paths('audio', 'filename')
    check_paths('cacheFile', 'cachePath')

    # Alembic Cache:
    if 'AlembicNode' in node_types:
        check_paths('AlembicNode', 'abc_File')

    # GPU Cache:
    if 'gpuCache' in node_types:
        check_paths('gpuCache', 'cacheFileName')

    # BIF Cache:
    if 'BifMeshImportNode' in node_types:
        check_paths('BifMeshImportNode', 'bifMeshDirectory')

    # MASH Checks
    if 'MASH_Audio' in node_types:
        check_paths('MASH_Audio', 'filename')

    # Arnold Checks
    if 'aiAreaLight' in node_types:
        check_paths('aiStandIn', 'dso')
        check_paths('aiVolume', 'filename')
        check_paths('aiPhotometricLight', 'aiFilename')

    # Redshift Checks
    if 'RedshiftPhysicalLight' in node_types:
        check_paths('RedshiftProxyMesh', 'fileName')
        check_paths('RedshiftVolumeShape', 'fileName')
        check_paths('RedshiftNormalMap', 'tex0')
        check_paths('RedshiftDomeLight', 'tex0')
        check_paths('RedshiftIESLight', 'profile')

    # Golaem Checks
    if 'CrowdEntityTypeNode' in node_types:
        check_paths('SimulationCacheProxyManager', 'destinationTerrainFile', accepts_empty=True)
        check_paths('SimulationCacheProxyManager', 'skinningShaderFile', accepts_empty=True)
        check_paths('CrowdEntityTypeNode', 'characterFile', accepts_empty=True)
        check_paths('CharacterMakerLocator', 'currentFile', accepts_empty=True)
        check_paths('TerrainLocator', 'navMeshFile', accepts_empty=True)
        check_paths('SimulationCacheProxy', 'inputCacheDir', accepts_empty=True)
        # Multiple Files
        check_paths('SimulationCacheProxy', 'characterFiles', accepts_empty=True, checks_multiple_paths=True)
        check_paths('CrowdManagerNode', 'characterFiles', accepts_empty=True, checks_multiple_paths=True)

    if len(incorrect_path_nodes) == 0:
        cmds.button("status_" + item_id, e=True, bgc=pass_color, l='',
                    c=lambda args: print_message('All file nodes currently sourced from the network.'))
        issues_found = 0
    else:
        cmds.button("status_" + item_id, e=True, bgc=error_color, l='?', c=lambda args: warning_other_network_paths())
        issues_found = len(incorrect_path_nodes)

    cmds.text("output_" + item_id, e=True, l=len(incorrect_path_nodes))

    # Manage Message
    string_message = ' paths aren\'t'
    if len(incorrect_path_nodes) == 1:
        string_message = ' path isn\'t'

    # Patch Function ----------------------
    def warning_other_network_paths():
        user_input = cmds.confirmDialog(
            title=item_name,
            message=str(len(incorrect_path_nodes)) + string_message + ' pointing to the network drive. \n'
                                                                      'Please change it to a network location. '
                                                                      '\n\n(Too see a list of nodes, '
                                                                      'generate a full report)',
            button=['OK', 'Select Nodes', 'Ignore Issue'],
            defaultButton='OK',
            cancelButton='Ignore Issue',
            dismissString='Ignore Issue',
            icon="warning")

        if user_input == 'Select Nodes':
            try:
                only_nodes = []
                for rejected_node in incorrect_path_nodes:
                    only_nodes.append(rejected_node[0])
                cmds.select(only_nodes)
            except Exception as e:
                logger.debug(str(e))
                cmds.warning('Sorry, something went wrong when selecting the nodes.')
        else:
            cmds.button("status_" + item_id, e=True, l='')

    # Return string for report ------------
    issue_string = "issues"
    if issues_found == 1:
        issue_string = "issue"
    if issues_found > 0:
        string_status = str(issues_found) + ' ' + issue_string + ' found.\n'
        for bad_node in incorrect_path_nodes:
            string_status = string_status + '"' + bad_node[0] + '" of the type "' + bad_node[
                1] + '" isn\'t pointing to the the network drive. Your paths should be sourced from the network.\n'
    else:
        string_status = str(issues_found) + ' issues found. All paths were sourced from the network'
    return '\n*** ' + item_name + " ***\n" + string_status


# Checklist Functions End Here ===================================================================


def print_message(message, as_warning=False, as_heads_up_message=False):
    if as_warning:
        cmds.warning(message)
    elif as_heads_up_message:
        cmds.headsUpMessage(message, verticalOffset=150, time=5.0)
    else:
        print(message)


def settings_apply_changes(reset_default=False):
    settings_buffer = checklist_settings.get('settings_text_fields')

    # Resetting Fields
    if reset_default:
        for item in settings_buffer:
            cmds.textField(item, q=True, text=True)

            if 'settings_warning_' in item:
                item_id = int(item.replace('settings_warning_', ''))

                cmds.textField(item, e=True, text=settings_default_checklist_values.get(item_id)[1][0])

            if 'settings_list_error_' in item:
                item_id = int(item.replace('settings_list_error_', ''))

                combined_values = ''
                for array_item in settings_default_checklist_values.get(item_id)[1]:
                    combined_values = str(combined_values) + str(array_item) + ', '

                if len(settings_default_checklist_values.get(item_id)[1]) > 0:
                    combined_values = combined_values[:-2]

                cmds.textField(item, e=True, text=combined_values)

            if 'settings_1d_error_' in item:
                item_id = int(item.replace('settings_1d_error_', ''))

                cmds.textField(item, e=True, text=settings_default_checklist_values.get(item_id)[1])

            if 'settings_2d_error_' in item:
                item_id = int(item.replace('settings_2d_error_', ''))

                cmds.textField(item, e=True, text=settings_default_checklist_values.get(item_id)[1][1])

    # Writing / Applying
    for item in settings_buffer:
        stored_value = cmds.textField(item, q=True, text=True)

        if 'settings_warning_' in item:
            item_id = item.replace('settings_warning_', '')
            if stored_value.isdigit():
                checklist_items[int(item_id)][1][0] = int(stored_value)
            else:
                checklist_items[int(item_id)][1][0] = stored_value

        if 'settings_list_error_' in item:
            item_id = item.replace('settings_list_error_', '')
            return_list = []
            value_as_list = stored_value.split(',')
            # Convert to number if possible
            for obj in value_as_list:
                if obj.isdigit():
                    return_list.append(int(obj))
                else:
                    return_list.append(obj)
            checklist_items[int(item_id)][1] = return_list

        if 'settings_1d_error_' in item:
            item_id = item.replace('settings_1d_error_', '')
            if stored_value.isdigit():
                checklist_items[int(item_id)][1] = int(stored_value)
            else:
                checklist_items[int(item_id)][1] = stored_value

        if 'settings_2d_error_' in item:
            item_id = item.replace('settings_2d_error_', '')
            if stored_value.isdigit():
                checklist_items[int(item_id)][1][1] = int(stored_value)
            else:
                checklist_items[int(item_id)][1][1] = stored_value


# Used to Export Full Report:
def export_report_to_txt(input_list):
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir + 'tmp.txt'

    f = open(txt_file, 'w')

    output_string = script_name + " Full Report:\n"

    for obj in input_list:
        output_string = output_string + obj + "\n\n"

    f.write(output_string)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)


# Import Settings
def settings_import_state():
    file_name = cmds.fileDialog2(fileFilter=script_name + " Settings (*.txt)", dialogStyle=2, fileMode=1,
                                 okCaption='Import', caption='Importing Settings for "' + script_name + '"') or []

    if len(file_name) > 0:
        settings_file = file_name[0]
        file_exists = True
    else:
        file_exists = False

    if file_exists:
        try:
            file_handle = open(settings_file, 'r')
        except Exception as e:
            logger.debug(str(e))
            file_exists = False
            cmds.warning("Couldn't read the file. Please make sure the selected file is accessible.")

    if file_exists:
        read_string = file_handle.read()

        imported_settings = read_string.split('\n')

        settings_buffer = checklist_settings.get('settings_text_fields')
        for txt_field in settings_buffer:
            logger.debug(str(txt_field))
            for value in imported_settings:
                extracted_values = value.split(':"')
                if len(extracted_values) > 1:
                    cmds.textField(extracted_values[0], e=True, text=extracted_values[1].replace('"', ''))


# Export Settings
def settings_export_state():
    file_name = cmds.fileDialog2(fileFilter=script_name + " Settings (*.txt)", dialogStyle=2, okCaption='Export',
                                 caption='Exporting Settings for "' + script_name + '"') or []

    if len(file_name) > 0:
        settings_file = file_name[0]
        successfully_created_file = True
    else:
        settings_file = None
        successfully_created_file = False

    if successfully_created_file:
        try:
            file_handle = open(settings_file, 'w')
        except Exception as e:
            file_handle = None
            logger.debug(str(e))
            successfully_created_file = False
            cmds.warning("Couldn't write to file. Please make sure the saving location is accessible.")

    if successfully_created_file:
        settings_name_value = []
        settings_buffer = checklist_settings.get('settings_text_fields')

        for stx in settings_buffer:
            stored_value = cmds.textField(stx, q=True, text=True)
            settings_name_value.append(str(stx) + ':"' + str(stored_value) + '"')

        output_string = script_name + ':\n'

        for line in settings_name_value:
            output_string = output_string + line + "\n"

        file_handle.write(output_string)
        file_handle.close()
        print('File exported to "' + settings_file + '"')


def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
            obj (string) - object to extract short name
    """
    short_name = ''
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path) - 1]
    return short_name


# Build GUI
get_persistent_settings_render_checklist()
if __name__ == '__main__':
    # logger.setLevel(logging.DEBUG)
    build_gui_gt_render_checklist()
