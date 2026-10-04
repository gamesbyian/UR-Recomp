#pragma once

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct UrUniracersCourseIdentity {
    int valid;
    int course_index; /* 1..45 for the canonical USA retail corpus */
} UrUniracersCourseIdentity;

/* Resolve the active decoded-course header at 7F:0000 to the canonical
 * course ordinal. This deliberately ignores the mutable resource cursor at
 * decoded offsets 0x0B..0x0C. */
UrUniracersCourseIdentity ur_uniracers_identify_course(
    const unsigned char* decoded_course,
    size_t available_bytes);

#ifdef __cplusplus
}
#endif
