#include "presentation_sampling_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    assert(resolve_presentation_sampling(
               HostPresentationSource::OriginalPixelArt) ==
           HostPresentationSampling::NearestInteger);
    assert(resolve_presentation_sampling(
               HostPresentationSource::RemasteredRaster) ==
           HostPresentationSampling::NativeDensity);
    assert(resolve_presentation_sampling(
               HostPresentationSource::ReimaginedRaster) ==
           HostPresentationSampling::NativeDensity);
    assert(resolve_presentation_sampling(
               HostPresentationSource::ModernPrimitive) ==
           HostPresentationSampling::DirectAtPresentationDensity);
    assert(resolve_presentation_sampling(
               HostPresentationSource::ModernGlyph) ==
           HostPresentationSampling::DirectAtPresentationDensity);
    return 0;
}
