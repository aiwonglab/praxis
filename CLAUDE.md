# praxis development

## Identity

You are helping a physician-researcher build PRAXIS — a methodology and scaffold
for trustworthy clinical AI. This is not a web app. It is a research practice.
The user is a PI. Collaborators are co-investigators. There is no CEO.

Read `ETHOS.md` for foundational principles. Apply them when making decisions
about definitions, data pipelines, validation, and code architecture.

## Commands

```bash
uv run pytest                # run tests
uv run ruff format .         # format code
uv run ruff check . --fix    # lint + autofix
uv run pyright               # type checking
```

## Tech stack

- **Language**: Python 3.13+
- **Package manager**: UV only. Never pip.
- **Core libraries** (when added): polars, pandas, pyarrow, scikit-learn, delta-lake
- **Testing**: pytest + anyio for async
- **Formatting/linting**: ruff (88 char lines, PEP 8)
- **Type checking**: pyright

## Project structure

```
praxis/
├── CLAUDE.md              # this file — meta-instructions for Claude Code
├── AGENTS.md              # agent roles, review skills, future expansion
├── ETHOS.md               # 4 ethos + 3 principles — shared decision framework
├── .gitignore             # Python + data science ignores
├── pyproject.toml         # project metadata
├── README.md              # project overview
├── plan-pi-review/
│   └── SKILL.md           # PI-level research strategy audit
├── plan-ds-review/
│   └── SKILL.md           # data pipeline, harmonization & stats audit
├── plan-ai-review/
│   └── SKILL.md           # model selection, fairness & explainability audit
├── plan-clinical-review/
│   └── SKILL.md           # bedside validity, safety & actionability audit
├── scripts/
│   └── setup.sh           # environment setup (placeholder)
└── src/
    └── praxis/
        └── __init__.py    # package root
```

## Data discipline

- **Public first when possible**: Prove on public data (MIMIC-IV, eICU, PhysioNet) when a
  public dataset fits the question. When it doesn't, build pipelines so logic is testable
  and portable even if the data can't be shared.
- **No hardcoded paths**: Use environment variables or config files for all file paths.
- **Data is sensitive**: Never log PHI. Never commit data files. Never print patient
  identifiers in error messages or logs.
- **Reproducibility**: Pin random seeds. Document data versions. Track preprocessing steps.

## Code philosophy

- Small, testable functions over large notebooks.
- Notebooks are for exploration only. Production logic lives in `src/`.
- Write the test before the function when working on cohort logic.
- Type hints required for all code. Public APIs must have docstrings.
- PEP 8 naming: `snake_case` for functions/variables, `PascalCase` for classes,
  `UPPER_SNAKE_CASE` for constants.
- Prefer functional, immutable approaches when not verbose.
- Use early returns to avoid nested conditions.
- DRY: use arguments/variables, not hardcoded values.

## Search before building

Before designing any solution involving unfamiliar patterns or libraries:

1. Search for "{library} {thing} built-in"
2. Search for "{thing} best practice {current year}"
3. Check official docs

Three layers of knowledge: tried-and-true (use it), new-and-popular (scrutinize it),
first-principles (prize it above all). The best research code avoids reinventing
wheels while making original observations about the problem.

## Interaction discipline

### When to ask

Always confirm before acting on:

- **Cohort definition choices** (inclusion/exclusion criteria, time windows)
- **Dataset selection** (MIMIC-IV vs eICU vs institutional)
- **File deletion or overwrite** of any existing work
- **Package installation** (always ask before `uv add`)
- **Schema changes** to any data pipeline

Researchers need interactive clarification before acting on ambiguous tasks.

### How to ask

- **Use AskUserQuestion for decisions** — don't bury them in long prose. If a
  response contains a decision point, it should be an AskUserQuestion, not a
  paragraph that ends with "what do you think?"
- **3 or fewer decisions per interaction.** If you have more, batch into
  sequential rounds. Don't overwhelm.
- **Each question should be self-contained.** The user shouldn't need to re-read
  the preceding output to answer. Put the context in the question itself.
- **Lead with the decision after long analysis.** If you've written a long
  exploration, put the AskUserQuestion first, or immediately after the summary —
  not buried at the bottom.

### When NOT to ask

- Low-stakes, reversible choices — just do them and mention what you chose
- Decisions the user already authorized in this session
- Things covered by CLAUDE.md rules or ETHOS.md principles — follow the rule

## Package management

- **ONLY use uv**, NEVER pip
- Installation: `uv add package`
- Running tools: `uv run tool`
- Upgrading: `uv add --dev package --upgrade-package package`
- **FORBIDDEN**: `uv pip install`, `@latest` syntax

## Testing requirements

- Framework: `uv run pytest`
- Async testing: use anyio, not asyncio
- Coverage: test edge cases and errors
- New features require tests
- Bug fixes require regression tests
- Cohort logic requires tests BEFORE implementation

## Error resolution — CI fix order

1. Formatting: `uv run ruff format .`
2. Type errors: `uv run pyright`
3. Linting: `uv run ruff check . --fix`

## Versioning — MAJOR.MINOR.PATCH.MICRO

VERSION file is the source of truth. Keep pyproject.toml in sync.

| Digit | When to bump | Auto-decide? |
|-------|-------------|-------------|
| **MICRO** (4th) | < 50 lines changed — typos, config, small refinements | Yes |
| **PATCH** (3rd) | 50+ lines — bug fixes, small-medium features | Yes |
| **MINOR** (2nd) | Major features, new skills, architectural changes | Ask user |
| **MAJOR** (1st) | Milestones, breaking changes to skill structure | Ask user |

Bumping any digit resets all digits to its right to 0.
Bump at ship time, not per-commit during development.

## Commit style

Every commit should be a single logical change. When you've made multiple changes,
split them into separate commits. Each commit should be independently understandable
and revertable.

## What NOT to do

- Do not install packages without asking first.
- Do not create files outside the project structure above.
- Do not add complexity layers (ORMs, frameworks, abstractions) that aren't needed yet.
- Do not commit data files, credentials, or environment files.
- Do not hardcode file paths, patient IDs, or institutional details.
- Do not create separate scripts for different sample sizes — parameterize.
- Do not skip tests for cohort logic.
- Do not create documentation files unless explicitly requested.

## Iterative building

Start with minimal functionality and verify it works before adding complexity.
When in doubt, do less. We iterate.
