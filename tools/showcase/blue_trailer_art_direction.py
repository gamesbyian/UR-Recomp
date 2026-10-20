#!/usr/bin/env python3
"""Unified Uniracers-inspired blue editorial frame system.

All lettering and drawings below are NEW editorial artwork, not extracted
gameplay or a claim of original box-art authorship. Game captures remain
source-qualified in the parent editor. Inspired by 1994 retail-package
blue/lavender grounds, flamboyant rainbow tubular track, contrasting yellow
lettering and glossy red/chrome/black-wheel unicycle.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H=1920,1080
BLUE=(72,121,193)
PALE=(129,173,218)
CREAM=(255,240,182)
YELLOW=(255,215,54)
INK=(29,32,67)
MAGENTA=(179,46,146)
RED=(245,59,50)
GREEN=(57,209,96)
CYAN=(84,225,228)
PURPLE=(94,66,160)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def ft(n,bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,n)

def track_footer(im, offset=0):
    """A fresh painterly tubular track + stylized unicycle illustration."""
    d=ImageDraw.Draw(im)
    pts=[]
    for x in range(-25,W+26,4):
        u=(x+offset)/W
        y=960+54*math.sin(u*math.pi*3.4)+18*math.sin(u*math.pi*7.5)
        pts.append((x,int(y)))
    for width,color,dy in [
       (150,INK,29),(140,PURPLE,14),(128,RED,1),
       (104,GREEN,-11),(77,YELLOW,-21),(51,PURPLE,-26),
       (31,CYAN,-33),(9,(234,247,242),-44)]:
        d.line([(x,y+dy) for x,y in pts],fill=color,width=width,joint="curve")
    # new glossy rolling rider motif, editorial drawing, not the copyrighted art
    x,y=1590,845
    d.ellipse((x-91,y-95,x+96,y+91),fill=INK)
    d.ellipse((x-76,y-83,x+83,y+75),fill=(20,23,39),outline=(179,197,220),width=8)
    d.ellipse((x-58,y-64,x+65,y+59),fill=(70,79,91),outline=(220,235,246),width=5)
    d.ellipse((x-22,y-28,x+32,y+27),fill=(201,211,220),outline=(249,252,255),width=5)
    for a in range(12):
        rad=a*math.pi/6
        d.line((x,y-4,x+61*math.cos(rad),y-4+61*math.sin(rad)),fill=(212,221,232),width=3)
    d.polygon([(x-20,y-24),(x+24,y-27),(x+11,y-194),(x-31,y-195)],fill=RED)
    d.ellipse((x-39,y-212,x+10,y-188),fill=(243,103,79))
    d.ellipse((x-112,y-254,x+90,y-212),fill=(25,28,44),outline=(163,179,211),width=4)
    d.ellipse((x-97,y-249,x+30,y-237),fill=(100,115,141))
    # light streaks and confetti
    for cx,cy,col,r in [(163,120,RED,16),(360,135,MAGENTA,8),
        (1785,192,YELLOW,12),(1160,202,GREEN,10),(1350,138,CYAN,8)]:
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=col)

def canvas():
    im=Image.new("RGB",(W,H),BLUE)
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        c=tuple(int(BLUE[i]*(1-t*0.25)+PALE[i]*(t*0.25)) for i in range(3))
        d.line((0,y,W,y),fill=c)
    # blue-paper / purple panel shape, broad sweeping geometry
    d.ellipse((-800,-500,1050,1100),outline=(98,143,204),width=15)
    d.arc((-800,-550,1740,1600),10,180,fill=(101,94,171),width=9)
    track_footer(im)
    return im

def title(d,title,deck=None):
    # Subtle chunky three-step shadows without a false official logo
    f=ft(82,True)
    y=94
    for dx,dy,color in [(10,14,PURPLE),(6,9,INK),(3,5,(149,65,97)),(0,0,YELLOW)]:
        d.text((123+dx,y+dy),title,font=f,fill=color,stroke_width=2,stroke_fill=INK)
    if deck:
        d.text((133,224),deck,font=ft(31),fill=CREAM)

def round_panel(d,bounds,fill=(50,84,148),outline=CREAM):
    d.rounded_rectangle(bounds,radius=35,fill=fill,outline=outline,width=5)

def card(kind):
    im=canvas();d=ImageDraw.Draw(im)
    if kind=="windows":
        title(d,"THE WINDOWS BUILD","What the current native tests actually demonstrate")
        rows=[
          ("CREATE A RACER","Named player profiles"),
          ("RACE IN TWO-PLAYER","Native result and match publishing"),
          ("REOPEN RECORDS","Entries survive a fresh process"),
        ]
        for i,(heading,body) in enumerate(rows):
            y=330+i*142
            round_panel(d,(128,y,1455,y+123))
            d.text((165,y+15),f"0{i+1}",font=ft(57,True),fill=YELLOW)
            d.text((285,y+13),heading,font=ft(41,True),fill=CREAM)
            d.text((288,y+68),body,font=ft(25),fill=(211,230,255))
        d.text((140,786),"Verified scripted journeys. New footage is still being captured.",font=ft(28),fill=CREAM)
    elif kind=="4k":
        title(d,"A REAL 4K FRAMEBUFFER","Verified SDL readback from native Original-mode rendering")
        round_panel(d,(142,324,1408,716))
        d.text((192,363),"3840 × 2160",font=ft(111,True),fill=YELLOW)
        d.text((194,530),"8,294,400 checked output pixels",font=ft(39,True),fill=CREAM)
        d.text((198,606),"One verified frame, not a 4K gameplay recording",font=ft(26),fill=(211,230,255))
    elif kind=="cta":
        title(d,"HELP FINISH THE REBUILD","The native game runs. Significant work remains.")
        round_panel(d,(126,335,1477,726))
        for n,s in enumerate([
            "C++ and reverse engineering",
            "Character art and animation",
            "Gameplay testing and reconstruction evidence",
        ]):
            d.ellipse((184,393+n*93,208,417+n*93),fill=YELLOW)
            d.text((232,374+n*93),s,font=ft(37,True),fill=CREAM)
        d.text((142,791),"github.com/gamesbyian/UR-Recomp",font=ft(40,True),fill=INK)
    else:raise ValueError(kind)
    return im

TITLES={
 "reveal":("THE WORLD OPENS","Original 256-column centre → genuine 342-column world"),
 "race":("TWO PLAYERS. ONE REAL GAME.","Continuous native gameplay, Original-wide presentation"),
 "code":("FROM 65816 TO NATIVE C","Source machine instructions and corresponding generated code"),
 "raster":("ANATOMY OF THE ORIGINAL RASTER","Real captured pixels, inspected frame by frame"),
 "parity":("EXACT CENTRE PIXEL COMPARISON","57,344 source pixels checked at the documented checkpoint"),
 "art":("RECONSTRUCTING THE RACERS","Early 4× studies. Character likeness still needs work"),
 "animation":("THE ORIGINAL ANIMATIONS","Recovering the source pose sequence"),
 "art_p2":("CHARACTER WORK IN PROGRESS","Experimental studies, not approved final artwork"),
 "modern":("THE MODERN FRONTEND","October 10 source capture; more recent states require new footage"),
}
def frame(kind):
    if kind not in TITLES:raise ValueError(kind)
    im=canvas();d=ImageDraw.Draw(im)
    a,b=TITLES[kind]
    title(d,a,b)
    # Inset is intentionally the only area used for documentary footage;
    # any old grey titles/caption raster sit inside a clearly editorial card.
    round_panel(d,(140,290,1775,848),fill=(35,55,99),outline=CREAM)
    return im

def produce(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for kind in ["windows","4k","cta"]:
        card(kind).save(out/f"{kind}.png")
    for kind in TITLES:
        frame(kind).save(out/f"{kind}-frame.png")
    print("Produced",len(TITLES)+3,"blue editorial assets")

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    produce(p.parse_args().out)
