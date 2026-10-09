#!/usr/bin/env python3
"""Bounded original/native 2014 scene witness, deliberately non-admitting."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

# Observation labels preserve historical source-relative times; no guest writes.
PROGRESS = (218, 604, 841, 1532, 1721)
ACTIVE_SAMPLES = ("scene-entered",) + tuple(
    f"progress-{frame:04d}" for frame in PROGRESS) + ("pre-result",)
SAMPLES = ACTIVE_SAMPLES + ("result-onset-candidate", "result-stable-candidate")
TIME = re.compile(r"^\\d+:[0-5]\\d\\.\\d\\d$")


def result_frames(log: str) -> dict:
    """Capture observed host frame counters; scripts may have different entry
    offsets and until-009F detection phases. Never compare absolute frames."""
    labels = ("scene-entered", "result-onset-candidate", "result-stable-candidate")
    values = {}
    for name in labels:
        matches = re.findall(r"(?m)^script f=(\\d+) dump " + re.escape(name) +
                             r"(?=\\s|$)", log)
        if len(matches) != 1:
            raise ValueError(f"expected exactly one logged {name} frame")
        values[name] = int(matches[0])
    if not (values["scene-entered"] < values["result-onset-candidate"] <
            values["result-stable-candidate"]):
        raise ValueError("non-monotonic observed result frames")
    return {
        "absolute": values,
        "onset_after_entry": (values["result-onset-candidate"] -
                              values["scene-entered"]),
        "stable_after_entry": (values["result-stable-candidate"] -
                               values["scene-entered"]),
    }


def p1_result_time(lines: list[str]) -> str | None:
    """Original scene is MIKE P1. Do not accept the CPU/qualifier clock."""
    for i, line in enumerate(lines):
        if line.strip() == "MIKE":
            if i + 1 < len(lines) and TIME.fullmatch(lines[i + 1].strip()):
                return lines[i + 1].strip()
            return None
    return None


def result_text_observations(original_dir: Path, native_dir: Path) -> dict:
    """Reuse the existing real VRAM/CGRAM/PPU title decoder, fail closed."""
    import extract_menu_visual_language as visual
    import probe_tier_opponents as textdecode
    lines = {
        label: textdecode.screen_texts(
            visual.Dump(directory, "result-stable-candidate"))
        for label, directory in (("original", original_dir), ("native", native_dir))
    }
    times = {label: p1_result_time(text) for label, text in lines.items()}
    labels_good = {
        label: any("LAPS ON ZOOM ZOO" in t for t in text) and
               any("BEST LAP" in t for t in text)
        for label, text in lines.items()
    }
    return {
        "decoded_stable_text": lines,
        "p1_result_times": times,
        "expected_circuit_labels_visible": labels_good,
        "stable_text_identical": lines["original"] == lines["native"],
        "p1_time_identical_and_visible": bool(times["original"]) and
                                         times["original"] == times["native"],
        "ppu_result_candidate": (all(labels_good.values()) and
                                 lines["original"] == lines["native"] and
                                 bool(times["original"]) and
                                 times["original"] == times["native"]),
    }


def course_identity(original_dir: Path, native_dir: Path, rom: Path) -> dict:
    """Decode stream 2 once; require exact loaded payload in both live guests.
    Two loader cursor bytes are legitimately mutable. No menu-only identity."""
    from analyze_rnc_streams import find_streams
    from rnc_method1 import unpack_method1
    from probe_runtime_course_payload import is_fully_loaded_course
    from probe_original_non_dragster_course_entry import USA_ROM_SHA256
    if hashlib.sha256(rom.read_bytes()).hexdigest() != USA_ROM_SHA256:
        raise ValueError("canonical USA ROM required for Zoo course residency")
    streams = list(find_streams(rom.read_bytes()))
    if len(streams) != 45:
        raise ValueError("USA ROM did not yield 45 course streams")
    decoded = unpack_method1(streams[1][1])  # Zoom Zoo, canonical stream 02
    witnessed = {}
    for label, directory in (("original", original_dir), ("native", native_dir)):
        witnessed[label] = {}
        for sample in ACTIVE_SAMPLES:
            w = (directory / f"{sample}.wram.bin").read_bytes()
            witnessed[label][sample] = bool(
                w[0x00CE] == 1 and w[0x0313] == 1 and
                is_fully_loaded_course(decoded, w[0x10000:]))
    return {
        "canonical_stream": 2,
        "decoded_size": len(decoded),
        "active_sample_residency": witnessed,
        "all_active_samples_correct": all(
            all(row.values()) for row in witnessed.values()),
    }


def snapshot(path: Path) -> dict:
    w = path.read_bytes()
    if len(w) != 0x20000:
        raise ValueError(f"{path}: expected 128 KiB WRAM, got {len(w)} bytes")
    u16 = lambda a: int.from_bytes(w[a:a+2], "little")
    return {
        "nmi_handler": f"0x{u16(0x53):04X}",
        "menu": w[0x009F],
        "race_flag": w[0x0313],
        "track_id": w[0x00CE],
        "p1_world_xy": [u16(0x0411), u16(0x0415)],
        "p2_world_xy": [u16(0x0413), u16(0x0417)],
        "p1_stored_contact": u16(0x0E95),
        "p2_stored_contact": u16(0x0E97),
        "p1_rider": w[0x017D],
        "p2_rider": w[0x017F],
        "p1_checkpoint": u16(0x1199),
        "p1_finish_gate": u16(0x119D),
        "p1_laps_remaining": u16(0x0EF1),
        "race_stopwatch_raw": [w[a] for a in (
            0x0E0F, 0x0E13, 0x0E17, 0x0E1B, 0x0E1F)],
    }


def analyze(original_dir: Path, native_dir: Path, metadata: dict,
            *, rom: Path | None = None, with_ppu: bool = False,
            frame_logs: dict[str, str] | None = None) -> dict:
    observations = {}
    for name, directory in (("original", original_dir), ("native", native_dir)):
        observations[name] = {
            sample: snapshot(directory / f"{sample}.wram.bin")
            for sample in SAMPLES
        }
    different = []
    for sample in SAMPLES:
        reference, candidate = observations["original"][sample], observations["native"][sample]
        for key in reference:
            if reference[key] != candidate[key]:
                different.append({
                    "sample": sample, "field": key,
                    "original": reference[key], "baldosa": candidate[key]})
    full_wram = {}
    for sample in SAMPLES:
        o = (original_dir / f"{sample}.wram.bin").read_bytes()
        n = (native_dir / f"{sample}.wram.bin").read_bytes()
        mismatched = [i for i, (a, b) in enumerate(zip(o, n)) if a != b]
        full_wram[sample] = {
            "guest_wram_bytes_compared": len(o),
            "original_wram_sha256": hashlib.sha256(o).hexdigest(),
            "baldosa_wram_sha256": hashlib.sha256(n).hexdigest(),
            "exact_match": not mismatched,
            "differing_byte_count": len(mismatched),
            "first_byte_offsets": [f"0x{i:05X}" for i in mismatched[:16]],
        }
    initial_good = all(
        rows["scene-entered"]["race_flag"] == 1 and
        rows["scene-entered"]["track_id"] == 1
        for rows in observations.values()
    )
    results = {
        label: (rows["result-onset-candidate"]["menu"] == 0xBC
                and rows["result-stable-candidate"]["menu"] == 0xBC
                and rows["result-stable-candidate"]["track_id"] == 1
                and rows["result-stable-candidate"]["race_flag"] != 1)
        for label, rows in observations.items()
    }
    timing = None
    if frame_logs is not None:
        timing = {label: result_frames(frame_logs[label])
                  for label in ("original", "native")}
        timing["onset_guest_relative_delta"] = (
            timing["original"]["onset_after_entry"] -
            timing["native"]["onset_after_entry"])
    ppu = result_text_observations(original_dir, native_dir) if with_ppu else None
    identity = course_identity(original_dir, native_dir, rom) if rom else None
    active_differences = [d for d in different if d["sample"] in ACTIVE_SAMPLES]
    contact_differences = [d for d in different
                           if d["field"] in ("p1_stored_contact", "p2_stored_contact")]
    contact_stage = ("active_window" if any(d in active_differences
                     for d in contact_differences) else
                     "result_transition_only" if contact_differences else "none")
    return {
        "schema_version": 2,
        "source": "2014 original Snes9x archived Zoom Zoo result scene input, independently fresh boot",
        "source_original_result_frame": 8353,
        "source_input": metadata,
        "original_and_baldosa_entered_zoo": initial_good,
        "original_reached_stable_circuit_result_state": results["original"],
        "baldosa_reached_stable_circuit_result_state": results["native"],
        "paired_result_state_candidate": initial_good and all(results.values())
                                          and not different,
        "active_sample_field_agreement": not active_differences,
        "contact_disagreement_first_stage": contact_stage,
        "observed_result_frame_phases": timing,
        "ppu_settled_result": ppu,
        "decoded_course_identity": identity,
        "result_text_and_course_identity_candidate": bool(
            initial_good and all(results.values()) and ppu and
            ppu["ppu_result_candidate"] and identity and
            identity["all_active_samples_correct"] and
            not active_differences and timing and
            timing["onset_guest_relative_delta"] == 0),
        "progression_samples": {
            label: [
                {"sample": name, "p1_checkpoint": rows[name]["p1_checkpoint"],
                 "p1_finish_gate": rows[name]["p1_finish_gate"],
                 "p1_laps_remaining": rows[name]["p1_laps_remaining"],
                 "p1_stored_contact": rows[name]["p1_stored_contact"],
                 "race_stopwatch_raw": rows[name]["race_stopwatch_raw"]}
                for name in ACTIVE_SAMPLES
            ] for label, rows in observations.items()
        },
        "observed_named_fields_compared": len(SAMPLES) *
                                          len(observations["original"][SAMPLES[0]]),
        "first_semantic_difference": different[0] if different else None,
        "all_sampled_differences": different,
        "raw_whole_wram_snapshots": full_wram,
        "raw_wram_exact_matched_count": sum(r["exact_match"]
                                            for r in full_wram.values()),
        "observations": observations,
        "complete_event_qa_credit": 0,
        "limitation": (
            "Displayed PPU result text is checked only when explicitly requested. "
            "A 2014 movie scene is a hypothesis for freshly booted guests, "
            "not the original entire movie execution state. A result-state "
            "candidate is NOT a complete accepted event."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--source-report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--calibration-report", type=Path)
    p.add_argument("--original-log", type=Path)
    p.add_argument("--native-log", type=Path)
    p.add_argument("--rom", type=Path)
    p.add_argument("--with-ppu", action="store_true")
    args = p.parse_args()
    meta = json.loads(args.source_report.read_text(encoding="utf-8"))
    if bool(args.original_log) != bool(args.native_log):
        p.error("both original and native logs required for event phase")
    logs = ({"original": args.original_log.read_text(),
             "native": args.native_log.read_text()}
            if args.original_log else None)
    r = analyze(args.original, args.native, meta, rom=args.rom,
                with_ppu=args.with_ppu, frame_logs=logs)
    if args.calibration_report:
        r["calibrated_movie_input"] = json.loads(
            args.calibration_report.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: r[key] for key in (
        "original_and_baldosa_entered_zoo",
        "original_reached_stable_circuit_result_state",
        "baldosa_reached_stable_circuit_result_state",
        "paired_result_state_candidate",
        "first_semantic_difference",
        "raw_wram_exact_matched_count",
        "contact_disagreement_first_stage",
        "observed_result_frame_phases",
        "ppu_settled_result",
        "decoded_course_identity",
        "result_text_and_course_identity_candidate",
        "complete_event_qa_credit")}))
    return 0 if r["original_and_baldosa_entered_zoo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
