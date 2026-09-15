import pandas as pd
import numpy as np
import yfinance as yf
import json
import time
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# FUNDAMENTAL ENGINE — PRODUCTION V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = OUTPUT_DIR / "fundamental_cache"

FUNDAMENTAL_FILE = OUTPUT_DIR / "fundamentals.csv"


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return np.nan

        value = float(value)

        if np.isfinite(value):
            return value

        return np.nan

    except Exception:

        return np.nan


def calculate_cagr(start_value, end_value, years):

    start_value = safe_float(start_value)
    end_value = safe_float(end_value)

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
        or years <= 0
    ):

        return np.nan

    return (
        (end_value / start_value)
        ** (1 / years)
        - 1
    ) * 100


def calculate_margin(profit, revenue):

    profit = safe_float(profit)
    revenue = safe_float(revenue)

    if (
        pd.isna(profit)
        or pd.isna(revenue)
        or revenue == 0
    ):

        return np.nan

    return (
        profit / revenue
    ) * 100


# ============================================================
# CACHE
# ============================================================

def get_cache_file(symbol):

    clean_symbol = (
        str(symbol)
        .replace(".NS", "")
        .replace("/", "_")
        .replace("\\", "_")
    )

    return (
        CACHE_DIR
        / f"{clean_symbol}.json"
    )


