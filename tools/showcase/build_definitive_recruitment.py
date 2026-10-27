#!/usr/bin/env python3
"""Assemble an evidence-locked recruitment master after all agent media is reviewed.

This script intentionally fails if the technical/art clips are not independently
approved. No placeholder graphics are quietly substituted for promised shots.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from build_three_source_recruitment import verify as verify_native

TOTAL_SECONDS = 58
REEL = [
    ("title", 4, "Original title art ordinals 270..359 then real checkerboard menu ordinals 420..569; deliberate editorial cut across source black transition"),
    ("modern", 10, "independent genuine Modern navigation and stock handoff, frames 1..600"),
    ("reveal", 7, "same-capture Original centre uncovered into 342-wide world"),
    ("comparison", 4, "two views of one wide capture, NOT two native runs"),
    ("technical", 9, "approved editorial reconstruction evidence"),
    ("art", 5, "approved 4x artwork demonstration, limited coverage"),
    ("archaeology", 5, "approved editorial animation archaeology"),
    ("race", 10, "real uninterrupted two-player native 342-wide recording, frames 2100..2699"),
    ("cta", 4, "editorial invitation to contribute"),
]
ROLE_LABELS = {
    "technical": "EDITORIAL ENGINEERING VISUALIZATION",
    "art": "APPROVED 4X ART - LIMITED POSE COVERAGE",
    "archaeology": "EDITORIAL ANIMATION ARCHAEOLOGY",
}

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def probe(path):
    streams = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
        "-of", "json", str(path)]))["streams"]
    if len(streams) != 1:
        raise ValueError(f"Require one video stream: {path}")
    return streams[0]

def verify_output(path, w, h, count):
    p = probe(path)
    got = p["width"],p["height"],p["r_frame_rate"],int(p["nb_read_frames"])
    if got != (w,h,"60/1",count):
        raise ValueError(f"Output mismatch {path}: {got}")

def verify_editorial(role, path, gate):
    item = gate["clips"][role]
    if item["kind"] != "editorial_graphic" or item["approved_for_trailer"] is not True:
        raise ValueError(f"{role}: no accepted editorial evidence")
    if item["sha256"] != sha(path):
        raise ValueError(f"{role}: media hash mismatch")
    if len(item.get("evidence_links", [])) < 1:
        raise ValueError(f"{role}: no evidence authority")
    review = item.get("review_frame_sha256", {})
    if len(review) < 3:
        raise ValueError(f"{role}: missing independent frame inspection")
    for file, expected in review.items():
        witness = gate["_gate_root"] / file
        if not witness.is_file() or sha(witness) != expected:
            raise ValueError(f"{role}: missing/changed review frame {file}")
    p = probe(path)
    if (p["width"],p["height"]) != (1920,1080):
        raise ValueError(f"{role}: require 1920x1080 editorial footage")
    if p["r_frame_rate"] not in ("30/1","60/1"):
        raise ValueError(f"{role}: only 30 or 60 editorial fps")
    minimum = next(duration for name,duration,_ in REEL if name == role)
    if int(p["nb_read_frames"]) < minimum * int(p["r_frame_rate"].split("/")[0]):
        raise ValueError(f"{role}: too few frames")
    return item

def verify_reveals(race, reveal, comparison, manifest):
    x = json.loads(manifest.read_text())
    if x.get("schema") != "UR-RECRUITMENT-CONTINUOUS-PRESENTATION/1":
        raise ValueError("Unknown presentation edit manifest")
    if x["source_sha256"] != sha(race) or not x["no_temporal_interpolation"]:
        raise ValueError("Unverified continuous origin")
    if x["comparison"]["independent_original_capture"] is not False:
        raise ValueError("Comparison must identify its actual editorial status")
    if x["comparison"]["independent_guest_wram_state_comparison"] is not False:
        raise ValueError("Do not imply independent WRAM-matched comparison")
    for role, path, frames in (("reveal",reveal,420),("comparison",comparison,300)):
        if x[role]["sha256"] != sha(path):
            raise ValueError(f"{role}: video SHA mismatch")
        verify_output(path,1920,1080,frames)
    return x

def music(path):
    file = Path(__file__).with_name("build_recruitment_teaser.py")
    spec=importlib.util.spec_from_file_location("ur_authored_editorial_music",file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.editorial_music(path,duration=60)

def execute(cmd):
    subprocess.run(cmd, check=True)

def build(args):
    for name in ("title","modern","race"):
        verify_native(name, getattr(args,name),getattr(args,name+"_manifest"))
    presentation = verify_reveals(args.race,args.reveal,args.comparison,args.presentation_manifest)
    gate=json.loads(args.editorial_approval.read_text())
    if gate.get("schema") != "UR-RECRUITMENT-MEDIA-APPROVAL/1" or gate.get("accepted_by") in (None,""):
        raise ValueError("Final media approval must identify an accountable reviewer and review method")
    gate["_gate_root"]=args.editorial_approval.parent
    for role in ROLE_LABELS:
        verify_editorial(role,getattr(args,role),gate)
    for name in ("technical","art","archaeology"):
        if getattr(args,name) in (args.title,args.modern,args.race):
            raise ValueError("Do not relabel game footage as editorial agent material")
    args.outdir.mkdir(parents=True,exist_ok=True)
    h=args.outdir/"ur-recomp-definitive-recruitment-58s-1080p.mp4"
    v=args.outdir/"ur-recomp-recruitment-vertical-20s-1080x1920.mp4"
    poster=args.outdir/"ur-recomp-recruitment-final-poster.png"
    input_files=[args.title,args.modern,args.reveal,args.comparison,args.technical,
                 args.art,args.archaeology,args.race]
    # 8/9 are the exclusive approved video background plates; 10 is score.
    plates=Path(__file__).resolve().parents[2] / "assets/promo/canonical"
    wide=plates/"blueprint-16x9-logo-right.png"
    portrait=plates/"blueprint-9x16-portrait-2160x3840.png"
    if not wide.is_file() or not portrait.is_file():
        raise ValueError("Owner-approved promotional background missing")
    input_flags=[]
    for f in input_files: input_flags.extend(["-i",str(f)])
    input_flags+=["-loop","1","-framerate","60","-i",str(wide)]
    input_flags+=["-loop","1","-framerate","60","-i",str(portrait)]
    horizontal=[]
    source_index={"title":0,"modern":1,"reveal":2,"comparison":3,
                  "technical":4,"art":5,"archaeology":6,"race":7,"cta":8}
    time_cursor=0
    timeline=[]
    for n,(role,duration,description) in enumerate(REEL):
        idx=source_index[role]
        if role=="title":
            filt=("[0:v]trim=start_frame=270:end_frame=360,setpts=PTS-STARTPTS[originaltitle];"
                  "[0:v]trim=start_frame=420:end_frame=570,setpts=PTS-STARTPTS[originalmenu];"
                  "[originaltitle][originalmenu]concat=n=2:v=1:a=0")
        elif role=="cta":
            filt=f"[{idx}:v]trim=duration={duration},setpts=PTS-STARTPTS"
        else:
            filt=f"[{idx}:v]trim=duration={duration},setpts=PTS-STARTPTS"
        if role in ROLE_LABELS:
            label=ROLE_LABELS[role]
            filt+=(
                ",fps=60,drawtext=text='"+label+"':fontsize=26:fontcolor=white:"
                "x=(w-text_w)/2:y=1030:box=1:boxcolor=black@0.72:boxborderw=8"
            )
        if role=="cta":
            filt+=(
                ",drawtext=text='UNIRACERS - REBUILT WITH EVIDENCE':"
                "fontsize=66:fontcolor=white:x=(w-text_w)/2:y=310,"
                "drawtext=text='CODERS  ARTISTS  REVERSE ENGINEERS  QA':"
                "fontsize=37:fontcolor=white:x=(w-text_w)/2:y=497,"
                "drawtext=text='github.com/gamesbyian/UR-Recomp':"
                "fontsize=47:fontcolor=white:x=(w-text_w)/2:y=667"
            )
        filt+=f",format=yuv420p[h{n}]"
        horizontal.append(filt)
        timeline.append({"at_frame":time_cursor*60,"frame_count":duration*60,
                         "source":role,"description":description})
        time_cursor+=duration
    assert time_cursor==TOTAL_SECONDS
    horizontal.append("".join(f"[h{i}]" for i in range(len(REEL)))+
                      f"concat=n={len(REEL)}:v=1:a=0[out]")
    graph_h=";".join(horizontal)
    # Editorial 20s mobile version retains *both* 2P bands by fitting the
    # complete raster, never cropping the lower racer out of the vertical cut.
    def mobile(idx, begin, duration, caption, out):
        bg="bg"+out[1:]
        clip="clip"+out[1:]
        return (
            f"[{idx}:v]trim=start={begin}:duration={duration},"
            "setpts=PTS-STARTPTS,scale=1080:608:flags=neighbor,"
            f"format=rgba[{clip}];"
            f"[{bg}][{clip}]overlay=x=0:y=656:shortest=1,"
            f"drawtext=text='{caption}':fontsize=42:fontcolor=white:"
            f"x=(w-text_w)/2:y=360,"
            f"format=yuv420p[{out}]"
        )
    graph_v=";".join([
      "[9:v]scale=1080:1920:flags=lanczos,split=5[bg0][bg1][bg2][bg3][bg4]",
      "[0:v]trim=start_frame=270:end_frame=360,setpts=PTS-STARTPTS[verticaltitle]",
      "[0:v]trim=start_frame=420:end_frame=450,setpts=PTS-STARTPTS[verticalmenu]",
      "[verticaltitle][verticalmenu]concat=n=2:v=1:a=0,"
      "scale=1080:608:flags=neighbor,format=rgba[clip0]",
      "[bg0][clip0]overlay=x=0:y=656:shortest=1,"
      "drawtext=text='GENUINE ORIGINAL TITLE AND MENU':fontsize=40:fontcolor=white:"
      "x=(w-text_w)/2:y=360,format=yuv420p[m0]",
      mobile(1,0,4,"REAL MODERN FRONTEND","m1"),
      mobile(2,1,6,"43 EXTRA WORLD COLUMNS PER SIDE","m2"),
      mobile(7,2,5,"UNINTERRUPTED TWO-PLAYER RACING","m3"),
      "[bg4]trim=duration=3,setpts=PTS-STARTPTS,"
      "drawtext=text='REBUILD THE REAL GAME':fontsize=58:fontcolor=white:"
      "x=(w-text_w)/2:y=680,"
      "drawtext=text='github.com/gamesbyian/UR-Recomp':fontsize=29:"
      "fontcolor=white:x=(w-text_w)/2:y=1040,format=yuv420p[m4]",
      "[m0][m1][m2][m3][m4]concat=n=5:v=1:a=0[out]"
    ])
    with tempfile.TemporaryDirectory() as td:
        score=Path(td)/"ur-promotional-score.wav"
        music(score)
        inputs=input_flags+["-i",str(score)]
        def encode(graph, dest, secs, size):
            execute(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y"]+
                    inputs+["-filter_complex",graph,"-map","[out]","-map","10:a:0",
                    "-frames:v",str(secs*60),"-t",str(secs),"-c:v","libx264",
                    "-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","144k","-movflags","+faststart",str(dest)])
            verify_output(dest,*size,secs*60)
        encode(graph_h,h,58,(1920,1080))
        encode(graph_v,v,20,(1080,1920))
    # Poster is a genuine captured native race moment from the film, with
    # conspicuously editorial title typography, never a remastered title shot.
    execute(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-ss","48","-i",str(h),"-vf",
        "scale=1700:956:flags=neighbor,pad=1920:1080:110:62:0x091421,"
        "drawtext=text='UNIRACERS RECOMP':fontsize=48:fontcolor=white:"
        "x=(w-text_w)/2:y=5,"
        "drawtext=text='REAL NATIVE GAMEPLAY - HELP BUILD WHAT COMES NEXT':"
        "fontsize=27:fontcolor=white:x=(w-text_w)/2:y=1040",
        "-frames:v","1",str(poster)])
    result={
      "schema":"UR-RECRUITMENT-FINAL-MEDIA/1",
      "film_duration_seconds":58,
      "fps":"60/1",
      "editorial_splices_not_continuous_title_to_race":True,
      "original_title_internal_edit": {
          "purpose":"skip proven black transition between authentic title and menu",
          "horizontal_source_ordinals":[[270,359],[420,569]],
          "vertical_source_ordinals":[[270,359],[420,449]],
          "faked_gameplay_frames":False,
      },
      "technical_art_segments_are_editorial_not_in_game_graphics":True,
      "original_widescreen_verified_2p_native_capture":True,
      "remastered_widescreen_claim":False,
      "finished_beta_claim":False,
      "continuous_4k_claim":False,
      "timeline":timeline,
      "source_sha256":{name:sha(getattr(args,name)) for name in
                       ("title","modern","race","reveal","comparison","technical","art","archaeology")},
      "source_manifest_sha256":{name:sha(getattr(args,name+"_manifest")) for name in
                       ("title","modern","race")},
      "presentation_manifest_sha256":sha(args.presentation_manifest),
      "editorial_acceptance_sha256":sha(args.editorial_approval),
      "output_sha256":{p.name:sha(p) for p in (h,v,poster)},
      "audio":"Original deterministic editorial score, not commercial or game audio",
    }
    (args.outdir/"definitive-trailer-provenance.json").write_text(
      json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"outputs":result["output_sha256"],"frames":3480},indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("title","modern","race"):
        p.add_argument("--"+name,required=True,type=Path)
        p.add_argument("--"+name+"-manifest",required=True,type=Path)
    for name in ("reveal","comparison","technical","art","archaeology"):
        p.add_argument("--"+name,required=True,type=Path)
    p.add_argument("--presentation-manifest",type=Path,required=True)
    p.add_argument("--editorial-approval",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    build(p.parse_args())
