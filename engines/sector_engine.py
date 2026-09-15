import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# SECTOR ENGINE — V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

SECTOR_FILE = OUTPUT_DIR / "sector_analysis.csv"


# ============================================================
# NSE SECTOR REPRESENTATIVE SYMBOLS
# ============================================================

SECTOR_INDEXES = {
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY FINANCIAL SERVICES": "^CNXFIN",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY IT": "^CNXIT",
    "NIFTY MEDIA": "^CNXMEDIA",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "NIFTY PRIVATE BANK": "^NIFTYPVTBANK",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY INFRASTRUCTURE": "^CNXINFRA",
    "NIFTY PSE": "^CNXPSE",
    "NIFTY CONSUMPTION": "^CNXCONSUM",
    "NIFTY COMMODITIES": "^CNXCOMMODITIES",
    "NIFTY MNC": "^CNXMNC",
    "NIFTY SERVICES SECTOR": "^CNXSERVICE",
    "NIFTY HEALTHCARE": "^CNXHEALTHCARE",
    "NIFTY OIL & GAS": "^CNXOILGAS",
    "NIFTY INDIA DEFENCE": "^NIFTYINDIADEFENCE"
}


# ============================================================
# DOWNLOAD DATA
# ============================================================

def download_sector_data(symbol, period="1y"):

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

        print(
            f"Unable to download sector data "
            f"{symbol}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_sector_indicators(data):

    if data.empty:
        return data

    data = data.copy()

    close = data["Close"]

    data["SMA20"] = close.rolling(20).mean()
    data["SMA50"] = close.rolling(50).mean()
    data["SMA200"] = close.rolling(200).mean()

    data["EMA20"] = close.ewm(
        span=20,
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

    data["Return_20D"] = (
        close.pct_change(20) * 100
    )

    data["Return_60D"] = (
        close.pct_change(60) * 100
    )

    return data


# ============================================================
# TREND CLASSIFICATION
# ============================================================

def determine_sector_trend(row):

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

    if (
        price > sma50
        and sma50 > sma200
    ):
        return "Uptrend"

    if (
        price < sma20
        and sma20 < sma50
        and sma50 < sma200
    ):
        return "Strong Downtrend"

    if price < sma200:
        return "Downtrend"

    return "Sideways"


# ============================================================
# MOMENTUM CLASSIFICATION
# ============================================================

def determine_sector_momentum(row):

    rsi = row["RSI14"]
    return_20d = row["Return_20D"]
    return_60d = row["Return_60D"]

    if pd.isna(rsi):
        return "Insufficient Data"

    if (
        rsi >= 60
        and return_20d > 0
        and return_60d > 0
    ):
        return "Strong Positive"

    if (
        rsi >= 50
        and return_20d > 0
    ):
        return "Positive"

    if (
        rsi < 40
        and return_20d < 0
        and return_60d < 0
    ):
        return "Strong Negative"

    if rsi < 50:
        return "Negative"

    return "Neutral"


# ============================================================
# TREND SCORE
# ============================================================

def calculate_trend_score(trend):

    scores = {
        "Strong Uptrend": 100,
        "Uptrend": 80,
        "Sideways": 50,
        "Downtrend": 25,
        "Strong Downtrend": 0
    }

    return scores.get(trend, 50)


# ============================================================
# MOMENTUM SCORE
# ============================================================

def calculate_momentum_score(momentum):

    scores = {
        "Strong Positive": 100,
        "Positive": 75,
        "Neutral": 50,
        "Negative": 25,
        "Strong Negative": 0
    }

    return scores.get(momentum, 50)


# ============================================================
# SECTOR SCORE
# ============================================================

def calculate_sector_score(
    trend,
    momentum,
    return_20d,
    return_60d
):

    trend_score = calculate_trend_score(trend)

    momentum_score = calculate_momentum_score(momentum)

    # Recent performance component
    performance_score = 50

    if not pd.isna(return_20d):

        if return_20d >= 10:
            performance_score = 100

        elif return_20d >= 5:
            performance_score = 85

        elif return_20d >= 2:
            performance_score = 70

        elif return_20d >= 0:
            performance_score = 55

        elif return_20d >= -5:
            performance_score = 35

        elif return_20d >= -10:
            performance_score = 20

        else:
            performance_score = 0

    # Final score
    score = (
        trend_score * 0.45
        + momentum_score * 0.35
        + performance_score * 0.20
    )

    return round(score, 2)


# ============================================================
# SECTOR CLASSIFICATION
# ============================================================

def classify_sector(score):

    if score >= 75:
        return "Leading"

    if score >= 60:
        return "Strong"

    if score >= 45:
        return "Neutral"

    if score >= 30:
        return "Weak"

    return "Lagging"


# ============================================================
# SECTOR ANALYSIS
# ============================================================

def analyze_sector(name, symbol):

    data = download_sector_data(symbol)

    if data.empty:
        return None

    data = calculate_sector_indicators(data)

    if len(data) < 200:
        return None

    latest = data.iloc[-1]

    trend = determine_sector_trend(latest)

    momentum = determine_sector_momentum(latest)

    return_20d = latest["Return_20D"]

    return_60d = latest["Return_60D"]

    score = calculate_sector_score(
        trend,
        momentum,
        return_20d,
        return_60d
    )

    classification = classify_sector(score)

    return {
        "sector": name,
        "symbol": symbol,
        "price": round(
            float(latest["Close"]),
            2
        ),
        "sma20": round(
            float(latest["SMA20"]),
            2
        ),
        "sma50": round(
            float(latest["SMA50"]),
            2
        ),
        "sma200": round(
            float(latest["SMA200"]),
            2
        ),
        "rsi14": round(
            float(latest["RSI14"]),
            2
        ),
        "return_20d_pct": round(
            float(return_20d),
            2
        ),
        "return_60d_pct": round(
            float(return_60d),
            2
        ),
        "trend": trend,
        "momentum": momentum,
        "sector_score": score,
        "classification": classification
    }


# ============================================================
# ANALYZE ALL SECTORS
# ============================================================

def analyze_all_sectors():

    results = []

    print()
    print("=" * 60)
    print("SECTOR ANALYSIS")
    print("=" * 60)

    total = len(SECTOR_INDEXES)

    for number, (name, symbol) in enumerate(
        SECTOR_INDEXES.items(),
        start=1
    ):

        print(
            f"[{number}/{total}] "
            f"Analyzing {name}..."
        )

        result = analyze_sector(
            name,
            symbol
        )

        if result is not None:
            results.append(result)

    if not results:

        return pd.DataFrame()

    df = pd.DataFrame(results)

    df = df.sort_values(
        "sector_score",
        ascending=False
    ).reset_index(drop=True)

    df["sector_rank"] = (
        df.index + 1
    )

    return df


# ============================================================
# SAVE SECTOR ANALYSIS
# ============================================================

def save_sector_analysis(df):

    if df is None or df.empty:
        print("No sector data available.")
        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        SECTOR_FILE,
        index=False
    )

    print()
    print(
        f"Saved sector analysis: "
        f"{SECTOR_FILE}"
    )


# ============================================================
# DISPLAY
# ============================================================

def display_sector_analysis(df):

    if df is None or df.empty:
        return

    print()
    print("=" * 60)
    print("SECTOR STRENGTH")
    print("=" * 60)
    print()

    columns = [
        "sector_rank",
        "sector",
        "sector_score",
        "classification",
        "trend",
        "momentum",
        "return_20d_pct",
        "return_60d_pct",
        "rsi14"
    ]

    print(
        df[columns].to_string(
            index=False
        )
    )

    print()
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def get_sector_analysis():

    df = analyze_all_sectors()

    if df.empty:

        print(
            "No sector analysis available."
        )

        return df

    save_sector_analysis(df)

    display_sector_analysis(df)

    return df


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    sector_data = get_sector_analysis()

    if not sector_data.empty:

        print()
        print(
            "Sector engine test completed."
        )
