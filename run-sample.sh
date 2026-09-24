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
python3 -c 'import numpy; from PIL import Image, ImageFont' >/dev/null 2>&1 || {
  echo "NumPy and Pillow are required; install requirements.txt" >&2
  exit 69
}

# Tesseract is no longer required. It remains reachable through
# `--engine tesseract` for comparison only.

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

# The calibration is passed as a PRIOR only. The lattice is measured from the
# image, and the receipt records how far the measurement fell from the
# declaration.
python3 "$repo_root/scripts/recover_monospace_ascii.py" \
  "$repo_root/sample/source.normalized.png" \
  "$output" \
  --calibration "$repo_root/sample/calibration.json"

python3 - "$output/machine-ocr.txt" "$output/quality.json" <<'PY'
import json
import sys
from pathlib import Path

text_path = Path(sys.argv[1])
quality_path = Path(sys.argv[2])
receipt = json.loads(quality_path.read_text(encoding="utf-8"))
lines = text_path.read_text(encoding="utf-8").splitlines()
if not lines:
    raise RuntimeError("recovery produced no rows")

coverage = receipt["coverage"]
regime = receipt["regime"]
lattice = receipt["measured_lattice"]
typeface = receipt["inferred_typeface"]
agreement = receipt["reconstruction_agreement"]["ink_intersection_over_union"]

print(
    "regime: {regime}, median band drift {drift} cells against a {threshold} "
    "cell threshold, {ok}/{n} bands within it".format(
        regime=regime["regime"],
        drift=regime["median_drift_cells"],
        threshold=regime["threshold_cells"],
        ok=regime["qualifying_bands"],
        n=regime["evaluable_bands"],
    )
)
print(
    "coverage: {resolved}/{ink} ink-bearing source cells resolved, "
    "{ambiguous} ambiguous".format(
        resolved=coverage["resolved_cells"],
        ink=coverage["ink_bearing_source_cells"],
        ambiguous=coverage["ambiguous_cells"],
    )
)
print(
    "measured lattice: {x:.3f} x {y:.3f} px, aspect {a:.4f}, {c} columns x {r} rows".format(
        x=lattice["cell_advance_x_px"],
        y=lattice["line_height_px"],
        a=lattice["cell_aspect_w_over_h"],
        c=lattice["columns"],
        r=lattice["rows"],
    )
)
print(
    "inferred typeface: {font} @ {size}px, residual {residual:.2f}".format(
        font=Path(typeface["font"]).name,
        size=typeface["size"],
        residual=typeface["residual"],
    )
)
print(
    "reconstruction agreement (ink IoU): "
    + ("n/a" if agreement is None else f"{agreement:.3f}")
)
print("status: " + receipt["acceptance_status"])
PY

printf 'recovered text: %s\n' "$output/machine-ocr.txt"
printf 'reconstruction: %s\n' "$output/reconstruction.png"
