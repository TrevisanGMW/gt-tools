"""
Alembic Utilities
github.com/TrevisanGMW/gt-tools
"""
from namespace_utils import get_namespaces
from transform_utils import Transform, Vector3
from math import degrees
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_alembic_plugin(include_alembic_bullet=False):
    """
    Attempt to load alembic plugins (required for export/import operations)
    Args:
        include_alembic_bullet (optional, bool): If active, the plugin "AbcBullet" is included in the loading operation
    Returns:
        True if all alembic plugins were successfully loaded, False if something is missing
    """
    plugins_to_load = ["AbcExport", "AbcImport"]
    if include_alembic_bullet:
        plugins_to_load.append("AbcBullet")
    plugins_loaded = []

    # Load Plug-in
    for plugin in plugins_to_load:
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            try:
                cmds.loadPlugin(plugin)
                if cmds.pluginInfo(plugin, q=True, loaded=True):
                    plugins_loaded.append(plugin)
            except Exception as e:
                logger.debug(f'Unable to load plugin "{plugin}". Plugin is likely not installed. Issue: {e}')
        else:
            plugins_loaded.append(plugin)

    if len(plugins_loaded) == len(plugins_to_load):
        return True
    else:
        return False


def get_alembic_nodes():
    """
    Get a list of alembic nodes in the scene
    Returns:
        List of alembic nodes in the scene. Empty list if nothing was found.
    """
    return cmds.ls(typ='AlembicNode', long=True) or []


def get_alembic_cycle_as_string(alembic_node):
    """
    Returns alembic cycle as a string (instead of number)
    Args:
        alembic_node (str): Name of the alembic alembic_node (must be an alembic alembic_node)
    Returns:
        str: String describing cycle type. None if failed to retrieve
    """
    cycle_string = ["Hold", "Loop", "Reverse", "Bounce"]
    if not cmds.objExists(f"{alembic_node}.cycleType"):
        logger.debug(f'Unable to get cycle as string. Missing alembic alembic_node attribute: '
                     f'"{alembic_node}.cycle_type".')
        return
    alembic_cycle = cmds.getAttr(f"{alembic_node}.cycleType")
    if alembic_cycle is not None and alembic_cycle <= len(cycle_string):
        return cycle_string[alembic_cycle]
    else:
        logger.debug(f'Unable to get cycle as string. "cmds.getAttr" returned: {alembic_cycle}')
        return


class AlembicNode:
    name: str
    time: int
    offset: int
    start_time: int
    end_time: int
    cycle_type: str
    transform: Transform
    # mesh_cache: str
    # keyframes: Keyframes

    def __init__(self, alembic_node):
        self.name = alembic_node
        self.time = cmds.getAttr(f"{alembic_node}.time")
        self.offset = cmds.getAttr(f"{alembic_node}.offset")
        self.start_time = cmds.getAttr(f"{alembic_node}.startFrame")
        self.end_time = cmds.getAttr(f"{alembic_node}.endFrame")
        self.cycle_type = get_alembic_cycle_as_string(alembic_node)
        # self.transform = self.get_root_transform(alembic_node)
        self.mesh_cache = cmds.getAttr(f"{alembic_node}.abc_File")
        # self.keyframes = getKeyFrames(self.get_root_node(alembic_node))

    @staticmethod
    def get_root_node(alembic_node):
        """
        WIP
        """
        node = alembic_node
        for history in cmds.listHistory(alembic_node):
            if cmds.objectType(history) == 'transform':
                node = history
        return node

    def get_root_transform(self, alembic_node):
        if self.is_camera(alembic_node):
            return Transform(Vector3(0, 0, 0),
                             Vector3(0, 0, 0),
                             Vector3(1, 1, 1))

        root = self.get_root_node(alembic_node)
        try:
            translation = cmds.xform(root, q=True, ws=True, translation=True)
            rotation = cmds.xform(root, q=True, ws=True, rotate=True)
            scale = cmds.xform(root, q=True, ws=True, scale=True)
        except Exception as e:
            logger.debug(f"Unable to retrieve root transforms. Origin returned instead. Issue: {e}")
            return Transform(Vector3(0, 0, 0),
                             Vector3(0, 0, 0),
                             Vector3(1, 1, 1))

        pos = Vector3(translation[0],
                      translation[1],
                      translation[2])
        rot = Vector3(degrees(rotation[0]),
                      degrees(rotation[1]),
                      degrees(rotation[2]))
        scl = Vector3(scale[0],
                      scale[1],
                      scale[2])
        trans = Transform(pos, rot, scl)
        return trans

    @staticmethod
    def is_camera(alembic_node):
        if len(get_namespaces(alembic_node)) > 0:
            for cam in cmds.ls(type='camera'):
                if len(get_namespaces(cam)) > 0:
                    if cam.namespaceList()[0] == alembic_node.namespaceList()[0]:
                        return True

        return "camera" in alembic_node.name()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    import maya.standalone
    maya.standalone.initialize()
    out = None
    pprint(out)

