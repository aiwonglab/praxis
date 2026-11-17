"""plan-pi-review: effort routing exists and the high path is untouched."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plan-pi-review" / "SKILL.md"
# Last plan-pi-review before effort levels. High effort must keep its text.
PRE_EFFORT = "c6cf4eb"


def test_effort_sections_present() -> None:
    text = SKILL.read_text()
    for heading in (
        "## Step 0.1 — Effort level",
        "## Shared rules for low and medium effort",
        "## Low effort — demo mode",
        "## Medium effort — operations",
    ):
        assert heading in text
    assert "praxis-answer" in text
    assert "credentialed_data_zdr confirmed" in text


def test_high_path_is_verbatim() -> None:
    try:
        old = subprocess.run(
            ["git", "show", f"{PRE_EFFORT}:plan-pi-review/SKILL.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git history unavailable")
    body = old[old.index("## Step 0.5 — Bounded reconnaissance") :]
    assert body in SKILL.read_text()
    intake = old[old.index("Read any plan files") : old.index("## Step 0.5")]
    # 0.5.0.0: the one sanctioned change to the high intake is the
    # /praxis-office-hours offer, which replaces the closing sentence.
    closing = "Do NOT proceed until you have all four.\n\n"
    assert intake.endswith(closing)
    now = SKILL.read_text()
    assert intake.removesuffix(closing) in now
    assert "Do NOT proceed until you have a plan (from PLAN.md or from the four" in now


REVIEWS = [
    "plan-ds-review",
    "plan-ai-review",
    "plan-clinical-review",
    "plan-deid-review",
    "plan-protocol",
]


def _old(skill: str) -> str:
    try:
        return subprocess.run(
            ["git", "show", f"{PRE_EFFORT}:{skill}/SKILL.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git history unavailable")


@pytest.mark.parametrize("skill", REVIEWS)
def test_review_has_levels_and_low_default(skill: str) -> None:
    text = (ROOT / skill / "SKILL.md").read_text()
    assert "## Step 0.1" in text and "Effort level" in text
    assert "## Low effort" in text and "## Medium effort" in text
    assert "No level stated means **low**" in text
    assert "**Close: ask about more effort.**" in text


@pytest.mark.parametrize("skill", REVIEWS)
def test_review_high_path_is_verbatim(skill: str) -> None:
    old = _old(skill)
    body = old[old.index("\n## Step 1") :].rstrip("\n")
    assert body in (ROOT / skill / "SKILL.md").read_text()


@pytest.mark.parametrize(
    ("skill", "gate"), [("plan-deid-review", "RELEASE"), ("plan-protocol", "SUBMIT")]
)
def test_gating_verdicts_are_high_only(skill: str, gate: str) -> None:
    text = (ROOT / skill / "SKILL.md").read_text()
    low = text[text.index("## Low effort") :]
    assert f"never issue {gate}" in text
    assert f"never {gate}" in low or f"Never write {gate}" in low


def test_plan_default_is_low_and_iterate_passes_level() -> None:
    pi = SKILL.read_text()
    assert "## Effort on a plan (low and medium)" in pi
    assert "No level stated means **low**, for a question or a plan" in pi
    it = (ROOT / "iterate" / "SKILL.md").read_text()
    assert "**Effort level.**" in it and "run every routed review at **low**" in it


def test_runner_defaults_to_low() -> None:
    from praxis.answer import Spec

    assert Spec("eicu_demo", "icu_los").effort == "low"


def test_office_hours_is_namespaced_and_high_only_up_front() -> None:
    oh = (ROOT / "praxis-office-hours" / "SKILL.md").read_text()
    assert oh.startswith("---\nname: praxis-office-hours\n")
    assert not (ROOT / "office-hours").exists()  # gstack owns /office-hours
    for f in ROOT.glob("*/SKILL.md"):
        assert "`/office-hours`" not in f.read_text(), f
    pi = (ROOT / "plan-pi-review" / "SKILL.md").read_text()
    intake = pi[pi.index("If no plan file exists") : pi.index("## Step 0.1")]
    assert "At **high** effort only" in intake
    assert "never offer it up front" in intake
    assert "**Formulate first**" in pi


def test_iterate_build_step_formats_changed_files_only() -> None:
    it = (ROOT / "iterate" / "SKILL.md").read_text()
    step = it[it.index("## Step 4.5") : it.index("## Step 5")]
    assert "ruff format ." not in step
    assert "ruff check . " not in step
    assert "only the Python files changed" in step
