#!/usr/bin/env python3
"""Stage five exact, successful ART-4K pose exports for integration into an existing Pages tree."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

POSES = ("upright", "pedal", "wheelie", "stunt", "bank")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(base, pose):
    folder = base / pose
    last = json.loads((folder / "articulated_blockout_last_attempt.json").read_text())
    ptr = json.loads((folder / "articulated_blockout_current.json").read_text())
    if last.get("status") != "succeeded" or not last.get("current_output_usable"):
        raise ValueError(f"{pose}: last attempt not successful")
    if last["attempt_id"] != ptr["attempt_id"] or last["source_sha256"] != ptr["source_sha256"]:
        raise ValueError(f"{pose}: stale pointer or different source")
    if ptr.get("rig_pose") != pose:
        raise ValueError(f"{pose}: pose mismatch")
    out = {}
    for key in ("glb", "receipt"):
        relative = Path(ptr[key + "_path"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "attempts":
            raise ValueError(f"{pose}: invalid output path")
        path = folder / relative
        if not path.is_file() or digest(path) != ptr[key + "_sha256"]:
            raise ValueError(f"{pose}: {key} missing or digest mismatch")
        out[key] = path
    report = json.loads(out["receipt"].read_text())
    if (report.get("attempt_id") != ptr["attempt_id"] or
        report.get("source_sha256") != ptr["source_sha256"] or
        report.get("rig_pose") != pose or
        report.get("glb_sha256") != ptr["glb_sha256"] or
        report.get("original_character_likeness_approved") is not False or
        report.get("shipping_art_approved") is not False):
        raise ValueError(f"{pose}: receipt identity / approval mismatch")
    return ptr, out


def stage(exports, site, source_commit):
    if not source_commit or any(c not in "0123456789abcdef" for c in source_commit.lower()) or len(source_commit) != 40:
        raise ValueError("exact 40-character source commit required")
    verified = {pose: validate(exports, pose) for pose in POSES}
    sources = {v[0]["source_sha256"] for v in verified.values()}
    if len(sources) != 1:
        raise ValueError("poses built from different source files")
    target = site / "model-review"
    if target.exists():
        raise ValueError("target exists; stage into a fresh directory and integrate atomically")
    assets = target / "assets" / source_commit
    assets.mkdir(parents=True)
    pose_map = {}
    for pose, (pointer, outputs) in verified.items():
        filename = pose + "-" + pointer["glb_sha256"][:16] + ".glb"
        shutil.copyfile(outputs["glb"], assets / filename)
        if digest(assets / filename) != pointer["glb_sha256"]:
            raise ValueError(f"{pose}: staged asset digest mismatch")
        pose_map[pose] = {"url": f"assets/{source_commit}/{filename}", "sha256": pointer["glb_sha256"]}
    here = Path(__file__).resolve().parent
    shutil.copy2(here / "index.html", target / "index.html")
    manifest = {"schema": "ur-racer-model-review/1", "version": source_commit[:12],
                "source_commit": source_commit, "source_model_sha256": next(iter(sources)),
                "model_url": pose_map["upright"]["url"],
                "candidate_sha256": pose_map["upright"]["sha256"],
                "poses": pose_map, "likeness_approved": False,
                "source_sprite_pose_registration": False}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"staged": str(target), "source_commit": source_commit,
                      "pose_hashes": {p: v["sha256"] for p, v in pose_map.items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exports", required=True, type=Path,
                        help="directory with upright/pedal/wheelie/stunt/bank successful exports")
    parser.add_argument("--site", required=True, type=Path, help="empty staging Pages root")
    parser.add_argument("--source-commit", required=True, help="exact rig exporter source commit")
    args = parser.parse_args()
    stage(args.exports, args.site, args.source_commit)
