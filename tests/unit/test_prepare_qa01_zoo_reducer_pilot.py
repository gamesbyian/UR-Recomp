"""ROM-free negative contracts for source-earned Zoo reducer intake."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_qa01_zoo_reducer_pilot as intake
from controller_input import load_controller_runs
from qa01_reducer_paired_oracle import validate as validate_oracle


def actual_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ZooReducerIntakeTests(unittest.TestCase):
    SOURCE = "a" * 40

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.case = self.root / "case"
        self.replay = self.case / "replay"
        self.reference = self.replay / "ref"
        self.native = self.replay / "native"
        self.binaries = self.root / "binaries"
        for directory in (self.reference, self.native, self.binaries):
            directory.mkdir(parents=True)
        self.rom = self.root / "test-only.rom"
        self.movie = self.root / "test-only.smv"
        self.rom.write_bytes(b"SYNTHETIC ROM REPLACEMENT ONLY")
        self.movie.write_bytes(b"SYNTHETIC MOVIE REPLACEMENT ONLY")
        self.seed = self.case / "anchored.srm"
        self.seed.write_bytes(b"S" * 8192)
        self.seed_sha = actual_hash(self.seed)
        for name in ("native", "snesref", "snes9x_libretro.so"):
            (self.binaries / name).write_bytes(name.encode())
        self.script = self.replay / "complete.script"
        self.script.write_text("until 009F == 16 8000\ndump race-entered\nwait 5039\n"
                               "dump scene-05039\nwait 1\ndump scene-05040\nquit\n")
        self.ref_input = self.replay / "ref.input"
        self.native_input = self.replay / "pinned-baldosa.input"
        self.ref_input.write_text("1017:10:001\n1030:5:004\n")
        self.native_input.write_text("1019:10:001\n1032:5:004\n")
        self.ref_log = self.replay / "reference.log"
        self.nat_log = self.replay / "native.log"
        self.ref_log.write_text("script f=1017 dump race-entered\n"
                                "script f=6056 dump scene-05039\n"
                                "script f=6057 dump scene-05040\n")
        self.nat_log.write_text("script f=1019 dump race-entered\n"
                                "script f=6058 dump scene-05039\n"
                                "script f=6059 dump scene-05040\n")
        def image(ptr, counter):
            out = bytearray(131072)
            out[0x009F], out[0x00CE], out[0x0313] = 0x16, 1, 1
            out[0x63], out[0x69] = ptr, counter
            return bytes(out)
        before = image(0xB0, 0x9F)
        (self.reference / "scene-05039.wram.bin").write_bytes(before)
        (self.native / "scene-05039.wram.bin").write_bytes(before)
        (self.reference / "scene-05040.wram.bin").write_bytes(image(0x73, 0xBE))
        (self.native / "scene-05040.wram.bin").write_bytes(image(0x4D, 0x97))
        observer_hash = actual_hash(self.script)
        control = {
            "repository_source_sha": self.SOURCE,
            "reference_script_sha256": observer_hash,
            "native_script_sha256": observer_hash,
            "reference_supplied_input_sha256": actual_hash(self.ref_input),
            "native_supplied_input_sha256": actual_hash(self.native_input),
            "reference_guest_log_sha256": actual_hash(self.ref_log),
            "native_guest_log_sha256": actual_hash(self.nat_log),
        }
        self.producer = self.root / "producer.json"
        self.producer.write_text(json.dumps({
            "admission": "investigative candidate; not a release-ledger pass",
            "name": "zoom-zoo", "course_id": "course:02",
            "native_backend": "pinned-baldosa",
            "rom_sha256": intake.ROM_USA_SHA256,
            "original_movie_sha256": intake.SOURCE_MOVIE_SHA256,
            "source_sram_sha256": self.seed_sha,
            "native_executable_sha256": actual_hash(self.binaries / "native"),
            "reference_core_sha256": actual_hash(self.binaries / "snes9x_libretro.so"),
            "reference_script_sha256": observer_hash,
            "reference_entry": 1017, "native_entry": 1019,
            "native_frame_shift": 2,
            "qa01_capture_ab_control": control,
        }))
        self.real_sha = intake.sha

    def isolated_sha(self, path):
        if path == self.rom:
            return intake.ROM_USA_SHA256
        if path == self.movie:
            return intake.SOURCE_MOVIE_SHA256
        return self.real_sha(path)

    def intake(self):
        with mock.patch.object(intake, "sha", side_effect=self.isolated_sha):
            return intake.prepare(
                producer=self.producer, case=self.case,
                binaries=self.binaries, rom=self.rom, movie=self.movie,
                source_sha=self.SOURCE, expected_sram_sha=self.seed_sha)

    def test_qualified_producer_constructs_exact_private_oracle(self):
        candidate, manifest, receipt = self.intake()
        self.assertIn(b"1017:10:001", candidate)
        self.assertEqual(receipt["current_first_sound_mismatch_offsets"], [0x63, 0x69])
        self.assertEqual(manifest["guest_clocks"]["native_frame_shift"]
                         if "native_frame_shift" in manifest["guest_clocks"] else
                         manifest["guest_clocks"]["native_entry_frame"] -
                         manifest["guest_clocks"]["reference_entry_frame"], 2)
        self.assertEqual(manifest["discrepancy"]["original_byte"], 0x73)
        self.assertEqual(manifest["discrepancy"]["native_byte"], 0x4D)
        self.assertEqual(manifest["after_target_pair"], [
            {"offset": 0x63, "original_byte": 0x73, "native_byte": 0x4D},
            {"offset": 0x69, "original_byte": 0xBE, "native_byte": 0x97},
        ])
        self.assertEqual(manifest["pre_target"]["dump"], "scene-05039.wram.bin")
        self.assertEqual(manifest["pre_target"]["sha256"],
                         actual_hash(self.reference / "scene-05039.wram.bin"))
        self.assertEqual(receipt["release_gate_credit"], 0)
        self.assertEqual(manifest["native_xvfb"], True)
        # The synthetic ROM bypass is limited to the real ROM hash check. All
        # remaining file/command checks are authentic production validation.
        with mock.patch("qa01_reducer_paired_oracle.file_sha",
                        side_effect=lambda path: intake.ROM_USA_SHA256
                        if Path(path) == self.rom else actual_hash(Path(path))):
            validate_oracle(manifest)

    def test_derived_checkpoint_script_stops_before_result_gate(self):
        from qa01_reducer_paired_oracle import checkpoint_only_observer
        self.script.write_text("until 009F == 16 8000\ndump race-entered\n"
                               "wait 5039\ndump scene-05039\nwait 1\n"
                               "dump scene-05040\nuntil 009F == BC 9000\n"
                               "dump result-onset\nquit\n")
        source = self.script.read_text()
        derived = checkpoint_only_observer(source, "scene-05040")
        self.assertEqual(derived, source.split("until 009F == BC 9000")[0] +
                         "quit\n")
        self.assertEqual(derived.count("dump scene-05039"), 1)
        self.assertEqual(derived.count("dump scene-05040"), 1)
        self.assertNotIn("9000", derived)
        with self.assertRaisesRegex(ValueError, "one authentic checkpoint"):
            checkpoint_only_observer(source, "result-unknown")

    def test_preceding_frame_must_be_full_byte_identical(self):
        image = bytearray((self.native / "scene-05039.wram.bin").read_bytes())
        image[0x01EE] = 1
        (self.native / "scene-05039.wram.bin").write_bytes(image)
        with self.assertRaisesRegex(ValueError, "full-byte identical"):
            self.intake()

    def test_new_unrelated_disparity_is_not_retconned_as_zoo_sound(self):
        image = bytearray((self.native / "scene-05040.wram.bin").read_bytes())
        image[0x01EE] = 1
        (self.native / "scene-05040.wram.bin").write_bytes(image)
        with self.assertRaisesRegex(ValueError, "different.*discrepancy"):
            self.intake()

    def test_native_input_must_equal_source_shift_not_merely_same_sha(self):
        self.native_input.write_text("1019:10:001\n1040:5:004\n")
        report = json.loads(self.producer.read_text())
        report["qa01_capture_ab_control"]["native_supplied_input_sha256"] = actual_hash(self.native_input)
        self.producer.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "host-shifted stream"):
            self.intake()

    def test_wrong_guest_observation_phase_is_not_accepted(self):
        self.nat_log.write_text("script f=1019 dump race-entered\nscript f=6060 dump scene-05040\n")
        report = json.loads(self.producer.read_text())
        report["qa01_capture_ab_control"]["native_guest_log_sha256"] = actual_hash(self.nat_log)
        self.producer.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "source-earned Zoo"):
            self.intake()

    def test_wrong_historical_seed_is_not_accepted(self):
        self.seed.write_bytes(b"T" * 8192)
        with self.assertRaisesRegex(ValueError, "source SRAM"):
            self.intake()

    def test_noncanonical_rom_provenance_refused(self):
        self.rom.write_bytes(b"WRONG ROM PROVENANCE")
        with mock.patch.object(intake, "sha",
                               side_effect=lambda path: ("f" * 64 if path == self.rom
                               else self.isolated_sha(path))):
            with self.assertRaisesRegex(ValueError, "wrong original retail ROM"):
                intake.prepare(producer=self.producer, case=self.case,
                    binaries=self.binaries, rom=self.rom, movie=self.movie,
                    source_sha=self.SOURCE, expected_sram_sha=self.seed_sha)

    def test_malformed_or_partial_checkpoint_rejected(self):
        (self.native / "scene-05040.wram.bin").write_bytes(bytes(513))
        with self.assertRaisesRegex(ValueError, "128 KiB"):
            self.intake()


if __name__ == "__main__":
    unittest.main()
