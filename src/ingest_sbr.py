"""
Ingest ELV dismantler directory from SBR (Sveriges Bilåtervinnares Riksförbund).

SBR publishes a county-based (län) directory of affiliated vehicle recyclers.
This module ingests the directory by iterating over counties and archiving
the raw HTML responses for transparency and reproducibility.

Scope:
    - Source: sbrservice.se
    - Unit of observation: dismantler / recycler site
    - Coverage: SBR-affiliated operators only (not exhaustive nationally)

Design choices:
    - Raw HTML is saved unchanged
    - No parsing into tables at this stage
    - Parsing & cleaning handled downstream
"""

import time
from pathlib import Path
from datetime import datetime

import requests

from config import RAW_DATA_DIR


BASE_URL = "https://sbrservice.se/skrota-din-bil-bilskrot/bildemonterare"
OUTPUT_DIR = Path(RAW_DATA_DIR) / "sbr"

# Conservative crawl settings
REQUEST_TIMEOUT = 15
SLEEP_SECONDS = 2


# Known län values as used by the SBR dropdown
# (Can be extended or validated later)
COUNTIES = [
    "Blekinge län",
    "Dalarnas län",
    "Gotlands län",
    "Gävleborgs län",
    "Hallands län",
    "Jämtlands län",
    "Jönköpings län",
    "Kalmar län",
    "Kronobergs län",
    "Norrbottens län",
    "Skåne län",
    "Stockholms län",
    "Södermanlands län",
    "Uppsala län",
    "Värmlands län",
    "Västerbottens län",
    "Västernorrlands län",
    "Västmanlands län",
    "Västra Götalands län",
    "Örebro län",
    "Östergötlands län",
]


def ensure_output_dir() -> None:
    """Create output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_county(county: str) -> str:
    """
    Fetch SBR directory page for a given county.

    Parameters
    ----------
    county : str
        County (län) name as expected by the SBR endpoint.

    Returns
    -------
    str
        Raw HTML response text.
    """
    params = {
        "show_cardisassembler_at": county.lower().replace(" ", "-"),
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": "sweden-elv-dismantlers-research/0.1"
        },
    )
    response.raise_for_status()
    return response.text


def save_raw_html(county: str, html: str) -> Path:
    """
    Save raw HTML response to disk.

    Filenames are timestamped and county-labelled.

    Returns
    -------
    Path
        Path to saved file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_county = county.lower().replace(" ", "_").replace("ä", "a").replace("ö", "o").replace("å", "a")
    filename = f"sbr_{safe_county}_{timestamp}.html"
    path = OUTPUT_DIR / filename
    path.write_text(html, encoding="utf-8")
    return path


def ingest():
    """
    Ingest SBR directory by county.

    This function:
    - iterates over known counties
    - fetches the directory page
    - archives raw HTML responses
    """
    ensure_output_dir()

    print("[ingest_sbr] Starting SBR ingestion")
    print(f"[ingest_sbr] Output directory: {OUTPUT_DIR.resolve()}")

    for county in COUNTIES:
        print(f"[ingest_sbr] Fetching county: {county}")
        try:
            html = fetch_county(county)
            path = save_raw_html(county, html)
            print(f"[ingest_sbr] Saved: {path.name}")
        except Exception as exc:
            print(f"[ingest_sbr] ERROR for {county}: {exc}")

        time.sleep(SLEEP_SECONDS)

    print("[ingest_sbr] Ingestion completed")


if __name__ == "__main__":
    ingest()