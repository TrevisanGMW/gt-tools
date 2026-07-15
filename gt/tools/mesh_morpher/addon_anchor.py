"""
Mesh Morpher Addon: Anchor Point
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


class Anchor(tools_morph_frm.MorpherAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = True

    def __init__(self):
        """
        Initializes an Anchor object with the default attributes.
        """
        super().__init__(name="Anchor")
        self.execution_order = self.Order.post_morph
        self.bake_mesh = True
        self.layers = []

    # -------------------------------------------- Setters/Getters ----------------------------------------------
    def set_bake_mesh_state(self, bake_state):
        """
        Sets the list of layers to a pre-defined list.
        Args:
            bake_state (bool): If True, the mesh is baked and history is deleted.
                               If False, the deformer nodes are still accessible.
        """
        self.bake_mesh = bake_state

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
        _new_layer = {"name": "", "opacity": 1, "vertices": "", "anchor": ""}
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

    # --------------------------------------------------- Misc --------------------------------------------------
    @staticmethod
    def anchor_blend_shape_weights(vertices, anchor, bs_node, opacity=1.0):
        """
        Sets blend shape vertices weights to opacity value. Vertices outside the provided range are set to 0.0
        (masked out)

        Args:
            vertices (list of str): A list of vertex names (e.g., ["mesh.vtx[0]", "mesh.vtx[1]"]) to set to weight 1.
            anchor (str): a vertex used as anchor point to move the entire selected vertices.
            bs_node (str): The name of the blend shape node controlling the target.
            opacity (float, optional): Value to set the selected vertices. If not provided it's set to 1 (100%)
        """
        source_mesh = vertices[0].split(".")[0]
        flatten_vertices = cmds.ls(vertices, flatten=True)
        vtx_num_pattern = re.compile(r"vtx\[(\d+)\]$")
        vertices = [int(match.group(1)) for item in flatten_vertices if (match := vtx_num_pattern.search(item))]
        vertex_nb = cmds.polyEvaluate(source_mesh, v=1)
        weight = cmds.getAttr(f"{bs_node}.inputTarget[0].baseWeights[0:{vertex_nb}]")
        weight_masked = [opacity if index in vertices else 0.0 for index in range(len(weight))]
        cmds.setAttr(f"{bs_node}.inputTarget[0].baseWeights[0:{vertex_nb}]", *weight_masked, size=len(weight))

    def move_based_on_anchor(self, vertices, anchor, target_mesh=None):
        """
        Move the selected vertices according to the vertex used as anchor point.

        Args:
            vertices (list of str): A list of vertex names (e.g., ["mesh.vtx[0]", "mesh.vtx[1]"]) to set to weight 1.
            anchor (int): vertex id used as anchor point to move the entire selected vertices.
            target_mesh (str, optional): target mesh to apply the movement. If None, reshaped_mesh is used.
        """
        if not target_mesh:
            target_mesh = self._reshaped_mesh
        flatten_vertices = cmds.ls(vertices, flatten=True)
        vtx_num_pattern = re.compile(r"vtx\[(\d+)\]$")
        vertices = [int(match.group(1)) for item in flatten_vertices if (match := vtx_num_pattern.search(item))]

        anchor_source_pos = cmds.xform(f"{self._subject_mesh}.vtx[{anchor}]", t=True, ws=True, q=True)
        anchor_moved_pos = cmds.xform(f"{self._reshaped_mesh}.vtx[{anchor}]", t=True, ws=True, q=True)
        anchor_delta = [anchor_source_pos[i] - anchor_moved_pos[i] for i in range(3)]

        for v in vertices:
            v_str = str(v)
            v_current_pos = cmds.xform(f"{self._subject_mesh}.vtx[{v_str}]", t=True, ws=True, q=True)
            v_anchored_pos = [v_current_pos[i] - anchor_delta[i] for i in range(3)]
            # set anchored pos
            cmds.xform(f"{target_mesh}.vtx[{v_str}]", ws=True, t=v_anchored_pos)

    # ------------------------------------------------- Main ---------------------------------------------------
    def apply_addon(self):
        """
        Applies the Mask RBF addon.
        """
        # Skip duplication if addon is not used
        if not self.layers:
            return

        # Duplicate original to be used as new reshaped
        _subject_dupe = cmds.duplicate(self._subject_mesh, name=f"{self._subject_mesh}_originalShape", fullPath=True)[0]
        _subject_dupe = core_node.Node(_subject_dupe)

        # Create the blend shape and activate it
        _reshaped_mesh = core_node.Node(self._reshaped_mesh)
        _reshaped_short_name = core_naming.get_short_name(self._reshaped_mesh, remove_namespace=True)

        # Apply Blend Shape deformer and set attributes
        for layer in self.layers:
            layer_name = layer.get("name")
            layer_opacity = layer.get("opacity") or 1.0
            layer_vertices_packed = layer.get("vertices")
            layer_vertices_unpacked = self.unpack_vertices(str(_subject_dupe), layer_vertices_packed)
            layer_anchor = layer.get("anchor")
            if not layer_vertices_packed or not layer_anchor:
                continue  # No vertices or anchor point, nothing to do

            # Move vertices based on the anchor point
            self.move_based_on_anchor(layer_vertices_unpacked, layer_anchor, target_mesh=_subject_dupe)

            # Create the blendshape
            bs_name = f"{_reshaped_short_name}_{layer_name}_blendShape"
            bs_node = cmds.blendShape(_subject_dupe, self._reshaped_mesh, name=bs_name)[0]
            cmds.setAttr(f"{bs_node}.{_subject_dupe.get_short_name()}", 1)

            self.anchor_blend_shape_weights(
                vertices=layer_vertices_unpacked,
                anchor=layer_anchor,
                bs_node=bs_node,
                opacity=layer_opacity,
            )

        # Clean up
        cmds.delete(_subject_dupe)
        # Bake
        if self.bake_mesh:
            cmds.delete(_reshaped_mesh, ch=True)


if __name__ == "__main__":
    a_anchor_addon = Anchor()
    a_anchor_addon.set_subject_mesh("cloth_mesh")
    a_anchor_addon.set_reshaped_mesh("cloth_mesh_female")

    # dangling bits
    test_layers = [
        {"name": "d_bit01", "vertices": "[127:133], [255:312]", "anchor": 129},
        {"name": "d_bit02", "vertices": "[182:188], [313:370]", "anchor": 184},
    ]

    a_anchor_addon.set_layers(test_layers)  # Set Layers (override them)
    a_anchor_addon.set_bake_mesh_state(False)  # To see the bs deformers in action and test setup
    a_anchor_addon.apply_addon()
