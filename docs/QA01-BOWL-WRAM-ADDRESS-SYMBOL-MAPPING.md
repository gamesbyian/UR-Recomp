# QA-01: source-annotate original/native Bowl WRAM discrepancies

The source-original Bowl scored Stunt and pinned Baldosa agree on all **28 active gameplay semantic samples** and show the same PPU tally and MIKE **764** score. A follow-up [eight-frame same-host tally phase witness](../analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json) captured original/native byte disagreements of 6, 6, 50, 14, 6, 6, 22, 16 in 128 KiB WRAM. In those frames the original/native menu, course, and in-race bytes match, VRAM differs by only two bytes once, and CGRAM always matches. The first witness retained **counts only**, not addresses.

PR #1142 extends the bounded original/native producer to retain at most 128 **differing addresses per memory class per frame**, never guest-memory contents, and a real intersection only if no frame is truncated. This independent source-only utility is deliberately *not* wired into another native build. Once #1142 has passed and merged, retrieve its small `bowl-report.json` CI artifact and run:

```bash
python3 tools/annotate_bowl_guest_memory_offsets.py \
  --report /path/to/bowl-report.json \
  --out /tmp/bowl-guest-memory-symbols.json
```

The tool validates the exact offset-only producer schema, eight sampled original/native frame pairs, bounded truncation flags, zero course credit and valid five-digit WRAM offsets. It maps each raw WRAM offset to its 7E/7F bank/offset and the most specific containing names in the **imported pinned Baldosa** `decomp/ram.txt`. More specific labels are ranked ahead of broad scratch/work-area ranges. Multiple aliases may cover one address; a name is a **source-visible reverse-engineering hypothesis**, not proof of active runtime ownership, game physics, CPU instruction or NMI time.

Unknown addresses remain unknown. Truncated profiles are explicitly marked incomplete and cannot support an exhaustive shared-difference inference. The tool does not load the USA ROM or write any raw original/native memory bytes to an artifact. It is fully independent of the frontend, HD graphics, controller routing and original/NMI timing implementation. **QA-01 accepts 0/45 complete USA courses**, including Bowl, until a distinct reviewed complete-event frame-parity gate is passed.
