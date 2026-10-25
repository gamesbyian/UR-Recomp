# RF083: original Zoo sound direct-page first-writer probe

**Source-only; not yet an executed guest or release-acceptance result.**

Historical archived producer: [run 40168208753](https://github.com/gamesbyian/UR-Recomp/actions/runs/40168208753), case artifact 12589271295, SHA256 02c23eef482e1841f61d5df7d48e87f8d7898d625dd5ad7b75f59d3414deb68b. Its authentic original/native WRAM snapshots are byte-exact at Zoo +5039; at +5040 the only two differing raw WRAM bytes are sound pointer low $0063 and transfer count $0069. The observed P1 input mask is unchanged across the one-frame boundary. This is not CPU input-read equivalence.

The new opt-in source adapter is applied ONLY to a disposable, exact-source Snes9x reference copy using python3 tools/qa01_rf083_original_sound_dp_first_writer.py --root PATH and the environment flag UR_QA01_RF083_ZOO_DP=1. It inserts a bounded observer into the genuine already-fetched original CPU opcode dispatch, watching original internal ICPU.Frame 6069..6079. Independently, it hooks the ENTRY of the existing S9xSetByte function. The observer watches $0063/$0064/$0065/$0069 using direct host WRAM snapshots; it does not perform extra guest bus calls, CPU dispatches, APU operations or clock charges.

QA01RF083ORIG_HEART establishes observed original internal frames. QA01RF083ORIG type=opcode_delta identifies a changed raw byte within one executed opcode interval and records the originally fetched PC/opcode and pre/post beam position. type=setter_entry identifies a genuine S9xSetByte invocation for a potentially matching address, retaining the entire 24-bit address and passed value. The setter record is emitted BEFORE mapping/commit. An opcode delta with zero observed setter entries is unattributed. QA01RF083ORIG_TRUNCATED invalidates coverage; absence of a heartbeat invalidates claims of nonexecution.

**Original ICPU.Frame is not the scene script frame or native host/master clock.** A genuine RF037 probe placed original sound execution near internal frames 6072..6080; the deliberately wider 6069..6079 window is a provisional sampling choice, not frame registration. This patch neither proves native compiled-opcode identity nor verifies any actual original source execution. To turn it into causal proof, run one exact-bound authenticated Zoo original/native producer, preserve the untruncated logs and raw paired frames, join a real mapped setter to a first live consumer, and separately instrument actual native generated-PC/continuation and CPU/SPC port clocks. Do not equate matching low 16-bit addresses with a committed WRAM write. No release-gate credit.

## 2026-10-25 executed original RF083 case and independent nonperturbation control

The [single manual disposable run #40237658745](https://github.com/gamesbyian/UR-Recomp/actions/runs/40237658745) passed plan, original/native build, Zoo case and aggregate. Original case artifact **12615823047** (ZIP SHA256 `97d72f79b4b1879cb1bbee8f606addf23d22b8c6d58cc85d0c47707278c02cc1`) contains 402 individually CRC-verified members and actual original CPU opcode trace. Independently reopened [prior control producer #40168208753](https://github.com/gamesbyian/UR-Recomp/actions/runs/40168208753), artifact **12589271295** (ZIP SHA256 `02c23eef482e1841f61d5df7d48e87f8d7898d625dd5ad7b75f59d3414deb68b`): all **320** common actual original/native raw WRAM/SRAM images are **byte-identical**, with no masks. This is *sampled-state* nonperturbation proof, not unchanged execution between samples. Source/native full WRAM agrees at +5039 and differs only at $0063/$0069 at +5040. The native executable SHA remains `869df40fb63ed1e50e0ffc164d9bdd8986fcc003010fc79d4d110109a654ed5d`; original core changed intentionally to the instrumented SHA `a7f7b3908c1ac16a9aa9150e6b6c0d66d79f932852fd9909d86be59331316d4e`.

**Actual executed original opcode intervals**, source-internal ICPU.Frame heartbeats 6069 through 6079, no truncation, contiguous event ordinals 1..3122:

| Byte | Original opcode-boundary raw byte changes | Fetched original guest PC and opcode populations |
| --- | ---: | --- |
| $0069, sound transfer counter | 1,482 | `82:80E0` E6 INC: **1,482** |
| $0063, low transfer pointer | 1,554 | `82:8154` E6 INC: 1,481; `82:814B` 85 STA: 69; `82:82CE` 64 STZ: 3; `82:813B` 85 STA: 1 |
| $0064, high transfer pointer | 78 | `82:814B` 85 STA: 64; `82:8154` E6 INC: 6; `82:813B` 85 STA: 4; `82:82D0` 64 STZ: 4 |
| $0065, sound bank | 8 | `82:8145` E6 INC: 5; `82:812F` 85 STA: 3 |

**Zero** corresponding watched `S9xSetByte` entries occurred. This demonstrates the generic setter hook does not witness these instruction-interval deltas; it **does not** show that no physical bus write happened, that the Snes9x instruction produced a native-equivalent value, or that any of these is the first divergent read-before-overwrite. Source original ICPU.Frame labels are *not* original script host frames or native host/master/SPC clocks. The observed original source M1X0 opcode sites, especially **82:80E0** and **82:8154**, are now source-qualified leads for the CPU/APU **native live generated-code actual executed PC / compiled continuation and first consumed sound-port observation**. A source-generated marker in unused mode, AOT direct memory helper bypass, missing original/native CPU input polls, or absent port-echo observation must not be interpreted as parity. Actual same native AOT source branch plus $2140..43 SPC receiver is still unresolved. The physical Windows product remains unapproved; course acceptance **0/45**, Windows gates **0/12**.

To reproduce the bounded archive classification **without rerunning any guest or accessing the local ROM**, download both immutable case ZIPs and run:

```bash
python3 tools/qa01_rf083_source_dp_archive_audit.py \
  --baseline previous-zoo-case.zip \
  --instrumented rf083-zoo-case.zip \
  --baseline-sha256 02c23eef482e1841f61d5df7d48e87f8d7898d625dd5ad7b75f59d3414deb68b \
  --instrumented-sha256 97d72f79b4b1879cb1bbee8f606addf23d22b8c6d58cc85d0c47707278c02cc1 \
  --expected-common-raw 320 \
  --out rf083-rechecked.json
```

The audit requires both complete ZIP identities and CRCs, original movie/ROM/native executable identities and source Zoo mesh equality, byte-exact shared original/native raw image members, genuine 11 heartbeats and all source event ordinals, correct +5039/+5040 complete 128-KiB WRAM residuals and never grants release credit. The permanent small source-backed checkpoint is [analysis/data/qa01-rf083-executed-original-evidence-20261025.json](../analysis/data/qa01-rf083-executed-original-evidence-20261025.json). Temporary experiment [PR #2590](https://github.com/gamesbyian/UR-Recomp/pull/2590) was closed **unmerged** after one authentic run.
