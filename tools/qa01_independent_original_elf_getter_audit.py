#!/usr/bin/env python3
"""QA01: inspect the genuine compiled ORIGINAL Snes9x stack-getter code path.

ROM-free ELF disassembly, independent of source-patch text. Proves what is (or
is not) emitted into exactly one pinned out-of-line getter/call site; it does
NOT prove all game instructions used it, actual memory-bus consumption timing,
native parity, or a shipping Windows event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SCHEMA = "ur-qa01-compiled-original-stack-getter-observer/1"
RF066_CORE_SHA256 = "9682cd2c2732541487c88cfef84f0d1b5a1005d4de0b00e95d43bac1cf9215c0"
GET_BYTE = "S9xGetByte(unsigned int)"
GET_WORD = "S9xGetWord(unsigned int, s9xwrap_t)"
SET_BYTE = "S9xSetByte(unsigned char, unsigned int)"
SET_WORD = "S9xSetWord(unsigned short, unsigned int, s9xwrap_t, s9xwriteorder_t)"
PULL_OPCODE = "Op68E0M0()"
SOURCES = (GET_BYTE, GET_WORD, SET_BYTE, SET_WORD, PULL_OPCODE)
SYM = re.compile(r"^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+[tT]\s+(.+)$")
CALL = re.compile(r"\bcall(?:q)?\s+.*<([^>]+)>")
HEX64 = re.compile("[0-9a-f]{64}\Z")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def symbol_locations(nm_text: str) -> dict:
    found: dict[str, list[tuple[int, int]]] = {label: [] for label in SOURCES}
    for line in nm_text.splitlines():
        match = SYM.fullmatch(line.strip())
        if match and match[3] in found:
            found[match[3]].append((int(match[1], 16), int(match[2], 16)))
    require(all(len(found[name]) == 1 and found[name][0][1] > 0
                for name in SOURCES),
            "missing/ambiguous exact compiled original getter/opcode symbol")
    spans = {name: {"start": point[0][0], "size": point[0][1],
                    "end": point[0][0] + point[0][1]}
             for name, point in found.items()}
    ordered = sorted(spans.values(), key=lambda item: item["start"])
    require(all(a["end"] <= b["start"] for a, b in zip(ordered, ordered[1:])),
            "overlapping compiled original ELF symbol ranges")
    return spans


def compiled_site(body: str) -> dict:
    # A real instruction call is not the same as a string constant existing
    # in .rodata or as a source-language instrumentation macro.
    instructions = [line for line in body.splitlines()
                    if re.match(r"^\s*[0-9a-f]+:\s", line)]
    require(instructions, "empty actual executable symbol disassembly")
    calls = [match.group(1) for line in instructions
             for match in CALL.finditer(line)]
    return {
        "call_destinations": calls,
        "direct_getenv_calls": sum("getenv" in dest for dest in calls),
        "direct_formatted_output_calls":
            sum("fprintf" in dest or "printf" in dest for dest in calls),
        "source_bus_ordinal_references":
            sum("ur_rf063_source_bus_seq" in line for line in instructions),
        "source_RF044_counter_references":
            sum("ur_rf044_orig_bus" in line for line in instructions),
    }


def classify(sites: dict[str, dict], spans: dict) -> dict:
    for name in SOURCES:
        require(name in sites and name in spans, "missing inspected symbol")
    getter_sides = {}
    for label in (GET_BYTE, GET_WORD):
        obj = sites[label]
        missing = not (obj["direct_getenv_calls"] or
                       obj["direct_formatted_output_calls"] or
                       obj["source_bus_ordinal_references"] or
                       obj["source_RF044_counter_references"])
        getter_sides[label] = missing
    setter_sides = {
        label: bool(sites[label]["direct_getenv_calls"] and
                    sites[label]["direct_formatted_output_calls"] and
                    sites[label]["source_bus_ordinal_references"] and
                    sites[label]["source_RF044_counter_references"])
        for label in (SET_BYTE, SET_WORD)
    }
    opcode = sites[PULL_OPCODE]
    direct = GET_WORD in opcode["call_destinations"]
    require(direct, "compiled original opcode does not directly call this getter")
    return {
        "schema": SCHEMA,
        "verified_compiled_symbols": spans,
        "sites": sites,
        "opcode_direct_call_to_uninstrumented_word_getter":
            bool(direct and getter_sides[GET_WORD]),
        "compiled_getbyte_no_direct_RF044_RF063_logger":
            getter_sides[GET_BYTE],
        "compiled_getword_no_direct_RF044_RF063_logger":
            getter_sides[GET_WORD],
        "both_compiled_setters_have_RF044_RF063_writer_hooks":
            all(setter_sides.values()),
        "setter_hook_controls": setter_sides,
        "compiled_opcode_postcall_sequence_references_present":
            opcode["source_bus_ordinal_references"] > 0,
        "actual_original_executable_guest_instruction_path_proven": False,
        "all_other_inlined_or_cloned_original_getters_qualified": False,
        "compiled_absence_cause_identified": False,
        "original_native_same_phase_reader_equivalence_proven": False,
        "accepted_USA_events": 0,
        "release_QA_gates": 0,
        "adjudication": "HOLD",
    }


def run_binary(binary: Path, expected_sha256: str) -> dict:
    require(HEX64.fullmatch(expected_sha256) is not None,
            "missing 64-hex original ELF SHA identity")
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    require(actual == expected_sha256, "genuine original executable hash mismatch")
    def execute(args: list[str]) -> str:
        return subprocess.check_output(args, text=True, timeout=30)
    locations = symbol_locations(execute(["nm", "-SnC", str(binary)]))
    sites = {}
    for name, loc in locations.items():
        body = execute(["objdump", "-d", "-C",
                        "--start-address=" + hex(loc["start"]),
                        "--stop-address=" + hex(loc["end"]), str(binary)])
        sites[name] = compiled_site(body)
    result = classify(sites, locations)
    result["verified_original_core_elf_sha256"] = actual
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_elf", type=Path)
    parser.add_argument("--expected-sha256", default=RF066_CORE_SHA256)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_binary(args.original_elf, args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("Original RF066 compiled getter/callsite inspected; causal evidence HOLD")


if __name__ == "__main__":
    main()
