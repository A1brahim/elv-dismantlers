# Sweden ELV Dismantlers

This project reconstructs the landscape of End-of-Life Vehicle (ELV)
dismantling operations in Sweden using a multi-source, institutionally
aware approach.

Rather than assuming the existence of a single national register, the
project explicitly models the **fragmented but overlapping structure**
through which ELV dismantling is authorised, organised, and operated.

The resulting dataset is designed to support:
- market structure analysis
- entry / exit dynamics
- geographic coverage
- fixed-asset reuse and business model transitions

---

## Institutional Context

ELV dismantling in Sweden operates under a federated system:

- **Naturvårdsverket**
  defines the national regulatory framework for ELV handling, recycling
  targets, and producer responsibility.

- **Länsstyrelserna** (County Administrative Boards) grant and revoke
  authorisations for ELV dismantling operations at the regional level.

- **Transportstyrelsen**
  administers vehicle deregistration and relies on authorised dismantlers
  to issue certificates of destruction (*skrotningsintyg*).

There is **no single publicly available national register** of all
authorised ELV dismantlers.

---

## Data Sources and Strategy

To reflect how the system actually operates, this project combines
multiple complementary sources:

### Operational Directories
- **Sveriges Bilåtervinnares Riksförbund (SBR)**  
  Industry association publishing a county-based directory of affiliated
  vehicle recyclers. This serves as the **primary baseline dataset**.

- **Skrotfrag**  
  A major producer-responsibility system and market participant operating
  its own national network of dismantling facilities.

- **Bilretur**  
  The car manufacturers’ producer-responsibility network, providing a
  consumer-facing directory of authorised dismantlers within its system.

### Legal Entity Validation
- **Bolagsverket**  
  Used to validate legal entity status (active, liquidated, bankrupt),
  registration dates, and legal form via organisation numbers.

Operational presence and legal existence are treated as **distinct but
linked layers**.

---

## Data Philosophy

- Raw source data is archived **unchanged** in `data/raw/`
- Each source is ingested independently and explicitly
- No assumptions of completeness are made
- Limitations and overlaps between sources are documented
- Legal status is validated separately from operational listings

Transparency is prioritised over false precision.

---

## Repository Structure (high level)
data/
raw/
sbr/
skrotfrag/
bilretur/
bolagsverket/
processed/
dismantlers/

src/
ingest_sbr.py
ingest_skrotfrag.py
ingest_bilretur.py
enrich_bolagsverket.py
clean_register.py
derive_history.py

## Project Status

Conceptual framework locked.
Primary data sources identified.
Initial ingestion scripts in progress.