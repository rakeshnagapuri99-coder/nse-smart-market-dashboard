import pandas as pd
import numpy as np


# ============================================================
# NSE SMART MARKET DASHBOARD
# RANKING ENGINE — PRODUCTION V2
# ============================================================


# ============================================================
# TECHNICAL SCORING
# ============================================================

def calculate_trend_score(trend):

    scores = {
        "Strong Uptrend": 20,
        "Uptrend": 16,
        "Sideways": 8,
        "Downtrend": 3,
        "Strong Downtrend": 0
    }

    return scores.get(trend, 5)


def calculate_momentum_score(momentum):

    scores = {
        "Strong Positive": 15,
        "Positive": 11,
        "Neutral": 7,
        "Negative": 3,
        "Strong Negative": 0
    }

    return scores.get(momentum, 4)


def calculate_rsi_score(rsi):

    if pd.isna(rsi):
        return 5

    if 55 <= rsi <= 68:
        return 15

    if 50 <= rsi < 55:
        return 12

    if 68 < rsi <= 72:
        return 11

    if 45 <= rsi < 50:
        return 8

    if 40 <= rsi < 45:
        return 5

    if rsi > 72:
        return 7

    return 2


def calculate_volume_score(volume_ratio):

    if pd.isna(volume_ratio):
        return 5

    if volume_ratio >= 2:
        return 15

    if volume_ratio >= 1.5:
        return 13

    if volume_ratio >= 1.25:
        return 10

    if volume_ratio >= 1:
        return 7

    if volume_ratio >= 0.75:
        return 4

    return 1


def calculate_position_score(row):

    score = 0

    price = row.get("price", np.nan)

    sma200 = row.get("sma200", np.nan)

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    if (
        not pd.isna(price)
        and not pd.isna(sma200)
        and price > sma200
    ):
        score += 8

    if not pd.isna(distance_high):

        if distance_high >= -3:
            score += 7

        elif distance_high >= -7:
            score += 5

        elif distance_high >= -12:
            score += 3

    return score


def calculate_breakout_score(
    breakout_status
):

    scores = {

        "Confirmed Breakout": 20,

        "Breakout - Volume Confirmation Required": 14,

        "Near Breakout": 10,

        "No Breakout": 4
    }

    return scores.get(
        breakout_status,
        4
    )


# ============================================================
# TECHNICAL SCORE
# ============================================================

def calculate_technical_score(row):

    trend = calculate_trend_score(
        row.get("trend")
    )

    momentum = calculate_momentum_score(
        row.get("momentum")
    )

    rsi = calculate_rsi_score(
        row.get("rsi14", np.nan)
    )

    volume = calculate_volume_score(
        row.get("volume_ratio", np.nan)
    )

    position = calculate_position_score(
        row
    )

    breakout = calculate_breakout_score(
        row.get("breakout_status")
    )

    score = (
        trend
        + momentum
        + rsi
        + volume
        + position
        + breakout
    )

    return round(
        max(0, min(100, score)),
        2
    )


# ============================================================
# SECTOR CONTEXT
# ============================================================

def calculate_sector_context(
    sector_classification
):

    scores = {

        "Leading": 100,

        "Strong": 80,

        "Neutral": 60,

        "Weak": 40,

        "Lagging": 20
    }

    return scores.get(
        sector_classification,
        50
    )


def calculate_sector_adjustment(
    sector_score
):

    if pd.isna(sector_score):
        return 0

    if sector_score >= 75:
        return 5

    if sector_score >= 60:
        return 3

    if sector_score >= 45:
        return 0

    if sector_score >= 30:
        return -3

    return -5


# ============================================================
# FUNDAMENTAL SCORE
# ============================================================

def calculate_fundamental_score(row):

    # --------------------------------------------------------
    # Fundamentals are not yet connected to the scanner.
    #
    # Therefore we DO NOT invent a score.
    #
    # Once fundamental_engine.py is connected, this function
    # will calculate the actual 40-point fundamental component.
    # --------------------------------------------------------

    required_fields = [
        "roe",
        "roce",
        "revenue_cagr",
        "profit_cagr",
        "debt_equity",
        "pe"
    ]

    available = 0

    for field in required_fields:

        value = row.get(
            field,
            np.nan
        )

        if (
            value is not None
            and not pd.isna(value)
        ):
            available += 1

    if available == 0:

        return np.nan

    # Temporary neutral score when partial
    # fundamental information exists.
    return 50.0


# ============================================================
# OVERALL RATING
# ============================================================

