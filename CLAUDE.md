# aidsmedstack development

## Identity

You are helping a physician-researcher (PI) build trustworthy clinical AI and
data science tools for critical care and pulmonary medicine. Collaborators are
co-investigators, not employees. This is a research scaffold, not a product.

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
aidsmedstack/
├── CLAUDE.md              # this file — meta-instructions for Claude Code
├── agents.md              # agent roles, review skills, future expansion
├── .gitignore             # Python + data science ignores
├── pyproject.toml         # project metadata
├── README.md              # one-paragraph description
├── plan-pi-review/
│   └── SKILL.md           # PI-level research strategy audit
├── plan-ds-review/
│   └── SKILL.md           # data pipeline, harmonization & stats audit
├── scripts/
│   └── setup.sh           # environment setup (placeholder)
└── src/
    └── aidsmedstack/
        └── __init__.py    # package root
```

## Data discipline

- **Public first**: Always prove on public data (MIMIC-IV, eICU, PhysioNet) before
  touching institutional data.
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

## AskUserQuestion — always confirm before acting on

Before executing any task that involves:

- **Cohort definition choices** (inclusion/exclusion criteria, time windows)
- **Dataset selection** (MIMIC-IV vs eICU vs institutional)
- **File deletion or overwrite** of any existing work
- **Package installation** (always ask before `uv add`)
- **Schema changes** to any data pipeline

...ask the user to confirm rather than assuming. Researchers need interactive
clarification before acting on ambiguous tasks.

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
