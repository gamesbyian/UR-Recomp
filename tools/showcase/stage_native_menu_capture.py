#!/usr/bin/env python3
"""Disposable media-only title/menu capture variant of the proven SDL recorder.

The established native recorder accepts only late post-GO frames. This adapter
pins its exact source text and relaxes that frame-window guard for pre-race
frontend observation, without modifying the general racing recorder.
"""
import argparse
from pathlib import Path
from stage_continuous_native_capture import patch as patch_capture

ORIGINAL = "count > 1200 || start < 1990)"
FRONTEND = "count > 1200 || start < 1)"
IDENT = "UR_CONTINUOUS_NATIVE_SDL_CAPTURE_V1"

def stage(source: str) -> str:
    if IDENT in source:
        raise ValueError("Frontend recorder requires unstaged host")
    output = patch_capture(source)
    if output.count(ORIGINAL) != 1:
        raise ValueError("Unexpected original source capture window")
    return output.replace(ORIGINAL, FRONTEND, 1)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework", type=Path, required=True)
    args = parser.parse_args()
    path = args.framework / "runner/src/desktop/host_main.c"
    text = path.read_text()
    path.write_text(stage(text))
    print("UR_NATIVE_MENU_CAPTURE_STAGED=1 actual_SDL_readback=1")

if __name__ == "__main__":
    main()
