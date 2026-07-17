"""
Animation Clip Tracker View
"""

from functools import partial
import os

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib


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
        self.preferences_frame = None

    def build_ui(self):
        """Builds the Maya UI."""
        cmds = get_maya_cmds()
        if cmds.window(self.WINDOW_NAME, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)
        title = "Animation Clip Tracker"
        if self.version:
            title += " - (v{0})".format(self.version)
        cmds.window(self.WINDOW_NAME, title=title, widthHeight=(700, 520))
        main_form = cmds.formLayout()
        top_form = self.build_top_toolbar(parent=main_form)
        clips_frame = self.build_clips_frame(parent=main_form)
        preferences_frame = self.build_preferences_frame(parent=main_form)
        cmds.formLayout(
            main_form,
            edit=True,
            attachForm=[
                (top_form, "top", 5),
                (top_form, "left", 0),
                (top_form, "right", 0),
                (clips_frame, "left", 8),
                (clips_frame, "right", 8),
                (preferences_frame, "left", 8),
                (preferences_frame, "right", 8),
                (preferences_frame, "bottom", 8),
            ],
            attachControl=[
                (clips_frame, "top", 5, top_form),
                (clips_frame, "bottom", 5, preferences_frame),
            ],
            attachNone=[(top_form, "bottom"), (preferences_frame, "top")],
        )
        cmds.showWindow(self.WINDOW_NAME)
        self.apply_window_icon()

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
            command=lambda x: self.controller.refresh(),
        )
        btn_add = cmds.symbolButton(
            parent=top_form,
            image="addClip.png",
            annotation="Add Current Timeline as Clip",
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
        """Builds the preferences frame.

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
        main_column = cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 8))
        validation_row = cmds.formLayout(parent=main_column, height=30)
        validation_controls = []
        validation_controls.append(cmds.checkBox(
            parent=validation_row,
            label="Min Frames",
            value=bool(model.validate_min_frames),
            changeCommand=partial(self.controller.update_preference, "validate_min_frames"),
        ))
        validation_controls.append(cmds.intField(
            parent=validation_row,
            value=int(model.min_frames),
            changeCommand=partial(self.controller.update_preference, "min_frames"),
        ))
        validation_controls.append(cmds.checkBox(
            parent=validation_row,
            label="Max Frames",
            value=bool(model.validate_max_frames),
            changeCommand=partial(self.controller.update_preference, "validate_max_frames"),
        ))
        validation_controls.append(cmds.intField(
            parent=validation_row,
            value=int(model.max_frames),
            changeCommand=partial(self.controller.update_preference, "max_frames"),
        ))
        validation_controls.append(cmds.checkBox(
            parent=validation_row,
            label="Overlaps",
            value=bool(model.detect_overlaps),
            changeCommand=partial(self.controller.update_preference, "detect_overlaps"),
        ))
        self.apply_even_form_spacing(validation_row, validation_controls)

        options_row = cmds.formLayout(parent=main_column, height=30)
        option_controls = []
        option_controls.append(cmds.checkBox(
            parent=options_row,
            label="Refresh On Focus",
            value=bool(model.refresh_on_focus),
            changeCommand=partial(self.controller.update_preference, "refresh_on_focus"),
        ))
        option_controls.append(cmds.checkBox(
            parent=options_row,
            label="Auto Add Timeline",
            value=bool(model.auto_add_timeline_clip),
            changeCommand=partial(self.controller.update_preference, "auto_add_timeline_clip"),
        ))
        option_controls.append(cmds.checkBox(
            parent=options_row,
            label="Sync Bookmarks",
            value=bool(model.sync_time_slider_bookmarks),
            changeCommand=partial(self.controller.update_preference, "sync_time_slider_bookmarks"),
        ))
        option_controls.append(cmds.checkBox(
            parent=options_row,
            label="Auto Reorder",
            value=bool(model.auto_reorder_clips),
            changeCommand=partial(self.controller.update_preference, "auto_reorder_clips"),
        ))
        option_controls.append(cmds.checkBox(
            parent=options_row,
            label="Confirm Delete",
            value=bool(model.confirm_delete_clip),
            changeCommand=partial(self.controller.update_preference, "confirm_delete_clip"),
        ))
        self.apply_even_form_spacing(options_row, option_controls)

        action_row = cmds.formLayout(parent=main_column, height=42)
        action_controls = []
        action_controls.append(cmds.button(
            parent=action_row,
            label="Add Current Timeline",
            command=lambda *args: self.controller.add_clip(),
        ))
        action_controls.append(cmds.button(
            parent=action_row,
            label="Sync Time Slider Bookmarks",
            command=lambda *args: self.controller.sync_bookmarks(),
        ))
        action_controls.append(cmds.button(
            parent=action_row,
            label="Reorder Clips",
            command=lambda *args: self.controller.reorder_clips(),
        ))
        action_controls.append(cmds.button(
            parent=action_row,
            label="Import JSON...",
            command=lambda *args: self.controller.import_data(),
        ))
        action_controls.append(cmds.button(
            parent=action_row,
            label="Export JSON...",
            command=lambda *args: self.controller.export_data(),
        ))
        action_controls.append(cmds.button(
            parent=action_row,
            label="Reset Settings",
            command=lambda *args: self.controller.reset_preferences(),
        ))
        self.apply_even_form_spacing(action_row, action_controls, bottom_padding=8)
        cmds.setParent(parent)
        return self.preferences_frame

    @staticmethod
    def apply_even_form_spacing(
        form_layout,
        controls,
        side_padding=8,
        inner_padding=4,
        top_padding=2,
        bottom_padding=2,
    ):
        """Applies equal-width spacing to controls in a form layout.

        Args:
            form_layout (str): Form layout to edit.
            controls (list): Child controls to distribute.
            side_padding (int, optional): Left and right padding.
            inner_padding (int, optional): Padding between controls.
            top_padding (int, optional): Top padding.
            bottom_padding (int, optional): Bottom padding.
        """
        cmds = get_maya_cmds()
        controls = list(controls or [])
        control_count = len(controls)
        if not control_count:
            return
        attach_form = []
        attach_position = []
        for index, control in enumerate(controls):
            left_position = int(index * 100.0 / control_count)
            right_position = int((index + 1) * 100.0 / control_count)
            attach_form.append((control, "top", top_padding))
            attach_form.append((control, "bottom", bottom_padding))
            if index == 0:
                attach_form.append((control, "left", side_padding))
            else:
                attach_position.append((control, "left", inner_padding, left_position))
            if index == control_count - 1:
                attach_form.append((control, "right", side_padding))
            else:
                attach_position.append((control, "right", inner_padding, right_position))
        cmds.formLayout(
            form_layout,
            edit=True,
            attachForm=attach_form,
            attachPosition=attach_position,
        )

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
        issues = self.controller.model.get_clip_issues()
        for index, clip in enumerate(clips_data):
            self.draw_clip_row(index=index, clip=clip, issues=issues.get(index), playing_index=playing_index)

    def draw_clip_row(self, index, clip, issues=None, playing_index=None):
        """Draws one clip row.

        Args:
            index (int): Clip index.
            clip (dict): Clip data.
            issues (dict, optional): Validation issue data.
            playing_index (int, optional): Currently playing clip index.
        """
        cmds = get_maya_cmds()
        cmds.rowLayout(numberOfColumns=10, columnWidth=self.CLIP_COLUMNS, adjustableColumn=4)
        cmds.text(label="")
        cmds.text(label=str(index + 1))
        cmds.checkBox(
            label="",
            value=clip.get("active"),
            changeCommand=partial(self.controller.update_clip_val, index, "active"),
        )
        cmds.textField(
            text=clip.get("name") or "",
            placeholderText="Enter clip name...",
            changeCommand=partial(self.controller.update_clip_val, index, "name"),
        )
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
