"""
===========================================================
NSE SMART MARKET DASHBOARD
MARKET ENGINE V3
===========================================================

Purpose
-------
Build the market-level decision context used by the
dashboard and ranking engine.

Instruments
-----------
NIFTY 50
BANK NIFTY
INDIA VIX

Data hierarchy
--------------
1. NSE official current-session snapshot
2. Yahoo/yfinance historical data
3. Yahoo Chart API fallback

Important
---------
The engine keeps current-session price and previous close
separate.

It does NOT label an EOD close as live LTP.

Market analysis
---------------
- Market regime
- Market score
- Trend
- Momentum
- RSI
- Support
- Resistance
- Pivot
- Bullish trigger
- Bearish trigger
- Scenario
- Trading environments
===========================================================
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import requests
import yfinance as yf


# =========================================================
# CONFIGURATION
# =========================================================

NIFTY_SYMBOL = "^NSEI"
BANK_NIFTY_SYMBOL = "^NSEBANK"
VIX_SYMBOL = "^INDIAVIX"

NSE_INDICES_URL = (
    "https://www.nseindia.com/api/allIndices"
)

NSE_HOME_URL = (
    "https://www.nseindia.com/"
)

REQUEST_TIMEOUT = 15

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": (
        "application/json,text/plain,*/*"
    ),
    "Accept-Language": (
        "en-US,en;q=0.9"
    ),
    "Referer": (
        "https://www.nseindia.com/"
    ),
    "Connection": "keep-alive",
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

        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except (
        TypeError,
        ValueError,
    ):

        return default


def clean_number(
    value: Any,
) -> float | None:

    return safe_float(value)


def safe_round(
    value: Any,
    digits: int = 2,
) -> float | None:

    value = safe_float(value)

    if value is None:
        return None

    return round(
        value,
        digits,
    )


# =========================================================
# NSE SESSION
# =========================================================

def create_nse_session() -> requests.Session:

    session = requests.Session()

    session.headers.update(
        NSE_HEADERS
    )

    return session


def get_nse_indices() -> list[dict]:

    session = create_nse_session()

    try:

        session.get(
            NSE_HOME_URL,
            timeout=REQUEST_TIMEOUT,
        )

        time.sleep(0.3)

        response = session.get(
            NSE_INDICES_URL,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        payload = response.json()

        data = payload.get(
            "data",
            []
        )

        if isinstance(
            data,
            list,
        ):

            return data

    except Exception as exc:

        print(
            f"NSE official index snapshot failed: {exc}"
        )

    return []


# =========================================================
# FIND NSE INDEX
# =========================================================

def find_nse_index(
    data: list[dict],
    names: list[str],
) -> dict | None:

    if not data:
        return None

    wanted = {
        name.strip().lower()
        for name in names
    }

    for item in data:

        if not isinstance(
            item,
            dict,
        ):
            continue

        name = str(
            item.get(
                "index",
                item.get(
                    "indexSymbol",
                    ""
                ),
            )
        ).strip().lower()

        if name in wanted:
            return item

    return None


# =========================================================
# NORMALIZE NSE INDEX
# =========================================================

def normalize_nse_index(
    item: dict | None,
) -> dict:

    if not item:
        return {}

    last = safe_float(
        item.get("last")
    )

    previous_close = safe_float(
        item.get("previousClose")
    )

    change = safe_float(
        item.get("variation")
    )

    if change is None:
        change = safe_float(
            item.get("percentChange")
        )

        if (
            change is not None
            and previous_close is not None
        ):
            change = (
                previous_close *
                change /
                100.0
            )

    percent_change = safe_float(
        item.get("percentChange")
    )

    if (
        percent_change is None
        and change is not None
        and previous_close
    ):

        percent_change = (
            change /
            previous_close
        ) * 100.0

    open_price = safe_float(
        item.get("open")
    )

    day_high = safe_float(
        item.get("dayHigh")
    )

    day_low = safe_float(
        item.get("dayLow")
    )

    return {

        "name":
            item.get("index"),

        "price":
            last,

        "previous_close":
            previous_close,

        "change":
            change,

        "percent_change":
            percent_change,

        "open":
            open_price,

        "day_high":
            day_high,

        "day_low":
            day_low,

        "source":
            "NSE Official",

    }


# =========================================================
# YAHOO HISTORICAL DATA
# =========================================================

def get_yahoo_history(
    symbol: str,
    period: str = "2y",
) -> pd.DataFrame:

    try:

        ticker = yf.Ticker(symbol)

        history = ticker.history(
            period=period,
            interval="1d",
            auto_adjust=False,
            actions=False,
        )

        if (
            history is not None
            and not history.empty
        ):

            return history

    except Exception as exc:

        print(
            f"yfinance history failed "
            f"{symbol}: {exc}"
        )

    return pd.DataFrame()


# =========================================================
# YAHOO CHART API FALLBACK
# =========================================================

def get_yahoo_chart_history(
    symbol: str,
) -> pd.DataFrame:

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol
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
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent":
                    NSE_HEADERS["User-Agent"]
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
            []
        )

        quote = (
            result
            .get("indicators", {})
            .get("quote", [{}])[0]
        )

        if not timestamps:
            return pd.DataFrame()

        frame = pd.DataFrame(
            {
                "Open":
                    quote.get(
                        "open",
                        []
                    ),

                "High":
                    quote.get(
                        "high",
                        []
                    ),

                "Low":
                    quote.get(
                        "low",
                        []
                    ),

                "Close":
                    quote.get(
                        "close",
                        []
                    ),

                "Volume":
                    quote.get(
                        "volume",
                        []
                    ),
            },
            index=pd.to_datetime(
                timestamps,
                unit="s",
                utc=True,
            ),
        )

        frame = frame.dropna(
            subset=["Close"]
        )

        return frame

    except Exception as exc:

        print(
            f"Yahoo Chart API failed "
            f"{symbol}: {exc}"
        )

    return pd.DataFrame()


# =========================================================
# GET HISTORY WITH FALLBACK
# =========================================================

def get_history(
    symbol: str,
) -> pd.DataFrame:

    history = get_yahoo_history(
        symbol
    )

    if (
        history is not None
        and not history.empty
    ):

        return history

    return get_yahoo_chart_history(
        symbol
    )


# =========================================================
# TECHNICAL INDICATORS
# =========================================================

def calculate_sma(
    series: pd.Series,
    period: int,
) -> pd.Series:

    return (
        series
        .rolling(
            period,
            min_periods=period,
        )
        .mean()
    )


def calculate_ema(
    series: pd.Series,
    period: int,
) -> pd.Series:

    return (
        series
        .ewm(
            span=period,
            adjust=False,
            min_periods=period,
        )
        .mean()
    )


def calculate_rsi(
    series: pd.Series,
    period: int = 14,
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

    rsi = 100 - (
        100 /
        (1 + rs)
    )

    return rsi


def enrich_history(
    history: pd.DataFrame,
) -> pd.DataFrame:

    if history is None or history.empty:
        return pd.DataFrame()

    df = history.copy()

    if isinstance(
        df.columns,
        pd.MultiIndex,
    ):

        df.columns = [
            column[0]
            if isinstance(
                column,
                tuple,
            )
            else column
            for column in df.columns
        ]

    required = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    for column in required:

        if column not in df.columns:
            return pd.DataFrame()

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "Close",
            "High",
            "Low",
        ]
    ).copy()

    close = df["Close"]

    df["SMA20"] = calculate_sma(
        close,
        20,
    )

    df["SMA50"] = calculate_sma(
        close,
        50,
    )

    df["SMA100"] = calculate_sma(
        close,
        100,
    )

    df["SMA200"] = calculate_sma(
        close,
        200,
    )

    df["EMA20"] = calculate_ema(
        close,
        20,
    )

    df["EMA50"] = calculate_ema(
        close,
        50,
    )

    df["RSI14"] = calculate_rsi(
        close,
        14,
    )

    previous_close = close.shift(1)

    tr1 = (
        df["High"] -
        df["Low"]
    )

    tr2 = (
        df["High"] -
        previous_close
    ).abs()

    tr3 = (
        df["Low"] -
        previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3,
        ],
        axis=1,
    ).max(axis=1)

    df["ATR14"] = (
        true_range
        .rolling(
            14,
            min_periods=14,
        )
        .mean()
    )

    df["Volume20"] = (
        df["Volume"]
        .rolling(
            20,
            min_periods=20,
        )
        .mean()
        if "Volume" in df.columns
        else np.nan
    )

    if "Volume" in df.columns:

        df["VolumeRatio"] = (
            df["Volume"] /
            df["Volume20"].replace(
                0,
                np.nan,
            )
        )

    else:

        df["VolumeRatio"] = np.nan

    df["High20"] = (
        df["High"]
        .shift(1)
        .rolling(
            20,
            min_periods=20,
        )
        .max()
    )

    df["Low20"] = (
        df["Low"]
        .shift(1)
        .rolling(
            20,
            min_periods=20,
        )
        .min()
    )

    df["High52W"] = (
        df["High"]
        .rolling(
            252,
            min_periods=100,
        )
        .max()
    )

    df["Low52W"] = (
        df["Low"]
        .rolling(
            252,
            min_periods=100,
        )
        .min()
    )

    return df


# =========================================================
# TREND
# =========================================================

def determine_trend(
    latest: pd.Series,
) -> str:

    price = safe_float(
        latest.get("Close")
    )

    sma20 = safe_float(
        latest.get("SMA20")
    )

    sma50 = safe_float(
        latest.get("SMA50")
    )

    sma200 = safe_float(
        latest.get("SMA200")
    )

    if (
        price is None
        or sma20 is None
        or sma50 is None
        or sma200 is None
    ):

        return "Insufficient Data"

    if (
        price > sma20
        and sma20 > sma50
        and sma50 > sma200
    ):

        return "Strong Bullish"

    if (
        price > sma50
        and sma50 > sma200
    ):

        return "Bullish"

    if price > sma200:

        return "Positive"

    if (
        price < sma20
        and sma20 < sma50
        and sma50 < sma200
    ):

        return "Strong Bearish"

    if price < sma200:

        return "Bearish"

    return "Neutral"


# =========================================================
# MOMENTUM
# =========================================================

def determine_momentum(
    latest: pd.Series,
) -> str:

    price = safe_float(
        latest.get("Close")
    )

    sma20 = safe_float(
        latest.get("SMA20")
    )

    sma50 = safe_float(
        latest.get("SMA50")
    )

    rsi = safe_float(
        latest.get("RSI14")
    )

    if (
        price is None
        or sma20 is None
        or sma50 is None
    ):

        return "Insufficient Data"

    if (
        price > sma20
        and price > sma50
        and (
            rsi is None
            or 50 <= rsi <= 70
        )
    ):

        return "Positive"

    if (
        price > sma20
        and (
            rsi is None
            or rsi >= 45
        )
    ):

        return "Positive"

    if (
        price < sma20
        and price < sma50
    ):

        return "Negative"

    return "Neutral"


# =========================================================
# INDEX SCORE
# =========================================================

def calculate_index_score(
    latest: pd.Series,
) -> float:

    score = 50.0

    price = safe_float(
        latest.get("Close")
    )

    sma20 = safe_float(
        latest.get("SMA20")
    )

    sma50 = safe_float(
        latest.get("SMA50")
    )

    sma200 = safe_float(
        latest.get("SMA200")
    )

    rsi = safe_float(
        latest.get("RSI14")
    )

    volume_ratio = safe_float(
        latest.get("VolumeRatio")
    )


    if (
        price is not None
        and sma20 is not None
    ):

        if price > sma20:
            score += 10
        else:
            score -= 10


    if (
        price is not None
        and sma50 is not None
    ):

        if price > sma50:
            score += 10
        else:
            score -= 10


    if (
        price is not None
        and sma200 is not None
    ):

        if price > sma200:
            score += 15
        else:
            score -= 15


    if (
        sma20 is not None
        and sma50 is not None
    ):

        if sma20 > sma50:
            score += 5
        else:
            score -= 5


    if rsi is not None:

        if 50 <= rsi <= 70:
            score += 10

        elif 40 <= rsi < 50:
            score += 2

        elif rsi > 75:
            score -= 5

        elif rsi < 35:
            score -= 8


    if volume_ratio is not None:

        if volume_ratio >= 1.2:
            score += 5

        elif volume_ratio < 0.7:
            score -= 2


    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        2,
    )


# =========================================================
# SUPPORT / RESISTANCE
# =========================================================

def calculate_levels(
    history: pd.DataFrame,
) -> dict:

    if (
        history is None
        or history.empty
    ):

        return {
            "support": None,
            "resistance": None,
            "pivot": None,
        }


    latest = history.iloc[-1]

    price = safe_float(
        latest.get("Close")
    )

    high = safe_float(
        latest.get("High")
    )

    low = safe_float(
        latest.get("Low")
    )


    support = safe_float(
        latest.get("Low20")
    )

    resistance = safe_float(
        latest.get("High20")
    )


    /*
     Use recent swing structure first.
     */

    if support is None:

        recent = history.tail(20)

        if not recent.empty:

            support = safe_float(
                recent["Low"].min()
            )


    if resistance is None:

        recent = history.tail(20)

        if not recent.empty:

            resistance = safe_float(
                recent["High"].max()
            )


    pivot = None

    if (
        high is not None
        and low is not None
        and price is not None
    ):

        pivot = (
            high +
            low +
            price
        ) / 3.0


    return {

        "support":
            safe_round(
                support
            ),

        "resistance":
            safe_round(
                resistance
            ),

        "pivot":
            safe_round(
                pivot
            ),

    }


# =========================================================
# CURRENT SESSION MERGE
# =========================================================

def merge_official_snapshot(
    history: pd.DataFrame,
    official: dict,
) -> pd.DataFrame:

    if history is None or history.empty:
        return history

    if not official:
        return history

    current_price =
        safe_float(
            official.get("price")
        )

    previous_close =
        safe_float(
            official.get(
                "previous_close"
            )
        )

    day_high =
        safe_float(
            official.get(
                "day_high"
            )
        )

    day_low =
        safe_float(
            official.get(
                "day_low"
            )
        )

    open_price =
        safe_float(
            official.get(
                "open"
            )
        )


    if current_price is None:
        return history


    df = history.copy()


    /*
     The historical Yahoo dataset normally already has the
     current completed session. We update the latest row
     with the official NSE current-session values.

     This avoids adding a synthetic future row.
     */

    latest_index = df.index[-1]


    if open_price is not None:
        df.loc[
            latest_index,
            "Open"
        ] = open_price


    if day_high is not None:
        df.loc[
            latest_index,
            "High"
        ] = day_high


    if day_low is not None:
        df.loc[
            latest_index,
            "Low"
        ] = day_low


    df.loc[
        latest_index,
        "Close"
    ] = current_price


    /*
     Recalculate indicators after current-session update.
     */

    return enrich_history(
        df
    )


# =========================================================
# INDEX ANALYSIS
# =========================================================

def analyse_index(
    name: str,
    symbol: str,
    official: dict | None = None,
) -> dict:

    history =
        get_history(
            symbol
        )


    if (
        history is None
        or history.empty
    ):

        return {

            "name": name,

            "symbol": symbol,

            "price":
                official.get("price")
                if official
                else None,

            "previous_close":
                official.get(
                    "previous_close"
                )
                if official
                else None,

            "change":
                official.get(
                    "change"
                )
                if official
                else None,

            "percent_change":
                official.get(
                    "percent_change"
                )
                if official
                else None,

            "trend":
                "Insufficient Data",

            "momentum":
                "Insufficient Data",

            "rsi":
                None,

            "score":
                50.0,

            "support":
                None,

            "resistance":
                None,

            "pivot":
                None,

            "source":
                (
                    "NSE Official"
                    if official
                    else "Unavailable"
                ),

        }


    history =
        enrich_history(
            history
        )


    if (
        history is None
        or history.empty
    ):

        return {

            "name": name,
            "symbol": symbol,
            "trend":
                "Insufficient Data",
            "momentum":
                "Insufficient Data",
            "rsi":
                None,
            "score":
                50.0,

        }


    if official:

        history =
            merge_official_snapshot(
                history,
                official,
            )


    latest =
        history.iloc[-1]


    technical_price =
        safe_float(
            latest.get("Close")
        )


    previous_close =
        safe_float(
            history.iloc[-2].get(
                "Close"
            )
        )
        if len(history) >= 2
        else None


    if official:

        price =
            safe_float(
                official.get(
                    "price"
                )
            )

        official_previous =
            safe_float(
                official.get(
                    "previous_close"
                )
            )

        if official_previous is not None:
            previous_close = official_previous

    else:

        price =
            technical_price


    change = None

    percent_change = None


    if (
        price is not None
        and previous_close is not None
    ):

        change =
            price -
            previous_close

        percent_change = (
            change /
            previous_close
        ) * 100.0


    levels =
        calculate_levels(
            history
        )


    trend =
        determine_trend(
            latest
        )


    momentum =
        determine_momentum(
            latest
        )


    score =
        calculate_index_score(
            latest
        )


    return {

        "name":
            name,

        "symbol":
            symbol,

        "price":
            safe_round(
                price,
                2,
            ),

        "previous_close":
            safe_round(
                previous_close,
                2,
            ),

        "change":
            safe_round(
                change,
                2,
            ),

        "percent_change":
            safe_round(
                percent_change,
                2,
            ),

        "open":
            safe_round(
                official.get(
                    "open"
                )
                if official
                else latest.get(
                    "Open"
                ),
                2,
            ),

        "day_high":
            safe_round(
                official.get(
                    "day_high"
                )
                if official
                else latest.get(
                    "High"
                ),
                2,
            ),

        "day_low":
            safe_round(
                official.get(
                    "day_low"
                )
                if official
                else latest.get(
                    "Low"
                ),
                2,
            ),

        "sma20":
            safe_round(
                latest.get(
                    "SMA20"
                )
            ),

        "sma50":
            safe_round(
                latest.get(
                    "SMA50"
                )
            ),

        "sma100":
            safe_round(
                latest.get(
                    "SMA100"
                )
            ),

        "sma200":
            safe_round(
                latest.get(
                    "SMA200"
                )
            ),

        "ema20":
            safe_round(
                latest.get(
                    "EMA20"
                )
            ),

        "ema50":
            safe_round(
                latest.get(
                    "EMA50"
                )
            ),

        "rsi":
            safe_round(
                latest.get(
                    "RSI14"
                )
            ),

        "atr":
            safe_round(
                latest.get(
                    "ATR14"
                )
            ),

        "volume_ratio":
            safe_round(
                latest.get(
                    "VolumeRatio"
                )
            ),

        "trend":
            trend,

        "momentum":
            momentum,

        "score":
            score,

        "support":
            levels["support"],

        "resistance":
            levels["resistance"],

        "pivot":
            levels["pivot"],

        "source":
            (
                "NSE Official + Yahoo Historical"
                if official
                else "Yahoo Historical"
            ),

    }


# =========================================================
# VIX
# =========================================================

def analyse_vix(
    official_data: list[dict],
) -> dict:

    vix_item =
        find_nse_index(
            official_data,
            [
                "INDIA VIX",
                "INDIA VIX ",
            ],
        )


    if vix_item:

        official =
            normalize_nse_index(
                vix_item
            )

        value =
            official.get(
                "price"
            )

        source =
            "NSE Official"


    else:

        history =
            get_history(
                VIX_SYMBOL
            )


        if (
            history is None
            or history.empty
        ):

            return {

                "value":
                    None,

                "interpretation":
                    "Unavailable",

                "source":
                    "Unavailable",

            }


        latest =
            history.iloc[-1]

        value =
            safe_float(
                latest.get(
                    "Close"
                )
            )

        source =
            "Yahoo Historical"


    if value is None:

        interpretation =
            "Unavailable"

    elif value < 12:

        interpretation =
            "Very Low Volatility"

    elif value < 16:

        interpretation =
            "Low Volatility"

    elif value < 20:

        interpretation =
            "Moderate Volatility"

    elif value < 25:

        interpretation =
            "Elevated Volatility"

    elif value < 30:

        interpretation =
            "High Volatility"

    else:

        interpretation =
            "Very High Volatility"


    return {

        "value":
            safe_round(
                value,
                2,
            ),

        "interpretation":
            interpretation,

        "source":
            source,

    }


# =========================================================
# MARKET SCORE
# =========================================================

def calculate_market_score(
    nifty: dict,
    bank_nifty: dict,
    breadth: dict | None = None,
    vix: dict | None = None,
) -> float:

    scores = []


    nifty_score =
        safe_float(
            nifty.get(
                "score"
            )
        )

    bank_score =
        safe_float(
            bank_nifty.get(
                "score"
            )
        )


    if nifty_score is not None:
        scores.append(
            nifty_score
        )

    if bank_score is not None:
        scores.append(
            bank_score
        )


    if breadth:

        breadth_score =
            safe_float(
                breadth.get(
                    "breadth_score",
                    breadth.get(
                        "Breadth_Score"
                    ),
                )
            )

        if breadth_score is not None:

            scores.append(
                breadth_score
            )


    if not scores:
        return 50.0


    /*
     Index scores receive greater weight than breadth.
     */

    if (
        nifty_score is not None
        and bank_score is not None
        and breadth
    ):

        breadth_score =
            safe_float(
                breadth.get(
                    "breadth_score",
                    breadth.get(
                        "Breadth_Score"
                    ),
                )
            )


        if breadth_score is not None:

            score = (
                nifty_score * 0.35
                +
                bank_score * 0.30
                +
                breadth_score * 0.35
            )

        else:

            score = (
                nifty_score * 0.55
                +
                bank_score * 0.45
            )

    else:

        score = (
            sum(scores) /
            len(scores)
        )


    /*
     VIX risk adjustment.
     */

    if vix:

        vix_value =
            safe_float(
                vix.get(
                    "value"
                )
            )


        if (
            vix_value is not None
            and vix_value >= 25
        ):

            score -= 8

        elif (
            vix_value is not None
            and vix_value >= 20
        ):

            score -= 4


    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        2,
    )


# =========================================================
# MARKET REGIME
# =========================================================

def determine_market_regime(
    score: float,
) -> str:

    if score >= 75:
        return "Strong Bullish"

    if score >= 60:
        return "Bullish"

    if score >= 50:
        return "Neutral"

    if score >= 40:
        return "Cautious"

    if score >= 25:
        return "Weak"

    return "Bearish"


# =========================================================
# MARKET ENVIRONMENT
# =========================================================

def determine_environments(
    regime: str,
    score: float,
    vix: dict,
) -> dict:

    vix_value =
        safe_float(
            vix.get(
                "value"
            )
            if vix
            else None
        )


    if regime in {
        "Strong Bullish",
        "Bullish",
    }:

        equity =
            "Favourable"

        swing =
            "Favourable"

        breakout =
            "Favour Breakouts"

        intraday =
            "Favourable"

        options =
            "Selective"


    elif regime == "Neutral":

        equity =
            "Selective"

        swing =
            "Selective"

        breakout =
            "Selective Breakouts"

        intraday =
            "Selective"

        options =
            "Selective"


    elif regime == "Cautious":

        equity =
            "Cautious"

        swing =
            "Cautious"

        breakout =
            "Confirmation Required"

        intraday =
            "Selective"

        options =
            "High Risk"


    elif regime == "Weak":

        equity =
            "Cautious"

        swing =
            "Defensive"

        breakout =
            "Avoid Weak Breakouts"

        intraday =
            "Selective"

        options =
            "High Risk"


    else:

        equity =
            "Defensive"

        swing =
            "Avoid"

        breakout =
            "Avoid Breakouts"

        intraday =
            "Avoid"

        options =
            "Very High Risk"


    if (
        vix_value is not None
        and vix_value >= 25
    ):

        options =
            "Very High Risk"


    elif (
        vix_value is not None
        and vix_value >= 20
    ):

        options =
            "High Risk"


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

def build_market_scenario(
    nifty: dict,
    bank_nifty: dict,
    regime: str,
) -> dict:

    nifty_price =
        safe_float(
            nifty.get(
                "price"
            )
        )

    nifty_support =
        safe_float(
            nifty.get(
                "support"
            )
        )

    nifty_resistance =
        safe_float(
            nifty.get(
                "resistance"
            )
        )

    nifty_pivot =
        safe_float(
            nifty.get(
                "pivot"
            )
        )


    if nifty_price is None:

        return {

            "scenario":
                "Market data unavailable.",

            "bullish_trigger":
                None,

            "bearish_trigger":
                None,

        }


    bullish_trigger =
        nifty_resistance


    bearish_trigger =
        nifty_support


    if (
        regime in {
            "Strong Bullish",
            "Bullish",
        }
    ):

        scenario = (
            "Market structure is constructive. "
            "Prefer stocks showing strength above "
            "key moving averages and confirmed "
            "breakouts."
        )


    elif regime == "Neutral":

        scenario = (
            "Market is balanced. "
            "Wait for a decisive move above "
            "resistance or below support before "
            "aggressively increasing exposure."
        )


    elif regime == "Cautious":

        scenario = (
            "Market conditions are cautious. "
            "Prefer selective setups with confirmation "
            "and controlled position sizing."
        )


    elif regime == "Weak":

        scenario = (
            "Market breadth and index structure are weak. "
            "Avoid chasing weak breakouts and favour "
            "confirmation-based trades."
        )


    else:

        scenario = (
            "Market is defensive. "
            "Capital preservation should take priority "
            "over aggressive new positions."
        )


    if (
        nifty_resistance is not None
        and nifty_support is not None
    ):

        scenario += (
            f" NIFTY support is around "
            f"{nifty_support:.2f} and resistance "
            f"around {nifty_resistance:.2f}."
        )


    return {

        "scenario":
            scenario,

        "bullish_trigger":
            safe_round(
                bullish_trigger
            ),

        "bearish_trigger":
            safe_round(
                bearish_trigger
            ),

        "support":
            safe_round(
                nifty_support
            ),

        "resistance":
            safe_round(
                nifty_resistance
            ),

        "pivot":
            safe_round(
                nifty_pivot
            ),

    }


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def get_market_regime(
    breadth: dict | None = None,
) -> dict:

    print(
        "\n"
        "----------------------------------------------------"
    )

    print(
        "Market Engine V3"
    )

    print(
        "----------------------------------------------------"
    )


    /*
     NSE official current-session data.
     */

    official_data =
        get_nse_indices()


    nifty_item =
        find_nse_index(
            official_data,
            [
                "NIFTY 50",
                "NIFTY50",
            ],
        )


    bank_item =
        find_nse_index(
            official_data,
            [
                "NIFTY BANK",
                "NIFTY BANK ",
                "NIFTYBANK",
            ],
        )


    nifty_official =
        normalize_nse_index(
            nifty_item
        )


    bank_official =
        normalize_nse_index(
            bank_item
        )


    /*
     Historical technical analysis.
     */

    nifty =
        analyse_index(
            "NIFTY 50",
            NIFTY_SYMBOL,
            nifty_official,
        )


    bank_nifty =
        analyse_index(
            "BANK NIFTY",
            BANK_NIFTY_SYMBOL,
            bank_official,
        )


    /*
     VIX.
     */

    vix =
        analyse_vix(
            official_data
        )


    /*
     Market score.
     */

    market_score =
        calculate_market_score(
            nifty,
            bank_nifty,
            breadth,
            vix,
        )


    regime =
        determine_market_regime(
            market_score
        )


    environments =
        determine_environments(
            regime,
            market_score,
            vix,
        )


    scenario =
        build_market_scenario(
            nifty,
            bank_nifty,
            regime,
        )


    generated_at =
        datetime.now()
        .astimezone()
        .isoformat()


    /*
     Flat fields are retained for compatibility with the
     dashboard and ranking engine.
     */

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
                "percent_change"
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
            bank_nifty.get(
                "price"
            ),

        "bank_nifty_previous_close":
            bank_nifty.get(
                "previous_close"
            ),

        "bank_nifty_daily_return_pct":
            bank_nifty.get(
                "percent_change"
            ),

        "bank_nifty_score":
            bank_nifty.get(
                "score"
            ),

        "bank_nifty_trend":
            bank_nifty.get(
                "trend"
            ),

        "bank_nifty_momentum":
            bank_nifty.get(
                "momentum"
            ),

        "bank_nifty_rsi":
            bank_nifty.get(
                "rsi"
            ),

        "bank_nifty_support":
            bank_nifty.get(
                "support"
            ),

        "bank_nifty_resistance":
            bank_nifty.get(
                "resistance"
            ),

        "bank_nifty_pivot":
            bank_nifty.get(
                "pivot"
            ),

        "vix":
            vix.get(
                "value"
            ),

        "vix_interpretation":
            vix.get(
                "interpretation"
            ),

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
            scenario.get(
                "support"
            ),

        "resistance":
            scenario.get(
                "resistance"
            ),

        "pivot":
            scenario.get(
                "pivot"
            ),

        "market_support":
            scenario.get(
                "support"
            ),

        "market_resistance":
            scenario.get(
                "resistance"
            ),

        "market_pivot":
            scenario.get(
                "pivot"
            ),

        "bullish_trigger":
            scenario.get(
                "bullish_trigger"
            ),

        "bearish_trigger":
            scenario.get(
                "bearish_trigger"
            ),

        "market_scenario":
            scenario.get(
                "scenario"
            ),

        "scenario":
            scenario.get(
                "scenario"
            ),

        "market_data_authority":
            (
                "NSE Official + Yahoo Historical"
                if official_data
                else "Yahoo Historical"
            ),

        "data_authority":
            (
                "NSE Official + Yahoo Historical"
                if official_data
                else "Yahoo Historical"
            ),

        "generated_at":
            generated_at,

        /*
         Nested objects make the frontend easier to extend.
         */

        "nifty":
            nifty,

        "bank_nifty":
            bank_nifty,

        "vix_data":
            vix,

        "environments":
            environments,

        "market_analysis":
            scenario,

    }


    print(
        f"NIFTY: "
        f"{nifty.get('price')}"
    )

    print(
        f"Bank NIFTY: "
        f"{bank_nifty.get('price')}"
    )

    print(
        f"India VIX: "
        f"{vix.get('value')}"
    )

    print(
        f"Market score: "
        f"{market_score}"
    )

    print(
        f"Market regime: "
        f"{regime}"
    )

    print(
        f"Data authority: "
        f"{result['market_data_authority']}"
    )

    print(
        "----------------------------------------------------"
    )


    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result =
        get_market_regime(
            {}
        )


    print("\nMarket Engine Result:\n")

    for key, value in result.items():

        if key not in {
            "nifty",
            "bank_nifty",
            "vix_data",
            "environments",
            "market_analysis",
        }:

            print(
                f"{key}: {value}"
            )
