# RF-030: executed CPU-to-SPC IPL ready read, echo and CPU-port handshake

**2026-10-16, research-only and source-exact.** Pinned game `gamesbyian/uniracers-recomp@10b864b9d14a7b7416dd909eb7b054c88faef101`, Baldosa runtime `075fbe4c8e0d97b0013be541795c39cb644a9709`, original Snes9x source `snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a`, original USA ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, original 2014 SMV SHA-256 `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442`. **No complete event admitted: USA 0/45.**

## Decision this experiment answers

After RF-029's exact original/native negative ([receipt](RF029-IPLCMP-BUS-PHASE-20261016.md)), changing the IPL `CMP $F4,#$CC` read alone from cycle 5 to 4 worsened sound upload parity. Its seven changed native frames +5040…+5046 were isolated by 78/78 identical original WRAM hashes across two completely separate original builds; sampled full WRAM agreement fell 51/78 to 46/78, while the true +5163 Zoo result, authentic +267 Bowl continuation, and 11/11 full earned SRAM pairs held.

The next missing causal evidence is the **actual ordered CPU↔SPC transaction** around the NMI-disabled Zoo driver upload, not the inferred source instruction sequence alone. Specifically capture the SNES CPU `$2140=$CC` write (and subsequent CPU `$2140` reads), the SPC `$F4` IPL compare-read at PC `FFD2` immediately after `78 CC F4`, the SPC output-port echo write, and the native queued write's scheduled/applied phases. This can determine whether the early observation arises from the sender/queue, reader, echo or their combination, before any corrective implementation is attempted.

## Implemented read-only apparatus

`tools/qa01_ipl_echo_trace_patch.py` rejects unfamiliar file revisions and injects opt-in **non-mutating** observers into disposable source checkouts: original Snes9x SMP `op_read/op_write`, SMP cycle increments and CPU `S9xAPUReadPort/S9xAPUWritePort`; native Baldosa `apu_schedulePortWrite`, `apu_writePortNow`, `apu_cpuRead`, `apu_cpuWrite`. No ROM, input, guest timing, SPC opcode timing, dynamic IP, Windows source, shipping binary or Modern persistence is changed. Capture requires `UR_QA01_IPL_ECHO_TRACE=1` and is bounded to original `ICPU.Frame 6050…6064` and native APU `portClock 103300000…103345000`, each independently calibrated. Both output explicit `*_TRUNCATED` on budget exhaustion.

`tools/qa01_ipl_echo_report.py` validates complete observations, untruncated clocks, correct executed source SPC compare PC/opcode, actual CPU write, SPC read/echo and native schedule/apply. It reports **each emulator's local SPC age and CPU-frame/beam phase independently**; it explicitly prohibits claiming cross-emulator phase equality, complete-event credit or all-frame parity. Unit tests require source pin/idempotence/negative unknown source, trace chronology, correct absence of any shipping instrumentation and failure on missing source or native events.

`.github/workflows/qa01-event-campaign.yml` adds manual/reusable opt-in `qa01_ipl_echo_trace`; requires the complete existing RF-015..019 + RF-021/023/024/026/028 stage, genuine Zoom Zoo `source_followthrough`, next Bowl, all 78 **unmasked** full-WRAM checkpoints and 13 consecutive original/native +5034..+5046 sound-DP samples. A temporary one-shot workflow runs this once on the research branch and **must be removed before merge**. The report is a bounded case artifact alongside original/native logs; no parallel factory or recurrence.

## Admission and stop rules

A valid executed receiver trace must show: first original CPU $CC age, original SPC compare-read age, original SPC echo age; equivalent native schedule/apply/read/echo ages; their own elapsed cycles and PC/opcode; 0 unmasked bytes skipped; source Zoo result +5163 and Bowl +267 and 11/11 full SRAM still hold. Reject traces missing any phase, exiting on truncated sample budgets, losing a true result or requiring controller retiming. The original/reference source exact binary and input/SRAM SHA must be recorded from the actual Actions run.

If the bus chronology is captured, derive the earliest phase disagreement **only** by comparing independently calibrated local ages, not by aligning frame labels or subtracting an arbitrary offset. A minimal CPU/APU corrective patch must then pass source-pinned negative regression and unmasked whole-WRAM checks; RF-018…028 remain opt-in research until an independently reviewable shipping decision. The entire run may be a negative if the observation range does not reach the IPL loop; that is evidence for tightening instrumentation, never an invitation to waive eligibility. Independently trace next-Bowl stack `7E:01ED–01F0` writer/reader liveness; untested transient stack differences are not automatically inert.

**0/45 admissions; independent QA continues to own the event census and release ledger.**
