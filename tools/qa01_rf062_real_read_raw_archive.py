#!/usr/bin/env python3
"""Independent archived RF062 original/native returned ROM read + raw-frame intake.

This is deliberately NOT qa01_factory_preflight or QA01 course acceptance.
The previously genuine RF054 original LDA has a different trace epoch from
the later native patch. Neither matching bytes nor matching post-script
frame images establish synchronized instruction timing or gameplay parity.

Requires archived full ZIPs; never executes, changes, or requires a retail ROM.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import qa01_verify_frame_capture as raw_verify

SCHEMA = "ur-qa01-rf062-authentic-opcode-raw-independent-intake/1"
BASELINE_SHA = "3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c"
ORIG = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
FRAME_ROOT = "work/zoom-zoo/replay/qa01-frame-evidence/"
ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
MOVIE = "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442"
ATTRS = ("addr", "master", "A", "Y", "D")


def need(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content(z: zipfile.ZipFile, name: str, limit: int = 2_000_000) -> bytes:
    obj = z.getinfo(name)
    need(not obj.is_dir() and 0 <= obj.file_size <= limit,
         "unbounded or missing case evidence: " + name)
    return z.read(name)


def records(log: str, prefix: str) -> list[dict[str, str]]:
    output = []
    for line in log.splitlines():
        if not line.startswith(prefix):
            continue
        items = [t.split("=", 1) for t in line.split()[1:] if "=" in t]
        row = dict(items)
        need(len(row) == len(items) and row, "ambiguous original/native row: " + prefix)
        output.append(row)
    return output


def observed_native_reads(text: str) -> dict:
    need("QA01RF062NATIVE_TRUNCATED" not in text and
         "QA01RF054NATIVEBUS_TRUNCATED" not in text,
         "bounded authentic native recorder overflow")
    direct = records(text, "QA01RF062NATIVE ")
    helper = records(text, "QA01RF054NATIVEBUS ")
    need(len(direct) == 10 and
         [int(r["seq"]) for r in direct] == list(range(1, 11)),
         "no ten actual native executed sound operands")
    need(helper and
         [int(r["seq"]) for r in helper] == list(range(1, len(helper)+1)) and
         all(r["kind"] == "read8" and
             r["scope"] == "Snd_UploadBlockList_82EF_M1X0" for r in helper),
         "genuine RF054 helper population incomplete/foreign")
    index = collections.defaultdict(list)
    for r in helper:
        index[tuple(r[k] for k in ATTRS)].append(r)
    matches = []
    for i, r in enumerate(direct):
        key = tuple(r[k] for k in ATTRS)
        hit = index.get(key, [])
        need(len(hit) == 1 and r["f"] == "6124" and
             r["executedPC"] == "8282F0" and
             r["addr"] == f"11{0xC770+i:04X}" and
             r["Y"] == f"{0xC770+i:04X}" and r["D"] == "0000" and
             r["dp65"] == "11",
             "native executed PC, original operand or actual CPU helper not joined")
        matches.append({
            "native_direct_ordinal": i+1,
            "native_read_address": r["addr"],
            "native_returned_byte": r["value"],
            "native_CPU_master_clock": int(r["master"]),
            "independent_native_RF054_helper_ordinal": int(hit[0]["seq"]),
        })
    need(matches[4]["native_read_address"] == "11C774" and
         matches[4]["native_returned_byte"] == "D0",
         "actual native opcode ROM value differs from original")
    return {
        "source_bound_native_read_count": len(matches),
        "frame_6124_real_helper_read_count": len(helper),
        "frame_6124_first_read": helper[0]["addr"],
        "frame_6124_last_read": helper[-1]["addr"],
        "native_read_rows": matches,
    }


def actual_original(z: zipfile.ZipFile) -> dict:
    orig = content(z, ORIG, 3_000_000).decode("utf8")
    lda = [x for x in records(orig, "QA01RF049LDA ")
           if x.get("ea") == "11C774"]
    need(len(lda) == 1 and
         all(lda[0].get(k) == v for k, v in (
             ("pc", "82:82F0"), ("frame", "6124"),
             ("a0", "630D"), ("a1", "63D0"), ("d", "0000"),
             ("ptr", "110000"), ("y", "C774"))),
         "authenticated original opcode LDA real return changed")
    ports = [x for x in records(orig, "QA01RF050ORIGAPU ")
             if x.get("seq") in ("21", "22")]
    need([(x.get("seq"),x.get("port"),x.get("val")) for x in ports] ==
         [("21","3","D0"),("22","2","63")],
         "original real sound CPU->SPC publication absent")
    return {
        "original_source_opcode_pc": lda[0]["pc"],
        "original_physical_ROM_read": lda[0]["ea"],
        "original_CPU_accumulator_before": lda[0]["a0"],
        "original_CPU_accumulator_after": lda[0]["a1"],
        "original_actual_returned_ROM_byte": "D0",
        "original_source_host_frame": 6124,
        "original_CPU_port3_and_port2": ["D0","63"],
        "same_original_native_CPU_clock_epoch_proven": False,
    }


def compare_frame_raw(z: zipfile.ZipFile, candidate: dict) -> dict:
    info = json.loads(content(z, FRAME_ROOT + "fingerprints.json", 500_000))
    receipt = json.loads(content(z, FRAME_ROOT + "independent-review.json", 500_000))
    identity = info["source_identity"]
    evidence = candidate["evidence"]
    need(info.get("schema") == "ur-qa01-frame-fingerprint/1" and
         identity.get("source_sha") == candidate["source_sha"] and
         identity.get("rom_sha256") == evidence["rom_sha256"] == ROM and
         identity.get("movie_sha256") == evidence["movie_sha256"] == MOVIE and
         identity.get("input_sha256") == evidence["original_movie_window_sha256"] and
         identity.get("original_frame_origin") == evidence["reference_entry_frame"] and
         identity.get("native_frame_origin") == evidence["native_entry_frame"],
         "raw snapshots not paired with actual controller/ROM/movie/source/guest origins")
    need(identity.get("observation_phase") == "post-script-dump" and
         info.get("accepted_USA_events") == 0 and
         info["coverage"]["between_frame_opcode_semantics_proven"] is False,
         "raw snapshots may not assert instruction-phase parity")
    need(info["coverage"]["start"] <= 6124 - identity["original_frame_origin"] <=
         info["coverage"]["end"] and
         info["coverage"]["start"] <= 6124 - identity["native_frame_origin"] <=
         info["coverage"]["end"], "at least one actual guest host6124 frame absent")
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        members = info["raw_retained_members"]
        need(len(members) <= 120 and len({m["member"] for m in members}) == len(members),
             "unsafe or duplicate raw manifest")
        for m in members:
            filename = m["member"]
            need(Path(filename).name == filename and not filename.startswith("."),
                 "untrusted raw archive path")
            name = FRAME_ROOT + "retained/" + filename
            size = 131072 if m["kind"] == "wram" else 8192
            need(m["kind"] in ("wram","sram") and
                 z.getinfo(name).file_size == size, "missing full raw WRAM/SRAM image")
            (temp / filename).write_bytes(content(z,name,131072))
        recomputed = raw_verify.verify(info, temp)
        for k in ("fingerprint_report_canonical_sha256",
                  "retained_raw_manifest_canonical_sha256",
                  "verified_raw_files", "verified_raw_frames",
                  "verified_differing_byte_occurrences",
                  "digest_only_equal_frames_not_independently_reopened",
                  "source_sha"):
            need(receipt.get(k) == recomputed[k],
                 "independent retained original/native raw audit differs: "+k)
        result = {}
        for guest in ("original","native"):
            relative = 6124 - identity[guest+"_frame_origin"]
            frame = info["rows"][relative - info["coverage"]["start"]]
            filename = f"{guest}-relative-{relative:06d}-wram.bin"
            mem = (temp / filename).read_bytes()
            need(frame["relative_frame"] == relative and
                 frame[guest+"_actual_host_frame"] == 6124 and
                 sha(mem) == frame["types"]["wram"][guest+"_sha256"],
                 "true original/native host6124 WRAM absent or changed")
            result[guest] = {
                "actual_host_frame":6124, "race_relative_frame":relative,
                "original_native_own_origin":identity[guest+"_frame_origin"],
                "wram_SHA256":sha(mem),
                "post_dump_Wram_values":{f"7E:{i:04X}":f"{mem[i]:02X}"
                                         for i in (0x63,0x69,0x1ED,0x1EE,0x1F1)},
            }
    return {
        "raw_guest_own_host_6124":result,
        "continuous_paired_frame_window":[info["coverage"]["start"],
                                          info["coverage"]["end"]],
        "independently_reopened_raw_image_files":recomputed["verified_raw_files"],
        "independently_reopened_raw_frame_pairs":recomputed["verified_raw_frames"],
        "original_native_WRAM_unequal_byte_occurrences_in_window":
            recomputed["verified_differing_byte_occurrences"]["wram"],
        "original_native_SRAM_unequal_byte_occurrences_in_window":
            recomputed["verified_differing_byte_occurrences"]["sram"],
        "at_actual_CPU_read_instant_memory_sampled":False,
        "original_native_executed_instruction_clock_equivalence_proven":False,
    }


def audit(baseline: Path, native: Path, binaries: Path, paired: Path) -> dict:
    need(sha_file(baseline) == BASELINE_SHA, "immutable independent original baseline SHA changed")
    with zipfile.ZipFile(baseline) as b, zipfile.ZipFile(native) as n, \
         zipfile.ZipFile(binaries) as v, zipfile.ZipFile(paired) as p:
        old = json.loads(content(b,"producer-report.json",2_000_000))
        early = json.loads(content(n,"producer-report.json",2_000_000))
        late = json.loads(content(p,"producer-report.json",2_000_000))
        early_case = json.loads(content(n,"case-result.json",100_000))
        late_case = json.loads(content(p,"case-result.json",100_000))
        for producer,case in ((early,early_case),(late,late_case)):
            need(case["disposition"] == "strict_candidate" and
                 case["release_credit"] == 0 and
                 all(producer[k] == old[k] for k in (
                     "rom_sha256","original_movie_sha256",
                     "original_movie_window_sha256","input_sha256")) and
                 case["evidence"]["original_movie_window_sha256"] ==
                     old["original_movie_window_sha256"],
                 "unchanged original movie/input or strict course result not preserved")
        build = json.loads(content(v,"rf062-static.json",10000))
        site = build.get("source_provenance",{})
        need(build["schema"] == "ur-qa01-rf062-live-generated-site/1" and
             site.get("live_generated_function") == "Snd_UploadBlockList_82EF_M1X0" and
             site.get("direct_original_8282F0_real_bus_read_callsites") == 1,
             "no compiler-generated live exact source opcode read site")
        sums = content(v,"SHA256SUMS",10000).decode().splitlines()
        for line in sums:
            checksum,name = line.split(None,1)
            need(checksum == sha(content(v,name,20_000_000)),
                 "instrumented native binary or original reference binary changed")
        need(sha(content(v,"native",20_000_000)) ==
             early["native_executable_sha256"] ==
             late["native_executable_sha256"],
             "independent executed native binary identity differs")
        old_src = actual_original(b)
        earlier = observed_native_reads(content(n,NATIVE,2_000_000).decode())
        newer = observed_native_reads(content(p,NATIVE,2_000_000).decode())
        need(earlier["native_read_rows"] == newer["native_read_rows"],
             "native live source opcode event chronology changed during raw capture")
        old_bus = records(content(b,NATIVE,2_000_000).decode(),"QA01RF054NATIVEBUS ")
        need(len(old_bus) == 656 and len(newer["native_read_rows"]) == 10,
             "baseline or genuine native sound census missing")
        result = compare_frame_raw(p,late_case)
    return {
        "schema":SCHEMA,
        "qualification":"bounded actual native ROM opcode return + historical original operand + post-script-dump full memory; NO whole-event acceptance",
        "baseline_original_archive_sha256":BASELINE_SHA,
        "native_case_archive_sha256":sha_file(native),
        "native_static_and_binaries_archive_sha256":sha_file(binaries),
        "raw_pair_case_archive_sha256":sha_file(paired),
        "candidate_source_sha":early_case["source_sha"],
        "raw_pair_source_sha":late_case["source_sha"],
        "rom_sha256":ROM,"movie_sha256":MOVIE,
        "normalized_movie_window_SHA256":old["original_movie_window_sha256"],
        "live_generated_opcall_file_SHA256":site["generated_file_sha256"],
        "native_binary_SHA256":early["native_executable_sha256"],
        "actual_original_RF049_RF050_archived":old_src,
        "actual_native_RF062_plus_independent_RF054_helper":newer,
        "raw_original_and_native":result,
        "archived_frame6124_helper_count":len(old_bus),
        "new_frame6124_helper_count":newer["frame_6124_real_helper_read_count"],
        "first_native_RF054_helper_addr_original":old_bus[0]["addr"],
        "first_native_RF054_helper_addr_instrumented":newer["frame_6124_first_read"],
        "native_whole_mesh_identical_to_original_baseline":
            old["zoo_race_mesh"] == late["zoo_race_mesh"],
        "native_postresult_state_identical_to_original_baseline":
            old["source_terminal_followthrough"] ==
                late["source_terminal_followthrough"],
        "no_added_bus_reads_or_guest_clock_changes_proven":False,
        "synchronous_original_native_CPU_bus_state_proven":False,
        "bounded_read_qualifies_factory_v2":False,
        "cold_guest_reload_persistence_proven_on_raw_script":False,
        "USA_complete_events_accepted":0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-baseline",required=True,type=Path)
    ap.add_argument("--native-case",required=True,type=Path)
    ap.add_argument("--native-binaries",required=True,type=Path)
    ap.add_argument("--raw-case",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    receipt=audit(args.original_baseline,args.native_case,args.native_binaries,args.raw_case)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("QA01 genuine RF062 operand + raw frame independently joined; USA HOLD, 0/45")


if __name__=="__main__":
    main()
