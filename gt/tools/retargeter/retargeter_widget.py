"""
Auto Rigger Attr Widgets
"""

import gt.tools.retargeter.retargeter_constants as tools_retargeter_const
import gt.tools.retargeter.retargeter_framework as tools_retargeter_frm
import gt.core.rig_switch as core_rig_switch
import gt.ui.resource_library as ui_res_lib
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_utils as ui_qt_utils
import gt.core.naming as core_naming
import gt.ui.qt_import as ui_qt
import gt.core.str as core_str
from functools import partial
import importlib
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ------------------------------------------ Retargeter Widgets ---------------------------------------------------
class TabWidget(ui_qt.QtWidgets.QTabWidget):
    def __init__(self, parent, tab_title_list=None, margin=None):
        """
        Initialize a custom tab widget with specified tab titles and optional margins.

        Args:
            parent (QWidget): The parent widget.
            tab_title_list (list[str], optional): List of tab titles to create. Defaults to ["Placeholder"] if None.
            margin (int, optional): Margin size applied on all sides inside each tab's layout. Defaults to 0 if None.
        """
        super().__init__(parent=parent)

        self.layout_list = []
        if not tab_title_list:
            tab_title_list = ["Placeholder"]

        if not margin:
            margin = 0

        for tab_name in tab_title_list:
            tab_item_widget = ui_qt.QtWidgets.QWidget()
            tab_item_layout = ui_qt.QtWidgets.QVBoxLayout(tab_item_widget)
            tab_item_layout.setContentsMargins(margin, margin, margin, margin)
            self.addTab(tab_item_widget, tab_name)
            self.layout_list.append(tab_item_layout)


class TextBrowseFileWidget(ui_qt.QtWidgets.QWidget):

    def __init__(
        self,
        parent,
        var_name=None,
        var_value=None,
        nice_name=None,
        browse=True,
        dir_only=False,
        file_filter=None,
        tooltip=None,
        label_width=0,
        browse_width=30,
        align_end=False,
    ):
        """
        A custom QWidget that defines a text line with a browse option.

        Args:
            parent (RetargeterView): The RetargeterView.
            var_name (str, optional): Name of the parent class variable that the widget will try to set when the
                                      text field change. Defaults to None.
            var_value (str, optional): The initial value of the variable used to set the value of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead.
            browse (bool, optional): Adds button to browse a file and insert the path in the text field.
            dir_only (bool, optional): If True it will only accept directories, no files.
            file_filter (str, optional): File filter used by the dialog.
            tooltip (str, optional): the widget tooltip.
            label_width (int): if not 0, it will apply a fixed width for the label (first field).
            browse_width (int): the width of the last part of the widget.
            align_end (bool): if True, the end of the text field will maintain the same position, independently if
                              there is or not the browse button.
        """
        super().__init__(parent=parent)

        _formatted_attr_name = core_str.snake_to_title(var_name)
        if nice_name:
            _formatted_attr_name = nice_name
        if tooltip:
            self.setToolTip(tooltip)

        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Create Widgets
        self.label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        font = self.label.font()
        self.label.setFont(font)
        if label_width:
            self.label.setMinimumWidth(label_width)

        self.text_field = ui_qt_utils.ConfirmableQLineEdit()
        self.text_field.setFixedHeight(35)

        # Add to Widgets
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_field)

        if browse:
            if not file_filter:
                file_filter = tools_retargeter_const.RetargeterConstants.BASE_FILTER
            path_btn = ui_qt.QtWidgets.QPushButton()
            path_btn.setFixedWidth(browse_width - 2)  # compensate button
            path_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
            path_btn.setToolTip("Use file dialog to set path")
            self.layout.addWidget(path_btn)
            _btn_func = partial(
                open_file_dialog,
                field=self.text_field,
                ok_caption="Set Path",
                file_filter=file_filter,
                dir_only=dir_only,
            )
            path_btn.clicked.connect(_btn_func)
        else:
            if align_end:
                _distance = ui_qt.QtWidgets.QLabel()
                _distance.setFixedWidth(browse_width)
                self.layout.addWidget(_distance)

        if var_value:
            self.text_field.setText(var_value)
            set_value_from_field(parent=parent, var=var_name, field=self.text_field)

        if var_name is None:
            return

        placeholder = f"<{var_name}>"
        if var_value is None:
            var_value = getattr(parent, var_name)

        self.text_field.setText(var_value)
        self.text_field.setPlaceholderText(placeholder)

        # Connect text field
        _func = partial(set_value_from_field, parent=parent, var=var_name, field=self.text_field)
        self.text_field.textChanged.connect(_func)


class DropDownWidget(ui_qt.QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        var_name=None,
        nice_name=None,
        option_list=None,
        default_option=None,
        add_none=True,
        tooltip=None,
        label_width=0,
        end_margin=0,
    ):
        """
        A custom QWidget that defines a drop-down custom widget.

        Args:
            parent (RetargeterView): The RetargeterView.
            var_name (str, optional): Name of the parent class variable that the widget will try to set when the
                                      selected option change. Defaults to None.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead.
            option_list (list, optional): List of strings to populate the drop-down widget. Defaults to None.
                                          If the given list has inside lists of two dimensions
                                          (e.g. [["label", "data"]]), the first element will be used as item label and
                                          the second as item data.
            default_option (str, optional): One of the options in the given option_list to set as default.
            add_none (bool): Adds None as first element of the dropdown list.
            tooltip (str, optional): the widget tooltip.
            label_width (int): if not 0, it will apply a fixed width for the label (first field).
            end_margin (int): margin to the right of the widget.
        """
        super().__init__(parent=parent)

        _formatted_attr_name = core_str.snake_to_title(var_name)
        if nice_name:
            _formatted_attr_name = nice_name
        if tooltip:
            self.setToolTip(tooltip)

        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Create Widgets
        self.label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        font = self.label.font()
        self.label.setFont(font)
        self.label.setFixedHeight(35)
        if label_width:
            self.label.setFixedWidth(label_width)

        self.combobox = ui_qt.QtWidgets.QComboBox()
        self.combobox.setFixedHeight(28)
        self.combobox.installEventFilter(self)

        # Add to Widgets
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)

        if end_margin:
            _distance = ui_qt.QtWidgets.QLabel()
            _distance.setFixedWidth(end_margin)
            self.layout.addWidget(_distance)

        # Populate ComboBox
        if add_none:
            if not option_list:
                option_list = ["None"]

        if option_list:
            self.populate_list(option_list, default_option=default_option, add_none=add_none)

        # Connect
        _func = partial(set_value_from_field, parent=parent, var=var_name, field=self.combobox)
        self.combobox.currentIndexChanged.connect(_func)

    def eventFilter(self, source, event):
        """
        Filters out mouse wheel events to prevent unwanted scrolling or zooming.

        Args:
            source (ui_qt.QtCore.QObject): The object that sent the event.
            event (ui_qt.QtCore.QEvent): The event that occurred.

        Returns:
            bool: True if the wheel event was filtered; otherwise, the return
                  value of the parent's eventFilter method.
        """
        if event.type() == ui_qt.QtCore.QEvent.Type.Wheel:
            event.ignore()
            return True
        else:
            return super().eventFilter(source, event)

    def populate_list(self, option_list, default_option=None, add_none=True):
        """
        Fills the combobox with the given list.

        Args:
            option_list (list): List of strings to populate the drop-down widget. Defaults to None.
                                if the given list has inside lists of two dimensions
                                (e.g. [["label", "data"]]), the first element will be used as item label and
                                the second as item data.
            default_option (str, optional): One of the options in the given option_list to set as default.
            add_none (bool): Adds None as first element of the dropdown list.
        """

        if not option_list:
            return

        _has_data = None
        if isinstance(option_list, list):
            if isinstance(option_list[0], list):  # attempt to use data, assumption elements of length two
                _has_data = True
                if add_none:
                    option_list.insert(0, ["None", None])
            elif isinstance(option_list[0], str):
                _has_data = False
                if add_none:
                    option_list.insert(0, "None")
            else:
                logger.debug("Given list of elements to populate the combobox has invalid type.")
                return

        # Populate combobox
        _available_options = []
        for index, opt in enumerate(option_list):
            if _has_data:
                self.combobox.addItem(opt[0])  # Add label
                self.combobox.setItemData(index, opt[1])  # Add data
                _available_options.append(opt[0])
            else:
                self.combobox.addItem(opt)  # Add label
                _available_options.append(opt)

        if default_option:
            if isinstance(default_option, str):
                if default_option in _available_options:
                    self.combobox.setCurrentText(default_option)
        else:
            self.combobox.setCurrentIndex(0)


class CheckBoxWidget(ui_qt.QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        var_name=None,
        nice_name=None,
        checked=True,
        tooltip=None,
        label_width=0,
        end_margin=0,
    ):
        """
        A custom QWidget that defines a checkbox custom widget.

        Args:
            parent (class): Another widget or the tool view.
            var_name (str, optional): Name of the parent class variable that the widget will try to set when the
                                      selected option change. Defaults to None.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead.
            checked (bool, optional): Initial status of the checkbox. Default to True.
            tooltip (str, optional): the widget tooltip.
            label_width (int): if not 0, it will apply a fixed width for the label (first field).
            end_margin (int): margin to the right of the widget.
        """
        super().__init__(parent=parent)

        _formatted_attr_name = core_str.snake_to_title(var_name)
        if nice_name:
            _formatted_attr_name = nice_name
        if tooltip:
            self.setToolTip(tooltip)

        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Create Widgets
        self.label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        font = self.label.font()
        font.setPointSize(8)
        self.label.setFont(font)
        self.label.setFixedHeight(35)
        if label_width:
            self.label.setFixedWidth(label_width)
        else:
            self.label.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Expanding, ui_qt.QtWidgets.QSizePolicy.Preferred)

        self.checkbox = ui_qt.QtWidgets.QCheckBox()

        # Add to Widgets
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)

        if end_margin:
            _distance = ui_qt.QtWidgets.QLabel()
            _distance.setFixedWidth(end_margin)
            self.layout.addWidget(_distance)

        # Set status
        self.checkbox.setChecked(checked)

        # Connect
        _func = partial(set_value_from_field, parent=parent, var=var_name, field=self.checkbox)
        self.checkbox.stateChanged.connect(_func)


