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
    static_assert(HostProductState::schema_version == 6);

    HostProductState defaults;
    const std::string expected_defaults =
        "UR-HOST-STATE/6\n"
        "profile=\n"
        "pause_on_focus_loss=1\n"
        "vibration_enabled=1\n"
        "display_mode=windowed\n"
        "vsync=on\n"
        "presentation_fps=game\n"
        "output_resolution=native\n";
    assert(encode_host_product_state(defaults) == expected_defaults);

    HostProductState customized;
    customized.active_profile_id = "ian.local-1";
    customized.settings.pause_on_focus_loss = false;
    customized.settings.vibration_enabled = false;
    customized.settings.display_mode = HostDisplayMode::Fullscreen;
    customized.settings.vsync_mode = HostVSyncMode::Adaptive;
    customized.settings.presentation_fps_mode = HostPresentationFpsMode::Fps120;
    customized.settings.output_resolution =
        HostOutputResolution::explicit_size(1920, 1080);
    const std::string encoded = encode_host_product_state(customized);
    assert(encoded ==
        "UR-HOST-STATE/6\n"
        "profile=ian.local-1\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=fullscreen\n"
        "vsync=adaptive\n"
        "presentation_fps=120\n"
        "output_resolution=1920x1080\n");

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
    assert(legacy_v1.state->settings.presentation_fps_mode ==
           HostPresentationFpsMode::Game);
    assert(legacy_v1.state->settings.output_resolution ==
           HostOutputResolution::native());

    const auto legacy_v2 = decode_host_product_state(
        "UR-HOST-STATE/2\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=borderless\n");
    assert(legacy_v2);
    assert(legacy_v2.state->settings.display_mode == HostDisplayMode::BorderlessFullscreen);
    assert(legacy_v2.state->settings.vsync_mode == HostVSyncMode::On);
    assert(legacy_v2.state->settings.presentation_fps_mode ==
           HostPresentationFpsMode::Game);
    assert(legacy_v2.state->settings.output_resolution ==
           HostOutputResolution::native());

    const auto legacy_v3 = decode_host_product_state(
        "UR-HOST-STATE/3\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=borderless\n"
        "vsync=adaptive\n");
    assert(legacy_v3);
    assert(legacy_v3.state->settings.presentation_fps_mode ==
           HostPresentationFpsMode::Game);
    assert(legacy_v3.state->settings.output_resolution ==
           HostOutputResolution::native());

    const auto legacy_v4 = decode_host_product_state(
        "UR-HOST-STATE/4\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=fullscreen\n"
        "vsync=adaptive\n");
    assert(legacy_v4);
    assert(legacy_v4.state->settings.display_mode == HostDisplayMode::Fullscreen);
    assert(legacy_v4.state->settings.presentation_fps_mode ==
           HostPresentationFpsMode::Game);
    assert(legacy_v4.state->settings.output_resolution ==
           HostOutputResolution::native());

    const auto legacy_v5 = decode_host_product_state(
        "UR-HOST-STATE/5\n"
        "profile=legacy.profile\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n"
        "display_mode=fullscreen\n"
        "vsync=adaptive\n"
        "presentation_fps=144\n");
    assert(legacy_v5);
    assert(legacy_v5.state->settings.presentation_fps_mode ==
           HostPresentationFpsMode::Fps144);
    assert(legacy_v5.state->settings.output_resolution ==
           HostOutputResolution::native());
    assert(encode_host_product_state(*legacy_v5.state).find("UR-HOST-STATE/6\n") == 0);

    assert(is_valid_profile_id("profile_01"));
    assert(!is_valid_profile_id(""));
    assert(!is_valid_profile_id("contains spaces"));
    assert(!is_valid_profile_id(std::string(65, 'x')));

    assert(!decode_host_product_state("UR-HOST-STATE/7\nprofile=\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\noutput_resolution=native\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=bad/id\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=x\npause_on_focus_loss=yes\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/3\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=fullscreen\nvsync=on\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=exclusive\nvsync=on\npresentation_fps=game\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=magic\npresentation_fps=game\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=magic\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/5\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\nextra=1\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/6\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\noutput_resolution=1920\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/6\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\noutput_resolution=0x1080\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/6\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\noutput_resolution=1920x0\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/6\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\ndisplay_mode=windowed\nvsync=on\npresentation_fps=game\noutput_resolution=1920x1080x60\n"));

    return 0;
}
