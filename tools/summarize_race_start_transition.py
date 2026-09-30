#!/usr/bin/env python3
"""Reduce a dense Uniracers race-start capture into presentation change points."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.summarize_presentation_geometry import summarize_dump
    from tools.summarize_window_seam import summarize as summarize_window
    from tools.summarize_color_math_state import summarize as summarize_color
except ModuleNotFoundError:
    from summarize_presentation_geometry import summarize_dump
    from summarize_window_seam import summarize as summarize_window
    from summarize_color_math_state import summarize as summarize_color


def summarize_transition(root: Path) -> dict:
    tags = sorted(
        p.name.removesuffix(".info.json")
        for p in root.glob("race-start-*.info.json")
        if (root / f"{p.name.removesuffix('.info.json')}.fb.bgrx").is_file()
    )
    rows = []
    previous = None
    for tag in tags:
        presentation = summarize_dump(root, tag)
        window = summarize_window(root / f"{tag}.regs.json")
        color = summarize_color(
            root / f"{tag}.regs.json",
            root / f"{tag}.fb.bgrx",
        )
        current = {
            "framebuffer_sha256": presentation["framebuffer"]["sha256"],
            "width": presentation["framebuffer"]["width"],
            "height": presentation["framebuffer"]["height"],
            "setini": presentation["ppu"]["setini"],
            "screen_height": presentation["ppu"]["screen_height"],
            "bgmode": presentation["ppu"]["bgmode"],
            "tm": presentation["ppu"]["tm"],
            "ts": presentation["ppu"]["ts"],
            "cgwsel": presentation["ppu"]["cgwsel"],
            "cgadsub": presentation["ppu"]["cgadsub"],
            "xor_layers": window["xor_layers"],
            "fixed_color": color["fixed_color"],
            "subscreen_math_selected": color["subscreen_math_selected"],
        }
        changed_fields = []
        if previous is not None:
            changed_fields = [
                key for key, value in current.items()
                if previous.get(key) != value
            ]
        rows.append({
            "checkpoint": tag,
            "frame": presentation["frame"],
            "state": current,
            "changed_from_previous": changed_fields,
            "bottom_edge": presentation["framebuffer"]["edges"]["bottom"],
        })
        previous = current
    return {
        "schema_version": 1,
        "checkpoints": rows,
        "change_points": [
            {
                "checkpoint": row["checkpoint"],
                "frame": row["frame"],
                "fields": row["changed_from_previous"],
            }
            for row in rows
            if row["changed_from_previous"]
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    report = summarize_transition(args.dump_dir)
    if not report["checkpoints"]:
        raise SystemExit("no race-start checkpoints found")
    for row in report["checkpoints"]:
        print(
            f"{row['checkpoint']}: frame={row['frame']} "
            f"changed={','.join(row['changed_from_previous']) or '-'} "
            f"tm={row['state']['tm']} ts={row['state']['ts']} "
            f"cg={row['state']['cgwsel']}/{row['state']['cgadsub']} "
            f"xor={row['state']['xor_layers']}"
        )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
