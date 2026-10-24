"""ROM-free signed checkpoint chain audit tests (cryptography optional)."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"/"p2p"))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from signed_checkpoint_anchor_lab import ZERO, signature_message
    from checkpoint_chain_audit import verify_chain
    HAS_CRYPTO=True
except ImportError:
    HAS_CRYPTO=False

S="a"*32
@unittest.skipUnless(HAS_CRYPTO, "cryptography Ed25519 unavailable")
class ChainTests(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)

    def receipt(self,revision,previous,contacts=None):
        raw=json.dumps({"session":S,"revision":revision,
                        "previous_digest":previous,"contacts":contacts or []},
                       sort_keys=True,separators=(",",":")).encode()
        digest=hashlib.sha256(raw).hexdigest()
        return (raw,self.key.sign(signature_message(S,revision,digest))),digest

    def test_two_monotonic_signed_receipts(self):
        a,h1=self.receipt(1,ZERO)
        b,h2=self.receipt(2,h1)
        self.assertEqual(verify_chain([a,b],pinned_key=self.pub,session=S),(2,h2))

    def test_fork_is_rejected(self):
        a,h1=self.receipt(1,ZERO)
        b,_=self.receipt(2,ZERO)
        with self.assertRaises(ValueError):
            verify_chain([a,b],pinned_key=self.pub,session=S)

    def test_skipped_revision_is_rejected(self):
        a,h1=self.receipt(1,ZERO)
        b,_=self.receipt(3,h1)
        with self.assertRaises(ValueError):
            verify_chain([a,b],pinned_key=self.pub,session=S)

    def test_duplicate_signed_receipt_is_not_progress(self):
        a,_=self.receipt(1,ZERO)
        with self.assertRaises(ValueError):
            verify_chain([a,a],pinned_key=self.pub,session=S)

    def test_tampered_signature_is_rejected(self):
        a,_=self.receipt(1,ZERO)
        raw,sig=a
        with self.assertRaises(ValueError):
            verify_chain([(raw,sig[:-1]+bytes([sig[-1]^1]))],
                         pinned_key=self.pub,session=S)

    def test_independently_pinned_external_anchor(self):
        a,h1=self.receipt(1,ZERO)
        b,h2=self.receipt(2,h1)
        self.assertEqual(verify_chain([b],pinned_key=self.pub,session=S,
                                      initial_anchor=(1,h1)),(2,h2))

    def test_untrusted_external_anchor(self):
        b,_=self.receipt(2,ZERO)
        with self.assertRaises(ValueError):
            verify_chain([b],pinned_key=self.pub,session=S)

    def test_empty_chain_refused(self):
        with self.assertRaises(ValueError):
            verify_chain([],pinned_key=self.pub,session=S)

if __name__=="__main__":unittest.main()
