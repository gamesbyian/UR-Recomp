"""Independent archival QA consistency, not Windows or gameplay acceptance."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from tools import audit_windows_smoke_artifact as audit


def _wrap(path: Path, payloads: dict[str, bytes]):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, payload in payloads.items():
            z.writestr(name, payload)


class HistoricalArchivedWindowsEvidenceRecordTests(unittest.TestCase):
    def test_retained_historical_receipt_is_deliberately_non_releasing(self):
        from tools.evidence_contract import validate_envelope
        path = Path(__file__).resolve().parents[2] / (
            "analysis/evidence/windows-smoke-38095271085-archived-consistency.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(data), [])
        self.assertEqual(data["outcome"], "inconclusive")
        self.assertEqual(data["subject"]["run_id"], 38095271085)
        self.assertEqual(data["subject"]["source_revision_claim"],
                         "1afe05edee2617c6a5b8cf67fce806fbfe939bf2")
        self.assertEqual(data["subject"]["inner_portable_zip_sha256"],
                         "f0401d21c9e8286794a5d247a2b50377470a74acb1148faa7b9827cf24b4969e")
        self.assertEqual(data["metrics"]["reported_real_joysticks"], 0)
        self.assertEqual(data["metrics"]["reported_sdl_audio_driver"], "dummy")
        self.assertTrue(data["metrics"]["synthetic_controller_label_observed"])
        for gate in ("independent_candidate_approved",
                     "current_native_1p_2p_complete", "physical_hardware_verified"):
            self.assertIs(data["metrics"][gate], False)


class WindowsSmokeArtifactArchiveTests(unittest.TestCase):
    def prepare(self, root: Path):
        inner = b"example archive only, not a ROM"
        digest = hashlib.sha256(inner).hexdigest()
        checksum = f"{digest}  UR-Recomp-Windows-x64.zip\n".encode()
        manifest = {"source_revision": "a" * 40, "files": []}
        portable = root / "windows-portable-transport.zip"
        smoke = root / "windows-smoke-transport.zip"
        _wrap(portable, {
            "UR-Recomp-Windows-x64.zip": inner,
            "UR-Recomp-Windows-x64.zip.sha256": checksum,
            "Test-URRecompPortable.ps1": b"synthetic test file",
        })
        _wrap(smoke, {
            "UR-Recomp-Windows-x64.zip": inner,
            "UR-Recomp-Windows-x64.zip.sha256": checksum,
            audit.SMOKE_MANIFEST: json.dumps(manifest).encode(),
            "qa09-root-win32.log": (
                b"SDL init ok: video=windows audio=dummy\n"
                b"[Gamepad] SDL reports 0 joystick(s)\n"
                b"UR_CONTROLLER SEAT_CONNECTED seat=1 name=UR HOTPLUG ACCEPTA\n"
            ),
            "package-race-result.log": b"UR_RUN_RECORD CAPTURED\n",
            "standalone-windows-verifier.log": b"UR_PORTABLE_MANIFEST_VERIFIED\n",
        })
        return portable, smoke, inner, checksum, manifest

    def test_good_cross_archive_report_never_promotes_release(self):
        with tempfile.TemporaryDirectory() as temp:
            portable, smoke, _, _, manifest = self.prepare(Path(temp))
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest) as verify:
                result = audit.audit(portable, smoke)
            self.assertEqual(verify.call_count, 1)
            self.assertEqual(result["outcome"], "inconclusive")
            self.assertEqual(result["metrics"]["qa09_reported_joystick_count"], 0)
            self.assertEqual(result["metrics"]["qa09_audio_driver"], "dummy")
            self.assertTrue(result["metrics"]["qa09_synthetic_pad_label_observed"])
            self.assertFalse(result["metrics"]["physical_hardware_verified"])
            self.assertNotIn("synthetic test file", json.dumps(result))

    def test_external_candidate_pins_are_paired_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            portable, smoke, inner, _, manifest = self.prepare(Path(temp))
            good_digest = hashlib.sha256(inner).hexdigest()
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest):
                good = audit.audit(
                    portable, smoke, expected_source="a" * 40,
                    expected_zip_sha256=good_digest,
                )
                self.assertTrue(good["metrics"]["nominated_candidate_pins_matched"])
                self.assertEqual(good["outcome"], "inconclusive")
                self.assertFalse(good["metrics"]["independent_candidate_approved"])
                with self.assertRaisesRegex(ValueError, "both exact candidate pins"):
                    audit.audit(portable, smoke, expected_source="a" * 40)
                with self.assertRaisesRegex(ValueError, "candidate source pin"):
                    audit.audit(portable, smoke, expected_source="main",
                                expected_zip_sha256=good_digest)
                with self.assertRaisesRegex(ValueError, "nominated candidate"):
                    audit.audit(portable, smoke, expected_source="a" * 40,
                                expected_zip_sha256="0" * 64)
                with self.assertRaisesRegex(ValueError, "archived source differs"):
                    audit.audit(portable, smoke, expected_source="b" * 40,
                                expected_zip_sha256=good_digest)

    def test_real_qa09_truncated_synthetic_pad_marker_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable, smoke, inner, checksum, manifest = self.prepare(root)
            with zipfile.ZipFile(smoke, "r") as old:
                original = {name: old.read(name) for name in old.namelist()}
            original["qa09-root-win32.log"] = (
                b"[host +0.031s] SDL init ok: video=windows audio=dummy\n"
                b"[Gamepad] SDL reports 0 joystick(s). enable_gamepad=[1,1]\n"
                b"UR_CONTROLLER SEAT_CONNECTED seat=1 name=GENERIC PHYSICAL\n"
            )
            _wrap(smoke, original)
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest):
                report = audit.audit(portable, smoke)
            self.assertFalse(report["metrics"]["qa09_synthetic_pad_label_observed"])
            self.assertEqual(report["metrics"]["qa09_reported_joystick_count"], 0)

    def test_wrong_independent_transport_sidecar_fails_before_package_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            portable, smoke, inner, _, manifest = self.prepare(Path(temp))
            with zipfile.ZipFile(portable, "w") as z:
                z.writestr("UR-Recomp-Windows-x64.zip", inner)
                z.writestr("UR-Recomp-Windows-x64.zip.sha256", b"0" * 64)
                z.writestr("Test-URRecompPortable.ps1", b"test")
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest) as verify:
                with self.assertRaisesRegex(ValueError, "sidecar does not match"):
                    audit.audit(portable, smoke)
            verify.assert_not_called()

    def test_smoke_replacement_or_manifest_divergence_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable, smoke, inner, sidecar, manifest = self.prepare(root)
            _wrap(smoke, {
                "UR-Recomp-Windows-x64.zip": b"replaced",
                "UR-Recomp-Windows-x64.zip.sha256": sidecar,
                audit.SMOKE_MANIFEST: json.dumps(manifest).encode(),
            })
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest):
                with self.assertRaisesRegex(ValueError, "smoke package bytes differ"):
                    audit.audit(portable, smoke)
            _wrap(smoke, {
                "UR-Recomp-Windows-x64.zip": inner,
                "UR-Recomp-Windows-x64.zip.sha256": sidecar,
                audit.SMOKE_MANIFEST: json.dumps({"source_revision": "b" * 40}).encode(),
            })
            with mock.patch.object(audit.package, "verify_archive", return_value=manifest):
                with self.assertRaisesRegex(ValueError, "smoke manifest differs"):
                    audit.audit(portable, smoke)

    def test_duplicate_transport_member_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable, smoke, inner, sidecar, _ = self.prepare(root)
            with zipfile.ZipFile(portable, "w") as z:
                z.writestr("UR-Recomp-Windows-x64.zip", inner)
                z.writestr("UR-Recomp-Windows-x64.zip", inner)
                z.writestr("UR-Recomp-Windows-x64.zip.sha256", sidecar)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                audit.audit(portable, smoke)


if __name__ == "__main__":
    unittest.main()
