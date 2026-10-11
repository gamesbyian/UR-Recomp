"""Causal original-PPU 2P countdown protection is stricter than RGB guessing."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_baldosa_2p_countdown_hd_foreground_guard import (
    verify, WIDTH, HEIGHT, FRAME,
)


def pam(data, width, height):
    return (f"P7\nWIDTH {width}\nHEIGHT {height}\nDEPTH 4\nMAXVAL 255\n"
            "TUPLTYPE RGB_ALPHA\nENDHDR\n").encode() + data


class CoveredRacerHDOverpaintTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stock = root / "stock" / f"ur-baldosa-ws342-{FRAME:06d}.pam"
        self.removed = root / "removed" / f"ur-baldosa-ws342-{FRAME:06d}.pam"
        self.sources = {
            slot: root / f"source{slot}" /
                  f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam"
            for slot in (96, 97)
        }
        self.candidate = root / "candidate" / "candidate-4x.pam"
        self.evidence = root / "proof.json"
        self.density = 4
        self.full = bytearray(bytes((10, 20, 30, 255)) * WIDTH * HEIGHT)
        self.alpha = {slot: bytearray(WIDTH * HEIGHT * 4) for slot in (96, 97)}
        # Both emit distinct pixels and also one shared coordinate.
        self.pixels = [(104, 159), (105, 159), (106, 159)]
        for x, y in self.pixels:
            off = 4 * (y * WIDTH + x)
            self.full[off:off + 4] = bytes((57, 57, 255, 255))
        for slot, xs in ((96, (104, 105)), (97, (105, 106))):
            for x in xs:
                off = 4 * (159 * WIDTH + x)
                self.alpha[slot][off:off + 4] = bytes((slot, 55, 50, 255))
        self.original = bytes(self.full)
        self.counterfactual = self.original
        self.presented = self.scale(self.original, self.density)
        self.write_all()

    @staticmethod
    def scale(src, density):
        pixels = memoryview(src)
        out = bytearray(WIDTH * HEIGHT * density * density * 4)
        out_w = WIDTH * density
        for y in range(HEIGHT):
            for x in range(WIDTH):
                px = pixels[4 * (y * WIDTH + x):4 * (y * WIDTH + x) + 4]
                for sub_y in range(density):
                    row = 4 * ((y * density + sub_y) * out_w + x * density)
                    out[row:row + 4 * density] = px.tobytes() * density
        return bytes(out)

    def write_all(self):
        for p in [self.stock, self.removed, self.candidate, *self.sources.values()]:
            p.parent.mkdir(parents=True, exist_ok=True)
        self.stock.write_bytes(pam(self.original, WIDTH, HEIGHT))
        self.removed.write_bytes(pam(self.counterfactual, WIDTH, HEIGHT))
        for slot in (96, 97):
            self.sources[slot].write_bytes(pam(self.alpha[slot], WIDTH, HEIGHT))
        self.candidate.write_bytes(
            pam(self.presented, WIDTH * self.density, HEIGHT * self.density))
        h = lambda d: hashlib.sha256(d).hexdigest()
        self.evidence.write_text(json.dumps({
            "schema_version": 1,
            "status": "recovered-authentic-native-ppu-two-slot-removal-zero-final-difference",
            "native_guest_frame": FRAME,
            "stock_native_source_full_raster": [WIDTH, HEIGHT],
            "actual_native_pair_removed": [96, 97],
            "whole_original_rgba_byte_exact_identical": True,
            "stock_vs_pair_guest_crc_cmp_in_native_workflow_passed": True,
            "source96_97_native_source_report_status": "passed",
            "final_original_changed_rgba_pixels_on_pair_deletion": 0,
            "final_original_changed_outside_emitted_original_source": 0,
            "expected_full_guest_crc_entries_per_native_route": 2473,
            "authorized_hd_widescreen_or_4x_art": False,
            "safe_to_erase_stock_2p_racers_in_host": False,
            "stock_full_original_rgba_sha256": h(self.original),
            "paired_deletion_full_original_rgba_sha256": h(self.counterfactual),
            "source96_original_rgba_sha256": h(self.alpha[96]),
            "source97_original_rgba_sha256": h(self.alpha[97]),
            "source96_original_alpha_pixels": 2,
            "source97_original_alpha_pixels": 2,
            "emitted_source_alpha_sum_counting_pair_overlap_twice": 4,
            "distinct_original_source_coordinates": 3,
            "distinct_original_source_coordinates_covered_by_final_blue": 3,
        }), encoding="utf-8")

    def check(self):
        return verify(self.stock, self.sources[96], self.sources[97],
                      self.removed, self.candidate, self.evidence, self.density)

    def test_exact_4x_original_protects_all_48_countdown_subpixels(self):
        out = self.check()
        self.assertEqual(out["status"],
                         "preserved-causally-hidden-original-countdown-source")
        self.assertEqual(out["protected_logical_original_coordinates"], 3)
        self.assertEqual(out["protected_output_subpixels_checked"], 48)
        self.assertEqual(out["unauthorized_candidate_subpixel_overpaints"], 0)
        self.assertFalse(out["general_2p_remastered_and_art_likeness_approved"])
        self.assertFalse(out["candidate_process_or_full_guest_event_authenticated_by_this_check"])

    def test_one_4x_subpixel_of_hidden_racer_fails(self):
        x, y = self.pixels[1]
        off = 4 * ((y * 4 + 2) * (WIDTH * 4) + x * 4 + 3)
        altered = bytearray(self.presented)
        altered[off] ^= 1
        self.presented = bytes(altered)
        self.write_all()
        out = self.check()
        self.assertEqual(out["unauthorized_candidate_subpixel_overpaints"], 1)
        self.assertEqual(out["bounded_overpaint_xy_subpixel_examples"],
                         [[x, y, 3, 2]])
        self.assertEqual(out["status"], "failed-countdown-foreground-overpaint")

    def test_candidate_may_change_outside_proven_hidden_racer_pixels(self):
        pos = 4 * ((45 * 4) * WIDTH * 4 + 14 * 4)
        altered = bytearray(self.presented)
        altered[pos] ^= 7
        self.presented = bytes(altered)
        self.write_all()
        self.assertEqual(self.check()["unauthorized_candidate_subpixel_overpaints"], 0)

    def test_a_1x_candidate_also_checks_full_original_rgba(self):
        self.density = 1
        self.presented = bytes(self.original)
        self.write_all()
        self.assertEqual(self.check()["protected_output_subpixels_checked"], 3)

    def test_forged_original_or_removed_different_raster_rejected(self):
        self.counterfactual = bytes([1]) + self.counterfactual[1:]
        self.write_all()
        with self.assertRaisesRegex(ValueError, "native Original changed"):
            # Update hash to show even a self-consistent forged report
            # cannot override the actual native before/after mismatch.
            report = json.loads(self.evidence.read_text())
            report["paired_deletion_full_original_rgba_sha256"] = (
                hashlib.sha256(self.counterfactual).hexdigest())
            self.evidence.write_text(json.dumps(report))
            self.check()

    def test_native_source_bytes_must_match_signed_hashes(self):
        self.alpha[97][-8:-4] = bytes((44, 22, 16, 255))
        self.sources[97].write_bytes(pam(self.alpha[97], WIDTH, HEIGHT))
        with self.assertRaisesRegex(ValueError, "SHA mismatches"):
            self.check()

    def test_report_must_keep_guest_crc_and_no_art_admission(self):
        for key, value in [
            ("expected_full_guest_crc_entries_per_native_route", 5447),
            ("safe_to_erase_stock_2p_racers_in_host", True),
            ("authorized_hd_widescreen_or_4x_art", True),
            ("whole_original_rgba_byte_exact_identical", False),
            ("actual_native_pair_removed", [98, 99]),
        ]:
            old = json.loads(self.evidence.read_text())
            report = dict(old)
            report[key] = value
            self.evidence.write_text(json.dumps(report))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "proof is incomplete"):
                self.check()
            self.evidence.write_text(json.dumps(old))

    def test_bad_density_and_alias_or_malformed_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError, "1x..4x"):
            verify(self.stock, self.sources[96], self.sources[97],
                   self.removed, self.candidate, self.evidence, 5)
        with self.assertRaisesRegex(ValueError, "independent"):
            verify(self.stock, self.sources[96], self.sources[97],
                   self.removed, self.stock, self.evidence, 1)
        self.candidate.write_bytes(b"not-a-PAM")
        with self.assertRaisesRegex(ValueError, "exact verified dimensions"):
            self.check()


if __name__ == "__main__":
    unittest.main()
