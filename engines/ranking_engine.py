# ============================================================
# NSE SMART MARKET DASHBOARD V2.1
# RANKING + WATCHLIST + TRADE PLAN ENGINE
# Created by Rakesh Nagapuri
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# GENERIC HELPERS
# ============================================================

def first_existing_column(df, columns):

    for column in columns:

        if column in df.columns:
            return column

    return None


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


def clean_text(value):

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


def clamp(
    value,
    minimum=0,
    maximum=100
):

    if pd.isna(value):
        return np.nan

    return max(
        minimum,
        min(
            maximum,
            float(value)
        )
    )


def normalize_series(series):

    numeric = pd.to_numeric(
        series,
        errors="coerce"
    )

    valid = numeric.dropna()

    if valid.empty:

        return pd.Series(
            np.nan,
            index=series.index
        )

    minimum = valid.min()
    maximum = valid.max()

    if maximum == minimum:

        return pd.Series(
            50.0,
            index=series.index
        )

    return (
        (numeric - minimum)
        /
        (maximum - minimum)
    ) * 100


def round_price(value):

    if pd.isna(value):
        return np.nan

    return round(
        float(value),
        2
    )


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_columns(df):

    df = df.copy()

    # --------------------------------------------------------
    # Symbol
    # --------------------------------------------------------

    if "symbol" not in df.columns:

        source = first_existing_column(
            df,
            [
                "SYMBOL",
                "Symbol",
                "nse_symbol",
                "NSE_SYMBOL"
            ]
        )

        if source:

            df = df.rename(
                columns={
                    source: "symbol"
                }
            )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    if "Close" not in df.columns:

        source = first_existing_column(
            df,
            [
                "price",
                "Price",
                "close"
            ]
        )

        if source:

            df = df.rename(
                columns={
                    source: "Close"
                }
            )

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if "Trend" not in df.columns:

        source = first_existing_column(
            df,
            [
                "trend"
            ]
        )

        if source:

            df = df.rename(
                columns={
                    source: "Trend"
                }
            )

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if "Momentum" not in df.columns:

        source = first_existing_column(
            df,
            [
                "momentum"
            ]
        )

        if source:

            df = df.rename(
                columns={
                    source: "Momentum"
                }
            )

    # --------------------------------------------------------
    # Technical aliases
    # --------------------------------------------------------

    aliases = {

        "RSI14": [
            "rsi14",
            "RSI"
        ],

        "Volume_Ratio": [
            "volume_ratio",
            "VolumeRatio"
        ],

        "Distance_From_200DMA_Pct": [
            "distance_from_200dma_pct"
        ],

        "Distance_From_52W_High_Pct": [
            "distance_from_52w_high_pct"
        ],

        "Distance_From_52W_Low_Pct": [
            "distance_from_52w_low_pct"
        ],

        "SMA200": [
            "sma200"
        ],

        "SMA100": [
            "sma100"
        ],

        "SMA50": [
            "sma50"
        ],

        "SMA20": [
            "sma20"
        ],

        "EMA9": [
            "ema9"
        ],

        "EMA20": [
            "ema20"
        ],

        "EMA50": [
            "ema50"
        ],

        "ATR14": [
            "atr14"
        ],

        "ATR_Pct": [
            "atr_percent",
            "ATR_Percent"
        ],

        "Support": [
            "support"
        ],

        "Resistance": [
            "resistance"
        ],

        "Breakout_Status": [
            "breakout_status"
        ],

        "52W_High": [
            "52w_high",
            "52W_High"
        ],

        "52W_Low": [
            "52w_low",
            "52W_Low"
        ],

        "Above_200DMA": [
            "above_200dma"
        ]
    }

    for target, candidates in aliases.items():

        if target not in df.columns:

            source = first_existing_column(
                df,
                candidates
            )

            if source:

                df = df.rename(
                    columns={
                        source: target
                    }
                )

    # --------------------------------------------------------
    # Fundamental aliases
    # --------------------------------------------------------

    fundamental_aliases = {

        "fundamental_score": [
            "Fundamental_Score",
            "fundamentalScore"
        ],

        "fundamental_quality": [
            "Fundamental_Quality"
        ],

        "fundamental_status": [
            "Fundamental_Status"
        ],

        "roe": [
            "ROE"
        ],

        "roce": [
            "ROCE"
        ],

        "roa": [
            "ROA"
        ],

        "revenue_cagr": [
            "Revenue_CAGR"
        ],

        "profit_cagr": [
            "Profit_CAGR"
        ],

        "eps_cagr": [
            "EPS_CAGR"
        ],

        "revenue_growth": [
            "Revenue_Growth"
        ],

        "earnings_growth": [
            "Earnings_Growth",
            "Profit_Growth"
        ],

        "eps": [
            "EPS"
        ],

        "debt_equity": [
            "Debt_Equity"
        ],

        "current_ratio": [
            "Current_Ratio"
        ],

        "quick_ratio": [
            "Quick_Ratio"
        ],

        "profit_margin": [
            "Profit_Margin"
        ],

        "operating_margin": [
            "Operating_Margin"
        ],

        "gross_margin": [
            "Gross_Margin"
        ],

        "ebitda_margin": [
            "EBITDA_Margin"
        ],

        "pe": [
            "PE"
        ],

        "forward_pe": [
            "Forward_PE"
        ],

        "peg": [
            "PEG"
        ],

        "price_to_book": [
            "Price_To_Book",
            "PB"
        ],

        "dividend_yield": [
            "Dividend_Yield"
        ]
    }

    for target, candidates in fundamental_aliases.items():

        if target not in df.columns:

            source = first_existing_column(
                df,
                candidates
            )

            if source:

                df = df.rename(
                    columns={
                        source: target
                    }
                )

    # --------------------------------------------------------
    # Safety columns
    # --------------------------------------------------------

    defaults = {

        "Trend":
            "Insufficient Data",

        "Momentum":
            "Insufficient Data",

        "Breakout_Status":
            "No Breakout",

        "Volume_Ratio":
            np.nan,

        "Distance_From_200DMA_Pct":
            np.nan,

        "Distance_From_52W_High_Pct":
            np.nan,

        "Distance_From_52W_Low_Pct":
            np.nan,

        "SMA200":
            np.nan,

        "SMA100":
            np.nan,

        "SMA50":
            np.nan,

        "SMA20":
            np.nan,

        "EMA9":
            np.nan,

        "EMA20":
            np.nan,

        "EMA50":
            np.nan,

        "ATR14":
            np.nan,

        "RSI14":
            np.nan,

        "Support":
            np.nan,

        "Resistance":
            np.nan,

        "52W_High":
            np.nan,

        "52W_Low":
            np.nan,

        "Close":
            np.nan,

        "fundamental_score":
            np.nan,

        "fundamental_status":
            "Unavailable",

        "sector_adjustment":
            0
    }

    for column, default in defaults.items():

        if column not in df.columns:

            df[column] = default

    return df


