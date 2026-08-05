"""
Auto Rigger Attr Widgets
"""

import gt.tools.auto_rigger.rigger_orient_view as tools_rig_orient_view
import gt.tools.auto_rigger.rig_modules as tools_rig_modules
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.input_window_text as ui_input_window_text
import gt.ui.resource_library as ui_res_lib
import gt.ui.file_dialog as ui_file_dialog
import gt.utils.system as utils_system
import gt.core.session as core_session
import gt.ui.qt_utils as ui_qt_utils
import gt.core.iterable as core_iter
import gt.core.naming as core_naming
import gt.core.prefs as core_prefs
import gt.core.color as core_color
import gt.ui.qt_import as ui_qt
import gt.core.str as core_str
import gt.core.io as core_io
from functools import partial
import textwrap
import logging
import inspect
import ast
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --------------------------------------------------- Base ---------------------------------------------------
class AttrWidget(ui_qt.QtWidgets.QWidget):
    """
    Base Widget for managing attributes of a module.
    """

    DATA_ROLE = ui_qt.QtLib.ItemDataRole.UserRole
    PROXY_ROLE = ui_qt.QtLib.ItemDataRole.UserRole + 1
    PARENT_ROLE = ui_qt.QtLib.ItemDataRole.UserRole + 2

    def __init__(self, parent=None, module=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """
        Initialize the AttrWidget.

        Args:
            parent (QWidget): The parent widget.
            module (ModuleGeneric): The module associated with this widget.
            project (RigProject): The project associated with this widget.
            refresh_parent_func (callable): A function used to refresh the widget's parent.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        # Basic Variables
        self.project = project
        self.module = module
        self.known_proxies = {}  # Used to populate drop-down lists
        self.table_proxy_basic_wdg = None
        self.table_proxy_parent_wdg = None
        self.mod_name_field = None
        self.mod_prefix_field = None
        self.mod_suffix_field = None
        self.mod_orient_method = None
        self.mod_edit_orient_btn = None
        self.refresh_parent_func = None

        if refresh_parent_func:
            self.set_refresh_parent_func(refresh_parent_func)

        # Content Layout
        self.content_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        # Create Layout
        self.scroll_content_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        self.scroll_content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.scroll_content_layout.addLayout(self.content_layout)

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_widget_separator_line(self, label_text="", parent_layout=None, tooltip=None):
        """
        Creates a separator in the UI. Made of QFrames.
        Args:
            label_text (str, optional): The text to appear in the middle of the QFrames (lines)
                                        If not provided it will become a soline line.
            parent_layout (QBoxLayout, optional): If provided, this is used as parent instead of the  content layout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
        """
        _parent_layout = self.content_layout
        if parent_layout:
            _parent_layout = parent_layout
        # Create and Add Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        _parent_layout.addLayout(_layout)

        left_line = ui_qt.QtWidgets.QFrame()
        left_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)  # Horizontal line
        left_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)  # Optional shado
        _layout.addWidget(left_line, 1)  # Stretch factor of 1 for left line

        # Create the label
        label = ui_qt.QtWidgets.QLabel(label_text)
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
        label.setStyleSheet("color: grey; padding: 0 8px;")  # Add padding for spacing
        _layout.addWidget(label, 0)  # No stretch factor for the label

        right_line = ui_qt.QtWidgets.QFrame()
        right_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)  # Horizontal line
        right_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)  # Optional shado
        _layout.addWidget(right_line, 1)  # Stretch factor of 1 for right line

        if tooltip and isinstance(tooltip, str):
            left_line.setToolTip(tooltip)
            label.setToolTip(tooltip)
            right_line.setToolTip(tooltip)

        _parent_layout.addLayout(_layout)

    def add_widget_module_header(self, activation=True):
        """
        Adds the header for controlling a module. With Icon, Type, Name and modify buttons.
        Args:
            activation (bool, optional): Includes a checkbox to be used as module activation.
        """
        # Module Header (Icon, Type, Name, Buttons)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        _layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        # Active Checkbox
        if activation:
            active_chk = ui_qt.QtWidgets.QCheckBox()
            active_chk.setChecked(self.module.is_active())
            active_chk.setStyleSheet("QCheckBox { spacing: 0px; }")
            active_chk.setToolTip("Module Active State")
            active_chk.stateChanged.connect(self.on_checkbox_active_state_changed)
            _layout.addWidget(active_chk)

        # Icon
        icon = ui_qt.QtGui.QIcon(self.module.icon)
        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        label_tooltip = self.module.get_module_class_name(remove_module_prefix=True, formatted=True, remove_side=True)
        icon_label.setToolTip(label_tooltip)
        _layout.addWidget(icon_label)

        # Type (Module Class)
        module_type = self.module.get_module_class_name(remove_module_prefix=True, formatted=True, remove_side=False)
        _layout.addWidget(ui_qt.QtWidgets.QLabel(f"{module_type}"))

        # Name (User Custom)
        name = self.module.get_name()
        self.mod_name_field = ui_qt_utils.ConfirmableQLineEdit()
        self.mod_name_field.setPlaceholderText(f"<{module_type}>")
        self.mod_name_field.setFixedHeight(35)
        if name:
            self.mod_name_field.setText(name)
        self.mod_name_field.editingFinished.connect(self.set_module_name)
        _layout.addWidget(self.mod_name_field)

        # Edit Button
        edit_mod_btn = ui_qt.QtWidgets.QPushButton()
        edit_mod_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        edit_mod_btn.setToolTip("Edit Raw Data")
        edit_mod_btn.clicked.connect(self.on_button_edit_module_clicked)
        _layout.addWidget(edit_mod_btn)
        self.content_layout.addLayout(_layout)

        # Delete Button
        delete_mod_btn = ui_qt.QtWidgets.QPushButton()
        delete_mod_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        delete_mod_btn.clicked.connect(self.delete_module)
        _layout.addWidget(delete_mod_btn)

    def add_widget_module_prefix_suffix(self):
        """
        Adds widgets to control the prefix of the module
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        # Prefix
        prefix_label = ui_qt.QtWidgets.QLabel("Prefix:")
        prefix_label.setFixedWidth(50)
        self.mod_prefix_field = ui_qt_utils.ConfirmableQLineEdit()
        self.mod_prefix_field.setPlaceholderText("<Prefix>")
        self.mod_prefix_field.setFixedHeight(35)
        _layout.addWidget(prefix_label)
        _layout.addWidget(self.mod_prefix_field)
        prefix = self.module.get_prefix()
        self.mod_prefix_field.textChanged.connect(self.set_module_prefix)
        if prefix:
            self.mod_prefix_field.setText(prefix)
        # Suffix
        suffix_label = ui_qt.QtWidgets.QLabel("Suffix:")
        suffix_label.setFixedWidth(50)
        self.mod_suffix_field = ui_qt_utils.ConfirmableQLineEdit()
        self.mod_suffix_field.setPlaceholderText("<Suffix>")
        self.mod_suffix_field.setFixedHeight(35)
        _layout.addWidget(suffix_label)
        _layout.addWidget(self.mod_suffix_field)
        suffix = self.module.get_suffix()
        if suffix:
            self.mod_suffix_field.setText(suffix)
        self.mod_suffix_field.textChanged.connect(self.set_module_suffix)
        self.content_layout.addLayout(_layout)

    def add_widget_module_orientation(self):
        """
        Adds widgets to control the module orientation
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        # Prefix
        orient_label = ui_qt.QtWidgets.QLabel("Orientation Method:")
        orient_label.setFixedWidth(170)
        self.mod_orient_method = ui_qt.QtWidgets.QComboBox()
        self.mod_orient_method.setFixedHeight(35)

        orientation_data = self.module.get_orientation_data()
        for method in orientation_data.get_available_methods():
            self.mod_orient_method.addItem(str(method).capitalize())

        self.mod_edit_orient_btn = ui_qt.QtWidgets.QPushButton("Edit Orientation Data")
        self.mod_edit_orient_btn.setFixedHeight(35)

        _layout.addWidget(orient_label)
        _layout.addWidget(self.mod_orient_method)
        _layout.addWidget(self.mod_edit_orient_btn)
        self.mod_orient_method.currentIndexChanged.connect(self.on_orientation_combobox_change)
        self.mod_edit_orient_btn.clicked.connect(self.on_orientation_edit_clicked)

        # Update Initial State:
        _method = self.module.get_orientation_method()
        _method_capitalize = _method.capitalize()
        index = self.mod_orient_method.findText(_method_capitalize)
        if index == -1:  # Add missing items (just in case)
            self.mod_orient_method.addItem(_method_capitalize)
            index = self.mod_orient_method.findText(_method_capitalize)
            logger.warning(f'Method "{_method_capitalize}" was not available as an option but was force added.')
        self.mod_orient_method.setCurrentIndex(index)

        self.content_layout.addLayout(_layout)

    def add_widget_module_parent(self):
        """
        Adds a widget to control the parent of the module
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.refresh_known_proxy_dict(ignore_list=self.module.get_proxies())
        parent_label = ui_qt.QtWidgets.QLabel("Parent:")
        parent_label.setFixedWidth(60)
        module_parent_combo_box = self.create_widget_parent_combobox(target=self.module)
        _layout.addWidget(parent_label)
        _layout.addWidget(module_parent_combo_box)
        module_parent_combo_box.setMinimumSize(1, 1)
        combo_func = partial(self.on_parent_combo_box_changed, combobox=module_parent_combo_box)
        module_parent_combo_box.currentIndexChanged.connect(combo_func)
        self.content_layout.addLayout(_layout)

    def add_widget_proxy_parent_table(self, table_minimum_height=250):
        """
        Adds a table widget to control proxies with options to determine parent or delete the proxy
        Args:
            table_minimum_height (int): The minimum height of the created table
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        # Setup Table
        self.table_proxy_parent_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_proxy_parent_table()
        columns = [
            "",
            "Prefix",
            "Name",
            "Suffix",
            "Parent",
            "",
            "",
        ]  # Icon, Prefix, Name, Suffix, Parent, Edit, Delete
        self.table_proxy_parent_wdg.setColumnCount(len(columns))
        self.table_proxy_parent_wdg.setHorizontalHeaderLabels(columns)
        header_view = ui_qt_utils.QHeaderWithWidgets()
        self.table_proxy_parent_wdg.setHorizontalHeader(header_view)
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Interactive)
        header_view.setSectionResizeMode(3, ui_qt.QtLib.QHeaderView.Interactive)
        header_view.setSectionResizeMode(4, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(5, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(6, ui_qt.QtLib.QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_proxy_parent_wdg)
        self.table_proxy_parent_wdg.setColumnWidth(1, 110)
        self.table_proxy_parent_wdg.setMinimumHeight(table_minimum_height)
        self.refresh_proxy_parent_table()
        self.table_proxy_parent_wdg.cellChanged.connect(self.on_proxy_parent_table_cell_changed)
        # Add Inherit Placeholder (Prefix/Suffix)
        delegate = ui_qt_utils.TablePlaceholderDelegate(
            "<inherit>",
            target_columns=[1, 3],  # Prefix, Name, Suffix,
            placeholder_color=ui_qt.QtGui.QColor(100, 100, 100),
            placeholder_alignment=ui_qt.QtLib.AlignmentFlag.AlignCenter,
        )
        self.table_proxy_parent_wdg.setItemDelegate(delegate)
        # Adjust Width
        prefix_idx = 1
        suffix_idx = 3
        ui_qt_utils.set_table_column_width_by_text(self.table_proxy_parent_wdg, prefix_idx, columns[prefix_idx], 3)
        ui_qt_utils.set_table_column_width_by_text(self.table_proxy_parent_wdg, suffix_idx, columns[suffix_idx], 4)

        add_proxy_btn = ui_qt.QtWidgets.QPushButton()
        add_proxy_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_proxy_btn.clicked.connect(self.on_button_add_proxy_clicked)
        add_proxy_btn.setToolTip("Add New Proxy")
        header_view.add_widget(6, add_proxy_btn)
        self.content_layout.addLayout(_layout)

    def add_widget_proxy_basic_table(self):
        """
        Adds a table widget to control the parent of the proxies inside this proxy
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        self.table_proxy_basic_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_proxy_basic_table()
        columns = ["", "Name", ""]  # Icon, Name, Edit
        self.table_proxy_basic_wdg.setColumnCount(len(columns))
        self.table_proxy_basic_wdg.setHorizontalHeaderLabels(columns)
        header_view = self.table_proxy_basic_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_proxy_basic_wdg)
        self.table_proxy_basic_wdg.setColumnWidth(1, 110)
        self.refresh_proxy_basic_table()
        self.table_proxy_basic_wdg.cellChanged.connect(self.on_proxy_basic_table_cell_changed)
        self.content_layout.addLayout(_layout)

    def add_widget_action_buttons(self):
        """
        Adds actions buttons (read proxy, build proxy, etc…)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Build Module Proxy
        build_mod_proxy_btn = ui_qt.QtWidgets.QPushButton("Build Proxy (This Module Only)")
        build_mod_proxy_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        build_mod_proxy_btn.clicked.connect(self.on_button_build_mod_proxy_clicked)
        build_mod_proxy_btn.setToolTip("Read Scene Data")
        _layout.addWidget(build_mod_proxy_btn)
        # Read Scene Data
        read_scene_data_btn = ui_qt.QtWidgets.QPushButton("Read Scene Data")
        read_scene_data_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_parameters))
        read_scene_data_btn.clicked.connect(self.on_button_read_scene_data_clicked)
        read_scene_data_btn.setToolTip("Read Scene Data")
        _layout.addWidget(read_scene_data_btn)
        self.scroll_content_layout.addLayout(_layout)

    def add_widget_code_data_editor(
        self, add_activation=False, add_order_editor=True, add_code_editor=False, layout=None
    ):
        """
        Add widgets necessary do edit the code data of a module
        Args:
            add_activation (bool, optional): If True, it adds a checkbox to active or deactivate the code data.
            add_order_editor (bool, optional): If True, it adds a combobox to allow for order selection.
            add_code_editor (bool, optional): If True, it adds a button to allow the user to edit the code data.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
        """
        # Get Basic Items
        code_data = self.module.get_code_data()
        is_code_data_available = isinstance(code_data, tools_rig_frm.CodeData)
        order_list = tools_rig_frm.CodeData.get_available_order_items()

        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)

        checkbox = None
        if add_activation:
            # Activation (Has CodeData?)
            label_activation = ui_qt.QtWidgets.QLabel(f"Run Code:")
            label_activation.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
            checkbox = ui_qt.QtWidgets.QCheckBox()
            checkbox.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
            _layout.addWidget(label_activation)
            _layout.addWidget(checkbox)

        combobox = None
        if add_order_editor:
            # Order Combobox
            _label = "Order:"
            if not add_activation:
                _label = f"Code {_label}"
            label_order = ui_qt.QtWidgets.QLabel(_label)
            label_order.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
            combobox = ui_qt_utils.ColorTextComboBox()
            combobox.setFixedHeight(30)
            combobox.addItems(order_list)
            _layout.addWidget(label_order)
            _layout.addWidget(combobox)
            _func = partial(self.on_combobox_code_data_order_changed)
            combobox.currentTextChanged.connect(_func)
            # Add Warning Color to Missing Steps -----------------------------------------
            is_pose_active = self.project.get_preferences_dict_value(key="apply_control_rig_pose", default=False)
            if not is_pose_active:
                tooltip = "This execution order is not included in build preferences."
                combobox.set_tooltip(tooltip, lambda text: "control_pose" in text)
                warning_list = [s for s in order_list if s.endswith("control_pose")]  # Get Control Pose
                for item in warning_list:
                    index = combobox.findText(item)
                    color = ui_res_lib.parse_rgb_numbers(ui_res_lib.Color.RGB.red_metallic_dark)
                    combobox.set_item_color(index, ui_qt.QtGui.QColor(*color))
            # Set Initial Value -----------------------------------------
            if is_code_data_available:
                current_value = code_data.get_order()
                index = combobox.findText(current_value)
                if index == -1:  # Add missing items (just in case)
                    combobox.addItem(current_value)
                    index = combobox.findText(current_value)
                    logger.warning(f'Item "{current_value}" was not available as an order but was force added.')
                combobox.setCurrentIndex(index)
            if checkbox:
                checkbox.stateChanged.connect(label_order.setEnabled)
                checkbox.stateChanged.connect(combobox.setEnabled)

        edit_code_btn = None
        if add_code_editor:
            # Code Editor
            edit_code_btn = ui_qt.QtWidgets.QPushButton(" Edit CodeData")
            edit_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
            _layout.addWidget(edit_code_btn)
            _func = partial(self.open_module_attr_code_data_editor)
            edit_code_btn.clicked.connect(_func)
            if checkbox:
                checkbox.stateChanged.connect(edit_code_btn.setEnabled)

        # Initial State
        if checkbox:
            if code_data:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
                if edit_code_btn:
                    edit_code_btn.setEnabled(False)
                if combobox:
                    combobox.setEnabled(False)
            _func = partial(self.on_checkbox_code_data_active_changed, checkbox=checkbox, combobox=combobox)
            checkbox.toggled.connect(_func)

    def add_module_attr_widget_text_field(
        self, attr_name, attr_value=None, nice_name=None, placeholder=None, layout=None, tooltip=None
    ):
        """
        Creates a module attribute text field widget.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        if tooltip and isinstance(tooltip, str):
            label.setToolTip(tooltip)
            text_field.setToolTip(tooltip)
        return text_field

    def add_module_attr_widget_path(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        placeholder=None,
        layout=None,
        ok_caption="Set Path",
        file_filter="All Files (*);;JSON Files (*.json)",
        dir_only=False,
    ):
        """
        Creates a module attribute text field widget that carries a path.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
            ok_caption (str, optional): Caption use for to accept (ok) function.
            file_filter (str, optional): File filter used by the dialog
            dir_only (bool, optional): If True, the path should point to a directory, otherwise a file.

        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """

        tooltip = textwrap.dedent(
            """\
        Environment Variables:
        "{project-name}": The name of the project
        "{project-sanitized-name}": Sanitized name of project (lowercase, no spaces, no illegal characters)
        "{temp-dir}": is the "temp" folder
        "{home-dir}": is the home folder. e.g. "Documents" on Windows.
        "{desktop-dir}": is the path to the desktop folder.
        "{tests-data-dir}": The package tests folder
        "{project-dir}": is the latest known project folder. (If not set, or missing project, it's empty. e.g. "")
        "{scene-dir}": is the directory of the current scene. (Only available when saved, otherwise "")
        "{year}": Current year (e.g. 2025)
        "{month}": Current month (e.g. 05)
        "{day}": Current day (e.g. 15)
        "{time}": Current time (e.g. 14-30-59)
        "{hostname}": Name of the machine/host. (e.g. "My-PC")
        "{module-name}": Name of the module.
        "{module-sanitized-name}": Sanitized name of module (lowercase, no spaces, no illegal characters)"""
        )

        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        path_btn = ui_qt.QtWidgets.QPushButton()
        path_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        path_btn.setToolTip("Use file dialog to set path")
        env_var_btn = ui_qt.QtWidgets.QPushButton()
        env_var_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        env_var_btn.setToolTip("Get more information about the current path.")
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Set Tooltip
        label.setToolTip(tooltip)
        text_field.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        _layout.addWidget(env_var_btn)
        _layout.addWidget(path_btn)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        _btn_func = partial(
            self.open_module_attr_file_dialog,
            field=text_field,
            ok_caption=ok_caption,
            file_filter=file_filter,
            dir_only=dir_only,
        )
        path_btn.clicked.connect(_btn_func)
        _func = partial(self.open_env_var_feedback_dialog, field=text_field)
        env_var_btn.clicked.connect(_func)
        return text_field

    def add_module_attr_widget_int_slider(
        self,
        attr_name,
        attr_value=None,
        min_int=-10,
        max_int=10,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute integer slider (with spinbox)
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (int, optional): The initial value of the attribute used to set the value of the created widget.
            min_int (int, str): Minimum value of the slider and the spinbox.
            max_int (int, str): Maximum value of the slider and the spinbox.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QIntSlider: A QSlider carrying a linked QSpinBox
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        int_slider = ui_qt_utils.QIntSlider(ui_qt.QtLib.Orientation.Horizontal)
        spinbox = ui_qt.QtWidgets.QSpinBox()
        int_slider.link_spin_box(spinbox)
        int_slider.set_int_range(min_int=min_int, max_int=max_int)
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        int_slider.set_int_value(attr_value)
        if tooltip:
            int_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(int_slider)
        _layout.addWidget(spinbox)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=int_slider)
        int_slider.intValueChanged.connect(_func)
        return int_slider

    def add_module_attr_widget_double_slider(
        self,
        attr_name,
        attr_value=None,
        min_double=-10,
        max_double=10,
        precision=3,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute float slider (with spinbox)
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            min_double (int, str): Minimum value of the slider and the spinbox.
            max_double (int, str): Maximum value of the slider and the spinbox.
            precision (int): The precision of the double spin box (decimals)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QDoubleSlider: A QSlider a linked spinbox.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        double_slider = ui_qt_utils.QDoubleSlider(ui_qt.QtLib.Orientation.Horizontal)
        spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox.setDecimals(precision)
        double_slider.link_spin_box(spinbox)
        double_slider.set_double_range(min_double=min_double, max_double=max_double)
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        double_slider.set_double_value(attr_value)
        if tooltip:
            double_slider.setToolTip(tooltip)
            label.setToolTip(tooltip)
            spinbox.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(double_slider)
        _layout.addWidget(spinbox)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=double_slider)
        double_slider.doubleValueChanged.connect(_func)
        return double_slider

    def add_module_attr_widget_int_spinbox(
        self,
        attr_name,
        attr_value=None,
        min_int=None,
        max_int=None,
        step=None,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute integer spinbox.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                             This name is used to find the variable and set its value in the module instance.
            attr_value (int, optional): The initial value of the attribute used to set the value of the created widget.
            min_int (int, optional): Minimum value of the spinbox. If None, a wide default is used.
            max_int (int, optional): Maximum value of the spinbox. If None, a wide default is used.
            step (int, optional): The increment (single step) value. Defaults to Qt's default (1).
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI; otherwise, the variable name is formatted.
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QSpinBox: A configured spinbox widget
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name

        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)

        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        spinbox = ui_qt.QtWidgets.QSpinBox()

        # Apply min/max range or safe wide defaults
        spinbox.setMinimum(min_int if min_int is not None else -2_147_483_648)
        spinbox.setMaximum(max_int if max_int is not None else 2_147_483_647)

        # Apply increment step if provided
        if step is not None:
            spinbox.setSingleStep(step)

        # Set initial value
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        spinbox.setValue(attr_value)

        # Tooltip
        if tooltip:
            spinbox.setToolTip(tooltip)
            label.setToolTip(tooltip)

        # Add to Layout
        _layout.addWidget(label)
        _layout.addWidget(spinbox)

        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=spinbox)
        spinbox.valueChanged.connect(_func)

        return spinbox

    def add_module_attr_widget_double_spinbox(
        self,
        attr_name,
        attr_value=None,
        min_double=None,
        max_double=None,
        precision=3,
        step=None,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute float spinbox (without slider).
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                             This name is used to find the variable and set its value in the module instance.
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            min_double (float, optional): Minimum value of the spinbox. If None, a very low default is used.
            max_double (float, optional): Maximum value of the spinbox. If None, a very high default is used.
            precision (int): Number of decimal places shown in the spinbox.
            step (float, optional): Step/increment size when adjusting the value.
            nice_name (str, optional): Display name for the label. If not provided, generated from the variable name.
            layout (QBoxLayout, optional): Optional layout to insert the widgets into.
            tooltip (str, optional): Optional tooltip text for label and spinbox.

        Returns:
            QDoubleSpinBox: The configured spinbox widget.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name

        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)

        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox.setDecimals(precision)

        # Apply optional min/max or use wide defaults
        spinbox.setMinimum(min_double if min_double is not None else -1e10)
        spinbox.setMaximum(max_double if max_double is not None else 1e10)

        # Set step if provided
        if step is not None:
            spinbox.setSingleStep(step)

        # Set initial value
        if attr_value is None:
            attr_value = getattr(self.module, attr_name)
        spinbox.setValue(attr_value)

        # Tooltip
        if tooltip:
            spinbox.setToolTip(tooltip)
            label.setToolTip(tooltip)

        # Add to Layout
        _layout.addWidget(label)
        _layout.addWidget(spinbox)

        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=spinbox)
        spinbox.valueChanged.connect(_func)

        return spinbox

    def add_module_attr_widget_checkbox(
        self, attr_name=None, attr_value=None, nice_name=None, layout=None, tooltip=None
    ):
        """
        Creates a module attribute checkbox.
        Args:
            attr_name (str, optional): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (bool, optional): The initial value of the attribute used to set the value
                                        of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QCheckBox: A QCheckBox object.
        """
        if nice_name:
            _formatted_attr_name = nice_name
        elif attr_name:
            _formatted_attr_name = core_str.snake_to_title(attr_name)
        else:
            _formatted_attr_name = ""
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        checkbox = ui_qt.QtWidgets.QCheckBox()
        if attr_value is None:
            if attr_name:
                attr_value = getattr(self.module, attr_name)
            else:
                attr_value = False
        checkbox.setChecked(attr_value)
        if tooltip:
            checkbox.setToolTip(tooltip)
            label.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(checkbox)
        # Connect
        if attr_name:
            _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=checkbox)
            checkbox.stateChanged.connect(_func)
        return checkbox

    def add_module_attr_widget_double3_spinbox(
        self,
        attr_name,
        attr_value=None,
        precision=3,
        nice_name=None,
        layout=None,
        tooltip=None,
        minimum=None,
        maximum=None,
    ):
        """
        Creates a module attribute for a tuple carrying 3 floats. e.g. (1.2, 3.4, 5.6)
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            precision (int): The precision of the double spin box (decimals)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            minimum (float, optional): Sets the minimum range.
            maximum (float, optional): Sets the maximum range.

        Returns:
            QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox: The three created double spin boxes representing x, y, z.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        spinbox_x = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox_y = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox_z = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox_x.setDecimals(precision)
        spinbox_y.setDecimals(precision)
        spinbox_z.setDecimals(precision)
        if minimum:
            spinbox_x.setMinimum(minimum)
            spinbox_y.setMinimum(minimum)
            spinbox_z.setMinimum(minimum)
        if maximum:
            spinbox_x.setMaximum(maximum)
            spinbox_y.setMaximum(maximum)
            spinbox_z.setMaximum(maximum)
        spinbox_y.setDecimals(precision)
        spinbox_z.setDecimals(precision)
        if attr_value is None:
            x, y, z = getattr(self.module, attr_name)
            spinbox_x.setValue(x)
            spinbox_y.setValue(y)
            spinbox_z.setValue(z)
        if tooltip:
            label.setToolTip(tooltip)
            spinbox_x.setToolTip(tooltip)
            spinbox_y.setToolTip(tooltip)
            spinbox_z.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(spinbox_x)
        _layout.addWidget(spinbox_y)
        _layout.addWidget(spinbox_z)
        # Connect
        _func = partial(self.set_module_attr_value_from_double3_spinbox, attr=attr_name, field=spinbox_x, tuple_index=0)
        spinbox_x.valueChanged.connect(_func)
        _func = partial(self.set_module_attr_value_from_double3_spinbox, attr=attr_name, field=spinbox_y, tuple_index=1)
        spinbox_y.valueChanged.connect(_func)
        _func = partial(self.set_module_attr_value_from_double3_spinbox, attr=attr_name, field=spinbox_z, tuple_index=2)
        spinbox_z.valueChanged.connect(_func)
        return spinbox_x, spinbox_y, spinbox_z

    def add_module_attr_widget_combobox(
        self,
        attr_name,
        items,
        attr_value=None,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute field to edit the value using a combo box (drop-down menu)
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            items (List[str]): A list of options for this combox box. e.g. ["Option 1", "Option 2"]
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QComboBox: The created combobox.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.setFixedHeight(30)
        combobox.addItems(items)
        if attr_value is None:
            _module_value = getattr(self.module, attr_name)
            index = combobox.findText(_module_value)
            if index == -1:  # Add missing items (just in case)
                combobox.addItem(_module_value)
                index = combobox.findText(_module_value)
                logger.warning(f'Item "{_module_value}" was not available as an option but was force added.')
            combobox.setCurrentIndex(index)

        if tooltip:
            label.setToolTip(tooltip)
            combobox.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(combobox)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=combobox)
        combobox.currentIndexChanged.connect(_func)

        return combobox

    def add_module_attr_widget_dictionary_editor(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        layout=None,
        tooltip=None,
        dict_editor_tooltip=None,
    ):
        """
        Creates a module attribute field to edit a dictionary using an extra code editor window.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            dict_editor_tooltip (str, optional): If provided, it's added to the dictionary editor as tooltip.

        Returns:
            QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox: The three created double spin boxes representing x, y, z.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        _nice_name = f' Modify Dictionary: "{_formatted_attr_name}"'
        if nice_name:
            _nice_name = _nice_name
        edit_dict_btn = ui_qt.QtWidgets.QPushButton(_nice_name)
        edit_dict_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        if attr_value is None:
            _module_value = getattr(self.module, attr_name)

        if tooltip:
            edit_dict_btn.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(edit_dict_btn)
        # Connect
        _func = partial(
            self.open_module_attr_dictionary_editor, attr=attr_name, dict_editor_tooltip=dict_editor_tooltip
        )
        edit_dict_btn.clicked.connect(_func)
        return edit_dict_btn

    def add_widget_auto_serialized_fields(self, ignore_attrs=None):
        """
        Automatically creates widgets based on the found attributes.

        Args:
            ignore_attrs (None, List[str], str): A list of attributes (variable names) to ignore.
                                                e.g. ["variable_one"]
        """
        if ignore_attrs is None:
            ignore_attrs = []
        if isinstance(ignore_attrs, str):
            ignore_attrs = [ignore_attrs]
        ignore_attrs.append("expanded")  # Auto ignore widget expanded attribute
        instance_attrs = self.get_module_serialized_attrs()

        for attr_name, attr_value in instance_attrs.items():
            if ignore_attrs and attr_name in ignore_attrs:
                continue
            if isinstance(attr_value, str):
                self.add_module_attr_widget_text_field(attr_name=attr_name, attr_value=attr_value)
            if isinstance(attr_value, float):
                self.add_module_attr_widget_double_slider(attr_name=attr_name, attr_value=attr_value)
            if not isinstance(attr_value, bool) and isinstance(attr_value, int):
                self.add_module_attr_widget_int_slider(attr_name=attr_name, attr_value=attr_value)
            if isinstance(attr_value, bool):
                self.add_module_attr_widget_checkbox(attr_name=attr_name, attr_value=attr_value)
            if isinstance(attr_value, dict):
                self.add_module_attr_widget_dictionary_editor(attr_name=attr_name, attr_value=attr_value)
            if (
                isinstance(attr_value, tuple)
                and len(attr_value) == 3
                and all(isinstance(x, (int, float)) for x in attr_value)
            ):
                self.add_module_attr_widget_double3_spinbox(attr_name=attr_name, attr_value=attr_value)

    def add_override_color_ctrls_combobox(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        layout=None,
        tooltip=None,
    ):
        """
        Creates a module attribute field to edit the value using a combo box (drop-down menu)
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (float, optional): Initial value of the attribute used to set the value of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QComboBox: The created combobox.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        combobox = ui_qt_utils.ColorSquareComboBox()
        combobox.setFixedHeight(30)
        # Add color items plus inherit color
        combobox.addItem("INHERIT COLOR", None)
        # Populate Combobox
        for color in dir(core_color.ColorConstants.RGB()):
            if color.startswith("_"):  # Filter Private Variables
                continue
            else:
                combobox.addItem(color)
                added_item_index = combobox.findText(color)
                rgb_value = getattr(core_color.ColorConstants.RGB, color)
                if rgb_value:
                    normalized_color = ui_qt.QtGui.QColor()
                    normalized_color.setRgbF(*rgb_value)
                    combobox.setItemData(
                        added_item_index, normalized_color, ui_qt_utils.ColorSquareDelegate.COLOR_DATA_IDX
                    )

        # Set Combobox to stored value ---
        if attr_value is None:
            _module_value = getattr(self.module, attr_name)
            if not _module_value or isinstance(_module_value, (list, tuple)):
                combobox.setCurrentIndex(0)
            else:
                index = combobox.findText(_module_value)
                combobox.setCurrentIndex(index)

        if tooltip:
            label.setToolTip(tooltip)
            combobox.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(combobox)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=combobox)
        combobox.currentIndexChanged.connect(_func)

        return combobox

    def add_module_rot_order_combobox(self, layout=None):
        """
        Add a combobox with the rotation order attribute ("rot_order") so it can be determined using a list.
        Args:
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
        Returns:
            QComboBox: The created combobox.
        """
        _tooltip = "Defined the rotation order of the proxies created by this module."
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        combobox_label = ui_qt.QtWidgets.QLabel("Rotation Order:")
        combobox_label.setToolTip(_tooltip)
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.setMinimumWidth(50)
        combobox.addItems(["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"])
        combobox.setCurrentIndex(self.module.rot_order)
        combobox.currentIndexChanged.connect(self.on_combobox_module_order_order_change)
        combobox.setToolTip(_tooltip)
        _layout.addWidget(combobox_label)
        _layout.addWidget(combobox)

        return combobox

    # Utils ---------------------------------------------------------------------------------------------------
    def refresh_current_widgets(self):
        """
        Refreshes available widgets. For example, tables, so they display the correct module name.
        """
        if self.mod_name_field:
            _name = self.module.get_name()
            if _name:
                self.mod_name_field.setText(_name)
        if self.mod_prefix_field:
            _prefix = self.module.get_prefix()
            if _prefix:
                self.mod_prefix_field.setText(_prefix)
        if self.mod_suffix_field:
            _suffix = self.module.get_suffix()
            if _suffix:
                self.mod_suffix_field.setText(_suffix)
        if self.table_proxy_parent_wdg:
            self.refresh_proxy_parent_table()
        if self.table_proxy_basic_wdg:
            self.refresh_proxy_basic_table()

    def refresh_known_proxy_dict(self, ignore_list=None):
        """
        Refreshes the "known_proxies" attribute with all proxies that could be used as parents.
        Args:
            ignore_list (list, optional): A list of proxies to be ignored
        """
        for module in self.project.get_modules():
            for proxy in module.get_proxies():
                if ignore_list and proxy in ignore_list:
                    continue
                self.known_proxies[proxy.get_uuid()] = (proxy, module)

    def refresh_proxy_parent_table(self):
        """
        Refresh the table with proxies associated with the module.
        With extra options to edit parent or delete the proxy.
        """
        self.clear_proxy_parent_table()
        for row, proxy in enumerate(self.module.get_proxies()):
            self.table_proxy_parent_wdg.insertRow(row)
            suffix = proxy.get_attr_dict_value(key="suffix")
            if not suffix:
                suffix = None
            prefix = proxy.get_attr_dict_value(key="prefix")
            if not prefix:
                prefix = None

            # Icon ---------------------------------------------------------------------------
            self.insert_item(
                row=row,
                column=0,
                table=self.table_proxy_parent_wdg,
                icon_path=ui_res_lib.Icon.util_reset_transforms,
                editable=False,
                centered=True,
            )

            # Prefix ---------------------------------------------------------------------------
            self.insert_item(row=row, column=1, table=self.table_proxy_parent_wdg, text=prefix, data_object=proxy)

            # Name ---------------------------------------------------------------------------
            self.insert_item(
                row=row, column=2, table=self.table_proxy_parent_wdg, text=proxy.get_name(), data_object=proxy
            )

            # Suffix ---------------------------------------------------------------------------
            self.insert_item(row=row, column=3, table=self.table_proxy_parent_wdg, text=suffix, data_object=proxy)

            # Parent Combobox ----------------------------------------------------------------
            self.refresh_known_proxy_dict()
            combo_box = self.create_widget_parent_combobox(target=proxy, parent_filter=False)
            combo_func = partial(self.on_table_parent_combo_box_changed, source_row=row, source_col=4)
            combo_box.currentIndexChanged.connect(combo_func)
            self.table_proxy_parent_wdg.setCellWidget(row, 4, combo_box)

            # Edit Proxy ---------------------------------------------------------------------
            edit_proxy_btn = ui_qt.QtWidgets.QPushButton()
            edit_proxy_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
            edit_proxy_func = partial(self.on_button_edit_proxy_clicked, proxy=proxy)
            edit_proxy_btn.clicked.connect(edit_proxy_func)
            edit_proxy_btn.setToolTip("Edit Raw Data")
            self.table_proxy_parent_wdg.setCellWidget(row, 5, edit_proxy_btn)

            # Delete Setup --------------------------------------------------------------------
            delete_proxy_btn = ui_qt.QtWidgets.QPushButton()
            delete_proxy_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_proxy_func = partial(self.delete_proxy, proxy=proxy)
            delete_proxy_btn.clicked.connect(delete_proxy_func)
            delete_proxy_btn.setToolTip("Delete Proxy")
            self.table_proxy_parent_wdg.setCellWidget(row, 6, delete_proxy_btn)

    def refresh_proxy_basic_table(self):
        """
        Refresh the table with proxies associated with the module.
        """
        self.clear_proxy_basic_table()
        for row, proxy in enumerate(self.module.get_proxies()):
            self.table_proxy_basic_wdg.insertRow(row)
            # Icon ---------------------------------------------------------------------------
            self.insert_item(
                row=row,
                column=0,
                table=self.table_proxy_basic_wdg,
                icon_path=ui_res_lib.Icon.util_reset_transforms,
                editable=False,
                centered=True,
            )

            # Name ---------------------------------------------------------------------------
            self.insert_item(
                row=row, column=1, table=self.table_proxy_basic_wdg, text=proxy.get_name(), data_object=proxy
            )

            # Edit Proxy ---------------------------------------------------------------------
            edit_proxy_btn = ui_qt.QtWidgets.QPushButton()
            edit_proxy_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
            edit_proxy_func = partial(self.on_button_edit_proxy_clicked, proxy=proxy)
            edit_proxy_btn.clicked.connect(edit_proxy_func)
            edit_proxy_btn.setToolTip("Edit Raw Data")
            self.table_proxy_basic_wdg.setCellWidget(row, 2, edit_proxy_btn)

    def update_proxy_from_raw_data(self, data_getter, proxy):
        """
        Updates a proxy description using raw string data.
        Args:
            data_getter (callable): A function used to retrieve the data string
            proxy (Proxy): A proxy object to be updated using the data
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            proxy.read_data_from_dict(_data_as_dict)
            self.refresh_current_widgets()
        except Exception as e:
            raise Exception(f'Unable to set proxy attributes from provided raw data. Issue: "{e}".')

    def update_module_from_raw_data(self, data_getter, module):
        """
        Updates a proxy description using raw string data.
        Used with "on_button_edit_module_clicked" to update modules from raw data.
        Args:
            data_getter (callable): A function used to retrieve the data string
            module (ModuleGeneric): A module object to be updated using the data
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            module.read_data_from_dict(_data_as_dict)
            self.refresh_current_widgets()
            self.call_parent_refresh()
        except Exception as e:
            raise Exception(f'Unable to set module attributes from provided raw data. Issue: "{e}".')

    def clear_proxy_parent_table(self):
        """
        Clear all rows from the proxy parent table widget if it exists.
        This effectively resets the table display to empty.
        """
        if self.table_proxy_parent_wdg:
            self.table_proxy_parent_wdg.setRowCount(0)

    def clear_proxy_basic_table(self):
        """
        Clear all rows from the proxy parent table widget if it exists.
        This effectively resets the table display to empty.
        """
        if self.table_proxy_basic_wdg:
            self.table_proxy_basic_wdg.setRowCount(0)

    def insert_item(
        self,
        row,
        column,
        table,
        text=None,
        data_object=None,
        icon_path="",
        icon_size=32,
        editable=True,
        centered=True,
    ):
        """
        Insert an item into the table.

        Args:
            row (int): Row index.
            column (int): Column index.
            table (QTableWidget): Target table.
            text (str): Text to display in the item.
            data_object: The associated data object.
            icon_path (str): Path to the icon. (If provided, text is ignored)
            icon_size (int): Icon size, one value, square. 32 by default.
            editable (bool): Whether the item is editable.
            centered (bool): Whether the text should be centered.
        """
        item = ui_qt.QtWidgets.QTableWidgetItem(text)
        self.set_table_item_proxy_object(item, data_object)

        if icon_path != "":
            icon = ui_qt.QtGui.QIcon(icon_path)
            icon_label = ui_qt.QtWidgets.QLabel()
            icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
            icon_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            table.setCellWidget(row, column, icon_label)
            return

        if centered:
            item.setTextAlignment(ui_qt.QtLib.AlignmentFlag.AlignHCenter | ui_qt.QtLib.AlignmentFlag.AlignVCenter)

        if not editable:
            item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)

        if table:
            table.setItem(row, column, item)

    def on_table_parent_combo_box_changed(self, index, source_row, source_col):
        """
        Handle the change in the parent combo box for the proxy table.

        Args:
            index (int): Index of the selected item.
            source_row (int): Row index.
            source_col (int): Column index.
        """
        _name_cell = self.table_proxy_parent_wdg.item(source_row, 2)
        _proxy = self.get_table_item_proxy_object(_name_cell)
        _combo_box = self.table_proxy_parent_wdg.cellWidget(source_row, source_col)
        _parent_proxy = _combo_box.itemData(index)
        if _parent_proxy is None:
            _proxy.clear_parent_uuid()
            logger.debug(f"{_proxy.get_name()}: to : None")
        else:
            _proxy.set_parent_uuid(_parent_proxy.get_uuid())
            logger.debug(f"{_proxy.get_name()}: to : {_parent_proxy.get_name()}")
        self.refresh_proxy_parent_table()

    def on_parent_combo_box_changed(self, index, combobox):
        """
        Handle the change in the parent combo box for the proxy table.

        Args:
            index (int): Index of the selected item.
            combobox (QComboBox): A module parent combo box QT object.
        """
        _parent_proxy = combobox.itemData(index)
        if _parent_proxy is None:
            self.module.clear_parent_uuid()
            logger.debug(f"{self.module.get_name()}: to : None")
        else:
            self.module.set_parent_uuid(_parent_proxy.get_uuid())
            logger.debug(f"{self.module.get_name()}: to : {_parent_proxy.get_name()}")
        self.call_parent_refresh()

    def on_proxy_parent_table_cell_changed(self, row, column):
        """
        Updates the name/prefix/suffix of the proxy object in case the user writes a new name/prefix/suffix in the name
        cell.
        Args:
            row (int): Row where the cell changed.
            column (int): Column where the cell changed.
        """
        _source_table = self.table_proxy_parent_wdg
        _cell = _source_table.item(row, column)
        _source_table.cellChanged.disconnect(self.on_proxy_parent_table_cell_changed)  # Fix recursion errors
        _proxy = self.get_table_item_proxy_object(_cell)
        if column == 1:  # 1 = Prefix
            current_prefix = _proxy.get_attr_dict_value(key="prefix")
            new_prefix = _source_table.item(row, column).text()
            if current_prefix != new_prefix:
                _proxy.add_to_attr_dict(attr="prefix", value=new_prefix)
                self.refresh_proxy_parent_table()
            else:
                _cell.setText(current_prefix)
        if column == 2:  # 2 = Name
            current_name = _proxy.get_name()
            new_name = _cell.text()
            if current_name != new_name:
                _proxy.set_name(new_name)
                _proxy.add_to_attr_dict(attr="baseName", value=new_name)
                self.refresh_proxy_parent_table()
            else:
                _cell.setText(current_name)
        if column == 3:  # 3 = Suffix
            current_suffix = _proxy.get_attr_dict_value(key="suffix")
            new_suffix = _source_table.item(row, column).text()
            if current_suffix != new_suffix:
                _proxy.add_to_attr_dict(attr="suffix", value=new_suffix)
                self.refresh_proxy_parent_table()
            else:
                _cell.setText(current_suffix)
        _source_table.cellChanged.connect(self.on_proxy_parent_table_cell_changed)  # Fix recursion errors

    def on_proxy_basic_table_cell_changed(self, row, column):
        """
        Updates the name of the proxy object in case the user writes a new name in the name cell.
        Args:
            row (int): Row where the cell changed.
            column (int): Column where the cell changed.
        """
        _source_table = self.table_proxy_basic_wdg
        _source_table.cellChanged.disconnect(self.on_proxy_basic_table_cell_changed)  # Fix recursion errors
        _name_cell = _source_table.item(row, 1)  # 1 = Name
        _proxy = self.get_table_item_proxy_object(_name_cell)
        current_name = _proxy.get_name()
        new_name = _name_cell.text()
        if new_name:
            _proxy.set_name(new_name)
            _proxy.add_to_attr_dict(attr="baseName", value=new_name)
            self.refresh_proxy_basic_table()
        else:
            _name_cell.setText(current_name)
        _source_table.cellChanged.connect(self.on_proxy_basic_table_cell_changed)  # Fix recursion errors

    def on_orientation_combobox_change(self, index):
        """
        Determines the module orientation method and updates the UI to allow edits.
        Args:
            index (int): Combo box index change (used to retrieve text item)
        """
        method = self.mod_orient_method.itemText(index)
        self.module.set_orientation_method(method=method.lower())
        self.mod_edit_orient_btn.setEnabled(False)
        if method.lower() == tools_rig_frm.OrientationData.Methods.automatic.lower():
            self.mod_edit_orient_btn.setEnabled(True)

    def on_orientation_edit_clicked(self):
        """
        Open edit orientation data edit view for the current module
        """
        edit_orient_window = tools_rig_orient_view.RiggerOrientView(parent=self, module=self.module)
        edit_orient_window.show()

    def on_button_edit_proxy_clicked(self, proxy):
        """
        Shows a text-editor window with the proxy converted to a dictionary (raw data)
        If the user applies the changes, and they are considered valid, the proxy is updated with it.
        Args:
            proxy (Proxy): The target proxy (proxy to be converted to dictionary)
        """
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=f'Editing Raw Data for the Proxy "{proxy.get_name()}"',
            window_title=f'Raw data for "{proxy.get_name()}"',
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")
        proxy_raw_data = proxy.get_proxy_as_dict(
            include_uuid=True, include_transform_data=True, include_offset_data=True
        )
        formatted_dict = core_iter.dict_as_formatted_str(proxy_raw_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.update_proxy_from_raw_data, param_win.get_text_field_text, proxy)
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.show()

    def on_button_edit_module_clicked(self, skip_proxies=True, *args):
        """
        Shows a text-editor window with the module converted to a dictionary (raw data)
        If the user applies the changes, and they are considered valid, the module is updated with it.
        Args:
            skip_proxies (bool, optional): If active, the "proxies" key will be ignored.
            *args: Variable-length argument list. - Here to avoid issues with the "skip_proxies" argument.
        """
        module_name = self.module.get_name()
        if not module_name:
            module_name = self.module.get_module_class_name(remove_module_prefix=True)
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=f'Editing Raw Data for the Module "{module_name}"',
            window_title=f'Raw data for "{module_name}"',
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")
        module_raw_data = self.module.get_module_as_dict(include_module_name=False, include_offset_data=True)
        if "proxies" in module_raw_data and skip_proxies:
            module_raw_data.pop("proxies")
        formatted_dict = core_iter.dict_as_formatted_str(module_raw_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.update_module_from_raw_data, param_win.get_text_field_text, self.module)
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.show()

    def on_button_add_proxy_clicked(self):
        """
        Adds a new proxy to the current module and refreshes the UI
        """
        self.module.add_new_proxy()
        self.refresh_current_widgets()

    def on_button_read_scene_data_clicked(self):
        """
        Reads proxy data from scene
        """
        logger.info(f"Data for this module from the scene")  # TODO
        self.module.read_data_from_scene()
        self.refresh_current_widgets()

    def on_button_build_mod_proxy_clicked(self):
        """
        Reads proxy data from scene
        """
        proxy_grp = tools_rig_utils.find_root_group_proxy()
        if proxy_grp:
            message_box = ui_qt.QtWidgets.QMessageBox(self)
            message_box.setWindowTitle(f"Proxy detected in the scene.")
            message_box.setText(f"A pre-existing proxy was detected in the scene. \n" f"How would you like to proceed?")

            message_box.addButton("Delete Proxy and Rebuild", ui_qt.QtLib.ButtonRoles.ActionRole)
            message_box.addButton("Cancel", ui_qt.QtLib.ButtonRoles.RejectRole)
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()
            if result == 0:
                import maya.cmds as cmds

                cmds.delete(proxy_grp)
            else:
                return
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(module=self.module, set_parent_project=False)
        a_project.build_proxy()

    def on_checkbox_active_state_changed(self, state):
        """
        Uses the state of the checkbox to determine the active state of the module
        Args:
            state (bool): If True, the state of the module will be set to Active. If False, to Inactive.
        """
        self.module.set_active_state(is_active=bool(state))
        self.call_parent_refresh()

    def on_checkbox_code_data_active_changed(self, *args, checkbox, combobox):
        """
        Uses the state of the checkbox to determine the active state of the module
        Args:
            args (any): Used to receive state
            checkbox (QCheckBox): If True, the state of the module will be set to Active. If False, to Inactive.
            combobox (QComboBox): A combobox of orders to be updated in case a new CodeData is created.
        """
        # Basic Vars
        is_checked = checkbox.isChecked()
        if not is_checked:
            module_name = self.module.get_name()
            if not module_name:
                module_name = self.module.get_module_class_name(remove_module_prefix=True)
            message_box = ui_qt.QtWidgets.QMessageBox(self)
            message_box.setWindowTitle(f'Delete CodeData for "{str(module_name)}"?')
            _message = f'Are you sure you want to deactivate the CodeData for "{str(module_name)}"?\n'
            _message += "This will cause any existing stored code to be deleted."
            message_box.setText(_message)
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
            message_box.addButton(ui_qt.QtLib.StandardButton.No)
            result = message_box.exec_()
            if result == ui_qt.QtLib.StandardButton.Yes:
                self.module.clear_code_data()
            else:
                checkbox.setChecked(True)
                return
        else:
            if not self.module.get_code_data():  # Does it not have a CodeData object?
                self.module.code = tools_rig_frm.CodeData()  # Initializes a new CodeData
                combobox.setCurrentIndex(0)

    def on_combobox_code_data_order_changed(self, *args):
        """
        Uses the state of the checkbox to determine the active state of the module
        Args:
            args (any): Used to receive the text value from the code order combobox.
        """
        code_data = self.module.get_code_data()
        code_data.set_order(order=args[0])

    def on_combobox_module_order_order_change(self, index):
        """
        Uses the index of the combobox to define the "rot_order" attribute of the module.
        Args:
            index (int): Index of the selected combobox item.
        """
        self.module.rot_order = index

    def create_widget_parent_combobox(self, target, parent_filter=True):
        """
        Creates a populated combobox with all potential parent targets.
        An extra initial item called "No Parent" is also added for the proxies without parents.
        Current parent is pre-selected during creation.
        Args:
            target (Proxy, Module): A proxy or module object used to determine current parent and pre-select it.
            parent_filter (bool, optional): If True, it will only populate the combobox with proxies available under
                                          the parent modules.
        Returns:
            QComboBox: A pre-populated combobox with potential parents. Current parent is also pre-selected.
        """
        self.refresh_known_proxy_dict()

        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.addItem("No Parent", None)

        # Get Variables
        _proxy_uuid = None
        if target and hasattr(target, "get_uuid"):  # Is proxy
            _proxy_uuid = target.get_uuid()
        _proxy_parent_uuid = target.get_parent_uuid()
        _parent_module = self.known_proxies.get(_proxy_parent_uuid, None)
        if _parent_module:
            _parent_module = _parent_module[1]  # Get second item in tuple (module)
        # Populate Combobox
        for key, (_proxy, _module) in self.known_proxies.items():
            if parent_filter and _parent_module and _parent_module != _module:
                continue
            if key == _proxy_uuid:
                continue  # Skip Itself
            description = f"{str(_proxy.get_name())}"
            module_name = _module.get_name()
            if module_name:
                description += f" : {str(module_name)}"
            combobox.addItem(description, _proxy)

        # Unknown Target (Not present in any of the modules)
        if _proxy_parent_uuid and _proxy_parent_uuid in self.known_proxies:
            for index in range(combobox.count()):
                _parent_proxy = combobox.itemData(index)
                if _parent_proxy and _proxy_parent_uuid == _parent_proxy.get_uuid():
                    combobox.setCurrentIndex(index)
        elif _proxy_parent_uuid and _proxy_parent_uuid not in self.known_proxies:
            description = f"unknown : ???"
            description += f" ({str(_proxy_parent_uuid)})"
            combobox.addItem(description, None)
            combobox.setCurrentIndex(combobox.count() - 1)  # Last item, which was just added
        return combobox

    def call_parent_refresh(self):
        """
        Calls the refresh parent function. This function needs to first be set before it can be used.
        In case it has not been set, or it's missing, the operation will be ignored.
        """
        if not self.refresh_parent_func or not callable(self.refresh_parent_func):
            logger.debug(f"Unable to call refresh tree function. Function has not been set or is missing.")
            return
        self.refresh_parent_func()

    def delete_proxy(self, proxy):
        """
        Prompt the user to confirm deletion of a proxy, and if confirmed,
        remove the proxy from the module and refresh relevant UI elements.

        Args:
            proxy (Proxy): The proxy object to be deleted.
        """
        _proxy_name = proxy.get_name()
        message_box = ui_qt.QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(f'Delete Proxy "{str(_proxy_name)}"?')
        message_box.setText(f'Are you sure you want to delete proxy "{str(_proxy_name)}"?')
        question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
        message_box.addButton(ui_qt.QtLib.StandardButton.No)
        result = message_box.exec_()
        if result == ui_qt.QtLib.StandardButton.Yes:
            self.module.remove_from_proxies(proxy)
            self.refresh_known_proxy_dict()
            self.refresh_current_widgets()

    def delete_module(self):
        """Deletes the module associated with this attribute widgets"""
        _module_name = self.module.get_name() or ""
        _module_class = self.module.get_module_class_name(remove_module_prefix=False)
        if _module_name:
            _module_name = f'\n"{_module_name}" ({_module_class})'
        else:
            _module_name = f"\n{_module_class}"
        message_box = ui_qt.QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(f"Delete Module {str(_module_name)}?")
        message_box.setText(f"Are you sure you want to delete module {str(_module_name)}?")
        question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
        message_box.addButton(ui_qt.QtLib.StandardButton.No)
        result = message_box.exec_()
        if result == ui_qt.QtLib.StandardButton.Yes:
            self.project.remove_from_modules(self.module)
            self.call_parent_refresh()
            self.toggle_content_visibility()

    def open_env_var_feedback_dialog(self, field):
        """Opens a dialog with more information about a parsed path
        Args:
            field (str): A path to parse and give as feedback.
        """
        _path = field.text()
        _parsed_path = self.module.parse_path(path=_path)
        _exists = os.path.exists(_parsed_path)
        _is_dir = os.path.isdir(_parsed_path)
        message = f"Parsed Path:\n{_parsed_path}\n\nExists: {str(_exists)}\nDirectory: {str(_is_dir)}"
        msg_box = ui_qt.QtWidgets.QMessageBox()
        msg_box.setIcon(ui_qt.QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle("Path Information")
        msg_box.setText(message)
        msg_box.setStandardButtons(ui_qt.QtWidgets.QMessageBox.Ok)
        msg_box.exec_()

    def open_module_attr_dictionary_editor(self, *args, attr, dict_editor_tooltip=None):
        """
        If the provided attribute name is available in the module, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
            attr (str): Name of the attribute.
            dict_editor_tooltip (str, optional): If provided, it's added to the dictionary editor as tooltip.
        """
        module_name = self.module.get_name()
        if not module_name:
            module_name = self.module.get_module_class_name(remove_module_prefix=True)
        _message = f'Editing Raw Dictionary Data for "{attr}" found in "{module_name}"'
        if dict_editor_tooltip:
            _message = f"{_message}\n{dict_editor_tooltip}"
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=_message,
            window_title=f'Raw data for "{attr}" found in "{module_name}"',
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")

        _value = getattr(self.module, attr)
        formatted_dict = core_iter.dict_as_formatted_str(_value, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(
            self.set_module_attr_value_from_dictionary_editor, attr=attr, data_getter=param_win.get_text_field_text
        )
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.show()

    def open_module_attr_code_data_editor(self, *args):
        """
        If the provided attribute name is available in the module, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
        """
        code_data = self.module.get_code_data()

        module_name = self.module.get_name()
        if not module_name:
            module_name = self.module.get_module_class_name(remove_module_prefix=True)
        _message = f'Editing Python CodeData found in "{module_name}"'
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=_message,
            window_title=f'Python CodeData for "{module_name}"',
            image=ui_res_lib.Icon.dev_code,
            window_icon=ui_res_lib.Icon.dev_code,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")

        _value = code_data.get_execution_code()
        # formatted_dict = core_iter.dict_as_formatted_str(_value, one_key_per_line=True)
        param_win.set_text_field_text(_value)
        confirm_button_func = partial(
            self.set_code_data_from_python_editor, code_data=code_data, data_getter=param_win.get_text_field_text
        )
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.confirm_button.clicked.connect(param_win.close_window)
        param_win.show()

    def open_module_attr_file_dialog(
        self, *args, field, ok_caption="Set Path", file_filter="All Files (*);;JSON Files (*.json)", dir_only=False
    ):
        """
        Opens file dialog used to populate a module text field responsible for a path.
        Args:
            field (QLineEdit): A text-field used to store the path.
            ok_caption (str, optional): Caption use for to accept (ok) function.
            file_filter (str, optional): File filter used by the dialog
            dir_only (bool, optional): If True it will only accept directories, no files.
        """
        _starting_directory = None
        current_path = field.text()
        if os.path.exists(current_path):
            _starting_directory = current_path

        file_path = ui_file_dialog.file_dialog(
            write_mode=False,
            starting_directory=_starting_directory,
            file_filter=file_filter,
            ok_caption=ok_caption,
            cancel_caption="Cancel",
            dir_only=dir_only,
        )
        if file_path and os.path.exists(file_path):
            # Should absolute path be converted to relative?
            _rigger_prefs = core_prefs.Prefs(tools_rig_const.RiggerConstants.PREFS_FILENAME)
            _on_set_path_abs_to_relative = _rigger_prefs.get_bool(
                key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_SET_PATH_ABS_TO_RELATIVE, default=True
            )
            if _on_set_path_abs_to_relative and self.project and self.module:
                file_path = self.module.parse_absolute_project_path_to_relative(absolute_path=file_path)
            # Set Text field
            field.setText(file_path)

    # Setters --------------------------------------------------------------------------------------------------
    def set_module_name(self):
        """
        Set the name of the module based on the text in the name text field.
        """
        new_name = self.mod_name_field.text() or ""
        self.module.set_name(new_name)
        self.refresh_current_widgets()
        self.call_parent_refresh()

    def set_module_prefix(self):
        """
        Set the name of the module based on the text in the name text field.
        """
        new_prefix = self.mod_prefix_field.text() or ""
        self.module.set_prefix(new_prefix)
        self.refresh_current_widgets()

    def set_module_suffix(self):
        """
        Set the name of the module based on the text in the name text field.
        """
        new_suffix = self.mod_suffix_field.text() or ""
        self.module.set_suffix(new_suffix)
        self.refresh_current_widgets()

    def set_table_item_proxy_object(self, item, proxy):
        """
        Set the proxy object as data for a table item.

        Args:
            item (QTableWidgetItem): The table item.
            proxy (Proxy): The proxy object.
        """
        item.setData(self.PROXY_ROLE, proxy)

    def set_refresh_parent_func(self, func):
        """
        Set the function to be called for refreshing the parent widget.
        Args:
        func (callable): The function to be set as the refresh table function.
        """
        if not callable(func):
            logger.warning(f"Unable to parent refresh function. Provided argument is not a callable object.")
            return
        self.refresh_parent_func = func

    def toggle_content_visibility(self):
        """
        Updates the visibility of the "scroll_content_layout" to the opposite of its value.
        """
        self.scroll_content_layout.parent().setHidden(not self.scroll_content_layout.parent().isHidden())

    def set_module_attr_value_from_field(self, *args, attr, field):
        """
        If the provided attribute name is available in the module, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
            attr (str): Name of the attribute.
            field (QtWidget): A QtWidget object to get the value from
        """
        _value = None
        if isinstance(field, ui_qt.QtWidgets.QLineEdit):
            _value = field.text()
        if isinstance(field, ui_qt_utils.QDoubleSlider):
            _value = field.double_value()
        if isinstance(field, ui_qt_utils.QIntSlider):
            _value = field.int_value()
        if isinstance(field, ui_qt.QtWidgets.QCheckBox):
            _value = field.isChecked()
        if isinstance(field, ui_qt.QtWidgets.QComboBox):
            _value = field.currentText()
        if isinstance(field, ui_qt.QtWidgets.QSpinBox):
            _value = field.value()
        if isinstance(field, ui_qt.QtWidgets.QDoubleSpinBox):
            _value = field.value()
        if hasattr(self.module, attr):
            setattr(self.module, attr, _value)
        else:
            logger.warning(f'Unable to set missing attribute. Attr: "{attr}". Type: "{type(self.module)}".')

    def set_module_attr_value_from_double3_spinbox(self, *args, attr, field, tuple_index):
        """
        If the provided attribute name is available in the module, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
            attr (str): Name of the attribute.
            field (QSpinBox): A QtWidget object to get the value from
            tuple_index (int): Which value to replace on the tuple. It can be 0, 1 or 2.
                               e.g. 0 = first element, so (x, y, z) in this case it would replace "x".
        """
        _value = getattr(self.module, attr)
        _value_as_list = list(_value)
        _channel_value = field.value()
        _value_as_list[tuple_index] = _channel_value
        if hasattr(self.module, attr):
            setattr(self.module, attr, tuple(_value_as_list))
        else:
            logger.warning(f'Unable to set missing attribute. Attr: "{attr}". Type: "{type(self.module)}".')

    def set_module_attr_value_from_dictionary_editor(self, *args, attr, data_getter):
        """
        Updates a proxy description using raw string data.
        Used with "on_button_edit_module_clicked" to update modules from raw data.
        Args:
            attr (str): Name of the module attribute (variable) to set.
            data_getter (callable): A function used to retrieve the data string
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            if hasattr(self.module, attr):
                setattr(self.module, attr, _data_as_dict)
                logger.info(f'Data for "{attr}" was set using the parameters editor.')
            else:
                logger.warning(f'Unable to set missing attribute. Attr: "{attr}". Type: "{type(self.module)}".')
        except Exception as e:
            raise Exception(f'Unable to set module attribute "{attr}" from provided dictionary data. Issue: "{e}".')

    @staticmethod
    def set_code_data_from_python_editor(*args, data_getter, code_data):
        """
        Updates a proxy description using raw string data.
        Used with "on_button_edit_module_clicked" to update modules from raw data.
        Args:
            data_getter (callable): A function used to retrieve the data string
            code_data (CodeData): A code data object to be updated with the new code.
        """
        data = data_getter()
        code_data.set_execution_code(data)
        logger.info(f"CodeData execution code was updated.")

    # Getters --------------------------------------------------------------------------------------------------
    def get_table_item_proxy_object(self, item):
        """
        Get the proxy object associated with a table item.

        Args:
            item (QTableWidgetItem): The table item.

        Returns:
            Proxy or None: The associated proxy object, None otherwise.
        """
        return item.data(self.PROXY_ROLE)

    def get_module_serialized_attrs(self):
        """
        Gets a dictionary containing the name and value for all class attributes except the manually serialized ones.
        Private variables starting with an underscore are ignored. e.g. "self._private" will not be returned.
        Returns:
            dict: A dictionary containing any attributes and their values.
            e.g. A class has an attribute "self.ctrl_visibility" set to True. This function will return:
            {"ctrl_visibility": True}, which can be serialized.
        """
        if not self.module:
            return {}
        _manually_serialized = tools_rig_const.RiggerConstants.CLASS_ATTR_SKIP_AUTO_SERIALIZATION
        _result = {}
        for key, value in self.module.__dict__.items():
            if key not in _manually_serialized and not key.startswith("_"):
                if core_io.is_json_serializable(data=value, allow_none=False):  # Skip proxies and other elements.
                    _result[key] = value
        return _result

    def get_potential_drivers_list(self, as_nice_name_pairs=False):
        """
        Gets a list of potential drivers. These are future controls that get created after the build step.

        Args:
            as_nice_name_pairs (bool, optional): If True, this function returns pairs where the first object is
                                                 a nice name and the second is the driver_uuid.

        Returns:
            list: A list of driver uuids or a 2d list containing a nice name and the driver uuids.
                  e.g. ["module_uuid-fk-purpose", "module_uuid-fk-purpose", ...]
                    or [["module_uuid-fk-spine", "Spine : Hips : FK"], [...]]
        """
        drivers_dict = self.project.get_potential_drivers()
        drivers_list = []
        for source, driver_uuids in drivers_dict.items():
            if as_nice_name_pairs:
                # Get Module Name
                _source_name = source.get_name() or ""
                if not _source_name and isinstance(source, tools_rig_frm.ModuleGeneric):
                    _source_name = self.module.get_module_class_name(remove_module_prefix=False)
                for driver in driver_uuids:
                    # Get Purpose and Driver Type
                    mod_uuid, drv_type, purpose = driver.split("-")
                    if len(drv_type) <= 3:
                        drv_type = drv_type.upper()
                    else:
                        drv_type = drv_type.capitalize()
                    _pair = [driver, f"{_source_name} : {purpose.capitalize()} : {drv_type}"]
                    drivers_list.append(_pair)
            else:
                drivers_list.extend(driver_uuids)
        return drivers_list


