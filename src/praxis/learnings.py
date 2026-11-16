"""Candidate learnings from a run, in the praxis-learn schema.

The runner proposes; it never persists. The skill shows the candidates after
the answer and saves only what the user accepts, with ``praxis-learn add``.
A wrong learning is worse than none: it comes back in later reviews with
authority.

Candidates are data-driven and portable: true of the dataset version, not of
this question. Ids are stable per dataset version, so a learning already in
any project's store is not proposed again. Counts in a learning always use
the default small-cell rule, whatever ``--min-cell`` the run used, because a
learning outlives the QI team that ran it.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from praxis import config, datasets, disclosure


def _slug(tag: str) -> str:
    return tag.replace(":", "-").replace(".", "-")


def _n(v: int) -> int | str:
    return disclosure.SUPPRESSED if 0 < v < disclosure.K_MIN else v


def _pct(part: int, whole: int) -> str:
    return f"{_n(part)}/{whole} ({100 * part / whole:.1f}%)" if whole else "0/0"


def existing_ids() -> set[str]:
    """Return every learning id in every project's store on this machine."""
    ids: set[str] = set()
    root = config.state_dir() / "projects"
    for f in root.glob("*/learnings.jsonl") if root.exists() else []:
        for line in f.read_text().splitlines():
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return ids


def candidates(
    metric: str,
    prof: dict[str, int],
    ds: datasets.Dataset,
    overall: dict[str, Any],
    narrowed: bool,
) -> list[dict[str, Any]]:
    """Propose learnings this run surfaced that are not stored anywhere yet.

    Nothing is proposed from a narrowed run: a hospital subsample's rates are
    not facts about the dataset version.
    """
    if narrowed or not ds.valid_for:
        return []
    tag, base = ds.valid_for, _slug(ds.valid_for)
    n = prof["index_stays"]
    out: list[dict[str, Any]] = []

    def add(key: str, typ: str, content: str, confidence: int) -> None:
        out.append(
            {
                "id": f"{base}-{key}",
                "type": typ,
                "content": content,
                "confidence": confidence,
                "source": "plan-pi-review",
                "dataset": ds.family,
                "valid_for": tag,
                "created": date.today().isoformat(),
            }
        )

    oe = overall.get("oe_ratio")
    if metric == "icu_los_oe" and isinstance(oe, float) and abs(oe - 1) > 0.15:
        add(
            "apache-iva-icu-los-oe",
            "dataset-gotcha",
            f"APACHE IVa observed/expected ICU LOS is {oe} overall on {tag}"
            f" (survivors with a valid prediction, n={_n(int(overall['n']))})."
            " Benchmark a hospital against the overall or peer-group O/E, not"
            " 1.0, or nearly every unit looks efficient.",
            8,
        )
    if n and prof["discharge_status_unknown"] / n >= 0.01:
        add(
            "discharge-status-unknown",
            "dataset-gotcha",
            f"{_pct(prof['discharge_status_unknown'], n)} adult index ICU stays"
            f" on {tag} have no hospital discharge status. They drop out of"
            " mortality and survivor LOS denominators; report them.",
            7,
        )
    if metric == "icu_los_oe" and n and prof["no_apache_prediction"] / n >= 0.05:
        add(
            "apache-iva-missing-prediction",
            "dataset-gotcha",
            f"{_pct(prof['no_apache_prediction'], n)} adult index ICU stays on"
            f" {tag} have no valid APACHE IVa predicted ICU LOS (-1 is the"
            " missing sentinel). O/E covers only the rest; compare that"
            " subset's case mix before reading it as the whole unit.",
            7,
        )
    if n and prof["race_other_unknown"] / n >= 0.05:
        add(
            "race-other-unknown",
            "dataset-gotcha",
            f"{_pct(prof['race_other_unknown'], n)} adult index ICU stays on"
            f" {tag} have Other/Unknown race/ethnicity. Equity breakdowns"
            " carry that group as its own row, never imputed.",
            6,
        )
    seen = existing_ids()
    return [c for c in out if c["id"] not in seen]
