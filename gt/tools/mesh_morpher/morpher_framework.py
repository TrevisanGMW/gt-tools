"""
 Mesh Morpher Framework

Import Line:
    import gt.tools.mesh_morpher.morpher_framework as tools_morpher_frm
"""

import gt.tools.mesh_morpher.morpher_constants as tools_morpher_const
import gt.ui.file_dialog as ui_file_dialog
import gt.core.feedback as core_fback
import gt.core.naming as core_naming
import gt.core.uuid as core_uuid
import gt.core.rbf as core_rbf
import gt.core.str as core_str
import gt.core.io as core_io
import maya.cmds as cmds
import datetime
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MorpherAddon:
    allow_multiple = True  # If only one is allowed, a definition will reject new items of the same type.

    class Order:
        """
        List of recognized/accepted order to apply
        """

        pre_morph = "pre_morph"  # Before anything is done in the scene
        post_morph = "post_morph"  # After reshaping/morphing mesh

    def __init__(self, name="Generic Addon"):
        """
        Initiates a MorpherAddon object.
        This is similar to a module.
        Args:
            name (str): The name of the addon. Defaults to "Generic Addon".
        """
        self.addon = self.__class__.__name__
        self.name = name
        self.execution_order = MorpherAddon.Order.post_morph  # Default happens after reshaping object.
        # Common Data
        self._definition = None  # The definition itself case anything needs to be references.
        self._subject_mesh = None
        self._reshaped_mesh = None  # Mesh generated after the post process

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_definition(self, definition):
        """
        Setter used to update common addon data. This is a reference to the definition.
        Args:
            definition (str): Subject mesh name/path
        """
        self._definition = definition

    def set_subject_mesh(self, subject_mesh):
        """
        Setter used to update common addon data. This is automatically updated from the definition.
        Args:
            subject_mesh (str): Subject mesh name/path
        """
        self._subject_mesh = subject_mesh

    def set_reshaped_mesh(self, reshaped_mesh):
        """
        Setter used to update common addon data. This is automatically updated from the definition.
        Args:
            reshaped_mesh (str): Reshaped mesh name/path (result of the RBF operation)
        """
        self._reshaped_mesh = reshaped_mesh

    def set_execution_order(self, order):
        """
        Sets the execution order for this addon.
        This determines when this addon is executed during the reshape process.
        Args:
            order: An order string found inside of this MorpherAddon object. (e.g. MorpherAddon.Order)
        """
        self.execution_order = order

    def set_addon_from_dict(self, addon_dict):
        """
        Modifies this object to match the data received. (Used to export and import as JSON)
        Args:
            addon_dict (dict): A dictionary where keys are the variable names and values are the variable values.
                             e.g. {'execution_order': 'pre_morph'}
        """
        for key, value in addon_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_definition(self):
        """
        Gets the parent definition for this addon.
        Returns:
            MorpherDefinition: Parent definition.
        """
        return self._definition

    def get_class_name(self):
        """
        Gets the class name (type) for this addon.
        Returns:
            str: The name of the addon class.
        """
        return self.addon

    def get_execution_order(self):
        """
        Gets the current execution order for this addon.
        Returns:
            str: Execution order string. Used to determine when this code will be executed during the reshape process.
        """
        return self.execution_order

    def get_addon_as_dict(self):
        """
        Gets all serializable variables as a dictionary.
        Returns:
            dict: A dictionary describing all variables listed on this addon object.
        """
        _result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if core_io.is_json_serializable(data=value, allow_none=False):
                    _result[key] = value
        return _result

    def apply_addon_ordered(self, required_order, *args, **kwargs):
        """
        Tries to run the code defined in the addon.
        Args:
            required_order (str): If provided, it becomes a requirement for the function to run.
        Return:
            any: Result received from the addon.
        """
        if self.execution_order == required_order:
            return self.apply_addon(*args, **kwargs)

    # -------------------------------------------------- Misc --------------------------------------------------
    @staticmethod
    def get_packed_vertices(mesh_name=None):
        """
        Returns a list of selected vertex indices formatted in a compact range notation.
        Args:
            mesh_name (str, optional): If not provided, selection is used. If provided, all vertices are returned.
        Returns:
            list: A list of vertex ranges or individual indices as strings.
        """
        if mesh_name and cmds.objExists(mesh_name):
            cmds.select(f"{mesh_name}.vtx[*]")
        selection = cmds.ls(selection=True, flatten=True)

        vertex_indices = []

        for sel in selection:
            if ".vtx[" in sel:
                vtx_index = int(sel.split(".vtx[")[1][:-1])  # Extract vertex index
                vertex_indices.append(vtx_index)

        if not vertex_indices:
            return []

        def format_ranges(indices):
            """
            Formats a list of integers into a concise range string.

            Converts consecutive numbers into a range (e.g. [1:3]) and isolated numbers
            into individual entries (e.g. [5]).

            Example:
                [1, 2, 3, 5, 6, 8] → "[1:3], [5:6], [8]"

            Args:
                indices (list[int]): List of integer indices.

            Returns:
                str: Formatted string with ranges.
            """
            indices.sort()
            ranges = []
            start = end = indices[0]

            for i in indices[1:]:
                if i == end + 1:
                    end = i
                else:
                    ranges.append(f"[{start}:{end}]" if start != end else f"[{start}]")
                    start = end = i

            ranges.append(f"[{start}:{end}]" if start != end else f"[{start}]")
            return ", ".join(ranges)

        return format_ranges(vertex_indices)

    @staticmethod
    def unpack_vertices(mesh_name, vertices_string):
        """
        Unpack vertices from simplified strings to full names read for selection.
        Args:
            mesh_name (str): Mesh containing the vertices
            vertices_string (str): A string with the vertices to unpack. e.g. "[0:23], [87:196], [255:370]"

        Returns:
            list: A list of vertices ready for selection. e.g. ['obj.vtx[0:23]', 'obj.vtx[87:196]'...]
        """
        vertices_list = vertices_string.split(", ")
        if not vertices_list:
            return []
        obj_vtx_list = []
        for vtx in vertices_list:
            obj_vtx_list.append(f"{mesh_name}.vtx{vtx}")
        return obj_vtx_list

    # -------------------------------------------------- Core --------------------------------------------------
    def apply_addon(self, *args, **kwargs):
        """
        Applies the changes defined by this addon.
        This function is overwritten by each addon to behave in whatever way it should behave.
        Args:
            *args: Any arguments necessary for this addon to run.
            **kwargs: Any key arguments necessary for this addon to run.

        Returns:
            any: The result depends on what the extended addon defined as a return value.
        """
        logger.debug(f'Addon "{self.name}" was applied.')


