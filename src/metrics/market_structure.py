import pandas as pd


# --------------------------------------------------
# MARKET SHARE (PER YEAR)
# --------------------------------------------------

def compute_market_share(df: pd.DataFrame, value_column: str, year_column: str = "year"):
    df = df.copy()

    industry_total = (
        df.groupby(year_column)[value_column]
        .sum()
        .rename("industry_total")
    )

    df = df.merge(industry_total, on=year_column)
    df["market_share"] = df[value_column] / df["industry_total"]

    return df


# --------------------------------------------------
# AVERAGE MARKET SHARE (OVER PERIOD)
# --------------------------------------------------

def compute_average_market_share(df: pd.DataFrame, value_column: str):
    ms_df = compute_market_share(df, value_column)

    return (
        ms_df.groupby("company")["market_share"]
        .mean()
        .reset_index()
    )


# --------------------------------------------------
# CONCENTRATION RATIO (CR-N)
# --------------------------------------------------

def concentration_ratio(df: pd.DataFrame, value_column: str, year: int, top_n: int = 3):
    year_df = df[df["year"] == year]

    total = year_df[value_column].sum()

    top_total = (
        year_df
        .sort_values(value_column, ascending=False)
        .head(top_n)[value_column]
        .sum()
    )

    return top_total / total


# --------------------------------------------------
# HERFINDAHL-HIRSCHMAN INDEX (HHI)
# --------------------------------------------------

def compute_hhi(df: pd.DataFrame, value_column: str, year: int):
    year_df = df[df["year"] == year]
    total = year_df[value_column].sum()

    shares = year_df[value_column] / total
    return (shares ** 2).sum()


# --------------------------------------------------
# EFFECTIVE NUMBER OF FIRMS (1 / HHI)
# --------------------------------------------------

def effective_number_of_firms(df: pd.DataFrame, value_column: str, year: int):
    hhi = compute_hhi(df, value_column, year)
    if hhi == 0:
        return None
    return 1 / hhi


# --------------------------------------------------
# DOMINANCE GAP (Leader - Second)
# --------------------------------------------------

def dominance_gap(df: pd.DataFrame, value_column: str, year: int):
    year_df = df[df["year"] == year]

    total = year_df[value_column].sum()

    ranked = (
        year_df
        .sort_values(value_column, ascending=False)
        .reset_index(drop=True)
    )

    if len(ranked) < 2 or total == 0:
        return None

    leader_share = ranked.loc[0, value_column] / total
    second_share = ranked.loc[1, value_column] / total

    return leader_share - second_share


# --------------------------------------------------
# GINI COEFFICIENT (MARKET SHARE INEQUALITY)
# --------------------------------------------------

def compute_gini_market_share(df: pd.DataFrame, value_column: str, year: int):
    year_df = df[df["year"] == year]

    total = year_df[value_column].sum()
    if total == 0:
        return None

    shares = (year_df[value_column] / total).sort_values().values
    n = len(shares)

    if n == 0:
        return None

    cumulative = shares.cumsum()
    gini = (n + 1 - 2 * (cumulative.sum() / cumulative[-1])) / n

    return gini


# --------------------------------------------------
# HHI CHANGE (YEAR-OVER-YEAR)
# --------------------------------------------------

def hhi_change(df: pd.DataFrame, value_column: str):
    years = sorted(df["year"].unique())
    results = []

    for i in range(1, len(years)):
        hhi_prev = compute_hhi(df, value_column, years[i - 1])
        hhi_curr = compute_hhi(df, value_column, years[i])

        results.append({
            "year": years[i],
            "delta_hhi": hhi_curr - hhi_prev
        })

    return pd.DataFrame(results)


# --------------------------------------------------
# MARKET SHARE MOBILITY INDEX
# --------------------------------------------------

def market_share_mobility(df: pd.DataFrame, value_column: str):
    df = compute_market_share(df, value_column)

    years = sorted(df["year"].unique())
    results = []

    for i in range(1, len(years)):
        prev_year = df[df["year"] == years[i - 1]][["company", "market_share"]]
        curr_year = df[df["year"] == years[i]][["company", "market_share"]]

        merged = prev_year.merge(
            curr_year,
            on="company",
            how="outer",
            suffixes=("_prev", "_curr")
        ).fillna(0)

        mobility = (abs(merged["market_share_curr"] - merged["market_share_prev"]).sum()) / 2

        results.append({
            "year": years[i],
            "mobility_index": mobility
        })

    return pd.DataFrame(results)