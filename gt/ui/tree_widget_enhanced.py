from PySide2.QtGui import QDrag
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


def reorder_tree_item(item, new_index):
    """
    Reorder the QTreeWidgetItem in its associated QTreeWidget to the specified index.

    Args:
        item (QTreeWidgetItem): The item to be reordered.
        new_index (int): The new index for the item.

    Returns:
        int: The adjusted new index after considering the highest available index.
    """
    tree_widget = item.treeWidget()

    if tree_widget is None:
        raise ValueError("The provided item is not associated with any QTreeWidget.")

    parent_item = item.parent()
    if not parent_item:
        parent_item = tree_widget.invisibleRootItem()

    parent_item.removeChild(item)

    if new_index > parent_item.childCount():
        new_index = parent_item.childCount()

    # Insert the item at the new index
    parent_item.insertChild(new_index, item)

    return new_index


class QTreeEnhanced(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QTreeWidget.InternalMove)  # Drag and Drop enabled
        self.drop_callback = None
        self.one_root_mode = False
        self.last_drop_source_item = None
        self.last_drop_target_item = None

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
        for index in range(self.topLevelItemCount()):
            top_level_items.append(self.topLevelItem(index))
        return top_level_items

    def get_last_drop_source_item(self):
        """
        Gets the last drop (source) object that is extracted when a drop operation happens. - Current item.
        Returns:
            QTreeWidgetItem, any: The last item (source) extracted when a drag operation happens.
        """
        return self.last_drag_source_item

    def get_last_drop_target_item(self):
        """
        Gets the last drop (target) object that is extracted when a drop operation happens. - Current item.
        Returns:
            QTreeWidgetItem, any: The last item (target) extracted when a drag operation happens.
        """
        return self.last_drop_target_item

    def get_all_items(self):
        """
        Get all items in a QTreeWidget, including children.

        Returns:
            list: A list of all items in the QTreeWidget.
        """
        all_items = []

        def traverse_items(item):
            all_items.append(item)
            for index in range(item.childCount()):
                traverse_items(item.child(index))

        top_level_items = self.invisibleRootItem()
        for i in range(top_level_items.childCount()):
            traverse_items(top_level_items.child(i))

        return all_items

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
        target_item = self.itemAt(event.pos())
        self.last_drop_source_item = dragged_item
        self.last_drop_target_item = target_item
        if dragged_item and isinstance(dragged_item, QTreeItemEnhanced):
            dragged_item.run_drop_callback()
            if not dragged_item.is_allowed_parenting():
                target_pos = event.pos()
                target_index = self.indexAt(target_pos).row()
                if target_item == dragged_item.parent():
                    target_index = dragged_item.parent().childCount()
                if not target_index < 0:
                    reorder_tree_item(dragged_item, target_index)

                event.ignore()
                if self.drop_callback:  # Tree callback, not item.
                    self.run_tree_drop_callback()
                return
        if self.one_root_mode:
            self.one_root_mode_drop_event(event=event)
        else:
            super().dropEvent(event)
        if self.drop_callback:  # Tree callback, not item.
            self.run_tree_drop_callback()

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

    def run_tree_drop_callback(self, *args, **kwargs):
        """
        If a drop callback function was defined for this tree,
        it will run when dropping it in an enhanced tree table.
        Args:
            *args: Variable-length positional arguments.
            **kwargs: Variable-length keyword arguments.
        Returns:
            any: The output of the drop callback function.
        """
        if self.drop_callback:
            return self.drop_callback(*args, **kwargs)


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

    def run_drop_callback(self, *args, **kwargs):
        """
        If a drop callback function was defined for this object,
        it will run when dropping it in an enhanced tree table.
        Args:
            *args: Variable-length positional arguments.
            **kwargs: Variable-length keyword arguments.
        Returns:
            any: The output of the drop callback function.
        """
        if self.drop_callback:
            return self.drop_callback(*args, **kwargs)


if __name__ == "__main__":
    from gt.ui import qt_utils
    with qt_utils.QtApplicationContext():
        a_tree_widget = QTreeEnhanced()
        a_tree_widget.set_one_root_mode(state=True)
        a_root_item = QTreeItemEnhanced(["InitialRoot"])
        child_item_one = QTreeItemEnhanced(["ChildOne"])
        child_item_two = QTreeItemEnhanced(["ChildTwo"])
        child_item_three = QTreeItemEnhanced(["ChildThree"])
        grand_child_item_one = QTreeItemEnhanced(["GrandchildOne"])

        a_root_item.set_allow_parenting(False)
        child_item_one.set_allow_parenting(False)
        child_item_two.set_allow_parenting(False)
        child_item_three.set_allow_parenting(False)
        grand_child_item_one.set_allow_parenting(True)

        def callback_test():
            print("Callback")

        a_tree_widget.set_drop_callback(callback_test)

        a_tree_widget.addTopLevelItem(a_root_item)
        a_root_item.addChild(child_item_one)
        a_root_item.addChild(child_item_two)
        a_root_item.addChild(child_item_three)
        child_item_one.addChild(grand_child_item_one)
        #
        # for obj in a_tree_widget.get_all_items():
        #     print(obj.text(0))
        a_tree_widget.show()
