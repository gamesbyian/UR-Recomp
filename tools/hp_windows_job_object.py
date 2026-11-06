#!/usr/bin/env python3
"""Windows suspended-launch Job Object containment, experimental and opt-in.

Creates the process suspended, assigns it to a kill-on-close Windows Job Object,
then resumes its primary thread. No globally installed hooks or services.
This is a low-level primitive; do not interpret it as GHA resource arbitration.
"""
import contextlib
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import time

CREATE_SUSPENDED = 0x00000004
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class BasicLimit(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IoCounters(ctypes.Structure):
    _fields_ = [(field, ctypes.c_uint64) for field in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", BasicLimit),
        ("IoInfo", IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class ThreadEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


def kernel():
    if os.name != "nt":
        raise OSError("Windows Job Object support requires Windows")
    dll = ctypes.WinDLL("kernel32", use_last_error=True)
    dll.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    dll.CreateJobObjectW.restype = wintypes.HANDLE
    dll.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                         ctypes.c_void_p, wintypes.DWORD]
    dll.SetInformationJobObject.restype = wintypes.BOOL
    dll.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    dll.AssignProcessToJobObject.restype = wintypes.BOOL
    dll.CloseHandle.argtypes = [wintypes.HANDLE]
    dll.CloseHandle.restype = wintypes.BOOL
    dll.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    dll.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    dll.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
    dll.Thread32First.restype = wintypes.BOOL
    dll.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
    dll.Thread32Next.restype = wintypes.BOOL
    dll.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    dll.OpenThread.restype = wintypes.HANDLE
    dll.ResumeThread.argtypes = [wintypes.HANDLE]
    dll.ResumeThread.restype = wintypes.DWORD
    return dll


def checked(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def new_job(k):
    handle = checked(k.CreateJobObjectW(None, None))
    try:
        info = ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        checked(k.SetInformationJobObject(handle, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                          ctypes.byref(info), ctypes.sizeof(info)))
        return handle
    except BaseException:
        k.CloseHandle(handle)
        raise


def resume_initial_thread(k, pid):
    """Only call before resuming: CREATE_SUSPENDED guarantees no child execution."""
    for _ in range(20):
        snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
        if snap == INVALID_HANDLE_VALUE:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ThreadEntry()
            entry.dwSize = ctypes.sizeof(entry)
            found = k.Thread32First(snap, ctypes.byref(entry))
            while found:
                if entry.th32OwnerProcessID == pid:
                    thread = checked(k.OpenThread(THREAD_SUSPEND_RESUME, False,
                                                  entry.th32ThreadID))
                    try:
                        if k.ResumeThread(thread) == 0xFFFFFFFF:
                            raise ctypes.WinError(ctypes.get_last_error())
                        return
                    finally:
                        k.CloseHandle(thread)
                found = k.Thread32Next(snap, ctypes.byref(entry))
        finally:
            k.CloseHandle(snap)
        time.sleep(0.05)
    raise RuntimeError("no suspended main thread found; process remains unresumed")


class ContainedProcess:
    """Context manager. Closing the job forcibly terminates all its descendants."""

    def __init__(self, command, **kwargs):
        if not isinstance(command, (list, tuple)) or not command:
            raise ValueError("pass an explicit executable argument vector")
        self.k = kernel()
        self.job = new_job(self.k)
        self.process = None
        try:
            self.process = subprocess.Popen(
                command, creationflags=CREATE_SUSPENDED, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
            checked(self.k.AssignProcessToJobObject(
                self.job, wintypes.HANDLE(int(self.process._handle))))
            resume_initial_thread(self.k, self.process.pid)
        except BaseException:
            self.close()
            raise

    def close(self):
        job, self.job = self.job, None
        if job is not None:
            self.k.CloseHandle(job)
        if self.process is not None:
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=5)
            for stream in (self.process.stdout, self.process.stderr):
                if stream is not None:
                    stream.close()

    def __enter__(self):
        return self.process

    def __exit__(self, exc_type, exc, tb):
        self.close()


if __name__ == "__main__":
    raise SystemExit("Import as a library; no arbitrary-command CLI is provided.")
