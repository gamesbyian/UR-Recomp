"""ROM-free guards for unmodified Pages-site GLB evidence intake."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.art.audit_real_viewer_glbs import (
    POSES, inspect_viewer, safe_existing_path,
)
from tools.art.build_racer_source_pixel_corpus import STRIP


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ViewerModelArtifactAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        (self.site/"sprites").mkdir()
        (self.site/"assets").mkdir()
        from tools.art.build_racer_source_pixel_corpus import build as corpus_build
        corpus = corpus_build()
        self.sprite = self.site/"sprites/p1-00.png"
        self.references = []
        originals = {}
        for row in corpus["observations"]:
            source = STRIP/"stock"/Path(row["source_image"]).name
            destination = self.site/"sprites"/source.name
            if not destination.exists():
                shutil.copyfile(source, destination)
            self.references.append({
                "player": row["player"], "guest_frame": row["guest_frame"],
                "sha256": row["png_file_sha256"],
                "representation_id": row["representation_id"],
                "image": "sprites/" + source.name,
            })
        self.rom_sha = corpus["historical_manifest_declared_rom_sha256"]
        poses = {}
        for pose in POSES:
            path = self.site/"assets"/(pose+".glb")
            path.write_bytes(b"glTF synthetic fixture " + pose.encode())
            poses[pose] = {"url": "assets/"+pose+".glb", "sha256": sha(path)}
        self.model = {
            "schema": "ur-racer-model-review/1",
            "source_commit": "a"*40, "source_model_sha256": "b"*64,
            "likeness_approved": False,
            "source_sprite_pose_registration": False,
            "model_url": poses["upright"]["url"],
            "candidate_sha256": poses["upright"]["sha256"],
            "poses": poses,
        }
        self.sprites = {
            "schema": "ur-racer-original-sprite-reference/1",
            "source_sha256": self.rom_sha,
            "sprite_3d_pose_mapping_verified": False,
            "frames": self.references,
        }
        self.save()

    def save(self):
        (self.site/"manifest.json").write_text(json.dumps(self.model))
        (self.site/"sprites.json").write_text(json.dumps(self.sprites))

    def test_untampered_five_pose_site_metadata_accepted(self):
        m, src, pose_files = inspect_viewer(self.site)
        self.assertEqual(m["candidate_sha256"], m["poses"]["upright"]["sha256"])
        self.assertEqual(src["sha256"], sha(self.sprite))
        self.assertEqual(set(pose_files), set(POSES))

    def test_model_hash_tamper_rejected(self):
        (self.site/"assets/bank.glb").write_bytes(b"glTF altered")
        with self.assertRaisesRegex(ValueError, "GLB SHA"):
            inspect_viewer(self.site)

    def test_duplicate_or_missing_source_frame_rejected(self):
        self.sprites["frames"].append(dict(self.sprites["frames"][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, "exactly 32"):
            inspect_viewer(self.site)
        self.sprites["frames"] = []
        self.save()
        with self.assertRaisesRegex(ValueError, "exactly 32"):
            inspect_viewer(self.site)

    def test_viewer_approval_or_invented_pose_mapping_rejected(self):
        for key in ("likeness_approved", "source_sprite_pose_registration"):
            self.model[key] = True
            self.save()
            with self.assertRaisesRegex(ValueError, "misleading"):
                inspect_viewer(self.site)
            self.model[key] = False
        self.sprites["sprite_3d_pose_mapping_verified"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "unverified"):
            inspect_viewer(self.site)

    def test_default_pose_must_be_sha_bound_upright(self):
        self.model["candidate_sha256"] = "0"*64
        self.save()
        with self.assertRaisesRegex(ValueError, "default"):
            inspect_viewer(self.site)

    def test_path_escape_and_wrong_file_type_rejected(self):
        for item in ("../somewhere.glb", "/etc/passwd", "assets\\bank.glb",
                     "assets/bank.png"):
            with self.subTest(path=item), self.assertRaises(ValueError):
                safe_existing_path(self.site, item, ".glb")

    def test_sprite_sha_tamper_and_source_resolution_rejected(self):
        self.sprite.write_bytes(self.sprite.read_bytes()+b"altered")
        with self.assertRaisesRegex(ValueError, "original sprite SHA"):
            inspect_viewer(self.site)
        self.sprites["frames"][0]["sha256"] = "0"*64
        self.save()
        with self.assertRaisesRegex(ValueError, "original-source authenticated"):
            inspect_viewer(self.site)

    def test_self_consistent_forged_original_sprite_is_rejected(self):
        # A website can lie consistently about a replaced image and its SHA.
        # The independent ROM-composed corpus must be authoritative instead.
        modified = self.sprite.read_bytes() + b"new untrusted source"
        self.sprite.write_bytes(modified)
        for row in self.sprites["frames"]:
            if row["image"] == "sprites/p1-00.png":
                row["sha256"] = sha(self.sprite)
        self.save()
        with self.assertRaisesRegex(ValueError, "original-source authenticated"):
            inspect_viewer(self.site)

    def test_source_rom_identity_cannot_be_spoofed(self):
        self.sprites["source_sha256"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "source ROM identity"):
            inspect_viewer(self.site)

    def test_missing_expected_pose_is_not_silent(self):
        self.model["poses"].pop("wheelie")
        self.save()
        with self.assertRaisesRegex(ValueError, "five experimental"):
            inspect_viewer(self.site)


if __name__ == "__main__":
    unittest.main()
