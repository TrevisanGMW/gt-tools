# motion_eval

Scores animation quality from 0 to 100 with configurable checks, and writes the
same summaries, JSON reports, and graphs as the Batch Processor
**Validate Animation** task. Everything below uses only this package plus Maya,
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
| `report_graphs` | Qt | PNG graphs (uses the host's Qt; falls back to PySide6, then PySide2) |
| `sampling`, `scene_io` | Maya | Reads the open scene, writes the score attribute |
| `runner` | Maya | Headless jobs: open files, evaluate, write every output |

The package only uses relative imports, so the `motion_eval` folder can be copied
anywhere on `sys.path` and imported as `motion_eval`. Inside this toolkit, import
it from its full package path instead; the examples below use
`from motion_eval import ...`.

## 1. Quick start: evaluate many files with every output

```python
from motion_eval import runner

job = runner.create_job(
    title="Locomotion Review",
    skeleton="maya_humanik",            # "none" = General checks only
    output_dir="D:/reviews/locomotion",
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

with runner.maya_session():             # starts maya.standalone if not inside Maya
    run = runner.run_job(["D:/anims/walk_01.ma", "D:/anims/run_01.ma"], job)

print(run["totals"]["statuses"])        # {"failed": 1, "warning": 0, "passed": 1, "skipped": 0}
print(run["failed_files"])              # failed or errored files
for result in run["results"]:
    print(result["source"], result["status"], result["score"], result["error"])
```

`run_job` raises `ValueError` when the job is invalid (`runner.validate_job(job)`
lists the problems without running anything). Errors in a single file do not stop
the run: that file gets `status == "error"` and an `error` message.

### Output layout

```text
<output_dir>/
    batch_summary.txt            totals, checks with the most issues, files sorted by score
    batch_report.json            totals + each file's per-check results, sorted by score
    batch_scores.png             one row per file, one colored cell per check
    walk_01/                     (directly in <output_dir> when file_folders is False)
        walk_01_summary.txt
        walk_01_report.json      full report (same as Export Report in the tool)
        walk_01_00_summary.png
        walk_01_01_jitter.png ...
```

Pass `source_root="D:/anims"` to `run_job` to keep input sub-folders under
`<output_dir>` when `file_folders` is on.

## 2. Job settings

`runner.create_job(**overrides)` returns a plain dictionary. `outputs` and `score`
are merged with their defaults, so pass only what changes.

| Key | Default | Meaning |
|---|---|---|
| `title` | `"Validate Animation"` | Title of batch summaries and graphs |
| `skeleton` | `"none"` | `"none"`, a built-in key, a Custom Skeleton JSON path, or a template dictionary. Any skeleton adds the Biped checks |
| `preset` | `None` | Preset dictionary, preset JSON path, or `None` for the defaults |
| `range_mode` | `"Playback Range"` | `"Playback Range"`, `"Animation Range"`, `"Keyed Range"`, `"Custom"` |
| `custom_start`, `custom_end` | `1`, `100` | Frames for `"Custom"` |
| `general_scope` | `"All Joints"` | Nodes evaluated without a skeleton: `"All Joints"`, `"Animated Transforms"`, `"Node List"` |
| `node_list` | `[]` | Names or wildcards for `"Node List"`, for example `["prop_ctrl", "*:root"]` |
| `load_mode` | `"open"` | `"open"` the file, or `"import"` into a new scene (FBX is always imported) |
| `output_dir` | `""` | Output folder; required when any output is on |
| `outputs` | see above | Which files to write (`outputs.DEFAULT_OUTPUT_OPTIONS`) |
| `write_score` | `False` | Store the score as a Maya attribute (see `score`) |
| `score` | network node `motionEval.motionScore` | `target_mode`, `node_name`, `score_attribute`, `report_attribute`, `write_report`, `write_policy` (see `scene_io.write_score`) |
| `save_copy_dir` | `""` | Save each evaluated scene (with its score) as a `.ma` copy here. Inputs are never overwritten |

The skeleton decides the mode, exactly like the Batch Processor task: with
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
Files saved from the Animation Evaluator's Skeleton tab use the same format.

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

Preset files saved from the Animation Evaluator's Checks tab, or from the Batch
Processor task, can be passed as `job["preset"]` directly.

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
mayapy -m motion_eval.runner job.json D:/anims/walk_01.ma D:/anims/run_01.ma --result D:/out/result.json
```

- `--source-root D:/anims` keeps input sub-folders under the output folder.
- `--result` writes totals, batch output paths, failed files, errors, and one compact
  result per file (with its batch `entry`) as JSON.
- Exit code: `0` every file passed or warned, `1` some file failed or errored,
  `2` invalid job.

`maya.standalone` is initialized and uninitialized automatically. Run from the
folder that contains `motion_eval` (or add it to `PYTHONPATH`).

## 7. Batch Processor task settings and their job keys

| Validate Animation task | Job key |
|---|---|
| Skeleton (None / built-in / Custom Skeleton + Custom SKM File) | `skeleton` (`"none"`, key, or JSON path) |
| Checks and Thresholds (inline or Preset File) | `preset` (dictionary or JSON path) |
| Frame Range, Start, End | `range_mode`, `custom_start`, `custom_end` |
| Nodes, Node List | `general_scope`, `node_list` |
| Scene Load (Open / Import) | `load_mode` |
| Output Folder | `output_dir` |
| Output > Summary / JSON Report / Graphs, Per-File Folders, Only On Failure | `outputs` |
| Score Attribute > Write Score, Target, Attributes, Policy | `write_score`, `score` |
| Score Attribute > Save Scene | `save_copy_dir` (saves a copy; inputs are never overwritten) |

Not included in the runner: the task's post-script, tracker reporting, and the
validation log. Use the returned results for those.
