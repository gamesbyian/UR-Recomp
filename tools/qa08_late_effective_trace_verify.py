#!/usr/bin/env python3
"""Verify late effective-PPU logs without promoting them to original/native parity.

The tool checks source stage, full input/CRC byte receipts, old Snes9x pixel
identity and eight genuine source anchors. A textual observer is not proof of
unchanged Windows executable behavior, beam alignment or renderer correctness.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

try:
    from tools.qa08_late_effective_cgram_probe import POINTS
except ImportError:
    from qa08_late_effective_cgram_probe import POINTS

EXPECTED_CRC = "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568"
EXPECTED_ROUTE = "ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194"
ORIGINAL_ZIP = "72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e"
ORIGINAL_5183_BGRX = "f0ee58c682776592d8a93003a42c508629c49973b206d6a6da2c71ec9dc993b7"
ARCHIVED_NATIVE_OUTER = "832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727"
ARCHIVED_NATIVE_INNER = "c36fdd0238735e739219b013d25665e42a008a7827ee97631a322217c9f4f0cd"
ARCHIVED_NATIVE_5184_P7 = "8dae60c1433aa26cd6edc20edda980d1dec17e8935a799d7edc6d0878ae387a8"
P7_HEADER = (b"P7\nWIDTH 256\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\n"
             b"TUPLTYPE RGB_ALPHA\nENDHDR\n")
PREFIX_SOURCE = "UR_QA08_LATE_PPU_SOURCE "
PREFIX_FINAL = "UR_QA08_LATE_PPU_FINAL "
PREFIX_SPAN_SOURCE = "UR_QA08_LATE_SPAN_SOURCE "
PREFIX_SPAN_FINAL = "UR_QA08_LATE_SPAN_FINAL "
PREFIX_SPAN_OBJECT_OVERRIDE = "UR_QA08_LATE_SPAN_OBJECT_OVERRIDE "
DEC_SOURCE = ("frame", "x", "logical_y", "ppu_line", "sub", "layer", "directcolor")
HEX_SOURCE = ("index", "selected_rgb555", "cgram_index_word",
              "cgram6c", "cgram6d", "cgram6e", "cgram6f",
              "inidisp", "cgadsub", "cgwsel")
DEC_FINAL = ("frame", "x", "logical_y", "ppu_line")
HEX_FINAL = ("inidisp", "fixed", "tm", "ts")
# Authentic original/native RGB5 at guest5184, eight source-qualified points.
EXPECTED_GRAY = {
    (70, 58): (20, 17), (202, 182): (20, 17),
    (84, 77): (15, 20), (175, 145): (15, 20),
    (53, 41): (16, 15), (187, 160): (16, 15),
    (65, 52): (17, 16), (190, 161): (17, 16),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_row(line: str) -> tuple[str, dict] | None:
    if PREFIX_SPAN_OBJECT_OVERRIDE in line:
        raise ValueError("host OBJ palette override is not a CGRAM witness")
    markers = [p for p in (PREFIX_SOURCE, PREFIX_FINAL,
                           PREFIX_SPAN_SOURCE, PREFIX_SPAN_FINAL) if p in line]
    if not markers:
        return None
    if len(markers) != 1:
        raise ValueError("ambiguous effective-PPU logger marker")
    prefix = markers[0]
    fields = {}
    for token in line.split(prefix, 1)[1].strip().split():
        if token.count("=") != 1:
            raise ValueError("malformed logger field")
        key, value = token.split("=", 1)
        if key in fields:
            raise ValueError("duplicate logger field")
        fields[key] = value
    kind = "source" if prefix in (PREFIX_SOURCE, PREFIX_SPAN_SOURCE) else "final"
    renderer = "span" if prefix in (PREFIX_SPAN_SOURCE, PREFIX_SPAN_FINAL) else "legacy"
    dec = DEC_SOURCE if kind == "source" else DEC_FINAL
    hx = HEX_SOURCE if kind == "source" else HEX_FINAL
    required = set(dec) | set(hx) | ({"RGB8"} if kind == "final" else set())
    if set(fields) != required:
        raise ValueError("missing or unknown effective-PPU fields")
    row = {"renderer": renderer}
    for k in dec:
        if not fields[k].isdigit():
            raise ValueError("nondecimal observer value")
        row[k] = int(fields[k], 10)
    for k in hx:
        if not (1 <= len(fields[k]) <= 4 and
                all(c in "0123456789abcdefABCDEF" for c in fields[k])):
            raise ValueError("non-hexadecimal PPU register value")
        row[k] = int(fields[k], 16)
    if kind == "final":
        rgb = fields["RGB8"].split(",")
        if len(rgb) != 3 or any(not x.isdigit() for x in rgb):
            raise ValueError("invalid RGB8 source pixel")
        row["RGB8"] = tuple(map(int, rgb))
    if (not 5176 <= row["frame"] <= 5186 or
        (row["x"], row["logical_y"]) not in POINTS or
        row["ppu_line"] != row["logical_y"] + 1):
        raise ValueError("source stage frame/position not authenticated")
    if kind == "source":
        if (row["sub"] not in (0, 1) or row["directcolor"] not in (0, 1) or
            not 0 <= row["layer"] <= 6 or not 0 <= row["index"] <= 255 or
            any(not 0 <= row[k] <= 0x7fff for k in
                ("selected_rgb555", "cgram_index_word",
                 "cgram6c", "cgram6d", "cgram6e", "cgram6f")) or
            any(not 0 <= row[k] <= 255 for k in
                ("inidisp", "cgadsub", "cgwsel"))):
            raise ValueError("impossible native effective-source state")
        if not row["directcolor"] and row["selected_rgb555"] != row["cgram_index_word"]:
            raise ValueError("resolver selected colour disagrees with CGRAM")
        # Independently logged slots must match an indexed selected word.
        if not row["directcolor"] and 0x6c <= row["index"] <= 0x6f:
            slot = ("cgram6c", "cgram6d", "cgram6e", "cgram6f")[row["index"] - 0x6c]
            if row["cgram_index_word"] != row[slot]:
                raise ValueError("indexed effective CGRAM word disagrees with slot snapshot")
        if row["directcolor"] and row["layer"] >= 4:
            raise ValueError("direct color cannot be OBJ or backdrop")
    elif (any(c > 255 for c in row["RGB8"]) or
          any(row[k] > 255 for k in ("inidisp", "tm", "ts")) or
          row["fixed"] > 0x7fff):
        raise ValueError("invalid composed source pixel or register")
    return kind, row


def summarize_trace(trace: str, *, require_full_window: bool = False) -> dict:
    if len(trace) > 24_000_000:
        raise ValueError("unbounded native observer output")
    source, final = {}, {}
    events = 0
    for line in trace.splitlines():
        parsed = parse_row(line)
        if parsed is None:
            continue
        kind, row = parsed
        events += 1
        if events > 1000:
            raise ValueError("unbounded native observer events")
        key = (row["frame"], row["x"], row["logical_y"])
        if kind == "source":
            key += (row["sub"],)
            if key in source:
                raise ValueError("duplicate native source pixel invocation")
            source[key] = row
        else:
            if key in final:
                raise ValueError("duplicate native final pixel invocation")
            final[key] = row
    if not source or not final:
        raise ValueError("missing actual source or final pixel observations")
    renderers = {r["renderer"] for r in source.values()} | {
        r["renderer"] for r in final.values()}
    if len(renderers) != 1:
        raise ValueError("mixed renderer identities across effective-PPU window")
    if require_full_window:
        expected = {(frame, x, y)
                    for frame in range(5176, 5187) for x, y in POINTS}
        main_keys = {key[:3] for key in source if key[3] == 0}
        if main_keys != expected or set(final) != expected:
            raise ValueError("incomplete 11-frame main-source/final window")
    results = []
    for x, y in POINTS:
        key = (5184, x, y)
        if key not in final or key + (0,) not in source:
            raise ValueError("missing guest5184 actual anchor source/final")
        main, end = source[key + (0,)], final[key]
        if main["inidisp"] != end["inidisp"]:
            raise ValueError("source/final brightness register mismatch")
        if main["renderer"] != end["renderer"]:
            raise ValueError("main pixel and composed pixel used different renderer")
        observed = tuple(v >> 3 for v in end["RGB8"])
        reference, old_native = EXPECTED_GRAY[(x, y)]
        results.append({
            "xy": [x, y],
            "authentic_original_RGB5": [reference] * 3,
            "archived_native_RGB5": [old_native] * 3,
            "new_native_final_RGB5": list(observed),
            "new_native_matches_original_RGB5": observed == (reference,) * 3,
            "new_native_matches_old_native_RGB5": observed == (old_native,) * 3,
            "main_selected_palette_index": (None if main["directcolor"]
                                            else main["index"]),
            "main_actual_resolved_rgb555": f"{main['selected_rgb555']:04x}",
            "main_current_index_CGRAM_word": f"{main['cgram_index_word']:04x}",
            "main_directcolor": bool(main["directcolor"]),
            "main_layer": main["layer"],
            "actual_renderer": main["renderer"],
            "current_main_CGRAM_6c_6f": [
                f"{main[k]:04x}" for k in
                ("cgram6c", "cgram6d", "cgram6e", "cgram6f")
            ],
            "original_native_same_beam_proven": False,
        })
    return {
        "schema": "QA08-late-effective-PPU-observer-readonly/1",
        "bounded_source_observations": len(source),
        "bounded_final_observations": len(final),
        "guest5184_anchor_count": len(results),
        "observed_span_anchors": sum(x["actual_renderer"] == "span"
                                    for x in results),
        "all_anchors_actual_span_renderer": all(
            x["actual_renderer"] == "span" for x in results),
        "anchors": results,
        "identical_native_binary_to_archived_CGRAM_writer_proven": False,
        "original_native_beam_and_CPU_instruction_parity_proven": False,
        "original_2014_hardware_DAC_equivalence_proven": False,
        "instrumentation_noninterference_proven_by_text": False,
        "QA08_QA10_or_release_authorized": False,
    }


def verify_archived_native_pixels(native_outer: Path) -> dict:
    """Recheck the original benchmark's eight native P7 positions from real ZIP."""
    raw = native_outer.read_bytes()
    if sha(raw) != ARCHIVED_NATIVE_OUTER:
        raise ValueError("archived compiled Windows P7 outer ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        nested = outer.read("qa08-premath-source-images.zip")
    if sha(nested) != ARCHIVED_NATIVE_INNER:
        raise ValueError("archived compiled Windows P7 nested ZIP SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(nested)) as images:
        frame = images.read("source/ur-baldosa-original-source-005184.pam")
    if (sha(frame) != ARCHIVED_NATIVE_5184_P7 or
        len(frame) != len(P7_HEADER) + 256 * 224 * 4 or
        not frame.startswith(P7_HEADER)):
        raise ValueError("archived compiled Windows guest5184 P7 member changed")
    for (x, y), (_, expected_native) in EXPECTED_GRAY.items():
        pos = len(P7_HEADER) + (y * 256 + x) * 4
        rgb = frame[pos:pos+4]
        if len(rgb) != 4 or rgb[3] or tuple(v >> 3 for v in rgb[:3]) != (
            expected_native,) * 3:
            raise ValueError("archived Windows source RGB5 anchor changed")
    return {
        "archived_native_outer_SHA256": ARCHIVED_NATIVE_OUTER,
        "archived_native_nested_SHA256": ARCHIVED_NATIVE_INNER,
        "archived_native_5184_P7_SHA256": ARCHIVED_NATIVE_5184_P7,
        "actual_archived_native_anchor_pixels_authenticated": 8,
    }


def verify(on: Path, off: Path, original: Path, crc_on: Path, crc_off: Path,
           route_on: Path, route_off: Path, native_outer: Path) -> dict:
    for label, path, required in (
        ("observer ON guest CRC", crc_on, EXPECTED_CRC),
        ("observer OFF guest CRC", crc_off, EXPECTED_CRC),
        ("observer ON controller route", route_on, EXPECTED_ROUTE),
        ("observer OFF controller route", route_off, EXPECTED_ROUTE),
    ):
        if sha(path.read_bytes()) != required:
            raise ValueError(label + " SHA mismatch")
    if sha(original.read_bytes()) != ORIGINAL_ZIP:
        raise ValueError("original Snes9x inner archive SHA differs")
    with zipfile.ZipFile(original) as source:
        frame = source.read("frames/frame_005183_256x224.raw")
    if sha(frame) != ORIGINAL_5183_BGRX or len(frame) != 256 * 224 * 4:
        raise ValueError("original source pixel 5183 SHA mismatch")
    for (x, y), (expected, _) in EXPECTED_GRAY.items():
        pos = (y * 256 + x) * 4
        if (frame[pos + 2] >> 3, frame[pos + 1] >> 3,
            frame[pos] >> 3) != (expected,) * 3:
            raise ValueError("original source anchor RGB5 changed")
    archived = verify_archived_native_pixels(native_outer)
    off_text = off.read_text(encoding="utf-8", errors="replace")
    if any(p in off_text for p in (
        PREFIX_SOURCE, PREFIX_FINAL, PREFIX_SPAN_SOURCE, PREFIX_SPAN_FINAL,
        PREFIX_SPAN_OBJECT_OVERRIDE)):
        raise ValueError("OFF control contains unexpected effective observer")
    result = summarize_trace(on.read_text(encoding="utf-8", errors="replace"),
                             require_full_window=True)
    result.update({
        **archived,
        "original_inner_SHA256": ORIGINAL_ZIP,
        "original_5183_BGRX_SHA256": ORIGINAL_5183_BGRX,
        "on_off_guest_CRC_transcript_SHA256": EXPECTED_CRC,
        "on_off_controller_route_file_SHA256": EXPECTED_ROUTE,
        "guest_consumed_inputs_proven_by_file_SHA_alone": False,
        "whole_P7_ON_OFF_noninterference_proven": False,
        "compiled_Windows_PE_identity_proven": False,
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("on", "off", "original-inner", "native-outer", "crc-on", "crc-off",
                 "route-on", "route-off"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    a = parser.parse_args()
    try:
        receipt = verify(a.on, a.off, a.original_inner, a.crc_on,
                         a.crc_off, a.route_on, a.route_off, a.native_outer)
        if a.out.exists():
            raise ValueError("would overwrite prior source evidence")
        a.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, "QA08_EFFECTIVE_PPU_EVIDENCE_REFUSED: " + str(exc) + "\n")
    print("QA08_EFFECTIVE_PPU_DIAGNOSTIC_ONLY anchors=8 release=0")


if __name__ == "__main__":
    main()