class AttrWidgetCommon(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for modules that are missing a proper unique AttrWidget.
        The "AttrWidgetCommon" will show all proxies (with the edit options)
        And automatically list all available attributes.

        Args:
            parent (QWidget): The parent widget.
            module: The module associated with this widget.
            project: The project associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_auto_serialized_fields()
        self.add_widget_action_buttons()


# -------------------------------------------------- Modules --------------------------------------------------
class AttrWidgetModuleGeneric(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget): The parent widget.
            module: The module associated with this widget.
            project: The project associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=True, add_order_editor=True, add_code_editor=True)
        self.add_widget_proxy_parent_table()
        self.add_widget_action_buttons()


class AttrWidgetModuleGenericFK(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=True, add_order_editor=True, add_code_editor=True)
        self.add_widget_proxy_parent_table()
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["extra_control_parent_groups", "ctrl_color", "ctrl_shape", "include_scale"]
        )

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_text_field(
            attr_name="ctrl_shape",
            nice_name="Control Shape",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="include_scale",
            nice_name="Include Scale",
            tooltip="When checked, the scale of the control will be unlocked, and a scale constraint between the "
            "control and the joint will be created.",
            layout=_layout,
        )
        self.add_override_color_ctrls_combobox(
            attr_name="ctrl_color",
            nice_name="Control Color",
            tooltip="Select the color of the controls in the module.",
        )
        extra_groups_field = self.add_extra_groups_widget_field(
            attr_name="extra_control_parent_groups",
            nice_name="Extra Parent Groups",
            tooltip="Write here the groups you want to have as offsets, separated by commas, spaces will be deleted.",
            placeholder='Separate group names using commas. e.g. "one, two, three"',
        )
        refresh_name_func = partial(self.refresh_extra_groups, field=extra_groups_field)
        extra_groups_field.textChanged.connect(refresh_name_func)

        self.add_widget_action_buttons()

    def refresh_extra_groups(self, *args, field):
        """
        Updates the module's extra parent groups based on the text from the given input field.

        Args:
            *args: Additional arguments (ignored).
            field (QLineEdit or similar): Text input widget containing the extra groups string.
        """
        if field:
            extra_groups = field.text()
            self.module.set_extra_parent_groups(extra_groups)
            self.refresh_proxy_parent_table()

    def add_extra_groups_widget_field(self, attr_name, nice_name=None, layout=None, tooltip=None, placeholder=None):
        """
        Args:
            attr_name (str, optional): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            placeholder (str, optional): Placeholder text added to the text-field
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        attr_value = getattr(self.module, attr_name)
        if attr_value:
            attr_value = ",".join(attr_value)
            attr_value = attr_value.replace(" ", "")
            text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        if tooltip:
            text_field.setToolTip(tooltip)
            label.setToolTip(tooltip)
        if placeholder:
            text_field.setPlaceholderText(placeholder)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)

        return text_field


class AttrWidgetModuleRoot(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Root Preferences")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.addStretch()
        self.content_layout.addLayout(_layout)

        _tooltip = "If active, the root will inherit the rotation found on the root proxy."
        self.add_module_attr_widget_checkbox(
            attr_name="matches_proxy_rot",
            nice_name="Match Proxy Rotation",
            tooltip=_tooltip,
            layout=_layout,
        )
        _layout.addStretch()
        _tooltip = "When enabled, a different scale setup is created for the root joint and its children.\n"
        _tooltip += " 1. Segment scale compensation is disabled on the root joint's children.\n"
        _tooltip += " 2. Inherit transformations are disabled on the root joint.\n"
        _tooltip += " 3. The skeleton group's scale is directly connect to the root joint scale.\n"
        _tooltip += "This allows compatibility with game engines as the root drives the scale directly."
        self.add_module_attr_widget_checkbox(
            attr_name="enable_scale",
            tooltip=_tooltip,
            layout=_layout,
        )
        _layout.addStretch()
        self.add_widget_action_buttons()


# IK Base (Used by other AttrWidgets)
class AttrWidgetModuleBaseIK(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

    def add_setup_name_field(self):
        """
        Adds a setup name text field.
        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """
        return self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the name of the system."
            "\nThis is used as prefix by a few of the setup elements."
            "\nIdeally it should be unique, and describe the purpose of this module."
            '\ne.g. "thumb", "leg", or "arm".',
        )


class AttrWidgetModuleGenericIK(AttrWidgetModuleBaseIK):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Generic IK Preferences")
        self.add_setup_name_field()
        self.add_module_attr_widget_checkbox(
            attr_name="create_twist_joints",
            nice_name="Create Twist Joints",
            tooltip="When active, two twist joints will be included along with their twist setup nodes.\n"
            "These joints are placed between the main joints in hierarchy. Two twist joints per parent/child.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="ik_world",
            nice_name="IK Ctrl World Oriented",
            tooltip="Sets the IK controls in world orientation instead of using the orientation found in the proxy.\n"
            "When checked, the orientation of the end/effector control will match the origin/world.\nWhen unchecked"
            ", the orientation of the joints is used to determine the end/effector control's orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="auto_pole_vector",
            nice_name="Auto Pole Vector",
            tooltip="Applies an automation that makes the pole vector control follow the end/effector control.",
        )
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_mid_rot",
            min_double=-180,
            max_double=180,
            nice_name="Control Pose Elbow Rotation",
            tooltip="Controls the offset added to the elbow pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "Is often necessary to get the correct elbow behaviour due to the solver implied direction.",
        )

        self.add_widget_action_buttons()


class AttrWidgetModuleArm(AttrWidgetModuleBaseIK):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Arm Preferences")
        self.add_setup_name_field()
        self.add_module_attr_widget_checkbox(
            attr_name="clavicle_world",
            nice_name="Clavicle Ctrl World Orientation",
            tooltip="Sets the clavicle ctrl in world orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="create_twist_joints",
            nice_name="Create Twist Joints",
            tooltip="When active, two twist joints will be included along with their twist setup nodes.\n"
            "These joints are placed between the main joints in hierarchy. Two twist joints per parent/child.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="ik_world",
            nice_name="IK Ctrl World Oriented",
            tooltip="Sets the IK controls in world orientation instead of using the orientation found in the proxy.\n"
            "When checked, the orientation of the end/effector control will match the origin/world.\nWhen unchecked"
            ", the orientation of the joints is used to determine the end/effector control's orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="auto_pole_vector",
            nice_name="Auto Pole Vector",
            tooltip="Applies an automation that makes the pole vector control follow the end/effector control.",
        )
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_elbow_rot",
            min_double=-180,
            max_double=180,
            nice_name="Rig Pose Elbow Rotation",
            tooltip="Controls the offset added to the elbow pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "Is often necessary to get the correct elbow behaviour due to the solver implied direction.",
        )
        self.add_module_attr_widget_double3_spinbox(
            attr_name="rig_pose_clavicle_rot",
            nice_name="Control Pose Clavicle Rotation",
            tooltip="Controls the offset added to the clavicle pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "This will help when a different rotation in the clavicle is necessary to achieve the TPose.",
            minimum=-360,
            maximum=360,
        )
        self.add_widget_action_buttons()


class AttrWidgetModuleAttributeHub(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Attribute Hub Preferences")
        self.add_widget_code_data_editor()
        self.add_widget_auto_serialized_fields(ignore_attrs=["parent_constraint_type", "attr_mapping", "attr_values"])
        import gt.core.constraint as core_cnstr

        _potential_constraints = [
            core_cnstr.ConstraintTypes.POINT,
            core_cnstr.ConstraintTypes.PARENT,
            core_cnstr.ConstraintTypes.ORIENT,
        ]
        self.add_module_attr_widget_combobox(
            attr_name="parent_constraint_type",
            items=_potential_constraints,
        )
        # Create and Add Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_dictionary_editor(attr_name="attr_mapping", layout=_layout)
        self.add_module_attr_widget_dictionary_editor(attr_name="attr_values", layout=_layout)
        self.content_layout.addLayout(_layout)
        self.add_widget_action_buttons()


class AttrWidgetModuleSpine(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self._cog_parent_combobox = None

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Spine Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["spine_number", "dropoff_rate", "cog_parent", "world_ctrls"]
        )  # those have specific ranges
        spine_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="spine_number",
            min_int=1,
            tooltip="Number of spine elements between the hip and the chest.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=spine_num_slider)
        spine_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.add_module_attr_widget_double_slider(
            attr_name="dropoff_rate",
            min_double=0.1,
            max_double=10,
            tooltip="Dropoff value applied to the spine ribbon skin weights.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="world_ctrls",
            nice_name="World Oriented Ctrls",
            tooltip="Sets the spine ctrls in world orientation.",
        )
        self.add_cog_parent_combobox()
        self.add_widget_action_buttons()

    def refresh_proxies(self, *args, slider):
        """
        Refreshes the proxies based on the value from the provided slider.

        Args:
            *args: Additional arguments (ignored).
            slider (QtSlider or similar): Slider widget providing the spine number value.
        """
        if slider:
            # set spine number
            spine_number = int(slider.int_value())
            self.module.set_spine_number(spine_number)
            # refresh interface
            self.refresh_proxy_basic_table()

    def add_cog_parent_combobox(self, cog_parent_attr="cog_parent"):
        """
        Adds a combo box widget to select an alternative parent for the COG control.

        The combo box is populated with potential driver options, including a 'No Parent Override' choice.
        It sets the current selection based on the module's current attribute value and connects a handler
        to respond to user changes.

        Args:
            cog_parent_attr (str): The attribute name on the module representing the current COG parent.
                                   Defaults to "cog_parent".
        """
        # Create Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"COG Parent:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        self._cog_parent_combobox = ui_qt.QtWidgets.QComboBox()
        self._cog_parent_combobox.setFixedHeight(30)
        tooltip = "Determines an alternative parent for the COG control"
        label.setToolTip(tooltip)
        self._cog_parent_combobox.setToolTip(tooltip)
        # Populate ComboBox
        driver_pairs = self.get_potential_drivers_list(as_nice_name_pairs=True)
        driver_pairs.insert(0, [None, "No Parent Override"])  # Add None item (No Parent)
        for index, (driver_uuid, nice_name) in enumerate(driver_pairs):
            self._cog_parent_combobox.addItem(nice_name)  # Add the nice name
            self._cog_parent_combobox.setItemData(index, driver_uuid)  # Attach the internal value
        # Get Current Value And Set Combobox
        _module_value = getattr(self.module, cog_parent_attr)
        self.set_cog_parent_combobox(_module_value)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(self._cog_parent_combobox)
        # Connect
        self._cog_parent_combobox.currentIndexChanged.connect(self.on_cog_parent_combobox_change)

    def on_cog_parent_combobox_change(self, index):
        """
        If the COG parent combobox changes, it updates the module variable value according to the driver_uuid value.
        Args:
            index: Index the combobox was changed to
        """
        internal_value = self._cog_parent_combobox.itemData(index)
        setattr(self.module, "cog_parent", internal_value)

    def set_cog_parent_combobox(self, driver_uuid):
        """
        Sets the value of the COG Parent combobox
        Args:
            driver_uuid: The UUID to set. If unavailable, it will force add it.
        """
        # Loop through the items to find the one with matching internal value
        for index in range(self._cog_parent_combobox.count()):
            if self._cog_parent_combobox.itemData(index) == driver_uuid:
                self._cog_parent_combobox.setCurrentIndex(index)
                return

        # If the value is not found, add it as a new item
        logger.warning(f'Driver "{driver_uuid}" was not available as an option but was force added.')
        self._cog_parent_combobox.addItem(driver_uuid)  # Use the internal value as the "nice name"
        new_index = self._cog_parent_combobox.count() - 1
        self._cog_parent_combobox.setItemData(new_index, driver_uuid)  # Attach the internal value
        self._cog_parent_combobox.setCurrentIndex(new_index)  # Set the new item as the current index


class AttrWidgetModuleHead(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()

        self.add_widget_separator_line(label_text="Head Preferences")
        # Create and Add Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        neck_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="neck_number",
            min_int=1,
            tooltip="Number of neck elements between the base neck and the head.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=neck_num_slider)
        neck_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.add_module_attr_widget_text_field(attr_name="prefix_eye_left", layout=_layout)
        self.add_module_attr_widget_text_field(attr_name="prefix_eye_right", layout=_layout)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="build_jaw", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="build_eyes", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="delete_head_jaw_bind_jnt", layout=_layout)
        self.content_layout.addLayout(_layout)
        self.add_widget_action_buttons()

    def refresh_proxies(self, *args, slider):
        """
        Update the number of middle neck proxies based on the slider value and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            slider: Slider widget providing the new middle neck count.
        """
        if slider:
            # set spine number
            neck_number = int(slider.int_value())
            self.module.set_mid_neck_num(neck_number)
            # refresh interface
            self.refresh_proxy_basic_table()


class AttrWidgetModuleBipedArm(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Arm Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=[
                "setup_name",
                "clavicle_world",
                "rig_pose_elbow_rot",
                "rig_pose_clavicle_rot",
                "create_twist_joints",
                "auto_pole_vector",
            ]
        )
        self.add_module_attr_widget_checkbox(
            attr_name="create_twist_joints",
            nice_name="Create Twist Joints",
            tooltip="When active, two twist joints will be included along with their twist setup nodes.\n"
            "These joints are placed between the main joints in hierarchy. Two twist joints per parent/child.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="clavicle_world",
            nice_name="Clavicle Ctrl World Orientation",
            tooltip="Sets the clavicle ctrl in world orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="auto_pole_vector",
            nice_name="Auto Pole Vector",
            tooltip="Applies an automation that makes the pole vector control follow the end/effector control.",
        )
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_elbow_rot",
            min_double=-180,
            max_double=180,
            nice_name="Rig Pose Elbow Rotation",
            tooltip="Controls the offset added to the elbow pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "Is often necessary to get the correct elbow behaviour due to the solver implied direction.",
        )
        self.add_module_attr_widget_double3_spinbox(
            attr_name="rig_pose_clavicle_rot",
            nice_name="Control Pose Clavicle Rotation",
            tooltip="Controls the offset added to the clavicle pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "This will help when a different rotation in the clavicle is necessary to achieve the TPose.",
            minimum=-360,
            maximum=360,
        )
        self.add_widget_action_buttons()


class AttrWidgetModuleQuadRearLeg(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Quad Rear Leg Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=[
                "setup_name",
                "dir_rot",
                "rearupperleg_dir_curve",
                "rearlowerleg_dir_curve",
                "dir_curve",
            ]
        )
        setup_name_field = self.add_module_attr_widget_text_field(attr_name="setup_name", nice_name="Setup Name")
        refresh_name_func = partial(self.refresh_name, field=setup_name_field)
        self.add_widget_action_buttons()

    def refresh_name(self, *args, field):
        """
        Update the module's proxies name from the given input field and refresh the proxy table.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): The input widget containing the new proxy name.
        """
        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()


class AttrWidgetModuleBipedLeg(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Leg Preferences")
        self.add_widget_auto_serialized_fields(ignore_attrs=["setup_name", "rig_pose_knee_rot"])
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_knee_rot",
            min_double=-180,
            max_double=180,
            nice_name="Control Pose Knee Rotation",
            tooltip="Controls the offset added to the knee pose.",
        )
        self.add_widget_action_buttons()
        ensure_coplanarity_label = [
            cb for cb in self.findChildren(ui_qt.QtWidgets.QLabel) if "Ensure Coplanarity" in cb.text()
        ]
        if ensure_coplanarity_label:
            _tooltip = (
                "It ensures that the leg joints are coplanar, in order to improve "
                "the switching between IK and FK. True by default (recommended)."
            )
            ensure_coplanarity_label[0].setToolTip(_tooltip)


class AttrWidgetModuleQuadFrontLeg(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Quad Front Leg Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=[
                "setup_name",
                "dir_rot",
                "upperleg_dir_curve",
                "lowerleg_dir_curve",
                "dir_curve",
            ]
        )
        setup_name_field = self.add_module_attr_widget_text_field(attr_name="setup_name", nice_name="Setup Name")
        refresh_name_func = partial(self.refresh_name, field=setup_name_field)
        self.add_widget_action_buttons()

    def refresh_name(self, *args, field):
        """
        Update the module's proxies name based on the text from the given input field
        and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): The text input widget containing the new proxy name.
        """
        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()


class AttrWidgetModuleBipedFinger(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Finger Preferences")

        textfield_names = "Name"
        finger_mapping = {
            "meta": "meta_name",
            "thumb": "thumb_name",
            "index": "index_name",
            "middle": "middle_name",
            "ring": "ring_name",
            "pinky": "pinky_name",
            "extra": "extra_name",
        }
        # Add Other Attributes
        ignore_attrs = list(finger_mapping.keys()) + list(finger_mapping.values())
        self.add_widget_auto_serialized_fields(ignore_attrs=ignore_attrs)
        # Activation / Name Lines
        for activation_attr, name_attr in finger_mapping.items():
            # Create and Add Layout
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
            # Create Activation Checkbox and Name Textfield
            _checkbox = self.add_module_attr_widget_checkbox(attr_name=activation_attr, layout=_layout)
            _textfield = self.add_module_attr_widget_text_field(
                attr_name=name_attr, layout=_layout, nice_name=textfield_names
            )
            _textfield.setEnabled(_checkbox.isChecked())
            refresh_name_func = partial(self.refresh_name, field=_textfield, label=activation_attr)
            _textfield.editingFinished.connect(refresh_name_func)
            # Create Enabled Connection
            _checkbox.stateChanged.connect(_textfield.setEnabled)
            refresh_proxies_func = partial(self.refresh_proxies)
            _checkbox.stateChanged.connect(refresh_proxies_func)

        self.add_widget_action_buttons()

    def refresh_proxies(self, *args):
        """
        Refresh the module's proxies list and update the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
        """
        self.module.refresh_proxies_list()
        self.refresh_proxy_basic_table()

    def refresh_name(self, *args, field, label):
        """
        Update the name of a specific proxy and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): The text input widget containing the new proxy name.
            label (str): The label identifying which proxy to rename.
        """
        if field:
            proxy_name = field.text()
            self.module.set_proxies_name(label, proxy_name)
            self.refresh_proxy_basic_table()


class AttrWidgetModuleChain(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Chain Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["setup_name", "chain_base_name", "chain_num", "rot_order", "ctrl_shapes"]
        )
        setup_name_field = self.add_module_attr_widget_text_field(attr_name="setup_name", nice_name="Setup Name")
        refresh_name_func = partial(self.refresh_name, field=setup_name_field)
        setup_name_field.textEdited.connect(refresh_name_func)
        self.refresh_mid_proxies_checkbox = self.add_module_attr_widget_checkbox(
            attr_value=False,
            nice_name="Middle Proxies Refresh",
            tooltip="Toggles on and off the refresh of the middle proxies",
        )
        chain_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="chain_num",
            min_int=0,
            nice_name="Chain Divisions",
            tooltip="Number of chain divisions.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=chain_num_slider)
        chain_num_slider.intValueChanged.connect(refresh_proxies_func)
        rot_order_slider = self.add_module_attr_widget_int_slider(
            attr_name="rot_order",
            min_int=0,
            max_int=5,
            nice_name="Rotation Order",
            tooltip="Rotation order of the joints and controls.",
        )
        refresh_rot_func = partial(self.refresh_rot_order, slider=rot_order_slider)
        rot_order_slider.intValueChanged.connect(refresh_rot_func)
        self.add_module_attr_widget_text_field(attr_name="ctrl_shapes", nice_name="Ctrl Shapes")

        self.add_widget_action_buttons()

        # Initial Refresh
        self.refresh_proxies(slider=chain_num_slider)
        self.refresh_rot_order(slider=rot_order_slider)
        self.refresh_name(field=setup_name_field)

    def refresh_proxies(self, *args, slider):
        """
        Refresh the proxies based on the slider value.

        Args:
            *args: Additional positional arguments (ignored).
            slider (QSlider): Slider controlling the number of proxies in the chain.
        """
        if slider:
            # set chain number
            chain_number = int(slider.int_value())
            self.module.set_chain_num(chain_number)
            chain_base_item = tools_rig_utils.find_proxy_from_uuid(self.module.chain_base_proxy.get_uuid())
            if chain_base_item:
                if self.refresh_mid_proxies_checkbox.isChecked():
                    self.module._refresh_middle_proxies = True
            # refresh interface
            self.refresh_proxy_basic_table()

    def refresh_rot_order(self, *args, slider):
        """
        Refresh the rotation order of the module based on the slider value.

        Args:
            *args: Additional positional arguments (ignored).
            slider (QSlider): Slider controlling the rotation order.
        """
        if slider:
            # set rot order
            rot_order = int(slider.int_value())
            self.module.set_rot_order(rot_order)
            # refresh interface
            self.refresh_proxy_basic_table()

    def refresh_name(self, *args, field):
        """
        Refresh the proxy names based on the text field content.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): Text field containing the new proxy name.
        """
        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()


# Ribbon Base (Used by other AttrWidgets)
class AttrWidgetModuleBaseRibbon(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.setup_name_field = None  # Created by "add_setup_name_text_field"
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.ribbon_num_slider = None  # Created by "add_ribbon_sliders"
        self.ctrls_slider_widget = None  # Created by "add_ribbon_sliders"

    def add_setup_name_text_field(self, layout=None):
        """
        Adds a setup name text field and a checkbox to control auto-renaming.
        Args:
            layout (QLayout): A layout to parent the setup name to. Default is None.
        Returns:
            ConfirmableQLineEdit: The "setup_name" textfield QT object.
        """
        # Create a horizontal layout to hold the text field and checkbox
        name_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B

        self.setup_name_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the base name of the ribbon and its proxies.",
            layout=name_layout,  # Add to the new horizontal layout
        )
        refresh_name_func = partial(self.refresh_proxy_names, field=self.setup_name_field)
        self.setup_name_field.textEdited.connect(refresh_name_func)

        self.add_module_attr_widget_checkbox(
            attr_name="proxy_inherit_name",  # The attribute on the module
            nice_name="Auto-rename Proxies",
            layout=name_layout,
            tooltip="When checked, changing the 'Setup Name' will automatically\n"
            "rename all proxies (e.g., 'mySetupBase').\n"
            "Uncheck this to manually rename proxies without them being overwritten.",
        )

        # Add the horizontal layout to the main content layout
        self.content_layout.addLayout(name_layout)

        return self.setup_name_field

    def add_ribbon_checkboxes(self, add_equidistant=True):
        """
        Adds checkboxes used to determine th preferences for a ribbon.
        Args:
            add_equidistant (bool, optional): Whether to include the "Equidistant" checkbox.
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.refresh_mid_proxies_checkbox = self.add_module_attr_widget_checkbox(
            attr_name="middle_proxies_reset",
            nice_name="Middle Proxies Reset",
            layout=_layout,
            tooltip="When enabled, the positions of the middle proxies will be reset to maintain equal "
            "spacing whenever the number of divisions changes.\nThis behavior ensures consistent positioning and "
            "prevents unintended offsets from previous proxy data.\nIf you prefer to preserve all existing "
            "proxy positions regardless of division count updates, disable this option.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="cable_ctrls",
            attr_value=None,
            nice_name="Cable Controls",
            layout=_layout,
            tooltip="When active, FK controls remain independent allowing them to more easily act as a cable.\n"
            "This setup can help a ribbon be controlled by multiple parents where the start and end controls "
            "can follow different objects independently.",
        )
        if add_equidistant:
            self.add_module_attr_widget_checkbox(
                attr_name="equidistant",
                attr_value=None,
                nice_name="Equidistant",
                layout=_layout,
                tooltip="When active, an extra equidistant setup is added to the FK controls of the ribbon.\n"
                "This setup makes it so the global and effector controls influence the FK controls.\n"
                "This behavior can be controlled through an influence attribute added to the ribbon global control.\n"
                "The standard FK behavior will still happen when the equidistant influence is deactivated.",
            )
        self.add_module_attr_widget_checkbox(
            attr_name="rotate_ribbon",
            attr_value=None,
            nice_name="Rotate Ribbon",
            layout=_layout,
            tooltip="When active, the generated ribbon is rotated 90 degrees.\n"
            "A rotated ribbon will output slightly different rotation priorities to the skin joints.\n"
            "This happens because being a plane, the ribbon rotation determines how the curvature is interpreted.\n"
            "e.g. It might move parallel to one another or aim towards one another.",
        )
        self.content_layout.addLayout(_layout)

    def add_ribbon_sliders(self):
        """
        Adds sliders used to determine the number of divisions and controls in a ribbon.
        """
        _min_divisions_int = 1
        _max_divisions_int = 25
        self.ribbon_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="divisions",
            min_int=_min_divisions_int,
            max_int=_max_divisions_int,
            nice_name="Number of Mid Joints",
            tooltip="Determines how many divisions the middle of the ribbon should have, "
            "which also determines the number of skinning middle.\n"
            "(Start and End joints are not counted in this number)",
        )
        refresh_proxies_func = partial(self.refresh_proxies_num, slider=self.ribbon_num_slider)
        self.ribbon_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.ribbon_num_slider.intValueChanged.connect(self.refresh_max_ctrl_num)

        self.ctrls_slider_widget = self.add_module_attr_widget_int_slider(
            attr_name="num_ctrls",
            min_int=_min_divisions_int,
            max_int=_max_divisions_int,
            nice_name="Number of Mid Controls",
            tooltip="Determines the number of in-between controls generated by the ribbon.\n"
            "(Start and End controls are not counted in this number)",
        )
        refresh_ctrls_func = partial(self.refresh_num_ctrls, slider=self.ctrls_slider_widget)
        self.ctrls_slider_widget.intValueChanged.connect(self.refresh_max_ctrl_num)
        self.ctrls_slider_widget.intValueChanged.connect(refresh_ctrls_func)

        self.add_module_attr_widget_int_slider(
            attr_name="span_multiplier",
            min_int=1,
            max_int=10,
            nice_name="Span Multiplier",
            tooltip="Multiplies the number of spans on a generated ribbon.\n"
            "More spans can give the user more precise control over the skin weight of the ribbon.\n"
            "This can be used to create harder transitions between one control and another for different effects.",
        )

    def add_ribbon_shapes_text_fields(self):
        """Adds text-field responsible for the shapes used by this ribbon"""
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_text_field(attr_name="fk_ctrl_shapes", nice_name="FK Ctrl Shapes", layout=_layout)
        self.add_module_attr_widget_text_field(attr_name="ik_ctrl_shapes", nice_name="IK Ctrl Shapes", layout=_layout)
        self.content_layout.addLayout(_layout)

    def refresh_proxies_num(self, *args, slider):
        """
        Refreshes the proxy data and table to reflect updated preferences, specifically, the number of proxies.
        Args:
            slider (QSlider): Slider used to determine the number of divisions.
        """
        if slider and core_session.is_script_in_interactive_maya():
            # Set ribbon number
            divisions_num = int(slider.int_value())
            self.module.set_divisions_num(divisions=divisions_num)
            # Marking refresh middle proxies
            ribbon_base_item = tools_rig_utils.find_proxy_from_uuid(self.module.base_proxy.get_uuid())
            if ribbon_base_item:
                if self.refresh_mid_proxies_checkbox.isChecked():
                    self.module.middle_proxies_reset = True
            # Update num ctrls to not overpass divisions
            widget_num_ctrls = self.ctrls_slider_widget.value()
            if widget_num_ctrls > self.module.divisions:
                self.ctrls_slider_widget.set_int_value(self.module.divisions)
            # Refresh interface
            self.refresh_proxy_basic_table()

    def refresh_num_ctrls(self, *args, slider):
        """
        Refreshes the number of controls
        Args:
            slider (QSlider): QSlider used to extract the new number of controls.
        """
        if slider:
            widget_num_ctrls = int(slider.int_value())
            if widget_num_ctrls > self.module.divisions:
                slider.blockSignals(True)
                slider.set_int_value(self.module.divisions)
                slider.linked_spin_box.setValue(self.module.divisions)
                slider.blockSignals(False)

    def refresh_proxy_names(self, *args, field):
        """
        Refreshes the name of the proxies of this module. So they can be displayed in the UI.
        Args:
            field (QLineEdit): A field to get the name of the setup from.
        """
        if not args:  # Only run if triggered by a signal that sends arguments
            return

        if not self.module.proxy_inherit_name:
            return  # Exit early if auto-rename is off

        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()

    def refresh_max_ctrl_num(self):
        """Force the num of controls to be less than the number of divisions"""
        ribbon_num_slider_int = int(self.ribbon_num_slider.int_value())
        ctrls_slider_widget_int = int(self.ctrls_slider_widget.int_value())
        if ctrls_slider_widget_int > ribbon_num_slider_int:
            self.ctrls_slider_widget.set_int_value(ribbon_num_slider_int)


