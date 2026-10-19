#!/usr/bin/env python3
"""RF062 fail-closed static verification of live generated AOT sound opcode PC.

A marker in a non-executing M/X variant cannot qualify a native read. This
source check is necessary before replay, never sufficient for causal proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCOPE = "Snd_UploadBlockList_82EF_M1X0"
DECL = re.compile(r"(?m)^[ \t]*RecompReturn[ \t]+" + SCOPE +
                  r"[ \t]*\([ \t]*CpuState[ \t]*\*[ \t]*cpu[ \t]*\)[ \t]*\{")
NEXT = re.compile(r"(?m)^[ \t]*RecompReturn[ \t]+\w+[ \t]*\(")
TARGET = re.compile(
    r"ur_rf062_read8_pc_8282f0[ \t]*\([ \t]*cpu[ \t]*,[^;]*\)[ \t]*;"
    r"[ \t]*/\*[ \t]*UR_QA01_RF062_DIRECT_PC_8282F0[ \t]*\*/")


def audit(generated_dir: Path) -> dict:
    if not generated_dir.is_dir():
        raise ValueError("RF062 actual generated C directory missing")
    owners = []
    for path in sorted(generated_dir.rglob("*.c")):
        data = path.read_bytes()
        source = data.decode("utf8")
        for match in DECL.finditer(source):
            end = NEXT.search(source, match.end())
            body = source[match.start():end.start() if end else len(source)]
            sites = TARGET.findall(body)
            owners.append({
                "file": str(path),
                "generated_file_sha256": hashlib.sha256(data).hexdigest(),
                "live_generated_function": SCOPE,
                "direct_original_8282F0_real_bus_read_callsites": len(sites),
                "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            })
    if len(owners) != 1:
        raise ValueError("RF062 missing/duplicated live M1X0 sound AOT body")
    if owners[0]["direct_original_8282F0_real_bus_read_callsites"] < 1:
        raise ValueError("RF062 live M1X0 lacks real executed 82:82F0 Read shim")
    return {
        "schema": "ur-qa01-rf062-live-generated-site/1",
        "source_provenance": owners[0],
        "runtime_executed_marker_proven": False,
        "actual_native_ROM_bus_read_pc_proven": False,
        "first_original_native_consumed_difference_proven": False,
        "accepted_complete_USA_events": 0,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("generated_dir", type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    result = audit(a.generated_dir)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RF062 live emitted M1X0 opcode shim present; still requires authentic execution")


if __name__ == "__main__":
    main()
