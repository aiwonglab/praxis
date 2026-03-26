# praxis

A research scaffold for trustworthy clinical AI. Built by a clinician-researcher,
for clinician-researchers — whether you write Python daily or are just getting started.

Praxis is early. It's a tested starting point for the repetitive parts of clinical
data science: cohort definitions, extraction pipelines, analysis scaffolding, and
structured review of study design. It won't replace your biostatistician or your ML
collaborator. It's meant to make your time with them more effective.

> This is not a finished product. It's a practice — opinionated, reproducible,
> and designed to compound across studies.

**Note:** The repository directory is still named `aidsmedstack`. It will be renamed
once git remotes are updated.

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
| Data discipline | No hardcoded paths. No PHI in logs. Reproducibility enforced by convention and tooling. |
| Dev workflow | Inherited from gstack — `/review`, `/qa`, `/ship`, `/investigate`, `/retro`, and more. |

## Principles

> Don't reinvent the wheel — and when you build a better one, make it reusable.

Our ethos and principles are in [ETHOS.md](ETHOS.md). The short version:

- **Novel methods on reproducible foundations** — boring foundations, clear novelty
- **Don't reinvent the wheel** — consensus definitions, existing phenotypes, published methods first
- **Bring cleaner starting points** — to collaborators, to the next study, to the field
- **Compound internally, share when ready** — fast iteration within studies, share the artifact when it's ready

## Disclaimer

Praxis is a research scaffold. It is not a medical device, not FDA-cleared, and not
intended for clinical decision-making without independent validation and institutional
review. The MIT license applies — this software is provided as-is, without warranty,
and the authors are not liable for clinical outcomes.

---

Let's help patients together.
