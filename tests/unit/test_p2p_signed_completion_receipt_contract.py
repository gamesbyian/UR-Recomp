"""ROM-free signed-completion negatives, not a production P2P test."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "p2p"))
from signed_completion_receipt_contract import (completion_message,
                                                verify_responder_completion)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
except ImportError:
    Ed25519PrivateKey = None


def digest(value):
    return hashlib.sha256(value).hexdigest()


def verify(public, message, signature):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(public).verify(signature, message)
        return True
    except InvalidSignature:
        return False


@unittest.skipIf(Ed25519PrivateKey is None, "cryptography Ed25519 unavailable")
class SignedResponderCompletionTests(unittest.TestCase):
    def setUp(self):
        self.responder = Ed25519PrivateKey.generate()
        self.attacker = Ed25519PrivateKey.generate()
        pub = self.responder.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()
        self.expected = {
            "expected_responder": pub,
            "invite_sha256": digest(b"signed invite"),
            "response_sha256": digest(b"signed challenge"),
            "finish_sha256": digest(b"signed initiator finish"),
            "challenge_nonce": "a5" * 16,
        }
        payload = {"version": 1, "responder": pub,
                   **{k: v for k, v in self.expected.items()
                      if k not in ("expected_responder", "responder")}}
        self.receipt = {"type": "responder_complete", "payload": payload,
                        "signature": self.responder.sign(completion_message(payload)).hex()}

    def check(self, receipt=Ellipsis, **changes):
        verify_responder_completion(self.receipt if receipt is Ellipsis else receipt,
                                    verify_signature=verify, **(self.expected | changes))

    def test_genuine_signed_completion(self):
        self.check()

    def test_unsigned_success_status_rejected(self):
        for status in ({"status": "authenticated-loopback-only"},
                       {"type": "responder_complete", "payload": self.receipt["payload"]},
                       None):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.check(status)

    def test_attacker_signature_rejected(self):
        forged = copy.deepcopy(self.receipt)
        forged["signature"] = self.attacker.sign(completion_message(forged["payload"])).hex()
        with self.assertRaisesRegex(ValueError, "signature invalid"):
            self.check(forged)

    def test_replay_across_invite_response_finish_or_nonce_rejected(self):
        for field in ("invite_sha256", "response_sha256", "finish_sha256", "challenge_nonce"):
            changed = "bb" * (16 if field == "challenge_nonce" else 32)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "transcript mismatch"):
                self.check(**{field: changed})

    def test_wrong_responder_identity_rejected(self):
        other = self.attacker.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()
        with self.assertRaisesRegex(ValueError, "transcript mismatch"):
            self.check(expected_responder=other)

    def test_malformed_and_extra_fields_fail_closed(self):
        cases = []
        for key, value in (("signature", "x" * 128), ("type", "ack")):
            item = copy.deepcopy(self.receipt)
            item[key] = value
            cases.append(item)
        for key, value in (("version", True), ("finish_sha256", 42),
                           ("challenge_nonce", "a" * 31)):
            item = copy.deepcopy(self.receipt)
            item["payload"][key] = value
            cases.append(item)
        extra = copy.deepcopy(self.receipt)
        extra["payload"]["accepted"] = True
        cases.append(extra)
        for item in cases:
            with self.subTest(item=item), self.assertRaises(ValueError):
                self.check(item)

    def test_domain_separation_refuses_valid_signature_on_wrong_message(self):
        # A real signature over JSON without the completion domain, or a
        # different domain, must not authenticate this completion receipt.
        payload = self.receipt["payload"]
        canonical_json = json.dumps(payload, sort_keys=True,
                                    separators=(",", ":")).encode("ascii")
        valid_message = completion_message(payload)
        self.assertTrue(valid_message.endswith(canonical_json))
        for other_message in (canonical_json,
                              b"UR-P2P-INVITE/1\\x00".replace(b"\\x00", b"\x00") + canonical_json):
            forged = copy.deepcopy(self.receipt)
            forged["signature"] = self.responder.sign(other_message).hex()
            with self.subTest(other_message=other_message[:28]), self.assertRaisesRegex(
                    ValueError, "signature invalid"):
                self.check(forged)
        self.check()

    def test_canonical_payload_independent_of_dict_insertion_order(self):
        payload = self.receipt["payload"]
        reordered = dict(reversed(tuple(payload.items())))
        self.assertEqual(completion_message(payload), completion_message(reordered))
        receipt = copy.deepcopy(self.receipt)
        receipt["payload"] = reordered
        self.check(receipt)

    def test_signature_callback_failure_never_looks_like_success(self):
        def failed_verifier(*args):
            raise RuntimeError("backend unavailable")
        with self.assertRaisesRegex(ValueError, "signature invalid"):
            verify_responder_completion(self.receipt,
                                        verify_signature=failed_verifier,
                                        **self.expected)

    def test_untrusted_verifier_refused(self):
        for verifier in (None, lambda *args: 1, lambda *args: False):
            with self.subTest(verifier=verifier), self.assertRaises(ValueError):
                verify_responder_completion(self.receipt, verify_signature=verifier,
                                            **self.expected)


if __name__ == "__main__":
    unittest.main()
