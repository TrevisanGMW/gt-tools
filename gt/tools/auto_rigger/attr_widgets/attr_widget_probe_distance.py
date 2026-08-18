"""
Auto Rigger Probe Distance Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_probe import AttrWidgetModuleProbe
from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

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