class AttrWidgetModuleRibbonGeneric(AttrWidgetModuleBaseRibbon):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        # --------------------------------------- Ribbon Preferences ---------------------------------------
        self.add_widget_separator_line(label_text="Ribbon Preferences")
        # Naming
        self.setup_name_field = None  # Created by "add_setup_name_text_field"
        self.add_setup_name_text_field()
        # Rotation Order
        self.add_module_rot_order_combobox()
        # Checkboxes
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.add_ribbon_checkboxes()
        # Sliders
        self.ribbon_num_slider = None  # Created by "add_ribbon_sliders"
        self.ctrls_slider_widget = None  # Created by "add_ribbon_sliders"
        self.add_ribbon_sliders()
        # Shapes
        self.add_ribbon_shapes_text_fields()
        # Action Buttons
        self.add_widget_action_buttons()
        # Initial Refresh
        self.refresh_proxies_num(slider=self.ribbon_num_slider)
        self.refresh_proxy_names(field=self.setup_name_field)


class AttrWidgetModuleRibbonQuadSpine(AttrWidgetModuleBaseRibbon):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()

        # ------------------------------------ Quadruped Spine Preferences ------------------------------------
        self.add_widget_separator_line(label_text="Quadruped Spine Preferences")
        # Naming
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.setup_name_field = self.add_setup_name_text_field(layout=_layout)
        self.add_module_attr_widget_text_field(
            attr_name="direction_name",
            nice_name="Direction Name",
            tooltip="Determines the name of the direction control.",
            layout=_layout,
        )
        self.setup_name_field.textEdited.connect(self.refresh_proxy_names)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.base_field = self.add_module_attr_widget_text_field(
            attr_name="hips_name",
            nice_name="Hips Name (Base)",
            tooltip="Determines the name of the base control. In this case the hips of the spine.",
            layout=_layout,
        )
        self.end_field = self.add_module_attr_widget_text_field(
            attr_name="chest_name",
            nice_name="Chest Name (End)",
            tooltip="Determines the name of the end control. In this case the chest of the spine.",
            layout=_layout,
        )
        self.content_layout.addLayout(_layout)
        self.base_field.textEdited.connect(self.refresh_proxy_names)
        self.end_field.textEdited.connect(self.refresh_proxy_names)
        # Rotation Order
        self.add_module_rot_order_combobox()
        # Checkboxes
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.add_ribbon_checkboxes(add_equidistant=False)
        # Sliders
        self.ribbon_num_slider = None  # Created by "add_ribbon_sliders"
        self.ctrls_slider_widget = None  # Created by "add_ribbon_sliders"
        self.add_ribbon_sliders()
        # Shapes
        self.add_ribbon_shapes_text_fields()
        # Action Buttons
        self.add_widget_action_buttons()
        # Initial Refresh
        self.refresh_proxies_num(slider=self.ribbon_num_slider)
        self.refresh_proxy_names()

    def refresh_proxy_names(self, *args, **kwargs):
        """
        Refreshes the name of the proxies of this module, so they can be displayed in the UI.
        This is an override function made specifically for the quadruped spine module.
        """
        setup_name = self.setup_name_field.text()
        base_name = self.base_field.text()
        end_name = self.end_field.text()
        self.module.set_proxies_name(setup_name=setup_name, base=base_name, end=end_name)
        self.refresh_proxy_basic_table()


