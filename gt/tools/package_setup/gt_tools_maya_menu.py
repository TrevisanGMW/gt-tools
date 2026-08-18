"""
 Main Maya Menu - GT Tools Menu - Creates a menu to call scripts from the GT Tools Package
 github.com/TrevisanGMW/gt-tools - 2020-03-03
"""

from gt.core.version import get_package_version
import gt.ui.resource_library as ui_res_lib
from gt.core.prefs import PackagePrefs
from gt.ui.maya_menu import MayaMenu
from gt.utils.dependency import is_auto_install_enabled
import logging
import sys

# Setup  Logger
logging.basicConfig()
logger = logging.getLogger(__name__)

MENU_NAME = "GT Tools"
IMPORT_TOOL = "from gt.utils.system import initialize_tool\n"
IMPORT_UTIL = "from gt.utils.system import initialize_utility\n"


def _rebuild_menu(*args):
    """
    Rebuilds the menu.
    Args:
       *args: Variable number of arguments. Not used, only logged as debug.
    """
    logger.debug(f"Args: {str(args)}")
    sys.stdout.write("Re-building GT Tools Menu...\n")
    load_menu()


def unload_menu(*args):
    """
    Unloads the menu by deleting it (if found)
    Args:
        *args: Variable number of arguments. Not used, only logged as debug.
    """
    logger.debug(f"Args: {str(args)}")
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
    logger.debug(f"Args: {str(args)}")
    package_version = get_package_version() or "?.?.?"

    menu = MayaMenu(MENU_NAME)
    # ------------------------------------ General / Tools ------------------------------------
    menu.add_sub_menu("General", icon=ui_res_lib.Icon.root_general, parent_to_root=True)
    menu.add_menu_item(
        label="Batch Processor",
        command=IMPORT_TOOL + 'initialize_tool("batch_processor")',
        tooltip="Opens the batch processor.",
        icon=ui_res_lib.Icon.tool_batch_processor,
    )
    menu.add_divider(parent="General")
    menu.add_menu_item(
        label="Attributes to Python",
        command=IMPORT_TOOL + 'initialize_tool("attributes_to_python")',
        tooltip="Converts attributes into Python code. TRS Channels or User-defined.",
        icon=ui_res_lib.Icon.tool_attributes_to_python,
    )
    menu.add_menu_item(
        label="Color Manager",
        command=IMPORT_TOOL + 'initialize_tool("color_manager")',
        tooltip="A way to quickly change colors of objects and objects names (outliner).",
        icon=ui_res_lib.Icon.tool_color_manager_roller,
    )
    menu.add_menu_item(
        label="Outliner Sorter",
        command=IMPORT_TOOL + 'initialize_tool("outliner_sorter")',
        tooltip="Manages the order of the elements in the outliner.",
        icon=ui_res_lib.Icon.tool_outliner_sorter,
    )
    menu.add_menu_item(
        label="Path Manager",
        command=IMPORT_TOOL + 'initialize_tool("path_manager")',
        tooltip="A script for managing and repairing the path of many nodes.",
        icon=ui_res_lib.Icon.tool_path_manager,
    )
    menu.add_menu_item(
        label="Renamer",
        command=IMPORT_TOOL + 'initialize_tool("renamer")',
        tooltip="Script for renaming multiple objects.",
        icon=ui_res_lib.Icon.tool_renamer,
    )
    menu.add_menu_item(
        label="Selection Manager",
        command=IMPORT_TOOL + 'initialize_tool("selection_manager")',
        tooltip="Manages or creates custom selections.",
        icon=ui_res_lib.Icon.tool_selection_manager,
    )
    menu.add_menu_item(
        label="Transfer Transforms",
        command=IMPORT_TOOL + 'initialize_tool("transfer_transforms")',
        tooltip="Script for quickly transferring Translate, Rotate, and Scale between objects.",
        icon=ui_res_lib.Icon.tool_transfer_transforms,
    )
    # ------------------------------------ Curves ------------------------------------
    menu.add_sub_menu("Curves", icon=ui_res_lib.Icon.root_curves, parent_to_root=True)
    menu.add_menu_item(
        label="Curve Library",
        command=IMPORT_TOOL + 'initialize_tool("curve_library")',
        tooltip="Open the Curve Library tool.",
        icon=ui_res_lib.Icon.tool_crv_library,
    )
    menu.add_menu_item(
        label="Curve to Python",
        command=IMPORT_TOOL + 'initialize_tool("curve_to_python")',
        tooltip="Extracts python code to recreate or reshape curves.",
        icon=ui_res_lib.Icon.tool_crv_python,
    )
    menu.add_menu_item(
        label="Generate Text Curve",
        command=IMPORT_TOOL + 'initialize_tool("shape_text_to_curve")',
        tooltip="Generates a single curve containing all shapes necessary to produce a word/text.",
        icon=ui_res_lib.Icon.tool_crv_text,
    )

    menu.add_divider(divider_label="Utilities")  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Combine Curves",
        command=IMPORT_UTIL + 'initialize_utility("curve", "selected_curves_combine")',
        tooltip="Combine curves by moving all the shape objects inside one single transform.",
        icon=ui_res_lib.Icon.util_crv_combine,
    )
    menu.add_menu_item(
        label="Separate Curves",
        command=IMPORT_UTIL + 'initialize_utility("curve", "selected_curves_separate")',
        tooltip="Separate curves by moving every shape object to their own separated transform.",
        icon=ui_res_lib.Icon.util_crv_separate,
    )

    # ------------------------------------ Modeling ------------------------------------
    menu.add_sub_menu("Modeling", icon=ui_res_lib.Icon.root_modeling, parent_to_root=True)
    menu.add_menu_item(
        label="Mesh Morpher",
        command=IMPORT_TOOL + 'initialize_tool("mesh_morpher")',
        tooltip="Opens the Mesh Morpher tool.",
        icon=ui_res_lib.Icon.tool_mesh_morpher,
    )
    menu.add_menu_item(
        label="Mesh Library",
        command=IMPORT_TOOL + 'initialize_tool("mesh_library")',
        tooltip="Open the Mesh Library tool.",
        icon=ui_res_lib.Icon.tool_mesh_library,
    )
    menu.add_menu_item(
        label="Transfer UVs",
        command=IMPORT_TOOL + 'initialize_tool("transfer_uvs")',
        tooltip="A script to export/import UVs as well as transfer them between objects.",
        icon=ui_res_lib.Icon.tool_transfer_uvs,
    )

    menu.add_divider(divider_label="Utilities")  # Utility Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Preview All UDIMs",
        command=IMPORT_UTIL + 'initialize_utility("display", "generate_udim_previews")',
        tooltip="Generates UDIM previews for all file nodes.",
        icon=ui_res_lib.Icon.util_mod_load_udims,
    )
    menu.add_menu_item(
        label="Convert Bif to Mesh",
        command=IMPORT_UTIL + 'initialize_utility("mesh", "convert_bif_to_mesh")',
        tooltip="Converts Bifrost Geometry into Maya Geometry (Mesh). "
        "If used with volume or particles the output will be empty.",
        icon=ui_res_lib.Icon.util_mod_bif_to_mesh,
    )

    menu.add_menu_item(
        label="Copy/Paste Material",
        command=IMPORT_TOOL + 'initialize_tool("utility_options", "open_copy_paste_material_options")',
        tooltip="Opens a window with options to copy and paste materials.",
        icon=ui_res_lib.Icon.util_mod_copy_material,
    )
    # ------------------------------------ Rigging ------------------------------------
    menu.add_sub_menu("Rigging", icon=ui_res_lib.Icon.root_rigging, parent_to_root=True)
    menu.add_menu_item(
        label="Auto Rigger",
        command=IMPORT_TOOL + 'initialize_tool("auto_rigger")',
        tooltip="Opens auto rigger.",
        icon=ui_res_lib.Icon.tool_auto_rigger,
    )

    menu.add_divider()  # General Rigging Tools +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Add Offset Transform",
        command=IMPORT_TOOL + 'initialize_tool("add_offset_transform")',
        tooltip="Generates offset transforms that can be used as transform " "layers for rigging/animation.",
        icon=ui_res_lib.Icon.tool_add_inbetween,
    )
    menu.add_menu_item(
        label="Add Sine Attributes",
        command=IMPORT_TOOL + 'initialize_tool("sine_attributes")',
        tooltip="Create Sine function without using third-party plugins or expressions.",
        icon=ui_res_lib.Icon.tool_sine_attributes,
    )
    menu.add_menu_item(
        label="Connect Attributes",
        command=IMPORT_TOOL + 'initialize_tool("connect_attributes")',
        tooltip="Automated solution for connecting multiple attributes.",
        icon=ui_res_lib.Icon.tool_connect_attributes,
    )
    menu.add_menu_item(
        label="Create FK Driver",
        command=IMPORT_TOOL + 'initialize_tool("create_fk_driver")',
        tooltip="Creates FK controls and driver groups for selected joints.",
        icon=ui_res_lib.Icon.tool_create_fk,
    )
    menu.add_menu_item(
        label="Influences to Python",
        command=IMPORT_TOOL + 'initialize_tool("influences_to_python")',
        tooltip="Generate Python code used to select influence (bound) joints.",
        icon=ui_res_lib.Icon.tool_influence_joints,
    )
    menu.add_menu_item(
        label="Make IK Stretchy",
        command=IMPORT_TOOL + 'initialize_tool("make_ik_stretchy")',
        tooltip="Automated solution for making an IK system stretchy.",
        icon=ui_res_lib.Icon.tool_make_ik_stretchy,
    )
    menu.add_menu_item(
        label="Mirror Cluster Tool",
        command=IMPORT_TOOL + 'initialize_tool("mirror_cluster_tool")',
        tooltip="Automated solution for mirroring clusters.",
        icon=ui_res_lib.Icon.tool_mirror_cluster,
    )
    menu.add_menu_item(
        label="Morphing Attributes",
        command=IMPORT_TOOL + 'initialize_tool("morphing_attributes")',
        tooltip="Creates attributes to drive selected blend shapes.",
        icon=ui_res_lib.Icon.tool_morphing_attributes,
    )
    menu.add_menu_item(
        label="Morphing Utilities",
        command=IMPORT_TOOL + 'initialize_tool("morphing_utilities")',
        tooltip="Morphing utilities (Blend Shapes).",
        icon=ui_res_lib.Icon.tool_morphing_utils,
    )
    menu.add_menu_item(
        label="Orient Joints",
        command=IMPORT_TOOL + 'initialize_tool("orient_joints")',
        tooltip="Orients Joint in a more predictable way.",
        icon=ui_res_lib.Icon.tool_orient_joints,
    )
    menu.add_menu_item(
        label="Ribbon Tool",
        command=IMPORT_TOOL + 'initialize_tool("ribbon_tool")',
        tooltip="Create ribbon setups, using existing objects or by itself.",
        icon=ui_res_lib.Icon.tool_ribbon,
    )
    menu.add_divider(divider_label="Utilities")  # General Rigging Tools +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Rivet Locator",
        command=IMPORT_UTIL + 'initialize_utility("constraint", "create_rivet")',
        tooltip="Creates a rivet between two polygon edges or on a surface point",
        icon=ui_res_lib.Icon.util_rivet,
    )

    # ------------------------------------ Animation ------------------------------------
    menu.add_sub_menu("Animation", icon=ui_res_lib.Icon.root_animation, parent_to_root=True)
    menu.add_menu_item(
        label="Annotation Tracker",
        command=IMPORT_TOOL + 'initialize_tool("anim_annotation_tracker")',
        tooltip="Opens annotation tracker.",
        icon=ui_res_lib.Icon.tool_annotation_tracker,
    )
    menu.add_menu_item(
        label="Clip Tracker",
        command=IMPORT_TOOL + 'initialize_tool("anim_clip_tracker")',
        tooltip="Opens the animation clip tracker.",
        icon=ui_res_lib.Icon.tool_clip_tracker,
    )
    menu.add_menu_item(
        label="Copy/Paste Animation",
        command=IMPORT_TOOL + 'initialize_tool("anim_copy_paste")',
        tooltip="Copies persistent animation data with scoped keyframe support and character namespace mapping.",
        icon=ui_res_lib.Icon.tool_anim_copy_paste,
    )
    menu.add_menu_item(
        label="Create Testing Keys",
        command=IMPORT_TOOL + 'initialize_tool("create_testing_keys")',
        tooltip="Automated solution for creating testing keyframes.",
        icon=ui_res_lib.Icon.tool_testing_keys,
    )
    menu.add_menu_item(
        label="Offset Keyframes",
        command=IMPORT_TOOL + 'initialize_tool("offset_keyframes")',
        tooltip="Offsets selected animation timing and provides selection-order staggering.",
        icon=ui_res_lib.Icon.tool_offset_keyframes,
    )
    menu.add_menu_item(
        label="Retargeter",
        command=IMPORT_TOOL + 'initialize_tool("retargeter")',
        tooltip="Opens retargeter.",
        icon=ui_res_lib.Icon.tool_retargeter,
    )
    menu.add_menu_item(
        label="World Space Baker",
        command=IMPORT_TOOL + 'initialize_tool("world_space_baker")',
        tooltip="Extracts and bakes translate and rotate animation in world space.",
        icon=ui_res_lib.Icon.tool_world_space_baker,
    )

    # ------------------------------------ Miscellaneous ------------------------------------
    menu.add_sub_menu("Miscellaneous", icon=ui_res_lib.Icon.root_miscellaneous, parent_to_root=True)
    menu.add_menu_item(
        label="fSpy Importer",
        command=IMPORT_TOOL + 'initialize_tool("fspy_importer")',
        tooltip="Imports the JSON data exported out of fSpy (Camera Matching software).",
        icon=ui_res_lib.Icon.tool_fspy_importer,
    )
    menu.add_menu_item(
        label="Maya to Discord",
        command=IMPORT_TOOL + 'initialize_tool("maya_to_discord")',
        tooltip="Send images and videos (playblasts) from Maya to Discord using a "
        "Discord Webhook to bridge the two programs.",
        icon=ui_res_lib.Icon.tool_maya_to_discord,
    )
    menu.add_menu_item(
        label="Render Calculator",
        command=IMPORT_TOOL + 'initialize_tool("render_calculator")',
        tooltip="Helps calculate how long it's going to take to render an image sequence.",
        icon=ui_res_lib.Icon.tool_render_calculator,
    )
    menu.add_menu_item(
        label="Startup Booster",
        command=IMPORT_TOOL + 'initialize_tool("startup_booster")',
        tooltip="Improve startup times by managing which plugins get loaded when starting Maya.",
        icon=ui_res_lib.Icon.tool_startup_booster,
    )

    # ------------------------------------ Utilities ------------------------------------
    menu.add_sub_menu("Utilities", icon=ui_res_lib.Icon.root_utilities, parent_to_root=True)
    menu.add_menu_item(
        label="Reload File",
        command=IMPORT_UTIL + 'initialize_utility("scene", "force_reload_file")',
        tooltip="Forces the re-opening of an opened file. (Changes are ignored)",
        icon=ui_res_lib.Icon.util_reload_file,
        option_box=True,
        option_box_command=(
            IMPORT_TOOL + 'initialize_tool("utility_options", "open_reload_file_options")'
        ),
    )
    menu.add_menu_item(
        label="Open File Directory",
        command=IMPORT_UTIL + 'initialize_utility("scene", "open_file_dir")',
        tooltip="Opens the directory where the scene is located.",
        icon=ui_res_lib.Icon.util_open_dir,
    )

    menu.add_divider(divider_label="General Utilities")  # General +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Complete HUD Toggle",
        command=IMPORT_UTIL + 'initialize_utility("display", "toggle_full_hud")',
        tooltip="Toggles most of the Heads-Up Display (HUD) options according to the state of "
        "the majority of them. (Keeps default elements intact when toggling it off)",
        icon=ui_res_lib.Icon.util_hud_toggle,
    )
    menu.add_menu_item(
        label="Select Non-Unique Objects",
        command=IMPORT_UTIL + 'initialize_utility("selection", "select_non_unique_objects")',
        tooltip="Selects all objects with the same short name. (non-unique objects)",
        icon=ui_res_lib.Icon.util_sel_non_unique,
    )
    menu.add_menu_item(
        label="Set Joint Name as Label",
        command=IMPORT_UTIL + 'initialize_utility("display", "set_joint_name_as_label")',
        tooltip="Set the label of the selected joints to be the same as their short name.",
        icon=ui_res_lib.Icon.util_joint_to_label,
    )
    menu.add_menu_item(
        label="Unhide Default Channels",
        command=IMPORT_UTIL + 'initialize_utility("attr", ' '"selection_unhide_default_channels")',
        tooltip="Un-hides the default channels of the selected objects. "
        "(Default channels : Translate, Rotate, Scale and Visibility)",
        icon=ui_res_lib.Icon.util_unhide_trs,
    )
    menu.add_menu_item(
        label="Uniform Joint Label Toggle",
        command=IMPORT_UTIL + 'initialize_utility("display", "toggle_uniform_jnt_label")',
        tooltip="Makes the visibility of the joint labels uniform according to the current "
        "state of the majority of them.",
        icon=ui_res_lib.Icon.util_joint_label_toggle,
    )
    menu.add_menu_item(
        label="Uniform LRA Toggle",
        command=IMPORT_UTIL + 'initialize_utility("display", "toggle_uniform_lra")',
        tooltip="Makes the visibility of the Local Rotation Axis uniform among the selected "
        "objects according to the current state of the majority of them.",
        icon=ui_res_lib.Icon.util_lra_toggle,
    )
    menu.add_menu_item(
        label="Unlock Default Channels",
        command=IMPORT_UTIL + 'initialize_utility("attr", ' '"selection_unlock_default_channels")',
        tooltip="Unlocks the default channels of the selected objects. "
        "(Default channels : Translate, Rotate, Scale and Visibility)",
        icon=ui_res_lib.Icon.util_unlock_trs,
    )

    menu.add_divider(divider_label="Convert Utilities")  # Convert Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Convert Joints to Mesh",
        command=IMPORT_UTIL + 'initialize_utility("joint", "convert_joints_to_mesh")',
        tooltip="Converts joints to mesh. (Helpful when sending references to other applications)",
        icon=ui_res_lib.Icon.util_convert_joint_mesh,
    )
    menu.add_menu_item(
        label="Convert to Locators",
        command=IMPORT_UTIL + 'initialize_utility("transform", "convert_transforms_to_locators")',
        tooltip="Converts transforms to locators. Function doesn't affect selected objects.",
        icon=ui_res_lib.Icon.util_convert_loc,
    )

    menu.add_divider(divider_label="Reference Utilities")  # References Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Import References",
        command=IMPORT_UTIL + 'initialize_utility("reference", "references_import")',
        tooltip="Imports all references.",
        icon=ui_res_lib.Icon.util_ref_import,
    )
    menu.add_menu_item(
        label="Remove References",
        command=IMPORT_UTIL + 'initialize_utility("reference", "references_remove")',
        tooltip="Removes all references.",
        icon=ui_res_lib.Icon.util_ref_remove,
    )

    menu.add_divider(divider_label="Pivot Utilities")  # Pivot Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Move Object to Origin",
        command=IMPORT_UTIL + 'initialize_utility("transform", "move_selection_to_origin")',
        tooltip="Moves selected objects to origin according to their pivot point.",
        icon=ui_res_lib.Icon.util_move_origin,
    )
    menu.add_menu_item(
        label="Move Pivot to Base",
        command=IMPORT_UTIL + 'initialize_utility("transform", "move_pivot_base")',
        tooltip="Moves pivot point to the base of the bounding box of every selected object.",
        icon=ui_res_lib.Icon.util_pivot_bottom,
        option_box=True,
        option_box_command=IMPORT_TOOL + 'initialize_tool("utility_options", "open_move_pivot_base_options")',
    )
    menu.add_menu_item(
        label="Move Pivot to Top",
        command=IMPORT_UTIL + 'initialize_utility("transform", "move_pivot_top")',
        tooltip="Moves pivot point to the top of the bounding box of every selected object.",
        icon=ui_res_lib.Icon.util_pivot_top,
        option_box=True,
        option_box_command=IMPORT_TOOL + 'initialize_tool("utility_options", "open_move_pivot_top_options")',
    )

    menu.add_divider(divider_label="Reset Utilities")  # Reset Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Reset Joints Display",
        command=IMPORT_UTIL + 'initialize_utility("display", "reset_joint_display")',
        tooltip="Resets the radius attribute back to one in all joints, then changes the global "
        "multiplier (jointDisplayScale) back to one.",
        icon=ui_res_lib.Icon.util_reset_jnt_display,
    )
    menu.add_menu_item(
        label='Reset "persp" Camera',
        command=IMPORT_UTIL + 'initialize_utility("camera", "reset_persp_shape_attributes")',
        tooltip="If persp camera exists (default camera), reset its attributes.",
        icon=ui_res_lib.Icon.util_reset_persp,
    )
    menu.add_menu_item(
        label="Reset Transforms",
        command=IMPORT_UTIL + 'initialize_utility("transform", "reset_transforms")',
        tooltip="Reset transforms. It checks for incoming connections, then set the attribute to 0 "
        "if there are none. Currently affects Joints, meshes and transforms. (Only Rotation)",
        icon=ui_res_lib.Icon.util_reset_transforms,
    )

    menu.add_divider(divider_label="Delete Utilities")  # Delete Section +++++++++++++++++++++++++++++++++
    menu.add_menu_item(
        label="Delete Custom Attributes",
        command=IMPORT_UTIL + 'initialize_utility("attr", ' '"selection_delete_user_defined_attrs")',
        tooltip="Deletes user-defined (custom) attributes found on the selected objects.",
        icon=ui_res_lib.Icon.util_delete_custom_attr,
    )
    menu.add_menu_item(
        label="Delete Namespaces",
        command=IMPORT_UTIL + 'initialize_utility("namespace", "delete_namespaces")',
        tooltip="Deletes all namespaces in the scene.",
        icon=ui_res_lib.Icon.util_delete_ns,
    )
    menu.add_menu_item(
        label="Delete Display Layers",
        command=IMPORT_UTIL + 'initialize_utility("display", "delete_display_layers")',
        tooltip="Deletes all display layers.",
        icon=ui_res_lib.Icon.util_delete_display_layers,
    )
    menu.add_menu_item(
        label="Delete Unused Nodes",
        command=IMPORT_UTIL + 'initialize_utility("cleanup", "delete_unused_nodes")',
        tooltip="Deletes unused nodes.",
        icon=ui_res_lib.Icon.util_delete_unused_nodes,
    )
    menu.add_menu_item(
        label="Delete Nucleus Nodes",
        command=IMPORT_UTIL + 'initialize_utility("cleanup", "delete_nucleus_nodes")',
        tooltip="Deletes all nodes related to particles. " "(Nucleus, nHair, nCloth, nConstraints, Emitter, etc...)",
        icon=ui_res_lib.Icon.util_delete_nucleus_nodes,
    )
    menu.add_menu_item(
        label="Delete Keyframes",
        command=IMPORT_UTIL + 'initialize_utility("anim", "delete_time_keyframes")',
        tooltip='Deletes all nodes of the type "animCurveTA" (keyframes).',
        icon=ui_res_lib.Icon.util_delete_keyframes,
        option_box=True,
        option_box_command=IMPORT_TOOL + 'initialize_tool("utility_options", "open_delete_keyframes_options")',
    )

    # ------------------------------------ Legacy ------------------------------------
    package_prefs = PackagePrefs()
    if package_prefs.is_legacy_menu_visible():
        menu.add_sub_menu("Legacy", icon=ui_res_lib.Icon.root_rigging, parent_to_root=True)
        menu.add_divider(parent="Legacy", divider_label="General")
        menu.add_menu_item(
            label="Render Checklist",
            command=IMPORT_TOOL + 'initialize_tool("legacy_render_checklist")',
            tooltip="Performs a series of checks to detect common issues that are often accidentally "
            "ignored/unnoticed.",
            icon=ui_res_lib.Icon.tool_render_checklist,
        )
        menu.add_divider(parent="Legacy", divider_label="Rigging")
        menu.add_menu_item(
            label="Biped Auto Rigger",
            command=IMPORT_TOOL + 'initialize_tool("legacy_biped_rigger")',
            tooltip="Automated solution for creating a legacy biped rig.",
            icon=ui_res_lib.Icon.tool_auto_rigger_legacy,
        )
        menu.add_menu_item(
            label="Biped Rig Interface",
            command=IMPORT_TOOL + 'initialize_tool("legacy_biped_rigger", "launch_biped_rig_interface")',
            tooltip="Rig interface for the legacy Biped Auto Rigger.",
            icon=ui_res_lib.Icon.tool_rig_interface,
        )
        menu.add_divider(parent="Legacy", divider_label="Animation")
        menu.add_menu_item(
            label="Game FBX Exporter",
            command=IMPORT_TOOL + 'initialize_tool("legacy_biped_rigger", "launch_game_exporter")',
            tooltip="Exports legacy biped rigs for real-time use as FBX files.",
            icon=ui_res_lib.Icon.tool_game_fbx_exporter,
        )
        menu.add_menu_item(
            label="Retarget Assistant",
            command=IMPORT_TOOL + 'initialize_tool("legacy_biped_rigger", "launch_retarget_assistant")',
            tooltip="HumanIK retargeting assistant for legacy biped rigs.",
            icon=ui_res_lib.Icon.tool_retarget_assistant,
        )
    # ------------------------------------ Development ------------------------------------
    if package_prefs.is_dev_menu_visible():
        menu.add_sub_menu("Develop", icon=ui_res_lib.Icon.root_dev, parent_to_root=True)
        menu.add_menu_item(
            label="Resource Library",
            command=IMPORT_TOOL + 'initialize_tool("resource_library")',
            tooltip="Opens Resource Library tool." "Library with colors, package icons and Maya icons.",
            icon=ui_res_lib.Icon.tool_resource_library,
        )
        menu.add_menu_item(
            label="Sample Tool",
            command=IMPORT_TOOL + 'initialize_tool("sample_tool")',
            tooltip="Opens sample tool.",
            icon=ui_res_lib.Icon.dev_screwdriver,
        )
        menu.add_divider(divider_label="Curves")  # Curve Thumbnails Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(
            label="Add Thumbnail Metadata to Selection",
            command="from gt.core.curve import add_thumbnail_metadata_attr_to_selection\n"
            "add_thumbnail_metadata_attr_to_selection()\n",
            tooltip="Add thumbnail metadata attributes to selection.",
            icon=ui_res_lib.Icon.dev_filter,
        )
        menu.add_menu_item(
            label="Get Package CRV files to Python",
            command="from gt.core.curve import print_code_for_crv_files\n"
            "print_code_for_crv_files(use_output_window=True)\n",
            tooltip='Get Python Lines used to call curves from "Curves" class.',
            icon=ui_res_lib.Icon.dev_binary,
        )
        menu.add_menu_item(
            label="Render Package Curves Thumbnails",
            command="from gt.core.curve import generate_package_curves_thumbnails\n"
            "generate_package_curves_thumbnails()\n",
            tooltip="Render thumbnails for the package curves to a desktop folder.",
            icon=ui_res_lib.Icon.dev_picker,
        )
        menu.add_menu_item(
            label="Write Curve Files from Selection",
            command="from gt.core.curve import write_curve_files_from_selection\n"
            "write_curve_files_from_selection()\n",
            tooltip="Write curve data attributes to a desktop folder.",
            icon=ui_res_lib.Icon.dev_binary,
        )
        menu.add_divider(divider_label="General")  # Misc Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(
            label="Get Loaded Package Location",
            command="from gt.core.session import get_module_path\n"
            "from gt.utils.system import open_file_dir\n"
            'open_file_dir(get_module_path(module_name="gt", verbose=True))\n',
            tooltip="Gets the loaded package path location.",
            icon=ui_res_lib.Icon.dev_code,
        )
        menu.add_menu_item(
            label="Silently Check for Updates",
            command=IMPORT_TOOL + 'initialize_tool("package_updater", "silently_check_for_updates")',
            tooltip="Silently checks for updates.",
            icon=ui_res_lib.Icon.dev_git_pull_request,
        )
        menu.add_menu_item(
            label="Take Viewport Snapshot",
            command="from gt.utils.system import get_desktop_path, get_formatted_time\n"
            "from gt.core.playblast import render_viewport_snapshot\nimport sys\n"
            "file_path = render_viewport_snapshot(get_formatted_time(format_str="
            '"Snapshot %Y-%m-%d %H%M%S"), get_desktop_path())\nif file_path:\n\t'
            "sys.stdout.write(f'\\nSnapshot written to: \"{file_path}\"')",
            tooltip="Saves a viewport snapshot to the desktop.",
            icon=ui_res_lib.Icon.dev_picker,
        )
        menu.add_divider(divider_label="Dangerous")  # Misc Section +++++++++++++++++++++++++++++++++
        menu.add_menu_item(
            label="Purge Package Settings",
            command="from gt.core.prefs import purge_package_settings\n" "purge_package_settings()\n",
            tooltip="Opens sample tool.",
            icon=ui_res_lib.Icon.dev_trash,
        )
        menu.add_menu_item(
            label="Skip Menu Creation Toggle",
            command="from gt.core.prefs import toggle_skip_menu_creation\n" "toggle_skip_menu_creation()\n",
            tooltip="Opens sample tool.",
            icon=ui_res_lib.Icon.dev_code,
        )
    # ------------------------------------ Settings / Help ------------------------------------
    menu.add_divider(parent_to_root=True)
    _rebuild_menu_command = (
        "from gt.tools.package_setup.gt_tools_maya_menu import _rebuild_menu\n"
        "from gt.utils.system import execute_deferred\n"
        "execute_deferred(_rebuild_menu)"
    )
    menu.add_sub_menu("Settings", icon=ui_res_lib.Icon.root_dev, parent_to_root=True)
    menu.add_menu_item(
        label="Automatic Dependency Installation",
        command="from gt.core.prefs import toggle_dependency_auto_install\n"
        "toggle_dependency_auto_install()\n"
        + _rebuild_menu_command,
        tooltip="Automatically installs missing Python packages for tools that request them.",
        icon=ui_res_lib.Icon.ui_progress,
        check_box=is_auto_install_enabled(),
        parent="Settings",
    )
    menu.add_menu_item(
        label="Show Develop Menu",
        command="from gt.core.prefs import toggle_dev_sub_menu\n" "toggle_dev_sub_menu()\n" + _rebuild_menu_command,
        tooltip="Shows or hides the development tools menu.",
        icon=ui_res_lib.Icon.root_dev,
        check_box=package_prefs.is_dev_menu_visible(),
        parent="Settings",
    )
    menu.add_menu_item(
        label="Show Legacy Menu",
        command="from gt.core.prefs import toggle_legacy_sub_menu\n"
        "toggle_legacy_sub_menu()\n"
        + _rebuild_menu_command,
        tooltip="Shows or hides the legacy tools menu.",
        icon=ui_res_lib.Icon.root_rigging,
        check_box=package_prefs.is_legacy_menu_visible(),
        parent="Settings",
    )
    menu.add_sub_menu("Help", icon=ui_res_lib.Icon.root_help, parent_to_root=True)
    menu.add_menu_item(
        label="About",
        command=IMPORT_TOOL + 'initialize_tool("package_setup", "open_about_window")',
        tooltip="Opens about menu.",
        icon=ui_res_lib.Icon.misc_about,
        parent="Help",
    )
    menu.add_menu_item(
        label="Re-Build Menu",
        command=_rebuild_menu_command,
        tooltip="Re-Creates this menu, and does a rehash to pick up any new scripts.",
        icon=ui_res_lib.Icon.misc_rebuild_menu,
        parent="Help",
    )
    menu.add_menu_item(
        label="Check for Updates",
        command=IMPORT_TOOL + 'initialize_tool("package_updater")',
        tooltip="Check for updates by comparing current version with latest release.",
        icon=ui_res_lib.Icon.tool_package_updater,
        parent="Help",
    )
    menu.add_menu_item(
        label=f"Installed Version: {str(package_version)}",
        enable=False,
        icon=ui_res_lib.Icon.misc_current_version,
        parent="Help",
    )
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
