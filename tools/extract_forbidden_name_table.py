#!/usr/bin/env python3
"""Locate and verify the stock forbidden-name table and its matching rule.

Decision served: the modern COOL NAME! Easter egg (analysis/frontend-modernization-policy.json,
feature ``forbidden-name-rejection``) must detect exactly the names the original
rejects, then accept them. This tool recovers that detection rule from the
canonical ROM so a host implementation can reuse it without hand-copying words.

Recovered structure (USA retail, bank 83):
- ``83:84DD`` scanner: for every start offset in the name buffer (until ``FF``)
  and for each of 71 words, ``JSR 83:8779``; any hit reports a match. The inner
  loop counts words to 0x47, then ``INC $04`` / ``BRL`` advances the name offset,
  so the test is a substring match anywhere in the stored (lowercase) name.
- ``83:8537`` pointer table: 71 little-endian bank-83 pointers.
- ``83:85C5..8778`` word table: lowercase ASCII words, each ``FF``-terminated.
- ``83:8779`` matcher: compares table bytes against the name until the table
  word's ``FF`` (match) or the first difference (no match), i.e. a prefix test
  at one name position.

The committed report records locations, count, length range and a hash only.
The words themselves stay derivable from the tracked ROM (``words_from_rom``).

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
BANK = 0x83
SCANNER = 0x84DD
POINTER_TABLE = 0x8537
WORD_COUNT = 71
MATCHER = 0x8779
# Opcode signatures (hand-decoded, 8-bit A with SEP #$20 context).
MATCHER_SIGNATURE = bytes.fromhex("08e220485abd0000c9fff009d90000d00ae8c880f07a6828e202607a6828c20260")
SCANNER_CALL = bytes.fromhex("aabf378583aa207987")  # TAX / LDA 83:8537,X / TAX / JSR $8779
SCANNER_ENTRY_LONG = bytes.fromhex("22d98483")    # JSL 83:84D9 (JSR $84DD; RTL)
EDITOR_OK_CHECK = 0xA4A3                          # 80:A4A3, in the shared name editor's OK path
EDITOR_ENTRY_CALL = bytes.fromhex("20e3a1")       # JSR $A1E3 (shared name editor, X = buffer)
EDITOR_CALLERS = {0x9E7C: "WHAT IS YOUR LEAGUE CALLED", 0xD47E: "WHAT IS YOUR PLAYER CALLED"}


def lorom(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)


def words_from_rom(rom: bytes) -> list[bytes]:
    base = lorom(BANK, POINTER_TABLE)
    out = []
    for i in range(WORD_COUNT):
        ptr = rom[base + 2 * i] | rom[base + 2 * i + 1] << 8
        start = lorom(BANK, ptr)
        end = rom.index(b"\xff", start)
        out.append(rom[start:end])
    return out


def is_forbidden(name: str, words: list[bytes]) -> bool:
    """Stock rule: any table word occurring anywhere in the lowercase stored name."""
    stored = name.lower().encode("latin1")
    return any(word in stored for word in words)


def find_all(rom: bytes, needle: bytes) -> list[int]:
    out, i = [], rom.find(needle)
    while i >= 0:
        out.append(i)
        i = rom.find(needle, i + 1)
    return out


def analyze(rom: bytes) -> dict:
    words = words_from_rom(rom)
    first = lorom(BANK, rom[lorom(BANK, POINTER_TABLE)] | rom[lorom(BANK, POINTER_TABLE) + 1] << 8)
    last_ptr = lorom(BANK, POINTER_TABLE) + 2 * (WORD_COUNT - 1)
    last = lorom(BANK, rom[last_ptr] | rom[last_ptr + 1] << 8)
    table_end = rom.index(b"\xff", last)
    blob = rom[first:table_end + 1]
    checks = {
        "matcher_signature_at_83_8779": rom[lorom(BANK, MATCHER):lorom(BANK, MATCHER) + len(MATCHER_SIGNATURE)] == MATCHER_SIGNATURE,
        "scanner_calls_matcher_through_pointer_table": SCANNER_CALL in rom[lorom(BANK, SCANNER):lorom(BANK, SCANNER) + 0x60],
        "pointer_table_is_contiguous_words": all(
            w.isalpha() and w == w.lower() for w in words),
        "word_table_ends_immediately_before_matcher": table_end + 1 == lorom(BANK, MATCHER),
        "default_racer_names_are_not_forbidden": not any(
            is_forbidden(n, words) for n in ("mike", "andrew", "martin", "melissa", "amy", "malcolm", "michelle", "colin",
                                             "dave", "tony", "carol", "craig", "ken", "robbie", "alice", "steve")),
        "publicly_reported_examples_are_forbidden": is_forbidden("sonic", words) and is_forbidden("sega", words),
        "scanner_has_one_caller_in_shared_editor": find_all(rom, SCANNER_ENTRY_LONG) == [lorom(0x80, EDITOR_OK_CHECK)],
        "shared_editor_serves_player_and_league_names": sorted(
            o for o in find_all(rom, EDITOR_ENTRY_CALL) if o < 0x8000) == sorted(lorom(0x80, a) for a in EDITOR_CALLERS),
    }
    return {
        "schema_version": 1,
        "purpose": "Exact stock forbidden-name detection for the modern COOL NAME! acknowledgement (detect like stock, then accept).",
        "rom": "reference/roms/retail/Uniracers_USA.sfc",
        "scanner": f"{BANK:02X}:{SCANNER:04X}",
        "matcher": f"{BANK:02X}:{MATCHER:04X}",
        "pointer_table": f"{BANK:02X}:{POINTER_TABLE:04X}",
        "word_table": f"{BANK:02X}:{0x8000 + first % 0x8000:04X}..{BANK:02X}:{0x8000 + table_end % 0x8000:04X}",
        "word_count": len(words),
        "word_length_range": [min(map(len, words)), max(map(len, words))],
        "word_table_sha256": hashlib.sha256(blob).hexdigest(),
        "rule": "case-insensitive substring: a name is forbidden if any table word occurs at any position of the stored lowercase name",
        "rule_evidence": "static decode of 83:84DD (outer INC $04 over name offsets until FF, inner loop over 71 pointers) and 83:8779 (prefix compare); runtime-confirmed for player names by tools/probe_name_entry.py (SONIC, XSEGAX, BASSIST rejected; ZED accepted)",
        "applies_to": "player and League names: the only scanner call (80:A4A3) is in the shared name editor 80:A1E3, entered from 80:9E7C ('WHAT IS YOUR LEAGUE CALLED') and 80:D47E ('WHAT IS YOUR PLAYER CALLED'); League path static only",
        "words_committed": False,
        "words_note": "Derive with tools/extract_forbidden_name_table.words_from_rom(); the list contains profanity plus 'sega' and 'sonic'.",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", type=Path, default=ROM)
    ap.add_argument("--out", type=Path, default=ROOT / "analysis/generated/forbidden-name-table.json")
    ap.add_argument("--check", metavar="NAME", help="report whether NAME would be rejected by stock")
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    if args.check:
        print("forbidden" if is_forbidden(args.check, words_from_rom(rom)) else "allowed")
        return 0
    report = analyze(rom)
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report["checks"], indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
