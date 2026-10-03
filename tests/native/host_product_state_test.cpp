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
    static_assert(HostProductState::schema_version == 3);

    HostProductState defaults;
    const std::string expected_defaults =
        "UR-HOST-STATE/3\n"
        "profile=\n"
        "pause_on_focus_loss=1\n"
        "vibration_enabled=1\n"
        "display_mode=windowed\n"
        "vsync=on\n";
    assert(encode_host_product_state(defaults) == expected_defaults);

    HostProductState customized;
    customized.active_profile_id = "ian.local-1";
    customized.settings.pause_on_focus_loss = false;
    customized.settings.vibration_enabled = false;
    customized.settings.display_mode = HostDisplayMode::BorderlessFullscreen;
    customized.settings.vsync_mode = HostVSyncMode::Adaptive;
    const std::string encoded = encode_host_product_state(customized);
    assert(encoded ==
        "UR-HOST-STATE/3\n"
        "profile=ian.local-1\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=borderless\n"
        "vsync=adaptive\n");

    const auto decoded = decode_host_product_state(encoded);
    assert(decoded);
    assert(*decoded.state == customized);
    assert(encode_host_product_state(*decoded.state) == encoded);

    const auto legacy_v1 = decode_host_product_state(
        "UR-HOST-STATE/1\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n");
    assert(legacy_v1);
    assert(legacy_v1.state->settings.display_mode == HostDisplayMode::Windowed);
    assert(legacy_v1.state->settings.vsync_mode == HostVSyncMode::On);

    const auto legacy_v2 = decode_host_product_state(
        "UR-HOST-STATE/2\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=borderless\n");
    assert(legacy_v2);
    assert(legacy_v2.state->settings.display_mode == HostDisplayMode::BorderlessFullscreen);
    assert(legacy_v2.state->settings.vsync_mode == HostVSyncMode::On);
    assert(encode_host_product_state(*legacy_v2.state).find("UR-HOST-STATE/3\n") == 0);

    assert(is_valid_profile_id("profile_01"));
    assert(!is_valid_profile_id(""));
    assert(!is_valid_profile_id("contains spaces"));
    assert(!is_valid_profile_id(std::string(65, 'x')));

    assert(!decode_host_product_state("UR-HOST-STATE/4\nprofile=\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=bad/id\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=x\npause_on_focus_loss=yes\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=exclusive\nvsync=on\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=magic\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\nextra=1\n"));

    return 0;
}
