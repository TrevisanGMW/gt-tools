"""
"Dreamwall" control picker utilities
https://github.com/DreamWall-Animation/dwpicker

Import Line:
    import gt.utils.dwpicker as utils_dw
"""

import gt.core.rig_switch as core_rig_switch
import gt.core.feedback as core_fback
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import maya.cmds as cmds
import maya.mel as mel
import traceback
import dwpicker
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_full_name(base_name):
    """
    Constructs the full, namespaced name for a given base object name.

    This function queries the active dwpicker namespace and prepends it to the
    base name if a namespace exists.

    Args:
        base_name (str): The base name of the object (e.g., 'R_arm_CTRL').

    Returns:
        str or None: The full, namespaced name (e.g., 'CHAR:R_arm_CTRL') or
                     None if the provided base_name is invalid.
    """
    if not isinstance(base_name, str) or not base_name:
        return None

    current_namespace = dwpicker.current_namespace()

    if current_namespace:
        return f"{current_namespace}:{base_name}"

    return base_name


def get_control(control_name):
    """
    Silently finds a single control and returns its full name if it exists.

    Args:
        control_name (str): The base name of the control to find.

    Returns:
        str: The full, namespaced name of the control if found, otherwise None.
    """
    full_name = get_full_name(control_name)

    if full_name and cmds.objExists(full_name):
        return full_name

    return None


def select_controls(control_names):
    """
    Selects one or more controls and returns a list of the ones found.

    Args:
        control_names (str or list[str]): The base name or a list of base names for the
                                         controls to be selected.

    Returns:
        list[str]: A list containing the full, namespaced names of all successfully
                   found controls. Returns an empty list if no controls were found.
    """
    if isinstance(control_names, str):
        controls_to_process = [control_names]
    elif isinstance(control_names, list):
        controls_to_process = control_names
    else:
        cmds.warning("Invalid input. 'control_names' must be a string or a list of strings.")
        return []

    if not controls_to_process:
        cmds.warning("Input 'control_names' cannot be an empty string or list.")
        return []

    valid_full_names = []

    for control in controls_to_process:
        full_control_name = get_full_name(control)
        if cmds.objExists(full_control_name):
            valid_full_names.append(full_control_name)
        else:
            cmds.warning(f"Control '{full_control_name}' does not exist in the scene.")

    if valid_full_names:
        cmds.select(valid_full_names, replace=True)
    else:
        # If no valid controls were found, clear the selection
        cmds.select(clear=True)

    return valid_full_names


def key_controls(control_names, trs_only=False, inview_feedback=True):
    """
    Sets a keyframe on one or more controls and returns a list of the ones found.

    This function finds the full, namespaced name for each control and sets a
    keyframe on all existing, valid controls at the current time.

    Args:
        control_names (str or list[str]): The base name or a list of base names for the
                                         controls to be keyed.
        trs_only (bool, optional): If True, only key the translate, rotate, and
                                   scale attributes (if they are keyable).
                                   Defaults to False, which keys all keyable
                                   attributes.
        inview_feedback (bool, optional): When True, in-view feedback is printed.

    Returns:
        list[str]: A list containing the full, namespaced names of all successfully
                   found and keyed controls. Returns an empty list if no
                   controls were found or valid.
    """
    if isinstance(control_names, str):
        controls_to_process = [control_names]
    elif isinstance(control_names, list):
        controls_to_process = control_names
    else:
        cmds.warning("Invalid input. 'control_names' must be a string or a list of strings.")
        return []

    if not controls_to_process:
        cmds.warning("Input 'control_names' cannot be an empty string or list.")
        return []

    valid_full_names = []

    for control in controls_to_process:
        # Assuming get_full_name is available in this module, based on select_controls
        full_control_name = get_full_name(control)
        if cmds.objExists(full_control_name):
            valid_full_names.append(full_control_name)
        else:
            cmds.warning(f"Control '{full_control_name}' does not exist in the scene.")

    if not valid_full_names:
        return []

    if trs_only:
        attributes_to_key = []
        trs_attributes = [
            "translateX",
            "translateY",
            "translateZ",
            "rotateX",
            "rotateY",
            "rotateZ",
            "scaleX",
            "scaleY",
            "scaleZ",
        ]

        for control_name in valid_full_names:
            for attr_name in trs_attributes:
                attribute_path = f"{control_name}.{attr_name}"

                # Check if the attribute exists and is keyable (not locked, etc.)
                if cmds.objExists(attribute_path):
                    if cmds.getAttr(attribute_path, keyable=True):
                        attributes_to_key.append(attribute_path)

        if attributes_to_key:
            cmds.setKeyframe(attributes_to_key)
    else:
        for attr in valid_full_names:
            cmds.setKeyframe(attr)

    if inview_feedback:
        _conclusion = ""
        if trs_only:
            _conclusion += " (TRS Only)"
        feedback = core_fback.FeedbackMessage(
            quantity=len(valid_full_names),
            singular="control was keyed",
            plural="controls were keyed",
            conclusion=_conclusion,
            zero_overwrite_message="No controls were keyed",
            style_conclusion="color:#FFFF00;text-decoration:underline;",
        )
        feedback.print_inview_message(system_write=False)

    return valid_full_names


