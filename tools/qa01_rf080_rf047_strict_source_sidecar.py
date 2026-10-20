#!/usr/bin/env python3
"""RF080: isolate genuine native RF047 source ordinals from mixed stderr.

The existing recorder emits each native line with a single write(2) syscall,
but other stderr producer fragments can prepend bytes to the same line. Stage
an ADDITIONAL separately opened source-only file descriptor, never rewrite
raw stderr, recover missing events, or loosen the RF076/RF079 validators.
"""
from __future__ import annotations
import argparse
from pathlib import Path

SRC=Path('snesrecomp/runner/src/beam_frame_driver.c')
STAMP='UR_QA01_RF080_RF047_STRICT_SIDECAR'
HEADER='#include <stdbool.h>\n'
EMIT='static void ur_rf047_emit(const char *fmt, ...) {\n'
TAIL='  (void)write(2, line, (size_t)n);\n}\n'
PATCH=r'''/* UR_QA01_RF080_RF047_STRICT_SIDECAR: isolated native sequence stream.
 * Never replaces or sanitizes the actual guest stderr log. */
static int ur_rf080_event_fd=-2;
static void ur_rf080_source_event_write(const char *data, size_t count) {
    if (ur_rf080_event_fd==-2) {
        const char *path=getenv("UR_QA01_RF047_EVENT_SIDECAR");
        ur_rf080_event_fd=-1;
        if (path && *path) {
            ur_rf080_event_fd=open(path,O_CREAT|O_TRUNC|O_WRONLY|O_CLOEXEC,0600);
            if (ur_rf080_event_fd<0) {
                static const char msg[]="QA01RF080_SIDECAR_OPEN_FAILED\n";
                (void)write(2,msg,sizeof msg-1);
                abort();
            }
        }
    }
    if (ur_rf080_event_fd>=0) {
        ssize_t saved=write(ur_rf080_event_fd,data,count);
        if (saved<0 || (size_t)saved!=count) {
            static const char msg[]="QA01RF080_SIDECAR_WRITE_FAILED\n";
            (void)write(2,msg,sizeof msg-1);
            abort();
        }
    }
}
'''

def patch(source:str)->str:
    if STAMP in source:
        raise ValueError('RF080 sidecar already or partially staged')
    if ('UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN' not in source or
        'UR_QA01_RF076_FINITE_RECORDER_CAP_131072' not in source or
        'UR_QA01_RF079_NATIVE_POST_BIT_BRANCH' not in source):
        raise ValueError('RF080 requires real staged RF047/RF076/RF079 native guest recorder')
    for token in (HEADER,EMIT,TAIL):
        if source.count(token)!=1:
            raise ValueError('RF080 exact source recorder layout changed')
    original_write_count=source.count('write(2, line, (size_t)n);')
    original_emit_count=source.count('ur_rf047_emit(')
    res=source.replace(HEADER,HEADER+'#include <fcntl.h>\n#include <stdlib.h>\n',1)
    res=res.replace(EMIT,PATCH+EMIT,1)
    res=res.replace(TAIL,'  ur_rf080_source_event_write(line,(size_t)n);\n'+TAIL,1)
    if (res.count(STAMP)!=1 or
        res.count('ur_rf080_source_event_write(')!=2 or
        res.count('write(2, line, (size_t)n);')!=original_write_count or
        res.count('ur_rf047_emit(')!=original_emit_count):
        raise AssertionError('RF080 genuine stderr event writer altered or duplicated')
    return res

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    a=parser.parse_args()
    file=a.root.resolve()/SRC
    if not file.is_file():
        parser.error('pinned Baldosa beam_frame_driver.c missing')
    file.write_text(patch(file.read_text()),encoding='utf-8')
    print('RF080 native source-only sidecar staged, raw stderr unchanged')

if __name__=='__main__':
    main()
