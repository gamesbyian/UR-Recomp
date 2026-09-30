#!/usr/bin/env python3
"""Summarize SNES window/color-math state from snesref *.regs.json dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LOGIC = {0: "OR", 1: "AND", 2: "XOR", 3: "XNOR"}
LAYER_NAMES = ["BG1", "BG2", "BG3", "BG4", "OBJ", "COL"]


def summarize(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    ppu = data["ppu"]
    window = ppu["window"]
    layers = []
    for name, state in zip(LAYER_NAMES, window["layers"]):
        entry = {
            "name": name,
            "w1_enable": state["w1_enable"],
            "w1_inside": state["w1_inside"],
            "w2_enable": state["w2_enable"],
            "w2_inside": state["w2_inside"],
            "logic": state["logic"],
            "logic_name": LOGIC.get(state["logic"], f"UNKNOWN_{state['logic']}"),
        }
        entry["two_window_active"] = bool(entry["w1_enable"] and entry["w2_enable"])
        entry["xor_active"] = bool(entry["two_window_active"] and entry["logic"] == 2)
        layers.append(entry)
    return {
        "checkpoint": path.name.removesuffix(".regs.json"),
        "frame_tag": data.get("frame_tag"),
        "window_bounds": {
            "w1_left": window["w1_left"],
            "w1_right": window["w1_right"],
            "w2_left": window["w2_left"],
            "w2_right": window["w2_right"],
        },
        "window_select": {
            "w12sel": window["w12sel"],
            "w34sel": window["w34sel"],
            "wobjsel": window["wobjsel"],
            "wbglog": window["wbglog"],
            "wobjlog": window["wobjlog"],
        },
        "screen_masks": {
            "tm": ppu["tm"],
            "ts": ppu["ts"],
            "tmw": ppu["tmw"],
            "tsw": ppu["tsw"],
        },
        "color_math": {
            "cgwsel": ppu["cgwsel"],
            "cgadsub": ppu["cgadsub"],
            "fixed_color": ppu["fixed_color"],
        },
        "layers": layers,
        "xor_layers": [layer["name"] for layer in layers if layer["xor_active"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    rows = [summarize(path) for path in args.inputs]
    report = {
        "schema_version": 1,
        "checkpoints": rows,
        "xor_checkpoints": [
            {"checkpoint": row["checkpoint"], "layers": row["xor_layers"]}
            for row in rows
            if row["xor_layers"]
        ],
    }

    text = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
