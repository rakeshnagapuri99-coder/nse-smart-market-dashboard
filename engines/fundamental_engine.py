# ============================================================
# NSE SMART MARKET DASHBOARD V2
# FUNDAMENTAL ENGINE
# Created by Rakesh Nagapuri
# ============================================================

import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CONFIGURATION
# ============================================================

CACHE_DIR = Path("output/fundamental_cache")
OUTPUT_FILE = Path("output/fundamentals.csv")

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    """
    Convert a value to float safely.
    """

    try:

        if value is None:
            return np.nan

        if isinstance(value, bool):
            return np.nan

        value = float(value)

        if not math.isfinite(value):
            return np.nan

        return value

    except (TypeError, ValueError):

        return np.nan


def normalize_percentage(value):
    """
    Yahoo Finance sometimes returns ratios as decimals
    and sometimes as percentages.

    Example:
        0.18 -> 18%
        18   -> 18%
    """

    value = safe_float(value)

    if pd.isna(value):
        return np.nan

    if abs(value) < 10:
        return value * 100

    return value


def clean_for_json(value):

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):

        if not np.isfinite(value):
            return None

        return float(value)

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    if pd.isna(value):
        return None

    return value


def safe_get(dictionary, key):

    if not isinstance(dictionary, dict):
        return None

    return dictionary.get(key)


# ============================================================
# CACHE
# ============================================================

def cache_file(symbol):

    safe_symbol = (
        str(symbol)
        .upper()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    return CACHE_DIR / f"{safe_symbol}.json"


def load_cache(symbol):

    file = cache_file(symbol)

    if not file.exists():
        return None

    try:

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return None


def save_cache(symbol, data):

    file = cache_file(symbol)

    try:

        cleaned = {
            key: clean_for_json(value)
            for key, value in data.items()
        }

        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                cleaned,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            f"Unable to save fundamental cache "
            f"for {symbol}: {error}"
        )


# ============================================================
# FINANCIAL STATEMENT HELPERS
# ============================================================

def get_statement_series(
    statement,
    possible_names
):
    """
    Find a financial statement row using several
    possible Yahoo Finance names.
    """

    if statement is None or statement.empty:
        return pd.Series(dtype=float)

    for name in possible_names:

        if name in statement.index:

            series = statement.loc[name]

            if isinstance(series, pd.DataFrame):
                series = series.iloc[0]

            return pd.to_numeric(
                series,
                errors="coerce"
            )

    return pd.Series(dtype=float)


def calculate_cagr_from_series(
    series,
    years=3
):
    """
    Calculate CAGR using the oldest available
    observation within the requested period.

    CAGR = (Ending / Beginning)^(1/n) - 1

    Requires positive beginning and ending values.
    """

    if series is None or len(series) < 2:
        return np.nan

    series = (
        pd.to_numeric(
            series,
            errors="coerce"
        )
        .dropna()
    )

    if len(series) < 2:
        return np.nan

    # Yahoo normally provides annual columns newest -> oldest.
    # Sort dates where possible.
    try:

        dates = pd.to_datetime(
            series.index,
            errors="coerce"
        )

        valid = ~dates.isna()

        if valid.any():

            series = series.loc[valid]
            dates = dates[valid]

            order = np.argsort(
                dates.values
            )

            series = series.iloc[order]

    except Exception:
        pass

    if len(series) < 2:
        return np.nan

    # Use approximately requested number of years.
    # With annual statements, selecting the oldest available
    # observation is preferable when fewer than the requested
    # years are available.
    periods = min(
        years,
        len(series) - 1
    )

    beginning = safe_float(
        series.iloc[-(periods + 1)]
    )

    ending = safe_float(
        series.iloc[-1]
    )

    if (
        pd.isna(beginning) or
        pd.isna(ending) or
        beginning <= 0 or
        ending <= 0
    ):
        return np.nan

    try:

        return (
            (
                ending /
                beginning
            ) ** (1 / periods)
            - 1
        ) * 100

    except Exception:

        return np.nan


