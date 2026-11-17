#!/usr/bin/env python3
"""Source-locked contributor recruitment cut from October 20 graph-paper film.

The first 4,260 frames are an unaltered editorial *selection* of the existing
genuine-capture film, re-encoded for concatenation. The four new panels are
plainly editorial and contain no invented gameplay. No release gate is awarded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw
import graph_paper_trailer_art_direction as art

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "media/showcase/2026-10-20/graphpaper-final/ur-recomp-graphpaper-action-80s-1080p.mp4"
LOGO = ROOT / "media/showcase/2026-10-20/graphpaper-source/uniracers_graphpaper_logo.jpg"
TRACK = ROOT / "media/showcase/2026-10-20/graphpaper-source/uniracers_track_unicycle.jpg"
JUMPS = ROOT / "media/showcase/2026-10-20/blue-action-final/verified-source-action-ordinal-0570.png"
EXPECTED = {
    SOURCE: "367375ef998ca951eca45a1383ffa33014d4975780eb21988d5a7a19f945888b",
    LOGO: "489b45ccf5d8d6da4d25b34e841ba9dded96814444a5f06c78325ff45be379a9",
    TRACK: "f5948a2af00352c56169c5059e3f24178b0e6e5ef486ced6a85e048f50091032",
}
OUT = ROOT / "media/showcase/2026-10-26/recruitment"
FPS = 60
BASE_FRAMES = 4260
CARD_FRAMES = 360
CARDS = ("playtest", "artists", "agent_hours", "join")
REPO_URL = "github.com/gamesbyian/UR-Recomp"
EMAIL = "ianmakesjokes@gmail.com"


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(*cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)["streams"]


def text(draw, message, x, y, size=38, color=art.INK, bold=True, max_width=1500):
    art.label(draw, message, (x, y), size, color, bold, max_width=max_width)


def main_card(which):
    im = art.base()
    art.footer(im, TRACK)
    d = ImageDraw.Draw(im)
    defs = {
        "playtest": ("TEST THE WINDOWS BUILD", "REAL HARDWARE / REAL FEEDBACK", "CONTRIBUTOR PLATE / 01"),
        "artists": ("REBUILD THE RACERS", "2D + 3D / CHARACTER + ENVIRONMENT ART", "CONTRIBUTOR PLATE / 02"),
        "agent_hours": ("PUT AGENT HOURS TO WORK", "GOOD TASKS / TESTS / REVIEWABLE CHANGES", "CONTRIBUTOR PLATE / 03"),
        "join": ("YOUR NEXT LAP STARTS HERE", "PLAYTEST / CREATE ART / CONTRIBUTE AGENT HOURS", "CONTRIBUTOR PLATE / 04"),
    }
    title, deck, kicker = defs[which]
    art.header(im, LOGO, title, deck, kicker)
    if which == "playtest":
        items = [
            ("01", "ONE-PLAYER + SPLIT-SCREEN", "Real controller-driven play"),
            ("02", "MONITORS + AUDIO", "1080p / 4K / fullscreen / device behavior"),
            ("03", "RECORDS + RECOVERY", "Racer profiles / saves / cold restarts"),
        ]
        for idx, (num, name, detail) in enumerate(items):
            y = 318 + idx * 151
            d.rounded_rectangle((123, y, 1800, y + 135), 12, fill=(255, 255, 251), outline=(152, 155, 146), width=2)
            text(d, num, 150, y + 23, 49, art.RED, max_width=100)
            d.line((264, y+18, 264, y+115), fill=(188, 179, 161), width=3)
            text(d, name, 300, y+10, 43)
            text(d, detail, 302, y+75, 26, art.SLATE, False)
        text(d, "Independent physical Windows acceptance is still needed.", 130, 804, 25, art.RED)
    elif which == "artists":
        d.rounded_rectangle((120, 318, 1038, 759), 16, fill=(247, 244, 237), outline=(127, 133, 128), width=3)
        if JUMPS.is_file():
            src = Image.open(JUMPS).convert("RGB")
            src.thumbnail((874, 373), Image.Resampling.LANCZOS)
            im.paste(src, (142 + (874-src.width)//2, 337 + (373-src.height)//2))
        d = ImageDraw.Draw(im)
        text(d, "GENUINE JUMPS CAPTURE / AIRBORNE RACER", 149, 766, 21, art.RED)
        for y, h, sub in [
            (339, "MODEL + RIG", "Faithful rounded 1994 CGI character"),
            (471, "DRAW + ANIMATE", "Coherent high-density racer poses"),
            (603, "PAINT + COMPOSITE", "Course art / UI / source-aware layers"),
        ]:
            d.line((1090, y, 1788, y), fill=art.GOLD, width=4)
            text(d, h, 1090, y+12, 35, max_width=690)
            text(d, sub, 1090, y+74, 22, art.SLATE, False, 690)
        text(d, "Current procedural 4x racers are a technical baseline, NOT approved final art.", 126, 833, 23, art.RED, max_width=1615)
    elif which == "agent_hours":
        boxes = [("01", "PICK A JOB"), ("02", "RUN AN AGENT"), ("03", "SUBMIT + REVIEW")]
        for idx, (num, label) in enumerate(boxes):
            x = 124 + idx * 572
            d.rounded_rectangle((x, 339, x+538, 630), 16, fill=(255, 255, 250), outline=(133, 138, 130), width=3)
            text(d, num, x+25, 365, 73, art.RED, max_width=450)
            d.line((x+28, 482, x+510, 482), fill=art.GOLD, width=4)
            text(d, label, x+26, 518, 31, max_width=477)
        text(d, "FIVE INTERCHANGEABLE HOURLY AGENTS / ONE RANKED WORKBOARD", 141, 679, 31, art.INK, max_width=1652)
        text(d, "Contribute compute and engineering time. Tests and integration still matter.", 143, 745, 25, art.SLATE, False)
        text(d, "Start with AGENTS.md and docs/HOURLY-AGENT-LINES.md", 143, 801, 24, art.RED)
    elif which == "join":
        text(d, "PLAYTEST.", 124, 328, 88, art.INK, max_width=1580)
        text(d, "CREATE ART.", 124, 431, 88, art.RED, max_width=1580)
        text(d, "CONTRIBUTE.", 124, 533, 88, art.INK, max_width=1580)
        d.rounded_rectangle((116, 666, 1803, 834), 16, fill=(255, 255, 251), outline=art.RED, width=4)
        text(d, REPO_URL, 146, 681, 42, art.RED, max_width=1610)
        text(d, EMAIL, 149, 751, 39, art.INK, max_width=1600)
    return im


def encode_segment(input_path, path, frames, still=False):
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
    if still:
        cmd += ["-loop", "1", "-framerate", str(FPS)]
    video_filter = "fps=60,scale=1920:1080:flags=lanczos,format=yuv420p"
    if not still:
        # Historical source graphics sometimes call the early 4x technical
        # prototype "approved". Likeness approval was subsequently revoked.
        # Keep the actual source clip and state the CURRENT art verdict onscreen.
        video_filter += (
            ",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ":text='4x TECHNICAL ART - CHARACTER LIKENESS NOT APPROVED'"
            ":x=416:y=855:fontsize=24:fontcolor=0xAF352B"
            ":box=1:boxcolor=0xFCFAF2@0.95:boxborderw=8"
            ":enable='between(t,46,61)'"
        )
    cmd += ["-i", input_path, "-an", "-frames:v", str(frames), "-vf", video_filter,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", "120", "-keyint_min", "120", "-sc_threshold", "0",
            "-r", "60", "-video_track_timescale", "15360", "-movflags", "+faststart", path]
    run(*cmd)


def render(output, plates_only=False):
    for path, expected in EXPECTED.items():
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError("Missing or changed authenticated source: " + str(path))
    output.mkdir(parents=True, exist_ok=True)
    plates = output / "cards"
    plates.mkdir(exist_ok=True)
    for name in CARDS:
        main_card(name).save(plates / (name + ".png"))
    if plates_only:
        return
    work = output / "_work"
    work.mkdir(exist_ok=True)
    first = work / "00-original-edit.mp4"
    encode_segment(SOURCE, first, BASE_FRAMES)
    clips = [first]
    for idx, name in enumerate(CARDS, 1):
        dest = work / (f"{idx:02d}-" + name + ".mp4")
        encode_segment(plates / (name + ".png"), dest, CARD_FRAMES, True)
        clips.append(dest)
    concat = work / "segments.txt"
    concat.write_text("".join("file '" + str(p.resolve()) + "'\n" for p in clips))
    video = work / "silent-cut.mp4"
    run("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", concat, "-c:v", "copy", video)
    sound = work / "score.m4a"
    audio_filter = (
        "[0:a]asplit=2[x][y];"
        "[x]atrim=0:71,asetpts=PTS-STARTPTS[a];"
        "[y]atrim=47:71,asetpts=PTS-STARTPTS,"
        "afade=t=in:st=0:d=0.4,afade=t=out:st=22:d=2[b];"
        "[a][b]concat=n=2:v=0:a=1,aresample=48000[out]"
    )
    run("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", SOURCE,
        "-filter_complex", audio_filter, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", sound)
    final = output / "ur-recomp-recruit-contributors-95s-1080p.mp4"
    run("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", video, "-i", sound, "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", final)
    streams = probe(final)
    v = next(s for s in streams if s["codec_type"] == "video")
    if (int(v["width"]), int(v["height"]), v["r_frame_rate"], int(v["nb_read_frames"])) != (1920, 1080, "60/1", 5700):
        raise RuntimeError("Unexpected exact final video stream: " + json.dumps(v))
    if not any(s["codec_type"] == "audio" for s in streams):
        raise RuntimeError("Final film is missing soundtrack")
    witnesses = {}
    for sec in (6, 13, 22, 37, 52, 66, 73, 79, 85, 91, 94):
        png = output / ("review-%02ds.png" % sec)
        run("ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", str(sec), "-i", final, "-frames:v", "1", png)
        witnesses[png.name] = digest(png)
    manifest = {
        "edition": "2026-10-26 targeted-contributor recruitment",
        "film": final.name, "sha256": digest(final),
        "duration_seconds": 95, "fps": 60, "frames": 5700, "size": [1920, 1080],
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": EXPECTED[SOURCE],
                   "selected_first_frames": BASE_FRAMES,
                   "source_film_original_frames": 4800},
        "new_editorial_panels": [
            {"name": name, "start_seconds": 71 + i*6, "duration_seconds": 6,
             "classification": "editorial, not game capture"}
            for i, name in enumerate(CARDS)
        ],
        "artwork_sha256": {"logo": EXPECTED[LOGO], "track": EXPECTED[TRACK]},
        "witnesses_sha256": witnesses,
        "boundaries": [
            "No newly captured 1P or Modern native menu footage; original film's 1994 title/menu remains.",
            "Original 4K framebuffer measurement is not native authored 4K racer art.",
            "4x procedural racer studies are not approved for likeness.",
            "No independently admitted full USA original/native event or certified physical Windows release.",
            "Three action courses in existing film are three independent authentic 2P sessions, not one race.",
            "New contributor cards are illustrated editorial, never synthetic gameplay.",
            "A visible editorial corrective label disambiguates historical art technical approval from current character-likeness rejection."
        ],
    }
    (output / "recruitment-provenance.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"film":str(final),"sha256":digest(final),"frames":5700},indent=2))
    # Remove intermediates after both source-locked checks and output checks.
    for entry in work.iterdir():
        entry.unlink()
    work.rmdir()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=OUT)
    ap.add_argument("--cards-only", action="store_true")
    args = ap.parse_args()
    render(args.outdir, args.cards_only)
