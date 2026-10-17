#!/usr/bin/env python3
"""Read-only source Snes9x original-USA blackout at 4015..4017.

Stage only in disposable exact-pinned reference host AFTER the existing
authenticated 5183/results observer. Do not alter the original 2P input
script, the libretro guest, time, PPU pixels, or previous four dumps.
Read $2100 writes from the original debug PPU ring for frames 3998..4035.
"""
from __future__ import annotations
import argparse
from pathlib import Path
try:
    from tools import qa08_snesref_results_previous_patch as base
except ImportError:
    import qa08_snesref_results_previous_patch as base

MARK="UR_QA08_ORIGINAL_BLACKOUT_BOUNDED"
DUMP_ANCHOR="static void do_dump(const char* tag) {"
WRITE_HISTORY=r"""/* UR_QA08_ORIGINAL_BLACKOUT_BOUNDED: read-only source original PPU ring.
 * The original controller script/core/guest/video are never modified. */
static void qa08_original_blackout_inidisp_history() {
    if (!p_dbg_ppuw_head || !p_dbg_ppuw_read || !p_dbg_ppuw_capacity ||
        !p_dbg_ppuw_entry_size ||
        p_dbg_ppuw_entry_size()!=sizeof(SnesrefPpuwEntry))
        return;
    const uint64_t head=p_dbg_ppuw_head();
    const uint64_t cap=p_dbg_ppuw_capacity();
    const uint64_t oldest=head>cap?head-cap:0;
    char name[1024];
    snprintf(name,sizeof name,"%s/qa08-original-blackout-3998-4035-INIDISP.tsv",dump_dir());
    FILE *f=fopen(name,"wb");
    if (!f) return;
    fprintf(f,"#original_frame_range=3998..4035\n");
    fprintf(f,"frame\tvcounter\thcounter\taddr\tvalue\tsource\n");
    std::vector<SnesrefPpuwEntry> chunk(65536);
    const char* source[3]={"cpu","dma","hdma"};
    uint64_t cursor=oldest;
    uint32_t earliest=0xffffffffu;
    size_t found=0;
    bool complete=true;
    while(cursor<head) {
        size_t want=(size_t)(head-cursor>chunk.size()?chunk.size():head-cursor);
        uint64_t first=0;
        size_t n=p_dbg_ppuw_read(cursor,want,chunk.data(),&first);
        if (!n || first<cursor || first+n<=cursor) {
            complete=false;
            break;
        }
        for(size_t i=0;i<n;++i) {
            const SnesrefPpuwEntry& e=chunk[i];
            if(e.frame<earliest) earliest=e.frame;
            if(e.frame>=3998 && e.frame<=4035 && e.addr==0x2100) {
                fprintf(f,"%u\t%u\t%u\t%04X\t%02X\t%s\n",
                    e.frame,e.vcounter,e.hcounter,e.addr,e.value,
                    e.source<3?source[e.source]:"?");
                ++found;
            }
        }
        cursor=first+n;
    }
    fprintf(f,"#ring_earliest=%u\n#write_count=%zu\n#scan_complete=%u\n",
        earliest,found,complete?1u:0u);
    fclose(f);
    fprintf(stderr,"UR_QA08_ORIGINAL_BLACKOUT_PPU source=original "
                   "frames=3998..4035 inidisp_writes=%zu earliest=%u complete=%u\n",
                   found,earliest,complete?1u:0u);
}

static void do_dump(const char* tag) {"""
ADDED=r"""        /* Source-only completed original frames; zero controller commands.
         * A prior attempt to split press actions inserted an idle frame
         * and was rejected. This hook is strictly after p_retro_run. */
        if (getenv("UR_QA08_ORIGINAL_BLACKOUT") &&
            (g_frame == 4015 || g_frame == 4016 || g_frame == 4017)) {
            if(g_frame==4015) do_dump("qa08_blackout_4015");
            if(g_frame==4016) do_dump("qa08_blackout_4016");
            if(g_frame==4017) do_dump("qa08_blackout_4017");
        }
        if(g_frame==4036 && getenv("UR_QA08_ORIGINAL_BLACKOUT"))
            qa08_original_blackout_inidisp_history();
"""
HOOK_AFTER=base.AFTER.replace("        trace_tick();",ADDED+"        trace_tick();")


def patch_source(source:str)->str:
    if MARK in source:
        if source.count(WRITE_HISTORY)!=1 or source.count(HOOK_AFTER)!=1:
            raise ValueError("source original blackout hook was altered or partial")
        return source
    if (source.count(DUMP_ANCHOR)!=1 or
        source.count(base.AFTER)!=1 or
        base.HISTORY_MARK not in source or
        "p_dbg_ppuw_entry_size" not in source):
        raise ValueError("original Snes9x exact previous results hook or debug ring absent")
    return (source.replace(DUMP_ANCHOR,WRITE_HISTORY,1)
                  .replace(base.AFTER,HOOK_AFTER,1))


def apply(game:Path,*,write:bool=False)->Path:
    game=game.resolve()
    if base.rev(game)!=base.GAME or base.rev(game/"snesrecomp")!=base.CORE:
        raise ValueError("foreign or unpinned original source/core checkout")
    f=game/base.RELATIVE
    old=f.read_text(encoding="utf-8")
    new=patch_source(old)
    if write and old!=new:
        f.write_text(new,encoding="utf-8")
    return f


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-readonly-capture",action="store_true")
    a=p.parse_args()
    try:
        f=apply(a.game,write=a.apply_readonly_capture)
    except (OSError,ValueError) as exc:
        p.exit(2,f"QA08_ORIGINAL_BLACKOUT_SOURCE_REJECTED: {exc}\n")
    print("QA08_ORIGINAL_BLACKOUT_READONLY",
          f"source={f} staged={int(a.apply_readonly_capture)}",
          "native_phase_and_graphics_release=unaccepted")


if __name__=="__main__":
    main()
