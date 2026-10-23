# Drive

You drive as Q1 or Q2, named in your prompt, against the contract that follows it. You choose the values, routes, ports and tools; the supervisor judges only what your saved evidence shows. Tests and type checks are not evidence here. Log what you see, including what the contract did not expect; never change a drive to make it pass.

## Verdicts

One per line (Q1: `S<k>` or `R<n>`) or risk area (Q2):

- **verified**: driven on its surface; the read-back meets settled when, read literally.
- **not verified**: driven and wrong, and wrong again on a fresh run (app restarted, new values) with the control passing. Wrong on only one run: add `intermittent`.
- **not driven**: nothing reached it after meeting its prerequisites and trying more than one route (one failed route is as often the driver's mistake as the app's); name the precondition and the routes. Or the ceiling or timebox ran out first: name what you would drive next.

A caveat is not verified or not driven. When the control fails too, the harness is broken: every line is not driven.

## What must hold

- **Start from a clean, matching checkout.** HEAD differs from the contract or `git status --porcelain` is not empty: stop, every line not driven, naming why. Read the contract's recipe in full first: its harness, traps and teardown win.
- **Change nothing in the checkout**, even briefly: another driver may be using it, and Judge names every new path. What the app writes belongs in the data dir; your own files go in your subdir of the evidence dir (run tools from there, since many write where they run). The supervisor already installed and built; a launch that needs an edit, install or build makes every line not driven, naming what it needs.
- **The app as shipped**: overrides only on the lines the contract lists them for. A line that passes only with an unlisted variable is not verified, naming it.
- **Contain every process you start** (server, browser script, suite): `python3 <this skill's directory>/scripts/contain.py -- <command>` (`--env KEY=VALUE` for variables; `--shell "<line>"` only for pipes and `&&`, cmd.exe on Windows). When it exits or is stopped, everything it started ends; its first stderr line `contain: pid <n>` is the pid to stop it by. contain will not start: stop, every line not driven; never run uncontained.
- **Your own server** in the Run line's working dir (a base: the same dir in its worktree), on a port no other live server holds, output saved, up on its health check before you drive. Stop only what you started.
- **Control first**: drive one path the diff never touched, saved as `control.txt`. It is how Judge tells a harness failure from a product failure.
- **Evidence**: every value you report sits in a file in your subdir under the command that printed it (e.g. `{ echo '$ <cmd>'; <cmd>; } >> <file> 2>&1`, or a saved script with its output beside it). The report gives the value, never the page or the log. HTTP with headers and status; CLI with its exit code.
- **Run values**: put the run id in every value you create, so runs never meet each other's data.
- **Local only**: every URL, receiver and service the app touches runs on this machine; no outside hosts (`example.com` included), production, real payments, real emails or shared accounts. Not doing stays out.
- **Credentials** only from their `MSTACK_SECRET_<NAME>` variables: never print one, write it into a saved script, `replay.json` or recipe, or type it into a recorded page; mask any that reaches a file as `***`. A login from a set credential or the repo's own seed, fixture or test data is a precondition: meet it, by script if need be. Any other login (a credential prompt, a sign-in opened in the default browser): stop that command; the line is not driven, naming the login. Never complete, script or get around it.
- **Browsers headless and honest**: never a visible window, never hiding automation (stealth flags such as `--disable-blink-features=AutomationControlled`, stealth plugins, a faked user agent). A bot check or captcha: not driven, naming it. A browser script of your own closes its browser in a `finally` and runs contained. Never the repo's test files.
- **A page value is read back by a command whose output is saved** (text, value, url, visibility, count, an accessibility snapshot). A screenshot shows it; it never settles it.
- **Teardown**: every contained command stopped by its pid, every browser session you opened closed (and confirmed gone), any base worktree you added removed, your ports free, `git status --porcelain` empty. The supervisor's sweep names anything still running as a teardown you missed.

## Q1, does it do what was asked?

