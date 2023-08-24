"""
 Main Maya Menu - GT Tools Menu - Creates a menu to call scripts from the GT Tools Package
 github.com/TrevisanGMW/gt-tools - 2020-03-03
"""
from gt.utils.version_utils import get_package_version
import gt.ui.resource_library as resource_library
from gt.utils.prefs_utils import PackagePrefs
from gt.ui.maya_menu import MayaMenu
import logging
import sys

# Setup  Logger
logging.basicConfig()
logger = logging.getLogger(__name__)

MENU_NAME = "GT Tools"
IMPORT_TOOL = "from gt.utils.system_utils import initialize_tool\n"
IMPORT_UTIL = "from gt.utils.system_utils import initialize_utility\n"


def _rebuild_menu(*args):
    """
    Rebuilds the menu.
    Args:
       *args: Variable number of arguments. Not used, only logged as debug.
    """
    logger.debug(f'Args: {str(args)}')
    sys.stdout.write("Re-building GT Tools Menu...\n")
    load_menu()


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
                       command=IMPORT_TOOL + 'initialize_tool("attributes_to_python")',
                       tooltip='Converts attributes into Python code. TRS Channels or User-defined.',
                       icon=resource_library.Icon.tool_attributes_to_python)
    menu.add_menu_item(label='Color Manager',
                       command=IMPORT_TOOL + 'initialize_tool("color_manager")',
                       tooltip='A way to quickly change colors of objects and objects names (outliner).',
                       icon=resource_library.Icon.tool_color_manager_roller)
    menu.add_menu_item(label='Outliner Sorter',
                       command=IMPORT_TOOL + 'initialize_tool("outliner_sorter")',
                       tooltip='Manages the order of the elements in the outliner.',
                       icon=resource_library.Icon.tool_outliner_sorter)
    menu.add_menu_item(label='Path Manager',
                       command=IMPORT_TOOL + 'initialize_tool("path_manager")',
                       tooltip='A script for managing and repairing the path of many nodes.',
                       icon=resource_library.Icon.tool_path_manager)
    menu.add_menu_item(label='Renamer',
                       command=IMPORT_TOOL + 'initialize_tool("renamer")',
                       tooltip='Script for renaming multiple objects.',
                       icon=resource_library.Icon.tool_renamer)
    menu.add_menu_item(label='Render Checklist',
                       command=IMPORT_TOOL + 'initialize_tool("render_checklist")',
                       tooltip='Performs a series of checks to detect common issues that are often accidentally '
                               'ignored/unnoticed.',
                       icon=resource_library.Icon.tool_render_checklist)
    menu.add_menu_item(label='Selection Manager',
                       command=IMPORT_TOOL + 'initialize_tool("selection_manager")',
                       tooltip='Manages or creates custom selections.',
                       icon=resource_library.Icon.tool_selection_manager)
    menu.add_menu_item(label='Transfer Transforms',
                       command=IMPORT_TOOL + 'initialize_tool("transfer_transforms")',
                       tooltip='Script for quickly transferring Translate, Rotate, and Scale between objects.',
                       icon=resource_library.Icon.tool_transfer_transforms)
    menu.add_menu_item(label='World Space Baker',
                       command=IMPORT_TOOL + 'initialize_tool("world_space_baker")',
                       tooltip='Script for getting and setting translate and rotate world space data.',
                       icon=resource_library.Icon.tool_world_space_baker)

    # ------------------------------------ Curves ------------------------------------
    menu.add_sub_menu("Curves",
                      icon=resource_library.Icon.root_curves,
                      parent_to_root=True)
    menu.add_menu_item(label='Curve Library',
                       command=IMPORT_TOOL + 'initialize_tool("curve_library")',
                       tooltip="Open Curve Library tools.",
                       icon=resource_library.Icon.tool_crv_library)
    menu.add_menu_item(label='Generate Text Curve',
                       command=IMPORT_TOOL + 'initialize_tool("shape_text_to_curve")',
                       tooltip='Generates a single curve containing all shapes necessary to produce a word/text.',
                       icon=resource_library.Icon.tool_crv_text)
    menu.add_menu_item(label='Extract Python Curve',
                       command=IMPORT_TOOL + 'initialize_tool("shape_curve_to_python")',
                       tooltip='Generates the python code necessary to create a selected curve.',
                       icon=resource_library.Icon.tool_crv_python)
    menu.add_menu_item(label='Extract Curve State',
                       command=IMPORT_TOOL + 'initialize_tool("shape_extract_state")',
                       tooltip='Generates the python command necessary to reshape curves back to their stored state.',
                       icon=resource_library.Icon.tool_crv_extract_state)

    menu.add_divider(divider_label="Utilities")  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Combine Curves',
                       command=IMPORT_UTIL + 'initialize_utility("curve_utils", "selected_curves_combine")',
                       tooltip='Combine curves by moving all the shape objects inside one single transform.',
                       icon=resource_library.Icon.util_crv_combine)
    menu.add_menu_item(label='Separate Curves',
                       command=IMPORT_UTIL + 'initialize_utility("curve_utils", "selected_curves_separate")',
                       tooltip='Separate curves by moving every shape object to their own separated transform.',
                       icon=resource_library.Icon.util_crv_separate)

    # ------------------------------------ Modeling ------------------------------------
    menu.add_sub_menu("Modeling",
                      icon=resource_library.Icon.root_modeling,
                      parent_to_root=True)
    menu.add_menu_item(label='Transfer UVs',
                       command=IMPORT_TOOL + 'initialize_tool("transfer_uvs")',
                       tooltip='A script to export/import UVs as well as transfer them between objects.',
                       icon=resource_library.Icon.tool_transfer_uvs)
    menu.add_menu_item(label='Sphere Types',
                       command=IMPORT_TOOL + 'initialize_tool("create_sphere_types")',
                       tooltip='A reminder for students that there are other sphere types.',
                       icon=resource_library.Icon.tool_sphere_types)

    menu.add_divider(divider_label="Utilities")  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Preview All UDIMs',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "generate_udim_previews")',
                       tooltip='Generates UDIM previews for all file nodes.',
                       icon=resource_library.Icon.util_mod_load_udims)
    menu.add_menu_item(label='Convert Bif to Mesh',
                       command=IMPORT_UTIL + 'initialize_utility("geometry_utils", "convert_bif_to_mesh")',
                       tooltip='Converts Bifrost Geometry into Maya Geometry (Mesh). '
                               'If used with volume or particles the output will be empty.',
                       icon=resource_library.Icon.util_mod_bif_to_mesh)

    menu.add_divider(divider_label="Copy/Paste Utilities")  # Material Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Copy Material',
                       command=IMPORT_UTIL + 'initialize_utility("misc_utils", "material_copy")',
                       tooltip='Copies material to clipboard.',
                       icon=resource_library.Icon.util_mod_copy_material)
    menu.add_menu_item(label='Paste Material',
                       command=IMPORT_UTIL + 'initialize_utility("misc_utils", "material_paste")',
                       tooltip='Pastes material from clipboard.',
                       icon=resource_library.Icon.util_mod_paste_material)
    # ------------------------------------ Rigging ------------------------------------
    menu.add_sub_menu("Rigging",
                      icon=resource_library.Icon.root_rigging,
                      parent_to_root=True)
    menu.add_menu_item(label='Biped Auto Rigger',
                       command=IMPORT_TOOL + 'initialize_tool("auto_rigger")',
                       tooltip='Automated solution for creating a biped rig.',
                       icon=resource_library.Icon.tool_auto_rigger)
    menu.add_menu_item(label='Biped Rig Interface',
                       command=IMPORT_TOOL + 'initialize_tool("auto_rigger", "launch_biped_rig_interface")',
                       tooltip='Custom Rig Interface for GT Biped Auto Rigger.',
                       icon=resource_library.Icon.tool_rig_interface)
    menu.add_menu_item(label='Retarget Assistant',
                       command=IMPORT_TOOL + 'initialize_tool("auto_rigger", "launch_retarget_assistant")',
                       tooltip='Script with HumanIK patches.',
                       icon=resource_library.Icon.tool_retarget_assistant)
    menu.add_menu_item(label='Game FBX Exporter',
                       command=IMPORT_TOOL + 'initialize_tool("auto_rigger", "launch_game_exporter")',
                       tooltip='Automated solution for exporting real-time FBX files.',
                       icon=resource_library.Icon.tool_game_fbx_exporter)

    menu.add_divider()  # General Rigging Tools +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Add In-Between',
                       command=IMPORT_TOOL + 'initialize_tool("add_inbetween")',
                       tooltip='Generates inbetween transforms that can be used as layers for rigging/animation.',
                       icon=resource_library.Icon.tool_add_inbetween)
    menu.add_menu_item(label='Add Sine Attributes',
                       command=IMPORT_TOOL + 'initialize_tool("sine_attributes")',
                       tooltip='Create Sine function without using third-party plugins or expressions.',
                       icon=resource_library.Icon.tool_sine_attributes)
    menu.add_menu_item(label='Connect Attributes',
                       command=IMPORT_TOOL + 'initialize_tool("connect_attributes")',
                       tooltip='Automated solution for connecting multiple attributes.',
                       icon=resource_library.Icon.tool_connect_attributes)
    menu.add_menu_item(label='Create Auto FK',
                       command=IMPORT_TOOL + 'initialize_tool("create_auto_fk")',
                       tooltip='Automated solution for created an FK control curve.',
                       icon=resource_library.Icon.tool_create_fk)
    menu.add_menu_item(label='Create Testing Keys',
                       command=IMPORT_TOOL + 'initialize_tool("create_testing_keys")',
                       tooltip='Automated solution for creating testing keyframes.',
                       icon=resource_library.Icon.tool_testing_keys)
    menu.add_menu_item(label='Extract Influence Joints',
                       command=IMPORT_TOOL + 'initialize_tool("extract_influence_joints")',
                       tooltip='Generate Python code used to select influence (bound) joints.',
                       icon=resource_library.Icon.tool_influence_joints)
    menu.add_menu_item(label='Make IK Stretchy',
                       command=IMPORT_TOOL + 'initialize_tool("make_ik_stretchy")',
                       tooltip='Automated solution for making an IK system stretchy.',
                       icon=resource_library.Icon.tool_make_ik_stretchy)
    menu.add_menu_item(label='Mirror Cluster Tool',
                       command=IMPORT_TOOL + 'initialize_tool("mirror_cluster_tool")',
                       tooltip='Automated solution for mirroring clusters.',
                       icon=resource_library.Icon.tool_mirror_cluster)
    menu.add_menu_item(label='Morphing Attributes',
                       command=IMPORT_TOOL + 'initialize_tool("morphing_attributes")',
                       tooltip='Creates attributes to drive selected blend shapes.',
                       icon=resource_library.Icon.tool_morphing_attributes)
    menu.add_menu_item(label='Morphing Utilities',
                       command=IMPORT_TOOL + 'initialize_tool("morphing_utilities")',
                       tooltip='Morphing utilities (Blend Shapes).',
                       icon=resource_library.Icon.tool_morphing_utils)

    # ------------------------------------ Utilities ------------------------------------
    menu.add_sub_menu("Utilities",
                      icon=resource_library.Icon.root_utilities,
                      parent_to_root=True)
    menu.add_menu_item(label='Reload File',
                       command=IMPORT_UTIL + 'initialize_utility("scene_utils", "force_reload_file")',
                       tooltip='Forces the re-opening of an opened file. (Changes are ignored)',
                       icon=resource_library.Icon.util_reload_file)
    menu.add_menu_item(label='Open File Directory',
                       command=IMPORT_UTIL + 'initialize_utility("scene_utils", "open_file_dir")',
                       tooltip='Opens the directory where the scene is located.',
                       icon=resource_library.Icon.util_open_dir)

    menu.add_divider(divider_label="General Utilities")  # General +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Complete HUD Toggle',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "toggle_full_hud")',
                       tooltip='Toggles most of the Heads-Up Display (HUD) options according to the state of '
                               'the majority of them. (Keeps default elements intact when toggling it off)',
                       icon=resource_library.Icon.util_hud_toggle)
    menu.add_menu_item(label='Resource Browser',
                       command=IMPORT_UTIL + 'initialize_utility("misc_utils", "open_resource_browser")',
                       tooltip="Opens Maya's Resource Browser. "
                               "A good way to find icons or elements you may want to use.",
                       icon=resource_library.Icon.util_resource_browser)
    menu.add_menu_item(label='Select Non-Unique Objects',
                       command=IMPORT_UTIL + 'initialize_utility("selection_utils", "select_non_unique_objects")',
                       tooltip='Selects all objects with the same short name. (non-unique objects)',
                       icon=resource_library.Icon.util_sel_non_unique)
    menu.add_menu_item(label='Set Joint Name as Label',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "set_joint_name_as_label")',
                       tooltip='Set the label of the selected joints to be the same as their short name.',
                       icon=resource_library.Icon.util_joint_to_label)
    menu.add_menu_item(label='Uniform LRA Toggle',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "toggle_uniform_lra")',
                       tooltip='Makes the visibility of the Local Rotation Axis uniform among the selected '
                               'objects according to the current state of the majority of them.',
                       icon=resource_library.Icon.util_lra_toggle)
    menu.add_menu_item(label='Uniform Joint Label Toggle',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "toggle_uniform_jnt_label")',
                       tooltip='Makes the visibility of the joint labels uniform according to the current '
                               'state of the majority of them.',
                       icon=resource_library.Icon.util_joint_label_toggle)
    menu.add_menu_item(label='Unhide Default Channels',
                       command=IMPORT_UTIL + 'initialize_utility("attr_utils", '
                                             '"selection_unhide_default_channels")',
                       tooltip='Un-hides the default channels of the selected objects. '
                               '(Default channels : Translate, Rotate, Scale and Visibility)',
                       icon=resource_library.Icon.util_unhide_trs)
    menu.add_menu_item(label='Unlock Default Channels',
                       command=IMPORT_UTIL + 'initialize_utility("attr_utils", '
                                             '"selection_unlock_default_channels")',
                       tooltip='Unlocks the default channels of the selected objects. '
                               '(Default channels : Translate, Rotate, Scale and Visibility)',
                       icon=resource_library.Icon.util_unlock_trs)

    menu.add_divider(divider_label="Convert Utilities")  # Convert Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Convert Joints to Mesh',
                       command=IMPORT_UTIL + 'initialize_utility("joint_utils", "convert_joints_to_mesh")',
                       tooltip='Converts joints to mesh. (Helpful when sending references to other applications)',
                       icon=resource_library.Icon.util_convert_joint_mesh)
    menu.add_menu_item(label='Convert to Locators',
                       command=IMPORT_UTIL + 'initialize_utility("transform_utils", "convert_transforms_to_locators")',
                       tooltip="Converts transforms to locators. Function doesn't affect selected objects.",
                       icon=resource_library.Icon.util_convert_loc)

    menu.add_divider(divider_label="Reference Utilities")  # References Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Import References',
                       command=IMPORT_UTIL + 'initialize_utility("reference_utils", "references_import")',
                       tooltip="Imports all references.",
                       icon=resource_library.Icon.util_ref_import)
    menu.add_menu_item(label='Remove References',
                       command=IMPORT_UTIL + 'initialize_utility("reference_utils", "references_remove")',
                       tooltip="Removes all references.",
                       icon=resource_library.Icon.util_ref_remove)

    menu.add_divider(divider_label="Pivot Utilities")  # Pivot Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Move Pivot to Top',
                       command=IMPORT_UTIL + 'initialize_utility("transform_utils", "move_pivot_top")',
                       tooltip="Moves pivot point to the top of the bounding box of every selected object.",
                       icon=resource_library.Icon.util_pivot_top)
    menu.add_menu_item(label='Move Pivot to Base',
                       command=IMPORT_UTIL + 'initialize_utility("transform_utils", "move_pivot_base")',
                       tooltip="Moves pivot point to the base of the bounding box of every selected object.",
                       icon=resource_library.Icon.util_pivot_bottom)
    menu.add_menu_item(label='Move Object to Origin',
                       command=IMPORT_UTIL + 'initialize_utility("transform_utils", "move_selection_to_origin")',
                       tooltip="Moves selected objects to origin according to their pivot point.",
                       icon=resource_library.Icon.util_move_origin)

    menu.add_divider(divider_label="Reset Utilities")  # Reset Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Reset Transforms',
                       command=IMPORT_UTIL + 'initialize_utility("transform_utils", "reset_transforms")',
                       tooltip="Reset transforms. It checks for incoming connections, then set the attribute to 0 "
                               "if there are none. Currently affects Joints, meshes and transforms. (Only Rotation)",
                       icon=resource_library.Icon.util_reset_transforms)
    menu.add_menu_item(label='Reset Joints Display',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "reset_joint_display")',
                       tooltip="Resets the radius attribute back to one in all joints, then changes the global "
                               "multiplier (jointDisplayScale) back to one.",
                       icon=resource_library.Icon.util_reset_jnt_display)
    menu.add_menu_item(label='Reset "persp" Camera',
                       command=IMPORT_UTIL + 'initialize_utility("camera_utils", "reset_persp_shape_attributes")',
                       tooltip="If persp camera exists (default camera), reset its attributes.",
                       icon=resource_library.Icon.util_reset_persp)

    menu.add_divider(divider_label="Delete Utilities")  # Delete Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(label='Delete Custom Attributes',
                       command=IMPORT_UTIL + 'initialize_utility("attr_utils", '
                                             '"selection_delete_user_defined_attributes")',
                       tooltip='Deletes user-defined (custom) attributes found on the selected objects.',
                       icon=resource_library.Icon.util_delete_custom_attr)
    menu.add_menu_item(label='Delete Namespaces',
                       command=IMPORT_UTIL + 'initialize_utility("namespace_utils", "delete_namespaces")',
                       tooltip="Deletes all namespaces in the scene.",
                       icon=resource_library.Icon.util_delete_ns)
    menu.add_menu_item(label='Delete Display Layers',
                       command=IMPORT_UTIL + 'initialize_utility("display_utils", "delete_display_layers")',
                       tooltip="Deletes all display layers.",
                       icon=resource_library.Icon.util_delete_display_layers)
    menu.add_menu_item(label='Delete Unused Nodes',
                       command=IMPORT_UTIL + 'initialize_utility("cleanup_utils", "delete_unused_nodes")',
                       tooltip="Deletes unused nodes.",
                       icon=resource_library.Icon.util_delete_unused_nodes)
    menu.add_menu_item(label='Delete Nucleus Nodes',
                       command=IMPORT_UTIL + 'initialize_utility("cleanup_utils", "delete_nucleus_nodes")',
                       tooltip="Deletes all nodes related to particles. "
                               "(Nucleus, nHair, nCloth, nConstraints, Emitter, etc...)",
                       icon=resource_library.Icon.util_delete_nucleus_nodes)
    menu.add_menu_item(label='Delete Keyframes',
                       command=IMPORT_UTIL + 'initialize_utility("anim_utils", "delete_time_keyframes")',
                       tooltip='Deletes all nodes of the type "animCurveTA" (keyframes).',
                       icon=resource_library.Icon.util_delete_keyframes)

    # ------------------------------------ Miscellaneous ------------------------------------
    menu.add_sub_menu("Miscellaneous",
                      icon=resource_library.Icon.root_miscellaneous,
                      parent_to_root=True)
    menu.add_menu_item(label='Startup Booster',
                       command=IMPORT_TOOL + 'initialize_tool("startup_booster")',
                       tooltip='Improve startup times by managing which plugins get loaded when starting Maya.',
                       icon=resource_library.Icon.tool_startup_booster)
    menu.add_menu_item(label='fSpy Importer',
                       command=IMPORT_TOOL + 'initialize_tool("fspy_importer")',
                       tooltip='Imports the JSON data exported out of fSpy (Camera Matching software).',
                       icon=resource_library.Icon.tool_fspy_importer)
    menu.add_menu_item(label='Maya to Discord',
                       command=IMPORT_TOOL + 'initialize_tool("maya_to_discord")',
                       tooltip='Send images and videos (playblasts) from Maya to Discord using a '
                               'Discord Webhook to bridge the two programs.',
                       icon=resource_library.Icon.tool_maya_to_discord)
    menu.add_menu_item(label='Render Calculator',
                       command=IMPORT_TOOL + 'initialize_tool("render_calculator")',
                       tooltip="Helps calculate how long it's going to take to render an image sequence.",
                       icon=resource_library.Icon.tool_render_calculator)
    # ------------------------------------ Development ------------------------------------
    if PackagePrefs().is_dev_menu_visible():
        menu.add_sub_menu("Develop",
                          icon=resource_library.Icon.root_dev,
                          parent_to_root=True)
        menu.add_menu_item(label='Sample Tool',
                           command=IMPORT_TOOL + 'initialize_tool("sample_tool")',
                           tooltip="Opens sample tool.",
                           icon=resource_library.Icon.dev_screwdriver)
        menu.add_divider(divider_label="Curves")  # Curve Thumbnails Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(label='Add Thumbnail Metadata to Selection',
                           command='from gt.utils.curve_utils import add_thumbnail_metadata_attr_to_selection\n'
                                   'add_thumbnail_metadata_attr_to_selection()\n',
                           tooltip="Add thumbnail metadata attributes to selection.",
                           icon=resource_library.Icon.dev_filter)
        menu.add_menu_item(label='Write Curve Files from Selection',
                           command='from gt.utils.curve_utils import write_curve_files_from_selection\n'
                                   'write_curve_files_from_selection()\n',
                           tooltip="Write curve data attributes to a desktop folder.",
                           icon=resource_library.Icon.dev_binary)
        menu.add_menu_item(label='Print Package CRV files to Python',
                           command='from gt.utils.curve_utils import print_code_for_crv_files\n'
                                   'print_code_for_crv_files()\n',
                           tooltip='Prints Python Lines used to call curves from "Curves" class.',
                           icon=resource_library.Icon.dev_binary)
        menu.add_menu_item(label='Render Package Curves Thumbnails',
                           command='from gt.utils.curve_utils import generate_package_curves_thumbnails\n'
                                   'generate_package_curves_thumbnails()\n',
                           tooltip="Render thumbnails for the package curves to a desktop folder.",
                           icon=resource_library.Icon.dev_picker)
        menu.add_divider(divider_label="General")  # Misc Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(label='Take Viewport Snapshot',
                           command='from gt.utils.playblast_utils import render_viewport_snapshot\n'
                                   'from gt.utils.system_utils import get_desktop_path, get_formatted_time\n'
                                   'render_viewport_snapshot(get_formatted_time(format_str="Snapshot %Y-%m-%d %H%M%S"),'
                                   ' get_desktop_path())',
                           tooltip="Saves a viewport snapshot to the desktop.",
                           icon=resource_library.Icon.dev_picker)
        menu.add_menu_item(label='Silently Check for Updates',
                           command=IMPORT_TOOL + 'initialize_tool("package_updater", "silently_check_for_updates")',
                           tooltip="Silently checks for updates.",
                           icon=resource_library.Icon.dev_git_pull_request)
        menu.add_menu_item(label='Get Loaded Package Location',
                           command='from gt.utils.session_utils import get_module_path\n'
                                   'from gt.utils.system_utils import open_file_dir\n'
                                   'open_file_dir(get_module_path(module_name="gt", verbose=True))\n',
                           tooltip="Gets the loaded package path location.",
                           icon=resource_library.Icon.dev_code)
        menu.add_divider(divider_label="Dangerous")  # Misc Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(label='Skip Menu Creation Toggle',
                           command='from gt.utils.prefs_utils import toggle_skip_menu_creation\n'
                                   'toggle_skip_menu_creation()\n',
                           tooltip="Opens sample tool.",
                           icon=resource_library.Icon.dev_code)
        menu.add_menu_item(label='Purge Package Settings',
                           command='from gt.utils.prefs_utils import purge_package_settings\n'
                                   'purge_package_settings()\n',
                           tooltip="Opens sample tool.",
                           icon=resource_library.Icon.dev_trash)
    # ------------------------------------ About/Help ------------------------------------
    menu.add_divider(parent_to_root=True)
    menu.add_sub_menu("Help",
                      icon=resource_library.Icon.root_help,
                      parent_to_root=True)
    menu.add_menu_item(label='About',
                       command=IMPORT_TOOL + 'initialize_tool("package_setup", "open_about_window")',
                       tooltip="Opens about menu.",
                       icon=resource_library.Icon.misc_about)
    _rebuild_menu_command = "from gt.tools.package_setup.gt_tools_maya_menu import _rebuild_menu\n_rebuild_menu()"
    menu.add_menu_item(label='Re-Build Menu',
                       command=_rebuild_menu_command,
                       tooltip="Re-Creates this menu, and does a rehash to pick up any new scripts.",
                       icon=resource_library.Icon.misc_rebuild_menu)
    menu.add_menu_item(label='Check for Updates',
                       command=IMPORT_TOOL + 'initialize_tool("package_updater")',
                       tooltip="Check for updates by comparing current version with latest release.",
                       icon=resource_library.Icon.tool_package_updater)
    menu.add_menu_item(label='Develop Menu Toggle',
                       command='from gt.utils.prefs_utils import toggle_dev_sub_menu\n'
                               'toggle_dev_sub_menu()\n' + _rebuild_menu_command,
                       tooltip="Check for updates by comparing current version with latest release.",
                       icon=resource_library.Icon.root_dev)
    menu.add_menu_item(label=f'Installed Version: {str(package_version)}',
                       enable=False,
                       icon=resource_library.Icon.misc_current_version)
    # ------------------------------------ End ------------------------------------
    if PackagePrefs().is_skipping_menu_creation():
        print('GT-Tools: "Skip Menu Creation" preference is active. Menu creation was skipped.')
        unload_menu()
        return
    menu_path = menu.create_menu()
    return menu_path


if __name__ == "__main__":
    from pprint import pprint
    logger.setLevel(logging.DEBUG)
    out = None
    out = load_menu()
    pprint(out)
