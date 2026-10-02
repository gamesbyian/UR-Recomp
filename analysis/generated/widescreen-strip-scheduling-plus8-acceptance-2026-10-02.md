# +8 Widescreen adjacent future-column scheduling acceptance

Date: 2026-10-02

Status: accepted bounded implementation-facing preparation experiment.

## Evidence

Workflow run: `37066327707`

Accepted diagnostic mode: `URRECOMP_WS_MODE=doublepass`

Matched control: stock margin 0.

Fixture: `tests/input/preparation-emission-race.script`

Independent activation guardrail: `tests/input/object-liveness-dragster.script`

## Result

The diagnostic path reuses the stock `81:A59E` preparation helper to stage one
additional horizontal column into the secondary low-WRAM lane, then lets the
existing `81:AB88` descriptor builder and NMI consumer emit that column through
slot 3.

The corrected acceptance analyzer reports:

- 932 common preparation frames;
- zero authoritative/camera-state differences;
- 314 exact later-stock future-column candidates;
- 309 accepted adjacent future columns;
- every accepted column is consumed by NMI in the same guest frame;
- every accepted column matches the exact post-NMI VRAM bytes;
- longest consecutive accepted run: 14 frames.

The independent liveness guardrail reports:

- 61 common samples;
- zero protected differences in player position, camera, progression, or the
  retained object-map prefix;
- identical first progress change in control and double-pass runs at
  `liveness-004`, guest frame 1225;
- no earlier gameplay activation.

## Classification

The first +8 widened-preparation seam is therefore proven to belong to
presentation preparation/streaming. It does not require moving authoritative
camera state or widening gameplay activation.

The current double-pass mechanism is disposable diagnostic code, not a shipping
implementation. Its durable implication is that the stock preparation machinery
can produce the correct adjacent future horizontal strip early enough for +8
while preserving authoritative state.

## Negative discriminators retained

A temporary `$052B: 16 -> 32` patch makes `81:AB88` emit a longer 64-byte
VMAIN=`$81` transfer, but the second 32 bytes do not match the next stock
horizontal column. This extends the existing column rather than preparing the
adjacent one.

Camera-WRAM bias experiments are also rejected as a shipping seam because they
perturb or lag authoritative camera state.

## Harness corrections

Two proof-harness defects were found and covered by regression tests before
acceptance was promoted:

1. horizontal adjacency was initially restricted to `$0D80..$0D9F`; the
   correct general rule advances the low five destination bits while retaining
   the current tilemap page/row, with `$0D9F -> $0D80` as one observed wrap;
2. the `WSVRAM` parser used an end-of-string anchor without multiline mode,
   causing nearly all post-NMI samples to be skipped.

Re-evaluating the retained failed-run artifact with those proof fixes already
yielded the accepted 309-column / 14-frame result; fresh run `37066327707`
then reproduced it and completed the liveness gate.

## Next bounded step

Express the proven +8 preparation intent as the smallest maintainable runtime
hook while leaving stock 4:3 selectable. Only then test whether repeating the
same mechanism naturally supplies the additional columns required by +16/+24.
Do not broaden into unrelated renderer or gameplay archaeology before that
generalization test.
