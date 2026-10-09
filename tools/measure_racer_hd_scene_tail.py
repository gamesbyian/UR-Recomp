#!/usr/bin/env python3
"""QA-08: measure bounded *actual native* HD/Original presentation in 1P/VS.

The companion scripts explicitly wait for ROM active-race 7E:0313 == 01,
then provide >=120 guest frames of racing. This analyzer takes exactly
the last N host-presented guest frames; it does not turn menu/boot
frames into race coverage or imply 1P/VS is HD-admitted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.measure_racer_hd_live_draws import CENSUS, analyze


def analyze_tail(log: str, *, mode: str, count: int, source: str = "") -> dict:
    if mode not in ("one-player", "vs"):
        raise ValueError("unsupported scene mode")
    if count < 1 or count > 3000:
        raise ValueError("invalid guest-frame tail length")
    present_ids = []
    for line in log.splitlines():
        match = CENSUS.search(line)
        if match and match.group(2) == "present":
            present_ids.append(int(match.group(1)))
    if not present_ids:
        raise ValueError("no actual native host present in scene")
    end = max(present_ids)
    begin = end - count + 1
    if begin < 0:
        raise ValueError("native scene shorter than requested moving window")
    report = analyze(
        log, source=source, from_frame=begin, to_frame=end
    )
    m = report["measurement"]
    if m["guest_frames_with_host_presents"] != count:
        raise ValueError("incomplete host presents in active-race tail")
    if m["guest_frames_without_host_presents"] or m["armed_without_hd_draw_guest_frames"]:
        raise ValueError("unsafe native graphics admission within scene")
    if m["hd_drawn_guest_frames"] + m["original_presented_guest_frames"] != count:
        raise ValueError("HD plus stock does not partition native present")
    report["scene_mode"] = mode
    report["classification"] = (
        "native 1P/VS script-confirmed active race tail host draw outcome;"
        " not same-frame original-raster visual or priority fidelity"
    )
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("--mode", choices=("one-player", "vs"), required=True)
    ap.add_argument("--tail", type=int, default=120)
    ap.add_argument("--json-out", type=Path)
    a = ap.parse_args()
    report = analyze_tail(
        a.log.read_text(encoding="utf-8", errors="replace"),
        mode=a.mode, count=a.tail, source=str(a.log),
    )
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(encoded, encoding="utf-8")
    print(
        f"UR_RACER_HD_SCENE_TAIL mode={a.mode} "
        f"guest={report['measurement']['guest_frames_observed']} "
        f"hd={report['measurement']['hd_drawn_guest_frames']} "
        f"original={report['measurement']['original_presented_guest_frames']} "
        f"switches={report['measurement']['draw_mode_switches']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
