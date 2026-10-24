#!/usr/bin/env python3
"""Assemble a 15-second truthful topology reel from exact native source captures.

No frame interpolation, merged-session simulation, geometry synthesis or course
renaming. The visually chosen extracts are independently authenticated real
native source frames. Audio intentionally omitted; master editor owns score.
"""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

SOURCES = [
 ("megajump-p2-leads", "cee7dbdf271068896c9636206c6613bda302ba938a1c473ac4483ab6369617a4", 280, 300, "MegaJump / steep curves and separated 2P"),
 ("jumps-p1-leads", "46283d6fb1f698868a736df0cee857aa8928cc587f39d88c77a41c41813c9b03", 300, 300, "Jumps / visible inverted airborne rider"),
 ("looper-p1-leads", "3de690c458b70d802af692418a155b31bb0381d595e61c897a62be492aeecbe3", 120, 300, "Looper / rolling graded terrain; full closed loop not certified"),
]
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
def probe(path):
 return json.loads(subprocess.check_output([
  "ffprobe","-v","error","-count_frames","-select_streams","v:0",
  "-show_entries","stream=width,height,r_frame_rate,nb_read_frames",
  "-of","json",str(path)]))["streams"][0]
def run(command):
 subprocess.run(command,check=True)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-dir",type=Path,required=True)
 p.add_argument("--out-dir",type=Path,required=True)
 args=p.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
 ledger=json.loads((args.source_dir/"dynamic-racing-provenance.json").read_text())
 if ledger.get("schema")!="UR-GENUINE-ASYNCHRONOUS-NATIVE-2P/1":
  raise ValueError("Not an accepted source-provenance format")
 provenance=[]
 with tempfile.TemporaryDirectory() as tmp:
  temp=Path(tmp)
  segments=[]
  for index,(name,expected,first,frames,desc) in enumerate(SOURCES):
   entry=ledger["routes"].get(name)
   movie=args.source_dir/f"native-{name}-900f.mp4"
   if not entry or entry.get("sha256")!=expected or sha(movie)!=expected:
    raise ValueError("Source video SHA mismatch "+name)
   if entry.get("recording_input_versus_control_crc_sha256") is None or len(entry.get("real_guest_world_position_witnesses",[]))<3:
    raise ValueError("Source run lacks independent guest/position evidence")
   s=probe(movie)
   if (s["width"],s["height"],s["r_frame_rate"],int(s["nb_read_frames"]))!=(1920,1080,"60/1",900):
    raise ValueError("Unexpected real source frame geometry or cadence")
   if first+frames>900: raise ValueError("Outside source run")
   target=temp/f"shot-{index:02d}.mp4"
   vf=f"trim=start_frame={first}:end_frame={first+frames},setpts=PTS-STARTPTS,format=yuv420p"
   run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-i",str(movie),"-vf",vf,"-an","-frames:v",str(frames),"-r","60",
        "-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",str(target)])
   z=probe(target)
   assert (z["width"],z["height"],z["r_frame_rate"],int(z["nb_read_frames"]))==(1920,1080,"60/1",frames)
   segments.append(target)
   provenance.append({"course":entry.get("course"),"route":name,"src_sha256":expected,
      "source_ordinal_first":first,"source_ordinal_last":first+frames-1,
      "source_guest_frame_first":entry["capture_frame_start_end"][0]+first,
      "source_guest_frame_last":entry["capture_frame_start_end"][0]+first+frames-1,
      "frame_count":frames,"description":desc,"camera_and_guest_state_unmodified":True,
      "visual_screening_type":"representative source decoded-frame inspection; not full-loop certification"})
  listing=temp/"concat.txt"
  listing.write_text("".join(f"file '{path}'\n" for path in segments))
  out=args.out_dir/"native-dynamic-2p-three-courses-15s.mp4"
  run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
       "-f","concat","-safe","0","-i",str(listing),"-an",
       "-c:v","libx264","-preset","veryfast","-crf","17",
       "-pix_fmt","yuv420p","-movflags","+faststart",str(out)])
 result=probe(out)
 assert (result["width"],result["height"],result["r_frame_rate"],int(result["nb_read_frames"]))==(1920,1080,"60/1",900)
 receipt={"schema":"UR-GENUINE-DYNAMIC-THREE-COURSE-SOURCE-REEL/1",
          "output_file":out.name,"output_sha256":sha(out),"total_frames":900,
          "total_duration_seconds":15,"fps":"60/1",
          "distinct_original_guest_sessions":True,
          "hard_cuts_explicit":True,"no_interpolation":True,
          "not_a_single_continuous_race":True,
          "has_certified_closed_loop":False,"has_certified_Hill_Climb":False,
          "recorded_gameplay":True,"source_capture_ledger_sha256":sha(args.source_dir/"dynamic-racing-provenance.json"),
          "shots":provenance}
 (args.out_dir/"dynamic-three-course-reel-provenance.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"sha256":receipt["output_sha256"],"shots":provenance},indent=2))
if __name__=="__main__":main()
