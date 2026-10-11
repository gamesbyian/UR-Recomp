# Technical-motion-graphics handoff (2026-10-10)

This lane is separate from the recruitment editor and the HD art editor. The master trailer, game guest, renderer, and source-of-truth research were not modified.

## Independently backed candidate shots

1. **Source-centre parity** (6s; 1920×1080, 30fps): an **editorial animated grid**, explaining the exact comparison between the 256×224 fixed native Original and the [43,299) centre of the separately executed 342×224 Original at 2P guest frame 1856. **0/57,344 RGBA centre pixels differ**, with matching complete 2,473-frame guest CRC sequences. Evidence: [accepted QA report](../../../../docs/QA08-NATIVE-STOCK-CENTER-PARITY-20261010.md); Actions run 38083079741; artifact 11681138053. This proves a bounded same-frame Original centre match, not all-game fidelity or 342-wide HD.
2. **Recorder non-interference** (6s; 1920×1080, 30fps): animated editorial bars representing two independently executed matching guest WRAM CRC streams, recording disabled and enabled. Validated continuous capture includes 600 consecutive guest frame IDs 2100–2699. Evidence: [continuous capture package](../recruitment/continuous/README.md), source commit `4748ae337f38d801039260ca6ed849fd2ca1d7a3`, native CI run 38089655141, artifact 11683697184. This proves recording did not perturb this bounded guest trace, not original-emulator equivalence or perfect physical 60-Hz pacing.

**Important:** Grid artwork and bar lengths are editorial motion graphics, not real PPU rasters, recovered SNES layers or measured CRC values. All captions must preserve these scopes. Do not replace imagery with simulated game frames.

## Status and use

The two standalone local MP4s and their decoded keyframes were produced and inspected, but **their binary media are not yet committed in this branch**. Do not advertise a repo-based delivery path for them until uploaded and independently decoded from GitHub. The local handoff contains `01-source-centre-parity.mp4`, `02-recording-noninterference.mp4`, `render.py`, representative PNGs, and `provenance.json`.

Expected SHA-256 from the independently rendered local handoff:
- `01-source-centre-parity.mp4`: `8f78907b1b444af84d40e887a0abd5e2e8df848faa7dbd29a1c6b197f8d26314`
- `02-recording-noninterference.mp4`: `744128dc4ee8e2efd54bf7f22d04a19abcf3363fc8d515a2b81c5fe8903b765f`

## Next shots

The **65816 → identified function → generated native C** shot requires a *single* verified cross-linked function/source pair. The source-faithful X-ray requires actual extracted background/OBJ/HUD layers with independently checked priorities. Neither has been manufactured from unrelated code excerpts or speculative layer masks.

Agent 1 can place the first clip before a real continuous native gameplay cut and the second after the gameplay to strengthen the evidence story. The existing 600-frame 1080p continuous source clip is Original mode, based on genuine 960×540 SDL output, and must not be labelled a 4K or Remastered clip.
