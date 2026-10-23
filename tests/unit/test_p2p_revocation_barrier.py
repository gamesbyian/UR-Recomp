"""Source-only P2P signed owner-sequence replay-barrier regressions.

This model consumes a caller-supplied signature_verified boolean; tests do
not constitute network cryptographic authentication or durable anti-rollback.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "tools/p2p/peer_island_directory_v0.py"
spec = importlib.util.spec_from_file_location("ur_peer_island_replay_barrier", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def record(n, seq=1, issued=100, expires=200, revoked=False):
    return module.Contact(
        owner=f"{n:02x}" * 32, sequence=seq,
        issued=issued, expires=expires,
        endpoints=() if revoked else (("8.8.8.8", 7777),),
        scope="wan", share_consent=not revoked, revoked=revoked,
    )


class RevocationBarrierTests(unittest.TestCase):
    def test_expired_signed_revocation_blocks_old_contact(self):
        cache = module.PeerIslandDirectory()
        self.assertTrue(cache.learn(record(1), owner_signature_verified=True, now=110))
        self.assertTrue(cache.learn(record(1, 2, 120, 121, True),
                                    owner_signature_verified=True, now=120))
        self.assertEqual(cache.known(now=122), ())
        self.assertFalse(cache.learn(record(1), owner_signature_verified=True, now=122))
        self.assertTrue(cache.learn(record(1, 3, 122, 204),
                                    owner_signature_verified=True, now=123))

    def test_evicted_owner_keeps_signed_sequence(self):
        cache = module.PeerIslandDirectory(capacity=1)
        self.assertTrue(cache.learn(record(1, 2), owner_signature_verified=True, now=110))
        self.assertTrue(cache.learn(record(2), owner_signature_verified=True, now=110))
        self.assertFalse(cache.learn(record(1), owner_signature_verified=True, now=111))
        self.assertTrue(cache.learn(record(1, 3), owner_signature_verified=True, now=111))

    def test_expired_newer_contact_keeps_high_water(self):
        cache = module.PeerIslandDirectory()
        self.assertTrue(cache.learn(record(1), owner_signature_verified=True, now=110))
        self.assertTrue(cache.learn(record(1, 2, 120, 121), owner_signature_verified=True, now=120))
        cache.prune(122)
        self.assertFalse(cache.learn(record(1), owner_signature_verified=True, now=122))

    def test_barrier_capacity_refuses_new_owners(self):
        cache = module.PeerIslandDirectory(capacity=1)
        for n in range(1, module.MAX_PEERS + 1):
            self.assertTrue(cache.learn(record(n), owner_signature_verified=True, now=110))
        self.assertFalse(cache.learn(record(65), owner_signature_verified=True, now=110))
        self.assertFalse(cache.learn(record(1), owner_signature_verified=True, now=110))
        self.assertTrue(cache.learn(record(1, 2), owner_signature_verified=True, now=110))

    def test_restart_limitation_remains_explicit(self):
        cache = module.PeerIslandDirectory()
        self.assertTrue(cache.learn(record(1, 2), owner_signature_verified=True, now=110))
        self.assertFalse(cache.learn(record(1), owner_signature_verified=True, now=110))
        restarted = module.PeerIslandDirectory()
        self.assertTrue(restarted.learn(record(1), owner_signature_verified=True, now=110))


if __name__ == "__main__":
    unittest.main()
