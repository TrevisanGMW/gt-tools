# motion_eval

Scores animation quality from 0 to 100 with configurable checks, and writes
summaries, JSON reports, and graphs. Everything below uses only this package plus a
program that can open the files:

- **Maya**: inside Maya, in `mayapy`, or headless on a server (every format below).
- **Blender**: `blender --background` (no Maya license needed; see [Blender](#blender)).
- **Plain Python 3**: motion sample files only (see [Motion sample files](#motion-sample-files)).

The checks never talk to Maya or Blender, so every check gives the same result in each
of them (see [Hosts](#8-hosts-maya-blender-plain-python) and [Adding a check](#9-adding-a-check)).

## Contents

| Module | Needs | Purpose |
|---|---|---|
| `templates` | Python | Skeletons: built-in templates, Custom Skeleton JSON files |
| `presets` | Python | Which checks run, weights, thresholds, detection settings |
| `checks_general`, `checks_biped`, `checks_limits`, `checks_pose`, `checks_base`, `scoring`, `math_utils` | Python | The checks and the scoring |
| `evaluation` | Python (a host to sample a scene) | Evaluates sampled motion and builds the report |
| `batch_summary` | Python | Combines many reports (totals, sorted files, batch chart data) |
| `outputs` | Python (Qt for graphs) | Writes summaries, JSON reports, and graphs |
| `report_graphs` | Qt | PNG graphs (PySide6, or PySide2 in older Maya versions; Blender needs `PySide6-Essentials` from pip) |
| `sampling`, `scene_io` | A host | Reads the open scene, writes the score attribute (through `hosts`) |
| `runner`, `cli` | A host | Headless jobs: open files, evaluate, write every output |
| `sample_io` | Python | Saves and loads motion sample files (`.motion.json`) |
| `hosts` | Maya, Blender, or Python | The only code that talks to a program: `maya_host`, `blender_host`, `sample_host` |
| `usd_scene` | Maya + mayaUsdPlugin | Loads USD files in Maya: frame rate, frame range, up axis and unit alignment |
| `console` | Python | Hides the host's console output while files load |
| `repairs` | Python (a host that can write keys to apply) | Targeted fixes for reported problems, driven by a patch manifest |

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
| `host` | `"auto"` | Program that opens the files: `"auto"` (the program running the script), `"maya"`, or `"blender"`. Motion sample files always use plain Python |
| `input_dir` | `""` | Folder searched for scenes by `run()` and the command line |
| `extensions` | `[".ma", ".mb", ".fbx", ".usd", ".usda", ".usdc"]` | Scene extensions searched in `input_dir`. Left at the default, the list follows the host (Blender: `.blend`, `.fbx`, `.usd*`, `.bvh`). `.motion.json` is always searched |
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
| `write_score` | `False` | Store the score in the scene: a Maya attribute, or a Blender custom property (see `score`) |
| `score` | network node `motionEval.motionScore` | `target_mode`, `node_name`, `score_attribute`, `report_attribute`, `write_report`, `write_policy` (see `scene_io.write_score`) |
| `save_copy_dir` | `""` | Save each evaluated scene (with its score) as a `.ma` copy (`.blend` in Blender) here. Inputs are never overwritten |
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
   The importer's own axis and unit conversion (on by default in Maya 2026 and later)
   is turned off, so every Maya version imports the same way.
3. The playback and animation range are set to the file's start and end time codes,
   so `range_mode="Playback Range"` evaluates exactly the exported frames.
4. With `align_up_axis` on (default), a file whose up axis differs from the scene
   (for example a Z-up export in a Y-up Maya scene) is grouped under `usd_align`
   and rotated into the scene's up axis. The group is also scaled when the file's
   `metersPerUnit` differs from the scene unit.

USD exports usually keep only the skeleton, so the Custom Skeleton should list the
joint names as they appear in the USD file (namespaces are usually stripped).

### Blender

The same jobs run in Blender, so files can be evaluated without a Maya license:

```bash
blender --background --factory-startup --python motion_eval/cli.py -- job.json
blender --background --factory-startup --python run_validate_animation.py
```

Everything after `--` goes to the script. With `"host": "auto"` a job uses Blender when
the script runs in Blender; `"host": "blender"` makes that explicit (a job that names
Blender fails with a clear message when run in another program).

| File | In Blender |
|---|---|
| `.blend` | Opened |
| `.fbx` | Imported into an empty scene (keys kept on their frames, leaf bones kept) |
| `.usd`, `.usda`, `.usdc` | Imported into an empty scene, at the file's frame rate and frame range |
| `.bvh` | Imported into an empty scene, at the file's frame rate |
| `.ma`, `.mb` | Not supported: export them to FBX or USD in Maya first |

How Blender data is read:

- **Joints** are the bones of every armature; a bone's path is its armature followed by
  its bone chain (`|Armature|Hips|Spine`). Skeleton templates match the bone names, and
  prefixes such as `mixamorig:` work like Maya namespaces.
- **Transforms** are objects. **Up axis** is always Z, **units** come from the scene unit
  scale (1.0 = meters); the checks handle both.
- **Playback Range** is the preview range when it is on, otherwise the scene range;
  **Animation Range** is the scene range.
- **Scores** (`write_score`) are custom properties, by default on an empty object named
  `motionEval`.

Differences from Maya that come from the files, not the checks:

- Maya joints can keep their children's length when scaled (segment scale compensate).
  Blender bones (and USD) cannot, so scaling a spine also counts as bone stretch.
- Blender's USD importer replaces NaN values with 0, so Invalid Values cannot see NaNs
  authored in USD files (FBX keeps them).

**Graphs need Qt.** Blender does not include it. Without it, graphs are skipped and the
run prints a warning with the command that installs it; text and JSON outputs are still
written. The command installs `PySide6-Essentials` with Blender's own Python into
Blender's user module folder (always on Blender's `sys.path`, including background runs):

```python
from motion_eval import hosts, report_graphs

# Run inside Blender to print the command for this Blender:
print(hosts.get_host("blender").build_pip_install_command(report_graphs.QT_PIP_PACKAGES))
```

`report_graphs.is_qt_available()` says whether graphs can be written in the running Python.

### Motion sample files

A motion sample (`.motion.json`, see `sample_io`) stores what the checks read: world
matrices per frame, parents, frame rate, units, and up axis. Samples are evaluated in
plain Python 3 (no Maya, no Blender), so motion that never lives in a 3D program, such as
the output of a motion model, can be scored directly:

```python
from motion_eval import math_utils, sample_io

hips_matrices = [math_utils.compose_matrix(position=(0.0, 95.0, frame * 2.0)) for frame in range(60)]
sample = sample_io.create_sample(
    fps=30, start_frame=1, up_axis="y", meters_per_unit=0.01,
    nodes={"|Hips": {"parent": None, "matrices": hips_matrices}},   # plus every other joint
)
sample_io.save_sample(sample, "D:/model_output/walk_01.motion.json")
```

Put the files in a job's `input_dir` and run the job with any Python 3
(`python motion_eval/cli.py job.json`). A sample of an open Maya or Blender scene is
saved with `sample_io.save_sample(sampling.sample_scene(...), path)`.

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

Inside Maya or Blender, `sampling.resolve_template_in_scene(template, require_biped=True)`
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
`balance` (props, sitting, and leaning trigger it), `gait_asymmetry` (turns,
starts, and stops trigger it), `elbow_side_bend` (forearm roll looks like side bend in
normal poses), and `t_pose` (see below). Enable them for data where they apply.

### Joint limits

`elbow_hyperextension`, `elbow_side_bend`, `knee_side_bend`, `wrist_bend`,
`forearm_twist`, and `head_turn` (in `checks_limits.py`) flag poses a body cannot
reach. Joint axis conventions differ between skeletons, so they never read rotation
values. Each joint learns its normal pose from the clip, in its parent joint's space:

- Elbows and knees learn their hinge axis from frames bent 25 degrees or more. A joint
  that never bends that far is reported in the details and not measured. Side bend is
  only measured while the joint bends 30 degrees or more.
- Wrist bend, forearm twist, and head turn measure the distance from the clip's median
  pose. A joint held in an impossible pose for most of a clip becomes its own median and
  is not flagged.
- The arm checks need the arm, forearm, and hand roles of at least one side. Head turn
  uses the chest role, or the lowest spine joint when the chest is not mapped.

The joint limits also read joint rotations: wrist bend uses the hand's rotation, forearm
twist uses the upper arm and hand, and head turn uses the chest and head.

### T-pose

`t_pose` (in `checks_pose.py`, off by default) flags calibration poses left in a clip.
A frame matches when both arms point sideways at the pose height with straight elbows,
and the trunk and knees are straight. It only counts while the arms and head hold still
(`hold_speed`) for `min_hold_seconds`, so motion that passes through a similar pose is
ignored. `search` = `edges` (default) only reports poses touching the first or last
`edge_seconds`. `pose_type` is `t` (default), `a` (arms about 45 degrees down), or `both`.
A one-frame bind pose on frame 0 is shorter than the hold time and is not reported.

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

Run one `mayapy` (or `blender --background`) process per file list (scenes are not thread-safe), keep
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
blender --background --factory-startup --python motion_eval/cli.py -- job.json D:/anims/walk_01.fbx
python motion_eval/cli.py job.json                     # motion sample files only
```

- Without files, the scenes come from the job's `input_dir`.
- Relative paths in the job start from the job file's folder.
- `--result` writes totals, batch output paths, failed files, errors, and one compact
  result per file (with its batch `entry`) as JSON (same as the job's `result_path`).
- `--verbose` shows the host's own console messages (hidden by default).
- `--host auto|maya|blender` overrides the job's `host`.
- Exit code: `0` every file passed or warned, `1` some file failed or errored,
  `2` invalid job.

`maya.standalone` is initialized and uninitialized automatically. Run `-m` from the
folder that contains `motion_eval` (or add it to `PYTHONPATH`); `cli.py` can be run by
path from anywhere. In Blender, add `--python-exit-code 2` to get exit code 2 when the
script itself crashes.

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

## 8. Hosts (Maya, Blender, plain Python)

A **host** is the only code that talks to a program. Everything else (checks, scoring,
outputs, runner) goes through it, which is why a check written once runs everywhere.

```text
runner / evaluation / sampling / scene_io      host-agnostic: call hosts.get_host()
        |
hosts/host_base.SceneHost                      the interface (load, ranges, nodes, matrices, scores)
        |-- hosts/maya_host.MayaHost           maya.cmds + OpenMaya (lazy imports)
        |-- hosts/blender_host.BlenderHost     bpy (lazy imports)
        '-- hosts/sample_host.SampleHost       motion sample files, plain Python
        |
sample dictionary  ->  checks_base.MotionData  ->  checks (pure Python)
```

```python
from motion_eval import hosts

hosts.get_host()              # the active host: a running Maya, else Blender, else mayapy, else plain Python
hosts.get_host("blender")     # a specific host
with hosts.use_host("maya"):  # make one active inside a block
    ...
```

Rules every host follows (details in `hosts/host_base.py`):

- **Node paths** look like Maya long paths (`|group|Hips|Spine`); the last part is the
  joint name templates match, optionally with a `namespace:` prefix.
- **Matrices** are flat lists of 16 floats in Maya's row-major layout (translation at
  indices 12, 13, 14). Hosts with column-vector math (Blender) transpose them.
- **Units and up axis** are reported, never converted: `MotionData` turns Z up into Y up
  and checks scale every distance by the character's own size.

To add a host (for example another 3D program): subclass `SceneHost`, implement every
method marked "Required", register it in `hosts/__init__.py` (`create_host`,
`HOST_NAMES`), and run the parity test below on the sample files.

**Rule enforced by the tests:** only `hosts/maya_host.py`, `hosts/blender_host.py`, and
`usd_scene.py` may import `maya`, `bpy`, or `mathutils`.

## 9. Adding a check

A check is a pure function plus a `CheckDefinition`. It reads only `MotionData`, so it
works in Maya, Blender, and plain Python with no extra work.

1. **Write the function** in `checks_general.py` (any animated nodes) or
   `checks_biped.py` (needs skeleton roles; joint limits live in `checks_limits.py` and
   pose checks in `checks_pose.py`). It receives `data` (`MotionData`) and
   `parameters` (the check's own settings) and returns a `CheckResult`:

   ```python
   def check_hand_speed(data, parameters):
       """Flags frames where a hand moves faster than a limit.

       Args:
           data (MotionData): Sampled motion.
           parameters (dict): max_speed (leg lengths per second).

       Returns:
           CheckResult: Findings.
       """
       result = CheckResult()
       limit = parameters["max_speed"] * data.measure_leg_length()
       series = []
       for role in ("left_hand", "right_hand"):
           speeds = math_utils.speeds(data.get_role_positions(role), data.fps)
           series.append(speeds)
           for index, speed in enumerate(speeds):
               if speed > limit:
                   result.flag(index, data.get_label(data.get_role_path(role)))
       result.add_series("fastest hand", worst_per_frame(data.frame_count, series))
       result.set_chart("units per second", limit, "Limit")
       return result
   ```

2. **Register it** by adding a `CheckDefinition` to `GENERAL_CHECKS` or `BIPED_CHECKS`
   at the bottom of the same file. Presets, reports, graphs, summaries, and every window
   that lists checks pick it up from there:

   ```python
   CheckDefinition(
       key="hand_speed",                       # stable: stored in presets and reports, never rename
       label="Hand Speed",
       mode=MODE_BIPED,
       description="Hands moving faster than a plausible swing.",
       function=check_hand_speed,
       parameters=[ParameterSpec("max_speed", "Max Speed", 8.0, 0.1, 100.0,
                                 "Fastest hand speed, in leg lengths per second.")],
       required_roles=["left_hand", "right_hand"],   # skipped (not failed) when a skeleton lacks them
       enabled=False,                                # start off until calibrated on real data
       weight=1.0, warn_below=85, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
   ),
   ```

3. **Test it** with a synthetic sample (no Maya or Blender needed): build a clean motion
   and a broken one, and check the score drops only for the broken one (see the existing
   tests that call `evaluation.evaluate_sample`).

4. **Check parity**: evaluate the Maya samples and their Blender versions
   (`samples/01-03` and `04-06` in the standalone package) and compare the scores.

Keep checks host-agnostic:

- Use `data.get_positions`, `data.get_role_positions`, `data.get_matrices`, and the
  `math_utils` helpers. Positions are already Y up.
- Express distances as ratios of the character (`data.get_reference_length()`,
  `data.measure_leg_length()`) and speeds per second (`data.fps`), never in centimeters
  or frames, so files in any unit or frame rate score the same.
- Prefer positions and frame-to-frame changes over local joint axes: Maya and Blender
  (and FBX and USD exports) orient bones differently, so absolute local axes differ
  between programs while positions and changes do not.
- **Data that is not a world matrix** (mesh bounds, contact geometry, custom
  attributes): add `required_data=["my_key"]` to the definition, read it with
  `data.get_extra("my_key")`, and implement `get_extra_data` for `"my_key"` in each host
  that can provide it (return JSON-compatible data). Hosts that cannot provide it make
  the check skip with a clear reason instead of failing, so the other checks keep working.

## 10. Repairs (patching reported problems)

`repairs` applies small, targeted fixes to the frames a check flagged. A **patch manifest**
(JSON) lists the steps for each take; a step names a fix (or a custom script) and the frame
span to repair, usually a span from the report (`checks[].spans`, `checks[].offenders`).

```python
from motion_eval.repairs import apply, registry

print(registry.describe_fixes())          # every fix, its parameters, and the fixes per check
result = apply.apply_manifest("patches.json", ["walk_042_v003"], seed=4711)
print(result["status"])                   # none / skipped / applied / partial / failed
```

```json
{
  "schema": "motion_eval_patches", "version": 1,
  "template": "data/custom_skeleton.json",
  "on_error": "warn",
  "takes": {
    "walk_042_v003": {
      "seed": 4711, "frame_range": [0, 311],
      "steps": [
        {"fix": "foot_lock", "frames": [120, 141], "params": {"side": "left"}},
        {"fix": "span_bridge", "frames": [200, 202], "nodes": ["calf_l (left_leg)"]},
        {"script": "custom/walk_042_v003.py", "frames": [250, 260], "params": {}}
      ]
    }
  }
}
```

| Fix | For | What it does |
|---|---|---|
| `foot_lock` | foot_slide, planted_foot_jitter, contact_flicker | Pins planted feet over a contact span with two-bone IK (bone lengths kept, foot keeps its world rotation); `side: auto` picks the planted feet |
| `hips_follow` | foot_slide (body drift) | Moves the body along the ground so the planted foot stays put |
| `foot_floor_clamp` | ground_penetration, below_ground | Lifts only a sinking foot with two-bone IK |
| `ground_snap` | below_ground, floating, contact_flicker | Moves the hips up/down so the lowest foot/toe sits on the floor |
| `spike_clamp` | position/rotation pops | Caps the speed inside the span relative to the motion around it |
| `span_bridge` | pops, invalid values, wrists, twist, head | Replaces a short span with a smooth transition between the poses around it |
| `span_smooth` | jitter | Gaussian smoothing over the span with blend in/out (`adaptive` keeps accents) |
| `limit_clamp` | knee/elbow hyperextension and side bend | Rotates the hinge back inside its limit (hinge axis learned from the clip) |

**Presets and order.** Each fix has named presets (`"preset": "contact"` in a step; the step's own
`params` override them) and `registry.LADDERS` lists, per check, which fix/preset to try first and
what to try next (`registry.get_ladder`, `registry.next_rungs`). `registry.describe_fixes()` prints all of it.

**Preview.** `repairs.preview` loads a scene, scores it, applies a patch in memory, and scores it again
(nothing is saved), so candidates can be compared quickly:

```
mayapy -m motion_eval.repairs.preview --job job.json --source walk.usd --patch patch.json --out result.json
```

`job.json` uses the runner job keys (skeleton, preset, range_mode, general_scope, align_up_axis, ...).

- Paths in the manifest are relative to the manifest's folder. `template` is a Custom Skeleton
  file or a built-in key (`maya_humanik`); it lets steps use role keys (`left_foot`) as node names.
  Report offender labels such as `"foot_l (left_foot)"` work as node names too.
- **Fingerprint**: `seed` and `frame_range` are optional. When both the entry and the scene know a
  value and it differs, the patch is skipped: the take was regenerated and the patch no longer fits.
- `on_error`: `"warn"` logs a failed step and goes on; `"fail"` raises `apply.PatchError`.
- A custom script defines `run(context)`; `context` holds `scene` (`RepairScene`: `resolve_node`,
  `sample`, `key_world_matrices`, `host`), `frames`, `params`, `take`, `log`, and the modules
  `fixes`, `solvers`, `transform_math`, `registry`.
- Fixes only key the frames they change (inside one undo chunk in Maya). Writing keys needs a host
  with `supports_keying` (Maya); the math (`transform_math`, `solvers`) and `manifest` are pure.
- A patch changes the motion; it must not hide problems (no deleted frames, no frozen spans).

