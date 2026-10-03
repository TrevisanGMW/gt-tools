"""User-facing guidance shared by the Kimodo Generator widgets."""

ACTION_TOOLTIPS = {
    "test_bridge": "Probe only the configured bridge URL without starting or changing any process. Reports whether "
                   "it is ready, where it runs (WSL, Windows, or another server), its PID, deployed code path, "
                   "server job directory, device, encoder URL, and queued/active work. A legacy bridge reports "
                   "limited information until it is restarted once with current GT Tools code.",
    "test_encoder": "Probe the configured text-encoder URL independently of the bridge and model. Verifies the "
                    "expected Kimodo Gradio API without computing embeddings, starting a process, or using GPU "
                    "inference. A stopped encoder can still be launched on the next generation when Start missing "
                    "text encoder is enabled and the bridge owns a local environment.",
    "restart_bridge": "For Start in WSL or Start on Windows, gracefully stop an idle managed bridge, wait for its "
                      "port to close, deploy the current GT Tools bridge source, start it with the configured Kimodo "
                      "Python, and reconnect. The server refuses while work is active. Jobs, models, downloads, and "
                      "an independently managed/detached encoder are preserved. A legacy bridge needs one manual "
                      "stop first; its child encoder may need restarting.",
    "stop_bridge": "Gracefully stop the configured bridge only after confirmation. The server refuses while jobs "
                   "are queued/running. Persistent server jobs, Hugging Face model weights, local downloads, and "
                   "an independently managed/detached encoder are preserved. Start it again with Connect / Start. "
                   "An older bridge needs one manual stop first; its child encoder may also stop.",
    "create_maya_files": "Create one .ma per downloaded sample in a separate local Maya process. Includes the "
                         "animation and a locked HumanIK source definition using HumanIK tab overrides or Kimodo "
                         "defaults. Saves beside motion JSON files; never changes your open scene or overwrites "
                         "existing/edited scenes. Also retries failed exports and repairs missing exported scenes.",
    "import_maya_file": "Import the selected job's generated .ma file into the current Maya scene. This does not "
                        "clear the scene; use the automatic processing options to force-clear before an automatic "
                        "import. For multi-sample jobs, the selected sample is imported when available.",
    "print_server_location": "Query the selected job's bridge and print its actual server-side directory to Maya's "
                             "Script Editor and the status field. WSL returns a Linux path; native Windows returns "
                             "a Windows path. This is not the local download folder. Requires an updated bridge.",
    "clear_finished": "Clear succeeded, failed and cancelled jobs. A confirmation lets you delete server/WSL "
                      "job files (default on) and optionally verified local artifacts. Imported animation, model "
                      "weights, edited files and added Maya scenes are preserved. Failures retain history for retry.",
    "clear_history": "Clear all tracked jobs after confirmation. Active jobs are cancelled first; their history "
                     "stays until they stop and cleanup succeeds. Choose server/WSL deletion and optional local "
                     "artifact deletion. Uncheck both for history-only removal. File deletion is permanent.",
    "delete_server_files": "Permanently delete server-side job records and folders for completed jobs associated "
                           "with the bridge URL currently shown in Connection. Maya asks for confirmation first. "
                           "Active jobs are not "
                           "deleted, local downloads and Maya scenes are untouched, and the job-history rows remain "
                           "available for reference. This only affects this bridge's managed job directory.",
    "hik_export_pose": "Export the selected Kimodo source's CURRENT pose as a complete .pose JSON and set it as "
                       "the T-pose override. First pose the skeleton in a valid T-pose. Clears Reference Frame. "
                       "This exports the current pose, not automatically the default Kimodo T-pose.",
    "hik_export_source": "Export the HumanIK definition attached to the selected Kimodo import, then set the XML "
                         "override to this file. Add a definition first. Existing output files require confirmation.",
    "hik_apply_pose": "Test the source pose in the current scene. Blank pose/frame fields automatically use the "
                      "default Kimodo T-pose; otherwise use your pose file or reference frame. Requires confirmation: "
                      "animated channels get new/replaced keys at the current frame. Maya Undo reverts this test.",
    "hik_import_source": "Create the source HumanIK definition using the default Kimodo definition and T-pose "
                         "when overrides are blank. Equivalent to Add HumanIK Definition in Results. Existing "
                         "definitions are never overwritten; animation is preserved.",
    "load_setup": "Load a saved Kimodo setup or generation definition JSON. Replaces the editable prompts and "
                  "constraints; it does not open a Maya scene or submit a job. Save your current setup first "
        "if needed.",
    "load_default_setup": "Reset generation prompts, sampling and import options, HumanIK overrides, and constraints "
                          "to their defaults while preserving the current bridge URL, launch mode, Kimodo Python, "
                          "WSL distribution, token, and job history. No Maya scene or server files are changed.",
    "save_setup": "Save prompts, sampling settings, and named pose/path constraints to JSON for reuse. "
                  "This does not save the Maya scene, connection credentials, or generated animations.",
    "connect": "Check the bridge and load its model list and SOMA pose skeleton. If no server is reachable, Start "
               "in WSL or Start on Windows deploys the current lightweight bridge source and launches it with your "
               "chosen Kimodo Python. Connect to existing bridge never starts a process. Nothing is installed.",
    "refresh_models": "Ask the currently configured bridge for its available model IDs and cached "
        "configuration status. "
                      "Connect first. Refresh after a model download to update the list.",
    "reset": "Reset connection, generation, and import settings to defaults, including the package-cache "
        "download folder. "
             "Generated files and existing job history are retained; nothing is deleted.",
    "browse_python": "Select the folder containing your installed Kimodo Python environment. Windows environments may "
                     "contain python.exe or Scripts/python.exe. In WSL mode, browse the selected distribution under "
                     "\\\\wsl.localhost and select its environment or bin folder; the path is converted to "
        "Linux format.",
    "query_wsl": "Run wsl.exe --list --quiet on Windows and populate the distribution dropdown. This does not start "
                 "a Linux process or install WSL. Choose a returned name, or type a name manually.",
    "download_model": "Download the selected model into the bridge machine's Hugging Face cache, after confirmation. "
                      "Files can be several GB. Model authorization and network access must already work on "
        "that machine. "
                      "Track this download in Results; this is separate from downloading generated clips to Maya.",
    "add_prompt": "Append another text-and-duration segment. Segments run in table order; describe the next "
        "action here.",
    "randomize_seed": "Choose a new unsigned 32-bit seed from 0 to 4294967295. The value is placed in the Seed "
                      "field and used by the next generation request; keep it to reproduce a request on the same "
                      "model and runtime.",
    "remove_prompt": "Remove the selected prompt row. At least one row is retained. This does not modify "
        "submitted jobs.",
    "prompt_up": "Move the selected segment earlier in the sequence, preserving its text and duration.",
    "prompt_down": "Move the selected segment later in the sequence, preserving its text and duration.",
    "validate": "Check current prompts, sampling settings, enabled constraints, and SOMA clip-frame bounds before "
                "submission. Validation does not run the model or modify the Maya scene.",
    "generate": "Submit the enabled constraints and current prompt sequence as a new job. Connect first. Maya stays "
                "available while inference runs. In Results, wait for success, download the clips, then "
        "import a sample.",
    "summary_generate": "Submit the project summarized on this tab using the same validation and background job "
                        "flow as Generate Motion on the Generate tab. The tool switches to Results after submission.",
    "create_skeleton": "After connecting, create a grounded, unkeyed SOMA77 skeleton in a new namespace. "
                       "The checked Auto HumanIK option also characterizes it using the HumanIK tab overrides "
                       "or Kimodo defaults. Pose manually or feed animation through Maya HumanIK, then capture "
                       "each desired clip frame. The placement group defines generation space.",
    "use_selection": "Select a Kimodo placement group or one of its joints, then use it as the pose/path source. "
                     "Arbitrary production rigs require a compatible skeleton conversion before pose capture.",
    "capture_pose": "Store the source skeleton's currently evaluated Maya pose at the chosen destination clip frame. "
                    "Repeat with different poses and times to guide a motion. Rotate joints; keep their "
        "offsets and scale. "
                    "Root translation is allowed. The destination frame does not change Maya's current time.",
    "preview_pose": "Select a stored body/hand/foot constraint and create a separate preview skeleton from "
        "its saved pose. "
                    "Connect first to load the reference skeleton. Previewing does not replace the authoring "
        "skeleton. Its Outliner name includes the constraint name and first clip frame.",
    "preview_all_constraints": "Create one Maya preview for every constraint row: pose rows create tagged skeletons, "
                               "and root paths create tagged curves. Disabled rows are included so you can inspect "
                               "them too. Pose preview names include the constraint name and first clip frame. "
                               "Connect first if any pose rows are present.",
    "remove_pose_previews": "Delete all pose skeleton and root-path curve previews created by this tool. Each "
                            "preview has a private Maya attribute for safe identification, so the authoring skeleton, "
                            "imported animation, and other scene objects are left untouched. The action is undoable.",
    "remove_all_constraints": "After confirmation, remove every pose and root-path row from the current setup. "
                              "The setup is saved immediately. This does not delete preview objects already in the "
                              "Maya scene; use Remove All Previews for those.",
    "duplicate_constraint": "Copy the selected constraint with a fresh identity. Its first key moves to the "
        "Clip frame "
                            "field; spacing between remaining keys is preserved. Retiming can avoid "
        "duplicate-key warnings.",
    "remove_constraint": "Remove the selected constraint row from this setup. This does not delete Maya "
        "objects or JSON files.",
    "capture_path": "Capture selected Maya transforms as a root trajectory: select one locator/transform per listed "
                    "frame in order, or select one NURBS curve transform. Curves are sampled at equal arc-length "
                    "intervals. When Root path frames is blank, Curve samples controls how many points are distributed "
                    "across the clip; explicit frames determine the sample count instead. Positions become ground-plane "
                    "root constraints in the pose source's placement space, or Maya world space if no source is assigned.",
    "import_constraints": "Append native Kimodo/demo constraint JSON, or the constraints from a generation "
        "definition. "
                          "Multi-key entries become separately editable rows. Source files are never changed.",
    "export_constraints": "Save enabled pose/path rows as native Kimodo constraint JSON. UI frame 1 is stored "
        "as index 0. "
                          "Use Save Setup if you also want names, prompt segments, and generation settings.",
    "refresh_job": "Select a job and query its original bridge for current status. Use this after reconnecting or an "
                   "uncertain submission. The original bridge must still be reachable.",
    "cancel_job": "Request cancellation of the selected job. Waiting work is skipped; active work stops at the next "
                  "supported boundary. Model loading or a download may finish its current call. The server "
        "stays running.",
    "download_results": "After a generation job succeeds, copy all its samples and metadata from the bridge into the "
                        "Download folder below a unique job ID. Files are verified; existing files are never "
        "overwritten. "
                        "Missing artifacts are repaired in their original folder. Edited/corrupt files are not "
                        "overwritten. Then select a sample and click Import Sample.",
    "import_sample": "Import the chosen downloaded motion into a new Maya namespace at the configured start frame. "
                     "Existing namespaces receive a numeric suffix. Scene units and frame rate are preserved; "
                     "source timing may use fractional keys. This creates a skeleton, not animation on an "
        "existing rig.",
    "browse_output": "Choose where generated clips are downloaded on this computer. The selection is saved "
        "immediately "
                     "in GT preferences and reused next time. Changing it does not move or delete previous downloads.",
    "use_cache": "Reset the download destination to PackageCache/kimodo/downloads and save that choice immediately. "
                 "This changes the target folder only; it does not clear the cache or remove previous results.",
    "open_folder": "Open the selected job's local folder after its results have been downloaded. If no job is "
                   "selected, open the configured Download Folder and show a warning so you know the fallback was used. "
                   "A missing Download Folder is created before opening.",
    "create_humanik": "Select one Kimodo group or joint; with no selection, use the current pose source "
                      "or latest import. "
                      "Create a native HumanIK character using the SOMA77 mapping and rest T-pose, then restore "
                      "existing animation. Optional overrides are in HumanIK. No server connection is needed. "
                      "Already characterized skeletons are left unchanged; manage them in Maya HumanIK.",
    "browse_hik_xml": "Choose an optional HumanIK Match List XML with key/value joint assignments, as used by the "
                      "batch processor. Names resolve only inside the chosen hierarchy. "
                      "Leave blank to automatically use the default Kimodo definition.",
    "browse_hik_pose": "Choose an optional core.pose/batch-processor .pose JSON containing local transform channels "
                       "for the full skeleton. Leave blank for the automatic default Kimodo T-pose "
                       "unless a reference frame is supplied.",
}