class AttrWidgetModuleSocket(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()

        self.add_widget_separator_line(label_text="Socket Preferences")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)

        _checkbox = self.add_module_attr_widget_checkbox(attr_name="add_child", layout=_layout)
        parent_text_field = self.add_module_attr_widget_text_field(attr_name="parent_tag", layout=_layout)
        child_text_field = self.add_module_attr_widget_text_field(attr_name="child_tag", layout=_layout)

        _layout.setEnabled(_checkbox.isChecked())
        # Create Enabled Connection
        _checkbox.stateChanged.connect(parent_text_field.setEnabled)
        _checkbox.stateChanged.connect(child_text_field.setEnabled)

        self.add_widget_action_buttons()


class AttrWidgetModuleMetaHumanFace(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_parent()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="MetaHuman Face Preferences")
        self.add_widget_auto_serialized_fields(ignore_attrs="file_path")
        self.add_module_attr_widget_path(attr_name="file_path")
        self.add_widget_action_buttons()


class AttrWidgetModulePiston(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """

        super().__init__(parent, *args, **kwargs)
        self._end_parent_combobox = None

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_module_end_combobox()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Piston Preferences")

        name_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B

        self.setup_name_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the base name of the piston and its proxies.",
            layout=name_layout,
        )
        refresh_name_func = partial(self.refresh_proxy_names, field=self.setup_name_field)
        self.setup_name_field.textEdited.connect(refresh_name_func)
        self.add_module_attr_widget_checkbox(
            attr_name="proxy_inherit_name",  # The attribute on the module
            nice_name="Auto-rename Proxies",
            layout=name_layout,
            tooltip="When checked, changing the 'Setup Name' will automatically\n"
            "rename all proxies (e.g., 'mySetupBase').\n"
            "Uncheck this to manually rename proxies without them being overwritten.",
        )
        # Add the horizontal layout to the main content layout
        self.content_layout.addLayout(name_layout)

        self.add_module_attr_widget_text_field(attr_name="ctrl_shapes", nice_name="Control Shape")

        self.add_module_attr_widget_checkbox(
            attr_name="parent_end_joint",
            nice_name="Parent End Joint to Base Joint",
            tooltip="When checked, it will parent the end joint to the base joint.",
        )
        self.add_widget_action_buttons()
        self.refresh_proxy_names(field=self.setup_name_field)

    def add_widget_module_end_combobox(self):
        """
        Adds a combo box widget to select an alternative parent for the end piston ctrl.

        The combo box is populated with potential driver options, including a 'No Parent Override' choice.
        It sets the current selection based on the module's current attribute value and connects a handler
        to respond to user changes.

        """
        # Create Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"End Ctrl Parent:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        self._end_parent_combobox = ui_qt.QtWidgets.QComboBox()
        self._end_parent_combobox.setFixedHeight(30)
        tooltip = "Determines an alternative parent for the End Piston control"
        label.setToolTip(tooltip)
        self._end_parent_combobox.setToolTip(tooltip)
        # Populate ComboBox
        driver_pairs = self.get_potential_parent_list(target=self.module)
        driver_pairs.insert(0, ["No Parent Override", None])  # Add None item (No Parent)
        for index, (nice_name, driver) in enumerate(driver_pairs):
            self._end_parent_combobox.addItem(nice_name)  # Add the nice name
            self._end_parent_combobox.setItemData(index, driver)  # Attach the internal value
        # Get Current Value And Set Combobox
        _module_value = getattr(self.module, "end_parent")
        self.set_end_parent_combobox(driver_uuid=_module_value)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(self._end_parent_combobox)
        # Connect
        self._end_parent_combobox.currentIndexChanged.connect(self.on_end_parent_piston_combo_box_changed)

    def on_end_parent_piston_combo_box_changed(self, index):
        """
        Handle the change in the parent combo box for the proxy table.

        Args:
            index (int): Index of the selected item.
        """
        internal_value = self._end_parent_combobox.itemData(index)
        end_parent_uuid = internal_value.get_uuid()
        setattr(self.module, "end_parent", end_parent_uuid)

    def set_end_parent_combobox(self, driver_uuid):
        """
        Sets the value of the COG Parent combobox
        Args:
            driver_uuid: The UUID to set. If unavailable, it will force add it.
        """
        # Loop through the items to find the one with matching internal value
        self.refresh_known_proxy_dict()
        for index in range(1, self._end_parent_combobox.count()):
            _parent_proxy = self._end_parent_combobox.itemData(index)
            _parent_uuid = _parent_proxy.get_uuid()
            if driver_uuid == _parent_uuid:
                self._end_parent_combobox.setCurrentIndex(index)
                return

        # If the value is not found, add it as a new item
        logger.warning(f'Driver "{driver_uuid}" was not available as an option.')
        self._end_parent_combobox.setCurrentIndex(0)

    def get_potential_parent_list(self, target, parent_filter=False):
        """
        Gets all potential parent targets.
        An extra initial item called "No Parent" is also added for the proxies without parents.
        Args:
            target (Proxy, Module): A proxy or module object used to determine current parent and pre-select it.
            parent_filter (bool, optional): If True, it will only populate the combobox with proxies available under
                                          the parent modules.
        Returns:
            QComboBox: A pre-populated combobox with potential parents. Current parent is also pre-selected.
        """
        self.refresh_known_proxy_dict()
        drivers_list = []
        # Get Variables
        _proxy_uuid = None
        if target and hasattr(target, "get_uuid"):  # Is proxy
            _proxy_uuid = target.get_uuid()
        _proxy_parent_uuid = target.get_parent_uuid()
        _parent_module = self.known_proxies.get(_proxy_parent_uuid, None)
        if _parent_module:
            _parent_module = _parent_module[1]  # Get second item in tuple (module)
        # Populate Combobox
        for key, (_proxy, _module) in self.known_proxies.items():
            if parent_filter and _parent_module and _parent_module != _module:
                continue
            if key == _proxy_uuid:
                continue  # Skip Itself
            description = f"{str(_proxy.get_name())}"
            module_name = _module.get_name()
            if module_name:
                description += f" : {str(module_name)}"
                drivers_list.append([description, _proxy])
        return drivers_list

    def refresh_proxy_names(self, *args, field):
        """
        Refreshes the name of the proxies of this module. So they can be displayed in the UI.
        Args:
            field (QLineEdit): A field to get the name of the setup from.
        """
        if not args:  # Only run if triggered by a signal that sends arguments
            return

        if not self.module.proxy_inherit_name:
            return  # Exit early if auto-rename is off

        if field:
            module_name = field.text()
            self.module.set_proxies_name(name=module_name)
            self.refresh_proxy_basic_table()


class AttrWidgetModuleAnimMassReferences(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_parent()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Animation Mass References Preferences")

        attributes = vars(self.module)
        weight_attrs = [attr for attr in attributes if attr.endswith("_weight")]
        color_attrs = [attr for attr in attributes if attr.endswith("_color")]

        self.add_module_attr_widget_int_slider(
            attr_name="com_locator_scale",
            attr_value=None,
            min_int=1,
            max_int=50,
            tooltip="Size of the center of mass locator.",
        )

        self.add_widget_auto_serialized_fields(ignore_attrs=weight_attrs + color_attrs + ["com_locator_scale"])

        for attr in weight_attrs:
            self.add_module_attr_widget_double_slider(
                attr_name=attr,
                min_double=0,
                max_double=50,
                precision=3,
            )

        for attr in color_attrs:
            self.add_module_attr_widget_double3_spinbox(
                attr_name=attr,
                precision=3,
            )


class AttrWidgetModuleGroup(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.add_widget_module_header(activation=False)

        # Activate Children
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        activate_btn = ui_qt.QtWidgets.QPushButton("Activate Children Modules")
        activate_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_green_circle))
        activate_btn_func = partial(self.on_set_activation_btn_pressed, True)
        activate_btn.clicked.connect(activate_btn_func)
        activate_btn.clicked.connect(self.call_parent_refresh)
        _layout.addWidget(activate_btn)
        self.content_layout.addLayout(_layout)

        # Deactivate Children
        deactivate_btn = ui_qt.QtWidgets.QPushButton("Deactivate Children Modules")
        deactivate_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_red_circle))
        deactivate_btn_func = partial(self.on_set_activation_btn_pressed, False)
        deactivate_btn.clicked.connect(deactivate_btn_func)
        deactivate_btn.clicked.connect(self.call_parent_refresh)
        _layout.addWidget(deactivate_btn)
        self.content_layout.addLayout(_layout)

    def on_set_activation_btn_pressed(self, state):
        """
        Sets the activation state of the children modules
        Args:
            state (bool): New state of the children modules. True is active, False is inactive
        """
        parent_uuid = self.module.proxies[0].get_uuid()
        self.set_children_modules_activation_state(parent_uuid=parent_uuid, state=state)

    def set_children_modules_activation_state(self, parent_uuid, state):
        """
        Sets the activation state of the children modules
        Args:
            state (bool): New state of the children modules. True is active, False is inactive
            parent_uuid (str): UUID of the parent group used for the operation
        """
        modules = self.project.get_modules()

        children = []
        for module in modules:
            if module.get_parent_uuid() == parent_uuid:
                children.append(module)

        for child in children:
            if not child.bypass_activation:
                child.set_active_state(state)
            if isinstance(child, tools_rig_modules.RigModules.Utils.ModuleGroup):
                _sub_parent_uuid = child.proxies[0].get_uuid()
                self.set_children_modules_activation_state(parent_uuid=_sub_parent_uuid, state=state)


class AttrWidgetModuleNewScene(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        code_editor_tooltip = """Use the default dictionary as an example of potential scene options."""

        self.add_widget_separator_line(label_text="New Scene Preferences")

        self.add_module_attr_widget_dictionary_editor(
            attr_name="scene_options", dict_editor_tooltip=code_editor_tooltip
        )


class AttrWidgetModuleImportFile(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        self.add_widget_separator_line(label_text="Import File Preferences")

        self.add_module_attr_widget_path(attr_name="file_path")
        ignore_attrs = [
            "file_path",
            "merge_namespaces_on_clash",
            "reference",
            "deactivate_drawing_overrides",
            "purge_display_layers",
            "purge_namespaces",
            "purge_keyframes",
            "proxy_import",
        ]
        self.add_widget_auto_serialized_fields(ignore_attrs=ignore_attrs)

        # Create and Add Layout Checkbox Layouts
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="merge_namespaces_on_clash", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="reference", layout=_layout)
        _tooltip = (
            'If active, the import function will also take place when entering in "Edit Proxy" mode.\n'
            "This happens independently of the order settings, and only happens when editing the proxy.\n"
            "The imported elements are automatically parented to a reference group for convenience.\n"
            "This option allows for one import module to simultaneously align proxies and bind of the skin weights."
        )
        self.add_module_attr_widget_checkbox(attr_name="proxy_import", layout=_layout, tooltip=_tooltip)
        self.content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Extra Module Features")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="deactivate_drawing_overrides", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="purge_display_layers", layout=_layout)
        self.content_layout.addLayout(_layout)

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="purge_namespaces", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="purge_keyframes", layout=_layout)
        self.content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Utilities")
        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Import File")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_import_file))
        import_file_btn.clicked.connect(self.module.import_file)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open File Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_file_dir)
        _layout.addWidget(open_dir_btn)
        self.content_layout.addLayout(_layout)

    def open_file_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)


class AttrWidgetModuleSkinWeights(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        self.add_widget_separator_line(label_text="Skin Weights Preferences")

        self.add_module_attr_widget_path(attr_name="influences_dir", dir_only=True)
        self.add_module_attr_widget_path(attr_name="weights_dir", dir_only=True)

        # Preferences
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.remove_unused_infl_chk = self.add_module_attr_widget_checkbox(
            attr_name="remove_unused_influences", layout=_layout
        )

        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir", nice_name="Clear Target Directory When Writing", layout=_layout
        )
        self.scroll_content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Utilities")

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Open Influences Directory")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        import_file_btn.clicked.connect(self.open_influence_dir)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Weights Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_weights_dir)
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

        self.add_widget_read_write_buttons()

    def open_influence_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.influences_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def open_weights_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.weights_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def add_widget_read_write_buttons(self):
        """
        Adds actions buttons (read proxy, build proxy, etc…)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Influences
        write_influences = ui_qt.QtWidgets.QPushButton("Write Influences")
        write_influences.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_influences.clicked.connect(self.write_influences)
        write_influences.setToolTip("Write Influences From Selection")
        # Weights
        write_weights = ui_qt.QtWidgets.QPushButton("Write Weights")
        write_weights.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_weights.clicked.connect(self.write_weights)
        write_weights.setToolTip("Write Weights From Selection")
        # Layout
        _layout.addWidget(write_influences)
        _layout.addWidget(write_weights)
        self.scroll_content_layout.addLayout(_layout)

    def write_influences(self):
        """Writes influences to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_influences_from_selection(clear_target_dir=clear_target_dir)

    def write_weights(self):
        """Writes weights to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_weights_from_selection(
            clear_target_dir=clear_target_dir,
            remove_unused_inf=self.remove_unused_infl_chk.isChecked(),
        )

    def set_module_remove_unused_influences(self):
        """Sets the checkbox remove unused influences user choice into the module variable."""
        self.module.set_remove_unused_influences(status=self.remove_unused_infl_chk.isChecked())


class AttrWidgetModuleShapesSnapshot(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Shapes Snapshot Preferences")
        # Purge Directory?
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        checkbox_label = ui_qt.QtWidgets.QLabel("Clear Target Directory When Writing: ")
        self.clear_target_dir_chk = ui_qt.QtWidgets.QCheckBox()
        self.clear_target_dir_chk.setChecked(False)
        _layout.addWidget(checkbox_label)
        _layout.addWidget(self.clear_target_dir_chk)
        self.scroll_content_layout.addLayout(_layout)

        self.add_module_attr_widget_path(attr_name="shapes_dir", dir_only=True)
        self.add_widget_read_write_buttons()

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Open Shapes Directory")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        import_file_btn.clicked.connect(self.open_shapes_dir)
        _layout.addWidget(import_file_btn)
        self.content_layout.addLayout(_layout)

    def open_shapes_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.shapes_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def add_widget_read_write_buttons(self):
        """
        Adds actions buttons (read proxy, build proxy, etc…)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Influences
        write_project_controls = ui_qt.QtWidgets.QPushButton("Write Project Controls")
        write_project_controls.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_project_controls.clicked.connect(self.write_project_controls)
        write_project_controls.setToolTip("Write Project Controls")
        # Weights
        write_selected_curves = ui_qt.QtWidgets.QPushButton("Write Curves From Selection")
        write_selected_curves.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_selected_curves.clicked.connect(self.write_selected_curves)
        write_selected_curves.setToolTip("Write Curves From Selection")
        # Layout
        _layout.addWidget(write_project_controls)
        _layout.addWidget(write_selected_curves)
        self.scroll_content_layout.addLayout(_layout)

    def write_project_controls(self):
        """Writes the shapes of the project controls"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_project_shapes(clear_target_dir=clear_target_dir)

    def write_selected_curves(self):
        """Writes the shapes of the selected objects"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_shapes_from_selection(clear_target_dir=clear_target_dir)


class AttrWidgetModuleExportSkeletalMesh(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Export Preferences")
        self.add_module_attr_widget_path(attr_name="export_dir", dir_only=True)
        self.add_module_attr_widget_text_field(attr_name="export_filename")

        # Export Options
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Poses
        poses = [core_naming.NamingConstants.Poses.APOSE, core_naming.NamingConstants.Poses.TPOSE]
        self.add_module_attr_widget_combobox(attr_name="export_pose", items=poses, layout=_layout)
        # Exporting Method
        methods = tools_rig_modules.RigModules.Utils.ModuleExportSkeletalMesh.RootLookupMethods.get_names()
        methods = [" ".join(word.title() for word in item.split("_")) for item in methods]
        combobox_label = ui_qt.QtWidgets.QLabel("Root Lookup Method:")
        combobox_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight)
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.addItems(methods)
        combobox.setCurrentIndex(self.module.root_lookup_method)
        combobox.currentIndexChanged.connect(self.update_root_lookup_method)
        _tooltip = (
            "The root lookup method determines which joints should be included when exporting a skeleton.\n"
            "Single Root: Uses the first detected joint under the skeleton group as project root. "
            "All children are included.\nSkinned Root: Find the top parents of the filtered meshes, and use "
            "them as project roots. All children are included.\nSkinned Only: Exports only the absolutely necessary "
            "hierarchy used to drive the filtered meshes are exported."
        )
        combobox.setToolTip(_tooltip)
        combobox_label.setToolTip(_tooltip)
        _layout.addWidget(combobox_label)
        _layout.addWidget(combobox, stretch=0)
        self.content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Mesh Filters")
        self.add_module_attr_widget_checkbox(attr_name="mesh_filter_short_names", nice_name="Filter Using Short Names")
        self.add_module_attr_widget_text_field(
            attr_name="mesh_filter_include",
            nice_name="Include Filter",
            placeholder="Include patterns. Accepts wild cards. Separated by commas.",
        )
        self.add_module_attr_widget_text_field(
            attr_name="mesh_filter_exclude",
            nice_name="Exclude Filter",
            placeholder="Exclude patterns. Accepts wild cards. Separated by commas.",
        )

    def update_root_lookup_method(self, index):
        """
        Uses the index of the combobox to define the root lookup method used by the SKM export module.
        Args:
            index (int): Index of the selected combobox item.
        """
        self.module.root_lookup_method = index


class AttrWidgetModuleSaveScene(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Save Scene Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        file_extensions = [".ma", ".mb"]
        self.add_module_attr_widget_combobox(attr_name="file_extension", items=file_extensions)
        # --------------------------------- Utilities ---------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        save_btn = ui_qt.QtWidgets.QPushButton("Save Scene")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.clicked.connect(self.save_scene_utility)
        save_btn.setToolTip("Saves the current scene.")
        _layout.addWidget(save_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_save_dir_utility)
        open_dir_btn.setToolTip("Opens the thumbnail directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def save_scene_utility(self):
        """Saves the scene using current preferences"""
        self.module.force_save_scene()

    def open_save_dir_utility(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        _parsed_path = os.path.dirname(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)


# Capture Base (Used by other AttrWidgets)
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


class AttrWidgetModuleThumbnailCapture(AttrWidgetModuleBaseCapture):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Thumbnail Capture Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        import gt.core.playblast as core_playblast

        file_extensions = core_playblast.ViewportImageFormats.get_all_formats()
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_combobox(attr_name="file_extension", items=file_extensions, layout=_layout)

        # Resolution (Width and Height)
        _min = 1
        _max = 7680
        self.add_module_attr_widget_int_spinbox(
            attr_name="width",
            min_int=_min,
            max_int=_max,
            tooltip="Width refers to the horizontal measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        self.add_module_attr_widget_int_spinbox(
            attr_name="height",
            min_int=_min,
            max_int=_max,
            tooltip="Height refers to the vertical measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )

        # Frame ------------------------------------------------
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        current_frame_checkbox = self.add_module_attr_widget_checkbox(attr_name="current_frame", layout=_layout)
        _layout.addStretch()
        self.frame_spinbox = self.add_module_attr_widget_int_spinbox(attr_name="frame", layout=_layout)
        current_frame_checkbox.toggled.connect(self.on_current_frame_checkbox_toggled)
        # Disable Spinbox if using current frame
        if self.module.current_frame:
            self.frame_spinbox.setEnabled(False)
        _layout.addStretch()

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="default_material",
            tooltip="When True, a default material will override all used materials. No textures or colors.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="x_ray",
            tooltip="When True, X-Ray mode is activated during the playblast.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="hide_curves",
            tooltip="When true, NURBS Curves are made invisible in the active panel for the thumbnail.\n"
            "This option does not affect the actual visibility of the objects, only the panel preference.\n"
            "The original value is restored after the thumbnail is saved.",
            layout=_layout,
        )

        self.add_widget_separator_line(label_text="Persp Camera Data")
        self.add_persp_camera_data_buttons()
        self.refresh_camera_buttons_enabled_state()

        # ---------------------------------- Utilities ----------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        capture_btn = ui_qt.QtWidgets.QPushButton("Capture Thumbnail")
        capture_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_thumbnail_capture))
        capture_btn.clicked.connect(self.capture_thumbnail)
        capture_btn.setToolTip("Captures a thumbnail using the current settings.")
        _layout.addWidget(capture_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_thumbnail_dir)
        open_dir_btn.setToolTip("Opens the thumbnail directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def capture_thumbnail(self):
        """Captures a thumbnail using the current settings"""
        self.module.capture_thumbnail()

    def open_thumbnail_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        _parsed_path = os.path.dirname(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def on_current_frame_checkbox_toggled(self, checked):
        """
        Handles checkbox toggling: disables spinbox if checked, enables if unchecked.
        Args:
            checked (bool): The state of the checkbox.
                            True if checked (spinbox should be disabled),
                            False if unchecked (spinbox should be enabled).
        """
        self.frame_spinbox.setEnabled(not checked)

    def on_add_metadata_toggled(self, state):
        """
        Enable or disable the metadata path QLineEdit based on the checkbox state.

        Args:
            state (int): The state of the checkbox.
                         The QLineEdit will be enabled only when the checkbox is checked.
        """
        self.asset_data_path_widget.setEnabled(state == ui_qt.QtLib.CheckState.Checked)


class AttrWidgetModulePlayblastCapture(AttrWidgetModuleBaseCapture):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Playblast Capture Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        import gt.core.playblast as core_playblast

        video_formats = core_playblast.ViewportPlayblastFormats.get_all_formats()
        combobox_format = self.add_module_attr_widget_combobox(
            attr_name="video_format", items=video_formats, layout=_layout
        )
        combobox_format.setMinimumWidth(150)

        # Resolution (Width and Height)
        _min = 1
        _max = 7680
        _spinbox_min_width = 150
        _layout.addStretch()
        spinbox_width = self.add_module_attr_widget_int_spinbox(
            attr_name="width",
            min_int=_min,
            max_int=_max,
            tooltip="Width refers to the horizontal measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        _layout.addStretch()
        spinbox_height = self.add_module_attr_widget_int_spinbox(
            attr_name="height",
            min_int=_min,
            max_int=_max,
            tooltip="Height refers to the vertical measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        spinbox_width.setMinimumWidth(_spinbox_min_width)
        spinbox_height.setMinimumWidth(_spinbox_min_width)

        # Start and End Frames
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        label = ui_qt.QtWidgets.QLabel("Frame Range:")
        label.setMinimumWidth(260)
        _layout.addWidget(label)
        _layout.addStretch()
        spinbox_start = self.add_module_attr_widget_int_spinbox(
            attr_name="start_frame",
            nice_name="Start",
            tooltip="Determines the frame when the playblast should start.",
            layout=_layout,
        )
        _layout.addStretch()
        spinbox_end = self.add_module_attr_widget_int_spinbox(
            attr_name="end_frame",
            nice_name="End",
            tooltip="Determines the frame when the playblast should end.",
            layout=_layout,
        )
        spinbox_start.setMinimumWidth(_spinbox_min_width)
        spinbox_end.setMinimumWidth(_spinbox_min_width)

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="show_ornaments",
            tooltip="When True, the playblast will include HUD elements such as the grid, camera name, and other info.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="default_material",
            tooltip="When True, a default material will override all used materials. No textures or colors.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="x_ray",
            tooltip="When True, X-Ray mode is activated during the playblast.",
            layout=_layout,
        )
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="hide_curves",
            tooltip="When true, NURBS Curves are made invisible in the active panel during recording.\n"
            "This option does not affect the actual visibility of the objects, only the panel preference.\n"
            "The original value is restored after the playblast recording is saved.",
            layout=_layout,
        )

        self.add_widget_separator_line(label_text="Persp Camera Data")
        self.add_persp_camera_data_buttons()
        self.refresh_camera_buttons_enabled_state()

        # Utilities -----------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        capture_btn = ui_qt.QtWidgets.QPushButton("Capture Playblast")
        capture_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_playblast_capture))
        capture_btn.clicked.connect(self.capture_playblast)
        capture_btn.setToolTip("Captures a playblast using the current settings.")
        _layout.addWidget(capture_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_playblast_dir)
        open_dir_btn.setToolTip("Opens the playblast directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def capture_playblast(self):
        """Captures a thumbnail using the current settings"""
        self.module.capture_playblast()

    def open_playblast_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        _parsed_path = os.path.dirname(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)


class AttrWidgetModuleCameraSetup(AttrWidgetModuleBaseCapture):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Camera Setup Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _layout.addStretch()
        cam_name_text_field = self.add_module_attr_widget_text_field(
            attr_name="camera_name",
            placeholder='camera path/name. e.g. "persp"',
            tooltip='This is the name of the camera affected by the operation. Often "persp".',
            layout=_layout,
        )
        cam_name_text_field.setMinimumWidth(300)
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="view_through_camera",
            tooltip="When True, the provided camera becomes the active camera of the current viewport.",
            layout=_layout,
        )
        _layout.addStretch()

        self.add_persp_camera_data_buttons(label="Camera Data:")
        self.refresh_camera_buttons_enabled_state()

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="default_material",
            tooltip="When True, a default material will override all used materials. No textures or colors.",
            layout=_layout,
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="x_ray",
            tooltip="When True, X-Ray mode is activated during the playblast.",
            layout=_layout,
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        _layout.addStretch()


class AttrWidgetModuleLoadScene(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Load Scene Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=False)
        # Utilities
        self.add_widget_separator_line(label_text="Utilities")

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Load Scene")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_import_file))
        import_file_btn.clicked.connect(self.module.force_load_scene)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open File Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_file_dir)
        _layout.addWidget(open_dir_btn)
        self.content_layout.addLayout(_layout)

        # Warning
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _tooltip = (
            "When enabled, this module will suppress warnings for files loaded from outside the rig project "
            "path.\nThis is useful when the project is based on another rig project and changes need to be "
            "quickly propagated."
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="bypass_warnings", nice_name="Suppress External File Warnings", tooltip=_tooltip, layout=_layout
        )
        _layout.addStretch()

    def open_file_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)


class AttrWidgetModuleROMLoader(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Load Range of Motion Preferences")
        self.add_module_attr_widget_path(attr_name="target_file_path", dir_only=False)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.addWidget(ui_qt.QtWidgets.QLabel("Range of Motion Definition:"))
        self.definition_combobox = self.add_widget_definition_combobox(
            initial_definition=self.module.retarget_definition
        )
        self.definition_combobox.currentIndexChanged.connect(self.on_definition_combobox_changed)
        _layout.addWidget(self.definition_combobox)
        self.content_layout.addLayout(_layout)
        # Preferences
        self.add_widget_separator_line(label_text="Comparison (Source) Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="comparison_offset",
            tooltip="If True, the weight of the comparison A+B setup is set to 1.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="comparison_visibility",
            tooltip="Defines the visibility of the source skeleton/mesh.",
            layout=_layout,
        )

    @staticmethod
    def add_widget_definition_combobox(initial_definition):
        """
        Creates a populated combobox with all potential retarget (ROM) definitions.
        Args:
            initial_definition (str, None): Name of the initial definition to be selected.
        Returns:
            QComboBox: A pre-populated combobox with potential definitions. Initial definition is also pre-selected.
        """
        import gt.tools.retargeter.retargeter_constants as tools_rt_const

        rom_folder = tools_rt_const.RetargeterConstants.DEFAULT_ROM_DATA_FOLDER
        definitions = set()
        for file in os.listdir(rom_folder):
            if os.path.isfile(os.path.join(rom_folder, file)):
                name_without_ext, _ = os.path.splitext(file)
                definitions.add(name_without_ext)

        # Create Combobox
        combobox = ui_qt.QtWidgets.QComboBox()

        # Populate Combobox
        for definition in list(definitions):
            combobox.addItem(core_str.snake_to_title(definition), definition)

        # Set Initial or Add Unknown Initial Probe (Not present in project)
        if initial_definition is None:
            return combobox
        if initial_definition in definitions:
            for index in range(combobox.count()):
                _definition = combobox.itemData(index)
                if _definition and initial_definition == _definition:
                    combobox.setCurrentIndex(index)
        return combobox

    def on_definition_combobox_changed(self, index):
        """
        Slot function called when the definition combobox selection changes.
        Updates the retarget_definition in the module based on the newly selected item.

        Args:
            index (int): The index of the currently selected item in the combobox.
        """
        snake_case_name = self.definition_combobox.itemData(index)
        if snake_case_name:
            self.module.retarget_definition = snake_case_name


class AttrWidgetModuleEnumVariants(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        import gt.tools.auto_rigger.modules.module_enum_variants as tools_mod_enum_vars

        self._KEYS = tools_mod_enum_vars.EnumVariantsKeys

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Enum Section -----------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Enum Variants")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _tooltip = "Name or path to the object that will receive the created ENUM. Often a control."
        self.add_module_attr_widget_text_field(
            attr_name="enum_target",
            layout=_layout,
            placeholder="C_visibility_CTRL",
            tooltip=_tooltip,
        )
        _tooltip = 'String used for when nothing should change in an ENUM. e.g. "None", or "Nothing".'
        self.add_module_attr_widget_text_field(
            attr_name="none_label",
            layout=_layout,
            placeholder="None",
            tooltip=_tooltip,
        )
        _tooltip = "Attribute to be updated using the ENUM. When the corresponding ENUM is selected, \n"
        _tooltip += 'this attribute is set to "1", when not selected, it is set to "0". Usually used with "visibility".'
        self.add_module_attr_widget_text_field(
            attr_name="driven_attr",
            layout=_layout,
            placeholder="visibility",
            tooltip=_tooltip,
        )
        # Expand/Collapse Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.toggle_enums_btn = ui_qt.QtWidgets.QPushButton()  # Label automatically updated when initializing
        self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
        self.toggle_enums_btn.setCheckable(True)
        self.toggle_enums_btn.setChecked(self.module.enum_frame_expanded)
        self.toggle_enums_btn.clicked.connect(self.refresh_toggle_enums_collapsed_state)
        _layout.addWidget(self.toggle_enums_btn)
        # Add Enum Button
        add_enum_btn = ui_qt.QtWidgets.QPushButton("Add Enum")
        add_enum_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_enum_btn.setToolTip(_tooltip)
        _layout.addWidget(add_enum_btn)
        add_enum_btn.clicked.connect(self.on_add_enum_dict_clicked)

        # Scroll Area ---
        self.enum_scroll = ui_qt.QtWidgets.QScrollArea()
        self.enum_scroll.setWidgetResizable(True)
        self.enum_scroll.setMinimumHeight(220)  # minimum height, not fixed
        self.enum_container = ui_qt.QtWidgets.QWidget()
        self.enum_vbox = ui_qt.QtWidgets.QVBoxLayout(self.enum_container)
        self.enum_vbox.setContentsMargins(0, 0, 0, 0)
        self.enum_vbox.setSpacing(8)
        self.enum_vbox.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)  # Keep groups at top
        self.enum_scroll.setWidget(self.enum_container)
        self.content_layout.addWidget(self.enum_scroll)

        # Offset Section ---------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Offset Conditions")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.export_data_checkbox = self.add_module_attr_widget_checkbox(
            attr_name="offset_export_data", layout=_layout, nice_name="Export Offset Data"
        )
        self.export_path_field = self.add_module_attr_widget_path(
            attr_name="offset_export_path",
            layout=_layout,
            placeholder=r"{project-dir}\exports\offsets.json",
            nice_name="Export Path",
        )
        self.export_data_checkbox.toggled.connect(self.refresh_export_data_enabled)

        # Expand/Collapse Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.toggle_offsets_btn = ui_qt.QtWidgets.QPushButton()  # Label automatically updated when initializing
        self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
        self.toggle_offsets_btn.setCheckable(True)
        self.toggle_offsets_btn.setChecked(self.module.offset_frame_expanded)
        self.toggle_offsets_btn.clicked.connect(self.refresh_toggle_offsets_collapsed_state)
        _layout.addWidget(self.toggle_offsets_btn)
        # Add Offset Button
        add_offset_btn = ui_qt.QtWidgets.QPushButton("Add Offset")
        add_offset_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_offset_btn.setToolTip(_tooltip)
        add_offset_btn.clicked.connect(self.on_add_offset_dict_clicked)
        _layout.addWidget(add_offset_btn)

        # Scroll Area ---
        self.offset_scroll = ui_qt.QtWidgets.QScrollArea()
        self.offset_scroll.setWidgetResizable(True)
        self.offset_scroll.setMinimumHeight(220)
        self.offset_container = ui_qt.QtWidgets.QWidget()
        self.offset_vbox = ui_qt.QtWidgets.QVBoxLayout(self.offset_container)
        self.offset_vbox.setContentsMargins(0, 0, 0, 0)
        self.offset_vbox.setSpacing(8)
        self.offset_vbox.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.offset_scroll.setWidget(self.offset_container)
        self.content_layout.addWidget(self.offset_scroll)

        # Initial Refresh (Populate)
        self.refresh_current_widgets()

    # ------------------------------------- Interface Assemble -------------------------------------
    def add_enum_widget(self, enum_dict):
        """
        Create and add a new enum dictionary widget to the UI.

        Builds a framed widget with:
          - An attribute name line edit (with delete button).
          - A collapsible container for enum groups.
          - Buttons for expanding/collapsing groups and adding new groups.

        Also initializes any existing groups from the provided dictionary and
        connects signals for editing, adding, and deleting groups.

        Args:
            enum_dict (dict): The dictionary containing enum data with keys:
                - ENUM_ATTR_NAME (str): Attribute name for the enum.
                - ENUM_TARGETS (list[list[str]]): Targets for each group.
                - ENUM_DISPLAY_NAMES (list[str]): Display names for each group.
        """
        attr_name = enum_dict.get(self._KEYS.ENUM_ATTR_NAME, "")
        default_index = enum_dict.get(self._KEYS.ENUM_INDEX, 0)
        target_lists = enum_dict.get(self._KEYS.ENUM_TARGETS, [])
        display_names = enum_dict.get(self._KEYS.ENUM_DISPLAY_NAMES, [])

        dict_frame = ui_qt.QtWidgets.QFrame()
        dict_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        dict_layout = ui_qt.QtWidgets.QVBoxLayout(dict_frame)

        # Header
        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        dict_label = ui_qt.QtWidgets.QLabel("Enum Attribute:")
        dict_edit = ui_qt_utils.ConfirmableQLineEdit(attr_name)
        dict_edit.setPlaceholderText('Name of the new ENUM attribute. e.g. "hat". (Use camelCase)')
        _func = partial(self.on_enum_attr_name_change, target_dict=enum_dict)
        dict_edit.editingFinished.connect(_func)

        # Create Widgets
        index_label = ui_qt.QtWidgets.QLabel(f"Index:")
        index_spinbox = ui_qt.QtWidgets.QSpinBox()
        _tooltip = "Defines the default index of the created ENUM. \n"
        _tooltip += "0 would be the first element.\n1 the second, and so on"
        index_label.setToolTip(_tooltip)
        index_spinbox.setToolTip(_tooltip)
        index_spinbox.setValue(default_index)
        index_spinbox.setMinimumWidth(55)

        delete_btn = ui_qt.QtWidgets.QPushButton()
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        header_layout.addWidget(dict_label)
        header_layout.addWidget(dict_edit)
        header_layout.addWidget(index_label)
        header_layout.addWidget(index_spinbox)
        header_layout.addWidget(delete_btn)
        dict_layout.addLayout(header_layout)

        # Groups area
        groups_layout = ui_qt.QtWidgets.QVBoxLayout()
        groups_container = ui_qt.QtWidgets.QWidget()
        groups_container.setLayout(groups_layout)
        groups_container.hide()  # start collapsed
        dict_layout.addWidget(groups_container)

        # Add Group + Collapse/Expand button
        btn_layout = ui_qt.QtWidgets.QHBoxLayout()
        toggle_btn = ui_qt.QtWidgets.QPushButton(" Expand Groups")
        toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_down))
        add_group_btn = ui_qt.QtWidgets.QPushButton("Add Group")
        add_group_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        btn_layout.addWidget(toggle_btn)
        btn_layout.addWidget(add_group_btn)
        dict_layout.addLayout(btn_layout)

        # Place dict above stretch
        self.enum_vbox.addWidget(dict_frame)

        def toggle_groups(*args, force_state=None):
            """
            Toggle or force the visibility of the enum groups container.

            Updates the container’s visibility, the toggle button text, and its icon
            based on the desired state.

            Args:
                *args: Unused positional arguments (required for signal connections).
                force_state (bool, optional): If True, forces the container to be visible.
                    If False, forces it to be hidden. If None, the state is toggled
                    relative to the current visibility. Defaults to None.
            """
            # Determine the desired visibility state
            if force_state is not None:
                should_be_visible = force_state
            else:
                should_be_visible = not groups_container.isVisible()

            # Apply changes only if the state needs to be updated
            if groups_container.isVisible() != should_be_visible:
                if should_be_visible:
                    groups_container.show()
                    toggle_btn.setText(" Collapse Groups")
                    toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_up))
                else:
                    groups_container.hide()
                    toggle_btn.setText(" Expand Groups")
                    toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_down))

        toggle_btn.clicked.connect(toggle_groups)

        # Initial groups
        if target_lists and display_names:
            for display_name, targets in zip(display_names, target_lists):
                self.add_enum_group(
                    parent_layout=groups_layout,
                    display_name=display_name,
                    targets=targets,
                    enum_dict=enum_dict,
                )

        # Connections
        _func = partial(self.commit_enum_data_to_module)
        dict_edit.editingFinished.connect(_func)
        _func = partial(self.on_delete_enum_widget_clicked, to_delete=dict_frame)
        delete_btn.clicked.connect(_func)

        _add_num_func = partial(self.on_add_enum_group_clicked, groups_layout=groups_layout, enum_dict=enum_dict)
        add_group_btn.clicked.connect(_add_num_func)
        _force_expand_func = partial(toggle_groups, force_state=True)
        add_group_btn.clicked.connect(_force_expand_func)
        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=groups_layout)
        add_group_btn.clicked.connect(_func)

        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=groups_layout)
        index_spinbox.valueChanged.connect(_func)

    def add_enum_group(self, parent_layout, display_name, targets, enum_dict):
        """
        Create and add a new enum group widget to the given parent layout.

        Builds a framed widget with:
          - A display name field (with "None" checkbox and delete button).
          - A targets field with a "Get" button for populating from selection.

        Handles the "None" state by disabling/hiding fields and ensures that
        changes update the provided dictionary.

        Args:
            parent_layout (QLayout): The layout to insert the group widget into.
            display_name (str | None): The display name of the group, or None if disabled.
            targets (list[str] | None): The list of target strings, or None if disabled.
            enum_dict (dict): The dictionary associated with the enum data being updated.
        """
        # Determine is None
        none_checked = False
        if display_name is None or display_name is None:
            none_checked = True

        group_frame = ui_qt.QtWidgets.QFrame()
        group_frame.setFrameShape(ui_qt.QtWidgets.QFrame.StyledPanel)
        group_layout = ui_qt.QtWidgets.QVBoxLayout(group_frame)

        # Display name row
        _tooltip = "Display name used for the enum item. This is what appears in the enum drop-down combobox.\n"
        _tooltip += 'Feel free to use title case (nice names) for these. e.g. "Object 00".'
        display_layout = ui_qt.QtWidgets.QHBoxLayout()
        display_label = ui_qt.QtWidgets.QLabel("Display Name:")
        display_edit = ui_qt_utils.ConfirmableQLineEdit()
        display_label.setToolTip(_tooltip)
        display_edit.setToolTip(_tooltip)
        display_edit.setPlaceholderText('Drop-down enum name. e.g. "Object 00"')
        if display_name and isinstance(display_name, str):
            display_edit.setText(display_name)
        # None Checkbox
        _tooltip = 'If checked, this will be considered a "None" group, which means it will not drive anything.\n'
        _tooltip += "Useful when an item should not change anything in the scene, such as when nothing is selected.\n"
        _tooltip += 'e.g. groups could be "None", "Hat 1", "Hat 2". None would not change anything in the scene.'
        none_checkbox = ui_qt.QtWidgets.QCheckBox("None")
        none_checkbox.setToolTip(_tooltip)
        # Delete Button
        delete_btn = ui_qt.QtWidgets.QPushButton()
        delete_btn.setToolTip("Deletes this group.")
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        display_layout.addWidget(display_label)
        display_layout.addWidget(display_edit)
        display_layout.addWidget(none_checkbox)
        display_layout.addWidget(delete_btn)
        group_layout.addLayout(display_layout)

        # Targets row
        _tooltip = 'Comma separated list of objects to be driven by the enum using the "Driven Attr" attribute.\n'
        _tooltip += 'For example "my_object_01, my_object_02".'
        targets_layout = ui_qt.QtWidgets.QHBoxLayout()
        targets_label = ui_qt.QtWidgets.QLabel("Targets:")
        targets_edit = ui_qt_utils.ConfirmableQLineEdit(self._list_to_string(targets))
        targets_label.setToolTip(_tooltip)
        targets_edit.setToolTip(_tooltip)
        targets_edit.setPlaceholderText('Command separated list of driven objects. e.g. "my_object_01, my_object_02"')
        # Get Object List Button (Driven Targets)
        get_objects_btn = ui_qt.QtWidgets.QPushButton("Get")
        get_objects_btn.setToolTip("Populates the target list with selected objects.")
        targets_layout.addWidget(targets_label)
        targets_layout.addWidget(targets_edit)
        targets_layout.addWidget(get_objects_btn)
        group_layout.addLayout(targets_layout)

        parent_layout.addWidget(group_frame)

        # Behavior for "None"
        def on_none_changed(state):
            """
            Handles the state change of a 'None' checkbox.

            Args:
                state (ui_qt.QtLib.CheckState): The new state of the checkbox.
                    Expected values are `ui_qt.QtLib.CheckState.Checked` or
                    `ui_qt.QtLib.CheckState.Unchecked`.
            """
            if state == ui_qt.QtLib.CheckState.Checked:
                display_edit.setText("None")
                display_edit.setDisabled(True)
                targets_edit.hide()
                get_objects_btn.hide()
                targets_label.hide()
            else:
                display_edit.setText("")
                display_edit.setDisabled(False)
                targets_edit.show()
                get_objects_btn.show()
                targets_label.show()

        # Find Index SpinBox
        container_widget = parent_layout.parentWidget()
        top_level_widget = container_widget.parentWidget()
        index_spinbox = top_level_widget.findChild(ui_qt.QtWidgets.QSpinBox)

        # Connections
        # Initialize if already "None"
        none_checkbox.stateChanged.connect(on_none_changed)
        if none_checked:
            none_checkbox.setChecked(True)
            on_none_changed(ui_qt.QtLib.CheckState.Checked)

        _func = partial(self.on_delete_enum_widget_clicked, to_delete=group_frame)
        delete_btn.clicked.connect(_func)
        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=parent_layout)
        delete_btn.clicked.connect(_func)

        # This function will now update the dict AND commit to the module
        _func_data_change = partial(self.on_enum_group_data_change, target_dict=enum_dict, groups_layout=parent_layout)

        display_edit.editingFinished.connect(_func_data_change)
        targets_edit.editingFinished.connect(_func_data_change)

        delete_btn.clicked.connect(_func_data_change)  # This is fine, deletion needs to trigger save
        none_checkbox.stateChanged.connect(_func_data_change)  # This is fine, state change needs to trigger save

        # Get Objects Button
        _get_func = partial(
            ui_qt_utils.populate_line_edit_with_selection,
            target_text_field=targets_edit,
            require_exact_count=False,
            selection_limit=None,
        )
        get_objects_btn.clicked.connect(_get_func)
        # ADDED: Ensure "Get" button also triggers a data save
        get_objects_btn.clicked.connect(_func_data_change)

    def add_offset_widget(self, offset_dict):
        """
        Create and add a new offset dictionary widget to the UI.

        Builds a framed widget with:
          - A mesh field with a "Get" button.
          - An offset transform field with "Get Position" and "Get Transform" buttons.
          - A condition field with a "Get Visibility" button.
          - A delete button.

        Tooltips are provided for guidance on usage. Signals are connected to
        commit changes to the module and handle "Get" operations.

        Args:
            offset_dict (dict): The dictionary containing offset data with keys:
                - OFFSET_MESH (str): Name of the target mesh.
                - OFFSET_TRANSFORM (tuple[float, ...]): Offset values as a tuple.
                - OFFSET_CONDITION (str): Condition string for applying the offset.
        """
        mesh_name = offset_dict.get(self._KEYS.OFFSET_MESH)
        offset_transform = offset_dict.get(self._KEYS.OFFSET_TRANSFORM)
        condition = offset_dict.get(self._KEYS.OFFSET_CONDITION)

        dict_frame = ui_qt.QtWidgets.QFrame()
        dict_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        dict_layout = ui_qt.QtWidgets.QVBoxLayout(dict_frame)

        # Offset name row
        mesh_layout = ui_qt.QtWidgets.QHBoxLayout()
        _tooltip = "Name of the mesh to receive an offset. This can be the short or long name to the mesh transform.\n"
        _tooltip += 'e.g. "pSphere" or "|myGroup|pSphere"'
        mesh_label = ui_qt.QtWidgets.QLabel("Mesh:")
        mesh_edit = ui_qt_utils.ConfirmableQLineEdit(mesh_name)
        mesh_edit.setPlaceholderText('Name of the mesh that will receive an offset. e.g. "my_object"')
        mesh_label.setToolTip(_tooltip)
        mesh_edit.setToolTip(_tooltip)
        _tooltip = "Gets the selection as a target mesh and populates the text-field accordingly."
        get_mesh_btn = ui_qt.QtWidgets.QPushButton("Get")
        get_mesh_btn.setToolTip(_tooltip)
        delete_btn = ui_qt.QtWidgets.QPushButton()
        _tooltip = "Deletes this offset."
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_btn.setToolTip(_tooltip)
        mesh_layout.addWidget(mesh_label)
        mesh_layout.addWidget(mesh_edit)
        mesh_layout.addWidget(get_mesh_btn)
        mesh_layout.addWidget(delete_btn)
        dict_layout.addLayout(mesh_layout)

        # Offset Transform row
        _tooltip = "This is the offset applied through conditions to the drivers constraint of the offset.\n"
        _tooltip += 'Only numbers on a properly formated tuple wil be used. e.g. "(1, 2, 3)"\n'
        _tooltip += 'Tuples of 3, 6 or 9 numbers can be used. Each 3 numbers represent position, rotation and scale."'
        offset_transform_layout = ui_qt.QtWidgets.QHBoxLayout()
        offset_transform_label = ui_qt.QtWidgets.QLabel("Offset:")
        offset_transform_edit = ui_qt_utils.ConfirmableQLineEdit(str(tuple(offset_transform)))
        offset_transform_label.setToolTip(_tooltip)
        offset_transform_edit.setToolTip(_tooltip)
        offset_transform_edit.setPlaceholderText('Tuple used as offset. e.g. of +5 Z offset: "(0, 0, 5)"')
        get_pos_btn = ui_qt.QtWidgets.QPushButton("Get Position")
        get_pos_btn.setToolTip("Gets the position of the selected elements (local) as offset.")
        get_trans_btn = ui_qt.QtWidgets.QPushButton("Get Transform")
        get_trans_btn.setToolTip("Gets the transform (TRS) of the selected elements (local) as offset.")
        offset_transform_layout.addWidget(offset_transform_label)
        offset_transform_layout.addWidget(offset_transform_edit)
        offset_transform_layout.addWidget(get_pos_btn)
        offset_transform_layout.addWidget(get_trans_btn)
        dict_layout.addLayout(offset_transform_layout)

        # Condition row
        _tooltip = "Condition to apply the offset. Usually the visibility of another mesh.\n"
        _tooltip += "For example, when a bigger base mesh is visible, the offset should be applied.\n"
        _tooltip += "But when such mesh is not visible, the offset should be ignored."
        cond_layout = ui_qt.QtWidgets.QHBoxLayout()
        cond_label = ui_qt.QtWidgets.QLabel("Condition:")
        cond_edit = ui_qt_utils.ConfirmableQLineEdit(condition)
        cond_label.setToolTip(_tooltip)
        cond_edit.setToolTip(_tooltip)
        cond_edit.setPlaceholderText('Attribute path to the "True" condition for offset to happen. e.g. "obj.v"')
        get_vis_btn = ui_qt.QtWidgets.QPushButton("Get Visibility")
        get_vis_btn.setToolTip("Gets the visibility attribute of the selected element as condition.")
        cond_layout.addWidget(cond_label)
        cond_layout.addWidget(cond_edit)
        cond_layout.addWidget(get_vis_btn)
        dict_layout.addLayout(cond_layout)

        # Place dict above stretch
        self.offset_vbox.addWidget(dict_frame)

        # Connections
        _func = partial(self.commit_offset_data_to_module)
        mesh_edit.editingFinished.connect(_func)
        cond_edit.editingFinished.connect(_func)
        offset_transform_edit.editingFinished.connect(_func)

        _func_delete = partial(self.on_delete_offset_widget_clicked, to_delete=dict_frame)
        delete_btn.clicked.connect(_func_delete)

        _func_get_mesh = partial(ui_qt_utils.populate_line_edit_with_selection, mesh_edit)
        get_mesh_btn.clicked.connect(_func_get_mesh)
        _func_get_pos = partial(self.on_get_offset_clicked, line_edit=offset_transform_edit, mode="position")
        get_pos_btn.clicked.connect(_func_get_pos)
        _func_get_trans = partial(self.on_get_offset_clicked, line_edit=offset_transform_edit, mode="transform")
        get_trans_btn.clicked.connect(_func_get_trans)
        _func_get_vis = partial(self.on_get_condition_visibility_clicked, line_edit=cond_edit)
        get_vis_btn.clicked.connect(_func_get_vis)

        # ADDED: Ensure all "Get" buttons also trigger a data save
        get_mesh_btn.clicked.connect(_func)
        get_pos_btn.clicked.connect(_func)
        get_trans_btn.clicked.connect(_func)
        get_vis_btn.clicked.connect(_func)

    # -------------------------------------- Refresh Functions -------------------------------------

    def refresh_toggle_enums_collapsed_state(self, force_state=None):
        """
        Toggles the visibility of the enums scroll area.

        Args:
            force_state (bool, optional): If True, forces the area to expand.
                If False, forces it to collapse. If None, the state is toggled
                based on the button's checked state. Defaults to None.
        """
        if force_state is not None:
            if force_state:
                self.toggle_enums_btn.setChecked(True)
            else:
                self.toggle_enums_btn.setChecked(False)

        if self.toggle_enums_btn.isChecked():
            self.toggle_enums_btn.setText("Collapse Enums")
            self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_up_arrow))
            self.enum_scroll.show()
            self.module.enum_frame_expanded = True
        else:
            self.toggle_enums_btn.setText("Expand Enums")
            self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
            self.enum_scroll.hide()
            self.module.enum_frame_expanded = False

    def refresh_toggle_offsets_collapsed_state(self, force_state=None):
        """
        Toggles the visibility of the offsets scroll area.

        Args:
            force_state (bool, optional): If True, forces the area to expand.
                If False, forces it to collapse. If None, the state is toggled
                based on the button's checked state. Defaults to None.
        """
        if force_state is not None:
            if force_state:
                self.toggle_offsets_btn.setChecked(True)
            else:
                self.toggle_offsets_btn.setChecked(False)

        if self.toggle_offsets_btn.isChecked():
            self.toggle_offsets_btn.setText("Collapse Offsets")
            self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_up_arrow))
            self.offset_scroll.show()
            self.module.offset_frame_expanded = True
        else:
            self.toggle_offsets_btn.setText("Expand Offsets")
            self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
            self.offset_scroll.hide()
            self.module.offset_frame_expanded = False

    def refresh_export_data_enabled(self):
        """
        Enable or disable the export path field based on the export checkbox state.

        When the checkbox is checked, the field is enabled for input.
        When unchecked, the field is disabled.
        """
        self.export_path_field.setEnabled(self.export_data_checkbox.isChecked())

    def refresh_index_spinbox_limits(self, *args, index_spinbox, groups_layout):
        """
        Handle changes to an enum group layout.

        Extracts updated group data (targets and display names) from the layout
        and updates the corresponding dictionary.

        Args:
            index_spinbox (QSpinBox): The spinbox to change the maximum value.
            groups_layout (QLayout): The layout containing group widgets, used to determine maximum length.
        """
        groups_len = groups_layout.count()
        # Compensate for zero based index
        if groups_len > 0:
            groups_len -= 1
        index_spinbox.setMaximum(groups_len)
        self.commit_enum_data_to_module()

    def refresh_current_widgets(self):
        """
        Rebuild the UI widgets to match the module’s current state.

        - Creates enum and offset widgets from the dictionaries stored in the module.
        - Restores the expanded/collapsed state of the enums and offsets sections.
        - Updates the enabled state of the export path field based on the export checkbox.

        This function is typically called during initialization or when the module
        data needs to be fully re-synced with the UI.
        """
        # Load initial data
        for enum_dict in self.module.enum_dicts:
            self.add_enum_widget(enum_dict=enum_dict)
        for offset_dict in self.module.offset_dicts:
            self.add_offset_widget(offset_dict=offset_dict)
        # Expanded or Collapsed
        self.refresh_toggle_offsets_collapsed_state()
        self.refresh_toggle_enums_collapsed_state()
        # Exported State
        self.refresh_export_data_enabled()

    # ------------------------------------ Data Update Functions -----------------------------------
    def get_enum_dict_data_from_layout(self, attr_parent_layout):
        """
        Extract enum dictionary data from a parent layout.

        Iterates over all child widgets in the given layout, finding frames
        that represent enum attribute groups. For each group, retrieves
        the attribute name, targets, and display names, then assembles them
        into a dictionary.

        Args:
            attr_parent_layout (QLayout): The parent layout containing enum group widgets.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - ENUM_ATTR_NAME (str): Attribute name for the enum.
                - ENUM_TARGETS (list[list[str]] | list[None]): Targets for each enum group.
                - ENUM_DISPLAY_NAMES (list[str] | list[None]): Display names for each enum group.
        """
        # Get All Data and Assemble Dictionaries
        enum_dicts = []
        for idx in range(attr_parent_layout.count()):
            item = attr_parent_layout.itemAt(idx)

            widget = item.widget()

            # Find specific child widgets inside each frame, these are the text-field for the attributes.
            dict_widgets = widget.children()
            attr_name = None
            index = None
            enum_targets = None
            enum_display_names = None
            for dict_widget in dict_widgets:
                if isinstance(dict_widget, ui_qt.QtWidgets.QLineEdit):
                    attr_name = dict_widget.text()
                if isinstance(dict_widget, ui_qt.QtWidgets.QSpinBox):
                    index = dict_widget.value()
                if isinstance(dict_widget, ui_qt.QtWidgets.QWidget):
                    for grp_widget in dict_widget.children():
                        if isinstance(grp_widget, ui_qt.QtWidgets.QFrame):
                            grp_layout = grp_widget.parentWidget().layout()
                            enum_targets, enum_display_names = self.get_enum_group_data_from_layout(grp_layout)
            # Assemble New Dictionary
            new_dict = {
                self._KEYS.ENUM_ATTR_NAME: attr_name,
                self._KEYS.ENUM_TARGETS: enum_targets,
                self._KEYS.ENUM_DISPLAY_NAMES: enum_display_names,
                self._KEYS.ENUM_INDEX: index,
            }
            enum_dicts.append(new_dict)
        return enum_dicts

    def get_enum_group_data_from_layout(self, groups_layout):
        """
        Extract enum group data from a groups layout.

        Iterates over the child widgets in the given layout to retrieve the
        display names, target strings, and 'is none' state for each group.
        Converts text fields into structured lists and handles the case where
        a group is marked as 'None'.

        Args:
            groups_layout (QLayout): The layout containing enum group frames.

        Returns:
            tuple[list[list[str] | None], list[str | None]]:
                - A list of targets (list of strings or None) for each group.
                - A list of display names (strings or None) for each group.
        """
        enum_targets = []
        enum_display_names = []
        for idx in range(groups_layout.count()):
            item = groups_layout.itemAt(idx)
            widget = item.widget()
            frame_widgets = widget.children()
            le_list = []
            checkbox_list = []
            for frame_widget in frame_widgets:
                if isinstance(frame_widget, ui_qt.QtWidgets.QLineEdit):
                    le_list.append(frame_widget)
                if isinstance(frame_widget, ui_qt.QtWidgets.QCheckBox):
                    checkbox_list.append(frame_widget)
            if not le_list or not checkbox_list:
                continue
            # Find specific child widgets inside each list
            display_name_le, targets_le = le_list
            is_none_checkbox = checkbox_list[0]
            # Get Group Data
            is_none_group = is_none_checkbox.isChecked()
            targets_string = targets_le.text()
            targets = self._string_to_list(targets_string)
            display_name = display_name_le.text()
            if is_none_group:
                display_name = None
                targets = None
            enum_targets.append(targets)
            enum_display_names.append(display_name)
        return enum_targets, enum_display_names

    def get_offset_dict_data_from_layout(self, attr_parent_layout):
        """
        Extract offset dictionary data from a parent layout.

        Iterates over all child widgets in the given layout, retrieving
        mesh names, transforms, and conditions from line edits. Each set of
        data is assembled into a dictionary.

        Args:
            attr_parent_layout (QLayout): The parent layout containing offset data widgets.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - OFFSET_MESH (str): Name of the mesh.
                - OFFSET_TRANSFORM (tuple[float, float, float]): Transform values as a tuple.
                - OFFSET_CONDITION (str): Offset condition string.
        """
        # Get All Data and Assemble Dictionaries
        offset_dicts = []
        for idx in range(attr_parent_layout.count()):
            item = attr_parent_layout.itemAt(idx)

            widget = item.widget()

            # Find specific child widgets inside each frame, these are the text-field for the attributes.
            dict_widgets = widget.children()
            offset_mesh = None
            offset_transform = None
            offset_condition = None
            line_edits = []
            for dict_widget in dict_widgets:
                if isinstance(dict_widget, ui_qt.QtWidgets.QLineEdit):
                    line_edits.append(dict_widget)

            if not line_edits:
                continue
            offset_mesh = line_edits[0].text()
            offset_transform = line_edits[1].text()
            offset_condition = line_edits[2].text()

            # Assemble New Dictionary
            new_dict = {
                self._KEYS.OFFSET_MESH: offset_mesh,
                self._KEYS.OFFSET_TRANSFORM: self._string_to_tuple(offset_transform),
                self._KEYS.OFFSET_CONDITION: offset_condition,
            }
            offset_dicts.append(new_dict)
        return offset_dicts

    def commit_enum_data_to_module(self, *args):
        """
        Commit the latest enum dictionary data from the UI to the module.

        Extracts updated enum dictionaries from the enum parent layout and
        assigns them to the module instance.
        """
        _enum_dicts_updated = self.get_enum_dict_data_from_layout(attr_parent_layout=self.enum_vbox)
        self.module.enum_dicts = _enum_dicts_updated

    def commit_offset_data_to_module(self, *args):
        """
        Commit the latest offset dictionary data from the UI to the module.

        Extracts updated offset dictionaries from the offset parent layout and
        assigns them to the module instance.
        """
        _offset_dicts_updated = self.get_offset_dict_data_from_layout(attr_parent_layout=self.offset_vbox)
        self.module.offset_dicts = _offset_dicts_updated

    def on_add_enum_dict_clicked(self):
        """
        Handle the event of adding a new enum dictionary.

        Creates a new empty enum dictionary, adds a corresponding widget to
        the UI, refreshes the collapsed state of the enums section, and commits
        the updated enum data to the module.
        """
        _enum_dict = {
            self._KEYS.ENUM_ATTR_NAME: "",
            self._KEYS.ENUM_TARGETS: [],
            self._KEYS.ENUM_DISPLAY_NAMES: [],
        }
        self.add_enum_widget(enum_dict=_enum_dict)
        self.refresh_toggle_enums_collapsed_state(force_state=True)
        self.commit_enum_data_to_module()

    def on_add_offset_dict_clicked(self):
        """
        Handle the event of adding a new offset dictionary.

        Creates a new empty offset dictionary, adds a corresponding widget to
        the UI, refreshes the collapsed state of the offsets section, and commits
        the updated offset data to the module.
        """
        _offset_dict = {
            self._KEYS.OFFSET_MESH: "",
            self._KEYS.OFFSET_TRANSFORM: (0, 0, 0),
            self._KEYS.OFFSET_CONDITION: "",
        }
        self.add_offset_widget(offset_dict=_offset_dict)
        self.refresh_toggle_offsets_collapsed_state(force_state=True)
        self.commit_offset_data_to_module()

    def on_enum_attr_name_change(self, line_data, target_dict):
        """
        Handle changes to the enum attribute name field.

        Updates the target dictionary with the new attribute name.

        Args:
            line_data (QLineEdit): The updated attribute name from the line edit.
            target_dict (dict): The dictionary to update with the new name.
        """
        if target_dict:
            target_dict[self._KEYS.ENUM_ATTR_NAME] = line_data

    def on_enum_group_data_change(self, *args, target_dict, groups_layout):
        """
        Handle changes to an enum group layout.

        Extracts updated group data (targets and display names) from the layout,
        updates the corresponding dictionary, and commits all enum data to the
        module to ensure the changes are saved.

        Args:
            target_dict (dict): The dictionary to update with new group data.
            groups_layout (QLayout): The layout containing group widgets.
        """
        enum_targets, enum_display_names = self.get_enum_group_data_from_layout(groups_layout=groups_layout)
        target_dict[self._KEYS.ENUM_TARGETS] = enum_targets
        target_dict[self._KEYS.ENUM_DISPLAY_NAMES] = enum_display_names
        self.commit_enum_data_to_module()

    def on_add_enum_group_clicked(self, groups_layout, enum_dict):
        """
        Handle the event of adding a new enum group.

        Creates and inserts a new enum group widget into the given layout,
        then updates the target dictionary with the new group data.

        Args:
            groups_layout (QLayout): The layout to add the group to.
            enum_dict (dict): The dictionary associated with the enum data.
        """
        self.add_enum_group(
            parent_layout=groups_layout,
            display_name=None,
            targets=None,
            enum_dict=enum_dict,
        )
        self.on_enum_group_data_change(target_dict=enum_dict, groups_layout=groups_layout)

    def on_delete_enum_widget_clicked(self, to_delete):
        """
        Handle the deletion of an enum widget.

        Removes the widget from the UI and commits the updated enum data
        to the module.

        Args:
            to_delete (QWidget): The widget to remove.
        """
        self._remove_widget(to_delete)
        self.commit_enum_data_to_module()

    def on_delete_offset_widget_clicked(self, to_delete):
        """
        Handle the deletion of an offset widget.

        Removes the widget from the UI and commits the updated offset data
        to the module.

        Args:
            to_delete (QWidget): The widget to remove.
        """
        self._remove_widget(to_delete)
        self.commit_offset_data_to_module()

    @staticmethod
    def on_get_offset_clicked(line_edit, mode="position"):
        """
        Retrieves the transform values (position, rotation, and scale) of the
        selected object and displays them.

        Args:
            line_edit (QLineEdit): The line edit UI element to display the values in.
            mode (str, optional): A string to decide what attributes to retrieve.
                     Use "position" for translation only or "transform" for all nine transform attributes.
        """
        import maya.cmds as cmds

        selection = cmds.ls(selection=True) or []

        if not selection:
            logging.warning("Nothing selected.")
            return

        if len(selection) > 1:
            logging.warning("Unable to get offset, please select only one object.")
            return

        # Define attribute lists based on the 'mode' argument
        if mode == "position":
            attrs = ["tx", "ty", "tz"]
        elif mode == "transform":
            attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
        else:
            logging.error("Invalid mode. Use 'position' or 'transform'.")
            return

        # Get the values and set the text
        transform_values = [cmds.getAttr(f"{selection[0]}.{attr}") for attr in attrs]
        line_edit.setText(f"{tuple(transform_values)}")

    @staticmethod
    def on_get_condition_visibility_clicked(line_edit):
        """
        Retrieves the visibility attribute path of the selected object and populates a line edit with it.

        Args:
            line_edit (QLineEdit): The line edit UI element to display the values in.
        """
        import maya.cmds as cmds

        selection = cmds.ls(selection=True) or []

        if not selection:
            logging.warning("Nothing selected.")
            return

        if len(selection) > 1:
            logging.warning("Unable to get offset, please select only one object.")
            return

        line_edit.setText(f"{selection[0]}.visibility")

    # --------------------------------------- Utils Functions --------------------------------------
    @staticmethod
    def _list_to_string(lst):
        """
        Convert a list of items to a comma-separated string.

        Args:
            lst (list): List of items to convert.

        Returns:
            str: Comma-separated string of items.
        """
        if not lst:
            return ""
        return ", ".join(str(x) for x in lst)

    @staticmethod
    def _string_to_list(input_string):
        """
        Convert a string into a list of valid Maya names, ignoring spaces
        and invalid characters.

        Valid Maya name rules applied:
            - Only letters, numbers, and underscores.
            - Names cannot start with a number.

        Args:
            input_string (str): Input string with items separated by commas.

        Returns:
            list: List of cleaned, valid Maya-compatible names.
        """
        import re

        if not input_string:
            return []

        items = input_string.split(",")
        valid_names = []
        for item in items:
            item = item.strip()  # Remove leading/trailing spaces
            # Remove invalid characters
            item = re.sub(r"[^a-zA-Z0-9_]", "", item)
            # Ensure name does not start with a number
            if item and not item[0].isdigit():
                valid_names.append(item)

        return valid_names

    @staticmethod
    def _remove_widget(widget):
        """
        Remove a Qt widget from its parent and schedule it for deletion.

        Args:
            widget (QtWidgets.QWidget): The widget to remove and delete.
        """
        widget.setParent(None)
        widget.deleteLater()

    @staticmethod
    def _string_to_tuple(input_string, precision=4):
        """
        Converts a string of comma-separated numbers into a tuple of floats with a specified precision.

        This function gracefully handles broken or incomplete strings and rounds the output
        floats to the desired number of decimal places.

        Args:
            input_string (str): The string to be converted, e.g., "(0, 1.2, 1.5)"
            precision (int): The number of decimal places to round the floats to.

        Returns:
            tuple: A tuple containing the successfully parsed numbers. Empty tuple if failed to parse.
        """
        import re

        try:
            cleaned_string = input_string.strip().strip("() ")
            parts = re.split(r",\s*", cleaned_string)
            numbers = []

            for part in parts:
                if part:
                    try:
                        number = float(part)
                        rounded_number = round(number, precision)  # Round the float to the specified precision
                        numbers.append(rounded_number)
                    except ValueError:
                        continue
            return tuple(numbers)
        except Exception as e:
            logger.debug("Failed to convert string to tuple. Issue: {e}")
            return tuple()


class AttrWidgetModulePickerData(AttrWidget):
    """
    An attribute widget for managing a list of picker file paths.

    This widget provides a user interface to dynamically add, remove, and
    define string paths to picker data files (e.g., JSON). The data is stored
    in the associated module's `pickers` attribute as a list of strings.
    """

    def __init__(self, parent=None, *args, **kwargs):
        """
        Initializes the attribute widget for the picker data module.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget. Defaults to None.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Picker Section ---------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Picker Data")

        # "Add Picker" Button
        add_picker_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(add_picker_button_layout)
        add_picker_button = ui_qt.QtWidgets.QPushButton("Add Picker")
        add_picker_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_picker_button.setToolTip("Adds a new picker path to the list.")
        add_picker_button.clicked.connect(self.on_add_picker_clicked)
        add_picker_button_layout.addWidget(add_picker_button)

        # Scroll Area for Picker Widgets
        self.picker_scroll_area = ui_qt.QtWidgets.QScrollArea()
        self.picker_scroll_area.setWidgetResizable(True)
        self.picker_scroll_area.setMinimumHeight(220)
        self.picker_container = ui_qt.QtWidgets.QWidget()
        self.picker_vertical_layout = ui_qt.QtWidgets.QVBoxLayout(self.picker_container)
        self.picker_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.picker_vertical_layout.setSpacing(8)
        self.picker_vertical_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.picker_scroll_area.setWidget(self.picker_container)
        self.content_layout.addWidget(self.picker_scroll_area)

        # Write Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        write_btn = ui_qt.QtWidgets.QPushButton("Write Picker Data to Scene")
        write_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        write_btn.setToolTip("Writes the picker data to the currently opened scene.")
        write_btn.clicked.connect(self.on_write_pickers_clicked)
        _layout.addWidget(write_btn)

        write_btn = ui_qt.QtWidgets.QPushButton("Clear Picker Data from Scene")
        write_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        write_btn.setToolTip("Clears the picker data from the currently opened scene.")
        write_btn.clicked.connect(self.on_clear_pickers_clicked)
        _layout.addWidget(write_btn)
        self.content_layout.addLayout(_layout)

        # Initial Refresh to populate the UI
        self.refresh_current_widgets()

    # -----------------------------------
    # Interface Assembly
    # -----------------------------------

    def add_picker_widget(self, picker_path):
        """
        Creates and adds a new picker widget to the UI layout.

        This builds a framed widget containing a line edit for the file path,
        buttons for path parsing and file browsing, and a delete button.

        Args:
            picker_path (str): The initial path string for the picker file.
                               This can be an empty string for a new picker entry.
        """
        picker_frame = ui_qt.QtWidgets.QFrame()
        picker_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        picker_layout = ui_qt.QtWidgets.QHBoxLayout(picker_frame)

        # Picker Path Widgets
        path_label = ui_qt.QtWidgets.QLabel("Picker Path:")
        path_line_edit = ui_qt_utils.ConfirmableQLineEdit(picker_path)
        path_line_edit.setPlaceholderText('Path to a picker file e.g. "humanoid_body.json"')

        show_parsed_path_button = ui_qt.QtWidgets.QPushButton()
        show_parsed_path_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        show_parsed_path_button.setToolTip("Shows the parsed path with environment variables resolved.")

        open_file_dialog_button = ui_qt.QtWidgets.QPushButton()
        open_file_dialog_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        open_file_dialog_button.setToolTip("Use file dialog to set path.")

        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_button.setToolTip("Deletes this picker path.")

        # Assemble Layout
        picker_layout.addWidget(path_label)
        picker_layout.addWidget(path_line_edit)
        picker_layout.addWidget(show_parsed_path_button)
        picker_layout.addWidget(open_file_dialog_button)
        picker_layout.addWidget(delete_button)

        self.picker_vertical_layout.addWidget(picker_frame)

        # Connections
        path_line_edit.editingFinished.connect(self.commit_picker_data_to_module)

        # Connect path utility buttons (assuming handlers exist on base class)
        show_parsed_path_function = partial(self.open_env_var_feedback_dialog, field=path_line_edit)
        show_parsed_path_button.clicked.connect(show_parsed_path_function)

        # Connect to the new handler that also commits data
        open_dialog_function = partial(
            self._on_open_file_dialog_clicked,
            line_edit_widget=path_line_edit,
            file_filter="JSON Files (*.json);;All Files (*)",
        )
        open_file_dialog_button.clicked.connect(open_dialog_function)

        delete_function = partial(self.on_delete_picker_widget_clicked, to_delete=picker_frame)
        delete_button.clicked.connect(delete_function)

    # -----------------------------------
    # Refresh Functions
    # -----------------------------------

    def refresh_current_widgets(self):
        """
        Rebuilds the UI to match the module's current state.

        This function clears any existing picker widgets and then creates new ones
        based on the `self.module.pickers` list.
        """
        self._clear_layout(self.picker_vertical_layout)

        if not hasattr(self.module, "pickers"):
            self.module.pickers = []

        for picker_path in self.module.pickers:
            self.add_picker_widget(picker_path=picker_path)

    # -----------------------------------
    # Data Update Functions
    # -----------------------------------

    def get_picker_data_from_layout(self):
        """
        Extracts all picker path strings from the UI widgets.

        Iterates through the picker widgets in the layout, reads the text from
        each line edit, and returns them as a list of strings.

        Returns:
            list[str]: A list of picker path strings currently present in the UI.
        """
        picker_paths = []
        for index in range(self.picker_vertical_layout.count()):
            item = self.picker_vertical_layout.itemAt(index)
            widget = item.widget()
            if not widget:
                continue

            line_edit = widget.findChild(ui_qt.QtWidgets.QLineEdit)
            if line_edit:
                picker_paths.append(line_edit.text())
        return picker_paths

    def commit_picker_data_to_module(self):
        """
        Commits the current picker data from the UI back to the module instance.
        """
        self.module.pickers = self.get_picker_data_from_layout()

    # -----------------------------------
    # Event Handlers
    # -----------------------------------

    def _on_open_file_dialog_clicked(self, line_edit_widget, file_filter):
        """
        Handles the file dialog button click for a picker path.

        This opens the file dialog and, if a file is selected (which updates
        the line edit), it immediately commits the new data to the module.

        Args:
            line_edit_widget (ui_qt.QtWidgets.QLineEdit): The line edit widget to populate
                                                          with the selected file path.
            file_filter (str): The file filter string for the dialog.
        """
        self.open_module_attr_file_dialog(field=line_edit_widget, file_filter=file_filter)
        self.commit_picker_data_to_module()

    def on_add_picker_clicked(self):
        """
        Handles the "Add Picker" button click event.

        This adds a new, empty picker widget to the UI and then updates the module data.
        """
        self.add_picker_widget(picker_path="")
        self.commit_picker_data_to_module()

    def on_delete_picker_widget_clicked(self, to_delete):
        """
        Handles the deletion of a specific picker widget.

        Args:
            to_delete (QWidget): The picker widget (frame) to be removed.
        """
        self._remove_widget(to_delete)
        self.commit_picker_data_to_module()

    def on_write_pickers_clicked(self):
        """Adds picker data to the currently opened scene."""
        self.module.add_picker_data()

    @staticmethod
    def on_clear_pickers_clicked():
        """Removes picker data from the currently opened scene."""
        import maya.cmds as cmds

        _picker_data_nodes = cmds.ls("_dwpicker_data") or []
        if _picker_data_nodes:
            try:
                cmds.delete(_picker_data_nodes)
            except Exception as e:
                logger.warning(f"Unable to delete picker data. Issue: {e}")
            logger.info(f"{len(_picker_data_nodes)} picker data nodes were deleted.")
        else:
            logger.info(f"No picker data nodes found in the scene.")

    # -----------------------------------
    # Utility Functions
    # -----------------------------------

    @staticmethod
    def _clear_layout(layout):
        """
        Removes all widgets from a given layout.

        Args:
            layout (QLayout): The layout to be cleared.
        """
        if not layout:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @staticmethod
    def _remove_widget(widget):
        """
        Removes a Qt widget from its parent and schedules it for deletion.

        Args:
            widget (QWidget): The widget to remove and delete.
        """
        if widget:
            widget.setParent(None)
            widget.deleteLater()


class AttrWidgetModulePython(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()

        _layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(_layout)

        _layout_top_prefs = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)

        self.add_widget_code_data_editor(
            add_activation=False, add_order_editor=True, add_code_editor=False, layout=_layout_top_prefs
        )

        # Get Basic Items
        code_data = self.module.get_code_data()

        _value = code_data.get_execution_code()

        # Font Size
        _layout.addLayout(_layout_top_prefs)
        self.font_size_slider = self.add_module_attr_widget_int_slider(
            attr_name="font_size",
            layout=_layout_top_prefs,
            min_int=8,
            max_int=24,
        )
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)

        # Python Edit
        self.python_edit = ui_qt.QtWidgets.QTextEdit()
        _layout.addWidget(self.python_edit)
        self.python_edit.setText(_value)
        self.base_stylesheet = ""  # In case we want to add something later
        self.python_edit.setStyleSheet(self.base_stylesheet)
        self.python_edit_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.python_edit.setFont(self.python_edit_font)
        initial_font_size = self.module.font_size
        self.python_edit.setFontPointSize(initial_font_size)

        import gt.ui.syntax_highlighter as ui_syntax_highlighter

        self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())

        # Run Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        run_code_btn = ui_qt.QtWidgets.QPushButton("Run Code")
        run_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        run_code_btn.setToolTip("Execute the Python code in the text editor.")
        run_code_btn.clicked.connect(self.on_button_run_code_clicked)
        _layout.addWidget(run_code_btn)

        # Insert Selection Button
        insert_selection_btn = ui_qt.QtWidgets.QPushButton("Insert Selection")
        insert_selection_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        insert_selection_btn.setToolTip("Inserts the current selection as a Python list at the cursor.")
        insert_selection_btn.clicked.connect(self.on_insert_selection_clicked)
        _layout.addWidget(insert_selection_btn)

        # Save Button
        save_btn = ui_qt.QtWidgets.QPushButton("Save")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.setToolTip("Save the current script to a file.")
        save_btn.clicked.connect(self.on_save_clicked)
        _layout.addWidget(save_btn)

        # Load Button
        load_btn = ui_qt.QtWidgets.QPushButton("Load")
        load_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        load_btn.setToolTip("Load a script from a file.")
        load_btn.clicked.connect(self.on_load_clicked)
        _layout.addWidget(load_btn)

        self.content_layout.addLayout(_layout)

        # Initial Refresh
        self.set_editor_font_size(initial_font_size)
        self._update_editor_stylesheet(initial_font_size)
        self.python_edit.textChanged.connect(self.on_text_changed)

    def on_button_run_code_clicked(self):
        """
        Executes the Python code from the text editor when the 'Run Code' button is clicked.


        """
        import gt.utils.system as utils_sys

        utils_sys.execute_python_code(code=self.python_edit.toPlainText(), import_cmds=True)

    def set_editor_font_size(self, size):
        """
        Updates the font size of the python text editor when the slider value changes.

        Args:
            size (int): The new font size from the slider.
        """
        self._update_editor_stylesheet(size)

    def _update_editor_stylesheet(self, font_size):
        """
        Constructs and applies the full stylesheet for the Python text editor.

        Args:
            font_size (int): The font size to include in the stylesheet.
        """
        dynamic_stylesheet = self.base_stylesheet + f"; font-size: {font_size}pt;"
        self.python_edit.setStyleSheet(dynamic_stylesheet)

        # 2. Update the tab stop width to equal 4 spaces in the new font size
        font_metrics = ui_qt.QtGui.QFontMetrics(self.python_edit.font())
        space_width = font_metrics.horizontalAdvance(" ")
        try:
            self.python_edit.setTabStopWidth(space_width * 6)  # For some reason 6 aligns better in this font.
        except Exception as e:
            logger.debug(e)
            self.python_edit.setTabStopDistance(space_width * 6)  # For some reason 6 aligns better in this font.


    def on_save_clicked(self):
        """
        Opens a custom file dialog to save the content of the text editor.

        Uses the core_io module to handle the file writing.
        """
        file_path = ui_file_dialog.file_dialog(
            write_mode=True, caption="Save Python Script", file_filter="Python Files (*.py)"
        )

        if not file_path:
            return  # User cancelled the dialog

        content = self.python_edit.toPlainText()
        success = core_io.write_data(path=file_path, data=content)

        if not success:
            logger.error(f"Failed to save script to {file_path}")

    def on_load_clicked(self):
        """
        Opens a custom file dialog to load a .py file into the text editor.

        Uses the core_io module to handle the file reading.
        """
        file_path = ui_file_dialog.file_dialog(
            write_mode=False, caption="Open Python Script", file_filter="Python Files (*.py)"
        )

        if not file_path:
            return  # User cancelled the dialog

        content = core_io.read_data(path=file_path)

        if content is not None:
            self.python_edit.setText(content)
        else:
            logger.error(f"Failed to read script from {file_path}")

        self.on_text_changed()  # Refresh

    def on_insert_selection_clicked(self):
        """
        Gets the current Maya selection and inserts it as a formatted Python list
        at the cursor's current position in the text editor.
        """
        import gt.core.selection as core_sel

        selection = core_sel.ensure_selection_count(
            selection_limit=None,
            require_exact_count=False,
        )
        if selection:
            # The 'repr' function is great here as it ensures strings have quotes
            formatted_selection = repr(selection)

            cursor = self.python_edit.textCursor()
            cursor.insertText(formatted_selection)

    def on_text_changed(self):
        """
        Automatically saves the editor's content to the module's code data.
        """
        current_code = self.python_edit.toPlainText()
        self.module.set_execution_code(current_code)

        # Enforce Set Font Size
        self.set_editor_font_size(self.font_size_slider.value())

        # Keep the same font
        self.python_edit.setFont(self.python_edit_font)


