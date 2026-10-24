"""Two recovered real-TCP replay-state negatives for the nonshipping P2P pilot.

Source: verified Incoming archive Drive 1fXw7f5CkgsmkO_YBeXqR1aVZ2ngfAFxt,
whole ZIP SHA-256 458bef7a8782bbc5055f82546a77193cc21c630dc13d36d4692c8cf98abbf5f2.
Original first-party tests/test_p2p_commit.py member SHA-256
c1519576e04bbf2c8d7bbd8889851fbc11d2262bbb5c796fa68ecc68a9c71ca7.
New independently expressed tests of existing main logic. No archived held
source rewritten, no WAN/NAT/durable trust/gameplay/release claims.
"""
from pathlib import Path
import socket
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
try:
    import direct_loopback_handshake as p2p
except ImportError:
    p2p = None


@unittest.skipUnless(p2p is not None, "optional Ed25519 dependency unavailable")
class InvalidInviteReplayStateTests(unittest.TestCase):
    def setUp(self):
        self.initiator = p2p.Ed25519PrivateKey.generate()
        self.responder = p2p.Ed25519PrivateKey.generate()
        self.inviter_public = p2p.public_hex(self.initiator)
        self.responder_public = p2p.public_hex(self.responder)
        self.seen = set()

    def serve(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(3)
        address = listener.getsockname()
        outcome = []

        def worker():
            try:
                p2p.responder_once(listener, self.responder, self.inviter_public,
                                   "a" * 64, self.seen)
                outcome.append("authenticated")
            except Exception as exc:
                outcome.append(("rejected", str(exc)))
            finally:
                listener.close()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return address, thread, outcome

    def reject_then_accept(self, incompatible_invite):
        address, thread, outcome = self.serve()
        with self.assertRaises((ValueError, OSError)):
            p2p.initiator_connect(address, self.initiator,
                                  self.responder_public, incompatible_invite)
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome, [("rejected", "invitation context mismatch")])
        self.assertEqual(self.seen, set(),
                         "invalid signed invitation must not commit replay state")

        # A genuine subsequent invitation under the same build/peers must
        # still complete. An invalid offer did not poison the local store.
        correct = p2p.make_invite(self.initiator, self.responder_public)
        address, thread, outcome = self.serve()
        accepted = p2p.initiator_connect(address, self.initiator,
                                         self.responder_public, correct)
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome, ["authenticated"])
        self.assertEqual(accepted["responder"], self.responder_public)
        self.assertEqual(len(self.seen), 1)

    def test_signed_offer_for_other_build_does_not_burn_replay(self):
        wrong_build = p2p.make_invite(self.initiator, self.responder_public,
                                      build="f" * 64)
        self.reject_then_accept(wrong_build)

    def test_signed_offer_for_other_responder_does_not_burn_replay(self):
        another_responder = p2p.Ed25519PrivateKey.generate()
        wrong_peer = p2p.make_invite(self.initiator,
                                     p2p.public_hex(another_responder))
        self.reject_then_accept(wrong_peer)


if __name__ == "__main__":
    unittest.main()
