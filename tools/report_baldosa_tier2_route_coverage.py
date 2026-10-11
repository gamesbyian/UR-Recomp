#!/usr/bin/env python3
"""Read-only route-bound interpreted-work triage for Baldosa Tier-2 JSON.

Consume output from the *pinned* framework's tier2_ingest.py --json. This tool
never promotes AOT roots, changes generator config, executes imported code, or
claims original/native gameplay acceptance. Keep every build identity separate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

try:
    from tools.query_baldosa_symbols import load as load_source_symbols, PIN as BALDOSA_PIN
except ModuleNotFoundError:
    from query_baldosa_symbols import load as load_source_symbols, PIN as BALDOSA_PIN

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (ROOT / "reference/imported/reverse-engineering/"
            "baldosa-uniracers-recomp/tests/routes")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ENTRY = re.compile(r"^M[01]X[01]$")
IDENTITY = ("rom_sha256", "program_digest", "build_digest", "module_id", "mapper")


def pc(value: str | int) -> int:
    parsed = value if isinstance(value, int) else int(str(value), 0)
    if not 0 <= parsed <= 0xFFFFFF:
        raise ValueError("invalid 24-bit PC")
    return parsed


def canonical_usa_pc(raw: int, mapper: str) -> int:
    # Only the established four LoROM banks in this USA source inventory.
    if mapper == "lorom" and raw & 0xFFFF >= 0x8000 and raw >> 16 in (0, 1, 2, 3):
        return raw | 0x800000
    return raw


def symbol_index(rows: list[dict]) -> dict[int, list[str]]:
    mapping: dict[int, set[str]] = {}
    for row in rows:
        if row.get("kind") != "function":
            continue
        address = int(row["address"], 16)
        # Both original low-bank and FastROM mirrored names are source leads.
        canonical = canonical_usa_pc(address, "lorom")
        mapping.setdefault(canonical, set()).add(row["name"])
    return {key: sorted(value) for key, value in mapping.items()}


def _valid_identity(data: dict) -> dict:
    identity = data.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("missing complete Tier-2 capture identity")
    for name in ("rom_sha256", "program_digest", "build_digest"):
        value = identity.get(name)
        if not isinstance(value, str) or not SHA256.fullmatch(value.lower()):
            raise ValueError(f"missing or invalid {name} identity; no cross-build reuse")
    for name in ("mapper", "module_id"):
        if not isinstance(identity.get(name), str) or not identity[name]:
            raise ValueError(f"missing Tier-2 identity: {name}")
    return {name: identity[name] for name in IDENTITY}


def evaluate(route: str, capture: dict, fixture: bytes,
             symbols: dict[int, list[str]], *, top: int = 12) -> dict:
    if not re.fullmatch(r"[a-z0-9_]+", route):
        raise ValueError("route must be a known fixture stem")
    if top < 1:
        raise ValueError("top must be positive")
    identity = _valid_identity(capture)
    count = capture.get("capture_count")
    if type(count) is not int or count < 1:
        raise ValueError("no completed coverage captures")
    warnings = capture.get("warnings")
    discoveries = capture.get("discoveries")
    hot = capture.get("hot_instructions")
    if not isinstance(warnings, list) or any(not isinstance(x, str) for x in warnings):
        raise ValueError("missing coverage warnings array")
    if not isinstance(discoveries, list) or not isinstance(hot, list):
        raise ValueError("coverage discovery and instruction-cost arrays required")
    instructions = capture.get("interpreted_instructions")
    cycles = capture.get("interpreted_guest_cycles")
    if any(type(x) is not int or x < 0 for x in (instructions, cycles)):
        raise ValueError("invalid interpreted-work counters")
    detailed = []
    for item in hot:
        if not isinstance(item, dict):
            raise ValueError("invalid instruction-cost record")
        if item.get("processor", "snes_cpu") != "snes_cpu":
            continue
        source = pc(item["target_pc24"])
        mode = item.get("entry_mx", "unknown")
        if mode != "unknown" and not ENTRY.fullmatch(str(mode)):
            raise ValueError("malformed M/X entry variant")
        work = item.get("guest_cycles")
        count_ins = item.get("interpreted_instructions")
        if any(type(x) is not int or x < 0 for x in (work, count_ins)):
            raise ValueError("invalid exclusive interpreted cost")
        addr = canonical_usa_pc(source, identity["mapper"])
        detailed.append({
            "pc": f"{source:06X}", "canonical_usa_pc": f"{addr:06X}",
            "entry_mx": mode, "emulation": item.get("emulation"),
            "guest_cycles": work, "interpreted_instructions": count_ins,
            "baldosa_named_function_leads": symbols.get(addr, []),
            "source_name_is_verified": False,
        })
    detailed.sort(key=lambda row: (-row["guest_cycles"], -row["interpreted_instructions"], row["pc"], str(row["entry_mx"])))
    status = Counter()
    for row in discoveries:
        if not isinstance(row, dict) or not isinstance(row.get("candidate_status"), str):
            raise ValueError("discovery lacks audited candidate_status")
        status[row["candidate_status"]] += 1
    total_detailed = sum(row["guest_cycles"] for row in detailed)
    return {
        "route": route,
        "route_fixture_sha256": hashlib.sha256(fixture).hexdigest(),
        "route_capture_binding_verified": False,
        "route_association": "caller-supplied name, not independently bound by Tier-2 identity",
        "identity": identity, "capture_count": count,
        "warnings": warnings,
        "interpreted_instructions": instructions,
        "interpreted_guest_cycles": cycles,
        "exclusive_cpu_instruction_cost_cycles": total_detailed,
        "instruction_cost_attribution_complete": total_detailed == cycles and not warnings,
        "discovery_status_counts": dict(sorted(status.items())),
        "top_interpreted_pcs": detailed[:top],
        "listed_pcs": len(detailed), "top_truncated": len(detailed) > top,
        "aot_promotion_authorized": False,
        "route_qa_acceptance_proven": False,
        "evidence_quality": "incomplete" if warnings or total_detailed != cycles
                            else "capture_identity_present_not_validated_against_original",
    }


def assemble(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("at least one route required")
    names = [row["route"] for row in rows]
    if len(set(names)) != len(names):
        raise ValueError("duplicate route")
    ids = [tuple(row["identity"][key] for key in IDENTITY) for row in rows]
    return {
        "schema_version": 1,
        "kind": "baldosa_tier2_interpreter_work_advisory",
        "external_project": "baldosa/uniracers-recomp",
        "external_source_commit": BALDOSA_PIN,
        "source_format": "baldosa/snesrecomp tier2_ingest.py --json",
        "same_build_identity_across_routes": len(set(ids)) == 1,
        "routes": rows,
        "totals_not_aggregated": True,
        "interpretation": (
            "Exclusive observed interpreted PC costs and external source-name leads; "
            "not function attribution, proof of AOT safety, a verified fix, "
            "complete original/native parity, or a product/release gate."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", action="append", required=True, metavar="NAME=INGEST_JSON",
                        help="Baldosa fixture stem and archived tier2_ingest --json report")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        symbols = symbol_index(load_source_symbols())
        rows = []
        for route_spec in args.route:
            if "=" not in route_spec:
                raise ValueError("route must be NAME=INGEST_JSON")
            route, src = route_spec.split("=", 1)
            if not re.fullmatch(r"[a-z0-9_]+", route):
                raise ValueError(f"invalid route name: {route!r}")
            fixture = (FIXTURES / (route + ".txt"))
            if not fixture.is_file():
                raise ValueError(f"not a pinned Baldosa source fixture: {route}")
            path = Path(src)
            data = json.loads(path.read_text(encoding="utf-8"))
            row = evaluate(route, data, fixture.read_bytes(), symbols, top=args.top)
            row["capture_report_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(row)
        result = assemble(rows)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
