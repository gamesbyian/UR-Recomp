"""ROM-free, independently pinned provisional Baldosa consumer archive QA."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import assemble_baldosa_windows_candidate as producer
import verify_baldosa_romless_candidate_qa as qa
from tests.unit.test_assemble_baldosa_windows_candidate import fake_x64_pe


def resigned(path, modify):
    with zipfile.ZipFile(path) as source:
        originals = [(item, source.read(item.filename)) for item in source.infolist()]
    with zipfile.ZipFile(path, "w") as dest:
        for entry, data in originals:
            dest.writestr(entry, modify(entry.filename, data))


class IndependentBaldosaZipQaTests(unittest.TestCase):
    def make(self, root):
        exe = root / producer.EXE
        fake_x64_pe(exe)
        zip_path = root / "provisional.zip"
        source = "a" * 40
        digest = producer.create_candidate(exe, zip_path, source)
        return zip_path, source, digest

    def test_real_candidate_historical_receipt_is_romfree_inconclusive(self):
        from evidence_contract import validate_envelope
        evidence = ROOT / "analysis/evidence/baldosa-romless-windows-38118756830-consistency.json"
        report = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(report), [])
        self.assertEqual(report["outcome"], "inconclusive")
        self.assertEqual(report["subject"]["backend"], "baldosa-aot-provisional")
        self.assertEqual(report["subject"]["candidate_merge_commit"],
                         "8f7767444157b49a02b4b502cae01f300e57cda8")
        self.assertEqual(report["subject"]["producing_pr_head"],
                         "d20cd31ef86131dd12e611f41956e0106703eddf")
        self.assertEqual(report["provenance"]["checkout_merge_second_parent"],
                         report["subject"]["producing_pr_head"])
        self.assertFalse(report["metrics"]["rom_bundled"])
        self.assertFalse(report["metrics"]["integrated_fresh_process_1p_2p_records_verified"])
        self.assertFalse(report["metrics"]["physical_windows_controller_audio_display_verified"])

    def test_retained_baldosa_artifact_pair_join_on_exact_runtime_executable(self):
        root = ROOT / "analysis/evidence"
        candidate = json.loads((root / "baldosa-romless-windows-38118756830-consistency.json").read_text())
        runtime = json.loads((root / "baldosa-windows-38118756830-runtime-correlation.json").read_text())
        self.assertEqual(candidate["outcome"], "inconclusive")
        self.assertEqual(runtime["outcome"], "inconclusive")
        self.assertEqual(candidate["subject"]["producing_run_id"],
                         runtime["subject"]["producing_run_id"])
        self.assertEqual(candidate["subject"]["archive_inner_zip_sha256"],
                         runtime["subject"]["inner_candidate_zip_sha256"])
        self.assertEqual(candidate["metrics"]["executable_payload_sha256"],
                         runtime["subject"]["win32_executable_sha256"])
        self.assertTrue(candidate["metrics"]["launcher_reparse_ancestor_guard_present"])
        self.assertFalse(candidate["metrics"]["template_bytes_compared_against_matching_source_commit"])
        self.assertEqual(runtime["metrics"]["guest_course_complete_credit"], 0)
        self.assertFalse(runtime["metrics"]["physical_controller_coverage"])

    def test_native_runtime_archive_matches_provisional_executable_only(self):
        from evidence_contract import validate_envelope
        path = ROOT / "analysis/evidence/baldosa-windows-38118756830-runtime-correlation.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(report), [])
        self.assertEqual(report["outcome"], "inconclusive")
        self.assertEqual(report["subject"]["backend"], "baldosa-aot-provisional")
        self.assertEqual(report["subject"]["win32_executable_sha256"],
                         "29982231bd85dacdb5058c65ccc87deec4e1641603e95dd5d6fb9a37c0c8a439")
        self.assertEqual(report["subject"]["inner_candidate_zip_sha256"],
                         "5bb9f872fd0e97b5f99fc50d41bb7ee9a04ab00752e7745dbb6bbc5d7f593a78")
        self.assertEqual(report["metrics"]["guest_course_complete_credit"], 0)
        self.assertEqual(report["metrics"]["source_settled_native_2p_result_publications"], 0)
        self.assertFalse(report["metrics"]["physical_controller_coverage"])
        self.assertFalse(report["metrics"]["fresh_process_native_1p_2p_results_records_verified"])

    def test_cli_requires_independent_actions_wrapper_nomination_and_writes_inconclusive_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inner, source, inner_digest = self.make(root)
            wrapper = root / "reviewed-actions.zip"
            with zipfile.ZipFile(wrapper, "w") as artifact:
                artifact.writestr(qa.ACTIONS_INNER, inner.read_bytes())
                artifact.writestr(
                    qa.ACTIONS_CHECKSUM,
                    f"{inner_digest} *{qa.ACTIONS_INNER}\n",
                )
            output = root / "receipt.json"
            tool = ROOT / "tools" / "verify_baldosa_romless_candidate_qa.py"
            base = [
                sys.executable, str(tool),
                "--actions-artifact", str(wrapper),
                "--expected-source", source,
                "--expected-zip-sha256", inner_digest,
                "--output", str(output),
            ]
            # The CLI must reject an unpinned downloaded wrapper even though
            # the inner ZIP itself carries a perfectly good .sha256 sidecar.
            no_pin = subprocess.run(
                base, capture_output=True, text=True, check=False,
            )
            self.assertEqual(no_pin.returncode, 2)
            self.assertIn("externally nominated wrapper", no_pin.stderr)
            self.assertFalse(output.exists())
            approved = subprocess.run(
                base + [
                    "--expected-actions-artifact-sha256",
                    qa.file_digest(wrapper),
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["outcome"], "inconclusive")
            self.assertEqual(result["subject"]["candidate_zip_sha256"], inner_digest)
            self.assertEqual(result["inputs"]["actions_wrapper_sha256"],
                             qa.file_digest(wrapper))
            # A subsequent review must not destroy the original evidence or
            # follow an output symlink. Explicitly choose another file.
            initial_receipt = output.read_bytes()
            repeated = subprocess.run(
                base + [
                    "--expected-actions-artifact-sha256",
                    qa.file_digest(wrapper),
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertEqual(output.read_bytes(), initial_receipt)
            self.assertIn("cannot create a new independent QA receipt", repeated.stderr)
            wrong = subprocess.run(
                base + ["--expected-actions-artifact-sha256", "0" * 64],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(wrong.returncode, 2)
            self.assertIn("wrapper bytes differ", wrong.stderr)

    def test_original_actions_zip_wrapper_and_checksum_are_independently_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inner, source, digest = self.make(root)
            wrapper = root / "downloaded-gh-actions.zip"
            with zipfile.ZipFile(wrapper, "w") as artifact:
                artifact.writestr(qa.ACTIONS_INNER, inner.read_bytes())
                artifact.writestr(
                    qa.ACTIONS_CHECKSUM,
                    f"{digest} *{qa.ACTIONS_INNER}\n",
                )
            report = qa.audit_actions_wrapper(wrapper, source, digest)
            self.assertEqual(report["outcome"], "inconclusive")
            self.assertTrue(report["metrics"]["original_actions_sidecar_verified"])
            self.assertEqual(report["inputs"]["actions_wrapper_sha256"],
                             qa.file_digest(wrapper))
            self.assertEqual(report["subject"]["candidate_zip_sha256"], digest)
            bound = qa.audit_actions_wrapper(
                wrapper, source, digest,
                expected_wrapper_sha=qa.file_digest(wrapper),
            )
            self.assertEqual(bound["inputs"]["actions_wrapper_sha256"], qa.file_digest(wrapper))
            with self.assertRaisesRegex(ValueError, "wrapper bytes differ"):
                qa.audit_actions_wrapper(
                    wrapper, source, digest, expected_wrapper_sha="0" * 64
                )
            with self.assertRaisesRegex(ValueError, "wrapper nomination"):
                qa.audit_actions_wrapper(
                    wrapper, source, digest, expected_wrapper_sha="invalid-sha"
                )
            with self.assertRaisesRegex(ValueError, "nominated digest|sidecar"):
                qa.audit_actions_wrapper(wrapper, source, "0" * 64)

            with zipfile.ZipFile(wrapper, "w") as artifact:
                artifact.writestr(qa.ACTIONS_INNER, inner.read_bytes())
                artifact.writestr(qa.ACTIONS_CHECKSUM, f"{'f'*64} *{qa.ACTIONS_INNER}\n")
            with self.assertRaisesRegex(ValueError, "sidecar"):
                qa.audit_actions_wrapper(wrapper, source, digest)

            with zipfile.ZipFile(wrapper, "a") as artifact:
                artifact.writestr("unmanifested-extra.txt", "injected")
            with self.assertRaisesRegex(ValueError, "exactly one inner ZIP"):
                qa.audit_actions_wrapper(wrapper, source, digest)

    def test_win32_runtime_wrapper_requires_exe_identity_and_real_entry_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inner, source, digest = self.make(root)
            candidate = qa.audit(inner, source, digest)
            with zipfile.ZipFile(inner) as z:
                manifest = json.loads(z.read(producer.PREFIX + producer.MANIFEST))
            exe_sha = next(x["sha256"] for x in manifest["immutable_files"]
                           if x["path"] == producer.EXE)
            report = {
                "classification": "windows_native_pause_and_named_profile_smoke_only",
                "exe_sha256": exe_sha,
                "course_complete_credit": 0,
                "physical_gamepad_hardware_tested": False,
                "native_named_readonly_records": {"actual_native_2p_match_published": False},
            }
            for players, key in ((1, "modern_root_race_entry_p1"),
                                 (2, "modern_root_race_entry_p2")):
                report[key] = {
                    "players": players,
                    "native_root_handoff_observed": True,
                    "original_race_nmi_barrier_passed": True,
                    "original_go_ticker_barrier_passed": True,
                    "complete_event_outcome_claimed": False,
                    "actual_guest_frames": 100,
                }
            launcher = {
                "archive_sha256": digest,
                "real_extracted_launcher_accepted": True,
                "published_zip_unchanged": True,
                "rom_not_in_archive": True,
                "canonical_8192_byte_save_outside_package": True,
            }
            def make_log(players):
                return (
                    "SDL reports 0 joystick(s)\n"
                    "SDL init ok: video=windows audio=dummy\n"
                    f"UR_BALDOSA_MODERN_ROOT stock_entered players={players} menu=3c\n"
                    "script f=100 quit\n"
                ).encode()
            evidence = root / "win32-logs-actions.zip"
            def pack(contents1, contents2, summary=report, launcher_summary=launcher):
                with zipfile.ZipFile(evidence, "w") as z:
                    z.writestr(qa.RUNTIME_REPORT, json.dumps(summary))
                    z.writestr(qa.RUNTIME_LAUNCHER, json.dumps(launcher_summary))
                    z.writestr(qa.RUNTIME_ONE, contents1)
                    z.writestr(qa.RUNTIME_TWO, contents2)
            one, two = make_log(1), make_log(2)
            pack(one, two)
            accepted = qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))
            self.assertEqual(accepted["outcome"], "inconclusive")
            self.assertTrue(accepted["metrics"]["hosted_2p_stock_entry_observed"])
            self.assertFalse(accepted["metrics"]["finished_native_event_or_new_match_observed"])
            self.assertEqual(accepted["inputs"]["runtime_actions_wrapper_sha256"],
                             qa.file_digest(evidence))

            # The real uploaded Win32 wrappers include these optional
            # diagnostic logs. Keep that source-compatible, but do not
            # accept an unreviewed renamed ROM/profile/archive alongside
            # the genuine positive game result or safe smoke logs.
            with zipfile.ZipFile(evidence, "a") as z:
                z.writestr(
                    "UR Baldosa Win32 Pause Route/with_pause/log.txt",
                    "bounded stock diagnostic, not release evidence",
                )
            bounded_diagnostic = qa.check_runtime_actions_wrapper(
                evidence, qa.audit(inner, source, digest),
            )
            self.assertEqual(bounded_diagnostic["outcome"], "inconclusive")
            # An allowlisted diagnostic member is not itself inspected for
            # product credit, but it still must be bounded against a highly
            # compressible multi-megabyte private export / ZIP bomb.
            pack(one, two)
            with zipfile.ZipFile(evidence, "a", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr(
                    "UR Baldosa Win32 Pause Route/with_pause/log.txt",
                    "x" * (2 * 1024 * 1024 + 1),
                )
            with self.assertRaisesRegex(ValueError, "oversized/empty ZIP member"):
                qa.check_runtime_actions_wrapper(
                    evidence, qa.audit(inner, source, digest),
                )
            # The two currently proposed first-racer Windows artifact
            # layouts are future producer diagnostics only. Admit each
            # complete three-file set without counting it as an authenticated
            # first-user/controller acceptance, reject fragments and two
            # competing layouts co-present in one ambiguous archive.
            for group in qa.RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS:
                with self.subTest(first_racer_group=group[0]):
                    pack(one, two)
                    with zipfile.ZipFile(evidence, "a") as z:
                        for member in group:
                            z.writestr(member, "test fixture: never release evidence")
                    if group == qa.RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS[0]:
                        # This triad is now an authenticated source-LOG
                        # contract. Three invented "positive" text blobs
                        # may no longer pass merely because names are known.
                        with self.assertRaisesRegex(ValueError, "first-racer evidence is not UTF-8 JSON"):
                            qa.check_runtime_actions_wrapper(
                                evidence, qa.audit(inner, source, digest),
                            )
                    else:
                        # Retired alternate producer layout remains safely
                        # bounded but deliberately receives no source credit.
                        new_diagnostics = qa.check_runtime_actions_wrapper(
                            evidence, qa.audit(inner, source, digest),
                        )
                        self.assertEqual(new_diagnostics["outcome"], "inconclusive")
                        self.assertFalse(new_diagnostics["metrics"][
                            "hosted_first_racer_anonymous_creation_to_fresh_named_boot_consistent"
                        ])
                        self.assertFalse(new_diagnostics["metrics"][
                            "finished_native_event_or_new_match_observed"
                        ])
                    pack(one, two)
                    with zipfile.ZipFile(evidence, "a") as z:
                        z.writestr(group[0], "incomplete test-owned record")
                    with self.assertRaisesRegex(ValueError, "diagnostic evidence group incomplete"):
                        qa.check_runtime_actions_wrapper(
                            evidence, qa.audit(inner, source, digest),
                        )
            pack(one, two)
            with zipfile.ZipFile(evidence, "a") as z:
                for group in qa.RUNTIME_FIRST_RACER_DIAGNOSTIC_GROUPS:
                    for member in group:
                        z.writestr(member, "ambiguous cross-PR diagnostics")
            with self.assertRaisesRegex(ValueError, "diagnostic evidence groups ambiguous"):
                qa.check_runtime_actions_wrapper(
                    evidence, qa.audit(inner, source, digest),
                )
            for unexpected in (
                "exported-private-profile.txt",
                "ROM-renamed-as-a-log.json",
                "UR Baldosa Win32 Pause Route/secret/save.srm.txt",
                "UR Baldosa Win32 Pause Route/native_real_2p_records/artifacts/other.urrun.txt",
                "../private-archive.txt",
                "C:/absolute/private-data.txt",
                "stray-folder/",
            ):
                with self.subTest(unexpected=unexpected):
                    pack(one, two)
                    with zipfile.ZipFile(evidence, "a") as z:
                        z.writestr(unexpected, "UNREVIEWED_BYTES")
                    with self.assertRaisesRegex(ValueError, "unreviewed ZIP member"):
                        qa.check_runtime_actions_wrapper(
                            evidence, qa.audit(inner, source, digest),
                        )
            pack(one, two)
            bound = qa.check_runtime_actions_wrapper(
                evidence, qa.audit(inner, source, digest),
                expected_wrapper_sha=qa.file_digest(evidence),
            )
            self.assertEqual(bound["outcome"], "inconclusive")
            with self.assertRaisesRegex(ValueError, "runtime evidence wrapper differs"):
                qa.check_runtime_actions_wrapper(
                    evidence, qa.audit(inner, source, digest),
                    expected_wrapper_sha="0" * 64,
                )
            with self.assertRaisesRegex(ValueError, "runtime evidence nomination"):
                qa.check_runtime_actions_wrapper(
                    evidence, qa.audit(inner, source, digest),
                    expected_wrapper_sha="not-a-sha",
                )

            # The downloaded real Windows logs are CRLF, not Linux LF.
            pack(one.replace(b"\n", b"\r\n"), two.replace(b"\n", b"\r\n"))
            crlf = qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))
            self.assertTrue(crlf["metrics"]["hosted_1p_stock_entry_observed"])

            # Newer Win32 reports may prove read-only *historical*
            # Records visibility. Require a complete set of nonmutation
            # qualifiers rather than admitting cherry-picked counters.
            prior_history = report["native_named_readonly_records"]
            safe_history = {
                "actual_native_2p_match_published": False,
                "canonical_2p_archive_readonly_tabs_checked": True,
                "historical_2p_pairs_read": 1,
                "incomplete_2p_pairs_reported_unavailable": 1,
                "2p_archive_unchanged_after_guest": True,
                "unbound_2p_never_attributed_to_a_record": True,
                "no_run_created_by_record_view_or_script_quit": True,
            }
            reported_history = {**report, "native_named_readonly_records": safe_history}
            pack(one, two, reported_history)
            good_history = qa.check_runtime_actions_wrapper(
                evidence, qa.audit(inner, source, digest),
            )
            self.assertTrue(good_history["metrics"]["historical_2p_records_readonly_observed"])
            self.assertTrue(good_history["metrics"]["historical_2p_records_tabs_checked"])
            self.assertEqual(good_history["metrics"]["historical_2p_pairs_read"], 1)
            self.assertFalse(good_history["metrics"]["finished_native_event_or_new_match_observed"])

            # A read-only empty tab is still a valid negative safety
            # observation, but it cannot claim a visible historical pair.
            no_pairs = {**safe_history, "historical_2p_pairs_read": 0}
            pack(one, two, {**report, "native_named_readonly_records": no_pairs})
            empty_history = qa.check_runtime_actions_wrapper(
                evidence, qa.audit(inner, source, digest),
            )
            self.assertTrue(empty_history["metrics"]["historical_2p_records_tabs_checked"])
            self.assertFalse(empty_history["metrics"]["historical_2p_records_readonly_observed"])
            self.assertEqual(empty_history["metrics"]["historical_2p_pairs_read"], 0)
            self.assertNotIn(
                "hosted-historical-2p-records-visible-without-mutation-or-publication",
                [x["name"] for x in empty_history["assertions"]],
            )
            for change in (
                {"2p_archive_unchanged_after_guest": False},
                {"unbound_2p_never_attributed_to_a_record": False},
                {"no_run_created_by_record_view_or_script_quit": False},
                {"historical_2p_pairs_read": -1},
                {"historical_2p_pairs_read": True},
            ):
                with self.subTest(change=change):
                    damaged = {**safe_history, **change}
                    pack(one, two, {**report, "native_named_readonly_records": damaged})
                    with self.assertRaisesRegex(ValueError, "missing or contradictory safety claims"):
                        qa.check_runtime_actions_wrapper(
                            evidence, qa.audit(inner, source, digest),
                        )
            report["native_named_readonly_records"] = prior_history
            changed = {**report, "exe_sha256": "0" * 64}
            pack(one, two, changed)
            with self.assertRaisesRegex(ValueError, "tested executable"):
                qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))

            pack(one, two + b"UR_MULTIPLAYER_MATCH CAPTURED fake\n")
            with self.assertRaisesRegex(ValueError, "contradicts smoke scope"):
                qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))

            changed = {**report, "course_complete_credit": 1}
            pack(one, two, changed)
            with self.assertRaisesRegex(ValueError, "incomplete hosted smoke"):
                qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))

            # Python bool compares equal to int 0/1; the consumer must not
            # accept booleans in the integer evidence fields.
            changed = {**report, "course_complete_credit": False}
            pack(one, two, changed)
            with self.assertRaisesRegex(ValueError, "incomplete hosted smoke"):
                qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))
            entry = {**report["modern_root_race_entry_p1"], "players": True}
            changed = {**report, "modern_root_race_entry_p1": entry}
            pack(one, two, changed)
            with self.assertRaisesRegex(ValueError, "stock-race entry report inconsistent"):
                qa.check_runtime_actions_wrapper(evidence, qa.audit(inner, source, digest))

    def test_latest_baldosa_win32_candidate_archive_has_no_fictitious_event_credit(self):
        from evidence_contract import validate_envelope
        path = ROOT / (
            "analysis/evidence/baldosa-windows-38120282979-package-runtime-consistency.json"
        )
        record = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(record), [])
        self.assertEqual(record["outcome"], "inconclusive")
        self.assertEqual(record["subject"]["source_checkout_merge_commit"],
                         "b00e1c0b1404e0576ada008bdd80e80bc8973a94")
        self.assertEqual(record["provenance"]["checkout_merge_second_parent"],
                         record["subject"]["producing_pr_head"])
        self.assertEqual(record["subject"]["win32_executable_sha256"],
                         "a72924e0e6aa1e8df8bc04abcdbee4b60ca879e7e159a2e61e1daf4ddd6d64d8")
        self.assertEqual(record["metrics"]["completed_original_event_credit"], 0)
        self.assertIs(record["metrics"]["new_native_2p_match_published"], False)
        self.assertIs(record["metrics"]["physical_windows_controller_audio_display_verified"], False)
        self.assertIs(record["metrics"]["independent_release_candidate_approved"], False)
        self.assertIs(record["metrics"]["post_raw_pre_typed_crash_divergence_reported"], True)

    def test_newest_hosted_win32_2p_records_visibility_is_only_historical(self):
        from evidence_contract import validate_envelope
        evidence = ROOT / "analysis/evidence/baldosa-win32-38150963449-readonly-2p-records.json"
        record = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(validate_envelope(record), [])
        self.assertEqual(record["outcome"], "inconclusive")
        self.assertEqual(record["subject"]["backend"], "baldosa-aot-provisional")
        self.assertEqual(record["subject"]["actual_checkout_source_merge_commit"],
                         "d187c922ec75296ad8034d638178e10f7a7f1ee0")
        self.assertEqual(record["inputs"]["native_win32_actions_artifact_id"], 11706228537)
        self.assertEqual(record["metrics"]["readable_historical_2p_pairs"], 1)
        self.assertEqual(record["metrics"]["incomplete_2p_pairs_unavailable"], 1)
        self.assertTrue(record["metrics"]["records_2p_archive_unchanged_after_guest"])
        self.assertFalse(record["metrics"]["new_2p_match_published"])
        self.assertEqual(record["metrics"]["original_guest_course_complete_credit"], 0)
        self.assertFalse(record["metrics"]["integrated_new_original_result_to_records_verified"])
        self.assertFalse(record["metrics"]["physical_controller_audio_display_verified"])

    def test_canonical_unexecuted_candidate_is_only_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            result = qa.audit(archive, source, digest)
            self.assertEqual(result["outcome"], "inconclusive")
            self.assertEqual(result["subject"]["backend"], "baldosa-aot-provisional")
            self.assertFalse(result["metrics"]["integrated_native_1p_2p_journey_verified"])
            self.assertFalse(result["metrics"]["physical_windows_verified"])

    def test_pins_are_full_and_mismatches_reject_before_zip_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            for badsource, baddigest in (("main", digest), ("A" * 40, digest),
                                          (source, "0" * 64), (source, "xx")):
                with self.subTest(source=badsource, digest=baddigest):
                    with self.assertRaisesRegex(ValueError, "nominated"):
                        qa.audit(archive, badsource, baddigest)
            with self.assertRaisesRegex(ValueError, "source mismatched"):
                qa.audit(archive, "b" * 40, digest)

    def test_forced_recomputed_digest_cannot_hide_mutated_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            def change(name, value):
                if name.endswith(producer.LAUNCHER):
                    return value.replace(b"setlocal DisableDelayedExpansion",
                                         b"setlocal EnableDelayedExpansion")
                return value
            resigned(archive, change)
            revised = qa.file_digest(archive)
            with self.assertRaisesRegex(ValueError, "digest or size mismatch"):
                qa.audit(archive, source, revised)

    def test_resigned_and_manifest_rehashed_wrong_launcher_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            original = {}
            with zipfile.ZipFile(archive) as z:
                original = {name: z.read(name) for name in z.namelist()}
            mutated = producer.launcher().replace(
                b"setlocal DisableDelayedExpansion",
                b"setlocal EnableDelayedExpansion")
            manifest = json.loads(original[producer.PREFIX + producer.MANIFEST])
            for entry in manifest["immutable_files"]:
                if entry["path"] == producer.LAUNCHER:
                    entry["bytes"] = len(mutated)
                    entry["sha256"] = hashlib.sha256(mutated).hexdigest()
            new_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
            def change(name, data):
                if name.endswith(producer.MANIFEST):
                    return new_manifest
                if name.endswith(producer.LAUNCHER):
                    return mutated
                return data
            resigned(archive, change)
            with self.assertRaisesRegex(ValueError, "noncanonical CMD encoding or entry"):
                qa.audit(archive, source, qa.file_digest(archive))

    def test_evolving_safe_product_launcher_is_not_rejected_by_old_qa_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive) as z:
                originals = {n: z.read(n) for n in z.namelist()}
            original_launcher = originals[producer.PREFIX + producer.LAUNCHER]
            # A genuine later product revision adds this security guard.
            # The old checkout template must not be used as an exact oracle.
            future_launcher = original_launcher.replace(
                b"Get-FileHash -LiteralPath $env:UR_BALDOSA_ROM",
                b"[IO.FileAttributes]::ReparsePoint; Get-FileHash -LiteralPath $env:UR_BALDOSA_ROM",
            )
            self.assertNotEqual(future_launcher, original_launcher)
            manifest = json.loads(originals[producer.PREFIX + producer.MANIFEST])
            for item in manifest["immutable_files"]:
                if item["path"] == producer.LAUNCHER:
                    item["bytes"] = len(future_launcher)
                    item["sha256"] = hashlib.sha256(future_launcher).hexdigest()
            revised_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
            def revised(name, data):
                if name.endswith(producer.LAUNCHER):
                    return future_launcher
                if name.endswith(producer.MANIFEST):
                    return revised_manifest
                return data
            resigned(archive, revised)
            reviewed = qa.audit(archive, source, qa.file_digest(archive))
            self.assertTrue(reviewed["metrics"]["launcher_reparse_ancestor_guard_present"])
            self.assertFalse(reviewed["metrics"]["template_bytes_compared_against_matching_source_commit"])
            self.assertEqual(reviewed["outcome"], "inconclusive")

    def test_non_pe_or_wrong_machine_rejected_despite_valid_manifest_and_zip_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive) as z:
                originals = {n: z.read(n) for n in z.namelist()}
            payload = bytearray(originals[producer.PREFIX + producer.EXE])
            payload[132:134] = b"\x4c\x01"  # Intel 386, not AMD64.
            manifest = json.loads(originals[producer.PREFIX + producer.MANIFEST])
            for item in manifest["immutable_files"]:
                if item["path"] == producer.EXE:
                    item["sha256"] = hashlib.sha256(payload).hexdigest()
            revised_manifest = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
            def revised(name, data):
                if name.endswith(producer.EXE):
                    return bytes(payload)
                if name.endswith(producer.MANIFEST):
                    return revised_manifest
                return data
            resigned(archive, revised)
            with self.assertRaisesRegex(ValueError, "AMD64 PE32"):
                qa.audit(archive, source, qa.file_digest(archive))

    def test_extra_or_duplicate_archive_member_refused_even_with_new_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr(producer.PREFIX + "Uniracers_USA.sfc", b"do not ship")
            with self.assertRaisesRegex(ValueError, "extra, missing"):
                qa.audit(archive, source, qa.file_digest(archive))
            archive.unlink()
            archive, source, digest = self.make(Path(tmp))
            with zipfile.ZipFile(archive, "a") as z:
                z.writestr(producer.PREFIX + producer.EXE, b"duplicate")
            with self.assertRaisesRegex(ValueError, "extra, missing"):
                qa.audit(archive, source, qa.file_digest(archive))

    def test_symlinked_archive_and_noncandidate_zip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, source, digest = self.make(root)
            linked = root / "aliased.zip"
            try:
                linked.symlink_to(archive)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "symlink"):
                qa.audit(linked, source, digest)


if __name__ == "__main__":
    unittest.main()
