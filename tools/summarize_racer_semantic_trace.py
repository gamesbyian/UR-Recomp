#!/usr/bin/env python3
"""Summarize bounded native racer semantic traces.

The trace is sampled immediately after each guest frame from the same WRAM
composition snapshot consumed by the native replacement selector. It is
authoritative for host-frame semantic selection, not for raster-time sprite
identity inside the just-rendered frame.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

TRACE_RE = re.compile(
    r"UR_RACER_PRESENTATION_TRACE frame=(?P<frame>\d+) "
    r"p1_primary=(?P<p1>[0-9A-Fa-f]{4}) p2_primary=(?P<p2>[0-9A-Fa-f]{4}) "
    r"p1_companion=(?P<p1c>[0-9A-Fa-f]{4}) p2_companion=(?P<p2c>[0-9A-Fa-f]{4}) "
    r"p1_selector=(?P<p1s>[0-9A-Fa-f]{4}) p2_selector=(?P<p2s>[0-9A-Fa-f]{4}) "
    r"p1_gate=(?P<p1g>[0-9A-Fa-f]{4}) p2_gate=(?P<p2g>[0-9A-Fa-f]{4})"
)


def parse_trace(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = TRACE_RE.search(line)
        if not m:
            continue
        g = m.groupdict()
        rows.append({
            "frame": int(g["frame"]),
            "p1_primary": f"0x{g['p1'].upper()}",
            "p2_primary": f"0x{g['p2'].upper()}",
            "p1_companion": f"0x{g['p1c'].upper()}",
            "p2_companion": f"0x{g['p2c'].upper()}",
            "p1_selector": int(g["p1s"], 16),
            "p2_selector": int(g["p2s"], 16),
            "p1_gate": f"0x{g['p1g'].upper()}",
            "p2_gate": f"0x{g['p2g'].upper()}",
        })
    return rows


def runs_for(rows: list[dict], key: str) -> list[dict]:
    if not rows:
        return []
    out = []
    start = rows[0]["frame"]
    prev = rows[0]["frame"]
    value = rows[0][key]
    count = 1
    for row in rows[1:]:
        if row["frame"] != prev + 1 or row[key] != value:
            out.append({
                "start_frame": start,
                "end_frame": prev,
                "frames": count,
                "semantic_frame_id": value,
            })
            start = row["frame"]
            value = row[key]
            count = 1
        else:
            count += 1
        prev = row["frame"]
    out.append({
        "start_frame": start,
        "end_frame": prev,
        "frames": count,
        "semantic_frame_id": value,
    })
    return out


def transition_counts(rows: list[dict], key: str) -> list[dict]:
    counts = Counter()
    for a, b in zip(rows, rows[1:]):
        if b["frame"] != a["frame"] + 1:
            continue
        counts[(a[key], b[key])] += 1
    return [
        {"from": a, "to": b, "count": n}
        for (a, b), n in sorted(counts.items())
    ]


def normalized_guard(value):
    if isinstance(value, str) and value.lower().startswith("0x"):
        return f"0x{int(value, 16):04X}"
    return value


def validate_registration_guard_scope(entry: dict) -> None:
    representation_id = entry.get("representation_id", "<unknown>")
    registration = entry.get("registration")
    nested_scope = registration.get("guard_scope") if isinstance(registration, dict) else None
    if nested_scope is not None:
        raise ValueError(
            f"{representation_id}: guard_scope must be representation-level; "
            "registration.guard_scope is invalid"
        )

    scope = entry.get("guard_scope")
    if scope not in (None, "player_local"):
        raise ValueError(
            f"{representation_id}: unsupported guard_scope {scope!r}; "
            "expected omitted/exact or 'player_local'"
        )

    proof = registration.get("guard_scope_proof") if isinstance(registration, dict) else None
    if scope != "player_local":
        if proof is not None:
            raise ValueError(
                f"{representation_id}: guard_scope_proof requires "
                "representation-level guard_scope='player_local'"
            )
        return

    player = entry.get("player")
    if player not in ("p1", "p2"):
        raise ValueError(
            f"{representation_id}: player_local guard requires player p1 or p2"
        )
    guards = entry.get("composition_guards")
    if not isinstance(guards, dict):
        raise ValueError(
            f"{representation_id}: player_local guard requires composition_guards"
        )
    required = (
        f"{player}_primary",
        f"{player}_companion",
        f"{player}_selector",
        f"{player}_companion_gate_word",
    )
    missing = [key for key in required if key not in guards]
    if missing:
        raise ValueError(
            f"{representation_id}: player_local guard is missing local keys: "
            + ", ".join(missing)
        )
    if not isinstance(proof, dict) or proof.get("scope") != "player_local":
        raise ValueError(
            f"{representation_id}: player_local guard requires matching "
            "registration.guard_scope_proof"
        )
    for field in ("structural_basis", "empirical_basis"):
        value = proof.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{representation_id}: guard_scope_proof lacks {field}"
            )
    for field in ("workflow_run", "artifact_id"):
        value = proof.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(
                f"{representation_id}: guard_scope_proof lacks positive {field}"
            )


def validate_registry_guard_scopes(registry: dict) -> None:
    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Racer HD registry entries must be a list")
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Racer HD registry entries must be objects")
        validate_registration_guard_scope(entry)


def row_matches_registration(row: dict, entry: dict) -> bool:
    validate_registration_guard_scope(entry)
    guards = entry["composition_guards"]
    mapping = {
        "p1_primary": "p1_primary",
        "p2_primary": "p2_primary",
        "p1_companion": "p1_companion",
        "p2_companion": "p2_companion",
        "p1_selector": "p1_selector",
        "p2_selector": "p2_selector",
        "p1_companion_gate_word": "p1_gate",
        "p2_companion_gate_word": "p2_gate",
    }
    if entry.get("guard_scope") == "player_local":
        player = entry["player"]
        keys = (
            f"{player}_primary",
            f"{player}_companion",
            f"{player}_selector",
            f"{player}_companion_gate_word",
        )
    else:
        keys = tuple(mapping)
    return all(
        normalized_guard(guards[key]) == normalized_guard(row[mapping[key]])
        for key in keys
    )


def registered_state_neighborhoods(rows: list[dict], registry: dict) -> list[dict]:
    out = []
    for entry in registry["entries"]:
        player = entry["player"]
        key = f"{player}_primary"
        hit_frames = []
        before = Counter()
        after = Counter()
        for i, row in enumerate(rows):
            if not row_matches_registration(row, entry):
                continue
            hit_frames.append(row["frame"])
            if i > 0 and rows[i - 1]["frame"] == row["frame"] - 1:
                before[rows[i - 1][key]] += 1
            if i + 1 < len(rows) and rows[i + 1]["frame"] == row["frame"] + 1:
                after[rows[i + 1][key]] += 1
        out.append({
            "representation_id": entry["representation_id"],
            "player": player,
            "semantic_frame_id": entry["semantic_frame_id"],
            "hit_frames": hit_frames,
            "hit_count": len(hit_frames),
            "previous_primary_counts": dict(sorted(before.items())),
            "next_primary_counts": dict(sorted(after.items())),
        })
    return out



def registered_composition_coverage(rows: list[dict], registry: dict) -> dict:
    """Report frames where both racers resolve through exact composition guards."""
    entries_by_player = {
        player: [e for e in registry["entries"] if e["player"] == player]
        for player in ("p1", "p2")
    }
    frames = []
    for row in rows:
        matched = {}
        for player in ("p1", "p2"):
            semantic_key = f"{player}_primary"
            matches = [
                entry["representation_id"]
                for entry in entries_by_player[player]
                if entry["semantic_frame_id"] == row[semantic_key]
                and row_matches_registration(row, entry)
            ]
            if len(matches) > 1:
                raise ValueError(
                    f"ambiguous {player} registration at frame {row['frame']}: {matches}"
                )
            matched[player] = matches[0] if matches else None
        frames.append({
            "frame": row["frame"],
            "fully_registered": all(matched.values()),
            "p1_representation_id": matched["p1"],
            "p2_representation_id": matched["p2"],
        })

    runs = []
    start = None
    previous = None
    for item in frames:
        frame = item["frame"]
        if item["fully_registered"]:
            if start is None or previous is None or frame != previous + 1:
                if start is not None:
                    runs.append([start, previous])
                start = frame
            previous = frame
        elif start is not None:
            runs.append([start, previous])
            start = None
            previous = None
    if start is not None:
        runs.append([start, previous])

    return {
        "fully_registered_frames": [
            item["frame"] for item in frames if item["fully_registered"]
        ],
        "fully_registered_runs": runs,
        "frames": frames,
    }


def build_report(rows: list[dict], registry: dict | None = None) -> dict:
    if registry is not None:
        validate_registry_guard_scopes(registry)
    frames = [r["frame"] for r in rows]
    contiguous = bool(rows) and frames == list(range(frames[0], frames[-1] + 1))
    players = {}
    for player in ("p1", "p2"):
        key = f"{player}_primary"
        players[player] = {
            "unique_primary_ids": sorted({r[key] for r in rows}),
            "runs": runs_for(rows, key),
            "transitions": transition_counts(rows, key),
        }
    return {
        "schema_version": 1,
        "source_semantics": "post-guest-frame WRAM composition used by native replacement selection",
        "raster_identity_authority": False,
        "timing_note": (
            "This trace does not collapse the known WRAM-vs-renderer timing seam; "
            "use it only for host-frame semantic selection and adjacency."
        ),
        "frame_window": [frames[0], frames[-1]] if rows else None,
        "frames_observed": len(rows),
        "contiguous": contiguous,
        "players": players,
        "registered_state_neighborhoods": (
            registered_state_neighborhoods(rows, registry)
            if registry is not None else []
        ),
        "registered_composition_coverage": (
            registered_composition_coverage(rows, registry)
            if registry is not None else {
                "fully_registered_frames": [],
                "fully_registered_runs": [],
                "frames": [],
            }
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument(
        "--registry",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "analysis/data/racer-hd-replacement-prototype.json",
    )
    args = ap.parse_args()
    rows = parse_trace(args.log.read_text(encoding="utf-8", errors="replace"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    report = build_report(rows, registry)
    if not report["contiguous"]:
        raise SystemExit("dense racer semantic trace is missing frames")
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
