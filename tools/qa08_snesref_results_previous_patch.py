#!/usr/bin/env python3
"""Stage one opt-in read-only 5183 PPU dump in the pinned original snesref host.

The authentic Snes9x script must remain byte-for-byte unchanged. Do not split
press: each command adds a trailing idle frame. This stages in a disposable
game/663816 reference checkout only; no shared SNESRecomp or guest edits.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess

GAME="10b864b9d14a7b7416dd909eb7b054c88faef101"
CORE="075fbe4c8e0d97b0013be541795c39cb644a9709"
RELATIVE=Path("snesrecomp/tools/snesref/frontend.cpp")
MARK="UR_QA08_SNESREF_RESULTS_PREVIOUS"
BEFORE="""        p_retro_run();
        g_frame++;
        trace_tick();"""
AFTER="""        p_retro_run();
        g_frame++;
        /* UR_QA08_SNESREF_RESULTS_PREVIOUS: actual completed original frame,
         * no input-script boundary, render substitution or core writes.
         * Disabled in normal reference usage; original PPU 263-frame raster
         * must replay byte-exact against independent unmodified Snes9x. */
        if (g_frame == 5183 && getenv("UR_QA08_SNESREF_RESULTS_PREVIOUS")) {
            do_dump("qa08_results_previous");
        }
        trace_tick();"""

HISTORY_MARK="UR_QA08_CGRAM_HISTORY"
HISTORY_ANCHOR="static void do_dump(const char* tag) {"
HISTORY_CODE=r"""/* UR_QA08_CGRAM_HISTORY: read existing patched original Snes9x PPU
 * ring from 5072 through 5184; no controller, guest, PPU or timing writes.
 * This is an opt-in, one-time discriminator for 112-frame results colour. */
static void qa08_dump_cgram_history(uint32_t through) {
    if (!p_dbg_ppuw_head || !p_dbg_ppuw_read || !p_dbg_ppuw_capacity ||
        !p_dbg_ppuw_entry_size || p_dbg_ppuw_entry_size() != sizeof(SnesrefPpuwEntry))
        return;
    const uint64_t head = p_dbg_ppuw_head();
    const uint64_t cap = p_dbg_ppuw_capacity();
    const uint64_t oldest = head > cap ? head - cap : 0;
    char path[1024];
    snprintf(path, sizeof path, "%s/qa08-results-5072-5184-cgram-history.tsv", dump_dir());
    FILE* f = fopen(path, "wb");
    if (!f) return;
    fprintf(f, "#range=5072..5184\n");
    fprintf(f, "frame\tvcounter\thcounter\taddr\tvalue\tsource\n");
    std::vector<SnesrefPpuwEntry> chunk(65536);
    const char* src[3] = {"cpu", "dma", "hdma"};
    uint64_t cursor = oldest;
    uint32_t earliest = 0xffffffffU;
    size_t matched = 0;
    bool complete = true;
    while (cursor < head) {
        const size_t want = (head - cursor > chunk.size())
                          ? chunk.size() : (size_t)(head - cursor);
        uint64_t first = 0;
        const size_t n = p_dbg_ppuw_read(cursor, want, chunk.data(), &first);
        if (!n || first < cursor || first + n <= cursor) {
            complete = false;
            break;
        }
        for (size_t i = 0; i < n; ++i) {
            const SnesrefPpuwEntry& e = chunk[i];
            if (e.frame < earliest) earliest = e.frame;
            if (e.frame >= through-112 && e.frame <= through &&
                (e.addr == 0x2121 || e.addr == 0x2122)) {
                fprintf(f, "%u\t%u\t%u\t%04X\t%02X\t%s\n",
                    e.frame, e.vcounter, e.hcounter, e.addr, e.value,
                    e.source < 3 ? src[e.source] : "?");
                ++matched;
            }
        }
        cursor = first + n;
    }
    fprintf(f, "#ring_earliest=%u\n#port_writes=%zu\n#scan_complete=%u\n",
        earliest, matched, complete ? 1u : 0u);
    fclose(f);
    fprintf(stderr,
        "UR_QA08_CGRAM_HISTORY source=original start=5072 end=5184 "
        "earliest=%u port_writes=%zu scan_complete=%u\n",
        earliest, matched, complete ? 1u : 0u);
}

static void do_dump(const char* tag) {"""
HISTORY_TRIGGER_BEFORE="""    dump_ppuw(tag, frame, &ppuw_n, &trunc);

    char info[2048];"""
HISTORY_TRIGGER_AFTER="""    dump_ppuw(tag, frame, &ppuw_n, &trunc);
    /* Original 5184 results source: preceding 112-frame port chronology,
     * diagnostic only, no changes to authentic input or Snes9x execution. */
    if (frame == 5184 && !strcmp(tag, "qa08_results_cgram") &&
        getenv("UR_QA08_CGRAM_HISTORY"))
        qa08_dump_cgram_history(frame);

    char info[2048];"""

def patch_source(source:str)->str:
    if MARK in source or HISTORY_MARK in source:
        if (source.count(MARK)!=AFTER.count(MARK) or
            source.count(AFTER)!=1 or
            source.count(HISTORY_MARK)!=HISTORY_CODE.count(HISTORY_MARK)+HISTORY_TRIGGER_AFTER.count(HISTORY_MARK) or
            source.count(HISTORY_CODE)!=1 or
            source.count(HISTORY_TRIGGER_AFTER)!=1):
            raise ValueError("original read-only source history patch is partial/tampered")
        return source
    if (source.count(BEFORE)!=1 or
        source.count(HISTORY_ANCHOR)!=1 or
        source.count(HISTORY_TRIGGER_BEFORE)!=1 or
        "static void dump_ppuw(const char* tag" not in source):
        raise ValueError("source PPU readback hooks changed")
    return (source.replace(BEFORE,AFTER,1)
                  .replace(HISTORY_ANCHOR,HISTORY_CODE,1)
                  .replace(HISTORY_TRIGGER_BEFORE,HISTORY_TRIGGER_AFTER,1))

def rev(path:Path)->str:
    return subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
                          check=True,capture_output=True,text=True).stdout.strip()

def apply(game:Path,write:bool=False)->Path:
    game=game.resolve()
    if rev(game)!=GAME or rev(game/"snesrecomp")!=CORE:
        raise ValueError("unrecognized original reference/core pin")
    path=game/RELATIVE
    old=path.read_text(encoding="utf-8")
    new=patch_source(old)
    if write and old!=new:
        path.write_text(new,encoding="utf-8")
    return path

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",required=True,type=Path)
    p.add_argument("--apply-readonly-capture",action="store_true")
    a=p.parse_args()
    try:
        path=apply(a.game,write=a.apply_readonly_capture)
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        p.exit(2,f"QA08_SOURCE_HOST_PREVIOUS_REJECTED: {exc}\n")
    print(f"QA08_SOURCE_HOST_PREVIOUS file={path} staged={int(a.apply_readonly_capture)} original_route_unchanged=1 raster_acceptance=0")

if __name__=="__main__":
    main()
