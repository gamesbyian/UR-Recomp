"""ROM/emulator-free validation of optional synchronized rider-state instrumentation."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"tools/capture_racer_composition_mesen.py"
WORKFLOW=ROOT/".github/workflows/racer-composition-mesen.yml"


def pure_source_helpers():
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
    names={"u16","pose_snapshot","bounded_watch_events"}
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:
            nodes.append(node)
        elif isinstance(node,ast.Assign) and any(
            isinstance(target,ast.Name) and target.id in {"POSE_WORDS","TRACE_WATCHES"}
            for target in node.targets
        ):
            nodes.append(node)
    assert len(nodes)==5
    namespace={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                 str(SOURCE),"exec"),namespace)
    return namespace


class SourceRiderPhaseTraceTests(unittest.TestCase):
    def test_original_wram_snapshot_is_little_endian_and_signed_when_named(self):
        n=pure_source_helpers()
        b=bytearray(0x1800)
        for addr,value in ((0x0F83,23),(0x0F49,63),(0x0F77,0x1234),
                           (0x0F97,0x0541),(0x0FE9,0x0541),(0x0FEB,0x0540),
                           (0x0F8F,0xFFFE),(0x0F69,0x8001),
                           (0x04C7,7),(0x04C9,55),(0x0306,1),(0x0300,1),
                           (0x12EB,0)):
            b[addr:addr+2]=value.to_bytes(2,"little")
        r=n["pose_snapshot"](bytes(b))
        self.assertEqual(r["w0F83_rider_wheel_presentation_phase_mod24"],23)
        self.assertEqual(r["w0F49_shared_current_uni_angle_index_mod64"],63)
        self.assertEqual(r["w0F97_shared_current_presentation_id"],0x0541)
        self.assertEqual(r["w0FE9_player1_persistent_presentation_id"],0x0541)
        self.assertEqual(r["w0FEB_player2_persistent_presentation_id"],0x0540)
        self.assertEqual(r["w0F8F_shared_rider_wheel_speed_signed16"],-2)
        self.assertEqual(r["w0F69_shared_rider_motion_signed16"],-32767)
        self.assertEqual(r["w04C7_player1_persistent_pitch_index"],7)
        self.assertEqual(r["w04C9_player2_persistent_pitch_index"],55)
        self.assertEqual(r["w0306_dma_pending"],1)
        with self.assertRaisesRegex(ValueError,"full original WRAM"):
            n["pose_snapshot"](bytes(0x17ff))

    def test_observational_exec_write_callbacks_preserve_original_PC_and_timing(self):
        n=pure_source_helpers()
        handles={"phase":"watch-1","angle":"watch-2"}
        events=[
            {"handle":"watch-1","address":0x0F83,"value":3,"frame":1602,
             "pcDisplay":"$83:EE6F","pc":0xEE6F,"pcBank":0x83,
             "cpuCycleCount":100001,"masterClock":34567},
            {"handle":"watch-2","address":0x0F49,"value":17,"frame":1602,
             "pcDisplay":"$83:F057","pc":0xF057,"pcBank":0x83,
             "cpuCycleCount":100777,"masterClock":34678},
        ]
        rows=n["bounded_watch_events"]({"events":events},handles)
        self.assertEqual([x["named_original_Wram_watch"] for x in rows],["phase","angle"])
        self.assertEqual([x["source_pc_display"] for x in rows],["$83:EE6F","$83:F057"])
        self.assertEqual([x["source_cpu_cycle"] for x in rows],[100001,100777])
        for invalid in (None,{},{"events":[{"handle":"unexpected","address":1,"value":3,"frame":3}]},
                        {"events":events*1024}):
            with self.assertRaises(ValueError):
                n["bounded_watch_events"](invalid,handles)

    def test_capture_reuses_existing_synchronized_breakpoints_without_original_3d_claim(self):
        s=SOURCE.read_text(encoding="utf-8")
        tree=ast.parse(s)
        self.assertIsNotNone(tree)
        for required in ('--trace-rider-state','"watch.create"','"watch.list"',
                         '"watch.delete"','"breakpoint.create"',
                         '"snesWorkRam"','"snesPrgRom"','source_rom_sha256',
                         'shared_working_phase_angle_not_per_player_bone_identity',
                         'original_1994_3d_rig_camera_or_joint_angles_recovered',
                         'original_source_frame_skipping_explicitly_disabled'):
            self.assertIn(required,s)

    def test_manual_workflow_unchanged_default_and_bounded_override(self):
        w=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("default: 1218",w)
        self.assertIn("trace_rider_state:",w)
        self.assertIn('if [[ "${{ inputs.trace_rider_state }}" == "true" ]]',w)
        self.assertIn('--advance-frames "${{ inputs.advance_frames || 1218 }}"',w)
        self.assertNotIn("  pull_request:",w)
        self.assertIn('trace+=(--trace-rider-state)',w)
        self.assertIn('MESEN_SNES_DISABLE_FRAME_SKIPPING: "1"',w)
        self.assertIn("SYNCHRONIZED_RACER_COMPOSITION_CONFIRMED",w)


if __name__=="__main__":
    unittest.main()
