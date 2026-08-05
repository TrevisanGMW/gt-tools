"""
 Mesh Morpher Addons

Import Line:
    import gt.tools.mesh_morpher.morpher_addons as tools_morpher_addons
"""

import gt.tools.mesh_morpher.addon_delta_mush as tools_addon_delta_mush
import gt.tools.mesh_morpher.addon_masking as tools_addon_masking
import gt.tools.mesh_morpher.addon_anchor as tools_addon_anchor
import gt.tools.mesh_morpher.addon_renaming as tools_addon_renaming
import logging
import inspect

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Addons:
    """A list of available modules"""

    DeltaMush = tools_addon_delta_mush.DeltaMush
    Masking = tools_addon_masking.Masking
    Anchor = tools_addon_anchor.Anchor
    Renaming = tools_addon_renaming.Renaming

    @staticmethod
    def get_addons_dict():
        """
        Gets available addons as a dictionary. Key is the name of the addon and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the addon and value is the class.
                  e.g. 'DeltaMushLayers': <class 'DeltaMushLayers'>
        """
        addon_attrs = vars(Addons)
        class_attributes = {name: value for name, value in addon_attrs.items() if inspect.isclass(value)}
        return class_attributes
