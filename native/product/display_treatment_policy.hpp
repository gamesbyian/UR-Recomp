#pragma once

#include <cstdint>

namespace ur::product {

/*
 * Post-composition display treatment.
 *
 * This is intentionally separate from:
 * - display geometry / pixel aspect;
 * - logical view width;
 * - graphics representation;
 * - per-source sampling;
 * - Internal Render Scale;
 * - final-window filtering for the untreated mixed-source frame.
 */
enum class HostDisplayTreatment : std::uint8_t {
    Clean = 0,
    CrtNtsc = 1,
    CuratedScaler = 2,
};

struct HostDisplayTreatmentCapabilities {
    bool crt_ntsc = false;
    bool curated_scaler = false;
};

struct HostDisplayTreatmentResolution {
    HostDisplayTreatment requested = HostDisplayTreatment::Clean;
    HostDisplayTreatment effective = HostDisplayTreatment::Clean;
    bool requested_available = true;
    bool uses_post_process = false;
};

constexpr const char* host_display_treatment_label(
    HostDisplayTreatment treatment) noexcept {
    switch (treatment) {
    case HostDisplayTreatment::Clean:
        return "CLEAN";
    case HostDisplayTreatment::CrtNtsc:
        return "CRT/NTSC";
    case HostDisplayTreatment::CuratedScaler:
        return "SCALER";
    }
    return "CLEAN";
}

constexpr bool host_display_treatment_available(
    HostDisplayTreatment treatment,
    HostDisplayTreatmentCapabilities capabilities) noexcept {
    switch (treatment) {
    case HostDisplayTreatment::Clean:
        return true;
    case HostDisplayTreatment::CrtNtsc:
        return capabilities.crt_ntsc;
    case HostDisplayTreatment::CuratedScaler:
        return capabilities.curated_scaler;
    }
    return false;
}

/*
 * Missing post-process capability never mutates another presentation axis.
 *
 * In particular, an unavailable CRT/scaler request does not:
 * - turn on linear final-window filtering;
 * - change source sampling;
 * - change view/aspect/overscan;
 * - change graphics representation;
 * - alter guest state or cadence.
 *
 * It simply resolves to the untreated Clean frame for this presentation.
 */
constexpr HostDisplayTreatmentResolution resolve_host_display_treatment(
    HostDisplayTreatment requested,
    HostDisplayTreatmentCapabilities capabilities) noexcept {
    const bool available =
        host_display_treatment_available(requested, capabilities);
    const auto effective =
        available ? requested : HostDisplayTreatment::Clean;
    return {
        requested,
        effective,
        available,
        effective != HostDisplayTreatment::Clean,
    };
}

constexpr HostDisplayTreatment next_host_display_treatment(
    HostDisplayTreatment treatment) noexcept {
    switch (treatment) {
    case HostDisplayTreatment::Clean:
        return HostDisplayTreatment::CrtNtsc;
    case HostDisplayTreatment::CrtNtsc:
        return HostDisplayTreatment::CuratedScaler;
    case HostDisplayTreatment::CuratedScaler:
        return HostDisplayTreatment::Clean;
    }
    return HostDisplayTreatment::Clean;
}

}  // namespace ur::product
