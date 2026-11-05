# motion_eval

Scores animation quality from 0 to 100 with configurable checks, and writes
summaries, JSON reports, and graphs. Everything below uses only this package plus Maya,
so it can run inside Maya, in `mayapy`, or headless on a server.

## Contents

| Module | Needs | Purpose |
|---|---|---|
| `templates` | Python | Skeletons: built-in templates, Custom Skeleton JSON files |
| `presets` | Python | Which checks run, weights, thresholds, detection settings |
| `checks_general`, `checks_biped`, `checks_base`, `scoring`, `math_utils` | Python | The checks and the scoring |
| `evaluation` | Python (Maya to sample a scene) | Evaluates sampled motion and builds the report |
| `batch_summary` | Python | Combines many reports (totals, sorted files, batch chart data) |
| `outputs` | Python (Qt for graphs) | Writes summaries, JSON reports, and graphs |
| `report_graphs` | Qt | PNG graphs (PySide6, or PySide2 in older Maya versions) |
| `sampling`, `scene_io` | Maya | Reads the open scene, writes the score attribute |
| `usd_scene` | Maya + mayaUsdPlugin | Loads USD files: frame rate, frame range, up axis and unit alignment |
| `runner` | Maya | Headless jobs: open files, evaluate, write every output |

The package only uses relative imports, so the `motion_eval` folder can be copied
anywhere on `sys.path` and imported as `motion_eval`. The examples below use
`from motion_eval import ...`.

## 1. Quick start: evaluate a folder with every output

```python
import os
from motion_eval import runner

job = runner.create_job(
    title="Locomotion Review",
    input_dir="01_input",               # scenes to evaluate (sub-folders included)
    output_dir="02_output",
    result_path="02_output/run_result.json",
    skeleton="maya_humanik",            # "none" = General checks only
    outputs={
        "summary_batch": True,          # batch_summary.txt
        "report_batch": True,           # batch_report.json
        "graphs_batch": True,           # batch_scores.png
        "summary_per_file": True,       # <file>_summary.txt
        "report_per_file": True,        # <file>_report.json
        "graphs_per_file": True,        # <file>_00_summary.png + one PNG per check
        "graphs_only_on_failure": True,
        "file_folders": True,           # False puts every file's outputs directly in output_dir
    },
)

# Relative paths start from base_dir. Starts maya.standalone when needed and hides Maya's console
# messages (quiet=False shows them). Prints one line per file with how many are left, then a summary.
run = runner.run(job, base_dir=os.path.dirname(os.path.abspath(__file__)))

print(run["totals"]["statuses"])        # {"failed": 1, "warning": 0, "passed": 1, "skipped": 0}
print(run["failed_files"])              # failed or errored files
for result in run["results"]:
    print(result["source"], result["status"], result["score"], result["error"])
```

Console output:

```text
Locomotion Review: 19 file(s) | Skeleton: Maya HumanIK | 19 checks (16 on)
Output: D:\reviews\02_output

Starting Maya (this can take a few seconds)...
[ 1/19] 18 left, ~1:07 | FAILED  score  18 | walk_01.mb
[ 2/19] 17 left, ~0:45 | PASSED  score 100 | walk_02.mb
[ 3/19] running... walk_03.mb
```

While a file is evaluated, a `running...` line shows its name; in a console it is
replaced by the result line (in a log file both lines are kept). The run ends with:

```text
Done: 19 evaluated | passed 12 | warning 3 | failed 4 | errors 0
```

