#include "uniracers_course_identity.h"

#include <cstddef>
#include <iostream>
#include <vector>

namespace {

void write16(std::vector<unsigned char>& data, std::size_t offset, int value) {
    data[offset] = static_cast<unsigned char>(value & 0xff);
    data[offset + 1] = static_cast<unsigned char>((value >> 8) & 0xff);
}

unsigned char encode_dim(int value) {
    return static_cast<unsigned char>(value == 256 ? 0 : value);
}

}  // namespace

int main() {
    int mode, ax, ay, bx, by, da, db;
    while (std::cin >> mode >> ax >> ay >> bx >> by >> da >> db) {
        std::vector<unsigned char> data(32, 0);
        data[0x02] = static_cast<unsigned char>(mode);
        write16(data, 0x03, ax);
        write16(data, 0x05, ay);
        write16(data, 0x07, bx);
        write16(data, 0x09, by);
        data[0x0D] = encode_dim(da);
        data[0x0E] = encode_dim(db);
        const auto identity =
            ur_uniracers_identify_course(data.data(), data.size());
        std::cout << (identity.valid ? identity.course_index : 0) << "\n";
    }
    return 0;
}
