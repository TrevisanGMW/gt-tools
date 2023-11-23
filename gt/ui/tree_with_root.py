from PySide2.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication


class QTreeWithRoot(QTreeWidget):
    def __init__(self):
        super().__init__()
        # Set the drag drop mode to InternalMove (Drag and Drop enabled)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.drop_callback = None

    def get_top_level_items(self):
        """
        Get a list of top-level QTreeWidgetItems from a QTreeWidget.

        Returns:
            list: List of top-level QTreeWidgetItems.
        """
        top_level_items = []
        for i in range(self.topLevelItemCount()):
            top_level_items.append(self.topLevelItem(i))
        return top_level_items

    def set_drop_callback(self, callback):
        """
        Sets a drop callback function.
        Args:
            callback (callable): A function that will be called when dropping an object.
        """
        if not callable(callback):
            return
        self.drop_callback = callback

    def dropEvent(self, event):
        """
        Override the dropEvent method to handle dropping items.
        Move new extra top level items into initial root item.

        Args:
            event (QDropEvent): The drop event.
        """
        root_item = None
        top_level_items = self.get_top_level_items()
        if top_level_items:
            root_item = top_level_items[0]
        # Get the drop target item
        dragged_item = self.currentItem()
        super().dropEvent(event)
        # Re-parent if not inside root
        parent = dragged_item.parent()
        if parent is None and root_item:
            remove_tree_item_from_tree(dragged_item)
            root_item.addChild(dragged_item)
        if self.drop_callback:
            self.drop_callback()



def remove_tree_item_from_tree(item_to_remove):
    """
    Removes a QTreeWidgetItem from its QTreeWidget.

    Parameters:
        item_to_remove (QTreeWidgetItem): The item to be removed.

    Returns:
    None
    """
    # Check if the item has a parent
    parent_item = item_to_remove.parent()
    if parent_item:
        # Remove the item from its parent
        parent_item.removeChild(item_to_remove)
    else:
        # If the item is in the root, remove it from the QTreeWidget
        index = item_to_remove.treeWidget().indexOfTopLevelItem(item_to_remove)
        item_to_remove.treeWidget().takeTopLevelItem(index)



if __name__ == "__main__":
    from gt.ui import qt_utils
    with qt_utils.QtApplicationContext():
        a_tree_widget = QTreeWithRoot()
        a_root_item = QTreeWidgetItem(["InitialRoot"])
        child_item_one = QTreeWidgetItem(["ChildOne"])
        child_item_two = QTreeWidgetItem(["ChildTwo"])

        a_tree_widget.addTopLevelItem(a_root_item)
        a_root_item.addChild(child_item_one)
        a_root_item.addChild(child_item_two)

        a_tree_widget.show()
