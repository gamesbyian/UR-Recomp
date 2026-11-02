#!/usr/bin/env python3
"""Validate an independently captured original-emulator frame witness.

This tool never fabricates capture, 1994 timing, or source-pose association.
Only genuinely captured consecutive emulator frame IDs count as live edges.
"""
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "UR-ART4K-LIVE-ORIGINAL-PPU-FRAME-WITNESS/1"
ROM_SHA = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def _sha(s):
    return type(s) is str and len(s) == 64 and all(c in "0123456789abcdef" for c in s)


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
        image = row.get("binary_alpha_file")
        if (not isinstance(image, str) or
                not image.startswith("frames/") or
                Path(image).is_absolute() or ".." in Path(image).parts):
            raise ValueError("unsafe or unverifiable source frame path")
        file = (root / image).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():
            raise ValueError("missing actual captured frame")
        raw = file.read_bytes()
        if (len(raw) != 4096 or any(v not in (0, 1) for v in raw)
                or not _sha(row.get("binary_alpha_sha256"))
                or hashlib.sha256(raw).hexdigest() != row["binary_alpha_sha256"]):
            raise ValueError("invalid or stale actual 64x64 PPU alpha pixels")
        oam = row.get("oam_sha256")
        if not _sha(oam):
            raise ValueError("missing observed PPU/OAM identity hash")
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
        if a.out.exists():
            raise FileExistsError("cannot overwrite prior live witness ledger")
        a.out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
