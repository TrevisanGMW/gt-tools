from gt.tools.auto_rigger.template_biped import create_template_biped
import types

class RigTemplates:
    # General
    TemplateBiped = create_template_biped

    @staticmethod
    def get_dict_templates():
        """
        Gets all available modules as a dictionary. Key is the name of the module and value is the class.
        Returns:
            dict: Dictionary where the key is the name of the module and value is the class.
                  e.g. 'ModuleBipedArm': <class 'ModuleBipedArm'>
        """
        modules_attrs = vars(RigTemplates)
        callable_attributes = {name: value for name, value in modules_attrs.items()
                               if isinstance(value, types.FunctionType)}
        return callable_attributes

    @staticmethod
    def get_templates():
        """
        Gets the available template functions. The output of these callable functions is a RigProject.
        Returns:
            list: A list of template functions, these are of the type callable.
                  When called, they produce a RigProject describing the template.
        """
        return list(RigTemplates.get_dict_templates().values())

    @staticmethod
    def get_template_names():
        """
        Gets the name of all available templates.
        Returns:
            list: A list of template names (strings)
        """
        return list(RigTemplates.get_dict_templates().keys())


if __name__ == "__main__":
    import pprint
    pprint.pprint(RigTemplates.get_dict_templates())
