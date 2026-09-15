import pandas as pd
import numpy as np


# ============================================================
# NSE SMART MARKET DASHBOARD
# RANKING & SETUP ENGINE
# ============================================================


# ============================================================
# TECHNICAL SCORE COMPONENTS
# ============================================================

def trend_score(row):
    """
    Score the broad price trend.
    Maximum: 20 points
    """

    trend = row.get("trend", "")

    scores = {
        "Strong Uptrend": 20,
        "Uptrend": 16,
        "Sideways": 8,
        "Downtrend": 3,
        "Strong Downtrend": 0,
        "Insufficient Data": 0
    }

    return scores.get(
        trend,
        0
    )


def momentum_score(row):
    """
    Score price momentum.
    Maximum: 15 points
    """

    momentum = row.get(
        "momentum",
        ""
    )

    scores = {
        "Strong Positive": 15,
        "Positive": 11,
        "Neutral": 7,
        "Negative": 3,
        "Strong Negative": 0,
        "Insufficient Data": 0
    }

    return scores.get(
        momentum,
        0
    )


def rsi_score(row):
    """
    Score RSI.

    We don't blindly reward a high RSI.
    Extremely overbought conditions receive
    a lower score.
    """

    rsi = row.get(
        "rsi14",
        np.nan
    )

    if pd.isna(rsi):
        return 0

    if 55 <= rsi <= 68:
        return 15

    elif 50 <= rsi < 55:
        return 12

    elif 68 < rsi <= 72:
        return 11

    elif 45 <= rsi < 50:
        return 8

    elif 40 <= rsi < 45:
        return 5

    elif rsi > 72:
        return 7

    else:
        return 2


def volume_score(row):
    """
    Score volume confirmation.
    Maximum: 15 points
    """

    ratio = row.get(
        "volume_ratio",
        np.nan
    )

    if pd.isna(ratio):
        return 0

    if ratio >= 2.0:
        return 15

    elif ratio >= 1.5:
        return 13

    elif ratio >= 1.25:
        return 10

    elif ratio >= 1.0:
        return 7

    elif ratio >= 0.75:
        return 4

    else:
        return 1


def position_score(row):
    """
    Score price position relative to 200 DMA
    and 52-week high.

    Maximum: 15 points
    """

    score = 0

    above_200dma = row.get(
        "above_200dma",
        False
    )

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    if above_200dma:
        score += 8

    if not pd.isna(distance_high):

        # Near 52-week high
        if -2 <= distance_high <= 0:
            score += 7

        elif -5 <= distance_high < -2:
            score += 6

        elif -10 <= distance_high < -5:
            score += 4

        elif -20 <= distance_high < -10:
            score += 2

    return min(
        score,
        15
    )


def breakout_score(row):
    """
    Score breakout conditions.
    Maximum: 20 points
    """

    status = row.get(
        "breakout_status",
        ""
    )

    if status == "Confirmed Breakout":
        return 20

    elif status == "Breakout - Volume Confirmation Required":
        return 14

    elif status == "Near Breakout":
        return 10

    else:
        return 4


# ============================================================
# TECHNICAL SCORE
# ============================================================