def calculate_growth_from_series(
    series
):
    """
    Calculate latest year-over-year growth.
    """

    if series is None or len(series) < 2:
        return np.nan

    series = (
        pd.to_numeric(
            series,
            errors="coerce"
        )
        .dropna()
    )

    if len(series) < 2:
        return np.nan

    try:

        latest = safe_float(
            series.iloc[0]
        )

        previous = safe_float(
            series.iloc[1]
        )

        if (
            pd.isna(latest) or
            pd.isna(previous) or
            previous == 0
        ):
            return np.nan

        return (
            (latest - previous) /
            abs(previous)
        ) * 100

    except Exception:

        return np.nan


# ============================================================
# ROCE
# ============================================================

def calculate_roce_from_statements(
    ticker
):
    """
    Calculate ROCE when sufficient financial statement
    information is available.

    ROCE =
        EBIT / (Total Assets - Current Liabilities)

    This is only returned when the required inputs exist.
    """

    try:

        financials = ticker.financials

        balance_sheet = ticker.balance_sheet

        if (
            financials is None or
            financials.empty or
            balance_sheet is None or
            balance_sheet.empty
        ):
            return np.nan

        ebit = get_statement_series(
            financials,
            [
                "EBIT",
                "Operating Income"
            ]
        )

        assets = get_statement_series(
            balance_sheet,
            [
                "Total Assets"
            ]
        )

        current_liabilities = get_statement_series(
            balance_sheet,
            [
                "Current Liabilities",
                "Total Current Liabilities"
            ]
        )

        if (
            ebit.empty or
            assets.empty or
            current_liabilities.empty
        ):
            return np.nan

        common_dates = (
            ebit.index
            .intersection(assets.index)
            .intersection(
                current_liabilities.index
            )
        )

        if len(common_dates) == 0:
            return np.nan

        date = common_dates[0]

        ebit_value = safe_float(
            ebit.loc[date]
        )

        assets_value = safe_float(
            assets.loc[date]
        )

        liabilities_value = safe_float(
            current_liabilities.loc[date]
        )

        capital_employed = (
            assets_value -
            liabilities_value
        )

        if (
            pd.isna(ebit_value) or
            pd.isna(capital_employed) or
            capital_employed <= 0
        ):
            return np.nan

        return (
            ebit_value /
            capital_employed
        ) * 100

    except Exception:

        return np.nan


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

