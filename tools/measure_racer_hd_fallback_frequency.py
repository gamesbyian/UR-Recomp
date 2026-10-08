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

from summarize_racer_semantic_trace import (
    parse_trace,
    row_matches_registration,
    validate_registry_guard_scopes,
)


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
    validate_registry_guard_scopes(registry)
    entries_by_player = {
        player: [e for e in registry["entries"] if e["player"] == player]
        for player in ("p1", "p2")
    }

    unsupported: dict[str, dict[str, Any]] = {}
    fallback_by_primary = Counter()
    fallback_by_player_primary = Counter()
    fallback_by_player_visual = Counter()
    visual_frames: dict[tuple[str, str, str, int, str], set[int]] = defaultdict(set)
    supported = 0
    observations = 0
    pair_gate_counts = Counter()
    pair_unlock_counts = Counter()
    pair_unlock_frames: dict[tuple[str, str, str, int, str], set[int]] = defaultdict(set)

    for row in rows:
        key = state_key(row)
        selected_by_player: dict[str, bool] = {}
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
            selected_by_player[player] = bool(matches)
            if matches:
                supported += 1
                continue

            fallback_by_primary[semantic] += 1
            fallback_by_player_primary[(player, semantic)] += 1
            visual_key = (
                player,
                semantic,
                row[f"{player}_companion"],
                row[f"{player}_selector"],
                row[f"{player}_gate"],
            )
            fallback_by_player_visual[visual_key] += 1
            visual_frames[visual_key].add(row["frame"])
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

        selected_count = sum(selected_by_player.values())
        pair_gate_counts[selected_count] += 1
        if selected_count == 1:
            # The shipping presenter currently activates only when *both*
            # selectors resolve. A new player-local family can release this
            # two-player gate only if the opposite racer is already supported.
            missing = "p1" if not selected_by_player["p1"] else "p2"
            visual_key = (
                missing,
                row[f"{missing}_primary"],
                row[f"{missing}_companion"],
                row[f"{missing}_selector"],
                row[f"{missing}_gate"],
            )
            pair_unlock_counts[visual_key] += 1
            pair_unlock_frames[visual_key].add(row["frame"])

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
        "host_presenter_pair_gate": {
            "rule": (
                "Live racer_hd_begin_sim_frame requires both player selectors "
                "and both assets before it captures the four OAM slots. "
                "These numbers are registration-only upper bounds; live "
                "placement, capture success and asset availability can "
                "further reduce actual HD draws."
            ),
            "frames_with_both_players_selected": pair_gate_counts[2],
            "frames_with_exactly_one_player_selected": pair_gate_counts[1],
            "frames_with_neither_player_selected": pair_gate_counts[0],
            "pair_gate_eligible_player_frames_upper_bound": pair_gate_counts[2] * 2,
            "selected_but_pair_blocked_player_frames": pair_gate_counts[1],
            "pair_gate_eligible_fraction_upper_bound": (
                2 * pair_gate_counts[2] / observations if observations else 0.0
            ),
        },
        "potential_pair_gate_unlock_by_player_local_family": [
            {
                "player": player,
                "semantic_frame_id": semantic,
                "companion": companion,
                "selector": selector,
                "gate": gate,
                "frames_with_supported_opponent": count,
                "potential_pair_gate_player_frame_gain_upper_bound": count * 2,
                "episode_count": episode_count(sorted(pair_unlock_frames[key])),
                "frames": sorted(pair_unlock_frames[key]),
            }
            for key, count in sorted(
                pair_unlock_counts.items(),
                key=lambda item: (
                    -item[1],
                    -episode_count(sorted(pair_unlock_frames[item[0]])),
                    item[0],
                ),
            )
            for player, semantic, companion, selector, gate in [key]
        ],
        "pair_gate_unlock_caveat": (
            "A local-family proposal can unlock two rendered player-frames "
            "only when the opposite registration is already selected; "
            "these counts are not an assertion of stock-pose equivalence, "
            "authored-art approval, OAM placement or native draw success."
        ),
        "unsupported_exact_states_ranked": ranked,
        "fallback_by_primary_semantic_id": [
            {"semantic_frame_id": semantic, "player_frames": count}
            for semantic, count in sorted(
                fallback_by_primary.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "fallback_by_player_primary_semantic_id": [
            {
                "player": player,
                "semantic_frame_id": semantic,
                "player_frames": count,
            }
            for (player, semantic), count in sorted(
                fallback_by_player_primary.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
        ],
        "fallback_by_player_visual_context": [
            {
                "player": player,
                "semantic_frame_id": semantic,
                "companion": companion,
                "selector": selector,
                "gate": gate,
                "player_frames": count,
                "frame_hits": len(visual_frames[(player, semantic, companion, selector, gate)]),
                "episode_count": episode_count(
                    sorted(visual_frames[(player, semantic, companion, selector, gate)])
                ),
                "frames": sorted(
                    visual_frames[(player, semantic, companion, selector, gate)]
                ),
            }
            for (player, semantic, companion, selector, gate), count in sorted(
                fallback_by_player_visual.items(),
                key=lambda item: (
                    -item[1],
                    -episode_count(sorted(visual_frames[item[0]])),
                    -len(visual_frames[item[0]]),
                    item[0],
                ),
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
