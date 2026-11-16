#!/usr/bin/env python3
"""WIDE-07: determine whether observed green discrepancies are a deterministic LUT.

Reads already-extracted original/native paired green-channel observations.
Does not imply phase alignment or course acceptance.
"""
import argparse
import collections
import json
from pathlib import Path

def characterize(pairs):
    outputs = collections.defaultdict(set)
    counts = collections.Counter()
    for original, native in pairs:
        if not (0 <= original <= 255 and 0 <= native <= 255):
            raise ValueError("CHANNEL_OUT_OF_RANGE")
        outputs[original].add(native)
        counts[(original, native)] += 1
    conflicts = {str(k): sorted(v) for k, v in outputs.items() if len(v) > 1}
    return {
        "schema": "wide07-green-lut/1",
        "observations": sum(counts.values()),
        "distinct_original_values": len(outputs),
        "ambiguous_original_values": conflicts,
        "deterministic_on_observed_values": not bool(conflicts),
        "observed_mapping": {str(k): next(iter(v)) for k, v in sorted(outputs.items()) if len(v) == 1},
        "unobserved_original_values": [v for v in range(256) if v not in outputs],
        "course_acceptance": 0,
    }

def selftest():
    good = characterize([(105,107),(134,132),(166,165),(105,107)])
    assert good["deterministic_on_observed_values"]
    assert good["observed_mapping"] == {"105":107,"134":132,"166":165}
    assert len(good["unobserved_original_values"]) == 253
    bad = characterize([(105,107),(105,106)])
    assert not bad["deterministic_on_observed_values"]
    assert bad["ambiguous_original_values"] == {"105":[106,107]}
    try:
        characterize([(256,0)])
    except ValueError as exc:
        assert str(exc) == "CHANNEL_OUT_OF_RANGE"
    else:
        raise AssertionError("INVALID_CHANNEL_ACCEPTED")
    print("WIDE07_GREEN_LUT_SELFTEST_PASS")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pairs-json", type=Path, help="JSON array of [original_green,native_green] pairs")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        selftest()
        return
    if args.pairs_json is None:
        p.error("--pairs-json required")
    pairs = json.loads(args.pairs_json.read_text())
    result = characterize(pairs)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(output)
    print(output, end="")

if __name__ == "__main__":
    main()
