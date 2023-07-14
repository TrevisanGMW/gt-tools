"""
Drag and drop this file into the viewport to run the package installer
"""
import sys


def onMayaDroppedPythonFile(*args):
    """
    Runs when file is dropped into the Maya's viewport
    The name of this function is what Maya expects/uses as entry point, so it cannot be changed
    """
    if sys.version_info.major < 3:
        # String formatting for this error should remain compatible to Python 2 to guarantee feedback
        user_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
        error = "Incompatible Python Version. Expected to find 3+. Found version: " + user_version
        error += "For Python 2, use an older version of GT-Tools before (e.g. 2.0.0)\n"
        raise ImportError(error)

    from gt.tools.package_setup import launcher_entry_point
    launcher_entry_point()
