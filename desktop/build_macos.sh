#!/bin/bash
# Build a native macOS single executable; recipients need no Python/Node/FFmpeg.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$(uname -s)" != Darwin ]]; then
    echo 'This script must run on macOS.' >&2
    exit 1
fi
python="${VPT_BUILD_PYTHON:-$repo/server/.venv/bin/python}"
ffmpeg_dir="${1:-${VPT_FFMPEG_DIR:-}}"
if [[ -z "$ffmpeg_dir" ]]; then
    ffmpeg_dir="$(dirname "$(command -v ffmpeg)")"
fi
export VPT_FFMPEG_DIR="$(cd "$ffmpeg_dir" && pwd)"
for binary in ffmpeg ffprobe; do
    if [[ ! -x "$VPT_FFMPEG_DIR/$binary" ]]; then
        echo "Missing executable: $VPT_FFMPEG_DIR/$binary" >&2
        exit 1
    fi
done
"$python" -c 'import PyInstaller; import platform; print("Build architecture:", platform.machine())'
(cd "$repo/front" && VITE_API_BASE_URL=/api npm run build)
cd "$repo"
"$python" -m PyInstaller --noconfirm --clean desktop/VideoPrinterTurbo.spec
# Ensure the bundled tools can run after extraction, including their dylibs.
./dist/VideoPrinterTurbo --check-binaries
echo "Built: $repo/dist/VideoPrinterTurbo"
echo 'Double-click in Finder to launch. Keep the Terminal window open; Ctrl+C stops the service.'
