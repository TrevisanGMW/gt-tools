"""
Parametric (Python) Mesh Creation Scripts (Meshes with Logic or extra components)
Similar to meshes, the output of a parametric mesh is usually a polygon or a surface element.
The difference is that a parametric mesh can be modified to look different before creation. It might also contain logic.
For example, a parametric mesh might have extra attributes that allow for shape change or transform limits.

Note: All parametric meshes return a "MeshData" object as their return value.
"MeshData" can be found in "gt.utils.data.py_meshes.mesh_data"

Note:
If the parametric mesh contains a keyword argument called "name" it will be  inherited by the ParametricMesh object.
e.g.
    Function definition
    >>> def create_kitchen_cabinet(name='scale_volume_kitchen_cabinet'):
    ParametricMesh object creation
    >>> scale_kitchen_cabinet = ParametricMesh(build_function=scale_volume.create_kitchen_cabinet)
    Name value = "scale_volume_kitchen_cabinet"
    >>> print(scale_kitchen_cabinet.get_name())
"""