def calculate_fundamental_score(row):

    score = 0
    available = 0

    # --------------------------------------------------------
    # ROE — 15
    # --------------------------------------------------------

    roe = safe_float(
        row.get("roe")
    )

    if not pd.isna(roe):

        available += 15

        if roe >= 20:
            score += 15

        elif roe >= 15:
            score += 12

        elif roe >= 10:
            score += 8

        elif roe > 0:
            score += 4


    # --------------------------------------------------------
    # ROCE — 15
    # --------------------------------------------------------

    roce = safe_float(
        row.get("roce")
    )

    if not pd.isna(roce):

        available += 15

        if roce >= 20:
            score += 15

        elif roce >= 15:
            score += 12

        elif roce >= 10:
            score += 8

        elif roce > 0:
            score += 4


    # --------------------------------------------------------
    # Revenue Growth / CAGR — 10
    # --------------------------------------------------------

    revenue_cagr = safe_float(
        row.get("revenue_cagr")
    )

    revenue_growth = safe_float(
        row.get("revenue_growth")
    )

    revenue_metric = (
        revenue_cagr
        if not pd.isna(revenue_cagr)
        else revenue_growth
    )

    if not pd.isna(revenue_metric):

        available += 10

        if revenue_metric >= 20:
            score += 10

        elif revenue_metric >= 12:
            score += 8

        elif revenue_metric >= 5:
            score += 5

        elif revenue_metric > 0:
            score += 2


    # --------------------------------------------------------
    # Earnings / Profit Growth — 10
    # --------------------------------------------------------

    profit_cagr = safe_float(
        row.get("profit_cagr")
    )

    earnings_growth = safe_float(
        row.get("earnings_growth")
    )

    earnings_metric = (
        profit_cagr
        if not pd.isna(profit_cagr)
        else earnings_growth
    )

    if not pd.isna(earnings_metric):

        available += 10

        if earnings_metric >= 20:
            score += 10

        elif earnings_metric >= 12:
            score += 8

        elif earnings_metric >= 5:
            score += 5

        elif earnings_metric > 0:
            score += 2


    # --------------------------------------------------------
    # Debt / Equity — 10
    # --------------------------------------------------------

    debt_equity = safe_float(
        row.get("debt_equity")
    )

    if not pd.isna(debt_equity):

        available += 10

        if debt_equity <= 0.25:
            score += 10

        elif debt_equity <= 0.50:
            score += 8

        elif debt_equity <= 1:
            score += 5

        elif debt_equity <= 2:
            score += 2


    # --------------------------------------------------------
    # Profit Margin — 10
    # --------------------------------------------------------

    profit_margin = safe_float(
        row.get("profit_margin")
    )

    if not pd.isna(profit_margin):

        available += 10

        if profit_margin >= 20:
            score += 10

        elif profit_margin >= 12:
            score += 8

        elif profit_margin >= 5:
            score += 5

        elif profit_margin > 0:
            score += 2


    # --------------------------------------------------------
    # PE — 10
    # --------------------------------------------------------

    pe = safe_float(
        row.get("pe")
    )

    if not pd.isna(pe):

        available += 10

        if 0 < pe <= 15:
            score += 10

        elif pe <= 25:
            score += 8

        elif pe <= 40:
            score += 5

        elif pe <= 60:
            score += 2


    if available == 0:

        return np.nan

    return (
        score /
        available
    ) * 100


# ============================================================
# FUNDAMENTAL QUALITY
# ============================================================