# ============================================================
# TECHNICAL SCORING
# ============================================================

def score_trend(row):

    trend = clean_text(
        row.get(
            "Trend",
            ""
        )
    ).lower()

    if trend in [
        "strong uptrend",
        "strong bullish"
    ]:
        return 20

    if trend in [
        "uptrend",
        "bullish"
    ]:
        return 15

    if trend in [
        "sideways",
        "neutral"
    ]:
        return 10

    if trend in [
        "downtrend",
        "bearish"
    ]:
        return 4

    if trend in [
        "strong downtrend",
        "strong bearish"
    ]:
        return 0

    return 5


def score_momentum(row):

    momentum = clean_text(
        row.get(
            "Momentum",
            ""
        )
    ).lower()

    if momentum == "strong positive":
        return 15

    if momentum == "positive":
        return 12

    if momentum == "neutral":
        return 8

    if momentum == "weak":
        return 4

    if momentum == "negative":
        return 4

    if momentum == "strong negative":
        return 0

    return 5


def score_rsi(row):

    rsi = safe_float(
        row.get(
            "RSI14"
        )
    )

    if pd.isna(rsi):
        return 7

    if 55 <= rsi <= 70:
        return 15

    if 50 <= rsi < 55:
        return 12

    if 70 < rsi <= 80:
        return 10

    if 40 <= rsi < 50:
        return 8

    if rsi < 40:
        return 4

    return 6


def score_volume(row):

    volume_ratio = safe_float(
        row.get(
            "Volume_Ratio"
        )
    )

    if pd.isna(volume_ratio):
        return 7

    if volume_ratio >= 2.0:
        return 15

    if volume_ratio >= 1.5:
        return 13

    if volume_ratio >= 1.2:
        return 10

    if volume_ratio >= 0.8:
        return 7

    return 4


def score_position(row):

    distance_200 = safe_float(
        row.get(
            "Distance_From_200DMA_Pct"
        )
    )

    if pd.isna(distance_200):
        return 7

    if 0 <= distance_200 <= 10:
        return 15

    if 10 < distance_200 <= 20:
        return 12

    if -3 <= distance_200 < 0:
        return 13

    if -7 <= distance_200 < -3:
        return 8

    if distance_200 > 20:
        return 9

    return 3


def score_breakout(row):

    status = clean_text(
        row.get(
            "Breakout_Status",
            ""
        )
    ).lower()

    if status == "confirmed breakout":
        return 20

    if status == (
        "breakout - volume confirmation required"
    ):
        return 15

    if status == "near breakout":
        return 12

    if status == "no breakout":
        return 6

    return 5


def calculate_technical_score(row):

    score = (

        score_trend(row)

        +

        score_momentum(row)

        +

        score_rsi(row)

        +

        score_volume(row)

        +

        score_position(row)

        +

        score_breakout(row)

    )

    return clamp(
        score
    )


# ============================================================
# FUNDAMENTAL SCORING
# ============================================================

def calculate_fundamental_score(row):

    existing = safe_float(
        row.get(
            "fundamental_score"
        )
    )

    if not pd.isna(existing):

        return clamp(
            existing
        )

    score = 0
    weight = 0

    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    roe = safe_float(
        row.get(
            "roe"
        )
    )

    if not pd.isna(roe):

        weight += 15

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
        row.get(
            "roce"
        )
    )

    if not pd.isna(roce):

        weight += 15

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
    # Revenue growth
    # --------------------------------------------------------

    revenue = safe_float(
        row.get(
            "revenue_cagr"
        )
    )

    if pd.isna(revenue):

        revenue = safe_float(
            row.get(
                "revenue_growth"
            )
        )

        if (
            not pd.isna(revenue)
            and abs(revenue) <= 2
        ):

            revenue *= 100

    if not pd.isna(revenue):

        weight += 10

        if revenue >= 20:
            score += 10

        elif revenue >= 15:
            score += 8

        elif revenue >= 10:
            score += 6

        elif revenue >= 5:
            score += 4

        elif revenue >= 0:
            score += 2

    # --------------------------------------------------------
    # Profit growth
    # --------------------------------------------------------

    profit = safe_float(
        row.get(
            "profit_cagr"
        )
    )

    if pd.isna(profit):

        profit = safe_float(
            row.get(
                "earnings_growth"
            )
        )

        if (
            not pd.isna(profit)
            and abs(profit) <= 2
        ):

            profit *= 100

    if not pd.isna(profit):

        weight += 10

        if profit >= 20:
            score += 10

        elif profit >= 15:
            score += 8

        elif profit >= 10:
            score += 6

        elif profit >= 5:
            score += 4

        elif profit >= 0:
            score += 2

    # --------------------------------------------------------
    # Debt / Equity
    # --------------------------------------------------------

    debt = safe_float(
        row.get(
            "debt_equity"
        )
    )

    if not pd.isna(debt):

        weight += 10

        if debt <= 0.25:
            score += 10

        elif debt <= 0.50:
            score += 8

        elif debt <= 1:
            score += 6

        elif debt <= 2:
            score += 3

    # --------------------------------------------------------
    # Profit Margin
    # --------------------------------------------------------

    margin = safe_float(
        row.get(
            "profit_margin"
        )
    )

    if not pd.isna(margin):

        if abs(margin) <= 2:
            margin *= 100

        weight += 10

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
        row.get(
            "pe"
        )
    )

    if not pd.isna(pe):

        weight += 10

        if 0 < pe <= 15:
            score += 10

        elif pe <= 25:
            score += 8

        elif pe <= 35:
            score += 6

        elif pe <= 50:
            score += 3

    if weight == 0:

        return np.nan

    return clamp(
        (
            score /
            weight
        ) * 100
    )


# ============================================================
# SECTOR SCORING
# ============================================================

def get_sector_strength(row):

    for column in [
        "sector_strength",
        "Sector_Strength",
        "strength",
        "Strength"
    ]:

        if column in row.index:

            value = row.get(
                column
            )

            if not pd.isna(value):

                return str(value)

    return "Unknown"


def calculate_sector_score(row):

    strength = get_sector_strength(
        row
    ).lower()

    if "leading" in strength:
        return 100

    if "strong" in strength:
        return 80

    if "neutral" in strength:
        return 60

    if "weak" in strength:
        return 40

    if "lagging" in strength:
        return 20

    return 60


def calculate_sector_adjustment(
    sector_score
):

    if pd.isna(
        sector_score
    ):
        return 0

    if sector_score >= 80:
        return 5

    if sector_score >= 65:
        return 3

    if sector_score >= 45:
        return 0

    if sector_score >= 30:
        return -3

    return -5


# ============================================================
# MARKET REGIME
# ============================================================

