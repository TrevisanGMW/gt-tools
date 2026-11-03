# Checks the scene playback range against expected values.
# Set an expected value to None to skip that part of the check.

EXPECTED_START = 0
EXPECTED_END = None
MINIMUM_FRAMES = 2

start_frame = cmds.playbackOptions(query=True, minTime=True)
end_frame = cmds.playbackOptions(query=True, maxTime=True)
frame_count = int(end_frame - start_frame) + 1

if EXPECTED_START is not None:
    validation.check(
        start_frame == EXPECTED_START,
        f"Playback starts at {start_frame:g}, expected {EXPECTED_START}.",
        start_frame=start_frame,
    )
if EXPECTED_END is not None:
    validation.check(
        end_frame == EXPECTED_END,
        f"Playback ends at {end_frame:g}, expected {EXPECTED_END}.",
        end_frame=end_frame,
    )
validation.check(
    frame_count >= MINIMUM_FRAMES,
    f"Playback range is too short: {frame_count} frame(s).",
    frame_count=frame_count,
)
validation.info(f"Playback range: {start_frame:g}-{end_frame:g} ({frame_count} frames)")
