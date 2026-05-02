import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
import yfinance as yf

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24
ELECTRICITY_CACHE_FILE = CACHE_DIR / "electricity_se3.csv"
DIESEL_CACHE_FILE = CACHE_DIR / "diesel_se.csv"
LME_STEEL_CACHE_FILE = CACHE_DIR / "lme_steel_hrc_nw_europe.csv"
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "downloaded_data"
OKQ8_FILE = RAW_DATA_DIR / "Prishistorik_foretag_2.xlsx"
LME_STEEL_RAW_JSON_FILE = RAW_DATA_DIR / "lme_steel_hrc_nw_europe_chart.json"

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
    df["trend_30d"] = df["price_sek_mwh"].rolling(20).mean()
    df["vol_30d"] = df["price_sek_mwh"].rolling(20).std()

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
    df["trend_30d"] = df["price_sek_litre"].rolling(30, min_periods=20).mean()
    df["vol_30d"] = df["price_sek_litre"].rolling(30, min_periods=20).std()

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

# --------------------------------------------------
# FERROUS STEEL (LME HRC NW EUROPE / ARGUS)
# --------------------------------------------------


def parse_lme_steel_payload(payload, contract_month="Month 1"):
    """
    Parses LME Steel HRC NW Europe (Argus) chart payload.

    Returns:
    date | steel_usd_tonne
    """

    labels = payload.get("Labels", [])
    datasets = payload.get("Datasets", [])

    selected_dataset = None
    for dataset in datasets:
        if dataset.get("RowTitle") == contract_month:
            selected_dataset = dataset
            break

    if selected_dataset is None:
        print(f"⚠️ LME steel dataset not found for {contract_month}.")
        return pd.DataFrame()

    prices = selected_dataset.get("Data", [])

    if not labels or not prices:
        return pd.DataFrame()

    df = pd.DataFrame({
        "date": labels,
        "steel_usd_tonne": prices,
    })

    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["steel_usd_tonne"] = pd.to_numeric(df["steel_usd_tonne"], errors="coerce")

    df = df.dropna(subset=["date", "steel_usd_tonne"])
    df = df.sort_values("date")

    return df[["date", "steel_usd_tonne"]]


