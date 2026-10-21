"""ROM-free negative controls for the recovered RF081 sample-only contract."""
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import qa01_rf081_coverage as coverage
import qa01_rf081_pair_diff_census as census

WRAM_BYTES = 131072
SRAM_BYTES = 8192


def synthetic_archive(*, changed=False, missing=None, bad_phase=False):
    producer = {'relative_sample_frames': [0, 2]}
    case = {
        'disposition': 'strict_candidate',
        'evidence': {
            'original_event_frames': 7,
            'source_original_movie_vs_fresh_guest_result_phase': {
                'continuous_original_to_fresh_equivalence_proven': bad_phase,
            },
        },
    }
    members = {
        'producer-report.json': json.dumps(producer).encode(),
        'case-result.json': json.dumps(case).encode(),
    }
    for stage in ('race-entered', 'scene-00002', 'result-onset', 'result-stable'):
        for side in ('ref', 'native'):
            for kind, size in (('wram', WRAM_BYTES), ('sram', SRAM_BYTES)):
                data = bytearray(size)
                if changed and stage == 'scene-00002' and side == 'native' and kind == 'wram':
                    data[493] = 1
                name = f'work/zoom-zoo/replay/{side}/{stage}.{kind}.bin'
                members[name] = bytes(data)
    if missing:
        members.pop(missing)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in members.items():
            z.writestr(name, value)
    return stream.getvalue()


class RF081SampledCensusTests(unittest.TestCase):
    def assess(self, raw):
        # This test-only override creates a separately pinned synthetic source.
        # Production always enforces the genuine fixed RF081 archive SHA.
        with patch.object(coverage, 'ARCHIVE_SHA256', hashlib.sha256(raw).hexdigest()):
            return coverage.assess(raw)

    def cross_stage(self, raw):
        with patch.object(coverage, 'ARCHIVE_SHA256', hashlib.sha256(raw).hexdigest()):
            return census.cross_stage_census(raw)

    def test_complete_synthetic_census_is_not_event_credit(self):
        result = self.assess(synthetic_archive())
        self.assertEqual(result['sampled_race_frame_labels'], 2)
        self.assertEqual(result['paired_raw_memory_files'], 16)
        self.assertFalse(result['continuous_guest_execution_observed'])
        self.assertFalse(result['complete_USA_event_accepted'])
        self.assertEqual(result['release_gate_credit'], 0)

    def test_single_synthetic_wram_difference_with_exact_stage_counts(self):
        result = self.cross_stage(synthetic_archive(changed=True))
        self.assertEqual((result['total_wram_differences'],
                          result['total_sram_differences']), (1, 0))
        self.assertEqual((result['race_frame_labels'],
                          result['race_memory_pairs'],
                          result['terminal_memory_pairs']), (2, 4, 4))
        self.assertFalse(result['source_phase_equivalence'])
        self.assertFalse(result['complete_event_admitted'])

    def test_missing_original_sample_is_refused(self):
        raw = synthetic_archive(
            missing='work/zoom-zoo/replay/ref/scene-00002.wram.bin')
        with self.assertRaisesRegex(ValueError, 'missing raw'):
            self.assess(raw)

    def test_producer_claim_of_continuity_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'source qualification'):
            self.assess(synthetic_archive(bad_phase=True))

    def test_wrong_outer_digest_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'wrong original'):
            coverage.assess(synthetic_archive())


if __name__ == '__main__':
    unittest.main()
