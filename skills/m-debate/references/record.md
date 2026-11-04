# Record

The file written to `Out`. A reviewer reads it to see what was decided and why; the caller stores it whole. Keep the headings and the `Requires` / `Adds` lines in this shape.

```
D<k> · <Dispatched question> → <chosen decision, one sentence>

## D<k> · record
Asked      · <the caller's Problem, verbatim>
Dispatched · <the neutral version sent to the debaters>
Spec       · <reference> · "<excerpt>"
Repo       · <path> · at <commit noted before dispatch>
Facts      · one per line: <as given> · current ✓ <how checked> | stale · now <what is true> · <evidence> | history · seen at <commit or time>
Rounds     · 1 · consensus | <n> · <why each later round ran: no consensus | review finding>

### Verdicts
V<n> · <strong|standard> · round <r> · <changed from the round before: yes · why | no>   (round field and change only after round 1)
  Decision · <one sentence>
  Why      · <…>
  Sources  · <source> · <checked ✓ | failed · <what the page, line or repeat shows instead> | not checked>   one per line, observations included
  Rejected · <alternative · why>   one per line
  Unobserved · <…>   when it is
  <unsourced>   when it is

### Groups
G<n> · <decision> · V<a> V<b> …          per round

### Chosen
Decision · <the decision, concrete enough to build>
Group    · G<n>
Basis    · sourced | most reversible · no verified source · <why it is the most reversible proposed>
Rests on · <each source the choice relies on> · checked ✓
Why      · <why this position beat the others, by sources>
Repeats  · no | <the earlier attempt in Facts it repeats, and why it is chosen anyway>
Undoes   · no | D<j> · <what of it is undone, why> · <requirements that lose their proof>
Requires · R<n>   only when the decision makes a derived requirement required
Adds     · "<requirement words>" · bound <domain | —>   only when the decision adds an observable behaviour no requirement covers

### Review
Pass <n> · <decision reviewed> · holds | breaks
  Breaks     · <what> · <source> · confirmed ✓ | not confirmed · <why>   one per line
  Undoes     · <as the reviewer gave it>
  Unobserved · <…>
  Then       · <chosen | another position chosen: G<m> | another round with the finding as a Fact>

### Against
- G<n> · <decision> · V<a> … · <its strongest source> · lost because <…>
- Rejection · "<shared reason>" · V<a> V<b> · <why it does not hold against the choice>

### Left as found
Checkout · at <commit>, no change by the debate | <what was changed and restored>
Processes · none left running | <what was stopped>
```

Checks before writing it:

- `Dispatched` holds no option, candidate approach, preference, yes/no or either-or; `Asked` is the caller's wording verbatim.
- Every Fact has its status; a stale one reached the debaters corrected.
- Round 1 lists 5 verdicts, 3 strong and 2 standard; each later round says why it ran.
- Every source under `Rests on` is `checked ✓` at the current commit or by repeating the observation; the chosen decision is one a debater proposed, breaks no `Fact` or proved requirement, and agrees with its own `Adds` and `Requires`.
- The last review pass is of the chosen decision and holds, or every break it lists is `not confirmed` with why.
- `Against` lists every position not chosen and every shared rejection of the chosen one.
