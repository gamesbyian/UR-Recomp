#include "regional_presentation_input_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    static_assert(regional_secret_title_surface(true, 0x84, false, false));
    static_assert(!regional_secret_title_surface(false, 0x84, false, false));
    static_assert(!regional_secret_title_surface(true, 0xD7, false, false));
    static_assert(!regional_secret_title_surface(true, 0x84, true, false));
    static_assert(!regional_secret_title_surface(true, 0x84, false, true));

    const auto title =
        regional_secret_context(true, 0x84, false, false);
    assert(title.modern_mode);
    assert(title.idle_title_surface);
    assert(!title.text_entry_active);

    const auto main_menu =
        regional_secret_context(true, 0xD7, false, false);
    assert(!main_menu.idle_title_surface);

    char out = 0;
    assert(regional_secret_keyboard_character('P', out));
    assert(out == 'P');
    assert(regional_secret_keyboard_character('a', out));
    assert(out == 'a');
    assert(!regional_secret_keyboard_character(13, out));
    assert(!regional_secret_keyboard_character(0x40000000, out));
    return 0;
}
