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

source_hash=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$repo_root/sample/source.normalized.png")
calibration_hash=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$repo_root/sample/calibration.json")
if [ "$source_hash" != "9ea8eab2c0b378ed89ad2337515a6baea4ec81d0eace6ba042fab4abee63a3d3" ]; then
  echo "bundled sample checksum mismatch" >&2
  exit 65
fi
if [ "$calibration_hash" != "f8a1aca96ccc43a08b1981a7fff0d34ebe773f7cc45fe148178c3554d65f7944" ]; then
  echo "bundled calibration checksum mismatch" >&2
  exit 65
fi

python3 "$repo_root/scripts/recover_monospace_ascii.py" \
  "$repo_root/sample/source.normalized.png" \
  "$output" \
  --calibration "$repo_root/sample/calibration.json"

printf 'recovered text: %s\n' "$output/machine-ocr.txt"
