#!/usr/bin/env python3
"""Charge Baldosa's static block clocks in instruction order around I/O (RF-017).

The pinned Baldosa recompiler (``baldosa/snesrecomp@075fbe4``, unchanged at
upstream ``ec8a3e7``) emits ``paced_bus`` code that adds a whole block's
opcode/operand fetches and internal cycles to ``cpu->master_cycles`` in one
constant at block entry, then lets the paced accessors charge each data byte
when it is transferred. For WRAM and ROM data this is only bookkeeping. For a
hardware register it is observable: the access sees a master clock that
already includes the fetches and internal cycles of every *later* instruction
in the block. On hardware the 65816 performs the register access after its own
fetches and before anything that follows it.

On the original USA ROM this decides the post-result VBlank wait
``80:FAC9..FAD9`` (RF-017). The block ``80:FAD6 LDA $4212 / BPL $FAD2``
charges the ``BPL`` fetches (16 clocks at SlowROM) before the ``$4212`` read.
In the Zoom Zoo result field the pinned runtime's read lands 6 clocks after
V=225 instead of 10 clocks before it, sees VBlank already set, leaves the poll
loop a whole iteration and NMI early and runs the next compute ~556 clocks
ahead. That puts it at the next wait before V=225 where Snes9x and bsnes arrive
after it, so the ``$C6`` cursor wait runs one field early from result +2.

This stages a narrow emitter correction into a DISPOSABLE pinned Baldosa
checkout. Only blocks that contain a statically addressed register access
(``$2100-$21FF`` or ``$4000-$43FF``) change: their static master clocks are
added before each instruction instead of once at block entry. The total per
block, the 65816 cycle counter, dynamic charges, deadline checks and every
other block are unchanged; a block whose per-instruction split would not
reproduce the existing total keeps the lumped charge. Regenerate ``src/gen``
afterwards with ``tools/regen.sh --cfg-roots`` (the pinned committed output is
reproduced byte-for-byte by that command without this patch). Idempotent;
refuses any other recompiler revision.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

MARK = "UR_BALDOSA_IO_ACCESS_CLOCK_ORDER"
RELATIVE = Path("snesrecomp/recompiler/v2/emit_function.py")

HELPER_ANCHOR = '''def _block_speed(bank: int, pc: int):
    """Code-region cycle weighting, using live PBR for mirrored bodies."""
'''

HELPER = '''# ''' + MARK + ''': a block's static clocks are charged in instruction
# order when it touches a hardware register, so the access sees only the bus
# cycles that precede it (hardware order) rather than the whole block's.
_INSN_MARK_RE = re.compile(r"/\\*@@UR_INSN (\\d+)@@\\*/")
_IO_ADDR_RE = re.compile(
    r"\\bcpu_(?:read|write)(?:8|16)_paced\\(cpu, [^,]+, \\(uint16\\)\\(0x([0-9a-fA-F]+)")


def _is_io_register(addr: int) -> bool:
    return 0x2100 <= addr <= 0x21FF or 0x4000 <= addr <= 0x43FF


def _io_ordered_charges(pairs, lines, speed_expr, speed_const):
    """Per-instruction master-clock adds for a paced block that touches I/O.

    Returns {instruction index: C statement} or None when the block has no
    statically addressed register access or the split cannot reproduce the
    lumped total (the caller then keeps the single block-entry charge)."""
    segs = {}
    cur = None
    io = False
    for ln in lines:
        mk = _INSN_MARK_RE.fullmatch(ln.strip())
        if mk:
            cur = int(mk.group(1))
            segs.setdefault(cur, [])
            continue
        if cur is None:
            if _PACED_RE.search(ln):
                return None
            continue
        segs[cur].append(ln)
        if any(_is_io_register(int(m.group(1), 16)) for m in _IO_ADDR_RE.finditer(ln)):
            io = True
    if not io or sorted(segs) != list(range(len(pairs))):
        return None
    out = {}
    for k, p in enumerate(pairs):
        insn = p[0]
        op = getattr(insn, 'opcode', None)
        if op is None:
            return None
        cycles, _dyn = block_static_cycles(
            [(op, getattr(insn, 'm_flag', 1), getattr(insn, 'x_flag', 1))])
        data = sum(1 if m.group(1) == "8" else 2
                   for ln in segs[k] for m in _PACED_RE.finditer(ln))
        fetch = int(insn.length)
        internal = cycles - fetch - data
        if internal < 0:
            return None
        if speed_const is not None:
            clocks = fetch * speed_const + internal * 6
            stmt = f"cpu->master_cycles += {clocks};" if clocks else ""
        else:
            stmt = f"cpu->master_cycles += {fetch} * {speed_expr} + {internal * 6};"
        if stmt:
            out[k] = stmt + "  /* in-order: register access sees prior bus cycles */"
    return out


'''

LOOP_ANCHOR = '''        for ii, (di_insn, ir_ops) in enumerate(pairs):
            # NLR: inject _pending_skip setter + diagnostics RIGHT BEFORE
'''

LOOP = '''        for ii, (di_insn, ir_ops) in enumerate(pairs):
            lines.append(f"/*@@UR_INSN {ii}@@*/")  # ''' + MARK + '''
            # NLR: inject _pending_skip setter + diagnostics RIGHT BEFORE
'''

CHARGE_ANCHOR = '''        if _cyc_const:
            src.append(f'    cpu->cycles += {_cyc_const};')
            _spd_expr, _spd_const = _block_speed(bank, key.pc)
            if _widths.PACED_BUS:
                _fetch = sum(int(p[0].length) for p in block_per_insn_ir.get(key, []))
                src.append('    cpu->master_cycles += ' + _paced_block_master(
                    _cyc_const, _fetch, _data_bytes, _spd_expr, _spd_const) + ';')
            elif _spd_const is not None:
                src.append(f'    cpu->master_cycles += {_cyc_const * _spd_const};')
            else:
                src.append(f'    cpu->master_cycles += {_cyc_const} * {_spd_expr};')
        for ln in block_lines[key]:
'''

CHARGE = '''        _io_charges = None  # ''' + MARK + '''
        if _cyc_const:
            src.append(f'    cpu->cycles += {_cyc_const};')
            _spd_expr, _spd_const = _block_speed(bank, key.pc)
            if _widths.PACED_BUS:
                _fetch = sum(int(p[0].length) for p in block_per_insn_ir.get(key, []))
                _io_charges = _io_ordered_charges(
                    block_per_insn_ir.get(key, []), block_lines[key],
                    _spd_expr, _spd_const)
                if _io_charges is None:
                    src.append('    cpu->master_cycles += ' + _paced_block_master(
                        _cyc_const, _fetch, _data_bytes, _spd_expr, _spd_const) + ';')
            elif _spd_const is not None:
                src.append(f'    cpu->master_cycles += {_cyc_const * _spd_const};')
            else:
                src.append(f'    cpu->master_cycles += {_cyc_const} * {_spd_expr};')
        for ln in block_lines[key]:
            _mk = _INSN_MARK_RE.fullmatch(ln.strip())
            if _mk:
                if _io_charges is not None and int(_mk.group(1)) in _io_charges:
                    src.append(f"    {_io_charges[int(_mk.group(1))]}")
                continue
'''

EDITS = ((HELPER_ANCHOR, HELPER + HELPER_ANCHOR),
         (LOOP_ANCHOR, LOOP),
         (CHARGE_ANCHOR, CHARGE))


def patch(source: str) -> str:
    if MARK in source:
        if source.count(MARK) != 3 or any(new not in source for _, new in EDITS):
            raise ValueError("I/O clock-order marker present but correction altered")
        return source
    for old, _ in EDITS:
        if source.count(old) != 1:
            raise ValueError("pinned Baldosa paced block charge not recognized; "
                             "do not splice against an unknown recompiler revision")
    for old, new in EDITS:
        source = source.replace(old, new, 1)
    return source


_CHARGE_LINE = re.compile(r"^\s*cpu->master_cycles \+= (.+?);(?:\s*/\*.*\*/)?\s*$")
_BLOCK_LINE = re.compile(r"cpu_trace_block\(cpu, (0x[0-9A-F]+)\);")
_TERM = re.compile(r"^(\d+) \* (.+) \+ (\d+)$")


def _block_totals(text: str) -> list[tuple[str, dict[str, int]]]:
    """Static master-clock statements per generated block, as {speed: coeff}.

    Only whole-line `cpu->master_cycles += ...;` statements count; dynamic
    charges sit inside `if` bodies on the same line and are left alone."""
    blocks: list[tuple[str, dict[str, int]]] = []
    for line in text.split("\n"):
        m = _BLOCK_LINE.search(line)
        if m:
            blocks.append((m.group(1), {}))
            continue
        if line.startswith("RecompReturn "):
            blocks.append(("<function>", {}))
            continue
        c = _CHARGE_LINE.match(line)
        if not c or not blocks:
            continue
        expr, acc = c.group(1), blocks[-1][1]
        t = _TERM.match(expr)
        if t:
            acc[t.group(2)] = acc.get(t.group(2), 0) + int(t.group(1))
            acc["1"] = acc.get("1", 0) + int(t.group(3))
        elif expr.isdigit():
            acc["1"] = acc.get("1", 0) + int(expr)
        else:
            raise ValueError(f"unrecognized static charge: {expr}")
    return blocks


def verify_generated(pinned: str, corrected: str) -> int:
    """Return the number of reordered blocks; raise unless the corrected file
    differs from the pinned one only in static charge lines with equal block
    totals."""
    strip = lambda text: [ln for ln in text.split("\n") if not _CHARGE_LINE.match(ln)]
    if strip(pinned) != strip(corrected):
        raise ValueError("generated code differs beyond static clock charges")
    a, b = _block_totals(pinned), _block_totals(corrected)
    if [k for k, _ in a] != [k for k, _ in b]:
        raise ValueError("generated block structure changed")
    changed = 0
    for (pc, ta), (_, tb) in zip(a, b):
        if {k: v for k, v in ta.items() if v} != {k: v for k, v in tb.items() if v}:
            raise ValueError(f"block {pc} static clock total changed")
    for line in corrected.split("\n"):
        if "in-order: register access" in line and _CHARGE_LINE.match(line):
            changed += 1
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", required=True, type=Path,
                    help="disposable gamesbyian/uniracers-recomp checkout")
    ap.add_argument("--verify-gen", action="store_true",
                    help="after regen: check every src/gen bank file against the "
                         "committed one (git HEAD) for reordered charges only")
    args = ap.parse_args()
    if args.verify_gen:
        import subprocess
        game = args.game.resolve()
        files = sorted((game / "src/gen").glob("bank*_v2.c"))
        if not files:
            raise SystemExit("no generated bank files to verify")
        total = 0
        for f in files:
            rel = f.relative_to(game).as_posix()
            pinned = subprocess.run(["git", "-C", str(game), "show", f"HEAD:{rel}"],
                                    check=True, capture_output=True, text=True).stdout
            total += verify_generated(pinned, f.read_text(encoding="utf-8"))
        if total == 0:
            raise SystemExit("no in-order charges found: was src/gen regenerated?")
        print(f"verified {len(files)} generated files: {total} in-order charge "
              "statements, every block total unchanged")
        return 0
    path = args.game.resolve() / RELATIVE
    before = path.read_text(encoding="utf-8")
    after = patch(before)
    if after == before:
        print(f"I/O clock-order correction already staged: {path}")
    else:
        path.write_text(after, encoding="utf-8")
        print(f"staged I/O clock-order correction: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
