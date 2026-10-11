#!/usr/bin/env python3
"""Source-locked continuous widescreen reveal and honest presentation comparison.

Only edits existing, independently validated host video. Requires FFmpeg/FFprobe.
No generated gameplay, no motion interpolation, no guest-code changes.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess

RACE_SHA = "182ef43ccf34f501dea4051312e71bf4d974a53dc6634cd98a5cbf3fae8ac130"
FRAMES = 600

def run(*args):
    subprocess.run(args, check=True)

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-count_frames", "-show_entries",
        "stream=width,height,avg_frame_rate,nb_read_frames", "-of", "json", str(path)
    ]))["streams"][0]

def render(inp, out, graph, seconds):
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(inp), "-filter_complex", graph, "-map", "[v]",
        "-t", str(seconds), "-an", "-c:v", "libx264", "-crf", "17",
        "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "60",
        "-movflags", "+faststart", str(out))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--race", type=pathlib.Path, required=True)
    ap.add_argument("--manifest", type=pathlib.Path, required=True)
    ap.add_argument("--outdir", type=pathlib.Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    assert manifest["guest_frame_start"] == 2100
    assert manifest["guest_frame_end"] == 2699
    assert manifest["consecutive_host_presentations"] == FRAMES
    assert manifest["dropped_or_skipped_host_frame_ids"] == 0
    assert manifest["control_guest_crc_sha256"] == manifest["recorded_guest_crc_sha256"]
    assert manifest["published_sha256"][args.race.name] == RACE_SHA
    assert digest(args.race) == RACE_SHA, "Video SHA mismatch"
    info = probe(args.race)
    assert (int(info["width"]), int(info["height"])) == (1920, 1080)
    assert info["avg_frame_rate"] == "60/1"
    assert int(info["nb_read_frames"]) == FRAMES
    args.outdir.mkdir(parents=True, exist_ok=True)

    # The genuine 342-column video keeps playing while matte panels uncover
    # 43 source columns on each side. All footage is uniformly fitted in a
    # 1728x972 editorial viewport so the labels sit OUTSIDE the game raster.
    # 1728 * (43/342) = 217.26px; 218px matte coverage is conservative.
    fade = "min(1,max(0,(t-1)/4.5))"
    reveal_graph = (
        "[0:v]setpts=PTS-STARTPTS,"
        "scale=1728:972:flags=neighbor,pad=1920:1080:96:54:black[base];"
        "color=c=black:s=218x972:r=60:d=7.5[left];"
        "color=c=black:s=218x972:r=60:d=7.5[right];"
        f"[base][left]overlay=x='96-218*{fade}':y=54:eval=frame[tmp];"
        f"[tmp][right]overlay=x='1606+218*{fade}':y=54:eval=frame,"
        "drawtext=text='ORIGINAL 256-COLUMN CENTRE':fontsize=30:fontcolor=white:"
        "x=96:y=8:enable='lt(t,3.2)',"
        "drawtext=text='WIDESCREEN 342-COLUMN WORLD':fontsize=30:fontcolor=white:"
        "x=96:y=8:enable='gte(t,3.2)',"
        "drawtext=text='GENUINE CONTINUOUS 2P CAPTURE':fontsize=23:"
        "fontcolor=white:x=w-text_w-96:y=13,format=yuv420p[v]"
    )
    # Only full-width source video is ever composited; covers cannot invent world.
    reveal = args.outdir / "authentic-widescreen-reveal-7s.mp4"
    render(args.race, reveal, reveal_graph, 7)

    # Editorial SAME-CAPTURE comparison, never represented as a separately
    # executed 256-wide reference. Both panels use identical timestamp IDs.
    # Stock centre has pixel aspect 7:6 and should occupy 4:3 in 1080p.
    comparison_graph = (
        "[0:v]setpts=PTS-STARTPTS,split=2[stock][wide];"
        "[stock]crop=w=1438:h=1080:x=241:y=0,"
        "scale=720:540:flags=neighbor,pad=960:1080:120:270:black[a];"
        "[wide]scale=960:540:flags=neighbor,"
        "pad=960:1080:0:270:black[b];"
        "[a][b]hstack=inputs=2,"
        "drawtext=text='256-COLUMN CENTRE CROP':fontsize=34:fontcolor=white:"
        "x=(960-text_w)/2:y=110:box=1:boxcolor=black@0.7:boxborderw=12,"
        "drawtext=text='342-COLUMN RECORDED WORLD':fontsize=34:fontcolor=white:"
        "x=960+(960-text_w)/2:y=110:box=1:boxcolor=black@0.7:boxborderw=12,"
        "drawtext=text='SAME SOURCE VIDEO - NOT TWO INDEPENDENT EXECUTIONS':"
        "fontsize=24:fontcolor=white:x=(w-text_w)/2:y=1023:"
        "box=1:boxcolor=black@0.7:boxborderw=10,format=yuv420p[v]"
    )
    comparison = args.outdir / "same-capture-centre-vs-wide-5s.mp4"
    render(args.race, comparison, comparison_graph, 5)

    # Retain review frames as direct decoded witnesses of the finished renders.
    stills = {}
    for video, moments in ((reveal, (0.25, 3.5, 6.5)),
                           (comparison, (0.25, 2.5, 4.5))):
        for index, moment in enumerate(moments):
            still = args.outdir / f"{video.stem}-review-{index:02d}.png"
            run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", str(moment), "-i", str(video), "-frames:v", "1", str(still))
            stills[still.name] = digest(still)

    output = {
        "schema": "UR-RECRUITMENT-CONTINUOUS-PRESENTATION/1",
        "review_frame_sha256": stills,
        "source": str(args.race),
        "source_sha256": RACE_SHA,
        "capture_manifest_sha256": digest(args.manifest),
        "source_guest_frames": [2100, 2699],
        "source_60fps_frames": 600,
        "guest_crc_capture_off_equals_on": True,
        "reveal": {
            "file": reveal.name, "sha256": digest(reveal),
            "duration_seconds": 7,
            "description": "Uninterrupted authentic 342-column world; side masks slide out to reveal already-recorded margins",
            "centre_original_columns": [43, 298],
            "editorial_overlay": "Animated black side mattes plus labels in exterior editorial letterbox"
        },
        "comparison": {
            "file": comparison.name, "sha256": digest(comparison),
            "duration_seconds": 5,
            "classification": "editorial_same_capture_crop_not_independent_original_render",
            "description": "Same-capture exact-time centre crop and full world, both at identical display scale",
            "independent_original_capture": False,
            "independent_guest_wram_state_comparison": False
        },
        "no_temporal_interpolation": True,
        "source_host_drawable": [960, 540],
        "output_encoded": [1920, 1080],
        "physical_4k_claim": False,
        "remastered_art_claim": False
    }
    (args.outdir / "presentation-provenance.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n")
    for item in (reveal, comparison):
        x = probe(item)
        assert (int(x["width"]), int(x["height"])) == (1920, 1080)
        print(item, digest(item), x["nb_read_frames"])

if __name__ == "__main__":
    main()
