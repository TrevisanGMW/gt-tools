import inspect
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
    ModuleBipedLeg = ModuleBipedLeg
    ModuleBipedLegLeft = ModuleBipedLegLeft
    ModuleBipedLegRight = ModuleBipedLegRight
    ModuleBipedArm = ModuleBipedArm
    ModuleBipedArmLeft = ModuleBipedArmLeft
    ModuleBipedArmRight = ModuleBipedArmRight
    ModuleBipedDigits = ModuleBipedFingers
    ModuleBipedFingersLeft = ModuleBipedFingersLeft
    ModuleBipedFingersRight = ModuleBipedFingersRight

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
    prefixes = ["Biped"]
    categories = {}
    unique_modules = {}

    # Create lists of modules with the same name that end with sides (a.k.a. Unique Modules)
    for name, module in RigModules.get_dict_modules().items():
        _name = remove_prefix(input_string=name, prefix="Module")
        _name = remove_suffix(input_string=_name, suffix="Left")
        _name = remove_suffix(input_string=_name, suffix="Right")
        _name = remove_suffix(input_string=_name, suffix="Center")
        if _name in unique_modules:
            unique_modules.get(_name).append(module)
        else:
            unique_modules[_name] = [module]

    # Create categories based on the name which the module starts with. Otherwise it's general
    for mod_name, mod_list in unique_modules.items():
        _category = "General"
        for prefix in prefixes:
            if mod_name.startswith(prefix):
                _category = prefix
        if _category in categories:
            categories.get(_category).append(mod_list)
        else:
            categories[_category] = [mod_list]


if __name__ == "__main__":
    import pprint
    # pprint.pprint(RigModules.get_dict_modules())
    pprint.pprint(RigModulesCategories)
