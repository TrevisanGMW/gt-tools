"""
Auto Rigger Group Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

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