def determine_fundamental_quality(
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
# SINGLE STOCK ANALYSIS
# ============================================================

def analyze_stock(
    symbol,
    use_cache=True
):

    symbol = str(symbol).upper().strip()

    if not symbol:
        return {}

    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    if use_cache:

        cached = load_cache(symbol)

        if cached:

            cached["symbol"] = symbol

            return cached

    yahoo_symbol = symbol

    if not yahoo_symbol.endswith(".NS"):
        yahoo_symbol = f"{symbol}.NS"

    result = {
        "symbol": symbol,
        "yahoo_symbol": yahoo_symbol,
        "fundamental_data_available": False
    }

    try:

        ticker = yf.Ticker(
            yahoo_symbol
        )

        info = ticker.info

        if not isinstance(info, dict):
            info = {}

        # ----------------------------------------------------
        # Basic company information
        # ----------------------------------------------------

        result["company_name"] = (
            safe_get(
                info,
                "longName"
            )
            or
            safe_get(
                info,
                "shortName"
            )
        )

        result["sector"] = safe_get(
            info,
            "sector"
        )

        result["industry"] = safe_get(
            info,
            "industry"
        )

        # ----------------------------------------------------
        # Valuation / size
        # ----------------------------------------------------

        result["market_cap"] = safe_float(
            safe_get(
                info,
                "marketCap"
            )
        )

        result["enterprise_value"] = safe_float(
            safe_get(
                info,
                "enterpriseValue"
            )
        )

        result["pe"] = safe_float(
            safe_get(
                info,
                "trailingPE"
            )
        )

        result["forward_pe"] = safe_float(
            safe_get(
                info,
                "forwardPE"
            )
        )

        result["peg"] = safe_float(
            safe_get(
                info,
                "pegRatio"
            )
        )

        result["price_to_book"] = safe_float(
            safe_get(
                info,
                "priceToBook"
            )
        )

        result["dividend_yield"] = normalize_percentage(
            safe_get(
                info,
                "dividendYield"
            )
        )

        # ----------------------------------------------------
        # Profitability
        # ----------------------------------------------------

        result["roe"] = normalize_percentage(
            safe_get(
                info,
                "returnOnEquity"
            )
        )

        result["roa"] = normalize_percentage(
            safe_get(
                info,
                "returnOnAssets"
            )
        )

        result["operating_margin"] = normalize_percentage(
            safe_get(
                info,
                "operatingMargins"
            )
        )

        result["profit_margin"] = normalize_percentage(
            safe_get(
                info,
                "profitMargins"
            )
        )

        result["gross_margin"] = normalize_percentage(
            safe_get(
                info,
                "grossMargins"
            )
        )

        result["ebitda_margin"] = normalize_percentage(
            safe_get(
                info,
                "ebitdaMargins"
            )
        )

        # ----------------------------------------------------
        # Growth
        # ----------------------------------------------------

        result["earnings_growth"] = normalize_percentage(
            safe_get(
                info,
                "earningsGrowth"
            )
        )

        result["revenue_growth"] = normalize_percentage(
            safe_get(
                info,
                "revenueGrowth"
            )
        )

        # ----------------------------------------------------
        # Balance sheet
        # ----------------------------------------------------

        result["debt_equity"] = safe_float(
            safe_get(
                info,
                "debtToEquity"
            )
        )

        result["current_ratio"] = safe_float(
            safe_get(
                info,
                "currentRatio"
            )
        )

        result["quick_ratio"] = safe_float(
            safe_get(
                info,
                "quickRatio"
            )
        )

        # ----------------------------------------------------
        # Financial values
        # ----------------------------------------------------

        result["revenue"] = safe_float(
            safe_get(
                info,
                "totalRevenue"
            )
        )

        result["gross_profit"] = safe_float(
            safe_get(
                info,
                "grossProfits"
            )
        )

        result["operating_income"] = safe_float(
            safe_get(
                info,
                "operatingIncome"
            )
        )

        result["ebitda"] = safe_float(
            safe_get(
                info,
                "ebitda"
            )
        )

        result["net_income"] = safe_float(
            safe_get(
                info,
                "netIncomeToCommon"
            )
        )

        result["eps"] = safe_float(
            safe_get(
                info,
                "trailingEps"
            )
        )

        result["forward_eps"] = safe_float(
            safe_get(
                info,
                "forwardEps"
            )
        )

        result["book_value"] = safe_float(
            safe_get(
                info,
                "bookValue"
            )
        )

        result["total_debt"] = safe_float(
            safe_get(
                info,
                "totalDebt"
            )
        )

        result["total_cash"] = safe_float(
            safe_get(
                info,
                "totalCash"
            )
        )

        result["current_assets"] = safe_float(
            safe_get(
                info,
                "totalCurrentAssets"
            )
        )

        result["current_liabilities"] = safe_float(
            safe_get(
                info,
                "totalCurrentLiabilities"
            )
        )

        # ----------------------------------------------------
        # ROCE
        # ----------------------------------------------------

        result["roce"] = normalize_percentage(
            safe_get(
                info,
                "returnOnCapitalEmployed"
            )
        )

        # If Yahoo doesn't provide ROCE, calculate it from
        # financial statements where possible.
        if pd.isna(result["roce"]):

            result["roce"] = calculate_roce_from_statements(
                ticker
            )

        # ----------------------------------------------------
        # Multi-year financial statements
        # ----------------------------------------------------

        try:

            financials = ticker.financials

        except Exception:

            financials = pd.DataFrame()

        revenue_series = get_statement_series(
            financials,
            [
                "Total Revenue",
                "Operating Revenue"
            ]
        )

        net_income_series = get_statement_series(
            financials,
            [
                "Net Income",
                "Net Income Common Stockholders",
                "Net Income Including Noncontrolling Interests"
            ]
        )

        ebit_series = get_statement_series(
            financials,
            [
                "EBIT",
                "Operating Income"
            ]
        )

        # ----------------------------------------------------
        # Revenue CAGR
        # ----------------------------------------------------

        result["revenue_cagr"] = (
            calculate_cagr_from_series(
                revenue_series,
                years=3
            )
        )

        result["revenue_cagr_3y"] = (
            result["revenue_cagr"]
        )

        # ----------------------------------------------------
        # Profit CAGR
        # ----------------------------------------------------

        result["profit_cagr"] = (
            calculate_cagr_from_series(
                net_income_series,
                years=3
            )
        )

        result["profit_cagr_3y"] = (
            result["profit_cagr"]
        )

        # ----------------------------------------------------
        # Latest financial statement growth
        # ----------------------------------------------------

        if pd.isna(
            result["revenue_growth"]
        ):

            result["revenue_growth"] = (
                calculate_growth_from_series(
                    revenue_series
                )
            )

        if pd.isna(
            result["earnings_growth"]
        ):

            result["earnings_growth"] = (
                calculate_growth_from_series(
                    net_income_series
                )
            )

        # ----------------------------------------------------
        # EPS CAGR
        # ----------------------------------------------------

        eps_series = pd.Series(
            dtype=float
        )

        if (
            not net_income_series.empty and
            not financials.empty
        ):

            try:

                shares = ticker.get_shares_full()

                if (
                    shares is not None and
                    not shares.empty
                ):

                    # EPS history from Yahoo shares data is
                    # not always aligned cleanly with annual
                    # financial statements, so only calculate
                    # where dates can be aligned.
                    shares = (
                        shares
                        .resample("YE")
                        .last()
                    )

                    shares.index = (
                        shares.index
                        .tz_localize(None)
                        if getattr(
                            shares.index,
                            "tz",
                            None
                        )
                        else shares.index
                    )

                    income = (
                        net_income_series.copy()
                    )

                    income.index = pd.to_datetime(
                        income.index,
                        errors="coerce"
                    )

                    income = income[
                        ~income.index.isna()
                    ]

                    if len(income) > 0:

                        eps_values = []

                        for date, value in income.items():

                            try:

                                nearest = (
                                    shares.index
                                    .to_series()
                                    .sub(date)
                                    .abs()
                                    .idxmin()
                                )

                                share_count = safe_float(
                                    shares.loc[nearest]
                                )

                                if (
                                    not pd.isna(share_count) and
                                    share_count > 0
                                ):

                                    eps_values.append(
                                        (
                                            date,
                                            value /
                                            share_count
                                        )
                                    )

                            except Exception:
                                continue

                        if eps_values:

                            eps_series = pd.Series(
                                {
                                    date: value
                                    for date, value
                                    in eps_values
                                }
                            )

            except Exception:
                eps_series = pd.Series(
                    dtype=float
                )

        result["eps_cagr"] = (
            calculate_cagr_from_series(
                eps_series,
                years=3
            )
        )

        result["eps_cagr_3y"] = (
            result["eps_cagr"]
        )

        # ----------------------------------------------------
        # Fundamental availability
        # ----------------------------------------------------

        important_fields = [
            "revenue",
            "net_income",
            "eps",
            "roe",
            "debt_equity",
            "pe"
        ]

        available_fields = sum(
            not pd.isna(
                result.get(field)
            )
            for field in important_fields
        )

        result["fundamental_data_available"] = (
            available_fields >= 2
        )

        # ----------------------------------------------------
        # Fundamental score
        # ----------------------------------------------------

        score_row = pd.Series(result)

        result["fundamental_score"] = (
            calculate_fundamental_score(
                score_row
            )
        )

        result["fundamental_quality"] = (
            determine_fundamental_quality(
                result["fundamental_score"]
            )
        )

        result["fundamental_status"] = (
            "Available"
            if result["fundamental_data_available"]
            else
            "Partial / Unavailable"
        )

        # ----------------------------------------------------
        # Cache
        # ----------------------------------------------------

        save_cache(
            symbol,
            result
        )

        return result

    except Exception as error:

        result["fundamental_status"] = (
            "Unavailable"
        )

        result["fundamental_quality"] = (
            "Data Unavailable"
        )

        result["error"] = str(error)

        return result


# ============================================================
# UNIVERSE ANALYSIS
# ============================================================

def analyze_universe(
    symbols,
    use_cache=True,
    delay=0.15
):

    if symbols is None:
        return pd.DataFrame()

    symbols = list(
        dict.fromkeys(
            [
                str(symbol)
                .upper()
                .strip()
                for symbol in symbols
                if str(symbol).strip()
            ]
        )
    )

    if not symbols:
        return pd.DataFrame()

    results = []

    total = len(symbols)

    print()
    print(
        f"Fundamental analysis: {total} stocks"
    )

    for index, symbol in enumerate(
        symbols,
        start=1
    ):

        try:

            result = analyze_stock(
                symbol,
                use_cache=use_cache
            )

            if result:
                results.append(result)

        except Exception as error:

            print(
                f"Fundamental error "
                f"{symbol}: {error}"
            )

        if delay > 0:
            time.sleep(delay)

        if (
            index == 1 or
            index % 25 == 0 or
            index == total
        ):

            print(
                f"Fundamentals progress: "
                f"{index}/{total}"
            )

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(
        results
    )


# ============================================================
# PUBLIC API
# ============================================================

def get_fundamentals(
    universe,
    symbols=None,
    use_cache=True
):

    if symbols is None:

        if isinstance(
            universe,
            pd.DataFrame
        ):

            if "YAHOO_SYMBOL" in universe.columns:

                symbols = (
                    universe[
                        "YAHOO_SYMBOL"
                    ]
                    .dropna()
                    .tolist()
                )

            elif "SYMBOL" in universe.columns:

                symbols = (
                    universe[
                        "SYMBOL"
                    ]
                    .dropna()
                    .tolist()
                )

        elif isinstance(
            universe,
            (list, tuple, set)
        ):

            symbols = list(universe)

    if not symbols:

        print(
            "No symbols supplied for fundamental analysis."
        )

        return pd.DataFrame()

    # Convert Yahoo symbols to NSE symbols
    cleaned_symbols = []

    for symbol in symbols:

        symbol = str(symbol).upper().strip()

        if symbol.endswith(".NS"):
            symbol = symbol[:-3]

        cleaned_symbols.append(
            symbol
        )

    data = analyze_universe(
        cleaned_symbols,
        use_cache=use_cache
    )

    if data.empty:

        print(
            "No fundamental data generated."
        )

        return data

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Saved fundamentals: {OUTPUT_FILE}"
    )

    print(
        f"Fundamental records: {len(data)}"
    )

    return data


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print(
        "NSE SMART MARKET DASHBOARD"
    )
    print(
        "FUNDAMENTAL ENGINE V2"
    )
    print("=" * 70)
    print()

    print(
        "Fundamental Engine loaded successfully."
    )

    print()
    print(
        "Fundamental metrics:"
    )

    metrics = [
        "Revenue",
        "Revenue Growth",
        "Revenue CAGR",
        "Net Income",
        "Profit Growth",
        "Profit CAGR",
        "EPS",
        "EPS CAGR",
        "ROE",
        "ROCE",
        "ROA",
        "Gross Margin",
        "Operating Margin",
        "Profit Margin",
        "EBITDA Margin",
        "Debt / Equity",
        "Current Ratio",
        "Quick Ratio",
        "PE",
        "Forward PE",
        "PEG",
        "Price / Book",
        "Dividend Yield",
        "Market Capitalisation",
        "Enterprise Value"
    ]

    for metric in metrics:
        print(f"- {metric}")

    print()
    print(
        "Fundamental scoring and quality classification enabled."
    )

    print()
    print("=" * 70)
