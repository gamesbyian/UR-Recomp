"""QA-01 full-result producer: synthetic contract tests, NEVER real witnesses."""
from __future__ import annotations

import sys
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_event_complete as target


def source_states(entry: int, result: int, track: int, menu: int, tally: bool = False):
    out = {}
    for f in range(entry - 1, result + 16):
        m = menu if f >= result else 0x16
        if tally and result - 60 <= f < result:
            m = 0x2F
        # Archived Bowl results observe 7E:0313 == 0x3C in the
        # 2F tally phase, not the active-race value 1.
        race_state = (0x3C if tally and result - 60 <= f < result
                      else (1 if entry <= f < result - 30 else 0))
        out[f] = {"track": track, "in_race": race_state, "menu": m}
    return out


def capture(menu=0xBC, text=None):
    if text is None:
        text = ["PLAYER", "TOTAL", "MIKE", "1:16.46"]
    return {"samples": [
                {"relative_frame": 0, "p1_x": 20, "p1_laps": 4},
                {"relative_frame": 218, "p1_x": 40, "p1_laps": 3},
                {"relative_frame": 1721, "p1_x": 80, "p1_laps": 2},
            ],
            "result": {"menu": menu}, "onset": {"menu": menu},
            "result_text": {"final": text, "onset": text}}


