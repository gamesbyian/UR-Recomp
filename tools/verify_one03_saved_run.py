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
    try:
        lines = body.decode('ascii').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('ONE-03 non-ASCII run record') from exc
    if not lines or lines[0] != 'URRUN 1' or lines[-1] != 'END' or lines.count('END') != 1:
        raise ValueError('ONE-03 invalid run-record envelope')
    fields: dict[str, str] = {}
    for line in lines[1:-1]:
        if line.startswith(('split ', 'input ')):
            continue
        parts = line.split(' ')
        if len(parts) != 2 or parts[0] in fields:
            raise ValueError('ONE-03 malformed or duplicate run-record scalar')
        fields[parts[0]] = parts[1]
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
