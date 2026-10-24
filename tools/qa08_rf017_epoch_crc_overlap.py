#!/usr/bin/env python3
"""Bounded RF017 vs held-QA08 WRAM CRC overlap negative, not a parity verdict.

Only authentic, SHA-pinned Windows archives are accepted. This reads the old
host-relative WRAM trace and the newer full guest-framedump transcript. It
cannot identify the first divergence or establish equal semantic stages.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

OLD_ZIP_SHA = 'c23a86336149084ca636ebd35a0d070f8e62cdb9b91a7f9178a90462ef3bd764'
NEW_ZIP_SHA = 'b4dd0417d1e9f158ac6abf798251a895ac256488f2218805231b2b21f4e0430c'
OLD_GUEST_SHA = 'b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568'
NEW_GUEST_SHA = '61826faa8a7c09c91a6013b5aabc5c3f1bd794d960396c76ce62fa34f7968bf8'
EXPECTED_OLD_WINDOW = range(1948, 1971)
TRACE_RE = re.compile(r'^UR_BALDOSA_HOST_FRAME_CRC host=(\d+) guest=(\d+) hash=([0-9a-fA-F]{8})$', re.M)
CRC_RE = re.compile(r'^0x[0-9a-f]{8}$')


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_pinned_zip(path: Path, expected: str, members: set[str]) -> dict[str, bytes]:
    blob = path.read_bytes()
    if sha(blob) != expected:
        raise ValueError('authentic artifact ZIP SHA mismatch')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or not members <= set(names):
            raise ValueError('missing or duplicate evidence members')
        if any(n.startswith('/') or '..' in Path(n).parts or '\\' in n for n in names):
            raise ValueError('unsafe evidence ZIP member')
        return {name: z.read(name) for name in members}


def parse_old(log: str) -> dict[int, str]:
    matches = TRACE_RE.findall(log.replace("\r\n", "\n"))
    frames = {}
    for host, guest, digest in matches:
        host, guest = int(host), int(guest)
        if host != guest or host in frames:
            raise ValueError('host/guest labels differ or duplicate old frame')
        frames[host] = digest.lower()
    if set(frames) != set(EXPECTED_OLD_WINDOW):
        raise ValueError('historical host-relative trace not the exact 23-frame window')
    return frames


def parse_new(blob: bytes) -> list[str]:
    rows = blob.decode('ascii').splitlines()
    if len(rows) != 5484 or any(not CRC_RE.fullmatch(r) for r in rows):
        raise ValueError('current-epoch CRC transcript format/count changed')
    return [r[2:] for r in rows]


def census(old: dict[int, str], new: list[str]) -> dict:
    if len(old) != 23 or len(new) != 5484:
        raise ValueError('incomplete census')
    new_set = set(new)
    overlap = {str(f): [i for i, value in enumerate(new) if value == crc]
               for f, crc in sorted(old.items()) if crc in new_set}
    direct = sum(new[f] == crc for f, crc in old.items())
    preceding = sum(new[f - 1] == crc for f, crc in old.items())
    following = sum(new[f + 1] == crc for f, crc in old.items())
    return {'historical_host_frames': len(old), 'current_guest_frames': len(new),
            'anywhere_matching_old_values': len(overlap), 'anywhere_match_indices': overlap,
            'same_numeric_guest_label_matches': direct,
            'one_earlier_index_matches': preceding, 'one_later_index_matches': following,
            'scope': '23 host WRAM hashes vs 5484 guest framedump WRAM CRCs; different source epochs',
            'same_semantic_stage_proven': False, 'first_divergence_located': False,
            'ppu_original_native_parity_proven': False, 'release_credit': False}


def audit(old_path: Path, new_path: Path) -> dict:
    old = read_pinned_zip(old_path, OLD_ZIP_SHA, {'baseline/log.txt', 'qa08-windows-2p-fullroute.json'})
    new = read_pinned_zip(new_path, NEW_ZIP_SHA,
                          {'off-guest-crc.txt', 'on-guest-crc.txt', 'status.json'})
    old_meta = json.loads(old['qa08-windows-2p-fullroute.json'])
    new_meta = json.loads(new['status.json'])
    if old_meta['actual_native_guest_CRC_sha256'] != OLD_GUEST_SHA or old_meta['actual_native_simulations'] != 5484:
        raise ValueError('historical RF017 guest identity not qualified')
    if new_meta.get('same_epoch_ON_OFF_guest_CRC_equal') is not True:
        raise ValueError('new ON/OFF equality not qualified')
    if sha(new['off-guest-crc.txt']) != NEW_GUEST_SHA or new['off-guest-crc.txt'] != new['on-guest-crc.txt']:
        raise ValueError('current source CRC SHA or ON/OFF bytes mismatch')
    result = census(parse_old(old['baseline/log.txt'].decode('utf-8')),
                    parse_new(new['off-guest-crc.txt']))
    result.update({'schema': 'QA08-RF017-vs-current-epoch-overlap-negative/1',
                   'historical_artifact_id': 12091090244,
                   'current_artifact_id': 12233560894,
                   'historical_artifact_sha256': OLD_ZIP_SHA,
                   'current_artifact_sha256': NEW_ZIP_SHA,
                   'historical_full_guest_digest': OLD_GUEST_SHA,
                   'current_full_guest_digest': NEW_GUEST_SHA,
                   'historical_source_window': [1948, 1970],
                   'historical_host_trace_source': 'baseline/log.txt',
                   'new_transcript_source': 'off-guest-crc.txt'})
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--historical-zip', type=Path, required=True)
    p.add_argument('--current-zip', type=Path, required=True)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = audit(a.historical_zip, a.current_zip)
    payload = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if a.out:
        if a.out.exists():
            p.error('refusing to overwrite an existing evidence receipt')
        a.out.write_text(payload, encoding='utf-8')
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
