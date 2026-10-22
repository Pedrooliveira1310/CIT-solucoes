#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null
command -v ffprobe >/dev/null || { echo 'Instale FFmpeg (ffprobe e ffmpeg) pelo gerenciador de pacotes do sistema.' >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo 'Instale FFmpeg pelo gerenciador de pacotes do sistema.' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.lock
.venv/bin/flask --app run init-db
