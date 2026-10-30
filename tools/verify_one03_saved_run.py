#!/usr/bin/env python3
"""ONE-03: independently reopen the actual second earned .urrun on disk.

This is a bounded evidence guard, not an original/native parity or release verdict.
The producer's CAPTURED line is not itself a durable-file witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CAPTURE = re.compile(
    r'^UR_RUN_RECORD CAPTURED path=(.*?) course=course:00 '
    r'elapsed_ticks60=([1-9][0-9]*)(?: |$)', re.MULTILINE)
CHECKSUM = re.compile(rb'checksum ([0-9a-f]{16})\n\Z')
MAX_BYTES = 64 * 1024 * 1024


_U64_MAX = (1 << 64) - 1
_TOKEN = re.compile(r'[A-Za-z0-9._:-]{1,160}\Z')
_HEX64 = re.compile(r'[0-9a-fA-F]{64}\Z')
_SCALARS = frozenset({
    'game', 'rom_sha256', 'build_compat', 'course', 'mode',
    'elapsed_ticks60', 'frame_count', 'terminal_digest',
})


def _uint(token: str, *, base: int = 10) -> int:
    """Match the native decoder's bounded unsigned 64-bit field grammar."""
    pattern = r'[0-9]+' if base == 10 else r'[0-9a-fA-F]+'
    if not re.fullmatch(pattern, token):
        raise ValueError('ONE-03 malformed native unsigned field')
    value = int(token, base)
    if value > _U64_MAX:
        raise ValueError('ONE-03 native unsigned field exceeds uint64')
    return value


def _token(token: str) -> bool:
    return _TOKEN.fullmatch(token) is not None


def _parse_native_v1(lines: list[str]) -> dict[str, str]:
    """Require the same field set and split/input constraints as the C++ decoder.

    A checksum authenticates bytes, not their decodability. This parser is
    intentionally stricter about blank lines than the native decoder because
    the source-owned encoder emits none. It does not claim product playback.
    """
    if not lines or lines[0] != 'URRUN 1' or lines[-1] != 'END':
        raise ValueError('ONE-03 invalid run-record envelope')
    fields: dict[str, str] = {}
    splits: list[tuple[str, int]] = []
    inputs: list[tuple[int, int, int, int]] = []
    for line in lines[1:-1]:
        parts = line.split(' ')
        if any(not part for part in parts):
            raise ValueError('ONE-03 malformed native run-record row')
        key = parts[0]
        if key in _SCALARS:
            if len(parts) != 2 or key in fields:
                raise ValueError('ONE-03 malformed or duplicate run-record scalar')
            fields[key] = parts[1]
        elif key == 'split':
            if len(parts) != 3 or not _token(parts[1]):
                raise ValueError('ONE-03 malformed native split')
            splits.append((parts[1], _uint(parts[2])))
        elif key == 'input':
            if len(parts) != 5:
                raise ValueError('ONE-03 malformed native input')
            inputs.append((_uint(parts[1]), _uint(parts[2]),
                           _uint(parts[3], base=16), _uint(parts[4], base=16)))
        else:
            raise ValueError('ONE-03 unknown native run-record field')
    if set(fields) != _SCALARS:
        raise ValueError('ONE-03 missing required native run-record scalar')
    if any(not _token(fields[key]) for key in
           ('game', 'build_compat', 'course', 'mode')):
        raise ValueError('ONE-03 invalid native provenance token')
    if not _HEX64.fullmatch(fields['rom_sha256']):
        raise ValueError('ONE-03 invalid native ROM hash')
    if (fields['terminal_digest'] != '-' and
            not _HEX64.fullmatch(fields['terminal_digest'])):
        raise ValueError('ONE-03 invalid native terminal digest')
    elapsed = _uint(fields['elapsed_ticks60'])
    frame_count = _uint(fields['frame_count'])
    previous_split = 0
    for _, ticks in splits:
        if ticks > elapsed or ticks < previous_split:
            raise ValueError('ONE-03 invalid native split order or bounds')
        previous_split = ticks
    previous_end = 0
    for start, duration, p1, p2 in inputs:
        if (duration == 0 or p1 > 0x0fff or p2 > 0x0fff or
                (p1 == 0 and p2 == 0) or
                start > _U64_MAX - duration or
                start < previous_end or start + duration > frame_count):
            raise ValueError('ONE-03 invalid native input run')
        previous_end = start + duration
    return fields


