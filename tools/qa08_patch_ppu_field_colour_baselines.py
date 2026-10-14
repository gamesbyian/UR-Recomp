#!/usr/bin/env python3
"""Expose authentic field-start colour registers in pinned raster debug JSON.

Debug printer only. No native PPU state, replay, rendering, OAM or guest mutation.
"""
from __future__ import annotations
import argparse
from pathlib import Path

OLD_TO_NEW = (
    ('  uint16_t bg1h, bg1v;\n',
     '  uint16_t bg1h, bg1v, fixed15;\n'),
    ('  memcpy(&bg1v, f->regs + RJ_OFF(vScroll), sizeof(bg1v));\n',
     '  memcpy(&bg1v, f->regs + RJ_OFF(vScroll), sizeof(bg1v));\n'
     '  memcpy(&fixed15, f->regs + RJ_OFF(fixedColor), sizeof(fixed15));\n'),
    ('                  "\\\"tmw\\\":\\\"0x%02X\\\",\\\"cgadsub\\\":\\\"0x%02X\\\","\n',
     '                  "\\\"tmw\\\":\\\"0x%02X\\\",\\\"cgadsub\\\":\\\"0x%02X\\\","\n'
     '                  "\\\"cgwsel\\\":\\\"0x%02X\\\",\\\"fixed15\\\":\\\"0x%04X\\\","\n'),
    ('                  f->regs[RJ_OFF(screenWindowed)], f->regs[RJ_OFF(cgadsub)],\n'
     '                  (unsigned)bg1h, (unsigned)bg1v);\n',
     '                  f->regs[RJ_OFF(screenWindowed)], f->regs[RJ_OFF(cgadsub)],\n'
     '                  f->regs[RJ_OFF(cgwsel)], (unsigned)fixed15,\n'
     '                  (unsigned)bg1h, (unsigned)bg1v);\n'),
)

def patch_source(source: str, header: str) -> str:
    snapshot = header.split('// -- START OF SNAPSHOT, 0x40 bytes', 1)
    if len(snapshot) != 2 or '// -- END OF SNAPSHOT' not in snapshot[1]:
        raise ValueError('pinned 0x40-byte register snapshot declaration missing')
    fields = snapshot[1].split('// -- END OF SNAPSHOT', 1)[0]
    if not ('uint16 fixedColor;' in fields and 'uint8 cgwsel;' in fields
            and fields.index('fixedColor') < fields.index('cgwsel')):
        raise ValueError('pinned CGWSEL/fixedColor snapshot layout changed')
    prefix, sep, rest = source.partition('static int raster_dump_field(')
    if not sep or 'int ppu_rasterDebugDump(' not in rest:
        raise ValueError('pinned raster debug exporter missing')
    scope, end, tail = rest.partition('int ppu_rasterDebugDump(')
    for old, new in OLD_TO_NEW:
        if scope.count(old) != 1 or new in scope:
            raise ValueError('unexpected or already-patched native raster printer')
        scope = scope.replace(old, new, 1)
    return prefix + sep + scope + end + tail

def apply(framework: Path, check_only: bool = False) -> Path:
    c = framework / 'runner/src/snes/ppu.c'
    h = framework / 'runner/src/snes/ppu.h'
    patched = patch_source(c.read_text(encoding='utf-8'),
                           h.read_text(encoding='utf-8'))
    if not check_only:
        c.write_text(patched, encoding='utf-8')
    return c

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--framework', required=True, type=Path)
    p.add_argument('--check-only', action='store_true')
    a = p.parse_args()
    try:
        result = apply(a.framework, a.check_only)
    except (OSError, ValueError) as exc:
        p.exit(2, f'QA08 native PPU baseline patch rejected: {exc}\n')
    print(f'QA08 PPU field baselines exported: {result}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
