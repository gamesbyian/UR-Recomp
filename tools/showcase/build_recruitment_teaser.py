#!/usr/bin/env python3
"""Build truthful contributor-facing UR-Recomp teasers from exact native CI captures.

Captured frames remain immutable source pixels, scaled only with nearest-neighbor.
Temporal edits are hard cuts or editorial holds, never synthetic guest frames.
Music is an original generated editorial bed, not ripped game audio.
"""
import argparse
import hashlib
import io
import json
import math
import random
import subprocess
import wave
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FPS = 24
C = {'bg':'#080d19', 'surface':'#101e2b', 'ink':'#f6fcff', 'muted':'#a3b6c6', 'cyan':'#5df3de', 'mint':'#99ecbb', 'orange':'#ffbb6b', 'line':'#28475c'}
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SOURCE_RUN=38083974528
SOURCE_ARTIFACT=11681865494

def checksum(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def fnt(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def txt(d,point,message,size=22,color=None,bold=False,anchor=None):
    d.text(point,message,font=fnt(size,bold),fill=color or C['ink'],anchor=anchor)

def pam(z,path):
    data=z.read(path); off=data.index(b'ENDHDR\n')+len(b'ENDHDR\n')
    header=data[:off].decode('ascii')
    attrs={p.split(' ',1)[0]:p.split(' ',1)[1] for p in header.splitlines() if ' ' in p}
    w,h,k=(int(attrs[x]) for x in ('WIDTH','HEIGHT','DEPTH'))
    assert attrs['TUPLTYPE']=='RGB_ALPHA' and k==4 and len(data)-off==w*h*4
    return Image.frombytes('RGBA',(w,h),data[off:]).convert('RGB')

def source_images(z):
    original=pam(z,'baldosa-fixed-source/ur-baldosa-original-source-001856.pam')
    wide=pam(z,'baldosa-ws342-captures/ur-baldosa-ws342-001856.pam')
    assert wide.crop((43,0,299,224)).tobytes()==original.tobytes()
    start=pam(z,'baldosa-fixed-source/ur-baldosa-original-source-000400.pam')
    later=pam(z,'baldosa-ws342-captures/ur-baldosa-ws342-002208.pam')
    early=[pam(z,f'baldosa-ws342-live-2p/ur-baldosa-ws342-{n:06d}.pam') for n in (1808,1824,1840,1856,1872,1888)]
    evidence=json.loads(z.read('baldosa-evidence/ws342_late_original_world.json'))
    assert evidence['real_late_guest_frame']==2208 and evidence['independent_guest_frames_equal']==2473
    assert '002208' in evidence['retained_raw_native_image']
    return {'original':original,'wide':wide,'start':start,'late':later,'early':early},evidence

def template(w,h):
    im=Image.new('RGB',(w,h),C['bg']);d=ImageDraw.Draw(im)
    for x in range(0,w,48):d.line((x,0,x,h),fill='#0e1a29',width=1)
    for y in range(0,h,48):d.line((0,y,w,y),fill='#0e1a29',width=1)
    d.rectangle((0,0,w,8),fill=C['cyan'])
    d.rectangle((0,h-6,w,h),fill=C['cyan'])
    return im,d

def framed(im,src,xywh,border=True):
    x,y,w,h=xywh;sw,sh=src.size
    scale=min(w/sw,h/sh);rw=max(1,int(sw*scale));rh=max(1,int(sh*scale))
    img=src.resize((rw,rh),Image.Resampling.NEAREST)
    at=(x+(w-rw)//2,y+(h-rh)//2)
    im.paste(img,at)
    if border:
        d=ImageDraw.Draw(im)
        d.rectangle((at[0]-3,at[1]-3,at[0]+rw+2,at[1]+rh+2),outline=C['line'],width=3)
    return at+(rw,rh)

def label(d,left,top,name):
    txt(d,(left,top),name,18,C['cyan'],True)

def header(d,w,head,sub,step=None):
    label(d,52,37,'UR-RECOMP   /   BUILD WITH US')
    txt(d,(52,79),head,40,C['ink'],True)
    txt(d,(54,132),sub,19,C['muted'])
    if step:txt(d,(w-48,46),step,15,C['orange'],True,anchor='ra')

def footer(d,w,h,disclaimer='SOURCE-CAPTURED DEVELOPMENT FOOTAGE  •  NOT A FINISHED GAME DEMO'):
    d.line((48,h-53,w-48,h-53),fill=C['line'],width=2)
    txt(d,(51,h-41),disclaimer,13,C['muted'])

def scene_horizontal(t,src):
    w,h=1280,720;im,d=template(w,h)
    if t<3:
        txt(d,(72,84),'A SNES CLASSIC.',36,C['orange'],True)
        txt(d,(72,139),'A NEW FRONTIER.',47,C['ink'],True)
        txt(d,(75,222),'UNIRACERS / UNIRALLY',30,C['cyan'],True)
        txt(d,(76,279),'Rebuilding the real game, frame by frame.',22,C['muted'])
        txt(d,(76,345),'AUTHENTIC EXECUTION',20,C['mint'],True)
        txt(d,(76,382),'WIDER WORLD   •   MODERN PC',20,C['mint'],True)
        framed(im,src['start'],(785,92,425,520))
        txt(d,(80,616),'OPEN COLLABORATION  /  ACTIVE DEVELOPMENT',18,C['orange'],True)
    elif t<9:
        header(d,w,'43 MORE SOURCE PIXELS ON EACH SIDE.','Native Original mode versus the genuine wider-world capture','01  /  THE EVIDENCE')
        framed(im,src['original'],(70,196,510,350))
        wide_box=framed(im,src['wide'],(611,196,600,350))
        x,y,rw,rh=wide_box
        d.line((x+round(43*rw/342),y,x+round(43*rw/342),y+rh),fill=C['cyan'],width=3)
        d.line((x+round(299*rw/342),y,x+round(299*rw/342),y+rh),fill=C['cyan'],width=3)
        txt(d,(310,565),'ORIGINAL 256 × 224',19,C['ink'],True,anchor='mm')
        txt(d,(910,565),'WIDER 342 × 224',19,C['cyan'],True,anchor='mm')
        txt(d,(640,612),'EXACT CENTRE-PIXEL MATCH   •   SAME GUEST FRAME 1856',18,C['orange'],True,anchor='mm')
    elif t<15:
        header(d,w,'TWO RIDERS. ORIGINAL GAME LOGIC.','Real split-screen Baldosa execution captured by CI','02  /  THE GAME')
        idx=min(5,int((t-9)*1.0))
        framed(im,src['early'][idx],(116,191,1048,406))
        txt(d,(640,619),f'SAMPLED ORIGINAL FRAME {1808+idx*16}   /   16-FRAME INTERVALS',18,C['orange'],True,anchor='mm')
    elif t<20:
        header(d,w,'THE RACE IS ALREADY RUNNING.','A genuine later guest-produced frame, beyond the start countdown','03  /  LATER FRAME')
        framed(im,src['late'],(128,179,1024,431))
        txt(d,(640,623),'FRAME 2208   •   RACE CLOCK ~0:03   •   SINGLE REAL CAPTURE',17,C['orange'],True,anchor='mm')
    elif t<25:
        header(d,w,'ONE PROJECT. TWO AMBITIONS.','A playable Windows remaster and a reproducible technical reference','04  /  THE VISION')
        for j,(head,detail) in enumerate([('THE GAME','Native execution • true widescreen • modern interface'),('THE REFERENCE','Original-ROM archaeology • independent evidence • open questions')]):
            y=217+j*166
            d.rounded_rectangle((74,y,1205,y+136),radius=16,fill=C['surface'],outline=C['line'],width=2)
            txt(d,(107,y+21),head,30,C['cyan'] if j==0 else C['orange'],True)
            txt(d,(110,y+83),detail,23,C['ink'])
        txt(d,(640,602),'Both are still under active development and independent QA.',19,C['muted'],anchor='mm')
    elif t<30:
        header(d,w,'YOUR AGENT CAN HELP BUILD IT.','Scoped tasks. Reviewed pull requests. Reproducible results.','05  /  CONTRIBUTORS')
        parts=[('AI CODING AGENTS','Own a bounded engineering task'),('SNES / C / C++ EXPERTS','Reverse engineering and source-level review'),('QA / ART / AUDIO','Human eyes, test hardware, technical creativity')]
        for i,(a,b) in enumerate(parts):
            y=205+i*127
            d.rounded_rectangle((84,y,1195,y+107),radius=12,fill=C['surface'],outline=C['line'],width=2)
            txt(d,(115,y+16),a,28,C['mint'],True)
            txt(d,(117,y+63),b,19,C['muted'])
    else:
        txt(d,(640,92),'HELP FINISH SOMETHING REAL.',40,C['orange'],True,anchor='mm')
        txt(d,(640,192),'UR-RECOMP',85,C['ink'],True,anchor='mm')
        txt(d,(640,292),'Code. Capture. Compare. Contribute.',27,C['mint'],anchor='mm')
        framed(im,src['late'],(434,348,412,252))
        d.rounded_rectangle((187,611,1093,664),radius=12,fill='#176271',outline=C['cyan'],width=2)
        txt(d,(640,637),'github.com/gamesbyian/UR-Recomp',27,C['ink'],True,anchor='mm')
    footer(d,w,h)
    return im

def scene_vertical(t,src):
    w,h=720,1280;im,d=template(w,h)
    if t<4:
        txt(d,(360,128),'REMEMBER',48,C['orange'],True,anchor='mm')
        txt(d,(360,198),'UNIRACERS?',52,C['ink'],True,anchor='mm')
        framed(im,src['start'],(80,295,560,530))
        txt(d,(360,895),'IT’S BEING REBUILT.',35,C['cyan'],True,anchor='mm')
        txt(d,(360,955),'WITH REAL SNES GAME LOGIC.',22,C['muted'],anchor='mm')
    elif t<9:
        txt(d,(360,122),'REAL WIDESCREEN.',39,C['cyan'],True,anchor='mm')
        txt(d,(360,186),'NOT A STRETCHED IMAGE.',23,C['muted'],anchor='mm')
        framed(im,src['wide'],(50,285,620,510))
        txt(d,(360,855),'+43 PIXELS PER SIDE',27,C['orange'],True,anchor='mm')
        txt(d,(360,903),'EXACT CENTRE MATCH',23,C['ink'],anchor='mm')
        txt(d,(360,1050),'Captured from native guest execution',19,C['muted'],anchor='mm')
    elif t<14:
        txt(d,(360,122),'TWO RACERS.',45,C['cyan'],True,anchor='mm')
        txt(d,(360,184),'ACTUAL GUEST FRAME 2208.',22,C['muted'],anchor='mm')
        framed(im,src['late'],(44,310,632,585))
        txt(d,(360,976),'DEVELOPMENT CAPTURE',26,C['orange'],True,anchor='mm')
        txt(d,(360,1028),'Not a continuous gameplay recording',17,C['muted'],anchor='mm')
    else:
        txt(d,(360,160),'HELP BUILD THE REST.',40,C['orange'],True,anchor='mm')
        txt(d,(360,300),'UR-RECOMP',57,C['ink'],True,anchor='mm')
        txt(d,(360,420),'AI AGENTS',36,C['cyan'],True,anchor='mm')
        txt(d,(360,492),'REVERSE ENGINEERS',32,C['cyan'],True,anchor='mm')
        txt(d,(360,564),'PLAYTESTERS',34,C['cyan'],True,anchor='mm')
        txt(d,(360,677),'EVIDENCE > HYPE',31,C['mint'],True,anchor='mm')
        d.rounded_rectangle((31,857,689,939),radius=13,fill='#176271',outline=C['cyan'],width=3)
        txt(d,(360,898),'github.com/gamesbyian/',27,C['ink'],True,anchor='mm')
        txt(d,(360,1000),'UR-Recomp',37,C['ink'],True,anchor='mm')
    d.line((34,1190,686,1190),fill=C['line'],width=2)
    txt(d,(360,1216),'SOURCE CAPTURES • WORK IN PROGRESS',14,C['muted'],True,anchor='mm')
    return im

def render(name, seconds, dims, callback, src, outdir):
    output=outdir/name
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{dims[0]}x{dims[1]}','-r',str(FPS),'-i','-','-i',str(outdir/'editorial_music.wav'),'-map','0:v:0','-map','1:a:0','-t',str(seconds),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-movflags','+faststart',str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(seconds*FPS):proc.stdin.write(callback(i/FPS,src).tobytes())
    finally:
        proc.stdin.close();code=proc.wait()
        if code:raise RuntimeError(f'ffmpeg failed: {code}')
    print('CREATED',output,output.stat().st_size)
    return output

def editorial_music(path,duration=35,rate=22050):
    """Original simple 120 BPM pulse/triangle backing; no sampled or source game music."""
    notes=[(220.0,261.63,329.63),(174.61,220.0,261.63),(130.81,164.81,196.0),(196.0,246.94,293.66)]
    rng=random.Random(701)
    with wave.open(str(path),'wb') as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(rate)
        chunk=bytearray()
        for i in range(duration*rate):
            t=i/rate;beat=int(t*2);bar=(beat//8)%4; chord=notes[bar]
            bassfreq=chord[0]/2
            bassp=(t*bassfreq)%1
            bass=(4*abs(bassp-.5)-1)*.16
            ap=(t*chord[(beat//2)%3]*2)%1
            lead=(.10 if ap<.24 else -.10)
            local=(t*2)%1
            env=max(0,1-local*3)
            thump=math.sin(2*math.pi*(57*t+7*math.exp(-local*35)))*.19*env
            hat=(rng.random()*2-1)*.037*max(0,1-((t*4)%1)*9)
            mixed=max(-.85,min(.85,bass+lead+thump+hat))
            sample=int(mixed*32767)
            chunk.extend(sample.to_bytes(2,'little',signed=True))
            if len(chunk)>=32768:wf.writeframesraw(chunk);chunk.clear()
        if chunk:wf.writeframesraw(chunk)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--zip',type=Path,required=True)
    ap.add_argument('--outdir',type=Path,required=True)
    args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.zip) as z:images,evidence=source_images(z)
    soundtrack=args.outdir/'editorial_music.wav'
    editorial_music(soundtrack)
    full=render('ur-recomp-recruitment-teaser-20261010.mp4',34,(1280,720),scene_horizontal,images,args.outdir)
    vertical=render('ur-recomp-recruitment-short-vertical-20261010.mp4',18,(720,1280),scene_vertical,images,args.outdir)
    poster=scene_horizontal(31,images)
    poster.save(args.outdir/'ur-recomp-recruitment-poster-20261010.png',optimize=True)
    images['late'].save(args.outdir/'native-late-source-frame-2208.png',optimize=True)
    # Intermediate uncompressed audio is reproducible and deliberately not retained in Git.
    soundtrack.unlink()
    outputs=[full,vertical,args.outdir/'ur-recomp-recruitment-poster-20261010.png',args.outdir/'native-late-source-frame-2208.png']
    result={'schema':'UR-RECRUITMENT-TEASER/1','source_run':SOURCE_RUN,'source_artifact_id':SOURCE_ARTIFACT,'source_zip_sha256':checksum(args.zip),'guest_frame_2208_ppu_sha256':evidence['late_ppu_rgba_sha256'],'original_centre_match_1856':True,'late_full_ppu_changed_pixels':evidence['changed_full_ppu_pixels_from_earlier'],'guest_crc_matching_frames':evidence['independent_guest_frames_equal'],'footage':'Discrete authentic native frames, selected from CI; video edits are holds and cuts, not gameplay frame interpolation','music':'Synthetic original editorial audio, not source-game soundtrack','status':'Development footage only; no release or L4/L5 QA gate implied','outputs':{p.name:{'bytes':p.stat().st_size,'sha256':checksum(p)} for p in outputs},'script':'tools/showcase/build_recruitment_teaser.py'}
    (args.outdir/'recruitment-provenance.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
