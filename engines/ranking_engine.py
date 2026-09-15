# ============================================================
# NSE SMART MARKET DASHBOARD V2
# RANKING ENGINE
# Created by Rakesh Nagapuri
# ============================================================

import numpy as np
import pandas as pd


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

    except (TypeError, ValueError):
        return np.nan


def clean_text(value):
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


def first_existing_column(df, columns):

    for column in columns:

        if column in df.columns:
            return column

    return None


# ============================================================
# TECHNICAL SCORE
# ============================================================

def calculate_technical_score(row):

    score = 0.0

    # --------------------------------------------------------
    # Trend — 20
    # --------------------------------------------------------

    trend = clean_text(
        row.get("Trend")
    ).lower()

    if trend == "strong uptrend":
        score += 20

    elif trend == "uptrend":
        score += 16

    elif trend == "sideways":
        score += 10

    elif trend == "downtrend":
        score += 5

    elif trend == "strong downtrend":
        score += 0


    # --------------------------------------------------------
    # Momentum — 15
    # --------------------------------------------------------

    momentum = clean_text(
        row.get("Momentum")
    ).lower()

    if momentum == "strong positive":
        score += 15

    elif momentum == "positive":
        score += 12

    elif momentum == "neutral":
        score += 8

    elif momentum == "negative":
        score += 4

    elif momentum == "strong negative":
        score += 0


    # --------------------------------------------------------
    # RSI — 15
    # --------------------------------------------------------

    rsi = safe_float(
        row.get("RSI14")
    )

    if not pd.isna(rsi):

        if 55 <= rsi <= 70:
            score += 15

        elif 50 <= rsi < 55:
            score += 12

        elif 45 <= rsi < 50:
            score += 8

        elif 30 <= rsi < 45:
            score += 4

        elif rsi > 70:
            # Strong momentum but potentially extended
            score += 10

        else:
            score += 0


    # --------------------------------------------------------
    # Volume — 15
    # --------------------------------------------------------

    volume_ratio = safe_float(
        row.get("Volume_Ratio")
    )

    if not pd.isna(volume_ratio):

        if volume_ratio >= 2.0:
            score += 15

        elif volume_ratio >= 1.5:
            score += 13

        elif volume_ratio >= 1.2:
            score += 10

        elif volume_ratio >= 0.8:
            score += 6

        else:
            score += 2


    # --------------------------------------------------------
    # Position — 15
    # --------------------------------------------------------

    distance_200 = safe_float(
        row.get("Distance_From_200DMA_Pct")
    )

    if not pd.isna(distance_200):

        if 0 <= distance_200 <= 10:
            score += 15

        elif 10 < distance_200 <= 20:
            score += 12

        elif -5 <= distance_200 < 0:
            score += 10

        elif 20 < distance_200 <= 30:
            score += 7

        elif distance_200 > 30:
            score += 4

        else:
            score += 3


    # --------------------------------------------------------
    # Breakout — 20
    # --------------------------------------------------------

    breakout = clean_text(
        row.get("Breakout_Status")
    ).lower()

    if breakout == "confirmed breakout":
        score += 20

    elif breakout == "breakout - volume confirmation required":
        score += 14

    elif breakout == "near breakout":
        score += 12

    elif breakout == "no breakout":
        score += 7


    return round(
        min(100, max(0, score)),
        2
    )


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

def calculate_fundamental_score(row):

    score = 0.0
    available_weight = 0.0

    # --------------------------------------------------------
    # ROE — 15
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

        available_weight += 15

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

        available_weight += 10

        if revenue_metric >= 20:
            score += 10

        elif revenue_metric >= 12:
            score += 8

        elif revenue_metric >= 5:
            score += 5

        elif revenue_metric > 0:
            score += 2


    # --------------------------------------------------------
    # Profit Growth / CAGR — 10
    # --------------------------------------------------------

    profit_cagr = safe_float(
        row.get("profit_cagr")
    )

    earnings_growth = safe_float(
        row.get("earnings_growth")
    )

    profit_metric = (
        profit_cagr
        if not pd.isna(profit_cagr)
        else earnings_growth
    )

    if not pd.isna(profit_metric):

        available_weight += 10

        if profit_metric >= 20:
            score += 10

        elif profit_metric >= 12:
            score += 8

        elif profit_metric >= 5:
            score += 5

        elif profit_metric > 0:
            score += 2


    # --------------------------------------------------------
    # Debt / Equity — 10
    # --------------------------------------------------------

    debt_equity = safe_float(
        row.get("debt_equity")
    )

    if not pd.isna(debt_equity):

        available_weight += 10

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

        available_weight += 10

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

        available_weight += 10

        if 0 < pe <= 15:
            score += 10

        elif pe <= 25:
            score += 8

        elif pe <= 40:
            score += 5

        elif pe <= 60:
            score += 2


    if available_weight == 0:
        return np.nan

    return round(
        (score / available_weight) * 100,
        2
    )


