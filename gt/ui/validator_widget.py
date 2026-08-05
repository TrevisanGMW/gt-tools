"""
Validator Widget to be used with validators that rely on the ValidatorBase class found in gt.core.validator

Import Line:
    import gt.ui.validator_widget as ui_validator

"""

import gt.ui.resource_library as ui_res_lib
import gt.core.validator as core_val
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging
import inspect

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ValidatorModel(ui_qt.QtCore.QAbstractListModel):
    """
    A model for managing a list of ValidatorBase objects.

    This model handles validator data, status icons, and sorting logic
    for display in a QListView.

    Args:
        validators (list[core_val.ValidatorBase]): A list of validator instances.
        parent (ui_qt.QtWidgets.QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, validators, parent=None):
        """
        Initializes the ValidatorModel.

        Args:
            validators (list[core_val.ValidatorBase]): A list of validator instances
                                                       to be managed by the model.
            parent (ui_qt.QtWidgets.QWidget, optional): The parent widget.
                                                         Defaults to None.
        """
        super().__init__(parent)
        self.validators = validators
        self._is_batch_running = False  # Flag to prevent signal spam
        self.refresh_on_external_run = True  # Controls if external runs refresh UI
        self._wrap_validator_methods()  # Wrap methods to intercept calls
        self.icons = {}
        self.load_icons()
        self.selected_index = None
        self.order_validators()
        self.scope = core_val.ValidatorScope.SCENE

    def set_refresh_on_external_run(self, refresh_enabled):
        """
        Sets whether the model will automatically refresh the UI
        when a single validator's `validate()` method is called
        externally (i.e., not via the model's `run_validators()` method).

        Args:
            refresh_enabled (bool): If True, external calls to `validate()`
                                    will trigger a UI refresh. If False,
                                    they will not.
        """
        self.refresh_on_external_run = bool(refresh_enabled)
        logging.debug(f"Refresh on external run set to: {self.refresh_on_external_run}")

    def set_scope(self, scope):
        """
        Sets the validation scope and updates all managed validators.

        Args:
            scope (int): Determines the validation scope (e.g. 'selection', 'scene', or 'type').
        """
        self.scope = scope

    def get_scope(self):
        """
        Sets the validation scope and updates all managed validators.

        Returns:
            int: Validation scope (e.g. 'selection', 'scene', or 'type' as int).
        """
        return self.scope

    def _wrap_validator_methods(self):
        """
        Wraps the 'validate' method of each validator instance.

        This intercepts calls to `validator.validate()` made from external
        code, ensuring the model can emit the necessary signals to
        refresh the view (e.g., update icon and re-sort the list).
        """
        for validator in self.validators:
            # 1. Store the original (bound) method
            original_validate_method = validator.validate

            # 2. Create a closure that captures the original method
            def create_wrapper(original_method, validator_name):
                """
                Creates a closure to wrap the original validate method of a validator.

                This wrapper ensures that the validator's name and the original method
                reference are preserved within the scope of the wrapped call.

                Args:
                    original_method (callable): The original bound 'validate' method
                        from the validator instance.
                    validator_name (str): The display name of the validator,
                        used for logging purposes.

                Returns:
                    callable: The 'wrapped_validate' function that replaces the
                        original method.
                """

                def wrapped_validate(*args, **kwargs):
                    """
                    Executes the original validation logic and triggers UI refresh signals.

                    This method ensures the correct scope is applied and notifies the
                    view to re-sort or refresh icons if the validation was triggered
                    externally and not part of a batch process.

                    Args:
                        *args: Variable length argument list passed to the original
                            validate method.
                        **kwargs: Arbitrary keyword arguments passed to the original
                            validate method.
                    """
                    # Ensure scope is passed if the validator method expects it via kwargs
                    # or if the original method logic relies on the instance attribute we updated in set_scope
                    if "scope" not in kwargs:
                        kwargs["scope"] = self.scope

                    # Run the original validation logic
                    original_method(*args, **kwargs)

                    # Only emit refresh signals if:
                    # 1. A batch run is NOT in progress.
                    # 2. The 'refresh_on_external_run' flag is True.
                    if not self._is_batch_running and self.refresh_on_external_run:
                        logging.debug(f"Validator '{validator_name}' ran externally, refreshing model.")
                        # We must do a full layout change to re-sort
                        self.layoutAboutToBeChanged.emit()
                        self.order_validators()
                        self.layoutChanged.emit()

                return wrapped_validate

            # 3. Replace the instance's 'validate' method with the wrapper
            validator.validate = create_wrapper(original_validate_method, validator.name)

    def load_icons(self):
        """
        Loads icons from the resource library and stores them as pixmaps.

        Icons are resized and cached in the `self.icons` dictionary for
        use in the `data` method.
        """
        icon_size = ui_qt.QtCore.QSize(25, 25)
        self.icons = {
            "not_run": ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_not_run).pixmap(icon_size),
            "pass": ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_pass).pixmap(icon_size),
            "warning": ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_warning).pixmap(icon_size),
            "fail": ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_fail_soft).pixmap(icon_size),
            "critical": ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_fail_hard).pixmap(icon_size),
        }

    def clear_validators(self):
        """
        Removes all validators from the model.
        Emits signals to update any connected views.
        """
        if not self.validators:
            return

        # Signal that the entire model is about to be reset
        self.beginResetModel()
        self.validators = []
        self.endResetModel()

    def add_validator(self, validator_instance):
        """
        Adds a single validator instance to the end of the model.

        Args:
            validator_instance (core_val.ValidatorBase): The instance to add.
        """
        # Get the index for the new row (which is the current count)
        new_row_index = len(self.validators)

        # Signal that we are about to insert a row
        self.beginInsertRows(
            ui_qt.QtCore.QModelIndex(),  # parent index (root)
            new_row_index,  # first new row
            new_row_index,  # last new row
        )

        # Add the data
        self.validators.append(validator_instance)

        # Signal that the insertion is complete
        self.endInsertRows()

    def order_validators(self):
        """
        Sorts the list of validators based on their status.

        Validators are sorted in reverse order of their status enum, placing
        failures and critical errors at the top.
        """
        self.validators.sort(key=lambda x: x.status, reverse=True)

    def rowCount(self, parent=ui_qt.QtCore.QModelIndex()):
        """
        Returns the number of rows in the model.

        Args:
            parent (ui_qt.QtCore.QModelIndex, optional): The parent index.
                Not used in this flat list model. Defaults to QModelIndex().

        Returns:
            int: The number of validators in the model.
        """
        return len(self.validators)

    def data(self, index, role=ui_qt.QtCore.Qt.DisplayRole):
        """
        Returns the data for a given item and role.

        Args:
            index (ui_qt.QtCore.QModelIndex): The index of the item to retrieve data for.
            role (int): The role for which data is being requested (e.g., DisplayRole,
                        DecorationRole).

        Returns:
            any: The data for the specified role, or None if the index is invalid
                 or the role is not handled.
        """
        if not index.isValid():
            return None
        val = self.validators[index.row()]
        if role == ui_qt.QtLib.ItemDataRole.DisplayRole:
            return val.name
        if role == ui_qt.QtCore.Qt.DecorationRole:
            if val.status == core_val.ValidatorStatus.PASS:
                return self.icons.get("pass")
            if val.status == core_val.ValidatorStatus.FAIL:
                return self.icons.get("fail")
            if val.status == core_val.ValidatorStatus.WARNING:
                return self.icons.get("warning")
            if val.status == core_val.ValidatorStatus.CRITICAL:
                return self.icons.get("critical")
            return self.icons.get("not_run")
        return None

    def get_selected_validator(self):
        """
        Retrieves the validator instance corresponding to the selected index.

        Returns:
            core_val.ValidatorBase: The currently selected validator instance,
                           or None if no valid item is selected.
        """
        if self.selected_index and self.selected_index.isValid():
            return self.validators[self.selected_index.row()]
        return None

    def reset_validators(self):
        """
        Resets the status of all validators to NOT_RUN.

        Emits layout change signals to update any connected views.
        """
        logging.debug("Resetting validators")
        self.layoutAboutToBeChanged.emit()
        for val in self.validators:
            if val.status != core_val.ValidatorStatus.NOT_RUN:
                val.status = core_val.ValidatorStatus.NOT_RUN
                val.check_message = ""
        self.order_validators()
        self.layoutChanged.emit()

    def run_validators(self):
        """
        Executes the `validate` method for all validators in the model.

        After running, it re-sorts the list and emits layout change
        signals to update views.
        """
        # Try to Keep Selection
        selection = []
        cmds_import = None
        try:
            import maya.cmds as cmds

            cmds_import = cmds
            selection = cmds.ls(selection=True, long=True) or []
        except Exception as e:
            logger.debug(e)

        logging.debug("Running validators")
        self.layoutAboutToBeChanged.emit()

        # Set the flag to prevent individual 'validate' wrappers
        # from emitting signals.
        self._is_batch_running = True
        try:
            for val in self.validators:
                val.validate(scope=self.scope)
        finally:
            # Always unset the flag
            self._is_batch_running = False

        self.order_validators()
        self.layoutChanged.emit()  # Emit one final signal for the batch

        # Restore Selection (If Available)
        if selection and cmds_import:
            import gt.core.iterable as core_iter

            existing_elements = core_iter.sanitize_maya_list(selection)
            cmds_import.select(existing_elements, replace=True)

    def all_validations_passed(self):
        """
        Checks if all validators in the model have a 'PASS' status.

        Returns:
            bool: True if all validators have a status of ValidatorStatus.PASS,
                  False otherwise (including if any are NOT_RUN, FAIL, etc.).
        """
        if not self.validators:
            return True  # An empty list is considered "passed"

        for val in self.validators:
            if val.status != core_val.ValidatorStatus.PASS:
                return False
        return True


class ValidatorWidget(ui_qt.QtWidgets.QWidget):
    """
    A Qt widget for displaying and interacting with a list of validators.

    This widget presents a list view of validators (using ValidatorModel)
    and a details area to show description, feedback, and action buttons
    (repair, select) for the selected validator.

    Args:
        validators (list[core_val.ValidatorBase] or ValidatorModel): A list of
            validator instances or a pre-built ValidatorModel.
        parent (ui_qt.QtWidgets.QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, validators, parent=None):
        """
        Initializes the ValidatorWidget.

        Args:
            validators (list[core_val.ValidatorBase] or ValidatorModel): A list of
                validator instances or a pre-built ValidatorModel.
            parent (ui_qt.QtWidgets.QWidget, optional): The parent widget.
                                                         Defaults to None.
        """
        super().__init__(parent=parent)
        self.setObjectName("ValidatorWidget")
        self.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)

        # List to store buttons that should only be enabled if all validations pass
        self.pass_restricted_buttons = []

        # Internal references for optional UI elements
        self.settings_container = None
        self.settings_layout = None
        self.scope_group = None
        self.scope_layout = None

        self.main_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.overlay_validator_results = ui_qt.QtWidgets.QHBoxLayout()
        self.splitter_validator_results = ui_qt.QtWidgets.QSplitter()

        if isinstance(validators, ValidatorModel):
            self.list_validator_model = validators
        elif isinstance(validators, list):
            self.list_validator_model = ValidatorModel(validators=validators, parent=self)

        self.icons = self.list_validator_model.icons  # For widget's legend

        self.list_validators = ui_qt.QtWidgets.QListView()
        self.list_validators.setModel(self.list_validator_model)
        self.overlay_validator_description = ui_qt.QtWidgets.QHBoxLayout()
        self.overlay_validator_description.setAlignment(ui_qt.QtCore.Qt.AlignTop | ui_qt.QtCore.Qt.AlignLeft)

        # --- Added Status layout ---
        self.overlay_validator_status = ui_qt.QtWidgets.QHBoxLayout()
        self.overlay_validator_status.setAlignment(ui_qt.QtCore.Qt.AlignTop | ui_qt.QtCore.Qt.AlignLeft)

        self.overlay_validator_buttons = ui_qt.QtWidgets.QHBoxLayout()
        self.overlay_validator_buttons.setAlignment(ui_qt.QtCore.Qt.AlignTop | ui_qt.QtCore.Qt.AlignLeft)
        self.overlay_validator_feedback = ui_qt.QtWidgets.QHBoxLayout()
        self.overlay_validator_feedback.setAlignment(ui_qt.QtCore.Qt.AlignTop | ui_qt.QtCore.Qt.AlignLeft)

        self.gbox_validator_details = ui_qt.QtWidgets.QGroupBox("Validation Details")

        self.scroll_area_results = ui_qt.QtWidgets.QScrollArea(self)
        self.scroll_area_results.setObjectName("ValidatorInfo")
        self.scroll_area_results.setWidgetResizable(True)
        self.scroll_area_results.setVerticalScrollBarPolicy(ui_qt.QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area_results.setHorizontalScrollBarPolicy(ui_qt.QtCore.Qt.ScrollBarAlwaysOff)

        result_area_widget = ui_qt.QtWidgets.QWidget()
        result_area_layout = ui_qt.QtWidgets.QVBoxLayout(result_area_widget)
        result_area_layout.setAlignment(ui_qt.QtCore.Qt.AlignTop)
        self.scroll_area_results.setWidget(result_area_widget)

        self.overlay_validator_details = ui_qt.QtWidgets.QVBoxLayout()
        self.gbox_validator_details.setLayout(self.overlay_validator_details)

        self.overlay_validator_details.addWidget(self.scroll_area_results)

        self.lab_details = ui_qt.QtWidgets.QLabel("Description:")
        self.label_description = ui_qt.QtWidgets.QLabel("")
        self.label_description.setWordWrap(True)
        self.label_description.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Minimum)
        self.overlay_validator_description.addWidget(self.lab_details)
        self.overlay_validator_description.addWidget(self.label_description)

        # --- Create Status widgets ---
        self.lab_status_label = ui_qt.QtWidgets.QLabel("Status:")
        self.lab_status_icon = ui_qt.QtWidgets.QLabel()
        self.lab_status_text = ui_qt.QtWidgets.QLabel("")
        self.overlay_validator_status.addWidget(self.lab_status_label)
        self.overlay_validator_status.addWidget(self.lab_status_icon)
        self.overlay_validator_status.addWidget(self.lab_status_text)
        self.overlay_validator_status.addStretch()

        self.label_fix_available = ui_qt.QtWidgets.QLabel("Actions:")
        self.repair_btn = ui_qt.QtWidgets.QPushButton("Repair")
        self.repair_btn.setEnabled(False)
        self.repair_btn.setVisible(False)

        self.select_button = ui_qt.QtWidgets.QPushButton("Select")
        self.select_button.setEnabled(False)
        self.select_button.setVisible(False)

        self.overlay_validator_buttons.addWidget(self.label_fix_available)
        self.overlay_validator_buttons.addWidget(self.repair_btn)
        self.overlay_validator_buttons.addWidget(self.select_button)

        self.lab_msg = ui_qt.QtWidgets.QLabel("Feedback:")
        self.label_feedback = ui_qt.QtWidgets.QLabel("")
        self.label_feedback.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.label_feedback.setWordWrap(False)
        self.overlay_validator_feedback.addWidget(self.lab_msg)
        self.overlay_validator_feedback.addWidget(self.label_feedback)

        # --- Add layouts to the inlined scroll area's layout ---
        self.scroll_area_results.widget().layout().addLayout(self.overlay_validator_description)
        self.scroll_area_results.widget().layout().addWidget(self.get_new_frame_line())
        # --- Add Status layout and a new line ---
        self.scroll_area_results.widget().layout().addLayout(self.overlay_validator_status)
        self.scroll_area_results.widget().layout().addWidget(self.get_new_frame_line())
        self.scroll_area_results.widget().layout().addLayout(self.overlay_validator_buttons)
        self.scroll_area_results.widget().layout().addWidget(self.get_new_frame_line())
        self.scroll_area_results.widget().layout().addLayout(self.overlay_validator_feedback)

        # --- Removed legend layout addition ---

        self.run_validations_btn = ui_qt.QtWidgets.QPushButton("Run Validations")
        self.splitter_validator_results.addWidget(self.list_validators)
        self.splitter_validator_results.addWidget(self.gbox_validator_details)
        self.splitter_validator_results.setSizes([1, 10])

        # --- Create layout for main buttons ---
        self.main_buttons_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.main_buttons_layout.addWidget(self.run_validations_btn)

        self.main_layout.addWidget(self.splitter_validator_results)
        self.main_layout.addLayout(self.main_buttons_layout)

        self.connect_ui()
        # Set initial state for pass-restricted buttons
        self._update_pass_restricted_buttons()

    @staticmethod
    def get_new_frame_line():
        """
        Creates a standard horizontal separator line.

        Returns:
            ui_qt.QtWidgets.QFrame: A QFrame configured as a sunken HLine.
        """
        line = ui_qt.QtWidgets.QFrame()
        line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        return line

    def connect_ui(self):
        """
        Connects widget signals to their corresponding slots.
        """
        self.list_validators.clicked.connect(self.list_validators_item_selected)
        self.run_validations_btn.clicked.connect(self.reset_validators)
        self.run_validations_btn.clicked.connect(self.run_validators)

        # Connect model layout changes to update button states
        self.list_validator_model.layoutChanged.connect(self._update_pass_restricted_buttons)

    def _update_pass_restricted_buttons(self):
        """
        Updates the enabled state of all buttons in self.pass_restricted_buttons.

        The state is based on whether all validations in the model have passed.
        """
        all_passed = self.list_validator_model.all_validations_passed()
        for button in self.pass_restricted_buttons:
            button.setEnabled(all_passed)

    def list_validators_item_selected(self, index):
        """
        Slot for handling selection changes in the validator list view.

        Updates the details area with the selected validator's information.
        Allows for deselection by clicking the same item again.

        Args:
            index (QModelIndex): The index of the clicked item.
        """
        if index != self.list_validators.model().selected_index:
            self.list_validators.model().selected_index = index
            self.update_validator_results()
        else:
            self.list_validators.model().selected_index = None
            self.clear_selection()

    def clear_selection(self):
        """
        Clears the selection in the list view and the model.
        """
        self.list_validators.model().selected_index = None
        self.list_validators.clearSelection()

    def reset_gui(self):
        """
        Resets the validator details area to its default empty state.
        """
        self.label_description.setText("")
        self.label_feedback.setText("")
        # --- Reset status widgets ---
        self.lab_status_icon.setPixmap(ui_qt.QtGui.QPixmap())  # Clear pixmap
        self.lab_status_text.setText("")
        self.lab_status_icon.setToolTip("")
        self.lab_status_text.setToolTip("")

        self.repair_btn.setToolTip("")
        self.repair_btn.setVisible(False)
        self.select_button.setToolTip("")
        self.select_button.setVisible(False)

    def reset_validators(self):
        """
        Resets the validator model and the GUI details area.
        """
        self.list_validator_model.reset_validators()
        self.clear_selection()
        self.reset_gui()

    def run_validators(self):
        """
        Triggers the validator model to run all validation checks.
        """
        self.list_validator_model.run_validators()

    def update_validator_results(self):
        """
        Updates the validator details area based on the currently selected validator.

        This method fetches the selected validator from the model, updates
        the description and feedback labels, and configures the visibility,
        text, and connections for the 'Repair' and 'Select' buttons.
        """
        self.list_validator_model.layoutAboutToBeChanged.emit()
        self.list_validator_model.order_validators()
        validator_instance = self.list_validator_model.get_selected_validator()
        if not validator_instance:
            return

        self.label_description.setText(validator_instance.description)
        self.label_feedback.setText(validator_instance.feedback)

        # ---  Update Status field ---
        status = validator_instance.status
        status_map = {
            core_val.ValidatorStatus.NOT_RUN: ("not_run", "Not Run", "The validation has not been run."),
            core_val.ValidatorStatus.PASS: ("pass", "Pass", "The validation has passed!"),
            core_val.ValidatorStatus.WARNING: ("warning", "Warning", "The validation has flagged a warning."),
            core_val.ValidatorStatus.FAIL: ("fail", "Fail", "The validation has failed."),
            core_val.ValidatorStatus.CRITICAL: ("critical", "Critical", "The validation has a critical failure!"),
        }

        icon_key, status_text, tooltip_text = status_map.get(status, ("not_run", "Unknown", "Unknown status"))
        icon_pixmap = self.list_validator_model.icons.get(icon_key)

        self.lab_status_icon.setPixmap(icon_pixmap)
        self.lab_status_text.setText(status_text)
        self.lab_status_icon.setToolTip(tooltip_text)
        self.lab_status_text.setToolTip(tooltip_text)

        # --- Disconnect repair_btn ---
        try:
            self.repair_btn.setEnabled(False)
            self.repair_btn.clicked.disconnect()
        except Exception as e:
            logger.debug(e)

        # --- Disconnect select_button ---
        try:
            self.select_button.setEnabled(False)
            self.select_button.clicked.disconnect()
        except Exception as e:
            logger.debug(e)

        if validator_instance.status != core_val.ValidatorStatus.CRITICAL and (
            validator_instance.status == core_val.ValidatorStatus.FAIL
            or validator_instance.status == core_val.ValidatorStatus.WARNING
        ):
            if validator_instance.is_repair_available():
                self.repair_btn.setEnabled(True)
                self.repair_btn.setVisible(True)
                self.repair_btn.setText("Repair")
                repair_doc = inspect.getdoc(validator_instance.repair)
                self.repair_btn.setToolTip(repair_doc or "No repair description given")
                self.repair_btn.clicked.connect(validator_instance.repair)
                self.repair_btn.clicked.connect(self.update_validator_results)
            else:
                self.repair_btn.setEnabled(False)
                self.repair_btn.setVisible(True)
                self.repair_btn.setText("No Repair")
                self.repair_btn.setToolTip("An automatic repair is not available for this issue.")

            if validator_instance.is_select_available():
                self.select_button.setEnabled(True)
                self.select_button.setVisible(True)
                self.select_button.setText("Select")
                select_doc = inspect.getdoc(validator_instance.select)
                self.select_button.setToolTip(select_doc or "Selects problematic components.")
                self.select_button.clicked.connect(validator_instance.select)
            else:
                self.select_button.setEnabled(False)
                self.select_button.setVisible(False)

        else:  # Catches PASS, CRITICAL, NOT_RUN
            self.repair_btn.setEnabled(False)
            self.repair_btn.setVisible(True)
            self.repair_btn.setText("No Repair")
            self.repair_btn.setToolTip("An automatic repair is not available.")
            self.select_button.setEnabled(False)
            self.select_button.setVisible(False)

        self.list_validator_model.layoutChanged.emit()

    def closeEvent(self, event):
        """
        Handles the widget's close event.
        Ensures the model is properly deleted to prevent memory leaks.

        Args:
            event (QCloseEvent): The close event.
        """
        self.list_validator_model.deleteLater()
        self.deleteLater()
        event.accept()

    def get_main_layout(self):
        """
        Returns the main layout of the widget.

        This is the top-level QVBoxLayout that contains the splitter and
        the main button layout.

        Returns:
            ui_qt.QtWidgets.QVBoxLayout: The main layout.
        """
        return self.main_layout

    def get_details_layout(self):
        """
        Returns the layout within the 'Validation Details' group box.

        This QVBoxLayout contains the icon legend and the scroll area
        for validator details.

        Returns:
            ui_qt.QtWidgets.QVBoxLayout: The layout for the details area.
        """
        return self.overlay_validator_details

    def get_main_buttons_layout(self):
        """
        Returns the layout at the bottom of the widget.

        This QVBoxLayout contains the 'Run Validations' button and any
        other buttons added via `add_button`.

        Returns:
            ui_qt.QtWidgets.QVBoxLayout: The layout for the main buttons.
        """
        return self.main_buttons_layout

    def get_or_create_settings_layout(self):
        """
        Ensures a 'settings' area exists above the main buttons (index 0).
        This allows multiple optional UI elements (scope, options) to exist in the same top area.

        Returns:
            ui_qt.QtWidgets.QHBoxLayout: The layout of the settings container.
        """
        if not self.settings_layout:
            self.settings_container = ui_qt.QtWidgets.QWidget()
            self.settings_container.setFixedHeight(80)
            self.settings_layout = ui_qt.QtWidgets.QHBoxLayout()
            self.settings_layout.setContentsMargins(0, 0, 0, 0)
            self.settings_layout.setSpacing(10)
            self.settings_container.setLayout(self.settings_layout)
            # Insert at index 0 so it sits above "Run Validations"
            self.main_buttons_layout.insertWidget(0, self.settings_container)
        return self.settings_layout

    def add_scope_selection_ui(self):
        """
        Adds the "Validation Scope" group box with Selection/Scene radio buttons.
        Updates the model scope when changed.
        """
        settings_layout = self.get_or_create_settings_layout()

        if self.scope_group:
            return  # Already added

        self.scope_group = ui_qt.QtWidgets.QGroupBox("Validation Scope")
        self.scope_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.scope_layout.setContentsMargins(10, 10, 10, 10)
        self.scope_layout.setAlignment(ui_qt.QtCore.Qt.AlignCenter)

        rb_sel = ui_qt.QtWidgets.QRadioButton("Selection")
        rb_scn = ui_qt.QtWidgets.QRadioButton("Scene")

        # Default to Scene as requested
        rb_scn.setChecked(True)
        self.list_validator_model.set_scope(core_val.ValidatorScope.SCENE)

        # Internal Logic to update model and reset
        def update_scope():
            """Updates Model scope"""
            new_scope = core_val.ValidatorScope.SELECTION if rb_sel.isChecked() else core_val.ValidatorScope.SCENE
            self.list_validator_model.set_scope(new_scope)
            self.reset_validators()

        rb_sel.toggled.connect(update_scope)

        self.scope_layout.addStretch()
        self.scope_layout.addWidget(rb_sel)
        self.scope_layout.addStretch()
        self.scope_layout.addWidget(rb_scn)
        self.scope_layout.addStretch()
        self.scope_group.setLayout(self.scope_layout)

        # Insert at the beginning (left) of the settings layout
        settings_layout.insertWidget(0, self.scope_group)

    def get_scope_layout(self):
        """
        Returns the layout of the 'Validation Scope' group box.
        Useful for adding more widgets to the scope area later.

        Returns:
            ui_qt.QtWidgets.QHBoxLayout: The layout inside the scope group box,
                                         or None if add_scope_selection_ui has not been called.
        """
        return self.scope_layout

    def add_button(self, text, function_to_run, run_only_if_all_passed=False):
        """
        Adds a new button to the main button layout, below 'Run Validations'.

        Args:
            text (str): The text to display on the button.
            function_to_run (callable): The function to execute when the
                                        button is clicked.
            run_only_if_all_passed (bool, optional): If True, the button will
                be disabled until all validators in the model have a 'PASS'
                status. Defaults to False.

        Returns:
            QPushButton: The newly created button.
        """
        new_button = ui_qt.QtWidgets.QPushButton(text)
        new_button.clicked.connect(function_to_run)

        self.main_buttons_layout.addWidget(new_button)

        if run_only_if_all_passed:
            self.pass_restricted_buttons.append(new_button)
            # Update its initial state
            new_button.setEnabled(self.list_validator_model.all_validations_passed())

        return new_button


