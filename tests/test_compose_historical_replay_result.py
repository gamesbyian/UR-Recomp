#!/usr/bin/env python3
"""ROM-free regression for tools/compose_historical_replay_result.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "compose_historical_replay_result.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        meta = td / "meta.json"
        trace = td / "trace.json"
        ref = td / "reference.tsv"
        native = td / "native.json"
        out = td / "result.json"

        meta.write_text(json.dumps({
            "path": "synthetic.smv",
            "sample_count": 100,
            "event_runs": 4,
            "reset_anchored": True,
            "emitted_sram_size": 8192,
        }))
        trace.write_text(json.dumps({
            "first_in_race_frame": 10,
            "first_race_results_frame": 20,
        }))
        ref.write_text(
            "10\tmenu=0x00\tinRace=0x01\ttrack=0\tx=1\ty=2\tvx=3\tvy=4\tair=0\tpitch=5\n"
            "20\tmenu=0x99\tinRace=0x00\ttrack=0\tx=6\ty=7\tvx=8\tvy=9\tair=0\tpitch=10\n"
        )
        native.write_text(json.dumps({
            "snapshots": [
                "SNAP 10 menu=00 inRace=01 track=0 x=1 y=2 vx=3 vy=4 air=0 pitch=5",
                "SNAP 20 menu=99 inRace=00 track=0 x=6 y=7 vx=8 vy=9 air=0 pitch=10",
            ]
        }))

        subprocess.run([
            sys.executable, str(TOOL),
            "--smv-meta", str(meta),
            "--trace-summary", str(trace),
            "--reference-tsv", str(ref),
            "--native-json", str(native),
            "--out", str(out),
        ], check=True)

        result = json.loads(out.read_text())
        assert result["shared_sampled_frames"] == [10, 20]
        assert result["sampled_mismatch_count"] == 0
        assert result["sampled_native_reference_match"] is True
        assert result["native_in_race_at_reference_entry"] is True
        assert result["native_results_at_reference_results"] is True

        payload = json.loads(native.read_text())
        payload["snapshots"][1] = (
            "SNAP 20 menu=16 inRace=00 track=0 x=6 y=7 vx=8 vy=9 air=0 pitch=10"
        )
        native.write_text(json.dumps(payload))
        subprocess.run([
            sys.executable, str(TOOL),
            "--smv-meta", str(meta),
            "--trace-summary", str(trace),
            "--reference-tsv", str(ref),
            "--native-json", str(native),
            "--out", str(out),
        ], check=True)
        result = json.loads(out.read_text())
        assert result["sampled_mismatch_count"] == 1
        assert result["first_sampled_mismatch_frame"] == 20
        assert result["native_results_at_reference_results"] is False
        assert result["sampled_native_reference_match"] is False

    print("PASS: historical replay composer transition and mismatch contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