def inview_selection_feedback(control_list=None):
    """
    Displays an in-view message summarizing the current or provided selection.

    If a list of controls is not provided, the function uses the current
    selection in the Maya scene. It provides no feedback if the selection is empty.

    Args:
        control_list (list[str], optional): A list of full control names to generate
                                            feedback for. Defaults to None, which triggers
                                            the use of `cmds.ls(selection=True)`.
    """
    if control_list is None:
        selected_items = cmds.ls(selection=True)
    else:
        selected_items = control_list

    if not selected_items:
        return

    num_selected = len(selected_items)

    if num_selected == 1:
        # Get the base name by splitting at the last colon
        base_name = selected_items[0].split(":")[-1]
        feedback = core_fback.FeedbackMessage(
            prefix="Control",
            intro=base_name,
            style_intro="color:#FFDD00;text-decoration:underline;",
            conclusion="selected.",
        )
    else:
        feedback = core_fback.FeedbackMessage(
            intro=str(num_selected),
            style_intro="color:#FFDD00;",
            conclusion="controls selected.",
        )

    feedback.print_inview_message(system_write=False)


def set_attr(names, attr, value, inview_feedback=True):
    """
    Sets a specified attribute to a given value on one or more controls.

    This function constructs the full name of each control using the active
    dwpicker namespace, validates its existence, and then sets the attribute.
    It provides an optional, context-aware in-view feedback message.

    Args:
        names (str or list[str]): The base name or a list of base names for the
                                         controls to be modified.
        attr (str): The name of the attribute to set (e.g., 'translateX').
        value (any): The value to apply to the attribute.
        inview_feedback (bool, optional): If True, an in-view message will be displayed
                                          summarizing the action. Defaults to False.

    Returns:
        list[str]: A list of the full attribute paths ('object.attribute') that were
                   successfully modified. Returns an empty list if none were changed.
    """
    if isinstance(names, str):
        controls_to_process = [names]
    elif isinstance(names, list):
        controls_to_process = names
    else:
        cmds.warning("Invalid input. 'control_names' must be a string or a list of strings.")
        return []

    if not all([controls_to_process, isinstance(attr, str), attr]):
        cmds.warning("Invalid input. Provide a non-empty list of controls and an attribute name.")
        return []

    successful_paths = []

    for control in controls_to_process:
        full_control_name = get_full_name(control)
        if not cmds.objExists(full_control_name):
            cmds.warning(f"Control '{full_control_name}' does not exist in the scene.")
            continue

        attribute_path = f"{full_control_name}.{attr}"
        try:
            # Maya requires a 'type' flag for string attributes
            if isinstance(value, str):
                cmds.setAttr(attribute_path, value, type="string")
            else:
                cmds.setAttr(attribute_path, value)
            successful_paths.append(attribute_path)
        except (RuntimeError, ValueError) as error:
            cmds.warning(f"Failed to set attribute '{attribute_path}': {error}")

    if inview_feedback and successful_paths:
        num_affected = len(successful_paths)
        # Use the first base name from the original list for single-item feedback
        base_control_name = controls_to_process[0]

        if num_affected == 1:
            feedback = core_fback.FeedbackMessage(
                intro=f"{attr}",
                style_intro="color:#FFDD00;",
                conclusion=f"on '{base_control_name}' set to {value}.",
            )
        else:
            feedback = core_fback.FeedbackMessage(
                intro=f"{attr}",
                style_intro="color:#FFDD00;",
                conclusion=f"set to {value} on {num_affected} controls.",
            )
        feedback.print_inview_message(system_write=False)

    return successful_paths


