"""
Sample Tool Model. (Logic, Database Access, Read/Write, Update Data)
The Model represents the data and business logic of the application. It encapsulates the data, defines how it is
structured, and provides methods to manipulate and access that data. The Model component is essentially responsible
for the application's data layer. It does not know anything about the user interface or how the data is presented to
the user. Instead, it focuses on managing data integrity, validation, and business rules.

In the example below, it's adding, removing and getting items from a list.
But it could be writing/reading a file or processing the data from a scene.
"""


class SampleToolModel:
    def __init__(self):
        """
        Initialize the SampleToolModel object.
        """
        self.items = []

    def add_item(self, item):
        """
        Add an item to the list.
        Parameters:
            item: The item to be added.
        """
        self.items.append(item)

    def remove_item(self, index):
        """
        Remove an item from the list based on its index.

        Parameters:
            index: The index of the item to be removed.

        """
        if 0 <= index < len(self.items):
            del self.items[index]

    def get_items(self):
        """
        Get the list of items.
        Returns:
            list: A list containing all the items in the SampleToolModel.
        """
        return self.items


if __name__ == "__main__":
    # The model should be able to work without the controller or view
    model = SampleToolModel()
    model.add_item("Test Item 1")
    model.add_item("Test Item 2")
    items = model.get_items()
    print(items)
