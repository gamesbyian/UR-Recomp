#!/usr/bin/env python3
"""Assert that a captured result screen prints the finisher's time.

Decision served: R-2026-10-04-UI-25 showed the native target could drop the
finish time on result screens (a framework LLE deadline-unwind fault) while
every other row rendered. The tilemap still looks structurally right, so only
decoded text catches it. This check is native-only and cheap: it reads an
existing dump checkpoint and requires at least ``--min-times`` ``m:ss.cc``
tokens in the decoded BG2 text.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import extract_menu_visual_language as mvl
import probe_tier_opponents as tier

TIME = re.compile(r"^\d:\d\d\.\d\d$")


def finish_times(texts: list[str]) -> list[str]:
    return [t for t in texts if TIME.match(t.strip())]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dump-dir", type=Path, required=True)
    ap.add_argument("--checkpoint", default="race-results")
    ap.add_argument("--min-times", type=int, default=1)
    args = ap.parse_args()
    texts = tier.screen_texts(mvl.Dump(args.dump_dir, args.checkpoint))
    times = finish_times(texts)
    print(f"RESULT_SCREEN_TEXT {args.checkpoint}: {texts}")
    print(f"RESULT_SCREEN_TIMES {args.checkpoint}: {times}")
    if len(times) < args.min_times:
        print(f"FAIL: expected >= {args.min_times} finish time(s) on {args.checkpoint}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
