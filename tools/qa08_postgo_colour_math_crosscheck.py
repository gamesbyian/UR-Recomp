#!/usr/bin/env python3
"""QA-08: verify existing genuine 2P PPU/OBJ counterfactual RGB arithmetic.

Reads ONE immutable original native Baldosa AOT artifact zip. Never infers
PPU main/sub layer ownership from a source RGBA raster or register state.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

GUEST_FRAME = 2208
STOCK_SHA = 'f9ca59c19dc3e8d51c7ca1dbce25d5dc14e56ba36011128abbadee8cec0e7b4a'
ROOT = 'baldosa-evidence/'
STOCK = 'baldosa-ws342-captures/ur-baldosa-ws342-002208.pam'
SOURCE = 'baldosa-ws342-obj-slots/ur-baldosa-ws342-obj-slot{slot}-frame002208.pam'
REMOVED = 'baldosa-ws342-counterfactual-slot{slot}-frame2208/ur-baldosa-ws342-002208.pam'
H = b'P7\nWIDTH 342\nHEIGHT 224\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n'

def expand5(c: int) -> int:
    return (c << 3) | (c >> 2)

def packed5(rgb: list[int]) -> list[int]:
    if len(rgb) != 3:
        raise ValueError('RGB triplet required')
    result = []
    for b in rgb:
        if type(b) is not int or b not in {expand5(i) for i in range(32)}:
            raise ValueError('not SNES 5-bit-expanded RGB')
        result.append(next(i for i in range(32) if expand5(i) == b))
    return result

def read_rgba(z: zipfile.ZipFile, name: str, expected: str) -> bytes:
    data = z.read(name)
    if not data.startswith(H) or len(data) != len(H) + 342 * 224 * 4:
        raise ValueError('wrong native Original P7 size/header: ' + name)
    raw = data[len(H):]
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('original native image hash differs: ' + name)
    return raw

def pixel(raw: bytes, x: int, y: int) -> list[int]:
    if type(x) is not int or type(y) is not int or not (0 <= x < 342 and 0 <= y < 224):
        raise ValueError('native image pixel outside source frame')
    i = 4 * (342 * y + x)
    return list(raw[i:i + 4])

def check(z: zipfile.ZipFile) -> dict:
    journal = json.loads(z.read(ROOT + 'ws342_2p_original_colour_journal_2208.json'))
    causal = json.loads(z.read(ROOT + 'ws342_postgo_front_text_causal_2208.json'))
    if (journal['guest_frame'] != GUEST_FRAME or
            journal['full_original_342x224_RGBA_SHA256'] != STOCK_SHA or
            journal['full_native_guest_CRC_entries_equal'] != 2473 or
            causal['guest_frame'] != GUEST_FRAME or
            causal['native_each_front_removed_in_independent_full_guest_process'] is not True):
        raise ValueError('native post-GO identity/CRC acceptance missing')
    fixed = [0, 19, 0]
    for name in ('completed', 'recording'):
        f = journal['field_register_journals'][name]['beam_order_colour_knowledge']
        spans = f['visible_line_tag_intervals_after_same_line_final_write']
        if (not f['baseline_cgwsel_known'] or not f['baseline_fixed_colour_known'] or
                spans != [{'first_visible_line_tag': 0, 'last_visible_line_tag': 223,
                           'cgadsub': '0x04', 'cgwsel': '0x02',
                           'fixed_R5_G5_B5': fixed, 'fixed_rgb15': '0x0260'}]):
            raise ValueError('native full-visible-field math-state evidence disagrees')
    stock = read_rgba(z, STOCK, STOCK_SHA)
    report = {}
    paired = {}
    for slot, bottom in ((98, False), (96, True)):
        name = str(slot)
        evidence = causal['per_original_front_slot'][name]
        samples = evidence['bounded_original_red_text_over_front_samples']
        if (evidence['native_guest_frame'] != GUEST_FRAME or
                evidence['all_four_guest_crc_streams_equal_at_exact_frame_count'] != 2473 or
                evidence['authentic_native_arm_marker_one'] is not True or
                len(samples) != 13 or
                evidence['counts']['native_final_changed_at_red_text_source_positions'] != 13 or
                evidence['unmodified_original_sha256'] != STOCK_SHA):
            raise ValueError('front-source counterfactual evidence incomplete')
        source = read_rgba(z, SOURCE.format(slot=slot), evidence['front_source_sha256'])
        absent = read_rgba(z, REMOVED.format(slot=slot), evidence['native_front_removed_original_sha256'])
        positions = set()
        source_hist, after_hist = Counter(), Counter()
        for item in samples:
            x, y = item['xy']
            if (x, y) in positions or item['native_final_changed'] is not True:
                raise ValueError('duplicate or unchanged original source+text pixel')
            positions.add((x, y))
            normal = pixel(stock, x, y)
            src = pixel(source, x, y)
            without = pixel(absent, x, y)
            if (src[3] == 0 or
                    normal[:3] != item['stock_original_rgb'] or
                    src[:3] != item['source_rgb'] or
                    without[:3] != item['native_original_after_front_removal_rgb']):
                raise ValueError('native source/composite/removal pixel witness disagreement')
            snes_src, snes_stock, snes_removed = map(packed5, (src[:3], normal[:3], without[:3]))
            if snes_stock != [snes_src[0] + 13, snes_src[1], snes_src[2]]:
                raise ValueError('not 13 red5 only at original racer+text intersection')
            source_hist[tuple(snes_src)] += 1
            after_hist[tuple(snes_removed)] += 1
            paired[(slot, x, y)] = (src[:3], normal[:3])
        expected_y = (159, 164) if bottom else (47, 52)
        if min(y for _, y in positions) != expected_y[0] or max(y for _, y in positions) != expected_y[1]:
            raise ValueError('unexpected original source row bounds')
        report[name] = {
            'source_sha256': evidence['front_source_sha256'],
            'removed_sha256': evidence['native_front_removed_original_sha256'],
            'red5_delta_only': 13,
            'exact_native_original_pixel_witnesses': len(positions),
            'source_rgb5_histogram': [{'RGB5': list(k), 'pixels': n} for k,n in sorted(source_hist.items())],
            'removed_rgb5_histogram': [{'RGB5': list(k), 'pixels': n} for k,n in sorted(after_hist.items())],
        }
    for (slot, x, y), values in paired.items():
        if slot == 98 and paired.get((96, x, y + 112)) != values:
            raise ValueError('paired upper/lower text-intersection pixels differ')
    return {
        'schema': 'qa08-2p-postgo-registered-bg3-colour-constraints/1',
        'status': 'exact-native-ppu-source-removal-colour-constraints-observed',
        'source_AOT_run': 38492408817,
        'source_artifact_id': 11863045863,
        'guest_frame': GUEST_FRAME,
        'original_RGBA_sha256': STOCK_SHA,
        'native_guest_CRC_records': 2473,
        'source_red5_witnesses_each_viewport': 13,
        'paired_text_witness_displacement': [0, 112],
        'field_CGADSUB': '0x04', 'field_CGWSEL': '0x02',
        'field_fixed_RGB5': fixed,
        'BG3_colour_math_enabled_in_pinned_native_renderer': True,
        'OBJ_colour_math_disabled_in_pinned_native_renderer': True,
        'candidate_BG3_main_plus_OBJ_subscreen_consistent': True,
        'BG3_main_and_OBJ_subscreen_per_pixel_observed': False,
        'source_physical_SNES_PPU_winner_observed': False,
        'remastered_racer_approved': False,
        'slot_evidence': report,
    }

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    with zipfile.ZipFile(a.artifact) as z:
        result = check(z)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf8')
    print('QA08_NATIVE_POSTGO_COLOUR_CONSTRAINTS_ACCEPTED 26=26 sourceSHA=exact CRC=2473 owner=unknown')

if __name__ == '__main__':
    main()
