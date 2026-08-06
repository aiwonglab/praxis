# praxis

A research scaffold for clinical AI and data science. Built by a clinician-researcher,
for clinician-researchers — whether you write Python daily or are just getting started.

Praxis is early. It's a tested starting point for the repetitive parts of clinical
data science: cohort definitions, extraction pipelines, analysis scaffolding, and
structured review of study design. It won't replace your biostatistician or your ML
collaborator. It's meant to make your time with them more effective.

> This is not a finished product. It's a practice — opinionated, reproducible,
> and designed to compound across studies.

## Install — 30 seconds

**Requirements:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/)

### Step 1: Install on your machine

Open Claude Code and paste this. Claude does the rest.

> Install praxis: run **`git clone https://github.com/aiwonglab/praxis.git ~/.claude/skills/praxis && cd ~/.claude/skills/praxis && bash scripts/setup.sh`** then add a "praxis" section to CLAUDE.md that lists the available skills: /plan-pi-review, /plan-ds-review, /plan-ai-review, /plan-clinical-review, /praxis-learn, and notes to read ETHOS.md for foundational principles. Then ask the user if they also want to add praxis to the current project so collaborators get it.

### Step 2: Add to your repo so collaborators get it (optional)

> Add praxis to this project: run **`cp -Rf ~/.claude/skills/praxis .claude/skills/praxis && rm -rf .claude/skills/praxis/.git && cd .claude/skills/praxis && bash scripts/setup.sh`** then add a "praxis" section to this project's CLAUDE.md that lists the available skills: /plan-pi-review, /plan-ds-review, /plan-ai-review, /plan-clinical-review, /praxis-learn, and tells Claude that if praxis skills aren't working, run `cd .claude/skills/praxis && bash scripts/setup.sh` to re-link them.

Real files get committed to your repo (not a submodule), so `git clone` just works. Everything lives inside `.claude/`. Nothing touches your PATH or runs in the background.

## See it work

```
You:    I want to build a sepsis phenotyping model using MIMIC-IV.
You:    /plan-pi-review

Claude: [Definition audit] You said "sepsis" — which definition?
        Sepsis-3 (organ dysfunction + suspected infection)?
        ICD-9/10 codes? A custom clinical phenotype?
        [scores 7 dimensions — question clarity, clinical significance,
         data feasibility, methods, scope, risk, collaboration readiness]
        [flags: no external validation plan, cohort definition too broad,
         unclear what "phenotyping" means here vs prediction]

        VERDICT: ITERATE — lock the sepsis definition (Sepsis-3),
        narrow to a specific ICU population, add an eICU validation
        arm before building the model.

You:    /plan-ds-review

Claude: [checks your data pipeline]
        [flags: chartevents timestamps arrive after your prediction
         window for 23% of cases — potential look-ahead bias]
        [checks MIMIC-IV → eICU harmonization: different vasopressor
         naming, different lab unit conventions]

        VERDICT: FIX — resolve the timestamp leakage before modeling.
        Harmonization layer needed for cross-dataset validation.

You:    /plan-ai-review

Claude: [reviews model choice, fairness across demographics,
         calibration plan, explainability approach]

You:    /plan-clinical-review

Claude: "So what? What do I do differently at 3 AM because this exists?"
        [assesses whether the phenotypes map to actionable clinical decisions]
```

Four reviews, each catching problems the others miss. The PI review catches scope and definition problems. The DS review catches data leakage. The AI review catches model and fairness issues. The clinical review catches "technically correct but clinically useless."

## Built on

Praxis is forked from [gstack](https://github.com/garrytan/gstack) by Garry Tan.
What was kept: the structured sprint workflow (code review, QA, shipping,
retrospectives) and the skill-based architecture. What was adapted: four original
review skills for clinical research (`/plan-pi-review`, `/plan-ds-review`,
`/plan-ai-review`, `/plan-clinical-review`), a data discipline for PHI-aware
EHR work, and an [ethos](ETHOS.md) grounded in clinical research rather than
startup velocity.

To pull upstream gstack improvements:

```bash
git fetch upstream
git merge upstream/main
```

## Current tooling

These are the current defaults, not doctrine. They'll evolve as the work demands.

- **Python 3.13+**, managed with **uv** (never pip)
- **polars / pandas** for tabular data, **pyarrow** for columnar interchange
- **DuckDB** for local analytical queries
- **Delta Lake** for multi-site data versioning (when needed)
- **Public data first**: MIMIC-IV, eICU, PhysioNet — prove it works here before
  touching institutional data. When no public dataset fits, build portable code anyway.
- **ruff** for formatting/linting, **pyright** for type checking, **pytest** for tests

## What's here

| Component | What it does |
|-----------|-------------|
| `/plan-pi-review` | PI-level research strategy audit. Scores 7 dimensions, GO / ITERATE / PIVOT / PAUSE verdict. |
| `/plan-ds-review` | Data pipeline and statistical rigor audit. Dataset-specific probes for MIMIC-IV, eICU, waveforms, DICOM. |
| `/plan-ai-review` | Model and fairness audit. Evaluates selection, methodology, fairness, explainability, deployment readiness. |
| `/plan-clinical-review` | Bedside validity and safety audit. Clinical actionability, workflow integration, population fit. |
| `/plan-deid-review` | De-identification and disclosure-risk audit. Inventories identifier surfaces, verifies the checks themselves. RELEASE / HOLD / REWORK. |
| `/praxis-learn` | View, add, search, and prune project learnings that feed the review skills. |
| Data discipline | No hardcoded paths. No PHI in logs. Reproducibility enforced by convention and tooling. |
| Dev workflow | Inherited from gstack — `/review`, `/qa`, `/ship`, `/investigate`, `/retro`, and more. |

## Principles

> Don't reinvent the wheel — and when you build a better one, make it reusable.

Our ethos and principles are in [ETHOS.md](ETHOS.md). The short version:

- **Novel methods on reproducible foundations** — boring foundations, clear novelty
- **Don't reinvent the wheel** — consensus definitions, existing phenotypes, published methods first
- **Bring cleaner starting points** — to collaborators, to the next study, to the field
- **Guardrails over warnings** — encode findings as assertions, not prose; prove each check fires
- **Compound internally, share when ready** — fast iteration within studies, share the artifact when it's ready

## Disclaimer

Praxis is a research scaffold. It is not a medical device, not FDA-cleared, and not
intended for clinical decision-making without independent validation and institutional
review. The MIT license applies — this software is provided as-is, without warranty,
and the authors are not liable for clinical outcomes.

---

Let's help patients together.
