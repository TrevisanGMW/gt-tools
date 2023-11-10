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

        self.project = project
        self.module = module
        self.known_proxy = {}

        # Module Header (Icon, Type, Name, Buttons) ----------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignTop)

        # Icon
        icon = QIcon(module.icon)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        header_layout.addWidget(icon_label)

        # Type (Module Class)
        module_type = module.get_module_class_name(remove_module_prefix=True)
        header_layout.addWidget(QLabel(f"{module_type}"))

        # Name (User Custom)
        name = module.get_name()
        self.name_text_field = QLineEdit()
        if name:
            self.name_text_field.setText(name)
        self.name_text_field.textChanged.connect(self.set_module_name)
        header_layout.addWidget(self.name_text_field)

        # Delete Button
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(resource_library.Icon.dev_trash))
        header_layout.addWidget(self.delete_btn)

        # Help Button
        self.help_btn = QPushButton()
        self.help_btn.setIcon(QIcon(resource_library.Icon.root_help))
        header_layout.addWidget(self.help_btn)

        # Other Options --------------------------------------------------------------------------

        self.body_layout = QGridLayout()
        self.body_layout.setAlignment(Qt.AlignTop)

        prefix_label = QLabel("Prefix:")
        self.prefix_text_field = QLineEdit()
        self.body_layout.addWidget(prefix_label, 0, 0)
        self.body_layout.addWidget(self.prefix_text_field, 0, 1)

        # Create Layout
        self.scroll_content_layout = QVBoxLayout(self)
        self.scroll_content_layout.setAlignment(Qt.AlignTop)
        self.scroll_content_layout.addLayout(header_layout)
        self.scroll_content_layout.addLayout(self.body_layout)

    # Setters --------------------------------------------------------------------------------------------------
    def set_module_name(self):
        """
        Set the name of the module based on the text in the name text field.
        """
        new_name = self.name_text_field.text() or ""
        self.module.set_name(new_name)

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

    def insert_item(self, row, column, text=None, data_object=None,
                    icon_path='', editable=True, centered=True):
        """
        Insert an item into the table.

        Args:
            row (int): Row index.
            column (int): Column index.
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
            self.table_wdg.setCellWidget(row, column, icon_label)
            return

        if centered:
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        if not editable:
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        self.table_wdg.setItem(row, column, item)

    # Utils ----------------------------------------------------------------------------------------------------
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

    def refresh_table(self):
        """
        Refresh the table with proxies associated with the module.
        """
        for row, proxy in enumerate(self.module.get_proxies()):
            self.table_wdg.insertRow(row)
            # Icon ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=0,
                             icon_path=resource_library.Icon.dev_git_fork,
                             editable=False,
                             centered=True)

            # Name ---------------------------------------------------------------------------
            self.insert_item(row=row,
                             column=1,
                             text=proxy.get_name(),
                             data_object=proxy)

            # Parent Combobox ----------------------------------------------------------------
            combo_box = self.create_parent_combobox(proxy)
            combo_func = partial(self.on_table_parent_combo_box_changed, source_row=row, source_col=2)
            combo_box.currentIndexChanged.connect(combo_func)

            # Proxy Setup --------------------------------------------------------------------
            self.insert_item(row=row,
                             column=2,
                             data_object=proxy)

            # Add to Table -------------------------------------------------------------------
            self.table_wdg.setCellWidget(row, 2, combo_box)

    def on_table_parent_combo_box_changed(self, index, source_row, source_col):
        """
        Handle the change in the parent combo box for the proxy table.

        Args:
            index (int): Index of the selected item.
            source_row (int): Row index.
            source_col (int): Column index.
        """
        _name_cell = self.table_wdg.item(source_row, 1)
        _proxy = self.get_table_item_proxy_object(_name_cell)
        _combo_box = self.table_wdg.cellWidget(source_row, source_col)
        _parent_proxy = _combo_box.itemData(index)
        if _parent_proxy is None:
            _proxy.clear_parent_uuid()
            logger.debug(f"{_proxy.get_name()}: to : None")
        else:
            _proxy.set_parent_uuid(_parent_proxy.get_uuid())
            logger.debug(f"{_proxy.get_name()}: to : {_parent_proxy.get_name()}")

    def create_parent_combobox(self, proxy):
        """
        Creates a populated combobox with all potential parent targets.
        An extra initial item called "No Parent" is also added for the proxies without parents.
        Current parent is pre-selected during creation.
        Args:
            proxy (Proxy): A proxy object used to determine current parent and pre-select it.
        Returns:
            QComboBox: A pre-populated combobox with potential parents. Current parent is also pre-selected.
        """
        self.refresh_known_proxy_dict()

        combo_box = QComboBox()
        combo_box.addItem("No Parent", None)
        _proxy_uuid = proxy.get_uuid()
        _proxy_parent_uuid = proxy.get_parent_uuid()

        # Populate Combobox
        for key, (_proxy, _module) in self.known_proxy.items():
            if key == _proxy_uuid:
                continue  # Skip Itself
            description = f'{str(_proxy.get_name())}'
            module_name = _module.get_name()
            if module_name:
                description += f' : {str(module_name)}'
            description += f' ({str(key)})'
            combo_box.addItem(description, _proxy)

        # Unknown Target
        if _proxy_parent_uuid and _proxy_parent_uuid in self.known_proxy:
            for index in range(combo_box.count()):
                _parent_proxy = combo_box.itemData(index)
                if _parent_proxy and _proxy_parent_uuid == _parent_proxy.get_uuid():
                    combo_box.setCurrentIndex(index)
        elif _proxy_parent_uuid and _proxy_parent_uuid not in self.known_proxy:
            description = f'unknown : ???'
            description += f' ({str(_proxy_parent_uuid)})'
            combo_box.addItem(description, None)
            combo_box.setCurrentIndex(combo_box.count() - 1)  # Last item, which was just added
        return combo_box


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

        #
        # parent_label = QLabel("Parent:")
        # self.parent_text_field = QLineEdit()
        # self.parent_btn = QPushButton("Get Selection")
        # self.body_layout.addWidget(parent_label, 1, 0)
        # self.body_layout.addWidget(self.parent_text_field, 1, 1)
        # self.body_layout.addWidget(self.parent_btn, 1, 2)

        proxy_table = QVBoxLayout()
        self.table_wdg = QTableWidget()
        self.table_wdg.setRowCount(0)
        self.table_wdg.setColumnCount(4)  # Icon, Name, Parent, Get, More
        self.table_wdg.setHorizontalHeaderLabels(["", "Name", "Parent", ""])
        header_view = self.table_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        proxy_table.addWidget(self.table_wdg)
        self.table_wdg.setColumnWidth(1, 110)
        self.refresh_table()

        self.scroll_content_layout.addLayout(proxy_table)


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

        # Help Button
        self.help_btn = QPushButton()
        self.help_btn.setIcon(QIcon(resource_library.Icon.root_help))
        header_layout.addWidget(self.help_btn)

        # Create Layout
        scroll_content_layout = QVBoxLayout(self)
        scroll_content_layout.addLayout(header_layout)

    def set_module_name(self):
        new_name = self.name_text_field.text() or ""
        self.project.set_name(new_name)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
