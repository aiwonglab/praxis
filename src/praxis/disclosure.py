"""Small-cell suppression and the check that output is summary-only.

The model sees what this module lets through and nothing else: aggregate rows
with every count >= ``k``. ``assert_releasable`` is the refusal; it runs on
every result, after suppression, and raises rather than emit a small cell.

``k`` is the minimum cell size, default ``K_MIN`` (10). ``k = 0`` turns
suppression off for internal QI, where exact small counts are the point.
Output is still aggregate-only at every ``k``: no setting releases a
patient-level row.
"""

from __future__ import annotations

from typing import Any

K_MIN = 10
SUPPRESSED = "<10"  # label at the default k
COMPLEMENTARY = "suppressed"

Row = dict[str, Any]


def label(k: int) -> str:
    """Return the primary-suppression label for minimum cell size ``k``."""
    return f"<{k}"


def check_k(k: int) -> int:
    """Validate a minimum cell size: 0 (off) or a positive integer."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError(f"min_cell must be 0 (off) or a positive integer, got {k!r}")
    return k


def suppress(
    rows: list[Row],
    count_cols: list[str],
    value_cols: list[str],
    dims: list[str],
    k: int = K_MIN,
) -> tuple[list[Row], int]:
    """Apply primary and complementary small-cell suppression.

    Primary: a count under ``k`` becomes ``"<k"`` and the row's values
    are blanked, since a percentage or median over a known n gives the count
    back.

    Complementary: with one dimension and an "All" row, a lone small row is
    recoverable as All minus the others. The next-smallest row then hides its
    counts (``"suppressed"``) but keeps its values: a median or a percentage
    without its n cannot rebuild the small cell, and a large group's estimate
    stays visible.

    Returns the new rows and the number of primary-suppressed rows. With
    ``k = 0`` the rows come back unchanged.
    """
    out = [dict(r) for r in rows]
    if check_k(k) == 0:
        return out, 0

    def small(i: int) -> bool:
        return any(
            isinstance(out[i][c], int | float) and out[i][c] < k for c in count_cols
        )

    total = [i for i, r in enumerate(out) if dims and r[dims[0]] == "All"]
    detail = [i for i in range(len(out)) if i not in total]
    primary = [i for i in range(len(out)) if small(i)]
    complementary: set[int] = set()
    lone = [i for i in primary if i in detail]
    if len(dims) == 1 and len(lone) == 1 and total and not small(total[0]):
        rest = [i for i in detail if i not in primary]
        if rest:
            complementary.add(min(rest, key=lambda i: out[i][count_cols[0]]))
    for i in primary:
        for c in count_cols:
            if isinstance(out[i][c], int | float) and out[i][c] < k:
                out[i][c] = label(k)
        for c in value_cols:
            out[i][c] = None
    for i in complementary:
        for c in count_cols:
            out[i][c] = COMPLEMENTARY
    return out, len(primary)


def assert_releasable(rows: list[Row], count_cols: list[str], k: int = K_MIN) -> None:
    """Raise if any count under ``k`` survived suppression."""
    for r in rows:
        for c in count_cols:
            v = r.get(c)
            if isinstance(v, int | float) and v < k:
                raise RuntimeError(f"refusing to release a cell with {c}={v} (< {k})")
