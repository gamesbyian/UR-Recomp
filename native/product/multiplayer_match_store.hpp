#pragma once

#include "completed_run_store.hpp"
#include "multiplayer_match_record.hpp"

#include <string>

namespace ur::product {

struct StoredMultiplayerMatchArtifacts {
    std::string run_path;
    std::string match_path;
};

/*
 * Persist one already-authoritative ordinary-2P run and its required metadata
 * sidecar as a product pair.
 *
 * All semantic binding is validated before the run is appended. If the
 * sidecar write then fails synchronously, the just-created run artifact is
 * removed so ordinary Records cannot discover an unpaired multiplayer run.
 * Replay authority remains entirely in the .urrun artifact.
 */
bool append_multiplayer_match_artifacts(
    const std::string& directory,
    const CompletedRunRecord& run,
    const BoundOrdinaryTwoPlayerMatchContext& context,
    StoredMultiplayerMatchArtifacts* stored = nullptr,
    std::string* detail = nullptr);

}  // namespace ur::product
