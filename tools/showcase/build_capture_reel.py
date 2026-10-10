#!/usr/bin/env python3
"""Construct a provenance-labelled video solely from captured Baldosa CI frame samples.

No guest execution is synthesized. Motion is limited to editorial camera moves and
transitions between separately captured source frames. Source game audio is not used.
"""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS = 1280, 720, 24, 24
INK = '#080f1b'
TEXT = '#f5f8fc'
MUTED = '#b9cad4'
CYAN = '#5be4d1'
AMBER = '#f9b657'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):
            h.update(b)
    return h.hexdigest()

def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,size)

def from_pam(content):
    end=content.index(b'ENDHDR\n')+len(b'ENDHDR\n')
    header=content[:end].decode('ascii')
    props=dict(line.split(' ',1) for line in header.splitlines() if ' ' in line)
    w,h,depth=(int(props[x]) for x in ('WIDTH','HEIGHT','DEPTH'))
    assert props['TUPLTYPE']=='RGB_ALPHA' and depth==4 and int(props['MAXVAL'])==255
    assert len(content)-end==w*h*depth
    # The source PAM alpha channel is all zero, but RGB contains the real PPU pixels.
    return Image.frombytes('RGBA',(w,h),content[end:]).convert('RGB')

def load(z,name):
    return from_pam(z.read(name))

def draw_t(draw, xy, txt, size, fill=TEXT, bold=False, anchor=None):
    draw.text(xy,txt,font=font(size,bold),fill=fill,anchor=anchor,stroke_width=0)

def game(draw, canvas, source, rect, emphasize=None):
    x,y,w,h=rect
    # Crop only mathematically requested portions; all game pixels remain nearest-neighbor.
    sw,sh=source.size
    factor=min(w/sw,h/sh)
    rw,rh=int(sw*factor),int(sh*factor)
    pic=source.resize((rw,rh),Image.Resampling.NEAREST)
    bx,by=x+(w-rw)//2,y+(h-rh)//2
    canvas.paste(pic,(bx,by))
    draw.rectangle([bx-1,by-1,bx+rw,by+rh],outline='#3b7188',width=2)
    if emphasize and sw==342:
        d1=int(43*rw/sw)
        d2=int(299*rw/sw)
        draw.line([bx+d1,by,bx+d1,by+rh],fill=CYAN,width=3)
        draw.line([bx+d2,by,bx+d2,by+rh],fill=CYAN,width=3)
    return bx,by,rw,rh

def panel(draw,title,sub,kicker='ACTUAL BALDOSA CI CAPTURE'):
    draw_t(draw,(65,41),kicker,18,CYAN,True)
    draw_t(draw,(65,78),title,42,TEXT,True)
    draw_t(draw,(65,135),sub,21,MUTED)

def base_frame(t):
    canvas=Image.new('RGB',(W,H),INK)
    d=ImageDraw.Draw(canvas)
    d.rectangle([0,0,W-1,H-1],outline='#233a50',width=2)
    d.line([0,0,W,0],fill=CYAN,width=7)
    d.line([48,666,W-48,666],fill='#254357',width=2)
    draw_t(d,(62,680),'UR-RECOMP  /  EVIDENCE-BASED PROGRESS REEL',13,MUTED,True)
    draw_t(d,(W-63,680),'OCT 2026   •   NOT A BETA DEMO',13,AMBER,True,anchor='ra')
    return canvas,d

