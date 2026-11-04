#!/usr/bin/env python3
"""The run spec: how scripts install, build, launch, health-check and reset the app.

  runspec.py check [<run.json>] [--checkout <dir>]
      Validates a spec and prints it resolved (placeholders filled), or what is wrong.
      Without a path: the fallback below. Exit 0 = usable, 1 = not.

prepare.py and replay.py batch read it; the supervisor writes it into the evidence dir as
run.json from the recipe's run.json (beside the recipe's SKILL.md), or from the recipe's text
or scan Q9 when the recipe has none. A recipe inside the checkout cannot hold it (the checkout
stays clean): keep it at <git common dir>/mstack/run.json, which the scripts read when the
evidence dir has none. JSON, every key optional:

  {
    "cwd":      "web",                         where commands run, relative to the checkout (".")
    "install":  ["npm ci"],                    shell lines, run once by prepare.py, in order
    "build":    ["npm run build"],
    "build_timeout": 3600,                     seconds one install or build line may take
    "launch":   "npm start -- --port {port}",  shell line that serves the app until stopped;
                                               none (a CLI, a library): nothing is launched and
                                               replays get no MSTACK_URL
    "port":     3000,                          the port when launch has no {port}; with {port},
                                               scripts pick a free one per instance
    "url":      "http://127.0.0.1:{port}",     what replays get as MSTACK_URL (this default)
    "health":   "http://127.0.0.1:{port}/health"   required with launch: a URL, or a shell line
                                               that exits 0 when the app is up
    "health_status": "any",                    which HTTP answers mean up: a list of codes, or
                                               "any" (a dev server whose root answers 404);
                                               default 200-399
    "health_timeout": 120,                     seconds to wait for health after a launch
    "data":     "data",                        the app's data dir (MSTACK_DATA), relative to cwd
    "env":      {"NODE_ENV": "production"},    what the recipe or .env.example sets; no secrets
    "env_files": [".env", "web/.env.local"],   ignored files a base worktree needs (default: every
                                               ignored file named .env*, outside dependency dirs)
    "restore":  "git checkout -- data",        shell line that puts shared state back; replays
                                               then run one at a time, each after a restore
    "parallel": 1                              replays at once: above 1 only when each replay's
                                               state is separable (it touches only values
                                               carrying its own MSTACK_RUN)
  }

Placeholders in any string: {port}, {data} (absolute data dir), {checkout}.
Shell lines run through contain.py --shell: cmd.exe on Windows, sh elsewhere.
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONTAIN = os.path.join(HERE, "contain.py")
PYTHON = getattr(sys, "_base_executable", None) or sys.executable
BUILD_TIMEOUT = 3600

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def common_dir(cwd=None):
    p = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       cwd=cwd, capture_output=True, text=True)
    return os.path.realpath(p.stdout.strip()) if p.returncode == 0 else None


def locate(path, evidence=None, checkout=None):
    """The spec to read: the path given, else <evidence>/run.json, else <git common dir>/mstack/run.json."""
    if path:
        return path
    tried = []
    if evidence:
        tried.append(os.path.join(evidence, "run.json"))
    common = common_dir(checkout)
    if common:
        tried.append(os.path.join(common, "mstack", "run.json"))
    for t in tried:
        if os.path.isfile(t):
            return t
    sys.exit("ABORT: no run spec: give --spec, or write " + " or ".join(tried))


def load(path):
    """The spec as a dict, or exit with what is wrong."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as e:
        sys.exit(f"ABORT: run spec {path}: {e}")
    errors = problems(spec)
    if errors:
        sys.exit("ABORT: run spec " + path + ": " + "; ".join(errors))
    return spec


def problems(spec):
    if not isinstance(spec, dict):
        return ["needs a JSON object"]
    out = []
    for key in ("launch", "health", "restore", "cwd", "data", "url"):
        if key in spec and (not isinstance(spec[key], str) or not spec[key].strip()):
            out.append(f"{key} must be a non-empty string")
    if spec.get("launch") and not spec.get("health"):
        out.append("launch needs a health check")
    for key in ("install", "build", "env_files"):
        v = spec.get(key, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            out.append(f"{key} must be a list of strings")
    if not isinstance(spec.get("env", {}), dict):
        out.append("env must be an object")
    if (spec.get("launch") and "{port}" not in spec["launch"]
            and not isinstance(spec.get("port"), int)):
        out.append("give port, or use {port} in launch")
    hs = spec.get("health_status")
    if hs is not None and hs != "any" and not (
            isinstance(hs, list) and hs and all(isinstance(c, int) for c in hs)):
        out.append('health_status must be "any" or a list of HTTP codes')
    if not isinstance(spec.get("parallel", 1), int) or spec.get("parallel", 1) < 1:
        out.append("parallel must be a whole number, 1 or more")
    return out


def cwd_of(spec, checkout):
    return os.path.realpath(os.path.join(checkout, spec.get("cwd", ".")))


def data_of(spec, checkout):
    d = spec.get("data")
    return os.path.realpath(os.path.join(cwd_of(spec, checkout), d)) if d else None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fill(text, spec, checkout, port):
    return (text.replace("{port}", str(port))
                .replace("{data}", data_of(spec, checkout) or "")
                .replace("{checkout}", os.path.realpath(checkout)))


def env_of(spec, checkout, port):
    return {**os.environ, **{k: fill(str(v), spec, checkout, port)
                             for k, v in spec.get("env", {}).items()}}


def parallel(spec):
    return 1 if spec.get("restore") else spec.get("parallel", 1)


def healthy_status(spec, code):
    allowed = spec.get("health_status")
    if allowed == "any":
        return True
    return code in allowed if allowed else 200 <= code < 400


def shell(line, spec, checkout, port, log, timeout=None):
    """Run one shell line contained, output appended to log. Returns (rc, last line, seconds).
    Never raises: a line that cannot start (its cwd missing, say) is rc 127 with the reason."""
    start = time.monotonic()
    filled = fill(line, spec, checkout, port)
    cmd = [PYTHON, CONTAIN, "--with-parent"]
    if timeout:
        cmd += ["--timeout", str(timeout)]
    cmd += ["--shell", filled]
    try:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"$ {filled}\n")
            fh.flush()
            try:
                p = subprocess.run(cmd, cwd=cwd_of(spec, checkout),
                                   env=env_of(spec, checkout, port), stdout=fh,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
                rc = p.returncode
            except OSError as e:
                fh.write(f"cannot start in {cwd_of(spec, checkout)}: {e}\n")
                rc = 127
            fh.write(f"# exit {rc}{' (timed out)' if rc == 124 and timeout else ''}\n")
    except OSError as e:
        return 127, f"cannot write {log}: {e}", round(time.monotonic() - start)
    return rc, last_line(log), round(time.monotonic() - start)


def last_line(log):
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip() and not l.startswith(("# exit", "contain: "))]
        return (lines or [""])[-1][:160]
    except OSError:
        return ""


