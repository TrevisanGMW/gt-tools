"""
Reference Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import logging
import sys

# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def references_import():
    """ Imports all references """
    errors = ''
    r_file = ''
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
                errors += str(e) + '(' + r_file + ')\n'
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were imported. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
    else:
        feedback = FeedbackMessage(quantity=len(refs),
                                   singular='reference was',
                                   plural='references were',
                                   conclusion='imported.',
                                   zero_overwrite_message='No references in this scene.')
        feedback.print_inview_message(system_write=False)
        if len(refs):
            sys.stdout.write(f'\n{feedback.get_string_message()}')
        else:
            sys.stdout.write('\nNo references found in this scene. Nothing was imported.')


def references_remove():
    """ Removes all references """
    errors = ''
    r_file = ''
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
                errors += str(e) + '(' + r_file + ')\n'
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were removed. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
    else:
        feedback = FeedbackMessage(quantity=len(refs),
                                   singular='reference was',
                                   plural='references were',
                                   conclusion='removed.',
                                   zero_overwrite_message='No references in this scene.')
        feedback.print_inview_message(system_write=False)
        if len(refs):
            sys.stdout.write(f'\n{feedback.get_string_message()}')
        else:
            sys.stdout.write('\nNo references found in this scene. Nothing was removed.')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