def generate_movie(z,out):
    source=load(z,'baldosa-fixed-source/ur-baldosa-original-source-001856.pam')
    original_title=load(z,'baldosa-fixed-source/ur-baldosa-original-source-000400.pam')
    two=[load(z,f'baldosa-ws342-live-2p/ur-baldosa-ws342-{n:06d}.pam') for n in (1808,1824,1840,1856,1872,1888)]
    one=[load(z,f'baldosa-ws342-live-1p/ur-baldosa-ws342-{n:06d}.pam') for n in (1536,1552,1568,1584,1600,1616)]
    wide=two[3]
    # Strict source-identity check for a central 256x224 crop at the same native frame.
    assert wide.crop((43,0,299,224)).tobytes()==source.tobytes(), 'source/native centre mismatch'
    ffmpeg=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-', '-an','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
    try:
        for i in range(SECONDS*FPS):
            t=i/FPS
            c,d=base_frame(t)
            if t<3.5:
                # Fade in captured cartridge artwork; contemporary project text remains editorial.
                original_title.thumbnail((690,530),Image.Resampling.NEAREST)
                art=original_title.resize((580,508),Image.Resampling.NEAREST)
                c.paste(art,(640,124))
                d.rectangle([640,124,1220,633],outline='#386073',width=2)
                draw_t(d,(68,150),'A SNES CLASSIC,',40,AMBER,True)
                draw_t(d,(68,210),'RECONSTRUCTED.',44,TEXT,True)
                draw_t(d,(70,298),'Uniracers / Unirally',26,MUTED)
                draw_t(d,(70,348),'Native recompilation',24,CYAN,True)
                draw_t(d,(70,386),'Original-driven behavior',24,CYAN,True)
                draw_t(d,(70,424),'Modern presentation research',24,CYAN,True)
            elif t<8.5:
                panel(d,'SAME ORIGINAL PIXELS.','Side-by-side native evidence at guest frame 1856')
                game(d,c,source,(60,195,510,354))
                game(d,c,wide,(614,195,600,354),emphasize=True)
                draw_t(d,(300,571),'ORIGINAL 256 × 224',21,TEXT,True,anchor='mm')
                draw_t(d,(910,571),'WIDER 342 × 224',21,CYAN,True,anchor='mm')
                draw_t(d,(640,616),'Central 256 × 224 region matches exactly  •  43 added source pixels per side',18,MUTED,anchor='mm')
            elif t<13.5:
                n=min(5,int((t-8.5)*1.2))
                panel(d,'TWO LOCAL RACERS.','Guest-produced 2P split-screen frames, sampled 16 frames apart')
                game(d,c,two[n],(115,205,1050,410))
                draw_t(d,(640,625),f'ACTUAL SOURCE FRAME  {1808+16*n}    /    DEVELOPMENT CAPTURE',19,AMBER,True,anchor='mm')
            elif t<17.5:
                n=min(5,int((t-13.5)*1.5))
                panel(d,'ORIGINAL RENDERING, WIDER WORLD.','1P source-backed scene, sampled at successive native frame IDs')
                game(d,c,one[n],(115,205,1050,410))
                draw_t(d,(640,625),f'ACTUAL SOURCE FRAME  {1536+16*n}    /    DEVELOPMENT CAPTURE',19,AMBER,True,anchor='mm')
            elif t<20.5:
                panel(d,'VERIFIED BUILDING BLOCKS.','Implementation work already captured by the native acceptance pipeline')
                for j,(a,b) in enumerate([('342-pixel logical world','Native widescreen experiments'),('1P + 2P guest frames','Actual runtime captures'),('4× Original composition','Source-faithful pixel fallback')]):
                    x,y=70,218+j*118
                    d.rounded_rectangle([x,y,1210,y+96],radius=12,fill='#14283b',outline='#306175',width=2)
                    draw_t(d,(x+26,y+17),a,29,TEXT,True)
                    draw_t(d,(x+27,y+59),b,18,MUTED)
            else:
                draw_t(d,(640,156),'HELP BUILD THE REST.',51,AMBER,True,anchor='mm')
                draw_t(d,(640,247),'UR-RECOMP',73,TEXT,True,anchor='mm')
                draw_t(d,(640,346),'A modern Uniracers remaster and',27,MUTED,anchor='mm')
                draw_t(d,(640,386),'a reproducible technical reference.',27,MUTED,anchor='mm')
                d.rounded_rectangle([168,483,1112,558],radius=16,fill='#16586a',outline=CYAN,width=3)
                draw_t(d,(640,519),'github.com/gamesbyian/UR-Recomp',29,TEXT,True,anchor='mm')
                draw_t(d,(640,621),'Experimental capture reel  •  gameplay and presentation remain under QA',18,AMBER,anchor='mm')
            ffmpeg.stdin.write(c.tobytes())
    finally:
        ffmpeg.stdin.close()
        code=ffmpeg.wait()
        if code: raise RuntimeError(f'ffmpeg failed with exit code {code}')
    return {'frame_1856_exact_center_match':True,'run_frames':{'two_player':[1808,1824,1840,1856,1872,1888],'one_player':[1536,1552,1568,1584,1600,1616]}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--zip',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True);args=ap.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    output=args.outdir/'ur-recomp-capture-reel-20261010.mp4'
    with zipfile.ZipFile(args.zip) as z:
        evidence=generate_movie(z,output)
        poster=load(z,'baldosa-ws342-live-2p/ur-baldosa-ws342-001856.pam')
        # Preserve an unretouched raw-frame PNG for a future independent visual comparison.
        poster.save(args.outdir/'native-widescreen-source-frame-1856.png',optimize=True)
    import subprocess as sp
    short=args.outdir/'ur-recomp-342px-comparison-20261010.mp4'
    sp.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','3.5','-t','10',
            '-i',str(output),'-an','-c:v','libx264','-preset','veryfast','-crf','22',
            '-pix_fmt','yuv420p','-movflags','+faststart',str(short)],check=True)
    poster=args.outdir/'ur-recomp-capture-reel-poster.png'
    sp.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','5','-i',str(output),
            '-frames:v','1',str(poster)],check=True)
    pr=sp.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate','-of','json',str(output)],capture_output=True,text=True,check=True)
    probe=json.loads(pr.stdout)
    assert int(probe['streams'][0]['nb_frames'])==SECONDS*FPS
    manifest={
        'title':'UR-Recomp October 10 source-frame progress reel',
        'purpose':'Contributor-facing development evidence, not a demonstration of a finished Windows beta',
        'source_repository':'gamesbyian/UR-Recomp',
        'source_action_run':38083079741,
        'source_artifact_id':11681138053,
        'source_artifact_zip_sha256':sha(args.zip),
        'source_artifact_name':'baldosa-native-spike-evidence',
        'source_content':'Original 256x224, wide 342x224, 1P and 2P original guest frame captures from source PPU / compositor',
        'verified':evidence,
        'encoding':{'size':[W,H],'fps':FPS,'frames':SECONDS*FPS,'seconds':SECONDS,'audio':'none','codec':'H.264 yuv420p'},
        'editorial_disclosure':'Not 60-fps uninterrupted gameplay; frames sampled every 16 native frames. Camera/slide transitions and captions are editorial. No interpolation of gameplay/physics. Not a physical 4K display acceptance.',
        'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [output,short,poster,args.outdir/'native-widescreen-source-frame-1856.png']}
    }
    (args.outdir/'provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(output),'bytes':output.stat().st_size,'source_artifact_zip_sha256':manifest['source_artifact_zip_sha256'],'movie_sha256':manifest['outputs'][output.name]['sha256']}))
if __name__=='__main__':main()
