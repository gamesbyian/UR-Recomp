"""ROM-free ART-4K source GLB mesh-topology compatibility tests."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[2]/"tools/art/audit_art4k_real_pose_topology.py"
spec=importlib.util.spec_from_file_location("art4k_pose_topology",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture():
    material_names=[
        f"{part}__material_{i}"
        for part,count in mod.MATERIAL_COUNTS.items()
        for i in range(count)
    ]
    result={}
    for pose in mod.SOURCE_GLB_SHA:
        table={}
        for name in material_names:
            table[name]={
                "vertex_count":12,
                "face_count":8,
                "vertex_bytes_sha256":"a"*64,
                "face_indices_sha256":"b"*64,
                "world_transform_sha256":"c"*64,
            }
        result[pose]=table
    return result


class SourceGLBTopologyTests(unittest.TestCase):
    def test_five_uniform_meshes_have_stable_necessary_topology(self):
        data=mod.compare_mesh_pose_tables(fixture())
        self.assertEqual(data["source_material_mesh_count"],16)
        self.assertEqual(data["source_parent_parts"],5)
        self.assertEqual(data["all_five_vertex_counts_stable_meshes"],16)
        self.assertEqual(data["all_five_face_index_arrays_stable_meshes"],16)
        self.assertTrue(data["all_material_meshes_meet_necessary_topology_conditions"])
        self.assertFalse(data["all_material_meshes_safe_for_naive_glb_vertex_morph"])
        self.assertTrue(all(m["direct_vertex_index_blending_requires_authored_correspondence"]
                            for m in data["material_meshes"]))
        self.assertFalse(data["matched_3d_semantic_vertex_correspondence_proven"])

    def test_equal_counts_and_faces_do_not_prove_vertex_correspondence(self):
        poses=fixture()
        poses["wheelie"]["fork_and_frame__material_0"]["vertex_bytes_sha256"]="f"*64
        data=mod.compare_mesh_pose_tables(poses)
        self.assertEqual(data["all_five_vertex_counts_stable_meshes"],16)
        self.assertEqual(data["all_five_face_index_arrays_stable_meshes"],16)
        self.assertEqual(data["all_five_local_positions_identical_meshes"],15)
        self.assertTrue(data["all_material_meshes_meet_necessary_topology_conditions"])
        self.assertFalse(data["all_material_meshes_safe_for_naive_glb_vertex_morph"])
        mesh=next(m for m in data["material_meshes"]
                  if m["material_mesh_name"]=="fork_and_frame__material_0")
        self.assertTrue(mesh["necessary_topology_conditions_met"])
        self.assertTrue(mesh["direct_vertex_index_blending_requires_authored_correspondence"])
        self.assertFalse(data["matched_3d_semantic_vertex_correspondence_proven"])

    def test_one_pose_changes_face_order_and_vertex_count(self):
        poses=fixture()
        poses["pedal"]["pedals__material_0"]["vertex_count"]=13
        poses["stunt"]["saddle__material_0"]["face_indices_sha256"]="d"*64
        poses["wheelie"]["fork_and_frame__material_0"]["vertex_bytes_sha256"]="f"*64
        poses["bank"]["tire__material_0"]["world_transform_sha256"]="e"*64
        data=mod.compare_mesh_pose_tables(poses)
        self.assertEqual(data["all_five_vertex_counts_stable_meshes"],15)
        self.assertEqual(data["all_five_face_index_arrays_stable_meshes"],15)
        self.assertEqual(data["all_five_local_positions_identical_meshes"],15)
        self.assertEqual(data["all_five_world_matrices_identical_meshes"],15)
        self.assertFalse(data["all_material_meshes_meet_necessary_topology_conditions"])
        self.assertFalse(data["all_material_meshes_safe_for_naive_glb_vertex_morph"])
        self.assertFalse(data["1994_original_pose_or_camera_identified"])

    def test_forged_mesh_and_missing_pose_fail_closed(self):
        poses=fixture();del poses["bank"]
        with self.assertRaisesRegex(ValueError,"five"):
            mod.compare_mesh_pose_tables(poses)
        poses=fixture();del poses["wheelie"]["tire__material_0"]
        with self.assertRaisesRegex(ValueError,"source part"):
            mod.compare_mesh_pose_tables(poses)
        poses=fixture()
        poses["stunt"]["tire__material_0"]["face_count"]=0
        with self.assertRaisesRegex(ValueError,"geometry"):
            mod.compare_mesh_pose_tables(poses)

    def test_exact_five_model_sha_distinct(self):
        self.assertEqual(len(set(mod.SOURCE_GLB_SHA.values())),5)
        self.assertEqual(set(mod.MATERIAL_COUNTS),
                         {"tire","rim_and_hub","fork_and_frame","pedals","saddle"})
        self.assertEqual(sum(mod.MATERIAL_COUNTS.values()),16)
        self.assertTrue(all(len(v)==64 for v in mod.SOURCE_GLB_SHA.values()))


if __name__=="__main__":
    unittest.main()