class NumericSliderWidget(ui_qt.QtWidgets.QWidget):
    def __init__(
        self,
        parent,
        var_name=None,
        nice_name=None,
        min_value=-10,
        max_value=10,
        default_value=0,
        float_type=False,
        float_precision=3,
        tooltip=None,
        label_width=0,
        end_margin=0,
    ):
        """
        A custom QWidget that defines a checkbox custom widget.

        Args:
            parent (class): Another widget or the tool view.
            var_name (str, optional): Name of the parent class variable that the widget will try to set when the
                                      selected option change. Defaults to None.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead.
            min_value (int, optional): Initial min value for the slider. Default to -10.
            max_value (int, optional): Initial max value for the slider. Default to 10.
            default_value (int, optional): Initial default value for the slider. Default to 0.
            float_type (bool, optional): If true the field will handle float values instead of integers.
            float_precision (int): The precision of the double spin box (decimals).
            tooltip (str, optional): the widget tooltip.
            label_width (int): if not 0, it will apply a fixed width for the label (first field).
            end_margin (int): margin to the right of the widget.
        """
        super().__init__(parent=parent)

        _formatted_attr_name = core_str.snake_to_title(var_name)
        if nice_name:
            _formatted_attr_name = nice_name
        if tooltip:
            self.setToolTip(tooltip)

        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        font = label.font()
        font.setPointSize(8)
        label.setFont(font)
        label.setFixedHeight(35)
        if label_width:
            label.setFixedWidth(label_width)
        else:
            label.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Expanding, ui_qt.QtWidgets.QSizePolicy.Preferred)

        if float_type:
            self.numeric_slider = ui_qt_utils.QDoubleSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
            spinbox.setDecimals(float_precision)
            self.numeric_slider.link_spin_box(spinbox)
            self.numeric_slider.set_double_range(min_double=min_value, max_double=max_value)
            self.numeric_slider.set_double_value(default_value)
        else:
            self.numeric_slider = ui_qt_utils.QIntSlider(ui_qt.QtLib.Orientation.Horizontal)
            spinbox = ui_qt.QtWidgets.QSpinBox()
            self.numeric_slider.link_spin_box(spinbox)
            self.numeric_slider.set_int_range(min_int=min_value, max_int=max_value)
            self.numeric_slider.set_int_value(default_value)

        # Add to Widgets
        self.layout.addWidget(label)
        self.layout.addWidget(self.numeric_slider)
        self.layout.addWidget(spinbox)

        if end_margin:
            _distance = ui_qt.QtWidgets.QLabel()
            _distance.setFixedWidth(end_margin)
            self.layout.addWidget(_distance)

        # Connect
        _func = partial(set_value_from_field, parent=parent, var=var_name, field=self.numeric_slider)
        if float_type:
            self.numeric_slider.doubleValueChanged.connect(_func)
        else:
            self.numeric_slider.intValueChanged.connect(_func)


class HLineWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, label_text=""):
        """
        A custom horizontal line to separate ui sections.

        Args:
            label_text (str, optional): The text to appear in the middle of the QFrames (lines)
                                        If not provided it will become a soline line.
        """
        super(HLineWidget, self).__init__()

        # Create and Add Layout
        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.left_line = ui_qt.QtWidgets.QFrame()
        self.left_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)  # Horizontal line
        self.left_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)  # Optional shado
        self.layout.addWidget(self.left_line, 1)  # Stretch factor of 1 for left line

        # Create the label
        if label_text:
            self.label = ui_qt.QtWidgets.QLabel(label_text)
            self.label.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Minimum)
            self.label.setStyleSheet("color: grey; padding: 0 8px;")  # Add padding for spacing
            self.layout.addWidget(self.label, 0)  # No stretch factor for the label

        self.right_line = ui_qt.QtWidgets.QFrame()
        self.right_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)  # Horizontal line
        self.right_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)  # Optional shado
        self.layout.addWidget(self.right_line, 1)  # Stretch factor of 1 for right line


class MappingTableWidget(ui_qt.QtWidgets.QTableWidget):
    def __init__(self, parent):
        """
        Initialize the mapping table widget.

        Args:
            parent (QWidget): The parent widget.
        """
        super(MappingTableWidget, self).__init__(parent=parent)
        self.view = parent

        self.target_items = []
        columns = ["Status", "Target", "Source", "Method"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

        # Headers
        header_view = ui_qt_utils.QHeaderWithWidgets()
        self.setHorizontalHeader(header_view)
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, ui_qt.QtLib.QHeaderView.ResizeToContents)

        # Context Menus variables
        self._source_context_menu = None
        self._action_set_to_selection = None
        self._source_item_identifier = "source_item"
        self._method_item_identifier = "method_item"

    @staticmethod
    def get_health_score_icon(score_value=-1):
        """
        Gets the icon to display based on the score value.

        Args:
            score_value (int): the retarget link health score value

        Returns:
            str: resource library icon path
        """
        status_icons = {
            0: ui_res_lib.Icon.ui_red_circle,
            1: ui_res_lib.Icon.ui_yellow_circle,
            2: ui_res_lib.Icon.ui_green_circle,
        }

        icon_path = ui_res_lib.Icon.ui_grey_circle
        if score_value in status_icons.keys():
            icon_path = status_icons[score_value]

        return icon_path

    def update_table(self, health_score_dict=None, source_joints=None):
        """Updates mapping table.

        Args:
            health_score_dict (dict, optional): health score dictionary from model.
                                                If None, the function will clear the table.
            source_joints (list): source joint list from the scene.
        """

        # Get scrollbar values
        _scroll_x = self.horizontalScrollBar().value()
        _scroll_y = self.verticalScrollBar().value()

        # Clear table
        self.setRowCount(0)

        if not health_score_dict:
            return

        if not source_joints:
            source_joints = []

        # Populate
        self.target_items = []
        for row, (link_obj, link_score) in enumerate(health_score_dict.items()):

            self.insertRow(row)
            # Health -----------------------------
            _icon_path = self.get_health_score_icon(link_score)
            self.insert_item(
                row=row,
                column=0,
                icon_path=_icon_path,
                icon_size=24,
                data_object=link_score,
            )

            # Target -----------------------------
            link_target_name = link_obj.get_target()
            display_target_name = get_short_display_name(link_target_name)
            target_item = self.insert_item(
                row=row,
                column=1,
                text=display_target_name,
                data_object=link_target_name,
                centered=False,
            )
            self.target_items.append(target_item)

            # Source -----------------------------
            _source_item_list = [["---", ""]]
            # Add source skeleton from scene
            if source_joints:
                _joints_item_list = [[get_short_display_name(j), j] for j in source_joints]
                _source_item_list.extend(_joints_item_list)
            # Insert link source value
            link_source_name = link_obj.get_source()
            display_source_name = link_source_name
            if link_source_name:
                display_source_name = get_short_display_name(link_source_name)
                if display_source_name not in source_joints:
                    _source_item_list.append([display_source_name, link_source_name])
            # Add dropdown widget
            source_widget = ui_qt.QtWidgets.QComboBox()
            source_widget.setWhatsThis(self._source_item_identifier)
            self.setCellWidget(row, 2, source_widget)
            # Fill
            for s_item in _source_item_list:
                source_widget.addItem(s_item[0], s_item[1])
            if link_source_name:
                source_widget.setCurrentText(display_source_name)
            _func_source = partial(
                self.update_model_and_table,
                target_data=link_target_name,
                combo_field=source_widget,
                field_type="source",
            )
            source_widget.currentIndexChanged.connect(_func_source)

            # Set Context Menu for source widget
            source_widget.installEventFilter(source_widget)

            # Method -----------------------------
            link_method = link_obj.get_method()
            available_methods = tools_retargeter_frm.TargetingMethods.get_available_methods()
            method_widget = ui_qt.QtWidgets.QComboBox()
            method_widget.setWhatsThis(self._method_item_identifier)
            for method_name in available_methods:
                method_widget.addItem(method_name, method_name)
            method_widget.setCurrentText(link_method)
            self.setCellWidget(row, 3, method_widget)
            _func_method = partial(
                self.update_model_and_table,
                target_data=link_target_name,
                combo_field=method_widget,
                field_type="method",
            )
            method_widget.currentIndexChanged.connect(_func_method)

        # Attempt to restore the scroll bars values
        try:
            self.horizontalScrollBar().setValue(_scroll_x)
            self.verticalScrollBar().setValue(_scroll_y)
        except Exception:
            pass

    def eventFilter(self, source, event):
        """
        Handle events within the table area, including context menu creation and mouse presses.

        Args:
            source (QObject): The object that received the event.
            event (QEvent): The event to be processed.

        Returns:
            bool: True if the event is handled, otherwise passes the event to the base implementation.
        """

        # Source widget context menu
        if event.type() == ui_qt.QtCore.QEvent.ContextMenu:
            if source.whatsThis() == self._source_item_identifier:
                self._source_context_menu = ui_qt.QtWidgets.QMenu()

                # Source context menu action - Set to selection
                self._action_set_to_selection = ui_qt.QtLib.QtGui.QAction("Set to selection")
                _set_to_selection_func = partial(self.set_source_to_selection, source)
                self._action_set_to_selection.triggered.connect(_set_to_selection_func)

                self._source_context_menu.addAction(self._action_set_to_selection)
                self._source_context_menu.popup(ui_qt.QtGui.QCursor.pos())

        if event.type() == ui_qt.QtCore.QEvent.MouseButtonPress:
            if source.whatsThis() == self._source_item_identifier:
                self.view.controller.select_scene_sources(source)

        if event.type() == ui_qt.QtCore.QEvent.Type.Wheel:
            if source.whatsThis() == self._source_item_identifier or source.whatsThis() == self._method_item_identifier:
                event.ignore()
                return True

        return ui_qt.QtWidgets.QWidget.eventFilter(self, source, event)

    def set_source_to_selection(self, combo_widget):
        """Sets the source combobox widget current text based on the scene selection.

        Args:
            combo_widget (QComboBox): the source widget provided by the action from the context menu.
        """
        import maya.cmds as cmds
        import gt.core.namespace as core_nspace

        _msg_title = "Set Source To Selection"
        selection = cmds.ls(sl=True)
        if not selection:
            _msg_text = "Nothing selected.\n\nPlease select in the scene a valid source joint to set."
            show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="warning")
            return

        sel_object = selection[0]
        if not cmds.nodeType(sel_object) == "joint":
            _msg_text = "Object selected is not a joint.\n\nPlease select in the scene a valid source joint to set."
            show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="warning")
            return

        if self.view.source_namespace:
            _sel_object_namespace = core_nspace.get_namespace(sel_object)
            if _sel_object_namespace != self.view.source_namespace:
                _msg_text = "Selected joint is not part of the source skeleton.\n\nPlease select a valid source joint."
                show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="warning")
                return

        items_in_list = [combo_widget.itemText(i) for i in range(combo_widget.count())]
        sel_object_short = core_naming.get_short_name(sel_object, remove_namespace=True)
        if sel_object_short not in items_in_list:
            _msg_text = "Selected joint is not an item of the list.\n\nPlease select a valid source joint."
            show_message_box(self.view, title=_msg_title, message=_msg_text, icon_type="warning")
            return

        # Set the object as source
        combo_widget.setCurrentText(sel_object_short)

    def update_model_and_table(self, *args, target_data, combo_field, field_type):
        """Updates the project model and refreshes the setup fields in the ui.

        Args:
            target_data (str): target data from the related ui item.
            combo_field (QComboBox): combobox widget to query.
            field_type (str): "source" or "method".
        """
        new_value_from_combo = combo_field.itemData(combo_field.currentIndex())
        link_to_edit = self.view.controller.model.project.get_links_from_target(target_data)
        if len(link_to_edit) > 1:
            logger.warning("The model contains multiple Links with the same Target.")
        link_to_edit = link_to_edit[0]

        # Update TargetingLink
        if field_type == "source":
            link_to_edit.set_source(new_value_from_combo)
        if field_type == "method":
            link_to_edit.set_method(new_value_from_combo)

        # Update Table
        self.view.controller.update_mapping_table()

    def insert_item(
        self,
        row,
        column,
        text=None,
        tooltip=None,
        data_object=None,
        icon_path="",
        icon_size=32,
        editable=False,
        centered=True,
    ):
        """
        Insert an item into the table.

        Args:
            row (int): Row index.
            column (int): Column index.
            text (str): Text to display in the item.
            tooltip (str): Text to use as tooltip.
            data_object: The associated data object.
            icon_path (str): Path to the icon. (If provided, text is ignored)
            icon_size (int): Icon size, one value, square. 32 by default.
            editable (bool): Whether the item is editable.
            centered (bool): Whether the text should be centered.
        """
        item = ui_qt.QtWidgets.QTableWidgetItem(text)
        item.setData(ui_qt.QtLib.ItemDataRole.UserRole, data_object)
        if tooltip:
            item.setToolTip(tooltip)

        if icon_path != "":
            icon = ui_qt.QtGui.QIcon(icon_path)
            icon_label = ui_qt.QtWidgets.QLabel()
            if tooltip:
                icon_label.setToolTip(tooltip)
            icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
            icon_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            self.setCellWidget(row, column, icon_label)
            return

        if centered:
            item.setTextAlignment(ui_qt.QtLib.AlignmentFlag.AlignHCenter | ui_qt.QtLib.AlignmentFlag.AlignVCenter)

        if not editable:
            item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)

        self.setItem(row, column, item)
        return item

    def select_target_items(self, target_names=None):
        """Selects the target items that match the target name in the given target_list.

        Args:
            target_names (list): long-absolute names that match the data value of the target item.
        """
        if not target_names:
            return
        if not isinstance(target_names, list):
            return

        for item in self.target_items:
            item_data = item.data(ui_qt.QtLib.ItemDataRole.UserRole)
            if item_data in target_names:
                item.setSelected(True)
            else:
                item.setSelected(False)


class DefinitionOptionsWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Retarget definition setup custom option checkboxes.
        Initialize the custom option checkboxes for retarget definition setup.

        Sets up a vertical layout containing checkboxes for various options, with default values:
        - Store User Defined Attrs
        - Reference Rig
        - Delete Source After Retarget
        - Fallback With Short Name

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)
        self.view = parent

        self.user_defined_attr = True
        self.reference_rig = True
        self.delete_source = False
        self.short_name_fallback = True

        # Name: Var name
        self.option_dict = {
            "Store User Defined Attrs": "user_defined_attr",
            "Reference Rig": "reference_rig",
            "Delete Source After Retarget": "delete_source",
            "Fallback With Short Name": "short_name_fallback",
        }
        self.option_list = []

        self.layout = ui_qt.QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        for opt_text, opt_var in self.option_dict.items():
            # Create Checkboxes
            _check_status = getattr(self, opt_var)
            _check_widget = CheckBoxWidget(
                self,
                var_name=opt_var,
                nice_name=opt_text,
                checked=_check_status,
                label_width=200,
            )
            self.layout.addWidget(_check_widget)
            self.option_list.append(_check_widget)

    def get_user_defined_attr(self):
        """Gets the status of the user defined attr checkbox widget.

        Returns:
            bool: status of the checkbox
        """
        return self.user_defined_attr

    def update_values(self):
        """Updates the status of the checkbox widgets from model definition."""
        _definition = self.view.controller.model.project
        for i, (field_text, field_var) in enumerate(self.option_dict.items()):
            if hasattr(_definition, field_var):
                _definition_status = getattr(_definition, field_var)
                self.option_list[i].checkbox.setChecked(_definition_status)

    def update_definition(self):
        """Updates model definition from the status of the checkbox widgets."""
        _definition = self.view.controller.model.project
        for i, (field_text, field_var) in enumerate(self.option_dict.items()):
            _option_value = getattr(self, field_var)
            if hasattr(_definition, field_var):
                setattr(_definition, field_var, _option_value)


class AddonSceneOptionsWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Initialize the Retarget Definition Addon Scene Options Widget.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)
        import gt.tools.retargeter.addon_scene_options as addon_scene_opts

        self.view = parent
        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(10, 10, 0, 0)
        self.layout.setSpacing(50)
        self.setLayout(self.layout)

        self.left_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(0)
        self.right_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)

        # Initialize matching class variables to separate
        # the update of the model from the update of the widget.
        self.linear_unit = "centimeter"
        self.angular_unit = "degree"
        self.frame_rate = "30fps"
        self.multi_sample = True
        self.multi_sample_count = 8
        self.persp_clip_plane_near = 1
        self.persp_clip_plane_far = 10000.0
        self.display_textures = True
        self.playback_frame_start_floor = True
        self.playback_frame_end_ceil = True
        self.animation_frame_start_floor = True
        self.animation_frame_end_ceil = True

        # Checkboxes
        self.option_list = []
        self.option_boxes_dict = {
            "Multi Sample": "multi_sample",
            "Display Textures": "display_textures",
            "Play Frame Start Floor": "playback_frame_start_floor",
            "Play Frame End Ceil": "playback_frame_end_ceil",
            "Anim Frame Start Floor": "animation_frame_start_floor",
            "Anim Frame End Ceil": "animation_frame_end_ceil",
        }

        # Init widgets
        _left_label_width = 140
        _option_list = ["millimeter", "centimeter", "meter", "kilometer", "inch", "foot", "yard", "mile"]
        self.linear_unit_widget = DropDownWidget(
            self,
            var_name="linear_unit",
            nice_name="Linear Unit",
            option_list=_option_list,
            default_option=self.linear_unit,
            add_none=False,
            label_width=_left_label_width,
        )
        self.angular_unit_widget = DropDownWidget(
            self,
            var_name="angular_unit",
            nice_name="Angular Unit",
            option_list=["degree", "radian"],
            default_option=self.angular_unit,
            add_none=False,
            label_width=_left_label_width,
        )
        _option_list = [
            "23.976fps",
            "24fps",
            "25fps",
            "29.97fps",
            "30fps",
            "47.952fps",
            "48fps",
            "50fps",
            "59.94fps",
            "60fps",
        ]
        self.frame_rate_widget = DropDownWidget(
            self,
            var_name="frame_rate",
            nice_name="Frame Rate",
            option_list=_option_list,
            default_option=self.frame_rate,
            add_none=False,
            label_width=_left_label_width,
        )
        self.multi_sample_widget = NumericSliderWidget(
            self,
            var_name="multi_sample_count",
            nice_name="Multi Sample Count",
            min_value=1,
            max_value=10,
            default_value=8,
            label_width=_left_label_width,
        )
        self.clip_near_widget = NumericSliderWidget(
            self,
            var_name="persp_clip_plane_near",
            nice_name="Persp Clip Plane Near",
            min_value=0.001,
            max_value=100.000,
            default_value=1.000,
            float_type=True,
            float_precision=3,
            label_width=_left_label_width,
        )
        self.clip_far_widget = NumericSliderWidget(
            self,
            var_name="persp_clip_plane_far",
            nice_name="Persp Clip Plane Far",
            min_value=1,
            max_value=100000.0,
            default_value=10000.0,
            float_type=True,
            float_precision=1,
            label_width=_left_label_width,
        )
        for opt_text, opt_var in self.option_boxes_dict.items():
            _check_status = getattr(self, opt_var)
            _checkbox_wdg = CheckBoxWidget(
                self,
                var_name=opt_var,
                nice_name=opt_text,
                checked=_check_status,
                label_width=250,
            )
            self.option_list.append(_checkbox_wdg)

        # Populate layout
        self.left_layout.addWidget(self.linear_unit_widget)
        self.left_layout.addWidget(self.angular_unit_widget)
        self.left_layout.addWidget(self.frame_rate_widget)
        self.left_layout.addWidget(self.multi_sample_widget)
        self.left_layout.addWidget(self.clip_near_widget)
        self.left_layout.addWidget(self.clip_far_widget)
        self.left_layout.addStretch()
        [self.right_layout.addWidget(wdg) for wdg in self.option_list]
        self.right_layout.addStretch()

    def update_values(self):
        """Updates the status of the checkbox widgets from model definition."""
        _addon_so = self.view.controller.model.project.get_addon_scene_options()

        # apply scene options
        try:
            _addon_so.apply_addon()
        except Exception as e:
            logger.warning(f"Failed to apply scene options. Issue: {e}")

        # Combo-boxes
        self.linear_unit_widget.combobox.setCurrentText(_addon_so.scene_options["linear_unit"])
        self.angular_unit_widget.combobox.setCurrentText(_addon_so.scene_options["angular_unit"])
        self.frame_rate_widget.combobox.setCurrentText(_addon_so.scene_options["frame_rate"])
        # Numeric sliders
        self.multi_sample_widget.numeric_slider.set_int_value(_addon_so.scene_options["multi_sample_count"])
        self.clip_near_widget.numeric_slider.set_double_value(_addon_so.scene_options["persp_clip_plane_near"])
        self.clip_far_widget.numeric_slider.set_double_value(_addon_so.scene_options["persp_clip_plane_far"])
        # Check-boxes
        for i, (field_text, field_var) in enumerate(self.option_boxes_dict.items()):
            if field_var in _addon_so.scene_options.keys():
                _addon_status = _addon_so.scene_options[field_var]
                self.option_list[i].checkbox.setChecked(_addon_status)

    def update_definition(self):
        """Updates model definition from the status of the checkbox widgets."""
        _addon_so = self.view.controller.model.project.get_addon_scene_options()
        # Combo-boxes
        _addon_so.scene_options["linear_unit"] = self.linear_unit
        _addon_so.scene_options["angular_unit"] = self.angular_unit
        _addon_so.scene_options["frame_rate"] = self.frame_rate
        # Numeric sliders
        _addon_so.scene_options["multi_sample_count"] = self.multi_sample_count
        _addon_so.scene_options["persp_clip_plane_near"] = self.persp_clip_plane_near
        _addon_so.scene_options["persp_clip_plane_far"] = self.persp_clip_plane_far
        # Check-boxes
        for i, (field_text, field_var) in enumerate(self.option_boxes_dict.items()):
            if field_var in _addon_so.scene_options.keys():
                _option_value = getattr(self, field_var)
                _addon_so.scene_options[field_var] = _option_value


class AddonSourceSetupWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Initialize the AddonSourceSetupWidget for retarget definition scene options.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)
        import gt.tools.retargeter.addon_scene_options as addon_scene_opts

        self.view = parent
        self.layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(10, 10, 0, 0)
        self.layout.setSpacing(50)
        self.setLayout(self.layout)

        self.left_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(4)
        self.right_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)

        self.transform_name = None
        self.comparison_loc_name = None
        self.imported_is_children = True
        self.deactivate_meshes_trans_inheritance = True

        _left_label_width = 140
        self.transform_name_widget = TextBrowseFileWidget(
            self,
            var_name="transform_name",
            nice_name="Main Transform",
            browse=False,
            label_width=_left_label_width,
        )
        self.transform_name_widget.text_field.setReadOnly(True)

        # read only icon
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_read_only)
        _read_only_label = ui_qt.QtWidgets.QLabel()
        _read_only_label.setPixmap(_icon.pixmap(24, 24))
        _read_only_label.setToolTip("Read-only field")
        self.transform_name_widget.layout.addWidget(_read_only_label)

        self.comp_loc_name_widget = TextBrowseFileWidget(
            self,
            var_name="comparison_loc_name",
            nice_name="Comparison Loc",
            browse=False,
            label_width=_left_label_width,
        )
        self.comp_loc_name_widget.text_field.setReadOnly(True)

        # read only icon
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_read_only)
        _read_only_label = ui_qt.QtWidgets.QLabel()
        _read_only_label.setPixmap(_icon.pixmap(24, 24))
        _read_only_label.setToolTip("Read-only field")
        self.comp_loc_name_widget.layout.addWidget(_read_only_label)

        self.deactivate_inheritance_widget = CheckBoxWidget(
            self,
            var_name="deactivate_meshes_trans_inheritance",
            nice_name="Disable Meshes Inheritance",
            checked=self.deactivate_meshes_trans_inheritance,
        )

        # group skeleton members
        self.grp_skeleton_widget = ui_qt.QtWidgets.QGroupBox("Source joints:")
        skeleton_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.grp_skeleton_widget.setLayout(skeleton_layout)
        self.grp_skeleton_widget.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Preferred, ui_qt.QtWidgets.QSizePolicy.Expanding
        )

        self.skeleton_list = ui_qt.QtWidgets.QListWidget()
        self.skeleton_list.setMinimumSize(20, 20)
        self.skeleton_list.setSpacing(1)
        skeleton_layout.addWidget(self.skeleton_list)

        self.left_layout.addWidget(self.transform_name_widget)
        self.left_layout.addWidget(self.comp_loc_name_widget)
        self.left_layout.addWidget(self.deactivate_inheritance_widget)
        self.left_layout.addWidget(self.grp_skeleton_widget)

        # group transform children
        self.grp_transform_widget = ui_qt.QtWidgets.QGroupBox("Transform Children:")
        transform_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.grp_transform_widget.setLayout(transform_layout)
        self.grp_transform_widget.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Preferred, ui_qt.QtWidgets.QSizePolicy.Expanding
        )

        self.imported_is_children_widget = CheckBoxWidget(
            self,
            var_name="imported_is_children",
            nice_name="Imported Is Children",
            checked=self.imported_is_children,
        )
        self.imported_is_children_widget.checkbox.stateChanged.connect(self.update_visibility_children_panel)

        # Selected Children Panel
        self.selected_children_widget = ui_qt.QtWidgets.QWidget()
        self.selected_children_widget.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Preferred, ui_qt.QtWidgets.QSizePolicy.Expanding
        )
        sel_children_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.selected_children_widget.setLayout(sel_children_layout)

        self.load_children_btn = ui_qt.QtWidgets.QPushButton("Load Children From Selection")
        self.load_children_btn.clicked.connect(self.load_children_from_selection)

        self.sel_children_list = ui_qt.QtWidgets.QListWidget()
        self.sel_children_list.setMinimumSize(20, 20)
        self.sel_children_list.setSpacing(1)
        sel_children_layout.addWidget(self.load_children_btn)
        sel_children_layout.addWidget(self.sel_children_list)

        self.children_spacer = ui_qt.QtWidgets.QSpacerItem(
            20, 40, ui_qt.QtWidgets.QSizePolicy.Minimum, ui_qt.QtWidgets.QSizePolicy.Expanding
        )

        transform_layout.addWidget(self.imported_is_children_widget)
        transform_layout.addWidget(self.selected_children_widget)
        transform_layout.addItem(self.children_spacer)
        self.right_layout.addWidget(self.grp_transform_widget)

        # Update children panel
        self.update_visibility_children_panel()

    def load_children_from_selection(self):
        """Calls Addon Source Setup set_children_from_selection and loads the
        result into the related list widget."""
        _addon_source = self.view.controller.model.project.get_addon_source_setup()
        _addon_source.set_children_from_selection()
        _children_list = _addon_source.get_children()
        self.update_children_list(children_list=_children_list)

    def update_children_list(self, children_list=None):
        """
        Update the Source Setup children list widget with the given items.

        Args:
            children_list (list, optional): List of child items to display. Each item is
                expected to be a string or an object convertible to a short name.
                If None or empty, the list will show a placeholder "<Empty>" item.
        """
        self.sel_children_list.clear()
        if children_list:
            for child in children_list:
                _child_name = core_naming.get_short_name(child)
                item = ui_qt.QtWidgets.QListWidgetItem(_child_name)
                item.setData(self.view._user_role, child)
                self.sel_children_list.addItem(item)
        else:
            item = ui_qt.QtWidgets.QListWidgetItem("<Empty>")
            self.sel_children_list.addItem(item)

    def update_visibility_children_panel(self):
        """Applies imported_is_children status."""
        if not self.imported_is_children:
            self.selected_children_widget.setMinimumSize(20, 20)
            self.selected_children_widget.setMaximumSize(9999, 9999)
            self.children_spacer.changeSize(0, 0)
        else:
            self.selected_children_widget.setFixedHeight(0)
            self.children_spacer.changeSize(
                20, 40, ui_qt.QtWidgets.QSizePolicy.Minimum, ui_qt.QtWidgets.QSizePolicy.Expanding
            )
        self.update_children_list()

    def update_values(self):
        """Updates the values of the widgets from model definition."""
        self.view.controller.model.project.retarget_refresh_addons_data()
        _addon_source = self.view.controller.model.project.get_addon_source_setup()
        try:
            # Check source namespace
            import maya.cmds as cmds

            _source_namespace = self.view.controller.model.get_source_namespace()
            _existing_source = cmds.ls(f"*{_source_namespace}:*")
        except Exception as e:
            logger.debug(f"Cannot read Source Data from scene: {e}")

        self.transform_name_widget.text_field.setText(_addon_source.transform_name)
        self.comp_loc_name_widget.text_field.setText(_addon_source._comparison_matrix_loc)
        self.skeleton_list.clear()

        if _addon_source.skeleton_pose:
            for k in _addon_source.skeleton_pose.keys():
                _joint_name = core_naming.get_short_name(k)
                item = ui_qt.QtWidgets.QListWidgetItem(_joint_name)
                item.setData(self.view._user_role, k)
                self.skeleton_list.addItem(item)
        else:
            _warning = "<Addon empty. Please Import/Reload to initialize the Source Setup caches.>"
            item = ui_qt.QtWidgets.QListWidgetItem(_warning)
            self.skeleton_list.addItem(item)

        # Checkboxes
        self.imported_is_children_widget.checkbox.setChecked(_addon_source.imported_is_children)
        self.deactivate_inheritance_widget.checkbox.setChecked(_addon_source.deactivate_meshes_trans_inheritance)

        # Children list
        if _addon_source.imported_is_children:
            # Clear data in model
            _addon_source.transform_children = []

        # Update children list
        _definition_children = None
        if len(_addon_source.transform_children) > 0:
            _definition_children = _addon_source.transform_children
        self.update_children_list(children_list=_definition_children)

    def update_definition(self):
        """Updates model definition from the UI widgets."""
        _addon_source = self.view.controller.model.project.get_addon_source_setup()
        # Combo-boxes
        _addon_source.imported_is_children = self.imported_is_children
        _addon_source.deactivate_meshes_trans_inheritance = self.deactivate_meshes_trans_inheritance
        # Children list already updated in the model when filled


class AddonPostBakeWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Initialize the Addon Post Bake Widget for retarget definitions.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)

        self.view = parent
        self.active = False
        self.switch_combinations = []
        self.combo_direction = None
        self.combo_switch_type = None

        self.layout = ui_qt.QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        # Active checkbox ----------------------------------------------------------
        self.active_check_box = ui_qt.QtWidgets.QCheckBox("Active")
        self.active_check_box.setChecked(self.active)
        self.active_check_box.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed)
        _btn_func = partial(set_value_from_field, parent=self, var="active", field=self.active_check_box)
        self.active_check_box.stateChanged.connect(_btn_func)
        self.layout.addWidget(self.active_check_box)

        # Add switch combination ---------------------------------------------------
        add_combo_line = HLineWidget(label_text="Add Switch Combination")
        self.layout.addWidget(add_combo_line)

        add_combo_layout = ui_qt.QtWidgets.QHBoxLayout()
        add_combo_layout.setContentsMargins(10, 0, 10, 0)
        add_combo_layout.setSpacing(20)
        self.layout.addLayout(add_combo_layout)

        self.direction_combo_widget = DropDownWidget(
            self,
            var_name="combo_direction",
            nice_name="Direction",
            tooltip="Direction of the switch combination",
        )
        self.direction_combo_widget.label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )

        self.switch_type_combo_widget = DropDownWidget(
            self,
            var_name="combo_switch_type",
            nice_name="Switch Type",
            tooltip="Type of the switch combination",
        )
        self.switch_type_combo_widget.label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )

        self.add_combo_btn = ui_qt.QtWidgets.QPushButton()
        self.add_combo_btn.setFixedWidth(28)
        self.add_combo_btn.setToolTip("Add a new switch combination")
        self.add_combo_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_plus))
        self.add_combo_btn.clicked.connect(self.add_switch_combination)

        add_combo_layout.addWidget(self.direction_combo_widget)
        add_combo_layout.addWidget(self.switch_type_combo_widget)
        add_combo_layout.addWidget(self.add_combo_btn)

        # Initiate dropdowns
        self.direction_combo_widget.combobox.clear()
        self.direction_combo_widget.populate_list(
            core_rig_switch.SwitchDirections.get_switch_directions(),
            add_none=False,
        )
        self.switch_type_combo_widget.combobox.clear()
        self.switch_type_combo_widget.populate_list(
            core_rig_switch.get_available_switch_types(),
            add_none=False,
        )

        # Switch combination list -------------------------------------------------
        combo_list_layout = ui_qt.QtWidgets.QHBoxLayout()
        combo_list_layout.setContentsMargins(10, 0, 10, 0)
        combo_list_layout.setSpacing(20)

        combo_list_line = HLineWidget(label_text="Switch Combination List")
        self.layout.addWidget(combo_list_line)
        self.layout.addLayout(combo_list_layout)

        self.switch_combo_list = ui_qt.QtWidgets.QListWidget()
        self.switch_combo_list.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.ExtendedSelection)
        self.switch_combo_list.setMinimumSize(20, 20)
        self.switch_combo_list.setSpacing(1)
        combo_list_layout.addWidget(self.switch_combo_list)

        # switch combinations options
        combo_list_options_layout = ui_qt.QtWidgets.QVBoxLayout()
        combo_list_options_layout.setContentsMargins(0, 0, 0, 0)
        combo_list_options_layout.setSpacing(10)
        combo_list_layout.addLayout(combo_list_options_layout)

        self.delete_selected_combo_btn = ui_qt.QtWidgets.QPushButton("Delete selected combinations")
        # self.delete_selected_combo_btn.setFixedWidth(28)
        self.delete_selected_combo_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        self.delete_selected_combo_btn.clicked.connect(self.delete_selected_switch_combo)
        combo_list_options_layout.addWidget(self.delete_selected_combo_btn)
        combo_list_options_layout.addStretch()

        # Initiate list
        self.update_switch_combo_list()

    def update_switch_combo_list(self, switch_combo_list=None):
        """
        Update the switch combination list widget.
        Args:
            switch_combo_list (list): list of switch combo dictionaries, keys are "direction" and "switch_type".
                                      None by default, if None it clears the list.
                                      Example: [{"direction": "fk_to_ik", "switch_type": "biped_right_arm"}]
        """
        self.switch_combo_list.clear()

        if switch_combo_list:
            for switch_combo_dict in switch_combo_list:
                combo_direction = switch_combo_dict.get(core_rig_switch.SwitchCombination.direction_key)
                combo_switch_type = switch_combo_dict.get(core_rig_switch.SwitchCombination.switch_type_key)
                # Format combo data
                combo_string = f"{combo_direction} - {combo_switch_type}"

                # Add combination to the list
                item = ui_qt.QtWidgets.QListWidgetItem(combo_string)
                item.setData(ui_qt.QtLib.ItemDataRole.UserRole, switch_combo_dict)
                # item.setCheckState(ui_qt.QtCore.Qt.Checked)
                self.switch_combo_list.addItem(item)

    def delete_selected_switch_combo(self):
        """Deletes selected items from the switch combinations list widget."""
        selected_combo_items = self.switch_combo_list.selectedItems()
        if not selected_combo_items:
            return

        for combo_item in selected_combo_items:
            self.switch_combo_list.takeItem(self.switch_combo_list.row(combo_item))

    def get_switch_combinations_from_list(self):
        """
        Gets the combination dictionaries from the list widget.
        Returns:
            list: list of switch combinations dictionaries.
                  Example: [{"direction": "fk_to_ik", "switch_type": "biped_right_arm"}]
        """
        switch_combinations = []
        for i in range(self.switch_combo_list.count()):
            switch_combinations.append(self.switch_combo_list.item(i).data(ui_qt.QtLib.ItemDataRole.UserRole))
        return switch_combinations

    def add_switch_combination(self):
        """Adds a new switch combination to the list based on the selected options in the dropdown widgets."""
        current_direction = self.direction_combo_widget.combobox.currentText()
        current_switch_type = self.switch_type_combo_widget.combobox.currentText()
        combo_obj = core_rig_switch.SwitchCombination(direction=current_direction, switch_type=current_switch_type)
        new_combo_dict = combo_obj.get_switch_combination_dict()

        if not new_combo_dict:
            return

        switch_combo_list = []
        current_combinations = self.get_switch_combinations_from_list()
        if current_combinations:

            # Check unique combination
            if new_combo_dict in current_combinations:
                _msg_text = "The new switch combination already exists in the list."
                show_message_box(self.view, title="Post Bake", message=_msg_text, icon_type="warning")
                return

            switch_combo_list.extend(current_combinations)
        switch_combo_list.append(new_combo_dict)

        # Update combinations list widget
        self.update_switch_combo_list(switch_combo_list=switch_combo_list)

    def update_values(self):
        """Updates the status of the checkbox widgets from model definition."""
        _addon_pb = self.view.controller.model.project.get_addon_post_bake()
        self.active = _addon_pb.active
        self.switch_combinations = _addon_pb.switch_combinations
        self.active_check_box.setChecked(self.active)
        self.update_switch_combo_list(switch_combo_list=self.switch_combinations)

    def update_definition(self):
        """Updates model definition from the status of the checkbox widgets."""
        _addon_pb = self.view.controller.model.project.get_addon_post_bake()
        _addon_pb.active = self.active
        _addon_pb.switch_combinations = self.get_switch_combinations_from_list()


class AddonPythonScriptWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Initialize the Addon Post Bake Widget for retarget definitions.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)

        self.view = parent
        self.active = False
        self.code = ""
        self.execution_order = tools_retargeter_frm.TargetingAddon.Order.post_retarget

        self._script_previous_name = None

        self.layout = ui_qt.QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        # Python Script list and commands ------------------------------------------------------
        _layout = ui_qt.QtWidgets.QHBoxLayout()

        self.script_list_wdg = ui_qt.QtWidgets.QListWidget()
        self.script_list_wdg.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.SingleSelection)
        self.script_list_wdg.setMinimumSize(20, 40)
        self.script_list_wdg.setMaximumHeight(126)
        self.script_list_wdg.setSpacing(1)
        self.script_list_wdg.itemSelectionChanged.connect(self.refresh_script_editor)
        self.script_list_wdg.itemDoubleClicked.connect(self.rename_script_previous_name)
        self.script_list_wdg.itemChanged.connect(self.rename_script_new_name)

        _script_option_layout = ui_qt.QtWidgets.QVBoxLayout()
        # Add New Script Button
        self.add_script_button = ui_qt.QtWidgets.QPushButton("New Python Script")
        self.add_script_button.clicked.connect(self.add_new_python_script)
        _script_option_layout.addWidget(self.add_script_button)

        # Delete Script Button
        self.delete_script_button = ui_qt.QtWidgets.QPushButton("Delete Selected Python Script")
        self.delete_script_button.clicked.connect(self.remove_python_script_by_selection)
        _script_option_layout.addWidget(self.delete_script_button)

        # Save Button
        save_btn = ui_qt.QtWidgets.QPushButton("Save Definition (Script Only)")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        _tooltip = (
            "Write data to the current selected definition.\n"
            "Used to update the script without accidentally affecting the link data (controls and joints)"
        )
        save_btn.setToolTip(_tooltip)
        save_btn.clicked.connect(self.save_definition_file)
        _script_option_layout.addWidget(save_btn)

        # Load Button
        load_btn = ui_qt.QtWidgets.QPushButton("Import External File")
        load_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        load_btn.setToolTip("Load a script from a file.")
        load_btn.clicked.connect(self.on_load_clicked)
        _script_option_layout.addWidget(load_btn)

        _layout.addWidget(self.script_list_wdg)
        _layout.addLayout(_script_option_layout)
        self.layout.addLayout(_layout)

        # Active checkbox and Buttons ----------------------------------------------------------
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.layout.addLayout(_layout)
        self.active_check_box = ui_qt.QtWidgets.QCheckBox("Active")
        self.active_check_box.setChecked(self.active)
        self.active_check_box.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed)
        self.active_check_box.stateChanged.connect(self.on_active_changed)
        _layout.addWidget(self.active_check_box)

        # Run Button
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

        # Order Combobox
        _label = "Order:"
        label_order = ui_qt.QtWidgets.QLabel(_label)
        label_order.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        self.order_combobox = ui_qt_utils.ColorTextComboBox()
        self.order_combobox.setFixedHeight(30)
        order_list = tools_retargeter_frm.TargetingAddon.Order.get_available_order_items()
        self.order_combobox.addItems(order_list)
        _layout.addWidget(label_order)
        _layout.addWidget(self.order_combobox)
        self.order_combobox.currentTextChanged.connect(self.on_combobox_order_changed)

        # Python Edit
        self.python_edit = ui_qt.QtWidgets.QTextEdit()
        self.python_edit.textChanged.connect(self.on_python_code_changed)
        self.layout.addWidget(self.python_edit)

        import gt.ui.syntax_highlighter as ui_syntax_highlighter

        self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())

    def update_values(self):
        """Updates the python script interface."""
        self.refresh_script_list()
        self.refresh_script_editor()

    def refresh_script_list(self):
        """Refreshes the script list section."""
        _addon_scripts = self.view.controller.model.project.get_addon_python_script()

        self.script_list_wdg.clear()
        for _addon in _addon_scripts:
            _script_name = _addon.name
            self.add_item_script_list(_script_name)
        self.select_last_item_script_list()

    def refresh_script_editor(self):
        """Refreshes the script editor section."""
        _addon_ps = self.get_current_script()
        if not _addon_ps:
            return

        self.order_combobox.blockSignals(True)
        self.active_check_box.blockSignals(True)
        self.python_edit.blockSignals(True)

        self.active = _addon_ps.active
        self.code = _addon_ps.code
        self.execution_order = _addon_ps.execution_order
        self.active_check_box.setChecked(self.active)
        self.python_edit.setText(self.code)
        # Execution Order
        _index = self.order_combobox.findText(self.execution_order)
        if _index == -1:  # Add missing items (just in case)
            self.order_combobox.addItem(self.execution_order)
            _index = self.order_combobox.findText(self.execution_order)
            logger.warning(f'Order "{self.execution_order}" was not available as an order but was force added.')
        self.order_combobox.setCurrentIndex(_index)

        self.python_edit.blockSignals(False)
        self.active_check_box.blockSignals(False)
        self.order_combobox.blockSignals(False)

    def update_definition(self):
        """
        Updates model definition from stored values.
        """
        _addon_ps = self.get_current_script()
        if not _addon_ps:
            return

        _addon_ps.active = self.active
        _addon_ps.code = self.code
        _addon_ps.execution_order = self.execution_order

    def save_definition_file(self):
        """
        Updates model definition from stored values and writes it to
        """
        _controller = self.view.controller
        _project = self.view.controller.model.project
        _definition_path = _controller.get_edit_definition_path()
        _file_name = os.path.basename(_definition_path)

        if not _definition_path:
            _msg_text = "Definition not selected. Cannot retrieve the file and save."
            logger.warning(_msg_text)
            show_message_box(self.view, title="Warning", message=_msg_text, icon_type="warning")
            return

        # Get the project dict
        _definition_dict = _project.get_definition_as_dict()

        # Save Definition json file
        # -- If already present, make it modifiable
        import gt.core.io as core_io

        if _definition_path and os.path.exists(_definition_path):
            core_io.set_file_permission_modifiable(_definition_path)
        _file_path = core_io.write_json(path=_definition_path, data=_definition_dict)
        if os.path.isfile(_file_path):
            _msg_text = (
                f"Successfully saved python data to current retarget definition."
                f'\n\nUpdated JSON file: "{_file_name}"'
            )
            show_message_box(self.view, title="Success", message=_msg_text, icon_type="info")

        logging.info(f'Python script data was written to "{_definition_path}".')

    def add_new_python_script(self):
        """Adds a new python script."""
        self.add_item_script_list()
        self.select_last_item_script_list()
        self.refresh_script_editor()

    def add_item_script_list(self, script_name=None):
        """Adds the script item to the list.
        Args:
            script_name (str): name of the python script.
        Returns:
            script_item (QListWidgetItem)
        """
        self.script_list_wdg.blockSignals(True)
        if not script_name:
            script_name = self.get_unique_script_name()
            # instantiate a new addon script
            self.view.controller.model.project.add_addon_python_script(script_name=script_name)

        for i in range(self.script_list_wdg.count()):
            item_text = self.script_list_wdg.item(i).text()
            if item_text == script_name:
                return self.script_list_wdg.item(i)

        script_item = ui_qt.QtWidgets.QListWidgetItem(script_name)
        script_item.setFlags(script_item.flags() | ui_qt.QtCore.Qt.ItemIsEditable)
        script_item.setSizeHint(ui_qt.QtCore.QSize(0, 25))

        self.script_list_wdg.addItem(script_item)
        self.script_list_wdg.blockSignals(False)
        return script_item

    def remove_python_script_by_selection(self):
        """Removes the selected python script."""
        if not self.script_list_wdg.currentItem():
            logger.error("Cannot remove the python script. Nothing selected.")
            return

        self.script_list_wdg.blockSignals(True)
        script_name = self.script_list_wdg.currentItem().text()
        self.view.controller.model.project.remove_addon_python_script_by_name(script_name)
        self.script_list_wdg.blockSignals(False)
        self.update_values()

    def get_unique_script_name(self):
        """
        Gets a unique python script name.
        Returns
            script_name (str)
        """
        script_name = None
        original_name = False
        suffix_number = 1
        current_names = [self.script_list_wdg.item(i).text() for i in range(self.script_list_wdg.count())]
        while not original_name:
            _suffix = str(suffix_number)
            if suffix_number == "1":
                _suffix = ""
            script_name = f"Python Script{_suffix}"
            if script_name in current_names:
                suffix_number += 1
            else:
                original_name = True
        return script_name

    def on_button_run_code_clicked(self):
        """
        Executes the Python code from the text editor when the 'Run Code' button is clicked.
        """
        import gt.utils.system as utils_sys

        utils_sys.execute_python_code(code=self.python_edit.toPlainText(), import_cmds=True)

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

        import gt.core.io as core_io

        content = core_io.read_data(path=file_path)

        if content is not None:
            self.python_edit.setText(content)
            logging.info(f"Imported external file as python script: {file_path}")
        else:
            logging.error(f"Failed to read script from {file_path}")

    def on_combobox_order_changed(self):
        """Updates execution order data according to what is selected in the combobox."""
        self.execution_order = self.order_combobox.currentText()
        _addon_ps = self.get_current_script()
        if not _addon_ps:
            return

        _addon_ps.execution_order = self.execution_order
        logging.info(f'Execution order changed to : "{self.execution_order}".')

    def on_active_changed(self):
        """Updates active data according to what is checked by the user."""
        self.active = self.active_check_box.isChecked()
        _addon_ps = self.get_current_script()
        if not _addon_ps:
            return

        _addon_ps.active = self.active

    def on_python_code_changed(self):
        """Updates code data according to what is prompted by the user."""
        self.code = self.python_edit.toPlainText()
        _addon_ps = self.get_current_script()
        if not _addon_ps:
            return

        _addon_ps.code = self.code

    def select_last_item_script_list(self):
        """Selects the last item in the list."""
        self.script_list_wdg.blockSignals(True)
        for i in range(self.script_list_wdg.count()):
            if i == self.script_list_wdg.count() - 1:
                self.script_list_wdg.item(i).setSelected(True)
            else:
                self.script_list_wdg.item(i).setSelected(False)
        self.script_list_wdg.blockSignals(False)

    def get_current_script(self):
        """Gets the selected script from the list widget to use.
        Returns:
            current_script_addon (AddonPythonScript class): the current script to use.
        """
        scripts_selected = self.script_list_wdg.selectedItems()
        if not scripts_selected:
            self.select_last_item_script_list()
            scripts_selected = self.script_list_wdg.selectedItems()
        if scripts_selected:
            _script_addon_list = self.view.controller.model.project.get_addon_python_script()
            script_item_name = scripts_selected[0].text()
            for _script in _script_addon_list:
                if script_item_name == _script.name:
                    return _script

    def get_script_addon_by_name(self, script_name):
        """Gets the script addon that has the supplied script name.
        Args:
            script_name (str): name of the subject used to find the related model.
        Returns:
            script_addon (AddonPythonScript class) or None: the related script addon.
        """
        _script_addon_list = self.view.controller.model.project.get_addon_python_script()
        for _script in _script_addon_list:
            if script_name == _script.name:
                return _script

    def rename_script_previous_name(self):
        """Stores the name of the script when the text field is clicked."""
        if not self.script_list_wdg.currentItem():
            return
        self._script_previous_name = self.script_list_wdg.currentItem().text()

    def rename_script_new_name(self):
        """Edits the script text fields when a new string is prompted by the user."""
        if not self._script_previous_name:
            return
        if not self.script_list_wdg.currentItem():
            return

        script_name = self.script_list_wdg.currentItem().text()
        if script_name == self._script_previous_name:
            return
        if not script_name:
            self.script_list_wdg.blockSignals(True)
            self.script_list_wdg.currentItem().setText(self._script_previous_name)
            self.script_list_wdg.blockSignals(False)
            return

        _script_addon_list = self.view.controller.model.project.get_addon_python_script()
        for _addon in _script_addon_list:
            _addon_script_name = _addon.name
            if script_name == _addon_script_name:
                self.script_list_wdg.blockSignals(True)
                self.script_list_wdg.currentItem().setText(self._script_previous_name)
                self.script_list_wdg.blockSignals(False)
                logger.warning("Rename skipped. Another python script in the list has the new chosen name.")
                return

        addon_to_rename = None
        for _addon in _script_addon_list:
            if self._script_previous_name == _addon.name:
                addon_to_rename = _addon
                break
        if addon_to_rename:
            addon_to_rename.name = script_name
            logger.info(f"Renamed python script '{self._script_previous_name}' to '{script_name}'.")
        else:
            error_message = (
                f"No data found for the selected python script '{self._script_previous_name}'. Corrupted list.\n"
                "Please delete and re-add the items."
            )
            logger.error(error_message)


class AddonPatchesWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Initialize the Patches Widget for retarget definitions.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)

        self.view = parent

        self.layout = ui_qt.QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        # Patches list
        self.patch_list = ui_qt.QtWidgets.QListWidget()
        self.patch_list.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.NoSelection)
        self.patch_list.setMinimumSize(20, 20)
        self.patch_list.setSpacing(1)
        self.layout.addWidget(self.patch_list)

        # Save Button
        save_btn = ui_qt.QtWidgets.QPushButton("Save Definition (Active Patches Only)")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        _tooltip = (
            "Write patches data to the current selected definition.\n"
            "Used to update the active patches without accidentally affecting the link data (controls and joints)."
        )
        save_btn.setToolTip(_tooltip)
        save_btn.clicked.connect(self.updated_definition_and_write_file)
        self.layout.addWidget(save_btn)

    def update_values(self):
        """Adds the pre-defined retargeter patches as list items."""
        import gt.tools.retargeter.retargeter_patches as tools_rt_patches

        self.patch_list.clear()
        _available_patches_names = tools_rt_patches.Patches.get_patches_dict().keys()
        _addon_patches = self.view.controller.model.project.get_addon_patches()
        _active_addon_names = [a_p.__class__.__name__ for a_p in _addon_patches]

        for patch_name in _available_patches_names:
            _patches_module = importlib.import_module("gt.tools.retargeter.retargeter_patches")
            _addon_patch_obj = eval(f"_patches_module.Patches.{patch_name}()")
            patch_item = ui_qt.QtWidgets.QListWidgetItem(_addon_patch_obj.name)
            patch_item.setWhatsThis(patch_name)
            patch_item.setToolTip(_addon_patch_obj.__class__.__doc__)
            patch_item.setSizeHint(ui_qt.QtCore.QSize(0, 25))
            if patch_name in _active_addon_names:
                patch_item.setCheckState(ui_qt.QtCore.Qt.Checked)
            else:
                patch_item.setCheckState(ui_qt.QtCore.Qt.Unchecked)
            self.patch_list.addItem(patch_item)

    def update_definition(self):
        """Updates model definition from interface fields."""

        active_addon_names = []
        for i in range(self.patch_list.count()):
            if self.patch_list.item(i).checkState() == ui_qt.QtCore.Qt.Checked:
                patch_name = self.patch_list.item(i).whatsThis()
                active_addon_names.append(patch_name)

        # Set the Addon Patches for the definition
        self.view.controller.model.project.set_addon_patches(active_addon_names)

    def updated_definition_and_write_file(self):
        """Updates model definition from stored values and writes it to."""

        self.update_definition()
        _controller = self.view.controller
        _project = self.view.controller.model.project
        _definition_path = _controller.get_edit_definition_path()
        _file_name = os.path.basename(_definition_path)

        if not _definition_path:
            _msg_text = "Definition not selected. Cannot retrieve the file and save."
            logger.warning(_msg_text)
            show_message_box(self.view, title="Warning", message=_msg_text, icon_type="warning")
            return

        # Get the project dict
        _definition_dict = _project.get_definition_as_dict()

        # Save Definition json file
        # -- If already present, make it modifiable
        import gt.core.io as core_io

        if _definition_path and os.path.exists(_definition_path):
            core_io.set_file_permission_modifiable(_definition_path)
        _file_path = core_io.write_json(path=_definition_path, data=_definition_dict)
        if os.path.isfile(_file_path):
            _msg_text = (
                f"Successfully saved active patches to current retarget definition."
                f'\n\nUpdated JSON file: "{_file_name}"'
            )
            show_message_box(self.view, title="Success", message=_msg_text, icon_type="info")

        logging.info(f'Active patches data was written to "{_definition_path}".')


