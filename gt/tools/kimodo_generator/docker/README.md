# Kimodo Docker deployment

Maya talks to the GT Kimodo bridge over authenticated HTTP. Docker contains Kimodo,
Torch, and a separate text encoder; Maya needs only GT Tools. Existing WSL and
native Python launch modes remain supported.

## Local setup

Requirements: a local Linux Docker engine, Compose v2.30 or newer, NVIDIA GPU
container support, Git, and an authorized Hugging Face credential. On Windows,
Docker Desktop GPU support uses its WSL2 backend. The default CUDA 12.8 / PyTorch
2.7.1 image supports Blackwell GPUs. First build requires several GB of downloads
and additional disk space for image layers and model weights.

1. Choose **Start in Docker** on Kimodo Generator's Connection tab.
2. Select a dedicated deployment folder under your Docker data root.
   **Open** opens that folder for inspection, creating it first if missing.
   **Force stable revisions** sits next to this folder setting. Set **Image name**
   to the repository name to generate; it defaults to `kimodo-bridge`.
3. Click **Prepare Deployment**. This creates the structure below. If available,
   an existing `HF_TOKEN`, `HF_TOKEN_PATH`, or Hugging Face cache credential is
   copied into `secrets/hf_token`. Otherwise put an authorized credential there.
   Credentials are mounted as files at runtime and excluded from the build context.
4. Leave **Force stable revisions** unchecked to try the latest Kimodo and Viser
   commits, or check it to build the known stable pair directly. Click
   **Build Image**. Read `logs/build.log` for build progress and any stable fallback.
5. Set the bridge URL to match `BRIDGE_PORT` in `configuration/.env`, then click
   **Connect / Start**. The bridge becomes available before the encoder finishes
   loading. **Test Text Encoder** checks encoder readiness from inside the bridge.
6. Generate normally. Maya downloads checksum-verified JSON/NPZ artifacts and
   creates/imports Maya scenes locally.

The deployment folder starts empty. Choose it explicitly by browsing or typing an
absolute path; that choice is saved immediately and restored next time. Selecting
a folder does not prepare, build, or start anything. A previously prepared folder
can be selected again to reuse its deployment. Changing the field does not move
or delete the previous deployment. An explicit executable field is available when
Docker CLI auto-discovery does not find your installation.

Leave **Docker executable** empty to look it up automatically when running Docker
actions, or click **Find Docker** to fill and save the detected path immediately.

The built image appears under **Images** in Docker Desktop. Its tag is the
`KIMODO_IMAGE` value in `configuration/.env`. New deployments prefer
`kimodo-bridge:1.12.0`; a conflict adds a suffix such as `kimodo-bridge-2:1.12.0`.
Image names use lowercase letters, numbers, dots, underscores, or hyphens without
an explicit tag. Changing the image name applies to the next Prepare/Build; it
does not rename an existing Compose project or its currently running containers.
Docker stores its layers in its Linux engine disk (Docker reports `/var/lib/docker`
internally); they are not an image file in the deployment folder. Docker Desktop
manages the host disk location separately from the persistent bind-mounted data.

Building the image installs software; it does not pre-download the model weights.
On first startup, the encoder downloads a large language model into
`models/huggingface/`, then loads it before listening on port 9550. During that
time the bridge can already be healthy while encoder diagnostics report
**Starting**. Wait for startup to finish and test again; **View Docker Logs**
opens a live log window for the encoder container. The tool also displays
measured download bytes/percent for known transfers, then an activity bar while
weights load. Encoder logs emit periodic download/loading summaries even without
a terminal. If the container is stopped or remains unavailable, inspect those
logs for the actual failure. Deleting the model cache requires downloading the
weights again; rebuilding the image alone does not restore that cache.

```text
docker-data-root/
└── kimodo/
    ├── deployment.json              # Stable Compose project identity and revisions
    ├── configuration/
    │   ├── .env                     # User settings; preparation never overwrites it
    │   ├── .env.example
    │   ├── compose.yaml
    │   └── Dockerfile
    ├── secrets/
    │   ├── bridge_token             # Random per-deployment access token
    │   └── hf_token                 # Hugging Face credential
    ├── source/
    │   ├── kimodo/                  # Pinned upstream source and Viser checkout
    │   ├── kimodo-bridge/           # Minimal bridge bundle, preserving gt Python imports
    │   ├── container_runtime.py
    │   ├── container_progress.py
    │   └── Dockerfile               # Build-context copy
    ├── models/huggingface/           # Persistent download cache
    ├── jobs/                        # Bridge definitions, status, and artifacts
    └── logs/                        # Build logs, service logs, container log exports
```

