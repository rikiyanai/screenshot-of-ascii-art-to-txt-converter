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

python3 - "$output/machine-ocr.txt" "$output/quality.json" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

text_path = Path(sys.argv[1])
quality_path = Path(sys.argv[2])
text = text_path.read_text(encoding="utf-8")
lines = text.splitlines()
line_lengths = [len(line) for line in lines]
if not lines or len(set(line_lengths)) != 1:
    raise RuntimeError(f"recovery did not produce a rectangular grid: {line_lengths}")
emitted_non_space_cells = sum(1 for char in text if not char.isspace())
unresolved_emitted_cells = text.count("?")
tesseract_version = subprocess.run(
    ["tesseract", "--version"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()[0]
receipt = {
    "schema": "lateletter.fixed_grid_recovery_quality.v2",
    "acceptance_status": "experimental_unaccepted",
    "source_coverage_status": "unknown_without_accepted_transcript",
    "grid_rows": len(lines),
    "grid_columns": line_lengths[0],
    "grid_cells": sum(line_lengths),
    "emitted_non_space_cells": emitted_non_space_cells,
    "recognized_emitted_cells": emitted_non_space_cells - unresolved_emitted_cells,
    "unresolved_emitted_cells": unresolved_emitted_cells,
    "unresolved_among_emitted_fraction": (
        unresolved_emitted_cells / emitted_non_space_cells
        if emitted_non_space_cells
        else None
    ),
    "tesseract_version": tesseract_version,
    "acceptance_note": (
        "Output-only counts do not measure omitted source glyphs. No accepted "
        "transcript, recovery threshold, or operator acceptance is recorded."
    ),
}
quality_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(
    f"emitted-output result: {unresolved_emitted_cells}/"
    f"{emitted_non_space_cells} emitted non-space cells unresolved; "
    "source_coverage=unknown; status=experimental_unaccepted"
)
PY

printf 'recovered text: %s\n' "$output/machine-ocr.txt"