class NewDefinitionDialog(ui_qt.QtWidgets.QDialog):
    """
    Dialog window to input the required values for the creation of a new definition.
    """

    def __init__(self, parent):
        """
        Initialize the dialog for creating a new retarget definition.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent=parent)
        import gt.ui.line_text_widget as ui_line_text

        self.definition_name = None
        self.definition_profile = None

        self.setWindowTitle("New Retarget Definition")
        self.setGeometry(100, 100, 400, 120)
        _label_width = 140

        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)

        # Name field
        self.definition_name_widget = TextBrowseFileWidget(
            self,
            var_name="definition_name",
            browse=False,
            label_width=_label_width,
        )

        # Profile List
        # TODO: currently hardcoded. Once we have a profile logic we can change this.
        _option_list = ["biped"]
        self.definition_profile = "biped"  # init variable
        self.definition_profile_widget = DropDownWidget(
            self,
            var_name="definition_profile",
            option_list=_option_list,
            default_option="biped",
            label_width=_label_width,
        )

        # Buttons
        button_box = ui_qt.QtWidgets.QDialogButtonBox(
            ui_qt.QtWidgets.QDialogButtonBox.Ok | ui_qt.QtWidgets.QDialogButtonBox.Cancel
        )

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.definition_name_widget)
        layout.addWidget(self.definition_profile_widget)
        layout.addStretch()
        layout.addWidget(button_box)
        self.setLayout(layout)

        proceed_btn = button_box.button(ui_qt.QtWidgets.QDialogButtonBox.Ok)
        _proceed_func = partial(self.close_dialog, choice="proceed")
        proceed_btn.clicked.connect(_proceed_func)

        cancel_btn = button_box.button(ui_qt.QtWidgets.QDialogButtonBox.Cancel)
        _cancel_func = partial(self.close_dialog, choice="cancel")
        cancel_btn.clicked.connect(_cancel_func)

        ui_qt_utils.center_window(self)

    def close_dialog(self, choice="proceed"):
        """
        Close the dialog, optionally validating before proceeding.

        Args:
            choice (str, optional): Action choice, either "proceed" to attempt closing
                with validation, or any other value to cancel and reset related attributes.
                Defaults to "proceed".
        """
        if choice == "proceed":
            if not self.definition_name:
                _msg_title = "New Definition"
                _msg_text = "Cannot create a new definition without a name."
                show_message_box(self, title=_msg_title, message=_msg_text, icon_type="warning")
        else:
            self.definition_name = None
            self.definition_profile = None
        self.accept()


class TimedLabel(ui_qt.QtWidgets.QLabel):
    def __init__(self, parent):
        """
        A custom QLabel that displays a message for only a certain amount of time.

        Args:
            parent (RetargeterView): The RetargeterView.
        """
        super().__init__(parent=parent)
        self.setFixedHeight(0)

        # Add timers
        self.seconds = 0
        self.main_timer = ui_qt.QtCore.QTimer(self, timeout=self.on_timeout)
        self.grey_timer = ui_qt.QtCore.QTimer(self, timeout=self.on_grey_timeout)

    def show_message(self, message, seconds=1, msg_type="info"):
        """Shows the supplied message for a certain amount of seconds.

        Args:
            message (str): the message to display.
            seconds (int): the amount of seconds after which the message will disappear.
            msg_type (str): the color applied to the text. Choose between "info", "warning", "error".
        """
        import datetime

        self.main_timer.stop()
        self.grey_timer.stop()

        if not message:
            logger.debug("Please provide a message.")
            return
        if not isinstance(message, str):
            logger.debug("Given message must be a string.")
            return
        if not isinstance(seconds, int):
            logger.debug("Given seconds must be an integer.")
            return
        if seconds < 1:
            seconds = 1

        self.seconds = seconds

        # Expand label
        self.setFixedHeight(35)

        # Set timed text and log
        _time_string = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        _message_string = f"{_time_string}: {message}"
        self.setText(_message_string)
        logger.info(_message_string)

        # Set color based on the type
        self.setStyleSheet("color: lightgreen;")
        if msg_type == "warning":
            self.setStyleSheet("color: yellow;")
        elif msg_type == "error":
            self.setStyleSheet("color: red;")

        # Run the timer
        self.main_timer.start(self.seconds * 1000)

    def on_timeout(self):
        """
        Handle the timeout event by starting the grey timer or resetting the widget.
        """
        if self.seconds:
            self.setStyleSheet("color: grey;")
            self.grey_timer.start(self.seconds * 1000)
        else:
            self.on_grey_timeout()

    def on_grey_timeout(self):
        """
        Reset the widget when the grey timeout occurs.

        This method sets the internal seconds counter to zero,
        collapses the widget height to zero, and clears any displayed text.
        """
        self.seconds = 0
        self.setFixedHeight(0)
        self.setText("")


class OverrideOptionsWidget(ui_qt.QtWidgets.QWidget):
    def __init__(self, parent):
        """
        Retarget override options widget.

        Args:
            parent (RetargeterView): The RetargeterView.
        """
        super().__init__(parent=parent)

        self.view = parent
        self.layout = ui_qt.QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.row01_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.row01_layout.setContentsMargins(0, 0, 0, 0)
        self.row01_layout.setSpacing(20)

        self.row02_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.row02_layout.setContentsMargins(0, 0, 0, 0)
        self.row02_layout.setSpacing(20)

        self.layout.addLayout(self.row01_layout)
        self.layout.addLayout(self.row02_layout)

        # Override Delete Source ------------------------------------------------
        self.override_delete_source_wdg = CheckBoxWidget(
            self.view,
            var_name="override_delete_source",
            nice_name="Delete Source",
            checked=self.view.override_delete_source,
        )
        _tooltip = "Delete the source skeleton after the retarget."
        self.override_delete_source_wdg.setToolTip(_tooltip)
        self.override_delete_source_wdg.label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )

        # Delete Static Channels ------------------------------------------------
        self.delete_static_channels_wdg = CheckBoxWidget(
            self.view,
            var_name="delete_static_channels",
            checked=self.view.delete_static_channels,
        )
        _tooltip = "Delete the static channels (flat animations) after the retarget."
        self.delete_static_channels_wdg.setToolTip(_tooltip)
        self.delete_static_channels_wdg.label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )

        # Post Bake To IK -------------------------------------------------------
        self.disable_post_wdg = CheckBoxWidget(
            self.view,
            var_name="disable_post_processing",
            checked=self.view.disable_post_processing,
        )
        _tooltip = (
            "For testing purposes only.\n"
            "When checked, additional post processing operations will be skipped during the retarget process, "
            "producing an incomplete result.\n"
            "These are not only used to transfer poses from one system to another, "
            "but also to collapse counter-rotations into one channel.\nWhen setup to do so, the IK to FK bake will "
            "limit the rotation to happen only in the available channels.\nPost processing operations can also handle "
            "extra accuracy enhancement steps, such as pole vector patching steps and more.\n"
            "Check the definition setup to see which post processing steps are included."
        )
        self.disable_post_wdg.setToolTip(_tooltip)
        self.disable_post_wdg.label.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed)
        self.disable_post_wdg.checkbox.stateChanged.connect(self.post_processing_highlight)

        _post_proc_checkbox_state = 2 if self.view.disable_post_processing is True else 0
        self.post_processing_highlight(_post_proc_checkbox_state)

        # Override Target Namespace ---------------------------------------------
        _placeholder_namespace = _get_placeholder_namespace_from_target(self.view.target_rig_path)
        if self.view.override_target_namespace:
            _placeholder_namespace = self.view.override_target_namespace
        self.override_target_namespace_wdg = TextBrowseFileWidget(
            self.view,
            var_name="override_target_namespace",
            nice_name="Target Namespace",
            var_value=_placeholder_namespace,
            browse=False,
        )
        self.override_target_namespace_wdg.text_field.setPlaceholderText("")

        self.override_target_namespace_checkbox_wdg = ui_qt.QtWidgets.QCheckBox()
        self.override_target_namespace_checkbox_wdg.setChecked(self.view.override_target_namespace_status)
        _func = partial(
            set_value_from_field,
            parent=self.view,
            var="override_target_namespace_status",
            field=self.override_target_namespace_checkbox_wdg,
        )
        self.override_target_namespace_checkbox_wdg.stateChanged.connect(_func)
        self.override_target_namespace_checkbox_wdg.stateChanged.connect(self.toggle_override_target_namespace_text)
        self.override_target_namespace_wdg.layout.addWidget(self.override_target_namespace_checkbox_wdg)

        _tooltip = "Use a specific namespace for the target (control rig)."
        self.override_target_namespace_wdg.setToolTip(_tooltip)
        self.override_target_namespace_wdg.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )

        self.row01_layout.addWidget(self.override_delete_source_wdg)
        self.row01_layout.addStretch()
        self.row01_layout.addWidget(self.override_target_namespace_wdg)

        self.row02_layout.addWidget(self.delete_static_channels_wdg)
        self.row02_layout.addStretch()
        self.row02_layout.addWidget(self.disable_post_wdg)

        self.toggle_override_target_namespace_text()

    def post_processing_highlight(self, checkbox_state):
        """
        Updates the highlight color of the disable label based on the checkbox state.

        Changes the label text color to red if the checkbox is checked (state 2),
        indicating that post-processing is disabled or in a warning state. Otherwise,
        resets the text color to white.

        Args:
            checkbox_state (int): The current state of the checkbox.
                Typically, 2 represents Qt.Checked, while 0 represents Qt.Unchecked.
        """
        if checkbox_state == 2:
            self.disable_post_wdg.label.setStyleSheet("QLabel { color: red; }")
        else:
            self.disable_post_wdg.label.setStyleSheet("QLabel { color: white; }")

    def toggle_override_target_namespace_text(self):
        """
        Enable or disable the target namespace text field based on the checkbox state.
        """
        if self.override_target_namespace_checkbox_wdg.isChecked():
            self.override_target_namespace_wdg.text_field.setFixedWidth(120)
            self.override_target_namespace_wdg.text_field.setEnabled(True)
        else:
            self.override_target_namespace_wdg.text_field.setFixedWidth(0)
            self.override_target_namespace_wdg.text_field.setEnabled(False)


# ------------------------------------------ Helpers ---------------------------------------------------
def open_file_dialog(*args, field, ok_caption="Set Path", file_filter=None, dir_only=False):
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

    if not file_filter:
        file_filter = tools_retargeter_const.RetargeterConstants.BASE_FILTER

    file_path = ui_file_dialog.file_dialog(
        write_mode=False,
        starting_directory=_starting_directory,
        file_filter=file_filter,
        ok_caption=ok_caption,
        cancel_caption="Cancel",
        dir_only=dir_only,
    )
    if file_path and os.path.exists(file_path):
        field.setText(file_path)


def show_message_box(parent, title="Information", message="Add your message.", icon_type="info", ask_user=False):
    """Shows a message box window.

    Args:
        parent (Qt class): parent class
        title (str): window title
        message (str): window message
        icon_type (str): "info", "warning" or "error", the icon displayed
        ask_user (bool): if True, the buttons "yes" and "no" will be created and the answer handled
    """

    message_box = ui_qt.QtWidgets.QMessageBox(parent)
    message_box.setWindowTitle(title)
    message_box.setText(message)

    _icon = None
    if icon_type == "info":
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_green_circle)
    elif icon_type == "warning":
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_yellow_circle)
    elif icon_type == "error":
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_red_circle)

    if ask_user:
        message_box.addButton("No", ui_qt.QtLib.ButtonRoles.RejectRole)
        message_box.addButton("Yes", ui_qt.QtLib.ButtonRoles.ActionRole)
        _icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)

    if _icon:
        message_box.setIconPixmap(_icon.pixmap(64, 64))

    return message_box.exec_()


def set_value_from_field(*args, parent, var, field):
    """
    If the provided name is available in the tool, this functions tries to set it.
    Args:
        args (any): Used to receive the change from the incoming QtWidget
        parent (RetargeterView): The RetargeterView.
        var (str): Name of the variable.
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
        _index = field.currentIndex()
        _data = field.itemData(_index)
        if _data:
            _value = _data
        else:
            _value = field.currentText()
    if isinstance(field, ui_qt.QtWidgets.QTabWidget):
        _value = field.currentIndex()

    if not field.isEnabled():
        _value = None
    if hasattr(parent, var):
        setattr(parent, var, _value)
        # Save Preferences if the function is defined
        if hasattr(parent, "save_preferences"):
            parent.save_preferences()
    else:
        logger.warning(f'Unable to set missing variable. Variable: "{var}". Class: "{type(parent)}".')


def get_short_display_name(name_value):
    """
    Gets the short name to use inside the interface.

    Args:
        name_value (str): original object name.
    Returns:
        str: short name to use.
    """
    import gt.core.namespace as core_nspace

    if not name_value:
        logger.error("Given value is invalid.")
        return
    if not isinstance(name_value, str):
        logger.error("Given value is not a string.")
        return

    return core_naming.get_short_name(name_value, remove_namespace=True)


def _get_placeholder_namespace_from_target(file_path):
    """Get the basename without extension from the given path.
    Args:
        file_path (str): The path to the target file.
    Returns:
        str: placeholder text
    """
    placeholder_text = "placeholder"
    if file_path:
        placeholder_text = os.path.basename(file_path).split(".")[0]
    return placeholder_text
