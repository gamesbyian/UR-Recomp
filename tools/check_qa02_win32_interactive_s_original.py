#!/usr/bin/env python3
"""Independent read-only original Win32 packaged CMD S-choice archive verifier.

Requires exact external original GitHub Actions ZIP and separately pinned CMD
digest. No guest execution, synthetic profile selection, release or physical QA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

A, B, C = "native-ci-rider", "native-ci-second", "native-ci-third"
NAMES = ("selector", "catalog", "a-raw", "a-typed", "b-raw", "b-typed", "c-raw")
STAGES = ("before-S", "after-S", "cold1-S", "cold2-S")
SOURCE = {f"source-bytes/{stage}.{name}.bin"
          for stage in STAGES for name in NAMES}
SOURCE.add("source-bytes/unrelated-C-original-typed.bin")
LOGS = {"fixture.log", "interactive-S.log", "interactive-S.key.log",
        "cold-S-1.log", "cold-S-2.log", "interactive-S.profile.log",
        "interactive-s-result.json"}
MEMBERS = SOURCE | LOGS
HEXDIGEST = re.compile(r"[0-9a-f]{64}\Z")
LIMIT = 500_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("QA02_INTERACTIVE_S_REJECTED: " + why)


def typed_sram(text: bytes) -> bytes:
    require(text.startswith(b"UR-HOST-PROFILE/5\n"),
            "noncanonical typed player schema")
    fields = re.findall(rb"(?m)^stock_sram=([0-9a-f]{16384})\r?$", text)
    require(len(fields) == 1, "missing or repeated complete stock SRAM")
    return bytes.fromhex(fields[0].decode("ascii"))


def check_original_zip(path: Path, external_sha: str, cmd_sha: str) -> dict:
    require(type(external_sha) is str and type(cmd_sha) is str and
            HEXDIGEST.fullmatch(external_sha) is not None and
            HEXDIGEST.fullmatch(cmd_sha) is not None,
            "require separately pinned source Actions ZIP and CMD digests")
    require(path.is_file() and not path.is_symlink() and
            0 < path.stat().st_size <= LIMIT,
            "original source artifact absent/redirected/too large")
    require(sha(path.read_bytes()) == external_sha,
            "source original Actions artifact SHA256 mismatch")
    require(len(MEMBERS) == 36, "internal ZIP inventory contract drift")
    with zipfile.ZipFile(path) as z:
        info = z.infolist()
        require(len(info) == len(MEMBERS) and
                {item.filename for item in info} == MEMBERS,
                "incomplete/extra/duplicated original archive members")
        require(sum(item.file_size for item in info) <= LIMIT and
                z.testzip() is None, "original size budget or ZIP CRC failed")
        for item in info:
            kind = stat.S_IFMT(item.external_attr >> 16)
            require(not item.is_dir() and not (item.flag_bits & 1) and
                    kind in (0, stat.S_IFREG) and item.file_size > 0,
                    "unsafe/empty original archive member " + item.filename)
        raw_report = z.read("interactive-s-result.json")
        report = json.loads(raw_report)
        lf = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
        require(raw_report in (lf, lf.replace(b"\n", b"\r\n")),
                "source report noncanonical")
        require(type(report) is dict and
                report.get("schema") == "ur-win32-interactive-original-cmd-s/1" and
                report.get("original_actual_cmd_sha256") == cmd_sha and
                report.get("actual_win32_console_choice") == "S" and
                report.get("literal_win32_console_profile_text") == B and
                type(report.get("original_native_guest_B_cold_boot_count")) is int and
                report["original_native_guest_B_cold_boot_count"] == 2 and
                all(report.get(k) is True for k in (
                    "original_cmd_committed_once", "damaged_A_untouched",
                    "healthy_B_untouched", "unrelated_broken_C_untouched",
                    "only_authorized_selector_changed")) and
                report.get("physical_operator") is False and
                type(report.get("release_gate_credit")) is int and
                report["release_gate_credit"] == 0,
                "source-reported recovery scope or release boundary failed")
        receipts = report.get("all_retained_source_bytes")
        require(type(receipts) is dict and
                set(receipts) == {x.removeprefix("source-bytes/") for x in SOURCE},
                "original byte receipt inventory differs")
        data: dict[str, bytes] = {}
        for path_name in SOURCE:
            value = z.read(path_name)
            key = path_name.removeprefix("source-bytes/")
            receipt = receipts[key]
            require(type(receipt) is dict and
                    set(receipt) == {"sha256", "bytes"} and
                    type(receipt["bytes"]) is int and
                    receipt["bytes"] == len(value) and
                    receipt["sha256"] == sha(value),
                    "source original byte SHA/length differs " + path_name)
            data[key] = value

        def d(stage: str, name: str) -> bytes:
            return data[f"{stage}.{name}.bin"]

        before = {name: d("before-S", name) for name in NAMES}
        after = {name: d("after-S", name) for name in NAMES}
        for who in ("a", "b", "c"):
            require(len(before[f"{who}-raw"]) == 8192 and
                    len(after[f"{who}-raw"]) == 8192,
                    "source raw is not canonical full 8KiB " + who)
        before_a = typed_sram(before["a-typed"])
        before_b = typed_sram(before["b-typed"])
        require(before_a[:16] == before["a-raw"][:16] and
                [i for i, (x, y) in enumerate(zip(before_a, before["a-raw"]))
                 if x != y] == [0x0711] and
                before["a-raw"][0x0711] == before_a[0x0711] ^ 0x35,
                "damaged selected racer A was not exact original source fixture")
        require(before["a-typed"].count(
                    b"profile=" + A.encode() + b"\n") == 1 and
                before["b-typed"].count(
                    b"profile=" + B.encode() + b"\n") == 1 and
                third_typed.count(
                    b"profile=" + C.encode() + b"\n") == 1,
                "original saved typed identities do not match registered A/B/C")
        require(before_b == before["b-raw"], "target B not a healthy matched pair")
        third_typed = data["unrelated-C-original-typed.bin"]
        require(typed_sram(third_typed) == before["c-raw"],
                "the unrelated C fixture wasn't independently healthy before deletion")
        require(len({before["a-raw"], before["b-raw"], before["c-raw"]}) == 3,
                "the three original racer raw images are not distinct")
        catalog = before["catalog"]
        require(catalog.startswith(b"UR-PROFILE-CATALOG/1\n") and
                all(catalog.count(identity.encode() + b"|") == 1
                    for identity in (A, B, C)),
                "locked canonical catalog missing exactly three racer identities")
        require(before["selector"].startswith(b"UR-HOST-STATE/6\n") and
                before["selector"].count(b"profile=" + A.encode() + b"\n") == 1 and
                after["selector"].count(b"profile=" + B.encode() + b"\n") == 1,
                "source-selector ID change A to B not proven")
        expected_selector = before["selector"].replace(
            b"profile=" + A.encode() + b"\n",
            b"profile=" + B.encode() + b"\n", 1)
        require(after["selector"] == expected_selector,
                "selector changed other product settings in addition to active ID")
        for name in NAMES:
            if name != "selector":
                require(after[name] == before[name],
                        "S altered source racer or catalog " + name)
            for stage in ("cold1-S", "cold2-S"):
                require(d(stage, name) == after[name],
                        "cold native guest changed " + stage + " " + name)
        fixture = z.read("fixture.log").decode("utf-8")
        source_log = z.read("interactive-S.log").decode("utf-8")
        injector = z.read("interactive-S.key.log").decode("utf-8")
        profile_injector = z.read("interactive-S.profile.log").decode("utf-8")
        require(fixture.count("UR_BALDOSA_NATIVE_PROFILE_FIXTURE") == 3,
                "three distinct genuine profile fixture stages missing")
        require(source_log.count("Explicit recovery choice [R/T/S/Q]:") == 1 and
                "Explicit recovery choice [R/T/S/Q]: S" in source_log and
                source_log.count("Healthy registered profile ID:") == 1 and
                source_log.count("UR-BALDOSA-STARTUP-PROFILE-REJECTED:") == 1 and
                source_log.count("UR-BALDOSA-RECOVERY-COMMITTED:") == 1 and
                source_log.count("first frame simulated") == 1 and
                f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={B}" in source_log and
                "UR-BALDOSA-RECOVERY-REFUSED:" not in source_log and
                "UR-BALDOSA-RECOVERY-RETRY-FAILED:" not in source_log,
                "original packaged CMD S console/guest evidence incomplete")
        require(injector.replace("\r\n", "\n").lstrip().startswith("exit=0\n") and
                "Traceback" not in injector,
                "genuine separate Win32 key input not confirmed")
        require(profile_injector.replace("\r\n", "\n").lstrip().startswith("exit=0\n")
                and "Traceback" not in profile_injector,
                "literal Win32 registered-profile text injector refused")
        for i in (1, 2):
            log = z.read(f"cold-S-{i}.log").decode("utf-8")
            require(log.count("first frame simulated") == 1 and
                    f"UR_BALDOSA_NATIVE_PROFILE APPLIED profile={B}" in log and
                    "Explicit recovery choice [R/T/S/Q]:" not in log and
                    "UR-BALDOSA-STARTUP-PROFILE-REJECTED:" not in log,
                    "fresh native B cold guest did not remain healthy")
    return {
        "schema": "ur-independent-original-win32-interactive-S/1",
        "original_actions_artifact_sha256": external_sha,
        "separate_original_CMD_sha256": cmd_sha,
        "rehashed_original_binary_members": len(SOURCE),
        "intact_named_profiles": ["A damaged unchanged", "B healthy unchanged",
                                 "C unrelated missing typed unchanged"],
        "sole_mutated_canonical_file": "host-state-v1.txt",
        "validated_original_win32_console_choice": "S",
        "cold_boots_of_authentic_B": 2,
        "human_operator_tested": False,
        "physical_storage_failure_tested": False,
        "release_gate_credit": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--cmd-sha256", required=True)
    args = p.parse_args()
    try:
        report = check_original_zip(args.zip, args.sha256, args.cmd_sha256)
    except (ValueError, KeyError, TypeError, OSError, UnicodeError,
            zipfile.BadZipFile, json.JSONDecodeError) as exc:
        p.exit(2, str(exc) + "\n")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
