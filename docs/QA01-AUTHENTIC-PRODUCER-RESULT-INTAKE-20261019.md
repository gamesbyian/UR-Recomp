# QA01 authentic producer consumption: nine-frame Zoo A/B and negative RF062 build

**19 October 2026.** Independent, offline intake of actual GitHub Actions ZIP members, not a new emulator run or a claim of QA event admission. Machine-level receipt: [authentic producer consumption](../analysis/data/qa01-authentic-producer-consumption-20261019.json). **Factory preflight remains HOLD; accepted USA events 0/45, release gates 0/12.** This work owns cross-producer evidence intake only; original/native instruments remain with their active PR owners.

## 1. Actual Zoom Zoo 9-frame capture-on/off trial

Authentic [run 39211385737](https://github.com/gamesbyian/UR-Recomp/actions/runs/39211385737) uploaded artifact 12167633197 (`qa01-zoo-authentic-5034-5042-source-native-ab`), independently fetched and SHA-256 rehashed as `be72834ac617da8dfb96c591e06efaa18adbfe7d872cc64f6a306d3db8db0765`. Its unchanged-source producer control reports source `a238df6edfff6893e6986e4ebb43af949069b620`, retail ROM `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, 2014 movie `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442` and normalized movie-controller window `7b03f40e3401d844c16c7c4e1cc7375e5419f33882793c8187dcebc88dbc8c93`. The **supplied original/native input files differ by guest representation**; source-input invariance means each guest's on/off pair retained identical own input bytes, not that its original and native input files had equal SHA-256.

Both OFF and ON producer reports exist with **exit code 1**: the comparator honestly does not accept full source/native parity. The bounded A/B reviewer positively checked matched producer binaries/source controller, unchanged existing semantic checkpoints, and nine real continuous script-dump acknowledgments on **each** guest; it does not independently prove controller CPU polling or instruction-time observation phases. Original replay wall time OFF 4.837964s / ON 4.863855s (delta +0.025891s, +0.535%); native OFF 109.049805s / ON 109.079837s (+0.030032s, +0.028%). These are one-run incidental timing measurements, not a confidence interval or whole-race recorder performance claim.

Independently reopened/rehashed all **32 retained full source/native WRAM/SRAM files** for the eight divergent/boundary frames. The one entirely equal **+5039** frame remains digest-only in the retained archive, explicitly counted as one unreviewed raw interior frame by the independent raw verifier. Full image lengths, each raw SHA, raw differing byte counts and report's frame-pair SHA chain `759c24c1cc87072c8abb188fb210879e4ff600c4e0461907162e5dc13d457a5c` matched. The independent comparisons gave **13 WRAM difference occurrences, zero SRAM**:

| Zoo-relative frame | Actual unmasked WRAM differences (original → native) |
| --- | --- |
| +5034 | `7E:01EE F0→EE` |
| +5035 | `7E:01EE F0→EE` |
| +5036 | `7E:01EE F0→EE`; `7E:01F1 F4→FB` |
| +5037 | `7E:01EE F0→EE`; `7E:01F1 F4→FB` |
| +5038 | `7E:01EE F0→EE` |
| +5039 | none; equal images by recorded SHA only |
| +5040 | `7E:0063 73→77`; `7E:0069 BE→C1` |
| +5041 | `7E:0063 4D→51`; `7E:0069 97→9C` |
| +5042 | `7E:0063 27→2C`; `7E:0069 71→76` |

Five `01EE` differences and two `01F1` differences concern the known stack window; three each at `0063` and `0069` concern the later DP/sound-related window. **A matching or mismatching checkpoint alone does not identify its first actual instruction consumer**. In particular, do not claim +5039 proves complete instruction equivalence or that the sound-window values are already causally responsible for gameplay. No retained executed original/native causal bus payloads exist in this A/B artifact. The independent raw review itself explicitly reports `actual_guest_frame_acknowledgments_verified=false`; the separate A/B reviewer checked the bounded nine acknowledgments and must not be confused with guest-CPU instruction/joypad proof.

The archive may be independently re-read with:

```bash
unzip -q qa01-zoo-nineframe-ab.zip -d /tmp/qa01-real-ab
python3 tools/qa01_verify_frame_capture.py \
  --report /tmp/qa01-real-ab/qa01-zoo-ab/on/zoom-zoo/replay/qa01-frame-evidence/fingerprints.json \
  --retained-raw /tmp/qa01-real-ab/qa01-zoo-ab/on/zoom-zoo/replay/qa01-frame-evidence/retained \
  --output /tmp/qa01-real-ab/reverified.json
```

The XML-less JSON report path and ZIP names above refer to fetched artifact **12167633197**, not a repository-checked-in binary. Do not commit multi-megabyte dumps to Git.

## 2. RF062 actual negative producer result

Separate [run 39211687859](https://github.com/gamesbyian/UR-Recomp/actions/runs/39211687859) did **not** execute the original/native sound causal case. Its plan (artifact 12167369773, ZIP SHA `3e3de19c320e7b56ae37f3361b2261177ba9c58181ee984e63b35030908026db`) selected one Zoom Zoo case at `ccba6f2983b4bdf3c4160928b74255f4bdb0e74e`. The build job failed at `tools/qa01_rf062_direct_sound_bus_pc_patch.py` while matching the pinned v2 decoded-source `Read` IR site:

```text
ValueError: RF062 exact pinned v2 decoded source Read IR source drift
```

The genuine aggregate (artifact 12167669187; ZIP SHA `28656297dfa9b27d767f3cc3856c35a5f4c79808785d440fc9038d89145633d7`) correctly records **completed 0 / missing_evidence 1 / transport_complete false**, because no case-result JSON was produced. This is a specific **pre-execution research instrumentation incompatibility**, not a detected audio mismatch and not a reason to retry a large factory. RF062 owner should first source-qualify the actual checked-out emitter `Read` statement/active M1X0 variant in a short preflight, then rerun only a bounded case after validation.

## 3. Factory next-action decision

The new, merged `qa01_factory_preflight.py` v2 would correctly withhold positive readiness: there are real bounded full-memory records but **no independently reviewed cross-guest causal executed-event JSON** for that same checkpoint, nor verified CPU joypad reads, authentic instruction-time phase equivalence, uninterrupted full race, exact Windows product or cold persistence. No attestation booleans should be set to true merely because this archive is real or its A/B workflow ran green.

**Highest-value next experiment:** preserve one source-authentic cross-guest `read/write/checkpoint` bus window at an already captured relative frame and phase, starting with **+5040 at `7E:0063`/`7E:0069`** once the RF062 emitter site and RF063/064 source byte-ordinal instrumentation are actually qualified. Recheck raw bytes from this nine-frame artifact, then use the merged causal consumer and factory gate without moving any existing guest clock or controller input. The stack window +5034–5038 provides a separate original/NMI cause line. Avoid 100/1,000/10,000-case batches until one such authenticated and causally discriminating pair exists.

Related producer lanes: [continuous capture #1904](https://github.com/gamesbyian/UR-Recomp/pull/1904), [RF062 staged native read #1911](https://github.com/gamesbyian/UR-Recomp/pull/1911), [RF062 disposable run #1916](https://github.com/gamesbyian/UR-Recomp/pull/1916), [original returned stack bytes #1919](https://github.com/gamesbyian/UR-Recomp/pull/1919). This intake does not merge or supersede them.
