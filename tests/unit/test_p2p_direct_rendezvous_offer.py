"""Offline signed rendezvous research tests, not network reachability."""
import json
from pathlib import Path
import sys
import unittest
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError as exc:
    raise unittest.SkipTest('optional cryptography package not installed') from exc

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'/'p2p'))
from direct_rendezvous_offer import verify_offer,DOMAIN

class RendezvousOfferTests(unittest.TestCase):
    def setUp(self):
        self.sk=Ed25519PrivateKey.generate()
        self.key=self.sk.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                                   format=serialization.PublicFormat.Raw)
        self.obj=dict(version=1,session='a1'*16,nonce='b2'*16,inviter_key=self.key.hex(),
                      issued=100000,expires=100300,scope='public',
                      endpoints=[dict(ip='8.8.8.8',port=5678),
                                 dict(ip='2606:4700::1111',port=5678)])
    def pack(self,obj=None):
        raw=json.dumps(obj or self.obj,sort_keys=True,separators=(',',':')).encode()
        return raw,self.sk.sign(DOMAIN+raw)

    def test_signed_offer_requires_out_of_band_key_pin(self):
        raw,sig=self.pack()
        result=verify_offer(raw,sig,self.key,100100)
        self.assertEqual(len(result['candidates']),2)
        self.assertIsNone(result['reachable'])
        self.assertEqual(result['identity_assurance'],'out-of-band-key-pin-only')

    def test_lan_candidate_requires_explicit_lan_scope(self):
        self.obj['endpoints']=[dict(ip='192.168.1.3',port=4567)]
        raw,sig=self.pack()
        with self.assertRaises(ValueError):verify_offer(raw,sig,self.key,100100)
        self.obj['scope']='lan'
        raw,sig=self.pack()
        self.assertEqual(verify_offer(raw,sig,self.key,100100)['scope'],'lan')

    def test_wrong_key_and_signature_refused(self):
        raw,sig=self.pack()
        with self.assertRaises(ValueError):verify_offer(raw,sig,b'0'*32,100100)
        with self.assertRaises(ValueError):verify_offer(raw,b'0'*64,self.key,100100)

    def test_signed_bytes_cannot_be_tampered(self):
        raw,sig=self.pack()
        with self.assertRaises(ValueError):
            verify_offer(raw.replace(b'5678',b'5679'),sig,self.key,100100)

    def test_expiry_not_before_replay_refused(self):
        raw,sig=self.pack()
        for now in (99900,100301,True):
            with self.subTest(now=now),self.assertRaises(ValueError):
                verify_offer(raw,sig,self.key,now)
        with self.assertRaisesRegex(ValueError,'replayed'):
            verify_offer(raw,sig,self.key,100100,used_sessions={self.obj['session']})

    def test_duplicate_unsorted_and_invalid_candidates_refused(self):
        for endpoints in (
            [self.obj['endpoints'][1],self.obj['endpoints'][0]],
            [self.obj['endpoints'][0],self.obj['endpoints'][0]],
            [dict(ip='8.8.8.8',port=True)],
            [dict(ip='127.0.0.1',port=80)],
            [dict(ip='2606:4700:0:0:0:0:0:1111',port=80)],
        ):
            with self.subTest(endpoints=endpoints):
                self.obj['endpoints']=endpoints
                raw,sig=self.pack()
                with self.assertRaises(ValueError):verify_offer(raw,sig,self.key,100100)

    def test_unsupported_format_and_noncanonical_json_refused(self):
        raw,sig=self.pack()
        with self.assertRaises(ValueError):verify_offer(raw+b' ',sig,self.key,100100)
        self.obj['version']=True
        raw,sig=self.pack()
        with self.assertRaises(ValueError):verify_offer(raw,sig,self.key,100100)

if __name__=='__main__':
    unittest.main()
