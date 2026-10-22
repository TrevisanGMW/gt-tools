# syntax=docker/dockerfile:1
# CUDA 12.8 / PyTorch 2.7 supports Blackwell GPUs, including the RTX 5090.
ARG BASE_IMAGE=pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/data/models/huggingface \
    HF_TOKEN_PATH=/run/secrets/hf_token \
    PYTHONPATH=/opt/kimodo-bridge

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates cmake build-essential libegl1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY kimodo/ /workspace/
# Keep the upstream dependency lock; pin the upstream SOMA dependency as well.
ARG SOMA_REVISION=56a3d957a549c66425b500fddf7f3183bc6fbdff
RUN python -c "from pathlib import Path; p = Path('docker_requirements.txt'); p.write_text(p.read_text().replace('git+https://github.com/NVlabs/SOMA-X.git', 'git+https://github.com/NVlabs/SOMA-X.git@${SOMA_REVISION}'))"
RUN --mount=type=cache,target=/root/.cache/pip \
    SKIP_MOTION_CORRECTION_IN_SETUP=1 python -m pip install -r docker_requirements.txt

COPY kimodo-bridge/ /opt/kimodo-bridge/
COPY container_runtime.py /opt/container_runtime.py
COPY container_progress.py /opt/container_progress.py
EXPOSE 7861
ENTRYPOINT ["python", "-u", "/opt/container_runtime.py"]
CMD ["bridge"]
