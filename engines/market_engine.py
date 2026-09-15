"""
===========================================================
NSE SMART MARKET DASHBOARD
MARKET ENGINE V3
===========================================================

Purpose
-------
Builds market-level decision intelligence using:

    NIFTY 50
    BANK NIFTY
    INDIA VIX

Includes:

    Current / latest available price
    Previous close
    Daily return
    SMA 20 / 50 / 100 / 200
    EMA 20 / 50
    RSI 14
    ATR 14
    Volume ratio
    Support
    Resistance
    Pivot
    Trend
    Momentum
    Index score
    Market score
    Market regime
    Trading environments
    Market scenario
    Bullish / bearish triggers

Important
---------
This engine does not manufacture live prices.

When NSE official current-session data is available,
it is preferred for the current index snapshot.

Historical indicators are calculated from Yahoo Finance
historical data.

If current-session data is unavailable, the latest
available historical close is used and labelled accordingly.
===========================================================
"""

from __future__ import annotations

import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import yfinance as yf


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# CONSTANTS
# =========================================================

NIFTY_SYMBOL = "^NSEI"
BANK_NIFTY_SYMBOL = "^NSEBANK"
VIX_SYMBOL = "^INDIAVIX"

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept":
        "application/json,text/plain,*/*",
    "Accept-Language":
        "en-US,en;q=0.9",
    "Referer":
        "https://www.nseindia.com/",
    "Connection":
        "keep-alive",
}


# =========================================================
# GENERIC HELPERS
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

        if not math.isfinite(number):
            return default

        return number

    except (
        TypeError,
        ValueError,
    ):
        return default


def clean_number(
    value: Any,
) -> float | None:

    return safe_float(value)


def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:

    return max(
        low,
        min(
            high,
            value,
        ),
    )


