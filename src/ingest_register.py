"""
Orchestrate ingestion of ELV operator directories (Sweden).

This module coordinates ingestion across multiple complementary sources
that together describe the End-of-Life Vehicle (ELV) dismantling
landscape in Sweden.

Important:
    There is no single public national register of all authorised ELV
    dismantlers. Authorisation is granted regionally (länsstyrelser),
    while operational visibility is provided through overlapping
    industry directories and producer-responsibility systems.

Accordingly, this module DOES NOT scrape data directly.
It documents sources, dispatches ingestion jobs, and records metadata.

Sources (current scope):
    - SBR (Sveriges Bilåtervinnares Riksförbund):
        Primary baseline directory of independent recyclers,
        published by county (län).

    - Skrotfrag:
        Major producer-responsibility operator and market participant
        with its own national network of facilities.

    - Bilretur:
        Car manufacturers’ producer-responsibility system with a
        consumer-facing directory of affiliated dismantlers.

Enrichment (separate stage):
    - Bolagsverket:
        Legal entity validation (org.nr, status, registration dates).
        This is NOT an operational directory and is handled downstream.

Design principles:
    - Each source is ingested independently in its own module.
    - Raw data is archived unchanged under data/raw/<source>/.
    - No assumptions of completeness are made.
    - This module remains lightweight and declarative.

Status:
    Dispatcher scaffold implemented.
    Individual ingestion modules to be implemented incrementally.
"""

from datetime import datetime
from typing import List

# NOTE:
# We intentionally avoid importing ingestion modules at top-level
# until they exist, to keep this file runnable and stable.


SOURCES = [
    {
        "key": "sbr",
        "description": "Sveriges Bilåtervinnares Riksförbund directory",
        "module": "ingest_sbr",
        "enabled": True,
    },
    {
        "key": "skrotfrag",
        "description": "Skrotfrag facility network",
        "module": "ingest_skrotfrag",
        "enabled": False,  # enable once implemented
    },
    {
        "key": "bilretur",
        "description": "Bilretur dismantler directory",
        "module": "ingest_bilretur",
        "enabled": False,  # enable once implemented
    },
]


def list_sources() -> List[str]:
    """Return keys of all configured data sources."""
    return [src["key"] for src in SOURCES]


def ingest_all(enabled_only: bool = True):
    """
    Run ingestion for all configured sources.

    Parameters
    ----------
    enabled_only : bool, default True
        If True, only sources marked as enabled are ingested.
        If False, all sources are attempted.

    Notes
    -----
    - Each source module is responsible for its own I/O.
    - Failures in one source should not crash the entire run
      (to be handled in source-specific code).
    """
    run_timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"[ingest_register] Run started at {run_timestamp}")

    for src in SOURCES:
        if enabled_only and not src["enabled"]:
            print(f"[ingest_register] Skipping {src['key']} (disabled)")
            continue

        module_name = src["module"]
        print(f"[ingest_register] Ingesting source: {src['key']}")

        try:
            module = __import__(module_name)
            if not hasattr(module, "ingest"):
                raise AttributeError(
                    f"Module '{module_name}' has no ingest() function"
                )
            module.ingest()
        except Exception as exc:
            print(
                f"[ingest_register] ERROR in source '{src['key']}': {exc}"
            )

    print(f"[ingest_register] Run completed at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    ingest_all()