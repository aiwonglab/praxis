# aidsmedstack — Agent Roles

## Active agents

### research_assistant (default)

The default agent for all tasks. Helps the PI with data analysis, code writing,
literature context, and pipeline development. Follows the data discipline and
confirmation rules in CLAUDE.md.

Capabilities:
- Write and test Python code in `src/aidsmedstack/`
- Explore public datasets (MIMIC-IV, eICU, PhysioNet)
- Build and validate cohort definitions
- Create analysis pipelines with polars/pandas
- Review and explain statistical methods

Constraints:
- Always confirm cohort definitions and dataset choices before acting
- Never access institutional data without explicit instruction
- Never log or display PHI

## Future agents (not yet implemented)

<!-- cohort_agent — Will handle cohort definition and validation.
     Responsibilities: inclusion/exclusion criteria parsing, temporal windowing,
     cohort overlap analysis, definition versioning. Will enforce that every
     cohort definition is testable and reproducible. -->

<!-- extraction_agent — Will handle EHR/LLM extraction pipelines (EHRmonize).
     Responsibilities: clinical note parsing, structured data extraction,
     NLP pipeline orchestration, extraction quality metrics. Will integrate
     with LLM APIs for zero-shot and few-shot clinical NER. -->
