"""
Drag and drop this file into the viewport to run the package installer
"""
import sys
import os


def onMayaDroppedPythonFile(*args):
    """
    Runs when file is dropped into the Maya's viewport
    The name of this function is what Maya expects/uses as entry point, so it cannot be changed
    """
    if sys.version_info.major < 3:
        # String formatting for this error should remain compatible to Python 2 to guarantee feedback
        user_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
        error = "Incompatible Python Version. Expected to find 3+. Found version: " + user_version
        error += "For Python 2, use an older version of GT-Tools below 3. (e.g. 2.5.5)\n"
        raise ImportError(error)

    # Initial Feedback
    print("_"*40)
    print("Initializing Drag-and-Drop Setup...")

    # Remove existing loaded modules (So it uses the new one)
    from gt.utils.setup_utils import remove_package_loaded_modules
    removed_modules = remove_package_loaded_modules()
    if removed_modules:
        print("Removing package loaded modules...")

    # Prepend sys path with drag and drop location
    print("Prepending system paths with drag-and-drop location...")
    parent_dir = os.path.dirname(__file__)
    print(f'Current location: "{parent_dir}"')
    package_dir = os.path.join(parent_dir, "gt")
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, package_dir)

    # Import and run installer GUI
    print("Initializing installer GUI...")
    import gt.tools.package_setup as package_setup
    package_setup.launcher_entry_point()


# Launch Options
if len(sys.argv) > 1:
    try:
        from gt.utils import system_utils
        system_utils.process_launch_options(sys.argv)
    except Exception as e:
        sys.stdout.write("Failed to process launch option. Issue: " + str(e))