def load_cached_fundamental(symbol):

    cache_file = get_cache_file(symbol)

    if not cache_file.exists():
        return None

    try:

        with open(
            cache_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return None


def save_cached_fundamental(
    symbol,
    data
):

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_file = get_cache_file(symbol)

    try:

        with open(
            cache_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                default=str
            )

    except Exception as e:

        print(
            f"Unable to save cache "
            f"{symbol}: {e}"
        )


# ============================================================
# YAHOO FUNDAMENTAL DATA
# ============================================================

def download_fundamental_data(
    symbol
):

    try:

        ticker = yf.Ticker(symbol)

        info = ticker.info

        if not info:

            return {}

        return info

    except Exception as e:

        print(
            f"Fundamental download failed "
            f"{symbol}: {e}"
        )

        return {}


# ============================================================
# FUNDAMENTAL EXTRACTION
# ============================================================

def extract_fundamentals(
    symbol,
    info
):

    if not info:

        return None

    market_cap = safe_float(
        info.get(
            "marketCap"
        )
    )

    enterprise_value = safe_float(
        info.get(
            "enterpriseValue"
        )
    )

    revenue = safe_float(
        info.get(
            "totalRevenue"
        )
    )

    gross_profit = safe_float(
        info.get(
            "grossProfits"
        )
    )

    operating_income = safe_float(
        info.get(
            "operatingIncome"
        )
    )

    ebitda = safe_float(
        info.get(
            "ebitda"
        )
    )

    net_income = safe_float(
        info.get(
            "netIncomeToCommon"
        )
    )

    eps = safe_float(
        info.get(
            "trailingEps"
        )
    )

    forward_eps = safe_float(
        info.get(
            "forwardEps"
        )
    )

    book_value = safe_float(
        info.get(
            "bookValue"
        )
    )

    total_debt = safe_float(
        info.get(
            "totalDebt"
        )
    )

    total_cash = safe_float(
        info.get(
            "totalCash"
        )
    )

    current_assets = safe_float(
        info.get(
            "totalCurrentAssets"
        )
    )

    current_liabilities = safe_float(
        info.get(
            "totalCurrentLiabilities"
        )
    )

    roe = safe_float(
        info.get(
            "returnOnEquity"
        )
    )

    roa = safe_float(
        info.get(
            "returnOnAssets"
        )
    )

    operating_margin = safe_float(
        info.get(
            "operatingMargins"
        )
    )

    profit_margin = safe_float(
        info.get(
            "profitMargins"
        )
    )

    gross_margin = safe_float(
        info.get(
            "grossMargins"
        )
    )

    ebitda_margin = safe_float(
        info.get(
            "ebitdaMargins"
        )
    )

    debt_to_equity = safe_float(
        info.get(
            "debtToEquity"
        )
    )

    current_ratio = safe_float(
        info.get(
            "currentRatio"
        )
    )

    quick_ratio = safe_float(
        info.get(
            "quickRatio"
        )
    )

    pe = safe_float(
        info.get(
            "trailingPE"
        )
    )

    forward_pe = safe_float(
        info.get(
            "forwardPE"
        )
    )

    peg = safe_float(
        info.get(
            "pegRatio"
        )
    )

    price_to_book = safe_float(
        info.get(
            "priceToBook"
        )
    )

    dividend_yield = safe_float(
        info.get(
            "dividendYield"
        )
    )

    earnings_growth = safe_float(
        info.get(
            "earningsGrowth"
        )
    )

    revenue_growth = safe_float(
        info.get(
            "revenueGrowth"
        )
    )

    return {

        "symbol": symbol,

        "company_name":
            info.get(
                "longName",
                info.get(
                    "shortName",
                    symbol
                )
            ),

        "sector":
            info.get(
                "sector",
                ""
            ),

        "industry":
            info.get(
                "industry",
                ""
            ),

        "market_cap":
            market_cap,

        "enterprise_value":
            enterprise_value,

        "revenue":
            revenue,

        "gross_profit":
            gross_profit,

        "operating_income":
            operating_income,

        "ebitda":
            ebitda,

        "net_income":
            net_income,

        "eps":
            eps,

        "forward_eps":
            forward_eps,

        "book_value":
            book_value,

        "total_debt":
            total_debt,

        "total_cash":
            total_cash,

        "current_assets":
            current_assets,

        "current_liabilities":
            current_liabilities,

        "roe":
            roe * 100
            if not pd.isna(roe)
            and abs(roe) < 10
            else roe,

        "roa":
            roa * 100
            if not pd.isna(roa)
            and abs(roa) < 10
            else roa,

        "operating_margin":
            operating_margin * 100
            if not pd.isna(operating_margin)
            and abs(operating_margin) < 10
            else operating_margin,

        "profit_margin":
            profit_margin * 100
            if not pd.isna(profit_margin)
            and abs(profit_margin) < 10
            else profit_margin,

        "gross_margin":
            gross_margin * 100
            if not pd.isna(gross_margin)
            and abs(gross_margin) < 10
            else gross_margin,

        "ebitda_margin":
            ebitda_margin * 100
            if not pd.isna(ebitda_margin)
            and abs(ebitda_margin) < 10
            else ebitda_margin,

        "debt_equity":
            debt_to_equity,

        "current_ratio":
            current_ratio,

        "quick_ratio":
            quick_ratio,

        "pe":
            pe,

        "forward_pe":
            forward_pe,

        "peg":
            peg,

        "price_to_book":
            price_to_book,

        "dividend_yield":
            dividend_yield,

        "earnings_growth":
            earnings_growth * 100
            if not pd.isna(earnings_growth)
            and abs(earnings_growth) < 10
            else earnings_growth,

        "revenue_growth":
            revenue_growth * 100
            if not pd.isna(revenue_growth)
            and abs(revenue_growth) < 10
            else revenue_growth,

        "fundamental_data_available":
            True
    }


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

def score_roe(roe):

    if pd.isna(roe):
        return 0

    if roe >= 25:
        return 15

    if roe >= 20:
        return 13

    if roe >= 15:
        return 10

    if roe >= 10:
        return 7

    if roe >= 5:
        return 3

    return 0


def score_roce(roce):

    if pd.isna(roce):
        return 0

    if roce >= 25:
        return 15

    if roce >= 20:
        return 13

    if roce >= 15:
        return 10

    if roce >= 10:
        return 7

    if roce >= 5:
        return 3

    return 0


def score_growth(growth):

    if pd.isna(growth):
        return 0

    if growth >= 20:
        return 10

    if growth >= 15:
        return 8

    if growth >= 10:
        return 6

    if growth >= 5:
        return 4

    if growth >= 0:
        return 2

    return 0


def score_debt(debt_equity):

    if pd.isna(debt_equity):
        return 5

    if debt_equity <= 0.25:
        return 10

    if debt_equity <= 0.50:
        return 8

    if debt_equity <= 1:
        return 6

    if debt_equity <= 2:
        return 3

    return 0


def score_margin(margin):

    if pd.isna(margin):
        return 0

    if margin >= 20:
        return 10

    if margin >= 15:
        return 8

    if margin >= 10:
        return 6

    if margin >= 5:
        return 3

    return 0


def score_valuation(pe):

    if pd.isna(pe) or pe <= 0:
        return 5

    if pe <= 15:
        return 10

    if pe <= 20:
        return 8

    if pe <= 30:
        return 6

    if pe <= 45:
        return 3

    return 1


def calculate_fundamental_score(
    row
):

    scores = []

    roe_score = score_roe(
        row.get(
            "roe",
            np.nan
        )
    )

    roce_score = score_roce(
        row.get(
            "roce",
            np.nan
        )
    )

    revenue_score = score_growth(
        row.get(
            "revenue_growth",
            np.nan
        )
    )

    profit_score = score_growth(
        row.get(
            "earnings_growth",
            np.nan
        )
    )

    debt_score = score_debt(
        row.get(
            "debt_equity",
            np.nan
        )
    )

    margin_score = score_margin(
        row.get(
            "profit_margin",
            np.nan
        )
    )

    valuation_score = score_valuation(
        row.get(
            "pe",
            np.nan
        )
    )

    scores.extend(
        [
            roe_score,
            roce_score,
            revenue_score,
            profit_score,
            debt_score,
            margin_score,
            valuation_score
        ]
    )

    # Maximum possible:
    # ROE       15
    # ROCE      15
    # Revenue   10
    # Earnings  10
    # Debt      10
    # Margin    10
    # Valuation 10
    #
    # Total = 80
    #
    # Normalize to 100.

    raw_score = sum(scores)

    return round(
        raw_score / 80 * 100,
        2
    )


# ============================================================
# FUNDAMENTAL QUALITY
# ============================================================

def classify_fundamental_quality(
    score
):

    if pd.isna(score):

        return "Data Unavailable"

    if score >= 80:

        return "Excellent"

    if score >= 65:

        return "Strong"

    if score >= 50:

        return "Average"

    if score >= 35:

        return "Weak"

    return "Poor"


# ============================================================
# SINGLE STOCK
# ============================================================

def analyze_stock(
    symbol,
    use_cache=True
):

    if use_cache:

        cached = load_cached_fundamental(
            symbol
        )

        if cached:

            return cached

    print(
        f"Fetching fundamentals: "
        f"{symbol}"
    )

    info = download_fundamental_data(
        symbol
    )

    if not info:

        return {

            "symbol": symbol,

            "fundamental_data_available":
                False,

            "fundamental_score":
                np.nan,

            "fundamental_quality":
                "Data Unavailable"
        }

    result = extract_fundamentals(
        symbol,
        info
    )

    if result is None:

        return None

    result[
        "fundamental_score"
    ] = calculate_fundamental_score(
        result
    )

    result[
        "fundamental_quality"
    ] = classify_fundamental_quality(
        result[
            "fundamental_score"
        ]
    )

    result[
        "data_source"
    ] = "Yahoo Finance"

    save_cached_fundamental(
        symbol,
        result
    )

    return result


# ============================================================
# UNIVERSE ANALYSIS
# ============================================================

def analyze_universe(
    universe,
    symbols=None,
    use_cache=True,
    delay=0.15
):

    if (
        universe is None
        or universe.empty
    ):

        return pd.DataFrame()


    if symbols is None:

        symbols = (
            universe[
                "YAHOO_SYMBOL"
            ]
            .dropna()
            .astype(str)
            .tolist()
        )


    results = []

    total = len(symbols)

    print()
    print("=" * 60)
    print("FUNDAMENTAL ANALYSIS")
    print("=" * 60)
    print(
        f"Stocks to analyze: {total}"
    )
    print("=" * 60)


    for number, symbol in enumerate(
        symbols,
        start=1
    ):

        print(
            f"[{number}/{total}] "
            f"{symbol}"
        )

        try:

            result = analyze_stock(
                symbol,
                use_cache=use_cache
            )

            if result:

                results.append(
                    result
                )

        except Exception as e:

            print(
                f"Fundamental error "
                f"{symbol}: {e}"
            )

        if delay > 0:

            time.sleep(delay)


    if not results:

        return pd.DataFrame()


    df = pd.DataFrame(
        results
    )


    numeric_columns = [

        "market_cap",
        "enterprise_value",
        "revenue",
        "gross_profit",
        "operating_income",
        "ebitda",
        "net_income",
        "eps",
        "forward_eps",
        "book_value",
        "total_debt",
        "total_cash",
        "current_assets",
        "current_liabilities",
        "roe",
        "roa",
        "operating_margin",
        "profit_margin",
        "gross_margin",
        "ebitda_margin",
        "debt_equity",
        "current_ratio",
        "quick_ratio",
        "pe",
        "forward_pe",
        "peg",
        "price_to_book",
        "dividend_yield",
        "earnings_growth",
        "revenue_growth",
        "fundamental_score"
    ]


    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )


    return df


