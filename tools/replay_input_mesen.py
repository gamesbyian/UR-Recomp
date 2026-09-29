#!/usr/bin/env python3
"""Replay the shared deterministic P1/P2 input stream through mesen-for-ai."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path

from controller_input import ControllerRun, load_controller_runs, masks_at

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MESEN_REPO = ROOT / ".tools" / "src" / "mesen-for-ai"
CLIENT = Path("skills/mesen-emulator/scripts/mesen_client.py")

MASK_BUTTONS = (
    ("b", 0x001), ("y", 0x002), ("select", 0x004), ("start", 0x008),
    ("up", 0x010), ("down", 0x020), ("left", 0x040), ("right", 0x080),
    ("a", 0x100), ("x", 0x200), ("l", 0x400), ("r", 0x800),
)


def load_mesen_class(repo: Path):
    client = repo / CLIENT
    if not client.is_file():
        raise FileNotFoundError(
            f"mesen-for-ai client not found at {client}; "
            "run bootstrap_toolchain.py --tool mesen-for-ai"
        )
    spec = importlib.util.spec_from_file_location("ur_mesen_client", client)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mesen-for-ai client from {client}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Mesen


def buttons_for_mask(mask: int) -> dict[str, bool]:
    return {name: True for name, bit in MASK_BUTTONS if mask & bit}


def replay(mesen, runs: list[ControllerRun], frames: int) -> None:
    if frames < 0:
        raise ValueError("frames must be non-negative")
    previous = (None, None)
    started = False
    for frame in range(frames):
        current = masks_at(runs, frame)
        for port, mask in enumerate(current):
            if mask != previous[port]:
                mesen.tool(
                    "input.set",
                    port=port,
                    subport=0,
                    buttons=buttons_for_mask(mask),
                )
        result = mesen.tool("run.step_frames", frames=1, reset=not started)
        started = True
        status_frame = int(result["status"]["frame"])
        if status_frame < frame + 1:
            raise RuntimeError(
                f"Mesen frame counter did not advance: expected >= {frame + 1}, got {status_frame}"
            )
        previous = current
    for port in (0, 1):
        mesen.tool("input.set", port=port, subport=0, buttons={})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_file", type=Path)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--rom")
    ap.add_argument(
        "--mesen-for-ai-repo",
        default=os.environ.get("MESEN_FOR_AI_REPO", str(DEFAULT_MESEN_REPO)),
    )
    args = ap.parse_args()

    runs = load_controller_runs(args.input_file)
    if not args.rom:
        ap.error("--rom is required")

    mesen_repo = Path(args.mesen_for_ai_repo).resolve()
    Mesen = load_mesen_class(mesen_repo)
    with Mesen(repo=str(mesen_repo)) as mesen:
        mesen.load_rom(str(Path(args.rom).resolve()), timeout=180)
        replay(mesen, runs, args.frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
