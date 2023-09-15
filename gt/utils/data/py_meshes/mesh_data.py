"""
Mesh Data - All parametric meshes return a "MeshData" object as their return value.
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeshData:
    """ Class representing mesh data. This class is used as a return value for all parametric meshes """
    def __init__(self, name, offset=None, setup=None, inputs=None, outputs=None, metadata=None):
        """
        Initialize MeshData response object.
        Args:
            name (str): Mesh transform name (long name with "|" pipe characters)
                        If not a string a ValueError is raised.
            offset (str, optional): Offset transform name (aka Offset Group). Main parent of the mesh.
            setup (list, optional): Rig setup items. Long name of the items used to create mesh logic.
            inputs (list, optional): A list of relevant input attributes available in the mesh.
            outputs (list, optional): A list of relevant output attributes available in the mesh.
            metadata (dict, optional): Metadata associated with the mesh data.
        """
        self.name = None
        self.offset = offset
        self.setup = []
        self.inputs = []
        self.outputs = []
        self.metadata = None
        self.set_name(name)
        self.set_offset(offset)
        if setup:
            self.set_setup(setup)
        self.set_inputs(inputs)
        self.set_outputs(outputs)
        if metadata:
            self.set_metadata(metadata)

    def __repr__(self):
        """
        Uses "get_short_name()" to return the name of the object for when converting mesh data to a string.
        Returns:
            str: Short name of the mesh (from self.get_short_name)
        """
        return self.get_short_name()

    # ---------------------------- Setters ----------------------------
    def set_name(self, name):
        """
        Sets the name (long name) the mesh
        Args:
            name (str): Long name for the mesh (this is also the full path to the mesh in Maya)
        """
        if not name or not isinstance(name, str):
            raise ValueError(f'MeshData "name" attribute must be a string. Issue: "{type(name)}" received instead.')
        self.name = name

    def set_offset(self, offset):
        """
        Sets the offset transform used to position the mesh
        Args:
            offset (str): Offset transform name (long)
        """
        self.offset = offset

    def set_setup(self, setup):
        """
        Sets the list of items used in the logic of the mesh.
        Args:
            setup (list): A list of items.
        """
        self.setup = setup

    def set_inputs(self, inputs):
        """
        Sets new inputs for the mesh.
        Args:
            inputs (list): A list of inputs (attributes) e.g. ["meshName.heightVisibility", "meshName.mainScale"]
        """
        if inputs is None:
            self.inputs = []
        if inputs and isinstance(inputs, list):
            self.inputs = inputs

    def set_outputs(self, outputs):
        """
        Sets new inputs for this mesh
        Args:
            outputs (list): A list of outputs (attributes) e.g. ["meshName.heightVisibility", "meshName.mainScale"]
        """
        if outputs is None:
            self.outputs = []
        if outputs and isinstance(outputs, list):
            self.outputs = outputs

    def set_metadata(self, new_metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the mesh.
        Args:
            new_metadata (dict): A dictionary describing extra information about the mesh
        """
        if not isinstance(new_metadata, dict):
            logger.warning(f'Unable to set metadata. Expected a dictionary, but got: "{str(type(new_metadata))}"')
            return
        self.metadata = new_metadata

    def add_to_setup(self, item):
        """
        Adds an item to the setup list of items.
        Args:
            item (str): Item used in the logic of the mesh
        """
        if item and isinstance(item, str):
            self.setup.append(item)
        else:
            logger.debug(f'Unable to add setup item. Must be a string.')

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    # ---------------------------- Getters ----------------------------
    def get_name(self):
        """
        Gets the long name of the mesh (aka full path)
        Returns:
            str: Long name of the mesh (self.name)
        """
        return self.name

    def get_short_name(self):
        """
        Gets the short version of the mesh name (default name is its long name)
        Note, this name might not be unique
        Returns:
            str: Short name of the mesh (short version of self.name) - Last name after "|" characters
        """
        from gt.utils.naming_utils import get_short_name
        return get_short_name(self.name)

    def get_offset(self):
        """
        Gets the name of the offset transform for this mesh. The offset is the parent transform of the mesh.
        This element is used to move the mesh around without introducing transform data directly to the mesh.
        e.g. "move_ctrlOffset" is the parent of "move_ctrl".
             "move_ctrlOffset" can be moved, and will cause "move_ctrl"  to also update its position, but no data
             will appear under the "move_ctrl" translate, rotate and scale attributes.
        Returns:
            str: Long name of the offset transform (mesh parent transform/group)
        """
        return self.offset

    def get_setup(self):
        """
        Gets the list of the setup items for this mesh.
        Returns:
            list: List of items used in the logic of the mesh
        """
        return self.setup

    def get_inputs(self):
        """
        Gets a list of inputs. These usually update the mesh in a certain way.
        Returns:
            list: A list of attributes following this pattern: ["<mesh-name>.<attribute-name>"] e.g. ["ctrl.tx"]
        """
        return self.inputs

    def get_outputs(self):
        """
        Gets a list of outputs. These usually cannot be set and carry data processed by the mesh.
        Returns:
            list: A list of attributes following this pattern: ["<mesh-name>.<attribute-name>"] e.g. ["ctrl.tx"]
        """
        return self.outputs

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata
