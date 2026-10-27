#!/usr/bin/env python3
"""Make a portrait flagship edition with animated AMBIENT backing only.

The central 1080x608 gameplay remains a complete unchanged fitted crop from
the source-locked 27s portrait master. Only the surrounding matte is filled
with the exclusive owner-approved 9:16 promotional background. No extra source world, interpolation or newly photographed gameplay.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
PORTRAIT_PLATE = Path(__file__).resolve().parents[2] / "assets/promo/canonical/blueprint-9x16-portrait-2160x3840.png"
SOURCE_SHA=None  # trust only current matched approved-art flagship receipt
SOURCE_NAME="ur-recomp-blue-action-27s-vertical.mp4"
OUTPUT_NAME="ur-recomp-flagship-27s-social-approved-background.mp4"
SHOTS=[
 (0,1.5,"THE ORIGINAL 1994"),(1.5,2,"GENUINE MAIN MENU"),
 (2,9,"THE 342 COLUMN WORLD"),(9,13,"REAL MODERN NAVIGATION - OCT 10"),
 (13,17,"VERIFIED 65816 TO NATIVE C"),(17,23,"ACTUAL TWO PLAYER RACING"),
 (23,27,"HELP BUILD WHAT COMES NEXT")
]
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def probe(p):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames",
  "-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate,nb_read_frames",
  "-of","json",str(p)]))["streams"][0]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--outdir",type=Path,required=True)
 a=p.parse_args()
 source=a.outdir/SOURCE_NAME
 assert source.is_file(), "Current approved-art flagship portrait source required"
 receipt_file=a.outdir/"flagship-provenance.json"
 assert receipt_file.is_file(), "Current flagship provenance required"
 evidence=json.loads(receipt_file.read_text(encoding="utf-8"))
 expected_sha=evidence.get("output_sha256",{}).get(SOURCE_NAME)
 assert (evidence.get("approved_visual_assets",{}).get("portrait") ==
         "blueprint-9x16-portrait-2160x3840.png"
         and expected_sha and sha(source)==expected_sha), "Historical/noncompliant portrait source refused"
 s=probe(source)
 assert (s["width"],s["height"],s["r_frame_rate"],int(s["nb_read_frames"]))==(1080,1920,"60/1",1620)
 assert PORTRAIT_PLATE.is_file(), "Exclusive approved portrait plate missing"
 filters=[
  "[0:v]crop=1080:608:0:656[fullgame]",
  "[1:v]scale=1080:1920:flags=lanczos[approved]",
  "[approved][fullgame]overlay=x=0:y=656:format=auto,"
   "drawbox=x=0:y=647:w=1080:h=7:color=0x48e8d8:t=fill,"
   "drawbox=x=0:y=1265:w=1080:h=7:color=0x48e8d8:t=fill,"
   "drawtext=text='SOURCE-LOCKED DEVELOPMENT SHOWCASE':fontsize=26:"
   "fontcolor=0x48e8d8:x=(w-text_w)/2:y=213,"
   "drawtext=text='github.com/gamesbyian/UR-Recomp':fontsize=33:"
   "fontcolor=white:x=(w-text_w)/2:y=1500"
 ]
 for i,(start,end,label) in enumerate(SHOTS):
  filters.append(
    "drawtext=text='"+label+"':fontsize=41:fontcolor=0xfac263:"
    "x=(w-text_w)/2:y=1370:box=1:boxcolor=black@0.58:boxborderw=14:"
    "enable='between(t,"+str(start)+","+str(end-0.0001)+")'"
  )
 graph=";".join(filters[:2])+";"+",".join(filters[2:])+",format=yuv420p[v]"
 output=a.outdir/OUTPUT_NAME
 subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
    "-i",str(source),"-loop","1","-i",str(PORTRAIT_PLATE),"-filter_complex",graph,"-map","[v]","-map","0:a:0",
    "-frames:v","1620","-t","27","-c:v","libx264","-preset","veryfast",
    "-crf","19","-pix_fmt","yuv420p","-r","60","-c:a","copy",
    "-movflags","+faststart",str(output)],check=True)
 result=probe(output)
 assert (result["width"],result["height"],result["r_frame_rate"],int(result["nb_read_frames"]))==(1080,1920,"60/1",1620)
 receipt={
  "schema":"UR-FLAGSHIP-PORTRAIT-AMBIENCE/1",
  "source_name":SOURCE_NAME,"source_sha256":expected_sha,
  "out_name":OUTPUT_NAME,"out_sha256":sha(output),"frames":1620,
  "editorial_blurred_matte":False,
  "approved_portrait_plate":str(PORTRAIT_PLATE.relative_to(Path(__file__).resolve().parents[2])),
  "approved_portrait_sha256":sha(PORTRAIT_PLATE),
  "visible_game_source_area_xywh":[0,656,1080,608],
  "original_fitted_gameplay_geometry_preserved":True,
  "original_source_labels_removed_and_recreated_from_verified_source_ranges":True,
  "shots":SHOTS,"authentic_extra_world_pixels_claimed":False,
  "physical_4k_video_claimed":False
 }
 (a.outdir/"flagship-social-ambient-provenance.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("SOURCE_SHA_VERIFIED",expected_sha,"OUTPUT",receipt["out_sha256"])
if __name__=="__main__":main()
