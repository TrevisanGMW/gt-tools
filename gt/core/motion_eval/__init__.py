"""
Motion Evaluation - Scores animation quality with configurable, skeleton-agnostic checks.

Pure modules (no Maya imports):
    math_utils, templates, checks_base, checks_general, checks_biped, presets, scoring, evaluation,
    batch_summary, outputs (graphs import Qt lazily)

Maya runtime modules (lazy Maya imports):
    sampling, scene_io, runner

The package uses relative imports only, so it can also be copied and imported on its own.
See README.md for headless jobs (runner.run_job) and examples.
"""

__version_tuple__ = (1, 0, 0)
__version__ = ".".join(str(number) for number in __version_tuple__)
