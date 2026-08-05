"""
Animation Retargeter Model
"""

import gt.tools.mesh_morpher.morpher_framework as tools_morpher_frm
import gt.core.io as core_io
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MorpherModel:
    def __init__(self):
        """
        Initialize the MorpherModel object.
        """
        self.definition = tools_morpher_frm.MorpherDefinition()

    # --------------------- Project ---------------------
    def clear_definition(self):
        """
        Re-initializes the definition to an empty one.
        """
        self.definition = tools_morpher_frm.MorpherDefinition()

    def set_definition(self, definition):
        """
        Sets a new definition.
        Args:
            definition (RetargeterDefinition): A new definition to be stored in "self.definition"
        """
        if not definition or not isinstance(definition, tools_morpher_frm.MorpherDefinition):
            logger.debug(f"Unable to set definition. Invalid input.")
            return
        self.definition = definition

    def get_definition(self):
        """
        Gets the current definition. (RetargeterDefinition)
        Returns:
            RetargeterDefinition: Current definition stored in "self.definition".
        """
        return self.definition

    # ------------------- Input/Output -------------------
    def save_definition_to_file(self, path):
        """
        Save the current definition to the provided path (JSON format)

        Args:
            path (str): The target file path where the JSON
        """
        data = self.definition.get_definition_as_dict()
        core_io.write_json(path=path, data=data)

    def load_definition_from_file(self, path):
        """
        Loads a new definition from the provided path (path should point to a definition description (JSON)
        Args:
            path (str): Path to the definition description (JSON format)
        """
        self.definition = tools_morpher_frm.MorpherDefinition()
        data = core_io.read_json_dict(path)
        self.definition.read_data_from_dict(data)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = MorpherModel()

    # Test JSON Output
    import os

    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    test_json_path = os.path.join(desktop_path, r"mesh_morpher_definition.json")
    model.save_definition_to_file(path=test_json_path)
