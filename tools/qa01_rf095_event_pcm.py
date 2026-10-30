#!/usr/bin/env python3
"""RF095: source-registered, opt-in original/native *actual stereo PCM* capture.

Patch only pinned, disposable Baldosa snesrecomp sources before compiling the
QA01 original/native experiment. The reference WAV is already emitted by
snesref; RF095 adds an exact retro_run-frame -> callback-sample index map.
The native DSP emits its already-computed post-echo stereo samples to a bounded
raw file and a guest-frame -> local-sample index map. No synthesis, input,
clock, register, queue, or guest state is modified. Different clocks and output
pipelines remain explicitly non-equated; RF095 alone cannot admit an event.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REFERENCE = Path('snesrecomp/tools/snesref/frontend.cpp')
NATIVE = Path('snesrecomp/runner/src/snes/dsp.c')
REFERENCE_STAMP = 'UR_QA01_RF095_REFERENCE_PCM_FRAME_MAP'
NATIVE_STAMP = 'UR_QA01_RF095_NATIVE_STEREO_PCM'
REF_WAV_INDEX = 'static uint64_t g_wav_sample_frames; // stereo frames written\n'
REF_RUN = '        p_retro_run();\n        g_frame++;\n'
REF_CLOSE = '    wav_close();\n'
NATIVE_ENTRY = 'void dsp_cycle(Dsp* dsp) {\n'
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
 * Actual DSP output after echo/mute, before host playback/ring consumption.
 * Bounded 6447..6456 source-owned guest frames; never infer sample-clock
 * equivalence with the original libretro output callback. The guest frame
 * index is only a registration label, not an SPC or CPU cycle timestamp. */
extern int snes_frame_counter;
static FILE *ur_rf095_native_pcm;
static FILE *ur_rf095_native_map;
static unsigned ur_rf095_native_samples;
static int ur_rf095_native_previous_frame = -1;
static int ur_rf095_native_state; /* 0 unopened, 1 active, 2 closed, 3 failed */
static void ur_rf095_native_close(void) {
  if (ur_rf095_native_pcm) fclose(ur_rf095_native_pcm);
  if (ur_rf095_native_map) fclose(ur_rf095_native_map);
  ur_rf095_native_pcm = NULL;
  ur_rf095_native_map = NULL;
}
static void ur_rf095_native_stereo_sample(int16_t left, int16_t right) {
  const int frame = snes_frame_counter;
  if (ur_rf095_native_state >= 2) return;
  if (frame < 6447) return;
  if (frame > 6456) {
    if (ur_rf095_native_state == 1) {
      if (fprintf(ur_rf095_native_map, "%d,%u\n", frame,
                  ur_rf095_native_samples) < 0)
        fprintf(stderr, "QA01RF095NATIVE_WRITE_FAILED\n");
      ur_rf095_native_close();
      ur_rf095_native_state = 2;
    }
    return;
  }
  if (ur_rf095_native_state == 0) {
    const char *pcm = getenv("UR_QA01_RF095_NATIVE_PCM");
    const char *map = getenv("UR_QA01_RF095_NATIVE_MAP");
    if (!pcm || !pcm[0] || !map || !map[0]) {
      ur_rf095_native_state = 3; /* observer not enabled */
      return;
    }
    ur_rf095_native_pcm = fopen(pcm, "wb");
    ur_rf095_native_map = fopen(map, "w");
    if (!ur_rf095_native_pcm || !ur_rf095_native_map ||
        fprintf(ur_rf095_native_map, "frame,samples\n") < 0) {
      fprintf(stderr, "QA01RF095NATIVE_OPEN_FAILED\n");
      ur_rf095_native_close();
      ur_rf095_native_state = 3;
      return;
    }
    ur_rf095_native_state = 1;
  }
  if (frame != ur_rf095_native_previous_frame) {
    if (frame < ur_rf095_native_previous_frame ||
        fprintf(ur_rf095_native_map, "%d,%u\n", frame,
                ur_rf095_native_samples) < 0) {
      fprintf(stderr, "QA01RF095NATIVE_FRAME_FAILED\n");
      ur_rf095_native_close();
      ur_rf095_native_state = 3;
      return;
    }
    ur_rf095_native_previous_frame = frame;
  }
  if (ur_rf095_native_samples >= 8192u) {
    fprintf(stderr, "QA01RF095NATIVE_TRUNCATED\n");
    ur_rf095_native_close();
    ur_rf095_native_state = 3;
    return;
  }
  const int16_t stereo[2] = {left, right};
  if (fwrite(stereo, sizeof(stereo), 1, ur_rf095_native_pcm) != 1) {
    fprintf(stderr, "QA01RF095NATIVE_WRITE_FAILED\n");
    ur_rf095_native_close();
    ur_rf095_native_state = 3;
    return;
  }
  ++ur_rf095_native_samples;
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
    patched = patch_reference(old) if args.side == 'original' else patch_native(old)
    path.write_text(patched, encoding='utf-8')
    print('RF095 staged ' + args.side + ' frame-indexed actual stereo PCM')


if __name__ == '__main__':
    main()
