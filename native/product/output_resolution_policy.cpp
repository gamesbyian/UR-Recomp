#include "output_resolution_policy.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <tuple>

namespace ur::product {
namespace {

std::int64_t refresh_distance(int a, int b) noexcept {
    const std::int64_t aa = a;
    const std::int64_t bb = b;
    return aa >= bb ? aa - bb : bb - aa;
}

bool same_resolution(
    const HostOutputResolution& a,
    const HostOutputResolution& b) noexcept {
    return a.kind == HostOutputResolutionKind::Explicit &&
           b.kind == HostOutputResolutionKind::Explicit &&
           a.width == b.width &&
           a.height == b.height;
}

}  // namespace

bool valid_output_mode(const HostOutputMode& mode) noexcept {
    return mode.width > 0 &&
           mode.height > 0 &&
           mode.refresh_millihz >= 0;
}

bool valid_output_resolution(
    const HostOutputResolution& resolution) noexcept {
    if (resolution.kind == HostOutputResolutionKind::Native) {
        return resolution.width == 0 && resolution.height == 0;
    }
    if (resolution.kind == HostOutputResolutionKind::Explicit) {
        return resolution.width > 0 && resolution.height > 0;
    }
    return false;
}

std::vector<HostOutputResolution> build_output_resolution_choices(
    const std::vector<HostOutputMode>& modes) {
    std::vector<HostOutputResolution> choices;
    choices.push_back(HostOutputResolution::native());

    for (const HostOutputMode& mode : modes) {
        if (!valid_output_mode(mode)) {
            continue;
        }
        const HostOutputResolution candidate =
            HostOutputResolution::explicit_size(mode.width, mode.height);
        const auto duplicate = std::find_if(
            choices.begin() + 1,
            choices.end(),
            [&](const HostOutputResolution& existing) {
                return same_resolution(existing, candidate);
            });
        if (duplicate == choices.end()) {
            choices.push_back(candidate);
        }
    }

    std::sort(
        choices.begin() + 1,
        choices.end(),
        [](const HostOutputResolution& a,
           const HostOutputResolution& b) {
            const std::int64_t area_a =
                static_cast<std::int64_t>(a.width) * a.height;
            const std::int64_t area_b =
                static_cast<std::int64_t>(b.width) * b.height;
            return std::tie(area_a, a.width, a.height) <
                   std::tie(area_b, b.width, b.height);
        });

    return choices;
}

HostOutputResolution select_supported_output_resolution(
    const HostOutputResolution& requested,
    const std::vector<HostOutputResolution>& choices) noexcept {
    if (valid_output_resolution(requested)) {
        const auto match = std::find(
            choices.begin(),
            choices.end(),
            requested);
        if (match != choices.end()) {
            return *match;
        }
    }
    return HostOutputResolution::native();
}

HostOutputResolution cycle_output_resolution(
    const HostOutputResolution& current,
    const std::vector<HostOutputResolution>& choices,
    int delta) noexcept {
    if (choices.empty()) {
        return HostOutputResolution::native();
    }

    const HostOutputResolution normalized =
        select_supported_output_resolution(current, choices);
    auto it = std::find(choices.begin(), choices.end(), normalized);
    std::size_t index =
        it == choices.end()
            ? 0u
            : static_cast<std::size_t>(it - choices.begin());

    if (delta > 0) {
        index = (index + 1u) % choices.size();
    } else if (delta < 0) {
        index = (index + choices.size() - 1u) % choices.size();
    }

    return choices[index];
}

std::optional<HostOutputMode> resolve_fullscreen_output_mode(
    const HostOutputResolution& resolution,
    const std::vector<HostOutputMode>& modes,
    const HostOutputMode& native_mode) {
    if (!valid_output_resolution(resolution) ||
        !valid_output_mode(native_mode)) {
        return std::nullopt;
    }

    const int wanted_width =
        resolution.kind == HostOutputResolutionKind::Native
            ? native_mode.width
            : resolution.width;
    const int wanted_height =
        resolution.kind == HostOutputResolutionKind::Native
            ? native_mode.height
            : resolution.height;

    const HostOutputMode* best = nullptr;
    std::int64_t best_distance = std::numeric_limits<std::int64_t>::max();

    for (const HostOutputMode& candidate : modes) {
        if (!valid_output_mode(candidate) ||
            candidate.width != wanted_width ||
            candidate.height != wanted_height) {
            continue;
        }

        const std::int64_t distance =
            native_mode.refresh_millihz > 0 && candidate.refresh_millihz > 0
                ? refresh_distance(
                      candidate.refresh_millihz,
                      native_mode.refresh_millihz)
                : 0;

        if (!best ||
            distance < best_distance ||
            (distance == best_distance &&
             candidate.refresh_millihz > best->refresh_millihz)) {
            best = &candidate;
            best_distance = distance;
        }
    }

    if (!best) {
        return std::nullopt;
    }
    return *best;
}

}  // namespace ur::product
