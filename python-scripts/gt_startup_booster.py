"""
 GT Startup Booster - A script for managing which plugins get loaded when starting Maya.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-20 - github.com/TrevisanGMW
 
 1.1 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.1.1 - 2022-07-11
 Added logging
 Added patch to version
 PEP8 Cleanup
  
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

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as OpenMayaUI
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_startup_booster")
logger.setLevel(logging.INFO)

# Script Version
script_version = "1.1.1"

# Script Version
script_name = "GT Startup Booster"


def build_gui_startup_booster():
    """ Builds the UI for GT Startup Booster"""
    if cmds.window("build_gui_startup_booster", exists=True):
        cmds.deleteUI("build_gui_startup_booster")

        # main dialog Start Here =================================================================================

    window_gui_startup_booster = cmds.window("build_gui_startup_booster",
                                             title='GT Startup Booster - (v' + script_version + ')',
                                             titleBar=True, minimizeButton=False, maximizeButton=False, sizeable=True)
    cmds.window(window_gui_startup_booster, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 330)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 260), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_startup_booster())
    cmds.separator(h=3, style='none', p=content_main)  # Empty Space

    cmds.separator(h=5, style='none')  # Empty Space

    cell_size = 65
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('Plugin File')
    cmds.text('Auto Load')
    cmds.text('Installed')
    cmds.text('Control')

    plugin_name_font = 'smallPlainLabelFont'

    # Arnold
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"mtoa.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('mtoa_autoload', label='...', bgc=(.2, .2, .2))
    cmds.text('mtoa_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Arnold', bgc=(.3, .3, .3))

    # Redshift
    cmds.separator(h=2, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"redshift4maya.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('redshift4maya_autoload', label='...', bgc=(.2, .2, .2))
    cmds.text('redshift4maya_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Redshift', bgc=(.3, .3, .3))

    # Bifrost
    cmds.separator(h=2, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"Boss.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('Boss_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('Boss_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    cmds.text('"bifmeshio.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('bifmeshio_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('bifmeshio_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    cmds.text('"bifrostGraph.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('bifrostGraph_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('bifrostGraph_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    cmds.text('"bifrostvisplugin.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('bifrostvisplugin_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('bifrostvisplugin_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    cmds.text('"mayaVnnPlugin.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('mayaVnnPlugin_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('mayaVnnPlugin_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    cmds.text('"bifrostshellnode.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('bifrostshellnode_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('bifrostshellnode_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bifrost', bgc=(.3, .3, .3))

    # Bullet
    cmds.separator(h=2, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"AbcBullet.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('AbcBullet_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('AbcBullet_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bullet', bgc=(.3, .3, .3))

    cmds.text('"bullet.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('bullet_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('bullet_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='Bullet', bgc=(.3, .3, .3))

    # MASH
    cmds.separator(h=2, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"MASH.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('MASH_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('MASH_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='MASH', bgc=(.3, .3, .3))

    # xGen
    cmds.separator(h=2, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=4,
                         columnWidth=[(1, 110), (2, cell_size), (3, cell_size), (4, cell_size)],
                         cs=[(1, 10), (2, 5), (3, 5), (4, 5)])
    cmds.text('"xgenToolkit.mll"', bgc=(.2, .2, .2), fn=plugin_name_font)
    cmds.text('xgenToolkit_autoload', label='... ', bgc=(.2, .2, .2))
    cmds.text('xgenToolkit_loaded', label='...', bgc=(.3, .3, .3))
    cmds.text(label='xGen', bgc=(.3, .3, .3))

    cmds.rowColumnLayout(p=content_main, numberOfColumns=6, columnWidth=[(1, 318)], cs=[(1, 10)])
    cmds.separator(h=5)
    cmds.separator(h=15, style='none')  # Empty Space

    cell_size = 103
    cmds.rowColumnLayout(p=content_main, numberOfColumns=3,
                         columnWidth=[(1, cell_size), (2, cell_size), (3, cell_size), (4, cell_size), (5, cell_size),
                                      (6, cell_size)], cs=[(1, 10), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5)])

    btns_height = 20
    btns_bgc = (.2, .2, .2)
    cmds.text('- Arnold -', bgc=btns_bgc)
    cmds.text('- Redshift -', bgc=btns_bgc)
    cmds.text('- Bifrost -', bgc=btns_bgc)

    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading Arnold plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_arnold(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading Redshift plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_redshift(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading Bifrost plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_bifrost(), font='tinyBoldLabelFont')

    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for Arnold.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_arnold(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for Redshift.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_redshift(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for Bifrost.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_bifrost(), font='tinyBoldLabelFont')

    cmds.separator(h=3, style='none')  # Empty Space
    cmds.rowColumnLayout(p=content_main, numberOfColumns=3,
                         columnWidth=[(1, cell_size), (2, cell_size), (3, cell_size), (4, cell_size), (5, cell_size),
                                      (6, cell_size)], cs=[(1, 10), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5)])

    cmds.text('- Bullet -', bgc=btns_bgc)
    cmds.text('- MASH -', bgc=btns_bgc)
    cmds.text('- xGen -', bgc=btns_bgc)

    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading Bullet plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_bullet(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading MASH plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_mash(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading xGen plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_xgen(), font='tinyBoldLabelFont')

    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for Bullet.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_bullet(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for MASH.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_mash(), font='tinyBoldLabelFont')
    cmds.iconTextButton(style='iconAndTextHorizontal', image1='redrawPaintEffects.png', label='  Auto Load',
                        statusBarMessage='This button will toggle the auto load option for xGen.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: toggle_startup_booster_xgen(), font='tinyBoldLabelFont')

    cmds.rowColumnLayout(p=content_main, numberOfColumns=6, columnWidth=[(1, 318)], cs=[(1, 10)])
    cmds.separator(h=2, style='none')  # Empty Space

    cmds.rowColumnLayout(p=content_main, numberOfColumns=6, columnWidth=[(1, 210)], cs=[(1, 10), (2, 5)])
    custom_plugin_input = cmds.textField(pht=" Other Plugins  (use comma for multiple)",
                                         enterCommand=lambda x: add_button_custom(
                                             cmds.textField(custom_plugin_input, q=True, text=True)),
                                         font='smallBoldLabelFont')

    cmds.iconTextButton(style='iconAndTextHorizontal', image1='openScript.png', label=' Shelf Button',
                        statusBarMessage='This button creates a shelf button for auto loading xGen plugins.',
                        olc=[1, 0, 0], enableBackground=True, bgc=btns_bgc, h=btns_height, marginWidth=10,
                        command=lambda: add_button_custom(cmds.textField(custom_plugin_input, q=True, text=True)),
                        font='tinyBoldLabelFont')

    cmds.rowColumnLayout(p=content_main, numberOfColumns=6, columnWidth=[(1, 318)], cs=[(1, 10)])
    cmds.separator(h=5)
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.rowColumnLayout(p=content_main, numberOfColumns=3, columnWidth=[(1, 157), (2, 157), (3, 10)],
                         cs=[(1, 10), (2, 5), (3, 5)])
    cmds.separator(h=10, p=content_main, st="none")
    cmds.button(l="Refresh", c=lambda x: refresh_startup_booster_ui(), w=100, bgc=(.6, .6, .6))
    cmds.button(l="Optimize", c=lambda x: optimize_all_plugins(), bgc=(.6, .6, .6))
    cmds.separator(h=10, st="none")

    def refresh_startup_booster_ui(plugins_to_load=None):
        """
        Refresh UI to show current state of plugins 
        
        Args:
            plugins_to_load (list): A list of plugins (strings) to load. If not provided refresh all.
                    
        """
        active_bgc = (.5, 0, 0)
        inactive_bgc = (0, .5, 0)
        loaded_bgc = (0, .5, 0)
        not_loaded_bgc = (.2, .2, .2)
        not_installed_bgc = (.2, .2, .2)

        plugins = ['mtoa', 'redshift4maya', 'bifmeshio', 'bifrostGraph', 'bifrostshellnode',
                   'bifrostvisplugin', 'Boss', 'mayaVnnPlugin', 'AbcBullet', 'bullet', 'MASH', 'xgenToolkit']

        if plugins_to_load:
            plugins = plugins_to_load

        main_progress_bar = mel.eval('$tmp = $gMainProgressBar')

        cmds.progressBar(main_progress_bar,
                         edit=True,
                         beginProgress=True,
                         isInterruptable=True,
                         status='"Loading Plug-ins...',
                         maxValue=len(plugins))

        for plugin in plugins:
            if cmds.progressBar(main_progress_bar, query=True, isCancelled=True):
                break
            is_plugin_installed = True
            try:
                if not cmds.pluginInfo(plugin, query=True, loaded=True):
                    cmds.loadPlugin(plugin, quiet=True)
            except Exception as e:
                is_plugin_installed = False
                logger.debug(str(e))

            if is_plugin_installed:
                # Auto Load
                if cmds.pluginInfo(plugin, q=True, autoload=True):
                    cmds.text(plugin + '_autoload', e=True, label='Active', bgc=active_bgc)
                else:
                    cmds.text(plugin + '_autoload', e=True, label='Inactive', bgc=inactive_bgc)
                # Loaded (Installed)
                if cmds.pluginInfo(plugin, q=True, loaded=True):
                    cmds.text(plugin + '_loaded', e=True, label='Yes', bgc=loaded_bgc)
                else:
                    cmds.text(plugin + '_loaded', e=True, label='No', bgc=not_loaded_bgc)
            else:
                cmds.text(plugin + '_autoload', e=True, label='...', bgc=not_installed_bgc)
                cmds.text(plugin + '_loaded', e=True, label='No', bgc=not_installed_bgc)

            cmds.progressBar(main_progress_bar, edit=True, step=1)

        cmds.progressBar(main_progress_bar, edit=True, endProgress=True)

    def toggle_startup_booster_arnold():
        """ Toggle the auto load checkbox for the Redshift plugin """

        plugin_name = 'mtoa'
        refresh_startup_booster_ui([plugin_name])

        plugin_status = cmds.pluginInfo(plugin_name, q=True, autoload=True)

        if plugin_status:
            cmds.pluginInfo(plugin_name, e=True, autoload=False)
        else:
            cmds.pluginInfo(plugin_name, e=True, autoload=True)

        refresh_startup_booster_ui([plugin_name])

    def toggle_startup_booster_redshift():
        """ Toggle the load checkbox for the Redshift plugin """

        plugin_name = 'redshift4maya'
        refresh_startup_booster_ui([plugin_name])

        plugin_status = cmds.pluginInfo(plugin_name, q=True, autoload=True)

        if plugin_status:
            cmds.pluginInfo(plugin_name, e=True, autoload=False)
        else:
            cmds.pluginInfo(plugin_name, e=True, autoload=True)

        refresh_startup_booster_ui([plugin_name])

    def toggle_startup_booster_bifrost():
        """ Toggle the load checkbox for the Bifrost plugin """

        plugin_names = ['bifmeshio', 'bifrostGraph', 'bifrostshellnode', 'bifrostvisplugin', 'Boss', 'mayaVnnPlugin']

        refresh_startup_booster_ui(plugin_names)

        plugin_status = cmds.pluginInfo('bifrostGraph', q=True, autoload=True)

        for plugin in plugin_names:
            if plugin_status:
                cmds.pluginInfo(plugin, e=True, autoload=False)
            else:
                cmds.pluginInfo(plugin, e=True, autoload=True)

        refresh_startup_booster_ui(plugin_names)

    def toggle_startup_booster_bullet():
        """ Toggle the load checkbox for the Bullet plugin """

        plugin_names = ['AbcBullet', 'bullet']

        refresh_startup_booster_ui(plugin_names)

        plugin_status = cmds.pluginInfo('bullet', q=True, autoload=True)

        for plugin in plugin_names:
            if plugin_status:
                cmds.pluginInfo(plugin, e=True, autoload=False)
            else:
                cmds.pluginInfo(plugin, e=True, autoload=True)

        refresh_startup_booster_ui(plugin_names)

    def toggle_startup_booster_mash():
        """ Toggle the load checkbox for the MASH plugin """

        plugin_name = 'MASH'
        refresh_startup_booster_ui([plugin_name])

        plugin_status = cmds.pluginInfo(plugin_name, q=True, autoload=True)

        if plugin_status:
            cmds.pluginInfo(plugin_name, e=True, autoload=False)
        else:
            cmds.pluginInfo(plugin_name, e=True, autoload=True)

        refresh_startup_booster_ui([plugin_name])

    def toggle_startup_booster_xgen():
        """ Toggle the oad checkbox for the MASH plugin """

        plugin_name = 'xgenToolkit'
        refresh_startup_booster_ui([plugin_name])

        plugin_status = cmds.pluginInfo(plugin_name, q=True, autoload=True)

        if plugin_status:
            cmds.pluginInfo(plugin_name, e=True, autoload=False)
        else:
            cmds.pluginInfo(plugin_name, e=True, autoload=True)

        refresh_startup_booster_ui([plugin_name])

    def optimize_all_plugins():
        """ Deactivate load for all heavy plugins """

        refresh_startup_booster_ui()
        plugins = ['mtoa', 'redshift4maya', 'bifmeshio', 'bifrostGraph', 'bifrostshellnode',
                   'bifrostvisplugin', 'Boss', 'mayaVnnPlugin', 'AbcBullet', 'bullet', 'MASH', 'xgenToolkit']

        for plugin in plugins:
            try:
                cmds.pluginInfo(plugin, e=True, autoload=False)
            except Exception as e:
                logger.debug(str(e))
        refresh_startup_booster_ui()
        message = 'All heavy plugins have been optimized to not open automatically.'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        sys.stdout.write(message)

    def add_button_arnold():
        """ Create a button for manually loading the Arnold plugin """
        create_shelf_button(
            "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - github.com/"
            "TrevisanGMW\n\n This button will try to load a plugin in case it's not already loaded.\n "
            "This is used to make Maya open faster by not auto loading heavy plugins during startup.\n \n"
            " How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the plugins you want"
            " to manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut for loading the "
            "plugin.\n 3. When you need the plugin, use the shelf button to load it.\n \n\"\"\"\nplugins_to_load"
            " = ['mtoa']\n\ndef gtu_load_plugins(plugin_list):\n    ''' \n    Attempts to load provided plug-ins,"
            " then gives the user feedback about their current state. (Feedback through inView messages and "
            "stdout.write messages)\n    \n            Parameters:\n                plugin_list (list): A list"
            " of strings containing the name of the plug-ings yo uwant to load\n    \n    '''\n    "
            "already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n    # Load Plug-in\n   "
            " for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, loaded=True):\n      "
            "      try:\n                cmds.loadPlugin(plugin)\n                if cmds.pluginInfo(plugin, "
            "q=True, loaded=True):\n                    now_loaded.append(plugin)\n            except:\n      "
            "          not_installed.append(plugin)\n        else:\n            already_loaded.append(plugin)\n"
            "    \n    # Give Feedback\n    if len(not_installed) > 0:\n        message_feedback = ''\n        "
            "for str in not_installed:\n            message_feedback += str + ', '\n        is_plural = 'plug-ins"
            " don\\'t'\n        if len(not_installed) == 1:\n            is_plural = 'plug-in doesn\\'t'\n        "
            "message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + "
            "'</span> ' + is_plural + ' seem to be installed.'\n        cmds.inViewMessage(amg=message, "
            "pos='botLeft', fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural "
            "+ ' seem to be installed.')\n        \n    if len(now_loaded) > 0:\n        message_feedback = ''\n   "
            "     for str in now_loaded:\n            message_feedback += str + ', '\n        is_plural = 'plug-ins "
            "are'\n        if len(now_loaded) == 1:\n            is_plural = 'plug-in is'\n        message = "
            "'<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + "
            "'</span> ' + is_plural + ' now loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', "
            "fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' "
            "now loaded.')\n    \n    if len(already_loaded) > 0:\n        message_feedback = ''\n        "
            "for str in already_loaded:\n            message_feedback += str + ', '\n        is_plural = "
            "'plug-ins are'\n        if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n       "
            " message = '<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural +  "
            "' already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n# Run Script\n"
            "if __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
            label='Arnold', tooltip='This button will try to load Arnold in case it\'s not already loaded.',
            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">Arnold</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_redshift():
        """ Create a button for manually loading the Redshift plugin """
        create_shelf_button(
            "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - "
            "github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not already "
            "loaded.\n This is used to make Maya open faster by not auto loading heavy plugins during "
            "startup.\n \n How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the "
            "plugins you want to manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut for "
            "loading the plugin.\n 3. When you need the plugin, use the shelf button to load it.\n \n\"\"\"\n\n"
            "plugins_to_load = ['redshift4maya']\n\ndef gtu_load_plugins(plugin_list):\n    ''' \n    "
            "Attempts to load provided plug-ins, then gives the user feedback about their current state. "
            "(Feedback through inView messages and stdout.write messages)\n    \n            Parameters:\n           "
            "     plugin_list (list): A list of strings containing the name of the plug-ings yo uwant to load\n    "
            "\n    '''\n    already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n    "
            "# Load Plug-in\n    for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, "
            "loaded=True):\n            try:\n                cmds.loadPlugin(plugin)\n                "
            "if cmds.pluginInfo(plugin, q=True, loaded=True):\n                    now_loaded.append(plugin)\n      "
            "      except:\n                not_installed.append(plugin)\n        else:\n            "
            "already_loaded.append(plugin)\n    \n    # Give Feedback\n    if len(not_installed) > 0:\n        "
            "message_feedback = ''\n        for str in not_installed:\n            message_feedback += str + ', '\n "
            "       is_plural = 'plug-ins don\\'t'\n        if len(not_installed) == 1:\n            "
            "is_plural = 'plug-in doesn\\'t'\n        message = "
            "'<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> "
            "' + is_plural + ' seem to be installed.'\n        cmds.inViewMessage(amg=message, pos='botLeft', "
            "fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' "
            "seem to be installed.')\n        \n    if len(now_loaded) > 0:\n        message_feedback = ''\n        "
            "for str in now_loaded:\n            message_feedback += str + ', '\n        "
            "is_plural = 'plug-ins are'\n        if len(now_loaded) == 1:\n            is_plural = 'plug-in is'\n     "
            "   message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  "
            "message_feedback[:-2] + '</span> ' + is_plural + ' now loaded.'\n        cmds.inViewMessage(amg=message, "
            "pos='botLeft', fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + "
            "is_plural + ' now loaded.')\n    \n    if len(already_loaded) > 0:\n        message_feedback = ''\n     "
            "   for str in already_loaded:\n            message_feedback += str + ', '\n        is_plural = "
            "'plug-ins are'\n        if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n        "
            "message = '<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural +  ' "
            "already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n# Run Script\n"
            "if __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
            label='RS', tooltip='This button will try to load Arnold in case it\'s not already loaded.',
            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">Redshift</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_bifrost():
        """ Create a button for manually loading the Bifrost plugin """
        create_shelf_button(
            "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - "
            "github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not already loaded."
            "\n This is used to make Maya open faster by not auto loading heavy plugins during startup.\n \n "
            "How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the plugins you want to "
            "manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut for loading the plugin."
            "\n 3. When you need the plugin, use the shelf button to load it.\n \n\"\"\"\nimport maya.cmds as "
            "cmds\nimport sys\n\nplugins_to_load = ['bifmeshio', 'bifrostGraph', 'bifrostshellnode', "
            "'bifrostvisplugin', 'Boss', 'mayaVnnPlugin']\n\ndef gtu_load_plugins(plugin_list):\n    ''' \n    "
            "Attempts to load provided plug-ins, then gives the user feedback about their current state. "
            "(Feedback through inView messages and stdout.write messages)\n    \n            Parameters:\n         "
            "       plugin_list (list): A list of strings containing the name of the plug-ings yo uwant to load\n    "
            "\n    '''\n    already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n    # Load Plug-in"
            "\n    for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, loaded=True):\n         "
            "   try:\n                cmds.loadPlugin(plugin)\n                if cmds.pluginInfo(plugin, q=True, "
            "loaded=True):\n                    now_loaded.append(plugin)\n            except:\n                "
            "not_installed.append(plugin)\n        else:\n            already_loaded.append(plugin)\n    \n    "
            "# Give Feedback\n    if len(not_installed) > 0:\n        message_feedback = ''\n        "
            "for str in not_installed:\n            message_feedback += str + ', '\n        "
            "is_plural = 'plug-ins don\\'t'\n        if len(not_installed) == 1:\n            "
            "is_plural = 'plug-in doesn\\'t'\n        message = "
            "'<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> '"
            " + is_plural + ' seem to be installed.'\n        cmds.inViewMessage(amg=message, pos='botLeft', "
            "fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + "
            "' seem to be installed.')\n        \n    if len(now_loaded) > 0:\n        message_feedback = ''\n       "
            " for str in now_loaded:\n            message_feedback += str + ', '\n        "
            "is_plural = 'plug-ins are'\n        if len(now_loaded) == 1:\n            is_plural = 'plug-in is'\n     "
            "   message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  "
            "message_feedback[:-2] + '</span> ' + is_plural + ' now loaded.'\n        "
            "cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' now loaded.')\n    \n    "
            "if len(already_loaded) > 0:\n        message_feedback = ''\n        for str in already_loaded:\n       "
            "     message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n        "
            "if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n        "
            "message = '<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural +  "
            "' already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n      "
            "  sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n"
            "# Run Script\nif __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
            label='Bifrost', tooltip='This button will try to load Arnold in case it\'s not already loaded.',
            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">Bifrost</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_bullet():
        """ Create a button for manually loading the Bullet plugin """
        create_shelf_button(
            "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - "
            "github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not already loaded."
            "\n This is used to make Maya open faster by not auto loading heavy plugins during startup.\n \n "
            "How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the plugins you want to "
            "manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut for loading the plugin."
            "\n 3. When you need the plugin, use the shelf button to load it.\n \n\"\"\"\nimport maya.cmds as "
            "cmds\nimport sys\n\nplugins_to_load = ['AbcBullet', 'bullet']\n\ndef gtu_load_plugins(plugin_list):"
            "\n    ''' \n    Attempts to load provided plug-ins, then gives the user feedback about their current "
            "state. (Feedback through inView messages and stdout.write messages)\n    \n            Parameters:\n  "
            "              plugin_list (list): A list of strings containing the name of the plug-ings yo uwant to"
            " load\n    \n    '''\n    already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n   "
            " # Load Plug-in\n    for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, "
            "loaded=True):\n            try:\n                cmds.loadPlugin(plugin)\n                "
            "if cmds.pluginInfo(plugin, q=True, loaded=True):\n                    now_loaded.append(plugin)\n     "
            "       except:\n                not_installed.append(plugin)\n        else:\n            "
            "already_loaded.append(plugin)\n    \n    # Give Feedback\n    if len(not_installed) > 0:\n       "
            " message_feedback = ''\n        for str in not_installed:\n            message_feedback += str + ', '\n "
            "       is_plural = 'plug-ins don\\'t'\n        if len(not_installed) == 1:\n            is_plural = "
            "'plug-in doesn\\'t'\n        message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' "
            "+  message_feedback[:-2] + '</span> ' + is_plural + ' seem to be installed.'\n        "
            "cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' seem to be installed.')\n        \n    "
            "if len(now_loaded) > 0:\n        message_feedback = ''\n        for str in now_loaded:\n            "
            "message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n        if len(now_loaded) == 1:\n "
            "           is_plural = 'plug-in is'\n        message = "
            "'<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> ' +"
            " is_plural + ' now loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n"
            "        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' now loaded.')\n    \n    "
            "if len(already_loaded) > 0:\n        message_feedback = ''\n        for str in already_loaded:\n         "
            "   message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n        "
            "if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n        "
            "message = '<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural +  "
            "' already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n       "
            " sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n# Run Script\n"
            "if __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
            label='Bullet', tooltip='This button will try to load Arnold in case it\'s not already loaded.',
            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">Bullet</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_mash():
        """ Create a button for manually loading the MASH plugin """
        create_shelf_button(
            "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - "
            "github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not already loaded."
            "\n This is used to make Maya open faster by not auto loading heavy plugins during startup.\n \n "
            "How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the plugins you want to "
            "manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut for loading the plugin."
            "\n 3. When you need the plugin, use the shelf button to load it.\n \n\"\"\"\nimport maya.cmds as cmds"
            "\nimport sys\n\nplugins_to_load = ['MASH']\n\ndef gtu_load_plugins(plugin_list):\n    ''' \n    "
            "Attempts to load provided plug-ins, then gives the user feedback about their current state. "
            "(Feedback through inView messages and stdout.write messages)\n    \n            Parameters:\n        "
            "        plugin_list (list): A list of strings containing the name of the plug-ings yo uwant to load\n "
            "   \n    '''\n    already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n    "
            "# Load Plug-in\n    for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, "
            "loaded=True):\n            try:\n                cmds.loadPlugin(plugin)\n                "
            "if cmds.pluginInfo(plugin, q=True, loaded=True):\n                    now_loaded.append(plugin)\n   "
            "         except:\n                not_installed.append(plugin)\n        else:\n            "
            "already_loaded.append(plugin)\n    \n    # Give Feedback\n    if len(not_installed) > 0:\n        "
            "message_feedback = ''\n        for str in not_installed:\n            message_feedback += str + ', '\n  "
            "      is_plural = 'plug-ins don\\'t'\n        if len(not_installed) == 1:\n            "
            "is_plural = 'plug-in doesn\\'t'\n        message = '<span style=\\\"color:#FF0000;text-decoration:"
            "underline;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural + ' seem to be installed.'\n      "
            "  cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' seem to be installed.')\n        \n    "
            "if len(now_loaded) > 0:\n        message_feedback = ''\n        for str in now_loaded:\n            "
            "message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n        if len(now_loaded) == 1:\n"
            "            is_plural = 'plug-in is'\n        message = "
            "'<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> '"
            " + is_plural + ' now loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', "
            "fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' now loaded.')\n"
            "    \n    if len(already_loaded) > 0:\n        message_feedback = ''\n        for str in already_loaded:\n"
            "            message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n        "
            "if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n        message = "
            "'<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural +  "
            "' already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n# Run Script\n"
            "if __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
            label='MASH', tooltip='This button will try to load Arnold in case it\'s not already loaded.',
            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">MASH</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_xgen():
        """ Create a button for manually loading the xGen plugin """
        create_shelf_button("\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan -"
                            " github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not "
                            "already loaded.\n This is used to make Maya open faster by not auto loading heavy"
                            " plugins during startup.\n \n How to use it:\n 1. Use GT Startup Booster and turn "
                            "off \"Auto Load\" for the plugins you want to manually load.\n 2. Click on  "
                            "\"Add Shelf Button\" so it creates a shortcut for loading the plugin.\n 3. When you "
                            "need the plugin, use the shelf button to load it.\n \n\"\"\"\nimport maya.cmds as "
                            "cmds\nimport sys\n\nplugins_to_load = ['xgenToolkit']\n\ndef gtu_load_plugins"
                            "(plugin_list):\n    ''' \n    Attempts to load provided plug-ins, then gives the "
                            "user feedback about their current state. (Feedback through inView messages and "
                            "stdout.write messages)\n    \n            Parameters:\n                plugin_list "
                            "(list): A list of strings containing the name of the plug-ings yo uwant to load\n    "
                            "\n    '''\n    already_loaded = []\n    not_installed = []\n    now_loaded = []\n    "
                            "\n    # Load Plug-in\n    for plugin in plugin_list:\n        if not cmds.pluginInfo"
                            "(plugin, q=True, loaded=True):\n            try:\n                cmds.loadPlugin"
                            "(plugin)\n                if cmds.pluginInfo(plugin, q=True, loaded=True):\n         "
                            "           now_loaded.append(plugin)\n            except:\n                "
                            "not_installed.append(plugin)\n        else:\n            already_loaded.append(plugin)"
                            "\n    \n    # Give Feedback\n    if len(not_installed) > 0:\n        "
                            "message_feedback = ''\n        for str in not_installed:\n            "
                            "message_feedback += str + ', '\n        is_plural = 'plug-ins don\\'t'\n        "
                            "if len(not_installed) == 1:\n            is_plural = 'plug-in doesn\\'t'\n        "
                            "message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' +  "
                            "message_feedback[:-2] + '</span> ' + is_plural + ' seem to be installed.'\n        "
                            "cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
                            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' seem to be installed.')"
                            "\n        \n    if len(now_loaded) > 0:\n        message_feedback = ''\n        "
                            "for str in now_loaded:\n            message_feedback += str + ', '\n        "
                            "is_plural = 'plug-ins are'\n        if len(now_loaded) == 1:\n            "
                            "is_plural = 'plug-in is'\n        message = '<span style=\\\"color:#FF0000;"
                            "text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural + "
                            "' now loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, "
                            "alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' "
                            "now loaded.')\n    \n    if len(already_loaded) > 0:\n        message_feedback = ''\n"
                            "        for str in already_loaded:\n            message_feedback += str + ', '\n        "
                            "is_plural = 'plug-ins are'\n        if len(already_loaded) == 1:\n            "
                            "is_plural = 'plug-in is'\n        message = '<span style=\\\"color:#FF0000;\\\">' +  "
                            "message_feedback[:-2] + '</span> ' + is_plural +  ' already loaded.'\n        "
                            "cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
                            "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' already loaded.')\n\n\n"
                            "# Run Script\nif __name__ == '__main__':\n    gtu_load_plugins(plugins_to_load)",
                            label='xGen', tooltip='This button will try to load Arnold '
                                                  'in case it\'s not already loaded.',
                            image='openScript.png')
        cmds.inViewMessage(
            amg='<span style=\"color:#FFFF00;\">xGen</span> load button was added to your current shelf.',
            pos='botLeft', fade=True, alpha=.9)

    def add_button_custom(text_field_data):
        """
        Create a button for manually loading a custom 3rd party plugin 
        
        Args:
               text_field_data (string): The input text containing the name of the plugins you want to load.
        
        """
        plugins_to_load = '['
        is_text_valid = True
        if len(text_field_data) <= 0:
            is_text_valid = False
            cmds.warning('The input text is empty, please type the name of the plugin you want to load. '
                         '(e.g. "mtoa" for Arnold)')

        if is_text_valid:
            return_list = text_field_data.replace(' ', '').split(",")
            empty_objects = []
            for obj in return_list:
                if '' == obj:
                    empty_objects.append(obj)
            for obj in empty_objects:
                return_list.remove(obj)

            for item in return_list:
                plugins_to_load += '\'' + item + '\', '

            if plugins_to_load != '[':
                plugins_to_load = plugins_to_load[:-2] + ']'
            else:
                plugins_to_load = plugins_to_load + ']'

            if plugins_to_load == '[]':
                cmds.warning('The input text is invalid. '
                             'Please make sure you typed the name of every plugin separated by commas.')
            else:
                create_shelf_button(
                    "\"\"\"\n This button was generated using GT Startup Booster\n @Guilherme Trevisan - "
                    "github.com/TrevisanGMW\n\n This button will try to load a plugin in case it's not already "
                    "loaded.\n This is used to make Maya open faster by not auto loading heavy plugins during "
                    "startup.\n \n How to use it:\n 1. Use GT Startup Booster and turn off \"Auto Load\" for the "
                    "plugins you want to manually load.\n 2. Click on  \"Add Shelf Button\" so it creates a shortcut"
                    "for loading the plugin.\n 3. When you need the plugin, use the shelf button to load it."
                    "\n \n\"\"\"\nimport maya.cmds as cmds\nimport sys\n\nplugins_to_load = " + plugins_to_load +
                    "\n\ndef gtu_load_plugins(plugin_list):\n    ''' \n    Attempts to load provided plug-ins, "
                    "then gives the user feedback about their current state. (Feedback through inView messages and "
                    "stdout.write messages)\n    \n            Parameters:\n                plugin_list (list): "
                    "A list of strings containing the name of the plug-ings yo uwant to load\n    \n    '''\n    "
                    "already_loaded = []\n    not_installed = []\n    now_loaded = []\n    \n    # Load Plug-in\n   "
                    " for plugin in plugin_list:\n        if not cmds.pluginInfo(plugin, q=True, loaded=True):\n   "
                    "         try:\n                cmds.loadPlugin(plugin)\n                if cmds.pluginInfo"
                    "(plugin, q=True, loaded=True):\n                    now_loaded.append(plugin)\n            "
                    "except:\n                not_installed.append(plugin)\n        else:\n            "
                    "already_loaded.append(plugin)\n    \n    # Give Feedback\n    if len(not_installed) > 0:\n        "
                    "message_feedback = ''\n        for str in not_installed:\n            message_feedback += "
                    "str + ', '\n        is_plural = 'plug-ins don\\'t'\n        if len(not_installed) == 1:\n     "
                    "       is_plural = 'plug-in doesn\\'t'\n        message = '<span style=\\\"color:#FF0000;"
                    "text-decoration:underline;\\\">' +  message_feedback[:-2] + '</span> ' + is_plural + ' seem "
                    "to be installed.'\n        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)"
                    "\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' seem to be installed.')"
                    "\n        \n    if len(now_loaded) > 0:\n        message_feedback = ''\n        "
                    "for str in now_loaded:\n            message_feedback += str + ', '\n        is_plural = "
                    "'plug-ins are'\n        if len(now_loaded) == 1:\n            is_plural = 'plug-in is'\n      "
                    "  message = '<span style=\\\"color:#FF0000;text-decoration:underline;\\\">' + "
                    " message_feedback[:-2] + '</span> ' + is_plural + ' now loaded.'\n        "
                    "cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)\n        "
                    "sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' now loaded.')\n    \n    "
                    "if len(already_loaded) > 0:\n        message_feedback = ''\n        for str in already_loaded:\n "
                    "           message_feedback += str + ', '\n        is_plural = 'plug-ins are'\n       "
                    " if len(already_loaded) == 1:\n            is_plural = 'plug-in is'\n       "
                    " message = '<span style=\\\"color:#FF0000;\\\">' +  message_feedback[:-2] + '</span> "
                    "' + is_plural +  ' already loaded.'\n        cmds.inViewMessage(amg=message, pos='botLeft', "
                    "fade=True, alpha=.9)\n        sys.stdout.write(message_feedback[:-2] + ' ' + is_plural + ' "
                    "already loaded.')\n\n\n# Run Script\nif __name__ == '__main__':\n    "
                    "gtu_load_plugins(plugins_to_load)",
                    label='Custom',
                    tooltip='This button will try to load a custom plugin in case it\'s not already loaded.',
                    image='openScript.png')
                cmds.inViewMessage(
                    amg='<span style=\"color:#FFFF00;\">A custom</span> load button was added to your current shelf.',
                    pos='botLeft', fade=True, alpha=.9)

    # Initial Refresh
    # refresh_startup_booster_ui()

    # Show and Lock Window
    cmds.showWindow(window_gui_startup_booster)
    cmds.window(window_gui_startup_booster, e=True, s=False)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_gui_startup_booster)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_gui_startup_booster)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/out_time.png')
    widget.setWindowIcon(icon)

    # main dialog Ends Here =================================================================================


def create_shelf_button(command,
                        label='',
                        tooltip='',
                        image=None,  # Default Python Icon
                        label_color=(1, 0, 0),  # Default Red
                        label_bgc_color=(0, 0, 0, 1),  # Default Black
                        bgc_color=None
                        ):
    """
    Add a shelf button to the current shelf (according to the provided parameters)
    
    Args:
        command (str): A string containing the code or command you want the button to run when clicking on it.
                       e.g. "print("Hello World")"
        label (str): The label of the button. This is the text you see below it.
        tooltip (str): The help message you get when hovering the button.
        image (str): The image used for the button (defaults to Python icon if none)
        label_color (tuple): A tuple containing three floats, these are RGB 0 to 1 values to determine
                             the color of the label.
        label_bgc_color (tuple): A tuple containing four floats, these are RGBA 0 to 1 values to determine
                                 the background of the label.
        bgc_color (tuple):  A tuple containing three floats, these are RGB 0 to 1 values to determine
                            the background of the icon
    
    """
    maya_version = int(cmds.about(v=True))

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


def build_gui_help_startup_booster():
    """ Builds the Help UI for GT Startup Booster """
    window_name = "build_gui_help_startup_booster"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    help_font = 'smallPlainLabelFont'
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.text(l=script_name + ' helps decrease the time Maya\n takes to load before becoming fully functional',
              align="center")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='How It works:', align="center", fn="boldLabelFont")
    cmds.text(l='Not all plugins are used every time Maya is opened,\n '
                'but they are usually still loaded during startup.\n This causes the startup time to be quite slow.',
              align="center", font=help_font)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='This script aims to fix that, by helping you skip the heavy \n'
                'plugins while still having easy access to them.',
              align="center", font=help_font)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='1st: Optimize\n2nd: Create Shelf Buttons\n3rd: Enjoy faster startups', align="center", font=help_font)

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Plugin List:', align="center", fn="boldLabelFont")
    cmds.text(l='This is a list of common plugins that are\n usually automatically loaded by default.', align="center",
              font=help_font)
    cmds.text(l='Plugin File: Name of the file used by the plugin.\nAuto Load: Is this plugin '
                'automatically loading?\nInstalled: Is the plugin installed?\nControl: General name of the plugin.',
              align="center", font=help_font)

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='"Shelf Button" and "Auto Load" Buttons:', align="center", fn="boldLabelFont")
    cmds.text(l='Shelf Button: Creates a Shelf Button (under the current shelf)\n'
                'to load the plugin and give you feedback on its current state.', align="center", font=help_font)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='Auto Load: Toggles the Auto Load function of the plugin.\n(same as "Auto Load" in the plugin manager)',
              align="center", font=help_font)

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Custom Shelf Button:', align="center", fn="boldLabelFont")
    cmds.text(l='This script couldn\'t account for every heavy 3rd party plug-in.'
                '\nThis shouldn\'t be an issue as you can manually add any plugin.', align="center", font=help_font)
    cmds.text(l='Just manually deactivate your third party plugin by going to \n'
                '"Windows > Settings/Preferences > Plug-in Manager"', align="center", font=help_font)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='Then create a custom load button using\n the textField that says "Other Plugins"', align="center",
              font=help_font)

    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
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


# Build UI
if __name__ == "__main__":
    # logger.setLevel(logging.DEBUG)
    build_gui_startup_booster()
