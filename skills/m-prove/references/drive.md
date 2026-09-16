# Drive

You drive as Q1 or Q2, named in your prompt. Tests and type checks are not evidence here. Log what you see, including what the contract did not expect; never change a drive to make it pass.

Verdicts, one per R line (Q1) or risk area (Q2):

- **verified**: driven on its surface; the read-back meets settled when, read literally.
- **not verified**: driven and wrong, repeated once on a fresh run with new values, with the control passing. Wrong on only one of the two runs: add `intermittent`.
- **not driven**: nothing reached it after doing its prerequisites and trying two different routes; name the precondition and both routes.

A caveat is one of the last two.

**Setup**
- HEAD differs from the contract, or `git status --porcelain` is not empty: stop; every line is not driven, naming why.
- Read the contract's recipe in full, as a file: its harness, traps and teardown win; evidence goes only to your subdir of the evidence dir. Leave `/run` and `/verify` uninvoked.
- Start every command with `cd <your subdir> &&`, so tools that write where they run (`playwright-cli`) stay out of the checkout.
- Change no file in the checkout, even temporarily, ignored files included; dependency installs and build output the recipe runs are the exception. A launch that needs an edit: every line not driven, naming the file.
- Environment: the shipped defaults; set an override only on the lines the contract lists it for. A line that passes only with a variable the contract does not list: not verified, naming the variable.
- Start your own server from the checkout, output to `launch.txt`, on a port the other driver is not using (Q1 the recipe's port or the next free one, Q2 that plus 100); poll the health check for up to 2 minutes. Stop only processes you started.
- **Control**: before anything else, drive one path the diff never touched and save it as `control.txt`.

**Q1, does it do what was asked?**
- For each R line choose the values and steps yourself; put the run id in every value you create.
- A timing requirement: report the raw numbers you measured. Judge only the tolerance the clause states; what you observe lags what the app does, so a value within your measurement gap of the bound meets it.

**Q2, what else broke?**
- For each risk area, find the smallest drive that would show it broken: the flow it shares, a restart, shutdown with work in flight, an integration that fails or hangs, defaults left unset. Spend most time where a break is likeliest.
- Timebox: 20 minutes of driving, then report. An area still open is not driven, naming what you would drive next.
- Compare against the base: `git worktree add --detach <subdir>/base <base>`, dependencies installed and env files copied, one server up at a time. Drive the base once against itself first, to learn what differs anyway (ids, timestamps); then the same drive with the same inputs on head and base. The base counts only when its health check and control pass and it needs no data state the head changed (migration, schema); else `base not run`.
- Report what each area covered and every break, with head and base values. What differs only in the noise you learned is not a break.

**Driving**
- Local only: every URL, receiver and service you point the app at runs on this machine. No outside hosts (`example.com` included), production, real payments, real emails or shared accounts.
- Not doing stays out, even where you see a gap in it.
- Browser: the repo's e2e library driven by your own commands, never its test files; else `npx @playwright/cli`. Act on snapshot refs and `find`. Screenshot what a requirement makes visible, cropped to the element, the viewport in the file name.
- HTTP: `curl -sS -i`. CLI: keep the exit code.
- Every value you report sits in a file in your subdir under the command that printed it: `{ echo '$ <cmd>'; <cmd>; } >> <file> 2>&1`, or a script saved there with its output beside it. The report gives the value, never the page or the log.
- Shutdown on Windows: `process.kill()` and `taskkill` end the process without running its shutdown handlers. Start the app in its own console and send Ctrl+Break to its process group, or share a console and send Ctrl+C with `GenerateConsoleCtrlEvent` from PowerShell. The app handles neither signal: not driven, naming both.

**A line comes back wrong**
1. Repeat it with the app restarted and a new run value.
2. The control fails too: the harness is broken; every line is not driven.

**Teardown**: stop the process trees you started (Windows: the port's owner from `netstat -ano`, then `taskkill //T //F //PID`) · close browsers · `git worktree remove` · port free · `git status --porcelain` empty.

```
HEAD <sha> · tree <sha> · checkout clean <yes | no: files> · driving <Q1 | Q2>
R1 — <verdict> · drove <what, with which values> → <value> via <route> · <file> · repeated <yes | no>
Area <name> — <verdict> · drove <what, head and base> → head <value> · base <value | not run> · <file>
Break — <what> · head <value> · base <value | not run> · <file>
Deviation — <what you saw that the contract did not expect> · <file>
Control — <passed | failed> · control.txt
Not driven — <line> · <precondition> · <routes tried>
Teardown — stopped <pids> · port free <yes | no>
Harness — <launch> · <health check> · <traps hit>
```
