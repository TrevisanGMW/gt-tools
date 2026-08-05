"""
 Mesh Morpher Constants

Import Line:
    import gt.tools.mesh_morpher.morpher_constants as tools_morpher_const
"""


class MeshMorpherConstants:
    def __init__(self):
        """
        Constant values used by the Mesh Morpher System.
        e.g. Attribute names, dictionary keys or initial values.
        """

    # General Keys and Attributes
    DATA_EXTENSION = "json"
    BASE_FILTER = "All Files (*);;JSON Files (*.json)"
    DATA_FILTER = f"Json File (*.{DATA_EXTENSION})"
    DEFAULT_RBF_CACHE_FOLDER = r"R:\DccTools\maya\external\assets\mesh_morpher_cache"
