"""
QT Controller for setup
"""

from PySide2 import QtCore


class PackageSetupController(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        """
        The controller that facilitates the communication between the asset
        builder reticulator view and the current reticulator instance
        """
        super().__init__(*args, **kwargs)

    def print_args(self, *args):
        """
        Prints arguments

        """
        data = self.model.get_data()
        print("Printing Data:")
        for arg in data:
            print(arg)

    def add_to_data(self, to_add):
        self.model.add_item(to_add)
        print(f"Added to data: {to_add}")
