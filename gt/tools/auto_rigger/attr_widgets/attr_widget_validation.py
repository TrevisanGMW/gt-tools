"""
Auto Rigger Validation Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleValidation(AttrWidget):
    """
    Attribute widget for the ModuleValidation auto-rigger module.

    Provides a button to open an editor for selecting which
    validations to run. Contains a private nested dialog class
    for the editor.
    """

    # --- Nested Dialog Class ---
    class _ValidatorEditDialog(ui_qt.QtWidgets.QDialog):
        """
        A modal dialog for editing the list of active validators.

        This UI presents a checkable list of all available validators from
        the ValidatorLibrary and updates the provided module instance on confirm.

        Args:
            module (module_validation.ModuleValidation): The backend validation
                module instance to modify.
            parent (ui_qt.QtWidgets.QWidget, optional): The parent widget.
        """

        def __init__(self, module, parent=None):
            """
            Initializes a dialog for selecting active validators
            Args:
                module (ModuleGeneric): The module to be updated with validators list.
                parent (QWidget, optional): The parent of this Qt dialog.
            """
            super().__init__(parent)

            # Store the backend module
            self.module = module

            self.setWindowTitle("Edit Validators")
            self.setMinimumWidth(350)
            self.setMinimumHeight(450)

            main_layout = ui_qt.QtWidgets.QVBoxLayout(self)

            # --- Instructions Label ---
            info_label = ui_qt.QtWidgets.QLabel("Select the validations to run for this rig:")
            main_layout.addWidget(info_label)

            # --- List Widget ---
            self.list_widget = ui_qt.QtWidgets.QListWidget()
            main_layout.addWidget(self.list_widget)

            self.populate_validator_list()

            # --- Button Layout ---
            button_layout = ui_qt.QtWidgets.QHBoxLayout()
            button_layout.addStretch()

            self.confirm_btn = ui_qt.QtWidgets.QPushButton("Confirm")
            self.confirm_btn.clicked.connect(self.on_confirm)
            button_layout.addWidget(self.confirm_btn)

            self.cancel_btn = ui_qt.QtWidgets.QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self.reject)  # Standard "close" slot
            button_layout.addWidget(self.cancel_btn)

            main_layout.addLayout(button_layout)

        def populate_validator_list(self):
            """
            Fetches all validators from the library and checks the ones
            currently active in the module.
            """
            self.list_widget.clear()

            try:
                # Get the list of names currently in the module
                current_validators = self.module.get_validation_list()
                # Get all available validator names from the library
                import gt.core.validator as core_val

                all_validators = core_val.ValidatorLibrary.get_available_validators()
            except Exception as e:
                logger.error(f"Failed to get validators from ValidatorLibrary: {e}")
                error_item = ui_qt.QtWidgets.QListWidgetItem("Error loading validators!")
                self.list_widget.addItem(error_item)
                return

            for validator_name in all_validators:
                item = ui_qt.QtWidgets.QListWidgetItem(validator_name)
                # Make the item check-able
                item.setFlags(item.flags() | ui_qt.QtCore.Qt.ItemIsUserCheckable)

                # Set its state based on the module's list
                if validator_name in current_validators:
                    item.setCheckState(ui_qt.QtCore.Qt.Checked)
                else:
                    item.setCheckState(ui_qt.QtCore.Qt.Unchecked)

                self.list_widget.addItem(item)

        def on_confirm(self):
            """
            Gathers the checked items, updates the module, and closes.
            """
            new_validation_list = []
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.checkState() == ui_qt.QtCore.Qt.Checked:
                    new_validation_list.append(item.text())

            # Update the backend module
            self.module.set_validation_list(new_validation_list)

            # Standard "OK" slot
            self.accept()

    # --- AttrWidgetModuleValidation Implementation ---

    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the ModuleValidation.

        Args:
            parent (ui_qt.QtWidgets.QWidget, optional): The parent widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.validator_widget_instance = None

        self.add_widget_module_header()

        setup_layout = ui_qt.QtWidgets.QHBoxLayout()

        self.edit_validators_btn = ui_qt.QtWidgets.QPushButton("Edit Validators")
        self.edit_validators_btn.setToolTip("Open a dialog to select which validators to run.")
        self.edit_validators_btn.clicked.connect(self.open_validator_dialog)

        setup_layout.addWidget(self.edit_validators_btn)

        self.add_widget_code_data_editor(
            add_activation=False, add_order_editor=True, add_code_editor=False, layout=setup_layout
        )

        self.content_layout.addLayout(setup_layout)

        # Initial population
        self.refresh_active_list()

    def refresh_active_list(self):
        """
        Updates the UI by destroying the old ValidatorWidget (if any)
        and creating a new one with the module's current model.
        """
        if self.validator_widget_instance:
            self.content_layout.removeWidget(self.validator_widget_instance)
            self.validator_widget_instance.deleteLater()
            self.validator_widget_instance = None

        model = self.module.get_validation_model(force_rebuild=True)

        import gt.ui.validator_widget as ui_validator

        if not model or not model.validators:
            # If no validators, show a label
            self.validator_widget_instance = ui_qt.QtWidgets.QLabel("No validators selected.")
            self.validator_widget_instance.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        else:
            # Create the full widget
            self.validator_widget_instance = ui_validator.ValidatorWidget(validators=model)

        self.content_layout.addWidget(self.validator_widget_instance, 1)

    def open_validator_dialog(self):
        """
        Opens the modal dialog to edit the validator list.
        """
        dialog = self._ValidatorEditDialog(module=self.module, parent=self)

        # Run the dialog modally (blocks until confirmed or canceled)
        result = dialog.exec_()

        # If the user clicked "Confirm"
        if result == ui_qt.QtWidgets.QDialog.Accepted:
            # The dialog already updated the module,
            # so we just refresh this widget's display.
            self.refresh_active_list()


# -------------------------------------------------- Project ---------------------------------------------------
