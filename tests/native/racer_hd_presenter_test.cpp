#include "racer_hd_presenter.hpp"
#include "racer_replacement_selector.hpp"

#include <cassert>
#include <cstdint>

int main() {
    using namespace ur::presentation;

    // The yellow marker is intentionally asymmetric.
    const std::uint32_t marker = sample_racer_hd_asset(144, 58, false, false);
    assert(marker == 0xFFFFD84Au);
    assert(sample_racer_hd_asset(111, 58, true, false) == marker);
    assert(sample_racer_hd_asset(144, 197, false, true) == marker);
    assert(sample_racer_hd_asset(111, 197, true, true) == marker);

    // Orientation is a presentation transform: the unflipped semantic asset
    // remains stable and transparent outside its local canvas.
    assert(sample_racer_hd_asset(-1, 0, false, false) == 0);
    assert(sample_racer_hd_asset(kRacerHdAssetSize, 0, false, false) == 0);
    assert(sample_racer_hd_asset(144, 58, false, false) ==
           sample_racer_hd_asset(144, 58, false, false));

    assert(racer_hd_asset_available(0x0541));
    assert(racer_hd_asset_available(0x0540));
    assert(racer_hd_asset_available(0x057D));
    assert(racer_hd_asset_available(0x0542));
    assert(racer_hd_asset_available(0x0543));
    assert(racer_hd_asset_available(0x057E));
    assert(racer_hd_asset_available(0x057F));
    assert(racer_hd_asset_available(0x0544));
    assert(!racer_hd_asset_available(0x0999));

    // Position is a later presentation coordinate, not semantic identity.
    const auto* registration = find_racer_registration(0x0541);
    assert(registration != nullptr);
    const auto selected = select_racer_presentation(
        GraphicsPack::Remastered,
        0x0541,
        registration->composition
    );
    assert(selected.uses_replacement());
    assert(selected.registration == registration);

    RacerOamPlacement a{};
    a.x_signed = 10;
    a.y_raw_8bit = 20;
    RacerOamPlacement b = a;
    b.x_signed = 30;
    b.y_raw_8bit = 35;

    const auto pa = sample_racer_hd_presented_pixel(a, 46, 34);
    const auto pb = sample_racer_hd_presented_pixel(b, 66, 49);
    assert(pa == pb);
    assert(pa != 0);
    assert(selected.registration->semantic_frame_id == 0x0541);
    return 0;
}
