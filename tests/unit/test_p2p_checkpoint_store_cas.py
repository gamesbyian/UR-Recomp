"""ROM-free SQLite P2P signed checkpoint alias and CAS tests."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"/"p2p"))
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    import checkpoint_store_cas as store
    from signed_checkpoint_anchor_lab import signature_message
    HAS_CRYPTO=True
except ImportError:
    HAS_CRYPTO=False

@unittest.skipUnless(HAS_CRYPTO, "cryptography Ed25519 unavailable")
class LocalStoreNamespaceTest(unittest.TestCase):
    def test_symlink_hardlink_and_memory_db_refused(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);db=d/"anchor.db";store.initialize(db)
            self.assertEqual(store.read_anchor(db,"a"*32),(0,store.ZERO))
            link=d/"alias.db";link.symlink_to(db)
            with self.assertRaisesRegex(ValueError,"symlink"):
                store.read_anchor(link,"a"*32)
            hard=d/"hard.db";os.link(db,hard)
            with self.assertRaisesRegex(ValueError,"aliased"):
                store.read_anchor(db,"a"*32)
            with self.assertRaisesRegex(ValueError,"non-durable"):
                store.initialize(":memory:")

    def test_symlink_ancestor_refused(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);real=d/"real";real.mkdir()
            alias=d/"alias";alias.symlink_to(real,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"symlink"):
                store.initialize(alias/"db.sqlite")

    def test_signed_cas_and_alias_refusal(self):
        key=Ed25519PrivateKey.generate()
        pub=key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        session="a"*32
        raw=json.dumps({"session":session,"revision":1,
                        "previous_digest":store.ZERO,"contacts":[]},
                       sort_keys=True,separators=(",",":")).encode()
        digest=hashlib.sha256(raw).hexdigest()
        receipt=(raw,key.sign(signature_message(session,1,digest)))
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/"signed.db";store.initialize(db)
            self.assertEqual(store.commit_chain(db,session,(0,store.ZERO),
                                               [receipt],pub),(1,digest))
            self.assertEqual(store.read_anchor(db,session),(1,digest))
            link=Path(d)/"alias.db";link.symlink_to(db)
            with self.assertRaisesRegex(ValueError,"symlink"):
                store.commit_chain(link,session,(0,store.ZERO),[receipt],pub)
            self.assertEqual(store.read_anchor(db,session),(1,digest))

if __name__=="__main__":unittest.main()
