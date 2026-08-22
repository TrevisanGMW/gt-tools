"""Example Annotation Tracker automation script."""


# The tool injects a ``context`` dictionary when this script runs.
# See the available helpers below for a small full-coverage example.
last_used_data = context["get_last_used_data"]()
print("Last used tracker data from Prefs:")
print(last_used_data)

context["update_file_data"]("quality", "high")
context["update_file_data"]("source", "mocap_shoot_01")
context["update_file_data"]("clipped", True)
context["update_file_data"]("annotated", True)
context["update_file_data"]("commercial_use", True)
context["update_file_data"]("style", "confident")
context["update_file_data"](
    "context",
    "Character walks through a heavy doorway.",
)

start_frame = int(context["cmds"].playbackOptions(q=True, min=True))
end_frame = int(context["cmds"].playbackOptions(q=True, max=True))
context["timeline_ranges"].clear()
context["create_range"](
    "Auto_Generated",
    start_frame,
    end_frame,
    (100, 200, 100),
)

context["update_range_data"]("state", "walk")
context["update_range_data"]("stance", "stand")
context["update_range_data"]("interaction_type", "navigate")
context["update_range_data"]("interaction_scope", "full_body")
context["update_range_data"]("interaction_volumes", "doorway_volume_01")
context["update_range_data"]("interaction_item", "heavy_door")
context["update_range_data"]("contact_attributes", "doorway_ctrl.open, doorway_ctrl.close")
context["update_range_data"](
    "event",
    '{"foot_strike": {"start_frame": 15, "end_frame": 25}}',
)
context["refresh_ui"]()
