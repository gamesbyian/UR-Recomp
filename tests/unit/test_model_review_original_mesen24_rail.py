"""Original Mesen24 source-only review rail integration and fail-closed browser data."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class OriginalMesen24BrowserTests(unittest.TestCase):
    def test_own_existing_pages_route_and_separate_source_controls(self):
        page = (ROOT/"tools/art/model-review/index.html").read_text()
        self.assertIn("id=\"originalMesen24Rail\"", page)
        self.assertIn("mountOriginalMesen24Rail", page)
        self.assertIn("original_mesen24_rail.mjs", page)
        rail = (ROOT/"tools/art/model-review/original_mesen24_rail.mjs").read_text()
        self.assertIn('width:224px;height:192px;object-fit:fill', rail)
        self.assertNotIn('object-fit:contain', rail)
        for path in ("tools/windows_visual_atlas.py", "tools/art/model-review/stage_pages.py"):
            self.assertIn("original_mesen24_rail.mjs", (ROOT/path).read_text())
            self.assertIn("original-mesen24", (ROOT/path).read_text())
        stage = (ROOT/"tools/art/model-review/stage_pages.py").read_text()
        self.assertIn('digest(path) != row.get("png_sha256")', stage)
        assert "source-poses.json" in stage
        assert "exact_original_rail" in (ROOT/"tools/windows_visual_atlas.py").read_text()

    @unittest.skipUnless(shutil.which("node"), "Node absent; static integration still checked")
    def test_pure_browser_packet_validation_without_original_3d_claim(self):
        script = r"""
import assert from 'node:assert/strict';
import {validateOriginalMesen24 as validate} from './tools/art/model-review/original_mesen24_rail.mjs';
const h='0'.repeat(64);
const frames=[];
for(const role of ['blue','red'])for(let tick=1601;tick<=1624;tick++){
 const id=(tick-1601)%24*64+(role==='blue'?60:57);
 frames.push({role,tick,original_OAM_slot:role==='blue'?96:97,
   original_ROM_frame_ID:id,source_phase_index:Math.floor(id/64),
   source_orientation_index:id%64,png:role+'-'+tick+'.png',
   png_sha256:h,source_4bpp_plane_sha256:h,source_RGBA_sha256:h});
}
const packet={
 schema:'UR-ART4K-ORIGINAL-MESEN24-VIEWER-REFERENCE/1',
 source_USA_ROM_sha256:'859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478',
 original_Mesen24_source_sha256:'28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6',
 exact_original_ROM_pose_receipt_sha256:'6286aedcda6080acf832ecece9fcdb879354db008e870bc00ada02db3ff3aa20',
 original_1994_3D_mesh_camera_pose_recovered:false,
 original_source_to_2026_GLB_joint_pose_verified:false,
 source_sprite_index_zero_transparent:true,
 source_pixel_size:[64,64],display_pixel_aspect:[7,6],frames};
assert.equal(validate(packet).frames.length,48);
const poison=(edit)=>{const copy=structuredClone(packet);edit(copy);
 assert.throws(()=>validate(copy));};
poison(p=>p.original_source_to_2026_GLB_joint_pose_verified=true);
poison(p=>p.original_1994_3D_mesh_camera_pose_recovered=true);
poison(p=>p.display_pixel_aspect=[1,1]);
poison(p=>p.frames.pop());
poison(p=>p.frames[0].png='../other.png');
poison(p=>p.frames[0].source_orientation_index=100);
poison(p=>p.frames[0].role='red');
poison(p=>p.frames[0].png_sha256='invalid');
poison(p=>p.original_Mesen24_source_sha256=h);
console.log('48 original states authenticated; no source-GLB pose mapping or URL escape');
"""
        r=subprocess.run(["node","--input-type=module","-e",script],
                         cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode,0,r.stdout+"\n"+r.stderr)


if __name__=="__main__":
    unittest.main()
