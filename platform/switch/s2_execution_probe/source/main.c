#include <switch.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

#include "types.h"
#include "common_cpu_infra.h"
#include "common_rtl.h"
#include "game_rtl.h"
#include "netplay/snes_state_digest.h"

extern const unsigned char _binary_rom_sfc_start[];
extern const unsigned char _binary_rom_sfc_end[];

struct SpcPlayer;
struct SpcPlayer *g_spc_player;

bool g_ws_active = false;
int g_ws_extra = 0;
bool g_new_ppu = true;

static FILE *g_report;

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
    fputs("[s2-exec] ", stderr);
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
}

void NORETURN Die(const char *error) {
    if (g_report) {
        fprintf(g_report, "fatal=%s\n", error ? error : "(null)");
        fflush(g_report);
    }
    fprintf(stderr, "UR-SWITCH-S2-FATAL: %s\n", error ? error : "(null)");
    abort();
}

static void write_digest(unsigned frame) {
    SnesStateDigestParts p = {0};
    snes_state_digest_parts(&p);
    fprintf(g_report,
            "checkpoint frame=%u master=%08x cpu=%08x wram=%08x apu=%08x "
            "ppu=%08x dma=%08x cart=%08x\n",
            frame, p.master, p.cpu, p.wram, p.apu, p.ppu, p.dma, p.cart);
    fflush(g_report);
    printf("frame=%u master=%08x\n", frame, p.master);
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    consoleInit(NULL);
    g_report = fopen("ur-recomp-s2-execution-report.txt", "wb");
    if (!g_report) {
        printf("report_open=0\n");
        consoleUpdate(NULL);
        svcSleepThread(2000000000ULL);
        consoleExit(NULL);
        return 2;
    }

    const uint8_t *rom = (const uint8_t *)_binary_rom_sfc_start;
    const size_t rom_size = (size_t)(_binary_rom_sfc_end - _binary_rom_sfc_start);

    fprintf(g_report, "UR-SWITCH-S2-EXEC/1\n");
    fprintf(g_report, "hardware_observation_only=1\n");
    fprintf(g_report, "rom_size=%zu\n", rom_size);
    fprintf(g_report, "simulation_requested_frames=120\n");
    fflush(g_report);

    RtlRegisterGame(&kGameInfo);
    Snes *snes = SnesInit(rom, (int)rom_size);
    fprintf(g_report, "snes_init=%d\n", snes != NULL ? 1 : 0);
    fflush(g_report);

    if (!snes) {
        printf("snes_init=0\n");
        fclose(g_report);
        g_report = NULL;
        consoleUpdate(NULL);
        svcSleepThread(2000000000ULL);
        consoleExit(NULL);
        return 3;
    }

    printf("snes_init=1\n");
    write_digest(0);

    for (unsigned frame = 1; frame <= 120; ++frame) {
        /* RtlRunFrame's bool return is not a success status in the pinned
         * framework: normal completed frames currently return false. Existing
         * hosts drive it for side effects, so this probe does the same. */
        (void)RtlRunFrame(0);
        if (frame == 1 || frame == 60 || frame == 120) write_digest(frame);
    }

    fprintf(g_report, "execution_complete=1\n");
    fprintf(g_report, "deterministic_parity_claim=0\n");
    fflush(g_report);
    printf("execution_complete=1\n");
    printf("Press + to exit\n");
    consoleUpdate(NULL);

    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);
    while (appletMainLoop()) {
        padUpdate(&pad);
        if (padGetButtonsDown(&pad) & HidNpadButton_Plus) break;
    }

    fclose(g_report);
    g_report = NULL;
    consoleExit(NULL);
    return 0;
}
