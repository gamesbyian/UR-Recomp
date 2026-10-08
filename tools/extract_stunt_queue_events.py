#!/usr/bin/env python3
"""Read actual P1 HUD/stunt message IDs and delayed boost changes from WRAM.

Consumes contiguous, frame-by-frame full WRAM dumps already emitted by the
input-only stunt boundary fixture (e.g. w000..w090). The game-owned P1 queue
is 32 byte slots at 7E:0CBB; reader 0CE1, writer 0CE3 (both mod 32).
A newly advanced writer identifies the *enqueued* message at the old slot.
An increase in persistent boost 11CF is a separate, later observable event.

An equal reward value is NOT enough to assign a message ID to a bonus: more
than one message may be pending, and meter decay can coincide with credit.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

WRAM_LEN = 0x20000
QUEUE_BASE = 0x0CBB
QUEUE_LEN = 32
READ_INDEX = 0x0CE1
WRITE_INDEX = 0x0CE3
PERSISTENT_BOOST = 0x11CF
AIR = 0x0545
X_SPEED = 0x04B7
# USA-retail P1 lap word and per-message consumer enable for ID 0x0F.
LAST_LAP_REMAINING = 0x0EF1
LAST_LAP_ENABLE = 0x20E8 + 0x0F - 1  # 7E:20F6, byte


class QueueEvidenceError(ValueError):
    """Bad capture, unsupported queue transition, or cross-engine disagreement."""


def u16(wram: bytes, addr: int) -> int:
    return struct.unpack_from("<H", wram, addr)[0]


def read_series(root: Path, first: int, last: int, prefix: str = "w",
                width: int = 3, track: int = 19) -> list[dict]:
    if (type(first) is not int or type(last) is not int or first < 0 or
            last < first or last - first > 4000 or
            type(width) is not int or width not in (3, 4) or
            type(track) is not int or not 0 <= track <= 49 or
            not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", prefix)):
        raise QueueEvidenceError("invalid bounded frame window or filename/course selector")
    result = []
    for n in range(first, last + 1):
        path = root / f"{prefix}{n:0{width}d}.wram.bin"
        if not path.is_file():
            raise QueueEvidenceError(f"missing required consecutive frame {n}: {path}")
        image = path.read_bytes()
        if len(image) != WRAM_LEN:
            raise QueueEvidenceError(f"frame {n}: invalid WRAM size {len(image)}, expected {WRAM_LEN}")
        if image[0x00CE] != track or image[0x0313] != 1:
            raise QueueEvidenceError(f"frame {n}: invalid active course {image[0x00CE]}/race {image[0x0313]}")
        reader, writer = u16(image, READ_INDEX), u16(image, WRITE_INDEX)
        if not 0 <= reader < QUEUE_LEN or not 0 <= writer < QUEUE_LEN:
            raise QueueEvidenceError(f"frame {n}: malformed queue indices {reader}/{writer}")
        result.append({
            "frame": n,
            "read": reader,
            "write": writer,
            "buffer": tuple(image[QUEUE_BASE:QUEUE_BASE + QUEUE_LEN]),
            "boost": u16(image, PERSISTENT_BOOST),
            "air": image[AIR],
            "x_speed": struct.unpack_from("<h", image, X_SPEED)[0],
            "laps_remaining": u16(image, LAST_LAP_REMAINING),
            "last_lap_enable": image[LAST_LAP_ENABLE],
        })
    return result


def analyze(rows: list[dict], lookback: int = 40) -> dict:
    if not rows or type(lookback) is not int or not 0 <= lookback <= 600:
        raise QueueEvidenceError("need nonempty consecutive frames and a bounded lookback")
    queued, boosts, lap_transitions = [], [], []
    for prev, curr in zip(rows, rows[1:]):
        if curr["frame"] != prev["frame"] + 1:
            raise QueueEvidenceError("capture has missing or out-of-order guest frames")
        delta = (curr["write"] - prev["write"]) % QUEUE_LEN
        # One frame cannot safely identify an overwritten 32-item ring cycle;
        # 0 advances are interpreted only as no *observed* index change.
        if delta > 8:
            raise QueueEvidenceError(f"frame {curr['frame']}: writer advances {delta} slots; event attribution unsafe")
        for n in range(delta):
            slot = (prev["write"] + n) % QUEUE_LEN
            queued.append({
                "frame": curr["frame"], "slot": slot,
                "message_id": f"0x{curr['buffer'][slot]:02X}",
                "read_index": curr["read"],
            })
        if curr["laps_remaining"] == 1 and prev["laps_remaining"] != 1:
            lap_transitions.append({
                "frame": curr["frame"],
                "previous": prev["laps_remaining"],
                "last_lap_enable_at_transition": curr["last_lap_enable"],
                "note": "per-player post-decrement lap word; not a credit assertion",
            })
        diff = curr["boost"] - prev["boost"]
        if diff > 0:
            recent = [ev for ev in queued if 0 <= curr["frame"] - ev["frame"] <= lookback]
            boosts.append({
                "frame": curr["frame"], "net_boost_increase": diff,
                "preceding_enqueues": [
                    {"frame": x["frame"], "message_id": x["message_id"]} for x in recent
                ],
                "attribution": "unproven: queue consumption and concurrent drain not captured",
            })
    return {
        "schema_version": 1,
        "window": [rows[0]["frame"], rows[-1]["frame"]],
        "count": len(rows),
        "p1_queue": {"buffer": "7E:0CBB..0CDA", "read": "7E:0CE1", "write": "7E:0CE3"},
        "p1_persistent_boost": "7E:11CF",
        "enqueued_messages": queued,
        "positive_net_boost_events": boosts,
        "last_lap_transitions": lap_transitions,
        "last_lap_consumer_enable": "7E:20F6 byte (USA, ID 0x0F)",
        "constraint": "input-only source captures; enqueued ID does not prove which message was consumed",
    }


def compare(a: list[dict], b: list[dict]) -> dict:
    if not a or len(a) != len(b) or [r["frame"] for r in a] != [r["frame"] for r in b]:
        raise QueueEvidenceError("native/reference must have equal, nonempty guest-relative frame windows")
    first = next(({"frame": x["frame"], "fields": sorted(
        k for k in ("read", "write", "buffer", "boost", "air", "x_speed",
                  "laps_remaining", "last_lap_enable") if x[k] != y[k]
    )} for x, y in zip(a, b) if x != y), None)
    return {"first_divergence": first, "native_reference_equal": first is None}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dumps", type=Path, help="P1 WRAM capture directory")
    p.add_argument("--other", type=Path, help="other engine's capture directory")
    p.add_argument("--first", type=int, default=0)
    p.add_argument("--last", type=int, default=90)
    p.add_argument("--prefix", default="w")
    p.add_argument("--width", type=int, default=3)
    p.add_argument("--track", type=int, default=19)
    p.add_argument("--lookback", type=int, default=40)
    p.add_argument("--json-out", type=Path)
    args = p.parse_args(argv)
    try:
        rows = read_series(args.dumps, args.first, args.last, args.prefix, args.width, args.track)
        report = analyze(rows, args.lookback)
        if args.other is not None:
            other = read_series(args.other, args.first, args.last, args.prefix, args.width, args.track)
            report["cross_engine"] = compare(rows, other)
            report["other"] = analyze(other, args.lookback)
    except (QueueEvidenceError, OSError, ValueError, TypeError, KeyError) as exc:
        p.error(str(exc))
    out = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(out, encoding="utf-8")
    print(out, end="")
    return 0 if report.get("cross_engine", {}).get("native_reference_equal", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
