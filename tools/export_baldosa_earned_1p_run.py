#!/usr/bin/env python3
"""Transport a real CI-earned 1P .urrun for independent byte review.

Run only after the existing three-process native Windows journey has passed.
This is a bounded copy/receipt, not a new run creator or QA acceptance oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import os
import shutil
import tempfile
import stat
import sys
import unicodedata

MAX_RUN_BYTES = 64 * 1024 * 1024
MAX_REPORT_BYTES = 32 * 1024
SOURCE_SCOPE = 'actual-native-windows-first-racer-to-earned-one-player-records'


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate source report JSON key: {key}')
        result[key] = value
    return result


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('Nonfinite source report JSON number')
    return parsed


def _reject_constant(value):
    raise ValueError(f'Nonfinite source report JSON constant: {value}')


def _regular_bytes(path: Path, limit: int) -> bytes:
    """Read a stable regular-file descriptor, refusing symlinked leaf swaps.

    Hardlinked aliases are also refused to keep source namespace provenance.
    O_NOFOLLOW is enforced on POSIX platforms that expose it. On Windows,
    pre/post lstat plus fstat bind the path to the opened file; ancestor
    reparse-point substitution remains outside this bounded helper's proof.
    """
    try:
        before = path.lstat()
    except FileNotFoundError as exc:
        raise ValueError(f'Missing source evidence: {path.name}') from exc
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
            not (0 < before.st_size <= limit)):
        raise ValueError(f'Missing/redirected/invalid source evidence: {path.name}')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f'Unable to open unredirected source evidence: {path.name}') from exc
    with os.fdopen(fd, 'rb') as source:
        opened = os.fstat(source.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or (
                opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
                before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
            raise ValueError(f'Source evidence changed before open: {path.name}')
        data = source.read(limit + 1)
        closed = os.fstat(source.fileno())
    after = path.lstat()
    identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
    if (len(data) != opened.st_size or identity(before) != identity(closed)
            or identity(before) != identity(after) or not stat.S_ISREG(after.st_mode)
            or closed.st_nlink != 1 or after.st_nlink != 1):
        raise ValueError(f'Source evidence changed during read: {path.name}')
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
    root_name = journey.name
    # Validate unencodable code points before computing the Win32 UTF-16
    # length. POSIX surrogateescaped filenames must get our bounded,
    # actionable refusal, not an uncaught UnicodeEncodeError.
    invalid_codepoints = any(
        ord(ch) < 32 or unicodedata.category(ch) in ('Cf', 'Cs')
        or ch in '<>:"|?*\\/' for ch in root_name
    )
    stem = root_name.split('.', 1)[0].upper().translate(str.maketrans('¹²³', '123'))
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'}
    reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10))
    if (not root_name or root_name.endswith((' ', '.')) or invalid_codepoints or
            unicodedata.normalize('NFC', root_name) != root_name or
            len(root_name.encode('utf-16-le')) // 2 > 255 or
            stem in reserved):
        raise ValueError('Nonportable source journey root name')
    if destination == journey or journey in destination.parents:
        raise ValueError('Evidence destination must be outside source journey')
    if (journey.is_symlink() or not journey.is_dir() or
            journey.resolve(strict=True) != journey.absolute()):
        raise ValueError('Missing/redirected native Windows journey')
    report_bytes = _regular_bytes(journey / 'report.json', MAX_REPORT_BYTES)
    report = json.loads(report_bytes, object_pairs_hook=_unique_pairs,
                        parse_float=_finite_float, parse_constant=_reject_constant)
    if not isinstance(report, dict) or report.get('scope') != SOURCE_SCOPE or any(
        report.get(key) is not True for key in (
            'first_game_created_first_named_racer',
            'second_game_loaded_named_sram_and_finished_real_source_race',
            'third_game_reopened_exact_earned_run_read_only',
            'active_selector_and_catalog_preserved',
            'anonymous_sram_preserved',
        )
    ) or (type(report.get('release_gate_credit')) is not int or
        report['release_gate_credit'] != 0) or any(
        report.get(key) is not False for key in (
            'physical_gamepad_verified', 'strict_original_native_event_pass',
        )
    ):
        raise ValueError('Source journey did not report qualified bounded 1P path')
    expected = report.get('one_canonical_run_sha256')
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('Missing canonical source-earned run digest')
    runs_root = journey / 'Brand New Player With Spaces' / 'runs' / 'mike'
    if (runs_root.is_symlink() or not runs_root.is_dir() or
            runs_root.resolve(strict=True) != runs_root.absolute()):
        raise ValueError('Missing/redirected earned-run namespace')
    candidates = [entry for entry in runs_root.iterdir()
                  if entry.name.split(':', 1)[0].rstrip(' .').casefold().endswith('.urrun')]
    if len(candidates) != 1 or candidates[0].suffix != '.urrun':
        raise ValueError('Expected exactly one source-earned .urrun')
    source_name = candidates[0].name
    if (unicodedata.normalize('NFC', source_name) != source_name or
            # Reject surrogateescaped POSIX filenames before UTF-8 encoding.
            # The source journey root already follows this bounded policy.
            any(ord(ch) < 32 or unicodedata.category(ch) in ('Cf', 'Cs')
                for ch in source_name) or
            len(source_name.encode('utf-8')) > 255 or
            source_name[-1] in (' ', '.') or
            any(ch in '<>:"|?*\\' for ch in source_name)):
        raise ValueError('Nonportable source-earned run filename')
    # A Linux-produced fixture may carry a filename that cannot be reopened
    # through Win32. Refuse reserved DOS device basenames before transport.
    device_stem = source_name.split('.', 1)[0].upper().translate(
        str.maketrans('¹²³', '123'))
    if (device_stem in {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} or
            device_stem in {f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10)}):
        raise ValueError('Nonportable source-earned run filename')
    data = _regular_bytes(candidates[0], MAX_RUN_BYTES)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError('Source-earned run differs from original Windows report')
    # Build outside the published artifact name. If verification or a write
    # fails, upload-artifact must never mistake partial bytes for evidence.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Evidence destination already exists: {destination}')
    if (not destination.parent.is_dir() or
            destination.parent.resolve(strict=True) != destination.parent.absolute()):
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
        # Same-parent rename publishes the complete evidence set at once.
        # Windows refuses a directory collision; on POSIX reject it first.
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
