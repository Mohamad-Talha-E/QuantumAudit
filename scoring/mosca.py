"""Risk scoring: a naive baseline and a Mosca-based contextual score.

Mosca's inequality (Mosca, IEEE S&P 2018): data is at risk when

    shelf life (X) + migration time (Y) > time until a quantum computer (Z)

Rearranged, the safe window left after migrating is ``Z - Y``. If the data
must stay secret longer than that window, the host is high risk.
"""

from __future__ import annotations

from scoring.rules import classify

#: Default planning assumptions. Documented in results.md.
DEFAULT_SHELF_LIFE = 15
DEFAULT_MIGRATION = 3
DEFAULT_HORIZON = 15

#: The three quantum-arrival scenarios used by E6.
HORIZONS = (10, 15, 20)

#: Shelf lives explored by E6.
SHELF_LIVES = (5, 10, 15, 25)

MIGRATION_STEP = {
    "vulnerable": (
        "replace RSA/ECC key exchange with ML-KEM or a hybrid "
        "X25519+ML-KEM-768 group"
    ),
    "weakened": "move to AES-256 and SHA-2/SHA-3; double symmetric key sizes",
    "hybrid": "no urgent action; monitor standardisation and finish cert migration",
    "resistant": "no action required; re-assess when standards change",
    "unknown": "manual review: algorithm not recognised by the classifier",
}


def scenario_name(shelf_life: int, migration: int, horizon: int) -> str:
    """Stable key for a planning scenario, e.g. ``x15_y3_z15``."""
    return f"x{shelf_life}_y{migration}_z{horizon}"


def safe_window(migration_years: int, quantum_years: int) -> int:
    """Years of protection left after migrating (Z - Y)."""
    return quantum_years - migration_years


def score(
    record: dict,
    shelf_life_years: int = DEFAULT_SHELF_LIFE,
    migration_years: int = DEFAULT_MIGRATION,
    quantum_years: int = DEFAULT_HORIZON,
) -> tuple[str, str, str]:
    """Return ``(level, reason, migration_step)`` for one scanned host."""
    alg_class = classify(record)
    window = safe_window(migration_years, quantum_years)

    if alg_class in ("resistant", "hybrid"):
        level = "low"
    elif alg_class == "unknown":
        level = "medium"
    elif shelf_life_years >= window:
        level = "high"
    elif shelf_life_years >= window - 5:
        level = "medium"
    else:
        level = "low"

    reason = (
        f"{level.upper()}: {alg_class} cryptography; data shelf life "
        f"{shelf_life_years}y vs safe window {window}y "
        f"(quantum horizon {quantum_years}y, migration {migration_years}y)"
    )
    return level, reason, MIGRATION_STEP[alg_class]


def naive_score(record: dict) -> tuple[str, str, str]:
    """Baseline: flag every host that still uses RSA/ECC as high risk.

    No context, no timeline. This is the comparison point for E2: it shows
    how much the contextual model changes the verdict.
    """
    alg_class = classify(record)
    if alg_class in ("vulnerable", "hybrid"):
        return (
            "high",
            f"HIGH (naive rule): {alg_class} algorithm present",
            MIGRATION_STEP[alg_class],
        )
    return "low", "LOW (naive rule): no RSA/ECC detected", MIGRATION_STEP[alg_class]
