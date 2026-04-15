from pathlib import Path
import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# --------------------------------------------------
# PATH CONFIG
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DASHBOARD_PATH = PROJECT_ROOT / "dashboard"
OUTPUT_PATH = PROJECT_ROOT / "outputs"

OUTPUT_PATH.mkdir(exist_ok=True)

YEARLY_CSV = DASHBOARD_PATH / "balance_sheet_yearly.csv"
SUMMARY_CSV = DASHBOARD_PATH / "balance_sheet_summary.csv"

PDF_FILE = OUTPUT_PATH / "balance_sheet_report.pdf"


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

yearly_df = pd.read_csv(YEARLY_CSV)
summary_df = pd.read_csv(SUMMARY_CSV)


# --------------------------------------------------
# HELPER: AUTO SCALE COLUMNS
# --------------------------------------------------

def autoscale_table(df, available_width, font_size=7):
    """
    Scale columns proportionally so total width fits inside page.
    """

    raw_widths = []

    for col in df.columns:
        max_len = max(
            df[col].astype(str).map(len).max(),
            len(str(col))
        )
        raw_widths.append(max_len * (font_size * 0.6))

    total_raw = sum(raw_widths)

    # Scale proportionally to fit page
    scale_factor = available_width / total_raw

    scaled_widths = [w * scale_factor for w in raw_widths]

    return scaled_widths


# --------------------------------------------------
# BUILD PDF
# --------------------------------------------------

doc = SimpleDocTemplate(
    str(PDF_FILE),
    pagesize=pagesizes.landscape(pagesizes.A4)
)

elements = []
styles = getSampleStyleSheet()

# ==================================================
# PAGE 1 — SUMMARY
# ==================================================

elements.append(
    Paragraph("<b>Balance Sheet Structural Report</b>", styles["Title"])
)
elements.append(Spacer(1, 20))

elements.append(
    Paragraph("<b>Structural Summary (Mean & Volatility)</b>", styles["Heading2"])
)
elements.append(Spacer(1, 10))

summary_df = summary_df.round(4)

summary_table_data = [summary_df.columns.tolist()] + summary_df.values.tolist()

available_width = doc.width

summary_table = Table(
    summary_table_data,
    colWidths=autoscale_table(summary_df, available_width, font_size=7),
    repeatRows=1
)

summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ('FONTSIZE', (0, 0), (-1, -1), 7),
]))

elements.append(summary_table)

# New Page
elements.append(PageBreak())


# ==================================================
# PAGE 2 — YEARLY METRICS
# ==================================================

elements.append(
    Paragraph("<b>Yearly Structural Metrics</b>", styles["Heading2"])
)
elements.append(Spacer(1, 10))

yearly_df = yearly_df.round(4)

yearly_table_data = [yearly_df.columns.tolist()] + yearly_df.values.tolist()

available_width = doc.width

yearly_table = Table(
    yearly_table_data,
    colWidths=autoscale_table(yearly_df, available_width, font_size=6),
    repeatRows=1
)

yearly_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ('FONTSIZE', (0, 0), (-1, -1), 6),
]))

elements.append(yearly_table)


# --------------------------------------------------
# BUILD
# --------------------------------------------------

doc.build(elements)

print("PDF exported to:", PDF_FILE.resolve())