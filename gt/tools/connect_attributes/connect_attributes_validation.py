"""Pure attribute type checks shared by scene inspection and execution."""


SCALAR_TYPES = frozenset((
    "bool", "byte", "char", "short", "long", "int64", "enum", "float",
    "double", "doubleAngle", "doubleLinear", "time",
))
VECTOR_TYPES = {
    "short2": 2, "long2": 2, "float2": 2, "double2": 2,
    "short3": 3, "long3": 3, "float3": 3, "double3": 3,
}
DATA_TYPES = frozenset((
    "string", "matrix", "fltMatrix", "mesh", "nurbsCurve", "nurbsSurface",
    "lattice", "doubleArray", "Int32Array", "stringArray", "vectorArray",
    "pointArray", "matrixArray", "message",
))


def check_connection_types(source_type, target_type, use_utility=False, add_reverse=False):
    """Checks known incompatibilities without rejecting numeric conversions.

    Unknown and custom data types are left for Maya to validate at execution.

    Args:
        source_type (str): Maya source attribute type.
        target_type (str): Maya target attribute type.
        use_utility (bool, optional): Whether a math/logic node is inserted.
        add_reverse (bool, optional): Whether a Reverse node is inserted.

    Returns:
        tuple: Status key and an explanatory message, empty when compatible.
    """
    source_dimension = 1 if source_type in SCALAR_TYPES else VECTOR_TYPES.get(source_type)
    target_dimension = 1 if target_type in SCALAR_TYPES else VECTOR_TYPES.get(target_type)
    if use_utility or add_reverse:
        if source_dimension not in (1, 3):
            return "blocked", "Math/logic and Invert require a number or a three-component vector."
        source_type = "float" if source_dimension == 1 else "float3"
    if source_dimension and target_dimension:
        if source_dimension != target_dimension:
            return "blocked", f"Incompatible dimensions: {source_dimension} -> {target_dimension}."
        return "ready", ""
    if source_type == target_type and source_type in DATA_TYPES:
        return "ready", ""
    known_source = source_dimension or source_type in DATA_TYPES
    known_target = target_dimension or target_type in DATA_TYPES
    if known_source and known_target:
        return "blocked", f"Incompatible attribute types: {source_type} -> {target_type}."
    return "warning", f"Maya will validate custom/compound types: {source_type} -> {target_type}."
