"""
Auto Rigger Rom Loader Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleROMLoader(AttrWidget):
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
        self.add_widget_separator_line(label_text="Load Range of Motion Preferences")
        self.add_module_attr_widget_path(attr_name="target_file_path", dir_only=False)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.addWidget(ui_qt.QtWidgets.QLabel("Range of Motion Definition:"))
        self.definition_combobox = self.add_widget_definition_combobox(
            initial_definition=self.module.retarget_definition
        )
        self.definition_combobox.currentIndexChanged.connect(self.on_definition_combobox_changed)
        _layout.addWidget(self.definition_combobox)
        self.content_layout.addLayout(_layout)
        # Preferences
        self.add_widget_separator_line(label_text="Comparison (Source) Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="comparison_offset",
            tooltip="If True, the weight of the comparison A+B setup is set to 1.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="comparison_visibility",
            tooltip="Defines the visibility of the source skeleton/mesh.",
            layout=_layout,
        )

    @staticmethod
    def add_widget_definition_combobox(initial_definition):
        """
        Creates a populated combobox with all potential retarget (ROM) definitions.
        Args:
            initial_definition (str, None): Name of the initial definition to be selected.
        Returns:
            QComboBox: A pre-populated combobox with potential definitions. Initial definition is also pre-selected.
        """
        import gt.tools.retargeter.retargeter_constants as tools_rt_const

        rom_folder = tools_rt_const.RetargeterConstants.DEFAULT_ROM_DATA_FOLDER
        definitions = set()
        for file in os.listdir(rom_folder):
            if os.path.isfile(os.path.join(rom_folder, file)):
                name_without_ext, _ = os.path.splitext(file)
                definitions.add(name_without_ext)

        # Create Combobox
        combobox = ui_qt.QtWidgets.QComboBox()

        # Populate Combobox
        for definition in list(definitions):
            combobox.addItem(core_str.snake_to_title(definition), definition)

        # Set Initial or Add Unknown Initial Probe (Not present in project)
        if initial_definition is None:
            return combobox
        if initial_definition in definitions:
            for index in range(combobox.count()):
                _definition = combobox.itemData(index)
                if _definition and initial_definition == _definition:
                    combobox.setCurrentIndex(index)
        return combobox

    def on_definition_combobox_changed(self, index):
        """
        Slot function called when the definition combobox selection changes.
        Updates the retarget_definition in the module based on the newly selected item.

        Args:
            index (int): The index of the currently selected item in the combobox.
        """
        snake_case_name = self.definition_combobox.itemData(index)
        if snake_case_name:
            self.module.retarget_definition = snake_case_name
