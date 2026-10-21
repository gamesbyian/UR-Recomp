#!/usr/bin/env python3
"""Independent, ROM-free QA08 correlation audit of 11 sampled source frames.

A cyclic palette transition at eight sample pixels is NOT source-epoch
original/native equivalence, whole-frame P7 noninterference, or release credit.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile

ARCHIVE_SHA = "10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2"
POINTS = {(53,41),(65,52),(70,58),(84,77),(175,145),(187,160),(190,161),(202,182)}
PALETTES = {
    5176: ("4210","56b5","4a52","4631"),
    **{f: ("56b5","4a52","4631","4210") for f in range(5177,5184)},
    **{f: ("4a52","4631","4210","56b5") for f in range(5184,5187)},
}


def parse_rows(rows):
    observations = defaultdict(dict)
    counts = Counter()
    for line in rows:
        fields = line.split()
        if len(fields) < 5:
            raise ValueError("short source row")
        kind = fields[0]
        if kind not in ("UR_QA08_LATE_PPU_SOURCE", "UR_QA08_LATE_PPU_FINAL"):
            raise ValueError("wrong source kind")
        kv = {}
        for token in fields[1:]:
            if "=" not in token:
                raise ValueError("invalid field")
            k, v = token.split("=", 1)
            if k in kv:
                raise ValueError("duplicate field")
            kv[k] = v
        frame = int(kv["frame"])
        xy = int(kv["x"]), int(kv["logical_y"])
        if frame not in PALETTES or xy not in POINTS or int(kv["ppu_line"]) != xy[1] + 1:
            raise ValueError("unexpected frame or coordinate")
        sub = kv["sub"] if kind == "UR_QA08_LATE_PPU_SOURCE" else "final"
        if kind == "UR_QA08_LATE_PPU_SOURCE" and sub not in ("0", "1"):
            raise ValueError("source row cannot impersonate final stage")
        if kind == "UR_QA08_LATE_PPU_FINAL" and "sub" in kv:
            raise ValueError("final row cannot carry source sub stage")
        key = xy, sub
        if key in observations[frame]:
            raise ValueError("duplicate stage")
        observations[frame][key] = kv
        counts[sub] += 1
    if len(rows) != 264 or counts != Counter({"0":88,"1":88,"final":88}):
        raise ValueError("incomplete sample cardinality")

    snapshots, changes = {}, {}
    for frame in PALETTES:
        sample = observations[frame]
        if len(sample) != 24:
            raise ValueError("missing stage")
        snapshot = set()
        for xy in POINTS:
            main, sub, final = (sample[(xy, stage)] for stage in ("0", "1", "final"))
            if (main["directcolor"] != "0" or main["layer"] != "0"
                    or sub["sub"] != "1" or final["RGB8"].count(",") != 2):
                raise ValueError("wrong pixel stage")
            slot = int(main["index"], 16)
            if slot not in range(0x6c, 0x70):
                raise ValueError("main indexed palette outside four-slot window")
            selected, word = main["selected_rgb555"], main["cgram_index_word"]
            actual = main[f"cgram{slot:02x}"]
            if selected != word or selected != actual:
                raise ValueError("indexed CGRAM identity contradiction")
            snapshot.add(tuple(main["cgram" + s] for s in ("6c","6d","6e","6f")))
        if snapshot != {PALETTES[frame]}:
            raise ValueError("frame palette not source-matched")
        snapshots[frame] = next(iter(snapshot))

    for before, after in zip(range(5176, 5186), range(5177, 5187)):
        changed = sum(observations[before][(xy,"final")]["RGB8"] !=
                      observations[after][(xy,"final")]["RGB8"] for xy in POINTS)
        selected_changed = sum(observations[before][(xy,"0")]["selected_rgb555"] !=
                               observations[after][(xy,"0")]["selected_rgb555"] for xy in POINTS)
        changes[f"{before}->{after}"] = {
            "palette_rotated": snapshots[before] != snapshots[after],
            "selected_changed": selected_changed,
            "final_rgb_changed": changed,
        }
        if changed != selected_changed or changed not in (0, 8):
            raise ValueError("unexpected stage-transition association")
        if (snapshots[before] != snapshots[after]) != (changed == 8):
            raise ValueError("transition phase disagreement")
        if snapshots[before] != snapshots[after] and snapshots[after] != snapshots[before][1:] + snapshots[before][:1]:
            raise ValueError("not a one-slot cyclic palette rotation")
    boundaries = [int(k.split("->")[1]) for k,v in changes.items() if v["palette_rotated"]]
    if boundaries != [5177, 5184]:
        raise ValueError("unexpected palette phase boundaries")
    return {
        "schema": "qa08-independent-11-frame-palette-rotation/1",
        "source_rows": len(rows),
        "main_sub_final_triplets": 88,
        "frame_palettes": {str(k): list(v) for k,v in snapshots.items()},
        "frame_transitions": changes,
        "palette_rotation_boundaries": boundaries,
        "source_pixel_correlation_only": True,
        "same_epoch_original_native_proven": False,
        "whole_frame_P7_noninterference_proven": False,
        "release_gate_credit": 0,
    }


def audit(path: Path):
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != ARCHIVE_SHA:
        raise ValueError("immutable hosted archive SHA mismatch")
    with ZipFile(BytesIO(blob)) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        rows = z.read("on-source.log").decode("ascii").splitlines()
    result = parse_rows(rows)
    result["outer_zip_sha256"] = ARCHIVE_SHA
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("archive", type=Path)
    args = p.parse_args()
    print(json.dumps(audit(args.archive), indent=2, sort_keys=True))