def verify(log: Path, root: Path, source_movie: bool,
           expected_receipt: Path | None = None) -> tuple[dict, bytes]:
    if not log.is_file() or log.is_symlink():
        raise ValueError('ONE-03 missing or redirected producer log')
    captures = CAPTURE.findall(log.read_text(encoding='utf-8', errors='replace'))
    if len(captures) != 1:
        raise ValueError('ONE-03 requires exactly one second-course capture')
    path_text, logged_ticks = captures[0]
    path = Path(path_text)
    if not path.is_absolute() or path.suffix != '.urrun' or path.parent != root:
        raise ValueError('ONE-03 saved record path escaped expected profile runs root')
    for component in (path, root, *root.parents):
        if component.is_symlink():
            raise ValueError('ONE-03 redirected saved record or ancestor')
    if not path.is_file() or not root.is_dir():
        raise ValueError('ONE-03 CAPTURED log has no actual saved record')
    size = path.stat().st_size
    if size <= 0 or size > MAX_BYTES:
        raise ValueError('ONE-03 missing or oversized saved record')
    raw = path.read_bytes()
    if len(raw) != size:
        raise ValueError('ONE-03 saved record changed while reading')
    match = CHECKSUM.search(raw)
    if not match:
        raise ValueError('ONE-03 missing canonical run-record checksum')
    body = raw[:match.start()]
    value = 14695981039346656037
    for byte in body:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    if f'{value:016x}'.encode('ascii') != match.group(1):
        raise ValueError('ONE-03 run-record checksum mismatch')
    # The native decoder uses std::getline(...), which recognizes LF only.
    # Python str.splitlines() also treats VT/FF/CR/record separators as line
    # boundaries and can falsely accept bytes that native decoding rejects.
    # The source-owned encoder always terminates each row with LF.
    if not body.endswith(b'\n'):
        raise ValueError('ONE-03 unterminated native run-record row')
    try:
        lines = body.decode('ascii').split('\n')[:-1]
    except UnicodeDecodeError as exc:
        raise ValueError('ONE-03 non-ASCII run record') from exc
    if not lines or lines[0] != 'URRUN 1' or lines[-1] != 'END' or lines.count('END') != 1:
        raise ValueError('ONE-03 invalid run-record envelope')
    fields = _parse_native_v1(lines)
    if (fields.get('game') != 'uniracers-usa' or
            fields.get('course') != 'course:00' or
            fields.get('mode') != 'race-1p' or
            not re.fullmatch('[0-9a-f]{64}', fields.get('rom_sha256', '')) or
            not fields.get('build_compat') or
            not fields.get('frame_count', '').isdecimal() or
            fields.get('elapsed_ticks60') != logged_ticks or
            (source_movie and logged_ticks != '1505')):
        raise ValueError('ONE-03 saved record provenance or elapsed time mismatch')
    receipt = {
        'schema': 'ur-one03-saved-run-evidence/1',
        'filename': path.name,
        'sha256': hashlib.sha256(raw).hexdigest(),
        'course': 'course:00',
        'elapsed_ticks60': int(logged_ticks),
        'size': len(raw),
    }
    if expected_receipt is not None:
        if not expected_receipt.is_file() or expected_receipt.is_symlink():
            raise ValueError('ONE-03 missing original saved-record receipt')
        if json.loads(expected_receipt.read_text(encoding='utf-8')) != receipt:
            raise ValueError('ONE-03 saved run record changed or vanished across cold boot')
    return receipt, raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--source-movie', choices=('0', '1'), required=True)
    parser.add_argument('--receipt-out', type=Path)
    parser.add_argument('--evidence-out', type=Path)
    parser.add_argument('--expected-receipt', type=Path)
    args = parser.parse_args()
    receipt, raw = verify(args.log, args.runs_root, args.source_movie == '1',
                          args.expected_receipt)
    if args.receipt_out:
        args.receipt_out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n',
                                    encoding='utf-8')
    if args.evidence_out:
        args.evidence_out.write_bytes(raw)
    print('ONE03_SAVED_RUN_VERIFIED course=course:00 ticks60=' +
          str(receipt['elapsed_ticks60']) + ' sha256=' + receipt['sha256'])


if __name__ == '__main__':
    main()
