from pdf2image import convert_from_path
import pytesseract
from pathlib import Path

pdf_path = Path(
    "data/raw/financials/ekholms/"
    "Ekholms Bildemontering Aktiebolag-bokslut-2022-04.pdf"
)

pages = convert_from_path(pdf_path, dpi=300)

full_text = ""

for page in pages:
    text = pytesseract.image_to_string(page, lang="swe")
    full_text += text + "\n\n"

# Print section around Flerårsöversikt
if "Flerårsöversikt" in full_text:
    idx = full_text.index("Flerårsöversikt")
    print(full_text[idx:idx+2000])
else:
    print("Flerårsöversikt not found")