# ============================================================
# SECTOR SCORE
# ============================================================

def calculate_sector_adjustment(
    sector_strength
):

    strength = clean_text(
        sector_strength
    ).lower()

    mapping = {
        "leading": 5,
        "strong": 3,
        "neutral": 0,
        "weak": -3,
        "lagging": -5
    }

    return mapping.get(
        strength,
        0
    )


def calculate_sector_score(
    sector_strength
):

    strength = clean_text(
        sector_strength
    ).lower()

    mapping = {
        "leading": 100,
        "strong": 80,
        "neutral": 60,
        "weak": 40,
        "lagging": 20
    }

    return mapping.get(
        strength,
        np.nan
    )


# ============================================================
# MARKET REGIME ADJUSTMENT
# ============================================================

def get_market_regime_adjustment(
    market_regime,
    setup
):

    regime = clean_text(
        market_regime
    ).lower()

    setup_text = clean_text(
        setup
    ).lower()

    adjustment = 0

    # --------------------------------------------------------
    # Bullish market
    # --------------------------------------------------------

    if "bullish" in regime:

        if (
            "strong breakout" in setup_text or
            "momentum" in setup_text
        ):
            adjustment += 3

        elif "long-term" in setup_text:
            adjustment += 2


    # --------------------------------------------------------
    # Bullish but cautious
    # --------------------------------------------------------

    elif "cautious" in regime:

        if "strong breakout" in setup_text:
            adjustment += 1

        elif (
            "momentum" in setup_text or
            "breakout" in setup_text
        ):
            adjustment -= 1


    # --------------------------------------------------------
    # Sideways
    # --------------------------------------------------------

    elif "sideways" in regime:

        if (
            "breakout" in setup_text or
            "momentum" in setup_text
        ):
            adjustment -= 2


    # --------------------------------------------------------
    # Weak
    # --------------------------------------------------------

    elif "weak" in regime:

        if (
            "strong breakout" in setup_text or
            "momentum" in setup_text
        ):
            adjustment -= 4

        elif "dma" in setup_text:
            adjustment -= 2


    # --------------------------------------------------------
    # Bearish
    # --------------------------------------------------------

    elif "bearish" in regime:

        if (
            "strong breakout" in setup_text or
            "momentum" in setup_text
        ):
            adjustment -= 6

        elif "52w" in setup_text:
            adjustment -= 4

        elif "dma" in setup_text:
            adjustment -= 3


    return adjustment


# ============================================================
# SETUP CLASSIFICATION
# ============================================================

def determine_setup(row):

    price = safe_float(
        row.get("Close")
    )

    high_52w = safe_float(
        row.get("52W_High")
    )

    distance_200 = safe_float(
        row.get("Distance_From_200DMA_Pct")
    )

    volume_ratio = safe_float(
        row.get("Volume_Ratio")
    )

    trend = clean_text(
        row.get("Trend")
    ).lower()

    momentum = clean_text(
        row.get("Momentum")
    ).lower()

    breakout = clean_text(
        row.get("Breakout_Status")
    ).lower()

    # --------------------------------------------------------
    # Strong confirmed breakout
    # --------------------------------------------------------

    if breakout == "confirmed breakout":

        return "Strong Breakout Watch"


    # --------------------------------------------------------
    # 52W High
    # --------------------------------------------------------

    if (
        not pd.isna(distance_200) and
        not pd.isna(high_52w) and
        high_52w > 0
    ):

        distance_high = (
            (
                price -
                high_52w
            ) /
            high_52w
        ) * 100

        if distance_high >= -2:

            return "52W High Watch"


    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if (
        momentum in [
            "strong positive",
            "positive"
        ] and
        trend in [
            "strong uptrend",
            "uptrend"
        ]
    ):

        return "Momentum Watch"


    # --------------------------------------------------------
    # 200 DMA recovery
    # --------------------------------------------------------

    if not pd.isna(distance_200):

        if (
            -5 <= distance_200 <= 5 and
            momentum in [
                "positive",
                "strong positive"
            ]
        ):

            return "200 DMA Recovery Watch"


    # --------------------------------------------------------
    # Breakout requiring confirmation
    # --------------------------------------------------------

    if (
        breakout ==
        "breakout - volume confirmation required"
    ):

        return "Breakout Confirmation Required"


    # --------------------------------------------------------
    # Near breakout
    # --------------------------------------------------------

    if breakout == "near breakout":

        return "Pre-Breakout Watch"


    # --------------------------------------------------------
    # Weak
    # --------------------------------------------------------

    if (
        trend in [
            "strong downtrend",
            "downtrend"
        ] and
        momentum in [
            "strong negative",
            "negative"
        ]
    ):

        return "Weak / Avoid"


    return "Neutral Watch"


