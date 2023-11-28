import inspect
from gt.ui import resource_library
from gt.utils.string_utils import remove_suffix, remove_prefix
from gt.tools.auto_rigger.rig_framework import ModuleGeneric
from gt.tools.auto_rigger.rig_module_root import ModuleRoot
from gt.tools.auto_rigger.rig_module_biped_leg import (ModuleBipedLeg,
                                                       ModuleBipedLegLeft,
                                                       ModuleBipedLegRight)
from gt.tools.auto_rigger.rig_module_spine import ModuleSpine
from gt.tools.auto_rigger.rig_module_biped_arm import (ModuleBipedArm,
                                                       ModuleBipedArmLeft,
                                                       ModuleBipedArmRight)
from gt.tools.auto_rigger.rig_module_biped_finger import (ModuleBipedFingers,
                                                          ModuleBipedFingersLeft,
                                                          ModuleBipedFingersRight)


class RigModules:
    # General
    ModuleGeneric = ModuleGeneric
    ModuleRoot = ModuleRoot
    ModuleSpine = ModuleSpine
    # Biped
    ModuleBipedArm = ModuleBipedArm
    ModuleBipedArmLeft = ModuleBipedArmLeft
    ModuleBipedArmRight = ModuleBipedArmRight
    ModuleBipedFingers = ModuleBipedFingers
    ModuleBipedFingersLeft = ModuleBipedFingersLeft
    ModuleBipedFingersRight = ModuleBipedFingersRight
    ModuleBipedLeg = ModuleBipedLeg
    ModuleBipedLegLeft = ModuleBipedLegLeft
    ModuleBipedLegRight = ModuleBipedLegRight

    @staticmethod
    def get_dict_modules():
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        modules_attrs = vars(RigModules)
        class_attributes = {name: value for name, value in modules_attrs.items() if inspect.isclass(value)}
        return class_attributes

    @staticmethod
    def get_modules():
        """
        Gets the available module classes stored in the RigModules class.
        Returns:
            list: A list of modules, these use the ModuleGeneric as their base.
        """
        return list(RigModules.get_dict_modules().values())

    @staticmethod
    def get_module_names():
        """
        Gets the name of all available modules.
        Returns:
            list: A list of module names (strings)
        """
        return list(RigModules.get_dict_modules().keys())


class RigModulesCategories:
    known_categories = {"General": resource_library.Icon.rigger_module_generic,
                        "Biped": resource_library.Icon.rigger_template_biped}
    categories = {}
    unique_modules = {}

    # Create lists of modules with the same name that end with sides (a.k.a. Unique Modules)
    for name, module in RigModules.get_dict_modules().items():
        _name = remove_prefix(input_string=name, prefix="Module")
        _name = remove_suffix(input_string=_name, suffix="Left")
        _name = remove_suffix(input_string=_name, suffix="Right")
        if _name in unique_modules:
            unique_modules.get(_name).append(module)
        else:
            unique_modules[_name] = [module]

    # Create categories based on the name which the module starts with. Otherwise, it's general.
    for mod_name, mod_list in unique_modules.items():
        _category = "General"  # Default (Misc)
        for prefix in known_categories:
            if mod_name.startswith(prefix) and prefix != _category:
                _category = prefix
        if mod_name not in unique_modules:
            continue  # Skip Sides
        if _category in categories:
            categories.get(_category).append(mod_name)
        else:
            categories[_category] = [mod_name]


if __name__ == "__main__":
    import pprint
    # pprint.pprint(RigModules.get_dict_modules())
    pprint.pprint(RigModulesCategories.categories)
