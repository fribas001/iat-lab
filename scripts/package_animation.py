"""Encode Blender PNG frames as a compact, captioned, infinitely looping GIF."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--input", default="build/setup-animation")
parser.add_argument("--output", default="docs/images/setup-tour.gif")
parser.add_argument("--width", type=int, default=320, help="GIF image width before captions")
args = parser.parse_args()
folder, target = (root / args.input).resolve(), (root / args.output).resolve()
record = json.loads((folder / "frames.json").read_text(encoding="utf-8"))
frames = sorted(record["frames"], key=lambda item: item["index"])
if [frame["index"] for frame in frames] != list(range(record["frame_count"])):
    raise ValueError("A complete, contiguous frame sequence is required")
source_width, source_height = record["resolution"]
if args.width < 320:
    raise ValueError("Use at least 320 pixels to keep captions readable")
width, height = args.width, round(source_height * args.width / source_width)
font = ImageFont.load_default(size=16)
small = ImageFont.load_default(size=11)
composed = []
for entry in frames:
    path = folder / entry["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError(f"Frame hash mismatch: {path.name}")
    with Image.open(path) as source:
        if source.size != (source_width, source_height):
            raise ValueError("Inconsistent frame dimensions")
        frame = Image.new("RGB", (width, height + 64), "#142434")
        frame.paste(source.convert("RGB").resize((width, height), Image.Resampling.LANCZOS), (0, 32))
    draw = ImageDraw.Draw(frame)
    draw.text((14, 8), "IAT LAB", font=font, fill="#ffffff")
    draw.text((width - 114, 11), "INTERIOR TOUR", font=small, fill="#a9c9dc")
    label = "ARCHIVED PATHS + HEATMAP" if entry["archived_results_visible"] else "PHYSICAL SETUP"
    draw.text((14, height + 42), label, font=small, fill="#ffffff")
    draw.line((0, height + 63, width, height + 63), fill="#4ba7ca", width=2)
    composed.append(frame)
# One shared palette avoids unrelated color shifts between successive frames.
rows = (len(composed) + 7) // 8
atlas = Image.new("RGB", (160 * 8, 120 * rows * 2), "#142434")
for index, frame in enumerate(composed):
    thumb = frame.copy()
    thumb.thumbnail((160, 120))
    atlas.paste(thumb, (160 * (index % 8), 120 * (index // 8)))
    # Give the small plants/apparatus equal palette weight to the large blue walls.
    detail = frame.crop((round(width * .40), 32 + round(height * .25),
                         round(width * .70), 32 + round(height * .75))).resize((160, 120))
    atlas.paste(detail, (160 * (index % 8), 120 * (rows + index // 8)))
palette = atlas.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in composed]
# GIF time is quantized to 10 ms; alternating delays preserve the exact rate.
durations = [10 * (round((i + 1) * 100 / record["fps"]) - round(i * 100 / record["fps"]))
             for i in range(len(indexed))]
target.parent.mkdir(parents=True, exist_ok=True)
indexed[0].save(target, save_all=True, append_images=indexed[1:], duration=durations,
                loop=0, optimize=True, disposal=1)
with Image.open(target) as gif:
    assert gif.n_frames == len(indexed) and gif.info["loop"] == 0
    total = 0
    for index in range(gif.n_frames):
        gif.seek(index)
        gif.load()
        total += gif.info["duration"]
    assert total == sum(durations)
record.update(gif_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), gif_bytes=target.stat().st_size,
              gif_resolution=list(indexed[0].size), duration_ms=total, palette_colors=128,
              pillow_version=pillow_version, loop="infinite")
target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"Saved {target}: {len(indexed)} frames, {total / 1000:g} s, {target.stat().st_size / 1024**2:.2f} MiB")
