#!/usr/bin/env python3
"""Upgrade original 85s flagship with independently verified genuine 2P courses.

Preserves 85-second original authored audio; replaces ONLY original flat 2P
race blocks at 10–14s and 70–76s with authentic source-contiguous native
MegaJump, Looper and Jumps runs, using explicit editorial cuts.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path

EXPECTED={
 "flagship":"6b5015fb83cb6e6deaebb08b8adf55f86004918f4169da7a71e73e46bc23cd9c",
 "mega":"cee7dbdf271068896c9636206c6613bda302ba938a1c473ac4483ab6369617a4",
 "jumps":"46283d6fb1f698868a736df0cee857aa8928cc587f39d88c77a41c41813c9b03",
 "looper":"3de690c458b70d802af692418a155b31bb0381d595e61c897a62be492aeecbe3",
}
SHOTS=[
 {"kind":"original","video":0,"first":0,"count":600,"description":"Original title and authentic reveal from approved 85s source"},
 {"kind":"actual_native","video":1,"first":300,"count":240,"course":"MegaJump","description":"True source frames: steep slopes / separate racers"},
 {"kind":"original","video":0,"first":840,"count":3360,"description":"Unchanged approved Modern and technical showcase"},
 {"kind":"actual_native","video":3,"first":180,"count":180,"course":"Looper","description":"Source observed curved graded terrain; complete loop not certified"},
 {"kind":"actual_native","video":2,"first":360,"count":180,"course":"Jumps","description":"Source-observed airborne 2P trick frame on authentic slopes"},
 {"kind":"original","video":0,"first":4560,"count":540,"description":"Original contribution invitation and entire authored ending"},
]
def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
def probe(path):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames",
 "-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_read_frames",
 "-of","json",str(path)]))["streams"][0]
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--flagship",type=Path,required=True)
 a.add_argument("--sources",type=Path,required=True)
 a.add_argument("--outdir",type=Path,required=True)
 z=a.parse_args()
 files=[z.flagship,z.sources/"native-megajump-p2-leads-900f.mp4",
   z.sources/"native-jumps-p1-leads-900f.mp4",z.sources/"native-looper-p1-leads-900f.mp4"]
 for key,src in zip(("flagship","mega","jumps","looper"),files):
  if sha(src)!=EXPECTED[key]: raise ValueError(f"Changed source: {key}")
  p=probe(src)
  if (p["width"],p["height"],p["r_frame_rate"],int(p["nb_read_frames"]))!=(
    1920,1080,"60/1",5100 if key=="flagship" else 900):raise ValueError("Source frame identity mismatch")
 ledger=json.loads((z.sources/"dynamic-racing-provenance.json").read_text())
 for key,name in [("mega","megajump-p2-leads"),("jumps","jumps-p1-leads"),("looper","looper-p1-leads")]:
  row=ledger["routes"][name]
  if row["sha256"]!=EXPECTED[key] or len(row["real_guest_world_position_witnesses"])<3:
   raise ValueError("Missing source native frame and WRAM proof "+key)
 if sum(s["count"] for s in SHOTS)!=5100:raise ValueError("Original timeline changed")
 fg=[]
 for i,shot in enumerate(SHOTS):
  v=shot["video"]
  filt=f"[{v}:v]trim=start_frame={shot['first']}:end_frame={shot['first']+shot['count']},setpts=PTS-STARTPTS"
  if shot["kind"]=="actual_native":
   # Complete native 2P window, uniformly sized into editorial margin only.
   label=("ACTUAL NATIVE "+shot["course"].upper()+"  /  INDEPENDENT SOURCE SESSION")
   filt+=(",scale=1707:960:flags=neighbor,pad=1920:1080:106:60:0x08101f,"
      "drawtext=text='"+label+"':fontsize=25:fontcolor=white:x=(w-text_w)/2:y=15")
  fg.append(filt+f",format=yuv420p[x{i}]")
 fg.append("".join(f"[x{i}]" for i in range(len(SHOTS)))+
           f"concat=n={len(SHOTS)}:v=1:a=0[out]")
 z.outdir.mkdir(parents=True,exist_ok=True)
 dest=z.outdir/"ur-recomp-flagship-85s-dynamic-courses-1080p.mp4"
 cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y"]
 for src in files:cmd+=["-i",str(src)]
 cmd+=["-filter_complex",";".join(fg),"-map","[out]","-map","0:a:0","-frames:v","5100",
  "-t","85","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
  "-r","60","-c:a","copy","-movflags","+faststart",str(dest)]
 subprocess.run(cmd,check=True)
 p=probe(dest)
 if (p["width"],p["height"],p["r_frame_rate"],int(p["nb_read_frames"]))!=(1920,1080,"60/1",5100):
  raise ValueError("Not 5100 exact output frames")
 receipt={"schema":"UR-RECRUITMENT-GENUINE-TOPOLOGY-REVISION/1","film":dest.name,
   "sha256":sha(dest),"frames":5100,"fps":"60/1",
   "unchanged_original_music":True,
   "edited_audio_source_sha256":EXPECTED["flagship"],
   "sources_sha256":EXPECTED,"shots":SHOTS,"independent_native_session_cuts_disclosed":True,
   "no_temporal_interpolation":True,"no_guest_or_track_changes":True,
   "complete_closed_loop_certified":False,"hill_climb_capture_certified":False,
   "source_racing_real_native_342_columns":True}
 (z.outdir/"dynamic-flagship-v2-provenance.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"sha256":receipt["sha256"],"frames":5100}))
if __name__=="__main__":main()
