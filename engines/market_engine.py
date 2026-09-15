import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET INTELLIGENCE ENGINE
# ============================================================


INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX"
}


# ============================================================
# DOWNLOAD DATA
# ============================================================

def download_data(
    symbol,
    period="2y"
):

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

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            data.columns = (
                data.columns
                .get_level_values(0)
            )

        data = data.dropna()

        return data

    except Exception as e:

        print(
            f"Error downloading {symbol}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# INDICATORS
# ============================================================

def calculate_indicators(data):

    if data.empty:

        return data

    close = data["Close"]

    data["SMA20"] = (
        close.rolling(20).mean()
    )

    data["SMA50"] = (
        close.rolling(50).mean()
    )

    data["SMA100"] = (
        close.rolling(100).mean()
    )

    data["SMA200"] = (
        close.rolling(200).mean()
    )

    data["EMA20"] = (
        close.ewm(
            span=20,
            adjust=False
        ).mean()
    )

    data["EMA50"] = (
        close.ewm(
            span=50,
            adjust=False
        ).mean()
    )

    # --------------------------------------------------------
    # RSI 14
    # --------------------------------------------------------

    delta = close.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = (
        gain.rolling(14).mean()
    )

    avg_loss = (
        loss.rolling(14).mean()
    )

    rs = (
        avg_gain
        / avg_loss.replace(
            0,
            np.nan
        )
    )

    data["RSI14"] = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    return data


# ============================================================
# LATEST VALUES
# ============================================================

def get_latest_values(data):

    if data.empty:

        return {}

    latest = data.iloc[-1]

    return {

        "price": float(
            latest["Close"]
        ),

        "sma20": float(
            latest["SMA20"]
        ),

        "sma50": float(
            latest["SMA50"]
        ),

        "sma100": float(
            latest["SMA100"]
        ),

        "sma200": float(
            latest["SMA200"]
        ),

        "ema20": float(
            latest["EMA20"]
        ),

        "ema50": float(
            latest["EMA50"]
        ),

        "rsi14": float(
            latest["RSI14"]
        )
    }


# ============================================================
# INDEX TREND
# ============================================================

def determine_trend(values):

    price = values["price"]

    sma20 = values["sma20"]

    sma50 = values["sma50"]

    sma200 = values["sma200"]

    score = 0

    if price > sma20:
        score += 1

    if price > sma50:
        score += 1

    if price > sma200:
        score += 2

    if sma20 > sma50:
        score += 1

    if sma50 > sma200:
        score += 2

    if score >= 6:

        return "Strong Bullish", score

    elif score >= 4:

        return "Bullish", score

    elif score >= 2:

        return "Neutral / Weak", score

    else:

        return "Bearish", score


# ============================================================
# INDEX MOMENTUM
# ============================================================

def determine_momentum(values):

    price = values["price"]

    ema20 = values["ema20"]

    ema50 = values["ema50"]

    rsi = values["rsi14"]

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

        return "Strong Positive", score

    elif score >= 2:

        return "Positive", score

    elif score >= 0:

        return "Neutral", score

    else:

        return "Weak", score


# ============================================================
# INDEX SCORE
# ============================================================

def calculate_index_score(
    trend_score,
    momentum_score
):

    # Trend = 60%
    trend_component = (
        trend_score / 7
    ) * 60

    # Momentum = 40%
    momentum_component = (
        (momentum_score + 2) / 7
    ) * 40

    score = (
        trend_component
        + momentum_component
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
# VIX INTERPRETATION
# ============================================================

def interpret_vix(vix):

    if pd.isna(vix):

        return "Unavailable"

    if vix < 12:

        return "Very Low Volatility"

    elif vix < 15:

        return "Low Volatility"

    elif vix < 20:

        return "Normal Volatility"

    elif vix < 25:

        return "High Volatility"

    else:

        return "Very High Volatility"


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
    # Combined components
    #
    # Nifty      = 40%
    # Bank Nifty = 20%
    # Breadth    = 40%
    # --------------------------------------------------------

    combined_score = (
        nifty_score * 0.40
        +
        bank_score * 0.20
        +
        breadth_score * 0.40
    )

    # --------------------------------------------------------
    # VIX adjustment
    #
    # High volatility reduces confidence.
    # Low volatility does not artificially increase score.
    # --------------------------------------------------------

    if not pd.isna(vix):

        if vix >= 25:

            combined_score -= 8

        elif vix >= 20:

            combined_score -= 4

    combined_score = round(
        max(
            0,
            min(
                100,
                combined_score
            )
        ),
        2
    )

    # --------------------------------------------------------
    # Regime
    # --------------------------------------------------------

    if combined_score >= 70:

        regime = "Bullish"

    elif combined_score >= 58:

        regime = "Bullish but Cautious"

    elif combined_score >= 45:

        regime = "Sideways"

    elif combined_score >= 30:

        regime = "Weak"

    else:

        regime = "Bearish"

    return (
        regime,
        combined_score
    )


# ============================================================
# MAIN MARKET ENGINE
# ============================================================

def get_market_regime(
    breadth=None
):

    results = {}

    # --------------------------------------------------------
    # NIFTY 50
    # --------------------------------------------------------

    nifty = download_data(
        INDEXES["NIFTY 50"]
    )

    if not nifty.empty:

        nifty = calculate_indicators(
            nifty
        )

        values = get_latest_values(
            nifty
        )

        trend, trend_score = (
            determine_trend(
                values
            )
        )

        momentum, momentum_score = (
            determine_momentum(
                values
            )
        )

        score = calculate_index_score(
            trend_score,
            momentum_score
        )

        results["NIFTY 50"] = {

            **values,

            "trend": trend,

            "trend_score": trend_score,

            "momentum": momentum,

            "momentum_score": momentum_score,

            "market_score": score
        }

    # --------------------------------------------------------
    # BANK NIFTY
    # --------------------------------------------------------

    banknifty = download_data(
        INDEXES["BANK NIFTY"]
    )

    if not banknifty.empty:

        banknifty = calculate_indicators(
            banknifty
        )

        values = get_latest_values(
            banknifty
        )

        trend, trend_score = (
            determine_trend(
                values
            )
        )

        momentum, momentum_score = (
            determine_momentum(
                values
            )
        )

        score = calculate_index_score(
            trend_score,
            momentum_score
        )

        results["BANK NIFTY"] = {

            **values,

            "trend": trend,

            "trend_score": trend_score,

            "momentum": momentum,

            "momentum_score": momentum_score,

            "market_score": score
        }

    # --------------------------------------------------------
    # INDIA VIX
    # --------------------------------------------------------

    vix = download_data(
        INDEXES["INDIA VIX"],
        period="1y"
    )

    vix_value = np.nan

    if not vix.empty:

        vix_value = float(
            vix["Close"].iloc[-1]
        )

        results["INDIA VIX"] = {

            "value": vix_value,

            "interpretation":
                interpret_vix(
                    vix_value
                )
        }

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

        results["MARKET BREADTH"] = {

            "stocks_analyzed":
                breadth.get(
                    "stocks_analyzed",
                    0
                ),

            "pct_above_20dma":
                breadth.get(
                    "pct_above_20dma",
                    0
                ),

            "pct_above_50dma":
                breadth.get(
                    "pct_above_50dma",
                    0
                ),

            "pct_above_200dma":
                breadth.get(
                    "pct_above_200dma",
                    0
                ),

            "52w_highs":
                breadth.get(
                    "52w_highs",
                    0
                ),

            "52w_lows":
                breadth.get(
                    "52w_lows",
                    0
                ),

            "high_low_ratio":
                breadth.get(
                    "high_low_ratio",
                    0
                ),

            "breadth_score":
                breadth_score,

            "breadth_regime":
                breadth.get(
                    "breadth_regime",
                    "Unknown"
                )
        }

    else:

        breadth_score = 50

    # --------------------------------------------------------
    # INDEX SCORES
    # --------------------------------------------------------

    nifty_score = results.get(
        "NIFTY 50",
        {}
    ).get(
        "market_score",
        50
    )

    bank_score = results.get(
        "BANK NIFTY",
        {}
    ).get(
        "market_score",
        50
    )

    # --------------------------------------------------------
    # OVERALL MARKET
    # --------------------------------------------------------

    regime, overall_score = (
        determine_market_regime(
            nifty_score,
            bank_score,
            breadth_score,
            vix_value
        )
    )

    results["MARKET"] = {

        "regime": regime,

        "market_score":
            overall_score,

        "nifty_score":
            nifty_score,

        "bank_nifty_score":
            bank_score,

        "breadth_score":
            breadth_score,

        "vix":
            vix_value,

        "vix_interpretation":
            interpret_vix(
                vix_value
            )
    }

    return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    market = get_market_regime()

    print()
    print("=" * 60)

    print(
        "NSE SMART MARKET DASHBOARD"
    )

    print(
        "MARKET INTELLIGENCE ENGINE"
    )

    print("=" * 60)

    for name, data in market.items():

        print()
        print(name)

        for key, value in data.items():

            print(
                f"{key}: {value}"
            )

    print()
    print("=" * 60)
