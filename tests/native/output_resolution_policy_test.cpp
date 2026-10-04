#include "output_resolution_policy.hpp"

#include <cassert>
#include <vector>

using namespace ur::product;

int main() {
    assert(valid_output_mode({1920, 1080, 60000}));
    assert(valid_output_mode({1920, 1080, 0}));
    assert(!valid_output_mode({0, 1080, 60000}));
    assert(!valid_output_mode({1920, -1, 60000}));
    assert(!valid_output_mode({1920, 1080, -1}));

    assert(valid_output_resolution(HostOutputResolution::native()));
    assert(valid_output_resolution(
        HostOutputResolution::explicit_size(1920, 1080)));
    assert(!valid_output_resolution(
        HostOutputResolution::explicit_size(0, 1080)));
    assert(!valid_output_resolution(
        {HostOutputResolutionKind::Native, 1920, 1080}));

    const std::vector<HostOutputMode> modes = {
        {1920, 1080, 60000},
        {1280, 720, 60000},
        {1920, 1080, 120000},
        {2560, 1440, 144000},
        {1920, 1080, 59940},
        {0, 0, 0},
        {1280, 720, 120000},
    };

    const auto choices = build_output_resolution_choices(modes);
    assert(choices.size() == 4);
    assert(choices[0] == HostOutputResolution::native());
    assert(choices[1] == HostOutputResolution::explicit_size(1280, 720));
    assert(choices[2] == HostOutputResolution::explicit_size(1920, 1080));
    assert(choices[3] == HostOutputResolution::explicit_size(2560, 1440));

    const HostOutputMode native{1920, 1080, 59940};

    const auto native_selected = resolve_fullscreen_output_mode(
        HostOutputResolution::native(), modes, native);
    assert(native_selected);
    assert(*native_selected == HostOutputMode{1920, 1080, 59940});

    const auto explicit_selected = resolve_fullscreen_output_mode(
        HostOutputResolution::explicit_size(1920, 1080),
        modes,
        HostOutputMode{2560, 1440, 60000});
    assert(explicit_selected);
    assert(*explicit_selected == HostOutputMode{1920, 1080, 60000});

    const auto nearest_refresh = resolve_fullscreen_output_mode(
        HostOutputResolution::explicit_size(1280, 720),
        modes,
        HostOutputMode{2560, 1440, 100000});
    assert(nearest_refresh);
    assert(*nearest_refresh == HostOutputMode{1280, 720, 120000});

    const auto unknown_refresh = resolve_fullscreen_output_mode(
        HostOutputResolution::explicit_size(1920, 1080),
        modes,
        HostOutputMode{1920, 1080, 0});
    assert(unknown_refresh);
    assert(*unknown_refresh == HostOutputMode{1920, 1080, 120000});

    assert(!resolve_fullscreen_output_mode(
        HostOutputResolution::explicit_size(3840, 2160),
        modes,
        native));
    assert(!resolve_fullscreen_output_mode(
        HostOutputResolution::native(),
        modes,
        HostOutputMode{}));

    return 0;
}
