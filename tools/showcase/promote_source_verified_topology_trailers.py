#!/usr/bin/env python3
"""Replace uninteresting 2P inserts with three VERIFIED authentic-course shots.

Refuses to render until a real captured, independently reviewed 600-frame
loop / ramp / hill montage exists, with source CRC, frame IDs and SHA evidence.
Only video is cut; native guest code, renderers, HUD and physical tracks stay
unchanged. Separate courses are shown as explicit editorial cuts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

FILMS = {
 "flagship85": ("ur-recomp-flagship-85s-1080p.mp4",
                "ur-recomp-flagship-85s-true-course-action.mp4",85,1920,1080,
                [(0,600,False),(0,240,True),(840,4200,False),(240,600,True),(4560,5100,False)]),
 "classic58": ("ur-recomp-definitive-recruitment-58s-1080p.mp4",
               "ur-recomp-definitive-58s-true-course-action.mp4",58,1920,1080,
               [(0,2640,False),(0,600,True),(3240,3480,False)]),
 "flagship27": ("ur-recomp-flagship-27s-vertical.mp4",
                "ur-recomp-flagship-27s-true-course-action.mp4",27,1080,1920,
                [(0,1020,False),(0,120,True),(240,360,True),(420,540,True),(1380,1620,False)]),
 "classic20": ("ur-recomp-recruitment-vertical-20s-1080x1920.mp4",
               "ur-recomp-recruitment-20s-true-course-action.mp4",20,1080,1920,
               [(0,720,False),(0,100,True),(240,340,True),(420,520,True),(1020,1200,False)]),
}
FEATURES=["loop","ramp","hill"]

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""): h.update(block)
 return h.hexdigest()

def probe(video):
 raw=subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_entries",
    "stream=width,height,r_frame_rate,nb_read_frames,codec_type","-of","json",str(video)])
 vids=[s for s in json.loads(raw)["streams"] if s["codec_type"]=="video"]
 if len(vids)!=1:raise ValueError("Need exactly one video stream")
 v=vids[0]
 return (int(v["width"]),int(v["height"]),v["r_frame_rate"],int(v["nb_read_frames"]))

def validate_review(ledger_path:Path,review_path:Path,reel:Path,reel_receipt:Path):
 l=json.loads(ledger_path.read_text())
 r=json.loads(review_path.read_text())
 v=json.loads(reel_receipt.read_text())
 if v.get("schema")!="UR-ACCEPTED-SOURCE-TOPOLOGY-REEL/1" or not v.get("no_interpolation"):
  raise ValueError("Unaccepted / temporally changed source reel")
 if v.get("source_gameplay_changed") is not False or v.get("editorial_topology_overlay_added") is not False:
  raise ValueError("Guest geometry, gameplay or labels were altered")
 if v.get("source_manifest_sha256")!=sha(ledger_path) or v.get("review_sha256")!=sha(review_path):
  raise ValueError("Reel not certified against the supplied exact evidence")
 if v.get("output_sha256")!=sha(reel):
  raise ValueError("Authentic 3-feature reel SHA mismatch")
 shots=v.get("shots")
 if not isinstance(shots,list) or len(shots)!=3:
  raise ValueError("Need exactly three visibly evidenced separate courses")
 if [s["observed_feature"] for s in shots]!=FEATURES:
  raise ValueError("Reel must be ordered loop, ramp, hill")
 if [s["source_frame_count"] for s in shots]!=[240,180,180]:
  raise ValueError("Edit points require exactly 240/180/180 authentic frames")
 if probe(reel)!=(1920,1080,"60/1",600):
  raise ValueError("Source topology reel must be exactly 600 genuine 1080p/60fps frames")
 # Source videos and guest-coordinate proof were checked upstream by the
 # source-native reel validator. Repeat source existence/hash and 3x witness.
 routes=l.get("routes",{})
 for shot in shots:
  ident=shot["route"]
  if ident not in routes or routes[ident]["sha256"]!=shot["sha256"]:
   raise ValueError("Reel references missing or changed native recording")
  orig=ledger_path.parent / routes[ident]["movie"]
  if sha(orig)!=shot["sha256"] or probe(orig)!=(1920,1080,"60/1",900):
   raise ValueError(f"Missing/unverified original native {ident}")
  if len(routes[ident].get("real_guest_world_position_witnesses",[]))<3:
   raise ValueError("Original race must have 3 read-only WRAM position witnesses")
 return v

def derive_feature_reel_graph(source_reel_idx:int, spans, vertical:bool):
 # Source horizontal 1920x1080 is fit to 1080x608 at same aspect, retaining
 # BOTH player screens. Blank 9:16 margins are deliberately editorial.
 pieces=[]
 for j,(lo,hi,isreel) in enumerate(spans):
  idx=source_reel_idx if isreel else 0
  frag=f"[{idx}:v]trim=start_frame={lo}:end_frame={hi},setpts=PTS-STARTPTS"
  if isreel and vertical:
   frag+=",scale=1080:608:flags=neighbor,pad=1080:1920:0:656:0x08101f"
   frag+=",drawtext=text='GENUINE ORIGINAL NATIVE 2P':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=575"
  # The source reel is visibly spliced by hard cuts, never implied to be
  # simultaneous competitors across distinct tracks.
  frag+=f",format=yuv420p[p{j}]"
  pieces.append(frag)
 pieces.append("".join(f"[p{k}]" for k in range(len(spans)))+
               f"concat=n={len(spans)}:v=1:a=0[out]")
 return ";".join(pieces)

def make_one(category,meta,old:Path,oldsha:str,reel:Path,out:Path):
 oldname,newname,secs,w,h,spans=meta
 if old.name!=oldname or sha(old)!=oldsha:
  raise ValueError(f"Unqualified older video or changed original SHA for {category}")
 if probe(old)!=(w,h,"60/1",secs*60):
  raise ValueError("Original film actual frame count or dimensions changed")
 if sum(hi-lo for lo,hi,_ in spans)!=secs*60:
  raise ValueError("Output cannot change total exact original runtime")
 if out.exists():
  raise ValueError("Refuse to overwrite existing promoted output")
 vf=derive_feature_reel_graph(1,spans,vertical=h>w)
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
     "-i",str(old),"-i",str(reel),"-filter_complex",vf,
     "-map","[out]","-map","0:a:0",
     "-frames:v",str(secs*60),"-t",str(secs),
     "-c:v","libx264","-preset","veryfast","-crf","18",
     "-pix_fmt","yuv420p","-r","60","-c:a","copy",
     "-movflags","+faststart",str(out)],check=True)
 if probe(out)!=(w,h,"60/1",secs*60):
  raise ValueError("Rendered film has incorrect duration or raster")
 return {"source_sha256":oldsha,"sha256":sha(out),
         "frames":secs*60,"dimensions":[w,h],
         "edited_source_ranges":[{"start":a,"end_exclusive":b,"source":"native_topology_reel" if switch else "original_trailer"} for a,b,switch in spans]}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--ledger",type=Path,required=True)
 p.add_argument("--review",type=Path,required=True)
 p.add_argument("--reel",type=Path,required=True)
 p.add_argument("--reel-provenance",type=Path,required=True)
 p.add_argument("--original-flagship-provenance",type=Path,required=True)
 p.add_argument("--original-definitive-provenance",type=Path,required=True)
 p.add_argument("--flagship-master",type=Path,required=True)
 p.add_argument("--definitive-master",type=Path,required=True)
 p.add_argument("--flagship-vertical",type=Path,required=True)
 p.add_argument("--definitive-vertical",type=Path,required=True)
 p.add_argument("--output-dir",type=Path,required=True)
 p.add_argument("--verify-only",action="store_true")
 a=p.parse_args()
 reel_review=validate_review(a.ledger,a.review,a.reel,a.reel_provenance)
 fa=json.loads(a.original_flagship_provenance.read_text())
 de=json.loads(a.original_definitive_provenance.read_text())
 sha_by_category={"flagship85":fa["output_sha256"],"flagship27":fa["output_sha256"],
                  "classic58":de["output_sha256"],"classic20":de["output_sha256"]}
 sources={"flagship85":a.flagship_master,"classic58":a.definitive_master,
          "flagship27":a.flagship_vertical,"classic20":a.definitive_vertical}
 for category,meta in FILMS.items():
  old=sources[category]
  if sha_by_category[category].get(old.name)!=sha(old) or probe(old)!=(meta[3],meta[4],"60/1",meta[2]*60):
   raise ValueError("Exact existing film not authorized by its original source receipt: "+category)
 if a.verify_only:
  print("VALIDATED_REAL_LOOP_RAMP_HILL_MONTAGE_AND_FOUR_EXISTING_FILMS")
  return
 a.output_dir.mkdir(parents=True,exist_ok=True)
 results={}
 for category,meta in FILMS.items():
  old=sources[category]
  dest=a.output_dir/meta[1]
  results[category]=make_one(category,meta,old,sha_by_category[category][old.name],a.reel,dest)
 doc={"schema":"UR-RECRUITMENT-PROMOTED-REAL-TOPOLOGY/1",
      "authentic_reel_sha256":sha(a.reel),
      "authentic_reel_provenance_sha256":sha(a.reel_provenance),
      "original_flagship_provenance_sha256":sha(a.original_flagship_provenance),
      "original_definitive_provenance_sha256":sha(a.original_definitive_provenance),
      "shots":reel_review["shots"],"updated_films":results,
      "no_guest_frame_invention":True,
      "editing_note":"Loop/ramp/hill each from distinct genuine race; hard-cut editorial montage",
      "source_gameplay_uses_true_342_column_world":True,
      "original_soundtrack_preserved_without_resampling":True}
 (a.output_dir/"topology-trailer-provenance.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
 print(json.dumps({k:v["sha256"] for k,v in results.items()},indent=2))

if __name__=="__main__":
 main()
