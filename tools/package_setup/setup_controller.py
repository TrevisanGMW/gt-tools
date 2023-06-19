"""
QT Controller for setup
"""

from PySide2 import QtCore
from utils import setup_utils


class PackageSetupController(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        """
        Initializes package setup controller object
        Parameters:
            args (any): Variable length argument list.
            kwargs (any): Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

    def print_args(self, *args):
        """
        Prints arguments (args)
        Parameters:
            args (any): Variable length argument list.
        """
        data = self.model.get_data()
        print("Printing Data:")
        for arg in data:
            print(arg)

    def install_package(self):
        setup_utils.install_package()

    def uninstall_package(self):
        setup_utils.uninstall_package()
