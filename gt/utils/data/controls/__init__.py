"""
Control Creation Scripts
Similar to curves, the output of a control is usually a nurbs or a bezier element.
The difference is that a control is usually composed of multiple elements or extra logic.
For example, a control might have extra attributes that allow for shape change or transform limits.

Note: All controls return a "ControlData" object as their return value.
"ControlData" can be found in "gt.utils.data.control_data"
"""