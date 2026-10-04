#pragma once

#include <cstdint>
#include <optional>
#include <vector>

namespace ur::product {

struct HostOutputMode {
    int width = 0;
    int height = 0;
    int refresh_millihz = 0;

    bool operator==(const HostOutputMode& other) const noexcept {
        return width == other.width &&
               height == other.height &&
               refresh_millihz == other.refresh_millihz;
    }
};

enum class HostOutputResolutionKind : std::uint8_t {
    Native = 0,
    Explicit = 1,
};

struct HostOutputResolution {
    HostOutputResolutionKind kind = HostOutputResolutionKind::Native;
    int width = 0;
    int height = 0;

    static constexpr HostOutputResolution native() noexcept {
        return {};
    }

    static constexpr HostOutputResolution explicit_size(
        int width,
        int height) noexcept {
        return {HostOutputResolutionKind::Explicit, width, height};
    }

    bool operator==(const HostOutputResolution& other) const noexcept {
        return kind == other.kind &&
               width == other.width &&
               height == other.height;
    }
};

bool valid_output_mode(const HostOutputMode& mode) noexcept;
bool valid_output_resolution(const HostOutputResolution& resolution) noexcept;

std::vector<HostOutputResolution> build_output_resolution_choices(
    const std::vector<HostOutputMode>& modes);

/* Keep a persisted request only while the active monitor still exposes it.
 * Missing/invalid requests fall back to Native without implying persistence. */
HostOutputResolution select_supported_output_resolution(
    const HostOutputResolution& requested,
    const std::vector<HostOutputResolution>& choices) noexcept;

/* Cycle within the current monitor's semantic catalog. A stale persisted
 * request first normalizes to Native, then moves in the requested direction. */
HostOutputResolution cycle_output_resolution(
    const HostOutputResolution& current,
    const std::vector<HostOutputResolution>& choices,
    int delta) noexcept;

std::optional<HostOutputMode> resolve_fullscreen_output_mode(
    const HostOutputResolution& resolution,
    const std::vector<HostOutputMode>& modes,
    const HostOutputMode& native_mode);

}  // namespace ur::product
