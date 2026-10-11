#!/usr/bin/env python3
"""Evidence-scoped engineering motion graphics; all drawn graphics are editorial.

No original PPU pixels, guest code, or reconstructed masks are faked.
Keep these outputs out of release-quality acceptance.
"""
from pathlib import Path
import argparse, hashlib, json, math, subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
WHITE='#f3f6fc'; MUTED='#a4b7cd'; CYAN='#5be2d9'; GOLD='#f4be73'; BG='#091422'

def f(n,bold=False): return ImageFont.truetype(B if bold else R,n)
def txt(d,xy,s,n=32,c=WHITE,bold=False): d.text(xy,s,font=f(n,bold),fill=c)
def base(label,n):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,11),fill=CYAN)
    txt(d,(110,70),'UR-RECOMP  /  ENGINEERING EVIDENCE',28,CYAN,True)
    txt(d,(110,972),label,22,MUTED)
    txt(d,(1540,972),f'{n+1:03d} / 30 FPS',24,GOLD)
    txt(d,(110,1024),'EDITORIAL ANIMATION  •  NOT RECOVERED PIXEL OR CHECKSUM DATA',18,MUTED)
    return im,d

def bar(d,xy,w,p,label,subtitle,col=CYAN):
    x,y=xy
    d.rounded_rectangle((x,y,x+w,y+74),radius=13,fill='#183046')
    if p>0: d.rounded_rectangle((x,y,x+max(1,int(w*p)),y+74),radius=13,fill=col)
    txt(d,(x+20,y+90),label,28,WHITE,True)
    txt(d,(x+20,y+132),subtitle,23,MUTED)

def parity(n,t):
    im,d=base('ORIGINAL CENTRE / SOURCE-IMAGE COMPARISON / FRAME 1856',n)
    txt(d,(110,155),'TWO INDEPENDENT NATIVE RENDERS',62,WHITE,True)
    txt(d,(110,238),'same guest frame 1856  •  Original graphics mode',30,MUTED)
    progress=min(1,t/3.3); x,y=170,365
    for bx in (x,1030):
        d.rounded_rectangle((bx-16,y-16,bx+770,y+465),radius=18,outline='#376077',width=3)
        for dx in range(0,768,24):
            v=30+int(25*math.sin(dx/120))
            d.line((bx+dx,y,bx+dx,y+448),fill=(v,v+18,v+26),width=1)
        d.rectangle((bx,y,bx+768*progress,y+448),outline=CYAN,width=7)
    txt(d,(170,834),'FIXED 256 × 224',31,WHITE,True)
    txt(d,(1030,834),'WIDE CENTRE [43,299)',31,WHITE,True)
    txt(d,(110,908),f'{int(57344*progress):,} / 57,344 RGBA pixels',38,CYAN,True)
    if t>3.6: txt(d,(1120,908),'0 DIFFERENCES',38,GOLD,True)
    return im

def recording(n,t):
    im,d=base('RECORDER NON-INTERFERENCE / GUEST WRAM CRC STREAMS',n)
    txt(d,(110,157),'RECORDING ON. RECORDING OFF.',59,WHITE,True)
    txt(d,(110,238),'Separate native runs  •  full guest WRAM CRC streams identical',30,MUTED)
    progress=min(1,t/3.7)
    bar(d,(155,385),1600,progress,'VIDEO CAPTURE DISABLED','Guest WRAM CRC stream  •  2P route')
    bar(d,(155,615),1600,progress,'VIDEO CAPTURE ENABLED','Guest WRAM CRC stream  •  same inputs',GOLD)
    if t>3.7:
        txt(d,(155,866),'CRC STREAMS BYTE-IDENTICAL',53,CYAN,True)
        txt(d,(155,935),'600 consecutive recorded guest frame IDs: 2100–2699',29,MUTED)
    return im

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as fp:
        for part in iter(lambda:fp.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def movie(outdir,name,fn):
    out=outdir/(name+'.mp4')
    args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(args,stdin=subprocess.PIPE)
    try:
        for n in range(FPS*6):
            frame=fn(n,n/FPS)
            if n==99:frame.save(outdir/(name+'-keyframe.png'))
            proc.stdin.write(frame.tobytes())
    finally: proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('FFmpeg encoding failed: '+name)
    details=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(out)]))['streams'][0]
    if (int(details['width']),int(details['height']),details['r_frame_rate'],int(details['nb_frames']))!=(W,H,'30/1',180):raise RuntimeError('Unexpected encoding '+str(details))
    return {'sha256':sha(out),'bytes':out.stat().st_size,'frames':180,'fps':30,'dimensions':[W,H]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--outdir',type=Path,required=True)
    ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    args=ap.parse_args()
    out=args.outdir;out.mkdir(parents=True,exist_ok=True)
    files={
        '01-source-centre-parity.mp4':movie(out,'01-source-centre-parity',parity),
        '02-recording-noninterference.mp4':movie(out,'02-recording-noninterference',recording),
    }
    gitrev=subprocess.check_output(['git','-C',str(args.repo_root),'rev-parse','HEAD'],text=True).strip()
    manifest={'type':'editorial-motion-graphics','source_commit':gitrev,'fps':FPS,
       'source_evidence':{
        'center':{'run_id':38083079741,'artifact_id':11681138053,'frame':1856,'pixels':57344,'differences':0,'source':'docs/QA08-NATIVE-STOCK-CENTER-PARITY-20261010.md'},
        'recording':{'run_id':38089655141,'artifact_id':11683697184,'guest_frames':'2100..2699','source':'media/showcase/2026-10-10/recruitment/continuous/README.md'}
       },
       'disclosure':'Grid and bar illustrations are editorial, not PPU pixels or CRC values. Zero differences is a bounded same-frame Original source-centre result. CRC identity is capture non-interference on this native route; neither is a complete-game release certificate.',
       'outputs':files}
    (out/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
