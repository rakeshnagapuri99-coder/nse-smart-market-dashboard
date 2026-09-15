import pandas as pd
import numpy as np


# ============================================================
# NSE SMART MARKET DASHBOARD
# TECHNICAL ENGINE
# ============================================================


def calculate_sma(data, period):
    """Calculate Simple Moving Average."""
    return data["Close"].rolling(period).mean()


def calculate_ema(data, period):
    """Calculate Exponential Moving Average."""
    return data["Close"].ewm(span=period, adjust=False).mean()


def calculate_rsi(data, period=14):
    """Calculate RSI."""
    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_atr(data, period=14):
    """Calculate Average True Range."""

    high_low = data["High"] - data["Low"]

    high_close = (
        data["High"] - data["Close"].shift(1)
    ).abs()

    low_close = (
        data["Low"] - data["Close"].shift(1)
    ).abs()

    true_range = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)

    atr = true_range.rolling(period).mean()

    return atr


def calculate_volume_ratio(data, period=20):
    """Calculate current volume relative to average volume."""

    average_volume = data["Volume"].rolling(period).mean()

    volume_ratio = (
        data["Volume"] / average_volume
    )

    return volume_ratio


def calculate_52_week_high(data):
    """Calculate rolling 52-week high."""

    return data["High"].rolling(252).max()


def calculate_52_week_low(data):
    """Calculate rolling 52-week low."""

    return data["Low"].rolling(252).min()


def calculate_distance_from_high(data):
    """Distance of current price from 52-week high."""

    distance = (
        (data["Close"] - data["52W_High"])
        / data["52W_High"]
    ) * 100

    return distance


def calculate_distance_from_low(data):
    """Distance of current price from 52-week low."""

    distance = (
        (data["Close"] - data["52W_Low"])
        / data["52W_Low"]
    ) * 100

    return distance


def calculate_distance_from_200dma(data):
    """Distance of current price from 200 DMA."""

    distance = (
        (data["Close"] - data["SMA200"])
        / data["SMA200"]
    ) * 100

    return distance


def calculate_support(data, lookback=20):
    """
    Basic support based on recent swing lows.
    """

    return data["Low"].rolling(lookback).min()


def calculate_resistance(data, lookback=20):
    """
    Basic resistance based on recent swing highs.
    """

    return data["High"].rolling(lookback).max()


def determine_trend(row):
    """
    Determine trend from price and moving-average structure.
    """

    price = row["Close"]

    sma20 = row["SMA20"]
    sma50 = row["SMA50"]
    sma200 = row["SMA200"]

    if (
        price > sma20
        and sma20 > sma50
        and sma50 > sma200
    ):
        return "Strong Uptrend"

    elif (
        price > sma50
        and sma50 > sma200
    ):
        return "Uptrend"

    elif (
        price < sma20
        and sma20 < sma50
        and sma50 < sma200
    ):
        return "Strong Downtrend"

    elif price < sma200:
        return "Downtrend"

    else:
        return "Sideways"


def determine_momentum(row):
    """
    Determine momentum using RSI and EMA structure.
    """

    rsi = row["RSI14"]

    price = row["Close"]

    ema9 = row["EMA9"]
    ema20 = row["EMA20"]

    if (
        rsi >= 60
        and price > ema9
        and ema9 > ema20
    ):
        return "Strong Positive"

    elif (
        rsi >= 50
        and price > ema20
    ):
        return "Positive"

    elif (
        rsi < 40
        and price < ema9
        and ema9 < ema20
    ):
        return "Strong Negative"

    elif rsi < 50:
        return "Negative"

    else:
        return "Neutral"


def determine_breakout(row):
    """
    Identify basic breakout conditions.
    """

    price = row["Close"]
    resistance = row["Resistance"]

    volume_ratio = row["Volume_Ratio"]

    if (
        price > resistance
        and volume_ratio >= 1.5
    ):
        return "Confirmed Breakout"

    elif price > resistance:
        return "Breakout - Volume Confirmation Required"

    elif (
        price >= resistance * 0.98
        and volume_ratio >= 1.2
    ):
        return "Near Breakout"

    else:
        return "No Breakout"


