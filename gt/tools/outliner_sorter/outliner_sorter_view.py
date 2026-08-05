"""
Outliner Sorter View
"""

from gt.tools.outliner_sorter import outliner_sorter_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class OutlinerSorterView(metaclass=MayaWindowMeta):
    """Qt view for the Outliner Sorter."""

    def __init__(self, parent=None, version=None):
        """Initializes the Outliner Sorter view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("Outliner Sorter" + (f" - (v{version})" if version else ""))
        self.setMinimumWidth(320)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_outliner_sorter))
        self.build_widgets()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def build_widgets(self):
        """Builds all widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        main_layout.addWidget(self.create_separator("Reorder"))
        reorder_layout_one = ui_qt.QtWidgets.QHBoxLayout()
        reorder_layout_two = ui_qt.QtWidgets.QHBoxLayout()
        self.move_up_btn = ui_qt.QtWidgets.QPushButton("Move Up")
        self.move_front_btn = ui_qt.QtWidgets.QPushButton("Move Front")
        self.move_down_btn = ui_qt.QtWidgets.QPushButton("Move Down")
        self.move_back_btn = ui_qt.QtWidgets.QPushButton("Move Back")
        self.move_up_btn.setToolTip("Move selected objects one position up among their siblings.")
        self.move_front_btn.setToolTip("Move selected objects to the top of their sibling list.")
        self.move_down_btn.setToolTip("Move selected objects one position down among their siblings.")
        self.move_back_btn.setToolTip("Move selected objects to the bottom of their sibling list.")
        reorder_layout_one.addWidget(self.move_up_btn)
        reorder_layout_one.addWidget(self.move_front_btn)
        reorder_layout_two.addWidget(self.move_down_btn)
        reorder_layout_two.addWidget(self.move_back_btn)
        main_layout.addLayout(reorder_layout_one)
        main_layout.addLayout(reorder_layout_two)

        utility_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.shuffle_btn = ui_qt.QtWidgets.QPushButton("Shuffle")
        self.shuffle_btn.setToolTip("Randomize selected objects among their siblings.")
        self.sort_order_combo = ui_qt.QtWidgets.QComboBox()
        self.sort_order_combo.addItems(model.SORT_ORDER_OPTIONS)
        self.sort_order_combo.setToolTip("Controls ascending or descending order for name and attribute sorting.")
        self.sort_order_combo.setFixedHeight(self.shuffle_btn.sizeHint().height())
        utility_layout.addWidget(self.shuffle_btn)
        utility_layout.addWidget(self.sort_order_combo)
        main_layout.addLayout(utility_layout)

        main_layout.addWidget(self.create_separator("Sort"))
        self.sort_name_btn = ui_qt.QtWidgets.QPushButton("Sort by Name")
        self.sort_name_btn.setToolTip("Sort selected objects alphabetically by object name.")
        main_layout.addWidget(self.sort_name_btn)

        attr_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.attribute_combo = ui_qt.QtWidgets.QComboBox()
        self.attribute_combo.addItems(model.ATTRIBUTE_OPTIONS)
        self.attribute_combo.setCurrentText(model.ATTR_TRANSLATE_Y)
        self.attribute_combo.setToolTip("Choose the attribute used by Sort by Attribute.")
        self.attribute_field = ui_qt.QtWidgets.QLineEdit("translateY")
        self.attribute_field.setToolTip("Custom attribute name used when Custom Attribute is selected.")
        self.attribute_field.setEnabled(False)
        attr_layout.addWidget(self.attribute_combo)
        attr_layout.addWidget(self.attribute_field)
        main_layout.addLayout(attr_layout)

        self.sort_attribute_btn = ui_qt.QtWidgets.QPushButton("Sort by Attribute")
        self.sort_attribute_btn.setToolTip("Sort selected objects by the selected or custom attribute value.")
        main_layout.addWidget(self.sort_attribute_btn)

    def resize_to_contents(self):
        """Resizes a floating window to the smallest height required by its contents."""
        try:
            if hasattr(self, "isFloating") and not self.isFloating():
                return
        except (AttributeError, RuntimeError):
            pass
        self.updateGeometry()
        self.adjustSize()
        content_height = self.sizeHint().height()
        if content_height > 0:
            self.resize(max(self.width(), self.minimumWidth()), content_height)

    @staticmethod
    def create_separator(text):
        """Creates a centered section separator.

        Args:
            text (str): Section text.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 7, 0, 2)
        layout.setSpacing(7)

        left_line = ui_qt.QtWidgets.QFrame()
        right_line = ui_qt.QtWidgets.QFrame()
        for line in [left_line, right_line]:
            line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
            line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)

        label = ui_qt.QtWidgets.QLabel(text)
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    def is_ascending(self):
        """Gets whether current sort order is ascending.

        Returns:
            bool: True when ascending.
        """
        return self.sort_order_combo.currentText() == model.SORT_ORDER_ASCENDING

    def get_attribute_name(self):
        """Gets the selected attribute name.

        Returns:
            str: Attribute name.
        """
        option = self.attribute_combo.currentText()
        if option == model.ATTR_CUSTOM:
            return self.attribute_field.text()
        return model.ATTRIBUTE_NAME_MAP.get(option, "translateY")
