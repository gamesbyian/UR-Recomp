# Local Tournament: exact saved-result link store

Status: product filesystem adapter with strict native disk tests. The Windows game does not yet invoke this API, so this is not a playable Local Tournament.

## Durable membership authority

The existing session and launch/receipt contracts establish independent tournament identity and attempt-scoped pre-race provenance. This adapter is the missing durable association between a successfully saved ordinary 2P match and one completed tournament fixture.

At the actual 2P capture completion boundary, the live host must retain the explicit attempt token it minted BEFORE guest route entry, and call the commit adapter only AFTER the ordinary match pair has been successfully published. The adapter reopens the exact specified .urrun from the existing multiplayer-runs directory and re-admits its checksum/course-bound .urmatch sidecar. It runs the existing attempt-scoped reducer and fixture receipt constructor on private copies of the current standings/launch model. A fixture-indexed UR-LOCAL-TOURNAMENT-RESULT-LINK/1 file contains ONLY the canonical existing fixture receipt and the exact safe basename of that saved run. It is published through same-directory temporary + complete write/flush/close + atomic replace. The in-memory fixture is marked complete and the pending launch is retired only after the link is successfully written.

A saved ordinary match remains ordinary Records history even when the tournament link cannot be published. In that case no tournament points are awarded. This code does not claim a multi-file crash transaction across the independently published ordinary Records pair, fixture link, and launch checkpoint. The caller must serialize writes per fixture, provide paths under the existing host data root and retire the launch checkpoint through its established exact-attempt store API.

Fresh-load restoration iterates the canonical fixture indices and reads only the exact expected fixture-link filenames. It resolves each explicit saved run basename within the supplied multiplayer run directory, admits the exact checksum/course-bound run+match pair, and delegates the entire batch to the existing all-or-nothing receipt restorer. It NEVER treats similar profile names, course, timestamps or arbitrary Records scans as tournament membership. Absent fixture links remain unplayed. Broken links, missing underlying pair, wrong instance/fixture, duplicate pair checksum, or mismatching result reject the whole standings reconstruction without partial awards.

The focused native test uses actual persisted .urrun/.urmatch files, explicit launch attempt tokens and real fixture-link files; verifies two credited fixtures, absent-link no-history inference, token/course/path rejection, corrupted-link all-or-nothing recovery, and missing sidecar rejection. It does NOT validate an actual Windows race, UI launch or completed tournament presentation.

## Next integration steps

Wire explicit tournament creation/selection to the persisted session definition, route the chosen fixture through the established Modern 2P join/stock course surface, keep the minted attempt in the existing live multiplayer capture owner, call this adapter after exact pair publication, then expose restored fixtures/standings and completion in Uniracers-native menu visual grammar. Keep frontend/controls ownership separate.
