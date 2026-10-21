"""Portable Win32 packet paths, no physical Windows evidence."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from check_qa04_physical_windows_packets import safe_member

class PortablePackets(unittest.TestCase):
    def test_plain_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"packet"
            (root/"logs").mkdir(parents=True)
            (root/"logs"/"startup.txt").write_text("source")
            self.assertEqual(safe_member(root,"logs/startup.txt"),root/"logs"/"startup.txt")

    @unittest.skipIf(sys.platform.startswith("win"),"Windows cannot create reserved components")
    def test_reserved_member_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"packet"
            root.mkdir()
            for name in ("CON.txt","NUL","COM¹.txt","LPT2.log","trailing. ","e\u0301.txt","a\u202eb.txt"):
                p=root/name
                p.write_bytes(b"x")
                with self.subTest(name=name),self.assertRaisesRegex(ValueError,"QA04_PACKET_REJECTED"):
                    safe_member(root,name)

    @unittest.skipIf(sys.platform.startswith("win"),"Windows cannot create device root")
    def test_reserved_packet_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"CON"
            root.mkdir()
            (root/"good.txt").write_text("x")
            with self.assertRaisesRegex(ValueError,"nonportable Win32"):
                safe_member(root,"good.txt")

    def test_symlinked_attachment_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"packet"
            root.mkdir()
            (root/"good.txt").write_bytes(b"x")
            (root/"bad.txt").symlink_to(root/"good.txt")
            with self.assertRaisesRegex(ValueError,"symlinked"):
                safe_member(root,"bad.txt")

if __name__=="__main__":
    unittest.main()
