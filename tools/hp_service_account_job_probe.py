#!/usr/bin/env python3
"""Bounded, dependency-free Windows service identity / atomic Job List probe.

Only a short sleeping child is allowed. No arbitrary job submission or service edits.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import sys

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
PROC_THREAD_ATTRIBUTE_JOB_LIST = 0x0002000D
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_NO_WINDOW = 0x08000000
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x102


class BasicLimit(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BasicLimit), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE)]


class StartupInfoEx(ctypes.Structure):
    _fields_ = [("StartupInfo", StartupInfo), ("lpAttributeList", ctypes.c_void_p)]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def signature(k, name, args, result):
    method = getattr(k, name)
    method.argtypes = args
    method.restype = result
    return method


def check(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def native_probe():
    if os.name != "nt":
        raise OSError("Windows-only probe")
    if ctypes.sizeof(ctypes.c_void_p) != 8 or ctypes.sizeof(StartupInfoEx) != 112:
        raise RuntimeError("unexpected Win64 ABI")
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    p = ctypes.c_void_p
    create_job = signature(k, "CreateJobObjectW", [p, wintypes.LPCWSTR], wintypes.HANDLE)
    set_job = signature(k, "SetInformationJobObject",
                        [wintypes.HANDLE, ctypes.c_int, p, wintypes.DWORD], wintypes.BOOL)
    init = signature(k, "InitializeProcThreadAttributeList",
                     [p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t)], wintypes.BOOL)
    update = signature(k, "UpdateProcThreadAttribute",
                       [p, wintypes.DWORD, ctypes.c_size_t, p, ctypes.c_size_t, p, p], wintypes.BOOL)
    delete = signature(k, "DeleteProcThreadAttributeList", [p], None)
    create = signature(k, "CreateProcessW",
                       [wintypes.LPCWSTR, wintypes.LPWSTR, p, p, wintypes.BOOL,
                        wintypes.DWORD, p, wintypes.LPCWSTR, p,
                        ctypes.POINTER(ProcessInfo)], wintypes.BOOL)
    wait = signature(k, "WaitForSingleObject", [wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD)
    close = signature(k, "CloseHandle", [wintypes.HANDLE], wintypes.BOOL)
    terminate = signature(k, "TerminateProcess", [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL)
    inside = signature(k, "IsProcessInJob",
                       [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL)
    current = signature(k, "GetCurrentProcess", [], wintypes.HANDLE)
    nested = wintypes.BOOL()
    check(inside(current(), None, ctypes.byref(nested)))
    job = check(create_job(None, None))
    pi = ProcessInfo()
    buf = None
    initialized = False
    try:
        limits = ExtendedLimit()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        check(set_job(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        size = ctypes.c_size_t()
        init(None, 1, 0, ctypes.byref(size))
        if size.value <= 0 or size.value > 65536:
            raise RuntimeError("invalid attribute-list size")
        buf = ctypes.create_string_buffer(size.value)
        check(init(buf, 1, 0, ctypes.byref(size)))
        initialized = True
        handles = (wintypes.HANDLE * 1)(job)
        check(update(buf, 0, PROC_THREAD_ATTRIBUTE_JOB_LIST,
                     handles, ctypes.sizeof(handles), None, None))
        startup = StartupInfoEx()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = ctypes.cast(buf, p)
        exe = sys.executable
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline(
            [exe, "-c", "import time; time.sleep(15)"]))
        check(create(exe, command, None, None, False,
                     EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW,
                     None, None, ctypes.byref(startup), ctypes.byref(pi)))
        if wait(pi.hProcess, 0) != WAIT_TIMEOUT:
            raise RuntimeError("contained process exited prematurely")
        check(close(job))
        job = None
        if wait(pi.hProcess, 5000) != WAIT_OBJECT_0:
            raise RuntimeError("job close did not terminate child")
        return {"atomic_job_list": "pass", "kill_on_close": "pass",
                "runner_already_in_job": bool(nested.value),
                "pointer_bits": ctypes.sizeof(p) * 8}
    finally:
        if job:
            close(job)
        if pi.hProcess:
            if wait(pi.hProcess, 0) == WAIT_TIMEOUT:
                terminate(pi.hProcess, 1)
                wait(pi.hProcess, 5000)
            close(pi.hProcess)
        if pi.hThread:
            close(pi.hThread)
        if initialized:
            delete(buf)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-network-service", action="store_true")
    args = parser.parse_args()
    identity = subprocess.check_output(["whoami"], text=True, timeout=8).strip().lower()
    if args.require_network_service and identity != r"nt authority\network service":
        raise RuntimeError("runner job identity differs from expected NETWORK SERVICE: " + identity)
    result = {"identity": identity, **native_probe()}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
