"""H25 recovered P2P IPv4-mapped IPv6 alias negatives on the signed offer parser.

Offline, source-exact candidate parsing only. No sockets, verified endpoint
reachability, session replay storage, or multiplayer shipping claim.
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


class IPv4MappedSignedRendezvousRegression(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        self.record = {
            'version': 1, 'session': 'a1' * 16,
            'nonce': 'b2' * 16, 'inviter_key': self.public.hex(),
            'issued': 100000, 'expires': 100300, 'scope': 'public',
            'endpoints': [{'ip': '8.8.8.8', 'port': 5678}],
        }

    def verify(self, address, scope):
        self.record['scope'] = scope
        self.record['endpoints'] = [{'ip': address, 'port': 5678}]
        raw = json.dumps(self.record, sort_keys=True, separators=(',', ':')).encode()
        return verify_offer(raw, self.key.sign(DOMAIN + raw),
                            self.public, 100100)

    def test_public_mapped_ipv4_rejected_even_with_correct_signature(self):
        # This canonical Python ipaddress spelling passes is_global, but it
        # aliases an IPv4 address already representable by a v4 candidate.
        with self.assertRaisesRegex(ValueError, 'mapped'):
            self.verify('::ffff:8.8.8.8', 'public')

    def test_lan_and_loopback_mapped_aliases_rejected(self):
        for address in ('::ffff:192.168.1.2', '::ffff:127.0.0.1'):
            with self.subTest(address=address):
                with self.assertRaisesRegex(ValueError, 'mapped'):
                    self.verify(address, 'lan')

    def test_genuine_ip_versions_stay_usable(self):
        for address, scope in (
                ('8.8.8.8', 'public'),
                ('192.168.1.2', 'lan'),
                ('2606:4700::1111', 'public')):
            with self.subTest(address=address):
                self.assertEqual(self.verify(address, scope)['candidates'],
                                 ((address, 5678),))


if __name__ == '__main__':
    unittest.main()
