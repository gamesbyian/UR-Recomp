"""Recovered H26 signed-checkpoint admission regressions for the current P2P pilot.

Original: Agent 1 H26 source/p2p/test_signed_checkpoint_anchor_lab.py.
Local, ROM-free, signed-data contract only. A restored trusted anchor can
still re-admit previously signed history: this is NOT durable anti-rollback.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from signed_checkpoint_anchor_lab import admit, signature_message, ZERO
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

SESSION = 'a1' * 16


@unittest.skipUnless(HAS_CRYPTO, "cryptography Ed25519 unavailable")
class SignedCheckpointAdmissionH26(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.raw = self.payload(1, ZERO)
        self.signature = self.sign(self.raw, 1)

    def payload(self, revision, previous, session=SESSION, contacts=None):
        return json.dumps(
            {'session': session, 'revision': revision,
             'previous_digest': previous, 'contacts': contacts or []},
            sort_keys=True, separators=(',', ':')).encode()

    def sign(self, raw, revision, session=SESSION):
        digest = hashlib.sha256(raw).hexdigest()
        return self.private.sign(signature_message(session, revision, digest))

    def test_genesis_and_idempotent_replay(self):
        first = admit(self.raw, self.public, self.signature, SESSION, 0, ZERO)
        self.assertTrue(first['admit'])
        same = admit(self.raw, self.public, self.signature,
                     SESSION, *first['next_anchor'])
        self.assertTrue(same['admit'])

    def test_signed_successor_updates_highwater(self):
        first = admit(self.raw, self.public, self.signature, SESSION, 0, ZERO)
        successor = self.payload(2, first['next_anchor'][1])
        result = admit(successor, self.public, self.sign(successor, 2),
                       SESSION, *first['next_anchor'])
        self.assertTrue(result['admit'])
        self.assertEqual(result['next_anchor'][0], 2)

    def test_signature_tamper_rejected(self):
        altered = self.payload(1, ZERO, contacts=[{'id': 'forged'}])
        self.assertFalse(
            admit(altered, self.public, self.signature, SESSION, 0, ZERO)['admit'])

    def test_wrong_pinned_key_rejected(self):
        other = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.assertFalse(
            admit(self.raw, other, self.signature, SESSION, 0, ZERO)['admit'])

    def test_session_replay_rejected(self):
        self.assertFalse(
            admit(self.raw, self.public, self.signature, 'b2' * 16, 0, ZERO)['admit'])

    def test_rollback_rejected_when_anchor_persists(self):
        first = admit(self.raw, self.public, self.signature, SESSION, 0, ZERO)
        next_raw = self.payload(2, first['next_anchor'][1])
        second = admit(next_raw, self.public, self.sign(next_raw, 2),
                       SESSION, *first['next_anchor'])
        self.assertFalse(
            admit(self.raw, self.public, self.signature,
                  SESSION, *second['next_anchor'])['admit'])

    def test_skipped_revision_rejected(self):
        third = self.payload(3, ZERO)
        self.assertFalse(
            admit(third, self.public, self.sign(third, 3),
                  SESSION, 0, ZERO)['admit'])

    def test_wrong_previous_digest_rejected(self):
        wrong = self.payload(1, 'f' * 64)
        self.assertFalse(
            admit(wrong, self.public, self.sign(wrong, 1),
                  SESSION, 0, ZERO)['admit'])

    def test_duplicate_and_nonfinite_fields_rejected(self):
        for raw in (self.raw[:-1] + b',"revision":1}',
                    self.raw[:-1] + b',"bad":1e999}',
                    self.raw[:-1] + b',"bad":NaN}'):
            with self.subTest(raw=raw):
                self.assertFalse(
                    admit(raw, self.public, self.signature,
                          SESSION, 0, ZERO)['admit'])

    def test_boolean_revision_rejected(self):
        raw = self.payload(True, ZERO)
        self.assertFalse(
            admit(raw, self.public, b'0' * 64, SESSION, 0, ZERO)['admit'])

    def test_signed_rollback_accepted_if_local_anchor_is_rolled_back_too(self):
        # Negative security result: rollback of external trust defeats this
        # local admission pilot; there is no durable monotonicity guarantee.
        first = admit(self.raw, self.public, self.signature, SESSION, 0, ZERO)
        self.assertTrue(first['admit'])
        self.assertTrue(
            admit(self.raw, self.public, self.signature, SESSION, 0, ZERO)['admit'])


if __name__ == '__main__':
    unittest.main()
