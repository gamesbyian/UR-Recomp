#!/usr/bin/env python3
"""One exact-source 2026 GLB near-side hub cover, not a recovered 1994 part."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.art.experimental_oblique_hub_cover import (
    CURRENT_2026_SOURCE_GLB_SHA256,SOURCE_MATERIAL,
    ORIGINAL_SOURCE_VERTEX_COUNT,ORIGINAL_SOURCE_FACE_COUNT,
    NEW_HUB_COVER_VERTICES,NEW_HUB_COVER_FACES,
    temporary_hub_cover_volume,
)
from tools.art.no_replace_report import publish_text_once

SCHEMA="UR-ART4K-EXPERIMENTAL-2026-PRINTED-HUB-COVER-VOLUME/1"
PDF_SHA="50d5d02a3f8f04b9a38a1dac7ff05fd96f5583fbdf1d0afc201bbaea454e2235"
P15_SOURCE_CROP_SHA="4c9242a0126891a2d6a6e8f574eec4179c4cdbcd30cb34a1cdff8589e9290d22"
P15_VISIBLE_DARK_FACE_AREA_PX2=35973.5


def analyze(source_glb:Path,preview_glb:Path|None=None):
    import numpy as np
    import trimesh
    raw=source_glb.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CURRENT_2026_SOURCE_GLB_SHA256:
        raise ValueError("exact single existing 2026 source five-parent upright GLB required")
    scene=trimesh.load(source_glb,force="scene",process=False)
    if not isinstance(scene,trimesh.Scene) or len(scene.geometry)!=16:
        raise ValueError("authored five-parent 2026 source GLB required")
    original={n:(np.asarray(m.vertices).copy(),np.asarray(m.faces).copy(),
                 np.asarray(m.visual.vertex_colors).copy())
              for n,m in scene.geometry.items()}
    mesh=scene.geometry[SOURCE_MATERIAL]
    old_volume=float(mesh.volume)
    before_nodes=set(scene.graph.nodes)
    with temporary_hub_cover_volume(scene):
        difference=np.asarray(mesh.vertices)[ORIGINAL_SOURCE_VERTEX_COUNT:]
        new_volume=float(mesh.volume)
        if (difference.shape!=(NEW_HUB_COVER_VERTICES,3)
                or not mesh.is_watertight or new_volume<=old_volume):
            raise ValueError("new model-only 2026 hub cover isn't a closed 3D candidate")
        components=len(mesh.split(only_watertight=False))
        if components!=2:
            raise ValueError("prototype is expected to have two distinct closed solids")
        if preview_glb is not None:
            if preview_glb.exists():
                raise ValueError("never overwrite existing experimental GLB")
            preview_glb.write_bytes(scene.export(file_type="glb"))
    if (set(scene.graph.nodes)!=before_nodes or
            any(not np.array_equal(scene.geometry[k].vertices,v[0])
                    or not np.array_equal(scene.geometry[k].faces,v[1])
                    or not np.array_equal(scene.geometry[k].visual.vertex_colors,v[2])
                    for k,v in original.items())):
        raise ValueError("2026 source original GLB not restored after hub proposal")
    return {
        "schema":SCHEMA,
        "original_2026_source_upright_glb_sha256":CURRENT_2026_SOURCE_GLB_SHA256,
        "source_original_print_manual_pdf_sha256":PDF_SHA,
        "source_original_print_p15_crop_png_sha256":P15_SOURCE_CROP_SHA,
        "source_original_print_visible_hub_face_2d_area_scan_px2":P15_VISIBLE_DARK_FACE_AREA_PX2,
        "same_1994_model_or_artist_camera_proven":False,
        "source_glb_five_parent_16_material_mesh_structure_preserved":True,
        "source_mesh_modified":SOURCE_MATERIAL,
        "source_original_dark_hub_vertices":ORIGINAL_SOURCE_VERTEX_COUNT,
        "source_original_dark_hub_triangles":ORIGINAL_SOURCE_FACE_COUNT,
        "new_cover_vertices":NEW_HUB_COVER_VERTICES,
        "new_cover_triangles":NEW_HUB_COVER_FACES,
        "new_total_dark_hub_material_vertices":len(original[SOURCE_MATERIAL][0])+NEW_HUB_COVER_VERTICES,
        "new_total_dark_hub_material_triangles":len(original[SOURCE_MATERIAL][1])+NEW_HUB_COVER_FACES,
        "source_dark_hub_material_original_volume_2026_units3":round(old_volume,9),
        "source_dark_hub_material_proposed_volume_2026_units3":round(new_volume,9),
        "source_dark_hub_material_volume_change_percent":round((new_volume/old_volume-1)*100,6),
        "prototype_closed_components_in_one_material":components,
        "prototype_is_boolean_fused_single_manifold":False,
        "source_original_2026_glb_restored_exactly":True,
        "original_1994_physical_hub_width_depth_or_shape_recovered":False,
        "original_1994_material_identity_recovered":False,
        "owner_character_likeness_approved":False,
        "shipping_art_approved":False,
        "notes":"One deliberately provisional 2026 source-model dark near-side hub cover shell, motivated only by an exposed 2D dark casing patch in the original 1994 printed manual p15. Dimensions are not a recovered original historical 3D mesh, and its two closed solids are intentionally not a final CSG union.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upright-glb",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--preview-glb",type=Path)
    args=p.parse_args()
    output=analyze(args.upright_glb,args.preview_glb)
    text=json.dumps(output,sort_keys=True,indent=2)+"\n"
    if args.out:
        publish_text_once(args.out,text)
    print(text,end="")


if __name__=="__main__":
    main()
