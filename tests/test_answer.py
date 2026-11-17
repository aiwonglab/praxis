"""The metric library: definitions, disclosure, boundaries, consistency."""

from __future__ import annotations

import time
from pathlib import Path

import duckdb
import pytest
from conftest import DEMO_EICU, set_config

from praxis import config, datasets, definitions, disclosure
from praxis.answer import Spec, run


def _row(result: dict, dimension: str, category: str) -> dict:
    return next(
        r
        for r in result["table"]
        if r["dimension"] == dimension and r["category"] == category
    )


# --- definitions are applied as written -------------------------------------


def test_index_stay_and_adult_filter(synth: Path) -> None:
    r = run(Spec("eicu_demo", "hospital_mortality"))
    # 20 + 12 + stays 902, 903, 904. Not 900 (second visit) or 901 (child).
    assert r["scope"]["index_stays"] == 35
    assert r["table"][-1]["n"] == 35


def test_los_is_survivors_only(synth: Path) -> None:
    r = run(Spec("eicu_demo", "icu_los", by=["sex"]))
    # 903 died; male survivors = 12 (hospital 2) + 904.
    assert _row(r, "sex", "Male")["n"] == 13
    assert _row(r, "Overall", "All")["n"] == 34


def test_age_over_89_is_80_plus(synth: Path) -> None:
    r = run(Spec("eicu_demo", "hospital_mortality", by=["age_band"]))
    # Only stay 902 is 80+: one row under 10, so it is suppressed.
    assert _row(r, "age_band", "80+")["n"] == disclosure.SUPPRESSED


def test_oe_uses_iva_and_drops_sentinel(synth: Path) -> None:
    r = run(Spec("eicu_demo", "icu_los_oe", by=["hospital"]))
    h1 = _row(r, "hospital", "1")
    h2 = _row(r, "hospital", "2")
    assert h1["oe_ratio"] == 1.0  # IV row (99 days) ignored; 902 included
    assert h1["n"] == 21
    assert h2["n"] == disclosure.COMPLEMENTARY or h2["n"] == 12  # 904 dropped
    assert h2["oe_ratio"] == 0.5


def test_mimic_has_no_severity_adjustment(state: Path) -> None:
    with pytest.raises(datasets.RefusedError):
        run(Spec("mimic_iv_demo", "icu_los_oe"))


# --- disclosure ---------------------------------------------------------------


def test_primary_and_complementary_suppression() -> None:
    rows = [
        {"sex": "Female", "n": 700, "median": 1.5},
        {"sex": "Male", "n": 900, "median": 1.4},
        {"sex": "Unknown", "n": 3, "median": 2.0},
        {"sex": "All", "n": 1603, "median": 1.45},
    ]
    out, n = disclosure.suppress(rows, ["n"], ["median"], ["sex"])
    assert n == 1
    assert out[2] == {"sex": "Unknown", "n": "<10", "median": None}
    # Female is next-smallest: n hidden, value kept.
    assert out[0] == {"sex": "Female", "n": "suppressed", "median": 1.5}
    assert out[1]["n"] == 900 and out[3]["n"] == 1603


def test_small_event_count_blanks_rate_not_denominator() -> None:
    rows = [
        {"g": "a", "n": 400, "deaths": 4, "pct": 1.0},
        {"g": "b", "n": 400, "deaths": 40, "pct": 10.0},
        {"g": "All", "n": 800, "deaths": 44, "pct": 5.5},
    ]
    out, _ = disclosure.suppress(rows, ["n", "deaths"], ["pct"], ["g"])
    assert out[0]["deaths"] == "<10" and out[0]["pct"] is None
    assert out[0]["n"] == 400
    assert out[1]["deaths"] == "suppressed" and out[1]["pct"] == 10.0


def test_release_check_refuses_small_cells() -> None:
    with pytest.raises(RuntimeError, match="refusing"):
        disclosure.assert_releasable([{"n": 4}], ["n"])
    disclosure.assert_releasable([{"n": "<10"}, {"n": 10}], ["n"])


def test_output_has_no_patient_level_fields(synth: Path) -> None:
    r = run(Spec("eicu_demo", "icu_los", by=["hospital", "sex"]))
    text = repr(r)
    for sid in ("100", "200", "patientunitstayid", "stay_id"):
        assert f"'{sid}'" not in text