if __name__ == "__main__":
    with ui_qt_utils.QtApplicationContext() as context:
        validator_window_instance = ui_qt.QtWidgets.QDialog(context.get_parent())
        validator_window_instance.setObjectName("ValidatorMainDialog")
        validator_window_instance.setWindowTitle("Validation Window Sample")
        validator_window_instance.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_validator))

        main_layout = ui_qt.QtWidgets.QVBoxLayout(validator_window_instance)
        main_layout.setContentsMargins(0, 0, 0, 0)

        def mocked_repair():
            """This is a mocked repair docstring"""
            print("Mocked repair button pressed.")

        def mocked_is_repair_available():
            """Mocked function used to force True result"""
            print('"is_repair_available" forced to return True')
            return True

        def mocked_select():
            """This is a mocked select docstring"""
            print("Mocked select button pressed.")

        def mocked_is_select_available():
            """Mocked function used to force True result"""
            print('"is_select_available" forced to return True')
            return True

        a_validators_list = []
        # Not Run
        validator_not_run = core_val.ValidatorBase(
            name="Val One: Not Run", description="This is the description for the 'Not Run' validator."
        )
        validator_not_run.status = core_val.ValidatorStatus.NOT_RUN
        validator_not_run.feedback = "Mocked Not Run Feedback..."
        a_validators_list.append(validator_not_run)
        # Pass
        validator_pass = core_val.ValidatorBase(
            name="Val Two: Pass",
            description="This is the description for the 'Pass' validator.",
        )
        validator_pass.status = core_val.ValidatorStatus.PASS
        validator_pass.feedback = "Mocked Pass Feedback..."
        a_validators_list.append(validator_pass)
        # Warning
        validator_warn = core_val.ValidatorBase(
            name="Val Three: Warning",
            description="This is the description for the 'Warning' validator.",
        )
        validator_warn.status = core_val.ValidatorStatus.WARNING
        validator_warn.feedback = "Mocked Warning Feedback..."
        validator_warn.is_select_available = mocked_is_select_available
        validator_warn.select = mocked_select
        a_validators_list.append(validator_warn)
        # Fail
        validator_fail = core_val.ValidatorBase(
            name="Val Four: Fail",
            description="This is the description for the 'Fail' validator. It has a repair.",
        )
        validator_fail.status = core_val.ValidatorStatus.FAIL
        validator_fail.feedback = "Mocked Fail Feedback..."
        validator_fail.is_repair_available = mocked_is_repair_available
        validator_fail.repair = mocked_repair
        a_validators_list.append(validator_fail)
        # Critical
        validator_critical = core_val.ValidatorBase(
            name="Val Five: Critical",
            description="This is the description for the 'Critical' validator.",
        )
        validator_critical.status = core_val.ValidatorStatus.CRITICAL
        validator_critical.feedback = "Mocked Critical Feedback..."
        a_validators_list.append(validator_critical)

        mocked_model = ValidatorModel(validators=a_validators_list, parent=None)
        main_widget = ValidatorWidget(validators=mocked_model, parent=validator_window_instance)

        # --- Test features ---
        # 1. Test adding the Scope UI
        main_widget.add_scope_selection_ui()

        # 2. Test adding a standard button
        main_widget.add_button(
            text="Export Log", function_to_run=lambda: print("--- Exporting Log ---"), run_only_if_all_passed=False
        )

        # 3. Test adding a button that requires all validations to pass
        main_widget.add_button(
            text="Submit Asset (Pass Only)",
            function_to_run=lambda: print("--- Submitting Asset ---"),
            run_only_if_all_passed=True,
        )

        # 4. Test adding a widget to one of the "areas"
        test_label = ui_qt.QtWidgets.QLabel("--- Custom Widget Area ---")
        test_label.setFixedHeight(20)
        test_label.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        main_widget.get_main_buttons_layout().insertWidget(0, test_label)  # Insert at top of button list

        main_layout.addWidget(main_widget)
        validator_window_instance.resize(800, 700)
        validator_window_instance.show()

        # --- EXTERNAL TESTS ---
        def test_model_run():
            """Tests running all validators via the model method."""
            print("\n--- (TIMER 1) RUNNING ALL VALIDATORS VIA model.run_validators() ---")
            mocked_model.run_validators()
            print("--- (TIMER 1) MODEL RUN COMPLETE ---")

        def test_external_run():
            """Tests running a single validator 'externally'."""
            print(f"\n--- (TIMER 2) RUNNING '{a_validators_list[0].name}' EXTERNALLY ---")
            a_validators_list[0].validate()
            print("--- (TIMER 2) EXTERNAL RUN COMPLETE ---")

        def test_reset_run():
            """Resets all validators to Not Run."""
            print(f"\n--- (TIMER 0) RESETTING VALIDATORS ---")
            mocked_model.reset_validators()
            print("--- (TIMER 0) RESET COMPLETE ---")

        def test_setter_behavior():
            """Tests turning the external refresh behavior off and on."""
            print("\n--- (TIMER 3) DISABLING external refresh ---")
            mocked_model.set_refresh_on_external_run(False)

            print(f"--- (TIMER 3) RUNNING '{a_validators_list[1].name}' EXTERNALLY (UI should NOT refresh) ---")
            a_validators_list[1].validate()
            print("--- (TIMER 3) RUN 1 COMPLETE ---")

            ui_qt.QtCore.QTimer.singleShot(2000, test_setter_re_enable)

        def test_setter_re_enable():
            print("\n--- (TIMER 4) RE-ENABLING external refresh ---")
            mocked_model.set_refresh_on_external_run(True)

            print(f"--- (TIMER 4) RUNNING '{a_validators_list[2].name}' EXTERNALLY (UI SHOULD refresh) ---")
            a_validators_list[2].validate()
            print("--- (TIMER 4) RUN 2 COMPLETE ---")

        # Uncomment to run timer tests
        # ui_qt.QtCore.QTimer.singleShot(1000, test_reset_run)
        # ui_qt.QtCore.QTimer.singleShot(2000, test_model_run)
        #
        # # Schedule the tests to run in sequence after the UI is live
        # # You will see the UI update at each step.
        # ui_qt.QtCore.QTimer.singleShot(1000, test_reset_run)  # At 1 sec, reset
        # ui_qt.QtCore.QTimer.singleShot(2000, test_model_run)  # At 2 sec, run all (as requested)
        # ui_qt.QtCore.QTimer.singleShot(4000, test_reset_run)  # At 4 sec, reset again
        # ui_qt.QtCore.QTimer.singleShot(5000, test_external_run)  # At 5 sec, run one (to test wrapper)
        # ui_qt.QtCore.QTimer.singleShot(7000, test_reset_run)  # At 7 sec, reset again
        # # At 8 sec, test setter (this will schedule Timer 4 to run at 10 sec)
        # ui_qt.QtCore.QTimer.singleShot(8000, test_setter_behavior)
