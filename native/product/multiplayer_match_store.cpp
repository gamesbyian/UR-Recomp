#include "multiplayer_match_store.hpp"

#include <filesystem>

namespace ur::product {
namespace {

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

}  // namespace

bool append_multiplayer_match_artifacts(
    const std::string& directory,
    const CompletedRunRecord& run,
    const BoundOrdinaryTwoPlayerMatchContext& context,
    StoredMultiplayerMatchArtifacts* stored,
    std::string* detail) {
    const auto match = make_multiplayer_match_record(run, context);
    if (!match) {
        set_detail(detail, "invalid multiplayer run/match binding");
        return false;
    }

    // Validate both canonical encodings before the first persistent write.
    if (encode_completed_run_record(run).empty() ||
        encode_multiplayer_match_record(*match).empty()) {
        set_detail(detail, "multiplayer artifact validation failed");
        return false;
    }

    std::string run_path;
    if (!append_completed_run_record(
            directory, run, &run_path, detail)) {
        return false;
    }

    const std::string match_path =
        multiplayer_match_record_path_for_run(run_path);
    std::string match_detail;
    if (!save_multiplayer_match_record_for_run(
            run_path, run, *match, &match_detail)) {
        std::error_code sidecar_ec;
        std::filesystem::remove(match_path, sidecar_ec);

        std::error_code run_ec;
        const bool removed =
            std::filesystem::remove(run_path, run_ec);
        if (run_ec || !removed) {
            set_detail(
                detail,
                match_detail +
                    "; rollback failed for unpaired run artifact");
        } else {
            set_detail(detail, match_detail);
        }
        return false;
    }

    if (stored) {
        stored->run_path = run_path;
        stored->match_path = match_path;
    }
    return true;
}

}  // namespace ur::product
