"""Research-only local TCP handshake controls; no WAN, NAT, durability or release claim.

Sources: Drive 1fXw7f5CkgsmkO_YBeXqR1aVZ2ngfAFxt (ZIP CRC verified per member) and
1cW_qjnxY8mfclORRfSCIHkQbenhZ4XcO for the handshake prototype (#2111). The
cross-invite binding class is the archived test with its import adapted. The
commit-after-finish and unsigned-acknowledgment classes re-express the archived
findings because those two test members could not be extracted byte-exactly.
"""
import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
try:
    import direct_loopback_handshake as p2p
except ImportError:  # optional cryptography dependency
    p2p = None

BUILD = "a" * 64


def listen():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(3)
    return server


@unittest.skipUnless(p2p is not None, "optional cryptography dependency")
class HandshakeBase(unittest.TestCase):
    def setUp(self):
        self.initiator = p2p.Ed25519PrivateKey.generate()
        self.responder = p2p.Ed25519PrivateKey.generate()
        self.ipub = p2p.public_hex(self.initiator)
        self.rpub = p2p.public_hex(self.responder)
        self.invite = p2p.make_invite(self.initiator, self.rpub)
        self.seen = set()

    def serve_responder(self, server):
        outcome = []

        def run():
            try:
                outcome.append(("ok", p2p.responder_once(
                    server, self.responder, self.ipub, BUILD, self.seen)))
            except Exception as exc:  # recorded for assertions
                outcome.append(("error", str(exc)))
            finally:
                server.close()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread, outcome


class CommitAfterAuthenticatedFinish(HandshakeBase):
    def test_completed_handshake_commits_and_replay_is_refused(self):
        server = listen()
        thread, outcome = self.serve_responder(server)
        p2p.initiator_connect(server.getsockname(), self.initiator, self.rpub, self.invite)
        thread.join(4)
        self.assertEqual(outcome[0][0], "ok")
        self.assertEqual(len(self.seen), 1)
        again = listen()
        thread, outcome = self.serve_responder(again)
        with self.assertRaises((ValueError, OSError)):
            p2p.initiator_connect(again.getsockname(), self.initiator, self.rpub, self.invite)
        thread.join(4)
        self.assertEqual(outcome[0], ("error", "replayed invite"))

    def test_abort_after_response_does_not_consume_the_invite(self):
        server = listen()
        thread, outcome = self.serve_responder(server)
        with socket.create_connection(server.getsockname(), timeout=3) as conn:
            conn.settimeout(3)
            p2p.send(conn, self.invite)
            p2p.verify(p2p.recv(conn), "response", self.rpub)
        thread.join(4)
        self.assertEqual(outcome[0], ("error", "short framed read"))
        self.assertEqual(self.seen, set())
        retry = listen()
        thread, outcome = self.serve_responder(retry)
        p2p.initiator_connect(retry.getsockname(), self.initiator, self.rpub, self.invite)
        thread.join(4)
        self.assertEqual(outcome[0][0], "ok")

    def test_invalid_finish_does_not_commit(self):
        server = listen()
        thread, outcome = self.serve_responder(server)
        with socket.create_connection(server.getsockname(), timeout=3) as conn:
            conn.settimeout(3)
            p2p.send(conn, self.invite)
            p2p.verify(p2p.recv(conn), "response", self.rpub)
            wrong = p2p.Ed25519PrivateKey.generate()
            p2p.send(conn, p2p.signed(wrong, "finish", {"invite_digest": "0" * 64,
                                                      "response_digest": "0" * 64}))
        thread.join(4)
        self.assertEqual(outcome[0][0], "error")
        self.assertEqual(self.seen, set())


class UnsignedAcknowledgmentLimitation(HandshakeBase):
    def test_fake_endpoint_replaying_recorded_challenge_gets_success(self):
        """Documented limitation: the final acknowledgment is unsigned.

        A fake endpoint that replays a recorded responder challenge for the
        SAME invitation makes initiator_connect succeed although the genuine
        responder never received the finish and holds no replay state. The
        signed completion receipt in tools/p2p/signed_completion_receipt_contract.py
        is the intended fix; this test pins the prototype's behavior so it is
        never mistaken for completion evidence.
        """
        server = listen()
        thread, outcome = self.serve_responder(server)
        with socket.create_connection(server.getsockname(), timeout=3) as conn:
            conn.settimeout(3)
            p2p.send(conn, self.invite)
            challenge = p2p.recv(conn)
        thread.join(4)
        self.assertEqual(self.seen, set())

        fake = listen()

        def impostor():
            with fake.accept()[0] as conn:
                conn.settimeout(3)
                p2p.recv(conn)
                p2p.send(conn, challenge)
                p2p.recv(conn)
                p2p.send(conn, {"status": "authenticated-loopback-only"})
            fake.close()

        threading.Thread(target=impostor, daemon=True).start()
        result = p2p.initiator_connect(fake.getsockname(), self.initiator,
                                       self.rpub, self.invite)
        self.assertEqual(result["responder"], self.rpub)
        self.assertEqual(self.seen, set())

    def test_wrong_acknowledgment_text_is_refused(self):
        server = listen()

        def bad_responder():
            with server.accept()[0] as conn:
                conn.settimeout(3)
                invite = p2p.recv(conn)
                payload = invite["payload"]
                import hashlib, os
                response = {"invite_digest": hashlib.sha256(p2p.canonical(invite)).hexdigest(),
                            "session": payload["session"], "build": payload["build"],
                            "course": payload["course"], "mode": "2p",
                            "responder": self.rpub, "nonce": os.urandom(16).hex()}
                p2p.send(conn, p2p.signed(self.responder, "response", response))
                p2p.recv(conn)
                p2p.send(conn, {"status": "ok"})
            server.close()

        threading.Thread(target=bad_responder, daemon=True).start()
        with self.assertRaisesRegex(ValueError, "no peer acknowledgment"):
            p2p.initiator_connect(server.getsockname(), self.initiator, self.rpub, self.invite)


class CapturedChallengeBinding(HandshakeBase):
    def capture(self):
        server = listen()
        thread, outcome = self.serve_responder(server)
        with socket.create_connection(server.getsockname(), timeout=3) as conn:
            conn.settimeout(3)
            p2p.send(conn, self.invite)
            challenge = p2p.recv(conn)
            p2p.verify(challenge, "response", self.rpub)
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome[0], ("error", "short framed read"))
        self.assertEqual(self.seen, set())
        return challenge

    def check_different_invite(self, *, session):
        challenge = self.capture()
        other = p2p.make_invite(self.initiator, self.rpub, session=session)
        self.assertNotEqual(p2p.canonical(other), p2p.canonical(self.invite))
        server = listen()
        received = []

        def replay():
            try:
                with server.accept()[0] as conn:
                    conn.settimeout(3)
                    received.append(p2p.recv(conn))
                    p2p.send(conn, challenge)
                    try:
                        received.append(p2p.recv(conn))
                    except ValueError as exc:
                        received.append(str(exc))
            finally:
                server.close()

        thread = threading.Thread(target=replay, daemon=True)
        thread.start()
        with self.assertRaisesRegex(ValueError, "unbound responder context"):
            p2p.initiator_connect(server.getsockname(), self.initiator, self.rpub, other)
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(received[0], other)
        self.assertEqual(received[1], "short framed read")
        self.assertEqual(self.seen, set())

    def test_different_nonce_same_session(self):
        self.check_different_invite(session=self.invite["payload"]["session"])

    def test_different_session_and_nonce(self):
        self.check_different_invite(session="c" * 32)


if __name__ == "__main__":
    unittest.main()