`run` raises `ValueError` when the job is invalid or no scene is found
(`runner.validate_job(job)` lists problems without running anything). Errors in a
single file do not stop the run: that file gets `status == "error"` and an `error`
message. A ready-to-copy script is in
[Standalone example script](#7-standalone-example-script).

To evaluate a list of files instead of a folder, pass `file_paths=[...]` to `run`,
or call the lower-level `run_job(file_paths, job, source_root="", progress_callback=None, quiet=False, start_callback=None)` inside
`with runner.maya_session():`.

### Output layout

```text
<output_dir>/
    batch_summary.txt            totals, checks with the most issues, files sorted by score
    batch_report.json            totals + each file's per-check results, sorted by score
    batch_scores.png             one row per file, one colored cell per check
    walk_01/                     (directly in <output_dir> when file_folders is False)
        walk_01_summary.txt
        walk_01_report.json      full report
        walk_01_00_summary.png
        walk_01_01_jitter.png ...
```

With `file_folders` on, sub-folders of `input_dir` are kept under `<output_dir>`.

## 2. Job settings

`runner.create_job(**overrides)` returns a plain dictionary. `outputs` and `score`
are merged with their defaults, so pass only what changes.

| Key | Default | Meaning |
|---|---|---|
| `title` | `"Validate Animation"` | Title of batch summaries and graphs |
| `input_dir` | `""` | Folder searched for scenes by `run()` and the command line |
| `extensions` | `[".ma", ".mb", ".fbx", ".usd", ".usda", ".usdc"]` | Scene extensions searched in `input_dir` |
| `include_subfolders` | `True` | Also search sub-folders of `input_dir` |
| `skeleton` | `"none"` | `"none"`, a built-in key, a Custom Skeleton JSON path, or a template dictionary. Any skeleton adds the Biped checks |
| `preset` | `None` | Preset dictionary, preset JSON path, or `None` for the defaults |
| `range_mode` | `"Playback Range"` | `"Playback Range"`, `"Animation Range"`, `"Keyed Range"`, `"Custom"` |
| `custom_start`, `custom_end` | `1`, `100` | Frames for `"Custom"` |
| `general_scope` | `"All Joints"` | Nodes evaluated without a skeleton: `"All Joints"`, `"Animated Transforms"`, `"Node List"` |
| `node_list` | `[]` | Names or wildcards for `"Node List"`, for example `["prop_ctrl", "*:root"]` |
| `load_mode` | `"open"` | `"open"` the file, or `"import"` into a new scene (FBX and USD are always imported) |
| `align_up_axis` | `True` | USD files: rotate and scale the file into the scene's up axis and unit (see [USD files](#usd-files)) |
| `output_dir` | `""` | Output folder; required when any output is on |
| `outputs` | see above | Which files to write (`outputs.DEFAULT_OUTPUT_OPTIONS`) |
| `write_score` | `False` | Store the score as a Maya attribute (see `score`) |
| `score` | network node `motionEval.motionScore` | `target_mode`, `node_name`, `score_attribute`, `report_attribute`, `write_report`, `write_policy` (see `scene_io.write_score`) |
| `save_copy_dir` | `""` | Save each evaluated scene (with its score) as a `.ma` copy here. Inputs are never overwritten |
| `result_path` | `""` | `run()` writes a JSON summary of the run here (scores, errors, output paths) |

Relative paths (`input_dir`, `output_dir`, `result_path`, `save_copy_dir`, and
skeleton or preset `.json` paths) start from the `base_dir` given to `run()`; the
command line uses the job file's folder.

The skeleton decides the mode: with
`"none"` only the General checks run (on `general_scope` nodes); with a skeleton
the General and Biped checks run on the joints the skeleton maps.

### Jobs as JSON

```python
runner.save_job(job, "D:/reviews/locomotion_job.json")
job = runner.load_job("D:/reviews/locomotion_job.json")   # missing keys get the defaults
```

```json
{
    "title": "Locomotion Review",
    "skeleton": "D:/pipeline/skeletons/hero_skeleton.json",
    "preset": "D:/pipeline/presets/locomotion.json",
    "range_mode": "Playback Range",
    "output_dir": "D:/reviews/locomotion",
    "outputs": {"report_batch": true, "graphs_batch": true, "graphs_per_file": true}
}
```

### USD files

`.usd`, `.usda`, and `.usdc` files are evaluated like Maya scenes (Maya's
`mayaUsdPlugin` must be available; it ships with Maya). Each file is loaded by
`usd_scene.load_usd_scene`:

1. A new scene gets the file's frame rate (time codes per second), so every USD
   time code is one Maya frame and speeds and gravity are measured correctly.
2. The file is imported with `mayaUSDImport`; skeleton animation becomes keyed joints.
3. The playback and animation range are set to the file's start and end time codes,
   so `range_mode="Playback Range"` evaluates exactly the exported frames.
4. With `align_up_axis` on (default), a file whose up axis differs from the scene
   (for example a Z-up export in a Y-up Maya scene) is grouped under `usd_align`
   and rotated into the scene's up axis. The group is also scaled when the file's
   `metersPerUnit` differs from the scene unit.

USD exports usually keep only the skeleton, so the Custom Skeleton should list the
joint names as they appear in the USD file (namespaces are usually stripped).

## 3. Skeletons

```python
from motion_eval import templates

templates.get_builtin_template_keys()                  # ["maya_humanik", "unreal_mannequin"]
humanik = templates.get_builtin_template("maya_humanik")

# Custom Skeleton: map each role to one or more candidate joint names.
# Prefixes such as "Character1_" and namespaces are matched automatically.
hero = templates.create_template(
    name="Hero Skeleton",
    up_axis="scene",                                   # "scene", "y", or "z"
    roles={
        "hips": ["pelvis"], "spine": ["spine_01"], "head": ["head"],
        "left_up_leg": ["thigh_l"], "left_leg": ["calf_l"], "left_foot": ["foot_l"], "left_toe": ["ball_l"],
        "right_up_leg": ["thigh_r"], "right_leg": ["calf_r"], "right_foot": ["foot_r"], "right_toe": ["ball_r"],
    },
)
print(templates.validate_template(hero, require_biped=True))   # [] when every required role is mapped
templates.save_template(hero, "D:/pipeline/skeletons/hero_skeleton.json")
hero = templates.load_template("D:/pipeline/skeletons/hero_skeleton.json")
```

Roles: `templates.ROLE_KEYS`. Roles required by the Biped checks:
`templates.REQUIRED_BIPED_ROLES` (hips, spine, head, both thighs, knees, and feet).

Inside Maya, `sampling.resolve_template_in_scene(template, require_biped=True)`
shows which joint each role resolved to, and
`templates.detect_builtin_template(node_paths)` picks the best built-in match.

## 4. Checks and thresholds (presets)

A preset stores only the values that differ from the defaults. Every setter
returns a new compact preset.

```python
from motion_eval import presets

preset = presets.create_preset(name="Locomotion")
preset = presets.set_check_value(preset, "balance", "enabled", True)          # off by default
preset = presets.set_check_value(preset, "gait_asymmetry", "enabled", True)   # off by default
preset = presets.set_check_value(preset, "foot_slide", "fail_below", 60)      # scoring setting
preset = presets.set_check_value(preset, "foot_slide", "slide_speed", 0.4)    # detection parameter
preset = presets.set_global_value(preset, "overall_fail_below", 60)
preset = presets.set_global_value(preset, "ignore_ranges", "1-10")            # skip a T-pose lead-in
print(presets.validate_preset(preset))                                        # [] when valid
presets.save_preset(preset, "D:/pipeline/presets/locomotion.json")
```

Discover what can be set:

```python
for check in presets.CHECK_DEFINITIONS:
    print(check.mode, check.key, check.label, [parameter.key for parameter in check.parameters])
print([parameter.key for parameter in presets.SCORING_PARAMETERS])   # enabled, weight, warn_below, fail_below, ...
print([parameter.key for parameter in presets.GLOBAL_PARAMETERS])    # score_method, overall_fail_below, ...
print(presets.get_check_defaults("foot_slide"))                      # every default value of one check
print(presets.SCORING_PARAMETERS_BY_KEY["fail_below"].tooltip)       # what a setting does
```

Checks off by default: `below_ground` (needs the floor at a known height),
`balance` (props, sitting, and leaning trigger it), and `gait_asymmetry` (turns,
starts, and stops trigger it). Enable them for data where they apply.

Preset files saved with `presets.save_preset` can be passed as `job["preset"]` directly.

## 5. Step by step (custom pipelines)

`run_job` is a thin loop over these calls. Use them directly to control loading,
naming, or parallelism yourself.

```python
from motion_eval import batch_summary, outputs, runner

job = runner.create_job(skeleton="maya_humanik", output_dir="D:/out", outputs={"graphs_per_file": True})
template = runner.resolve_skeleton(job["skeleton"])
preset = runner.resolve_job_preset(job["preset"], template)     # mode set by the skeleton

entries = []
for file_path in ["D:/anims/walk_01.ma", "D:/anims/run_01.ma"]:
    runner.load_scene(file_path)
    report = runner.evaluate_open_scene(
        preset, template=template, range_mode="Playback Range",
        include_series=outputs.needs_series(job["outputs"]),     # graph data only when needed
    )
    outputs.write_file_outputs(report, file_path, job["output_dir"], job["outputs"])
    entries.append(batch_summary.build_batch_entry(report, file_path))

outputs.write_batch_outputs(entries, job["output_dir"], job["outputs"], title="Review")
```

The open scene can also be evaluated with no files involved:

```python
from motion_eval import evaluation, presets, runner, templates

report = runner.evaluate_open_scene(presets.create_preset(mode="biped"),
                                    template=templates.get_builtin_template("maya_humanik"))
print("\n".join(evaluation.summarize_report(report)))
```

### Report contents

`report["score"]` (0-100), `report["status"]` (`passed`, `warning`, `failed`),
`report["frame_range"]`, `report["mode"]`, `report["template"]`, `report["settings"]`,
and `report["checks"]`: one entry per check with `key`, `label`, `score`, `status`,
`flagged_frames`, `events`, `spans` (flagged frame ranges), and `offenders`.
Disabled checks have status `disabled`. Use `evaluation.strip_series(report)`
before saving a report made with `include_series=True`.

### Parallel servers

Run one `mayapy` process per file list (Maya scenes are not thread-safe), keep
each result's `entry`, then build the batch outputs once:

```python
import json
from motion_eval import outputs

entries = []
for result_path in ["D:/out/worker_1.json", "D:/out/worker_2.json"]:
    with open(result_path, "r", encoding="utf-8") as result_file:
        entries.extend(result["entry"] for result in json.load(result_file)["results"] if result["entry"])
outputs.write_batch_outputs(entries, "D:/out", {"summary_batch": True, "graphs_batch": True})
```

Each worker's `--result` file (command line below) already has this shape; from
Python use `outputs.write_json_file(path, runner.build_result_summary(run))`. In each
worker, turn the batch outputs off (they are rebuilt here) and leave the per-file
outputs on.

## 6. Command line (headless)

```bash
mayapy -m motion_eval.runner job.json
mayapy -m motion_eval.runner job.json D:/anims/walk_01.ma D:/anims/run_01.ma --result D:/out/result.json
```

- Without files, the scenes come from the job's `input_dir`.
- Relative paths in the job start from the job file's folder.
- `--result` writes totals, batch output paths, failed files, errors, and one compact
  result per file (with its batch `entry`) as JSON (same as the job's `result_path`).
- `--verbose` shows Maya's own console messages (hidden by default).
- Exit code: `0` every file passed or warned, `1` some file failed or errored,
  `2` invalid job.

`maya.standalone` is initialized and uninitialized automatically. Run from the
folder that contains `motion_eval` (or add it to `PYTHONPATH`).

## 7. Standalone example script

A complete script to hand to other people. Save it next to an `01_input` folder and
run it with `mayapy run_validate_animation.py` (or a `.bat` that calls mayapy).

```python
import os
import sys

# Folder that CONTAINS the "motion_eval" folder.
sys.path.insert(0, r"D:/pipeline/python")
from motion_eval import presets, runner

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Which checks run: start from the defaults and change only what you need.
checks = presets.create_preset()
checks = presets.set_check_value(checks, "balance", "enabled", True)        # off by default
# checks = presets.set_check_value(checks, "foot_slide", "fail_below", 60)  # stricter foot sliding

job = runner.create_job(
    input_dir="01_input",
    output_dir="02_output",
    result_path="02_output/run_result.json",
    skeleton="maya_humanik",       # "none", "unreal_mannequin", or "data/my_rig.json"
    preset=checks,
    outputs={"graphs_batch": True, "summary_per_file": True, "graphs_per_file": True},
)

if __name__ == "__main__":
    try:
        result = runner.run(job, base_dir=THIS_FOLDER)
    except ValueError as error:
        print(f"Setup problem: {error}")
        sys.exit(2)
    sys.exit(1 if result["failed_files"] else 0)
```
