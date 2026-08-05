"""
Auto Rigger Collections Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.naming as core_naming
import gt.core.logger as core_log
import gt.core.attr as core_attr
import maya.cmds as cmds
import logging
import json


# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


class ModuleCollections(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_collections
    allow_parenting = True
    allow_multiple = False

    def __init__(self, name="Collections", prefix=None, suffix=None):
        """
        Initializes the Collections module.

        Args:
            name (str, optional): The module name.
            prefix (str, optional): Prefix string for naming. Defaults to None.
            suffix (str, optional): Suffix string for naming. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self.setup_collections, order=tools_rig_frm.CodeData.Order.post_build)

        # Collection Data
        self.collection_dicts = []  # {"name": ["objOne", "objTwo"]}
        self.collection_expressions = []
        # Cache
        self._cached_collections_dict = None

    def setup_collections(self):
        """Creates a collection attribute and populates it with the set data."""
        self._cached_collections_dict = None
        root_group = tools_rig_utils.find_root_group_rig()

        # Add Collections Attribute
        attr_collections = tools_rig_const.RiggerConstants.ATTR_RIG_COLLECTIONS
        if not cmds.objExists(f"{root_group}.{attr_collections}"):
            core_attr.add_attr(
                obj_list=root_group,
                attr_type="string",
                is_keyable=False,
                attributes=attr_collections,
            )

        # Merge Collections:
        merged_dict = {}
        for collection_dict in self.collection_dicts:
            for key, value in collection_dict.items():
                if key in merged_dict:
                    logger.warning(f"Key '{key}' already exists — overwriting {merged_dict[key]!r} with {value!r}")
                merged_dict[key] = value

        # Store Collections
        json_data = json.dumps(merged_dict)
        self._cached_collections_dict = merged_dict
        core_attr.set_attr(f"{root_group}.{attr_collections}", json_data)

        # Handle Expressions
        self.process_expressions()

    def process_expressions(self):
        """
        Processes all defined query expressions and updates the collections attribute with the found elements.

        This function handles two types of queries: Maya search (cmds.ls) and
        Collection search (rig_utils.filter_by_collection).
        """
        if not self.collection_expressions:
            return

        # 1. Resolve Maya Search Queries (is_collection_query = False)
        for expression_data in self.collection_expressions:
            collection_name = expression_data["name"]
            expression = expression_data["expression"].strip()
            is_collection_query = expression_data["is_collection_query"]
            is_joints_only = expression_data.get("is_joints_only", True)

            if not expression:
                logger.warning(
                    f"Collection '{collection_name}' is set to query mode but has an empty expression. Skipping."
                )
                continue

            # --- Maya Search Query (cmds.ls) ---
            if not is_collection_query:
                # Use Maya commands to find elements based on the expression
                found_elements = cmds.ls(expression, recursive=True, type=["transform", "joint", "mesh"])

                if found_elements:
                    self._cached_collections_dict[collection_name] = found_elements
                else:
                    logger.warning(f"Maya expression '{expression}' for '{collection_name}' returned no elements.")

            # --- Collection Search Query (rig_utils) ---
            else:
                try:
                    # Get rig metadata needed for collection filtering
                    scene_rigs_metadata = tools_rig_utils.get_rigs_metadata()

                    if not scene_rigs_metadata:
                        logger.warning(
                            f"Collection search for '{collection_name}' failed: No rig metadata found in scene."
                        )
                        continue

                    # Grab the first available rig (assuming one rig build per scene for simplicity)
                    rig_uuid, rig_metadata = next(iter(scene_rigs_metadata.items()))

                    # Use the utility function to filter elements based on the expression
                    if is_joints_only:
                        found_elements = tools_rig_utils.filter_rig_joints_by_collection(
                            rig_metadata=rig_metadata, filter_query=expression
                        )
                    else:
                        found_elements = tools_rig_utils.filter_by_collection(
                            rig_metadata=rig_metadata, filter_query=expression
                        )

                    if found_elements:
                        # Update the cached collections with the results of the expression
                        short_names = [core_naming.get_short_name(item) for item in found_elements]
                        self._cached_collections_dict[collection_name] = short_names
                    else:
                        logger.warning(
                            f"Collection expression '{expression}' for '{collection_name}' returned no elements."
                        )

                except Exception as error:
                    logger.error(
                        f"Failed to process collection expression for"
                        f" '{collection_name}' with expression '{expression}': {error}"
                    )

        # Store New Data
        root_group = tools_rig_utils.find_root_group_rig()
        json_data = json.dumps(self._cached_collections_dict)
        attr_collections = tools_rig_const.RiggerConstants.ATTR_RIG_COLLECTIONS
        core_attr.set_attr(f"{root_group}.{attr_collections}", json_data)

    @staticmethod
    def clear_collections():
        """Clears the collection data in case the attribute is present."""
        root_group = tools_rig_utils.find_root_group_rig()

        # Add Collections Attribute
        attr_collections = tools_rig_const.RiggerConstants.ATTR_RIG_COLLECTIONS
        if not cmds.objExists(f"{root_group}.{attr_collections}"):
            logger.warning(f"No collections attribute detected in the scene. Unable to clear data.")
            return

        # Clear Collections
        core_attr.set_attr(f"{root_group}.{attr_collections}", "")
        logger.info(f'Collections data was cleared from "root_group".')


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric
    import gt.tools.auto_rigger.rig_modules as tools_rig_mods

    # Create Test Modules ---------------------------------------------------------------------------------
    a_generic_module = ModuleGeneric()
    a_new_scene_module = tools_rig_mods.RigModules.Utils.ModuleNewScene()
    a_collections_module = ModuleCollections()

    # Test File Paths -------------------------------------------------------------------------------------
    import gt.tests.test_auto_rigger as test_auto_rigger
    import inspect
    import os

    module_path = inspect.getfile(test_auto_rigger)
    module_dir = os.path.dirname(module_path)
    a_cube_obj = os.path.join(module_dir, "data", "cylinder_project", "cylinder.obj")
    a_cube_fbx = os.path.join(module_dir, "data", "cylinder_project", "cylinder.fbx")

    # Configure Modules -----------------------------------------------------------------------------------
    p1 = a_generic_module.add_new_proxy()
    p2 = a_generic_module.add_new_proxy()
    p3 = a_generic_module.add_new_proxy()
    p1.set_name("first")
    p2.set_name("second")
    p3.set_name("third")
    p2.set_initial_position(y=15)
    p3.set_initial_position(y=30)
    p2.set_parent_uuid(p1.get_uuid())
    p3.set_parent_uuid(p2.get_uuid())
    p1.set_locator_scale(6)
    p2.set_locator_scale(5)
    p3.set_locator_scale(4)

    # Create Project and Build ----------------------------------------------------------------------------
    a_project = RigProject()
    a_project.add_to_modules(a_new_scene_module)
    a_project.add_to_modules(a_collections_module)

    a_collections_module.collection_dicts = [{"name": ["objOne", "objTwo"]}, {"name2": ["objOne", "objTwo"]}]

    # # Creates new scene after building resulting in empty scene
    a_project.build_proxy()
    a_project.build_rig()

    # Frame all
    cmds.viewFit(all=True)
