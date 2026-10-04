#include "uniracers_course_identity.h"

#include <cassert>
#include <cstddef>
#include <vector>

namespace {

void write16(std::vector<unsigned char>& data, std::size_t offset, int value) {
    data[offset] = static_cast<unsigned char>(value & 0xff);
    data[offset + 1] = static_cast<unsigned char>((value >> 8) & 0xff);
}

std::vector<unsigned char> dragster_header(unsigned cursor_low) {
    std::vector<unsigned char> data(32, 0);
    data[0x02] = 0;
    write16(data, 0x03, 68);
    write16(data, 0x05, 50);
    write16(data, 0x07, 68);
    write16(data, 0x09, 50);
    data[0x0B] = static_cast<unsigned char>(cursor_low);
    data[0x0C] = 0x84;
    data[0x0D] = 0;  // encoded 256
    data[0x0E] = 4;
    return data;
}

}  // namespace

int main() {
    auto decoded = dragster_header(0x0f);
    auto dragster = ur_uniracers_identify_course(decoded.data(), decoded.size());
    assert(dragster.valid);
    assert(dragster.course_index == 1);

    // The resource-list cursor is known to mutate 0x840F -> 0x8416 during
    // Dragster setup; identity must remain stable across that mutation.
    decoded[0x0B] = 0x16;
    auto settled = ur_uniracers_identify_course(decoded.data(), decoded.size());
    assert(settled.valid);
    assert(settled.course_index == 1);

    // One immutable header field changing must fail closed rather than
    // guessing the nearest course.
    write16(decoded, 0x03, 69);
    assert(!ur_uniracers_identify_course(decoded.data(), decoded.size()).valid);

    assert(!ur_uniracers_identify_course(nullptr, decoded.size()).valid);
    assert(!ur_uniracers_identify_course(decoded.data(), 0x0e).valid);

    return 0;
}
