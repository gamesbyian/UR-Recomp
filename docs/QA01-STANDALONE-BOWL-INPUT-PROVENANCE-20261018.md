# QA-01: original/native Bowl supplied-input receipt closure (18 October 2026)

**Scope:** independently inspect the original controller-input artifacts submitted to the genuine Snes9x/Baldosa guest processes. This is not proof that the emulated 65816 consumed each mask at a particular instruction/host/beam clock, not a game-fidelity fix and not full-event acceptance.

## Concrete existing evidence gap

The independently rehashed [authentic completed Bowl→Switcher run 39168164480](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480) retains the exact original execution report, original/native source logs, 48 raw WRAM/SRAM images, cold guest observations and QA review. Its original [artifact 12151357791](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480/artifacts/12151357791) is 398053 bytes, SHA256 `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`, verified directly. However, its 62 members **do not include** the actual supplied original `bowl/replay/ref.input`, native `bowl/replay/pinned-baldosa.input`, or shared `bowl/replay/complete.script`. A reviewer cannot independently recompute the *supplied* controller masks and source script bytes from that old archive, even though the producer reports the script hash and result. Do not retroactively claim those original files were retained.

## Exact minimal correction

The standalone Bowl source-pinned manual/PR workflow retains those **already existing** three tiny text files and runs the existing distributed-campaign `tools/qa01_event_route_artifact_audit.py` before it declares a successful original/native result. The existing route verifier's original default artifact-root layout is preserved; an optional explicit `--replay-dir` lets the standalone Bowl runner reuse the **same** mask, start/duration, independent guest-frame shift and guest dump/script SHA checks instead of forking another input comparator. It emits `bowl-source-input-identity.json` linked to the exact original producer-report SHA. Any missing, reordered or modified source input row or replay script fails closed, with zero admission.

For manual offline review of a future extracted *original* Bowl artifact:

```sh
python3 tools/qa01_event_route_artifact_audit.py \
  --artifact-root /path/to/original-archive   --producer-report /path/to/original-archive/bowl-report.json \
  --replay-dir /path/to/original-archive/bowl/replay \
  --out /tmp/bowl-source-input-identity.json
```

The first genuine run on the amended workflow must pass the original/native scorer, independent raw memory checker, supplied-input verifier and actual cold record experiment before its artifact is promoted from an **infrastructure-ready** PR to inspected genuine evidence. ROM-free synthetics establish only failure behavior, not original controller consumption. No new emulator, game code, CPU/SPC scheduling or controller rephase is introduced, and the official 45-event and Windows release ledgers remain **0/45** and **0/12** respectively.