# --- boundaries -----------------------------------------------------------------


def test_credentialed_needs_zdr(state: Path) -> None:
    with pytest.raises(datasets.RefusedError, match="zero data retention"):
        datasets.guard(datasets.DATASETS["eicu_crd"])
    set_config(state, **{config.ZDR_KEY: "yes"})  # anything but "confirmed"
    with pytest.raises(datasets.RefusedError):
        datasets.guard(datasets.DATASETS["eicu_crd"])
    set_config(state, **{config.ZDR_KEY: config.ZDR_CONFIRMED})
    datasets.guard(datasets.DATASETS["eicu_crd"])  # no raise


def test_open_data_needs_no_zdr(state: Path) -> None:
    datasets.guard(datasets.DATASETS["eicu_demo"])


def test_unregistered_dataset_refused(state: Path) -> None:
    with pytest.raises(datasets.RefusedError, match="enclave"):
        run(Spec("prcc_enclave", "icu_los"))


def test_unset_location_refused_not_guessed(state: Path) -> None:
    with pytest.raises(datasets.RefusedError, match="praxis-config set"):
        run(Spec("eicu_demo", "icu_los"))


def test_budget_interrupts_slow_query() -> None:
    con = duckdb.connect()
    slow = "SELECT COUNT(*) FROM range(100000000) a, range(100000) b"
    t0 = time.perf_counter()
    with pytest.raises(datasets.BudgetExceededError):
        datasets.run_sql(con, slow, budget_s=0.5)
    assert time.perf_counter() - t0 < 10


def test_catalog_says_what_is_missing() -> None:
    out = {r["concept"]: r for r in definitions.check(["cost", "icu_los"], "eicu")}
    assert out["cost"]["status"] == "not_in_data"
    assert "finance" in out["cost"]["detail"]
    assert out["icu_los"]["status"] == "available"
    unk = definitions.check(["unicorns"], "eicu")[0]
    assert unk["status"] == "unknown_concept"


# --- one code path ----------------------------------------------------------------


def test_effort_never_changes_numbers(synth: Path) -> None:
    by = ["age_band", "sex", "race_ethnicity", "peer_group"]
    for metric in ("icu_los", "hospital_mortality", "icu_los_oe"):
        res = {
            e: run(Spec("eicu_demo", metric, by=by, effort=e))
            for e in ("low", "medium", "high")
        }
        for e in ("low", "medium"):
            assert res[e]["table"] == res["high"]["table"]
            assert res[e]["assumptions"] == res["high"]["assumptions"]


def test_narrowing_is_reported_and_deterministic(synth: Path) -> None:
    a = run(Spec("eicu_demo", "icu_los", max_hospitals=1))
    b = run(Spec("eicu_demo", "icu_los", max_hospitals=1))
    assert a["scope"]["narrowed"] == [
        "1 of 2 hospitals (fixed hash sample, same every run)"
    ]
    assert a["table"] == b["table"]
    assert a["scope"]["hospitals"] == 1


def test_bigquery_rendering(state: Path) -> None:
    sql = datasets.cohort_sql(datasets.DATASETS["eicu_crd"], ["1", "2"])
    assert "SAFE_CAST" in sql and "FLOAT64" in sql and "TRY_CAST" not in sql
    assert "`physionet-data.eicu_crd.patient`" in sql
    assert "IN ('1', '2')" in sql
    msql = datasets.cohort_sql(datasets.DATASETS["mimic_iv"])
    assert "`physionet-data.mimiciv_3_1_icu.icustays`" in msql
    assert "`physionet-data.mimiciv_3_1_hosp.admissions`" in msql


# --- real open demo (skipped when absent) -------------------------------------------


@pytest.mark.skipif(not DEMO_EICU.exists(), reason="eICU demo not downloaded")
def test_eicu_demo_smoke(state: Path, tmp_path: Path) -> None:
    set_config(state, eicu_demo_path=str(DEMO_EICU))
    r = run(Spec("eicu_demo", "icu_los", by=["age_band", "sex"]), tmp_path)
    assert r["scope"]["hospitals"] == 186
    assert r["scope"]["index_stays"] == 2115
    assert Path(r["chart"]).exists()
    assert sum(r["timings_s"].values()) < 60


