"""
Sample Tool Model. (Logic, Database Access, Read/Write, Update Data)
The Model represents the data and business logic of the application. It encapsulates the data, defines how it is
structured, and provides methods to manipulate and access that data. The Model component is essentially responsible
for the application's data layer. It does not know anything about the user interface or how the data is presented to
the user. Instead, it focuses on managing data integrity, validation, and data rules.
"""
import gt.utils.system_utils as system_utils
import gt.utils.data_utils as data_utils
import os.path


class SampleToolModel:
    def __init__(self):
        """
        Initializes the class instance.
        This constructor sets the initial state of the object, creating an instance
        of the class with an empty `_data` attribute.
        """
        self._data = ""

    def get_data(self):
        """
        Retrieves the stored data. (Data Getter)
        This method returns the currently stored data within the instance.
        Returns:
            str: The stored data.
        """
        return self._data

    def set_data(self, data):
        """
        Sets the data. (Data Setter)
        This method updates the `_data` attribute of the instance with the provided data.
        Args:
            self (object): The instance of the class.
            data (str): The data to be stored.
        """
        self._data = data

    def write_data_to_desktop(self):
        """
        Writes the data to a file named 'sample_tool_data.txt' on the desktop.
        This method retrieves the desktop path using system_utils.get_desktop_path(),
        and then constructs the file path by joining the desktop path with the default
        filename 'sample_tool_data.txt'. It writes the stored data to the file using
        data_utils.write_data().
        Note:
            - "data_utils" and "system_utils" imported from "gt.utils"
            - The data will be written to a file named 'sample_tool_data.txt' on the desktop.
        """
        desktop_path = system_utils.get_desktop_path()
        file_path = os.path.join(desktop_path, "sample_tool_data.txt")
        data_utils.write_data(path=file_path, data=self._data)


if __name__ == "__main__":
    # Application - To launch without Maya
    model = SampleToolModel()
    model.set_data("test_data")
    print(model.get_data())
    model.write_data_to_desktop()