# ============================================================
# REASONS
# ============================================================

def generate_reasons(row):

    reasons = []

    trend = clean_text(
        row.get("Trend")
    )

    momentum = clean_text(
        row.get("Momentum")
    )

    breakout = clean_text(
        row.get("Breakout_Status")
    )

    rsi = safe_float(
        row.get("RSI14")
    )

    volume_ratio = safe_float(
        row.get("Volume_Ratio")
    )

    distance_200 = safe_float(
        row.get("Distance_From_200DMA_Pct")
    )

    distance_high = safe_float(
        row.get(
            "Distance_From_52W_High_Pct"
        )
    )

    roe = safe_float(
        row.get("roe")
    )

    roce = safe_float(
        row.get("roce")
    )

    revenue_cagr = safe_float(
        row.get("revenue_cagr")
    )

    profit_cagr = safe_float(
        row.get("profit_cagr")
    )

    debt_equity = safe_float(
        row.get("debt_equity")
    )

    # --------------------------------------------------------
    # Technical reasons
    # --------------------------------------------------------

    if trend:
        reasons.append(
            f"Trend: {trend}"
        )

    if momentum:
        reasons.append(
            f"Momentum: {momentum}"
        )

    if (
        not pd.isna(rsi) and
        50 <= rsi <= 70
    ):

        reasons.append(
            f"RSI {rsi:.1f} supports momentum"
        )

    if (
        not pd.isna(volume_ratio) and
        volume_ratio >= 1.2
    ):

        reasons.append(
            f"Volume {volume_ratio:.1f}x average"
        )

    if breakout and breakout != "No Breakout":

        reasons.append(
            f"Breakout status: {breakout}"
        )

    if (
        not pd.isna(distance_200) and
        -5 <= distance_200 <= 5
    ):

        reasons.append(
            f"Price is {distance_200:+.1f}% from 200 DMA"
        )

    if (
        not pd.isna(distance_high) and
        distance_high >= -5
    ):

        reasons.append(
            f"Within {abs(distance_high):.1f}% of 52W high"
        )

    # --------------------------------------------------------
    # Fundamental reasons
    # --------------------------------------------------------

    if (
        not pd.isna(roe) and
        roe >= 15
    ):

        reasons.append(
            f"ROE {roe:.1f}%"
        )

    if (
        not pd.isna(roce) and
        roce >= 15
    ):

        reasons.append(
            f"ROCE {roce:.1f}%"
        )

    if (
        not pd.isna(revenue_cagr) and
        revenue_cagr > 0
    ):

        reasons.append(
            f"Revenue CAGR {revenue_cagr:.1f}%"
        )

    if (
        not pd.isna(profit_cagr) and
        profit_cagr > 0
    ):

        reasons.append(
            f"Profit CAGR {profit_cagr:.1f}%"
        )

    if (
        not pd.isna(debt_equity) and
        debt_equity <= 0.5
    ):

        reasons.append(
            f"Debt/Equity {debt_equity:.2f}"
        )

    if not reasons:

        reasons.append(
            "Limited supporting data available"
        )

    return " • ".join(
        reasons[:8]
    )


# ============================================================
# RISK / REWARD
# ============================================================

