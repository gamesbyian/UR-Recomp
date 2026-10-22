"""H25 recovered signed P2P contact-identity whitespace controls."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from signed_checkpoint_anchor_lab import admit, signature_message, ZERO
    HAS_CRYPTO=True
except ImportError:
    HAS_CRYPTO=False

SESSION='a1'*16


@unittest.skipUnless(HAS_CRYPTO, 'optional Ed25519 library unavailable')
class ContactIdentityWhitespace(unittest.TestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        self.public=self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)

    def check(self,name):
        raw=json.dumps({'session':SESSION,'revision':1,
                        'previous_digest':ZERO,'contacts':[{'id':name}]},
                       sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        sig=self.private.sign(signature_message(
            SESSION,1,hashlib.sha256(raw).hexdigest()))
        return admit(raw,self.public,sig,SESSION,0,ZERO)

    def test_valid_contact_id(self):
        self.assertTrue(self.check('alice')['admit'])

    def test_internal_space_allowed(self):
        self.assertTrue(self.check('Alice Smith')['admit'])

    def test_leading_space_refused(self):
        self.assertFalse(self.check(' alice')['admit'])

    def test_trailing_space_refused(self):
        self.assertFalse(self.check('alice ')['admit'])

    def test_whitespace_only_refused(self):
        self.assertFalse(self.check('  ')['admit'])

    def test_nonbreaking_space_refused(self):
        self.assertFalse(self.check('alice\u00a0')['admit'])


if __name__=='__main__':
    unittest.main()
