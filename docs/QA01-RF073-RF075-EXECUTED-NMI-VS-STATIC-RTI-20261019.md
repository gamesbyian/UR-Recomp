# QA01: RF073 genuine live NMI vs RF075 pinned compiled RTI ABI, independent decision

**19 October 2026. ROM-free, read-only acceptance archaeology, NO event credit.** Two **distinct kinds of evidence** must be verified separately before combining their logical consequences:

- **Live original/native RF054 archive**: [Actions run 39161563837](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837), case artifact **12149640496**, ZIP SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`. Merged [RF073](RF073-AUTHENTIC-NATIVE-NMI-COMPILED-RTI-BRACKETS-20261019.md) source-byte consumer independently reopens all 2,741 actual native RF047 sequenced markers, fragmented unrelated logger prefixes, nine live native handler-return brackets and nine original NMI stack snapshots from this *same frozen experiment*. It observes exactly one real **status** helper read `01ED=26` inside each compiled NMI bracket, with **no saved PC/PB helper reads** between native push and compiled return. Four original/native **same-numbered-host-frame** saved low PCs are F0/EE, the other five EE/EE. No intra-frame instruction-phase alignment follows.
- **Static pinned RTI architecture**: source checkout of [RetroPortingToolKit/snesrecomp `075fbe4c...`](RF075-PINNED-NATIVE-COMPILED-VS-INTERP-RTI-20261019.md), verified from five immutable Git blobs; genuine [source-contract workflow 39322567648](https://github.com/gamesbyian/UR-Recomp/actions/runs/39322567648), artifact **12220307932**, source-contract ZIP SHA256 `b199009e3c7c924e0bd6a7d1842311296ce0bcc2afd8137b9980e1863db54e39` (one JSON, independently reopened with valid CRC and exact reported source blob hashes). At generated compiled RTI: read true stacked **P once**, advance S two bytes past **PC** and, in native mode, once past **PB**, **no guest read of saved PC/PB**, no restoring PC/PB register from those bytes. Host C/scheduler continuation remains authoritative. By contrast **interpreted RTI** performs real stack pulls for P, 16-bit PC and PB.

## What this combination proves, and what it does not

| Assertion | Evidence | Independent QA disposition |
|---|---|---|
| The nine native compiled handler brackets genuinely consume **status 26** | RF073 actual native helper; RF075 actual source ABI | **Observed / source-qualified** |
| The compiled RTI reads saved PC or PB to determine its next target | RF075 source has **zero** such reads | **No. Compiled ABI does not load them** |
| Four different saved-PC low bytes alone caused a wrong native continuation | Same host-frame snapshots, compiled continuation from scheduler | **Not proven**; stack byte is not compiled return target |
| Original/native interrupts happened at the same instruction-fetch boundary | No shared guest fetched-PC/beam/master witness in RF054 | **Not proven** |
| Original game rewrote a stacked PC/PB that compiled RTI then ignored | No complete same-case read/write before RTI with matched native phase | **Not proven** |
| Scheduler published an architectural PC different from original interrupted instruction | RF074 provenance and future real decode needed | **Not proven** |
| First original/native **actually consumed differing byte**, complete original/native course, exact Windows earned cold record | Partial historic experiments | **HOLD: 0/45, 0/12** |

An immutable source contract can describe a real **conditional** fidelity liability without demonstrating that this game exercised it. In particular, a native stack byte difference at `01EE` can be a *symptom of an interrupt-phase difference* while the compiled return uses a different scheduler path. The direct next tests are: (1) same-case native resume-origin ring assignment **versus independently decoded guest interrupted fetched PC**, not merely the vector or host saved cache, (2) original stack push→first actually returned byte→first write at the matched *semantic phase* alongside native executed RTI/continuation, (3) any authentic pre-return **saved target rewrite** and its effect on the very next decoded executed opcode, not only stored WRAM, and (4) uninterrupted full course raw frames, result, handoff, original/native input, cold earned record and exact Windows source/PE/ZIP. **No speculative gameplay patch, byte mask, clock shift or release promotion.**

## Reproduce the decision from BOTH real ZIPs

```bash
python3 tools/qa01_independent_rf073_rf075_return_decision.py \
  --rf054-case /path/to/authentic-rf054-original-native-case.zip \
  --rf075-source-contract /path/to/authentic-rf075-source-contract.zip \
  --output /tmp/qa01-rf073-rf075-abi-vs-runtime.json
python3 -m unittest tests.unit.test_qa01_independent_rf073_rf075_return_decision -v
```

This **new independent QA verifier** refuses replaced ZIP bytes, an extra/missing RF075 receipt member, changed source Git blob, a falsely claimed PC/PB guest-load or source/native clock equivalence, missing native brackets/status, changed saved PC or unearned gate. It uses merged RF073's **exact true original/native case auditor** rather than reconstructing observations from unrelated RF044 stderr fragments, and checks source semantics from RF075's complete source-pinned code-contract output rather than an assumed generic 65816 description. The output explicitly labels the nine **host-frame observations as non-joinable across guest clocks**. It is not a same-core A/B run or a producer of an executed native fetched opcode PC.
