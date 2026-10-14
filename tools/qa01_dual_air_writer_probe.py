#!/usr/bin/env python3
"""QA-01: original/native 2P P1 air/vertical writer discriminator.

This is a read-only adjunct to real seed 50036056, not an event acceptance
machine. All source inputs are bit-identical to the original paired run; extra
zero-frame dump commands do not consume simulation/input frames. Original
CPU ICPU.Frame, native pre-run counter and host-script clocks remain distinct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import qa01_dual_air_paired as paired

EXTRA = (2576, 2577, 2578, 2582, 2583, 2584)
DENSE = tuple(range(2576, 2585))
PINNED_WITNESS_RUN = 38509912672
PINNED_WITNESS_ZIP = "7bc085861183e7667620ad66fb0c7a18f8be7a870afe8c2e4752eb6229cd6c2a"
PINNED_SNAPSHOT_SHA = {
    "original": {
        2579: "b713236891aecd999e9776389f7b6ec535c6497a7a204f6ff9f9eba4a49aae07",
        2580: "764db04eb2464c55b1eecbe2c38d6f90041756e4ef5897c196ebb6985370486b",
        2581: "8838392a8b0e63c03e3fde22151140abecb5ffdaa4ebbcfb16ddb742b297318b",
    },
    "native": {
        2579: "48e9dbd85063a0085a51d0c855ad5be861328a0e02ce2ae8ab244073c8cd7918",
        2580: "ae9f1bcc95c74fbb088cc2eabc2b8a2ab48283e9a3a751779c8f66fd500ec7d8",
        2581: "e993a60ae8f9c09bbf34cecbc256daf8734974012dea0a20c5db6e881f422173",
    },
}
ORIGINAL_OPCODE = re.compile(
    r"^QA01AIRPC f=(\d+) v=(\d+) pc=([0-9A-Fa-f]{6}) "
    r"addr=([0-9A-Fa-f]{4}) old=([0-9A-Fa-f]{2}) "
    r"new=([0-9A-Fa-f]{2}) candidate=([01])$", re.MULTILINE)
NATIVE_WRITER = re.compile(
    r"^f\s*(\d+)\s+([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})="
    r"([0-9A-Fa-f]{2,4}) w([12]) ([^\n]+)$", re.MULTILINE)
HOST_DUMP = re.compile(
    r"^script f=(\d+) dump ([A-Za-z0-9-]+) (.+)$", re.MULTILINE)
ORIGINAL_DESCRIPTOR = re.compile(
    r"fb=256x224 RGB565 sram=8192 ppuw=\d+(?: \(truncated\))?")
TARGETS = (0x0545, 0x0547, 0x0415, 0x0417, 0x04BB, 0x04BD)
SCHEMA = "UR-QA01-DUAL-AIR-SOURCE-NATIVE-OPCODE-WRITER/1"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def tag(frame: int) -> str:
    if frame in (2579, 2581):
        return f"qa01-neighbor-{frame}"
    if frame == 2580:
        return "endurance-2580"
    if frame in EXTRA:
        return f"qa01-air-{frame}"
    raise ValueError("not in pinned 2P air boundary")


def dense_script(paired_script: str) -> str:
    old = ("wait 119\ndump qa01-neighbor-2579\n"
           "wait 1\ndump endurance-2580\n"
           "wait 1\ndump qa01-neighbor-2581\n"
           "wait 119\ndump endurance-2700\n")
    new = "wait 116\ndump qa01-air-2576\n"
    for f in range(2577, 2585):
        new += f"wait 1\ndump {tag(f)}\n"
    new += "wait 116\ndump endurance-2700\n"
    if paired_script.count(old) != 1:
        raise ValueError("original source 2P legal-input sampling plan drifted")
    if new.count("dump endurance-2580") != 1:
        raise ValueError("dense source window missing fixed witness frame")
    return paired_script.replace(old, new, 1)


def expected_tags(base_tags: list[str]) -> list[tuple[int, str]]:
    expected = []
    for t in base_tags:
        if t == paired.BASE:
            f = 1620
        else:
            f = int(t.rsplit("-", 1)[-1])
        expected.append((f, t))
    expected += [(f, tag(f)) for f in EXTRA]
    expected.sort(key=lambda x: x[0])
    if len(expected) != 24 or len(set(expected)) != 24:
        raise ValueError("not the original 18+6 exact 2P trace frame labels")
    return expected


def prepare(root: Path) -> dict:
    # Retains the source original input, original paired 18-frame script and
    # source identity. The derived 24-frame script is deliberately separate.
    original = paired.prepare(root)
    script = dense_script((root / "case.script").read_text(encoding="utf-8"))
    (root / "dense.script").write_text(script, encoding="utf-8")
    report = {
        "schema": SCHEMA,
        "source_original_manifest_sha256": sha(
            (root / "manifest.json").read_bytes()),
        "source_original_input_sha256": original["input_sha256"],
        "original_18_frame_script_sha256": original["script_sha256"],
        "derived_24_frame_script_sha256": sha(script.encode("utf-8")),
        "source_original_rom_sha256": paired.ROM_SHA,
        "native_frontier_executable_sha256": paired.NATIVE_FRONTIER_SHA,
        "preceding_executed_paired_run": PINNED_WITNESS_RUN,
        "preceding_zip_sha256": PINNED_WITNESS_ZIP,
        "source_input_frames_retained_exact": True,
        "extra_dumps_consume_zero_guest_frames": True,
        "checkpoints": expected_tags(original["checkpoints"]),
        "dense_window": [DENSE[0], DENSE[-1]],
        "source_core_is_disposably_cpu_instrumented": True,
        "native_exe_is_unmodified_source_frontier": True,
        "release_gate_credit": 0,
        "strict_complete_event_accepted": False,
    }
    (root / "dense-manifest.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def valid_logs(log: str, side: str, samples: list[tuple[int, str]]) -> dict:
    matches = []
    for f, t, receipt in HOST_DUMP.findall(log):
        if t not in {q[1] for q in samples}:
            continue
        if side == "original":
            good = ORIGINAL_DESCRIPTOR.fullmatch(receipt) is not None
        else:
            good = side == "native" and receipt == "ok"
        if not good:
            raise ValueError(f"{side} invalid real emulator receipt for {t}")
        matches.append((int(f), t))
    if matches != samples:
        raise ValueError(f"{side} missing/duplicate/mistimed actual emulator frame receipt")
    return {"script_host_receipts_verified": True,
            "transcript_sha256": sha(log.encode("utf-8")),
            "count": len(matches)}


def sample(frame: int, path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing independent exact original/native WRAM sample")
    data = path.read_bytes()
    if len(data) != 131072:
        raise ValueError("not an actual complete 128-KiB WRAM sample")
    def word(a: int) -> int:
        return int.from_bytes(data[a:a + 2], "little")
    return {"guest_sha256": sha(data),
            "p1_raw_air": word(0x0545),
            "p2_raw_air": word(0x0547),
            "p1_y": word(0x0415),
            "p2_y": word(0x0417),
            "p1_y_velocity": word(0x04BB),
            "p2_y_velocity": word(0x04BD),
            "active_race_byte": data[0x0313]}


def analyze(root: Path, *, rom: Path, native_exe: Path) -> dict:
    manifest_path = root / "dense-manifest.json"
    plan = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (plan.get("schema") != SCHEMA
            or plan.get("checkpoints") != [list(x) for x in expected_tags(source["checkpoints"])]
            or plan.get("source_original_input_sha256") != source.get("input_sha256")
            or plan.get("source_original_manifest_sha256") != sha((root / "manifest.json").read_bytes())
            or plan.get("original_18_frame_script_sha256") != source.get("script_sha256")
            or plan.get("derived_24_frame_script_sha256") != sha((root / "dense.script").read_bytes())
            or (root / "dense.script").read_text(encoding="utf-8") != dense_script(
                (root / "case.script").read_text(encoding="utf-8"))
            or plan.get("release_gate_credit") != 0
            or plan.get("strict_complete_event_accepted") is not False
            or plan.get("native_frontier_executable_sha256") != paired.NATIVE_FRONTIER_SHA
            or source.get("frontier_native_executable_sha256") != paired.NATIVE_FRONTIER_SHA
            or source.get("original_rom_sha256") != paired.ROM_SHA
            or plan.get("source_original_rom_sha256") != paired.ROM_SHA
            or plan.get("source_original_input_sha256") != sha((root / "case.input").read_bytes())
            or sha(rom.read_bytes()) != paired.ROM_SHA
            or sha(native_exe.read_bytes()) != paired.NATIVE_FRONTIER_SHA):
        raise ValueError("reused or mutated original/native executable, ROM, dense plan or source input")
    samples = expected_tags(source["checkpoints"])
    log_o = (root / "original.log").read_text(encoding="utf-8", errors="replace")
    log_n = (root / "native.log").read_text(encoding="utf-8", errors="replace")
    receipts = {"original": valid_logs(log_o, "original", samples),
                "native": valid_logs(log_n, "native", samples)}
    o = {f: sample(f, root / "original" / (t + ".wram.bin"))
         for f, t in samples}
    n = {f: sample(f, root / "native-run/dumps" / (t + ".wram.bin"))
         for f, t in samples}
    for side, rows in (("original", o), ("native", n)):
        for f, digest in PINNED_SNAPSHOT_SHA[side].items():
            if rows[f]["guest_sha256"] != digest:
                raise ValueError(f"{side} genuine guest frame {f} changed under read-only observer")
        if any(v["active_race_byte"] != 1 for f, v in rows.items()
               if f in DENSE):
            raise ValueError(side + " left authentic active 2P racing during source boundary")
    source_lines = [dict(frame=int(f), vcounter=int(v),
                         pc=p.upper()[:2] + ":" + p.upper()[2:],
                         address="7E:" + a.upper(), old=old, new=new,
                         static_candidate_pc=int(c) == 1)
                    for f, v, p, a, old, new, c in ORIGINAL_OPCODE.findall(log_o)]
    native_log = (root / "native-writers.log").read_text(encoding="utf-8",
                                                        errors="replace")
    if len(native_log) > 20_000_000:
        raise ValueError("unbounded native original/source CPU writer trace")
    native_lines = [dict(pre_run_host=int(f), bank=bank.upper(),
                         address=address.upper(), value=value.upper(),
                         width=int(width), source_scope=scope)
                    for f, bank, address, value, width, scope
                    in NATIVE_WRITER.findall(native_log)
                    if 2574 <= int(f) <= 2586]
    if not source_lines:
        raise ValueError("no real original opcode-scoped vertical/movement observations")
    if not native_lines:
        raise ValueError("no real native CPU-helper movement/address writes")
    targets = {f"{a:04X}" for a in TARGETS}
    source_lines = [x for x in source_lines if x["address"][3:] in targets]
    native_lines = [x for x in native_lines
                    if int(x["address"], 16) <= 0x0547
                    and int(x["address"], 16) >= 0x0415]
    rows = []
    for f in DENSE:
        before = o[f]
        after = n[f]
        rows.append({
            "absolute_host_frame": f,
            "original": before,
            "native": after,
            "same_host_named_raw_bytes_equal": all(
                before[k] == after[k] for k in (
                    "p1_raw_air", "p2_raw_air", "p1_y", "p2_y",
                    "p1_y_velocity", "p2_y_velocity")),
            "p1_y_native_minus_original": after["p1_y"] - before["p1_y"],
            "p2_y_native_minus_original": after["p2_y"] - before["p2_y"],
        })
    result = {
        "schema": SCHEMA,
        "source_run": PINNED_WITNESS_RUN,
        "source_artifact_zip_sha256": PINNED_WITNESS_ZIP,
        "original_native_host_receipts": receipts,
        "original_unchanged_source_core_proven_by_3_hashes": True,
        "native_same_frontier_binary_proven_by_3_hashes": True,
        "original_cpu_opcode_changes": source_lines,
        "native_cpu_helper_writes": native_lines,
        "source_pal_candidate_pcs_executed_while_observed":
            sorted({w["pc"] for w in source_lines if w["static_candidate_pc"]}),
        "dense_original_native_same_host": rows,
        "earliest_named_difference_in_observed_dense_window": next(
            (x["absolute_host_frame"] for x in rows
             if not x["same_host_named_raw_bytes_equal"]), None),
        "actual_cpu_instruction_and_ppu_phase_aligned": False,
        "raw_air_value_proves_physical_airborne": False,
        "strict_complete_event_accepted": False,
        "complete_event_release_credit": 0,
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("prepare", "classify"))
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--native-exe", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.mode == "prepare":
        plan = prepare(a.root)
        print(json.dumps({"checkpoints": len(plan["checkpoints"]),
                          "new_read_only_frame_dumps": len(EXTRA),
                          "complete_event_release_credit": 0}))
        return 0
    if not all((a.rom, a.native_exe, a.out)):
        ap.error("classify requires --rom, --native-exe and --out")
    report = analyze(a.root, rom=a.rom, native_exe=a.native_exe)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                     encoding="utf-8")
    print(json.dumps({
        "earliest_named_difference": report["earliest_named_difference_in_observed_dense_window"],
        "source_cpu_opcodes": len(report["original_cpu_opcode_changes"]),
        "native_cpu_helper_writes": len(report["native_cpu_helper_writes"]),
        "complete_event_release_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
