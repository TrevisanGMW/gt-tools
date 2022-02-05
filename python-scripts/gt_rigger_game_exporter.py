"""
GT Rigger - Game Exporter

v1.0.0 - Initial Release

v1.0.1 - Removed namespaces before exporting
"""
import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import logging
import sys

from gt_rigger_utilities import find_joint, find_transform, get_metadata, selectItems, getChildren
from functools import partial
from collections import namedtuple
from gt_tools.gt_utilities import make_flat_list

SCRIPT_VERSION = '1.0.1'
SCRIPT_NAME = 'GT Rigger - Game Exporter'
logging.basicConfig()
logger = logging.getLogger("exporter")


def _get_object_namespaces(objectName):
    """
    Returns only the namespace of the object
    Args:
        objectName (string): Name of the object to extract the namespace from
    Returns:
        namespaces (string): Extracted namespaces combined into a string (without the name of the object)
                             e.g. Input = "One:Two:pSphere" Output = "One:Two:"
    """
    namespaces_list = objectName.split(':')
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

        :type uuid: basestring
        :rtype: unicode|None
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
                    api_obj = om.MGlobal.getSelectionListByName(absolute_name).getDependNode(0)
                    api_node = om.MFnDependencyNode(api_obj)

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
            api_obj = om.MGlobal.getSelectionListByName(current_name).getDependNode(0)
            api_node = om.MFnDependencyNode(api_obj)
            api_node.setName(original_name)


def _export_fbx(file_path, export_baked_animation=True):
    '''
    Exports auto biped rig data as FBX to be imported into real-time engines.
    This function was specifically made for rigs created with GT biped rigger it assumes that
    all geometry will be found inside "geometry_grp" and the bound skeleton is "root_jnt"

    Args:
        file_path (string) : Path to export location. For example "C:\\character.fbx"
        export_baked_animation (optional, bool) : If active, animation will be baked and geometry will be ignored.
                                                  Only skeleton and animation are exported with this option.
                                                  If deactivated, then skeleton and geometry will be exported
                                                  (no animation baking)

    Returns:
        response (bool) : True if operation was successful and False if it failed.
    '''
    prerolldata = export_preroll()
    configureFBX()
    if export_baked_animation:
        exportBakedAnimation()
        selectItems(prerolldata.root)
    else:
        selectItems(prerolldata.geo, prerolldata.root)

    # Handle Namespaces in References
    namespace = _get_object_namespaces(prerolldata.root)
    if namespace:
        with StripNamespace(namespace) as stripped_nodes:
            cmds.FBXExport('-file', file_path, '-s')
    else:
        cmds.FBXExport('-file', file_path, '-s')

    _set_stored_attributes(prerolldata.attrs)
    return True


def export_preroll():
    """
    does a series of preroll steps to find the parts and set some fbx attrs
    Returns:
        PrerollData namedtuple:
            root: <str> root item
            geo: <str> of geo group
            attrs: <dict> of the attrs that were made visible, so we can set them back after
    """
    prerollData = namedtuple("PrerollData", ['root', 'geo', 'attrs'])

    _root = find_root()
    if _root is None:
        return False

    _geo = find_geo_grp()
    if _geo is None:
        return False

    _skeleton = find_skeleton_grp()
    if _skeleton is None:
        return False

    if not fbxPluginLoaded():
        return False

    attr_state_dict = _make_visible(_geo, _skeleton, _root)

    return prerollData(root=_root, geo=getChildren(_geo), attrs=attr_state_dict)


def fbxPluginLoaded():
    """simple checker for the fbx loaded status"""
    try:
        cmds.FBXExport
    except:
        try:
            cmds.loadPlugin('fbxmaya')
        except:
            sys.stderr.write('ERROR: FBX Export Plug-in was not detected.\n')
            return False
    return True


def exportBakedAnimation():
    fbxPluginLoaded()
    setFBXProperty('FBXExportBakeComplexAnimation', 'true')


