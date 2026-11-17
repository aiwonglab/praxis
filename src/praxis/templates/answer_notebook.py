# %% [markdown]
# # {{TITLE}}
#
# **Question:** {{QUESTION}}
#
# Effort: **{{EFFORT}}** · Dataset: {{DATASET_NOTE}} · Created {{CREATED}} by
# praxis {{VERSION}}
#
# One template for every effort level: the same sections in the same order.
# A level fills what it runs and marks the rest. To make this rigorous, change
# `effort` in the spec cell and fill the sections marked *not run*; the numbers
# do not move, because every level uses the same definitions and metric code.
#
# | Section | {{EFFORT}} |
# |---|---|
{{STATUS}}

# %% [markdown]
# ## 1. Spec
# The only cell that changes a number. Effort and `min_cell` are recorded;
# effort never changes a value, and `min_cell` only hides cells.

# %%
import sys
from pathlib import Path

sys.path.insert(0, {{SRC}})
from praxis.answer import Spec, run  # noqa: E402
from praxis.notebook import show, table_sha  # noqa: E402

spec = Spec(**{{SPEC_JSON}})
OUT = Path("praxis_out")

# %% [markdown]
# ## 2. Assumptions used
# House definitions from `praxis.definitions`. Say which to change and rerun.
#
{{ASSUMPTIONS}}

# %% [markdown]
# ## 3. Answer
# Aggregates only. `<k>` and `suppressed` are small-cell suppression; never
# back-calculate them.

# %%
result = run(spec, OUT)
show(result)

# %% [markdown]
# ## 4. Watch-outs / next refinements
#
{{WATCHOUTS}}

# %% [markdown]
# ## 5. Review
#
{{REVIEW}}

# %% [markdown]
# ## 6. Learnings
# Proposed by the run, saved only when accepted (`praxis-learn add`).
#
{{LEARNINGS}}

# %% [markdown]
# ## 7. Audit

# %%
_expected = {{TABLE_SHA}}
_got = table_sha(result["table"])
print(f"table sha  expected {_expected}  got {_got}")
print(f"disclosure {result['disclosure']}")
assert _got == _expected, "numbers changed since this notebook was written"
print("AUDIT OK: rerun reproduces the released table")
