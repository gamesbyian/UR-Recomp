#!/usr/bin/env python3
"""Read a ``[dp],Y`` pointer once in Baldosa's emitter (RF-018).

The pinned Baldosa emitter (``baldosa/snesrecomp@075fbe4``,
``recompiler/v2/codegen.py::_segref_addr_expr``) resolves the indexed
direct-page indirect-long mode ``[dp],Y`` into two separate C expressions,
bank and offset, each of which re-reads the 3-byte pointer. Its comment
expects the C compiler to merge them, which is true for plain reads but not
for the paced-bus build: there every guest read is a ``cpu_read*_paced``
call that charges master clocks, so each ``LDA/STA/CMP/ADC/... [dp],Y``
reads and charges its pointer twice, 3 extra bus bytes (24 master clocks
from WRAM) per execution.

On the original USA ROM this slows the attract decompressor (``81:BB10 CMP
[$88],Y``: 103.6 vs 80.1 clocks per execution against Snes9x) by ~6.5% and
makes the second attract screen load one field longer than both references.

This stages, into a DISPOSABLE pinned Baldosa checkout, a read/write emit
that loads the pointer once in hardware order (low word, then bank), adds Y
with carry into the bank, and addresses the operand through that temporary.
Every other addressing mode, and the non-paced build's values, are
unchanged. ``src/gen`` must then be regenerated. Idempotent; refuses any
other framework revision.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

MARK = "UR_BALDOSA_DP_INDIRECT_LONG_POINTER_ONCE"
RELATIVE = Path("snesrecomp/recompiler/v2/codegen.py")

PINNED_READ_WRITE = '''def _emit_read(op: Read) -> List[str]:
    bank, addr = _segref_addr_expr(op.seg)
    return [f"{widths.ctype(op.width)} {_v(op.out)} = "
            f"{widths.read_fn(op.width)}(cpu, {bank}, {addr});"]


def _emit_write(op: Write) -> List[str]:
    bank, addr = _segref_addr_expr(op.seg)
    return [f"{widths.write_fn(op.width)}(cpu, {bank}, {addr}, {_v(op.src)});"]
'''

CORRECTED_READ_WRITE = '''# ''' + MARK + ''': an indexed [dp],Y operand reads its 3-byte
# pointer ONCE, in hardware order, into a temporary. _segref_addr_expr returns
# separate bank and offset expressions that each re-read the pointer; with the
# paced bus every read charges master clocks, so the duplicate charged 3 extra
# bus bytes per execution.
_UR_EA_SEQ = [0]


def _segref_hoisted(seg: SegRef) -> tuple:
    """(prelude lines, bank_expr, addr_expr) for a read/write operand."""
    if seg.kind == SegKind.DP_INDIRECT_LONG and seg.index is not None:
        _UR_EA_SEQ[0] += 1
        ea = f"_ea{_UR_EA_SEQ[0]}"
        ptr_addr = f"(uint16)(cpu->D + {seg.offset:#06x})"
        idx_reg = "cpu->X" if seg.index == Reg.X else "cpu->Y"
        prelude = [
            f"uint32 {ea} = (uint32)cpu_read16(cpu, 0x00, {ptr_addr});",
            f"{ea} |= (uint32)cpu_read8(cpu, 0x00, (uint16)({ptr_addr} + 2)) << 16;",
            f"{ea} += (uint32){idx_reg};",
        ]
        return prelude, f"(uint8)({ea} >> 16)", f"(uint16)({ea})"
    bank, addr = _segref_addr_expr(seg)
    return [], bank, addr


def _emit_read(op: Read) -> List[str]:
    prelude, bank, addr = _segref_hoisted(op.seg)
    return prelude + [f"{widths.ctype(op.width)} {_v(op.out)} = "
                      f"{widths.read_fn(op.width)}(cpu, {bank}, {addr});"]


def _emit_write(op: Write) -> List[str]:
    prelude, bank, addr = _segref_hoisted(op.seg)
    return prelude + [
        f"{widths.write_fn(op.width)}(cpu, {bank}, {addr}, {_v(op.src)});"]
'''

# The duplicated form the correction removes; it must exist where expected.
PINNED_INDEXED = '''        base24 = (f"(((uint32){bank_expr} << 16) | "
                  f"(uint32)cpu_read16(cpu, 0x00, {ptr_addr}))")
        eff24 = f"({base24} + (uint32){idx_reg})"
        return (f"(uint8)(({eff24}) >> 16)", f"(uint16)({eff24})")
'''


def patch(source: str) -> str:
    if MARK in source:
        if source.count(CORRECTED_READ_WRITE) != 1:
            raise ValueError("pointer-once marker present but correction altered")
        return source
    if source.count(PINNED_READ_WRITE) != 1 or source.count(PINNED_INDEXED) != 1:
        raise ValueError("pinned Baldosa [dp],Y emit not recognized; "
                         "do not splice against an unknown framework revision")
    return source.replace(PINNED_READ_WRITE, CORRECTED_READ_WRITE, 1)


# A generated line that reads one [dp] pointer twice (the pinned defect).
_DOUBLED = re.compile(
    r"cpu_read8(?:_paced)?\(cpu, 0x00, \(uint16\)\(\(uint16\)\(cpu->D \+ (0x[0-9a-f]+)\) \+ 2\)\)"
    r".*cpu_read8(?:_paced)?\(cpu, 0x00, \(uint16\)\(\(uint16\)\(cpu->D \+ \1\) \+ 2\)\)")


def count_doubled_pointer_reads(text: str) -> int:
    return sum(1 for line in text.split("\n") if _DOUBLED.search(line))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    ap.add_argument("--verify-gen", action="store_true",
                    help="after regen: fail if any generated line still reads a "
                         "[dp] pointer twice, or if no [dp],Y site was hoisted")
    args = ap.parse_args()
    game = args.game.resolve()
    if args.verify_gen:
        files = sorted((game / "src/gen").glob("bank*_v2.c"))
        if not files:
            raise SystemExit("no generated bank files to verify")
        doubled = hoisted = 0
        for f in files:
            text = f.read_text(encoding="utf-8")
            doubled += count_doubled_pointer_reads(text)
            hoisted += len(re.findall(r"\buint32 _ea\d+ = ", text))
        if doubled:
            raise SystemExit(f"{doubled} generated lines still read a [dp] pointer twice")
        if not hoisted:
            raise SystemExit("no hoisted [dp],Y pointers found: was src/gen regenerated?")
        print(f"verified {len(files)} generated files: {hoisted} [dp],Y pointers "
              "read once, none twice")
        return 0
    path = game / RELATIVE
    before = path.read_text(encoding="utf-8")
    after = patch(before)
    if after == before:
        print(f"[dp],Y pointer-once correction already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged [dp],Y pointer-once correction: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
