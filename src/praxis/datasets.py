"""Dataset registry and the one extraction query per dataset family.

Each family (eICU, MIMIC-IV) has a single SQL template that produces the
standard cohort frame. The template is rendered for DuckDB (local CSV) or
BigQuery (hosted tables); only table references and two type names differ.
Everything downstream of the cohort frame runs in DuckDB, once, in
``metrics.py``.

Cohort frame columns:
    stay_id, hospital_id, age_years, sex, race_ethnicity, icu_los_days,
    hosp_died, pred_icu_los_days, numbedscategory, teaching
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import duckdb

from praxis import config


class Access(StrEnum):
    """Data-use tier of a dataset."""

    OPEN = "open"  # open demo data, no credentialing
    CREDENTIALED = "credentialed"  # PhysioNet credentialed, DUA applies


class Engine(StrEnum):
    """Where the extraction query runs."""

    DUCKDB = "duckdb"
    BIGQUERY = "bigquery"


class RefusedError(RuntimeError):
    """Raised when a run would break a data-boundary rule."""


class BudgetExceededError(RuntimeError):
    """Raised when a query runs past its time budget."""


@dataclass(frozen=True)
class Dataset:
    """A registered data source."""

    name: str
    family: str  # "eicu" or "mimic"
    access: Access
    engine: Engine
    location_key: str  # config key holding the path or BigQuery dataset prefix
    default_location: str | None
    note: str
    valid_for: str = ""  # learnings tag, e.g. "eicu-crd-demo:2.0.1"

    def location(self) -> str:
        """Resolve the path or BigQuery prefix from config, then the default."""
        loc = config.get(self.location_key) or self.default_location
        if not loc:
            raise RefusedError(
                f"{self.name}: set its location first:"
                f" praxis-config set {self.location_key} <path-or-prefix>"
            )
        return loc


DATASETS: dict[str, Dataset] = {
    d.name: d
    for d in [
        Dataset(
            "eicu_demo",
            "eicu",
            Access.OPEN,
            Engine.DUCKDB,
            "eicu_demo_path",
            None,
            "eICU-CRD demo 2.0.1: 2,520 ICU stays, 186 hospitals, 2014-2015.",
            "eicu-crd-demo:2.0.1",
        ),
        Dataset(
            "mimic_iv_demo",
            "mimic",
            Access.OPEN,
            Engine.DUCKDB,
            "mimic_iv_demo_path",
            None,
            "MIMIC-IV demo 2.2: 100 patients, one hospital (BIDMC).",
            "mimic-iv-demo:2.2",
        ),
        Dataset(
            "eicu_demo_bq",
            "eicu",
            Access.OPEN,
            Engine.BIGQUERY,
            "eicu_demo_bq_prefix",
            "physionet-data.eicu_crd_demo",
            "eICU-CRD demo on BigQuery; same rows as eicu_demo.",
            "eicu-crd-demo:2.0.1",
        ),
        Dataset(
            "eicu_crd",
            "eicu",
            Access.CREDENTIALED,
            Engine.BIGQUERY,
            "eicu_crd_bq_prefix",
            "physionet-data.eicu_crd",
            "eICU-CRD 2.0: ~200k ICU stays, 208 hospitals, 2014-2015.",
            "eicu-crd:2.0",
        ),
        Dataset(
            "mimic_iv",
            "mimic",
            Access.CREDENTIALED,
            Engine.BIGQUERY,
            "mimic_iv_bq_prefix",
            "physionet-data.mimiciv_3_1",
            "MIMIC-IV 3.1 on BigQuery (<prefix>_icu / <prefix>_hosp).",
            "mimic-iv:3.1",
        ),
    ]
}

_DIALECT = {
    Engine.DUCKDB: {"float": "DOUBLE", "try_cast": "TRY_CAST"},
    Engine.BIGQUERY: {"float": "FLOAT64", "try_cast": "SAFE_CAST"},
}

EICU_COHORT_SQL = """
SELECT
  CAST(p.patientunitstayid AS STRING) AS stay_id,
  CAST(p.hospitalid AS STRING) AS hospital_id,
  CASE WHEN p.age = '> 89' THEN 90
       ELSE {try_cast}(p.age AS {float}) END AS age_years,
  CASE p.gender WHEN 'Female' THEN 'Female' WHEN 'Male' THEN 'Male'
       ELSE 'Unknown' END AS sex,
  CASE p.ethnicity
       WHEN 'Caucasian' THEN 'White'
       WHEN 'African American' THEN 'Black or African American'
       WHEN 'Hispanic' THEN 'Hispanic or Latino'
       WHEN 'Asian' THEN 'Asian'
       WHEN 'Native American' THEN 'American Indian or Alaska Native'
       ELSE 'Other/Unknown' END AS race_ethnicity,
  CAST(p.unitdischargeoffset AS {float}) / 1440 AS icu_los_days,
  CASE p.hospitaldischargestatus WHEN 'Expired' THEN 1 WHEN 'Alive' THEN 0
       END AS hosp_died,
  a.pred_icu_los_days,
  CAST(h.numbedscategory AS STRING) AS numbedscategory,
  CASE WHEN LOWER(CAST(h.teachingstatus AS STRING)) IN ('t', 'true', '1')
       THEN 'teaching' ELSE 'non-teaching' END AS teaching
