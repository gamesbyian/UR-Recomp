#!/usr/bin/env python3
"""Metamorphic A/B: identical frontier cases with runtime turbo off vs on.

Turbo sets ``disableRender`` on 15 of 16 frames. It is admissible for the
WRAM-only frontier observers only while every checkpoint WRAM dump stays
byte-identical. Re-run this against any new SNESRecomp pin or native candidate
before trusting EXECUTION_POLICY there. Needs a real native candidate and the
verified USA ROM; produces evidence about rendering invariance only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import qa02_native_2p_seeded_endurance as guest
import qa_adaptive_frontier as fr


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--cases", type=int, default=12)
    ap.add_argument("--base-seed", type=int, default=50037001)
    args = ap.parse_args()
    if args.work.exists():
        raise SystemExit("refuse to reuse a work root")
    args.work.mkdir(parents=True)
    source_input, source_script = guest.base_source()
    rendered = guest.render_script(source_script)
    scripts = {"rendered": rendered, "turbo": fr.turbo_script(rendered)}
    for name, text in scripts.items():
        (args.work / f"{name}.script").write_text(text)
    names = [guest.BASE_CHECK, *(f"endurance-{f}" for f in guest.FRAMES)]
    rows = []
    for i in range(args.cases):
        seed, arm = args.base_seed + 11 * i, fr.ARMS[i % len(fr.ARMS)]
        result = {}
        for mode in scripts:
            root = args.work / f"{mode}-{seed}"
            start = time.monotonic()
            out = fr.execute_once(exe=args.exe, rom=args.rom, source_input=source_input,
                                  script=args.work / f"{mode}.script", root=root,
                                  seed=seed, arm=arm, timeout=170)
            result[mode] = (time.monotonic() - start,
                            [hashlib.sha256((root / "dumps" / f"{n}.wram.bin").read_bytes()).hexdigest()
                             for n in names], sorted(out["full_trace"]["features"]))
        rows.append({"seed": seed, "arm": arm,
                     "identical_wram": result["rendered"][1] == result["turbo"][1],
                     "features_equal": result["rendered"][2] == result["turbo"][2],
                     "rendered_s": round(result["rendered"][0], 2),
                     "turbo_s": round(result["turbo"][0], 2)})
        print(json.dumps(rows[-1]), flush=True)
    rendered_s = sum(r["rendered_s"] for r in rows)
    turbo_s = sum(r["turbo_s"] for r in rows)
    ok = all(r["identical_wram"] and r["features_equal"] for r in rows)
    print(json.dumps({"cases": len(rows), "all_identical": ok,
                      "saving_fraction": round(1 - turbo_s / rendered_s, 3)}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
