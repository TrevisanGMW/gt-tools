"""
Auto Rigger Attr Widgets
"""

import gt.tools.auto_rigger.rigger_orient_view as tools_rig_orient_view
import gt.tools.auto_rigger.rigger_path_utils as tools_rig_path_utils
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
            nice_name (str, optional): If provided, this name appears in the UI.
                Otherwise, the variable name is formatted.
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
        """Opens a detailed window with more information about a parsed path.

        Args:
            field (QLineEdit): A path field to parse and describe.
        """
        configured_path = field.text()
        parsed_path = self.resolve_path(configured_path)
        tools_rig_path_utils.show_path_information(
            parent=self,
            configured_path=configured_path,
            parsed_path=parsed_path,
            title="Path Information",
        )

    def resolve_path(self, path):
        """Resolves environment variables in a module or project path.

        Args:
            path (str): Configured path to resolve.

        Returns:
            str: Resolved and normalized path.
        """
        if self.module and hasattr(self.module, "parse_path"):
            return self.module.parse_path(path=path)
        environment_variables = tools_rig_frm.get_environment_variables(rig_project=self.project)
        parsed_path = core_str.replace_keys_with_values(path or "", environment_variables)
        if not parsed_path:
            return ""
        return os.path.normpath(parsed_path)

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
    """Provides fallback attributes for modules without a dedicated widget."""

    def __init__(self, parent=None, *args, **kwargs):
        """Initializes the fallback module attribute widget.

        Args:
            parent (QWidget): Parent widget.
            *args: Additional positional arguments for the base widget.
            **kwargs: Additional keyword arguments for the base widget.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_auto_serialized_fields()
        self.add_widget_action_buttons()
