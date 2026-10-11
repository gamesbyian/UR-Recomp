#!/usr/bin/env python3
"""Export the original 1205..1220 pose strip from canonical ROM + authored code.

Intentionally uses the *existing* stock compositor and authored generators.
Any mismatch with the external shipping approval ledger stops export.
No placeholder art, guessed poses, or source gameplay capture is involved.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from prototype_racer_hd_replacement import build_stock_rgba
from build_racer_hd_asset_dossier import authored_candidate_rgba_for_entry, encode_png_rgba

ROM = ROOT / "reference/roms/retail/Uniracers_USA.sfc"
REGISTRY = ROOT / "analysis/data/racer-hd-replacement-prototype.json"
EXPECTED_ROM_SHA256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--player", choices=["p1","p2"], default="p1")
    a = ap.parse_args()
    rom = ROM.read_bytes()
    if sha(rom) != EXPECTED_ROM_SHA256:
        raise ValueError("USA ROM digest mismatch; cannot make authoritative original art")
    registry_bytes = REGISTRY.read_bytes()
    registry = json.loads(registry_bytes)
    by_id = {e["representation_id"]: e for e in registry["entries"]}
    decisions = {}
    ledger_paths = sorted((ROOT/"analysis/data").glob("racer-hd-art-approval*.json"))
    if not ledger_paths:
        raise ValueError("No shipping ledgers found")
    for ledger in ledger_paths:
        j = json.loads(ledger.read_text())
        if j["family_blockers"]:
            continue
        for d in j["decisions"]:
            if d["status"] != "approved" or not d["shipping_art_approved"] or d["blocker_codes"]:
                continue
            rid = d["authored_source_representation_id"]
            item = {"sha256": d["reviewed_authored_rgba_sha256"], "ledger": str(ledger.relative_to(ROOT)),
                    "run": j["review_basis"]["workflow_run"], "artifact": j["review_basis"]["artifact_id"]}
            if rid in decisions and decisions[rid]["sha256"] != item["sha256"]:
                raise ValueError(f"Conflicting shipping approvals for {rid}")
            decisions[rid] = item
    sequence = registry["motion_review_sequence"]
    if [sequence["window_start"],sequence["window_end"]] != [1205,1220]:
        raise ValueError("Unexpected first strip timeline")
    out = a.output.resolve()
    (out / "stock").mkdir(parents=True,exist_ok=True)
    (out / "authored").mkdir(parents=True,exist_ok=True)
    frames = []
    cache = {}
    for row in sequence["frames"]:
        rid = row[a.player+"_representation_id"]
        if rid not in decisions or rid not in by_id:
            raise ValueError(f"Unapproved / unregistered animation pose {rid}")
        if rid not in cache:
            entry = by_id[rid]
            if entry["player"] != a.player:
                raise ValueError("Registry player does not match sequence")
            stock = build_stock_rgba(rom,entry)
            authored, generator, sampler = authored_candidate_rgba_for_entry(entry)
            if len(stock) != 64*64*4 or len(authored) != 256*256*4:
                raise ValueError("Unexpected raster dimensions")
            if sha(authored) != decisions[rid]["sha256"]:
                raise ValueError(f"Approved artwork changed: {rid}")
            if not any(stock[i] for i in range(3,len(stock),4)):
                raise ValueError("Empty stock raster")
            token = f"{a.player}-{len(cache):02d}"
            sfile = out/"stock"/(token+".png")
            afile = out/"authored"/(token+".png")
            sfile.write_bytes(encode_png_rgba(64,64,stock))
            afile.write_bytes(encode_png_rgba(256,256,authored))
            cache[rid] = (sfile,afile,generator,sampler,sha(stock))
        sfile,afile,generator,sampler,stock_sha = cache[rid]
        frames.append({
            "frame":row["frame"],"representation_id":rid,
            "stock_png":str(sfile.relative_to(out)),"authored_png":str(afile.relative_to(out)),
            "stock_source":"Canonical USA ROM "+EXPECTED_ROM_SHA256+"; tools/prototype_racer_hd_replacement.py::build_stock_rgba",
            "stock_evidence":"Exact guarded ROM composition in analysis/data/racer-hd-replacement-prototype.json; validated first-family motion sequence, frames 1205..1220",
            "stock_rgba_sha256":stock_sha,
            "authored_generator":generator,"native_sampler":sampler,
            "approval": decisions[rid]
        })
    manifest={"schema_version":1,"kind":"ordered-evidence-backed-editorial-sprite-strip",
        "source_rom_sha256":EXPECTED_ROM_SHA256,"registry_sha256":sha(registry_bytes),
        "source":str(REGISTRY.relative_to(ROOT))+"::motion_review_sequence",
        "window":[1205,1220],"player":a.player,"frames":frames}
    dest=out/"inputs.json"
    dest.write_text(json.dumps(manifest,indent=2)+"\n")
    print("UR_ART_EXPORT PASS frames=%d unique=%d player=%s manifest=%s"%
        (len(frames),len(cache),a.player,dest))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
