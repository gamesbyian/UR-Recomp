# USJO v8 static inventory

Generated from `references/imported/tas-bots/usjo8.lua` by `tools/inventory_usjo8.py`.

This is **recovered-source evidence**, not promoted game truth. The variable names,
addresses, timing assumptions and scoring rules below describe what the 2008 bot
reads or assumes. Each item still needs canonical-ROM/runtime reproduction before it
can become an authoritative symbol or gameplay rule.

Source lines: 1459

## RAM reads

| Address | Width | USJO v8 variable | First/only source line |
|---|---:|---|---:|
| `0x7E04B7` | 16 | `curspeed` | 144 |
| `0x7E04BB` | 16 | `yspeed` | 210 |
| `0x7E0545` | 8 | `airflag` | 218 |
| `0x7E0F61` | 8 | `numtwists` | 219 |
| `0x7E042F` | 8 | `numtabletops` | 220 |
| `0x7E042B` | 8 | `numzflips` | 221 |
| `0x7E11F9` | 8 | `numrolls` | 222 |
| `0x7E11FD` | 8 | `numflips` | 223 |
| `0x7E0DFD` | 8 | `zrotation` | 224 |
| `0x7E0F57` | 8 | `zprerotation` | 225 |
| `0x7E11CD` | 8 | `realboostmeter` | 226 |

The alternative X-speed address mentioned only in a source comment is deliberately
not classified as a read. Static comments remain leads until tested.

## Comment-encoded state enums

- `changedirection`: `0` = no; `1` = yes
- `mode`: `0` = initializing; `1` = jumping; `2` = first twist; `3` = stunt; `4` = replaying best; `5` = done
- `jumpstatus`: `0` = not trying to jump; `1` = trying to jump; `2` = airborne; `3` = peaked; `4` = landed
- `twiststatus`: `0` = not trying; `1` = waiting for back twist to finish; `2` = waiting for front twist to finish
- `strategy`: `1` = build up; `2` = individual maximums; `3` = tear down from maxes

## Search/timing constants

The JSON artifact records every literal top-level local initialized before the bot's
savestate/setup section, including search-window, jump, tabletop, twist, rut and
loop-detection parameters. They are source constants, not yet game constants.

## Boost/scoring rule source block

The recovered bot's hand-authored boost estimate and final score calculation occupy
lines 946-995. The machine-readable artifact preserves
that complete source block. It combines stunt-count thresholds into
`thisboostmeter`, zeros that estimate when direction/speed is wrong or
`realboostmeter == 0`, then sets `finalscore = thisboostmeter + lastspeed`.

## Controller policy source block

The final controller-output policy occupies lines 1392-1446.
The JSON preserves the whole block plus every assignment to the intermediate control
signals `jumping`, `reverse`, `rolling`, `flipping`, and `xing`.

## How to use this

1. Pick one RAM field or source rule from the JSON inventory.
2. Reproduce it against the canonical ROM/runtime with the smallest deterministic fixture.
3. Promote only the reproduced semantics into `docs/SYMBOLS.md`,
   `docs/RESEARCH-LEDGER.md`, and regression fixtures.
4. Keep unsupported USJO names as historical aliases/leads rather than silently treating
   the 2008 script as specification.
