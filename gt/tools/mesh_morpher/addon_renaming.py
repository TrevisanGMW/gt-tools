"""
 Mesh Morpher Addon: Renaming
"""

import gt.tools.mesh_morpher.morpher_framework as tools_morph_frm
import gt.core.naming as core_naming
import gt.core.node as core_node
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Renaming(tools_morph_frm.MorpherAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = True

    def __init__(self):
        """
        Initializes a Naming object with the default attributes.
        """
        super().__init__(name="Naming")
        self.execution_order = self.Order.post_morph
        self.apply_override = False
        self.apply_prefix = False
        self.apply_suffix = False
        self.override = ""
        self.prefix = ""
        self.suffix = ""
        self.layers = []

    # -------------------------------------------- Setters/Getters ----------------------------------------------
    def set_apply_override(self, apply_override):
        """
        Args:
            apply_override (bool): If active, override text will be applied.
        """
        self.apply_override = apply_override

    def set_apply_prefix(self, apply_prefix):
        """
        Args:
            apply_prefix (bool): If active, prefix text will be applied.
        """
        self.apply_prefix = apply_prefix

    def set_apply_suffix(self, apply_suffix):
        """
        Args:
            apply_suffix (bool): If active, suffix text will be applied.
        """
        self.apply_suffix = apply_suffix

    def set_override(self, override):
        """
        Args:
            override (str): Override name string.
        """
        self.override = override

    def set_prefix(self, prefix):
        """
        Args:
            prefix (str): Prefix string.
        """
        self.prefix = prefix

    def set_suffix(self, suffix):
        """
        Args:
            suffix (str): Prefix string.
        """
        self.suffix = suffix

    def set_layers(self, layers):
        """
        Sets the list of layers to a pre-defined list.
        Args:
            layers (list): A list of dictionaries. Each dictionary is considered a layer.
                           See "add_default_layer" to understand the pattern.
        """
        self.layers = layers

    def add_default_layer(self):
        """
        Adds a new layer to the list of layers. A default layer comes with no name and default values.
        Returns:
            dict: The dictionary representing the created layer.
        """
        _new_layer = {"search": "$CACHE", "replace": ""}
        self.layers.append(_new_layer)
        return _new_layer

    def remove_layer_by_index(self, index):
        """
        Removes an existing layer
        Args:
            index (int): Index of the layer to be removed.
        """
        if index < 0 or index >= len(self.layers):
            raise IndexError("Unable to remove layer. Provided index out of range.")

        return self.layers[:index] + self.layers[index + 1 :]

    def clear_layers(self):
        """
        Resets the layers list back to an empty list.
        """
        self.layers = []

    # ------------------------------------------------- Main ---------------------------------------------------
    def apply_addon(self):
        """
        Applies the Mask RBF addon.
        """
        # Create the blend shape and activate it
        _reshaped_mesh = core_node.Node(self._reshaped_mesh)

        # Search and Replace
        if self.layers:
            for layer in self.layers:
                layer_search = layer.get("search") or ""
                layer_search_ev = self.get_definition().parse_str_using_environment_variable(layer_search)
                layer_replace = layer.get("replace") or ""
                layer_replace_ev = self.get_definition().parse_str_using_environment_variable(layer_replace)
                _reshaped_short_name = core_naming.get_short_name(str(_reshaped_mesh), remove_namespace=True)
                _new_name = _reshaped_short_name.replace(layer_search_ev, layer_replace_ev)
                _reshaped_mesh.rename(_new_name)

        # Overriding?
        _reshaped_short_name = _reshaped_mesh.get_short_name()
        _new_name = _reshaped_short_name
        if self.apply_override and self.override:
            _new_name = self.override

        # Adding Prefix?
        if self.apply_prefix and self.prefix:
            _new_name = f"{self.prefix}{_new_name}"

        # Adding Suffix?
        if self.apply_suffix and self.suffix:

            _new_name = f"{_new_name}{self.suffix}"

        # If not empty and different from the original, rename it
        if _new_name and _new_name != _reshaped_short_name:
            _reshaped_mesh.rename(_new_name)


if __name__ == "__main__":
    a_renaming_addon = Renaming()
    a_renaming_addon.set_subject_mesh("cloth_mesh")
    a_renaming_addon.set_reshaped_mesh("cloth_mesh_mesh_morpher_definition")

    # Test Layer A
    a_renaming_addon.set_override("override")
    a_renaming_addon.set_prefix("prefix_")
    a_renaming_addon.set_suffix("_suffix")

    # a_renaming_addon.set_apply_override(True)
    # a_renaming_addon.set_apply_prefix(True)
    # a_renaming_addon.set_apply_suffix(True)

    test_layers = [{"search": "definition", "replace": "something_else"}]
    a_renaming_addon.set_layers(test_layers)  # Set Layers (override them)

    a_renaming_addon.apply_addon()
