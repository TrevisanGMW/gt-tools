from PySide2.QtWidgets import QWidget, QApplication
import sys
import os

# Paths to Append
source_dir = os.path.dirname(__file__)
tools_root_dir = os.path.dirname(source_dir)
for to_append in [source_dir, tools_root_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)

from utils import session_utils
import setup_view


def get_maya_main_window():
    """
    Finds the instance of maya's main window
    Returns:
        QWidget: The main maya widget
    """
    from shiboken2 import wrapInstance
    from maya import OpenMayaUI as OpenMayaUI
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_window = wrapInstance(int(ptr), QWidget)
    return maya_window


def build_installer_gui(standalone=True):
    if standalone:
        app = QApplication(sys.argv)
        window = setup_view.PackageSetupWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        maya_window = get_maya_main_window()
        window = setup_view.PackageSetupWindow(parent=maya_window)
        window.show()


def launcher_entry_point():
    if session_utils.is_script_in_py_maya():
        build_installer_gui(standalone=True)
    else:
        build_installer_gui(standalone=False)


def open_about_window():
    import about_window
    about_window.build_gui_about_gt_tools()


if __name__ == "__main__":
    build_installer_gui()
