import json
from pathlib import Path
import subprocess
import sys


def test_summarize_window_seam_detects_two_window_xor(tmp_path: Path):
    regs = tmp_path / "race.regs.json"
    regs.write_text(json.dumps({
        "frame_tag": 123,
        "ppu": {
            "tm": "11", "ts": "02", "tmw": "01", "tsw": "00",
            "cgwsel": "20", "cgadsub": "41",
            "fixed_color": {"r": 1, "g": 2, "b": 3},
            "window": {
                "w1_left": 10, "w1_right": 40, "w2_left": 80, "w2_right": 120,
                "w12sel": "AA", "w34sel": "00", "wobjsel": "00",
                "wbglog": "02", "wobjlog": "00",
                "layers": [
                    {"w1_enable": 1, "w1_inside": 1, "w2_enable": 1, "w2_inside": 0, "logic": 2},
                    {"w1_enable": 0, "w1_inside": 0, "w2_enable": 0, "w2_inside": 0, "logic": 0},
                    {"w1_enable": 0, "w1_inside": 0, "w2_enable": 0, "w2_inside": 0, "logic": 0},
                    {"w1_enable": 0, "w1_inside": 0, "w2_enable": 0, "w2_inside": 0, "logic": 0},
                    {"w1_enable": 0, "w1_inside": 0, "w2_enable": 0, "w2_inside": 0, "logic": 0},
                    {"w1_enable": 0, "w1_inside": 0, "w2_enable": 0, "w2_inside": 0, "logic": 0},
                ],
            },
        },
    }))
    out = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, "tools/summarize_window_seam.py", str(regs), "--json-out", str(out)],
        check=True,
    )
    report = json.loads(out.read_text())
    assert report["xor_checkpoints"] == [{"checkpoint": "race", "layers": ["BG1"]}]
    assert report["checkpoints"][0]["layers"][0]["logic_name"] == "XOR"
