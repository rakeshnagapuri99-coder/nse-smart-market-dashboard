"""
===========================================================
NSE SMART MARKET DASHBOARD
TECHNICAL ENGINE V3
===========================================================

Purpose
-------
Calculates technical indicators for NSE equity stocks.

Indicators
----------
    Previous Close
    Daily Return %
    SMA 20
    SMA 50
    SMA 100
    SMA 200
    EMA 9
    EMA 20
    EMA 50
    RSI 14
    ATR 14
    ATR %
    Volume
    Average Volume 20
    Volume Ratio
    52 Week High
    52 Week Low
    Distance from 52 Week High
    Distance from 52 Week Low
    Distance from 200 DMA
    Above 200 DMA
    Support
    Resistance
    Trend
    Momentum
    Breakout Status
    Technical Score

Important
---------
This module is defensive against:

    yfinance MultiIndex columns
    lowercase columns
    Yahoo Finance column naming
    missing OHLCV data
    malformed symbols
    empty DataFrames

===========================================================
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


# =========================================================
# CONSTANTS
# =========================================================

MIN_DATA_POINTS = 220

SMA_SHORT = 20
SMA_MEDIUM = 50
SMA_LONG = 100
SMA_200 = 200

EMA_FAST = 9
EMA_SHORT = 20
EMA_MEDIUM = 50

RSI_PERIOD = 14
ATR_PERIOD = 14

VOLUME_PERIOD = 20
HIGH_LOW_PERIOD = 252

SUPPORT_PERIOD = 20
RESISTANCE_PERIOD = 20


# =========================================================
# GENERAL HELPERS
# =========================================================

def safe_float(
    value: Any,
    default: float | None = None,
) -> float | None:

    if value is None:
        return default

    try:

        if pd.isna(value):
            return default

    except (
        TypeError,
        ValueError,
    ):
        pass

    try:

        number = float(value)

        if not np.isfinite(number):
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


# =========================================================
# COLUMN NORMALIZATION
# =========================================================

def _normalise_column_name(
    column: Any,
) -> str:

    text = str(
        column
    ).strip()

    text = text.replace(
        "_",
        " ",
    )

    text = " ".join(
        text.split()
    )

    return text.lower()


def normalize_ohlcv_columns(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert yfinance / Yahoo columns into:

        Open
        High
        Low
        Close
        Adj Close
        Volume

    Handles MultiIndex DataFrames.
    """

    if data is None:

        return pd.DataFrame()

    if not isinstance(
        data,
        pd.DataFrame,
    ):

        return pd.DataFrame()

    if data.empty:

        return pd.DataFrame()

    df = data.copy()

    # -----------------------------------------------------
    # Handle MultiIndex columns.
    #
    # Examples:
    #
    # ('Close', 'RELIANCE.NS')
    # ('RELIANCE.NS', 'Close')
    #
    # We search every level for the OHLCV field.
    # -----------------------------------------------------

    if isinstance(
        df.columns,
        pd.MultiIndex,
    ):

        new_columns = []

        for column in df.columns:

            selected = None

            for part in column:

                name = _normalise_column_name(
                    part
                )

                if name in {
                    "open",
                    "high",
                    "low",
                    "close",
                    "adj close",
                    "volume",
                }:

                    selected = name
                    break

            if selected is None:

                selected = "_".join(
                    str(part)
                    for part in column
                )

            new_columns.append(
                selected
            )

        df.columns = new_columns

    else:

        df.columns = [
            _normalise_column_name(
                column
            )
            for column
            in df.columns
        ]

    # -----------------------------------------------------
    # Rename standard columns.
    # -----------------------------------------------------

    rename_map = {}

    for column in df.columns:

        name = _normalise_column_name(
            column
        )

        if name == "open":
            rename_map[column] = "Open"

        elif name == "high":
            rename_map[column] = "High"

        elif name == "low":
            rename_map[column] = "Low"

        elif name == "close":
            rename_map[column] = "Close"

        elif name == "adj close":
            rename_map[column] = "Adj Close"

        elif name == "volume":
            rename_map[column] = "Volume"

    df = df.rename(
        columns=rename_map
    )

    # -----------------------------------------------------
    # If duplicate columns exist after flattening,
    # keep the first usable one.
    # -----------------------------------------------------

    for column in [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]:

        matching = [
            c
            for c in df.columns
            if c == column
        ]

        if len(matching) > 1:

            df[column] = (
                df[matching]
                .bfill(axis=1)
                .iloc[:, 0]
            )

    # -----------------------------------------------------
    # Numeric conversion.
    # -----------------------------------------------------

    for column in [
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -----------------------------------------------------
    # Sort and remove duplicate dates.
    # -----------------------------------------------------

    try:

        df = df.sort_index()

        if df.index.duplicated().any():

            df = df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]

    except Exception:
        pass

    return df


