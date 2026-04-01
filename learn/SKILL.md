---
name: learn
version: 1.0.0
description: |
  View, add, search, and prune project learnings. Learnings are hard-won
  insights about datasets, definitions, statistical traps, and clinical
  observations that compound across iterations and projects.
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# /learn

Manage project learnings — hard-won insights that feed back into review skills.

## What learnings are

Learnings are experiential knowledge that doesn't live in code or git history:
- **dataset-gotcha**: Surprising behavior in a specific dataset/table/variable
- **definition-pitfall**: What goes wrong when operationalizing a clinical definition
- **statistical-trap**: Structural issues with a study design that repeat across projects
- **clinical-insight**: Observations about clinical data patterns or measurement bias
- **user-stated**: Explicit PI decisions or preferences

Learnings are NOT: code patterns, architecture decisions, or things derivable from
the codebase. Those belong in CLAUDE.md or comments.

## Event-gated invalidation (not time decay)

Learnings don't expire on a clock. They're tagged with the context that makes them
true, and flagged for re-verification when that context changes:

| Type | `valid_for` tag | Invalidation trigger |
|------|----------------|---------------------|
| dataset-gotcha | Dataset + version (e.g., `mimic-iv:2.2`) | Referenced dataset version changes |
| definition-pitfall | Definition source (e.g., `sepsis-3:2016`) | Consensus definition superseded |
| statistical-trap | `permanent` | Never — structural truths |
| clinical-insight | Source PMID or study | Contradicting evidence found |
| user-stated | `permanent` | User explicitly changes it |

When a review loads learnings, it checks: "Is this learning still applicable to the
current context?" If context has changed, the learning is surfaced with a caveat —
"This was observed on MIMIC-IV v2.2, verify still applies" — rather than silently
dropped.

## Schema

Each learning is one line of JSONL:

```json
{
  "id": "uuid",
  "type": "dataset-gotcha",
  "content": "labevents itemid 50817 captures all specimen types including venous; use mimiciv_3_1_derived.bg for arterial ABGs",
  "confidence": 9,
  "source": "plan-ds-review",
  "project": "hidden-hypoxemia",
  "dataset": "mimic-iv",
  "valid_for": "mimic-iv:2.2",
  "created": "2026-03-30"
}
```

Fields:
- `id`: unique identifier (UUID or short slug)
- `type`: one of the five types above
- `content`: the learning itself — specific, actionable, one paragraph max
- `confidence`: 1-10 (same scale as review findings)
- `source`: which review skill or manual entry created it
- `project`: project slug (auto-detected from git remote)
- `dataset`: (optional) which dataset this applies to
- `valid_for`: context tag for invalidation checking
- `created`: ISO date

## Commands

### `/learn` — show learnings for this project

```bash
~/.claude/skills/praxis/bin/praxis-learn list 2>/dev/null || \
.claude/skills/praxis/bin/praxis-learn list 2>/dev/null || true
```

Display learnings grouped by type. For each, show content, confidence, valid_for,
and created date. If no learnings exist, say "No learnings stored for this project yet."

### `/learn search <term>` — search across all projects

```bash
~/.claude/skills/praxis/bin/praxis-learn search "TERM" 2>/dev/null || \
.claude/skills/praxis/bin/praxis-learn search "TERM" 2>/dev/null || true
```

Show matches with project name and relevance. Cross-project learnings are valuable
when starting a new study on the same dataset or condition.

### `/learn add` — manually add a learning

Ask the user for:
1. What did you learn? (the content)
2. What type? (dataset-gotcha / definition-pitfall / statistical-trap / clinical-insight / user-stated)
3. How confident are you? (1-10)
4. What makes this true? (the valid_for tag — dataset version, PMID, or "permanent")

Construct the JSON and save:

```bash
~/.claude/skills/praxis/bin/praxis-learn add '{"id":"ID","type":"TYPE","content":"CONTENT","confidence":N,"source":"manual","project":"PROJECT","valid_for":"TAG","created":"DATE"}' 2>/dev/null || \
.claude/skills/praxis/bin/praxis-learn add '{"id":"ID","type":"TYPE","content":"CONTENT","confidence":N,"source":"manual","project":"PROJECT","valid_for":"TAG","created":"DATE"}' 2>/dev/null || true
```

Substitute all values. Generate a short descriptive ID (e.g., `labevents-specimen-types`).

### `/learn prune` — remove stale or wrong learnings

Show all learnings with their IDs. Ask the user which to remove.

```bash
~/.claude/skills/praxis/bin/praxis-learn prune "ID" 2>/dev/null || \
.claude/skills/praxis/bin/praxis-learn prune "ID" 2>/dev/null || true
```

## How reviews use learnings

Review skills load learnings in Step 0 and inject relevant ones into dimensional
scoring. The mapping:

| Learning type | Review skill | Dimension(s) |
|--------------|-------------|-------------|
| dataset-gotcha | plan-ds-review | Dim 1 (Data Understanding), Dim 3 (Harmonization) |
| definition-pitfall | plan-pi-review | Step 1.5 (Definition Audit), Dim 4 (Methodological Soundness) |
| statistical-trap | plan-ds-review | Dim 4 (Cohort & Bias), Dim 5 (Feature Engineering) |
| clinical-insight | plan-clinical-review | Dim 1 (Face Validity), Dim 5 (Safety) |
| clinical-insight | plan-ai-review | Dim 4 (Fairness) |
| user-stated | all | whichever dimension the preference applies to |

When a learning is applied, the review says:
"Prior learning applied: [content] (confidence X/10, from [date])"

When a learning's `valid_for` context doesn't match the current project context,
the review says:
"Prior learning (verify): [content] — observed on [valid_for], current context is [X]"
