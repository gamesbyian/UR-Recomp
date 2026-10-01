# Bottom-border / missing-effects compatibility seam

Recovered-work execution note, 2026-09-29.

The historical compatibility source describes SNEeSe 0.842 as having an "error on bottom border" and "a few effects missing", but does not identify a screen or claim a common root cause. Treat those as separate symptoms until local evidence joins them.

## Canonical presentation survey

Run `36661300863` captures the deterministic boot/title timeline and the standard first-race route through pinned patched Snes9x.

Across every sampled checkpoint:

- framebuffer = 256×224;
- `SETINI=00`;
- effective PPU screen height = 224;
- interlace = off;
- pseudo-hires = off.

Therefore the observed game path does not use SNES 239-line overscan. A correct fix for the historical "bottom border" symptom must not globally crop, blank, or switch the game to an overscan-height model.

The bottom of the normal 224-line picture is actively used. At stable Main Menu, rider/tour/track setup, Now Playing and first active race, row 223 contains 256/256 non-black pixels. The bottom 16 rows are also essentially fully populated in active scenes. Those rows go blank only at specific transition checkpoints such as boot 60/120, boot 420 and the first instantaneous Main Menu entry.

Representative active states:

| checkpoint | frame | BG mode | bottom 16 non-black | last row non-black |
| --- | ---: | ---: | ---: | ---: |
| Main Menu settled | 500 | 3 | 4096/4096 | 256/256 |
| Rider Select | 563 | 3 | 3995/4096 | 256/256 |
| Tours | 633 | 3 | 4096/4096 | 256/256 |
| Tracks | 696 | 3 | 4096/4096 | 256/256 |
| Now Playing | 821 | 3 | 4096/4096 | 256/256 |
| Race entered | 1035 | 1 | 4096/4096 | 256/256 |

This closes the coarse geometry hypothesis: the bottom edge is ordinary live 224-line content, not an optional overscan border.

## Remaining discriminator

Use the independent Beetle core to confirm the 256×224/live-bottom-edge invariant without requiring framebuffer hash equality. Snes9x remains the detailed PPU-register oracle; Beetle supplies an independent presentation/output check.

The historical "a few effects missing" phrase remains unlocalized. Do not merge it into window XOR, color math, OAM, or bottom-edge handling absent a historical scene or a new local reproduction.

Durable survey: `analysis/generated/presentation-border-effects-survey.json`.
