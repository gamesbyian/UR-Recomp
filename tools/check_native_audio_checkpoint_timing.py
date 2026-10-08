#!/usr/bin/env python3
"""Assert the native audio tail brackets a named checkpoint by guest frames.

This establishes the *guest* window only. It does not pretend the SDL device
stream has a measured fixed phase offset from emulated audio sample production.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from tools.build_audio_checkpoint_route import CHECKPOINTS, POST_CHECKPOINT_FRAMES
from tools.build_audio_pause_route import CHECKPOINTS as PAUSE_CHECKPOINTS


def validate_log(log_text: str, checkpoint: str) -> dict:
    if checkpoint not in (*CHECKPOINTS, *PAUSE_CHECKPOINTS):
        raise ValueError(f"unrecognized audio checkpoint {checkpoint!r}")
    positions = {}
    for name in (checkpoint, checkpoint + "-audio-post"):
        pattern = re.compile(
            rf"\bscript f=(\d+) dump {re.escape(name)} ok(?:\r?\n|$)"
        )
        matches = pattern.findall(log_text)
        if len(matches) != 1:
            raise ValueError(
                f"expected exactly one completed guest-frame dump for {name}, "
                f"found {len(matches)}"
            )
        positions[name] = int(matches[0])
    begin = positions[checkpoint]
    end = positions[checkpoint + "-audio-post"]
    if end - begin != POST_CHECKPOINT_FRAMES:
        raise ValueError(
            f"native audio window waited {end - begin} frames, "
            f"expected {POST_CHECKPOINT_FRAMES}"
        )
    return {
        "checkpoint": checkpoint,
        "guest_frame_at_checkpoint": begin,
        "guest_frame_at_post_capture": end,
        "guest_frames_after_checkpoint": POST_CHECKPOINT_FRAMES,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", type=Path)
    ap.add_argument("checkpoint", choices=(*CHECKPOINTS, *PAUSE_CHECKPOINTS))
    args = ap.parse_args()
    report = validate_log(
        args.log.read_text(encoding="utf-8", errors="replace"), args.checkpoint
    )
    print(
        "NATIVE_AUDIO_WINDOW PASS "
        f"checkpoint={report['checkpoint']} "
        f"guest_frame={report['guest_frame_at_checkpoint']} "
        f"post_frame={report['guest_frame_at_post_capture']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