def calculate_risk_reward(row):

    price = safe_float(
        row.get("Close")
    )

    support = safe_float(
        row.get("Support")
    )

    resistance = safe_float(
        row.get("Resistance")
    )

    if (
        pd.isna(price) or
        price <= 0 or
        pd.isna(support) or
        pd.isna(resistance)
    ):
        return np.nan

    risk = price - support
    reward = resistance - price

    if risk <= 0:
        return np.nan

    if reward <= 0:
        return 0.0

    return round(
        reward / risk,
        2
    )


# ============================================================
# MARKET REGIME
# ============================================================

def extract_market_regime(
    market_regime
):

    if market_regime is None:
        return "Unknown"

    if isinstance(
        market_regime,
        dict
    ):

        return (
            market_regime.get(
                "regime"
            )
            or
            market_regime.get(
                "market_regime"
            )
            or
            "Unknown"
        )

    return str(
        market_regime
    )


# ============================================================
# NORMALIZE TECHNICAL COLUMNS
# ============================================================

def normalize_columns(df):

    df = df.copy()

    rename_map = {}

    aliases = {

        "symbol": [
            "SYMBOL",
            "Symbol",
            "nse_symbol"
        ],

        "price": [
            "Price",
            "Close"
        ],

        "trend": [
            "trend",
            "Trend"
        ],

        "momentum": [
            "momentum",
            "Momentum"
        ],

        "technical_score": [
            "technical_score",
            "Technical_Score"
        ]

    }

    for target, candidates in aliases.items():

        if target in df.columns:
            continue

        source = first_existing_column(
            df,
            candidates
        )

        if source and source != target:
            rename_map[source] = target

    if rename_map:
        df = df.rename(
            columns=rename_map
        )

    return df


# ============================================================
# MERGE SECTOR DATA
# ============================================================

def merge_sector_data(
    stocks,
    sector_data
):

    if (
        stocks is None or
        stocks.empty or
        sector_data is None or
        sector_data.empty
    ):
        return stocks

    stocks = stocks.copy()
    sectors = sector_data.copy()

    # --------------------------------------------------------
    # Normalize sector columns
    # --------------------------------------------------------

    sector_name_col = first_existing_column(
        sectors,
        [
            "sector",
            "Sector",
            "name"
        ]
    )

    sector_strength_col = first_existing_column(
        sectors,
        [
            "strength",
            "Strength"
        ]
    )

    sector_score_col = first_existing_column(
        sectors,
        [
            "score",
            "Score"
        ]
    )

    if not sector_name_col:
        return stocks

    # --------------------------------------------------------
    # If stock sector is already available,
    # map Yahoo-style sector names to sector-analysis names.
    # --------------------------------------------------------

    stock_sector_col = first_existing_column(
        stocks,
        [
            "sector",
            "Sector"
        ]
    )

    if not stock_sector_col:
        return stocks

    sector_lookup = {}

    for _, sector_row in sectors.iterrows():

        name = clean_text(
            sector_row.get(
                sector_name_col
            )
        )

        if not name:
            continue

        sector_lookup[
            name.lower()
        ] = {
            "sector_strength":
                (
                    sector_row.get(
                        sector_strength_col
                    )
                    if sector_strength_col
                    else np.nan
                ),
            "sector_score":
                (
                    sector_row.get(
                        sector_score_col
                    )
                    if sector_score_col
                    else np.nan
                )
        }

    # Common Yahoo Finance -> NSE sector mappings.
    yahoo_to_nse = {

        "technology":
            "nifty it",

        "financial services":
            "nifty financial services",

        "healthcare":
            "nifty pharma",

        "basic materials":
            "nifty metal",

        "consumer defensive":
            "nifty fmcg",

        "energy":
            "nifty energy",

        "real estate":
            "nifty realty",

        "industrials":
            "nifty infrastructure",

        "communication services":
            "nifty media",

        "consumer cyclical":
            "nifty consumption",

    }

    def resolve_sector(value):

        text = clean_text(
            value
        )

        if not text:
            return None

        lower = text.lower()

        # Direct match
        if lower in sector_lookup:
            return lower

        # Yahoo mapping
        mapped = yahoo_to_nse.get(
            lower
        )

        if mapped and mapped in sector_lookup:
            return mapped

        # Partial matching
        for key in sector_lookup:

            if (
                lower in key or
                key in lower
            ):
                return key

        return None

    stocks["_sector_lookup_key"] = (
        stocks[stock_sector_col]
        .apply(resolve_sector)
    )

    stocks["sector_strength"] = (
        stocks["_sector_lookup_key"]
        .map(
            lambda key:
                sector_lookup.get(
                    key,
                    {}
                ).get(
                    "sector_strength",
                    np.nan
                )
        )
    )

    stocks["sector_score"] = (
        stocks["_sector_lookup_key"]
        .map(
            lambda key:
                sector_lookup.get(
                    key,
                    {}
                ).get(
                    "sector_score",
                    np.nan
                )
        )
    )

    stocks["sector_adjustment"] = (
        stocks["sector_strength"]
        .apply(
            calculate_sector_adjustment
        )
    )

    stocks = stocks.drop(
        columns=[
            "_sector_lookup_key"
        ],
        errors="ignore"
    )

    return stocks


