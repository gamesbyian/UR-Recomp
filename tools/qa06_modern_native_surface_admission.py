"""ROM-free exact-source visual readback audit for two observed Modern SDL controls.

A 4:3 Modern menu root is painted across its entire drawable, while a 16:9
Modern root is painted in a 256x224 Original-PAR viewport with side mattes.
This deliberately does not change the shipping 16:9 gameplay composition.
A matching block pattern is a diagnostic property, not original pixel parity.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from PIL import Image
from qa06_raster_roi_reference import raster_roi, source_pixel_at_host_coordinate

SOURCE_SHA = 'd693a6c36640e2accb0ffad84f387f08bb5a8227'
PE_SHA256 = 'a1b4e4ed5a13bffa9521ff240c636524765e19960d31425cb894ddd8b5ac30d0'

def _digest(blob): return hashlib.sha256(blob).hexdigest()

def _roi(w,h):
    if (w,h)==(1024,768):
        # Observed Modern 4:3 SDL root uses a complete 256x224 PAR-corrected
        # source, NOT the 16:9 gameplay canvas assumed by H25's ROI tool.
        return (0,0,w,h)
    if (w,h)==(1280,720):
        return tuple(raster_roi(256,224,w,h)['roi_xywh'])
    raise ValueError('unqualified host resolution')

def _sample_index(pos, source, output):
    return ((2*pos+1)*source)//(2*output)

def verify_capture(folder):
    folder=Path(folder)
    receipt=json.loads((folder/'readback-receipt.json').read_text())
    w,h=receipt['actual_sdl_renderer_output']
    if type(w) is not int or type(h) is not int: raise ValueError('invalid dimensions')
    if receipt['source_sha']!=SOURCE_SHA or receipt['exe_sha256']!=PE_SHA256:
        raise ValueError('source/PE epoch changed')
    if receipt['native_process_exit']!=0 or receipt['observed_in_draw']!=40:
        raise ValueError('native process/draw receipt mismatch')
    if receipt['native_semantic_route']!='root-quit' or receipt['execution_mode']!='modern':
        raise ValueError('wrong Modern control journey')
    pam=(folder/'probe_first/actual-sdl-drawable.pam').read_bytes()
    png=(folder/'actual-sdl-drawable.png').read_bytes()
    log=(folder/'probe_first/native-process.log').read_bytes()
    if (_digest(pam),_digest(png),_digest(log)) != (receipt['p7_sha256'],receipt['png_sha256'],receipt['native_process_log_sha256']):
        raise ValueError('artifact receipt hash mismatch')
    header=(f'P7\nWIDTH {w}\nHEIGHT {h}\nDEPTH 4\nMAXVAL 255\n'
            'TUPLTYPE RGB_ALPHA\nENDHDR\n').encode()
    if not pam.startswith(header) or len(pam)!=len(header)+w*h*4:
        raise ValueError('P7 envelope mismatch')
    raw=pam[len(header):]
    with Image.open(folder/'actual-sdl-drawable.png') as im:
        if im.mode!='RGBA' or im.size!=(w,h) or im.tobytes()!=raw:
            raise ValueError('PNG/P7 pixel disagreement')
    x0,y0,rw,rh=_roi(w,h)
    first={};matte=0;sampled=0
    # Exact host-pixel -> source-pixel nearest-neighbour block census.
    for y in range(h):
        inside_y=y0<=y<y0+rh
        sy=_sample_index(y-y0,224,rh) if inside_y else None
        for x in range(w):
            offset=4*(y*w+x)
            pixel=raw[offset:offset+4]
            if not inside_y or not x0<=x<x0+rw:
                matte+=1
                if pixel!=b'\0\0\0\0':
                    raise ValueError('noncanonical black/transparent matte')
                continue
            sampled+=1
            key=(_sample_index(x-x0,256,rw),sy)
            old=first.setdefault(key,pixel)
            if old!=pixel:
                raise ValueError('within-source-pixel nearest-neighbour inconsistency')
    if len(first)!=256*224 or sampled+matte!=w*h:
        raise ValueError('source coverage contradiction')
    return {'schema':'qa06-modern-native-actual-sdl-control/1','host':[w,h],
            'source_sha':SOURCE_SHA,'exe_sha256':PE_SHA256,
            'p7_sha256':receipt['p7_sha256'],'png_sha256':receipt['png_sha256'],
            'roi_xywh':[x0,y0,rw,rh],'source_pixels':len(first),
            'source_host_samples':sampled,'matte_samples':matte,
            'source_exact_epoch':True,'original_native_pixel_parity_proven':False,
            'independent_build_reproduced':False,'art_approved':False,
            'physical_4k_accepted':False,'release_gate_credit':0}
