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

    return 100 - (100 / (1 + rs))


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

    return true_range.rolling(period).mean()


def calculate_volume_ratio(data, period=20):
    """Calculate current volume compared with average volume."""

    average_volume = data["Volume"].rolling(period).mean()

    return data["Volume"] / average_volume


def calculate_52_week_high(data):
    """
    Calculate rolling 52-week high.

    252 trading sessions are approximately one trading year.
    """

    return data["High"].rolling(252).max()


def calculate_52_week_low(data):
    """
    Calculate rolling 52-week low.
    """

    return data["Low"].rolling(252).min()


def calculate_distance_from_high(data):
    """Distance of current price from 52-week high in percentage."""

    return (
        (data["Close"] - data["52W_High"])
        / data["52W_High"]
    ) * 100


def calculate_distance_from_low(data):
    """Distance of current price from 52-week low in percentage."""

    return (
        (data["Close"] - data["52W_Low"])
        / data["52W_Low"]
    ) * 100


def calculate_distance_from_200dma(data):
    """Distance of current price from 200 DMA in percentage."""

    return (
        (data["Close"] - data["SMA200"])
        / data["SMA200"]
    ) * 100


def calculate_support(data, lookback=20):
    """
    Basic support based on previous trading sessions.

    Current day's low is excluded.
    """

    return (
        data["Low"]
        .rolling(lookback)
        .min()
        .shift(1)
    )


def calculate_resistance(data, lookback=20):
    """
    Basic resistance based on previous trading sessions.

    Current day's high is excluded.
    """

    return (
        data["High"]
        .rolling(lookback)
        .max()
        .shift(1)
    )


def determine_trend(row):
    """
    Determine broad price trend using
    price + SMA structure.
    """

    price = row["Close"]

    sma20 = row["SMA20"]
    sma50 = row["SMA50"]
    sma200 = row["SMA200"]

    if pd.isna(sma200):
        return "Insufficient Data"

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

    if pd.isna(rsi):
        return "Insufficient Data"

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
    Determine basic price breakout status.

    Resistance is based on previous sessions,
    so the current price can genuinely break it.
    """

    price = row["Close"]
    resistance = row["Resistance"]
    volume_ratio = row["Volume_Ratio"]

    if pd.isna(resistance):
        return "Insufficient Data"

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
        Dataframe containing technical indicators.
    """

    if data is None or data.empty:
        return pd.DataFrame()

    data = data.copy()

    # ========================================================
    # PRICE
    # ========================================================

    data["Previous_Close"] = data["Close"].shift(1)

    data["Daily_Return_Pct"] = (
        data["Close"].pct_change() * 100
    )

    # ========================================================
    # SIMPLE MOVING AVERAGES
    # ========================================================

    data["SMA20"] = calculate_sma(data, 20)

    data["SMA50"] = calculate_sma(data, 50)

    data["SMA100"] = calculate_sma(data, 100)

    data["SMA200"] = calculate_sma(data, 200)

    # ========================================================
    # EXPONENTIAL MOVING AVERAGES
    # ========================================================

    data["EMA9"] = calculate_ema(data, 9)

    data["EMA20"] = calculate_ema(data, 20)

    data["EMA50"] = calculate_ema(data, 50)

    # ========================================================
    # RSI
    # ========================================================

    data["RSI14"] = calculate_rsi(data, 14)

    # ========================================================
    # ATR
    # ========================================================

    data["ATR14"] = calculate_atr(data, 14)

    data["ATR_Percent"] = (
        data["ATR14"]
        / data["Close"]
    ) * 100

    # ========================================================
    # VOLUME
    # ========================================================

    data["Average_Volume_20"] = (
        data["Volume"].rolling(20).mean()
    )

    data["Volume_Ratio"] = calculate_volume_ratio(
        data,
        20
    )

    # ========================================================
    # 52-WEEK HIGH / LOW
    # ========================================================

    data["52W_High"] = calculate_52_week_high(data)

    data["52W_Low"] = calculate_52_week_low(data)

    data["Distance_From_52W_High_Pct"] = (
        calculate_distance_from_high(data)
    )

    data["Distance_From_52W_Low_Pct"] = (
        calculate_distance_from_low(data)
    )

    # ========================================================
    # 200 DMA POSITION
    # ========================================================

    data["Distance_From_200DMA_Pct"] = (
        calculate_distance_from_200dma(data)
    )

    data["Above_200DMA"] = (
        data["Close"] > data["SMA200"]
    )

    # ========================================================
    # SUPPORT / RESISTANCE
    # ========================================================

    data["Support"] = calculate_support(
        data,
        20
    )

    data["Resistance"] = calculate_resistance(
        data,
        20
    )

    # ========================================================
    # TREND
    # ========================================================

    data["Trend"] = data.apply(
        determine_trend,
        axis=1
    )

    # ========================================================
    # MOMENTUM
    # ========================================================

    data["Momentum"] = data.apply(
        determine_momentum,
        axis=1
    )

    # ========================================================
    # BREAKOUT
    # ========================================================

    data["Breakout_Status"] = data.apply(
        determine_breakout,
        axis=1
    )

    return data


