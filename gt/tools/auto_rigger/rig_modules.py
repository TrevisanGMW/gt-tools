import inspect
import gt.core.str as core_str
import gt.ui.resource_library as ui_res_lib
import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
import gt.tools.auto_rigger.modules.module_root as tools_mod_root
import gt.tools.auto_rigger.modules.module_spine as tools_mod_spine
import gt.tools.auto_rigger.modules.module_biped_leg as tools_mod_leg
import gt.tools.auto_rigger.modules.module_biped_arm as tools_mod_biped_arm
import gt.tools.auto_rigger.modules.module_arm as tools_mod_arm
import gt.tools.auto_rigger.modules.module_biped_finger as tools_mod_finger
import gt.tools.auto_rigger.modules.module_head as tools_mod_head
import gt.tools.auto_rigger.modules.module_utils as tools_mod_utils
import gt.tools.auto_rigger.modules.module_ngskin as tools_mod_ngskin
import gt.tools.auto_rigger.modules.module_mh_facial as tools_mod_meta_face
import gt.tools.auto_rigger.modules.module_socket as tools_mod_socket
import gt.tools.auto_rigger.modules.module_attr_hub as tools_mod_attr_switcher
import gt.tools.auto_rigger.modules.module_chain as tools_mod_chain
import gt.tools.auto_rigger.modules.module_ribbon as tools_mod_ribbon
import gt.tools.auto_rigger.modules.module_rbf_load as tools_mod_rbf_load
import gt.tools.auto_rigger.modules.module_generic_fk as tools_mod_generic_fk
import gt.tools.auto_rigger.modules.module_generic_ik as tools_mod_generic_ik
import gt.tools.auto_rigger.modules.module_ref_mass as tools_mod_ref_mass
import gt.tools.auto_rigger.modules.module_piston as tools_mod_piston
import gt.tools.auto_rigger.modules.module_pivot as tools_mod_pivot
import gt.tools.auto_rigger.modules.module_quad_front_leg as tools_mod_quad_front_leg
import gt.tools.auto_rigger.modules.module_quad_spine as tools_mod_quad_spine
import gt.tools.auto_rigger.modules.module_quad_rear_leg as tools_mod_quad_rear_leg
import gt.tools.auto_rigger.modules.module_probes as tools_mod_probes
import gt.tools.auto_rigger.modules.module_correctives as tools_mod_correctives
import gt.tools.auto_rigger.modules.module_enum_variants as tools_mod_enum_variants
import gt.tools.auto_rigger.modules.module_picker_data as tools_mod_picker_data
import gt.tools.auto_rigger.modules.module_collections as tools_mod_collections
import gt.tools.auto_rigger.modules.module_validation as tools_mod_validation


