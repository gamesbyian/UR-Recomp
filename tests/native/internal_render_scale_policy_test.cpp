#include "internal_render_scale_policy.hpp"

#include <cassert>

int main() {
    using ur::product::resolve_internal_render_scale;

    assert(resolve_internal_render_scale(true, false, false, 1) == 1);
    assert(resolve_internal_render_scale(true, false, false, 4) == 4);
    assert(resolve_internal_render_scale(true, true, false, 4) == 4);
    assert(resolve_internal_render_scale(true, false, true, 4) == 1);
    assert(resolve_internal_render_scale(false, false, false, 4) == 1);
    assert(resolve_internal_render_scale(true, false, false, 0) == 1);
    assert(resolve_internal_render_scale(true, false, false, 5) == 1);
    return 0;
}
