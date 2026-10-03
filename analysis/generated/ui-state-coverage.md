# UI State Coverage

| State | Tier | Menu byte(s) | Required captures | Optional captures | Public visual leads | Blockers | In | Out | Strongest edge evidence |
|---|---:|---|---:|---:|---:|---|---:|---:|---|
| BOOT_STARTUP | 2 |  | 0 | 10 | 0 |  | 0 | 1 | hypothesis |
| SPLASH | 2 | 0x84 | 0 | 1 | 0 |  | 1 | 2 | documented |
| DEMO | 3 | 0x00? | 0 | 1 | 0 |  | 1 | 1 | verified |
| MAIN_MENU | 1 | 0xD7 | 1 | 13 | 2 |  | 7 | 7 | verified |
| PLAYER_SELECT_P1 | 1 | 0x3C | 1 | 0 | 3 |  | 1 | 1 | verified |
| TWO_PLAYER_SELECT | 1 | 0x3D | 0 | 1 | 1 |  | 1 | 2 | verified |
| VS_SELECT | 1 | 0x3E | 0 | 3 | 1 |  | 2 | 2 | verified |
| VS_CHALLENGER | 1 | 0x3F | 0 | 1 | 0 |  | 1 | 1 | verified |
| VS_CHALLENGE_TRACK | 1 | 0x5A | 0 | 1 | 0 |  | 1 | 1 | verified |
| TOUR_SELECT | 1 | 0x6D, 0x10 | 1 | 1 | 2 |  | 4 | 1 | verified |
| TRACK_SELECT | 1 | 0xF6, 0x91, 0x96? | 1 | 3 | 2 |  | 5 | 2 | verified |
| PRE_RACE_CARD | 1 | 0x16 | 1 | 4 | 0 |  | 5 | 1 | verified |
| GAMEPLAY | 1 |  | 7 | 4 | 2 |  | 2 | 4 | verified |
| PAUSE | 1 |  | 0 | 1 | 0 |  | 1 | 1 | verified |
| RESULT_BY_TRACK_TYPE | 1 |  | 0 | 0 | 0 |  | 0 | 0 |  |
| RESULT_RACE | 1 | 0x99, 0xF9 | 0 | 1 | 2 |  | 1 | 3 | verified |
| RESULT_CIRCUIT | 1 | 0xBC | 0 | 1 | 1 |  | 1 | 2 | verified |
| RESULT_STUNT | 1 | 0x18, 0x2F, 0xAD?, 0xAF?, 0xB3?, 0xD3?, 0xD8?, 0xED?, 0xF3? | 0 | 1 | 1 |  | 1 | 2 | verified |
| POST_RESULT_DECISION | 1 | 0xD3, 0xB7 | 0 | 2 | 0 |  | 2 | 2 | documented |
| LEAGUE_SELECT | 2 |  | 0 | 3 | 1 |  | 1 | 1 | documented |
| LEAGUE_TABLE | 2 |  | 0 | 1 | 0 |  | 1 | 1 | documented |
| OPTIONS_MENU | 1 | 0x57 | 0 | 11 | 1 |  | 7 | 5 | verified |
| RECORDS | 1 | 0x5D | 0 | 18 | 2 |  | 3 | 6 | verified |
| RECORD_TRACK | 1 | 0xCC | 0 | 1 | 1 |  | 1 | 1 | verified |
| RECORD_HIGH_SCORES | 1 |  | 0 | 1 | 1 |  | 1 | 1 | verified |
| RECORD_PLAYER_SCORES | 1 |  | 0 | 1 | 1 |  | 2 | 2 | documented |
| RECORD_GROUP_TABLES | 1 |  | 0 | 1 | 1 |  | 2 | 1 | documented |
| DEFINE_PLAYER | 2 |  | 0 | 1 | 1 |  | 1 | 1 | documented |
| RENAME_PLAYER | 2 |  | 0 | 2 | 1 |  | 2 | 2 | documented |
| PLAYER_NAME_EDITOR | 2 |  | 0 | 10 | 1 |  | 2 | 3 | documented |
| FORBIDDEN_NAME_REJECTION | 3 |  | 0 | 0 | 2 | name_entry_cursor_mapping | 2 | 2 | documented |
| DEFINE_LEAGUE | 2 |  | 0 | 1 | 1 |  | 1 | 1 | documented |
| NAME_LEAGUE | 2 |  | 0 | 1 | 1 |  | 2 | 2 | documented |
| ENDING | 1 | 0x5B? | 0 | 1 | 1 |  | 1 | 1 | hypothesis |
| ERASE_ALL_CONFIRM | 2 |  | 0 | 1 | 0 |  | 1 | 1 | documented |

## Tier 1 gaps

- ENDING: menu id remains historical/unverified

## All evidence gaps

- DEMO: menu id remains historical/unverified
- FORBIDDEN_NAME_REJECTION: no capture contract
- FORBIDDEN_NAME_REJECTION: blocked by open capability name_entry_cursor_mapping
- ENDING: menu id remains historical/unverified

## Summary

- conceptual states: 35
- executable transitions: 67
- capture contracts: 115
- menu-index entries: 32
- locally verified menu-index entries: 22
- states with at least one capture contract: 33
- states with at least one public visual lead: 24
- Tier 1 states: 23
- Tier 1 gap observations: 1
- incomplete capability dependencies: 2
- raw gap observations: 4
