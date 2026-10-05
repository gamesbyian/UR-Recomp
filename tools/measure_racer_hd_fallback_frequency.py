#!/usr/bin/env python3
"""Measure player-visible Racer HD fallback frequency from a dense ordinary-play trace."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from summarize_racer_semantic_trace import parse_trace, row_matches_registration


def state_key(row: dict[str, Any]) -> str:
    return (
        f"{row['p1_primary']}/{row['p2_primary']} + "
        f"{row['p1_companion']}/{row['p2_companion']} "
        f"sel {row['p1_selector']}/{row['p2_selector']} "
        f"gate {row['p1_gate']}/{row['p2_gate']}"
    )


def episode_count(frames: list[int]) -> int:
    count = 0
    previous = None
    for frame in sorted(frames):
        if previous is None or frame != previous + 1:
            count += 1
        previous = frame
    return count


def build_report(
    rows: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entries_by_player = {
        player: [e for e in registry["entries"] if e["player"] == player]
        for player in ("p1", "p2")
    }

    unsupported: dict[str, dict[str, Any]] = {}
    fallback_by_primary = Counter()
    supported = 0
    observations = 0

    for row in rows:
        key = state_key(row)
        for player in ("p1", "p2"):
            observations += 1
            semantic = row[f"{player}_primary"]
            matches = [
                entry for entry in entries_by_player[player]
                if entry["semantic_frame_id"] == semantic
                and row_matches_registration(row, entry)
            ]
            if len(matches) > 1:
                raise ValueError(
                    f"ambiguous {player} registration at frame {row['frame']}: "
                    + ", ".join(e["representation_id"] for e in matches)
                )
            if matches:
                supported += 1
                continue

            fallback_by_primary[semantic] += 1
            item = unsupported.setdefault(key, {
                "state": key,
                "composition": {
                    "p1_primary": row["p1_primary"],
                    "p2_primary": row["p2_primary"],
                    "p1_companion": row["p1_companion"],
                    "p2_companion": row["p2_companion"],
                    "p1_selector": row["p1_selector"],
                    "p2_selector": row["p2_selector"],
                    "p1_gate": row["p1_gate"],
                    "p2_gate": row["p2_gate"],
                },
                "frames": set(),
                "player_frames": 0,
                "players": Counter(),
            })
            item["frames"].add(row["frame"])
            item["player_frames"] += 1
            item["players"][player] += 1

    ranked = []
    for item in unsupported.values():
        frames = sorted(item["frames"])
        ranked.append({
            "state": item["state"],
            "composition": item["composition"],
            "frame_hits": len(frames),
            "player_frames": item["player_frames"],
            "episode_count": episode_count(frames),
            "frames": frames,
            "player_fallback_frames": dict(sorted(item["players"].items())),
        })
    ranked.sort(
        key=lambda item: (
            -item["player_frames"],
            -item["episode_count"],
            -item["frame_hits"],
            item["state"],
        )
    )

    fallback = observations - supported
    return {
        "schema_version": 1,
        "source": source or {},
        "measurement": {
            "frames_observed": len(rows),
            "player_frame_observations": observations,
            "hd_selected_player_frames": supported,
            "original_fallback_player_frames": fallback,
            "hd_coverage_fraction": (supported / observations) if observations else 0.0,
            "fallback_fraction": (fallback / observations) if observations else 0.0,
        },
        "unsupported_exact_states_ranked": ranked,
        "fallback_by_primary_semantic_id": [
            {"semantic_frame_id": semantic, "player_frames": count}
            for semantic, count in sorted(
                fallback_by_primary.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "ranking_rule": (
            "Rank exact synchronized states by fallback player-frames, then by "
            "independent episode count, then frame hits. This favors recurring "
            "player-visible burden over ROM/table adjacency."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--workflow-run", type=int)
    ap.add_argument("--artifact-id", type=int)
    args = ap.parse_args()

    rows = parse_trace(args.log.read_text(encoding="utf-8", errors="replace"))
    if not rows:
        raise SystemExit("no dense racer presentation trace rows found")
    report = build_report(
        rows,
        json.loads(args.registry.read_text(encoding="utf-8")),
        source={
            "kind": "ordinary-windows-native-racer-presentation-trace",
            "workflow_run": args.workflow_run,
            "artifact_id": args.artifact_id,
            "trace_window": [rows[0]["frame"], rows[-1]["frame"]],
        },
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
