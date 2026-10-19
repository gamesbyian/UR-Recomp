#!/usr/bin/env python3
"""QA01: genuine RF073 first *later* native stack helper reads after compiled RTI.

These reads belong to the first ordinary gameplay window AFTER handler_return.
They are not the missing compiled RTI saved-PC/PB consumption, not decoded
instruction-fetch PCs, and never join separate RF072 original guest clocks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

import qa01_rf073_native_nmi_brackets as rf073

SCHEMA = "ur-qa01-independent-rf073-native-posthandler-first-helper/1"
BYTES = tuple(range(0x01ED, 0x01F2))


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def first_posthandler(events: list[dict], brackets: list[dict]) -> dict:
    need(len(brackets) == 9 and
         [row["native_frame"] for row in brackets] == list(rf073.FRAMES),
         "nine genuine RF073 source-local native NMI brackets required")
    need([int(e["seq"]) for e in events] == list(range(1,len(events)+1)),
         "native RF047 source-local event sequence incomplete")
    frames = []
    counts = {f"00:{addr:04X}": 0 for addr in BYTES}
    native_first_status_reads = 0
    for br in brackets:
        frame = br["native_frame"]
        local = [e for e in events if int(e["f"]) == frame]
        need(local and local[0]["stage"] == "entry",
             "actual native entry not first in same original/native host frame")
        push_seq = br["native_after_push_seq"]
        marker_seq = br["native_compiled_RTI_seq"]
        return_seq = br["native_handler_return_seq"]
        need(push_seq < marker_seq < return_seq,
             "original/native native RTI ordering differs")
        handler = next((row for row in local if int(row["seq"]) == return_seq),None)
        need(handler is not None and handler["stage"] == "handler_return",
             "compiled native handler return absent")
        pre = [e for e in local if push_seq < int(e["seq"]) < marker_seq]
        need(len(pre)==1 and pre[0]["stage"]=="read" and
             int(pre[0]["seq"]) == br["native_true_status_stack_helper_read_seq"] and
             pre[0]["bank"]=="00" and pre[0]["addr"]=="01ED" and
             pre[0]["value"]=="0026" and pre[0]["nmi"]=="1",
             "genuine native compiled NMI status-only helper bracket changed")
        # Source-local RF047 event sequence is authoritative. Physical stderr
        # text ordering is not, because RF044 and RF047 logger lines collide.
        after = [e for e in local if int(e["seq"]) > return_seq and
                 e["stage"] == "read" and e["bank"] == "00" and
                 e["width"] in ("1","2") and e["nmi"]=="0"]
        got = {}
        for addr in BYTES:
            label = f"00:{addr:04X}"
            # The native helper genuinely emits width=2 reads. One actual
            # word at 01ED returns BOTH 01ED and 01EE in little-endian
            # order; do not skip it merely because no one-byte row exists.
            rows = [e for e in after if
                    int(e["addr"],16) <= addr <
                    int(e["addr"],16) + int(e["width"])]
            need(rows, "no actual later native stack helper covering "+label)
            first = rows[0]
            start = int(first["addr"],16)
            shift = (addr - start) * 8
            whole = int(first["value"],16)
            byte = (whole >> shift) & 0xFF
            need(whole < 1 << (8 * int(first["width"])) and
                 int(first["seq"]) > return_seq and
                 int(first["master"]) > int(handler["master"]),
                 "native byte/word helper is malformed or not strictly after RTI")
            got[label] = {
                "native_RF047_local_seq": int(first["seq"]),
                "native_value": f"{byte:02X}",
                "native_full_helper_value": first["value"],
                "actual_helper_base_address": f"00:{start:04X}",
                "actual_helper_width_bytes": int(first["width"]),
                "native_master": int(first["master"]),
                "native_cycles_after_handler_return":
                    int(first["master"]) - int(handler["master"]),
                "outside_compiled_NMI_return": True,
                "guest_opcode_fetch_PC_qualified": False,
                "no_intervening_non_helper_guest_writes_proven": False,
            }
            counts[label] += 1
        need(got["00:01F1"]["native_RF047_local_seq"] ==
             br["native_first_post_handler_stack_helper_read_seq"],
             "RF073 first post-handler stack-helper identity drift")
        need(got["00:01F1"]["native_value"]=="26" and
             got["00:01F1"]["native_RF047_local_seq"] ==
             return_seq+1, "the genuine first native outside-NMI read changed")
        native_first_status_reads += 1
        frames.append({
            "native_host_frame": frame,
            "compiled_native_handler_return_seq": return_seq,
            "saved_native_NMI_push_raw_01ED_to_01F0":
                br["native_after_push_raw_4_bytes"],
            "original_same_host_source_NMI_saved_bytes":
                br["original_post_real_NMI_raw_5_stack_bytes"],
            "observed_first_later_stack_helper_reads": got,
            "native_intra_frame_phase_matched_to_original": False,
            "these_later_reads_are_the_compiled_RTI_saved_PC_reads": False,
        })
    need(all(v==9 for v in counts.values()),"not all nine native frames rechecked")
    return {
        "schema": SCHEMA,
        "nine_authentic_native_NMI_windows": len(frames),
        "actual_first_outside_handler_native_helper_observations": sum(counts.values()),
        "native_helpers_during_compiled_RTI_for_saved_PC_or_PB": 0,
        "first_posthandler_read_is_01F1_26_in_all_nine":native_first_status_reads==9,
        "native_first_helper_counts_by_stack_address": counts,
        "native_saved_PC_or_PB_read_during_compiled_RTI_proven":False,
        "original_native_same_semantic_NMI_checkpoint_proven":False,
        "actual_native_fetched_opcode_PC_proven":False,
        "all_guest_memory_writers_observed":False,
        "first_original_native_differing_consumed_stack_byte_proven":False,
        "accepted_complete_USA_events":0,
        "release_QA_gates":0,
        "decision":"HOLD",
        "frames":frames,
    }


def authentic(path: Path) -> dict:
    prior = rf073.authenticated_case(path)
    with zipfile.ZipFile(path) as z:
        native = z.read(rf073.NATIVE)
    events, collisions = rf073.parse_native(native.decode("utf8"))
    need(prior["native_RF047_other_logger_prefix_fragment_count"] == len(collisions)
         and prior["native_RF047_event_count"] == len(events)
         and prior["native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI"]==0,
         "RF073 original/native host-source witness changed")
    result = first_posthandler(events, prior["brackets"])
    result.update({
        "exact_authenticated_native_original_Zoo_zip_SHA256":
            prior["exact_authenticated_RF054_zip_sha256"],
        "native_executable_SHA256":prior["native_executable_sha256"],
        "original_core_SHA256":prior["original_core_sha256"],
        "ROM_SHA256":prior["ROM_sha256"],
        "original_movie_SHA256":prior["original_movie_sha256"],
        "source_SHA":prior["source_commit_sha"],
        "native_real_log_SHA256":prior["actual_native_log_sha256"],
        "untrusted_fragmented_logger_prefixes":len(collisions),
    })
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("authentic_rf054_case",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args = ap.parse_args()
    result = authentic(args.authentic_rf054_case)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RF073 45 later native stack-helper observations qualified; RTI consumer HOLD")


if __name__=="__main__":
    main()
