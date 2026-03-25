# aidsmedstack

> I spend a lot of my research time sorting through problems that are mostly the same, just slightly tweaked. Different cohort, different outcome, different dataset — but the same data cleaning, the same inclusion/exclusion logic, the same pipeline scaffolding. I built aidsmedstack to stop reinventing that work and start compounding it.

I'm a pulmonary and critical care physician at Duke. My research lives in EHR data science — harmonizing electronic health records across sites, building NLP pipelines for radiology reports, running clinical studies and a multi-site trial. The work is equal parts clinical reasoning and data engineering, and the engineering side has been too slow for too long.

**aidsmedstack is a research scaffold for clinical data science.** It's a tested, extensible starting point for the work clinician-researchers actually do: defining cohorts, extracting structured data from clinical notes, building reproducible analysis pipelines, and validating models before anyone trusts them at the bedside.

**This won't replace your biostatistician or your ML collaborator.** It's meant to make your time with them more effective. If you can bring a clean, tested, reproducible cohort definition to your first meeting instead of a messy notebook — that meeting goes differently. If your extraction pipeline has tests and runs on public data — your collaborator can actually build on it.

**This is not a finished product.** It's a frame for exploration. The best clinical data science tools will come from clinician-researchers who understand both the clinical questions and the data — working together, iterating in the open. Come build with us.

## Why this exists

If you've done EHR-based research, you've lived this:

- You define a cohort for one study, then redefine something nearly identical for the next — from scratch
- Your extraction pipeline works on MIMIC-IV but breaks when you try eICU or institutional data
- You spend weeks on data cleaning and pipeline plumbing before you can even ask your research question
- Your analysis code lives in a notebook that only you can run, and only on a good day
- You evaluate a model on discrimination alone because the validation infrastructure for calibration, fairness, and clinical workflow analysis doesn't exist in your codebase

These aren't hard problems individually. They're repetitive problems that compound into months of lost time across projects. aidsmedstack captures the patterns so you can focus on the science.

## Who this is for

- **Clinician-researchers** running EHR-based studies who want tested, reusable scaffolding — whether you write Python daily or are just getting started
- **Clinical data science teams** that want shared infrastructure instead of one-off scripts per project
- **Research trainees** who want a tested starting point for their first clinical data science project
- **Anyone** who believes clinical AI needs more rigor in the engineering, not just the modeling

## What's here today

This is early. Here's what exists and what's coming:

### Active

| Component | What it does |
|-----------|-------------|
| **Research stack** | Python environment with dependency management, type checking, linting, and testing built in. Ready for polars, pandas, scikit-learn. |
| **`/plan-pi-review`** | PI-level research strategy audit. Scores your plan across 7 dimensions — question clarity, clinical significance, data feasibility, methods, scope, risk, collaboration readiness. Interactive: walks through each dimension with you before giving a GO / ITERATE / PIVOT / PAUSE verdict. |
| **Data discipline** | Public data first (MIMIC-IV, eICU, PhysioNet). No hardcoded paths. No PHI in logs. Reproducibility enforced by convention and tooling. |
| **Development workflow** | Inherited from [gstack](https://github.com/garrytan/gstack) — structured sprint skills for code review, QA, shipping, debugging, and retrospectives. |

### Planned

| Component | What it will do |
|-----------|----------------|
| **`/plan-ds-review`** | Data pipeline and statistical rigor review |
| **`/plan-ai-review`** | Model selection, fairness, explainability review |
| **`/plan-clinical-review`** | Bedside validity, safety, actionability review |
| **Cohort builder** | Reusable cohort definitions — inclusion/exclusion parsing, temporal windowing, version tracking, and tests that travel with the definition |
| **Extraction pipelines** | Structured data from clinical notes — clinical NER, LLM-based extraction, rule-based fallbacks |

## The research sprint

Clinical data science projects follow a rhythm. aidsmedstack gives each phase structure:

**Question → Review → Build → Validate → Ship → Reflect**

| Phase | What happens |
|-------|-------------|
| **Question** | Define the research question. Identify the gap. Clarify the clinical scenario. |
| **PI Review** | Score the plan across 7 dimensions. Catch strategic errors — wrong question, infeasible data, scope mismatch — before you write code. |
| **Architecture** | Lock in data flow, pipeline structure, and evaluation strategy. |
| **Build** | Write the cohort logic, extraction pipeline, and analysis code — with tests. |
| **Review** | Catch bugs and logic errors before they reach your results. |
| **Validate** | Test on held-out data. Check calibration. Run fairness analysis. |
| **Ship** | Clean commit history. Reproducibility checklist. Shareable code. |
| **Reflect** | What worked, what didn't, what to try next. |

Each phase catches problems that are expensive to find later. The PI review catches scope problems before you build. The code review catches pipeline bugs before you validate. The validation catches model problems before you write the paper.

## Getting started

**If you're technical:**

```bash
git clone https://github.com/aiwonglab/aidsmedstack.git
cd aidsmedstack
uv sync              # set up Python environment
uv run pytest        # verify everything works
```

**If you're less technical or just exploring:**

1. Clone this repo and open it in a [devcontainer](https://containers.dev/) — the environment sets itself up
2. Start a conversation with Claude Code and describe your research question
3. Run `/plan-pi-review` to get structured feedback on your study design
4. Build iteratively from there — you don't need to know the whole stack on day one

## How to extend

aidsmedstack is designed to be forked and adapted:

- **Add a cohort definition** for your population of interest — with tests, so the next researcher can verify it
- **Build an extraction pipeline** for your note type (radiology, discharge summaries, operative notes)
- **Adapt `/plan-pi-review`** for your domain — cardiology, oncology, surgery all have different review priorities
- **Port a pipeline** from MIMIC-IV to eICU or your institutional data
- **Add validation tooling** — calibration plots, fairness metrics, subgroup analysis

The pattern: start on public data, test thoroughly, then adapt for your institution. PRs welcome — especially if they make the scaffold more general without adding complexity.

## Philosophy

**Public data first.** Prove everything on MIMIC-IV, eICU, or PhysioNet before touching institutional data. This isn't just convenience — it's reproducibility. If your pipeline only works behind your IRB, no one can verify or extend it.

**Test before you trust.** Cohort logic gets tests before implementation. Every bug fix gets a regression test. Clinical data science is high-stakes — "it worked when I ran it" is not a standard.

**Iterate, don't over-engineer.** Start with the minimum viable analysis. Get a result. Then extend. Three similar functions are better than a premature abstraction that doesn't fit the next dataset.

**Make your team's time count.** The goal is to walk into your collaborator meeting with a clean, tested, reproducible starting point — not a finished product, but something real enough to build on together. Your biostatistician shouldn't have to debug your data cleaning. Your ML colleague shouldn't have to guess what your cohort definition means.

## Upstream

aidsmedstack builds on [gstack](https://github.com/garrytan/gstack). All gstack development workflow skills are available here. To pull upstream improvements:

```bash
git fetch upstream
git merge upstream/main
```

## Contributing

This is an open exploration. If you're a clinician-researcher, clinical data scientist, or anyone who cares about making EHR-based research more rigorous and reproducible — come build with us.

- **Try it** — run `/plan-pi-review` on your next research idea
- **Break it** — file an issue when something doesn't fit your workflow
- **Extend it** — submit a PR when you build something reusable
- **Fork it** — make it yours for your institution or specialty

We're not trying to be perfect. We're trying to be useful, tested, and honest about what works. The best version of this will be shaped by the people who use it.

---

Let's help patients together.
