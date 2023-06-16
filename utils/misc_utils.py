"""
Misc Utilities - Any utilities that might not clearly fit in an existing category.
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import maya.mel as mel
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("misc_utils")
logger.setLevel(logging.INFO)


def open_resource_browser():
    """ Opens Maya's Resource Browser """
    try:
        import maya.app.general.resourceBrowser as resourceBrowser
        resourceBrowser.resourceBrowser().run()
    except Exception as e:
        logger.debug(str(e))


def material_copy():
    """ Copies selected material to clipboard """
    selection = cmds.ls(selection=True)
    try:
        mel.eval('ConvertSelectionToFaces;')
        cmds.polyClipboard(copy=True, shader=True)
        cmds.inViewMessage(amg='Material <hl>copied</hl> to the clipboard.', pos='midCenterTop', fade=True)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't copy material. Make sure you selected an object or component before copying.")
    cmds.select(selection)


def material_paste():
    """ Copies selected material to clipboard """
    try:
        cmds.polyClipboard(paste=True, shader=True)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't paste material. Make sure you copied a material first, "
                     "then selected the target objects or components.")


def delete_nucleus_nodes():
    """ Deletes all elements related to particles """
    errors = ''
    function_name = 'Delete Nucleus Nodes'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # Without Transform
        emitters = cmds.ls(typ='pointEmitter')
        solvers = cmds.ls(typ='nucleus')
        instancers = cmds.ls(typ='instancer')

        no_transforms = emitters + instancers + solvers + instancers

        # With Transform
        nparticle_nodes = cmds.ls(typ='nParticle')
        spring_nodes = cmds.ls(typ='spring')
        particle_nodes = cmds.ls(typ='particle')
        nrigid_nodes = cmds.ls(typ='nRigid')
        ncloth_nodes = cmds.ls(typ='nCloth')
        pfxhair_nodes = cmds.ls(typ='pfxHair')
        hair_nodes = cmds.ls(typ='hairSystem')
        nconstraint_nodes = cmds.ls(typ='dynamicConstraint')

        transforms = nparticle_nodes + spring_nodes + particle_nodes + nrigid_nodes
        transforms += ncloth_nodes + pfxhair_nodes + hair_nodes + nconstraint_nodes

        # Fields/Solvers Types
        # airField
        # dragField
        # newtonField
        # radialField
        # turbulenceField
        # uniformField
        # vortexField
        # volumeAxisField

        deleted_counter = 0
        for obj in transforms:
            try:
                parent = cmds.listRelatives(obj, parent=True) or []
                cmds.delete(parent[0])
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        for obj in no_transforms:
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        in_view_message = '<' + str(random.random()) + '>'
        if deleted_counter > 0:
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter)
            in_view_message += ' </span>'
            is_plural = 'objects were'
            if deleted_counter == 1:
                is_plural = 'object was'
            in_view_message += is_plural + ' deleted.'
        else:
            in_view_message += 'No nucleus nodes found in this scene.'

        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def output_string_to_notepad(string, file_name='tmp'):
    """
    Creates a txt file and writes a list of objects to it (with necessary code used to select it, in Mel and Python)

    Args:
        string (string): A list of string to be exported to a txt file
        file_name (string): Name of the generated file

    """
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir + file_name + '.txt'

    f = open(txt_file, 'w')
    f.write(string)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)
