# S2 execution-report comparison

`tools/compare_s2_execution_reports.py` compares the retained desktop S2 digest reference with the report produced by the Switch S2 hardware execution probe.

The comparison is deliberately strict:

- both reports must contain frames 0, 1, 60 and 120 exactly;
- both must report successful `SnesInit` and bounded execution completion;
- master, CPU, WRAM, APU, PPU, DMA and cart digests must match at every checkpoint;
- failure output identifies the first divergent frame and partition.

Example:

```bash
python3 tools/compare_s2_execution_reports.py \
  desktop-reference.txt \
  ur-recomp-s2-execution-report.txt \
  --json-out switch-s2-parity.json
```

A zero exit status means all retained simulation checkpoints match. A non-zero exit status means either the report contract is incomplete or the first differing checkpoint has been identified. Presentation, audio-device timing and other host-only state are intentionally outside this digest domain.