def get_attr(name, attr):
    """
    Safely retrieves the value of a specified attribute from a single control.

    This function constructs the full name of the control using the active
    dwpicker namespace and attempts to get the attribute value. It is designed
    to fail gracefully, returning None instead of raising an exception if the
    object or attribute cannot be found.

    Args:
        name (str): The base name of the control to query.
        attr (str): The name of the attribute to get (e.g., 'translateX').

    Returns:
        any: The value of the requested attribute, or None if the operation fails.
    """
    if not all([isinstance(name, str), name, isinstance(attr, str), attr]):
        cmds.warning("Invalid input. Provide a non-empty control and attribute name.")
        return None

    full_control_name = get_full_name(name)
    attribute_path = f"{full_control_name}.{attr}"

    try:
        value = cmds.getAttr(attribute_path)
        return value
    except (RuntimeError, ValueError):
        # This will catch errors if the object/attribute doesn't exist or
        # is otherwise inaccessible. The function fails quietly by design.
        return None


def toggle_attr(names, attr, inview_feedback=True):
    """
    Toggles a boolean or integer attribute on one or more controls.

    This function flips the value of an attribute for each specified control.
    It handles integers (0 to 1, 1 to 0) and booleans (True to False,
    False to True). The check is performed individually for each control.

    Args:
        names (str or list[str]): The base name or a list of base names for the
                                  controls to be modified.
        attr (str): The name of the attribute to toggle (e.g., 'visibility').
        inview_feedback (bool, optional): If True, an in-view message will be displayed
                                          summarizing the action. Defaults to True.

    Returns:
        list[str]: A list of the full attribute paths ('object.attribute') that were
                   successfully toggled. Returns an empty list if none were changed.
    """
    if isinstance(names, str):
        controls_to_process = [names]
    elif isinstance(names, list):
        controls_to_process = names
    else:
        cmds.warning("Invalid input. 'names' must be a string or a list of strings.")
        return []

    if not all([controls_to_process, isinstance(attr, str), attr]):
        cmds.warning("Invalid input. Provide a non-empty list of controls and an attribute name.")
        return []

    successful_paths = []

    for control in controls_to_process:
        full_control_name = get_full_name(control)
        if not full_control_name:
            continue

        attribute_path = f"{full_control_name}.{attr}"
        try:
            current_value = cmds.getAttr(attribute_path)

            # The 'not' operator correctly toggles both booleans and 0/1 integers
            new_value = not current_value

            cmds.setAttr(attribute_path, new_value)
            successful_paths.append(attribute_path)

        except (RuntimeError, ValueError) as error:
            cmds.warning(f"Failed to toggle attribute '{attribute_path}': {error}")

    if inview_feedback and successful_paths:
        num_affected = len(successful_paths)
        base_control_name = controls_to_process[0]

        if num_affected == 1:
            feedback = core_fback.FeedbackMessage(
                intro=f"{attr}",
                style_intro="color:#FFDD00;",
                conclusion=f"toggled on '{base_control_name}'.",
            )
        else:
            feedback = core_fback.FeedbackMessage(
                intro=f"{attr}",
                style_intro="color:#FFDD00;",
                conclusion=f"toggled on {num_affected} controls.",
            )
        feedback.print_inview_message(system_write=False)

    return successful_paths


