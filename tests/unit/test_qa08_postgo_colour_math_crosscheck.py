"""QA-08: synthetic pixel-fingerprint, counterfactual and fail-closed tests."""
from __future__ import annotations
import hashlib
import io
import json
import unittest
import zipfile
from unittest.mock import patch
from tools import qa08_postgo_colour_math_crosscheck as qa


def fixture(mutate=False):
    def raw(): return bytearray(342 * 224 * 4)
    def write(arr,x,y,rgb,alpha=0):
        i = 4*(342*y+x)
        arr[i:i+4] = bytes([*rgb,alpha])
    def hashbytes(arr): return hashlib.sha256(arr).hexdigest()
    coords = [(132+i%5,47+i%6) for i in range(13)]
    stock = raw()
    for x,y in coords:
        for yy in (y,y+112):
            write(stock,x,yy,[qa.expand5(22),qa.expand5(9),qa.expand5(9)])
    causal = {'guest_frame':2208,
              'native_each_front_removed_in_independent_full_guest_process':True,
              'per_original_front_slot':{}}
    files = {qa.STOCK:stock}
    for slot in (98,96):
        bottom = slot == 96
        source,removed = raw(),raw()
        samples=[]
        for x,y in coords:
            y+=112 if bottom else 0
            rgb = [qa.expand5(9)]*3
            absent = [qa.expand5(t) for t in ([13,19,0] if bottom else [28,0,0])]
            write(source,x,y,rgb,255)
            write(removed,x,y,absent)
            samples.append({'xy':[x,y], 'native_final_changed':True,
              'source_rgb':rgb,
              'stock_original_rgb':[qa.expand5(22),qa.expand5(9),qa.expand5(9)],
              'native_original_after_front_removal_rgb':absent})
        if mutate and slot == 98:
            write(source,132,47,[qa.expand5(11)]*3,255)
        files[qa.SOURCE.format(slot=slot)] = source
        files[qa.REMOVED.format(slot=slot)] = removed
        causal['per_original_front_slot'][str(slot)] = {
            'native_guest_frame':2208,
            'all_four_guest_crc_streams_equal_at_exact_frame_count':2473,
            'authentic_native_arm_marker_one':True,
            'counts':{'native_final_changed_at_red_text_source_positions':13},
            'front_source_sha256':hashbytes(source),
            'native_front_removed_original_sha256':hashbytes(removed),
            'unmodified_original_sha256':hashbytes(stock),
            'bounded_original_red_text_over_front_samples':samples}
    journal = {'guest_frame':2208,
               'full_original_342x224_RGBA_SHA256':hashbytes(stock),
               'full_native_guest_CRC_entries_equal':2473,
               'field_register_journals':{}}
    for kind in ('completed','recording'):
        journal['field_register_journals'][kind] = {'beam_order_colour_knowledge':{
            'baseline_cgwsel_known':True,
            'baseline_fixed_colour_known':True,
            'visible_line_tag_intervals_after_same_line_final_write':[{
                'first_visible_line_tag':0,'last_visible_line_tag':223,
                'cgadsub':'0x04','cgwsel':'0x02',
                'fixed_R5_G5_B5':[0,19,0],'fixed_rgb15':'0x0260'}]}}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,image in files.items():
            z.writestr(name,qa.H+bytes(image))
        z.writestr(qa.ROOT+'ws342_2p_original_colour_journal_2208.json',
                   json.dumps(journal))
        z.writestr(qa.ROOT+'ws342_postgo_front_text_causal_2208.json',
                   json.dumps(causal))
    buf.seek(0)
    return buf,hashbytes(stock)


class NativePixelCrosscheckTests(unittest.TestCase):
    def test_two_viewport_exact_synthetic_sanity(self):
        archive,stock_sha = fixture()
        with patch.object(qa,'STOCK_SHA',stock_sha),zipfile.ZipFile(archive) as z:
            r = qa.check(z)
        self.assertEqual(r['slot_evidence']['98']['removed_rgb5_histogram'],
                         [{'RGB5':[28,0,0],'pixels':13}])
        self.assertEqual(r['slot_evidence']['96']['removed_rgb5_histogram'],
                         [{'RGB5':[13,19,0],'pixels':13}])
        self.assertFalse(r['BG3_main_and_OBJ_subscreen_per_pixel_observed'])

    def test_forged_racer_pixel_is_not_accepted(self):
        archive,sha = fixture(mutate=True)
        with patch.object(qa,'STOCK_SHA',sha),zipfile.ZipFile(archive) as z:
            with self.assertRaisesRegex(ValueError,'pixel witness disagreement'):
                qa.check(z)

    def test_non_native_colour_and_bad_coordinate_rejected(self):
        for rgb in ([1,0,0],[True,0,0],[0],[0,0,300]):
            with self.assertRaises(ValueError):
                qa.packed5(rgb)
        with self.assertRaisesRegex(ValueError,'outside'):
            qa.pixel(bytes(342*224*4),342,47)
        with self.assertRaisesRegex(ValueError,'outside'):
            qa.pixel(bytes(342*224*4),100,False)


if __name__=='__main__':
    unittest.main()
