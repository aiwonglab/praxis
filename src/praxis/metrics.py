"""The one metric code path. Every effort level and every engine ends here.

Input is the ``cohort`` table that ``datasets.load_cohort`` builds. Output is
aggregate rows that have already passed small-cell suppression.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import duckdb

from praxis import disclosure

DIMENSIONS: dict[str, str] = {
    "age_band": (
        "CASE WHEN age_years IS NULL THEN 'Unknown'"
        " WHEN age_years < 45 THEN '18-44' WHEN age_years < 65 THEN '45-64'"
        " WHEN age_years < 80 THEN '65-79' ELSE '80+' END"
    ),
    "sex": "sex",
    "race_ethnicity": "race_ethnicity",
    "hospital": "hospital_id",
    "peer_group": (
        "COALESCE(numbedscategory || ' beds', 'Unknown bed size') || ', '"
        " || COALESCE(teaching, 'unknown')"
    ),
}


@dataclass(frozen=True)
class Metric:
    """An aggregate over a defined population."""

    id: str
    population: str  # SQL predicate on cohort
    aggregates: dict[str, str]  # output column -> SQL aggregate
    count_cols: list[str]
    sort_col: str
    definitions: list[str]
    label: str


_LOS_DEFS = ["index_icu_stay", "icu_los_days", "los_population"]

METRICS: dict[str, Metric] = {
    m.id: m
    for m in [
        Metric(
            "icu_los",
            "hosp_died = 0 AND icu_los_days IS NOT NULL",
            {
                "n": "COUNT(*)",
                "median_days": "QUANTILE_CONT(icu_los_days, 0.5)",
                "p25_days": "QUANTILE_CONT(icu_los_days, 0.25)",
                "p75_days": "QUANTILE_CONT(icu_los_days, 0.75)",
            },
            ["n"],
            "median_days",
            _LOS_DEFS,
            "ICU length of stay among survivors (days)",
        ),
        Metric(
            "hospital_mortality",
            "hosp_died IS NOT NULL",
            {
                "n": "COUNT(*)",
                "deaths": "SUM(hosp_died)",
                "mortality_pct": "100.0 * AVG(hosp_died)",
            },
            ["n", "deaths"],
            "mortality_pct",
            ["index_icu_stay", "hospital_mortality"],
            "Hospital mortality (%)",
        ),
        Metric(
            "icu_los_oe",
            "hosp_died = 0 AND icu_los_days IS NOT NULL"
            " AND pred_icu_los_days IS NOT NULL",
            {
                "n": "COUNT(*)",
                "observed_mean_days": "AVG(icu_los_days)",
                "expected_mean_days": "AVG(pred_icu_los_days)",
                "oe_ratio": "SUM(icu_los_days) / SUM(pred_icu_los_days)",
            },
            ["n"],
            "oe_ratio",
            [*_LOS_DEFS, "severity_adjusted_icu_los"],
            "Observed / expected ICU LOS (APACHE IVa), survivors",
        ),
    ]
}


@dataclass
class Table:
    """A released aggregate table and what it took to make it."""

    metric: str
    by: list[str]
    rows: list[dict[str, Any]]
    count_cols: list[str]
    value_cols: list[str]
    suppressed_rows: int
    population_n: int
    excluded: dict[str, int] = field(default_factory=dict)


def _scope_sql(hospital_ids: list[str] | None) -> str:
    if not hospital_ids:
        return "TRUE"
    quoted = ", ".join("'" + h.replace("'", "''") + "'" for h in hospital_ids)
    return f"hospital_id IN ({quoted})"


def compute(
    con: duckdb.DuckDBPyConnection,
    metric_id: str,
    by: list[str],
    hospital_ids: list[str] | None = None,
    min_cell: int = disclosure.K_MIN,
) -> Table:
    """Aggregate ``metric_id`` over ``cohort`` by ``by``, then suppress.

    ``hospital_ids`` narrows scope. It is the only scope lever; definitions
    have no parameters. ``min_cell`` is the suppression threshold (0 = off);
    it hides cells and never changes a computed value.
    """
    m = METRICS[metric_id]
    unknown = [d for d in by if d not in DIMENSIONS]
    if unknown:
        raise ValueError(f"unknown dimension(s) {unknown}; have {list(DIMENSIONS)}")
    scope = _scope_sql(hospital_ids)
    aggs = ", ".join(f"{sql} AS {col}" for col, sql in m.aggregates.items())
    dim_sel = ", ".join(f"{DIMENSIONS[d]} AS {d}" for d in by)
    base = f"SELECT * FROM cohort WHERE ({scope}) AND ({m.population})"

    detail: list[tuple] = []
    if by:
        detail = con.execute(
            f"SELECT {dim_sel}, {aggs} FROM ({base}) GROUP BY ALL"
            f" ORDER BY {', '.join(by)}"
        ).fetchall()
    total = con.execute(f"SELECT {aggs} FROM ({base})").fetchone()
    assert total is not None
    cols = list(m.aggregates)
    rows = [dict(zip([*by, *cols], r, strict=True)) for r in detail]
    rows.append({**{d: "All" for d in by}, **dict(zip(cols, total, strict=True))})
    for r in rows:
        for c in cols:
            if isinstance(r[c], float):
                r[c] = round(r[c], 2)
            if c in m.count_cols and r[c] is not None:
                r[c] = int(r[c])

    value_cols = [c for c in cols if c not in m.count_cols]
    rows, n_sup = disclosure.suppress(rows, m.count_cols, value_cols, by, min_cell)
    disclosure.assert_releasable(rows, m.count_cols, min_cell)

    in_scope = con.execute(f"SELECT COUNT(*) FROM cohort WHERE {scope}").fetchone()
    assert in_scope is not None
    return Table(
        metric=metric_id,
        by=by,
        rows=rows,
        count_cols=m.count_cols,
        value_cols=value_cols,
        suppressed_rows=n_sup,
        population_n=int(total[0]),
        excluded={"index_stays_in_scope": int(in_scope[0])},
    )


def profile(con: duckdb.DuckDBPyConnection, hospital_ids: list[str] | None) -> dict:
    """Return cohort-level counts that feed the data-driven watch-outs."""
    scope = _scope_sql(hospital_ids)
    r = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT hospital_id),"
        " SUM(CASE WHEN hosp_died IS NULL THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN hosp_died = 1 THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN pred_icu_los_days IS NULL THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN age_years IS NULL THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN sex = 'Unknown' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN race_ethnicity = 'Other/Unknown' THEN 1 ELSE 0 END)"
        f" FROM cohort WHERE {scope}"
    ).fetchone()
    assert r is not None
    keys = [
        "index_stays",
        "hospitals",
        "discharge_status_unknown",
        "hospital_deaths",
        "no_apache_prediction",
        "age_unknown",
        "sex_unknown",
        "race_other_unknown",
    ]
    return {k: int(v or 0) for k, v in zip(keys, r, strict=True)}
