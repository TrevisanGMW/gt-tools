import logging
import inspect

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SPOOF_RETURN = "maya_spoofing"


def _log_debug(function, *args, **kwargs):
    _output = f"maya-spoofing:\n  [{function}]\n  args: {args}\n  kwargs: {kwargs}"
    logger.debug(_output)


class MayaCmdsSpoof(object):
    """ Spoof maya.cmds """
    def ls(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def objExists(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def getAttr(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def setAttr(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def polySphere(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def sphere(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def warning(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def select(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def listRelatives(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def loadPlugin(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def unloadPlugin(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def playbackOptions(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def fileDialog2(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def file(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def FBXExport(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def namespace(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def namespaceInfo(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def currentUnit(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def currentTime(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    # UI ---------------------------------
    def button(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def deleteUI(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def columnLayout(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def text(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def rowColumnLayout(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def window(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def showWindow(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def separator(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def menu(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def menuItem(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def confirmDialog(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN


class MayaMelSpoof(object):
    """ Spoof maya.mel """
    def eval(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN


class MayaStandaloneSpoof(object):
    """ Spoof maya.standalone """
    def initialize(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN


class MiscOpenMaya(object):
    """ Functions found in OpenMaya and OpenMaya.api """
    def getSelectionListByName(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN

    def currentFile(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN


class OpenMayaSpoof(object):
    """ Spoof OpenMaya """
    MFileIO = MiscOpenMaya()


class OpenMayaApiSpoof(object):
    """ Spoof OpenMayaApi """
    MGlobal = MiscOpenMaya()

    def MFnDependencyNode(self, *args, **kwargs):
        _log_debug(inspect.stack()[0][3], *args, **kwargs)
        return SPOOF_RETURN


if __name__ == '__main__':
    out = None
    maya_spoof = MayaCmdsSpoof()
    out = maya_spoof.ls('sample_arg', sample_kwarg="value_one", second_kward="value_two")
    print(out)
