"""Fixtures: a synthetic eICU-shaped dataset and an isolated praxis config."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

import pytest

DEMO_EICU = Path("/workspace/data/physionet.org/eicu-crd-demo/2.0.1")

PATIENT_COLS = [
    "patientunitstayid",
    "hospitalid",
    "age",
    "gender",
    "ethnicity",
    "unitdischargeoffset",
    "hospitaldischargestatus",
    "unitvisitnumber",
]


def _write(path: Path, cols: list[str], rows: list[list]) -> None:
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def synthetic_eicu(root: Path) -> dict[str, list[list]]:
    """Write a small eICU-shaped dataset with known answers.

    Hospital 1: 20 adult survivors, LOS 1..20 days, female, Caucasian.
    Hospital 2: 12 adult survivors, LOS 2 days, male, African American.
    Edge rows, each of which a definition must handle:
      - stay 900: second unit visit (excluded from index stays)
      - stay 901: age 12 (excluded, not adult)
      - stay 902: age '> 89', survivor (counts as 80+)
      - stay 903: Expired (in mortality, not in survivor LOS)
      - stay 904: APACHE prediction -1 (excluded from O/E only)
    """
    root.mkdir(parents=True, exist_ok=True)
    pts: list[list] = []
    apache: list[list] = []
    for i in range(20):
        sid = 100 + i
        pts.append([sid, 1, "50", "Female", "Caucasian", (i + 1) * 1440, "Alive", 1])
        apache.append([sid, "IVa", float(i + 1)])  # predicted == observed
    for i in range(12):
        sid = 200 + i
        pts.append([sid, 2, "40", "Male", "African American", 2 * 1440, "Alive", 1])
        apache.append([sid, "IVa", 4.0])  # O/E = 0.5
    pts += [
        [900, 1, "50", "Female", "Caucasian", 1440, "Alive", 2],
        [901, 1, "12", "Female", "Caucasian", 1440, "Alive", 1],
        [902, 1, "> 89", "Female", "Caucasian", 1440, "Alive", 1],
        [903, 2, "70", "Male", "Hispanic", 1440, "Expired", 1],
        [904, 2, "60", "Male", "Hispanic", 1440, "Alive", 1],
    ]
    apache += [[902, "IVa", 1.0], [903, "IVa", 1.0], [904, "IVa", -1.0]]
    apache += [[100, "IV", 99.0]]  # APACHE IV row must be ignored
    _write(root / "patient.csv.gz", PATIENT_COLS, pts)
    _write(
        root / "apachePatientResult.csv.gz",
        ["patientunitstayid", "apacheversion", "predictediculos"],
        apache,
    )
    _write(
        root / "hospital.csv.gz",
        ["hospitalid", "numbedscategory", "teachingstatus", "region"],
        [[1, "<100", "f", "South"], [2, ">= 500", "t", "West"]],
    )
    return {"patient": pts, "apache": apache}


@pytest.fixture
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty praxis state dir, isolated from ~/.praxis."""
    d = tmp_path / "state"
    d.mkdir()
    monkeypatch.setenv("PRAXIS_STATE_DIR", str(d))
    return d


def set_config(state: Path, **kv: str) -> None:
    """Write key: value lines into the isolated config."""
    (state / "config.yaml").write_text("".join(f"{k}: {v}\n" for k, v in kv.items()))


@pytest.fixture
def synth(tmp_path: Path, state: Path) -> Path:
    """Synthetic eICU data registered as eicu_demo."""
    root = tmp_path / "eicu"
    synthetic_eicu(root)
    set_config(state, eicu_demo_path=str(root))
    return root
