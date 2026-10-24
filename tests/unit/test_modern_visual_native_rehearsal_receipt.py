"""Fail-closed provenance guard for an independently audited old Win32 visual cohort.

This checks a *committed compact audit index*, not source PNG/P7/PE ZIP bytes.
Those original archive bytes were independently re-read to prepare the index;
any new cohort requires fresh raw-archive audit, never relabeling this receipt.
"""
import copy
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[2] / "analysis/evidence/modern-visual-native-rehearsal-39558777827.json"
SOURCE = "a87d02debb237590578fe024e0a895bef6ce67fd"
EXE = "74556a0cad1863fc8e8a656df63995a9a889840dff5b6e954f94e03a8b113d60"
ARCHIVES = {
    "size": (12327545665, "86ca95c40faaec520af2240eb0e470b1ac1f00c1d606e639789c445b8c6c96e3"),
    "navigation": (12327206809, "315c637801894623922e04f214f3dad47f65b585a4f7e9c934161dc9c4d1ec6c"),
    "title": (12327216738, "3505c377cb5f06a3a6a3b36ff679ead31f45481ad13086c15eced8e8f598e50f"),
    "authentic": (12327470974, "bb7e71241902093c2f41779eec8a4a371061407601bdba4717a44d175a935c02"),
    "root856": (12327381363, "06dc2cc24ef75e804d6af05e5550ebcaffec469753ef1bd796561c51a997c06a"),
}
EXPECTED = {
    ("root856", "root-quit", 856, 480, 342, "root"),
    ("size", "root-quit", 1280, 720, 342, "root"),
    ("size", "root-quit", 1024, 768, 256, "root"),
    ("navigation", "multiplayer-unrecorded", 1280, 720, 342, "multiplayer-unrecorded-warning"),
    ("navigation", "options-p1", 1280, 720, 342, "options"),
    ("navigation", "practice-picker", 1280, 720, 342, "practice-picker"),
    ("navigation", "profile-first-p1", 1280, 720, 342, "profile-first-saved"),
    ("navigation", "records-keyboard", 1024, 768, 256, "records-1p"),
    *(("title", route, width, height, source, stage)
      for width, height, source in ((1024, 768, 256), (1280, 720, 342))
      for route, stage in (
          ("title-still", "title-intro"),
          ("title-reduced-still", "title-intro"),
          ("title-entered-root", "root"),
          ("title-reduced-entered-root", "root"),
      )),
    ("authentic", "authentic-stock", 1280, 720, 256, "authentic-original"),
    ("authentic", "authentic-stock", 1024, 768, 256, "authentic-original"),
}

