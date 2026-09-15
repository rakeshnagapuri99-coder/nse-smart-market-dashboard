import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# NSE SMART MARKET DASHBOARD
# MARKET REGIME ENGINE V2.1
#
# IMPORTANT:
# - NSE official snapshot = authoritative latest market value
# - Yahoo Finance = historical technical data
# - Latest NSE session is merged into historical data
# - Previous Close is kept separately
# ============================================================


BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SYMBOLS
# ============================================================

INDEXES = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX"
}


NSE_INDEX_ALIASES = {

    "NIFTY 50": [
        "NIFTY 50",
        "NIFTY",
    ],

    "BANK NIFTY": [
        "NIFTY BANK",
        "BANK NIFTY",
    ],

    "INDIA VIX": [
        "INDIA VIX",
        "INDIA VIX INDEX",
    ],
}


# ============================================================
# NSE SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({

    "User-Agent":
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36",

    "Accept":
        "application/json,text/plain,*/*",

    "Accept-Language":
        "en-IN,en;q=0.9",

    "Referer":
        "https://www.nseindia.com/",

    "Connection":
        "keep-alive",

})


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value):

    try:

        if value is None:
            return np.nan

        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:

        return np.nan


# ============================================================
# CLEAN DATAFRAME
# ============================================================

def clean_dataframe(data):

    if data is None:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    data = data.copy()

    if isinstance(
        data.columns,
        pd.MultiIndex
    ):

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

    if "Close" not in data.columns:

        close_columns = [
            column
            for column in data.columns
            if str(column).lower() == "close"
        ]

        if close_columns:

            data["Close"] = (
                data[close_columns[0]]
            )

    if "Close" not in data.columns:

        return pd.DataFrame()

    data["Close"] = pd.to_numeric(
        data["Close"],
        errors="coerce"
    )

    data = data[
        data["Close"].notna()
    ].copy()

    if not data.empty:

        try:

            data.index = pd.to_datetime(
                data.index
            )

            if getattr(
                data.index,
                "tz",
                None
            ) is not None:

                data.index = (
                    data.index
                    .tz_convert(
                        "Asia/Kolkata"
                    )
                    .tz_localize(None)
                )

        except Exception:
            pass

    return data


# ============================================================
# NSE HOME SESSION
# ============================================================

def initialise_nse_session():

    urls = [

        "https://www.nseindia.com/",

        "https://www.nseindia.com/market-data/"
        "live-equity-market",

    ]

    for url in urls:

        try:

            response = SESSION.get(
                url,
                timeout=20
            )

            if response.status_code == 200:

                return True

        except Exception as error:

            print(
                f"NSE session warning: {error}"
            )

    return False


# ============================================================
# NSE OFFICIAL INDEX SNAPSHOT
# ============================================================

def get_nse_index_snapshot():

    print()
    print("=" * 60)
    print("NSE OFFICIAL INDEX SNAPSHOT")
    print("=" * 60)

    initialise_nse_session()

    url = (
        "https://www.nseindia.com/api/allIndices"
    )

    try:

        response = SESSION.get(
            url,
            timeout=30
        )

        if response.status_code != 200:

            print(
                f"NSE allIndices HTTP "
                f"{response.status_code}"
            )

            return {}

        payload = response.json()

        rows = payload.get(
            "data",
            []
        )

        if not rows:

            print(
                "NSE allIndices returned "
                "no data"
            )

            return {}

        result = {}

        for row in rows:

            index_name = str(
                row.get(
                    "index",
                    ""
                )
            ).strip()

            if not index_name:
                continue

            normalized_name = (
                index_name.upper()
                .replace("-", " ")
                .replace("_", " ")
            )

            matched_key = None

            for key, aliases in (
                NSE_INDEX_ALIASES.items()
            ):

                for alias in aliases:

                    alias_normalized = (
                        alias.upper()
                        .replace("-", " ")
                        .replace("_", " ")
                    )

                    if (
                        normalized_name
                        == alias_normalized
                    ):

                        matched_key = key
                        break

                if matched_key:
                    break

            if not matched_key:
                continue

            result[matched_key] = row

        print(
            "NSE index records found:",
            list(result.keys())
        )

        return result

    except Exception as error:

        print(
            f"NSE index API failed: {error}"
        )

        return {}


