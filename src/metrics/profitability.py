import pandas as pd
import numpy as np


# --------------------------------------------------
# EBITDA Margin
# --------------------------------------------------

def compute_ebitda_margin(
    df: pd.DataFrame,
    revenue_column: str = "total_revenue",
    ebitda_column: str = "ebitda"
):

    df = df.copy()
    df["ebitda_margin"] = df[ebitda_column] / df[revenue_column]

    return df


# --------------------------------------------------
# Margin Volatility
# --------------------------------------------------

def compute_margin_volatility(df: pd.DataFrame):

    volatility = (
        df.groupby("company")["ebitda_margin"]
        .std()
        .reset_index()
        .rename(columns={"ebitda_margin": "margin_volatility"})
    )

    return volatility


# --------------------------------------------------
# Margin Dispersion (Cross-sectional inequality)
# --------------------------------------------------

def compute_margin_dispersion(df: pd.DataFrame, year_column: str = "year"):

    dispersion = (
        df.groupby(year_column)["ebitda_margin"]
        .std()
        .reset_index()
        .rename(columns={"ebitda_margin": "margin_dispersion"})
    )

    return dispersion


# --------------------------------------------------
# Profit Share (Share of total EBITDA)
# --------------------------------------------------

def compute_profit_share(
    df: pd.DataFrame,
    ebitda_column: str = "ebitda",
    year_column: str = "year"
):

    df = df.copy()

    total_ebitda_by_year = (
        df.groupby(year_column)[ebitda_column]
        .sum()
        .reset_index()
        .rename(columns={ebitda_column: "total_ebitda"})
    )

    df = df.merge(total_ebitda_by_year, on=year_column, how="left")

    df["profit_share"] = df[ebitda_column] / df["total_ebitda"]

    return df


# --------------------------------------------------
# Margin Premium vs Industry
# --------------------------------------------------

def compute_margin_premium(df: pd.DataFrame, year_column: str = "year"):

    industry_margin = (
        df.groupby(year_column)["ebitda_margin"]
        .mean()
        .reset_index()
        .rename(columns={"ebitda_margin": "industry_margin"})
    )

    df = df.merge(industry_margin, on=year_column, how="left")

    df["margin_premium"] = df["ebitda_margin"] - df["industry_margin"]

    return df