New deployments check Docker project/image names and adjacent prepared folders
before selecting a name. Existing deployments retain their names and image tags.
The tool also checks the existing containers' owning folder before changing a
project, so a conflicting project is left alone. No fixed container names or global
Docker cleanup commands are used.
Use separate folders and published ports for additional deployments. Image layers,
the engine disk, and Docker's bounded stdout/stderr logs live in Docker's own
storage; changing this tool's folder does not relocate Docker Desktop's engine.

## Configuration and lifecycle

The bottom-right indicator uses the Batch Processor status icons: yellow while
connecting, green when connected, red after a failed/lost connection, and gray
when disconnected. A periodic HTTP health check detects lost connections. Bridge
connection and encoder readiness are separate states.

Connected/connecting sessions lock deployment folder/name/source settings,
Prepare, Build, Remove Image, and redundant Connect actions. Open Folder and Docker
Logs remain available. **Disconnect** releases only the UI connection; services
and accepted jobs continue. **Stop Bridge** stops the verified idle deployment
and unlocks setup for a rebuild. Loading a generation setup while connected keeps
the active connection settings.

During **Build Image**, an activity bar and bounded live log tail show the current
step. An overall percentage is not fabricated: source resolution, layer downloads,
compilation, cached stages, and image export have different workloads.

Edit `configuration/.env` while the deployment is stopped:

| Setting | Meaning |
| --- | --- |
| `BRIDGE_BIND_ADDRESS` | Published host interface; defaults to `127.0.0.1` |
| `BRIDGE_PORT` | Host bridge port; container always listens on 7861 |
| `BRIDGE_DEVICE` | Motion inference: `cuda`, `cpu`, or `auto` |
| `ENCODER_DEVICE` | Encoder inference, independent of the motion device |
| `BASE_IMAGE` | Tested Torch/CUDA base; changing it requires a build |
| `KIMODO_IMAGE` | Built image tag for this deployment |
| `ALLOW_REMOTE_SHUTDOWN` | Allow authenticated bridge shutdown; false for shared servers |

Both services request NVIDIA GPU access. Selecting CPU inference does not remove
that reservation; GPU-free deployments require removing `gpus: all` from Compose.
CPU encoding can require substantial system RAM. The encoder and motion model
share the selected GPU by default; check free VRAM when other DCC applications run.

**Stop Bridge** in Docker mode first checks the bridge identity and asks its API to
stop accepting jobs. Busy bridges refuse. It then stops this project's bridge and
encoder; no data folders or volumes are removed. An unreachable running bridge is
left alone because its work state cannot be verified. Inspect its logs on the host.

**Restart Bridge** stops and starts the project using its latest built image.
After a GT Tools update, run **Build Image** before restarting. A build does not
interrupt running containers. Startup does not automatically build or pull images.
Intentional API shutdown exits successfully; `on-failure:3` does not restart it.
Container termination is handled through SIGTERM. Interrupted jobs become failed
on the next bridge startup; jobs are not automatically resumed.

Choose **Text encoder** or **Bridge**, then **View Docker Logs** to see that
container's output in a refreshing log window, including stopped containers.
Open Docker Desktop from that window to inspect containers there.
For a portable snapshot, the import-safe `export_logs()` helper remains available
and writes `logs/containers.log`. Python service logs rotate under `logs/`, and
Docker's own logs are bounded independently.

For recovery from incompatible latest sources, image deletion is usually not
required: Stop Bridge, select stable revisions, Build Image, then Connect / Start.
The optional **Remove Image...** action previews its exact scope and asks for
confirmation. It refuses running services and images referenced by other
containers, removes only stopped owned containers and the selected image tag,
and revalidates the image ID before removal. Models, jobs, credentials, sources,
and logs are retained. No forced image deletion, volume removal, or global prune
is performed. Build again before starting services.