def fk_ik_switch(ik_fk_data, inview_feedback=True):
    """Triggers an automatic FK/IK switch for a specified limb.

    This function is a convenience wrapper around the core switching logic.
    It automatically resolves the current namespace from the dwpicker context
    and executes the switch in 'auto' mode, which matches the controls to
    the opposite state based on the rig's FK/IK attribute.

    Args:
        ik_fk_data (dict): A dictionary containing the necessary rig component
                           names and attribute paths required for the switch.
        inview_feedback (bool, optional): When True, feedback regarding the operation is displayed in the viewport.
    """
    current_namespace = dwpicker.current_namespace()
    if current_namespace is None:
        current_namespace = ""

    core_rig_switch.fk_ik_switch(
        ik_fk_data=ik_fk_data,
        direction=core_rig_switch.SwitchDirections.auto,
        namespace=current_namespace,
    )

    switch_control_base = ik_fk_data.get("switch_ctrl")
    full_control_name = get_full_name(switch_control_base)

    if inview_feedback:
        if not cmds.objExists(full_control_name):
            return  # Exit quietly if the control isn't in the scene
        try:
            attribute_path = f"{full_control_name}.{core_rig_switch.SWITCH_ATTR}"
            current_value = cmds.getAttr(attribute_path)
            # 0 = FK, 1 = IK. A value > 0.5 is considered IK.
            current_state = "IK" if current_value > 0.5 else "FK"
        except (RuntimeError, ValueError):
            cmds.warning(f"Could not read attribute '{core_rig_switch.SWITCH_ATTR}' on '{full_control_name}'.")
            return
        feedback = core_fback.FeedbackMessage(
            intro=switch_control_base,
            style_intro="color:#FFDD00;text-decoration:underline;",
            conclusion=f"switched to {current_state}.",
        )
        feedback.print_inview_message(system_write=False)


def restore_picker_rig_data(target_node=None):
    """
    Restores the 'dwpicker' data from a dedicated backup attribute.

    If a target node is provided, only that node is processed. Otherwise,
    the function searches the entire scene for all picker data nodes.

    After a successful restoration, the 'dwpicker' UI is closed and
    re-opened to reflect the restored data.

    Args:
        target_node (str, optional): The specific picker data node (script node)
            to restore. If None, all nodes found by
            `dwpicker.scenedata.list_picker_holder_nodes()` will be processed.
            Defaults to None. (Entire scene)
    """
    if target_node:
        _picker_data_nodes = [target_node]
    else:
        _picker_data_nodes = dwpicker.scenedata.list_picker_holder_nodes()
    if not _picker_data_nodes:
        logging.warning("Unable to restore picker rig data. Not picker data nodes detected in the scene.")
        return
    import gt.tools.auto_rigger.modules.module_picker_data as tools_rig_picker

    attr_data = tools_rig_picker.ATTR_DW_PICKER_DATA  # Gets restored
    attr_rig_data = tools_rig_picker.ATTR_DW_PICKER_DATA_RIG  # Backup
    counter = 0
    for picker_data_node in _picker_data_nodes:
        if not cmds.attributeQuery(attr_rig_data, node=picker_data_node, exists=True):
            message = f'Unable to restore picker rig data for "{picker_data_node}".'
            message += f' Missing original data attribute "{attr_data}".'
            logging.warning(message)
            continue

        original_data = cmds.getAttr(f"{picker_data_node}.{attr_rig_data}")
        try:
            cmds.setAttr(f"{picker_data_node}.{attr_data}", original_data, type="string")
            counter += 1
        except Exception as e:
            logging.warning(f'Unable to restore picker rig data for "{picker_data_node}". Issue: {e}')
    if counter > 0:
        logging.info(f"Original rig data restored in {counter} picker(s).")
        dwpicker.close()
        dwpicker.show()


