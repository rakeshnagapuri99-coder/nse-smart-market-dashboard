import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
from pathlib import Path


# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET REGIME ENGINE — V2
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INDEX SYMBOLS
# ============================================================

INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX"
}


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-IN,en;q=0.9"
})


# ============================================================
# CLEAN DATAFRAME
# ============================================================

def clean_dataframe(data):

    if data is None:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    data = data.copy()

    # Handle yfinance MultiIndex
    if isinstance(data.columns, pd.MultiIndex):

        data.columns = [
            column[0]
            if isinstance(column, tuple)
            else column
            for column in data.columns
        ]

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    # Make sure Close exists
    if "Close" not in data.columns:

        close_columns = [
            column
            for column in data.columns
            if str(column).lower() == "close"
        ]

        if close_columns:
            data["Close"] = data[close_columns[0]]

    if "Close" not in data.columns:
        return pd.DataFrame()

    data["Close"] = pd.to_numeric(
        data["Close"],
        errors="coerce"
    )

    data = data[
        data["Close"].notna()
    ].copy()

    return data


# ============================================================
# YFINANCE DOWNLOAD
# ============================================================

def download_yfinance(
    symbol,
    period="2y"
):

    try:

        print(
            f"Trying yfinance: {symbol}"
        )

        data = yf.download(
            symbol,
            period=period,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        data = clean_dataframe(data)

        if not data.empty:

            print(
                f"yfinance success: "
                f"{symbol} "
                f"({len(data)} rows)"
            )

            return data

        print(
            f"yfinance returned no data: "
            f"{symbol}"
        )

    except Exception as error:

        print(
            f"yfinance failed for "
            f"{symbol}: {error}"
        )

    return pd.DataFrame()


# ============================================================
# YAHOO CHART API FALLBACK
# ============================================================

def download_yahoo_chart(
    symbol,
    period_days=730
):

    print(
        f"Trying Yahoo Chart API: {symbol}"
    )

    end_time = int(
        time.time()
    )

    start_time = (
        end_time
        - period_days * 24 * 60 * 60
    )

    params = {
        "period1": start_time,
        "period2": end_time,
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true"
    }

    urls = [
        (
            "https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{symbol}"
        ),
        (
            "https://query2.finance.yahoo.com/"
            f"v8/finance/chart/{symbol}"
        )
    ]

    for url in urls:

        try:

            response = SESSION.get(
                url,
                params=params,
                timeout=30
            )

            if response.status_code != 200:

                print(
                    f"Yahoo API HTTP "
                    f"{response.status_code}: "
                    f"{symbol}"
                )

                continue

            payload = response.json()

            chart = payload.get(
                "chart",
                {}
            )

            results = chart.get(
                "result"
            )

            if not results:

                print(
                    f"Yahoo API returned "
                    f"no result: {symbol}"
                )

                continue

            result = results[0]

            timestamps = result.get(
                "timestamp"
            )

            indicators = result.get(
                "indicators",
                {}
            )

            quote_list = indicators.get(
                "quote",
                []
            )

            if not timestamps or not quote_list:
                continue

            quote = quote_list[0]

            closes = quote.get(
                "close",
                []
            )

            opens = quote.get(
                "open",
                []
            )

            highs = quote.get(
                "high",
                []
            )

            lows = quote.get(
                "low",
                []
            )

            volumes = quote.get(
                "volume",
                []
            )

            length = len(timestamps)

            def fill_values(values):

                if values is None:
                    return [np.nan] * length

                return values

            closes = fill_values(closes)
            opens = fill_values(opens)
            highs = fill_values(highs)
            lows = fill_values(lows)
            volumes = fill_values(volumes)

            data = pd.DataFrame({
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": volumes
            })

            data["Date"] = pd.to_datetime(
                timestamps,
                unit="s",
                utc=True
            )

            data["Date"] = (
                data["Date"]
                .dt.tz_convert("Asia/Kolkata")
                .dt.tz_localize(None)
            )

            data = data.set_index(
                "Date"
            )

            data = clean_dataframe(
                data
            )

            if not data.empty:

                print(
                    f"Yahoo Chart API success: "
                    f"{symbol} "
                    f"({len(data)} rows)"
                )

                return data

        except Exception as error:

            print(
                f"Yahoo Chart API failed: "
                f"{symbol}: {error}"
            )

    return pd.DataFrame()


# ============================================================
# DOWNLOAD DATA
# ============================================================

def download_data(
    symbol,
    period="2y"
):

    # Primary source
    data = download_yfinance(
        symbol,
        period
    )

    if not data.empty:
        return data

    # Fallback source
    data = download_yahoo_chart(
        symbol,
        period_days=730
    )

    if not data.empty:
        return data

    print(
        f"ERROR: No market data available "
        f"for {symbol}"
    )

    return pd.DataFrame()


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_indicators(data):

    if data.empty:
        return data

    data = data.copy()

    close = pd.to_numeric(
        data["Close"],
        errors="coerce"
    )

    # Moving averages
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

    # EMAs
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

    # Daily return
    data["Daily_Return_Pct"] = (
        close.pct_change() * 100
    )

    # RSI 14
    delta = close.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        14
    ).mean()

    avg_loss = loss.rolling(
        14
    ).mean()

    rs = (
        avg_gain /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    data["RSI14"] = (
        100 -
        (
            100 /
            (1 + rs)
        )
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

    if any(
        pd.isna(value)
        for value in [
            price,
            sma20,
            sma50,
            sma200
        ]
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

    if any(
        pd.isna(value)
        for value in [
            rsi,
            price,
            ema20,
            ema50
        ]
    ):
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
# SCORES
# ============================================================

def trend_score(trend):

    scores = {
        "Strong Bullish": 100,
        "Bullish": 80,
        "Neutral": 50,
        "Bearish": 25,
        "Strong Bearish": 0
    }

    return scores.get(
        trend,
        50
    )


def momentum_score(momentum):

    scores = {
        "Strong Positive": 100,
        "Positive": 75,
        "Neutral": 50,
        "Weak": 25,
        "Strong Negative": 0
    }

    return scores.get(
        momentum,
        50
    )


# ============================================================
# INDEX ANALYSIS
# ============================================================

def analyze_index(
    name,
    symbol
):

    print()
    print(
        f"Analysing {name} ({symbol})"
    )

    data = download_data(
        symbol
    )

    if data.empty:

        return {
            "name": name,
            "symbol": symbol,
            "price": np.nan,
            "previous_close": np.nan,
            "daily_return_pct": np.nan,
            "trend": "Unavailable",
            "momentum": "Unavailable",
            "rsi": np.nan,
            "sma20": np.nan,
            "sma50": np.nan,
            "sma100": np.nan,
            "sma200": np.nan,
            "ema20": np.nan,
            "ema50": np.nan,
            "score": 50
        }

    data = calculate_indicators(
        data
    )

    latest = data.iloc[-1]

    trend = determine_trend(
        latest
    )

    momentum = determine_momentum(
        latest
    )

    t_score = trend_score(
        trend
    )

    m_score = momentum_score(
        momentum
    )

    score = (
        t_score * 0.60
        +
        m_score * 0.40
    )

    previous_close = np.nan

    if len(data) >= 2:

        previous_close = float(
            data["Close"].iloc[-2]
        )

    def safe_float(value):

        try:

            if pd.isna(value):
                return np.nan

            return float(value)

        except Exception:

            return np.nan

    return {

        "name": name,

        "symbol": symbol,

        "price": safe_float(
            latest["Close"]
        ),

        "previous_close":
            previous_close,

        "daily_return_pct":
            safe_float(
                latest[
                    "Daily_Return_Pct"
                ]
            ),

        "trend": trend,

        "momentum": momentum,

        "rsi": safe_float(
            latest["RSI14"]
        ),

        "sma20": safe_float(
            latest["SMA20"]
        ),

        "sma50": safe_float(
            latest["SMA50"]
        ),

        "sma100": safe_float(
            latest["SMA100"]
        ),

        "sma200": safe_float(
            latest["SMA200"]
        ),

        "ema20": safe_float(
            latest["EMA20"]
        ),

        "ema50": safe_float(
            latest["EMA50"]
        ),

        "score": round(
            score,
            2
        )
    }


# ============================================================
# VIX
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

    base_score = (
        nifty_score * 0.40
        +
        bank_score * 0.20
        +
        breadth_score * 0.40
    )

    vix_adjustment = 0

    if not pd.isna(vix):

        if vix >= 25:
            vix_adjustment = -10

        elif vix >= 20:
            vix_adjustment = -5

        elif vix < 12:
            vix_adjustment = 2

    market_score = (
        base_score +
        vix_adjustment
    )

    market_score = round(
        max(
            0,
            min(
                100,
                market_score
            )
        ),
        2
    )

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

    return (
        regime,
        market_score
    )


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

def get_market_regime(
    breadth=None
):

    print()
    print("=" * 60)
    print("MARKET REGIME ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # NIFTY 50
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

    print()
    print("Analysing INDIA VIX")

    vix_data = download_data(
        INDEXES["INDIA VIX"],
        period="1y"
    )

    if vix_data.empty:

        vix = np.nan
        vix_daily_return = np.nan

    else:

        vix = float(
            vix_data["Close"].iloc[-1]
        )

        if len(vix_data) >= 2:

            previous_vix = float(
                vix_data["Close"].iloc[-2]
            )

            if previous_vix != 0:

                vix_daily_return = (
                    (
                        vix -
                        previous_vix
                    )
                    /
                    previous_vix
                    *
                    100
                )

            else:

                vix_daily_return = np.nan

        else:

            vix_daily_return = np.nan

    vix_interpretation = interpret_vix(
        vix
    )

    # --------------------------------------------------------
    # MARKET BREADTH
    # --------------------------------------------------------

    if breadth:

        breadth_score = float(
            breadth.get(
                "breadth_score",
                50
            )
        )

    else:

        breadth_score = 50.0

    # --------------------------------------------------------
    # MARKET REGIME
    # --------------------------------------------------------

    regime, market_score = (
        determine_market_regime(
            nifty["score"],
            bank["score"],
            breadth_score,
            vix
        )
    )

    # --------------------------------------------------------
    # TRADING ENVIRONMENT
    # --------------------------------------------------------

    trading_environment = (
        determine_trading_environment(
            regime,
            breadth_score,
            vix
        )
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "market_regime":
            regime,

        "market_score":
            market_score,

        "nifty_score":
            nifty["score"],

        "bank_nifty_score":
            bank["score"],

        "breadth_score":
            breadth_score,

        "vix":
            round(vix, 2)
            if not pd.isna(vix)
            else None,

        "vix_daily_return_pct":
            round(
                vix_daily_return,
                2
            )
            if not pd.isna(
                vix_daily_return
            )
            else None,

        "vix_interpretation":
            vix_interpretation,

        # NIFTY
        "nifty_price":
            nifty["price"],

        "nifty_previous_close":
            nifty["previous_close"],

        "nifty_daily_return_pct":
            nifty["daily_return_pct"],

        "nifty_trend":
            nifty["trend"],

        "nifty_momentum":
            nifty["momentum"],

        "nifty_rsi":
            nifty["rsi"],

        "nifty_sma20":
            nifty["sma20"],

        "nifty_sma50":
            nifty["sma50"],

        "nifty_sma100":
            nifty["sma100"],

        "nifty_sma200":
            nifty["sma200"],

        "nifty_ema20":
            nifty["ema20"],

        "nifty_ema50":
            nifty["ema50"],

        # BANK NIFTY
        "bank_nifty_price":
            bank["price"],

        "bank_nifty_previous_close":
            bank["previous_close"],

        "bank_nifty_daily_return_pct":
            bank["daily_return_pct"],

        "bank_nifty_trend":
            bank["trend"],

        "bank_nifty_momentum":
            bank["momentum"],

        "bank_nifty_rsi":
            bank["rsi"],

        "bank_nifty_sma20":
            bank["sma20"],

        "bank_nifty_sma50":
            bank["sma50"],

        "bank_nifty_sma100":
            bank["sma100"],

        "bank_nifty_sma200":
            bank["sma200"],

        "bank_nifty_ema20":
            bank["ema20"],

        "bank_nifty_ema50":
            bank["ema50"],

        # ENVIRONMENTS
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

    display_market(
        result
    )

    return result


# ============================================================
# DISPLAY
# ============================================================

def display_market(
    market
):

    if not market:
        return

    print()
    print("=" * 60)
    print("MARKET REGIME SUMMARY")
    print("=" * 60)

    print(
        f"Market Regime        : "
        f"{market.get('market_regime')}"
    )

    print(
        f"Market Score         : "
        f"{market.get('market_score')}"
    )

    print(
        f"NIFTY 50 Price       : "
        f"{market.get('nifty_price')}"
    )

    print(
        f"NIFTY 50 Change      : "
        f"{market.get('nifty_daily_return_pct')}"
    )

    print(
        f"NIFTY 50 Trend       : "
        f"{market.get('nifty_trend')}"
    )

    print(
        f"NIFTY 50 Momentum    : "
        f"{market.get('nifty_momentum')}"
    )

    print(
        f"NIFTY 50 RSI         : "
        f"{market.get('nifty_rsi')}"
    )

    print(
        f"BANK NIFTY Price     : "
        f"{market.get('bank_nifty_price')}"
    )

    print(
        f"BANK NIFTY Change    : "
        f"{market.get('bank_nifty_daily_return_pct')}"
    )

    print(
        f"BANK NIFTY Trend     : "
        f"{market.get('bank_nifty_trend')}"
    )

    print(
        f"BANK NIFTY Momentum  : "
        f"{market.get('bank_nifty_momentum')}"
    )

    print(
        f"BANK NIFTY RSI       : "
        f"{market.get('bank_nifty_rsi')}"
    )

    print(
        f"Breadth Score        : "
        f"{market.get('breadth_score')}"
    )

    print(
        f"India VIX            : "
        f"{market.get('vix')}"
    )

    print(
        f"VIX Interpretation   : "
        f"{market.get('vix_interpretation')}"
    )

    print()
    print(
        f"Equity Environment   : "
        f"{market.get('equity_environment')}"
    )

    print(
        f"Swing Environment    : "
        f"{market.get('swing_environment')}"
    )

    print(
        f"Breakout Environment : "
        f"{market.get('breakout_environment')}"
    )

    print(
        f"Intraday Environment : "
        f"{market.get('intraday_environment')}"
    )

    print(
        f"Options Environment  : "
        f"{market.get('options_environment')}"
    )

    print("=" * 60)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    market = get_market_regime()

    display_market(
        market
    )