def get_market_regime_name(
    market_regime
):

    if market_regime is None:
        return "Unknown"

    if isinstance(
        market_regime,
        dict
    ):

        return str(
            market_regime.get(
                "regime",
                market_regime.get(
                    "market_regime",
                    "Unknown"
                )
            )
        )

    return str(
        market_regime
    )


def market_adjustment(
    setup,
    market_regime
):

    regime = (
        get_market_regime_name(
            market_regime
        )
        .lower()
    )

    setup_text = str(
        setup
    ).lower()

    if "bullish" in regime:

        if "breakout" in setup_text:
            return 5

        if "momentum" in setup_text:
            return 4

        return 2

    if "cautious" in regime:

        if "breakout" in setup_text:
            return 2

        return 0

    if "sideways" in regime:

        if "breakout" in setup_text:
            return -2

        if "recovery" in setup_text:
            return 1

        return 0

    if "weak" in regime:

        if "breakout" in setup_text:
            return -5

        if "momentum" in setup_text:
            return -3

        return -2

    if "bearish" in regime:

        if "breakout" in setup_text:
            return -8

        if "momentum" in setup_text:
            return -5

        if "long term" in setup_text:
            return -5

        return -3

    return 0


# ============================================================
# SETUP DETECTION
# ============================================================

def determine_setup(row):

    trend = clean_text(
        row.get(
            "Trend",
            ""
        )
    ).lower()

    momentum = clean_text(
        row.get(
            "Momentum",
            ""
        )
    ).lower()

    breakout = clean_text(
        row.get(
            "Breakout_Status",
            ""
        )
    ).lower()

    distance_high = safe_float(
        row.get(
            "Distance_From_52W_High_Pct"
        )
    )

    distance_dma = safe_float(
        row.get(
            "Distance_From_200DMA_Pct"
        )
    )

    # --------------------------------------------------------
    # Confirmed breakout
    # --------------------------------------------------------

    if breakout == "confirmed breakout":

        return "Strong Breakout Watch"

    # --------------------------------------------------------
    # 52W high
    # --------------------------------------------------------

    if (
        not pd.isna(distance_high)
        and
        distance_high >= -3
        and
        trend in [
            "strong uptrend",
            "uptrend",
            "strong bullish",
            "bullish"
        ]
    ):

        return "52W High Watch"

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if (
        momentum in [
            "strong positive",
            "positive"
        ]
        and
        trend in [
            "strong uptrend",
            "uptrend",
            "strong bullish",
            "bullish"
        ]
    ):

        return "Momentum Watch"

    # --------------------------------------------------------
    # 200 DMA recovery
    # --------------------------------------------------------

    if (
        not pd.isna(distance_dma)
        and
        -7 <= distance_dma <= 5
        and
        momentum in [
            "positive",
            "strong positive",
            "neutral"
        ]
    ):

        return "200 DMA Recovery Watch"

    # --------------------------------------------------------
    # Breakout confirmation
    # --------------------------------------------------------

    if (
        breakout ==
        "breakout - volume confirmation required"
    ):

        return "Breakout Confirmation Required"

    # --------------------------------------------------------
    # Pre-breakout
    # --------------------------------------------------------

    if breakout == "near breakout":

        return "Pre-Breakout Watch"

    # --------------------------------------------------------
    # Weak
    # --------------------------------------------------------

    if (
        (
            "downtrend" in trend
            or
            "bearish" in trend
        )
        and
        (
            "negative" in momentum
            or
            "weak" in momentum
        )
    ):

        return "Weak / Avoid"

    return "Neutral Watch"


# ============================================================
# OLD RISK / REWARD
# ============================================================

def calculate_risk_reward(row):

    price = safe_float(
        row.get(
            "Close"
        )
    )

    support = safe_float(
        row.get(
            "Support"
        )
    )

    resistance = safe_float(
        row.get(
            "Resistance"
        )
    )

    if (
        pd.isna(price)
        or
        price <= 0
        or
        pd.isna(support)
        or
        pd.isna(resistance)
    ):

        return np.nan

    risk = (
        price -
        support
    )

    reward = (
        resistance -
        price
    )

    if risk <= 0:

        return np.nan

    return reward / risk


# ============================================================
# TRADE PLAN ENGINE
# ============================================================