# =========================================================
# RSI
# =========================================================

def calculate_rsi(
    series: pd.Series,
    period: int = RSI_PERIOD,
) -> pd.Series:

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    average_gain = (
        gain
        .ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        )
        .mean()
    )

    average_loss = (
        loss
        .ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period,
        )
        .mean()
    )

    rs = (
        average_gain /
        average_loss.replace(
            0,
            np.nan,
        )
    )

    rsi = (
        100 -
        (
            100 /
            (
                1 + rs
            )
        )
    )

    return rsi


# =========================================================
# ATR
# =========================================================

def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = ATR_PERIOD,
) -> pd.Series:

    previous_close = (
        close.shift(1)
    )

    range_1 = (
        high -
        low
    )

    range_2 = (
        high -
        previous_close
    ).abs()

    range_3 = (
        low -
        previous_close
    ).abs()

    true_range = pd.concat(
        [
            range_1,
            range_2,
            range_3,
        ],
        axis=1,
    ).max(
        axis=1
    )

    atr = (
        true_range
        .rolling(
            period
        )
        .mean()
    )

    return atr


# =========================================================
# TECHNICAL SCORE
# =========================================================

def calculate_trend_score(
    row: pd.Series,
) -> float:

    price = safe_float(
        row.get("Close")
    )

    sma20 = safe_float(
        row.get("SMA_20")
    )

    sma50 = safe_float(
        row.get("SMA_50")
    )

    sma200 = safe_float(
        row.get("SMA_200")
    )

    if (
        price is None
        or sma20 is None
        or sma50 is None
        or sma200 is None
    ):

        return 50.0

    if (
        price > sma20
        and sma20 > sma50
        and sma50 > sma200
    ):

        return 100.0

    if (
        price > sma20
        and price > sma50
        and price > sma200
    ):

        return 90.0

    if (
        price > sma200
        and price > sma20
    ):

        return 80.0

    if price > sma200:

        return 70.0

    if (
        price < sma200
        and price < sma50
        and price < sma20
    ):

        return 10.0

    if price < sma200:

        return 30.0

    return 50.0


def calculate_momentum_score(
    row: pd.Series,
) -> float:

    price = safe_float(
        row.get("Close")
    )

    sma20 = safe_float(
        row.get("SMA_20")
    )

    sma50 = safe_float(
        row.get("SMA_50")
    )

    rsi = safe_float(
        row.get("RSI_14")
    )

    if (
        price is None
        or sma20 is None
        or sma50 is None
    ):

        return 50.0

    if (
        price > sma20 > sma50
        and rsi is not None
        and rsi >= 60
    ):

        return 100.0

    if (
        price > sma20
        and rsi is not None
        and rsi >= 50
    ):

        return 80.0

    if (
        price > sma50
        and rsi is not None
        and rsi >= 45
    ):

        return 65.0

    if (
        rsi is not None
        and rsi < 35
    ):

        return 15.0

    if (
        rsi is not None
        and rsi < 45
    ):

        return 30.0

    return 50.0


