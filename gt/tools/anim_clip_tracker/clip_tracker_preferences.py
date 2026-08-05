"""
Animation Clip Tracker Preferences Panel

A pure Qt panel with grouped preference areas.
This module must remain importable outside Maya, so it never imports "maya.cmds".
Values are provided by the caller and changes are reported through signals.
"""
import gt.ui.qt_import as ui_qt

from gt.tools.anim_clip_tracker.clip_tracker_constants import (
    MODE_LABELS,
    TIMELINE_MODES,
    get_valid_mode,
)


ACTION_SYNC_BOOKMARKS = "sync_bookmarks"
ACTION_REORDER_CLIPS = "reorder_clips"
ACTION_IMPORT_DATA = "import_data"
ACTION_EXPORT_DATA = "export_data"
ACTION_RESET_PREFERENCES = "reset_preferences"
ACTION_DELETE_SCENE_DATA = "delete_scene_data"

TOOLTIP_MIN_FRAMES = (
    "Warns when a clip is shorter than the minimum duration.\n"
    "The duration field of offending clips turns red."
)
TOOLTIP_MIN_FRAMES_VALUE = (
    "Minimum number of frames a clip should have.\n"
    'Only used when "Min Frames" is enabled.'
)
TOOLTIP_MAX_FRAMES = (
    "Warns when a clip is longer than the maximum duration.\n"
    "The duration field of offending clips turns red."
)
TOOLTIP_MAX_FRAMES_VALUE = (
    "Maximum number of frames a clip should have.\n"
    'Only used when "Max Frames" is enabled.'
)
TOOLTIP_OVERLAPS = (
    "Warns when two or more clips share frames.\n"
    "Overlapping clips get an orange duration field listing\n"
    "the clips they overlap."
)
TOOLTIP_SHOW_TIMELINE = (
    "Shows an interactive timeline above the clip list.\n"
    "Clip blocks can be selected, moved and resized there.\n"
    "Inverted clips (end frame before start frame) are drawn\n"
    "with orange stripes."
)
TOOLTIP_SHOW_NAMES = (
    "Draws the clip name in the middle of each timeline block.\n"
    "Clips without a name show their frame range instead,\n"
    "for example f0001-f0024."
)
TOOLTIP_SYNC_TIME_EDIT = (
    'Moves the current frame while using the timeline in "Edit" mode.\n'
    "Keep it on to preview where a new range will end while drawing it.\n"
    "When off, editing clips never changes the current frame.\n"
    'The "Navigate" and "Select" modes are not affected.'
)
TOOLTIP_ALLOW_OUTSIDE_RANGE = (
    "Allows clips to be moved and resized outside the timeline range\n"
    "in the timeline view, into the darker areas on both sides.\n"
    "When off, those areas are hidden and clips stop at the\n"
    "start and end of the timeline range."
)
TOOLTIP_TIMELINE_MODE = (
    "Controls what the left mouse button does in the timeline view.\n"
    "Navigate: drag anywhere to change the current frame.\n"
    "Select: click a clip to highlight it, drag the playhead to scrub.\n"
    "Edit: drag a clip edge to resize it, drag the middle to move it,\n"
    "and drag an empty area to create a new clip.\n"
    "Hold Ctrl while dragging for precision.\n"
    "Right-click the timeline for clip and creation actions."
)
TOOLTIP_REFRESH_ON_FOCUS = (
    "Reloads clip data from the scene whenever this window\n"
    "regains focus. Useful when clips change elsewhere or\n"
    "after opening another scene."
)
TOOLTIP_AUTO_ADD_TIMELINE = (
    "When refreshing, adds the current timeline range as a clip\n"
    'named "Timeline" if no clip already covers that exact range.'
)
TOOLTIP_SYNC_BOOKMARKS = (
    "When refreshing, imports Maya time slider bookmarks as clips.\n"
    "Ranges that already exist are skipped."
)
TOOLTIP_AUTO_REORDER = (
    "Keeps the clip list sorted by start frame, then end frame,\n"
    "every time clip data is saved."
)
TOOLTIP_CONFIRM_DELETE = "Asks for confirmation before deleting a clip."
TOOLTIP_NEW_CLIP_CURRENT_FRAME = (
    "New clips created with the + button start at the current frame\n"
    "instead of the timeline range start.\n"
    "The end frame stays at the timeline range end when that frame\n"
    "is later than the current frame."
)
TOOLTIP_BTN_SYNC_BOOKMARKS = (
    "Imports Maya time slider bookmarks as clips right now.\n"
    "Ranges that already exist are skipped."
)
TOOLTIP_BTN_REORDER = "Sorts the clip list by start frame, then end frame."
TOOLTIP_BTN_IMPORT = (
    "Replaces the clips stored in this scene with the clips\n"
    "read from a JSON file."
)
TOOLTIP_BTN_EXPORT = "Writes the clips stored in this scene to a JSON file."
TOOLTIP_BTN_RESET = (
    "Restores every preference in this section to its default value\n"
    "and rebuilds the window. Clip data is not affected."
)
TOOLTIP_BTN_DELETE_SCENE_DATA = (
    "Deletes the clip data node from the current scene,\n"
    "removing every clip stored in it.\n"
    "A confirmation is required and the action cannot be undone\n"
    "unless the scene is reopened without saving."
)