New images use `/opt/kimodo-bridge/gt/utils/kimodo.py` for the bridge module. The
`gt.utils.kimodo` Python import and the versioned WSL launcher remain unchanged.
Rebuild and restart older images to get the renamed path and live encoder progress;
the existing model cache does not need to be deleted or downloaded again.

To administer the prepared deployment without Maya, enter `configuration/` and run:

```shell
docker compose build bridge
docker compose up -d --no-build --pull never
docker compose ps
docker compose logs --tail 200
```

The GUI stop action provides the busy-job check; direct Docker stop/restart
commands bypass that check. Do not use them during active jobs unless intentionally
interrupting work. Never remove the persistent data as part of routine restart.

The same preparation/build services can be scripted outside Maya:

```python
from gt.tools.kimodo_generator import kimodo_generator_docker as deployment

directory = "/absolute/docker-data/kimodo"
deployment.prepare_deployment(directory)
deployment.build_image(directory)
```

## Network GPU servers

Prepare/build on the Docker host. Set `BRIDGE_BIND_ADDRESS` to its LAN interface
(or `0.0.0.0` deliberately), choose a port, and set `ALLOW_REMOTE_SHUTDOWN=false`.
Keep the generated `COMPOSE_PROJECT_NAME`. Start Compose on that host and permit
the published port through the intended network/firewall boundary.

In Maya, choose **Connect to existing bridge**, enter `http://gpu-server:7861`
(adjust the port), and enter that deployment's `secrets/bridge_token` value in the
Access token field. No shared drive, local Docker install, or Kimodo Python is
required on the Maya machine. Managed **Start in Docker** only supports a local
engine and localhost URL; it does not administer a remote Docker daemon.

Only the bridge port is published. The encoder stays private at
`http://text-encoder:9550`; Maya's diagnostic runs through the bridge. The server
controls the encoder URL, so diagnostic requests cannot supply arbitrary URLs.
The optional upstream browser demo is not started by this deployment.

The bridge uses bearer authentication over HTTP. Use a trusted private network,
VPN, or HTTPS reverse proxy when encryption is needed. The client supports HTTPS.
One shared token gives access to the service's jobs; this is not per-user access
control. Generation runs sequentially through the bridge's bounded queue.

## Batch Processor

Kimodo Generate tasks use **existing** connection mode for local and remote Docker
bridges. Configure the bridge URL and `token_environment`, then provide the bridge
token in that environment variable before launching the batch workers. Store only
the variable name in task settings. Do not copy tokens into project JSON files.
Start the deployment separately; batch workers do not build or create containers.

## Build sources

Latest is the default build policy. Each build resolves the upstream default
branches to concrete Kimodo and Viser commit hashes. **Force stable revisions** skips
that lookup and uses the known pinned pair. If latest resolution or the latest
build fails, the tool can retry the stable pair once. A failed stable build stops;
there are no indefinite retries. Existing tracked source edits and unrecorded
checkouts stop the operation rather than being reset for fallback.

`deployment.json` records the selected policy, currently checked-out commits,
source selection (`latest`, `stable`, or `stable_fallback`), and the last successful
build's commits. `logs/build.log` records lookup/build fallback reasons. Changing
the checkbox affects the next build; it does not rebuild or restart containers.

The Dockerfile uses the selected Kimodo revision's dependency file and additionally
pins its SOMA-X Git dependency.
The default base image is a version tag; deployments requiring digest-level
reproducibility can put a digest-qualified image in `BASE_IMAGE`.

`kimodo_revision` selects a commit of Kimodo's upstream Git source, and
`viser_revision` selects a commit of Kimodo's Viser dependency. These Git hashes
keep builds tied to known source versions; they are not Docker image IDs or model
weight versions. Viser is installed because upstream Kimodo depends on it, even
though this deployment does not run the optional browser demo. `KIMODO_IMAGE`
selects the resulting Docker image tag instead.

Existing source checkouts are verified before building. Clean checkouts at the
previously recorded revision can update to the selected commit; no forced reset
or cleanup is used. Tracked edits or an unrecorded commit require review. Existing
configuration and secrets are retained by repeated preparation. Back up this
folder, especially its secrets and jobs, before migrating it to another host.

