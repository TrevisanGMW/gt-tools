"""
 Main Maya Menu - GT Tools Menu - Creates a menu to call scripts from the GT Tools Package
 github.com/TrevisanGMW/gt-tools - 2020-03-03
"""
from gt.utils.version_utils import get_package_version
import gt.ui.resource_library as resource_library
from gt.ui.maya_menu import MayaMenu
from functools import partial
import logging
import sys
import os

# Setup  Logger
logging.basicConfig()
logger = logging.getLogger(__name__)

MENU_NAME = "GT Tools"


def _rebuild_menu(*args):
    """
    Rebuilds the menu.
    Args:
       *args: Variable number of arguments. Not used, only logged as debug.
    """
    logger.debug(f'Args: {str(args)}')
    sys.stdout.write("Re-building GT Tools Menu...\n")
    load_menu()


def _open_named_tool(import_path, entry_point_function=None, *args):
    """
    Opens a named tool using its import path and entry point function (when provided)
    Parameters:
        import_path (str): Tool package name (same as its folder) e.g. "renamer"
        entry_point_function (str, optional): Name of the entry point function, if not provided it's assumed to be
                                              the default name "launch_tool"
    """
    logger.debug(f'Package Path: {str(str(import_path))}')
    logger.debug(f'Entry Function: {str(entry_point_function)}')
    logger.debug(f'Args: {str(args)}')
    utils_dir = os.path.dirname(__file__)
    package_dir = os.path.dirname(utils_dir)
    if package_dir not in sys.path:
        sys.path.append(package_dir)  # Ensure package is available
    from gt.utils import system_utils
    if entry_point_function:
        system_utils.initialize_tool(import_path=import_path,
                                     entry_point_function=entry_point_function)
    else:
        system_utils.initialize_tool(import_path=import_path)


def _run_utility(import_path, util_name, *args):
    """
    Runs a named utility
    Parameters:
        import_path (str): Util script name (same as its file name) e.g. "curve_utils"
        util_name (str): Name of the utility (name of the function)
    """
    logger.debug(f'Args: {str(args)}')
    utils_dir = os.path.dirname(__file__)
    package_dir = os.path.dirname(utils_dir)
    if package_dir not in sys.path:
        sys.path.append(package_dir)  # Ensure package is available
    from gt.utils import system_utils
    system_utils.initialize_utility(import_path, util_name)


def unload_menu(*args):
    """
    Unloads the menu by deleting it (if found)
    Args:
        *args: Variable number of arguments. Not used, only logged as debug.
    """
    logger.debug(f'Args: {str(args)}')
    menu = MayaMenu(MENU_NAME)
    menu.delete_menu()


