# Racer spatial placement generalization — 2026-10-02

## Result

The recovered 5×6 racer occupancy lattice has a stable spatial interpretation in retained ordinary-2P runtime evidence:

- `major_slot` = stored 8×8 tile **row**
- `minor_slot` = stored 8×8 tile **column**
- the 5×6 rectangle is placed at tile-grid offset **(1,0)** inside the stable 64×64 racer OBJ
- OAM H/V flip is applied later, after stored-cell placement, to obtain the presented orientation

The retained race snapshots use `OBSEL = 0x83`, which selects 16×16 small and 64×64 large OBJ sizes.

## Generalization evidence

The retained ordinary-2P artifact contains 9 snapshots. Scanning each snapshot's actual persistent racer IDs at `$0FE9/$0FEB`, OAM and VRAM produced:

- **8 exact persistent-ID spatial bindings**
- **17 unique nearby-ID occupancy bindings** within ±3 IDs
- every unique binding uses the same 5×6 tile-grid offset **(1,0)**

Representative exact bindings include:

| Checkpoint | Player | Persistent ID | OAM slot | OAM tile | Packed cells | Offset |
|---|---:|---:|---:|---:|---:|---:|
| two-player-race-1220 | P1 | `0x0541` | 98 | `0x00` | 12 | (1,0) |
| two-player-race-1220 | P2 | `0x0540` | 99 | `0x88` | 13 | (1,0) |
| two-player-race-1420 | P2 | `0x0544` | 99 | `0x88` | 15 | (1,0) |
| two-player-p1-post-1520 | P1 | `0x027A` | 98 | `0x00` | 15 | (1,0) |
| two-player-p2-post-1570 | P1 | `0x017B` | 98 | `0x00` | 15 | (1,0) |
| two-player-both-post-1620 | P1 | `0x033A` | 98 | `0x00` | 15 | (1,0) |

The nearby-ID matches are useful evidence for spatial-family stability but are not promoted as frame-identity proof because neighboring animation frames can share the same occupancy mask.

## Timing note

The raw WRAM snapshots clarify an earlier endpoint discrepancy: for example, frame 1220 contains persistent P1 ID `0x0541`, while an earlier renderer-observed trace reported `0x0542`. This is a state-to-presentation timing seam, not a failure of the spatial mapping.

## Evidence

- tool: `tools/analyze_racer_spatial_generalization.py`
- retained ordinary-2P run: **36943103609**
- successful generalization workflow: **36978560724**
- canonical data surface: `analysis/data/presentation-assets.json`
