#pragma once

// Pure native-to-shipping-.urrun admission. This never publishes files or
// grants medals, ghosts, Replay or tournament outcomes. A caller must supply
// a guest-authored BaldosaSettledResult plus separate verified Modern profile
// participant authority; a menu appearance by itself is never sufficient.
#include "baldosa_guest_result_observer.hpp"
#include "completed_run_record.hpp"

#include <optional>

namespace ur::product {

// Distinct from the old patched SNESRecomp replay target. These are exact
// pinned Baldosa AOT/runner sources; deliberately no cross-core replay/PB
// compatibility until independent input-latch acceptance.
constexpr const char* kBaldosaNativeRunCompatId =
    "baldosa-10b864b9d14a7b7416dd909eb7b054c88faef101"
    "-snes-075fbe4c8e0d97b0013be541795c39cb644a9709-v1";

struct BaldosaRunRecordAuthority {
    // Checked by the established named Modern catalog/profile selector.
    // Does NOT become true merely because a default anonymous save exists.
    bool selected_named_profile_verified = false;
    // For 2P, both player identities additionally require authenticated
    // Modern local participants and the established match context binder.
    bool multiplayer_participants_bound = false;
};

// Build a canonical, in-memory CompletedRunRecord only after the supplied
// settled native guest result and separate identity authorization agree.
// The existing shipping record validator/codecs remain final authority.
// This function does not make a guest result, storage path, or win.
std::optional<CompletedRunRecord> assemble_baldosa_native_run_record(
    const BaldosaSettledResult& result,
    const BaldosaRunRecordAuthority& authority);

} // namespace ur::product
