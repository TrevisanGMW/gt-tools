"""Example Animation Clip Tracker automation script.

The Clip Tracker injects a ``context`` dictionary when this file runs. The
available helpers create and update clips while refreshing the Clip Tracker UI:

context["cmds"]
context["create_clip"](start_frame, end_frame, name="", active=True)
context["set_clip_start"](clip_index, start_frame)
context["set_clip_end"](clip_index, end_frame)
context["set_clip_name"](clip_index, name)
context["set_clip_active"](clip_index, is_active)
context["get_clips"]()
context["refresh_ui"]()
"""


# ``create_clip`` returns the list index of the new frame range.
clip_index = context["create_clip"](
    start_frame=100,
    end_frame=120,
    name="Automation Example",
    active=True,
)

# Each setter updates the current clip data and refreshes the visible rows.
context["set_clip_start"](clip_index, 105)
context["set_clip_end"](clip_index, 135)
context["set_clip_name"](clip_index, "Automation Updated")

# The active value controls the checkbox shown in the Animation Clips tab.
context["set_clip_active"](clip_index, False)
context["set_clip_active"](clip_index, True)