class RigModules:
    class General:
        icon = ui_res_lib.Icon.rigger_module_generic
        # General Modules
        ModuleGeneric = tools_rig_fmr.ModuleGeneric
        ModuleGenericFK = tools_mod_generic_fk.ModuleGenericFK
        ModuleGenericIK = tools_mod_generic_ik.ModuleGenericIK
        ModuleGenericIKLeft = tools_mod_generic_ik.ModuleGenericIKLeft
        ModuleGenericIKRight = tools_mod_generic_ik.ModuleGenericIKRight
        ModuleRoot = tools_mod_root.ModuleRoot
        ModuleSpine = tools_mod_spine.ModuleSpine
        ModuleHead = tools_mod_head.ModuleHead
        ModuleArm = tools_mod_arm.ModuleArm
        ModuleArmLeft = tools_mod_arm.ModuleArmLeft
        ModuleArmRight = tools_mod_arm.ModuleArmRight
        ModuleAttributeHub = tools_mod_attr_switcher.ModuleAttributeHub
        ModuleSocket = tools_mod_socket.ModuleSocket
        ModuleChain = tools_mod_chain.ModuleChain
        ModuleRibbon = tools_mod_ribbon.ModuleRibbon
        ModulePiston = tools_mod_piston.ModulePiston
        ModulePivot = tools_mod_pivot.ModulePivot

    class Biped:
        icon = ui_res_lib.Icon.rigger_template_biped
        # Biped Modules
        ModuleBipedArm = tools_mod_biped_arm.ModuleBipedArm
        ModuleBipedArmLeft = tools_mod_biped_arm.ModuleBipedArmLeft
        ModuleBipedArmRight = tools_mod_biped_arm.ModuleBipedArmRight
        ModuleBipedFingers = tools_mod_finger.ModuleBipedFingers
        ModuleBipedFingersLeft = tools_mod_finger.ModuleBipedFingersLeft
        ModuleBipedFingersRight = tools_mod_finger.ModuleBipedFingersRight
        ModuleBipedLeg = tools_mod_leg.ModuleBipedLeg
        ModuleBipedLegLeft = tools_mod_leg.ModuleBipedLegLeft
        ModuleBipedLegRight = tools_mod_leg.ModuleBipedLegRight
        ModuleMetaHumanFace = tools_mod_meta_face.ModuleMetaHumanFace
        ModuleAnimMassReferences = tools_mod_ref_mass.ModuleAnimMassReferences

    class Quadruped:
        icon = ui_res_lib.Icon.rigger_template_quadruped
        # Quadruped Modules
        ModuleQuadFrontLeg = tools_mod_quad_front_leg.ModuleQuadFrontLeg
        ModuleQuadFrontLegLeft = tools_mod_quad_front_leg.ModuleQuadFrontLegLeft
        ModuleQuadFrontLegRight = tools_mod_quad_front_leg.ModuleQuadFrontLegRight
        ModuleQuadRearLeg = tools_mod_quad_rear_leg.ModuleQuadRearLeg
        ModuleQuadRearLegLeft = tools_mod_quad_rear_leg.ModuleQuadRearLegLeft
        ModuleQuadRearLegRight = tools_mod_quad_rear_leg.ModuleQuadRearLegRight
        ModuleQuadSpine = tools_mod_quad_spine.ModuleQuadSpine

    class Correctives:
        icon = ui_res_lib.Icon.rigger_category_corrective
        # Corrective Modules
        ModuleCorrectiveGeneric = tools_mod_correctives.ModuleCorrectiveGeneric
        ModuleCorrectiveFK = tools_mod_correctives.ModuleCorrectiveFK
        ModuleRBFPoseLoader = tools_mod_rbf_load.ModuleRBFPoseLoader

    class Probes:
        icon = ui_res_lib.Icon.rigger_category_probe
        # Probe Modules
        ModuleProbeDistance = tools_mod_probes.ModuleProbeDistance
        ModuleProbeRotation = tools_mod_probes.ModuleProbeRotation

    class Utils:
        icon = ui_res_lib.Icon.rigger_module_util
        # Utility Modules
        ModuleGroup = tools_mod_utils.ModuleGroup
        ModuleNotes = tools_mod_utils.ModuleNotes
        ModuleNewScene = tools_mod_utils.ModuleNewScene
        ModuleImportFile = tools_mod_utils.ModuleImportFile
        ModuleSkinWeights = tools_mod_utils.ModuleSkinWeights
        ModuleNGSkinWeights = tools_mod_ngskin.ModuleNGSkinWeights
        ModulePython = tools_mod_utils.ModulePython
        ModuleExportSkeletalMesh = tools_mod_utils.ModuleExportSkeletalMesh
        ModuleSaveScene = tools_mod_utils.ModuleSaveScene
        ModuleLoadScene = tools_mod_utils.ModuleLoadScene
        ModuleShapesSnapshot = tools_mod_utils.ModuleShapesSnapshot
        ModuleCameraSetup = tools_mod_utils.ModuleCameraSetup
        ModuleThumbnailCapture = tools_mod_utils.ModuleThumbnailCapture
        ModulePlayblastCapture = tools_mod_utils.ModulePlayblastCapture
        ModuleROMLoader = tools_mod_utils.ModuleROMLoader
        ModuleEnumVariants = tools_mod_enum_variants.ModuleEnumVariants
        ModulePickerData = tools_mod_picker_data.ModulePickerData
        ModuleCollections = tools_mod_collections.ModuleCollections
        ModuleValidation = tools_mod_validation.ModuleValidation

    @staticmethod
    def get_modules_dict():
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        category_attrs = vars(RigModules)
        class_attributes = {name: value for name, value in category_attrs.items() if inspect.isclass(value)}
        modules_dict = {}
        for category, a_class in class_attributes.items():
            modules_attrs = vars(a_class)
            class_attributes = {name: value for name, value in modules_attrs.items() if inspect.isclass(value)}
            modules_dict.update(class_attributes)
        return modules_dict

    @staticmethod
    def get_modules():
        """
        Gets the available module classes stored in the RigModules class.
        Returns:
            list: A list of modules, these use the ModuleGeneric as their base.
        """
        return list(RigModules.get_modules_dict().values())

    @staticmethod
    def get_module_names():
        """
        Gets the name of all available modules.
        Returns:
            list: A list of module names (strings)
        """
        return list(RigModules.get_modules_dict().keys())

    @staticmethod
    def get_unique_modules_dict(remove_module_prefix=True):
        """
        Gets the lists of modules with the same name that end with sides (a.k.a. Unique Modules).
        Args:
            remove_module_prefix (bool, optional): If True, the "Module" prefix is removed.
        Returns:
            dict: name as key, module as value.
        """
        unique_modules = {}
        for name, module in RigModules.get_modules_dict().items():
            _name = name
            if remove_module_prefix:
                _name = core_str.remove_prefix(input_string=name, prefix="Module")
            _name = core_str.remove_suffix(input_string=_name, suffix="Left")
            _name = core_str.remove_suffix(input_string=_name, suffix="Right")
            if _name in unique_modules:
                unique_modules.get(_name).append(module)
            else:
                unique_modules[_name] = [module]
        return unique_modules

    @staticmethod
    def get_known_categories_dict():
        """
        Gets a dictionary where the keys are the categories and the values are their classes.
        Returns:
            dict: Known categories. e.g. {"General": <class '__main__.RigModules.General'>}
        """
        category_attrs = vars(RigModules)
        known_categories = {name: value for name, value in category_attrs.items() if inspect.isclass(value)}
        return known_categories

    @staticmethod
    def get_categorized_modules_dict(remove_module_prefix=True):
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Args:
            remove_module_prefix (bool): If True, removes the "Module" prefix from module class names
                                         in the returned dictionary.
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        known_categories = RigModules.get_known_categories_dict()
        unique_modules = RigModules.get_unique_modules_dict(remove_module_prefix=False)

        categorized_modules = {}
        for cat_name, cat_class in known_categories.items():
            modules_attrs = vars(cat_class)
            modules_in_cat = {name: value for name, value in modules_attrs.items() if inspect.isclass(value)}
            list_unique_names = []
            for module in modules_in_cat:
                if module in unique_modules:  # Keys are unique names, values are the list of sides.
                    _name = module
                    if remove_module_prefix:
                        _name = core_str.remove_prefix(input_string=module, prefix="Module")
                    list_unique_names.append(_name)
            categorized_modules[cat_name] = list_unique_names
        return categorized_modules


# Specific categories -------------------------------------------
def get_mirror_category():
    """
    Gets the list of available modules that can be mirrored.

    Returns:
        dict: name as key, module as value.
    """
    unique_modules = RigModules.get_unique_modules_dict()
    mirror_category = {}
    exclude = ["module_utils", "module_attr_hub"]
    for mod_name, mod_list in unique_modules.items():
        skip = False
        for e_mod in exclude:
            if mod_list[0].__module__.endswith(e_mod):
                skip = True
                break
        if not skip:
            mirror_category[mod_name] = mod_list
    return mirror_category


if __name__ == "__main__":
    import pprint

    pprint.pprint(RigModules.get_known_categories_dict())
    pprint.pprint(RigModules.get_categorized_modules_dict())
