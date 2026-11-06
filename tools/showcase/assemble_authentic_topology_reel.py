#!/usr/bin/env python3
"""Assemble ONLY independently observed authentic hill / loop / ramp footage.

The review is an explicit external visual witness, not guessed from course names,
controller inputs, WRAM deltas or script success. Without a complete signed-off
review plus exact source SHA receipts, fail without emitting a movie.

The output is an editorial montage of genuine, consecutive source frames inside
each shot. It does not pretend the different source sessions are one race.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

FEATURES = {"loop", "ramp", "hill"}
SCHEMA = "UR-DYNAMIC-TOPOLOGY-VISUAL-REVIEW/1"
LEDGER = "UR-GENUINE-ASYNCHRONOUS-NATIVE-2P/1"
FPS = 60
FRAMECOUNT = 900
MIN_FRAMES = 180
MAX_FRAMES = 420

class AdmissionError(ValueError):
    pass

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def accepted_shots(ledger: dict, review: dict) -> list[dict]:
    if ledger.get("schema") != LEDGER or review.get("schema") != SCHEMA:
        raise AdmissionError("Unrecognized capture/review manifest")
    if review.get("review_method") not in ("human_video_screening", "model_assisted_video_frame_screening"):
        raise AdmissionError("Real video or source-frame screening method required")
    if not isinstance(review.get("reviewer"), str) or len(review["reviewer"].strip()) < 3:
        raise AdmissionError("Named reviewer required")
    if review.get("asserts_source_sessions_are_distinct") is not True:
        raise AdmissionError("Independent source-session editorial-cuts disclosure missing")
    shots = review.get("shots")
    if not isinstance(shots, list) or len(shots) < 3:
        raise AdmissionError("Three distinct source-observed features required")
    parsed = []
    features, used = set(), set()
    for item in shots:
        if not isinstance(item, dict):
            raise AdmissionError("Invalid review shot entry")
        name = item.get("route")
        feature = item.get("observed_feature")
        if not isinstance(name, str) or name not in ledger["routes"] or name in used:
            raise AdmissionError("Each shot must reference a distinct captured course/source route")
        if feature not in FEATURES or feature in features:
            raise AdmissionError("Need distinct visible loop, ramp and hill evidence")
        entry = ledger["routes"][name]
        if feature == "loop" and entry.get("course") not in ("Looper", "Loopback", "Two Loops"):
            raise AdmissionError("Loop shot must have identified authentic loop-course source")
        if feature == "ramp" and entry.get("course") not in ("MegaJump", "Jumps", "123 Jump", "Jumpover"):
            raise AdmissionError("Ramp shot must have an identified source course candidate")
        if feature == "hill" and entry.get("course") not in ("Hill Climb", "Hairpin Hill", "Down+Up", "Twinpeak"):
            raise AdmissionError("Hill shot must have an identified source course candidate")
        if entry.get("sha256") != item.get("source_sha256"):
            raise AdmissionError("Clip SHA doesn't match accepted native source ledger")
        span = entry.get("capture_frame_start_end")
        if not isinstance(span, list) or len(span) != 2 or span[1]-span[0] != 899:
            raise AdmissionError("No verified consecutive 900 native source frame IDs")
        first, count = item.get("first_source_ordinal"), item.get("frame_count")
        if (type(first) is not int or type(count) is not int
                or first < 0 or not MIN_FRAMES <= count <= MAX_FRAMES
                or first + count > FRAMECOUNT):
            raise AdmissionError("Source shot outside 900 genuine consecutive frames")
        if item.get("source_gameplay_visually_observed") is not True:
            raise AdmissionError("Track topology must actually be visible")
        if item.get("full_two_player_raster_visible") is not True:
            raise AdmissionError("Cannot crop away one racer")
        if item.get("two_racers_visibly_separated") is not True:
            raise AdmissionError("Source player separation must be independently observed")
        if not isinstance(item.get("observation"), str) or len(item["observation"].strip()) < 48:
            raise AdmissionError("Observation must explain actual visual track, racer, and motion evidence")
        if item.get("source_video_guest_state_modified") is not False:
            raise AdmissionError("Source guest physics, course, and state must be unmodified")
        coords = entry.get("real_guest_world_position_witnesses")
        if not isinstance(coords, list) or len(coords) < 3:
            raise AdmissionError("Read-only real-guest P1/P2 WRAM witnesses absent")
        if not any(max(int(v.get("raw_abs_x_difference",0)),
                           int(v.get("raw_abs_y_difference",0))) >= 32 for v in coords):
            raise AdmissionError("No guest-coordinate evidence of source player separation")
        parsed.append({"route":name,"source":entry["movie"],"sha256":entry["sha256"],
                       "observed_feature":feature,"first_source_ordinal":first,
                       "source_frame_count":count,
                       "first_guest_frame":span[0]+first,
                       "last_guest_frame":span[0]+first+count-1,
                       "observation":item["observation"]})
        features.add(feature)
        used.add(name)
    if features != FEATURES:
        raise AdmissionError("Required genuine hill, loop and ramp trio incomplete")
    return parsed

def probe_frames(video: Path) -> tuple[int, int, int]:
    streams = json.loads(subprocess.check_output([
        "ffprobe","-v","error","-count_frames","-select_streams","v:0",
        "-show_entries","stream=width,height,r_frame_rate,nb_read_frames",
        "-of","json",str(video)]))["streams"]
    if len(streams) != 1:
        raise AdmissionError("One source video stream required")
    s = streams[0]
    if s["r_frame_rate"] != "60/1":
        raise AdmissionError("Source cadence changed")
    return int(s["width"]),int(s["height"]),int(s["nb_read_frames"])

def render(ledger_path: Path, review_path: Path, output_path: Path):
    ledger = json.loads(ledger_path.read_text())
    review = json.loads(review_path.read_text())
    shots = accepted_shots(ledger,review)
    for item in shots:
        src = ledger_path.parent / item["source"]
        if not src.is_file() or sha256_file(src) != item["sha256"]:
            raise AdmissionError(f"Unavailable/mismatched native source: {src}")
        if probe_frames(src) != (1920,1080,900):
            raise AdmissionError("Unexpected source raster or frame count")
    if output_path.exists():
        raise AdmissionError("Refusing to overwrite a prior acceptance candidate")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ur-actual-topology-") as temp:
        work = Path(temp)
        for i,shot in enumerate(shots):
            src=ledger_path.parent / shot["source"]
            part=work / f"shot-{i:02d}.mp4"
            start=shot["first_source_ordinal"]
            count=shot["source_frame_count"]
            filt=f"trim=start_frame={start}:end_frame={start+count},setpts=PTS-STARTPTS,format=yuv420p"
            subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                "-y","-i",str(src),"-vf",filt,"-an","-frames:v",str(count),
                "-r","60","-c:v","libx264","-preset","veryfast","-crf","17",
                "-pix_fmt","yuv420p",str(part)],check=True)
            if probe_frames(part)!=(1920,1080,count):
                raise AdmissionError(f"Shot {i} loses/repeats frame count")
        sources=[work/f"shot-{i:02d}.mp4" for i in range(len(shots))]
        concat=work/"shots.txt"
        concat.write_text("".join(f"file '{src}'\n" for src in sources))
        target=work/"genuine-topology.mp4"
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-y","-safe","0","-f","concat","-i",str(concat),
            "-an","-c:v","libx264","-preset","veryfast","-crf","17",
            "-movflags","+faststart",str(target)],check=True)
        expected=sum(s["source_frame_count"] for s in shots)
        if probe_frames(target)!=(1920,1080,expected):
            raise AdmissionError("Joined film frame count is not exact")
        target.replace(output_path)
    manifest={
        "schema":"UR-ACCEPTED-SOURCE-TOPOLOGY-REEL/1",
        "review_sha256":sha256_file(review_path),
        "source_manifest_sha256":sha256_file(ledger_path),
        "output_sha256":sha256_file(output_path),
        "source_frame_count":sum(s["source_frame_count"] for s in shots),
        "frame_rate":"60/1",
        "provenance":"genuine continuous guest-source frames within each distinct shot",
        "editing":"visible hard cuts across unrelated independently played sessions",
        "no_interpolation":True,
        "source_gameplay_changed":False,
        "editorial_topology_overlay_added":False,
        "shots":shots,
        "approved_by":review["reviewer"],
        "approved_method":review["review_method"],
    }
    output_path.with_suffix(".provenance.json").write_text(
        json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger",type=Path,required=True)
    ap.add_argument("--review",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    shots=accepted_shots(json.loads(a.ledger.read_text()),
                         json.loads(a.review.read_text()))
    if not a.out:
        print(json.dumps({"status":"visual_evidence_manifest_valid",
                          "shots":shots},indent=2))
        return
    record=render(a.ledger,a.review,a.out)
    print(json.dumps({"status":"source_verified_true_track_topology_reel",
                      "sha256":record["output_sha256"],
                      "frames":record["source_frame_count"]},indent=2))

if __name__=="__main__":
    main()