class MorpherDefinition:
    """
    Represents the definition (project) of the Mesh Morpher process.
    """

    def __init__(self):
        """
        Initializes the MorpherDefinition object with default values.
        """
        # UUID to identify MorpherDefinition definition
        self.uuid = core_uuid.generate_uuid(short=True, short_length=12)

        # Basic Data
        self.subject_mesh = ""
        self.rbf_data_paths = []
        # Other Preferences
        self.keep_original_mesh = True
        # Environment variable data
        self._latest_cache_name = ""

        # Create Addons
        import gt.tools.mesh_morpher.morpher_addons as tools_morph_addons  # Here to avoid circular import

        # Main Elements (Addons and Links)
        self.addons = [
            tools_morph_addons.Addons.DeltaMush(),
            tools_morph_addons.Addons.Masking(),
            tools_morph_addons.Addons.Anchor(),
            tools_morph_addons.Addons.Renaming(),
        ]

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_uuid(self, uuid):
        """
        Sets the UUID of the MorpherDefinition.

        Args:
            uuid (str): The unique identifier for the MorpherDefinition definition.
        """
        self.uuid = uuid

    def set_subject_mesh(self, subject_mesh):
        """
        Sets the subject mesh name/path.

        Args:
            subject_mesh (str): The path to the subject mesh/path.
        """
        self.subject_mesh = subject_mesh

    def set_rbf_data_paths(self, rbf_data_paths):
        """
        Sets the list of RBF data paths. These are paths to data files exported using "export_rbf_data_file()"

        Args:
            rbf_data_paths (List[str]): The list of paths used to reshape the subject mesh.
                                        e.g. ["R:/file_a.json", "R:/file_b.json"]
        """
        self.rbf_data_paths = rbf_data_paths

    def clear_rbf_data_paths(self):
        """
        Clears the stored rbf data paths back to an empty list.
        """
        self.rbf_data_paths = []

    def read_data_from_dict(self, definition_dict):
        """
        Modifies this definition to match the data received. (Used to export and import preferences)
        Args:
            definition_dict (dict): A dictionary with definition keys and values.
                             e.g. {'source': 'base_jnt', 'target': 'base_ctrl', 'method': 'position_rotation'}
        """
        addons_key = "addons"
        keys_to_skip = [addons_key]
        for key, value in definition_dict.items():
            if hasattr(self, key) and key not in keys_to_skip:
                setattr(self, key, value)

        # Addons -----------------------------------------
        _serialized_addons = definition_dict.get(addons_key)
        new_addons = []
        import gt.tools.mesh_morpher.morpher_addons as tools_morpher_addons

        available_addons = tools_morpher_addons.Addons.get_addons_dict()
        for addon_data in _serialized_addons:
            addon_class = addon_data.get("addon")
            if addon_class not in available_addons:
                logger.warning(f'Unable to read unknown addon: "{addon_class}".')
                continue
            new_addon = _module = available_addons.get(addon_class)()
            new_addon.set_addon_from_dict(addon_data)
            new_addons.append(new_addon)
        self.addons = new_addons

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_uuid(self):
        """
        Gets the UUID of the MorpherDefinition.

        Returns:
            str: The unique identifier of the MorpherDefinition definition.
        """
        return self.uuid

    def get_subject_mesh(self):
        """
        Gets the name/path to the subject mesh. That is the mesh affected by the process.
        The tool uses the data calculated from source to target to reshape the subject mesh.

        Returns:
            str: The name/path to the subject mesh.
        """
        return self.subject_mesh

    def get_rbf_data_paths(self):
        """
        Gets the list of RBF paths to be used with this definition.

        Returns:
            list: A list of paths. e.g. ["R:/file_a", "R:/file_b"]
        """
        return self.rbf_data_paths

    def get_addons(self, filter_type=None):
        """
        Gets the list of targeting addons.

        Args:
            filter_type (str): Name of the type of addons to retrieve. Can be used to easily retrieve unique addons.

        Returns:
            list: A list of TargetingAddons objects.
        """
        if filter_type is None:
            return self.addons
        found_addons = []
        for addon in self.addons:
            class_name = addon.get_class_name()
            if class_name == filter_type:
                found_addons.append(addon)
        return found_addons

    def get_definition_as_dict(self):
        """
        Gets definition as a JSON ready dictionary.
        Returns:
            dict: A dictionary describing this definition.
        """
        # Ordered Basic Variables
        definition_as_dict = {
            "uuid": self.get_uuid(),
            "subject_mesh": self.get_subject_mesh(),
            "rbf_data_paths": self.get_rbf_data_paths(),
        }

        # Remaining Variables (Auto Serialization)
        for key, value in self.__dict__.items():
            if not key.startswith("_") and key not in definition_as_dict.keys():
                if core_io.is_json_serializable(data=value, allow_none=False):
                    definition_as_dict[key] = value

        # Addons
        addons_as_dict = []
        for addon in self.addons:
            addons_as_dict.append(addon.get_addon_as_dict())
        definition_as_dict["addons"] = addons_as_dict
        return definition_as_dict

    # -------------------------------------------------- Misc --------------------------------------------------
    def add_addon(self, addon):
        """
        Adds a TargetingLink to the list of links.

        Args:
            addon (MorpherAddon): The link to be added.
        """
        found_addon_types = [addon.get_class_name() for addon in self.get_addons()]

        if not addon.allow_multiple and addon.get_class_name() in found_addon_types:
            logger.warning(
                f"Unable to add addon as multiples of this type are not allowed. "
                f"Rejected addon: {addon.get_class_name()}"
            )
            return
        self.addons.append(addon)

    def apply_addons(self, required_order):
        """
        Tries to run any addon that matches the required order.
        Args:
            required_order (str, None): If provided, the code will only run when matching the provided order
            according to the CodeData object.
        """
        for addon in self.addons:
            addon.apply_addon_ordered(required_order=required_order)

    def refresh_addons_data(self):
        """Populates addons with shared data such as source and target names"""
        for addon in self.addons:
            addon.set_definition(self)
            addon.set_subject_mesh(self.subject_mesh)

    def refresh_addons_reshaped_data(self, reshaped_mesh):
        """
        Populates addons with the result mesh path/name
        Args:
            reshaped_mesh (str): Name/path to the reshaped mesh (result of the RBF operation)
        """
        for addon in self.addons:
            addon.set_reshaped_mesh(reshaped_mesh)

    @staticmethod
    def export_rbf_data_file():
        """
        Caches RBF morph data from source to target.
        And exports as a file. Used to create potential variations, one definition might use many of this.
        """
        # Source + Target Selection
        selection = cmds.ls(selection=True)
        if len(selection) < 2:
            cmds.warning("Please select the source mesh and target mesh (in this order) and try again.")
            return
        _source_mesh = selection[0]
        _target_mesh = selection[1]

        # File Path
        file_path = ui_file_dialog.file_dialog(
            write_mode=True,
            starting_directory=tools_morpher_const.MeshMorpherConstants.DEFAULT_RBF_CACHE_FOLDER,
            file_filter=tools_morpher_const.MeshMorpherConstants.DATA_FILTER,
            ok_caption="Export RBF Cache",
            cancel_caption="Cancel",
        )
        if not file_path:
            return  # Cancel operation

        # Export RBF Data
        logging.info(f"Calculating RBF cache data...")
        try:
            rbf_data = core_rbf.get_source_and_weights_arrays(source_mesh=_source_mesh, target_mesh=_target_mesh)
            if rbf_data and isinstance(rbf_data, tuple) and len(rbf_data) == 2:
                _data_dict = {
                    "source_array": rbf_data[0],
                    "weights_array": rbf_data[1],
                    "timestamp": datetime.datetime.now().isoformat(),
                }

                core_io.write_json(path=file_path, data=_data_dict)
                logging.info(f"RBF cache data exported to: {file_path}")
            else:
                raise Exception("Unexpected data type returned from caching operation.")
        except Exception as e:
            logger.warning(f"Unable to export RBF data. Issue: {e}")

    def parse_str_using_environment_variable(self, input_string):
        """
        Replaces environment variables with their actual values. See "_get_environment_variables" for more information
        on what is being replaced.

        Args:
            input_string (str): A string to have environment variables replaced with the actual values.
        Returns:
            str: A string with the environment variables replaced with their actual values instead of reference.
        """
        if input_string is None:
            logger.debug('"None" was parsed as a string for the environment variables.')
            return ""
        environment_vars_dict = self._get_environment_variables()
        parsed_string = core_str.replace_keys_with_values(input_string, environment_vars_dict)  # Replace Variables
        return parsed_string

    def _get_environment_variables(self):
        """
        Gets a dictionary where the keys are the variables and the values are the run-time determined paths.
        These are used to determine what variables should represent when updating a path. For example:
        "$TEMP_DIR/dir" would become "C:/Users/<user>/AppData/Local/Temp/dir"
        Variables:
            "$CACHE": The name of the latest cache used when processing.
            "$SUBJECT": The name of the subject mesh.
        Returns:
            dict: A dictionary where keys are variables and values are the current data.
        """
        # Get Initial Values
        environment_vars_dict = {
            "$CACHE": self._latest_cache_name,
            "$SUBJECT": self.subject_mesh,
        }

        # Return Environment Variables Dictionary
        return environment_vars_dict

    def reshape_subject_mesh(self, mesh_name, source_array, weights_array):
        """
        Reshapes the subject mesh.
        Args:
            mesh_name (str): Name suffix to use for the duplicated reshaped mesh.
            source_array (list or array-like): The source data array used for reshaping.
            weights_array (list or array-like): The weight data array controlling the reshape influence.
        """
        # Basic Checks
        if not self.subject_mesh:
            logger.warning(f"Subject mesh was not provided. Unable to reshape undefined mesh.")
        if not cmds.objExists(self.subject_mesh):
            msg = f'Subject mesh "{self.subject_mesh}" was not found in the scene. '
            msg += "Set a subject mesh and try again."
            logger.warning(msg)
        # Get Source
        if not source_array or not weights_array:
            logger.warning(f"Unable to retrieve source/target arrays. Check the integrity of the RBF data file.")
            return
        # Reshape Operation
        self.refresh_addons_data()  # Update common data with new updated names/paths
        self.apply_addons(required_order=MorpherAddon.Order.pre_morph)  # Apply Addons before Morphing
        # Use duplicate for operation
        _subject_mesh = self.subject_mesh
        _dupe_name = core_naming.get_short_name(_subject_mesh)
        _subject_mesh = cmds.duplicate(_subject_mesh, name=f"{_dupe_name}_{mesh_name}")[0]
        # Reshape/Morph subject mesh
        core_rbf.retarget_mesh(
            subject_mesh=_subject_mesh,
            source_array=source_array,
            weights_array=weights_array,
        )
        self.refresh_addons_reshaped_data(reshaped_mesh=_subject_mesh)
        self.apply_addons(required_order=MorpherAddon.Order.post_morph)  # Apply Addons after Morphing
        # Clean-up
        if not self.keep_original_mesh:
            cmds.delete(self.subject_mesh)

    # ---------------------------------------------- Mesh Morph Steps ----------------------------------------------
    def morpher_generate_reshaped_subject_meshes(self):
        """
        Generates reshaped versions of the subject mesh using available RBF cache data.

        For each valid RBF data path, this method:
        - Loads the corresponding source and weight arrays.
        - Reshapes the subject mesh.
        - Tracks the number of successfully generated meshes.

        Preconditions:
            - RBF cache paths must be set in self.rbf_data_paths.
            - A subject mesh must be set and exist in the scene.

        Warnings:
            - Logs warnings if no RBF paths are found, if the subject mesh is missing,
              or if any of the RBF files are not found on disk.
        """
        if not self.rbf_data_paths:
            logging.warning("No RBF caches selected. Nothing to generate.")
            return
        if not self.subject_mesh:
            logging.warning("No subject mesh to reshape. Nothing to generate.")
            return
        if not cmds.objExists(self.subject_mesh):
            logging.warning(f'Unable to locate subject mesh in the scene. Mesh: "{self.subject_mesh}".')
            return
        counter = 0
        for path in self.rbf_data_paths:
            if not os.path.exists(path):
                logging.warning(f"The selected RBF data is missing: {path}")
            else:
                rbf_data = core_io.read_json_dict(path=path)
                base_file_name = os.path.basename(path)
                file_name, _ = os.path.splitext(base_file_name)
                self._latest_cache_name = file_name
                self.reshape_subject_mesh(
                    mesh_name=file_name,
                    source_array=rbf_data.get("source_array"),
                    weights_array=rbf_data.get("weights_array"),
                )
                counter += 1
        feedback = core_fback.FeedbackMessage(
            quantity=counter,
            singular="mesh was",
            plural="meshes were",
            conclusion="generated.",
            zero_overwrite_message="No mesh was generated.",
        )
        feedback.print_inview_message()


