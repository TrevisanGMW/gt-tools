"""
GT Rigger - Game Exporter
github.com/TrevisanGMW/gt-tools - 2022-02-04

v1.0.0 - 2022-02-04
Initial Release

v1.0.1
Removed namespaces before exporting

v1.0.2 - 2022-08-04
Added link to help button sending to documentation

v1.0.3 - 2022-08-08
Changed "SmoothMesh" to true
"""
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel
import logging
import sys

from gt_rigger_utilities import find_joint, find_transform, get_metadata, select_items, get_children
from gt_tools.gt_utilities import make_flat_list
from collections import namedtuple
from functools import partial

SCRIPT_VERSION = '1.0.3'
SCRIPT_NAME = 'GT Rigger - Game Exporter'

logging.basicConfig()
logger = logging.getLogger("gt_rigger_game_exporter")
logger.setLevel(logging.INFO)


def _get_object_namespaces(object_name):
    """
    Returns only the namespace of the object
    Args:
        object_name (string): Name of the object to extract the namespace from
    Returns:
        namespaces (string): Extracted namespaces combined into a string (without the name of the object)
                             e.g. Input = "One:Two:pSphere" Output = "One:Two:"
    """
    namespaces_list = object_name.split(':')
    object_namespace = ''
    for namespace in namespaces_list:
        if namespace != namespaces_list[-1]:
            object_namespace += namespace + ':'

    return object_namespace


class StripNamespace(object):
    """
    Context manager use to temporarily strip a namespace from all dependency nodes within a namespace.

    This allows nodes to masquerade as if they never had namespace, including those considered read-only
    due to file referencing.

    Usage:

        with StripNamespace('someNamespace') as stripped_nodes:
            print cmds.ls(stripped_nodes)
    """

    @classmethod
    def as_name(cls, uuid):
        """
        Convenience method to extract the name from uuid

        type uuid: basestring
        rtype: unicode|None
        """
        names = cmds.ls(uuid)
        return names[0] if names else None

    def __init__(self, namespace):
        if cmds.namespace(exists=namespace):
            self.original_names = {}  # (UUID, name_within_namespace)
            self.namespace = cmds.namespaceInfo(namespace, fn=True)
        else:
            raise ValueError('Could not locate supplied namespace, "{0}"'.format(namespace))

    def __enter__(self):
        for absolute_name in cmds.namespaceInfo(self.namespace, listOnlyDependencyNodes=True, fullName=True):

            # Ensure node was *not* auto-renamed (IE: shape nodes)
            if cmds.objExists(absolute_name):

                # get an api handle to the node
                try:
                    api_obj = OpenMaya.MGlobal.getSelectionListByName(absolute_name).getDependNode(0)
                    api_node = OpenMaya.MFnDependencyNode(api_obj)

                    # Remember the original name to return upon exit
                    uuid = api_node.uuid().asString()
                    self.original_names[uuid] = api_node.name()

                    # Strip namespace by renaming via api, bypassing read-only restrictions
                    without_namespace = api_node.name().replace(self.namespace, '')
                    api_node.setName(without_namespace)

                except RuntimeError:
                    pass  # Ignores Unrecognized objects (kFailure) Internal Errors

        return [self.as_name(uuid) for uuid in self.original_names]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for uuid, original_name in self.original_names.items():
            current_name = self.as_name(uuid)
            api_obj = OpenMaya.MGlobal.getSelectionListByName(current_name).getDependNode(0)
            api_node = OpenMaya.MFnDependencyNode(api_obj)
            api_node.setName(original_name)


def _export_fbx(file_path, baked_animation_export=True):
    """
    Exports auto biped rig data as FBX to be imported into real-time engines.
    This function was specifically made for rigs created with GT biped rigger it assumes that
    all geometry will be found inside "geometry_grp" and the bound skeleton is "root_jnt"

    Args:
        file_path (string) : Path to export location. For example "C:\\character.fbx"
        baked_animation_export (optional, bool) : If active, animation will be baked and geometry will be ignored.
                                                  Only skeleton and animation are exported with this option.
                                                  If deactivated, then skeleton and geometry will be exported
                                                  (no animation baking)

    Returns:
        response (bool) : True if operation was successful and False if it failed.
    """
    pre_roll_data = export_pre_roll()
    configure_fbx()
    if baked_animation_export:
        export_baked_animation()
        select_items(pre_roll_data.root)
    else:
        select_items(pre_roll_data.geo, pre_roll_data.root)

    # Handle Namespaces in References
    namespace = _get_object_namespaces(pre_roll_data.root)
    if namespace:
        with StripNamespace(namespace) as stripped_nodes:
            cmds.FBXExport('-file', file_path, '-s')
            logger.debug(stripped_nodes)
    else:
        cmds.FBXExport('-file', file_path, '-s')

    _set_stored_attributes(pre_roll_data.attrs)
    return True


