# ============================================================
# NSE SMART MARKET DASHBOARD V2
# FUNDAMENTAL ENGINE
# Created by Rakesh Nagapuri
# ============================================================

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CONFIGURATION
# ============================================================

CACHE_DIR = Path(
    "output/fundamental_cache"
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MAX_YAHOO_REQUESTS = 50

REQUEST_DELAY = 0.25


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return np.nan

        value = float(value)

        if not np.isfinite(value):
            return np.nan

        return value

    except (
        TypeError,
        ValueError
    ):

        return np.nan


def cache_path(symbol):

    safe_symbol = (
        str(symbol)
        .upper()
        .replace(
            ".NS",
            ""
        )
        .replace(
            "/",
            "_"
        )
    )

    return (
        CACHE_DIR /
        f"{safe_symbol}.json"
    )


def load_cache(symbol):

    path = cache_path(
        symbol
    )

    if not path.exists():
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except Exception:

        return None


def save_cache(
    symbol,
    data
):

    path = cache_path(
        symbol
    )

    try:

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            f"Cache save failed for "
            f"{symbol}: {error}"
        )


# ============================================================
# CAGR
# ============================================================

def calculate_cagr(
    start_value,
    end_value,
    years
):

    start_value = safe_float(
        start_value
    )

    end_value = safe_float(
        end_value
    )

    if (
        pd.isna(start_value) or
        pd.isna(end_value) or
        start_value <= 0 or
        end_value <= 0 or
        years <= 0
    ):

        return np.nan

    try:

        return (
            (
                end_value /
                start_value
            )
            ** (1 / years)
            - 1
        ) * 100

    except Exception:

        return np.nan


# ============================================================
# ROCE
# ============================================================

def calculate_roce(info):

    # First preference: Yahoo supplied ROCE
    direct_roce = safe_float(
        info.get(
            "returnOnCapitalEmployed"
        )
    )

    if not pd.isna(
        direct_roce
    ):

        # Yahoo may return decimal
        if abs(direct_roce) <= 5:

            return direct_roce * 100

        return direct_roce

    # --------------------------------------------------------
    # Fallback calculation
    # ROCE = EBIT / Capital Employed
    # Capital Employed = Total Assets - Current Liabilities
    # --------------------------------------------------------

    operating_income = safe_float(
        info.get(
            "operatingIncome"
        )
    )

    total_assets = safe_float(
        info.get(
            "totalAssets"
        )
    )

    current_liabilities = safe_float(
        info.get(
            "currentLiabilities"
        )
    )

    if (
        pd.isna(operating_income) or
        pd.isna(total_assets) or
        pd.isna(current_liabilities)
    ):

        return np.nan

    capital_employed = (
        total_assets -
        current_liabilities
    )

    if capital_employed <= 0:
        return np.nan

    return (
        operating_income /
        capital_employed
    ) * 100


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

def score_fundamentals(row):

    score = 0.0
    available_weight = 0.0

    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = safe_float(
        row.get("roe")
    )

    if not pd.isna(roe):

        available_weight += 15

        if roe >= 20:
            score += 15

        elif roe >= 15:
            score += 12

        elif roe >= 10:
            score += 9

        elif roe >= 5:
            score += 5

        else:
            score += 2

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    roce = safe_float(
        row.get("roce")
    )

    if not pd.isna(roce):

        available_weight += 15

        if roce >= 20:
            score += 15

        elif roce >= 15:
            score += 12

        elif roce >= 10:
            score += 9

        elif roce >= 5:
            score += 5

        else:
            score += 2

    # --------------------------------------------------------
    # Revenue Growth
    # --------------------------------------------------------

    revenue_growth = safe_float(
        row.get(
            "revenue_cagr"
        )
    )

    if pd.isna(
        revenue_growth
    ):

        revenue_growth = safe_float(
            row.get(
                "revenue_growth"
            )
        )

    if not pd.isna(
        revenue_growth
    ):

        available_weight += 10

        if revenue_growth >= 20:
            score += 10

        elif revenue_growth >= 15:
            score += 8

        elif revenue_growth >= 10:
            score += 6

        elif revenue_growth >= 5:
            score += 4

        elif revenue_growth >= 0:
            score += 2

    # --------------------------------------------------------
    # Profit Growth
    # --------------------------------------------------------

    profit_growth = safe_float(
        row.get(
            "profit_cagr"
        )
    )

    if pd.isna(
        profit_growth
    ):

        profit_growth = safe_float(
            row.get(
                "earnings_growth"
            )
        )

        if not pd.isna(
            profit_growth
        ):

            profit_growth *= 100

    if not pd.isna(
        profit_growth
    ):

        available_weight += 10

        if profit_growth >= 20:
            score += 10

        elif profit_growth >= 15:
            score += 8

        elif profit_growth >= 10:
            score += 6

        elif profit_growth >= 5:
            score += 4

        elif profit_growth >= 0:
            score += 2

    # --------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------

    debt_equity = safe_float(
        row.get(
            "debt_equity"
        )
    )

    if not pd.isna(
        debt_equity
    ):

        available_weight += 10

        if debt_equity <= 0.25:
            score += 10

        elif debt_equity <= 0.50:
            score += 8

        elif debt_equity <= 1.00:
            score += 6

        elif debt_equity <= 2.00:
            score += 3

    # --------------------------------------------------------
    # Profit Margin
    # --------------------------------------------------------

    margin = safe_float(
        row.get(
            "profit_margin"
        )
    )

    if not pd.isna(
        margin
    ):

        if abs(margin) <= 2:
            margin *= 100

        available_weight += 10

        if margin >= 20:
            score += 10

        elif margin >= 15:
            score += 8

        elif margin >= 10:
            score += 6

        elif margin >= 5:
            score += 4

        elif margin >= 0:
            score += 2

    # --------------------------------------------------------
    # PE
    # --------------------------------------------------------

    pe = safe_float(
        row.get("pe")
    )

    if not pd.isna(pe):

        available_weight += 10

        if 0 < pe <= 15:
            score += 10

        elif pe <= 25:
            score += 8

        elif pe <= 35:
            score += 6

        elif pe <= 50:
            score += 3

    # --------------------------------------------------------
    # Normalize score
    # --------------------------------------------------------

    if available_weight <= 0:

        return np.nan

    return (
        score /
        available_weight
    ) * 100