if __name__ == "__main__":
    # Reset Scene and Create Test Paths ------------------------------------------------------------
    logger.setLevel(logging.DEBUG)

    # a_definition.export_rbf_data_file()  # Select source, then target and export file.

    # Create Definition ----------------------------------------------------------------------------
    a_definition = MorpherDefinition()
    a_definition.set_subject_mesh("cloth_mesh")

    test_rbf_data = os.path.join(
        tools_morpher_const.MeshMorpherConstants.DEFAULT_RBF_CACHE_FOLDER, r"male_mid_to_female_mid.json"
    )
    a_definition.set_rbf_data_paths([test_rbf_data])  # Multiple paths can be added

    # Create Delta Mush Test Layers ----------------------------------------------------------------
    a_delta_mush_addon = a_definition.get_addons(filter_type="DeltaMush")[0]
    # Zippers Layer
    dm_test_layers = [{"name": "zippers", "distanceWeight": 1, "smoothingIterations": 12, "vertices": "[0:370]"}]
    # Bottom Layer
    bottom_vertices = (
        "[371:373], [375:409], [411:812], [846:895], [1438:1440], [1548:1571], [1850], [1857], "
        "[1882:1890], [1963:1964], [1968:1979], [2009:2010], [2129:2182], [2235:2236], [2238:2241], "
        "[2247:2248], [2250:2253], [2259:2260], [2262:2263], [2352:2375], [2381:2382], [2384:2385], "
        "[2480:2503], [2510], [2517], [2541:2549], [2621:2622], [2624:2635], [2653:2705], [2742:2743], "
        "[2745:2748], [2754:2755], [2757:2760], [2766:2767], [2769:2770], [2786:2807], [2813:2814], "
        "[2816:2817], [2821:2830], [3263:3268], [3278:3308], [3446:3476], [3485:3758], [3787:3800], "
        "[3857], [3891:3903], [3913:3926], [3968:3969], [3971], [3981:3983], [4435:4436], [4464], "
        "[4520:4521]"
    )

    dm_test_layers.append({"name": "bottom", "vertices": bottom_vertices})
    a_delta_mush_addon.set_layers(dm_test_layers)

    # Create Masking Test Layers ----------------------------------------------------------------
    a_masking_addon = a_definition.get_addons(filter_type="Masking")[0]
    masking_test_layers = [{"name": "bottom", "vertices": bottom_vertices, "opacity": 0.5}]
    a_masking_addon.set_layers(masking_test_layers)

    # Generate Reshaped Meshes --------------------------------------------------------------------
    # a_definition.morpher_generate_reshaped_subject_meshes()  # Called again in the read 2nd project

    # Test JSON Export/Import ---------------------------------------------------------------------
    a_definition_as_dict = a_definition.get_definition_as_dict()
    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    test_json_path = os.path.join(desktop_path, r"mesh_morpher_definition.json")
    core_io.write_json(path=test_json_path, data=a_definition_as_dict)

    # Try to re-crete it from a dictionary (JSON compatibility)
    a_2nd_definition_as_dict = core_io.read_json_dict(path=test_json_path)
    a_2nd_definition = MorpherDefinition()
    a_2nd_definition.read_data_from_dict(a_definition_as_dict)

    a_2nd_definition.morpher_generate_reshaped_subject_meshes()
    os.remove(test_json_path)  # Delete test JSON file
