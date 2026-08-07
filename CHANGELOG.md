# Changelog

All notable changes to praxis. The current release is tracked in the `VERSION`
file; `bin/praxis-update-check` compares it against `prod/VERSION` to prompt
upgrades. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

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
