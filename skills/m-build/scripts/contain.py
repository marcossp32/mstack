#!/usr/bin/env python3
"""Run a command so nothing it starts outlives it.

  contain.py [--timeout <s>] [--cpu <percent>] -- <program> [args...]
  contain.py [--timeout <s>] [--cpu <percent>] --shell "<command line>"
      Runs the command and exits with its exit code. When it exits, times out,
      or this process dies for any reason (killed, its parent gone), every
      process the command started dies too: servers, test workers, browsers.
      Timeout: exit 124 and a `contain: TIMEOUT` line on stderr. Only for a
      call whose cut costs no verdict: a suite or a check cut short reads as a
      failure it never had.
  contain.py sweep [--kill]
      Lists automation browsers whose parent is gone (debugging port or pipe,
      throwaway profile or headless), and with --kill ends their trees. A
      browser a live process still owns is never touched.

Windows: this process joins a kill-on-close job object before it starts the
command, so every descendant is in the job and the OS ends them all when the
job's last handle closes, which happens when this process dies, however it
dies. The job also runs them at below-normal priority, so the machine stays
responsive. POSIX: the command runs in its own session, killed on every exit
this process can catch; a SIGKILL of this process cannot be caught there, and
`sweep` covers what it leaves.

Env: MSTACK_CPU_CAP=<percent> caps the whole tree's share of the machine's CPU
(Windows; off by default: a hard cap throttles in bursts and makes timing tests
flaky). MSTACK_PRIORITY=normal keeps normal priority.

Identical copies live in m-build, m-prove and m-review scripts/, so each skill
installs on its own. Change all three.
"""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time

WINDOWS = os.name == "nt"
TIMEOUT_RC = 124
PARENT_GONE_RC = 125

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def note(msg):
    # The reader may be gone (its parent was killed): a note must never stop
    # the tree from ending.
    try:
        print(f"contain: {msg}", file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass


# --- Windows job object -------------------------------------------------------

if WINDOWS:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class _Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _Io(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _Basic), ("IoInfo", _Io),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _CpuRate(ctypes.Structure):
        _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]

    class _Accounting(ctypes.Structure):
        _fields_ = [("TotalUserTime", ctypes.c_int64),
                    ("TotalKernelTime", ctypes.c_int64),
                    ("ThisPeriodTotalUserTime", ctypes.c_int64),
                    ("ThisPeriodTotalKernelTime", ctypes.c_int64),
                    ("TotalPageFaultCount", wintypes.DWORD),
                    ("TotalProcesses", wintypes.DWORD),
                    ("ActiveProcesses", wintypes.DWORD),
                    ("TotalTerminatedProcesses", wintypes.DWORD)]

    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                             ctypes.c_void_p, wintypes.DWORD]
    _k32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD,
                                               ctypes.c_void_p]
    _k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.GetCurrentProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]

    _KILL_ON_JOB_CLOSE = 0x2000
    _LIMIT_PRIORITY_CLASS = 0x20
    _BELOW_NORMAL = 0x4000
    _EXTENDED_LIMITS, _CPU_RATE, _ACCOUNTING = 9, 15, 1
    _CPU_ENABLE, _CPU_HARD_CAP = 0x1, 0x4
    _SYNCHRONIZE = 0x00100000
    _CREATE_NEW_PROCESS_GROUP = 0x200

    def _job(cpu, low_priority):
        """A kill-on-close job holding this process, or None if Windows refuses."""
        job = _k32.CreateJobObjectW(None, None)  # handle not inheritable
        if not job:
            return None
        info = _Extended()
        info.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
        if low_priority:
            info.BasicLimitInformation.LimitFlags |= _LIMIT_PRIORITY_CLASS
            info.BasicLimitInformation.PriorityClass = _BELOW_NORMAL
        if not _k32.SetInformationJobObject(job, _EXTENDED_LIMITS,
                                            ctypes.byref(info), ctypes.sizeof(info)):
            return None
        if cpu:
            rate = _CpuRate(_CPU_ENABLE | _CPU_HARD_CAP,
                            max(1, min(10000, int(cpu * 100))))
            if not _k32.SetInformationJobObject(job, _CPU_RATE, ctypes.byref(rate),
                                                ctypes.sizeof(rate)):
                note(f"CPU cap not applied (error {ctypes.get_last_error()})")
        # Joined before the command starts, so no descendant can start outside.
        if not _k32.AssignProcessToJobObject(job, _k32.GetCurrentProcess()):
            return None
        return job

    def _active(job):
        acc = _Accounting()
        if _k32.QueryInformationJobObject(job, _ACCOUNTING, ctypes.byref(acc),
                                          ctypes.sizeof(acc), None):
            return acc.ActiveProcesses
        return 0

    def _watch_parent(on_gone):
        handle = _k32.OpenProcess(_SYNCHRONIZE, False, os.getppid())
        if not handle:
            return  # cannot watch; the job still ends the tree with this process

        def wait():
            _k32.WaitForSingleObject(handle, 0xFFFFFFFF)
            on_gone()
        threading.Thread(target=wait, daemon=True).start()


