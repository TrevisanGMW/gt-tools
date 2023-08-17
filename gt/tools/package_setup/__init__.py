"""
 Package Setup - Entry point tool used to install, uninstall or run tools directly from location.
 github.com/TrevisanGMW/gt-tools - 2023-06-01
"""
from gt.tools.package_setup import setup_controller
from gt.tools.package_setup import setup_model
from gt.tools.package_setup import setup_view
from gt.ui import qt_utils

# Tool Version
__version_tuple__ = (1, 0, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launcher_entry_point():
    """ Determines if it should open the installer GUI as a child of Maya or by itself """
    with qt_utils.QtApplicationContext() as context:
        _view = setup_view.PackageSetupWindow(parent=context.get_parent())
        _model = setup_model.PackageSetupModel()
        _controller = setup_controller.PackageSetupController(model=_model, view=_view)


def open_about_window():
    """ Opens about window for the package """
    from gt.tools.package_setup import about_window
    about_window.build_gui_about_gt_tools()


if __name__ == "__main__":
    launcher_entry_point()
