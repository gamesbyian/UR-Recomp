"""Reject glTF extension semantics before a base-only Trimesh GLB comparison."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import types
from unittest import mock
import struct
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / 'tools/art/glb_roundtrip_guard.py'
spec = importlib.util.spec_from_file_location('glb_roundtrip_guard', GUARD)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_glb(gltf: dict) -> bytes:
    payload = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    payload += b' ' * ((-len(payload)) % 4)
    binary = b'\0' * 72
    total = 12 + 8 + len(payload) + 8 + len(binary)
    return (struct.pack('<4sII', b'glTF', 2, total)
            + struct.pack('<II', len(payload), 0x4E4F534A) + payload
            + struct.pack('<II', len(binary), 0x004E4942) + binary)


class GLBExtensionSafetyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'candidate.glb'
        self.gltf = {
            'asset': {'version': '2.0'},
            'meshes': [{'name': 'tire__material_0',
                        'primitives': [{'attributes': {'NORMAL': 0, 'POSITION': 1}}]}],
            'accessors': [
                {'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3'},
                {'bufferView': 0, 'componentType': 5126, 'count': 3, 'type': 'VEC3'},
            ],
            'bufferViews': [{'buffer': 0, 'byteLength': 72}],
            'buffers': [{'byteLength': 72}],
            'nodes': [{'name': 'tire__material_0', 'mesh': 0}],
        }

    def validate(self, gltf):
        self.path.write_bytes(make_glb(gltf))
        module.require_explicit_glb_normals(self.path, {'tire__material_0'})

    def test_unextended_dense_normal_glb_still_passes(self):
        self.validate(self.gltf)

    def test_declared_extension_lists_rejected_even_when_no_node_declares_it(self):
        for key in ('extensionsUsed', 'extensionsRequired'):
            with self.subTest(key=key):
                altered = copy.deepcopy(self.gltf)
                altered[key] = ['EXT_mesh_gpu_instancing']
                with self.assertRaisesRegex(ValueError, 'NORMAL accessor') as ctx:
                    self.validate(altered)
                self.assertIn('extensions unsupported', str(ctx.exception.__cause__))

    def test_nested_extension_payloads_rejected_without_top_level_declarations(self):
        paths = (
            ('node', lambda x: x['nodes'][0]),
            ('primitive', lambda x: x['meshes'][0]['primitives'][0]),
            ('accessor', lambda x: x['accessors'][0]),
            ('asset', lambda x: x['asset']),
        )
        for name, target in paths:
            with self.subTest(where=name):
                altered = copy.deepcopy(self.gltf)
                target(altered)['extensions'] = {'EXT_mesh_gpu_instancing': {}}
                with self.assertRaisesRegex(ValueError, 'NORMAL accessor') as ctx:
                    self.validate(altered)
                self.assertIn('extensions unsupported', str(ctx.exception.__cause__))

    def test_extension_refused_before_trimesh_scene_load(self):
        # An extension-aware viewer could draw additional geometry. Reject it
        # before the base-only importer ever interprets the candidate.
        altered = copy.deepcopy(self.gltf)
        altered['extensionsUsed'] = ['EXT_mesh_gpu_instancing']
        altered['extensionsRequired'] = ['EXT_mesh_gpu_instancing']
        altered['nodes'][0]['extensions'] = {
            'EXT_mesh_gpu_instancing': {'attributes': {'TRANSLATION': 0}}}
        self.path.write_bytes(make_glb(altered))
        report = {'components': [
            {'name': f'part{i}', 'material_count': 1,
             'materials': [{'node': f'part{i}__material_0'}]}
            for i in range(5)]}
        fake_trimesh = types.ModuleType('trimesh')
        fake_trimesh.load = mock.Mock(
            side_effect=AssertionError('Trimesh loader must not run'))
        with mock.patch.dict(sys.modules, {
            'numpy': types.ModuleType('numpy'), 'trimesh': fake_trimesh
        }):
            with self.assertRaisesRegex(ValueError, 'NORMAL accessor') as caught:
                module.validate_glb_roundtrip(self.path, report)
        self.assertIn('extensions unsupported', str(caught.exception.__cause__))
        fake_trimesh.load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
