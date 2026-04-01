---
name: iterate
version: 1.0.0
description: |
  Advance the research process. Detects what changed, checks for scope drift,
  routes to the right review skills, captures learnings, and logs progress.
  Use when asked to "iterate", "review progress", "checkpoint", or "what's next".
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /iterate

Advance the research process — the praxis equivalent of `/ship`.

You are not shipping code. You are advancing a research plan through its lifecycle.
Each iteration detects what changed, checks for drift, runs the right reviews,
captures learnings, and logs progress.

## Research lifecycle

```
PLANNING → REVIEWED → IMPLEMENTING → VALIDATING → REFINING → WRITING
    ↑                                                    |
    └────────────────────────────────────────────────────┘
```

`/iterate` is what moves you forward. The PI runs it when they've made progress
and want to checkpoint — after changing the plan, after building a pipeline,
after getting first results, after fixing something a review flagged.

---

## Step 0 — Update check

```bash
_UPD=$(~/.claude/skills/praxis/bin/praxis-update-check 2>/dev/null || .claude/skills/praxis/bin/praxis-update-check 2>/dev/null || true)
[ -n "$_UPD" ] && echo "$_UPD" || true
```
If `UPGRADE_AVAILABLE`: read praxis-upgrade SKILL.md and follow inline flow.
If `JUST_UPGRADED`: tell user and continue.

---

## Step 1 — Read current state

Gather context. Read all of these if they exist:

1. **Plan files**: `PLAN.md`, `plan-*.md`, `*.plan.md`, files in `plans/`
2. **Iteration log**: `ITERATIONS.md` — if none, this is iteration 1
3. **Prior review summaries**: look for review summary blocks in `ITERATIONS.md`
4. **Implementation artifacts**: code in `src/`, notebooks in `notebooks/`
5. **Results**: figures, tables, output files in `output/` or `results/`

```bash
# Detect iteration number
if [ -f ITERATIONS.md ]; then
  LAST_ITER=$(grep -c "^## Iteration" ITERATIONS.md 2>/dev/null || echo "0")
  NEXT_ITER=$((LAST_ITER + 1))
else
  NEXT_ITER=1
fi
echo "ITERATION: $NEXT_ITER"
```

Load learnings count:
```bash
_LEARN_COUNT=$(~/.claude/skills/praxis/bin/praxis-learn count 2>/dev/null || .claude/skills/praxis/bin/praxis-learn count 2>/dev/null || echo "0")
echo "LEARNINGS: $_LEARN_COUNT entries"
```

If this is iteration 1 and no plan file exists, ask the user for:
1. The research question (one sentence)
2. The proposed approach (2-3 sentences)
3. The target dataset(s)
4. The intended output (paper, tool, pilot, grant aim)

Do NOT proceed without a plan.

---

## Step 2 — Detect what changed

If this is iteration 1, skip to Step 3 (no prior state to diff against).

For iteration 2+, determine what changed since the last iteration:

```bash
# Find the commit tagged in the last iteration
LAST_TAG=$(grep "^### Version" ITERATIONS.md | tail -1 | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' || true)
if [ -n "$LAST_TAG" ]; then
  # Try to find the commit from git log
  LAST_COMMIT=$(git log --all --oneline --grep="$LAST_TAG" -1 --format="%H" 2>/dev/null || true)
fi
```

If no commit tag found, use the diff of recently modified files:
```bash
git diff --stat HEAD~10 2>/dev/null || git status --short
```

Classify what changed into categories:

| Change type | What to look for |
|------------|-----------------|
| **plan-change** | Modified PLAN.md, new/changed plan files |
| **data-change** | Modified data pipeline code, new data scripts, changed SQL |
| **model-change** | Modified model code, new model files, changed features |
| **results-new** | New output files, figures, tables |
| **fix-applied** | Changes that address a prior review finding |
| **definition-change** | Changed clinical definitions, thresholds, operationalizations |

State the classification. If ambiguous, list what you see and let the routing
logic in Step 4 handle it.

---

## Step 3 — Scope drift check

Compare current state against the plan. Look for:

**Scope creep** — work not in the plan:
- Analyses or features that weren't planned
- Additional datasets not mentioned in the plan
- Extra model variants beyond what was specified

**Scope gap** — planned work not yet done:
- Planned analyses not yet implemented
- Specified sensitivity analyses not started
- External validation not addressed

**Definition drift** — clinical definitions changed without review:
- Thresholds modified since last PI review
- New operationalizations introduced
- Inclusion/exclusion criteria altered

If drift is detected, surface the top 2-3 items via `AskUserQuestion`. Each
question should include what the plan says, what the current state is, and whether
the change is intentional.

If no drift detected, state "Scope check: on track" and proceed.

---

## Step 4 — Route to reviews

Based on what changed (Step 2), decide which reviews to run:

