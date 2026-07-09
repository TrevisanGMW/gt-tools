"""
Auto Rigger Probe Rotation Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

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
