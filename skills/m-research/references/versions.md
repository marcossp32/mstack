# Reading the pinned version

`latest` docs are often the development branch. Read the installed version's.

- **Versioned docs**: the version in the path (`/en/<version>/`, `/v3/`), reached through the site's version switcher. On Read the Docs, `latest` is the development branch and `stable` the newest release.
- **No versioned docs**: the source at the tag, `github.com/<owner>/<repo>/tree/<tag>`.
- **Registry**: `npm view <pkg>@<version>` — without `@<version>` it answers for `latest`. `pypi.org/pypi/<project>/<version>/json` — check `yanked`; `project_urls` leads to the source.
- **What changed**: the release notes of every release between the two versions, Deprecated, Removed and Security first. `gh release view <tag> -R <owner>/<repo>`; the code between them at `github.com/<owner>/<repo>/compare/<old>...<new>`. Below `1.0.0`, any release may break.
- **Only another version is documented**: quote it, put that version on **Source**, and mark same behaviour in yours as **Inference**.
