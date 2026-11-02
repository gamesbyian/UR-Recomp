#!/usr/bin/env python3
"""Validate an independently captured original-emulator frame witness.

This tool never fabricates capture, 1994 timing, or source-pose association.
Only genuinely captured consecutive emulator frame IDs count as live edges.
"""
import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .no_replace_report import publish_text_once
else:
    from no_replace_report import publish_text_once

SCHEMA = "UR-ART4K-LIVE-ORIGINAL-PPU-FRAME-WITNESS/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def _sha(s):
    return type(s) is str and len(s) == 64 and all(c in "0123456789abcdef" for c in s)


def _read_capture(root: Path, name, prefix, size, digest, binary=False):
    """Read a source-owned, unique regular file without accepting symlink aliases."""
    if (type(name) is not str or not name.startswith(prefix + "/")
            or Path(name).is_absolute() or ".." in Path(name).parts
            or not _sha(digest)):
        raise ValueError("unsafe or unverifiable " + prefix + " capture")
    path = root
    for component in Path(name).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError("symlink capture path is not independent evidence")
    resolved_root = root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(resolved_root) or not path.is_file():
        raise ValueError("missing actual " + prefix + " capture")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
        raise ValueError("capture changed while being read")
    if (len(raw) != size or (binary and any(v not in (0, 1) for v in raw))
            or hashlib.sha256(raw).hexdigest() != digest):
        raise ValueError("invalid or stale actual " + prefix + " capture bytes")
    return raw, (after.st_dev, after.st_ino)


def validate(manifest, root: Path):
    if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA
            or manifest.get("rom_sha256") != ROM_SHA
            or manifest.get("source_kind") != "live-original-emulator-PPU"
            or manifest.get("recorded_by_live_emulator") is not True
            or manifest.get("registry_sequence_reused_as_live_capture") is not False):
        raise ValueError("not declared independently captured original emulator evidence")
    producer = manifest.get("emulator")
    if (not isinstance(producer, dict) or not _sha(producer.get("executable_sha256"))
            or not _sha(producer.get("source_revision_sha256"))
            or not isinstance(producer.get("identity"), str)
            or not producer["identity"]):
        raise ValueError("missing pinned original emulator identity")
    frames = manifest.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("no live frame observations")
    seen, counts, edges, prev = set(), {"p1": 0, "p2": 0}, [], {}
    alpha_files, oam_files = set(), {}
    observations = []
    global_tick = global_replay = global_oam = None
    for row in frames:
        if not isinstance(row, dict):
            raise ValueError("malformed captured frame")
        tick, player = row.get("emulated_frame_index"), row.get("player")
        if (type(tick) is not int or tick < 0 or player not in counts
                or type(row.get("input_replay_frame_index")) is not int
                or row["input_replay_frame_index"] < 0):
            raise ValueError("unbound original frame or player")
        key = player, tick
        if key in seen:
            raise ValueError("duplicate captured player/frame")
        seen.add(key)
        replay = row["input_replay_frame_index"]
        image_raw, alpha_id = _read_capture(
            root, row.get("binary_alpha_file"), "frames", 4096,
            row.get("binary_alpha_sha256"), binary=True)
        if alpha_id in alpha_files:
            raise ValueError("reused physical alpha file cannot represent a new capture")
        alpha_files.add(alpha_id)
        oam_raw, oam_id = _read_capture(
            root, row.get("oam_binary_file"), "oam", 544,
            row.get("oam_sha256"))
        if oam_id in oam_files and oam_files[oam_id] != tick:
            raise ValueError("reused physical OAM file across distinct emulator frames")
        oam_files[oam_id] = tick
        if global_tick is not None:
            if tick < global_tick or (tick == global_tick and
                                     (replay != global_replay or oam_raw != global_oam)):
                raise ValueError("contradictory interleaved emulator/OAM frame chronology")
            if tick > global_tick and replay <= global_replay:
                raise ValueError("nonmonotonic global replay frame chronology")
        global_tick, global_replay, global_oam = tick, replay, oam_raw
        # Retain independently rehashable per-frame input identity in the
        # derived ledger; change/hold booleans alone collide across corpora.
        observations.append({
            "player": player,
            "emulated_frame_index": tick,
            "input_replay_frame_index": replay,
            "binary_alpha_file": row["binary_alpha_file"],
            "binary_alpha_sha256": row["binary_alpha_sha256"],
            "oam_binary_file": row["oam_binary_file"],
            "oam_sha256": row["oam_sha256"],
        })
        raw = image_raw
        prior = prev.get(player)
        if prior is not None:
            if tick <= prior[0] or row["input_replay_frame_index"] <= prior[1]:
                raise ValueError("nonmonotonic original emulator frame/replay timeline")
            if tick == prior[0] + 1 and row["input_replay_frame_index"] == prior[1] + 1:
                edges.append({"player": player, "from_emulated_frame": prior[0],
                              "to_emulated_frame": tick,
                              "original_binary_silhouette_changed": prior[2] != raw})
        prev[player] = tick, row["input_replay_frame_index"], raw
        counts[player] += 1
    return {"schema": "UR-ART4K-VERIFIED-LIVE-PPU-TEMPORAL-LEDGER/1",
            "rom_sha256": ROM_SHA,
            "emulator": producer,
            "capture_observations": observations,
            "capture_producer_independently_authenticated": False,
            "captured_player_frame_counts": counts,
            "live_consecutive_edges": len(edges),
            "live_silhouette_change_edges": sum(x["original_binary_silhouette_changed"] for x in edges),
            "live_silhouette_hold_edges": sum(not x["original_binary_silhouette_changed"] for x in edges),
            "edges": edges,
            "registry_order_substituted": False,
            "1994_original_3d_joint_pose_recovered": False,
            "original_camera_recovered": False,
            "shipping_art_approved": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    a = parser.parse_args()
    data = validate(json.loads(a.manifest.read_text(encoding="utf-8")), a.manifest.parent)
    result = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if a.out:
        publish_text_once(a.out, result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
