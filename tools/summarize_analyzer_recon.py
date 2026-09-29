#!/usr/bin/env python3
"""Summarize SNESRecomp's generated whole-program analysis manifest.

This is intentionally framework-schema-facing rather than Uniracers-specific:
the generated program_manifest.json is the durable analyzer contract for exact
AOT/LLE variants and unresolved/dynamic transfer edges.  Keep the output small
enough to preserve as research evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


AOT_DISPOSITIONS = {"aot_eligible", "aot_emitted", "hle_overlay"}
LLE_DISPOSITIONS = {"lle_only"}
RUNTIME_EDGE_KINDS = {
    "dynamic_dispatch",
    "unresolved_indirect",
    "suppressed_indirect_call",
}


def _hex24(value: int) -> str:
    value &= 0xFFFFFF
    return f"{value >> 16:02X}:{value & 0xFFFF:04X}"


def summarize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    version = int(manifest.get("format_version", 0))
    if version != 3:
        raise ValueError(f"unsupported program manifest format_version={version}")

    nodes = manifest.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise ValueError("program manifest has no nodes")

    dispositions: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    edge_kinds: Counter[str] = Counter()
    edge_resolutions: Counter[str] = Counter()
    runtime_edges: list[dict[str, Any]] = []
    lle_examples: list[dict[str, Any]] = []
    instruction_count = 0

    for key in sorted(nodes):
        node = nodes[key]
        disposition = str(node.get("disposition", "unknown"))
        dispositions[disposition] += 1
        instruction_count += int(node.get("instruction_count", 0))

        node_reasons = [str(item) for item in node.get("reasons", [])]
        reasons.update(node_reasons)

        if disposition in LLE_DISPOSITIONS and len(lle_examples) < 32:
            lle_examples.append(
                {
                    "variant": key,
                    "pc": _hex24(int(node["key"]["pc24"])),
                    "m": int(node["key"]["m"]),
                    "x": int(node["key"]["x"]),
                    "instruction_count": int(node.get("instruction_count", 0)),
                    "reasons": node_reasons,
                }
            )

        for edge in node.get("demands", []):
            kind = str(edge.get("kind", "unknown"))
            resolution = str(edge.get("resolution", "unknown"))
            edge_kinds[kind] += 1
            edge_resolutions[resolution] += 1
            if kind in RUNTIME_EDGE_KINDS or resolution == "lle_dynamic":
                target = edge.get("target")
                runtime_edges.append(
                    {
                        "source_variant": key,
                        "site_pc": _hex24(int(edge.get("site_pc24", 0))),
                        "kind": kind,
                        "resolution": resolution,
                        "target_pc": (
                            _hex24(int(target["pc24"]))
                            if isinstance(target, dict) and "pc24" in target
                            else None
                        ),
                        "detail": str(edge.get("detail", "")),
                    }
                )

    total_nodes = sum(dispositions.values())
    aot_nodes = sum(dispositions[name] for name in AOT_DISPOSITIONS)
    lle_nodes = sum(dispositions[name] for name in LLE_DISPOSITIONS)

    return {
        "schema": "ur-recomp analyzer reconnaissance v1",
        "program_manifest_format": version,
        "roots": len(manifest.get("roots", [])),
        "nodes": {
            "total": total_nodes,
            "aot_capable": aot_nodes,
            "lle_only": lle_nodes,
            "aot_capable_fraction": round(aot_nodes / total_nodes, 6),
            "by_disposition": dict(sorted(dispositions.items())),
            "decoded_instruction_instances": instruction_count,
        },
        "exits": {
            "exact_mode_proofs": len(manifest.get("exit_modes", {})),
            "multi_mode_proofs": len(manifest.get("exit_mode_sets", {})),
        },
        "edges": {
            "total": sum(edge_kinds.values()),
            "by_kind": dict(sorted(edge_kinds.items())),
            "by_resolution": dict(sorted(edge_resolutions.items())),
            "runtime_or_unresolved_count": len(runtime_edges),
            "runtime_or_unresolved": runtime_edges,
        },
        "lle": {
            "reason_counts": dict(sorted(reasons.items())),
            "examples": lle_examples,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = summarize_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
