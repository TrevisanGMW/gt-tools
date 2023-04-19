"""
Drag and drop this file into the viewport to run the installer for GT-Tools
"""
import sys
import os
import glob
import shutil
import stat
import traceback
import time
import maya.cmds as cmds


def onMayaDroppedPythonFile(*args):
    """
    Runs when file is dropped into the Maya's viewport
    """
    try:
        package_name = "gt-tools"
        source_dir = os.path.dirname(__file__)
        source_path = os.path.normpath(os.path.join(source_dir, "scripts", package_name))
        
        # Make sure this installer is relative to the main tool.
        relative_path = os.path.join(source_path, "weights_editor.py")
        if not os.path.exists(relative_path):
            raise RuntimeError("Unable to find 'scripts/weights_editor.py' relative to this installer file.")

        # Suggest installing in user's script preferences.
        prefs_dir = os.path.dirname(cmds.about(preferences=True))
        scripts_dir = os.path.normpath(os.path.join(prefs_dir, "scripts"))

        continue_option = "Continue"
        manual_option = "No, let me choose"
        cancel_option = "Cancel"

        dialog = cmds.confirmDialog(
            message=(
                "The weights editor tool will be installed in a new folder here:<br>"
                "<i>{}</i>".format(os.path.normpath(os.path.join(scripts_dir, package_name)))),
            title="Installation path", icon="warning",
            button=[continue_option, manual_option, cancel_option],
            cancelButton=cancel_option, dismissString=cancel_option)

        if dialog == continue_option:
            install_path = scripts_dir
        elif dialog == manual_option:
            install_path = None
        else:
            return
        
        # Open file picker to choose where to install to.
        if install_path is None:
            results = cmds.fileDialog2(
                fileMode=3,
                okCaption="Install here",
                caption="Pick a folder to install to",
                dir=scripts_dir)
            
            # Exit if it was cancelled.
            if not results:
                return
            
            install_path = os.path.normpath(results[0])
        
        # Check if install path is in Python's path.
        python_paths = [os.path.normpath(path) for path in sys.path]
        print(install_path)
        print(python_paths)
        if install_path not in python_paths:
            cancel_option = "Cancel"

            dialog = cmds.confirmDialog(
                message=(
                    "Uh oh! Python can't see the path you picked:<br>"
                    "<i>{}</i><br><br>"
                    "This means the tool won't run unless you add this path to your environment variables using <b>Maya.env</b> or <b>userSetup.py</b>."
                    "<br><br>"
                    "Would you like to continue anyways?".format(install_path)),
                title="Path not found in Python's paths!", icon="warning",
                button=["Continue", cancel_option],
                cancelButton=cancel_option, dismissString=cancel_option)
            
            if dialog == cancel_option:
                return

        # If it already exists, asks if it's ok to overwrite.
        tool_path = os.path.join(install_path, package_name)
        if os.path.exists(tool_path):
            dialog = cmds.confirmDialog(
                message=(
                    "This folder already exists:<br>"
                    "<i>{}</i><br><br>"
                    "Continue to overwrite it?".format(tool_path)),
                title="Warning!", icon="warning",
                button=["OK", "Cancel"],
                cancelButton="Cancel", dismissString="Cancel")
            
            if dialog == "Cancel":
                return

            # May need to tweak permissions before deleting.
            # for root, dirs, files in os.walk(tool_path, topdown=False):
                # for name in files + dirs:
                    # os.chmod(os.path.join(root, name), stat.S_IWUSR)

            #shutil.rmtree(tool_path)
        print(tool_path)
        # Windows may throw an 'access denied' exception doing a copytree right after a rmtree.
        # Forcing it a slight delay seems to solve it.
        time.sleep(1)
        
        # Copy tool's directory over.
        #shutil.copytree(source_path, tool_path)

        # Display success!
        cmds.confirmDialog(
            message=(
                "The tool has been successfully installed!<br><br>"
                "If you want to remove it then simply delete this folder:<br>"
                "<i>{}</i><br><br>"
                "Run the tool from the script editor by executing the following:<br>"
                "<b>from weights_editor_tool import weights_editor<br>"
                "weights_editor.run()</b>".format(tool_path)),
            title="Install successful!",
            button=["OK"])
    except Exception as e:
        # Display error message if an exception was raised.
        print(traceback.format_exc())
