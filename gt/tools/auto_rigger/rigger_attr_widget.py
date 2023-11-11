"""
Auto Rigger Attr Widgets
"""
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QGridLayout
from PySide2.QtWidgets import QComboBox, QTableWidget, QHeaderView
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt
from functools import partial
import logging

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

    def __init__(self, parent=None, module=None, project=None, *args, **kwargs):
        """
        Initialize the ModuleAttrWidget.

        Args:
            parent (QWidget): The parent widget.
            module: The module associated with this widget.
            project: The project associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        # Basic Variables
        self.project = project
        self.module = module
        self.known_proxy = {}
        self.table_proxy_parent_wdg = None
        self.table_proxy_basic_wdg = None
        self.mod_name_field = None
        self.mod_prefix_field = None
        self.mod_suffix_field = None

        # Body Options --------------------------------------------------------------------------
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

        # Delete Button
        delete_btn = QPushButton()
        delete_btn.setIcon(QIcon(resource_library.Icon.ui_delete))
        _layout.addWidget(delete_btn)

        # Edit Button
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(resource_library.Icon.ui_edit))
        _layout.addWidget(edit_btn)
        self.content_layout.addLayout(_layout)
        # self.body_layout

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
        header_view = self.table_proxy_parent_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_proxy_parent_wdg)
        self.table_proxy_parent_wdg.setColumnWidth(1, 110)
        self.refresh_proxy_parent_table()
        self.table_proxy_parent_wdg.cellChanged.connect(self.on_proxy_parent_table_cell_changed)
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
        self.table_proxy_basic_wdg.cellChanged.connect(self.on_proxy_parent_table_cell_changed)
        self.scroll_content_layout.addLayout(_layout)

    # Utils ----------------------------------------------------------------------------------------------------
    def refresh_current_widgets(self):
        """
        Refreshes available widgets. For example, tables, so they should the correct module name.
        """
        if self.table_proxy_parent_wdg:
            self.refresh_proxy_parent_table()

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

            # Setup --------------------------------------------------------------------
            edit_proxy_btn = QPushButton()
            edit_proxy_btn.setIcon(QIcon(resource_library.Icon.misc_cog))
            self.table_proxy_parent_wdg.setCellWidget(row, 3, edit_proxy_btn)

            # Delete Setup --------------------------------------------------------------------
            edit_proxy_btn = QPushButton()
            edit_proxy_btn.setIcon(QIcon(resource_library.Icon.ui_delete))
            self.table_proxy_parent_wdg.setCellWidget(row, 4, edit_proxy_btn)

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

            # Setup --------------------------------------------------------------------
            edit_proxy_btn = QPushButton()
            edit_proxy_btn.setIcon(QIcon(resource_library.Icon.misc_cog))
            self.table_proxy_basic_wdg.setCellWidget(row, 2, edit_proxy_btn)

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
        self.edit_btn.setIcon(QIcon(resource_library.Icon.misc_cog))
        header_layout.addWidget(self.edit_btn)

        # Create Layout
        scroll_content_layout = QVBoxLayout(self)
        scroll_content_layout.addLayout(header_layout)

    def set_module_name(self):
        new_name = self.name_text_field.text() or ""
        self.project.set_name(new_name)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
