"""
Auto Rigger Attr Widgets
"""
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QGridLayout
import gt.ui.resource_library as resource_library
from PySide2.QtGui import QIcon


class ModuleAttrWidget(QWidget):
    def __init__(self, parent=None, module=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.module = module

        # Module Header (Icon, Type, Name, Buttons) ----------------------------------------------
        header_layout = QHBoxLayout()

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
        attr_layout = QGridLayout()

        prefix_label = QLabel("Prefix:")
        self.prefix_text_field = QLineEdit()
        attr_layout.addWidget(prefix_label, 0, 0)
        attr_layout.addWidget(self.prefix_text_field, 0, 1)

        parent_label = QLabel("Parent:")
        self.parent_text_field = QLineEdit()
        self.parent_btn = QPushButton("Set")
        attr_layout.addWidget(parent_label, 1, 0)
        attr_layout.addWidget(self.parent_text_field, 1, 1)
        attr_layout.addWidget(self.parent_btn, 1, 2)

        # Create Layout
        scroll_content_layout = QVBoxLayout(self)
        scroll_content_layout.addLayout(header_layout)
        scroll_content_layout.addLayout(attr_layout)

    def set_module_name(self):
        new_name = self.name_text_field.text() or ""
        self.module.set_name(new_name)


if __name__ == "__main__":
    print('Run it from "__init__.py".')
