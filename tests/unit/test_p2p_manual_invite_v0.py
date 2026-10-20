#!/usr/bin/env python3
"""Offline contact-code conformance. No network or guest-harness dependency."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/p2p/manual_invite_v0.py"
spec = importlib.util.spec_from_file_location("ur_manual_invite_v0", MODULE_PATH)
assert spec is not None and spec.loader is not None
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)


def sample(*, with_reply=False):
    value = {
        "v": 0, "peer_key": "01" * 32, "nonce": "02" * 16,
        "valid_from": 1_700_000_000, "valid_until": 1_700_000_600,
        "sim_sha256": "03" * 32,
        "endpoints": [
            {"ip": "192.0.2.10", "port": 7777, "transport": "udp"},
            {"ip": "2001:db8::7", "port": 7778, "transport": "udp"},
        ],
    }
    if with_reply:
        value["recipient_key"] = "04" * 32
        value["reply_to"] = "05" * 16
    return value


def independently_framed(payload: bytes) -> str:
    # Deliberately independent envelope fixture constructor. The protocol's
    # checksum is NOT a signature; malicious changes can be rechecksummed.
    b64 = lambda data: base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")
    tag = hashlib.sha256(
        b"UR-RECOMP-OFFLINE-UNTRUSTED-CONTACT-V0\x00" + payload).digest()[:12]
    return "URP0." + b64(payload) + "." + b64(tag)


class OfflinePeerInviteTests(unittest.TestCase):
    def test_canonical_roundtrip_and_manual_deep_link(self):
        data = sample()
        code = inv.make_code(data, now=1_700_000_001)
        self.assertTrue(code.startswith("URP0."))
        self.assertEqual(inv.read_code(code, now=1_700_000_599), data)
        self.assertEqual(inv.read_code(inv.make_link(code)), data)
        self.assertEqual(inv.read_code("  " + code + "\n"), data)
        self.assertEqual(inv.make_code(inv.read_code(code)), code)

    def test_frozen_golden_vector(self):
        # Do not derive expected bytes from the production encoder.
        fixture = json.loads((ROOT / "tests/data/p2p-urp0-v0-golden.json")
                             .read_text(encoding="utf-8"))
        self.assertEqual(fixture["format"], "UNTRUSTED_OFFLINE_URP0")
        self.assertEqual(fixture["payload"], sample())
        self.assertEqual(inv.make_code(sample()), fixture["code"])
        self.assertEqual(inv.read_code(fixture["code"]), fixture["payload"])
        raw = json.dumps(sample(), sort_keys=True, separators=(",", ":")
                         ).encode("ascii")
        self.assertEqual(hashlib.sha256(
            b"UR-RECOMP-OFFLINE-UNTRUSTED-CONTACT-V0\x00" + raw
        ).digest()[:12].hex(), fixture["checksum_hex"])

    def test_independent_canonical_json_framing(self):
        raw = json.dumps(sample(), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True).encode("ascii")
        self.assertEqual(inv.make_code(sample()), independently_framed(raw))
        self.assertEqual(inv.read_code(independently_framed(raw)), sample())

    def test_expiration_and_non_authenticity(self):
        code = inv.make_code(sample())
        self.assertEqual(inv.read_code(code), sample())
        for now in (1_699_999_999, 1_700_000_600):
            with self.assertRaises(inv.InviteError):
                inv.read_code(code, now=now)
        # Checksums detect accidental corruption but anybody can recalculate
        # them. A different valid public-key claim cannot identify the sender.
        spoofed = sample()
        spoofed["peer_key"] = "ab" * 32
        self.assertEqual(inv.read_code(inv.make_code(spoofed)), spoofed)
        self.assertNotEqual(inv.make_code(spoofed), code)

    def test_two_way_reply_in_no_discovery_condition(self):
        offer = sample()
        incoming = inv.read_code(inv.make_link(inv.make_code(offer)),
                                 now=1_700_000_002)
        reply = sample(with_reply=True)
        reply["peer_key"] = "04" * 32
        reply["recipient_key"] = incoming["peer_key"]
        reply["reply_to"] = incoming["nonce"]
        reply["nonce"] = "05" * 16
        reply["endpoints"] = [
            inv.parse_endpoint("udp@[2001:db8::8]:9000")]
        returned = inv.read_code(inv.make_code(reply), now=1_700_000_003)
        self.assertEqual(returned["reply_to"], offer["nonce"])
        self.assertEqual(returned["recipient_key"], offer["peer_key"])
        self.assertNotIn("example.com", str(returned))

    def test_invalid_endpoints_and_untrusted_fields_fail_closed(self):
        good = sample()
        for endpoint in [
            {"ip": "peer.example", "port": 7000, "transport": "udp"},
            {"ip": "ff02::1", "port": 7000, "transport": "udp"},
            {"ip": "0.0.0.0", "port": 7000, "transport": "udp"},
            {"ip": "2001:DB8::7", "port": 7000, "transport": "udp"},
            {"ip": "fe80::1%eth0", "port": 7000, "transport": "udp"},
            {"ip": "192.0.2.1", "port": 0, "transport": "udp"},
            {"ip": "192.0.2.1", "port": 65536, "transport": "udp"},
            {"ip": "192.0.2.1", "port": True, "transport": "udp"},
            {"ip": "192.0.2.1", "port": 2, "transport": "tcp"},
        ]:
            candidate = dict(good, endpoints=[endpoint])
            with self.subTest(endpoint=endpoint), self.assertRaises(inv.InviteError):
                inv.make_code(candidate)
        for mutation in [
            {"v": 1}, {"v": True}, {"nonce": "0" * 32},
            {"peer_key": "AA" * 32}, {"sim_sha256": "g" * 64},
            {"valid_from": -1}, {"valid_until": good["valid_from"]},
            {"valid_until": good["valid_from"] + 86_401},
            {"recipient_key": "0" * 64}, {"reply_to": "x" * 32},
            {"extra": "remote-code-to-execute"}, {"endpoints": []},
            {"endpoints": good["endpoints"] * 5},
            {"endpoints": good["endpoints"] * 2},
        ]:
            with self.subTest(mutation=mutation), self.assertRaises(inv.InviteError):
                inv.make_code(dict(good, **mutation))
        self.assertEqual(
            inv.parse_endpoint("udp@198.51.100.7:7777"),
            {"ip": "198.51.100.7", "port": 7777, "transport": "udp"})
        for malformed in ["tcp@127.0.0.1:8000", "udp@2001:db8::1:8000",
                          "udp@localhost:8000", "udp@[::1]", "udp@a:0",
                          "udp@[::1]:-1", "udp@192.0.2.1:" + "9" * 9000,
                          "udp@192.0.2.1:٣"]:
            with self.assertRaises(inv.InviteError):
                inv.parse_endpoint(malformed)

    def test_reject_forged_json_rechecksummed_and_noncanonical_encoding(self):
        code = inv.make_code(sample())
        malformed = [
            code + ".", code + "/extra", code + "?join=1",
            code.replace("URP0.", "URP1.", 1),
            "ur-recomp://evil/" + code,
            "URP0.bad.bad", "URP0.", "URP0." + "A" * 4096,
            " " * 100000 + code,
            code[:-1] + ("A" if code[-1] != "A" else "B"),
        ]
        for text in malformed:
            with self.subTest(code=text[:50]), self.assertRaises(inv.InviteError):
                inv.read_code(text)
        # Even a correctly rechecksummed modified payload is not accepted if
        # JSON keys/order, duplicated keys, or unknown fields are wrong.
        base = json.dumps(sample(), sort_keys=True, separators=(",", ":"))
        payloads = [
            json.dumps(sample()).encode(),
            base.replace('"v":0', '"v":0,"v":0').encode(),
            base.replace('"v":0', '"v":0,"unknown":1').encode(),
            b'{"v":NaN}',
            # Huge exponents can decode to infinity; reject with InviteError.
            base.replace('"valid_until":1700000600', '"valid_until":1e999').encode(),
        ]
        for raw in payloads:
            with self.subTest(payload=raw[:45]), self.assertRaises(inv.InviteError):
                inv.read_code(independently_framed(raw))
        # Corrupted/truncated payload and checksum cannot crash the parser.
        rng = random.Random(117)
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789_-.!+"
        for _ in range(250):
            text = code[:rng.randrange(len(code))] + rng.choice(alphabet)
            try:
                inv.read_code(text)
            except inv.InviteError:
                pass

    def test_cli_requires_explicit_ip_disclosure_and_remains_offline(self):
        command = [
            sys.executable, str(MODULE_PATH), "create",
            "--peer-key", "01" * 32, "--nonce", "02" * 16,
            "--sim-sha256", "03" * 32,
            "--valid-from", "1700000000", "--valid-until", "1700000600",
            "--endpoint", "udp@192.0.2.10:7777",
        ]
        denied = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(denied.returncode, 2)
        self.assertIn("address", denied.stderr)
        made = subprocess.run(command + ["--acknowledge-address-disclosure"],
                              text=True, capture_output=True)
        self.assertEqual(made.returncode, 0, made.stderr)
        linked = subprocess.run(
            command + ["--acknowledge-address-disclosure", "--link"],
            text=True, capture_output=True)
        self.assertEqual(linked.returncode, 0, linked.stderr)
        self.assertEqual(linked.stdout.strip(),
                         inv.make_link(made.stdout.strip()))
        inspected = subprocess.run(
            [sys.executable, str(MODULE_PATH), "inspect", linked.stdout.strip(),
             "--at", "1700000001"], text=True, capture_output=True)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        self.assertEqual(json.loads(inspected.stdout)["trust"],
                         "UNAUTHENTICATED_OFFLINE_RESEARCH_ONLY")
        expired = subprocess.run(
            [sys.executable, str(MODULE_PATH), "inspect", made.stdout.strip()],
            text=True, capture_output=True)
        self.assertEqual(expired.returncode, 2)
        self.assertIn("not presently valid", expired.stderr)


if __name__ == "__main__":
    unittest.main()
