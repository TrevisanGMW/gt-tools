# Reports unknown nodes and unknown plugin requirements, which usually mean the
# file references a plugin that is not available on this machine.

unknown_nodes = cmds.ls(type=["unknown", "unknownDag", "unknownTransform"], long=True) or []
for node_name in unknown_nodes:
    validation.error("Unknown node found.", node=node_name)

unknown_plugins = cmds.unknownPlugin(query=True, list=True) or []
for plugin_name in unknown_plugins:
    validation.warning(f"Scene requires an unknown plugin: {plugin_name}")

if not unknown_nodes and not unknown_plugins:
    validation.info("No unknown nodes or plugins.")
