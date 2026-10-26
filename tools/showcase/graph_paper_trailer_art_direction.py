#!/usr/bin/env python3
"""Light graph-paper editorial art for Uniracers recruitment film.

All artwork panels use source sketches without altering their fine pen strokes.
Do not represent technical editorial footage as actual gameplay. Reference
images are used in monochrome; footage compositing is done by parent editor.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math
import argparse

W,H=1920,1080
PAPER=(253,252,247)
INK=(32,36,39)
SLATE=(78,86,92)
RED=(176,53,43)
GOLD=(194,131,50)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TITLES={
 "reveal":("WIDESCREEN, FOR REAL","256 COLUMNS  →  342 COLUMNS"),
 "race":("TWO RACERS. ONE TRACK.","NATIVE ORIGINAL / FULL TWO-PLAYER RASTER"),
 "code":("65816 TO NATIVE C","ORIGINAL CODE / VERIFIED TRANSLATION"),
 "raster":("RASTER ARCHAEOLOGY","SOURCE PIXELS / UNDER THE MICROSCOPE"),
 "parity":("PIXEL-EXACT CENTRE","57,344 PIXELS / ZERO DIFFERENCES AT CHECKPOINT"),
 "art":("REBUILDING THE RACERS","EARLY 4× ART / NOT YET APPROVED"),
 "animation":("THE ORIGINAL MOTION","POSE STUDIES / SOURCE ANIMATIONS"),
 "art_p2":("CHARACTER RECONSTRUCTION","EXPERIMENTAL ART / VISUAL REVIEW ONGOING"),
 "modern":("NATIVE FRONTEND RESEARCH","OLDER CAPTURE / NEWER STATES NOT FILMED"),
}
def font(size,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,size)
def label(d,text,xy,size=30,fill=INK,bold=False,max_width=None):
    x,y=xy
    f=font(size,bold)
    while max_width and size>15 and d.textbbox((0,0),text,font=f)[2]>max_width:
        size-=2; f=font(size,bold)
    d.text((x,y),text,font=f,fill=fill)
def base():
    im=Image.new("RGB",(W,H),PAPER)
    d=ImageDraw.Draw(im)
    for x in range(0,W,24):
        d.line((x,0,x,H),fill=(240,238,231),width=1)
    for y in range(0,H,24):
        d.line((0,y,W,y),fill=(240,238,231),width=1)
    for x in range(0,W,120):
        d.line((x,0,x,H),fill=(227,226,218),width=1)
    for y in range(0,H,120):
        d.line((0,y,W,y),fill=(227,226,218),width=1)
    return im
def ink_overlay(im,source,crop,xy,width,opacity=1.0):
    """Preserve fine ink, hatching, construction lines; remove white field."""
    crop_im=Image.open(source).convert("RGB").crop(crop)
    height=round(crop_im.height*width/crop_im.width)
    crop_im=crop_im.resize((width,height),Image.Resampling.LANCZOS)
    gray=ImageOps.grayscale(crop_im)
    # keep even very pale pencil; paper tone becomes transparent
    alpha=gray.point(lambda p: round(min(245,max(0,(245-p)*3.0*opacity))))
    black=Image.new("RGB",crop_im.size,(24,26,27))
    im.paste(black,xy,alpha)
def footer(im,track):
    """Use the owner's complete long continuous track, edge-to-edge.

    Crop only empty paper above/below the drawing, never trim the horizontal
    ends or redraw course geometry. Preserve all original construction strokes,
    pen hatch and the authentic unicycle. This intentionally replaces the old
    hand-computed left-side continuation.
    """
    source=Image.open(track).convert("RGB")
    gray=ImageOps.grayscale(source)
    # The owner's updated reference has very pale graph guides. Detect only
    # meaningful pencil/ink mass to avoid removing the subtle drawing detail.
    histogram=[]
    for y in range(source.height):
        band=gray.crop((0,y,source.width,y+1))
        n=sum(band.histogram()[:205])
        histogram.append(n)
    significant=[y for y,count in enumerate(histogram) if count >= max(15, source.width//220)]
    if not significant:
        raise ValueError("Long footer source has no recognizable track strokes")
    top=max(0,min(significant)-12)
    bottom=min(source.height,max(significant)+13)
    # Keep the entire drawing from left to right. Never stretch its aspect.
    artwork=source.crop((0,top,source.width,bottom))
    target_h=round(artwork.height*W/artwork.width)
    artwork=artwork.resize((W,target_h),Image.Resampling.LANCZOS)
    if target_h>300:
        raise ValueError("Long footer is too tall after whitespace crop")
    # Entire original paper image is placed flush at the bottom. It is
    # already white graph paper; retaining its original lines avoids losing
    # fine gray drafting detail via thresholded masks.
    im.paste(artwork,(0,H-target_h))

def header(im,logo,title,deck,small="UNIRACERS / ENGINEERING NOTES"):
    ink_overlay(im,logo,(60,213,1480,693),(89,28),688)
    d=ImageDraw.Draw(im)
    d.line((800,48,800,241),fill=(150,145,129),width=2)
    label(d,small,(848,47),20,RED,bold=True,max_width=920)
    label(d,title,(839,94),68,INK,bold=True,max_width=995)
    label(d,deck,(842,187),28,SLATE,max_width=990)
    d.line((100,267,1820,267),fill=(119,115,103),width=2)
    for x,y in [(104,267),(1818,267)]:
        d.ellipse((x-5,y-5,x+5,y+5),outline=RED,width=2)
def card(kind,logo,track):
    im=base()
    footer(im,track)
    if kind=="windows":
        header(im,logo,"WINDOWS. NATIVE.","A DOCUMENTED PLAYER JOURNEY","PLATE 01 / VERIFIED WORK")
        d=ImageDraw.Draw(im)
        rows=[
            ("01","CREATE A RACER","Named profiles / native frontend"),
            ("02","RUN TWO-PLAYER","Results recorded from guest gameplay"),
            ("03","REOPEN RECORDS","Persistence checked across a new process")
        ]
        for i,(num,title,detail) in enumerate(rows):
            y=325+i*147
            d.rounded_rectangle((124,y,1783,y+125),radius=13,fill=(255,255,250),outline=(146,149,143),width=2)
            d.line((260,y+16,260,y+108),fill=(184,183,171),width=2)
            label(d,num,(150,y+23),52,RED,True)
            label(d,title,(299,y+12),48,INK,True)
            label(d,detail,(302,y+73),28,SLATE)
        label(d,"Scripted Windows evidence / final hardware release QA remains open.",(128,790),26,RED,max_width=1500)
    elif kind=="4k":
        header(im,logo,"THE 4K READBACK","A REAL FRAMEBUFFER MEASUREMENT","PLATE 02 / SOURCE QUALIFIED")
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((124,325,1790,738),radius=16,fill=(255,255,250),outline=(146,149,143),width=2)
        label(d,"3840 × 2160",(175,355),139,INK,True,max_width=1510)
        d.line((174,562,1667,562),fill=RED,width=3)
        label(d,"8,294,400 SOURCE-CHECKED OUTPUT PIXELS",(179,598),43,RED,True,max_width=1510)
        label(d,"One measured Original-mode frame. Not a filmed 4K gameplay sequence.",(128,782),28,SLATE,max_width=1510)
    elif kind=="cta":
        header(im,logo,"JOIN THE REBUILD","A PLAYABLE NATIVE GAME / WORK STILL AHEAD","PLATE 03 / OPEN INVITATION")
        d=ImageDraw.Draw(im)
        skills=["C++ / REVERSE ENGINEERING","CHARACTER ART / ANIMATION","GAMEPLAY QA / SOURCE EVIDENCE"]
        for i,item in enumerate(skills):
            y=343+i*108
            d.ellipse((149,y+10,172,y+33),outline=RED,width=3)
            label(d,item,(206,y),51,INK,True,max_width=1500)
        d.rounded_rectangle((127,710,1632,798),radius=15,fill=(253,252,247),outline=RED,width=3)
        label(d,"github.com/gamesbyian/UR-Recomp",(162,727),45,RED,True,max_width=1390)
    else:
        raise ValueError(kind)
    return im
def frame(kind,logo,track):
    if kind not in TITLES:raise ValueError(kind)
    title,deck=TITLES[kind]
    im=base()
    footer(im,track)
    header(im,logo,title,deck,"MOTION PLATE / SOURCE-GROUNDED")
    d=ImageDraw.Draw(im)
    # Exact 1120x630 safe area matches the parent FFmpeg video overlay.
    d.rounded_rectangle((389,260,1531,912),radius=18,fill=(253,252,247),outline=INK,width=5)
    d.rectangle((400,270,1519,899),fill=(36,40,45))
    # Only preview image, film compositor paints actual source footage here.
    label(d,"[ NATIVE FOOTAGE / SOURCE-QUALIFIED MOTION ]",(441,562),27,(230,228,215),True,max_width=1015)
    label(d,"EDIT FRAME", (112,330),26,RED,True)
    d.line((138,369,355,369),fill=RED,width=2)
    return im
def produce(out,logo,track):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    for kind in ("windows","4k","cta"):
        card(kind,logo,track).save(out/(kind+".png"))
    for kind in TITLES:
        frame(kind,logo,track).save(out/(kind+"-frame.png"))
    print("Rendered", len(TITLES)+3, "coherent graph-paper art boards")
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",required=True)
    a.add_argument("--logo",required=True)
    a.add_argument("--track",required=True)
    q=a.parse_args()
    produce(q.out,q.logo,q.track)