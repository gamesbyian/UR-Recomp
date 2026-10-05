#include "host_product_store.hpp"
#include "regional_presentation_runtime.hpp"

#include <cassert>
#include <cstdio>
#include <string>

using namespace ur::product;

namespace {

constexpr RegionalSecretContext kModernTitle{true, true, false};

RegionalPresentationUpdate type(
    RegionalPresentationRuntime& runtime,
    HostProductState& state,
    const char* text,
    std::uint64_t start_ms) {
    RegionalPresentationUpdate update = RegionalPresentationUpdate::NoChange;
    for (std::size_t i = 0; text[i] != '\0'; ++i) {
        update = runtime.feed_text(
            state,
            text[i],
            start_ms + static_cast<std::uint64_t>(i) * 100,
            kModernTitle);
    }
    return update;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string path = argv[1];
    std::remove(path.c_str());

    HostProductState first;
    first.active_profile_id = "alpha";
    assert(save_host_product_state_file(path, first) ==
           HostProductSaveStatus::Saved);

    auto loaded = load_host_product_state_file(path);
    assert(loaded.loaded());
    assert(loaded.state->regional_presentation ==
           RegionalPresentation::NorthAmerica);

    RegionalPresentationRuntime runtime(*loaded.state);
    assert(type(runtime, *loaded.state, "PAL", 1000) ==
           RegionalPresentationUpdate::SaveRequired);
    assert(loaded.state->regional_presentation == RegionalPresentation::Europe);
    assert(save_host_product_state_file(path, *loaded.state) ==
           HostProductSaveStatus::Saved);

    // Fresh store load is the persistence boundary: no matcher/session survives.
    auto fresh = load_host_product_state_file(path);
    assert(fresh.loaded());
    assert(fresh.state->regional_presentation == RegionalPresentation::Europe);
    assert(fresh.state->active_profile_id &&
           *fresh.state->active_profile_id == "alpha");

    // Profile identity is orthogonal to regional presentation.
    fresh.state->active_profile_id = "beta";
    assert(save_host_product_state_file(path, *fresh.state) ==
           HostProductSaveStatus::Saved);
    auto after_profile_change = load_host_product_state_file(path);
    assert(after_profile_change.loaded());
    assert(after_profile_change.state->regional_presentation ==
           RegionalPresentation::Europe);
    assert(after_profile_change.state->active_profile_id &&
           *after_profile_change.state->active_profile_id == "beta");

    RegionalPresentationRuntime reverse(*after_profile_change.state);
    assert(type(reverse, *after_profile_change.state, "NTSC", 2000) ==
           RegionalPresentationUpdate::SaveRequired);
    assert(save_host_product_state_file(path, *after_profile_change.state) ==
           HostProductSaveStatus::Saved);

    auto restored_ntsc = load_host_product_state_file(path);
    assert(restored_ntsc.loaded());
    assert(restored_ntsc.state->regional_presentation ==
           RegionalPresentation::NorthAmerica);
    assert(restored_ntsc.state->active_profile_id &&
           *restored_ntsc.state->active_profile_id == "beta");

    std::remove(path.c_str());
    return 0;
}
