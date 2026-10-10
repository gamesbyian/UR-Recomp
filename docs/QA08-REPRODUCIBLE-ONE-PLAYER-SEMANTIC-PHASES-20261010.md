# Automated 1P semantic phase audit

The source-authenticated native 1P phases were discovered and documented
in [QA08-ONE-PLAYER-SEMANTIC-PHASES-20261010.md](QA08-ONE-PLAYER-SEMANTIC-PHASES-20261010.md).

To reproduce the phase classification from **the real raw native
artifact** `11684526840` (AOT run `38091207834`, PR #1231):

```sh
python3 tools/report_baldosa_1p_semantic_phases.py \
  --baseline-crc path/to/baldosa-evidence/race_1p/fd/crc.txt \
  --candidate-crc path/to/baldosa-evidence/race_1p_ur_ws342_live/fd/crc.txt \
  --log path/to/baldosa-evidence/race_1p_ur_ws342_live/log.txt \
  --out path/to/reproduced-phase-summary.json
```

The script requires the **same** full independent 5,447-frame guest
CRC match, the original race-script entry and terminal milestones,
one unique source-observed semantic state per actual native guest
frame, a nontrivial contiguous held interval, and no gaps between
classifications. It automatically identifies the three predominant
semantics *before* the longest same-semantic held run, finds their
last source occurrence, and separates motion-rich, transitional,
and held windows. It separately retains the companion-gate
distribution of the long held state.

It does not make the held state a confirmed game terminal or result
scene, does not grant sprite visibility, and cannot certify any
authored HD racer or a Windows beta. It is a reproducible audit of
one source-observed guest route, not a new scoring or gameplay path.
