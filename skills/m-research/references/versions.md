# Reading the pinned version

The goal: quote the docs for the version that is installed, because behaviour, limits and defaults move between releases. Known traps:

- **`latest` is often the development branch.** On Read the Docs, `latest` is development and `stable` the newest release; many sites put the version in the path (`/en/<version>/`, `/v3/`) behind a version switcher.
- **No versioned docs**: the source at the tag (`github.com/<owner>/<repo>/tree/<tag>`) is what runs at that version.
- **Registries answer for `latest`** unless asked for a version (e.g. `npm view <pkg>@<version>`, `pypi.org/pypi/<project>/<version>/json`). A PyPI release can be yanked; its `project_urls` lead to the source.
- **What changed between two versions** is spread over every release in between, not just the newest; Deprecated, Removed and Security entries are the ones that break code. Below `1.0.0`, any release may break.
- **Only another version is documented**: quote it, put that version on **Source**, and mark same behaviour in yours as **Inference**.
