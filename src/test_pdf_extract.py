import pdfplumber
from pathlib import Path

pdf_path = Path(
    "data/raw/financials/ekholms/"
    "Ekholms Bildemontering Aktiebolag-bokslut-2022-04.pdf"
)

with pdfplumber.open(pdf_path) as pdf:
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted

print(text[:3000])