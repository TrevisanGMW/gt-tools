import inspect
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
    ModuleSpine = ModuleSpine
    ModuleRoot = ModuleRoot
    # Biped
    ModuleBipedLegLeft = ModuleBipedLegLeft
    ModuleBipedLegRight = ModuleBipedLegRight
    ModuleBipedArm = ModuleBipedArm
    ModuleBipedLeg = ModuleBipedLeg
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


if __name__ == "__main__":
    import pprint
    pprint.pprint(RigModules.get_dict_modules())
