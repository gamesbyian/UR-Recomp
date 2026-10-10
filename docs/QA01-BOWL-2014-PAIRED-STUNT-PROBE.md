# QA-01: original 2014 Bowl scored-Stunt transplant experiment

**Experiment, not accepted course evidence.** Dedicated job `.github/workflows/qa01-bowl-stunt-2014.yml`; existing source/event oracle `tools/probe_original_event_complete.py --case bowl --native-backend pinned-baldosa`.

## Why this is the next independent event

The preserved *original Snes9x* 2014 Dessyreqt input and anchored SRAM already have source-visible **Bowl** (USA course 03, 45-second Stunt) results: tally menu `0x2F` at original movie frame **11915**, settled score screen `0x18` at **11985**, and displayed **MIKE 764**. See `analysis/generated/result-screens-probe.json`. This is original-only evidence. It is independent of the Zoom Zoo Circuit one-frame restore routine and specifically exercises a scored Stunt rather than extrapolating from Circuit or Dragster.

The existing fail-closed `probe_original_event_complete.py` first **scans the source original stream** to identify an actual 7E:00CE course-2 active-entry and stable result menu, requires original `0x2F` tally before `0x18`, and preserves the entire exact original source guest-controller mask sequence. It then independently boots original Snes9x and native Baldosa from the source's embedded SRAM, uses each fresh guest's observed stock course-entry frame to rebase the unaltered scene-relative controller stream, and compares gameplay fields plus PPU score and result text.

The existing producer previously used the legacy host's `SNESRECOMP_INPUT_FILE` transport. The new **opt-in** `pinned-baldosa` transport now reuses the proven disposable `UR_QA_SCENE_INPUT_FILE` shim from the successful Zoo native/native-input studies, and passes proper Baldosa `--no-launcher --config --script` arguments. Empty calibration input runs use unmodified menu-script control, while genuine source movie frames use the source mask file. This is not another game backend, host, input schema, or new generic harness. No writable memory poke, save transplantation or game rule change is authorized. The historical source's previous-tour state is diagnostic only; the new original/native boot states must match each other.

## Outcome rule

A job reporting **0** means a *candidate* scored event only, not approval. Retained report and logs must separately establish genuine active timed Stunt, original and native score, source P1 identity, consistent original/native source-relative clock, a real settled result, and exact ROM/build/controller/SRAM fingerprints. Failures or timeouts are negative diagnostic evidence, **not** evidence of a Baldosa gameplay defect without attribution.

Even if this experiment yields a matching P1 score, **do not promote USA course 03** without reviewed result/timer/event scoring semantics and independently reproduced exact-artifact evidence in the QA-01 ledger and course census. The official count remains **0/45**, with Bowl only partially observed until then. The separate first completed non-Dragster Race B (Switcher, USA course 04) remains future work.

## Original source interim staging (CI 38021691116)

The first source result probe failed closed despite the **genuine** original Bowl tally at frame **11915** (`menu=0x2F`, course `7E:00CE=2`, in-race byte `0x3C`) and settled score menu at frame **11985** (`0x18`, course 2). The retained [CI artifact 11657918608](https://github.com/gamesbyian/UR-Recomp/actions/runs/38021691116) isolates the cause: the original movie first enters Bowl at **8620**; during its final 34 active-flag frames **11867..11900**, course `7E:00CE` briefly reads **0** rather than 2, then returns to course 2 by **11901**, with a valid original scored tally appearing at **11915**. This is source-observed original game staging, not proof of another event.

The corrected source eligibility predicate is narrowly original-only: permit that intermediate `track=0` interval **only** in the 80 frames before a sustained real scored-Stunt `0x2F` tally, with the original course active both before and immediately after, and no other sustained competing course. Mid-race foreign tracks, missing return, missing tally, or any similar Race/Circuit exception still reject. Neither this source classification nor the probe's eventual native result can independently satisfy the official complete-course acceptance protocol (**0/45**). Do not modify Baldosa guest physics or result-clock ordering on this evidence.
