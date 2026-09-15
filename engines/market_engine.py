import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET REGIME ENGINE — V2
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX"
}


# ============================================================
# DOWNLOAD DATA
# ============================================================

def download_data(symbol, period="2y"):

    try:
        data = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        return data

    except Exception as e:

        print(f"Unable to download {symbol}: {e}")

        return pd.DataFrame()


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_indicators(data):

    if data.empty:
        return data

    data = data.copy()

    close = data["Close"]

    data["SMA20"] = close.rolling(20).mean()
    data["SMA50"] = close.rolling(50).mean()
    data["SMA100"] = close.rolling(100).mean()
    data["SMA200"] = close.rolling(200).mean()

    data["EMA20"] = close.ewm(
        span=20,
        adjust=False
    ).mean()

    data["EMA50"] = close.ewm(
        span=50,
        adjust=False
    ).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    data["RSI14"] = 100 - (
        100 / (1 + rs)
    )

    return data


# ============================================================
# TREND
# ============================================================

def determine_trend(row):

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
        return "Strong Bullish"

    if (
        price > sma50
        and sma50 > sma200
    ):
        return "Bullish"

    if (
        price < sma20
        and sma20 < sma50
        and sma50 < sma200
    ):
        return "Strong Bearish"

    if price < sma200:
        return "Bearish"

    return "Neutral"


# ============================================================
# MOMENTUM
# ============================================================

def determine_momentum(row):

    rsi = row["RSI14"]
    price = row["Close"]

    ema20 = row["EMA20"]
    ema50 = row["EMA50"]

    if pd.isna(rsi):
        return "Insufficient Data"

    if (
        rsi >= 60
        and price > ema20
        and ema20 > ema50
    ):
        return "Strong Positive"

    if (
        rsi >= 50
        and price > ema20
    ):
        return "Positive"

    if (
        rsi < 40
        and price < ema20
        and ema20 < ema50
    ):
        return "Strong Negative"

    if rsi < 50:
        return "Weak"

    return "Neutral"


# ============================================================
# TREND SCORE
# ============================================================

def trend_score(trend):

    scores = {
        "Strong Bullish": 100,
        "Bullish": 80,
        "Neutral": 50,
        "Bearish": 25,
        "Strong Bearish": 0
    }

    return scores.get(trend, 50)


# ============================================================
# MOMENTUM SCORE
# ============================================================

def momentum_score(momentum):

    scores = {
        "Strong Positive": 100,
        "Positive": 75,
        "Neutral": 50,
        "Weak": 25,
        "Strong Negative": 0
    }

    return scores.get(momentum, 50)


# ============================================================
# INDEX ANALYSIS
# ============================================================

def analyze_index(name, symbol):

    data = download_data(symbol)

    if data.empty:
        return {
            "name": name,
            "symbol": symbol,
            "price": np.nan,
            "trend": "Unavailable",
            "momentum": "Unavailable",
            "rsi": np.nan,
            "score": 50
        }

    data = calculate_indicators(data)

    latest = data.iloc[-1]

    trend = determine_trend(latest)

    momentum = determine_momentum(latest)

    t_score = trend_score(trend)

    m_score = momentum_score(momentum)

    score = (
        t_score * 0.60
        + m_score * 0.40
    )

    return {
        "name": name,
        "symbol": symbol,
        "price": float(latest["Close"]),
        "trend": trend,
        "momentum": momentum,
        "rsi": round(float(latest["RSI14"]), 2)
        if not pd.isna(latest["RSI14"])
        else np.nan,
        "score": round(score, 2)
    }


# ============================================================
# VIX INTERPRETATION
# ============================================================

def interpret_vix(vix):

    if pd.isna(vix):
        return "Unavailable"

    if vix < 12:
        return "Very Low"

    if vix < 15:
        return "Low"

    if vix < 20:
        return "Normal"

    if vix < 25:
        return "High"

    return "Very High"


# ============================================================
# MARKET REGIME
# ============================================================

def determine_market_regime(
    nifty_score,
    bank_score,
    breadth_score,
    vix
):

    # --------------------------------------------------------
    # Core market score
    # --------------------------------------------------------

    base_score = (
        nifty_score * 0.40
        + bank_score * 0.20
        + breadth_score * 0.40
    )

    # --------------------------------------------------------
    # VIX risk adjustment
    # --------------------------------------------------------

    vix_adjustment = 0

    if not pd.isna(vix):

        if vix >= 25:
            vix_adjustment = -10

        elif vix >= 20:
            vix_adjustment = -5

        elif vix < 12:
            vix_adjustment = 2

    market_score = base_score + vix_adjustment

    market_score = round(
        max(0, min(100, market_score)),
        2
    )

    # --------------------------------------------------------
    # Market regime
    # --------------------------------------------------------

    if market_score >= 70:

        regime = "Bullish"

    elif market_score >= 58:

        regime = "Bullish but Cautious"

    elif market_score >= 45:

        regime = "Sideways"

    elif market_score >= 30:

        regime = "Weak"

    else:

        regime = "Bearish"

    return regime, market_score


