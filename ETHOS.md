# aidsmedstack ethos

> Don't reinvent the wheel — and when you build a better one, make it reusable.

This document shapes how aidsmedstack skills make decisions. It's a living
document — expect it to evolve as we learn what works.

---

## Ethos

### 1. Novel methods on reproducible foundations

The foundation should be boring: consensus definitions, tested pipelines,
documented preprocessing. The novel contribution should be clear and isolated.
When the foundation is reproducible, the novelty is evaluable. When it's not,
neither is the novelty.

### 2. Don't reinvent the wheel

Use consensus definitions (Sepsis-3, Berlin ARDS, KDIGO AKI) when they exist.
Check phenotype libraries (OHDSI, PheKB) and published methods before building.
When you deviate from the standard, document why and sensitivity-test against it.

### 3. Bring cleaner starting points

To your collaborators, to your next study, to the field. Your biostatistician
shouldn't debug your data cleaning. Your next project shouldn't start from a
blank notebook. Everything you build should be an artifact someone else can
pick up.

### 4. Compound internally, share when ready

Within a study: fast iteration cycles — question, build, review, refine.
Between studies: each study's cohort definitions, extraction pipelines, and
validation tooling feed the next. Share the artifact when the work is ready —
code with the paper, methods with the community. Not forced, not premature.

---

## Principles

These are the operational rules that implement the ethos above. Skills reference
these during execution.

### Definitions before conclusions

Explore data freely. Lock definitions before primary analysis. Document which
definition, document why. When multiple standards exist (and they often do),
pick one and sensitivity-test alternatives.

*Anti-patterns:* SQL that implicitly defines sepsis without citing a standard.
Choosing the definition that gives the biggest cohort without justification.
Different definitions across studies in the same research program without
acknowledging the deviation.

### Search the landscape

Before building a cohort definition, extraction pipeline, or validation
framework — check what exists. Phenotype libraries (OHDSI, PheKB), published
extraction methods, public repos. The search reveals what to reuse and where
the actual gaps are. Reusable clinical data science code is rare — that's the
gap we're filling.

*Anti-patterns:* Building a custom NER pipeline when scispaCy handles the
entity type. Writing a new MIMIC-IV sepsis cohort when three published ones
exist. Skipping the search because "our approach is different."

### Portable code, honest validation

Separate data access from analysis logic so the code travels between datasets
and institutions. Be explicit about what validation proves — MIMIC-IV is
single-center development data, not external validation. Public data is for
building and debugging. Don't let "validated on public data" do more
rhetorical work than it deserves.

*Anti-patterns:* Hardcoded SQL paths that only work on one MIMIC extract.
Analysis logic interleaved with data loading so nothing is reusable.
"Externally validated" when the external dataset is also public, also US,
also ICU.
