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

    HostProductState defaults;
    const std::string expected_defaults =
        "UR-HOST-STATE/1\n"
        "profile=\n"
        "pause_on_focus_loss=1\n"
        "vibration_enabled=1\n";
    assert(encode_host_product_state(defaults) == expected_defaults);

    HostProductState customized;
    customized.active_profile_id = "ian.local-1";
    customized.settings.pause_on_focus_loss = false;
    customized.settings.vibration_enabled = false;
    const std::string encoded = encode_host_product_state(customized);
    assert(encoded ==
        "UR-HOST-STATE/1\n"
        "profile=ian.local-1\n"
        "pause_on_focus_loss=0\n"
        "vibration_enabled=0\n");

    const auto decoded = decode_host_product_state(encoded);
    assert(decoded);
    assert(*decoded.state == customized);
    assert(encode_host_product_state(*decoded.state) == encoded);

    assert(is_valid_profile_id("profile_01"));
    assert(!is_valid_profile_id(""));
    assert(!is_valid_profile_id("contains spaces"));
    assert(!is_valid_profile_id(std::string(65, 'x')));

    assert(!decode_host_product_state("UR-HOST-STATE/2\nprofile=\npause_on_focus_loss=1\nvibration_enabled=1\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/1\nprofile=bad/id\npause_on_focus_loss=1\nvibration_enabled=1\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/1\nprofile=x\npause_on_focus_loss=yes\nvibration_enabled=1\n"));
    assert(!decode_host_product_state("UR-HOST-STATE/1\nprofile=x\npause_on_focus_loss=1\nvibration_enabled=1\nextra=1\n"));

    return 0;
}