def calculate_technical_indicators(data):
    """
    Main technical calculation function.

    Input:
        Historical OHLCV dataframe

    Output:
        Same dataframe with technical indicators.
    """

    if data is None or data.empty:
        return pd.DataFrame()

    data = data.copy()

    # --------------------------------------------------------
    # Moving Averages
    # --------------------------------------------------------

    data["SMA20"] = calculate_sma(data, 20)
    data["SMA50"] = calculate_sma(data, 50)
    data["SMA100"] = calculate_sma(data, 100)
    data["SMA200"] = calculate_sma(data, 200)

    # --------------------------------------------------------
    # Exponential Moving Averages
    # --------------------------------------------------------

    data["EMA9"] = calculate_ema(data, 9)
    data["EMA20"] = calculate_ema(data, 20)
    data["EMA50"] = calculate_ema(data, 50)

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    data["RSI14"] = calculate_rsi(data, 14)

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    data["ATR14"] = calculate_atr(data, 14)

    data["ATR_Percent"] = (
        data["ATR14"] / data["Close"]
    ) * 100

    # --------------------------------------------------------
    # Volume
    # --------------------------------------------------------

    data["Average_Volume_20"] = (
        data["Volume"].rolling(20).mean()
    )

    data["Volume_Ratio"] = calculate_volume_ratio(
        data,
        20
    )

    # --------------------------------------------------------
    # 52-Week High / Low
    # --------------------------------------------------------

    data["52W_High"] = calculate_52_week_high(data)

    data["52W_Low"] = calculate_52_week_low(data)

    data["Distance_From_52W_High_Pct"] = (
        calculate_distance_from_high(data)
    )

    data["Distance_From_52W_Low_Pct"] = (
        calculate_distance_from_low(data)
    )

    # --------------------------------------------------------
    # 200 DMA Position
    # --------------------------------------------------------

    data["Distance_From_200DMA_Pct"] = (
        calculate_distance_from_200dma(data)
    )

    data["Above_200DMA"] = (
        data["Close"] > data["SMA200"]
    )

    # --------------------------------------------------------
    # Support / Resistance
    # --------------------------------------------------------

    data["Support"] = calculate_support(
        data,
        20
    )

    data["Resistance"] = calculate_resistance(
        data,
        20
    )

    # --------------------------------------------------------
    # Trend
    # --------------------------------------------------------

    data["Trend"] = data.apply(
        determine_trend,
        axis=1
    )

    # --------------------------------------------------------
    # Momentum
    # --------------------------------------------------------

    data["Momentum"] = data.apply(
        determine_momentum,
        axis=1
    )

    # --------------------------------------------------------
    # Breakout
    # --------------------------------------------------------

    data["Breakout_Status"] = data.apply(
        determine_breakout,
        axis=1
    )

    return data


def get_latest_analysis(data):
    """
    Return the latest technical analysis
    as a dictionary.
    """

    if data is None or data.empty:
        return {}

    latest = data.iloc[-1]

    return {
        "price": latest["Close"],

        "previous_close": (
            data["Close"].iloc[-2]
            if len(data) > 1
            else np.nan
        ),

        "sma20": latest["SMA20"],
        "sma50": latest["SMA50"],
        "sma100": latest["SMA100"],
        "sma200": latest["SMA200"],

        "ema9": latest["EMA9"],
        "ema20": latest["EMA20"],
        "ema50": latest["EMA50"],

        "rsi14": latest["RSI14"],

        "atr14": latest["ATR14"],
        "atr_percent": latest["ATR_Percent"],

        "volume": latest["Volume"],
        "average_volume_20": (
            latest["Average_Volume_20"]
        ),
        "volume_ratio": latest["Volume_Ratio"],

        "52w_high": latest["52W_High"],
        "52w_low": latest["52W_Low"],

        "distance_from_52w_high_pct": (
            latest["Distance_From_52W_High_Pct"]
        ),

        "distance_from_52w_low_pct": (
            latest["Distance_From_52W_Low_Pct"]
        ),

        "distance_from_200dma_pct": (
            latest["Distance_From_200DMA_Pct"]
        ),

        "above_200dma": latest["Above_200DMA"],

        "support": latest["Support"],
        "resistance": latest["Resistance"],

        "trend": latest["Trend"],
        "momentum": latest["Momentum"],
        "breakout_status": latest["Breakout_Status"]
    }


if __name__ == "__main__":

    print("=" * 60)
    print("NSE SMART MARKET DASHBOARD")
    print("TECHNICAL ENGINE")
    print("=" * 60)

    print()
    print("Technical Engine loaded successfully.")
    print()
    print("Indicators:")
    print("- SMA 20 / 50 / 100 / 200")
    print("- EMA 9 / 20 / 50")
    print("- RSI 14")
    print("- ATR 14")
    print("- ATR %")
    print("- Volume Ratio")
    print("- 52-Week High / Low")
    print("- Distance from 52-Week High")
    print("- Distance from 200 DMA")
    print("- Support / Resistance")
    print("- Trend")
    print("- Momentum")
    print("- Breakout Status")
