# Challenge Generation Transient Discriminator

This experiment answers one implementation-blocking question for Modern Bronze/Silver/Gold selection:

**Can the stock tour-confirm medal snapshot at SRAM `0x10D1` act as the complete challenge-generation seam after persistent medal ownership remains unchanged?**

The broader progression model is already closed. This is not permission to reopen generic SRAM archaeology.

## Evidence already established

- Ordinary tours choose BRONSEN/SILVIA/GOLDWYN from medal generation 0/1/2.
- Hunter is the canonical Gold/ANTI-UNI exception.
- Persistent medals live in the checksum-protected matrix at `0x069C + 16*tour + rider`.
- Tour confirmation snapshots the current medal generation into `0x10D1`.
- `0x10D1` drives the TRACK_SELECT Bronze/Silver/Gold label and the stock keep-row comparison.
- Stock award increments the persistent medal cell by one generation.

## A/B design

Both runs use the same checksum-valid clean Crawler/MIKE SRAM with persistent medal 0.

### Control

Drive the ordinary stock path:

`MAIN_MENU -> RIDER_SELECT -> CRAWLER -> TRACK_SELECT -> DRAGSTER -> NOW PLAYING -> RACE`.

Expected baseline:

- TRACK_SELECT label: BRONZE;
- NOW PLAYING opponent: BRONSEN;
- live P2 rider index: 17;
- persistent Crawler/MIKE medal: 0.

### Transient variant

Drive the same path. After stock reaches settled TRACK_SELECT:

1. dump SRAM, proving stock snapshot `0x10D1 == 0`;
2. use the experiment-only snesref `spoke` patch to change **only** `0x10D1` to `2`;
3. dump again at zero guest frames to prove exactly one SRAM byte changed;
4. advance one guest frame;
5. continue to NOW PLAYING and race;
6. decode TRACK_SELECT label, card opponent name, live P2 rider index and palette.

The persistent medal cell remains 0 and its checksum remains valid throughout.

The `spoke` patch is deliberately applied only inside this workflow's private tool checkout. It is not added to the canonical snesrecomp toolchain patch set.

## Classification

`tools/probe_challenge_generation.py` returns one of four outcomes:

### `full-generation-seam`

Variant shows GOLD + GOLDWYN / rider 19.

Interpretation: `0x10D1` is sufficient to drive both presentation and canonical ordinary-tour opponent generation after tour confirmation. The next implementation should build a typed title adapter around that transient seam, then separately solve success commit semantics.

### `label-only-seam`

Variant shows GOLD but still BRONSEN / rider 17.

Interpretation: `0x10D1` owns presentation/row lifecycle but opponent identity was committed earlier or is sourced elsewhere. The next discriminator should locate only the CPU-opponent generation source. Do not widen to arbitrary WRAM mutation.

### `no-effect`

Variant remains BRONZE + BRONSEN.

Interpretation: TRACK_SELECT presentation and opponent generation are already materialized before the substitution. The next discriminator should move one boundary earlier, centered on the tour-confirm routine that writes `0x10D1`.

### `mixed-or-unexpected`

Any other combination.

Interpretation: retain the exact dumps and explain the mixed state before changing code. No production adapter is authorized.

## Acceptance invariants

Regardless of classification:

- control must reproduce Bronze/Bronsen;
- stock must first write `0x10D1 == 0`;
- the experiment must change exactly one byte at zero guest frames;
- persistent medal stays 0;
- persistent medal checksum remains valid;
- the variant reaches a real race.

Only those integrity checks determine whether the experiment itself is valid. A negative candidate result is still a successful discriminator.

## Stop rule

Once the classification is known, update the challenge-tier owning doc with that result and pursue only the single next seam it identifies. Do not start a broad progression trace, generic memory diff, or new medal search.
