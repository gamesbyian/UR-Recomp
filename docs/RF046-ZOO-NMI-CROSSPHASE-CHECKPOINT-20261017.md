# RF046: exact first Zoo checkpoint stack bytes match opposite source-NMI phases

**Pure analysis of existing executed RF044 case; zero new hosted replay, zero CPU/APU timing mutation, complete USA events 0/45.**

The independently rehashed [RF044 genuine USA Zoo case 12118217074](https://github.com/gamesbyian/UR-Recomp/actions/runs/39078406796/artifacts/12118217074), ZIP SHA-256 `84d6906af7ebfe0dee3f77fb90b4c4f50400fc7c45add3e586f14035daf15357`, has the source-original `QA01RF044ORIGNMI` true non-opcode Snes9x NMI pre/post stack snapshots, and the 78 independently sampled original/native whole 128KiB unmasked WRAM checkpoints. The original and native fresh-host frame references are from separately executed guests, **not an assertion that their 65816 instruction or NMI phases are aligned**.

## Newly confirmed four-byte cross-phase identity

`7E:01ED–01F0` in hexadecimal byte order:

| Checkpoint relative / guest host | Preceding source-original NMI host, interrupted PC | Source NMI **before** image | Source NMI **after** image | Original checkpoint | Native checkpoint |
|---|---|---|---|---|---|
| **+1 / 1018** | 1017, `82:D4F0` | `81 97 00 55` | `26 F0 D4 82` | **`26 F0 D4 82`** | **`81 97 00 55`** |
| **+2 / 1019** | 1018, `82:D4EE` | `81 97 FF 27` | `26 EE D4 82` | **`26 EE D4 82`** | **`81 97 FF 27`** |
| **+4 / 1021** | 1020, `82:D4EE` | `81 97 FF 27` | `26 EE D4 82` | **`26 EE D4 82`** | **`81 97 FF 27`** |

Thus **in each of the three earliest sampled mismatching Zoo frames**, every original checkpoint byte equals the **preceding host's actual original NMI *post*** byte and every native checkpoint byte equals that *same actual original NMI's pre* byte. Across these three frames: twelve exact original-post correspondences and twelve exact native-pre correspondences, **24/24 byte comparisons**, not simply a two-byte return-PC resemblance. The first source NMI was actually executed once per host 1017–1025 with SP `01F0→01EC`; the complete WRAM was equal at +0 and again by +8.

This supports the **transient interrupt-stack observation-phase hypothesis** more strongly than calling the four bytes arbitrary gameplay state drift. It does *not* establish when the native NMI actually ran relative to its checkpoint, whether its interrupt PC is correct, whether CPU stack entries were consumed before overwrite, or that the discrepancy is safe to exclude. No byte may be masked for acceptance.

The preceding host offset matters. At source host1018, for example, the source NMI's own new `26 EE D4 82` is **not** the source checkpoint at +1/host1018; that checkpoint equals host1017's post-NMI `26 F0 D4 82`. A future probe must explicitly correlate source/native NMI/RTI boundaries with checkpoint sampling phases rather than compare same-labeled host numbers blindly.

## Reproducible fail-closed audit

`tools/qa01_rf046_zoo_nmi_checkpoint_crossphase.py` consumes the original immutable ZIP and refuses other SHA identities, any missing/truncated/malformed source NMI, incomplete original and native paired 78-checkpoint mesh, any nonzero masking, absent +0/+8 whole-WRAM equality, shifted checkpoint hosts, a changed mismatch address or one wrong pre/post byte. It independently checks 51/78 exact whole WRAM pairs, 92 unmasked differing-byte occurrences and explicit 0 release credit. Machine result in [`analysis/data/rf046-first-zoo-nmi-crossphase-20261017.json`](../analysis/data/rf046-first-zoo-nmi-crossphase-20261017.json).

```bash
python3 tools/qa01_rf046_zoo_nmi_checkpoint_crossphase.py \
  /path/to/qa01-campaign-case-zoom-zoo.zip \
  --output /tmp/rf046-crossphase.json
```

The report strictly sets `native_actual_NMI_instruction_phase_from_correspondence_proven=false`, `original_physical_bus_writer_reader_proven=false`, `differing_stack_bytes_never_consumed_proven=false`, and `complete_USA_events_admitted=0`. It does not retime a game or replace the strict source comparator.

## Next actual executed discriminator

[RF045 draft #1812](https://github.com/gamesbyian/UR-Recomp/pull/1812) is already implementing the genuine source-original Snes9x `cpuops.cpp` stack `PushB/PushW/PullB/PullW` bus macro witness after RF044's unsuccessful `getset.h` hook. Reuse that evidence, **do not dispatch a redundant investigator**. Record true source NMI push sequence / original stack pulls (if any) before overwrite and compare to the native genuine NMI/RTI instruction-phase and actual first consumer. RF044's native `IPC=80EFDA` annotation was stale across unrelated scopes, so it must **not** be taken as a precise source PC witness; independently resolve native NMI return PC and interrupt timing. Native stdout/stderr WRAM writer/read logs interleave, so total line order does not prove a first read.

If the original/native samples prove two *different* observation phases of an otherwise matching event, that would explain the transient stack residues without timing mutation, but full original/native CPU-state parity and strict all-frame source-event acceptance remain separate obligations. **0/45 USA complete events.**
