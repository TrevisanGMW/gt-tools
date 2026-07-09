"""
Auto Rigger Capture Base Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBaseCapture(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.store_btn = None  # Created by "add_persp_camera_data_buttons"
        self.apply_btn = None  # Created by "add_persp_camera_data_buttons"
        self.edit_btn = None  # Created by "add_persp_camera_data_buttons"
        self.clear_btn = None  # Created by "add_persp_camera_data_buttons"

    def add_persp_camera_data_buttons(self, label="Use Persp Data:", layout=None):
        """
        Add buttons used to set data for the perspective camera.
        It's expected that the module have two variables, one called "use_camera_data" and the other one "camera_data".
        "use_camera_data" determines if the data is used or ignored during build.
        "camera_data" is used for the actual data, transform and properties.
        Args:
            label (str, optional): Defines the text found to the left of the activation checkbox.
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
        Returns:
            QComboBox: The created combobox.
        """
        _minimum_width = 130  # Minimum width for the buttons

        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)

        # Label
        _layout.addStretch()
        _checkbox_layout = ui_qt.QtWidgets.QHBoxLayout()
        _label = ui_qt.QtWidgets.QLabel(label)
        _checkbox_layout.addWidget(_label)
        # Using Data?
        checkbox = ui_qt.QtWidgets.QCheckBox()
        attr_value = getattr(self.module, "use_camera_data")
        checkbox.setChecked(attr_value)
        _checkbox_layout.addWidget(checkbox)
        checkbox.stateChanged.connect(self.on_checkbox_use_cam_data_changed)
        _layout.addLayout(_checkbox_layout)

        btn_layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.addLayout(btn_layout)

        # Store Button
        self.store_btn = ui_qt.QtWidgets.QPushButton("Get")
        self.store_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        self.store_btn.clicked.connect(self.cam_data_store)
        self.store_btn.setToolTip(
            "Stores the data (transform and properties) for the perspective (persp) camera.\n"
            "The camera is then set to this exact values when the apply function is called.\n"
            "When button is green, data is stored. When gray, data is not stored."
        )
        self.store_btn.setMinimumWidth(_minimum_width)
        btn_layout.addWidget(self.store_btn)

        # Apply Button
        self.apply_btn = ui_qt.QtWidgets.QPushButton("Apply")
        self.apply_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        self.apply_btn.clicked.connect(self.cam_data_apply)
        self.apply_btn.setToolTip("Applies the stored camera data for the perspective (persp) camera.")
        self.apply_btn.setMinimumWidth(_minimum_width)
        btn_layout.addWidget(self.apply_btn)

        # Edit Button
        self.edit_btn = ui_qt.QtWidgets.QPushButton("Edit")
        self.edit_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_edit))
        self.edit_btn.clicked.connect(self.cam_data_edit)
        self.edit_btn.setToolTip(
            "Opens a window with the stored camera data (dictionary) for the perspective (persp) camera."
        )
        self.edit_btn.setMinimumWidth(_minimum_width)
        btn_layout.addWidget(self.edit_btn)

        # Clear Button
        self.clear_btn = ui_qt.QtWidgets.QPushButton("Clear")
        self.clear_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        self.clear_btn.clicked.connect(self.cam_data_clear)
        self.clear_btn.setToolTip("Clears the data (transform and properties) for the perspective (persp) camera.")
        self.clear_btn.setMinimumWidth(_minimum_width)
        btn_layout.addWidget(self.clear_btn)
        _layout.addStretch()

    def refresh_camera_buttons_enabled_state(self):
        """
        Updates the color and enabled state of the camera buttons according to the stored data.
        """
        is_using_cam_data = self.module.use_camera_data
        if not is_using_cam_data:
            self.store_btn.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
        else:  # Using, so determine what should be active
            cam_data = self.module.camera_data
            if cam_data:  # Already has data set
                self.apply_btn.setEnabled(True)
                self.edit_btn.setEnabled(True)
                self.clear_btn.setEnabled(True)
                self.store_btn.setEnabled(False)
            else:  # Ready to set initial data
                self.apply_btn.setEnabled(False)
                self.edit_btn.setEnabled(False)
                self.clear_btn.setEnabled(False)
                self.store_btn.setEnabled(True)

    def on_checkbox_use_cam_data_changed(self, state):
        """
        Determines if the camera data is used or ignored.
        Args:
            state (bool, int): If True, the camera data is used and this value is stored in the module.
                               The UI is also updated to reflect  the use of the camera data.
        """
        _state = bool(state)
        self.module.use_camera_data = _state
        self.refresh_camera_buttons_enabled_state()

    def cam_data_store(self):
        """
        Stores the persp camera data as it is at the moment in the scene.
        """
        import gt.core.camera as core_cam

        camera_name = getattr(self.module, "camera_name", "persp")  # Defined camera_name value, or "persp"
        camera_data = core_cam.get_camera_data(camera_name=camera_name)
        if camera_data:
            self.module.camera_data = camera_data
            logger.info(f"Camera Data was stored.")
            self.refresh_camera_buttons_enabled_state()
        else:
            logger.warning('Unable to retrieve camera data. "get_camera_data() returned an empty dictionary."')

    def cam_data_apply(self):
        """
        Applies the stored camera data to the current scene. (Persp camera)
        """
        import gt.core.camera as core_cam

        if self.module.camera_data:
            core_cam.apply_camera_data(data=self.module.camera_data)
            logger.info(f"Camera Data was applied.")

    def cam_data_edit(self):
        """
        Opens a window for the user to edit the camera data manually. (As a dictionary)
        """
        camera_data = self.module.camera_data

        module_name = self.module.get_name()
        if not module_name:
            module_name = self.module.get_module_class_name(remove_module_prefix=True)
        _message = f'Editing Camera Data found in "{module_name}"'
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=_message,
            window_title=f'Camera Data for "{module_name}"',
            image=ui_res_lib.Icon.dev_code,
            window_icon=ui_res_lib.Icon.dev_code,
            image_scale_pct=15,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")

        formatted_dict = core_iter.dict_as_formatted_str(camera_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.set_camera_data_from_editor, data_getter=param_win.get_text_field_text)
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.confirm_button.clicked.connect(param_win.close_window)
        param_win.show()

    def cam_data_clear(self):
        """
        Clears the camera data from the module in case the user no longer wants to use it.
        """
        self.module.camera_data = {}
        self.refresh_camera_buttons_enabled_state()
        logger.info(f"Camera Data was cleared.")

    def set_camera_data_from_editor(self, data_getter):
        """
        Updates the camera data dictory used to set the transforms and property of the persp camera.
        Args:
            data_getter (callable): A function used to retrieve the data string from the editor window.
        """
        data = data_getter()
        self.module.camera_data = data
        logger.info(f"Camera Data was updated.")