| What changed | Review to run | Why |
|---|---|---|
| Plan updated | plan-pi-review | Question/scope may have shifted |
| Data source or pipeline | plan-ds-review | Harmonization, cohort, leakage |
| Model or features | plan-ai-review | Selection, fairness, evaluation |
| Results are in | plan-clinical-review | Face validity, actionability |
| Definition changed | plan-pi-review (Step 1.5 only) | Definition audit |
| Fix applied to prior finding | Re-score affected dimension only | Verify fix resolved the issue |
| Iteration 1 (new plan) | plan-pi-review (full) | First-pass strategic review |

**Routing rules:**
- If multiple reviews needed, run in dependency order: PI → DS → AI → Clinical
- If a review gives a blocking verdict (REDESIGN, PIVOT, PAUSE, REFRAME, PREMATURE),
  stop and surface the blocker — don't run downstream reviews
- For "fix applied" changes, don't re-run the entire review — re-score only the
  affected dimension(s) and update the finding's status

**Invoking reviews** (composable skill convention from CLAUDE.md):
Read the target review's SKILL.md. Skip Step 0 (update check and context gathering
are already done). Follow remaining steps using the plan and data context from
this session. Return here when done.

If the review only needs a subset (e.g., definition audit only), specify:
"Read plan-pi-review/SKILL.md Step 1.5 only."

Before running reviews, tell the user what you're about to do:
"Based on [what changed], running [review name(s)]. This will [what it checks]."

If no review is needed (e.g., only documentation changes), skip to Step 4.5.

---

## Step 4.5 — Build & verify

If implementation artifacts changed (code in `src/`, pipeline scripts, notebooks),
run the project's build checks. Read CLAUDE.md for the exact commands. Default:

```bash
uv run ruff format . 2>&1 | tail -5
uv run ruff check . --fix 2>&1 | tail -10
uv run pyright 2>&1 | tail -10
uv run pytest 2>&1 | tail -20
```

**Routing:** Only run checks relevant to what changed:
- Code formatting/linting: always if any `.py` file changed
- Type checking: if function signatures, imports, or type hints changed
- Tests: if any code in `src/` or `tests/` changed

**If tests fail:**
- Classify as in-branch (caused by this iteration's changes) or pre-existing
- In-branch failures: surface via `AskUserQuestion` — fix now or defer?
- Pre-existing failures: note them, don't block the iteration

**If no code changed** (plan-only iteration, definition changes): skip entirely.

Output: `Build: [pass / N issues] | Tests: [pass / N failures (X in-branch, Y pre-existing)]`

---

## Step 5 — Capture learnings

After reviews complete (or if no reviews needed), check for learnable moments:

1. **High-confidence findings (8+)** that the user confirmed or acted on →
   capture as learnings
2. **Surprising data behavior** discovered during the iteration →
   capture as dataset-gotcha
3. **Definition decisions** made during the iteration →
   capture as user-stated
4. **Statistical traps** discovered →
   capture as statistical-trap

Batch proposed learnings into a single `AskUserQuestion`:
"These findings could help future projects. Save as learnings?"

Show each proposed learning with its type and valid_for tag. The user can
accept all, select individually, or decline.

For accepted learnings, save via praxis-learn:
```bash
~/.claude/skills/praxis/bin/praxis-learn add 'JSON' 2>/dev/null || \
.claude/skills/praxis/bin/praxis-learn add 'JSON' 2>/dev/null || true
```

If no learnable moments, skip silently.

---

## Step 6 — Update iteration log

Append to `ITERATIONS.md` (create if it doesn't exist):

```markdown
## Iteration N — YYYY-MM-DD

**Trigger:** [what the user changed or why they ran /iterate]
**Changes:** [categorized list from Step 2]

### Scope check
[On track / drift findings from Step 3]

### Reviews run
- [review-name]: [VERDICT] ([avg score], [change from prior iteration if applicable])
  - [dimension]: [score] ([change note if re-scored])

### Key findings
| Finding | Confidence | Status |
|---------|-----------|--------|
| [from review] | X/10 | [open / resolved / deferred] |

### Learnings captured
- [type] [content] (confidence X)

### Decisions made
- [decisions from AskUserQuestion interactions during this iteration]

### Next actions
- [ ] [concrete next steps based on review verdicts and findings]

### Version
vX.Y.Z.W
```

If `ITERATIONS.md` already exists, compare findings from this iteration against
prior iterations. Note which findings are new, which resolved, and which persisted.

---

## Step 7 — Version bump

Follow the versioning rules from CLAUDE.md:
- MICRO for small iterations (< 50 lines changed, re-scoring a dimension)
- PATCH for significant methodology changes (new data source, definition change)
- MINOR/MAJOR: ask user

Update both `VERSION` and `pyproject.toml`.

---

## Summary output

After all steps, output a concise summary:

```
## Iteration N Summary

**Trigger:** [what changed]
**Scope:** [on track / N drift items flagged]
**Reviews:** [which ran, verdicts]
**Findings:** [N total — X high, Y medium, Z low]
**Learnings:** [N captured]
**Version:** vX.Y.Z.W
**Next:** [top 1-2 actions]
```
