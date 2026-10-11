#!/usr/bin/env python3
"""Source-raster anatomical animation. REAL source RGB; all guides editorial.

No separate BG/OBJ/HUD planes are claimed: input is an already-composited
native PPU screenshot. This script crops/marks coordinates only.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,N=1920,1080,30,180
BG='#081523'; WHITE='#f2f7fc';CYAN='#60ead6';GOLD='#eab06d'; MUTED='#bbcfdb'
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SOURCE='media/showcase/2026-10-10/native-widescreen-source-frame-1856.png'
SHA='4dd40af5c80aa670de15c474f02c89f8e9ac7b6f689e894e67da66f59a18e79c'
def font(size,bold=False):return ImageFont.truetype(B if bold else R,size)
def txt(d,x,y,text,size=29,ink=WHITE,bold=False):
    d.text((x,y),text,fill=ink,font=font(size,bold))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def render(src,outdir):
    source=Image.open(src).convert('RGB')
    assert source.size==(342,224),source.size
    # Reuse actual raster pixels exclusively, resized with nearest-neighbor.
    image_rect=(228,200,1692,1022);x0,y0,x1,y1=image_rect
    sx=(x1-x0)/342;sy=(y1-y0)/224
    c1=int(x0+43*sx); c2=int(x0+299*sx); mid=int(y0+112*sy)
    centre=source.crop((43,0,299,224))
    centre.save(outdir/'03-actual-source-centre-1856.png')
    source.crop((0,0,43,224)).save(outdir/'03-actual-left-extension-1856.png')
    source.crop((299,0,342,224)).save(outdir/'03-actual-right-extension-1856.png')
    pic=source.resize((x1-x0,y1-y0),Image.Resampling.NEAREST)
    dest=outdir/'03-source-raster-xray.mp4'
    p=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE)
    try:
        for n in range(N):
            t=n/FPS
            im=Image.new('RGB',(W,H),BG);im.paste(pic,(x0,y0))
            d=ImageDraw.Draw(im)
            d.rectangle((0,0,W,10),fill=CYAN)
            txt(d,90,56,'UR-RECOMP / SOURCE RASTER X-RAY',28,CYAN,True)
            txt(d,90,1038,'REAL SOURCE PIXELS  •  EDITORIAL COORDINATE GUIDES  •  NO RECOVERED LAYER MASKS',18,MUTED)
            if t<1.3:
                txt(d,230,122,'ONE REAL 342 × 224 ORIGINAL PPU CAPTURE',40,WHITE,True)
            elif t<3.2:
                # Geometry source: independently verified centre crop at same guest frame.
                tint=Image.new('RGBA',(W,H),(0,0,0,0))
                q=ImageDraw.Draw(tint)
                q.rectangle((x0,y0,c1,y1),fill=(4,16,30,135))
                q.rectangle((c2,y0,x1,y1),fill=(4,16,30,135))
                im=Image.alpha_composite(im.convert('RGBA'),tint).convert('RGB');d=ImageDraw.Draw(im)
                d.rectangle((c1,y0,c2,y1),outline=CYAN,width=7)
                txt(d,165,122,'CENTRE 256 × 224 MATCHES THE FIXED NATIVE IMAGE',35,WHITE,True)
                txt(d,260,948,'57,344 pixels tested independently   /   0 differences',29,CYAN,True)
            elif t<4.7:
                d.rectangle((x0,y0,c1,y1),outline=GOLD,width=7)
                d.rectangle((c2,y0,x1,y1),outline=GOLD,width=7)
                d.line((c1,y0,c1,y1),fill=CYAN,width=5)
                d.line((c2,y0,c2,y1),fill=CYAN,width=5)
                txt(d,178,122,'43 REAL SOURCE COLUMNS ADDED ON EACH SIDE',37,WHITE,True)
                txt(d,245,934,'EXTENSION',25,GOLD,True)
                txt(d,1504,934,'EXTENSION',25,GOLD,True)
            else:
                d.line((x0,mid,x1,mid),fill=GOLD,width=5)
                d.rectangle(image_rect,outline=CYAN,width=5)
                txt(d,190,122,'TWO SPLIT VIEWS / SAME SOURCE COMPOSITE',37,WHITE,True)
                txt(d,230,932,'TOP VIEW',25,CYAN,True)
                txt(d,1470,932,'BOTTOM VIEW',25,GOLD,True)
            if n==97:im.save(outdir/'03-source-raster-xray-keyframe.png')
            p.stdin.write(im.tobytes())
    finally:p.stdin.close()
    assert p.wait()==0
    d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(dest)]))['streams'][0]
    assert (int(d['width']),int(d['height']),d['r_frame_rate'],int(d['nb_frames']))==(W,H,'30/1',N)
    metadata={'clip':'03-source-raster-xray.mp4','sha256':sha(dest),'bytes':dest.stat().st_size,'dimensions':[W,H],'fps':FPS,'frames':N,'seconds':6,
      'source':SOURCE,'source_sha256':SHA,'original_capture_run':38083079741,'original_artifact_id':11681138053,
      'geometry':{'wide':[342,224],'centre_crop_xyxy':[43,0,299,224],'left_extension_x':[0,43],'right_extension_x':[299,342],'split_guide_y':112},
      'independent_comparator':'docs/QA08-NATIVE-STOCK-CENTER-PARITY-20261010.md',
      'disclosure':'Input is one composited source PPU image. Crop and tint are editorial; no independently extracted background, HUD, OBJ, masks, or depth order. Same-frame native fixed/wide centre is independently proven in the cited QA report.'}
    (outdir/'03-provenance.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--outdir',type=Path,required=True)
    a=ap.parse_args();p=a.repo_root/SOURCE
    assert sha(p)==SHA,'Source image SHA mismatch'
    a.outdir.mkdir(parents=True,exist_ok=True)
    print(json.dumps(render(p,a.outdir),indent=2))
if __name__=='__main__':main()