def calculate_technical_score(row):
    """
    Calculate technical score out of 100.

    Components:

    Trend       = 20
    Momentum    = 15
    RSI         = 15
    Volume      = 15
    Position    = 15
    Breakout    = 20
    """

    score = (
        trend_score(row)
        + momentum_score(row)
        + rsi_score(row)
        + volume_score(row)
        + position_score(row)
        + breakout_score(row)
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


# ============================================================
# SETUP DETECTION
# ============================================================

def identify_setup(row):
    """
    Identify the most relevant trading setup.

    Priority is given to stronger price-action
    conditions first.
    """

    trend = row.get(
        "trend",
        ""
    )

    momentum = row.get(
        "momentum",
        ""
    )

    breakout = row.get(
        "breakout_status",
        ""
    )

    above_200dma = row.get(
        "above_200dma",
        False
    )

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    rsi = row.get(
        "rsi14",
        np.nan
    )

    volume_ratio = row.get(
        "volume_ratio",
        np.nan
    )

    # --------------------------------------------------------
    # Confirmed Breakout
    # --------------------------------------------------------

    if (
        breakout == "Confirmed Breakout"
        and volume_ratio >= 1.5
    ):
        return "Strong Breakout Watch"

    # --------------------------------------------------------
    # Near 52W High
    # --------------------------------------------------------

    if (
        above_200dma
        and not pd.isna(distance_high)
        and distance_high >= -5
        and trend in [
            "Strong Uptrend",
            "Uptrend"
        ]
    ):
        return "52W High Watch"

    # --------------------------------------------------------
    # Momentum Setup
    # --------------------------------------------------------

    if (
        trend in [
            "Strong Uptrend",
            "Uptrend"
        ]
        and momentum in [
            "Strong Positive",
            "Positive"
        ]
        and volume_ratio >= 1.25
    ):
        return "Momentum Watch"

    # --------------------------------------------------------
    # 200 DMA Recovery
    # --------------------------------------------------------

    distance_200 = row.get(
        "distance_from_200dma_pct",
        np.nan
    )

    if not pd.isna(distance_200):

        if (
            -3 <= distance_200 <= 3
            and rsi >= 45
        ):
            return "200 DMA Recovery Watch"

    # --------------------------------------------------------
    # Breakout Confirmation Required
    # --------------------------------------------------------

    if (
        breakout ==
        "Breakout - Volume Confirmation Required"
    ):
        return "Breakout Confirmation Required"

    # --------------------------------------------------------
    # Near Breakout
    # --------------------------------------------------------

    if breakout == "Near Breakout":
        return "Pre-Breakout Watch"

    # --------------------------------------------------------
    # Weak Conditions
    # --------------------------------------------------------

    if trend in [
        "Strong Downtrend",
        "Downtrend"
    ]:
        return "Weak / Avoid"

    return "Neutral Watch"


# ============================================================
# REASONS
# ============================================================

def generate_reasons(row):
    """
    Generate human-readable reasons explaining
    why the stock received its setup.
    """

    reasons = []

    trend = row.get(
        "trend",
        ""
    )

    momentum = row.get(
        "momentum",
        ""
    )

    rsi = row.get(
        "rsi14",
        np.nan
    )

    volume_ratio = row.get(
        "volume_ratio",
        np.nan
    )

    above_200dma = row.get(
        "above_200dma",
        False
    )

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    breakout = row.get(
        "breakout_status",
        ""
    )

    distance_200 = row.get(
        "distance_from_200dma_pct",
        np.nan
    )

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    if trend == "Strong Uptrend":
        reasons.append(
            "Price is in a strong uptrend"
        )

    elif trend == "Uptrend":
        reasons.append(
            "Price is above major moving averages"
        )

    elif trend in [
        "Downtrend",
        "Strong Downtrend"
    ]:
        reasons.append(
            "Price trend is weak"
        )

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if momentum == "Strong Positive":
        reasons.append(
            "Strong positive momentum"
        )

    elif momentum == "Positive":
        reasons.append(
            "Positive momentum"
        )

    elif momentum in [
        "Negative",
        "Strong Negative"
    ]:
        reasons.append(
            "Negative momentum"
        )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if not pd.isna(rsi):

        if 55 <= rsi <= 68:
            reasons.append(
                "RSI supports bullish momentum"
            )

        elif rsi < 35:
            reasons.append(
                "RSI indicates oversold conditions"
            )

        elif rsi > 72:
            reasons.append(
                "RSI is highly extended"
            )

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    if not pd.isna(volume_ratio):

        if volume_ratio >= 2:
            reasons.append(
                "Volume is more than 2x average"
            )

        elif volume_ratio >= 1.5:
            reasons.append(
                "Strong volume confirmation"
            )

        elif volume_ratio >= 1.25:
            reasons.append(
                "Above-average volume"
            )

    # --------------------------------------------------------
    # 200 DMA
    # --------------------------------------------------------

    if above_200dma:
        reasons.append(
            "Price is above 200 DMA"
        )
    else:
        reasons.append(
            "Price is below 200 DMA"
        )

    # --------------------------------------------------------
    # 52W High
    # --------------------------------------------------------

    if not pd.isna(distance_high):

        if -2 <= distance_high <= 0:
            reasons.append(
                "Very close to 52-week high"
            )

        elif -5 <= distance_high < -2:
            reasons.append(
                "Within 5% of 52-week high"
            )

    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    if breakout == "Confirmed Breakout":
        reasons.append(
            "Price broke previous resistance"
        )

    elif breakout == "Near Breakout":
        reasons.append(
            "Price is near resistance"
        )

    # --------------------------------------------------------
    # 200 DMA Recovery
    # --------------------------------------------------------

    if not pd.isna(distance_200):

        if -3 <= distance_200 <= 3:
            reasons.append(
                "Price is near 200 DMA"
            )

    return " | ".join(
        reasons
    )


# ============================================================
# RISK / REWARD
# ============================================================

def calculate_risk_reward(row):
    """
    Estimate basic risk/reward using support
    and resistance.

    This is NOT an execution signal.
    """

    price = row.get(
        "price",
        np.nan
    )

    support = row.get(
        "support",
        np.nan
    )

    resistance = row.get(
        "resistance",
        np.nan
    )

    if (
        pd.isna(price)
        or pd.isna(support)
        or pd.isna(resistance)
    ):
        return np.nan

    risk = price - support

    reward = resistance - price

    if risk <= 0:
        return np.nan

    return round(
        reward / risk,
        2
    )


# ============================================================
# PROCESS ONE ROW
# ============================================================

def rank_stock(row):
    """
    Add all ranking and setup fields
    to one stock.
    """

    row = row.copy()

    technical = calculate_technical_score(
        row
    )

    setup = identify_setup(
        row
    )

    reasons = generate_reasons(
        row
    )

    risk_reward = calculate_risk_reward(
        row
    )

    row["technical_score"] = technical

    row["setup"] = setup

    row["setup_reasons"] = reasons

    row["risk_reward"] = risk_reward

    return row


# ============================================================
# RANK COMPLETE DATAFRAME
# ============================================================

def rank_stocks(df):
    """
    Rank all scanned stocks.

    Higher technical score = higher rank.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    df = df.apply(
        rank_stock,
        axis=1
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    df = df.sort_values(
        by="technical_score",
        ascending=False
    )

    df["technical_rank"] = (
        range(
            1,
            len(df) + 1
        )
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# SETUP SUMMARY
# ============================================================

def create_setup_summary(df):
    """
    Create counts by setup.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby(
            "setup"
        )
        .size()
        .reset_index(
            name="stock_count"
        )
        .sort_values(
            "stock_count",
            ascending=False
        )
    )

    return summary.reset_index(
        drop=True
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "RANKING & SETUP ENGINE"
    )

    print("=" * 60)

    print()

    print(
        "Ranking Engine loaded successfully."
    )

    print()

    print(
        "Technical scoring:"
    )

    print(
        "Trend       : 20 points"
    )

    print(
        "Momentum    : 15 points"
    )

    print(
        "RSI         : 15 points"
    )

    print(
        "Volume      : 15 points"
    )

    print(
        "Position    : 15 points"
    )

    print(
        "Breakout    : 20 points"
    )

    print()

    print(
        "Total       : 100 points"
    )

    print()

    print(
        "Setup types:"
    )

    print(
        "- Strong Breakout Watch"
    )

    print(
        "- 52W High Watch"
    )

    print(
        "- Momentum Watch"
    )

    print(
        "- 200 DMA Recovery Watch"
    )

    print(
        "- Breakout Confirmation Required"
    )

    print(
        "- Pre-Breakout Watch"
    )

    print(
        "- Weak / Avoid"
    )

    print(
        "- Neutral Watch"
    )

    print()

    print("=" * 60)