- The supervisor's replay output (`<evidence dir>/replay.txt`) is a lead for the lines it left open, never evidence.
- Slice mode: drive only what the slice range touched; no base, no other slice's lines. Final mode: an `S<k>` whose replay failed or went stale is driven like any line; whether a later line supersedes it is the supervisor's call.
- Never drive the base: a line that fails is not verified whatever the base does.
- A clause over a set is checked over the whole set by a script that prints the member count and an expected count from an independent route (a fresh read, the source list) and fails on 0 or a mismatch. A not verified names every failing member.
- A clause with a bound is driven at each limit and just past it.
- A timing clause: report the raw numbers. Judge only the tolerance the clause states; what you observe lags what the app does, so a value within your measurement gap of the bound meets it.
- Ceiling: 60 minutes in all, cut after 10 minutes with no new file in your subdir and no command of yours running. A whole-set script is slow, not stuck. Lines done keep their results; open lines are `not driven · ceiling`, naming what is next.
- `media only` lines (final mode): their replay verified them; drive each once only to record its clip and after screenshot, and report `media only · <files>`. One you see fail is a Deviation naming the value, not a verdict.

**Replays.** Each line you verify by a script gets a replay in `replay/<line>/`, so later proves can re-check it without an agent. It must:

- hold everything it imports or reads (only that dir is kept; copy a shared helper into each);
- read the app's URL from `MSTACK_URL`, the data dir from `MSTACK_DATA`, credentials from `MSTACK_SECRET_<NAME>`, and put `MSTACK_RUN` in every value it creates (it runs again, against data earlier runs left);
- exit 0 only when settled when holds, printing the observed value on its last line;
- be listed in `replay/replay.json` as `{"<line>": {"cmd": "<program and arguments, run from replay/<line>/>", "clause": "<the line's clause, exactly as clauses.json has it>"}}`. The command runs without a shell on every OS: no `$`, `%`, quotes, pipes, redirects or `&&`, no `bash`, `sh` or `cmd`.

Check them as they will be replayed, against your own server: `python3 <this skill's directory>/scripts/replay.py run --from <subdir>/replay --url <your server> --data <data dir> --clauses <evidence dir>/clauses.json --run <run id>-q1 --out <subdir>/replay-check.txt`. A line it does not pass, or one whose check needs a step no script can take, gets no entry.

## Q2, what else broke? (final mode only)

- For each risk area, find the smallest drive that would show it broken, spending most time where a break is likeliest. What a diff reaches is often outside the request path it was written for (illustrative: a restart, shutdown with work in flight, an integration that hangs).
- Timebox: 20 minutes of driving. Open areas are not driven, naming what you would drive next.
- Compare against the base: the contract's base worktree, already built; change nothing in it. None: add your own under your subdir, installed and with the env files copied. Drive the base against itself first to learn the noise (ids, timestamps), then the same drive with the same inputs on head and base. The base counts only when its health check and control pass and it needs no data state the head changed (migration, schema); else `base not run`.
- Each R line whose surface is a page: a before screenshot on the base, `<line>-base-<w>x<h>.png`, at the viewport the clause names (else 1280x720), for the pull request to show beside Q1's after.
- Report what each area covered and every break with head and base values. Noise you learned is not a break. A difference that is exactly what an R line's settled when observes on that surface is the change: report it as `intended R<n>` with both values and the value that clause predicts for your inputs. What an Assumed decision describes is still a break.

## Media (Q1, final mode, when the Run line has ffmpeg)

Media show a reviewer the line working; they settle nothing, and a missing clip is never a not verified.

- After screenshots of what a requirement makes visible, once the page shows the value you read back, at the clause's viewport (else 1280x720) with the element scrolled into view: `<line>-head-<w>x<h>.png`.
- A clip per page R line, `media only` included, from after its preconditions to its read-back: `<line>-head-<w>x<h>.mp4`, with a contact sheet beside it. A line you repeat: record the repeat.
- One demo once every page line is done: `demo-head-1280x720.mp4`, the verified page R lines in id order as a user would meet them, each verified result on screen long enough to read, short enough to watch in one sitting.

