#!/usr/bin/env python3
"""QA-01: independently re-evaluate the executed seed-50036056 2P writer ZIP.

Reads an already-executed original Snes9x/native artifact, never a ROM or an
invented input stream. Distinct clocks: host dump, original ICPU.Frame,
original V-counter, native pre-run host. No comparator weakening or QA credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

import qa01_dual_air_writer_probe as writer

SCHEMA = "UR-QA01-EXECUTED-DUAL-AIR-PRODUCER-CROSSWALK/1"
RUN = 38520105599
ARTIFACT_ID = 11873951116
ARCHIVE_SHA256 = "1fa1cf0e4c50e2d1977443310e31acd26f2fcf5941ccb93232d289ca9ce469af"
CROSSWALK_SHA256 = "3716fdf4d5612791ad9ef9f6e08d797e0591409aad8abe56e327d02eeec78775"
FRAMES = tuple(range(2576, 2585))
WRAM_SIZE = 131072
NAMED = ("p1_raw_air", "p2_raw_air", "p1_y", "p2_y",
         "p1_y_velocity", "p2_y_velocity")
WORD_OFFSETS = {"p1_candidate_state_word": 0x0545,
                "p2_candidate_state_word": 0x0547,
                # Post-run *P2-last* shared scratch, NOT the pre-P1 branch.
                "postrun_shared_collision_02c0_word": 0x02C0,
                "postrun_active_seat_selector_0fef_word": 0x0FEF}
TARGETS = ("0545", "0547", "0415", "0417", "04BB", "04BD")
HEX = re.compile(r"^[a-f0-9]{64}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def label(frame: int) -> str:
    return ("endurance-2580" if frame == 2580 else
            f"qa01-neighbor-{frame}" if frame in (2579, 2581) else
            f"qa01-air-{frame}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def report_zip(path: Path) -> dict:
    """Verify ZIP identity, actual guest memory and logged CPU-helper scopes."""
    require(path.is_file() and not path.is_symlink(), "missing actual writer ZIP")
    require(digest(path.read_bytes()) == ARCHIVE_SHA256,
            "exact executed artifact ZIP SHA-256 mismatch")
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        require(len(members) <= 120 and len(names) == len(set(names)),
                "ZIP member duplicate or oversized member table")
        require(sum(item.file_size for item in members) < 22_000_000,
                "unbounded source/native guest evidence")
        for item in members:
            name = item.filename
            require(not name.startswith("/") and
                    all(part not in ("", ".", "..") for part in name.split("/"))
                    and not stat.S_ISLNK(item.external_attr >> 16),
                    "unsafe source evidence ZIP member")
        def read(name: str, maximum: int) -> bytes:
            require(name in names, f"missing archived execution witness: {name}")
            info = archive.getinfo(name)
            require(info.file_size <= maximum and not info.is_dir(),
                    f"invalid source/native artifact member: {name}")
            return archive.read(name)

        crosswalk_bytes = read("qa01-writer-crosswalk.json", 500_000)
        require(digest(crosswalk_bytes) == CROSSWALK_SHA256,
                "original writer crosswalk bytes changed")
        crosswalk = json.loads(crosswalk_bytes)
        require(crosswalk.get("schema") == writer.SCHEMA and
                crosswalk.get("source_run") == writer.PINNED_WITNESS_RUN and
                crosswalk.get("complete_event_release_credit") == 0 and
                crosswalk.get("strict_complete_event_accepted") is False and
                crosswalk.get("actual_cpu_instruction_and_ppu_phase_aligned") is False and
                crosswalk.get("raw_air_value_proves_physical_airborne") is False,
                "source crosswalk redefined physics/clock/admission contract")
        source = json.loads(read("manifest.json", 20_000))
        dense = json.loads(read("dense-manifest.json", 20_000))
        require(source.get("seed") == 50036056 and source.get("arm") == "rotation"
                and source.get("release_gate_credit") == 0
                and dense.get("preceding_executed_paired_run") == 38509912672
                and dense.get("dense_window") == [2576, 2584]
                and dense.get("release_gate_credit") == 0
                and dense.get("source_input_frames_retained_exact") is True
                and dense.get("extra_dumps_consume_zero_guest_frames") is True,
                "not the original neutral-input rotation dense window")
        input_bytes = read("case.input", 20_000)
        require(digest(input_bytes) == source.get("input_sha256"),
                "actual original/native controller input content changed")
        inputs = input_bytes.decode("utf-8")
        require("2548:31:000:140\n" in inputs and
                "2590:18:000:180\n" in inputs and
                not any(2579 <= int(line.split(":", 1)[0]) <= 2589
                        for line in inputs.splitlines()
                        if line and not line.startswith("#")),
                "new neutral-window input event or changed P2 exit")

        original_log = read("original.log", 300_000)
        native_log = read("native.log", 300_000)
        receipts = crosswalk.get("original_native_host_receipts", {})
        require(all(digest(log) == receipts[side]["transcript_sha256"]
                    and receipts[side]["count"] == 24
                    and receipts[side]["script_host_receipts_verified"] is True
                    for side, log in (("original", original_log),
                                      ("native", native_log))),
                "side-specific original/native executed host receipts invalid")
        require(len(writer.source_opcode_chronology(
            original_log.decode("utf-8", errors="replace"))) ==
            crosswalk["original_cpu_source_receipts_qualified"],
            "original source CPU opcode chronology changed")
        native_writer_log = read("native-writers.log", 7_000_000)
        parsed = writer.NATIVE_WRITER.findall(
            native_writer_log.decode("utf-8", errors="replace"))
        actual = [dict(pre_run_host=int(f), bank=bank.upper(),
                       address=address.upper(), value=value.upper(),
                       width=int(width), source_scope=scope)
                  for f, bank, address, value, width, scope in parsed
                  if 2574 <= int(f) <= 2586
                  and 0x0415 <= int(address, 16) <= 0x0548]
        require(actual == crosswalk["native_cpu_helper_writes"],
                "native CPU helper write chronology changed")

        rows = crosswalk.get("dense_original_native_same_host")
        require(isinstance(rows, list) and
                [row["absolute_host_frame"] for row in rows] == list(FRAMES),
                "missing or reordered genuine nine-host snapshots")
        word_rows = []
        for row in rows:
            f = row["absolute_host_frame"]
            words = {}
            for side, prefix in (("original", "original/"),
                                 ("native", "native-run/dumps/")):
                state = row[side]
                name = prefix + label(f) + ".wram.bin"
                raw = read(name, WRAM_SIZE)
                require(len(raw) == WRAM_SIZE and
                        digest(raw) == state["guest_sha256"],
                        "complete independent side-specific WRAM changed")
                words[side] = {
                    key: int.from_bytes(raw[pos:pos + 2], "little")
                    for key, pos in WORD_OFFSETS.items()
                }
                require(all(state[k] == raw[pos] for k, pos in
                            (("p1_raw_air", 0x0545),
                             ("p2_raw_air", 0x0547))) and
                        state["p1_y"] == int.from_bytes(raw[0x0415:0x0417], "little")
                        and state["p2_y"] == int.from_bytes(raw[0x0417:0x0419], "little"),
                        "named source guest observations changed")
                require(state["active_race_byte"] == 1 and
                        all(state[key] == 1 for key in
                            ("p1_laps_remaining", "p2_laps_remaining",
                             "p1_next_checkpoint", "p2_next_checkpoint")),
                        "not two original/native active race seats")
            word_rows.append(words)
    return summarize(crosswalk, word_rows)


def _unique(rows: list[dict], **fields: object) -> dict:
    found = [r for r in rows if all(r.get(k) == v for k, v in fields.items())]
    require(len(found) == 1, "missing or ambiguous executed writer discriminator")
    return found[0]


def summarize(record: dict, word_rows: list[dict]) -> dict:
    """Pure classifier, separately testable with adversarial synthetic rows."""
    require(record.get("schema") == writer.SCHEMA and
            record.get("source_run") == 38509912672 and
            record.get("complete_event_release_credit") == 0 and
            record.get("strict_complete_event_accepted") is False and
            record.get("actual_cpu_instruction_and_ppu_phase_aligned") is False,
            "wrong unadmitted original/native source event")
    rows = record.get("dense_original_native_same_host")
    require(isinstance(rows, list) and len(rows) == 9
            and len(word_rows) == 9 and
            [x.get("absolute_host_frame") for x in rows] == list(FRAMES),
            "not exactly nine original/native frame witnesses")
    observed = []
    for i, row in enumerate(rows):
        f = FRAMES[i]
        o, n = row["original"], row["native"]
        require(all(type(o[k]) is int and type(n[k]) is int for k in NAMED),
                "missing authenticated named original/native field")
        differences = {key: {"original": o[key], "native": n[key]}
                       for key in NAMED if o[key] != n[key]}
        require(row["same_host_named_raw_bytes_equal"] is (not differences)
                and row["p1_y_native_minus_original"] == n["p1_y"]-o["p1_y"]
                and row["p2_y_native_minus_original"] == n["p2_y"]-o["p2_y"],
                "named original/native comparison fields contradictory")
        w = word_rows[i]
        for side, state in (("original", o), ("native", n)):
            require(w[side]["p1_candidate_state_word"] & 255 == state["p1_raw_air"]
                    and w[side]["p2_candidate_state_word"] & 255 == state["p2_raw_air"],
                    "candidate full-word/low-byte source identity lost")
        observed.append({
            "host_frame": f,
            "named_differences": differences,
            "candidate_state_words": w,
        })
    require([x["host_frame"] for x in observed if x["named_differences"]]
            == [2580, 2581, 2582] and
            observed[4]["named_differences"] == {
                "p1_raw_air": {"original": 0, "native": 1},
                "p1_y": {"original": 857, "native": 858},
                "p1_y_velocity": {"original": 0, "native": 19},
                "p2_y": {"original": 863, "native": 862}},
            "seed-50036056 original/native named divergence changed")

    # Both post-host guests agree on the shared *last P2 stage*. This
    # cannot identify the earlier P1 branch operand/flags, even though the
    # low $02C0 byte = FF would be negative in an 8-bit signed test.
    for i in (3, 4):
        w = word_rows[i]
        require(all(w[side].get("postrun_shared_collision_02c0_word") == 0x00FF
                    and w[side].get("postrun_active_seat_selector_0fef_word") == 2
                    for side in ("original", "native")),
                "same-host P2-last collision/selector control changed")
    source = record["original_cpu_opcode_changes"]
    native = record["native_cpu_helper_writes"]
    require(len(source) == 126 and len(native) == 813
            and len(record["original_cpu_shared_working_scopes"]) == 205
            and len(record["original_cpu_neighbor_high_byte_scopes"]) == 0
            and record["original_cpu_source_receipts_qualified"] == 331,
            "source/native executed writer receipt coverage changed")
    def s(addr: str, pc: str, frame: int = 2579) -> dict:
        return _unique(source, frame=frame, pc=pc, address="7E:"+addr)
    def n(addr: str, frame: int = 2579) -> dict:
        return _unique(native, pre_run_host=frame, address=addr,
                       source_scope="bank_81_8D18_M0X0")
    p1o, p2o = s("0545", "81:8E26"), s("0547", "81:8F7A")
    p1n, p2n = n("0545"), n("0547")
    scratch = record["original_cpu_shared_working_scopes"]
    p1_load = _unique(scratch, frame=2579, address="7E:0F29", pc="81:8DB1")
    p2_load = _unique(scratch, frame=2579, address="7E:0F29", pc="81:8F0B")
    p2_collision_increment = _unique(
        scratch, frame=2579, address="7E:0F29", pc="81:9268")
    p2_landing_reset = _unique(
        scratch, frame=2580, address="7E:0F29", pc="81:966D")
    require((p1_load["old"], p1_load["new"], p1_load["vcounter"],
             p2_load["old"], p2_load["new"], p2_load["vcounter"],
             p2_collision_increment["old"], p2_collision_increment["new"],
             p2_collision_increment["vcounter"],
             p2_landing_reset["old"], p2_landing_reset["new"]) ==
            ("01", "00", 56, "00", "01", 82, "01", "02", 103, "02", "00"),
            "observed original P1/P2 collision scratch staging changed")
    require((p1o["old"], p1o["new"], p1o["static_candidate_pc"],
             p1o["vcounter"]) == ("00", "00", True, 80)
            and (p2o["old"], p2o["new"], p2o["vcounter"]) ==
                ("01", "02", 104)
            and (p1n["value"], p1n["width"], p2n["value"], p2n["width"])
                == ("0001", 2, "0002", 2),
            "actual P1/P2 original/native writebacks changed")
    require((s("0415", "81:8E3C")["new"],
             s("04BB", "81:8E48")["new"],
             n("0415")["value"],
             n("04BB")["value"]) == ("59", "00", "035A", "0013"),
            "P1 original/native Y/velocity writeback asymmetry changed")
    require((s("0417", "82:928F")["new"],
             n("0417")["value"]) == ("5F", "035E"),
            "P2 early projection differs before matching result state")
    require((s("0545", "81:8E26", 2580)["new"],
             n("0545", 2580)["value"]) == ("00", "0000"),
            "subsequent frame no longer reconverges in raw P1 state")
    return {
        "schema": SCHEMA,
        "provenance": {"workflow_run": RUN, "artifact_id": ARTIFACT_ID,
                       "artifact_zip_sha256": ARCHIVE_SHA256,
                       "source_crosswalk_sha256": CROSSWALK_SHA256,
                       "original_reference_paired_witness": 38509912672,
                       "original_core_cpu_receipts": 331,
                       "original_named_opcode_scopes": 126,
                       "original_shared_scratch_scopes": 205,
                       "native_helper_write_scopes": 813},
        "dense_same_host": observed,
        "earliest_named_guest_difference_host": 2580,
        "first_named_reconvergence_host": 2583,
        "original_cpu_frame_2579": {
            "p1_state": p1o, "p2_state": p2o,
            "p1_y_writeback": s("0415", "81:8E3C"),
            "p1_vertical_writeback": s("04BB", "81:8E48"),
            "p2_early_projection": s("0417", "82:928F"),
        },
        "original_cpu_collision_scratch_2579": {
            "p1_stage_from_prior_p2": p1_load,
            "p2_stage_from_prior_state": p2_load,
            "p2_actual_collision_state_increment": p2_collision_increment,
            "p2_next_cpu_frame_collision_state_reset": p2_landing_reset,
        },
        "native_cpu_internal_collision_scratch_observed": False,
        "native_helper_pre_run_host_2579": {
            "p1_state": p1n, "p2_state": p2n,
            "p1_y_writeback": n("0415"),
            "p1_vertical_writeback": n("04BB"),
            "p2_y_writeback": n("0417"),
        },
        "posthost_2579_2580_collision_control": {
            "original_native_02c0_word": "00FF",
            "original_native_0fef_seat_selector_word": "0002",
            "these_are_pre_p1_branch_preconditions": False,
            "eight_bit_collision_sign_when_read_at_this_value": "negative",
        },
        "input_event_frames_2579_through_2589": 0,
        "cpu_instruction_or_ppu_beam_phase_aligned": False,
        "native_helper_scope_is_opcode_pc": False,
        "physical_airborne_semantics_proven": False,
        "first_causal_upstream_condition_proven": False,
        "strict_complete_usa_events_admitted": 0,
        "conclusion": (
            "Original actually executes 81:8E26 P1 unchanged 00 while native "
            "bank-81 helper writes 0001. Original 81:9268 explicitly "
            "increments P2 collision-state scratch from 01 to 02, with "
            "no equivalent changed P1 0F29 write in its scoped receipts; "
            "native internal 0F29 was not watched. Executed original P2 81:8F7A "
            "updates 01 to 02, native writes 0002. Both original/native "
            "host 2580 snapshots corroborate a short P1 state/Y/vY "
            "difference. Original ICPU.Frame, native pre-run host, "
            "v-counter and host dumps are not an instruction-phase crosswalk. "
            "Investigate upstream collision/contact or scheduler/read "
            "decisions before any behavior patch."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-zip", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = report_zip(args.artifact_zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "executed_original_opcode_and_scratch_scopes": 331,
        "executed_native_helper_writes": 813,
        "first_named_difference": result["earliest_named_guest_difference_host"],
        "release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
