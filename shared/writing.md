# Writing rules

Everything the flow writes: chat with the human, prompts to agents, agent reports, issues, comments, pull requests.

- Result first. No preamble, no closing recap, no offers of more help.
- Bullets and fragments, one idea per line. Use the stage's template where one exists.
- An agent's final message is its report template and nothing else.
- Only what changes what the reader does. Cut what they already have: the title, the diff, the map, the prompt.
- Numbers and names, not adjectives: "timeout 5s, vendor docs", not "a reasonable timeout".
- Every finding has a file:line or a link; without one, do not report it. For a defect, add what is wrong and what it should be.
- State what was found or decided, not how: no search or reasoning narrative. Give a reason only when it changes the reader's action.
- Literal words: no metaphors, "not X but Y" contrasts, rhythmic triads, intensifiers ("crucial", "robust") or hedges. Unverified is labelled, not softened.
- Between steps, write only when the human has to see or decide something.
