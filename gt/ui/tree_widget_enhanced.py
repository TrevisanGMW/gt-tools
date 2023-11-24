from PySide2.QtWidgets import QTreeWidget, QTreeWidgetItem


def remove_tree_item_from_tree(item_to_remove):
    """
    Removes a QTreeWidgetItem from its QTreeWidget.

    Args:
        item_to_remove (QTreeWidgetItem): The item to be removed.
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


class QTreeEnhanced(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QTreeWidget.InternalMove) # Drag and Drop enabled
        self.drop_callback = None
        self.one_root_mode = False

    def set_one_root_mode(self, state):
        """
        Determines if the one root mode is active.
        If True, it will enforce the rule of only having one item at the root.
        Args:
            state (bool): State of the mode. If True, it's active, if False, inactive.
        """
        self.one_root_mode = state

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
        dragged_item = self.currentItem()
        if dragged_item and isinstance(dragged_item, QTreeItemEnhanced):
            dragged_item.run_drop_callback()
            if not dragged_item.is_allowed_parenting():
                parent = dragged_item.parent()
                target_item = self.itemAt(event.pos())
                # print(f'parent: {str(parent)}')
                # print(f'target_item: {str(target_item)}')
                target_index = self.indexOfTopLevelItem(target_item)
                print(f'target_index: {str(target_index)}')
                if parent != target_item:
                    event.ignore()
                    return
        if self.one_root_mode:
            self.one_root_mode_drop_event(event=event)
        else:
            super().dropEvent(event)
        if self.drop_callback:  # Tree callback, not item.
            self.drop_callback()

    def one_root_mode_drop_event(self, event):
        """
        Event called when running one root mode. It
        """
        dragged_item = self.currentItem()
        root_item = None
        top_level_items = self.get_top_level_items()
        if top_level_items:
            root_item = top_level_items[0]
        # Get the drop target item
        super().dropEvent(event)
        # Re-parent if not inside root
        parent = dragged_item.parent()
        if parent is None and root_item:
            remove_tree_item_from_tree(dragged_item)
            root_item.addChild(dragged_item)


class QTreeItemEnhanced(QTreeWidgetItem):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.drop_callback = None
        self.allow_parenting = True

    def set_allow_parenting(self, state):
        """
        Sets the skip drop value.
        If True and this item is part of an enhanced tree object, it will skip the drop event.
        (Callback is still invoked)
        Args:
            state (bool): True if the original drop event shouldn't happen, False if you want it to skip.
        """
        self.allow_parenting = state

    def is_allowed_parenting(self):
        """
        Gets the allow parenting value. If True, it means that this item is allowed to be re-parented.
        If False, it's not allowed to be re-parented, even if dragged and dropped.
        """
        return self.allow_parenting

    def set_drop_callback(self, callback):
        """
        Sets a drop callback function.
        Args:
            callback (callable): A function that will be called when dropping the item.
        """
        if not callable(callback):
            return
        self.drop_callback = callback

    def run_drop_callback(self):
        """
        If a drop callback function was defined for this object,
        it will run when dropping it in an enhanced tree table.
        Returns:
            any: The output of the drop callback function.
        """
        if self.drop_callback:
            return self.drop_callback()


if __name__ == "__main__":
    from gt.ui import qt_utils
    with qt_utils.QtApplicationContext():
        a_tree_widget = QTreeEnhanced()
        a_tree_widget.set_one_root_mode(state=True)
        a_root_item = QTreeItemEnhanced(["InitialRoot"])
        child_item_one = QTreeWidgetItem(["ChildOne"])
        child_item_two = QTreeItemEnhanced(["ChildTwo"])
        child_item_two.set_allow_parenting(True)
        def callback_test():
            print("Callback")
        child_item_two.set_drop_callback(callback_test)

        a_tree_widget.addTopLevelItem(a_root_item)
        a_root_item.addChild(child_item_one)
        a_root_item.addChild(child_item_two)

        a_tree_widget.show()
