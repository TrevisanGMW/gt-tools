"""
Reference Utilities

Import Line:
    import gt.core.reference as core_ref
"""

from gt.core.feedback import FeedbackMessage
import maya.cmds as cmds
import logging
import sys

# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def references_import():
    """Imports all references"""
    errors = ""
    r_file = ""
    refs = []
    refs_imported_counter = 0
    try:
        refs = cmds.ls(rf=True) or []
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, importReference=True)
                refs_imported_counter += 1
            except Exception as e:
                errors += str(e) + "(" + r_file + ")\n"
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != "":
        cmds.warning("Not all references were imported. Open the script editor for more information.")
        print(("#" * 50) + "\n")
        print(errors)
        print("#" * 50)
    else:
        feedback = FeedbackMessage(
            quantity=len(refs),
            singular="reference was",
            plural="references were",
            conclusion="imported.",
            zero_overwrite_message="No references in this scene.",
        )
        feedback.print_inview_message(system_write=False)
        if len(refs):
            sys.stdout.write(f"\n{feedback.get_string_message()}")
        else:
            sys.stdout.write("\nNo references found in this scene. Nothing was imported.")


def references_remove():
    """Removes all references"""
    errors = ""
    r_file = ""
    refs = []
    refs_imported_counter = 0
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, removeReference=True)
                refs_imported_counter += 1
            except Exception as e:
                errors += str(e) + "(" + r_file + ")\n"
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != "":
        cmds.warning("Not all references were removed. Open the script editor for more information.")
        print(("#" * 50) + "\n")
        print(errors)
        print("#" * 50)
    else:
        feedback = FeedbackMessage(
            quantity=len(refs),
            singular="reference was",
            plural="references were",
            conclusion="removed.",
            zero_overwrite_message="No references in this scene.",
        )
        feedback.print_inview_message(system_write=False)
        if len(refs):
            sys.stdout.write(f"\n{feedback.get_string_message()}")
        else:
            sys.stdout.write("\nNo references found in this scene. Nothing was removed.")


def get_referenced_files_from_ma(filename, wild_cards=None):
    """
    Gets the referenced files listed inside a supplied MA file.

    Args:
        filename (str): path of the supplied MA file.
        wild_cards (list): list of words to filter the search.

    Returns:
        referenced_files (list)
    """
    reference_list = []

    if not filename.lower().endswith(".ma"):
        logger.debug("Supplied file is not a MayaAscii.")
        return reference_list
    if not os.path.exists(filename):
        logger.debug("Supplied path does not exist.")
        return reference_list
    if not isinstance(wild_cards, list):
        wild_cards = []

    with open(filename) as fp:
        line_string = fp.readline()
        line_count = 1
        has_reference = False

        while line_string:
            if line_string.startswith("file -rdi"):
                has_reference = True
                asset_namespace = line_string.split(" ")[4].replace('"', "")

                if len(wild_cards) > 0:
                    has_wcards = True
                    for wcard in wild_cards:
                        if wcard not in asset_namespace:
                            has_wcards = False
                            break
                    if has_wcards:
                        reference_list.append(asset_namespace)
                else:
                    reference_list.append(asset_namespace)

            if not has_reference and line_count == 20:
                break
            if has_reference and line_count == 60:
                break

            line_string = fp.readline()
            line_count += 1

    return reference_list


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = None
    pprint(out)
