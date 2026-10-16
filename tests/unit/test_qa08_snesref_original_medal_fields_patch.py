"""Source-only original 2014 Snes9x medal field probe and negative contracts."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_snesref_original_medal_fields_patch as original_patch
import qa08_snesref_original_blackout_host_patch as blackout
import qa08_verify_original_medal_endfields as verify

class MedalFieldReadOnlyHostPatch(unittest.TestCase):
    def setUp(self):
        self.source="static void do_dump(const char* tag) {}\n"+blackout.WRITE_HISTORY+blackout.HOOK_AFTER

    def test_previous_zero_input_change_reference_and_idempotence(self):
        changed=original_patch.patch_source(self.source)
        self.assertEqual(original_patch.patch_source(changed),changed)
        self.assertEqual(changed.count(original_patch.MARK),1)
        self.assertIn('g_frame == 1280',changed)
        self.assertIn('g_frame == 4032',changed)
        self.assertIn('g_frame == 4176',changed)
        self.assertIn('UR_QA08_ORIGINAL_MEDAL_FIELDS',changed)
        self.assertEqual(changed.replace(original_patch.AFTER,blackout.HOOK_AFTER),self.source)
        self.assertEqual(changed.count('p_retro_run();'),1)
        self.assertEqual(changed.count('trace_tick();'),1)
        self.assertNotIn('p_retro_run();\n        p_retro_run();',changed)

    def test_unqualified_original_host_never_accepted_or_partially_patched(self):
        for bad in (self.source.replace(blackout.WRITE_HISTORY,""),
                    self.source.replace(blackout.HOOK_AFTER,""),
                    self.source+self.source,
                    original_patch.patch_source(self.source).replace(
                      'g_frame == 4032','g_frame == 4032')):
            with self.subTest(bad=bad[:55]),self.assertRaises(ValueError):
                original_patch.patch_source(bad)

    def test_original_source_revision_required_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/blackout.base.RELATIVE
            path.parent.mkdir(parents=True)
            path.write_text(self.source)
            with patch.object(blackout.base,"rev",return_value="other"):
                with self.assertRaises(ValueError):
                    original_patch.apply(root,write=True)
            self.assertEqual(path.read_text(),self.source)

class ActualOriginalFieldReceipt(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.prev=self.root/"prior"
        self.prev.mkdir()
        self.root.joinpath("registers").mkdir()
        self.root.joinpath("frames").mkdir()
        self.script=self.root/"script"
        self.script.write_bytes(b"original-controller-input\n")
        self.log=self.root/"original.log"
        lines=[]
        refs=[]
        self.host_hashes={}
        for frame,tag in verify.CALLBACKS.items():
            raw=bytearray(256*224*4)
            for (x,y),rgb in verify.POINTS[frame].items():
                i=(y*256+x)*4
                raw[i:i+4]=bytes((rgb[2],rgb[1],rgb[0],0))
            path=self.root/"registers"/tag
            (self.root/"frames"/f"frame_{frame:06d}_256x224.raw").write_bytes(raw)
            # Same numbered original callback and host end-field image are
            # distinct valid source producers, never assumed pixel-identical.
            host=bytearray(raw)
            path.with_suffix(".fb.bgrx").write_bytes(host)
            self.host_hashes[frame]=hashlib.sha256(host).hexdigest()
            oam=bytearray(544)
            for slot,tileattr in verify.SOURCE_MEDAL_TILE_ATTR.get(frame,{}).items():
                attr=int(tileattr[:2],16);tile=int(tileattr[2:],16)
                y=91 if slot==112 else 115 if slot==113 else 139 if slot==114 else (112 if slot in (96,98) else 88)
                x=200 if slot in (112,113,114) else 219
                oam[slot*4:slot*4+4]=bytes((x,y,tile,attr))
            path.with_suffix(".oam.bin").write_bytes(oam)
            path.with_suffix(".cgram.bin").write_bytes(bytes(512))
            path.with_suffix(".ppuw.tsv").write_bytes(
                b"#frame\tvcounter\thcounter\taddr\tvalue\tsource\n")
            path.with_suffix(".regs.json").write_text(json.dumps(
                {"frame_tag":frame+1,"total_emulated_frames":frame+1}))
            path.with_suffix(".info.json").write_text(json.dumps({
                "frame":frame+1,"fb_frame":frame+1,"tag":tag,
                "fb_width":256,"fb_height":224,"fb_dump_format":"BGRX8888",
                "ppuw_truncated":False,"no_colormath":False,"no_clip":False}))
            refs.append({"real_original_snes9x_callback_frame":frame,
                         "original_unchanged_BGRX_sha256":hashlib.sha256(raw).hexdigest()})
            lines.append(f"script f={frame+1} dump {tag} fb=256x224 BGRX8888")
        lines.append("script f=5484 quit")
        self.log.write_text("\n".join(lines))
        (self.prev/"qa08-original-2p-fullroute.json").write_text(json.dumps({
            "actual_callbacks_captured":263,"actual_script_quit_frame":5484,
            "exact_original_two_pad_route_LF_without_turbo_sha256":hashlib.sha256(
              self.script.read_bytes()).hexdigest(),
            "each_authentic_callback":refs}))

    def accept(self):
        if True:
            return verify.verify(self.root,self.prev,self.log,self.script)

    def test_three_actual_source_frames_and_OAM_slots(self):
        d=self.accept()
        self.assertEqual(d["original_unmodified_callback_endfield_count"],3)
        self.assertEqual([f["actual_original_callback"]
                          for f in d["original_unmodified_source_PPU_field_samples"]],
                         [1279,4031,4175])
        self.assertTrue(d["original_snapshot_OAM_is_not_effective_line_OBJ_owner"])
        self.assertFalse(d["original_host_snapshot_RGB_not_relabelled_as_original_callback"])
        for row in d["original_unmodified_source_PPU_field_samples"]:
            f=row["actual_original_callback"]
            self.assertTrue(row["host_endfield_is_the_same_preincrement_video_callback"])
        self.assertFalse(d["original_native_identical_cpu_field_phase_accepted"])
        self.assertFalse(d["physical_windows_7to6_4x_HD_likeness_release_approved"])

    def test_pixel_and_ppu_state_forgery_cannot_pass(self):
        p=self.root/"registers/qa08_medal_4032.fb.bgrx"
        original=p.read_bytes()
        p.write_bytes(original[:-1]+bytes((original[-1]^1,)))
        with self.assertRaisesRegex(ValueError,"properly aligned original postrun"):
            self.accept()
        p.write_bytes(original)
        q=self.root/"registers/qa08_medal_4176.oam.bin"
        q.write_bytes(bytes(543))
        with self.assertRaisesRegex(ValueError,"incomplete original"):
            self.accept()

    def accept_input(self,script):
        with patch.dict(verify.HOST_FRAME_SHA256,self.host_hashes):
            return verify.verify(self.root,self.prev,self.log,script)

    def test_original_input_and_callback_selection_guard(self):
        with self.assertRaises(ValueError):
            self.accept_input(self.root/"original.log")
        self.log.write_text(self.log.read_text()+"\nscript f=4031 dump qa08_medal_4032 fb=256x224 BGRX8888\n")
        with self.assertRaisesRegex(ValueError,"missing/duplicated"):
            self.accept()

if __name__=="__main__":
    unittest.main()
