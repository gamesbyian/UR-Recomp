# GameHacking.org Uniracers code concordance

Source: https://gamehacking.org/game/45291  
Retrieved: 2026-10-05  
Canonical ROM identity on source page: Uniracers (USA), CRC32 `383858C7`.

This is a project-owned transcription/normalization of the public code metadata needed for reverse-engineering triage. It is not an emulator cheat pack and does not treat code descriptions as verified game semantics.

The existing imported libretro corpus at `reference/imported/libretro/Uniracers (USA).cht` already preserves 24 historical cheats. The table below highlights GameHacking.org entries that are either absent from that corpus or provide a more direct RAM/ROM form than the libretro entry.

| Reported behavior | Code / write | Relationship to libretro corpus | Research value |
| --- | --- | --- | --- |
| 1 Z-Flip = 1 Z-Flip City | `829620:EB` | New direct ROM write; libretro has only Game Genie `38B4-CDDB` | Direct localization of stunt-classification code |
| CPU racers brake at start | `828ECF:FF` | New direct ROM write; libretro has Game Genie form | Direct localization of CPU-start/braking behavior |
| Double/treble rolls or flips from one | `829B50:A1` | New direct ROM write; libretro has Game Genie `CFB9-3DDC` | Direct localization of stunt-count classification |
| Jump in Midair | `C264-CF65` + `BA6D-CD65` | New | High-value probe for jump eligibility / airborne gate |
| Max qualifying score | `7007BB:FF`, `7007BC:01`, `7E0CE1:FF` | New direct RAM form | Anchors P1 score backing and queue/read state; descriptions require local verification |
| Background/track/racer color mutation | `0220DD:D7` | New direct write distinct from libretro color hacks | Presentation/state localization |
| Quick Win in Lap Missions | `7E0EF1:01` | Duplicate of libretro `7E0EF101` | Confirms laps-remaining probe; already locally meaningful |
| Race Any Track | `AAB4-370E` | Duplicate | Existing route-selection probe; source notes some menu states crash |
| Time Modifier (Seconds) | `7E0E17:??` | Same address as libretro `7E0E1700` | Confirms explicit seconds field |
| Always win draw at 00:00:19 | `7E1B8D:00` | Same raw address as one libretro color entry, exposing inconsistent historical descriptions | Strong reason to verify rather than trust labels |

GameHacking.org also repeats the familiar timer, speed, lead-indicator, strobing-background, arbitrary-course and stunt-classification Game Genie codes already present in the libretro corpus.

## Immediate conclusions

- Do **not** import another cheat pack merely to duplicate existing Game Genie strings.
- The unique direct ROM writes (`829620`, `828ECF`, `829B50`) and the two-code midair-jump patch are the useful additions.
- The qualifying-score RAM writes are especially useful because `77:07BB` is already independently identified by recovered Nitrodon code as the P1 backing stunt score. This makes the external label partially corroborative rather than a new semantic authority.
- The conflicting `7E:1B8D` descriptions illustrate why historical cheat labels must be treated as leads only.

Before promoting any newly named behavior, reproduce the relevant code/write against the canonical ROM/runtime and record the exact state delta.
