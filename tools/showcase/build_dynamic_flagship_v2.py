#!/usr/bin/env python3
"""Create a stronger 90s flagship from two immutable existing finished films.

Cuts old near-identical, flat two-player portions; replaces with three
genuinely recorded 342-wide course excerpts, without extrapolating geometry,
re-timing source actions, combining rider positions, or claiming a closed loop.
Editorial cuts between three different guest sessions are explicit.
"""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FILM=ROOT/"media/showcase/2026-10-19/flagship/ur-recomp-flagship-85s-1080p.mp4"
FILM_SHA="6b5015fb83cb6e6deaebb08b8adf55f86004918f4169da7a71e73e46bc23cd9c"
RACE=ROOT/"media/showcase/2026-10-19/dynamic-native-2p/native-dynamic-2p-three-courses-15s.mp4"
RACE_SHA="46b5bf43bcfb4f8bdd4874e7a9994f70996688c2c86a259bef01d5102630598d"
LEDGER=RACE.parent/"dynamic-three-course-reel-provenance.json"
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1<<20),b""):h.update(c)
 return h.hexdigest()
def ffprobe(p):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_read_frames","-of","json",str(p)]))["streams"][0]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--outdir",type=Path,required=True)
 a=p.parse_args()
 for source,expected,frames in ((FILM,FILM_SHA,5100),(RACE,RACE_SHA,900)):
  if sha(source)!=expected:raise ValueError(f"Source changed: {source}")
  s=ffprobe(source)
  if (s["width"],s["height"],s["r_frame_rate"],int(s["nb_read_frames"]))!=(1920,1080,"60/1",frames):raise ValueError(f"Source frame mismatch: {source}")
 j=json.loads(LEDGER.read_text())
 if (j["schema"]!="UR-GENUINE-DYNAMIC-THREE-COURSE-SOURCE-REEL/1" or j["output_sha256"]!=RACE_SHA or j["total_frames"]!=900
      or not j["hard_cuts_explicit"] or not j["no_interpolation"] or j["has_certified_closed_loop"]):raise ValueError("Unknown or misleading topology reel")
 if [x["course"] for x in j["shots"]]!=["MegaJump","Jumps","Looper"]:raise ValueError("Unknown racing edit")
 a.outdir.mkdir(parents=True,exist_ok=True)
 output=a.outdir/"ur-recomp-flagship-dynamic-90s-1080p.mp4"
 # Original flagship: 0..10s title/reveal, 10..14s original flat 2P,
 # 14..70s Modern+technical+art, 70..76s original flat 2P, 76..85s CTA.
 # Remove ONLY the two flat sections. Insert 15s of documented racing at 10s.
 # 10+15+56+9=90s; no interpolated source game frames.
 graph=(
 "[0:v]trim=start_frame=0:end_frame=600,setpts=PTS-STARTPTS[a];"
 "[1:v]trim=start_frame=0:end_frame=900,setpts=PTS-STARTPTS,"
 "drawtext=text='GENUINE ORIGINAL 342-WIDE 2P - THREE SEPARATE COURSES':"
 "fontcolor=white:fontsize=23:x=(w-text_w)/2:y=8:"
 "box=1:boxcolor=black@0.66:boxborderw=8[b];"
 "[0:v]trim=start_frame=840:end_frame=4200,setpts=PTS-STARTPTS[c];"
 "[0:v]trim=start_frame=4560:end_frame=5100,setpts=PTS-STARTPTS[d];"
 "[a][b][c][d]concat=n=4:v=1:a=0,format=yuv420p[v]"
 )
 # Original music is retained in the exact original 0-10, 14-70 and 76-85s
 # intervals, while the corresponding score for the inserted 15s is copied
 # from the original film's own composition (45-60s) with no foreign samples.
 audio=(
 "[0:a]atrim=start=0:end=10,asetpts=PTS-STARTPTS[a0];"
 "[0:a]atrim=start=45:end=60,asetpts=PTS-STARTPTS[a1];"
 "[0:a]atrim=start=14:end=70,asetpts=PTS-STARTPTS[a2];"
 "[0:a]atrim=start=76:end=85,asetpts=PTS-STARTPTS[a3];"
 "[a0][a1][a2][a3]concat=n=4:v=0:a=1[a]"
 )
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-i",str(FILM),"-i",str(RACE),
  "-filter_complex",graph+";"+audio,"-map","[v]","-map","[a]",
  "-frames:v","5400","-t","90","-c:v","libx264","-preset","veryfast","-crf","18",
  "-r","60","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output)],check=True)
 s=ffprobe(output)
 if (s["width"],s["height"],s["r_frame_rate"],int(s["nb_read_frames"]))!=(1920,1080,"60/1",5400):raise ValueError("Final frame count failed")
 report={
  "schema":"UR-NATIVE-DYNAMIC-90S-FLAGSHIP/1",
  "film":{"path":str(FILM.relative_to(ROOT)),"sha256":FILM_SHA,"source_frames":5100},
  "race":{"path":str(RACE.relative_to(ROOT)),"sha256":RACE_SHA,"source_frames":900},
  "race_provenance_sha256":sha(LEDGER),
  "new_output_sha256":sha(output),
  "new_output_frames":5400,
  "new_output_fps":60,
  "old_flat_gameplay_removal_source_frames":[[600,839],[4200,4559]],
  "source_verified_shots":[
    {"role":"original-title-and-wide-reveal","source":"original 85s film","frames":[0,599]},
    {"role":"three-distinct-native-2p-races","source":"15s true multi-course reel","frames":[0,899],"courses":["MegaJump","Jumps","Looper"]},
    {"role":"Modern-engineering-and-art","source":"original 85s film","frames":[840,4199]},
    {"role":"recruitment-invitation","source":"original 85s film","frames":[4560,5099]}
  ],
  "genuine_race_motion_interpolated":False,
  "original_2p_cameras_repositioned":False,
  "closed_loop_completion_claimed":False,
  "jump_or_landing_success_overclaimed":False,
  "genuine_racer_position_source":"native recorded guest play, distinct independently evidenced P1/P2 coordinates",
  "new_audio":"Original preexisting promotional soundtrack spliced from original film; no new commercial music",
  "review_status":"source-validated pending independent decoded-frame and full-film review"
 }
 (a.outdir/"dynamic-flagship-provenance.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
 print("DYNAMIC_FLAGSHIP_SOURCE_SHA_PASS",report["new_output_sha256"])
if __name__=="__main__":main()
