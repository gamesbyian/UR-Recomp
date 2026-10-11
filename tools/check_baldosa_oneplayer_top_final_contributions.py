#!/usr/bin/env python3
"""Exact live 1P native PPU contribution test, independent slot98/99 deletions.

Use the already-validated frame2208 342x224 Original PPU/source98/source99
captures and *two further* independent single-slot RemoveFromGame counterfactual
runs. The PPU renders the changed final pixels itself; no host paint, guest
writes, new asset or 342-wide Remastered activation can result from this tool.
A source-emitted pixel may be fully hidden. Zero changed pixels is a valid
negative if all controls match; changing a pixel outside the emitted slot is
a failure. This does not prove which other layer covered a hidden pixel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT
except ModuleNotFoundError:
    from check_baldosa_wide_slot_final_visibility import read_pam, WIDTH, HEIGHT

FRAME = 2208
CRC_FRAMES = 5447
REPORT_STATUS = "native-1p-paired-top-oam-source-truth"


def inspect(original: Path, sources: dict[int, Path], removed: dict[int, Path],
            crcs: dict[str, Path], logs: dict[int, Path],
            source_report: Path) -> dict:
    """All inputs are original native output; reject swapped files and logs."""
    name = f"ur-baldosa-ws342-{FRAME:06d}.pam"
    if original.name != name or any(p.name != name for p in removed.values()):
        raise ValueError("native original/counterfactual frame identity mismatch")
    if (set(sources) != {98, 99} or set(removed) != {98, 99} or
            set(logs) != {98, 99} or
            set(crcs) != {"stock", "probe98", "probe99", "removed98", "removed99"}):
        raise ValueError("exact pair source/removal/CRC roles required")
    for slot in (98, 99):
        if sources[slot].name != f"ur-baldosa-ws342-obj-slot{slot}-frame{FRAME:06d}.pam":
            raise ValueError("native isolated slot/source frame identity mismatch")
        if original.resolve() == removed[slot].resolve():
            raise ValueError("independent counterfactual must not alias Original path")
    if removed[98].resolve() == removed[99].resolve():
        raise ValueError("slot removal outputs must originate from separate runs")
    streams = [crcs[key].read_bytes().splitlines() for key in
               ("stock", "probe98", "probe99", "removed98", "removed99")]
    if len(streams[0]) != CRC_FRAMES or any(s != streams[0] for s in streams[1:]):
        raise ValueError("native original and counterfactual 5447-frame guest CRC mismatch")
    report = json.loads(source_report.read_text(encoding="utf-8"))
    if (report.get("status") != REPORT_STATUS or
            report.get("native_guest_frame") != FRAME or
            report.get("native_original_guest_crc_identical") != CRC_FRAMES or
            report.get("native_1x_and_4x_source_frames_identical") != 7 or
            report.get("independent_original_guest_processes") != 5 or
            report.get("no_sprite_removal_or_guest_mutation") is not True or
            report.get("source_slot_emission_accepted") is not True or
            report.get("individual_final_bg_or_obj_priority_accepted") is not False or
            report.get("authored_hd_or_wide_replacement_accepted") is not False):
        raise ValueError("missing accepted independent Original/slot-source provenance")
    records = report.get("original_top_slot98_and_slot99_sources")
    if (not isinstance(records, list) or len(records) != 2 or
            [rec.get("original_oam_slot") for rec in records
             if isinstance(rec, dict)] != [98, 99]):
        raise ValueError("untrusted or swapped original top PPU slot attribution")

    stock = read_pam(original)
    measured = {}
    contribution_masks = {}
    source_masks = {}
    for slot, rec in zip((98, 99), records):
        alpha = read_pam(sources[slot])
        counterfactual = read_pam(removed[slot])
        if hashlib.sha256(alpha).hexdigest() != rec.get("rgba_sha256"):
            raise ValueError(f"slot {slot}: source alpha SHA mismatch")
        native = rec.get("native_source", {})
        expected = native.get("top_opaque_source_pixels", -1) + native.get(
            "bottom_opaque_source_pixels", -1)
        if (expected <= 0 or
                rec.get("rgb_vs_final_observation", {}).get("isolated_source_opaque") != expected):
            raise ValueError(f"slot {slot}: source report has no verified real OBJ")
        marker = (f"UR_RACER_HD_WIDE_REMOVE_SLOT frame={FRAME} slot={slot} "
                  "status=armed guest_unchanged=1")
        lines = logs[slot].read_text(encoding="utf-8", errors="replace").splitlines()
        if sum(line.strip() == marker for line in lines) != 1:
            raise ValueError(f"slot {slot}: missing/duplicate authentic native remove marker")

        emitted, changed, unexpected = set(), set(), set()
        matches = 0
        for at in range(0, len(stock), 4):
            pixel = at // 4
            has_alpha = alpha[at + 3] != 0
            if has_alpha:
                emitted.add(pixel)
                if alpha[at:at + 3] == stock[at:at + 3]:
                    matches += 1
            if stock[at:at + 4] != counterfactual[at:at + 4]:
                (changed if has_alpha else unexpected).add(pixel)
        if len(emitted) != expected:
            raise ValueError(f"slot {slot}: source pixels disagree with PPU provenance")
        if unexpected:
            y, x = divmod(min(unexpected), WIDTH)
            raise ValueError(f"slot {slot}: native PPU changed outside OBJ alpha at ({x},{y})")
        source_masks[slot] = emitted
        contribution_masks[slot] = changed
        sample = [list(reversed(divmod(index, WIDTH))) for index in sorted(changed)[:12]]
        measured[str(slot)] = {
            "original_oam_slot": slot,
            "source_emitted_alpha_pixels": len(emitted),
            "source_rgb_matches_final_original": matches,
            "source_rgb_differs_final_original": len(emitted) - matches,
            "changed_final_ppu_pixels_after_native_slot_removal": len(changed),
            "source_emitted_but_no_final_delta": len(emitted - changed),
            "changed_pixels_outside_slot_source": 0,
            "changed_raster_0_111": sum(index // WIDTH < 112 for index in changed),
            "changed_raster_112_223": sum(index // WIDTH >= 112 for index in changed),
            "bounded_changed_original_xy_examples": sample,
            "original_rgba_sha256": hashlib.sha256(stock).hexdigest(),
            "isolated_source_rgba_sha256": rec["rgba_sha256"],
            "counterfactual_final_rgba_sha256":
                hashlib.sha256(counterfactual).hexdigest(),
            "native_ppu_contribution_positive": bool(changed),
            "foreground_bg_or_competing_obj_owner_proven": False,
        }
    source_overlap = len(source_masks[98] & source_masks[99])
    changed_overlap = len(contribution_masks[98] & contribution_masks[99])
    return {
        "schema_version": 1,
        "status": "native-oneplayer-paired-single-slot-final-counterfactual",
        "native_guest_frame": FRAME,
        "source_report_status": REPORT_STATUS,
        "all_five_native_guest_crc_streams_identical": CRC_FRAMES,
        "source_reference_five_processes_and_7_original_frames_verified": True,
        "independent_single_slot_removal_processes": 2,
        "slots": measured,
        "emitted_source_coordinate_overlap": source_overlap,
        "joint_contribution_coordinate_overlap": changed_overlap,
        "distinct_changed_final_ppu_coordinates":
            len(contribution_masks[98] | contribution_masks[99]),
        "any_native_final_contribution_proven": any(contribution_masks.values()),
        "complete_per_slot_final_visibility_proven": True,
        "authored_hd_replacement_or_sprite_removal_admitted": False,
        "widescreen_remastered_or_windows_release_admitted": False,
        "limits": ("Independent exact-frame PPU removal counterfactuals find changed "
                   "final Original pixels, not a reusable full BG/OBJ priority "
                   "mask, a causal explanation for source-hidden pixels, "
                   "or authorization to change the Original renderer."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("original", "source98", "source99", "removed98", "removed99",
                 "stock-crc", "probe98-crc", "probe99-crc", "removed98-crc",
                 "removed99-crc", "log98", "log99", "source-report", "out"):
        p.add_argument("--" + flag, required=True, type=Path)
    args = p.parse_args()
    result = inspect(args.original,
                     {98: args.source98, 99: args.source99},
                     {98: args.removed98, 99: args.removed99},
                     {"stock": args.stock_crc, "probe98": args.probe98_crc,
                      "probe99": args.probe99_crc,
                      "removed98": args.removed98_crc,
                      "removed99": args.removed99_crc},
                     {98: args.log98, 99: args.log99}, args.source_report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print("UR_QA08_1P_NATIVE_PPU_CONTRIBUTION " + result["status"] +
          " source98=" + str(result["slots"]["98"]["source_emitted_alpha_pixels"]) +
          " final98=" + str(result["slots"]["98"]["changed_final_ppu_pixels_after_native_slot_removal"]) +
          " source99=" + str(result["slots"]["99"]["source_emitted_alpha_pixels"]) +
          " final99=" + str(result["slots"]["99"]["changed_final_ppu_pixels_after_native_slot_removal"]) +
          " overlap=" + str(result["joint_contribution_coordinate_overlap"]) +
          " hd_admitted=0")


if __name__ == "__main__":
    main()
