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
    fputs("[s2-reference] ", stderr);
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
}

void NORETURN Die(const char *error) {
    fprintf(stderr, "S2_REFERENCE_FATAL: %s\n", error ? error : "(null)");
    exit(2);
}

static unsigned char *read_file(const char *path, size_t *size_out) {
    FILE *f = fopen(path, "rb");
    unsigned char *data;
    long size;
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    size = ftell(f);
    if (size <= 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    data = (unsigned char *)malloc((size_t)size);
    if (!data) { fclose(f); return NULL; }
    if (fread(data, 1, (size_t)size, f) != (size_t)size) {
        free(data);
        fclose(f);
        return NULL;
    }
    fclose(f);
    *size_out = (size_t)size;
    return data;
}

static void emit_digest(unsigned frame) {
    SnesStateDigestParts p = {0};
    snes_state_digest_parts(&p);
    printf(
        "checkpoint frame=%u master=%08x cpu=%08x wram=%08x apu=%08x "
        "ppu=%08x dma=%08x cart=%08x\n",
        frame, p.master, p.cpu, p.wram, p.apu, p.ppu, p.dma, p.cart);
}

int main(int argc, char **argv) {
    size_t rom_size = 0;
    unsigned char *rom;
    Snes *snes;

    if (argc != 2) {
        fprintf(stderr, "usage: %s <canonical-rom>\n", argv[0]);
        return 64;
    }

    rom = read_file(argv[1], &rom_size);
    if (!rom) {
        fprintf(stderr, "could not read ROM: %s\n", argv[1]);
        return 65;
    }

    printf("UR-S2-DESKTOP-REFERENCE/1\n");
    printf("rom_size=%zu\n", rom_size);
    printf("simulation_requested_frames=120\n");

    RtlRegisterGame(&kGameInfo);
    snes = SnesInit(rom, (int)rom_size);
    printf("snes_init=%d\n", snes != NULL ? 1 : 0);
    if (!snes) {
        free(rom);
        return 66;
    }

    emit_digest(0);
    for (unsigned frame = 1; frame <= 120; ++frame) {
        /* The pinned framework's normal RtlRunFrame path returns false after
         * completing a frame. Treat it as a frame-driving side effect, matching
         * the framework's desktop and test clients. */
        (void)RtlRunFrame(0);
        if (frame == 1 || frame == 60 || frame == 120) emit_digest(frame);
    }

    printf("execution_complete=1\n");
    free(rom);
    return 0;
}