class AttrWidgetModuleNotes(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.add_widget_module_header()

        # Main layout for this specific widget's content
        _layout = ui_qt.QtWidgets.QVBoxLayout()

        # Bottom Layout for Preferences/Data
        _layout_top = ui_qt.QtWidgets.QHBoxLayout()
        self.add_widget_code_data_editor(
            add_activation=False, add_order_editor=True, add_code_editor=False, layout=_layout_top
        )
        self.add_module_attr_widget_checkbox(attr_name="show_warning", layout=_layout_top, nice_name="  Show Warning")
        self.content_layout.addLayout(_layout_top)

        # Font Size Slider
        self.font_size_slider = self.add_module_attr_widget_int_slider(
            attr_name="font_size",
            layout=_layout_top,
            min_int=8,
            max_int=24,
        )
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)

        # Note Edit
        self.notes_edit = ui_qt.QtWidgets.QTextEdit()
        self.notes_edit.setHtml(self.module.get_notes())
        self.notes_edit.setPlaceholderText("Start typing your notes here...")
        _layout.addWidget(self.notes_edit)
        self.content_layout.addLayout(_layout)

        # --- Initial Refresh ---
        self.set_editor_font_size(self.module.font_size)
        self.notes_edit.textChanged.connect(self.on_notes_text_change)

    def on_notes_text_change(self):
        """Function used to update the module with the text found in the notes text field"""
        current_html = self.notes_edit.toHtml()
        self.module.set_notes(current_html)

    def set_editor_font_size(self, size):
        """
        Updates the base font size for the entire document using a QTextCursor,
        preserving all other rich text formatting.

        Args:
            size (int): The new font size from the slider.
        """
        original_cursor = self.notes_edit.textCursor()

        # Create a new cursor to modify the document
        modifier_cursor = self.notes_edit.textCursor()
        modifier_cursor.select(ui_qt.QtGui.QTextCursor.Document)

        # Create a format that ONLY specifies font size
        char_format = ui_qt.QtGui.QTextCharFormat()
        char_format.setFontPointSize(size)

        # Temporarily set the document's cursor to the one with the full selection
        self.notes_edit.setTextCursor(modifier_cursor)
        self.notes_edit.mergeCurrentCharFormat(char_format)

        # Restore the user's original cursor position and selection
        self.notes_edit.setTextCursor(original_cursor)

        # Update tab stop width based on the new font size
        font = self.notes_edit.font()
        font.setPointSize(size)
        font_metrics = ui_qt.QtGui.QFontMetrics(font)
        space_width = font_metrics.horizontalAdvance(" ")
        self.notes_edit.setTabStopWidth(space_width * 4)


