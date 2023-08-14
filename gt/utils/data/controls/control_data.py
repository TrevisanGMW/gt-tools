"""
Control Data - All controls return a "ControlData" object as their return value.
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ControlData:
    """ Class representing control data. This class is used as a return value for all controls """
    def __init__(self, name, offset=None, setup=None, drivers=None, inputs=None, outputs=None, metadata=None):
        """
        Initialize ControlData response object.
        Args:
            name (str): Control transform name (long name with "|" pipe characters)
                        If not a string a ValueError is raised.
            offset (str, optional): Offset transform name (aka Offset Group). Main parent of the control.
            setup (str, optional): Rig setup transform name. Long name of the group carrying any extra
                                   elements used to drive the control.
            drivers (list, str, optional): Driver names. This would be extra objects used to drive the control.
                                           For example, other controls inside a main control.
                                           If not provided, the main transform ("name") is assumed to be the driver.
                                           Causing it to become "self.drivers = [self.name]"
            inputs (list, optional): A list of relevant input attributes available in the main control.
            outputs (list, optional): A list of relevant output attributes available in the main control.
            metadata (dict, optional): Metadata associated with the control data.
        """
        self.name = None
        self.offset = offset
        self.setup = None
        self.drivers = None
        self.inputs = []
        self.outputs = []
        self.metadata = None
        self.set_name(name)
        self.set_offset(offset)
        self.set_setup(setup)
        self.set_drivers(drivers)
        self.set_inputs(inputs)
        self.set_outputs(outputs)
        if metadata:
            self.set_metadata(metadata)

    def __repr__(self):
        """
        Uses "get_short_name()" to return the name of the object for when converting control data to a string.
        Returns:
            str: Short name of the control (from self.get_short_name)
        """
        return self.get_short_name()

    # ---------------------------- Setters ----------------------------
    def set_name(self, name):
        """
        Sets the name (long name) the control
        Args:
            name (str): Long name for the control (this is also the full path to the control)
        """
        if not name or not isinstance(name, str):
            raise ValueError(f'ControlData "name" attribute must be a string. Issue: "{type(name)}" received instead.')
        self.name = name

    def set_offset(self, offset):
        """
        Sets the offset transform used to position the control
        Args:
            offset (str): Offset transform name (long)
        """
        self.offset = offset

    def set_setup(self, setup):
        """
        Sets the setup group long name. (Item that is usually re-parented to a main "rig_setup" group)
        Args:
            setup (str): Long name of the setup transform group.
        """
        self.setup = setup

    def set_drivers(self, drivers):
        """
        Sets the drivers for this control. A driver is a control that is expected to be interacted with.
        This attribute is used when returning information about a control composed of multiple controls.
        e.g. When creating a complete set of facial controls, the drivers would be all the slider controls that the
             user might interact with.
        Args:
            drivers (list, str): A list of controls to be used a drivers.
                                 If a string is provided, it is converted to a list.
                                 If drivers is "None", then it's assumed to be the same as "name" (main control)
        """
        if drivers and isinstance(drivers, str):
            self.drivers = [drivers]
            return
        if drivers and isinstance(drivers, list):
            self.drivers = drivers
            return
        if drivers is None:
            self.drivers = [self.name]

    def set_inputs(self, inputs):
        """
        Sets new inputs for this control
        Args:
            inputs (list): A list of inputs (attributes) e.g. ["controlName.ikFkVisibility", "controlName.mainScale"]
        """
        if inputs is None:
            self.inputs = []
        if inputs and isinstance(inputs, list):
            self.inputs = inputs

    def set_outputs(self, outputs):
        """
        Sets new inputs for this control
        Args:
            outputs (list): A list of outputs (attributes) e.g. ["controlName.ikFkVisibility", "controlName.mainScale"]
        """
        if outputs is None:
            self.outputs = []
        if outputs and isinstance(outputs, list):
            self.outputs = outputs

    def set_metadata(self, new_metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            new_metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(new_metadata, dict):
            logger.warning(f'Unable to set curve metadata. Expected a dictionary, but got: "{str(type(new_metadata))}"')
            return
        self.metadata = new_metadata

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
        Gets the long name of the control (aka full path)
        Returns:
            str: Long name of the control (self.name)
        """
        return self.name

    def get_short_name(self):
        """
        Gets the short version of the name of the control (default name is its long name)
        Note, this name might not be unique
        Returns:
            str: Short name of the control (short version of self.name) - Last name after "|" characters
        """
        from gt.utils.naming_utils import get_short_name
        return get_short_name(self.name)

    def get_offset(self):
        """
        Gets the name of the offset transform for this control. The offset is the parent transform of the control.
        This element is used to move the control around without introducing transform data directly to the control.
        e.g. "move_ctrlOffset" is the parent of "move_ctrl".
             "move_ctrlOffset" can be moved, and will cause "move_ctrl"  to also update its position, but no data
             will appear under the "move_ctrl" translate, rotate and scale attributes.
        Returns:
            str: Long name of the offset transform (control parent transform/group)
        """
        return self.offset

    def get_setup(self):
        """
        Gets the name of the setup transform for this control. The setup is the parent of extra elements of the control.
        This group is usually stored inside a different location, such as "rig_setup" as it's just the logic for the
        control to behave in a certain way.
        Returns:
            str: Long name of the setup transform (control setup parent group)
        """
        return self.setup

    def get_drivers(self):
        """
        Returns the list of drivers. In case none were provided, this will be a list with the name of the main control.
        Returns:
            list: List of drivers (long names, strings)
        """
        return self.drivers

    def get_inputs(self):
        """
        Gets a list of inputs. These usually update the control in a certain way.
        Returns:
            list: A list of attributes following this pattern: ["<control-name>.<attribute-name>"] e.g. ["ctrl.tx"]
        """
        return self.inputs

    def get_outputs(self):
        """
        Gets a list of outputs. These usually cannot be set and carry data processed by the control.
        Returns:
            list: A list of attributes following this pattern: ["<control-name>.<attribute-name>"] e.g. ["ctrl.tx"]
        """
        return self.outputs

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata
