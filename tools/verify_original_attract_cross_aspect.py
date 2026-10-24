#!/usr/bin/env python3
"""Independent real-artifact original-title/demo cross-aspect SDL audit.

No ROM pixels are published; private artifact is a user-owned Actions ZIP.
This checks presentation geometry and source-state consistency only.

Usage: verify_original_attract_cross_aspect.py PATH_TO_ARTIFACT_ZIP
"""
import hashlib,io,json,sys,zipfile
from pathlib import Path
from PIL import Image

EXPECTED_SHA='65bb91d07a7e4292a3695e4e04e72acb6838f9b99f56c2ad7e1fcbefb869e4a6'
SOURCE='e7bdbacb360ed021065b82d836a12156117c1c78'
PE='6231c6a1d783c639442b170a59595dfe303eb047cc856fac079b94292d593b64'
MODES={'wide':((1280,720),(160,0,960,720)),'4by3':((1024,768),(0,0,1024,768))}
STAGES=('original-title','original-demo','woken-modern','confirmed-root')

def require(ok,why):
    if not ok: raise ValueError(why)

def sha(x): return hashlib.sha256(x).hexdigest()

def base(mode): return f'modern-title-original-attract-sdl-{mode}-pr2043/'

def decode_pam(p7,size):
    h=(f'P7\nWIDTH {size[0]}\nHEIGHT {size[1]}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n').encode()
    require(p7.startswith(h) and len(p7)==len(h)+size[0]*size[1]*4,'bad P7')
    return p7[len(h):]

def recover_source(raw,mode):
    (w,h),(left,top,vw,vh)=MODES[mode]
    src=bytearray(256*224*3)
    for y in range(224):
        py=top+((2*y+1)*vh)//448
        for x in range(256):
            px=left+((2*x+1)*vw)//512
            src[(y*256+x)*3:(y*256+x)*3+3]=raw[(py*w+px)*4:(py*w+px)*4+3]
    return bytes(src)

def compare_pixels(raw,mode,source):
    (w,h),(left,top,vw,vh)=MODES[mode]
    mismatch=0; matte=0
    for y in range(h):
        inside_y=top<=y<top+vh
        sy=((2*(y-top)+1)*224)//(2*vh) if inside_y else 0
        for x in range(w):
            i=(y*w+x)*4
            if inside_y and left<=x<left+vw:
                sx=((2*(x-left)+1)*256)//(2*vw)
                j=(sy*256+sx)*3
                mismatch+=raw[i:i+3]!=source[j:j+3]
            else:
                matte+=any(raw[i:i+3])
    return mismatch,matte

def audit(archive):
    archive=Path(archive)
    rawzip=archive.read_bytes();require(sha(rawzip)==EXPECTED_SHA,'ZIP hash mismatch')
    observations={};recovered={}
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist())==len(set(z.namelist())),'duplicate ZIP member')
        for mode,(size,rect) in MODES.items():
            receipt=json.loads(z.read(base(mode)+'real-stock-title-demo-wake-sdl-receipt.json'))
            require(receipt['exact_native_source_sha']==SOURCE and receipt['one_actual_windows_aot_pe_sha256']==PE,'source/PE mismatch')
            require(tuple(receipt['actual_native_sdl_output'])==size,'size mismatch')
            for stage in STAGES:
                b=base(mode)+stage+'/'
                p7=z.read(b+'native-sdl.pam');png=z.read(b+'native-sdl.png');log=z.read(b+'native-process.log')
                r=next(x for x in receipt['real_original_guest_and_controller_source_stage_log'] if x['stage']==stage)
                require(sha(p7)==r['sdl_raw_p7_sha256'] and sha(png)==r['lossless_png_sha256'] and sha(log)==r['original_native_process_log_sha256'],'receipt hash mismatch')
                rgba=decode_pam(p7,size)
                im=Image.open(io.BytesIO(png))
                require(im.mode=='RGBA' and im.size==size and im.tobytes()==rgba,'P7/PNG mismatch')
                recovered[(mode,stage)]=(rgba,recover_source(rgba,mode))
                observations[(mode,stage)]={'frame':r['observed_guest_frame'],'P7_PNG_RGBA_equal':True,'receipt_hashes_match':True}
        for mode in MODES:
            ppm=z.read(base(mode)+'original-title/original-presdl.ppm')
            header=b'P6\n256 224\n255\n'
            require(ppm.startswith(header) and len(ppm)==len(header)+256*224*3,'original P6 mismatch')
            require(recovered[(mode,'original-title')][1]==ppm[len(header):],'title P6 vs SDL source mismatch')
    result={}
    for stage in ('original-title','original-demo'):
        wide=recovered[('wide',stage)][1];compact=recovered[('4by3',stage)][1]
        diff=sum(wide[i:i+3]!=compact[i:i+3] for i in range(0,len(wide),3))
        result[stage]={'source_rgb_cross_geometry_different_pixels':diff,'source_pixels':57344,'source_rgb_sha256':sha(wide),'host_checks':{}}
        for mode in MODES:
            rgb,src=recovered[(mode,stage)]
            mismatch,matte=compare_pixels(rgb,mode,wide)
            result[stage]['host_checks'][mode]={'rgb_mismatches':mismatch,'matte_nonblack':matte,'host_pixels':MODES[mode][0][0]*MODES[mode][0][1]}
            require(mismatch==0 and matte==0,stage+' host RGB mismatch '+mode)
        require(diff==0,'original source cross geometry mismatch '+stage)
    for stage in ('woken-modern','confirmed-root'):
        a=recovered[('wide',stage)][1];b=recovered[('4by3',stage)][1]
        result[stage]={'cross_geometry_sampled_rgb_differences':sum(a[i:i+3]!=b[i:i+3] for i in range(0,len(a),3)),'different_logical_compositions_expected':True}
    return {'schema':'ur-original-attract-cross-aspect-independent/1','source_sha':SOURCE,'pe_sha256':PE,'artifact_id':12335111546,'artifact_sha256':EXPECTED_SHA,'stage_results':result,'eight_P7_PNG_pairs_verified':8,'no_guest_parity_or_art_or_release_credit':True}

if __name__=='__main__':
    require(len(sys.argv)==2,'usage: verify_original_attract_cross_aspect.py ARTIFACT_ZIP')
    print(json.dumps(audit(sys.argv[1]),indent=2))