def test_total_row_is_suppressed_too() -> None:
    rows = [
        {"g": "a", "n": 20, "deaths": 0, "pct": 0.0},
        {"g": "b", "n": 20, "deaths": 1, "pct": 5.0},
        {"g": "All", "n": 40, "deaths": 1, "pct": 2.5},
    ]
    out, _ = disclosure.suppress(rows, ["n", "deaths"], ["pct"], ["g"])
    assert out[2]["deaths"] == "<10" and out[2]["pct"] is None
    disclosure.assert_releasable(out, ["n", "deaths"])


def test_usage_errors_are_json(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    from praxis.answer import main

    with pytest.raises(SystemExit) as e:
        main(["run", "--dataset", "eicu_demo", "--metric", "nope"])
    assert e.value.code == 4
    assert json.loads(capsys.readouterr().out)["error"] == "usage"


def test_check_aliases_and_unknown() -> None:
    out = definitions.check(["icu_los_oe", "peer_group", "unicornz"], "eicu")
    assert [r["status"] for r in out] == ["available", "available", "unknown_concept"]
    assert "severity_adjustment" in out[2]["detail"]


def test_acceptance_run_vocabulary() -> None:
    """Names cold sessions actually tried in acceptance runs."""
    got = {
        r["concept"]: r["status"]
        for r in definitions.check(
            [
                "age_band",
                "sex",
                "race_ethnicity",
                "hospital",
                "icu_los_days",
                "product_margin",
                "revenue",
                "reimbursement",
                "cost",
            ],
            "eicu",
        )
    }
    for c in ("age_band", "sex", "race_ethnicity", "hospital", "icu_los_days"):
        assert got[c] == "available", c
    for c in ("product_margin", "revenue", "reimbursement", "cost"):
        assert got[c] == "not_in_data", c


# --- suppression threshold is a flag ---------------------------------------------


def test_min_cell_zero_turns_suppression_off(synth: Path) -> None:
    on = run(Spec("eicu_demo", "hospital_mortality", by=["age_band"]))
    off = run(Spec("eicu_demo", "hospital_mortality", by=["age_band"], min_cell=0))
    assert _row(on, "age_band", "80+")["n"] == disclosure.SUPPRESSED
    assert _row(off, "age_band", "80+")["n"] == 1  # stay 902, exact
    assert off["suppressed_rows"] == 0
    assert off["disclosure"] == {"min_cell": 0, "source": "flag", "suppression": False}
    assert any("suppression is off" in w for w in off["watchouts"])


def test_min_cell_never_changes_unsuppressed_values(synth: Path) -> None:
    by = ["age_band", "sex", "peer_group"]
    for metric in ("icu_los", "hospital_mortality", "icu_los_oe"):
        off = run(Spec("eicu_demo", metric, by=by, min_cell=0))["table"]
        on = run(Spec("eicu_demo", metric, by=by))["table"]
        assert len(off) == len(on)
        for a, b in zip(off, on, strict=True):
            for col, v in b.items():
                if v not in (None, disclosure.SUPPRESSED, disclosure.COMPLEMENTARY):
                    assert a[col] == v, (metric, a, b)


def test_min_cell_custom_k_and_config(synth: Path, state: Path) -> None:
    # Hospital 2 survivors with a valid prediction: 12. k=13 suppresses it.
    r = run(Spec("eicu_demo", "icu_los_oe", by=["hospital"], min_cell=13))
    assert _row(r, "hospital", "2")["n"] == "<13"
    assert _row(r, "hospital", "2")["oe_ratio"] is None
    set_config(state, eicu_demo_path=str(synth), min_cell="0")
    r = run(Spec("eicu_demo", "icu_los_oe", by=["hospital"]))
    assert r["disclosure"]["source"] == "config"
    assert _row(r, "hospital", "2")["n"] == 12
    # The flag beats config.
    r = run(Spec("eicu_demo", "icu_los_oe", by=["hospital"], min_cell=10))
    assert r["disclosure"] == {"min_cell": 10, "source": "flag", "suppression": True}


def test_min_cell_rejects_bad_values(synth: Path) -> None:
    with pytest.raises(ValueError, match="min_cell"):
        run(Spec("eicu_demo", "icu_los", min_cell=-1))