def setFBXProperty(name, value):
    _propString = "{name} -v {value};".format(name=name, value=value)
    try:
        mel.eval(_propString)
    except Exception as e:
        logger.warning(f"[setFBXProperty] failed to set property {name} to {value}")
        logger.warning(f"{_propString}")
        logger.warning(str(e))


def setFBXGeometryProperty(name, value):
    _fullname = f"FBXProperty Export|IncludeGrp|Geometry|{name}"
    setFBXProperty(name=_fullname, value=value)


def setFBXExportProperty(name, value):
    _fullname = f"FBXExport{name}"
    setFBXProperty(name=_fullname, value=value)


def configureFBX():
    fbxPluginLoaded()
    # Configure FBX export settings
    # https://docs.unity3d.com/2017.4/Documentation/Manual/HOWTO-ArtAssetBestPracticeGuide.html
    # https://docs.unity3d.com/560/Documentation/Manual/HOWTO-exportFBX.html
    # https://docs.unrealengine.com/en-us/Engine/Content/FBX/BestPractices

    _geo_properties = {
        "expHardEdges": "false",
        "TangentsandBinormals": "false",
        "SmoothMesh": "false",
        "SelectionSet": "false",
        "BlindData": "false",
        "Instances": "false",
        "Triangulate": "false",

        "SmoothingGroups": "true",
        "ContainerObjects": "true",
    }
    for _name, _value in _geo_properties.items():
        setFBXGeometryProperty(_name, _value)

    setFBXGeometryProperty("GeometryNurbsSurfaceAs", '\"Interactive Display Mesh\"')

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
        setFBXExportProperty(_name, _value)


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

            pass
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
        except:
            pass


def _get_skeleton_root_from_metadata():
    """
    looks for the metadata and if it finds it, return the root value
    Returns:
        <str> or None if cant find
    """
    _data = get_metadata(object_name=find_main_ctrl())
    if _data:
        return _data.get("skeleton_root")


def _validate_scene():
    """Returns true if all necessary elements are present in the scene"""
    _root = find_root()
    if _root is None:
        cmds.warning('Script couldn\'t find "root_jnt" joint. Make sure you have a valid scene opened.')
        return False

    _geo = find_geo_grp()
    if _geo is None:
        cmds.warning('Script couldn\'t find geometry group. Make sure you have a valid scene opened.')
        return False

    _skeleton = find_skeleton_grp()
    if _skeleton is None:
        cmds.warning('Script couldn\'t find skeleton group. Make sure you have a valid scene opened.')
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
                                     caption='Exporting ' + caption_description + ' (FBX) file for a WideAwake Rig') or []
        if len(file_name) > 0:
            return file_name[0]


def _export_fbx_model(*args):
    fbx_path = _export_fbx_file_dialog()
    if fbx_path:
        _export_fbx(fbx_path, export_baked_animation=False)


def _export_fbx_animation(*args):
    fbx_path = _export_fbx_file_dialog('Animation')
    if fbx_path:
        _export_fbx(fbx_path, export_baked_animation=True)


def _build_gui_help_fbx_exporter(*args):
    cmds.warning('No help yet. It will be here soon')


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
    cmds.button(label="Help", backgroundColor=title_bgc_color, c=partial(_build_gui_help_fbx_exporter))

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


# Tests
if __name__ == '__main__':
    pass
    build_gui_fbx_exporter()

    # # Export Model
    # temp_file = 'C:\\Users\\guilherme.trevisan\\Desktop\\model.fbx'
    # reponse = _export_fbx(temp_file, export_baked_animation=False)
    # print(str(reponse))

    # # Export Animation
    # temp_file = 'C:\\Users\\guilherme.trevisan\\Desktop\\animation.fbx'
    # reponse = _export_fbx(temp_file, export_baked_animation=True)
    # print(str(reponse))

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
