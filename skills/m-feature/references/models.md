# Models

Each agent's model is a tier: cheap, standard or strong, the harness's quickest, middle and most capable, by its own names. A harness that offers no choice, or a tier that does not resolve, runs the agent on the session's model.

| Stage | Model |
|---|---|
| scan A | cheap |
| scan B–D | standard |
| build, fix mode included | standard; strong when the undo verdict is hard |
| review | standard |
| prove | strong |

Three judges stand after a build (step check, review, prove), so it does not need the most capable model by default. `/m-research` and `/m-review` name the tier of the agents they dispatch.
