"""
Script used to determine which version of PySide is being imported

Import Line:
    import gt.ui.qt_import as ui_qt

Use Example:
    ui_qt.QtWidgets.QLabel("My Label")
"""

import pkg_resources
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

IS_PYSIDE6 = False

try:
    import PySide2 as PySide
    from PySide2 import (
        QtCore,
        QtGui,
        QtWidgets,
        QtSvg,
        QtNetwork,
        QtPrintSupport,
        QtMultimedia,
        QtQml,
        QtQuick,
        QtQuickWidgets,
        QtOpenGL,
        QtTest,
        QtWebEngineWidgets,
        QtWebSockets,
        Qt3DCore,
        Qt3DInput,
    )
    import shiboken2 as shiboken

except ImportError:
    logging.debug("Pyside2 not found, attempting to import PySide6")
    import PySide6 as PySide
    from PySide6 import (
        QtCore,
        QtGui,
        QtWidgets,
        QtSvg,
        QtNetwork,
        QtPrintSupport,
        QtMultimedia,
        QtQml,
        QtQuick,
        QtQuickWidgets,
        QtOpenGL,
        QtTest,
        QtWebEngineWidgets,
        QtWebSockets,
        Qt3DCore,
        Qt3DInput,
    )
    import shiboken6 as shiboken

    IS_PYSIDE6 = True


def get_pyside_version(major_only=False):
    """
    Get the version of PySide2 or PySide6 installed in the environment.

    Args:
        major_only (bool): If True, returns only the major version number.
                           Defaults to False, which returns the full version string.

    Returns:
        str or None: The version of PySide2 or PySide6, or a message indicating that neither is installed. e.g. "6.5.3"
                     If major_only is True, only the major version number is returned. e.g. "6"
    """
    for package in ["PySide2", "PySide6"]:
        try:
            version = pkg_resources.get_distribution(package).version
            return version.split(".")[0] if major_only else version
        except pkg_resources.DistributionNotFound:
            continue
    logger.debug("Neither PySide2 nor PySide6 is installed")
    return None


