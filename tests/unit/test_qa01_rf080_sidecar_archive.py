"""ROM-free adversarial tests for the independent RF080 event-only source."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf080_sidecar_archive as audit

class RF080NativeSidecarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A valid-sized *synthetic* source stream exercises the exact-count
        # gate without importing a copyrighted ROM, compiled guest or video.
        seq=0
        out=[]
        groups=[
            ("opcode",45103,"guestPC=82D4EE tier=aot"),
            ("read",2705,"addr=01ED value=0026"),
            ("bit_real_return",6483,"guestPC=82D4EE D=0000 addr=0057 value=00"),
            ("bpl_actual_input",6483,"guestPC=82D4F0 D=0000 N=0 bitReadSeen=1")
        ]+[(name,9,"resume=82D4EE") for name in
            ("entry","resume_origin","after_push","compiled_rti","handler_return")]
        for stage,count,rest in groups:
            for _ in range(count):
                seq+=1
                out.append(f"QA01RF047NATIVE seq={seq} stage={stage} f=1017 {rest}")
        assert seq==60819
        cls.valid=("\n".join(out)+"\n").encode()

    def checked(self,raw):
        with mock.patch.object(audit,"SIDECAR_SHA",hashlib.sha256(raw).hexdigest()):
            return audit.qualify_sidecar(raw)

    def test_synthetic_strict_event_population_accepted_as_stream_only(self):
        lines,rows,stages=self.checked(self.valid)
        self.assertEqual(len(lines),60819)
        self.assertEqual(len(rows),60819)
        self.assertEqual(stages["bit_real_return"],6483)

    def test_noncontiguous_source_local_ordinal_refused_even_if_rehashed(self):
        bad=self.valid.replace(b"seq=2 ",b"seq=7 ",1)
        with self.assertRaisesRegex(ValueError,"noncontiguous"):
            self.checked(bad)

    def test_interleaved_partial_logger_line_refused_even_if_rehashed(self):
        bad=b"QA01RF044NATIVE partial "+self.valid
        with self.assertRaisesRegex(ValueError,"non-isolated"):
            self.checked(bad)

    def test_missing_actual_BIT_read_refused_even_if_rehashed(self):
        bad=self.valid.replace(b"stage=bit_real_return",
                               b"stage=opcode",1)
        with self.assertRaisesRegex(ValueError,"count changed"):
            self.checked(bad)

    def test_wrong_actual_direct_page_read_refused_even_if_rehashed(self):
        bad=self.valid.replace(b"addr=0057 value=00",b"addr=0059 value=00",1)
        with self.assertRaisesRegex(ValueError,"unqualified native paced BIT return"):
            self.checked(bad)

    def test_missing_or_wrong_immutable_sidecar_digest_refused(self):
        with self.assertRaisesRegex(ValueError,"SHA256"):
            audit.qualify_sidecar(self.valid)

if __name__=="__main__":
    unittest.main()
