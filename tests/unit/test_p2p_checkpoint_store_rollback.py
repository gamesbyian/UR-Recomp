"""Independent H27 filesystem rollback negative for local P2P checkpoint CAS.

A private, valid, signed SQLite state cannot itself prevent restoration of an
older signed DB snapshot. This test MUST continue to demonstrate the limit.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"/"p2p"))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from signed_checkpoint_anchor_lab import ZERO,signature_message
    import checkpoint_store_cas as store
    HAS_CRYPTO=True
except ImportError:
    HAS_CRYPTO=False

@unittest.skipUnless(HAS_CRYPTO,"cryptography Ed25519 unavailable")
class SignedLocalDBRollbackTest(unittest.TestCase):
    def test_actual_old_database_restore_replays_signed_checkpoint(self):
        key=Ed25519PrivateKey.generate()
        public=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        session="a"*32

        def signed(revision,previous):
            raw=json.dumps({"session":session,"revision":revision,
                            "previous_digest":previous,"contacts":[]},
                           sort_keys=True,separators=(",",":")).encode()
            digest=hashlib.sha256(raw).hexdigest()
            return (raw,key.sign(signature_message(session,revision,digest))),digest

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            path=root/"anchor.db"
            old=root/"snapshot.db"
            replacement=root/"restore.tmp"
            store.initialize(path)
            first,d1=signed(1,ZERO)
            second,d2=signed(2,d1)
            self.assertEqual(store.commit_chain(path,session,(0,ZERO),[first],public),(1,d1))
            shutil.copyfile(path,old)
            self.assertEqual(store.commit_chain(path,session,(1,d1),[second],public),(2,d2))
            # This is a real on-disk restoration, with valid old signed data.
            shutil.copyfile(old,replacement)
            os.replace(replacement,path)
            self.assertEqual(store.read_anchor(path,session),(1,d1))
            # An independently unprotected external anchor can also be reset.
            self.assertEqual(store.commit_chain(path,session,(1,d1),[second],public),(2,d2))
            self.assertEqual(store.read_anchor(path,session),(2,d2))

if __name__=="__main__":
    unittest.main()
