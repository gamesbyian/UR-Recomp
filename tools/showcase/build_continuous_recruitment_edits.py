#!/usr/bin/env python3
"""Edit an independently verified continuous native 2P source into recruitment media.

The first ten seconds of BOTH edits are consecutive, unmodified-in-time
Baldosa gameplay. The remaining video comes from the October 10 provenance-
labelled *sampled-frame* recruitment teaser and is editorial, never claimed to
be newly recorded gameplay. The background music is the existing original
generated promotional score.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def probe(path: Path) -> dict:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_read_frames,r_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    streams = json.loads(p.stdout).get("streams", [])
    if len(streams) != 1:
        raise ValueError("Video must have exactly one video stream")
    return streams[0]


def source_contract(clip: Path, provenance: Path) -> dict:
    record = json.loads(provenance.read_text())
    count = record.get("consecutive_host_presentations")
    if (record.get("status") != "verified_consecutive_host_presentations"
            or count != 600
            or record.get("guest_frame_end", -1) - record.get("guest_frame_start", 0) + 1 != count
            or record.get("dropped_or_skipped_host_frame_ids") != 0
            or record.get("control_guest_crc_sha256") != record.get("recorded_guest_crc_sha256")):
        raise ValueError("Not accepted continuous native evidence")
    if record.get("published_sha256", {}).get(clip.name) != sha256(clip):
        raise ValueError("Continuous source video SHA-256 mismatch")
    p = probe(clip)
    if p.get("width") != 1920 or p.get("height") != 1080:
        raise ValueError("Clean delivery must be 1920x1080")
    if p.get("r_frame_rate") != "60/1" or int(p.get("nb_read_frames", -1)) != 600:
        raise ValueError("Clean delivery must contain precisely 600 genuine 60-fps frames")
    return record


def music(path: Path, duration: int) -> None:
    reference = Path(__file__).with_name("build_recruitment_teaser.py")
    spec = importlib.util.spec_from_file_location("ur_original_editorial_music", reference)
    if not spec or not spec.loader:
        raise RuntimeError("Original editorial soundtrack generator missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.editorial_music(path, duration=duration)


def render(clip: Path, existing: Path, soundtrack: Path, dest: Path,
           vertical: bool) -> None:
    # No frame interpolation on gameplay; 600 60-Hz frames feed directly
    # into the first 10 s. The old 24-Hz editorial material is cadence-
    # converted separately and retains its original sampled-frame labels.
    if vertical:
        first = (
            "[0:v]trim=start_frame=0:end_frame=600,setpts=PTS-STARTPTS,"
            "scale=720:405:flags=neighbor,pad=720:1280:0:437:black,"
            "drawtext=text='REAL NATIVE GAMEPLAY':fontsize=37:"
            "fontcolor=white:x=(w-text_w)/2:y=255,"
            "drawtext=text='2P ORIGINAL WIDESCREEN':fontsize=29:"
            "fontcolor=white:x=(w-text_w)/2:y=920,"
            "format=yuv420p[v0];"
        )
        second = (
            "[1:v]trim=start=7:duration=11,setpts=PTS-STARTPTS,"
            "fps=60,scale=720:1280:flags=lanczos,format=yuv420p[v1];"
        )
        total = 21
    else:
        first = (
            "[0:v]trim=start_frame=0:end_frame=600,setpts=PTS-STARTPTS,"
            "format=yuv420p[v0];"
        )
        second = (
            "[1:v]trim=start=3:duration=31,setpts=PTS-STARTPTS,"
            "fps=60,scale=1920:1080:flags=lanczos,format=yuv420p[v1];"
        )
        total = 41
    graph = first + second + "[v0][v1]concat=n=2:v=1:a=0[v]"
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(clip), "-i", str(existing), "-i", str(soundtrack),
        "-filter_complex", graph, "-map", "[v]", "-map", "2:a:0",
        "-t", str(total), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "112k",
        "-movflags", "+faststart", str(dest)], check=True)
    p = probe(dest)
    if (p["width"], p["height"], p["r_frame_rate"]) != (
        (720, 1280, "60/1") if vertical else (1920, 1080, "60/1")
    ):
        raise ValueError("Edited video format rejected")
    if int(p["nb_read_frames"]) != total * 60:
        raise ValueError("Edited video unexpectedly dropped frames")


def main() -> None:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--clip", type=Path, required=True)
    a.add_argument("--provenance", type=Path, required=True)
    a.add_argument("--teaser", type=Path, required=True)
    a.add_argument("--vertical", type=Path, required=True)
    a.add_argument("--outdir", type=Path, required=True)
    args = a.parse_args()
    source = source_contract(args.clip, args.provenance)
    args.outdir.mkdir(parents=True, exist_ok=True)
    horizontal = args.outdir / "ur-recomp-recruitment-continuous-20261010.mp4"
    short = args.outdir / "ur-recomp-recruitment-continuous-vertical-20261010.mp4"
    with tempfile.TemporaryDirectory(prefix="ur-recruitment-") as td:
        bed = Path(td) / "original-editorial-score.wav"
        music(bed, duration=42)
        render(args.clip, args.teaser, bed, horizontal, vertical=False)
        render(args.clip, args.vertical, bed, short, vertical=True)
    report = {
        "schema": "UR-CONTINUOUS-RECRUITMENT-EDIT/1",
        "source_video_sha256": sha256(args.clip),
        "source_provenance_sha256": sha256(args.provenance),
        "source_guest_frames": [source["guest_frame_start"], source["guest_frame_end"]],
        "originals": {
            "horizontal_editorial_teaser_sha256": sha256(args.teaser),
            "vertical_editorial_teaser_sha256": sha256(args.vertical)
        },
        "editorial": (
            "The leading 600 frames are the complete continuous native clip "
            "without interpolation. Following scenes reuse an existing "
            "explicitly sampled-frame October 10 development teaser; "
            "its cadence conversion is editorial, never gameplay evidence."
        ),
        "audio": "Existing deterministic original editorial score; no game soundtrack",
        "outputs": {
            p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in (horizontal, short)
        },
    }
    (args.outdir / "continuous-recruitment-edit-provenance.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
