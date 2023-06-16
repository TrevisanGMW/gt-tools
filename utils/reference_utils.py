import maya.cmds as cmds
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("reference_utils")
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
        in_view_message = '<' + str(random.random()) + '>'
        if len(refs) == 0:
            in_view_message += 'No references in this scene.'
            sys.stdout.write('No references found in this scene. Nothing was imported.')
        else:
            is_plural = 'references were'
            affected = str(refs_imported_counter)
            if refs_imported_counter == 1:
                is_plural = 'reference was'
                affected = '"' + str(refs[0]) + '"'
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
            in_view_message += affected + '</span> ' + is_plural + ' imported.'
            sys.stdout.write(affected + ' ' + is_plural + ' imported.')
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)


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
        in_view_message = '<' + str(random.random()) + '>'
        if len(refs) == 0:
            in_view_message += 'No references in this scene.'
            sys.stdout.write('No references found in this scene. Nothing removed.')
        else:
            is_plural = 'references were'
            affected = str(refs_imported_counter)
            if refs_imported_counter == 1:
                is_plural = 'reference was'
                affected = '"' + str(refs[0]) + '"'
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
            in_view_message += affected + '</span> ' + is_plural + ' removed.'
            sys.stdout.write(affected + ' ' + is_plural + ' removed.')
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
