"""
Selection Utilities

Import Line:
    import gt.core.selection as core_sel
"""

from gt.core.feedback import FeedbackMessage
from gt.core.naming import get_short_name
import maya.cmds as cmds
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def select_non_unique_objects():
    """Selects all non-unique objects (objects with the same short name)"""
    all_transforms = cmds.ls(type="transform")
    short_names = []
    non_unique_transforms = []
    for obj in all_transforms:  # Get all Short Names
        short_names.append(get_short_name(obj))

    for obj in all_transforms:
        short_name = get_short_name(obj)
        if short_names.count(short_name) > 1:
            non_unique_transforms.append(obj)

    cmds.select(non_unique_transforms, r=True)
    feedback = FeedbackMessage(
        quantity=len(non_unique_transforms),
        singular="non-unique object was.",
        plural="non-unique objects were",
        conclusion="selected.",
        zero_overwrite_message="All objects seem to have unique names in this scene.",
    )
    feedback.print_inview_message(system_write=False)
    if len(non_unique_transforms):
        message = f"\n{str(len(non_unique_transforms))} non-unique objects were found in this scene. "
        message += "Rename them to avoid conflicts."
        sys.stdout.write(message)
    else:
        sys.stdout.write("\nNo repeated names found in this scene.")


def ensure_selection_count(selection_limit=1, require_exact_count=True, verbose=True):
    """
    Validates the current Maya selection count.

    Args:
        selection_limit (int, list, tuple, None):
            - If None: No limit. Only checks if something is selected.
            - If int: The target number (e.g., 1).
            - If list/tuple: A range of acceptable counts (min, max) (e.g., (2, 5)).
        require_exact_count (bool):
            - Only applies if selection_limit is an int.
            - If True: Selection must be EXACTLY `selection_limit`.
            - If False: Selection can be ANY number UP TO `selection_limit`.
            - Defaults to True.
        verbose (bool): Logs warnings to script editor.

    Returns:
        list: The selected objects if valid, otherwise an empty list.
    """
    selection = cmds.ls(selection=True) or []
    selection_count = len(selection)

    # --- 1. Empty Selection Check (Universal) ---
    if not selection:
        if verbose:
            logging.warning("Nothing selected.")
        return []

    # --- 2. Count Validation Logic ---
    # If selection_limit is None, we skip validation and return the selection immediately.
    if selection_limit is None:
        return selection

    count_is_valid = True
    message = ""

    # A) Range Logic (List or Tuple)
    if isinstance(selection_limit, (list, tuple)):
        if len(selection_limit) != 2 or not all(isinstance(i, int) for i in selection_limit):
            if verbose:
                logging.error("selection_limit tuple must contain exactly two integers (min, max).")
            return []

        min_limit, max_limit = sorted(selection_limit)

        if not (min_limit <= selection_count <= max_limit):
            count_is_valid = False
            message = f"Select between {min_limit} and {max_limit} objects. Found {selection_count}."

    # B) Integer Logic (Single Number)
    elif isinstance(selection_limit, int):
        if selection_limit < 1:
            if verbose:
                logging.error("selection_limit must be a positive integer.")
            return []

        if require_exact_count:
            # Enforce EXACT match
            if selection_count != selection_limit:
                count_is_valid = False
                message = f"Select exactly {selection_limit} object(s). Found {selection_count}."

        # Enforce MAXIMUM limit ("Up to...")
        elif selection_count > selection_limit:
            count_is_valid = False
            message = f"Select no more than {selection_limit} object(s). Found {selection_count}."

    # C) Invalid Argument Type
    else:
        if verbose:
            logging.error("selection_limit must be None, an integer, or a tuple/list of two integers.")
        return []

    # --- 3. Final Check ---
    if not count_is_valid:
        if verbose:
            logging.warning(message)
        return []

    return selection


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = ensure_selection_count(selection_limit=None, require_exact_count=True)
    pprint(out)
