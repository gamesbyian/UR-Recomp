#!/usr/bin/env python3
"""RF076: qualify emitted AOT sites and opt-in interpreter fetch instrumentation.

After authentic Baldosa regeneration, require the three sound sites to have
actual emitted AOT calls, and the five NMI branch/wait candidates to have
source-staged interpreter fetch hooks. Some NMI sites are absent from AOT;
their real execution is UNKNOWN until a decoded guest opcode marker is seen.
This check must never substitute a possible interpreter path for execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

GENERATED = Path('src/gen')
INTERP = Path('snesrecomp/runner/src/snes/interp_bridge.c')
RECORDER = Path('snesrecomp/runner/src/beam_frame_driver.c')
BANK_PART = re.compile(r'bank[0-9a-fA-F]{2}_part[0-9]+_v2\.c\Z')
CALL = re.compile(
    r'(?m)^[ \t]*ur_rf047_mark_executed_pc[ \t]*\([ \t]*'
    r'0x([0-9A-Fa-f]{6})u[ \t]*,[ \t]*1u[ \t]*\)[ \t]*;[ \t]*$')
COMMENTS = re.compile(r'/\*.*?\*/|//[^\n]*', re.DOTALL)
SOUND_AOT = {0x8282F0, 0x8282F2, 0x8282F6}
NMI_CANDIDATES = {0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5}
ALL_TARGETS = SOUND_AOT | NMI_CANDIDATES
INTERP_ANCHOR = ('const uint8_t  op = bridge_bus_read(cpu, pc_before);\n'
                 '        ur_rf047_mark_executed_pc(pc_before, 0u);')


def _source(root: Path, path: Path) -> tuple[str, str]:
    file = root / path
    if not file.is_file() or file.is_symlink():
        raise ValueError(f'missing pinned source-stage file: {path}')
    raw = file.read_bytes()
    return raw.decode('utf-8'), hashlib.sha256(raw).hexdigest()


def inspect(root: Path) -> dict:
    root = root.resolve()
    generated = root / GENERATED
    if not generated.is_dir():
        raise ValueError(f'generated source missing: {GENERATED}; run exact Baldosa regen first')
    bridge, bridge_sha = _source(root, INTERP)
    recorder, recorder_sha = _source(root, RECORDER)
    if bridge.count(INTERP_ANCHOR) != 1:
        raise ValueError('actual interpreter opcode fetch hook missing or relocated')
    if recorder.count('void ur_rf047_mark_executed_pc(uint32_t pc, unsigned tier) {') != 1 or \
       'UR_QA01_RF047_EXEC_PC' not in recorder or 'stage=opcode' not in recorder:
        raise ValueError('RF047 native opcode recorder not source-staged')
    # The source recorder must keep every researched target in its real filter.
    for pc in ALL_TARGETS:
        if recorder.count(f'pc != 0x{pc:06X}u') != 1:
            raise ValueError(f'RF047 filter cannot observe decoded target {pc:06X}')
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
        lines = COMMENTS.sub('', content)
        pcs = [int(m.group(1), 16) for m in CALL.finditer(lines)]
        if pcs:
            observed.update(pcs)
            witnessed.append({
                'path': (GENERATED / file.name).as_posix(),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'site_counts': {f'{pc:06X}': pcs.count(pc) for pc in sorted(set(pcs))},
            })
    missing_sound = SOUND_AOT - observed
    if missing_sound:
        raise ValueError('missing generated sound AOT opcode-PC targets: ' +
                         ','.join(f'{pc:06X}' for pc in sorted(missing_sound)))
    # Historical genuine 39336562146 found all 5 NMI candidate sites absent
    # from AOT but all 3 SOUND_AOT present. Preserve that negative explicitly:
    # the source-staged interpreter fetch hook may observe them later; only
    # real native replay can decide which tier actually executes those PCs.
    return {
        'schema': 'ur-qa01-rf076-generated-exec-pc-preflight/3',
        'generated_dir': GENERATED.as_posix(),
        'generated_bank_part_count': len(files),
        'marker_bearing_translation_units': witnessed,
        'required_sound_AOT_sites': [f'{pc:06X}' for pc in sorted(SOUND_AOT)],
        'NMI_candidate_sites': [f'{pc:06X}' for pc in sorted(NMI_CANDIDATES)],
        'NMI_candidate_AOT_sites_observed': [f'{pc:06X}' for pc in sorted(NMI_CANDIDATES & observed)],
        'NMI_candidate_AOT_sites_absent': [f'{pc:06X}' for pc in sorted(NMI_CANDIDATES - observed)],
        'actual_interpreter_fetch_hook_source_staged': True,
        'interpreter_source_sha256': bridge_sha,
        'native_event_recorder_source_sha256': recorder_sha,
        'sound_AOT_compiled_calls_present': True,
        'NMI_candidate_fetched_opcode_observed_in_native_guest': False,
        'actual_native_guest_execution_checked': False,
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
