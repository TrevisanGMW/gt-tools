"""
Animation Clip Tracker View
"""
from gt.tools.anim_clip_tracker import clip_tracker_preferences
from gt.tools.anim_clip_tracker import clip_tracker_timeline
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import os


TIMELINE_HEIGHT = 110
PREFERENCES_HEIGHT = 320
SELECTED_ROW_COLOR = [0.30, 0.26, 0.12]
SELECTED_ROW_LABEL_COLOR = "#FFC832"
MAX_SCROLL_PIXELS = 100000


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


class ClipTrackerView:
    """Builds the Animation Clip Tracker UI."""

    WINDOW_NAME = "GTClipTrackerWindow"
    CLIP_COLUMNS = [(1, 15), (2, 20), (3, 20), (4, 140), (5, 60), (6, 60), (7, 60), (8, 30), (9, 30), (10, 30)]

    def __init__(self, version=None):
        """Initializes the clip tracker view.

        Args:
            version (str, optional): Tool version.
        """
        self.version = version
        self.controller = None
        self.clips_layout = None
        self.info_ui = None
        self.play_buttons = []
        self.duration_fields = []
        self.frame_fields = {}
        self.default_bg = [0.17, 0.17, 0.17]
        self.default_name_bg = None
        self.name_fields = {}
        self.index_labels = {}
        self.clip_rows = {}
        self.clips_scroll = None
        self.preferences_frame = None
        self.timeline_host = None
        self.timeline_widget = None
        self.preferences_host = None
        self.preferences_panel = None

    def build_ui(self):
        """Builds the Maya UI."""
        cmds = get_maya_cmds()
        if cmds.window(self.WINDOW_NAME, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)
        model = self.controller.model
        title = "Animation Clip Tracker"
        if self.version:
            title += " - (v{0})".format(self.version)
        self.timeline_host = None
        self.timeline_widget = None
        self.preferences_host = None
        self.preferences_panel = None
        cmds.window(self.WINDOW_NAME, title=title, widthHeight=(780, 710))
        main_form = cmds.formLayout()
        top_form = self.build_top_toolbar(parent=main_form)
        clips_frame = self.build_clips_frame(parent=main_form)
        preferences_frame = self.build_preferences_frame(parent=main_form)
        attach_form = [
            (top_form, "top", 5),
            (top_form, "left", 0),
            (top_form, "right", 0),
            (clips_frame, "left", 8),
            (clips_frame, "right", 8),
            (preferences_frame, "left", 8),
            (preferences_frame, "right", 8),
            (preferences_frame, "bottom", 8),
        ]
        attach_control = [(clips_frame, "bottom", 5, preferences_frame)]
        attach_none = [(top_form, "bottom"), (preferences_frame, "top")]
        if model.show_timeline:
            self.timeline_host = self.build_timeline_host(parent=main_form)
            attach_form.extend([(self.timeline_host, "left", 8), (self.timeline_host, "right", 8)])
            attach_control.extend(
                [
                    (self.timeline_host, "top", 5, top_form),
                    (clips_frame, "top", 5, self.timeline_host),
                ]
            )
            attach_none.append((self.timeline_host, "bottom"))
        else:
            attach_control.append((clips_frame, "top", 5, top_form))
        cmds.formLayout(
            main_form,
            edit=True,
            attachForm=attach_form,
            attachControl=attach_control,
            attachNone=attach_none,
        )
        cmds.showWindow(self.WINDOW_NAME)
        self.apply_window_icon()
        self.attach_preferences_panel()
        if model.show_timeline:
            self.attach_timeline_widget()

    def window_exists(self):
        """Checks whether the tool window still exists.

        Returns:
            bool: True if the Maya window exists.
        """
        cmds = get_maya_cmds()
        return bool(cmds.window(self.WINDOW_NAME, exists=True))

    def clips_layout_exists(self):
        """Checks whether the clip list layout still exists.

        Returns:
            bool: True if the clip list layout can receive UI edits.
        """
        cmds = get_maya_cmds()
        if not self.window_exists() or not self.clips_layout:
            return False
        try:
            return bool(cmds.layout(self.clips_layout, exists=True))
        except RuntimeError:
            return False

    def apply_window_icon(self):
        """Applies the menu icon to the Maya window when Qt access is available."""
        try:
            from maya import OpenMayaUI

            pointer = OpenMayaUI.MQtUtil.findWindow(self.WINDOW_NAME)
            if not pointer:
                return
            widget = ui_qt.shiboken.wrapInstance(int(pointer), ui_qt.QtWidgets.QWidget)
            widget.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_clip_tracker))
        except Exception:
            pass

    def build_top_toolbar(self, parent):
        """Builds the top toolbar.

        Args:
            parent (str): Parent layout.

        Returns:
            str: Created layout.
        """
        cmds = get_maya_cmds()
        top_form = cmds.formLayout(parent=parent, height=30)
        self.info_ui = cmds.text(parent=top_form, label=self.get_scene_info(), font="plainLabelFont")

        btn_refresh = cmds.symbolButton(
            parent=top_form,
            image="refresh.png",
            annotation="Refresh Data",
            width=26,
            height=26,
            # Pass force=True to ensure manual clicks always rebuild the UI
            command=lambda x: self.controller.refresh(force=True),
        )
        btn_add = cmds.symbolButton(
            parent=top_form,
            image="addClip.png",
            annotation="Add New Clip\n(Uses the timeline range or the current frame)",
            width=26,
            height=26,
            command=lambda x: self.controller.add_clip(),
        )
        cmds.formLayout(
            top_form,
            edit=True,
            attachForm=[
                (self.info_ui, "top", 8),
                (self.info_ui, "left", 10),
                (btn_add, "top", 2),
                (btn_add, "right", 10),
                (btn_refresh, "top", 2),
            ],
            attachControl=[(btn_refresh, "right", 5, btn_add)],
        )
        return top_form

    def build_timeline_host(self, parent):
        """Builds the layout that hosts the Qt timeline widget.

        Args:
            parent (str): Parent layout.

        Returns:
            str: Created layout.
        """
        cmds = get_maya_cmds()
        host = cmds.columnLayout(parent=parent, adjustableColumn=True, height=TIMELINE_HEIGHT, rowSpacing=0)
        cmds.setParent(parent)
        return host

    def attach_timeline_widget(self):
        """Creates the Qt timeline widget inside the timeline host layout."""
        if not self.timeline_host:
            return
        try:
            host_widget = self.wrap_host_layout(self.timeline_host)
            if not host_widget:
                self.controller.model.log("Unable to find the timeline host layout.")
                return
            host_layout = self.get_host_layout(host_widget)
            widget = clip_tracker_timeline.ClipTimelineWidget(parent=host_widget)
            host_layout.addWidget(widget)
            widget.show()
            self.timeline_widget = widget
            self.controller.connect_timeline(widget)
            self.update_timeline()
        except Exception as exception:
            self.timeline_widget = None
            self.controller.model.log("Unable to build the timeline view: {0}".format(exception))

    def timeline_widget_alive(self):
        """Checks whether the Qt timeline widget can still receive updates.

        Returns:
            bool: True when the timeline widget exists and was not deleted.
        """
        if not self.timeline_widget:
            return False
        try:
            return bool(ui_qt.shiboken.isValid(self.timeline_widget))
        except Exception:
            return False

    def update_timeline(self):
        """Pushes clip data and the interaction mode into the timeline widget."""
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

    def build_clips_frame(self, parent):
        """Builds the clips frame.

        Args:
            parent (str): Parent layout.

        Returns:
            str: Created frame.
        """
        cmds = get_maya_cmds()
        frame = cmds.frameLayout(parent=parent, label="Animation Clips", collapsable=True, collapse=False)
        frame_form = cmds.formLayout()
        header_row = cmds.rowLayout(numberOfColumns=10, columnWidth=self.CLIP_COLUMNS, adjustableColumn=4)
        for label in ["", "", "", "Clip Name", "Start", "End", "Frames", "", "", ""]:
            cmds.text(label=label, align="left", font="boldLabelFont")
        cmds.setParent("..")
        clips_scroll = cmds.scrollLayout(childResizable=True)
        self.clips_scroll = clips_scroll
        self.add_clips_popup(parent=clips_scroll)
        self.clips_layout = cmds.columnLayout(adjustableColumn=True)
        cmds.setParent("..")
        cmds.setParent("..")
        cmds.formLayout(
            frame_form,
            edit=True,
            attachForm=[
                (header_row, "top", 0),
                (header_row, "left", 0),
                (header_row, "right", 0),
                (clips_scroll, "bottom", 0),
                (clips_scroll, "left", 0),
                (clips_scroll, "right", 0),
            ],
            attachControl=[(clips_scroll, "top", 0, header_row)],
        )
        cmds.setParent(parent)
        return frame

    def build_preferences_frame(self, parent):
        """Builds the frame that hosts the Qt preferences panel.

        Args:
            parent (str): Parent layout.

        Returns:
            str: Created frame.
        """
        cmds = get_maya_cmds()
        model = self.controller.model
        self.preferences_frame = cmds.frameLayout(
            parent=parent,
            label="Preferences",
            collapsable=True,
            collapse=bool(model.preferences_collapsed),
            collapseCommand=lambda *args: self.controller.set_preferences_collapsed(True),
            expandCommand=lambda *args: self.controller.set_preferences_collapsed(False),
        )
        self.preferences_host = cmds.columnLayout(
            parent=self.preferences_frame,
            adjustableColumn=True,
            height=PREFERENCES_HEIGHT,
            rowSpacing=0,
        )
        cmds.setParent(parent)
        return self.preferences_frame

    def attach_preferences_panel(self):
        """Creates the Qt preferences panel inside the preferences host layout."""
        cmds = get_maya_cmds()
        if not self.preferences_host:
            return
        try:
            host_widget = self.wrap_host_layout(self.preferences_host)
            if not host_widget:
                return
            host_layout = self.get_host_layout(host_widget)
            panel = clip_tracker_preferences.ClipPreferencesPanel(
                preferences=self.controller.model.get_preference_values(),
                parent=host_widget,
            )
            host_layout.addWidget(panel)
            panel.show()
            self.preferences_panel = panel
            self.controller.connect_preferences_panel(panel)
            panel_height = max(panel.sizeHint().height(), panel.minimumSizeHint().height())
            cmds.columnLayout(self.preferences_host, edit=True, height=panel_height + 4)
        except Exception as exception:
            self.preferences_panel = None
            self.controller.model.log("Unable to build the preferences panel: {0}".format(exception))

    @staticmethod
    def wrap_host_layout(layout_name):
        """Wraps a Maya layout into a Qt widget.

        Args:
            layout_name (str): Maya layout name.

        Returns:
            QWidget or None: Wrapped widget, or None when the layout was not found.
        """
        from maya import OpenMayaUI

        pointer = OpenMayaUI.MQtUtil.findControl(layout_name)
        if not pointer:
            pointer = OpenMayaUI.MQtUtil.findLayout(layout_name)
        if not pointer:
            return None
        return ui_qt.shiboken.wrapInstance(int(pointer), ui_qt.QtWidgets.QWidget)

    @staticmethod
    def get_host_layout(host_widget):
        """Gets the Qt layout used to add widgets to a Maya layout.

        Args:
            host_widget (QWidget): Wrapped Maya layout.

        Returns:
            QLayout: Layout that can receive Qt widgets.
        """
        host_layout = host_widget.layout()
        if host_layout is None:
            host_layout = ui_qt.QtWidgets.QVBoxLayout(host_widget)
        host_layout.setContentsMargins(0, 0, 0, 0)
        return host_layout

    def get_scene_info(self):
        """Gets scene info label text.

        Returns:
            str: Rich text scene info.
        """
        cmds = get_maya_cmds()
        om = get_open_maya()
        scene_path = cmds.file(query=True, sceneName=True)
        scene_name = os.path.basename(scene_path) if scene_path else "Untitled"
        fps_numeric = om.MTime(1.0, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())
        fps_string = str(int(fps_numeric)) if float(fps_numeric).is_integer() else "{0:.2f}".format(fps_numeric)
        label_color = "#999999"
        value_color = "#E0E0E0"
        return (
            '<font color="{0}">Scene:</font> <font color="{1}">{2}</font>   |   '
            '<font color="{0}">FPS:</font> <font color="{1}">{3}</font>   |   '
            '<font color="{0}">Data Updated:</font> <font color="{1}">{4}</font>'
        ).format(label_color, value_color, scene_name, fps_string, self.controller.model.last_edited)

    def update_top_info(self):
        """Updates the top info label."""
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        if self.info_ui and cmds.text(self.info_ui, query=True, exists=True):
            cmds.text(self.info_ui, edit=True, label=self.get_scene_info())

    def draw_clips(self, clips_data, playing_index=None):
        """Draws clip rows.

        Args:
            clips_data (list): Clip dictionaries.
            playing_index (int, optional): Currently playing clip index.
        """
        cmds = get_maya_cmds()
        self.update_timeline()
        if not self.clips_layout_exists():
            return
        self.update_top_info()
        children = cmds.layout(self.clips_layout, query=True, childArray=True)
        for child in children or []:
            cmds.deleteUI(child)
        cmds.setParent(self.clips_layout)
        self.play_buttons = []
        self.duration_fields = []
        self.frame_fields = {}
        self.name_fields = {}
        self.index_labels = {}
        self.clip_rows = {}
        issues = self.controller.model.get_clip_issues()
        for index, clip in enumerate(clips_data):
            self.draw_clip_row(index=index, clip=clip, issues=issues.get(index), playing_index=playing_index)
        self.highlight_clip_row(self.controller.selected_index)

    def draw_clip_row(self, index, clip, issues=None, playing_index=None):
        """Draws one clip row.

        Args:
            index (int): Clip index.
            clip (dict): Clip data.
            issues (dict, optional): Validation issue data.
            playing_index (int, optional): Currently playing clip index.
        """
        cmds = get_maya_cmds()
        self.clip_rows[index] = cmds.rowLayout(
            numberOfColumns=10,
            columnWidth=self.CLIP_COLUMNS,
            adjustableColumn=4,
        )
        cmds.text(label="")
        self.index_labels[index] = cmds.text(label=str(index + 1))
        cmds.checkBox(
            label="",
            value=clip.get("active"),
            changeCommand=partial(self.controller.update_clip_val, index, "active"),
        )
        self.name_fields[index] = cmds.textField(
            text=clip.get("name") or "",
            placeholderText="Enter clip name...",
            changeCommand=partial(self.controller.update_clip_val, index, "name"),
        )
        if self.default_name_bg is None:
            self.default_name_bg = cmds.textField(self.name_fields[index], query=True, backgroundColor=True)
        start_field = cmds.intField(
            value=int(clip.get("start", 0)),
            changeCommand=partial(self.controller.update_clip_val, index, "start"),
        )
        self.frame_fields[(index, "start")] = start_field
        self.add_frame_popup(parent=start_field, index=index, key="start")
        end_field = cmds.intField(
            value=int(clip.get("end", 0)),
            changeCommand=partial(self.controller.update_clip_val, index, "end"),
        )
        self.frame_fields[(index, "end")] = end_field
        self.add_frame_popup(parent=end_field, index=index, key="end")
        duration = int(clip.get("end", 0)) - int(clip.get("start", 0)) + 1
        duration_field = cmds.textField(text=str(duration), editable=False)
        if not self.duration_fields:
            self.default_bg = cmds.textField(duration_field, query=True, backgroundColor=True) or self.default_bg
        background_color = self.default_bg
        tooltip = "Duration in frames."
        if issues:
            tooltip = "\n".join(issues.get("messages") or [])
            background_color = [0.55, 0.18, 0.18] if issues.get("severity") == "error" else [0.55, 0.36, 0.08]
        cmds.textField(duration_field, edit=True, backgroundColor=background_color, annotation=tooltip)
        self.duration_fields.append(duration_field)
        cmds.symbolButton(
            image="adjustTimeline.png",
            width=30,
            height=30,
            annotation="Set Timeline Range",
            command=partial(self.controller.set_range, index),
        )
        play_icon = "pause_S.png" if playing_index == index else "timeplay.png"
        play_btn = cmds.symbolButton(
            image=play_icon,
            width=30,
            height=30,
            annotation="Play/Pause Clip",
            command=partial(self.controller.toggle_play, index),
        )
        self.play_buttons.append(play_btn)
        cmds.symbolButton(
            image="smallTrash.png",
            width=30,
            height=30,
            annotation="Delete Clip",
            command=partial(self.controller.delete_clip, index),
        )
        cmds.setParent("..")

    def highlight_clip_row(self, selected_index, scroll_into_view=False):
        """Highlights the clip row matching the clip selected in the timeline.

        Args:
            selected_index (int): Clip index, or a negative value to clear the highlight.
            scroll_into_view (bool, optional): Whether the row should be scrolled into view.
        """
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        selected_index = int(selected_index)
        if not self.controller.model.show_timeline:
            # Without the timeline view there is no selection to mirror in the clip list
            selected_index = -1
            scroll_into_view = False
        for index, name_field in self.name_fields.items():
            try:
                if not cmds.textField(name_field, query=True, exists=True):
                    continue
            except RuntimeError:
                continue
            is_selected = index == selected_index
            background_color = SELECTED_ROW_COLOR if is_selected else self.default_name_bg
            if background_color:
                cmds.textField(name_field, edit=True, backgroundColor=background_color)
            self.update_index_label(index=index, is_selected=is_selected)
        if scroll_into_view and selected_index >= 0:
            self.scroll_clip_row_into_view(selected_index)

    def update_index_label(self, index, is_selected):
        """Updates the row number label of one clip row.

        Args:
            index (int): Clip index.
            is_selected (bool): Whether the row is highlighted.
        """
        cmds = get_maya_cmds()
        label_control = self.index_labels.get(index)
        if not label_control:
            return
        try:
            if not cmds.text(label_control, query=True, exists=True):
                return
        except RuntimeError:
            return
        number = str(index + 1)
        if is_selected:
            number = '<font color="{0}"><b>{1}</b></font>'.format(SELECTED_ROW_LABEL_COLOR, number)
        cmds.text(label_control, edit=True, label=number)

    def scroll_clip_row_into_view(self, selected_index):
        """Scrolls the clip list so a row becomes visible.

        Args:
            selected_index (int): Clip index to reveal.
        """
        cmds = get_maya_cmds()
        row_control = self.clip_rows.get(selected_index)
        if not self.clips_scroll or not row_control:
            return
        try:
            if not cmds.scrollLayout(self.clips_scroll, query=True, exists=True):
                return
            row_height = cmds.rowLayout(row_control, query=True, height=True) or 0
            visible_height = cmds.scrollLayout(self.clips_scroll, query=True, height=True) or 0
            # Scrolling is relative, so the list is moved back to the top first
            cmds.scrollLayout(self.clips_scroll, edit=True, scrollByPixel=("up", MAX_SCROLL_PIXELS))
            offset = int((selected_index * row_height) - (max(0, visible_height - row_height) / 2))
            if offset > 0:
                cmds.scrollLayout(self.clips_scroll, edit=True, scrollByPixel=("down", offset))
        except RuntimeError:
            return

    def add_clips_popup(self, parent):
        """Adds a popup menu with clip list shortcuts.

        Args:
            parent (str): Parent layout.
        """
        cmds = get_maya_cmds()
        cmds.popupMenu(parent=parent)
        cmds.menuItem(
            label="Add New Clip",
            command=lambda *args: self.controller.add_clip(),
        )
        cmds.menuItem(
            label="Add Timeline Range as Clip",
            command=lambda *args: self.controller.add_timeline_clip(),
        )
        cmds.menuItem(divider=True)
        cmds.menuItem(
            label="Refresh Clip List",
            command=lambda *args: self.controller.refresh(force=True),
        )

    def add_frame_popup(self, parent, index, key):
        """Adds a popup menu to a frame field.

        Args:
            parent (str): Parent field.
            index (int): Clip index.
            key (str): Clip key.
        """
        cmds = get_maya_cmds()
        cmds.popupMenu(parent=parent)
        cmds.menuItem(
            label="Set to Current Time",
            command=partial(self.controller.modify_frame_from_popup, index, key, "current", parent),
        )
        cmds.menuItem(
            label="Go to Frame",
            command=partial(self.controller.go_to_frame, index, key, parent),
        )
        cmds.menuItem(
            label="Increment",
            command=partial(self.controller.modify_frame_from_popup, index, key, "increment", parent),
        )
        cmds.menuItem(
            label="Decrement",
            command=partial(self.controller.modify_frame_from_popup, index, key, "decrement", parent),
        )

    def update_frame_field(self, index, key, value, field=None):
        """Updates one start or end frame field without rebuilding rows.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            value (int): New frame value.
            field (str, optional): Explicit Maya int field name to update.
        """
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        field = field or self.frame_fields.get((index, key))
        try:
            if field and cmds.intField(field, query=True, exists=True):
                cmds.intField(field, edit=True, value=int(value))
        except RuntimeError:
            return

    def get_frame_field_value(self, index, key, field=None):
        """Gets the value currently shown in a start or end frame field.

        Args:
            index (int): Clip index.
            key (str): Clip key.
            field (str, optional): Explicit Maya int field name to query.

        Returns:
            int or None: Field value, or None when the field is unavailable.
        """
        cmds = get_maya_cmds()
        if not self.window_exists():
            return None
        field = field or self.frame_fields.get((index, key))
        try:
            if field and cmds.intField(field, query=True, exists=True):
                return int(cmds.intField(field, query=True, value=True))
        except RuntimeError:
            return None
        return None

    def update_duration_field(self, index, start_frame, end_frame):
        """Updates one duration field.

        Args:
            index (int): Clip index.
            start_frame (int): Start frame.
            end_frame (int): End frame.
        """
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        if index < len(self.duration_fields):
            field = self.duration_fields[index]
            if cmds.textField(field, query=True, exists=True):
                cmds.textField(field, edit=True, text=str(int(end_frame) - int(start_frame) + 1))

    def refresh_duration_fields(self):
        """Refreshes duration values and validation colors without rebuilding rows."""
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        self.update_timeline()
        clips_data = self.controller.model.get_data()
        issues = self.controller.model.get_clip_issues()
        for index, field in enumerate(self.duration_fields):
            try:
                if not cmds.textField(field, query=True, exists=True):
                    continue
            except RuntimeError:
                continue
            if index >= len(clips_data):
                continue
            clip = clips_data[index]
            duration = int(clip.get("end", 0)) - int(clip.get("start", 0)) + 1
            tooltip = "Duration in frames."
            background_color = self.default_bg
            issue = issues.get(index)
            if issue:
                tooltip = "\n".join(issue.get("messages") or [])
                background_color = [0.55, 0.18, 0.18] if issue.get("severity") == "error" else [0.55, 0.36, 0.08]
            cmds.textField(
                field,
                edit=True,
                text=str(duration),
                backgroundColor=background_color,
                annotation=tooltip,
            )

    def update_play_icons(self, playing_index):
        """Updates play/pause icons.

        Args:
            playing_index (int): Currently playing index.
        """
        cmds = get_maya_cmds()
        if not self.window_exists():
            return
        for index, button in enumerate(self.play_buttons):
            if cmds.symbolButton(button, query=True, exists=True):
                icon = "pause_S.png" if playing_index == index else "timeplay.png"
                cmds.symbolButton(button, edit=True, image=icon)
