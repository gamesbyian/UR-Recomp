# QA01: Genuine RF062 source replay script, exactly three added dumps

**Read-only independent source-input qualification, October 19, 2026.** This does not alter the emulator, trusted cold-record source whitelist, controllers, ROM/movie, or event ledger.

The successfully executed [RF062 experiment 39307379568](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307379568) archived case ZIP **12214972031**, SHA256 `239d606436f47631e146fe8b7e66b2284f366f9321099711b0c0244af01cb927`. The later [raw-frame research run 39308189433](https://github.com/gamesbyian/UR-Recomp/actions/runs/39308189433) uploaded case ZIP **12216270293**, SHA256 `85b8585539001210e4a9d2b22e5484034679fbda5d40808300d221e1ec583aed`. Both actual original/native artifacts are ZIP-CRC verified, and the independently compared source-original/native case producer reports agree on ROM, original SMV, original controller movie window, seed SRAM, native executable, both guest frame origins, game results, sampled full WRAM mesh and next Bowl handoff. The **original Snes9x reference executable differs** across these runs, so matching reported guest states is not a same-binary capture-on/off proof.

The complete source replay command script changes from SHA256 `1eb3e8416b7fa40935d097c78d281ca98537c9a555e23f1906a99912dcdb2c52` (2,815 bytes) to `92012c94af3a27c54144e34c9d1d7a6cdb97ddf3e519d3f24c375c7c76bf6bc2` (2,905 bytes). Exactly one contiguous source-script block changes:

```diff
 dump scene-05100
-wait 20
+wait 5
+dump qa01-frame-005105
+wait 1
+dump qa01-frame-005106
+wait 1
+dump qa01-frame-005107
+wait 13
 dump scene-05120
```

There are **no other changed script lines**. All actual original and native *supplied controller files* are byte-identical across the two real ZIPs: `ref.input` is 4,264 bytes, SHA256 `a5b909fe87aa394024cdba8f5eaf67a0ac6652000df145252bf558d755ed79b8`; `pinned-baldosa.input` is 4,470 bytes, SHA256 `bc3d364ff3b2ac1a120be3b3efa33b4938749c648e1b64df28d29742b4c64160`. The full script command timeline of `until`, `press`, standard `dump` and `quit` commands is unchanged, and all `wait` durations still sum to **5,742**.

**Executable QA:** `tools/qa01_independent_rf062_dump_script_provenance.py` independently reopens both **pinned source ZIP hashes**, the two real scripts and supplied guest inputs, insists on *the exact three* inserted `dump` directives and 5+1+1+13 wait split, independently crosschecks the producer semantic controls, and emits a machine-readable **SOURCE_SCRIPT_DELTA_ONLY_COLD_PROOF_HOLD** classification. It never silently canonicalizes arbitrary changed controller, wait or other dump commands. ROM-free adversarial tests cover substitutions, changed buttons, changed waits, extra dumps and truncated/non-ASCII scripts.

```bash
python3 tools/qa01_independent_rf062_dump_script_provenance.py \
  --baseline /path/to/rf062-first-case.zip \
  --candidate /path/to/rf062-added-dumps-case.zip \
  --output /tmp/qa01-rf062-source-script-identity.json
```

**Separate strict negatives remain:** `qa01_cold_result_record.py` correctly fails the *new* script hash with `ColdProofError: unknown original Zoo controller replay script SHA256` until the cold-proof owner explicitly admits that exact source/binary class and independently reruns its true fresh-guest record test; this evidence never bypasses that guard. This run also has 655 versus historical 656 native sound helper reads and 46/78 versus historical 51/78 full-WRAM exact original/native samples. No inference of observed dump noninterference at the CPU-instruction level, original/native clock alignment or Windows disk durability. **USA event credit 0/45, release QA gates 0/12.**