def json_safe(
    value: Any,
) -> Any:

    if value is None:
        return None

    if isinstance(
        value,
        np.integer,
    ):
        return int(value)

    if isinstance(
        value,
        np.floating,
    ):

        if not np.isfinite(
            float(value)
        ):
            return None

        return float(value)

    if isinstance(
        value,
        np.bool_,
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
                json_safe(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):

        return [
            json_safe(item)
            for item in value
        ]

    try:

        if pd.isna(value):
            return None

    except (
        TypeError,
        ValueError,
    ):
        pass

    return value


# =========================================================
# TECHNICAL INDICATORS
# =========================================================

def calculate_rsi(
    close: pd.Series,
    period: int = 14,
) -> pd.Series:

    delta = close.diff()

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
            min_periods=period,
            adjust=False,
        )
        .mean()
    )

    average_loss = (
        loss
        .ewm(
            alpha=1 / period,
            min_periods=period,
            adjust=False,
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


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:

    previous_close = (
        close.shift(1)
    )

    tr1 = (
        high -
        low
    )

    tr2 = (
        high -
        previous_close
    ).abs()

    tr3 = (
        low -
        previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3,
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


def prepare_history(
    data: pd.DataFrame,
) -> pd.DataFrame:

    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()

    # Flatten yfinance MultiIndex columns.
    if isinstance(
        df.columns,
        pd.MultiIndex,
    ):

        flattened = []

        for column in df.columns:

            parts = [
                str(part)
                for part
                in column
                if str(part)
                not in {
                    "",
                    "None",
                }
            ]

            flattened.append(
                "_".join(parts)
            )

        df.columns = flattened

    rename_map = {}

    for column in df.columns:

        name = str(
            column
        ).strip().lower()

        if name == "open":
            rename_map[column] = "Open"

        elif name == "high":
            rename_map[column] = "High"

        elif name == "low":
            rename_map[column] = "Low"

        elif name == "close":
            rename_map[column] = "Close"

        elif name == "volume":
            rename_map[column] = "Volume"

    df = df.rename(
        columns=rename_map
    )

    required = [
        "High",
        "Low",
        "Close",
    ]

    if not all(
        column in df.columns
        for column in required
    ):
        return pd.DataFrame()

    for column in required:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if "Volume" in df.columns:

        df["Volume"] = pd.to_numeric(
            df["Volume"],
            errors="coerce",
        )

    df = df.dropna(
        subset=required
    )

    df = df.sort_index()

    return df


def add_indicators(
    data: pd.DataFrame,
) -> pd.DataFrame:

    df = prepare_history(
        data
    )

    if df.empty:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df["SMA20"] = (
        close
        .rolling(20)
        .mean()
    )

    df["SMA50"] = (
        close
        .rolling(50)
        .mean()
    )

    df["SMA100"] = (
        close
        .rolling(100)
        .mean()
    )

    df["SMA200"] = (
        close
        .rolling(200)
        .mean()
    )

    df["EMA20"] = (
        close
        .ewm(
            span=20,
            adjust=False,
        )
        .mean()
    )

    df["EMA50"] = (
        close
        .ewm(
            span=50,
            adjust=False,
        )
        .mean()
    )

    df["RSI14"] = calculate_rsi(
        close,
        14,
    )

    df["ATR14"] = calculate_atr(
        high,
        low,
        close,
        14,
    )

    if "Volume" in df.columns:

        df["AverageVolume20"] = (
            df["Volume"]
            .rolling(20)
            .mean()
        )

        df["VolumeRatio"] = (
            df["Volume"] /
            df[
                "AverageVolume20"
            ].replace(
                0,
                np.nan,
            )
        )

    else:

        df["AverageVolume20"] = np.nan
        df["VolumeRatio"] = np.nan

    return df


# =========================================================
# SUPPORT / RESISTANCE / PIVOT
# =========================================================

def calculate_levels(
    df: pd.DataFrame,
) -> dict:

    if df is None or df.empty:

        return {
            "support": None,
            "resistance": None,
            "pivot": None,
        }

    recent = df.tail(
        20
    )

    current = safe_float(
        df["Close"].iloc[-1]
    )

    if current is None:

        return {
            "support": None,
            "resistance": None,
            "pivot": None,
        }

    # Use prior-session / prior-period levels
    # to avoid treating today's close as its own
    # resistance.
    previous = df.iloc[
        :-1
    ].tail(
        20
    )

    if previous.empty:
        previous = recent

    support = safe_float(
        previous["Low"].min()
    )

    resistance = safe_float(
        previous["High"].max()
    )

    last_high = safe_float(
        df["High"].iloc[-1]
    )

    last_low = safe_float(
        df["Low"].iloc[-1]
    )

    previous_close = safe_float(
        df["Close"].iloc[-2]
        if len(df) >= 2
        else current
    )

    if (
        last_high is not None
        and last_low is not None
        and previous_close is not None
    ):

        pivot = (
            last_high +
            last_low +
            previous_close
        ) / 3.0

    else:

        pivot = (
            current
            if current
            else None
        )

    return {
        "support": support,
        "resistance": resistance,
        "pivot": pivot,
    }


# =========================================================
# TREND
# =========================================================

def determine_trend(
    row: pd.Series,
) -> tuple[str, float]:

    price = safe_float(
        row.get("Close")
    )

    sma20 = safe_float(
        row.get("SMA20")
    )

    sma50 = safe_float(
        row.get("SMA50")
    )

    sma100 = safe_float(
        row.get("SMA100")
    )

    sma200 = safe_float(
        row.get("SMA200")
    )

    if price is None:

        return (
            "Unavailable",
            50.0,
        )

    if (
        sma20 is not None
        and sma50 is not None
        and sma100 is not None
        and sma200 is not None
    ):

        if (
            price > sma20
            > sma50
            > sma100
            > sma200
        ):

            return (
                "Strong Bullish",
                100.0,
            )

        if (
            price > sma20
            and price > sma50
            and price > sma200
        ):

            return (
                "Bullish",
                85.0,
            )

        if (
            price > sma200
            and (
                price > sma20
                or price > sma50
            )
        ):

            return (
                "Positive",
                70.0,
            )

        if (
            price < sma20
            and price < sma50
            and price < sma200
        ):

            return (
                "Bearish",
                10.0,
            )

        if price < sma200:

            return (
                "Sideways / Weak",
                30.0,
            )

    return (
        "Neutral",
        50.0,
    )


# =========================================================
# MOMENTUM
# =========================================================

def determine_momentum(
    row: pd.Series,
) -> tuple[str, float]:

    price = safe_float(
        row.get("Close")
    )

    sma20 = safe_float(
        row.get("SMA20")
    )

    rsi = safe_float(
        row.get("RSI14")
    )

    if price is None:
        return (
            "Unavailable",
            50.0,
        )

    if (
        rsi is not None
        and rsi >= 60
        and sma20 is not None
        and price > sma20
    ):

        return (
            "Strong",
            100.0,
        )

    if (
        rsi is not None
        and rsi >= 50
        and sma20 is not None
        and price > sma20
    ):

        return (
            "Positive",
            75.0,
        )

    if (
        rsi is not None
        and rsi < 35
    ):

        return (
            "Weak",
            20.0,
        )

    if (
        rsi is not None
        and rsi < 45
    ):

        return (
            "Weak",
            30.0,
        )

    return (
        "Neutral",
        50.0,
    )


# =========================================================
# INDEX SCORE
# =========================================================

def calculate_index_score(
    row: pd.Series,
) -> float:

    _, trend_score = (
        determine_trend(
            row
        )
    )

    _, momentum_score = (
        determine_momentum(
            row
        )
    )

    rsi = safe_float(
        row.get("RSI14")
    )

    if rsi is None:

        rsi_score = 50.0

    elif 45 <= rsi <= 65:

        rsi_score = 100.0

    elif 35 <= rsi < 45:

        rsi_score = 55.0

    elif 65 < rsi <= 75:

        rsi_score = 70.0

    elif rsi < 35:

        rsi_score = 25.0

    else:

        rsi_score = 35.0

    volume_ratio = safe_float(
        row.get("VolumeRatio")
    )

    if volume_ratio is None:

        volume_score = 50.0

    elif volume_ratio >= 1.5:

        volume_score = 90.0

    elif volume_ratio >= 1.0:

        volume_score = 70.0

    else:

        volume_score = 40.0

    score = (
        trend_score * 0.40
        +
        momentum_score * 0.35
        +
        rsi_score * 0.15
        +
        volume_score * 0.10
    )

    return round(
        clamp(score),
        2,
    )


# =========================================================
# FETCH YAHOO DATA
# =========================================================

def download_history(
    symbol: str,
) -> pd.DataFrame:

    try:

        data = yf.download(
            symbol,
            period="2y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        data = prepare_history(
            data
        )

        if not data.empty:
            return data

    except Exception as error:

        print(
            f"Yahoo download failed "
            f"for {symbol}: {error}"
        )

    return pd.DataFrame()


# =========================================================
# YAHOO CHART API FALLBACK
# =========================================================

def yahoo_chart_fallback(
    symbol: str,
) -> pd.DataFrame:

    url = (
        "https://query1.finance.yahoo.com/"
        f"v8/finance/chart/{symbol}"
    )

    params = {
        "range": "2y",
        "interval": "1d",
        "events": "history",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20,
            headers={
                "User-Agent":
                    NSE_HEADERS[
                        "User-Agent"
                    ]
            },
        )

        response.raise_for_status()

        payload = response.json()

        result = (
            payload
            .get("chart", {})
            .get("result")
        )

        if not result:
            return pd.DataFrame()

        result = result[0]

        timestamps = result.get(
            "timestamp",
            [],
        )

        quote = (
            result
            .get("indicators", {})
            .get("quote", [{}])[0]
        )

        if not timestamps:
            return pd.DataFrame()

        dataframe = pd.DataFrame(
            {
                "Open":
                    quote.get(
                        "open",
                        [],
                    ),

                "High":
                    quote.get(
                        "high",
                        [],
                    ),

                "Low":
                    quote.get(
                        "low",
                        [],
                    ),

                "Close":
                    quote.get(
                        "close",
                        [],
                    ),

                "Volume":
                    quote.get(
                        "volume",
                        [],
                    ),
            },
            index=pd.to_datetime(
                timestamps,
                unit="s",
            ),
        )

        return prepare_history(
            dataframe
        )

    except Exception as error:

        print(
            f"Yahoo chart fallback failed "
            f"for {symbol}: {error}"
        )

        return pd.DataFrame()


# =========================================================
# NSE OFFICIAL INDEX SNAPSHOT
# =========================================================

def get_nse_snapshot() -> dict:

    url = (
        "https://www.nseindia.com/api/allIndices"
    )

    session = requests.Session()

    try:

        session.get(
            "https://www.nseindia.com/",
            headers=NSE_HEADERS,
            timeout=15,
        )

        response = session.get(
            url,
            headers=NSE_HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        payload = response.json()

        rows = payload.get(
            "data",
            [],
        )

        snapshot = {}

        for row in rows:

            index_name = str(
                row.get(
                    "index",
                    row.get(
                        "indexSymbol",
                        "",
                    ),
                )
            ).strip().upper()

            if "NIFTY 50" in index_name:

                snapshot[
                    "NIFTY 50"
                ] = {
                    "price":
                        safe_float(
                            row.get(
                                "last"
                            )
                        ),

                    "previous_close":
                        safe_float(
                            row.get(
                                "previousClose"
                            )
                        ),

                    "change":
                        safe_float(
                            row.get(
                                "variation"
                            )
                        ),

                    "change_pct":
                        safe_float(
                            row.get(
                                "percentChange"
                            )
                        ),

                    "timestamp":
                        row.get(
                            "lastUpdateTime"
                        ),
                }

            elif (
                "NIFTY BANK"
                in index_name
                or "BANK NIFTY"
                in index_name
            ):

                snapshot[
                    "BANK NIFTY"
                ] = {
                    "price":
                        safe_float(
                            row.get(
                                "last"
                            )
                        ),

                    "previous_close":
                        safe_float(
                            row.get(
                                "previousClose"
                            )
                        ),

                    "change":
                        safe_float(
                            row.get(
                                "variation"
                            )
                        ),

                    "change_pct":
                        safe_float(
                            row.get(
                                "percentChange"
                            )
                        ),

                    "timestamp":
                        row.get(
                            "lastUpdateTime"
                        ),
                }

            elif "INDIA VIX" in index_name:

                snapshot[
                    "INDIA VIX"
                ] = {
                    "price":
                        safe_float(
                            row.get(
                                "last"
                            )
                        ),

                    "previous_close":
                        safe_float(
                            row.get(
                                "previousClose"
                            )
                        ),

                    "change":
                        safe_float(
                            row.get(
                                "variation"
                            )
                        ),

                    "change_pct":
                        safe_float(
                            row.get(
                                "percentChange"
                            )
                        ),

                    "timestamp":
                        row.get(
                            "lastUpdateTime"
                        ),
                }

        return snapshot

    except Exception as error:

        print(
            "NSE official snapshot "
            f"unavailable: {error}"
        )

        return {}


# =========================================================
# VIX INTERPRETATION
# =========================================================

def interpret_vix(
    value: float | None,
) -> str:

    if value is None:
        return "Unavailable"

    if value < 12:
        return "Very Low Volatility"

    if value < 15:
        return "Low Volatility"

    if value < 20:
        return "Normal Volatility"

    if value < 25:
        return "Elevated Risk"

    if value < 30:
        return "High Risk"

    return "Very High Risk"


# =========================================================
# MARKET REGIME
# =========================================================

def determine_market_regime(
    nifty_score: float,
    bank_score: float,
    breadth_score: float | None = None,
    vix: float | None = None,
) -> tuple[str, float]:

    index_score = (
        nifty_score * 0.60
        +
        bank_score * 0.40
    )

    if breadth_score is None:

        market_score = index_score

    else:

        market_score = (
            index_score * 0.75
            +
            breadth_score * 0.25
        )

    # VIX is treated as a risk overlay, not as a
    # directional signal by itself.
    if vix is not None:

        if vix >= 25:
            market_score -= 8

        elif vix >= 20:
            market_score -= 4

        elif vix < 12:
            market_score += 2

    market_score = clamp(
        market_score
    )

    if market_score >= 75:

        regime = "Strong Bullish"

    elif market_score >= 60:

        regime = "Bullish"

    elif market_score >= 45:

        regime = "Neutral"

    elif market_score >= 30:

        regime = "Cautious"

    else:

        regime = "Bearish"

    return (
        regime,
        round(
            market_score,
            2,
        ),
    )


# =========================================================
# ENVIRONMENTS
# =========================================================

def build_environments(
    regime: str,
    market_score: float,
    vix: float | None,
) -> dict:

    if regime == "Strong Bullish":

        equity = "Favorable"
        swing = "Favorable"
        breakout = "Favorable"
        intraday = "Favorable"
        options = "Favorable"

    elif regime == "Bullish":

        equity = "Favorable"
        swing = "Favorable"
        breakout = "Selective"
        intraday = "Selective"
        options = "Selective"

    elif regime == "Neutral":

        equity = "Selective"
        swing = "Selective"
        breakout = "Confirmation Required"
        intraday = "Selective"
        options = "Selective"

    elif regime == "Cautious":

        equity = "Defensive"
        swing = "Selective"
        breakout = "Confirmation Required"
        intraday = "High Selectivity"
        options = "High Risk"

    else:

        equity = "Defensive"
        swing = "High Selectivity"
        breakout = "Avoid Weak Breakouts"
        intraday = "High Risk"
        options = "High Risk"

    if vix is not None and vix >= 20:

        intraday = "High Risk"
        options = "High Risk"

    return {
        "equity_environment":
            equity,

        "swing_environment":
            swing,

        "breakout_environment":
            breakout,

        "intraday_environment":
            intraday,

        "options_environment":
            options,
    }


# =========================================================
# MARKET SCENARIO
# =========================================================

def build_scenario(
    nifty: dict,
    bank: dict,
    market_score: float,
    regime: str,
) -> dict:

    nifty_support = safe_float(
        nifty.get(
            "support"
        )
    )

    nifty_resistance = safe_float(
        nifty.get(
            "resistance"
        )
    )

    nifty_pivot = safe_float(
        nifty.get(
            "pivot"
        )
    )

    price = safe_float(
        nifty.get(
            "price"
        )
    )

    if price is None:

        return {
            "scenario":
                "Market data unavailable.",

            "market_scenario":
                "Market data unavailable.",

            "bullish_trigger":
                None,

            "bearish_trigger":
                None,
        }

    bullish_trigger = (
        f"Above {nifty_resistance:.2f}"
        if nifty_resistance is not None
        else None
    )

    bearish_trigger = (
        f"Below {nifty_support:.2f}"
        if nifty_support is not None
        else None
    )

    if (
        nifty_resistance is not None
        and price > nifty_resistance
    ):

        scenario = (
            "Bullish continuation possible "
            "if the breakout sustains."
        )

    elif (
        nifty_support is not None
        and price < nifty_support
    ):

        scenario = (
            "Downside risk remains elevated "
            "while price stays below support."
        )

    elif (
        nifty_pivot is not None
        and price >= nifty_pivot
    ):

        scenario = (
            "Market is above pivot; "
            "watch resistance for confirmation."
        )

    else:

        scenario = (
            "Market is range-bound; "
            "wait for support/resistance confirmation."
        )

    return {
        "scenario":
            scenario,

        "market_scenario":
            scenario,

        "bullish_trigger":
            bullish_trigger,

        "bearish_trigger":
            bearish_trigger,
    }


# =========================================================
# BUILD INDEX DATA
# =========================================================

def build_index_data(
    name: str,
    symbol: str,
    snapshot: dict,
) -> dict:

    history = download_history(
        symbol
    )

    if history.empty:

        history = yahoo_chart_fallback(
            symbol
        )

    if history.empty:

        return {
            "name":
                name,

            "symbol":
                symbol,

            "price":
                snapshot.get(
                    "price"
                ),

            "previous_close":
                snapshot.get(
                    "previous_close"
                ),

            "daily_return_pct":
                snapshot.get(
                    "change_pct"
                ),

            "trend":
                "Unavailable",

            "trend_score":
                50.0,

            "momentum":
                "Unavailable",

            "momentum_score":
                50.0,

            "rsi":
                None,

            "sma20":
                None,

            "sma50":
                None,

            "sma100":
                None,

            "sma200":
                None,

            "ema20":
                None,

            "ema50":
                None,

            "atr14":
                None,

            "atr_percent":
                None,

            "volume_ratio":
                None,

            "support":
                None,

            "resistance":
                None,

            "pivot":
                None,

            "score":
                50.0,

            "data_source":
                "NSE snapshot only",
        }

    indicators = add_indicators(
        history
    )

    if indicators.empty:

        return {
            "name":
                name,

            "symbol":
                symbol,

            "price":
                snapshot.get(
                    "price"
                ),

            "previous_close":
                snapshot.get(
                    "previous_close"
                ),

            "daily_return_pct":
                snapshot.get(
                    "change_pct"
                ),

            "trend":
                "Unavailable",

            "trend_score":
                50.0,

            "momentum":
                "Unavailable",

            "momentum_score":
                50.0,

            "rsi":
                None,

            "score":
                50.0,

            "data_source":
                "NSE snapshot",
        }

    latest = indicators.iloc[-1]

    trend, trend_score = (
        determine_trend(
            latest
        )
    )

    momentum, momentum_score = (
        determine_momentum(
            latest
        )
    )

    score = calculate_index_score(
        latest
    )

    levels = calculate_levels(
        indicators
    )

    price = safe_float(
        snapshot.get(
            "price"
        )
    )

    if price is None:

        price = safe_float(
            latest.get(
                "Close"
            )
        )

    previous_close = safe_float(
        snapshot.get(
            "previous_close"
        )
    )

    if previous_close is None:

        if len(indicators) >= 2:

            previous_close = safe_float(
                indicators[
                    "Close"
                ].iloc[-2]
            )

    daily_return_pct = safe_float(
        snapshot.get(
            "change_pct"
        )
    )

    if (
        daily_return_pct is None
        and price is not None
        and previous_close is not None
        and previous_close != 0
    ):

        daily_return_pct = (
            (
                price -
                previous_close
            )
            /
            previous_close
        ) * 100

    atr = safe_float(
        latest.get(
            "ATR14"
        )
    )

    atr_percent = None

    if (
        atr is not None
        and price is not None
        and price != 0
    ):

        atr_percent = (
            atr /
            price
        ) * 100

    return {
        "name":
            name,

        "symbol":
            symbol,

        "price":
            price,

        "previous_close":
            previous_close,

        "daily_return_pct":
            daily_return_pct,

        "trend":
            trend,

        "trend_score":
            round(
                trend_score,
                2,
            ),

        "momentum":
            momentum,

        "momentum_score":
            round(
                momentum_score,
                2,
            ),

        "rsi":
            safe_float(
                latest.get(
                    "RSI14"
                )
            ),

        "sma20":
            safe_float(
                latest.get(
                    "SMA20"
                )
            ),

        "sma50":
            safe_float(
                latest.get(
                    "SMA50"
                )
            ),

        "sma100":
            safe_float(
                latest.get(
                    "SMA100"
                )
            ),

        "sma200":
            safe_float(
                latest.get(
                    "SMA200"
                )
            ),

        "ema20":
            safe_float(
                latest.get(
                    "EMA20"
                )
            ),

        "ema50":
            safe_float(
                latest.get(
                    "EMA50"
                )
            ),

        "atr14":
            atr,

        "atr_percent":
            atr_percent,

        "volume_ratio":
            safe_float(
                latest.get(
                    "VolumeRatio"
                )
            ),

        "support":
            levels.get(
                "support"
            ),

        "resistance":
            levels.get(
                "resistance"
            ),

        "pivot":
            levels.get(
                "pivot"
            ),

        "score":
            score,

        "data_source":
            (
                "NSE official snapshot + "
                "Yahoo historical indicators"
            ),
    }


# =========================================================
# MAIN MARKET ENGINE
# =========================================================

def get_market_regime() -> dict:

    print(
        "\n"
        + "=" * 60
    )

    print(
        "RUNNING MARKET ENGINE"
    )

    print(
        "=" * 60
    )

    snapshot = get_nse_snapshot()

    nifty_snapshot = snapshot.get(
        "NIFTY 50",
        {},
    )

    bank_snapshot = snapshot.get(
        "BANK NIFTY",
        {},
    )

    vix_snapshot = snapshot.get(
        "INDIA VIX",
        {},
    )

    nifty = build_index_data(
        "NIFTY 50",
        NIFTY_SYMBOL,
        nifty_snapshot,
    )

    bank = build_index_data(
        "BANK NIFTY",
        BANK_NIFTY_SYMBOL,
        bank_snapshot,
    )

    vix = safe_float(
        vix_snapshot.get(
            "price"
        )
    )

    # -----------------------------------------------------
    # Breadth
    # -----------------------------------------------------

    breadth_score = None

    breadth_file = (
        OUTPUT_DIR /
        "market_breadth.csv"
    )

    if breadth_file.exists():

        try:

            breadth_df = pd.read_csv(
                breadth_file
            )

            if not breadth_df.empty:

                latest_breadth = (
                    breadth_df.iloc[-1]
                )

                breadth_score = safe_float(
                    latest_breadth.get(
                        "breadth_score"
                    )
                )

        except Exception as error:

            print(
                "Unable to read breadth: "
                f"{error}"
            )

    # -----------------------------------------------------
    # Market score
    # -----------------------------------------------------

    nifty_score = safe_float(
        nifty.get(
            "score"
        ),
        50.0,
    )

    bank_score = safe_float(
        bank.get(
            "score"
        ),
        50.0,
    )

    regime, market_score = (
        determine_market_regime(
            nifty_score,
            bank_score,
            breadth_score,
            vix,
        )
    )

    environments = (
        build_environments(
            regime,
            market_score,
            vix,
        )
    )

    scenario = build_scenario(
        nifty,
        bank,
        market_score,
        regime,
    )

    vix_interpretation = (
        interpret_vix(
            vix
        )
    )

    generated_at = (
        datetime.now()
        .astimezone()
        .isoformat()
    )

    # -----------------------------------------------------
    # Flat compatibility fields
    # -----------------------------------------------------

    result = {
        "market_regime":
            regime,

        "market_score":
            market_score,

        "nifty_price":
            nifty.get(
                "price"
            ),

        "nifty_previous_close":
            nifty.get(
                "previous_close"
            ),

        "nifty_daily_return_pct":
            nifty.get(
                "daily_return_pct"
            ),

        "nifty_score":
            nifty.get(
                "score"
            ),

        "nifty_trend":
            nifty.get(
                "trend"
            ),

        "nifty_momentum":
            nifty.get(
                "momentum"
            ),

        "nifty_rsi":
            nifty.get(
                "rsi"
            ),

        "nifty_support":
            nifty.get(
                "support"
            ),

        "nifty_resistance":
            nifty.get(
                "resistance"
            ),

        "nifty_pivot":
            nifty.get(
                "pivot"
            ),

        "bank_nifty_price":
            bank.get(
                "price"
            ),

        "bank_nifty_previous_close":
            bank.get(
                "previous_close"
            ),

        "bank_nifty_daily_return_pct":
            bank.get(
                "daily_return_pct"
            ),

        "bank_nifty_score":
            bank.get(
                "score"
            ),

        "bank_nifty_trend":
            bank.get(
                "trend"
            ),

        "bank_nifty_momentum":
            bank.get(
                "momentum"
            ),

        "bank_nifty_rsi":
            bank.get(
                "rsi"
            ),

        "bank_nifty_support":
            bank.get(
                "support"
            ),

        "bank_nifty_resistance":
            bank.get(
                "resistance"
            ),

        "bank_nifty_pivot":
            bank.get(
                "pivot"
            ),

        "vix":
            vix,

        "vix_interpretation":
            vix_interpretation,

        "equity_environment":
            environments[
                "equity_environment"
            ],

        "swing_environment":
            environments[
                "swing_environment"
            ],

        "breakout_environment":
            environments[
                "breakout_environment"
            ],

        "intraday_environment":
            environments[
                "intraday_environment"
            ],

        "options_environment":
            environments[
                "options_environment"
            ],

        "support":
            nifty.get(
                "support"
            ),

        "resistance":
            nifty.get(
                "resistance"
            ),

        "pivot":
            nifty.get(
                "pivot"
            ),

        "market_support":
            nifty.get(
                "support"
            ),

        "market_resistance":
            nifty.get(
                "resistance"
            ),

        "market_pivot":
            nifty.get(
                "pivot"
            ),

        "bullish_trigger":
            scenario[
                "bullish_trigger"
            ],

        "bearish_trigger":
            scenario[
                "bearish_trigger"
            ],

        "market_scenario":
            scenario[
                "market_scenario"
            ],

        "scenario":
            scenario[
                "scenario"
            ],

        "market_data_authority":
            (
                "NSE official index snapshot "
                "where available; Yahoo Finance "
                "historical data for indicators"
            ),

        "data_authority":
            (
                "NSE official index snapshot "
                "where available; Yahoo Finance "
                "historical data for indicators"
            ),

        "generated_at":
            generated_at,

        # Nested structures.
        "nifty":
            nifty,

        "bank_nifty":
            bank,

        "vix_data":
            {
                "price":
                    vix,

                "previous_close":
                    vix_snapshot.get(
                        "previous_close"
                    ),

                "daily_return_pct":
                    vix_snapshot.get(
                        "change_pct"
                    ),

                "interpretation":
                    vix_interpretation,

                "environment":
                    vix_interpretation,
            },

        "environments":
            environments,

        "market_analysis":
            {
                "support":
                    nifty.get(
                        "support"
                    ),

                "resistance":
                    nifty.get(
                        "resistance"
                    ),

                "pivot":
                    nifty.get(
                        "pivot"
                    ),

                "bullish_trigger":
                    scenario[
                        "bullish_trigger"
                    ],

                "bearish_trigger":
                    scenario[
                        "bearish_trigger"
                    ],

                "scenario":
                    scenario[
                        "scenario"
                    ],

                "market_scenario":
                    scenario[
                        "market_scenario"
                    ],
            },

        "breadth_score":
            breadth_score,
    }

    result = json_safe(
        result
    )

    # -----------------------------------------------------
    # Console output
    # -----------------------------------------------------

    print(
        f"\nOverall Market Regime : "
        f"{regime}"
    )

    print(
        f"Overall Market Score   : "
        f"{market_score:.2f}"
    )

    print(
        "\nNIFTY 50"
    )

    print(
        f"Price       : "
        f"{nifty.get('price')}"
    )

    print(
        f"Trend       : "
        f"{nifty.get('trend')}"
    )

    print(
        f"Momentum    : "
        f"{nifty.get('momentum')}"
    )

    print(
        f"RSI         : "
        f"{nifty.get('rsi')}"
    )

    print(
        f"Score       : "
        f"{nifty.get('score')}"
    )

    print(
        "\nBANK NIFTY"
    )

    print(
        f"Price       : "
        f"{bank.get('price')}"
    )

    print(
        f"Trend       : "
        f"{bank.get('trend')}"
    )

    print(
        f"Momentum    : "
        f"{bank.get('momentum')}"
    )

    print(
        f"RSI         : "
        f"{bank.get('rsi')}"
    )

    print(
        f"Score       : "
        f"{bank.get('score')}"
    )

    print(
        f"\nINDIA VIX   : "
        f"{vix}"
    )

    print(
        f"VIX Risk    : "
        f"{vix_interpretation}"
    )

    print(
        f"\nSupport     : "
        f"{nifty.get('support')}"
    )

    print(
        f"Resistance  : "
        f"{nifty.get('resistance')}"
    )

    print(
        f"Pivot       : "
        f"{nifty.get('pivot')}"
    )

    print(
        f"\nScenario    : "
        f"{scenario.get('scenario')}"
    )

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    csv_path = (
        OUTPUT_DIR /
        "market_regime.csv"
    )

    rows = []

    rows.append(
        {
            "market_component":
                "NIFTY 50",

            "price":
                nifty.get(
                    "price"
                ),

            "previous_close":
                nifty.get(
                    "previous_close"
                ),

            "daily_return_pct":
                nifty.get(
                    "daily_return_pct"
                ),

            "sma20":
                nifty.get(
                    "sma20"
                ),

            "sma50":
                nifty.get(
                    "sma50"
                ),

            "sma100":
                nifty.get(
                    "sma100"
                ),

            "sma200":
                nifty.get(
                    "sma200"
                ),

            "ema20":
                nifty.get(
                    "ema20"
                ),

            "ema50":
                nifty.get(
                    "ema50"
                ),

            "rsi14":
                nifty.get(
                    "rsi"
                ),

            "atr14":
                nifty.get(
                    "atr14"
                ),

            "atr_percent":
                nifty.get(
                    "atr_percent"
                ),

            "trend":
                nifty.get(
                    "trend"
                ),

            "trend_score":
                nifty.get(
                    "trend_score"
                ),

            "momentum":
                nifty.get(
                    "momentum"
                ),

            "momentum_score":
                nifty.get(
                    "momentum_score"
                ),

            "market_score":
                nifty.get(
                    "score"
                ),

            "support":
                nifty.get(
                    "support"
                ),

            "resistance":
                nifty.get(
                    "resistance"
                ),

            "pivot":
                nifty.get(
                    "pivot"
                ),

            "regime":
                regime,
        }
    )

    rows.append(
        {
            "market_component":
                "BANK NIFTY",

            "price":
                bank.get(
                    "price"
                ),

            "previous_close":
                bank.get(
                    "previous_close"
                ),

            "daily_return_pct":
                bank.get(
                    "daily_return_pct"
                ),

            "sma20":
                bank.get(
                    "sma20"
                ),

            "sma50":
                bank.get(
                    "sma50"
                ),

            "sma100":
                bank.get(
                    "sma100"
                ),

            "sma200":
                bank.get(
                    "sma200"
                ),

            "ema20":
                bank.get(
                    "ema20"
                ),

            "ema50":
                bank.get(
                    "ema50"
                ),

            "rsi14":
                bank.get(
                    "rsi"
                ),

            "atr14":
                bank.get(
                    "atr14"
                ),

            "atr_percent":
                bank.get(
                    "atr_percent"
                ),

            "trend":
                bank.get(
                    "trend"
                ),

            "trend_score":
                bank.get(
                    "trend_score"
                ),

            "momentum":
                bank.get(
                    "momentum"
                ),

            "momentum_score":
                bank.get(
                    "momentum_score"
                ),

            "market_score":
                bank.get(
                    "score"
                ),

            "support":
                bank.get(
                    "support"
                ),

            "resistance":
                bank.get(
                    "resistance"
                ),

            "pivot":
                bank.get(
                    "pivot"
                ),

            "regime":
                regime,
        }
    )

    rows.append(
        {
            "market_component":
                "INDIA VIX",

            "price":
                vix,

            "previous_close":
                vix_snapshot.get(
                    "previous_close"
                ),

            "daily_return_pct":
                vix_snapshot.get(
                    "change_pct"
                ),

            "trend":
                "",

            "momentum":
                "",

            "market_score":
                "",

            "value":
                vix,

            "regime":
                vix_interpretation,
        }
    )

    rows.append(
        {
            "market_component":
                "MARKET",

            "market_score":
                market_score,

            "value":
                market_score,

            "regime":
                regime,

            "support":
                nifty.get(
                    "support"
                ),

            "resistance":
                nifty.get(
                    "resistance"
                ),

            "pivot":
                nifty.get(
                    "pivot"
                ),
        }
    )

    pd.DataFrame(
        rows
    ).to_csv(
        csv_path,
        index=False,
    )

    print(
        f"\nSaved market data: "
        f"{csv_path}"
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "MARKET REGIME"
    )

    print(
        "=" * 60
    )

    print(
        f"Regime : {regime}"
    )

    print(
        f"Score  : {market_score:.2f}"
    )

    return result


# =========================================================
# ALIAS
# =========================================================

def get_market_analysis() -> dict:
    return get_market_regime()


# =========================================================
# SCRIPT ENTRY
# =========================================================

if __name__ == "__main__":

    get_market_regime()
