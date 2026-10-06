#!/usr/bin/env python3
"""Measure Racer HD fallback burden from dense reference-core WRAM dumps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from measure_racer_hd_fallback_frequency import build_report, state_key

ADDR = {
    "p1_primary": 0x0FE9,
    "p2_primary": 0x0FEB,
    "p1_companion": 0x0D3F,
    "p2_companion": 0x0D41,
    "p1_selector": 0x0C83,
    "p2_selector": 0x0C85,
    "p1_gate": 0x0D1B,
    "p2_gate": 0x0D1D,
}

TARGET_STATE = (
    "0x0545/0x057C + 0x0000/0x0C27 "
    "sel 0/0 gate 0x0000/0x0001"
)


def read_le16(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def row_from_wram(frame: int, data: bytes) -> dict:
    if len(data) < 0x20000:
        raise ValueError(f"frame {frame}: WRAM dump too small ({len(data)})")
    row = {"frame": frame}
    for key, offset in ADDR.items():
        value = read_le16(data, offset)
        if key.endswith("selector"):
            row[key] = value
        else:
            row[key] = f"0x{value:04X}"
    return row


def load_rows(dump_dir: Path, prefix: str) -> list[dict]:
    rows = []
    for path in sorted(dump_dir.glob(f"{prefix}-*.wram.bin")):
        stem = path.name.removesuffix(".wram.bin")
        try:
            frame = int(stem.rsplit("-", 1)[1])
        except (IndexError, ValueError) as exc:
            raise ValueError(f"cannot parse frame from {path.name}") from exc
        rows.append(row_from_wram(frame, path.read_bytes()))
    rows.sort(key=lambda row: row["frame"])
    if not rows:
        raise ValueError("no Racer sample WRAM dumps found")
    expected = list(range(rows[0]["frame"], rows[-1]["frame"] + 1))
    actual = [row["frame"] for row in rows]
    if actual != expected:
        raise ValueError(
            f"sample frames are not dense/contiguous: "
            f"{actual[:3]}...{actual[-3:]} vs {expected[0]}..{expected[-1]}"
        )
    return rows


def generate_script(start: int, end: int, prefix: str) -> str:
    if start < 0 or end < start:
        raise ValueError("invalid sample window")
    lines = [
        "# Generated dense Racer semantic sampling route.",
        f"wait {start}",
        f"dump {prefix}-{start}",
    ]
    for frame in range(start + 1, end + 1):
        lines.append("wait 1")
        lines.append(f"dump {prefix}-{frame}")
    lines.append("quit")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("script")
    gen.add_argument("--start", type=int, required=True)
    gen.add_argument("--end", type=int, required=True)
    gen.add_argument("--prefix", default="racer-sample")
    gen.add_argument("--out", type=Path, required=True)

    measure = sub.add_parser("measure")
    measure.add_argument("dump_dir", type=Path)
    measure.add_argument("--prefix", default="racer-sample")
    measure.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "analysis/data/racer-hd-replacement-prototype.json",
    )
    measure.add_argument("--json-out", type=Path)
    measure.add_argument("--workflow-run", type=int)

    args = ap.parse_args()
    if args.command == "script":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            generate_script(args.start, args.end, args.prefix),
            encoding="utf-8",
        )
        return 0

    rows = load_rows(args.dump_dir, args.prefix)
    report = build_report(
        rows,
        json.loads(args.registry.read_text(encoding="utf-8")),
        source={
            "kind": "ordinary-snes9x-reference-racer-wram-census",
            "workflow_run": args.workflow_run,
            "trace_window": [rows[0]["frame"], rows[-1]["frame"]],
            "input_fixture": "tests/input/two-player-p1-win.input",
            "sampling": "every guest frame from full 128 KiB WRAM dumps",
        },
    )
    target = next(
        (
            item for item in report["unsupported_exact_states_ranked"]
            if item["state"] == TARGET_STATE
        ),
        None,
    )
    report["target_discriminator"] = {
        "state": TARGET_STATE,
        "observed": target is not None,
        "measurement": target,
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
