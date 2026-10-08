"""ROM-free P1 queue-message identity versus delayed persistent boost."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract_stunt_queue_events as q  # noqa: E402


def wram(track=19, race=1, reader=0, writer=0, boost=0,
         slots=None, size=q.WRAM_LEN, x_speed=448, laps=2, enable=0):
    b = bytearray(size)
    if size < q.WRAM_LEN:
        return bytes(b)
    b[0x00CE], b[0x0313] = track, race
    for a, value in ((q.READ_INDEX, reader), (q.WRITE_INDEX, writer),
                     (q.PERSISTENT_BOOST, boost)):
        b[a:a + 2] = value.to_bytes(2, "little")
    b[q.X_SPEED:q.X_SPEED + 2] = x_speed.to_bytes(2, "little", signed=True)
    b[q.LAST_LAP_REMAINING:q.LAST_LAP_REMAINING + 2] = laps.to_bytes(2, "little")
    b[q.LAST_LAP_ENABLE] = enable
    for k, v in (slots or {}).items():
        b[q.QUEUE_BASE + k] = v
    return bytes(b)


class QueueIdentityTests(unittest.TestCase):
    def test_exact_writer_slot_event_before_later_boost(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            # Ring wrap: the write from 31 to 0 is message 0x09 at slot 31.
            for frame, data in enumerate([
                wram(reader=31, writer=31, boost=0),
                wram(reader=31, writer=0, boost=0, slots={31: 0x09},
                     laps=1, enable=1),
                wram(reader=0, writer=0, boost=128, slots={31: 0x09},
                     laps=1, enable=1),
            ]):
                (d / f"w{frame:03d}.wram.bin").write_bytes(data)
            rows = q.read_series(d, 0, 2)
            found = q.analyze(rows)
            self.assertEqual(found["last_lap_transitions"], [{
                "frame": 1, "previous": 2, "last_lap_enable_at_transition": 1,
                "sram_mode_low_at_transition": None,
                "note": "per-player post-decrement lap word; not a credit assertion",
            }])
            self.assertEqual(rows[1]["last_lap_enable"], 1)
            self.assertEqual(found["enqueued_messages"], [
                {"frame": 1, "slot": 31, "message_id": "0x09", "read_index": 31}
            ])
            self.assertEqual(found["positive_net_boost_events"][0]["frame"], 2)
            self.assertEqual(found["positive_net_boost_events"][0]["net_boost_increase"], 128)
            self.assertEqual(found["positive_net_boost_events"][0]["preceding_enqueues"], [
                {"frame": 1, "message_id": "0x09"}
            ])
            self.assertIn("unproven", found["positive_net_boost_events"][0]["attribution"])
            self.assertTrue(q.compare(rows, copy.deepcopy(rows))["native_reference_equal"])
            other = copy.deepcopy(rows)
            other[2]["boost"] = 124
            self.assertEqual(q.compare(rows, other)["first_divergence"],
                             {"frame": 2, "fields": ["boost"]})

    def test_optional_sram_mode_gate_is_never_guessed(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "w000.wram.bin").write_bytes(wram())
            (d / "w001.wram.bin").write_bytes(wram(laps=1, enable=1))
            with self.assertRaisesRegex(q.QueueEvidenceError, "missing required SRAM"):
                q.read_series(d, 0, 1, require_sram=True)
            sram = bytearray(0x2000)
            sram[0x074B] = 2
            (d / "w000.sram.bin").write_bytes(sram)
            with self.assertRaisesRegex(q.QueueEvidenceError, "partial SRAM"):
                q.read_series(d, 0, 1)
            (d / "w001.sram.bin").write_bytes(sram)
            rows = q.read_series(d, 0, 1, require_sram=True)
            self.assertEqual(rows[1]["sram_mode_low"], 2)
            self.assertEqual(q.analyze(rows)["last_lap_transitions"][0][
                "sram_mode_low_at_transition"], 2)
            (d / "w001.sram.bin").write_bytes(bytes(11))
            with self.assertRaisesRegex(q.QueueEvidenceError, "invalid SRAM size"):
                q.read_series(d, 0, 1, require_sram=True)

    def test_multiple_enqueues_preserve_order_without_inventing_attribution(self):
        before = {"frame": 7, "write": 30, "read": 29, "buffer": tuple([0] * 32),
                  "boost": 20, "air": 5, "x_speed": 400,
                  "laps_remaining": 2, "last_lap_enable": 0, "sram_mode_low": None}
        after = copy.deepcopy(before)
        payload = list(after["buffer"])
        payload[30], payload[31] = 0x01, 0x09
        after.update(frame=8, write=0, buffer=tuple(payload), boost=140)
        found = q.analyze([before, after])
        self.assertEqual([x["message_id"] for x in found["enqueued_messages"]],
                         ["0x01", "0x09"])
        self.assertEqual(len(found["positive_net_boost_events"][0]["preceding_enqueues"]), 2)
        after["write"] = 29
        with self.assertRaisesRegex(q.QueueEvidenceError, "unsafe"):
            q.analyze([before, after])

    def test_capture_integrity_and_frame_gap(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            file = d / "w000.wram.bin"
            file.write_bytes(wram())
            with self.assertRaisesRegex(q.QueueEvidenceError, "missing"):
                q.read_series(d, 0, 1)
            for image, term in ((wram(size=0x10000), "size"),
                                (wram(track=21), "course"),
                                (wram(race=0), "course"),
                                (wram(writer=32), "indices")):
                file.write_bytes(image)
                with self.assertRaisesRegex(q.QueueEvidenceError, term):
                    q.read_series(d, 0, 0)
            with self.assertRaisesRegex(q.QueueEvidenceError, "selector"):
                q.read_series(d, 0, 0, prefix="../escape")
        row = {"frame": 1, "write": 0, "read": 0, "boost": 0, "buffer": tuple([0]*32),
               "air": 0, "x_speed": 0, "laps_remaining": 2, "last_lap_enable": 0,
               "sram_mode_low": None}
        with self.assertRaisesRegex(q.QueueEvidenceError, "missing or out-of-order"):
            q.analyze([row, dict(row, frame=3)])
        with self.assertRaisesRegex(q.QueueEvidenceError, "nonempty"):
            q.compare([], [])


if __name__ == "__main__":
    unittest.main()
