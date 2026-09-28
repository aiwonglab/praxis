# Changelog

All notable changes to praxis. The current release is tracked in the `VERSION`
file; `bin/praxis-update-check` compares it against `prod/VERSION` to prompt
upgrades. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added
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
