"""
Animation Retargeter Addons

Import Line:
    import gt.tools.retargeter.retargeter_addons as tools_rt_addons
"""

import gt.tools.retargeter.addon_scene_options as tools_addon_scene_options
import gt.tools.retargeter.addon_source_setup as tools_addon_source_setup
import gt.tools.retargeter.addon_post_bake as tools_addon_post_bake
import gt.tools.retargeter.addon_python_script as tools_addon_python
import logging
import inspect

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Addons:
    """A list of available modules"""

    AddonSceneOptions = tools_addon_scene_options.AddonSceneOptions
    AddonSourceSetup = tools_addon_source_setup.AddonSourceSetup
    AddonPostBake = tools_addon_post_bake.AddonPostBake
    AddonPythonScript = tools_addon_python.AddonPythonScript

    @staticmethod
    def get_addons_dict():
        """
        Gets available addons as a dictionary. Key is the name of the addon and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the addon and value is the class.
                  e.g. 'AddonSourceManager': <class 'AddonSourceManager'>
        """
        addon_attrs = vars(Addons)
        class_attributes = {name: value for name, value in addon_attrs.items() if inspect.isclass(value)}
        return class_attributes
