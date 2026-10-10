# QA-01: original vs Baldosa same-host 5782 raw-memory difference observation

**Observed 2026-10-10:** one-shot [workflow run 38078429375](https://github.com/gamesbyian/UR-Recomp/actions/runs/38078429375), job `original-native-switcher-race-b`. **Research evidence only.** The temporary workflow PR #1195 is intentionally NEVER-MERGE; source opt-in diagnostic code merged in #1193. Preserve this non-ROM factual result in the permanent source.

At authenticated **absolute host frame 5782**, the actual original Snes9x and Baldosa completed-script witnesses are each one host frame before their matching positive P1 result `MIKE 1:08.81` at host frame **5783**. Source entered course at host 1079, native at 1081, with different guest-relative terminal offsets, original +4704/native +4702. Both used unchanged archived 2014 original movie input and verified ROM.

The full memory comparison in the completed job report records:

| Guest memory class | Bytes compared per engine | Different byte count | Exact match? |
|---|---:|---:|---|
| WRAM | 131,072 | **8** | No |
| VRAM | 65,536 | **0** | Yes |
| CGRAM | 512 | **0** | Yes |

WRAM different-byte offsets (only addresses, no ROM or memory bytes): `0x001DD`, `0x001E6`, `0x001E7`, `0x001EF`, `0x001F0`, `0x001F1`, `0x001F2`, `0x001F3`. All 21 separately sampled named state fields match on the same host frame. The complete 197,120-byte guest-state pair is **not** equal.

The job ended with expected failure due to the unchanged **strict guest-relative terminal comparator**, rather than being a passing original/native event. This is a valid diagnostic outcome, **not** permission to relax or bypass the original/native gate. Official USA full-event acceptance remains **0/45**. Equal VRAM/CGRAM at this single frame cannot establish CPU PC, NMI phase or all-frame equality. Eight differing WRAM addresses are observations, not evidence that gameplay physics is wrong.

Future work: identify the original instruction writers and scope of these eight offsets; prioritize whether differences matter to result, timing, progression or user-visible behavior before launching another experiment. Do not retain the temporary workflow override in production. Retain [run artifact 11679710756](https://github.com/gamesbyian/UR-Recomp/actions/runs/38078429375/artifacts/11679710756) provenance; short artifact retention means this committed address/count report is the durable summary.
