#!/usr/bin/env python3
"""Actual project-code pipeline, ending in real continuous native gameplay.

Stages show linked build artifacts and separate real host glue, not a fake
line-by-line transformation of a 65816 function into invented C.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,re
from PIL import Image,ImageDraw,ImageFont

W,H,FPS,N=1920,1080,30,270
BG='#091321';CYAN='#65e5d4';GOLD='#f5bd71';WHITE='#f6f8ff';MUTED='#a6bbc9';BLUE='#a5c6ff'
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
VIDEO='media/showcase/2026-10-10/recruitment/continuous/ur-native-2p-clean-600f.mp4'
VIDEO_SHA='182ef43ccf34f501dea4051312e71bf4d974a53dc6634cd98a5cbf3fae8ac130'
ROOT='reference/imported/reverse-engineering/baldosa-uniracers-recomp/'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(s,bold=False,mono=False):return ImageFont.truetype(MONO if mono else B if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
def tx(d,x,y,s,sz=35,c=WHITE,bold=False,mono=False):
    d.text((x,y),s,fill=c,font=font(sz,bold,mono))
def panel(d,xy,size,title,lines,colour):
    x,y=xy;w,h=size
    d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill='#112a3e',outline=colour,width=3)
    tx(d,x+30,y+22,title,25,colour,True)
    for i,(s,col) in enumerate(lines):tx(d,x+36,y+88+52*i,s,27,col,False,True)

def editorial_base(n):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,12),fill=CYAN)
    tx(d,95,62,'UR-RECOMP / INSIDE THE NATIVE RECOMPILER',29,CYAN,True)
    tx(d,95,1013,'VERIFIED PROJECT SOURCE + GENUINE NATIVE GAMEPLAY  /  NO INVENTED INSTRUCTION TRANSLATION',19,MUTED)
    tx(d,1700,58,f'{n+1:03d}',25,GOLD,True)
    return im,d
def stage(n):
    t=n/FPS;im,d=editorial_base(n)
    if t<1.8:
        tx(d,94,148,'01 / ORIGINAL 65816 PROGRAM',63,WHITE,True)
        tx(d,99,244,'Source-mapped behaviour from the US ROM',29,MUTED)
        panel(d,(145,349),(1630,488),'CARTRIDGE ADDRESS / NAMED RECONSTRUCTION',[
           ('80:8881    20 C6 AC  /  MainLoop',GOLD),
           ('            JSR $ACC6',CYAN),
           ('            calls MainMenu_Draw',WHITE),
           ('            returns at $8884',MUTED),
           ('            original USA retail ROM',BLUE)],CYAN)
        tx(d,151,864,'Actual instruction bytes validated directly from USA retail ROM.',25,GOLD)
    elif t<3.6:
        tx(d,94,148,'02 / ADDRESSES BECOME RECOMP INPUT',54,WHITE,True)
        tx(d,99,244,'Exact MainLoop entry from Baldosa recomp/symbols.toml',29,MUTED)
        panel(d,(145,343),(1628,533),'REAL RECOMPILER CONFIGURATION',[
            ('[[func]]',GOLD),
            ('name = "MainLoop"',WHITE),
            ('addr = "8881"',WHITE),
            ('bank = 0',WHITE),
            ('emit = true',CYAN),
            ('entry_m = 1  /  entry_x = 0',BLUE)],CYAN)
    elif t<5.6:
        tx(d,94,147,'03 / AOT C + NATIVE FRAME DRIVER',56,WHITE,True)
        tx(d,100,245,'Actual MainLoop generated C and distinct native host frame driver',29,MUTED)
        panel(d,(112,338),(840,532),'GENUINE GENERATED C / MAINLOOP M1X0',[
            ('L_8881_M1X0:',GOLD),
            ('  cpu_trace_block(cpu, 0x008881);',WHITE),
            ('  cpu->cycles += 6;',WHITE),
            ('  ... [omitted C] ...',MUTED),
            ('  case 2: _r =',WHITE),
            ('    MainMenu_Draw_M1X0(cpu);',CYAN)],CYAN)
        panel(d,(968,338),(840,532),'ACTUAL NATIVE HOST C',[
            ('void GameRunOneFrame(void)',BLUE),
            ('{',WHITE),
            ('    snes_beam_frame_driver_',WHITE),
            ('        run_frame();',WHITE),
            ('}',WHITE)],GOLD)
        tx(d,122,899,'Pinned Baldosa bank00_part01_v2.c. Host driver is separate code.',25,GOLD)
    return im
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--outdir',type=Path,required=True)
    a=ap.parse_args();root=a.repo_root; out=a.outdir;out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['python3',str(root/'tools/showcase/verify_mainloop_codegen.py'),'--repo-root',str(root),'--out',str(out/'04-mainloop-bytecode-evidence.json')],check=True,stdout=subprocess.DEVNULL)
    v=root/VIDEO
    assert v.exists() and sha(v)==VIDEO_SHA,'Continuous native gameplay source SHA mismatch'
    symbols=root/(ROOT+'recomp/symbols.toml')
    source=symbols.read_text()
    assert re.search(r'\[\[func\]\]\s*name = "MainLoop"\s*addr = "8881"\s*bank = 0\s*emit = true\s*entry_m = 1\s*entry_x = 0',source)
    driver=root/(ROOT+'src/game_rtl.c')
    assert re.search(r'void GameRunOneFrame\(void\)\s*\{\s*snes_beam_frame_driver_run_frame\(\);\s*\}',driver.read_text())
    inventory=root/(ROOT+'src/gen/.snesrecomp-cache.json')
    cache=json.loads(inventory.read_text())
    assert 'bank00_part01_v2.c' in cache['bank_outputs']['00']
    # Decode 102 genuine footage frames from the 60 fps master with integer
    # temporal decimation to 30 fps. No interpolation or simulated gameplay.
    rd=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-ss','2','-i',str(v),'-vf','fps=30','-frames:v','102','-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE)
    dest=out/'04-machine-code-to-native.mp4'
    wr=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],stdin=subprocess.PIPE)
    source_frame_bytes=W*H*3
    try:
        for n in range(N):
            if n<168:
                im=stage(n)
            else:
                raw=rd.stdout.read(source_frame_bytes)
                assert len(raw)==source_frame_bytes,'Continuous video decoder exhausted'
                im=Image.frombytes('RGB',(W,H),raw)
                d=ImageDraw.Draw(im)
                d.rectangle((0,0,W,128),fill='#07121e')
                tx(d,82,23,'04 / REAL NATIVE EXECUTION',48,WHITE,True)
                tx(d,90,82,'Guest-run recording • 30fps selection from genuine 60fps SDL capture',24,CYAN)
            if n==165 or n==207:im.save(out/('04-machine-code-to-native-keyframe-'+str(n)+'.png'))
            wr.stdin.write(im.tobytes())
    finally:
        wr.stdin.close()
        rd.stdout.close()
    assert wr.wait()==0,'MP4 encoding failed'
    assert rd.wait()==0,'Native footage input failed'
    details=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(dest)]))['streams'][0]
    assert (int(details['width']),int(details['height']),details['r_frame_rate'],int(details['nb_frames']))==(W,H,'30/1',N)
    report={'clip':dest.name,'sha256':sha(dest),'bytes':dest.stat().st_size,'fps':FPS,'frames':N,'seconds':9,'size':[W,H],
      'mapping':{'source_address':'80:8881','symbol':'MainLoop','source':ROOT+'recomp/symbols.toml',
       'generated_code_inventory':ROOT+'src/gen/.snesrecomp-cache.json','real_host_c':ROOT+'src/game_rtl.c',
       'same_function_65816':'80:8881 20 C6 AC JSR $ACC6',
       'upstream_generated_C':'gamesbyian/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101:src/gen/bank00_part01_v2.c',
       'upstream_generated_C_blob_sha1':'cc9ef833a5c7c0809aaab53ea00c182158241b83',
       'generated_C_exhibit':'media/showcase/2026-10-10/technical-motion/mainloop-aot-source-exhibit.txt',
       'ROM_opcode_gate':'04-mainloop-bytecode-evidence.json'},
      'input_video':{'path':VIDEO,'sha256':VIDEO_SHA,'original_guest_frame_range':[2100,2699],
         'original_fps':60,'output_fps':30,'selection':'integer decimation, no interpolated gameplay'},
      'source_sha256':{p:sha(root/p) for p in [ROOT+'recomp/symbols.toml',ROOT+'src/game_rtl.c',ROOT+'src/gen/.snesrecomp-cache.json','media/showcase/2026-10-10/technical-motion/mainloop-aot-source-exhibit.txt']},
      'source_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
      'limits':'This clip verifies the exact ROM MainLoop instruction and displays actual C generated for that same function in the pinned Baldosa guest; code omitted between displayed lines is labelled. Native host C is a distinct adapter. The genuine gameplay comes from previously accepted continuous native footage. No whole-game original/native equivalence is implied.'}
    (out/'04-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
