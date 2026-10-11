#!/usr/bin/env python3
"""Report *structural-map* gaps in the pinned malmazuke PAL/USA evidence index.

A missing interval is NOT an unimplemented feature, unexecuted original code,
or an accepted USA gameplay discrepancy. Read-only, ROM-free, no new atlas.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:
    from tools.query_malmazuke_symbols import PIN, UPSTREAM, canonical_address, load_inputs
except ModuleNotFoundError:
    from query_malmazuke_symbols import PIN, UPSTREAM, canonical_address, load_inputs

STATUSES = ("not-covered", "structural-interval-candidate", "data-interval-only")
CLASS_ORDER = {"observed": 0, "inferred": 1, "not-labeled": 2, "unknown": 3, "data": 4}


def build_report(links: dict, labels: list[dict], *, domains: tuple[str, ...] = (),
                 limit: int = 30) -> dict:
    if limit < 1:
        raise ValueError("limit must be positive")
    if links.get("schema_version") != 1 or links.get("source", {}).get("commit") != PIN:
        raise ValueError("structural index does not match pinned malmazuke revision")
    entries = links["entries"]
    all_domains = {d for e in entries for d in e["domains"]}
    unknown = set(domains) - all_domains
    if unknown:
        raise ValueError("unknown indexed domain(s): " + ", ".join(sorted(unknown)))
    chosen = [e for e in entries if not domains or set(e["domains"]).intersection(domains)]
    label_by_address = {canonical_address(e["address"]): e for e in labels}
    statuses = Counter(e["correspondence"]["status"] for e in chosen)
    if set(statuses) - set(STATUSES):
        raise ValueError("unexpected structural mapping status")
    rows = {}
    for domain in sorted(all_domains if not domains else set(domains)):
        relevant = [e for e in chosen if domain in e["domains"]]
        counted = Counter(e["correspondence"]["status"] for e in relevant)
        rows[domain] = {"total": len(relevant), **{s: counted[s] for s in STATUSES}}
    unmapped = sorted(
        (e for e in chosen if e["correspondence"]["status"] == "not-covered"),
        key=lambda e: (CLASS_ORDER.get(e.get("pal_symbol_class"), 99), e["pal"]),
    )
    worklist = []
    for e in unmapped[:limit]:
        label = label_by_address.get(e["pal"], {})
        records = label.get("source_records", [])
        worklist.append({
            "pal": e["pal"],
            "domains": e["domains"],
            "pal_class": e["pal_symbol_class"],
            "native_symbols": e.get("mark_native", []),
            "source_records": records,
            "source_record_urls": [UPSTREAM + p for p in records],
            "usa_candidate": None,
            "status": "not-covered",
            "verified_usa_semantics": False,
        })
    return {
        "schema_version": 1,
        "kind": "malmazuke_structural_index_gap_report",
        "source_commit": PIN,
        "source_index": "analysis/data/malmazuke-pal-structural-links-20261010.json",
        "scope": {"domains": list(domains) if domains else sorted(all_domains)},
        "interpretation": "Unmapped means not covered by UR's selected bounded PAL/USA structural intervals, not an absent implementation, missing execution, failed event, or proven regional difference.",
        "counts": {"selected_unique_pal_addresses": len(chosen),
                   **{s: statuses[s] for s in STATUSES},
                   "not_covered_worklist_total": len(unmapped)},
        "by_domain": rows,
        "worklist": worklist,
        "worklist_truncated": len(unmapped) > limit,
        "sort": "PAL observed class first, then inferred/not-labeled/unknown/data, then ascending PAL address; no product-priority score",
        "domain_count_note": "A PAL address may appear in several domains; per-domain counts must not be summed into total unique addresses.",
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Pinned malmazuke PAL/USA structural mapping gaps", "",
        f"Source: `malmazuke/unirally-reconstruction@{PIN}`",
        "", report["interpretation"], "",
        "| domain | indexed | not covered | interval candidate | data interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, r in report["by_domain"].items():
        lines.append(f"| {name} | {r['total']} | {r['not-covered']} | {r['structural-interval-candidate']} | {r['data-interval-only']} |")
    lines += [
        "", report["domain_count_note"], "",
        f"Unique addresses selected: **{report['counts']['selected_unique_pal_addresses']}**; "
        f"not covered: **{report['counts']['not-covered']}**.",
        "", "## First unmapped evidence leads (not claims of defects)", "",
        "| PAL | domain(s) | original PAL class | source | research records |",
        "|---|---|---|---|---|",
    ]
    for e in report["worklist"]:
        short = e["native_symbols"][0] if e["native_symbols"] else "unattributed"
        refs = ", ".join(p.rsplit("/", 1)[-1] for p in e["source_records"][:3]) or "none"
        lines.append(f"| {e['pal']} | {', '.join(e['domains'])} | {e['pal_class']} | {short} | {refs} |")
    if report["worklist_truncated"]:
        lines += ["", "Worklist truncated. Filter with --domain and/or increase --limit."]
    lines += ["", "Only original USA ROM evidence can promote a structural interval into authoritative semantics.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", action="append", default=[], help="filter by indexed domain; may repeat")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--md-out", type=Path)
    a = ap.parse_args(argv)
    try:
        _symbols, links, labels = load_inputs()
        report = build_report(links, labels, domains=tuple(a.domain), limit=a.limit)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        ap.error(str(exc))
    markdown = render_markdown(report)
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if a.md_out:
        a.md_out.parent.mkdir(parents=True, exist_ok=True)
        a.md_out.write_text(markdown, encoding="utf-8")
    print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
