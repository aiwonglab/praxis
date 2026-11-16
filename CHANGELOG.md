# Changelog

All notable changes to praxis. The current release is tracked in the `VERSION`
file; `bin/praxis-update-check` compares it against `prod/VERSION` to prompt
upgrades. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [0.4.0.0] — 2026-11-16

### Added
- `/plan-pi-review` effort levels: **low** (demo mode: 0-1 questions, house
  definitions applied and shown as *Assumptions used*, answer first, review
  after as *Watch-outs*), **medium** (operations: 2-3 questions, short review,
  severity adjustment on, full scope, saved notebook), **high** (unchanged).
  **Low is the default** when no level is stated, for a question or a plan:
  the skill no longer asks up front. After the result it asks once (Stop /
  Medium / High), in the same round as proposed learnings. `praxis-answer
  --effort` and `Spec.effort` default to `low`.
- Effort levels in `/plan-ds-review`, `/plan-ai-review`,
  `/plan-clinical-review`, `/plan-deid-review` and `/plan-protocol` (Step 0.1,
  default low). Low reports the top findings at confidence ≥ 8 with no scores
  or verdict; medium scores every dimension in one table; high is the existing
  text, unchanged and pinned by a test. Gates stay at high: low and medium
  never issue RELEASE (deid) or SUBMIT, and never draft a submittable protocol
  or write the scope lock (protocol).
- `/iterate` runs routed reviews at the session's level (default low), then
  asks once which to rerun at medium or high. A confidence ≥ 8 blocking finding
  at low stops downstream reviews, as a blocking verdict does.
- Metric library in `src/praxis/` and the `praxis-answer` runner: one set of
  canonical definitions and one metric code path for every effort level and
  engine (DuckDB on the open demos, BigQuery for hosted eICU / MIMIC-IV).
  Metrics: survivor ICU LOS, hospital mortality, APACHE IVa observed/expected
  ICU LOS. Cells under n=10 are suppressed by default, with complementary
  suppression, and a release check refuses any that slip through.
- `--min-cell N` (or config `min_cell`) sets the suppression threshold, e.g.
  11 for a k=11 rule; `0` turns it off for internal QI. It only hides cells,
  never changes a value, and output stays aggregate-only at every setting.
- Credentialed-data runs refuse unless `credentialed_data_zdr: confirmed` is
  set (Claude API account with zero data retention).
- One answer notebook for every effort level
  (`src/praxis/templates/answer_notebook.py`): spec, assumptions, answer,
  watch-outs, review, learnings, audit. A level fills what it runs and marks
  the rest *not run*; escalating fills the same file. The audit cell reruns
  the spec and asserts the released table's hash. `run --out` writes it.
- Learnings at low and medium effort: the runner proposes data-driven
  `candidate_learnings` (praxis-learn schema, stable ids per dataset version,
  counts always masked at n<10, nothing from a narrowed run, nothing already
  stored in any project); the skill asks once after the answer and saves only
  what is accepted. Low and medium read prior learnings for the dataset from
  every project (`praxis-learn search <family>`).
- `tests/`: 51 tests, synthetic eICU-shaped data plus an open-demo smoke test.

### Fixed
- `praxis-learn` docs named the store `praxis-learnings.jsonl`; it is
  `learnings.jsonl`.
- `pyproject.toml` named a nonexistent build backend (`hatchling.backends`).
- `/plan-protocol` — regulatory expert that takes a reviewed plan through to a
  submittable IRB protocol for an investigator-sponsored study. Threshold
  determinations (research / human subjects / PHI authority / FDA-regulated
  article / sponsor / sIRB / funding obligations), pathway and waiver findings
  written to the regulatory text, an identifiability ladder and a closed
  minimum-necessary element table, protocol drafting, seven scored dimensions,
  a stipulation pre-mortem, and a `protocol.lock.yaml` scope contract the
  pipeline asserts against. Verdicts: SUBMIT / REVISE / DETERMINE / HOLD.
  Sponsor-investigator obligations under 21 CFR 312 and 812 are a first-class
  branch, not a footnote.
- `regulatory-trap` learning type, `valid_for` an institution and rule version.
- `plan-protocol/references/regulatory-index.md` — citation index, read on demand
  rather than on every invocation.

### Changed
- Review chain is now PI → protocol → DS → AI → Clinical. A protocol can be
  revised after the science settles; a data pull cannot be retroactively
  authorized.
- `/iterate` routes cohort, window, site, element, and *new-use* changes to
  `/plan-protocol`, and distinguishes regulatory drift from scope creep.

## [0.3.0.1] — 2026-08-07

### Fixed
- The learnings skill is now `/praxis-learn` (was `/learn`). gstack ships its own
  real `~/.claude/skills/learn/` directory, so `scripts/setup.sh`'s symlink guard
  silently skipped praxis's `learn` skill — it never registered as a slash command
  for anyone who also ran gstack, and both declared frontmatter `name: learn`.
  Renaming the skill end-to-end (directory, frontmatter, and the five `/learn`
  command headers) lets setup.sh's generic loop link it as `praxis-learn` with no
  special-casing and no collision. The `learn/SKILL.md` reference in all four
  `plan-*-review` skills was updated to `praxis-learn/SKILL.md`; the
  `bin/praxis-learn` CLI is unchanged.

## [0.3.0.0] — 2026-08-06

### Added
- `/plan-deid-review` — de-identification and disclosure-risk audit (identifier
  surfaces, removal-method checks, verify-the-checks, RELEASE / HOLD / REWORK).
- findings-to-guardrails workflow; format-forensics learning types.

## [0.2.0.0] — 2026-04-01

### Added
- Confidence calibration across the review skills.
- Composable skills and `/iterate` (research-lifecycle orchestrator).
- `/praxis-learn` (originally `/learn`) and the per-project learnings system.
