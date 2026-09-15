import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET ENGINE
# ============================================================

INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX"
}


def download_data(symbol, period="1y"):
    """
    Download historical daily data from Yahoo Finance.
    """

    try:
        data = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if data is None or data.empty:
            return pd.DataFrame()

        # Handle MultiIndex columns returned by yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()

        return data

    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return pd.DataFrame()


def calculate_indicators(data):
    """
    Calculate major market indicators.
    """

    if data.empty:
        return data

    close = data["Close"]

    data["SMA20"] = close.rolling(20).mean()
    data["SMA50"] = close.rolling(50).mean()
    data["SMA100"] = close.rolling(100).mean()
    data["SMA200"] = close.rolling(200).mean()

    data["EMA20"] = close.ewm(span=20, adjust=False).mean()
    data["EMA50"] = close.ewm(span=50, adjust=False).mean()

    # RSI 14
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    data["RSI14"] = 100 - (100 / (1 + rs))

    return data


def get_latest_values(data):
    """
    Extract the latest market values.
    """

    if data.empty:
        return {}

    latest = data.iloc[-1]

    return {
        "price": float(latest["Close"]),
        "sma20": float(latest["SMA20"]),
        "sma50": float(latest["SMA50"]),
        "sma100": float(latest["SMA100"]),
        "sma200": float(latest["SMA200"]),
        "ema20": float(latest["EMA20"]),
        "ema50": float(latest["EMA50"]),
        "rsi14": float(latest["RSI14"])
    }


def determine_trend(values):
    """
    Determine broad market trend using price and moving averages.
    """

    price = values["price"]
    sma20 = values["sma20"]
    sma50 = values["sma50"]
    sma200 = values["sma200"]

    score = 0

    # Price position
    if price > sma20:
        score += 1

    if price > sma50:
        score += 1

    if price > sma200:
        score += 2

    # Moving average structure
    if sma20 > sma50:
        score += 1

    if sma50 > sma200:
        score += 2

    if score >= 6:
        return "Bullish", score

    elif score >= 4:
        return "Bullish but Cautious", score

    elif score >= 2:
        return "Sideways / Weak", score

    else:
        return "Bearish", score


def determine_momentum(values):
    """
    Determine market momentum using RSI and EMA structure.
    """

    rsi = values["rsi14"]

    price = values["price"]
    ema20 = values["ema20"]
    ema50 = values["ema50"]

    score = 0

    if price > ema20:
        score += 1

    if price > ema50:
        score += 1

    if ema20 > ema50:
        score += 1

    if 50 <= rsi <= 70:
        score += 2

    elif rsi > 70:
        score += 1

    elif rsi < 40:
        score -= 2

    elif rsi < 50:
        score -= 1

    if score >= 4:
        return "Strong", score

    elif score >= 2:
        return "Positive", score

    elif score >= 0:
        return "Neutral", score

    else:
        return "Weak", score


def calculate_market_score(trend_score, momentum_score):
    """
    Combine trend and momentum into a market score.
    """

    # Normalize roughly to a 100-point scale
    trend_component = (trend_score / 7) * 60
    momentum_component = ((momentum_score + 2) / 7) * 40

    score = trend_component + momentum_component

    return round(max(0, min(100, score)), 2)


def get_market_regime():
    """
    Main function.
    Downloads NIFTY, BANK NIFTY and INDIA VIX
    and creates the overall market regime.
    """

    results = {}

    # --------------------------------------------------------
    # NIFTY 50
    # --------------------------------------------------------

    nifty = download_data(INDEXES["NIFTY 50"])

    if not nifty.empty:

        nifty = calculate_indicators(nifty)

        values = get_latest_values(nifty)

        trend, trend_score = determine_trend(values)

        momentum, momentum_score = determine_momentum(values)

        market_score = calculate_market_score(
            trend_score,
            momentum_score
        )

        results["NIFTY 50"] = {
            **values,
            "trend": trend,
            "trend_score": trend_score,
            "momentum": momentum,
            "momentum_score": momentum_score,
            "market_score": market_score
        }

    # --------------------------------------------------------
    # BANK NIFTY
    # --------------------------------------------------------

    banknifty = download_data(INDEXES["BANK NIFTY"])

    if not banknifty.empty:

        banknifty = calculate_indicators(banknifty)

        values = get_latest_values(banknifty)

        trend, trend_score = determine_trend(values)

        momentum, momentum_score = determine_momentum(values)

        market_score = calculate_market_score(
            trend_score,
            momentum_score
        )

        results["BANK NIFTY"] = {
            **values,
            "trend": trend,
            "trend_score": trend_score,
            "momentum": momentum,
            "momentum_score": momentum_score,
            "market_score": market_score
        }

    # --------------------------------------------------------
    # INDIA VIX
    # --------------------------------------------------------

    vix = download_data(INDEXES["INDIA VIX"])

    if not vix.empty:

        vix_latest = float(vix["Close"].iloc[-1])

        results["INDIA VIX"] = {
            "value": vix_latest
        }

    # --------------------------------------------------------
    # OVERALL MARKET REGIME
    # --------------------------------------------------------

    nifty_score = results.get("NIFTY 50", {}).get(
        "market_score", 50
    )

    bank_score = results.get("BANK NIFTY", {}).get(
        "market_score", 50
    )

    overall_score = round(
        (nifty_score * 0.70) +
        (bank_score * 0.30),
        2
    )

    if overall_score >= 70:
        regime = "Bullish"

    elif overall_score >= 60:
        regime = "Bullish but Cautious"

    elif overall_score >= 45:
        regime = "Sideways"

    elif overall_score >= 30:
        regime = "Weak"

    else:
        regime = "Bearish"

    results["MARKET"] = {
        "regime": regime,
        "market_score": overall_score
    }

    return results


if __name__ == "__main__":

    market = get_market_regime()

    print("\n" + "=" * 60)
    print("NSE SMART MARKET DASHBOARD")
    print("MARKET ENGINE")
    print("=" * 60)

    for name, data in market.items():

        print(f"\n{name}")

        for key, value in data.items():
            print(f"{key}: {value}")

    print("\n" + "=" * 60)
