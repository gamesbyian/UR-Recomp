from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_network_trace", ROOT / "tools" / "audit_network_trace.py"
)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditNetworkTraceTests(unittest.TestCase):
    def test_ignores_unix_and_plain_socket_creation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "trace"
            p.write_text(
                'socket(AF_INET, SOCK_STREAM, IPPROTO_TCP) = 3\n'
                'connect(3, {sa_family=AF_UNIX, sun_path="/tmp/x"}, 110) = 0\n',
                encoding="utf-8",
            )
            report = audit.scan([p])
        self.assertEqual(report["inet_attempt_count"], 0)

    def test_reports_ipv4_and_ipv6_connect_send(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "trace"
            p.write_text(
                'connect(3, {sa_family=AF_INET, sin_port=htons(443), sin_addr=inet_addr("1.2.3.4")}, 16) = -1\n'
                'sendto(4, "dns", 3, 0, {sa_family=AF_INET6, sin6_port=htons(53)}, 28) = 3\n',
                encoding="utf-8",
            )
            report = audit.scan([p])
        self.assertEqual(report["inet_attempt_count"], 2)


if __name__ == "__main__":
    unittest.main()
