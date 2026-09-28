# praxis — Agent Roles

## Active agents

### research_assistant (default)

The default agent for all tasks. Helps the PI with data analysis, code writing,
literature context, and pipeline development. Follows the data discipline and
confirmation rules in CLAUDE.md.

Capabilities:
- Write and test Python code in `src/praxis/`
- Explore public datasets (MIMIC-IV, eICU, PhysioNet)
- Build and validate cohort definitions
- Create analysis pipelines with polars/pandas
- Review and explain statistical methods

Constraints:
- Always confirm cohort definitions and dataset choices before acting
- Never access institutional data without explicit instruction
- Never log or display PHI

## Review skills

| Skill | Status | What it does |
|-------|--------|-------------|
| `/plan-pi-review` | **Active** | PI-level research strategy audit. Scores 7 dimensions, interactive. |
| `/plan-ds-review` | **Active** | Data pipeline, harmonization, stats & reproducibility audit. |
| `/plan-ai-review` | **Active** | Model selection, fairness, explainability, generalizability audit. |
| `/plan-clinical-review` | **Active** | Bedside validity, safety, actionability, workflow integration audit. |
| `/plan-deid-review` | **Active** | De-identification & disclosure-risk audit. Run before data crosses any boundary. |
| `/plan-protocol` | **Active** | Regulatory audit and IRB protocol drafting for investigator-sponsored studies. Idea to submittable protocol, plus a scope lock the pipeline asserts against. |

## Review chain protocol

### Execution order

```
plan-pi-review → plan-protocol → plan-ds-review → plan-ai-review → plan-clinical-review
"Right question?"  "Allowed to    "Right data?"     "Right model?"   "Right at bedside?"
                    ask it?"

plan-deid-review — runs on the data-movement axis, not this chain
"Safe to move?"
```

`/plan-protocol` sits between the science and the data because that is the only
place it can sit. A protocol can be revised after the science settles; a pull
cannot be retroactively authorized. It runs once PI review returns GO or ITERATE,
and again whenever the cohort, window, site list, element list, or intended *use*
changes.

`/plan-deid-review` is not a stage in the chain. It gates *movement* rather than
progress: run it whenever data crosses a boundary, and re-run it on every batch,
because the method that was complete for the last export is only a hypothesis
about the next one. `/plan-protocol` Step 2a hands its egress hop to it directly.

**Sequential within a thread**: PI must pass before protocol drafting. The
protocol must reach SUBMIT or a documented determination before DS runs on
institutional data. DS must pass before AI runs. Clinical review runs last.

**Parallel across independent threads**: Threads with no data/outcome dependencies
can run their review chains concurrently.

### Handoff: structured summary as artifact

Each skill writes a structured summary block at the end. The next skill in the
chain should read prior summaries for context. Convention: if writing to files,
use `reviews/{thread-name}-{skill}.md` (e.g., `reviews/hidden-hypoxemia-pi.md`).

### Dependency map for current research threads

```
Thread 1 (phenotyping) ──→ Thread 2 (prediction)
     │                         │
     │  (phenotypes define      │  (prediction targets
     │   the endotypes)         │   come from phenotypes)
     │                         │
Thread 3 (LLM extraction) ──────────→ Thread 4 (multimodal)
     (independent, can              (needs data infrastructure
      run in parallel)               from 1-3, runs last)
```

### Skip rules

- Descriptive studies with standard statistics: may skip plan-ai-review
- Research-enabling tools (extraction, infrastructure): clinical review uses
  the "Monday morning" test instead of the 3 AM test
- If PI review says PAUSE: stop. Resolve the blocker before downstream reviews.
- `/plan-protocol` may be skipped only for work entirely on public de-identified
  data under an existing DUA — and even then run Step 1 Gate B, because the DUA
  is what binds you, and Step 2d, because grant preliminary data and operational
  hand-offs are uses the DUA may not cover.
- If plan-protocol says HOLD because data was already pulled outside an approved
  scope: stop and route it through the institution. That is not a finding to fix
  quietly.
- `/plan-deid-review` has no skip rule. Public-data-only work still has an
  identifier surface — figures, filenames, and notebook outputs all leave.

## Future skills

| Skill | Purpose | When to build |
|-------|---------|---------------|
| `/plan-irb-review` | Reviewer-side audit of a submitted or approved protocol and its ongoing conduct — the late-stage counterpart to `/plan-protocol`, the way `/review` is the late-stage counterpart to a plan review. Reads the protocol, the pipeline, and the deviations log together. | When the first protocol has been approved and the cohort is being built against it |
| `/plan-program-review` | Multi-project coherence review — do the threads form a fundable program (R01, K-award)? Evaluate narrative arc, dependency sequencing, and portfolio balance. | When preparing a grant application or annual review |
| `/office-hours` | Research hypothesis brainstorm — pre-PI-review ideation for new threads | When exploring whether a question is worth pursuing |

## Long-term learning: MD-based project memory

Review skills produce structured artifacts. Over time, these accumulate into a
learning corpus that makes future reviews sharper. Three layers, built iteratively:

### Layer 1 — Review artifacts (MVP, build when first review runs)
`reviews/{thread}-{skill}.md` — point-in-time structured summaries.
Accumulate naturally as skills are invoked. Prior summaries are context for
the next skill in the chain.

### Layer 2 — Decision log (build when first non-obvious decision is made)
`decisions/` — capture the *why* behind pivots, scope changes, and method choices.
Written by the PI (or prompted by the assistant) when a non-obvious call is made.
Format: date, decision, rationale, alternatives considered, what would change the decision.

### Layer 3 — Lessons learned (build after first completed review cycle)
`lessons/` — project-specific knowledge that should influence future reviews.
Things discovered during data exploration, modeling, or validation that aren't
obvious from the code or literature. Feed back into review skills as
project-specific anti-patterns and probes.

<!-- TODO: plan-program-review should read all three layers to assess
     multi-project coherence and narrative arc for grants -->

<!-- TODO: Consider whether lessons/ should be auto-prompted after each
     review cycle: "Did this review surface anything surprising that
     future reviews should check for?" -->

## Future agents (not yet implemented)

<!-- cohort_agent — Will handle cohort definition and validation.
     Responsibilities: inclusion/exclusion criteria parsing, temporal windowing,
     cohort overlap analysis, definition versioning. Will enforce that every
     cohort definition is testable and reproducible. -->

<!-- extraction_agent — Will handle EHR/LLM extraction pipelines (EHRmonize).
     Responsibilities: clinical note parsing, structured data extraction,
     NLP pipeline orchestration, extraction quality metrics. Will integrate
     with LLM APIs for zero-shot and few-shot clinical NER. -->
