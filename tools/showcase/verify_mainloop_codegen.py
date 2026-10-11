#!/usr/bin/env python3
"""Independent on-checkout identity and opcode gate for the technical trailer.

Checks *actual ROM bytes* and published repo symbol/AOT config, not an
editor's reconstruction. The pinned upstream code excerpt is separately
attributed, not self-certified by this gate.
"""
import argparse,hashlib,json,re
from pathlib import Path

ROM='reference/roms/retail/Uniracers_USA.sfc'
ROM_SHA='859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478'
UPSTREAM='10b864b9d14a7b7416dd909eb7b054c88faef101'
UPSTREAM_BLOB='cc9ef833a5c7c0809aaab53ea00c182158241b83'
BASE='reference/imported/reverse-engineering/baldosa-uniracers-recomp/'
EXHIBIT='media/showcase/2026-10-10/technical-motion/mainloop-aot-source-exhibit.txt'
OFFSET=0x0881
EXPECTED=bytes.fromhex('20c6ac') # 65816 JSR $ACC6 (absolute, little-endian)

def sha(p):
    d=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):d.update(chunk)
    return d.hexdigest()

def check(root):
    rom=root/ROM
    assert sha(rom)==ROM_SHA,'USA ROM digest does not match canonical retail image'
    with rom.open('rb') as f:
        f.seek(OFFSET);instruction=f.read(3)
    assert instruction==EXPECTED, f'MainLoop opcode mismatch: {instruction.hex()}'
    symbols=root/(BASE+'recomp/symbols.toml'); s=symbols.read_text()
    assert re.search(r'\[\[func\]\]\s*name = "MainLoop"\s*addr = "8881"\s*bank = 0\s*emit = true\s*entry_m = 1\s*entry_x = 0',s)
    listings=root/(BASE+'decomp/symbols.txt')
    assert '808881 MainLoop' in listings.read_text()
    aot=root/(BASE+'src/gen/.snesrecomp-cache.json'); inventory=json.loads(aot.read_text())
    assert 'bank00_part01_v2.c' in inventory['bank_outputs']['00']
    e=(root/EXHIBIT).read_text()
    assert UPSTREAM in e and UPSTREAM_BLOB in e
    assert all(x in e for x in ('L_8881_M1X0:', 'cpu_trace_block(cpu, 0x008881);',
        'cpu->cycles += 6;', 'case 2: _r = MainMenu_Draw_M1X0(cpu); break;', 'goto L_8884_M1X0;'))
    assert 'NONCONTIGUOUS' in e,'Do not imply this excerpt is contiguous original C'
    return {
        'result':'accepted_exact_65816_opcode_witness',
        'rom_sha256':ROM_SHA,'rom_path':ROM,'rom_lorom_offset_hex':'0x0881',
        'cpu_address':'80:8881 (00:8881 LoROM mirror)',
        'decoded_65816_instruction':'JSR $ACC6','instruction_hex':instruction.hex(),
        'source_symbol':'MainLoop','source_function_address':'00:8881','recompiler_mx':'M1X0',
        'recompiler_configuration':BASE+'recomp/symbols.toml',
        'generated_C_inventory':BASE+'src/gen/.snesrecomp-cache.json',
        'generated_C_upstream_git_commit':UPSTREAM,'generated_C_upstream_blob_sha1':UPSTREAM_BLOB,
        'generated_C_upstream_path':'src/gen/bank00_part01_v2.c','generated_C_excerpt_path':EXHIBIT,
        'source_files_sha256':{p:sha(root/p) for p in (EXHIBIT,BASE+'recomp/symbols.toml',BASE+'decomp/symbols.txt',BASE+'src/gen/.snesrecomp-cache.json')},
        'limits':'Exact ROM opcode and project symbol map are checked locally. The excerpt attribution to the pinned upstream AOT blob was independently reviewed against the GitHub source; the manifest does not imply a new original-vs-native gameplay equivalence test.'
    }

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--out',type=Path)
    args=p.parse_args();a=check(args.repo_root)
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(a,indent=2)+'\n')
    print(json.dumps(a,indent=2))
if __name__=='__main__':main()
