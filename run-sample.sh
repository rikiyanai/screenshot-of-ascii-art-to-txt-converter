#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 64
fi

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output=$1

if [ -e "$output" ]; then
  echo "refusing existing output path: $output" >&2
  exit 73
fi

command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required" >&2
  exit 69
}
command -v tesseract >/dev/null 2>&1 || {
  echo "tesseract is required" >&2
  exit 69
}
python3 -c 'import numpy; from PIL import Image' >/dev/null 2>&1 || {
  echo "NumPy and Pillow are required; install requirements.txt" >&2
  exit 69
}

python3 "$repo_root/scripts/recover_monospace_ascii.py" \
  "$repo_root/sample/source.normalized.png" \
  "$output" \
  --calibration "$repo_root/sample/calibration.json"

printf 'recovered text: %s\n' "$output/machine-ocr.txt"