def calculate_overall_rating(
    technical_score,
    fundamental_score,
    sector_score
):

    # --------------------------------------------------------
    # Fundamentals unavailable
    # --------------------------------------------------------

    if pd.isna(fundamental_score):

        # Current production stage:
        # Technical score remains primary.
        #
        # Sector context contributes a small adjustment.

        adjustment = calculate_sector_adjustment(
            sector_score
        )

        return round(
            max(
                0,
                min(
                    100,
                    technical_score
                    + adjustment
                )
            ),
            2
        )

    # --------------------------------------------------------
    # Fundamentals available
    # --------------------------------------------------------

    base_score = (
        technical_score * 0.60
        + fundamental_score * 0.40
    )

    adjustment = calculate_sector_adjustment(
        sector_score
    )

    return round(
        max(
            0,
            min(
                100,
                base_score
                + adjustment
            )
        ),
        2
    )


# ============================================================
# SETUP CLASSIFICATION
# ============================================================

def determine_setup(row):

    trend = str(
        row.get(
            "trend",
            ""
        )
    )

    momentum = str(
        row.get(
            "momentum",
            ""
        )
    )

    breakout = str(
        row.get(
            "breakout_status",
            ""
        )
    )

    distance_200 = row.get(
        "distance_from_200dma_pct",
        np.nan
    )

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    technical_score = row.get(
        "technical_score",
        0
    )


    # --------------------------------------------------------
    # Strong confirmed breakout
    # --------------------------------------------------------

    if (
        breakout == "Confirmed Breakout"
        and technical_score >= 65
    ):

        return "Strong Breakout Watch"


    # --------------------------------------------------------
    # 52 Week High
    # --------------------------------------------------------

    if (
        not pd.isna(distance_high)
        and distance_high >= -3
        and technical_score >= 55
    ):

        return "52W High Watch"


    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    if (
        momentum == "Strong Positive"
        and technical_score >= 55
    ):

        return "Momentum Watch"


    # --------------------------------------------------------
    # 200 DMA recovery
    # --------------------------------------------------------

    if (
        not pd.isna(distance_200)
        and -5 <= distance_200 <= 5
        and momentum
        in [
            "Positive",
            "Strong Positive"
        ]
    ):

        return "200 DMA Recovery Watch"


    # --------------------------------------------------------
    # Breakout confirmation
    # --------------------------------------------------------

    if (
        breakout
        == "Breakout - Volume Confirmation Required"
    ):

        return "Breakout Confirmation Required"


    # --------------------------------------------------------
    # Pre-breakout
    # --------------------------------------------------------

    if (
        breakout == "Near Breakout"
        and technical_score >= 45
    ):

        return "Pre-Breakout Watch"


    # --------------------------------------------------------
    # Weak / avoid
    # --------------------------------------------------------

    if (
        technical_score < 30
        or trend
        in [
            "Strong Downtrend",
            "Strong Bearish",
            "Strong Downtrend"
        ]
    ):

        return "Weak / Avoid"


    return "Neutral Watch"


# ============================================================
# REASONS
# ============================================================

def generate_reasons(row):

    reasons = []

    trend = str(
        row.get(
            "trend",
            ""
        )
    )

    momentum = str(
        row.get(
            "momentum",
            ""
        )
    )

    breakout = str(
        row.get(
            "breakout_status",
            ""
        )
    )

    rsi = row.get(
        "rsi14",
        np.nan
    )

    volume_ratio = row.get(
        "volume_ratio",
        np.nan
    )

    distance_200 = row.get(
        "distance_from_200dma_pct",
        np.nan
    )

    distance_high = row.get(
        "distance_from_52w_high_pct",
        np.nan
    )

    # Trend
    if trend in [
        "Strong Uptrend",
        "Strong Bullish"
    ]:

        reasons.append(
            "Strong price trend"
        )

    elif trend in [
        "Uptrend",
        "Bullish"
    ]:

        reasons.append(
            "Positive price trend"
        )

    elif trend in [
        "Strong Downtrend",
        "Strong Bearish"
    ]:

        reasons.append(
            "Strong negative trend"
        )

    # Momentum
    if momentum == "Strong Positive":

        reasons.append(
            "Strong positive momentum"
        )

    elif momentum == "Positive":

        reasons.append(
            "Positive momentum"
        )

    elif momentum in [
        "Strong Negative"
    ]:

        reasons.append(
            "Strong negative momentum"
        )

    # RSI
    if not pd.isna(rsi):

        if 50 <= rsi <= 68:

            reasons.append(
                "RSI in constructive range"
            )

        elif rsi > 70:

            reasons.append(
                "RSI elevated"
            )

        elif rsi < 40:

            reasons.append(
                "RSI indicates weakness"
            )

    # Volume
    if not pd.isna(volume_ratio):

        if volume_ratio >= 1.5:

            reasons.append(
                "Strong volume participation"
            )

        elif volume_ratio >= 1.2:

            reasons.append(
                "Above-average volume"
            )

    # 200 DMA
    if not pd.isna(distance_200):

        if distance_200 > 0:

            reasons.append(
                "Price above 200 DMA"
            )

        elif -5 <= distance_200 <= 0:

            reasons.append(
                "Near 200 DMA"
            )

        else:

            reasons.append(
                "Price below 200 DMA"
            )

    # 52W high
    if not pd.isna(distance_high):

        if distance_high >= -3:

            reasons.append(
                "Near 52-week high"
            )

    # Breakout
    if breakout == "Confirmed Breakout":

        reasons.append(
            "Breakout with volume confirmation"
        )

    elif breakout == "Near Breakout":

        reasons.append(
            "Price approaching resistance"
        )

    return reasons


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def calculate_risk_reward(row):

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
# NORMALIZE STOCK DATA
# ============================================================