# ============================================================
# MAIN RANKING
# ============================================================

def rank_stocks(
    technical_data,
    fundamental_data=None,
    sector_data=None,
    market_regime=None
):

    if (
        technical_data is None or
        technical_data.empty
    ):
        return pd.DataFrame()

    stocks = normalize_columns(
        technical_data
    )

    stocks = stocks.copy()

    # --------------------------------------------------------
    # Technical score
    # --------------------------------------------------------

    stocks["technical_score"] = (
        stocks.apply(
            calculate_technical_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Fundamental merge
    # --------------------------------------------------------

    if (
        fundamental_data is not None and
        not fundamental_data.empty
    ):

        fundamentals = fundamental_data.copy()

        if "symbol" not in fundamentals.columns:

            symbol_col = first_existing_column(
                fundamentals,
                [
                    "SYMBOL",
                    "Symbol"
                ]
            )

            if symbol_col:
                fundamentals = fundamentals.rename(
                    columns={
                        symbol_col:
                        "symbol"
                    }
                )

        if "symbol" in fundamentals.columns:

            fundamentals["symbol"] = (
                fundamentals["symbol"]
                .astype(str)
                .str.upper()
                .str.replace(
                    ".NS",
                    "",
                    regex=False
                )
            )

            stocks["symbol"] = (
                stocks["symbol"]
                .astype(str)
                .str.upper()
                .str.replace(
                    ".NS",
                    "",
                    regex=False
                )
            )

            fundamental_columns = [
                column
                for column in fundamentals.columns
                if column != "symbol"
            ]

            stocks = stocks.merge(
                fundamentals[
                    [
                        "symbol"
                    ] +
                    fundamental_columns
                ],
                on="symbol",
                how="left",
                suffixes=(
                    "",
                    "_fundamental"
                )
            )

    # --------------------------------------------------------
    # Sector merge
    # --------------------------------------------------------

    stocks = merge_sector_data(
        stocks,
        sector_data
    )

    # --------------------------------------------------------
    # Fundamental score
    # --------------------------------------------------------

    stocks["fundamental_score"] = (
        stocks.apply(
            calculate_fundamental_score,
            axis=1
        )
    )

    stocks["fundamental_quality"] = (
        stocks["fundamental_score"]
        .apply(
            lambda score:
                (
                    "Data Unavailable"
                    if pd.isna(score)
                    else
                    "Excellent"
                    if score >= 80
                    else
                    "Strong"
                    if score >= 65
                    else
                    "Average"
                    if score >= 50
                    else
                    "Weak"
                    if score >= 35
                    else
                    "Poor"
                )
        )
    )

    stocks["fundamental_status"] = (
        stocks["fundamental_score"]
        .apply(
            lambda score:
                (
                    "Available"
                    if not pd.isna(score)
                    else
                    "Unavailable"
                )
        )
    )

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    stocks["setup"] = (
        stocks.apply(
            determine_setup,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Reasons
    # --------------------------------------------------------

    stocks["reasons"] = (
        stocks.apply(
            generate_reasons,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Risk / Reward
    # --------------------------------------------------------

    stocks["risk_reward"] = (
        stocks.apply(
            calculate_risk_reward,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

    regime = extract_market_regime(
        market_regime
    )

    stocks["market_regime"] = regime

    stocks["market_regime_adjustment"] = (
        stocks["setup"]
        .apply(
            lambda setup:
                get_market_regime_adjustment(
                    regime,
                    setup
                )
        )
    )

    # --------------------------------------------------------
    # Overall score
    # --------------------------------------------------------

    def calculate_overall(row):

        technical = safe_float(
            row.get(
                "technical_score"
            )
        )

        fundamental = safe_float(
            row.get(
                "fundamental_score"
            )
        )

        sector_adjustment = safe_float(
            row.get(
                "sector_adjustment"
            )
        )

        market_adjustment = safe_float(
            row.get(
                "market_regime_adjustment"
            )
        )

        if pd.isna(technical):
            technical = 0

        # When fundamentals are available:
        # Technical 60% + Fundamental 40%
        if not pd.isna(fundamental):

            score = (
                technical * 0.60 +
                fundamental * 0.40
            )

        else:

            # Do not penalize stocks simply because
            # fundamentals weren't fetched.
            score = technical

        if pd.isna(sector_adjustment):
            sector_adjustment = 0

        if pd.isna(market_adjustment):
            market_adjustment = 0

        score += (
            sector_adjustment +
            market_adjustment
        )

        return round(
            max(
                0,
                min(
                    100,
                    score
                )
            ),
            2
        )

    stocks["overall_score"] = (
        stocks.apply(
            calculate_overall,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    stocks = stocks.sort_values(
        by=[
            "overall_score",
            "technical_score"
        ],
        ascending=[
            False,
            False
        ]
    ).reset_index(
        drop=True
    )

    stocks["rank"] = (
        np.arange(
            1,
            len(stocks) + 1
        )
    )

    # --------------------------------------------------------
    # Rating label
    # --------------------------------------------------------

    def rating_label(score):

        score = safe_float(score)

        if pd.isna(score):
            return "Unrated"

        if score >= 80:
            return "Excellent Setup"

        if score >= 70:
            return "Strong Setup"

        if score >= 60:
            return "Good Setup"

        if score >= 50:
            return "Watch"

        if score >= 40:
            return "Confirmation Required"

        return "Weak / Avoid"

    stocks["rating"] = (
        stocks["overall_score"]
        .apply(rating_label)
    )

    return stocks


# ============================================================
# WATCHLIST CREATION
# ============================================================

def create_watchlists(
    ranked_data,
    market_regime=None
):

    if (
        ranked_data is None or
        ranked_data.empty
    ):
        return {}

    data = ranked_data.copy()

    regime = extract_market_regime(
        market_regime
    )

    # --------------------------------------------------------
    # Helper
    # --------------------------------------------------------

    def filter_sorted(condition):

        result = data.loc[
            condition
        ].copy()

        return result.sort_values(
            by=[
                "overall_score",
                "technical_score"
            ],
            ascending=False
        ).reset_index(
            drop=True
        )

    # --------------------------------------------------------
    # Base conditions
    # --------------------------------------------------------

    trend_positive = data[
        "Trend"
    ].astype(str).str.lower().isin(
        [
            "strong uptrend",
            "uptrend"
        ]
    )

    momentum_positive = data[
        "Momentum"
    ].astype(str).str.lower().isin(
        [
            "strong positive",
            "positive"
        ]
    )

    momentum_negative = data[
        "Momentum"
    ].astype(str).str.lower().isin(
        [
            "strong negative",
            "negative"
        ]
    )

    distance_200 = pd.to_numeric(
        data[
            "Distance_From_200DMA_Pct"
        ],
        errors="coerce"
    )

    distance_high = pd.to_numeric(
        data[
            "Distance_From_52W_High_Pct"
        ],
        errors="coerce"
    )

    volume_ratio = pd.to_numeric(
        data[
            "Volume_Ratio"
        ],
        errors="coerce"
    )

    above_200 = (
        pd.to_numeric(
            data["Close"],
            errors="coerce"
        )
        >
        pd.to_numeric(
            data["SMA200"],
            errors="coerce"
        )
    )

    # --------------------------------------------------------
    # Next Day
    # --------------------------------------------------------

    next_day_condition = (
        data["setup"].astype(str)
        != "Weak / Avoid"
    )

    # In bearish/weak markets, prioritize stronger
    # confirmation-based setups.
    if (
        "bearish" in regime.lower() or
        "weak" in regime.lower()
    ):

        next_day_condition = (
            next_day_condition &
            (
                (
                    data["overall_score"] >= 60
                )
                |
                (
                    data["setup"].astype(str)
                    .isin(
                        [
                            "52W High Watch",
                            "200 DMA Recovery Watch"
                        ]
                    )
                )
            )
        )

    # --------------------------------------------------------
    # Intraday
    # --------------------------------------------------------

    intraday_condition = (
        volume_ratio >= 1.2
    ) & (
        ~momentum_negative
    ) & (
        data["overall_score"] >= 45
    )

    # --------------------------------------------------------
    # Swing
    # --------------------------------------------------------

    swing_condition = (
        trend_positive &
        momentum_positive &
        (
            data["overall_score"] >= 50
        )
    )

    # --------------------------------------------------------
    # Long term
    # --------------------------------------------------------

    long_term_condition = (
        above_200 &
        (
            data["overall_score"] >= 55
        )
    )

    # Prefer fundamental quality when available.
    fundamental_available = (
        ~data["fundamental_score"]
        .isna()
    )

    long_term_condition = (
        long_term_condition &
        (
            ~fundamental_available |
            (
                data["fundamental_score"] >= 50
            )
        )
    )

    # --------------------------------------------------------
    # 52W High
    # --------------------------------------------------------

    high_condition = (
        distance_high >= -5
    ) & (
        data["overall_score"] >= 50
    )

    # --------------------------------------------------------
    # 200 DMA Recovery
    # --------------------------------------------------------

    dma_condition = (
        distance_200 >= -5
    ) & (
        distance_200 <= 5
    ) & (
        momentum_positive
    )

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    momentum_condition = (
        momentum_positive &
        (
            data["overall_score"] >= 50
        )
    )

    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    breakout_condition = data[
        "Breakout_Status"
    ].astype(str).str.lower().isin(
        [
            "confirmed breakout",
            "breakout - volume confirmation required",
            "near breakout"
        ]
    ) & (
        data["overall_score"] >= 45
    )

    # --------------------------------------------------------
    # Options underlying candidates
    # --------------------------------------------------------

    options_condition = (
        volume_ratio >= 1.2
    ) & (
        data["overall_score"] >= 50
    ) & (
        ~momentum_negative
    )

    # --------------------------------------------------------
    # Create watchlists
    # --------------------------------------------------------

    watchlists = {

        "next_day":
            filter_sorted(
                next_day_condition
            ),

        "intraday":
            filter_sorted(
                intraday_condition
            ),

        "swing":
            filter_sorted(
                swing_condition
            ),

        "long_term":
            filter_sorted(
                long_term_condition
            ),

        "52w_high":
            filter_sorted(
                high_condition
            ),

        "dma_recovery":
            filter_sorted(
                dma_condition
            ),

        "momentum":
            filter_sorted(
                momentum_condition
            ),

        "breakout":
            filter_sorted(
                breakout_condition
            ),

        "options":
            filter_sorted(
                options_condition
            )
    }

    return watchlists


# ============================================================
# SETUP SUMMARY
# ============================================================

def create_setup_summary(
    ranked_data
):

    if (
        ranked_data is None or
        ranked_data.empty
    ):
        return pd.DataFrame(
            columns=[
                "setup",
                "count"
            ]
        )

    summary = (
        ranked_data[
            "setup"
        ]
        .value_counts()
        .rename_axis(
            "setup"
        )
        .reset_index(
            name="count"
        )
    )

    return summary


# ============================================================
# END
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print(
        "NSE SMART MARKET DASHBOARD"
    )
    print(
        "RANKING ENGINE V2"
    )
    print("=" * 70)
    print()

    print(
        "Ranking Engine loaded successfully."
    )

    print()
    print(
        "Scoring model:"
    )

    print(
        "Technical: 60%"
    )

    print(
        "Fundamental: 40%"
    )

    print(
        "Sector adjustment: +/- 5"
    )

    print(
        "Market-regime adjustment: contextual"
    )

    print()
    print(
        "Watchlists:"
    )

    for name in [
        "Next Day",
        "Intraday",
        "Swing",
        "Long-Term",
        "52W High",
        "200 DMA Recovery",
        "Momentum",
        "Breakout",
        "Options"
    ]:

        print(
            f"- {name}"
        )

    print()
    print("=" * 70)
