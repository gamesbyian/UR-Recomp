#include "host_product_state.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

int main() {
    static_assert(!policy_for(ExecutionMode::Authentic).host_profiles);
    static_assert(!policy_for(ExecutionMode::Authentic).host_settings);
    static_assert(!policy_for(ExecutionMode::Authentic).modern_commands);
    static_assert(policy_for(ExecutionMode::Modern).host_profiles);
    static_assert(policy_for(ExecutionMode::Modern).host_settings);
    static_assert(policy_for(ExecutionMode::Modern).modern_commands);
    static_assert(HostProductState::schema_version == 2);

    HostProductState defaults;
    const std::string expected_defaults =
        "UR-HOST-STATE/2\n"
        "profile=\n"
        "pause_on_focus_loss=1\n"
        "vibration_enabled=1\n"
        "display_mode=windowed\n";
    assert(encode_host_product_state(defaults) == expected_defaults);

    HostProductState customized;
    customized.active_profile_id = "ian.local-1";
    customized.settings.pause_on_focus_loss = false;
    customized.settings.vibration_enabled = false;
    customized.settings.display_mode = HostDisplayMode::BorderlessFullscreen;
    const std::string encoded = encode_host_product_state(customized);
    assert(encoded ==
        "UR-HOST-STATE/2\n"
        "profile=ian.local-1\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=borderless\n");

    const auto decoded = decode_host_product_state(encoded);
    assert(decoded);
    assert(*decoded.state == customized);
    assert(encode_host_product_state(*decoded.state) == encoded);

    // Schema v1 remains readable so existing Focus Pause/vibration settings
    // migrate naturally when the state is next saved as v2.
    const auto legacy = decode_host_product_state(
        "UR-HOST-STATE/1\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n");
    assert(legacy);
    assert(legacy.state->active_profile_id == "legacy.profile");
    assert(!legacy.state->settings.pause_on_focus_loss);
    assert(!legacy.state->settings.vibration_enabled);
    assert(legacy.state->settings.display_mode == HostDisplayMode::Windowed);
    assert(encode_host_product_state(*legacy.state).find("UR-HOST-STATE/2\n") == 0);

    assert(is_valid_profile_id("profile_01"));
    assert(!is_valid_profile_id(""));
    assert(!is_valid_profile_id("contains spaces"));
    assert(!is_valid_profile_id(std::string(65, 'x')));

    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/2\nprofile=bad/id\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/2\nprofile=x\npause_on_focus_loss=yes\nvibration_enabled=1\ndisplay_mode=windowed\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/2\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=exclusive\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/2\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nextra=1\n"));

    return 0;
}
