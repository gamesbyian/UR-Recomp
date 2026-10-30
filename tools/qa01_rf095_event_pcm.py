#!/usr/bin/env python3
"""RF095: source-registered, opt-in original/native *actual stereo PCM* capture.

Patch only pinned, disposable Baldosa snesrecomp sources before compiling the
QA01 original/native experiment. The reference WAV is already emitted by
snesref; RF095 adds an exact retro_run-frame -> callback-sample index map.
The native DSP buffers its already-computed post-echo stereo samples and guest
frame boundaries, then flushes them on normal process exit outside the APU lock. No synthesis, input,
clock, register, queue, or guest state is modified. Different clocks and output
pipelines remain explicitly non-equated; RF095 alone cannot admit an event.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REFERENCE = Path('snesrecomp/tools/snesref/frontend.cpp')
NATIVE = Path('snesrecomp/runner/src/snes/dsp.c')
NATIVE_BOUNDARY = Path('snesrecomp/runner/src/common_rtl.c')
REFERENCE_STAMP = 'UR_QA01_RF095_REFERENCE_PCM_FRAME_MAP'
NATIVE_STAMP = 'UR_QA01_RF095_NATIVE_STEREO_PCM'
REF_WAV_INDEX = 'static uint64_t g_wav_sample_frames; // stereo frames written\n'
REF_RUN = '        p_retro_run();\n        g_frame++;\n'
REF_CLOSE = '    wav_close();\n'
NATIVE_ENTRY = 'void dsp_cycle(Dsp* dsp) {\n'
NATIVE_FRAME_ENTRY = 'bool RtlRunFrame(uint32 inputs) {\n'
NATIVE_FRAME_SYNC = ('  if (!g_rtl_speculative_frame)\n'
                     '    rtl_sync_apu_frame_boundary();\n')
NATIVE_SAMPLE = ('  audio_trace_on_sample((int16_t)totalL, (int16_t)totalR, dropped,\n'
                 '                        dropped ? fill : fill + 1);\n')

REF_DECL = r'''/* UR_QA01_RF095_REFERENCE_PCM_FRAME_MAP
 * Map each completed retro_run frame to the exact number of stereo samples
 * already handed to the libretro audio callback. No clock interpolation. */
static FILE *ur_rf095_ref_map;
static bool ur_rf095_ref_map_initialized;
static void ur_rf095_reference_pcm_map_init() {
    if (ur_rf095_ref_map_initialized) return;
    ur_rf095_ref_map_initialized = true;
    const char *path = getenv("SNESREF_PCM_FRAME_MAP");
    if (!path || !path[0]) return;
    ur_rf095_ref_map = fopen(path, "w");
    if (!ur_rf095_ref_map ||
        fprintf(ur_rf095_ref_map, "frame,samples\n0,0\n") < 0) {
        fprintf(stderr, "QA01RF095ORIG_OPEN_FAILED\n");
        if (ur_rf095_ref_map) fclose(ur_rf095_ref_map);
        ur_rf095_ref_map = nullptr;
    }
}
static void ur_rf095_reference_pcm_map_row() {
    if (ur_rf095_ref_map &&
        fprintf(ur_rf095_ref_map, "%u,%llu\n", g_frame,
                (unsigned long long)g_wav_sample_frames) < 0)
        fprintf(stderr, "QA01RF095ORIG_WRITE_FAILED\n");
}
'''

NATIVE_DECL = r'''/* UR_QA01_RF095_NATIVE_STEREO_PCM
 * Buffered post-echo samples; no synchronous file I/O in the DSP/APU lock.
 * At normal process exit, atexit flushes after the lock has been released.
 * An abnormal termination produces no successful receipt. */
extern int snes_frame_counter;
#define UR_RF095_MAX_SAMPLES 8192u
#define UR_RF095_MAX_ROWS 12u
static int16_t ur_rf095_native_buffer[UR_RF095_MAX_SAMPLES][2];
static struct { int frame; unsigned samples; } ur_rf095_native_rows[UR_RF095_MAX_ROWS];
static unsigned ur_rf095_native_samples;
static unsigned ur_rf095_native_row_count;
static int ur_rf095_native_previous_frame = -1;
static int ur_rf095_native_state; /* 0 unopened, 1 collecting, 2 complete, 3 failed */
static void ur_rf095_native_flush(void) {
  if (ur_rf095_native_state != 2 || ur_rf095_native_row_count != 11u ||
      ur_rf095_native_previous_frame != 6457) {
    fprintf(stderr, "QA01RF095NATIVE_INCOMPLETE\n");
    return;
  }
  const char *pcm = getenv("UR_QA01_RF095_NATIVE_PCM");
  const char *map = getenv("UR_QA01_RF095_NATIVE_MAP");
  if (!pcm || !pcm[0] || !map || !map[0]) {
    fprintf(stderr, "QA01RF095NATIVE_OPEN_FAILED\n");
    return;
  }
  FILE *fp = fopen(pcm, "wb");
  FILE *mp = fopen(map, "w");
  if (!fp || !mp) {
    fprintf(stderr, "QA01RF095NATIVE_OPEN_FAILED\n");
    if (fp) fclose(fp);
    if (mp) fclose(mp);
    return;
  }
  int failed = fprintf(mp, "frame,samples\n") < 0;
  for (unsigned i = 0; i < ur_rf095_native_row_count; ++i)
    if (fprintf(mp, "%d,%u\n", ur_rf095_native_rows[i].frame,
                ur_rf095_native_rows[i].samples) < 0) failed = 1;
  if (fwrite(ur_rf095_native_buffer, sizeof(ur_rf095_native_buffer[0]),
             ur_rf095_native_samples, fp) != ur_rf095_native_samples) failed = 1;
  if (fclose(fp) != 0) failed = 1;
  if (fclose(mp) != 0) failed = 1;
  if (failed) fprintf(stderr, "QA01RF095NATIVE_WRITE_FAILED\n");
}
static void ur_rf095_native_stereo_sample(int16_t left, int16_t right) {
  /* The APU may advance during a guest frame AND at its final sync.
   * Sample-time snes_frame_counter is not a completed-frame boundary.
   * Only the explicit post-sync hook below assigns frame/sample rows. */
  if (ur_rf095_native_state != 1) return;
  if (ur_rf095_native_samples >= UR_RF095_MAX_SAMPLES) {
    fprintf(stderr, "QA01RF095NATIVE_TRUNCATED\n");
    ur_rf095_native_state = 3;
    return;
  }
  ur_rf095_native_buffer[ur_rf095_native_samples][0] = left;
  ur_rf095_native_buffer[ur_rf095_native_samples][1] = right;
  ++ur_rf095_native_samples;
}
void ur_rf095_native_frame_boundary(int frame) {
  /* Called only after RtlRunFrame's real guest-frame APU sync, outside
   * RtlApuLock. Frame 6447 is the zero-index boundary; 6457 closes it. */
  if (ur_rf095_native_state >= 2 || frame < 6447) return;
  if (ur_rf095_native_state == 0) {
    const char *pcm = getenv("UR_QA01_RF095_NATIVE_PCM");
    const char *map = getenv("UR_QA01_RF095_NATIVE_MAP");
    if (!pcm || !pcm[0] || !map || !map[0]) {
      ur_rf095_native_state = 3;
      return;
    }
    if (atexit(ur_rf095_native_flush) != 0) {
      fprintf(stderr, "QA01RF095NATIVE_OPEN_FAILED\n");
      ur_rf095_native_state = 3;
      return;
    }
    ur_rf095_native_state = 1;
  }
  if (frame != 6447 + (int)ur_rf095_native_row_count ||
      ur_rf095_native_row_count >= UR_RF095_MAX_ROWS) {
    fprintf(stderr, "QA01RF095NATIVE_FRAME_FAILED\n");
    ur_rf095_native_state = 3;
    return;
  }
  ur_rf095_native_rows[ur_rf095_native_row_count].frame = frame;
  ur_rf095_native_rows[ur_rf095_native_row_count].samples = ur_rf095_native_samples;
  ++ur_rf095_native_row_count;
  ur_rf095_native_previous_frame = frame;
  if (frame == 6457) ur_rf095_native_state = 2;
}
'''


def once(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError('RF095 pinned source drift: ' + name)
    return source.replace(old, new, 1)


def patch_reference(source: str) -> str:
    if REFERENCE_STAMP in source or 'ur_rf095_reference_pcm_map_' in source:
        raise ValueError('RF095 original already/partially patched')
    for anchor in (REF_WAV_INDEX, REF_RUN, REF_CLOSE):
        if source.count(anchor) != 1:
            raise ValueError('RF095 original source drift: ' + anchor[:40])
    source = once(source, REF_WAV_INDEX, REF_WAV_INDEX + REF_DECL,
                  'reference audio callback index')
    source = once(source, REF_RUN,
                  '        ur_rf095_reference_pcm_map_init();\n' +
                  REF_RUN + '        ur_rf095_reference_pcm_map_row();\n',
                  'retro_run boundary')
    source = once(source, REF_CLOSE,
                  REF_CLOSE +
                  '    if (ur_rf095_ref_map) {\n'
                  '        if (fclose(ur_rf095_ref_map) != 0)\n'
                  '            fprintf(stderr, "QA01RF095ORIG_WRITE_FAILED\\n");\n'
                  '        ur_rf095_ref_map = nullptr;\n'
                  '    }\n', 'reference shutdown')
    if source.count('p_retro_run();') != 1 or source.count('wav_close();') != 1:
        raise AssertionError('RF095 changed original run/audio population')
    return source


def patch_native(source: str) -> str:
    if NATIVE_STAMP in source or 'ur_rf095_native_stereo_sample(' in source:
        raise ValueError('RF095 native already/partially patched')
    if source.count(NATIVE_ENTRY) != 1 or source.count(NATIVE_SAMPLE) != 1:
        raise ValueError('RF095 native DSP output anchor drift')
    source = once(source, NATIVE_ENTRY, NATIVE_DECL + '\n' + NATIVE_ENTRY,
                  'native DSP output helper')
    source = once(source, NATIVE_SAMPLE,
                  NATIVE_SAMPLE +
                  '  ur_rf095_native_stereo_sample((int16_t)totalL, (int16_t)totalR);\n',
                  'native post-echo output')
    if source.count('audio_trace_on_sample(') != 1 or source.count('dsp_handleEcho(dsp, &totalL, &totalR);') != 1:
        raise AssertionError('RF095 changed native DSP synthesis population')
    return source


def patch_native_boundary(source: str) -> str:
    """Record completed guest-frame audio boundaries after the actual APU sync."""
    if 'ur_rf095_native_frame_boundary' in source:
        raise ValueError('RF095 native boundary already/partially patched')
    for anchor in (NATIVE_FRAME_ENTRY, NATIVE_FRAME_SYNC):
        if source.count(anchor) != 1:
            raise ValueError('RF095 pinned native frame-boundary source drift')
    source = once(source, NATIVE_FRAME_ENTRY,
                  'extern void ur_rf095_native_frame_boundary(int);\n' +
                  NATIVE_FRAME_ENTRY, 'native real-frame entry')
    source = once(
        source, NATIVE_FRAME_SYNC,
        '  if (!g_rtl_speculative_frame) {\n'
        '    rtl_sync_apu_frame_boundary();\n'
        '    ur_rf095_native_frame_boundary(snes_frame_counter);\n'
        '  }\n',
        'native completed-frame APU sync')
    return source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True,
                        help='Disposable pinned Baldosa snesrecomp parent root')
    parser.add_argument('--side', choices=('original', 'native'), required=True)
    args = parser.parse_args()
    path = args.root / (REFERENCE if args.side == 'original' else NATIVE)
    if not path.is_file() or path.is_symlink():
        parser.error('missing/nonregular/symlinked pinned RF095 source')
    old = path.read_text(encoding='utf-8')
    if args.side == 'original':
        patched = patch_reference(old)
        path.write_text(patched, encoding='utf-8')
    else:
        boundary = args.root / NATIVE_BOUNDARY
        if not boundary.is_file() or boundary.is_symlink():
            parser.error('missing/nonregular/symlinked pinned native frame source')
        old_boundary = boundary.read_text(encoding='utf-8')
        # Validate BOTH pinned anchors before modifying either source file.
        patched = patch_native(old)
        patched_boundary = patch_native_boundary(old_boundary)
        path.write_text(patched, encoding='utf-8')
        boundary.write_text(patched_boundary, encoding='utf-8')
    print('RF095 staged ' + args.side + ' completed-frame-indexed stereo PCM')


if __name__ == '__main__':
    main()
