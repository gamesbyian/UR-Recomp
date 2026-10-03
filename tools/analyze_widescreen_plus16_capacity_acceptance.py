#!/usr/bin/env python3
"""Acceptance for the course-backed host-owned +16/+24 Widescreen materializer."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ws_plus8", ROOT / "tools/analyze_native_widescreen_hook_acceptance.py"
)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(BASE)

PAYLOAD_RE = r"([0-9A-Fa-f]{64})"
PREP_RE = {
    16: re.compile(r"URWS_PREP16 camx=(\d+) edge=([0-9A-Fa-f]{4}) count=(\d+) payload=" + PAYLOAD_RE + r"(?: camy=(\d+))?"),
    24: re.compile(r"URWS_PREP24 camx=(\d+) edge=([0-9A-Fa-f]{4}) count=(\d+) payload=" + PAYLOAD_RE + r"(?: camy=(\d+))?"),
}
SHADOW_RE = {
    16: re.compile(
        r"URWS_SHADOW16 provider=course-runtime column=(\d+) camx=(\d+) "
        r"edge=([0-9A-Fa-f]{4}) count=(\d+) payload=" + PAYLOAD_RE +
        r" camy=(\d+) finex=(\d+) finey=(\d+) edgey=([0-9A-Fa-f]{4}) county=(\d+)"
    ),
    24: re.compile(
        r"URWS_SHADOW24 provider=course-runtime column=(\d+) camx=(\d+) "
        r"edge=([0-9A-Fa-f]{4}) count=(\d+) payload=" + PAYLOAD_RE +
        r" camy=(\d+) finex=(\d+) finey=(\d+) edgey=([0-9A-Fa-f]{4}) county=(\d+)"
    ),
}
PRIMARY_VIEW_RE = re.compile(
    r"URWS_PRIMARY margin=(\d+) camx=(\d+) edge=([0-9A-Fa-f]{4}) count=(\d+) "
    r"payload=" + PAYLOAD_RE + r" camy=(\d+) edgey=([0-9A-Fa-f]{4}) county=(\d+)"
)
STOP_RE = re.compile(r"URWS_STOP margin=(16|24) column=(\d+) reason=([^\s]+)")
CLEAN_RE = {
    16: re.compile(r"URWS_CLEANUP16 shadows=(\d+)"),
    24: re.compile(r"URWS_CLEANUP24 shadows=(\d+)"),
}


def effective_fine_y(camy: int, edgey: int, county: int) -> int:
    approx = (camy + 4) >> 4
    if edgey == 0xFFFF or county == 0:
        return approx
    phase = ((edgey & 0x1F) + 2) & 0x1F
    candidate = (approx & ~0x1F) | phase
    while candidate - approx > 16:
        candidate -= 32
    while approx - candidate > 16:
        candidate += 32
    return candidate


def prep_rows(margin: int, text: str) -> list[dict]:
    out = []
    for c, e, n, p, y in PREP_RE[margin].findall(text):
        row = {"camx": int(c), "edge": int(e, 16), "count": int(n), "payload": p.upper()}
        if y:
            row["camy"] = int(y)
        out.append(row)
    return out


def shadow_rows(margin: int, text: str) -> list[dict]:
    out = []
    for col, c, e, n, p, y, fx, fy, ey, cy in SHADOW_RE[margin].findall(text):
        out.append({
            "column": int(col), "camx": int(c), "edge": int(e, 16),
            "count": int(n), "payload": p.upper(), "camy": int(y),
            "finex": int(fx), "finey": int(fy), "edgey": int(ey, 16),
            "county": int(cy),
        })
    return out


def primary_rows(text: str, margin: int) -> list[dict]:
    out = []
    for mm, c, e, n, p, y, ey, cy in PRIMARY_VIEW_RE.findall(text):
        if int(mm) != margin or int(n) != 16 or int(e, 16) == 0xFFFF:
            continue
        camy = int(y)
        edgey = int(ey, 16)
        county = int(cy)
        out.append({
            "camx": int(c), "edge": int(e, 16), "count": int(n),
            "payload": p.upper(), "camy": camy, "edgey": edgey,
            "county": county, "finey": effective_fine_y(camy, edgey, county),
        })
    return out


def _oracle_classify(shadow: dict, oracle: list[dict]) -> tuple[str, dict | None]:
    wanted_ring = shadow["edge"] & 0x1F
    bounded = [
        r for r in oracle
        if r["camx"] > shadow["camx"]
        and 1 <= r["camx"] - shadow["camx"] <= 96
        and (r["edge"] & 0x1F) == wanted_ring
    ]
    if not bounded:
        return "unmatched", None
    same_view = [r for r in bounded if r["finey"] == shadow["finey"]]
    if not same_view:
        return "vertical-view-transition", min(bounded, key=lambda r: r["camx"] - shadow["camx"])
    return "same-view", min(same_view, key=lambda r: r["camx"] - shadow["camx"])


def analyze_margin(margin: int, log: str, p8: list[dict], oracle: list[dict],
                   control: list[dict], state0: dict, state: dict) -> dict:
    expected_host_columns = margin // 8 - 1
    expected_columns = list(range(2, 2 + expected_host_columns))
    prep = prep_rows(margin, log)
    shadows = shadow_rows(margin, log)
    primary = primary_rows(log, margin)

    p8_sig = [(r["camx"], r["edge"], r["count"], r["payload"]) for r in p8]
    prep_sig = [(r["camx"], r["edge"], r["count"], r["payload"]) for r in prep]
    stock_deltas = {
        (b["edge"] - a["edge"]) & 0xFFFF for a, b in zip(control, control[1:])
    } | {1}

    primary_by_cam = {r["camx"]: r for r in primary}
    shadow_by_key = {(r["camx"], r["column"]): r for r in shadows}
    chain_failures = []
    missing_columns = []
    pairs = []

    for first in prep:
        base = primary_by_cam.get(first["camx"])
        if base is None:
            missing_columns.append({"camx": first["camx"], "missing": "primary"})
            continue
        d1 = (first["edge"] - base["edge"]) & 0xFFFF
        first_ok = BASE._ring_adjacent(base["edge"], first["edge"]) and d1 in stock_deltas
        previous = first
        item = {
            "camx": first["camx"],
            "primary_edge": base["edge"],
            "guest_edge": first["edge"],
            "guest_stock_compatible": first_ok,
            "hosts": [],
        }
        if not first_ok:
            chain_failures.append({"camx": first["camx"], "column": 1, "reason": "guest-step"})
        for col in expected_columns:
            host = shadow_by_key.get((first["camx"], col))
            if host is None:
                missing_columns.append({"camx": first["camx"], "missing": col})
                continue
            adjacent = BASE._ring_adjacent(previous["edge"], host["edge"])
            item["hosts"].append({
                "column": col, "edge": host["edge"],
                "delta": (host["edge"] - previous["edge"]) & 0xFFFF,
                "ring_adjacent": adjacent,
            })
            if not adjacent:
                chain_failures.append({"camx": first["camx"], "column": col, "reason": "ring-step"})
            previous = host
        pairs.append(item)

    classifications = {"same-view": 0, "vertical-view-transition": 0, "unmatched": 0}
    exact_same_view = 0
    payload_failures = []
    oracle_examples = []
    for row in shadows:
        cls, stock = _oracle_classify(row, oracle)
        classifications[cls] += 1
        if stock is None:
            payload_failures.append({"shadow": row, "reason": "no-bounded-stock-oracle"})
            continue
        if len(oracle_examples) < 40:
            oracle_examples.append({
                "column": row["column"], "host_camx": row["camx"],
                "host_edge": row["edge"], "host_finey": row["finey"],
                "classification": cls, "stock_camx": stock["camx"],
                "stock_edge": stock["edge"], "stock_finey": stock["finey"],
                "payload_exact": row["payload"] == stock["payload"],
            })
        if cls == "same-view":
            if row["payload"] == stock["payload"]:
                exact_same_view += 1
            elif len(payload_failures) < 40:
                payload_failures.append({
                    "shadow": row, "stock": stock, "reason": "same-view-payload-divergence"
                })

    clean = [int(x) for x in CLEAN_RE[margin].findall(log)]
    terminal_pending = len(prep) == len(clean) + 1
    cleanup_ok = (
        len(prep) > 0
        and (len(prep) == len(clean) or terminal_pending)
        and all(x == expected_host_columns for x in clean)
    )
    stops = [
        {"margin": int(m), "column": int(c), "reason": reason}
        for m, c, reason in STOP_RE.findall(log) if int(m) == margin
    ]
    protected = {
        k: {"control": state0[k], f"margin_{margin}": state[k]}
        for k in state0 if state0[k] != state[k]
    }
    expected_shadow_rows = len(prep) * expected_host_columns

    checks = {
        f"margin{margin}_guest_column_exactly_matches_plus8_path": prep_sig == p8_sig,
        f"margin{margin}_all_host_columns_materialized": (
            len(prep) > 0 and len(shadows) == expected_shadow_rows and not missing_columns
        ),
        f"margin{margin}_no_provider_miss": not stops,
        f"margin{margin}_all_counts_16": all(r["count"] == 16 for r in prep + shadows),
        f"margin{margin}_ring_chain_adjacent": len(pairs) == len(prep) and not chain_failures,
        f"margin{margin}_same_view_payloads_exact": (
            classifications["same-view"] > 0
            and exact_same_view == classifications["same-view"]
            and classifications["unmatched"] == 0
            and not payload_failures
        ),
        f"margin{margin}_all_oracle_rows_classified": (
            sum(classifications.values()) == len(shadows)
            and classifications["unmatched"] == 0
        ),
        f"margin{margin}_cleanup_lifecycle": cleanup_ok,
        f"margin{margin}_protected_state_equal": not protected,
    }
    return {
        "margin": margin,
        "expected_host_columns": expected_host_columns,
        "expected_columns": expected_columns,
        "counts": {
            "guest_prepare_events": len(prep),
            "host_shadow_events": len(shadows),
            "same_view_comparable_rows": classifications["same-view"],
            "same_view_exact_payload_matches": exact_same_view,
            "vertical_view_transition_rows": classifications["vertical-view-transition"],
            "unmatched_oracle_rows": classifications["unmatched"],
            "cleanup_events": len(clean),
        },
        "provider_misses": stops,
        "protected_state_differences": protected,
        "missing_columns": missing_columns[:40],
        "chain_failures": chain_failures[:40],
        "payload_failures": payload_failures[:40],
        "pair_examples": pairs[:40],
        "oracle_examples": oracle_examples[:40],
        "checks": checks,
        "accepted": all(checks.values()),
    }


def analyze(log0: str, log8: str, log16: str, log24: str, oracle_log: str,
            dump0: Path, dump8: Path, dump16: Path, dump24: Path) -> dict:
    fake16 = (
        "URWS_LIMIT margin=16 required_extra_columns=2 "
        "stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n"
    )
    fake24 = (
        "URWS_LIMIT margin=24 required_extra_columns=3 "
        "stock_extra_horizontal_lanes=1 first_constraint=secondary-lane-capacity\n"
    )
    plus8 = BASE.analyze(
        {0: log0, 8: log8, 16: fake16, 24: fake24},
        {0: dump0, 8: dump8, 16: dump0, 24: dump0},
    )
    p8 = [
        {"camx": int(c), "edge": int(e, 16), "count": int(n), "payload": p.upper()}
        for c, e, n, p in BASE.PREP_RE.findall(log8)
    ]
    control = primary_rows(log0, 0)
    oracle = primary_rows(oracle_log, 0)
    states = {
        0: BASE.read_words(dump0), 8: BASE.read_words(dump8),
        16: BASE.read_words(dump16), 24: BASE.read_words(dump24),
    }
    r16 = analyze_margin(16, log16, p8, oracle, control, states[0], states[16])
    r24 = analyze_margin(24, log24, p8, oracle, control, states[0], states[24])
    checks = {
        "accepted_plus8_unchanged": plus8["accepted"],
        "accepted_plus16_unchanged": r16["accepted"],
        "margin24_materializes_two_host_columns": r24["accepted"],
    }
    return {
        "schema_version": 2,
        "architecture": {
            "guest_first_extra_column": "accepted PR #228 secondary lane",
            "host_extra_columns": "columns +2 and beyond are host-owned presentation state",
            "host_provider": "live 7F:000F coarse table + 7F:800F packed-surface fine records",
            "acceptance_oracle": "independent later-stock control run only; never read by implementation",
            "synthetic_guest_descriptor_lanes": 0,
            "validated_host_materializer_depth": 2,
            "validated_margin_pixels": 24,
            "scaling_conclusion": (
                "The random-access provider generalizes from one to two host columns without "
                "additional guest lanes; +24 does not establish the final 16:9 capacity ceiling."
            ),
        },
        "plus16": r16,
        "plus24": r24,
        "checks": checks,
        "accepted": all(checks.values()),
    }


def render(r: dict) -> str:
    r16, r24 = r["plus16"], r["plus24"]
    c24, n24 = r24["checks"], r24["counts"]
    return "\n".join([
        "# +24 Widescreen host-capacity acceptance", "",
        "The accepted +8 guest path still supplies column +1. +16 retains one host-owned "
        "course-runtime column, and +24 now retains two host-owned columns (+2/+3) from the "
        "same live coarse/fine presentation tables. No additional guest $03xx lane is used.", "",
        f"- accepted +8 unchanged: **{r['checks']['accepted_plus8_unchanged']}**",
        f"- accepted +16 regression: **{r16['accepted']}**",
        f"- +24 guest preparation events: **{n24['guest_prepare_events']}**",
        f"- +24 host-shadow events: **{n24['host_shadow_events']}**",
        f"- same-view comparable host rows: **{n24['same_view_comparable_rows']}**",
        f"- same-view exact payload matches: **{n24['same_view_exact_payload_matches']}**",
        f"- vertical-view-transition rows: **{n24['vertical_view_transition_rows']}**",
        f"- unmatched oracle rows: **{n24['unmatched_oracle_rows']}**",
        f"- two host columns for every preparation: **{c24['margin24_all_host_columns_materialized']}**",
        f"- complete adjacent ring chain: **{c24['margin24_ring_chain_adjacent']}**",
        f"- +24 protected state equal: **{c24['margin24_protected_state_equal']}**",
        f"- deterministic cleanup: **{c24['margin24_cleanup_lifecycle']}**",
        f"- provider misses: **{r24['provider_misses']}**", "",
        "Rows whose independent future-stock oracle samples a different fine camera-Y viewport "
        "remain explicitly classified as vertical-view transitions. Same-view rows are a hard "
        "payload-exactness gate. The oracle is acceptance-only and is never consulted by the "
        "runtime materializer.", "",
        "Scaling result: two host-owned columns work through +24 using the same random-access "
        "course provider. This removes the previous one-shadow storage cap, but does not by "
        "itself prove the full final 16:9 width.", "",
        f"Overall accepted: **{r['accepted']}**", "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    for m in (0, 8, 16, 24):
        ap.add_argument(f"--log-{m}", type=Path, required=True)
        ap.add_argument(f"--dump-{m}", type=Path, required=True)
    ap.add_argument("--oracle-log", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    a = ap.parse_args()
    r = analyze(
        a.log_0.read_text(encoding="utf-8", errors="replace"),
        a.log_8.read_text(encoding="utf-8", errors="replace"),
        a.log_16.read_text(encoding="utf-8", errors="replace"),
        a.log_24.read_text(encoding="utf-8", errors="replace"),
        a.oracle_log.read_text(encoding="utf-8", errors="replace"),
        a.dump_0, a.dump_8, a.dump_16, a.dump_24,
    )
    md = render(r)
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    if a.md_out:
        a.md_out.parent.mkdir(parents=True, exist_ok=True)
        a.md_out.write_text(md, encoding="utf-8")
    print(md, end="")
    return 0 if r["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
