#!/usr/bin/env python3
"""Analyze SNESRecomp audio_events into CPU->APU command handoff chains.

This is game-neutral transport analysis. It does not assume what a port or value
means to a particular title. A nonzero CPU write is treated as a candidate
command; the report records whether it was applied to the APU input port and
whether the SPC later read the same value before another applied write replaced
it.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, deque
from pathlib import Path


def _ival(value) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    return int(text, 0) if text.startswith("0x") else int(text)


def _hexval(value) -> int:
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    return int(text, 16)


def analyze(events: list[dict]) -> dict:
    has_apply = any(event.get("t") == "cpu_ap" for event in events)
    mutation_type = "cpu_ap" if has_apply else "cpu_wr"

    requests = [deque() for _ in range(4)]
    open_commands: list[dict | None] = [None, None, None, None]
    commands: list[dict] = []
    counters = Counter()

    for seq, event in enumerate(events):
        kind = event.get("t")
        if kind not in {"cpu_wr", "cpu_ap", "spc_rd", "spc_wr", "cpu_rd"}:
            continue
        port = _hexval(event.get("adr", 0)) & 3
        value = _hexval(event.get("val", 0)) & 0xFF
        sample = _ival(event.get("s", 0))
        frame = _ival(event.get("aux", 0))
        counters[kind] += 1

        if has_apply and kind == "cpu_wr":
            requests[port].append(
                {"sample": sample, "frame": frame, "value": value, "seq": seq}
            )
            continue

        if kind == mutation_type:
            request = None
            if has_apply:
                queue = requests[port]
                match_at = None
                for index, candidate in enumerate(queue):
                    if candidate["value"] == value:
                        match_at = index
                        break
                if match_at is not None:
                    for _ in range(match_at + 1):
                        request = queue.popleft()

            previous = open_commands[port]
            if previous is not None:
                previous["fate"] = "LOST"
                previous["replaced_by"] = {
                    "value": value,
                    "frame": frame,
                    "sample": sample,
                    "seq": seq,
                }

            command = None
            if value != 0:
                command = {
                    "port": port,
                    "value": value,
                    "value_hex": f"0x{value:02X}",
                    "frame": frame,
                    "sample": sample,
                    "seq": seq,
                    "request_frame": request["frame"] if request else None,
                    "request_sample": request["sample"] if request else None,
                    "apply_latency_samples": (
                        sample - request["sample"] if request else None
                    ),
                    "fate": "PENDING",
                    "seen_frame": None,
                    "seen_sample": None,
                    "seen_latency_samples": None,
                    "replaced_by": None,
                }
                commands.append(command)
            open_commands[port] = command
            continue

        if kind == "spc_rd":
            command = open_commands[port]
            if command is not None and value == command["value"]:
                command["fate"] = "SEEN"
                command["seen_frame"] = frame
                command["seen_sample"] = sample
                command["seen_latency_samples"] = sample - command["sample"]
                open_commands[port] = None

    fates = Counter(command["fate"] for command in commands)
    by_port = {}
    for port in range(4):
        rows = [command for command in commands if command["port"] == port]
        by_port[str(port)] = {
            "commands": len(rows),
            "fates": dict(sorted(Counter(row["fate"] for row in rows).items())),
            "values": dict(
                sorted(Counter(row["value_hex"] for row in rows).items())
            ),
        }

    return {
        "schema_version": 1,
        "has_apply_events": has_apply,
        "mutation_type": mutation_type,
        "event_type_counts": dict(sorted(counters.items())),
        "candidate_command_count": len(commands),
        "fates": dict(sorted(fates.items())),
        "ports": by_port,
        "commands": commands,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("events_json", type=Path)
    ap.add_argument(
        "--events-key",
        default="events",
        help="key containing the debug-server audio event list",
    )
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    payload = json.loads(args.events_json.read_text(encoding="utf-8"))
    events = payload[args.events_key] if isinstance(payload, dict) else payload
    if not isinstance(events, list):
        raise SystemExit("audio event input must resolve to a list")

    report = analyze(events)
    print(
        f"commands={report['candidate_command_count']} "
        f"fates={report['fates']} "
        f"events={report['event_type_counts']}"
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