FROM {patient} AS p
LEFT JOIN (
  SELECT patientunitstayid,
         CAST(MAX(predictediculos) AS {float}) AS pred_icu_los_days
  FROM {apachepatientresult}
  WHERE apacheversion = 'IVa' AND predictediculos > 0
  GROUP BY patientunitstayid
) AS a ON a.patientunitstayid = p.patientunitstayid
LEFT JOIN {hospital} AS h ON h.hospitalid = p.hospitalid
WHERE p.unitvisitnumber = 1
  AND {hospital_filter}
  AND ({try_cast}(p.age AS {float}) >= 18 OR p.age = '> 89'
       OR p.age IS NULL OR p.age = '')
"""

MIMIC_COHORT_SQL = """
WITH s AS (
  SELECT i.*,
         ROW_NUMBER() OVER (PARTITION BY i.hadm_id
                            ORDER BY i.intime, i.stay_id) AS rn
  FROM {icustays} AS i
), c AS (
  SELECT
    CAST(s.stay_id AS STRING) AS stay_id,
    'BIDMC' AS hospital_id,
    CAST(p.anchor_age + (EXTRACT(YEAR FROM s.intime) - p.anchor_year)
         AS {float}) AS age_years,
    CASE p.gender WHEN 'F' THEN 'Female' WHEN 'M' THEN 'Male'
         ELSE 'Unknown' END AS sex,
    CASE
      WHEN a.race LIKE 'HISPANIC%' OR a.race = 'SOUTH AMERICAN'
        THEN 'Hispanic or Latino'
      WHEN a.race LIKE 'WHITE%' OR a.race = 'PORTUGUESE' THEN 'White'
      WHEN a.race LIKE 'BLACK%' THEN 'Black or African American'
      WHEN a.race LIKE 'ASIAN%' THEN 'Asian'
      WHEN a.race LIKE 'AMERICAN INDIAN%' THEN 'American Indian or Alaska Native'
      WHEN a.race LIKE 'NATIVE HAWAIIAN%'
        THEN 'Native Hawaiian or Other Pacific Islander'
      ELSE 'Other/Unknown' END AS race_ethnicity,
    CAST(s.los AS {float}) AS icu_los_days,
    a.hospital_expire_flag AS hosp_died,
    CAST(NULL AS {float}) AS pred_icu_los_days,
    CAST(NULL AS STRING) AS numbedscategory,
    CAST(NULL AS STRING) AS teaching
  FROM s
  JOIN {patients} AS p ON p.subject_id = s.subject_id
  JOIN {admissions} AS a ON a.hadm_id = s.hadm_id
  WHERE s.rn = 1
)
SELECT * FROM c WHERE age_years >= 18
"""


def _tables(ds: Dataset) -> dict[str, str]:
    loc = ds.location()
    if ds.engine is Engine.DUCKDB:
        root = Path(loc)

        def csv(rel: str) -> str:
            path = root / rel
            if not path.exists():
                raise RefusedError(f"{ds.name}: missing {path}")
            return f"read_csv_auto('{path.as_posix()}')"

        if ds.family == "eicu":
            return {
                "patient": csv("patient.csv.gz"),
                "apachepatientresult": csv("apachePatientResult.csv.gz"),
                "hospital": csv("hospital.csv.gz"),
            }
        return {
            "icustays": csv("icu/icustays.csv.gz"),
            "patients": csv("hosp/patients.csv.gz"),
            "admissions": csv("hosp/admissions.csv.gz"),
        }
    if ds.family == "eicu":
        return {
            t: f"`{loc}.{t}`" for t in ("patient", "apachepatientresult", "hospital")
        }
    return {
        "icustays": f"`{loc}_icu.icustays`",
        "patients": f"`{loc}_hosp.patients`",
        "admissions": f"`{loc}_hosp.admissions`",
    }


def cohort_sql(ds: Dataset, hospital_ids: list[str] | None = None) -> str:
    """Render the family's cohort SQL for the dataset's engine.

    ``hospital_ids`` narrows extraction (eICU only; MIMIC-IV is one hospital).
    """
    if ds.family == "eicu":
        hf = "TRUE"
        if hospital_ids:
            ids = ", ".join("'" + h.replace("'", "''") + "'" for h in hospital_ids)
            hf = f"CAST(p.hospitalid AS STRING) IN ({ids})"
        return EICU_COHORT_SQL.format(
            **_DIALECT[ds.engine], **_tables(ds), hospital_filter=hf
        )
    return MIMIC_COHORT_SQL.format(**_DIALECT[ds.engine], **_tables(ds))


def hospital_sql(ds: Dataset) -> str:
    """SQL listing the distinct hospital ids, for scope narrowing."""
    if ds.family != "eicu":
        return "SELECT 'BIDMC' AS hospital_id"
    return (
        "SELECT DISTINCT CAST(hospitalid AS STRING) AS hospital_id"
        f" FROM {_tables(ds)['patient']}"
    )


def guard(ds: Dataset) -> None:
    """Refuse a run that the data-boundary rules do not allow.

    Credentialed data needs ``credentialed_data_zdr: confirmed`` in the praxis
    config: the Claude API account in use must have zero data retention. The
    library never returns patient-level rows either way; see ``disclosure``.
    """
    if ds.access is Access.CREDENTIALED and (
        config.get(config.ZDR_KEY) != config.ZDR_CONFIRMED
    ):
        raise RefusedError(
            f"{ds.name} is credentialed data. Runs need a Claude API account"
            " with zero data retention. After confirming it, set"
            f" `praxis-config set {config.ZDR_KEY} {config.ZDR_CONFIRMED}`."
        )


def resolve(name: str) -> Dataset:
    """Look up a registered dataset; anything else is refused."""
    if name not in DATASETS:
        raise RefusedError(
            f"Unknown dataset {name!r}. Registered: {', '.join(DATASETS)}."
            " Restricted enclaves are never a demo-mode target."
        )
    return DATASETS[name]


def _with_budget(fn: Callable[[], Any], seconds: float, cancel: Callable[[], object]):
    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["value"] = fn()
        except BaseException as e:  # re-raised on the calling thread
            box["error"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        cancel()
        t.join(5)
        raise BudgetExceededError(f"query passed its {seconds:.0f} s budget")
    if "error" in box:
        raise box["error"]
    return box["value"]


def run_sql(con: duckdb.DuckDBPyConnection, sql: str, budget_s: float) -> None:
    """Execute a statement on a DuckDB connection within a time budget."""
    _with_budget(lambda: con.execute(sql), budget_s, con.interrupt)


def load_cohort(
    ds: Dataset,
    con: duckdb.DuckDBPyConnection,
    budget_s: float,
    hospital_ids: list[str] | None = None,
) -> None:
    """Materialize the cohort frame as table ``cohort`` on ``con``."""
    guard(ds)
    sql = cohort_sql(ds, hospital_ids)
    if ds.engine is Engine.DUCKDB:
        run_sql(con, f"CREATE OR REPLACE TABLE cohort AS {sql}", budget_s)
        return
    tbl = _bigquery_arrow(sql, budget_s)  # rows stay in-process
    con.register("_cohort_src", tbl)
    con.execute("CREATE OR REPLACE TABLE cohort AS SELECT * FROM _cohort_src")
    con.unregister("_cohort_src")


def _bigquery_arrow(sql: str, budget_s: float):
    try:
        from google.cloud import bigquery
    except ImportError as e:
        raise RefusedError(
            "BigQuery datasets need the optional extra: uv sync --extra bigquery"
        ) from e
    project = config.get("bq_project")
    client = bigquery.Client(project=project)
    job = client.query(sql, job_config=bigquery.QueryJobConfig(use_legacy_sql=False))
    return _with_budget(
        lambda: job.result(timeout=budget_s).to_arrow(), budget_s, job.cancel
    )


def list_hospitals(
    ds: Dataset, con: duckdb.DuckDBPyConnection, budget_s: float
) -> list[str]:
    """Return the dataset's hospital ids (aggregate metadata, not patients)."""
    guard(ds)
    sql = hospital_sql(ds)
    if ds.engine is Engine.DUCKDB:
        res = _with_budget(lambda: con.execute(sql).fetchall(), budget_s, con.interrupt)
        return [r[0] for r in res]
    return [str(v) for v in _bigquery_arrow(sql, budget_s).column(0).to_pylist()]
