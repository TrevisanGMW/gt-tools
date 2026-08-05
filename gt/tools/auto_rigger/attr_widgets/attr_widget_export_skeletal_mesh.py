"""
Auto Rigger Export Skeletal Mesh Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

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