def run(argv, shell, timeout, cpu):
    low = os.environ.get("MSTACK_PRIORITY", "").lower() != "normal"
    cpu = cpu or float(os.environ.get("MSTACK_CPU_CAP") or 0) or None
    job = None
    if WINDOWS:
        job = _job(cpu, low)
        if job is None:
            note(f"no job object (error {ctypes.get_last_error()}): "
                 "running uncontained")

    def end(rc):
        """End the whole tree, this process included, with this exit code."""
        if job is not None:
            _k32.TerminateJobObject(job, rc)
        elif not WINDOWS and child is not None:
            _killpg(child.pid)
        os._exit(rc)

    child = None
    kwargs = {}
    if WINDOWS:
        # Its own process group: a driver can send it Ctrl+Break alone.
        kwargs["creationflags"] = _CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda s, _f: end(128 + s))
    child = subprocess.Popen(argv, shell=shell, **kwargs)
    note(f"pid {child.pid}{' · job' if job is not None else ''}"
         f"{f' · timeout {timeout:g}s' if timeout else ''}")

    def parent_gone():
        try:
            note("parent exited: ending the tree")
        finally:
            end(PARENT_GONE_RC)
    if WINDOWS:
        _watch_parent(parent_gone)
    else:
        ppid = os.getppid()

        def poll():
            while os.getppid() == ppid:
                time.sleep(1)
            parent_gone()
        threading.Thread(target=poll, daemon=True).start()

    try:
        rc = child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        note(f"TIMEOUT after {timeout:g}s: ending the tree")
        end(TIMEOUT_RC)
    except KeyboardInterrupt:
        end(130)
    if job is not None:
        left = _active(job) - 1  # this process is in the job too
        if left > 0:
            note(f"ending {left} process(es) the command left running")
    elif not WINDOWS:
        _killpg(child.pid)
    try:
        sys.stdout.flush()
    except (OSError, ValueError):
        pass
    end(rc)


def _killpg(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


# --- sweep ------------------------------------------------------------------

# A browser started for automation: a debugging port or pipe (Chromium, and
# Firefox through Marionette or Juggler, WebKit through its inspector pipe).
AUTOMATION = re.compile(r"--remote-debugging-(port|pipe)|(^|\s)-?-marionette\b"
                        r"|-juggler(-pipe)?\b|--inspector-pipe")
# Child processes of a browser end with it: only the browser process counts.
SUBPROCESS = re.compile(r"\s--type=")
PROFILE = re.compile(r"(--user-data-dir|-profile)[= ]\"?([^\"]+?)\"?(\s--?\w|\s*$)")


def _throwaway(cmd):
    """A headless browser, or one whose profile lives in the temp dir."""
    if re.search(r"--headless\b|(^|\s)-headless\b", cmd):
        return True
    m = PROFILE.search(cmd)
    if not m:
        return False
    tmp = os.path.normcase(os.path.realpath(tempfile.gettempdir()))
    prof = os.path.normcase(os.path.realpath(m.group(2).strip()))
    return prof.startswith(tmp)


def _processes():
    """[(pid, ppid, started, command line)] for every process we can see."""
    if WINDOWS:
        ps = ("Get-CimInstance Win32_Process | Select-Object ProcessId,"
              "ParentProcessId,@{n='Started';e={$_.CreationDate.ToFileTimeUtc()}},"
              "CommandLine | ConvertTo-Json -Compress")
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        rows = json.loads(p.stdout or "[]")
        rows = rows if isinstance(rows, list) else [rows]
        return [(r["ProcessId"], r["ParentProcessId"], r.get("Started") or 0,
                 r.get("CommandLine") or "") for r in rows]
    p = subprocess.run(["ps", "-eo", "pid=,ppid=,etimes=,args="],
                       capture_output=True, text=True, timeout=60)
    out = []
    for line in p.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[2].isdigit():
            out.append((int(parts[0]), int(parts[1]), -int(parts[2]), parts[3]))
    return out


def sweep(kill):
    procs = _processes()
    by_pid = {pid: (ppid, started, cmd) for pid, ppid, started, cmd in procs}
    orphans = []
    for pid, ppid, started, cmd in procs:
        if not AUTOMATION.search(cmd) or SUBPROCESS.search(cmd) or not _throwaway(cmd):
            continue
        parent = by_pid.get(ppid)
        if WINDOWS:
            # A parent id Windows has reused belongs to a newer process.
            alive = parent is not None and parent[1] <= started
        else:
            alive = ppid > 1 and parent is not None and not re.match(
                r"(/\S*/)?(systemd|launchd|init)\b", parent[2])
        if not alive:
            orphans.append((pid, cmd))
    for pid, cmd in orphans:
        print(f"orphan {pid} · {cmd[:160]}")
        if kill:
            if WINDOWS:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)],
                               capture_output=True)
            else:
                try:
                    os.kill(pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
    verb = "ended" if kill else "found"
    print(f"SWEEP: {verb} {len(orphans)} orphaned automation browser(s)")


def main():
    args = sys.argv[1:]
    if args[:1] == ["sweep"]:
        if args[1:] not in ([], ["--kill"]):
            sys.exit(__doc__)
        sweep("--kill" in args)
        return
    timeout = cpu = None
    shell = False
    while args and args[0] != "--":
        flag = args.pop(0)
        if flag in ("--timeout", "--cpu", "--shell") and args:
            value = args.pop(0)
            if flag == "--timeout":
                timeout = float(value)
            elif flag == "--cpu":
                cpu = float(value)
            else:
                shell, args = True, [value] + args
                break
        else:
            sys.exit(__doc__)
    if args[:1] == ["--"]:
        args = args[1:]
    if not args or (shell and len(args) != 1):
        sys.exit(__doc__)
    run(args[0] if shell else args, shell, timeout, cpu)


if __name__ == "__main__":
    main()
