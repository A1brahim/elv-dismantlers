import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24
ELECTRICITY_CACHE_FILE = CACHE_DIR / "electricity_se3.csv"
DIESEL_CACHE_FILE = CACHE_DIR / "diesel_se.csv"
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "downloaded_data"
OKQ8_FILE = RAW_DATA_DIR / "Prishistorik_foretag_2.xlsx"

# -------------------------------------------------
# HELPER: Check cache freshness
# -------------------------------------------------

def is_cache_valid(file_path, ttl_hours=None):
    if ttl_hours is None:
        ttl_hours = CACHE_TTL_HOURS

    if not file_path.exists():
        return False

    last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.now() - last_modified < timedelta(hours=ttl_hours)

# -------------------------------------------------
# FETCH: Electricity (SE3)
# -------------------------------------------------

def fetch_electricity_se3(days_back=365):
    records = []

    for i in range(days_back):
        date = datetime.today().date() - timedelta(days=i+1)
        url = f"https://www.elprisetjustnu.se/api/v1/prices/{date.strftime('%Y/%m-%d')}_SE3.json"

        try:
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                continue

            data = response.json()

            for entry in data:
                records.append({
                    "datetime": entry["time_start"],
                    "price_sek_kwh": entry["SEK_per_kWh"]
                })

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            time.sleep(1)  # Brief pause before retrying
            continue

    df = pd.DataFrame(records)

    if df.empty:
        return df

    # Robust datetime handling
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
    df = df.dropna(subset=["datetime"])

    # Daily aggregation (cleaner)
    df["date"] = df["datetime"].dt.tz_convert("Europe/Stockholm").dt.date
    df = df.groupby("date", as_index=False)["price_sek_kwh"].mean()

    # Convert to MWh
    df["price_sek_mwh"] = df["price_sek_kwh"] * 1000

    return df[["date", "price_sek_mwh"]]


# -------------------------------------------------
# PUBLIC FUNCTION (WITH CACHE)
# -------------------------------------------------

def get_electricity_se3(force_refresh=False):
    """
    Returns electricity prices (SE3) as DataFrame:
    date | price_sek_mwh
    """

    # Use cache if valid
    if not force_refresh and is_cache_valid(ELECTRICITY_CACHE_FILE):
        return pd.read_csv(ELECTRICITY_CACHE_FILE, parse_dates=["date"])

    # Fetch fresh data
    df = fetch_electricity_se3()

    # Check AFTER fetch
    if df.empty:
        print("⚠️ Warning: Electricity data is empty after fetch.")
        return df

    # Save to cache
    df.to_csv(ELECTRICITY_CACHE_FILE, index=False)

    return df


# -------------------------------------------------
# TREND METRICS 
# -------------------------------------------------

def compute_electricity_metrics(df):
    """
    Returns:
    - summary metrics
    - enriched dataframe (trend + volatility bands)
    """

    if df.empty:
        return {}, df

    df = df.copy()

    # -------------------------------
    # Time-series structure
    # -------------------------------
    df["trend_30d"] = df["price_sek_mwh"].rolling(30).mean()
    df["vol_30d"] = df["price_sek_mwh"].rolling(30).std()

    df["upper"] = df["trend_30d"] + df["vol_30d"]
    df["lower"] = df["trend_30d"] - df["vol_30d"]

    # -------------------------------
    # Summary metrics
    # -------------------------------
    series = df["price_sek_mwh"]

    latest = series.iloc[-1]
    avg_7d = series.tail(7).mean()
    avg_30d = series.tail(30).mean()
    volatility = series.tail(30).std()

    prev_30d = series.tail(60).head(30).mean()

    trend = None
    if prev_30d:
        trend = (avg_30d - prev_30d) / prev_30d

    metrics = {
        "latest": latest,
        "avg_7d": avg_7d,
        "avg_30d": avg_30d,
        "volatility": volatility,
        "trend": trend
    }

    return metrics, df


# --------------------------------------------------
# DIESEL (SWEDEN – OKQ8 SNAPSHOT)
# --------------------------------------------------

def fetch_okq8_diesel_snapshot():

    if not OKQ8_FILE.exists():
        print("⚠️ OKQ8 file not found.")
        return {}

    try:
        df = pd.read_excel(OKQ8_FILE, sheet_name="2026")
        df.columns = df.columns.str.strip()

        df = df[["Datum", "Diesel", "+/-.3"]].copy()

        df["date"] = pd.to_datetime(df["Datum"], format="%d/%m/%Y", errors="coerce")
        df["price_sek_litre"] = pd.to_numeric(df["Diesel"], errors="coerce")
        df["change_sek"] = pd.to_numeric(df["+/-.3"], errors="coerce") / 100

        df = df.dropna(subset=["date", "price_sek_litre"])
        df = df.sort_values("date")

        return df[["date", "price_sek_litre"]]

    except Exception as e:
        print(f"Error reading OKQ8 file: {e}")
        return pd.DataFrame()


def get_diesel_se(force_refresh=False):
    """
    Returns diesel time series from OKQ8 Excel
    """

    df = fetch_okq8_diesel_snapshot()

    if df is None or df.empty:
        return pd.DataFrame()

    return df


def compute_diesel_metrics(df):

    if df.empty:
        return {}, df

    df = df.copy()
    df = df.sort_values("date")

    # -------------------------------
    # Time-series structure
    # -------------------------------
    df["trend_30d"] = df["price_sek_litre"].rolling(30).mean()
    df["vol_30d"] = df["price_sek_litre"].rolling(30).std()

    df["upper"] = df["trend_30d"] + df["vol_30d"]
    df["lower"] = df["trend_30d"] - df["vol_30d"]

    # -------------------------------
    # Summary metrics
    # -------------------------------
    series = df["price_sek_litre"]

    latest = series.iloc[-1]
    prev = series.iloc[-2] if len(series) > 1 else None
    change = latest - prev if prev is not None else None

    avg_7d = series.tail(7).mean()
    avg_30d = series.tail(30).mean()
    volatility = series.tail(30).std()

    prev_30d = series.tail(60).head(30).mean()

    trend = None
    if prev_30d:
        trend = (avg_30d - prev_30d) / prev_30d

    metrics = {
        "latest": round(latest, 2),
        "change": round(change, 2) if change is not None else None,
        "avg_7d": round(avg_7d, 2),
        "avg_30d": round(avg_30d, 2),
        "volatility": round(volatility, 2),
        "trend": trend
    }

    return metrics, df