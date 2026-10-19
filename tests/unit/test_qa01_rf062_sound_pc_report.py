"""RF062 real-opcode/read-helper join must reject aliases and fake timing."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf062_sound_pc_report as rf


class BoundedRF062(unittest.TestCase):
    def cases(self, root: Path, *, defect: str = "") -> tuple[Path, Path, str]:
        baseline, candidate = root / "baseline.zip", root / "candidate.zip"
        producer = {
            "rom_sha256": "a" * 64,
            "original_movie_sha256": "b" * 64,
            "input_sha256": "c" * 64,
            "zoo_race_mesh": {"mesh_checkpoint_count": 78},
            "zoo_next_bowl_handoff": {"actual": 267},
            "source_terminal_followthrough": {"actual": 5163},
        }
        source = [
            "QA01RF049LDA ordinal=33703 frame=6124 v=159 h=992 pc=82:82F0"
            " d=0000 ptr=110000 y=C774 ea=11C774 a0=630D a1=63D0",
            "QA01RF050ORIGAPU seq=21 age=104485254 v=159 h=1016 port=3 val=D0",
            "QA01RF050ORIGAPU seq=22 age=104485258 v=159 h=1066 port=2 val=63",
        ]
        rows, direct = [], []
        start = 0xC589
        for i in range(656):
            seq = i + 1
            addr = start + i
            stamp = 2188739002 + (i - 491) * 540
            bank_addr = f"11{addr:04X}"
            y = f"{addr:04X}"
            a = "630D" if addr == 0xC774 else "0000"
            rows.append(f"QA01RF054NATIVEBUS kind=read8 seq={seq} frame=6124"
                        f" master={stamp} addr={bank_addr} A={a} Y={y} D=0000"
                        " dp63=00 dp64=00 dp65=11"
                        f" scope={rf.LIVE}")
            if 0xC770 <= addr <= 0xC779:
                line = (f"QA01RF062NATIVE seq={addr-0xC770+1} f=6124"
                        f" executedPC=8282F0 master={stamp} addr={bank_addr}"
                        f" value={'D0' if addr == 0xC774 else '00'} A={a}"
                        f" Y={y} D=0000 dp63=00 dp64=00 dp65=11")
                direct.append(line)
        if defect == "wrong_pc":
            direct[4] = direct[4].replace("executedPC=8282F0", "executedPC=8282F2")
        if defect == "wrong_clock":
            direct[4] = direct[4].replace("master=2188739002", "master=2188739003")
        if defect == "wrong_byte":
            direct[4] = direct[4].replace("value=D0", "value=D1")
        if defect == "gap":
            direct.pop(4)
        if defect == "original":
            source[0] = source[0].replace("ea=11C774", "ea=13C774")
        old_producer = json.loads(json.dumps(producer))
        if defect == "masked":
            producer["zoo_race_mesh"]["masked_or_excluded_wram_bytes"] = 1
        def write_zip(path, p, s, n):
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("producer-report.json", json.dumps(p))
                z.writestr("case-result.json", json.dumps({
                    "source_sha": "f"*40, "release_credit": 0,
                    "disposition": "strict_candidate"}))
                z.writestr(rf.ORIG, s)
                z.writestr(rf.NATIVE, n)
        write_zip(baseline, old_producer, "\n".join(source), "\n".join(rows))
        write_zip(candidate, producer, "\n".join(source),
                  "\n".join(rows + direct))
        return candidate, baseline, hashlib.sha256(baseline.read_bytes()).hexdigest()

    def run_fake(self, root, defect=""):
        candidate, baseline, sha = self.cases(Path(root), defect=defect)
        with mock.patch.object(rf, "BASELINE_SHA", sha):
            return rf.report(candidate, baseline)

    def test_executed_8282f0_direct_bus_reader_correlates_without_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_fake(tmp)
            self.assertEqual(result["actual_native_decoder_bound_read_count"], 10)
            self.assertEqual(result["native_reads"][4]["native_physical_operand"], "11C774")
            self.assertEqual(result["native_reads"][4]["native_real_returned_byte"], "D0")
            self.assertEqual(result["native_reads"][4]["independent_rf054_real_helper_ordinal"], 492)
            self.assertFalse(result["original_native_clock_epochs_equivalent"])
            self.assertFalse(result["first_consumed_original_native_difference_proven"])
            self.assertEqual(result["complete_USA_events_accepted"], 0)

    def test_data_time_pc_and_mask_tampering_fail_closed(self):
        for defect, reason in (
            ("wrong_pc", "decoded opcode"),
            ("wrong_clock", "matching actual RF054"),
            ("wrong_byte", "consumed byte mismatch"),
            ("gap", "missing/repeated/gapped"),
            ("original", "original real 11:C774"),
            ("masked", "strict whole-WRAM"),
        ):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError, reason):
                    self.run_fake(tmp, defect)


if __name__ == "__main__":
    unittest.main()
