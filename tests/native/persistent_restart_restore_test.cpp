#include "modern_session_c_api.h"

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

std::vector<std::uint8_t> guest;
std::vector<std::uint8_t> persistent;
bool refuse_load = false;

bool load_snapshot(const void* data, std::size_t size) {
    if (refuse_load) {
        persistent = {0xEE, 0xEE};
        return false;
    }
    const auto* bytes = static_cast<const std::uint8_t*>(data);
    guest.assign(bytes, bytes + size);
    // Model the rollback serializer restoring cartridge SRAM from the anchor.
    persistent = {1, 2, 3, 4};
    return true;
}

}  // namespace

int main() {
    const std::uint8_t snapshot[] = {9, 8, 7};

    persistent = {5, 6, 7, 8};
    assert(ur_modern_session_load_preserving_persistent_bytes(
        &load_snapshot,
        snapshot,
        sizeof(snapshot),
        persistent.data(),
        persistent.size()));
    assert((guest == std::vector<std::uint8_t>{9, 8, 7}));
    assert((persistent == std::vector<std::uint8_t>{5, 6, 7, 8}));

    // Preservation is fail-closed around a refused/partial runtime load too.
    persistent = {4, 3};
    refuse_load = true;
    assert(!ur_modern_session_load_preserving_persistent_bytes(
        &load_snapshot,
        snapshot,
        sizeof(snapshot),
        persistent.data(),
        persistent.size()));
    assert((persistent == std::vector<std::uint8_t>{4, 3}));

    assert(!ur_modern_session_load_preserving_persistent_bytes(
        nullptr,
        snapshot,
        sizeof(snapshot),
        persistent.data(),
        persistent.size()));

    return 0;
}
