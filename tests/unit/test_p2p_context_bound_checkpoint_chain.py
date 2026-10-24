"""Source-free context-bound P2P signed checkpoint acceptance controls."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"/"p2p"))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from signed_checkpoint_anchor_lab import ZERO,signature_message
    from context_bound_checkpoint_chain import verify_context_bound_chain
    HAS_CRYPTO=True
except ImportError:
    HAS_CRYPTO=False

@unittest.skipUnless(HAS_CRYPTO,"cryptography Ed25519 unavailable")
class ContextBoundCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        self.session="a"*32
        self.raw=json.dumps({"session":self.session,"revision":1,
                             "previous_digest":ZERO,"contacts":[]},
                            sort_keys=True,separators=(",",":")).encode()
        self.digest=hashlib.sha256(self.raw).hexdigest()
        self.sig=self.key.sign(signature_message(self.session,1,self.digest))
        self.context={"session":self.session,
                      "inviter_key_sha256":hashlib.sha256(self.public).hexdigest(),
                      "revision":0,"digest":ZERO}

    def check(self,context=None,receipts=None,**overrides):
        return verify_context_bound_chain(
            [(self.raw,self.sig)] if receipts is None else receipts,
            pinned_key=overrides.get("pinned_key",self.public),
            session=overrides.get("session",self.session),
            trusted_context=self.context if context is None else context)

    def test_signed_advancement_bound_to_trusted_key_and_session(self):
        result=self.check()
        self.assertEqual(result["revision"],1)
        self.assertEqual(result["digest"],self.digest)
        self.assertEqual(result["inviter_key_sha256"],self.context["inviter_key_sha256"])

    def test_independent_identity_or_session_change_refused(self):
        for forged in (
            dict(self.context,inviter_key_sha256="0"*64),
            dict(self.context,session="b"*32),
        ):
            with self.subTest(forged=forged),self.assertRaises(ValueError):
                self.check(context=forged)
        with self.assertRaises(ValueError):
            self.check(session="b"*32)

    def test_incomplete_and_boolean_revision_anchor_refused(self):
        for forged in (dict(self.context,revision=True),
                       dict(self.context,revision=-1),
                       dict(self.context,extra="not allowed"),
                       {k:v for k,v in self.context.items() if k!="digest"}):
            with self.subTest(forged=forged),self.assertRaises(ValueError):
                self.check(context=forged)

    def test_stale_high_water_or_bad_signature_refused(self):
        with self.assertRaises(ValueError):
            self.check(context=dict(self.context,revision=1))
        with self.assertRaises(ValueError):
            self.check(receipts=[(self.raw,self.sig[:-1]+bytes([self.sig[-1]^1]))])

if __name__=="__main__":unittest.main()
