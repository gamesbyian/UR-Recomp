#!/usr/bin/env python3
"""Fail closed if regenerated AOT opcode-PC call sites are absent.

Execute after native regeneration and before compilation. A positive static
result is NOT proof that a guest executed any instruction.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

CALL = re.compile(r'\bur_rf047_mark_executed_pc\s*\(\s*0x([0-9A-Fa-f]{6})u\s*,\s*1u\s*\)\s*;')
REQUIRED = {0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5,
            0x8282F0, 0x8282F2, 0x8282F6}


def inspect(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("native root does not exist")
    found = []
    # Do not presume runner/src/gen: actual generated roots vary by revision.
    for path in sorted(root.rglob("*.c")):
        parts = path.relative_to(root).parts
        if "build" in parts or ".tools" in parts:
            continue
        if path.name in ("beam_frame_driver.c", "interp_bridge.c", "cpu_state.c"):
            continue
        data = path.read_bytes()
        sites = [int(x, 16) for x in CALL.findall(data.decode("utf-8", errors="replace"))]
        if sites:
            found.append({"path": path.relative_to(root).as_posix(),
                          "sha256": hashlib.sha256(data).hexdigest(),
                          "sites": [f"{x:06X}" for x in sites]})
    if not found:
        raise ValueError("no generated C translation unit with compiled opcode-PC marker calls")
    seen = {int(s, 16) for f in found for s in f["sites"]}
    missing = REQUIRED - seen
    if missing:
        raise ValueError("missing generated opcode-PC targets: " +
                         ",".join(f"{x:06X}" for x in sorted(missing)))
    return {"schema": "ur-qa01-rf076-generated-exec-pc-preflight/1",
            "generated_translation_units": found,
            "required_decoded_sites": [f"{x:06X}" for x in sorted(REQUIRED)],
            "static_generated_calls_present": True,
            "actual_guest_opcode_executed": False,
            "original_native_same_semantic_phase": False,
            "accepted_USA_events": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = inspect(args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
