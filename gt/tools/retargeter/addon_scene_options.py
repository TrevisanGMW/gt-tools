"""
Animation Retargeter Addon: Scene Options
"""

import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import gt.core.scene as core_scene
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddonSceneOptions(tools_rt_frm.TargetingAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = True

    def __init__(self):
        """
        Initializes a SceneOptions object with the default scene options.
        """
        super().__init__(name="Scene Setup")
        self.execution_order = self.Order.post_import
        self.scene_options = {
            "linear_unit": "centimeter",
            "angular_unit": "degree",
            "frame_rate": "30fps",
            "multi_sample": True,
            "multi_sample_count": 8,
            "persp_clip_plane_near": 1,
            "persp_clip_plane_far": 10000.0,
            "display_textures": True,
            "playback_frame_start_floor": True,
            "playback_frame_end_ceil": True,
            "animation_frame_start_floor": True,
            "animation_frame_end_ceil": True,
        }

    def set_scene_options(self, scene_options_dict):
        """
        Sets the initial options dictionary for the scene.
        The keys are the name of the attributes/options that will be affected.
        The values are the desired preferences.
        Example:
            scene_options_dict = {
                         'linear_unit': 'centimeter',
                         'angular_unit': 'degree',
                         'frame_rate': '30fps',
                         'multi_sample': True,
                         'multi_sample_count': 8,
                         'persp_clip_plane_near': 1,
                         'persp_clip_plane_far': 10000.0,
                         'display_textures': True,
                        }

        Args:
            scene_options_dict: A dictionary describing the initial values of a scene.
        """
        if not scene_options_dict or not isinstance(scene_options_dict, dict):
            logger.warning(f"Unable to set attribute values dictionary. Incorrect input type.")
            return
        self.scene_options = scene_options_dict

    def get_scene_options(self):
        """
        Gets the scene options stored in this class
        Returns:
            dict: A dictionary where the keys are the options and the values are the user-defined values.
                  e.g. {'frame_rate': '30fps'}
        """
        return self.scene_options

    def apply_addon(self):
        """
        Applies the stored scene options.
        See "core_scene.set_scene_from_dict()" docstrings for recognized keys and values.
        """
        core_scene.set_scene_from_dict(scene_dict=self.scene_options)


if __name__ == "__main__":
    a_scene_options_addon = AddonSceneOptions()
    a_scene_options_addon.apply_addon()
