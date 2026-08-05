"""Example Animation Label Tracker automation script."""


# The tool injects a ``context`` dictionary when this script runs.
# See the available helpers below for a small full-coverage example.
context["update_file_data"]("quality", "high")
context["update_file_data"]("source", "mocap_shoot_01")
context["update_file_data"]("clipped", True)
context["update_file_data"]("labelled", True)

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
context["update_range_data"]("style", "confident")
context["update_range_data"]("stance", "stand")
context["update_range_data"]("interaction_type", "navigate")
context["update_range_data"]("interaction_scope", "full_body")
context["update_range_data"]("interaction_volumes", "doorway_volume_01")
context["update_range_data"]("interaction_context", "heavy_door")
context["update_range_data"]("events", '{"foot_strike": [15, 30, 45]}')
context["update_range_data"]("auxiliary_context", "Floor is slightly uneven.")
context["refresh_ui"]()