# ============================================================
# PARSE NSE SNAPSHOT
# ============================================================

def parse_nse_snapshot(
    snapshot,
    name
):

    if not snapshot:

        return {
            "name": name,
            "available": False
        }

    row = snapshot.get(name)

    if not row:

        return {
            "name": name,
            "available": False
        }

    return {

        "name":
            name,

        "available":
            True,

        "index":
            row.get("index"),

        "last":
            safe_float(
                row.get("last")
            ),

        "open":
            safe_float(
                row.get("open")
            ),

        "high":
            safe_float(
                row.get("high")
            ),

        "low":
            safe_float(
                row.get("low")
            ),

        "previous_close":
            safe_float(
                row.get("previousClose")
            ),

        "change":
            safe_float(
                row.get("variation")
            ),

        "percent_change":
            safe_float(
                row.get("percentChange")
            ),

        "year_high":
            safe_float(
                row.get("yearHigh")
            ),

        "year_low":
            safe_float(
                row.get("yearLow")
            ),

        "date":
            row.get("date"),

    }


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

        data = clean_dataframe(
            data
        )

        if not data.empty:

            print(
                f"yfinance success: "
                f"{symbol} "
                f"({len(data)} rows)"
            )

            return data

    except Exception as error:

        print(
            f"yfinance failed "
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
        f"Trying Yahoo Chart API: "
        f"{symbol}"
    )

    end_time = int(
        time.time()
    )

    start_time = (
        end_time
        - period_days * 24 * 60 * 60
    )

    params = {

        "period1":
            start_time,

        "period2":
            end_time,

        "interval":
            "1d",

        "events":
            "history",

        "includeAdjustedClose":
            "true",

    }

    urls = [

        (
            "https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{symbol}"
        ),

        (
            "https://query2.finance.yahoo.com/"
            f"v8/finance/chart/{symbol}"
        ),

    ]

    for url in urls:

        try:

            response = SESSION.get(
                url,
                params=params,
                timeout=30
            )

            if response.status_code != 200:
                continue

            payload = response.json()

            results = (
                payload
                .get("chart", {})
                .get("result")
            )

            if not results:
                continue

            result = results[0]

            timestamps = result.get(
                "timestamp"
            )

            quote_list = (
                result
                .get("indicators", {})
                .get("quote", [])
            )

            if not timestamps:
                continue

            if not quote_list:
                continue

            quote = quote_list[0]

            length = len(timestamps)

            def fill_values(values):

                if values is None:

                    return [
                        np.nan
                        for _ in range(length)
                    ]

                return values

            data = pd.DataFrame({

                "Open":
                    fill_values(
                        quote.get("open")
                    ),

                "High":
                    fill_values(
                        quote.get("high")
                    ),

                "Low":
                    fill_values(
                        quote.get("low")
                    ),

                "Close":
                    fill_values(
                        quote.get("close")
                    ),

                "Volume":
                    fill_values(
                        quote.get("volume")
                    ),

            })

            data["Date"] = (
                pd.to_datetime(
                    timestamps,
                    unit="s",
                    utc=True
                )
                .tz_convert(
                    "Asia/Kolkata"
                )
                .tz_localize(None)
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
                f"Yahoo Chart failed "
                f"{symbol}: {error}"
            )

    return pd.DataFrame()


# ============================================================
# HISTORICAL DATA
# ============================================================

def download_data(
    symbol,
    period="2y"
):

    data = download_yfinance(
        symbol,
        period
    )

    if not data.empty:

        return data

    data = download_yahoo_chart(
        symbol,
        period_days=730
    )

    return data


