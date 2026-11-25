"""
Motion Evaluation - Scores animation quality with configurable, skeleton-agnostic checks.

Pure modules (no Maya imports):
    math_utils, templates, checks_base, checks_general, checks_biped, presets, scoring, evaluation,
    batch_summary, outputs (graphs import Qt lazily)

Host-agnostic scene modules (every scene call goes through hosts.get_host()):
    sampling, scene_io, runner, sample_io, console, cli

Hosts (the only modules that import maya or bpy, lazily):
    hosts.maya_host, hosts.blender_host, hosts.sample_host (plain Python, motion sample files),
    usd_scene (Maya USD loading)

Checks never talk to a host: they read checks_base.MotionData, so a new check works in
Maya, Blender, and plain Python at once (see README.md, "Adding a check").

The package uses relative imports only, so it can also be copied and imported on its own.
See README.md for headless jobs (runner.run_job) and examples.
"""

__version_tuple__ = (1, 1, 0)
__version__ = ".".join(str(number) for number in __version_tuple__)
