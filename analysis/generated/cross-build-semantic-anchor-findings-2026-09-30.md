# Cross-build semantic anchor findings — 2026-09-30

This report applies relocation-resistant correspondence to eight trusted USA semantic anchors across the four preserved builds.

The first-pass matcher uses:
- relocation-tolerant byte n-gram voting;
- whole-window byte-shape similarity;
- known WRAM/PPU operand relationships;
- explicit inspection of byte deltas at the top candidate.

Same-address status is recorded but is not used as proof.

## Anchor correspondences

| USA semantic anchor | USA | Legacy beta | PAL prototype | Europe retail | Current reading |
|---|---|---|---|---|---|
| racer frame update | `82:89B9` | `82:89B9`, exact | `82:89B6`, strong | `82:89CC`, strong | same semantic pipeline, locally relocated/repacked |
| course load/materialize | `82:E165` | `82:E165`, exact | `82:E101`, strong | `82:E12B`, strong | same loader/materializer family |
| racer OAM projection | `82:ACA5` | `82:ACA5`, exact | `82:AC96`, strong | `82:ACAC`, supported | same world→camera→screen seam |
| checkpoint/finish | `81:8050` | `81:8050`, exact | `81:8050`, supported/strong | `81:8042`, candidate | prototype retains address but changes state operands; Europe needs another local discriminator |
| HUD/message enqueue | `81:C5B3` | `81:C5B3`, exact | `81:C590`, very strong | `81:C59C`, supported | PAL body is 96.9% byte-similar with full known queue-reference retention |
| collision shape builder | `81:9E2A` | `81:9E2A`, exact | `81:9E0A`, very strong | `81:9E1B`, very strong | bodies are 99.1% / 96.9% similar; changed bytes expose shifted WRAM operands |
| collision velocity transform | `81:9546` | `81:9546`, exact | `81:9526`, very strong | `81:952C`, very strong | matrix/velocity structure preserved while working-state addresses move |
| stunt finalizer | `82:9A42` | `82:9A42`, exact | `82:9A3D`, strong | `82:9A53`, strong | stunt-state layout shifts coherently with other systems |

The legacy beta is exact for all eight tested anchors, consistent with the known 486 isolated USA/beta byte differences living elsewhere in the ROM.

## Aggregate operand-motion evidence

The final successful corpus run mechanically projected known USA LE16 semantic operands through each top structurally aligned candidate.

Aggregate displacement evidence:

| Build | Dominant displacement families |
|---|---|
| legacy beta | `+0`: 212 |
| PAL prototype | `+4`: 108; `+0`: 90 |
| Europe retail | `+10`: 99; `+4`: 38; `+6`: 28; `+0`: 19 |

These counts are not a claim that every occurrence is an independently named variable. They measure repeated structurally aligned operand motion across the trusted anchor corpus. The fact that the same small set of deltas recurs across unrelated routines is the useful signal.

## A second structural signal: coherent WRAM layout translation

The top candidates do more than resemble the USA bytes. At the same relative instruction positions, known USA state operands repeatedly become nearby but different WRAM addresses in the other builds.

### PAL prototype: repeated +4 semantic displacement

Examples from unrelated routines:

| USA semantic address | PAL candidate operand | Seen in |
|---:|---:|---|
| `0E89` | `0E8D` | course loader |
| `0E8B` | `0E8F` | course loader |
| `15A1` | `15A5` | course loader |
| `1645` | `1649` | course loader |
| `16E9` | `16ED` | course loader |
| `0F7B` | `0F7F` | collision shape |
| `0F47` | `0F4B` | collision shape |
| `125B` | `125F` | derived collision geometry |
| `0F9F` | `0FA3` | collision velocity |
| `0FA1` | `0FA5` | collision velocity |
| `119D` | `11A1` | checkpoint/finish |
| `1361` | `1365` | stunt state |
| `11F9` | `11FD` | stunt counters |
| `11FD` | `1201` | stunt counters |
| `1201` | `1205` | stunt progress |
| `1205` | `1209` | stunt progress |

This is cross-system evidence that the PAL prototype uses a related WRAM layout with a recurrent four-byte displacement in several structures.

### Europe retail: repeated +10 semantic displacement, plus structure-specific exceptions

Examples:

| USA semantic address | Europe candidate operand | Seen in |
|---:|---:|---|
| `0E89` | `0E93` | course loader |
| `0E8B` | `0E95` | course loader |
| `15A1` | `15AB` | course loader |
| `1645` | `164F` | course loader |
| `16E9` | `16F3` | course loader |
| `0F7B` | `0F85` | collision shape |
| `0F47` | `0F51` | collision shape |
| `125B` | `1265` | derived collision geometry |
| `0F9F` | `0FA9` | collision velocity |
| `0FA1` | `0FAB` | collision velocity |
| `0EF1` | `0EFB` | checkpoint/lap state |
| `1361` | `136B` | stunt state |
| `11F9` | `1203` | stunt counters |
| `11FD` | `1207` | stunt counters |
| `1201` | `120B` | stunt progress |

But Europe is **not** a simple whole-WRAM +10 translation. The message-ring block instead moves by +6:

- `0CBB → 0CC1`
- `0CE1 → 0CE7`
- `0CE3 → 0CE9`
- `0CE5 → 0CEB`
- `0D0B → 0D11`
- `0D0D → 0D13`

The racer/OAM family also shows different local displacements. This points to structure-specific insertion/removal/repacking rather than one global relocation.

## Why this matters

This converts cross-build differences from nuisance into semantic evidence.

If a structurally matched routine changes only a family of operands by the same delta, those operands are likely members of the same relocated/repacked state structure. Conversely, where one field does **not** follow the dominant local translation, that exception becomes a high-value clue: it may mark a field added/removed between builds, a split/merged structure, or a genuinely different behavior path.

Practical consequences:

1. Build-specific symbol maps should be derived by structural correspondence plus local address translation, never copied by literal address.
2. The PAL prototype is especially valuable because several core routines remain 72–99% byte-similar while exposing small, mechanically interpretable state-layout changes.
3. Europe retail provides an independent later layout with larger structure-specific shifts, useful for inferring field grouping.
4. The strongest next pass is to convert these repeated operand translations into **WRAM structure clusters**: fields that move together across builds belong together more plausibly than fields that merely sit near each other in USA.
5. Cross-build field-motion can therefore help reconstruct lost structs/records even before every field is semantically named.

## Confidence boundaries

Promoted as strong correspondence:
- all eight legacy-beta anchors are exact;
- PAL course loader, racer update, racer OAM, HUD queue, collision shape, collision velocity, and stunt finalizer;
- Europe course loader, racer update, collision shape, collision velocity, and stunt finalizer.

Still requiring another local discriminator before semantic-label transfer:
- Europe checkpoint/finish;
- Europe HUD/message enqueue;
- some Europe OAM substructure;
- exact semantics of every shifted-but-unnamed WRAM field.

## Next high-value action

Build a cross-build WRAM motion atlas from trusted structurally matched routines:

- collect every absolute/DP WRAM operand in each matched anchor;
- align operand positions structurally;
- cluster address pairs by shared displacement and co-occurrence;
- identify stable fields, shifted blocks, insertions/removals, and exceptions;
- feed those clusters back into `docs/SYMBOLS.md`, decompilation gaps, and course/physics/rendering structure inference.

That should recover parts of the original logical data structures without needing source declarations.