def print_key_command_from_selection(trs_only=False):
    """
    Prints a python command that can be used to key the selected controls.
    Used to quickly populate picker with key control scripts.

    Args:
        trs_only (bool, optional): Determines if it will key only translate, rotate and scale or all keyable attrs.
    """
    selection = cmds.ls(selection=True)
    if not selection:
        logging.warning(f"Nothing selected.")
        return
    command = "import gt.utils.dwpicker as utils_dw\n"
    ctrl_string = '", "'.join(selection)
    command += f'controls = ["{ctrl_string}"]\n'
    command += f"utils_dw.key_controls(controls, trs_only={trs_only})"
    print(command)


class BakeOptionsDialog(ui_qt.QtWidgets.QDialog):
    """
    A non-blocking (modeless) dialog for users to specify bake options for FK/IK switching.
    """

    def __init__(self, limb_ids, initial_namespace, show_limb_edit, callback, parent=None):
        """
        Initializes the BakeOptionsDialog with baking parameters and UI configuration.

            Args:
                limb_ids (list[str]): A list of string identifiers for the limbs to be baked.
                initial_namespace (str): The default namespace to populate in the UI.
                show_limb_edit (bool): If True, allows the user to edit the list of limbs via a text field.
                                       If False, limbs are displayed as static labels.
                callback (callable): The function to execute when the bake operation is confirmed.
                                     Must accept (namespace, start_frame, end_frame, direction, limb_list).
                parent (QtWidgets.QWidget, optional): The parent widget for this dialog.
                                                      Defaults to None, which will find the Maya Main Window.
        """
        # 1. Parent Handling
        if not parent:
            parent = ui_qt_utils.get_maya_main_window()

        super(BakeOptionsDialog, self).__init__(parent)

        # 2. Persistence Magic (Garbage Collection Prevention)
        # We attach the reference to the QApplication singleton.
        # This keeps the Python object alive without global variables in your script.
        self._protect_from_gc()

        # 3. Cleanup Hook
        # When the window closes, we must remove the reference to allow memory cleanup.
        self.finished.connect(self._on_finished)

        # Attribute Initialization
        self.limb_input = None
        self.ns_input = None
        self.rb_auto = None
        self.rb_fk_ik = None
        self.dir_btn_group = None
        self.start_input = None
        self.end_input = None
        self.rb_ik_fk = None

        self.setWindowTitle("Bake Options")

        # WindowStaysOnTop ensures the tool doesn't get buried
        self.setWindowFlags(ui_qt.QtCore.Qt.Window | ui_qt.QtCore.Qt.WindowStaysOnTopHint)
        self.resize(380, 350)

        # Ensure C++ resources are freed on close
        self.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)

        self.limb_ids = limb_ids
        self.show_limb_edit = show_limb_edit
        self._callback = callback
        self.initial_namespace = initial_namespace or ""

        # Initialize default frames to ENTIRE TIMELINE
        self.start_frame = int(cmds.playbackOptions(query=True, minTime=True))
        self.end_frame = int(cmds.playbackOptions(query=True, maxTime=True))

        self.create_ui()

    def _protect_from_gc(self):
        """Attaches this instance to the QApplication to prevent premature garbage collection."""
        app = ui_qt.QtWidgets.QApplication.instance()
        if not hasattr(app, "_tech_anim_bake_refs"):
            app._tech_anim_bake_refs = set()
        app._tech_anim_bake_refs.add(self)

    def _on_finished(self, result):
        """
        Handles the cleanup of the dialog instance to ensure proper garbage collection.

        Removes the instance reference from the QApplication's custom set, allowing Python
        to release the memory when the window is closed.

        Args:
            result (int): The result code returned when the dialog is closed (e.g., Accepted or Rejected).
        """
        app = ui_qt.QtWidgets.QApplication.instance()
        if hasattr(app, "_tech_anim_bake_refs"):
            app._tech_anim_bake_refs.discard(self)

    def create_ui(self):
        """Builds the user interface layouts and widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)

        # 1. Limbs Input
        if self.show_limb_edit:
            limb_group = ui_qt.QtWidgets.QGroupBox("Limbs to Bake (Comma Separated)")
            limb_layout = ui_qt.QtWidgets.QVBoxLayout()

            self.limb_input = ui_qt.QtWidgets.QLineEdit()
            self.limb_input.setText(", ".join(self.limb_ids))
            self.limb_input.setPlaceholderText("e.g. biped_left_arm, biped_right_arm")

            limb_layout.addWidget(self.limb_input)
            limb_group.setLayout(limb_layout)
            main_layout.addWidget(limb_group)
        else:
            header_group = ui_qt.QtWidgets.QGroupBox("Limbs to Bake")
            header_layout = ui_qt.QtWidgets.QVBoxLayout()
            for raw_id in self.limb_ids:
                formatted = raw_id.replace("_", " ").title()
                lbl = ui_qt.QtWidgets.QLabel(f"• {formatted}")
                lbl.setStyleSheet("font-weight: bold;")
                header_layout.addWidget(lbl)
            header_group.setLayout(header_layout)
            main_layout.addWidget(header_group)

        # 2. Namespace Selection
        ns_group = ui_qt.QtWidgets.QGroupBox("Target Namespace")
        ns_layout = ui_qt.QtWidgets.QHBoxLayout()

        self.ns_input = ui_qt.QtWidgets.QLineEdit()
        self.ns_input.setText(self.initial_namespace)
        self.ns_input.setPlaceholderText("e.g. character_01")

        ns_get_btn = ui_qt.QtWidgets.QPushButton("Get Selection")
        ns_get_btn.setToolTip("Get namespace from current selection")
        ns_get_btn.clicked.connect(self.on_get_namespace)

        ns_layout.addWidget(self.ns_input)
        ns_layout.addWidget(ns_get_btn)
        ns_group.setLayout(ns_layout)
        main_layout.addWidget(ns_group)

        # 3. Direction Options
        dir_group = ui_qt.QtWidgets.QGroupBox("Switch Direction")
        dir_layout = ui_qt.QtWidgets.QHBoxLayout()

        self.rb_auto = ui_qt.QtWidgets.QRadioButton("Auto")
        self.rb_auto.setChecked(True)
        self.rb_fk_ik = ui_qt.QtWidgets.QRadioButton("FK to IK")
        self.rb_ik_fk = ui_qt.QtWidgets.QRadioButton("IK to FK")

        self.dir_btn_group = ui_qt.QtWidgets.QButtonGroup()
        self.dir_btn_group.addButton(self.rb_auto)
        self.dir_btn_group.addButton(self.rb_fk_ik)
        self.dir_btn_group.addButton(self.rb_ik_fk)

        dir_layout.addWidget(self.rb_auto)
        dir_layout.addWidget(self.rb_fk_ik)
        dir_layout.addWidget(self.rb_ik_fk)
        dir_group.setLayout(dir_layout)
        main_layout.addWidget(dir_group)

        # 4. Frame Range Selection
        range_group = ui_qt.QtWidgets.QGroupBox("Frame Range")
        range_layout = ui_qt.QtWidgets.QGridLayout()

        # Start Frame
        range_layout.addWidget(ui_qt.QtWidgets.QLabel("Start:"), 0, 0)
        self.start_input = ui_qt.QtWidgets.QSpinBox()
        self.start_input.setRange(-99999, 99999)
        self.start_input.setValue(self.start_frame)
        range_layout.addWidget(self.start_input, 0, 1)

        btn_get_start = ui_qt.QtWidgets.QPushButton("Get")
        btn_get_start.setFixedWidth(40)
        btn_get_start.clicked.connect(lambda: self.on_get_current(self.start_input))
        range_layout.addWidget(btn_get_start, 0, 2)

        # End Frame
        range_layout.addWidget(ui_qt.QtWidgets.QLabel("End:"), 1, 0)
        self.end_input = ui_qt.QtWidgets.QSpinBox()
        self.end_input.setRange(-99999, 99999)
        self.end_input.setValue(self.end_frame)
        range_layout.addWidget(self.end_input, 1, 1)

        btn_get_end = ui_qt.QtWidgets.QPushButton("Get")
        btn_get_end.setFixedWidth(40)
        btn_get_end.clicked.connect(lambda: self.on_get_current(self.end_input))
        range_layout.addWidget(btn_get_end, 1, 2)

        range_group.setLayout(range_layout)
        main_layout.addWidget(range_group)

        # 5. Range Helper Buttons (Horizontal)
        helpers_layout = ui_qt.QtWidgets.QHBoxLayout()

        btn_get_sel_range = ui_qt.QtWidgets.QPushButton("Get Selected Range")
        btn_get_sel_range.clicked.connect(self.on_get_timeline_selection)
        helpers_layout.addWidget(btn_get_sel_range)

        btn_get_full_range = ui_qt.QtWidgets.QPushButton("Get Timeline")
        btn_get_full_range.clicked.connect(self.on_get_full_timeline)
        helpers_layout.addWidget(btn_get_full_range)

        main_layout.addLayout(helpers_layout)

        # Separator
        line = ui_qt.QtWidgets.QFrame()
        line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        # 6. Action Buttons
        btn_layout = ui_qt.QtWidgets.QHBoxLayout()
        bake_btn = ui_qt.QtWidgets.QPushButton("Bake")
        bake_btn.setFixedHeight(40)
        bake_btn.setStyleSheet("background-color: #5D5D5D; font-weight: bold; font-size: 14px;")
        bake_btn.clicked.connect(self.on_bake)

        cancel_btn = ui_qt.QtWidgets.QPushButton("Close")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(bake_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    # --- Slots ---

    def on_get_namespace(self):
        """Populates the namespace field based on the first selected object."""
        sel = cmds.ls(selection=True)
        if sel:
            obj = sel[0]
            if ":" in obj:
                ns = obj.split(":")[0]
                self.ns_input.setText(ns)
            else:
                self.ns_input.setText("")
        else:
            logger.warning("No selection found to determine namespace.")

    @staticmethod
    def on_get_current(widget):
        """
        Sets the value of the provided widget to the current Maya timeline frame.

        Args:
            widget (QtWidgets.QSpinBox): The UI widget (spinbox) to update with the current time.
        """
        curr = int(cmds.currentTime(query=True))
        widget.setValue(curr)

    def on_get_timeline_selection(self):
        """Updates fields to match highlighted timeline range."""
        try:
            g_playback_slider = mel.eval("$tmpVar=$gPlayBackSlider")
            if cmds.timeControl(g_playback_slider, query=True, rangeVisible=True):
                raw_range = cmds.timeControl(g_playback_slider, query=True, rangeArray=True)
                self.start_input.setValue(int(raw_range[0]))
                self.end_input.setValue(int(raw_range[1]) - 1)
            else:
                curr = int(cmds.currentTime(query=True))
                self.start_input.setValue(curr)
                self.end_input.setValue(curr + 1)
        except Exception as e:
            logger.warning(f"Could not fetch timeline: {e}")

    def on_get_full_timeline(self):
        """Updates fields to match global playback range."""
        start = int(cmds.playbackOptions(query=True, minTime=True))
        end = int(cmds.playbackOptions(query=True, maxTime=True))
        self.start_input.setValue(start)
        self.end_input.setValue(end)

    def on_bake(self):
        """Gather UI data and trigger callback."""
        # Added try/except to catch silent failures and 'nothing happens' bugs
        try:
            s_frame = self.start_input.value()
            e_frame = self.end_input.value()
            namespace = self.ns_input.text()

            direction = "auto"
            if self.rb_fk_ik.isChecked():
                direction = "fk_to_ik"
            elif self.rb_ik_fk.isChecked():
                direction = "ik_to_fk"

            limb_list = self.limb_ids
            if self.show_limb_edit:
                raw_text = self.limb_input.text()
                limb_list = [x.strip() for x in raw_text.split(",") if x.strip()]

            if self._callback:
                self._callback(namespace, s_frame, e_frame, direction, limb_list)
            else:
                logger.error("Callback function is missing.")

        except Exception as e:
            logger.error(f"UI Error during bake: {e}")
            traceback.print_exc()


def fk_ik_switch_bake(switch_types, direction="auto", time_mode="timeline", edit_limbs_mode=False):
    """
    The main worker function to handle switching logic, time ranges, and execution.

    Args:
        switch_types (str | list[str]): The identifier for the limb(s).
        direction (str, optional): The switch direction.
        time_mode (str, optional): 'timeline' or 'custom'.
        edit_limbs_mode (bool, optional): If True, UI opens with editable text field.
    """
    current_ns = dwpicker.current_namespace()

    if isinstance(switch_types, str):
        if "," in switch_types:
            switch_types = [part.strip() for part in switch_types.split(",") if part.strip()]
        else:
            switch_types = [switch_types]

    # --- Callback Logic ---
    def perform_bake(target_namespace, start_f, end_f, dir_override, active_limb_list):
        """
        Executes the FK/IK switch bake operation within a safe context.

        This internal function handles the actual call to the core rig switch library,
        managing scene refresh suspension and error logging.

        Args:
            target_namespace (str): The namespace of the rig character.
            start_f (int): The starting frame of the bake range.
            end_f (int): The ending frame of the bake range.
            dir_override (str): The direction of the switch ('fk_to_ik', 'ik_to_fk', or 'auto').
            active_limb_list (list[str]): A list of limb identifiers to process.
        """
        limb_str = active_limb_list[0] if len(active_limb_list) == 1 else ", ".join(active_limb_list)

        logger.info(f"Switch: {limb_str} ({dir_override}) on '{target_namespace}' | Frames: {start_f}-{end_f}")

        if not target_namespace:
            logger.warning("No namespace provided. Attempting operation on root.")

        switch_dicts = core_rig_switch.get_switch_dictionaries_from_types(active_limb_list)
        if not switch_dicts:
            logger.error(f"Could not resolve switch dictionaries for: {active_limb_list}")
            return

        try:
            cmds.refresh(suspend=True)
            core_rig_switch.fk_ik_switch(
                ik_fk_data=switch_dicts,
                direction=dir_override,
                namespace=target_namespace,
                keyframe=True,
                start_time=start_f,
                end_time=end_f,
                method="bake",
            )
        except Exception as e:
            logger.error(f"Error during FK/IK Switch: {e}")
            traceback.print_exc()
        finally:
            cmds.refresh(suspend=False)

    # --- Execution Modes ---
    if time_mode == "custom":
        dialog = BakeOptionsDialog(
            limb_ids=switch_types,
            initial_namespace=current_ns,
            show_limb_edit=edit_limbs_mode,
            callback=perform_bake,
        )
        dialog.show()

    else:
        # --- Immediate Mode (No UI) ---
        s_frame = int(cmds.playbackOptions(query=True, animationStartTime=True))
        e_frame = int(cmds.playbackOptions(query=True, animationEndTime=True))

        if time_mode != "timeline":
            s_frame = int(cmds.currentTime(query=True))
            e_frame = s_frame + 1

        perform_bake(current_ns, s_frame, e_frame, direction, switch_types)


if __name__ == "__main__":
    # set_attr(
    #     names=["L_arm_CTRL"],
    #     attr="influenceSwitch",
    #     value=1,
    #     inview_feedback=True,
    # )
    # fk_ik_switch(core_rig_switch.SwitchPairs.biped_left_arm)
    # select_controls(control_names=["L_hand_CTRL", "L_upperArm_CTRL"])
    # inview_selection_feedback()

    # if controls:
    #     cmds.setKeyframe(controls)
    # restore_picker_rig_data(),
    # print_key_command_from_selection()

    # key_controls(["L_lowerArm_CTRL", "L_upperArm_CTRL"], trs_only=True)
    fk_ik_switch_bake(switch_types=["biped_left_arm", "biped_right_arm"], direction="auto", time_mode="custom")
