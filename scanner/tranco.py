"""Download the Tranco top-sites list and take a reproducible sample.

Tranco is a research-oriented ranking that is hard to manipulate. We pin the
sample with a seed so anybody can regenerate the exact same 100 or 1,000
domains.
"""

from __future__ import annotations

import csv
import io
import random
import zipfile
from pathlib import Path

import requests

ZIP_URL = "https://tranco-list.eu/top-1m.csv.zip"
API_URL = "https://tranco-list.eu/api/lists/date/latest"


def download(dest: str = "data/tranco/top-1m.csv", timeout: int = 120) -> str:
    """Download and unpack the Tranco list. Returns the CSV path."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return str(path)

    response = requests.get(ZIP_URL, timeout=timeout)
    response.raise_for_status()

    if response.content[:2] == b"PK":  # a real zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            name = archive.namelist()[0]
            data = archive.read(name)
    else:  # plain CSV served directly
        data = response.content

    path.write_bytes(data)
    return str(path)


def load_domains(csv_path: str = "data/tranco/top-1m.csv") -> list[str]:
    """Read a Tranco CSV into a list of domains, in rank order."""
    domains: list[str] = []
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.reader(handle):
            if len(row) >= 2:
                domains.append(row[1].strip())
    return [d for d in domains if d]


def sample(
    domains: list[str],
    n: int = 100,
    seed: int = 413,
    pool: int = 10000,
) -> list[str]:
    """Take ``n`` domains at random from the top ``pool``.

    Sampling from the top 10,000 rather than the full million keeps the
    survey focused on sites people actually use.
    """
    candidates = domains[:pool]
    rng = random.Random(seed)
    picked = rng.sample(candidates, min(n, len(candidates)))
    return sorted(picked)