# ============================================================
# SAVE
# ============================================================

def save_fundamentals(
    df
):

    if (
        df is None
        or df.empty
    ):

        print(
            "No fundamental data "
            "available to save."
        )

        return


    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    df.to_csv(
        FUNDAMENTAL_FILE,
        index=False
    )


    print()
    print(
        f"Saved fundamentals: "
        f"{FUNDAMENTAL_FILE}"
    )

    print(
        f"Stocks with data: "
        f"{len(df)}"
    )


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def get_fundamentals(
    universe,
    symbols=None
):

    df = analyze_universe(
        universe,
        symbols=symbols
    )

    save_fundamentals(
        df
    )

    return df


# ============================================================
# STANDALONE
# ============================================================

if __name__ == "__main__":

    from engines.nse_universe import (
        get_nse_universe
    )

    universe = get_nse_universe()

    if universe.empty:

        print(
            "NSE universe unavailable."
        )

    else:

        fundamentals = get_fundamentals(
            universe
        )

        if not fundamentals.empty:

            print()
            print(
                fundamentals[
                    [
                        "symbol",
                        "company_name",
                        "fundamental_score",
                        "fundamental_quality",
                        "roe",
                        "debt_equity",
                        "pe"
                    ]
                ]
                .head(20)
                .to_string(
                    index=False
                )
            )
