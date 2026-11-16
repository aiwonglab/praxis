"""Answer an aggregate question from a spec: the runner every effort level uses.

    praxis-answer run --dataset eicu_demo --metric icu_los \\
        --by age_band,sex,race_ethnicity --out ./out
    praxis-answer check --dataset eicu_demo --concepts cost,icu_los
    praxis-answer definitions

Output is JSON on stdout: assumptions, one table, a chart path, watch-outs and
timings. It never contains patient-level rows. ``effort`` is recorded in the
output and changes nothing else: the same spec gives the same numbers at every
level.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import duckdb

from praxis import config, datasets, definitions, disclosure, learnings, metrics
from praxis import notebook as nb

EFFORTS = ("low", "medium", "high")
MIN_CELL_KEY = "min_cell"


@dataclass
class Spec:
    """What to compute. Everything that can change a number is in here."""

    dataset: str
    metric: str
    by: list[str] = field(default_factory=list)
    cross: bool = False  # False: one breakdown per dimension, stacked
    hospital_ids: list[str] | None = None
    max_hospitals: int | None = None  # deterministic hash sample of hospitals
    budget_s: float = 60.0
    effort: str = "low"
    # Minimum cell size. None: config ``min_cell``, else 10. 0: off (internal QI).
    min_cell: int | None = None


def resolve_min_cell(spec: Spec) -> tuple[int, str]:
    """Return the suppression threshold and where it came from."""
    if spec.min_cell is not None:
        return disclosure.check_k(spec.min_cell), "flag"
    raw = config.get(MIN_CELL_KEY)
    if raw is not None:
        try:
            k = int(raw)
        except ValueError:
            raise ValueError(
                f"config {MIN_CELL_KEY}={raw!r} is not an integer"
            ) from None
        return disclosure.check_k(k), "config"
    return disclosure.K_MIN, "default"


def _mask(v: int, k: int) -> int | str:
    return disclosure.label(k) if 0 < v < k else v


def _sample_hospitals(ids: list[str], n: int) -> list[str]:
    return sorted(ids, key=lambda h: hashlib.md5(h.encode()).hexdigest())[:n]


def _stack(tables: list[metrics.Table]) -> list[dict[str, Any]]:
    """Stack single-dimension tables into dimension | category | values."""
    rows: list[dict[str, Any]] = []
    overall = None
    for t in tables:
        dim = t.by[0]
        for r in t.rows:
            vals = {k: v for k, v in r.items() if k != dim}
            if r[dim] == "All":
                overall = {"dimension": "Overall", "category": "All", **vals}
            else:
                rows.append({"dimension": dim, "category": r[dim], **vals})
    return ([overall] if overall else []) + rows


def _watchouts(
    spec: Spec, prof: dict, sup: int, ds: datasets.Dataset, overall: dict, k: int
) -> list[str]:
    w = []
    if k == 0:
        w.append(
            "Small-cell suppression is off: every count is exact, including"
            " counts under 10. Fine inside the QI team; rerun with suppression"
            " on (--min-cell 10) before sharing outside it."
        )
    oe = overall.get("oe_ratio")
    if spec.metric == "icu_los_oe" and isinstance(oe, float) and abs(oe - 1) > 0.15:
        w.append(
            f"Overall O/E is {oe}, not 1.0: APACHE IVa is miscalibrated for this"
            " population. Compare a hospital to the overall O/E or its peer"
            " group, not to 1.0."
        )
    if sup:
        w.append(
            f"{sup} row(s) suppressed: fewer than {k} stays or"
            " events. Where one row in a breakdown is suppressed, a second row"
            " hides its n so the small cell cannot be recovered from the total."
        )
    if prof["discharge_status_unknown"]:
        w.append(
            f"{_mask(prof['discharge_status_unknown'], k)} index stays have unknown"
            " discharge status and are excluded from LOS and mortality."
        )
    if spec.metric == "icu_los_oe" and prof["no_apache_prediction"]:
        w.append(
            f"{_mask(prof['no_apache_prediction'], k)} of {prof['index_stays']} index"
            " stays have no valid APACHE IVa prediction and are excluded from O/E."
        )
    if spec.metric == "icu_los":
        w.append(
            "Not severity-adjusted. Differences between groups may reflect case"
            " mix. eICU can adjust with APACHE IVa (metric icu_los_oe)."
            if ds.family == "eicu"
            else "Not severity-adjusted; MIMIC-IV has no APACHE in the library."
        )
    if spec.metric in ("icu_los", "icu_los_oe"):
        w.append(
            "LOS is among survivors. Deaths are reported separately"
            " (metric hospital_mortality)."
        )
    if prof["race_other_unknown"]:
        w.append(
            f"{_mask(prof['race_other_unknown'], k)} of {prof['index_stays']} index"
            " stays (all statuses, before the metric's population filter) have"
            " Other/Unknown race/ethnicity."
        )
    w.append(
        f"Public research data ({ds.note.split(':')[0]}), not your hospital's."
        " It shows how ICUs in this sample compare; placing your own units"
        " needs your own data run through the same definitions."
    )
    if ds.name.startswith("eicu_demo"):
        w.append(
            "Demo data: a sample of eICU-CRD. Most hospitals have under 30"
            " stays, so per-hospital estimates are unstable. Rerun on eicu_crd"
            " for real comparisons."
        )
    elif ds.name == "mimic_iv_demo":
        w.append("Demo data: 100 MIMIC-IV patients. Rerun on mimic_iv for real n.")
    return w


def run(spec: Spec, out_dir: Path | None = None) -> dict[str, Any]:
    """Compute the spec and return the releasable result."""
    if spec.effort not in EFFORTS:
        raise ValueError(f"effort must be one of {EFFORTS}")
    if spec.metric not in metrics.METRICS:
        raise ValueError(
            f"unknown metric {spec.metric!r}; have {list(metrics.METRICS)}"
        )
    ds = datasets.resolve(spec.dataset)
    if spec.metric == "icu_los_oe" and ds.family != "eicu":
        raise datasets.RefusedError(
            "Severity-adjusted LOS needs APACHE, which only eICU has here."
        )
    if "peer_group" in spec.by and ds.family != "eicu":
        raise datasets.RefusedError("Peer groups need the eICU hospital table.")

    k, k_source = resolve_min_cell(spec)
    timings: dict[str, float] = {}
    narrowed: list[str] = []
    con = duckdb.connect()
    hospital_ids = spec.hospital_ids
    if spec.max_hospitals and not hospital_ids:
        t0 = time.perf_counter()
        all_ids = datasets.list_hospitals(ds, con, spec.budget_s)
        if spec.max_hospitals < len(all_ids):
            hospital_ids = _sample_hospitals(all_ids, spec.max_hospitals)
            narrowed.append(
                f"{spec.max_hospitals} of {len(all_ids)} hospitals"
                " (fixed hash sample, same every run)"
            )
        timings["hospital_list"] = round(time.perf_counter() - t0, 2)
    if spec.hospital_ids:
        narrowed.append(f"{len(spec.hospital_ids)} named hospital(s)")

    t0 = time.perf_counter()
    datasets.load_cohort(ds, con, spec.budget_s, hospital_ids)
    timings["cohort"] = round(time.perf_counter() - t0, 2)

    t0 = time.perf_counter()
    if spec.by and not spec.cross:
        tables = [
            metrics.compute(con, spec.metric, [d], hospital_ids, k) for d in spec.by
        ]
        rows = _stack(tables)
    else:
        tables = [metrics.compute(con, spec.metric, spec.by, hospital_ids, k)]
        rows = tables[0].rows
    sup = sum(t.suppressed_rows for t in tables)
    prof = metrics.profile(con, hospital_ids)
    timings["metrics"] = round(time.perf_counter() - t0, 2)

    m = metrics.METRICS[spec.metric]
    defs = list(m.definitions)
    defs += [d for d in spec.by if d in definitions.DEFINITIONS]
    result: dict[str, Any] = {
        "effort": spec.effort,
        "spec": asdict(spec),
        "dataset": {
            "name": ds.name,
            "access": str(ds.access),
            "engine": str(ds.engine),
            "note": ds.note,
        },
        "metric": {"id": m.id, "label": m.label},
        "scope": {
            "index_stays": prof["index_stays"],
            "hospitals": prof["hospitals"],
            "population_n": tables[-1].population_n,
            "narrowed": narrowed,
        },
        "assumptions": [definitions.DEFINITIONS[d].as_dict() for d in defs],
        "table": rows,
        "count_cols": m.count_cols,
        "disclosure": {"min_cell": k, "source": k_source, "suppression": k > 0},
        "suppressed_rows": sup,
        "watchouts": _watchouts(spec, prof, sup, ds, tables[-1].rows[-1], k),
        "candidate_learnings": learnings.candidates(
            spec.metric, prof, ds, tables[-1].rows[-1], bool(narrowed)
        ),
        "timings_s": timings,
    }
    disclosure.assert_releasable(rows, m.count_cols, k)
    if out_dir is not None:
        t0 = time.perf_counter()
        result["chart"] = str(_chart(result, out_dir))
        timings["chart"] = round(time.perf_counter() - t0, 2)
    return result


def _chart(result: dict[str, Any], out_dir: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    metric = metrics.METRICS[result["metric"]["id"]]
    col = metric.sort_col
    rows = [r for r in result["table"] if r.get(col) is not None]
    by = result["spec"]["by"]
    path = out_dir / f"{result['dataset']['name']}_{metric.id}.png"

    if by == ["hospital"]:
        pts = [r for r in rows if r.get("category", r.get("hospital")) != "All"]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.scatter([r["n"] for r in pts], [r[col] for r in pts], s=18, color="#3b6ea5")
        overall = next(
            (r[col] for r in result["table"] if r.get("category") == "All"), None
        )
        if overall is not None:
            ax.axhline(overall, color="#888", lw=1, ls="--", label="All hospitals")
            ax.legend(frameon=False)
        ax.set_xlabel("Stays per hospital (n)")
        ax.set_ylabel(metric.label)
        k = result["disclosure"]["min_cell"]
        ax.set_title(f"{metric.label}: hospitals with n >= {k}" if k else metric.label)
    else:
        dims = [d for d in dict.fromkeys(r.get("dimension") for r in rows) if d]
        dims = [d for d in dims if d != "Overall"] or ["Overall"]
        fig, axes = plt.subplots(
            len(dims), 1, figsize=(7, 1.2 + 0.42 * len(rows)), squeeze=False
        )
        for ax, d in zip(axes[:, 0], dims, strict=True):
            sub = [r for r in rows if r.get("dimension") == d]
            labels = [str(r["category"]) for r in sub]
            ax.barh(labels, [r[col] for r in sub], color="#3b6ea5")
            for i, r in enumerate(sub):
                ax.text(r[col], i, f"  n={r['n']}", va="center", fontsize=8)
            ref = next(
                (r[col] for r in result["table"] if r.get("dimension") == "Overall"),
                None,
            )
            if ref is not None and d != "Overall":
                ax.axvline(ref, color="#888", lw=1, ls="--")
                ax.text(ref, -0.7, f" all = {ref}", fontsize=8, color="#555")
            ax.invert_yaxis()
            ax.set_title(d.replace("_", " "), loc="left", fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
        axes[-1, 0].set_xlabel(metric.label)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


class _JsonArgParser(argparse.ArgumentParser):
    """Usage errors as JSON on stdout, exit 4, so callers parse one format."""

    def error(self, message: str):  # type: ignore[override]
        print(json.dumps({"error": "usage", "detail": message}, indent=2))
        sys.exit(4)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    p = _JsonArgParser(prog="praxis-answer")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_JsonArgParser)
    r = sub.add_parser("run")
    r.add_argument("--dataset", required=True)
    r.add_argument("--metric", required=True, choices=list(metrics.METRICS))
    r.add_argument("--by", default="")
    r.add_argument("--cross", action="store_true")
    r.add_argument("--hospitals", default="")
    r.add_argument("--max-hospitals", type=int)
    r.add_argument("--budget", type=float, default=60.0)
    r.add_argument("--effort", choices=EFFORTS, default="low")
    r.add_argument(
        "--min-cell",
        type=int,
        help="Suppress cells under N (default: config min_cell, else 10). 0 = off.",
    )
    r.add_argument("--out", type=Path)
    r.add_argument(
        "--notebook",
        type=Path,
        help="Notebook path (default: <out>/<dataset>_<metric>.ipynb with --out)",
    )
    r.add_argument("--question", default="", help="The question, for the notebook")
    c = sub.add_parser("check")
    c.add_argument("--dataset", required=True)
    c.add_argument("--concepts", required=True)
    sub.add_parser("definitions")
    sub.add_parser("datasets")
    sub.add_parser("concepts")
    a = p.parse_args(argv)

    try:
        if a.cmd == "concepts":
            out = {
                "concepts": list(definitions.CATALOG),
                "aliases": definitions.ALIASES,
            }
        elif a.cmd == "definitions":
            out: Any = [d.as_dict() for d in definitions.DEFINITIONS.values()]
        elif a.cmd == "datasets":
            out = [
                {
                    "name": d.name,
                    "access": str(d.access),
                    "engine": str(d.engine),
                    "config_key": d.location_key,
                    "note": d.note,
                }
                for d in datasets.DATASETS.values()
            ]
        elif a.cmd == "check":
            ds = datasets.resolve(a.dataset)
            out = definitions.check(
                [x.strip() for x in a.concepts.split(",") if x.strip()], ds.family
            )
        else:
            spec = Spec(
                dataset=a.dataset,
                metric=a.metric,
                by=[x.strip() for x in a.by.split(",") if x.strip()],
                cross=a.cross,
                hospital_ids=[x for x in a.hospitals.split(",") if x] or None,
                max_hospitals=a.max_hospitals,
                budget_s=a.budget,
                effort=a.effort,
                min_cell=a.min_cell,
            )
            out = run(spec, a.out)
            nb_path = a.notebook or (
                a.out / f"{spec.dataset}_{spec.metric}.ipynb" if a.out else None
            )
            if nb_path:
                out["notebook"] = str(nb.write(spec, out, nb_path, a.question))
    except datasets.BudgetExceededError as e:
        out = {
            "error": "budget",
            "detail": str(e),
            "next": "Narrow scope: rerun with --max-hospitals N or --hospitals.",
        }
        print(json.dumps(out, indent=2))
        return 3
    except (datasets.RefusedError, ValueError) as e:
        print(json.dumps({"error": "refused", "detail": str(e)}, indent=2))
        return 2
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
