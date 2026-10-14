# QA-08: actual native $2100 INIDISP write source at the split seam

**Source accepted in exact-head run 38545867736 (artifact 11885605603),\nindependently checked against original run 38546562780.\nNative tags below are real observed register-write tags, not synthetic tests.**

The authenticated source raster comparison
[`QA08-ORIGINAL-NATIVE-2P-RGB5-SPLIT-BAND-PIXEL-20261014.md`](QA08-ORIGINAL-NATIVE-2P-RGB5-SPLIT-BAND-PIXEL-20261014.md)
found **56,832/57,344 equal RGB5 source pixels** between original
Snes9x callback2207 and Baldosa native 2P guest2208,
after the interpreter's documented green6→green5 conversion.
Exactly two 256-pixel-wide rows differ. Genuine original
`go.ppuw.tsv` shows source HDMA `$2100 INIDISP=00` at
original V111 and `$2100=0F` at V113. The original
brightness-zero black rows are 111/112, native 112/113.
That identifies the **visual symptom** and a real original
register-origin cause but does not prove the native HDMA
write-to-render-row schedule or physical SNES HBlank timing.

## The independently instrumented native source seam

Reuse the already compiled and source-gated
`tools/qa08_patch_hdma_coldata_source.py`
at the existing disposable pinned `snesrecomp` DMA
`dma_transferByte` after its real
`snes_writeBBus(dma->snes,bAdr,val)`. The exact same
guest2208 frame arm used for the previously accepted
channel-5 COLDATA/CGADSUB probe now also observes any
channel that *actually writes* `bAdr=0x00` (`$2100 INIDISP`).
It reads, without mutation, guest frame, real native
`ppu_wlog_position` tagged frame/line, active DMA channel
number, mode/directness, actual A-bus byte source and table
pointer, B-bus input and **post-write live PPU `inidisp`**.
The observer explicitly **does not assume the writer is
channel5** or hardcode its split scanline. A 2048-line
bound rejects overflow. There is no production binary,
gameplay, OAM, camera, PPU draw, shader or input change.

The strict `tools/check_qa08_native_split_inidisp_source.py`
first checks original/native SHA-referenced 99.107% source
pixel evidence and unchanged native source 2473 guest CRC/
26 BG3/OBJ source-pixel acceptance. It requires actual
`$2100` HDMA writes at guest2208, real after-write
register equality, bounded chronological line tags,
valid channel/source metadata, and a genuine
`00 → 0F` brightness-zero/brightness-15 restore pair.
The resulting JSON preserves actual **measured** native
source registers, table addresses and tags. Synthetic
unit fixtures use tags 114/116 merely to test parser
behaviour; **these are not empirical observations**.

The existing, full source-backed [Baldosa core spike
workflow](../.github/workflows/baldosa-core-spike.yml)
reuses its own stock source-size guest2208 and independent
racer front-removal CRC/raster acceptance. It emits and
archives `ws342_native_hdma_inidisp_split_2208.json`
alongside the earlier accepted colour-HDMA report. No
second CI factory or route, unpinned source process or
new extra emulator is introduced.

## Next decision

- If real native `$2100` HDMA lands a line too late,
  trace the exact HDMA source rep-count/beam progression and
  original Snes9x reference interval.
- If the actual native transfer is timely but the black
  pixels appear one row lower, inspect
  `snes_beam_frame_driver_draw_ppu_frame`'s
  `ppu_rasterApplyLine`, `ppu_runLine` and
  `dma_doHdma` call ordering and the `PpuDrawWholeLine`
  1-based source output row.
- In either case, reproduce the **full 256×224 original/native
  RGB5 pixel regression**, including the 26 genuine BG3/OBJ
  source witnesses, before changing one HDMA tick globally or
  promoting the native graphics gate.

This is still original-emulator evidence, **not physical SNES
hardware timing**. The authentic 256×224 and 7:6 PAR policy,
real wide-world geometry, byte-faithful Original 4× fallback
and HD racer human aesthetic veto remain unchanged.


## Accepted exact-source result

The true Baldosa guest2208 channel-7, direct, mode-0 BBUS $2100
source probe passed in [run 38545867736](https://github.com/gamesbyian/UR-Recomp/actions/runs/38545867736):

| Real native write tag | WRAM source | $2100 after-write byte |
| ---: | --- | --- |
| 0 | `7E:2065` | `0F` (first-line prime) |
| 2 | `7E:2065` | `0F` |
| 113 | `7E:2067` | `00` (zero brightness) |
| 115 | `7E:2069` | `0F` (restore brightness) |

The independently accepted original Snes9x channel-7 source probe,
[run 38546562780](https://github.com/gamesbyian/UR-Recomp/actions/runs/38546562780),
identifies identical WRAM source addresses and the same register bytes
at original V0, V111 and V113. It also measured **real original brightness**
15 → 0 → 15 and an *unset* forced-blank bit. Native's read-only observer
measures live `inidisp` byte, not a separate native brightness shadow.
The actual source write tags differ by two and the rendered zero-brightness
band differs by one row. Neither log alone establishes physical SNES
HBlank timing or the correct downstream native PPU output-row mapping.

Source ZIP SHA-256, exact individual JSON report hashes and the paired
2P 256×224 source-frame evidence are retained in
[`analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json`](../analysis/data/qa08-original-native-2p-brightness-split-channel7-handoff-20261014.json).
