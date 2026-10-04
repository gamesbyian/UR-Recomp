#include <switch.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

#include "types.h"

struct SpcPlayer;
struct SpcPlayer *g_spc_player;

bool g_ws_active = false;
int g_ws_extra = 0;
bool g_new_ppu = true;

void RtlApuLock(void) {}
void RtlApuUnlock(void) {}

void RtlDrawPpuFrame(uint8 *pixel_buffer, size_t pitch, uint32 render_flags) {
    (void)pixel_buffer;
    (void)pitch;
    (void)render_flags;
}

void MkDir(const char *path) {
    if (path && path[0]) (void)mkdir(path, 0755);
}

void ChangeWindowScale(int scale_step) {
    (void)scale_step;
}

void host_report_breadcrumb(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    fputs("[s2-host] ", stderr);
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
}

void NORETURN Die(const char *error) {
    fprintf(stderr, "UR-SWITCH-S2-FATAL: %s\n", error ? error : "(null)");
    abort();
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    consoleInit(NULL);
    printf("UR_SWITCH_S2_LINK_OK\n");
    printf("guest_runtime_linked=1\n");
    printf("simulation_started=0\n");
    printf("hardware_parity_claim=0\n");
    consoleUpdate(NULL);

    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);

    while (appletMainLoop()) {
        padUpdate(&pad);
        if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break;
    }

    consoleExit(NULL);
    return 0;
}
