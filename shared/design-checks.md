# Design checks

`/m-plan` runs them on the plan. `/m-review` runs them on the code (B2), only when hard to undo, and reports intended vs built where they differ.

Depth: hard to undo → all seven, report each. Easy → one pass in `/m-plan`, report only failures; `/m-review` skips them.

1. Will other code use this? Yes → put it somewhere shared, outside the feature folder.
2. If this decision changes, how many files change? More than 1–2 → keep the decision in one place. *(S)*
3. Does the next similar case require editing existing code (the same `if`)? Yes → there is nowhere to extend (check 7 still applies). *(O)*
4. Does any implementation leave methods empty or throw "not supported"? Yes → callers cannot rely on the interface it claims. *(L)*
5. Does the caller use every method of the interface? Only some (e.g. 2 of 9) → split or narrow it. *(I)*
6. How many fakes does a test of this need? Many → it depends on things it should not know. *(D)*
7. Does this abstraction have two real cases yet? One → do not abstract. This check overrides 3 and 6: no factories, interfaces or pass-through layers "just in case".
