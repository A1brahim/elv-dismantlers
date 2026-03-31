"""
Parse SBR raw HTML files into structured dismantler dataset.

Reads raw HTML from:
    data/raw/dismantlers/sbr/

Outputs:
    data/processed/dismantlers/sbr/sbr_dismantlers.csv
"""

from pathlib import Path
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR


RAW_DIR = Path(RAW_DATA_DIR) / "sbr"
OUT_DIR = Path(PROCESSED_DATA_DIR) / "sbr"


def ensure_output_dir():
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_county_from_filename(path: Path) -> str:
    """
    Extract county from filename like:
    sbr_orebro_lan_20260205_170744.html
    """
    name = path.stem  # without .html
    parts = name.split("_")

    # Remove prefix "sbr" and timestamp
    county_parts = parts[1:-2]
    county = " ".join(county_parts)

    return county.replace("_", " ").title()


def parse_html_file(path: Path) -> list[dict]:
    """
    Parse one SBR HTML file and return dismantler records.
    """

    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    county = extract_county_from_filename(path)

    records = []

    company_blocks = soup.find_all("div", class_="company-item")

    for block in company_blocks:
        content = block.find("div", class_="company-item-content")
        if not content:
            continue

        # Company name
        name_tag = content.find("h4")
        company = name_tag.get_text(strip=True) if name_tag else None

        # City
        city_tag = content.find("h5")
        city = city_tag.get_text(strip=True) if city_tag else None

        address = None
        postcode = None
        phone = None
        email = None
        website = None

        for p in content.find_all("p"):
            text = p.get_text(strip=True)

            if "Adress:" in text:
                address = text.replace("Adress:", "").strip()

            elif "Postnr:" in text:
                postcode = text.replace("Postnr:", "").strip()

            elif "Telefonnr:" in text:
                phone = text.replace("Telefonnr:", "").strip()

            elif "E-post:" in text:
                email_link = p.find("a")
                if email_link:
                    email = email_link.get_text(strip=True)

            elif "Webbplats:" in text:
                site_link = p.find("a")
                if site_link:
                    website = site_link.get("href")

        records.append(
            {
                "county": county,
                "company": company,
                "city": city,
                "address": address,
                "postcode": postcode,
                "phone": phone,
                "email": email,
                "website": website,
                "source": "SBR",
            }
        )

    return records


def parse_all():
    ensure_output_dir()

    print("[parse_sbr] Parsing SBR raw HTML files")

    all_records = []

    for path in RAW_DIR.glob("*.html"):
        print(f"[parse_sbr] Processing: {path.name}")
        records = parse_html_file(path)
        all_records.extend(records)

    df = pd.DataFrame(all_records)

    df = df.drop_duplicates(subset=["company", "address", "county"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUT_DIR / f"sbr_dismantlers_{timestamp}.csv"

    df.to_csv(output_path, index=False)

    print(f"[parse_sbr] Saved structured dataset: {output_path}")
    print(f"[parse_sbr] Total companies: {len(df)}")


if __name__ == "__main__":
    parse_all()