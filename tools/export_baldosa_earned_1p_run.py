#!/usr/bin/env python3
"""Transport a real CI-earned 1P .urrun for independent byte review.

Run only after the existing three-process native Windows journey has passed.
This is a bounded copy/receipt, not a new run creator or QA acceptance oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import os
import shutil
import tempfile

MAX_RUN_BYTES = 64 * 1024 * 1024
MAX_REPORT_BYTES = 32 * 1024
SOURCE_SCOPE = 'actual-native-windows-first-racer-to-earned-one-player-records'


def _regular_bytes(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Missing/redirected source evidence: {path.name}')
    size = path.stat().st_size
    if not (0 < size <= limit):
        raise ValueError(f'Invalid source evidence length: {path.name}')
    with path.open('rb') as source:
        data = source.read(limit + 1)
    if len(data) != size:
        raise ValueError(f'Source evidence changed/oversized: {path.name}')
    return data


def _publish_directory_no_replace(staging: Path, destination: Path) -> None:
    """Publish an evidence directory atomically without replacing an incumbent.

    Linux renameat2(RENAME_NOREPLACE) and Windows MoveFileW refuse an
    existing destination in the filesystem operation itself. Other hosts fail
    closed instead of silently weakening the publication guarantee.
    """
    import ctypes
    import sys

    if sys.platform.startswith('linux'):
        libc = ctypes.CDLL(None, use_errno=True)
        operation = getattr(libc, 'renameat2', None)
        if operation is None:
            raise OSError('Linux renameat2 RENAME_NOREPLACE unavailable')
        operation.argtypes = (ctypes.c_int, ctypes.c_char_p,
                              ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        operation.restype = ctypes.c_int
        result = operation(-100, os.fsencode(staging), -100,
                           os.fsencode(destination), 1)
        if result != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(destination))
    elif os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        operation = kernel.MoveFileW
        operation.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p)
        operation.restype = ctypes.c_int
        if not operation(str(staging), str(destination)):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        raise OSError('No audited atomic no-replace directory publish on this host')


def export(journey: Path, destination: Path) -> dict[str, object]:
    if journey.is_symlink() or not journey.is_dir():
        raise ValueError('Missing/redirected native Windows journey')
    report_bytes = _regular_bytes(journey / 'report.json', MAX_REPORT_BYTES)
    report = json.loads(report_bytes)
    if not isinstance(report, dict) or report.get('scope') != SOURCE_SCOPE or any(
        report.get(key) is not True for key in (
            'first_game_created_first_named_racer',
            'second_game_loaded_named_sram_and_finished_real_source_race',
            'third_game_reopened_exact_earned_run_read_only',
            'active_selector_and_catalog_preserved',
            'anonymous_sram_preserved',
        )
    ) or (type(report.get('release_gate_credit')) is not int or report['release_gate_credit'] != 0) or any(
        report.get(key) is not False for key in (
            'physical_gamepad_verified', 'strict_original_native_event_pass',
        )
    ):
        raise ValueError('Source journey did not report qualified bounded 1P path')
    expected = report.get('one_canonical_run_sha256')
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('Missing canonical source-earned run digest')
    runs_root = journey / 'Brand New Player With Spaces' / 'runs' / 'mike'
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise ValueError('Missing/redirected earned-run namespace')
    candidates = list(runs_root.glob('*.urrun'))
    if len(candidates) != 1:
        raise ValueError('Expected exactly one source-earned .urrun')
    data = _regular_bytes(candidates[0], MAX_RUN_BYTES)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError('Source-earned run differs from original Windows report')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Evidence destination already exists: {destination}')
    if not destination.parent.is_dir():
        raise ValueError('Evidence destination parent does not exist')
    staging = Path(tempfile.mkdtemp(prefix='.pending-earned-1p-',
                                    dir=destination.parent))
    try:
        members = {
            'earned.urrun': data,
            'source-report.json': report_bytes,
        }
        for name, payload in members.items():
            with (staging / name).open('xb') as output:
                output.write(payload)
            if _regular_bytes(staging / name, MAX_RUN_BYTES) != payload:
                raise ValueError('CI evidence copy differs from original bytes')
        manifest = {
            'schema_version': 1,
            'source_run_filename': candidates[0].name,
            'source_scope': SOURCE_SCOPE,
            'members': {name: {'sha256': hashlib.sha256(payload).hexdigest(),
                               'bytes': len(payload)}
                        for name, payload in members.items()},
            'independent_release_acceptance': False,
        }
        with (staging / 'manifest.json').open('x', encoding='utf-8') as output:
            json.dump(manifest, output, indent=2, sort_keys=True)
            output.write('\n')
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f'Evidence destination already exists: {destination}')
        _publish_directory_no_replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journey', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = export(args.journey.absolute(), args.out.absolute())
    print('UR_CI_EARNED_1P_RUN_EXPORTED', manifest['members']['earned.urrun']['sha256'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