class App:
    """One contained instance of the app, started in the background of this script."""

    def __init__(self, spec, checkout, log):
        self.spec, self.checkout, self.log = spec, checkout, log
        self.port = free_port() if "{port}" in spec["launch"] else spec.get("port")
        self.url = fill(spec.get("url", "http://127.0.0.1:{port}"), spec, checkout, self.port)
        self.proc = self.fh = None

    def start(self):
        """Launch and wait for health. Returns (up, seconds, why)."""
        start = time.monotonic()
        self.fh = open(self.log, "a", encoding="utf-8")
        line = fill(self.spec["launch"], self.spec, self.checkout, self.port)
        self.fh.write(f"$ {line}\n")
        self.fh.flush()
        try:
            self.proc = subprocess.Popen(
                [PYTHON, CONTAIN, "--with-parent", "--shell", line],
                cwd=cwd_of(self.spec, self.checkout),
                env=env_of(self.spec, self.checkout, self.port),
                stdout=self.fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        except OSError as e:
            return False, 0, f"cannot launch: {e}"
        deadline = start + self.spec.get("health_timeout", 120)
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                return False, round(time.monotonic() - start), f"launch exited {self.proc.returncode}"
            if self.healthy():
                return True, round(time.monotonic() - start), ""
            time.sleep(1)
        return False, round(time.monotonic() - start), "health check timed out"

    def healthy(self):
        target = fill(self.spec["health"], self.spec, self.checkout, self.port)
        if target.startswith(("http://", "https://")):
            try:
                with urllib.request.urlopen(target, timeout=10) as r:
                    return healthy_status(self.spec, r.status)
            except urllib.error.HTTPError as e:
                return healthy_status(self.spec, e.code)
            except (OSError, ValueError):
                return False
        try:
            p = subprocess.run([PYTHON, CONTAIN, "--with-parent", "--timeout", "60", "--shell", target],
                               cwd=cwd_of(self.spec, self.checkout),
                               env=env_of(self.spec, self.checkout, self.port),
                               capture_output=True, timeout=90)
        except (subprocess.TimeoutExpired, OSError):
            return False
        return p.returncode == 0

    def stop(self):
        """End the instance and everything it started (contain ends the tree when its wrapper goes)."""
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()  # POSIX: SIGTERM, contain ends the group; Windows: the job closes
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        if self.fh:
            self.fh.write("# stopped\n")
            self.fh.close()
            self.fh = None


def main():
    args = sys.argv[1:]
    if args[:1] in (["-h"], ["--help"]) or args[:1] != ["check"]:
        print(__doc__)
        sys.exit(0 if args[:1] in (["-h"], ["--help"]) else 2)
    args = args[1:]
    checkout = os.getcwd()
    if "--checkout" in args:
        i = args.index("--checkout")
        checkout = args[i + 1] if i + 1 < len(args) else checkout
        del args[i:i + 2]
    path = locate(args[0] if args else None, None, checkout)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            spec = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"RUNSPEC: BAD · {e}")
        sys.exit(1)
    errors = problems(spec)
    if errors:
        print("RUNSPEC: BAD · " + "; ".join(errors))
        sys.exit(1)
    launch = spec.get("launch")
    port = "<free port>" if launch and "{port}" in launch else spec.get("port")
    print(f"spec · {path}")
    print(f"cwd · {cwd_of(spec, checkout)}")
    for key in ("install", "build"):
        for line in spec.get(key, []):
            print(f"{key} · {fill(line, spec, checkout, port)}")
    if launch:
        print(f"launch · {fill(launch, spec, checkout, port)}")
        print(f"health · {fill(spec['health'], spec, checkout, port)} · "
              f"up on {spec.get('health_status', '200-399')}")
    else:
        print("launch · none: replays run without an app and get no MSTACK_URL")
    print(f"data · {data_of(spec, checkout) or 'none'}")
    print(f"restore · {spec.get('restore') or 'none'} · replays at once {parallel(spec)}")
    print("RUNSPEC: OK")


if __name__ == "__main__":
    main()
