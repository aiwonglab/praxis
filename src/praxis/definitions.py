"""Canonical definitions and the concept catalog.

These are the house definitions. Every effort level reads them from here, and
the SQL in ``datasets.py`` and ``metrics.py`` implements exactly these and no
others. Changing a definition means a new ``version`` here, never an inline
variant in a notebook or a skill.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Definition:
    """One operationalized clinical or analytic concept."""

    id: str
    version: str
    text: str
    source: str

    def as_dict(self) -> dict[str, str]:
        """Return the definition as a plain dict for JSON output."""
        return asdict(self)


DEFINITIONS: dict[str, Definition] = {
    d.id: d
    for d in [
        Definition(
            "index_icu_stay",
            "1",
            "First ICU stay of each hospital admission. eICU: unitvisitnumber = 1."
            " MIMIC-IV: earliest intime per hadm_id. Adults (age >= 18 or age"
            " unrecorded).",
            "House definition; eICU-CRD and MIMIC-IV data dictionaries",
        ),
        Definition(
            "icu_los_days",
            "1",
            "ICU length of stay of the index stay, in days. eICU:"
            " unitdischargeoffset / 1440. MIMIC-IV: icustays.los.",
            "eICU-CRD patient table; MIMIC-IV icustays",
        ),
        Definition(
            "los_population",
            "1",
            "LOS metrics are computed among hospital survivors (discharged"
            " alive). Stays with unknown discharge status are excluded.",
            "House definition: avoids death truncating LOS",
        ),
        Definition(
            "hospital_mortality",
            "1",
            "Died before hospital discharge. eICU: hospitaldischargestatus ="
            " 'Expired'. MIMIC-IV: admissions.hospital_expire_flag = 1. Unknown"
            " status excluded from the denominator.",
            "eICU-CRD patient table; MIMIC-IV admissions",
        ),
        Definition(
            "age_band",
            "1",
            "Age at ICU admission: 18-44, 45-64, 65-79, 80+. eICU '> 89' counts"
            " as 90. MIMIC-IV: anchor_age + (year(intime) - anchor_year).",
            "House bands; MIMIC-IV anchor_age convention",
        ),
        Definition(
            "sex",
            "1",
            "Recorded sex: Female, Male, Unknown.",
            "Source field as recorded",
        ),
        Definition(
            "race_ethnicity",
            "1",
            "One combined field, NIH labels. eICU records race and ethnicity"
            " in a single 'ethnicity' column, so Hispanic or Latino is a"
            " category here rather than a separate axis.",
            "NIH categories, as in aiwonglab normalize_demographics",
        ),
        Definition(
            "severity_adjusted_icu_los",
            "1",
            "Observed / expected ICU LOS = sum(icu_los_days) / sum(APACHE IVa"
            " predicted ICU LOS), over stays with a valid prediction"
            " (predictediculos > 0; -1 is a missing-value sentinel).",
            "APACHE IVa as recorded in eICU apachePatientResult (Zimmerman 2006)",
        ),
        Definition(
            "peer_group",
            "1",
            "Hospital peer group: eICU bed-size category x teaching status.",
            "eICU-CRD hospital table",
        ),
    ]
}


class Availability(StrEnum):
    """Whether a concept can be answered on a dataset."""

    AVAILABLE = "available"
    NOT_IN_LIBRARY = "not_in_library"  # in the data, not yet a canonical metric
    NOT_IN_DATA = "not_in_data"  # the dataset cannot answer this
    UNKNOWN = "unknown_concept"  # not a catalog name; pick one from the list


_FINANCE = (
    "Not recorded in eICU-CRD or MIMIC-IV. Needs finance data: charges or"
    " cost-accounting extracts linked to the encounter."
)

# concept -> family -> (availability, reason). Family is "eicu" or "mimic".
CATALOG: dict[str, dict[str, tuple[Availability, str]]] = {
    "icu_los": {
        "eicu": (Availability.AVAILABLE, "icu_los_days"),
        "mimic": (Availability.AVAILABLE, "icu_los_days"),
    },
    "hospital_mortality": {
        "eicu": (Availability.AVAILABLE, "hospital_mortality"),
        "mimic": (Availability.AVAILABLE, "hospital_mortality"),
    },
    "demographics": {
        "eicu": (Availability.AVAILABLE, "age_band, sex, race_ethnicity"),
        "mimic": (Availability.AVAILABLE, "age_band, sex, race_ethnicity"),
    },
    "hospital_comparison": {
        "eicu": (Availability.AVAILABLE, "hospital, peer_group"),
        "mimic": (
            Availability.NOT_IN_DATA,
            "MIMIC-IV is one hospital (BIDMC); there are no peers to compare.",
        ),
    },
    "severity_adjustment": {
        "eicu": (Availability.AVAILABLE, "severity_adjusted_icu_los"),
        "mimic": (
            Availability.NOT_IN_LIBRARY,
            "MIMIC-IV has no APACHE. SOFA exists in mimic-derived but is not a"
            " library metric yet; escalate to medium or high.",
        ),
    },
    "icu_readmission": {
        "eicu": (
            Availability.NOT_IN_LIBRARY,
            "Derivable from unitvisitnumber > 1; not a library metric yet.",
        ),
        "mimic": (
            Availability.NOT_IN_LIBRARY,
            "Derivable from icustays; not a library metric yet.",
        ),
    },
    "cost": {
        "eicu": (Availability.NOT_IN_DATA, _FINANCE),
        "mimic": (Availability.NOT_IN_DATA, _FINANCE),
    },
    "charges": {
        "eicu": (Availability.NOT_IN_DATA, _FINANCE),
        "mimic": (Availability.NOT_IN_DATA, _FINANCE),
    },
    "margin": {
        "eicu": (
            Availability.NOT_IN_DATA,
            _FINANCE + " Margin also needs revenue, which neither dataset has.",
        ),
        "mimic": (
            Availability.NOT_IN_DATA,
            _FINANCE + " Margin also needs revenue, which neither dataset has.",
        ),
    },
    "payer": {
        "eicu": (Availability.NOT_IN_DATA, "eICU-CRD has no insurance field."),
        "mimic": (
            Availability.NOT_IN_LIBRARY,
            "admissions.insurance is a coarse payer category; not a library"
            " metric yet.",
        ),
    },
    "staffing": {
        "eicu": (Availability.NOT_IN_DATA, "No nurse or physician staffing data."),
        "mimic": (Availability.NOT_IN_DATA, "No nurse or physician staffing data."),
    },
}


# Metric ids, definition ids and plain words that mean a catalog concept.
ALIASES: dict[str, str] = {
    "los": "icu_los",
    "length_of_stay": "icu_los",
    "icu_los_days": "icu_los",
    "los_population": "icu_los",
    "index_icu_stay": "icu_los",
    "mortality": "hospital_mortality",
    "death": "hospital_mortality",
    "age_band": "demographics",
    "sex": "demographics",
    "race_ethnicity": "demographics",
    "hospital": "hospital_comparison",
    "peer_group": "hospital_comparison",
    "peers": "hospital_comparison",
    "icu_los_oe": "severity_adjustment",
    "severity_adjusted_icu_los": "severity_adjustment",
    "apache": "severity_adjustment",
    "readmission": "icu_readmission",
    "insurance": "payer",
    "age": "demographics",
    "gender": "demographics",
    "ethnicity": "demographics",
    "race": "demographics",
    "hospital_id": "hospital_comparison",
    "discharge_status": "hospital_mortality",
    "revenue": "margin",
    "reimbursement": "margin",
    "product_margin": "margin",
    "profit": "margin",
    "cost_per_day": "cost",
    "cost_per_icu_day": "cost",
}


def check(concepts: list[str], family: str) -> list[dict[str, str]]:
    """Report availability of each concept on a dataset family.

    Accepts catalog names, metric ids, definition ids and the aliases above.
    Anything else is ``unknown_concept`` with the valid names, so a caller
    can tell "not a word I know" from "known, not built yet".
    """
    out = []
    for raw in concepts:
        c = ALIASES.get(raw.strip().lower(), raw.strip().lower())
        if c not in CATALOG:
            out.append(
                {
                    "concept": raw,
                    "status": str(Availability.UNKNOWN),
                    "detail": "Use one of: " + ", ".join(CATALOG),
                }
            )
            continue
        status, reason = CATALOG[c].get(
            family, (Availability.NOT_IN_LIBRARY, "Not catalogued for this dataset.")
        )
        out.append({"concept": raw, "status": str(status), "detail": reason})
    return out