class QtLib:
    """
    Pyside2 and Pyside6 use different patterns for certain variables.
    For example in Pyside2 you would use "QtCore.Qt.Horizontal" but in PySide6 "QtCore.Qt.Orientation.Horizontal"
    This class aims to provide one access to certain variables independently of the pyside version.
    """

    # --------------------------------------- Orientation Flags ---------------------------------------
    class Orientation:
        Horizontal = None
        Vertical = None
        if IS_PYSIDE6:  # PySide6
            Horizontal = QtCore.Qt.Orientation.Horizontal
            Vertical = QtCore.Qt.Orientation.Vertical
        else:  # PySide2
            Horizontal = QtCore.Qt.Horizontal
            Vertical = QtCore.Qt.Vertical

    # ------------------------------------------- Keys ENUM --------------------------------------------
    class Key:
        Key_Return = None
        Key_Enter = None
        if IS_PYSIDE6:  # PySide6
            Key_Return = QtCore.Qt.Key.Key_Return
            Key_Enter = QtCore.Qt.Key.Key_Enter
        else:  # PySide2
            Key_Return = QtCore.Qt.Key_Return
            Key_Enter = QtCore.Qt.Key_Enter

    # ----------------------------------------- Alignment Flags ----------------------------------------
    class AlignmentFlag:
        AlignCenter = None
        AlignLeft = None
        AlignRight = None
        AlignHCenter = None
        AlignVCenter = None
        AlignTop = None
        AlignBottom = None
        if IS_PYSIDE6:  # PySide6
            AlignCenter = QtCore.Qt.AlignmentFlag.AlignCenter
            AlignLeft = QtCore.Qt.AlignmentFlag.AlignLeft
            AlignRight = QtCore.Qt.AlignmentFlag.AlignRight
            AlignHCenter = QtCore.Qt.AlignmentFlag.AlignHCenter
            AlignVCenter = QtCore.Qt.AlignmentFlag.AlignVCenter
            AlignTop = QtCore.Qt.AlignmentFlag.AlignTop
            AlignBottom = QtCore.Qt.AlignmentFlag.AlignBottom
        else:  # PySide2
            AlignCenter = QtCore.Qt.AlignCenter
            AlignLeft = QtCore.Qt.AlignLeft
            AlignRight = QtCore.Qt.AlignRight
            AlignHCenter = QtCore.Qt.AlignHCenter
            AlignVCenter = QtCore.Qt.AlignVCenter
            AlignTop = QtCore.Qt.AlignTop
            AlignBottom = QtCore.Qt.AlignBottom

    # ------------------------------------------ Mouse Buttons -----------------------------------------
    class MouseButton:
        LeftButton = None
        RightButton = None
        MiddleButton = None
        if IS_PYSIDE6:  # PySide6
            LeftButton = QtCore.Qt.MouseButton.LeftButton
            RightButton = QtCore.Qt.MouseButton.RightButton
            MiddleButton = QtCore.Qt.MouseButton.MiddleButton
        else:  # PySide2
            LeftButton = QtCore.Qt.LeftButton
            RightButton = QtCore.Qt.RightButton
            MiddleButton = QtCore.Qt.MiddleButton

    # ------------------------------------------ Cursor Shapes -----------------------------------------
    class CursorShape:
        ArrowCursor = None
        CrossCursor = None
        SizeHorCursor = None
        SplitHCursor = None
        PointingHandCursor = None
        if IS_PYSIDE6:  # PySide6
            ArrowCursor = QtCore.Qt.CursorShape.ArrowCursor
            CrossCursor = QtCore.Qt.CursorShape.CrossCursor
            SizeHorCursor = QtCore.Qt.CursorShape.SizeHorCursor
            SplitHCursor = QtCore.Qt.CursorShape.SplitHCursor
            PointingHandCursor = QtCore.Qt.CursorShape.PointingHandCursor
        else:  # PySide2
            ArrowCursor = QtCore.Qt.ArrowCursor
            CrossCursor = QtCore.Qt.CrossCursor
            SizeHorCursor = QtCore.Qt.SizeHorCursor
            SplitHCursor = QtCore.Qt.SplitHCursor
            PointingHandCursor = QtCore.Qt.PointingHandCursor

    # ------------------------------------------ Brush Styles ------------------------------------------
    class BrushStyle:
        SolidPattern = None
        BDiagPattern = None
        FDiagPattern = None
        if IS_PYSIDE6:  # PySide6
            SolidPattern = QtCore.Qt.BrushStyle.SolidPattern
            BDiagPattern = QtCore.Qt.BrushStyle.BDiagPattern
            FDiagPattern = QtCore.Qt.BrushStyle.FDiagPattern
        else:  # PySide2
            SolidPattern = QtCore.Qt.SolidPattern
            BDiagPattern = QtCore.Qt.BDiagPattern
            FDiagPattern = QtCore.Qt.FDiagPattern

    # -------------------------------------------- Pen Styles ------------------------------------------
    class PenStyle:
        SolidLine = None
        DashLine = None
        DotLine = None
        if IS_PYSIDE6:  # PySide6
            SolidLine = QtCore.Qt.PenStyle.SolidLine
            DashLine = QtCore.Qt.PenStyle.DashLine
            DotLine = QtCore.Qt.PenStyle.DotLine
        else:  # PySide2
            SolidLine = QtCore.Qt.SolidLine
            DashLine = QtCore.Qt.DashLine
            DotLine = QtCore.Qt.DotLine

    # --------------------------------------- Keyboard Modifiers ---------------------------------------
    class KeyboardModifier:
        ControlModifier = None
        ShiftModifier = None
        AltModifier = None
        if IS_PYSIDE6:  # PySide6
            ControlModifier = QtCore.Qt.KeyboardModifier.ControlModifier
            ShiftModifier = QtCore.Qt.KeyboardModifier.ShiftModifier
            AltModifier = QtCore.Qt.KeyboardModifier.AltModifier
        else:  # PySide2
            ControlModifier = QtCore.Qt.ControlModifier
            ShiftModifier = QtCore.Qt.ShiftModifier
            AltModifier = QtCore.Qt.AltModifier

    # ------------------------------------------- Font Weights -----------------------------------------
    class Font:
        Bold = None
        if IS_PYSIDE6:  # PySide6
            Bold = QtGui.QFont.Weight.Bold
        else:  # PySide2
            Bold = QtGui.QFont.Bold

    # ------------------------------------------- ItemDataRoles ----------------------------------------
    class ItemDataRole:
        UserRole = None
        DisplayRole = None
        ForegroundRole = None
        ToolTipRole = None
        if IS_PYSIDE6:  # PySide6
            UserRole = QtCore.Qt.ItemDataRole.UserRole
            ForegroundRole = QtCore.Qt.ItemDataRole.ForegroundRole
            ToolTipRole = QtCore.Qt.ItemDataRole.ToolTipRole
        else:  # PySide2
            UserRole = QtCore.Qt.UserRole
            DisplayRole = QtCore.Qt.DisplayRole
            ForegroundRole = QtCore.Qt.ForegroundRole
            ToolTipRole = QtCore.Qt.ToolTipRole

    # ------------------------------------------- ItemDataRoles ----------------------------------------
    class StandardButton:
        Yes = None
        No = None
        Cancel = None
        Close = None
        if IS_PYSIDE6:  # PySide6
            Yes = QtWidgets.QMessageBox.StandardButton.Yes
            No = QtWidgets.QMessageBox.StandardButton.No
            Cancel = QtWidgets.QMessageBox.StandardButton.Cancel
            Close = QtWidgets.QMessageBox.StandardButton.Close
        else:  # PySide2
            Yes = QtWidgets.QMessageBox.Yes
            No = QtWidgets.QMessageBox.No
            Cancel = QtWidgets.QMessageBox.Cancel
            Close = QtWidgets.QMessageBox.Close

    # -------------------------------------------- ButtonRoles -----------------------------------------
    class ButtonRoles:
        ActionRole = None
        RejectRole = None
        if IS_PYSIDE6:  # PySide6
            ActionRole = QtWidgets.QMessageBox.ButtonRole.ActionRole
            RejectRole = QtWidgets.QMessageBox.ButtonRole.RejectRole
        else:  # PySide2
            ActionRole = QtWidgets.QMessageBox.ActionRole
            RejectRole = QtWidgets.QMessageBox.RejectRole

    # ------------------------------------------- ItemDataRoles ----------------------------------------
    class ItemFlag:
        ItemIsEnabled = None
        ItemIsSelectable = None
        ItemIsDragEnabled = None
        ItemIsUserCheckable = None
        if IS_PYSIDE6:  # PySide6
            ItemIsEnabled = QtCore.Qt.ItemFlag.ItemIsEnabled
            ItemIsSelectable = QtCore.Qt.ItemFlag.ItemIsSelectable
            ItemIsDragEnabled = QtCore.Qt.ItemFlag.ItemIsDragEnabled
            ItemIsUserCheckable = QtCore.Qt.ItemFlag.ItemIsUserCheckable
        else:  # PySide2
            ItemIsEnabled = QtCore.Qt.ItemIsEnabled
            ItemIsSelectable = QtCore.Qt.ItemIsSelectable
            ItemIsDragEnabled = QtCore.Qt.ItemIsDragEnabled
            ItemIsUserCheckable = QtCore.Qt.ItemIsUserCheckable

    # ------------------------------------------- AbstractItemView ----------------------------------------
    class ScrollHint:
        PositionAtCenter = None
        if IS_PYSIDE6:  # PySide6
            PositionAtCenter = QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter
        else:  # PySide2
            PositionAtCenter = QtWidgets.QAbstractItemView.PositionAtCenter

    # -------------------------------------------- Size Policy -----------------------------------------
    class SizePolicy:
        Expanding = None
        Fixed = None
        Preferred = None
        Minimum = None
        if IS_PYSIDE6:  # PySide6
            Expanding = QtWidgets.QSizePolicy.Policy.Expanding
            Fixed = QtWidgets.QSizePolicy.Policy.Fixed
            Preferred = QtWidgets.QSizePolicy.Policy.Preferred
            Minimum = QtWidgets.QSizePolicy.Policy.Minimum
        else:  # PySide2
            Expanding = QtWidgets.QSizePolicy.Expanding
            Fixed = QtWidgets.QSizePolicy.Fixed
            Preferred = QtWidgets.QSizePolicy.Preferred
            Minimum = QtWidgets.QSizePolicy.Minimum

    # -------------------------------------------- Size Policy -----------------------------------------
    class FocusPolicy:
        NoFocus = None
        if IS_PYSIDE6:  # PySide6
            NoFocus = QtCore.Qt.FocusPolicy.NoFocus
        else:  # PySide2
            NoFocus = QtCore.Qt.NoFocus

    # ------------------------------------------- WindowFlag ----------------------------------------
    class WindowFlag:
        WindowMaximizeButtonHint = None  # Max
        WindowMinimizeButtonHint = None  # Min
        WindowContextHelpButtonHint = None
        WindowStaysOnTopHint = None
        WindowModal = None
        Tool = None
        if IS_PYSIDE6:  # PySide6
            WindowMaximizeButtonHint = QtCore.Qt.WindowType.WindowMaximizeButtonHint
            WindowMinimizeButtonHint = QtCore.Qt.WindowType.WindowMinimizeButtonHint
            WindowContextHelpButtonHint = QtCore.Qt.WindowType.WindowContextHelpButtonHint
            WindowStaysOnTopHint = QtCore.Qt.WindowType.WindowStaysOnTopHint
            WindowModal = QtCore.Qt.WindowModality.WindowModal
            Tool = QtCore.Qt.WindowType.Tool
        else:  # PySide2
            WindowMaximizeButtonHint = QtCore.Qt.WindowMaximizeButtonHint
            WindowMinimizeButtonHint = QtCore.Qt.WindowMinimizeButtonHint
            WindowContextHelpButtonHint = QtCore.Qt.WindowContextHelpButtonHint
            WindowStaysOnTopHint = QtCore.Qt.WindowStaysOnTopHint
            WindowModal = QtCore.Qt.WindowModal
            Tool = QtCore.Qt.Tool

    # ------------------------------------------- ButtonStyle ----------------------------------------
    class ToolButtonStyle:
        ToolButtonTextUnderIcon = None
        if IS_PYSIDE6:  # PySide6
            ToolButtonTextUnderIcon = QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        else:  # PySide2
            ToolButtonTextUnderIcon = QtCore.Qt.ToolButtonTextUnderIcon

    # ------------------------------------------- TransformationMode ----------------------------------------
    class TransformationMode:
        SmoothTransformation = None
        if IS_PYSIDE6:  # PySide6
            SmoothTransformation = QtCore.Qt.TransformationMode.SmoothTransformation
        else:  # PySide2
            SmoothTransformation = QtCore.Qt.SmoothTransformation

    # ------------------------------------------- OpenModeFlag ----------------------------------------
    class OpenModeFlag:
        ReadOnly = None
        if IS_PYSIDE6:  # PySide6
            ReadOnly = QtCore.QIODevice.OpenModeFlag.ReadOnly
        else:  # PySide2
            ReadOnly = QtCore.QIODevice.ReadOnly

    # ------------------------------------------- FormLayout ----------------------------------------
    class FormLayout:
        AllNonFixedFieldsGrow = None
        if IS_PYSIDE6:  # PySide6
            AllNonFixedFieldsGrow = QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        else:  # PySide2
            AllNonFixedFieldsGrow = QtWidgets.QFormLayout.AllNonFixedFieldsGrow

    # ------------------------------------------- FrameStyle ----------------------------------------
    class FrameStyle:
        StyledPanel = None
        Sunken = None
        NoFrame = None
        HLine = None
        if IS_PYSIDE6:  # PySide6
            StyledPanel = QtWidgets.QFrame.Shape.StyledPanel
            Sunken = QtWidgets.QFrame.Shadow.Sunken
            NoFrame = QtWidgets.QFrame.Shape.NoFrame
            HLine = QtWidgets.QFrame.Shape.HLine
        else:  # PySide2
            StyledPanel = QtWidgets.QFrame.StyledPanel
            Sunken = QtWidgets.QFrame.Sunken
            NoFrame = QtWidgets.QFrame.NoFrame
            HLine = QtWidgets.QFrame.HLine

    # ------------------------------------------- LineWrapModes ----------------------------------------
    class LineWrapMode:
        NoWrap = None
        if IS_PYSIDE6:  # PySide6
            NoWrap = QtWidgets.QTextEdit.LineWrapMode.NoWrap
        else:  # PySide2
            NoWrap = QtWidgets.QTextEdit.NoWrap

    # ------------------------------------------- TextCursor ----------------------------------------
    class TextCursor:
        MoveAnchor = None
        KeepAnchor = None
        Start = None
        End = None
        Down = None
        StartOfLine = None
        EndOfLine = None
        NextBlock = None
        if IS_PYSIDE6:  # PySide6
            MoveAnchor = QtGui.QTextCursor.MoveMode.MoveAnchor
            KeepAnchor = QtGui.QTextCursor.MoveMode.KeepAnchor
            Start = QtGui.QTextCursor.MoveOperation.Start
            End = QtGui.QTextCursor.MoveOperation.End
            Down = QtGui.QTextCursor.MoveOperation.Down
            StartOfLine = QtGui.QTextCursor.MoveOperation.StartOfLine
            EndOfLine = QtGui.QTextCursor.MoveOperation.EndOfLine
            NextBlock = QtGui.QTextCursor.MoveOperation.NextBlock
        else:  # PySide2
            MoveAnchor = QtGui.QTextCursor.MoveAnchor
            KeepAnchor = QtGui.QTextCursor.KeepAnchor
            Start = QtGui.QTextCursor.Start
            End = QtGui.QTextCursor.End
            Down = QtGui.QTextCursor.Down
            StartOfLine = QtGui.QTextCursor.StartOfLine
            EndOfLine = QtGui.QTextCursor.EndOfLine
            NextBlock = QtGui.QTextCursor.NextBlock

    # ------------------------------------------- TextDocument ----------------------------------------
    class TextDocument:
        FindBackward = None
        if IS_PYSIDE6:  # PySide6
            FindBackward = QtGui.QTextDocument.FindFlag.FindBackward
        else:  # PySide2
            FindBackward = QtGui.QTextDocument.FindBackward

    # ------------------------------------------- TextDocument ----------------------------------------
    class RenderHint:
        SmoothPixmapTransform = None
        Antialiasing = None
        TextAntialiasing = None
        if IS_PYSIDE6:  # PySide6
            SmoothPixmapTransform = QtGui.QPainter.RenderHint.SmoothPixmapTransform
            Antialiasing = QtGui.QPainter.RenderHint.Antialiasing
            TextAntialiasing = QtGui.QPainter.RenderHint.TextAntialiasing
        else:  # PySide2
            SmoothPixmapTransform = QtGui.QPainter.SmoothPixmapTransform
            Antialiasing = QtGui.QPainter.Antialiasing
            TextAntialiasing = QtGui.QPainter.TextAntialiasing

    # ------------------------------------------ Misc Overrides ----------------------------------------
    class QtCore:
        QRegExp = None
        if IS_PYSIDE6:  # PySide6
            QRegExp = QtCore.QRegularExpression
        else:  # PySide2
            QRegExp = QtCore.QRegExp

    class QtGui:
        QAction = None
        if IS_PYSIDE6:  # PySide6
            QAction = QtGui.QAction
        else:  # PySide2
            QAction = QtWidgets.QAction

    class DragDropMode:
        InternalMove = None
        if IS_PYSIDE6:  # PySide6
            InternalMove = QtWidgets.QTreeWidget.DragDropMode.InternalMove
        else:  # PySide2
            InternalMove = QtWidgets.QTreeWidget.InternalMove

    class SelectionMode:
        SingleSelection = None
        if IS_PYSIDE6:  # PySide6
            SingleSelection = QtWidgets.QTreeWidget.SelectionMode.SingleSelection
        else:  # PySide2
            SingleSelection = QtWidgets.QTreeWidget.SingleSelection

    class QHeaderView:
        ResizeToContents = None
        Interactive = None
        Stretch = None
        if IS_PYSIDE6:  # PySide6
            ResizeToContents = QtWidgets.QHeaderView.ResizeMode.ResizeToContents
            Interactive = QtWidgets.QHeaderView.ResizeMode.Interactive
            Stretch = QtWidgets.QHeaderView.ResizeMode.Stretch
        else:  # PySide2
            ResizeToContents = QtWidgets.QHeaderView.ResizeToContents
            Interactive = QtWidgets.QHeaderView.Interactive
            Stretch = QtWidgets.QHeaderView.Stretch

    class CheckState:
        Checked = None
        Unchecked = None
        if IS_PYSIDE6:  # PySide6
            Checked = QtCore.Qt.CheckState.Checked
            Unchecked = QtCore.Qt.CheckState.Unchecked
        else:  # PySide2
            Checked = QtCore.Qt.Checked
            Unchecked = QtCore.Qt.Unchecked


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    print(get_pyside_version(False))
    print(type(QtGui.QFont.Weight.Bold))