def calculate_rsi_score(
    row: pd.Series,
) -> float:

    rsi = safe_float(
        row.get("RSI_14")
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
    row: pd.Series,
) -> float:

    ratio = safe_float(
        row.get("Volume_Ratio")
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
    row: pd.Series,
) -> float:

    price = safe_float(
        row.get("Close")
    )

    sma200 = safe_float(
        row.get("SMA_200")
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
    row: pd.Series,
) -> float:

    breakout = str(
        row.get(
            "Breakout_Status",
            "",
        )
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

    price = safe_float(
        row.get("Close")
    )

    resistance = safe_float(
        row.get("Resistance")
    )

    volume_ratio = safe_float(
        row.get("Volume_Ratio")
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

            if (
                volume_ratio is not None
                and volume_ratio >= 1.2
            ):

                return 90.0

            return 75.0

        if distance >= -3:

            return 60.0

        if distance >= -5:

            return 50.0

    return 30.0


def calculate_technical_score(
    row: pd.Series,
) -> float:

    trend = calculate_trend_score(
        row
    )

    momentum = calculate_momentum_score(
        row
    )

    rsi = calculate_rsi_score(
        row
    )

    volume = calculate_volume_score(
        row
    )

    position = calculate_position_score(
        row
    )

    breakout = calculate_breakout_score(
        row
    )

    score = (
        trend * 0.20
        +
        momentum * 0.15
        +
        rsi * 0.15
        +
        volume * 0.15
        +
        position * 0.15
        +
        breakout * 0.20
    )

    return round(
        clamp(score),
        2,
    )


# =========================================================
# TREND LABEL
# =========================================================

def determine_trend(
    row: pd.Series,
) -> str:

    score = calculate_trend_score(
        row
    )

    if score >= 90:
        return "Strong Uptrend"

    if score >= 75:
        return "Uptrend"

    if score >= 60:
        return "Positive"

    if score <= 20:
        return "Downtrend"

    if score <= 40:
        return "Weak"

    return "Sideways"


# =========================================================
# MOMENTUM LABEL
# =========================================================

def determine_momentum(
    row: pd.Series,
) -> str:

    score = calculate_momentum_score(
        row
    )

    if score >= 90:
        return "Strong Positive"

    if score >= 70:
        return "Positive"

    if score <= 25:
        return "Strong Negative"

    if score <= 40:
        return "Negative"

    return "Neutral"


# =========================================================
# BREAKOUT STATUS
# =========================================================

def determine_breakout_status(
    row: pd.Series,
) -> str:

    price = safe_float(
        row.get("Close")
    )

    resistance = safe_float(
        row.get("Resistance")
    )

    volume_ratio = safe_float(
        row.get("Volume_Ratio")
    )

    if (
        price is None
        or resistance is None
        or resistance <= 0
    ):

        return "No Breakout"

    distance = (
        (
            price -
            resistance
        )
        /
        resistance
    ) * 100.0

    if distance >= 0:

        if (
            volume_ratio is None
            or volume_ratio >= 1.2
        ):

            return "Confirmed Breakout"

        return "Breakout Confirmation Required"

    if distance >= -3:

        return "Near Breakout"

    if distance >= -5:

        return "Pre-Breakout"

    return "No Breakout"


# =========================================================
# PREPARE DATA
# =========================================================

def prepare_data(
    data: pd.DataFrame,
) -> pd.DataFrame:

    df = normalize_ohlcv_columns(
        data
    )

    if df.empty:

        return pd.DataFrame()

    required = [
        "High",
        "Low",
        "Close",
    ]

    missing = [
        column
        for column
        in required
        if column not in df.columns
    ]

    if missing:

        print(
            "Technical engine skipped "
            f"data because columns are missing: "
            f"{missing}"
        )

        print(
            "Available columns: "
            f"{list(df.columns)}"
        )

        return pd.DataFrame()

    df = df.dropna(
        subset=[
            "Close",
        ]
    )

    if df.empty:

        return pd.DataFrame()

    # -----------------------------------------------------
    # Basic fields
    # -----------------------------------------------------

    df["Previous_Close"] = (
        df["Close"]
        .shift(1)
    )

    df["Daily_Return_Pct"] = (
        (
            df["Close"] -
            df["Previous_Close"]
        )
        /
        df["Previous_Close"]
        .replace(
            0,
            np.nan,
        )
    ) * 100.0

    # -----------------------------------------------------
    # Moving averages
    # -----------------------------------------------------

    df["SMA_20"] = (
        df["Close"]
        .rolling(
            SMA_SHORT
        )
        .mean()
    )

    df["SMA_50"] = (
        df["Close"]
        .rolling(
            SMA_MEDIUM
        )
        .mean()
    )

    df["SMA_100"] = (
        df["Close"]
        .rolling(
            SMA_LONG
        )
        .mean()
    )

    df["SMA_200"] = (
        df["Close"]
        .rolling(
            SMA_200
        )
        .mean()
    )

    # -----------------------------------------------------
    # EMA
    # -----------------------------------------------------

    df["EMA_9"] = (
        df["Close"]
        .ewm(
            span=EMA_FAST,
            adjust=False,
        )
        .mean()
    )

    df["EMA_20"] = (
        df["Close"]
        .ewm(
            span=EMA_SHORT,
            adjust=False,
        )
        .mean()
    )

    df["EMA_50"] = (
        df["Close"]
        .ewm(
            span=EMA_MEDIUM,
            adjust=False,
        )
        .mean()
    )

    # -----------------------------------------------------
    # RSI
    # -----------------------------------------------------

    df["RSI_14"] = calculate_rsi(
        df["Close"],
        RSI_PERIOD,
    )

    # -----------------------------------------------------
    # ATR
    # -----------------------------------------------------

    df["ATR_14"] = calculate_atr(
        df["High"],
        df["Low"],
        df["Close"],
        ATR_PERIOD,
    )

    df["ATR_Pct"] = (
        df["ATR_14"] /
        df["Close"].replace(
            0,
            np.nan,
        )
    ) * 100.0

    # -----------------------------------------------------
    # Volume
    # -----------------------------------------------------

    if "Volume" in df.columns:

        df["Average_Volume_20"] = (
            df["Volume"]
            .rolling(
                VOLUME_PERIOD
            )
            .mean()
        )

        df["Volume_Ratio"] = (
            df["Volume"] /
            df[
                "Average_Volume_20"
            ].replace(
                0,
                np.nan,
            )
        )

    else:

        df["Volume"] = np.nan

        df["Average_Volume_20"] = np.nan

        df["Volume_Ratio"] = np.nan

    # -----------------------------------------------------
    # 52 week high / low
    # -----------------------------------------------------

    df["52W_High"] = (
        df["High"]
        .rolling(
            HIGH_LOW_PERIOD,
            min_periods=20,
        )
        .max()
    )

    df["52W_Low"] = (
        df["Low"]
        .rolling(
            HIGH_LOW_PERIOD,
            min_periods=20,
        )
        .min()
    )

    df["Distance_52W_High_Pct"] = (
        (
            df["Close"] -
            df["52W_High"]
        )
        /
        df["52W_High"]
        .replace(
            0,
            np.nan,
        )
    ) * 100.0

    df["Distance_52W_Low_Pct"] = (
        (
            df["Close"] -
            df["52W_Low"]
        )
        /
        df["52W_Low"]
        .replace(
            0,
            np.nan,
        )
    ) * 100.0

    # -----------------------------------------------------
    # 200 DMA distance
    # -----------------------------------------------------

    df["Distance_200DMA_Pct"] = (
        (
            df["Close"] -
            df["SMA_200"]
        )
        /
        df["SMA_200"]
        .replace(
            0,
            np.nan,
        )
    ) * 100.0

    df["Above_200DMA"] = (
        df["Close"] >
        df["SMA_200"]
    )

    # -----------------------------------------------------
    # Support / resistance
    #
    # Shift by one day so today's price does not become
    # today's own support/resistance.
    # -----------------------------------------------------

    df["Support"] = (
        df["Low"]
        .shift(1)
        .rolling(
            SUPPORT_PERIOD
        )
        .min()
    )

    df["Resistance"] = (
        df["High"]
        .shift(1)
        .rolling(
            RESISTANCE_PERIOD
        )
        .max()
    )

    # -----------------------------------------------------
    # Technical labels
    # -----------------------------------------------------

    df["Trend"] = df.apply(
        determine_trend,
        axis=1,
    )

    df["Momentum"] = df.apply(
        determine_momentum,
        axis=1,
    )

    df["Breakout_Status"] = df.apply(
        determine_breakout_status,
        axis=1,
    )

    # -----------------------------------------------------
    # Technical score
    # -----------------------------------------------------

    df["Technical_Score"] = df.apply(
        calculate_technical_score,
        axis=1,
    )

    # -----------------------------------------------------
    # Technical rank
    # -----------------------------------------------------

    df["Technical_Rank"] = (
        df["Technical_Score"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    return df


# =========================================================
# LATEST ROW
# =========================================================

def get_latest_analysis(
    data: pd.DataFrame,
) -> dict:

    df = prepare_data(
        data
    )

    if df.empty:

        return {}

    latest = df.iloc[-1]

    return {
        "price":
            safe_float(
                latest.get(
                    "Close"
                )
            ),

        "previous_close":
            safe_float(
                latest.get(
                    "Previous_Close"
                )
            ),

        "daily_return_pct":
            safe_float(
                latest.get(
                    "Daily_Return_Pct"
                )
            ),

        "sma20":
            safe_float(
                latest.get(
                    "SMA_20"
                )
            ),

        "sma50":
            safe_float(
                latest.get(
                    "SMA_50"
                )
            ),

        "sma100":
            safe_float(
                latest.get(
                    "SMA_100"
                )
            ),

        "sma200":
            safe_float(
                latest.get(
                    "SMA_200"
                )
            ),

        "ema9":
            safe_float(
                latest.get(
                    "EMA_9"
                )
            ),

        "ema20":
            safe_float(
                latest.get(
                    "EMA_20"
                )
            ),

        "ema50":
            safe_float(
                latest.get(
                    "EMA_50"
                )
            ),

        "rsi14":
            safe_float(
                latest.get(
                    "RSI_14"
                )
            ),

        "atr14":
            safe_float(
                latest.get(
                    "ATR_14"
                )
            ),

        "atr_percent":
            safe_float(
                latest.get(
                    "ATR_Pct"
                )
            ),

        "volume":
            safe_float(
                latest.get(
                    "Volume"
                )
            ),

        "average_volume_20":
            safe_float(
                latest.get(
                    "Average_Volume_20"
                )
            ),

        "volume_ratio":
            safe_float(
                latest.get(
                    "Volume_Ratio"
                )
            ),

        "52w_high":
            safe_float(
                latest.get(
                    "52W_High"
                )
            ),

        "52w_low":
            safe_float(
                latest.get(
                    "52W_Low"
                )
            ),

        "distance_from_52w_high_pct":
            safe_float(
                latest.get(
                    "Distance_52W_High_Pct"
                )
            ),

        "distance_from_52w_low_pct":
            safe_float(
                latest.get(
                    "Distance_52W_Low_Pct"
                )
            ),

        "distance_from_200dma_pct":
            safe_float(
                latest.get(
                    "Distance_200DMA_Pct"
                )
            ),

        "above_200dma":
            bool(
                latest.get(
                    "Above_200DMA",
                    False,
                )
            ),

        "support":
            safe_float(
                latest.get(
                    "Support"
                )
            ),

        "resistance":
            safe_float(
                latest.get(
                    "Resistance"
                )
            ),

        "trend":
            latest.get(
                "Trend"
            ),

        "momentum":
            latest.get(
                "Momentum"
            ),

        "breakout_status":
            latest.get(
                "Breakout_Status"
            ),

        "technical_score":
            safe_float(
                latest.get(
                    "Technical_Score"
                )
            ),
    }


# =========================================================
# MAIN FUNCTION USED BY SCANNER.PY
# =========================================================

def calculate_technical_indicators(
    data: pd.DataFrame,
    symbol: str | None = None,
) -> pd.DataFrame:
    """
    Main technical-engine entry point.

    Compatible with scanner.py calls such as:

        calculate_technical_indicators(data)

    or:

        calculate_technical_indicators(
            data,
            symbol,
        )
    """

    if data is None:

        return pd.DataFrame()

    if not isinstance(
        data,
        pd.DataFrame,
    ):

        return pd.DataFrame()

    if data.empty:

        return pd.DataFrame()

    try:

        df = prepare_data(
            data
        )

        if df.empty:

            return pd.DataFrame()

        # -------------------------------------------------
        # Add symbol if supplied.
        # -------------------------------------------------

        if symbol is not None:

            df["Symbol"] = str(
                symbol
            )

        # -------------------------------------------------
        # Compatibility aliases.
        #
        # Ranking engine expects several possible names.
        # Keeping these aliases makes the pipeline robust.
        # -------------------------------------------------

        df["Close"] = df[
            "Close"
        ]

        df["Price"] = df[
            "Close"
        ]

        df["Previous_Close"] = df[
            "Previous_Close"
        ]

        df["Daily_Return_Pct"] = df[
            "Daily_Return_Pct"
        ]

        df["SMA20"] = df[
            "SMA_20"
        ]

        df["SMA50"] = df[
            "SMA_50"
        ]

        df["SMA100"] = df[
            "SMA_100"
        ]

        df["SMA200"] = df[
            "SMA_200"
        ]

        df["EMA9"] = df[
            "EMA_9"
        ]

        df["EMA20"] = df[
            "EMA_20"
        ]

        df["EMA50"] = df[
            "EMA_50"
        ]

        df["RSI14"] = df[
            "RSI_14"
        ]

        df["ATR14"] = df[
            "ATR_14"
        ]

        df["ATR_Percent"] = df[
            "ATR_Pct"
        ]

        df["AverageVolume20"] = df[
            "Average_Volume_20"
        ]

        df["VolumeRatio"] = df[
            "Volume_Ratio"
        ]

        df["52w_high"] = df[
            "52W_High"
        ]

        df["52w_low"] = df[
            "52W_Low"
        ]

        df["distance_from_52w_high_pct"] = (
            df[
                "Distance_52W_High_Pct"
            ]
        )

        df["distance_from_52w_low_pct"] = (
            df[
                "Distance_52W_Low_Pct"
            ]
        )

        df["distance_from_200dma_pct"] = (
            df[
                "Distance_200DMA_Pct"
            ]
        )

        df["above_200dma"] = (
            df[
                "Above_200DMA"
            ]
        )

        df["support"] = df[
            "Support"
        ]

        df["resistance"] = df[
            "Resistance"
        ]

        df["trend"] = df[
            "Trend"
        ]

        df["momentum"] = df[
            "Momentum"
        ]

        df["breakout_status"] = df[
            "Breakout_Status"
        ]

        df["technical_score"] = df[
            "Technical_Score"
        ]

        df["technical_rank"] = df[
            "Technical_Rank"
        ]

        # -------------------------------------------------
        # Minimum data check.
        #
        # Do not reject the whole DataFrame here because
        # scanner.py may handle minimum-history filtering.
        # -------------------------------------------------

        return df

    except Exception as error:

        print(
            "Technical engine error"
            + (
                f" for {symbol}"
                if symbol
                else ""
            )
            + f": {error}"
        )

        return pd.DataFrame()


# =========================================================
# SCRIPT TEST
# =========================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "TECHNICAL ENGINE TEST"
    )

    print(
        "=" * 60
    )

    print(
        "Module loaded successfully."
    )

    print(
        "Yahoo Finance MultiIndex handling: ENABLED"
    )

    print(
        "OHLCV normalization: ENABLED"
    )

    print(
        "SMA / EMA / RSI / ATR: ENABLED"
    )

    print(
        "52W High / Low: ENABLED"
    )

    print(
        "200 DMA: ENABLED"
    )

    print(
        "Support / Resistance: ENABLED"
    )

    print(
        "Technical Score: ENABLED"
    )