def normalize_stock_columns(df):

    if df.empty:
        return df

    df = df.copy()

    # --------------------------------------------------------
    # Technical engine uses capitalized field names.
    # Convert to dashboard-friendly lowercase names.
    # --------------------------------------------------------

    rename_map = {

        "Close": "price",

        "SMA20": "sma20",

        "SMA50": "sma50",

        "SMA100": "sma100",

        "SMA200": "sma200",

        "EMA9": "ema9",

        "EMA20": "ema20",

        "EMA50": "ema50",

        "RSI14": "rsi14",

        "ATR14": "atr14",

        "ATR_Percent": "atr_percent",

        "Volume": "volume",

        "Average_Volume_20":
            "average_volume_20",

        "Volume_Ratio":
            "volume_ratio",

        "52W_High":
            "52w_high",

        "52W_Low":
            "52w_low",

        "Distance_From_52W_High_Pct":
            "distance_from_52w_high_pct",

        "Distance_From_52W_Low_Pct":
            "distance_from_52w_low_pct",

        "Distance_From_200DMA_Pct":
            "distance_from_200dma_pct",

        "Support":
            "support",

        "Resistance":
            "resistance",

        "Trend":
            "trend",

        "Momentum":
            "momentum",

        "Breakout_Status":
            "breakout_status"
    }

    df = df.rename(
        columns=rename_map
    )

    return df


# ============================================================
# RANK STOCKS
# ============================================================

def rank_stocks(
    stock_data,
    sector_data=None
):

    if (
        stock_data is None
        or stock_data.empty
    ):

        return pd.DataFrame()


    df = normalize_stock_columns(
        stock_data
    )


    # --------------------------------------------------------
    # Sector mapping
    # --------------------------------------------------------

    if (
        sector_data is not None
        and not sector_data.empty
        and "sector" in df.columns
    ):

        sector_columns = [
            "sector",
            "sector_score",
            "classification"
        ]

        available_columns = [
            column
            for column in sector_columns
            if column in sector_data.columns
        ]

        if len(available_columns) >= 2:

            sector_lookup = (
                sector_data[
                    available_columns
                ]
                .drop_duplicates(
                    "sector"
                )
            )

            df = df.merge(
                sector_lookup,
                on="sector",
                how="left"
            )

    # --------------------------------------------------------
    # Technical score
    # --------------------------------------------------------

    df["technical_score"] = df.apply(
        calculate_technical_score,
        axis=1
    )

    # --------------------------------------------------------
    # Sector score
    # --------------------------------------------------------

    if "sector_score" not in df.columns:

        df["sector_score"] = np.nan

    # --------------------------------------------------------
    # Fundamental score
    # --------------------------------------------------------

    df["fundamental_score"] = df.apply(
        calculate_fundamental_score,
        axis=1
    )

    # --------------------------------------------------------
    # Overall rating
    # --------------------------------------------------------

    df["overall_rating"] = df.apply(
        lambda row:
            calculate_overall_rating(
                row["technical_score"],
                row["fundamental_score"],
                row["sector_score"]
            ),
        axis=1
    )

    # Dashboard compatibility
    df["rating"] = df[
        "overall_rating"
    ]

    df["total_score"] = df[
        "overall_rating"
    ]

    # --------------------------------------------------------
    # Setup
    # --------------------------------------------------------

    df["setup"] = df.apply(
        determine_setup,
        axis=1
    )

    # --------------------------------------------------------
    # Reasons
    # --------------------------------------------------------

    df["reasons_list"] = df.apply(
        generate_reasons,
        axis=1
    )

    df["reasons"] = df[
        "reasons_list"
    ].apply(
        lambda x:
            " • ".join(x)
    )

    # --------------------------------------------------------
    # Risk / reward
    # --------------------------------------------------------

    df["risk_reward"] = df.apply(
        calculate_risk_reward,
        axis=1
    )

    # --------------------------------------------------------
    # Fundamental status
    # --------------------------------------------------------

    df["fundamental_status"] = np.where(
        df["fundamental_score"].isna(),
        "Data unavailable",
        "Available"
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "overall_rating",
            "technical_score"
        ],
        ascending=False
    ).reset_index(
        drop=True
    )

    df["technical_rank"] = (
        df.index + 1
    )

    df["rank"] = (
        df.index + 1
    )

    return df


