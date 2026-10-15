#!/usr/bin/env python3
"""Run a command so nothing it starts outlives it.

  contain.py [options] -- <program> [args...]
  contain.py [options] --shell "<command line>"
      Runs the command and exits with its exit code. When it exits or is
      stopped, every process it started ends too: servers, test workers,
      browsers. The first stderr line, `contain: pid <n>`, is the pid to give
      `stop`. On Windows it is often a launcher, not the program: cmd.exe for
      npm and other .cmd shims, the app-execution alias for python. `stop`
      reaches the whole process group, so that is enough; never use it to
      find or kill the program itself.
      Exit 123 with `contain: REAPED` means another run's `sweep --within`
      ended the tree: not a result of the command.
      --env KEY=VALUE  sets a variable for the command (repeatable), so no
                       shell syntax is needed; `--shell` is cmd.exe on Windows.
      --with-parent    also ends the tree when the process that started this
                       one exits. For scripts; never for a server started in
                       the background, whose launching shell exits at once.
      --timeout <s>    a ceiling: ends the tree, exits 124 and prints
                       `contain: TIMEOUT`. Only where the caller reports a cut
                       run as not finished, never as a failure.
  contain.py stop <pid>
      Asks a contained command to shut down, by the pid it printed: Ctrl+Break
      to its process group on Windows (Node sees SIGBREAK), SIGTERM on POSIX.
      What the command leaves running gets up to 5 s to finish shutting down
      before it is ended.
  contain.py sweep [--kill] [--within <dir>]...
      Lists, and with --kill ends: contained trees whose owner is gone;
      with --within, every contained tree started in that directory, except
      in another git worktree nested inside it; and automation browsers (a
      debugging port or pipe, and a profile named for an automation tool, or
      headless on a profile in the temp dir) whose parent is gone. A browser
      a live process still owns, and a browser without those signs, is never
      touched.

Windows: this process joins a kill-on-close job object before it starts the
command, so every descendant is in the job and the OS ends them all when this
process dies, however it dies. A program may still leave the job by asking to
(CREATE_BREAKAWAY_FROM_JOB). POSIX: the command gets its own session; ending
it sends SIGTERM, waits, then SIGKILL, so a test runner can close the browsers
it started in sessions of their own. A watchdog process ends the session if
this process is SIGKILLed.

Every command gets BROWSER=none and PW_TEST_HTML_REPORT_OPEN=never unless set:
dev servers and test reports otherwise open the user's default browser.
MSTACK_PRIORITY=low runs the tree at below-normal priority (off by default:
under load it makes timing tests flaky).

Identical copies live in m-build, m-prove and m-review scripts/, so each skill
installs on its own. Change all three; CI checks that they match.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

WINDOWS = os.name == "nt"
TIMEOUT_RC = 124
PARENT_GONE_RC = 125
REAPED_RC = 123    # ended by another run's sweep, printed as `contain: REAPED`
GRACE = 5          # seconds a stopped tree gets before it is killed
STALE = 24 * 3600  # a registry entry older than this is only deleted
REGISTRY = os.path.join(tempfile.gettempdir(), "mstack-contain")
DEFAULT_ENV = {"BROWSER": "none", "PW_TEST_HTML_REPORT_OPEN": "never"}

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


# --- Windows ---------------------------------------------------------------

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
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.GetCurrentProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_uint64)] * 4
    _k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.AttachConsole.argtypes = [wintypes.DWORD]
    _k32.SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, wintypes.BOOL]
    _k32.GenerateConsoleCtrlEvent.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.CreateEventW.restype = wintypes.HANDLE
    _k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL,
                                  wintypes.LPCWSTR]
    _k32.OpenEventW.restype = wintypes.HANDLE
    _k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    _k32.SetEvent.argtypes = [wintypes.HANDLE]

    _KILL_ON_JOB_CLOSE = 0x2000
    _BREAKAWAY_OK = 0x800
    _LIMIT_PRIORITY_CLASS = 0x20
    _BELOW_NORMAL = 0x4000
    _EXTENDED_LIMITS, _ACCOUNTING = 9, 1
    _SYNCHRONIZE = 0x00100000
    _QUERY_LIMITED = 0x1000
    _TERMINATE = 0x0001
    _STILL_ACTIVE = 259
    _CREATE_NEW_PROCESS_GROUP = 0x200
    _CTRL_BREAK = 1
    _CTRL_EXIT = 0xC000013A  # STATUS_CONTROL_C_EXIT: ended by Ctrl+C/Break
    _EVENT_MODIFY = 0x0002

    def _reap_event(pid):
        return f"Local\\mstack-contain-reap-{pid}"

    def _job(low_priority):
        """A kill-on-close job holding this process, or None if Windows refuses."""
        job = _k32.CreateJobObjectW(None, None)  # handle not inheritable
        if not job:
            return None
        info = _Extended()
        # A program that asks to leave the job may: refusing it makes the
        # program fail inside the job and nowhere else.
        info.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE | _BREAKAWAY_OK
        if low_priority:
            info.BasicLimitInformation.LimitFlags |= _LIMIT_PRIORITY_CLASS
            info.BasicLimitInformation.PriorityClass = _BELOW_NORMAL
        # Joined before the command starts, so no descendant can start outside.
        if not (_k32.SetInformationJobObject(job, _EXTENDED_LIMITS, ctypes.byref(info),
                                             ctypes.sizeof(info))
                and _k32.AssignProcessToJobObject(job, _k32.GetCurrentProcess())):
            _k32.CloseHandle(job)
            return None
        return job

    def _active(job):
        acc = _Accounting()
        if _k32.QueryInformationJobObject(job, _ACCOUNTING, ctypes.byref(acc),
                                          ctypes.sizeof(acc), None):
            return acc.ActiveProcesses
        return 0

    def _started(handle):
        times = [ctypes.c_uint64() for _ in range(4)]
        if _k32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            return times[0].value
        return 0

    def _alive(pid, started):
        h = _k32.OpenProcess(_QUERY_LIMITED, False, pid)
        if not h:
            return False
        try:
            code = wintypes.DWORD()
            if not _k32.GetExitCodeProcess(h, ctypes.byref(code)):
                return False
            return code.value == _STILL_ACTIVE and (not started or _started(h) == started)
        finally:
            _k32.CloseHandle(h)

    def _self_started():
        return _started(_k32.GetCurrentProcess())

    def _end_wrapper(pid):
        """Asks a live wrapper to end its tree as reaped, so its caller sees
        REAPED_RC and a `contain: REAPED` line; kills it if it cannot."""
        h = _k32.OpenProcess(_TERMINATE | _SYNCHRONIZE, False, pid)
        ev = _k32.OpenEventW(_EVENT_MODIFY, False, _reap_event(pid))
        if ev:
            _k32.SetEvent(ev)
            _k32.CloseHandle(ev)
        if h:
            if not ev or _k32.WaitForSingleObject(h, GRACE * 1000) != 0:
                _k32.TerminateProcess(h, REAPED_RC)
            _k32.CloseHandle(h)


else:
    def _ps_started(pid):
        p = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                           capture_output=True, text=True)
        return p.stdout.strip()

    def _alive(pid, started):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            pass
        return not started or _ps_started(pid) == started

    def _self_started():
        return _ps_started(os.getpid())

    def _group_alive(pgid):
        try:
            os.killpg(pgid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def _end_group(pgid):
        """SIGTERM, a grace period, then SIGKILL: a runner's own handlers get
        to close the browsers it started outside its group."""
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return
        deadline = time.monotonic() + GRACE
        while time.monotonic() < deadline and _group_alive(pgid):
            time.sleep(0.1)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    def _watchdog(pgid):
        """A process in its own session that ends the command's session when
        this process dies, SIGKILL included: it holds a pipe only we write to."""
        r, w = os.pipe()
        if os.fork() == 0:
            try:
                os.setsid()
                os.close(w)
                # Never hold the caller's output pipes open.
                null = os.open(os.devnull, os.O_RDWR)
                for fd in (0, 1, 2):
                    os.dup2(null, fd)
                while os.read(r, 1):
                    pass
                _end_group(pgid)
            finally:
                os._exit(0)
        os.close(r)
        return w  # kept open for this process's whole life


# --- registry ----------------------------------------------------------------

def _register(child_pid, cmd):
    """One file per live contained tree, so `sweep` can find what an agent
    left running or a crash left behind."""
    try:
        os.makedirs(REGISTRY, exist_ok=True)
        path = os.path.join(REGISTRY, f"{os.getpid()}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"wrapper": os.getpid(), "started": _self_started(),
                       "child": child_pid, "cwd": os.getcwd(), "cmd": cmd,
                       "at": time.time()}, fh)
        return path
    except OSError:
        return None


def _stop_marker(child_pid):
    """Left by `stop`, so the wrapper knows its command was asked to stop."""
    return os.path.join(REGISTRY, f"stop-{child_pid}")


def _unregister(path):
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


# --- run ---------------------------------------------------------------------

def run(argv, shell, timeout, with_parent, extra_env):
    low = os.environ.get("MSTACK_PRIORITY", "").lower() == "low"
    ppid = os.getppid()  # before anything else: the parent may die meanwhile
    env = {**DEFAULT_ENV, **os.environ, **extra_env}
    job = None
    if WINDOWS:
        job = _job(low)
        if job is None:
            note(f"WARNING · no job object (error {ctypes.get_last_error()}): a stop "
                 "ends only what taskkill /T still finds")
        if not shell:
            found = shutil.which(argv[0])  # npm, npx: .cmd files on Windows
            if found:
                argv = [found] + argv[1:]

    child = None
    reg = None

    def end(rc):
        """End the whole tree, this process included, with this exit code."""
        _unregister(reg)
        if child is not None:
            _unregister(_stop_marker(child.pid))
        if WINDOWS:
            if job is not None:
                _k32.TerminateJobObject(job, rc)
            elif child is not None:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                               capture_output=True)
        elif child is not None:
            _end_group(child.pid)
        os._exit(rc)

    kwargs = {"env": env}
    if WINDOWS:
        # Its own process group, so `stop` can send it Ctrl+Break alone.
        kwargs["creationflags"] = _CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
        if low:
            kwargs["preexec_fn"] = lambda: os.nice(10)
    try:
        child = subprocess.Popen(argv, shell=shell, **kwargs)
    except OSError as e:
        note(f"cannot start {argv if not shell else argv!r}: {e}")
        end(127)
    keep = _watchdog(child.pid) if not WINDOWS else None  # noqa: F841
    reg = _register(child.pid, argv if shell else " ".join(argv))

    def reaped():
        try:
            note("REAPED · another run's sweep ended this tree: not a result "
                 "of the command")
        finally:
            end(REAPED_RC)
    if WINDOWS:
        reap_ev = _k32.CreateEventW(None, True, False, _reap_event(os.getpid()))
        if reap_ev:
            def wait_reap():
                _k32.WaitForSingleObject(reap_ev, 0xFFFFFFFF)
                reaped()
            threading.Thread(target=wait_reap, daemon=True).start()
    else:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda s, _f: end(128 + s))
        signal.signal(signal.SIGUSR1, lambda _s, _f: reaped())
    note(f"pid {child.pid}{' · job' if job is not None else ''}"
         f"{f' · timeout {timeout:g}s' if timeout else ''}")

    if with_parent:
        def parent_gone():
            try:
                note("parent exited: ending the tree")
            finally:
                end(PARENT_GONE_RC)
        if WINDOWS:
            handle = _k32.OpenProcess(_SYNCHRONIZE, False, ppid)
            if not handle:
                parent_gone()

            def wait():
                _k32.WaitForSingleObject(handle, 0xFFFFFFFF)
                parent_gone()
            threading.Thread(target=wait, daemon=True).start()
        else:
            def poll():
                while os.getppid() == ppid and ppid != 1:
                    time.sleep(0.5)
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
        if left > 0 and (rc == _CTRL_EXIT or os.path.exists(_stop_marker(child.pid))):
            # Stopped: Ctrl+Break often ends a launcher (cmd.exe for npm) at
            # once while the program it started is still in its shutdown
            # handler. Give the rest the grace POSIX gives, then end them.
            note(f"stopped: waiting up to {GRACE}s for {left} process(es) to exit")
            deadline = time.monotonic() + GRACE
            while _active(job) > 1 and time.monotonic() < deadline:
                time.sleep(0.1)
            left = _active(job) - 1
        if left > 0:
            note(f"ending {left} process(es) the command left running")
    try:
        sys.stdout.flush()
    except (OSError, ValueError):
        pass
    end(rc if rc >= 0 else 128 - rc)


# --- stop --------------------------------------------------------------------

def stop(pid):
    if not WINDOWS:
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError) as e:
            sys.exit(f"contain: cannot stop {pid}: {e}")
        print(f"STOP: SIGTERM sent to process group {pid}")
        return
    # Ctrl+Break reaches only processes on the sender's console: join the
    # command's console, ignore the event here, send it to its group.
    try:
        with open(_stop_marker(pid), "w"):
            pass
    except OSError:
        pass
    _k32.FreeConsole()
    if not _k32.AttachConsole(pid):
        _unregister(_stop_marker(pid))
        sys.exit(f"contain: cannot attach to the console of {pid} "
                 f"(error {ctypes.get_last_error()})")
    _k32.SetConsoleCtrlHandler(None, True)
    ok = _k32.GenerateConsoleCtrlEvent(_CTRL_BREAK, pid)
    err = ctypes.get_last_error()
    _k32.FreeConsole()
    if not ok:
        _unregister(_stop_marker(pid))
        sys.exit(f"contain: Ctrl+Break to {pid} failed (error {err})")
    print(f"STOP: Ctrl+Break sent to process group {pid}")


# --- sweep -------------------------------------------------------------------

BROWSER_IMAGE = re.compile(r"(^|[\\/])(chrome|chromium|msedge|brave|firefox|"
                           r"headless_shell|chrome-headless-shell|minibrowser|"
                           r"playwright|webkit\w*)(\.exe)?$", re.IGNORECASE)
AUTOMATION = re.compile(r"--remote-debugging-(port|pipe)|(^|\s)-?-marionette\b"
                        r"|-juggler(-pipe)?\b|--inspector-pipe")
SUBPROCESS = re.compile(r"\s\"?--type=")
HEADLESS = re.compile(r"--headless\b|(^|\s)-headless\b")
# Profiles named for the automation tool that made them: Puppeteer, Playwright,
# Lighthouse, agent-browser, chrome-devtools-mcp (the profile's parent dir).
AUTOMATION_PROFILE = re.compile(r"^(puppeteer[_-]|playwright[_-]|lighthouse\.|"
                                r"agent-browser-|chrome-devtools-mcp$|mstack-)",
                                re.IGNORECASE)


def _exe(cmd):
    cmd = cmd.strip()
    if cmd.startswith('"'):
        return cmd[1:].split('"', 1)[0]
    return cmd.split(" ", 1)[0]


def _profile(cmd):
    for key in ("--user-data-dir=", "-profile "):
        i = cmd.find(key)
        if i < 0:
            continue
        rest = cmd[i + len(key):].lstrip()
        if rest.startswith('"'):
            return rest[1:].split('"', 1)[0]
        return re.split(r'"|\s--?\w', rest, maxsplit=1)[0].strip()
    return None


def _throwaway(cmd):
    """A profile named for an automation tool, or a headless browser on a
    profile in the temp dir. Headless alone is not enough: a person's own
    headless Chrome, started by a script that has since exited, is theirs."""
    prof = _profile(cmd)
    if not prof:
        return False
    full = os.path.normcase(os.path.realpath(prof))
    parent, name = os.path.split(full)
    if any(AUTOMATION_PROFILE.match(n) for n in (name, os.path.basename(parent))):
        return True
    if not HEADLESS.search(cmd):
        return False
    tmp = os.path.normcase(os.path.realpath(tempfile.gettempdir()))
    try:
        return os.path.commonpath([tmp, full]) == tmp and full != tmp
    except ValueError:  # different drives
        return False


def _processes():
    """[(pid, ppid, started, command line)], or None if listing failed."""
    if WINDOWS:
        ps = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
              "Get-CimInstance Win32_Process | Select-Object ProcessId,"
              "ParentProcessId,@{n='Started';e={$_.CreationDate.ToFileTimeUtc()}},"
              "CommandLine | ConvertTo-Json -Compress")
        try:
            p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=120)
            rows = json.loads(p.stdout or "null")
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return None
        if rows is None:
            return None
        rows = rows if isinstance(rows, list) else [rows]
        return [(r["ProcessId"], r["ParentProcessId"], r.get("Started") or 0,
                 r.get("CommandLine") or "") for r in rows]
    try:
        p = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,ppid=,command="],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    out = []
    for line in p.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            out.append((int(parts[0]), int(parts[1]), 0, parts[2]))
    return out


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def _under(path, d):
    try:
        return os.path.commonpath([path, d]) == d
    except ValueError:  # different drives
        return False


_WORKTREES = {}


def _worktrees(d):
    """(d's own worktree, every worktree of its repo), or None outside git."""
    if d not in _WORKTREES:
        _WORKTREES[d] = None
        try:
            git = ["git", "-C", d]
            kw = {"capture_output": True, "text": True, "timeout": 30,
                  "stdin": subprocess.DEVNULL}
            top = subprocess.run(git + ["rev-parse", "--show-toplevel"], **kw)
            lst = subprocess.run(git + ["worktree", "list", "--porcelain"], **kw)
            if top.returncode == 0 and lst.returncode == 0 and top.stdout.strip():
                _WORKTREES[d] = (_norm(top.stdout.strip()),
                                 [_norm(line[len("worktree "):])
                                  for line in lst.stdout.splitlines()
                                  if line.startswith("worktree ")])
        except (OSError, subprocess.TimeoutExpired):
            pass
    return _WORKTREES[d]


def _within(path, dirs):
    """Started in one of dirs, and not in another git worktree nested there:
    Claude Code puts parallel runs' worktrees inside the repo they branch
    from, and those runs are alive and not ours to end."""
    p = _norm(path)
    for d in dirs:
        d = _norm(d)
        if not _under(p, d):
            continue
        trees = _worktrees(d)
        if trees:
            own, every = trees
            inner = max((w for w in every if _under(p, w)), key=len, default=own)
            if inner != own:
                continue
        return True
    return False


def _reap(kill, within):
    """Contained trees whose owner is gone, and with --within every tree
    started there: an agent's server left running, a crash's leftovers."""
    ended = 0
    if not os.path.isdir(REGISTRY):
        return ended
    for name in os.listdir(REGISTRY):
        path = os.path.join(REGISTRY, name)
        try:
            with open(path, encoding="utf-8") as fh:
                e = json.load(fh)
        except (OSError, ValueError):
            continue
        live = _alive(e["wrapper"], e.get("started"))
        if live and not (within and _within(e.get("cwd", ""), within)):
            continue
        if not live and (WINDOWS or not _group_alive(e["child"])):
            # Nothing is left to end: the job died with its wrapper (Windows),
            # or the session already ended (POSIX).
            if kill:
                _unregister(path)
            continue
        old = time.time() - e.get("at", 0) > STALE
        what = "owner gone" if not live else "left running"
        if not (old and not live):
            print(f"contained {e['child']} · {what} · {str(e.get('cmd'))[:140]}")
            ended += 1
        if not kill:
            continue
        if live:
            # Ending the wrapper ends its tree: the job closes (Windows), or
            # its handler ends the session (POSIX). Its caller sees REAPED_RC.
            if WINDOWS:
                _end_wrapper(e["wrapper"])
            else:
                try:
                    # SIGUSR1: the wrapper ends its tree as reaped (a wrapper
                    # without the handler dies and its watchdog ends it).
                    os.kill(e["wrapper"], signal.SIGUSR1)
                except (ProcessLookupError, PermissionError):
                    pass
        elif not WINDOWS and not old and _group_alive(e["child"]):
            # The group still exists, so its id cannot have been reused.
            _end_group(e["child"])
        _unregister(path)
    return ended


def sweep(kill, within):
    reaped = _reap(kill, within)
    verb = "ended" if kill else "found"
    print(f"REAP: {verb} {reaped} contained tree(s) left behind")
    procs = _processes()
    if procs is None:
        print("SWEEP: not run · the process list could not be read")
        return
    by_pid = {pid: (ppid, started, cmd) for pid, ppid, started, cmd in procs}
    orphans = []
    for pid, ppid, started, cmd in procs:
        if (not BROWSER_IMAGE.search(_exe(cmd)) or not AUTOMATION.search(cmd)
                or SUBPROCESS.search(cmd) or not _throwaway(cmd)):
            continue
        parent = by_pid.get(ppid)
        if WINDOWS:
            # A parent id Windows has reused belongs to a newer process.
            alive = parent is not None and parent[1] <= started
        else:
            alive = ppid > 1 and parent is not None and not re.match(
                r"(\S*/)?(systemd|launchd|init)(\s|$)", parent[2])
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
    print(f"SWEEP: {verb} {len(orphans)} orphaned automation browser(s)")


# --- main --------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if args[:1] == ["sweep"]:
        rest, kill, within = args[1:], False, []
        while rest:
            flag = rest.pop(0)
            if flag == "--kill":
                kill = True
            elif flag == "--within" and rest:
                within.append(rest.pop(0))
            else:
                sys.exit(__doc__)
        sweep(kill, within)
        return
    if args[:1] == ["stop"]:
        if len(args) != 2 or not args[1].isdigit():
            sys.exit(__doc__)
        stop(int(args[1]))
        return
    timeout, shell, with_parent, env = None, False, False, {}
    while args and args[0] != "--":
        flag = args.pop(0)
        if flag == "--with-parent":
            with_parent = True
        elif flag == "--timeout" and args:
            timeout = float(args.pop(0))
            if timeout <= 0:
                sys.exit("contain: --timeout must be positive")
        elif flag == "--env" and args and "=" in args[0]:
            key, value = args.pop(0).split("=", 1)
            env[key] = value
        elif flag == "--shell" and args:
            shell, args = True, args
            break
        else:
            sys.exit(__doc__)
    if args[:1] == ["--"]:
        args = args[1:]
    if not args or (shell and len(args) != 1):
        sys.exit(__doc__)
    run(args[0] if shell else args, shell, timeout, with_parent, env)


if __name__ == "__main__":
    main()
