#!/usr/bin/env python3
"""Fail-closed RF076 check of the actual Baldosa published AOT C output.

Run AFTER baldosa/tools/regen.sh --cfg-roots --rom ... and BEFORE the
native C build. This proves only regenerated source contains the hooks;
actual decoded guest fetch requires a live RF047 stream and exact ELF.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

GENERATED = Path('src/gen')
# The pinned project publishes bank parts here, not runner/src/gen.
BANK_PART = re.compile(r'bank[0-9a-fA-F]{2}_part[0-9]+_v2\.c\Z')
CALL = re.compile(
    r'(?m)^[ \t]*ur_rf047_mark_executed_pc[ \t]*\([ \t]*'
    r'0x([0-9A-Fa-f]{6})u[ \t]*,[ \t]*1u[ \t]*\)[ \t]*;[ \t]*$')
COMMENTS = re.compile(r'/\*.*?\*/|//[^\n]*', re.DOTALL)
REQUIRED = {0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5,
            0x8282F0, 0x8282F2, 0x8282F6}


def inspect(root: Path) -> dict:
    root = root.resolve()
    generated = root / GENERATED
    if not generated.is_dir():
        raise ValueError(f'generated source missing: {GENERATED}; run exact Baldosa regen first')
    files = sorted(p for p in generated.iterdir()
                   if p.is_file() and BANK_PART.fullmatch(p.name) and not p.is_symlink())
    if not files:
        raise ValueError('no published AOT bank*_part*_v2.c files in src/gen')
    observed = set()
    witnessed = []
    for file in files:
        raw = file.read_bytes()
        try:
            content = raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError(f'generated C not UTF-8: {file.name}') from exc
        # Decomp descriptions are emitted as comments; a mentioned call is not a call.
        executable_lines = COMMENTS.sub('', content)
        pcs = [int(m.group(1), 16) for m in CALL.finditer(executable_lines)]
        if pcs:
            observed.update(pcs)
            witnessed.append({
                'path': (GENERATED / file.name).as_posix(),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'site_counts': {f'{pc:06X}': pcs.count(pc) for pc in sorted(set(pcs))},
            })
    missing = REQUIRED - observed
    if missing:
        raise ValueError('missing generated opcode-PC targets: ' +
                         ','.join(f'{pc:06X}' for pc in sorted(missing)))
    return {
        'schema': 'ur-qa01-rf076-generated-exec-pc-preflight/2',
        'generated_dir': GENERATED.as_posix(),
        'generated_bank_part_count': len(files),
        'marker_bearing_translation_units': witnessed,
        'required_decoded_sites': [f'{pc:06X}' for pc in sorted(REQUIRED)],
        'static_generated_calls_present': True,
        'actual_guest_opcode_executed': False,
        'original_native_same_semantic_phase': False,
        'accepted_USA_events': 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = inspect(args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
