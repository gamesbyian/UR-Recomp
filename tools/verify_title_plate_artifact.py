#!/usr/bin/env python3
"""Independent ROM-free check of retained *real* Windows SDL title plate pixels.

Input: original GitHub Actions artifact 12327216738 from run 39558777827.
No source/ROM/PE/capture bytes are shipped with this script. This verifies
source-bound capture *consistency*, not hardware, original artwork, or release.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import zipfile
from PIL import Image
import numpy as np

RUN = 39558777827
ARTIFACT = 12327216738
ARTIFACT_SHA256 = '3505c377cb5f06a3a6a3b36ff679ead31f45481ad13086c15eced8e8f598e50f'
HEAD = 'dabda1ae56f099bf4529f44dfdd80316a492328f'
SOURCE = 'a87d02debb237590578fe024e0a895bef6ce67fd'
EXE = '74556a0cad1863fc8e8a656df63995a9a889840dff5b6e954f94e03a8b113d60'
SIZES = {'1024x768': (1024, 768, 256, 9), '1280x720': (1280, 720, 342, 52)}
CASES = ('title-still','title-reduced-still','title-entered-root','title-reduced-entered-root')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exact_log_event(log, prefix, fields):
    """Require exactly one line with exact event identity and required fields."""
    matches=[]
    for line in log.decode('utf-8').splitlines():
        tokens=line.split()
        if not tokens or tokens[0]!=prefix:
            continue
        row={}
        for token in tokens[1:]:
            k,sep,v=token.partition('=')
            if not sep or not k or not v or k in row:
                raise ValueError('malformed/duplicate native event field')
            row[k]=v
        if all(row.get(k)==v for k,v in fields.items()):
            matches.append(row)
    if len(matches)!=1:
        raise ValueError('missing/ambiguous native event '+prefix)
    return matches[0]


def load_case(z,res,case):
    ow,oh,sw,art_x=SIZES[res]
    prefix=f'ur-modern-title-final-sdl-{res}/{case}/'
    receipt=json.loads(z.read(prefix+'readback-receipt.json'))
    p7=z.read(prefix+'probe_first/actual-sdl-drawable.pam')
    png=z.read(prefix+'actual-sdl-drawable.png')
    log=z.read(prefix+'probe_first/native-process.log')
    for key,blob in [('p7_sha256',p7),('png_sha256',png),('native_process_log_sha256',log)]:
        if receipt.get(key)!=digest(blob):
            raise ValueError(f'{res}/{case} {key} mismatch')
    if (receipt.get('source_sha')!=SOURCE or receipt.get('exe_sha256')!=EXE or
        receipt.get('native_semantic_route')!=case or
        receipt.get('native_process_exit')!=0 or
        receipt.get('execution_mode')!='modern' or
        receipt.get('SDL_driver')!='windows' or
        receipt.get('actual_sdl_renderer_output')!=[ow,oh] or
        receipt.get('requested_window_size')!=[ow,oh] or
        receipt.get('visual_approved') is not False or
        receipt.get('release_gate_credit')!=0):
        raise ValueError('receipt source/stage/approval mismatch')
    draw=100 if case.endswith('entered-root') else 40
    if receipt.get('observed_in_draw')!=draw:
        raise ValueError('unexpected SDL capture draw')
    exact_log_event(log,'UR_MODERN_VISUAL_SDL_CAPTURE',
        {'status':'saved','draw':str(draw),'guest_frame':str(draw),
         'output':f'{ow}x{oh}','source':'SDL_RenderReadPixels'})
    if not case.endswith('entered-root'):
        exact_log_event(log,'UR_BALDOSA_MODERN_TITLE',
                        {'painted':'1','raster':f'{sw}x224','host':'modern'})
    else:
        exact_log_event(log,'UR_BALDOSA_MODERN_TITLE',
                        {'entered_root':'1','frame':('60' if case.startswith('title-reduced-') else '74'),'input_owned':'1'})
        exact_log_event(log,'UR_BALDOSA_MODERN_DESTINATION',
                        {'stage':'root','raster':f'{sw}x224'})
    header=(f'P7\nWIDTH {ow}\nHEIGHT {oh}\nDEPTH 4\nMAXVAL 255\n'
            'TUPLTYPE RGB_ALPHA\nENDHDR\n').encode('ascii')
    if not p7.startswith(header) or len(p7)!=len(header)+ow*oh*4:
        raise ValueError('not exact native SDL P7')
    native=np.frombuffer(p7[len(header):],dtype=np.uint8).reshape(oh,ow,4)
    with Image.open(io.BytesIO(png)) as img:
        if img.mode!='RGBA' or img.size!=(ow,oh):
            raise ValueError('PNG not exact expected RGBA')
        converted=np.asarray(img)
    if not np.array_equal(native,converted):
        raise ValueError('PNG differs from actual native SDL P7')
    return native,art_x,sw


def plate(img,source_width,x):
    # Pixel-center sampling, no interpolation or arbitrary image alignment.
    h,w,_=img.shape
    xs=np.floor((np.arange(238)+x+.5)*w/source_width).astype(int)
    ys=np.floor((np.arange(81)+27+.5)*h/224).astype(int)
    if xs.min()<0 or xs.max()>=w or ys.min()<0 or ys.max()>=h:
        raise ValueError('plate source bounds invalid')
    return img[np.ix_(ys,xs)]



def prompt_only_motion(mask, output_height):
    """Admit only changed title pixels in the captured lower prompt band.

    The native title presenter places the prompt at source rows 200..211.
    Map *actual* output pixel centers back to the 224-row source; avoid
    hand-tuned 720p/768p output bboxes or a blanket bottom-screen crop.
    This checks the archived still/reduced-still pair, not every possible
    animation or a physical display's reduced-motion behavior.
    """
    if mask.ndim != 2 or mask.shape[0] != output_height:
        raise ValueError('invalid title motion mask geometry')
    changed_rows = np.flatnonzero(np.any(mask, axis=1))
    if changed_rows.size == 0:
        raise ValueError('normal/reduced title prompt did not change')
    source_rows = np.floor((changed_rows + .5) * 224 / output_height).astype(int)
    if np.any((source_rows < 200) | (source_rows >= 212)):
        raise ValueError('reduced-motion difference escaped title prompt band')


def verify(path):
    data=path.read_bytes()
    if digest(data)!=ARTIFACT_SHA256:
        raise ValueError('original Windows artifact SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or len(z.namelist())!=34:
            raise ValueError('invalid original artifact members')
        frames={}
        for res in SIZES:
            for case in CASES:
                frames[res,case]=load_case(z,res,case)
    summaries={}
    plate_hashes=[]
    for case in CASES[:2]:
        a,ax,aw=frames['1024x768',case]
        b,bx,bw=frames['1280x720',case]
        pa,pb=plate(a,aw,ax),plate(b,bw,bx)
        if not np.array_equal(pa,pb):
            raise ValueError('actual 4:3/16:9 retail plate pixels differ')
        if np.count_nonzero(pa[:,:,:3])<5000 or len(np.unique(pa.reshape(-1,4),axis=0))<32:
            raise ValueError('retail plate is blank or insufficiently varied')
        summaries[case]={'exact_rgba_pixels':238*81,'plate_sha256':digest(pa.tobytes())}
        plate_hashes.append(summaries[case]['plate_sha256'])
    if len(set(plate_hashes))!=1:
        raise ValueError('reduced-motion title plate differs')
    motion={}
    for res in SIZES:
        still=frames[res,'title-still'][0]
        reduced=frames[res,'title-reduced-still'][0]
        mask=np.any(still!=reduced,axis=2)
        prompt_only_motion(mask, still.shape[0])
        ys,xs=np.where(mask)
        if not np.array_equal(frames[res,'title-entered-root'][0],
                              frames[res,'title-reduced-entered-root'][0]):
            raise ValueError('normal/reduced root differs')
        motion[res]={'title_changed_pixels':int(mask.sum()),
                     'title_difference_bbox_xyxy':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
                     'root_identical_rgba':True}
    return {'schema':'ur-title-plate-cross-aspect-real-SDL/1',
            'workflow_run_id':RUN,'artifact_id':ARTIFACT,'artifact_sha256':ARTIFACT_SHA256,
            'integration_head':HEAD,'native_reported_source_sha':SOURCE,
            'native_executable_sha256':EXE,'actual_windows_cases_checked':8,
            'native_P7_png_exact_cases':8,'cross_aspect_title_plate':summaries,
            'reduced_motion':motion,'release_gate_credit':False,
            'physical_or_human_art_approval':False,
            'original_native_ppu_parity_proven':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifact',type=__import__('pathlib').Path)
    a=p.parse_args()
    print(json.dumps(verify(a.artifact),indent=2,sort_keys=True))

if __name__=='__main__':
    main()
