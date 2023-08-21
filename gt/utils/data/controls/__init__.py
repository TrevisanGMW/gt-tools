"""
Control Creation Scripts (Complex Curves, or Curves with Logic)
Similar to curves, the output of a control is usually a nurbs or a bezier element.
The difference is that a control is usually composed of multiple elements or extra logic.
For example, a control might have extra attributes that allow for shape change or transform limits.

Note: All controls return a "ControlData" object as their return value.
"ControlData" can be found in "gt.utils.data.control_data"

Note:
If the control contains a keyword argument called "name" it will be automatically inherited by the Control object.
e.g.
    Function definition
    >>> def create_scalable_arrow(name='scalable_arrow', initial_scale=1):
    Control object creation
    >>> scalable_arrow = Control(build_function=cluster_driven.create_scalable_two_sides_arrow)
    Name value = "scalable_arrow"
    >>> print(scalable_arrow.get_name())
"""