"""
Mesh Morpher Addon: Masking
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


class Masking(tools_morph_frm.MorpherAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = True

    def __init__(self):
        """
        Initializes a Masking object with the default attributes.
        """
        super().__init__(name="Masking")
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
        _new_layer = {"name": "", "opacity": 1, "vertices": ""}
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

        return self.layers[:index] + self.layers[index + 1:]

    def clear_layers(self):
        """
        Resets the layers list back to an empty list.
        """
        self.layers = []

    # --------------------------------------------------- Misc --------------------------------------------------
    @staticmethod
    def mask_blend_shape_weights(vertices, bs_node, opacity=1.0):
        """
        Sets blend shape vertices weights to opacity value. Vertices outside the provided range are set to 0.0
        (masked out)

        Args:
            vertices (list of str): A list of vertex names (e.g., ["mesh.vtx[0]", "mesh.vtx[1]"]) to set to weight 1.
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

    @staticmethod
    def skip_translations(skip_axes, reshaped_vertices, subject_dup_vertices):
        """
        Skips the translation axes selected by the user.

        Args:
            skip_axes (list of three booleans): x, y, z (e.g., [0, 0, 0]).
            reshaped_vertices (list of str): A list of vertex names (e.g., ["mesh.vtx[0]", "mesh.vtx[1]"]).
            subject_dup_vertices (list of str): A list of vertex names (e.g., ["mesh.vtx[0]", "mesh.vtx[1]"]).
        """
        flatten_vertices = cmds.ls(reshaped_vertices, flatten=True)
        rbf_pos_dict = {index: cmds.xform(index, q=True, t=True, ws=True) for index in flatten_vertices}
        flatten_vertices = cmds.ls(subject_dup_vertices, flatten=True)
        dupe_pos_dict = {index: cmds.xform(index, q=True, t=True, ws=True) for index in flatten_vertices}
        _subject_dupe_short_name = str(next(iter(dupe_pos_dict))).split(".")[0]

        # apply skip on the subject dupe that will be used for the blendShape
        for v, pos in rbf_pos_dict.items():
            v_number = v.split(".")[-1]
            pos_skipped = pos
            dupe_pos = dupe_pos_dict[f"{_subject_dupe_short_name}.{v_number}"]

            # skip translation X
            if skip_axes[0]:
                pos_skipped[0] = dupe_pos[0]
            # skip translation Y
            if skip_axes[1]:
                pos_skipped[1] = dupe_pos[1]
            # skip translation Z
            if skip_axes[2]:
                pos_skipped[2] = dupe_pos[2]

            dupe_v = f"{_subject_dupe_short_name}.{v_number}"
            cmds.xform(dupe_v, t=pos_skipped, ws=True)

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
            layer_skip_translations = layer.get("skip_translations") or [0, 0, 0]
            layer_vertices_packed = layer.get("vertices")
            if not layer_vertices_packed:
                continue  # No vertices, nothing to do

            reshaped_vertices_unpacked = self.unpack_vertices(str(_reshaped_mesh), layer_vertices_packed)
            layer_vertices_unpacked = self.unpack_vertices(str(_subject_dupe), layer_vertices_packed)
            self.skip_translations(layer_skip_translations, reshaped_vertices_unpacked, layer_vertices_unpacked)

            bs_name = f"{_reshaped_short_name}_{layer_name}_blendShape"
            bs_node = cmds.blendShape(_subject_dupe, self._reshaped_mesh, name=bs_name)[0]
            cmds.setAttr(f"{bs_node}.{_subject_dupe.get_short_name()}", 1)

            self.mask_blend_shape_weights(vertices=layer_vertices_unpacked, bs_node=bs_node, opacity=layer_opacity)

        # Clean up
        cmds.delete(_subject_dupe)
        # Bake
        if self.bake_mesh:
            cmds.delete(_reshaped_mesh, ch=True)


if __name__ == "__main__":
    a_mask_addon = Masking()
    a_mask_addon.set_subject_mesh("cloth_mesh")
    a_mask_addon.set_reshaped_mesh("cloth_mesh_mesh_morpher_definition")

    # Zippers Layer
    test_layers = [{"name": "zippers", "vertices": "[0:370]"}]
    # Bottom Layer
    bottom_vertices = (
        "[371:373], [375:409], [411:812], [846:895], [1438:1440], [1548:1571], [1850], [1857], "
        "[1882:1890], [1963:1964], [1968:1979], [2009:2010], [2129:2182], [2235:2236], [2238:2241], "
        "[2247:2248], [2250:2253], [2259:2260], [2262:2263], [2352:2375], [2381:2382], [2384:2385], "
        "[2480:2503], [2510], [2517], [2541:2549], [2621:2622], [2624:2635], [2653:2705], [2742:2743], "
        "[2745:2748], [2754:2755], [2757:2760], [2766:2767], [2769:2770], [2786:2807], [2813:2814], "
        "[2816:2817], [2821:2830], [3263:3268], [3278:3308], [3446:3476], [3485:3758], [3787:3800], "
        "[3857], [3891:3903], [3913:3926], [3968:3969], [3971], [3981:3983], [4435:4436], [4464], "
        "[4520:4521]"
    )
    test_layers.append({"name": "bottom", "vertices": bottom_vertices, "opacity": 0.5})

    a_mask_addon.set_layers(test_layers)  # Set Layers (override them)

    a_mask_addon.set_bake_mesh_state(False)  # To see the bs deformers in action and test setup

    a_mask_addon.apply_addon()
    cmds.setAttr("cloth_mesh.visibility", 0)