def validate(data):
    if (data.get("schema_version") != 1 or data.get("github_run") != 39558777827
            or data.get("source_checkout_sha") != SOURCE
            or data.get("source_is_current_main") is not False):
        raise ValueError("wrong historical source/run or disguised current-main approval")
    exe = data.get("windows_executable", {})
    if (exe.get("artifact_id") != 12327356500
            or exe.get("exe_sha256") != EXE
            or exe.get("zip_sha256") != "fd0b85b7d8fe989ffdaccaffa034aea4346612629e841934a5ec3c24b866cbf1"
            or exe.get("uncompressed_bytes") != 20456448
            or exe.get("format") != "Windows x64 AMD64 PE32+"):
        raise ValueError("original executable transport replaced")
    archives = data.get("original_capture_archives", {})
    if set(archives) != set(ARCHIVES) or any(
            archives[k] != {"artifact_id": aid, "zip_sha256": sha}
            for k, (aid, sha) in ARCHIVES.items()):
        raise ValueError("original archive byte references replaced")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 18:
        raise ValueError("incomplete original native capture population")
    rows = []
    for case in cases:
        if not isinstance(case, dict) or not all(
                key in case for key in ("artifact", "route", "output",
                                       "logical_source", "last_native_stage")):
            raise ValueError("missing capture evidence fields")
        output, source = case["output"], case["logical_source"]
        if (not isinstance(output, list) or len(output) != 2
                or not isinstance(source, list) or len(source) != 2):
            raise ValueError("malformed native dimensions")
        rows.append((case["artifact"], case["route"], *output,
                     source[0], case["last_native_stage"]))
        if source[1] != 224:
            raise ValueError("nonexistent source canvas height")
    if len(set(rows)) != len(rows) or set(rows) != EXPECTED:
        raise ValueError("substituted native semantic route/source or duplicated case")
    checks = data.get("independent_verifications", {})
    for key, value in (
        ("archive_download_hashes_recorded", 5),
        ("exact_matching_executable_from_original_PE_archive", True),
        ("native_successful_process_logs_sha256_match", 18),
        ("original_P7_png_byte_exact_RGBA_matches", 18),
        ("last_native_stage_checked_before_sdl_readback", True),
        ("native_fallback_source_256x224_records", True),
        ("authentic_source_P6_to_final_SDL_RGB_exact_captures", 2),
        ("wide_root_to_child_unchanged_identity_glyphs_per_case", 4670),
        ("compact_root_to_records_unchanged_identity_glyphs", 5168),
        ("windows_logs_reported_physical_joysticks", 0),
    ):
        if checks.get(key) != value:
            raise ValueError("changed observed native byte/geometry measurement: " + key)
    if checks.get("native_wide_source_342x224_open_destinations") != [
        "options", "practice-picker", "multiplayer-unrecorded-warning",
        "profile-first-saved"]:
        raise ValueError("rewritten observed native destination list")
    limits = data.get("scope_limits", {})
    if (set(limits) != {
            "no_named_p2_join", "no_locked_course", "no_earned_1p_2p_records",
            "no_hardware_controller", "no_physical_monitor",
            "no_authenticated_current_main_build", "no_human_visual_approval",
            "no_original_guest_parity", "no_4k_output",
            "formal_visual_approved", "release_gate_credit"}
            or any(value is not True for key, value in limits.items()
                   if key not in ("formal_visual_approved", "release_gate_credit"))
            or limits["formal_visual_approved"] != 0
            or limits["release_gate_credit"] != 0):
        raise ValueError("unearned human/hardware/release approval")
    return len(rows)


class NativeVisualRehearsalEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads(FILE.read_text(encoding="utf-8"))

    def test_exact_original_windows_run_remains_technical_only(self):
        self.assertEqual(validate(self.evidence), 18)

    def test_disguised_newer_source_or_archives_are_rejected(self):
        for change in ("main", "source", "zip", "executable"):
            evidence = copy.deepcopy(self.evidence)
            if change == "main":
                evidence["source_is_current_main"] = True
            elif change == "source":
                evidence["source_checkout_sha"] = "0" * 40
            elif change == "zip":
                evidence["original_capture_archives"]["navigation"]["zip_sha256"] = "0" * 64
            else:
                evidence["windows_executable"]["exe_sha256"] = "0" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(evidence)

    def test_missing_or_transposed_capture_is_rejected(self):
        for field, replacement in (
                ("route", "multiplayer-p2-named"),
                ("logical_source", [256, 224]),
                ("last_native_stage", "root")):
            evidence = copy.deepcopy(self.evidence)
            selected = next(c for c in evidence["cases"] if c["route"] == "options-p1")
            selected[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(evidence)
        evidence = copy.deepcopy(self.evidence)
        evidence["cases"][0] = copy.deepcopy(evidence["cases"][1])
        with self.assertRaises(ValueError):
            validate(evidence)

    def test_visual_and_hardware_approval_cannot_be_invented(self):
        for field, value in (
                ("no_hardware_controller", False),
                ("no_named_p2_join", False),
                ("no_human_visual_approval", False),
                ("formal_visual_approved", 18),
                ("release_gate_credit", 1)):
            evidence = copy.deepcopy(self.evidence)
            evidence["scope_limits"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    ValueError, "unearned"):
                validate(evidence)


if __name__ == "__main__":
    unittest.main()
