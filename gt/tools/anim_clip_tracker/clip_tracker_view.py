"""Qt view for the Animation Clip Tracker."""

from functools import partial
from glob import glob as find_glob_paths
import os

from gt.tools.anim_clip_tracker import clip_tracker_preferences
from gt.tools.anim_clip_tracker import clip_tracker_timeline
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.resource_library as ui_res_lib


TIMELINE_HEIGHT = 110
TIMELINE_HANDLE_WIDTH = 6
SELECTED_ROW_COLOR = "rgb(77, 66, 31)"
SELECTED_ROW_LABEL_COLOR = "#FFC832"
ISSUE_ERROR_COLOR = "rgb(140, 46, 46)"
ISSUE_WARNING_COLOR = "rgb(140, 92, 20)"
FRAME_FIELD_MINIMUM = -(2**31)
FRAME_FIELD_MAXIMUM = 2**31 - 1


def get_maya_cmds():
    """Gets maya.cmds lazily.

    Returns:
        module: maya.cmds module.
    """
    import maya.cmds as cmds

    return cmds


def get_open_maya():
    """Gets Maya API lazily.

    Returns:
        module: maya.api.OpenMaya module.
    """
    import maya.api.OpenMaya as om

    return om


class ClipTrackerView(metaclass=ui_qt_utils.MayaWindowMeta):
    """Builds the dockable Animation Clip Tracker Qt interface."""

    WINDOW_NAME = "GTClipTrackerWindow"
    LEGACY_WORKSPACE_CONTROL = "GTClipTrackerWorkspaceControl"
    CLIP_INDEX_WIDTH = 20
    CLIP_ACTIVE_WIDTH = 20
    CLIP_NAME_MINIMUM_WIDTH = 120
    CLIP_FRAME_WIDTH = 60
    CLIP_ACTION_WIDTH = 30
    CLIP_COLUMN_COUNT = 9

    def __init__(self, parent=None, version=None):
        """Initializes the clip tracker view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.version = version
        self.controller = None
        self.info_ui = None
        self.play_buttons = []
        self.duration_fields = []
        self.frame_fields = {}
        self.name_fields = {}
        self.index_labels = {}
        self.clip_rows = {}
        self.clips_scroll = None
        self.clips_content = None
        self.clips_layout = None
        self.timeline_widget = None
        self.timeline_splitter = None
        self._timeline_height = TIMELINE_HEIGHT
        self.preferences_panel = None
        self.preferences_scroll = None
        self.automations_scroll = None
        self.automations_content = None
        self.automations_layout = None
        self.automation_checkboxes = {}
        self.automation_index_labels = []
        self.automation_empty_label = None
        self.tabs = None
        self._scaled_width_widgets = []
        self._scaled_icon_buttons = []
        self._ui_scale = 1.0
        self._ui_built = False
        self.setMinimumSize(0, 0)
        self.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_clip_tracker))

    def build_ui(self):
        """Builds or rebuilds the Qt interface."""
        self.remove_legacy_workspace_control()
        self._ui_built = False
        self.clear_layout()
        self.update_ui_scale_metrics(force=True)
        title = "Clip Tracker"
        if self.version:
            title += " - (v{0})".format(self.version)
        self.setWindowTitle(title)
        self.resize(780, 710)

        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        no_constraint = getattr(ui_qt.QtWidgets.QLayout, "SetNoConstraint", None)
        if no_constraint is None:
            no_constraint = ui_qt.QtWidgets.QLayout.SizeConstraint.SetNoConstraint
        main_layout.setSizeConstraint(no_constraint)
        main_layout.setContentsMargins(8, 6, 8, 8)
        main_layout.setSpacing(6)
        main_layout.addLayout(self.build_top_toolbar())

        # Keep this widget alive while hidden. Rebuilding a docked workspace
        # control from the preference signal can leave Maya with stale Qt state.
        self.timeline_widget = clip_tracker_timeline.ClipTimelineWidget(parent=self)
        self.tabs = ui_qt.QtWidgets.QTabWidget()
        self.tabs.setMinimumSize(0, 0)
        self.tabs.setElideMode(ui_qt.QtCore.Qt.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        self.tabs.addTab(self.build_clips_tab(), "Animation Clips")
        self.tabs.addTab(self.build_automations_tab(), "Automations")
        self.tabs.addTab(self.build_preferences_tab(), "Preferences")
        self.timeline_splitter = self.build_timeline_splitter()
        main_layout.addWidget(self.timeline_splitter, 1)
        self.set_timeline_visible(self.controller.model.show_timeline)
        self.controller.connect_timeline(self.timeline_widget)
        self.apply_stylesheet()
        self.attach_preferences_panel()
        self.build_automations_ui()
        self.update_timeline()
        self.setMinimumSize(0, 0)
        self._ui_built = True
        if not self.isVisible():
            self.show()
        self.draw_clips(self.controller.model.get_data())

    @classmethod
    def remove_legacy_workspace_control(cls):
        """Removes the workspace control used before the Qt view migration."""
        try:
            cmds = get_maya_cmds()
            if cmds.workspaceControl(cls.LEGACY_WORKSPACE_CONTROL, query=True, exists=True):
                cmds.deleteUI(cls.LEGACY_WORKSPACE_CONTROL)
        except Exception:
            pass

    def clear_layout(self):
        """Deletes widgets from a previous UI build."""
        layout = self.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            child_widget = item.widget()
            if child_layout:
                self.clear_nested_layout(child_layout)
            if child_widget:
                child_widget.setParent(None)
                child_widget.deleteLater()
        layout.setParent(None)
        layout.deleteLater()
        self.timeline_widget = None
        self.timeline_splitter = None
        self.preferences_panel = None
        self.clips_scroll = None
        self.clips_content = None
        self.clips_layout = None
        self.preferences_scroll = None
        self.automations_scroll = None
        self.automations_content = None
        self.automations_layout = None
        self.automation_checkboxes = {}
        self.automation_index_labels = []
        self.automation_empty_label = None
        self.tabs = None
        self._scaled_width_widgets = []
        self._scaled_icon_buttons = []
        self.play_buttons = []
        self.duration_fields = []
        self.frame_fields = {}
        self.name_fields = {}
        self.index_labels = {}
        self.clip_rows = {}

    @staticmethod
    def clear_nested_layout(layout):
        """Removes widgets and nested layouts from a Qt layout.

        Args:
            layout (QLayout): Layout to clear.
        """
        while layout.count():
            item = layout.takeAt(0)
            child_layout = item.layout()
            child_widget = item.widget()
            if child_layout:
                ClipTrackerView.clear_nested_layout(child_layout)
            if child_widget:
                child_widget.setParent(None)
                child_widget.deleteLater()

    def showEvent(self, event):
        """Refreshes DPI-aware metrics after the view is shown.

        Args:
            event (QShowEvent): Qt show event.
        """
        super().showEvent(event)
        if self._ui_built:
            self.update_ui_scale_metrics()

    def moveEvent(self, event):
        """Refreshes DPI-aware metrics after moving between displays.

        Args:
            event (QMoveEvent): Qt move event.
        """
        super().moveEvent(event)
        if self._ui_built:
            self.update_ui_scale_metrics()

    def resizeEvent(self, event):
        """Refreshes DPI-aware metrics when a remote display changes size.

        Args:
            event (QResizeEvent): Qt resize event.
        """
        super().resizeEvent(event)
        if self._ui_built:
            self.update_ui_scale_metrics()

    def get_ui_scale_factor(self):
        """Gets a safe DPI scale factor for the display hosting this view.

        Returns:
            float: Current DPI scale, clamped to at least the standard scale.
        """
        try:
            screen_number = ui_qt_utils.get_window_screen_number(window=self)
            scale_factor = float(ui_qt_utils.get_screen_dpi_scale(screen_number))
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return 1.0
        return max(1.0, scale_factor)

    def get_scaled_width(self, width):
        """Scales a logical control width for the current display DPI.

        Args:
            width (int): Width at the standard DPI scale.

        Returns:
            int: Width suitable for the current display.
        """
        return max(1, int(round(int(width) * self._ui_scale)))

    def get_clip_row_minimum_width(self):
        """Gets the minimum width that keeps all clip-row columns usable.

        Returns:
            int: Minimum width for a complete clip row.
        """
        fixed_width = (
            self.CLIP_INDEX_WIDTH
            + self.CLIP_ACTIVE_WIDTH
            + (self.CLIP_FRAME_WIDTH * 3)
            + (self.CLIP_ACTION_WIDTH * 3)
        )
        spacing_width = (self.CLIP_COLUMN_COUNT - 1) * 2
        return (
            self.get_scaled_width(fixed_width)
            + self.get_scaled_width(self.CLIP_NAME_MINIMUM_WIDTH)
            + spacing_width
        )

    def register_scaled_width_widget(self, widget, width):
        """Tracks and sizes a fixed-width control using the current DPI scale.

        Args:
            widget (QWidget): Widget that should retain a scaled fixed width.
            width (int): Width at the standard DPI scale.
        """
        self._scaled_width_widgets.append((widget, int(width)))
        widget.setFixedWidth(self.get_scaled_width(width))

    def set_icon_button_size(self, button, width):
        """Applies scaled dimensions and icon padding to an action button.

        Args:
            button (QToolButton): Action button to resize.
            width (int): Square button size at the standard DPI scale.
        """
        button_size = self.get_scaled_width(width)
        icon_padding = self.get_scaled_width(3)
        button.setFixedSize(button_size, button_size)
        button.setIconSize(
            ui_qt.QtCore.QSize(
                max(1, button_size - (icon_padding * 2)),
                max(1, button_size - (icon_padding * 2)),
            )
        )

    def update_ui_scale_metrics(self, force=False):
        """Updates fixed clip-list control widths when the screen DPI changes.

        Args:
            force (bool, optional): Whether to update even when the scale is unchanged.
        """
        scale_factor = self.get_ui_scale_factor()
        if not force and abs(scale_factor - self._ui_scale) < 0.01:
            return
        self._ui_scale = scale_factor
        for widget, width in self._scaled_width_widgets:
            if ui_qt_utils.is_qt_object_valid(widget):
                widget.setFixedWidth(self.get_scaled_width(width))
        for button, width in self._scaled_icon_buttons:
            if ui_qt_utils.is_qt_object_valid(button):
                self.set_icon_button_size(button, width)
        if ui_qt_utils.is_qt_object_valid(self.preferences_panel):
            self.preferences_panel.update_icon_button_sizes()
        for name_field in self.name_fields.values():
            if ui_qt_utils.is_qt_object_valid(name_field):
                name_field.setMinimumWidth(self.get_scaled_width(self.CLIP_NAME_MINIMUM_WIDTH))
        for index_label in self.automation_index_labels:
            if ui_qt_utils.is_qt_object_valid(index_label):
                index_label.setFixedWidth(self.get_scaled_width(24))
        for row in self.clip_rows.values():
            if ui_qt_utils.is_qt_object_valid(row):
                row.setMinimumWidth(self.get_clip_row_minimum_width())
        if ui_qt_utils.is_qt_object_valid(self.clips_content):
            self.clips_content.setMinimumWidth(self.get_clip_row_minimum_width())
            self.clips_content.updateGeometry()
        if self.clips_layout:
            self.clips_layout.invalidate()
        self.updateGeometry()

    def get_workspace_control_name(self):
        """Gets the workspace-control name generated by MayaWindowMeta.

        Returns:
            str: Workspace-control name for this dockable view.
        """
        return "{0}WorkspaceControl".format(self.objectName())

    def window_exists(self):
        """Checks whether the dockable Qt view is visible and valid.

        Returns:
            bool: True when the view can receive UI updates.
        """
        return bool(ui_qt_utils.is_qt_object_valid(self) and self._ui_built)

    def closeEvent(self, event):
        """Stops controller-owned updates when this dockable view closes.

        Args:
            event (QCloseEvent): Qt close event.
        """
        if self.controller:
            self.controller.stop_timeline_sync()
            self.controller.teardown_scene_callbacks()
        self._ui_built = False
        super().closeEvent(event)

    def build_top_toolbar(self):
        """Builds the scene-info toolbar.

        Returns:
            QHBoxLayout: Toolbar layout.
        """
        toolbar_layout = ui_qt.QtWidgets.QHBoxLayout()
        toolbar_layout.setContentsMargins(2, 0, 2, 0)
        toolbar_layout.setSpacing(4)
        self.info_ui = ui_qt.QtWidgets.QLabel(self.get_scene_info())
        self.info_ui.setTextFormat(ui_qt.QtCore.Qt.RichText)
        self.info_ui.setMinimumWidth(0)
        self.info_ui.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        toolbar_layout.addWidget(self.info_ui, 1)
        toolbar_layout.addWidget(
            self.create_icon_button(
                icon_name="addClip.png",
                fallback_icon=ui_res_lib.Icon.ui_add,
                fallback_text="+",
                tooltip="Add New Clip\n(Uses the timeline range or the current frame)",
                callback=self.controller.add_clip,
                button_width=26,
            )
        )
        toolbar_layout.addWidget(
            self.create_icon_button(
                icon_name="refresh.png",
                fallback_icon=ui_res_lib.Icon.ui_reset,
                fallback_text="R",
                tooltip="Refresh Data",
                callback=lambda: self.controller.refresh(force=True),
                button_width=26,
            )
        )
        return toolbar_layout

    def build_timeline_splitter(self):
        """Builds the draggable container for the timeline and tracker tabs.

        Returns:
            QSplitter: Vertical splitter containing the timeline and tracker tabs.
        """
        splitter = ui_qt.QtWidgets.QSplitter(ui_qt.QtCore.Qt.Vertical)
        splitter.setMinimumSize(0, 0)
        splitter.setHandleWidth(TIMELINE_HANDLE_WIDTH)
        splitter.setChildrenCollapsible(False)
        splitter.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        splitter.addWidget(self.timeline_widget)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.restore_timeline_height(splitter=splitter)
        return splitter

    def build_clips_tab(self):
        """Builds the Animation Clips tab.

        Returns:
            QWidget: Clip-list tab content.
        """
        clips_tab = ui_qt.QtWidgets.QWidget()
        clips_tab.setMinimumSize(0, 0)
        clips_tab.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        tab_layout = ui_qt.QtWidgets.QVBoxLayout(clips_tab)
        tab_layout.setContentsMargins(6, 6, 6, 6)
        tab_layout.setSpacing(2)

        header = ui_qt.QtWidgets.QWidget()
        header.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        header_layout = ui_qt.QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)
        header_columns = [
            ("", self.CLIP_INDEX_WIDTH),
            ("", self.CLIP_ACTIVE_WIDTH),
            ("Clip Name", None),
            ("Start", self.CLIP_FRAME_WIDTH),
            ("End", self.CLIP_FRAME_WIDTH),
            ("Frames", self.CLIP_FRAME_WIDTH),
            ("", self.CLIP_ACTION_WIDTH),
            ("", self.CLIP_ACTION_WIDTH),
            ("", self.CLIP_ACTION_WIDTH),
        ]
        for label, width in header_columns:
            header_label = ui_qt.QtWidgets.QLabel(label)
            header_label.setStyleSheet("font-weight: bold;")
            header_label.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
            if width:
                self.register_scaled_width_widget(header_label, width)
                header_layout.addWidget(header_label)
            else:
                header_label.setAlignment(
                    ui_qt.QtCore.Qt.AlignLeft | ui_qt.QtCore.Qt.AlignVCenter
                )
                header_layout.addWidget(header_label, 1)
        tab_layout.addWidget(header)

        self.clips_scroll = ui_qt.QtWidgets.QScrollArea()
        self.clips_scroll.setWidgetResizable(True)
        self.clips_scroll.setFrameShape(ui_qt.QtWidgets.QFrame.NoFrame)
        self.clips_scroll.setHorizontalScrollBarPolicy(ui_qt.QtCore.Qt.ScrollBarAsNeeded)
        self.clips_scroll.setMinimumSize(0, 0)
        self.clips_scroll.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        self.clips_scroll.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        self.clips_scroll.customContextMenuRequested.connect(self.show_clips_popup)
        clips_content = ui_qt.QtWidgets.QWidget()
        clips_content.setMinimumWidth(self.get_clip_row_minimum_width())
        clips_content.setMinimumHeight(0)
        clips_content.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.MinimumExpanding,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        self.clips_content = clips_content
        self.clips_layout = ui_qt.QtWidgets.QVBoxLayout(clips_content)
        self.clips_layout.setContentsMargins(0, 0, 0, 0)
        self.clips_layout.setSpacing(2)
        self.clips_layout.addStretch()
        self.clips_scroll.setWidget(clips_content)
        tab_layout.addWidget(self.clips_scroll, 1)
        return clips_tab

    def build_preferences_tab(self):
        """Builds the preferences tab host.

        Returns:
            QScrollArea: Scrollable preferences tab content.
        """
        self.preferences_scroll = ui_qt.QtWidgets.QScrollArea()
        self.preferences_scroll.setWidgetResizable(True)
        self.preferences_scroll.setFrameShape(ui_qt.QtWidgets.QFrame.NoFrame)
        self.preferences_scroll.setHorizontalScrollBarPolicy(ui_qt.QtCore.Qt.ScrollBarAsNeeded)
        self.preferences_scroll.setMinimumSize(0, 0)
        self.preferences_scroll.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        return self.preferences_scroll

    def build_automations_tab(self):
        """Builds the scrollable Automations tab host.

        Returns:
            QScrollArea: Scrollable automation tab content.
        """
        self.automations_scroll = ui_qt.QtWidgets.QScrollArea()
        self.automations_scroll.setWidgetResizable(True)
        self.automations_scroll.setFrameShape(ui_qt.QtWidgets.QFrame.NoFrame)
        self.automations_scroll.setHorizontalScrollBarPolicy(
            ui_qt.QtCore.Qt.ScrollBarAsNeeded
        )
        self.automations_scroll.setMinimumSize(0, 0)
        self.automations_scroll.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Ignored,
        )
        self.automations_content = ui_qt.QtWidgets.QWidget()
        self.automations_content.setMinimumSize(0, 0)
        self.automations_content.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        self.automations_layout = ui_qt.QtWidgets.QVBoxLayout(
            self.automations_content
        )
        self.automations_layout.setContentsMargins(6, 6, 6, 6)
        self.automations_layout.setSpacing(4)
        self.automations_layout.setAlignment(ui_qt.QtCore.Qt.AlignTop)
        self.automations_scroll.setWidget(self.automations_content)
        return self.automations_scroll

    def clear_automations_ui(self):
        """Removes all dynamic controls from the Automations tab."""
        if self.automations_layout:
            self.clear_nested_layout(self.automations_layout)
        self.automation_checkboxes = {}
        self.automation_index_labels = []
        self.automation_empty_label = None

    def add_automation_empty_message(self, message):
        """Centers a prominent message in the Automations tab.

        Args:
            message (str): Empty-state message to display.
        """
        self.automations_layout.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        empty_label = ui_qt.QtWidgets.QLabel(message)
        empty_label.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        empty_label.setWordWrap(True)
        empty_label.setStyleSheet("color: #b0b0b0; padding: 12px;")
        message_font = empty_label.font()
        message_font.setPointSize(max(message_font.pointSize() + 2, 11))
        empty_label.setFont(message_font)
        self.automation_empty_label = empty_label
        self.automations_layout.addWidget(empty_label)

    def build_automations_ui(self):
        """Builds the available automation script controls."""
        if not self.automations_layout or not self.controller:
            return
        self.clear_automations_ui()
        self.automations_layout.setAlignment(ui_qt.QtCore.Qt.AlignTop)
        folder = str(self.controller.model.automation_path or "").strip(' "\'')
        if not folder or not os.path.isdir(folder):
            self.add_automation_empty_message(
                "Automations folder not found or path is empty."
            )
            return

        script_paths = sorted(find_glob_paths(os.path.join(folder, "*.py")))
        if not script_paths:
            self.add_automation_empty_message(
                f"No Python automation scripts were found in:\n{folder}"
            )
            return

        info_label = ui_qt.QtWidgets.QLabel(
            f"<b>Found {len(script_paths)} automation scripts</b><br>"
            f"<span style='color:gray'>{folder}</span>"
        )
        info_label.setWordWrap(True)
        self.automations_layout.addWidget(info_label)

        run_checked_button = ui_qt.QtWidgets.QPushButton("Run Checked")
        run_checked_button.setStyleSheet(
            "background-color: #b0b0b0; color: black; font-weight: bold; "
            "padding: 4px;"
        )
        run_checked_button.clicked.connect(self.controller.run_checked_automations)
        self.automations_layout.addWidget(run_checked_button)

        separator = ui_qt.QtWidgets.QFrame()
        separator.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        self.automations_layout.addWidget(separator)

        check_states = self.controller.model.get_automation_check_states(folder)
        for index, script_path in enumerate(script_paths, 1):
            row_layout = ui_qt.QtWidgets.QHBoxLayout()
            row_layout.setSpacing(4)
            script_name = os.path.basename(script_path)

            index_label = ui_qt.QtWidgets.QLabel(f"{index}.")
            index_label.setAlignment(
                ui_qt.QtCore.Qt.AlignRight | ui_qt.QtCore.Qt.AlignVCenter
            )
            self.automation_index_labels.append(index_label)
            index_label.setFixedWidth(self.get_scaled_width(24))
            row_layout.addWidget(index_label)

            check_box = ui_qt.QtWidgets.QCheckBox()
            check_box.setSizePolicy(
                ui_qt.QtWidgets.QSizePolicy.Fixed,
                ui_qt.QtWidgets.QSizePolicy.Fixed,
            )
            check_box.setChecked(check_states.get(script_name, True))
            check_box.setToolTip(
                "Include this automation when running checked scripts."
            )
            check_box.toggled.connect(
                partial(self.controller.set_automation_check_state, script_name)
            )
            self.automation_checkboxes[script_path] = check_box
            row_layout.addWidget(check_box)

            run_button = ui_qt.QtWidgets.QPushButton(script_name)
            run_button.clicked.connect(
                partial(self.controller.run_automation, script_path)
            )
            row_layout.addWidget(run_button, 1)

            edit_button = ui_qt.QtWidgets.QPushButton("Edit")
            edit_button.setStyleSheet("padding: 0 6px;")
            edit_button.setMinimumWidth(edit_button.sizeHint().width())
            edit_button.setSizePolicy(
                ui_qt.QtWidgets.QSizePolicy.Fixed,
                ui_qt.QtWidgets.QSizePolicy.Preferred,
            )
            edit_button.clicked.connect(
                partial(self.controller.open_automation_in_editor, script_path)
            )
            row_layout.addWidget(edit_button)
            self.automations_layout.addLayout(row_layout)

    def set_automation_path(self, automation_path):
        """Updates the displayed automation folder and script list.

        Args:
            automation_path (str): Automation folder path to display.
        """
        if self.preferences_panel:
            self.preferences_panel.set_automation_path(automation_path)
        self.build_automations_ui()

    def attach_preferences_panel(self):
        """Creates and connects the Qt preferences panel."""
        panel = clip_tracker_preferences.ClipPreferencesPanel(
            preferences=self.controller.model.get_preference_values(),
            parent=self.preferences_scroll,
        )
        panel.setMinimumSize(0, 0)
        panel.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        self.preferences_scroll.setWidget(panel)
        self.preferences_panel = panel
        panel.update_icon_button_sizes()
        self.controller.connect_preferences_panel(panel)

    def timeline_widget_alive(self):
        """Checks whether the timeline widget can receive updates.

        Returns:
            bool: True when the timeline widget is valid.
        """
        return ui_qt_utils.is_qt_object_valid(self.timeline_widget)

    def timeline_splitter_alive(self):
        """Checks whether the timeline splitter can receive updates.

        Returns:
            bool: True when the splitter is valid.
        """
        return ui_qt_utils.is_qt_object_valid(self.timeline_splitter)

    def get_timeline_splitter_handle(self):
        """Gets the splitter handle between the timeline and tracker tabs.

        Returns:
            QSplitterHandle or None: Draggable timeline divider when available.
        """
        if not self.timeline_splitter_alive():
            return None
        return self.timeline_splitter.handle(1)

    def remember_timeline_height(self):
        """Stores the timeline height before it is hidden.

        The stored size lets the timeline return to its last user-selected height
        when the Show Timeline preference is enabled again.
        """
        if not self.timeline_splitter_alive() or self.timeline_widget.isHidden():
            return
        splitter_sizes = self.timeline_splitter.sizes()
        if not splitter_sizes:
            return
        minimum_height = self.timeline_widget.minimumHeight()
        self._timeline_height = max(minimum_height, splitter_sizes[0])

    def restore_timeline_height(self, splitter=None):
        """Restores the timeline's saved height in its splitter.

        Args:
            splitter (QSplitter, optional): Splitter to resize. When omitted,
                the view's timeline splitter is used.
        """
        splitter = splitter or self.timeline_splitter
        if not ui_qt_utils.is_qt_object_valid(splitter):
            return
        minimum_height = self.timeline_widget.minimumHeight()
        timeline_height = max(minimum_height, self._timeline_height)
        total_height = splitter.height()
        if total_height <= 0:
            total_height = self.height()
        tabs_height = max(1, total_height - timeline_height - splitter.handleWidth())
        splitter.setSizes([timeline_height, tabs_height])

    def set_timeline_visible(self, is_visible):
        """Shows or hides the timeline and its resize divider without rebuilding.

        Args:
            is_visible (bool): Whether the timeline should be displayed.
        """
        if not self.timeline_widget_alive():
            return
        is_visible = bool(is_visible)
        splitter_handle = self.get_timeline_splitter_handle()
        if not is_visible:
            self.remember_timeline_height()
        self.timeline_widget.setVisible(is_visible)
        if splitter_handle:
            splitter_handle.setVisible(is_visible)
        if is_visible:
            self.restore_timeline_height()
            self.timeline_widget.update()

    def update_timeline(self):
        """Pushes clip data and interaction preferences into the timeline widget."""
        if not self.timeline_widget_alive():
            return
        model = self.controller.model
        self.timeline_widget.set_mode(model.timeline_mode)
        self.timeline_widget.set_show_names(model.timeline_show_names)
        self.timeline_widget.set_sync_time_on_edit(model.timeline_sync_time_edit)
        self.timeline_widget.set_allow_outside_range(model.timeline_allow_outside_range)
        self.timeline_widget.set_magnet_state(model.timeline_magnet_enabled, model.timeline_snap_tolerance)
        self.timeline_widget.set_clips(model.get_data())
        self.timeline_widget.set_selected_index(self.controller.selected_index)

    def get_scene_info(self):
        """Gets formatted scene information for the toolbar.

        Returns:
            str: Rich-text scene information.
        """
        cmds = get_maya_cmds()
        om = get_open_maya()
        scene_path = cmds.file(query=True, sceneName=True)
        scene_name = os.path.basename(scene_path) if scene_path else "Untitled"
        fps_numeric = om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())
        fps_string = str(int(fps_numeric)) if float(fps_numeric).is_integer() else "{0:.2f}".format(fps_numeric)
        last_edited = self.controller.model.last_edited if self.controller else ""
        return (
            '<font color="#999999">Scene:</font> <font color="#E0E0E0">{0}</font>   |   '
            '<font color="#999999">FPS:</font> <font color="#E0E0E0">{1}</font>   |   '
            '<font color="#999999">Data Updated:</font> <font color="#E0E0E0">{2}</font>'
        ).format(scene_name, fps_string, last_edited)

    def update_top_info(self):
        """Updates the toolbar scene information."""
        if self.window_exists() and self.info_ui:
            self.info_ui.setText(self.get_scene_info())

    def draw_clips(self, clips_data, playing_index=None):
        """Rebuilds Qt rows for the provided clip data.

        Args:
            clips_data (list): Clip dictionaries.
            playing_index (int, optional): Currently playing clip index.
        """
        if not self.clips_layout:
            return
        self.update_timeline()
        self.update_top_info()
        self.clear_clip_rows()
        issues = self.controller.model.get_clip_issues()
        for index, clip in enumerate(clips_data):
            self.draw_clip_row(index, clip, issues.get(index), playing_index)
        self.clips_layout.addStretch()
        self.highlight_clip_row(self.controller.selected_index)

    def clear_clip_rows(self):
        """Deletes all clip-row widgets from the scroll layout."""
        self.discard_clip_row_metrics()
        while self.clips_layout.count():
            item = self.clips_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.play_buttons = []
        self.duration_fields = []
        self.frame_fields = {}
        self.name_fields = {}
        self.index_labels = {}
        self.clip_rows = {}

    def discard_clip_row_metrics(self):
        """Removes DPI-metric references owned by clip rows being rebuilt."""
        clip_rows = tuple(self.clip_rows.values())
        if not clip_rows:
            return
        self._scaled_width_widgets = [
            (widget, width)
            for widget, width in self._scaled_width_widgets
            if not any(row is widget or row.isAncestorOf(widget) for row in clip_rows)
        ]
        self._scaled_icon_buttons = [
            (button, width)
            for button, width in self._scaled_icon_buttons
            if not any(row is button or row.isAncestorOf(button) for row in clip_rows)
        ]

    def draw_clip_row(self, index, clip, issues=None, playing_index=None):
        """Builds one editable clip row.

        Args:
            index (int): Clip index.
            clip (dict): Clip data.
            issues (dict, optional): Validation issue information.
            playing_index (int, optional): Currently playing clip index.
        """
        row = ui_qt.QtWidgets.QWidget()
        row.setMinimumHeight(30)
        row.setMinimumWidth(self.get_clip_row_minimum_width())
        row.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.MinimumExpanding,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        row_layout = ui_qt.QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(2)
        index_label = self.create_fixed_label(str(index + 1), self.CLIP_INDEX_WIDTH)
        index_label.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        index_label.customContextMenuRequested.connect(
            partial(self.show_clip_order_popup, index_label, index)
        )
        self.index_labels[index] = index_label
        row_layout.addWidget(index_label)

        active_checkbox = ui_qt.QtWidgets.QCheckBox()
        active_checkbox.setChecked(bool(clip.get("active")))
        self.register_scaled_width_widget(active_checkbox, self.CLIP_ACTIVE_WIDTH)
        active_checkbox.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        active_checkbox.customContextMenuRequested.connect(
            partial(self.show_clip_order_popup, active_checkbox, index)
        )
        active_checkbox.toggled.connect(partial(self.controller.update_clip_val, index, "active"))
        row_layout.addWidget(active_checkbox)

        name_field = ui_qt.QtWidgets.QLineEdit(str(clip.get("name") or ""))
        name_field.setObjectName("ClipTrackerNameField")
        name_field.setMinimumWidth(self.get_scaled_width(self.CLIP_NAME_MINIMUM_WIDTH))
        name_field.setPlaceholderText("Enter clip name...")
        name_field.editingFinished.connect(
            lambda field=name_field, clip_index=index: self.controller.update_clip_val(
                clip_index,
                "name",
                field.text(),
            )
        )
        self.name_fields[index] = name_field
        row_layout.addWidget(name_field, 1)

        start_field = self.create_frame_field(index, "start", clip.get("start", 0))
        end_field = self.create_frame_field(index, "end", clip.get("end", 0))
        self.frame_fields[(index, "start")] = start_field
        self.frame_fields[(index, "end")] = end_field
        row_layout.addWidget(start_field)
        row_layout.addWidget(end_field)

        duration_field = self.create_duration_field()
        self.duration_fields.append(duration_field)
        row_layout.addWidget(duration_field)
        self.set_duration_display(duration_field, clip, issues)
        row_layout.addWidget(
            self.create_icon_button(
                icon_name="adjustTimeline.png",
                fallback_icon=ui_res_lib.Icon.ui_goto_location,
                fallback_text="R",
                tooltip="Set Timeline Range",
                callback=partial(self.controller.set_range, index),
            )
        )
        is_playing = playing_index == index
        play_button = self.create_icon_button(
            icon_name="pause_S.png" if is_playing else "timeplay.png",
            fallback_icon=ui_res_lib.Icon.ui_reset if is_playing else ui_res_lib.Icon.ui_arrow_right,
            fallback_text="II" if is_playing else ">",
            tooltip="Play/Pause Clip",
            callback=partial(self.controller.toggle_play, index),
        )
        self.play_buttons.append(play_button)
        row_layout.addWidget(play_button)
        row_layout.addWidget(
            self.create_icon_button(
                icon_name="smallTrash.png",
                fallback_icon=ui_res_lib.Icon.ui_trash,
                fallback_text="X",
                tooltip="Delete Clip",
                callback=partial(self.controller.delete_clip, index),
            )
        )
        self.clip_rows[index] = row
        self.clips_layout.addWidget(row)

    def create_frame_field(self, index, key, value):
        """Creates a frame spin box and its context menu.

        Args:
            index (int): Clip index.
            key (str): Clip frame key.
            value (int): Current frame value.

        Returns:
            QSpinBox: Configured frame spin box.
        """
        field = ui_qt.QtWidgets.QSpinBox()
        field.setRange(FRAME_FIELD_MINIMUM, FRAME_FIELD_MAXIMUM)
        field.setValue(int(value))
        field.setObjectName("ClipTrackerFrameField")
        self.register_scaled_width_widget(field, self.CLIP_FRAME_WIDTH)
        field.editingFinished.connect(
            lambda frame_field=field, clip_index=index, clip_key=key: self.controller.update_clip_val(
                clip_index,
                clip_key,
                frame_field.value(),
            )
        )
        field.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        field.customContextMenuRequested.connect(
            partial(self.show_frame_popup, field, index, key)
        )
        return field

    def create_fixed_label(self, text, width):
        """Creates a fixed-width row label.

        Args:
            text (str): Label text.
            width (int): Fixed widget width in pixels.

        Returns:
            QLabel: Configured label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        self.register_scaled_width_widget(label, width)
        return label

    def create_duration_field(self):
        """Creates the read-only duration field used by a clip row.

        Returns:
            QLineEdit: Configured duration display.
        """
        duration_field = ui_qt.QtWidgets.QLineEdit()
        duration_field.setObjectName("ClipTrackerDurationField")
        duration_field.setReadOnly(True)
        duration_field.setAlignment(ui_qt.QtCore.Qt.AlignCenter)
        self.register_scaled_width_widget(duration_field, self.CLIP_FRAME_WIDTH)
        return duration_field

    @staticmethod
    def get_icon(icon_name, fallback_icon):
        """Finds a Maya icon and falls back to a packaged GT icon.

        Args:
            icon_name (str): Maya image resource name.
            fallback_icon (str): Packaged icon file path.

        Returns:
            QIcon: Resolved icon.
        """
        for icon_path in (":/{0}".format(icon_name), icon_name):
            icon = ui_qt.QtGui.QIcon(icon_path)
            if not icon.isNull():
                return icon
        return ui_qt.QtGui.QIcon(fallback_icon)

    def create_icon_button(
        self,
        icon_name,
        fallback_icon,
        fallback_text,
        tooltip,
        callback,
        button_width=None,
    ):
        """Creates an icon-based action button using Maya's familiar imagery.

        Args:
            icon_name (str): Maya image resource name.
            fallback_icon (str): Packaged icon file path.
            fallback_text (str): Text shown when no icon can be resolved.
            tooltip (str): Hover description.
            callback (callable): Function called when clicked.
            button_width (int, optional): Fixed square button size.

        Returns:
            QToolButton: Configured action button.
        """
        button = ui_qt.QtWidgets.QToolButton()
        button.setObjectName("ClipTrackerIconButton")
        button.setToolTip(tooltip)
        button_size = int(button_width or self.CLIP_ACTION_WIDTH)
        self._scaled_icon_buttons.append((button, button_size))
        self.set_icon_button_size(button, button_size)
        icon = self.get_icon(icon_name, fallback_icon)
        if icon.isNull():
            button.setText(fallback_text)
        else:
            button.setIcon(icon)
        button.clicked.connect(lambda *args: callback())
        return button

    def set_duration_display(self, duration_field, clip, issue=None):
        """Updates a duration label and its validation appearance.

        Args:
            duration_field (QLineEdit): Duration display field.
            clip (dict): Clip data.
            issue (dict, optional): Validation issue information.
        """
        duration = int(clip.get("end", 0)) - int(clip.get("start", 0)) + 1
        duration_field.setText(str(duration))
        duration_field.setToolTip("Duration in frames.")
        background = "rgb(59, 59, 59)"
        if not issue:
            duration_field.setStyleSheet(self.get_duration_style(background))
            return
        duration_field.setToolTip("\n".join(issue.get("messages") or []))
        background = ISSUE_ERROR_COLOR if issue.get("severity") == "error" else ISSUE_WARNING_COLOR
        duration_field.setStyleSheet(self.get_duration_style(background))

    @staticmethod
    def get_duration_style(background):
        """Builds the duration-field styling used for normal and warning states.

        Args:
            background (str): CSS color for the field background.

        Returns:
            str: Qt stylesheet fragment.
        """
        return (
            "QLineEdit {{ background-color: {0}; border: 1px solid rgb(31, 31, 31); "
            "padding: 0 3px; min-height: 26px; }}"
        ).format(background)

    def highlight_clip_row(self, selected_index, scroll_into_view=False):
        """Highlights the row selected by the timeline.

        Args:
            selected_index (int): Clip index or negative value to clear selection.
            scroll_into_view (bool, optional): Whether to reveal the selected row.
        """
        selected_index = int(selected_index)
        if not self.controller.model.show_timeline:
            selected_index = -1
            scroll_into_view = False
        for index, name_field in self.name_fields.items():
            is_selected = index == selected_index
            name_field.setStyleSheet(
                "QLineEdit { background-color: %s; }" % SELECTED_ROW_COLOR
                if is_selected
                else ""
            )
            self.update_index_label(index, is_selected)
        if scroll_into_view and selected_index >= 0:
            self.scroll_clip_row_into_view(selected_index)

    def update_index_label(self, index, is_selected):
        """Updates the color of one row index label.

        Args:
            index (int): Clip index.
            is_selected (bool): Whether the row is selected.
        """
        label = self.index_labels.get(index)
        if not label:
            return
        label.setText(str(index + 1))
        label.setStyleSheet(
            "color: {0}; font-weight: bold;".format(SELECTED_ROW_LABEL_COLOR)
            if is_selected
            else ""
        )

    def scroll_clip_row_into_view(self, selected_index):
        """Scrolls the selected clip row into view.

        Args:
            selected_index (int): Clip index to reveal.
        """
        row = self.clip_rows.get(selected_index)
        if row and self.clips_scroll:
            self.clips_scroll.ensureWidgetVisible(row, 0, 20)

    def show_clip_order_popup(self, widget, index, position):
        """Shows clip-order actions for a row number or active check box.

        Args:
            widget (QWidget): Widget that received the context-menu request.
            index (int): Current clip index.
            position (QPoint): Widget-local context-menu position.
        """
        clip_count = len(self.controller.model.get_data())
        menu = ui_qt.QtWidgets.QMenu(widget)
        move_up_action = menu.addAction("Move Clip Up")
        move_up_action.setEnabled(index > 0)
        move_up_action.triggered.connect(partial(self.controller.move_clip, index, -1))
        move_down_action = menu.addAction("Move Clip Down")
        move_down_action.setEnabled(index < clip_count - 1)
        move_down_action.triggered.connect(partial(self.controller.move_clip, index, 1))
        self.execute_menu(menu, widget.mapToGlobal(position))

    def show_clips_popup(self, position):
        """Shows clip-list actions at the requested scroll-area position.

        Args:
            position (QPoint): Scroll-area position.
        """
        menu = ui_qt.QtWidgets.QMenu(self)
        menu.addAction("Add New Clip", self.controller.add_clip)
        menu.addAction("Add Timeline Range as Clip", self.controller.add_timeline_clip)
        menu.addSeparator()
        menu.addAction("Refresh Clip List", lambda: self.controller.refresh(force=True))
        self.execute_menu(menu, self.clips_scroll.viewport().mapToGlobal(position))

    def show_frame_popup(self, field, index, key, position):
        """Shows frame-field actions at the requested position.

        Args:
            field (QSpinBox): Frame field receiving the menu.
            index (int): Clip index.
            key (str): Clip frame key.
            position (QPoint): Field-local menu position.
        """
        menu = ui_qt.QtWidgets.QMenu(field)
        menu.addAction(
            "Set to Current Time",
            partial(self.controller.modify_frame_from_popup, index, key, "current", field),
        )
        menu.addAction("Go to Frame", partial(self.controller.go_to_frame, index, key, field))
        menu.addAction(
            "Increment",
            partial(self.controller.modify_frame_from_popup, index, key, "increment", field),
        )
        menu.addAction(
            "Decrement",
            partial(self.controller.modify_frame_from_popup, index, key, "decrement", field),
        )
        self.execute_menu(menu, field.mapToGlobal(position))

    @staticmethod
    def execute_menu(menu, position):
        """Executes a Qt menu across supported Qt versions.

        Args:
            menu (QMenu): Menu to execute.
            position (QPoint): Global menu position.
        """
        if hasattr(menu, "exec_"):
            menu.exec_(position)
        else:
            menu.exec(position)

    def update_frame_field(self, index, key, value, field=None):
        """Updates one frame spin box without rebuilding rows.

        Args:
            index (int): Clip index.
            key (str): Clip frame key.
            value (int): New frame value.
            field (QSpinBox, optional): Explicit frame field.
        """
        field = field or self.frame_fields.get((index, key))
        if not ui_qt_utils.is_qt_object_valid(field):
            return
        field.blockSignals(True)
        field.setValue(int(value))
        field.blockSignals(False)

    def get_frame_field_value(self, index, key, field=None):
        """Gets the value currently displayed in a frame spin box.

        Args:
            index (int): Clip index.
            key (str): Clip frame key.
            field (QSpinBox, optional): Explicit frame field.

        Returns:
            int or None: Current displayed value when available.
        """
        field = field or self.frame_fields.get((index, key))
        if not ui_qt_utils.is_qt_object_valid(field):
            return None
        return int(field.value())

    def update_duration_field(self, index, start_frame, end_frame):
        """Updates one duration label.

        Args:
            index (int): Clip index.
            start_frame (int): Start frame.
            end_frame (int): End frame.
        """
        if index >= len(self.duration_fields):
            return
        duration_field = self.duration_fields[index]
        if not ui_qt_utils.is_qt_object_valid(duration_field):
            return
        duration_field.setText(str(int(end_frame) - int(start_frame) + 1))

    def refresh_duration_fields(self):
        """Refreshes duration values and validation appearances."""
        if not self.window_exists():
            return
        self.update_timeline()
        clips_data = self.controller.model.get_data()
        issues = self.controller.model.get_clip_issues()
        for index, duration_field in enumerate(self.duration_fields):
            if index >= len(clips_data):
                continue
            if ui_qt_utils.is_qt_object_valid(duration_field):
                self.set_duration_display(duration_field, clips_data[index], issues.get(index))

    def update_play_icons(self, playing_index):
        """Updates play/pause button icons.

        Args:
            playing_index (int): Currently playing clip index.
        """
        for index, button in enumerate(self.play_buttons):
            if ui_qt_utils.is_qt_object_valid(button):
                is_playing = playing_index == index
                icon = self.get_icon(
                    "pause_S.png" if is_playing else "timeplay.png",
                    ui_res_lib.Icon.ui_reset if is_playing else ui_res_lib.Icon.ui_arrow_right,
                )
                if icon.isNull():
                    button.setText("II" if is_playing else ">")
                else:
                    button.setText("")
                    button.setIcon(icon)

    def apply_stylesheet(self):
        """Applies styling only to Clip Tracker row widgets."""
        self.setStyleSheet(
            "QLineEdit#ClipTrackerNameField { min-height: 26px; padding: 0 5px; }"
            "QSpinBox#ClipTrackerFrameField { min-height: 26px; padding: 0 3px; }"
            "QLineEdit#ClipTrackerDurationField { background-color: rgb(59, 59, 59); "
            "border: 1px solid rgb(31, 31, 31); padding: 0 3px; min-height: 26px; }"
            "QToolButton#ClipTrackerIconButton { border: 1px solid transparent; padding: 1px; }"
            "QToolButton#ClipTrackerIconButton:hover { border-color: rgb(105, 105, 105); }"
        )


if __name__ == "__main__":
    from gt.tools.anim_clip_tracker import launch_tool

    launch_tool()
