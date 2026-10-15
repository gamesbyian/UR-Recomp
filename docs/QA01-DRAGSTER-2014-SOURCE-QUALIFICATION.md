# QA-01/07: source-original 2014 Dragster Race A replay candidate

**Status: source-qualified first-course Race A input transplant is executable;
fresh original/native result has NOT been run or admitted by this PR.**
Official USA counts stay **0/45 accepted, 4/45 partial, 41/45 unverified**.
Do not modify the independent release ledger from this gameplay lane.

## Independent original evidence already retained

The actual reset-anchored Dessyreqt 2014 single-controller SMV
(`reference/imported/tas-bots/dessyreqt-4250-submission.smv`, including
its original embedded SRAM) was replayed against the canonical USA ROM in
the pinned Snes9x reference. The first sustained original guest course
is **Dragster, track 0, stream 1**, entered at **source movie frame 794**.
A genuine stable Race result menu `7E:009F = 0x99` starts at **2874**,
**2,080 original guest host frames later**. The source-owned PPU result
screen (original movie snapshot at 2883) names **DRAGSTER**, shows **MIKE
0:25.08** and uses the genuine Race result presentation, not a host-invented
finish predicate. Exact original source observations are preserved in
`analysis/generated/result-screens-probe.json`,
`docs/QA07-HISTORICAL-ZOOM-ZOO-SCENE.md` and
`docs/ORIGINAL-COURSE-EVENT-CENSUS.md`. This does not alone prove a
fresh original/native event pair.

The old partial Dragster course census concerns a distinct native-only
finish/checkpoint transition. It does not receive a stronger release status
from this new original source input route.

## Bounded producer reuse

The existing `tools/probe_original_event_complete.py` now permits
`--case dragster` with `--native-backend pinned-baldosa`. This adds no
emulator, recompiler, game logic or new controller movie:

1. Scan exactly the same reset-anchored SMV in original Snes9x, with
   canonical USA ROM, full source horizon and embedded original SRAM;
   demand genuine source entry/result at **794/2874** and a sustained
   course-0 active episode before `0x99`.
2. Independently boot the source-pinned Snes9x and native Baldosa guest
   via the existing stock Crawler first-track selection. For track 0,
   `7E:009B=0` and **zero** Down inputs are expected. No synthetic
   course-state poke, savestate transplant or timing offset.
3. Observe each fresh guest's actual Race A entry and compare its live
   entry signature and decoded original stream-1 course payload. Extract
   the source movie's P1 button stream from the original entry for 2,120
   original host frames (2,080 to the real source result plus 40), shifting
   only its absolute origin to each independently calibrated guest entry.
4. Compare unmodified original/native sampled course/rider/clock/contact/
   checkpoint/finish/lap states, genuine post-race `0x99` onset and
   independently decoded settled PPU result text. Reject differing
   guest-relative result onset and any prior sampled gameplay mismatch.
   `paired_event_candidate` remains a strict *investigative* predicate.
5. Retain exact SHA-bound ROM, movie, embedded SRAM, native binary,
   reference core, input, source-window, original entry/result and fresh
   entry-shift receipts. Review the actual per-event report before any
   further probe.

The existing three-case `qa01-event-campaign.yml` **deliberately does not
include Dragster** until this new fresh-guest original/native producer is
actually executed and independently shown to produce a meaningful matched
or strict-negative real result. No automatic CPU-intensive CI fanout has
been created. The existing Bowl PR regression checks only that the
established Bowl replay remains unchanged.

## Actual runtime invocation (once binaries are already available)

```sh
python3 tools/probe_original_event_complete.py \
  --case dragster --native-backend pinned-baldosa \
  --source-horizon 22000 \
  --snesref /path/to/pinned/snesref \
  --core /path/to/pinned/snes9x_libretro.so \
  --native /path/to/verified/UniracersSNESRecomp \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --work-dir /fresh/unique/qa01-dragster-work \
  --json-out /fresh/unique/qa01-dragster.json
```

Use a **fresh unique process/work root** per attempt, verify exact build and
ROM/source identities, and preserve a compact source/result receipt. The
historical input transport is the existing `baldosa_qa_dense_scene_input_patch.py`
shim in a disposable pinned guest checkout; an arbitrary native executable
without that transport is not a valid first experiment.

## Admission and next decision

A passing *source-original* check or synthetic unit assertion proves only
that the genuine historical event is internally coherent. A matched PPU
result after fresh native replay does not supersede a differing guest-entry
phase, full game execution, result onset, progression, terminal restoration,
save data or Windows release candidate. After an independently reproduced
real negative, isolate the **smallest first divergent guest frame window**;
handoff CPU/APU/NMI/VBlank timing to Opus with source instructions, rather
than fixing game timing in the QA-01 lane.

Three-project reuse preflight: the established UR movie extractor, original
Snes9x and strict comparator are reused; pinned Baldosa USA guest executes
as the candidate only; malmazuke PAL result/finish machinery is an advisory
source lead, not an independently accepted USA event oracle. No 45-course
case has been promoted.
