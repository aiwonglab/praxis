"""Render the one answer notebook, at any effort level.

The template is ``templates/answer_notebook.py`` (py:percent, so it reads and
diffs as plain text). Every level renders the same sections; ``SECTIONS`` says
which a level fills and which it marks *not run*.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from praxis.answer import Spec

TEMPLATE = Path(__file__).with_name("templates") / "answer_notebook.py"
SRC = Path(__file__).resolve().parents[1]
VERSION_FILE = SRC.parent / "VERSION"

# section -> effort -> state shown in the status table
SECTIONS: dict[str, dict[str, str]] = {
    "1. Spec": dict.fromkeys(("low", "medium", "high"), "filled"),
    "2. Assumptions used": dict.fromkeys(("low", "medium", "high"), "filled"),
    "3. Answer": dict.fromkeys(("low", "medium", "high"), "filled"),
    "4. Watch-outs": dict.fromkeys(("low", "medium", "high"), "filled"),
    "5. Review": {
        "low": "not run",
        "medium": "short review",
        "high": "full audit",
    },
    "6. Learnings": dict.fromkeys(("low", "medium", "high"), "proposed"),
    "7. Audit": dict.fromkeys(("low", "medium", "high"), "filled"),
}

REVIEW_TEXT = {
    "low": (
        "*Not run at low effort.* To make this rigorous, set `effort` to"
        ' "medium" in the spec cell and ask for a medium run: 2-3 questions,'
        " a one-pass review of the seven dimensions, full scope."
    ),
    "medium": (
        "*Short review (plan-pi-review M2).* The skill replaces this cell with"
        " the one-pass dimension table and verdict."
    ),
    "high": (
        "*Full audit.* The skill replaces this cell with the plan-pi-review"
        " report, or a link to it."
    ),
}


def table_sha(table: list[dict[str, Any]]) -> str:
    """Return a short, stable hash of a released table."""
    blob = json.dumps(table, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def show(result: dict[str, Any]) -> None:
    """Display the released table as markdown, in a notebook or a terminal."""
    rows = result["table"]
    cols = list(rows[0]) if rows else []
    md = "\n".join(
        [
            f"**{result['metric']['label']}** ({result['dataset']['name']},"
            f" min cell {result['disclosure']['min_cell'] or 'off'})",
            "",
            "| " + " | ".join(cols) + " |",
            "|" + "---|" * len(cols),
            *(
                "| "
                + " | ".join("" if r[c] is None else str(r[c]) for c in cols)
                + " |"
                for r in rows
            ),
        ]
    )
    try:
        from IPython.display import (  # pyright: ignore[reportMissingImports]
            Markdown,
            display,
        )

        display(Markdown(md))
    except ImportError:
        print(md)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) or "- None."


def _cells(text: str) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for block in re.split(r"^# %%", text, flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        if "[markdown]" in head:
            lines = [re.sub(r"^# ?", "", ln) for ln in body.strip("\n").splitlines()]
            cells.append(
                {"cell_type": "markdown", "metadata": {}, "source": "\n".join(lines)}
            )
        else:
            cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": body.strip("\n"),
                }
            )
    return cells


def render(spec: Spec, result: dict[str, Any], question: str = "") -> dict[str, Any]:
    """Fill the template for ``spec`` at its effort level; return nbformat 4."""
    effort = spec.effort
    learn = result.get("candidate_learnings", [])
    values = {
        "TITLE": result["metric"]["label"],
        "QUESTION": question or "(not recorded)",
        "EFFORT": effort,
        "DATASET_NOTE": result["dataset"]["note"],
        "CREATED": date.today().isoformat(),
        "VERSION": VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "?",
        "STATUS": "\n".join(f"| {s} | {lv[effort]} |" for s, lv in SECTIONS.items()),
        "SRC": repr(str(SRC)),
        "SPEC_JSON": repr(asdict(spec)),  # Python literal, not JSON
        "ASSUMPTIONS": _bullets(
            [
                f"**{a['id']}** (v{a['version']}): {a['text']}"
                for a in result["assumptions"]
            ]
            + [
                f"**min_cell**: {result['disclosure']['min_cell'] or 'off'}"
                f" ({result['disclosure']['source']})"
            ]
        ),
        "WATCHOUTS": _bullets(result["watchouts"]),
        "REVIEW": REVIEW_TEXT[effort],
        "LEARNINGS": _bullets(
            [
                f"`{c['id']}` ({c['type']}, {c['confidence']}/10): {c['content']}"
                for c in learn
            ]
        ),
        "TABLE_SHA": repr(table_sha(result["table"])),
    }
    cells = _cells(TEMPLATE.read_text())
    for cell in cells:
        src = cell["source"]
        for k, v in values.items():
            src = src.replace("{{" + k + "}}", v)
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", src)
        assert not leftover, f"unfilled template fields: {leftover}"
        cell["source"] = src.splitlines(keepends=True)
    return {
        "cells": cells,
        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write(spec: Spec, result: dict[str, Any], path: Path, question: str = "") -> Path:
    """Render and write the notebook; return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(render(spec, result, question), indent=1))
    return path
