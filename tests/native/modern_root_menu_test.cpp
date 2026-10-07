#include "modern_root_menu.hpp"

#include <cassert>
#include <cstring>

using namespace ur::product;

namespace {

bool same(const char* lhs, const char* rhs) {
    return std::strcmp(lhs, rhs) == 0;
}

}  // namespace

int main() {
    static_assert(kModernRootDestinationCount == 5);
    static_assert(
        modern_root_destination_index(ModernRootDestination::Play) == 0);
    static_assert(
        modern_root_destination_index(ModernRootDestination::Options) == 4);

    auto menu = modern_root_menu_reset();
    assert(menu.selected == ModernRootDestination::Play);
    assert(same(modern_root_destination_label(menu.selected), "PLAY"));

    const ModernRootDestination forward[] = {
        ModernRootDestination::Practice,
        ModernRootDestination::Multiplayer,
        ModernRootDestination::Records,
        ModernRootDestination::Options,
        ModernRootDestination::Play,
    };
    for (const auto expected : forward) {
        menu = modern_root_menu_move(menu, 1);
        assert(menu.selected == expected);
    }

    const ModernRootDestination reverse[] = {
        ModernRootDestination::Options,
        ModernRootDestination::Records,
        ModernRootDestination::Multiplayer,
        ModernRootDestination::Practice,
        ModernRootDestination::Play,
    };
    for (const auto expected : reverse) {
        menu = modern_root_menu_move(menu, -1);
        assert(menu.selected == expected);
    }

    const auto unchanged = modern_root_menu_move(menu, 0);
    assert(unchanged.selected == ModernRootDestination::Play);

    assert(same(
        modern_root_destination_label(ModernRootDestination::Practice),
        "PRACTICE"));
    assert(same(
        modern_root_destination_label(ModernRootDestination::Multiplayer),
        "MULTIPLAYER"));
    assert(same(
        modern_root_destination_label(ModernRootDestination::Records),
        "RECORDS"));
    assert(same(
        modern_root_destination_label(ModernRootDestination::Options),
        "OPTIONS"));

    ModernRootMenu invalid{
        static_cast<ModernRootDestination>(255)};
    invalid = modern_root_menu_move(invalid, 1);
    assert(invalid.selected == ModernRootDestination::Practice);

    return 0;
}