# ============================================================
# SETUP SUMMARY
# ============================================================

def create_setup_summary(
    ranked
):

    if (
        ranked is None
        or ranked.empty
    ):

        return pd.DataFrame()


    summary = (
        ranked
        .groupby(
            "setup"
        )
        .agg(
            stocks=(
                "symbol",
                "count"
            ),
            average_rating=(
                "overall_rating",
                "mean"
            )
        )
        .reset_index()
    )


    summary[
        "average_rating"
    ] = summary[
        "average_rating"
    ].round(2)


    return summary.sort_values(
        "average_rating",
        ascending=False
    ).reset_index(
        drop=True
    )


# ============================================================
# WATCHLIST CREATION
# ============================================================

def create_watchlists(
    ranked
):

    if (
        ranked is None
        or ranked.empty
    ):

        return {}


    watchlists = {}


    # --------------------------------------------------------
    # Next Day
    # --------------------------------------------------------

    watchlists[
        "next_day"
    ] = ranked[
        ~ranked["setup"].isin(
            ["Weak / Avoid"]
        )
    ].copy()


    # --------------------------------------------------------
    # Swing
    # --------------------------------------------------------

    watchlists[
        "swing"
    ] = ranked[
        ranked["trend"].isin(
            [
                "Strong Uptrend",
                "Uptrend",
                "Strong Bullish",
                "Bullish"
            ]
        )
    ].copy()


    # --------------------------------------------------------
    # 52 Week High
    # --------------------------------------------------------

    watchlists[
        "52w_high"
    ] = ranked[
        ranked[
            "distance_from_52w_high_pct"
        ] >= -5
    ].copy()


    # --------------------------------------------------------
    # 200 DMA Recovery
    # --------------------------------------------------------

    distance = pd.to_numeric(
        ranked[
            "distance_from_200dma_pct"
        ],
        errors="coerce"
    )

    watchlists[
        "dma_recovery"
    ] = ranked[
        distance.between(
            -5,
            5
        )
    ].copy()


    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    watchlists[
        "momentum"
    ] = ranked[
        ranked["momentum"].isin(
            [
                "Positive",
                "Strong Positive"
            ]
        )
    ].copy()


    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    watchlists[
        "breakout"
    ] = ranked[
        ranked["breakout_status"].isin(
            [
                "Confirmed Breakout",
                "Breakout - Volume Confirmation Required",
                "Near Breakout"
            ]
        )
    ].copy()


    # --------------------------------------------------------
    # Intraday
    #
    # This is only an EOD candidate list for now.
    # True intraday/VWAP analysis will be added when
    # genuine intraday data is available.
    # --------------------------------------------------------

    volume = pd.to_numeric(
        ranked[
            "volume_ratio"
        ],
        errors="coerce"
    )

    watchlists[
        "intraday"
    ] = ranked[
        volume >= 1.2
    ].copy()


    # --------------------------------------------------------
    # Long Term
    # --------------------------------------------------------

    watchlists[
        "long_term"
    ] = ranked[
        distance > 0
    ].copy()


    # --------------------------------------------------------
    # Options
    #
    # Underlying candidates only at this stage.
    # Option-chain analysis will be connected later.
    # --------------------------------------------------------

    watchlists[
        "options"
    ] = ranked[
        volume >= 1.2
    ].copy()


    return watchlists
