#include "uniracers_course_identity.h"

#include <stdint.h>

namespace {

struct CourseHeaderSignature {
    int index;
    int mode;
    int a_x;
    int a_y;
    int b_x;
    int b_y;
    int dim_a;
    int dim_b;
};

constexpr CourseHeaderSignature kUsaRetailCourses[] = {
    {1, 0, 68, 50, 68, 50, 256, 4},
    {2, 0, 575, 93, 575, 93, 64, 16},
    {3, 45, 361, 89, 323, 90, 64, 16},
    {4, 0, 99, 26, 99, 34, 256, 4},
    {5, 0, 290, 26, 290, 28, 32, 32},
    {6, 0, 142, 32, 142, 30, 16, 64},
    {7, 0, 445, 244, 445, 243, 64, 16},
    {8, 45, 8, 22, 8, 22, 32, 32},
    {9, 0, 36, 104, 36, 104, 128, 8},
    {10, 0, 481, 190, 481, 190, 64, 16},
    {11, 0, 111, 40, 111, 38, 16, 64},
    {12, 0, 593, 202, 593, 202, 64, 16},
    {13, 45, 262, 393, 137, 394, 32, 32},
    {14, 0, 137, 2, 137, 4, 128, 8},
    {15, 0, 45, 81, 45, 81, 64, 16},
    {16, 0, 1013, 3, 1013, 3, 64, 16},
    {17, 0, 312, 44, 312, 44, 64, 16},
    {18, 45, 154, 113, 157, 113, 64, 16},
    {19, 0, 2, 2, 2, 2, 32, 32},
    {20, 0, 51, 28, 51, 28, 64, 16},
    {21, 0, 204, 20, 204, 22, 128, 8},
    {22, 0, 495, 92, 495, 92, 64, 16},
    {23, 45, 0, 60, 0, 60, 32, 32},
    {24, 0, 7, 8, 7, 8, 64, 16},
    {25, 0, 496, 159, 496, 159, 64, 16},
    {26, 0, 42, 62, 42, 62, 32, 32},
    {27, 0, 79, 30, 79, 30, 32, 32},
    {28, 45, 128, 64, 128, 64, 64, 16},
    {29, 0, 10, 2, 10, 2, 32, 32},
    {30, 0, 110, 28, 110, 24, 64, 16},
    {31, 0, 88, 2, 88, 2, 256, 4},
    {32, 0, 556, 90, 556, 90, 64, 16},
    {33, 45, 29, 6, 29, 6, 16, 64},
    {34, 0, 193, 26, 193, 28, 256, 4},
    {35, 0, 498, 175, 498, 173, 64, 16},
    {36, 0, 36, 1008, 36, 1008, 16, 64},
    {37, 0, 340, 181, 340, 181, 32, 32},
    {38, 45, 30, 499, 33, 499, 4, 256},
    {39, 0, 22, 2, 22, 2, 64, 16},
    {40, 0, 144, 58, 144, 58, 64, 16},
    {41, 0, 135, 11, 135, 9, 32, 32},
    {42, 0, 97, 96, 97, 96, 64, 16},
    {43, 45, 356, 168, 356, 168, 64, 16},
    {44, 0, 24, 0, 24, 0, 32, 32},
    {45, 0, 198, 156, 198, 156, 64, 16},
};

uint16_t le16(const unsigned char* p, size_t offset) {
    return static_cast<uint16_t>(
        static_cast<uint16_t>(p[offset]) |
        (static_cast<uint16_t>(p[offset + 1]) << 8));
}

int decode_dim(unsigned char value) {
    return value == 0 ? 256 : static_cast<int>(value);
}

}  // namespace

extern "C" UrUniracersCourseIdentity ur_uniracers_identify_course(
    const unsigned char* decoded_course,
    size_t available_bytes) {
    if (!decoded_course || available_bytes < 0x0Fu) return {};

    const int mode = decoded_course[0x02];
    const int a_x = le16(decoded_course, 0x03);
    const int a_y = le16(decoded_course, 0x05);
    const int b_x = le16(decoded_course, 0x07);
    const int b_y = le16(decoded_course, 0x09);
    const int dim_a = decode_dim(decoded_course[0x0D]);
    const int dim_b = decode_dim(decoded_course[0x0E]);

    for (const auto& course : kUsaRetailCourses) {
        if (course.mode == mode &&
            course.a_x == a_x &&
            course.a_y == a_y &&
            course.b_x == b_x &&
            course.b_y == b_y &&
            course.dim_a == dim_a &&
            course.dim_b == dim_b) {
            return {1, course.index};
        }
    }
    return {};
}