def get_latest_analysis(data):
    """
    Extract the latest technical analysis
    as a dictionary.
    """

    if data is None or data.empty:
        return {}

    latest = data.iloc[-1]

    previous_close = (
        data["Close"].iloc[-2]
        if len(data) > 1
        else np.nan
    )

    return {

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        "price": latest["Close"],

        "previous_close": previous_close,

        "daily_return_pct": latest["Daily_Return_Pct"],

        # ----------------------------------------------------
        # SMA
        # ----------------------------------------------------

        "sma20": latest["SMA20"],

        "sma50": latest["SMA50"],

        "sma100": latest["SMA100"],

        "sma200": latest["SMA200"],

        # ----------------------------------------------------
        # EMA
        # ----------------------------------------------------

        "ema9": latest["EMA9"],

        "ema20": latest["EMA20"],

        "ema50": latest["EMA50"],

        # ----------------------------------------------------
        # MOMENTUM
        # ----------------------------------------------------

        "rsi14": latest["RSI14"],

        # ----------------------------------------------------
        # VOLATILITY
        # ----------------------------------------------------

        "atr14": latest["ATR14"],

        "atr_percent": latest["ATR_Percent"],

        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        "volume": latest["Volume"],

        "average_volume_20": (
            latest["Average_Volume_20"]
        ),

        "volume_ratio": latest["Volume_Ratio"],

        # ----------------------------------------------------
        # 52 WEEK
        # ----------------------------------------------------

        "52w_high": latest["52W_High"],

        "52w_low": latest["52W_Low"],

        "distance_from_52w_high_pct": (
            latest["Distance_From_52W_High_Pct"]
        ),

        "distance_from_52w_low_pct": (
            latest["Distance_From_52W_Low_Pct"]
        ),

        # ----------------------------------------------------
        # 200 DMA
        # ----------------------------------------------------

        "distance_from_200dma_pct": (
            latest["Distance_From_200DMA_Pct"]
        ),

        "above_200dma": (
            latest["Above_200DMA"]
        ),

        # ----------------------------------------------------
        # SUPPORT / RESISTANCE
        # ----------------------------------------------------

        "support": latest["Support"],

        "resistance": latest["Resistance"],

        # ----------------------------------------------------
        # CLASSIFICATION
        # ----------------------------------------------------

        "trend": latest["Trend"],

        "momentum": latest["Momentum"],

        "breakout_status": (
            latest["Breakout_Status"]
        )
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print("NSE SMART MARKET DASHBOARD")

    print("TECHNICAL ENGINE")

    print("=" * 60)

    print()

    print("Technical Engine loaded successfully.")

    print()

    print("Indicators included:")

    print("- Previous Close")

    print("- Daily Return %")

    print("- SMA 20")

    print("- SMA 50")

    print("- SMA 100")

    print("- SMA 200")

    print("- EMA 9")

    print("- EMA 20")

    print("- EMA 50")

    print("- RSI 14")

    print("- ATR 14")

    print("- ATR %")

    print("- Volume")

    print("- Average Volume 20")

    print("- Volume Ratio")

    print("- 52-Week High")

    print("- 52-Week Low")

    print("- Distance from 52-Week High")

    print("- Distance from 52-Week Low")

    print("- Distance from 200 DMA")

    print("- Above 200 DMA")

    print("- Support")

    print("- Resistance")

    print("- Trend")

    print("- Momentum")

    print("- Breakout Status")

    print()

    print("=" * 60)
