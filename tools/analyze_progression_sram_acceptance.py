#!/usr/bin/env python3
"""Validate gameplay-authored Uniracers progression against the canonical model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def offset(spec: str) -> int:
    return int(spec.split(":", 1)[1].split("..", 1)[0], 16)


def range_offsets(spec: str) -> tuple[int, int]:
    bankless = spec.split(":", 1)[1]
    start_s, end_s = bankless.split("..", 1)
    return int(start_s, 16), int(end_s, 16) + 1


def region_changes(a: bytes, b: bytes, start: int, end: int):
    return [
        {"offset": i, "before": a[i], "after": b[i]}
        for i in range(start, end)
        if a[i] != b[i]
    ]


def layout(model: dict) -> dict:
    medals = model["medal_matrix"]
    medal_start = offset(medals["base"])
    medal_end = medal_start + medals["rows"] * medals["row_stride"]
    tier_a_start, tier_a_end = range_offsets(model["derived_tiers"]["primary_table"])
    tier_b_start, tier_b_end = range_offsets(model["derived_tiers"]["mirror_table"])
    checksum_start, checksum_end = range_offsets(model["checksum"]["protected_region"])
    return {
        "medal_start": medal_start,
        "medal_end": medal_end,
        "tier_a_start": tier_a_start,
        "tier_a_end": tier_a_end,
        "tier_b_start": tier_b_start,
        "tier_b_end": tier_b_end,
        "checksum_start": checksum_start,
        "checksum_end": checksum_end,
        "checksum_words": model["checksum"]["word_count"],
        "checksum_addr": offset(model["checksum"]["stored_at"]),
    }


def checksum(data: bytes, model: dict) -> int:
    l = layout(model)
    words = l["checksum_words"]
    start = l["checksum_start"]
    assert l["checksum_end"] - start == words * 2
    return sum(
        int.from_bytes(data[start + i * 2:start + i * 2 + 2], "little")
        for i in range(words)
    ) & 0xFFFF


def medal_coordinates(model: dict, absolute_offset: int) -> tuple[int, int]:
    l = layout(model)
    rel = absolute_offset - l["medal_start"]
    stride = model["medal_matrix"]["row_stride"]
    return rel // stride, rel % stride


def predict_tier(model: dict, sram: bytes, rider_column: int) -> int:
    l = layout(model)
    medals = model["medal_matrix"]
    stride = medals["row_stride"]
    values = [
        sram[l["medal_start"] + row * stride + rider_column]
        for row in model["derived_tiers"]["prerequisite_rows"]
    ]
    tier = 0
    for threshold in sorted(model["derived_tiers"]["thresholds"], key=lambda x: x["tier"]):
        rule = threshold["machine_rule"]
        matched = False
        if rule["kind"] == "count_at_least":
            matched = sum(v >= rule["medal_value_gte"] for v in values) >= rule["count_gte"]
        elif rule["kind"] == "sum_equals":
            matched = sum(values) == rule["sum_equals"]
        else:
            raise ValueError(f"unsupported tier rule {rule['kind']}")
        if matched:
            tier = threshold["tier"]
    return tier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--reload", type=Path, required=True)
    ap.add_argument("--model", type=Path, default=Path("analysis/data/progression-model.json"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--require-medal", action="store_true")
    args = ap.parse_args()

    model = json.loads(args.model.read_text(encoding="utf-8"))
    l = layout(model)
    before = args.before.read_bytes()
    after = args.after.read_bytes()
    reload = args.reload.read_bytes()
    for name, data in [("before", before), ("after", after), ("reload", reload)]:
        if len(data) != 8192:
            raise SystemExit(f"{name}: expected 8192 bytes, got {len(data)}")

    medals = region_changes(before, after, l["medal_start"], l["medal_end"])
    tier_a = region_changes(before, after, l["tier_a_start"], l["tier_a_end"])
    tier_b = region_changes(before, after, l["tier_b_start"], l["tier_b_end"])
    protected = region_changes(before, after, l["checksum_start"], l["checksum_end"])
    all_changes = region_changes(before, after, 0, len(before))

    update = model["medal_matrix"]["update_rule_machine"]
    awards = []
    for c in medals:
        row, rider = medal_coordinates(model, c["offset"])
        expected_after = min(update["maximum"], c["before"] + update["amount"])
        awards.append({
            **c,
            "tour_row": row,
            "tour": model["medal_matrix"]["row_order"][row],
            "rider_column": rider,
            "expected_after": expected_after,
            "matches_model_update": c["after"] == expected_after,
            "predicted_tier_before": predict_tier(model, before, rider),
            "predicted_tier_after": predict_tier(model, after, rider),
            "actual_primary_tier_after": after[l["tier_a_start"] + rider],
            "actual_mirror_tier_after": after[l["tier_b_start"] + rider],
        })

    medal_shape = bool(awards) and all(a["matches_model_update"] for a in awards)
    tier_predictions_match = all(
        a["actual_primary_tier_after"] == a["predicted_tier_after"]
        and a["actual_mirror_tier_after"] == a["predicted_tier_after"]
        for a in awards
    )

    stored_before = int.from_bytes(before[l["checksum_addr"]:l["checksum_addr"] + 2], "little")
    stored_after = int.from_bytes(after[l["checksum_addr"]:l["checksum_addr"] + 2], "little")
    stored_reload = int.from_bytes(reload[l["checksum_addr"]:l["checksum_addr"] + 2], "little")

    report = {
        "schema_version": 2,
        "oracle": args.model.as_posix(),
        "changed_byte_count": len(all_changes),
        "protected_region_changes": protected,
        "medal_changes": medals,
        "awards": awards,
        "tier_primary_changes": tier_a,
        "tier_mirror_changes": tier_b,
        "checksum": {
            "before_stored": stored_before,
            "before_computed": checksum(before, model),
            "after_stored": stored_after,
            "after_computed": checksum(after, model),
            "reload_stored": stored_reload,
            "reload_computed": checksum(reload, model),
        },
        "observations": {
            "game_authored_medal_change_observed": bool(medals),
            "medal_changes_match_model_update": medal_shape,
            "tier_predictions_match_model": tier_predictions_match,
            "tier_change_observed": bool(tier_a or tier_b),
        },
        "checks": {
            "game_authored_sram_change_observed": bool(all_changes),
            "checksum_protected_change_observed": bool(protected),
            "after_checksum_valid": stored_after == checksum(after, model),
            "reload_checksum_valid": stored_reload == checksum(reload, model),
            "full_sram_survives_reload": after == reload,
            "checksum_survives_reload": stored_after == stored_reload,
            "model_tier_prediction_matches": tier_predictions_match,
        },
        "scope_note": (
            "Synthetic SRAM may be used only as a pre-run setup. Every medal/tier change "
            "reported here is measured between the pre-gameplay baseline and the game-authored "
            "post-accomplishment SRAM."
        ),
    }
    if args.require_medal:
        report["checks"]["required_medal_change_observed"] = bool(medals)
        report["checks"]["single_medal_cell_changed"] = len(medals) == 1
        report["checks"]["medal_change_matches_model"] = medal_shape

    report["all_checks_pass"] = all(report["checks"].values())
    payload = json.dumps(report, indent=2) + "\n"
    print(payload, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
