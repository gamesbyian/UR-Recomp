# RF074: native NMI scheduler resume origin is not an executed opcode

**October 19, 2026. Research-only source patch and ROM-free tests, no genuine RF074 guest replay.** Source-original RF071/RF072 prove actual post-NMI stack byte consumption in the original emulator. The separately archived RF073 native experiment confirms all nine real status helper reads inside compiled RTI brackets but lacks equivalent intra-frame instruction provenance. USA acceptance **0/45**, Windows QA **0/12**.

## Reuse actual pinned upstream scheduler history

Pinned Baldosa snesrecomp revision 075fbe4c8e0d97b0013be541795c39cb644a9709 already maintains a permanent **1024-entry LLE resume-origin ring** in runner/src/snes/interp_bridge.c: interp_bridge_resume_total, interp_bridge_resume_get, and original assignment-site/kind names. Every write to the guest scheduler resume PC records old/new PC, original host frame, SP, kind, site and bridge/scheduler depths, without opt-in research logging.

Pinned beam_frame_driver.c takes s_resume_pc from interp_bridge_lle_resume_pc() via update_resume_pc() on return from its quiescent run, then on the subsequent NMI pushes s_resume_pc through cpu_push_interrupt_frame_at. Thus native RF047 resume=82D4EE is **a real scheduler-published PC and interrupt-stack source**, not independently evidence of the last opcode actually fetched. Original Snes9x recorded PC 82:D4F0 in four host frames and 82:D4EE in five; those host-frame labels cannot certify equal native/original interrupted instruction phase.

## The bounded opt-in source observer

tools/qa01_rf074_nmi_resume_origin_source.py stages after RF044/RF047 and before native recompilation in the disposable beam frame driver only. With both UR_QA01_RF047_NATIVE_NMI_RETURN=1 and UR_QA01_RF074_NMI_RESUME_ORIGIN=1, it appends a single atomic RF047-shared-sequence stage=resume_origin event **between real native NMI entry and cpu_push_interrupt_frame_at**, for frames1017..1025. It reads no guest ROM, WRAM or bus.

Rather than choose any convenient matching history, the observer retrieves the **latest genuine ring SET or RESTORE assignment** within 1024 entries and records sourceFound, originMatches, ringTotal/ringSeq, old/new PC, source frame/SP/site/kind and nesting, **WAI flag before the native NMI wake and separately after the driver clears it**, NMI vector, native master and beam V/H. An absent or disagreeing origin is HOLD; it must not be silently repaired from an older matching ring event.

tools/qa01_rf074_nmi_resume_origin_report.py validates nine entry→resume_origin→after_push→compiled_rti→handler_return brackets from a contiguous native-local RF047 ordinal stream. It demands immediately adjacent original push stage, the same PC/vector/clock at native entry and before push, a qualified latest ring assignment with exact scheduler-PC match, known assignment site/kind and real ring position. It never treats ring-origin site as a fetched guest opcode PC, nor native host-frame labels as original/native semantic-phase equality. Adversarial ROM-free tests reject a fabricated match, unknown site, wrong ring count, misplaced event, changed SP/PC/vector, missing native event or truncated recorder.

## Next real go/no-go

Stage existing RF044, RF047 then RF074 on disposable **commit-verified** pinned Baldosa, compile the actual driver and run ONE unchanged-source authentic original/native Zoom Zoo NMI window with unchanged ROM/movie/input and raw original/native five stack bytes. Recover live actual executed decoded native opcode PCs via existing RF061 independent AOT/interpreter hook and source-original PC under the corresponding real interruption point. The RF074 ring assignment alone never grants that fetch identity. Independently check first read/overwrite at aligned semantic stage and only then apply the strict qa01_causal_window.py schema; never fill missing bytes or rebase unrelated clocks. Preserve the original/native memory sample discrepancies and source/NMI raw logs. Source-authentic RFC074 has not yet executed in a game or proved a first consumed **differing** byte.

There is no gameplay patch, timer change, byte mask, input change or USA event admission. **0/45 USA, 0/12 Windows QA.**
