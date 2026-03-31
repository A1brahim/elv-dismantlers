from playwright.sync_api import sync_playwright
import pandas as pd
import re

url = "https://www.allabolag.se/bokslut/ekholms-bildemontering-aktiebolag/kumla/avfallshantering/2K0K91OI63IOK"

targets = [
    "Nettoomsättning",
    "Rörelseresultat efter avskrivningar",
    "Resultat efter finansiella poster",
    "Årets resultat",
]

data = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=60000)
    page.wait_for_load_state("networkidle")

    for label in targets:
        # Locate the label element directly in DOM
        label_locator = page.locator(f"text={label}").first

        if label_locator.count() == 0:
            continue

        # Climb two DOM levels to capture the full financial row container
        row = label_locator.locator("xpath=ancestor::*[self::div or self::tr][2]")

        row_text = row.inner_text()
        row_text = row_text.replace("−", "-")

        # Extract numeric values from that row only
        numbers = re.findall(r"-?\d+(?:[\s\xa0]\d{3})*", row_text)

        cleaned = []
        for num in numbers:
            cleaned_num = (
                num.replace(" ", "")
                .replace("\xa0", "")
                .strip()
            )
            if cleaned_num.lstrip("-").isdigit():
                cleaned.append(int(cleaned_num))

        # Keep only the last 5 yearly values (visible financial grid width)
        if len(cleaned) >= 5:
            last_five = cleaned[-5:]
            for idx, value in enumerate(last_five):
                data[f"{label} - Year_{idx+1}"] = value

    browser.close()

df = pd.DataFrame([data])
df.to_csv("ekholms_financials_full_history.csv", index=False)

print(df)