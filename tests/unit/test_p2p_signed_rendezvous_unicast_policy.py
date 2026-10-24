"""Recovered H25 supplemental unicast policy for signed rendezvous candidates.

Source: Evidence Library bundle 142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ
(h26.zip -> agent5-h25.zip -> agent4-h25.zip -> prior_p2p/p2p_endpoint_unicast_policy.py).
Offline candidate parsing only: no sockets, reachability, NAT traversal or
multiplayer shipping claim.
"""
import json
from pathlib import Path
import sys
import unittest

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError as exc:
    raise unittest.SkipTest('optional Ed25519 cryptography dependency unavailable') from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools' / 'p2p'))
from direct_rendezvous_offer import DOMAIN, verify_offer


class SignedRendezvousUnicastPolicy(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)

    def verify(self, address, scope):
        record = {
            'version': 1, 'session': 'a1' * 16, 'nonce': 'b2' * 16,
            'inviter_key': self.public.hex(), 'issued': 100000,
            'expires': 100300, 'scope': scope,
            'endpoints': [{'ip': address, 'port': 5678}],
        }
        raw = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
        return verify_offer(raw, self.key.sign(DOMAIN + raw), self.public, 100100)

    def test_lan_scope_refuses_broadcast_reserved_and_link_local(self):
        for address in ('255.255.255.255', '0.1.2.3', '240.0.0.1', 'fe80::1'):
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    self.verify(address, 'lan')

    def test_public_scope_still_refuses_the_same_addresses(self):
        for address in ('255.255.255.255', '0.1.2.3', '240.0.0.1', 'fe80::1',
                        '2001:db8::1'):
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    self.verify(address, 'public')

    def test_genuine_lan_and_public_unicast_stay_usable(self):
        for address, scope in (
                ('192.168.1.2', 'lan'),
                ('10.0.0.5', 'lan'),
                ('100.64.0.1', 'lan'),
                ('fd00::1', 'lan'),
                ('8.8.8.8', 'public'),
                ('2606:4700::1111', 'public')):
            with self.subTest(address=address, scope=scope):
                self.assertEqual(self.verify(address, scope)['candidates'],
                                 ((address, 5678),))


if __name__ == '__main__':
    unittest.main()
