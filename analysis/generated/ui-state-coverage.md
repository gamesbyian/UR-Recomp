# UI State Coverage

| State | Menu byte(s) | Required captures | Optional captures | Public visual leads | Blockers | In | Out | Strongest edge evidence |
|---|---|---:|---:|---:|---|---:|---:|---|
| BOOT_STARTUP |  | 0 | 10 | 0 |  | 0 | 1 | hypothesis |
| SPLASH | 0x84? | 0 | 1 | 0 |  | 1 | 2 | documented |
| DEMO | 0x00? | 0 | 1 | 0 |  | 1 | 1 | hypothesis |
| MAIN_MENU | 0xD7 | 1 | 13 | 2 |  | 6 | 7 | verified |
| PLAYER_SELECT_P1 | 0x3C | 1 | 0 | 3 |  | 1 | 1 | verified |
| TWO_PLAYER_SELECT | 0x3D? | 0 | 1 | 1 |  | 1 | 1 | documented |
| VS_SELECT | 0x3E? | 0 | 1 | 1 |  | 1 | 1 | documented |
| VS_CHALLENGER | 0x3F? | 0 | 0 | 0 | multiplayer_controller_2 | 1 | 1 | historical |
| VS_CHALLENGE_TRACK | 0x5A? | 0 | 0 | 0 | multiplayer_controller_2 | 1 | 1 | historical |
| TOUR_SELECT | 0x6D, 0x10? | 1 | 0 | 2 |  | 2 | 1 | verified |
| TRACK_SELECT | 0xF6, 0x91?, 0x96? | 1 | 2 | 2 |  | 2 | 1 | verified |
| PRE_RACE_CARD | 0x16 | 1 | 4 | 0 |  | 4 | 1 | verified |
| GAMEPLAY |  | 1 | 4 | 2 |  | 2 | 4 | verified |
| PAUSE |  | 0 | 1 | 0 |  | 1 | 1 | documented |
| RESULT_BY_TRACK_TYPE |  | 0 | 0 | 0 |  | 0 | 0 |  |
| RESULT_RACE | 0x99? | 0 | 1 | 2 |  | 1 | 1 | documented |
| RESULT_CIRCUIT | 0xBC? | 0 | 1 | 1 |  | 1 | 1 | documented |
| RESULT_STUNT | 0x18?, 0x2F?, 0xAD?, 0xAF?, 0xB3?, 0xD3?, 0xD8?, 0xED?, 0xF3? | 0 | 1 | 1 |  | 1 | 1 | documented |
| POST_RESULT_DECISION |  | 0 | 3 | 0 |  | 3 | 2 | documented |
| LEAGUE_SELECT |  | 0 | 3 | 1 |  | 1 | 1 | documented |
| LEAGUE_TABLE |  | 0 | 1 | 0 |  | 1 | 1 | documented |
| OPTIONS_MENU |  | 0 | 11 | 1 |  | 7 | 5 | documented |
| RECORDS |  | 0 | 17 | 2 |  | 1 | 6 | documented |
| RECORD_TRACK |  | 0 | 1 | 1 |  | 1 | 0 | documented |
| RECORD_HIGH_SCORES |  | 0 | 1 | 1 |  | 1 | 0 | documented |
| RECORD_PLAYER_SCORES |  | 0 | 1 | 1 |  | 2 | 2 | documented |
| RECORD_GROUP_TABLES |  | 0 | 1 | 1 |  | 2 | 1 | documented |
| DEFINE_PLAYER |  | 0 | 1 | 1 |  | 1 | 1 | documented |
| RENAME_PLAYER |  | 0 | 2 | 1 |  | 2 | 2 | documented |
| PLAYER_NAME_EDITOR |  | 0 | 10 | 1 |  | 2 | 3 | documented |
| FORBIDDEN_NAME_REJECTION |  | 0 | 0 | 2 | name_entry_cursor_mapping | 2 | 2 | documented |
| DEFINE_LEAGUE |  | 0 | 1 | 1 |  | 1 | 1 | documented |
| NAME_LEAGUE |  | 0 | 1 | 1 |  | 2 | 2 | documented |
| ENDING | 0x5B? | 0 | 1 | 1 |  | 1 | 1 | hypothesis |
| ERASE_ALL_CONFIRM |  | 0 | 1 | 0 |  | 1 | 1 | documented |

## Evidence gaps

- SPLASH: menu id remains historical/unverified
- DEMO: menu id remains historical/unverified
- TWO_PLAYER_SELECT: menu id remains historical/unverified
- VS_SELECT: menu id remains historical/unverified
- VS_CHALLENGER: no capture contract
- VS_CHALLENGER: no local capture or public visual lead
- VS_CHALLENGER: menu id remains historical/unverified
- VS_CHALLENGER: blocked by open capability multiplayer_controller_2
- VS_CHALLENGE_TRACK: no capture contract
- VS_CHALLENGE_TRACK: no local capture or public visual lead
- VS_CHALLENGE_TRACK: menu id remains historical/unverified
- VS_CHALLENGE_TRACK: blocked by open capability multiplayer_controller_2
- RESULT_RACE: menu id remains historical/unverified
- RESULT_CIRCUIT: menu id remains historical/unverified
- RESULT_STUNT: menu id remains historical/unverified
- RECORD_TRACK: no outgoing transition in executable contract
- RECORD_HIGH_SCORES: no outgoing transition in executable contract
- FORBIDDEN_NAME_REJECTION: no capture contract
- FORBIDDEN_NAME_REJECTION: blocked by open capability name_entry_cursor_mapping
- ENDING: menu id remains historical/unverified

## Summary

- conceptual states: 35
- executable transitions: 58
- capture contracts: 103
- menu-index entries: 26
- locally verified menu-index entries: 5
- states with at least one capture contract: 31
- states with at least one public visual lead: 24
- framebuffer comparison pairs: 32
- open capability dependencies: 2
- raw gap observations: 20