def calculate_trade_plan(row):

    price = safe_float(
        row.get(
            "Close"
        )
    )

    support = safe_float(
        row.get(
            "Support"
        )
    )

    resistance = safe_float(
        row.get(
            "Resistance"
        )
    )

    sma20 = safe_float(
        row.get(
            "SMA20"
        )
    )

    sma50 = safe_float(
        row.get(
            "SMA50"
        )
    )

    sma200 = safe_float(
        row.get(
            "SMA200"
        )
    )

    atr = safe_float(
        row.get(
            "ATR14"
        )
    )

    high_52w = safe_float(
        row.get(
            "52W_High"
        )
    )

    setup = clean_text(
        row.get(
            "setup"
        )
    )

    result = {

        "entry_low":
            np.nan,

        "entry_high":
            np.nan,

        "entry_price":
            np.nan,

        "stop_loss":
            np.nan,

        "target_1":
            np.nan,

        "target_2":
            np.nan,

        "risk_points":
            np.nan,

        "reward_1_points":
            np.nan,

        "reward_2_points":
            np.nan,

        "risk_reward_1":
            np.nan,

        "risk_reward_2":
            np.nan,

        "trade_plan_type":
            "No Trade Plan",

        "trade_plan_status":
            "Confirmation Required",

        "trade_plan_reason":
            "",

        "invalidation":
            ""
    }

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if (
        pd.isna(price)
        or
        price <= 0
    ):

        result[
            "trade_plan_reason"
        ] = (
            "Price data unavailable."
        )

        return result

    # --------------------------------------------------------
    # ATR fallback
    # --------------------------------------------------------

    if (
        pd.isna(atr)
        or
        atr <= 0
    ):

        atr = price * 0.02

    # --------------------------------------------------------
    # Support fallback
    # --------------------------------------------------------

    if (
        pd.isna(support)
        or
        support <= 0
    ):

        candidates = [

            sma20,
            sma50,
            sma200,
            price - atr

        ]

        candidates = [

            value
            for value in candidates
            if (
                not pd.isna(value)
                and
                value > 0
                and
                value < price
            )

        ]

        if candidates:

            support = max(
                candidates
            )

        else:

            support = (
                price -
                atr
            )

    # --------------------------------------------------------
    # Resistance fallback
    # --------------------------------------------------------

    if (
        pd.isna(resistance)
        or
        resistance <= price
    ):

        candidates = [

            sma20,
            sma50,
            sma200,
            high_52w,
            price + atr

        ]

        candidates = [

            value
            for value in candidates
            if (
                not pd.isna(value)
                and
                value > price
            )

        ]

        if candidates:

            resistance = min(
                candidates
            )

        else:

            resistance = (
                price +
                atr
            )

    # ========================================================
    # STRONG BREAKOUT
    # ========================================================

    if setup == "Strong Breakout Watch":

        buffer = max(
            atr * 0.15,
            resistance * 0.002
        )

        entry_low = (
            resistance +
            buffer
        )

        entry_high = (
            resistance +
            atr * 0.50
        )

        entry = entry_low

        stop = max(
            support,
            resistance - atr
        )

        target_1 = (
            entry +
            atr * 2
        )

        target_2 = (
            entry +
            atr * 3.5
        )

        result[
            "trade_plan_type"
        ] = "Breakout Trade"

        result[
            "trade_plan_status"
        ] = "Strong Setup"

        result[
            "trade_plan_reason"
        ] = (
            "Confirmed breakout above "
            "resistance. Entry requires "
            "breakout confirmation."
        )

        result[
            "invalidation"
        ] = (
            f"Below ₹{stop:.2f}"
        )

    # ========================================================
    # BREAKOUT CONFIRMATION
    # ========================================================

    elif setup == (
        "Breakout Confirmation Required"
    ):

        buffer = max(
            atr * 0.20,
            resistance * 0.002
        )

        entry_low = (
            resistance +
            buffer
        )

        entry_high = (
            resistance +
            atr * 0.60
        )

        entry = entry_low

        stop = max(
            support,
            resistance - atr
        )

        target_1 = (
            entry +
            atr * 1.75
        )

        target_2 = (
            entry +
            atr * 3
        )

        result[
            "trade_plan_type"
        ] = "Breakout Confirmation"

        result[
            "trade_plan_status"
        ] = "Confirmation Required"

        result[
            "trade_plan_reason"
        ] = (
            "Price is near resistance. "
            "Wait for price and volume "
            "confirmation above resistance."
        )

        result[
            "invalidation"
        ] = (
            f"Breakout invalid below "
            f"₹{stop:.2f}"
        )

    # ========================================================
    # PRE-BREAKOUT
    # ========================================================

    elif setup == "Pre-Breakout Watch":

        entry_low = max(
            support,
            resistance - atr * 0.75
        )

        entry_high = (
            resistance -
            atr * 0.15
        )

        if entry_low >= entry_high:

            entry_low = (
                price -
                atr * 0.25
            )

            entry_high = (
                price +
                atr * 0.10
            )

        entry = (
            entry_low +
            entry_high
        ) / 2

        stop = min(
            support - atr * 0.25,
            entry - atr
        )

        target_1 = resistance

        target_2 = (
            resistance +
            atr * 2
        )

        result[
            "trade_plan_type"
        ] = "Pre-Breakout Trade"

        result[
            "trade_plan_status"
        ] = "Watch"

        result[
            "trade_plan_reason"
        ] = (
            "Price is approaching "
            "resistance. Prefer entry near "
            "the breakout zone rather than "
            "chasing price."
        )

        result[
            "invalidation"
        ] = (
            f"Below ₹{stop:.2f}"
        )

    # ========================================================
    # 52 WEEK HIGH
    # ========================================================

    elif setup == "52W High Watch":

        if (
            not pd.isna(high_52w)
            and
            high_52w > price
        ):

            breakout_level = high_52w

        else:

            breakout_level = resistance

        buffer = max(
            atr * 0.15,
            breakout_level * 0.002
        )

        entry_low = (
            breakout_level +
            buffer
        )

        entry_high = (
            breakout_level +
            atr * 0.50
        )

        entry = entry_low

        stop = max(
            support,
            breakout_level - atr
        )

        target_1 = (
            entry +
            atr * 2
        )

        target_2 = (
            entry +
            atr * 3.5
        )

        result[
            "trade_plan_type"
        ] = "52W High Breakout"

        result[
            "trade_plan_status"
        ] = "Watch"

        result[
            "trade_plan_reason"
        ] = (
            "Stock is near its rolling "
            "52-week high. Entry requires "
            "breakout confirmation."
        )

        result[
            "invalidation"
        ] = (
            f"Below ₹{stop:.2f}"
        )

    # ========================================================
    # 200 DMA RECOVERY
    # ========================================================

    elif setup == "200 DMA Recovery Watch":

        if (
            not pd.isna(sma200)
            and
            sma200 > 0
        ):

            recovery_level = sma200

        else:

            recovery_level = price

        entry_low = max(
            support,
            recovery_level
        )

        entry_high = (
            recovery_level +
            atr * 0.50
        )

        entry = entry_low

        stop = min(
            support - atr * 0.25,
            recovery_level - atr
        )

        target_1 = max(
            resistance,
            sma50
            if not pd.isna(sma50)
            else resistance
        )

        target_2 = (
            target_1 +
            atr * 2
        )

        result[
            "trade_plan_type"
        ] = "200 DMA Recovery"

        result[
            "trade_plan_status"
        ] = "Confirmation Required"

        result[
            "trade_plan_reason"
        ] = (
            "Stock is recovering around "
            "the 200 DMA. Confirmation "
            "above the recovery level "
            "is preferred."
        )

        result[
            "invalidation"
        ] = (
            f"Below ₹{stop:.2f}"
        )

    # ========================================================
    # MOMENTUM
    # ========================================================

    elif setup == "Momentum Watch":

        entry_low = max(
            support,
            price - atr * 0.50
        )

        entry_high = (
            price +
            atr * 0.25
        )

        entry = price

        stop = max(
            support,
            price - atr * 1.25
        )

        target_1 = max(
            resistance,
            price + atr * 1.75
        )

        target_2 = max(
            target_1,
            price + atr * 3
        )

        result[
            "trade_plan_type"
        ] = "Momentum Trade"

        result[
            "trade_plan_status"
        ] = "Watch"

        result[
            "trade_plan_reason"
        ] = (
            "Positive trend and momentum. "
            "Prefer entry near current price "
            "or on a controlled pullback."
        )

        result[
            "invalidation"
        ] = (
            f"Below ₹{stop:.2f}"
        )

    # ========================================================
    # NEUTRAL
    # ========================================================

    elif setup == "Neutral Watch":

        result[
            "trade_plan_type"
        ] = "No Immediate Trade"

        result[
            "trade_plan_status"
        ] = "Confirmation Required"

        result[
            "trade_plan_reason"
        ] = (
            "Technical setup is not strong "
            "enough for an immediate trade."
        )

        result[
            "invalidation"
        ] = (
            "Wait for a clearer setup."
        )

        return result

    # ========================================================
    # WEAK / AVOID
    # ========================================================

    elif setup == "Weak / Avoid":

        result[
            "trade_plan_type"
        ] = "Avoid"

        result[
            "trade_plan_status"
        ] = "Avoid"

        result[
            "trade_plan_reason"
        ] = (
            "Trend and momentum do not "
            "provide sufficient confirmation."
        )

        result[
            "invalidation"
        ] = (
            "No long trade setup."
        )

        return result

    else:

        result[
            "trade_plan_type"
        ] = "No Immediate Trade"

        result[
            "trade_plan_status"
        ] = "Confirmation Required"

        result[
            "trade_plan_reason"
        ] = (
            "No validated trade setup."
        )

        result[
            "invalidation"
        ] = (
            "Wait for confirmation."
        )

        return result

    # ========================================================
    # SANITY CHECK
    # ========================================================

    if (
        pd.isna(entry)
        or
        pd.isna(stop)
        or
        pd.isna(target_1)
        or
        pd.isna(target_2)
    ):

        result[
            "trade_plan_type"
        ] = "No Immediate Trade"

        result[
            "trade_plan_status"
        ] = "Insufficient Data"

        result[
            "trade_plan_reason"
        ] = (
            "Insufficient technical levels "
            "to calculate a reliable trade plan."
        )

        return result

    # --------------------------------------------------------
    # Stop loss below entry
    # --------------------------------------------------------

    if stop >= entry:

        stop = (
            entry -
            max(
                atr,
                entry * 0.01
            )
        )

    # --------------------------------------------------------
    # Target 1 above entry
    # --------------------------------------------------------

    if target_1 <= entry:

        target_1 = (
            entry +
            atr * 1.5
        )

    # --------------------------------------------------------
    # Target 2 above Target 1
    # --------------------------------------------------------

    if target_2 <= target_1:

        target_2 = (
            target_1 +
            atr * 1.5
        )

    # ========================================================
    # RISK / REWARD
    # ========================================================

    risk = (
        entry -
        stop
    )

    reward_1 = (
        target_1 -
        entry
    )

    reward_2 = (
        target_2 -
        entry
    )

    if risk <= 0:

        result[
            "trade_plan_status"
        ] = "Insufficient Data"

        return result

    rr1 = (
        reward_1 /
        risk
    )

    rr2 = (
        reward_2 /
        risk
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    result[
        "entry_low"
    ] = round_price(
        entry_low
    )

    result[
        "entry_high"
    ] = round_price(
        entry_high
    )

    result[
        "entry_price"
    ] = round_price(
        entry
    )

    result[
        "stop_loss"
    ] = round_price(
        stop
    )

    result[
        "target_1"
    ] = round_price(
        target_1
    )

    result[
        "target_2"
    ] = round_price(
        target_2
    )

    result[
        "risk_points"
    ] = round_price(
        risk
    )

    result[
        "reward_1_points"
    ] = round_price(
        reward_1
    )

    result[
        "reward_2_points"
    ] = round_price(
        reward_2
    )

    result[
        "risk_reward_1"
    ] = round(
        rr1,
        2
    )

    result[
        "risk_reward_2"
    ] = round(
        rr2,
        2
    )

    return result


# ============================================================
# SETUP REASONS
# ============================================================

def create_setup_reasons(row):

    reasons = []

    trend = clean_text(
        row.get(
            "Trend",
            ""
        )
    )

    momentum = clean_text(
        row.get(
            "Momentum",
            ""
        )
    )

    breakout = clean_text(
        row.get(
            "Breakout_Status",
            ""
        )
    )

    rsi = safe_float(
        row.get(
            "RSI14"
        )
    )

    volume = safe_float(
        row.get(
            "Volume_Ratio"
        )
    )

    dma_distance = safe_float(
        row.get(
            "Distance_From_200DMA_Pct"
        )
    )

    high_distance = safe_float(
        row.get(
            "Distance_From_52W_High_Pct"
        )
    )

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if (
        "strong uptrend" in
        trend.lower()
        or
        "strong bullish" in
        trend.lower()
    ):

        reasons.append(
            "Strong price trend"
        )

    elif (
        "uptrend" in
        trend.lower()
        or
        "bullish" in
        trend.lower()
    ):

        reasons.append(
            "Price is in an uptrend"
        )

    elif (
        "downtrend" in
        trend.lower()
        or
        "bearish" in
        trend.lower()
    ):

        reasons.append(
            "Price trend is weak"
        )

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if (
        "strong positive"
        in momentum.lower()
    ):

        reasons.append(
            "Strong positive momentum"
        )

    elif momentum.lower() == "positive":

        reasons.append(
            "Positive momentum"
        )

    elif (
        "negative"
        in momentum.lower()
        or
        "weak"
        in momentum.lower()
    ):

        reasons.append(
            "Weak momentum"
        )

    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    if (
        "confirmed breakout"
        in breakout.lower()
    ):

        reasons.append(
            "Confirmed price breakout"
        )

    elif (
        "volume confirmation"
        in breakout.lower()
    ):

        reasons.append(
            "Breakout requires volume confirmation"
        )

    elif (
        "near breakout"
        in breakout.lower()
    ):

        reasons.append(
            "Price is close to resistance"
        )

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    if not pd.isna(volume):

        if volume >= 2:

            reasons.append(
                "Volume is more than 2x average"
            )

        elif volume >= 1.5:

            reasons.append(
                "Strong volume confirmation"
            )

        elif volume >= 1.2:

            reasons.append(
                "Volume is above average"
            )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if not pd.isna(rsi):

        if rsi >= 70:

            reasons.append(
                "RSI indicates overbought conditions"
            )

        elif rsi <= 30:

            reasons.append(
                "RSI indicates oversold conditions"
            )

        elif 50 <= rsi < 70:

            reasons.append(
                "RSI supports positive momentum"
            )

    # --------------------------------------------------------
    # 200 DMA
    # --------------------------------------------------------

    if not pd.isna(dma_distance):

        if dma_distance > 0:

            reasons.append(
                "Price is above 200 DMA"
            )

        else:

            reasons.append(
                "Price is below 200 DMA"
            )

        if abs(dma_distance) <= 3:

            reasons.append(
                "Price is near 200 DMA"
            )

    # --------------------------------------------------------
    # 52W high
    # --------------------------------------------------------

    if not pd.isna(high_distance):

        if high_distance >= -3:

            reasons.append(
                "Price is near 52-week high"
            )

    if not reasons:

        reasons.append(
            "No strong confirmation"
        )

    return " | ".join(
        reasons
    )


# ============================================================
# MERGE SECTOR DATA
# ============================================================

def merge_sector_data(
    data,
    sector_data
):

    if (
        sector_data is None
        or
        sector_data.empty
    ):

        return data

    data = data.copy()
    sectors = sector_data.copy()

    sector_symbol = first_existing_column(
        sectors,
        [
            "symbol",
            "SYMBOL",
            "Symbol",
            "yahoo_symbol"
        ]
    )

    if sector_symbol is None:
        return data

    sectors[
        "merge_symbol"
    ] = (
        sectors[
            sector_symbol
        ]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(
            ".NS",
            "",
            regex=False
        )
    )

    strength_column = first_existing_column(
        sectors,
        [
            "sector_strength",
            "Sector_Strength",
            "strength",
            "Strength"
        ]
    )

    score_column = first_existing_column(
        sectors,
        [
            "sector_score",
            "Sector_Score",
            "score",
            "Score"
        ]
    )

    sector_name_column = first_existing_column(
        sectors,
        [
            "sector",
            "Sector",
            "index",
            "Index"
        ]
    )

    columns_to_keep = [
        "merge_symbol"
    ]

    rename_map = {}

    if strength_column:

        columns_to_keep.append(
            strength_column
        )

        rename_map[
            strength_column
        ] = "sector_strength"

    if score_column:

        columns_to_keep.append(
            score_column
        )

        rename_map[
            score_column
        ] = "sector_score"

    if sector_name_column:

        columns_to_keep.append(
            sector_name_column
        )

        rename_map[
            sector_name_column
        ] = "sector_index"

    sectors = (
        sectors[
            columns_to_keep
        ]
        .drop_duplicates(
            subset=[
                "merge_symbol"
            ]
        )
        .rename(
            columns=rename_map
        )
    )

    data[
        "merge_symbol"
    ] = (
        data[
            "symbol"
        ]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(
            ".NS",
            "",
            regex=False
        )
    )

    data = data.merge(
        sectors,
        on="merge_symbol",
        how="left"
    )

    data = data.drop(
        columns=[
            "merge_symbol"
        ],
        errors="ignore"
    )

    return data


# ============================================================
# RANK STOCKS
# ============================================================

def rank_stocks(
    technical_data,
    fundamental_data=None,
    sector_data=None,
    market_regime=None
):

    if (
        technical_data is None
        or
        technical_data.empty
    ):

        return pd.DataFrame()

    data = normalize_columns(
        technical_data
    )

    # ========================================================
    # FUNDAMENTALS
    # ========================================================

    if (
        fundamental_data is not None
        and
        not fundamental_data.empty
    ):

        fundamentals = (
            fundamental_data.copy()
        )

        if "symbol" not in fundamentals.columns:

            source = first_existing_column(
                fundamentals,
                [
                    "SYMBOL",
                    "Symbol",
                    "nse_symbol"
                ]
            )

            if source:

                fundamentals = fundamentals.rename(
                    columns={
                        source:
                            "symbol"
                    }
                )

        if "symbol" in fundamentals.columns:

            fundamentals[
                "symbol"
            ] = (
                fundamentals[
                    "symbol"
                ]
                .astype(str)
                .str.upper()
                .str.replace(
                    ".NS",
                    "",
                    regex=False
                )
            )

            fund_columns = [

                column
                for column
                in fundamentals.columns

                if (
                    column != "symbol"
                    and
                    column not in data.columns
                )

            ]

            if fund_columns:

                data[
                    "symbol"
                ] = (
                    data[
                        "symbol"
                    ]
                    .astype(str)
                    .str.upper()
                    .str.replace(
                        ".NS",
                        "",
                        regex=False
                    )
                )

                data = data.merge(
                    fundamentals[
                        [
                            "symbol"
                        ]
                        +
                        fund_columns
                    ],
                    on="symbol",
                    how="left"
                )

    # ========================================================
    # SECTOR
    # ========================================================

    data = merge_sector_data(
        data,
        sector_data
    )

    # ========================================================
    # NUMERIC NORMALIZATION
    # ========================================================

    numeric_columns = [

        "Close",

        "RSI14",

        "Volume_Ratio",

        "Distance_From_200DMA_Pct",

        "Distance_From_52W_High_Pct",

        "Distance_From_52W_Low_Pct",

        "SMA20",

        "SMA50",

        "SMA100",

        "SMA200",

        "EMA9",

        "EMA20",

        "EMA50",

        "ATR14",

        "Support",

        "Resistance",

        "52W_High",

        "52W_Low"

    ]

    for column in numeric_columns:

        if column in data.columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce"
            )

    # ========================================================
    # TECHNICAL SCORE
    # ========================================================

    data[
        "technical_score"
    ] = data.apply(
        calculate_technical_score,
        axis=1
    )

    # ========================================================
    # FUNDAMENTAL SCORE
    # ========================================================

    data[
        "fundamental_score"
    ] = data.apply(
        calculate_fundamental_score,
        axis=1
    )

    # ========================================================
    # FUNDAMENTAL STATUS
    # ========================================================

    def fundamental_status(row):

        score = safe_float(
            row.get(
                "fundamental_score"
            )
        )

        existing = clean_text(
            row.get(
                "fundamental_status",
                ""
            )
        )

        if not pd.isna(score):

            return "Available"

        if existing.lower() not in [
            "",
            "nan",
            "none",
            "unavailable"
        ]:

            return existing

        return "Unavailable"

    data[
        "fundamental_status"
    ] = data.apply(
        fundamental_status,
        axis=1
    )

    # ========================================================
    # SECTOR SCORE
    # ========================================================

    data[
        "sector_score"
    ] = data.apply(
        calculate_sector_score,
        axis=1
    )

    data[
        "sector_adjustment"
    ] = data[
        "sector_score"
    ].apply(
        calculate_sector_adjustment
    )

    # ========================================================
    # SETUP
    # ========================================================

    data[
        "setup"
    ] = data.apply(
        determine_setup,
        axis=1
    )

    # ========================================================
    # MARKET ADJUSTMENT
    # ========================================================

    data[
        "market_adjustment"
    ] = data[
        "setup"
    ].apply(
        lambda setup:
            market_adjustment(
                setup,
                market_regime
            )
    )

    # ========================================================
    # OVERALL SCORE
    #
    # Technical 60%
    # Fundamental 40%
    #
    # Missing fundamentals are not treated as zero.
    # ========================================================

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

        sector_adj = safe_float(
            row.get(
                "sector_adjustment"
            )
        )

        market_adj = safe_float(
            row.get(
                "market_adjustment"
            )
        )

        if pd.isna(
            technical
        ):

            technical = 0

        if pd.isna(
            fundamental
        ):

            base = technical

        else:

            base = (
                technical * 0.60
                +
                fundamental * 0.40
            )

        return clamp(
            base
            +
            (
                0
                if pd.isna(
                    sector_adj
                )
                else sector_adj
            )
            +
            (
                0
                if pd.isna(
                    market_adj
                )
                else market_adj
            )
        )

    data[
        "overall_score"
    ] = data.apply(
        calculate_overall,
        axis=1
    )

    # ========================================================
    # TRADE PLAN
    #
    # This is deliberately calculated AFTER setup.
    # Therefore entry / SL / targets are setup-specific.
    # ========================================================

    trade_plan = data.apply(
        calculate_trade_plan,
        axis=1,
        result_type="expand"
    )

    data = pd.concat(
        [
            data,
            trade_plan
        ],
        axis=1
    )

    # ========================================================
    # RISK / REWARD
    # ========================================================

    data[
        "risk_reward"
    ] = data[
        "risk_reward_1"
    ]

    # ========================================================
    # SETUP REASONS
    # ========================================================

    data[
        "setup_reasons"
    ] = data.apply(
        create_setup_reasons,
        axis=1
    )

    # ========================================================
    # TRADE PLAN QUALITY
    # ========================================================

    def trade_quality(row):

        rr = safe_float(
            row.get(
                "risk_reward_1"
            )
        )

        status = clean_text(
            row.get(
                "trade_plan_status"
            )
        )

        if status == "Avoid":
            return "Avoid"

        if pd.isna(rr):
            return "Not Ready"

        if rr >= 2:

            return "Strong"

        if rr >= 1.5:

            return "Acceptable"

        return "Poor"

    data[
        "trade_plan_quality"
    ] = data.apply(
        trade_quality,
        axis=1
    )

    # ========================================================
    # TECHNICAL RANK
    # ========================================================

    data[
        "technical_rank"
    ] = (
        data[
            "technical_score"
        ]
        .rank(
            method="min",
            ascending=False
        )
        .astype("Int64")
    )

    # ========================================================
    # FINAL RANK
    # ========================================================

    data[
        "rank"
    ] = (
        data[
            "overall_score"
        ]
        .rank(
            method="min",
            ascending=False
        )
        .astype("Int64")
    )

    # ========================================================
    # SORT
    # ========================================================

    data = data.sort_values(
        by=[
            "overall_score",
            "technical_score"
        ],
        ascending=[
            False,
            False
        ],
        na_position="last"
    )

    data = data.reset_index(
        drop=True
    )

    return data


