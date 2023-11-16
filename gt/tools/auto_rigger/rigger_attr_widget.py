"""
Auto Rigger Attr Widgets
"""
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QMessageBox
from PySide2.QtWidgets import QComboBox, QTableWidget, QHeaderView
from gt.utils.iterable_utils import dict_as_formatted_str
from gt.ui.input_window_text import InputWindowText
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import QHeaderWithWidgets
from PySide2 import QtWidgets, QtCore
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt
from functools import partial
import logging
import ast

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleAttrWidget(QWidget):
    """
    Base Widget for managing attributes of a module.
    """
    PROXY_ROLE = QtCore.Qt.UserRole
    PARENT_ROLE = QtCore.Qt.UserRole + 1

    def __init__(self, parent=None, module=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """
        Initialize the ModuleAttrWidget.

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
        self.known_proxy = {}
        self.table_proxy_basic_wdg = None
        self.table_proxy_parent_wdg = None
        self.mod_name_field = None
        self.mod_prefix_field = None
        self.mod_suffix_field = None
        self.refresh_parent_func = None

        if refresh_parent_func:
            self.set_refresh_parent_func(refresh_parent_func)

        # Content Layout
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignTop)

        # Create Layout
        self.scroll_content_layout = QVBoxLayout(self)
        self.scroll_content_layout.setAlignment(Qt.AlignTop)
        self.scroll_content_layout.addLayout(self.content_layout)

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_widget_module_header(self):
        """
        Adds the header for controlling a module. With Icon, Type, Name and modify buttons.
        """
        # Module Header (Icon, Type, Name, Buttons)
        _layout = QHBoxLayout()
        _layout.setAlignment(Qt.AlignTop)

        # Icon
        icon = QIcon(self.module.icon)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        _layout.addWidget(icon_label)

        # Type (Module Class)
        module_type = self.module.get_module_class_name(remove_module_prefix=True)
        _layout.addWidget(QLabel(f"{module_type}"))

        # Name (User Custom)
        name = self.module.get_name()
        self.mod_name_field = QLineEdit()
        if name:
            self.mod_name_field.setText(name)
        self.mod_name_field.textChanged.connect(self.set_module_name)
        _layout.addWidget(self.mod_name_field)

        # Edit Button
        edit_mod_btn = QPushButton()
        edit_mod_btn.setIcon(QIcon(resource_library.Icon.rigger_dict))
        edit_mod_btn.setToolTip("Edit Raw Data")
        edit_mod_btn.clicked.connect(self.on_button_edit_module_clicked)
        _layout.addWidget(edit_mod_btn)
        self.content_layout.addLayout(_layout)

        # Delete Button
        delete_mod_btn = QPushButton()
        delete_mod_btn.setIcon(QIcon(resource_library.Icon.ui_delete))
        delete_mod_btn.clicked.connect(self.delete_module)
        _layout.addWidget(delete_mod_btn)

    def add_widget_module_prefix_suffix(self):
        """
        Adds widgets to control the prefix of the module
        """
        _layout = QHBoxLayout()
        # Prefix
        prefix_label = QLabel("Prefix:")
        prefix_label.setFixedWidth(50)
        self.mod_prefix_field = QLineEdit()
        _layout.addWidget(prefix_label)
        _layout.addWidget(self.mod_prefix_field)
        prefix = self.module.get_prefix()
        self.mod_prefix_field.textChanged.connect(self.set_module_prefix)
        if prefix:
            self.mod_prefix_field.setText(prefix)
        # Suffix
        suffix_label = QLabel("Suffix:")
        suffix_label.setFixedWidth(50)
        self.mod_suffix_field = QLineEdit()
        _layout.addWidget(suffix_label)
        _layout.addWidget(self.mod_suffix_field)
        suffix = self.module.get_suffix()
        if suffix:
            self.mod_suffix_field.setText(suffix)
        self.mod_suffix_field.textChanged.connect(self.set_module_suffix)
        self.content_layout.addLayout(_layout)

    def add_widget_module_parent(self):
        """
        Adds a widget to control the parent of the module
        """
        _layout = QHBoxLayout()
        self.refresh_known_proxy_dict(ignore_list=self.module.get_proxies())
        parent_label = QLabel("Parent:")
        parent_label.setFixedWidth(50)
        module_parent_combo_box = self.create_widget_parent_combobox(target=self.module)
        _layout.addWidget(parent_label)
        _layout.addWidget(module_parent_combo_box)
        module_parent_combo_box.setMinimumSize(1, 1)
        combo_func = partial(self.on_parent_combo_box_changed, combobox=module_parent_combo_box)
        module_parent_combo_box.currentIndexChanged.connect(combo_func)
        self.content_layout.addLayout(_layout)

    def add_widget_proxy_parent_table(self):
        """
        Adds a table widget to control proxies with options to determine parent or delete the proxy
        """
        _layout = QVBoxLayout()
        self.table_proxy_parent_wdg = QTableWidget()
        self.clear_proxy_parent_table()
        columns = ["", "Name", "Parent", "", ""]  # Icon, Name, Parent, Edit, Delete
        self.table_proxy_parent_wdg.setColumnCount(len(columns))
        self.table_proxy_parent_wdg.setHorizontalHeaderLabels(columns)
        header_view = QHeaderWithWidgets()
        self.table_proxy_parent_wdg.setHorizontalHeader(header_view)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_proxy_parent_wdg)
        self.table_proxy_parent_wdg.setColumnWidth(1, 110)
        self.refresh_proxy_parent_table()
        self.table_proxy_parent_wdg.cellChanged.connect(self.on_proxy_parent_table_cell_changed)
        add_proxy_btn = QPushButton()
        add_proxy_btn.setIcon(QIcon(resource_library.Icon.ui_add))
        add_proxy_btn.clicked.connect(self.on_button_add_proxy_clicked)
        add_proxy_btn.setToolTip("Add New Proxy")
        header_view.add_widget(4, add_proxy_btn)
        self.scroll_content_layout.addLayout(_layout)

    def add_widget_proxy_basic_table(self):
        """
        Adds a table widget to control the parent of the proxies inside this proxy
        """
        _layout = QVBoxLayout()
        self.table_proxy_basic_wdg = QTableWidget()
        self.clear_proxy_basic_table()
        columns = ["", "Name", ""]  # Icon, Name, Edit
        self.table_proxy_basic_wdg.setColumnCount(len(columns))
        self.table_proxy_basic_wdg.setHorizontalHeaderLabels(columns)
        header_view = self.table_proxy_basic_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_proxy_basic_wdg)
        self.table_proxy_basic_wdg.setColumnWidth(1, 110)
        self.refresh_proxy_basic_table()
        self.scroll_content_layout.addLayout(_layout)

    def add_widget_action_buttons(self):
        """
        Adds actions buttons (read proxy, build proxy, etc…)
        """
        _layout = QHBoxLayout()
        # Build Module Proxy
        build_mod_proxy_btn = QPushButton("Build Proxy (This Module Only)")
        build_mod_proxy_btn.setIcon(QIcon(resource_library.Icon.library_build))
        build_mod_proxy_btn.clicked.connect(self.on_button_build_mod_proxy_clicked)
        build_mod_proxy_btn.setToolTip("Read Scene Data")
        _layout.addWidget(build_mod_proxy_btn)
        # Read Scene Data
        read_scene_data_btn = QPushButton("Read Scene Data")
        read_scene_data_btn.setIcon(QIcon(resource_library.Icon.library_parameters))
        read_scene_data_btn.clicked.connect(self.on_button_read_scene_data_clicked)
        read_scene_data_btn.setToolTip("Read Scene Data")
        _layout.addWidget(read_scene_data_btn)
        self.scroll_content_layout.addLayout(_layout)

    # Utils ----------------------------------------------------------------------------------------------------
    def refresh_current_widgets(self):
        """
        Refreshes available widgets. For example, tables, so they should the correct module name.
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
        Refreshes the "known_proxy" attribute with all proxies that could be used as parents.
        Args:
            ignore_list (list, optional): A list of proxies to be ignored
        """
        for module in self.project.get_modules():
            for proxy in module.get_proxies():
                if ignore_list and proxy in ignore_list:
                    continue
                self.known_proxy[proxy.get_uuid()] = (proxy, module)

    def refresh_proxy_parent_table(self):
        """
        Refresh the table with proxies associated with the module.
        With extra options to edit parent or delete the proxy.
        """
        self.clear_proxy_parent_table()
        for row, proxy in enumerate(self.module.get_proxies()):
            self.table_proxy_parent_wdg.insertRow(row)
            # Icon ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=0,
                             table=self.table_proxy_parent_wdg,
                             icon_path=resource_library.Icon.util_reset_transforms,
                             editable=False,
                             centered=True)

            # Name ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=1,
                             table=self.table_proxy_parent_wdg,
                             text=proxy.get_name(),
                             data_object=proxy)

            # Parent Combobox ----------------------------------------------------------------
            self.refresh_known_proxy_dict()
            combo_box = self.create_widget_parent_combobox(proxy)
            combo_func = partial(self.on_table_parent_combo_box_changed, source_row=row, source_col=2)
            combo_box.currentIndexChanged.connect(combo_func)
            self.table_proxy_parent_wdg.setCellWidget(row, 2, combo_box)

            # Edit Proxy ---------------------------------------------------------------------
            edit_proxy_btn = QPushButton()
            edit_proxy_btn.setIcon(QIcon(resource_library.Icon.rigger_dict))
            edit_proxy_func = partial(self.on_button_edit_proxy_clicked, proxy=proxy)
            edit_proxy_btn.clicked.connect(edit_proxy_func)
            edit_proxy_btn.setToolTip("Edit Raw Data")
            self.table_proxy_parent_wdg.setCellWidget(row, 3, edit_proxy_btn)

            # Delete Setup --------------------------------------------------------------------
            delete_proxy_btn = QPushButton()
            delete_proxy_btn.setIcon(QIcon(resource_library.Icon.ui_delete))
            delete_proxy_func = partial(self.delete_proxy, proxy=proxy)
            delete_proxy_btn.clicked.connect(delete_proxy_func)
            delete_proxy_btn.setToolTip("Delete Proxy")
            self.table_proxy_parent_wdg.setCellWidget(row, 4, delete_proxy_btn)

    def refresh_proxy_basic_table(self):
        """
        Refresh the table with proxies associated with the module.
        """
        self.clear_proxy_basic_table()
        for row, proxy in enumerate(self.module.get_proxies()):
            self.table_proxy_basic_wdg.insertRow(row)
            # Icon ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=0,
                             table=self.table_proxy_basic_wdg,
                             icon_path=resource_library.Icon.util_reset_transforms,
                             editable=False,
                             centered=True)

            # Name ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=1,
                             table=self.table_proxy_basic_wdg,
                             text=proxy.get_name(),
                             data_object=proxy)

            # Edit Proxy ---------------------------------------------------------------------
            edit_proxy_btn = QPushButton()
            edit_proxy_btn.setIcon(QIcon(resource_library.Icon.rigger_dict))
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
        Args:
            data_getter (callable): A function used to retrieve the data string
            module (ModuleGeneric): A module object to be updated using the data
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            module.read_data_from_dict(_data_as_dict)
            self.refresh_current_widgets()
        except Exception as e:
            raise Exception(f'Unable to set module attributes from provided raw data. Issue: "{e}".')

    def clear_proxy_parent_table(self):
        if self.table_proxy_parent_wdg:
            self.table_proxy_parent_wdg.setRowCount(0)

    def clear_proxy_basic_table(self):
        if self.table_proxy_basic_wdg:
            self.table_proxy_basic_wdg.setRowCount(0)

    def insert_item(self, row, column, table, text=None, data_object=None,
                    icon_path='', editable=True, centered=True):
        """
        Insert an item into the table.

        Args:
            row (int): Row index.
            column (int): Column index.
            table (QTableWidget): Target table.
            text (str): Text to display in the item.
            data_object: The associated data object.
            icon_path (str): Path to the icon. (If provided, text is ignored)
            editable (bool): Whether the item is editable.
            centered (bool): Whether the text should be centered.
        """
        item = QtWidgets.QTableWidgetItem(text)
        self.set_table_item_proxy_object(item, data_object)

        if icon_path != '':
            icon = QIcon(icon_path)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(32, 32))
            icon_label.setAlignment(Qt.AlignCenter)
            table.setCellWidget(row, column, icon_label)
            return

        if centered:
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        if not editable:
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

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
        _name_cell = self.table_proxy_parent_wdg.item(source_row, 1)
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

    def on_proxy_parent_table_cell_changed(self, row, column):
        """
        Updates the name of the proxy object in case the user writes a new name in the name cell.
        Args:
            row (int): Row where the cell changed.
            column (int): Column where the cell changed.
        """
        _source_table = self.table_proxy_parent_wdg
        _source_table.cellChanged.disconnect(self.on_proxy_parent_table_cell_changed)  # Fix recursion errors
        _name_cell = _source_table.item(row, 1)  # 1 = Name
        _proxy = self.get_table_item_proxy_object(_name_cell)
        current_name = _proxy.get_name()
        new_name = _name_cell.text()
        if new_name:
            _proxy.set_name(new_name)
            self.refresh_proxy_parent_table()
        else:
            _name_cell.setText(current_name)
        _source_table.cellChanged.connect(self.on_proxy_parent_table_cell_changed)  # Fix recursion errors

    def on_button_edit_proxy_clicked(self, proxy):
        """
        Shows a text-editor window with the proxy converted to a dictionary (raw data)
        If the user applies the changes, and they are considered valid, the proxy is updated with it.
        Args:
            proxy (Proxy): The target proxy (proxy to be converted to dictionary)
        """
        param_win = InputWindowText(parent=self,
                                    message=f'Editing Raw Data for the Proxy "{proxy.get_name()}"',
                                    window_title=f'Raw data for "{proxy.get_name()}"',
                                    image=resource_library.Icon.rigger_dict,
                                    window_icon=resource_library.Icon.library_parameters,
                                    image_scale_pct=10,
                                    is_python_code=True)
        param_win.set_confirm_button_text("Apply")
        proxy_raw_data = proxy.get_proxy_as_dict(include_uuid=True,
                                                 include_transform_data=True,
                                                 include_offset_data=True)
        formatted_dict = dict_as_formatted_str(proxy_raw_data, one_key_per_line=True)
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
        param_win = InputWindowText(parent=self,
                                    message=f'Editing Raw Data for the Module "{module_name}"',
                                    window_title=f'Raw data for "{module_name}"',
                                    image=resource_library.Icon.rigger_dict,
                                    window_icon=resource_library.Icon.library_parameters,
                                    image_scale_pct=10,
                                    is_python_code=True)
        param_win.set_confirm_button_text("Apply")
        module_raw_data = self.module.get_module_as_dict(include_module_name=True, include_offset_data=True)
        if "proxies" in module_raw_data and skip_proxies:
            module_raw_data.pop("proxies")
        formatted_dict = dict_as_formatted_str(module_raw_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.update_module_from_raw_data,
                                      param_win.get_text_field_text,
                                      self.module)
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
        print('"on_button_read_scene_data_clicked called')
        self.module.read_data_from_scene()
        self.refresh_current_widgets()

    def on_button_build_mod_proxy_clicked(self):
        """
        Reads proxy data from scene
        """
        print('"on_button_build_mod_proxy_clicked called')

    def create_widget_parent_combobox(self, target):
        """
        Creates a populated combobox with all potential parent targets.
        An extra initial item called "No Parent" is also added for the proxies without parents.
        Current parent is pre-selected during creation.
        Args:
            target (Proxy, Module): A proxy or module object used to determine current parent and pre-select it.
        Returns:
            QComboBox: A pre-populated combobox with potential parents. Current parent is also pre-selected.
        """
        self.refresh_known_proxy_dict()

        combobox = QComboBox()
        combobox.addItem("No Parent", None)

        _proxy_uuid = None
        if target and hasattr(target, 'get_uuid'):  # Is proxy
            _proxy_uuid = target.get_uuid()
        _proxy_parent_uuid = target.get_parent_uuid()

        # Populate Combobox
        for key, (_proxy, _module) in self.known_proxy.items():
            if key == _proxy_uuid:
                continue  # Skip Itself
            description = f'{str(_proxy.get_name())}'
            module_name = _module.get_name()
            if module_name:
                description += f' : {str(module_name)}'
            description += f' ({str(key)})'
            combobox.addItem(description, _proxy)

        # Unknown Target
        if _proxy_parent_uuid and _proxy_parent_uuid in self.known_proxy:
            for index in range(combobox.count()):
                _parent_proxy = combobox.itemData(index)
                if _parent_proxy and _proxy_parent_uuid == _parent_proxy.get_uuid():
                    combobox.setCurrentIndex(index)
        elif _proxy_parent_uuid and _proxy_parent_uuid not in self.known_proxy:
            description = f'unknown : ???'
            description += f' ({str(_proxy_parent_uuid)})'
            combobox.addItem(description, None)
            combobox.setCurrentIndex(combobox.count() - 1)  # Last item, which was just added
        return combobox

    def call_parent_refresh(self):
        """
        Calls the refresh parent function. This function needs to first be set before it can be used.
        In case it has not been set, or it's missing, the operation will be ignored.
        """
        if not self.refresh_parent_func or not callable(self.refresh_parent_func):
            logger.debug(f'Unable to call refresh tree function. Function has not been set or is missing.')
            return
        self.refresh_parent_func()

    def delete_proxy(self, proxy):
        _proxy_name = proxy.get_name()
        message_box = QMessageBox(self)
        message_box.setWindowTitle(f'Delete Proxy "{str(_proxy_name)}"?')
        message_box.setText(f'Are you sure you want to delete proxy "{str(_proxy_name)}"?')
        question_icon = QIcon(resource_library.Icon.ui_delete)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        message_box.addButton(QMessageBox.Yes)
        message_box.addButton(QMessageBox.No)
        result = message_box.exec_()
        if result == QMessageBox.Yes:
            self.module.remove_from_proxies(proxy)
            self.refresh_known_proxy_dict()
            self.refresh_current_widgets()

    def delete_module(self):
        _module_name = self.module.get_name() or ""
        _module_class = self.module.get_module_class_name(remove_module_prefix=False)
        if _module_name:
            _module_name = f'\n"{_module_name}" ({_module_class})'
        else:
            _module_name = f'\n{_module_class}'
        message_box = QMessageBox(self)
        message_box.setWindowTitle(f'Delete Module {str(_module_name)}?')
        message_box.setText(f'Are you sure you want to delete module {str(_module_name)}?')
        question_icon = QIcon(resource_library.Icon.ui_delete)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        message_box.addButton(QMessageBox.Yes)
        message_box.addButton(QMessageBox.No)
        result = message_box.exec_()
        if result == QMessageBox.Yes:
            self.project.remove_from_modules(self.module)
            self.call_parent_refresh()
            self.toggle_content_visibility()

    # Setters --------------------------------------------------------------------------------------------------
    def set_module_name(self):
        """
        Set the name of the module based on the text in the name text field.
        """
        new_name = self.mod_name_field.text() or ""
        self.module.set_name(new_name)
        self.refresh_current_widgets()

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
            logger.warning(f'Unable to set refresh tree function. Provided argument is not a callable object.')
            return
        self.refresh_parent_func = func

    def toggle_content_visibility(self):
        """
        Updates the visibility of the "scroll_content_layout" to the opposite of its value.
        """
        self.scroll_content_layout.parent().setHidden(not self.scroll_content_layout.parent().isHidden())

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


class ModuleGenericAttrWidget(ModuleAttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the ModuleGenericAttrWidget.
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
        self.add_widget_proxy_parent_table()
        self.add_widget_action_buttons()


class ModuleSpineAttrWidget(ModuleAttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the ModuleSpineAttrWidget.
        Used for generic nodes with options to edit parents and proxies directly.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()


class ProjectAttrWidget(QWidget):
    def __init__(self, parent=None, project=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.project = project

        # Project Header (Icon, Type, Name, Buttons) ----------------------------------------------
        header_layout = QHBoxLayout()

        # Icon
        icon = QIcon(project.icon)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        header_layout.addWidget(icon_label)

        # Type (Project)
        header_layout.addWidget(QLabel("RigProject"))
        header_layout.setAlignment(Qt.AlignTop)

        # Name (User Custom)
        name = project.get_name()
        self.name_text_field = QLineEdit()
        if name:
            self.name_text_field.setText(name)
        self.name_text_field.textChanged.connect(self.set_module_name)
        header_layout.addWidget(self.name_text_field)

        # Edit Button
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(resource_library.Icon.rigger_dict))
        header_layout.addWidget(self.edit_btn)

        # Create Layout
        scroll_content_layout = QVBoxLayout(self)
        scroll_content_layout.addLayout(header_layout)

    def set_module_name(self):
        new_name = self.name_text_field.text() or ""
        self.project.set_name(new_name)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