def export_pre_roll():
    """
    does a series of pre-roll steps to find the parts and set some fbx attrs
    Returns:
        Pre-rollData namedtuple:
            root: <str> root item
            geo: <str> of geo group
            attrs: <dict> of the attrs that were made visible, so we can set them back after
    """
    pre_roll_data = namedtuple("PrerollData", ['root', 'geo', 'attrs'])

    _root = find_root()
    if _root is None:
        return False

    _geo = find_geo_grp()
    if _geo is None:
        return False

    _skeleton = find_skeleton_grp()
    if _skeleton is None:
        return False

    if not fbx_plugin_loaded():
        return False

    attr_state_dict = _make_visible(_geo, _skeleton, _root)

    return pre_roll_data(root=_root, geo=get_children(_geo), attrs=attr_state_dict)


def fbx_plugin_loaded():
    """simple checker for the fbx loaded status"""
    try:
        cmds.FBXExport
    except Exception as e:
        logger.debug(str(e))
        try:
            cmds.loadPlugin('fbxmaya')
        except Exception as e:
            logger.debug(str(e))
            sys.stderr.write('ERROR: FBX Export Plug-in was not detected.\n')
            return False
    return True


def export_baked_animation():
    fbx_plugin_loaded()
    set_fbx_property('FBXExportBakeComplexAnimation', 'true')


def set_fbx_property(name, value):
    _propString = "{name} -v {value};".format(name=name, value=value)
    try:
        mel.eval(_propString)
    except Exception as e:
        logger.warning("[setFBXProperty] failed to set property " + name + '" to "' + value + '"')
        logger.warning(str(_propString))
        logger.warning(str(e))


def set_fbx_geometry_property(name, value):
    _fullname = "FBXProperty Export|IncludeGrp|Geometry|" + name
    set_fbx_property(name=_fullname, value=value)


def set_fbx_export_property(name, value):
    _fullname = "FBXExport" + name
    set_fbx_property(name=_fullname, value=value)


def configure_fbx():
    fbx_plugin_loaded()
    # Configure FBX export settings
    # https://docs.unity3d.com/2017.4/Documentation/Manual/HOWTO-ArtAssetBestPracticeGuide.html
    # https://docs.unity3d.com/560/Documentation/Manual/HOWTO-exportFBX.html
    # https://docs.unrealengine.com/en-us/Engine/Content/FBX/BestPractices

    _geo_properties = {
        "expHardEdges": "false",
        "TangentsandBinormals": "false",
        "SmoothMesh": "true",
        "SelectionSet": "false",
        "BlindData": "false",
        "Instances": "false",
        "Triangulate": "false",

        "SmoothingGroups": "true",
        "ContainerObjects": "true",
    }
    for _name, _value in _geo_properties.items():
        set_fbx_geometry_property(_name, _value)

    set_fbx_geometry_property("GeometryNurbsSurfaceAs", '\"Interactive Display Mesh\"')

    _export_properties = {
        "ReferencedAssetsContent": "false",
        "Constraints": "false",
        "Cameras": "false",
        "Lights": "false",
        "EmbeddedTextures": "false",
        "InputConnections": "false",
        "SmoothingGroups": "false",
        "SmoothMesh": "false",
        "BakeComplexAnimation": "false",

        "UseSceneName": "true",
    }

    # Ignore unnecessary elements
    for _name, _value in _export_properties.items():
        set_fbx_export_property(_name, _value)


def find_root():
    _root_joint = _get_skeleton_root_from_metadata()
    if not _root_joint:
        _root_joint = 'root_jnt'
    return find_joint(_root_joint)


find_geo_grp = partial(find_transform, name='geometry_grp')
find_skeleton_grp = partial(find_transform, name='skeleton_grp')
find_main_ctrl = partial(find_transform, name='main_ctrl')


def _make_visible(*args):
    """
    Changes the overrideEnabled and visibility attributes to force the object into a visible state.
    Use the function "_set_stored_attributes()" to set values back after exporting
            Returns:
                attr_state_dict (dictionary) : The data before it was changed, for example: "{ 'skeleton_grp.v': True }"
    """
    obj_list = make_flat_list(args)
    attr_state_dict = {}
    for obj in obj_list:
        try:
            attr_state_dict[obj + '.overrideEnabled'] = cmds.getAttr(obj + '.overrideEnabled')
            attr_state_dict[obj + '.v'] = cmds.getAttr(obj + '.v')
            cmds.setAttr(obj + '.overrideEnabled', 0)
            cmds.setAttr(obj + '.v', 1)
        except Exception as e:
            logger.debug(str(e))
    return attr_state_dict


def _set_stored_attributes(attr_state_dict):
    """
    Sets the provided attributes (key) back to their stored values (value)
    According to the follow pattern: { 'object_name.attribute' : data }
    For example: "{ 'skeleton_grp.v': True }"
    """
    for key, value in attr_state_dict.items():
        try:
            cmds.setAttr(key, value)
        except Exception as e:
            logger.debug(str(e))