def fetch_lme_steel_hrc_nw_europe(start_date="2025-12-01", end_date=None, contract_month="Month 1"):
    """
    Fetches LME Steel HRC NW Europe (Argus) chart data from LME's public chart endpoint.

    Falls back to a locally saved browser-exported JSON payload if the LME endpoint blocks Python requests.

    Returns:
    date | steel_usd_tonne

    Notes:
    - Prices are shown by LME in USD per tonne.
    - This is used as a European ferrous-market proxy, not Swedish yard-level ELV scrap pricing.
    """

    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    url = "https://www.lme.com/api/trading-data/chart-data"

    params = {
        "datasourceId": "2d71123c-0e03-4995-bf85-cd9c897199eb",
        "startDate": start_date,
        "endDate": end_date,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.lme.com/metals/ferrous/lme-steel-hrc-nw-europe-argus",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return parse_lme_steel_payload(payload, contract_month=contract_month)

    except Exception as e:
        print(f"⚠️ Error fetching LME steel data: {e}")

    if LME_STEEL_RAW_JSON_FILE.exists():
        try:
            with open(LME_STEEL_RAW_JSON_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            print("ℹ️ Using locally saved LME steel chart JSON fallback.")
            return parse_lme_steel_payload(payload, contract_month=contract_month)
        except Exception as e:
            print(f"⚠️ Error reading local LME steel JSON fallback: {e}")

    return pd.DataFrame()


def get_lme_steel_hrc_nw_europe(force_refresh=False):
    """
    Returns LME Steel HRC NW Europe (Argus) prices.
    Uses a short cache because the LME endpoint is a public web endpoint.
    """

    if not force_refresh and is_cache_valid(LME_STEEL_CACHE_FILE):
        return pd.read_csv(LME_STEEL_CACHE_FILE, parse_dates=["date"])

    df = fetch_lme_steel_hrc_nw_europe()

    if df is None or df.empty:
        return pd.DataFrame()

    df.to_csv(LME_STEEL_CACHE_FILE, index=False)

    return df

# --------------------------------------------------
# METALS (GLOBAL – LME PROXIES)
# --------------------------------------------------

def fetch_metal_prices(days_back=365, force_refresh=False):
    """
    Returns:
    date | copper | aluminium | steel_proxy
    """

    tickers = {
        "copper": "HG=F",      # Copper futures, USD
        "aluminium": "ALI=F",  # Aluminium futures, USD
        "usdsek": "SEK=X"      # USD/SEK exchange rate
    }

    dfs = []

    for name, ticker in tickers.items():
        data = yf.download(ticker, period="1y", interval="1d", progress=False)

        if data.empty:
            continue

        close = data["Close"]

        # yfinance can return either a Series or a single-column DataFrame
        # depending on version/settings. Force it to a clean Series.
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce")
        close.name = name
        dfs.append(close)

    if not dfs:
        return pd.DataFrame()
    
    df = pd.concat(dfs, axis=1)

# --- CRITICAL: ensure expected columns always exist ---
    expected_cols = ["copper", "aluminium", "usdsek"]
    
    for col in expected_cols:
        if col not in df.columns:
            df[col] = np.nan

    df = df.reset_index().rename(columns={"Date": "date"})

# Ensure proper datetime and sorting
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

# Convert all to numeric safely
    for col in expected_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# --- SEK conversion (safe even if NaN) ---
    df["copper_sek"] = df["copper"] * df["usdsek"]
    df["aluminium_sek"] = df["aluminium"] * df["usdsek"]

# --- LME ferrous steel proxy ---
    steel_df = get_lme_steel_hrc_nw_europe(force_refresh=force_refresh)

    if not steel_df.empty:
        df = df.merge(steel_df, on="date", how="left")
        df["steel_usd_tonne"] = df["steel_usd_tonne"].ffill()
        df["ferrous_proxy_sek"] = df["steel_usd_tonne"] * df["usdsek"]
    else:
        df["steel_usd_tonne"] = np.nan
        df["ferrous_proxy_sek"] = np.nan

# Drop rows where we have no usable copper data
    df = df.dropna(subset=["copper_sek"])

    return df

# --------------------------------------------------
# METALS Get Data 
# --------------------------------------------------

def get_metal_prices(force_refresh=False):
    df = fetch_metal_prices(force_refresh=force_refresh)

    if df is None or df.empty:
        return pd.DataFrame()

    return df

# --------------------------------------------------
# METALS Compute Metrics
# --------------------------------------------------


def compute_metal_metrics(df):
    if df.empty:
        return {}, df

    df = df.copy()
    df = df.sort_values("date")

    # Ensure required columns exist
    if "copper_sek" not in df.columns:
        return {}, pd.DataFrame()

    if "aluminium_sek" not in df.columns:
        df["aluminium_sek"] = np.nan

    if "steel_usd_tonne" not in df.columns:
        df["steel_usd_tonne"] = np.nan

    if "ferrous_proxy_sek" not in df.columns:
        df["ferrous_proxy_sek"] = np.nan


    # Clean copper series before calculations
    df = df.dropna(subset=["copper_sek"])

    series = pd.to_numeric(df["copper_sek"], errors="coerce")
    df["copper_sek"] = series

    # Rolling structure for copper
    df["trend_30d"] = series.rolling(30, min_periods=10).mean()
    df["vol_30d"] = series.rolling(30, min_periods=10).std()

    df["upper"] = df["trend_30d"] + df["vol_30d"]
    df["lower"] = df["trend_30d"] - df["vol_30d"]

    # Metrics
    latest = series.iloc[-1]
    prev = series.iloc[-2] if len(series) > 1 else None
    change = latest - prev if prev is not None else None

    avg_7d = series.tail(7).mean()
    avg_30d = series.tail(30).mean()
    volatility = series.tail(30).std()

    prev_30d = series.tail(60).head(30).mean()

    trend = None
    if pd.notna(prev_30d) and prev_30d != 0:
        trend = (avg_30d - prev_30d) / prev_30d

    metrics = {
        "latest": float(round(latest, 2)),
        "change": float(round(change, 2)) if change is not None else None,
        "avg_7d": float(round(avg_7d, 2)),
        "avg_30d": float(round(avg_30d, 2)),
        "volatility": float(round(volatility, 2)),
        "trend": float(trend) if trend is not None else None
    }

    return metrics, df[
        [
            "date",
            "copper_sek",
            "aluminium_sek",
            "steel_usd_tonne",
            "ferrous_proxy_sek",
            "trend_30d",
            "vol_30d",
            "upper",
            "lower"
        ]
    ]
