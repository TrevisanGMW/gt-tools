"""
Outliner Sorter Model
"""

import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SORT_ORDER_ASCENDING = "Sort Ascending"
SORT_ORDER_DESCENDING = "Sort Descending"
SORT_ORDER_OPTIONS = [SORT_ORDER_ASCENDING, SORT_ORDER_DESCENDING]

ATTR_CUSTOM = "Custom Attribute"
ATTR_TRANSLATE_X = "Translate X"
ATTR_TRANSLATE_Y = "Translate Y"
ATTR_TRANSLATE_Z = "Translate Z"
ATTR_ROTATE_X = "Rotate X"
ATTR_ROTATE_Y = "Rotate Y"
ATTR_ROTATE_Z = "Rotate Z"
ATTR_SCALE_X = "Scale X"
ATTR_SCALE_Y = "Scale Y"
ATTR_SCALE_Z = "Scale Z"

ATTRIBUTE_OPTIONS = [
    ATTR_CUSTOM,
    ATTR_TRANSLATE_X,
    ATTR_TRANSLATE_Y,
    ATTR_TRANSLATE_Z,
    ATTR_ROTATE_X,
    ATTR_ROTATE_Y,
    ATTR_ROTATE_Z,
    ATTR_SCALE_X,
    ATTR_SCALE_Y,
    ATTR_SCALE_Z,
]

ATTRIBUTE_NAME_MAP = {
    ATTR_TRANSLATE_X: "translateX",
    ATTR_TRANSLATE_Y: "translateY",
    ATTR_TRANSLATE_Z: "translateZ",
    ATTR_ROTATE_X: "rotateX",
    ATTR_ROTATE_Y: "rotateY",
    ATTR_ROTATE_Z: "rotateZ",
    ATTR_SCALE_X: "scaleX",
    ATTR_SCALE_Y: "scaleY",
    ATTR_SCALE_Z: "scaleZ",
}


class OutlinerSorterModel:
    """Runs outliner sorting operations."""

    def get_selection(self):
        """Gets the current Maya selection.

        Returns:
            list: Selected object paths.
        """
        cmds = get_maya_cmds()
        return cmds.ls(selection=True, long=True) or []

    def run_operation(self, operation, is_ascending=True, attr=None):
        """Runs one outliner sort operation.

        Args:
            operation (str): Operation key.
            is_ascending (bool, optional): Whether sort operations are ascending.
            attr (str, optional): Attribute used by the attribute sort.

        Returns:
            bool: True when an operation was attempted.
        """
        cmds = get_maya_cmds()
        selection = self.get_selection()
        if not selection:
            cmds.warning("Nothing selected. Please select objects you want to sort and try again.")
            return False
        core_outliner = get_core_outliner()
        cmds.undoInfo(openChunk=True, chunkName="Outliner Sorter")
        try:
            if operation == "reorder_up":
                return core_outliner.reorder_up(selection)
            if operation == "reorder_down":
                return core_outliner.reorder_down(selection)
            if operation == "reorder_front":
                return core_outliner.reorder_front(selection)
            if operation == "reorder_back":
                return core_outliner.reorder_back(selection)
            if operation == "sort_name":
                core_outliner.outliner_sort(
                    selection,
                    operation=core_outliner.OutlinerSortOptions.NAME,
                    is_ascending=is_ascending,
                )
                return True
            if operation == "sort_attribute":
                core_outliner.outliner_sort(
                    selection,
                    operation=core_outliner.OutlinerSortOptions.ATTRIBUTE,
                    attr=clean_attribute_name(attr),
                    is_ascending=is_ascending,
                    verbose=True,
                )
                return True
            if operation == "shuffle":
                core_outliner.outliner_sort(selection, operation=core_outliner.OutlinerSortOptions.SHUFFLE)
                return True
        except Exception as exception:
            logger.warning("Outliner sort operation failed: %s", exception)
            raise
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Outliner Sorter")
        return False


def clean_attribute_name(attr):
    """Normalizes an attribute name.

    Args:
        attr (str): Attribute name.

    Returns:
        str: Attribute name without a leading dot.
    """
    attr = str(attr or "").strip()
    if attr.startswith("."):
        attr = attr[1:]
    return attr or "translateY"


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def get_core_outliner():
    """Gets the shared outliner core module lazily.

    Returns:
        module: gt.core.outliner module.
    """
    from gt.core import outliner as core_outliner

    return core_outliner