class ClipPreferencesPanel(ui_qt.QtWidgets.QWidget):
    """Grouped preference areas used by the Animation Clip Tracker."""

    preference_changed = ui_qt.QtCore.Signal(str, object)
    action_triggered = ui_qt.QtCore.Signal(str)

    def __init__(self, preferences, parent=None):
        """Initializes the preferences panel.

        Args:
            preferences (dict): Current preference values keyed by preference name.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.preferences = dict(preferences or {})
        self.mode_buttons = {}
        self.mode_button_group = None
        self.timeline_dependent_widgets = []
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 4)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.build_warnings_group())
        main_layout.addWidget(self.build_timeline_group())
        main_layout.addWidget(self.build_behavior_group())
        main_layout.addWidget(self.build_actions_group())
        self.update_timeline_dependent_widgets()

    # ------------------------------------------------------------------ helpers
    def build_group(self, label):
        """Builds an empty preference group.

        Args:
            label (str): Group title.

        Returns:
            tuple: Group box and its vertical layout.
        """
        group_box = ui_qt.QtWidgets.QGroupBox(label)
        group_layout = ui_qt.QtWidgets.QVBoxLayout(group_box)
        group_layout.setContentsMargins(8, 4, 8, 6)
        group_layout.setSpacing(4)
        return group_box, group_layout

    def build_check_box(self, label, key, tooltip):
        """Builds a check box bound to a preference.

        Args:
            label (str): Check box label.
            key (str): Preference key.
            tooltip (str): Check box tooltip.

        Returns:
            QCheckBox: Created check box.
        """
        check_box = ui_qt.QtWidgets.QCheckBox(label)
        check_box.setToolTip(tooltip)
        check_box.setChecked(bool(self.preferences.get(key)))
        check_box.toggled.connect(lambda state, name=key: self.preference_changed.emit(name, bool(state)))
        return check_box

    def build_spin_box(self, key, tooltip):
        """Builds a frame count spin box bound to a preference.

        Args:
            key (str): Preference key.
            tooltip (str): Spin box tooltip.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setToolTip(tooltip)
        spin_box.setRange(1, 100000)
        spin_box.setMaximumWidth(70)
        # Typed values are only reported once editing finishes
        spin_box.setKeyboardTracking(False)
        spin_box.setValue(int(self.preferences.get(key) or 1))
        spin_box.valueChanged.connect(lambda value, name=key: self.preference_changed.emit(name, int(value)))
        return spin_box

    def build_button(self, label, action, tooltip):
        """Builds an action button.

        Args:
            label (str): Button label.
            action (str): Action name reported when the button is clicked.
            tooltip (str): Button tooltip.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setToolTip(tooltip)
        button.clicked.connect(lambda *args, name=action: self.action_triggered.emit(name))
        return button

    @staticmethod
    def build_row(layout):
        """Adds an evenly spaced horizontal row to a layout.

        Args:
            layout (QVBoxLayout): Layout receiving the row.

        Returns:
            QHBoxLayout: Created row layout.
        """
        row_layout = ui_qt.QtWidgets.QHBoxLayout()
        row_layout.setSpacing(6)
        layout.addLayout(row_layout)
        return row_layout

    # ------------------------------------------------------------------- groups
    def build_warnings_group(self):
        """Builds the clip duration warning preferences.

        Returns:
            QGroupBox: Created group.
        """
        group_box, group_layout = self.build_group("Warnings")
        row_layout = self.build_row(group_layout)
        row_layout.addWidget(self.build_check_box("Min Frames", "validate_min_frames", TOOLTIP_MIN_FRAMES))
        row_layout.addWidget(self.build_spin_box("min_frames", TOOLTIP_MIN_FRAMES_VALUE))
        row_layout.addStretch()
        row_layout.addWidget(self.build_check_box("Max Frames", "validate_max_frames", TOOLTIP_MAX_FRAMES))
        row_layout.addWidget(self.build_spin_box("max_frames", TOOLTIP_MAX_FRAMES_VALUE))
        row_layout.addStretch()
        row_layout.addWidget(self.build_check_box("Overlaps", "detect_overlaps", TOOLTIP_OVERLAPS))
        return group_box

    def build_timeline_group(self):
        """Builds the timeline view preferences.

        Returns:
            QGroupBox: Created group.
        """
        group_box, group_layout = self.build_group("Timeline View")
        show_check_box = self.build_check_box("Show Timeline View", "show_timeline", TOOLTIP_SHOW_TIMELINE)
        show_check_box.toggled.connect(self.on_show_timeline_toggled)
        names_check_box = self.build_check_box("Show Clip Names", "timeline_show_names", TOOLTIP_SHOW_NAMES)
        sync_check_box = self.build_check_box(
            "Move Time While Editing",
            "timeline_sync_time_edit",
            TOOLTIP_SYNC_TIME_EDIT,
        )
        outside_check_box = self.build_check_box(
            "Allow Clips Outside Range",
            "timeline_allow_outside_range",
            TOOLTIP_ALLOW_OUTSIDE_RANGE,
        )
        self.timeline_dependent_widgets.extend([names_check_box, sync_check_box, outside_check_box])
        first_row = self.build_row(group_layout)
        first_row.addWidget(show_check_box)
        first_row.addStretch()
        first_row.addWidget(names_check_box)

        second_row = self.build_row(group_layout)
        second_row.addWidget(sync_check_box)
        second_row.addStretch()
        second_row.addWidget(outside_check_box)

        third_row = self.build_row(group_layout)
        mode_label = ui_qt.QtWidgets.QLabel("Mode:")
        mode_label.setToolTip(TOOLTIP_TIMELINE_MODE)
        self.timeline_dependent_widgets.append(mode_label)
        third_row.addWidget(mode_label)
        current_mode = get_valid_mode(self.preferences.get("timeline_mode"))
        mode_group = ui_qt.QtWidgets.QButtonGroup(self)
        for mode in TIMELINE_MODES:
            radio_button = ui_qt.QtWidgets.QRadioButton(MODE_LABELS.get(mode, mode))
            radio_button.setToolTip(TOOLTIP_TIMELINE_MODE)
            radio_button.setChecked(mode == current_mode)
            radio_button.toggled.connect(lambda state, name=mode: self.on_mode_toggled(state, name))
            mode_group.addButton(radio_button)
            self.mode_buttons[mode] = radio_button
            self.timeline_dependent_widgets.append(radio_button)
            third_row.addStretch()
            third_row.addWidget(radio_button)
        # The button group must be retained so Qt does not delete it early
        self.mode_button_group = mode_group
        return group_box

    def build_behavior_group(self):
        """Builds the clip behavior preferences.

        Returns:
            QGroupBox: Created group.
        """
        group_box, group_layout = self.build_group("Clip Behavior")
        first_row = self.build_row(group_layout)
        first_row.addWidget(self.build_check_box("Refresh On Focus", "refresh_on_focus", TOOLTIP_REFRESH_ON_FOCUS))
        first_row.addStretch()
        first_row.addWidget(
            self.build_check_box("Auto Add Timeline", "auto_add_timeline_clip", TOOLTIP_AUTO_ADD_TIMELINE)
        )
        first_row.addStretch()
        first_row.addWidget(
            self.build_check_box("Sync Bookmarks", "sync_time_slider_bookmarks", TOOLTIP_SYNC_BOOKMARKS)
        )
        second_row = self.build_row(group_layout)
        second_row.addWidget(self.build_check_box("Auto Reorder", "auto_reorder_clips", TOOLTIP_AUTO_REORDER))
        second_row.addStretch()
        second_row.addWidget(self.build_check_box("Confirm Delete", "confirm_delete_clip", TOOLTIP_CONFIRM_DELETE))
        second_row.addStretch()
        second_row.addWidget(
            self.build_check_box(
                "New Clips Start At Current Frame",
                "new_clip_at_current_frame",
                TOOLTIP_NEW_CLIP_CURRENT_FRAME,
            )
        )
        return group_box

    def build_actions_group(self):
        """Builds the preference action buttons.

        Returns:
            QGroupBox: Created group.
        """
        group_box, group_layout = self.build_group("Actions")
        first_row = self.build_row(group_layout)
        first_row.addWidget(
            self.build_button("Sync Time Slider Bookmarks", ACTION_SYNC_BOOKMARKS, TOOLTIP_BTN_SYNC_BOOKMARKS)
        )
        first_row.addWidget(self.build_button("Reorder Clips", ACTION_REORDER_CLIPS, TOOLTIP_BTN_REORDER))
        first_row.addWidget(self.build_button("Reset Settings", ACTION_RESET_PREFERENCES, TOOLTIP_BTN_RESET))
        second_row = self.build_row(group_layout)
        second_row.addWidget(self.build_button("Export Scene Data", ACTION_EXPORT_DATA, TOOLTIP_BTN_EXPORT))
        second_row.addWidget(self.build_button("Import Scene Data", ACTION_IMPORT_DATA, TOOLTIP_BTN_IMPORT))
        second_row.addWidget(
            self.build_button("Delete Scene Data", ACTION_DELETE_SCENE_DATA, TOOLTIP_BTN_DELETE_SCENE_DATA)
        )
        return group_box

    # ------------------------------------------------------------------ signals
    def on_mode_toggled(self, state, mode):
        """Reports the selected timeline mode.

        Args:
            state (bool): Whether the radio button became checked.
            mode (str): Timeline mode key of the radio button.
        """
        if state:
            self.preference_changed.emit("timeline_mode", mode)

    def on_show_timeline_toggled(self, state):
        """Updates the widgets that only apply while the timeline is visible.

        Args:
            state (bool): Whether the timeline view is enabled.
        """
        self.preferences["show_timeline"] = bool(state)
        self.update_timeline_dependent_widgets()

    def update_timeline_dependent_widgets(self):
        """Enables timeline options only while the timeline view is visible."""
        is_enabled = bool(self.preferences.get("show_timeline"))
        for widget in self.timeline_dependent_widgets:
            widget.setEnabled(is_enabled)