# ============================================================
# WATCHLIST FILTER HELPERS
# ============================================================

def positive_trend_mask(data):

    return data[
        "Trend"
    ].astype(str).str.lower().isin(
        [
            "strong uptrend",
            "uptrend",
            "strong bullish",
            "bullish"
        ]
    )


def positive_momentum_mask(data):

    return data[
        "Momentum"
    ].astype(str).str.lower().isin(
        [
            "strong positive",
            "positive"
        ]
    )


def above_200dma_mask(data):

    return (
        pd.to_numeric(
            data[
                "Close"
            ],
            errors="coerce"
        )
        >
        pd.to_numeric(
            data[
                "SMA200"
            ],
            errors="coerce"
        )
    )


# ============================================================
# WATCHLIST CREATION
# ============================================================

def create_watchlists(
    ranked_data,
    market_regime=None
):

    empty = {
        "next_day":
            pd.DataFrame(),

        "intraday":
            pd.DataFrame(),

        "swing":
            pd.DataFrame(),

        "long_term":
            pd.DataFrame(),

        "52w_high":
            pd.DataFrame(),

        "dma_recovery":
            pd.DataFrame(),

        "momentum":
            pd.DataFrame(),

        "breakout":
            pd.DataFrame(),

        "options":
            pd.DataFrame()
    }

    if (
        ranked_data is None
        or
        ranked_data.empty
    ):

        return empty

    data = normalize_columns(
        ranked_data
    )

    if "setup" not in data.columns:

        data[
            "setup"
        ] = data.apply(
            determine_setup,
            axis=1
        )

    if (
        "technical_score"
        not in data.columns
    ):

        data[
            "technical_score"
        ] = data.apply(
            calculate_technical_score,
            axis=1
        )

    if (
        "overall_score"
        not in data.columns
    ):

        data[
            "overall_score"
        ] = data[
            "technical_score"
        ]

    # --------------------------------------------------------
    # Ensure trade plan exists
    # --------------------------------------------------------

    required_trade_columns = [
        "entry_low",
        "entry_high",
        "entry_price",
        "stop_loss",
        "target_1",
        "target_2",
        "risk_points",
        "reward_1_points",
        "reward_2_points",
        "risk_reward_1",
        "risk_reward_2",
        "trade_plan_type",
        "trade_plan_status",
        "trade_plan_reason",
        "invalidation",
        "trade_plan_quality"
    ]

    missing_trade_columns = [
        column
        for column
        in required_trade_columns
        if column not in data.columns
    ]

    if missing_trade_columns:

        trade_plan = data.apply(
            calculate_trade_plan,
            axis=1,
            result_type="expand"
        )

        data = pd.concat(
            [
                data,
                trade_plan
            ],
            axis=1
        )

        def quality(row):

            rr = safe_float(
                row.get(
                    "risk_reward_1"
                )
            )

            if pd.isna(rr):
                return "Not Ready"

            if rr >= 2:
                return "Strong"

            if rr >= 1.5:
                return "Acceptable"

            return "Poor"

        data[
            "trade_plan_quality"
        ] = data.apply(
            quality,
            axis=1
        )

    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

    regime = (
        get_market_regime_name(
            market_regime
        )
        .lower()
    )

    # --------------------------------------------------------
    # Base masks
    # --------------------------------------------------------

    trend_positive = (
        positive_trend_mask(
            data
        )
    )

    momentum_positive = (
        positive_momentum_mask(
            data
        )
    )

    above_200 = (
        above_200dma_mask(
            data
        )
    )

    # --------------------------------------------------------
    # 52W High
    # --------------------------------------------------------

    high_distance = pd.to_numeric(
        data[
            "Distance_From_52W_High_Pct"
        ],
        errors="coerce"
    )

    near_52w_high = (
        high_distance >= -3
    )

    # --------------------------------------------------------
    # 200 DMA
    # --------------------------------------------------------

    dma_distance = pd.to_numeric(
        data[
            "Distance_From_200DMA_Pct"
        ],
        errors="coerce"
    )

    near_200dma = (
        dma_distance.between(
            -7,
            5
        )
    )

    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    breakout_status = (
        data[
            "Breakout_Status"
        ]
        .astype(str)
        .str.lower()
    )

    confirmed_breakout = (
        breakout_status ==
        "confirmed breakout"
    )

    possible_breakout = (
        breakout_status.isin(
            [
                "near breakout",
                "breakout - volume confirmation required"
            ]
        )
    )

    # ========================================================
    # NEXT DAY
    # ========================================================

    if (
        "bearish" in regime
        or
        "weak" in regime
    ):

        next_day_mask = (

            confirmed_breakout

            |

            (
                trend_positive
                &
                momentum_positive
                &
                above_200
                &
                (
                    pd.to_numeric(
                        data[
                            "Volume_Ratio"
                        ],
                        errors="coerce"
                    )
                    >= 1.2
                )
            )
        )

    else:

        next_day_mask = (

            confirmed_breakout

            |

            (
                trend_positive
                &
                momentum_positive
            )

            |

            possible_breakout
        )

    next_day = data[
        next_day_mask
    ].copy()

    # ========================================================
    # INTRADAY CANDIDATES
    #
    # Important:
    # EOD data cannot produce true live VWAP.
    # Therefore this remains a candidate list.
    # ========================================================

    intraday_mask = (

        (
            confirmed_breakout
            |
            possible_breakout
        )

        &

        (
            pd.to_numeric(
                data[
                    "Volume_Ratio"
                ],
                errors="coerce"
            )
            >= 1.2
        )
    )

    intraday = data[
        intraday_mask
    ].copy()

    # ========================================================
    # SWING
    # ========================================================

    swing_mask = (

        (
            trend_positive
            &
            momentum_positive
        )

        |

        confirmed_breakout

        |

        near_200dma
    )

    swing = data[
        swing_mask
    ].copy()

    # ========================================================
    # LONG TERM
    # ========================================================

    fundamental_available = (
        pd.to_numeric(
            data[
                "fundamental_score"
            ],
            errors="coerce"
        )
        .notna()
    )

    strong_fundamentals = (
        pd.to_numeric(
            data[
                "fundamental_score"
            ],
            errors="coerce"
        )
        >= 60
    )

    long_term_mask = (

        above_200

        &

        trend_positive

        &

        (
            strong_fundamentals
            |
            ~fundamental_available
        )

        &

        (
            pd.to_numeric(
                data[
                    "overall_score"
                ],
                errors="coerce"
            )
            >= 55
        )
    )

    long_term = data[
        long_term_mask
    ].copy()

    # ========================================================
    # 52W HIGH
    # ========================================================

    high_mask = (

        near_52w_high

        &

        (
            trend_positive
            |
            confirmed_breakout
        )
    )

    high_watch = data[
        high_mask
    ].copy()

    # ========================================================
    # 200 DMA RECOVERY
    # ========================================================

    dma_recovery_mask = (

        near_200dma

        &

        (
            momentum_positive

            |

            (
                data[
                    "Momentum"
                ]
                .astype(str)
                .str.lower()
                == "neutral"
            )
        )
    )

    dma_recovery = data[
        dma_recovery_mask
    ].copy()

    # ========================================================
    # MOMENTUM
    # ========================================================

    momentum_mask = (

        trend_positive
        &
        momentum_positive
    )

    momentum_watch = data[
        momentum_mask
    ].copy()

    # ========================================================
    # BREAKOUT
    # ========================================================

    breakout_mask = (
        confirmed_breakout
        |
        possible_breakout
    )

    breakout_watch = data[
        breakout_mask
    ].copy()

    # ========================================================
    # OPTIONS
    #
    # Underlying-stock candidates only.
    # No fake option-chain signals.
    # ========================================================

    options_mask = (

        (
            confirmed_breakout
            |
            possible_breakout
            |
            momentum_positive
        )

        &

        (
            pd.to_numeric(
                data[
                    "overall_score"
                ],
                errors="coerce"
            )
            >= 50
        )
    )

    options_watch = data[
        options_mask
    ].copy()

    # ========================================================
    # WATCHLIST DICTIONARY
    # ========================================================

    watchlists = {

        "next_day":
            next_day,

        "intraday":
            intraday,

        "swing":
            swing,

        "long_term":
            long_term,

        "52w_high":
            high_watch,

        "dma_recovery":
            dma_recovery,

        "momentum":
            momentum_watch,

        "breakout":
            breakout_watch,

        "options":
            options_watch
    }

    # ========================================================
    # SORT + DEDUPLICATE
    # ========================================================

    for name, watchlist in (
        watchlists.items()
    ):

        if watchlist.empty:
            continue

        sort_columns = []

        if "overall_score" in watchlist.columns:

            sort_columns.append(
                "overall_score"
            )

        if "technical_score" in watchlist.columns:

            sort_columns.append(
                "technical_score"
            )

        if sort_columns:

            watchlist = watchlist.sort_values(
                by=sort_columns,
                ascending=[
                    False
                    for _ in sort_columns
                ],
                na_position="last"
            )

        if "symbol" in watchlist.columns:

            watchlist = (
                watchlist
                .drop_duplicates(
                    subset=[
                        "symbol"
                    ],
                    keep="first"
                )
                .reset_index(
                    drop=True
                )
            )

        watchlists[
            name
        ] = watchlist

    return watchlists


