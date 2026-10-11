#!/usr/bin/env python3
"""R4 logical extinction/peer-introduction lab, never WAN/crypto proof."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/p2p/peer_island_directory_v0.py"
spec = importlib.util.spec_from_file_location("ur_peer_island", SOURCE)
assert spec and spec.loader
directory = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = directory
spec.loader.exec_module(directory)

def node(n, *, ip=None, issued=100, sequence=1, share=True,
         scope="wan", revoked=False, expires=200):
    ip = ip or "8.8.8." + str(n)
    return directory.Contact(
        owner=f"{n:02x}"*32, sequence=sequence,
        issued=issued, expires=expires,
        endpoints=() if revoked else ((ip, 7777),),
        scope=scope, share_consent=share if not revoked else False,
        revoked=revoked
    )


class IndependentP2PIslandModel(unittest.TestCase):
    def test_extinction_resurrection_with_manual_contact_and_consent(self):
        # A and B are completely new, with no bootstrap node, project
        # domain, global overlay or pre-seeded local directory.
        a = directory.PeerIslandDirectory()
        b = directory.PeerIslandDirectory()
        c = directory.PeerIslandDirectory()
        self.assertEqual(a.known(now=110), ())
        self.assertEqual(b.introduce(now=110, scope="wan"), ())
        # A sends a self-contained independently verified contact outside
        # the game. The module NEVER sends it or verifies its signature.
        a_contact = node(1)
        self.assertFalse(b.learn(a_contact,
                                 owner_signature_verified=False, now=110))
        self.assertTrue(b.learn(a_contact,
                                owner_signature_verified=True, now=110))
        self.assertEqual(b.known(now=110), (a_contact.owner,))
        # A's owner opted into third-party introductions. B may share A's
        # signed descriptor with C, but C still verifies owner proof.
        shared = b.introduce(now=110, scope="wan")
        self.assertEqual(shared, (a_contact,))
        self.assertTrue(c.learn(shared[0], owner_signature_verified=True,
                                now=111))
        self.assertEqual(c.known(now=111), (a_contact.owner,))
        # A can stop running; these are portable contacts, not a permanent
        # project-hosted directory. No network availability is inferred.
        self.assertEqual(a.introduce(now=201, scope="wan"), ())
        self.assertEqual(b.known(now=201), ())
        self.assertEqual(c.known(now=201), ())

    def test_islands_bridge_only_with_owner_consented_signed_records(self):
        west, east = directory.PeerIslandDirectory(), directory.PeerIslandDirectory()
        private = node(1, share=False)
        public = node(2, share=True)
        lan = node(3, ip="192.168.1.3", scope="lan", share=True)
        for peer in (private, public, lan):
            self.assertTrue(west.learn(peer, owner_signature_verified=True,
                                       now=110))
        self.assertEqual(west.introduce(now=110, scope="wan"), (public,))
        self.assertEqual(west.introduce(now=110, scope="lan"), (lan,))
        self.assertFalse(east.learn(private,
                                    owner_signature_verified=False, now=110))
        for peer in west.introduce(now=110, scope="wan"):
            east.learn(peer, owner_signature_verified=True, now=110)
        self.assertEqual(east.known(now=110), (public.owner,))
        # A bridge cannot expose a private contact or LAN IP merely by
        # connecting two islands. The owner must sign explicit share consent.
        self.assertNotIn(private, east.introduce(now=110, scope="wan"))
        self.assertNotIn(lan, east.introduce(now=110, scope="wan"))

    def test_expiry_replay_equivocation_and_owner_revocation(self):
        cache = directory.PeerIslandDirectory()
        original = node(1, share=True)
        self.assertTrue(cache.learn(original, owner_signature_verified=True,
                                    now=110))
        self.assertFalse(cache.learn(original, owner_signature_verified=True,
                                     now=111))
        forged_same_seq = node(1, ip="8.8.8.5")
        self.assertFalse(cache.learn(forged_same_seq,
                                     owner_signature_verified=True, now=111))
        revoked = node(1, sequence=2, revoked=True)
        self.assertTrue(cache.learn(revoked, owner_signature_verified=True,
                                    now=111))
        self.assertEqual(cache.known(now=111), ())
        self.assertFalse(cache.learn(original, owner_signature_verified=True,
                                     now=111))
        self.assertEqual(cache.introduce(now=111, scope="wan"), ())
        new = node(1, sequence=3, issued=112, expires=204)
        self.assertTrue(cache.learn(new, owner_signature_verified=True,
                                    now=115))
        self.assertEqual(cache.known(now=115), (original.owner,))
        self.assertEqual(cache.known(now=204), ())

    def test_bounded_eviction_and_exactly_limited_introduction(self):
        cache = directory.PeerIslandDirectory(capacity=2)
        x, y, z = node(1, expires=160), node(2, expires=170), node(3)
        for record in (x, y, z):
            self.assertTrue(cache.learn(record, owner_signature_verified=True,
                                        now=110))
        self.assertEqual(cache.known(now=110), tuple(sorted((y.owner, z.owner))))
        self.assertEqual(len(cache.introduce(now=110, scope="wan", limit=1)), 1)
        for kwargs in ({"capacity":0}, {"capacity":65},
                       {"capacity":True}):
            with self.assertRaises(ValueError):
                directory.PeerIslandDirectory(**kwargs)
        with self.assertRaises(ValueError):
            cache.introduce(now=110, scope="wan", limit=100)

    def test_invalid_dns_private_wan_multicast_oversized_and_wrong_signature(self):
        cache = directory.PeerIslandDirectory()
        base = node(1)
        mutations = [
            {"owner": "0"*64}, {"owner": "X"*64},
            {"sequence": True}, {"sequence": 0},
            {"issued": 200}, {"expires": 999999},
            {"scope": "overlay"}, {"share_consent": "yes"},
            {"endpoints": (("localhost", 7777),)},
            {"endpoints": (("192.168.1.8", 7777),)},
            {"endpoints": (("ff02::1", 7777),)},
            {"endpoints": (("0.0.0.0", 7777),)},
            {"endpoints": (("127.0.0.1", 7777),)},
            {"endpoints": (("8.8.8.8", 0),)},
            {"endpoints": (("8.8.8.8", 7777),)*2},
            {"endpoints": (("8.8.8.8", 7777),)*5},
            {"revoked": True},
        ]
        for changes in mutations:
            record = directory.Contact(**(dict(base.__dict__) | changes))
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                cache.learn(record, owner_signature_verified=True, now=110)
        self.assertFalse(cache.learn(base, owner_signature_verified=False,
                                     now=110))
        self.assertEqual(cache.known(now=110), ())
        with self.assertRaises(ValueError):
            cache.learn(base, owner_signature_verified=1, now=110)

if __name__ == "__main__":
    unittest.main()
