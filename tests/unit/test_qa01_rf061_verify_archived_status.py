"""ROM-free adversarial executable qualification for the RF061 ZIP verifier."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_rf061_verify_archived_status as m


class RF061Archive(unittest.TestCase):
    def make_zip(self, root: Path, *, mutant: str = "") -> tuple[Path, str]:
        originals = []
        native = []
        ordinal = 0
        for frame in m.FRAMES:
            pc = "82D4F0" if frame in (1017, 1019, 1021, 1023) else "82D4EE"
            stack = "26" + pc[4:6] + pc[2:4] + "8226"
            originals.append(
                f"QA01RF044ORIGNMI f={frame} f1={frame} pc={pc}"
                f" S0=01F0 S1=01EC old=8197005526 new={stack}")
            originals.append(
                f"QA01RF045ORIGSTACK f={frame} v=225 h=5 kind=pullB"
                " addr=01ED width=1 value=0026 sp0=01EC sp1=01ED pc=80:B0EB")
            def add(stage, **kwargs):
                nonlocal ordinal
                ordinal += 1
                native.append("QA01RF047NATIVE seq=%d stage=%s f=%d %s" % (
                    ordinal, stage, frame,
                    " ".join(f"{k}={v}" for k, v in kwargs.items())))
            add("entry", resume="82D4EE", S="01F0")
            add("after_push", resume="82D4EE", S="01EC", stack="26EED482")
            add("read", bank="00", addr="01ED", width=1, value="0026", nmi=1)
            add("compiled_rti", S="01F0")
            add("handler_return", resume="82D4EE", S="01F0")
        originals.extend("QA01RF045ORIGSTACK f=1025 kind=pushW" for _ in range(1806 - 9))
        originals.extend("QA01RF044ORIGBUS f=1025 kind=wb" for _ in range(903))
        for _ in range(2705 - 9):
            ordinal += 1
            native.append(f"QA01RF047NATIVE seq={ordinal} stage=read f=1025"
                          " bank=00 addr=01F1 width=1 value=0000 nmi=0")
        if mutant == "status":
            native[2] = native[2].replace("value=0026", "value=0027")
        if mutant == "sequence":
            native[3] = native[3].replace("seq=4 ", "seq=3 ")
        if mutant == "source":
            originals[0] = originals[0].replace("new=26F0D48226", "new=26EED48226")
        samples = []
        for i in range(78):
            count = 0 if i < 51 else (92 if i == 51 else 0)
            # Distribute all 92 unequal bytes across exactly 27 unequal rows.
            if i >= 51:
                count = 3 if i < 77 else 14
            samples.append({
                "original_native_full_wram_byte_difference": {
                    "full_wram_bytes_per_guest": 131072,
                    "every_byte_compared": True,
                    "excluded_byte_count": 1 if mutant == "mask" and i == 0 else 0,
                    "differing_byte_count": count,
                    "byte_exact": count == 0,
                    "release_complete_event_credit": 0,
                }})
        # 26*3 + 14 = 92; 51 exact and 27 unequal observations.
        producer = {
            "rom_sha256": "a" * 64,
            "original_movie_sha256": "b" * 64,
            "input_sha256": "c" * 64,
            "native_executable_sha256": "d" * 64,
            "reference_core_sha256": "e" * 64,
            "zoo_race_mesh": {
                "mesh_checkpoint_count": 78,
                "raw_byte_exact_sample_count": 51,
                "masked_or_excluded_wram_bytes": 0,
                "samples": samples,
            },
        }
        decision = {"source_sha": "f" * 40, "disposition": "strict_candidate",
                    "release_credit": 0}
        p = root / "synthetic.zip"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr(m.SOURCE, "\n".join(originals) + "\n")
            z.writestr(m.NATIVE, "\n".join(native) + "\n")
            z.writestr("producer-report.json", json.dumps(producer))
            z.writestr("case-result.json", json.dumps(decision))
        return p, hashlib.sha256(p.read_bytes()).hexdigest()

    def test_bounded_nine_status_reads_and_never_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            case, sha = self.make_zip(Path(tmp))
            actual = m.verify(case, expected_sha=sha)
            self.assertEqual(actual["verified_real_status_reads_matching"], 9)
            self.assertEqual(actual["native_real_bus_helper_reads"], 2705)
            self.assertEqual(actual["original_resume_counts"],
                             {"82D4F0": 4, "82D4EE": 5})
            self.assertFalse(actual["first_consumed_different_byte_proven"])
            self.assertFalse(actual["causal_window_eligible"])
            self.assertEqual(actual["complete_USA_events_accepted"], 0)

    def test_no_synthetic_or_wrong_identity_as_real_rf054(self):
        with tempfile.TemporaryDirectory() as tmp:
            case, sha = self.make_zip(Path(tmp))
            with self.assertRaisesRegex(ValueError, "SHA256"):
                m.verify(case)  # only the real pinned RF054 SHA is admissible by default
            with self.assertRaisesRegex(ValueError, "SHA256"):
                m.verify(case, expected_sha="0" * 64)

    def test_status_source_sequence_and_mask_mutations_fail(self):
        for mutation, failure in (
            ("status", "status consumer"),
            ("source", "actual NMI stack"),
            ("sequence", "ordinal"),
            ("mask", "full-WRAM"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                case, sha = self.make_zip(Path(tmp), mutant=mutation)
                with self.assertRaisesRegex(ValueError, failure):
                    m.verify(case, expected_sha=sha)


if __name__ == "__main__":
    unittest.main()
