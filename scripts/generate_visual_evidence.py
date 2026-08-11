#!/usr/bin/env python3
"""Render source-versus-output evidence for the bundled fixed-grid experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS_SIZE = (1400, 860)
DURATIONS_MS = (4200, 3600, 3600, 4200)
HOLD_LABEL = "EXPERIMENTAL — 40 unresolved / 78 emitted; source coverage unknown"
CLOSEUP_ROWS = ((0, 5), (7, 12), (14, 19))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int) -> ImageFont.FreeTypeFont:
    # Pillow 12.1.0's packaged default font avoids a host-font dependency. Text
    # cells are positioned explicitly below, so proportional metrics cannot
    # collapse the fixed-grid result.
    return ImageFont.load_default(size=size)


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    draw.rounded_rectangle(box, radius=16, fill="#ffffff", outline="#c8c8c0", width=2)
    draw.text((box[0] + 22, box[1] + 18), title, font=font(22), fill="#202124")


def fixed_grid(
    draw: ImageDraw.ImageDraw,
    rows: list[str],
    origin: tuple[int, int],
    *,
    cell_width: int,
    cell_height: int,
    text_size: int,
) -> None:
    grid_font = font(text_size)
    x0, y0 = origin
    for row_index, row in enumerate(rows):
        for column_index, glyph in enumerate(row):
            if glyph == " ":
                continue
            x = x0 + column_index * cell_width
            y = y0 + row_index * cell_height
            bounds = draw.textbbox((0, 0), glyph, font=grid_font)
            glyph_width = bounds[2] - bounds[0]
            draw.text(
                (x + (cell_width - glyph_width) / 2, y),
                glyph,
                font=grid_font,
                fill="#151515",
            )


def common_header(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, CANVAS_SIZE[0], 60), fill="#182027")
    draw.text(
        (28, 17),
        "SCREENSHOT OF ASCII ART  TO  FIXED-GRID TXT",
        font=font(27),
        fill="#ffffff",
    )
    draw.rectangle((0, 60, CANVAS_SIZE[0], 116), fill="#ffd166")
    hold_font = font(23)
    prefix = "EXPERIMENTAL "
    suffix = " 40 unresolved / 78 emitted; source coverage unknown"
    draw.text((28, 76), prefix, font=hold_font, fill="#351c00")
    dash_x = 28 + round(draw.textlength(prefix, font=hold_font))
    # Pillow's packaged font has no em dash. Drawing the long horizontal mark
    # keeps the mandated label exact without adding a host-font dependency.
    draw.rectangle((dash_x + 2, 89, dash_x + 22, 91), fill="#351c00")
    draw.text((dash_x + 26, 76), suffix, font=hold_font, fill="#351c00")


def source_crop_for_rows(
    row_start: int,
    row_stop: int,
    calibration: dict[str, object],
    source_height: int,
) -> tuple[int, int, int, int]:
    grid = calibration["grid"]
    assert isinstance(grid, dict)
    baseline = float(grid["first_baseline_y_px"])
    line_height = float(grid["line_height_px"])
    measurement = grid["row_crop_measurement"]
    assert isinstance(measurement, dict)
    top_offset = float(measurement["top"])
    bottom_offset = float(measurement["bottom"])
    top = max(0, round(baseline + row_start * line_height + top_offset))
    bottom = min(
        source_height,
        round(baseline + (row_stop - 1) * line_height + bottom_offset),
    )
    return (0, top, int(calibration["canvas"]["width_px"]), bottom)


def overview_frame(source: Image.Image, rows: list[str]) -> Image.Image:
    image = Image.new("RGB", CANVAS_SIZE, "#f2f1eb")
    common_header(image)
    draw = ImageDraw.Draw(image)
    draw.text((30, 136), "FULL BUNDLED SAMPLE", font=font(25), fill="#30343b")
    panel(draw, (30, 176, 665, 804), "INPUT | sample/source.normalized.png")
    panel(draw, (695, 176, 1370, 804), "OUTPUT | exact machine-ocr.txt (22 x 37)")

    shown_source = source.resize((530, 585), Image.Resampling.LANCZOS)
    image.paste(shown_source, (82, 218))
    fixed_grid(draw, rows, (760, 236), cell_width=14, cell_height=24, text_size=20)
    draw.text(
        (720, 752),
        "? = unresolved emitted cell  /  blank cells may include OCR omissions",
        font=font(17),
        fill="#7a2100",
    )
    return image


def closeup_frame(
    source: Image.Image,
    rows: list[str],
    source_crop: tuple[int, int, int, int],
    row_range: tuple[int, int],
    index: int,
) -> Image.Image:
    image = Image.new("RGB", CANVAS_SIZE, "#f2f1eb")
    common_header(image)
    draw = ImageDraw.Draw(image)
    start, stop = row_range
    draw.text(
        (30, 136),
        f"MATCHED CLOSE-UP {index}/3 | GRID ROWS {start + 1}-{stop}",
        font=font(25),
        fill="#30343b",
    )
    panel(draw, (30, 176, 680, 636), f"SOURCE CROP | y={source_crop[1]}-{source_crop[3]} px")
    panel(draw, (720, 176, 1370, 636), f"OUTPUT ROWS {start + 1}-{stop} | unchanged characters")

    crop = source.crop(source_crop)
    shown_source = crop.resize((610, round(crop.height * 610 / crop.width)), Image.Resampling.LANCZOS)
    image.paste(shown_source, (50, 290 - shown_source.height // 2 + 90))
    fixed_grid(
        draw,
        rows[start:stop],
        (748, 304),
        cell_width=16,
        cell_height=40,
        text_size=28,
    )
    draw.rounded_rectangle((130, 684, 1270, 802), radius=14, fill="#fff4d6", outline="#d29600", width=2)
    draw.text(
        (164, 710),
        "This is a visual comparison, not a pass. The same calibrated row band",
        font=font(20),
        fill="#482900",
    )
    draw.text(
        (164, 749),
        "shows recognitions, unresolved ? cells, and possible blank omissions.",
        font=font(20),
        fill="#482900",
    )
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--machine-output", type=Path, required=True)
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--gif", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    source = Image.open(args.source).convert("RGB")
    machine_text = args.machine_output.read_text(encoding="utf-8")
    rows = machine_text.splitlines()
    quality = json.loads(args.quality.read_text(encoding="utf-8"))
    calibration = json.loads(args.calibration.read_text(encoding="utf-8"))

    if len(rows) != 22 or {len(row) for row in rows} != {37}:
        raise ValueError("machine output must be the exact 22-by-37 fixed grid")
    if source.size != (424, 468):
        raise ValueError(f"unexpected bundled source size: {source.size}")
    emitted = sum(1 for glyph in machine_text if not glyph.isspace())
    unresolved = machine_text.count("?")
    if (
        quality["acceptance_status"] != "experimental_unaccepted"
        or quality["source_coverage_status"] != "unknown_without_accepted_transcript"
        or quality["emitted_non_space_cells"] != emitted
        or quality["unresolved_emitted_cells"] != unresolved
        or (unresolved, emitted) != (40, 78)
    ):
        raise ValueError("quality receipt does not match the held 40/78 sample")

    source_hash = sha256(args.source)
    output_hash = sha256(args.machine_output)
    quality_hash = sha256(args.quality)
    frame_records: list[dict[str, object]] = [
        {
            "id": "full-source-and-full-output",
            "duration_ms": DURATIONS_MS[0],
            "source_crop_px": [0, 0, source.width, source.height],
            "output_rows_zero_based_half_open": [0, len(rows)],
            "source_sha256": source_hash,
            "machine_output_sha256": output_hash,
        }
    ]
    frames = [overview_frame(source, rows)]
    for index, row_range in enumerate(CLOSEUP_ROWS, start=1):
        crop = source_crop_for_rows(row_range[0], row_range[1], calibration, source.height)
        frames.append(closeup_frame(source, rows, crop, row_range, index))
        frame_records.append(
            {
                "id": f"matched-closeup-{index}",
                "duration_ms": DURATIONS_MS[index],
                "source_crop_px": list(crop),
                "output_rows_zero_based_half_open": list(row_range),
                "source_sha256": source_hash,
                "machine_output_sha256": output_hash,
            }
        )

    args.gif.parent.mkdir(parents=True, exist_ok=True)
    first_palette = frames[0].quantize(colors=256)
    palette_frames = [first_palette] + [
        frame.quantize(palette=first_palette) for frame in frames[1:]
    ]
    palette_frames[0].save(
        args.gif,
        save_all=True,
        append_images=palette_frames[1:],
        duration=DURATIONS_MS,
        loop=0,
        # Preserve the common header across Pillow's delta-encoded GIF frames.
        disposal=1,
        optimize=False,
    )
    receipt = {
        "schema": "lateletter.fixed_grid_visual_evidence.v1",
        "artifact": args.gif.name,
        "canvas_px": {"width": CANVAS_SIZE[0], "height": CANVAS_SIZE[1]},
        "frame_count": len(frames),
        "hold_label_on_every_frame": HOLD_LABEL,
        "acceptance_status": "experimental_unaccepted",
        "source_coverage_status": "unknown_without_accepted_transcript",
        "source_sha256": source_hash,
        "machine_output_sha256": output_hash,
        "quality_receipt_sha256": quality_hash,
        "gif_sha256": sha256(args.gif),
        "semantic_frames": frame_records,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
