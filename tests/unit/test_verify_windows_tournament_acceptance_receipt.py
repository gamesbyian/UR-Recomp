"""Read-only Windows tournament receipt checks without game/ROM data."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.verify_windows_tournament_acceptance_receipt import verify, fields, CANDIDATE_KEYS, ARTIFACT_KEYS


def digest(data):
    return hashlib.sha256(data).hexdigest()


def make_v1_pair() -> tuple[bytes, bytes]:
    """Independent minimal canonical 2P fixture; no production fixture reuse."""
    from tools.verify_windows_tournament_acceptance_receipt import fnv_hex
    run_body = (
        "URRUN 1\n"
        "game uniracers\n"
        "rom_sha256 " + "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478" + "\n"
        "build_compat harness\n"
        "course course:01\n"
        "mode race-2p\n"
        "elapsed_ticks60 60\n"
        "frame_count 120\n"
        "terminal_digest -\n"
        "input 0 60 10 20\n"
        "END\n"
    )
    run_checksum = fnv_hex(run_body.encode("ascii"))
    match_body = (
        "UR-MULTIPLAYER-MATCH/1\n"
        f"run_checksum {run_checksum}\n"
        "course course:01\n"
        "outcome p1\n"
        "p1_result 100\n"
        "p2_result 60000\n"
        "p1_profile " + "join.alpha".encode().hex() + "\n"
        "p1_name " + "MIKE".encode().hex() + "\n"
        "p1_rider 0\n"
        "p2_profile " + "join.bravo".encode().hex() + "\n"
        "p2_name " + "ANDREW".encode().hex() + "\n"
        "p2_rider 1\n"
    )
    return ((run_body + "checksum " + run_checksum + "\n").encode("ascii"),
            (match_body + "checksum " + fnv_hex(match_body.encode("ascii")) + "\n").encode("ascii"))


def make_v1_fixture(
    run_bytes: bytes, run_name: str = "run-123.urrun",
    tournament_id: str = "1" * 32, outcome: str = "p1",
    source_p1: str = "join.alpha", run_checksum: str | None = None,
) -> bytes:
    from tools.verify_windows_tournament_acceptance_receipt import fnv_hex
    checksum = run_checksum or run_bytes.decode().splitlines()[-1].split(" ")[1]
    receipt = (
        "UR-LOCAL-TOURNAMENT-FIXTURE/1\n"
        f"tournament {tournament_id}\n"
        "fixture 0\n"
        f"run_checksum {checksum}\n"
        "course course:01\n"
        "source_p1 " + source_p1.encode().hex() + "\n"
        "source_p2 " + "join.bravo".encode().hex() + "\n"
        f"outcome {outcome}\n"
        "swapped 0\n"
    )
    receipt += "checksum " + fnv_hex(receipt.encode()) + "\n"
    link = (
        "UR-LOCAL-TOURNAMENT-RESULT-LINK/1\n"
        "run " + run_name.encode().hex() + "\n"
        "receipt " + receipt.encode().hex() + "\n"
    )
    return (link + "checksum " + fnv_hex(link.encode()) + "\n").encode()


class WindowsTournamentReceiptVerifierTests(unittest.TestCase):
    def make(self, root):
        work = root / "tournament work"
        runs = work / "multiplayer-runs"
        fixtures = work / "user data" / "local-tournaments" / ("1" * 32) / "fixtures"
        runs.mkdir(parents=True)
        fixtures.mkdir(parents=True)
        p = runs / "run-123.urrun"
        q = runs / "run-123.urrun.urmatch"
        f = fixtures / "fixture-0.urfixture"
        run_bytes, match_bytes = make_v1_pair()
        p.write_bytes(run_bytes)
        q.write_bytes(match_bytes)
        f.write_bytes(make_v1_fixture(run_bytes))
        (work / "tournament.log").write_text(
            "\n".join((
                "UR_LOCAL_MULTIPLAYER SESSION_READY",
                "UR_LOCAL_TOURNAMENT PANEL_OPENED page=setup",
                "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1",
                "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01",
                "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED",
                "UR_MULTIPLAYER_MATCH CAPTURED course=course:01 p1=join.alpha p2=join.bravo outcome=1",
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
                "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=F9 text=CHAMPION: MIKE",
            )) + "\n", encoding="utf-8",
        )
        (work / "reopen.log").write_text(
            "\n".join((
                "UR_LOCAL_TOURNAMENT SESSION_RESTORED",
                "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0",
                "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview",
                "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0",
            )) + "\n", encoding="utf-8",
        )
        candidate = root / "windows-tournament-candidate.txt"
        candidate.write_text(
            "schema=ur-windows-qa-candidate/1\n"
            "backend=snesrecomp\n"
            "smoke_run_id=12345\n"
            "source_commit=" + "a" * 40 + "\n"
            "inner_zip_sha256=" + "b" * 64 + "\n"
            "qa_harness_commit=" + "c" * 40 + "\n",
            encoding="ascii",
        )
        report = work / "tournament-artifacts.log"
        report.write_text(
            "schema=ur-windows-tournament-artifacts/1\n"
            "backend=snesrecomp\n"
            "source_commit=" + "a" * 40 + "\n"
            "inner_zip_sha256=" + "b" * 64 + "\n"
            "run_file=run-123.urrun\nrun_sha256=" + digest(p.read_bytes()) + "\n"
            "match_file=run-123.urrun.urmatch\nmatch_sha256=" + digest(q.read_bytes()) + "\n"
            "receipt_file=fixture-0.urfixture\nreceipt_sha256=" + digest(f.read_bytes()) + "\n"
            "create_log_sha256=" + digest((work / "tournament.log").read_bytes()) + "\n"
            "reopen_log_sha256=" + digest((work / "reopen.log").read_bytes()) + "\n"
            "fresh_process_reopen=passed\n",
            encoding="ascii",
        )
        return work, candidate, p, q, f, report

    def test_records_cannot_masquerade_as_baldosa_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            good = verify(work, candidate, "a" * 40, "b" * 64)
            self.assertEqual(good["backend"], "snesrecomp")
            original = candidate.read_text()
            candidate.write_text(original.replace("backend=snesrecomp", "backend=baldosa"))
            with self.assertRaisesRegex(ValueError, "QA backend does not match"):
                verify(work, candidate, "a" * 40, "b" * 64)
            candidate.write_text(original)
            first = report.read_text()
            report.write_text(first.replace("backend=snesrecomp", "backend=baldosa"))
            with self.assertRaisesRegex(ValueError, "QA backend does not match"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_real_files_and_exact_pins_are_cross_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            r = verify(work, candidate, "a" * 40, "b" * 64)
            self.assertEqual(r["smoke_run_id"], "12345")
            self.assertIn("not physical", r["result"])
            self.assertEqual(r["tournament_instance"], "1" * 32)
            self.assertEqual(r["paired_winner"], "join.alpha")

    def test_harness_commit_and_smoke_run_reverified_against_job_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            good = verify(
                work, candidate, "a" * 40, "b" * 64,
                expected_harness="c" * 40, expected_smoke_run="12345",
            )
            self.assertEqual(good["qa_harness_commit"], "c" * 40)
            for harness, run in (("d" * 40, "12345"), ("c" * 40, "98765"),
                                 ("main", "12345"), ("c" * 40, "bad-id")):
                with self.subTest(harness=harness, run=run):
                    with self.assertRaises(ValueError):
                        verify(
                            work, candidate, "a" * 40, "b" * 64,
                            expected_harness=harness, expected_smoke_run=run,
                        )

    def test_rehashed_wrong_fixture_reference_fails_on_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, report = self.make(Path(tmp))
            original = fixture.read_bytes()
            receipt = report.read_text(encoding="ascii")
            for change in (
                {"run_name": "another.urrun"},
                {"tournament_id": "2" * 32},
                {"outcome": "p2"},
                {"source_p1": "impostor"},
                {"run_checksum": "0" * 16},
            ):
                with self.subTest(change=change):
                    edited = make_v1_fixture(run.read_bytes(), **change)
                    fixture.write_bytes(edited)
                    report.write_text(
                        receipt.replace(digest(original), digest(edited)),
                        encoding="ascii",
                    )
                    with self.assertRaisesRegex(ValueError, "fixture|tournament|result"):
                        verify(work, candidate, "a" * 40, "b" * 64)
            fixture.write_bytes(original)
            report.write_text(receipt, encoding="ascii")

    def test_rehashed_wrong_paired_result_is_rejected_on_semantics_not_digest(self):
        from tools.verify_windows_tournament_acceptance_receipt import fnv_hex
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, report = self.make(Path(tmp))
            original = match.read_bytes()
            receipt = report.read_text(encoding="ascii")
            body = original.decode("ascii").rsplit("\nchecksum ", 1)[0] + "\n"
            for change in (
                body.replace("outcome p1", "outcome p2"),
                body.replace("p2_profile " + "join.bravo".encode().hex(),
                             "p2_profile " + "impostor".encode().hex()),
                body.replace("run_checksum ", "run_checksum 0"),
                body.replace("p2_result 60000", "p2_result 20"),
            ):
                with self.subTest(mutated=change[:50]):
                    mutated = (change + "checksum " + fnv_hex(change.encode()) + "\n").encode()
                    match.write_bytes(mutated)
                    report.write_text(
                        receipt.replace(digest(original), digest(mutated)),
                        encoding="ascii",
                    )
                    with self.assertRaisesRegex(ValueError, "sidecar|result|checksum"):
                        verify(work, candidate, "a" * 40, "b" * 64)
            match.write_bytes(original)
            report.write_text(receipt, encoding="ascii")

    def test_rehashed_noncanonical_usa_rom_identity_is_rejected(self):
        from tools.verify_windows_tournament_acceptance_receipt import fnv_hex
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, report = self.make(Path(tmp))
            original_run = run.read_bytes()
            original_side = match.read_bytes()
            receipt = report.read_text(encoding="ascii")
            old_body = original_run.decode("ascii").rsplit("\nchecksum ", 1)[0] + "\n"
            altered_body = old_body.replace(
                "rom_sha256 859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
                "rom_sha256 " + "0" * 64,
            )
            altered_run = (altered_body + "checksum " +
                           fnv_hex(altered_body.encode()) + "\n").encode()
            side_body = original_side.decode("ascii").rsplit("\nchecksum ", 1)[0] + "\n"
            side_body = side_body.replace(
                "run_checksum " + fnv_hex(old_body.encode()),
                "run_checksum " + fnv_hex(altered_body.encode()),
            )
            altered_side = (side_body + "checksum " +
                            fnv_hex(side_body.encode()) + "\n").encode()
            run.write_bytes(altered_run)
            match.write_bytes(altered_side)
            report.write_text(
                receipt.replace(digest(original_run), digest(altered_run))
                       .replace(digest(original_side), digest(altered_side)),
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "unexpected ROM/course/mode"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_rehashed_missing_second_input_lane_is_rejected(self):
        from tools.verify_windows_tournament_acceptance_receipt import fnv_hex
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, report = self.make(Path(tmp))
            original = run.read_bytes()
            receipt = report.read_text(encoding="ascii")
            body = original.decode("ascii").rsplit("\nchecksum ", 1)[0] + "\n"
            edited = body.replace("input 0 60 10 20", "input 0 60 10 0")
            edited_run = (edited + "checksum " + fnv_hex(edited.encode()) + "\n").encode()
            run.write_bytes(edited_run)
            # Also update the match's internal run checksum and its own
            # internal FNV, so the assertion tests missing P2 input, not
            # stale standalone or cross-artifact hashes.
            old_side = match.read_bytes()
            side_body = old_side.decode("ascii").rsplit("\nchecksum ", 1)[0] + "\n"
            side_body = side_body.replace(
                "run_checksum " + fnv_hex(body.encode()),
                "run_checksum " + fnv_hex(edited.encode()),
            )
            new_side = (side_body + "checksum " + fnv_hex(side_body.encode()) + "\n").encode()
            match.write_bytes(new_side)
            report.write_text(
                receipt.replace(digest(original), digest(edited_run))
                       .replace(digest(old_side), digest(new_side)),
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "missing either captured input lane"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_wrong_nominated_pins_or_mutated_files_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            for bad_source, bad_zip in (("f" * 40, "b" * 64),
                                        ("a" * 40, "f" * 64),
                                        ("main", "b" * 64)):
                with self.subTest(source=bad_source):
                    with self.assertRaises(ValueError):
                        verify(work, candidate, bad_source, bad_zip)
            for target in (p, q, f):
                before = target.read_bytes()
                target.write_bytes(before + b"mutated")
                with self.subTest(target=target.name):
                    with self.assertRaisesRegex(ValueError, "digest differs"):
                        verify(work, candidate, "a" * 40, "b" * 64)
                target.write_bytes(before)

    def test_missing_or_failed_launch_history_is_rejected_even_with_valid_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            create = work / "tournament.log"
            reopen = work / "reopen.log"
            create_original = create.read_text()
            reopen_original = reopen.read_text()
            create.write_text(create_original.replace(
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED"))
            with self.assertRaisesRegex(ValueError, "lacks required event|failed event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            create.write_text(create_original)
            reopen.write_text(reopen_original.replace(
                "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0",
                "UR_LOCAL_TOURNAMENT HISTORY completed=0 unavailable=1"))
            with self.assertRaisesRegex(ValueError, "lacks required event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            reopen.write_text(reopen_original + (
                "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED\n"))
            with self.assertRaisesRegex(ValueError, "failed event"):
                verify(work, candidate, "a" * 40, "b" * 64)
            reopen.unlink()
            with self.assertRaisesRegex(ValueError, "missing, linked or oversized"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_rehashed_out_of_order_native_tournament_transition_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, receipt_path = self.make(Path(tmp))
            log = work / "tournament.log"
            saved_log = log.read_text(encoding="utf-8")
            saved_receipt = receipt_path.read_text(encoding="ascii")
            lines = saved_log.splitlines(keepends=True)
            self.assertGreater(len(lines), 5)
            # The strings still exist and the receipt's SHA is re-signed.
            lines[3], lines[6] = lines[6], lines[3]
            swapped = "".join(lines)
            log.write_text(swapped, encoding="utf-8")
            receipt_path.write_text(
                saved_receipt.replace(
                    digest(saved_log.encode()), digest(swapped.encode())),
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "impossible tournament event order"):
                verify(work, candidate, "a" * 40, "b" * 64)
            log.write_text(saved_log, encoding="utf-8")
            receipt_path.write_text(saved_receipt, encoding="ascii")

    def test_rehashed_reopen_done_before_restore_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, run, match, fixture, receipt_path = self.make(Path(tmp))
            log = work / "reopen.log"
            before = log.read_text(encoding="utf-8")
            original_receipt = receipt_path.read_text(encoding="ascii")
            lines = before.splitlines(keepends=True)
            lines[0], lines[-1] = lines[-1], lines[0]
            swapped = "".join(lines)
            log.write_text(swapped, encoding="utf-8")
            receipt_path.write_text(
                original_receipt.replace(
                    digest(before.encode()), digest(swapped.encode())),
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "reopen completed before restore"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_transcript_edits_with_all_expected_markers_still_fail_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            for filename in ("tournament.log", "reopen.log"):
                log = work / filename
                before = log.read_bytes()
                log.write_bytes(before + b"untrusted extra transcript evidence\n")
                with self.subTest(filename=filename):
                    with self.assertRaisesRegex(ValueError, "native transcript digest differs"):
                        verify(work, candidate, "a" * 40, "b" * 64)
                log.write_bytes(before)

    def test_nested_orphan_fixture_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            extra = work / "user data" / "local-tournaments" / "nested" / "future" / "fixtures" / "fixture-2.urfixture"
            extra.parent.mkdir(parents=True)
            extra.write_bytes(b"unexpected fixture beyond immediate session directory")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_duplicate_settled_match_notice_fails_even_if_log_is_resigned(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            log = work / "tournament.log"
            receipt = report.read_text()
            for duplicate in (
                "UR_MULTIPLAYER_MATCH CAPTURED",
                "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED",
            ):
                with self.subTest(duplicate=duplicate):
                    original = log.read_bytes()
                    modified = original + duplicate.encode("ascii") + b"\n"
                    log.write_bytes(modified)
                    old_hash = digest(original)
                    new_hash = digest(modified)
                    self.assertIn(old_hash, receipt)
                    report.write_text(receipt.replace(old_hash, new_hash))
                    with self.assertRaisesRegex(ValueError, "duplicate/missing settled event"):
                        verify(work, candidate, "a" * 40, "b" * 64)
                    log.write_bytes(original)
                    report.write_text(receipt)

    def test_symlinked_work_root_rejected_before_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work, candidate, p, q, f, report = self.make(root)
            link = root / "forged-work-root"
            try:
                link.symlink_to(work, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "work root is missing or linked"):
                verify(link, candidate, "a" * 40, "b" * 64)

    def test_spoofed_fields_and_reopen_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            before = report.read_text()
            for after in (before.replace("fresh_process_reopen=passed", "fresh_process_reopen=failed"),
                          before.replace("match_file=run-123.urrun.urmatch", "match_file=other.urmatch"),
                          before.replace("source_commit=" + "a" * 40, "source_commit=" + "f" * 40),
                          before.replace("run_file=run-123.urrun", "run_file=../outside.urrun"),
                          before + "extra=value\n",
                          before.replace("run_sha256=", "run_sha256=0" * 2, 1)):
                report.write_text(after)
                with self.assertRaises(ValueError):
                    verify(work, candidate, "a" * 40, "b" * 64)
            report.write_text(before)

    def test_duplicate_field_noncanonical_crlf_or_symlink_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work, candidate, p, q, f, report = self.make(root)
            backup = report.read_bytes()
            report.write_bytes(backup.replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "canonical LF"):
                fields(report, ARTIFACT_KEYS)
            report.write_bytes(backup)
            linked = root / "linked-receipt.txt"
            try:
                linked.symlink_to(report)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "linked"):
                fields(linked, ARTIFACT_KEYS)
            self.assertEqual(fields(candidate, CANDIDATE_KEYS)["smoke_run_id"], "12345")

    def test_orphan_sidecar_and_extra_fixture_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            other = q.parent / "orphan.urmatch"
            other.write_bytes(b"unclaimed match sidecar")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)
            other.unlink()
            unexpected = f.parent / "fixture-1.urfixture"
            unexpected.write_bytes(b"unexpected credited fixture")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)

    def test_missing_or_duplicate_sidecar_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, candidate, p, q, f, report = self.make(Path(tmp))
            original_match = q.read_bytes()
            q.unlink()
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)
            q.write_bytes(original_match)
            (q.parent / "other.urrun.urmatch").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                verify(work, candidate, "a" * 40, "b" * 64)


if __name__ == "__main__":
    unittest.main()
