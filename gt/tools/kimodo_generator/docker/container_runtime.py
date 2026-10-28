"""Container entry points, private health probes, and persistent service logs."""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys


def configure_logging(service):
    """Adds bounded service logs without recording credentials.

    Args:
        service (str): Bridge or encoder log filename stem.
    """
    os.makedirs("/data/logs", exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler = RotatingFileHandler(f"/data/logs/{service}.log", maxBytes=10 * 1024 * 1024,
                                  backupCount=3, encoding="utf-8")
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger().addHandler(handler)


def read_secret(name):
    """Reads a mounted secret without including its value in errors.

    Args:
        name (str): Secret file basename.

    Returns:
        str: Nonempty credential.
    """
    with open(f"/run/secrets/{name}", encoding="utf-8") as stream:
        value = stream.read().strip()
    if not value:
        raise ValueError(f"Configure secrets/{name} in the deployment folder before starting services.")
    return value


def run_encoder():
    """Runs upstream encoding with explicit device selection and reusable caches."""
    configure_logging("text-encoder")
    read_secret("hf_token")
    device = os.environ.get("ENCODER_DEVICE", "cuda")
    if device not in ("auto", "cpu", "cuda"):
        raise ValueError("ENCODER_DEVICE must be auto, cpu, or cuda.")
    import huggingface_hub.file_download as downloads
    from container_progress import EncoderProgress
    from gt.utils import kimodo

    def probe():
        """Checks readiness without running embedding inference."""
        kimodo.probe_text_encoder("http://127.0.0.1:9550", timeout=1)

    progress = EncoderProgress(probe=probe)
    progress.install(downloads)
    progress.start()
    try:
        from kimodo.scripts import run_text_encoder_server

        run_text_encoder_server.TEXT_ENCODER_PRESETS["llm2vec"]["kwargs"]["device"] = device
        sys.argv = [sys.argv[0]]
        run_text_encoder_server.main()
    except BaseException:
        progress.close(failed=True)
        raise
    else:
        progress.close()


def run_bridge():
    """Runs the bridge independently of encoder startup and model downloads."""
    configure_logging("bridge")
    from gt.utils import kimodo

    kimodo.serve(host="0.0.0.0", port=7861, directory="/data/jobs", token=read_secret("bridge_token"),
                 device=os.environ.get("BRIDGE_DEVICE", "cuda"),
                 text_encoder_url=os.environ.get("TEXT_ENCODER_URL", "http://text-encoder:9550"),
                 start_encoder=False,
                 allow_shutdown=os.environ.get("ALLOW_REMOTE_SHUTDOWN", "false").lower() == "true")


def check_health(service):
    """Probes services inside the container, including authenticated bridge health.

    Args:
        service (str): Bridge or encoder service name.
    """
    from gt.utils import kimodo

    if service == "encoder":
        kimodo.probe_text_encoder("http://127.0.0.1:9550", timeout=3)
    else:
        connection = kimodo.KimodoConnection(token=read_secret("bridge_token"), timeout=3)
        kimodo.KimodoClient(connection).health()


def main():
    """Dispatches a single container service or healthcheck command."""
    command = sys.argv[1] if len(sys.argv) > 1 else "bridge"
    if command == "bridge":
        run_bridge()
    elif command == "encoder":
        run_encoder()
    elif command in ("bridge-health", "encoder-health"):
        check_health(command.split("-")[0])
    else:
        raise ValueError(f"Unknown container command: {command}")


if __name__ == "__main__":
    main()