def load_menu(*args):
    """
    Loads the package drop-down menu with various submenus and menu items.
    Args:
        *args: Variable number of arguments. Not used, only logged as debug.
    Returns:
        str: The path of the created menu.
    """
    logger.debug(f'Args: {str(args)}')
    package_version = get_package_version() or "?.?.?"

    menu = MayaMenu(MENU_NAME)
    # ------------------------------------ General / Tools ------------------------------------
    menu.add_sub_menu("General",
                      icon=resource_library.Icon.root_general,
                      parent_to_root=True)
    menu.add_menu_item(label='Attributes to Python',
                       command=partial(_open_named_tool, "attributes_to_python"),
                       tooltip='Converts attributes into Python code. TRS Channels or User-defined.',
                       icon=resource_library.Icon.tool_attributes_to_python)
    menu.add_menu_item(label='Color Manager',
                       command=partial(_open_named_tool, "color_manager"),
                       tooltip='A way to quickly change colors of objects and objects names (outliner).',
                       icon=resource_library.Icon.tool_color_manager)
    menu.add_menu_item(label='Outliner Sorter',
                       command=partial(_open_named_tool, "outliner_sorter"),
                       tooltip='Manages the order of the elements in the outliner.',
                       icon=resource_library.Icon.tool_outliner_sorter)
    menu.add_menu_item(label='Path Manager',
                       command=partial(_open_named_tool, "path_manager"),
                       tooltip='A script for managing and repairing the path of many nodes.',
                       icon=resource_library.Icon.tool_path_manager)
    menu.add_menu_item(label='Renamer',
                       command=partial(_open_named_tool, "renamer"),
                       tooltip='Script for renaming multiple objects.',
                       icon=resource_library.Icon.tool_renamer)
    menu.add_menu_item(label='Render Checklist',
                       command=partial(_open_named_tool, "render_checklist"),
                       tooltip='Performs a series of checks to detect common issues that are often accidentally '
                               'ignored/unnoticed.',
                       icon=resource_library.Icon.tool_render_checklist)
    menu.add_menu_item(label='Selection Manager',
                       command=partial(_open_named_tool, "selection_manager"),
                       tooltip='Manages or creates custom selections.',
                       icon=resource_library.Icon.tool_selection_manager)
    menu.add_menu_item(label='Transfer Transforms',
                       command=partial(_open_named_tool, "transfer_transforms"),
                       tooltip='Script for quickly transferring Translate, Rotate, and Scale between objects.',
                       icon=resource_library.Icon.tool_transfer_transforms)
    menu.add_menu_item(label='World Space Baker',
                       command=partial(_open_named_tool, "world_space_baker"),
                       tooltip='Script for getting and setting translate and rotate world space data.',
                       icon=resource_library.Icon.tool_world_space_baker)

    # ------------------------------------ Curves ------------------------------------
    menu.add_sub_menu("Curves",
                      icon=resource_library.Icon.root_curves,
                      parent_to_root=True)
    menu.add_menu_item(label='Generate Text Curve',
                       command=partial(_open_named_tool, "shape_text_to_curve"),
                       tooltip='Generates a single curve containing all shapes necessary to produce a word/text.',
                       icon=resource_library.Icon.tool_crv_text)
    menu.add_menu_item(label='Extract Python Curve',
                       command=partial(_open_named_tool, "shape_curve_to_python"),
                       tooltip='Generates the python code necessary to create a selected curve.',
                       icon=resource_library.Icon.tool_crv_python)
    menu.add_menu_item(label='Extract Curve State',
                       command=partial(_open_named_tool, "shape_extract_state"),
                       tooltip='Generates the python command necessary to reshape curves back to their stored state.',
                       icon=resource_library.Icon.tool_crv_extract_state)

    menu.add_divider()  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Combine Curves',
                       command=partial(_run_utility, "curve_utils", "selected_curves_combine"),
                       tooltip='Combine curves by moving all the shape objects inside one single transform.',
                       icon=resource_library.Icon.util_crv_combine)
    menu.add_menu_item(label='Separate Curves',
                       command=partial(_run_utility, "curve_utils", "selected_curves_separate"),
                       tooltip='Separate curves by moving every shape object to their own separated transform.',
                       icon=resource_library.Icon.util_crv_separate)

    # ------------------------------------ Modeling ------------------------------------
    menu.add_sub_menu("Modeling",
                      icon=resource_library.Icon.root_modeling,
                      parent_to_root=True)
    menu.add_menu_item(label='Transfer UVs',
                       command=partial(_open_named_tool, "transfer_uvs"),
                       tooltip='A script to export/import UVs as well as transfer them between objects.',
                       icon=resource_library.Icon.tool_transfer_uvs)
    menu.add_menu_item(label='Sphere Types',
                       command=partial(_open_named_tool, "create_sphere_types"),
                       tooltip='A reminder for students that there are other sphere types.',
                       icon=resource_library.Icon.tool_sphere_types)

    menu.add_divider()  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Preview All UDIMs',
                       command=partial(_run_utility, "display_utils", "generate_udim_previews"),
                       tooltip='Generates UDIM previews for all file nodes.',
                       icon=resource_library.Icon.util_mod_load_udims)
    menu.add_menu_item(label='Convert Bif to Mesh',
                       command=partial(_run_utility, "geometry_utils", "convert_bif_to_mesh"),
                       tooltip='Converts Bifrost Geometry into Maya Geometry (Mesh). '
                               'If used with volume or particles the output will be empty.',
                       icon=resource_library.Icon.util_mod_bif_to_mesh)

    menu.add_divider()  # Material Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Copy Material',
                       command=partial(_run_utility, "misc_utils", "material_copy"),
                       tooltip='Copies material to clipboard.',
                       icon=resource_library.Icon.util_mod_copy_material)
    menu.add_menu_item(label='Paste Material',
                       command=partial(_run_utility, "misc_utils", "material_paste"),
                       tooltip='Pastes material from clipboard.',
                       icon=resource_library.Icon.util_mod_paste_material)
    # ------------------------------------ Rigging ------------------------------------
    menu.add_sub_menu("Rigging",
                      icon=resource_library.Icon.root_rigging,
                      parent_to_root=True)
    menu.add_menu_item(label='Biped Auto Rigger',
                       command=partial(_open_named_tool, "auto_rigger"),
                       tooltip='Automated solution for creating a biped rig.',
                       icon=resource_library.Icon.tool_auto_rigger)
    menu.add_menu_item(label='Biped Rig Interface',
                       command=partial(_open_named_tool, "auto_rigger", "launch_biped_rig_interface"),
                       tooltip='Custom Rig Interface for GT Biped Auto Rigger.',
                       icon=resource_library.Icon.tool_rig_interface)
    menu.add_menu_item(label='Retarget Assistant',
                       command=partial(_open_named_tool, "auto_rigger", "launch_retarget_assistant"),
                       tooltip='Script with HumanIK patches.',
                       icon=resource_library.Icon.tool_retarget_assistant)
    menu.add_menu_item(label='Game FBX Exporter',
                       command=partial(_open_named_tool, "auto_rigger", "launch_game_exporter"),
                       tooltip='Automated solution for exporting real-time FBX files.',
                       icon=resource_library.Icon.tool_game_fbx_exporter)

    menu.add_divider()  # General Rigging Tools +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Add Sine Attributes',
                       command=partial(_open_named_tool, "sine_attributes"),
                       tooltip='Create Sine function without using third-party plugins or expressions.',
                       icon='sineCurveProfile.png')
    menu.add_menu_item(label='Connect Attributes',
                       command=partial(_open_named_tool, "connect_attributes"),
                       tooltip='Automated solution for connecting multiple attributes.',
                       icon='hsRearrange.png')
    menu.add_menu_item(label='Create Auto FK',
                       command=partial(_open_named_tool, "create_auto_fk"),
                       tooltip='Automated solution for created an FK control curve.',
                       icon='kinInsert.png')
    menu.add_menu_item(label='Create Testing Keys',
                       command=partial(_open_named_tool, "create_testing_keys"),
                       tooltip='Automated solution for creating testing keyframes.',
                       icon='setMaxInfluence.png')
    menu.add_menu_item(label='Extract Influence Joints',
                       command=partial(_open_named_tool, "extract_influence_joints"),
                       tooltip='Generate Python code used to select influence (bound) joints.',
                       icon='smoothSkin.png')
    menu.add_menu_item(label='Generate In-Between',
                       command=partial(_open_named_tool, "generate_inbetween"),
                       tooltip='Generates inbetween transforms that can be used as layers for rigging/animation.',
                       icon='hsGraphMaterial.png')
    menu.add_menu_item(label='Make IK Stretchy',
                       command=partial(_open_named_tool, "make_ik_stretchy"),
                       tooltip='Automated solution for making an IK system stretchy.',
                       icon='ikSCsolver.svg')
    menu.add_menu_item(label='Mirror Cluster Tool',
                       command=partial(_open_named_tool, "mirror_cluster_tool"),
                       tooltip='Automated solution for mirroring clusters.',
                       icon='cluster.png')
    menu.add_menu_item(label='Morphing Attributes',
                       command=partial(_open_named_tool, "morphing_attributes"),
                       tooltip='Creates attributes to drive selected blend shapes.',
                       icon='blendShape.png')
    menu.add_menu_item(label='Morphing Utilities',
                       command=partial(_open_named_tool, "morphing_utilities"),
                       tooltip='Morphing utilities (Blend Shapes).',
                       icon='falloff_blend.png')

    # ------------------------------------ Utilities ------------------------------------
    menu.add_sub_menu("Utilities",
                      icon=resource_library.Icon.root_utilities,
                      parent_to_root=True)
    menu.add_menu_item(label='Reload File',
                       command=partial(_run_utility, "scene_utils", "force_reload_file"),
                       tooltip='Forces the re-opening of an opened file. (Changes are ignored)',
                       icon='openScript.png')
    menu.add_menu_item(label='Open File Directory',
                       command=partial(_run_utility, "scene_utils", "open_file_dir"),
                       tooltip='Opens the directory where the scene is located.',
                       icon='openLoadGeneric.png')

    menu.add_divider()  # General +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Complete HUD Toggle',
                       command=partial(_run_utility, "display_utils", "toggle_full_hud"),
                       tooltip='Toggles most of the Heads-Up Display (HUD) options according to the state of '
                               'the majority of them. (Keeps default elements intact when toggling it off)',
                       icon='channelBox.png')
    menu.add_menu_item(label='Resource Browser',
                       command=partial(_run_utility, "misc_utils", "open_resource_browser"),
                       tooltip="Opens Maya's Resource Browser. "
                               "A good way to find icons or elements you may want to use.",
                       icon='bsd-head.png')
    menu.add_menu_item(label='Select Non-Unique Objects',
                       command=partial(_run_utility, "selection_utils", "select_non_unique_objects"),
                       tooltip='Selects all objects with the same short name. (non-unique objects)',
                       icon='gotoLine.png')
    menu.add_menu_item(label='Set Joint Name as Label',
                       command=partial(_run_utility, "display_utils", "set_joint_name_as_label"),
                       tooltip='Set the label of the selected joints to be the same as their short name.',
                       icon='falloff_transfer.png')
    menu.add_menu_item(label='Uniform LRA Toggle',
                       command=partial(_run_utility, "display_utils", "toggle_uniform_lra"),
                       tooltip='Makes the visibility of the Local Rotation Axis uniform among the selected '
                               'objects according to the current state of the majority of them.',
                       icon='srt.png')
    menu.add_menu_item(label='Uniform Joint Label Toggle',
                       command=partial(_run_utility, "display_utils", "toggle_uniform_jnt_label"),
                       tooltip='Makes the visibility of the joint labels uniform according to the current '
                               'state of the majority of them.',
                       icon='QR_xRay.png')
    menu.add_menu_item(label='Unhide Default Channels',
                       command=partial(_run_utility, "attribute_utils", "unhide_default_channels"),
                       tooltip='Un-hides the default channels of the selected objects. '
                               '(Default channels : Translate, Rotate, Scale and Visibility)',
                       icon='RS_filter_list.png')
    menu.add_menu_item(label='Unlock Default Channels',
                       command=partial(_run_utility, "attribute_utils", "unlock_default_channels"),
                       tooltip='Unlocks the default channels of the selected objects. '
                               '(Default channels : Translate, Rotate, Scale and Visibility)',
                       icon='Lock_OFF_grey.png')

    menu.add_divider()  # Convert Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Convert Joints to Mesh',
                       command=partial(_run_utility, "joint_utils", "convert_joints_to_mesh"),
                       tooltip='Converts joints to mesh. (Helpful when sending references to other applications)',
                       icon='HIKCharacterToolSkeleton.png')
    menu.add_menu_item(label='Convert to Locators',
                       command=partial(_run_utility, "transform_utils", "convert_transforms_to_locators"),
                       tooltip="Converts transforms to locators. Function doesn't affect selected objects.",
                       icon='locator.svg')

    menu.add_divider()  # References Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Import References',
                       command=partial(_run_utility, "reference_utils", "references_import"),
                       tooltip="Imports all references.",
                       icon='reference.svg')
    menu.add_menu_item(label='Remove References',
                       command=partial(_run_utility, "reference_utils", "references_remove"),
                       tooltip="Removes all references.",
                       icon='referenceProxy.png')

    menu.add_divider()  # Pivot Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Move Pivot to Top',
                       command=partial(_run_utility, "transform_utils", "move_pivot_top"),
                       tooltip="Moves pivot point to the top of the bounding box of every selected object.",
                       icon='moveLayerUp.png')
    menu.add_menu_item(label='Move Pivot to Base',
                       command=partial(_run_utility, "transform_utils", "move_pivot_base"),
                       tooltip="Moves pivot point to the base of the bounding box of every selected object.",
                       icon='moveLayerDown.png')
    menu.add_menu_item(label='Move Object to Origin',
                       command=partial(_run_utility, "transform_utils", "move_to_origin"),
                       tooltip="Moves selected objects to origin according to their pivot point.",
                       icon='grid.svg')

    menu.add_divider()  # Reset Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Reset Transforms',
                       command=partial(_run_utility, "transform_utils", "reset_transforms"),
                       tooltip="Reset transforms. It checks for incoming connections, then set the attribute to 0 "
                               "if there are none. Currently affects Joints, meshes and transforms. (Only Rotation)",
                       icon='CenterPivot.png')
    menu.add_menu_item(label='Reset Joints Display',
                       command=partial(_run_utility, "display_utils", "reset_joint_display"),
                       tooltip="Resets the radius attribute back to one in all joints, then changes the global "
                               "multiplier (jointDisplayScale) back to one.",
                       icon='kinJoint.png')
    menu.add_menu_item(label='Reset "persp" Camera',
                       command=partial(_run_utility, "attribute_utils", "reset_persp_shape_attributes"),
                       tooltip="If persp camera exists (default camera), reset its attributes.",
                       icon='camera.svg')

    menu.add_divider()  # Delete Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Delete Namespaces',
                       command=partial(_run_utility, "namespace_utils", "delete_namespaces"),
                       tooltip="Deletes all namespaces in the scene.",
                       icon='renamePreset.png')
    menu.add_menu_item(label='Delete Display Layers',
                       command=partial(_run_utility, "display_utils", "delete_display_layers"),
                       tooltip="Deletes all display layers.",
                       icon='displayLayer.svg')
    menu.add_menu_item(label='Delete Unused Nodes',
                       command=partial(_run_utility, "cleanup_utils", "delete_unused_nodes"),
                       tooltip="Deletes unused nodes.",
                       icon='nodeGrapherRemoveNodes.png')
    menu.add_menu_item(label='Delete Nucleus Nodes',
                       command=partial(_run_utility, "cleanup_utils", "delete_nucleus_nodes"),
                       tooltip="Deletes all nodes related to particles. "
                               "(Nucleus, nHair, nCloth, nConstraints, Emitter, etc...)",
                       icon='nParticle.svg')
    menu.add_menu_item(label='Delete Keyframes',
                       command=partial(_run_utility, "anim_utils", "delete_time_keyframes"),
                       tooltip='Deletes all nodes of the type "animCurveTA" (keyframes).',
                       icon='keyIntoclip.png')

    # ------------------------------------ Miscellaneous ------------------------------------
    menu.add_sub_menu("Miscellaneous",
                      icon=resource_library.Icon.root_miscellaneous,
                      parent_to_root=True)
    menu.add_menu_item(label='Startup Booster',
                       command=partial(_open_named_tool, "startup_booster"),
                       tooltip='Improve startup times by managing which plugins get loaded when starting Maya.',
                       icon=resource_library.Icon.tool_startup_booster)
    menu.add_menu_item(label='fSpy Importer',
                       command=partial(_open_named_tool, "fspy_importer"),
                       tooltip='Imports the JSON data exported out of fSpy (Camera Matching software).',
                       icon=resource_library.Icon.tool_fspy_importer)
    menu.add_menu_item(label='Maya to Discord',
                       command=partial(_open_named_tool, "maya_to_discord"),
                       tooltip='Send images and videos (playblasts) from Maya to Discord using a '
                               'Discord Webhook to bridge the two programs.',
                       icon=resource_library.Icon.tool_maya_to_discord)
    menu.add_menu_item(label='Render Calculator',
                       command=partial(_open_named_tool, "render_calculator"),
                       tooltip="Helps calculate how long it's going to take to render an image sequence.",
                       icon=resource_library.Icon.tool_render_calculator)
    # ------------------------------------ Development ------------------------------------
    if False:  # TODO - Replace with global variable
        menu.add_sub_menu("Develop",
                          icon=resource_library.Icon.misc_about,
                          parent_to_root=True)
        menu.add_menu_item(label='Sample Tool',
                           command=partial(_open_named_tool, "sample_tool"),
                           tooltip="Opens sample tool.",
                           icon=resource_library.Icon.misc_about)
    # ------------------------------------ About/Help ------------------------------------
    menu.add_divider(parent_to_root=True)
    menu.add_sub_menu("Help",
                      icon=resource_library.Icon.root_help,
                      parent_to_root=True)
    menu.add_menu_item(label='About',
                       command=partial(_open_named_tool, "package_setup", "open_about_window"),
                       tooltip="Opens about menu.",
                       icon=resource_library.Icon.misc_about)
    menu.add_menu_item(label='Re-Build Menu',
                       command=_rebuild_menu,
                       tooltip="Re-Creates this menu, and does a rehash to pick up any new scripts.",
                       icon=resource_library.Icon.misc_rebuild_menu)
    menu.add_menu_item(label='Check for Updates',
                       command=partial(_open_named_tool, "check_for_updates"),
                       tooltip="Check for updates by comparing current version with latest release.",
                       icon=resource_library.Icon.tool_check_for_updates)
    menu.add_menu_item(label=f'Installed Version: {str(package_version)}',
                       enable=False,
                       icon=resource_library.Icon.misc_current_version)
    # ------------------------------------ End ------------------------------------
    menu_path = menu.create_menu()
    return menu_path


if __name__ == "__main__":
    from pprint import pprint
    logger.setLevel(logging.DEBUG)
    out = None
    out = load_menu()
    pprint(out)