# ============================================================
# SETUP SUMMARY
# ============================================================

def create_setup_summary(
    ranked_data
):

    if (
        ranked_data is None
        or
        ranked_data.empty
    ):

        return pd.DataFrame()

    if "setup" not in ranked_data.columns:

        return pd.DataFrame()

    summary = (
        ranked_data[
            "setup"
        ]
        .value_counts()
        .rename_axis(
            "setup"
        )
        .reset_index(
            name="stocks"
        )
    )

    total = summary[
        "stocks"
    ].sum()

    if total > 0:

        summary[
            "percentage"
        ] = (
            summary[
                "stocks"
            ]
            /
            total
            *
            100
        )

    return summary


# ============================================================
# EXPORT CLEANUP
# ============================================================

def prepare_export_data(
    data
):

    if (
        data is None
        or
        data.empty
    ):

        return data

    result = data.copy()

    for column in result.columns:

        if (
            pd.api.types
            .is_numeric_dtype(
                result[column]
            )
        ):

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce"
            )

    return result


# ============================================================
# STANDALONE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "NSE SMART MARKET DASHBOARD V2.1"
    )
    print(
        "RANKING + WATCHLIST + TRADE PLAN ENGINE"
    )
    print(
        "Created by Rakesh Nagapuri"
    )
    print("=" * 70)
    print()

    print(
        "Ranking engine loaded successfully."
    )

    print()
    print(
        "Technical weighting:"
    )

    print(
        "  Trend       : 20"
    )

    print(
        "  Momentum    : 15"
    )

    print(
        "  RSI         : 15"
    )

    print(
        "  Volume      : 15"
    )

    print(
        "  Position    : 15"
    )

    print(
        "  Breakout    : 20"
    )

    print()
    print(
        "Fundamental weighting:"
    )

    print(
        "  ROE         : 15"
    )

    print(
        "  ROCE        : 15"
    )

    print(
        "  Revenue     : 10"
    )

    print(
        "  Profit      : 10"
    )

    print(
        "  Debt/Equity : 10"
    )

    print(
        "  Margin      : 10"
    )

    print(
        "  PE          : 10"
    )

    print()
    print(
        "Trade Plan:"
    )

    print(
        "  Entry Zone"
    )

    print(
        "  Stop Loss"
    )

    print(
        "  Target 1"
    )

    print(
        "  Target 2"
    )

    print(
        "  Risk / Reward"
    )

    print(
        "  Invalidation"
    )

    print()