def _get_skeleton_root_from_metadata():
    """
    looks for the metadata and if it finds it, return the root value
    Returns:
        <str> or None if it can't find the metadata
    """
    _data = get_metadata(object_name=find_main_ctrl())
    if _data:
        return _data.get("skeleton_root")


def _validate_scene():
    """Returns true if all necessary elements are present in the scene"""
    _root = find_root()
    if _root is None:
        cmds.warning("Script couldn't find \"root_jnt\" joint. Make sure you have a valid scene opened.")
        return False

    _geo = find_geo_grp()
    if _geo is None:
        cmds.warning("Script couldn't find geometry group. Make sure you have a valid scene opened.")
        return False

    _skeleton = find_skeleton_grp()
    if _skeleton is None:
        cmds.warning("Script couldn't find skeleton group. Make sure you have a valid scene opened.")
        return False
    return True


def _export_fbx_file_dialog(caption_description='Model'):
    """
    Opens a dialog for exporting fbx files

    Returns:
        string_path (string) : The path to a valid file
    """
    if _validate_scene():
        file_name = cmds.fileDialog2(fileFilter='FBX File (*.fbx)',
                                     dialogStyle=2,
                                     okCaption='Export',
                                     caption='Exporting ' + caption_description +
                                             ' (FBX) file for a WideAwake Rig') or []
        if len(file_name) > 0:
            return file_name[0]


def _export_fbx_model(*args):
    logger.debug(str(*args))
    fbx_path = _export_fbx_file_dialog()
    if fbx_path:
        _export_fbx(fbx_path, baked_animation_export=False)


def _export_fbx_animation(*args):
    logger.debug(str(*args))
    fbx_path = _export_fbx_file_dialog('Animation')
    if fbx_path:
        _export_fbx(fbx_path, baked_animation_export=True)


def build_gui_fbx_exporter():
    """Creates simple GUI for FBX Exporter"""
    window_name = "build_gui_fbx_exporter"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    build_gui_world_space_baker = cmds.window(window_name,
                                              title=SCRIPT_NAME + '  (v' + SCRIPT_VERSION + ')',
                                              titleBar=True,
                                              minimizeButton=False,
                                              maximizeButton=False,
                                              sizeable=True)

    cmds.window(window_name, e=True, sizeable=True, widthHeight=[1, 1])
    content_main = cmds.columnLayout(adjustableColumn=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(numberOfColumns=1,
                         columnWidth=[(1, 270)],
                         columnSpacing=[(1, 10)],
                         parent=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(numberOfColumns=3,
                         columnWidth=[(1, 10), (2, 200), (3, 50)],
                         columnSpacing=[(1, 10), (2, 0), (3, 0)],
                         parent=content_main)  # Title Column
    cmds.text(" ", backgroundColor=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(SCRIPT_NAME, backgroundColor=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(label="Help", backgroundColor=title_bgc_color, c=partial(_open_gt_tools_documentation))

    # Buttons
    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 240)], columnSpacing=[(1, 20)], parent=content_main)
    cmds.separator(height=15, style='none')  # Empty Space
    cmds.button(label="Export Model FBX File", backgroundColor=(.3, .3, .3), c=partial(_export_fbx_model))
    cmds.separator(height=15, style='none')  # Empty Space
    cmds.button(label="Export Animation FBX File", backgroundColor=(.3, .3, .3), c=partial(_export_fbx_animation))
    cmds.separator(height=15, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(build_gui_world_space_baker)
    cmds.window(window_name, e=True, sizeable=False)


def _open_gt_tools_documentation(*args):
    """ Opens a web browser with the auto rigger docs  """
    logger.debug(str(args))
    cmds.showHelp('https://github.com/TrevisanGMW/gt-tools/tree/release/docs', absolute=True)


# Tests
if __name__ == '__main__':
    pass
    build_gui_fbx_exporter()

    # # Export Model
    # temp_file = 'C:\\Users\\guilherme.trevisan\\Desktop\\model.fbx'
    # response = _export_fbx(temp_file, export_baked_animation=False)
    # print(str(response))

    # # Export Animation
    # temp_file = 'C:\\Users\\guilherme.trevisan\\Desktop\\animation.fbx'
    # response = _export_fbx(temp_file, export_baked_animation=True)
    # print(str(response))

    # output = _export_fbx_file_dialog()
    # print(output)

    # import unittest
    # class TestFBX(unittest.TestCase):
    #     def test_find_root(self):
    #         result = find_root()
    #         expected = "root_jnt"
    #         # expected = "Hips"
    #         self.assertEqual(result, expected)

    #     def test_find_main_ctrl(self):
    #         result = find_main_ctrl()
    #         expected = "main_ctrl"
    #         self.assertEqual(result, expected)
    # unittest.main()
