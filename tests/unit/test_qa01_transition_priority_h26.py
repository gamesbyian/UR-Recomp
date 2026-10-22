"""ROM-free bounded opposite-state QA01 probe priority regressions."""
import hashlib
import io
import sys
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_transition_priority as qa

SIZE = 131072
MISMATCH = bytes((1, 2, 3, 4))
LABELS = [1, 4, 8, 16, 32] + list(range(33, 69))


def fixture(*, missing=False, partial=False, duplicate=False):
    out = io.BytesIO()
    baseline = bytes(SIZE)
    bad = bytearray(baseline)
    bad[0x1ed:0x1f1] = MISMATCH
    if partial:
        bad[0x1ed+1:0x1f1] = b'\0' * 3
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with ZipFile(out, 'w', compression=ZIP_DEFLATED) as z:
            for f in LABELS:
                bad_state = f in (1, 4) or f >= 32
                name = f'scene-{f:05d}.wram.bin'
                z.writestr('work/zoom-zoo/replay/ref/' + name, baseline)
                if not (missing and f == 8):
                    z.writestr('work/zoom-zoo/replay/native/' + name,
                               bytes(bad) if bad_state else baseline)
            if duplicate:
                z.writestr('work/zoom-zoo/replay/ref/scene-00001.wram.bin', baseline)
    return out.getvalue()


class BoundedTransitionPriority(unittest.TestCase):
    def source(self, raw):
        with patch.object(qa, 'RF081_SHA', hashlib.sha256(raw).hexdigest()):
            return qa.qa01_transition_priority(raw)

    def test_bounded_transition_locates_earliest_missing_probe(self):
        result = self.source(fixture())
        self.assertEqual(result['earliest_bounded_interval'], [4, 8])
        self.assertEqual(result['earliest_bounded_probe'], 5)
        self.assertEqual(result['next_onset_probe'], 17)
        self.assertEqual(result['scene_pairs'], 41)
        self.assertFalse(result['assume_monotonicity'])
        self.assertEqual(result['complete_event_credit'], 0)

    def test_untrusted_source_sha_rejected(self):
        with self.assertRaisesRegex(ValueError, 'wrong genuine RF081 archive'):
            qa.qa01_transition_priority(fixture())

    def test_missing_peer_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing or duplicated pair'):
            self.source(fixture(missing=True))

    def test_partial_wram_mismatch_class_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unexpected mismatch class'):
            self.source(fixture(partial=True))

    def test_duplicate_member_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous or corrupt'):
            self.source(fixture(duplicate=True))


if __name__ == '__main__':
    unittest.main()
