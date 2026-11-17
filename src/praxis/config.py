"""Read praxis settings from ``~/.praxis/config.yaml``.

The file is the flat ``key: value`` format that ``bin/praxis-config`` writes.
``PRAXIS_STATE_DIR`` overrides the directory, as it does for the shell tools.
"""

from __future__ import annotations

import os
from pathlib import Path

ZDR_KEY = "credentialed_data_zdr"
ZDR_CONFIRMED = "confirmed"


def state_dir() -> Path:
    """Return the praxis state directory."""
    return Path(os.environ.get("PRAXIS_STATE_DIR", Path.home() / ".praxis"))


def read_config() -> dict[str, str]:
    """Return every key in config.yaml. Later lines win, as in praxis-config."""
    path = state_dir() / "config.yaml"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() and not key.startswith("#"):
            out[key.strip()] = value.strip()
    return out


def get(key: str) -> str | None:
    """Return one config value, or None when unset or empty."""
    return read_config().get(key) or None