class CompleteEventProducerTests(unittest.TestCase):
    def test_terminal_result_is_guest_frame_bound_not_menu_alone(self):
        log = ("script f=3190 dump race-entered\n"
               "script f=8353 dump result-onset\n"
               "script f=8359 dump result-stable\n")
        self.assertEqual(target.observed_dump_frame(log, "result-onset"), 8353)
        self.assertEqual(target.observed_dump_frame(log, "result-stable"), 8359)
        with self.assertRaisesRegex(target.CompleteEventError, "exactly one"):
            target.observed_dump_frame(log, "result-tally")
        with self.assertRaisesRegex(target.CompleteEventError, "exactly one"):
            target.observed_dump_frame(log + "script f=8354 dump result-onset\n",
                                       "result-onset")

    def test_source_anchors_come_from_real_state_change_not_guess(self):
        event = target.source_event(source_states(3190, 8353, 1, 0xBC),
                                    1, 0xBC)
        self.assertEqual(event["original_entry_frame"], 3190)
        self.assertEqual(event["original_result_frame"], 8353)
        self.assertEqual(event["source_active_frames_to_result"], 5163)
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(source_states(3190, 8353, 1, 0xBC), 3, 0x99)
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(source_states(3190, 8353, 1, 0xBC), 1, 0x99)

    def test_transient_menu_scratch_and_inrace_result_like_values_do_not_end_event(self):
        states = source_states(3190, 8353, 1, 0xBC)
        # The stock DP $9F menu byte is reused as scratch during ordinary
        # gameplay. Even an observed 0xBC while still racing is not a result.
        states[4000]["menu"] = 0xBC
        states[4000]["in_race"] = 0
        for f in range(6200, 6220):
            states[f]["menu"] = 0xBC
            states[f]["in_race"] = 1
        event = target.source_event(states, 1, 0xBC)
        self.assertEqual(event["original_result_frame"], 8353)
        self.assertEqual(event["source_active_frames_to_result"], 5163)
        # No eight-frame settled result screen must fail closed.
        states = source_states(3190, 8353, 1, 0xBC)
        for f in range(8353, 8369):
            states[f]["menu"] = 0x16
        states[8353]["menu"] = 0xBC
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(states, 1, 0xBC)

    def test_bowl_source_course_switch_does_not_require_race_flag_deassert(self):
        states = source_states(8620, 11985, 2, 0x18, tally=True)
        # Prior Crawler course remains active through the new track-ID
        # transition: 7E:0313 stays asserted while 7E:00CE becomes Bowl.
        for f in range(8600, 8620):
            states[f]["in_race"] = 1
            states[f]["track"] = 1
        entry = target.source_event(states, 2, 0x18)
        self.assertEqual(entry["original_entry_frame"], 8620)
        self.assertEqual(entry["original_result_frame"], 11985)
        self.assertLess(entry["source_stunt_tally_frame"], 11985)
        self.assertEqual(target.source_event_diagnostic(
            states, 2, 0x18)["complete_event_qa_credit"], 0)
        # A one-frame track-ID scratch write must not count as entry.
        isolated = source_states(8620, 11985, 2, 0x18, tally=True)
        for f in range(8620, 8627):
            isolated[f]["track"] = 1
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(isolated, 2, 0x18)

    def test_stunt_tally_must_be_stable_and_track_matched(self):
        states = source_states(8620, 11985, 2, 0x18)
        states[11800]["menu"] = 0x2F
        states[11800]["in_race"] = 0
        with self.assertRaisesRegex(target.CompleteEventError, "missing prior"):
            target.source_event(states, 2, 0x18)
        # Even a long result-looking run cannot be admitted as a tally
        # while the original course remains in the active-race state.
        active_fake = source_states(8620, 11985, 2, 0x18)
        for f in range(11870, 11915):
            active_fake[f]["menu"] = 0x2F
            active_fake[f]["in_race"] = 1
        with self.assertRaisesRegex(target.CompleteEventError, "missing prior"):
            target.source_event(active_fake, 2, 0x18)
        for f in range(11915, 11980):
            states[f]["menu"] = 0x2F
            states[f]["in_race"] = 0
        event = target.source_event(states, 2, 0x18)
        self.assertEqual(event["source_stunt_tally_frame"], 11915)

    def test_stunt_requires_two_distinct_original_result_phases(self):
        states = source_states(8620, 11985, 2, 0x18, tally=True)
        event = target.source_event(states, 2, 0x18)
        self.assertEqual(event["source_stunt_tally_frame"], 11925)
        with self.assertRaisesRegex(target.CompleteEventError, "missing prior"):
            target.source_event(source_states(8620, 11985, 2, 0x18), 2, 0x18)

    def test_stock_route_selection_uses_original_menu_and_no_guest_poke(self):
        for case, (slot, _, menu, kind) in target.CASES.items():
            script = target.stock_crawler_script(slot)
            self.assertIn(f"until 009B == {slot - 1:02X} 600", script)
            self.assertEqual(script.count("press down 2"), slot - 1)
            self.assertEqual(script.count("dump race-entered"), 1)
            self.assertNotIn("poke ", script)
            frames = target.sample_frames(case, 5163)
            self.assertIn(0, frames)
            self.assertIn(64, frames)
            self.assertLess(max(frames), 5163 - 200)
            replay = target.replay_script(slot, menu, frames, kind == "stunt")
            self.assertIn(f"until 009F == {menu:02X} 9000", replay)
            self.assertEqual(replay.count("dump result-stable"), 1)
            self.assertNotIn("poke ", replay)
        self.assertIn("dump result-tally", target.replay_script(
            3, 0x18, target.sample_frames("bowl", 3500), True))
        self.assertNotIn("dump result-tally", target.replay_script(
            2, 0xBC, target.sample_frames("zoom-zoo", 5163), False))
        with self.assertRaisesRegex(target.CompleteEventError, "only"):
            target.stock_crawler_script(1)

    def test_result_parity_requires_score_text_and_all_guest_samples(self):
        ref = capture()
        nat = capture()
        self.assertTrue(target.diagnose(ref, nat, 0xBC, False)["paired_event_candidate"])
        nat["samples"][1]["p1_laps"] = 4
        mismatch = target.diagnose(ref, nat, 0xBC, False)
        self.assertEqual(mismatch["first_sample_disagreement"]["relative_frame"], 218)
        self.assertEqual(mismatch["first_sample_disagreement"]["fields"], ["p1_laps"])
        self.assertFalse(mismatch["paired_event_candidate"])
        nat = capture(text=["MIKE", "1:17.46"])
        self.assertFalse(target.diagnose(ref, nat, 0xBC, False)["paired_event_candidate"])
        nat = capture(menu=0x99)
        self.assertFalse(target.diagnose(ref, nat, 0xBC, False)["both_reached_terminal_menu"])

    def test_settled_score_parity_does_not_gate_on_tally_animation_glyphs(self):
        original = capture(0x18, ["BOWL", "MIKE", ": 764"])
        native = capture(0x18, ["BOWL", "MIKE", ": 764"])
        original["result_text"]["tally"] = ["BOWL", "COUNTING", "MIKE", ": 500"]
        native["result_text"]["tally"] = ["BOWL", "COUNTING", "MIKE", ": 720"]
        compared = target.diagnose(original, native, 0x18, True)
        self.assertFalse(compared["intermediate_result_text_matched"])
        self.assertTrue(compared["rendered_result_and_score_text_matched"])
        self.assertTrue(compared["paired_event_candidate"])

    def test_circuit_requires_two_observed_lap_decrements(self):
        reference, native = capture(), capture()
        self.assertTrue(target.diagnose(reference, native, 0xBC, False)[
            "circuit_multiple_lap_decrements_sampled"])
        for case in (reference, native):
            case["samples"][2]["p1_laps"] = 3
        result = target.diagnose(reference, native, 0xBC, False)
        self.assertTrue(result["both_reached_terminal_menu"])
        self.assertFalse(result["circuit_multiple_lap_decrements_sampled"])
        self.assertFalse(result["paired_event_candidate"])

    def test_result_menu_with_no_player_finish_time_is_not_a_race(self):
        reference = capture(0x99, ["SWITCHER", "MIKE", "NO TIME"])
        native = capture(0x99, ["SWITCHER", "MIKE", "NO TIME"])
        result = target.diagnose(reference, native, 0x99, False)
        self.assertTrue(result["both_reached_terminal_menu"])
        self.assertFalse(result["timed_race_or_circuit_result_visible"])
        self.assertFalse(result["paired_event_candidate"])

    def test_source_result_on_different_course_cannot_finish_event(self):
        source = source_states(3190, 8353, 1, 0xBC)
        source[4500]["track"] = 3
        with self.assertRaisesRegex(target.CompleteEventError, "never demonstrated"):
            target.source_event(source, 1, 0xBC)

    def test_original_source_entry_must_match_both_fresh_guests(self):
        source = {
            "p1_rider": 0, "p2_rider": 17,
            "p1_x": 9200, "p1_y": 1489,
            "p2_x": 9200, "p2_y": 1489,
            "p1_laps": 4, "p2_laps": 4,
            "p1_checkpoint": 0, "p1_finish_gate": 0,
            "clock_raw": [0, 0, 0, 0, 0],
        }
        equal = target.entry_diagnostics(source, dict(source), dict(source))
        self.assertTrue(equal["source_original_state_equivalent"])
        self.assertTrue(equal["fresh_reference_native_equivalent"])
        fresh = dict(source, p2_rider=18)
        wrong = target.entry_diagnostics(source, dict(source), fresh)
        self.assertFalse(wrong["source_original_state_equivalent"])
        self.assertFalse(wrong["fresh_reference_native_equivalent"])
        self.assertEqual(wrong["discrepancies"]["fresh_native"]["fields"],
                         ["p2_rider"])
        wrong = target.entry_diagnostics(source, fresh, fresh)
        self.assertFalse(wrong["source_original_state_equivalent"])
        # A shared different in-tour history is diagnostic only. A genuine
        # fresh paired completion remains admissible, if all other oracles pass.
        self.assertTrue(wrong["fresh_reference_native_equivalent"])
        with self.assertRaisesRegex(target.CompleteEventError, "incomplete"):
            target.entry_diagnostics(source, {"p1_x": 9200}, source)

    def test_cpu_time_or_score_cannot_stand_in_for_mike_p1(self):
        self.assertFalse(target.archived_p1_positive_result(
            ["MIKE", "NO TIME", "BRONSEN", "0:21.54"], False))
        self.assertFalse(target.archived_p1_positive_result(
            ["BRONSEN", ": 1200", "MIKE", ": 0"], True))
        self.assertTrue(target.archived_p1_positive_result(
            ["MIKE", ": 764", "QUALIFY", ": 68"], True))
        self.assertTrue(target.archived_p1_positive_result(
            ["MIKE", "1:16.46", "0:25.10"], False))
        cpu_win = capture(0x99, ["MIKE", "NO TIME", "BRONSEN", "0:21.54"])
        result = target.diagnose(cpu_win, capture(
            0x99, ["MIKE", "NO TIME", "BRONSEN", "0:21.54"]), 0x99, False)
        self.assertFalse(result["paired_event_candidate"])

    def test_stunt_idle_zero_score_cannot_pass_scored_result(self):
        ref = capture(0x18, ["BOWL", "MIKE", ": 0"])
        nat = capture(0x18, ["BOWL", "MIKE", ": 0"])
        self.assertFalse(target.diagnose(ref, nat, 0x18, True)["stunt_positive_score_visible"])
        self.assertFalse(target.diagnose(ref, nat, 0x18, True)["paired_event_candidate"])
        ref = capture(0x18, ["BOWL", "MIKE", ": 764"])
        nat = capture(0x18, ["BOWL", "MIKE", ": 764"])
        self.assertTrue(target.diagnose(ref, nat, 0x18, True)["paired_event_candidate"])

    def test_bounded_samples_include_original_circuit_changes(self):
        frames = target.sample_frames("zoom-zoo", 5163)
        for original_frame in (218, 604, 841, 1532, 1721):
            self.assertIn(original_frame, frames)
        self.assertGreater(len(frames), len(target.INITIAL_FRAMES))
        with self.assertRaisesRegex(target.CompleteEventError, "too short"):
            target.sample_frames("bowl", 200)


    def test_pinned_baldosa_uses_dense_scene_input_only_after_calibration(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build = root / "baldosa-build"
            build.mkdir()
            executable = build / "UniracersSNESRecomp"
            executable.write_text("placeholder")
            rom = root / "Uniracers_USA.sfc"
            rom.write_bytes(b"fixture")
            sram = root / "movie.srm"
            sram.write_bytes(b"S" * 8192)
            script = root / "route.script"
            script.write_text("dump race-entered\nquit\n")
            args = types.SimpleNamespace(
                native=executable, rom=rom, sram=sram,
                native_backend="pinned-baldosa",
            )
            invocations = []

            def fake_run(command, *, env, cwd, capture_output, text, timeout):
                invocations.append((command, env.copy(), cwd))
                self.assertTrue((build / "saves" / "save.srm").exists())
                return types.SimpleNamespace(stdout="script f=123 dump race-entered ok\n",
                                             stderr="")
            with mock.patch.object(target.subprocess, "run", side_effect=fake_run):
                result = target.replay_native(root, args, script, [], 0)
                self.assertIn("script f=123", result)
                self.assertNotIn("UR_QA_SCENE_INPUT_FILE", invocations[-1][1])
                self.assertFalse((root / "pinned-baldosa.input").exists())
                result = target.replay_native(root, args, script,
                                              [(1600, 2, 0x80), (1603, 1, 0x10)], 6)
                self.assertIn("script f=123", result)
                self.assertEqual((root / "pinned-baldosa.input").read_text(),
                                 "1606:2:080\n1609:1:010\n")
                self.assertEqual(invocations[-1][1]["UR_QA_SCENE_INPUT_FILE"],
                                 str(root / "pinned-baldosa.input"))
                self.assertIn("--no-launcher", invocations[-1][0])
                self.assertIn("--config", invocations[-1][0])
                self.assertFalse((build / "saves").exists())
            with self.assertRaisesRegex(target.CompleteEventError, "invalid"):
                target.replay_native(root, args, script,
                                     [(10, 1, 0x1000)], 0)


if __name__ == "__main__":
    unittest.main()