# ============================================================
# TRADING ENVIRONMENT
# ============================================================

def determine_trading_environment(
    regime,
    breadth_score,
    vix
):

    if regime == "Bullish":

        return {
            "equity": "Favorable",
            "swing": "Favorable",
            "breakout": "Favorable",
            "intraday": "Favorable",
            "options": "Selective"
        }

    if regime == "Bullish but Cautious":

        return {
            "equity": "Selective",
            "swing": "Selective",
            "breakout": "Selective",
            "intraday": "Selective",
            "options": "Selective"
        }

    if regime == "Sideways":

        return {
            "equity": "Selective",
            "swing": "Selective",
            "breakout": "Confirmation Required",
            "intraday": "Selective",
            "options": "Risky"
        }

    if regime == "Weak":

        return {
            "equity": "Cautious",
            "swing": "Cautious",
            "breakout": "Avoid Weak Breakouts",
            "intraday": "Selective",
            "options": "High Risk"
        }

    return {
        "equity": "Defensive",
        "swing": "Avoid",
        "breakout": "Avoid",
        "intraday": "Selective",
        "options": "Very High Risk"
    }


# ============================================================
# MAIN MARKET REGIME FUNCTION
# ============================================================

def get_market_regime(breadth=None):

    print()
    print("=" * 60)
    print("MARKET REGIME ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # NIFTY
    # --------------------------------------------------------

    nifty = analyze_index(
        "NIFTY 50",
        INDEXES["NIFTY 50"]
    )

    # --------------------------------------------------------
    # BANK NIFTY
    # --------------------------------------------------------

    bank = analyze_index(
        "BANK NIFTY",
        INDEXES["BANK NIFTY"]
    )

    # --------------------------------------------------------
    # INDIA VIX
    # --------------------------------------------------------

    vix_data = download_data(
        INDEXES["INDIA VIX"]
    )

    if vix_data.empty:

        vix = np.nan

    else:

        vix = float(vix_data["Close"].iloc[-1])

    vix_interpretation = interpret_vix(vix)

    # --------------------------------------------------------
    # BREADTH
    # --------------------------------------------------------

    if breadth:

        breadth_score = float(
            breadth.get(
                "breadth_score",
                50
            )
        )

    else:

        breadth_score = 50

    # --------------------------------------------------------
    # COMBINED MARKET REGIME
    # --------------------------------------------------------

    regime, market_score = determine_market_regime(
        nifty["score"],
        bank["score"],
        breadth_score,
        vix
    )

    # --------------------------------------------------------
    # TRADING ENVIRONMENT
    # --------------------------------------------------------

    trading_environment = determine_trading_environment(
        regime,
        breadth_score,
        vix
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "market_regime": regime,

        "market_score": market_score,

        "nifty_score": nifty["score"],

        "bank_nifty_score": bank["score"],

        "breadth_score": breadth_score,

        "vix": round(vix, 2)
        if not pd.isna(vix)
        else np.nan,

        "vix_interpretation": vix_interpretation,

        "nifty_price": nifty["price"],

        "nifty_trend": nifty["trend"],

        "nifty_momentum": nifty["momentum"],

        "nifty_rsi": nifty["rsi"],

        "bank_nifty_price": bank["price"],

        "bank_nifty_trend": bank["trend"],

        "bank_nifty_momentum": bank["momentum"],

        "bank_nifty_rsi": bank["rsi"],

        "equity_environment":
            trading_environment["equity"],

        "swing_environment":
            trading_environment["swing"],

        "breakout_environment":
            trading_environment["breakout"],

        "intraday_environment":
            trading_environment["intraday"],

        "options_environment":
            trading_environment["options"]
    }

    return result


# ============================================================
# DISPLAY
# ============================================================

def display_market(market):

    if not market:
        return

    print()
    print("=" * 60)
    print("MARKET REGIME SUMMARY")
    print("=" * 60)
    print()

    print(
        f"Market Regime        : "
        f"{market['market_regime']}"
    )

    print(
        f"Market Score         : "
        f"{market['market_score']}"
    )

    print(
        f"Nifty Score          : "
        f"{market['nifty_score']}"
    )

    print(
        f"Bank Nifty Score     : "
        f"{market['bank_nifty_score']}"
    )

    print(
        f"Breadth Score        : "
        f"{market['breadth_score']}"
    )

    print(
        f"India VIX            : "
        f"{market['vix']}"
    )

    print(
        f"VIX Interpretation   : "
        f"{market['vix_interpretation']}"
    )

    print()

    print(
        f"Equity Environment   : "
        f"{market['equity_environment']}"
    )

    print(
        f"Swing Environment     : "
        f"{market['swing_environment']}"
    )

    print(
        f"Breakout Environment : "
        f"{market['breakout_environment']}"
    )

    print(
        f"Intraday Environment  : "
        f"{market['intraday_environment']}"
    )

    print(
        f"Options Environment   : "
        f"{market['options_environment']}"
    )

    print()

    print("=" * 60)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    market = get_market_regime()

    display_market(market)
