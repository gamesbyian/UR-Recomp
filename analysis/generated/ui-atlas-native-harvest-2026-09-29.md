# Native UI atlas evidence harvest — 2026-09-29

This note preserves the useful conclusions from an already-completed native atlas run before its Actions artifact expires. It is evidence provenance, not a replacement for the raw framebuffer/WRAM artifact.

## Source

- workflow: `Native build and boot smoke`
- Actions run: `36553582809`
- result: success
- head commit: `58d439addf91ba347daf02c05349baf3a7762cd6`
- artifact id: `11027910194`
- artifact name: `uniracers-native-frame`
- artifact digest: `sha256:477a7681aa18b27194eef774fd89d65ef6b3c6b3d0ae190dffc29acbc8d166e3`
- artifact-created: 2026-09-29T10:20:21Z

The artifact contained the generated `ui-atlas.json` / HTML / Markdown, comparison reports, fixture logs, and the raw dump families used below.

## Tier 1 promotions supported by the artifact

### Two-player entry

`ui-main-branches` reached `ui-two-player-entry` before the fixture's later reset crashed the native runner.

- `currentMenu = 0x3D`
- framebuffer SHA-256: `20fe883bb545b396d866b02ae756e638c842b0dc6f09db22172bbcff90987f0f`
- visible frame: `PICK A PLAYER` roster screen
- X returned to `MAIN_MENU = 0xD7`

This locally promotes `TWO_PLAYER_SELECT = 0x3D` and the entry/back edges. It does **not** prove P1→P2 ownership handoff, P2-only causality, or the next multiplayer state.

The same process then crashed on scripted console reset, so the artifact contains no valid `VS_SELECT` capture from that fixture. Do not promote VS from this run.

### Race results and return flow

`ui-race-result-route` completed normally.

`race-results`:
- `currentMenu = 0x99`
- framebuffer SHA-256: `a84330d749471996b23c2721acf8fcb841a01d4ffe705a1fcdb31f6bf241953f`
- visible frame: `DRAGSTER COMPLETE` race-result table matching the manual's result family

After one A press:
- `currentMenu = 0xF6`
- framebuffer SHA-256: `4eb2f323fdaf3a494639ad00757e1fe98c27335656435d538ff145855b73b826`
- visible frame: Crawler `PICK TRACK`

After the fixture's following X press:
- `currentMenu = 0x6D`
- framebuffer SHA-256: `e95b4f476167986de7aae891b10fca4326221d41f65ca8c25f79c047e3bdaaf2`
- visible frame: `PICK TOUR`

Therefore the tested ordinary 1P Race result flow is locally `RESULT_RACE -> TRACK_SELECT -> TOUR_SELECT`. The prior manifest label `POST_RESULT_DECISION` on the first post-result capture was incorrect and should not be retained as evidence.

### Pause

`ui-pause-route` completed normally.

Before pause:
- `currentMenu = 0x00`, `inRace = 0x01`
- framebuffer SHA-256: `3b04bba3b2b1a3882a1e2217ba0ca14acba8e125d161019a40b3bc41af52af7a`

After Start:
- `currentMenu = 0x00`, `inRace = 0x01`
- framebuffer SHA-256: `4a9acf4d6f071e3dd85be1766a9d7aa0f1cb120df2cbc47b6ae2e8346f112e6b`
- visible overlay: `RACE`, timer, `CONTINUE GAME`, `QUIT`

A second Start returned to gameplay. Pause is therefore a reproduced overlay/state that does not require a distinct `currentMenu` value on this route.

### Options and Records

Useful locally reproduced anchors:

| Capture | State | currentMenu | Framebuffer SHA-256 |
|---|---|---:|---|
| `ui-options-entry` | `OPTIONS_MENU` | `0x57` | `309f746535ed7d3b6c792b011ab8443822eec6212240cd7b5a3537f860a2a6a4` |
| `ui-records-entry` | `RECORDS` | `0x5D` | `f6bcc5c27ff35def8862949a0e2adb56b3e2c55912f5aacb6ca8e26d85aa8a03` |
| `ui-records-back-options` | `OPTIONS_MENU` | `0x57` | `ea83db84e51fe0d6148f258d8ea141df39796b1e7b04c6255ed4e078efbe9164` |
| `ui-record-track-entry` | `RECORD_TRACK` | `0xCC` | `afda490a41dcccdbe8610d5af1a3315d188eec8d39722ca1f380da206fa291fe` |

The Track Records probe's X discriminator did **not** return to Records. Its next raw capture remained visibly in Track Records while `currentMenu` changed to `0x5A`. Keep that behavior unclassified rather than inventing a return edge.

## Useful negative / non-promotion evidence

- `ui-main-branches`: native scripted reset crashed after the successful 2P branch, so VS and League branches from that fixture were not captured.
- `ui-league-table`: the captures visibly show `PICK PLAYER ONE` then `PICK PLAYER TWO`, both with `currentMenu = 0x3E`; the fixture labels are wrong for this SRAM/context and must not be promoted as League evidence.
- `ui-stunt-result-route`: entered Stunt gameplay but timed out before a result capture.
- `ui-circuit-result-route`: remained in active Circuit gameplay and timed out waiting for the result menu.
- `ui-ending-shortcut`: captured the recovered `0x84` startup state, then timed out waiting for `0x5B`; the ending shortcut is not locally verified by this run.
- `ui-attract-route`: departed Main Menu to `0x84`, and its framebuffer hash exactly matches the sampled `ui-splash-observed` black frame. This does not reproduce the recovered bot's `DEMO = 0x00` claim.
- reset-separated reconnaissance fixtures repeatedly hit a native reset crash. Prefer one-route-per-process probes or fix reset semantics before treating later branches as absent game behavior.

## Promotion rule

Promote only facts above that combine a successful controller route, stable runtime signature, and a framebuffer consistent with the intended state. Preserve failures and mislabeled captures as diagnostics; never turn a fixture's intended label into evidence when the frame contradicts it.
