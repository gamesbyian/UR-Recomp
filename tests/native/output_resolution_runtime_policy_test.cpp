#include "output_resolution_runtime_policy.hpp"

#include <cassert>
#include <vector>

using namespace ur::product;

namespace {

struct ApplyProbe {
    int calls = 0;
    bool accept = true;
    HostOutputMode last{};
};

bool apply_probe(void* context, const HostOutputMode& mode) {
    auto* probe = static_cast<ApplyProbe*>(context);
    ++probe->calls;
    probe->last = mode;
    return probe->accept;
}

}  // namespace

int main() {
    const std::vector<HostOutputMode> modes = {
        {1280, 720, 60000},
        {1920, 1080, 59940},
        {1920, 1080, 120000},
        {2560, 1440, 144000},
    };
    const HostOutputMode native{1920, 1080, 59940};

    ApplyProbe probe;

    auto result = apply_output_resolution_policy(
        HostDisplayMode::Windowed,
        HostOutputResolution::explicit_size(1280, 720),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::NotApplicable);
    assert(!result.selected_mode);
    assert(probe.calls == 0);

    result = apply_output_resolution_policy(
        HostDisplayMode::BorderlessFullscreen,
        HostOutputResolution::explicit_size(1280, 720),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::NotApplicable);
    assert(!result.selected_mode);
    assert(probe.calls == 0);

    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::native(),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::Applied);
    assert(result.selected_mode);
    const HostOutputMode expected_native{1920, 1080, 59940};
    assert(*result.selected_mode == expected_native);
    assert(probe.calls == 1);
    assert(probe.last == expected_native);

    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::explicit_size(2560, 1440),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::Applied);
    assert(result.selected_mode);
    const HostOutputMode expected_explicit{2560, 1440, 144000};
    assert(*result.selected_mode == expected_explicit);
    assert(probe.calls == 2);
    assert(probe.last == expected_explicit);

    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::explicit_size(3840, 2160),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::Unsupported);
    assert(!result.selected_mode);
    assert(probe.calls == 2);

    probe.accept = false;
    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::explicit_size(1280, 720),
        modes,
        native,
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::HostRejected);
    assert(result.selected_mode);
    const HostOutputMode expected_rejected{1280, 720, 60000};
    assert(*result.selected_mode == expected_rejected);
    assert(probe.calls == 3);
    assert(probe.last == expected_rejected);

    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::native(),
        modes,
        HostOutputMode{},
        apply_probe,
        &probe);
    assert(result.status == OutputResolutionApplyStatus::Unsupported);
    assert(!result.selected_mode);
    assert(probe.calls == 3);

    result = apply_output_resolution_policy(
        HostDisplayMode::Fullscreen,
        HostOutputResolution::native(),
        modes,
        native,
        nullptr,
        nullptr);
    assert(result.status == OutputResolutionApplyStatus::HostRejected);
    assert(result.selected_mode);

    return 0;
}
