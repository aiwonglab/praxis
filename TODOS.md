# TODOS

Deferred work, captured 2026-09-28 during the `/plan-eng-review` of Codex host
support. Each item was explicitly considered and deferred, not forgotten.

---

## 1. Reconcile the `dev` branch

**What:** Decide the fate of `origin/dev`, which is ahead of `prod` by 2 commits
and behind by 11.

**Why:** It carries two commits that never shipped: `92d67b5 feat: /office-hours
skill — research formulation` and `644fd5f feat: add build & verify step to
/iterate`. Meanwhile CLAUDE.md documents a dev -> prod flow that nobody is
following; both the global checkout and the workspace copy sit directly on
`prod`. The branch is a trap: anyone who follows the documented workflow
branches off an 11-commit-stale base.

**Pros:** Either the /office-hours skill ships or the branch stops implying it
might. The documented workflow becomes true again.

**Cons:** Merging prod into dev will conflict against the /learn -> /praxis-learn
rename and the v0.3.0.0 skill rewrites. Cherry-picking the two commits forward is
probably cleaner but means rewriting them against a changed `iterate/SKILL.md`.

**Context:** Three options: merge prod into dev and continue there; cherry-pick
the two commits onto prod and delete dev; or abandon both commits. The
/office-hours skill is the only real content at stake — the /iterate build-verify
step is small enough to re-derive.

**Depends on / blocked by:** Nothing. Do it before the Codex work lands, or the
Codex branch makes the conflict worse.

---

## 2. Use `.codex/skills` for project-local, not `.agents/skills`

**What:** When writing the Codex host entry, use `.codex/skills/` as the
project-local root rather than copying gstack's `.agents/skills/`.

**Why:** gstack's `hosts/codex.ts` sets `localSkillRoot: '.agents/skills/gstack'`
and `hostSubdir: '.agents'`. Current Codex documentation says personal skills
live in `~/.codex/skills/` and project skills in `.codex/skills/`. `.agents/` is
an older convention. Copying gstack's config verbatim inherits a stale path on
day one.

**Pros:** praxis ships on the documented convention. One fewer thing to migrate
later.

**Cons:** Diverges from the reference implementation, so a future diff against
gstack's host config shows a difference that is intentional and needs a comment
saying so.

**Context:** The global root (`~/.codex/skills/`) is correct in gstack and should
be copied as-is; only the project-local root differs. Worth reporting upstream to
gstack rather than silently diverging.

**Depends on / blocked by:** Nothing. Decide it while writing the host table.

---

## 3. Stand up CI

**What:** Add a GitHub Actions workflow that regenerates all host output and
fails if the committed files differ.

**Why:** The pytest byte-equality test is the only thing standing between a
template edit and stale committed output. A test that only runs when someone
remembers to run it is not a gate. praxis has no `.github/workflows/` at all, so
there is nowhere a check runs that a human cannot skip.

**Pros:** The "generated output is committed" decision becomes safe. Contributors
get told immediately instead of shipping a skill whose prose does not match its
template.

**Cons:** praxis has never had CI, so this is a new surface: runner setup, uv
install, and a decision about whether CI also runs ruff and pyright.

**Context:** gstack's equivalent is `.github/workflows/skill-docs.yml`, which
regenerates, diffs, and fails with "Generated Codex SKILL.md files are stale".
Copy that shape. A pre-commit hook is a weaker substitute because `--no-verify`
exists and because contributors on a fresh clone will not have hooks installed.

**Depends on / blocked by:** The pytest suite landing first (nothing to run
otherwise).

---

## 4. Hosts beyond claude and codex

**What:** Decide whether praxis ever targets cursor, kiro, opencode, factory, or
the others gstack supports.

**Why:** The host table makes a third host cheap, but only if the abstraction was
built with one in mind. Recording why we stopped at two keeps the next person
from reading it as an oversight and "helpfully" generalizing it.

**Pros:** Adding a host later becomes a config entry rather than an argument.

**Cons:** None now. This is a note, not work.

**Context:** Deliberately out of scope for the Codex port. gstack supports 9
hosts because gstack is a general builder framework. praxis serves clinical
researchers, who overwhelmingly use one or two agents. Two hosts is the honest
scope until someone asks for a third.

**Depends on / blocked by:** Actual demand. Do not build speculatively.
