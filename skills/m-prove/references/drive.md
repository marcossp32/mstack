# Drive

You drive as Q1 or Q2, named in your prompt. Tests and type checks are not evidence here. Log what you see, including what the contract did not expect; never change a drive to make it pass.

Verdicts, one per R line (Q1) or risk area (Q2):

- **verified**: driven on its surface; the read-back meets settled when, read literally.
- **not verified**: driven and wrong, repeated once on a fresh run with new values, with the control passing. Wrong on only one of the two runs: add `intermittent`.
- **not driven**: nothing reached it after doing its prerequisites and trying two different routes; name the precondition and both routes.
- **pre-existing** (Q1): not verified on head, and the base fails the same observation the same way.

A caveat is not verified or not driven.

**Setup**
- HEAD differs from the contract, or `git status --porcelain` is not empty: stop; every line is not driven, naming why.
- Read the contract's recipe in full, as a file: its harness, traps and teardown win; evidence goes only to your subdir of the evidence dir. Leave `/run` and `/verify` uninvoked.
- Start every command with `cd <your subdir> &&`, so tools that write where they run stay out of the checkout.
- Change no file in the checkout, even temporarily, ignored files included. The supervisor already ran the recipe's installs and builds there; run none yourself, since the other driver may be using the same checkout. A launch that needs an edit, an install or a build: every line not driven, naming what it needs.
- Environment: the shipped defaults; set an override only on the lines the contract lists it for. A line that passes only with a variable the contract does not list: not verified, naming the variable.
- Start your own server from the checkout, output to `launch.txt`, on a port the other driver is not using (Q1 the recipe's port or the next free one, Q2 that plus 100); poll the health check for up to 2 minutes. Stop only processes you started.
- That health check is the only loop you wait on. A long command (a suite, a build): run it in the background when the harness tells you it has finished; never wait with `sleep` or `until` loops.
- **Control**: before anything else, drive one path the diff never touched and save it as `control.txt`.

**Q1, does it do what was asked?**
- For each R line choose the values and steps yourself; put the run id in every value you create.
- A line comes back not verified: drive the same observation on the base, set up as Q2 does below. It fails the same way there: `pre-existing`, with head and base values. The base cannot run: keep not verified and add `base not run`.
- A timing requirement: report the raw numbers you measured. Judge only the tolerance the clause states; what you observe lags what the app does, so a value within your measurement gap of the bound meets it.

**Q2, what else broke?**
- For each risk area, find the smallest drive that would show it broken: the flow it shares, a restart, shutdown with work in flight, an integration that fails or hangs, defaults left unset. Spend most time where a break is likeliest.
- Timebox: 20 minutes of driving, then report. An area still open is not driven, naming what you would drive next.
- Compare against the base: `git worktree add --detach <subdir>/base <base>`, dependencies installed and env files copied, one server up at a time. Drive the base once against itself first, to learn what differs anyway (ids, timestamps); then the same drive with the same inputs on head and base. The base counts only when its health check and control pass and it needs no data state the head changed (migration, schema); else `base not run`.
- A page: on the base, save its full `snapshot` (not `-i`: the diff compares full trees) to a file and a screenshot of it; on head, at the same viewport, the same page through `diff snapshot --baseline <file>` and `diff screenshot --baseline <png>`. Both servers are never up at once, so never `diff url`.
- Report what each area covered and every break, with head and base values. What differs only in the noise you learned is not a break.

**Driving**
- Local only: every URL, receiver and service you point the app at runs on this machine. No outside hosts (`example.com` included), production, real payments, real emails or shared accounts.
- Not doing stays out, even where you see a gap in it.
- HTTP: `curl -sS -i`. CLI: keep the exit code.
- Every value you report sits in a file in your subdir under the command that printed it: `{ echo '$ <cmd>'; <cmd>; } >> <file> 2>&1`, or a script saved there with its output beside it. The report gives the value, never the page or the log.
- Shutdown on Windows: `process.kill()` and `taskkill` end the process without running its shutdown handlers. Start the app in its own console and send Ctrl+Break to its process group, or share a console and send Ctrl+C with `GenerateConsoleCtrlEvent` from PowerShell. The app handles neither signal: not driven, naming both.

**Browser**: any line or area whose surface is a page.
- `agent-browser`, which the supervisor installed. Before your first browser command, read `agent-browser skills get core` once: it matches the installed version. `agent-browser doctor --offline --quick` fails: `npx @playwright/cli` in its own named session, named in Harness; local only still holds without the allowlist. Never the repo's test files.
- Your own session on every command: `--session <run id>-<q1 | q2>`, and `<run id>-q2-base` for the base, since localhost cookies do not separate by port and a session's cache would serve head's pages to the base. Never the default session and never `close --all`: the other driver's browser is live.
- The first command of each session carries `--allowed-domains localhost,127.0.0.1`; the session keeps it. The control fails because the page loads from another host: allow only that host, named in Harness.
- Act on refs from `snapshot -i` and take a fresh one after every page change; `find` when a ref will not do. Wait on what you expect (`wait --text`, `wait --url`, `wait @ref`), never `wait <ms>`.
- A page value is read back by a command whose output lands in the evidence file: `get text | value | url`, `is visible | enabled | checked`, `get count`, `snapshot -i --json`. A screenshot shows it; it never settles it.
- Screenshot what a requirement makes visible: `set viewport <w> <h>`, then `screenshot <@ref | selector> <line>-<head | base>-<w>x<h>.png`, cropped to that element.
- After each flow, `errors --json` (plain `errors` prints nothing in 0.38) and `network requests` into the same file, and the same after the control. An uncaught error or a failed request (4xx, 5xx, no status) the flow did not ask for and the control did not show is a Deviation for Q1 and a break to check against the base for Q2.

**A line comes back wrong**
1. Repeat it with the app restarted and a new run value.
2. The control fails too: the harness is broken; every line is not driven.

**Teardown**: stop the process trees you started (Windows: the port's owner from `netstat -ano`, then `taskkill //T //F //PID`) · `agent-browser --session <s> close` for each of your sessions, and `agent-browser session list` shows none of them (it can lag a close by a moment: check once more) · `git worktree remove` · port free · `git status --porcelain` empty.

```
HEAD <sha> · tree <sha> · checkout clean <yes | no: files> · driving <Q1 | Q2>
R1 — <verdict> · drove <what, with which values> → <value> via <route> · <file> · repeated <yes | no> · base <value | not run>   base only when not verified or pre-existing
Area <name> — <verdict> · drove <what, head and base> → head <value> · base <value | not run> · <file>
Break — <what> · head <value> · base <value | not run> · <file>
Deviation — <what you saw that the contract did not expect> · <file>
Control — <passed | failed> · control.txt
Not driven — <line> · <precondition> · <routes tried>
Teardown — stopped <pids> · port free <yes | no>
Harness — <launch> · <health check> · <traps hit> · browser <agent-browser version | playwright-cli | none> · allowed hosts <beyond localhost | none>
```
