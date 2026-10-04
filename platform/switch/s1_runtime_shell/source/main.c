#include <switch.h>
#include <SDL.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct UrSwitchS1Report {
    int lifecycle_started;
    int clean_exit;
    int display_ready;
    int audio_ready;
    int storage_writable;
    int input_seen;
    int operation_mode;
    int display_width;
    int display_height;
    unsigned controller_styles_seen;
    unsigned background_events;
    unsigned foreground_events;
} UrSwitchS1Report;

static const char* kReportPath = "ur-recomp-s1-capability-report.txt";
static const char* kStorageProbePath = "ur-recomp-s1-storage-probe.tmp";

static void audio_silence(void* userdata, Uint8* stream, int len) {
    (void)userdata;
    if (stream && len > 0) memset(stream, 0, (size_t)len);
}

static void select_output_size(int operation_mode, int* width, int* height) {
    if (operation_mode == (int)AppletOperationMode_Console) {
        *width = 1920;
        *height = 1080;
    } else {
        *width = 1280;
        *height = 720;
    }
}

static int storage_probe(void) {
    static const char payload[] = "UR-RECOMP-SWITCH-S1\n";
    char verify[sizeof(payload)] = {0};

    FILE* file = fopen(kStorageProbePath, "wb");
    if (!file) return 0;
    const size_t written = fwrite(payload, 1, sizeof(payload), file);
    const int flushed = fflush(file) == 0;
    const int closed = fclose(file) == 0;
    if (written != sizeof(payload) || !flushed || !closed) {
        remove(kStorageProbePath);
        return 0;
    }

    file = fopen(kStorageProbePath, "rb");
    if (!file) {
        remove(kStorageProbePath);
        return 0;
    }
    const size_t read = fread(verify, 1, sizeof(verify), file);
    const int read_closed = fclose(file) == 0;
    const int match =
        read == sizeof(payload) &&
        read_closed &&
        memcmp(payload, verify, sizeof(payload)) == 0;
    remove(kStorageProbePath);
    return match;
}

static void write_report(const UrSwitchS1Report* report) {
    FILE* file = fopen(kReportPath, "wb");
    if (!file) return;

    fprintf(file, "UR-SWITCH-S1/1\n");
    fprintf(file, "scope=hardware-observation-only\n");
    fprintf(file, "lifecycle_started=%d\n", report->lifecycle_started);
    fprintf(file, "clean_exit=%d\n", report->clean_exit);
    fprintf(file, "operation_mode=%d\n", report->operation_mode);
    fprintf(file, "display_ready=%d\n", report->display_ready);
    fprintf(file, "display_size=%dx%d\n", report->display_width, report->display_height);
    fprintf(file, "audio_ready=%d\n", report->audio_ready);
    fprintf(file, "storage_writable=%d\n", report->storage_writable);
    fprintf(file, "input_seen=%d\n", report->input_seen);
    fprintf(file, "controller_styles_seen=0x%08X\n", report->controller_styles_seen);
    fprintf(file, "background_events=%u\n", report->background_events);
    fprintf(file, "foreground_events=%u\n", report->foreground_events);
    fprintf(file, "suspend_resume_observed=%d\n",
            report->background_events > 0 && report->foreground_events > 0 ? 1 : 0);
    fclose(file);
}

static void draw_status(SDL_Renderer* renderer, const UrSwitchS1Report* report) {
    SDL_SetRenderDrawColor(renderer, 16, 18, 24, 255);
    SDL_RenderClear(renderer);

    const int width = report->display_width;
    SDL_Rect display_bar = {0, 0, report->display_ready ? width : 0, 24};
    SDL_Rect audio_bar = {0, 32, report->audio_ready ? width : 0, 24};
    SDL_Rect storage_bar = {0, 64, report->storage_writable ? width : 0, 24};
    SDL_Rect input_bar = {0, 96, report->input_seen ? width : 0, 24};

    SDL_SetRenderDrawColor(renderer, 60, 180, 120, 255);
    SDL_RenderFillRect(renderer, &display_bar);
    SDL_SetRenderDrawColor(renderer, 80, 140, 220, 255);
    SDL_RenderFillRect(renderer, &audio_bar);
    SDL_SetRenderDrawColor(renderer, 220, 180, 80, 255);
    SDL_RenderFillRect(renderer, &storage_bar);
    SDL_SetRenderDrawColor(renderer, 180, 100, 220, 255);
    SDL_RenderFillRect(renderer, &input_bar);
    SDL_RenderPresent(renderer);
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    UrSwitchS1Report report = {0};
    report.lifecycle_started = 1;
    report.operation_mode = (int)appletGetOperationMode();
    select_output_size(report.operation_mode, &report.display_width, &report.display_height);

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_EVENTS) < 0) {
        write_report(&report);
        return EXIT_FAILURE;
    }

    SDL_Window* window = SDL_CreateWindow(
        "UR-Recomp Switch S1",
        0,
        0,
        report.display_width,
        report.display_height,
        0);
    if (!window) {
        write_report(&report);
        SDL_Quit();
        return EXIT_FAILURE;
    }

    SDL_Renderer* renderer = SDL_CreateRenderer(
        window,
        -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!renderer) {
        write_report(&report);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return EXIT_FAILURE;
    }
    report.display_ready = 1;

    SDL_AudioSpec want;
    SDL_AudioSpec have;
    SDL_zero(want);
    SDL_zero(have);
    want.freq = 48000;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    want.callback = audio_silence;
    SDL_AudioDeviceID audio_device =
        SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    if (audio_device != 0) {
        report.audio_ready = 1;
        SDL_PauseAudioDevice(audio_device, 0);
    }

    report.storage_writable = storage_probe();

    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);

    write_report(&report);

    int running = 1;
    while (running && appletMainLoop()) {
        padUpdate(&pad);
        const u64 down = padGetButtonsDown(&pad);
        const u64 held = padGetButtons(&pad);
        const u32 style = padGetStyleSet(&pad);
        report.controller_styles_seen |= style;
        if (style != 0 || held != 0) report.input_seen = 1;
        if (down & HidNpadButton_Plus) running = 0;

        const int operation_mode = (int)appletGetOperationMode();
        if (operation_mode != report.operation_mode) {
            report.operation_mode = operation_mode;
            select_output_size(
                report.operation_mode,
                &report.display_width,
                &report.display_height);
            SDL_SetWindowSize(window, report.display_width, report.display_height);
            write_report(&report);
        }

        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
            case SDL_QUIT:
                running = 0;
                break;
            case SDL_APP_WILLENTERBACKGROUND:
            case SDL_APP_DIDENTERBACKGROUND:
                ++report.background_events;
                write_report(&report);
                break;
            case SDL_APP_WILLENTERFOREGROUND:
            case SDL_APP_DIDENTERFOREGROUND:
                ++report.foreground_events;
                write_report(&report);
                break;
            default:
                break;
            }
        }

        draw_status(renderer, &report);
    }

    if (audio_device != 0) {
        SDL_CloseAudioDevice(audio_device);
    }
    report.clean_exit = 1;
    write_report(&report);

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return EXIT_SUCCESS;
}