# ============================================================
# QUALITY
# ============================================================

def determine_quality(score):

    if pd.isna(score):
        return "Unavailable"

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
# YAHOO FUNDAMENTAL FETCH
# ============================================================

def fetch_yahoo_fundamentals(
    symbol
):

    yahoo_symbol = (
        str(symbol)
        .upper()
        .replace(
            ".NS",
            ""
        ) +
        ".NS"
    )

    ticker = yf.Ticker(
        yahoo_symbol
    )

    info = ticker.info

    if not info:

        return None

    data = {

        "symbol":
            str(symbol)
            .upper()
            .replace(
                ".NS",
                ""
            ),

        "yahoo_symbol":
            yahoo_symbol,

        "company_name":
            info.get(
                "longName"
            ),

        "sector":
            info.get(
                "sector"
            ),

        "industry":
            info.get(
                "industry"
            ),

        "market_cap":
            info.get(
                "marketCap"
            ),

        "enterprise_value":
            info.get(
                "enterpriseValue"
            ),

        "revenue":
            info.get(
                "totalRevenue"
            ),

        "gross_profit":
            info.get(
                "grossProfits"
            ),

        "operating_income":
            info.get(
                "operatingIncome"
            ),

        "ebitda":
            info.get(
                "ebitda"
            ),

        "net_income":
            info.get(
                "netIncomeToCommon"
            ),

        "eps":
            info.get(
                "trailingEps"
            ),

        "forward_eps":
            info.get(
                "forwardEps"
            ),

        "book_value":
            info.get(
                "bookValue"
            ),

        "total_debt":
            info.get(
                "totalDebt"
            ),

        "total_cash":
            info.get(
                "totalCash"
            ),

        "current_assets":
            info.get(
                "totalCurrentAssets"
            ),

        "current_liabilities":
            info.get(
                "totalCurrentLiabilities"
            ),

        "roe":
            (
                safe_float(
                    info.get(
                        "returnOnEquity"
                    )
                ) * 100
                if not pd.isna(
                    safe_float(
                        info.get(
                            "returnOnEquity"
                        )
                    )
                )
                else np.nan
            ),

        "roa":
            (
                safe_float(
                    info.get(
                        "returnOnAssets"
                    )
                ) * 100
                if not pd.isna(
                    safe_float(
                        info.get(
                            "returnOnAssets"
                        )
                    )
                )
                else np.nan
            ),

        "operating_margin":
            info.get(
                "operatingMargins"
            ),

        "profit_margin":
            info.get(
                "profitMargins"
            ),

        "gross_margin":
            info.get(
                "grossMargins"
            ),

        "ebitda_margin":
            info.get(
                "ebitdaMargins"
            ),

        "debt_equity":
            info.get(
                "debtToEquity"
            ),

        "current_ratio":
            info.get(
                "currentRatio"
            ),

        "quick_ratio":
            info.get(
                "quickRatio"
            ),

        "pe":
            info.get(
                "trailingPE"
            ),

        "forward_pe":
            info.get(
                "forwardPE"
            ),

        "peg":
            info.get(
                "pegRatio"
            ),

        "price_to_book":
            info.get(
                "priceToBook"
            ),

        "dividend_yield":
            info.get(
                "dividendYield"
            ),

        "earnings_growth":
            info.get(
                "earningsGrowth"
            ),

        "revenue_growth":
            info.get(
                "revenueGrowth"
            )
    }

    data["roce"] = calculate_roce(
        info
    )

    # --------------------------------------------------------
    # Normalize percentages
    # --------------------------------------------------------

    for column in [
        "operating_margin",
        "profit_margin",
        "gross_margin",
        "ebitda_margin",
        "dividend_yield"
    ]:

        value = safe_float(
            data.get(column)
        )

        if not pd.isna(value):

            if abs(value) <= 2:

                value *= 100

            data[column] = value

    # --------------------------------------------------------
    # Fundamental availability
    # --------------------------------------------------------

    important_fields = [
        "roe",
        "roce",
        "revenue",
        "net_income",
        "debt_equity",
        "profit_margin",
        "pe"
    ]

    available = sum(
        not pd.isna(
            safe_float(
                data.get(
                    field
                )
            )
        )
        for field in important_fields
    )

    data["fundamental_fields_available"] = (
        available
    )

    data["fundamental_status"] = (
        "Available"
        if available >= 2
        else "Limited"
    )

    data["fundamental_score"] = (
        score_fundamentals(
            data
        )
    )

    data["fundamental_quality"] = (
        determine_quality(
            data[
                "fundamental_score"
            ]
        )
    )

    data["retrieved_at"] = (
        pd.Timestamp.now(
            tz="Asia/Kolkata"
        ).isoformat()
    )

    return data


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def get_fundamentals(
    universe,
    symbols=None,
    use_cache=True
):

    if symbols is None:

        if (
            universe is None or
            universe.empty
        ):

            return pd.DataFrame()

        symbols = (
            universe[
                "SYMBOL"
            ]
            .dropna()
            .astype(str)
            .str.upper()
            .tolist()
        )

    symbols = list(
        dict.fromkeys(
            [
                str(symbol)
                .upper()
                .replace(
                    ".NS",
                    ""
                )
                for symbol in symbols
            ]
        )
    )

    print()
    print(
        "=" * 70
    )

    print(
        "FUNDAMENTAL ENGINE"
    )

    print(
        f"Requested stocks: "
        f"{len(symbols)}"
    )

    print(
        "=" * 70
    )

    results = []

    yahoo_requests = 0

    yahoo_blocked = False

    for index, symbol in enumerate(
        symbols,
        start=1
    ):

        # ----------------------------------------------------
        # Cache first
        # ----------------------------------------------------

        cached = None

        if use_cache:

            cached = load_cache(
                symbol
            )

        if cached:

            results.append(
                cached
            )

            continue

        # ----------------------------------------------------
        # Do not continue hammering Yahoo after 401.
        # ----------------------------------------------------

        if yahoo_blocked:

            continue

        if (
            yahoo_requests >=
            MAX_YAHOO_REQUESTS
        ):

            print(
                "Yahoo fundamental request "
                "limit reached for this run."
            )

            break

        try:

            yahoo_requests += 1

            print(
                f"Fundamentals "
                f"{index}/"
                f"{len(symbols)}: "
                f"{symbol}"
            )

            result = (
                fetch_yahoo_fundamentals(
                    symbol
                )
            )

            if result:

                save_cache(
                    symbol,
                    result
                )

                results.append(
                    result
                )

            time.sleep(
                REQUEST_DELAY
            )

        except Exception as error:

            message = str(
                error
            ).lower()

            print(
                f"Fundamental fetch failed "
                f"for {symbol}: {error}"
            )

            # ------------------------------------------------
            # Critical Yahoo authentication failure.
            # Stop making further requests.
            # ------------------------------------------------

            if (
                "401" in message
                or
                "unauthorized" in message
                or
                "invalid crumb" in message
                or
                "unable to access this feature"
                in message
            ):

                print()
                print(
                    "Yahoo Finance fundamental "
                    "access is currently unavailable."
                )

                print(
                    "Stopping further fundamental "
                    "requests for this run."
                )

                yahoo_blocked = True

    # ========================================================
    # RESULT
    # ========================================================

    if not results:

        print()
        print(
            "No fundamental data available."
        )

        print(
            "Technical analysis will continue "
            "without fabricated fundamentals."
        )

        return pd.DataFrame()

    result = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

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
        "roce",
        "fundamental_score"
    ]

    for column in numeric_columns:

        if column in result.columns:

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    if "fundamental_score" in result.columns:

        result = result.sort_values(
            "fundamental_score",
            ascending=False,
            na_position="last"
        )

    result = result.drop_duplicates(
        subset=[
            "symbol"
        ],
        keep="last"
    )

    result = result.reset_index(
        drop=True
    )

    print()
    print(
        f"Fundamental records available: "
        f"{len(result)}"
    )

    return result


# ============================================================
# STANDALONE
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=" * 70
    )

    print(
        "NSE SMART MARKET DASHBOARD V2"
    )

    print(
        "FUNDAMENTAL ENGINE"
    )

    print(
        "=" * 70
    )

    print()
    print(
        "Fundamental engine loaded successfully."
    )

    print(
        "Yahoo authentication failures are "
        "handled safely."
    )
