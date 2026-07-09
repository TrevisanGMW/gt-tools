"""
Animation Retargeter Patches

Import Line:
    import gt.tools.retargeter.retargeter_patches as tools_rt_patches
"""

import gt.tools.retargeter.addon_patch as tools_addon_patch
import logging
import inspect

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Patches:
    """A list of available patches.
    Note: the Patches inherit TargetingAddon as the other Addons, they are just predefined addon scripts."""

    AddonPatchXsensProportions = tools_addon_patch.AddonPatchXsensProportions
    AddonPatchXsensPoleVector = tools_addon_patch.AddonPatchXsensPoleVector

    @staticmethod
    def get_patches_dict():
        """
        Gets available patches as a dictionary. Key is the name of the patch and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the patch and value is the class.
                  e.g. 'PatchXsensProportions': <class 'AddonPatchXsensProportions'>
        """
        addon_attrs = vars(Patches)
        class_attributes = {name: value for name, value in addon_attrs.items() if inspect.isclass(value)}
        return class_attributes
