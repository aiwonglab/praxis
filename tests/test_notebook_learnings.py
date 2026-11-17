"""One notebook template for every level; learnings proposed, never persisted."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from praxis import datasets, learnings, notebook
from praxis.answer import EFFORTS, Spec, run

PROF = {
    "index_stays": 2000,
    "hospitals": 100,
    "discharge_status_unknown": 40,
    "hospital_deaths": 150,
    "no_apache_prediction": 3,
    "age_unknown": 0,
    "sex_unknown": 2,
    "race_other_unknown": 120,
}
DEMO = datasets.DATASETS["eicu_demo"]


def _code(nbj: dict) -> str:
    return "\n".join(
        "".join(c["source"]) for c in nbj["cells"] if c["cell_type"] == "code"
    )


@pytest.mark.parametrize("effort", EFFORTS)
def test_one_template_every_level(synth: Path, effort: str) -> None:
    spec = Spec("eicu_demo", "icu_los_oe", by=["hospital"], effort=effort)
    nbj = notebook.render(spec, run(spec), "How are ICUs doing?")
    md = "".join("".join(c["source"]) for c in nbj["cells"])
    for section in notebook.SECTIONS:
        assert f"## {section}" in md
    assert notebook.REVIEW_TEXT[effort] in md
    assert "{{" not in md


def test_levels_share_everything_but_status_and_review(synth: Path) -> None:
    def code(e: str) -> str:
        spec = Spec("eicu_demo", "icu_los", by=["sex"], effort=e)
        return _code(notebook.render(spec, run(spec)))

    low, high = code("low"), code("high")
    assert low.replace("'low'", "'high'") == high


def test_notebook_reruns_and_audit_passes(
    synth: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = Spec("eicu_demo", "hospital_mortality", by=["age_band"], effort="low")
    path = notebook.write(spec, run(spec), tmp_path / "nb.ipynb")
    monkeypatch.chdir(tmp_path)
    ns: dict = {}
    exec(_code(json.loads(path.read_text())), ns)  # the audit cell asserts
    assert ns["_got"] == ns["_expected"]


def test_candidates_schema_and_masking(state: Path) -> None:
    overall = {"n": 1500, "oe_ratio": 0.75}
    got = {
        c["id"]: c
        for c in learnings.candidates("icu_los_oe", PROF, DEMO, overall, False)
    }
    assert set(got) == {
        "eicu-crd-demo-2-0-1-apache-iva-icu-los-oe",
        "eicu-crd-demo-2-0-1-discharge-status-unknown",
        "eicu-crd-demo-2-0-1-race-other-unknown",
    }  # 3/2000 missing predictions is under the 5% bar
    for c in got.values():
        assert c["valid_for"] == "eicu-crd-demo:2.0.1"
        assert {"id", "type", "content", "confidence", "source", "created"} <= set(c)
    small = dict(PROF, index_stays=100, discharge_status_unknown=4)
    c = learnings.candidates("icu_los", small, DEMO, {}, False)
    assert any("<10/100" in x["content"] for x in c)  # always masked


def test_no_candidates_from_narrowed_run(state: Path) -> None:
    assert learnings.candidates("icu_los_oe", PROF, DEMO, {"oe_ratio": 0.5}, True) == []


def test_stored_learnings_are_not_proposed_again(state: Path) -> None:
    store = state / "projects" / "other-project"
    store.mkdir(parents=True)
    (store / "learnings.jsonl").write_text(
        json.dumps({"id": "eicu-crd-demo-2-0-1-race-other-unknown"}) + "\nnot json\n"
    )
    ids = {c["id"] for c in learnings.candidates("icu_los", PROF, DEMO, {}, False)}
    assert "eicu-crd-demo-2-0-1-race-other-unknown" not in ids
    assert "eicu-crd-demo-2-0-1-discharge-status-unknown" in ids