Upstream references: [Kimodo Docker setup](https://research.nvidia.com/labs/sil/projects/kimodo/docs/getting_started/installation_docker.html),
[Docker Desktop GPU support](https://docs.docker.com/desktop/features/gpu/).

Deployment settings can be collapsed after setup; this choice is saved. Encoder
progress remains visible outside this section while loading, then hides two
seconds after readiness is confirmed. The status indicator stays yellow while
the encoder loads and turns green when ready. WSL and Windows use separate
launch settings panels and retain their own Python environment settings.

### Windows RAM and GPU allocation

The Compose services have no per-container RAM limit and expose all GPUs. On
Docker Desktop's WSL 2 backend, the WSL VM defaults to half of Windows RAM.
That ceiling is separate from GPU VRAM; increasing it does not increase VRAM.
For example, on a 128 GB workstation you can allow WSL up to 120 GB by merging
this into `%USERPROFILE%\.wslconfig` (preserve any existing settings):

```ini
[wsl2]
memory=120GB
```

This is a ceiling, not a reservation. Windows and Maya still need RAM, so using
all physical RAM is not recommended. Apply it when no work is running: quit
Docker Desktop, run `wsl --shutdown`, then restart Docker Desktop and reconnect.
This affects all WSL 2 distributions and interrupts their running processes.
No machine-wide memory setting is changed by Kimodo Generator.

References: [WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
and [Docker Desktop GPU support](https://docs.docker.com/desktop/features/gpu/).

### Batch Processor

In **Kimodo Generate > Connection**, choose **Start / reuse local Docker** and
select an existing deployment prepared and built by Kimodo Generator. Leave the
Docker executable empty for automatic detection. **Use Saved Generator Connection**
copies the saved endpoint and deployment references; tokens are read from the
selected deployment at runtime, never serialized in the batch project. Workers
start or reuse that deployment, wait for the encoder within the Startup timeout,
and never build images or change deployments. For a container on another
machine, use **Existing bridge / remote Docker** and a token environment variable.

**Kimodo Definition > Generation > Model > Get** queries the first enabled
Kimodo Generate task after that definition. With no downstream generator, it
uses the saved Kimodo Generator connection. Start the bridge first; discovery
never launches services or submits work. Selecting a model also updates Model FPS
from the server's current metadata. A setup / definition file controls its own
model, so the local model selector is disabled while that file is set.

**NumPy arrays only (.npz)** moves each downloaded native array out of recovery
storage into the target folder, using the configured output name, relative
folders and sample suffix (for example `walk_s001.npz`). It creates no Maya scenes
or artifact bundle. The usual overwrite, skip-existing, retry and cache cleanup
settings still apply. JSON definitions and server-side results are preserved.

### Batch credentials

Keep **Credentials: Automatic (local deployment)** for local Docker, including
**Existing bridge** when its containers are already running. Select the local
deployment folder or click **Use Saved Generator Connection**. With a matching
localhost URL, the saved Generator deployment is also found automatically.
The client checks the configured port before reading the deployment token, then
checks the authenticated deployment identity before submitting work. No environment
variable is needed; old unused token-variable settings are ignored for local deployments.

For a remote bridge, explicitly choose **Environment variable (remote / advanced)**.
**Token variable name** is the name of a variable containing the remote server's token,
not the token itself. Configure it before launching Maya so workers inherit it.
**No authentication (legacy bridge)** is only for servers already configured to allow
requests without a token; choosing it does not disable Docker's server authentication.
Local token files are never automatically forwarded to remote URLs.

After correcting a failed request or updating the bridge, enable **Retry failed jobs**
in the Generate task to submit a new job. Otherwise its recovery record deliberately
retains the existing failed job ID. The sparse multi-prompt conditioning compatibility
fix is included in the bridge; existing images must be rebuilt and restarted to receive it.

### WSL cache location

New WSL launches stage the bridge under `~/.cache/kimodo-bridge/<source-hash>/`
and store server jobs in `~/.cache/kimodo-bridge/jobs/`. Restart an existing WSL
bridge to apply this default. Old `~/.cache/gt-tools/kimodo/` data is retained;
nothing is moved or deleted automatically. An explicit `--directory` still wins.
Docker continues to use its configured `/data/jobs` bind mount.
