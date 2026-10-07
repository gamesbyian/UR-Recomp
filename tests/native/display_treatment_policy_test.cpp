#include "display_treatment_policy.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

int main() {
    const HostDisplayTreatmentCapabilities none{};

    const auto clean =
        resolve_host_display_treatment(HostDisplayTreatment::Clean, none);
    assert(clean.requested == HostDisplayTreatment::Clean);
    assert(clean.effective == HostDisplayTreatment::Clean);
    assert(clean.requested_available);
    assert(!clean.uses_post_process);

    const auto unavailable_crt =
        resolve_host_display_treatment(HostDisplayTreatment::CrtNtsc, none);
    assert(unavailable_crt.requested == HostDisplayTreatment::CrtNtsc);
    assert(unavailable_crt.effective == HostDisplayTreatment::Clean);
    assert(!unavailable_crt.requested_available);
    assert(!unavailable_crt.uses_post_process);

    const auto unavailable_scaler =
        resolve_host_display_treatment(
            HostDisplayTreatment::CuratedScaler, {true, false});
    assert(unavailable_scaler.requested ==
           HostDisplayTreatment::CuratedScaler);
    assert(unavailable_scaler.effective == HostDisplayTreatment::Clean);
    assert(!unavailable_scaler.requested_available);
    assert(!unavailable_scaler.uses_post_process);

    const auto crt =
        resolve_host_display_treatment(
            HostDisplayTreatment::CrtNtsc, {true, false});
    assert(crt.effective == HostDisplayTreatment::CrtNtsc);
    assert(crt.requested_available);
    assert(crt.uses_post_process);

    const auto scaler =
        resolve_host_display_treatment(
            HostDisplayTreatment::CuratedScaler, {false, true});
    assert(scaler.effective == HostDisplayTreatment::CuratedScaler);
    assert(scaler.requested_available);
    assert(scaler.uses_post_process);

    assert(std::string(host_display_treatment_label(
               HostDisplayTreatment::Clean)) == "CLEAN");
    assert(std::string(host_display_treatment_label(
               HostDisplayTreatment::CrtNtsc)) == "CRT/NTSC");
    assert(std::string(host_display_treatment_label(
               HostDisplayTreatment::CuratedScaler)) == "SCALER");

    assert(next_host_display_treatment(
               HostDisplayTreatment::Clean) ==
           HostDisplayTreatment::CrtNtsc);
    assert(next_host_display_treatment(
               HostDisplayTreatment::CrtNtsc) ==
           HostDisplayTreatment::CuratedScaler);
    assert(next_host_display_treatment(
               HostDisplayTreatment::CuratedScaler) ==
           HostDisplayTreatment::Clean);

    const auto invalid = static_cast<HostDisplayTreatment>(255);
    assert(!host_display_treatment_available(invalid, {true, true}));
    assert(resolve_host_display_treatment(invalid, {true, true}).effective ==
           HostDisplayTreatment::Clean);
    assert(next_host_display_treatment(invalid) ==
           HostDisplayTreatment::Clean);
    assert(std::string(host_display_treatment_label(invalid)) == "CLEAN");

    return 0;
}
