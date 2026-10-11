#!/usr/bin/env python3
"""Produce the recruitment film from three separately verified native Baldosa recordings.

Editorial CUTS between different CI executions are explicit; never claim one
uninterrupted session from title to race. No synthetic gameplay or interpolation.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

SOURCES = (
    ("title", "ur-native-title-menu-900f.mp4", 900, "published_sha256"),
    ("modern", "ur-modern-root-600f.mp4", 600, "output_sha256"),
    ("race", "ur-native-2p-clean-600f.mp4", 600, "published_sha256"),
)
FRAMES = 1800

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda: stream.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def probe(path):
    raw=subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0",
        "-show_entries","stream=width,height,r_frame_rate,nb_read_frames","-of","json",str(path)],
        check=True,capture_output=True,text=True)
    streams=json.loads(raw.stdout)["streams"]
    if len(streams)!=1:raise ValueError("Exactly one video stream required")
    return streams[0]

def verify(kind,video,manifest):
    m=json.loads(manifest.read_text())
    name,expected,field=next((n,c,k) for t,n,c,k in SOURCES if t==kind)
    if video.name!=name or m.get("status")!="verified_consecutive_host_presentations":
        raise ValueError(f"{kind}: wrong source or unverified manifest")
    if m.get("consecutive_host_presentations")!=expected or m.get("dropped_or_skipped_host_frame_ids")!=0:
        raise ValueError(f"{kind}: missing or repeated guest presentations")
    if m["guest_frame_end"]-m["guest_frame_start"]+1!=expected:
        raise ValueError(f"{kind}: discontinuous guest index")
    if m["control_guest_crc_sha256"]!=m["recorded_guest_crc_sha256"]:
        raise ValueError(f"{kind}: execution divergence")
    if m[field][video.name]!=sha(video):
        raise ValueError(f"{kind}: video sha256 differs from native manifest")
    stream=probe(video)
    if (stream.get("width"),stream.get("height"),stream.get("r_frame_rate"),int(stream.get("nb_read_frames",-1)))!=(1920,1080,"60/1",expected):
        raise ValueError(f"{kind}: decoded video count/dimensions/cadence rejected: {stream}")
    return m

def main():
    p=argparse.ArgumentParser()
    for kind in ("title","modern","race"):
        p.add_argument("--"+kind,type=Path,required=True)
        p.add_argument("--"+kind+"-manifest",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    a=p.parse_args()
    manifests={k:verify(k,getattr(a,k),getattr(a,k+"_manifest")) for k in ("title","modern","race")}
    a.outdir.mkdir(parents=True,exist_ok=True)
    target=a.outdir/"ur-recomp-three-source-recruitment-30s-1080p.mp4"
    # Five seconds of genuine title frames 150..449, ten Modern frames 0..599,
    # ten original widened-world race frames 0..599, then 5s editorial card.
    graph=(
        "[0:v]trim=start_frame=150:end_frame=450,setpts=PTS-STARTPTS,format=yuv420p[v0];"
        "[1:v]trim=start_frame=0:end_frame=600,setpts=PTS-STARTPTS,format=yuv420p[v1];"
        "[2:v]trim=start_frame=0:end_frame=600,setpts=PTS-STARTPTS,format=yuv420p[v2];"
        "[3:v]trim=start_frame=0:end_frame=300,setpts=PTS-STARTPTS,"
        "drawtext=text='UNIRACERS  REBUILT':fontcolor=white:fontsize=84:"
        "x=(w-text_w)/2:y=365,"
        "drawtext=text='Research  Gameplay  Art  QA':fontcolor=white:fontsize=44:"
        "x=(w-text_w)/2:y=540,"
        "drawtext=text='github.com/gamesbyian/UR-Recomp':fontcolor=white:fontsize=42:"
        "x=(w-text_w)/2:y=660,format=yuv420p[v3];"
        "[v0][v1][v2][v3]concat=n=4:v=1:a=0[v]"
    )
    # Keep the soundtrack entirely synthesized by our existing original editor.
    import importlib.util
    editor=Path(__file__).with_name("build_recruitment_teaser.py")
    spec=importlib.util.spec_from_file_location("ur_original_promotional_score",editor)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as temp:
        music=Path(temp)/"original-promotional-score.wav"
        module.editorial_music(music,duration=31)
        cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-i",str(a.title),"-i",str(a.modern),"-i",str(a.race),
            "-f","lavfi","-i","color=c=black:s=1920x1080:r=60:d=5",
            "-i",str(music),"-filter_complex",graph,"-map","[v]","-map","4:a:0",
            "-frames:v",str(FRAMES),"-c:v","libx264","-preset","veryfast","-crf","19",
            "-pix_fmt","yuv420p","-c:a","aac","-b:a","144k",
            "-t","30","-movflags","+faststart",str(target)]
        subprocess.run(cmd,check=True)
    output=probe(target)
    if int(output["nb_read_frames"])!=FRAMES or (output["width"],output["height"])!=(1920,1080):
        raise ValueError("Final edit frame count rejected")
    manifest={
      "schema":"UR-THREE-VERIFIED-NATIVE-SOURCES/1",
      "editorial_splices_not_seamless_gameplay":True,
      "total_encoded_frames":FRAMES,"encoded_rate":"60/1",
      "timeline":[
        {"start_frame":0,"count":300,"kind":"original_title","source_guest_frames":[manifests["title"]["guest_frame_start"]+150,manifests["title"]["guest_frame_start"]+449]},
        {"start_frame":300,"count":600,"kind":"modern_root_and_stock_handoff","source_guest_frames":[manifests["modern"]["guest_frame_start"],manifests["modern"]["guest_frame_end"]]},
        {"start_frame":900,"count":600,"kind":"original_2p_genuine_342_wide_race","source_guest_frames":[manifests["race"]["guest_frame_start"],manifests["race"]["guest_frame_end"]]},
        {"start_frame":1500,"count":300,"kind":"editorial_text_card_not_gameplay"}],
      "source_sha256":{k:{"mp4":sha(getattr(a,k)),"manifest":sha(getattr(a,k+"_manifest"))} for k in manifests},
      "output_sha256":sha(target),
      "audio":"Original synthesized editorial soundtrack from existing recruitment teaser tool",
      "limits":"Three different native runs, editorial splices; stock 256-wide title, genuine 342-wide racing. 1080p delivery from 960x540 SDL drawable. Not physical 4K or finished beta."
    }
    (a.outdir/"three-source-recruitment-provenance.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"video":str(target),"frames":FRAMES,"sha256":sha(target)},indent=2))
if __name__=="__main__":main()