# Corrective Base (Used by other AttrWidgets)
class AttrWidgetModuleBaseCorrective(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a corrective module.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.table_driver_lookup_wdg = None
        self.clear_target_dir_chk = None

    def add_widget_driver_lookup_table(self, table_minimum_height=150):
        """
        Adds a table widget to control driver attribute with options to determine parent or delete the proxy
        Args:
            table_minimum_height (int): The minimum height of the created table
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        # Setup Table
        self.table_driver_lookup_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_proxy_parent_table()
        columns = [
            "",  # Icon
            "Driver",
            "Attribute",
            "",  # Set Driven Key
            "",  # Delete
        ]  # Icon, Driver, Attribute, Set Driven Key, Delete
        self.table_driver_lookup_wdg.setColumnCount(len(columns))
        self.table_driver_lookup_wdg.setHorizontalHeaderLabels(columns)
        header_view = ui_qt_utils.QHeaderWithWidgets()
        self.table_driver_lookup_wdg.setHorizontalHeader(header_view)
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, ui_qt.QtLib.QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_driver_lookup_wdg)
        self.table_driver_lookup_wdg.setColumnWidth(1, 110)
        self.table_driver_lookup_wdg.setMinimumHeight(table_minimum_height)

        # Add Attribute Placeholder Delegate
        delegate = ui_qt_utils.TablePlaceholderDelegate(
            "<attribute>",
            target_columns=[2],
            placeholder_color=ui_qt.QtGui.QColor(100, 100, 100),
            placeholder_alignment=ui_qt.QtLib.AlignmentFlag.AlignCenter,
        )
        self.table_driver_lookup_wdg.setItemDelegate(delegate)

        # Connect Cell Changes
        self.table_driver_lookup_wdg.cellChanged.connect(self.on_driver_lookup_table_cell_changed)

        # Add Button
        add_driver_btn = ui_qt.QtWidgets.QPushButton()
        add_driver_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_driver_btn.clicked.connect(self.on_button_add_driver_clicked)
        add_driver_btn.setToolTip("Add New Driver Attribute")
        header_view.add_widget(4, add_driver_btn)
        self.content_layout.addLayout(_layout)

    def add_widgets_multiplier_fields(self):
        """
        Creates widgets necessary to control the TRS multipliers on a corrective module.
        """
        _precision = 2
        _min = -20
        _max = 20
        _tooltip = (
            "TRS Multiplier modifies the stored valued when reading existing driven keys.\n"
            "These multipliers only influence the values read by the module. \n"
            "A value of 1 represents 100% influence, which is the default behavior."
        )
        self.add_widget_separator_line(label_text="Multiplier Preferences", tooltip=_tooltip)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_double_spinbox(
            attr_name="translate_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Translate X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a translate value of 10 when multiplier by 0.5 would become 5.\n"
            "This can help adjust driven keys created in a different rig scale so they work on a new scale.",
            layout=_layout,
        )
        self.add_module_attr_widget_double_spinbox(
            attr_name="rotate_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Rotate X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a rotate value of 90 when multiplier by 2 would become 180.\n"
            "This allows for fine-tuning the amount of rotation read by the module, without writing new keys.",
            layout=_layout,
        )
        self.add_module_attr_widget_double_spinbox(
            attr_name="scale_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Scale X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a scale value of 1 when multiplier by 0.5 would become 0.5.\n"
            "This allows for fine-tuning the amount of scale read by the module, without writing new keys.",
            layout=_layout,
        )

    def on_button_add_driver_clicked(self):
        """
        Adds a new proxy to the current module and refreshes the UI
        """
        self.module.add_new_driver_attr_path()
        self.refresh_driver_lookup_table()

    def clear_driver_lookup_table(self):
        """
        Clears the driver lookup table (No items)
        """
        if self.table_driver_lookup_wdg:
            self.table_driver_lookup_wdg.setRowCount(0)

    def refresh_driver_lookup_table(self):
        """
        Refresh the table with drivers associated with the module.
        """
        self.clear_driver_lookup_table()
        current_modules = self.project.get_modules()
        uuid_to_module = {module.get_uuid(): module for module in current_modules}

        self.table_driver_lookup_wdg.cellChanged.disconnect(
            self.on_driver_lookup_table_cell_changed
        )  # Fix recursion errors

        for row, driver_attr_dict in enumerate(self.module.driver_attr_paths):
            self.table_driver_lookup_wdg.insertRow(row)
            driver, attr = next(iter(driver_attr_dict.items()))

            # Icon -------------------------------------------------------------------------------
            default_icon = ui_res_lib.Icon.util_sel_non_unique
            if driver and driver in uuid_to_module:
                default_icon = uuid_to_module.get(driver).icon
            self.insert_item(
                row=row,
                column=0,
                table=self.table_driver_lookup_wdg,
                icon_path=default_icon,
                editable=False,
                centered=True,
            )

            # Driver -----------------------------------------------------------------------------
            combo_box = self.create_widget_probe_combobox(initial_probe=driver)
            combo_func = partial(self.on_table_driver_lookup_combo_box_changed, row=row, col=1)
            combo_box.currentIndexChanged.connect(combo_func)
            self.table_driver_lookup_wdg.setCellWidget(row, 1, combo_box)

            # Attribute ---------------------------------------------------------------------------
            if driver and driver in uuid_to_module:
                _probe = uuid_to_module.get(driver)
                _updated_attr = attr
                try:
                    _updated_attr = _probe.get_probe_output_attr_path()
                    self.module.update_driver_attr_path(index=row, new_mapping={driver: _updated_attr})
                except Exception as e:
                    logger.warning(f"Unable to refresh probe data from source. Issue: {e}")
                self.insert_item(
                    row=row,
                    column=2,
                    table=self.table_driver_lookup_wdg,
                    text=_updated_attr,
                    data_object=driver_attr_dict,
                    editable=False,
                )

                item = self.table_driver_lookup_wdg.item(row, 2)
                item.setForeground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.purple_medium)))
            else:
                self.insert_item(
                    row=row,
                    column=2,
                    table=self.table_driver_lookup_wdg,
                    text=attr,
                    data_object=driver_attr_dict,
                )

            # Edit Proxy ---------------------------------------------------------------------
            set_driven_key_btn = ui_qt.QtWidgets.QPushButton("Set Driven Key")
            set_driven_key_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_testing_keys))
            set_driven_key_func = partial(self.on_btn_set_driven_key_clicked, index=row)
            set_driven_key_btn.clicked.connect(set_driven_key_func)
            set_driven_key_btn.setToolTip("Set Driven Key Using Driver")
            self.table_driver_lookup_wdg.setCellWidget(row, 3, set_driven_key_btn)

            # Delete Setup --------------------------------------------------------------------
            delete_driver_btn = ui_qt.QtWidgets.QPushButton()
            delete_driver_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_driver_func = partial(self.on_btn_delete_driver_clicked, index=row)
            delete_driver_btn.clicked.connect(delete_driver_func)
            delete_driver_btn.setToolTip("Delete Driver Attribute")
            self.table_driver_lookup_wdg.setCellWidget(row, 4, delete_driver_btn)

        self.table_driver_lookup_wdg.cellChanged.connect(
            self.on_driver_lookup_table_cell_changed
        )  # Fix recursion errors

    def create_widget_probe_combobox(self, initial_probe):
        """
        Creates a populated combobox with all potential probes to be used as drivers.
        An extra initial item called "Manually Set" is also added for user-defined custom attributes.
        Args:
            initial_probe (str, None): UUID of a probe module or None if not defined.
        Returns:
            QComboBox: A pre-populated combobox with potential probes. Initial probe is also pre-selected.
        """
        current_modules = self.project.get_modules()
        uuid_to_module = {module.get_uuid(): module for module in current_modules}

        category_attrs = vars(tools_rig_modules.RigModules.Probes)
        probe_module_classes = {name: value for name, value in category_attrs.items() if inspect.isclass(value)}

        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.addItem("Manually Set", None)

        detected_probes = [obj for obj in current_modules if obj.__class__.__name__ in probe_module_classes]

        # Populate Combobox
        for _probe in detected_probes:
            _probe_name = _probe.get_name()
            combobox.addItem(_probe_name, _probe)

        # Set Initial or Add Unknown Initial Probe (Not present in project)
        if initial_probe is None:
            return combobox
        if initial_probe in uuid_to_module:
            for index in range(combobox.count()):
                _probe = combobox.itemData(index)
                if _probe and initial_probe == _probe.get_uuid():
                    combobox.setCurrentIndex(index)
        elif initial_probe and initial_probe not in uuid_to_module:
            description = f"unknown"
            description += f" (UUID: {str(initial_probe)})"
            combobox.addItem(description, None)
            combobox.setCurrentIndex(combobox.count() - 1)  # Last item, which was just added
        return combobox

    def on_btn_set_driven_key_clicked(self, index):
        """
        Opens the Maya dialog for setting driven keys with pre-populated values.
        Args:
            index (int): Index used to determine the driver attribute.
        """
        item = self.table_driver_lookup_wdg.item(index, 2)  # 2 = Attribute
        if item:
            import maya.cmds as cmds
            import maya.mel as mel

            driver_attr = item.text()
            if not cmds.objExists(driver_attr):
                logger.warning(f"Driver attribute not available. Make sure it exists and the rig built then try again.")
                return

            cor_joints = []
            for proxy in self.module.proxies:
                _joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                if _joint:
                    cor_joints.append(_joint)
            if not cor_joints:
                logger.warning(f"Missing driven joints. Make sure the rig is built then try again.")
                return

            cmds.select(cor_joints, replace=True)
            mel.eval('setDrivenKeyWindow "" {""};')
            driver = driver_attr
            if "." in driver_attr:
                driver = driver_attr.split(".")[0]
            cmds.select(driver, replace=True)
            mel.eval('updateSetDrivenWnd("driver", "", {""});')
            cmds.select(clear=True)
        else:
            logger.warning(f"No driver attribute provided.")

    def on_btn_delete_driver_clicked(self, index):
        """
        Removes driver attribute stored in the specified index
        Args:
            index (int): Index of the driver that should be deleted.
        """
        self.module.remove_driver_attr_path(index)
        self.refresh_driver_lookup_table()

    def on_driver_lookup_table_cell_changed(self, row, column):
        """
        Updates the name of the attributes in case the user writes a new name in the attribute cell.
        Args:
            row (int): Row where the cell changed.
            column (int): Column where the cell changed.
        """
        _source_table = self.table_driver_lookup_wdg
        _attr_cell = _source_table.item(row, 2)  # 2 = Attribute
        attr_dict = _attr_cell.data(self.PROXY_ROLE)
        driver, attribute = next(iter(attr_dict.items()))
        new_name = _attr_cell.text()
        if new_name:
            attr_dict[driver] = new_name
            self.module.update_driver_attr_path(index=row, new_mapping=attr_dict)
            self.refresh_driver_lookup_table()
        else:
            _attr_cell.setText(attribute)

    def on_table_driver_lookup_combo_box_changed(self, index, row, col):
        """
        Handle the change in the probe combo box for the driver table.

        Args:
            index (int): Index of the selected item.
            row (int): Row index.
            col (int): Column index.
        """
        _source_table = self.table_driver_lookup_wdg
        _combo_box = _source_table.cellWidget(row, col)
        _probe_mod = _combo_box.itemData(index)
        _attr_cell = _source_table.item(row, 2)  # 2 = Attribute
        if _probe_mod is None:
            self.module.update_driver_attr_path(index=row, new_mapping={None: ""})
        else:
            uuid = _probe_mod.get_uuid()
            attr_path = _probe_mod.get_probe_output_attr_path()
            self.module.update_driver_attr_path(index=row, new_mapping={uuid: attr_path})
        self.refresh_driver_lookup_table()

    def add_widget_read_write_buttons(self):
        """
        Adds actions buttons
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Write Driven Keys
        write_keys_btn = ui_qt.QtWidgets.QPushButton("Write Driven Keys")
        write_keys_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_keys_btn.clicked.connect(self.write_driven_keys)
        write_keys_btn.setToolTip("Write Influences From Selection")

        # Open Dir
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_driven_keys_dir)
        open_dir_btn.setToolTip("Write Weights From Selection")
        # Layout
        _layout.addWidget(write_keys_btn)
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def open_driven_keys_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.driven_keys_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def write_driven_keys(self):
        """Writes influences to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_driven_keys(clear_target_dir=clear_target_dir)


class AttrWidgetModuleCorrectiveGeneric(AttrWidgetModuleBaseCorrective):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a corrective module.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=False, add_order_editor=True, add_code_editor=False)
        # Driver Lookup Table ------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driver Lookup Table")
        self.add_widget_driver_lookup_table()
        # Driven Proxy Table -------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Proxy Table")
        self.add_widget_proxy_parent_table()
        # TRS Multiplier Preferences -----------------------------------------------------------------------------
        self.add_widgets_multiplier_fields()
        # Driven Keys Interface ----------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Keys Interface")
        self.add_module_attr_widget_path(attr_name="driven_keys_dir", dir_only=True)
        # Purge Directory?
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.scroll_content_layout.addLayout(_layout)
        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir", nice_name="Clear Target Directory When Writing", layout=_layout
        )
        self.add_widget_read_write_buttons()
        # Misc --------------------------------------------------------------------------------------------------
        # Initial Refresh
        self.refresh_driver_lookup_table()


class AttrWidgetModuleCorrectiveFK(AttrWidgetModuleBaseCorrective):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a corrective module.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=False, add_order_editor=True, add_code_editor=False)
        # Driver Lookup Table ------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driver Lookup Table")
        self.add_widget_driver_lookup_table()
        # Driven Proxy Table -------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Proxy Table")
        self.add_widget_proxy_parent_table()
        # Driven Keys Interface ----------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Control Preferences")
        self.add_module_attr_widget_text_field(attr_name="ctrl_shape", nice_name="Control Shape")
        self.add_override_color_ctrls_combobox(
            attr_name="ctrl_color",
            nice_name="Control Color",
            tooltip="Select the color of the controls in the module.",
        )
        # TRS Multiplier Preferences -----------------------------------------------------------------------------
        self.add_widgets_multiplier_fields()
        # Driven Keys Interface ----------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Keys Interface")
        self.add_module_attr_widget_path(attr_name="driven_keys_dir", dir_only=True)

        # Purge Directory?
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.scroll_content_layout.addLayout(_layout)
        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir", nice_name="Clear Target Directory When Writing", layout=_layout
        )
        self.add_module_attr_widget_checkbox(
            attr_name="include_scale",
            nice_name="Include Scale",
            tooltip="When checked, the scale of the control will be unlocked, and a scale constraint between the "
            "control and the corrective joint will be created.",
            layout=_layout,
        )
        self.add_widget_read_write_buttons()
        # Misc --------------------------------------------------------------------------------------------------
        # Initial Refresh
        self.refresh_driver_lookup_table()

    def on_btn_set_driven_key_clicked(self, index):
        """
        Opens the Maya dialog for setting driven keys with pre-populated values.
        Args:
            index (int): Index used to determine the driver attribute.
        """
        item = self.table_driver_lookup_wdg.item(index, 2)  # 2 = Attribute
        if item:
            import maya.cmds as cmds
            import maya.mel as mel

            driver_attr = item.text()
            if not cmds.objExists(driver_attr):
                logger.warning(f"Driver attribute not available. Make sure it exists and the rig built then try again.")
                return
            driven_grp = self.module.get_driven_groups()
            cmds.select(driven_grp, replace=True)
            mel.eval('setDrivenKeyWindow "" {""};')
            driver = driver_attr
            if "." in driver_attr:
                driver = driver_attr.split(".")[0]
            cmds.select(driver, replace=True)
            mel.eval('updateSetDrivenWnd("driver", "", {""});')
            cmds.select(clear=True)
        else:
            logger.warning(f"No driver attribute provided.")


class AttrWidgetModuleRBFLoad(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_parent()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Import RBF Json")
        self.add_widget_auto_serialized_fields(ignore_attrs="file_path")
        self.add_module_attr_widget_path(attr_name="file_path")


class AttrWidgetModuleProbe(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a probe module. This is used as base for other probe modules.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self._output_attr_path_widget = None

    def add_widget_probe_output_text_field(self):
        """Adds a line edit widget showing the output attribute path for the probe"""
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        label = ui_qt.QtWidgets.QLabel(f"Output Attribute Path:")
        self._output_attr_path_widget = ui_qt.QtWidgets.QLineEdit()
        self._output_attr_path_widget.setReadOnly(True)
        text_color = ui_res_lib.Color.RGB.purple_medium
        self._output_attr_path_widget.setStyleSheet(f"color: {text_color};")

        # Get Start Button
        copy_attr_path_clipboard_btn = ui_qt.QtWidgets.QPushButton("COPY TO CLIPBOARD")
        copy_attr_path_clipboard_btn.clicked.connect(self.copy_output_attr_path_to_clipboard)

        # Create Layout
        _layout.addWidget(label)
        _layout.addWidget(self._output_attr_path_widget)
        _layout.addWidget(copy_attr_path_clipboard_btn)
        self.scroll_content_layout.addLayout(_layout)
        self.refresh_output_attr_path_text_field()

    def refresh_output_attr_path_text_field(self):
        """Refreshes the output attribute path text field with updated data."""
        _attr_path = self.module.get_probe_output_attr_path()
        self._output_attr_path_widget.setText(_attr_path)

    def copy_output_attr_path_to_clipboard(self):
        """Copies the text content from the output attribute path to the clipboard"""
        _attr_path = self._output_attr_path_widget.text()
        utils_system.copy_to_clipboard(_attr_path)
        logger.info(f"Probe output attribute path copied to clipboard.")


class AttrWidgetModuleProbeDistance(AttrWidgetModuleProbe):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_separator_line(label_text="Distance Probe Preferences")

        # Start and End Paths
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        start_txt_field = self.add_module_attr_widget_text_field(
            attr_name="start",
            nice_name="Start",
            placeholder="<Path to Start Object>",
            layout=_layout,
        )
        start_txt_field.setToolTip("Path to a Maya object where to start measuring the distance.")
        start_txt_field.textChanged.connect(self.refresh_output_attr_path_text_field)
        # Get Start Button
        get_selection_btn = ui_qt.QtWidgets.QPushButton("GET")
        _func = partial(ui_qt_utils.populate_line_edit_with_selection, start_txt_field)
        get_selection_btn.clicked.connect(_func)
        _layout.addWidget(get_selection_btn)

        end_txt_field = self.add_module_attr_widget_text_field(
            attr_name="end",
            nice_name="End",
            placeholder="<Path to End Object>",
            layout=_layout,
        )
        end_txt_field.setToolTip(
            "Path to a Maya object where to end measuring the distance. "
            "If part of the hierarchy of the starting object, a chain distance can be created."
        )
        end_txt_field.textChanged.connect(self.refresh_output_attr_path_text_field)
        # Get End Button
        get_selection_btn = ui_qt.QtWidgets.QPushButton("GET")
        _func = partial(ui_qt_utils.populate_line_edit_with_selection, end_txt_field)
        get_selection_btn.clicked.connect(_func)
        _layout.addWidget(get_selection_btn)
        self.content_layout.addLayout(_layout)

        # Setup name and Chain Options
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        setup_name_txt_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            placeholder="<Setup Name / Prefix>",
            layout=_layout,
        )
        setup_name_txt_field.textChanged.connect(self.refresh_output_attr_path_text_field)
        self.add_module_attr_widget_checkbox(
            attr_name="chain",
            nice_name="Use Chain Structure",
            tooltip="If active, module will attempt to detect the hierarchy between start (parent) and end (child) "
            "then create all necessary measuring nodes for the in-between transforms.",
            layout=_layout,
        )
        self.content_layout.addLayout(_layout)

        # Output Field
        self.add_widget_separator_line(label_text="Distance Probe Output Attribute Path")
        self.add_widget_probe_output_text_field()


class AttrWidgetModuleProbeRotation(AttrWidgetModuleProbe):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_separator_line(label_text="Rotation Probe Preferences")

        # Start and End Paths
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        source_txt_field = self.add_module_attr_widget_text_field(
            attr_name="source",
            nice_name="Source",
            placeholder="<Path to Source Object>",
            layout=_layout,
        )
        source_txt_field.setToolTip("Path to a Maya object where to read the isolate rotation from.")
        source_txt_field.textChanged.connect(self.refresh_output_attr_path_text_field)
        # Get Start Button
        get_selection_btn = ui_qt.QtWidgets.QPushButton("GET")
        _func = partial(ui_qt_utils.populate_line_edit_with_selection, source_txt_field)
        get_selection_btn.clicked.connect(_func)
        _layout.addWidget(get_selection_btn)
        combobox_label = ui_qt.QtWidgets.QLabel("Axis:")
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.setMinimumWidth(50)
        combobox.addItems(["X", "Y", "Z"])
        combobox.setCurrentIndex(self.module.axis)
        combobox.currentIndexChanged.connect(self.update_probe_axis)
        _layout.addWidget(combobox_label)
        _layout.addWidget(combobox)
        self.content_layout.addLayout(_layout)

        # Setup name and Chain Options
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        setup_name_txt_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            placeholder="<Setup Name / Prefix>",
            layout=_layout,
        )
        setup_name_txt_field.textChanged.connect(self.refresh_output_attr_path_text_field)
        self.content_layout.addLayout(_layout)

        # Output Field
        self.add_widget_separator_line(label_text="Rotation Probe Output Attribute Path")
        self.add_widget_probe_output_text_field()

    def update_probe_axis(self, index):
        """
        Uses the index of the combobox to define the axis used by the rotation probe
        Args:
            index (int): Index of the selected combobox item.
        """
        self.module.axis = index


class AttrWidgetModuleCollections(AttrWidget):
    """
    An attribute widget for managing rig collections, including support for
    dynamic query-based collections.

    This widget ensures that module data is committed immediately upon any UI change
    and when the widget is instructed to save its data (e.g., when switching modules)
    to prevent data loss.
    """

    def __init__(self, parent=None, *args, **kwargs):
        """
        Initializes the attribute widget for the collections module.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            *args: Additional positional arguments for the base class.
            **kwargs: Additional keyword arguments for the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Collections Section
        self.add_widget_separator_line(label_text="Collections Data")

        # "Add Collection" Button
        add_collection_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(add_collection_button_layout)
        add_collection_button = ui_qt.QtWidgets.QPushButton("Add Collection")
        add_collection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_collection_button.setToolTip("Adds a new, empty collection.")
        add_collection_button.clicked.connect(self.on_add_collection_clicked)
        add_collection_button_layout.addWidget(add_collection_button)

        # Scroll Area for Collection Widgets
        self.collection_scroll_area = ui_qt.QtWidgets.QScrollArea()
        self.collection_scroll_area.setWidgetResizable(True)
        self.collection_scroll_area.setMinimumHeight(220)
        self.collection_container = ui_qt.QtWidgets.QWidget()
        self.collection_vertical_layout = ui_qt.QtWidgets.QVBoxLayout(self.collection_container)
        self.collection_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.collection_vertical_layout.setSpacing(8)
        self.collection_vertical_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.collection_scroll_area.setWidget(self.collection_container)
        self.content_layout.addWidget(self.collection_scroll_area)

        self.refresh_current_widgets()

        # Action Buttons
        write_collections_btn = ui_qt.QtWidgets.QPushButton("Write Collections Data To Current Rig")
        write_collections_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        clear_collections_btn = ui_qt.QtWidgets.QPushButton("Clear Collections Data from Current Rig")
        clear_collections_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))

        _layout = ui_qt.QtWidgets.QHBoxLayout(self)
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(write_collections_btn)
        _layout.addWidget(clear_collections_btn)
        self.content_layout.addLayout(_layout)

        write_collections_btn.clicked.connect(self._write_collections_data)
        clear_collections_btn.clicked.connect(self._clear_collections_data)

    def commit_data(self):
        """
        Overrides the base class method to ensure data is committed
        when the widget is instructed to save (e.g., when switching modules).
        """
        self.commit_collection_data_to_module()

    def add_collection_widget(self, collection_data, query_expression=None):
        """
        Creates and adds a widget for managing a single collection.

        Args:
            collection_data (dict): A dictionary representing one collection.
            query_expression (tuple[str, bool, bool] or None, optional):
                                         It should be (expression_string, is_collection_query, is_joints_only).
                                         If provided, the expression UI is shown. Defaults to None.
        """
        collection_name = list(collection_data.keys())[0]
        collection_objects = list(collection_data.values())[0]
        is_query_mode = query_expression is not None
        query_text = query_expression[0] if is_query_mode else ""
        is_collection_query = query_expression[1] if is_query_mode else False

        default_joints_only = True
        if is_query_mode:
            is_joints_only = query_expression[2] if len(query_expression) > 2 else default_joints_only
        else:
            is_joints_only = default_joints_only

        collection_frame = ui_qt.QtWidgets.QFrame()
        collection_frame.setFrameShape(ui_qt.QtWidgets.QFrame.StyledPanel)
        main_collection_layout = ui_qt.QtWidgets.QVBoxLayout(collection_frame)

        # Top Layout: Name, Query Checkbox, and Delete button
        top_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_label = ui_qt.QtWidgets.QLabel("Collection Name:")
        name_line_edit = ui_qt_utils.ConfirmableQLineEdit(collection_name)
        name_line_edit.setObjectName("collection_name_field")

        # Query Expression Checkbox
        query_checkbox = ui_qt.QtWidgets.QCheckBox("Query Expression")
        query_checkbox.setChecked(is_query_mode)
        query_checkbox.setObjectName("query_checkbox")
        query_checkbox.setToolTip(
            "If checked, this collection is dynamically populated using a search "
            "expression instead of a static object list."
        )

        delete_collection_button = ui_qt.QtWidgets.QPushButton()
        delete_collection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_collection_button.setToolTip("Deletes this entire collection.")

        # Layout for the top row
        top_layout.addWidget(name_label)
        top_layout.addWidget(name_line_edit, 1)
        top_layout.addWidget(query_checkbox)
        top_layout.addWidget(delete_collection_button)

        # Bottom Layout: Static Objects (Default)
        self.static_objects_widget = ui_qt.QtWidgets.QWidget()
        static_objects_layout = ui_qt.QtWidgets.QHBoxLayout(self.static_objects_widget)
        static_objects_layout.setContentsMargins(0, 0, 0, 0)
        objects_label = ui_qt.QtWidgets.QLabel("Objects:")
        objects_line_edit = ui_qt_utils.ConfirmableQLineEdit(", ".join(collection_objects))
        objects_line_edit.setObjectName("objects_list_field")
        objects_line_edit.setPlaceholderText("objOne, objTwo, ...")
        add_selection_button = ui_qt.QtWidgets.QPushButton("Add Selection")
        add_selection_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_cursor))
        add_selection_button.setToolTip("Populates the field with the current Maya selection.")
        static_objects_layout.addWidget(objects_label)
        static_objects_layout.addWidget(objects_line_edit)
        static_objects_layout.addWidget(add_selection_button)

        # Expression Widget (Query Mode)
        self.query_expression_widget = ui_qt.QtWidgets.QWidget()
        query_expression_layout = ui_qt.QtWidgets.QHBoxLayout(self.query_expression_widget)
        query_expression_layout.setContentsMargins(0, 0, 0, 0)
        expression_label = ui_qt.QtWidgets.QLabel("Expression:")
        expression_line_edit = ui_qt_utils.ConfirmableQLineEdit(query_text)
        expression_line_edit.setObjectName("expression_field")
        expression_line_edit.setPlaceholderText("*_JNT, |path|to|geo, etc.")

        # Joints Only Checkbox
        joints_only_checkbox = ui_qt.QtWidgets.QCheckBox("Joints Only")
        joints_only_checkbox.setChecked(is_joints_only)
        joints_only_checkbox.setObjectName("is_joints_only_checkbox")
        joints_only_checkbox.setToolTip("If checked, the Maya search is restricted only to joint type elements.")

        # Query Type Checkbox (Collection Search)
        collection_query_checkbox = ui_qt.QtWidgets.QCheckBox("Collection Search")
        collection_query_checkbox.setChecked(is_collection_query)
        collection_query_checkbox.setObjectName("is_collection_query_checkbox")
        collection_query_checkbox.setToolTip(
            "If checked, the expression is run against existing collections (e.g., 'mesh_collection'), "
            "otherwise it is run as a standard Maya `cmds.ls` query (e.g., '*_GEO')."
        )

        # Update Expression Layout
        query_expression_layout.addWidget(expression_label)
        query_expression_layout.addWidget(expression_line_edit)
        query_expression_layout.addWidget(joints_only_checkbox)
        query_expression_layout.addWidget(collection_query_checkbox)

        self.query_expression_widget.setVisible(is_query_mode)
        self.static_objects_widget.setVisible(not is_query_mode)

        # Assemble Layout
        main_collection_layout.addLayout(top_layout)
        main_collection_layout.addWidget(self.static_objects_widget)
        main_collection_layout.addWidget(self.query_expression_widget)
        self.collection_vertical_layout.addWidget(collection_frame)

        # Connections (Crucial for immediate commit)
        name_line_edit.editingFinished.connect(self.commit_collection_data_to_module)
        objects_line_edit.editingFinished.connect(self.commit_collection_data_to_module)
        expression_line_edit.editingFinished.connect(self.commit_collection_data_to_module)

        # Ensure checkbox state changes commit immediately
        joints_only_checkbox.toggled.connect(self.commit_collection_data_to_module)
        collection_query_checkbox.toggled.connect(self.commit_collection_data_to_module)

        # Query Checkbox Toggling Logic and Commit
        toggle_func = partial(
            self.on_query_checkbox_toggled,
            static_widget=self.static_objects_widget,
            query_widget=self.query_expression_widget,
        )
        query_checkbox.toggled.connect(toggle_func)
        query_checkbox.toggled.connect(self.commit_collection_data_to_module)

        delete_func = partial(self.on_delete_collection_widget_clicked, to_delete=collection_frame)
        delete_collection_button.clicked.connect(delete_func)
        add_selection_func = partial(self.on_add_selection_clicked, target_field=objects_line_edit)
        add_selection_button.clicked.connect(add_selection_func)

    def refresh_current_widgets(self):
        """
        Rebuilds the UI to match the module's current collection data.
        """
        self._clear_layout(self.collection_vertical_layout)

        # Ensure data lists exist on the module
        if not hasattr(self.module, "collection_dicts"):
            self.module.collection_dicts = []
        # Note: self.module.collection_private_keys is no longer managed in the UI
        if not hasattr(self.module, "collection_expressions"):
            self.module.collection_expressions = []

        # Convert expression list for quick lookup: {name: (expression, is_collection_query, is_joints_only)}
        expression_lookup = {}
        default_joints_only = True

        for item in self.module.collection_expressions:
            is_joints_only = item.get("is_joints_only", default_joints_only)
            expression_lookup[item["name"]] = (item["expression"], item["is_collection_query"], is_joints_only)

        # Note: private_keys retrieval removed

        for collection_data in self.module.collection_dicts:
            collection_name = list(collection_data.keys())[0]

            # Note: is_private check removed
            query_expression = expression_lookup.get(collection_name)

            self.add_collection_widget(collection_data=collection_data, query_expression=query_expression)

    def get_collection_data_from_layout(self):
        """
        Extracts all collection data and query expressions from the UI widgets.

        Returns:
            tuple[list[dict], list[str], list[dict]]: A tuple containing:
                - A list of dictionaries representing the collections (name: [objects]).
                - An empty list (legacy compatibility, previously private keys).
                - A list of dictionaries for query expressions.
                  Example: [{"name": "coll_name", "expression": "str", "is_collection_query": bool, "is_joints_only": bool}]
        """
        new_collection_dicts = []
        # The list for private keys is kept but remains empty to match the expected return signature.
        new_private_keys = []
        new_collection_expressions = []

        for index in range(self.collection_vertical_layout.count()):
            collection_frame = self.collection_vertical_layout.itemAt(index).widget()
            if not collection_frame:
                continue

            name_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "collection_name_field")
            collection_name = name_field.text() if name_field else "unknown_collection"

            # Find all relevant UI elements
            query_checkbox = collection_frame.findChild(ui_qt.QtWidgets.QCheckBox, "query_checkbox")

            objects_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "objects_list_field")
            expression_field = collection_frame.findChild(ui_qt.QtWidgets.QLineEdit, "expression_field")
            collection_query_checkbox = collection_frame.findChild(
                ui_qt.QtWidgets.QCheckBox, "is_collection_query_checkbox"
            )
            joints_only_checkbox = collection_frame.findChild(ui_qt.QtWidgets.QCheckBox, "is_joints_only_checkbox")

            # 1. Get Query Expression Status and Data
            is_query_mode = query_checkbox and query_checkbox.isChecked()

            if is_query_mode and expression_field and collection_query_checkbox and joints_only_checkbox:
                expression = expression_field.text().strip()
                is_collection_query = collection_query_checkbox.isChecked()
                is_joints_only = joints_only_checkbox.isChecked()

                # Append the expression data regardless of whether the expression string is empty.
                new_collection_expressions.append(
                    {
                        "name": collection_name,
                        "expression": expression,
                        "is_collection_query": is_collection_query,
                        "is_joints_only": is_joints_only,
                    }
                )

                # The collection_dicts entry will have an empty list of objects when in query mode
                object_names = []

            # 2. Get Static Objects (only if NOT in query mode)
            else:
                if objects_field:
                    objects_text = objects_field.text()
                    # Split by comma, strip whitespace, and remove empty entries
                    object_names = [item.strip() for item in objects_text.split(",") if item.strip()]
                else:
                    object_names = []

            new_collection_dicts.append({collection_name: object_names})

        return new_collection_dicts, new_private_keys, new_collection_expressions

    def commit_collection_data_to_module(self):
        """
        Writes the current collection data, private keys (empty), and expressions from
        the UI to the module instance.
        """
        (new_collection_dicts, new_private_keys, new_collection_expressions) = self.get_collection_data_from_layout()

        self.module.collection_dicts = new_collection_dicts
        # Set collection_private_keys to the empty list returned by get_collection_data_from_layout
        self.module.collection_private_keys = new_private_keys
        self.module.collection_expressions = new_collection_expressions

    def on_add_collection_clicked(self):
        """
        Handles adding a new, empty collection widget.
        """
        # We only need the names from the current layout for conflict checking
        existing_names = [list(d.keys())[0] for d in self.get_collection_data_from_layout()[0]]
        new_name = "collection"
        counter = 1
        while new_name in existing_names:
            new_name = f"collection_{counter}"
            counter += 1

        self.add_collection_widget(collection_data={new_name: []}, query_expression=None)
        self.commit_collection_data_to_module()

    def on_query_checkbox_toggled(self, is_checked, static_widget, query_widget):
        """
        Handles the visibility toggle for the static objects vs. query expression widgets.

        Args:
            is_checked (bool): True if the query checkbox is checked.
            static_widget (QWidget): The widget containing the 'Objects:' field.
            query_widget (QWidget): The widget containing the 'Expression:' field.
        """
        static_widget.setVisible(not is_checked)
        query_widget.setVisible(is_checked)

    def on_delete_collection_widget_clicked(self, to_delete):
        """
        Handles the deletion of a collection widget.

        Args:
            to_delete (QWidget): The collection frame widget to be removed.
        """
        self._remove_widget(to_delete)
        self.commit_collection_data_to_module()

    def on_add_selection_clicked(self, target_field):
        """
        Gets the current Maya selection and populates the target text field.

        Args:
            target_field (QLineEdit): The line edit widget to populate.
        """
        import gt.core.selection as core_sel

        selection = core_sel.ensure_selection_count(
            selection_limit=None,
            require_exact_count=False,
        )

        target_field.setText(", ".join(selection))
        self.commit_collection_data_to_module()

    @staticmethod
    def _clear_layout(layout):
        """
        Removes all widgets from a given layout.

        Args:
            layout (QLayout): The layout to be cleared.
        """
        if not layout:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @staticmethod
    def _remove_widget(widget):
        """
        Removes a Qt widget from its parent and schedules it for deletion.

        Args:
            widget (QWidget): The widget to remove and delete.
        """
        if widget:
            widget.setParent(None)
            widget.deleteLater()

    def _write_collections_data(self):
        """
        Executes the model's setup_collections method to write data to the rig.
        """
        # The first thing we must do here is commit the current UI state to the module
        self.commit_collection_data_to_module()

        root_group = tools_rig_utils.find_root_group_rig()
        if not root_group:
            # Assuming logger and tools_rig_utils are imported/available
            logger.warning(f"No rig detected in the scene. Unable to apply collections data.")
            return
        self.module.setup_collections()
        logger.info("Collection data was written to the current rig.")

    def _clear_collections_data(self):
        """
        Finds and clears the collections data attribute from the rig's root node.
        """
        self.module.clear_collections()


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
class AttrWidgetProject(AttrWidget):
    def __init__(self, parent=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """
        Initialize the project attribute widget panel.

        This widget is designed to display and edit project-level attributes
        and preferences in the UI. It includes project name and prefix fields,
        preference checkboxes, directory path selector, and a mirror proxies table.

        Args:
            parent (QWidget, optional): Parent widget for this UI element.
            project (Project, optional): The project instance whose attributes will be edited.
            refresh_parent_func (callable, optional): Function to call to refresh the parent UI
                after changes. If provided, it is set internally.
            *args: Additional positional arguments passed to the base AttrWidget.
            **kwargs: Additional keyword arguments passed to the base AttrWidget.
        """
        super().__init__(parent, *args, **kwargs)

        # Basic Variables
        self.project = project
        self.project_name_field = None
        self.project_prefix_field = None
        self.refresh_parent_func = None
        self.table_mirror_wdg = None

        if refresh_parent_func:
            self.set_refresh_parent_func(refresh_parent_func)

        self.add_widget_project_header()

        # Preferences
        self.add_widget_separator_line(label_text="Preferences")
        self.add_project_preferences_attr_widget_path(
            attr_name="project_dir",
            nice_name="Project Directory",
            dir_only=True,
            ok_caption="Set Directory",
            placeholder='Project Directory (env-var: "{project-dir}")',
        )

        # Preferences
        _tooltip = (
            "An alias or alternative name for the project. Used when a different name is necessary in "
            "another pipeline step, for example when exporting."
        )
        self.add_project_preferences_attr_widget_text_field(
            attr_name="alias",
            nice_name="Project Alias",
            placeholder='Project Alias (env-var: "{project-alias}")',
            tooltip=_tooltip,
        )
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_project_preferences_attr_widget_checkbox(attr_name="delete_proxy_after_build", layout=_layout)
        self.add_project_preferences_attr_widget_checkbox(attr_name="apply_control_rig_pose", layout=_layout)
        self.add_project_preferences_attr_widget_checkbox(attr_name="hide_skeleton", layout=_layout)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_project_preferences_attr_widget_checkbox(attr_name="view_fit_skeleton", layout=_layout)
        self.content_layout.addLayout(_layout)
        _export_anim_bs_tooltip = (
            "If checked, the generated rig will flag to the Exporter that animations "
            "should include extra geometry describing animated blendshapes."
        )
        self.add_project_preferences_attr_widget_checkbox(
            attr_name="export_anim_blendshapes", layout=_layout, tooltip=_export_anim_bs_tooltip
        )
        self.content_layout.addLayout(_layout)

        # Mirror Table -------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Mirror Proxies")
        self.add_widget_mirror_table()
        self.add_widget_mirror_buttons()

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_widget_project_header(self):
        """
        Adds the header for controlling a project. With Icon, Name and modify button.
        """
        # Project Header (Icon, Name, Buttons)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        _layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        # Icon
        icon = ui_qt.QtGui.QIcon(self.project.icon)
        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        label_tooltip = "Rig Project"
        icon_label.setToolTip(label_tooltip)
        _layout.addWidget(icon_label)

        # Name (User Custom)
        name = self.project.get_name()
        self.project_name_field = ui_qt_utils.ConfirmableQLineEdit()
        self.project_name_field.setFixedHeight(35)
        if name:
            self.project_name_field.setText(name)
        self.project_name_field.editingFinished.connect(self.set_project_name)
        _layout.addWidget(self.project_name_field)

        # Edit Button
        edit_project_btn = ui_qt.QtWidgets.QPushButton()
        edit_project_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        edit_project_btn.setToolTip("Edit Raw Data")
        edit_project_btn.clicked.connect(self.on_button_edit_project_clicked)
        _layout.addWidget(edit_project_btn)
        self.content_layout.addLayout(_layout)

    def on_button_edit_project_clicked(self, skip_modules=True, *args):
        """
        Shows a text-editor window with the project converted to a dictionary (raw data)
        If the user applies the changes, and they are considered valid, the module is updated with it.
        Args:
            skip_modules (bool, optional): If active, the "modules" key will be ignored.
            *args: Variable-length argument list. - Here to avoid issues with the "skip_modules" argument.
        """
        project_name = self.project.get_name()
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=f'Editing Raw Data for the Project "{project_name}"',
            window_title=f'Raw data for "{project_name}"',
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")
        project_raw_data = self.project.get_project_as_dict()
        if "modules" in project_raw_data and skip_modules:
            project_raw_data.pop("modules")
        formatted_dict = core_iter.dict_as_formatted_str(project_raw_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.update_project_from_raw_data, param_win.get_text_field_text, self.project)
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.show()

    # Setters --------------------------------------------------------------------------------------------------
    def set_project_name(self):
        """
        Sets the project name based on the text from the project name input field.

        Retrieves the current text from the project name field, defaults to an empty string
        if the field is empty, updates the project name, and triggers a refresh in the parent.
        """
        new_name = self.project_name_field.text() or ""
        self.project.set_name(new_name)
        self.call_parent_refresh()

    def update_project_from_raw_data(self, data_getter, project):
        """
        Updates a project description using raw string data.
        Used with "on_button_edit_project_clicked" to update a project from raw data.
        Args:
            data_getter (callable): A function used to retrieve the data string. e.g. Get a string from a textfield.
            project (RigProject): A rig project object to be updated using the provided data.
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            project.read_data_from_dict(module_dict=_data_as_dict, clear_modules=False)
            self.refresh_current_widgets()
            self.call_parent_refresh()
        except Exception as e:
            raise Exception(f'Unable to set project attributes from provided raw data. Issue: "{e}".')

    def add_widget_mirror_table(self):
        """
        Adds a table widget to handle the mirroring of the proxies for the listed modules
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        # Mirror table
        self.table_mirror_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_mirror_table()
        columns = ["Source Module", "", "Target Module"]  # Source, Direction, Target
        self.table_mirror_wdg.setColumnCount(len(columns))
        self.table_mirror_wdg.setHorizontalHeaderLabels(columns)
        header_view = self.table_mirror_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        _layout.addWidget(self.table_mirror_wdg)
        self.refresh_mirror_table()
        self.scroll_content_layout.addLayout(_layout)

    def clear_mirror_table(self):
        """
        Clears all rows from the mirror table widget, effectively emptying the table.
        """
        if self.table_mirror_wdg:
            self.table_mirror_wdg.setRowCount(0)

    def get_available_mirror_modules(self):
        """
        Gets the modules of the project allowed to be mirrored.

        Returns:
            list: mirror modules
        """
        mirror_modules = []
        mirror_cat = list(tools_rig_modules.get_mirror_category().keys())
        for module in self.project.get_modules():
            if not any(m_cat in module.__class__.__name__ for m_cat in mirror_cat):
                continue
            mirror_modules.append(module)
        return mirror_modules

    def get_auto_assigned_mirror_map(self, source_prefix=None, target_prefix=None):
        """
        Gets a dictionary with the automatic mirror modules assignment.

        Args:
            source_prefix (str, optional): Prefix identifying source-side modules (e.g., "L_").
                                           Defaults to core_naming.NamingConstants.Prefix.LEFT.
            target_prefix (str, optional): Prefix identifying target-side modules (e.g., "R_").
                                           Defaults to core_naming.NamingConstants.Prefix.RIGHT.

        Returns:
            dict: A mapping where keys are source module names and values are corresponding target module names
                  if a mirror exists, or None if no mirror target is found.
        """

        if not source_prefix:
            source_prefix = core_naming.NamingConstants.Prefix.LEFT
        if not target_prefix:
            target_prefix = core_naming.NamingConstants.Prefix.RIGHT

        auto_assigned_mirror = {}

        mod_list = self.project.get_modules()
        for s_mod in mod_list:
            s_mod_name = s_mod.get_name()
            s_mod_name_no_sides = self._remove_side_from_module_name(s_mod_name)
            s_mod_c_name = s_mod.__module__  # s_mod.get_module_class_name()
            if s_mod.get_prefix() == source_prefix:
                for t_mod in mod_list:
                    t_mod_name = t_mod.get_name()
                    t_mod_name_no_sides = self._remove_side_from_module_name(t_mod_name)
                    t_mod_c_name = t_mod.__module__  # t_mod.get_module_class_name()
                    t_mod_prefix = t_mod.get_prefix()
                    if (
                        s_mod_c_name == t_mod_c_name
                        and t_mod_prefix == target_prefix
                        and s_mod_name_no_sides == t_mod_name_no_sides
                    ):
                        auto_assigned_mirror[s_mod_name] = t_mod_name
            if s_mod_name not in auto_assigned_mirror.keys():
                auto_assigned_mirror[s_mod_name] = None

        return auto_assigned_mirror

    @staticmethod
    def _remove_side_from_module_name(module_name):
        """
        Helper func that returns the module name without sides.
        Args:
            module_name (str): string to filter
        Returns:
            filtered_name: given name without sides
        """
        filtered_name = module_name
        lower_name = module_name.lower()
        separators = ["_", " "]
        sides = ["l", "r", "rt", "lf", "rx", "lt", "left", "right"]

        # clean the start
        for sd in sides:
            for sp in separators:
                full_start_side = sd + sp
                if lower_name.startswith(full_start_side):
                    char_id = len(full_start_side)
                    filtered_name = module_name[char_id:]
                    break

        # clean the rest
        for sd in sides:
            for sp in separators:
                full_inbetween_side = sp + sd + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")
                full_inbetween_side = sp + sd.capitalize() + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")
                full_inbetween_side = sp + sd.upper() + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")

        return filtered_name

    def refresh_mirror_table(self):
        """
        Refresh the mirror table with the module list.
        """
        self.clear_mirror_table()
        mirror_modules = self.get_available_mirror_modules()

        for row, module in enumerate(mirror_modules):
            self.table_mirror_wdg.insertRow(row)

            # Source module
            self.insert_item(
                row=row,
                column=0,
                table=self.table_mirror_wdg,
                text=module.get_name(),
                editable=False,
                data_object=module,
            )

            # Direction
            self.insert_item(
                row=row,
                column=1,
                table=self.table_mirror_wdg,
                icon_path=ui_res_lib.Icon.ui_thin_arrow_right,
                icon_size=22,
                editable=False,
                centered=True,
            )

            # Target module
            combo_mirror_mod_list = self.create_widget_mirror_module_combobox(exclude_mod=[module])
            combo_mirror_mod_list.currentIndexChanged.connect(self.update_table_mirror_target_status)
            self.table_mirror_wdg.setCellWidget(row, 2, combo_mirror_mod_list)

    def create_widget_mirror_module_combobox(self, exclude_mod=None):
        """
        Creates a populated combobox with the mirror modules available.
        Args:
            exclude_mod (list): list of modules to exclude in the combobox
        Returns:
            QComboBox: A pre-populated combobox with the mirror modules.
        """
        mirror_modules = self.get_available_mirror_modules()
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.setEditable(True)
        combobox.lineEdit().setAlignment(ui_qt.QtCore.Qt.AlignCenter)

        # Populate Combobox
        combobox.addItem("---", None)
        exclude_mod_uuids = []
        if exclude_mod:
            exclude_mod_uuids = [mod.uuid for mod in exclude_mod]
        for module in mirror_modules:
            if module.uuid in exclude_mod_uuids:
                continue
            combobox.addItem(module.get_name(), module)

        # Set No Parent at the beginning
        combobox.setCurrentIndex(0)
        combobox.setProperty("lastindex", 0)

        return combobox

    def add_widget_mirror_buttons(self):
        """
        Adds actions buttons (auto assign, mirror proxies)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Auto Assign mirror module
        auto_assign_mirror_btn = ui_qt.QtWidgets.QPushButton("Auto Assign Mirror Targets")
        auto_assign_mirror_btn.clicked.connect(self.on_button_auto_assign_mirror)
        auto_assign_mirror_btn.setToolTip("Auto Assign Mirror Targets")
        _layout.addWidget(auto_assign_mirror_btn)
        # Mirror Proxies
        mirror_proxies_btn = ui_qt.QtWidgets.QPushButton("Mirror Proxies")
        mirror_proxies_btn.clicked.connect(self.on_button_mirror_proxies)
        mirror_proxies_btn.setToolTip("Mirror Proxies")
        _layout.addWidget(mirror_proxies_btn)
        self.scroll_content_layout.addLayout(_layout)

    def on_button_auto_assign_mirror(self):
        """
        Auto-assigns the mirror modules in the mirror table.
        """

        mirror_mod_map = self.get_auto_assigned_mirror_map()
        if not any(mirror_mod_map.values()):
            message_box = ui_qt.QtWidgets.QMessageBox(self)
            message_box.setWindowTitle("Mirror Auto Assign")
            message_box.setText(f"No suitable modules found to auto-assign as mirror targets.")
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()

        rows_to_disable = []
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_mod_name = self.table_mirror_wdg.item(row_num, 0).text()
            target_name_assigned = mirror_mod_map[source_mod_name]
            if not target_name_assigned:
                continue
            combo_target_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            target_index = combo_target_item.findText(target_name_assigned)
            combo_target_item.setCurrentIndex(target_index)

            for t_num in range(self.table_mirror_wdg.rowCount()):
                t_name = self.table_mirror_wdg.item(t_num, 0).text()
                if t_name == target_name_assigned:
                    rows_to_disable.append(t_num)

        self.set_table_mirror_rows_status(row_list=rows_to_disable, status=False)

    def on_button_mirror_proxies(self):
        """
        Initiates the mirroring process for proxies between source and target modules as specified in the mirror table.
        """
        mirrored_modules = []
        failed_modules = {}
        for row_num in range(self.table_mirror_wdg.rowCount()):
            combo_target_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            combo_target_module_obj = combo_target_item.currentData()

            if combo_target_module_obj:
                target_name = combo_target_module_obj.get_name()
                source_module = self.table_mirror_wdg.item(row_num, 0).data(self.PROXY_ROLE)
                source_module_uuid = source_module.get_uuid()
                # check scene proxies
                try:
                    source_mod_proxies = tools_rig_utils.find_drivers_from_module(
                        source_uuid=source_module_uuid,
                        filter_driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
                    )
                    if source_mod_proxies:
                        combo_target_module_obj.set_mirror_uuid(source_module_uuid)
                        combo_target_module_obj.get_proxies_mirrored()
                        mirrored_modules.append(target_name)
                    else:
                        failed_modules[target_name] = "Cannot find source proxies."
                except Exception as e:
                    failed_modules[target_name] = e

        combined_msg = ""
        failed_msg = ""
        mirrored_msg = ""
        msg_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_green_circle)

        if failed_modules:
            failed_msg = "The following modules failed the mirroring process:"
            for mod_name, error in failed_modules.items():
                failed_msg += f"\n - {mod_name}: {error}"
            logger.warning(failed_msg)
            msg_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_yellow_circle)
            combined_msg = failed_msg + "\n\n"

        if mirrored_modules:
            mirrored_msg = f"The following modules have been mirrored: {str(mirrored_modules)}"
            combined_msg += mirrored_msg
            logger.info(mirrored_msg)

        message_box = ui_qt.QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("Mirror Proxies")
        message_box.setText(combined_msg)
        message_box.setIconPixmap(msg_icon.pixmap(64, 64))
        result = message_box.exec_()

    def update_table_mirror_target_status(self, target_index):
        """
        Updates the enabled/disabled status of mirror target widgets in the mirror table
        based on the change in the combo box selection.

        Args:
            target_index (int): The newly selected index in the combo box.
        """
        combo_item = self.sender()
        last_index = combo_item.property("lastindex")
        last_name = combo_item.itemText(last_index)
        new_name = combo_item.itemText(target_index)

        # update status
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_module_name = self.table_mirror_wdg.item(row_num, 0).text()
            target_module_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            if source_module_name == last_name:
                target_module_item.setEnabled(True)
            if source_module_name == new_name:
                target_module_item.setEnabled(False)

        # update combobox item value
        combo_item.setProperty("lastindex", target_index)

    def set_table_mirror_rows_status(self, row_list=None, status=True):
        """
        Sets the given table row status.
        If row_list is None, the status will be applied to all the rows.

        Args:
            row_list (list): row indices of the rows to edit
            status (bool): set enabled or disabled
        """
        if not row_list:
            row_list = [row_num for row_num in range(self.table_mirror_wdg.rowCount())]
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_module_item = self.table_mirror_wdg.item(row_num, 0)
            target_module_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            if row_num in row_list:
                target_module_item.setEnabled(status)
            else:
                target_module_item.setEnabled(not status)

    def refresh_current_widgets(self):
        """
        Refreshes available widgets. For example, text-fields, so they display the correct data.
        """
        if self.project_name_field:
            _name = self.project.get_name()
            if _name:
                self.project_name_field.setText(_name)

        self.refresh_mirror_table()

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_project_preferences_attr_widget_path(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        placeholder=None,
        layout=None,
        ok_caption="Set Path",
        file_filter="All Files (*);;JSON Files (*.json)",
        dir_only=False,
    ):
        """
        Creates a project attribute text field widget that carries a path.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
            ok_caption (str, optional): Caption use for to accept (ok) function.
            file_filter (str, optional): File filter used by the dialog
            dir_only (bool, optional): If True, the path should point to a directory, otherwise a file.

        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """

        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        path_btn = ui_qt.QtWidgets.QPushButton()
        path_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        path_btn.setToolTip("Use file dialog to set path")
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        _layout.addWidget(path_btn)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        _btn_func = partial(
            self.open_module_attr_file_dialog,
            field=text_field,
            ok_caption=ok_caption,
            file_filter=file_filter,
            dir_only=dir_only,
        )
        path_btn.clicked.connect(_btn_func)
        return text_field

    def add_project_preferences_attr_widget_checkbox(
        self, attr_name, attr_value=None, nice_name=None, layout=None, tooltip=None
    ):
        """
        Creates a project preferences attribute checkbox.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (bool, optional): The initial value of the attribute used to set the value
                                        of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QCheckBox: A QCheckBox object.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        checkbox = ui_qt.QtWidgets.QCheckBox()
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        checkbox.setChecked(attr_value)
        if tooltip:
            checkbox.setToolTip(tooltip)
            label.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(checkbox)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=checkbox)
        checkbox.stateChanged.connect(_func)
        return checkbox

    def add_project_preferences_attr_widget_text_field(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        placeholder=None,
        tooltip=None,
        layout=None,
    ):
        """
        Creates a project attribute text field widget that carries a path.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """

        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Tooltip
        if tooltip and isinstance(tooltip, str):
            label.setToolTip(tooltip)
            text_field.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        return text_field

    def set_project_preferences_attr_value_from_field(self, *args, attr, field):
        """
        If the provided attribute name is available in the project preferences, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
            attr (str): Name of the attribute.
            field (QtWidget): A QtWidget object to get the value from
        """
        _value = None
        if isinstance(field, ui_qt.QtWidgets.QLineEdit):
            _value = field.text()
        if isinstance(field, ui_qt_utils.QDoubleSlider):
            _value = field.double_value()
        if isinstance(field, ui_qt_utils.QIntSlider):
            _value = field.int_value()
        if isinstance(field, ui_qt.QtWidgets.QCheckBox):
            _value = field.isChecked()
        if isinstance(field, ui_qt.QtWidgets.QComboBox):
            _value = field.currentText()
        if hasattr(self.project.get_preferences(), attr):
            setattr(self.project.get_preferences(), attr, _value)
        else:
            logger.warning(f'Unable to set missing attribute project preference attribute. Attr: "{attr}".')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
