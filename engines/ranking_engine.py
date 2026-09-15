"""
===========================================================
NSE SMART MARKET DASHBOARD
RANKING ENGINE V3
===========================================================

Combines:

    Technical Analysis
    Fundamental Analysis
    Sector Strength
    Market Regime

into:

    Technical Score
    Fundamental Score
    Sector Score
    Overall Score
    Setup Classification
    Trade Plan
    Watchlists

Trade-plan philosophy
---------------------
This engine does NOT create an arbitrary stop-loss such as
"10% below entry".

Every actionable trade plan is derived from:

    price
    SMA / DMA
    support
    resistance
    ATR
    52-week high
    breakout structure

The engine is long-only for the portfolio builder.

Possible setup labels
---------------------
    Strong Breakout Watch
    Breakout Confirmation Required
    Pre-Breakout Watch
    52W High Watch
    200 DMA Recovery Watch
    Momentum Watch
    Neutral Watch
    Weak / Avoid

Watchlists
----------
    next_day
    intraday
    swing
    long_term
    52w_high
    dma_recovery
    momentum
    breakout
    options

Important
---------
This module is intentionally defensive because upstream
data can come from pandas, yfinance or cached CSV files
with slightly different column names.
===========================================================
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# =========================================================
# CONSTANTS
# =========================================================

TECHNICAL_WEIGHT = 0.60
FUNDAMENTAL_WEIGHT = 0.40

TECHNICAL_WEIGHTS = {
    "trend": 0.20,
    "momentum": 0.15,
    "rsi": 0.15,
    "volume": 0.15,
    "position": 0.15,
    "breakout": 0.20,
}

FUNDAMENTAL_WEIGHTS = {
    "roe": 0.15,
    "roce": 0.15,
    "revenue": 0.10,
    "profit": 0.10,
    "debt": 0.10,
    "margin": 0.10,
    "pe": 0.10,
    "pb": 0.05,
    "growth": 0.05,
}

MIN_ACTIONABLE_SCORE = 45.0


# =========================================================
# GENERAL HELPERS
# =========================================================

def is_missing(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        text = value.strip().lower()

        return text in {
            "",
            "nan",
            "none",
            "null",
            "na",
            "n/a",
            "-",
        }

    try:
        return bool(pd.isna(value))
    except (
        TypeError,
        ValueError,
    ):
        return False


def to_float(
    value: Any,
    default: float | None = None,
) -> float | None:

    if is_missing(value):
        return default

    try:
        number = float(value)

        if not math.isfinite(number):
            return default

        return number

    except (
        TypeError,
        ValueError,
    ):
        return default


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def first_value(
    row: Any,
    candidates: list[str],
    default: Any = None,
) -> Any:

    if row is None:
        return default

    for column in candidates:

        try:
            value = row.get(
                column,
                None,
            )

        except AttributeError:

            try:
                value = row[column]

            except (
                KeyError,
                TypeError,
            ):
                value = None

        if not is_missing(value):
            return value

    return default


def first_float(
    row: Any,
    candidates: list[str],
    default: float | None = None,
) -> float | None:

    return to_float(
        first_value(
            row,
            candidates,
            default,
        ),
        default,
    )


def text_value(
    row: Any,
    candidates: list[str],
    default: str = "",
) -> str:

    value = first_value(
        row,
        candidates,
        default,
    )

    if is_missing(value):
        return default

    return str(value).strip()


def normalise_symbol(
    value: Any,
) -> str:

    if is_missing(value):
        return ""

    return (
        str(value)
        .strip()
        .upper()
        .replace(".NS", "")
    )


def score_boolean(
    condition: bool,
    positive: float = 100.0,
    negative: float = 0.0,
) -> float:

    return positive if condition else negative


# =========================================================
# DATAFRAME HELPERS
# =========================================================

def ensure_dataframe(
    data: Any,
) -> pd.DataFrame:

    if data is None:
        return pd.DataFrame()

    if isinstance(
        data,
        pd.DataFrame,
    ):
        return data.copy()

    if isinstance(
        data,
        list,
    ):
        return pd.DataFrame(data)

    if isinstance(
        data,
        dict,
    ):
        return pd.DataFrame(data)

    return pd.DataFrame()


def find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    if df is None or df.empty:
        return None

    lookup = {
        str(column).strip().lower():
        column
        for column in df.columns
    }

    for candidate in candidates:

        key = (
            str(candidate)
            .strip()
            .lower()
        )

        if key in lookup:
            return lookup[key]

    return None


# =========================================================
# TECHNICAL SCORING
# =========================================================

def calculate_trend_score(
    row: Any,
) -> float:

    trend = text_value(
        row,
        [
            "Trend",
            "trend",
        ],
    ).lower()

    score = 50.0

    if any(
        word in trend
        for word in [
            "strong bullish",
            "strong positive",
            "bullish",
            "strong up",
        ]
    ):
        score = 100.0

    elif any(
        word in trend
        for word in [
            "positive",
            "uptrend",
            "up trend",
        ]
    ):
        score = 85.0

    elif any(
        word in trend
        for word in [
            "neutral",
            "sideways",
        ]
    ):
        score = 50.0

    elif any(
        word in trend
        for word in [
            "weak",
            "negative",
            "downtrend",
            "down trend",
        ]
    ):
        score = 20.0

    elif any(
        word in trend
        for word in [
            "bearish",
            "strong negative",
            "strong down",
        ]
    ):
        score = 0.0

    else:

        price = first_float(
            row,
            [
                "Close",
                "close",
                "Price",
                "price",
            ],
        )

        sma20 = first_float(
            row,
            [
                "SMA_20",
                "SMA20",
                "sma20",
            ],
        )

        sma50 = first_float(
            row,
            [
                "SMA_50",
                "SMA50",
                "sma50",
            ],
        )

        sma200 = first_float(
            row,
            [
                "SMA_200",
                "SMA200",
                "sma200",
                "200_DMA",
            ],
        )

        if (
            price is not None
            and sma20 is not None
            and sma50 is not None
            and sma200 is not None
        ):

            if (
                price > sma20
                > sma50
                > sma200
            ):
                score = 100.0

            elif (
                price > sma50
                and price > sma200
            ):
                score = 85.0

            elif price > sma200:
                score = 65.0

            elif price > sma50:
                score = 45.0

            else:
                score = 20.0

    return score


def calculate_momentum_score(
    row: Any,
) -> float:

    momentum = text_value(
        row,
        [
            "Momentum",
            "momentum",
        ],
    ).lower()

    score = 50.0

    if any(
        word in momentum
        for word in [
            "strong positive",
            "strong",
        ]
    ):
        score = 100.0

    elif "positive" in momentum:
        score = 85.0

    elif any(
        word in momentum
        for word in [
            "neutral",
            "sideways",
        ]
    ):
        score = 50.0

    elif any(
        word in momentum
        for word in [
            "negative",
            "weak",
        ]
    ):
        score = 20.0

    elif any(
        word in momentum
        for word in [
            "strong negative",
            "bearish",
        ]
    ):
        score = 0.0

    else:

        price = first_float(
            row,
            [
                "Close",
                "close",
                "Price",
                "price",
            ],
        )

        sma20 = first_float(
            row,
            [
                "SMA_20",
                "SMA20",
                "sma20",
            ],
        )

        sma50 = first_float(
            row,
            [
                "SMA_50",
                "SMA50",
                "sma50",
            ],
        )

        if (
            price is not None
            and sma20 is not None
            and sma50 is not None
        ):

            if price > sma20 > sma50:
                score = 90.0

            elif price > sma20:
                score = 70.0

            elif price > sma50:
                score = 50.0

            else:
                score = 20.0

    return score


def calculate_rsi_score(
    row: Any,
) -> float:

    rsi = first_float(
        row,
        [
            "RSI_14",
            "RSI14",
            "RSI",
            "rsi",
        ],
    )

    if rsi is None:
        return 50.0

    if 50 <= rsi <= 65:
        return 100.0

    if 45 <= rsi < 50:
        return 70.0

    if 65 < rsi <= 70:
        return 80.0

    if 40 <= rsi < 45:
        return 50.0

    if 70 < rsi <= 80:
        return 45.0

    if rsi > 80:
        return 20.0

    return 25.0


def calculate_volume_score(
    row: Any,
) -> float:

    ratio = first_float(
        row,
        [
            "Volume_Ratio",
            "volume_ratio",
            "VolumeRatio",
        ],
    )

    if ratio is None:
        return 50.0

    if ratio >= 2.0:
        return 100.0

    if ratio >= 1.5:
        return 90.0

    if ratio >= 1.2:
        return 80.0

    if ratio >= 1.0:
        return 65.0

    if ratio >= 0.8:
        return 45.0

    return 25.0


def calculate_position_score(
    row: Any,
) -> float:

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    sma200 = first_float(
        row,
        [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],
    )

    if (
        price is None
        or sma200 is None
        or sma200 <= 0
    ):
        return 50.0

    distance = (
        (
            price -
            sma200
        )
        /
        sma200
    ) * 100.0

    if distance >= 15:
        return 100.0

    if distance >= 5:
        return 90.0

    if distance >= 0:
        return 80.0

    if distance >= -3:
        return 70.0

    if distance >= -7:
        return 50.0

    if distance >= -12:
        return 30.0

    return 10.0


def calculate_breakout_score(
    row: Any,
) -> float:

    breakout = text_value(
        row,
        [
            "Breakout",
            "Breakout_Status",
            "breakout",
        ],
    ).lower()

    if any(
        phrase in breakout
        for phrase in [
            "confirmed",
            "strong breakout",
        ]
    ):
        return 100.0

    if any(
        phrase in breakout
        for phrase in [
            "possible",
            "potential",
            "pre-breakout",
        ]
    ):
        return 75.0

    if "near" in breakout:
        return 60.0

    if any(
        phrase in breakout
        for phrase in [
            "failed",
            "negative",
        ]
    ):
        return 20.0

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    resistance = first_float(
        row,
        [
            "Resistance",
            "resistance",
        ],
    )

    volume_ratio = first_float(
        row,
        [
            "Volume_Ratio",
            "volume_ratio",
        ],
    )

    if (
        price is not None
        and resistance is not None
        and resistance > 0
    ):

        distance = (
            (
                price -
                resistance
            )
            /
            resistance
        ) * 100.0

        if distance >= 0:

            return (
                100.0
                if (
                    volume_ratio is not None
                    and volume_ratio >= 1.2
                )
                else 80.0
            )

        if distance >= -2:
            return 70.0

        if distance >= -5:
            return 50.0

    return 35.0


# =========================================================
# TECHNICAL SCORE
# =========================================================

def calculate_technical_score(
    row: Any,
) -> float:

    components = {
        "trend":
            calculate_trend_score(row),

        "momentum":
            calculate_momentum_score(row),

        "rsi":
            calculate_rsi_score(row),

        "volume":
            calculate_volume_score(row),

        "position":
            calculate_position_score(row),

        "breakout":
            calculate_breakout_score(row),
    }

    score = sum(
        components[key] *
        TECHNICAL_WEIGHTS[key]
        for key in components
    )

    return round(
        clamp(score),
        2,
    )


# =========================================================
# FUNDAMENTAL SCORING
# =========================================================

def score_roe(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value >= 25:
        return 100.0

    if value >= 20:
        return 90.0

    if value >= 15:
        return 75.0

    if value >= 10:
        return 60.0

    if value >= 5:
        return 40.0

    return 20.0


def score_roce(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value >= 25:
        return 100.0

    if value >= 20:
        return 90.0

    if value >= 15:
        return 75.0

    if value >= 10:
        return 60.0

    if value >= 5:
        return 40.0

    return 20.0


def score_growth(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value >= 25:
        return 100.0

    if value >= 15:
        return 85.0

    if value >= 10:
        return 75.0

    if value >= 5:
        return 60.0

    if value >= 0:
        return 50.0

    return 25.0


def score_debt(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value < 0.25:
        return 100.0

    if value < 0.50:
        return 90.0

    if value < 1.00:
        return 75.0

    if value < 1.50:
        return 55.0

    if value < 2.00:
        return 35.0

    return 15.0


def score_margin(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value >= 25:
        return 100.0

    if value >= 20:
        return 90.0

    if value >= 15:
        return 80.0

    if value >= 10:
        return 65.0

    if value >= 5:
        return 50.0

    return 30.0


def score_pe(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value <= 0:
        return 35.0

    if value <= 15:
        return 100.0

    if value <= 20:
        return 90.0

    if value <= 30:
        return 75.0

    if value <= 40:
        return 55.0

    if value <= 60:
        return 35.0

    return 20.0


def score_pb(
    value: float | None,
) -> float:

    if value is None:
        return 50.0

    if value <= 0:
        return 35.0

    if value <= 2:
        return 100.0

    if value <= 3:
        return 85.0

    if value <= 5:
        return 65.0

    if value <= 8:
        return 45.0

    return 25.0


def calculate_fundamental_score(
    row: Any,
) -> float:

    roe = first_float(
        row,
        [
            "ROE",
            "roe",
            "return_on_equity",
        ],
    )

    roce = first_float(
        row,
        [
            "ROCE",
            "roce",
            "return_on_capital_employed",
        ],
    )

    revenue_growth = first_float(
        row,
        [
            "Revenue_Growth",
            "revenue_growth",
            "Revenue_Growth_Pct",
            "revenue_cagr",
            "Revenue_CAGR",
        ],
    )

    profit_growth = first_float(
        row,
        [
            "Profit_Growth",
            "profit_growth",
            "Profit_Growth_Pct",
            "profit_cagr",
            "Profit_CAGR",
        ],
    )

    debt_equity = first_float(
        row,
        [
            "Debt_to_Equity",
            "Debt_Equity",
            "debt_to_equity",
            "debt_equity",
        ],
    )

    margin = first_float(
        row,
        [
            "Operating_Margin",
            "Operating_Margin_Pct",
            "operating_margin",
            "Profit_Margin",
            "Net_Margin",
            "net_margin",
        ],
    )

    pe = first_float(
        row,
        [
            "PE",
            "PE_Ratio",
            "pe",
            "trailingPE",
            "Forward_PE",
        ],
    )

    pb = first_float(
        row,
        [
            "PB",
            "PB_Ratio",
            "pb",
            "priceToBook",
        ],
    )

    growth_values = [
        value
        for value in [
            revenue_growth,
            profit_growth,
        ]
        if value is not None
    ]

    growth = (
        sum(growth_values) /
        len(growth_values)
        if growth_values
        else None
    )

    components = {
        "roe":
            score_roe(roe),

        "roce":
            score_roce(roce),

        "revenue":
            score_growth(
                revenue_growth
            ),

        "profit":
            score_growth(
                profit_growth
            ),

        "debt":
            score_debt(
                debt_equity
            ),

        "margin":
            score_margin(
                margin
            ),

        "pe":
            score_pe(pe),

        "pb":
            score_pb(pb),

        "growth":
            score_growth(
                growth
            ),
    }

    score = sum(
        components[key] *
        FUNDAMENTAL_WEIGHTS[key]
        for key in components
    )

    return round(
        clamp(score),
        2,
    )


# =========================================================
# SECTOR SCORE
# =========================================================

def get_sector_score(
    row: Any,
    sector_data: Any = None,
) -> float:

    direct = first_float(
        row,
        [
            "Sector_Score",
            "sector_score",
        ],
    )

    if direct is not None:
        return clamp(direct)

    sector_name = text_value(
        row,
        [
            "Primary_Sector",
            "primary_sector",
            "Sector",
            "sector",
        ],
        "Unknown",
    ).strip().lower()

    if (
        sector_data is None
        or not isinstance(
            sector_data,
            pd.DataFrame,
        )
        or sector_data.empty
    ):
        return 50.0

    sector_df = sector_data.copy()

    sector_col = find_column(
        sector_df,
        [
            "Primary_Sector",
            "primary_sector",
            "Sector",
            "sector",
            "Index",
            "index",
            "Sector_Index",
        ],
    )

    score_col = find_column(
        sector_df,
        [
            "Sector_Score",
            "sector_score",
            "Score",
            "score",
            "Overall_Score",
        ],
    )

    if (
        sector_col is None
        or score_col is None
    ):
        return 50.0

    for _, sector_row in sector_df.iterrows():

        current_sector = str(
            sector_row.get(
                sector_col,
                "",
            )
        ).strip().lower()

        if (
            current_sector == sector_name
            or (
                sector_name
                and sector_name
                in current_sector
            )
            or (
                current_sector
                and current_sector
                in sector_name
            )
        ):

            value = to_float(
                sector_row.get(
                    score_col
                )
            )

            if value is not None:
                return clamp(value)

    return 50.0


# =========================================================
# MARKET ADJUSTMENT
# =========================================================

def get_market_adjustment(
    market_regime: Any,
) -> float:

    if isinstance(
        market_regime,
        pd.DataFrame,
    ):

        if market_regime.empty:
            return 0.0

        market_regime = (
            market_regime
            .iloc[-1]
            .to_dict()
        )

    if not isinstance(
        market_regime,
        dict,
    ):
        return 0.0

    regime = str(
        market_regime.get(
            "market_regime",
            market_regime.get(
                "Regime",
                "",
            ),
        )
    ).lower()

    if "strong" in regime and (
        "bull" in regime
        or "positive" in regime
    ):
        return 8.0

    if "bull" in regime:
        return 5.0

    if "positive" in regime:
        return 4.0

    if "neutral" in regime:
        return 0.0

    if "cautious" in regime:
        return -3.0

    if "weak" in regime:
        return -6.0

    if "bear" in regime:
        return -10.0

    return 0.0


# =========================================================
# SETUP CLASSIFICATION
# =========================================================

def classify_setup(
    row: Any,
) -> str:

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    sma200 = first_float(
        row,
        [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],
    )

    high52 = first_float(
        row,
        [
            "52W_High",
            "High_52W",
            "high_52w",
        ],
    )

    resistance = first_float(
        row,
        [
            "Resistance",
            "resistance",
        ],
    )

    volume_ratio = first_float(
        row,
        [
            "Volume_Ratio",
            "volume_ratio",
        ],
    )

    trend_score = calculate_trend_score(row)
    momentum_score = calculate_momentum_score(row)
    breakout_score = calculate_breakout_score(row)

    overall = first_float(
        row,
        [
            "Overall_Score",
            "overall_score",
            "Score",
            "score",
        ],
        0.0,
    )

    breakout_text = text_value(
        row,
        [
            "Breakout",
            "Breakout_Status",
            "breakout",
        ],
    ).lower()

    distance_high = None

    if (
        price is not None
        and high52 is not None
        and high52 > 0
    ):

        distance_high = (
            (
                high52 -
                price
            )
            /
            high52
        ) * 100.0

    distance_dma = None

    if (
        price is not None
        and sma200 is not None
        and sma200 > 0
    ):

        distance_dma = (
            (
                price -
                sma200
            )
            /
            sma200
        ) * 100.0

    # Strong breakout
    if (
        (
            "confirmed" in breakout_text
            or "strong breakout"
            in breakout_text
        )
        and (
            volume_ratio is None
            or volume_ratio >= 1.2
        )
        and overall >= 60
    ):
        return "Strong Breakout Watch"

    # Breakout confirmation
    if (
        breakout_score >= 75
        and (
            volume_ratio is None
            or volume_ratio < 1.2
        )
    ):
        return "Breakout Confirmation Required"

    # 52-week high
    if (
        distance_high is not None
        and distance_high <= 3
        and trend_score >= 70
    ):
        return "52W High Watch"

    # 200 DMA recovery
    if (
        distance_dma is not None
        and -3 <= distance_dma <= 5
        and momentum_score >= 50
    ):
        return "200 DMA Recovery Watch"

    # Pre-breakout
    if (
        resistance is not None
        and price is not None
        and resistance > 0
        and 0 < (
            (
                resistance -
                price
            )
            /
            resistance
        ) * 100 <= 5
        and trend_score >= 65
    ):
        return "Pre-Breakout Watch"

    # Momentum
    if (
        trend_score >= 75
        and momentum_score >= 75
        and overall >= 50
    ):
        return "Momentum Watch"

    # Weak
    if (
        trend_score <= 30
        and momentum_score <= 30
    ):
        return "Weak / Avoid"

    return "Neutral Watch"


# =========================================================
# TRADE PLAN
# =========================================================

def calculate_trade_plan(
    row: Any,
) -> dict:

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    atr = first_float(
        row,
        [
            "ATR_14",
            "ATR14",
            "ATR",
            "atr",
        ],
    )

    support = first_float(
        row,
        [
            "Support",
            "support",
        ],
    )

    resistance = first_float(
        row,
        [
            "Resistance",
            "resistance",
        ],
    )

    sma200 = first_float(
        row,
        [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],
    )

    high52 = first_float(
        row,
        [
            "52W_High",
            "High_52W",
            "high_52w",
        ],
    )

    setup = classify_setup(row)

    # Only actionable setups receive a trade plan.
    actionable_setups = {
        "Strong Breakout Watch",
        "Breakout Confirmation Required",
        "Pre-Breakout Watch",
        "52W High Watch",
        "200 DMA Recovery Watch",
        "Momentum Watch",
    }

    if setup not in actionable_setups:

        return {
            "entry_low": None,
            "entry_high": None,
            "entry_price": None,
            "stop_loss": None,
            "target_1": None,
            "target_2": None,
            "risk_points": None,
            "reward_1_points": None,
            "reward_2_points": None,
            "risk_reward_1": None,
            "risk_reward_2": None,
            "risk_reward": None,
            "trade_plan_type": setup,
            "trade_plan_status":
                "No Actionable Plan",
            "trade_plan_reason":
                "Setup does not currently meet the actionable criteria.",
            "trade_plan_invalidation":
                "Wait for stronger technical confirmation.",
            "trade_plan_quality": "N/A",
        }

    if (
        price is None
        or price <= 0
    ):

        return {
            "entry_low": None,
            "entry_high": None,
            "entry_price": None,
            "stop_loss": None,
            "target_1": None,
            "target_2": None,
            "risk_points": None,
            "reward_1_points": None,
            "reward_2_points": None,
            "risk_reward_1": None,
            "risk_reward_2": None,
            "risk_reward": None,
            "trade_plan_type": setup,
            "trade_plan_status": "Insufficient Data",
            "trade_plan_reason":
                "Current price is unavailable.",
            "trade_plan_invalidation":
                "Wait for valid price data.",
            "trade_plan_quality": "N/A",
        }

    if atr is None or atr <= 0:

        if support is not None:

            atr = max(
                price * 0.01,
                (
                    price -
                    support
                ) * 0.50,
            )

        else:

            atr = price * 0.02

    # -----------------------------------------------------
    # Entry zone
    # -----------------------------------------------------

    if setup == "Strong Breakout Watch":

        entry_low = price

        entry_high = (
            price +
            min(
                atr * 0.50,
                price * 0.015,
            )
        )

    elif setup == "Breakout Confirmation Required":

        if resistance is not None:

            entry_low = resistance

            entry_high = (
                resistance +
                min(
                    atr * 0.50,
                    price * 0.02,
                )
            )

        else:

            entry_low = price
            entry_high = price + atr * 0.50

    elif setup == "Pre-Breakout Watch":

        if resistance is not None:

            entry_low = price

            entry_high = min(
                resistance,
                price + atr * 0.50,
            )

        else:

            entry_low = price
            entry_high = price + atr * 0.50

    elif setup == "52W High Watch":

        entry_low = price

        entry_high = (
            price +
            min(
                atr * 0.50,
                price * 0.015,
            )
        )

    elif setup == "200 DMA Recovery Watch":

        entry_low = price

        if sma200 is not None:

            entry_high = max(
                price,
                min(
                    sma200 * 1.01,
                    price + atr * 0.50,
                ),
            )

        else:

            entry_high = price + atr * 0.50

    else:
        # Momentum
        entry_low = price

        entry_high = (
            price +
            min(
                atr * 0.50,
                price * 0.015,
            )
        )

    entry_price = (
        entry_low +
        entry_high
    ) / 2.0

    # -----------------------------------------------------
    # Stop loss
    # -----------------------------------------------------

    structural_supports = [
        value
        for value in [
            support,
            sma200,
        ]
        if (
            value is not None
            and value < entry_price
        )
    ]

    if structural_supports:

        structural_stop = max(
            structural_supports
        )

        atr_stop = (
            entry_price -
            (atr * 1.25)
        )

        stop_loss = min(
            structural_stop,
            atr_stop,
        )

    else:

        stop_loss = (
            entry_price -
            (atr * 1.25)
        )

    # Never allow a non-positive stop.
    if stop_loss <= 0:

        stop_loss = (
            entry_price -
            (
                entry_price *
                0.05
            )
        )

    if stop_loss <= 0:

        return {
            "entry_low": None,
            "entry_high": None,
            "entry_price": None,
            "stop_loss": None,
            "target_1": None,
            "target_2": None,
            "risk_points": None,
            "reward_1_points": None,
            "reward_2_points": None,
            "risk_reward_1": None,
            "risk_reward_2": None,
            "risk_reward": None,
            "trade_plan_type": setup,
            "trade_plan_status":
                "Insufficient Data",
            "trade_plan_reason":
                "Unable to construct a valid structural stop.",
            "trade_plan_invalidation":
                "Wait for better technical structure.",
            "trade_plan_quality": "N/A",
        }

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    risk_points = (
        entry_price -
        stop_loss
    )

    # -----------------------------------------------------
    # Targets
    # -----------------------------------------------------

    target_candidates = []

    if resistance is not None:
        target_candidates.append(
            resistance
        )

    if high52 is not None:
        target_candidates.append(
            high52
        )

    # Target 1 should preferably be the next
    # meaningful resistance above entry.
    valid_targets = sorted(
        {
            round(
                target,
                6,
            )
            for target
            in target_candidates
            if target >
            entry_price
        }
    )

    target1 = None

    for target in valid_targets:

        if target > entry_price:

            target1 = target
            break

    # If structural resistance is not available,
    # ATR-based target.
    if target1 is None:

        target1 = (
            entry_price +
            (
                risk_points *
                1.5
            )
        )

    # Target 2.
    higher_targets = [
        target
        for target in valid_targets
        if target >
        target1
    ]

    if higher_targets:

        target2 = higher_targets[0]

    else:

        target2 = (
            entry_price +
            (
                risk_points *
                2.5
            )
        )

    reward1 = max(
        0.0,
        target1 -
        entry_price,
    )

    reward2 = max(
        0.0,
        target2 -
        entry_price,
    )

    rr1 = (
        reward1 /
        risk_points
        if risk_points > 0
        else None
    )

    rr2 = (
        reward2 /
        risk_points
        if risk_points > 0
        else None
    )

    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    if rr1 is None:

        quality = "N/A"

    elif rr1 >= 2.0:

        quality = "Strong"

    elif rr1 >= 1.5:

        quality = "Acceptable"

    else:

        quality = "Poor"

    if (
        rr1 is not None
        and rr1 >= 1.5
    ):

        status = "Actionable"

    else:

        status = "Confirmation Required"

    # -----------------------------------------------------
    # Reason
    # -----------------------------------------------------

    reason_parts = []

    trend = text_value(
        row,
        [
            "Trend",
            "trend",
        ],
    )

    momentum = text_value(
        row,
        [
            "Momentum",
            "momentum",
        ],
    )

    breakout = text_value(
        row,
        [
            "Breakout",
            "Breakout_Status",
            "breakout",
        ],
    )

    if trend:
        reason_parts.append(
            f"Trend: {trend}"
        )

    if momentum:
        reason_parts.append(
            f"Momentum: {momentum}"
        )

    if breakout:
        reason_parts.append(
            f"Breakout: {breakout}"
        )

    reason = "; ".join(
        reason_parts
    )

    if not reason:

        reason = (
            f"{setup} identified "
            "by the ranking engine."
        )

    # -----------------------------------------------------
    # Invalidation
    # -----------------------------------------------------

    invalidation_parts = []

    if support is not None:

        invalidation_parts.append(
            f"close below support {support:.2f}"
        )

    if sma200 is not None:

        invalidation_parts.append(
            f"loss of 200 DMA {sma200:.2f}"
        )

    invalidation_parts.append(
        f"stop loss {stop_loss:.2f}"
    )

    invalidation = "; ".join(
        invalidation_parts
    )

    return {
        "entry_low":
            round(
                entry_low,
                2,
            ),

        "entry_high":
            round(
                entry_high,
                2,
            ),

        "entry_price":
            round(
                entry_price,
                2,
            ),

        "stop_loss":
            round(
                stop_loss,
                2,
            ),

        "target_1":
            round(
                target1,
                2,
            ),

        "target_2":
            round(
                target2,
                2,
            ),

        "risk_points":
            round(
                risk_points,
                2,
            ),

        "reward_1_points":
            round(
                reward1,
                2,
            ),

        "reward_2_points":
            round(
                reward2,
                2,
            ),

        "risk_reward_1":
            round(
                rr1,
                2,
            )
            if rr1 is not None
            else None,

        "risk_reward_2":
            round(
                rr2,
                2,
            )
            if rr2 is not None
            else None,

        "risk_reward":
            round(
                rr1,
                2,
            )
            if rr1 is not None
            else None,

        "trade_plan_type":
            setup,

        "trade_plan_status":
            status,

        "trade_plan_reason":
            reason,

        "trade_plan_invalidation":
            invalidation,

        "trade_plan_quality":
            quality,
    }


# =========================================================
# RANK ONE STOCK
# =========================================================

def rank_one_stock(
    row: Any,
    sector_data: Any = None,
    market_regime: Any = None,
) -> dict:

    result = dict(row)

    technical_score = (
        calculate_technical_score(
            row
        )
    )

    fundamental_score = (
        calculate_fundamental_score(
            row
        )
    )

    sector_score = (
        get_sector_score(
            row,
            sector_data,
        )
    )

    market_adjustment = (
        get_market_adjustment(
            market_regime
        )
    )

    # If fundamental data is substantially unavailable,
    # don't punish the stock as though fundamentals are zero.
    fundamental_fields = [
        "ROE",
        "ROCE",
        "Revenue_Growth",
        "Profit_Growth",
        "Debt_to_Equity",
        "Operating_Margin",
        "PE",
        "PB",
    ]

    available_fundamentals = sum(
        not is_missing(
            first_value(
                row,
                [field],
            )
        )
        for field
        in fundamental_fields
    )

    if available_fundamentals <= 1:

        base_score = technical_score
        fundamental_score_for_output = None

    else:

        base_score = (
            technical_score *
            TECHNICAL_WEIGHT
            +
            fundamental_score *
            FUNDAMENTAL_WEIGHT
        )

        fundamental_score_for_output = (
            fundamental_score
        )

    # Sector adjustment.
    sector_adjustment = (
        sector_score -
        50.0
    ) * 0.10

    overall_score = clamp(
        base_score
        +
        sector_adjustment
        +
        market_adjustment
    )

    classification_row = dict(row)
    classification_row["Overall_Score"] = (
        overall_score
    )

    setup = classify_setup(
        classification_row
    )

    trade_plan_row = dict(row)
    trade_plan_row["Overall_Score"] = (
        overall_score
    )

    trade_plan = calculate_trade_plan(
        trade_plan_row
    )

    result["Technical_Score"] = round(
        technical_score,
        2,
    )

    result["Fundamental_Score"] = (
        round(
            fundamental_score_for_output,
            2,
        )
        if fundamental_score_for_output
        is not None
        else np.nan
    )

    result["Sector_Score"] = round(
        sector_score,
        2,
    )

    result["Market_Adjustment"] = round(
        market_adjustment,
        2,
    )

    result["Overall_Score"] = round(
        overall_score,
        2,
    )

    result["Setup"] = setup

    result.update(
        trade_plan
    )

    # Ranking quality.
    result["Ranking_Quality"] = (
        "Excellent"
        if overall_score >= 80
        else
        "Strong"
        if overall_score >= 70
        else
        "Good"
        if overall_score >= 60
        else
        "Watch"
        if overall_score >= 50
        else
        "Weak"
    )

    return result


# =========================================================
# RANK ALL STOCKS
# =========================================================

def rank_stocks(
    technical_data: Any,
    fundamental_data: Any = None,
    sector_data: Any = None,
    market_regime: Any = None,
) -> pd.DataFrame:

    """
    Main public ranking function.

    Compatible with:

        rank_stocks(
            technical_data,
            fundamental_data,
            sector_data,
            market_regime
        )

    and:

        rank_stocks(
            technical_data,
            market_regime=...,
            sector_data=...
        )
    """

    technical = ensure_dataframe(
        technical_data
    )

    if technical.empty:
        return pd.DataFrame()

    fundamentals = ensure_dataframe(
        fundamental_data
    )

    sectors = ensure_dataframe(
        sector_data
    )

    data = technical.copy()

    # Normalise symbols.
    symbol_col = find_column(
        data,
        [
            "Symbol",
            "symbol",
            "SYMBOL",
            "Ticker",
        ],
    )

    if symbol_col is None:

        raise ValueError(
            "Ranking engine requires a Symbol column."
        )

    if symbol_col != "Symbol":

        data = data.rename(
            columns={
                symbol_col:
                    "Symbol"
            }
        )

    data["Symbol"] = (
        data["Symbol"]
        .apply(
            normalise_symbol
        )
    )

    # Merge fundamentals if supplied separately.
    if not fundamentals.empty:

        fundamental_symbol_col = (
            find_column(
                fundamentals,
                [
                    "Symbol",
                    "symbol",
                    "SYMBOL",
                    "Ticker",
                ],
            )
        )

        if fundamental_symbol_col is not None:

            if (
                fundamental_symbol_col
                != "Symbol"
            ):

                fundamentals = (
                    fundamentals.rename(
                        columns={
                            fundamental_symbol_col:
                                "Symbol"
                        }
                    )
                )

            fundamentals["Symbol"] = (
                fundamentals["Symbol"]
                .apply(
                    normalise_symbol
                )
            )

            duplicate_columns = [
                column
                for column
                in fundamentals.columns
                if (
                    column in data.columns
                    and column != "Symbol"
                )
            ]

            if duplicate_columns:

                fundamentals = (
                    fundamentals.drop(
                        columns=duplicate_columns
                    )
                )

            data = data.merge(
                fundamentals,
                on="Symbol",
                how="left",
            )

    # Ensure sector column.
    if "Primary_Sector" not in data.columns:

        sector_column = find_column(
            data,
            [
                "primary_sector",
                "Sector",
                "sector",
            ],
        )

        if sector_column is not None:

            data["Primary_Sector"] = (
                data[sector_column]
            )

        else:

            data["Primary_Sector"] = (
                "Unknown"
            )

    # Rank each stock.
    ranked_records = []

    total = len(data)

    for position, (_, row) in enumerate(
        data.iterrows(),
        start=1,
    ):

        ranked_records.append(
            rank_one_stock(
                row,
                sectors,
                market_regime,
            )
        )

        if (
            position % 250 == 0
            or position == total
        ):

            print(
                "Ranking progress: "
                f"{position:,}/{total:,}"
            )

    ranked = pd.DataFrame(
        ranked_records
    )

    if ranked.empty:
        return ranked

    # Sort by overall score.
    ranked = (
        ranked
        .sort_values(
            by=[
                "Overall_Score",
                "Technical_Score",
            ],
            ascending=[
                False,
                False,
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    ranked["Rank"] = (
        np.arange(
            len(ranked)
        ) + 1
    )

    # Put Rank first.
    columns = [
        "Rank"
    ] + [
        column
        for column
        in ranked.columns
        if column != "Rank"
    ]

    ranked = ranked[
        columns
    ]

    return ranked


# =========================================================
# WATCHLIST HELPERS
# =========================================================

def positive_trend(
    row: Any,
) -> bool:

    score = calculate_trend_score(
        row
    )

    return score >= 70


def positive_momentum(
    row: Any,
) -> bool:

    score = calculate_momentum_score(
        row
    )

    return score >= 70


def confirmed_breakout(
    row: Any,
) -> bool:

    breakout = text_value(
        row,
        [
            "Breakout",
            "Breakout_Status",
            "breakout",
        ],
    ).lower()

    return (
        "confirmed" in breakout
        or "strong breakout"
        in breakout
    )


def possible_breakout(
    row: Any,
) -> bool:

    score = calculate_breakout_score(
        row
    )

    return score >= 70


def above_200dma(
    row: Any,
) -> bool:

    value = first_value(
        row,
        [
            "Above_200DMA",
            "above_200dma",
        ],
    )

    if not is_missing(value):

        if isinstance(
            value,
            str,
        ):

            return (
                value
                .strip()
                .lower()
                in {
                    "true",
                    "yes",
                    "1",
                    "above",
                }
            )

        return bool(value)

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    sma200 = first_float(
        row,
        [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],
    )

    return (
        price is not None
        and sma200 is not None
        and price > sma200
    )


def near_52w_high(
    row: Any,
    tolerance_pct: float = 3.0,
) -> bool:

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    high52 = first_float(
        row,
        [
            "52W_High",
            "High_52W",
            "high_52w",
        ],
    )

    if (
        price is None
        or high52 is None
        or high52 <= 0
    ):
        return False

    distance = (
        (
            high52 -
            price
        )
        /
        high52
    ) * 100.0

    return (
        0 <= distance <=
        tolerance_pct
    )


def near_200dma(
    row: Any,
    tolerance_pct: float = 3.0,
) -> bool:

    price = first_float(
        row,
        [
            "Close",
            "close",
            "Price",
            "price",
        ],
    )

    sma200 = first_float(
        row,
        [
            "SMA_200",
            "SMA200",
            "sma200",
            "200_DMA",
        ],
    )

    if (
        price is None
        or sma200 is None
        or sma200 <= 0
    ):
        return False

    distance = abs(
        (
            price -
            sma200
        )
        /
        sma200
    ) * 100.0

    return distance <= tolerance_pct


def quality_actionable(
    row: Any,
) -> bool:

    score = first_float(
        row,
        [
            "Overall_Score",
            "overall_score",
            "Score",
        ],
        0.0,
    )

    setup = text_value(
        row,
        [
            "Setup",
            "setup",
        ],
    ).lower()

    if score is None:
        score = 0.0

    if score < MIN_ACTIONABLE_SCORE:
        return False

    if (
        "weak" in setup
        or "avoid" in setup
    ):
        return False

    return True


def trade_plan_actionable(
    row: Any,
) -> bool:

    status = text_value(
        row,
        [
            "trade_plan_status",
            "Trade_Plan_Status",
        ],
    ).lower()

    rr = first_float(
        row,
        [
            "risk_reward_1",
            "Risk_Reward_1",
            "risk_reward",
            "Risk_Reward",
        ],
    )

    return (
        status == "actionable"
        and (
            rr is None
            or rr >= 1.5
        )
    )


def safe_score(
    row: Any,
) -> float:

    value = first_float(
        row,
        [
            "Overall_Score",
            "overall_score",
            "Score",
            "score",
        ],
        0.0,
    )

    return (
        value
        if value is not None
        else 0.0
    )


def safe_sort(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if columns is None:
        columns = [
            column
            for column in [
                "Overall_Score",
                "Technical_Score",
                "Fundamental_Score",
                "Sector_Score",
            ]
            if column in result.columns
        ]

    if columns:

        available = [
            column
            for column in columns
            if column in result.columns
        ]

        if available:

            result = (
                result
                .sort_values(
                    by=available,
                    ascending=False,
                    na_position="last",
                )
                .reset_index(
                    drop=True
                )
            )

    return result


# =========================================================
# WATCHLIST CREATION
# =========================================================

def create_watchlists(
    ranked_data: Any,
    market_regime: Any = None,
) -> dict[str, pd.DataFrame]:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:

        return {
            "next_day": pd.DataFrame(),
            "intraday": pd.DataFrame(),
            "swing": pd.DataFrame(),
            "long_term": pd.DataFrame(),
            "52w_high": pd.DataFrame(),
            "dma_recovery": pd.DataFrame(),
            "momentum": pd.DataFrame(),
            "breakout": pd.DataFrame(),
            "options": pd.DataFrame(),
        }

    # -----------------------------------------------------
    # Market environment
    # -----------------------------------------------------

    regime = ""

    if isinstance(
        market_regime,
        pd.DataFrame,
    ):

        if not market_regime.empty:

            market_regime = (
                market_regime
                .iloc[-1]
                .to_dict()
            )

    if isinstance(
        market_regime,
        dict,
    ):

        regime = str(
            market_regime.get(
                "market_regime",
                market_regime.get(
                    "Regime",
                    "",
                ),
            )
        ).lower()

    weak_market = any(
        term in regime
        for term in [
            "weak",
            "bear",
            "cautious",
        ]
    )

    strong_market = any(
        term in regime
        for term in [
            "strong bull",
            "bullish",
            "positive",
        ]
    )

    # -----------------------------------------------------
    # Build candidate frames
    # -----------------------------------------------------

    next_day_records = []
    intraday_records = []
    swing_records = []
    long_term_records = []
    high_records = []
    dma_records = []
    momentum_records = []
    breakout_records = []
    options_records = []

    for _, row in ranked.iterrows():

        setup = text_value(
            row,
            [
                "Setup",
                "setup",
            ],
        )

        setup_lower = setup.lower()

        score = safe_score(row)

        if score < MIN_ACTIONABLE_SCORE:
            continue

        if (
            "weak" in setup_lower
            or "avoid" in setup_lower
        ):
            continue

        actionable = trade_plan_actionable(
            row
        )

        positive_trend_flag = positive_trend(
            row
        )

        positive_momentum_flag = positive_momentum(
            row
        )

        confirmed = confirmed_breakout(
            row
        )

        possible = possible_breakout(
            row
        )

        above_dma = above_200dma(
            row
        )

        high_watch = near_52w_high(
            row
        )

        dma_watch = near_200dma(
            row
        )

        # -------------------------------------------------
        # Next day
        # -------------------------------------------------

        if (
            (
                confirmed
                or possible
                or high_watch
            )
            and positive_trend_flag
            and (
                strong_market
                or not weak_market
            )
        ):

            next_day_records.append(row.to_dict())

        # -------------------------------------------------
        # Intraday
        #
        # This is a candidate watchlist only when the
        # backend is not providing live intraday prices.
        # -------------------------------------------------

        if (
            (
                confirmed
                or (
                    positive_momentum_flag
                    and positive_trend_flag
                )
            )
            and score >= 60
        ):

            intraday_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # Swing
        # -------------------------------------------------

        if (
            positive_trend_flag
            and positive_momentum_flag
            and above_dma
            and score >= 55
            and actionable
        ):

            swing_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # Long term
        # -------------------------------------------------

        fundamental_score = first_float(
            row,
            [
                "Fundamental_Score",
                "fundamental_score",
            ],
        )

        if (
            above_dma
            and score >= 60
            and (
                fundamental_score is None
                or fundamental_score >= 55
            )
        ):

            long_term_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # 52W high
        # -------------------------------------------------

        if high_watch:

            high_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # 200 DMA recovery
        # -------------------------------------------------

        if dma_watch:

            dma_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # Momentum
        # -------------------------------------------------

        if (
            positive_momentum_flag
            and positive_trend_flag
            and score >= 55
        ):

            momentum_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # Breakout
        # -------------------------------------------------

        if possible or confirmed:

            breakout_records.append(
                row.to_dict()
            )

        # -------------------------------------------------
        # Options
        #
        # This is an underlying-stock watchlist.
        # It does not claim that a specific option contract
        # is liquid or available.
        # -------------------------------------------------

        options_liquidity = first_float(
            row,
            [
                "Volume_Ratio",
                "volume_ratio",
            ],
        )

        if (
            (
                confirmed
                or positive_momentum_flag
                or high_watch
            )
            and score >= 60
            and (
                options_liquidity is None
                or options_liquidity >= 0.8
            )
        ):

            options_records.append(
                row.to_dict()
            )

    watchlists = {
        "next_day": safe_sort(
            pd.DataFrame(
                next_day_records
            )
        ),

        "intraday": safe_sort(
            pd.DataFrame(
                intraday_records
            )
        ),

        "swing": safe_sort(
            pd.DataFrame(
                swing_records
            )
        ),

        "long_term": safe_sort(
            pd.DataFrame(
                long_term_records
            )
        ),

        "52w_high": safe_sort(
            pd.DataFrame(
                high_records
            )
        ),

        "dma_recovery": safe_sort(
            pd.DataFrame(
                dma_records
            )
        ),

        "momentum": safe_sort(
            pd.DataFrame(
                momentum_records
            )
        ),

        "breakout": safe_sort(
            pd.DataFrame(
                breakout_records
            )
        ),

        "options": safe_sort(
            pd.DataFrame(
                options_records
            )
        ),
    }

    return watchlists


# =========================================================
# SETUP SUMMARY
# =========================================================

def create_setup_summary(
    ranked_data: Any,
) -> pd.DataFrame:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:

        return pd.DataFrame(
            columns=[
                "Setup",
                "Count",
                "Average_Score",
                "Actionable_Count",
                "Average_Risk_Reward",
            ]
        )

    if "Setup" not in ranked.columns:

        ranked["Setup"] = "Neutral Watch"

    records = []

    for setup, group in ranked.groupby(
        "Setup",
        dropna=False,
    ):

        score_values = pd.to_numeric(
            group.get(
                "Overall_Score",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        )

        rr_values = pd.to_numeric(
            group.get(
                "risk_reward_1",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        )

        status_values = (
            group.get(
                "trade_plan_status",
                pd.Series(
                    "",
                    index=group.index,
                ),
            )
            .astype(str)
            .str.lower()
        )

        actionable_count = int(
            (
                status_values
                == "actionable"
            ).sum()
        )

        records.append(
            {
                "Setup": str(setup),
                "Count": int(len(group)),
                "Average_Score": round(
                    float(
                        score_values.mean()
                    )
                    if not score_values.dropna().empty
                    else 0.0,
                    2,
                ),
                "Actionable_Count":
                    actionable_count,
                "Average_Risk_Reward":
                    round(
                        float(
                            rr_values.mean()
                        )
                        if not rr_values.dropna().empty
                        else 0.0,
                        2,
                    ),
            }
        )

    summary = pd.DataFrame(
        records
    )

    if summary.empty:
        return summary

    preferred_order = [
        "Strong Breakout Watch",
        "Breakout Confirmation Required",
        "Pre-Breakout Watch",
        "52W High Watch",
        "200 DMA Recovery Watch",
        "Momentum Watch",
        "Neutral Watch",
        "Weak / Avoid",
    ]

    order_map = {
        value: index
        for index, value
        in enumerate(
            preferred_order
        )
    }

    summary["_order"] = (
        summary["Setup"]
        .map(order_map)
        .fillna(999)
    )

    summary = (
        summary
        .sort_values(
            by=[
                "_order",
                "Average_Score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop(
            columns=["_order"]
        )
        .reset_index(
            drop=True
        )
    )

    return summary


# =========================================================
# EXPORT PREPARATION
# =========================================================

def prepare_export_data(
    ranked_data: Any,
    watchlists: Any = None,
    setup_summary: Any = None,
) -> dict[str, pd.DataFrame]:

    ranked = ensure_dataframe(
        ranked_data
    )

    exports: dict[str, pd.DataFrame] = {}

    exports["stocks"] = ranked.copy()

    if setup_summary is not None:

        exports["setup_summary"] = (
            ensure_dataframe(
                setup_summary
            )
        )

    if watchlists is not None:

        if isinstance(
            watchlists,
            dict,
        ):

            for name, values in watchlists.items():

                if isinstance(
                    values,
                    pd.DataFrame,
                ):

                    exports[name] = (
                        values.copy()
                    )

                elif isinstance(
                    values,
                    list,
                ):

                    exports[name] = (
                        pd.DataFrame(values)
                    )

                elif isinstance(
                    values,
                    dict,
                ):

                    exports[name] = (
                        pd.DataFrame(values)
                    )

                else:

                    exports[name] = (
                        pd.DataFrame()
                    )

    return exports


# =========================================================
# JSON-SAFE CONVERSION
# =========================================================

def make_json_safe(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,),
    ):

        if not math.isfinite(
            float(value)
        ):
            return None

        return float(value)

    if isinstance(
        value,
        (np.bool_,),
    ):
        return bool(value)

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                make_json_safe(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):

        return [
            make_json_safe(item)
            for item in value
        ]

    if is_missing(value):
        return None

    return value


# =========================================================
# WATCHLIST SERIALISATION
# =========================================================

def watchlists_to_records(
    watchlists: dict[str, pd.DataFrame],
) -> dict[str, list[dict]]:

    result = {}

    for name, dataframe in (
        watchlists or {}
    ).items():

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):
            dataframe = ensure_dataframe(
                dataframe
            )

        if dataframe.empty:

            result[name] = []
            continue

        records = (
            dataframe
            .replace(
                {
                    np.nan: None
                }
            )
            .to_dict(
                orient="records"
            )
        )

        result[name] = [
            make_json_safe(record)
            for record in records
        ]

    return result


# =========================================================
# SETUP COUNTS
# =========================================================

def get_setup_counts(
    ranked_data: Any,
) -> dict[str, int]:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:
        return {}

    if "Setup" not in ranked.columns:
        return {}

    counts = (
        ranked["Setup"]
        .fillna("Neutral Watch")
        .astype(str)
        .value_counts()
        .to_dict()
    )

    return {
        str(key): int(value)
        for key, value
        in counts.items()
    }


# =========================================================
# WATCHLIST COUNTS
# =========================================================

def get_watchlist_counts(
    watchlists: dict[str, pd.DataFrame],
) -> dict[str, int]:

    counts = {}

    for name, dataframe in (
        watchlists or {}
    ).items():

        if isinstance(
            dataframe,
            pd.DataFrame,
        ):

            counts[name] = int(
                len(dataframe)
            )

        else:

            try:
                counts[name] = int(
                    len(dataframe)
                )
            except (
                TypeError,
                ValueError,
            ):
                counts[name] = 0

    return counts


# =========================================================
# TOP STOCKS
# =========================================================

def get_top_stocks(
    ranked_data: Any,
    limit: int = 15,
) -> pd.DataFrame:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:
        return ranked

    return safe_sort(
        ranked
    ).head(
        int(limit)
    ).copy()


# =========================================================
# PORTFOLIO CANDIDATES
# =========================================================

def get_portfolio_candidates(
    ranked_data: Any,
    limit: int = 50,
) -> pd.DataFrame:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:
        return ranked

    working = ranked.copy()

    if "Setup" in working.columns:

        setup_lower = (
            working["Setup"]
            .fillna("")
            .astype(str)
            .str.lower()
        )

        working = working[
            ~setup_lower.str.contains(
                "weak|avoid",
                regex=True,
            )
        ]

    if "Overall_Score" in working.columns:

        working["_score"] = pd.to_numeric(
            working["Overall_Score"],
            errors="coerce",
        )

        working = working[
            working["_score"]
            >= MIN_ACTIONABLE_SCORE
        ]

    if "trade_plan_status" in working.columns:

        status = (
            working["trade_plan_status"]
            .fillna("")
            .astype(str)
            .str.lower()
        )

        actionable = working[
            status == "actionable"
        ]

        if not actionable.empty:
            working = actionable

    if "risk_reward_1" in working.columns:

        rr = pd.to_numeric(
            working["risk_reward_1"],
            errors="coerce",
        )

        filtered = working[
            rr.isna()
            | (rr >= 1.5)
        ]

        if not filtered.empty:
            working = filtered

    working = safe_sort(
        working
    )

    return working.head(
        int(limit)
    ).copy()


# =========================================================
# STOCK DETAIL DATA
# =========================================================

def build_stock_detail(
    row: Any,
) -> dict:

    if isinstance(
        row,
        pd.Series,
    ):
        record = row.to_dict()

    elif isinstance(
        row,
        dict,
    ):
        record = dict(row)

    else:
        record = {}

    detail = {
        "symbol":
            normalise_symbol(
                first_value(
                    record,
                    [
                        "Symbol",
                        "symbol",
                    ],
                )
            ),

        "company_name":
            text_value(
                record,
                [
                    "Company_Name",
                    "company_name",
                    "Company",
                    "Name",
                ],
            ),

        "price":
            first_float(
                record,
                [
                    "Close",
                    "close",
                    "Price",
                    "price",
                ],
            ),

        "overall_score":
            first_float(
                record,
                [
                    "Overall_Score",
                    "overall_score",
                    "Score",
                    "score",
                ],
            ),

        "technical_score":
            first_float(
                record,
                [
                    "Technical_Score",
                    "technical_score",
                ],
            ),

        "fundamental_score":
            first_float(
                record,
                [
                    "Fundamental_Score",
                    "fundamental_score",
                ],
            ),

        "sector_score":
            first_float(
                record,
                [
                    "Sector_Score",
                    "sector_score",
                ],
            ),

        "setup":
            text_value(
                record,
                [
                    "Setup",
                    "setup",
                ],
            ),

        "trend":
            text_value(
                record,
                [
                    "Trend",
                    "trend",
                ],
            ),

        "momentum":
            text_value(
                record,
                [
                    "Momentum",
                    "momentum",
                ],
            ),

        "rsi":
            first_float(
                record,
                [
                    "RSI_14",
                    "RSI14",
                    "RSI",
                ],
            ),

        "sma20":
            first_float(
                record,
                [
                    "SMA_20",
                    "SMA20",
                ],
            ),

        "sma50":
            first_float(
                record,
                [
                    "SMA_50",
                    "SMA50",
                ],
            ),

        "sma200":
            first_float(
                record,
                [
                    "SMA_200",
                    "SMA200",
                    "200_DMA",
                ],
            ),

        "atr":
            first_float(
                record,
                [
                    "ATR_14",
                    "ATR14",
                    "ATR",
                ],
            ),

        "volume_ratio":
            first_float(
                record,
                [
                    "Volume_Ratio",
                    "volume_ratio",
                ],
            ),

        "support":
            first_float(
                record,
                [
                    "Support",
                    "support",
                ],
            ),

        "resistance":
            first_float(
                record,
                [
                    "Resistance",
                    "resistance",
                ],
            ),

        "high_52w":
            first_float(
                record,
                [
                    "52W_High",
                    "High_52W",
                ],
            ),

        "low_52w":
            first_float(
                record,
                [
                    "52W_Low",
                    "Low_52W",
                ],
            ),

        "primary_sector":
            text_value(
                record,
                [
                    "Primary_Sector",
                    "primary_sector",
                    "Sector",
                    "sector",
                ],
                "Unknown",
            ),

        "trade_plan_type":
            text_value(
                record,
                [
                    "trade_plan_type",
                    "Trade_Plan_Type",
                ],
            ),

        "trade_plan_status":
            text_value(
                record,
                [
                    "trade_plan_status",
                    "Trade_Plan_Status",
                ],
            ),

        "trade_plan_reason":
            text_value(
                record,
                [
                    "trade_plan_reason",
                    "Trade_Plan_Reason",
                ],
            ),

        "trade_plan_invalidation":
            text_value(
                record,
                [
                    "trade_plan_invalidation",
                    "Trade_Plan_Invalidation",
                ],
            ),

        "entry_low":
            first_float(
                record,
                [
                    "entry_low",
                    "Entry_Low",
                ],
            ),

        "entry_high":
            first_float(
                record,
                [
                    "entry_high",
                    "Entry_High",
                ],
            ),

        "entry_price":
            first_float(
                record,
                [
                    "entry_price",
                    "Entry_Price",
                ],
            ),

        "stop_loss":
            first_float(
                record,
                [
                    "stop_loss",
                    "Stop_Loss",
                ],
            ),

        "target_1":
            first_float(
                record,
                [
                    "target_1",
                    "Target_1",
                ],
            ),

        "target_2":
            first_float(
                record,
                [
                    "target_2",
                    "Target_2",
                ],
            ),

        "risk_points":
            first_float(
                record,
                [
                    "risk_points",
                    "Risk_Points",
                ],
            ),

        "risk_reward_1":
            first_float(
                record,
                [
                    "risk_reward_1",
                    "Risk_Reward_1",
                    "risk_reward",
                    "Risk_Reward",
                ],
            ),

        "risk_reward_2":
            first_float(
                record,
                [
                    "risk_reward_2",
                    "Risk_Reward_2",
                ],
            ),

        "trade_plan_quality":
            text_value(
                record,
                [
                    "trade_plan_quality",
                    "Trade_Plan_Quality",
                ],
            ),

        "company_sector":
            text_value(
                record,
                [
                    "Sector",
                    "sector",
                ],
            ),

        "industry":
            text_value(
                record,
                [
                    "Industry",
                    "industry",
                ],
            ),

        "market_cap":
            first_float(
                record,
                [
                    "Market_Cap",
                    "market_cap",
                ],
            ),

        "pe":
            first_float(
                record,
                [
                    "PE",
                    "PE_Ratio",
                    "pe",
                ],
            ),

        "pb":
            first_float(
                record,
                [
                    "PB",
                    "PB_Ratio",
                    "pb",
                ],
            ),

        "roe":
            first_float(
                record,
                [
                    "ROE",
                    "roe",
                ],
            ),

        "roce":
            first_float(
                record,
                [
                    "ROCE",
                    "roce",
                ],
            ),

        "debt_equity":
            first_float(
                record,
                [
                    "Debt_to_Equity",
                    "Debt_Equity",
                    "debt_to_equity",
                ],
            ),

        "revenue_growth":
            first_float(
                record,
                [
                    "Revenue_Growth",
                    "Revenue_CAGR",
                    "revenue_growth",
                ],
            ),

        "profit_growth":
            first_float(
                record,
                [
                    "Profit_Growth",
                    "Profit_CAGR",
                    "profit_growth",
                ],
            ),
    }

    return make_json_safe(
        detail
    )


# =========================================================
# ENGINE SUMMARY
# =========================================================

def get_engine_summary(
    ranked_data: Any,
) -> dict:

    ranked = ensure_dataframe(
        ranked_data
    )

    if ranked.empty:

        return {
            "stock_count": 0,
            "average_score": None,
            "top_score": None,
            "actionable_count": 0,
            "weak_count": 0,
        }

    scores = pd.to_numeric(
        ranked.get(
            "Overall_Score",
            pd.Series(dtype=float),
        ),
        errors="coerce",
    )

    setups = (
        ranked.get(
            "Setup",
            pd.Series(
                "",
                index=ranked.index,
            ),
        )
        .fillna("")
        .astype(str)
        .str.lower()
    )

    statuses = (
        ranked.get(
            "trade_plan_status",
            pd.Series(
                "",
                index=ranked.index,
            ),
        )
        .fillna("")
        .astype(str)
        .str.lower()
    )

    return {
        "stock_count":
            int(len(ranked)),

        "average_score":
            round(
                float(scores.mean()),
                2,
            )
            if not scores.dropna().empty
            else None,

        "top_score":
            round(
                float(scores.max()),
                2,
            )
            if not scores.dropna().empty
            else None,

        "actionable_count":
            int(
                (
                    statuses ==
                    "actionable"
                ).sum()
            ),

        "weak_count":
            int(
                setups.str.contains(
                    "weak|avoid",
                    regex=True,
                ).sum()
            ),
    }


# =========================================================
# PUBLIC API
# =========================================================

__all__ = [
    "rank_stocks",
    "rank_one_stock",
    "calculate_technical_score",
    "calculate_fundamental_score",
    "get_sector_score",
    "get_market_adjustment",
    "classify_setup",
    "calculate_trade_plan",
    "create_watchlists",
    "create_setup_summary",
    "prepare_export_data",
    "watchlists_to_records",
    "get_setup_counts",
    "get_watchlist_counts",
    "get_top_stocks",
    "get_portfolio_candidates",
    "build_stock_detail",
    "get_engine_summary",
]