# ============================================================
# MERGE OFFICIAL NSE LATEST SESSION
# ============================================================

def merge_nse_latest(
    historical,
    snapshot
):

    if not snapshot:
        return historical

    if not snapshot.get(
        "available",
        False
    ):

        return historical

    latest_close = safe_float(
        snapshot.get("last")
    )

    if pd.isna(latest_close):
        return historical

    latest_date = pd.Timestamp(
        datetime.now()
        .astimezone()
        .date()
    )

    # --------------------------------------------------------
    # Prefer the NSE reported date when available
    # --------------------------------------------------------

    raw_date = snapshot.get(
        "date"
    )

    if raw_date:

        try:

            parsed = pd.to_datetime(
                raw_date,
                dayfirst=True,
                errors="coerce"
            )

            if not pd.isna(parsed):

                latest_date = (
                    pd.Timestamp(
                        parsed.date()
                    )
                )

        except Exception:
            pass

    official_row = {

        "Open":
            snapshot.get("open"),

        "High":
            snapshot.get("high"),

        "Low":
            snapshot.get("low"),

        "Close":
            latest_close,

        "Volume":
            np.nan,

    }

    if historical is None:

        historical = pd.DataFrame()

    historical = historical.copy()

    if not historical.empty:

        historical.index = pd.to_datetime(
            historical.index
        ).tz_localize(None)

        historical = (
            historical[
                historical.index
                != latest_date
            ]
        )

    official_df = pd.DataFrame(
        [official_row],
        index=[latest_date]
    )

    merged = pd.concat(
        [
            historical,
            official_df
        ]
    )

    merged = (
        merged[
            ~merged.index.duplicated(
                keep="last"
            )
        ]
        .sort_index()
    )

    print(
        "Official NSE session merged:",
        latest_date.date(),
        latest_close
    )

    return merged


# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def calculate_indicators(
    data
):

    if data.empty:
        return data

    data = data.copy()

    close = pd.to_numeric(
        data["Close"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Moving averages
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

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
    # Daily return
    # --------------------------------------------------------

    data["Daily_Return_Pct"] = (
        close.pct_change()
        * 100
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

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

def determine_trend(
    row
):

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

def determine_momentum(
    row
):

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

def trend_score(
    trend
):

    scores = {

        "Strong Bullish":
            100,

        "Bullish":
            80,

        "Neutral":
            50,

        "Bearish":
            25,

        "Strong Bearish":
            0,

    }

    return scores.get(
        trend,
        50
    )


def momentum_score(
    momentum
):

    scores = {

        "Strong Positive":
            100,

        "Positive":
            75,

        "Neutral":
            50,

        "Weak":
            25,

        "Strong Negative":
            0,

    }

    return scores.get(
        momentum,
        50
    )


# ============================================================
# ANALYSE INDEX
# ============================================================

def analyze_index(
    name,
    symbol,
    nse_snapshot
):

    print()
    print(
        f"Analysing {name}"
    )

    # --------------------------------------------------------
    # Historical data
    # --------------------------------------------------------

    data = download_data(
        symbol
    )

    # --------------------------------------------------------
    # Official NSE snapshot
    # --------------------------------------------------------

    official = parse_nse_snapshot(
        nse_snapshot,
        name
    )

    # --------------------------------------------------------
    # Merge latest NSE session
    # --------------------------------------------------------

    data = merge_nse_latest(
        data,
        official
    )

    if data.empty:

        return {

            "name":
                name,

            "symbol":
                symbol,

            "price":
                np.nan,

            "previous_close":
                np.nan,

            "daily_return_pct":
                np.nan,

            "trend":
                "Unavailable",

            "momentum":
                "Unavailable",

            "rsi":
                np.nan,

            "sma20":
                np.nan,

            "sma50":
                np.nan,

            "sma100":
                np.nan,

            "sma200":
                np.nan,

            "ema20":
                np.nan,

            "ema50":
                np.nan,

            "score":
                50,

            "data_source":
                "Unavailable",

            "data_date":
                None,

            "open":
                np.nan,

            "high":
                np.nan,

            "low":
                np.nan,

            "year_high":
                np.nan,

            "year_low":
                np.nan,

        }

    data = calculate_indicators(
        data
    )

    latest = data.iloc[-1]

    # --------------------------------------------------------
    # Previous close
    #
    # IMPORTANT:
    # This is the previous row BEFORE the official latest
    # NSE session.
    # --------------------------------------------------------

    previous_close = np.nan

    if len(data) >= 2:

        previous_close = safe_float(
            data["Close"].iloc[-2]
        )

    # --------------------------------------------------------
    # Prefer official previous close
    # --------------------------------------------------------

    official_previous = safe_float(
        official.get(
            "previous_close"
        )
    )

    if not pd.isna(
        official_previous
    ):

        previous_close = (
            official_previous
        )

    # --------------------------------------------------------
    # Trend / momentum
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Daily return
    # --------------------------------------------------------

    daily_return = safe_float(
        latest[
            "Daily_Return_Pct"
        ]
    )

    if (
        not pd.isna(
            official.get(
                "percent_change"
            )
        )
    ):

        daily_return = (
            official[
                "percent_change"
            ]
        )

    # --------------------------------------------------------
    # Data date
    # --------------------------------------------------------

    data_date = None

    try:

        data_date = (
            data.index[-1]
            .strftime(
                "%Y-%m-%d"
            )
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # Data source
    # --------------------------------------------------------

    if official.get(
        "available",
        False
    ):

        data_source = (
            "NSE Official + "
            "Yahoo Historical"
        )

    else:

        data_source = (
            "Yahoo Finance"
        )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return {

        "name":
            name,

        "symbol":
            symbol,

        "price":
            safe_float(
                latest["Close"]
            ),

        "previous_close":
            previous_close,

        "daily_return_pct":
            daily_return,

        "trend":
            trend,

        "momentum":
            momentum,

        "rsi":
            safe_float(
                latest["RSI14"]
            ),

        "sma20":
            safe_float(
                latest["SMA20"]
            ),

        "sma50":
            safe_float(
                latest["SMA50"]
            ),

        "sma100":
            safe_float(
                latest["SMA100"]
            ),

        "sma200":
            safe_float(
                latest["SMA200"]
            ),

        "ema20":
            safe_float(
                latest["EMA20"]
            ),

        "ema50":
            safe_float(
                latest["EMA50"]
            ),

        "score":
            round(
                score,
                2
            ),

        "open":
            safe_float(
                latest["Open"]
            ),

        "high":
            safe_float(
                latest["High"]
            ),

        "low":
            safe_float(
                latest["Low"]
            ),

        "year_high":
            safe_float(
                official.get(
                    "year_high"
                )
            ),

        "year_low":
            safe_float(
                official.get(
                    "year_low"
                )
            ),

        "data_source":
            data_source,

        "data_date":
            data_date,

    }


# ============================================================
# VIX INTERPRETATION
# ============================================================

def interpret_vix(
    vix
):

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

        base_score
        +
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

            "equity":
                "Favorable",

            "swing":
                "Favorable",

            "breakout":
                "Favorable",

            "intraday":
                "Favorable",

            "options":
                "Selective",

        }

    if regime == "Bullish but Cautious":

        return {

            "equity":
                "Selective",

            "swing":
                "Selective",

            "breakout":
                "Selective",

            "intraday":
                "Selective",

            "options":
                "Selective",

        }

    if regime == "Sideways":

        return {

            "equity":
                "Selective",

            "swing":
                "Selective",

            "breakout":
                "Confirmation Required",

            "intraday":
                "Selective",

            "options":
                "Risky",

        }

    if regime == "Weak":

        return {

            "equity":
                "Cautious",

            "swing":
                "Cautious",

            "breakout":
                "Avoid Weak Breakouts",

            "intraday":
                "Selective",

            "options":
                "High Risk",

        }

    return {

        "equity":
            "Defensive",

        "swing":
            "Avoid",

        "breakout":
            "Avoid",

        "intraday":
            "Selective",

        "options":
            "Very High Risk",

    }


# ============================================================
# MAIN MARKET FUNCTION
# ============================================================

def get_market_regime(
    breadth=None
):

    print()
    print("=" * 70)
    print("NSE SMART MARKET DASHBOARD")
    print("MARKET REGIME ANALYSIS V2.1")
    print("=" * 70)

    # --------------------------------------------------------
    # Get official NSE data FIRST
    # --------------------------------------------------------

    nse_snapshot = (
        get_nse_index_snapshot()
    )

    # --------------------------------------------------------
    # NIFTY
    # --------------------------------------------------------

    nifty = analyze_index(

        "NIFTY 50",

        INDEXES[
            "NIFTY 50"
        ],

        nse_snapshot

    )

    # --------------------------------------------------------
    # BANK NIFTY
    # --------------------------------------------------------

    bank = analyze_index(

        "BANK NIFTY",

        INDEXES[
            "BANK NIFTY"
        ],

        nse_snapshot

    )

    # --------------------------------------------------------
    # INDIA VIX
    # --------------------------------------------------------

    print()
    print(
        "Analysing INDIA VIX"
    )

    vix_official = parse_nse_snapshot(
        nse_snapshot,
        "INDIA VIX"
    )

    vix_data = download_data(
        INDEXES["INDIA VIX"],
        period="1y"
    )

    vix_data = merge_nse_latest(
        vix_data,
        vix_official
    )

    if vix_data.empty:

        vix = np.nan
        vix_previous = np.nan
        vix_daily_return = np.nan

    else:

        vix = safe_float(
            vix_data[
                "Close"
            ].iloc[-1]
        )

        if len(vix_data) >= 2:

            vix_previous = safe_float(
                vix_data[
                    "Close"
                ].iloc[-2]
            )

        else:

            vix_previous = np.nan

        if (
            not pd.isna(
                vix_previous
            )
            and vix_previous != 0
        ):

            vix_daily_return = (

                (
                    vix
                    -
                    vix_previous
                )
                /
                vix_previous
                *
                100

            )

        else:

            vix_daily_return = np.nan

    official_vix_change = safe_float(
        vix_official.get(
            "percent_change"
        )
    )

    if not pd.isna(
        official_vix_change
    ):

        vix_daily_return = (
            official_vix_change
        )

    vix_interpretation = (
        interpret_vix(vix)
    )

    # --------------------------------------------------------
    # Breadth
    # --------------------------------------------------------

    if breadth:

        breadth_score = safe_float(

            breadth.get(
                "breadth_score",
                50
            )

        )

        if pd.isna(
            breadth_score
        ):

            breadth_score = 50.0

    else:

        breadth_score = 50.0

    # --------------------------------------------------------
    # Market regime
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
    # Environment
    # --------------------------------------------------------

    environment = (
        determine_trading_environment(

            regime,

            breadth_score,

            vix

        )
    )

    # --------------------------------------------------------
    # Market date
    # --------------------------------------------------------

    market_date = (

        nifty.get(
            "data_date"
        )

        or

        bank.get(
            "data_date"
        )

    )

    # --------------------------------------------------------
    # Result
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

        # ----------------------------------------------------
        # VIX
        # ----------------------------------------------------

        "vix":
            None
            if pd.isna(vix)
            else round(
                vix,
                2
            ),

        "vix_previous_close":
            None
            if pd.isna(
                vix_previous
            )
            else round(
                vix_previous,
                2
            ),

        "vix_daily_return_pct":
            None
            if pd.isna(
                vix_daily_return
            )
            else round(
                vix_daily_return,
                2
            ),

        "vix_interpretation":
            vix_interpretation,

        # ----------------------------------------------------
        # NIFTY
        # ----------------------------------------------------

        "nifty_price":
            nifty["price"],

        "nifty_previous_close":
            nifty[
                "previous_close"
            ],

        "nifty_daily_return_pct":
            nifty[
                "daily_return_pct"
            ],

        "nifty_open":
            nifty["open"],

        "nifty_high":
            nifty["high"],

        "nifty_low":
            nifty["low"],

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

        # ----------------------------------------------------
        # BANK NIFTY
        # ----------------------------------------------------

        "bank_nifty_price":
            bank["price"],

        "bank_nifty_previous_close":
            bank[
                "previous_close"
            ],

        "bank_nifty_daily_return_pct":
            bank[
                "daily_return_pct"
            ],

        "bank_nifty_open":
            bank["open"],

        "bank_nifty_high":
            bank["high"],

        "bank_nifty_low":
            bank["low"],

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

        # ----------------------------------------------------
        # DATA QUALITY
        # ----------------------------------------------------

        "market_data_date":
            market_date,

        "nifty_data_source":
            nifty[
                "data_source"
            ],

        "bank_nifty_data_source":
            bank[
                "data_source"
            ],

        "vix_data_source":
            (
                "NSE Official + "
                "Yahoo Historical"
                if vix_official.get(
                    "available",
                    False
                )
                else "Yahoo Finance"
            ),

        "market_data_authority":
            "NSE Official",

        # ----------------------------------------------------
        # ENVIRONMENTS
        # ----------------------------------------------------

        "equity_environment":
            environment[
                "equity"
            ],

        "swing_environment":
            environment[
                "swing"
            ],

        "breakout_environment":
            environment[
                "breakout"
            ],

        "intraday_environment":
            environment[
                "intraday"
            ],

        "options_environment":
            environment[
                "options"
            ],

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
    print("=" * 70)
    print("MARKET REGIME SUMMARY")
    print("=" * 70)

    print(
        f"Market Date          : "
        f"{market.get('market_data_date')}"
    )

    print(
        f"Market Data Authority: "
        f"{market.get('market_data_authority')}"
    )

    print(
        f"Market Regime        : "
        f"{market.get('market_regime')}"
    )

    print(
        f"Market Score         : "
        f"{market.get('market_score')}"
    )

    print()
    print(
        f"NIFTY Last Close     : "
        f"{market.get('nifty_price')}"
    )

    print(
        f"NIFTY Previous Close : "
        f"{market.get('nifty_previous_close')}"
    )

    print(
        f"NIFTY Change %       : "
        f"{market.get('nifty_daily_return_pct')}"
    )

    print(
        f"NIFTY Data Source    : "
        f"{market.get('nifty_data_source')}"
    )

    print()
    print(
        f"BANK Last Close      : "
        f"{market.get('bank_nifty_price')}"
    )

    print(
        f"BANK Previous Close  : "
        f"{market.get('bank_nifty_previous_close')}"
    )

    print(
        f"BANK Change %        : "
        f"{market.get('bank_nifty_daily_return_pct')}"
    )

    print(
        f"BANK Data Source     : "
        f"{market.get('bank_nifty_data_source')}"
    )

    print()
    print(
        f"India VIX            : "
        f"{market.get('vix')}"
    )

    print(
        f"VIX Change %         : "
        f"{market.get('vix_daily_return_pct')}"
    )

    print(
        f"VIX Interpretation   : "
        f"{market.get('vix_interpretation')}"
    )

    print()
    print(
        f"Breadth Score        : "
        f"{market.get('breadth_score')}"
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

    print("=" * 70)


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    market = get_market_regime()

    display_market(
        market
    )
