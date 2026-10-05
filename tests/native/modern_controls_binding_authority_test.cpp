#include "modern_controls_binding_authority.hpp"

#include <cassert>
#include <utility>
#include <vector>

using namespace ur::product;

int main() {
    std::vector<std::pair<int, int>> sets;
    int resets = 0;
    int saves = 0;

    ModernControlsBindingAuthority authority{
        [&](int button, int scancode) {
            sets.emplace_back(button, scancode);
        },
        [&]() { ++resets; },
        [&]() { ++saves; },
    };

    assert(apply_modern_controls_command(
        {ModernControlsCommandKind::ApplyCapturedKey,
         ModernControlBinding::B,
         42},
        authority));
    assert(sets.size() == 1);
    assert(sets[0].first == static_cast<int>(ModernControlBinding::B));
    assert(sets[0].second == 42);
    assert(saves == 1);

    // Clearing is represented by the framework's UNKNOWN/unbound scancode 0.
    assert(apply_modern_controls_command(
        {ModernControlsCommandKind::ClearBinding,
         ModernControlBinding::B,
         0},
        authority));
    assert(sets.size() == 2);
    assert(sets[1].second == 0);
    assert(saves == 2);

    assert(apply_modern_controls_command(
        {ModernControlsCommandKind::ResetPlayer,
         ModernControlBinding::A,
         0},
        authority));
    assert(resets == 1);
    assert(saves == 3);

    // UI-only commands do not touch framework authority or persistence.
    assert(!apply_modern_controls_command(
        {ModernControlsCommandKind::BeginCapture,
         ModernControlBinding::A,
         0},
        authority));
    assert(!apply_modern_controls_command(
        {ModernControlsCommandKind::Close,
         ModernControlBinding::A,
         0},
        authority));
    assert(saves == 3);

    ModernControlsBindingAuthority incomplete{};
    assert(!apply_modern_controls_command(
        {ModernControlsCommandKind::ApplyCapturedKey,
         ModernControlBinding::A,
         42},
        incomplete));

    return 0;
}