## Pitfalls

- **Backgrounding a server**: start it with the Bash tool's `run_in_background`, never `&` or `Start-Process`: a shell that returns at once takes the server with it; the harness tracks a background command.
- **No `sleep`/`until` loops in Bash**: they hold the turn until the shell tool's time limit cuts them. Run long commands in the background and let the harness say when they exit; the health check is the only thing worth polling.
- **No `contain.py --timeout`** on a server or drive: a cut-short drive reads as a false failure.
- **A just-freed port can still answer** from the server that held it: give each server (yours, another driver's, a base) its own port.
- **Dev servers compile routes on first request**: hit each route once before reading or timing it, head and base alike, or you measure the build.
- **Shutdown with work in flight**: use `contain.py stop <pid>` (SIGTERM on POSIX, Ctrl+Break on Windows, which Node sees as `SIGBREAK`). `taskkill` and `process.kill()` on Windows skip shutdown handlers. The app ignores that signal: not driven, naming it.
- **agent-browser** (the supervisor installs it): read `agent-browser skills get core` once, since it matches the installed version. `agent-browser doctor --offline --quick` failing: `npx @playwright/cli` in its own session, named on Harness.
  - Use your own `--session` on every command (and a separate one for a base): localhost cookies do not separate by port, and a shared session's cache serves head's pages to the base. Never the default session, never `close --all`: another driver's browser is live.
  - Every command of a session needs `--allowed-domains localhost,127.0.0.1 --idle-timeout 10m`: one without them relaunches the browser on a blank page. A page that loads from another host fails the control: allow only that host, named on Harness.
  - Refs from `snapshot -i` go stale on every page change; take a fresh one. Wait on what you expect (`wait --text`, `--url`, `@ref`), not on milliseconds. `session list` can lag a `close`: check again before reporting a session still open.
  - `get count` prints 0 and exits 0 for a selector that matches nothing, a blank page included: a count needs its expected count.
  - `errors --json`, not plain `errors` (prints nothing in 0.38); with `network requests`, save both after each flow and after the control. An uncaught error or failed request the flow did not ask for and the control did not show is a Deviation (Q1) or a break to check on the base (Q2).
  - Head vs base pages: both servers are never up at once, so never `diff url`; save the base's full `snapshot` (not `-i`) and screenshot, then `diff snapshot --baseline` / `diff screenshot --baseline` on head at the same viewport. Both exit 0 on a difference: read their output.
- **Recording**: when the Run line gives an ffmpeg dir, prefix agent-browser commands with `PATH="<dir>:$PATH"`: the session's daemon starts ffmpeg, and the shell's PATH predates its install. `record start <file> --fps 15 --cursor --contact-sheet`, `record stop`. Start recording after any secret is typed: a video cannot be masked. `record start` failing: run `doctor` into your file and try once more, then record nothing and name it on Harness.
- **Windows teardown of an uncontained process**: find the port's owner (`netstat -ano`) and end its tree (`taskkill //T //F //PID`).

## Report

In this shape, so Judge can check it against the files:

```
HEAD <sha> · tree <sha> · checkout clean <yes | no: files> · driving <Q1 | Q2>
<line> — <verdict | media only> · drove <what, with which values> → <value> via <route> · <file> · repeated <yes | no> · replay <saved in replay/<line> | none · why>
Area <name> — <verdict> · drove <what, head and base> → head <value> · base <value | not run> · <file> [· intended R<n> · predicts <value>]
Break — <what> · head <value> · base <value | not run> · <file>
Deviation — <what you saw that the contract did not expect> · <file>
Control — <passed | failed> · control.txt
Media — <line> <clip mp4 | screenshot png, Q2: base png> · demo <mp4> | none · <why>
Not driven — <line> · <precondition> · <routes tried>
Teardown — stopped <pids> · port free <yes | no>
Harness — <launch> · <health check> · <traps hit> · browser <tool and version | none> · allowed hosts <beyond localhost | none>
```