TABLE_ACTION_TOOLTIPS = {
    "preview_root_path": "Select a root-path constraint and create a Maya curve showing its stored path in the "
                         "generation plane. When a pose source is assigned, the preview is parented beneath its "
                         "placement group so the curve appears in the same space used during capture. The saved "
                         "constraint and source animation are not changed.",
}

CONTROL_TOOLTIPS = {
    "auto_maya_file": "Enabled by default and saved in preferences. After a job is downloaded, create one .ma per "
                      "sample beside its JSON file, with animation at its native FPS starting at frame 1 and a "
                      "locked HumanIK definition. Uses HumanIK overrides or the built-in Kimodo defaults. A separate "
                      "local mayapy process keeps the open scene untouched. If auto-download is off, download "
                      "manually first. Runs while this tool is open; failed exports require manual retry. Cleanup "
                      "preserves these Maya scenes and their verification receipts. No retargeting is performed.",
    "auto_download": "Enabled by default and saved in preferences. Completed generation jobs download to the "
                     "configured folder while this window is open. Status becomes Downloaded after verification. "
                     "Missing files are flagged; use Download Results to repair them. Failed automatic downloads "
                     "require a manual retry, and model-download jobs are excluded. Saved in preferences.",
    "auto_import_maya": "Enabled by default and saved in preferences. After Auto-create Maya + HumanIK finishes, "
                        "import the generated .ma file(s) into the current scene. Import all samples controls whether "
                        "a multi-sample job imports every alternative or only the selected/first sample. Optional "
                        "timing adjustments match Maya's scene frame-rate and playback range. Force-clear runs once "
                        "before automatic import when enabled.",
    "auto_import_all_samples": "Checked by default and saved in preferences. With Auto-import Maya file enabled, "
                               "import every generated sample from the job into the same Maya scene, each under a "
                               "distinct namespace. Force-clear runs once before the group of imports. Uncheck to "
                               "import only the selected sample, or the first sample when none is selected.",
    "auto_clear_scene": "Off by default and saved in preferences. Applies only to automatic Maya imports. When "
                        "enabled, the tool force-creates a new scene immediately before importing the generated .ma, "
                        "without prompting to save. This discards unsaved scene contents; enable only when that is "
                        "the intended workflow. It is disabled when Auto-import Maya file is off.",
    "auto_frame_rate": "Enabled by default and saved in preferences. On automatic Maya-file import, set the open "
                       "Maya scene's time unit to the generated motion's FPS. Existing keyframe numbers are kept "
                       "unchanged, so this changes their real-time interpretation; enable only when the scene should "
                       "use the generated clip's rate. Disabled unless Auto-import Maya file is checked.",
    "auto_frame_range": "Enabled by default and saved in preferences. On automatic Maya-file import, set Maya's "
                        "playback and animation range to frames 1 through the generated motion's frame count. Other "
                        "scene content is not deleted unless Force-clear scene before import is also enabled. "
                        "Disabled unless Auto-import Maya file is checked.",
    "auto_humanik": "Enabled by default: Create Pose Skeleton also adds a Kimodo HumanIK definition, using any "
                    "overrides in the HumanIK tab. You can then use Maya HumanIK to feed other animations to this "
                    "skeleton and capture desired poses. Disable for a plain editable skeleton. This local option "
                    "is saved with your definition and preferences; it does not change server generation.",
    "limit_body_joint_translations": "Enabled by default. On Create Pose Skeleton, set Maya translation limits on "
                                     "each non-root body joint to its current rest offset; the root remains free for "
                                     "motion. This prevents moving a bone or HumanIK from changing its offset and "
                                     "triggering the pose-capture warning. Rotate joints to pose them. Saved with the "
                                     "generation definition and available as a Python definition option. This only "
                                     "affects skeletons created with this tool; Use Selected Skeleton is not changed.",
    "template_pose_previews": "Enabled by default. Preview Pose creates the preview skeleton as a Maya template, "
                              "so it displays distinctly and cannot be selected or mistaken for the animated "
                              "authoring skeleton. Disable this if you need to select or edit preview joints. "
                              "Every preview is tracked either way, so Remove All Previews only deletes previews "
                              "created by this tool. Saved in preferences.",
    "hik_name": "Leave blank to automatically name the default Kimodo definition kimodo. If a node or namespace "
                "already uses that name, use kimodo1, kimodo2, etc. A supplied name overrides the default; "
                "existing nodes are never replaced.",
    "hik_xml": "Leave blank to automatically use the default Kimodo definition (SOMA77 mapping); no XML is required. "
               "Optionally supply native HumanIK Match List XML instead. Namespaces "
               "in the file are ignored and joints are resolved within the selected skeleton only.",
    "hik_pose": "Leave blank to automatically use the default Kimodo T-pose unless Reference Frame is provided. "
                "Optionally supply complete .pose JSON from core.pose or the batch processor. Uses local translation "
                "and rotation channels in current Maya scene units. Definition creation restores animation "
                "without editing keys; Apply Pose To Source deliberately changes this frame. "
                "Use this OR a reference frame, not both.",
    "hik_frame": "Optional Maya timeline frame at which the skeleton is already in a valid HumanIK T-pose. "
                 "Blank with no pose file automatically uses the default Kimodo T-pose. Time is restored "
                 "after definition creation. This is a Maya frame, not a generation clip-frame index.",
    "hik_lock": "Lock the completed definition so it can be used as a HumanIK source. Disable to inspect/edit "
                "the mapping manually in Maya HumanIK. No retargeting or control rig is created. "
                "This checkbox applies to interactive actions; exported Maya files always use locked definitions.",
    "mode": "Existing bridge connects by HTTP without starting processes. Start in WSL uses a selected Linux "
            "distribution and Python environment. Start on Windows uses a native Kimodo Python environment.",
    "url": "Full Kimodo bridge URL, for example http://127.0.0.1:7861. Use another host/port for a remote/customized "
           "server. Port 7860 is the browser demo and does not provide this generation API.",
    "python_path": "Absolute environment folder or Python executable where Kimodo already works, not Maya's "
                   "Python. Examples: C:/Environments/kimodo, /home/user/kimodo_env, or either environment's "
                   "Python executable. Environment folders are resolved to Scripts/python.exe or bin/python "
                   "when connecting and the resolved value is saved. WSL paths must not start with ~.",
    "distribution": "Exact installed WSL distribution name, such as Ubuntu-26.04. Click Query WSL and choose a name "
                    "or enter one manually. The Python environment must live in this distribution.",
    "encoder_url": "URL of Kimodo's separate text-embedding service, normally http://127.0.0.1:9550. "
                   "Used when starting a local bridge; changing this does not reconfigure an already-running bridge.",
    "token": "Optional bearer token configured on the bridge. Required for a bridge exposed beyond localhost. "
             "Kept in memory only, scoped to its server, and never saved to preferences or setup JSON.",
    "device": "Inference device used when starting a local bridge: auto prefers CUDA when available; cuda requires "
              "a compatible GPU; cpu uses system memory and is slower. This does not change the text encoder's device "
              "or reconfigure a bridge that is already running.",
    "start_encoder": "Allow the local bridge to start a missing local text encoder on the first generation job. "
                     "An existing encoder is reused. Disable this if you manage the encoder yourself.",
    "show_console": "Enabled by default and saved in preferences. When Maya launches a WSL or native Windows "
                    "bridge, open a separate console window that shows server output and remains visible while "
                    "the bridge runs. Closing that window stops the bridge. Disable this for a hidden background "
                    "process; startup output is then written to the log path shown in Bridge status. This setting "
                    "does not affect an already-running bridge or Connect to existing bridge.",
    "auto_connect": "When enabled, the tool runs the same action as Connect / Start after it opens. Existing mode "
                    "tests the configured URL; WSL and Windows modes start the selected local bridge if needed. "
                    "Connection failures are reported in the tool status and can be retried manually. This setting "
                    "is saved in preferences and defaults off.",
    "model": "Motion model advertised by the connected Kimodo installation. Select a model compatible with your pose "
             "constraints; the authoring skeleton is SOMA77. A cached configuration does not guarantee all weights "
             "are present. Missing weights may download on first use.",
    "prompts": "Double-click cells to edit durations and motion descriptions. Rows execute in order; punctuation does "
               "not split a row. Up to 16 segments, 30 seconds each, 120 seconds total. Each segment must be longer "
               "than the advanced transition overlap at the model's sample rate. Right-click for add, duplicate, "
               "copy, paste, reorder, and remove actions. Enable Enter durations in frames to type integer model "
               "frames; the selected model's FPS converts them to seconds for the API. Stored setup values remain "
               "seconds.",
    "prompt_frames": "When checked, the first prompt column accepts whole frame counts and displays Frames. Values "
                     "are converted to seconds using the selected model's advertised FPS (30 FPS if unavailable) "
                     "before validation and submission. Switching models preserves the prompt durations in seconds "
                     "and updates their displayed frame counts. When unchecked, values are seconds as before. This "
                     "choice is saved in preferences; setup/API definitions continue to store seconds.",
    "seed": "Unsigned integer seed from 0 to 4294967295. Leave blank to choose a random seed, recorded in Results. "
            "A fixed seed helps repeat a request; different hardware/model versions can still produce differences.",
    "samples": "Number of alternative clips generated by one request, from 1 to 8. Higher values use more memory. "
               "Download the completed job, then choose a sample for manual import; Automatic Processing can import "
               "every sample into the same scene.",
    "steps": "Number of diffusion/denoising steps, from 1 to 1000. More steps take longer and may improve refinement. "
             "The default 100 follows the current integration's sampling settings.",
    "postprocess": "Apply Kimodo's foot cleanup and constraint post-processing after generation. Disable to inspect "
                   "the model's unprocessed motion. This happens on the bridge, before Maya import.",
    "advanced": "Expand optional generation controls, including foot cleanup, text and constraint guidance, "
                "transition overlap, and initial heading. Collapsing this area keeps its current values.",
    "text_guidance": "Text guidance weight, from 0 to 20; default 2. Larger values push generation toward the prompt "
                     "but can affect motion quality. This is the first separated-guidance weight.",
    "constraint_guidance": "Constraint guidance weight, from 0 to 20; default 2. Controls the strength of pose/path "
                           "conditioning. It is not an exact rotation-lock guarantee.",
    "transition": "Number of model frames used to blend neighboring prompt segments. Default 5. Each segment "
                  "must contain more frames than this overlap. Not measured in the Maya timeline's frame rate.",
    "heading": "Initial facing direction in degrees relative to generation space. Zero uses the model's default "
               "heading. This value is converted to radians for Kimodo; scene placement remains separate.",
    "output": "Local or network directory receiving downloaded clips, not the WSL model cache. Saved immediately "
              "when you choose a folder or finish editing this field. Each job gets its own subfolder. "
              "New installations default to PackageCache/kimodo/downloads; existing saved choices are retained.",
    "namespace": "Prefix for imported Maya skeletons, for example kimodo_walk. Existing names receive a numeric "
                 "suffix. Use letters, digits, and underscores, starting with a letter or underscore.",
    "start_frame": "Maya timeline frame at which an imported clip begins. This does not retime generation or its "
                   "constraints. Motion duration is preserved in seconds even when Maya's frame rate differs.",
    "pose_source": "Current Kimodo placement group used for pose and path capture. Select another Kimodo skeleton "
                   "and click Use Selected Skeleton to change it. The group defines local generation space.",
    "pose_kind": "Choose full-body, left/right hand, or left/right foot conditioning. All modes capture a compatible "
                 "skeleton pose; Kimodo uses the relevant joint positions. These are not arbitrary "
        "rig-control targets.",
    "pose_frame": "Destination frame within the generated clip, starting at 1. Capture stores the skeleton's "
                  "currently evaluated Maya pose at this clip frame; it does not change Maya's current time. "
                  "Right-click this number and choose Set Clip Frame to Current Maya Frame to query Maya's timeline "
                  "time and copy its nearest whole frame here. For a four-second 30 FPS SOMA clip, frames run from "
                  "1 to 120. Duplicate uses this field to place the copied constraint's first key.",
    "constraints": "Use toggles whether a row is sent to Kimodo. Double-click Clip frame(s) or Name to edit. "
                   "Frames are one-based here and zero-based in JSON. Right-click to preview, enable, change the "
                   "pose type, duplicate, copy, paste, remove, or exchange constraint JSON. Root paths cannot "
                   "change pose type. Duplicate channel/frame constraints are "
                   "rejected.",
    "path_frames": "Optional comma-separated destination clip frames, for example 1, 30, 60, 90. Select one "
                   "transform for each frame. Leave empty with two or more selected transforms to spread the path "
                   "keys from the first through the last generated frame. With one selected NURBS curve, the Curve "
                   "samples control chooses how many evenly spaced points are captured when this field is blank. "
                   "Entering frames disables that control and samples one point per frame. Frames must fit the prompt "
                   "duration; Generate checks this before submitting. Frame spacing controls path timing; root paths "
                   "constrain the ground plane, not height.",
    "path_heading": "Facing direction captured with the root path: None, Direction of travel (curve tangent or "
                    "movement, held while stopped), Node +Z axis (each transform's world +Z, or an animated "
                    "transform's keyed rotation), or Fixed (offset only). Without a heading Kimodo chooses the "
                    "facing itself, which often produces strafing on long paths.",
    "path_heading_offset": "Degrees added to the captured heading, or the absolute heading when Root heading is "
                           "Fixed. 0 faces +Z; 180 travels backward; 90 or -90 strafes.",
    "path_curve_samples": "Number of equally spaced points to capture from a selected NURBS curve, or samples of "
                          "one selected animated transform from the playback start, when Root path "
                          "frames is blank. These samples are spread across the generated clip. Two or more selected "
                          "transforms ignore this value. Enter explicit Root path frames to determine the count from "
                          "that list; this control will disable. The default is four samples and the setting is saved "
                          "in preferences.",
    "jobs": "One row per server request, not per imported Maya skeleton. Right-click for refresh, download, "
            "Maya-file, import, copy-ID/location, cancel, Clear Finished, Clear All History, and scoped cleanup "
            "actions. "
            "Ready to download means "
            "generation "
            "finished on the server; Downloaded means tracked local files exist. Missing files need repair. "
            "Clear Finished/All can remove tracked server copies and optionally local artifacts. "
            "Closing the window does not stop jobs; automatic downloading resumes when it is reopened.",
    "progress": "Reported generation progress when the backend provides it. Model loading, multi-prompt generation, "
                "and downloads may only report a stage; lack of percentage changes alone is not a failure.",
    "result_info": "Details for the selected job, including its bridge URL, full job ID, stage/error, and resolved "
                   "model/seed. Select this text to copy it when diagnosing a failed or interrupted job.",
    "sample": "Alternative clip inside the selected successful job. This selector stays hidden for the normal "
              "single-sample result and appears only when Generate requested multiple samples. Download Results "
              "first, then choose motion.json, sample_1.json, sample_2.json, and so on.",
    "connection_info": "Connection readiness and startup-log location. Local startup uses your existing installation. "
                       "Inspect the log if the bridge cannot start or fails to import Kimodo.",
    "status": "Feedback for the last action. Warnings explain missing selections, unfinished steps, or invalid "
              "settings; they do not mean the tool crashed. Unexpected failures are also recorded in the Python log.",
    "project_summary": "Read-only overview of the current connection, prompt duration, model, sampling, enabled "
                       "constraints, output automation, HumanIK mode, and job history. It refreshes when this tab "
                       "is opened and as job history changes.",
}

TAB_TOOLTIPS = (
    "Configure and connect to the Kimodo bridge. Local modes can launch it from an existing Kimodo installation.",
    "Choose a model, describe sequential actions, adjust sampling, and submit a generation request.",
    "Author and time multiple poses or root paths, preview stored poses, and exchange constraint JSON.",
    "Blank overrides automatically use the default Kimodo definition and T-pose. "
    "Source-only Actions and Testing use the batch processor formats; no target or server is required.",
    "Review the current project configuration and job history, then submit the summarized request.",
    "Monitor categorized automatic processing and jobs. Common selected-result actions stay fixed at the bottom; "
    "manual recovery, history, and diagnostics remain collapsed until needed.",
)
