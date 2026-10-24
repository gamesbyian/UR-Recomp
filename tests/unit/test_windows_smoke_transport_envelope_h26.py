"""Bounded Windows Actions transport ZIP envelope regression.

First-party research lead: H26 Evidence archive Drive
142bXAi_4D-928Wz7FntyRbVzTYvt_sJZ, nested
evidence/agent2-h25.zip -> evidence/agent2-h24.zip ->
prior-bundles/20261020T23-agent2-five-line-recovery.zip ->
evidence/agent2-h22-recovery.zip -> evidence/agent2-h17.zip ->
qa04_zip_preflight.py, SHA-256
28728223fadf9fc7cb2debd60e3a909ae1946220901b0501af1e96c5960a71e2.

Synthetic wrapper bytes only. These assertions do not qualify original ROM
material, a Windows executable, gameplay, or an actual GitHub run artifact.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools import audit_windows_smoke_artifact as audit


def wrapper(*, comment=b""):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(audit.PORTABLE_MEMBERS):
            archive.writestr(name, b"synthetic content")
        archive.comment = comment
    return data.getvalue()


def unrelated():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("undisclosed.txt", b"unindexed local ZIP member")
    return data.getvalue()


class WindowsSmokeTransportEnvelopeTests(unittest.TestCase):
    def check(self, raw, *, accepted):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "transport.zip"
            target.write_bytes(raw)
            if accepted:
                with audit._open_transport(target, exactly=audit.PORTABLE_MEMBERS) as archive:
                    self.assertEqual(set(archive.namelist()), audit.PORTABLE_MEMBERS)
                return
            with self.assertRaisesRegex(ValueError, "noncanonical transport ZIP"):
                with audit._open_transport(target, exactly=audit.PORTABLE_MEMBERS):
                    self.fail("unqualified wrapper was admitted")

    def test_plain_expected_wrapper_still_passes(self):
        self.check(wrapper(), accepted=True)

    def test_self_extracting_prefix_rejected(self):
        # zipfile accepts this SFX-like envelope and reports only normal entries.
        self.check(b"MZ" + bytes(32) + wrapper(), accepted=False)

    def test_unindexed_local_zip_prelude_rejected(self):
        # A whole preceding ZIP is not included by namelist() for the
        # trailing ZIP's central directory, despite the PK local-file magic.
        self.check(unrelated() + wrapper(), accepted=False)

    def test_unindexed_local_record_inserted_before_central_directory(self):
        canonical = wrapper()
        hidden = unrelated()
        with zipfile.ZipFile(io.BytesIO(canonical)) as z:
            offset = z.start_dir
        with zipfile.ZipFile(io.BytesIO(hidden)) as z:
            extra_local = hidden[:z.start_dir]
        altered = bytearray(canonical[:offset] + extra_local + canonical[offset:])
        # EOCD central-directory offset must be adjusted so zipfile sees
        # exactly the same three official entries, not the unindexed one.
        struct.pack_into("<I", altered, len(altered) - 22 + 16,
                         offset + len(extra_local))
        with zipfile.ZipFile(io.BytesIO(altered)) as z:
            self.assertEqual(set(z.namelist()), audit.PORTABLE_MEMBERS)
        self.check(bytes(altered), accepted=False)

    def test_trailing_opaque_bytes_rejected(self):
        self.check(wrapper() + b"hidden trailer", accepted=False)

    def test_archive_comment_rejected(self):
        self.check(wrapper(comment=b"opaque comment"), accepted=False)


if __name__ == "__main__":
    unittest.main()
