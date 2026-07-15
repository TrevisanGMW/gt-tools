"""
 Mesh Morpher Addon: Delta Mush
"""

import gt.tools.mesh_morpher.morpher_framework as tools_morph_frm
import gt.core.naming as core_naming
import gt.core.mesh as core_mesh
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DeltaMush(tools_morph_frm.MorpherAddon):
    __version__ = "0.0.2"
    allow_multiple = True

    def __init__(self):
        """
        Initializes a DeltaMush object with the default attributes.
        """
        super().__init__(name="DeltaMush")
        self.execution_order = self.Order.post_morph
        self.bake_mesh = True
        self.layers = []

    # -------------------------------------------- Setters/Getters ----------------------------------------------
    def set_bake_mesh_state(self, bake_state):
        """
        Sets the list of layers to a pre-defined list.
        Args:
            bake_state (bool): If True, the mesh is baked and history is deleted.
                               If False, delta mush node are still accessible.
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
        _new_layer = {"name": "", "distanceWeight": 1, "smoothingIterations": 10, "vertices": ""}
        self.layers.append(_new_layer)
        return _new_layer

    def remove_layer_by_index(self, index):
        """
        Removes an existing delta mush layer
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
    def mask_delta_mush_weights(vertices, delta_mush_node):
        """
        Set weights of the Delta Mush deformer based on selected vertices.

        Args:
            vertices (list): List of strings with the vertex components (e.g., ["pCube1.vtx[0]", "pCube1.vtx[1]"]).
            delta_mush_node (str): Name of the Delta Mush deformer node as a string.
        """
        if not vertices:
            return
        source_mesh = vertices[0].split(".")[0]
        all_vertices = core_mesh.get_vertices(source_mesh)
        cmds.percent(delta_mush_node, all_vertices, value=0)  # Remove existing weights
        cmds.percent(delta_mush_node, vertices, value=1)  # Add Masking

    # ------------------------------------------------- Core ---------------------------------------------------
    def apply_addon(self):
        """
        Applies the delta mush addon.
        """
        # Skip duplication if addon is not used
        if not self.layers:
            return

        # Rename Shaped (It will become the blend shape source)
        _reshaped_short_name = core_naming.get_short_name(self._reshaped_mesh, remove_namespace=True)
        _reshaped_bs_name = f"{_reshaped_short_name}_deltaMushSource"
        _reshaped_mesh = core_node.Node(self._reshaped_mesh)
        _reshaped_mesh.rename(_reshaped_bs_name)
        # Duplicate original to be used as new reshaped
        _subject_mesh = cmds.duplicate(self._subject_mesh, name=_reshaped_short_name)[0]

        # Create the blend shape and activate it
        bs_node = cmds.blendShape(_reshaped_mesh, _subject_mesh, name=f"{_reshaped_short_name}_blendShape")[0]
        cmds.setAttr(f"{bs_node}.{_reshaped_mesh.get_short_name()}", 1)

        # Apply Delta Mush deformer and set attributes
        for layer in self.layers:
            delta_mush_name = f"{_subject_mesh}_deltaMush"
            layer_name = layer.get("name")
            if layer_name:
                delta_mush_name += f"_{str(layer_name)}"
            delta_mush_node = cmds.deltaMush(_subject_mesh, name=delta_mush_name)[0]
            # Apply layer attributes
            layer_vertices_packed = layer.get("vertices")
            layer_vertices_unpacked = self.unpack_vertices(_subject_mesh, layer_vertices_packed)
            self.mask_delta_mush_weights(vertices=layer_vertices_unpacked, delta_mush_node=delta_mush_node)
            layer_distance_weight = layer.get("distanceWeight", 1)
            cmds.setAttr(f"{delta_mush_node}.distanceWeight", layer_distance_weight)
            layer_smoothing_iterations = layer.get("smoothingIterations", 10)
            cmds.setAttr(f"{delta_mush_node}.smoothingIterations", layer_smoothing_iterations)

        # Clean up and reset reshaped mesh
        cmds.delete(_reshaped_mesh)

        # Bake
        if self.bake_mesh:
            cmds.delete(_subject_mesh, ch=True)


if __name__ == "__main__":
    a_delta_mush_addon = DeltaMush()
    a_delta_mush_addon.set_subject_mesh("cloth_mesh")
    a_delta_mush_addon.set_reshaped_mesh("cloth_mesh_mesh_morpher_definition")

    # Zippers Layer
    test_layers = [{"name": "zippers", "distanceWeight": 1, "smoothingIterations": 10, "vertices": "[0:370]"}]
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
    test_layers.append({"name": "bottom", "vertices": bottom_vertices})

    a_delta_mush_addon.set_layers(test_layers)  # Set Layers (override them)

    a_delta_mush_addon.set_bake_mesh_state(False)  # To see delta mush deformers in action and test setup

    a_delta_mush_addon.apply_addon()
    cmds.setAttr("cloth_mesh.visibility", 0)
