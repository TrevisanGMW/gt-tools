"""
Sine Attributes Controller

This module handles the binding between the Sine Attributes view and model,
and performs the Maya scene operations to build the sine network.
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds
    return cmds


class SineAttributesController:
    """Controller class for the Sine Attributes tool."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (SineAttributesModel): The model object holding preferences.
            view (SineAttributesView): The view object displaying the UI.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # Initialize View values from Model
        self.view.set_prefix(self.model.sine_prefix)
        self.view.set_add_abs(self.model.add_absolute_output)
        self.view.set_add_prefix_nn(self.model.nice_name_prefix)

        # Connect signals
        self.view.help_btn.clicked.connect(self.open_help)
        self.view.add_sine_btn.clicked.connect(self.execute_add_sine_attributes)

        self.view.show()

    def open_help(self):
        """Opens the Help dialog for the tool."""
        from gt.tools.sine_attributes.sine_attributes_view import SineAttributesHelpDialog
        help_dialog = SineAttributesHelpDialog(parent=self.view)
        help_dialog.exec_()

    def execute_add_sine_attributes(self):
        """Validates input, updates model settings, and creates the sine attribute network."""
        cmds = get_maya_cmds()

        # Get values from view
        raw_prefix = self.view.get_prefix()
        add_abs = self.view.get_add_abs()
        nice_name_prefix = self.view.get_add_prefix_nn()

        # Check selection
        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("Please select a target object to be the attribute holder.")
            return

        target = selection[0]

        # Determine prefix
        prefix = raw_prefix.replace(" ", "")
        if not prefix:
            prefix = "sine"

        # Check attribute conflicts
        current_attributes = cmds.listAttr(target, r=True, s=True, userDefined=True) or []
        possible_conflicts = [
            prefix + "Time",
            prefix + "Amplitude",
            prefix + "Frequency",
            prefix + "Offset",
            prefix + "Output",
            prefix + "Tick",
            prefix + "AbsOutput",
        ]

        for conflict in possible_conflicts:
            if conflict in current_attributes:
                cmds.warning(
                    f"The selected object already has a conflicting attribute: '{conflict}'. "
                    f"Please change the prefix or choose another object."
                )
                return

        # Update model and save preferences
        self.model.sine_prefix = prefix
        self.model.add_absolute_output = add_abs
        self.model.nice_name_prefix = nice_name_prefix
        self.model.save_preferences()

        # Execute Node Creation
        self.create_sine_network(
            target,
            sine_prefix=prefix,
            tick_source_attr="time1.outTime",
            hide_unkeyable=False,
            add_absolute_output=add_abs,
            nice_name_prefix=nice_name_prefix,
        )

        cmds.select(target, r=True)
        logger.info(f"Successfully added sine attributes to '{target}'.")

    @staticmethod
    def create_sine_network(
        obj,
        sine_prefix="sine",
        tick_source_attr="time1.outTime",
        hide_unkeyable=True,
        add_absolute_output=False,
        nice_name_prefix=True,
    ):
        """Creates the sine network connections in Autodesk Maya.

        Args:
            obj (str): Name of the target object.
            sine_prefix (str): Prefix for the attributes.
            tick_source_attr (str): Attribute path for the time source.
            hide_unkeyable (bool): Set non-keyable state for output/tick.
            add_absolute_output (bool): Create absolute output attribute.
            nice_name_prefix (bool): Prefix nice names.

        Returns:
            list: List of output attributes created.
        """
        import re
        cmds = get_maya_cmds()

        # Load quatNodes plugin
        required_plugin = "quatNodes"
        if not cmds.pluginInfo(required_plugin, q=True, loaded=True):
            cmds.loadPlugin(required_plugin, qt=False)

        influence_suffix = "Time"
        amplitude_suffix = "Amplitude"
        frequency_suffix = "Frequency"
        offset_suffix = "Offset"
        output_suffix = "Output"
        tick_suffix = "Tick"
        abs_suffix = "AbsOutput"

        influence_attr = sine_prefix + influence_suffix
        amplitude_attr = sine_prefix + amplitude_suffix
        frequency_attr = sine_prefix + frequency_suffix
        offset_attr = sine_prefix + offset_suffix
        output_attr = sine_prefix + output_suffix
        tick_attr = sine_prefix + tick_suffix
        abs_attr = sine_prefix + abs_suffix

        # Create utility nodes
        mdl_node = cmds.createNode("multDoubleLinear", name=f"{obj}_multDoubleLiner")
        quat_node = cmds.createNode("eulerToQuat", name=f"{obj}_eulerToQuat")
        multiply_node = cmds.createNode("multiplyDivide", name=f"{obj}_amplitude_multiply")
        sum_node = cmds.createNode("plusMinusAverage", name=f"{obj}_offset_sum")
        influence_multiply_node = cmds.createNode("multiplyDivide", name=f"{obj}_influence_multiply")

        # Add Attributes
        if nice_name_prefix:
            cmds.addAttr(obj, ln=influence_attr, at="double", k=True, maxValue=1, minValue=0)
            cmds.addAttr(obj, ln=amplitude_attr, at="double", k=True)
            cmds.addAttr(obj, ln=frequency_attr, at="double", k=True)
            cmds.addAttr(obj, ln=offset_attr, at="double", k=True)
            cmds.addAttr(obj, ln=tick_attr, at="double", k=True)
            cmds.addAttr(obj, ln=output_attr, at="double", k=True)
            if add_absolute_output:
                cmds.addAttr(obj, ln=abs_attr, at="double", k=True)
        else:
            cmds.addAttr(obj, ln=influence_attr, at="double", k=True, maxValue=1, minValue=0, nn=influence_suffix)
            cmds.addAttr(obj, ln=amplitude_attr, at="double", k=True, nn=amplitude_suffix)
            cmds.addAttr(obj, ln=frequency_attr, at="double", k=True, nn=frequency_suffix)
            cmds.addAttr(obj, ln=offset_attr, at="double", k=True, nn=offset_suffix)
            cmds.addAttr(obj, ln=tick_attr, at="double", k=True, nn=tick_suffix)
            cmds.addAttr(obj, ln=output_attr, at="double", k=True, nn=output_suffix)
            if add_absolute_output:
                cmds.addAttr(obj, ln=abs_attr, at="double", k=True, nn=re.sub(r"(\w)([A-Z])", r"\1 \2", abs_suffix))

        # Set default values
        cmds.setAttr(f"{obj}.{influence_attr}", 1)
        cmds.setAttr(f"{obj}.{amplitude_attr}", 1)
        cmds.setAttr(f"{obj}.{frequency_attr}", 10)

        # Hide unkeyable attributes if needed
        if hide_unkeyable:
            cmds.setAttr(f"{obj}.{tick_attr}", k=False)
            cmds.setAttr(f"{obj}.{output_attr}", k=False)
            if add_absolute_output:
                cmds.setAttr(f"{obj}.{abs_attr}", k=False)

        # Create connections
        cmds.connectAttr(tick_source_attr, f"{influence_multiply_node}.input1X")
        cmds.connectAttr(f"{influence_multiply_node}.outputX", f"{obj}.{tick_attr}")
        cmds.connectAttr(f"{obj}.{influence_attr}", f"{influence_multiply_node}.input2X")

        cmds.connectAttr(f"{obj}.{amplitude_attr}", f"{multiply_node}.input2X")
        cmds.connectAttr(f"{obj}.{frequency_attr}", f"{mdl_node}.input1")
        cmds.connectAttr(f"{obj}.{tick_attr}", f"{mdl_node}.input2")
        cmds.connectAttr(f"{obj}.{offset_attr}", f"{sum_node}.input1D[0]")
        cmds.connectAttr(f"{mdl_node}.output", f"{quat_node}.inputRotateX")

        cmds.connectAttr(f"{quat_node}.outputQuatX", f"{multiply_node}.input1X")
        cmds.connectAttr(f"{multiply_node}.outputX", f"{sum_node}.input1D[1]")
        cmds.connectAttr(f"{sum_node}.output1D", f"{obj}.{output_attr}")

        if add_absolute_output:
            squared_node = cmds.createNode("multiplyDivide", name=f"{obj}_abs_squared")
            reverse_squared_node = cmds.createNode("multiplyDivide", name=f"{obj}_reverseAbs_multiply")
            cmds.setAttr(f"{squared_node}.operation", 3)  # Power operation
            cmds.setAttr(f"{reverse_squared_node}.operation", 3)  # Power operation
            cmds.setAttr(f"{squared_node}.input2X", 2)
            cmds.setAttr(f"{reverse_squared_node}.input2X", 0.5)
            cmds.connectAttr(f"{obj}.{output_attr}", f"{squared_node}.input1X")
            cmds.connectAttr(f"{squared_node}.outputX", f"{reverse_squared_node}.input1X")
            cmds.connectAttr(f"{reverse_squared_node}.outputX", f"{obj}.{abs_attr}")
            return [f"{obj}.{output_attr}", f"{obj}.{abs_attr}"]

        return [f"{obj}.{output_attr}", None]
