# Record

The file written to `Out`. A reviewer reads it to see what was decided and why; the caller stores it whole. Keep the headings and the `Requires` / `Adds` lines in this shape.

```
D<k> · <Dispatched question> → <chosen decision, one sentence>

## D<k> · record
Asked      · <the caller's Problem, verbatim>
Dispatched · <the neutral version sent to the debaters>
Spec       · <reference> · "<excerpt>"
Facts      · <as dispatched, one per line>
Rounds     · 1 · consensus | 2 · no consensus after round 1: <why>

### Verdicts
V<n> · <strong|standard> · round <1|2> · <changed from round 1: yes · why | no>   (round field and change only in round 2)
  Decision · <one sentence>
  Why      · <…>
  Sources  · <source> · <checked ✓ | failed · <what the page says instead> | not checked>   one per line
  Rejected · <alternative · why>   one per line
  <unsourced>   when it is

### Groups
G<n> · <decision> · V<a> V<b> …          round 1, then round 2 when it ran

### Chosen
Decision · <the decision, concrete enough to build>
Group    · G<n>
Basis    · sourced | most reversible · no verified source · <why it is the most reversible proposed>
Rests on · <each source the choice relies on> · checked ✓
Why      · <why this position beat the others, by sources>
Repeats  · no | <the earlier attempt in Facts it repeats, and why it is chosen anyway>
Requires · R<n>   only when the decision makes a derived requirement required
Adds     · "<requirement words>" · bound <domain | —>   only when the decision adds an observable behaviour no requirement covers

### Against
- G<n> · <decision> · V<a> … · <its strongest source> · lost because <…>
- Rejection · "<shared reason>" · V<a> V<b> · <why it does not hold against the choice>
```

Checks before writing it:

- `Dispatched` holds no option, candidate approach, preference, yes/no or either-or; `Asked` is the caller's wording verbatim.
- Round 1 lists 5 verdicts, 3 strong and 2 standard.
- Round 2 verdicts appear only when `Rounds` says round 1 reached no consensus, and why.
- Every source under `Rests on` is `checked ✓`; the chosen decision is one a debater proposed and breaks no `Fact`.
- `Against` lists every position not chosen and every shared rejection of the chosen one.
